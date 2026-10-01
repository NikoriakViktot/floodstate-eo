# New in floodstate-eo, 2026-10-01 (maintainer: "there must be a full flood mask"). STATUS: ACTIVE. Packages existing p95 / p95e /
# Sentinel-1 products; nothing is re-derived and no number of the paper changes.
"""P103 -- the full flood mask: the envelope of the reconstructed inundation over the whole event, one raster per zone and a
mosaic, with the Monte-Carlo and the Sentinel-1 views next to it -- what a hydraulic model needs as its wetted-extent input (the
maximum extent, the pre-breach water, the days and the depth), read from the frozen products of the primary run.

flood_envelope_class.tif (uint8):
  0  never water in the domain (or outside it)
  1  pre-breach water (optically observed, Sentinel-2 water frequency >= 20 %)
  2  normally wet (the model-only part of the normal regime: below the surface under the same rule on a pre-breach day)
  3  new inundation in the nominal run on >= 1 day of 26 May .. 10 July (the envelope of terrain_daily)
  4  new inundation in the Monte-Carlo median world on >= 1 evaluated day (P >= 0.5) but never in the nominal run
  5  marginal: 0.05 <= P < 0.5 on some evaluated day, never nominal and never in the median world
The total water envelope is classes 1-4; the new-inundation envelope is 3-4 (3 alone = nominal run). first_day, last_day,
duration_days and max_depth_m of the nominal run already sit next to it (floodplain_dyn/<ZONE>_connected_ceiling);
flood_envelope_pmax.tif = max over the evaluated days of P(new inundation) x 100 (255 = not evaluated).
s1_observed_envelope.tif (uint8): 1 new dark water on >= 1 event date (6-30 June; not dark on 1-2 June), 2 observed on >= 1
event date and never dark, 3 dark already on 1-2 June (pre-breach dark surface: water or dry sand), 0 never observed.
Mosaic (ZONE_2 owns the overlap) and GeoJSON polygons (EPSG:4326) of the total and of the new-inundation envelope in
$BULK/floodplain_dyn/_envelope/; areas per zone and reporting region in tables/p103_flood_envelope.csv; figures/p103_flood_envelope.png.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio import features
from rasterio.crs import CRS
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from floodstate_eo import _kakhovka_legacy_config as CFG

REPO = Path(__file__).resolve().parents[4]
BULK = CFG.BULK_ROOT; DYN = BULK / "floodplain_dyn"; OUT = DYN / "_envelope"; SFX = "_connected_ceiling"
ZONES = ["ZONE_4_DAM_TO_KHERSON_FLOODWAY", "ZONE_2_KHERSON_DELTA"]                     # painted in this order: ZONE_2 owns the overlap
S1CACHE = {"ZONE_4_DAM_TO_KHERSON_FLOODWAY": "ZONE_4_FLOODWAY_june2023_s32", "ZONE_2_KHERSON_DELTA": "ZONE_2_KHERSON_DELTA_flood_june2023"}
CELL, CELL_KM2, UTM = 20.0, 0.0004, CRS.from_epsg(32636)
EVENT_FROM, EVENT_TO = "2023-06-06", "2023-06-30"
CLS = {0: ("never water", "#ffffff"), 1: ("pre-breach water (optical)", "#0b2a5c"), 2: ("normally wet (model, same rule before the breach)", "#5a93da"),
       3: ("new inundation, nominal run (>= 1 day)", "#2a78d6"), 4: ("new inundation, Monte-Carlo median world only (P >= 0.5)", "#7fb3e6"),
       5: ("marginal (0.05 <= P < 0.5)", "#f5d58a")}
S1C = {0: ("never observed", "#ffffff"), 1: ("new dark water on >= 1 event date", "#eb6834"), 2: ("observed, never dark", "#efece6"), 3: ("dark already on 1-2 June", "#f5b79b")}
CONTEXT = REPO / "apps" / "dashboard" / "data" / "context" / "frames_and_points.geojson"


def grid(z):
    with rasterio.open(DYN / f"{z}{SFX}" / "duration_days.tif") as s:
        return s.transform, s.shape


def zone_products(z):
    """(class, pmax, s1) on the zone grid of the primary run."""
    tr, shp = grid(z); n = shp[0] * shp[1]
    zz = np.load(DYN / f"{z}{SFX}" / "daily_new.npz"); un = lambda k: np.unpackbits(zz[k], count=n).reshape(shp).astype(bool)
    base, nw = un("baseline"), un("normally_wet"); env = np.zeros(shp, bool); dates = sorted(k for k in zz.files if k.startswith("2023"))
    for d in dates:
        env |= un(d)
    pmax = np.full(shp, np.nan, "f4"); files = sorted((DYN / f"{z}{SFX}").glob("p95e_cellprob_*.tif"))
    for f in files:
        with rasterio.open(f) as s:
            c = s.read(1).astype("f4"); nd = s.nodata; nd_ = c == nd if nd is not None else np.zeros(shp, bool); p = c / float(s.tags().get("n_draws", 1000))
        p[nd_] = np.nan; pmax = np.fmax(pmax, p)
    cls = np.zeros(shp, "u1"); cls[base & ~nw] = 1; cls[nw] = 2; cls[env & (cls == 0)] = 3
    cls[(pmax >= 0.5) & (cls == 0)] = 4; cls[(pmax >= 0.05) & (cls == 0)] = 5
    pm = np.full(shp, 255, "u1"); ok = np.isfinite(pmax); pm[ok] = np.round(pmax[ok] * 100)
    # Sentinel-1: per-scene masks of the zone cache (20 m); onto the zone grid where the cache grid differs
    c = np.load(CFG.S1_CACHE / S1CACHE[z] / "per_scene_water.npz", allow_pickle=True); cshp = tuple(int(v) for v in c["shape"])
    ctr = from_origin(float(c["x0"]), float(c["y1"]), float(c["cell"]), float(c["cell"])); unc = lambda k: np.unpackbits(c[k], count=cshp[0] * cshp[1]).reshape(cshp).astype(bool)
    W, V = {}, {}
    for k in c.files:
        if k.startswith("2023"):
            d = k[:10]; W[d] = W.get(d, np.zeros(cshp, bool)) | (unc(k) & unc("valid_" + k)); V[d] = V.get(d, np.zeros(cshp, bool)) | unc("valid_" + k)
    pre = W["2023-06-01"] | W["2023-06-02"]; ev = [d for d in W if EVENT_FROM <= d <= EVENT_TO]
    dark = np.zeros(cshp, bool); obs = np.zeros(cshp, bool)
    for d in ev:
        dark |= W[d]; obs |= V[d]
    s1 = np.zeros(cshp, "u1"); s1[obs & ~dark] = 2; s1[dark & ~pre] = 1; s1[pre] = 3
    if (ctr, cshp) != (tr, shp):
        dst = np.zeros(shp, "u1"); reproject(s1, dst, src_transform=ctr, src_crs=UTM, dst_transform=tr, dst_crs=UTM, resampling=Resampling.nearest, src_nodata=0, dst_nodata=0); s1 = dst
    return cls, pm, s1, tr, shp, dict(n_daily=len(dates), first=dates[0], last=dates[-1], n_cellprob=len(files), s1_event_dates=ev)


def write(path, a, tr, nodata, tags):
    prof = dict(driver="GTiff", height=a.shape[0], width=a.shape[1], count=1, dtype="uint8", crs=UTM, transform=tr, compress="deflate", tiled=True, blockxsize=512, blockysize=512, nodata=nodata)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **prof) as o:
        o.write(a, 1); o.update_tags(**tags)


def regions(tr, shp):
    """Reporting regions of the dashboard context (EPSG:4326 polygons) rasterised on the mosaic grid; the corridor = everything outside the Inhulets valley."""
    from pyproj import Transformer
    from shapely.geometry import shape
    from shapely.ops import transform as stf
    if not CONTEXT.exists():
        return {}
    tf = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True); out = {}
    for f in json.loads(CONTEXT.read_text())["features"]:
        if f["properties"].get("kind") == "reporting_region":
            g = stf(lambda x, y, z=None: tf.transform(x, y), shape(f["geometry"]))
            out[f["properties"]["name"]] = features.rasterize([(g.__geo_interface__, 1)], out_shape=shp, transform=tr, fill=0, dtype="uint8").astype(bool)
    if "inhulets_valley" in out:
        out = {"DNIPRO_CORRIDOR": ~out["inhulets_valley"], "INHULETS_VALLEY_rect": out["inhulets_valley"], **{k: v for k, v in out.items() if k != "inhulets_valley"}}
    return out


def polygons(a, tr, keep, path, name, simplify_m=10.0):
    from pyproj import Transformer
    from shapely.geometry import shape, mapping
    from shapely.ops import transform as stf
    tf = Transformer.from_crs("EPSG:32636", "EPSG:4326", always_xy=True); m = np.isin(a, keep).astype("u1"); feats = []
    for geom, v in features.shapes(m, mask=m.astype(bool), transform=tr, connectivity=8):
        g = shape(geom).simplify(simplify_m); km2 = g.area / 1e6
        if km2 < 0.004:                                                             # fewer than ten cells: not a polygon a model would use
            continue
        feats.append(dict(type="Feature", properties=dict(name=name, area_km2=round(km2, 4)), geometry=mapping(stf(lambda x, y, z=None: tf.transform(x, y), g))))
    path.write_text(json.dumps(dict(type="FeatureCollection", name=name, features=feats)))
    return len(feats), round(float(m.sum()) * CELL_KM2, 1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--no-figure", action="store_true"); a = ap.parse_args(); t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True); per = {}; rows = []; meta = {}
    for z in ZONES:
        cls, pm, s1, tr, shp, m = zone_products(z); per[z] = (cls, pm, s1, tr, shp); meta[z] = m
        tags = dict(producer="p103_flood_envelope.py", zone=z, source=f"p95 primary run ({SFX[1:]}), p95e cellprob, Sentinel-1 per-scene masks", classes=json.dumps({k: v[0] for k, v in CLS.items()}),
                    days=f"{m['first']} .. {m['last']} ({m['n_daily']} days)", vertical_datum="EVRF2019", meaning="envelope of the reconstructed inundation; terrain_reconstructed, not an observation")
        write(DYN / f"{z}{SFX}" / "flood_envelope_class.tif", cls, tr, 0, tags)
        write(DYN / f"{z}{SFX}" / "flood_envelope_pmax.tif", pm, tr, 255, {**tags, "meaning": f"max over {m['n_cellprob']} evaluated days of P(new inundation) x 100; 255 = not evaluated"})
        write(DYN / f"{z}{SFX}" / "s1_observed_envelope.tif", s1, tr, 0, {**tags, "classes": json.dumps({k: v[0] for k, v in S1C.items()}), "meaning": f"Sentinel-1 dark water over the event dates {m['s1_event_dates'][0]} .. {m['s1_event_dates'][-1]}; observed_S1; not observed is not dry"})
        for name, arr, key in (("flood_envelope", cls, CLS), ("s1_observed_envelope", s1, S1C)):
            r = dict(region=z, product=name, **{f"{key[k][0]}_km2": round(float((arr == k).sum()) * CELL_KM2, 1) for k in key if k > 0})
            if name == "flood_envelope":
                r.update(total_water_envelope_km2=round(float(np.isin(cls, (1, 2, 3, 4)).sum()) * CELL_KM2, 1), new_envelope_nominal_km2=round(float((cls == 3).sum()) * CELL_KM2, 1),
                         new_envelope_median_world_km2=round(float(np.isin(cls, (3, 4)).sum()) * CELL_KM2, 1))
            rows.append(r)
        print(f"{z}: envelope classes on {shp}, {m['n_daily']} days, {m['n_cellprob']} cellprob days, S1 {len(m['s1_event_dates'])} event dates ({time.time() - t0:.0f} s)", flush=True)
    # ---- mosaic on the union of the two zone grids (one lattice, asserted); ZONE_2 painted last ----
    trs = [per[z][3] for z in ZONES]; assert all(abs((t.c - trs[0].c) % CELL) < 1e-6 and abs((t.f - trs[0].f) % CELL) < 1e-6 for t in trs), "zone grids on different lattices"
    x0 = min(t.c for t in trs); y1 = max(t.f for t in trs); x1 = max(t.c + CELL * per[z][4][1] for z, t in zip(ZONES, trs)); y0 = min(t.f - CELL * per[z][4][0] for z, t in zip(ZONES, trs))
    ny, nx = int(round((y1 - y0) / CELL)), int(round((x1 - x0) / CELL)); mtr = from_origin(x0, y1, CELL, CELL)
    mos = {k: np.full((ny, nx), 255 if k == "pmax" else 0, "u1") for k in ("cls", "pmax", "s1")}
    for z in ZONES:
        cls, pm, s1, tr, shp = per[z]; r0 = int(round((y1 - tr.f) / CELL)); c0 = int(round((tr.c - x0) / CELL))
        for k, arr in (("cls", cls), ("pmax", pm), ("s1", s1)):
            view = mos[k][r0:r0 + shp[0], c0:c0 + shp[1]]; own = arr != (255 if k == "pmax" else 0); view[own] = arr[own]
    tags = dict(producer="p103_flood_envelope.py", zones=",".join(ZONES), overlap="ZONE_2 owns", vertical_datum="EVRF2019", classes=json.dumps({k: v[0] for k, v in CLS.items()}))
    write(OUT / "flood_envelope_class_20m.tif", mos["cls"], mtr, 0, {**tags, "meaning": "envelope of the reconstructed inundation (total water = classes 1-4; new inundation = 3-4)"})
    write(OUT / "flood_envelope_pmax_20m.tif", mos["pmax"], mtr, 255, {**tags, "meaning": "max over the evaluated days of P(new inundation) x 100; 255 = not evaluated"})
    write(OUT / "s1_observed_envelope_20m.tif", mos["s1"], mtr, 0, {**tags, "classes": json.dumps({k: v[0] for k, v in S1C.items()}), "meaning": "Sentinel-1 dark water over the event dates; not observed is not dry"})
    R = {"MOSAIC_ALL": np.ones((ny, nx), bool), **regions(mtr, (ny, nx))}
    for rn, rm in R.items():
        c = mos["cls"][rm]; s = mos["s1"][rm]
        rows.append(dict(region=rn, product="flood_envelope", **{f"{CLS[k][0]}_km2": round(float((c == k).sum()) * CELL_KM2, 1) for k in CLS if k > 0},
                         total_water_envelope_km2=round(float(np.isin(c, (1, 2, 3, 4)).sum()) * CELL_KM2, 1), new_envelope_nominal_km2=round(float((c == 3).sum()) * CELL_KM2, 1),
                         new_envelope_median_world_km2=round(float(np.isin(c, (3, 4)).sum()) * CELL_KM2, 1)))
        rows.append(dict(region=rn, product="s1_observed_envelope", **{f"{S1C[k][0]}_km2": round(float((s == k).sum()) * CELL_KM2, 1) for k in S1C if k > 0}))
    n1, a1 = polygons(mos["cls"], mtr, (1, 2, 3, 4), OUT / "total_water_envelope.geojson", "total water envelope (pre-breach water + normally wet + new inundation, nominal run and MC median world)")
    n2, a2 = polygons(mos["cls"], mtr, (3, 4), OUT / "new_inundation_envelope.geojson", "new-inundation envelope (nominal run + MC median world)")
    T = pd.DataFrame(rows); T.to_csv(CFG.TABLES / "p103_flood_envelope.csv", index=False)
    man = dict(product="p103_flood_envelope", created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), zones=meta, mosaic=dict(x0=x0, y1=y1, ny=ny, nx=nx, cell_m=CELL, crs="EPSG:32636"),
               classes={k: v[0] for k, v in CLS.items()}, s1_classes={k: v[0] for k, v in S1C.items()},
               outputs=dict(per_zone=[str(DYN / f"{z}{SFX}" / n) for z in ZONES for n in ("flood_envelope_class.tif", "flood_envelope_pmax.tif", "s1_observed_envelope.tif")],
                            mosaic=[str(OUT / n) for n in ("flood_envelope_class_20m.tif", "flood_envelope_pmax_20m.tif", "s1_observed_envelope_20m.tif")],
                            polygons=dict(total_water_envelope=dict(file=str(OUT / "total_water_envelope.geojson"), n=n1, km2=a1), new_inundation_envelope=dict(file=str(OUT / "new_inundation_envelope.geojson"), n=n2, km2=a2))),
               companions="first_day.tif, last_day.tif, duration_days.tif, max_depth_m.tif of the nominal run (floodplain_dyn/<ZONE>_connected_ceiling)")
    (CFG.TABLES / "p103_flood_envelope_manifest.json").write_text(json.dumps(man, indent=1, default=str))
    print(T[T["product"] == "flood_envelope"][["region", "total_water_envelope_km2", "new_envelope_nominal_km2", "new_envelope_median_world_km2"]].to_string(index=False), flush=True)
    if not a.no_figure:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap, BoundaryNorm
        from matplotlib.patches import Patch
        f = max(1, int(np.ceil(max(ny, nx) / 1800))); fig, axs = plt.subplots(1, 2, figsize=(15, 7.5))
        for ax, key, leg, title in ((axs[0], "cls", CLS, "the full flood mask: envelope of the reconstructed inundation (26 May .. 10 July 2023)"),
                                    (axs[1], "s1", S1C, f"Sentinel-1 dark water over the event dates ({EVENT_FROM} .. {EVENT_TO})")):
            cm = ListedColormap([leg[k][1] for k in sorted(leg)]); nm = BoundaryNorm(np.arange(-0.5, len(leg) + 0.5, 1), cm.N)
            ax.imshow(mos[key][::f, ::f], cmap=cm, norm=nm, interpolation="nearest", extent=(x0 / 1e3, x1 / 1e3, y0 / 1e3, y1 / 1e3))
            ax.set_title(title, fontsize=9, loc="left"); ax.set_xlabel("UTM 36N easting, km"); ax.set_ylabel("northing, km")
            ax.legend(handles=[Patch(color=leg[k][1], label=leg[k][0]) for k in sorted(leg) if k > 0], loc="lower left", fontsize=7, frameon=True)
        fig.suptitle("p103: the envelope of the terrain-connectivity reconstruction (terrain_reconstructed) and what Sentinel-1 saw (observed_S1); ZONE_2 owns the overlap", fontsize=9)
        fig.tight_layout(); fig.savefig(CFG.FIG / "p103_flood_envelope.png", dpi=120); plt.close(fig)
    print(f"-> {OUT}, tables/p103_flood_envelope.csv, figures/p103_flood_envelope.png ({time.time() - t0:.0f} s)", flush=True)


if __name__ == "__main__":
    main()
