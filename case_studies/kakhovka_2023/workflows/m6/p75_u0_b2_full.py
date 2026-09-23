# Provenance: SWOT-DNIPRO scripts/p75_u0_b2_full.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: ACTIVE -- U0_B2_FULL trainer; its --run U0_B2_CORRECTED output on p71v2 dB inputs is the ACTIVE_REFERENCE; label contract v001 (p69b, BASE_CLASS-entangled) -- superseded for ablations by m6_labels_v002.
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P75 -- U0_B2_FULL: does orbit-safe SAR change, segmented spatially, generalise to unseen geographic blocks?

NOT the final M6 model, and PASS here means only that a SAR-only U-Net generalises spatially on B2's weak labels.
It says nothing about validated flood extent.

WHAT IS DELIBERATELY ABSENT: Sentinel-2, HAND, distance to water, BASE_CLASS, p73, TRACE. U0 is the clean SAR-only
baseline; everything else is a later ablation whose value can only be measured against this.

THE DISPUTED POPULATION IS NEVER SUPERVISED. The cells Sentinel-1 claims and the optical model does not stay
IGNORE: out of the loss, out of threshold selection, out of early stopping, out of tuning. That is the whole point
-- the network has never been told they are flood, so what it predicts there is evidence rather than an echo. Such
predictions are named MODEL-SUPPORTED CANDIDATES and never "recovered flood".

THREE DISJOINT GEOGRAPHIES, asserted rather than assumed. The 28 blocks held out earlier become TEST and are not
touched again until the threshold is frozen; VALIDATION blocks are carved out of the training geography. A patch
may not straddle any boundary. Normalisation statistics come from TRAIN patches alone.

THE INTERESTING RESULT IS NOT GLOBAL F1. It is whether rectangular field-shaped false positives fall while recall
on the confirmed delta holds. Either alone is easy; together they would be the argument that moving from a
per-pixel forest to spatial segmentation addressed a structural problem rather than swapping classifiers.

Outputs: runs/U0_B2/{config.json,split_manifest.csv,normalization.json,training_history.csv,
         validation_threshold.json,test_metrics.json,challenge_metrics.csv,disputed_score_stats.csv,
         model_best.pt,model_last.pt,maps/*.tif}
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
from scipy import ndimage
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
RUN = ROOT / "runs" / "U0_B2"
FID = "B2"; PATCH = 512; STRIDE = 128; SCALE = 100.0; ND = -32768
#: THE SPLIT USES 10 km BLOCKS, NOT THE 5 km ONES. A 512-cell patch is 5.12 km across -- wider than a 5 km block --
#: so every candidate patch straddled two blocks and the boundary rule rejected all of them: measured, 0 of 364.
#: On the 10 km lattice 78 of 364 survive at stride 256, and stride 128 raises that to a workable number. The
#: overlapping patches share geography only WITHIN their own split, so no train patch sees test ground.
SPLIT_BAND = 5          # folds.tif band 5 = blk10
PEAK = ("2023-06-09", "2023-06-13", "2023-06-14")
SEED = 20260923


def s1_peak(F):
    z = np.load(CFG.S1_CACHE / "ZONE_2_KHERSON_DELTA_flood_june2023" / "per_scene_water.npz", allow_pickle=True)
    shp = tuple(int(v) for v in z["shape"]); cell = float(z["cell"])
    tr = from_origin(float(z["x0"]), float(z["y1"]), cell, cell); wet = np.zeros(shp, bool)
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


def metrics(yt, pr):
    tp = int((pr & (yt == 1)).sum()); fp = int((pr & (yt == 0)).sum()); fn = int((~pr & (yt == 1)).sum())
    tn = int((~pr & (yt == 0)).sum())
    P = tp / max(tp + fp, 1); R = tp / max(tp + fn, 1)
    return dict(TP=tp, FP=fp, FN=fn, TN=tn, precision=round(P, 5), recall=round(R, 5),
                F1=round(2 * P * R / max(P + R, 1e-9), 5), IoU=round(tp / max(tp + fp + fn, 1), 5))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--batch", type=int, default=6); ap.add_argument("--lr", type=float, default=3e-4)
    #: The run directory is an argument because the FIRST U0 is frozen as SUPERSEDED_PREPROCESSING_UNIT_ERROR --
    #: it was fitted on a change stack that differenced linear gamma0 (see p71's to_db note). Re-running this file
    #: must never overwrite that record, so the corrected fit lands in its own directory and the two can be
    #: compared rather than one silently replacing the other.
    ap.add_argument("--run", default="U0_B2", help="subdirectory under runs/")
    a = ap.parse_args()
    global RUN
    RUN = ROOT / "runs" / a.run
    import torch, torch.nn as nn, segmentation_models_pytorch as smp
    RUN.mkdir(parents=True, exist_ok=True); (RUN / "maps").mkdir(exist_ok=True)
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
        blk = s.read(SPLIT_BAND)
    with rasterio.open(OUT / FID / "p69a_base_class.tif") as s:
        bc = s.read(1)
    s1w = s1_peak(F); m2 = np.isin(sem, (1, 2, 3, 4, 5))
    y = np.full((F["ny"], F["nx"]), 255, np.uint8)
    y[lab == 0] = 0
    y[(lab == 1) & s1w & m2] = 1
    disputed = s1w & ~m2
    y[disputed] = 255

    # ---- three disjoint geographies, asserted -----------------------------------------------------------------
    rng = np.random.default_rng(SEED)
    ub = np.unique(blk[blk > 0]); rng.shuffle(ub)
    n_te = max(1, len(ub) // 5); test_b = set(ub[:n_te].tolist())
    rest = ub[n_te:]; n_va = max(1, len(rest) // 5); val_b = set(rest[:n_va].tolist())
    train_b = set(rest[n_va:].tolist())
    assert not (train_b & val_b) and not (train_b & test_b) and not (val_b & test_b)
    role = np.zeros_like(blk, np.uint8)
    role[np.isin(blk, list(train_b))] = 1; role[np.isin(blk, list(val_b))] = 2
    role[np.isin(blk, list(test_b))] = 3
    print(f"blocks: train {len(train_b)}, val {len(val_b)}, test {len(test_b)}  (disjoint asserted)", flush=True)

    half = PATCH // 2; cand = []
    for r in range(half, F["ny"] - half, STRIDE):
        for c in range(half, F["nx"] - half, STRIDE):
            sl = (slice(r - half, r + half), slice(c - half, c + half))
            rr = role[sl]; u = set(np.unique(rr[rr > 0]).tolist())
            if len(u) != 1:
                continue                                    # straddles a split boundary -> rejected
            if np.isnan(X[0][sl]).mean() > 0.5:
                continue
            yy = y[sl]
            cand.append(dict(row=r, col=c, split={1: "train", 2: "val", 3: "test"}[u.pop()],
                             flood_px=int((yy == 1).sum()), neg_px=int((yy == 0).sum()),
                             disputed_px=int(disputed[sl].sum())))
    C = pd.DataFrame(cand)
    if not len(C):
        raise SystemExit("no candidate patch fits inside a single split block -- the patch is wider than a block")
    C = C[(C.flood_px + C.neg_px) > 0]
    for sp in ("train", "val", "test"):
        n = int((C.split == sp).sum())
        if n == 0:
            raise SystemExit(f"{sp} has no usable patch; do not proceed with an empty split")
    C.to_csv(RUN / "split_manifest.csv", index=False)
    print("  patches: " + ", ".join(f"{k} {v}" for k, v in C.split.value_counts().items()) +
          f"; with flood: {int((C.flood_px>0).sum())}", flush=True)

    # PATCHES ARE SLICED ON DEMAND, NEVER PRE-STACKED. Materialising 335 train patches as one array costs
    # 335 x 15 x 512 x 512 x 4 = 5.3 GB, and with val and test it OOM-killed the run on a 15 GB machine. The full
    # frame is already resident at 1.7 GB, so a patch is a view, not a copy.
    tr_df = C[C.split == "train"].reset_index(drop=True)
    va_df = C[C.split == "val"].reset_index(drop=True)
    te_df = C[C.split == "test"].reset_index(drop=True)
    w = np.where(tr_df.flood_px.values > 0, 4.0, 1.0); w /= w.sum()

    # normalisation from TRAIN patch geography only, sampled rather than fully materialised
    trmask = np.zeros((F["ny"], F["nx"]), bool)
    for r in tr_df.itertuples():
        trmask[r.row - half:r.row + half, r.col - half:r.col + half] = True
    rr, cc = np.nonzero(trmask)
    take = rng.choice(len(rr), size=min(2_000_000, len(rr)), replace=False)
    samp = X[:, rr[take], cc[take]]
    med = np.nanmedian(samp, axis=1)[:, None, None]
    iqr = (np.nanpercentile(samp, 75, axis=1) - np.nanpercentile(samp, 25, axis=1))[:, None, None]
    iqr[iqr < 1e-6] = 1.0
    del samp, rr, cc, take, trmask
    X = np.nan_to_num((X - med) / iqr, nan=0.0).astype("f4")     # normalise once, in place semantics
    json.dump(dict(channels=CH, median=med.ravel().tolist(), iqr=iqr.ravel().tolist(),
                   source="TRAIN patch geography only, 2M-pixel sample"),
              open(RUN / "normalization.json", "w"), indent=2)

    def cut(df, i):
        r = df.iloc[i]
        return (X[:, r.row - half:r.row + half, r.col - half:r.col + half],
                y[r.row - half:r.row + half, r.col - half:r.col + half])
    def batch(df, idx):
        xs = np.stack([X[:, df.iloc[i].row - half:df.iloc[i].row + half,
                         df.iloc[i].col - half:df.iloc[i].col + half] for i in idx])
        ys = np.stack([y[df.iloc[i].row - half:df.iloc[i].row + half,
                         df.iloc[i].col - half:df.iloc[i].col + half] for i in idx])
        return xs, ys

    dev = "cuda"; torch.manual_seed(SEED)
    net = smp.Unet("resnet34", encoder_weights=None, in_channels=len(CH), classes=1).to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr)
    scaler = torch.amp.GradScaler("cuda"); bce = nn.BCEWithLogitsLoss(reduction="none")
    hist = []; best = -1
    t0 = time.time()
    for ep in range(a.epochs):
        net.train()
        idx = rng.choice(len(tr_df), size=min(len(tr_df), 64), replace=True, p=w)
        tot = 0.0; nb = 0
        for i in range(0, len(idx), a.batch):
            b = idx[i:i + a.batch]
            xnp, ynp = batch(tr_df, b)
            xb = torch.from_numpy(xnp).to(dev); yb = torch.from_numpy(ynp.astype("i8")).to(dev)
            if rng.random() < 0.5:
                xb = torch.flip(xb, [-1]); yb = torch.flip(yb, [-1])
            if rng.random() < 0.5:
                xb = torch.flip(xb, [-2]); yb = torch.flip(yb, [-2])
            v = (yb != 255); t = torch.where(v, yb, torch.zeros_like(yb)).float()
            if v.sum() == 0:
                continue
            opt.zero_grad()
            with torch.amp.autocast("cuda"):
                o = net(xb).squeeze(1)
                lb = (bce(o, t) * v).sum() / v.sum()
                p = torch.sigmoid(o) * v
                dl = 1 - (2 * (p * t).sum() + 1) / (p.sum() + (t * v).sum() + 1)
                loss = lb + dl
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update()
            tot += loss.detach().item(); nb += 1
        net.eval(); sc = []; yl = []
        with torch.no_grad(), torch.amp.autocast("cuda"):
            for i in range(0, len(va_df), a.batch):
                xnp, ynp = batch(va_df, range(i, min(i + a.batch, len(va_df))))
                sc.append(torch.sigmoid(net(torch.from_numpy(xnp).to(dev)).squeeze(1)).float().cpu().numpy())
                yl.append(ynp)
        S = np.concatenate(sc); Yva = np.concatenate(yl); V = Yva != 255
        f1 = metrics(Yva[V], (S[V] >= 0.5))["F1"]
        hist.append(dict(epoch=ep, train_loss=round(tot / max(nb, 1), 5), val_F1_at_0p5=f1,
                         vram_gb=round(torch.cuda.max_memory_allocated() / 1e9, 2)))
        if f1 > best:
            best = f1; torch.save(net.state_dict(), RUN / "model_best.pt")
        if ep % 5 == 0 or ep == a.epochs - 1:
            print(f"  ep {ep:3d}  loss {hist[-1]['train_loss']:.4f}  val F1@0.5 {f1:.4f}  best {best:.4f}",
                  flush=True)
    torch.save(net.state_dict(), RUN / "model_last.pt")
    pd.DataFrame(hist).to_csv(RUN / "training_history.csv", index=False)

    # ---- threshold on VALIDATION only, then TEST once -----------------------------------------------------------
    net.load_state_dict(torch.load(RUN / "model_best.pt")); net.eval()
    def score_df(df):
        o = []; yl = []
        with torch.no_grad(), torch.amp.autocast("cuda"):
            for i in range(0, len(df), a.batch):
                xnp, ynp = batch(df, range(i, min(i + a.batch, len(df))))
                o.append(torch.sigmoid(net(torch.from_numpy(xnp).to(dev)).squeeze(1)).float().cpu().numpy())
                yl.append(ynp)
        return np.concatenate(o), np.concatenate(yl)
    Sva, Yva = score_df(va_df); V = Yva != 255
    grid = np.arange(0.05, 0.96, 0.01)
    f1s = [metrics(Yva[V], (Sva[V] >= t))["F1"] for t in grid]
    thr = float(grid[int(np.argmax(f1s))])
    json.dump(dict(threshold=thr, criterion="max F1 on VALIDATION patches", val_F1=max(f1s),
                   never_used=["test F1", "disputed area", "literature area"]),
              open(RUN / "validation_threshold.json", "w"), indent=2)
    print(f"\nthreshold frozen on validation: {thr:.2f} (val F1 {max(f1s):.4f})", flush=True)
    Ste, Yte = score_df(te_df); T = Yte != 255
    m = metrics(Yte[T], (Ste[T] >= thr))
    m["threshold"] = thr; m["n_test_patches"] = int(len(te_df)); m["n_supervised_px"] = int(T.sum())
    json.dump(m, open(RUN / "test_metrics.json", "w"), indent=2)
    print("TEST (evaluated once): " + ", ".join(f"{k} {v}" for k, v in m.items() if k in
                                                ("precision", "recall", "F1", "IoU", "TP", "FP", "FN")), flush=True)

    # ---- disputed: never supervised, reported as candidates ------------------------------------------------------
    dis_rows = []
    for split in ("train", "val", "test"):
        df = C[(C.split == split) & (C.disputed_px > 0)]
        if not len(df):
            continue
        df = df.reset_index(drop=True)
        Sd, _ = score_df(df)
        D = np.stack([disputed[r.row - half:r.row + half, r.col - half:r.col + half] for r in df.itertuples()])
        v = Sd[D]
        if v.size == 0:
            continue
        lab_, n_ = ndimage.label(((Sd >= thr) & D)[0]) if len(Sd) else (None, 0)
        dis_rows.append(dict(split=split, n_disputed_px=int(D.sum()), km2=round(float(D.sum()) * 1e-4, 2),
                             score_p10=round(float(np.percentile(v, 10)), 4),
                             score_median=round(float(np.median(v)), 4),
                             score_p90=round(float(np.percentile(v, 90)), 4),
                             predicted_positive_km2=round(float((v >= thr).sum()) * 1e-4, 3),
                             predicted_positive_pct=round(100 * float((v >= thr).mean()), 2),
                             status="MODEL_SUPPORTED_CANDIDATES_not_recovered_flood"))
    pd.DataFrame(dis_rows).to_csv(RUN / "disputed_score_stats.csv", index=False)
    print("\ndisputed (never supervised):")
    for r in dis_rows:
        print(f"  {r['split']:5s} {r['km2']:7.2f} km2, median score {r['score_median']:.3f}, "
              f"predicted positive {r['predicted_positive_pct']:5.2f} %", flush=True)

    # ---- challenge strata on TEST --------------------------------------------------------------------------------
    ch = []
    BCn = {1: "VEG_AGRI", 2: "BARE_SAND", 3: "BUILT_UP", 4: "WETLAND", 5: "OTHER_DRY"}
    Bte = np.stack([bc[r.row - half:r.row + half, r.col - half:r.col + half] for r in te_df.itertuples()])
    pr = Ste >= thr
    for code, nm in BCn.items():
        sel = T & (Bte == code)
        if sel.sum() < 1000:
            continue
        mm = metrics(Yte[sel], pr[sel])
        ch.append(dict(stratum=nm, n_px=int(sel.sum()), km2=round(float(sel.sum()) * 1e-4, 1), **mm))
    pd.DataFrame(ch).to_csv(RUN / "challenge_metrics.csv", index=False)
    print("\nTEST by pre-event surface:")
    for r in ch:
        print(f"  {r['stratum']:10s} {r['km2']:7.1f} km2  P {r['precision']:.3f}  R {r['recall']:.3f}  "
              f"F1 {r['F1']:.3f}  FP {r['FP']:,}", flush=True)
    json.dump(dict(model="U0_B2_FULL", inputs="p71 orbit-safe S1 only (15 channels)",
                   absent=["Sentinel-2", "HAND", "distance_to_water", "BASE_CLASS", "p73", "TRACE"],
                   patch=PATCH, stride=STRIDE, epochs=a.epochs, batch=a.batch, lr=a.lr, seed=SEED,
                   disputed_policy="IGNORE in loss, threshold, early stopping and tuning",
                   meaning="PASS means a SAR-only U-Net generalises spatially on B2 weak labels; it does NOT mean "
                           "validated flood extent"),
              open(RUN / "config.json", "w"), indent=2)
    print(f"\n{time.time()-t0:.0f}s total -> {RUN.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
