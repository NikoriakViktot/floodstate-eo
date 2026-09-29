# New in floodstate-eo, 2026-09-29 (review F13). STATUS: ACTIVE.
"""Bounded 1-D interpolation: NaN outside the tabulated domain, never numpy's silent endpoint plateau.

A level-area-volume table defined from 10 m upward must not answer 6.95 km3 at 5 m just because np.interp clamps to its
first row (F13). Callers that need an extrapolation model must state one; this function refuses to invent it.
"""
from __future__ import annotations

import numpy as np


def bounded_interp(x, xp, fp, left=np.nan, right=np.nan) -> np.ndarray:
    """Linear interpolation of (xp, fp) at x, with `left`/`right` (default NaN) outside [min(xp), max(xp)].
    `xp` may be given in increasing or decreasing order; it must be strictly monotonic and free of NaN."""
    xp = np.asarray(xp, float); fp = np.asarray(fp, float); x = np.asarray(x, float)
    if xp.ndim != 1 or xp.shape != fp.shape or len(xp) < 2:
        raise ValueError("xp and fp must be 1-D of the same length >= 2")
    if not np.isfinite(xp).all():
        raise ValueError("xp contains NaN")
    d = np.diff(xp)
    if (d > 0).all():
        pass
    elif (d < 0).all():
        xp, fp = xp[::-1], fp[::-1]
    else:
        raise ValueError("xp must be strictly monotonic")
    out = np.interp(x, xp, fp)
    out = np.where(x < xp[0], left, out); out = np.where(x > xp[-1], right, out)
    return out
