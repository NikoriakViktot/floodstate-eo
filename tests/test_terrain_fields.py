"""Review F02: the stochastic terrain field must carry the stated marginal variance and covariance. Runs without bulk data."""
from __future__ import annotations

import numpy as np
import pytest

from floodstate_eo.terrain.fields import (
    FieldSynthesizer,
    bilinear_zoom_std,
    correlated_field,
    covariance_kernel,
    empirical_correlation,
)


def test_unit_marginal_variance_and_stated_correlation():
    rng = np.random.default_rng(1)
    f = correlated_field((1024, 1024), cell_m=20.0, range_m=300.0, rng=rng, model="exponential")
    assert f.dtype == np.float32 and f.shape == (1024, 1024)
    assert abs(float(f.std()) - 1.0) < 0.03, f.std()
    assert abs(float(f.mean())) < 0.05
    r = empirical_correlation(f, lag_cells=15, axis=1)                       # one range -> e^-1
    assert abs(r - np.exp(-1.0)) < 0.05, r
    r2 = empirical_correlation(f, lag_cells=15, axis=0)
    assert abs(r2 - np.exp(-1.0)) < 0.05, r2


def test_seed_reproducible_and_models_valid():
    a = correlated_field((64, 96), 20.0, 200.0, np.random.default_rng(7))
    b = correlated_field((64, 96), 20.0, 200.0, np.random.default_rng(7))
    assert np.array_equal(a, b)
    for m in ("gaussian", "spherical"):
        g = correlated_field((256, 256), 20.0, 200.0, np.random.default_rng(3), model=m)
        assert abs(float(g.std()) - 1.0) < 0.06
    with pytest.raises(ValueError):
        covariance_kernel((8, 8), 20.0, 100.0, model="cubic")
    with pytest.raises(ValueError):
        correlated_field((8, 8), 20.0, 100.0, np.random.default_rng(0), nugget=1.0)


def test_nugget_adds_white_share():
    f = correlated_field((512, 512), 20.0, 300.0, np.random.default_rng(5), nugget=0.5)
    assert abs(float(f.std()) - 1.0) < 0.04
    r = empirical_correlation(f, 15, 1)
    assert abs(r - 0.5 * np.exp(-1.0)) < 0.05, r


def test_kernel_is_one_at_zero_lag_and_symmetric():
    C = covariance_kernel((32, 40), 20.0, 100.0)
    assert C[0, 0] == 1.0 and np.allclose(C[1, 0], C[-1, 0]) and np.allclose(C[0, 3], C[0, -3])


def test_superseded_zoom_field_lost_variance():
    """The record of F02: white noise bilinearly zoomed had std ~0.66 (reviewer's Appendix C), not 1."""
    assert 0.6 < bilinear_zoom_std() < 0.72


def test_synthesizer_reuses_the_spectrum_and_matches_the_one_off_function():
    syn = FieldSynthesizer((300, 500), 20.0, 250.0)
    a = syn.draw(np.random.default_rng(9)); b = correlated_field((300, 500), 20.0, 250.0, np.random.default_rng(9))
    assert np.array_equal(a, b) and a.shape == (300, 500)
    draws = np.stack([syn.draw(np.random.default_rng(k)) for k in range(20)])
    assert abs(float(draws.std()) - 1.0) < 0.03                              # unit variance over many realizations
    assert abs(float(draws[:, 150, 250].std()) - 1.0) < 0.35                 # and at a single cell (20 draws: loose)


def test_nested_structures_keep_unit_variance_and_the_stated_correlation():
    syn = FieldSynthesizer((1024, 1024), 20.0, structures=[(0.4, 60.0, "exponential"), (0.6, 600.0, "exponential")], nugget=0.1)
    f = syn.draw(np.random.default_rng(21))
    assert abs(float(f.std()) - 1.0) < 0.04
    for lag in (3, 15, 30):                                                    # 60, 300, 600 m
        expect = float(syn.correlation(lag * 20.0)[0])
        assert abs(empirical_correlation(f, lag, 1) - expect) < 0.06, (lag, expect)
    with pytest.raises(ValueError):
        FieldSynthesizer((8, 8), 20.0, structures=[(-0.1, 60.0, "exponential")])
    with pytest.raises(ValueError):
        FieldSynthesizer((8, 8), 20.0)
