# New in floodstate-eo, 2026-09-29 (maintainer: "подивись що можна витягнути з Інгульця ... Калинінське 80575 особливо"). STATUS: ACTIVE.
"""P95k -- the Inhulets gauge Kalynivske (80575) as an INDEPENDENT in-situ check of the reconstructed water surface in the
Inhulets valley (the gauge takes no part in p95 / p95e; in the `_inhulets_gauge_node` sensitivity of p95 it becomes an input).

Gauge record: UkrHMC hydrological yearbook 2023, vol. 2, table 1.2 (daily levels), file 80575U_2023.xls, parsed by the
ingestion job 378b6706 of the icesat2-atl13-kakhovka repository (ГІДРОЛОГІЯ_2023.zip; parser confidence 0.9); date-only daily
values (the 11:00 UTC SWOT passes and the daily yearbook value are not simultaneous -- during the rise the level changed by up to
2.4 m in a day). Table 1.2 gives daily MEAN levels in cm above the gauge zero (means of the observation terms, more frequent during
the event), the monthly highest and lowest levels ('Вищий', 'Нижчий') and the highest level of the year with its date: the peak, the
rise and the record use that highest level (HIGHEST, cross-checked against the ingested monthly maxima), the day-by-day comparison
with the reconstruction uses the daily means (the only daily values). Gauge zero -1.34 m BS from the header of the yearbook sheet
('Відмітка нуля поста -1.34 м БС'): the passport table's '1.34' carries no sign, and +1.34 m was used until 2026-09-29 (every
Kalynivske level 2.68 m too high). Station passport (maintainer's table, 2026-09-29): 47°07' N 32°58' E, floodplain exit
490 cm, multi-year extremes 1 and 710 cm; the post at 47°6'59" N 32°57'38" E (station catalogue of the Kakhovka hydrometeorological
observatory; the point located from the yearbook remark -- road bridge 0.75 km upstream -- lies ~165 m east). Kryvyi Rih 80568: the
store's 2023 levels were checked against the yearbook table 1.2 given by the maintainer (June: 295, 289, 303 on 3-19 June, 300, 297 cm;
1-2 June are the annual minimum), and its discharges against table 1.3 (June 0.68-3.86 m3/s). Upstream posts on the same river (Kryvyi Rih 80568, Iskrivka 80564,
Oleksandro-Stepanivka 80561) show whether the rise came from the Inhulets itself or from the Dnipro (backwater).
Vertical frame: H_EVRF2019 = zero_BS77 + stage + delta_EPSG9902(lon, lat) -- the official grid step used for every gauge of
the series (Paper 1; `ua_2019z.asc`, bilinear), never an empirical alignment.

Comparison: the reconstructed water surface (p95 engine, map-anchored, evaluated at the gauge) per day with its support (nodes
within 3 km / nearest node farther away, its river and distance), the terrain at the gauge cell (seamless terrain-bed model,
rev 6 residual bias removed), the days on which the gauge level stands above that terrain, and the days on which the
reconstruction has new inundation at the gauge cell (daily_new.npz of the primary run).

Outputs: <case_study>/tables/p95k_inhulets_kalynivske.csv (per day), p95k_inhulets_summary.csv, p95k_manifest.json;
         <case_study>/figures/m6_v003A/p95k_inhulets_kalynivske.png
"""
from __future__ import annotations
import glob, hashlib, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from affine import Affine
from rasterio.warp import transform as tf_transform
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.terrain.vertical import read_esri_ascii_grid, sample_esri_ascii_grid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = ROOT / "figures" / "m6_v003A"
ICE = Path(CFG._ICESAT2_SIBLING)
STORE = ICE / "data/1_data/data/parquet"
JOB = "378b6706-0e1d-45eb-b815-e07e6bff5dd4"                              # ingestion of ГІДРОЛОГІЯ_2023.zip (UkrHMC yearbook 2023)
EPSG9902_GRID = ICE / "data/external/datum/ua_2019z.asc"
# station passports (maintainer's table, 2026-09-29): lat, lon (degree-minute), zero m BS-77, floodplain-exit cm, multi-year extremes cm
# Kalynivske: the station catalogue of the Kakhovka hydrometeorological observatory (maintainer, 2026-09-29): 47°6'59" N 32°57'38" E
# (to the second). Kept for provenance: the point located from the yearbook remark (road bridge 0.75 km upstream; ~165 m east) and the
# passport's degree-minute position (47°07' N 32°58' E)
POSTS = {80575: dict(name="Inhulets - Kalynivske", lat=47 + 6 / 60 + 59 / 3600, lon=32 + 57 / 60 + 38 / 3600,
                     coord_source="station catalogue, Kakhovka hydrometeorological observatory (Kherson oblast): 47°6'59\" N 32°57'38\" E",
                     lat_bridge_estimate=47.11628141526601, lon_bridge_estimate=32.96271606822572, lat_passport=47 + 7 / 60, lon_passport=32 + 58 / 60,
                     zero_bs77_m=-1.34, zero_source="yearbook 2023 vol. 2 table 1.2 header, 80575U_2023.xls: 'Відмітка нуля поста -1.34 м БС' (passport table: '1.34', no sign)",
                     floodplain_exit_cm=490, extremes_cm=(1, 710)),
         80568: dict(name="Inhulets - Kryvyi Rih", lat=47 + 53 / 60 + 50.20 / 3600, lon=33 + 20 / 60 + 13.55 / 3600, lat_passport=47 + 54 / 60, lon_passport=33 + 21 / 60,
                     coord_source="station catalogue, Dnipropetrovsk regional hydrometeorological centre: 47°53'50.20\" N 33°20'13.55\" E",
                     zero_bs77_m=27.57, zero_source="yearbook 2023 vol. 2 table 1.2 header, 80568U_2023.xls: 'Відмітка нуля поста 27.57 м БС-77'",
                     floodplain_exit_cm=500, extremes_cm=(280, 811)),
         80564: dict(name="Inhulets - Iskrivka", lat=48 + 12 / 60, lon=33 + 23 / 60, zero_bs77_m=56.34, floodplain_exit_cm=None, extremes_cm=(384, 1028),
                     zero_source="yearbook 2023 vol. 2 table 1.2 header, 80564U_2023.xls: 'Відмітка нуля поста 56.34 м БС-77' (passport table: 56.44)"),
         80561: dict(name="Inhulets - Oleksandro-Stepanivka", lat=48 + 37 / 60, lon=33 + 9 / 60, zero_bs77_m=81.99, floodplain_exit_cm=None, extremes_cm=(44, 497),
                     zero_source="yearbook 2023 vol. 2 table 1.2 header, 80561U_2023.xls: 'Відмітка нуля поста 81.99 м БС'")}
GAUGE = 80575
# the liman: Southern Bug - Mykolaiv 98027 (yearbook 2023 vol. 1 table 1.2, same ingestion job). Graph zero -5.00 m BS-77 in the header of
# the 2023 sheet and of the 2021 yearbook ("Відмітка нуля поста -5.00 м БС"; icesat2-atl13-kakhovka config/gauges.yaml; likely a rounded
# nominal): the levels of ~500 cm above the zero are ~0 m BS-77, the liman at sea level;
# position from the station catalogue of the Mykolaiv hydrometeorological centre (maintainer, 2026-09-29); wind setup / setdown
# dominates the regime (+-0.3..0.5 m events). Outside the terrain domain: only the water surface is compared.
LIMAN = dict(post=98027, name="Southern Bug - Mykolaiv", lat=46 + 59 / 60 + 3.75 / 3600, lon=31 + 58 / 60 + 19.46 / 3600,
             coord_source="station catalogue, Mykolaiv hydrometeorological centre: 46°59'3.75\" N 31°58'19.46\" E",
             lat_surveyed=46 + 59 / 60 + 3.5 / 3600, lon_surveyed=31 + 58 / 60 + 15.3 / 3600, zero_bs77_m=-5.00,
             zero_source="yearbook 2023 vol. 1 table 1.2 header, 98027U_2023.xls, and the 2021 yearbook: 'Відмітка нуля поста -5.00 м БС'")
# the yearbook's highest level of the year ('За рік' -> 'Вищий': level, date), an instantaneous value from the observation terms -- not
# a daily mean. Transcribed from the 2023 sheets (UkrHMC, ГІДРОЛОГІЯ_2023) and checked against the June maximum of the ingested monthly
# parquet (same job). '*' marks the highest of the whole record period; the parentheses of '(772*)' -- meaning to be confirmed from
# the yearbook legend (usually an approximate or indirectly determined value; pile No. 5 was re-levelled during the event).
HIGHEST = {80575: dict(stage_cm=772, date="2023-06-10", printed="(772*)", record_period="1927-1941, 1944-2023",
                       source="80575U_2023.xls (vol. 2, table 1.2): June 'Вищий' 772; 'За рік' (772*) 10.06; '1927-1941, 1944-2023' (772*) 10.06.2023"),
           98027: dict(stage_cm=602, date="2023-06-08", printed="602*", record_period="1963-2023",
                       source="98027U_2023.xls (vol. 1, table 1.2): June 'Вищий' 602; 'За рік' 602* 08.06; '1963-2023' 602* 08.06.2023")}
FLOODPLAIN_RADIUS_M = 250.0                                                  # land (non-water, FABDEM) cells around the post = its floodplain
# the yearbook's station remark (maintainer, 2026-09-29), verbatim, and its reading
YEARBOOK_REMARK = ("114. р. Інгулець – с. Калинівське. Внаслідок СГЯ змінила приводку паля № 5. З 07-18.06.2023 року різко піднявся рівень води. "
                   "Максимальний рівень води сформувався внаслідок підриву Каховської ГЕС. Були проведені почащені спостереження. Негативні наслідки "
                   "затоплення житлових будинків, автомобільного моста (0,75 км вище поста).")
REMARK_PERIOD = ("2023-06-07", "2023-06-18")                               # "з 07-18.06.2023 року різко піднявся рівень води"
REMARK_READING = ("the yearbook attributes the maximum to the destruction of the Kakhovka HPP; high water 7-18 June; observations were made more "
                  "often than the two daily terms during the event (daily values are means of them); houses and the road bridge 0.75 km upstream were "
                  "flooded; CAVEAT: the levelling of pile No. 5 changed during the hazard (date and size not given), so levels read on it may carry a "
                  "datum step -- post-event levels are not comparable with pre-event levels without that correction")


def _ld(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def yearbook_daily(post: int, year: int = 2023, variable: str = "level"):
    """Daily yearbook values of `post` (level: cm above the gauge zero, table 1.2; discharge: m3/s, table 1.3) written by the
    ingestion job JOB; (frame indexed by date, parquet path, sha256)."""
    for f in sorted(glob.glob(str(STORE / "*" / "daily" / f"post_id={post}" / f"year={year}" / "data.parquet"))):
        d = pd.read_parquet(f)
        if "ingestion_job_id" in d.columns and (d.ingestion_job_id == JOB).all() and (d.variable == variable).any():
            d = d[d.variable == variable].copy(); d["date"] = pd.to_datetime(d.date)
            return d.set_index("date").sort_index(), f, hashlib.sha256(Path(f).read_bytes()).hexdigest()
    return None, None, None


def yearbook_monthly(post: int, year: int = 2023, variable: str = "level"):
    """Monthly yearbook statistics of `post` (mean, highest 'max', lowest 'min'; cm) written by the ingestion job JOB."""
    for f in sorted(glob.glob(str(STORE / "*" / "monthly" / f"post_id={post}" / f"year={year}" / "data.parquet"))):
        d = pd.read_parquet(f)
        if "ingestion_job_id" in d.columns and (d.ingestion_job_id == JOB).all() and (d.variable == variable).any():
            return d[d.variable == variable].set_index("month").sort_index()
    return None


def highest(post: int, zero_m: float, delta_m: float):
    """The yearbook's highest level of `post` (HIGHEST) in cm above the gauge zero, m BS-77 and m EVRF2019; checked against the
    ingested monthly maximum of its month."""
    h = dict(HIGHEST[post]); m = yearbook_monthly(post)
    mon = int(h["date"][5:7])
    if m is not None:
        assert float(m.loc[mon, "max"]) == h["stage_cm"], (post, float(m.loc[mon, "max"]), h["stage_cm"])
    h.update(checked_against_monthly_parquet=m is not None, bs77_m=round(zero_m + h["stage_cm"] / 100.0, 3),
             H_evrf2019_m=round(zero_m + h["stage_cm"] / 100.0 + delta_m, 3))
    return h


def liman_check(W, P95, z9902, h9902, kh):
    """The liman gauge Mykolaiv (98027) against the reconstructed water surface extrapolated to it, and against Kherson."""
    d, f, sha = yearbook_daily(LIMAN["post"])
    if d is None:
        return None
    delta = float(sample_esri_ascii_grid(z9902, h9902, LIMAN["lon"], LIMAN["lat"]))
    x, y = tf_transform("EPSG:4326", CFG.CRS_METRIC, [LIMAN["lon"]], [LIMAN["lat"]]); x, y = x[0], y[0]
    Gd = dict(transform=Affine(20.0, 0.0, np.floor(x / 20) * 20 - 20, 0.0, -20.0, np.floor(y / 20) * 20 + 40), ny=3, nx=3, crs=CFG.CRS_METRIC)
    Z = W.prepare(Gd); iN = int(Z["i1"][0]); dN = float(Z["d1"][0])
    rows = []
    for j, dt in enumerate(W.dates):
        ds = str(dt.date()); st = d.value.get(dt, np.nan); fl = d.flag.get(dt) if "flag" in d.columns else None
        H = LIMAN["zero_bs77_m"] + st / 100.0 + delta if np.isfinite(st) else np.nan
        rows.append(dict(date=ds, post_id=LIMAN["post"], lat=LIMAN["lat"], lon=LIMAN["lon"], stage_cm=st, flag=fl if isinstance(fl, str) else "", zero_bs77_m=LIMAN["zero_bs77_m"],
                         delta_epsg9902_m=round(delta, 4), H_evrf2019_m=round(H, 3) if np.isfinite(H) else np.nan, H_reconstructed_primary_m=round(float(W.field(Z, ds)[1, 1]), 3),
                         support_primary=P95.SUPPORT_KIND.get(int(W.support_kind(Z, ds)[1, 1])), gauge_capped=bool(Z["far"][0]), nearest_node_id=W.node_id[iN],
                         nearest_node_river=W.river[iN], nearest_node_km=round(dN / 1e3, 2), kherson_gauge_m=round(float(W.H[-1, j]), 3)))
    L = pd.DataFrame(rows); L["recon_minus_gauge_m"] = (L.H_reconstructed_primary_m - L.H_evrf2019_m).round(3); L["kherson_minus_mykolaiv_m"] = (L.kherson_gauge_m - L.H_evrf2019_m).round(3)
    p_ = L[(L.date >= "2023-05-26") & (L.date <= "2023-06-05")]            # event-relative error: free of any constant datum offset
    L["recon_rise_m"] = (L.H_reconstructed_primary_m - p_.H_reconstructed_primary_m.median()).round(3); L["gauge_rise_m"] = (L.H_evrf2019_m - p_.H_evrf2019_m.median()).round(3)
    L["e_rise_m"] = (L.recon_rise_m - L.gauge_rise_m).round(3)
    L.to_csv(CFG.TABLES / "p95k_liman_mykolaiv.csv", index=False)
    pre = L[(L.date >= "2023-05-26") & (L.date <= "2023-06-05")]; ev = L[(L.date >= "2023-06-06") & (L.date <= "2023-06-20")]; late = L[(L.date >= "2023-06-21") & (L.date <= "2023-06-30")]
    im = L.H_evrf2019_m.idxmax(); ik = L.kherson_gauge_m.idxmax(); pm = pre.H_evrf2019_m.median(); pc = pre.stage_cm.median()
    hi = highest(LIMAN["post"], LIMAN["zero_bs77_m"], delta); km = yearbook_monthly(80805)
    od = [str(t.date()) for t, o in zip(W.dates, W.obs[iN]) if o]
    ob_before = max((t for t in od if t < "2023-06-06"), default="none"); ob_after = min((t for t in od if t >= "2023-06-06"), default="none")
    kh_hi = f"; its June highest {km.loc[6, 'max']:.0f} cm" if km is not None else ""
    S = [dict(id="gauge_max", item="liman maximum at Mykolaiv: the yearbook's highest level",
              value=f"{hi['stage_cm']} cm above the gauge zero = {hi['bs77_m']:+.2f} m BS-77 = {hi['H_evrf2019_m']:.2f} m EVRF2019 on {hi['date']} (printed '{hi['printed']}': the highest of {hi['record_period']})"),
         dict(id="gauge_max_daily_mean", item="highest daily mean", value=f"{L.stage_cm[im]:.0f} cm = {L.H_evrf2019_m[im]:.2f} m EVRF2019 on {L.date[im]}"),
         dict(id="pre_breach_level", item="pre-breach level 26 May - 5 June (median of the daily means)", value=f"{pc:.0f} cm = {LIMAN['zero_bs77_m'] + pc / 100:+.2f} m BS-77 = {pm:.2f} m EVRF2019"),
         dict(id="rise", item="rise to the highest level (in daily means)",
              value=f"{(hi['stage_cm'] - pc) / 100:.2f} m ({(L.stage_cm[im] - pc) / 100:.2f} m); Kherson: {L.kherson_gauge_m[ik] - pre.kherson_gauge_m.median():.2f} m (daily values = yearbook 80805{kh_hi})"),
         dict(id="pre_breach_evrf", item="pre-breach level, m EVRF2019", value=f"{pm:.2f} m EVRF2019"),
         dict(id="highest_evrf", item="highest level, m EVRF2019 and date", value=f"{hi['H_evrf2019_m']:.2f} m EVRF2019 on {hi['date']}"),
         dict(id="rise_m", item="rise to the highest level, m", value=f"{(hi['stage_cm'] - pc) / 100:.2f} m"),
         dict(id="lag_after_kherson", item="lag of the liman maximum after the Kherson peak stage", value=f"{(pd.Timestamp(L.date[im]) - pd.Timestamp(L.date[ik])).days} d"),
         dict(id="late_june", item="21-30 June above the pre-breach level (median)", value=f"{late.H_evrf2019_m.median() - pm:+.2f} m"),
         dict(id="kherson_minus_mykolaiv", item="Kherson - Mykolaiv water level: pre-breach median / on the Kherson peak day", value=f"{pre.kherson_minus_mykolaiv_m.median():+.2f} m / {L.kherson_minus_mykolaiv_m[ik]:+.2f} m"),
         dict(id="reconstruction_support", item="reconstructed surface at the gauge: nearest SWOT node / Kherson cap", value=f"{W.node_id[iN]} ({W.river[iN]}), {dN / 1e3:.1f} km; capped at the Kherson gauge: {bool(Z['far'][0])}"),
         dict(id="serving_node_unobserved", item="that node without observation", value=f"{(pd.Timestamp(ob_before) + pd.Timedelta(days=1)).date()} .. {(pd.Timestamp(ob_after) - pd.Timedelta(days=1)).date()}" if "none" not in (ob_before, ob_after) else "n/a"),
         dict(id="serving_node_gap", item="observations of that node around the event",
              value=f"E {W.xy[iN, 0] / 1e3:.1f} km, N {W.xy[iN, 1] / 1e3:.1f} km (EPSG:32636): last observed {ob_before}, next {ob_after}; interpolated across the flood"),
         dict(id="recon_minus_gauge", item="reconstruction - gauge: pre-breach median / 6-20 June median (range)", value=f"{pre.recon_minus_gauge_m.median():+.2f} m / {ev.recon_minus_gauge_m.median():+.2f} m ({ev.recon_minus_gauge_m.min():+.2f} .. {ev.recon_minus_gauge_m.max():+.2f})"),
         dict(id="e_rise_at_max", item="event-relative error (reconstructed rise - gauge rise) on the liman's maximum day", value=f"{L.e_rise_m[im]:+.2f} m on {L.date[im]} (reconstructed rise {L.recon_rise_m[im]:+.2f} m)"),
         dict(id="e_abs_at_max", item="absolute error (reconstruction - gauge, daily means) on the liman's maximum day", value=f"{L.recon_minus_gauge_m[im]:+.2f} m on {L.date[im]}"),
         dict(id="role", item="role of the gauge", value="withheld validation site (never an input): tests the water surface of the western delta, served by a SWOT node unobserved across the flood; Kherson 80805 is the input and anchor, Kalynivske 80575 the withheld tributary site"),
         dict(id="flags", item="days flagged in the yearbook", value=", ".join(f"{r.date} '{r.flag}'" for r in L[L.flag != ""].itertuples()) + " -- meaning of '/' to be confirmed from the yearbook legend"),
         dict(id="caveats", item="caveats", value="graph zero -5.00 m BS-77 is a rounded nominal (absorbs a zero error); wind setup / setdown of +-0.3-0.5 m is part of the regime; date-only daily values; outside the terrain domain (no inundation check)")]
    pd.DataFrame(S).to_csv(CFG.TABLES / "p95k_liman_summary.csv", index=False)
    t_ = pd.to_datetime(L.date); fig, ax = plt.subplots(figsize=(9.5, 3.8), constrained_layout=True)
    ax.plot(t_, L.H_evrf2019_m, "o-", color="#0b0b0b", ms=3, lw=1.5, label="gauge Mykolaiv 98027, liman (yearbook daily means, EVRF2019; independent)")
    ax.plot(pd.Timestamp(hi["date"]), hi["H_evrf2019_m"], "*", color="#0b0b0b", ms=9, label=f"highest level of the year {hi['printed']} cm, {hi['date'][8:]}.{hi['date'][5:7]}")
    ax.plot(t_, L.kherson_gauge_m, "-", color="#52514e", lw=1.2, label="Kherson gauge 80805 (Dnipro)")
    ax.plot(t_, L.H_reconstructed_primary_m, "-", color="#2a78d6", lw=1.4, label=f"reconstructed surface extrapolated to the gauge (nearest node {dN / 1e3:.0f} km; Kherson cap {bool(Z['far'][0])})")
    ax.axvline(pd.Timestamp("2023-06-06"), color="#e34948", lw=0.8); ax.set_xlim(pd.Timestamp("2023-05-26"), pd.Timestamp("2023-07-10"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b")); ax.set_ylabel("water level, m EVRF2019", fontsize=8); ax.grid(color="#efece6"); ax.tick_params(labelsize=7)
    ax.legend(fontsize=6.5, frameon=False, loc="upper right"); ax.set_title("The Dnipro-Buh liman at Mykolaiv during the Kakhovka flood (outside the terrain domain: water surface only)", fontsize=8, loc="left")
    fig.savefig(FIG / "p95k_liman_mykolaiv.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    return dict(post=LIMAN["post"], parquet=f, sha256=sha, delta_epsg9902_m=delta, xy_epsg32636=[round(x, 1), round(y, 1)], highest=hi, **{k: v for k, v in LIMAN.items() if k != "post"})


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    z9902, h9902 = read_esri_ascii_grid(EPSG9902_GRID)
    st = {}
    for post, meta in POSTS.items():
        d, f, sha = yearbook_daily(post)
        if d is not None:
            st[post] = dict(meta, series=d.value, flags=d.get("flag"), source_file=str(d.source_file.iloc[0]), parquet=f, sha256=sha,
                            delta_epsg9902_m=float(sample_esri_ascii_grid(z9902, h9902, meta["lon"], meta["lat"])))
    g = st[GAUGE]
    qk, qf, qsha = yearbook_daily(80568, variable="discharge")                  # Inhulets discharge at Kryvyi Rih (yearbook table 1.3)
    Q = qk.value if qk is not None else pd.Series(dtype=float)
    P95 = _ld("p95_hand_daily_inundation"); W, dxm, dym, _ = P95.load_engine()
    x, y = tf_transform("EPSG:4326", CFG.CRS_METRIC, [g["lon"]], [g["lat"]]); x, y = x[0], y[0]
    Gd = dict(transform=Affine(20.0, 0.0, np.floor(x / 20) * 20 - 20, 0.0, -20.0, np.floor(y / 20) * 20 + 40), ny=3, nx=3, crs=CFG.CRS_METRIC)
    engines = {"primary": W}
    sens = CFG.TABLES / "p95_manifest_connected_ceiling_inhulets_gauge_node.json"
    if sens.exists() and (CFG.TABLES / "p95k_inhulets_kalynivske.csv").exists():
        engines["gauge_node_sensitivity"] = P95.load_engine(extra_nodes=P95.inhulets_gauge_node())[0]
    Zs = {k: e.prepare(Gd) for k, e in engines.items()}
    iN = int(Zs["primary"]["i1"][0]); dN = float(Zs["primary"]["d1"][0])
    # terrain and the primary run's daily new inundation at the gauge cell
    cell = {}
    for zn in P95.ZONES:                                                     # the post's cell is the river channel: use the floodplain around it
        with rasterio.open(CFG.BULK_ROOT / "dem_seamless" / f"{zn}_dem_evrf2019_20m.tif") as s:
            b = s.bounds
            if not (b.left <= x <= b.right and b.bottom <= y <= b.top):
                continue
            r, c = s.index(x, y); R_ = int(np.ceil(FLOODPLAIN_RADIUS_M / 20)); win = ((r - R_, r + R_ + 1), (c - R_, c + R_ + 1))
            raw = s.read(1, window=win).astype("f8"); G = dict(transform=s.transform, crs=s.crs, ny=s.height, nx=s.width)
        with rasterio.open(CFG.BULK_ROOT / "dem_seamless" / f"{zn}_dem_source_20m.tif") as ss:
            src = ss.read(1, window=win)
        wc = P95.worldcover_on(zn, G)[win[0][0]:win[0][1], win[1][0]:win[1][1]]
        E, _ = P95.terrain_residual_table(zn)
        bias = np.where(np.isin(src, P95.FABDEM_SOURCES), np.vectorize(lambda k: E.get(int(k), E["other"])["bias"])(wc), 0.0)
        terr = P95.PF.fabdem_to_paper1(raw, src).astype("f8") - bias                      # Paper 1 v6 frame, as in p95
        yy, xx = np.mgrid[-R_:R_ + 1, -R_:R_ + 1]; disk = np.hypot(yy, xx) * 20 <= FLOODPLAIN_RADIUS_M
        land = disk & (wc != 80) & np.isin(src, P95.FABDEM_SOURCES) & np.isfinite(terr)
        npz = np.load(P95.DYN / f"{zn}_connected_ceiling" / "daily_new.npz"); shp = tuple(int(v) for v in npz["shape"])
        share = {}
        for k in npz.files:
            if k.startswith("2023"):
                nw = np.unpackbits(npz[k], count=shp[0] * shp[1]).reshape(shp)[win[0][0]:win[0][1], win[1][0]:win[1][1]].astype(bool)
                share[k] = float(nw[land].mean()) if land.any() else np.nan
        cell = dict(zone=zn, row=int(r), col=int(c), channel_cell_terrain_raw_m=float(raw[R_, R_]), channel_cell_worldcover=int(wc[R_, R_]),
                    channel_cell_source=int(src[R_, R_]), floodplain_radius_m=FLOODPLAIN_RADIUS_M, floodplain_land_cells=int(land.sum()),
                    terrain_m=float(np.median(terr[land])), terrain_p25_m=float(np.percentile(terr[land], 25)), new_share=share)
    rows = []
    for j, dt in enumerate(W.dates):
        ds = str(dt.date()); stage = g["series"].get(dt, np.nan)
        r = dict(date=ds, post_id=GAUGE, lat=g["lat"], lon=g["lon"], stage_cm=stage, zero_bs77_m=g["zero_bs77_m"], delta_epsg9902_m=round(g["delta_epsg9902_m"], 4),
                 H_evrf2019_m=round(g["zero_bs77_m"] + stage / 100.0 + g["delta_epsg9902_m"], 3) if np.isfinite(stage) else np.nan)
        for k, e in engines.items():
            r[f"H_reconstructed_{k}_m"] = round(float(e.field(Zs[k], ds)[1, 1]), 3)
            r[f"support_{k}"] = P95.SUPPORT_KIND.get(int(e.support_kind(Zs[k], ds)[1, 1]))
        r.update(nearest_node_id=W.node_id[iN], nearest_node_river=W.river[iN], nearest_node_km=round(dN / 1e3, 2), nearest_node_observed=bool(W.obs[iN, j]),
                 kherson_gauge_m=round(float(W.H[-1, j]), 3))
        for post in (80568, 80564, 80561):
            if post in st:
                r[f"stage_{post}_cm"] = st[post]["series"].get(dt, np.nan)
        r["Q_80568_m3s"] = Q.get(dt, np.nan)
        if cell:
            sh = cell["new_share"].get(ds, np.nan)
            r.update(floodplain_terrain_m=round(cell["terrain_m"], 3), gauge_above_floodplain=bool(np.isfinite(r["H_evrf2019_m"]) and r["H_evrf2019_m"] > cell["terrain_m"]),
                     reconstructed_new_share_floodplain=round(sh, 3) if np.isfinite(sh) else np.nan, reconstructed_new_at_gauge=bool(np.isfinite(sh) and sh >= 0.5))
        rows.append(r)
    D = pd.DataFrame(rows); D["recon_minus_gauge_m"] = (D.H_reconstructed_primary_m - D.H_evrf2019_m).round(3)   # e_abs
    p_ = D[(D.date >= "2023-05-26") & (D.date <= "2023-06-05")]            # e_rise: event-relative, free of any constant datum offset
    D["recon_rise_m"] = (D.H_reconstructed_primary_m - p_.H_reconstructed_primary_m.median()).round(3); D["gauge_rise_m"] = (D.H_evrf2019_m - p_.H_evrf2019_m.median()).round(3)
    D["e_rise_m"] = (D.recon_rise_m - D.gauge_rise_m).round(3); D["same_river_support"] = D.nearest_node_river == "Inhulets"
    D.to_csv(CFG.TABLES / "p95k_inhulets_kalynivske.csv", index=False)
    # summary
    ev = D[(D.date >= "2023-06-06") & (D.date <= "2023-06-30")]; pre = D[D.date <= "2023-06-05"]
    imax = D.H_evrf2019_m.idxmax(); pk_kh = D.loc[D.kherson_gauge_m.idxmax(), "date"]
    above = D[(D.stage_cm >= g["floodplain_exit_cm"])]; hi = highest(GAUGE, g["zero_bs77_m"], g["delta_epsg9902_m"]); pc = pre.stage_cm.median()
    S = [dict(id="gauge_max", item="gauge maximum: the yearbook's highest level",
              value=f"{hi['stage_cm']} cm above the gauge zero = {hi['bs77_m']:+.2f} m BS-77 = {hi['H_evrf2019_m']:.2f} m EVRF2019 on {hi['date']} (printed '{hi['printed']}': the highest of {hi['record_period']})"),
         dict(id="gauge_max_daily_mean", item="highest daily mean", value=f"{D.stage_cm[imax]:.0f} cm = {D.H_evrf2019_m[imax]:.2f} m EVRF2019 on {D.date[imax]}"),
         dict(id="pre_breach_level", item="pre-breach level 26 May - 5 June (median of the daily means)", value=f"{pc:.0f} cm = {g['zero_bs77_m'] + pc / 100:+.2f} m BS-77 = {pre.H_evrf2019_m.median():.2f} m EVRF2019"),
         dict(id="rise", item="rise to the highest level (in daily means)", value=f"{hi['stage_cm'] - pc:.0f} cm ({D.stage_cm[imax] - pc:.0f} cm)"),
         dict(id="pre_breach_evrf", item="pre-breach level, m EVRF2019", value=f"{pre.H_evrf2019_m.median():.2f} m EVRF2019"),
         dict(id="highest_evrf", item="highest level, m EVRF2019 and date", value=f"{hi['H_evrf2019_m']:.2f} m EVRF2019 on {hi['date']}"),
         dict(id="rise_m", item="rise to the highest level, m", value=f"{(hi['stage_cm'] - pc) / 100:.2f} m"),
         dict(id="largest_daily_rise", item="largest daily rise", value=f"{D.stage_cm.diff().max():.0f} cm on {D.date[D.stage_cm.diff().idxmax()]}"),
         dict(id="days_above_floodplain_exit", item="days at or above the floodplain exit (490 cm)", value=f"{len(above)} ({above.date.min()} .. {above.date.max()})" if len(above) else "0"),
         dict(id="record_exceedance", item="multi-year maximum of the passport (710 cm) exceeded: highest level (daily mean)",
              value=f"by {hi['stage_cm'] - g['extremes_cm'][1]:.0f} cm ({D.stage_cm.max() - g['extremes_cm'][1]:.0f} cm); the yearbook marks {hi['printed']} as the highest of {hi['record_period']}" if hi["stage_cm"] > g["extremes_cm"][1] else "no"),
         dict(id="lag_after_kherson", item="lag of the gauge maximum after the Kherson peak stage", value=f"{(pd.Timestamp(D.date[imax]) - pd.Timestamp(pk_kh)).days} d (Kherson maximum {pk_kh})"),
         dict(id="upstream_posts", item="upstream posts 80568 / 80564 during 1-20 June (range, cm)", value="; ".join(f"{p}: {st[p]['series'].loc['2023-06-01':'2023-06-20'].min():.0f}-{st[p]['series'].loc['2023-06-01':'2023-06-20'].max():.0f}" for p in (80568, 80564) if p in st)),
         dict(id="nearest_node", item="nearest SWOT node to the gauge", value=f"{W.node_id[iN]} ({W.river[iN]}), {dN / 1e3:.1f} km; nodes within 3 km: {int(Zs['primary']['valid'][0].sum())}"),
         dict(id="recon_minus_gauge_pre", item="reconstruction - gauge, pre-breach (median)", value=f"{pre.recon_minus_gauge_m.median():+.2f} m"),
         dict(id="recon_minus_gauge_event", item="reconstruction - gauge, 6-20 June (median; range)", value=f"{ev[ev.date <= '2023-06-20'].recon_minus_gauge_m.median():+.2f} m; {ev[ev.date <= '2023-06-20'].recon_minus_gauge_m.min():+.2f} .. {ev[ev.date <= '2023-06-20'].recon_minus_gauge_m.max():+.2f} m"),
         dict(id="day_of_max", item="day of the maximum: gauge / reconstruction", value=f"{D.date[imax]} / {D.loc[D.H_reconstructed_primary_m.idxmax(), 'date']}")]
    # validation of the withheld gauge (maintainer's decision D-INHULETS, 2026-09-29): absolute error, event-relative error, timing, recession
    gmax = D.date[imax]; mmax = D.loc[D.H_reconstructed_primary_m.idxmax(), "date"]; p_ = D[(D.date >= "2023-05-26") & (D.date <= "2023-06-05")]
    rising = D[(D.date >= "2023-06-06") & (D.date < gmax)]; rec = D[(D.date > gmax) & (D.date <= "2023-06-20")]; late = D[(D.date >= "2023-06-21") & (D.date <= "2023-06-30")]
    ph = lambda c: (f"pre-breach median {p_[c].median():+.2f} m; rising limb 2023-06-06 .. {rising.date.max()}: {rising[c].max():+.2f} m ({rising.loc[rising[c].idxmax(), 'date']}) "
                    f".. {rising[c].min():+.2f} m; gauge maximum {gmax}: {D.loc[imax, c]:+.2f} m; recession to 2023-06-20: {rec[c].min():+.2f} .. {rec[c].max():+.2f} m; 21-30 June median {late[c].median():+.2f} m")
    rc = D[(D.date > gmax) & (D.date <= "2023-06-30")].reset_index(drop=True); zc = rc[rc.e_rise_m < 0].date.min(); im_ = rc.e_rise_m.idxmin()
    aft = rc.loc[im_:]; hold = (aft.e_rise_m.abs() <= 0.25).astype(int)[::-1].cumprod()[::-1].astype(bool); reconv = aft[hold].date.min() if hold.any() else "not before 1 July"
    nin = np.array([r == "Inhulets" for r in W.river]); gxy = np.array([x, y])
    d_inh = float(np.hypot(*(W.xy[nin] - gxy).T).min() / 1e3) if nin.any() else np.nan
    S += [dict(id="e_abs", item="absolute error e_abs = H_reconstructed - H_gauge (daily means)", value=ph("recon_minus_gauge_m")),
          dict(id="e_rise", item="event-relative error e_rise = (H_rec - H_rec,pre) - (H_gauge - H_gauge,pre); pre = 26 May - 5 June medians", value=ph("e_rise_m")),
          dict(id="peak_timing", item="day of the maximum: reconstruction - gauge", value=f"{(pd.Timestamp(mmax) - pd.Timestamp(gmax)).days:+d} d (reconstruction {mmax}, gauge {gmax})"),
          dict(id="rise_amplitude", item="rise to the maximum: reconstruction / gauge", value=f"{D.recon_rise_m.max():+.2f} m / {D.gauge_rise_m.max():+.2f} m (daily means; {(hi['stage_cm'] - pc) / 100:+.2f} m to the highest level)"),
          dict(id="recession", item="recession: e_rise after the gauge maximum",
               value=f"the reconstructed rise falls below the gauge's on {zc}; minimum {rc.e_rise_m.min():+.2f} m on {rc.date[im_]} (the reconstruction drains ahead of the valley); within +-0.25 m from {reconv} to 30 June"),
          dict(id="e_abs_rising_max", item="largest absolute error on the rising limb", value=f"{rising.recon_minus_gauge_m.max():+.2f} m on {rising.loc[rising.recon_minus_gauge_m.idxmax(), 'date']}"),
          dict(id="e_abs_recession", item="absolute error from the day after the gauge maximum to 20 June", value=f"{rec.recon_minus_gauge_m.min():+.2f} .. {rec.recon_minus_gauge_m.max():+.2f} m"),
          dict(id="e_rise_at_gauge_max", item="event-relative error on the day of the gauge maximum", value=f"{D.loc[imax, 'e_rise_m']:+.2f} m"),
          dict(id="e_rise_recession_min", item="most negative event-relative error after the gauge maximum", value=f"{rc.e_rise_m.min():+.2f} m on {rc.date[im_]}"),
          dict(id="reconvergence", item="event-relative error within +-0.25 m for good (to 30 June) from", value=f"{reconv}"),
          dict(id="support_node_km", item="distance of the Dnipro node that serves the gauge", value=f"{dN / 1e3:.1f} km"),
          dict(id="support_days", item="days on which that node serves the gauge", value=f"{int((D.nearest_node_id == W.node_id[iN]).sum())} of {len(D)} days"),
          dict(id="peak_lag", item="the reconstruction's maximum before the gauge's by", value=f"{(pd.Timestamp(gmax) - pd.Timestamp(mmax)).days} days"),
          dict(id="rise_reconstruction", item="reconstructed rise to its maximum at the gauge", value=f"{D.recon_rise_m.max():+.2f} m"),
          dict(id="rise_gauge_daily", item="gauge rise to its maximum (daily means)", value=f"{D.gauge_rise_m.max():+.2f} m"),
          dict(id="support_at_gauge", item="water-surface support at the gauge, 26 May - 10 July",
               value=f"{(D.support_primary == D.support_primary.iloc[0]).sum()} of {len(D)} days {D.support_primary.iloc[0]} from the {W.river[iN]} node {W.node_id[iN]} at {dN / 1e3:.1f} km "
                     f"(observed on {int(D.nearest_node_observed.sum())} of those days); nearest Inhulets (same-river) node {d_inh:.1f} km")]
    q6 = Q.loc["2023-06-01":"2023-06-20"] if len(Q) else Q
    S.append(dict(id="upstream_discharge", item="Inhulets discharge at Kryvyi Rih 80568, 1-20 June (yearbook table 1.3)",
                  value=f"{q6.min():.2f}-{q6.max():.2f} m3/s (mean {q6.mean():.2f}); 2023 annual mean {Q.mean():.2f} m3/s" if len(q6) else "n/a"))
    if cell:
        obs_days = D[D.gauge_above_floodplain].date; rec_days = D[D.reconstructed_new_at_gauge].date
        S += [dict(id="terrain_at_gauge", item=f"floodplain terrain around the post (land cells within {FLOODPLAIN_RADIUS_M:.0f} m, rev 6)",
                   value=f"median {cell['terrain_m']:.2f} m, p25 {cell['terrain_p25_m']:.2f} m EVRF2019 ({cell['floodplain_land_cells']} cells; the post's own cell is the channel, WorldCover {cell['channel_cell_worldcover']})"),
              dict(id="days_gauge_above_terrain", item="days with the gauge level above that floodplain (median)", value=f"{len(obs_days)} ({obs_days.min()} .. {obs_days.max()})" if len(obs_days) else "0"),
              dict(id="days_reconstructed_new", item="days with reconstructed new inundation on >= 50 % of that floodplain", value=f"{len(rec_days)} ({rec_days.min()} .. {rec_days.max()})" if len(rec_days) else "0"),
              dict(id="yearbook_high_water", item="high-water period in the yearbook remark (vol. 2, item 114)", value=f"{REMARK_PERIOD[0]} .. {REMARK_PERIOD[1]} (houses and the road bridge 0.75 km upstream flooded)")]
    if "H_reconstructed_gauge_node_sensitivity_m" in D.columns:
        d2 = (D.H_reconstructed_gauge_node_sensitivity_m - D.H_evrf2019_m)
        S.append(dict(id="gauge_node_sensitivity", item="gauge-node sensitivity: reconstruction - gauge, 6-20 June (max |.|; the gauge is an input there)", value=f"{d2[(D.date >= '2023-06-06') & (D.date <= '2023-06-20')].abs().max():.2f} m"))
    S.append(dict(id="caveat_pile5", item="data caveat (yearbook remark)", value="pile No. 5 re-levelled during the hazard (date and size not given): a possible datum step inside the series; post- vs pre-event levels not comparable without it"))
    Sdf = pd.DataFrame(S); Sdf.to_csv(CFG.TABLES / "p95k_inhulets_summary.csv", index=False)
    man = dict(producer="p95k_inhulets_gauge_check.py", independent_of_reconstruction=True, ingestion_job=JOB, yearbook_remark=YEARBOOK_REMARK, remark_reading=REMARK_READING,
               vertical="H_EVRF2019 = zero_BS77 (header of the yearbook sheet) + stage_cm / 100 + delta_EPSG9902 (ua_2019z.asc, bilinear; Paper 1)",
               levels="table 1.2 daily means (day-by-day comparison); the yearbook's highest level of the year for peak, rise and record", highest=hi,
               role="D-INHULETS (maintainer, 2026-09-29): withheld from the primary water surface; independent tributary validation (absolute error, event-relative error, peak timing, recession); the gauge-node run is a separate sensitivity; the support of the valley's new area is classified in p95l (direct / extrapolated / weak, cross-river flag)",
               posts={p: {k: v for k, v in m.items() if k not in ("series", "flags")} for p, m in st.items()}, gauge_xy_epsg32636=[round(x, 1), round(y, 1)],
               gauge_cell={k: v for k, v in cell.items() if k != "new_share"}, engines=list(engines), discharge_80568=dict(parquet=qf, sha256=qsha))
    man["liman"] = liman_check(W, P95, z9902, h9902, None)
    (CFG.TABLES / "p95k_manifest.json").write_text(json.dumps(man, indent=1, default=str))
    # figure
    t = pd.to_datetime(D.date); fig, (ax, bx) = plt.subplots(2, 1, figsize=(9.5, 6.2), sharex=True, height_ratios=(2.2, 1), constrained_layout=True)
    ax.plot(t, D.H_evrf2019_m, "o-", color="#0b0b0b", ms=3.5, lw=1.6, label="gauge Kalynivske 80575 (yearbook daily means, EVRF2019; independent)")
    ax.plot(pd.Timestamp(hi["date"]), hi["H_evrf2019_m"], "*", color="#0b0b0b", ms=10, label=f"highest level of the year {hi['printed']} cm, {hi['date'][8:]}.{hi['date'][5:7]}")
    ax.plot(t, D.H_reconstructed_primary_m, "-", color="#2a78d6", lw=1.6, label=f"reconstructed water surface at the gauge (rev 6; nearest node {dN / 1e3:.0f} km away, {W.river[iN]})")
    if "H_reconstructed_gauge_node_sensitivity_m" in D.columns:
        ax.plot(t, D.H_reconstructed_gauge_node_sensitivity_m, ":", color="#1baf7a", lw=1.4, label="sensitivity: the gauge as an Inhulets node (input)")
    ax.plot(t, D.kherson_gauge_m, "-", color="#52514e", lw=1.0, label="Kherson gauge 80805 (Dnipro)")
    if cell:
        ax.axhline(cell["terrain_m"], color="#eda100", lw=0.9, ls="--", label=f"floodplain around the post (median, {cell['terrain_m']:.2f} m)")
        for dd in D[D.reconstructed_new_at_gauge].date:
            ax.axvspan(pd.Timestamp(dd) - pd.Timedelta(hours=12), pd.Timestamp(dd) + pd.Timedelta(hours=12), color="#2a78d6", alpha=0.07, lw=0)
    ax.axhline(g["zero_bs77_m"] + g["floodplain_exit_cm"] / 100 + g["delta_epsg9902_m"], color="#e34948", lw=0.8, ls=":", label="floodplain exit 490 cm")
    ax.axvline(pd.Timestamp("2023-06-06"), color="#e34948", lw=0.8)
    ax.axvspan(pd.Timestamp(REMARK_PERIOD[0]), pd.Timestamp(REMARK_PERIOD[1]) + pd.Timedelta(days=1), ymin=0.97, ymax=1.0, color="#e34948", alpha=0.5, lw=0,
               label="high water 7-18 June (yearbook remark)")
    ax.set_xlim(pd.Timestamp("2023-05-26"), pd.Timestamp("2023-07-10")); ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.set_ylabel("water level, m EVRF2019", fontsize=8); ax.grid(color="#efece6"); ax.tick_params(labelsize=7); ax.legend(fontsize=6.5, frameon=False, loc="upper right")
    bx.axhline(0, color="#0b0b0b", lw=0.6); bx.axvline(pd.Timestamp("2023-06-06"), color="#e34948", lw=0.8)
    bx.plot(t, D.recon_minus_gauge_m, "-", color="#2a78d6", lw=1.4, label="e_abs = reconstruction - gauge")
    bx.plot(t, D.e_rise_m, "--", color="#e8743b", lw=1.4, label="e_rise = reconstructed rise - gauge rise (free of a constant datum offset)")
    bx.set_ylabel("error at the gauge, m", fontsize=8); bx.grid(color="#efece6"); bx.tick_params(labelsize=7); bx.legend(fontsize=6.5, frameon=False, loc="upper right")
    ax.set_title("Inhulets backwater at Kalynivske (80575) vs the reconstructed water surface (shaded: reconstructed new inundation on >= 50 % of the floodplain around the post)", fontsize=8, loc="left")
    fig.savefig(FIG / "p95k_inhulets_kalynivske.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    pd.set_option("display.width", 250); print(Sdf.to_string(index=False))
    print(D[(D.date >= "2023-06-03") & (D.date <= "2023-06-22")][[c for c in D.columns if c in ("date", "stage_cm", "H_evrf2019_m", "H_reconstructed_primary_m", "H_reconstructed_gauge_node_sensitivity_m",
                                                                         "recon_minus_gauge_m", "gauge_above_floodplain", "reconstructed_new_share_floodplain", "Q_80568_m3s", "stage_80568_cm")]].to_string(index=False))
    print("-> tables/p95k_*, figures/m6_v003A/p95k_inhulets_kalynivske.png")


if __name__ == "__main__":
    main()
