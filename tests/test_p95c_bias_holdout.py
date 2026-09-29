"""Review F12: the class bias that corrects the terrain is re-estimated WITHOUT the ICESat-2 passes it is checked on."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

_P = Path(__file__).resolve().parents[1] / "case_studies/kakhovka_2023/workflows/m6/p95c_icesat2_check.py"
_s = importlib.util.spec_from_file_location("p95c", _P); M = importlib.util.module_from_spec(_s); _s.loader.exec_module(M)
TRUE = {10: 1.0, 30: 0.3, 40: 0.1, 50: 0.4, 60: 0.2, 90: 0.5, 20: 0.7}           # class residual bias; 20 (shrub) has no row


def _population(n=30000, seed=0, n_passes=40):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2021-01-03", periods=n_passes, freq=f"{1160 // n_passes}D")   # passes on both sides of the breach
    C = pd.DataFrame(dict(zone=rng.choice(M.ZONES, n), wc=rng.choice(list(TRUE), n), pass_day=rng.choice(days, n)))
    C["r"] = C.wc.map(TRUE) + rng.normal(0, 0.2, n)
    return C, days


def test_a_held_out_pass_never_calibrates_its_own_check_and_is_checked_exactly_once():
    C, days = _population()
    check_days = days[::3]
    seen = {}
    for scheme, fold, held in M.holdout_folds(C.pass_day, check_days):
        cal = C[~C.pass_day.isin(held)]
        assert not cal.pass_day.isin(held).any()
        for d in check_days[check_days.isin(held)]:
            seen[(scheme, d)] = seen.get((scheme, d), 0) + 1
    for scheme in ("leave_one_pass_out", "five_fold_passes", "epoch"):
        assert all(seen.get((scheme, d)) == 1 for d in check_days), scheme


def test_the_epoch_folds_hold_out_every_pass_on_one_side_of_the_breach():
    C, days = _population()
    E = {fold: held for scheme, fold, held in M.holdout_folds(C.pass_day, days[:5]) if scheme == "epoch"}
    assert (E["calibrate_pre_check_post"] >= M.BREACH).all() and set(E["calibrate_pre_check_post"]) == set(days[days >= M.BREACH])
    assert (E["calibrate_post_check_pre"] < M.BREACH).all() and set(E["calibrate_post_check_pre"]) == set(days[days < M.BREACH])


def test_the_class_rule_is_the_p95_rule():
    C, _ = _population()
    few = C.index[(C.zone == M.ZONES[0]) & (C.wc == 60)][150:]                  # leave 150 bare points in the first zone: < N_MIN
    C = C.drop(few)
    b, used = M.class_bias(C)
    assert used[M.ZONES[0]][60] == "pooled" and used[M.ZONES[1]][60] == "own zone" and used[M.ZONES[0]][10] == "own zone"
    assert abs(b[M.ZONES[0]][60] - C[C.wc == 60].r.median()) < 1e-12
    assert abs(b[M.ZONES[0]]["other"] - C[C.wc.isin(list(M.WC6))].r.median()) < 1e-12   # shrub is not in the pooled 'other'
    assert np.allclose(M.bias_at(b[M.ZONES[1]], [10, 20, -1]), [b[M.ZONES[1]][10], b[M.ZONES[1]]["other"], b[M.ZONES[1]]["other"]])


def test_an_anomalous_pass_cannot_correct_itself(monkeypatch):
    """The defect the review names: with in-sample calibration a pass's own error leaks into the bias that 'checks' it."""
    C, days = _population(n_passes=12)
    bad = days[7]; C.loc[C.pass_day == bad, "r"] += 3.0                         # one pass 3 m off (e.g. a cloud or water top)
    K = C[C.pass_day.isin(days[5:10])].sample(3000, random_state=1).copy()
    K = K.assign(cat=3, res=K.r, seam=K.r + 10.0, H_ice=10.0, wse=11.0)
    monkeypatch.setattr(M, "check_p95j", lambda b: None)
    K2, F, _, _ = M.bias_holdout(C, K)
    k = K2[K2.pass_day == bad]
    shift_in = (k.b_in - k.wc.map(TRUE).where(k.wc.isin(list(M.WC6)))).dropna()
    shift_lopo = (k.b_leave_one_pass_out - k.wc.map(TRUE).where(k.wc.isin(list(M.WC6)))).dropna()
    assert shift_in.abs().median() > 0.02 and shift_in.abs().median() > 3 * shift_lopo.abs().median()   # in-sample: the bad pass pulls its own bias
    assert {"leave_one_pass_out", "five_fold_passes", "epoch"} <= set(F.scheme)
    H = M.holdout_rows(K2)
    assert set(H.scheme) == {"leave_one_pass_out", "five_fold_passes", "epoch"} and (H.n_passes == 5).all()
