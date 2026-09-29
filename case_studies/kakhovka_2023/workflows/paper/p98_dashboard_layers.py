# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Renders the lightweight map layers of the Streamlit dashboard.
"""P98 -- dashboard layers: classed / boolean PNG overlays in EPSG:4326 (~76 x 80 m) with bounds and a manifest, so the
dashboard needs no bulk data, no rasterio and no FABDEM-derived numeric raster (only rendered classed images).

Layers (apps/dashboard/data/):
  terrain/daily/<date>.png        terrain-reconstructed new inundation per day (connected ceiling, central), 46 days
  terrain/duration.png, terrain/max_depth.png, terrain/depth_2023-06-08.png   classed summaries
  s1/<date>_new.png, s1/<date>_footprint.png     S1 new dark water and the valid footprint, 11 dates
  unet/U2b_v003A.png, unet/U2_v1.png             predicted flood at the frozen thresholds (10 m frames -> 4326 grid)
  labels/v003A.png                                LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN
  rf/p73.png                                      RF20 classes
  reservoir/model/<date>.png, reservoir/exposed_day.png     p95h modelled pool (water / bed exposed since 06-05), day of exposure
  reservoir/s1/<date>.png                         p95h S1 VH dark surface (water or wet mud) / dark on 06-01 but not now / not observed
  reservoir/s2/<date>_{class,water,<INDEX>}.png   p25 k10e classes, water3 (+ p15 crosscheck water), the 7 indices in display classes
  context/*.geojson                               frames, cut rectangles, p42 floodplain (simplified), gauge and dam, reservoir pool
  manifest.json                                   id, file, bounds [[S, W], [N, E]], legend, source, sha256, bytes
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np, rasterio
from PIL import Image
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.crs import CRS
from floodstate_eo import _kakhovka_legacy_config as CFG

REPO = Path(__file__).resolve().parents[4]; OUTD = REPO / "apps" / "dashboard" / "data"
BULK = CFG.BULK_ROOT; FR = BULK / "frames10"
ZONES = {"ZONE_4_DAM_TO_KHERSON_FLOODWAY": "B1", "ZONE_2_KHERSON_DELTA": "B2"}
S1CACHE = {"ZONE_4_DAM_TO_KHERSON_FLOODWAY": "ZONE_4_FLOODWAY_june2023_s32", "ZONE_2_KHERSON_DELTA": "ZONE_2_KHERSON_DELTA_flood_june2023"}
DLON, DLAT = 0.001, 0.00072
BBOX = (32.15, 46.35, 33.55, 47.15)                         # W, S, E, N (both zones)
NX, NY = int(round((BBOX[2] - BBOX[0]) / DLON)), int(round((BBOX[3] - BBOX[1]) / DLAT))
TR = from_origin(BBOX[0], BBOX[3], DLON, DLAT); CRS4326 = CRS.from_epsg(4326)
RBOX = (33.30, 46.70, 35.40, 47.95)                         # W, S, E, N (the Kakhovka pool)
HEX = {"terrain": "#2a78d6", "s1": "#eb6834", "unet": "#4a3aa7", "unet2": "#8a7fd6", "foot": "#c3c2b7"}
MAN = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "grid": dict(crs="EPSG:4326", dlon=DLON, dlat=DLAT, nx=NX, ny=NY, bounds=[[BBOX[1], BBOX[0]], [BBOX[3], BBOX[2]]]), "layers": []}


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def box_grid(box):
    return from_origin(box[0], box[3], DLON, DLAT), int(round((box[3] - box[1]) / DLAT)), int(round((box[2] - box[0]) / DLON))


def cell_km2(box):
    lat = np.radians(0.5 * (box[1] + box[3])); return float(DLON * 111.32 * np.cos(lat) * DLAT * 110.574)


def to_grid(a, transform, crs, nodata=0, box=BBOX):
    tr, ny, nx = box_grid(box); d = np.full((ny, nx), nodata, a.dtype)
    reproject(a, d, src_transform=transform, src_crs=crs, dst_transform=tr, dst_crs=CRS4326, resampling=Resampling.nearest, src_nodata=nodata, dst_nodata=nodata)
    return d


def mosaic(per_zone):
    """per_zone: zone -> (array uint8, transform, crs) on the zone grid; ZONE_2 painted last (owns overlap)."""
    out = np.zeros((NY, NX), "u1")
    for z in ("ZONE_4_DAM_TO_KHERSON_FLOODWAY", "ZONE_2_KHERSON_DELTA"):
        if z in per_zone:
            a, tr, crs = per_zone[z]; g = to_grid(a, tr, crs); out = np.where(g > 0, g, out)
    return out


def write_png(arr, path: Path, palette: dict, legend: dict, layer_id: str, group: str, source: str, note: str = "", box=BBOX):
    """arr uint8 classes (0 = transparent) on the EPSG:4326 grid of `box`; palette code -> hex."""
    img = Image.fromarray(arr, "P"); pal = [0, 0, 0] * 256
    for k, h in palette.items():
        r, g, b = hexrgb(h); pal[3 * k:3 * k + 3] = [r, g, b]
    img.putpalette(pal); img.info["transparency"] = 0
    path.parent.mkdir(parents=True, exist_ok=True); img.save(path, optimize=True, transparency=0)
    ck = 0.0061 if box == BBOX else cell_km2(box)             # 0.0061: the published constant of the downstream box
    MAN["layers"].append(dict(id=layer_id, group=group, file=str(path.relative_to(OUTD)), bounds=[[box[1], box[0]], [box[3], box[2]]], legend=legend, palette={str(k): v for k, v in palette.items()},
                              source=source, note=note, bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), area_km2_by_class={str(k): round(float((arr == k).sum()) * ck, 1) for k in palette}))


def zone_raster(z, name, sub="floodplain_dyn"):
    p = BULK / sub / z / name if sub != "floodplain_dyn" else BULK / "floodplain_dyn" / f"{z}_connected_ceiling" / name
    with rasterio.open(p) as s:
        return s.read(1), s.transform, s.crs, s.nodata


def terrain_layers():
    src = "p95 rev 6 (seamless terrain-bed model, residual FABDEM class bias removed on FABDEM cells, union mosaic), connected_ceiling, closure kherson_paper1 (floodplain_dyn/<ZONE>_connected_ceiling)"
    per = {}
    for z in ZONES:
        zz = np.load(BULK / "floodplain_dyn" / f"{z}_connected_ceiling" / "daily_new.npz"); shp = tuple(int(v) for v in zz["shape"])
        with rasterio.open(BULK / "floodplain_dyn" / f"{z}_connected_ceiling" / "duration_days.tif") as s:
            tr, crs = s.transform, s.crs
        per[z] = (zz, shp, tr, crs)
    dates = [k for k in np.load(BULK / "floodplain_dyn" / "ZONE_2_KHERSON_DELTA_connected_ceiling" / "daily_new.npz").files if k.startswith("2023")]
    for d in dates:
        m = mosaic({z: (np.unpackbits(zz[d], count=shp[0] * shp[1]).reshape(shp).astype("u1"), tr, crs) for z, (zz, shp, tr, crs) in per.items()})
        write_png(m, OUTD / "terrain" / "daily" / f"{d}.png", {1: HEX["terrain"]}, {"1": "terrain-reconstructed new inundation"}, f"terrain_daily_{d}", "terrain_daily", src)
    for name, bins, labels, lid in [("duration_days.tif", [1, 4, 8, 15, 999], ["1–3 d", "4–7 d", "8–14 d", "≥ 15 d"], "terrain_duration"),
                                    ("max_depth_m.tif", [0.001, 0.5, 1, 2, 4, 99], ["< 0.5 m", "0.5–1 m", "1–2 m", "2–4 m", "> 4 m"], "terrain_max_depth"),
                                    ("depth_2023-06-08_m.tif", [0.001, 0.5, 1, 2, 4, 99], ["< 0.5 m", "0.5–1 m", "1–2 m", "2–4 m", "> 4 m"], "terrain_depth_20230608")]:
        pz = {}
        for z in ZONES:
            a, tr, crs, nd = zone_raster(z, name); a = a.astype("f4"); a[a == nd] = np.nan if nd is not None else a
            c = np.zeros(a.shape, "u1")
            for k in range(len(bins) - 1):
                c[(a >= bins[k]) & (a < bins[k + 1])] = k + 1
            pz[z] = (c, tr, crs)
        ramp = ["#dbe9f8", "#9cc0ea", "#5a93da", "#2a78d6", "#0b2a5c"][-(len(labels)):] if "depth" in name else ["#f4f8fc", "#eda100", "#e34948", "#4a3aa7"]
        write_png(mosaic(pz), OUTD / "terrain" / f"{lid}.png", {i + 1: ramp[i] for i in range(len(labels))}, {str(i + 1): l for i, l in enumerate(labels)}, lid, "terrain_summary", src)


SUPPORT = {1: ("direct (nearest SWOT node <= 3 km)", "#0b2a5c"), 2: ("extrapolated (3-10 km)", "#5a93da"), 3: ("weak (> 10 km)", "#eda100"),
           4: ("cross-river (Inhulets valley, node of another river)", "#e34948"), 5: ("capped at the Kherson gauge", "#4a3aa7")}
GAUGES = [("Kherson 80805", 32.612026, 46.623750, "input (anchor of the water surface)"),
          ("Kalynivske 80575 (Inhulets)", 32 + 57 / 60 + 38 / 3600, 47 + 6 / 60 + 59 / 3600, "withheld: independent tributary validation site"),
          ("Mykolaiv 98027 (liman)", 31 + 58 / 60 + 19.46 / 3600, 46 + 59 / 60 + 3.75 / 3600, "withheld: independent validation of the western delta")]


def support_layers():
    """D-SUPPORT: the new inundation of every day coloured by the support class of its water surface (p95l support_class.tif
    x daily_new.npz), and the three river gauges with their roles."""
    src = "p95l support classes (distance of the nearest SWOT node; operational thresholds) x p95 rev 6 connected_ceiling daily new inundation"
    per = {}
    for z in ZONES:
        d = BULK / "floodplain_dyn" / f"{z}_connected_ceiling"
        with rasterio.open(d / "support_class.tif") as s:
            code, tr, crs = s.read(1), s.transform, s.crs
        zz = np.load(d / "daily_new.npz"); per[z] = (code, zz, tuple(int(v) for v in zz["shape"]), tr, crs)
    dates = [k for k in np.load(BULK / "floodplain_dyn" / "ZONE_2_KHERSON_DELTA_connected_ceiling" / "daily_new.npz").files if k.startswith("2023")]
    for dd in dates:
        m = mosaic({z: (np.where(np.unpackbits(zz[dd], count=shp[0] * shp[1]).reshape(shp).astype(bool), code, 0).astype("u1"), tr, crs) for z, (code, zz, shp, tr, crs) in per.items()})
        write_png(m, OUTD / "support" / "daily" / f"{dd}.png", {k: c for k, (_, c) in SUPPORT.items()}, {str(k): lab for k, (lab, _) in SUPPORT.items()}, f"support_daily_{dd}", "support_daily", src,
                  note="the full reconstruction stays the primary product; supported core = direct + extrapolated (T11k)")
    feats = [dict(type="Feature", properties=dict(name=nm, role=role, kind="gauge"), geometry=dict(type="Point", coordinates=[lon, lat])) for nm, lon, lat, role in GAUGES]
    (OUTD / "context").mkdir(parents=True, exist_ok=True); gp = OUTD / "context" / "gauges.geojson"
    gp.write_text(json.dumps(dict(type="FeatureCollection", features=feats)))
    MAN["layers"].append(dict(id="gauges", group="context", file=str(gp.relative_to(OUTD)), bounds=None, legend={}, source="UkrHMC hydrological yearbook 2023 station positions (station catalogues); roles per D-INHULETS",
                              bytes=gp.stat().st_size, sha256=hashlib.sha256(gp.read_bytes()).hexdigest()))


def s1_layers():
    for z, cache in S1CACHE.items():
        pass
    zz = {z: np.load(CFG.S1_CACHE / cache / "per_scene_water.npz", allow_pickle=True) for z, cache in S1CACHE.items()}
    dates = sorted({k[:10] for k in zz["ZONE_2_KHERSON_DELTA"].files if k.startswith("2023")})
    pre = {}
    for z, c in zz.items():
        shp = tuple(int(v) for v in c["shape"]); tr = from_origin(float(c["x0"]), float(c["y1"]), float(c["cell"]), float(c["cell"]))
        un = lambda k: np.unpackbits(c[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
        W = {}; V = {}
        for k in c.files:
            if k.startswith("2023"):
                d = k[:10]; W[d] = W.get(d, np.zeros(shp, bool)) | (un(k) & un("valid_" + k)); V[d] = V.get(d, np.zeros(shp, bool)) | un("valid_" + k)
        pre[z] = (W, V, tr, CRS.from_epsg(32636), W["2023-06-01"] | W["2023-06-02"])
    for d in dates:
        new = mosaic({z: ((W[d] & ~p).astype("u1"), tr, crs) for z, (W, V, tr, crs, p) in pre.items()})
        foot = mosaic({z: (V[d].astype("u1"), tr, crs) for z, (W, V, tr, crs, p) in pre.items()})
        write_png(new, OUTD / "s1" / f"{d}_new.png", {1: HEX["s1"]}, {"1": "S1 new dark water (not water on 06-01/02)"}, f"s1_new_{d}", "s1_daily", "p0v/p0w M3 per-scene masks (s1_zone_cache), 20 m")
        write_png(foot, OUTD / "s1" / f"{d}_footprint.png", {1: HEX["foot"]}, {"1": "S1 valid footprint"}, f"s1_footprint_{d}", "s1_footprint", "s1_zone_cache valid masks")


def frame_layers():
    import json as _j
    def frames_mosaic(fn):
        out = np.zeros((NY, NX), "u1")
        for f in ("B1", "B2"):
            a, tr = fn(f); g = to_grid(a, tr, CRS.from_epsg(32636)); out = np.where(g > 0, g, out)
        return out
    def pred(run, name):
        thr = _j.loads((REPO / "case_studies/kakhovka_2023/runs" / run / "validation_threshold.json").read_text())["threshold"]
        def fn(f):
            with rasterio.open(FR / f / "m6" / name) as s:
                q = s.read(1); return ((q != 65535) & (q / 1e4 >= thr)).astype("u1"), s.transform
        return fn, thr
    fn, thr = pred("U2b_B1B2_v003A", "U2b_v003A_score.tif"); write_png(frames_mosaic(fn), OUTD / "unet" / "U2b_v003A.png", {1: HEX["unet"]}, {"1": f"U2b (v003_A) predicted flood, score ≥ {thr}"}, "unet_U2b_v003A", "unet", "runs/U2b_B1B2_v003A", "agreement with weak labels; persistent-water concept")
    fn, thr = pred("U2_B1B2_v1", "U2_score.tif"); write_png(frames_mosaic(fn), OUTD / "unet" / "U2_v1.png", {1: HEX["unet2"]}, {"1": f"U2 (v002) predicted flood, score ≥ {thr}"}, "unet_U2_v1", "unet", "runs/U2_B1B2_v1", "agreement with weak labels")
    for arm, col in (("U2b", HEX["unet"]), ("U2", HEX["unet2"])):                   # review F09/F10: the arms on the corrected labels (first seed)
        if (REPO / "case_studies/kakhovka_2023/runs" / f"{arm}_B1B2_v004" / "validation_threshold.json").exists():
            fn, thr = pred(f"{arm}_B1B2_v004", f"{arm}_v004_score.tif")
            write_png(frames_mosaic(fn), OUTD / "unet" / f"{arm}_v004.png", {1: col}, {"1": f"{arm} (v004) predicted flood, score ≥ {thr}"}, f"unet_{arm}_v004", "unet",
                      f"runs/{arm}_B1B2_v004", "agreement with weak labels v004 (M2 without TRACE, out-of-fold threshold); persistent-water concept")
    def lab(f):
        with rasterio.open(FR / f / "m6_labels_v003_A.tif") as s:
            o = s.read(1); c = np.zeros(o.shape, "u1"); c[o == 0] = 1; c[o == 1] = 2; c[o == 2] = 3; c[o == 255] = 4; return c, s.transform
    write_png(frames_mosaic(lab), OUTD / "labels" / "v003A.png", {1: "#efece6", 2: "#2a78d6", 3: "#b9c7d6", 4: "#f7f5f0"}, {"1": "LAND", "2": "EVENT_FLOOD", "3": "REFERENCE_WATER", "4": "UNKNOWN"}, "labels_v003A", "labels", "m6_labels_v003_A (FROZEN)", "weak reference labels")
    def lab4(f):
        with rasterio.open(FR / f / "m6_labels_v004.tif") as s:
            o = s.read(1); c = np.zeros(o.shape, "u1"); c[o == 0] = 1; c[o == 1] = 2; c[o == 2] = 3; c[o == 255] = 4; return c, s.transform
    if (FR / "B1" / "m6_labels_v004.tif").exists():
        write_png(frames_mosaic(lab4), OUTD / "labels" / "v004.png", {1: "#efece6", 2: "#2a78d6", 3: "#b9c7d6", 4: "#f7f5f0"}, {"1": "LAND", "2": "EVENT_FLOOD", "3": "REFERENCE_WATER", "4": "UNKNOWN"},
                  "labels_v004", "labels", "frames10/<F>/m6_labels_v004.tif", "weak labels v004: the v003_A rule on the M2 without TRACE (review F09/F10)")
    def rf(f):
        with rasterio.open(FR / f / "p73_rf20_rev2" / "surface_class_20m.tif") as s:            # review F08: the rev-2 refit
            c = s.read(1).astype("u1"); c[c == 255] = 0; return c, s.transform
    write_png(frames_mosaic(rf), OUTD / "rf" / "p73.png", {1: "#5b9bd5", 2: "#eda100", 3: "#b5d33d", 4: "#1b7f3b", 5: "#8fbc8f", 6: "#1baf7a", 7: "#7d3c98", 8: "#e8d8a0", 9: "#95a5a6", 10: "#d8dbdd"},
              {"1": "WATER", "2": "CROPLAND", "3": "GRASS_LOW_VEGETATION", "4": "FOREST", "5": "SHRUB", "6": "WETLAND_REED", "7": "BUILT_UP", "8": "BARE_SAND", "9": "OTHER", "10": "UNCERTAIN"}, "rf_p73", "rf", "p73 RF20 rev 2 (global blocks, overlap owned by B2; review F08)", "context, agreement with WorldCover")


def context_layers():
    import importlib.util
    from pyproj import Transformer
    from floodstate_eo.spatial import canonical_grid as CG
    tf = Transformer.from_crs("EPSG:32636", "EPSG:4326", always_xy=True)
    def ring(coords):
        return [[float(x), float(y)] for x, y in zip(*tf.transform([c[0] for c in coords], [c[1] for c in coords]))]
    feats = []
    for f in ("B1", "B2"):
        F = CG.frame_grid(f); t = F["transform"]; x0, y1 = t.c, t.f; x1, y0 = x0 + 10 * F["nx"], y1 - 10 * F["ny"]
        feats.append(dict(type="Feature", properties=dict(name=f"frame {f}", kind="frame"), geometry=dict(type="Polygon", coordinates=[ring([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])])))
    s = importlib.util.spec_from_file_location("p92", REPO / "case_studies/kakhovka_2023/workflows/m6/p92_flood_area_dam_to_liman.py"); P92 = importlib.util.module_from_spec(s); s.loader.exec_module(P92)
    for nm, (x0, y0, x1, y1) in P92.CUT_RECTS.items():
        y1 = min(y1, 5225000.0); feats.append(dict(type="Feature", properties=dict(name=nm, kind="cut_rect"), geometry=dict(type="Polygon", coordinates=[ring([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])])))
    for nm, lon, lat in (("Kherson gauge 80805", 32.612026, 46.623750), ("Kakhovka dam", 33.3667, 46.7783)):
        feats.append(dict(type="Feature", properties=dict(name=nm, kind="point"), geometry=dict(type="Point", coordinates=[lon, lat])))
    (OUTD / "context").mkdir(parents=True, exist_ok=True)
    (OUTD / "context" / "frames_and_points.geojson").write_text(json.dumps(dict(type="FeatureCollection", features=feats)))
    gj = Path(CFG._SWOT_DNIPRO_SIBLING) / "data/processed/domains/below_dam_floodplain_utm.geojson"
    if gj.exists():
        from shapely.geometry import shape, mapping
        from shapely.ops import transform as stf
        g = json.loads(gj.read_text()); out = []
        for ft in g["features"]:
            geom = shape(ft["geometry"]).simplify(60); geom = stf(lambda x, y, z=None: tf.transform(x, y), geom)
            out.append(dict(type="Feature", properties=dict(name="p42 terrain-eligible floodplain", kind="floodplain"), geometry=mapping(geom)))
        (OUTD / "context" / "p42_floodplain.geojson").write_text(json.dumps(dict(type="FeatureCollection", features=out)))
    for p in (q for q in (OUTD / "context").glob("*.geojson") if q.stem != "reservoir_pool"):     # reservoir_pool: registered by reservoir_layers
        MAN["layers"].append(dict(id=p.stem, group="context", file=str(p.relative_to(OUTD)), bounds=None, legend={}, source="own work (frame grids, p42 CUT_RECTS, p42 domain simplified 60 m)", bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()))


RES_GROUPS = ("reservoir_model", "reservoir_s1", "reservoir_s2_class", "reservoir_s2_water", "reservoir_s2_index")


def reservoir_layers():
    """p95h products (model / S1 / S2) -> classed overlays on the reservoir box RBOX; pool outline -> context/reservoir_pool.geojson."""
    import importlib.util
    import pandas as pd
    from affine import Affine
    s = importlib.util.spec_from_file_location("p95h", REPO / "case_studies/kakhovka_2023/workflows/m6/p95h_reservoir_maps.py"); H = importlib.util.module_from_spec(s); s.loader.exec_module(H)
    from rasterio import features
    RM = BULK / "reservoir_maps"; utm = CRS.from_epsg(32636); rd = OUTD / "reservoir"
    zone = CFG.load_utm("reservoir_full_pool_prebreach").buffer(1000.0)       # S1/S2 shown on the pool + 1 km only: the S1 VH rule is not a land classifier
    clip = lambda tr, shp: features.rasterize([(zone.__geo_interface__, 1)], out_shape=shp, transform=tr, fill=0, dtype="uint8").astype(bool)
    put =lambda a, tr, path, pal, leg, lid, grp, src, note="": write_png(to_grid(a, tr, utm, box=RBOX), rd / path, pal, leg, lid, grp, src, note, box=RBOX)
    # ---- model ----
    src = "p95h MODEL: p95f sloped daily surface over the 50 m seamless DEM inside the pre-breach pool (terrain-reconstructed)"
    z = np.load(RM / "model" / "wet_daily.npz"); shp = tuple(int(v) for v in z["shape"]); mtr = Affine(*z["transform"])
    un = lambda k: np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
    ref = un(str(H.REF_DAY.date()))
    for d in sorted(k for k in z.files if k.startswith("2023") and k >= "2023-05-31"):
        w = un(d); c = np.zeros(shp, "u1"); c[w] = 1; c[ref & ~w] = 2
        put(c, mtr, f"model/{d}.png", {1: "#1b6ca8", 2: "#d9a441"}, {"1": "pool water (model)", "2": "bed exposed since 06-05 (model)"}, f"reservoir_model_{d}", "reservoir_model", src)
    with rasterio.open(RM / "model" / "exposed_day.tif") as f:
        e = f.read(1); etr = f.transform
    c = np.zeros(e.shape, "u1")
    for k, (lo, hi) in enumerate([(6, 6), (7, 7), (8, 8), (9, 10), (11, 13)], 1):
        c[(e >= lo) & (e <= hi)] = k
    c[e == 255] = 6
    put(c, etr, "exposed_day.png", {1: "#7d1d1d", 2: "#c7522a", 3: "#e08214", 4: "#eda100", 5: "#f2d98a", 6: "#1b6ca8"},
        {"1": "exposed 06-06", "2": "exposed 06-07", "3": "exposed 06-08", "4": "exposed 06-09–10", "5": "exposed 06-11–13", "6": "still wet on 06-13"},
        "reservoir_exposed_day", "reservoir_model", src, "day on which a cell wet on 06-05 first falls dry under the modelled surface")
    # ---- water depth in the pool (p95m, decision D-DEPTH): classed, the full pool and the drawdown ----
    dsrc = "p95m: p95f sloped daily surface minus the 50 m seamless terrain-bed model, wet pool cells (terrain-reconstructed; Fig10)"
    dbins = [(0.0, 2.0), (2.0, 5.0), (5.0, 10.0), (10.0, 15.0), (15.0, 99.0)]; dleg = {"1": "< 2 m", "2": "2–5 m", "3": "5–10 m", "4": "10–15 m", "5": "> 15 m"}
    dpal = {1: "#dbe9f8", 2: "#9cc0ea", 3: "#5a93da", 4: "#2a78d6", 5: "#0b2a5c"}
    for d in ("2023-06-05", "2023-06-07", "2023-06-09", "2023-06-13"):
        f = RM / "model" / f"depth_{d}.tif"
        if not f.exists():
            continue
        with rasterio.open(f) as g:
            a = g.read(1); dtr = g.transform
        c = np.zeros(a.shape, "u1")
        for k, (lo, hi) in enumerate(dbins, 1):
            c[(a > lo) & (a <= hi)] = k
        put(c, dtr, f"model/depth_{d}.png", dpal, dleg, f"reservoir_depth_{d}", "reservoir_model", dsrc, "water depth in the pool (m); terrain-reconstructed, not observed")
    # ---- S1 ----
    T = pd.read_csv(CFG.TABLES / "p95h_reservoir_maps.csv"); s1d = T[(T.source == "S1") & (T.mapped == True)].date.tolist()   # noqa: E712
    src = "p95h S1: VH dB < per-date Otsu (all covered cells), 20 m, s1_zone_cache/ZONE_1_reservoir_corrected"
    r0 = np.load(RM / "s1" / "2023-06-01.npz"); sshp = tuple(int(v) for v in r0["shape"]); str_ = Affine(*r0["transform"])
    un1 = lambda z_, k: np.unpackbits(z_[k], count=sshp[0] * sshp[1]).reshape(sshp).astype(bool)
    dark0 = un1(r0, "water"); spool = H.pool_on(str_, sshp); sclip = clip(str_, sshp)
    for d in s1d:
        z1 = np.load(RM / "s1" / f"{d}.npz"); w, o = un1(z1, "water"), un1(z1, "observed")
        c = np.zeros(sshp, "u1"); c[w] = 1; c[o & ~w & dark0] = 2; c[spool & ~o] = 3; c[~sclip] = 0
        put(c, str_, f"s1/{d}.png", {1: "#1b6ca8", 2: "#d9a441", 3: "#c3c2b7"}, {"1": "S1 dark surface (open water or smooth wet mud)", "2": "dark on 06-01, not dark now", "3": "pool not observed"},
            f"reservoir_s1_{d}", "reservoir_s1", src, f"VH threshold {float(z1['threshold_db']):.2f} dB; not observed is not dry")
    # ---- S2 ----
    src = "SWOT-DNIPRO p25 zone_spectral ZONE_1 (FROZEN, 20 m): k10e class, water3, 7 indices; p15 ZONE_1_s2_crosscheck water"
    ztr, zshp = H.s2_grid(); zclip = clip(ztr, zshp); nt = "pool + 1 km; transparent = not observed"
    for d in H.S2_DATES:
        with rasterio.open(H.S2DIR / f"{d}_class.tif") as f:
            cl = f.read(1); cl[~zclip] = 0
        put(cl, ztr, f"s2/{d}_class.png", {k: v[1] for k, v in H.K10E.items()}, {str(k): v[0] for k, v in H.K10E.items()}, f"reservoir_s2_class_{d}", "reservoir_s2_class", src, nt)
        with rasterio.open(H.S2DIR / f"{d}_water3.tif") as f:
            w3 = f.read(1)
        c = np.zeros(w3.shape, "u1"); c[w3 == 1] = 1; c[w3 == 0] = 2; c[~zclip] = 0
        put(c, ztr, f"s2/{d}_water.png", {1: "#1b6ca8", 2: "#efece6"}, {"1": "S2 water (NDWI>0 & MNDWI>0)", "2": "S2 observed, not water"}, f"reservoir_s2_water_{d}", "reservoir_s2_water", src, nt)
        with rasterio.open(H.S2DIR / f"{d}_indices.tif") as f:
            for i, nm in enumerate(H.INDEX_NAMES, 1):
                v = f.read(i).astype("f4"); v[(v == -32768) | ~zclip] = np.nan; v /= 1e4
                edges, labels, cols = H.INDEX_BINS[nm]
                put(H.classify_index(v, nm), ztr, f"s2/{d}_{nm}.png", {k + 1: cols[k] for k in range(len(labels))}, {str(k + 1): f"{nm} {lab}" for k, lab in enumerate(labels)},
                    f"reservoir_s2_{nm}_{d}", "reservoir_s2_index", src, "display classes only; " + nt)
    xtr = H.xc_transform(ztr); xclip = clip(xtr, zshp)
    for d in H.S2XC_DATES:
        z2 = np.load(H.S2XC / f"{d}.npz"); un2 = lambda k: np.unpackbits(z2[k], count=zshp[0] * zshp[1]).reshape(zshp).astype(bool)
        w, v = un2("water"), un2("valid"); c = np.zeros(zshp, "u1"); c[v & ~w] = 2; c[w] = 1; c[~xclip] = 0
        put(c, xtr, f"s2/{d}_water.png", {1: "#1b6ca8", 2: "#efece6"}, {"1": "S2 water (p15 crosscheck)", "2": "S2 observed, not water"}, f"reservoir_s2_water_{d}", "reservoir_s2_water", "p15 ZONE_1_s2_crosscheck (FROZEN)", nt)
    # ---- pool outline ----
    from pyproj import Transformer
    from shapely.geometry import mapping
    from shapely.ops import transform as stf
    tf = Transformer.from_crs("EPSG:32636", "EPSG:4326", always_xy=True)
    g = stf(lambda x, y, z=None: tf.transform(x, y), CFG.load_utm("reservoir_full_pool_prebreach").simplify(100))
    p = OUTD / "context" / "reservoir_pool.geojson"; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(type="FeatureCollection", features=[dict(type="Feature", properties=dict(name="Kakhovka pool before the breach", kind="reservoir"), geometry=mapping(g))])))
    MAN["layers"].append(dict(id=p.stem, group="context", file=str(p.relative_to(OUTD)), bounds=None, legend={}, source="reservoir_full_pool_prebreach (Kakhovka_SA_2.geojson), simplified 100 m",
                              bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--only", choices=["reservoir", "terrain", "support", "frames"], help="rebuild only the reservoir, terrain, support or frame (U-Net, labels, RF20) layers, keep the rest of the manifest")
    a = ap.parse_args(); t0 = time.time(); OUTD.mkdir(parents=True, exist_ok=True)
    if a.only == "terrain":                                               # e.g. after a new p95 run: keep every other layer, terrain first as before
        old = json.loads((OUTD / "manifest.json").read_text())
        kept = [l for l in old["layers"] if l["group"] not in ("terrain_daily", "terrain_summary")]
        MAN["layers"] = []; terrain_layers(); MAN["layers"] = MAN["layers"] + kept; print("terrain", round(time.time() - t0), flush=True)
    elif a.only == "support":                                             # support classes of the new inundation + the gauges (p95l)
        old = json.loads((OUTD / "manifest.json").read_text())
        MAN["layers"] = [l for l in old["layers"] if l["group"] != "support_daily" and l["id"] != "gauges"]
        support_layers(); print("support", round(time.time() - t0), flush=True)
    elif a.only == "frames":                                              # U-Net predictions, labels and RF20 (stage 2 of the review)
        old = json.loads((OUTD / "manifest.json").read_text())
        MAN["layers"] = [l for l in old["layers"] if l["group"] not in ("unet", "labels", "rf")]
        frame_layers(); print("frames", round(time.time() - t0), flush=True)
    elif a.only == "reservoir":
        old = json.loads((OUTD / "manifest.json").read_text())
        MAN["layers"] = [l for l in old["layers"] if l["group"] not in RES_GROUPS and l["id"] != "reservoir_pool"]
        reservoir_layers(); print("reservoir", round(time.time() - t0), flush=True)
    else:
        terrain_layers(); print("terrain", round(time.time() - t0), flush=True)
        support_layers(); print("support", round(time.time() - t0), flush=True)
        s1_layers(); print("s1", round(time.time() - t0), flush=True)
        frame_layers(); print("frames", round(time.time() - t0), flush=True)
        reservoir_layers(); print("reservoir", round(time.time() - t0), flush=True)
        context_layers()
    tr, ny, nx = box_grid(RBOX); MAN["reservoir_grid"] = dict(crs="EPSG:4326", dlon=DLON, dlat=DLAT, nx=nx, ny=ny, bounds=[[RBOX[1], RBOX[0]], [RBOX[3], RBOX[2]]])
    MAN["total_bytes"] = int(sum(l["bytes"] for l in MAN["layers"])); MAN["n_layers"] = len(MAN["layers"])
    MAN["licence_note"] = ("Terrain layers are rendered classed images derived from FABDEM v1.2 (Hawker et al. 2022, CC BY-NC-SA 4.0) via the seamless terrain-bed model; "
                           "provided for non-commercial use with attribution; no FABDEM-derived numeric raster is redistributed. Sentinel data: Copernicus. WorldCover 2021: CC BY 4.0.")
    (OUTD / "manifest.json").write_text(json.dumps(MAN, indent=1)); print(f"-> {OUTD}: {MAN['n_layers']} layers, {MAN['total_bytes'] / 1e6:.1f} MB ({round(time.time() - t0)} s)")


if __name__ == "__main__":
    main()
