"""Review F06 (Appendix C of the review): connectivity must be evaluated on the whole terrain graph."""
from __future__ import annotations

import numpy as np
import pytest

from floodstate_eo.terrain.connectivity import connected_to_seed, largest_component


def test_split_domain_loses_connectivity_and_mosaic_keeps_it():
    cand = np.ones((1, 6), bool); seed = np.zeros_like(cand); seed[0, 0] = True
    own = np.array([[True, True, True, False, False, False]])
    whole = connected_to_seed(cand, seed)
    zonal = connected_to_seed(cand & own, seed) | connected_to_seed(cand & ~own, seed)
    assert int(whole.sum()) == 6 and int(zonal.sum()) == 3                  # the reviewer's numbers


def test_4_vs_8_connectivity_on_a_diagonal():
    cand = np.eye(4, dtype=bool); seed = np.zeros_like(cand); seed[0, 0] = True
    assert int(connected_to_seed(cand, seed, 8).sum()) == 4
    assert int(connected_to_seed(cand, seed, 4).sum()) == 1
    with pytest.raises(ValueError):
        connected_to_seed(cand, seed, 6)


def test_no_seed_inside_candidates_means_nothing_is_kept():
    cand = np.ones((3, 3), bool); seed = np.zeros_like(cand)
    assert not connected_to_seed(cand, seed).any()
    cand[1, 1] = False; seed[1, 1] = True                                   # a seed that is not a candidate does not seed
    assert not connected_to_seed(cand, seed).any()


def test_largest_component():
    m = np.zeros((5, 5), bool); m[0, :3] = True; m[4, 4] = True
    lc = largest_component(m)
    assert int(lc.sum()) == 3 and lc[0, 0] and not lc[4, 4]
    assert not largest_component(np.zeros((2, 2), bool)).any()


# ---- seed classes, erosion sensitivity and day-to-day links (QA of the seed network, 2026-09-30) ----------------------------
def _river_pond_blob():
    """Row 0: a river (seed_river) linked to a blob on rows 2-4 through a 1-cell bridge; an isolated pond on row 4 seeds
    its own component; a seedless component on row 6."""
    cand = np.zeros((7, 9), bool)
    cand[0, :] = True                                 # river
    cand[1, 4] = True                                 # 1-cell bridge
    cand[2:5, 2:7] = True                             # blob
    cand[4, 8] = True                                 # isolated pond (cand & seed)
    cand[6, 0:3] = True                               # no seed
    seed_all = np.zeros_like(cand); seed_all[0, :] = True; seed_all[4, 8] = True
    seed_river = np.zeros_like(cand); seed_river[0, :] = True
    return cand, seed_all, seed_river


def test_seed_classes_river_isolated_and_none():
    from floodstate_eo.terrain.connectivity import seed_classes
    cand, seed_all, seed_river = _river_pond_blob()
    lab, cls = seed_classes(cand, seed_all, seed_river)
    assert cls[lab[3, 4]] == 1 and cls[lab[0, 0]] == 1          # blob is river-connected through the bridge
    assert cls[lab[4, 8]] == 2                                   # pond: seeded, but not by the river
    assert cls[lab[6, 1]] == 0 and cls[0] == 0                   # no seed
    lab4, cls4 = seed_classes(cand, seed_all, seed_river, 4)
    assert cls4[lab4[3, 4]] == 1                                 # the bridge is a 4-neighbour of both


def test_erosion_disconnect_px():
    from floodstate_eo.terrain.connectivity import erosion_disconnect_px
    cand, _, seed_river = _river_pond_blob()
    blob = np.zeros_like(cand); blob[2:5, 2:7] = True
    assert erosion_disconnect_px(cand, blob, seed_river) == 1     # the 1-cell bridge does not survive one erosion
    pond = np.zeros_like(cand); pond[4, 8] = True
    assert erosion_disconnect_px(cand, pond, seed_river) == 0     # never linked
    wide = np.zeros((9, 9), bool); wide[0, :] = True; wide[1:4, 2:7] = True; wide[4:8, 2:7] = True
    river = np.zeros_like(wide); river[0, :] = True; target = np.zeros_like(wide); target[4:8, 2:7] = True
    assert erosion_disconnect_px(wide, target, river, max_px=3) == 3   # a 5-wide link: 5 -> 3 -> 1 -> gone at the third erosion
    assert erosion_disconnect_px(wide, target, river, max_px=2) == 3   # = max_px + 1: survives every erosion tried


def test_link_components_split_and_merge():
    from floodstate_eo.terrain.connectivity import link_components
    prev = np.array([[1, 1, 0, 2, 2]]); nxt = np.array([[3, 0, 0, 3, 4]])
    L = link_components(prev, nxt)
    assert L.tolist() == [[1, 3, 1], [2, 3, 1], [2, 4, 1]]        # 1 and 2 merge into 3; 2 also splits into 4
    assert link_components(prev, np.zeros_like(prev)).shape == (0, 3)
    assert link_components(prev, nxt, min_cells=2).shape == (0, 3)
