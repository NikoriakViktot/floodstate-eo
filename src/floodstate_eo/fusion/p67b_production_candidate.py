# Provenance: SWOT-DNIPRO scripts/p67b_production_candidate.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 13 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo; `git rev-parse` now runs against this repo.
"""P67b -- M2_PRODUCTION_CANDIDATE_CORRECTED10M: one model, three frames, and the overlap invariant on its output.

THIS IS A CANDIDATE, NOT THE FINAL PRODUCTION MODEL, and the name says so everywhere it is written.

BASELINE: PRE_ALL. A methodological choice, not a claim of superiority -- it has the largest temporal support, there
is no consistent evidence that restricting the baseline seasonally helps, and it gives the highest corrected pooled
AP on the main layer (0.9299 against 0.9218 and 0.9156). PRE_SEASONAL and PRE_ALL_NMATCH remain ablations and their
results are kept.

TRAINING: B1 and B2 only. B3 weak labels are used for NOTHING -- not training, not thresholds, not hyperparameters,
not feature selection, not calibration -- so that B3 stays unseen geography for a later transfer experiment.

DEDUPLICATION BY PHYSICAL PIXEL. The frames overlap, so the same patch of ground can enter the fitting population
twice. Ownership is resolved on the canonical lattice (B1 owns the shared ground) and the counts are reported rather
than asserted: a physical location appearing twice in the fit, or on both sides of a split, would invalidate the
whole spatial design.

OUTPUT IS A SCORE, NOT A PROBABILITY. A random forest's vote fraction is a discrimination score until a calibration
analysis says otherwise. Three products are stored separately and never merged into one raster: continuous score,
thresholded state, and the validity of the prediction itself.

THE OVERLAP INVARIANT, NOW ON THE MODEL. One deterministic forest applied to bitwise-identical feature vectors must
return bitwise-identical scores. Anything else is feature decoding, feature ordering, nodata handling, batch
inference or model serialisation -- never an acceptable seam. Target: zero mismatching cells, zero maximum
difference. Score, class and validity are reported SEPARATELY, because a support disagreement and a score
disagreement are different defects.

UNION AREA. Every physical cell is counted once; the overlaps are 4 229 km2 and double counting them would inflate
any flooded area by that much.

Outputs: <frame>/cand_score.tif, cand_state.tif, cand_valid.tif; production_candidate_manifest.json;
         <case_study>/tables/p67b_{training_qa,overlap_score_qa,union_area_qa}.csv
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, os, subprocess, sys, time
from pathlib import Path
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.windows import Window, from_bounds
from sklearn.ensemble import RandomForestClassifier
from .. import _kakhovka_legacy_config as CFG
from ..spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
ML = OUT / "_ml"
NAME = "M2_PRODUCTION_CANDIDATE_CORRECTED10M"
ND = -32768
SCORE_SCALE = 10_000
SCORE_ND = 65535
FIT_N = 300_000
SEED = 20260922
ROWS = 128
FRAMES = ("B1", "B2", "B3")
TRAIN_FRAMES = ("B1", "B2")


def sha256(p: Path, buf=1 << 24) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while (b := f.read(buf)):
            h.update(b)
    return h.hexdigest()


def choose_params():
    t = pd.read_csv(CFG.TABLES / "p65b_m2_tuning.csv")
    s = t[(t.baseline == "preall") & (t.regime == "buffered")]
    g = s.groupby(["n_estimators", "max_depth", "min_samples_leaf", "max_features"],
                  dropna=False).inner_AP.median().sort_values(ascending=False)
    k = g.index[0]
    p = dict(n_estimators=int(k[0]), max_depth=None if pd.isna(k[1]) else int(k[1]),
             min_samples_leaf=int(k[2]), max_features=k[3])
    try:
        p["max_features"] = float(p["max_features"])
    except (TypeError, ValueError):
        pass
    return p, float(g.iloc[0])


def aligned_window(path, bnds):
    with rasterio.open(path) as s:
        w = from_bounds(*bnds, transform=s.transform)
    for v in (w.col_off, w.row_off, w.width, w.height):
        assert abs(v - round(v)) < 1e-9, f"{Path(path).name}: overlap window off-lattice"
    return Window(round(w.col_off), round(w.row_off), round(w.width), round(w.height))


def overlap_bounds(a, b):
    GA, GB = CG.frame_grid(a), CG.frame_grid(b)
    x0, x1 = max(GA["x0"], GB["x0"]), min(GA["x1"], GB["x1"])
    y0, y1 = max(GA["y0"], GB["y0"]), min(GA["y1"], GB["y1"])
    return (x0, y0, x1, y1) if (x1 > x0 and y1 > y0) else None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fit-n", type=int, default=FIT_N)
    ap.add_argument("--jobs", type=int, default=32); ap.add_argument("--threshold", type=float, default=None)
    a = ap.parse_args()
    t0 = time.time()
    names = pd.read_csv(CFG.TABLES / "p65a_feature_manifest.csv").feature.tolist()
    params, med_ap = choose_params()
    print(f"{NAME}\n  hyperparameters (inner AP only): {params}  median inner AP {med_ap:.5f}", flush=True)

    # ---- training population, deduplicated by PHYSICAL pixel ------------------------------------------------------
    I = pd.read_parquet(ML / "index.parquet")
    y = I.label.to_numpy().astype(np.int8)
    X = np.load(ML / "X_preall.i2", mmap_mode="r")
    assert set(I.frame.unique()) <= set(TRAIN_FRAMES), f"B3 must not be in the population: {I.frame.unique()}"
    # the index was built under frame ownership, so a physical cell appears once; VERIFY rather than trust
    # FLOOR, never round. The stored x and y are cell CENTRES, so x / CELL always ends in .5, and numpy's
    # banker's rounding then maps two adjacent columns onto the same index -- and two adjacent rows likewise, a
    # fourfold collapse that reported 16.05 million phantom "duplicates" out of 22.17 million cells. Flooring a
    # centre coordinate gives the cell index exactly.
    key = (np.floor(I.x.to_numpy() / CG.CELL).astype(np.int64) * 10_000_000
           + np.floor(I.y.to_numpy() / CG.CELL).astype(np.int64))
    n_before = len(I); n_unique = int(len(np.unique(key)))
    dup_px = n_before - n_unique
    blocks_per_frame = I.groupby("blk5").frame.nunique()
    dup_blocks = int((blocks_per_frame > 1).sum())
    qa = dict(model=NAME, n_samples_before_overlap_dedup=n_before, n_samples_after_overlap_dedup=n_unique,
              n_duplicate_pixels_removed=dup_px, n_duplicate_blocks_removed=dup_blocks,
              dedup_rule="canonical 10 m physical coordinate; B1 owns the shared ground, B2 the rest",
              train_frames="|".join(TRAIN_FRAMES), b3_used_for="nothing")
    print(f"  training population: {n_before:,} rows, {n_unique:,} distinct physical cells, "
          f"{dup_px:,} duplicates, {dup_blocks} blocks spanning two frames", flush=True)
    if dup_px:
        print("  STOP: the same physical location occurs more than once in the fitting population.")
        pd.DataFrame([qa]).to_csv(CFG.TABLES / "p67b_training_qa.csv", index=False); sys.exit(1)

    rng = np.random.default_rng(SEED)
    fit = np.sort(rng.choice(np.arange(n_before), min(a.fit_n, n_before), replace=False))
    rf = RandomForestClassifier(**params, class_weight="balanced_subsample", n_jobs=a.jobs, random_state=SEED)
    rf.fit(X[fit].astype("f4"), y[fit])
    qa.update(training_n=int(len(fit)), training_positive_n=int((y[fit] == 1).sum()),
              training_negative_n=int((y[fit] == 0).sum()), training_prevalence=round(float(y[fit].mean()), 5))
    pd.DataFrame([qa]).to_csv(CFG.TABLES / "p67b_training_qa.csv", index=False)
    print(f"  fitted on {len(fit):,} cells ({qa['training_positive_n']:,} positive) in {time.time()-t0:.0f}s",
          flush=True)

    thr = a.threshold if a.threshold is not None else float(
        np.median(pd.read_csv(CFG.TABLES / "p65b_m2_folds.csv").query(
            "baseline=='preall' and regime=='block'").threshold))
    print(f"  state threshold {thr:.4f} (median of the frozen per-fold thresholds; NOT re-tuned here)", flush=True)

    meta = dict(model=NAME, status="PRODUCTION_CANDIDATE_NOT_FINAL", baseline="PRE_ALL",
                baseline_rationale="largest temporal support; no consistent evidence that seasonal restriction or "
                                   "date-count matching improves performance; highest corrected pooled AP on the "
                                   "main layer. A methodological choice, not a claim of universal superiority.",
                training_frames=list(TRAIN_FRAMES), b3_status="PREDICTION_ONLY_UNSEEN_GEOGRAPHY",
                b3_used_for_training_or_tuning=False,
                label_status="WEAK_REFERENCE_NOT_GROUND_TRUTH",
                output_semantics="score = random-forest discrimination score, NOT a calibrated probability",
                hyperparameters=params, hyperparameter_selection="best median inner AP, outer test never consulted",
                state_threshold=thr, threshold_selection="median of the frozen per-fold thresholds from p65b",
                class_weight="balanced_subsample", random_state=SEED, **{k: v for k, v in qa.items() if k != "model"},
                feature_manifest_hash=sha256(CFG.TABLES / "p65a_feature_manifest.csv"),
                git=subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=CFG.REPO_ROOT, capture_output=True,
                                   text=True).stdout.strip())

    # ---- inference, the SAME model on all three frames ------------------------------------------------------------
    for fid in FRAMES:
        tf = time.time(); F = CG.frame_grid(fid)
        comp = OUT / fid / "composite_preall.tif"
        prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=1, dtype="uint16", crs=CFG.CRS_METRIC,
                    transform=F["transform"], compress="deflate", predictor=2, tiled=True, blockxsize=512,
                    blockysize=ROWS, nodata=SCORE_ND, BIGTIFF="IF_SAFER")
        vprof = dict(prof); vprof.update(dtype="uint8", nodata=255, predictor=1)
        sp, cp, vp = (OUT / fid / f"cand_{k}.tif" for k in ("score", "state", "valid"))
        n_valid = 0
        with rasterio.open(comp) as cs, rasterio.open(sp.with_suffix(".tif.part"), "w", **prof) as ds, \
                rasterio.open(cp.with_suffix(".tif.part"), "w", **vprof) as dc, \
                rasterio.open(vp.with_suffix(".tif.part"), "w", **vprof) as dv:
            cn = list(cs.descriptions); bidx = [cn.index(n) for n in names]
            for r0 in range(0, F["ny"], ROWS):
                h = min(ROWS, F["ny"] - r0); win = Window(0, r0, F["nx"], h)
                cube = cs.read(window=win)
                Xb = cube[bidx].reshape(len(names), -1).T
                nob = {k: cube[cn.index(k)].reshape(-1) for k in ("n_obs_pre", "n_obs_event", "n_obs_trace")}
                ok = (~(Xb == ND).any(1)) & (nob["n_obs_pre"] > 0) & \
                     ((nob["n_obs_event"] > 0) | (nob["n_obs_trace"] > 0))
                sc = np.full(Xb.shape[0], SCORE_ND, np.uint16); st = np.full(Xb.shape[0], 255, np.uint8)
                if ok.any():
                    pr = rf.predict_proba(Xb[ok].astype("f4"))[:, 1]
                    q = np.clip(np.round(pr * SCORE_SCALE), 0, SCORE_SCALE - 1).astype(np.uint16)
                    sc[ok] = q; st[ok] = (q >= int(round(thr * SCORE_SCALE))).astype(np.uint8)
                n_valid += int(ok.sum())
                ds.write(sc.reshape(h, F["nx"]), 1, window=win)
                dc.write(st.reshape(h, F["nx"]), 1, window=win)
                dv.write(ok.reshape(h, F["nx"]).astype(np.uint8), 1, window=win)
                del cube, Xb, sc, st
            for d, desc in ((ds, "score"), (dc, "state"), (dv, "prediction_valid")):
                d.set_band_description(1, desc)
                d.update_tags(model=NAME, status="PRODUCTION_CANDIDATE_NOT_FINAL", frame=fid,
                              semantics="discrimination score, not a calibrated probability" if desc == "score"
                              else ("score >= threshold" if desc == "state" else
                                    "all 84 features present AND pre and post optical observations exist"))
        for s_, d_ in ((sp, sp), (cp, cp), (vp, vp)):
            src = d_.with_suffix(".tif.part")
            with rasterio.open(src) as chk:
                assert (chk.height, chk.width) == (F["ny"], F["nx"])
            os.replace(src, d_)
        print(f"  {fid}: {n_valid:,} of {F['ny']*F['nx']:,} cells scored "
              f"({100*n_valid/(F['ny']*F['nx']):.1f} %) in {time.time()-tf:.0f}s", flush=True)

    # ---- overlap QA on score, state and validity -------------------------------------------------------------------
    rows = []
    for A, B in itertools.combinations(FRAMES, 2):
        bnds = overlap_bounds(A, B)
        if bnds is None:
            continue
        r = dict(pair=f"{A}|{B}")
        for kind in ("score", "state", "valid"):
            pa, pb = OUT / A / f"cand_{kind}.tif", OUT / B / f"cand_{kind}.tif"
            wa, wb = aligned_window(pa, bnds), aligned_window(pb, bnds)
            nmis = 0; mx = 0; ncom = 0
            with rasterio.open(pa) as sa, rasterio.open(pb) as sb:
                for r0 in range(0, wa.height, 512):
                    h = min(512, wa.height - r0)
                    x = sa.read(1, window=Window(wa.col_off, wa.row_off + r0, wa.width, h)).astype("i4")
                    z = sb.read(1, window=Window(wb.col_off, wb.row_off + r0, wb.width, h)).astype("i4")
                    if kind == "score":
                        both = (x != SCORE_ND) & (z != SCORE_ND)
                    else:
                        both = (x != 255) & (z != 255)
                    ncom += int(both.sum())
                    d = np.abs(x - z)[both]
                    nmis += int((d > 0).sum()); mx = max(mx, int(d.max()) if d.size else 0)
            r[f"n_common_{kind}"] = ncom; r[f"n_mismatch_{kind}"] = nmis
            r[f"max_abs_diff_{kind}"] = mx
            print(f"  {A}|{B} {kind:6s}: {ncom:,} common, {nmis:,} mismatch, max |d| {mx}", flush=True)
        rows.append(r)
    pd.DataFrame(rows).to_csv(CFG.TABLES / "p67b_overlap_score_qa.csv", index=False)
    bad = sum(r[f"n_mismatch_{k}"] for r in rows for k in ("score", "state", "valid"))

    # ---- union area, every physical cell counted once ---------------------------------------------------------------
    ua = []
    for i, fid in enumerate(FRAMES):
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
        with rasterio.open(OUT / fid / "cand_state.tif") as s:
            st = s.read(1)
        ua.append(dict(frame=fid, frame_km2=round(F["ny"] * F["nx"] * 1e-4, 1),
                       owned_km2=round(float(own.sum()) * 1e-4, 1),
                       shared_dropped_km2=round(float((~own).sum()) * 1e-4, 1),
                       scored_owned_km2=round(float(((st != 255) & own).sum()) * 1e-4, 1),
                       state1_owned_km2=round(float(((st == 1) & own).sum()) * 1e-4, 2),
                       state1_all_cells_km2=round(float((st == 1).sum()) * 1e-4, 2)))
        del st, own
    U = pd.DataFrame(ua); U.to_csv(CFG.TABLES / "p67b_union_area_qa.csv", index=False)
    meta["union_state1_km2_deduplicated"] = round(float(U.state1_owned_km2.sum()), 2)
    meta["naive_sum_state1_km2_double_counted"] = round(float(U.state1_all_cells_km2.sum()), 2)
    meta["overlap_qa_mismatches"] = int(bad)
    meta["verdict"] = "PASS" if bad == 0 else "HOLD"
    (OUT / "production_candidate_manifest.json").write_text(json.dumps(meta, indent=2, default=str))
    print(f"\nunion state=1 deduplicated {meta['union_state1_km2_deduplicated']:,.1f} km2 "
          f"(naive sum would be {meta['naive_sum_state1_km2_double_counted']:,.1f} km2)")
    print(f"VERDICT: {meta['verdict']}")
    print("-> <case_study>/tables/p67b_{training_qa,overlap_score_qa,union_area_qa}.csv")
    print(f"-> {OUT}/production_candidate_manifest.json")
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
