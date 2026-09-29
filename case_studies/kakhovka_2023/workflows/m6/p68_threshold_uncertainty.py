# Provenance: SWOT-DNIPRO scripts/p68_threshold_uncertainty.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: ACTIVE -- M2 threshold envelope -> flood_core/central/possible.tif (cand_score >= T50 0.5358 for central); WorldCover used ONLY for strata tables, never in the masks.
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged, except
# 2026-09-29 (review F09/F10): `--tag` (e.g. _notrace) reads the equally tagged p65b fold table (inner out-of-fold
# thresholds) and cand_score, and writes every raster, table and manifest with the tag -- the untagged products behind the
# frozen v002/v003_A labels are never overwritten.
"""P68 -- how much of the mapped flood depends on where exactly the decision threshold was put.

THIS IS THRESHOLD SENSITIVITY, NOT A CONFIDENCE INTERVAL. The five thresholds come from the five outer folds of the
frozen estimator; their spread says how stable the DECISION RULE is across space, not how uncertain the flooded AREA
is. A genuine area-estimation uncertainty needs a probability reference sample and an error matrix (Olofsson et al.,
2014, SRC-80), which this study does not yet have. The phrase "95 % CI of flooded area" must not appear anywhere
these numbers are used; the phrase to use is "mapped-area sensitivity to the frozen decision threshold".

THE ENVELOPE IS THE FROZEN ESTIMATOR'S OWN POPULATION AND NOTHING ELSE: the per-fold thresholds of PRE_ALL under
BLOCK, the same five numbers whose median produced T50 = 0.5358. Thresholds from PRE_ALL/BUFFERED, from
PRE_SEASONAL, from PRE_ALL_NMATCH or from any other run are NOT mixed in, even though they exist and are wider --
mixing them would silently redefine the estimator after the fact.

    0.4667  0.5131  [0.5358]  0.6429  0.6636          min .. Q25 .. median .. Q75 .. max

Nothing is retrained, no feature is touched, PRE_ALL stays, and T50 is not moved.

CLASSES (never called probability classes):
    CORE               flood under the STRICTEST threshold in the envelope -- classification stable throughout
    UNCERTAIN          class changes inside the envelope -- threshold-sensitive
    NON_FLOOD_STABLE   below the most permissive threshold -- stable non-flood
    INVALID            insufficient prediction support

AREAS COME FROM THE DEDUPLICATED UNION. The frames overlap by 4 229 km2 and summing frame areas would inflate the
flooded area by about 56 % -- measured, not hypothetical.

Outputs: <frame>/thr_class.tif; outputs/tables/p68_threshold_{registry,area_sensitivity,spatial_summary,overlap_qa}.csv;
         $BULK_ROOT/frames10/p68_threshold_manifest.json
"""
from __future__ import annotations
import argparse, itertools, json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
from rasterio.windows import Window, from_bounds
from scipy import ndimage
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
FRAMES = ("B1", "B2", "B3")
SCORE_ND = 65535
SCALE = 10_000
PX = 1e-4
COARSE = 40.0
CLS = {0: "INVALID", 1: "NON_FLOOD_STABLE", 2: "UNCERTAIN", 3: "CORE"}
WCZ = {"B1": "ZONE_4_DAM_TO_KHERSON_FLOODWAY", "B2": "ZONE_2_KHERSON_DELTA", "B3": "ZONE_3_DNIPRO_BUG_ESTUARY"}
WC = {10: "tree", 20: "shrub", 30: "grass", 40: "cropland", 50: "built_up", 60: "bare_sand", 80: "water",
      90: "wetland"}
DBINS = [0, 100, 250, 500, 1000, 2500, 5000, np.inf]


def owner(fid, i):
    F = CG.frame_grid(fid)
    own = np.ones((F["ny"], F["nx"]), bool)
    for prev in FRAMES[:i]:
        GP = CG.frame_grid(prev)
        x0, x1 = max(F["x0"], GP["x0"]), min(F["x1"], GP["x1"])
        y0, y1 = max(F["y0"], GP["y0"]), min(F["y1"], GP["y1"])
        if x1 <= x0 or y1 <= y0:
            continue
        c0 = int(round((x0 - F["x0"]) / CG.CELL)); c1 = int(round((x1 - F["x0"]) / CG.CELL))
        r0 = int(round((F["y1"] - y1) / CG.CELL)); r1 = int(round((F["y1"] - y0) / CG.CELL))
        own[r0:r1, c0:c1] = False
    return own


def aligned_window(path, bnds):
    with rasterio.open(path) as s:
        w = from_bounds(*bnds, transform=s.transform)
    for v in (w.col_off, w.row_off, w.width, w.height):
        assert abs(v - round(v)) < 1e-9, f"{Path(path).name}: overlap window off-lattice"
    return Window(round(w.col_off), round(w.row_off), round(w.width), round(w.height))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=list(FRAMES))
    ap.add_argument("--tag", default="", help="variant tag of the p65b tables and the cand_score raster, e.g. _notrace"); a = ap.parse_args(); tag = a.tag
    # ---- the frozen threshold population, named and nothing else --------------------------------------------------
    f = pd.read_csv(CFG.TABLES / f"p65b_m2_folds{tag}.csv").query("baseline=='preall' and regime=='block'")
    thr = np.sort(f.threshold.values)
    T50 = float(np.median(thr)); TLO, THI = float(thr.min()), float(thr.max())
    reg = f[["baseline", "regime", "outer_fold", "threshold", "AP", "recall", "precision"]].copy()
    reg["role"] = ["envelope_member"] * len(reg)
    reg["estimator"] = "PRE_ALL / BLOCK, corrected run; the population whose median is T50"
    reg.to_csv(CFG.TABLES / f"p68_threshold_registry{tag}.csv", index=False)
    print(f"frozen threshold population (n={len(thr)}): {list(np.round(thr,4))}")
    print(f"  min {TLO:.4f}  Q25 {np.percentile(thr,25):.4f}  median(T50) {T50:.4f}  "
          f"Q75 {np.percentile(thr,75):.4f}  max {THI:.4f}")
    print(f"  CORE = score >= {THI:.4f} (strictest)   NON_FLOOD_STABLE = score < {TLO:.4f} (most permissive)\n",
          flush=True)
    qlo, q50, qhi = int(round(TLO * SCALE)), int(round(T50 * SCALE)), int(round(THI * SCALE))

    area, spat = [], []
    for i, fid in enumerate(a.frames):
        F = CG.frame_grid(fid)
        own = owner(fid, FRAMES.index(fid))
        with rasterio.open(OUT / fid / f"cand_score{tag}.tif") as s:
            sc = s.read(1)
        valid = sc != SCORE_ND
        cls = np.zeros((F["ny"], F["nx"]), np.uint8)
        cls[valid] = 1
        cls[valid & (sc >= qlo)] = 2
        cls[valid & (sc >= qhi)] = 3
        prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=1, dtype="uint8", crs=CFG.CRS_METRIC,
                    transform=F["transform"], compress="deflate", tiled=True, blockxsize=512, blockysize=512,
                    nodata=255, BIGTIFF="IF_SAFER")
        p = OUT / fid / f"thr_class{tag}.tif"
        with rasterio.open(p.with_suffix(".tif.part"), "w", **prof) as d:
            d.write(cls, 1); d.set_band_description(1, "threshold_class")
            d.update_tags(classes="|".join(f"{k}={v}" for k, v in CLS.items()),
                          envelope=f"{TLO:.4f}..{THI:.4f}", central=f"{T50:.4f}",
                          estimator="PRE_ALL/BLOCK per-fold thresholds of the corrected run",
                          semantics="THRESHOLD SENSITIVITY, not a confidence interval for flooded area",
                          producer="p68_threshold_uncertainty.py")
        os.replace(p.with_suffix(".tif.part"), p)

        # ---- the four binary products, each its own raster ----------------------------------------------------------
        # thr_class alone cannot answer "which cells are flood at T50": its classes are built from the envelope ends,
        # so the CENTRAL map is not recoverable from it. Each decision gets its own layer, 1 = flood, 0 = not,
        # 255 = no prediction support.
        bprof = dict(prof)
        for nm, q in (("flood_core", qhi), ("flood_central", q50), ("flood_possible", qlo)):
            arr = np.full((F["ny"], F["nx"]), 255, np.uint8)
            arr[valid] = (sc[valid] >= q).astype(np.uint8)
            bp = OUT / fid / f"{nm}{tag}.tif"
            with rasterio.open(bp.with_suffix(".tif.part"), "w", **bprof) as d:
                d.write(arr, 1); d.set_band_description(1, nm)
                d.update_tags(threshold=f"{q/SCALE:.4f}", model="M2_PRODUCTION_CANDIDATE_CORRECTED10M" + tag.upper(),
                              semantics="1 = mapped flood at this threshold; 255 = no prediction support. "
                                        "THRESHOLD SENSITIVITY, not a probability and not a confidence interval",
                              envelope=f"{TLO:.4f}..{THI:.4f}", central=f"{T50:.4f}",
                              producer="p68_threshold_uncertainty.py")
            os.replace(bp.with_suffix(".tif.part"), bp)
            del arr
        arr = np.full((F["ny"], F["nx"]), 255, np.uint8)
        arr[valid] = ((sc[valid] >= qlo) & (sc[valid] < qhi)).astype(np.uint8)
        bp = OUT / fid / f"threshold_uncertain{tag}.tif"
        with rasterio.open(bp.with_suffix(".tif.part"), "w", **bprof) as d:
            d.write(arr, 1); d.set_band_description(1, "threshold_uncertain")
            d.update_tags(semantics="1 = the flood/non-flood decision CHANGES inside the frozen threshold envelope",
                          envelope=f"{TLO:.4f}..{THI:.4f}", producer="p68_threshold_uncertainty.py")
        os.replace(bp.with_suffix(".tif.part"), bp)
        del arr

        # ---- areas at EVERY threshold of the envelope, on owned cells only ----------------------------------------
        for t in thr:
            q = int(round(t * SCALE))
            km2 = float(((sc >= q) & valid & own).sum()) * PX
            area.append(dict(frame=fid, threshold=round(float(t), 4), mapped_flood_km2=round(km2, 2),
                             is_central=bool(abs(t - T50) < 1e-9)))
        # ---- spatial strata of the threshold-sensitive band --------------------------------------------------------
        with rasterio.open(OUT / fid / "labels.tif") as s:
            wf = s.read(list(s.descriptions).index("pre_water_frac") + 1).astype("f4")
        prew = wf >= 20.0
        ny_c = int(np.ceil(F["ny"] * CG.CELL / COARSE)); nx_c = int(np.ceil(F["nx"] * CG.CELL / COARSE))
        small = prew[::int(COARSE // CG.CELL), ::int(COARSE // CG.CELL)][:ny_c, :nx_c]
        dist_c = ndimage.distance_transform_edt(~small, sampling=COARSE).astype("f4")
        dist = np.repeat(np.repeat(dist_c, int(COARSE // CG.CELL), 0), int(COARSE // CG.CELL), 1)[:F["ny"], :F["nx"]]
        wcp = CFG.BULK_ROOT / "worldcover_frames" / WCZ[fid] / "wc_2021_20m.tif"
        wc = np.zeros((F["ny"], F["nx"]), "u1")
        if wcp.exists():
            with rasterio.open(wcp) as s:
                reproject(source=s.read(1), destination=wc, src_transform=s.transform, src_crs=s.crs,
                          dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest,
                          src_nodata=0, dst_nodata=0)
        base = own & valid
        for lo, hi in zip(DBINS[:-1], DBINS[1:]):
            m = base & (dist >= lo) & (dist < hi)
            if not m.any():
                continue
            spat.append(dict(frame=fid, stratum="distance_to_pre_water_m", bin=f"{lo:.0f}-{hi:.0f}",
                             area_km2=round(float(m.sum()) * PX, 1),
                             core_km2=round(float((cls[m] == 3).sum()) * PX, 2),
                             uncertain_km2=round(float((cls[m] == 2).sum()) * PX, 2),
                             uncertain_share_of_flood_pct=round(
                                 100 * float((cls[m] == 2).sum()) / max(float((cls[m] >= 2).sum()), 1), 2)))
        for code, nm in WC.items():
            m = base & (wc == code)
            if not m.any():
                continue
            spat.append(dict(frame=fid, stratum="worldcover", bin=nm, area_km2=round(float(m.sum()) * PX, 1),
                             core_km2=round(float((cls[m] == 3).sum()) * PX, 2),
                             uncertain_km2=round(float((cls[m] == 2).sum()) * PX, 2),
                             uncertain_share_of_flood_pct=round(
                                 100 * float((cls[m] == 2).sum()) / max(float((cls[m] >= 2).sum()), 1), 2)))
        n = {k: float(((cls == k) & own).sum()) * PX for k in CLS}
        spat.append(dict(frame=fid, stratum="frame_total", bin="owned",
                         area_km2=round(float(own.sum()) * PX, 1), core_km2=round(n[3], 2),
                         uncertain_km2=round(n[2], 2),
                         uncertain_share_of_flood_pct=round(100 * n[2] / max(n[3] + n[2], 1e-9), 2)))
        print(f"  {fid}: CORE {n[3]:,.1f} km2, UNCERTAIN {n[2]:,.1f} km2, STABLE NON-FLOOD {n[1]:,.0f} km2, "
              f"INVALID {n[0]:,.1f} km2 (owned {own.sum()*PX:,.0f} km2)", flush=True)
        del sc, cls, valid, own, dist, wc, prew, wf

        area.append(dict(frame=fid, threshold=np.nan, mapped_flood_km2=np.nan, is_central=False,
                         stable_flood_km2=round(n[3], 2), threshold_sensitive_km2=round(n[2], 2),
                         stable_nonflood_km2=round(n[1], 2), invalid_km2=round(n[0], 2)))

    A = pd.DataFrame(area)
    tot = A.groupby("threshold").mapped_flood_km2.sum().reset_index()
    c = float(tot[np.isclose(tot.threshold, T50)].mapped_flood_km2.iloc[0])
    tot["delta_from_central_km2"] = (tot.mapped_flood_km2 - c).round(2)
    tot["delta_percent"] = (100 * (tot.mapped_flood_km2 - c) / c).round(2)
    tot["is_central"] = np.isclose(tot.threshold, T50)
    sm = A[A.threshold.isna()]
    # `col`, not `c`: `c` already holds the central-threshold area and reusing the name shadowed a float with a
    # column name, which only surfaced three statements later inside round().
    for col in ("stable_flood_km2", "threshold_sensitive_km2", "stable_nonflood_km2", "invalid_km2"):
        tot[col] = round(float(sm[col].sum()), 2)   # union totals, identical on every row: they are envelope-wide
    tot.to_csv(CFG.TABLES / f"p68_threshold_area_sensitivity{tag}.csv", index=False)
    S = pd.DataFrame(spat); S.to_csv(CFG.TABLES / f"p68_threshold_spatial_summary{tag}.csv", index=False)

    # ---- the overlap invariant, on the new product ------------------------------------------------------------------
    orows = []; bad = 0
    for A_, B_ in itertools.combinations(FRAMES, 2):
        GA, GB = CG.frame_grid(A_), CG.frame_grid(B_)
        x0, x1 = max(GA["x0"], GB["x0"]), min(GA["x1"], GB["x1"])
        y0, y1 = max(GA["y0"], GB["y0"]), min(GA["y1"], GB["y1"])
        if x1 <= x0 or y1 <= y0:
            continue
        for prod in ("thr_class", "flood_core", "flood_central", "flood_possible", "threshold_uncertain"):
            pa, pb = OUT / A_ / f"{prod}{tag}.tif", OUT / B_ / f"{prod}{tag}.tif"
            wa, wb = aligned_window(pa, (x0, y0, x1, y1)), aligned_window(pb, (x0, y0, x1, y1))
            nmis = 0; ncom = 0
            with rasterio.open(pa) as sa, rasterio.open(pb) as sb:
                for r0 in range(0, wa.height, 512):
                    h = min(512, wa.height - r0)
                    u = sa.read(1, window=Window(wa.col_off, wa.row_off + r0, wa.width, h))
                    v = sb.read(1, window=Window(wb.col_off, wb.row_off + r0, wb.width, h))
                    ncom += u.size; nmis += int((u != v).sum())
            orows.append(dict(pair=f"{A_}|{B_}", product=prod, n_common=ncom, n_mismatch=nmis))
            bad += nmis
            print(f"  overlap {A_}|{B_} {prod:20s}: {ncom:,} cells, {nmis:,} mismatch", flush=True)
    pd.DataFrame(orows).to_csv(CFG.TABLES / f"p68_threshold_overlap_qa{tag}.csv", index=False)

    st = S[S.stratum == "frame_total"]
    meta = dict(product="M2_THRESHOLD_SENSITIVITY_v1", model="M2_PRODUCTION_CANDIDATE_CORRECTED10M",
                semantics="mapped-area sensitivity to the frozen decision threshold; NOT a confidence interval "
                          "for flooded area and NOT a probability",
                estimator="per-fold thresholds of PRE_ALL under BLOCK, corrected run",
                n_thresholds=int(len(thr)), thresholds=[round(float(x), 4) for x in thr],
                threshold_min=round(TLO, 4), threshold_q25=round(float(np.percentile(thr, 25)), 4),
                threshold_median_T50=round(T50, 4), threshold_q75=round(float(np.percentile(thr, 75)), 4),
                threshold_max=round(THI, 4),
                not_mixed_in=["PRE_ALL/BUFFERED", "PRE_SEASONAL", "PRE_ALL_NMATCH", "B3 results"],
                union_core_km2=round(float(st.core_km2.sum()), 2),
                union_uncertain_km2=round(float(st.uncertain_km2.sum()), 2),
                union_flood_at_central_km2=round(c, 2),
                union_flood_at_min_threshold_km2=round(float(tot.mapped_flood_km2.max()), 2),
                union_flood_at_max_threshold_km2=round(float(tot.mapped_flood_km2.min()), 2),
                overlap_mismatches=int(bad),
                git=subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                                   text=True).stdout.strip())
    meta["verdict"] = "PASS" if bad == 0 else "HOLD"
    (OUT / f"p68_threshold_manifest{tag}.json").write_text(json.dumps(meta, indent=2))
    print("\n=== MAPPED-AREA SENSITIVITY TO THE FROZEN DECISION THRESHOLD (deduplicated union) ===")
    print(tot.to_string(index=False))
    print(f"\nVERDICT: {meta['verdict']}")
    print("-> outputs/tables/p68_threshold_{registry,area_sensitivity,spatial_summary,overlap_qa}.csv")
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
