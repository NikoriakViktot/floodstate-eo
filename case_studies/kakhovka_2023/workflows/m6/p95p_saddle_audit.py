# New in floodstate-eo, 2026-09-30 (maintainer: local terrain / bathymetry audit of a marginal component). STATUS: ACTIVE. Diagnostic only.
"""P95p -- local geodetic audit of the bottleneck ("saddle") through which a reconstructed component connects to the river network.

Question: is the sill that connects a component on the peak days real terrain, a FABDEM (vegetation-corrected Copernicus DEM)
artefact under forest, or a channel whose bed the terrain products do not see? Two axes are kept apart: the height of dry land
(FABDEM vs Copernicus DEM GLO-30 vs ICESat-2 ATL08 night ground) and the channel bed (the seamless terrain-bed model, p55).

--step profile (this repo's venv):
  1. the lowest path (minimax: the path from the pre-breach river network -- largest connected component of the pre-breach
     water map -- to the target cell whose highest cell is lowest; a priority flood, 8-neighbours) on three terrain surfaces:
     the seamless terrain-bed model with the residual FABDEM class bias removed (the model's terrain), the same without the
     bias correction, and Copernicus DEM GLO-30 on the FABDEM cells with the bed kept;
  2. the profile along the path: z of every surface, the bed where the model has one, WorldCover, the SWOT-derived water
     surface H_t of the requested days, the datum step FABDEM-raster(EVRF2019) - FABDEM-tile(EGM2008) that also moves GLO-30 (both
     are EGM2008) into the frame of the model;
  3. the saddle per surface and day: z_saddle, H_t(saddle), Delta_H = H_t - z_saddle (positive = connected in the nominal world);
  4. Delta_z = FABDEM - GLO-30 in the window by class (forest, open ground, the saddle strip, the shoreline strip): where the
     vegetation correction of FABDEM lowered the surface;
  window rasters for --step icesat under $BULK_ROOT/floodplain_dyn/_saddle_audit/<name>_*.tif.
--step icesat (SWOT-DNIPRO venv, as p95c): night ATL08 ground segments (p57.load_points, Paper-1 frame) inside the window:
  r_FAB = z_FABDEM - z_ICESat2 and r_COP = z_GLO30 - z_ICESat2 by class and within the saddle strip; points along the path.
--step figure: the profile with the surfaces, the bed, the water surfaces and the ICESat-2 points, plus a map of the path.

Outputs: <case_study>/tables/p95p_saddle_profile_<name>.csv, p95p_saddle_summary_<name>.csv, p95p_saddle_dz_classes_<name>.csv,
         p95p_saddle_icesat_<name>.csv, p95p_saddle_icesat_points_<name>.csv, p95p_saddle_path_<name>.geojson, p95p_saddle_manifest_<name>.json;
         <case_study>/figures/m6_v003A/p95p_saddle_<name>.png
"""
from __future__ import annotations

import argparse
import heapq
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject, transform as tf_transform

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = ROOT / "figures" / "m6_v003A"
CELL = 20.0
ZONE = "ZONE_4_DAM_TO_KHERSON_FLOODWAY"
WC_NAMES = {10: "trees", 20: "shrub", 30: "grass", 40: "cropland", 50: "built", 60: "bare_sparse", 80: "water", 90: "wetland"}
OPEN = (30, 40, 60)
STRIP_M = 200.0


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def nmad(x):
    x = np.asarray(x, "f8"); x = x[np.isfinite(x)]
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if len(x) else np.nan


def minimax_path(z, sources, target, limit=None):
    """Priority flood from `sources` over `z` (8-neighbours): for every reached cell the lowest possible highest elevation on a
    path from a source; stops when `target` is reached. Returns (saddle value, path as a list of (r, c) from source to target,
    the saddle cell). `limit`: cells with z > limit are never entered (pruning; None = no limit)."""
    ny, nx = z.shape; INF = np.inf
    best = np.full(z.shape, INF, "f8"); prev = np.full(z.shape, -1, "i8"); done = np.zeros(z.shape, bool)
    heap = []
    rr, cc = np.nonzero(sources)
    for r, c in zip(rr, cc):
        v = float(z[r, c])
        if np.isfinite(v):
            best[r, c] = v; heapq.heappush(heap, (v, int(r), int(c)))
    tr, tc = target
    while heap:
        v, r, c = heapq.heappop(heap)
        if done[r, c]:
            continue
        done[r, c] = True
        if (r, c) == (tr, tc):
            break
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r2, c2 = r + dr, c + dc
                if r2 < 0 or r2 >= ny or c2 < 0 or c2 >= nx or done[r2, c2]:
                    continue
                zz = z[r2, c2]
                if not np.isfinite(zz) or (limit is not None and zz > limit):
                    continue
                nv = v if v > zz else float(zz)
                if nv < best[r2, c2]:
                    best[r2, c2] = nv; prev[r2, c2] = r * nx + c; heapq.heappush(heap, (nv, r2, c2))
    if not np.isfinite(best[tr, tc]):
        return np.nan, [], None
    path = []; cur = tr * nx + tc
    while cur >= 0:
        path.append((cur // nx, cur % nx)); cur = prev[cur // nx, cur % nx] if prev[cur // nx, cur % nx] != cur else -1
    path = path[::-1]
    zs = np.array([z[r, c] for r, c in path]); k = int(np.argmax(zs))
    return float(best[tr, tc]), path, path[k]


def window_grid(G, x0, x1, y0, y1):
    tr = G["transform"]; c0 = int((x0 - tr.c) / CELL); c1 = int(np.ceil((x1 - tr.c) / CELL)); r0 = int((tr.f - y1) / CELL); r1 = int(np.ceil((tr.f - y0) / CELL))
    c0, r0 = max(c0, 0), max(r0, 0); c1, r1 = min(c1, G["nx"]), min(r1, G["ny"])
    from rasterio.transform import from_origin
    return (slice(r0, r1), slice(c0, c1)), dict(transform=from_origin(tr.c + c0 * CELL, tr.f - r0 * CELL, CELL, CELL), ny=r1 - r0, nx=c1 - c0, crs=G["crs"])


def onto(path, Gw, resampling=Resampling.bilinear, nodata_to_nan=True):
    """Any raster (any CRS) resampled onto the window grid."""
    with rasterio.open(path) as s:
        a = s.read(1).astype("f4"); nd = s.nodata
        if nodata_to_nan and nd is not None:
            a[a == nd] = np.nan
        d = np.full((Gw["ny"], Gw["nx"]), np.nan, "f4")
        reproject(a, d, src_transform=s.transform, src_crs=s.crs, dst_transform=Gw["transform"], dst_crs=Gw["crs"], resampling=resampling, src_nodata=np.nan, dst_nodata=np.nan)
    return d


def copdem_mosaic(Gw, tiles):
    out = np.full((Gw["ny"], Gw["nx"]), np.nan, "f4")
    for t in tiles:
        d = onto(t, Gw); m = np.isfinite(d) & ~np.isfinite(out); out[m] = d[m]
    return out


def step_profile(a):
    from floodstate_eo import _kakhovka_legacy_config as CFG
    from floodstate_eo.terrain.connectivity import largest_component
    P95 = _ld("p95", HERE / "p95_hand_daily_inundation.py"); P = P95.load_p92()
    t0 = time.time(); L = P95.zone_layers(ZONE, P, with_s1=False); G = L["G"]
    x, y = tf_transform("EPSG:4326", CFG.CRS_METRIC, [a.lon], [a.lat]); x, y = float(x[0]), float(y[0])
    win, Gw = window_grid(G, x - a.window_km[0] * 1e3, x + a.window_km[0] * 1e3, y - a.window_km[1] * 1e3, y + a.window_km[1] * 1e3)
    dem, dem_raw, src, wc = L["dem"][win], L["dem_raw"][win], L["src"][win], L["wc"][win]
    seed_river = largest_component(L["seed"])[win]; is_fab = np.isin(src, P95.FABDEM_SOURCES); is_bed = np.isin(src, P95.BED_SOURCES)
    print(f"window {Gw['ny']} x {Gw['nx']} cells; river-network cells {int(seed_river.sum())}; {round(time.time() - t0)} s", flush=True)
    # FABDEM tile (EGM2008) and Copernicus DEM GLO-30 (EGM2008) on the window grid; the datum step from the seamless raster itself
    fab_egm = onto(CFG.BULK_ROOT / "fabdem" / "fabdem_project_aoi.tif", Gw)
    tiles = sorted((CFG.BULK_ROOT / "copdem").glob("Copernicus_DSM_COG_10_*_DEM.tif"))
    cop_egm = copdem_mosaic(Gw, tiles) if tiles else np.full(dem.shape, np.nan, "f4")
    d_step = (dem_raw - fab_egm)[is_fab & np.isfinite(fab_egm)]
    shift = float(np.nanmedian(d_step)); shift_nmad = nmad(d_step)
    cop_evrf = cop_egm + shift; fab_tile_evrf = fab_egm + shift
    z_cop_seam = np.where(is_fab & np.isfinite(cop_evrf), cop_evrf, dem)                       # GLO-30 on the land cells, the bed kept
    # water surface of the requested days on the window
    W, dxm, dym, nodes = P95.load_engine(); Zw = W.prepare(dict(G=Gw)); H = {d: W.field(Zw, d) for d in a.days}
    riv = np.array(W.river); up = lambda v: np.asarray(v).reshape(Zw["shape_c"])[np.ix_(Zw["ri"], Zw["ci"])]
    node_river = riv[up(Zw["i1"])]; node_km = up(Zw["d1"]) / 1e3
    # target cell and the minimax path on each surface
    tr = Gw["transform"]; tc, trow = int((x - tr.c) / CELL), int((tr.f - y) / CELL); target = (trow, tc)
    hmax = float(np.nanmax([np.nanmax(H[d]) for d in a.days])) + 2.0
    surfaces = {"model_terrain_bias_removed": dem, "fabdem_uncorrected": dem_raw, "glo30_on_land_bed_kept": z_cop_seam}
    rows, paths = [], {}
    for name, z in surfaces.items():
        t1 = time.time(); zs, path, sad = minimax_path(z, seed_river, target, limit=hmax)
        paths[name] = path
        for d in a.days:
            hs = float(H[d][sad]) if sad is not None else np.nan
            rows.append(dict(surface=name, day=d, z_saddle_m=round(zs, 3) if np.isfinite(zs) else np.nan, H_saddle_m=round(hs, 3) if np.isfinite(hs) else np.nan,
                             delta_H_saddle_m=round(hs - zs, 3) if np.isfinite(zs) and np.isfinite(hs) else np.nan,
                             saddle_x=round(tr.c + (sad[1] + 0.5) * CELL, 1) if sad else np.nan, saddle_y=round(tr.f - (sad[0] + 0.5) * CELL, 1) if sad else np.nan,
                             saddle_wc=WC_NAMES.get(int(wc[sad]), str(int(wc[sad]))) if sad else "", saddle_source={1: "bed", 2: "bed", 5: "bed", 3: "FABDEM", 4: "FABDEM_taper"}.get(int(src[sad]), "?") if sad else "",
                             saddle_node_river=str(node_river[sad]) if sad else "", saddle_node_km=round(float(node_km[sad]), 1) if sad else np.nan,
                             path_length_km=round(len(path) * CELL / 1e3, 2), target_z_m=round(float(z[target]), 2), target_H_m=round(float(H[d][target]), 2),
                             seconds=round(time.time() - t1, 1)))
        print(f"  {name}: saddle {zs:.2f} m, path {len(path)} cells, {round(time.time() - t1)} s", flush=True)
    S = pd.DataFrame(rows); S["datum_step_fabdem_raster_minus_tile_m"] = round(shift, 3); S["datum_step_nmad_m"] = round(shift_nmad, 3)
    S.to_csv(ROOT / "tables" / f"p95p_saddle_summary_{a.name}.csv", index=False); print(S.to_string(index=False))
    # profile along the model's path
    path = paths["model_terrain_bias_removed"]; prof = []; s_ = 0.0; prev = None
    for r, c in path:
        if prev is not None:
            s_ += CELL * float(np.hypot(r - prev[0], c - prev[1]))
        prev = (r, c); px, py = tr.c + (c + 0.5) * CELL, tr.f - (r + 0.5) * CELL
        prof.append(dict(s_m=round(s_, 1), x=round(px, 1), y=round(py, 1), z_model_m=round(float(dem[r, c]), 3), z_fabdem_uncorrected_m=round(float(dem_raw[r, c]), 3),
                         z_fabdem_tile_m=round(float(fab_tile_evrf[r, c]), 3) if np.isfinite(fab_tile_evrf[r, c]) else np.nan, z_glo30_m=round(float(cop_evrf[r, c]), 3) if np.isfinite(cop_evrf[r, c]) else np.nan,
                         z_bed_m=round(float(dem[r, c]), 3) if is_bed[r, c] else np.nan, source=int(src[r, c]), worldcover=WC_NAMES.get(int(wc[r, c]), str(int(wc[r, c]))),
                         river_network=bool(seed_river[r, c]), nearest_node_river=str(node_river[r, c]), nearest_node_km=round(float(node_km[r, c]), 1),
                         **{f"H_{d}_m": round(float(H[d][r, c]), 3) for d in a.days}))
    Pf = pd.DataFrame(prof); Pf.to_csv(ROOT / "tables" / f"p95p_saddle_profile_{a.name}.csv", index=False)
    lon, lat = tf_transform(CFG.CRS_METRIC, "EPSG:4326", Pf.x.values, Pf.y.values)
    (ROOT / "tables" / f"p95p_saddle_path_{a.name}.geojson").write_text(json.dumps(dict(type="FeatureCollection", features=[
        dict(type="Feature", properties=dict(name=a.name, surface="model_terrain_bias_removed"), geometry=dict(type="LineString", coordinates=[[round(float(o), 6), round(float(t), 6)] for o, t in zip(lon, lat)]))])))
    # Delta z = FABDEM - GLO-30 in the window by class
    pm = np.zeros(dem.shape, bool)
    for r, c in path:
        pm[r, c] = True
    from scipy import ndimage
    d_path = ndimage.distance_transform_edt(~pm) * CELL; d_shore = ndimage.distance_transform_edt(~seed_river) * CELL
    dz = fab_tile_evrf - cop_evrf; ok = is_fab & np.isfinite(dz)
    classes = {"forest": ok & (wc == 10), "open_ground": ok & np.isin(wc, OPEN), "wetland": ok & (wc == 90), "saddle_strip_200m": ok & (d_path <= STRIP_M), "shoreline_strip_200m": ok & (d_shore <= STRIP_M), "all_fabdem_cells": ok}
    C = pd.DataFrame([dict(cls=k, n_cells=int(m.sum()), dz_fabdem_minus_glo30_median_m=round(float(np.median(dz[m])), 3) if m.any() else np.nan, dz_nmad_m=round(nmad(dz[m]), 3),
                           dz_p10_m=round(float(np.percentile(dz[m], 10)), 3) if m.any() else np.nan, dz_p90_m=round(float(np.percentile(dz[m], 90)), 3) if m.any() else np.nan,
                           bias_removed_by_model_median_m=round(float(np.median((dem_raw - dem)[m])), 3) if m.any() else np.nan) for k, m in classes.items()])
    C.to_csv(ROOT / "tables" / f"p95p_saddle_dz_classes_{a.name}.csv", index=False); print(C.to_string(index=False))
    # window rasters for the ICESat-2 step
    od = CFG.BULK_ROOT / "floodplain_dyn" / "_saddle_audit"; od.mkdir(parents=True, exist_ok=True)
    prof_ = dict(driver="GTiff", height=Gw["ny"], width=Gw["nx"], count=1, crs=Gw["crs"], transform=Gw["transform"], compress="deflate")
    for nm, arr, dt in (("model", dem, "float32"), ("fabdem_raster", dem_raw, "float32"), ("fabdem_tile", fab_tile_evrf, "float32"), ("glo30", cop_evrf, "float32"),
                        ("wc", wc, "uint8"), ("src", src, "uint8"), ("dist_path", d_path.astype("f4"), "float32"), ("dist_shore", d_shore.astype("f4"), "float32")):
        with rasterio.open(od / f"{a.name}_{nm}.tif", "w", dtype=dt, nodata=(0 if dt == "uint8" else -9999.0), **prof_) as o:
            o.write((np.nan_to_num(arr, nan=-9999.0) if dt == "float32" else arr).astype(dt), 1)
    man = dict(producer="p95p_saddle_audit.py --step profile", name=a.name, target_lonlat=[a.lon, a.lat], window_km=a.window_km, days=a.days, zone=ZONE,
               datum_step_fabdem_raster_minus_tile_m=round(shift, 4), datum_step_nmad_m=round(shift_nmad, 4), copdem_tiles=[t.name for t in tiles],
               copdem_source="Copernicus DEM GLO-30 (ESA / Airbus, 2021 release), AWS open data bucket copernicus-dem-30m; EGM2008 heights moved to EVRF2019 with the same step as the FABDEM tile",
               fabdem_tile="fabdem/fabdem_project_aoi.tif (EGM2008)", surfaces=list(surfaces), river_network="largest connected component of the pre-breach water map (zone grid)",
               minimax="priority flood, 8-neighbours, cells above H_max + 2 m never entered")
    (ROOT / "tables" / f"p95p_saddle_manifest_{a.name}.json").write_text(json.dumps(man, indent=1, default=str))
    print("-> tables/p95p_saddle_*", a.name, round(time.time() - t0), "s")


def step_icesat(a):
    """SWOT-DNIPRO venv: night ATL08 ground segments (p57.load_points) in the window, residuals of FABDEM and GLO-30 by class."""
    sd = Path.home() / "repo/SWOT-DNIPRO"; sys.path.insert(0, str(sd / "src")); sys.path.insert(0, str(sd / "scripts"))
    P57 = _ld("p57", sd / "scripts/p57_dem_accuracy_night.py")
    PF = _ld("paper1_frame", HERE / "paper1_frame.py")
    from swot_dnipro import config as SCFG
    P, c = P57.load_points(); P = P[~P.in_former_pool].copy(); P["H_ice"] = PF.icesat_ground_to_paper1(P.H_ice.values)
    od = Path(SCFG.BULK_ROOT) / "floodplain_dyn" / "_saddle_audit"
    with rasterio.open(od / f"{a.name}_model.tif") as s:
        b = s.bounds
    P = P[(P.x >= b.left) & (P.x <= b.right) & (P.y >= b.bottom) & (P.y <= b.top)].copy(); print("night ground points in the window:", len(P), flush=True)
    smp = lambda nm: P57.sample(od / f"{a.name}_{nm}.tif", P.x.values, P.y.values)
    for nm in ("model", "fabdem_raster", "fabdem_tile", "glo30", "dist_path", "dist_shore"):
        v = smp(nm); v = np.where(v == -9999.0, np.nan, v); P[nm] = v
    P["wc"] = smp("wc"); P["src"] = smp("src")
    P["r_model"] = P.model - P.H_ice; P["r_fabdem"] = P.fabdem_raster - P.H_ice; P["r_glo30"] = P.glo30 - P.H_ice
    land = np.isin(P.src, (3, 4)) & (P.wc != 80)
    classes = {"forest": land & (P.wc == 10), "open_ground": land & np.isin(P.wc, OPEN), "wetland": land & (P.wc == 90), "saddle_strip_200m": land & (P.dist_path <= STRIP_M),
               "shoreline_strip_200m": land & (P.dist_shore <= STRIP_M), "all_land": land}
    rows = []
    for k, m in classes.items():
        q = P[m]
        rows.append(dict(cls=k, n_points=int(len(q)), n_dates=int(q.date.nunique()) if len(q) else 0,
                         r_model_median_m=round(float(q.r_model.median()), 3) if len(q) else np.nan, r_model_nmad_m=round(nmad(q.r_model), 3),
                         r_fabdem_median_m=round(float(q.r_fabdem.median()), 3) if len(q) else np.nan, r_fabdem_nmad_m=round(nmad(q.r_fabdem), 3),
                         r_glo30_median_m=round(float(q.r_glo30.median()), 3) if len(q) else np.nan, r_glo30_nmad_m=round(nmad(q.r_glo30), 3)))
    R = pd.DataFrame(rows); R.to_csv(HERE.parents[1] / "tables" / f"p95p_saddle_icesat_{a.name}.csv", index=False); print(R.to_string(index=False))
    pts = P[P.dist_path <= 100.0][["date", "x", "y", "H_ice", "model", "fabdem_raster", "glo30", "wc", "src", "dist_path"]].copy()
    pts.to_csv(HERE.parents[1] / "tables" / f"p95p_saddle_icesat_points_{a.name}.csv", index=False); print("points within 100 m of the path:", len(pts))


def step_crosstest(a):
    """The saddles are path-dependent: evaluate every surface along every path (the sill of surface X along the path found on
    surface Y), the overlap of the routes, and -- along the fixed model path -- the raw and corrected terrain, the class correction
    and the ICESat-2 ground per 1 km bin and per land-cover class (was the class correction locally too strong?)."""
    from floodstate_eo import _kakhovka_legacy_config as CFG
    from floodstate_eo.terrain.connectivity import largest_component
    P95 = _ld("p95", HERE / "p95_hand_daily_inundation.py"); P = P95.load_p92(); L = P95.zone_layers(ZONE, P, with_s1=False); G = L["G"]
    x, y = tf_transform("EPSG:4326", CFG.CRS_METRIC, [a.lon], [a.lat]); x, y = float(x[0]), float(y[0])
    win, Gw = window_grid(G, x - a.window_km[0] * 1e3, x + a.window_km[0] * 1e3, y - a.window_km[1] * 1e3, y + a.window_km[1] * 1e3)
    dem, dem_raw, src, wc = L["dem"][win], L["dem_raw"][win], L["src"][win], L["wc"][win]
    seed_river = largest_component(L["seed"])[win]; is_fab = np.isin(src, P95.FABDEM_SOURCES)
    fab_egm = onto(CFG.BULK_ROOT / "fabdem" / "fabdem_project_aoi.tif", Gw); tiles = sorted((CFG.BULK_ROOT / "copdem").glob("Copernicus_DSM_COG_10_*_DEM.tif"))
    cop = copdem_mosaic(Gw, tiles); shift = float(np.nanmedian((dem_raw - fab_egm)[is_fab & np.isfinite(fab_egm)])); cop_evrf = cop + shift
    z_cop = np.where(is_fab & np.isfinite(cop_evrf), cop_evrf, dem)
    W, dxm, dym, nodes = P95.load_engine(); Zw = W.prepare(dict(G=Gw)); H = {d: W.field(Zw, d) for d in a.days}
    tr = Gw["transform"]; target = (int((tr.f - y) / CELL), int((x - tr.c) / CELL)); hmax = float(np.nanmax([np.nanmax(H[d]) for d in a.days])) + 2.0
    surfaces = {"model": dem, "raw": dem_raw, "glo30": z_cop}; paths = {}
    for nm, z in surfaces.items():
        zs, path, sad = minimax_path(z, seed_river, target, limit=hmax); paths[nm] = path
    rows = []
    for pn, path in paths.items():
        if not path:
            continue
        cells = np.array(path); rr, cc = cells[:, 0], cells[:, 1]
        row = dict(path_found_on=pn, n_cells=len(path), length_km=round(len(path) * CELL / 1e3, 2))
        for sn, z in surfaces.items():
            v = z[rr, cc]; k = int(np.nanargmax(v)); row[f"sill_of_{sn}_along_path_m"] = round(float(v[k]), 2); row[f"sill_of_{sn}_at_km"] = round(k * CELL / 1e3, 1)
        for d in a.days:
            row[f"H_{d}_at_model_sill_m"] = round(float(H[d][rr, cc][int(np.nanargmax(dem[rr, cc]))]), 2)
        rows.append(row)
    sets = {k: set(map(tuple, v)) for k, v in paths.items() if v}
    if "model" in sets and "raw" in sets:
        j = len(sets["model"] & sets["raw"]) / max(len(sets["model"] | sets["raw"]), 1)
        for r in rows:
            r["route_overlap_model_vs_raw_jaccard"] = round(j, 3)
    X = pd.DataFrame(rows); X.to_csv(ROOT / "tables" / f"p95p_saddle_crosstest_{a.name}.csv", index=False); pd.set_option("display.width", 250); print(X.to_string(index=False))
    # along the FIXED model path: raw, corrected, the correction and the ICESat-2 ground per 1 km bin and per class
    path = paths["model"]; cells = np.array(path); rr, cc = cells[:, 0], cells[:, 1]; s_m = np.concatenate([[0.0], np.cumsum(CELL * np.hypot(np.diff(rr), np.diff(cc)))])
    ip = ROOT / "tables" / f"p95p_saddle_icesat_points_{a.name}.csv"; pts = pd.read_csv(ip) if ip.exists() else None
    prof = pd.DataFrame(dict(s_km=s_m / 1e3, z_raw=dem_raw[rr, cc], z_model=dem[rr, cc], corr_m=(dem - dem_raw)[rr, cc], wc=wc[rr, cc], src=src[rr, cc]))
    if pts is not None and len(pts):
        px = tr.c + (cc + 0.5) * CELL; py = tr.f - (rr + 0.5) * CELL
        idx = [int(np.argmin(np.hypot(px - x_, py - y_))) for x_, y_ in zip(pts.x, pts.y)]
        pts = pts.assign(s_km=s_m[idx] / 1e3, z_model_path=dem[rr, cc][idx], z_raw_path=dem_raw[rr, cc][idx], wc_path=wc[rr, cc][idx])
        pts["r_model"] = pts.z_model_path - pts.H_ice; pts["r_raw"] = pts.z_raw_path - pts.H_ice
    prof["bin_km"] = np.floor(prof.s_km).astype(int); out = []
    for b, g in prof.groupby("bin_km"):
        q = pts[(pts.s_km >= b) & (pts.s_km < b + 1)] if pts is not None else pd.DataFrame()
        out.append(dict(bin_km=int(b), n_cells=len(g), z_raw_median_m=round(float(g.z_raw.median()), 2), z_model_median_m=round(float(g.z_model.median()), 2), correction_median_m=round(float(g.corr_m.median()), 2),
                        wc_mode=WC_NAMES.get(int(g.wc.mode().iloc[0]), "?"), share_forest=round(float((g.wc == 10).mean()), 2), share_wetland=round(float((g.wc == 90).mean()), 2), share_bed=round(float(np.isin(g.src, (1, 2, 5)).mean()), 2),
                        n_icesat=int(len(q)), icesat_ground_median_m=round(float(q.H_ice.median()), 2) if len(q) else np.nan,
                        r_model_median_m=round(float(q.r_model.median()), 2) if len(q) else np.nan, r_raw_median_m=round(float(q.r_raw.median()), 2) if len(q) else np.nan,
                        r_model_nmad_m=round(nmad(q.r_model), 2) if len(q) else np.nan, **{f"H_{d}_median_m": round(float(H[d][rr, cc][g.index.values].mean()), 2) for d in a.days}))
    B = pd.DataFrame(out); B.to_csv(ROOT / "tables" / f"p95p_saddle_path_bins_{a.name}.csv", index=False); print(B.to_string(index=False))
    if pts is not None and len(pts):
        C = pts.groupby("wc_path").agg(n=("H_ice", "size"), r_model_median_m=("r_model", "median"), r_raw_median_m=("r_raw", "median"), r_model_nmad_m=("r_model", nmad)).reset_index()
        C["wc_path"] = C.wc_path.map(lambda v: WC_NAMES.get(int(v), str(int(v)))); C = C.round(2); C.to_csv(ROOT / "tables" / f"p95p_saddle_path_classes_{a.name}.csv", index=False); print(C.to_string(index=False))


def step_figure(a):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    T = ROOT / "tables"; Pf = pd.read_csv(T / f"p95p_saddle_profile_{a.name}.csv"); S = pd.read_csv(T / f"p95p_saddle_summary_{a.name}.csv")
    ip = T / f"p95p_saddle_icesat_points_{a.name}.csv"; pts = pd.read_csv(ip) if ip.exists() else None
    fig, ax = plt.subplots(figsize=(9.5, 4.6), constrained_layout=True); s_km = Pf.s_m / 1e3
    ax.plot(s_km, Pf.z_model_m, color="#1b1b1b", lw=1.6, label="model terrain (seamless terrain-bed, FABDEM class bias removed)")
    ax.plot(s_km, Pf.z_fabdem_uncorrected_m, color="#777", lw=1.0, ls="--", label="FABDEM as delivered (EVRF2019)")
    ax.plot(s_km, Pf.z_glo30_m, color="#c2185b", lw=1.1, label="Copernicus DEM GLO-30 (moved to EVRF2019 with the FABDEM datum step)")
    ax.plot(s_km, Pf.z_bed_m, color="#8b5a2b", lw=2.2, label="channel bed (model, source 1/2/5)")
    for d, col in zip([c for c in Pf.columns if c.startswith("H_")], ("#2a78d6", "#7fb3e6", "#eda100")):
        ax.plot(s_km, Pf[d], color=col, lw=1.3, ls="-.", label=f"water surface {d[2:12]} (SWOT nodes + gauge)")
    if pts is not None and len(pts):
        prof_xy = Pf[["x", "y"]].values
        sp = [float(Pf.s_m.iloc[int(np.argmin(np.hypot(prof_xy[:, 0] - x, prof_xy[:, 1] - y)))]) / 1e3 for x, y in zip(pts.x, pts.y)]
        ax.scatter(sp, pts.H_ice, s=10, color="#1baf7a", zorder=5, label=f"ICESat-2 ATL08 night ground within 100 m of the path (n = {len(pts)})")
    wcn = Pf.worldcover.values; y0 = float(np.nanmin(Pf[["z_model_m", "z_bed_m"]].min())) - 0.5
    for k in range(len(Pf) - 1):
        col = {"trees": "#2e7d32", "wetland": "#00897b", "grass": "#c0ca33", "cropland": "#f9a825", "water": "#1e88e5", "built": "#8d6e63"}.get(wcn[k], "#bdbdbd")
        ax.plot([s_km[k], s_km[k + 1]], [y0, y0], color=col, lw=6, solid_capstyle="butt")
    m = S[S.surface == "model_terrain_bias_removed"]
    txt = " | ".join(f"{r.day[5:]}: ΔH_saddle {r.delta_H_saddle_m:+.2f} m" for r in m.itertuples())
    ax.set_title(f"Lowest path from the river network to {a.name} ({Pf.s_m.max() / 1e3:.1f} km): saddle {m.z_saddle_m.iloc[0]:.2f} m on the model terrain; {txt}", fontsize=8.5, loc="left")
    ax.set_xlabel("distance along the path from the river network, km"); ax.set_ylabel("height, m EVRF2019"); ax.legend(fontsize=6.5, loc="upper right"); ax.grid(alpha=0.3)
    ax.text(0.01, 0.02, "bar: WorldCover along the path (green forest, teal wetland, lime grass, orange cropland, blue water)", transform=ax.transAxes, fontsize=6.5, color="#555")
    FIG.mkdir(parents=True, exist_ok=True); fig.savefig(FIG / f"p95p_saddle_{a.name}.png", dpi=150); plt.close(fig); print("->", FIG / f"p95p_saddle_{a.name}.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", choices=["profile", "icesat", "figure", "crosstest"], default="profile")
    ap.add_argument("--name", default="kozachi_laheri_lowland"); ap.add_argument("--lon", type=float, default=33.12); ap.add_argument("--lat", type=float, default=46.665)
    ap.add_argument("--window-km", type=float, nargs=2, default=[14.0, 13.0], help="half-sizes E-W and N-S of the window around the target")
    ap.add_argument("--days", nargs="*", default=["2023-06-07", "2023-06-08"])
    a = ap.parse_args()
    {"profile": step_profile, "icesat": step_icesat, "figure": step_figure, "crosstest": step_crosstest}[a.step](a)


if __name__ == "__main__":
    main()
