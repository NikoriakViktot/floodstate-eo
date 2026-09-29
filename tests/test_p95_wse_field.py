"""Review F03/F05: every water-surface error term enters the field once, through Hmat; support flags are right.
Synthetic engine (three SWOT nodes + the gauge), no bulk data."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from affine import Affine

P95_PATH = Path(__file__).resolve().parents[1] / "case_studies" / "kakhovka_2023" / "workflows" / "m6" / "p95_hand_daily_inundation.py"


@pytest.fixture(scope="module")
def P95():
    s = importlib.util.spec_from_file_location("p95_for_test", P95_PATH); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def _engine(P95, max_gap_days=None, river_aware=False):
    """Nodes A, B (main stem, x = 0 / 2 km) and C (a side river, x = 1 km); gauge 30 km west at x = -30 km."""
    D = P95.DATES; rows = []
    for nid, x, river, days in (("A", 0.0, "no_data", range(0, 46, 2)), ("B", 2000.0, "no_data", range(1, 46, 3)), ("C", 1000.0, "Inhulets", range(0, 46, 1))):
        for j in days:
            rows.append({"node_id": nid, "date": D[j], "x": x, "y": 0.0, "reach_id": 1, "river_name": river, "H": 10.0 + 0.1 * j + {"A": 0, "B": 0.5, "C": 3.0}[nid], "H_evrf": np.nan, "wse_u": 0.1})
    nodes = pd.DataFrame(rows)
    gauge = pd.Series(2.0 + 0.02 * np.arange(46), index=D)
    return P95.WSE(nodes, gauge, kx=-30000.0, ky=0.0, max_gap_days=max_gap_days, river_aware=river_aware)


def _grid(x0, nx, ny=2):
    return {"transform": Affine(20.0, 0.0, x0, 0.0, -20.0, 20.0 * ny), "ny": ny, "nx": nx, "crs": "EPSG:32636"}


def test_offset_enters_once_with_cap_active_and_inactive(P95):
    W = _engine(P95); day = str(P95.DATES[10].date())
    near = _grid(-100.0, 10); far = _grid(-50000.0, 10)                  # far: > 15 km from every node, west of the gauge -> capped
    Zn, Zf = W.prepare(near), W.prepare(far)
    h_near, h_far = W.field(Zn, day)[0, 0], W.field(Zf, day)[0, 0]
    assert abs(h_far - W.H[-1, 10]) < 1e-5                                   # capped at the gauge exactly, nothing added
    Hp = W.H.copy(); Hp[:-1] += 0.1                                          # a +0.1 m closure realization on the SWOT nodes
    assert abs(W.field(Zn, day, Hmat=Hp)[0, 0] - (h_near + 0.1)) < 1e-5     # +0.1, not +0.2
    assert abs(W.field(Zf, day, Hmat=Hp)[0, 0] - h_far) < 1e-5              # the cap is the gauge: a SWOT offset does not move it
    Hg = W.H.copy(); Hg[-1] += 0.07                                          # a gauge realization moves the cap once
    assert abs(W.field(Zf, day, Hmat=Hg)[0, 0] - (h_far + 0.07)) < 1e-5
    assert abs(W.field(Zn, day, margin=0.3)[0, 0] - (h_near + 0.3)) < 1e-5  # the deterministic margin still applies


def test_support_flags_and_gap_lengths(P95):
    W = _engine(P95); iA = W.node_id.index("A"); iB = W.node_id.index("B")
    assert W.kind[iA, 0] == 0 and W.kind[iA, 1] == 1 and W.gap[iA, 1] == 1 and W.kind[iA, 45] == 2   # held after the last obs (44)
    assert W.kind[iB, 0] == 2 and W.gap[iB, 0] == 1                                                   # held before the first obs (1)
    t = W.support_table(); assert len(t) == 46 and int(t.n_observed.iloc[0]) == 2
    Wg = _engine(P95, max_gap_days=0)                                       # nodes unavailable on every unobserved day
    assert Wg.kind[iA, 1] == 3 and np.isnan(Wg.H[iA, 1]) and np.isfinite(Wg.H[-1, 1])
    Z = Wg.prepare(_grid(-100.0, 10)); k = Wg.support_kind(Z, str(P95.DATES[1].date()))
    assert k[0, 0] in (0, 1)                                                 # C is observed every day: still a surface


def test_river_aware_median_uses_the_nearest_nodes_river(P95):
    W = _engine(P95); Wr = _engine(P95, river_aware=True); day = str(P95.DATES[0].date())
    g = _grid(-100.0, 5)                                                     # nearest node = A (main stem); C (side river, +3 m) is within 3 km
    h_all, h_river = W.field(W.prepare(g), day)[0, 0], Wr.field(Wr.prepare(g), day)[0, 0]
    assert h_river < h_all                                                   # the side-river node no longer lifts the median


def test_row_nanmedian_is_bit_identical_to_numpy(P95):
    rng = np.random.default_rng(5)
    v = rng.normal(5.0, 2.0, (20000, 5)).astype("f4")
    v[rng.random(v.shape) < 0.35] = np.nan; v[:50] = np.nan                  # all-NaN rows, even and odd counts
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        ref = np.nanmedian(v, axis=1)
    got = P95.row_nanmedian(v)
    assert got.dtype == ref.dtype and np.array_equal(got, ref, equal_nan=True)
