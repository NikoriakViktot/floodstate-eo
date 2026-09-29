# New in floodstate-eo, 2026-09-24. STATUS: ACTIVE. Paired comparison of two finished arms; trains nothing.
"""P88 -- arm B vs arm A on the frozen m6_split_v1 TEST: side-by-side D1 (+ A1/A2) endpoints per frame and pooled,
and the paired spatial-block bootstrap of B - A (physical blocks, 2000 resamples). Reads only eval_d1a/ outputs.

Output: runs/compare_<A>_vs_<B>[_<run>]/{pooled.csv, by_frame.csv, paired_bootstrap.csv}
"""
from __future__ import annotations
import argparse, importlib.util
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
RUNS = HERE.parents[1] / "runs"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--run", default="v1", help="run-directory suffix: v1 (v002 labels), v003A, v004, v004_s<seed>, v002nt ...")
    ap.add_argument("--dir-a", help="evaluation directory of A under runs/ (e.g. U2_B1B2_v003A/eval_d1a_refv004_p73rev2); overrides --run")
    ap.add_argument("--dir-b", help="evaluation directory of B under runs/"); ap.add_argument("--out", help="comparison directory name under runs/")
    x = ap.parse_args()
    s = importlib.util.spec_from_file_location("m6_eval", HERE / "m6_eval.py")
    E = importlib.util.module_from_spec(s); s.loader.exec_module(E)
    ra = RUNS / x.dir_a if x.dir_a else RUNS / f"{x.a}_B1B2_{x.run}" / "eval_d1a"
    rb = RUNS / x.dir_b if x.dir_b else RUNS / f"{x.b}_B1B2_{x.run}" / "eval_d1a"
    for r_ in (ra, rb):                                                   # both sides must be scored on the same TEST geography
        assert (r_ / "blocks.csv").exists(), r_
    od = RUNS / (x.out or (f"compare_{x.a}_vs_{x.b}" + ("" if x.run == "v1" else f"_{x.run}"))); od.mkdir(exist_ok=True)
    (od / "SOURCES.txt").write_text(f"A = {ra.relative_to(RUNS)}\nB = {rb.relative_to(RUNS)}\n")
    pa = pd.read_csv(ra / "endpoints.csv", index_col=0).value
    pb = pd.read_csv(rb / "endpoints.csv", index_col=0).value
    P = pd.DataFrame({x.a: pa, x.b: pb}); P.to_csv(od / "pooled.csv")
    fa, fb = pd.read_csv(ra / "by_frame.csv"), pd.read_csv(rb / "by_frame.csv")
    F = pd.concat([fa.assign(arm=x.a), fb.assign(arm=x.b)]).set_index(["arm", "frame"]).T
    F.to_csv(od / "by_frame.csv")
    PB = E.paired_bootstrap(pd.read_csv(ra / "blocks.csv"), pd.read_csv(rb / "blocks.csv"))
    PB.to_csv(od / "paired_bootstrap.csv")
    keys = ["A_FP_area_dry_cropland_km2", "A1_isolated_field_FP_km2",
            "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2", "A2_isolated_field_like_km2",
            "B_recall_flooded_open_low_veg", "B_IoU_open_low_veg", "C_recall_flooded_cropland_LOWN",
            "W_IoU", "BU_FP_area_km2", "G_F1", "G_IoU"]
    print(P.loc[[k for k in keys + ["threshold"] if k in P.index]].to_string())
    print(F.loc[[k for k in keys if k in F.index]].to_string())
    print(f"\npaired block bootstrap, {x.b} - {x.a}:")
    print(PB.loc[[k for k in keys if k in PB.index]].round(4).to_string())


if __name__ == "__main__":
    main()
