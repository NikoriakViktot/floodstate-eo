"""Review F09: the M2 operating threshold comes from spatial inner out-of-fold scores, never from the fit set."""
import numpy as np

from floodstate_eo.fusion import p65b_m2_spatial_cv as P


def _data(n=6000, seed=1):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 5)).astype("f4")
    y = (X[:, 0] + 0.5 * rng.normal(size=n) > 1.0).astype(np.int8)
    blk = rng.integers(0, 60, n)                                   # 60 spatial blocks
    return X, y, blk


def test_calibration_cells_are_never_in_the_fit_set_and_never_in_the_outer_test():
    X, y, blk = _data()
    outer_test = np.flatnonzero(blk < 12); itr = np.flatnonzero(blk >= 12)
    ub = np.unique(blk[itr]); iass = np.array([dict(zip(ub, np.arange(len(ub)) % 3))[b] for b in blk[itr]])
    params = {"n_estimators": 20, "max_depth": 6, "min_samples_leaf": 5, "max_features": "sqrt"}
    thr, n_cal, pairs = P.inner_oof_threshold(X, y, itr, iass, params, np.random.default_rng(0), fit_n=1500, cal_n=800, jobs=1)
    assert len(pairs) == 3 and n_cal == sum(len(c) for _, c in pairs)
    for fit, cal in pairs:
        assert np.intersect1d(fit, cal).size == 0                  # a forest never scores a cell it was fit on
        assert np.isin(cal, itr).all() and not np.isin(cal, outer_test).any()
        assert np.isin(fit, itr).all() and not np.isin(fit, outer_test).any()
    assert 0.0 < thr < 1.0


def test_the_calibration_units_are_whole_spatial_blocks():
    X, y, blk = _data(seed=2)
    itr = np.arange(len(y)); ub = np.unique(blk); iass = np.array([dict(zip(ub, np.arange(len(ub)) % 3))[b] for b in blk])
    params = {"n_estimators": 10, "max_depth": 4, "min_samples_leaf": 5, "max_features": "sqrt"}
    _, _, pairs = P.inner_oof_threshold(X, y, itr, iass, params, np.random.default_rng(0), fit_n=10**6, cal_n=10**6, jobs=1)
    for fit, cal in pairs:
        assert not set(blk[fit]) & set(blk[cal])                   # no block on both sides


def test_an_in_sample_threshold_is_higher_than_the_out_of_fold_one():
    """The defect the review found: a forest scored on its own training cells is over-confident, so the threshold that
    reaches the target recall there sits higher than the out-of-fold one -- and recall on new data falls short."""
    X, y, blk = _data(n=8000, seed=3)
    itr = np.arange(len(y)); ub = np.unique(blk); iass = np.array([dict(zip(ub, np.arange(len(ub)) % 3))[b] for b in blk])
    params = {"n_estimators": 50, "max_depth": None, "min_samples_leaf": 1, "max_features": "sqrt"}
    thr_oof, _, _ = P.inner_oof_threshold(X, y, itr, iass, params, np.random.default_rng(0), fit_n=10**6, cal_n=10**6, jobs=1)
    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(**params, class_weight="balanced_subsample", n_jobs=1, random_state=P.SEED).fit(X, y)
    hold = itr[iass == 0]
    thr_in = P.thr_at_recall(y[hold], rf.predict_proba(X[hold])[:, 1], P.TARGET_RECALL)
    assert thr_in > thr_oof
