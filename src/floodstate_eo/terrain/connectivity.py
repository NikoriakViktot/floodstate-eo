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

def seed_classes(cand: np.ndarray, seed_all: np.ndarray, seed_river: np.ndarray, connectivity: int = 8) -> tuple[np.ndarray, np.ndarray]:
    """Label the components of `cand` and class each one by the seed cells it contains: 0 = no seed cell, 1 = it touches
    `seed_river` (the event-source network), 2 = it touches other seed cells only (an isolated water body: a pond, a canal).
    Returns (labels, cls) with cls[k] the class of label k and cls[0] = 0. `seed_river` is expected to be a subset of
    `seed_all`; where it is not, class 1 still wins."""
    if connectivity not in STRUCTURE:
        raise ValueError("connectivity must be 4 or 8")
    cand = np.asarray(cand, bool)
    lab, n = ndimage.label(cand, structure=STRUCTURE[connectivity])
    cls = np.zeros(n + 1, "u1")
    if n:
        cls[np.unique(lab[cand & np.asarray(seed_all, bool)])] = 2
        cls[np.unique(lab[cand & np.asarray(seed_river, bool)])] = 1
        cls[0] = 0
    return lab, cls


def erosion_disconnect_px(mask: np.ndarray, target: np.ndarray, seed_river: np.ndarray, max_px: int = 3, connectivity: int = 8) -> int:
    """A morphological sensitivity test, NOT a geometric width: the smallest k in 1..max_px such that after k 4-neighbour
    erosions of `mask` no remaining cell of `target` lies in a component of the eroded mask that still contains a cell of
    `seed_river`. The source network itself (`mask & seed_river`) is never eroded: only the link and the target are thinned.
    Returns 0 when `target` is not linked to `seed_river` in `mask` itself, and `max_px + 1` when the link survives every
    erosion. Cells of `target` eroded away count as no longer linked."""
    mask = np.asarray(mask, bool); target = np.asarray(target, bool); seed_river = np.asarray(seed_river, bool)
    source = mask & seed_river

    def linked(m):
        lab, cls = seed_classes(m, seed_river, seed_river, connectivity)
        return bool((cls[lab[target & m]] == 1).any())

    if not linked(mask):
        return 0
    er = mask
    for k in range(1, max_px + 1):
        er = ndimage.binary_erosion(er, structure=STRUCTURE[4]) | source
        if not linked(er):
            return k
    return max_px + 1


def link_components(labels_prev: np.ndarray, labels_next: np.ndarray, min_cells: int = 1) -> np.ndarray:
    """Overlap links between two labelled images of the same shape (0 = background): an integer array of rows
    (id_prev, id_next, cells) for every pair of labels that share at least `min_cells` cells. The building block of a
    day-to-day lineage graph (ancestry by backward traversal), which is how temporal attributes such as 'first day connected'
    must be derived -- never from the union of all days, which merges areas that were never simultaneously connected."""
    a = np.asarray(labels_prev); b = np.asarray(labels_next)
    if a.shape != b.shape:
        raise ValueError("labels_prev and labels_next must have the same shape")
    m = (a > 0) & (b > 0)
    if not m.any():
        return np.zeros((0, 3), "i8")
    base = int(b.max()) + 1
    pairs = a[m].astype("i8") * base + b[m].astype("i8")
    u, c = np.unique(pairs, return_counts=True)
    keep = c >= min_cells
    return np.c_[u[keep] // base, u[keep] % base, c[keep]].astype("i8")
