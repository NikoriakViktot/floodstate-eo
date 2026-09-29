"""Review F13: no silent endpoint plateau outside a table's domain."""
from __future__ import annotations

import numpy as np
import pytest

from floodstate_eo.terrain.interp import bounded_interp


def test_inside_equals_numpy_and_outside_is_nan():
    xp = np.array([10.0, 12.0, 14.0]); fp = np.array([6.95, 9.0, 12.0])
    x = np.array([9.999, 10.0, 11.0, 14.0, 14.001, 5.0])
    out = bounded_interp(x, xp, fp)
    assert np.isnan(out[0]) and out[1] == 6.95 and np.isclose(out[2], np.interp(11.0, xp, fp)) and out[3] == 12.0
    assert np.isnan(out[4]) and np.isnan(out[5])


def test_decreasing_table_and_custom_fill():
    xp = np.array([14.0, 12.0, 10.0]); fp = np.array([12.0, 9.0, 6.95])
    assert np.isclose(bounded_interp(11.0, xp, fp), 7.975)
    assert bounded_interp(9.0, xp, fp, left=-1.0) == -1.0


def test_refuses_non_monotonic_or_nan_tables():
    with pytest.raises(ValueError):
        bounded_interp(1.0, [1.0, 3.0, 2.0], [0.0, 1.0, 2.0])
    with pytest.raises(ValueError):
        bounded_interp(1.0, [1.0, np.nan], [0.0, 1.0])


def test_nan_level_gives_nan():
    assert np.isnan(bounded_interp(np.nan, [10.0, 12.0], [6.95, 9.0]))


def test_committed_hypsometry_has_no_plateau_below_the_table():
    """p95f_hypsometry_dem.csv: the design columns are NaN below 10 m BS (review F13), finite from 10 m up."""
    from pathlib import Path
    import pandas as pd
    p = Path(__file__).resolve().parents[1] / "case_studies/kakhovka_2023/tables/p95f_hypsometry_dem.csv"
    H = pd.read_csv(p)
    below = H.level_bs77_m < 10.0
    assert below.any() and H.loc[below, ["A_table19_km2", "V_table19_km3"]].isna().all().all()
    assert H.loc[~below, ["A_table19_km2", "V_table19_km3"]].notna().all().all()
