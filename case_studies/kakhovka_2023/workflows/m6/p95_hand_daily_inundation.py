# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Terrain (HAND) reconstruction of the DAILY potential inundation.
"""P95 -- daily potential inundation from the observed water surface: SWOT KaRIn node WSE (daily, 1-day orbit) + the
Kherson gauge, projected onto the terrain with the p42 v21 rule, for every day 2023-05-26 .. 2023-07-10.

This is the third pillar next to the U-Net (M6) and the RF surface class (p73): it says what the water surface ALLOWS on
every day, including the 7-8 June peak that no satellite image saw, and it is independent of the S1/S2 labels.

Rule (per zone 20 m grid, p42 v20/v21 constants, unchanged):
    WSE_t(cell) = H_t(s of the nearest SWOT node) + SWOT_MARGIN (0.5 m; SWOT under-reads the gauge);
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
H_t(s): per date, 1-km bins of the node median H_EVRF2019 (p59 nodes, node_q/dark_frac already screened) plus the daily
Kherson gauge as one more node; gaps filled in time (linear between SWOT days) then along s; 3-bin rolling median.
HAND = p42 (FABDEM floored at 1 m, WhiteboxTools, streams = pre-breach water); DEM = p55 seamless EVRF2019 (bathymetric
bed where surveyed, FABDEM elsewhere), so channel depth is physical where the bed is known.
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
SWOT_MARGIN_M, RIVER_LEVEL_M, SWOT_MAX_DIST_M, DIST_MAX_M, DAM_BUFFER_M = 0.5, 1.0, 15000.0, 10000.0, 1000.0
BASE_MARGIN_M = 0.5                    # the pre-breach baseline always uses the p42 margin (--margin varies event days only)
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


def wse_table(nodes: pd.DataFrame, gauge: pd.DataFrame, s_kh: float):
    """H[date, 1-km bin] in m EVRF2019: SWOT node medians + the Kherson gauge as a node; time then s interpolation."""
    nodes = nodes.copy(); nodes["b"] = np.floor(nodes.s_km).astype(int)
    bins = np.arange(int(np.floor(nodes.s_km.min())), int(np.ceil(nodes.s_km.max())) + 1)
    T = pd.DataFrame(index=DATES, columns=bins, dtype=float)
    med = nodes.groupby([nodes.date.dt.normalize(), "b"]).H_evrf.median()
    for (d, b), h in med.items():
        if d in T.index and b in T.columns:
            T.loc[d, b] = h
    bk = int(np.floor(s_kh))
    for d, h in gauge.items():
        if d in T.index:
            T.loc[d, bk] = h if np.isnan(T.loc[d, bk]) else 0.5 * (T.loc[d, bk] + h)
    raw_mask = T.notna()
    T = T.interpolate(axis=0, limit_direction="both")                      # time first (same reach, adjacent days)
    T = T.interpolate(axis=1, limit_direction="both")                      # then along the channel
    T = T.T.rolling(3, center=True, min_periods=1).median().T              # 3-km rolling median along s
    return T, raw_mask


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
    ap.add_argument("--margin", type=float, default=SWOT_MARGIN_M, help="WSE margin added to SWOT/gauge (p42: 0.5; sensitivity 0.3 / 0.8)")
    args = ap.parse_args(); RULE = args.rule; SFX = "" if RULE == "hand_and_ceiling" else f"_{RULE}"
    if abs(args.margin - SWOT_MARGIN_M) > 1e-9:
        SWOT_MARGIN_M = args.margin; SFX += f"_m{int(round(args.margin * 100)):03d}"
    t0 = time.time(); P = load_p92(); FIG.mkdir(parents=True, exist_ok=True)
    nodes = pd.read_csv(CFG.TABLES / "p59_swot_flood_nodes.csv", parse_dates=["date"])
    kh = pd.read_csv(Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p59_swot_vs_kherson.csv", parse_dates=["date"])
    gauge = kh.set_index("date").H_gauge_evrf.dropna()
    N = nodes.groupby("node_id").agg(x=("x", "median"), y=("y", "median"), s_km=("s_km", "median")).reset_index()
    tree = cKDTree(np.c_[N.x.values, N.y.values])
    kx, ky = tf_transform("EPSG:4326", CFG.CRS_METRIC, [KHERSON_LONLAT[0]], [KHERSON_LONLAT[1]])
    dx, dy = tf_transform("EPSG:4326", CFG.CRS_METRIC, [DAM_LONLAT[0]], [DAM_LONLAT[1]])
    s_kh = float(N.s_km.values[tree.query([kx[0], ky[0]])[1]])
    H, raw = wse_table(nodes, gauge, s_kh)
    H.to_csv(CFG.TABLES / "p95_wse_table.csv"); raw.to_csv(CFG.TABLES / "p95_wse_table_observed_mask.csv")
    print(f"WSE table {H.shape}, Kherson gauge at s = {s_kh:.1f} km, dam x = {dx[0]:.0f}", flush=True)
    bins = np.array(H.columns, dtype=int)
    rows, val_rows, m6_rows, man = [], [], [], {}
    curve_cache = {}
    for zone in ZONES:
        L = zone_layers(zone, P); G = L["G"]; print(zone, "layers", round(time.time() - t0), "s", flush=True)
        YY, XX = np.meshgrid(L["ys"], L["xs"], indexing="ij")
        dn, ii = tree.query(np.c_[XX.ravel(), YY.ravel()]); dn = dn.reshape(G["ny"], G["nx"]).astype("f4")
        sb = np.clip(np.floor(N.s_km.values[ii]).astype(int), bins.min(), bins.max()).reshape(G["ny"], G["nx"])
        bidx = np.searchsorted(bins, sb)
        far = (dn > SWOT_MAX_DIST_M) & (sb >= s_kh)          # cap by the Kherson gauge only DOWNSTREAM of it (outer delta)
        base = np.isfinite(L["dem"]) & (L["dist"] <= DIST_MAX_M) & (XX < dx[0] - DAM_BUFFER_M) & L["own"]
        if RULE == "hand_and_ceiling":
            base &= np.isfinite(L["hand"])
        del XX, YY
        def wse_on(d, margin=None):
            mg = SWOT_MARGIN_M if margin is None else margin
            h = H.loc[d].values.astype("f4")[bidx] + mg
            g = gauge.get(d, np.nan)
            if np.isfinite(g):
                h = np.where(far, np.minimum(h, g + mg), h)
            return h
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
        man[zone] = dict(cells=int(base.sum()), far_from_swot_frac=round(float(far[base].mean()), 3), outputs=str(od))
        curve_cache[zone] = dict(L=L, ever=ever, dur=dur, d0608=d0608, s1_0609=(L["W"].get("2023-06-09", np.zeros_like(ever)) & ~L["pre"]),
                                 v_0609=L["V"].get("2023-06-09", np.zeros_like(ever)), new_0609=np.unpackbits(packed["2023-06-09"], count=ever.size).reshape(ever.shape).astype(bool))
        print(zone, "done", round(time.time() - t0), "s", flush=True)
    A = pd.DataFrame(rows); A.to_csv(CFG.TABLES / f"p95_daily_area{SFX}.csv", index=False)
    Vd = pd.DataFrame(val_rows); Vd.to_csv(CFG.TABLES / f"p95_validation_s1{SFX}.csv", index=False)
    M = pd.DataFrame(m6_rows); M.to_csv(CFG.TABLES / f"p95_validation_m6{SFX}.csv", index=False)
    (CFG.TABLES / f"p95_manifest{SFX}.json").write_text(json.dumps(dict(
        rule=__doc__.split("Rule")[1].split("Limits")[0], constants=dict(SWOT_MARGIN_M=SWOT_MARGIN_M, RIVER_LEVEL_M=RIVER_LEVEL_M,
        SWOT_MAX_DIST_M=SWOT_MAX_DIST_M, DIST_MAX_M=DIST_MAX_M, baseline_until=BASELINE_DATE, margin_m=SWOT_MARGIN_M), rule_variant=RULE, kherson_s_km=s_kh, zones=man,
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
    Hm = H.loc[:, (H.columns >= 0) & (H.columns <= 90)]
    im = ax.imshow(Hm.values, aspect="auto", cmap=LinearSegmentedColormap.from_list("w", ["#f4f8fc", "#2a78d6", "#0b2a5c"]),
                   extent=[Hm.columns.min(), Hm.columns.max() + 1, mdates.date2num(DATES[-1]), mdates.date2num(DATES[0])])
    ax.yaxis_date(); ax.yaxis.set_major_formatter(mdates.DateFormatter("%m-%d")); ax.set_xlabel("distance from the dam along the channel, km", fontsize=8)
    ax.axvline(s_kh, color="#e34948", lw=0.8, ls="--"); ax.text(s_kh + 0.5, mdates.date2num(DATES[2]), "Kherson gauge", fontsize=7, color="#e34948")
    ax.set_title("Water surface elevation H(s, t), m EVRF2019 -- SWOT node medians + gauge, gaps interpolated (observed cells listed in p95_wse_table_observed_mask.csv)", fontsize=9, loc="left")
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
