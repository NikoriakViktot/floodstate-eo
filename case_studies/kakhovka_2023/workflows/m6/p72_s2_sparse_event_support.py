# Provenance: SWOT-DNIPRO scripts/p72_s2_sparse_event_support.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: ACTIVE -- builds s2_sparse_support.tif, the 06-08 / 06-18 optical support channels planned for U3/U4.
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P72 -- sparse DATED optical support for M6. Not a peak composite, because there is no optical peak to composite.

THE INVENTORY DECIDED THIS FILE'S SHAPE. Inside the peak window 2023-06-06..06-14 the archive holds exactly ONE
Sentinel-2 acquisition, 06-08, valid over 21.4 % of B1, 25.7 % of B2 and 16.2 % of B3; no pixel anywhere has two.
`event_min` and `event_max` would therefore be the same number, and a "peak composite" would be a single scene with
a misleading name. So each date is carried separately, with its own validity, and nothing is aggregated over time.

TEMPORAL ROLES ARE EXPLICIT AND NOT INTERCHANGEABLE:
    2023-06-08   EARLY_EVENT_OPTICAL_SUPPORT   the early stage of the event: the breach was 06-06, Sentinel-1 -- the breach was 06-06 and Sentinel-1 sees water on
                                        06-09, 06-13 and 06-14, all AFTER this acquisition
    2023-06-18   EARLY_RECESSION        four days past the peak window; it is never called peak
Later optical data belongs to TRACE and is not read here.

WHY THESE TWO DATES AND NOT THE NEAREST PER FRAME. B1 also has 06-15 and B3 has 06-16, closer to the peak. Using
each frame's nearest date would put different observations on the same ground in an overlap and break the invariant
that a physical pixel has one value. 06-08 and 06-18 are the only dates present in all three frames, so the
frame-consistent choice and the temporally sensible one coincide.

Sentinel-2 is SUPPORT here, not the backbone: the peak is carried by Sentinel-1 (p71). A cell without a valid
optical observation gets a deterministic fill AND a zero validity channel; it is never treated as dry.

Outputs: <frame>/s2_sparse_support.tif (22 channels), outputs/tables/p72_s2_{inventory,support,overlap_qa}.csv,
         $BULK_ROOT/frames10/p72_manifest.json
"""
from __future__ import annotations
import argparse, itertools, json, os, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.windows import Window, from_bounds
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG
from floodstate_eo.optical import sentinel_preprocess as SP

OUT = CFG.BULK_ROOT / "frames10"
FR = ("B1", "B2", "B3")
IDX = ["NDVI", "NDWI", "MNDWI", "NDMI", "BSI"]
DATES = {"2023-06-08": "EARLY_EVENT_OPTICAL_SUPPORT", "2023-06-18": "EARLY_RECESSION"}
ND = SP.INDEX_NODATA
SCALE = SP.INDEX_SCALE
FILL = 0                      # deterministic neutral fill; the validity channel is what carries the absence


def channels():
    c = []
    for dt in DATES:
        tag = dt.replace("-", "")[4:]
        c += [f"{i}_{tag}" for i in IDX] + [f"d{i}_{tag}" for i in IDX] + [f"valid_{tag}"]
    return c


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=list(FR)); a = ap.parse_args()
    CH = channels()
    inv, sup, orows = [], [], []
    for fid in a.frames:
        t0 = time.time(); F = CG.frame_grid(fid)
        with rasterio.open(OUT / fid / "composite_preall.tif") as s:
            cn = list(s.descriptions)
            pre = {i: s.read(cn.index(f"{i}_pre_med") + 1).astype("f4") for i in IDX}
        for i in IDX:
            pre[i][pre[i] == ND] = np.nan
        prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=len(CH), dtype="int16",
                    crs=CFG.CRS_METRIC, transform=F["transform"], compress="deflate", predictor=2, tiled=True,
                    blockxsize=512, blockysize=128, nodata=ND, BIGTIFF="IF_SAFER")
        p = OUT / fid / "s2_sparse_support.tif"
        with rasterio.open(p.with_suffix(".tif.part"), "w", **prof) as dst:
            b = 0
            for dt, role in DATES.items():
                tag = dt.replace("-", "")[4:]
                ip = OUT / fid / "indices" / f"{dt}.tif"; vp = OUT / fid / "indices" / f"{dt}_valid.tif"
                if not ip.exists():
                    raise SystemExit(f"{fid}: {dt} missing -- the support dates must exist in every frame")
                with rasterio.open(ip) as s:
                    names = list(SP.INDEX_NAMES)
                    vals = {i: s.read(names.index(i) + 1).astype("f4") for i in IDX}
                    tags = s.tags()
                with rasterio.open(vp) as s:
                    val = (s.read(1) == 1)
                for i in IDX:
                    vals[i][vals[i] == ND] = np.nan
                    vals[i] /= SCALE
                inv.append(dict(frame=fid, date=dt, temporal_role=role, lineage=tags.get("lineage"),
                                n_safe=tags.get("n_safe"), valid_pct=round(100 * float(val.mean()), 2),
                                frame_km2=round(F["ny"] * F["nx"] * 1e-4, 1),
                                valid_km2=round(float(val.sum()) * 1e-4, 1)))
                for i in IDX:
                    b += 1
                    q = np.where(val & np.isfinite(vals[i]),
                                 np.clip(np.round(vals[i] * SCALE), -32767, 32767), FILL).astype("i2")
                    dst.write(q, b); dst.set_band_description(b, f"{i}_{tag}")
                for i in IDX:
                    b += 1
                    d = vals[i] - pre[i]
                    q = np.where(val & np.isfinite(d), np.clip(np.round(d * SCALE), -32767, 32767),
                                 FILL).astype("i2")
                    dst.write(q, b); dst.set_band_description(b, f"d{i}_{tag}")
                b += 1
                dst.write(val.astype("i2"), b); dst.set_band_description(b, f"valid_{tag}")
                sup.append(dict(frame=fid, date=dt, temporal_role=role,
                                n_pixels_no_obs=int((~val).sum()), n_pixels_1_obs=int(val.sum()),
                                n_pixels_2plus_obs=0,
                                pct_no_obs=round(100 * float((~val).mean()), 2)))
                del vals, val
            dst.update_tags(
                purpose="sparse DATED optical support for M6; NOT a peak composite and NOT a classifier",
                dates="|".join(f"{d}={r}" for d, r in DATES.items()),
                why_no_composite="only one Sentinel-2 acquisition (2023-06-08) falls inside the peak window "
                                 "2023-06-06..06-14, so min and max over time would be the same number",
                rising_limb="2023-06-08 precedes the Sentinel-1 water observations of 06-09, 06-13 and 06-14",
                date_choice="06-08 and 06-18 are the only acquisitions present in ALL three frames; per-frame "
                            "nearest dates would break the overlap invariant",
                missing="deterministic fill 0 with an explicit validity channel; absence is NEVER dry",
                producer="p72_s2_sparse_event_support.py")
        os.replace(p.with_suffix(".tif.part"), p)
        print(f"  {fid}: {len(CH)} channels, {p.stat().st_size/1e9:.2f} GB, {time.time()-t0:.0f}s", flush=True)
        del pre

    for A_, B_ in itertools.combinations(FR, 2):
        GA, GB = CG.frame_grid(A_), CG.frame_grid(B_)
        x0, x1 = max(GA["x0"], GB["x0"]), min(GA["x1"], GB["x1"])
        y0, y1 = max(GA["y0"], GB["y0"]), min(GA["y1"], GB["y1"])
        if x1 <= x0 or y1 <= y0:
            continue
        ws = []
        for f_ in (A_, B_):
            with rasterio.open(OUT / f_ / "s2_sparse_support.tif") as s:
                w = from_bounds(x0, y0, x1, y1, transform=s.transform)
            for v in (w.col_off, w.row_off, w.width, w.height):
                assert abs(v - round(v)) < 1e-9
            ws.append(Window(round(w.col_off), round(w.row_off), round(w.width), round(w.height)))
        nmis = ncom = 0
        with rasterio.open(OUT / A_ / "s2_sparse_support.tif") as sa, \
                rasterio.open(OUT / B_ / "s2_sparse_support.tif") as sb:
            for r0 in range(0, ws[0].height, 256):
                h = min(256, ws[0].height - r0)
                u = sa.read(window=Window(ws[0].col_off, ws[0].row_off + r0, ws[0].width, h))
                v = sb.read(window=Window(ws[1].col_off, ws[1].row_off + r0, ws[1].width, h))
                ncom += u[0].size; nmis += int((u != v).any(0).sum())
        orows.append(dict(pair=f"{A_}|{B_}", n_common=ncom, n_mismatch=nmis))
        print(f"  overlap {A_}|{B_}: {ncom:,} cells, {nmis:,} mismatch", flush=True)
    pd.DataFrame(inv).to_csv(CFG.TABLES / "p72_s2_inventory.csv", index=False)
    pd.DataFrame(sup).to_csv(CFG.TABLES / "p72_s2_support.csv", index=False)
    pd.DataFrame(orows).to_csv(CFG.TABLES / "p72_s2_overlap_qa.csv", index=False)
    bad = sum(r["n_mismatch"] for r in orows)
    man = dict(product="S2_SPARSE_EVENT_SUPPORT_v1", channels=CH, dates=DATES,
               role="support for an S1-driven peak segmentation; Sentinel-2 is not the backbone",
               peak_window="2023-06-06..2023-06-14", n_s2_acquisitions_in_peak_window=1,
               overlap_mismatches=int(bad),
               git=subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                                  text=True).stdout.strip())
    man["verdict"] = "PASS" if bad == 0 else "HOLD"
    (OUT / "p72_manifest.json").write_text(json.dumps(man, indent=2))
    print("\n" + pd.DataFrame(inv)[["frame", "date", "temporal_role", "valid_pct", "valid_km2"]].to_string(index=False))
    print(f"\nVERDICT: {man['verdict']}")
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
