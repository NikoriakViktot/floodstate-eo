# Provenance: SWOT-DNIPRO scripts/p74_m6_smoke_b2.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: ACTIVE_ENGINEERING -- intentional 15-patch overfit: a pipeline test, not evidence of generalisation; label contract v001 (p69b, BASE_CLASS-entangled).
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P74 -- Stage S: does spatial SAR segmentation work at all? U0 on B2, 12-16 patches, intentional overfit.

U0 IS DELIBERATELY IMPOVERISHED. Only the orbit-safe Sentinel-1 anomaly channels from p71 -- no HAND, no
BASE_CLASS, no Sentinel-2, no TRACE. If the network can separate connected delta inundation from rectangular
agricultural false water with SAR change and spatial context alone, that is a result about the architecture. If it
can only do so once terrain and land cover are added, that is a different result. Bundling them from the start
would have answered neither.

THE OVERFIT IS A TEST OF THE PIPELINE, NOT OF THE SCIENCE. A U-Net given 12-16 patches must reproduce their labels
almost exactly. If it cannot, the fault is in tensor ordering, normalisation, the IGNORE mask, the loss or the
spatial alignment -- never in the data being "hard" -- and a multi-hour training run would only hide it.

LABELS, three states, and the disputed area is NOT among the positives:
    FLOOD        weak-reference positive AND Sentinel-1 peak water -- two sources agreeing
    NON_FLOOD    weak-reference negative: dry in every observed post-breach event, with support
    IGNORE       everything else, and explicitly the 79.2 km2 of B2 that Sentinel-1 claims and the optical model
                 does not. Those stay out of supervision so that a later run can ask whether the network recovers
                 them from spatial context -- which it cannot answer if they were trained on.

GEOGRAPHY IS SPLIT BEFORE PATCHES ARE CUT, never after: a patch may not straddle a split boundary, and no training
patch centre may lie within half a patch of a validation block.

Outputs: outputs/tables/p74_smoke_{patches,labels,overfit}.csv, outputs/figures/p74_smoke_patches.png,
         $BULK_ROOT/frames10/_m6/smoke_b2.pt
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
M6 = OUT / "_m6"; M6.mkdir(parents=True, exist_ok=True)
FID = "B2"
PATCH = 512
SCALE = 100.0
ND = -32768
PEAK = ("2023-06-09", "2023-06-13", "2023-06-14")
SEED = 20260923


def s1_peak_water(F):
    z = np.load(CFG.S1_CACHE / "ZONE_2_KHERSON_DELTA_flood_june2023" / "per_scene_water.npz", allow_pickle=True)
    shp = tuple(int(v) for v in z["shape"]); cell = float(z["cell"])
    tr = from_origin(float(z["x0"]), float(z["y1"]), cell, cell)
    wet = np.zeros(shp, bool)
    for k in [k for k in z.keys() if k[:4] == "2023" and not k.startswith("valid_")]:
        if k[:10] not in PEAK:
            continue
        w = np.unpackbits(z[k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
        v = np.unpackbits(z["valid_" + k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
        wet |= (w & v)
    d = np.zeros((F["ny"], F["nx"]), "u1")
    reproject(source=wet.astype("u1"), destination=d, src_transform=tr, src_crs=CFG.CRS_METRIC,
              dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest,
              src_nodata=0, dst_nodata=0)
    return d.astype(bool)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--n-patches", type=int, default=16); a = ap.parse_args()
    F = CG.frame_grid(FID)
    with rasterio.open(OUT / FID / "s1_change.tif") as s:
        CH = list(s.descriptions); X = s.read().astype("f4")
    X[X == ND] = np.nan
    for i, c in enumerate(CH):
        if not c.startswith("n_"):
            X[i] /= SCALE
    with rasterio.open(OUT / FID / "labels.tif") as s:
        lab = s.read(1)
    with rasterio.open(OUT / FID / "p69b_semantic_state.tif") as s:
        sem = s.read(1)
    with rasterio.open(OUT / FID / "folds.tif") as s:
        blk = s.read(4)
    s1w = s1_peak_water(F)
    m2 = np.isin(sem, (1, 2, 3, 4, 5))

    y = np.full((F["ny"], F["nx"]), 255, np.uint8)
    y[(lab == 0)] = 0                                   # weak-reference negative: observed dry throughout
    y[(lab == 1) & s1w & m2] = 1                        # two independent sources agreeing
    disputed = s1w & ~m2                                # the 79.2 km2: stays IGNORE by construction
    y[disputed] = 255
    print(f"{FID}: FLOOD {int((y==1).sum())*1e-4:,.1f} km2, NON_FLOOD {int((y==0).sum())*1e-4:,.0f} km2, "
          f"IGNORE {int((y==255).sum())*1e-4:,.0f} km2 (disputed {float(disputed.sum())*1e-4:,.1f} km2)", flush=True)

    # ---- geography FIRST: whole 5 km blocks to train or val, then patches inside them --------------------------
    rng = np.random.default_rng(SEED)
    ub = np.unique(blk[blk > 0]); rng.shuffle(ub)
    val_blocks = set(ub[:max(1, len(ub) // 5)].tolist())
    is_val = np.isin(blk, list(val_blocks))
    print(f"  {len(ub)} blocks of 5 km -> {len(val_blocks)} held out for validation", flush=True)

    # ---- patch selection: deliberately diverse, never straddling the split -------------------------------------
    half = PATCH // 2
    cand = []
    step = PATCH // 2
    for r in range(half, F["ny"] - half, step):
        for c in range(half, F["nx"] - half, step):
            sl = (slice(r - half, r + half), slice(c - half, c + half))
            if is_val[sl].any() and (~is_val[sl]).any():
                continue                                        # straddles the split -> rejected
            yy = y[sl]
            nf = int((yy == 1).sum())
            if np.isnan(X[0][sl]).mean() > 0.5:
                continue
            cand.append(dict(row=r, col=c, split="val" if is_val[r, c] else "train",
                             flood_px=nf, flood_frac=nf / (PATCH * PATCH),
                             ignore_frac=float((yy == 255).mean()),
                             disputed_px=int(disputed[sl].sum())))
    C = pd.DataFrame(cand)
    print(f"  {len(C)} candidate patches, {int((C.flood_px>0).sum())} contain flood", flush=True)
    tr = C[C.split == "train"].sort_values("flood_frac", ascending=False)
    pick = pd.concat([tr.head(a.n_patches // 2),                                   # flood-rich
                      tr[tr.flood_px == 0].head(a.n_patches // 4),                 # stable dry
                      tr[tr.disputed_px > 0].sort_values("disputed_px", ascending=False).head(a.n_patches // 4)
                      ]).drop_duplicates(subset=["row", "col"]).head(a.n_patches)
    pick.to_csv(CFG.TABLES / "p74_smoke_patches.csv", index=False)
    print(f"  selected {len(pick)} patches: flood_frac {pick.flood_frac.min():.4f}..{pick.flood_frac.max():.4f}",
          flush=True)

    # ---- tensors; normalisation statistics from the TRAIN patches only -------------------------------------------
    xs, ys = [], []
    for r_ in pick.itertuples():
        sl = (slice(r_.row - half, r_.row + half), slice(r_.col - half, r_.col + half))
        xs.append(X[:, sl[0], sl[1]]); ys.append(y[sl])
    Xp = np.stack(xs); Yp = np.stack(ys)
    med = np.nanmedian(Xp, axis=(0, 2, 3), keepdims=True)
    iqr = np.nanpercentile(Xp, 75, axis=(0, 2, 3), keepdims=True) - \
          np.nanpercentile(Xp, 25, axis=(0, 2, 3), keepdims=True)
    iqr[iqr < 1e-6] = 1.0
    Xn = np.nan_to_num((Xp - med) / iqr, nan=0.0).astype("f4")
    pd.DataFrame(dict(channel=CH, median=med.ravel(), iqr=iqr.ravel())).to_csv(
        CFG.TABLES / "p74_smoke_labels.csv", index=False)

    import torch, torch.nn as nn, segmentation_models_pytorch as smp
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(SEED)
    net = smp.Unet("resnet34", encoder_weights=None, in_channels=len(CH), classes=1).to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-4)
    scaler = torch.amp.GradScaler("cuda")
    bce = nn.BCEWithLogitsLoss(reduction="none")
    xt = torch.from_numpy(Xn).to(dev)
    yt = torch.from_numpy(Yp.astype("i8")).to(dev)
    valid = (yt != 255)
    tgt = torch.where(valid, yt, torch.zeros_like(yt)).float()
    print(f"  tensor {tuple(xt.shape)} on {dev}; supervised pixels {int(valid.sum()):,} of {valid.numel():,}",
          flush=True)
    hist = []
    t0 = time.time()
    for ep in range(a.epochs):
        net.train(); opt.zero_grad()
        with torch.amp.autocast("cuda"):
            out = net(xt).squeeze(1)
            l_bce = (bce(out, tgt) * valid).sum() / valid.sum()
            p = torch.sigmoid(out) * valid
            t = tgt * valid
            dice = 1 - (2 * (p * t).sum() + 1) / (p.sum() + t.sum() + 1)
            loss = l_bce + dice
        scaler.scale(loss).backward(); scaler.step(opt); scaler.update()
        if ep % 10 == 0 or ep == a.epochs - 1:
            with torch.no_grad():
                pr = (torch.sigmoid(out) > 0.5) & valid
                tp = int((pr & (yt == 1)).sum()); fp = int((pr & (yt == 0)).sum())
                fn = int((~pr & (yt == 1) & valid).sum())
                f1 = 2 * tp / max(2 * tp + fp + fn, 1)
            hist.append(dict(epoch=ep, loss=float(loss), bce=float(l_bce), dice=float(dice), f1=round(f1, 4),
                             vram_gb=round(torch.cuda.max_memory_allocated() / 1e9, 2)))
            print(f"    ep {ep:3d}  loss {float(loss):.4f}  dice {float(dice):.4f}  F1 {f1:.4f}  "
                  f"VRAM {hist[-1]['vram_gb']:.2f} GB", flush=True)
    H = pd.DataFrame(hist); H.to_csv(CFG.TABLES / "p74_smoke_overfit.csv", index=False)
    ok = H.f1.iloc[-1] > 0.90
    print(f"\n  {a.epochs} epochs in {time.time()-t0:.0f}s, peak VRAM {H.vram_gb.max():.2f} GB")
    print(f"OVERFIT {'PASS' if ok else 'FAIL'}: final F1 on supervised pixels {H.f1.iloc[-1]:.4f}")
    torch.save(dict(state=net.state_dict(), channels=CH, median=med, iqr=iqr), M6 / "smoke_b2.pt")
    print("-> outputs/tables/p74_smoke_{patches,labels,overfit}.csv")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
