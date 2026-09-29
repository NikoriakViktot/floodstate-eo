# New in floodstate-eo, 2026-09-29 (review F01/F06). STATUS: ACTIVE.
"""One union lattice for several member grids that share a cell size and lattice phase.

The terrain reconstruction of a case study may be produced per computational zone; the connectivity and the stochastic
terrain field must nevertheless be evaluated ONCE on the union of the zones (one possible world, one terrain graph), and the
zones only own cells for accounting and for writing their own rasters. `UnionGrid` holds the union window and each member's
slice into it; `compose` pastes member arrays into the union (later members overwrite earlier ones: put the owner last) and
`extract` slices a union array back to a member.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from affine import Affine


@dataclass
class UnionGrid:
    transform: Affine
    shape: tuple[int, int]
    cell: float
    members: dict[str, tuple[int, int, int, int]] = field(default_factory=dict)   # name -> (row0, col0, ny, nx)

    @classmethod
    def from_members(cls, members: dict[str, tuple[Affine, tuple[int, int]]], tol: float = 1e-6) -> UnionGrid:
        """`members`: name -> (transform, (ny, nx)); north-up grids with one cell size on one lattice phase."""
        if not members:
            raise ValueError("no members")
        cells = {round(abs(t.a), 9) for t, _ in members.values()} | {round(abs(t.e), 9) for t, _ in members.values()}
        if len(cells) != 1:
            raise ValueError(f"members have different cell sizes: {cells}")
        cell = cells.pop()
        for name, (t, _) in members.items():
            if t.b != 0 or t.d != 0 or t.e >= 0:
                raise ValueError(f"{name}: only north-up, non-rotated grids are supported")
        x0 = min(t.c for t, _ in members.values()); y1 = max(t.f for t, _ in members.values())
        x1 = max(t.c + s[1] * cell for t, s in members.values()); y0 = min(t.f - s[0] * cell for t, s in members.values())
        for name, (t, _) in members.items():
            for off in ((t.c - x0) / cell, (y1 - t.f) / cell):
                if abs(off - round(off)) > tol:
                    raise ValueError(f"{name}: not on the lattice of the union (offset {off} cells)")
        ny, nx = round((y1 - y0) / cell), round((x1 - x0) / cell)
        g = cls(Affine(cell, 0.0, x0, 0.0, -cell, y1), (ny, nx), cell)
        for name, (t, s) in members.items():
            g.members[name] = (round((y1 - t.f) / cell), round((t.c - x0) / cell), int(s[0]), int(s[1]))
        return g

    def window(self, name: str) -> tuple[slice, slice]:
        r0, c0, ny, nx = self.members[name]
        return slice(r0, r0 + ny), slice(c0, c0 + nx)

    def extract(self, arr: np.ndarray, name: str) -> np.ndarray:
        rs, cs = self.window(name)
        return arr[rs, cs]

    def compose(self, arrays: dict[str, np.ndarray], fill, order: list[str] | None = None, dtype=None) -> np.ndarray:
        """Paste member arrays into a union array initialised with `fill`; members in `order` (default: insertion order)
        overwrite earlier ones, so the owner of an overlap goes last."""
        names = order or list(arrays)
        first = np.asarray(arrays[names[0]])
        out = np.full(self.shape, fill, dtype=dtype or first.dtype)
        for name in names:
            a = np.asarray(arrays[name]); r0, c0, ny, nx = self.members[name]
            if a.shape != (ny, nx):
                raise ValueError(f"{name}: array shape {a.shape} != member shape {(ny, nx)}")
            out[r0:r0 + ny, c0:c0 + nx] = a
        return out

    def member_mask(self, name: str) -> np.ndarray:
        m = np.zeros(self.shape, bool); rs, cs = self.window(name); m[rs, cs] = True
        return m

    def xs(self) -> np.ndarray:
        return self.transform.c + self.cell * (np.arange(self.shape[1]) + 0.5)

    def ys(self) -> np.ndarray:
        return self.transform.f - self.cell * (np.arange(self.shape[0]) + 0.5)
