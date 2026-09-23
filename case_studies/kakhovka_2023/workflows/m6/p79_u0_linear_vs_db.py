# Provenance: SWOT-DNIPRO scripts/p79_u0_linear_vs_db.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: LEGACY -- one-off forensic comparison of the linear-gamma0 U0 (SUPERSEDED) against the dB U0; documents the unit error, not an ablation.
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P79 -- what did correcting the change operator actually buy, and where?

A PAIRED PIPELINE COMPARISON, NOT A SINGLE-FACTOR ABLATION. Legacy U0 and corrected U0 share their seed, their
10 km block split, their 406-patch manifest, their loss, their schedule and their threshold rule; they differ in
the definition of the input features. Each model must therefore be scored on ITS OWN stack -- the legacy weights
against the archived linear-gamma0 stack, the corrected weights against the dB stack -- because a model evaluated
on features it was not fitted to measures nothing. The test GEOGRAPHY is identical, which is what makes the
comparison paired and what lets the difference be bootstrapped over shared blocks.

THE PREDICTION THIS TEST EXISTS TO FALSIFY, recorded before the numbers were seen: p78's label-free null found the
agricultural flood signature in the INCREASE channel (real/null 1.304) while the decrease channel was weaker than
manufactured noise (0.687), and wetland detected in both directions (1.495 / 2.435). A log-ratio raises the
relative weight of change over dark surfaces, so if p78 is right the correction should lift VEG_AGRI more than
WETLAND, and may cost a little on WETLAND, which the linear operator over-represented. If instead every stratum
rises by a similar amount, the gain is better quantisation rather than a better operator -- a different and much
weaker conclusion, and it must be reported as such.

PRIMARY ENDPOINTS: per-stratum recall and PR-AUC, with N positives stated. Global F1 is reported but is not an
endpoint: 95.6 % of the positive test support is WETLAND, so it is a wetland metric (SRC-84).

Outputs: outputs/tables/p79_linear_vs_db_by_stratum.csv
         outputs/tables/p79_linear_vs_db_paired_bootstrap.csv
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from sklearn.metrics import average_precision_score
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
FID = "B2"; PATCH = 512; SCALE = 100.0; ND = -32768; BOOT = 2000
PEAK = ("2023-06-09", "2023-06-13", "2023-06-14")
ARMS = {"LINEAR_legacy": ("U0_B2", "SUPERSEDED_linear_domain_s1_change.tif"),
        "dB_corrected": ("U0_B2_CORRECTED", "s1_change.tif")}
BCn = {0: "PRE_WATER", 1: "VEG_AGRI", 2: "BARE_SAND", 3: "BUILT_UP", 4: "WETLAND", 5: "OTHER_DRY"}


def load_stack(name, norm):
    with rasterio.open(OUT / FID / name) as s:
        CH = list(s.descriptions); X = s.read().astype("f4")
    X[X == ND] = np.nan
    for i, c in enumerate(CH):
        if not c.startswith("n_"):
            X[i] /= SCALE
    med = np.array(norm["median"])[:, None, None]; iqr = np.array(norm["iqr"])[:, None, None]
    return np.nan_to_num((X - med) / iqr, nan=0.0).astype("f4"), CH


def metrics(yt, pr):
    tp = int((pr & (yt == 1)).sum()); fp = int((pr & (yt == 0)).sum()); fn = int((~pr & (yt == 1)).sum())
    P = tp / max(tp + fp, 1); R = tp / max(tp + fn, 1)
    return dict(TP=tp, FP=fp, FN=fn, precision=round(P, 5), recall=round(R, 5),
                F1=round(2 * P * R / max(P + R, 1e-9), 5))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--batch", type=int, default=6)
    a = ap.parse_args()
    import torch, segmentation_models_pytorch as smp
    F = CG.frame_grid(FID); half = PATCH // 2
    with rasterio.open(OUT / FID / "labels.tif") as s:
        lab = s.read(1)
    with rasterio.open(OUT / FID / "p69b_semantic_state.tif") as s:
        sem = s.read(1)
    with rasterio.open(OUT / FID / "p69a_base_class.tif") as s:
        bc = s.read(1)
    z = np.load(CFG.S1_CACHE / "ZONE_2_KHERSON_DELTA_flood_june2023" / "per_scene_water.npz", allow_pickle=True)
    shp = tuple(int(v) for v in z["shape"]); cell = float(z["cell"])
    tr = from_origin(float(z["x0"]), float(z["y1"]), cell, cell); wet = np.zeros(shp, bool)
    for k in [k for k in z.keys() if k[:4] == "2023" and not k.startswith("valid_")]:
        if k[:10] not in PEAK:
            continue
        wet |= (np.unpackbits(z[k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
                & np.unpackbits(z["valid_" + k], count=shp[0] * shp[1]).astype(bool).reshape(shp))
    d = np.zeros((F["ny"], F["nx"]), "u1")
    reproject(source=wet.astype("u1"), destination=d, src_transform=tr, src_crs=CFG.CRS_METRIC,
              dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest,
              src_nodata=0, dst_nodata=0)
    s1w = d.astype(bool); m2 = np.isin(sem, (1, 2, 3, 4, 5))
    y = np.full((F["ny"], F["nx"]), 255, np.uint8)
    y[lab == 0] = 0
    y[(lab == 1) & s1w & m2] = 1
    y[s1w & ~m2] = 255

    man = {k: pd.read_csv(ROOT / "runs" / v[0] / "split_manifest.csv") for k, v in ARMS.items()}
    ref = man["LINEAR_legacy"][["row", "col", "split"]].sort_values(["row", "col"]).reset_index(drop=True)
    for k, m in man.items():
        got = m[["row", "col", "split"]].sort_values(["row", "col"]).reset_index(drop=True)
        if not ref.equals(got):
            raise SystemExit(f"{k}: split manifest differs -- the comparison would not be paired")
    te = man["LINEAR_legacy"]
    te = te[te.split == "test"].reset_index(drop=True)
    print(f"paired on {len(ref)} patches, {len(te)} in TEST; split manifests identical across arms", flush=True)

    S = {}
    for arm, (run, stack) in ARMS.items():
        R = ROOT / "runs" / run
        X, CH = load_stack(stack, json.load(open(R / "normalization.json")))
        thr = json.load(open(R / "validation_threshold.json"))["threshold"]
        net = smp.Unet("resnet34", encoder_weights=None, in_channels=len(CH), classes=1).cuda()
        net.load_state_dict(torch.load(R / "model_best.pt")); net.eval()
        o = []
        with torch.no_grad(), torch.amp.autocast("cuda"):
            for i in range(0, len(te), a.batch):
                idx = range(i, min(i + a.batch, len(te)))
                xs = np.stack([X[:, te.iloc[j].row - half:te.iloc[j].row + half,
                                 te.iloc[j].col - half:te.iloc[j].col + half] for j in idx])
                o.append(torch.sigmoid(net(torch.from_numpy(xs).cuda()).squeeze(1)).float().cpu().numpy())
        S[arm] = (np.concatenate(o), thr)
        del X, net; torch.cuda.empty_cache()
        print(f"  {arm}: scored, threshold {thr:.2f}", flush=True)

    Y = np.stack([y[r.row - half:r.row + half, r.col - half:r.col + half] for r in te.itertuples()])
    B = np.stack([bc[r.row - half:r.row + half, r.col - half:r.col + half] for r in te.itertuples()])
    T = Y != 255
    rows = []
    for k, nm in BCn.items():
        sel = T & (B == k)
        npos = int((Y[sel] == 1).sum())
        if sel.sum() < 1000 or npos == 0:
            continue
        r = dict(stratum=nm, km2=round(float(sel.sum()) * 1e-4, 1), n_positive=npos,
                 prevalence=round(npos / sel.sum(), 5), support_limited=bool(npos < 5000))
        for arm, (sc, thr) in S.items():
            m = metrics(Y[sel], sc[sel] >= thr)
            r[f"{arm}_R"] = m["recall"]; r[f"{arm}_P"] = m["precision"]; r[f"{arm}_F1"] = m["F1"]
            r[f"{arm}_AP"] = round(float(average_precision_score((Y[sel] == 1).astype("u1"), sc[sel])), 5)
        r["dR"] = round(r["dB_corrected_R"] - r["LINEAR_legacy_R"], 5)
        r["dAP"] = round(r["dB_corrected_AP"] - r["LINEAR_legacy_AP"], 5)
        rows.append(r)
    D = pd.DataFrame(rows)
    D.to_csv(CFG.TABLES / "p79_linear_vs_db_by_stratum.csv", index=False)
    print("\n" + D.to_string(index=False))

    # paired spatial-block bootstrap: resample TEST BLOCKS, form the difference inside each resample.
    # The p75 manifest carries no block column, and falling back to one-block-per-patch would be silently wrong:
    # patches overlap at stride 128, so the same ground would enter a resample several times as if independent.
    # The block id is therefore recovered from the fold raster, which is the same lattice the split used.
    with rasterio.open(OUT / FID / "folds.tif") as s:
        fb = s.read(5)
    blk = np.array([np.bincount(fb[r.row - half:r.row + half, r.col - half:r.col + half].ravel()
                                [fb[r.row - half:r.row + half, r.col - half:r.col + half].ravel() > 0]).argmax()
                    for r in te.itertuples()])
    if len(np.unique(blk)) < 3:
        raise SystemExit(f"only {len(np.unique(blk))} distinct test blocks recovered -- a block bootstrap needs "
                         f"more resampling units than that; do not silently fall back to patches")
    ub = np.unique(blk); rng = np.random.default_rng(20260923)
    out = []
    for k, nm in BCn.items():
        sel_all = T & (B == k)
        if sel_all.sum() < 1000 or (Y[sel_all] == 1).sum() == 0:
            continue
        per = []
        for b in ub:
            w = np.isin(blk, [b]); s_ = sel_all[w]
            if s_.sum() == 0 or (Y[w][s_] == 1).sum() == 0:
                continue
            yy = Y[w][s_]
            c = [int((yy == 1).sum())]
            for arm, (sc, thr) in S.items():
                p = sc[w][s_] >= thr
                c += [int((p & (yy == 1)).sum()), int((p & (yy == 0)).sum())]
            per.append(c)
        if len(per) < 3:
            continue
        dR = np.empty(BOOT)
        for it in range(BOOT):
            pick = rng.integers(0, len(per), len(per))
            pos = sum(per[i][0] for i in pick)
            t0 = sum(per[i][1] for i in pick); t1 = sum(per[i][3] for i in pick)
            dR[it] = t1 / max(pos, 1) - t0 / max(pos, 1)
        out.append(dict(stratum=nm, n_blocks=len(per), dR=round(float(dR.mean()), 5),
                        dR_lo=round(float(np.percentile(dR, 2.5)), 5),
                        dR_hi=round(float(np.percentile(dR, 97.5)), 5),
                        excludes_zero=bool(np.percentile(dR, 2.5) > 0 or np.percentile(dR, 97.5) < 0)))
    E = pd.DataFrame(out); E.to_csv(CFG.TABLES / "p79_linear_vs_db_paired_bootstrap.csv", index=False)
    print("\npaired spatial-block bootstrap, dB - linear (recall):")
    print(E.to_string(index=False))
    va = E[E.stratum == "VEG_AGRI"]; we = E[E.stratum == "WETLAND"]
    if len(va) and len(we):
        print(f"\np78 predicted VEG_AGRI to gain more than WETLAND: "
              f"dR_VEG {va.dR.iloc[0]:+.4f} vs dR_WET {we.dR.iloc[0]:+.4f} -> "
              f"{'CONSISTENT' if va.dR.iloc[0] > we.dR.iloc[0] else 'NOT CONSISTENT'}")


if __name__ == "__main__":
    main()
