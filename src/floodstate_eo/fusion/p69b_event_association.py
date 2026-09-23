# Provenance: SWOT-DNIPRO scripts/p69b_event_association.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 15 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo.
"""P69b -- what happened to a surface whose PRE-event state is already frozen. Two axes, kept apart.

    BASE_CLASS (p69a, PRE only)  +  M2 CENTRAL decision (p67b/p68, frozen)  ->  semantic_state
    the frozen p68 masks                                                   ->  decision_stability5

NOTHING NEW IS ESTIMATED. No S1, no HAND, no UNOSAT, no new threshold, no change to BASE_CLASS and no change to the
M2 threshold. Both products are derived views of layers that are already frozen.

THE NAME IS DELIBERATELY WEAKER THAN "FLOOD". M2 and BASE_CLASS together support the statement "this surface was X
before the breach and shows an optical event response classified as flood-associated" -- they do not independently
prove open water stood on it. Hence FLOOD_ASSOCIATED_*, and no OPEN_FLOOD class until texture and an independent
reference exist (flooded-vegetation user accuracy has been raised from ~17 % to 78 % elsewhere by adding both).

PRE-EXISTING WATER IS NEVER FLOOD-ASSOCIATED, AND NEVER DISCARDED. A cell whose pre-breach state is water keeps that
semantic state whatever M2 says, so seasonal movement of the liman shoreline cannot enter the headline area as new
water. Its M2 score, its decision stability and its area are still reported -- as a separate diagnostic, because
p68 found 220.5 km2 of threshold-sensitive response sitting on exactly this class.

THE HEADLINE NUMBER CHANGES MEANING HERE. 414.92 km2 is the RAW M2 central mapped response. The quantity that
belongs in a flood statement is

    A(new-land) = M2 central AND BASE_CLASS != PRE_EXISTING_WATER

decomposed by pre-event surface. Both are reported, and the raw figure is never presented as flood-associated land.

DECISION STABILITY GETS ITS FIVE STATES BACK. p68's thr_class merged CENTRAL_ONLY with POSSIBLE_ONLY into one
UNCERTAIN class, which loses the distinction between "flood at the central threshold but not at the strictest" and
"flood only at the most permissive". Everything needed was already stored, so this is a re-view of frozen masks and
not a recomputation.

Outputs: <frame>/p69b_semantic_state.tif, p69b_decision_stability5.tif;
         <case_study>/tables/p69b_{base_x_stability,semantic_x_stability,area_accounting,overlap_qa}.csv;
         $BULK_ROOT/frames10/p69b_manifest.json
"""
from __future__ import annotations
import argparse, itertools, json, os, subprocess, sys
from pathlib import Path
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.windows import Window, from_bounds
from .. import _kakhovka_legacy_config as CFG
from ..spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
FRAMES = ("B1", "B2", "B3")
PX = 1e-4
BASE = {0: "PRE_EXISTING_WATER", 1: "VEGETATION_AGRICULTURE", 2: "BARE_SAND", 3: "BUILT_UP_URBAN",
        4: "WETLAND_MIXED", 5: "OTHER_DRY", 6: "UNCERTAIN", 255: "INVALID"}
SEM = {0: "PRE_EXISTING_WATER", 1: "FLOOD_ASSOCIATED_VEGETATION_AGRICULTURE",
       2: "FLOOD_ASSOCIATED_WETLAND_MIXED", 3: "FLOOD_ASSOCIATED_BUILT_UP", 4: "FLOOD_ASSOCIATED_BARE_SAND",
       5: "FLOOD_ASSOCIATED_OTHER_DRY", 6: "NON_FLOODED", 7: "UNCERTAIN_BASE_STATE", 255: "INVALID"}
STAB = {1: "CORE", 2: "CENTRAL_ONLY", 3: "POSSIBLE_ONLY", 4: "STABLE_NON_FLOOD", 255: "INVALID"}
BASE2SEM = {1: 1, 4: 2, 3: 3, 2: 4, 5: 5}          # pre-event surface -> its flood-associated counterpart


def read(fid, name, band=1):
    with rasterio.open(OUT / fid / name) as s:
        return s.read(band)


def owner(fid):
    F = CG.frame_grid(fid)
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
    return own


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=list(FRAMES)); a = ap.parse_args()
    bxs, sxs, acc, orows = [], [], [], []
    for fid in a.frames:
        F = CG.frame_grid(fid)
        bc = read(fid, "p69a_base_class.tif")
        core = read(fid, "flood_core.tif"); cen = read(fid, "flood_central.tif"); pos = read(fid, "flood_possible.tif")
        val = read(fid, "cand_valid.tif")
        sc = read(fid, "cand_score.tif")
        own = owner(fid)

        # ---- A. five-state decision stability, a view of the frozen masks ------------------------------------------
        stab = np.full((F["ny"], F["nx"]), 255, np.uint8)
        ok = val == 1
        stab[ok & (pos == 0)] = 4
        stab[ok & (pos == 1) & (cen == 0)] = 3
        stab[ok & (cen == 1) & (core == 0)] = 2
        stab[ok & (core == 1)] = 1

        # ---- B. semantic state, M2 CENTRAL only --------------------------------------------------------------------
        sem = np.full((F["ny"], F["nx"]), 255, np.uint8)
        flood = ok & (cen == 1)
        sem[ok & (bc != 255)] = 6                                    # NON_FLOODED until a rule claims otherwise
        for b, s_ in BASE2SEM.items():
            sem[flood & (bc == b)] = s_
        sem[ok & (bc == 6)] = 7                                      # the pre-event state was never established
        sem[ok & (bc == 0)] = 0                                      # pre-existing water wins over any M2 response
        sem[~ok | (bc == 255)] = 255

        for arr, nm, lut in ((sem, "p69b_semantic_state", SEM), (stab, "p69b_decision_stability5", STAB)):
            prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=1, dtype="uint8", crs=CFG.CRS_METRIC,
                        transform=F["transform"], compress="deflate", tiled=True, blockxsize=512, blockysize=512,
                        nodata=255, BIGTIFF="IF_SAFER")
            p = OUT / fid / f"{nm}.tif"
            with rasterio.open(p.with_suffix(".tif.part"), "w", **prof) as d:
                d.write(arr, 1); d.set_band_description(1, nm)
                d.update_tags(classes="|".join(f"{k}={v}" for k, v in lut.items()), frame=fid,
                              inputs="p69a BASE_CLASS (PRE only) + frozen flood_core/central/possible masks of the "
                                     "frozen M2 candidate",
                              forbidden_not_read="Sentinel-1; S1 weak labels; HAND; UNOSAT; any new threshold",
                              semantics="FLOOD_ASSOCIATED means an optical event response in a known pre-event "
                                        "surface context; it does NOT prove open-water inundation"
                              if nm.endswith("semantic_state") else
                              "sensitivity of the flood/non-flood call to the frozen threshold envelope",
                              producer="p69b_event_association.py")
            os.replace(p.with_suffix(".tif.part"), p)

        # ---- C + D. accounting and cross-tabs, on owned cells only -------------------------------------------------
        raw = float((flood & own).sum()) * PX
        onwater = float((flood & own & (bc == 0)).sum()) * PX
        acc.append(dict(frame=fid, raw_m2_central_km2=round(raw, 2),
                        m2_central_on_pre_existing_water_km2=round(onwater, 2),
                        new_land_central_km2=round(raw - onwater, 2),
                        **{f"new_land_{SEM[s_].replace('FLOOD_ASSOCIATED_','').lower()}_km2":
                           round(float((flood & own & (bc == b)).sum()) * PX, 3)
                           for b, s_ in BASE2SEM.items()},
                        new_land_uncertain_base_km2=round(float((flood & own & (bc == 6)).sum()) * PX, 3)))
        for b, bn in BASE.items():
            for s_, sn in STAB.items():
                n = int(((bc == b) & (stab == s_) & own).sum())
                if n:
                    bxs.append(dict(frame=fid, base_class=bn, decision_stability=sn, n_cells=n,
                                    km2=round(n * PX, 3)))
        for v, vn in SEM.items():
            for s_, sn in STAB.items():
                n = int(((sem == v) & (stab == s_) & own).sum())
                if n:
                    sxs.append(dict(frame=fid, semantic_state=vn, decision_stability=sn, n_cells=n,
                                    km2=round(n * PX, 3)))
        # pre-existing water kept as a diagnostic, never in the headline
        w = own & (bc == 0) & ok
        acc[-1].update(pre_existing_water_km2=round(float(w.sum()) * PX, 1),
                       pre_water_median_m2_score=round(float(np.median(sc[w])) / 1e4, 4) if w.any() else np.nan,
                       pre_water_core_km2=round(float((w & (stab == 1)).sum()) * PX, 2),
                       pre_water_threshold_sensitive_km2=round(float((w & np.isin(stab, (2, 3))).sum()) * PX, 2))
        print(f"  {fid}: raw M2 central {raw:,.1f} km2 = {onwater:,.1f} on pre-existing water + "
              f"{raw-onwater:,.1f} new land", flush=True)
        del bc, core, cen, pos, val, sc, own, stab, sem, flood, ok

    # ---- E. frame invariance ----------------------------------------------------------------------------------------
    bad = 0
    for A_, B_ in itertools.combinations(FRAMES, 2):
        GA, GB = CG.frame_grid(A_), CG.frame_grid(B_)
        x0, x1 = max(GA["x0"], GB["x0"]), min(GA["x1"], GB["x1"])
        y0, y1 = max(GA["y0"], GB["y0"]), min(GA["y1"], GB["y1"])
        if x1 <= x0 or y1 <= y0:
            continue
        for prod in ("p69b_semantic_state", "p69b_decision_stability5"):
            ws = []
            for f_ in (A_, B_):
                with rasterio.open(OUT / f_ / f"{prod}.tif") as s:
                    w = from_bounds(x0, y0, x1, y1, transform=s.transform)
                for v in (w.col_off, w.row_off, w.width, w.height):
                    assert abs(v - round(v)) < 1e-9, f"{f_}: overlap window off-lattice"
                ws.append(Window(round(w.col_off), round(w.row_off), round(w.width), round(w.height)))
            nmis = ncom = 0
            with rasterio.open(OUT / A_ / f"{prod}.tif") as sa, rasterio.open(OUT / B_ / f"{prod}.tif") as sb:
                for r0 in range(0, ws[0].height, 512):
                    h = min(512, ws[0].height - r0)
                    u = sa.read(1, window=Window(ws[0].col_off, ws[0].row_off + r0, ws[0].width, h))
                    v = sb.read(1, window=Window(ws[1].col_off, ws[1].row_off + r0, ws[1].width, h))
                    ncom += u.size; nmis += int((u != v).sum())
            orows.append(dict(pair=f"{A_}|{B_}", product=prod, n_common=ncom, n_mismatch=nmis)); bad += nmis
            print(f"  overlap {A_}|{B_} {prod:28s}: {ncom:,} cells, {nmis:,} mismatch", flush=True)

    A = pd.DataFrame(acc); A.to_csv(CFG.TABLES / "p69b_area_accounting.csv", index=False)
    BX = pd.DataFrame(bxs); BX.to_csv(CFG.TABLES / "p69b_base_x_stability.csv", index=False)
    SX = pd.DataFrame(sxs); SX.to_csv(CFG.TABLES / "p69b_semantic_x_stability.csv", index=False)
    pd.DataFrame(orows).to_csv(CFG.TABLES / "p69b_overlap_qa.csv", index=False)
    man = dict(product="EVENT_ASSOCIATION_v1",
               inputs=["p69a BASE_CLASS (PRE only)", "M2_PRODUCTION_CANDIDATE_CORRECTED10M score/valid",
                       "frozen flood_core / flood_central / flood_possible"],
               forbidden_not_read=["Sentinel-1", "S1 weak labels", "HAND", "UNOSAT", "any new threshold"],
               semantic_classes={str(k): v for k, v in SEM.items()},
               stability_classes={str(k): v for k, v in STAB.items()},
               naming_note="FLOOD_ASSOCIATED, not FLOODED: optical event response in a known pre-event surface "
                           "context. No OPEN_FLOOD class is created at this stage.",
               raw_m2_central_km2=round(float(A.raw_m2_central_km2.sum()), 2),
               m2_central_on_pre_existing_water_km2=round(float(A.m2_central_on_pre_existing_water_km2.sum()), 2),
               headline_new_land_central_km2=round(float(A.new_land_central_km2.sum()), 2),
               headline_definition="M2 central AND BASE_CLASS != PRE_EXISTING_WATER; the raw figure is NOT the "
                                   "flood-associated land area",
               overlap_mismatches=int(bad),
               git=subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=CFG.REPO_ROOT, capture_output=True,
                                  text=True).stdout.strip())
    man["verdict"] = "PASS" if bad == 0 else "HOLD"
    (OUT / "p69b_manifest.json").write_text(json.dumps(man, indent=2, default=str))
    print(f"\n=== AREA ACCOUNTING (deduplicated union) ===")
    print(f"  raw M2 central response            {man['raw_m2_central_km2']:>10,.2f} km2")
    print(f"  of which on PRE_EXISTING_WATER     {man['m2_central_on_pre_existing_water_km2']:>10,.2f} km2")
    print(f"  NEW-LAND event-associated          {man['headline_new_land_central_km2']:>10,.2f} km2  <- headline")
    print("\n=== SEMANTIC_STATE x DECISION_STABILITY (union, km2) ===")
    print(SX.pivot_table(index="semantic_state", columns="decision_stability", values="km2",
                         aggfunc="sum").fillna(0).round(2).to_string())
    print(f"\nVERDICT: {man['verdict']}")
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
