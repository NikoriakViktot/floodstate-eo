# Provenance: SWOT-DNIPRO scripts/p69a_base_class.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 14 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo; `git rev-parse` now runs against this repo.
# NOTE FOR docs/METHODS.md and docs/DATA_DICTIONARY.md: this is the real, frozen implementation of BASE_CLASS --
# the 2026-09-21 planning audit that first drafted the migration docs predates this script and states "BASE_CLASS
# is PROPOSED / NOT YET CANONICAL"; that claim is now only half true (see 00_EXECUTIVE_SUMMARY.md addendum).
"""P69a -- BASE_CLASS: what the pixel WAS before the breach. Frozen independently of any flood evidence.

PROVENANCE IS THE POINT OF THIS FILE. BASE_CLASS describes the pre-event land state and must not know anything about
whether the pixel flooded, so that combining it with the frozen M2 evidence later is a genuine combination of two
independent statements rather than a restatement of one.

ALLOWED, and all that is read here:
  * PRE-window Sentinel-2 statistics from composite_preall.tif -- ONLY the `*_pre_*` bands and n_obs_pre
  * pre-breach Sentinel-2 water frequency, PRE_BREACH-regime per-zone rasters (30 dates)
  * WorldCover 2021, an external land-cover product that predates the June 2023 breach
  * the frozen canonical 10 m lattice

FORBIDDEN, and never opened by this script: EVENT or TRACE bands, the M2 score or class, the June-2023 Sentinel-1
masks, the weak-reference labels, HAND, UNOSAT. There was no pre-existing BASE_CLASS product to audit -- none had
ever been built -- so nothing needed repairing.

NO THRESHOLD IS INVENTED HERE. Every cut is one already frozen elsewhere for other purposes and none was chosen by
looking at flood output: NDVI 0.15/0.30, NDMI 0.10, BSI 0.10 from `sentinel_preprocess` (the k10e surface scheme),
NDWI/MNDWI at 0 from `watermask` (the frozen water rule), and the 20 % pre-breach water frequency from the weak-label
rule.

ANCILLARY LAYERS ARE SAMPLED IN A FIXED GLOBAL ORDER, not per frame. WorldCover and the water frequency exist as
FOUR per-zone rasters; if each frame simply used "its own" zone, the same ground could take its value from a
different source in B1 than in B2 and the overlap invariant would break through the ancillary path rather than
through the model. Every zone raster is therefore projected onto every frame and resolved first-valid in the fixed
order ZONE_1, ZONE_2, ZONE_3, ZONE_4, so a given cell is decided by the same source whichever frame reads it.

Outputs: <frame>/p69a_base_class.tif; <case_study>/tables/p69a_base_class_{registry,area}.csv, p69a_overlap_qa.csv;
         $BULK_ROOT/frames10/p69a_semantic_contract.json
"""
from __future__ import annotations
import argparse, itertools, json, os, subprocess, sys
from pathlib import Path
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
from rasterio.windows import Window, from_bounds
from .. import _kakhovka_legacy_config as CFG
from ..spatial import canonical_grid as CG
from ..optical import sentinel_preprocess as SP
from ..optical import watermask as WM

OUT = CFG.BULK_ROOT / "frames10"
FRAMES = ("B1", "B2", "B3")
ZONES = ("ZONE_1_KAKHOVKA_LOWER_DNIPRO", "ZONE_2_KHERSON_DELTA", "ZONE_3_DNIPRO_BUG_ESTUARY",
         "ZONE_4_DAM_TO_KHERSON_FLOODWAY")
ZNUM = {"ZONE_1_KAKHOVKA_LOWER_DNIPRO": 1, "ZONE_2_KHERSON_DELTA": 2, "ZONE_3_DNIPRO_BUG_ESTUARY": 3,
        "ZONE_4_DAM_TO_KHERSON_FLOODWAY": 4}
ND = SP.INDEX_NODATA
PX = 1e-4
PRE_WF_WATER = 20.0        # frozen with the weak-label rule
MIN_OBS_PRE = 3            # below this the pre-event state is not established; the cell is UNCERTAIN, never guessed
CLASSES = {0: "PRE_EXISTING_WATER", 1: "VEGETATION_AGRICULTURE", 2: "BARE_SAND", 3: "BUILT_UP_URBAN",
           4: "WETLAND_MIXED", 5: "OTHER_DRY", 6: "UNCERTAIN", 255: "INVALID"}
WC_BUILT, WC_BARE, WC_WET = 50, 60, 90
WC_VEG = (10, 20, 30, 40, 95, 100)


def onto(frame, src_path, band=1, nodata=0, dtype="f4", resampling=Resampling.nearest):
    F = CG.frame_grid(frame)
    dst = np.full((F["ny"], F["nx"]), nodata, dtype)
    with rasterio.open(src_path) as s:
        a = s.read(band)
        sn = s.nodata
        reproject(source=a.astype(dtype), destination=dst, src_transform=s.transform, src_crs=s.crs,
                  dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC, resampling=resampling,
                  src_nodata=sn if sn is not None else nodata, dst_nodata=nodata)
    return dst


def ancillary(frame, kind):
    """First valid in the FIXED order ZONE_1..ZONE_4, so the winning source never depends on which frame reads it."""
    F = CG.frame_grid(frame)
    out = np.full((F["ny"], F["nx"]), np.nan, "f4")
    who = np.zeros((F["ny"], F["nx"]), "u1")
    for z in ZONES:
        p = (CFG.BULK_ROOT / "worldcover_frames" / z / "wc_2021_20m.tif" if kind == "wc"
             else CFG.REPO_ROOT / "case_studies/kakhovka_2023" /
             f"outputs/rasters/zone{ZNUM[z]}/zone{ZNUM[z]}_water_frac_PRE_BREACH_20m.tif")
        if not p.exists():
            continue
        v = onto(frame, p, nodata=np.nan, dtype="f4")
        if kind == "wf":
            v[v == 255] = np.nan                      # 255 = never observed in the source encoding
        else:
            v[v == 0] = np.nan
        take = np.isnan(out) & np.isfinite(v)
        out[take] = v[take]; who[take] = ZNUM[z]
    return out, who


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=list(FRAMES)); a = ap.parse_args()
    PRE = [f"{i}_pre_med" for i in list(SP.INDEX_NAMES) + ["NDBI"]]
    print("BASE_CLASS -- PRE-event only. Reading: composite *_pre_* bands, PRE_BREACH water frequency, "
          "WorldCover 2021.\nNever opened: EVENT/TRACE bands, M2 score, S1 June masks, weak labels, HAND, UNOSAT.\n",
          flush=True)
    areas, orows = [], []
    for fid in a.frames:
        F = CG.frame_grid(fid)
        with rasterio.open(OUT / fid / "composite_preall.tif") as s:
            cn = list(s.descriptions)
            assert all(("_event_" not in n and "_trace_" not in n) for n in PRE), "forbidden window in the PRE list"
            idx = {n: s.read(cn.index(n) + 1).astype("f4") for n in PRE}
            nobs = s.read(cn.index("n_obs_pre") + 1)
        for k in idx:
            idx[k][idx[k] == ND] = np.nan
            idx[k] /= SP.INDEX_SCALE
        wf, wf_src = ancillary(fid, "wf")
        wc, wc_src = ancillary(fid, "wc")
        wc_i = np.where(np.isfinite(wc), np.nan_to_num(wc, nan=0).astype("i4"), 0)

        ndvi, ndwi, mndwi = idx["NDVI_pre_med"], idx["NDWI_pre_med"], idx["MNDWI_pre_med"]
        ndmi, bsi = idx["NDMI_pre_med"], idx["BSI_pre_med"]
        cls = np.full((F["ny"], F["nx"]), 255, np.uint8)
        valid = np.isfinite(ndvi) & np.isfinite(ndwi) & np.isfinite(mndwi) & (nobs > 0)
        cls[valid] = 6                                                   # UNCERTAIN until a rule claims the cell
        enough = valid & (nobs >= MIN_OBS_PRE)
        water = enough & ((np.nan_to_num(wf, nan=-1) >= PRE_WF_WATER) |
                          ((ndwi > WM.DEFAULT_NDWI) & (mndwi > WM.DEFAULT_MNDWI)))
        cls[enough & (wc_i == WC_BUILT)] = 3
        cls[enough & (wc_i == WC_WET)] = 4
        cls[enough & ((wc_i == WC_BARE) | ((bsi >= SP.BSI_BARE) & (ndvi < SP.NDVI_SPARSE) &
                                           (ndmi < SP.NDMI_WET)))] = 2
        veg = enough & ((ndvi >= SP.NDVI_SPARSE) | np.isin(wc_i, WC_VEG))
        cls[veg & (cls == 6)] = 1
        cls[enough & (cls == 6)] = 5                                     # valid, supported, claimed by nothing
        cls[water] = 0                                                   # water wins: it is the least ambiguous state
        prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=1, dtype="uint8", crs=CFG.CRS_METRIC,
                    transform=F["transform"], compress="deflate", tiled=True, blockxsize=512, blockysize=512,
                    nodata=255, BIGTIFF="IF_SAFER")
        p = OUT / fid / "p69a_base_class.tif"
        with rasterio.open(p.with_suffix(".tif.part"), "w", **prof) as d:
            d.write(cls, 1); d.set_band_description(1, "base_class")
            d.update_tags(classes="|".join(f"{k}={v}" for k, v in CLASSES.items()),
                          describes="the PRE-BREACH land state; it says NOTHING about whether the pixel flooded",
                          allowed_inputs="composite *_pre_med bands; n_obs_pre; PRE_BREACH water frequency; "
                                         "WorldCover 2021",
                          forbidden_inputs_not_read="EVENT/TRACE bands; M2 score or class; S1 June 2023 masks; "
                                                    "weak-reference labels; HAND; UNOSAT",
                          thresholds=f"NDVI {SP.NDVI_SPARSE}/{SP.NDVI_VEG}; NDMI {SP.NDMI_WET}; BSI {SP.BSI_BARE}; "
                                     f"NDWI/MNDWI {WM.DEFAULT_NDWI}; pre water frequency {PRE_WF_WATER} %; "
                                     f"min n_obs_pre {MIN_OBS_PRE}",
                          threshold_provenance="all frozen previously for other purposes; none chosen by inspecting "
                                               "flood results",
                          ancillary_resolution="first valid in the fixed order ZONE_1..ZONE_4, identical in every "
                                               "frame", producer="p69a_base_class.py")
        os.replace(p.with_suffix(".tif.part"), p)
        own = np.ones((F["ny"], F["nx"]), bool)
        for prev in FRAMES[:FRAMES.index(fid)]:
            GP = CG.frame_grid(prev)
            x0, x1 = max(F["x0"], GP["x0"]), min(F["x1"], GP["x1"])
            y0, y1 = max(F["y0"], GP["y0"]), min(F["y1"], GP["y1"])
            if x1 <= x0 or y1 <= y0:
                continue
            c0 = int(round((x0 - F["x0"]) / CG.CELL)); c1 = int(round((x1 - F["x0"]) / CG.CELL))
            r0 = int(round((F["y1"] - y1) / CG.CELL)); r1 = int(round((F["y1"] - y0) / CG.CELL))
            own[r0:r1, c0:c1] = False
        for k, nm in CLASSES.items():
            n_all = int((cls == k).sum()); n_own = int(((cls == k) & own).sum())
            areas.append(dict(frame=fid, code=k, base_class=nm, km2_frame=round(n_all * PX, 2),
                              km2_owned=round(n_own * PX, 2),
                              pct_of_owned=round(100 * n_own / max(int(own.sum()), 1), 3)))
        print(f"  {fid}: " + ", ".join(f"{CLASSES[k]} {((cls==k)&own).sum()*PX:,.0f}" for k in (0, 1, 2, 3, 4, 5, 6))
              + " km2 (owned)", flush=True)
        del idx, cls, wf, wc, wc_i, valid, enough, water, veg, own

    # ---- overlap invariant -----------------------------------------------------------------------------------------
    bad = 0
    for A_, B_ in itertools.combinations(FRAMES, 2):
        GA, GB = CG.frame_grid(A_), CG.frame_grid(B_)
        x0, x1 = max(GA["x0"], GB["x0"]), min(GA["x1"], GB["x1"])
        y0, y1 = max(GA["y0"], GB["y0"]), min(GA["y1"], GB["y1"])
        if x1 <= x0 or y1 <= y0:
            continue
        ws = []
        for f_ in (A_, B_):
            with rasterio.open(OUT / f_ / "p69a_base_class.tif") as s:
                w = from_bounds(x0, y0, x1, y1, transform=s.transform)
            for v in (w.col_off, w.row_off, w.width, w.height):
                assert abs(v - round(v)) < 1e-9, f"{f_}: overlap window off-lattice"
            ws.append(Window(round(w.col_off), round(w.row_off), round(w.width), round(w.height)))
        nmis = ncom = 0
        with rasterio.open(OUT / A_ / "p69a_base_class.tif") as sa, \
                rasterio.open(OUT / B_ / "p69a_base_class.tif") as sb:
            for r0 in range(0, ws[0].height, 512):
                h = min(512, ws[0].height - r0)
                u = sa.read(1, window=Window(ws[0].col_off, ws[0].row_off + r0, ws[0].width, h))
                v = sb.read(1, window=Window(ws[1].col_off, ws[1].row_off + r0, ws[1].width, h))
                ncom += u.size; nmis += int((u != v).sum())
        orows.append(dict(pair=f"{A_}|{B_}", n_common=ncom, n_mismatch=nmis))
        bad += nmis
        print(f"  overlap {A_}|{B_}: {ncom:,} cells, {nmis:,} mismatch", flush=True)

    reg = [dict(code=0, base_class="PRE_EXISTING_WATER", type="HYBRID",
                inputs="PRE_BREACH water frequency; NDWI_pre_med; MNDWI_pre_med",
                window="pre-breach only", rule="water_frac >= 20 % OR (NDWI_pre_med > 0 AND MNDWI_pre_med > 0)",
                thresholds=f"20 %; {WM.DEFAULT_NDWI}; {WM.DEFAULT_MNDWI}",
                provenance="30 pre-breach dates + frozen water rule"),
           dict(code=1, base_class="VEGETATION_AGRICULTURE", type="HYBRID", inputs="NDVI_pre_med; WorldCover 2021",
                window="pre-breach only", rule="NDVI_pre_med >= 0.15 OR WorldCover in (10,20,30,40,95,100)",
                thresholds=f"NDVI {SP.NDVI_SPARSE}", provenance="k10e surface scheme + ESA WorldCover 2021"),
           dict(code=2, base_class="BARE_SAND", type="HYBRID", inputs="WorldCover 2021; BSI/NDVI/NDMI_pre_med",
                window="pre-breach only",
                rule="WorldCover == 60 OR (BSI >= 0.10 AND NDVI < 0.15 AND NDMI < 0.10)",
                thresholds=f"BSI {SP.BSI_BARE}; NDVI {SP.NDVI_SPARSE}; NDMI {SP.NDMI_WET}",
                provenance="ESA WorldCover 2021 + k10e DRY_BARE_SEDIMENT rule"),
           dict(code=3, base_class="BUILT_UP_URBAN", type="EXTERNAL_LC", inputs="WorldCover 2021",
                window="2021, pre-breach", rule="WorldCover == 50", thresholds="none",
                provenance="ESA WorldCover 2021. NDBI is NOT used as ground truth for built-up"),
           dict(code=4, base_class="WETLAND_MIXED", type="EXTERNAL_LC", inputs="WorldCover 2021",
                window="2021, pre-breach", rule="WorldCover == 90", thresholds="none",
                provenance="ESA WorldCover 2021 herbaceous wetland"),
           dict(code=5, base_class="OTHER_DRY", type="RULE_BASED", inputs="all of the above",
                window="pre-breach only", rule="valid, supported, claimed by no other class", thresholds="none",
                provenance="residual class"),
           dict(code=6, base_class="UNCERTAIN", type="RULE_BASED", inputs="n_obs_pre",
                window="pre-breach only", rule=f"valid pixel but n_obs_pre < {MIN_OBS_PRE}",
                thresholds=f"n_obs_pre {MIN_OBS_PRE}",
                provenance="insufficient pre-event support; the state is not established and is not guessed"),
           dict(code=255, base_class="INVALID", type="RULE_BASED", inputs="composite PRE bands; n_obs_pre",
                window="pre-breach only", rule="a required PRE index is NODATA or n_obs_pre == 0",
                thresholds="none", provenance="no pre-event observation at all")]
    pd.DataFrame(reg).to_csv(CFG.TABLES / "p69a_base_class_registry.csv", index=False)
    A = pd.DataFrame(areas); A.to_csv(CFG.TABLES / "p69a_base_class_area.csv", index=False)
    pd.DataFrame(orows).to_csv(CFG.TABLES / "p69a_overlap_qa.csv", index=False)
    u = A.groupby(["code", "base_class"]).km2_owned.sum().reset_index().sort_values("km2_owned", ascending=False)
    contract = dict(product="BASE_CLASS_v1", describes="pre-breach land state",
                    says_nothing_about="whether the pixel flooded",
                    classes={str(k): v for k, v in CLASSES.items()},
                    allowed_inputs=["composite *_pre_med bands", "n_obs_pre", "PRE_BREACH water frequency",
                                    "WorldCover 2021", "frozen canonical 10 m lattice"],
                    forbidden_inputs_not_read=["EVENT bands", "TRACE bands", "M2 score/class", "S1 June 2023 masks",
                                               "weak-reference labels", "HAND", "UNOSAT"],
                    pre_existing_base_class_audited="none existed; nothing to repair",
                    thresholds_all_previously_frozen=True,
                    ancillary_conflict_rule="first valid in the fixed order ZONE_1..ZONE_4, frame-independent",
                    union_km2={r.base_class: float(r.km2_owned) for r in u.itertuples()},
                    overlap_mismatches=int(bad),
                    git=subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=CFG.REPO_ROOT,
                                       capture_output=True, text=True).stdout.strip())
    contract["verdict"] = "PASS" if bad == 0 else "HOLD"
    (OUT / "p69a_semantic_contract.json").write_text(json.dumps(contract, indent=2))
    print("\n=== BASE_CLASS on the deduplicated union ===")
    print(u.to_string(index=False))
    print(f"\nVERDICT: {contract['verdict']}")
    print("-> <case_study>/tables/p69a_base_class_{registry,area}.csv, p69a_overlap_qa.csv")
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
