# Provenance: SWOT-DNIPRO scripts/p66_production_m2.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 12 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo; `git rev-parse` now runs against this repo
# (CFG.REPO_ROOT), so `meta["git"]` records the floodstate-eo commit, not SWOT-DNIPRO's.
"""P66 -- the production M2: one Random Forest, one continuous 10 m flood score over B1, B2 and B3.

NOT A BENCHMARK. Validation is closed (p65b, p65c). This fits ONE model and produces the first real product: a
continuous score, deliberately NOT a binary mask. Thresholding is a separate, later step that needs no retraining --
average precision proved far more stable across folds than any threshold-dependent metric, and recall moved by 0.16
to 0.23 under spatial transfer, so committing to a cut here would freeze the least reliable part of the result.

HYPERPARAMETERS COME FROM THE INNER LOOP ONLY. Taken from the p65b tuning table for PRE_ALL / BUFFERED by
aggregating inner AP over the five outer runs and choosing the best median. Outer-test scores were never consulted,
so the production model inherits no selection bias from the evaluation.

PRE_ALL is the production baseline because it is the complete available pre-event record and needs no artificial
downsampling -- NOT because it won. The three baselines were statistically indistinguishable: every paired
spatial-block interval for a baseline contrast includes zero.

B3 IS PREDICTION-ONLY. Its weak labels failed the label gate (p61) and were never used for training or scoring.

WHY `prediction_valid` IS NOT OPTIONAL. Measured, not assumed: the training population contains ZERO nodata feature
values -- every labelled cell has n_obs_pre >= 9, n_obs_event >= 1 and n_obs_trace >= 4. The forest has therefore
never seen the -32768 sentinel. Wall-to-wall inference reaches cells with no optical observation at all, where that
sentinel would sit far outside every training split and be routed arbitrarily, producing a confident-looking number
with no meaning. Such cells get NODATA, never a score, and never a zero. Not observed is not dry, applied to
prediction rather than to labels.

Outputs per frame: flood_score.tif (uint16, score * 10000, nodata 65535), prediction_valid.tif (uint8)
Plus <case_study>/tables/p66_production_{metadata,overlap_qa,score_distribution}.csv and
     $BULK_ROOT/frames10/production_model_metadata.json
"""
from __future__ import annotations
import argparse, hashlib, json, os, resource, subprocess, sys, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.windows import Window
from sklearn.ensemble import RandomForestClassifier
from .. import _kakhovka_legacy_config as CFG
from ..spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
ML = OUT / "_ml"
ND = -32768
SCORE_SCALE = 10_000
SCORE_ND = 65535
FIT_N = 300_000               # the same final-fit sampling contract as p65b, drawn from the WHOLE population
SEED = 20260922
ROWS = 128


def sha256(p: Path, buf=1 << 24) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while (b := f.read(buf)):
            h.update(b)
    return h.hexdigest()


def choose_params():
    """Best median inner AP over the five outer runs of PRE_ALL / BUFFERED. Outer-test is never read."""
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
    return p, float(g.iloc[0]), int(len(g))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fit-n", type=int, default=FIT_N)
    ap.add_argument("--jobs", type=int, default=32)
    ap.add_argument("--frames", nargs="*", default=["B2", "B1", "B3"]); a = ap.parse_args()
    t0 = time.time()
    names = pd.read_csv(CFG.TABLES / "p65a_feature_manifest.csv").feature.tolist()
    params, med_ap, n_combos = choose_params()
    print(f"hyperparameters from inner AP over {n_combos} combinations: {params}  (median inner AP {med_ap:.5f})",
          flush=True)

    I = pd.read_parquet(ML / "index.parquet")
    y = I.label.to_numpy().astype(np.int8)
    X = np.load(ML / "X_preall.i2", mmap_mode="r")
    rng = np.random.default_rng(SEED)
    pool = np.arange(len(I))                      # the WHOLE admissible B1+B2 population, not four fifths of it
    fit = np.sort(rng.choice(pool, min(a.fit_n, len(pool)), replace=False))
    rf = RandomForestClassifier(**params, class_weight="balanced_subsample", n_jobs=a.jobs, random_state=SEED)
    rf.fit(X[fit].astype("f4"), y[fit])
    print(f"fitted on {len(fit):,} of {len(pool):,} admissible cells "
          f"({int((y[fit]==1).sum()):,} positive, {int((y[fit]==0).sum()):,} negative) in {time.time()-t0:.0f}s",
          flush=True)

    meta = dict(model="M2", baseline="PRE_ALL", model_version="p66.v1",
                training_population="B1+B2 deduplicated SECONDARY WEAK_REFERENCE",
                B3_status="PREDICTION_ONLY", label_status="WEAK_REFERENCE_NOT_GROUND_TRUTH",
                hyperparameters={k: (None if v is None else v) for k, v in params.items()},
                hyperparameter_selection="best median inner AP over 5 outer runs of PRE_ALL/BUFFERED; "
                                         "outer-test never consulted",
                median_inner_AP=round(med_ap, 5), class_weight="balanced_subsample", random_state=SEED,
                training_n=int(len(fit)), training_available_n=int(len(pool)),
                training_positive_n=int((y[fit] == 1).sum()), training_negative_n=int((y[fit] == 0).sum()),
                training_prevalence=round(float(y[fit].mean()), 5),
                nodata_contract="the training population contains ZERO nodata feature values; cells carrying the "
                                f"{ND} sentinel, or without pre/post optical observations, are NOT scored",
                score="uint16, probability * 10000, nodata 65535",
                feature_manifest_hash=sha256(CFG.TABLES / "p65a_feature_manifest.csv"),
                label_hash={f: sha256(OUT / f / "labels.tif") for f in ("B1", "B2", "B3")},
                folds_hash={f: sha256(OUT / f / "folds.tif") for f in ("B1", "B2")},
                git=subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=CFG.REPO_ROOT, capture_output=True,
                                   text=True).stdout.strip())

    # ---- wall-to-wall inference ----------------------------------------------------------------------------------
    dist, scored = [], {}
    for fid in a.frames:
        tf = time.time()
        F = CG.frame_grid(fid)
        comp = OUT / fid / "composite_preall.tif"
        sp = OUT / fid / "flood_score.tif"; vp = OUT / fid / "prediction_valid.tif"
        sprof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=1, dtype="uint16", crs=CFG.CRS_METRIC,
                     transform=F["transform"], compress="deflate", predictor=2, tiled=True, blockxsize=512,
                     blockysize=ROWS, nodata=SCORE_ND, BIGTIFF="IF_SAFER")
        vprof = dict(sprof); vprof.update(dtype="uint8", nodata=255, predictor=1)
        n_valid = 0; n_tot = F["ny"] * F["nx"]; hist = np.zeros(101, np.int64)
        with rasterio.open(comp) as cs, rasterio.open(sp.with_suffix(".tif.part"), "w", **sprof) as ds, \
                rasterio.open(vp.with_suffix(".tif.part"), "w", **vprof) as dv:
            cn = list(cs.descriptions)
            bidx = [cn.index(nm) for nm in names]
            for r0 in range(0, F["ny"], ROWS):
                r1 = min(r0 + ROWS, F["ny"]); h = r1 - r0
                win = Window(0, r0, F["nx"], h)
                cube = cs.read(window=win)
                Xb = cube[bidx].reshape(len(names), -1).T
                nobs = {k: cube[cn.index(k)].reshape(-1) for k in ("n_obs_pre", "n_obs_event", "n_obs_trace")}
                ok = (~(Xb == ND).any(1)) & (nobs["n_obs_pre"] > 0) & \
                     ((nobs["n_obs_event"] > 0) | (nobs["n_obs_trace"] > 0))
                sc = np.full(Xb.shape[0], SCORE_ND, np.uint16)
                if ok.any():
                    pr = rf.predict_proba(Xb[ok].astype("f4"))[:, 1]
                    sc[ok] = np.clip(np.round(pr * SCORE_SCALE), 0, SCORE_SCALE - 1).astype(np.uint16)
                    hist += np.bincount((pr * 100).astype(np.int32).clip(0, 100), minlength=101)
                n_valid += int(ok.sum())
                ds.write(sc.reshape(h, F["nx"]), 1, window=win)
                dv.write(ok.reshape(h, F["nx"]).astype(np.uint8), 1, window=win)
                del cube, Xb, sc
            ds.update_tags(**{k: json.dumps(v) if isinstance(v, dict) else str(v) for k, v in meta.items()})
            ds.set_band_description(1, "flood_score")
            dv.set_band_description(1, "prediction_valid")
            dv.update_tags(rule=f"all 84 features != {ND} AND n_obs_pre > 0 AND (n_obs_event > 0 OR n_obs_trace > 0)",
                           note="a cell that cannot be predicted is NODATA, never a score of zero")
        for src, dst in ((sp.with_suffix(".tif.part"), sp), (vp.with_suffix(".tif.part"), vp)):
            with rasterio.open(src) as chk:
                assert (chk.height, chk.width) == (F["ny"], F["nx"])
            os.replace(src, dst)
        scored[fid] = n_valid
        dist.append(dict(frame=fid, n_cells=n_tot, n_scored=n_valid,
                         pct_scored=round(100 * n_valid / n_tot, 2),
                         km2_scored=round(n_valid * 1e-4, 1), seconds=round(time.time() - tf),
                         **{f"score_p{p}": round(float(np.searchsorted(hist.cumsum(), hist.sum() * p / 100) / 100), 3)
                            for p in (10, 50, 90, 99)}))
        print(f"  {fid}: scored {n_valid:,} of {n_tot:,} cells ({dist[-1]['pct_scored']:.1f} %, "
              f"{dist[-1]['km2_scored']:,.0f} km2) in {dist[-1]['seconds']}s", flush=True)

    meta["peak_rss_gb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2)
    meta["scored_cells"] = scored
    (OUT / "production_model_metadata.json").write_text(json.dumps(meta, indent=2))
    pd.DataFrame(dist).to_csv(CFG.TABLES / "p66_production_score_distribution.csv", index=False)
    pd.DataFrame([dict(feature=n, i=i + 1) for i, n in enumerate(names)]).to_csv(
        CFG.TABLES / "p66_production_feature_manifest.csv", index=False)
    print(f"\n-> {OUT}/<FRAME>/flood_score.tif, prediction_valid.tif")
    print("-> <case_study>/tables/p66_production_{score_distribution,feature_manifest}.csv")
    print(f"-> {OUT}/production_model_metadata.json")


if __name__ == "__main__":
    main()
