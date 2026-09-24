# New in floodstate-eo, 2026-09-24. STATUS: ACTIVE. Re-evaluates a FINISHED arm from its stored scores; trains nothing.
"""P87 -- D1 + amendment (A1/A2) evaluation of an existing arm from its full-frame score rasters and FROZEN threshold.

Used for U0d, whose TEST was computed before the 2026-09-24 D1 amendment: the model, the scores and the validation
threshold are the ones already on disk; nothing is refitted, re-thresholded or re-selected. The original
test_endpoints.csv is left untouched; the amended evaluation goes to runs/<ARM>_B1B2_v1/eval_d1a/, and a note records
that A2 was computed post hoc for this arm (pre-registered for every later arm).
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np, rasterio
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

HERE = Path(__file__).resolve().parent
OUT = CFG.BULK_ROOT / "frames10"


def _load(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--arm", required=True); a = ap.parse_args()
    E, P84, P86 = _load("m6_eval"), _load("p84_m6_split_b1b2"), _load("p86_m6_train_arm")
    run = HERE.parents[1] / "runs" / f"{a.arm}_B1B2_v1"
    thr = json.loads((run / "validation_threshold.json").read_text())["threshold"]
    D = {}
    for f in P86.FRAMES:
        F = CG.frame_grid(f)
        with rasterio.open(OUT / f / "s1_change.tif") as s:
            desc = list(s.descriptions)
            ne, d0 = s.read(desc.index("n_valid_event") + 1), s.read(1)
        has = (ne > 0) & (d0 != P86.ND)
        with rasterio.open(OUT / f / "m6" / f"{a.arm}_score.tif") as s:
            q = s.read(1)
        score = np.where(q == 65535, np.nan, q / 10000.0).astype("f4")
        role = P86.read(f, f"{P86.SPLIT}_role.tif", 1)[0]
        y = P86.read(f, "m6_labels_v002.tif", 1)[0]
        y = np.where(np.isin(role, (1, 2, 3)) & has, y, 255).astype(np.uint8)
        gx = F["transform"].c + 10.0 * np.arange(F["nx"]); gy = F["transform"].f - 10.0 * np.arange(F["ny"])
        blk = np.floor(gy / P84.BLOCK_M).astype("i8")[:, None] * 100000 + np.floor(gx / P84.BLOCK_M).astype("i8")[None, :]
        D[f] = dict(score=score, y=y, p73=P84.p73_10m(f, F), role=role, has=has, blk=blk)
    ep, byf, curve = E.evaluate_arm(run, a.arm, D, thr)
    (run / "eval_d1a" / "NOTE.txt").write_text(
        "D1 amendment (2026-09-24: A1 supervised / A2 challenge) evaluated by p87 from the stored scores and the frozen "
        f"validation threshold {thr}. For {a.arm} this is POST HOC (its TEST was first read before the amendment); "
        "no model, score or threshold was changed. For later arms the amendment is pre-registered.\n")
    import pandas as pd
    print(pd.Series(ep).to_string()); print(byf.T.to_string()); print(curve.to_string(index=False))


if __name__ == "__main__":
    main()
