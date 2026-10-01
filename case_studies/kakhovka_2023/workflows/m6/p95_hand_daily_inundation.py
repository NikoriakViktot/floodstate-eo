# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Terrain-connectivity reconstruction of the DAILY inundation (rev 8, 2026-09-30: D-SEED;
# rev 9, 2026-09-30: the baseline holds optical pre-breach water only -- Sentinel-1 darkness of 1/2 June is not reference water).
"""P95 -- daily inundation reconstructed from the observed water surface and the terrain: SWOT KaRIn node WSE (daily, 1-day
orbit) + the Kherson gauge, projected on the seamless terrain-bed elevation model with a connectivity rule, for every day
2023-05-26 .. 2023-07-10 (observation-constrained terrain-connectivity reconstruction).

This is the third pillar next to the U-Net (M6) and the RF surface class (p73): it says what the water surface ALLOWS on
every day, including the 7-8 June maximum that no satellite image saw, and it is independent of the S1/S2 labels.

Terrain layer z_terrain (Paper 2 / p55): FABDEM bare-earth DTM outside the surveyed channel (source codes 3, 4 of
<ZONE>_dem_source_20m.tif), observed / reconstructed bed elevation inside it (codes 1, 2, 5) -- a seamless terrain-bed
elevation model, EVRF2019. FABDEM is already a DTM: the class-median residual against night ICESat-2 ground (p95j; Paper 2 /
p57) that is subtracted from the FABDEM-sourced cells is a RESIDUAL class-dependent terrain-elevation bias, not a canopy
correction; bed cells receive no FABDEM statistics (`--dem-bias none` keeps the raw product as a sensitivity).

Rule (rev 6: evaluated ONCE on the union mosaic of the zones; ownership only for accounting and for the per-zone rasters;
rev 8: the pre-breach water map is composed from the frames where each frame HAS labels -- the 30 m strip east of frame B2
inside ZONE_2 used to overwrite ZONE_4's water with 'no data' and cut the pre-breach river network in two at Kherson):
    H_t(cell)   = median H_t of the K = 5 nearest SWOT nodes within 3 km (+ margin, central 0.0 m); each node time-filled
                  between its own observations (observed / interpolated / held flags kept); the Kherson gauge is one more
                  node; cells > 15 km from a node and west of the gauge: min(that, gauge_t). Coarse 100 m lattice anchored
                  in map coordinates (so zonal and mosaic evaluations coincide), replicated to 20 m.
    C_t         = z_terrain < H_t  AND  dist to pre-breach water <= 10 km  AND  downstream of the dam (x < dam - 1 km)
    P_t         = connected_ceiling (PRIMARY): C_t 8-connected to the pre-breach RIVER NETWORK -- the largest connected
                  component of the pre-breach optical water map (p60 pre_water_frac >= 20 %): the Dnipro from the dam to the
                  liman with its delta, the Inhulets and the Kokan' -- the published flood-fill logic (terrain below the
                  surface AND connected to the flood source). Seeding from EVERY pre-breach water cell (ponds, canals) is the
                  superseded rev-7 semantics (`--seed-network all_prewater`, kept as a provenance variant): a few pond cells
                  let ~40 km2 of terrace cropland 'flood' under a level extrapolated 14 km from the Kokan' (D-SEED, maintainer
                  2026-09-30; audit p95o);
                  hand_and_ceiling (p42 rule, additionally HAND < H_t - 1 m; lower bound where the delta drainage is unmapped)
                  and ceiling_only (no connectivity; upper bound) are sensitivities.  depth_t = H_t - z_terrain.
    N_t         = P_t AND NOT B,  B = optically observed pre-breach water (p60 pre_water_frac >= 20 %: Sentinel-2 water frequency
                  before the breach) OR P on ANY pre-breach day 05-26..06-05 under the same rule (normal regime; N = 0 before the
                  breach by construction). rev 9 (maintainer, 2026-09-30): Sentinel-1 darkness on 06-01/02 is NOT part of B -- over
                  dry sand and smooth fields it is not water (403 km2 of the domain, mostly dry cropland / grass in later EO; p95x
                  check); it stays only as the mask of the S1 'new water' in the validations (the sensor was already dark there).
                  The model-only part of B ("normally wet": low reed beds below the normal surface that no optical/SAR mask
                  lists as water) is its own validation category -- S1 dark-water onset there is a DEPTH signal.
Sensitivities: --connectivity 4, --seed-network all_prewater (superseded rev-7 seeding), --memory (D-MEMORY: a cell
inundated on day t-1 stays inundated on day t while it is still below the surface -- retained water, a storage hypothesis
without infiltration / drainage, sensitivity only), --max-gap-days N (node unavailable beyond N days from an observation),
--wse-river-aware (median over nodes of the nearest node's river only), --closure p59_reservoir --margin 0.5 (superseded
chain), --dem-bias none. The uncertainty of every area and volume is p95e (coherent Monte-Carlo worlds).
Vertical frame: EVERY height is EVRF2019 (terrain raster tag; SWOT wse + geoid_hght - zeta_EGG2015 + c_Kherson, Paper 1;
gauge H_gauge_evrf; ICESat-2 via the p57 chain) -- asserted, recorded in the manifest, never assumed.
Limits (state them with every number): a planar water surface per node neighbourhood, no momentum, no timing of filling /
draining (ponds drain slower than the channel: the recession may be underestimated), terrain under reeds / forest, SWOT
nodes on the channel only, no scene at the maximum, the Inhulets valley gets the Dnipro level at its mouth (backwater).

Outputs: $BULK_ROOT/floodplain_dyn/<ZONE>_<rule>[_variant]/{duration_days.tif, first_day.tif, last_day.tif, max_depth_m.tif,
         depth_2023-06-08_m.tif, wse_support_kind.tif, daily_new.npz (bit-packed: one key per date + baseline + normally_wet)}
         <case_study>/tables/p95_{daily_area,daily_area_pooled,validation_s1,validation_s1_pooled,validation_m6,wse_support_nodes,
         wse_support_cells,source_share,seam_check}<sfx>.csv, p95_manifest<sfx>.json, p95_wse_{nodes,nodes_observed,profile_display}*.csv
         <case_study>/figures/m6_v003A/hand_dyn_{curve,maps_<ZONE>,wse_profile}.png
"""
from __future__ import annotations
import importlib.util, json, re, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio import features
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling, transform as tf_transform
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.patches import Patch
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.terrain.connectivity import connected_to_seed, largest_component
from floodstate_eo.terrain.mosaic import UnionGrid
from floodstate_eo.terrain.vertical import assert_same_vertical_frame
_pf = importlib.util.spec_from_file_location("paper1_frame", Path(__file__).with_name("paper1_frame.py")); PF = importlib.util.module_from_spec(_pf); _pf.loader.exec_module(PF)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = ROOT / "figures" / "m6_v003A"
DYN = CFG.BULK_ROOT / "floodplain_dyn"
ZONES = {"ZONE_4_DAM_TO_KHERSON_FLOODWAY": dict(frame="B1", cache="ZONE_4_FLOODWAY_june2023_s32"),
         "ZONE_2_KHERSON_DELTA": dict(frame="B2", cache="ZONE_2_KHERSON_DELTA_flood_june2023")}
OWNER_ORDER = ["ZONE_4_DAM_TO_KHERSON_FLOODWAY", "ZONE_2_KHERSON_DELTA"]     # pasted in this order: ZONE_2 owns the overlap
ZONE2_BBOX = (437980.0, 5134980.0, 475720.0, 5211580.0)      # ZONE_2 owns the overlap (same rule as m6_split_v1: B2 owns)
DAM_LONLAT = (33.3667, 46.7783); KHERSON_LONLAT = (32.612026, 46.623750)
SWOT_MARGIN_M, RIVER_LEVEL_M, SWOT_MAX_DIST_M, DIST_MAX_M, DAM_BUFFER_M = 0.0, 1.0, 15000.0, 10000.0, 1000.0
BASE_MARGIN_M = 0.0                    # the pre-breach baseline uses the central (zero) margin; --margin varies event days only
RULES = ("connected_ceiling", "hand_and_ceiling", "ceiling_only")
PRIMARY_RULE = "connected_ceiling"
# Vertical closure (rev 3, 2026-09-25, after Paper 1 of the series): SWOT heights are EGG2015-referenced heights,
# H_S = wse + geoid_hght - zeta_EGG2015 (SWOT's crust is already mean-tide, no permanent-tide term), shifted by the LOCAL
# empirical closure residual c = gauge - satellite. Paper 1 measured c ~ 0 at Kherson (+0.9 cm RiverSP pre-breach, -2.6 cm PIXC,
# +1.9 cm through the breach fortnight, NMAD 4-5 cm), whereas p59 had applied the mean reservoir closure (-0.173 m) plus a
# free2mean term (-0.036 m) to the downstream reach, i.e. -0.209 m too low, hidden by the old +0.5 m margin.
C_KHERSON_M, C_KHERSON_NMAD_M = 0.0, 0.05
VERTICAL_DATUM = "EVRF2019"
VERTICAL_CHAINS = {"terrain": "p55 seamless terrain-bed model, raster tag vertical_datum (FABDEM -> EVRF2019 by p56; bed by p53/hist20)",
                   "swot": "H = wse + geoid_hght - zeta_EGG2015 + c_Kherson (Paper 1; EGG2015-referenced heights re-anchored at Kherson)",
                   "gauge": "river yearbook BS-77 -> EVRF2019 (EPSG:9902 at the post), column H_gauge_evrf",
                   "icesat2": "ATL08 h_te + free2mean - zeta_EGG2015 + c (Paper 2 / p57 chain)"}
# Terrain residual model (rev 6): FABDEM-DTM residual statistics against night ICESat-2 ground by WorldCover class
# (b_c = median, sigma_c = NMAD; p95j per zone, pooled fallback; p57 'A FABDEM' rows as the last resort). Applied ONLY where the
# seamless product is FABDEM-sourced (source codes 3 = FABDEM->EVRF2019, 4 = FABDEM tapered at a bathymetric edge); bed
# cells (1 = zone bed DEM p53, 2 = reservoir bed hist20, 5 = former-pool gap fill) get neither bias nor sigma (limitation).
TERRAIN_BIAS = "class"                 # or "none" (sensitivity, suffix _dem_uncorrected)
TERRAIN_TABLE = "fabdem_zone"          # rev 6; "legacy_c_seamless" = the rev-5 table (C seamless rows of ZONE_2 on EVERY cell) -- reproduction gate only
TERRAIN_CLASS = {10: "trees", 30: "grass", 40: "cropland", 50: "built", 60: "bare", 90: "wetland"}
DEM_CLASS = TERRAIN_CLASS              # name kept for p95c/p95g
FABDEM_SOURCES, BED_SOURCES = (3, 4), (1, 2, 5)
SOURCE_NAMES = {0: "nodata", 1: "zone_bed_p53", 2: "reservoir_bed_hist20", 3: "FABDEM", 4: "FABDEM_tapered_edge", 5: "gap_fill"}
N_MIN_CLASS = 500                      # own-zone class row accepted when N >= this; else the pooled row, flagged transferred
CLOSURES = {"kherson_paper1": "H = wse + geoid_hght - zeta_EGG2015 + c_Kherson (c = 0.00 m, NMAD 0.05 m; Paper 1 Table 5 / Sec. 5.12)",
            "p59_reservoir": "H_evrf of p59: wse + geoid_hght + free2mean(lat) - zeta + mean reservoir c (-0.173 m) -- SUPERSEDED, sensitivity only"}
BASELINE_DATE = "2023-06-05"
DATES = pd.date_range("2023-05-26", "2023-07-10", freq="D")
S1_DATES = ["2023-06-01", "2023-06-02", "2023-06-06", "2023-06-09", "2023-06-13", "2023-06-14", "2023-06-18",
            "2023-06-21", "2023-06-25", "2023-06-26", "2023-06-30"]
CELL_M, CELL_KM2 = 20.0, 0.0004
C_HAND, C_S1, C_GAUGE = "#2a78d6", "#eb6834", "#52514e"
SUPPORT_KIND = {0: "nodes_within_3km", 1: "nearest_node_fallback", 3: "no_water_surface"}


def load_p92():
    s = importlib.util.spec_from_file_location("p92", HERE / "p92_flood_area_dam_to_liman.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def zone_id(zone: str) -> int:
    return int(re.search(r"ZONE_(\d)", zone).group(1))


# ---- terrain residual model ------------------------------------------------------------------------------------------------
def terrain_residual_table(zone: str | None = None):
    """FABDEM-DTM residual statistics by WorldCover class for `zone`: b_c = median, sigma_c = NMAD of z_FABDEM - z_ICESat2,ground
    (night ATL08, p57 QC). Own-zone rows of p95j when N >= N_MIN_CLASS, else the pooled row (both zones) flagged transferred;
    without a p95j table the p57 'A FABDEM, WorldCover <class>' rows (pooled over the frames of Paper 2). The 'other' entry
    (pooled, all classes) serves FABDEM cells whose WorldCover code has no row. Returns (table, source path)."""
    p = CFG.TABLES / "p95j_terrain_residual_stats.csv"; out = {}
    if p.exists():
        S = pd.read_csv(p)
        def take(r, transferred):
            r = r.iloc[0]
            return dict(bias=float(r["median"]), sigma=float(r["NMAD"]), rmse=float(r["RMSE"]), n=int(r["N"]), cls=str(r["wc_class"]), transferred=bool(transferred), zone_used=str(r["zone"]))
        for code, nm in TERRAIN_CLASS.items():
            r = S[(S.zone == zone) & (S.wc_class == nm)] if zone else S.iloc[0:0]
            if len(r) and int(r.iloc[0]["N"]) >= N_MIN_CLASS:
                out[code] = take(r, False)
            else:
                rp = S[(S.zone == "POOLED") & (S.wc_class == nm)]
                if len(rp):
                    out[code] = take(rp, True)
        ra = S[(S.zone == "POOLED") & (S.wc_class == "all")]
        out["other"] = take(ra, True) if len(ra) else dict(bias=0.0, sigma=float(S.NMAD.median()), rmse=np.nan, n=0, cls="all", transferred=True, zone_used="POOLED")
        return out, str(p)
    src = CFG.TABLES / "p57_dem_accuracy_night.csv"
    if not src.exists():
        src = Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p57_dem_accuracy_night.csv"
    Tb = pd.read_csv(src)
    for code, nm in TERRAIN_CLASS.items():
        r = Tb[Tb.set.str.strip('"') == f"A FABDEM, WorldCover {nm}"]
        if len(r):
            out[code] = dict(bias=float(r.iloc[0]["median"]), sigma=float(r.iloc[0]["NMAD"]), rmse=float(r.iloc[0]["RMSE"]), n=int(r.iloc[0]["N"]), cls=nm, transferred=True, zone_used="p57 A FABDEM (frames pooled)")
    a = Tb[Tb.set.str.startswith("A FABDEM->EVRF2019")].iloc[0]
    out["other"] = dict(bias=float(a["median"]), sigma=float(a["NMAD"]), rmse=float(a["RMSE"]), n=int(a["N"]), cls="all", transferred=True, zone_used="p57 A FABDEM (frames pooled)")
    return out, str(src)


def legacy_c_seamless_table():
    """The rev-5 table, reproduced exactly for the reproduction gate: 'C seamless, ZONE_2' class rows (ZONE_4 where ZONE_2 has
    none) and the ZONE_2 'all' row as default, applied to EVERY cell (bed included). Superseded: not a FABDEM-only model."""
    src = CFG.TABLES / "p57_dem_accuracy_night.csv"
    if not src.exists():
        src = Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p57_dem_accuracy_night.csv"
    Tb = pd.read_csv(src); out = {}
    for code, nm in TERRAIN_CLASS.items():
        r = Tb[Tb.set.str.contains("C seamless, ZONE_2_KHERSON_DELTA, WorldCover " + nm)]
        if len(r) == 0:
            r = Tb[Tb.set.str.contains("C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover " + nm)]
        if len(r):
            out[code] = dict(bias=float(r.iloc[0]["median"]), sigma=float(r.iloc[0]["NMAD"]), rmse=float(r.iloc[0]["RMSE"]), n=int(r.iloc[0]["N"]), cls=nm, transferred=True, zone_used="legacy C seamless")
    a = Tb[Tb.set.str.startswith("C seamless, ZONE_2_KHERSON_DELTA")].iloc[0]
    out["other"] = dict(bias=float(a["median"]), sigma=float(a["NMAD"]), rmse=float(a["RMSE"]), n=int(a["N"]), cls="all", transferred=True, zone_used="legacy C seamless")
    return out, str(src)


def dem_error_table(zone: str | None = None):
    """Compatibility name (p95c / p95g): the terrain residual table of `zone` (rev 6: FABDEM-only, per zone)."""
    return terrain_residual_table(zone)


def worldcover_on(zone, G):
    with rasterio.open(CFG.BULK_ROOT / "worldcover_frames" / zone / "wc_2021_20m.tif") as s:
        wc = np.zeros((G["ny"], G["nx"]), "u1")
        reproject(s.read(1), wc, src_transform=s.transform, src_crs=s.crs, dst_transform=G["transform"], dst_crs=G["crs"], resampling=Resampling.nearest)
    return wc


def terrain_bias_fields(zone, G, is_fabdem, wc=None):
    """(bias, sigma, rows used) per cell: the class residual statistics on FABDEM-sourced cells, ZERO elsewhere (bed)."""
    wc = worldcover_on(zone, G) if wc is None else wc
    if TERRAIN_TABLE == "legacy_c_seamless":                                 # rev 5 exactly: every cell, bed included
        E, src = legacy_c_seamless_table()
        bias = np.full((G["ny"], G["nx"]), E["other"]["bias"], "f4"); sig = np.full((G["ny"], G["nx"]), E["other"]["sigma"], "f4")
        for code, v in E.items():
            if code != "other":
                bias[wc == code] = v["bias"]; sig[wc == code] = v["sigma"]
        return bias, sig, dict(rows=E, source=src)
    E, src = terrain_residual_table(zone)
    bias = np.zeros((G["ny"], G["nx"]), "f4"); sig = np.zeros((G["ny"], G["nx"]), "f4")
    bias[is_fabdem] = E["other"]["bias"]; sig[is_fabdem] = E["other"]["sigma"]
    for code, v in E.items():
        if code != "other":
            m = is_fabdem & (wc == code); bias[m] = v["bias"]; sig[m] = v["sigma"]
    assert not bias[~is_fabdem].any() and not sig[~is_fabdem].any(), "FABDEM residual statistics leaked onto bed cells"
    return bias, sig, dict(rows=E, source=src)


def dem_bias_fields(zone, G):
    """Compatibility name (p95g): (bias, sigma) on the zone grid, FABDEM cells only."""
    with rasterio.open(CFG.BULK_ROOT / "dem_seamless" / f"{zone}_dem_source_20m.tif") as s:
        src = s.read(1).astype("u1")
    b, sg, _ = terrain_bias_fields(zone, G, np.isin(src, FABDEM_SOURCES))
    return b, sg


# ---- water surface --------------------------------------------------------------------------------------------------------
def load_gauge():
    """Kherson daily stage, EVRF2019 (river yearbook), from the repository copy; the sibling repo only as a fallback."""
    p = CFG.TABLES / "p59_swot_vs_kherson.csv"
    if not p.exists():
        p = Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p59_swot_vs_kherson.csv"
    kh = pd.read_csv(p, parse_dates=["date"])
    assert "H_gauge_evrf" in kh.columns, "gauge table without an EVRF2019 column"
    return kh.set_index("date").H_gauge_evrf.dropna(), str(p)


def node_heights(nodes: pd.DataFrame, closure="kherson_paper1") -> pd.Series:
    if closure == "kherson_paper1":
        return nodes.wse + nodes.geoid_hght - nodes.zeta + C_KHERSON_M
    return nodes.H_evrf


def inhulets_gauge_node():
    """The Inhulets gauge Kalynivske (80575) as an extra water-surface node (sensitivity only): its daily EVRF2019 level from
    p95k (yearbook 2023 daily means, zero -1.34 m BS from the sheet header, EPSG:9902 step) at the gauge coordinates. An input here, so no longer an
    independent check of the surface -- the independent check of this variant is the S1 agreement in the Inhulets valley."""
    k = pd.read_csv(CFG.TABLES / "p95k_inhulets_kalynivske.csv", parse_dates=["date"]).set_index("date")
    x, y = tf_transform("EPSG:4326", CFG.CRS_METRIC, [float(k.lon.iloc[0])], [float(k.lat.iloc[0])])
    return [dict(node_id="GAUGE_80575", x=x[0], y=y[0], river="Inhulets", reach="GAUGE_80575", series=k.H_evrf2019_m)]


def load_engine(closure="kherson_paper1", max_gap_days=None, river_aware=False, anchor="map", extra_nodes=None, fallback_max_m=None):
    """(WSE engine, dam x, dam y, nodes) exactly as main() builds them -- used by p95c/p95d/p95e/p95g."""
    nodes = pd.read_csv(CFG.TABLES / "p59_swot_flood_nodes.csv", parse_dates=["date"])
    nodes["H"] = node_heights(nodes, closure)
    gauge, _ = load_gauge()
    kx, ky = tf_transform("EPSG:4326", CFG.CRS_METRIC, [KHERSON_LONLAT[0]], [KHERSON_LONLAT[1]])
    dx, dy = tf_transform("EPSG:4326", CFG.CRS_METRIC, [DAM_LONLAT[0]], [DAM_LONLAT[1]])
    assert_same_vertical_frame({"SWOT nodes (chain)": VERTICAL_DATUM, "Kherson gauge (H_gauge_evrf)": VERTICAL_DATUM})
    return WSE(nodes, gauge, kx[0], ky[0], max_gap_days=max_gap_days, river_aware=river_aware, anchor=anchor, extra_nodes=extra_nodes,
               fallback_max_m=fallback_max_m), dx[0], dy[0], nodes


def row_nanmedian(v: np.ndarray) -> np.ndarray:
    """Median over the finite values of each row (NaN where a row has none) -- bit-identical to np.nanmedian(v, axis=1) for float
    input, without its per-row all-NaN warnings (22 million warning calls per Monte-Carlo world made it the bottleneck)."""
    s = np.where(np.isnan(v), np.inf, v); s.sort(axis=1)
    n = np.isfinite(s).sum(axis=1); r = np.arange(len(s)); k = s.shape[1] - 1
    lo, hi = np.clip((n - 1) // 2, 0, k), np.clip(n // 2, 0, k)
    m = (s[r, lo] + s[r, hi]) * np.asarray(0.5, s.dtype)
    m[n == 0] = np.nan
    return m


class WSE:
    """Water surface per day, NODE-BASED (rev 4), coherent-error contract (rev 6). No along-channel chainage: every cell takes
    the median height of its K nearest SWOT nodes within RMAX_M on the day; each node is time-filled between its own
    observations (kind 0 observed / 1 interpolated / 2 held at an end / 3 unavailable beyond --max-gap-days); the Kherson gauge
    is one more node. Cells whose nearest node is farther than FAR_M and that lie west of the gauge are capped at the gauge
    level. Evaluated on a COARSE lattice (COARSE_M) anchored in MAP coordinates and replicated to the target grid, so a zone
    and the mosaic see the same surface. Every stochastic term enters through `Hmat` (a perturbed copy of `H`): `field`
    adds nothing but the deterministic margin (review F03)."""
    K, RMAX_M, FAR_M, COARSE_M, MIN_OBS, KCHAIN = 5, 3000.0, 15000.0, 100.0, 3, 25
    COARSE = 5     # COARSE_M / CELL_M, kept for callers of the old attribute

    def __init__(self, nodes: pd.DataFrame, gauge: pd.Series, kx: float, ky: float, max_gap_days=None, river_aware=False, anchor="map", extra_nodes=None,
                 fallback_max_m=None):
        if anchor not in ("map", "grid_legacy"):
            raise ValueError("anchor must be 'map' or 'grid_legacy'")
        self.anchor = anchor; self.fallback_max_m = fallback_max_m
        daily = nodes.groupby(["node_id", nodes.date.dt.normalize()]).H.median().unstack().reindex(columns=DATES)
        daily = daily[daily.notna().sum(axis=1) >= self.MIN_OBS]
        pos = nodes.groupby("node_id").agg(x=("x", "median"), y=("y", "median"), reach_id=("reach_id", "first"),
                                           river_name=("river_name", "first")).loc[daily.index]
        g = gauge.reindex(DATES)
        ex = extra_nodes or []                                               # extra gauge nodes (sensitivity), placed before the Kherson gauge row
        es = [e["series"].reindex(DATES) for e in ex]
        self.node_id = list(daily.index) + [e["node_id"] for e in ex] + ["GAUGE_80805"]
        self.reach = list(pos.reach_id) + [e["reach"] for e in ex] + ["GAUGE"]; self.river = list(pos.river_name) + [e["river"] for e in ex] + ["gauge"]
        self.xy = np.vstack([pos[["x", "y"]].values] + [[[e["x"], e["y"]]] for e in ex] + [[[kx, ky]]]).astype("f8")
        self.obs = np.vstack([daily.notna().values] + [s.notna().values[None] for s in es] + [g.notna().values[None]])
        H = np.vstack([daily.interpolate(axis=1, limit_direction="both").values] + [s.interpolate(limit_direction="both").values[None] for s in es]
                      + [g.interpolate(limit_direction="both").values[None]]).astype("f4")
        self.n_extra = len(ex)
        # support flags per node-day: 0 observed, 1 interpolated between observations, 2 held beyond the first/last one
        self.kind = np.full(self.obs.shape, 1, "u1"); self.gap = np.zeros(self.obs.shape, "i2")
        days = np.arange(self.obs.shape[1])
        for i in range(self.obs.shape[0]):
            o = days[self.obs[i]]
            if len(o) == 0:
                self.kind[i] = 3; self.gap[i] = 999; continue
            self.gap[i] = np.abs(days[:, None] - o[None, :]).min(1)
            self.kind[i, self.obs[i]] = 0; self.kind[i, (days < o.min()) | (days > o.max())] = 2
        self.max_gap_days = max_gap_days
        if max_gap_days is not None:
            drop = (self.gap > max_gap_days); drop[-1 - self.n_extra:] = False    # gauges are never dropped
            H[drop] = np.nan; self.kind[drop] = 3
        self.H = H
        self.dates = list(DATES); self.tree = cKDTree(self.xy); self.kx = kx
        self.river_aware = bool(river_aware)
        main = {"no_data", "gauge", "Dnipro", "Dnieper"}
        self.river_code = np.array([0 if (r in main or str(r).lower().startswith("dn")) else hash(str(r)) % 10007 + 1 for r in self.river])

    def support_table(self) -> pd.DataFrame:
        """Per day: number of SWOT nodes observed / interpolated / held / unavailable (the gauge row excluded)."""
        rows = []
        for j, d in enumerate(self.dates):
            k = self.kind[:-1, j]
            rows.append(dict(date=str(d.date()), n_nodes=int(len(k)), n_observed=int((k == 0).sum()), n_interpolated=int((k == 1).sum()),
                             n_held=int((k == 2).sum()), n_unavailable=int((k == 3).sum()), gauge_observed=bool(self.obs[-1, j]),
                             median_gap_days_interpolated=float(np.median(self.gap[:-1, j][k == 1])) if (k == 1).any() else np.nan))
        return pd.DataFrame(rows)

    def prepare(self, L):
        """Neighbour structure for a grid (a layer dict with 'G', or a G dict): coarse cells anchored at multiples of COARSE_M."""
        G = L["G"] if "G" in L else L; c = self.COARSE_M
        xs = G["transform"].c + CELL_M * (np.arange(G["nx"]) + 0.5); ys = G["transform"].f - CELL_M * (np.arange(G["ny"]) + 0.5)
        if self.anchor == "grid_legacy":                                     # rev 5: every COARSE-th cell centre of THIS grid, replicated
            k = self.COARSE; xc, yc = xs[::k], ys[::k]
            ri, ci = np.arange(G["ny"]) // k, np.arange(G["nx"]) // k; uy, ux = yc, xc
            YY, XX = np.meshgrid(yc, xc, indexing="ij")
        else:                                                                 # rev 6: coarse cells anchored at multiples of COARSE_M
            cx, cy = np.floor(xs / c).astype("i8"), np.floor(ys / c).astype("i8")
            ux, uy = np.unique(cx), np.unique(cy)[::-1]                      # columns west->east, rows north->south
            ci = np.searchsorted(ux, cx); ri = len(uy) - 1 - np.searchsorted(uy[::-1], cy)
            YY, XX = np.meshgrid((uy + 0.5) * c, (ux + 0.5) * c, indexing="ij")
        pts = np.c_[XX.ravel(), YY.ravel()]
        d, idx = self.tree.query(pts, k=self.K, distance_upper_bound=self.RMAX_M)
        valid = np.isfinite(d); idx = np.where(valid, idx, 0).astype("i4")
        d1, i1 = self.tree.query(pts, k=1)
        _, chain = self.tree.query(pts, k=min(self.KCHAIN, len(self.node_id)))   # nearest AVAILABLE node when the K within RMAX have no height
        chain = chain.reshape(len(pts), -1).astype("i4")
        if self.river_aware:
            valid &= self.river_code[idx] == self.river_code[i1][:, None]
        far = (d1 > self.FAR_M) & (pts[:, 0] < self.kx)
        return dict(idx=idx, valid=valid, i1=i1, d1=d1, chain=chain, far=far, shape_c=(len(uy), len(ux)), ri=ri, ci=ci,
                    shape=(G["ny"], G["nx"]), far_frac=float(far.mean()), within_frac=float(valid.any(1).mean()))

    def _coarse(self, Z, day, margin, Hmat, want_kind):
        Hm = self.H if Hmat is None else Hmat; j = self.dates.index(pd.Timestamp(day))
        col = Hm[:, j]; hv = np.where(Z["valid"], col[Z["idx"]], np.nan)
        h = row_nanmedian(hv)
        kind = np.where(np.isfinite(h), 0, 1).astype("u1")
        need = ~np.isfinite(h)
        if need.any():                                                       # no node within RMAX (or none available): nearest available node
            cv = col[Z["chain"][need]]; ok = np.isfinite(cv); first = ok.argmax(1)
            fb = np.where(ok.any(1), cv[np.arange(len(cv)), first], np.nan); h[need] = fb
            kind[need] = np.where(np.isfinite(fb), 1, 3)
        if self.fallback_max_m is not None:                                 # sensitivity: no surface from a node farther than this (gauge-capped cells keep the gauge)
            h = np.where((Z["d1"] > self.fallback_max_m) & ~Z["far"], np.nan, h)
            kind = np.where(np.isfinite(h) | Z["far"], kind, 3).astype("u1")
        gj = col[-1]
        if np.isfinite(gj):
            h = np.where(Z["far"], np.where(np.isfinite(h), np.minimum(h, gj), gj), h)
        h = (h + margin).astype("f4").reshape(Z["shape_c"])
        return (h, kind.reshape(Z["shape_c"])) if want_kind else h

    def field(self, Z, day, margin=0.0, Hmat=None):
        """Water surface on the target grid for `day` (m, EVRF2019). Stochastic terms come in through `Hmat` only."""
        h = self._coarse(Z, day, margin, Hmat, False)
        return h[np.ix_(Z["ri"], Z["ci"])]

    def support_kind(self, Z, day, Hmat=None):
        """Per target cell: 0 = median of nodes within RMAX, 1 = nearest available node (fallback), 3 = no water surface."""
        _, k = self._coarse(Z, day, 0.0, Hmat, True)
        return k[np.ix_(Z["ri"], Z["ci"])]

    def profile_display(self, dx, dy):
        """Display-only profile: date x 1-km straight-line distance from the dam, OBSERVED main-stem nodes (no Inhulets,
        no Kokan', no gauge), medians; NaN where unobserved. For the H(s,t) figure and T17, never for the reconstruction."""
        main = np.array([r not in ("Inhulets", "Kokan'", "gauge") for r in self.river])
        dd = np.hypot(self.xy[:, 0] - dx, self.xy[:, 1] - dy) / 1e3
        rows = {}
        for j, d in enumerate(self.dates):
            ok = main & self.obs[:, j]; b = np.floor(dd[ok]).astype(int)
            rows[d] = pd.Series(self.H[ok, j]).groupby(b).median()
        T = pd.DataFrame(rows).T.sort_index(axis=1); T.index.name = "date"
        return T


# ---- layers ---------------------------------------------------------------------------------------------------------------
def zone_layers(zone, P, with_s1=True):
    """All per-zone 20 m layers. `dem` = the seamless terrain-bed model minus the class residual bias on FABDEM cells (rev 6)."""
    Z = ZONES[zone]; T = CFG.BULK_ROOT / "terrain" / zone
    with rasterio.open(CFG.BULK_ROOT / "dem_seamless" / f"{zone}_dem_evrf2019_20m.tif") as s:
        dem = s.read(1).astype("f4"); dem[dem == s.nodata] = np.nan; G = dict(transform=s.transform, crs=s.crs, ny=s.height, nx=s.width)
        tag = s.tags().get("vertical_datum")
    with rasterio.open(CFG.BULK_ROOT / "dem_seamless" / f"{zone}_dem_source_20m.tif") as s:
        src = s.read(1).astype("u1")
    frame = assert_same_vertical_frame({"terrain raster tag": tag, "SWOT nodes (chain)": VERTICAL_DATUM, "Kherson gauge (H_gauge_evrf)": VERTICAL_DATUM})
    dem = PF.fabdem_to_paper1(dem, src)                                    # Paper 1 v6 frame (2026-09-30): FABDEM cells +0.038 m, bed unchanged
    is_fabdem = np.isin(src, FABDEM_SOURCES)
    def onto(path, nodata_to_nan=True, resampling=Resampling.nearest, dtype="f4"):
        with rasterio.open(path) as s:
            a = s.read(1).astype("f4"); nd = s.nodata
            if nodata_to_nan and nd is not None:
                a[a == nd] = np.nan
            d = np.full((G["ny"], G["nx"]), np.nan, "f4")
            reproject(a, d, src_transform=s.transform, src_crs=s.crs, dst_transform=G["transform"], dst_crs=G["crs"],
                      resampling=resampling, src_nodata=np.nan, dst_nodata=np.nan)
        return d
    wc = worldcover_on(zone, G)
    bias, sig, used = terrain_bias_fields(zone, G, is_fabdem, wc)
    dem_raw = dem
    if TERRAIN_BIAS == "class":
        dem = (dem - bias).astype("f4")                                     # rev 5/6: residual class bias removed on FABDEM cells only
    hand = onto(CFG.BULK_ROOT / "floodplain" / zone / f"{zone}_hand_m.tif")
    dist = onto(T / "dist_ref_water_m.tif")
    with rasterio.open(P.OUT / Z["frame"] / "labels.tif") as s:
        d_ = list(s.descriptions); wf = s.read(d_.index("pre_water_frac") + 1).astype("f4"); tr10 = s.transform; lb = s.bounds
        pre10 = (wf >= 20).astype("f4")
    pre = np.zeros((G["ny"], G["nx"]), "f4")
    reproject(pre10, pre, src_transform=tr10, src_crs=G["crs"], dst_transform=G["transform"], dst_crs=G["crs"], resampling=Resampling.nearest)
    xs_ = G["transform"].c + CELL_M * (np.arange(G["nx"]) + 0.5); ys_ = G["transform"].f - CELL_M * (np.arange(G["ny"]) + 0.5)
    lab_cover = ((xs_ >= lb.left) & (xs_ < lb.right))[None, :] & ((ys_ > lb.bottom) & (ys_ <= lb.top))[:, None]   # rev 8: where this frame HAS labels
    W, V = {}, {}
    z = np.load(CFG.S1_CACHE / Z["cache"] / "per_scene_water.npz", allow_pickle=True); shp = tuple(int(v) for v in z["shape"])
    trc = from_origin(float(z["x0"]), float(z["y1"]), float(z["cell"]), float(z["cell"]))
    un = lambda k: np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
    for k in sorted(z.files):
        if not k.startswith("2023"):
            continue
        d = k[:10]
        if not with_s1 and d not in ("2023-06-01", "2023-06-02"):
            continue
        w, v = un(k), un("valid_" + k)
        for D, a in ((W, w & v), (V, v)):
            m = np.zeros((G["ny"], G["nx"]), "u1")
            reproject(a.astype("u1"), m, src_transform=trc, src_crs=G["crs"], dst_transform=G["transform"], dst_crs=G["crs"], resampling=Resampling.nearest)
            D[d] = D.get(d, np.zeros((G["ny"], G["nx"]), bool)) | m.astype(bool)
    pre_s1 = W["2023-06-01"] | W["2023-06-02"]
    if not with_s1:
        W, V = {}, {}
    xs = G["transform"].c + CELL_M * (np.arange(G["nx"]) + 0.5); ys = G["transform"].f - CELL_M * (np.arange(G["ny"]) + 0.5)
    own = np.ones((G["ny"], G["nx"]), bool)
    if zone != "ZONE_2_KHERSON_DELTA":
        x0, y0, x1, y1 = ZONE2_BBOX
        own &= ~(((xs >= x0) & (xs < x1))[None, :] & ((ys >= y0) & (ys < y1))[:, None])
    cut = np.zeros((G["ny"], G["nx"]), bool)
    for x0, y0, x1, y1 in P.CUT_RECTS.values():
        cut |= ((xs >= x0) & (xs < x1))[None, :] & ((ys >= y0) & (ys < y1))[:, None]
    inh = ((xs >= P.CUT_RECTS["inhulets_valley"][0]) & (xs < P.CUT_RECTS["inhulets_valley"][2]))[None, :] & \
          ((ys >= P.CUT_RECTS["inhulets_valley"][1]) & (ys < P.CUT_RECTS["inhulets_valley"][3]))[:, None]
    fp = None
    gj = Path(CFG._SWOT_DNIPRO_SIBLING) / "data/processed/domains/below_dam_floodplain_utm.geojson"
    if gj.exists():
        g = json.loads(gj.read_text())
        fp = features.rasterize([(ft["geometry"], 1) for ft in g["features"]], out_shape=(G["ny"], G["nx"]),
                                transform=G["transform"], fill=0, dtype="uint8").astype(bool)
    return dict(G=G, dem=dem, dem_raw=dem_raw, src=src, is_fabdem=is_fabdem, bias=bias, sig=sig, wc=wc, residual_rows=used, hand=hand, dist=dist,
                pre=pre > 0, s1_pre_dark=pre_s1, seed=pre > 0, lab_cover=lab_cover, W=W, V=V, xs=xs, ys=ys, own=own, cut=cut, inh=inh, fp=fp, frame=Z["frame"], vertical_frame=frame)


def mosaic_layers(P, with_s1=True, zones=None):
    """The union mosaic of the zones (rev 6): one terrain graph, one water surface, ownership only for accounting.
    Layers of the owner (ZONE_2 in the overlap) win where zones overlap."""
    names = [z for z in OWNER_ORDER if (zones is None or z in zones)]
    Ls = {z: zone_layers(z, P, with_s1) for z in names}
    grid = UnionGrid.from_members({z: (L["G"]["transform"], (L["G"]["ny"], L["G"]["nx"])) for z, L in Ls.items()})
    comp = lambda key, fill, dtype=None: grid.compose({z: L[key] for z, L in Ls.items()}, fill, order=names, dtype=dtype)

    def comp_labelled(key):
        # rev 8: a frame-derived water mask is pasted only where its frame has labels; the owner's 'no data' never
        # overwrites the other zone's water (the 30 m strip east of B2 inside ZONE_2 cut the river network at Kherson)
        out = np.zeros(grid.shape, bool)
        for z in names:
            rs, cs = grid.window(z); m = Ls[z]["lab_cover"]; out[rs, cs][m] = Ls[z][key][m]
        return out
    own_id = grid.compose({z: np.where(L["own"], zone_id(z), 0).astype("u1") for z, L in Ls.items()}, 0, order=names, dtype="u1")
    M = dict(grid=grid, G=dict(transform=grid.transform, crs=Ls[names[0]]["G"]["crs"], ny=grid.shape[0], nx=grid.shape[1]), zones=Ls, names=names,
             zone_id={z: zone_id(z) for z in names}, own_id=own_id, dem=comp("dem", np.nan), dem_raw=comp("dem_raw", np.nan), src=comp("src", 0, "u1"),
             is_fabdem=comp("is_fabdem", False, bool), bias=comp("bias", 0.0), sig=comp("sig", 0.0), hand=comp("hand", np.nan), dist=comp("dist", np.nan),
             pre=comp_labelled("pre"), s1_pre_dark=comp_labelled("s1_pre_dark"), seed=comp_labelled("seed"), cut=comp("cut", False, bool), inh=comp("inh", False, bool),
             fp=(comp("fp", False, bool) if all(L["fp"] is not None for L in Ls.values()) else None), xs=grid.xs(), ys=grid.ys(),
             vertical_frame=Ls[names[0]]["vertical_frame"])
    M["base_geom"] = np.isfinite(M["dem"]) & (M["dist"] <= DIST_MAX_M)      # the dam buffer is added by `dam_mask`
    M["regions"] = region_masks(M)
    return M


def dam_mask(M, dxm):
    return (M["xs"] < dxm - DAM_BUFFER_M)[None, :] & np.ones((M["G"]["ny"], 1), bool)


def region_masks(M):
    """Accounting regions on the union grid (owned cells only)."""
    o = M["own_id"] > 0
    R = {"DNIPRO_CORRIDOR": o & ~M["cut"], "INHULETS_VALLEY_rect": o & M["inh"]}
    if M["fp"] is not None:
        R["P42_FLOODPLAIN_DOMAIN"] = o & M["fp"]
    return R


def potential_mosaic(M, W, Z, day, rule=PRIMARY_RULE, dem=None, Hmat=None, margin=0.0, connectivity=8, seed=None, base=None):
    """(P_t, H_t) on the union grid: C_t = base & terrain < H_t; connected_ceiling keeps the components touching the seed network."""
    dem = M["dem"] if dem is None else dem; seed = M["seed"] if seed is None else seed; base = M["base"] if base is None else base
    w = W.field(Z, day, margin, Hmat)
    cand = base & (dem < w)
    if rule == "ceiling_only":
        return cand, w
    if rule == "hand_and_ceiling":
        return cand & np.isfinite(M["hand"]) & (M["hand"] < w - RIVER_LEVEL_M), w
    return connected_to_seed(cand, seed, connectivity), w


def potential_zonal(M, W, Zs, day, rule=PRIMARY_RULE, dem=None, Hmat=None, margin=0.0, connectivity=8, seed=None, base=None):
    """The SUPERSEDED rev-5 evaluation (review F06): per zone, ownership inside the candidate mask BEFORE labelling, each zone
    with its own water-surface lattice `Zs[zone]`; composed on the union grid. Reproduction gate and seam check only."""
    dem = M["dem"] if dem is None else dem; seed = M["seed"] if seed is None else seed; base = M["base"] if base is None else base
    g = M["grid"]; pot = np.zeros(M["dem"].shape, bool); w_u = np.full(M["dem"].shape, np.nan, "f4")
    for z in M["names"]:
        own = g.extract(M["own_id"], z) == M["zone_id"][z]; w = W.field(Zs[z], day, margin, Hmat)
        cand = g.extract(base, z) & own & (g.extract(dem, z) < w)
        if rule == "ceiling_only":
            pz = cand
        elif rule == "hand_and_ceiling":
            hz = g.extract(M["hand"], z); pz = cand & np.isfinite(hz) & (hz < w - RIVER_LEVEL_M)
        else:
            pz = connected_to_seed(cand, g.extract(seed, z), connectivity)
        rs, cs = g.window(z); pot[rs, cs] |= pz; wz = w_u[rs, cs]; wz[own] = w[own]
    return pot, w_u


def baseline_mosaic(M, W, Z, rule=PRIMARY_RULE, dem=None, Hmat=None, connectivity=8, seed=None, base=None, margin=BASE_MARGIN_M, pot_fn=None):
    """(baseline, normally_wet): the union over the pre-breach days of P under the SAME rule (fixed margin), plus the optically
    observed pre-breach water (rev 9: no Sentinel-1 darkness); normally_wet = the model-only part."""
    pot_fn = potential_mosaic if pot_fn is None else pot_fn
    nw = np.zeros(M["pre"].shape, bool)
    for d in DATES[DATES <= pd.Timestamp(BASELINE_DATE)]:
        nw |= pot_fn(M, W, Z, d, rule, dem, Hmat, margin, connectivity, seed, base)[0]
    nw &= ~M["pre"]
    return M["pre"] | nw, nw


def m6_layers(L, P, run="U2b_B1B2_v003A"):
    """v003_A EVENT_FLOOD label and the U2b prediction on the zone grid (10 m -> 20 m nearest)."""
    G = L["G"]; f = L["frame"]
    with rasterio.open(P.OUT / f / "m6_labels_v003_A.tif") as s:
        ont = s.read(1); tr10 = s.transform
    arm, suffix = run.split("_B1B2_")
    with rasterio.open(P.OUT / f / "m6" / f"{arm}_{suffix}_score.tif") as s:
        q = s.read(1)
    thr = json.loads((ROOT / "runs" / run / "validation_threshold.json").read_text())["threshold"]
    out = {}
    for nm, a in (("label_event_flood", (ont == 1)), ("label_reference_water", (ont == 2)),
                  ("pred", (q != 65535) & (q / 1e4 >= thr)), ("pred_valid", q != 65535)):
        d = np.zeros((G["ny"], G["nx"]), "u1")
        reproject(a.astype("u1"), d, src_transform=tr10, src_crs=G["crs"], dst_transform=G["transform"], dst_crs=G["crs"], resampling=Resampling.nearest)
        out[nm] = d.astype(bool)
    return out


def zonal_potential_legacy(L, W, day, rule, dxm, margin=0.0):
    """The SUPERSEDED per-zone evaluation (ownership inside the candidate mask before labelling; review F06) -- seam check only."""
    Z = W.prepare(L); w = W.field(Z, day, margin)
    base = np.isfinite(L["dem"]) & (L["dist"] <= DIST_MAX_M) & (L["xs"] < dxm - DAM_BUFFER_M)[None, :] & L["own"]
    cand = base & (L["dem"] < w)
    if rule == "ceiling_only":
        return cand
    if rule == "hand_and_ceiling":
        return cand & np.isfinite(L["hand"]) & (L["hand"] < w - RIVER_LEVEL_M)
    return connected_to_seed(cand, L["seed"], 8)


def main():
    global SWOT_MARGIN_M, TERRAIN_BIAS, TERRAIN_TABLE
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", default=PRIMARY_RULE, choices=RULES, help="connected_ceiling = PRIMARY (terrain < WSE and 8-connected to the pre-breach RIVER network, D-SEED); "
                    "hand_and_ceiling = p42 rule (+ HAND < WSE - 1 m; lower bound); ceiling_only = no connectivity (upper bound)")
    ap.add_argument("--margin", type=float, default=SWOT_MARGIN_M, help="WSE margin added to SWOT/gauge on event days (central 0.0; the old p42 value 0.5 is a sensitivity)")
    ap.add_argument("--closure", default="kherson_paper1", choices=sorted(CLOSURES), help="vertical closure of the SWOT heights (see CLOSURES)")
    ap.add_argument("--dem-bias", default="class", choices=["class", "none"], help="subtract the FABDEM residual class bias vs ICESat-2 on FABDEM cells (default) or not (sensitivity)")
    ap.add_argument("--connectivity", type=int, default=8, choices=[4, 8])
    ap.add_argument("--seed-network", default="main_stem", choices=["main_stem", "all_prewater"],
                    help="main_stem = PRIMARY (D-SEED 2026-09-30): the largest connected component of the pre-breach water map; all_prewater = superseded rev-7 seeding (provenance variant)")
    ap.add_argument("--memory", action="store_true", help="D-MEMORY sensitivity: a cell inundated on day t-1 stays inundated on day t while still below the surface (retained water)")
    ap.add_argument("--max-gap-days", type=int, default=None, help="a node is unavailable on days farther than this from one of its observations (sensitivity)")
    ap.add_argument("--wse-river-aware", action="store_true", help="median over the nodes of the nearest node's river only (sensitivity)")
    ap.add_argument("--seam-check", action="store_true", help="compare the mosaic with the superseded per-zone evaluation on three dates (tables/p95_seam_check<sfx>.csv)")
    ap.add_argument("--terrain-table", default="fabdem_zone", choices=["fabdem_zone", "legacy_c_seamless"], help="legacy_c_seamless = the rev-5 table on every cell (gate only)")
    ap.add_argument("--evaluation", default="mosaic", choices=["mosaic", "zonal_legacy"], help="zonal_legacy = rev 5: ownership before connectivity (gate only)")
    ap.add_argument("--coarse-anchor", default="map", choices=["map", "grid_legacy"], help="grid_legacy = rev 5: each zone's own 100 m lattice (gate only)")
    ap.add_argument("--no-rasters", action="store_true", help="tables only (no rasters, npz or figures): gate and attribution runs")
    ap.add_argument("--inhulets-gauge-node", action="store_true", help="add the Inhulets gauge Kalynivske (80575, p95k) as a water-surface node (sensitivity)")
    ap.add_argument("--fallback-max-km", type=float, default=None, help="no water surface from a node farther than this (gauge-capped cells keep the gauge; sensitivity)")
    args = ap.parse_args(); RULE = args.rule; SFX = f"_{RULE}"
    TERRAIN_BIAS = "class" if args.dem_bias == "class" else "none"
    if args.closure != "kherson_paper1":
        SFX += "_closure_p59"
    if TERRAIN_BIAS == "none":
        SFX += "_dem_uncorrected"
    if abs(args.margin - SWOT_MARGIN_M) > 1e-9:
        SWOT_MARGIN_M = args.margin; SFX += f"_m{int(round(args.margin * 100)):03d}"
    if args.connectivity == 4:
        SFX += "_conn4"
    if args.seed_network == "all_prewater":
        SFX += "_seed_allprewater"
    if args.memory:
        SFX += "_memory"
    if args.max_gap_days is not None:
        SFX += f"_maxgap{args.max_gap_days}"
    if args.wse_river_aware:
        SFX += "_riveraware"
    if args.inhulets_gauge_node:
        SFX += "_inhulets_gauge_node"
    if args.fallback_max_km is not None:
        SFX += f"_fallback{args.fallback_max_km:g}km"
    TERRAIN_TABLE = args.terrain_table
    lg = ("T" if args.terrain_table != "fabdem_zone" else "") + ("Z" if args.evaluation != "mosaic" else "") + ("A" if args.coarse_anchor != "map" else "")
    if lg:
        SFX += f"_legacy{lg}"
    t0 = time.time(); P = load_p92(); FIG.mkdir(parents=True, exist_ok=True)
    W, dxm, dym, nodes = load_engine(args.closure, args.max_gap_days, args.wse_river_aware, args.coarse_anchor, inhulets_gauge_node() if args.inhulets_gauge_node else None,
                                     args.fallback_max_km * 1000 if args.fallback_max_km is not None else None)
    closure_offset = float((nodes.H - nodes.H_evrf).median())
    gauge, gauge_src = load_gauge()
    kx, ky = tf_transform("EPSG:4326", CFG.CRS_METRIC, [KHERSON_LONLAT[0]], [KHERSON_LONLAT[1]])
    WSFX = "" if args.closure == "kherson_paper1" else "_closure_p59"
    H = W.profile_display(dxm, dym); H.to_csv(CFG.TABLES / f"p95_wse_profile_display{WSFX}.csv")
    pd.DataFrame(W.H, index=W.node_id, columns=[str(d.date()) for d in W.dates]).to_csv(CFG.TABLES / f"p95_wse_nodes{WSFX}.csv")
    pd.DataFrame(W.obs, index=W.node_id, columns=[str(d.date()) for d in W.dates]).to_csv(CFG.TABLES / f"p95_wse_nodes_observed{WSFX}.csv")
    W.support_table().to_csv(CFG.TABLES / f"p95_wse_support_nodes{SFX}.csv", index=False)
    print(f"WSE engine: {len(W.node_id) - 1} nodes + gauge, {int(W.obs.sum())} observed node-days; dam x = {dxm:.0f}", flush=True)
    M = mosaic_layers(P); G = M["G"]; print("mosaic", G["ny"], "x", G["nx"], "cells;", {z: L["G"]["ny"] * L["G"]["nx"] for z, L in M["zones"].items()}, round(time.time() - t0), "s", flush=True)
    M["base"] = M["base_geom"] & dam_mask(M, dxm)
    if RULE == "hand_and_ceiling":
        M["base"] &= np.isfinite(M["hand"])
    seed = largest_component(M["seed"]) if args.seed_network == "main_stem" else M["seed"]
    if args.evaluation == "zonal_legacy":
        Z = {z: W.prepare(L) for z, L in M["zones"].items()}; POT = potential_zonal
        Z_support = W.prepare(M) if args.coarse_anchor == "map" else None
    else:
        Z = W.prepare(M); POT = potential_mosaic; Z_support = Z
    baseline, normally_wet = baseline_mosaic(M, W, Z, RULE, connectivity=args.connectivity, seed=seed, pot_fn=POT)
    print("baseline", round(float(baseline.sum()) * CELL_KM2), "km2, normally wet", round(float(normally_wet.sum()) * CELL_KM2), "km2", round(time.time() - t0), "s", flush=True)
    R = M["regions"]
    acc = {z: dict(dur=np.zeros((L["G"]["ny"], L["G"]["nx"]), "u1")) for z, L in M["zones"].items()}
    for z, L in M["zones"].items():
        a = acc[z]; a["first"] = np.zeros_like(a["dur"]); a["last"] = np.zeros_like(a["dur"]); a["maxd"] = np.zeros(a["dur"].shape, "f4"); a["packed"] = {}
        a["obs"] = np.logical_or.reduce([L["V"][d] for d in L["V"]]); a["own"] = M["grid"].extract(M["own_id"], z) == M["zone_id"][z]
        a["regions"] = {nm: M["grid"].extract(m, z) & a["own"] for nm, m in R.items()}; a["nw"] = M["grid"].extract(normally_wet, z)
    rows, val_rows, m6_rows, sup_rows, src_rows, man = [], [], [], [], [], {}
    corridor_base = M["base"] & R["DNIPRO_CORRIDOR"]
    far_full = Z_support["far"].reshape(Z_support["shape_c"])[np.ix_(Z_support["ri"], Z_support["ci"])] if Z_support is not None else None
    prev_pot = None
    for k, d in enumerate(DATES, 1):
        pot, w = POT(M, W, Z, d, RULE, margin=SWOT_MARGIN_M, connectivity=args.connectivity, seed=seed)
        if args.memory and prev_pot is not None:                              # D-MEMORY: retained water while still below today's surface
            pot = pot | (prev_pot & M["base"] & (M["dem"] < w))
        prev_pot = pot
        new = pot & ~baseline; depth = np.where(pot, w - M["dem"], 0).astype("f4"); ds = str(d.date())
        if Z_support is not None:
            kind = W.support_kind(Z_support, ds); cb = corridor_base
            for kk, nm in SUPPORT_KIND.items():
                m = cb & (kind == kk)
                sup_rows.append(dict(date=ds, support_kind=nm, km2=round(float(m.sum()) * CELL_KM2, 1), share_of_corridor_base=round(float(m.sum() / max(cb.sum(), 1)), 4),
                                     km2_water=round(float((m & pot).sum()) * CELL_KM2, 1), km2_gauge_capped=round(float((m & far_full).sum()) * CELL_KM2, 1)))
        cnt = np.bincount(M["src"][new & R["DNIPRO_CORRIDOR"]], minlength=6)
        for code, nm in SOURCE_NAMES.items():
            src_rows.append(dict(date=ds, region="DNIPRO_CORRIDOR", terrain_source=nm, source_code=code, new_km2=round(float(cnt[code]) * CELL_KM2, 2), share_of_new=round(float(cnt[code] / max(cnt.sum(), 1)), 4)))
        for z, L in M["zones"].items():
            a = acc[z]; g = M["grid"]; pz, nz, dz = g.extract(pot, z), g.extract(new, z), g.extract(depth, z)
            a["dur"] += nz; a["first"][(a["first"] == 0) & nz] = k; a["last"][nz] = k; a["maxd"] = np.maximum(a["maxd"], np.where(nz, dz, 0))
            a["packed"][ds] = np.packbits(nz)
            if ds == "2023-06-08":
                a["d0608"] = np.where(nz, dz, np.nan).astype("f4")
            for nm, m in a["regions"].items():
                rows.append(dict(zone=z, date=ds, region=nm, potential_km2=round(float((pz & m).sum()) * CELL_KM2, 1), new_km2=round(float((nz & m).sum()) * CELL_KM2, 1),
                                 new_volume_hm3=round(float(dz[nz & m].sum()) * 400 / 1e6, 2), new_mean_depth_m=round(float(dz[nz & m].mean()), 2) if (nz & m).any() else 0.0,
                                 new_in_s1_observable_km2=round(float((nz & m & a["obs"]).sum()) * CELL_KM2, 1), kherson_gauge_m=round(float(gauge.get(d, np.nan)), 2)))
            if ds in L["W"]:                                                   # validation against the S1 scene of that day
                v = L["V"][ds]; s1new = L["W"][ds] & ~(L["pre"] | L["s1_pre_dark"])      # S1 new water: not where S1 was already dark
                for nm, m in a["regions"].items():
                    mm = m & v; hit = (nz & s1new & mm).sum(); miss = (~nz & s1new & mm).sum(); fa = (nz & ~s1new & mm).sum()
                    nw = (~nz & s1new & mm & a["nw"]).sum()                    # S1 dark-water onset on normally wet low ground
                    val_rows.append(dict(zone=z, date=ds, region=nm, s1_valid_km2=round(float(mm.sum()) * CELL_KM2, 1),
                                         s1_new_km2=round(float((s1new & mm).sum()) * CELL_KM2, 1), hand_new_km2=round(float((nz & mm).sum()) * CELL_KM2, 1),
                                         hit_km2=round(float(hit) * CELL_KM2, 1), miss_km2=round(float(miss) * CELL_KM2, 1),
                                         miss_on_normally_wet_km2=round(float(nw) * CELL_KM2, 1), hand_only_km2=round(float(fa) * CELL_KM2, 1),
                                         POD=round(float(hit / max(hit + miss, 1)), 3), FAR=round(float(fa / max(hit + fa, 1)), 3),
                                         CSI=round(float(hit / max(hit + miss + fa, 1)), 3), POD_excl_normally_wet=round(float(hit / max(hit + miss - nw, 1)), 3)))
        if k % 10 == 0:
            print(ds, round(time.time() - t0), "s", flush=True)
    kind0609 = W.support_kind(Z_support, "2023-06-09") if Z_support is not None else np.full(M["dem"].shape, 255, "u1")
    curve_cache = {}
    for z, L in M["zones"].items():
        a = acc[z]; G_ = L["G"]; ever = a["dur"] > 0; M6 = m6_layers(L, P)
        for nm, m in a["regions"].items():
            mm = m & M6["pred_valid"]; lab, prd = M6["label_event_flood"] & mm, M6["pred"] & mm
            m6_rows.append(dict(zone=z, region=nm, label_event_flood_km2=round(float(lab.sum()) * CELL_KM2, 1),
                                label_inside_hand_ever_frac=round(float((lab & ever).sum() / max(lab.sum(), 1)), 3),
                                u2b_pred_km2=round(float(prd.sum()) * CELL_KM2, 1), u2b_inside_hand_ever_frac=round(float((prd & ever).sum() / max(prd.sum(), 1)), 3),
                                hand_ever_km2=round(float((ever & mm).sum()) * CELL_KM2, 1),
                                hand_ever_not_predicted_not_labelled_km2=round(float((ever & mm & ~prd & ~lab).sum()) * CELL_KM2, 1),
                                hand_peak_0608_km2=round(float((np.isfinite(a["d0608"]) & m).sum()) * CELL_KM2, 1)))
        od = DYN / (z + SFX)
        if args.no_rasters:
            man[z] = dict(outputs="(no rasters: --no-rasters)", residual_rows_used={str(k): v for k, v in L["residual_rows"]["rows"].items()}, residual_source=L["residual_rows"]["source"])
            continue
        od.mkdir(parents=True, exist_ok=True)
        prof = dict(driver="GTiff", height=G_["ny"], width=G_["nx"], count=1, crs=G_["crs"], transform=G_["transform"], compress="deflate", tiled=True)
        for nm, arr, dt, nd in (("duration_days", a["dur"], "uint8", 0), ("first_day", a["first"], "uint8", 0), ("last_day", a["last"], "uint8", 0),
                                ("max_depth_m", a["maxd"], "float32", 0.0), ("depth_2023-06-08_m", np.nan_to_num(a["d0608"], nan=-9999), "float32", -9999.0),
                                ("wse_support_kind", M["grid"].extract(kind0609, z), "uint8", 255)):
            with rasterio.open(od / f"{nm}.tif", "w", dtype=dt, nodata=nd, **prof) as o:
                o.write(arr.astype(dt), 1)
                o.update_tags(producer="p95_hand_daily_inundation.py rev 6", day_index_origin=str(DATES[0].date()), vertical_datum=VERTICAL_DATUM,
                              meaning="terrain-allowed NEW inundation from the SWOT+gauge water surface on the union mosaic; ownership for accounting; not an observation",
                              support_kind=str(SUPPORT_KIND) if nm == "wse_support_kind" else "")
        np.savez_compressed(od / "daily_new.npz", shape=np.array([G_["ny"], G_["nx"]]), baseline=np.packbits(M["grid"].extract(baseline, z)),
                            normally_wet=np.packbits(a["nw"]), **a["packed"])
        man[z] = dict(cells_base=int((M["grid"].extract(M["base"], z) & a["own"]).sum()), grid=[G_["ny"], G_["nx"]], outputs=str(od),
                      fabdem_share_of_base=round(float((M["grid"].extract(M["is_fabdem"], z) & M["grid"].extract(M["base"], z) & a["own"]).sum() / max((M["grid"].extract(M["base"], z) & a["own"]).sum(), 1)), 4),
                      residual_rows_used={str(k): v for k, v in L["residual_rows"]["rows"].items()}, residual_source=L["residual_rows"]["source"])
        curve_cache[z] = dict(L=L, ever=ever, dur=a["dur"], d0608=a["d0608"], s1_0609=(L["W"].get("2023-06-09", np.zeros_like(ever)) & ~(L["pre"] | L["s1_pre_dark"])),
                              v_0609=L["V"].get("2023-06-09", np.zeros_like(ever)), new_0609=np.unpackbits(a["packed"]["2023-06-09"], count=ever.size).reshape(ever.shape).astype(bool))
        print(z, "written", round(time.time() - t0), "s", flush=True)
    A = pd.DataFrame(rows); A.to_csv(CFG.TABLES / f"p95_daily_area{SFX}.csv", index=False)
    Vd = pd.DataFrame(val_rows); Vd.to_csv(CFG.TABLES / f"p95_validation_s1{SFX}.csv", index=False)
    Mt = pd.DataFrame(m6_rows); Mt.to_csv(CFG.TABLES / f"p95_validation_m6{SFX}.csv", index=False)
    pd.DataFrame(sup_rows).to_csv(CFG.TABLES / f"p95_wse_support_cells{SFX}.csv", index=False)
    pd.DataFrame(src_rows).to_csv(CFG.TABLES / f"p95_source_share{SFX}.csv", index=False)
    seam = None
    if args.seam_check and args.evaluation == "mosaic":
        srows = []
        for ds in ("2023-06-07", "2023-06-09", "2023-06-13"):
            pot, _ = potential_mosaic(M, W, Z, ds, RULE, margin=SWOT_MARGIN_M, connectivity=args.connectivity, seed=seed)
            for z, L in M["zones"].items():
                old = zonal_potential_legacy(L, W, ds, RULE, dxm, SWOT_MARGIN_M); a = acc[z]; nz = M["grid"].extract(pot, z)
                for nm, m in a["regions"].items():
                    srows.append(dict(date=ds, zone=z, region=nm, mosaic_km2=round(float((nz & m).sum()) * CELL_KM2, 2), zonal_legacy_km2=round(float((old & m).sum()) * CELL_KM2, 2),
                                      mosaic_only_km2=round(float((nz & ~old & m).sum()) * CELL_KM2, 2), zonal_only_km2=round(float((old & ~nz & m).sum()) * CELL_KM2, 2)))
        seam = pd.DataFrame(srows); seam.to_csv(CFG.TABLES / f"p95_seam_check{SFX}.csv", index=False); print(seam.to_string(index=False))
    (CFG.TABLES / f"p95_manifest{SFX}.json").write_text(json.dumps(dict(
        rev=9, rule=__doc__.split("Rule")[1].split("Sensitivities")[0], constants=dict(SWOT_MARGIN_M=SWOT_MARGIN_M, RIVER_LEVEL_M=RIVER_LEVEL_M,
        SWOT_MAX_DIST_M=SWOT_MAX_DIST_M, DIST_MAX_M=DIST_MAX_M, baseline_until=BASELINE_DATE, margin_m=SWOT_MARGIN_M, connectivity=args.connectivity,
        seed_network=args.seed_network, memory=bool(args.memory), max_gap_days=args.max_gap_days, wse_river_aware=args.wse_river_aware, coarse_m=WSE.COARSE_M),
        event_source_network=dict(definition=("largest 8-connected component of the pre-breach optical water map (p60 pre_water_frac >= 20 %, frames composed where they have labels)"
                                              if args.seed_network == "main_stem" else "every pre-breach water cell (superseded rev-7 seeding; ponds and canals included)"),
                                  seed_km2=round(float(seed.sum()) * CELL_KM2, 2), all_prewater_km2=round(float(M["seed"].sum()) * CELL_KM2, 2),
                                  decision="D-SEED_PRIMARY (maintainer, 2026-09-30); D-MEMORY = sensitivity only"),
        baseline=dict(definition="optical pre-breach water (p60 pre_water_frac >= 20 %) OR the same rule on any pre-breach day (normally wet)",
                      s1_pre_dark="Sentinel-1 dark water 06-01/02: NOT in the baseline (rev 9, maintainer 2026-09-30); masks the S1 'new water' of the validations only",
                      s1_pre_dark_km2=round(float(M["s1_pre_dark"].sum()) * CELL_KM2, 1), optical_km2=round(float(M["pre"].sum()) * CELL_KM2, 1),
                      baseline_km2=round(float(baseline.sum()) * CELL_KM2, 1), normally_wet_km2=round(float(normally_wet.sum()) * CELL_KM2, 1)),
        evaluation=("union mosaic of the zones (one terrain graph, one water surface); ownership only for accounting and the per-zone rasters (review F06)" if args.evaluation == "mosaic"
                    else "SUPERSEDED per-zone evaluation (rev 5; ownership before connectivity) -- reproduction gate / attribution only"),
        legacy_flags=dict(terrain_table=args.terrain_table, evaluation=args.evaluation, coarse_anchor=args.coarse_anchor),
        wse_method=f"node-based: median of K={WSE.K} nearest SWOT nodes within {WSE.RMAX_M/1e3:.0f} km, per-node time interpolation (observed/interpolated/held flags), gauge as a node, gauge cap beyond {WSE.FAR_M/1e3:.0f} km west of the gauge; coarse {WSE.COARSE_M:.0f} m lattice anchored in map coordinates (rev 6; the p59 chainage is not comparable across SWORD branches)",
        wse_support=(dict(coarse_within_3km_frac=Z_support["within_frac"], coarse_far_cap_frac=Z_support["far_frac"]) if Z_support is not None
                     else {z: dict(coarse_within_3km_frac=v["within_frac"], coarse_far_cap_frac=v["far_frac"]) for z, v in Z.items()}),
        terrain=dict(product="seamless terrain-bed elevation model (p55): FABDEM bare-earth DTM outside the surveyed channel (source 3, 4), observed/reconstructed bed inside (1, 2, 5)",
                     bias_correction=TERRAIN_BIAS, bias_meaning="residual class-dependent terrain-elevation bias (median FABDEM - ICESat-2 ground by WorldCover class), FABDEM cells only; bed cells uncorrected",
                     source_codes=SOURCE_NAMES, fabdem_sources=list(FABDEM_SOURCES), bed_sources=list(BED_SOURCES)),
        vertical_frame=dict(datum=M["vertical_frame"], chains=VERTICAL_CHAINS, checked="assert_same_vertical_frame over the terrain raster tag, the SWOT chain and the gauge column",
                            paper1_frame=dict(fabdem_shift_m=round(PF.mixed_chain_shift(), 4), kherson_delta_epsg9902_m=PF.KHERSON_DELTA_EPSG9902_M,
                                              note="Paper 1 v6 production chain: FABDEM cells raised by c_production - c_tide-free (Paper 2 paired + free2mean with the tide-free closure); Kherson gauge at the post's own EPSG:9902 step")),
        rule_variant=RULE, closure=args.closure, closure_chain=CLOSURES[args.closure], closure_offset_vs_p59_H_evrf_m=round(closure_offset, 4),
        c_kherson_m=C_KHERSON_M, c_kherson_nmad_m=C_KHERSON_NMAD_M, zones=man, seam_check=(seam.to_dict("records") if seam is not None else None),
        sources=dict(swot_nodes="tables/p59_swot_flood_nodes.csv (SWOT-DNIPRO p59)", gauge=gauge_src, hand="floodplain/<ZONE>_hand_m.tif (p42)",
                     terrain="dem_seamless/<ZONE>_dem_evrf2019_20m.tif + _dem_source_20m.tif (p55)")), indent=1, default=str))
    # ---- pooled daily curve (zones summed; overlap owned by ZONE_2) ----------------------------------------------------
    S = A.groupby(["date", "region"], as_index=False).agg(new_km2=("new_km2", "sum"), potential_km2=("potential_km2", "sum"),
                                                          new_volume_hm3=("new_volume_hm3", "sum"), kherson_gauge_m=("kherson_gauge_m", "first"))
    S.to_csv(CFG.TABLES / f"p95_daily_area_pooled{SFX}.csv", index=False)
    Vp = Vd.groupby(["date", "region"], as_index=False)[["s1_new_km2", "hand_new_km2", "hit_km2", "miss_km2", "miss_on_normally_wet_km2", "hand_only_km2"]].sum()
    Vp["POD"] = (Vp.hit_km2 / (Vp.hit_km2 + Vp.miss_km2).clip(lower=1e-9)).round(3); Vp["FAR"] = (Vp.hand_only_km2 / (Vp.hit_km2 + Vp.hand_only_km2).clip(lower=1e-9)).round(3)
    Vp["CSI"] = (Vp.hit_km2 / (Vp.hit_km2 + Vp.miss_km2 + Vp.hand_only_km2).clip(lower=1e-9)).round(3)
    Vp["POD_excl_normally_wet"] = (Vp.hit_km2 / (Vp.hit_km2 + Vp.miss_km2 - Vp.miss_on_normally_wet_km2).clip(lower=1e-9)).round(3)
    Vp.to_csv(CFG.TABLES / f"p95_validation_s1_pooled{SFX}.csv", index=False)
    if args.no_rasters:
        pd.set_option("display.width", 250); print(S[S.region == "DNIPRO_CORRIDOR"][["date", "new_km2", "potential_km2", "new_volume_hm3"]].to_string(index=False))
        print(f"-> tables/p95_*{SFX}.csv (tables only, {round(time.time() - t0)} s)"); return
    regs = [r for r in ("DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect") if r in set(S.region)]
    fig, axs = plt.subplots(2, len(regs), figsize=(5 * len(regs), 6.4), constrained_layout=True, gridspec_kw=dict(height_ratios=[3, 1.2]))
    for j, r in enumerate(regs):
        a, b = axs[0, j], axs[1, j]; s = S[S.region == r].copy(); s["t"] = pd.to_datetime(s.date)
        a.plot(s.t, s.new_km2, color=C_HAND, lw=2, label="terrain-reconstructed new inundation (SWOT + gauge WSE)")
        v = Vp[Vp.region == r].copy(); v["t"] = pd.to_datetime(v.date)
        a.plot(v.t, v.s1_new_km2, color=C_S1, lw=0, marker="o", ms=6, label="S1 observed new water (same footprint)")
        a.plot(v.t, v.hand_new_km2, color=C_HAND, lw=0, marker="o", ms=6, mfc="white", label="reconstruction on the S1 footprint")
        pk = s.loc[s.new_km2.idxmax()]; a.annotate(f"{pk.new_km2:.0f} km² {pk.date[5:]}", (pk.t, pk.new_km2), fontsize=7, color="#52514e", xytext=(4, 2), textcoords="offset points")
        a.axvline(pd.Timestamp("2023-06-06"), color="#e34948", lw=0.8, ls="--")
        a.set_title(r, fontsize=9, loc="left"); a.set_ylabel("new inundation, km²", fontsize=8)
        b.plot(s.t, s.kherson_gauge_m, color=C_GAUGE, lw=1.5); b.set_ylabel("Kherson gauge, m EVRF2019", fontsize=8)
        for ax in (a, b):
            ax.grid(color="#efece6", lw=0.8); ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=7)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d")); ax.set_xlim(DATES[0], DATES[-1])
    axs[0, 0].legend(fontsize=6.5, frameon=False)
    fig.suptitle(f"Daily terrain-connectivity reconstruction from the observed water surface ({RULE}; planar per node neighbourhood; ponding not modelled) vs S1 observations", fontsize=10)
    fig.savefig(FIG / f"hand_dyn_curve{SFX}.png", dpi=120, bbox_inches="tight"); plt.close(fig)
    # ---- WSE profile heatmap ------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 4.2), constrained_layout=True)
    Hm = H.loc[:, (H.columns >= 0) & (H.columns <= 90)].interpolate(axis=0, limit_direction="both")
    im = ax.imshow(Hm.values, aspect="auto", cmap=LinearSegmentedColormap.from_list("w", ["#f4f8fc", "#2a78d6", "#0b2a5c"]),
                   extent=[Hm.columns.min(), Hm.columns.max() + 1, mdates.date2num(DATES[-1]), mdates.date2num(DATES[0])])
    ax.yaxis_date(); ax.yaxis.set_major_formatter(mdates.DateFormatter("%m-%d")); ax.set_xlabel("straight-line distance from the dam, km", fontsize=8)
    dkh = float(np.hypot(kx[0] - dxm, ky[0] - dym) / 1e3)
    ax.axvline(dkh, color="#e34948", lw=0.8, ls="--"); ax.text(dkh + 0.5, mdates.date2num(DATES[2]), "Kherson gauge", fontsize=7, color="#e34948")
    ax.set_title("Water surface H(d, t), gauge-anchored EGG2015-referenced heights -- main-stem SWOT node medians per 1 km of straight-line distance from the dam (display; the reconstruction is node-based)", fontsize=8, loc="left")
    cb = fig.colorbar(im, ax=ax, shrink=0.8); cb.set_label("m EVRF2019", fontsize=8); ax.tick_params(labelsize=7)
    fig.savefig(FIG / "hand_dyn_wse_profile.png", dpi=120, bbox_inches="tight"); plt.close(fig)
    # ---- maps per zone: 06-08 depth (unobserved maximum), duration, 06-09 agreement -----------------------------------
    for zone, C in curve_cache.items():
        G_ = C["L"]["G"]; DS = 4; ds_ = lambda a: a[::DS, ::DS]
        ext = [G_["transform"].c / 1e3, (G_["transform"].c + 20 * G_["nx"]) / 1e3, (G_["transform"].f - 20 * G_["ny"]) / 1e3, G_["transform"].f / 1e3]
        ext_show = (ext[0], 540, ext[2], ext[3]) if zone.startswith("ZONE_4") else tuple(ext)
        fig, axs = plt.subplots(1, 3, figsize=(16, 5.6), constrained_layout=True)
        a = axs[0]; im = a.imshow(ds_(C["d0608"]), cmap=LinearSegmentedColormap.from_list("d", ["#dbe9f8", "#2a78d6", "#0b2a5c"]), vmin=0, vmax=6, extent=ext, interpolation="nearest")
        a.set_title(f"{zone}\n2023-06-08 (reconstructed maximum, no full-coverage scene): terrain-allowed NEW inundation depth", fontsize=8, loc="left"); fig.colorbar(im, ax=a, shrink=0.7).set_label("depth, m", fontsize=7)
        a2 = axs[1]; im2 = a2.imshow(np.ma.masked_where(ds_(C["dur"]) == 0, ds_(C["dur"])), cmap=LinearSegmentedColormap.from_list("t", ["#f4f8fc", "#eda100", "#e34948", "#4a3aa7"]), vmin=1, vmax=30, extent=ext, interpolation="nearest")
        a2.set_title("duration of terrain-allowed new inundation, days (05-26..07-10)", fontsize=8, loc="left"); fig.colorbar(im2, ax=a2, shrink=0.7).set_label("days", fontsize=7)
        a3 = axs[2]; st = np.zeros(C["ever"].shape, "u1"); v = C["v_0609"]; st[v] = 1; st[v & C["new_0609"]] = 2; st[v & C["s1_0609"]] = 3; st[v & C["new_0609"] & C["s1_0609"]] = 4
        a3.imshow(ds_(st), cmap=ListedColormap(["#ffffff", "#efece6", "#7fb3e6", "#eb6834", "#1baf7a"]), vmin=-0.5, vmax=4.5, extent=ext, interpolation="nearest")
        a3.set_title("2023-06-09: reconstruction vs S1 observed new water (S1 footprint only)", fontsize=8, loc="left")
        a3.legend(handles=[Patch(fc="#1baf7a", label="both"), Patch(fc="#7fb3e6", label="terrain only (allowed, not seen: vegetation / drained / terrain)"),
                           Patch(fc="#eb6834", label="S1 only (seen, not allowed: terrain error, ponding or sensor)"), Patch(fc="#efece6", label="neither")],
                  fontsize=6.5, frameon=False, loc="lower left")
        for ax in axs:
            ax.set_xlim(ext_show[0], ext_show[1]); ax.set_ylim(ext_show[2], ext_show[3]); ax.set_aspect("equal"); ax.tick_params(labelsize=6)
        fig.savefig(FIG / f"hand_dyn_maps_{zone}{SFX}.png", dpi=100, bbox_inches="tight"); plt.close(fig)
    pd.set_option("display.width", 250)
    print(S[S.region == "DNIPRO_CORRIDOR"][["date", "new_km2", "potential_km2", "new_volume_hm3", "kherson_gauge_m"]].to_string(index=False))
    print(Vp.to_string(index=False)); print(Mt.to_string(index=False))
    print(f"-> tables/p95_*{SFX}.csv, {FIG.relative_to(ROOT)}/hand_dyn_*.png, {DYN}  ({round(time.time() - t0)} s)")


if __name__ == "__main__":
    main()
