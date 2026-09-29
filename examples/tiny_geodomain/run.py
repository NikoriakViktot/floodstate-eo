"""Tiny open geodomain: the whole reconstruction and Monte-Carlo chain on synthetic, openly generated inputs (review F16).

Nothing here needs bulk data, credentials or a sibling repository: a 90 x 180 lattice of 20 m cells (1.8 x 3.6 km) (two overlapping "zones" to
exercise the union mosaic), a meandering channel (bed cells) in a floodplain that rises away from it, a terrace, four river nodes
with a daily event hydrograph (observed every day, one node every fourth day) and a distant gauge. The chain is the production
code of the case study, called exactly as the paper runs it:

    water surface H(x, y, t)      p95.WSE (nodes + gauge; interpolation / hold flags; every error term once, through Hmat)
    terrain realization           terrain residual field (floodstate_eo.terrain.fields) on the non-bed cells only
    connected inundation          p95.potential_mosaic: z < H and connected to the pre-event water network, on the union mosaic
    baseline and new water        the same world's pre-event regime; new = potential minus baseline
    ensemble                      p95e.run_draw per world (seeded, reproducible), p95e.pooled / summarise -> quantiles

Run:  python examples/tiny_geodomain/run.py [--draws 100] [--out examples/tiny_geodomain/output]
Outputs: <out>/draws.csv (every world, day, zone, region), <out>/summary.csv (per day: nominal, p05/p50/p95 of the new and of
the total water area), <out>/peak_depth.png (depth of the nominal world on the day of its areal maximum).
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from affine import Affine

from floodstate_eo.terrain.fields import FieldSynthesizer
from floodstate_eo.terrain.mosaic import UnionGrid

ROOT = Path(__file__).resolve().parents[2]
M6 = ROOT / "case_studies" / "kakhovka_2023" / "workflows" / "m6"
NY, NX, CELL = 90, 180, 20.0


def _ld(name):
    s = importlib.util.spec_from_file_location(name + "_tiny", M6 / f"{name}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def hydrograph(D):
    """Node water level (m) per day: 0.5 m before the event, a rise to 1.9 m on the second event day, a recession to 0.5 m."""
    t0 = pd.Timestamp("2023-06-06"); out = []
    for d in D:
        k = (d - t0).days
        out.append(0.5 if k < 0 else 0.5 + 1.4 * min(1.0, (k + 1) / 2) * np.exp(-max(0, k - 1) / 4.0))
    return np.array(out)


def build(P95, P95E, seed=11):
    D = P95.DATES
    half = NX // 2
    grid = UnionGrid.from_members({"ZONE_4_A": (Affine(CELL, 0.0, 0.0, 0.0, -CELL, CELL * NY), (NY, half + 5)),
                                   "ZONE_2_B": (Affine(CELL, 0.0, CELL * half, 0.0, -CELL, CELL * NY), (NY, NX - half))})
    y = np.arange(NY)[:, None]; x = np.arange(NX)[None, :]
    chan = (NY // 2 + np.round(9 * np.sin(x / 27.0))).astype(int)                    # a meander
    dist = np.abs(y - chan)
    dem = (0.35 + 0.025 * dist).astype("f4"); dem[dist <= 1] = 0.0                  # floodplain rising away from a 3-cell channel
    dem[dist > 36] = 2.6                                                              # a terrace above every water level
    is_fabdem = dist > 1                                                              # the channel is bed: no terrain perturbation
    sig = np.where(is_fabdem, 0.25, 0.0).astype("f4")
    pre = dem == 0.0; own_id = np.full((NY, NX), 4, "u1"); own_id[:, half:] = 2
    M = {"grid": grid, "G": {"transform": grid.transform, "ny": NY, "nx": NX, "crs": "EPSG:32636"}, "dem": dem, "dem_raw": dem, "sig": sig,
         "is_fabdem": is_fabdem, "pre": pre, "seed": pre.copy(), "hand": np.full((NY, NX), np.nan, "f4"), "own_id": own_id,
         "names": ["ZONE_4_A", "ZONE_2_B"], "zone_id": {"ZONE_4_A": 4, "ZONE_2_B": 2}, "base": np.ones((NY, NX), bool),
         "cut": np.zeros((NY, NX), bool), "inh": np.zeros((NY, NX), bool), "fp": np.ones((NY, NX), bool)}
    M["regions"] = {"DNIPRO_CORRIDOR": own_id > 0, "INHULETS_VALLEY_rect": np.zeros((NY, NX), bool), "P42_FLOODPLAIN_DOMAIN": own_id > 0}
    H = hydrograph(D); rows = []
    for nid, xm, days in (("N1", 300.0, range(len(D))), ("N2", 1350.0, range(len(D))), ("N3", 2550.0, range(len(D))), ("N4", 3450.0, range(0, len(D), 4))):
        yc = CELL * NY - CELL * (chan[0, int(xm // CELL)] + 0.5)
        rows += [{"node_id": nid, "date": D[j], "x": xm, "y": yc, "reach_id": 1, "river_name": "no_data", "H": H[j] - 0.0002 * xm,
                  "H_evrf": np.nan, "wse_u": 0.05} for j in days]      # a gentle downstream slope of 0.2 m per km
    W = P95.WSE(pd.DataFrame(rows), pd.Series(H - 0.5, index=D), kx=-40000.0, ky=CELL * NY / 2)
    Z = W.prepare(M)
    code = (own_id.astype("i4") * 8 + 1 + 4).astype("u1"); bidx = np.flatnonzero(M["base"]); rc = code.ravel()[bidx]
    sig_gap = {1: {b: 0.03 * (b + 1) for b in range(5)}, 2: {b: 0.06 * (b + 1) for b in range(5)}}
    prm = {"seed": seed, "rule": "connected_ceiling", "margin": 0.0, "connectivity": 8, "sigma_datum": 0.05, "sigma_gauge": 0.05, "sigma_swot": 0.05,
           "sigma_gap": sig_gap, "sigma_pass": 0.0, "field": "primary", "terrain": True, "wse": True, "baseline_fixed": False,
           "base_dates": [str(d.date()) for d in D if d <= pd.Timestamp(P95.BASELINE_DATE)], "days": [str(d.date()) for d in D]}
    # _G["seed"] is the pre-event water network (a mask); prm["seed"] is the random seed of the worlds
    P95E._G.update(M=M, W=W, Z=Z, prm=prm, P95=P95, seed=M["seed"], bidx=bidx, rc=rc, zone_ids=[2, 4], zone_name={4: "ZONE_4_A", 2: "ZONE_2_B"},
                   regions=set(M["regions"]), runs=P95E.gap_runs(W),
                   syns={"primary": FieldSynthesizer((NY, NX), CELL, structures=[(0.9, 150.0, "exponential")], nugget=0.1)}, crop=(0, NY, 0, NX))
    return M, W, Z


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--draws", type=int, default=100); ap.add_argument("--out", default=str(Path(__file__).parent / "output"))
    a = ap.parse_args(argv); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    P95, P95E = _ld("p95_hand_daily_inundation"), _ld("p95e_uncertainty_mc")
    M, W, Z = build(P95, P95E)
    R = pd.concat([pd.DataFrame(P95E.run_draw(k)[1]) for k in range(a.draws + 1)], ignore_index=True)   # draw 0 = the nominal world
    R.to_csv(out / "draws.csv", index=False)
    S = P95E.summarise(P95E.pooled(R)); S = S[S.region == "DNIPRO_CORRIDOR"].drop(columns="region")
    S.to_csv(out / "summary.csv", index=False)
    pk = S.loc[S.A_central_km2.idxmax(), "date"]
    pot, w = P95.potential_mosaic(M, W, Z, pk, "connected_ceiling", seed=M["seed"])
    depth = np.where(pot & ~M["pre"], w - M["dem"], np.nan)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 3.2), constrained_layout=True)
        im = ax.imshow(depth, cmap="Blues", vmin=0); ax.contour(M["pre"], levels=[0.5], colors="k", linewidths=0.6)
        fig.colorbar(im, ax=ax, shrink=0.8).set_label("depth of new water, m"); ax.set_title(f"tiny geodomain, nominal world, {pk}", fontsize=8)
        fig.savefig(out / "peak_depth.png", dpi=110); plt.close(fig)
    except ImportError:                                                      # plotting is optional
        pass
    print(S[["date", "A_central_km2", "A_p05_km2", "A_p50_km2", "A_p95_km2", "W_total_p50_km2", "n_draws"]].to_string(index=False))
    print(f"-> {out}/ (areal maximum of the nominal world on {pk}; {a.draws} Monte-Carlo worlds)")
    return S


if __name__ == "__main__":
    main()
