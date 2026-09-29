# New in floodstate-eo, 2026-09-29 (review 2026-09-28, F11). STATUS: ACTIVE. Summarises finished runs; trains nothing.
"""P86s -- training-seed variability of the M6 arms on the corrected labels (v004, v002_notrace).

A single training run is one draw of the optimisation: the weight initialisation, the patch order and the augmentation all
follow the seed. Every arm on the corrected labels is trained with three seeds (p86 --seed; the first seed has no run suffix)
on the SAME split, labels and recipe, so the spread across seeds is the training noise that a between-arm difference must
exceed before it is read as an input effect. Nothing is re-thresholded: each run keeps its own frozen validation threshold.

Per labels x arm x endpoint (D1 + amendment, eval_d1a/endpoints.csv): the value of every seed, mean, SD, min, max, range.
Per labels x comparison x endpoint (p88 paired block bootstrap of each seed's pair): the median and 95 % interval of every
seed, how many seeds exclude zero and whether all seeds agree in sign.

Outputs: <case_study>/tables/m6_seed_summary.csv, m6_seed_paired.csv
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from floodstate_eo import _kakhovka_legacy_config as CFG

RUNS = Path(__file__).resolve().parents[2] / "runs"
SEEDS = (20260923, 20261001, 20261002)
SETS = {"v004": ("v004", ("U0d", "U1", "U2", "U2b")), "v002_notrace": ("v002nt", ("U2",))}
PAIRS = {"v004": (("U0d", "U2"), ("U0d", "U1"), ("U2", "U2b"))}


def run_dir(arm, run, seed):
    return RUNS / (f"{arm}_B1B2_{run}" + ("" if seed == SEEDS[0] else f"_s{seed}"))


def main():
    rows, prs = [], []
    for lab, (run, arms) in SETS.items():
        for arm in arms:
            vals = {}
            for sd in SEEDS:
                p = run_dir(arm, run, sd) / "eval_d1a" / "endpoints.csv"
                if p.exists():
                    assert json.loads((p.parents[1] / "config.json").read_text())["seed"] == sd, p
                    vals[sd] = pd.to_numeric(pd.read_csv(p, index_col=0).value, errors="coerce")
            if not vals:
                continue
            V = pd.DataFrame(vals)
            for ep, r in V.iterrows():
                x = r.dropna().to_numpy(float)
                if not len(x):                                         # text rows (arm, status) and endpoints undefined in every seed
                    continue
                rows.append(dict(labels=lab, arm=arm, endpoint=ep, n_seeds=len(x), **{f"s{sd}": r.get(sd, np.nan) for sd in SEEDS},
                                 mean=x.mean() if len(x) else np.nan, sd=x.std(ddof=1) if len(x) > 1 else np.nan,
                                 min=x.min() if len(x) else np.nan, max=x.max() if len(x) else np.nan,
                                 range=(x.max() - x.min()) if len(x) else np.nan))
        for a, b in PAIRS.get(lab, ()):
            per = {}
            for sd in SEEDS:
                p = RUNS / (f"compare_{a}_vs_{b}_{run}" + ("" if sd == SEEDS[0] else f"_s{sd}")) / "paired_bootstrap.csv"
                if p.exists():
                    per[sd] = pd.read_csv(p, index_col=0)
            if not per:
                continue
            for ep in per[next(iter(per))].index:
                d = {sd: per[sd].loc[ep] for sd in per if ep in per[sd].index}
                ex = [bool(v["lo"] > 0 or v["hi"] < 0) for v in d.values()]; sg = {int(np.sign(v["median"])) for v in d.values()}
                prs.append(dict(labels=lab, comparison=f"{b} - {a}", endpoint=ep, n_seeds=len(d),
                                **{f"s{sd}_{k}": d[sd][k] if sd in d else np.nan for sd in SEEDS for k in ("median", "lo", "hi")},
                                n_seeds_excluding_zero=int(sum(ex)), same_sign_all_seeds=len(sg - {0}) <= 1 and 0 not in sg))
    S = pd.DataFrame(rows); P = pd.DataFrame(prs)
    S.to_csv(CFG.TABLES / "m6_seed_summary.csv", index=False); P.to_csv(CFG.TABLES / "m6_seed_paired.csv", index=False)
    pd.set_option("display.width", 250)
    key = ["G_F1", "G_IoU", "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2", "B_recall_flooded_open_low_veg", "BU_FP_area_km2"]
    if len(S):
        print(S[S.endpoint.isin(key)].round(4).to_string(index=False))
    if len(P):
        print(P[P.endpoint.isin(key)][["labels", "comparison", "endpoint", "n_seeds", "n_seeds_excluding_zero", "same_sign_all_seeds"]].to_string(index=False))
    print("-> tables/m6_seed_summary.csv, m6_seed_paired.csv")


if __name__ == "__main__":
    main()
