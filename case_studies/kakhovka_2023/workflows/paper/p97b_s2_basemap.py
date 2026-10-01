# New in floodstate-eo, 2026-09-30 (maintainer: satellite basemap in the paper figures, not only in the dashboard). STATUS: ACTIVE.
"""P97b -- Sentinel-2 L2A true colour from the project's own archive on the 20 m zone grids of the reconstruction: the basemap
of Fig07 / FigS14 / FigS16 and an overlay of the dashboard (Copernicus attribution; no third-party tiles in the paper).

Scenes. The downstream reach spans the 100 km squares U (E 300-410 km), V (400-510) and W (500-610): the R107 orbit covers U and V,
the W squares (Kozachi Laheri - Krynky - dam, the left-bank terrace) need R064 or the R107 edge.
  2022-06-13 R107  T36TUS / TUT / TVS / TVT, cloud + shadow 2.0 / 2.5 / 6.2 / 3.7 % -- one year before the breach, the same season;
  2022-06-20 R064  T36TWS / TWT (0 % cloud over E 500-540 km) one week later for the W squares;
  2022-06-03 R107  T36TVS / TWS (2 %) fill the remaining cloud gaps.                                   -> the pre-breach basemap
  2023-06-18 R107  T36TUS / TUT / TVS / TVT / TWT, 7-14 % cloud -- twelve days after the breach (recession): the event panel of
              FigS16 (no T36TWS of that week in the archive: the south bank east of E 510 km below N 5200 km stays empty).
  (No cloud-free pre-breach 2023 scene of the downstream squares is in the archive: 2023-06-05 covers the reservoir only,
  2023-06-08 is 70 % cloud.)
Fixed stretch: reflectance 0.00-0.30 -> 0-255, gamma 0.9 (recorded in the manifest; never a per-image percentile).

Outputs: $BULK_ROOT/truecolour/<ZONE>_s2_<date>_20m.tif (uint8 RGB, LZW, nodata 0), <ZONE>_s2_<date>_filled.tif (which scene),
         <case_study>/tables/p97b_s2_basemap_manifest.json,
         apps/dashboard/data/context/s2_truecolour_2022-06-13.jpg (EPSG:4326 box of the dashboard, <= 1 MB).
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.warp import reproject

from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.io import optical_catalogue as OC
from floodstate_eo.optical import truecolour as TC
from floodstate_eo.terrain.mosaic import UnionGrid

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ROOT = HERE.parents[1]
OUT = CFG.BULK_ROOT / "truecolour"
DASH = REPO / "apps" / "dashboard" / "data" / "context"
ZONES = ("ZONE_4_DAM_TO_KHERSON_FLOODWAY", "ZONE_2_KHERSON_DELTA")
TILES = ("T36TUS", "T36TUT", "T36TVS", "T36TVT", "T36TWS", "T36TWT")
SCENES = {"2022-06-13": [("2022-06-13", TILES), ("2022-06-20", ("T36TWS", "T36TWT")), ("2022-06-03", ("T36TVS", "T36TWS"))],   # priority order
          "2023-06-18": [("2023-06-18", TILES)]}
STRETCH, GAMMA = (0.0, 0.30), 0.9
ATTRIBUTION = "Contains modified Copernicus Sentinel data {year}, processed by the authors (Sentinel-2 L2A, ESA)"
DLON, DLAT, BBOX = 0.001, 0.00072, (32.15, 46.35, 33.55, 47.15)                         # = p98 dashboard grid


def tile_of(p: Path) -> str:
    m = re.search(r"_(T36[A-Z]{3})_", p.name); return m.group(1) if m else ""


def scene_list(key):
    safes = OC.scan_safes(); zips = []
    for date, tiles in SCENES[key]:
        zips += [p for p in sorted(safes.get(date, [])) if tile_of(p) in tiles]
    if not zips:
        raise SystemExit(f"no SAFE archives for {key}")
    return zips


def zone_grid(zone):
    with rasterio.open(CFG.BULK_ROOT / "dem_seamless" / f"{zone}_dem_evrf2019_20m.tif") as s:
        return dict(transform=s.transform, ny=s.height, nx=s.width, crs=s.crs)


def write_tif(path, arr, G, nodata=0):
    count = arr.shape[0] if arr.ndim == 3 else 1
    with rasterio.open(path, "w", driver="GTiff", height=G["ny"], width=G["nx"], count=count, dtype="uint8", crs=G["crs"], transform=G["transform"],
                       nodata=nodata, compress="lzw", tiled=True, blockxsize=512, blockysize=512, photometric="RGB" if count == 3 else None) as o:
        o.write(arr if arr.ndim == 3 else arr[None])


def dashboard_jpeg(rgb_by_zone, grids, path, max_bytes=1_000_000):
    """The two zone mosaics composed (ZONE_2 owns the overlap) and warped to the dashboard's EPSG:4326 box; JPEG <= max_bytes."""
    from rasterio.transform import from_origin
    g = UnionGrid.from_members({z: (grids[z]["transform"], (grids[z]["ny"], grids[z]["nx"])) for z in ZONES})
    tr = from_origin(BBOX[0], BBOX[3], DLON, DLAT); ny = int(round((BBOX[3] - BBOX[1]) / DLAT)); nx = int(round((BBOX[2] - BBOX[0]) / DLON))
    out = np.zeros((3, ny, nx), "u1")
    for i in range(3):
        band = g.compose({z: rgb_by_zone[z][i] for z in ZONES}, 0, order=list(ZONES), dtype="u1")
        dst = np.zeros((ny, nx), "u1")
        reproject(source=band, destination=dst, src_transform=g.transform, src_crs=grids[ZONES[0]]["crs"], dst_transform=tr, dst_crs="EPSG:4326",
                  resampling=Resampling.bilinear, src_nodata=0, dst_nodata=0)
        out[i] = dst
    img = Image.fromarray(np.moveaxis(out, 0, -1), "RGB"); path.parent.mkdir(parents=True, exist_ok=True)
    for q in (85, 78, 70, 60):
        img.save(path, "JPEG", quality=q, optimize=True, progressive=True)
        if path.stat().st_size <= max_bytes:
            return q, path.stat().st_size
    return q, path.stat().st_size


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dates", nargs="*", default=list(SCENES)); ap.add_argument("--no-jpeg", action="store_true")
    a = ap.parse_args(); t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True)
    man = dict(producer="p97b_s2_basemap.py", stretch_reflectance=STRETCH, gamma=GAMMA, cloud_scl=list(TC.CLOUD_SCL), cell_m=20.0, runs={})
    grids = {z: zone_grid(z) for z in ZONES}; keep = {}
    for key in a.dates:
        zips = scene_list(key); year = key[:4]
        for z in ZONES:
            rgb, filled = TC.truecolour_mosaic(zips, grids[z], cell=20.0, stretch=STRETCH, gamma=GAMMA)
            write_tif(OUT / f"{z}_s2_{key}_20m.tif", rgb, grids[z]); write_tif(OUT / f"{z}_s2_{key}_filled.tif", filled, grids[z])
            n = filled.size; shares = {zp.name: round(float((filled == k).sum()) / n, 4) for k, zp in enumerate(zips, 1)}
            man["runs"][f"{z}:{key}"] = dict(zone=z, date=key, scenes=[zp.name for zp in zips], fill_share_by_scene=shares, no_data_share=round(float((filled == 0).sum()) / n, 4),
                                             attribution=ATTRIBUTION.format(year=year), output=str(OUT / f"{z}_s2_{key}_20m.tif"))
            keep[(z, key)] = rgb
            print(z, key, "no-data share", man["runs"][f"{z}:{key}"]["no_data_share"], "fill", shares, round(time.time() - t0), "s", flush=True)
    if "2022-06-13" in a.dates and not a.no_jpeg:
        q, nbytes = dashboard_jpeg({z: keep[(z, "2022-06-13")] for z in ZONES}, grids, DASH / "s2_truecolour_2022-06-13.jpg")
        man["dashboard_jpeg"] = dict(file="apps/dashboard/data/context/s2_truecolour_2022-06-13.jpg", quality=q, bytes=nbytes, bounds=[[BBOX[1], BBOX[0]], [BBOX[3], BBOX[2]]],
                                     attribution=ATTRIBUTION.format(year=2022), licence="Copernicus Sentinel data: free, full and open access (Copernicus data policy); attribution required")
        print("dashboard JPEG", q, nbytes, "bytes")
    (ROOT / "tables" / "p97b_s2_basemap_manifest.json").write_text(json.dumps(man, indent=1, default=str))
    print("->", OUT, "and tables/p97b_s2_basemap_manifest.json", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
