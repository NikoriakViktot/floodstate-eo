# New in floodstate-eo, 2026-09-29 (review F06). STATUS: ACTIVE.
"""Cells connected to a seed network -- the connectivity core of the terrain reconstruction.

    P_t = Connected_S( { x : z_terrain(x) < H(x, t) } )

`connected_to_seed` keeps every connected component of the candidate mask that touches at least one seed cell. It must be
evaluated on the WHOLE terrain graph (the mosaic of all zones); cutting the graph by an accounting boundary before labelling
turns that boundary into an artificial hydrological barrier (F06). Ownership belongs to the accounting step, not here.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

STRUCTURE = {8: np.ones((3, 3), bool), 4: np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)}


def connected_to_seed(cand: np.ndarray, seed: np.ndarray, connectivity: int = 8) -> np.ndarray:
    """Boolean mask of the cells of `cand` that lie in a component (4- or 8-connected) containing a cell of `cand & seed`."""
    if connectivity not in STRUCTURE:
        raise ValueError("connectivity must be 4 or 8")
    cand = np.asarray(cand, bool); seed = np.asarray(seed, bool)
    if cand.shape != seed.shape:
        raise ValueError("cand and seed must have the same shape")
    lab, n = ndimage.label(cand, structure=STRUCTURE[connectivity])
    if n == 0:
        return np.zeros_like(cand)
    keep = np.zeros(n + 1, bool)
    keep[np.unique(lab[cand & seed])] = True
    keep[0] = False
    return keep[lab]


def largest_component(mask: np.ndarray, connectivity: int = 8) -> np.ndarray:
    """The largest connected component of a boolean mask (e.g. the main-stem water network as a seed variant)."""
    lab, n = ndimage.label(np.asarray(mask, bool), structure=STRUCTURE[connectivity])
    if n == 0:
        return np.zeros_like(mask, dtype=bool)
    sizes = np.bincount(lab.ravel()); sizes[0] = 0
    return lab == int(sizes.argmax())
