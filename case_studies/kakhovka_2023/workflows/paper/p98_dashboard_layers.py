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
  context/*.geojson                               frames, cut rectangles, p42 floodplain (simplified), gauge and dam
  manifest.json                                   id, file, bounds [[S, W], [N, E]], legend, source, sha256, bytes
"""
from __future__ import annotations
import hashlib, json, time
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
HEX = {"terrain": "#2a78d6", "s1": "#eb6834", "unet": "#4a3aa7", "unet2": "#8a7fd6", "foot": "#c3c2b7"}
MAN = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "grid": dict(crs="EPSG:4326", dlon=DLON, dlat=DLAT, nx=NX, ny=NY, bounds=[[BBOX[1], BBOX[0]], [BBOX[3], BBOX[2]]]), "layers": []}


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def to_grid(a, transform, crs, nodata=0):
    d = np.full((NY, NX), nodata, a.dtype)
    reproject(a, d, src_transform=transform, src_crs=crs, dst_transform=TR, dst_crs=CRS4326, resampling=Resampling.nearest, src_nodata=nodata, dst_nodata=nodata)
    return d


def mosaic(per_zone):
    """per_zone: zone -> (array uint8, transform, crs) on the zone grid; ZONE_2 painted last (owns overlap)."""
    out = np.zeros((NY, NX), "u1")
    for z in ("ZONE_4_DAM_TO_KHERSON_FLOODWAY", "ZONE_2_KHERSON_DELTA"):
        if z in per_zone:
            a, tr, crs = per_zone[z]; g = to_grid(a, tr, crs); out = np.where(g > 0, g, out)
    return out


def write_png(arr, path: Path, palette: dict, legend: dict, layer_id: str, group: str, source: str, note: str = ""):
    """arr uint8 classes (0 = transparent); palette code -> hex."""
    img = Image.fromarray(arr, "P"); pal = [0, 0, 0] * 256
    for k, h in palette.items():
        r, g, b = hexrgb(h); pal[3 * k:3 * k + 3] = [r, g, b]
    img.putpalette(pal); img.info["transparency"] = 0
    path.parent.mkdir(parents=True, exist_ok=True); img.save(path, optimize=True, transparency=0)
    MAN["layers"].append(dict(id=layer_id, group=group, file=str(path.relative_to(OUTD)), bounds=[[BBOX[1], BBOX[0]], [BBOX[3], BBOX[2]]], legend=legend, palette={str(k): v for k, v in palette.items()},
                              source=source, note=note, bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), area_km2_by_class={str(k): round(float((arr == k).sum()) * 0.0061, 1) for k in palette}))


def zone_raster(z, name, sub="floodplain_dyn"):
    p = BULK / sub / z / name if sub != "floodplain_dyn" else BULK / "floodplain_dyn" / f"{z}_connected_ceiling" / name
    with rasterio.open(p) as s:
        return s.read(1), s.transform, s.crs, s.nodata


def terrain_layers():
    src = "p95 rev 5 (DEM class-bias corrected), connected_ceiling, closure kherson_paper1 (floodplain_dyn/<ZONE>_connected_ceiling)"
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
    from floodstate_eo.spatial import canonical_grid as CG
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
    def lab(f):
        with rasterio.open(FR / f / "m6_labels_v003_A.tif") as s:
            o = s.read(1); c = np.zeros(o.shape, "u1"); c[o == 0] = 1; c[o == 1] = 2; c[o == 2] = 3; c[o == 255] = 4; return c, s.transform
    write_png(frames_mosaic(lab), OUTD / "labels" / "v003A.png", {1: "#efece6", 2: "#2a78d6", 3: "#b9c7d6", 4: "#f7f5f0"}, {"1": "LAND", "2": "EVENT_FLOOD", "3": "REFERENCE_WATER", "4": "UNKNOWN"}, "labels_v003A", "labels", "m6_labels_v003_A (FROZEN)", "weak reference labels")
    def rf(f):
        with rasterio.open(FR / f / "p73_rf20" / "surface_class_20m.tif") as s:
            c = s.read(1).astype("u1"); c[c == 255] = 0; return c, s.transform
    write_png(frames_mosaic(rf), OUTD / "rf" / "p73.png", {1: "#5b9bd5", 2: "#eda100", 3: "#b5d33d", 4: "#1b7f3b", 5: "#8fbc8f", 6: "#1baf7a", 7: "#7d3c98", 8: "#e8d8a0", 9: "#95a5a6", 10: "#d8dbdd"},
              {"1": "WATER", "2": "CROPLAND", "3": "GRASS_LOW_VEGETATION", "4": "FOREST", "5": "SHRUB", "6": "WETLAND_REED", "7": "BUILT_UP", "8": "BARE_SAND", "9": "OTHER", "10": "UNCERTAIN"}, "rf_p73", "rf", "p73 RF20 (FROZEN)", "context, agreement with WorldCover")


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
    for p in (OUTD / "context").glob("*.geojson"):
        MAN["layers"].append(dict(id=p.stem, group="context", file=str(p.relative_to(OUTD)), bounds=None, legend={}, source="own work (frame grids, p42 CUT_RECTS, p42 domain simplified 60 m)", bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()))


def main():
    t0 = time.time(); OUTD.mkdir(parents=True, exist_ok=True)
    terrain_layers(); print("terrain", round(time.time() - t0), flush=True)
    s1_layers(); print("s1", round(time.time() - t0), flush=True)
    frame_layers(); print("frames", round(time.time() - t0), flush=True)
    context_layers()
    MAN["total_bytes"] = int(sum(l["bytes"] for l in MAN["layers"])); MAN["n_layers"] = len(MAN["layers"])
    MAN["licence_note"] = ("Terrain layers are rendered classed images derived from FABDEM v1.2 (Hawker et al. 2022, CC BY-NC-SA 4.0) via the seamless DEM; "
                           "provided for non-commercial use with attribution; no FABDEM-derived numeric raster is redistributed. Sentinel data: Copernicus. WorldCover 2021: CC BY 4.0.")
    (OUTD / "manifest.json").write_text(json.dumps(MAN, indent=1)); print(f"-> {OUTD}: {MAN['n_layers']} layers, {MAN['total_bytes'] / 1e6:.1f} MB ({round(time.time() - t0)} s)")


if __name__ == "__main__":
    main()
