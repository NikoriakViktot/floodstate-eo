"""Review F01/F04/F06: the Monte-Carlo contract on a synthetic two-zone mosaic (no bulk data).
(a) one realization per draw, reproducible; (b) new = potential minus the draw's own baseline; (c) total quantiles come from the
total ensemble; (d) pre-breach new = 0; (e) a pocket connected to the seed only through the other zone's territory is water on
the mosaic and not under the superseded per-zone evaluation; (f) the perturbation never touches bed cells."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from affine import Affine

from floodstate_eo.terrain.connectivity import connected_to_seed
from floodstate_eo.terrain.fields import FieldSynthesizer
from floodstate_eo.terrain.mosaic import UnionGrid

M6 = Path(__file__).resolve().parents[1] / "case_studies" / "kakhovka_2023" / "workflows" / "m6"


def _ld(name):
    s = importlib.util.spec_from_file_location(name + "_t", M6 / f"{name}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


@pytest.fixture(scope="module")
def world():
    P95, P95E = _ld("p95_hand_daily_inundation"), _ld("p95e_uncertainty_mc")
    D = P95.DATES
    # union 20 x 40 cells of 20 m: zone A = columns 0..24 (x 0..500 m), zone B = columns 20..39 (x 400..800 m); B owns the overlap
    grid = UnionGrid.from_members({"ZONE_4_A": (Affine(20.0, 0.0, 0.0, 0.0, -20.0, 400.0), (20, 25)), "ZONE_2_B": (Affine(20.0, 0.0, 400.0, 0.0, -20.0, 400.0), (20, 20))})
    dem = np.full((20, 40), 1.5, "f4"); dem[10, :] = 0.0                     # a river along row 10 (bed cells)
    dem[2:5, 30:36] = 0.5                                                    # a pocket in B's territory
    dem[3, 10:36] = 0.8; dem[3:10, 10] = 0.8                                 # its only path to the river runs through A's exclusive columns (< 20)
    is_fabdem = np.ones((20, 40), bool); is_fabdem[10, :] = False
    sig = np.where(is_fabdem, 0.3, 0.0).astype("f4")
    pre = dem == 0.0; seed = pre.copy()
    own_id = np.full((20, 40), 4, "u1"); own_id[:, 20:] = 2
    M = {"grid": grid, "G": {"transform": grid.transform, "ny": 20, "nx": 40, "crs": "EPSG:32636"}, "dem": dem, "dem_raw": dem, "sig": sig, "is_fabdem": is_fabdem, "pre": pre, "seed": seed,
             "hand": np.full((20, 40), np.nan, "f4"), "own_id": own_id, "names": ["ZONE_4_A", "ZONE_2_B"], "zone_id": {"ZONE_4_A": 4, "ZONE_2_B": 2},
             "base": np.ones((20, 40), bool), "cut": np.zeros((20, 40), bool), "inh": np.zeros((20, 40), bool), "fp": np.ones((20, 40), bool)}
    M["regions"] = {"DNIPRO_CORRIDOR": own_id > 0, "INHULETS_VALLEY_rect": np.zeros((20, 40), bool), "P42_FLOODPLAIN_DOMAIN": own_id > 0}
    # water surface: three river nodes observed every day (0.6 m before the breach, 1.0 m on 06-06..06-15, then 0.6 m), one gappy node, a far gauge
    def h(j):
        d = D[j]; return 1.0 if pd.Timestamp("2023-06-06") <= d <= pd.Timestamp("2023-06-15") else 0.6
    rows = []
    for nid, x in (("N1", 100.0), ("N2", 400.0), ("N3", 700.0)):
        rows += [{"node_id": nid, "date": D[j], "x": x, "y": 190.0, "reach_id": 1, "river_name": "no_data", "H": h(j), "H_evrf": np.nan, "wse_u": 0.05} for j in range(46)]
    rows += [{"node_id": "N4", "date": D[j], "x": 250.0, "y": 190.0, "reach_id": 1, "river_name": "no_data", "H": h(j), "H_evrf": np.nan, "wse_u": 0.05} for j in range(0, 46, 4)]
    W = P95.WSE(pd.DataFrame(rows), pd.Series(np.full(46, -5.0), index=D), kx=-40000.0, ky=190.0)
    Z = W.prepare(M)
    code = (own_id.astype("i4") * 8 + 1 + 4).astype("u1"); bidx = np.flatnonzero(M["base"]); rc = code.ravel()[bidx]
    cvtab, _, _, _ = P95E.gap_cv(W)
    sig_gap = {1: {b: 0.02 * (b + 1) for b in range(5)}, 2: {b: 0.05 * (b + 1) for b in range(5)}}   # piecewise-constant synthetic heights give a zero CV sigma
    prm = {"seed": 11, "rule": "connected_ceiling", "margin": 0.0, "connectivity": 8, "sigma_datum": 0.05, "sigma_gauge": 0.05, "sigma_swot": 0.05, "sigma_gap": sig_gap, "sigma_pass": 0.0,
               "field": "primary", "terrain": True, "wse": True, "baseline_fixed": False, "base_dates": [str(d.date()) for d in D if d <= pd.Timestamp(P95.BASELINE_DATE)],
               "days": [str(d.date()) for d in D]}
    P95E._G.update(M=M, W=W, Z=Z, prm=prm, P95=P95, seed=seed, bidx=bidx, rc=rc, zone_ids=[2, 4], zone_name={4: "ZONE_4_A", 2: "ZONE_2_B"},
                   regions=set(M["regions"]), runs=P95E.gap_runs(W), syns={"primary": FieldSynthesizer((20, 40), 20.0, structures=[(1.0, 100.0, "exponential")])},
                   crop=(0, 20, 0, 40))
    return P95, P95E, M, W, Z, cvtab


def test_nominal_world_counts_and_seam_pocket(world):
    P95, P95E, M, W, Z, _ = world
    pot, w = P95.potential_mosaic(M, W, Z, "2023-06-07", "connected_ceiling", seed=M["seed"])
    assert pot[3, 32] and pot[3, 15] and pot[10, 0] and not pot[0, 0]      # pocket + its path + the river; the 1.5 m floodplain stays dry
    # the superseded per-zone evaluation on B's own grid (columns 20..39) cannot reach the river through A's columns
    rs, cs = M["grid"].window("ZONE_2_B"); cand_b = (M["dem"] < w)[rs, cs]; seed_b = M["seed"][rs, cs]
    assert not connected_to_seed(cand_b, seed_b)[3, 12]                    # the pocket cell (3, 32) in B's local frame is disconnected
    k, rows, info = P95E.run_draw(0); R = pd.DataFrame(rows); c = R[(R.region == "DNIPRO_CORRIDOR") & (R.date == "2023-06-07")]
    assert k == 0 and info == {} and np.isclose(c.potential_km2.sum(), float(pot.sum()) * 0.0004, atol=1e-6)
    pre = R[(R.region == "DNIPRO_CORRIDOR") & (R.date == "2023-05-30")]
    assert np.isclose(pre.potential_km2.sum(), 40 * 0.0004) and (pre.new_km2 == 0).all()   # (d) river only before the breach, new = 0
    assert np.isclose(c.new_km2.sum(), (float(pot.sum()) - 40) * 0.0004, atol=1e-6)         # everything but the river is new on 06-07


def test_draws_are_reproducible_coherent_and_consistent(world):
    _, P95E, _, W, _, _ = world
    _, rows1, info1 = P95E.run_draw(1); _, rows1b, _ = P95E.run_draw(1); _, rows2, _ = P95E.run_draw(2)
    assert rows1 == rows1b and rows1 != rows2                               # (a) one realization per draw index, reproducible
    assert 0.5 < info1["field_std"] < 1.6 and info1["eps_std_fabdem"] > 0   # a unit-ish field on a 20 x 40 lattice, scaled by sigma
    for rows in (rows1, rows2):
        R = pd.DataFrame(rows)
        assert (R.new_km2 <= R.potential_km2 + 1e-9).all()                   # (b) new is a subset of potential ...
        assert (R.potential_km2 - R.new_km2 <= R.baseline_km2 + 1e-9).all()  # ... and potential minus new lies inside the draw's baseline
        assert (R[R.date < "2023-06-06"].new_km2 == 0).all()                 # (d)
    rng = np.random.default_rng(3); Hm, i = P95E.draw_hmat(W, P95E._G["prm"], rng, P95E._G["runs"])
    Hm2, _ = P95E.draw_hmat(W, P95E._G["prm"], np.random.default_rng(3), P95E._G["runs"])
    assert np.array_equal(Hm, Hm2) and np.isclose(Hm[-1, 0] - W.H[-1, 0], i["e_gauge"])   # the gauge row carries e_gauge only
    # one standard normal per node per gap run: N4 is observed every 4th day, so days 1-3 form one run with gaps 1, 2, 1
    n4 = W.node_id.index("N4"); sg = P95E._G["prm"]["sigma_gap"][1]; b = P95E.gap_bin
    z1 = (Hm[n4, 1] - W.H[n4, 1] - i["off_datum"]) / sg[b(1)]; z2 = (Hm[n4, 2] - W.H[n4, 2] - i["off_datum"]) / sg[b(2)]
    assert np.isclose(z1, z2, atol=1e-4)
    n1 = W.node_id.index("N1"); assert not np.isclose(Hm[n1, 1] - W.H[n1, 1], Hm[n1, 2] - W.H[n1, 2])   # observed days: independent wse_u noise


def test_total_quantiles_come_from_the_total_ensemble(world):
    _, P95E, _, _, _, cvtab = world
    R = pd.concat([pd.DataFrame(P95E.run_draw(k)[1]) for k in range(6)], ignore_index=True)
    Pd = P95E.pooled(R); S = P95E.summarise(Pd); s = S[(S.region == "DNIPRO_CORRIDOR") & (S.date == "2023-06-07")].iloc[0]
    draws = Pd[(Pd.region == "DNIPRO_CORRIDOR") & (Pd.date == "2023-06-07") & (Pd.draw > 0)]
    assert np.isclose(s.W_total_p50_km2, round(float(draws.potential_km2.median()), 1))    # (c) not central - A_central + A_q
    assert np.isclose(s.A_p50_km2, round(float(draws.new_km2.median()), 1)) and s.n_draws == 5
    assert set(cvtab.kind) >= {"interpolated", "all (gap-matched)"} and cvtab.n.sum() > 0
    pk = P95E.peak_dates(Pd, "new_km2"); assert pk.share.sum() > 0.99 and (pk.n_draws == 5).all()
