# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Reservoir drawdown (levels, area, volume) linked to the downstream flood.
"""P95f -- the Kakhovka pool during the drawdown, day by day, and its water balance against the downstream inundation.

Pool water surface per day: the Paper-1/p61 level sources in one frame (EVRF2019) and one longitudinal coordinate (SWORD
chainage upstream of the dam): SWOT outlet nodes (0 km), Nikopol press values (~160 km), the Rozumivka gauge (247.5 km),
G-REALM (111 km) -- linearly interpolated along the chainage per day (the surface is NOT level during the drawdown: 4 m of
gradient on 6 June). Pool area and volume: the 50 m seamless DEM (Paper 2: kriged bed inside the pre-breach water polygon)
integrated under that sloped surface inside the pre-breach pool polygon; the design hypsometry (Table 19, BS-77 levels) is
evaluated at the outlet level for reference. Chainage of a pool cell = position along the polyline dam -> Nikopol ->
Rozumivka scaled to the SWORD chainage of those anchors.

Balance per day: dV/dt of the pool, inflow from DniproHES (daily releases), the implied breach outflow Q_out = Q_in - dV/dt,
and, downstream, the terrain-reconstructed volume of new water (p95, corridor + Inhulets) and the Kherson stage.

Paper 1 frame (2026-09-30): the SWOT outlet levels are moved from the p60/p61 chain (+free2mean with the tide-free closure -0.173 m) to the
production chain of Paper 1 v6 (no permanent-tide term for SWOT, reservoir closure -0.135 m): +0.073 m, reproducing Paper 1's 17.61 m
(31 May) and 5.71 m (13 June). G-REALM is no longer an anchor (not in Paper 1's frame; 0.5 m above Nikopol upstream on 9 June).

Censored level (maintainer's check of the drawdown maps, 2026-09-30): the Nikopol post reported on 13 June only an upper bound
(CENSORED_UPPER_BOUND, 9.17 m: the level had fallen below the post), and the forward fill had carried the 11 June value (9.52 m)
over it. A post-breach upper bound now caps the source's series on its day, the gap before it is interpolated towards the bound,
and every day whose surface rests on a bound carries `surface_upper_bound` = True (12-13 June): the pool surface, area and volume
of those days are upper estimates.

Sparse altimetry (same check): after the breach G-REALM enters only on its own day. The forward fill had held its 9 June level
(12.43 m at 111 km) over 10-11 June while the observed Nikopol level upstream was already lower (10.37 m on 10 June): a hump in
the surface that inflated the 10-11 June volumes and put a spurious release peak on 12 June when the hold ran out.

Review F13 (2026-09-29): the design table (Table 19) is read with `terrain.interp.bounded_interp` -- NaN below its first
level (10 m BS) and above its last, never the endpoint value repeated (np.interp wrote 1443 km2 / 6.95 km3 at 5 m).

Outputs: <case_study>/tables/p95f_reservoir_daily.csv, p95f_hypsometry_dem.csv, p95f_manifest.json
"""
from __future__ import annotations
import importlib.util, json, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio import features
from rasterio.warp import transform as tf
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.terrain.interp import bounded_interp

SD = Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs" / "tables"
DATES = pd.date_range("2023-05-26", "2023-07-10", freq="D")
ANCHORS = [("dam", 33.3667, 46.7783, 0.0), ("nikopol", 34.375355, 47.554451, 159.863), ("rozumivka", 35.1, 47.75, 247.512)]   # Rozumivka lon/lat replaced by UTM below
ROZ_UTM = (661001.4, 5293107.6)
BS77_TO_EVRF = 0.185                           # median EPSG:9902 offset at the reservoir gauges (Paper 1: 0.1715-0.2157 m)
SOURCES = {"SWOT_OUTLET": 0.0, "NIKOPOL_UHE": 159.863, "ROZUMIVKA_GAUGE": 247.512, "ICESAT2_ATL13": None}   # None = chain_km per row
# G-REALM (Sentinel-6A, 111 km) is not an anchor (check of 2026-09-30): its vertical chain is not part of Paper 1's validated frame, and on
# 9 June it stood 0.5 m above the Nikopol post 50 km upstream -- impossible for a draining pool. It stays in p61 and in Fig09a as a check.
_pf = importlib.util.spec_from_file_location("paper1_frame", Path(__file__).with_name("paper1_frame.py")); PF = importlib.util.module_from_spec(_pf); _pf.loader.exec_module(PF)
BREACH = pd.Timestamp("2023-06-06")
GOOD_Q = {"OK", "FILLED", "SINGLE_NODE", "PRESS", "DERIVED", "PRESS_TIME_UNCERTAIN", "QC_PARTIAL"}                       # excluded: CENSORED, QC_FAIL, ASSUMED_*, FILLED_SUSPECT, ICE


def chainage_grid(xs, ys):
    """Path distance along dam -> Nikopol -> Rozumivka, scaled per segment to the SWORD chainage of the anchors."""
    dx, dy = tf("EPSG:4326", CFG.CRS_METRIC, [ANCHORS[0][1]], [ANCHORS[0][2]]); nx_, ny_ = tf("EPSG:4326", CFG.CRS_METRIC, [ANCHORS[1][1]], [ANCHORS[1][2]])
    P = np.array([[dx[0], dy[0]], [nx_[0], ny_[0]], list(ROZ_UTM)]); S = np.array([0.0, ANCHORS[1][3], ANCHORS[2][3]])
    XX, YY = np.meshgrid(xs, ys); pts = np.c_[XX.ravel(), YY.ravel()]; best = np.full(len(pts), np.inf); chain = np.zeros(len(pts))
    for i in range(2):
        a, b = P[i], P[i + 1]; ab = b - a; L2 = float(ab @ ab)
        t = np.clip(((pts - a) @ ab) / L2, 0, 1); proj = a + t[:, None] * ab; d = np.hypot(*(pts - proj).T)
        better = d < best; best[better] = d[better]; chain[better] = S[i] + t[better] * (S[i + 1] - S[i])
    return chain.reshape(XX.shape)


def load_levels(return_bounds=False):
    """Daily pool levels per fixed source (held before the breach, gap-limited after) + ICESat-2 passes with their own chainage.
    A post-breach CENSORED_UPPER_BOUND caps its source on that day and the gap before it is interpolated towards the bound."""
    raw = pd.read_csv(SD / "p61_pool_levels_2023.csv", parse_dates=["date"])
    cens = raw[(raw.quality == "CENSORED_UPPER_BOUND") & raw.source.isin([k for k, v in SOURCES.items() if v is not None]) & (raw.date >= BREACH)]
    lv = raw[raw.source.isin(SOURCES) & raw.quality.isin(GOOD_Q)]
    lv = lv[(lv.date >= DATES[0]) & (lv.date <= DATES[-1])].copy()
    # Paper 1 v6 frame (2026-09-30): p60/p61 built the SWOT outlet as wse + geoid_hght + free2mean - zeta + c_tide-free (-0.173 m). SWOT's
    # crust is already mean-tide (no free2mean) and the production closure of the reservoir is -0.135 m: +0.073 m, which reproduces Paper 1's
    # outlet levels (17.61 m on 31 May, 5.71 m on 13 June). Gauges (BS-77 + EPSG:9902) and the ICESat-2 pass levels (tide-free heights with
    # their own tide-free c) are already in Paper 1's frame.
    sw = lv.source == "SWOT_OUTLET"
    lv.loc[sw, "H_evrf2019"] = lv.loc[sw, "H_evrf2019"] - PF.free2mean(lv.loc[sw, "lat"]) + PF.mixed_chain_shift()
    lv["chain"] = [SOURCES[s_] if SOURCES[s_] is not None else float(c) for s_, c in zip(lv.source, lv.chain_km)]
    fixed = {k: v for k, v in SOURCES.items() if v is not None}
    daily = lv[lv.source.isin(fixed)].groupby(["date", "source"]).H_evrf2019.median().unstack().reindex(DATES)
    for src in fixed:
        if src in daily.columns:
            pre, post = daily.loc[:BREACH - pd.Timedelta(days=1), src], daily.loc[BREACH:, src]
            pre = pre.ffill().bfill()                                                   # the pool is level and steady before the breach: hold, never interpolate across it
            obs_post = post.copy()                                                      # observed values only
            if src == "SWOT_OUTLET":
                post = post.interpolate(limit=3, limit_direction="forward")
            elif src != "GREALM_S6A":                                                   # daily gauges: a short hold
                post = post.ffill(limit=2)
            # G-REALM (~10-day altimetry) enters only on its own day after the breach, like the ICESat-2 passes: holding its
            # 9 June level over 10-11 June put a 2 m hump above the observed Nikopol level upstream (check of 2026-09-30)
            for d_, b_ in cens[cens.source == src].groupby("date").H_evrf2019.min().items():
                last = obs_post.loc[:d_ - pd.Timedelta(days=1)].last_valid_index()      # the gap before the bound: linear towards it, not held above it
                if last is not None and (d_ - last).days <= 3:
                    n = (d_ - last).days
                    for k in range(1, n):
                        post.loc[last + pd.Timedelta(days=k)] = obs_post.loc[last] + (b_ - obs_post.loc[last]) * k / n
                post.loc[d_] = min(post.loc[d_], b_) if np.isfinite(post.loc[d_]) else b_   # the bound caps its own day
            daily[src] = pd.concat([pre, post])
    extra = lv[~lv.source.isin(fixed)]                                                  # ICESat-2 passes with their own chainage
    if return_bounds:                                                                   # days whose surface rests on a bound: the bound's day and the filled days before it
        ub = set()
        for r in cens.itertuples():
            last = lv[(lv.source == r.source) & (lv.date < r.date)].date.max()
            ub |= {str(x.date()) for x in pd.date_range(last + pd.Timedelta(days=1), r.date)}
        return daily, extra, fixed, sorted(ub)
    return daily, extra, fixed


def load_pool():
    """Seamless 50 m DEM, pre-breach pool mask (plausible bed only), transform, CRS and cell-centre coordinates."""
    pool = CFG.load_utm("reservoir_full_pool_prebreach")
    with rasterio.open(CFG.BULK_ROOT / "dem_seamless" / "dem_seamless_evrf2019_50m.tif") as s:
        dem = s.read(1).astype("f4"); dem[dem == s.nodata] = np.nan; tr = s.transform; crs = s.crs
        mask = features.rasterize([(pool.__geo_interface__, 1)], out_shape=dem.shape, transform=tr, fill=0, dtype="uint8").astype(bool)
        xs = tr.c + tr.a * (np.arange(s.width) + 0.5); ys = tr.f + tr.e * (np.arange(s.height) + 0.5)
    mask &= np.isfinite(dem) & (dem > -30) & (dem < 40)
    return dem, mask, tr, crs, xs, ys


def day_points(d, daily, extra, fixed):
    """(chainage km, level m) anchors of the sloped surface on day d, sorted by chainage."""
    pts = [(fixed[s_], daily.loc[d, s_]) for s_ in fixed if s_ in daily.columns and np.isfinite(daily.loc[d, s_])]
    pts += [(float(r.chain), float(r.H_evrf2019)) for r in extra[extra.date == d].itertuples()]
    return sorted(pts)


def sloped_wse(pts, chain):
    """Water surface on the pool grid, linear in chainage between the day's anchors."""
    cs, hs = np.array([p[0] for p in pts]), np.array([p[1] for p in pts])
    return np.interp(chain, cs, hs).astype("f4")


def main():
    t0 = time.time()
    daily, extra, fixed, upper = load_levels(return_bounds=True)
    q = pd.read_csv(SD / "dniprohes_releases.csv", parse_dates=["date"]).set_index("date").discharge_m3s.reindex(DATES)
    kh = pd.read_csv(CFG.TABLES / "p59_swot_vs_kherson.csv", parse_dates=["date"]).set_index("date").H_gauge_evrf.reindex(DATES)
    hyp = pd.read_csv(SD / "hist2_hypsometry.csv")
    dem, mask, tr, _, xs, ys = load_pool()
    chain = chainage_grid(xs, ys); cell_km2 = abs(tr.a * tr.e) / 1e6
    # DEM hypsometry (level surface) for reference
    hrows = []
    for h in np.arange(5.0, 18.5, 0.5):
        w = mask & (dem < h); hrows.append(dict(level_evrf2019_m=h, A_dem_km2=round(float(w.sum()) * cell_km2, 1), V_dem_km3=round(float(np.nansum((h - dem[w]))) * cell_km2 * 1e6 / 1e9, 3)))
    H = pd.DataFrame(hrows)
    H["level_bs77_m"] = (H.level_evrf2019_m - BS77_TO_EVRF).round(2)
    # review F13: the design table is defined from 10 m BS up; outside its range the answer is NaN, never the endpoint plateau
    H["A_table19_km2"] = bounded_interp(H.level_bs77_m, hyp.water_level_m, hyp.A_table19_km2); H["V_table19_km3"] = bounded_interp(H.level_bs77_m, hyp.water_level_m, hyp.V_table19_km3)
    H.to_csv(CFG.TABLES / "p95f_hypsometry_dem.csv", index=False)
    dn = pd.read_csv(CFG.TABLES / "p95_daily_area_pooled_connected_ceiling.csv"); dn["date"] = pd.to_datetime(dn.date)
    vd = dn[dn.region.isin(["DNIPRO_CORRIDOR", "INHULETS_VALLEY_rect"])].groupby("date").new_volume_hm3.sum().reindex(DATES)
    ad = dn[dn.region.isin(["DNIPRO_CORRIDOR", "INHULETS_VALLEY_rect"])].groupby("date").potential_km2.sum().reindex(DATES)
    rows = []
    for d in DATES:
        pts = day_points(d, daily, extra, fixed)
        if len(pts) < 2 or d > pd.Timestamp("2023-06-13"):                             # after 13 June the pool is a river at 2-5 m: no pool volume
            rows.append(dict(date=str(d.date()), n_level_sources=len(pts), H_outlet_m=daily.loc[d].get("SWOT_OUTLET", np.nan),
                             kherson_stage_m=float(kh.loc[d]) if np.isfinite(kh.loc[d]) else np.nan, Q_in_dniprohes_m3s=float(q.loc[d]) if np.isfinite(q.loc[d]) else np.nan,
                             downstream_new_volume_hm3=float(vd.loc[d]) if np.isfinite(vd.loc[d]) else np.nan, downstream_total_water_km2=float(ad.loc[d]) if np.isfinite(ad.loc[d]) else np.nan,
                             phase="post-drawdown (pool volume not defined)" if d > pd.Timestamp("2023-06-13") else "insufficient level sources")); continue
        if len(pts) < 2:
            rows.append(dict(date=str(d.date()), n_level_sources=len(pts))); continue
        hs = np.array([p[1] for p in pts]); wse = sloped_wse(pts, chain)                # sloped surface along the chainage
        w = mask & (dem < wse); A = float(w.sum()) * cell_km2; V = float(np.nansum((wse - dem)[w])) * cell_km2 * 1e6 / 1e9
        rows.append(dict(date=str(d.date()), n_level_sources=len(pts), H_outlet_m=daily.loc[d].get("SWOT_OUTLET", np.nan), H_nikopol_m=daily.loc[d].get("NIKOPOL_UHE", np.nan),
                         H_rozumivka_m=daily.loc[d].get("ROZUMIVKA_GAUGE", np.nan), gradient_m=float(hs[-1] - hs[0]), A_pool_km2=round(A, 1), V_pool_km3=round(V, 3),
                         A_table19_at_outlet_km2=float(bounded_interp(daily.loc[d].get("SWOT_OUTLET", np.nan) - BS77_TO_EVRF, hyp.water_level_m, hyp.A_table19_km2)) if np.isfinite(daily.loc[d].get("SWOT_OUTLET", np.nan)) else np.nan,
                         Q_in_dniprohes_m3s=float(q.loc[d]) if np.isfinite(q.loc[d]) else np.nan, kherson_stage_m=float(kh.loc[d]) if np.isfinite(kh.loc[d]) else np.nan,
                         downstream_new_volume_hm3=float(vd.loc[d]) if np.isfinite(vd.loc[d]) else np.nan, downstream_total_water_km2=float(ad.loc[d]) if np.isfinite(ad.loc[d]) else np.nan,
                         phase="pre-breach" if d < BREACH else "drawdown", surface_upper_bound=str(d.date()) in upper))
    R = pd.DataFrame(rows); R["dV_pool_hm3"] = (R.V_pool_km3.diff() * 1000).round(1)
    R["Q_in_hm3_day"] = (R.Q_in_dniprohes_m3s * 86400 / 1e6).round(1); R["Q_out_breach_est_hm3_day"] = (R.Q_in_hm3_day - R.dV_pool_hm3).round(1)
    R["Q_out_breach_est_m3s"] = (R.Q_out_breach_est_hm3_day * 1e6 / 86400).round(0)
    R["cum_released_km3"] = ((R.V_pool_km3.iloc[0] - R.V_pool_km3)).round(3)
    R.to_csv(CFG.TABLES / "p95f_reservoir_daily.csv", index=False)
    man = dict(sources=dict(levels=str(SD / "p61_pool_levels_2023.csv"), inflow=str(SD / "dniprohes_releases.csv"), hypsometry=str(SD / "hist2_hypsometry.csv"),
                            dem="dem_seamless_evrf2019_50m.tif (Paper 2, kriged bed inside the pool)", pool="reservoir_full_pool_prebreach (Kakhovka_SA_2.geojson, 2174.7 km2)"),
               method="sloped daily surface interpolated along the SWORD chainage between outlet (SWOT), Nikopol (press), Rozumivka (gauge), G-REALM; integrated under the DEM inside the pool polygon; chainage = polyline dam-Nikopol-Rozumivka scaled to SWORD anchors",
               bs77_to_evrf_m=BS77_TO_EVRF, surface_upper_bound_days=upper, pool_cells=int(mask.sum()), cell_km2=cell_km2, seconds=round(time.time() - t0))
    (CFG.TABLES / "p95f_manifest.json").write_text(json.dumps(man, indent=1))
    pd.set_option("display.width", 250)
    print(R[(R.date >= "2023-06-04") & (R.date <= "2023-06-24")][["date", "H_outlet_m", "H_nikopol_m", "H_rozumivka_m", "gradient_m", "A_pool_km2", "V_pool_km3", "dV_pool_hm3", "Q_in_hm3_day", "Q_out_breach_est_m3s", "downstream_new_volume_hm3", "downstream_total_water_km2", "kherson_stage_m"]].to_string(index=False))
    print(H[H.level_evrf2019_m.isin([16.0, 14.0, 12.0, 10.0, 8.0])].to_string(index=False)); print("-> tables/p95f_*.csv", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
