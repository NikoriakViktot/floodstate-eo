"""Review F14: the weekly storage balance uses the same days for every term, and no balance series switches level source."""
from pathlib import Path

import numpy as np
import pandas as pd

T = Path(__file__).resolve().parents[1] / "case_studies/kakhovka_2023/tables"


def test_weekly_storage_change_is_the_boundary_difference_and_the_sum_of_daily_changes():
    D = pd.read_csv(T / "p95i_design_daily.csv").set_index("date"); W = pd.read_csv(T / "p95i_design_weekly_2023.csv")
    C = W[W.complete]
    assert len(C) >= 15
    for r in C.itertuples():
        days = D.loc[r.date_first:r.date_last]
        prev = (pd.Timestamp(r.date_first) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        boundary = D.loc[r.date_last, "V_design_at_rozumivka_km3"] - D.loc[prev, "V_design_at_rozumivka_km3"]
        assert np.isclose(r.dV_week_km3, boundary, atol=1e-3)                                  # V(end) - V(end of previous week)
        assert np.isclose(r.dV_week_km3, days.dV_design_rozumivka_hm3_day.sum() / 1000, atol=1e-3)   # = sum of the daily changes
        assert np.isclose(r.Q_out_design_km3, r.Q_in_km3 - r.dV_week_km3, atol=1e-3)            # outflow = inflow - storage change, same days
    assert W[~W.complete].Q_out_design_km3.isna().all()                                        # an incomplete week has no balance


def test_no_balance_series_switches_level_source():
    D = pd.read_csv(T / "p95i_design_daily.csv")
    assert "dV_design_hm3_day" not in D.columns and "Q_out_design_m3s" not in D.columns        # the switched series is gone
    for nm in ("rozumivka", "outlet"):
        dv = D[f"V_design_at_{nm}_km3"].diff() * 1000
        assert np.allclose(D[f"dV_design_{nm}_hm3_day"], dv.round(1), atol=0.051, equal_nan=True)
