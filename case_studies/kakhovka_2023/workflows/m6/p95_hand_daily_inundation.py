# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Terrain (HAND) reconstruction of the DAILY potential inundation.
"""P95 -- daily potential inundation from the observed water surface: SWOT KaRIn node WSE (daily, 1-day orbit) + the
Kherson gauge, projected onto the terrain with the p42 v21 rule, for every day 2023-05-26 .. 2023-07-10.

This is the third pillar next to the U-Net (M6) and the RF surface class (p73): it says what the water surface ALLOWS on
every day, including the 7-8 June peak that no satellite image saw, and it is independent of the S1/S2 labels.

Rule (per zone 20 m grid, p42 v20/v21 constants, unchanged):
    WSE_t(cell) = median H_t of the 5 nearest nodes within 3 km + margin (central 0.0 m; the SWOT heights are re-anchored to the
                  Kherson-local closure of Paper 1 -- see CLOSURES -- so no bias term is needed; uncertainty enters via p95e);
                  cells > 15 km from a node: min(that, Kherson gauge_t + margin)
    potential_t = HAND < WSE_t - 1 m (river floor)  AND  DEM_seamless < WSE_t  AND  dist to pre-breach water <= 10 km
                  AND downstream of the dam (x < dam - 1 km);   depth_t = WSE_t - DEM
    new_t       = potential_t AND NOT baseline,  baseline = potential on ANY pre-breach day 05-26..06-05 under the same rule
                  (normal regime; new = 0 before the breach by construction; absorbs the +-10 cm WSE noise) OR observed
                  pre-breach water (S1 06-01/02, p60 pre_water_frac >= 20 %). The model-only part of the baseline
                  ("normally wet": low reed beds below the normal water surface that no optical/SAR mask lists as water) is
                  reported in the S1 validation as its own category -- S1 dark-water onset there is a DEPTH signal (reeds
                  submerged), not inundation onset.
    --rule ceiling_only drops the HAND term (p42 v21: HAND is unreliable where the delta drainage is unmapped) = upper bound.
    --rule connected_ceiling: DEM < WSE_t AND 8-connected to the pre-breach optical water network (p60 pre_water_frac >= 20 %)
                  -- no HAND (unmapped delta drainage), no isolated low pockets; the recommended primary variant.
Water surface (rev 4, node-based): every cell takes the median of its 5 nearest SWOT nodes within 3 km on the day; each
node is time-filled between its own observations; the Kherson gauge is one more node; no chainage is used (the SWORD
p_dist_out chainage of p59 is not comparable across branches). A straight-line-distance profile is written for display only.
HAND = p42 (FABDEM floored at 1 m, WhiteboxTools, streams = pre-breach water); DEM = p55 seamless EVRF2019 (bathymetric
bed where surveyed, FABDEM elsewhere), so channel depth is physical where the bed is known.
DEM (rev 5): the seamless DEM minus its class-median bias against night ICESat-2 (Paper 2 / p57), so that the p95e band is
centred on the central run; `--dem-bias none` is the uncorrected sensitivity.
Limits (state them with every number): a planar water surface per reach, no momentum, no timing of filling / draining
(ponds drain slower than the channel, so the recession is UNDER-estimated), HAND is unreliable where the delta drainage is
incompletely mapped (p42 v21 note), and the Inhulets valley only gets the Dnipro level at its mouth (backwater assumption).

Outputs: $BULK_ROOT/floodplain_dyn/<ZONE>/{duration_days.tif, first_day.tif, last_day.tif, max_depth_m.tif,
         depth_2023-06-08_m.tif, daily_new.npz (bit-packed, one key per date)}
         <case_study>/tables/p95_{daily_area,wse_table,validation_s1,validation_m6}.csv, p95_manifest.json
         <case_study>/figures/m6_v003A/hand_dyn_{curve,maps_<ZONE>,wse_profile}.png
"""
from __future__ import annotations
import importlib.util, json, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio import features
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling, transform as tf_transform
from scipy.spatial import cKDTree
from scipy import ndimage
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.patches import Patch
from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = ROOT / "figures" / "m6_v003A"
DYN = CFG.BULK_ROOT / "floodplain_dyn"
ZONES = {"ZONE_4_DAM_TO_KHERSON_FLOODWAY": dict(frame="B1", cache="ZONE_4_FLOODWAY_june2023_s32"),
         "ZONE_2_KHERSON_DELTA": dict(frame="B2", cache="ZONE_2_KHERSON_DELTA_flood_june2023")}
ZONE2_BBOX = (437980.0, 5134980.0, 475720.0, 5211580.0)      # ZONE_2 owns the overlap (same rule as m6_split_v1: B2 owns)
DAM_LONLAT = (33.3667, 46.7783); KHERSON_LONLAT = (32.612026, 46.623750)
SWOT_MARGIN_M, RIVER_LEVEL_M, SWOT_MAX_DIST_M, DIST_MAX_M, DAM_BUFFER_M = 0.0, 1.0, 15000.0, 10000.0, 1000.0
BASE_MARGIN_M = 0.0                    # the pre-breach baseline uses the central (zero) margin; --margin varies event days only
# Vertical closure (rev 3, 2026-09-25, after Paper 1 of the series): SWOT heights are EGG2015-referenced heights,
# H_S = wse + geoid_hght - zeta_EGG2015 (SWOT's crust is already mean-tide, no permanent-tide term), shifted by the LOCAL
# empirical closure residual c = gauge - satellite. Paper 1 measured c ~ 0 at Kherson (+0.9 cm RiverSP pre-breach, -2.6 cm PIXC,
# +1.9 cm through the breach fortnight, NMAD 4-5 cm), whereas p59 had applied the mean reservoir closure (-0.173 m) plus a
# free2mean term (-0.036 m) to the downstream reach, i.e. -0.209 m too low, hidden by the old +0.5 m margin.
C_KHERSON_M, C_KHERSON_NMAD_M = 0.0, 0.05
# DEM bias correction (rev 5): the seamless DEM sits above night ICESat-2 ground by a class-dependent median (Paper 2 / p57,
# C seamless by WorldCover class: trees +1.5-2 m, wetland +0.5, grass +0.4, cropland ~0). The reconstruction subtracts that
# class median so the Monte-Carlo band (p95e, class NMAD as sigma) is centred on the reported central run.
DEM_BIAS = "p57_class"                 # or "none" (sensitivity, suffix _dem_uncorrected)
DEM_CLASS = {10: "trees", 30: "grass", 40: "cropland", 50: "built", 60: "bare", 90: "wetland"}
CLOSURES = {"kherson_paper1": "H = wse + geoid_hght - zeta_EGG2015 + c_Kherson (c = 0.00 m, NMAD 0.05 m; Paper 1 Table 5 / Sec. 5.12)",
            "p59_reservoir": "H_evrf of p59: wse + geoid_hght + free2mean(lat) - zeta + mean reservoir c (-0.173 m) -- SUPERSEDED, sensitivity only"}
BASELINE_DATE = "2023-06-05"
DATES = pd.date_range("2023-05-26", "2023-07-10", freq="D")
S1_DATES = ["2023-06-01", "2023-06-02", "2023-06-06", "2023-06-09", "2023-06-13", "2023-06-14", "2023-06-18",
            "2023-06-21", "2023-06-25", "2023-06-26", "2023-06-30"]
CELL_KM2 = 0.0004
C_HAND, C_S1, C_GAUGE = "#2a78d6", "#eb6834", "#52514e"


def load_p92():
    s = importlib.util.spec_from_file_location("p92", HERE / "p92_flood_area_dam_to_liman.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def dem_error_table():
    """median (bias) and NMAD (sigma) of seamless DEM - ICESat-2 by WorldCover class (p57 copy, Paper 2)."""
    src = CFG.TABLES / "p57_dem_accuracy_night.csv"
    if not src.exists():
        src = Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p57_dem_accuracy_night.csv"
    Tb = pd.read_csv(src); out = {}
    for code, nm in DEM_CLASS.items():
        r = Tb[Tb.set.str.contains("C seamless, ZONE_2_KHERSON_DELTA, WorldCover " + nm)]
        if len(r) == 0:
            r = Tb[Tb.set.str.contains("C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover " + nm)]
        if len(r):
            out[code] = dict(bias=float(r.iloc[0]["median"]), sigma=float(r.iloc[0]["NMAD"]), rmse=float(r.iloc[0]["RMSE"]), n=int(r.iloc[0]["N"]), cls=nm)
    a = Tb[Tb.set.str.startswith("C seamless, ZONE_2_KHERSON_DELTA")].iloc[0]
    out["default"] = dict(bias=float(a["median"]), sigma=float(a["NMAD"]), rmse=float(a["RMSE"]), n=int(a["N"]), cls="all")
    return out, str(src)


def dem_bias_fields(zone, G):
    """(bias, sigma) per cell from WorldCover 2021 on the zone grid and the p57 class table."""
    E, _ = dem_error_table()
    with rasterio.open(CFG.BULK_ROOT / "worldcover_frames" / zone / "wc_2021_20m.tif") as s:
        wc = np.zeros((G["ny"], G["nx"]), "u1")
        reproject(s.read(1), wc, src_transform=s.transform, src_crs=s.crs, dst_transform=G["transform"], dst_crs=G["crs"], resampling=Resampling.nearest)
    bias = np.full((G["ny"], G["nx"]), E["default"]["bias"], "f4"); sig = np.full((G["ny"], G["nx"]), E["default"]["sigma"], "f4")
    for code, v in E.items():
        if code != "default":
            bias[wc == code] = v["bias"]; sig[wc == code] = v["sigma"]
    return bias, sig


def load_engine(closure="kherson_paper1"):
    """(WSE engine, dam x, dam y, nodes) exactly as main() builds them -- used by p95c/p95d/p95e."""
    nodes = pd.read_csv(CFG.TABLES / "p59_swot_flood_nodes.csv", parse_dates=["date"])
    nodes["H"] = (nodes.wse + nodes.geoid_hght - nodes.zeta + C_KHERSON_M) if closure == "kherson_paper1" else nodes.H_evrf
    kh = pd.read_csv(Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p59_swot_vs_kherson.csv", parse_dates=["date"])
    gauge = kh.set_index("date").H_gauge_evrf.dropna()
    kx, ky = tf_transform("EPSG:4326", CFG.CRS_METRIC, [KHERSON_LONLAT[0]], [KHERSON_LONLAT[1]])
    dx, dy = tf_transform("EPSG:4326", CFG.CRS_METRIC, [DAM_LONLAT[0]], [DAM_LONLAT[1]])
    return WSE(nodes, gauge, kx[0], ky[0]), dx[0], dy[0], nodes


class WSE:
    """Water surface per day, NODE-BASED (rev 4): no along-channel chainage. The SWORD p_dist_out chainage of p59 is not
    comparable across branches (Inhulets, Kokan', the side channels at Kherson start their own count), so binning H by s
    mixed reaches. Here every cell takes the median height of its K nearest SWOT nodes within RMAX_M on the day; each node
    is time-filled between its own observations; the Kherson gauge is one more node at its own coordinates. Cells whose
    nearest node is farther than FAR_M and that lie west (downstream) of the gauge are capped at the gauge level. Evaluated
    on a COARSE (100 m) lattice and replicated to 20 m."""
    K, RMAX_M, FAR_M, COARSE, MIN_OBS = 5, 3000.0, 15000.0, 5, 3

    def __init__(self, nodes: pd.DataFrame, gauge: pd.Series, kx: float, ky: float):
        daily = nodes.groupby(["node_id", nodes.date.dt.normalize()]).H.median().unstack().reindex(columns=DATES)
        daily = daily[daily.notna().sum(1) >= self.MIN_OBS]
        pos = nodes.groupby("node_id").agg(x=("x", "median"), y=("y", "median"), reach_id=("reach_id", "first"),
                                           river_name=("river_name", "first")).loc[daily.index]
        g = gauge.reindex(DATES)
        self.node_id = list(daily.index) + ["GAUGE_80805"]
        self.reach = list(pos.reach_id) + ["GAUGE"]; self.river = list(pos.river_name) + ["gauge"]
        self.xy = np.vstack([pos[["x", "y"]].values, [[kx, ky]]]).astype("f8")
        self.obs = np.vstack([daily.notna().values, g.notna().values[None]])
        self.H = np.vstack([daily.interpolate(axis=1, limit_direction="both").values, g.interpolate(limit_direction="both").values[None]]).astype("f4")
        self.dates = list(DATES); self.tree = cKDTree(self.xy); self.kx = kx

    def prepare(self, L):
        G = L["G"]; c = self.COARSE
        xs, ys = L["xs"][::c], L["ys"][::c]; YY, XX = np.meshgrid(ys, xs, indexing="ij"); pts = np.c_[XX.ravel(), YY.ravel()]
        d, idx = self.tree.query(pts, k=self.K, distance_upper_bound=self.RMAX_M)
        valid = np.isfinite(d); idx = np.where(valid, idx, 0)
        d1, i1 = self.tree.query(pts, k=1)
        return dict(idx=idx, valid=valid, i1=i1, far=(d1 > self.FAR_M) & (pts[:, 0] < self.kx), shape_c=(len(ys), len(xs)),
                    shape=(G["ny"], G["nx"]), far_frac=float(((d1 > self.FAR_M) & (pts[:, 0] < self.kx)).mean()))

    def field(self, Z, day, margin=0.0, offset=0.0, off_far=0.0, Hmat=None):
        Hm = self.H if Hmat is None else Hmat; j = self.dates.index(pd.Timestamp(day))
        col = Hm[:, j]; hv = np.where(Z["valid"], col[Z["idx"]], np.nan)
        with np.errstate(all="ignore"):
            h = np.nanmedian(hv, axis=1)
        h = np.where(np.isfinite(h), h, col[Z["i1"]])                       # no node within RMAX -> nearest node
        gj = col[-1]
        if np.isfinite(gj):
            h = np.where(Z["far"], np.minimum(h, gj + off_far), h)
        h = (h + margin + offset).astype("f4").reshape(Z["shape_c"])
        c = self.COARSE
        return np.repeat(np.repeat(h, c, 0), c, 1)[:Z["shape"][0], :Z["shape"][1]]

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


def zone_layers(zone, P):
    Z = ZONES[zone]; T = CFG.BULK_ROOT / "terrain" / zone
    with rasterio.open(CFG.BULK_ROOT / "dem_seamless" / f"{zone}_dem_evrf2019_20m.tif") as s:
        dem = s.read(1).astype("f4"); dem[dem == s.nodata] = np.nan; G = dict(transform=s.transform, crs=s.crs, ny=s.height, nx=s.width)
    def onto(path, nodata_to_nan=True, resampling=Resampling.nearest, dtype="f4"):
        with rasterio.open(path) as s:
            a = s.read(1).astype("f4"); nd = s.nodata
            if nodata_to_nan and nd is not None:
                a[a == nd] = np.nan
            d = np.full((G["ny"], G["nx"]), np.nan, "f4")
            reproject(a, d, src_transform=s.transform, src_crs=s.crs, dst_transform=G["transform"], dst_crs=G["crs"],
                      resampling=resampling, src_nodata=np.nan, dst_nodata=np.nan)
        return d
    if DEM_BIAS == "p57_class":
        bias, _ = dem_bias_fields(zone, G); dem = (dem - bias).astype("f4")            # rev 5: class-median bias removed
    hand = onto(CFG.BULK_ROOT / "floodplain" / zone / f"{zone}_hand_m.tif")
    dist = onto(T / "dist_ref_water_m.tif")
    with rasterio.open(P.OUT / Z["frame"] / "labels.tif") as s:
        d_ = list(s.descriptions); wf = s.read(d_.index("pre_water_frac") + 1).astype("f4"); tr10 = s.transform
        pre10 = (wf >= 20).astype("f4")
    pre = np.zeros((G["ny"], G["nx"]), "f4")
    reproject(pre10, pre, src_transform=tr10, src_crs=G["crs"], dst_transform=G["transform"], dst_crs=G["crs"], resampling=Resampling.nearest)
    # S1 per-scene water / valid from the zone cache (20 m, own origin)
    z = np.load(CFG.S1_CACHE / Z["cache"] / "per_scene_water.npz", allow_pickle=True); shp = tuple(int(v) for v in z["shape"])
    trc = from_origin(float(z["x0"]), float(z["y1"]), float(z["cell"]), float(z["cell"]))
    un = lambda k: np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
    W, V = {}, {}
    for k in sorted(z.files):
        if not k.startswith("2023"):
            continue
        d = k[:10]; w, v = un(k), un("valid_" + k)
        for D, a in ((W, w & v), (V, v)):
            m = np.zeros((G["ny"], G["nx"]), "u1")
            reproject(a.astype("u1"), m, src_transform=trc, src_crs=G["crs"], dst_transform=G["transform"], dst_crs=G["crs"], resampling=Resampling.nearest)
            D[d] = D.get(d, np.zeros((G["ny"], G["nx"]), bool)) | m.astype(bool)
    pre_s1 = W["2023-06-01"] | W["2023-06-02"]
    xs = G["transform"].c + 20.0 * (np.arange(G["nx"]) + 0.5); ys = G["transform"].f - 20.0 * (np.arange(G["ny"]) + 0.5)
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
    return dict(G=G, dem=dem, hand=hand, dist=dist, pre=(pre > 0) | pre_s1, seed=pre > 0, W=W, V=V, xs=xs, ys=ys, own=own, cut=cut,
                inh=inh, fp=fp, frame=Z["frame"])


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


def main():
    global SWOT_MARGIN_M
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", default="hand_and_ceiling", choices=["hand_and_ceiling", "ceiling_only", "connected_ceiling"],
                    help="hand_and_ceiling = p42 extension rule (default); ceiling_only = DEM < WSE within 10 km of pre-breach "
                         "water, no HAND (p42 v21 observed-term rule; upper bound where the delta drainage is unmapped)")
    ap.add_argument("--margin", type=float, default=SWOT_MARGIN_M, help="WSE margin added to SWOT/gauge on event days (central 0.0; the old p42 value 0.5 is a sensitivity)")
    ap.add_argument("--closure", default="kherson_paper1", choices=sorted(CLOSURES), help="vertical closure of the SWOT heights (see CLOSURES)")
    ap.add_argument("--dem-bias", default="p57_class", choices=["p57_class", "none"], help="subtract the class-median DEM bias vs ICESat-2 (default) or not (sensitivity)")
    args = ap.parse_args(); RULE = args.rule; SFX = "" if RULE == "hand_and_ceiling" else f"_{RULE}"
    global DEM_BIAS
    DEM_BIAS = args.dem_bias
    if args.closure != "kherson_paper1":
        SFX += "_closure_p59"
    if DEM_BIAS == "none":
        SFX += "_dem_uncorrected"
    if abs(args.margin - SWOT_MARGIN_M) > 1e-9:
        SWOT_MARGIN_M = args.margin; SFX += f"_m{int(round(args.margin * 100)):03d}"
    t0 = time.time(); P = load_p92(); FIG.mkdir(parents=True, exist_ok=True)
    nodes = pd.read_csv(CFG.TABLES / "p59_swot_flood_nodes.csv", parse_dates=["date"])
    if args.closure == "kherson_paper1":
        nodes["H"] = nodes.wse + nodes.geoid_hght - nodes.zeta + C_KHERSON_M
    else:
        nodes["H"] = nodes.H_evrf
    closure_offset = float((nodes.H - nodes.H_evrf).median())
    kh = pd.read_csv(Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p59_swot_vs_kherson.csv", parse_dates=["date"])
    gauge = kh.set_index("date").H_gauge_evrf.dropna()
    kx, ky = tf_transform("EPSG:4326", CFG.CRS_METRIC, [KHERSON_LONLAT[0]], [KHERSON_LONLAT[1]])
    dx, dy = tf_transform("EPSG:4326", CFG.CRS_METRIC, [DAM_LONLAT[0]], [DAM_LONLAT[1]])
    W = WSE(nodes, gauge, kx[0], ky[0])
    WSFX = "" if args.closure == "kherson_paper1" else "_closure_p59"
    H = W.profile_display(dx[0], dy[0]); H.to_csv(CFG.TABLES / f"p95_wse_profile_display{WSFX}.csv")
    pd.DataFrame(W.H, index=W.node_id, columns=[str(d.date()) for d in W.dates]).to_csv(CFG.TABLES / f"p95_wse_nodes{WSFX}.csv")
    pd.DataFrame(W.obs, index=W.node_id, columns=[str(d.date()) for d in W.dates]).to_csv(CFG.TABLES / f"p95_wse_nodes_observed{WSFX}.csv")
    print(f"WSE engine: {len(W.node_id) - 1} nodes + gauge, {int(W.obs.sum())} observed node-days; dam x = {dx[0]:.0f}", flush=True)
    rows, val_rows, m6_rows, man = [], [], [], {}
    curve_cache = {}
    for zone in ZONES:
        L = zone_layers(zone, P); G = L["G"]; print(zone, "layers", round(time.time() - t0), "s", flush=True)
        Z = W.prepare(L)
        base = np.isfinite(L["dem"]) & (L["dist"] <= DIST_MAX_M) & (L["xs"] < dx[0] - DAM_BUFFER_M)[None, :] & L["own"]
        if RULE == "hand_and_ceiling":
            base &= np.isfinite(L["hand"])
        def wse_on(d, margin=None):
            return W.field(Z, d, SWOT_MARGIN_M if margin is None else margin)
        def potential(d, margin=None):
            w = wse_on(d, margin)
            if RULE == "ceiling_only":
                return base & (L["dem"] < w), w
            if RULE == "connected_ceiling":                    # bathtub with connectivity: DEM < WSE and 8-connected to
                cand = base & (L["dem"] < w)                    # the pre-breach OPTICAL water network (no HAND, no SAR seeds)
                lab, n = ndimage.label(cand, structure=np.ones((3, 3), bool))
                keep = np.zeros(n + 1, bool); keep[np.unique(lab[cand & L["seed"]])] = True; keep[0] = False
                return keep[lab], w
            return base & (L["hand"] < w - RIVER_LEVEL_M) & (L["dem"] < w), w
        normally_wet = np.zeros(L["pre"].shape, bool)
        for d in DATES[DATES <= pd.Timestamp(BASELINE_DATE)]:                # union over every pre-breach day under the SAME
            normally_wet |= potential(d, BASE_MARGIN_M)[0]                    # rule, FIXED p42 margin: the normal regime does not
        normally_wet &= ~L["pre"]                                             # model-only normal water (mostly low reed beds)
        baseline = L["pre"] | normally_wet
        dur = np.zeros((G["ny"], G["nx"]), "u1"); first = np.zeros_like(dur); last = np.zeros_like(dur)
        maxd = np.zeros((G["ny"], G["nx"]), "f4"); packed = {}
        regions = {"DNIPRO_CORRIDOR": L["own"] & ~L["cut"], "INHULETS_VALLEY_rect": L["own"] & L["inh"]}
        if L["fp"] is not None:
            regions["P42_FLOODPLAIN_DOMAIN"] = L["own"] & L["fp"]
        obs = np.logical_or.reduce([L["V"][d] for d in L["V"]])
        for k, d in enumerate(DATES, 1):
            pot, w = potential(d); new = pot & ~baseline; depth = np.where(pot, w - L["dem"], 0).astype("f4")
            dur += new; first[(first == 0) & new] = k; last[new] = k; maxd = np.maximum(maxd, np.where(new, depth, 0))
            packed[str(d.date())] = np.packbits(new)
            if str(d.date()) == "2023-06-08":
                d0608 = np.where(new, depth, np.nan).astype("f4")
            for nm, m in regions.items():
                rows.append(dict(zone=zone, date=str(d.date()), region=nm, potential_km2=round(float((pot & m).sum()) * CELL_KM2, 1),
                                 new_km2=round(float((new & m).sum()) * CELL_KM2, 1),
                                 new_volume_hm3=round(float(depth[new & m].sum()) * 400 / 1e6, 2),
                                 new_mean_depth_m=round(float(depth[new & m].mean()), 2) if (new & m).any() else 0.0,
                                 new_in_s1_observable_km2=round(float((new & m & obs).sum()) * CELL_KM2, 1),
                                 kherson_gauge_m=round(float(gauge.get(d, np.nan)), 2)))
            ds = str(d.date())
            if ds in L["W"]:                                                   # validation against the S1 scene of that day
                v = L["V"][ds]; s1new = L["W"][ds] & ~L["pre"]
                for nm, m in regions.items():
                    mm = m & v; hit = (new & s1new & mm).sum(); miss = (~new & s1new & mm).sum(); fa = (new & ~s1new & mm).sum()
                    nw = (~new & s1new & mm & normally_wet).sum()             # S1 dark-water onset on normally wet low ground
                    val_rows.append(dict(zone=zone, date=ds, region=nm, s1_valid_km2=round(float(mm.sum()) * CELL_KM2, 1),
                                         s1_new_km2=round(float((s1new & mm).sum()) * CELL_KM2, 1), hand_new_km2=round(float((new & mm).sum()) * CELL_KM2, 1),
                                         hit_km2=round(float(hit) * CELL_KM2, 1), miss_km2=round(float(miss) * CELL_KM2, 1),
                                         miss_on_normally_wet_km2=round(float(nw) * CELL_KM2, 1),
                                         hand_only_km2=round(float(fa) * CELL_KM2, 1),
                                         POD=round(float(hit / max(hit + miss, 1)), 3), FAR=round(float(fa / max(hit + fa, 1)), 3),
                                         CSI=round(float(hit / max(hit + miss + fa, 1)), 3),
                                         POD_excl_normally_wet=round(float(hit / max(hit + miss - nw, 1)), 3)))
        ever = dur > 0
        M6 = m6_layers(L, P)
        for nm, m in regions.items():
            mm = m & M6["pred_valid"]
            lab, prd = M6["label_event_flood"] & mm, M6["pred"] & mm
            m6_rows.append(dict(zone=zone, region=nm, label_event_flood_km2=round(float(lab.sum()) * CELL_KM2, 1),
                                label_inside_hand_ever_frac=round(float((lab & ever).sum() / max(lab.sum(), 1)), 3),
                                u2b_pred_km2=round(float(prd.sum()) * CELL_KM2, 1),
                                u2b_inside_hand_ever_frac=round(float((prd & ever).sum() / max(prd.sum(), 1)), 3),
                                hand_ever_km2=round(float((ever & mm).sum()) * CELL_KM2, 1),
                                hand_ever_not_predicted_not_labelled_km2=round(float((ever & mm & ~prd & ~lab).sum()) * CELL_KM2, 1),
                                hand_peak_0608_km2=round(float((np.isfinite(d0608) & m).sum()) * CELL_KM2, 1)))
        od = DYN / (zone + SFX); od.mkdir(parents=True, exist_ok=True)
        prof = dict(driver="GTiff", height=G["ny"], width=G["nx"], count=1, crs=G["crs"], transform=G["transform"], compress="deflate", tiled=True)
        for nm, a, dt, nd in (("duration_days", dur, "uint8", 0), ("first_day", first, "uint8", 0), ("last_day", last, "uint8", 0),
                              ("max_depth_m", maxd, "float32", 0.0), ("depth_2023-06-08_m", np.nan_to_num(d0608, nan=-9999), "float32", -9999.0)):
            with rasterio.open(od / f"{nm}.tif", "w", dtype=dt, nodata=nd, **prof) as o:
                o.write(a.astype(dt), 1); o.update_tags(producer="p95_hand_daily_inundation.py", day_index_origin=str(DATES[0].date()),
                                                        meaning="terrain-allowed NEW inundation from SWOT+gauge WSE; not an observation")
        np.savez_compressed(od / "daily_new.npz", shape=np.array([G["ny"], G["nx"]]), **packed)
        man[zone] = dict(cells=int(base.sum()), far_from_swot_frac_coarse=round(Z["far_frac"], 3), outputs=str(od))
        curve_cache[zone] = dict(L=L, ever=ever, dur=dur, d0608=d0608, s1_0609=(L["W"].get("2023-06-09", np.zeros_like(ever)) & ~L["pre"]),
                                 v_0609=L["V"].get("2023-06-09", np.zeros_like(ever)), new_0609=np.unpackbits(packed["2023-06-09"], count=ever.size).reshape(ever.shape).astype(bool))
        print(zone, "done", round(time.time() - t0), "s", flush=True)
    A = pd.DataFrame(rows); A.to_csv(CFG.TABLES / f"p95_daily_area{SFX}.csv", index=False)
    Vd = pd.DataFrame(val_rows); Vd.to_csv(CFG.TABLES / f"p95_validation_s1{SFX}.csv", index=False)
    M = pd.DataFrame(m6_rows); M.to_csv(CFG.TABLES / f"p95_validation_m6{SFX}.csv", index=False)
    (CFG.TABLES / f"p95_manifest{SFX}.json").write_text(json.dumps(dict(
        rule=__doc__.split("Rule")[1].split("Limits")[0], constants=dict(SWOT_MARGIN_M=SWOT_MARGIN_M, RIVER_LEVEL_M=RIVER_LEVEL_M,
        SWOT_MAX_DIST_M=SWOT_MAX_DIST_M, DIST_MAX_M=DIST_MAX_M, baseline_until=BASELINE_DATE, margin_m=SWOT_MARGIN_M),
        wse_method=f"node-based: median of K={WSE.K} nearest SWOT nodes within {WSE.RMAX_M/1e3:.0f} km, per-node time interpolation, gauge as a node, gauge cap beyond {WSE.FAR_M/1e3:.0f} km west of the gauge (rev 4; the p59 chainage is not comparable across SWORD branches)",
        dem_bias_correction=DEM_BIAS, dem_error_table=dem_error_table()[0],
        rule_variant=RULE, closure=args.closure, closure_chain=CLOSURES[args.closure], closure_offset_vs_p59_H_evrf_m=round(closure_offset, 4),
        c_kherson_m=C_KHERSON_M, c_kherson_nmad_m=C_KHERSON_NMAD_M, zones=man,
        sources=dict(swot_nodes="tables/p59_swot_flood_nodes.csv (SWOT-DNIPRO p59)", gauge="SWOT-DNIPRO p59_swot_vs_kherson.csv",
                     hand="floodplain/<ZONE>_hand_m.tif (p42)", dem="dem_seamless/<ZONE>_dem_evrf2019_20m.tif (p55)")), indent=1))
    # ---- pooled daily curve (zones summed; overlap owned by ZONE_2) ----------------------------------------------------
    S = A.groupby(["date", "region"], as_index=False).agg(new_km2=("new_km2", "sum"), potential_km2=("potential_km2", "sum"),
                                                          new_volume_hm3=("new_volume_hm3", "sum"), kherson_gauge_m=("kherson_gauge_m", "first"))
    S.to_csv(CFG.TABLES / f"p95_daily_area_pooled{SFX}.csv", index=False)
    Vp = Vd.groupby(["date", "region"], as_index=False)[["s1_new_km2", "hand_new_km2", "hit_km2", "miss_km2", "miss_on_normally_wet_km2", "hand_only_km2"]].sum()
    Vp["POD"] = (Vp.hit_km2 / (Vp.hit_km2 + Vp.miss_km2).clip(lower=1e-9)).round(3); Vp["FAR"] = (Vp.hand_only_km2 / (Vp.hit_km2 + Vp.hand_only_km2).clip(lower=1e-9)).round(3)
    Vp["CSI"] = (Vp.hit_km2 / (Vp.hit_km2 + Vp.miss_km2 + Vp.hand_only_km2).clip(lower=1e-9)).round(3)
    Vp["POD_excl_normally_wet"] = (Vp.hit_km2 / (Vp.hit_km2 + Vp.miss_km2 - Vp.miss_on_normally_wet_km2).clip(lower=1e-9)).round(3)
    Vp.to_csv(CFG.TABLES / f"p95_validation_s1_pooled{SFX}.csv", index=False)
    regs = [r for r in ("DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect") if r in set(S.region)]
    fig, axs = plt.subplots(2, len(regs), figsize=(5 * len(regs), 6.4), constrained_layout=True, gridspec_kw=dict(height_ratios=[3, 1.2]))
    for j, r in enumerate(regs):
        a, b = axs[0, j], axs[1, j]; s = S[S.region == r].copy(); s["t"] = pd.to_datetime(s.date)
        a.plot(s.t, s.new_km2, color=C_HAND, lw=2, label="HAND potential new inundation (SWOT + gauge WSE)")
        v = Vp[Vp.region == r].copy(); v["t"] = pd.to_datetime(v.date)
        a.plot(v.t, v.s1_new_km2, color=C_S1, lw=0, marker="o", ms=6, label="S1 observed new water (same footprint)")
        a.plot(v.t, v.hand_new_km2, color=C_HAND, lw=0, marker="o", ms=6, mfc="white", label="HAND on the S1 footprint")
        pk = s.loc[s.new_km2.idxmax()]; a.annotate(f"{pk.new_km2:.0f} km² {pk.date[5:]}", (pk.t, pk.new_km2), fontsize=7, color="#52514e", xytext=(4, 2), textcoords="offset points")
        a.axvline(pd.Timestamp("2023-06-06"), color="#e34948", lw=0.8, ls="--")
        a.set_title(r, fontsize=9, loc="left"); a.set_ylabel("new inundation, km²", fontsize=8)
        b.plot(s.t, s.kherson_gauge_m, color=C_GAUGE, lw=1.5); b.set_ylabel("Kherson gauge, m EVRF", fontsize=8)
        for ax in (a, b):
            ax.grid(color="#efece6", lw=0.8); ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=7)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d")); ax.set_xlim(DATES[0], DATES[-1])
    axs[0, 0].legend(fontsize=6.5, frameon=False)
    fig.suptitle(f"Daily potential inundation from the observed water surface ({RULE}; planar per reach; ponding not modelled) vs S1 observations", fontsize=10)
    fig.savefig(FIG / f"hand_dyn_curve{SFX}.png", dpi=120, bbox_inches="tight"); plt.close(fig)
    # ---- WSE profile heatmap ------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 4.2), constrained_layout=True)
    Hm = H.loc[:, (H.columns >= 0) & (H.columns <= 90)].interpolate(axis=0, limit_direction="both")
    im = ax.imshow(Hm.values, aspect="auto", cmap=LinearSegmentedColormap.from_list("w", ["#f4f8fc", "#2a78d6", "#0b2a5c"]),
                   extent=[Hm.columns.min(), Hm.columns.max() + 1, mdates.date2num(DATES[-1]), mdates.date2num(DATES[0])])
    ax.yaxis_date(); ax.yaxis.set_major_formatter(mdates.DateFormatter("%m-%d")); ax.set_xlabel("straight-line distance from the dam, km", fontsize=8)
    dkh = float(np.hypot(kx[0] - dx[0], ky[0] - dy[0]) / 1e3)
    ax.axvline(dkh, color="#e34948", lw=0.8, ls="--"); ax.text(dkh + 0.5, mdates.date2num(DATES[2]), "Kherson gauge", fontsize=7, color="#e34948")
    ax.set_title("Water surface H(d, t), gauge-anchored EGG2015-referenced heights -- main-stem SWOT node medians per 1 km of straight-line distance from the dam (display; the reconstruction is node-based)", fontsize=8, loc="left")
    cb = fig.colorbar(im, ax=ax, shrink=0.8); cb.set_label("m EVRF2019", fontsize=8); ax.tick_params(labelsize=7)
    fig.savefig(FIG / "hand_dyn_wse_profile.png", dpi=120, bbox_inches="tight"); plt.close(fig)
    # ---- maps per zone: 06-08 depth (unobserved peak), duration, 06-09 agreement ----------------------------------------
    for zone, C in curve_cache.items():
        G = C["L"]["G"]; DS = 4; ds = lambda a: a[::DS, ::DS]
        ext = [G["transform"].c / 1e3, (G["transform"].c + 20 * G["nx"]) / 1e3, (G["transform"].f - 20 * G["ny"]) / 1e3, G["transform"].f / 1e3]
        if zone.startswith("ZONE_4"):
            ext_show = (ext[0], 540, ext[2], ext[3])
        else:
            ext_show = tuple(ext)
        fig, axs = plt.subplots(1, 3, figsize=(16, 5.6), constrained_layout=True)
        a = axs[0]; im = a.imshow(ds(C["d0608"]), cmap=LinearSegmentedColormap.from_list("d", ["#dbe9f8", "#2a78d6", "#0b2a5c"]), vmin=0, vmax=6, extent=ext, interpolation="nearest")
        a.set_title(f"{zone}\n2023-06-08 (peak, no satellite scene): terrain-allowed NEW inundation depth", fontsize=8, loc="left"); fig.colorbar(im, ax=a, shrink=0.7).set_label("depth, m", fontsize=7)
        a2 = axs[1]; im2 = a2.imshow(np.ma.masked_where(ds(C["dur"]) == 0, ds(C["dur"])), cmap=LinearSegmentedColormap.from_list("t", ["#f4f8fc", "#eda100", "#e34948", "#4a3aa7"]), vmin=1, vmax=30, extent=ext, interpolation="nearest")
        a2.set_title("duration of terrain-allowed new inundation, days (05-26..07-10)", fontsize=8, loc="left"); fig.colorbar(im2, ax=a2, shrink=0.7).set_label("days", fontsize=7)
        a3 = axs[2]; st = np.zeros(C["ever"].shape, "u1"); v = C["v_0609"]; st[v] = 1; st[v & C["new_0609"]] = 2; st[v & C["s1_0609"]] = 3; st[v & C["new_0609"] & C["s1_0609"]] = 4
        a3.imshow(ds(st), cmap=ListedColormap(["#ffffff", "#efece6", "#7fb3e6", "#eb6834", "#1baf7a"]), vmin=-0.5, vmax=4.5, extent=ext, interpolation="nearest")
        a3.set_title("2023-06-09: HAND potential vs S1 observed new water (S1 footprint only)", fontsize=8, loc="left")
        a3.legend(handles=[Patch(fc="#1baf7a", label="both"), Patch(fc="#7fb3e6", label="HAND only (allowed, not seen: vegetation / drained / DEM)"),
                           Patch(fc="#eb6834", label="S1 only (seen, not allowed: DEM/HAND error or ponding)"), Patch(fc="#efece6", label="neither")],
                  fontsize=6.5, frameon=False, loc="lower left")
        for ax in axs:
            ax.set_xlim(ext_show[0], ext_show[1]); ax.set_ylim(ext_show[2], ext_show[3]); ax.set_aspect("equal"); ax.tick_params(labelsize=6)
        fig.savefig(FIG / f"hand_dyn_maps_{zone}{SFX}.png", dpi=100, bbox_inches="tight"); plt.close(fig)
    pd.set_option("display.width", 250)
    print(S[S.region == "DNIPRO_CORRIDOR"][["date", "new_km2", "new_volume_hm3", "kherson_gauge_m"]].to_string(index=False))
    print(Vp.to_string(index=False)); print(M.to_string(index=False))
    print(f"-> tables/p95_*, {FIG.relative_to(ROOT)}/hand_dyn_*.png, {DYN}  ({round(time.time() - t0)} s)")


if __name__ == "__main__":
    main()
