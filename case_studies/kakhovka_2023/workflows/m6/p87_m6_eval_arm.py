# New in floodstate-eo, 2026-09-24. STATUS: ACTIVE. Re-evaluates a FINISHED arm from its stored scores; trains nothing.
"""P87 -- D1 + amendment (A1/A2) evaluation of an existing arm from its full-frame score rasters and FROZEN threshold.

Used for U0d, whose TEST was computed before the 2026-09-24 D1 amendment: the model, the scores and the validation
threshold are the ones already on disk; nothing is refitted, re-thresholded or re-selected. The original
test_endpoints.csv is left untouched; the amended evaluation goes to runs/<ARM>_B1B2_v1/eval_d1a/, and a note records
that A2 was computed post hoc for this arm (pre-registered for every later arm).

Stage 2 of the review (2026-09-29): `--run <dir> [--labels K] [--p73-rev R]` re-evaluates any finished run against another
reference label set and/or the RF20 rev-2 strata (F08), into runs/<dir>/eval_d1a_ref<K>_p73rev<R>/ -- so arms trained on
different label versions can be compared on one reference and one stratification. The run's own eval_d1a is never touched.
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
    ap = argparse.ArgumentParser(); ap.add_argument("--arm", help="v1 run of this arm (the original use: U0d, post hoc D1 amendment)")
    ap.add_argument("--run", help="any finished run directory under runs/, e.g. U2_B1B2_v003A (review 2026-09-28, stage 2)")
    ap.add_argument("--labels", default=None, help="reference labels of the evaluation (p86 LABELS key); default: the run's own")
    ap.add_argument("--p73-rev", type=int, default=None, choices=[1, 2], help="RF20 strata; default: the run's own (config p73_rev, else 1)")
    a = ap.parse_args()
    E, P84, P86 = _load("m6_eval"), _load("p84_m6_split_b1b2"), _load("p86_m6_train_arm")
    rn = a.run or f"{a.arm}_B1B2_v1"; run = HERE.parents[1] / "runs" / rn
    cfg = json.loads((run / "config.json").read_text()); arm = cfg["arm"]
    own = next(k for k, v in P86.LABELS.items() if v["file"].replace(".tif", "") == cfg["labels"])
    lab = a.labels or own; rev = a.p73_rev or int(cfg.get("p73_rev", 1))
    default = lab == own and rev == int(cfg.get("p73_rev", 1))
    out = "eval_d1a" if default else f"eval_d1a_ref{lab.replace('_', '')}_p73rev{rev}"        # a re-evaluation never overwrites the run's own
    thr = json.loads((run / "validation_threshold.json").read_text())["threshold"]
    arm_, suffix = rn.split("_B1B2_"); score_name = f"{arm_}_score.tif" if suffix == "v1" else f"{arm_}_{suffix}_score.tif"
    D = {}
    for f in P86.FRAMES:
        F = CG.frame_grid(f)
        with rasterio.open(OUT / f / "s1_change.tif") as s:
            desc = list(s.descriptions)
            ne, d0 = s.read(desc.index("n_valid_event") + 1), s.read(1)
        has = (ne > 0) & (d0 != P86.ND)
        with rasterio.open(OUT / f / "m6" / score_name) as s:
            q = s.read(1)
        score = np.where(q == 65535, np.nan, q / 10000.0).astype("f4")
        role = P86.read(f, f"{P86.SPLIT}_role.tif", 1)[0]
        y = P86.labels_10m(f, lab)
        y = np.where(np.isin(role, (1, 2, 3)) & has, y, 255).astype(np.uint8)
        gx = F["transform"].c + 10.0 * np.arange(F["nx"]); gy = F["transform"].f - 10.0 * np.arange(F["ny"])
        blk = np.floor(gy / P84.BLOCK_M).astype("i8")[:, None] * 100000 + np.floor(gx / P84.BLOCK_M).astype("i8")[None, :]
        D[f] = dict(score=score, y=y, p73=P84.p73_10m(f, F, rev), role=role, has=has, blk=blk)
    ep, byf, curve = E.evaluate_arm(run, arm, D, thr, out_name=out)
    if a.arm and default:
        (run / out / "NOTE.txt").write_text(
            "D1 amendment (2026-09-24: A1 supervised / A2 challenge) evaluated by p87 from the stored scores and the frozen "
            f"validation threshold {thr}. For {arm} this is POST HOC (its TEST was first read before the amendment); "
            "no model, score or threshold was changed. For later arms the amendment is pre-registered.\n")
    else:
        (run / out / "NOTE.txt").write_text(
            f"Re-evaluation by p87 (2026-09-29, review stage 2) of the stored scores at the frozen validation threshold {thr}: reference labels "
            f"{lab} (the run was trained on {own}), RF20 strata rev {rev}. Nothing was refitted or re-thresholded; the TEST geography is the frozen split.\n")
    import pandas as pd
    print(pd.Series(ep).to_string()); print(byf.T.to_string()); print(curve.to_string(index=False)); print(f"-> runs/{rn}/{out}/")

if __name__ == "__main__":
    main()
