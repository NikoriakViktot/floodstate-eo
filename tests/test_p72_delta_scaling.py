"""p72 d* bands: both sides of the difference in the same units before int16 rounding/clipping (KNOWN_ISSUES.md)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

M6 = Path(__file__).resolve().parents[1] / "case_studies" / "kakhovka_2023" / "workflows" / "m6"


def _p72():
    s = importlib.util.spec_from_file_location("p72", M6 / "p72_s2_sparse_event_support.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def test_delta_is_in_index_units_and_never_saturates():
    P = _p72()
    pre_raw = np.array([-5000.0, 0.0, 3000.0, 8000.0])          # composite int16 x 10000
    event = np.array([0.2, -0.1, 0.3, -0.9])                     # already value / 10000
    d, q = P.delta_i16(event, pre_raw)
    np.testing.assert_allclose(d, event - pre_raw / 10000.0)
    np.testing.assert_array_equal(q, np.round(d * 10000))
    assert np.all(np.abs(q) < 32767)
    assert P.sanity(q, np.ones_like(q, bool))["ok"]


def test_sanity_gate_rejects_the_old_bug():
    P = _p72()
    pre_raw = np.array([-5000.0, 3000.0]); event = np.array([0.2, 0.3])
    buggy = np.clip(np.round((event - pre_raw) * 10000), -32767, 32767)     # the pre-fix formula
    assert not P.sanity(buggy, np.ones_like(buggy, bool))["ok"]
