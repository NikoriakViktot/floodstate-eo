# Provenance: SWOT-DNIPRO scripts/p54a_frame_index_stacks_10m.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 8 (migration_phase=5).
#
# MIGRATION TODO / RESOLVED SUBSTITUTION (provenance/UNRESOLVED_DEPENDENCIES.md): the source script loaded
# `scripts/p53a_frame_index_stacks.py` via importlib purely for two module-level constants, `P53A.ZONES` and
# `P53A.WIN`. `p53a` is explicitly SUPERSEDED (18_RISKS_AND_BLOCKERS.md of the source audit: "p53a/p53b (20 m,
# OOM; still imported by p54a)") and is NOT in the migration manifest, so it is not pulled in here. Both
# constants are inlined below instead of guessed: `ZONES` is copied verbatim from the migrated
# `p52b_frame_sensor_inventory.py` (same three zone names, same tuple), and `WIN` is copied verbatim from
# `p54b_frame_composites_10m.py`'s own module-level `WIN` dict -- i.e. both values are independently present
# elsewhere in this same migrated codebase, not invented for this file.
"""P54a -- per-date Sentinel-2 index stacks on the CANONICAL 10 m lattice. Memory-bounded rewrite of a legacy,
whole-frame-array predecessor.

WHY THIS REPLACES THE PREDECESSOR. The predecessor held whole-frame float32 arrays: seven indices inside one
per-date stacking pass and seven more in the caller, ~8.5 GB for one B3 date before the merge copies, and the
kernel killed it (`anon-rss 12.4 GB` on a 15 GB box). That was a planning error -- the same message that said
"tiled processing, never hold the cube in RAM" left whole-frame arrays in place, which merely happened to fit
at 20 m.

Here every date is written STRIP BY STRIP. Peak memory is set by the strip, not by the frame, so B3 at 144.9 Mpx
costs the same as B2 at 28.9 Mpx.

Sources per strip, merged first-valid-wins:
  1. PASS 1/2 SAFE archives. Bands are read through a window onto the strip. The tile grid IS the canonical lattice
     (native origins are multiples of 20 m), so 10 m bands move by an exact integer offset with no interpolation.
     B11/B12 are native 20 m and are brought to 10 m ONCE, bilinear, BEFORE the index. SCL is categorical: nearest.
  2. legacy per-zone 20 m index stacks, for dates no archive covers. One 20 m zone cell is exactly two lattice cells
     per axis, so this is an integer relation too -- the half-cell defect of the 20 m build cannot recur.

`n_obs` is not computed here; the companion `<date>_valid.tif` is the only thing the composite stage counts.

PERSISTENT SOURCE DESCRIPTORS WERE TESTED AND REJECTED. Opening each archive once per date instead of once per strip
was tried on the largest frame (B3, acquisition 2023-06-18, 144.9 Mpx). It produced pixel-identical outputs -- zero
mismatches across all seven bands and the validity mask -- but increased runtime from 198 to 218 s (+10.1 %) with a
negligible memory change (2.21 -> 2.25 GB). The non-persistent windowed implementation was therefore retained.
`--persistent` remains as a documented experimental option, off by default. Tables: p54a_ab_persistent_descriptors.csv,
p54a_ab_pixel_mismatch.csv.
Outputs: $BULK_ROOT/frames10/<FID>/indices/<date>.tif (7 bands int16 1e4) and <date>_valid.tif (0/1)
         <case_study>/tables/p54a_frame_index_stacks.csv
"""
from __future__ import annotations
import argparse, sys, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
import os, resource
os.environ.setdefault("GDAL_CACHEMAX", "256")      # MB: keep GDAL's own cache out of the RSS budget
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from rasterio.windows import Window, from_bounds
from .. import _kakhovka_legacy_config as CFG
from . import sentinel_preprocess as SP
from . import watermask as WM
from ..spatial import canonical_grid as CG
from ..io import optical_catalogue as OC

OUT = CFG.BULK_ROOT / "frames10"
ZONES = ("ZONE_4_DAM_TO_KHERSON_FLOODWAY", "ZONE_2_KHERSON_DELTA", "ZONE_3_DNIPRO_BUG_ESTUARY")  # = p52b.ZONES
WIN = {"pre": ("2022-01-01", "2023-06-05"), "event": ("2023-06-07", "2023-07-31"),
       "trace": ("2023-08-01", "2023-11-30")}                                                    # = p54b.WIN
CELL = CG.CELL
STRIP = 512
B10 = ("B02", "B03", "B04", "B08")
B20 = ("B11", "B12")


def strip_grid(F, r0, r1):
    y1 = F["y1"] - r0 * CELL
    return dict(x0=F["x0"], y1=y1, y0=y1 - (r1 - r0) * CELL, x1=F["x1"],
                nx=F["nx"], ny=r1 - r0, transform=from_origin(F["x0"], y1, CELL, CELL))


def open_safe(zp: Path):
    """Open every band of one archive ONCE. Only file handles are kept, never arrays: the memory architecture is
    unchanged and peak RSS still depends on the strip, not the frame. Without this each 512-row strip reopened all
    seven bands of all five archives -- 32 opens per date on B3, pure I/O overhead."""
    import zipfile
    with zipfile.ZipFile(zp) as z:
        names = z.namelist()
    h = {}
    for b in B10 + B20 + ("SCL",):
        m = WM._find(names, b, "10m" if b in B10 else "20m")
        if m is None:
            for d in h.values():
                d.close()
            return None
        h[b] = rasterio.open(f"zip+file://{zp}!/{m}")
    return h


def safe_strip(handles, meta, S) -> dict | None:
    """All seven-index inputs for ONE archive on ONE strip, read from already-open datasets."""
    if handles is None:
        return None
    out = {}
    for b, src in handles.items():
        rs = Resampling.nearest if (b == "SCL" or b not in B20) else Resampling.bilinear
        # EXPLICIT REPROJECTION, NOT A DECIMATED READ.
        # `src.read(window=..., out_shape=..., resampling=...)` scales the requested window onto the output shape and
        # DISCARDS the fractional part of the window offset. For a 10 m source that offset is always integral and the
        # result is exact; for a 20 m source it is not. Frame B2 starts at y = 5 211 570, which is 10 m -- half a
        # 20 m pixel -- off the native Sentinel-2 lattice that B1 and B3 sit on, so its SWIR windows carried a
        # permanent 0.5-pixel phase and every B11/B12 index came out shifted by 10 m relative to the other frames.
        # Measured on the B1/B2 overlap before the fix: NDWI (B03/B08, native 10 m) identical on 100 % of cells,
        # while MNDWI, NDMI, NDBI, BSI and AWEIsh differed on ~97 % with a median of 0.0011 and a maximum of 0.59
        # index units, modulated with the 512-row processing stripe -- the code's own architecture printed onto the
        # map. `reproject` with explicit source and destination transforms places every destination cell centre in
        # source coordinates exactly, whatever the frame origin happens to be.
        win = from_bounds(S["x0"], S["y0"], S["x1"], S["y1"], transform=src.transform)
        pad = 3          # halo so the bilinear kernel has real neighbours at the strip edge, never fill_value
        r0 = int(np.floor(win.row_off)) - pad; c0 = int(np.floor(win.col_off)) - pad
        rwin = Window(c0, r0, int(np.ceil(win.width)) + 2 * pad, int(np.ceil(win.height)) + 2 * pad)
        a = src.read(1, window=rwin, boundless=True, fill_value=0)
        dst = np.zeros((S["ny"], S["nx"]), a.dtype)
        reproject(source=a, destination=dst, src_transform=src.window_transform(rwin), src_crs=src.crs,
                  dst_transform=S["transform"], dst_crs=CFG.CRS_METRIC, resampling=rs)
        out[b] = dst.astype("i2") if b == "SCL" else meta.reflectance(b, dst)
    return out


def stack_strip(zone, path, S):
    """A legacy 20 m zone index stack on one 10 m strip: integer relation, nearest is exact."""
    ZG = SP.zone_grid(zone, 20.0)
    ztr = from_origin(ZG["x0"], ZG["y1"], 20.0, 20.0)
    idx = {}
    with rasterio.open(path) as ds:
        win = from_bounds(S["x0"], S["y0"], S["x1"], S["y1"], transform=ztr)
        for i, nm in enumerate(SP.INDEX_NAMES, 1):
            a = ds.read(i, window=win, boundless=True, fill_value=SP.INDEX_NODATA)
            dst = np.full((S["ny"], S["nx"]), SP.INDEX_NODATA, "i2")
            sub = from_origin(ZG["x0"] + max(int(np.floor(win.col_off)), 0) * 20.0,
                              ZG["y1"] - max(int(np.floor(win.row_off)), 0) * 20.0, 20.0, 20.0)
            reproject(source=a, destination=dst, src_transform=sub, src_crs=CFG.CRS_METRIC,
                      dst_transform=S["transform"], dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest,
                      src_nodata=SP.INDEX_NODATA, dst_nodata=SP.INDEX_NODATA)
            idx[nm] = np.where(dst == SP.INDEX_NODATA, np.nan, dst.astype("f4") / SP.INDEX_SCALE)
    sp = path.with_name(path.name.replace("_indices.tif", "_scl.tif"))
    if sp.exists():
        with rasterio.open(sp) as ds:
            win = from_bounds(S["x0"], S["y0"], S["x1"], S["y1"], transform=ztr)
            scl = ds.read(1, window=win, boundless=True, fill_value=0)
        v = np.where(~np.isin(scl, WM.SCL_REJECT) & (scl > 0), 1, 255).astype("u1")
        dst = np.full((S["ny"], S["nx"]), 255, "u1")
        sub = from_origin(ZG["x0"] + max(int(np.floor(win.col_off)), 0) * 20.0,
                          ZG["y1"] - max(int(np.floor(win.row_off)), 0) * 20.0, 20.0, 20.0)
        reproject(source=v, destination=dst, src_transform=sub, src_crs=CFG.CRS_METRIC,
                  dst_transform=S["transform"], dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest,
                  src_nodata=255, dst_nodata=255)
        valid = dst == 1
    else:
        valid = np.isfinite(idx["NDWI"])
    return idx, valid


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--windows", nargs="*", default=["event", "pre", "trace"])
    ap.add_argument("--frames", nargs="*", default=list(CG.FRAME_BBOX))
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--strip", type=int, default=STRIP)
    ap.add_argument("--dates", nargs="*", default=None, help="restrict to these acquisition dates (smoke tests)")
    ap.add_argument("--persistent", action="store_true",
                    help="variant B: open each archive once per date instead of once per strip")
    ap.add_argument("--out-root", default=str(OUT))
    a = ap.parse_args()
    OUT = Path(a.out_root)
    rows = []; t0 = time.time()
    def peak_gb():
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6   # Linux reports kB
    for w in a.windows:
        lo, hi = WIN[w]
        # LINEAGE, not just coverage. An early catalogue searched ONE directory for SAFE and fell back to the legacy
        # per-zone 20 m stacks everywhere else: pre and trace came out 100 % legacy, plus five event dates. Those
        # stacks are cell_m = 20 on the x0 = 10 (mod 20) grid, so the change features would have differenced a true
        # 10 m event statistic against a 20 m-derived one. OC.catalogue prefers native SAFE per date and never
        # mixes the two within a date. See floodstate_eo/io/optical_catalogue.py.
        cat = OC.catalogue(lo, hi)
        if a.dates:
            cat = {k: v for k, v in cat.items() if k in set(a.dates)}
        print(f"\n=== window {w} {lo}..{hi}: {len(cat)} dates ===", flush=True)
        for dt, src in cat.items():
            metas = {}
            for fid in a.frames:
                F = CG.frame_grid(fid)
                out = OUT / fid / "indices"; out.mkdir(parents=True, exist_ok=True)
                ip = out / f"{dt}.tif"; vp = out / f"{dt}_valid.tif"
                if ip.exists() and ip.stat().st_size > 0 and vp.exists() and not a.overwrite:
                    continue
                prof = SP._profile(F, len(SP.INDEX_NAMES), "int16", SP.INDEX_NODATA)
                prof.update(BIGTIFF="IF_SAFER", blockxsize=512, blockysize=512)
                vprof = dict(prof); vprof.update(count=1, dtype="uint8", nodata=255)
                # ATOMIC PUBLICATION. A killed process left a zero-byte raster that a restart would have accepted as
                # finished. Nothing reaches the final name until every strip is written and the file is read back.
                ipp = ip.with_suffix(".tif.part"); vpp = vp.with_suffix(".tif.part")
                tags = dict(date=dt, frame=fid, producer="p54a_frame_index_stacks_10m.py",
                            bands="|".join(SP.INDEX_NAMES), cell_m=str(CELL),
                            resampling=str(CG.RESAMPLING), scale=f"value/{SP.INDEX_SCALE}",
                            lineage=src.get("lineage", "UNKNOWN"), native_m=str(src.get("native_m", "")),
                            n_safe=str(len(src.get("safes", []))), n_stack=str(len(src.get("stacks", []))),
                            superseded_stacks=";".join(f"{Path(x).parent.name}/{Path(x).name}"
                                                       for x in src.get("superseded_stacks", [])),
                            note="NDBI is derived as -NDMI at the composite stage, with min/max transposed")
                origin_bits = []; vsum = 0
                handles = {}
                if a.persistent:
                    for zp in src["safes"]:
                        if zp not in metas:
                            try:
                                metas[zp] = SP.read_metadata(zp)
                            except Exception:
                                metas[zp] = None
                        handles[zp] = open_safe(zp) if metas[zp] is not None else None
                with rasterio.open(ipp, "w", **prof) as dst, rasterio.open(vpp, "w", **vprof) as vdst:
                    for i, nm in enumerate(SP.INDEX_NAMES, 1):
                        dst.set_band_description(i, nm)
                    for r0 in range(0, F["ny"], a.strip):
                        r1 = min(r0 + a.strip, F["ny"]); S = strip_grid(F, r0, r1)
                        acc = {nm: np.full((S["ny"], S["nx"]), np.nan, "f4") for nm in SP.INDEX_NAMES}
                        val = np.zeros((S["ny"], S["nx"]), bool)
                        for zp in src["safes"]:
                            if zp not in metas:
                                try:
                                    metas[zp] = SP.read_metadata(zp)
                                except Exception:
                                    metas[zp] = None
                            if metas[zp] is None:
                                continue
                            hs = handles.get(zp) if a.persistent else open_safe(zp)
                            b = safe_strip(hs, metas[zp], S)
                            if not a.persistent and hs:
                                for _d in hs.values():
                                    _d.close()
                            if b is None:
                                continue
                            i2 = SP.compute_indices(b); v2 = SP.valid_mask(b["SCL"], b["B03"])
                            take = v2 & ~val
                            if take.any():
                                for nm in SP.INDEX_NAMES:
                                    acc[nm][take] = i2[nm][take]
                                val |= take
                            del b, i2, v2
                        if not val.all():
                            for z, sp_ in src["stacks"]:
                                i2, v2 = stack_strip(z, sp_, S)
                                take = v2 & ~val
                                if take.any():
                                    for nm in SP.INDEX_NAMES:
                                        acc[nm][take] = i2[nm][take]
                                    val |= take
                                del i2, v2
                        win = Window(0, r0, F["nx"], r1 - r0)
                        for i, nm in enumerate(SP.INDEX_NAMES, 1):
                            q = np.where(val & np.isfinite(acc[nm]),
                                         np.clip(np.round(acc[nm] * SP.INDEX_SCALE), -32767, 32767),
                                         SP.INDEX_NODATA).astype("i2")
                            dst.write(q, i, window=win)
                        vdst.write(val.astype("u1"), 1, window=win)
                        vsum += int(val.sum())
                        del acc, val
                    dst.update_tags(**tags); vdst.update_tags(**tags)
                for hs in handles.values():
                    if hs:
                        for _d in hs.values():
                            _d.close()
                frac = vsum / (F["ny"] * F["nx"])
                if vsum == 0:
                    ipp.unlink(missing_ok=True); vpp.unlink(missing_ok=True)
                    print(f"  {w:5s} {dt} {fid}: no valid observation, nothing written", flush=True)
                    continue
                try:
                    with rasterio.open(ipp) as chk:
                        assert (chk.height, chk.width) == (F["ny"], F["nx"]), "shape"
                        assert chk.count == len(SP.INDEX_NAMES), "band count"
                        assert chk.dtypes[0] == "int16", "dtype"
                        assert max(abs(x - y) for x, y in zip(chk.transform[:6], F["transform"][:6])) < 1e-9, "transform"
                        chk.read(2, window=Window(0, F["ny"] // 2, min(2048, F["nx"]), 64))
                    with rasterio.open(vpp) as chk:
                        assert (chk.height, chk.width) == (F["ny"], F["nx"]), "valid shape"
                except Exception as ex:
                    print(f"  {w:5s} {dt} {fid}: READ-BACK FAILED ({ex}); left as .part", flush=True)
                    continue
                os.replace(ipp, ip); os.replace(vpp, vp)
                rows.append(dict(window=w, date=dt, frame=fid, valid_frac=round(frac, 4),
                                 valid_km2=round(vsum * CELL * CELL / 1e6, 1),
                                 n_safes=len(src["safes"]), n_stacks=len(src["stacks"]),
                                 peak_rss_gb=round(peak_gb(), 2), bytes_out=ip.stat().st_size))
                print(f"  {w:5s} {dt} {fid}: valid {100*frac:5.1f} %  "
                      f"({len(src['safes'])} safe, {len(src['stacks'])} stack)  {time.time()-t0:.0f}s  "
                      f"peakRSS {peak_gb():.2f} GB", flush=True)
                pd.DataFrame(rows).to_csv(CFG.TABLES / "p54a_frame_index_stacks.csv", index=False)
    print(f"\n-> {OUT}/<FID>/indices/   ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
