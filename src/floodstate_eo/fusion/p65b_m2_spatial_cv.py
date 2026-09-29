# Provenance: SWOT-DNIPRO scripts/p65b_m2_spatial_cv.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 11 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo package imports.
# Logic changed 2026-09-29 (review 2026-09-28, F09): the operating threshold is calibrated on spatial inner out-of-fold
# predictions (`inner_oof_threshold`, fit and calibration cells disjoint, asserted and tested) instead of the outer-train
# forest's in-sample scores; the superseded in-sample threshold is recorded beside it. The calibration draws from its own
# random generator, so tuning, refit sample and outer-test scores follow the original sequence. `--exclude` drops features
# by name pattern (e.g. the post-event TRACE window) into separately tagged outputs.
"""P65b -- M2 (Sentinel-2 only) under the frozen evaluation design: 3 pre-event baselines x 2 CV regimes.

ONLY M2 IS RUN HERE. M3 (S2 + S1) is deliberately absent: the weak labels ARE a Sentinel-1 rule, so feeding S1
evidence as features would measure reconstruction of the target-generation rule rather than what SAR adds. That
comparison waits for an independent reference (see the Methods, external-reference tiers).

WHAT EACH RUN IS
    baseline   preall | preseas | nmatch      differ ONLY in which dates fill the pre-event slot
    regime     block                          5 km spatial blocks, five outer folds, no buffer
               buffered                       THE SAME outer test folds, with every training cell within 3.5 km of
                                              the test population removed
The two regimes share their test sets by construction, so the difference in AP and F1 is attributable to the removed
training proximity and to nothing else. It is needed rather than decorative: the measured median train-to-test
distance under `block` is about 950 m, and 99.5 % of test cells have a training cell inside the 3.5 km predictor
autocorrelation range.

NESTED, AND SPATIAL AT BOTH LEVELS. Inner folds are whole 5 km blocks drawn from the outer training set only, and
for `buffered` they are formed AFTER the buffer has been removed -- otherwise the strict run would be tuned on the
very proximity it exists to exclude. Hyperparameters are chosen on the inner split; the operating threshold is taken
at the target recall from the pooled inner out-of-fold scores of the chosen hyperparameters (every calibration cell
scored by a forest that never saw it); both are frozen, the forest is refit on the full outer-training set and applied
once to the untouched outer test fold.

BASELINE CHOICE IS NOT TUNED. The three baselines are three fixed models compared on aggregate out-of-fold results;
selecting among them per fold would make the scientific ablation part of the tuning.

REPORTING follows the two frozen layers, over the same population for every model: SECONDARY (all admissible weak
labels of B1 and B2) is the main result; PRIMARY (consensus cells, where two independent S1 caches agree) is a
label-quality sensitivity subset, reported as POOLED out-of-fold only -- consensus samples are spread so unevenly
that one fold contains none at all. Confidence intervals come from a bootstrap over spatial blocks, never over
pixels.

Outputs: <case_study>/tables/p65b_m2_{main,folds,bootstrap,tuning,importance}.csv, $BULK_ROOT/frames10/_ml/oof_*.npy
"""
from __future__ import annotations
import argparse, itertools, re, time, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import ndimage
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from .. import _kakhovka_legacy_config as CFG

ML = CFG.BULK_ROOT / "frames10" / "_ml"
BASELINES = ("preall", "preseas", "nmatch")
REGIMES = ("block", "buffered")
BUFFER_M = 3500.0
COARSE = 40.0
TARGET_RECALL = 0.90
N_INNER = 3
GRID = dict(n_estimators=[300, 500], max_depth=[None, 20, 40], min_samples_leaf=[1, 5, 20],
            max_features=["sqrt", 0.5])
TUNE_N = 25_000
FIT_N = 300_000
N_BOOT = 200
SEED = 20260921


class _Cols:
    """Column subset of a row-major memmap that keeps fancy row indexing lazy: X[rows] reads only those rows."""
    def __init__(self, X, cols):
        self.X, self.cols = X, np.asarray(cols); self.shape = (X.shape[0], len(self.cols))

    def __getitem__(self, rows):
        return np.asarray(self.X[rows])[:, self.cols]


def metrics(y, s, thr):
    p = s >= thr
    tp = int((p & (y == 1)).sum()); fp = int((p & (y == 0)).sum()); fn = int((~p & (y == 1)).sum())
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    return dict(AP=float(average_precision_score(y, s)), AUC=float(roc_auc_score(y, s)),
                precision=prec, recall=rec, F1=2 * prec * rec / max(prec + rec, 1e-12),
                IoU=tp / max(tp + fp + fn, 1), TP=tp, FP=fp, FN=fn)


def thr_at_recall(y, s, target):
    o = np.argsort(-s); ys = y[o]
    tp = np.cumsum(ys == 1); need = target * max(int((y == 1).sum()), 1)
    i = int(np.searchsorted(tp, need))
    return float(s[o][min(i, len(s) - 1)])


def inner_oof_threshold(X, y, itr, iass, params, rng, fit_n, cal_n, jobs, target=TARGET_RECALL, seed=SEED):
    """Operating threshold at `target` recall from spatial inner out-of-fold scores (review F09). For every inner fold j
    a forest with `params` is fit on the other inner folds of the outer-train `itr` and scores fold j, so no calibration
    cell was seen by the forest that scored it. Returns (threshold, n_calibration_cells, [(fit, cal), ...])."""
    ys, ss, pairs = [], [], []
    for j in np.unique(iass):
        fit = itr[iass != j]; cal = itr[iass == j]
        if len(fit) > fit_n:
            fit = np.sort(rng.choice(fit, fit_n, replace=False))
        if len(cal) > cal_n:
            cal = np.sort(rng.choice(cal, cal_n, replace=False))
        assert np.intersect1d(fit, cal).size == 0, "calibration cells inside the fit set"
        rf = RandomForestClassifier(**params, class_weight="balanced_subsample", n_jobs=jobs, random_state=seed)
        rf.fit(X[fit].astype("f4"), y[fit])
        ys.append(y[cal]); ss.append(rf.predict_proba(X[cal].astype("f4"))[:, 1]); pairs.append((fit, cal))
    ys, ss = np.concatenate(ys), np.concatenate(ss)
    return thr_at_recall(ys, ss, target), len(ys), pairs


def buffer_mask(I, test):
    """True for training cells FARTHER than BUFFER_M from any test cell, on a 40 m auxiliary grid."""
    x0, x1 = I.x.min() - COARSE, I.x.max() + COARSE
    y0, y1 = I.y.min() - COARSE, I.y.max() + COARSE
    nx = int(np.ceil((x1 - x0) / COARSE)) + 1; ny = int(np.ceil((y1 - y0) / COARSE)) + 1
    cx = ((I.x.to_numpy() - x0) / COARSE).astype(np.int32)
    cy = ((y1 - I.y.to_numpy()) / COARSE).astype(np.int32)
    g = np.zeros((ny, nx), bool)
    g[cy[test], cx[test]] = True
    d = ndimage.distance_transform_edt(~g, sampling=COARSE)
    return d[cy, cx] >= BUFFER_M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baselines", nargs="*", default=list(BASELINES))
    ap.add_argument("--regimes", nargs="*", default=list(REGIMES))
    ap.add_argument("--tune-n", type=int, default=TUNE_N)
    ap.add_argument("--fit-n", type=int, default=FIT_N)
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--jobs", type=int, default=32)
    ap.add_argument("--folds", nargs="*", type=int, default=None, help="restrict outer folds (smoke test)")
    ap.add_argument("--grid-limit", type=int, default=None, help="use only the first N grid combinations (smoke)")
    ap.add_argument("--cal-n", type=int, default=300_000, help="calibration cells per inner fold (inner out-of-fold threshold)")
    ap.add_argument("--exclude", default=None, help="regex on feature names to drop (e.g. 'trace'); outputs tagged _no<regex>")
    a = ap.parse_args()

    I = pd.read_parquet(ML / "index.parquet")
    y = I.label.to_numpy().astype(np.int8)
    fold = I.outer_fold.to_numpy(); blk = I.blk5.to_numpy(); tier = I.tier.to_numpy()
    names = pd.read_csv(CFG.TABLES / "p65a_feature_manifest.csv").feature.tolist()
    keep = np.arange(len(names)) if not a.exclude else np.array([i for i, f in enumerate(names) if not re.search(a.exclude, f, re.IGNORECASE)])
    tag = "" if not a.exclude else "_no" + re.sub(r"[^a-z0-9]+", "", a.exclude.lower())
    n = len(I)
    print(f"population {n:,} cells, prevalence {y.mean():.4f}, {len(np.unique(blk)):,} blocks of 5 km; {len(keep)} of {len(names)} features"
          + (f" (dropped /{a.exclude}/: {[names[i] for i in range(len(names)) if i not in set(keep.tolist())]})" if a.exclude else ""), flush=True)
    rng = np.random.default_rng(SEED)
    main_rows, fold_rows, boot_rows, tune_rows, imp_rows = [], [], [], [], []
    combos = [dict(zip(GRID, v)) for v in itertools.product(*GRID.values())]
    if a.grid_limit:
        combos = combos[:a.grid_limit]
    print(f"{len(combos)} hyperparameter combinations x {N_INNER} inner folds per outer fold", flush=True)

    for bl in a.baselines:
        X0 = np.load(ML / f"X_{bl}.i2", mmap_mode="r")
        assert X0.shape == (n, len(names)), X0.shape
        X = X0 if len(keep) == len(names) else _Cols(X0, keep)
        for rg in a.regimes:
            t0 = time.time(); oof = np.full(n, np.nan, "f4"); thr_used = {}
            rng_cal = np.random.default_rng([SEED, BASELINES.index(bl), REGIMES.index(rg)])   # the calibration's own stream
            for k in (a.folds if a.folds else sorted(set(fold.tolist()))):
                te = fold == k
                tr = (~te)
                if rg == "buffered":
                    tr = tr & buffer_mask(I, te)
                itr = np.flatnonzero(tr); ite = np.flatnonzero(te)
                # ---- inner spatial CV on the (already buffered) training set ------------------------------------
                tb = blk[itr]; ub = np.unique(tb); rng.shuffle(ub)
                inner = {b: i % N_INNER for i, b in enumerate(ub)}
                iass = np.array([inner[b] for b in tb])
                best, best_ap = None, -1.0
                for cmb in combos:
                    aps = []
                    for j in range(N_INNER):
                        a_tr = itr[iass != j]; a_te = itr[iass == j]
                        if len(a_tr) > a.tune_n:
                            a_tr = rng.choice(a_tr, a.tune_n, replace=False)
                        if len(a_te) > a.tune_n:
                            a_te = rng.choice(a_te, a.tune_n, replace=False)
                        a_tr = np.sort(a_tr); a_te = np.sort(a_te)   # a memmap wants ascending fancy indices
                        rf = RandomForestClassifier(**cmb, class_weight="balanced_subsample",
                                                    n_jobs=a.jobs, random_state=SEED)
                        rf.fit(X[a_tr].astype("f4"), y[a_tr])
                        aps.append(average_precision_score(y[a_te],
                                                           rf.predict_proba(X[a_te].astype("f4"))[:, 1]))
                    m = float(np.mean(aps))
                    tune_rows.append(dict(baseline=bl, regime=rg, outer_fold=k, **cmb, inner_AP=round(m, 5)))
                    if m > best_ap:
                        best_ap, best = m, cmb
                # ---- refit on the full outer-train; threshold from inner out-of-fold scores (F09) ----------------
                a_tr = itr if len(itr) <= a.fit_n else np.sort(rng.choice(itr, a.fit_n, replace=False))
                rf = RandomForestClassifier(**best, class_weight="balanced_subsample", n_jobs=a.jobs,
                                            random_state=SEED)
                rf.fit(X[a_tr].astype("f4"), y[a_tr])
                hold = itr[iass == 0]                           # SUPERSEDED in-sample threshold, kept for comparison only:
                hold = hold if len(hold) <= 300_000 else np.sort(rng.choice(hold, 300_000, replace=False))
                thr_in = thr_at_recall(y[hold], rf.predict_proba(X[hold].astype("f4"))[:, 1], TARGET_RECALL)
                thr, n_cal, pairs = inner_oof_threshold(X, y, itr, iass, best, rng_cal, a.fit_n, a.cal_n, a.jobs)
                assert all(np.isin(c, itr).all() and not np.isin(c, ite).any() for _, c in pairs)
                thr_used[k] = thr
                sc = np.empty(len(ite), "f4")
                for s0 in range(0, len(ite), 2_000_000):
                    sl = ite[s0:s0 + 2_000_000]
                    sc[s0:s0 + len(sl)] = rf.predict_proba(X[sl].astype("f4"))[:, 1]
                oof[ite] = sc
                # The strict regime removes 56-60 % of the training data. If a buffered fold then behaves oddly,
                # these columns say immediately whether that is a spatial-transfer effect or simply a much smaller
                # and differently balanced training set.
                fold_rows.append(dict(baseline=bl, regime=rg, outer_fold=k, n_train=len(itr),
                                      n_train_pos=int((y[itr] == 1).sum()), n_train_neg=int((y[itr] == 0).sum()),
                                      train_prevalence=round(float(y[itr].mean()), 5),
                                      n_train_available=int((fold != k).sum()),
                                      train_kept_pct=round(100 * len(itr) / max(int((fold != k).sum()), 1), 2),
                                      n_fit_pos=int((y[a_tr] == 1).sum()), n_fit_neg=int((y[a_tr] == 0).sum()),
                                      n_train_fit=len(a_tr), n_test=len(ite),
                                      test_prevalence=round(float(y[ite].mean()), 4), threshold=round(thr, 4),
                                      threshold_source="inner out-of-fold (fit and calibration disjoint)", n_calibration=n_cal,
                                      threshold_insample_superseded=round(thr_in, 4),
                                      recall_at_insample_superseded=round(metrics(y[ite], sc, thr_in)["recall"], 5),
                                      best_params=str(best), inner_AP=round(best_ap, 5),
                                      **{kk: round(v, 5) if isinstance(v, float) else v
                                         for kk, v in metrics(y[ite], sc, thr).items()}))
                print(f"  {bl}/{rg} fold {k}: n_tr {len(itr):,} -> fit {len(a_tr):,}, AP "
                      f"{fold_rows[-1]['AP']:.4f}, F1 {fold_rows[-1]['F1']:.4f}  ({time.time()-t0:.0f}s)", flush=True)
                for nm, v in zip(names, rf.feature_importances_):
                    imp_rows.append(dict(baseline=bl, regime=rg, outer_fold=k, feature=nm, gini=round(float(v), 6)))
                # CHECKPOINT PER OUTER FOLD. Hours of fitting must not be lost to a system or memory event, and
                # the partial OOF vector is itself the restart point.
                np.save(ML / f"oof_{bl}_{rg}{tag}.npy", oof)
                for cnm, crows in (("folds", fold_rows), ("tuning", tune_rows), ("importance", imp_rows)):
                    pd.DataFrame(crows).to_csv(CFG.TABLES / f"p65b_m2_{cnm}{tag}.csv", index=False)
            np.save(ML / f"oof_{bl}_{rg}{tag}.npy", oof)
            # ---- pooled OOF over the two layers -------------------------------------------------------------
            thr_p = float(np.median(list(thr_used.values())))
            for layer, sel in (("SECONDARY", np.ones(n, bool)), ("PRIMARY", np.isin(tier, (2, 3)))):
                m = sel & np.isfinite(oof)
                mm = metrics(y[m], oof[m], thr_p)
                main_rows.append(dict(model="M2", baseline=bl, regime=rg, layer=layer, n=int(m.sum()),
                                      km2=round(float(m.sum()) * 1e-4, 1),
                                      prevalence=round(float(y[m].mean()), 4), pooled_threshold=round(thr_p, 4),
                                      **{kk: round(v, 5) if isinstance(v, float) else v for kk, v in mm.items()}))
                bb = blk[m]; ub = np.unique(bb); yb = y[m]; sb = oof[m]
                idx_by_block = {b: np.flatnonzero(bb == b) for b in ub}
                aps, f1s = [], []
                for _ in range(a.n_boot):
                    pick = rng.choice(ub, len(ub), replace=True)
                    ii = np.concatenate([idx_by_block[b] for b in pick])
                    if len(np.unique(yb[ii])) < 2:
                        continue
                    r = metrics(yb[ii], sb[ii], thr_p); aps.append(r["AP"]); f1s.append(r["F1"])
                if aps:
                    boot_rows.append(dict(model="M2", baseline=bl, regime=rg, layer=layer, n_boot=len(aps),
                                          n_blocks=len(ub),
                                          AP_lo=round(float(np.percentile(aps, 2.5)), 5),
                                          AP_med=round(float(np.median(aps)), 5),
                                          AP_hi=round(float(np.percentile(aps, 97.5)), 5),
                                          F1_lo=round(float(np.percentile(f1s, 2.5)), 5),
                                          F1_med=round(float(np.median(f1s)), 5),
                                          F1_hi=round(float(np.percentile(f1s, 97.5)), 5)))
                print(f"  {bl}/{rg} {layer}: AP {mm['AP']:.4f} F1 {mm['F1']:.4f} on {m.sum():,} cells "
                      f"(prevalence {y[m].mean():.4f})", flush=True)
            for nm, rows in (("main", main_rows), ("folds", fold_rows), ("bootstrap", boot_rows),
                             ("tuning", tune_rows), ("importance", imp_rows)):
                pd.DataFrame(rows).to_csv(CFG.TABLES / f"p65b_m2_{nm}{tag}.csv", index=False)
        del X, X0
    print("\n" + pd.DataFrame(main_rows)[["baseline", "regime", "layer", "AP", "AUC", "precision", "recall",
                                          "F1", "IoU", "prevalence"]].to_string(index=False))
    print("\n-> <case_study>/tables/p65b_m2_{main,folds,bootstrap,tuning,importance}.csv")


if __name__ == "__main__":
    main()
