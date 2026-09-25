# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Uncertainty budget of the terrain reconstruction (area, volume).
"""P95e -- Monte-Carlo uncertainty of the daily terrain-reconstructed inundation (claim C01), replacing the rule x margin
sensitivity as the uncertainty statement. Components (T11b), each with its source:

    sigma_closure   Kherson-local closure residual of the SWOT chain (Paper 1): NMAD 0.05 m, one offset per draw (all cells)
    sigma_gauge     daily gauge without observation time, used only where cells are > 15 km from a node: 0.05 m, per draw
    sigma_swot      SWOT node height uncertainty: median wse_u of the accepted nodes (p59), independent per node-day
    sigma_interp    per-node time interpolation: NMAD of leave-one-out residuals on observed node-days (value vs mean of the
                    previous and next observed day), applied to interpolated node-days only
    DEM             seamless DEM error by WorldCover class from Paper 2 / p57 (C seamless: the class median is removed in the
                    reconstruction itself, rev 5; NMAD as sigma here), spatially correlated field at 500 m, one field per draw
Per draw the same-rule pre-breach baseline is rebuilt with the perturbed DEM, so "new" stays consistent. Key dates only.

Outputs: <case_study>/tables/p95e_uncertainty_components.csv (T11b), p95e_area_volume_uncertainty.csv (region x date:
         A/V p05, p50, p95 and the deterministic central run), p95e_draws.csv (every draw, for re-analysis)
"""
from __future__ import annotations
import argparse, importlib.util, json, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio.warp import reproject, Resampling
from scipy import ndimage
from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
KEY_DATES = ["2023-06-06", "2023-06-07", "2023-06-08", "2023-06-09", "2023-06-11", "2023-06-13", "2023-06-14", "2023-06-18", "2023-06-21"]
BASE_DATES = [str(d.date()) for d in pd.date_range("2023-05-26", "2023-06-05", freq="D")]   # same normal regime as p95
SIGMA_CLOSURE_M, SIGMA_GAUGE_M = 0.05, 0.05
DEM_CLASS = {10: "trees", 30: "grass", 40: "cropland", 50: "built", 60: "bare", 90: "wetland"}     # WorldCover codes with p57 rows
CORR_M = 500.0
CELL_KM2 = 0.0004


def _ld(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def interp_sigma(H, obs):
    """NMAD of leave-one-out residuals on OBSERVED node-days: each observed value against the mean of its observed time
    neighbours (previous and next day of the same node)."""
    res = []
    for i in range(H.shape[0]):
        for j in range(1, H.shape[1] - 1):
            if obs[i, j] and obs[i, j - 1] and obs[i, j + 1]:
                res.append(H[i, j] - 0.5 * (H[i, j - 1] + H[i, j + 1]))
    r = np.array(res); return float(1.4826 * np.median(np.abs(r - np.median(r)))), len(r)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=40); ap.add_argument("--seed", type=int, default=20260925)
    ap.add_argument("--rule", default="connected_ceiling"); a = ap.parse_args()
    t0 = time.time(); P95 = _ld("p95_hand_daily_inundation"); P = P95.load_p92(); rng = np.random.default_rng(a.seed)
    W, dxm, dym, nodes = P95.load_engine()
    sig_swot = float(nodes.wse_u.median()); sig_interp, n_loo = interp_sigma(W.H, W.obs)
    DEMERR, dem_src = P95.dem_error_table()
    comp = [dict(component="closure_kherson", sigma_m=SIGMA_CLOSURE_M, applied="one offset per draw, all cells", source="Paper 1 Table 5 / Sec. 5.12 (NMAD 4-5 cm at Kherson)"),
            dict(component="gauge_daily", sigma_m=SIGMA_GAUGE_M, applied="per draw, cells > 15 km from a node (gauge cap)", source="date-only daily values; two yearbooks differ by NMAD 1.5 cm (Paper 1 Sec. 5.12)"),
            dict(component="swot_node_wse_u", sigma_m=round(sig_swot, 3), applied="per (day, 1-km bin), 5-km smoothed field", source="p59 nodes, median wse_u"),
            dict(component="H(s,t)_interpolation", sigma_m=round(sig_interp, 3), applied="interpolated cells only, per (day, bin), 5-km smoothed", source=f"leave-one-out NMAD on {n_loo} observed cells")]
    for k, v in DEMERR.items():
        comp.append(dict(component=f"dem_{v['cls']}", sigma_m=round(v["sigma"], 3), bias_m=round(v["bias"], 3), rmse_m=round(v["rmse"], 3), n=v["n"],
                         applied="class-wise sigma, spatially correlated field (500 m) per draw; class median bias removed in p95 rev 5", source=f"{dem_src} (C seamless by WorldCover class)"))
    pd.DataFrame(comp).to_csv(CFG.TABLES / "p95e_uncertainty_components.csv", index=False)
    print(pd.DataFrame(comp).to_string(index=False), flush=True)
    draws = []
    for zone in P95.ZONES:
        L = P95.zone_layers(zone, P); G = L["G"]; Z = W.prepare(L)
        base = np.isfinite(L["dem"]) & (L["dist"] <= P95.DIST_MAX_M) & (L["xs"] < dxm - P95.DAM_BUFFER_M)[None, :] & L["own"]
        _, sig = P95.dem_bias_fields(zone, G)                            # the DEM in L is already bias-corrected (rev 5)
        regions = {"DNIPRO_CORRIDOR": L["own"] & ~L["cut"], "INHULETS_VALLEY_rect": L["own"] & L["inh"]}
        if L["fp"] is not None:
            regions["P42_FLOODPLAIN_DOMAIN"] = L["own"] & L["fp"]
        kf = (int(np.ceil(G["ny"] * 20 / CORR_M)), int(np.ceil(G["nx"] * 20 / CORR_M)))
        def potential(day, dem_pert, off, Hmat, off_far):
            w = W.field(Z, day, 0.0, off, off_far, Hmat); cand = base & (dem_pert < w)
            if a.rule == "hand_and_ceiling":
                return cand & np.isfinite(L["hand"]) & (L["hand"] < w - P95.RIVER_LEVEL_M), w
            if a.rule == "ceiling_only":
                return cand, w
            lab, n = ndimage.label(cand, structure=np.ones((3, 3), bool)); keep = np.zeros(n + 1, bool)
            keep[np.unique(lab[cand & L["seed"]])] = True; keep[0] = False
            return keep[lab], w
        for k in range(a.n + 1):                                         # draw 0 = central (no perturbation)
            if k == 0:
                dem_p, off, off_far, Hmat = L["dem"], 0.0, 0.0, None
            else:
                field = ndimage.zoom(rng.standard_normal(kf).astype("f4"), (G["ny"] / kf[0], G["nx"] / kf[1]), order=1)[:G["ny"], :G["nx"]]
                dem_p = (L["dem"] + field * sig).astype("f4")                  # bias already removed in zone_layers; correlated noise only
                off = float(rng.normal(0, SIGMA_CLOSURE_M)); off_far = off + float(rng.normal(0, SIGMA_GAUGE_M))
                n_sw = rng.normal(0, sig_swot, W.H.shape); n_it = rng.normal(0, sig_interp, W.H.shape) * (~W.obs)
                Hmat = (W.H + n_sw + n_it).astype("f4"); Hmat[-1] = W.H[-1]      # the gauge node carries off_far, not node noise
            baseline = L["pre"].copy()
            for day in BASE_DATES:
                baseline |= potential(day, dem_p, off, Hmat, off_far)[0]
            for day in KEY_DATES:
                pot, w = potential(day, dem_p, off, Hmat, off_far); new = pot & ~baseline; depth = np.where(new, w - dem_p, 0).astype("f4")
                for nm, m in regions.items():
                    draws.append(dict(zone=zone, draw=k, date=day, region=nm, area_km2=round(float((new & m).sum()) * CELL_KM2, 2),
                                      volume_hm3=round(float(depth[new & m].sum()) * 400 / 1e6, 2)))
            if k % 10 == 0:
                print(zone, "draw", k, round(time.time() - t0), "s", flush=True)
    D = pd.DataFrame(draws); D.to_csv(CFG.TABLES / "p95e_draws.csv", index=False)
    Pd = D.groupby(["draw", "date", "region"], as_index=False)[["area_km2", "volume_hm3"]].sum()        # zones pooled (owner rule)
    rows = []
    for (d, r), g in Pd.groupby(["date", "region"]):
        c = g[g.draw == 0]; s = g[g.draw > 0]
        rows.append(dict(date=d, region=r, area_semantics="terrain_reconstructed", A_central_km2=float(c.area_km2.iloc[0]),
                         A_p05_km2=round(float(s.area_km2.quantile(.05)), 1), A_p50_km2=round(float(s.area_km2.median()), 1), A_p95_km2=round(float(s.area_km2.quantile(.95)), 1),
                         V_central_hm3=float(c.volume_hm3.iloc[0]), V_p05_hm3=round(float(s.volume_hm3.quantile(.05)), 1),
                         V_p50_hm3=round(float(s.volume_hm3.median()), 1), V_p95_hm3=round(float(s.volume_hm3.quantile(.95)), 1), n_draws=int(s.draw.nunique())))
    R = pd.DataFrame(rows); R.to_csv(CFG.TABLES / "p95e_area_volume_uncertainty.csv", index=False)
    pd.set_option("display.width", 250); print(R[R.region == "DNIPRO_CORRIDOR"].to_string(index=False))
    print(f"-> tables/p95e_*.csv ({round(time.time() - t0)} s)")


if __name__ == "__main__":
    main()
