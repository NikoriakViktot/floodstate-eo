# New in floodstate-eo, 2026-09-23. STATUS: ACTIVE_DIAGNOSTIC. Runs AFTER m6_labels_v002 is frozen; changes nothing.
"""P77b -- what moved between label contract v001 (p75's rule) and m6_labels_v002, and how much BASE_CLASS explains.

Kept out of p77 on purpose: p77 must provably never open a land-cover layer. This file reads p69b (to rebuild v001) and
p69a (BASE_CLASS, as a leakage indicator) only after v002 exists on disk.

LEAKAGE INDICATOR. BASE_CLASS alone ranked v001 at AUC 0.955. Against v002 the same number measures physical
association only (flooding is not uniform across surface types), since BASE_CLASS no longer decides the target;
a lower value is expected but not required, and it is reported, not gated.

Outputs: <case_study>/tables/p77b_labels_v002_vs_v001.csv, p77b_baseclass_association.csv
"""
from __future__ import annotations
import argparse, importlib.util
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

HERE = Path(__file__).resolve().parent
OUT = CFG.BULK_ROOT / "frames10"
PX = 1e-4
BASE = {0: "PRE_EXISTING_WATER", 1: "VEG_AGRI", 2: "BARE_SAND", 3: "BUILT_UP", 4: "WETLAND", 5: "OTHER_DRY",
        6: "UNCERTAIN_BASE"}


def rd(fid, name, band=1):
    with rasterio.open(OUT / fid / name) as s:
        return s.read(band)


def auc_by_class(cls, y):
    """AUC of a categorical predictor: each class scored by its own positive rate (the best any model using only
    this layer could do), ties handled by average rank."""
    from scipy.stats import rankdata
    m = (y == 0) | (y == 1)
    c, t = cls[m], y[m]
    rate = {k: t[c == k].mean() for k in np.unique(c)}
    s = np.vectorize(rate.get)(c).astype("f8")
    r = rankdata(s); n1 = int(t.sum()); n0 = t.size - n1
    return float((r[t == 1].sum() - n1 * (n1 + 1) / 2) / max(n0 * n1, 1)), float(t.mean())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=["B2", "B1"]); a = ap.parse_args()
    s = importlib.util.spec_from_file_location("p77", HERE / "p77_m6_labels_v002.py")
    P77 = importlib.util.module_from_spec(s); s.loader.exec_module(P77)
    V, A = [], []
    for fid in a.frames:
        F = CG.frame_grid(fid)
        y2 = rd(fid, "m6_labels_v002.tif", 1)
        lab = rd(fid, "labels.tif"); sem = rd(fid, "p69b_semantic_state.tif"); bc = rd(fid, "p69a_base_class.tif")
        s1w = P77.s1_peak(fid, F); m2v1 = np.isin(sem, (1, 2, 3, 4, 5))
        y1 = np.full(lab.shape, 255, np.uint8); y1[lab == 0] = 0; y1[(lab == 1) & s1w & m2v1] = 1
        y1[s1w & ~m2v1] = 255
        for a_ in (1, 0, 255):
            for b_ in (1, 0, 255):
                V.append(dict(frame=fid, v001=a_, v002=b_, km2=round(float(((y1 == a_) & (y2 == b_)).sum()) * PX, 3)))
        for nm, yy in (("v001", y1), ("v002", y2)):
            auc, prev = auc_by_class(bc, yy)
            A.append(dict(frame=fid, labels=nm, baseclass_only_auc=round(auc, 4), prevalence=round(prev, 4)))
        for code, cn in BASE.items():
            m = bc == code
            A.append(dict(frame=fid, labels="v002_by_class", base_class=cn,
                          flood_km2=round(float(((y2 == 1) & m).sum()) * PX, 2),
                          nonflood_km2=round(float(((y2 == 0) & m).sum()) * PX, 2),
                          v001_flood_km2=round(float(((y1 == 1) & m).sum()) * PX, 2)))
        print(pd.DataFrame([r for r in A if r["frame"] == fid and "baseclass_only_auc" in r]).to_string(index=False))
    pd.DataFrame(V).to_csv(CFG.TABLES / "p77b_labels_v002_vs_v001.csv", index=False)
    pd.DataFrame(A).to_csv(CFG.TABLES / "p77b_baseclass_association.csv", index=False)
    print("-> <case_study>/tables/p77b_{labels_v002_vs_v001,baseclass_association}.csv")


if __name__ == "__main__":
    main()
