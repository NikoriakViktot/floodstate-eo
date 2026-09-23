# Provenance: SWOT-DNIPRO tests/test_p71_change_domain.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CORE_LIBRARY, per 19_MIGRATION_MANIFEST.csv row 31 (migration_phase=5).
# Import fixed: `sys.path` hack + `from p71_s1_event_change import to_db` -> a normal package import of the
# migrated module.
"""The change operator must be a log-ratio, and invalid backscatter must never survive the logarithm.

These exist because p71 differenced linear gamma0 for months in the source repository while documenting its
channels as "dB x 100". The defect passed every gate: shapes, CRS, transforms, nodata, counts and channel names
were all correct, and the only thing wrong was the units the arithmetic was performed in. A test that asserts a
known ratio in decibels cannot be satisfied by the linear implementation, so it closes that failure permanently.
"""
from __future__ import annotations

import numpy as np
import pytest

from floodstate_eo.sar.p71_s1_event_change import to_db

HALVING_DB = -10.0 * np.log10(2.0)      # -3.0103


def test_halving_is_minus_three_db_at_any_absolute_level():
    """A factor-of-two drop is -3.01 dB whether the surface is bright or dark.

    This is the whole point of the correction: a linear difference gives -0.05 for the bright pixel and -0.005
    for the dark one, so it encodes the absolute level as much as the change. The log-ratio does not.
    """
    for pre in (0.5, 0.1, 0.02, 0.004):
        d = to_db(np.array([pre / 2.0], "f4")) - to_db(np.array([pre], "f4"))
        assert d[0] == pytest.approx(HALVING_DB, abs=1e-4)


def test_doubling_is_plus_three_db_and_is_antisymmetric():
    up = to_db(np.array([0.1], "f4")) - to_db(np.array([0.05], "f4"))
    down = to_db(np.array([0.05], "f4")) - to_db(np.array([0.1], "f4"))
    assert up[0] == pytest.approx(-HALVING_DB, abs=1e-4)
    assert up[0] == pytest.approx(-down[0], abs=1e-6)


def test_no_change_is_exactly_zero():
    a = np.array([0.0132, 0.0841, 0.4410], "f4")
    assert np.allclose(to_db(a) - to_db(a), 0.0, atol=0.0)


def test_invalid_backscatter_becomes_nan_not_a_floor():
    """Zero, negative and NaN must not be substituted with a finite decibel value."""
    out = to_db(np.array([0.0, -0.01, np.nan, 1e-12, 0.08], "f4"))
    assert np.isnan(out[0]) and np.isnan(out[1]) and np.isnan(out[2])
    assert np.isfinite(out[3]), "a tiny but positive measurement is valid data, not an error"
    assert np.isfinite(out[4])


def test_invalidity_propagates_through_median_mad_and_order_statistics():
    """One bad sample must not poison the baseline, and must not be counted as an extreme."""
    rng = np.random.default_rng(0)
    P = to_db(rng.uniform(0.05, 0.15, size=(9, 64)).astype("f4"))
    P_bad = P.copy()
    P_bad[3, :] = np.nan
    good = np.delete(np.arange(9), 3)
    assert np.allclose(np.nanmedian(P_bad, 0), np.median(P[good], 0), atol=1e-5)
    assert np.isfinite(np.nanmin(P_bad, 0)).all()


def test_linear_subtraction_and_log_ratio_are_not_monotonically_related():
    """The correction is a different statistic, not a rescaling of the old one.

    A monotone transform of a ratio leaves its ROC unchanged, so "we took a logarithm" would not by itself
    justify anything. The claim here is narrower and checkable: a linear difference and a log-ratio ORDER
    PIXELS DIFFERENTLY, because the former depends on the absolute level. A dark pixel halving ranks below a
    bright pixel losing a third under subtraction, and above it under the log-ratio -- so the two cannot be
    connected by any monotone function.
    """
    pre = np.array([0.30, 0.02], "f4")
    post = np.array([0.20, 0.01], "f4")
    lin = post - pre                                  # -0.100 vs -0.010
    log = to_db(post) - to_db(pre)                    # -1.76 dB vs -3.01 dB
    assert lin[0] < lin[1], "subtraction ranks the bright pixel as the larger change"
    assert log[0] > log[1], "the log-ratio ranks the dark pixel as the larger change"
