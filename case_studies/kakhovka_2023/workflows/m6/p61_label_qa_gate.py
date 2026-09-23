# Provenance: SWOT-DNIPRO scripts/p61_label_qa_gate.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: ACTIVE_DIAGNOSTIC -- label QA gate; WorldCover used ONLY for stratified reporting (G8), never in the label.
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P61 -- LABEL_QA_GATE: are the weak reference labels fit to supervise M0-M5? Ten gates, decided per frame.

INDEPENDENT OF p60 BY CONSTRUCTION. Nothing is imported from the constructor: coverage is recounted from the S1
cache, areas are recomputed on both grids, and the optical evidence comes from the frozen composites. A constructor
that agrees with itself is how `not observed` became `dry` over 979 km2 of B1 (the uint8 wrap, G1 below).

LOW PREVALENCE IS NOT AUTOMATICALLY AN ERROR. B3 yields 1.7 km2 of positives against B1's 145.9 and B2's 80.2, and
this gate does NOT assume that is a defect. Three readings are separated by evidence, not asserted:
    A  positives along the delta distributaries and floodplain, confirmed by S2 event/trace  -> physically plausible
    B  positives on dry steppe or sand, in isolated specks, not confirmed by S2              -> weak-classifier FP
    C  strong S2 flood-like change where the S1 label is negative or unlabelled              -> weak-label FALSE
                                                                                                NEGATIVE
Reading C is why the `valid_peak_count` table exists. With `>= 2 of 3 peak events` and one peak date covering 7 % of
ZONE_3, much of B3 has only TWO usable peak opportunities, so the rule may be rejecting real flood for want of a
third look. Distance to water is reported but is NOT decisive on its own: false S1 water also concentrates on
shorelines, wet sand, shallows, spits and smooth surfaces, so it cannot separate A from B by itself.

THE RULE IS NOT CHANGED HERE. This gate diagnoses; it never re-tunes. If B3 fails, B3 goes on LABEL_HOLD.

G1  INVALID != NEGATIVE     no cell without an S1 observation carries label 0
G2  COVERAGE                area and % with >= 1 / >= 2 / >= 3 usable peak observations
G3  PREVALENCE              positive / negative / unlabelled, reported without a verdict attached
G4  SPATIAL TOPOLOGY        connected components of positives: area, compactness, distance to pre-water, speck share
G5  CROSS-SENSOR EVIDENCE   S2 event/trace at the positives: MNDWI/NDWI/AWEIsh and the change from PRE
G6  SCENE CONSISTENCY       per peak scene: usable area, separation, positive area, overlap between scenes
G7  MAP QA                  labels over a false-colour index backdrop with the pre-breach shoreline
G8  STRATA                  WorldCover 2021: water, wetland, cropland, grass, tree, built-up, bare
G9  REPROJECTION INVARIANT  class areas on the 20 m cache grid == areas on the 10 m lattice
G10 LABEL PROVENANCE        per-cell peak_count, valid_peak_count, pre_water_frac, source scenes, rule version

Outputs: outputs/tables/p61_label_qa_{gates,peak_support,topology,evidence,strata,scenes}.csv,
         outputs/figures/p61_label_qa_<FRAME>.png
"""
from __future__ import annotations
import argparse, os, sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from scipy import ndimage
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG
from floodstate_eo.optical import watermask as WM

OUT = CFG.BULK_ROOT / "frames10"
PEAK = ("2023-06-09", "2023-06-13", "2023-06-14")
RULE_VERSION = "p51/p60 v1: pos = land_pre & n_pos_peak>=2; neg = land_pre & n_post_wet==0 & n_post_obs>=6"
SRC = {"B1": ("ZONE_4_FLOODWAY_june2023_s32", "ZONE_4_DAM_TO_KHERSON_FLOODWAY"),
       "B2": ("ZONE_2_KHERSON_DELTA_flood_june2023", "ZONE_2_KHERSON_DELTA"),
       "B3": ("ZONE_3_DNIPRO_BUG_ESTUARY_flood_june2023", "ZONE_3_DNIPRO_BUG_ESTUARY")}
WC = {10: "tree", 20: "shrub", 30: "grass", 40: "cropland", 50: "built_up", 60: "bare_sand", 80: "water",
      90: "wetland", 95: "mangrove", 100: "moss"}
PX = CG.CELL * CG.CELL / 1e6


def band(path, name):
    with rasterio.open(path) as s:
        return s.read(list(s.descriptions).index(name) + 1)


def onto(src, tr, crs, F, dtype, nodata, rs=Resampling.nearest):
    dst = np.full((F["ny"], F["nx"]), nodata, dtype)
    reproject(source=src.astype(dtype), destination=dst, src_transform=tr, src_crs=crs,
              dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC, resampling=rs,
              src_nodata=nodata, dst_nodata=nodata)
    return dst


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=list(CG.FRAME_BBOX))
    a = ap.parse_args()
    gates, peaksup, topo, evid, strata, scenes = [], [], [], [], [], []

    def gate(name, fid, ok, measured, note=""):
        gates.append(dict(gate=name, frame=fid, status="PASS" if ok else ("INFO" if ok is None else "FAIL"),
                          measured=measured, note=note, rule_version=RULE_VERSION))
        tag = "PASS" if ok else ("INFO" if ok is None else "FAIL")
        print(f"  {tag:4s} {name:24s} {fid}  {measured}", flush=True)

    for fid in a.frames:
        print(f"\n=== {fid} ===", flush=True)
        F = CG.frame_grid(fid)
        cache, zone = SRC[fid]
        lp = OUT / fid / "labels.tif"
        L = band(lp, "label").astype("i2")
        nvp = band(lp, "n_valid_peak"); npp = band(lp, "n_pos_peak")
        npo = band(lp, "n_post_obs"); npre = band(lp, "n_pre_obs")
        wfr = band(lp, "pre_water_frac").astype("f4")

        # ---- G1: an unobserved cell may never be a negative -------------------------------------------------------
        z = np.load(CFG.S1_CACHE / cache / "per_scene_water.npz", allow_pickle=True)
        shp = tuple(int(v) for v in z["shape"]); cell = float(z["cell"])
        ctr = from_origin(float(z["x0"]), float(z["y1"]), cell, cell)
        anyobs = np.zeros(shp, bool)
        for k in [k for k in z.keys() if k[:4] == "2023" and not k.startswith("valid_")]:
            anyobs |= np.unpackbits(z["valid_" + k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
        obs10 = onto(anyobs, ctr, CFG.CRS_METRIC, F, "u1", 0).astype(bool)   # recounted, not taken from p60
        bad = int(((~obs10) & (L == 0)).sum())
        gate("G1_INVALID_NOT_NEGATIVE", fid, bad == 0,
             f"{bad:,} unobserved cells labelled negative ({bad*PX:.1f} km2); S1 observed {100*obs10.mean():.1f} % "
             f"of the frame")

        # ---- G9: reprojection invariant ---------------------------------------------------------------------------
        inv = []
        for nm, v in (("positive", 1), ("negative", 0)):
            a10 = float((L == v).sum()) * PX
            inv.append((nm, a10))
        lab20 = onto(L.astype("i2"), F["transform"], CFG.CRS_METRIC, F, "i2", -32768)  # identity; areas from 20 m below
        cache_px = cell * cell / 1e6
        # recompute the class areas on the 20 m grid straight from the cache and the frame labels' own rule inputs
        back = np.full(shp, -32768, "i2")
        reproject(source=L, destination=back, src_transform=F["transform"], src_crs=CFG.CRS_METRIC,
                  dst_transform=ctr, dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest,
                  src_nodata=-32768, dst_nodata=-32768)
        d20 = {nm: float((back == v).sum()) * cache_px for nm, v in (("positive", 1), ("negative", 0))}
        worst = max(abs(d20[nm] - a) / max(a, 1e-9) for nm, a in inv)
        gate("G9_REPROJECTION_INVARIANT", fid, worst < 0.02,
             "; ".join(f"{nm} 10 m {a:,.1f} km2 vs 20 m {d20[nm]:,.1f} km2" for nm, a in inv)
             + f"; worst relative difference {100*worst:.2f} %")

        # ---- G2 + the valid_peak_count table (reading C) -----------------------------------------------------------
        comp = OUT / fid / "composite_preall.tif"
        mnd_ev_max = band(comp, "MNDWI_event_max").astype("f4") / 1e4
        mnd_pre = band(comp, "MNDWI_pre_med").astype("f4") / 1e4
        ndw_ev_max = band(comp, "NDWI_event_max").astype("f4") / 1e4
        awe_ev_max = band(comp, "AWEIsh_event_max").astype("f4") / 1e4
        mnd_tr = band(comp, "MNDWI_trace_med").astype("f4") / 1e4
        nobs_ev = band(comp, "n_obs_event")
        for arr in (mnd_ev_max, mnd_pre, ndw_ev_max, awe_ev_max, mnd_tr):
            arr[arr <= -3.2767] = np.nan
        # FLOOD-LIKE is the frozen water rule applied to the event extreme, minus what already looked like water
        # before: it is a transparent threshold on published indices, never a model output.
        floodlike = (mnd_ev_max > WM.DEFAULT_MNDWI) & (ndw_ev_max > WM.DEFAULT_NDWI) & (mnd_pre < WM.DEFAULT_MNDWI)
        seen_s2 = nobs_ev > 0
        for k in (0, 1, 2, 3):
            m = (nvp == k) & obs10
            ar = float(m.sum()) * PX
            if ar <= 0:
                continue
            fl = float((floodlike & m & seen_s2).sum()) * PX
            s2a = float((m & seen_s2).sum()) * PX
            peaksup.append(dict(frame=fid, valid_peak_count=k, area_km2=round(ar, 1),
                                pct_of_s1_observed=round(100 * ar / (obs10.sum() * PX), 2),
                                positive_km2=round(float(((L == 1) & m).sum()) * PX, 2),
                                negative_km2=round(float(((L == 0) & m).sum()) * PX, 1),
                                unlabelled_km2=round(float(((L == 2) & m).sum()) * PX, 1),
                                s2_observed_km2=round(s2a, 1),
                                s2_floodlike_km2=round(fl, 2),
                                s2_floodlike_pct_of_observed=round(100 * fl / s2a, 2) if s2a > 0 else np.nan))
        g2 = {k: round(float(((nvp >= k) & obs10).sum()) * PX, 1) for k in (1, 2, 3)}
        tot = float(obs10.sum()) * PX
        gate("G2_COVERAGE", fid, None,
             ", ".join(f">={k} peak: {v:,.0f} km2 ({100*v/tot:.1f} %)" for k, v in g2.items()))

        # ---- G3: prevalence, stated without a verdict --------------------------------------------------------------
        npos = int((L == 1).sum()); nneg = int((L == 0).sum()); nun = int((L == 2).sum())
        gate("G3_PREVALENCE", fid, None,
             f"pos {npos:,} ({npos*PX:.2f} km2), neg {nneg:,} ({nneg*PX:,.0f} km2), unlab {nun*PX:,.0f} km2, "
             f"prevalence {npos/max(npos+nneg,1):.4f}",
             "low prevalence is reported, not judged; see G4/G5/G8 and the peak-support table")

        # ---- G4: topology of the positives -------------------------------------------------------------------------
        pos = L == 1
        prewater = wfr >= 20.0
        if pos.any():
            lab, n = ndimage.label(pos, structure=np.ones((3, 3), int))
            sizes = np.bincount(lab.ravel())[1:]
            d_pre = ndimage.distance_transform_edt(~prewater, sampling=CG.CELL) if prewater.any() else None
            dm = ndimage.mean(d_pre, lab, range(1, n + 1)) if d_pre is not None else np.full(n, np.nan)
            areas = sizes * PX
            speck = float((sizes <= 4).sum()) / n
            speck_a = float(sizes[sizes <= 4].sum()) * PX
            q = np.percentile(dm[np.isfinite(dm)], [50, 90]) if np.isfinite(dm).any() else (np.nan, np.nan)
            topo.append(dict(frame=fid, n_components=n, total_km2=round(areas.sum(), 2),
                             largest_km2=round(areas.max(), 2),
                             median_component_px=int(np.median(sizes)),
                             frac_components_le_4px=round(speck, 4), km2_in_specks=round(speck_a, 3),
                             median_dist_to_prewater_m=round(float(q[0]), 1),
                             p90_dist_to_prewater_m=round(float(q[1]), 1)))
            gate("G4_SPATIAL_TOPOLOGY", fid, None,
                 f"{n:,} components, largest {areas.max():.2f} km2, {100*speck:.1f} % are <=4 px "
                 f"({speck_a:.3f} km2), median distance to pre-breach water {q[0]:,.0f} m")
        else:
            gate("G4_SPATIAL_TOPOLOGY", fid, False, "no positive cells at all")

        # ---- G5: cross-sensor evidence at the positives --------------------------------------------------------------
        for nm, m in (("positive", L == 1), ("negative", L == 0), ("unlabelled", L == 2)):
            mm = m & seen_s2
            if not mm.any():
                continue
            evid.append(dict(frame=fid, label=nm, n=int(mm.sum()), km2=round(float(mm.sum()) * PX, 2),
                             s2_floodlike_pct=round(100 * float((floodlike & mm).sum()) / mm.sum(), 2),
                             mndwi_event_max_med=round(float(np.nanmedian(mnd_ev_max[mm])), 4),
                             mndwi_pre_med=round(float(np.nanmedian(mnd_pre[mm])), 4),
                             d_mndwi_med=round(float(np.nanmedian(mnd_ev_max[mm] - mnd_pre[mm])), 4),
                             ndwi_event_max_med=round(float(np.nanmedian(ndw_ev_max[mm])), 4),
                             aweish_event_max_med=round(float(np.nanmedian(awe_ev_max[mm])), 4),
                             mndwi_trace_med=round(float(np.nanmedian(mnd_tr[mm])), 4)))
        e = [r for r in evid if r["frame"] == fid and r["label"] == "positive"]
        if e:
            gate("G5_CROSS_SENSOR", fid, None,
                 f"S2 confirms flood-like on {e[0]['s2_floodlike_pct']:.1f} % of positives; "
                 f"median d(MNDWI) event-max minus pre {e[0]['d_mndwi_med']:+.3f}")

        # ---- G6: per peak scene ---------------------------------------------------------------------------------------
        qa_file = {"B1": "p0v_zone4_scene_qa.csv", "B2": "p0w_zone2_scene_qa.csv",
                   "B3": "p0w3_zone3_scene_qa.csv"}[fid]
        Q = pd.read_csv(CFG.TABLES / qa_file)
        per = {}
        for k in [k for k in z.keys() if k[:4] == "2023" and not k.startswith("valid_")]:
            if k[:10] not in PEAK:
                continue
            w = np.unpackbits(z[k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
            v = np.unpackbits(z["valid_" + k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
            per[k[:10]] = (onto(w & v, ctr, CFG.CRS_METRIC, F, "u1", 0).astype(bool),
                           onto(v, ctr, CFG.CRS_METRIC, F, "u1", 0).astype(bool))
            row = Q[Q.event_id.str.startswith(k[:10])]
            scenes.append(dict(frame=fid, peak_date=k[:10],
                               usable_km2=round(float(per[k[:10]][1].sum()) * PX, 1),
                               usable_pct_of_frame=round(100 * float(per[k[:10]][1].mean()), 1),
                               water_km2=round(float(per[k[:10]][0].sum()) * PX, 1),
                               lda_separation=round(float(row.lda_separation.iloc[0]), 3) if len(row) else np.nan,
                               fp_land_anchor_pct=round(100 * float(row.fp_land_anchor_fraction.iloc[0]), 2)
                               if len(row) else np.nan,
                               scene_quality_flag=row.scene_quality_flag.iloc[0] if len(row) else "?"))
        ds = sorted(per)
        ov = []
        for i in range(len(ds)):
            for j in range(i + 1, len(ds)):
                both = per[ds[i]][1] & per[ds[j]][1]
                if both.any():
                    inter = (per[ds[i]][0] & per[ds[j]][0] & both).sum()
                    uni = ((per[ds[i]][0] | per[ds[j]][0]) & both).sum()
                    ov.append(f"{ds[i][5:]}&{ds[j][5:]} IoU {inter/max(uni,1):.3f} on {both.sum()*PX:,.0f} km2")
        gate("G6_SCENE_CONSISTENCY", fid, None,
             "; ".join(f"{d} usable {100*per[d][1].mean():.0f} %" for d in ds) + " | " + "; ".join(ov))

        # ---- G8: strata ------------------------------------------------------------------------------------------------
        wcp = CFG.BULK_ROOT / "worldcover_frames" / zone / "wc_2021_20m.tif"
        if wcp.exists():
            with rasterio.open(wcp) as s:
                wc = onto(s.read(1), s.transform, s.crs, F, "u1", 0)
            for code, nm in WC.items():
                m = (wc == code) & obs10
                if not m.any():
                    continue
                strata.append(dict(frame=fid, wc_class=nm, area_km2=round(float(m.sum()) * PX, 1),
                                   positive_km2=round(float(((L == 1) & m).sum()) * PX, 3),
                                   negative_km2=round(float(((L == 0) & m).sum()) * PX, 1),
                                   unlabelled_km2=round(float(((L == 2) & m).sum()) * PX, 1),
                                   pos_share_of_class_pct=round(100 * float(((L == 1) & m).sum()) / m.sum(), 3),
                                   s2_floodlike_pct=round(100 * float((floodlike & m & seen_s2).sum())
                                                          / max(float((m & seen_s2).sum()), 1), 2)))
            top = sorted([r for r in strata if r["frame"] == fid], key=lambda r: -r["positive_km2"])[:3]
            gate("G8_STRATA", fid, None,
                 "positives concentrate in " + ", ".join(f"{r['wc_class']} {r['positive_km2']:.2f} km2" for r in top))
        else:
            gate("G8_STRATA", fid, None, f"no WorldCover for {zone}")

        # ---- G10: provenance --------------------------------------------------------------------------------------------
        with rasterio.open(lp) as s:
            t = s.tags()
        need = ("rule", "label_values", "label_kind", "label_native_m", "s1_cache", "candidate_peak_dates",
                "usable_peak_dates", "n_peak_required", "pre_water_frac_source")
        miss = [k for k in need if k not in t]
        gate("G10_LABEL_PROVENANCE", fid, not miss,
             f"{len(need)-len(miss)}/{len(need)} provenance tags present" + (f"; missing {miss}" if miss else "")
             + f"; per-cell bands: n_valid_peak, n_pos_peak, n_post_obs, n_pre_obs, pre_water_frac")

        # ---- G7: map ---------------------------------------------------------------------------------------------------
        st = max(1, int(max(F["ny"], F["nx"]) / 1600))
        bg = mnd_ev_max[::st, ::st]
        Ls = L[::st, ::st]; pw = prewater[::st, ::st]
        fig, ax = plt.subplots(figsize=(11, 11 * F["ny"] / F["nx"]), dpi=130)
        ax.imshow(bg, cmap="Greys_r", vmin=-0.6, vmax=0.6, interpolation="nearest")
        ov_ = np.full(Ls.shape, np.nan)
        ov_[Ls == 2] = 0; ov_[Ls == 0] = 1; ov_[Ls == 1] = 2
        ax.imshow(ov_, cmap=ListedColormap(["#c8c8c8", "#3a7bd5", "#e8322d"]), vmin=-0.5, vmax=2.5, alpha=0.45,
                  interpolation="nearest")
        ax.contour(pw.astype(float), levels=[0.5], colors="#00d0ff", linewidths=0.6)
        ax.set_title(f"{fid}  WEAK reference labels over MNDWI event-max\n"
                     f"red = positive {npos*PX:.1f} km2 | blue = negative {nneg*PX:,.0f} km2 | grey = unlabelled | "
                     f"cyan = pre-breach shoreline (water freq >= 20 %)", fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
        fig.tight_layout(); fig.savefig(CFG.FIG / f"p61_label_qa_{fid}.png", bbox_inches="tight"); plt.close(fig)
        print(f"  -> outputs/figures/p61_label_qa_{fid}.png", flush=True)
        del L, nvp, npp, npo, npre, wfr, mnd_ev_max, mnd_pre, ndw_ev_max, awe_ev_max, mnd_tr, floodlike, obs10

    for nm, rows in (("gates", gates), ("peak_support", peaksup), ("topology", topo), ("evidence", evid),
                     ("strata", strata), ("scenes", scenes)):
        pd.DataFrame(rows).to_csv(CFG.TABLES / f"p61_label_qa_{nm}.csv", index=False)
    G = pd.DataFrame(gates)
    nf = int((G.status == "FAIL").sum())
    print(f"\n{'LABEL_QA_GATE: no hard failure' if nf == 0 else f'LABEL_QA_GATE: {nf} FAIL'}")
    print("-> outputs/tables/p61_label_qa_{gates,peak_support,topology,evidence,strata,scenes}.csv")
    print("The verdict on each frame is a decision, not an exit code: read peak_support and evidence.")


if __name__ == "__main__":
    main()
