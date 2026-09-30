"""Paper 3 heights are Paper 1's heights (maintainer, 2026-09-30: "our results must match this article", SWOT-DNIPRO release
paper1-v6): the reservoir closures of Paper 1 are reproduced, the Kherson gauge sits at the post's own EPSG:9902 step, the FABDEM
part of the terrain moves by the chain difference only, and the pool outlet reproduces Paper 1's 17.61 m -> 5.71 m."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
CS = ROOT / "case_studies/kakhovka_2023"
_s = importlib.util.spec_from_file_location("paper1_frame", CS / "workflows/m6/paper1_frame.py")
PF = importlib.util.module_from_spec(_s); _s.loader.exec_module(PF)


def test_free2mean_is_the_iers_term():
    assert PF.free2mean(0.0) == pytest.approx(0.06029)
    assert -0.040 < float(PF.free2mean(46.8)) < -0.033                # negative at these latitudes (Paper 1 v6 S1.2)


@pytest.mark.skipif(not PF.COMPANION_STATIONS.exists(), reason="the companion station table is not available")
def test_reservoir_closures_reproduce_paper1():
    c_tf, c_prod = PF.reservoir_closures()
    assert c_tf == pytest.approx(-0.173, abs=5e-4)                   # the superseded 'term omitted' chain (S1.5)
    assert c_prod == pytest.approx(-0.135, abs=1e-3)                 # the production chain (Sec. 5.1)
    assert PF.mixed_chain_shift() == pytest.approx(0.0377, abs=1e-3)


def test_kherson_gauge_at_the_posts_own_step():
    g = pd.read_csv(CS / "tables/p59_swot_vs_kherson.csv").dropna(subset=["H_gauge_evrf", "water_level_m_abs"])
    assert np.allclose(g.H_gauge_evrf - g.water_level_m_abs, PF.KHERSON_DELTA_EPSG9902_M, atol=1e-4)


def test_only_fabdem_cells_move():
    z = np.array([1.0, 2.0, 3.0, 4.0, 5.0], "f4"); src = np.array([1, 2, 3, 4, 5], "u1")
    out = PF.fabdem_to_paper1(z, src) - z
    assert np.allclose(out[[0, 1, 4]], 0.0) and np.allclose(out[[2, 3]], PF.mixed_chain_shift(), atol=1e-6)


def test_pool_outlet_reproduces_paper1():
    R = pd.read_csv(CS / "tables/p95f_reservoir_daily.csv").set_index("date")
    assert round(float(R.loc["2023-05-31", "H_outlet_m"]), 2) == 17.61        # Paper 1 v6 Sec. 4.2 / Table 2
    assert round(float(R.loc["2023-06-13", "H_outlet_m"]), 2) == 5.71
    assert bool(R.loc["2023-06-13", "surface_upper_bound"]) and not bool(R.loc["2023-06-11", "surface_upper_bound"])
