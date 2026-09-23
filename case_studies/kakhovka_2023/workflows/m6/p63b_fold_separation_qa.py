# Provenance: SWOT-DNIPRO scripts/p63b_fold_separation_qa.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: ACTIVE_DIAGNOSTIC -- fold separation QA.
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P63b -- how far is a test cell actually from the nearest training cell? A 5 km block is not a 5 km separation.

Adjacent blocks touch. A test cell on a block edge can sit tens of metres from a training cell on the other side,
and with a predictor autocorrelation range near 3.5 km the signal crosses that boundary freely. Calling such a
design "spatially separated by 5 km" would be false; calling it spatial block cross-validation is accurate. This
script measures which sentence we are entitled to write.

Per outer fold, over the LABELLED population only (a cell with no label supervises nothing, so its distance is
irrelevant): the minimum, 10th-percentile and median distance from a test-labelled cell to the nearest
training-labelled cell, and the share of test cells whose nearest training cell is closer than 1, 2, 3.5 and 5 km.

Distances come from a Euclidean distance transform of the training mask on the shared canonical lattice, which is
exact to the cell and needs no neighbour search over 22 million points. B1 and B2 are stitched into one array on a
common 40 m grid: the question is answered at kilometre scale, and a 40 m posting keeps a 3 700 x 4 000 raster in
memory while leaving the sub-100 m tail resolvable.

Output: outputs/tables/p63b_fold_separation.csv
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from scipy import ndimage
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
FRAMES = ("B1", "B2")
COARSE = 40.0
THR = (1000.0, 2000.0, 3500.0, 5000.0)


def main():
    x0 = min(CG.frame_grid(f)["x0"] for f in FRAMES); x1 = max(CG.frame_grid(f)["x1"] for f in FRAMES)
    y0 = min(CG.frame_grid(f)["y0"] for f in FRAMES); y1 = max(CG.frame_grid(f)["y1"] for f in FRAMES)
    nx = int(round((x1 - x0) / COARSE)); ny = int(round((y1 - y0) / COARSE))
    tr = from_origin(x0, y1, COARSE, COARSE)
    print(f"stitched grid {ny} x {nx} at {COARSE:.0f} m  ({x0:,.0f}..{x1:,.0f}, {y0:,.0f}..{y1:,.0f})")

    fold = np.zeros((ny, nx), np.int16)          # 0 = not in the labelled population
    for fid in FRAMES:
        F = CG.frame_grid(fid)
        with rasterio.open(OUT / fid / "labels.tif") as s:
            L = s.read(1)
        with rasterio.open(OUT / fid / "folds.tif") as s:
            own = s.read(1).astype(bool); fo = s.read(2)
        m = own & ((L == 0) | (L == 1)) & (fo > 0)
        src = np.where(m, fo, 0).astype(np.int16)
        dst = np.zeros((ny, nx), np.int16)
        # MAX, not nearest: downsampling a sparse mask with nearest would drop labelled cells and understate the
        # population. Any 40 m cell containing a labelled 10 m cell counts as labelled.
        reproject(source=src, destination=dst, src_transform=F["transform"], src_crs=CFG.CRS_METRIC,
                  dst_transform=tr, dst_crs=CFG.CRS_METRIC, resampling=Resampling.max,
                  src_nodata=0, dst_nodata=0)
        fold = np.where(dst > 0, dst, fold)
    n_lab = int((fold > 0).sum())
    print(f"labelled population on the coarse grid: {n_lab:,} cells "
          f"({n_lab*COARSE*COARSE/1e6:,.0f} km2)\n")

    rows = []
    for k in sorted(set(fold[fold > 0].tolist())):
        test = fold == k
        train = (fold > 0) & ~test
        d = ndimage.distance_transform_edt(~train, sampling=COARSE)[test]
        r = dict(outer_fold=int(k), n_test_cells=int(test.sum()),
                 test_km2=round(float(test.sum()) * COARSE * COARSE / 1e6, 1),
                 min_m=round(float(d.min()), 1), p10_m=round(float(np.percentile(d, 10)), 1),
                 median_m=round(float(np.median(d)), 1), p90_m=round(float(np.percentile(d, 90)), 1),
                 max_m=round(float(d.max()), 1))
        for t in THR:
            r[f"pct_train_within_{t/1000:g}km"] = round(100 * float((d < t).mean()), 2)
        # IS A BUFFERED CV EVEN FEASIBLE? Removing every training cell within `t` of any test cell is the standard
        # remedy, but it is only a remedy if training data survives it. Measured here rather than assumed.
        dtest = ndimage.distance_transform_edt(~test, sampling=COARSE)
        n_tr = float(train.sum())
        for t in (2000.0, 3500.0):
            keep = train & (dtest >= t)
            r[f"train_kept_at_{t/1000:g}km_buffer_pct"] = round(100 * float(keep.sum()) / n_tr, 2)
            r[f"train_kept_at_{t/1000:g}km_buffer_km2"] = round(float(keep.sum()) * COARSE * COARSE / 1e6, 1)
        rows.append(r)
        print(f"  fold {k}: min {r['min_m']:>6.0f} m, p10 {r['p10_m']:>7.0f} m, median {r['median_m']:>7.0f} m | "
              + ", ".join(f"<{t/1000:g} km {r[f'pct_train_within_{t/1000:g}km']:5.1f} %" for t in THR)
              + f" | train kept at 2 km {r['train_kept_at_2km_buffer_pct']:5.1f} %, "
                f"at 3.5 km {r['train_kept_at_3.5km_buffer_pct']:5.1f} %", flush=True)
    D = pd.DataFrame(rows); D.to_csv(CFG.TABLES / "p63b_fold_separation.csv", index=False)
    med = D[f"pct_train_within_3.5km"].median()
    print(f"\nmedian over folds: {med:.1f} % of test cells have a training cell within 3.5 km "
          f"(the predictor autocorrelation range)")
    print("VERDICT: " + ("the design is spatial block CV and must NOT be described as separated by 5 km; "
                         "run the buffered-CV sensitivity" if med > 10 else
                         "blocks are effectively separated at the autocorrelation scale"))
    print("-> outputs/tables/p63b_fold_separation.csv")


if __name__ == "__main__":
    main()
