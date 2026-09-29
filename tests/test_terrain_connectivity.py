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
