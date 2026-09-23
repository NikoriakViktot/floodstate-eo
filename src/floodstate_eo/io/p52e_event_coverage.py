# Provenance: SWOT-DNIPRO scripts/p52e_event_coverage.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 6 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo; importlib loads of p52a/p52b -> package imports.
"""P52e -- how RELIABLE the optical record is inside each frame, per date and cumulatively. Coverage only.

After PASS 1 the question is not "was this cell ever seen" but "how many times". A cell seen once in eight weeks and a
cell seen eight times support very different claims, and a single "% covered" number hides that. So the output is the
distribution the user asked for -- 0, 1, 2, 3-5, 6+ valid EVENT observations, in km2 and per cent of each frame.

Two sources are merged and DATES ARE COUNTED ONCE. The zone index stacks are per-zone mosaics of a date; the PASS 1
downloads are per-tile products of the same or other dates. Counting both would inflate the record, so for every date
the frame-level valid mask is the union over every source that carries it, and the counter goes up by one.

Validity is per pixel from each scene's own SCL, using the project's shared SCL_REJECT. A product accepted at
cloudCover <= 20 % still contributes only the pixels it actually saw; the query ceiling never decided a pixel.
not observed != dry: a cell with zero valid observations is recorded as such, never as land.
Outputs: <case_study>/tables/p52e_event_coverage_histogram.csv, p52e_event_coverage_by_date.csv,
         $BULK_ROOT/frames/<FID>/s2_event_obs_count_pass1.tif
"""
from __future__ import annotations
import sys, time, warnings, zipfile
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from shapely.geometry import box
from .. import _kakhovka_legacy_config as CFG
from ..optical import sentinel_preprocess as SP
from ..optical import watermask as WM
from ..spatial import p52a_processing_frames_qa as P52A
from ..spatial import p52b_frame_sensor_inventory as P52B

FRAMES = P52A.FRAMES
ZONES = ("ZONE_4_DAM_TO_KHERSON_FLOODWAY", "ZONE_2_KHERSON_DELTA", "ZONE_3_DNIPRO_BUG_ESTUARY")
EVENT = ("2023-06-07", "2023-07-31")
NEW = CFG.BULK_ROOT / "sentinel_event_2023"
OUT = CFG.BULK_ROOT / "frames"
BINS = [(0, 0, "0"), (1, 1, "1"), (2, 2, "2"), (3, 5, "3-5"), (6, 999, "6+")]


def sources_by_date():
    """{date: [(kind, payload), ...]} over both the existing zone stacks and the PASS 1 SAFE archives."""
    out = {}
    for z in ZONES:
        d = CFG.BULK_ROOT / "zone_spectral" / z
        if not d.exists():
            continue
        for p in sorted(d.glob("*_scl.tif")):
            dt = p.name[:10]
            if EVENT[0] <= dt <= EVENT[1]:
                out.setdefault(dt, []).append(("stack", (z, p)))
    if NEW.exists():
        for p in sorted(NEW.glob("*.SAFE.zip")):
            parts = p.name.split("_")
            dt = parts[2][:8] if len(parts) > 2 else ""
            dt = f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}" if len(dt) == 8 else ""
            if dt and EVENT[0] <= dt <= EVENT[1]:
                out.setdefault(dt, []).append(("safe", p))
    return {k: out[k] for k in sorted(out)}


def valid_from_stack(z, p, F, zone_tr):
    with rasterio.open(p) as ds:
        scl = ds.read(1)
    src = np.where(~np.isin(scl, WM.SCL_REJECT), 1, 255).astype("u1")
    return P52B.to_frame(src, zone_tr, F) == 1


def valid_from_safe(p, F):
    with zipfile.ZipFile(p) as z:
        member = WM._find(z.namelist(), "SCL", "20m")
    if member is None:
        return None
    with rasterio.open(f"zip+file://{p}!/{member}") as src:
        scl = src.read(1); tr = src.transform; crs = src.crs
    good = np.where(~np.isin(scl, WM.SCL_REJECT), 1, 255).astype("u1")
    dst = np.full((F["ny"], F["nx"]), 255, "u1")
    reproject(source=good, destination=dst, src_transform=tr, src_crs=crs,
              dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC,
              resampling=Resampling.nearest, src_nodata=255, dst_nodata=255)
    return dst == 1


def main():
    t0 = time.time()
    grids = {fid: P52B.frame_grid(f["bbox"]) for fid, f in FRAMES.items()}
    zone_tr = {z: (lambda g: from_origin(g["x0"], g["y1"], 20.0, 20.0))(SP.zone_grid(z, 20.0)) for z in ZONES}
    cnt = {fid: np.zeros((g["ny"], g["nx"]), "u1") for fid, g in grids.items()}
    by_date = []
    S = sources_by_date()
    print(f"event window {EVENT[0]}..{EVENT[1]}: {len(S)} distinct dates from "
          f"{sum(len(v) for v in S.values())} sources (zone stacks + PASS 1 archives)\n", flush=True)
    for dt, srcs in S.items():
        row = dict(date=dt, n_sources=len(srcs), kinds="|".join(sorted({k for k, _ in srcs})))
        for fid, F in grids.items():
            acc = np.zeros((F["ny"], F["nx"]), bool)
            for kind, payload in srcs:
                try:
                    v = valid_from_stack(*payload, F, zone_tr[payload[0]]) if kind == "stack" else valid_from_safe(payload, F)
                except Exception as e:
                    print(f"   !! {dt} {kind}: {type(e).__name__}: {str(e)[:70]}", flush=True); continue
                if v is not None:
                    acc |= v
            cnt[fid] = np.minimum(cnt[fid].astype("u2") + acc, 255).astype("u1")   # one increment per DATE
            row[f"valid_frac_{fid}"] = round(float(acc.mean()), 4)
        by_date.append(row)
        print(f"  {dt}: {len(srcs)} src -> " + "  ".join(f"{fid} {100*row['valid_frac_'+fid]:5.1f} %" for fid in grids)
              + f"   ({time.time()-t0:.0f}s)", flush=True)
    px = 20.0 * 20.0 / 1e6
    rows = []
    for fid, F in grids.items():
        tot = F["ny"] * F["nx"]
        c = cnt[fid]
        r = dict(frame=fid, name=FRAMES[fid]["label"], area_km2=round(tot * px, 1),
                 dates_in_window=len(S), median_obs=int(np.median(c)), max_obs=int(c.max()))
        for lo, hi, lab in BINS:
            m = (c >= lo) & (c <= hi)
            r[f"km2_{lab}"] = round(m.sum() * px, 1); r[f"pct_{lab}"] = round(100 * m.mean(), 2)
        rows.append(r)
        P52B.write(OUT / fid / "s2_event_obs_count_pass1.tif", c, F,
                   dict(values="number of DISTINCT dates with at least one valid Sentinel-2 observation in "
                               f"{EVENT[0]}..{EVENT[1]} (zone stacks + PASS 1 archives, per-pixel SCL)",
                        note="coverage only -- says nothing about flood or dry"), nodata=255)
    T = pd.DataFrame(rows); T.to_csv(CFG.TABLES / "p52e_event_coverage_histogram.csv", index=False)
    D = pd.DataFrame(by_date); D.to_csv(CFG.TABLES / "p52e_event_coverage_by_date.csv", index=False)
    pd.set_option("display.width", 250)
    print("\n" + "=" * 100)
    print("VALID EVENT OBSERVATIONS PER CELL (distinct dates), by frame")
    cols = ["frame", "area_km2", "median_obs", "max_obs"] + [f"{p}_{l}" for _, _, l in BINS for p in ("km2", "pct")]
    print(T[cols].to_string(index=False)); print("=" * 100)
    print("\n-> <case_study>/tables/p52e_event_coverage_{histogram,by_date}.csv")
    print(f"-> {OUT}/<FID>/s2_event_obs_count_pass1.tif   ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
