"""Review F11: an empty (re)sample gives an UNDEFINED metric, never a zero; the bootstrap counts defined resamples."""
import importlib.util
import math
from pathlib import Path

import numpy as np
import pandas as pd

_P = Path(__file__).resolve().parents[1] / "case_studies/kakhovka_2023/workflows/m6/m6_eval.py"
_s = importlib.util.spec_from_file_location("m6_eval", _P); E = importlib.util.module_from_spec(_s); _s.loader.exec_module(E)


def test_empty_support_is_undefined_not_zero():
    m = E._m(0, 0, 0)
    assert all(math.isnan(m[k]) for k in ("precision", "recall", "F1", "IoU"))


def test_a_genuine_miss_is_still_zero():
    m = E._m(0, 5, 7)                                   # predictions and positives exist, none overlap
    assert m["precision"] == 0 and m["recall"] == 0 and m["F1"] == 0 and m["IoU"] == 0


def test_no_prediction_on_existing_positives():
    m = E._m(0, 0, 4)                                   # nothing predicted: precision undefined, recall a true zero
    assert math.isnan(m["precision"]) and m["recall"] == 0 and math.isnan(m["F1"])


def test_paired_bootstrap_counts_resamples_without_support():
    rng = np.random.default_rng(0)
    cols = {c: rng.integers(0, 50, 10) for c in ("tp_px", "fp_px", "fn_px")}
    a = pd.DataFrame({"frame": "B1", "block": np.arange(10), **cols})
    a.loc[:7, ["tp_px", "fp_px", "fn_px"]] = 0          # most blocks carry no support at all
    b = a.copy()
    orig = E.endpoints
    E.endpoints = lambda s: {"F1": E._m(s["tp_px"], s["fp_px"], s["fn_px"])["F1"]}
    try:
        R = E.paired_bootstrap(a, b, n=300, seed=1)
    finally:
        E.endpoints = orig
    assert 0 < R.loc["F1", "n_defined"] < 300           # empty resamples are counted as undefined, not as F1 = 0
