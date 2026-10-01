# New in floodstate-eo, 2026-10-01 (maintainer: the Surface-context page needs the satellite images themselves -- Sentinel-2 true colour
# for every possible date). STATUS: ACTIVE. A viewing product: not an input of any result.
"""p97c -- Sentinel-2 L2A true colour of EVERY archive date that covers the lower Dnipro (tiles T36TUS/TUT/TVS/TVT/TWS/TWT), rendered
straight onto the dashboard's EPSG:4326 box (p98 BBOX, 0.001 x 0.00072 deg, 1400 x 1111 px) as one JPEG per date, clouds left as
photographed (cloud_scl=(0,)), nodata light grey. The clear share of the box comes from the SCL cloud mask of the same read (the
default CLOUD_SCL of truecolour.py). Dates with less than MIN_CLEAR clear are listed but not rendered (pure cloud).

Outputs: apps/dashboard/data/s2rgb/<date>.jpg (quality ladder until <= MAX_BYTES) and apps/dashboard/data/s2rgb/manifest.json
(date -> tiles, orbits, clear_share, file, bytes, sha256, quality). p98 context_layers registers the JPEGs as group s2_truecolour.
Attribution: contains modified Copernicus Sentinel data <year>, processed by the authors.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import multiprocessing as mp
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUT = REPO / "apps" / "dashboard" / "data" / "s2rgb"
LD_TILES = ("T36TUS", "T36TUT", "T36TVS", "T36TVT", "T36TWS", "T36TWT")
MIN_CLEAR = 0.02
MAX_BYTES = 260_000
CELL = 40.0                                                      # read the 10 m bands decimated to 40 m: the box is ~80 m per pixel
NODATA_GREY = 235


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def tile_of(p):
    return p.name.split("_")[5]


def orbit_of(p):
    return p.name.split("_")[4]


def render(args):
    """One date: (date, [zip paths]) -> manifest entry. Reads every scene once (cached reader), two mosaics: as photographed and cloud-masked."""
    date, zips = args
    import rasterio
    from floodstate_eo.optical import sentinel_preprocess as SP
    from floodstate_eo.optical import truecolour as TC
    from PIL import Image
    P98 = _ld("p98", HERE / "p98_dashboard_layers.py")
    grid = dict(transform=P98.TR, ny=P98.NY, nx=P98.NX, crs=rasterio.crs.CRS.from_epsg(4326))
    cache = {}

    def reader(zp, cell):
        if zp not in cache:
            cache[zp] = SP.read_scene_bands(zp, cell)
        return cache[zp]
    zips = sorted(zips, key=lambda p: (LD_TILES.index(tile_of(p)), p.name))
    try:
        rgb, filled = TC.truecolour_mosaic(zips, grid, cell=CELL, stretch=(0.0, 0.30), gamma=1.0, cloud_scl=(0,), reader=reader)
        _, clear = TC.truecolour_mosaic(zips, grid, cell=CELL, stretch=(0.0, 0.30), gamma=1.0, reader=reader)
    except Exception as e:                                         # a broken archive member must not stop the other dates
        return dict(date=date, tiles=[tile_of(p) for p in zips], orbits=sorted({orbit_of(p) for p in zips}), error=repr(e)[:300], rendered=False)
    finally:
        cache.clear()
    seen = float((filled > 0).mean()); clear_share = float((clear > 0).mean())
    entry = dict(date=date, tiles=[tile_of(p) for p in zips], orbits=sorted({orbit_of(p) for p in zips}), seen_share=round(seen, 4), clear_share=round(clear_share, 4))
    if clear_share < MIN_CLEAR:
        entry.update(rendered=False, reason=f"clear share {clear_share:.1%} < {MIN_CLEAR:.0%}: cloud only"); return entry
    arr = np.moveaxis(np.asarray(rgb), 0, -1).astype("u1").copy(); arr[filled == 0] = NODATA_GREY
    img = Image.fromarray(arr, "RGB"); path = OUT / f"{date}.jpg"
    for q in (82, 75, 68, 60, 50):
        img.save(path, "JPEG", quality=q, optimize=True, progressive=True)
        if path.stat().st_size <= MAX_BYTES:
            break
    entry.update(rendered=True, file=f"s2rgb/{date}.jpg", quality=q, bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    return entry


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--since", default="2017-01-01"); ap.add_argument("--until", default="2099-12-31")
    ap.add_argument("--workers", type=int, default=4); ap.add_argument("--dates", nargs="*", help="only these dates")
    a = ap.parse_args(); t0 = time.time()
    from floodstate_eo.io import optical_catalogue as OC
    S = OC.scan_safes()
    jobs = [(d, [p for p in S[d] if tile_of(p) in LD_TILES]) for d in sorted(S) if a.since <= d <= a.until and (not a.dates or d in a.dates)]
    jobs = [(d, z) for d, z in jobs if z]
    OUT.mkdir(parents=True, exist_ok=True)
    mf = OUT / "manifest.json"; old = json.loads(mf.read_text())["dates"] if mf.exists() and not a.dates else {}
    print(f"{len(jobs)} dates, {a.workers} workers", flush=True)
    entries = dict(old); done = 0
    with mp.get_context("fork").Pool(a.workers) as pool:
        for e in pool.imap_unordered(render, jobs, chunksize=1):
            entries[e["date"]] = e; done += 1
            print(f"  {e['date']}: {'ok ' + str(e.get('bytes', 0) // 1000) + ' kB, clear ' + format(e['clear_share'], '.0%') if e.get('rendered') else 'skipped: ' + e.get('reason', e.get('error', ''))}  [{done}/{len(jobs)}, {round(time.time() - t0)} s]", flush=True)
    entries = dict(sorted(entries.items()))
    nb = sum(e.get("bytes", 0) for e in entries.values()); nr = sum(1 for e in entries.values() if e.get("rendered"))
    mf.write_text(json.dumps(dict(producer="p97c_s2_truecolour_dates.py", box=dict(bounds=[[32.15, 46.35], [33.55, 47.15]], note="p98 BBOX, EPSG:4326"), cell_m=CELL,
                                  min_clear=MIN_CLEAR, max_bytes=MAX_BYTES, tiles=LD_TILES, n_dates=len(entries), n_rendered=nr, total_bytes=nb,
                                  attribution="Sentinel-2 L2A true colour, clouds as photographed, processed by the authors; contains modified Copernicus Sentinel data",
                                  dates=entries), indent=1))
    print(f"-> {mf}: {nr} rendered of {len(entries)} dates, {nb / 1e6:.1f} MB, {round(time.time() - t0)} s")


if __name__ == "__main__":
    main()
