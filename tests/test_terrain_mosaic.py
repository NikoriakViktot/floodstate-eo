"""Review F01/F06: one union lattice, ownership only when pasting/accounting."""
from __future__ import annotations

import numpy as np
import pytest
from affine import Affine

from floodstate_eo.terrain.mosaic import UnionGrid


def _members():
    a = (Affine(20.0, 0.0, 1000.0, 0.0, -20.0, 2000.0), (10, 10))          # x 1000..1200, y 1800..2000
    b = (Affine(20.0, 0.0, 1100.0, 0.0, -20.0, 1900.0), (10, 10))          # x 1100..1300, y 1700..1900 (overlaps a)
    return {"A": a, "B": b}


def test_union_window_and_member_slices():
    g = UnionGrid.from_members(_members())
    assert g.shape == (15, 15) and g.cell == 20.0 and g.transform.c == 1000.0 and g.transform.f == 2000.0
    assert g.members["A"] == (0, 0, 10, 10) and g.members["B"] == (5, 5, 10, 10)
    assert np.allclose(g.xs()[:2], [1010.0, 1030.0]) and np.allclose(g.ys()[:2], [1990.0, 1970.0])


def test_compose_owner_last_and_extract_round_trip():
    g = UnionGrid.from_members(_members())
    a = np.full((10, 10), 1.0, "f4"); b = np.full((10, 10), 2.0, "f4")
    u = g.compose({"A": a, "B": b}, fill=np.nan, order=["A", "B"])
    assert u[7, 7] == 2.0 and u[0, 0] == 1.0 and np.isnan(u[14, 0])         # overlap owned by B (pasted last)
    assert np.array_equal(g.extract(u, "B"), b)
    assert np.array_equal(g.extract(u, "A")[:5, :5], a[:5, :5]) and (g.extract(u, "A")[5:, 5:] == 2.0).all()
    assert g.member_mask("A").sum() == 100


def test_misaligned_or_mixed_cells_are_refused():
    m = _members(); m["C"] = (Affine(20.0, 0.0, 1005.0, 0.0, -20.0, 2000.0), (2, 2))
    with pytest.raises(ValueError):
        UnionGrid.from_members(m)
    m = _members(); m["C"] = (Affine(10.0, 0.0, 1000.0, 0.0, -10.0, 2000.0), (2, 2))
    with pytest.raises(ValueError):
        UnionGrid.from_members(m)
    with pytest.raises(ValueError):
        UnionGrid.from_members(_members()).compose({"A": np.zeros((3, 3))}, fill=0)
