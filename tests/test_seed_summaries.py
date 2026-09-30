"""D-SEEDS (maintainer, 2026-09-29): the per-seed summary of the attribution comparisons (T07s) is exactly the T07b rows of the
three training seeds, with the count of seeds whose interval excludes zero and the sign agreement derived from them."""
from pathlib import Path

import numpy as np
import pandas as pd

PT = Path(__file__).resolve().parents[1] / "case_studies/kakhovka_2023/publication/tables"
SEEDS = (20260923, 20261001, 20261002)
PAIRS = {"v004 - v002_notrace (U2)": ("U2_B1B2_v002nt", "U2_B1B2_v004"), "U2 - U0d (v004)": ("U0d_B1B2_v004", "U2_B1B2_v004"),
         "U2b - U2 (v004)": ("U2_B1B2_v004", "U2b_B1B2_v004")}


def test_t07s_is_t07b_per_seed():
    S, B = pd.read_csv(PT / "T07s.csv"), pd.read_csv(PT / "T07b.csv")
    assert len(S) > 0
    for _, r in S.iterrows():
        a, b = PAIRS[r.comparison]; meds, excl = [], 0
        for sd in SEEDS:
            sfx = "" if sd == SEEDS[0] else f"_s{sd}"
            q = B[(B.A == a + sfx) & (B.B == b + sfx) & (B.endpoint == r.endpoint)].iloc[0]
            assert np.isclose(r[f"s{sd}_median"], q["median"]) and np.isclose(r[f"s{sd}_lo"], q.lo) and np.isclose(r[f"s{sd}_hi"], q.hi)
            meds.append(q["median"]); excl += int(bool(q.excludes_zero))
        assert r.n_seeds_excluding_zero == excl and bool(r.same_sign_all_seeds) == bool((np.array(meds) > 0).all() or (np.array(meds) < 0).all())


def test_decided_c09_c10_numbers():
    S = pd.read_csv(PT / "T07s.csv").set_index(["comparison", "endpoint"]); Q = pd.read_csv(PT / "T06s.csv")
    r = S.loc[("v004 - v002_notrace (U2)", "R_pred_on_reference_water_km2")]
    assert (round(-r.max_median, 1), round(-r.min_median, 1)) == (13.8, 48.8) and r.n_seeds_excluding_zero == 3     # D-C09
    h = Q[(Q.labels == "v004") & (Q.comparison == "U2 - U0d") & (Q.endpoint == "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2")].iloc[0]
    assert [round(h[f"s{sd}_median"], 1) for sd in SEEDS] == [1.0, 7.6, -3.8]                                          # D-C10
