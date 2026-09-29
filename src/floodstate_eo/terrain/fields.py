# New in floodstate-eo, 2026-09-29 (review F02). STATUS: ACTIVE.
"""Spatially correlated Gaussian random fields on a regular lattice, unit marginal variance by construction.

The review of 2026-09-28 (F02) found that the earlier terrain-error field -- white noise on a coarse lattice bilinearly zoomed
to the target lattice -- had a marginal standard deviation of ~0.66 instead of 1, so the class sigma it was multiplied with was
silently reduced, and the interpolation imposed its own covariance rather than a stated one. Here the field is synthesised by
FFT on a periodic embedding of a *stated* covariance model (exponential, Gaussian or spherical) padded by at least four
correlation ranges, and rescaled to unit variance exactly. A nugget share puts white noise on top of the correlated part.
"""
from __future__ import annotations

import numpy as np
from scipy import fft

MODELS = ("exponential", "gaussian", "spherical")


def covariance_kernel(shape: tuple[int, int], cell_m: float, range_m: float, model: str = "exponential") -> np.ndarray:
    """Stationary covariance C(h) on a periodic lattice of `shape` cells (lag measured the short way round), C(0) = 1.

    `range_m` is the e-folding distance of the exponential model, the length scale of the Gaussian model exp(-(h/range)^2)
    and the range of the spherical model."""
    if model not in MODELS:
        raise ValueError(f"model must be one of {MODELS}, got {model!r}")
    if range_m <= 0 or cell_m <= 0:
        raise ValueError("range_m and cell_m must be positive")
    ny, nx = shape
    ly = np.minimum(np.arange(ny), ny - np.arange(ny)) * cell_m
    lx = np.minimum(np.arange(nx), nx - np.arange(nx)) * cell_m
    h = np.hypot(ly[:, None], lx[None, :]) / range_m
    if model == "exponential":
        return np.exp(-h)
    if model == "gaussian":
        return np.exp(-h * h)
    c = 1.0 - 1.5 * h + 0.5 * h ** 3
    c[h >= 1.0] = 0.0
    return c


def nested_kernel(shape: tuple[int, int], cell_m: float, structures) -> np.ndarray:
    """Weighted sum of stationary structures [(weight, range_m, model), ...] on a periodic lattice; C(0) = sum of weights."""
    C = None
    for w, r, m in structures:
        k = float(w) * covariance_kernel(shape, cell_m, float(r), m)
        C = k if C is None else C + k
    return C


class FieldSynthesizer:
    """Precomputed spectral amplitude for repeated draws on one lattice (a Monte-Carlo draws hundreds of fields of the same
    shape and covariance: the kernel and its spectrum are computed once).

    Covariance: one structure (`range_m`, `model`) or a nested sum `structures` = [(weight, range_m, model), ...] of the
    correlated part, plus a white `nugget` share; the correlated part is normalised to 1 - nugget, so the field has UNIT
    marginal variance whatever the parameters.
    Synthesis by circulant embedding: the covariance kernel on the padded periodic lattice is transformed to its spectrum S,
    white noise W is coloured as irfft2(rfft2(W) * sqrt(S)); with numpy's FFT convention the variance of the result is exactly
    C(0) = mean(S). Negative spectral values (an embedding that is not quite positive definite) are clipped and the field is
    rescaled so that its analytic variance is 1 regardless; the padding of `pad_ranges` times the LONGEST range keeps that
    clipping negligible for exponential structures."""

    def __init__(self, shape: tuple[int, int], cell_m: float, range_m: float | None = None, model: str = "exponential", nugget: float = 0.0,
                 pad_ranges: float = 4.0, structures=None):
        if not 0.0 <= nugget < 1.0:
            raise ValueError("nugget must be in [0, 1)")
        if structures is None:
            if range_m is None:
                raise ValueError("give range_m or structures")
            structures = [(1.0, float(range_m), model)]
        structures = [(float(w), float(r), m) for w, r, m in structures]
        if any(w < 0 for w, _, _ in structures) or sum(w for w, _, _ in structures) <= 0:
            raise ValueError("structure weights must be non-negative with a positive sum")
        self.shape = (int(shape[0]), int(shape[1])); self.cell_m, self.nugget = float(cell_m), float(nugget)
        self.structures = structures; self.range_m = max(r for _, r, _ in structures); self.model = "+".join(m for _, _, m in structures)
        ny, nx = self.shape
        pad = int(np.ceil(pad_ranges * self.range_m / cell_m))
        self.Ny, self.Nx = fft.next_fast_len(ny + pad, real=True), fft.next_fast_len(nx + pad, real=True)
        C = nested_kernel((self.Ny, self.Nx), cell_m, structures).astype(np.float64)
        S = np.maximum(fft.rfft2(C).real, 0.0); del C
        # analytic variance of the coloured field = C(0) of the clipped spectrum = mean of the FULL spectrum; the half spectrum
        # of rfft2 counts the interior columns twice in the full one
        weight = np.full(S.shape[1], 2.0); weight[0] = 1.0
        if self.Nx % 2 == 0:
            weight[-1] = 1.0
        var = float((S * weight[None, :]).sum() / (self.Ny * self.Nx))
        self.amp = (np.sqrt(S) / np.sqrt(var)).astype(np.float32)

    def correlation(self, h_m) -> np.ndarray:
        """The model correlation at lag h (h > 0): (1 - nugget) * normalised correlated part."""
        tot = sum(w for w, _, _ in self.structures); h = np.atleast_1d(np.asarray(h_m, float))
        c = sum(w * _rho(h, r, m) for w, r, m in self.structures) / tot
        return (1.0 - self.nugget) * c

    def draw(self, rng: np.random.Generator, dtype=np.float32) -> np.ndarray:
        ny, nx = self.shape
        W = rng.standard_normal((self.Ny, self.Nx), dtype=np.float32)
        F = fft.irfft2(fft.rfft2(W) * self.amp, s=(self.Ny, self.Nx))[:ny, :nx]
        if self.nugget > 0.0:
            F = np.sqrt(1.0 - self.nugget) * F + np.sqrt(self.nugget) * rng.standard_normal((ny, nx), dtype=np.float32)
        return np.ascontiguousarray(F, dtype=dtype)


def _rho(h, range_m, model):
    x = np.asarray(h, float) / range_m
    if model == "exponential":
        return np.exp(-x)
    if model == "gaussian":
        return np.exp(-x * x)
    c = 1.0 - 1.5 * x + 0.5 * x ** 3
    return np.where(x >= 1.0, 0.0, c)


def correlated_field(shape: tuple[int, int], cell_m: float, range_m: float | None, rng: np.random.Generator, model: str = "exponential",
                     nugget: float = 0.0, pad_ranges: float = 4.0, dtype=np.float32, structures=None) -> np.ndarray:
    """One realization of a zero-mean Gaussian random field with the given covariance model and UNIT marginal variance
    (a one-off `FieldSynthesizer(...).draw(rng)`)."""
    return FieldSynthesizer(shape, cell_m, range_m, model, nugget, pad_ranges, structures).draw(rng, dtype)


def empirical_correlation(field: np.ndarray, lag_cells: int, axis: int = 1) -> float:
    """Pearson correlation between the field and itself shifted by `lag_cells` along `axis` (a check, not a fit)."""
    a = np.moveaxis(field, axis, 0)
    x, y = a[:-lag_cells].ravel(), a[lag_cells:].ravel()
    return float(np.corrcoef(x, y)[0, 1])


def bilinear_zoom_std(coarse_shape=(160, 160), zoom: int = 25, seed: int = 472) -> float:
    """The marginal standard deviation of the SUPERSEDED field (white noise bilinearly zoomed), for the record of F02.
    Reproduces the reviewer's diagnostic (Appendix C): ~0.66 instead of 1."""
    from scipy import ndimage
    f = ndimage.zoom(np.random.default_rng(seed).standard_normal(coarse_shape), zoom, order=1)
    return float(f.std())
