# Provenance: SWOT-DNIPRO scripts/p52b_frame_sensor_inventory.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 3 (migration_phase=5).
# Import block only: sys.path/swot_dnipro imports -> floodstate_eo package imports; the importlib
# spec_from_file_location load of p52a is replaced by a normal package import of the sibling module.
"""P52b -- what the sensors ACTUALLY see inside the three processing frames. Inventory only, no classification.

The user's first required result after the geography was fixed: not a flood area, but an honest table of sensor
coverage per frame. Nothing here decides flood or dry; nothing here removes a cell.

RULES THIS ENFORCES
  * The processing domain is B1/B2/B3 and nothing else. HAND, basin polygons, water masks, the FABDEM ceiling,
    persistent water and the old CUT_RECTS may not shrink a frame.
  * not observed != dry. A cell no sensor saw gets a status saying so.
  * A missing DERIVED product is not a missing observation. ZONE_3 has no `per_scene_water.npz`, but its variant store
    holds 192 scenes, 11 of them June 2023, each with its own `valid` plane on the zone grid -- so B3's Sentinel-1
    coverage is reconstructed from those, not declared absent.
  * EVENT and TRACE are separate evidence. The trace window can support a retrospective footprint; it is never a direct
    observation of the 06-09/13/14 peak, and the table keeps the two apart.
  * Every zone store that overlaps a frame contributes to it. The frames straddle zone boundaries on purpose.

Windows: PRE 2022-01-01..2023-06-05, EVENT 2023-06-07..2023-07-31, TRACE 2023-08-01..2023-11-30.
Outputs: <case_study>/tables/p52b_frame_sensor_inventory.csv, p52b_s1_scene_inventory.csv, p52b_s2_scene_inventory.csv,
         $BULK_ROOT/frames/<FID>/{s1_obs_count,s2_event_obs_count,s2_trace_obs_count,s2_pre_obs_count,sensor_status}.tif
"""
from __future__ import annotations
import json, sys, time, warnings
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
from . import p52a_processing_frames_qa as P52A

FRAMES = P52A.FRAMES

ZONES = ("ZONE_4_DAM_TO_KHERSON_FLOODWAY", "ZONE_2_KHERSON_DELTA", "ZONE_3_DNIPRO_BUG_ESTUARY")
CELL = 20.0
WIN = {"pre": ("2022-01-01", "2023-06-05"), "event": ("2023-06-07", "2023-07-31"), "trace": ("2023-08-01", "2023-11-30")}
S1_WIN = ("2023-06-01", "2023-06-30")          # the flood scenes; pre/post S1 all sit inside June here
OUT = CFG.BULK_ROOT / "frames"


def frame_grid(bbox):
    """A 20 m grid snapped outward to the frame, so the raster covers the whole rectangle and nothing is lost at the edge."""
    x0 = np.floor(bbox[0] / CELL) * CELL; y0 = np.floor(bbox[1] / CELL) * CELL
    x1 = np.ceil(bbox[2] / CELL) * CELL; y1 = np.ceil(bbox[3] / CELL) * CELL
    nx = int(round((x1 - x0) / CELL)); ny = int(round((y1 - y0) / CELL))
    return dict(x0=x0, y0=y0, x1=x1, y1=y1, nx=nx, ny=ny, transform=from_origin(x0, y1, CELL, CELL))


def to_frame(src_u8, src_tr, F, nodata=255):
    """Nearest reprojection of a uint8 layer onto a frame grid. `nodata` survives the warp, so NOT OBSERVED stays itself."""
    dst = np.full((F["ny"], F["nx"]), nodata, "u1")
    reproject(source=src_u8, destination=dst, src_transform=src_tr, src_crs=CFG.CRS_METRIC,
              dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest,
              src_nodata=nodata, dst_nodata=nodata)
    return dst


def write(path, arr, F, tags, nodata=255):
    path.parent.mkdir(parents=True, exist_ok=True)
    prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=1, dtype=arr.dtype.name,
                crs=CFG.CRS_METRIC, transform=F["transform"], nodata=nodata, compress="deflate",
                tiled=True, blockxsize=512, blockysize=512)
    with rasterio.open(path, "w", **prof) as ds:
        ds.write(arr, 1); ds.update_tags(**tags)


def main():
    t0 = time.time()
    grids = {fid: frame_grid(f["bbox"]) for fid, f in FRAMES.items()}
    zone_grids = {z: SP.zone_grid(z, CELL) for z in ZONES}
    for fid, F in grids.items():
        print(f"{fid}: grid {F['ny']}x{F['nx']} = {F['ny']*F['nx']/1e6:.1f} Mpx, "
              f"{F['ny']*F['nx']*CELL*CELL/1e6:,.0f} km2", flush=True)

    s1_rows, s2_rows = [], []
    s1_obs = {fid: np.zeros((g["ny"], g["nx"]), "u2") for fid, g in grids.items()}
    s2_cnt = {w: {fid: np.zeros((g["ny"], g["nx"]), "u2") for fid, g in grids.items()} for w in WIN}

    # ---------------- Sentinel-1: rebuilt from the per-scene VARIANT STORE, which every zone has
    for z in ZONES:
        store = CFG.BULK_ROOT / "s1_variants" / z
        ZG = zone_grids[z]
        ztr = from_origin(ZG["x0"], ZG["y1"], CELL, CELL)
        zbox = box(ZG["x0"], ZG["y0"], ZG["x1"], ZG["y1"])
        scenes = sorted(p for p in store.glob("*.npz") if S1_WIN[0] <= p.stem[:10] <= S1_WIN[1])
        touched = [fid for fid, f in FRAMES.items() if box(*f["bbox"]).intersects(zbox)]
        print(f"\nS1 {z}: {len(scenes)} scenes in {S1_WIN[0]}..{S1_WIN[1]} -> frames {touched}", flush=True)
        for p in scenes:
            with np.load(p, allow_pickle=False) as d:
                shp = tuple(int(v) for v in d["shape"]); n = shp[0] * shp[1]
                if shp != (ZG["ny"], ZG["nx"]):
                    print(f"   !! {p.stem}: store shape {shp} != zone grid {(ZG['ny'], ZG['nx'])}, skipped"); continue
                valid = np.unpackbits(d["valid"], count=n).astype("u1").reshape(shp)
                meta = json.loads(str(d["meta"])) if "meta" in d else {}
            src = np.where(valid.astype(bool), 1, 255).astype("u1")
            row = dict(zone=z, scene=p.stem, date=p.stem[:10], orbit=meta.get("relative_orbit"),
                       observed_frac_zone=round(float(valid.mean()), 4))
            for fid in touched:
                v = to_frame(src, ztr, grids[fid]) == 1
                s1_obs[fid] += v
                row[f"observed_frac_{fid}"] = round(float(v.mean()), 4)
            s1_rows.append(row)
        print(f"   {len(scenes)} scenes folded in ({time.time()-t0:.0f}s)", flush=True)

    # ---------------- Sentinel-2: every scene in the archive, validity from its own SCL
    for z in ZONES:
        d = CFG.BULK_ROOT / "zone_spectral" / z
        if not d.exists():
            print(f"\nS2 {z}: no stacks"); continue
        ZG = zone_grids[z]; ztr = from_origin(ZG["x0"], ZG["y1"], CELL, CELL)
        zbox = box(ZG["x0"], ZG["y0"], ZG["x1"], ZG["y1"])
        touched = [fid for fid, f in FRAMES.items() if box(*f["bbox"]).intersects(zbox)]
        dates = sorted(p.name[:10] for p in d.glob("*_indices.tif"))
        use = {w: [x for x in dates if lo <= x <= hi] for w, (lo, hi) in WIN.items()}
        print(f"\nS2 {z}: {len(dates)} stacks; pre {len(use['pre'])}, event {len(use['event'])}, "
              f"trace {len(use['trace'])} -> frames {touched}", flush=True)
        for w, ds_ in use.items():
            for dt in ds_:
                sp = d / f"{dt}_scl.tif"
                if not sp.exists():
                    continue
                with rasterio.open(sp) as ds:
                    scl = ds.read(1)
                ok = (~np.isin(scl, WM.SCL_REJECT)).astype("u1")
                src = np.where(ok.astype(bool), 1, 255).astype("u1")
                row = dict(zone=z, date=dt, window=w, observed_frac_zone=round(float(ok.mean()), 4))
                for fid in touched:
                    v = to_frame(src, ztr, grids[fid]) == 1
                    s2_cnt[w][fid] += v
                    row[f"observed_frac_{fid}"] = round(float(v.mean()), 4)
                s2_rows.append(row)
        print(f"   folded in ({time.time()-t0:.0f}s)", flush=True)

    # ---------------- the table the user asked for
    px = CELL * CELL / 1e6
    rows = []
    for fid, F in grids.items():
        tot = F["ny"] * F["nx"]
        s1 = s1_obs[fid] > 0
        ev = s2_cnt["event"][fid] > 0; tr = s2_cnt["trace"][fid] > 0; pr = s2_cnt["pre"][fid] > 0
        none = ~s1 & ~ev & ~tr
        rows.append(dict(frame=fid, name=FRAMES[fid]["label"], area_km2=round(tot * px, 1),
                         s1_observed_km2=round(s1.sum() * px, 1), s1_observed_pct=round(100 * s1.mean(), 2),
                         s1_unobserved_km2=round((~s1).sum() * px, 1), s1_unobserved_pct=round(100 * (~s1).mean(), 2),
                         s1_scenes_median=int(np.median(s1_obs[fid])), s1_scenes_max=int(s1_obs[fid].max()),
                         s2_event_observed_km2=round(ev.sum() * px, 1), s2_event_observed_pct=round(100 * ev.mean(), 2),
                         s2_trace_observed_km2=round(tr.sum() * px, 1), s2_trace_observed_pct=round(100 * tr.mean(), 2),
                         s2_pre_observed_km2=round(pr.sum() * px, 1), s2_pre_observed_pct=round(100 * pr.mean(), 2),
                         s2_event_scenes_median=int(np.median(s2_cnt["event"][fid])),
                         s2_trace_scenes_median=int(np.median(s2_cnt["trace"][fid])),
                         both_unavailable_km2=round(none.sum() * px, 1), both_unavailable_pct=round(100 * none.mean(), 2)))
        # sensor availability status: 0 none | 1 S1 only | 2 S2 event only | 3 S1 + S2 event | 4 S2 trace only | 5 S1 + trace
        st = np.zeros((F["ny"], F["nx"]), "u1")
        st[s1] = 1; st[ev & ~s1] = 2; st[ev & s1] = 3; st[tr & ~ev & ~s1] = 4; st[tr & ~ev & s1] = 5
        o = OUT / fid
        write(o / "s1_obs_count.tif", s1_obs[fid].astype("u2"), F,
              dict(values="number of Sentinel-1 scenes that OBSERVED this cell (June 2023), rebuilt from the per-scene variant store", nodata="none"), nodata=0)
        for w in WIN:
            write(o / f"s2_{w}_obs_count.tif", s2_cnt[w][fid].astype("u2"), F,
                  dict(values=f"number of Sentinel-2 scenes with a VALID observation in the {w} window {WIN[w][0]}..{WIN[w][1]}"), nodata=0)
        write(o / "sensor_status.tif", st, F,
              dict(values="0 neither sensor ever observed | 1 S1 only | 2 S2 event only | 3 S1 + S2 event | "
                          "4 S2 trace only | 5 S1 + S2 trace (no event optics)",
                   note="availability only -- says nothing about flood or dry"), nodata=255)
    T = pd.DataFrame(rows)
    T.to_csv(CFG.TABLES / "p52b_frame_sensor_inventory.csv", index=False)
    pd.DataFrame(s1_rows).to_csv(CFG.TABLES / "p52b_s1_scene_inventory.csv", index=False)
    pd.DataFrame(s2_rows).to_csv(CFG.TABLES / "p52b_s2_scene_inventory.csv", index=False)
    pd.set_option("display.width", 260)
    key = ["frame", "area_km2", "s1_observed_km2", "s1_observed_pct", "s1_unobserved_km2",
           "s2_event_observed_km2", "s2_event_observed_pct", "s2_trace_observed_km2", "s2_trace_observed_pct",
           "both_unavailable_km2", "both_unavailable_pct"]
    print("\n" + "=" * 110); print(T[key].to_string(index=False)); print("=" * 110)
    print(f"\n-> <case_study>/tables/p52b_{{frame_sensor_inventory,s1_scene_inventory,s2_scene_inventory}}.csv")
    print(f"-> {OUT}/<FID>/{{s1_obs_count,s2_*_obs_count,sensor_status}}.tif   ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
