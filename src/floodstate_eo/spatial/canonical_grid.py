# Provenance: SWOT-DNIPRO src/swot_dnipro/canonical_grid.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CORE_LIBRARY, copied verbatim per 19_MIGRATION_MANIFEST.csv row 25 (migration_phase=5).
#
# KNOWN EVENT-AGNOSTIC GATE EXCEPTION (see provenance/KNOWN_GATE_EXCEPTIONS.md): this module hard-codes the
# Kakhovka B1/B2/B3 frame bboxes and the string "Kherson" in FRAME_LABEL. It is depended on by CG.frame_grid()
# in every one of the 20 migrated scripts, so splitting the generic snap/grid mechanics from the Kakhovka
# frame constants is Phase 6 work ("replace hard-coding with config"; study_area.yaml already stages the
# frame data), not this Phase 5 copy step. Copied verbatim rather than half-refactored.
"""The canonical 10 m processing lattice for the flood recompute. Single source of truth for B1/B2/B3.

WHY 10 m AND WHY A LATTICE RATHER THAN ARITHMETIC. The task is pixel-level classification of urban flooding in Kherson,
Hola Prystan and Oleshky, of narrow flood boundaries, and of the sand/bare-soil confusion that produces Sentinel-1
false water. 20 m is too coarse for that, so 20 m is no longer canonical.

The grid is NOT derived by `floor(bbox / 10)`. It is taken from the pixel lattice of the real native Sentinel-2 10 m
bands (B02/B03/B04/B08) in EPSG:32636. Every MGRS tile of zone 36T in this archive has its 10 m origin on a multiple
of 20 m -- 399960 / 300000 / 499980 easting, 5200020 / 5300040 northing -- so one lattice with cell edges on multiples
of 10 m holds every tile exactly, with no resampling between tiles.

THE DEFECT THIS REPLACES. The previous 20 m frame grids were snapped with `floor(bbox/20)*20`, giving x0 = 0 (mod 20),
while `SD.build_grid` zone grids sit at x0 = 10 (mod 20). That is a HALF-CELL offset, and it was measurable: a
same-acquisition comparison of the two preprocessing paths (p53d/p53e) showed a median signed difference of ~1e-4 --
so the BOA correction was fine -- but median |delta| 0.03 and 79 % of pixels above 0.01 IN THE FLAT INTERIOR, not only
on edges. Decomposing the lineage showed the order of operations contributed exactly zero (index-then-warp equals
warp-then-index under nearest neighbour) and the entire difference was the half-cell resampling hop.

At 10 m the problem disappears by construction: a 20 m zone cell spans exactly two 10 m lattice cells, so every legacy
product maps onto the lattice as an integer relation.

NATIVE RESOLUTION IS NOT INVENTED BY UPSAMPLING. B02/B03/B04/B08 are natively 10 m. B11/B12/B8A and SCL are natively
20 m; they are resampled ONCE onto the lattice before any index is computed, never afterwards, and categorical layers
(SCL, class masks) move only by nearest neighbour. An index that contains B11 carries 20 m native SWIR information at
a 10 m target resolution, and the manifest must say so rather than imply new detail.
"""
from __future__ import annotations

import numpy as np
from rasterio.transform import from_origin

from .. import _kakhovka_legacy_config as CFG

CELL = 10.0
#: Native Sentinel-2 10 m tile origins observed in this archive (EPSG:32636), read from MTD_TL.xml of every tile the
#: three frames actually consume -- all ten, not the three the lattice was first derived from. Every one is a multiple
#: of 20 m, so a 20 m zone cell is exactly two lattice cells per axis and the half-cell hop cannot return.
NATIVE_ORIGINS = ((300000.0, 5200020.0), (300000.0, 5300040.0),      # 36TUS 36TUT
                  (399960.0, 5200020.0), (399960.0, 5300040.0),      # 36TVS 36TVT
                  (499980.0, 5200020.0), (499980.0, 5300040.0),      # 36TWS 36TWT
                  (600000.0, 5200020.0), (600000.0, 5300040.0),      # 36TXS 36TXT
                  (499980.0, 5400000.0), (600000.0, 5400000.0))      # 36UWU 36UXU
#: Resampling contract, recorded in every product's provenance.
RESAMPLING = dict(continuous="bilinear", categorical="nearest",
                  note="20 m bands are brought to the lattice ONCE, before index computation")

#: B1 PROVENANCE. The frame was reduced on the user's instruction ("завелика") after the reduction was MEASURED, not
#: guessed: three candidates were scored by how much observed Sentinel-1 new water each retained, and variant B was
#: chosen. The old full bbox is superseded, not lost, and must not be restored by confusing the legacy frame with the
#: canonical one.
B1_FULL_LEGACY_KM2 = 10337.6      # 455680, 5132240, 569280, 5223240 -- SUPERSEDED 2026-09-21
B1_CANONICAL_KM2 = 6091.7         # 455680, 5138000, 538000, 5212000 -- in force
B1_CHANGE_REASON = ("canonical B1 preserves 99.96 % of the observed new Sentinel-1 water at the June peak while "
                    "excluding ~4 246 km2 of upstream reservoir area that is handled separately by B4 (drawdown). "
                    "The east edge sits 9.8 km past the dam instead of 41 km inside the pool. Flood mapping below the "
                    "dam and reservoir drawdown are different questions and are not mixed in one frame.")

#: The three processing frames, fixed by the user 2026-09-21. bbox is the request; the raster is snapped outward to the
#: lattice, which can move an edge by at most one 10 m cell.
FRAME_BBOX = {
    "B1": (455680.0, 5138000.0, 538000.0, 5212000.0),
    "B2": (438000.0, 5135002.0, 475685.0, 5211567.0),
    "B3": (374260.0, 5107360.0, 465000.0, 5267000.0),
}
FRAME_LABEL = {"B1": "B1 · dam -> Kherson", "B2": "B2 · Kherson -> delta", "B3": "B3 · delta with the liman"}


def snap_out(v: float, up: bool) -> float:
    """Move v to the lattice: outward, so the frame is never clipped."""
    return (np.ceil(v / CELL) if up else np.floor(v / CELL)) * CELL


def frame_grid(fid: str) -> dict:
    x0, y0, x1, y1 = FRAME_BBOX[fid]
    X0 = snap_out(x0, False); Y0 = snap_out(y0, False)
    X1 = snap_out(x1, True); Y1 = snap_out(y1, True)
    nx = int(round((X1 - X0) / CELL)); ny = int(round((Y1 - Y0) / CELL))
    return dict(frame=fid, x0=X0, y0=Y0, x1=X1, y1=Y1, nx=nx, ny=ny, cell_m=CELL,
                transform=from_origin(X0, Y1, CELL, CELL), crs=str(CFG.CRS_METRIC))


#: ONE canonical 20 m lattice, phased to the native Sentinel-2 20 m grid -- NOT to any frame origin.
#: Every native tile origin is a multiple of 20 m (verified from MTD_TL.xml for all ten tiles the frames consume),
#: so a 20 m grid on absolute multiples of 20 m receives native 20 m pixels 1:1 with no reprojection. Anchoring a
#: 20 m grid to a frame origin instead would force a half-pixel resample for B2, whose y1 = 5 211 570 is 10 m off
#: the native phase -- precisely the defect that put a 10 m shift into every SWIR index and cost a full rebuild.
#: B1, B2 and B3 are CLIPS of this one grid, never three independent 20 m grids: that is what makes the optical
#: surface class identical on shared ground by construction rather than by later checking.
CELL20 = 20.0


def snap20(v: float, up: bool) -> float:
    return (np.ceil(v / CELL20) if up else np.floor(v / CELL20)) * CELL20


def grid20_for(fid: str) -> dict:
    """The clip of the global 20 m lattice covering this frame, plus how its cells map onto the 10 m grid.

    `phase_rows`/`phase_cols` are 0 when the frame's 10 m origin coincides with the 20 m lattice (B1, B3) and 1
    when it sits half a cell out (B2 in y). An interior 20 m cell always covers exactly 2x2 ten-metre cells; only
    the first row or column can be partial, and that is reported, never padded away.
    """
    F = frame_grid(fid)
    X0 = snap20(F["x0"], False); Y1 = snap20(F["y1"], True)
    X1 = snap20(F["x1"], True); Y0 = snap20(F["y0"], False)
    nx = int(round((X1 - X0) / CELL20)); ny = int(round((Y1 - Y0) / CELL20))
    return dict(frame=fid, x0=X0, y0=Y0, x1=X1, y1=Y1, nx=nx, ny=ny, cell_m=CELL20,
                transform=from_origin(X0, Y1, CELL20, CELL20), crs=str(CFG.CRS_METRIC),
                phase_cols=int(round((F["x0"] - X0) / CELL)) % 2,
                phase_rows=int(round((Y1 - F["y1"]) / CELL)) % 2,
                aligned_to_native_20m=all(abs((X0 - ox) / CELL20 - round((X0 - ox) / CELL20)) < 1e-9
                                          and abs((oy - Y1) / CELL20 - round((oy - Y1) / CELL20)) < 1e-9
                                          for ox, oy in NATIVE_ORIGINS))


def verify_alignment() -> list[dict]:
    """Every frame origin must be an integer number of cells from every native tile origin."""
    out = []
    for fid in FRAME_BBOX:
        G = frame_grid(fid)
        ok = True
        for (ox, oy) in NATIVE_ORIGINS:
            dx = (G["x0"] - ox) / CELL; dy = (oy - G["y1"]) / CELL
            if abs(dx - round(dx)) > 1e-9 or abs(dy - round(dy)) > 1e-9:
                ok = False
        out.append(dict(frame=fid, x0=G["x0"], y1=G["y1"], nx=G["nx"], ny=G["ny"],
                        megapixels=round(G["nx"] * G["ny"] / 1e6, 1),
                        area_km2=round(G["nx"] * G["ny"] * CELL * CELL / 1e6, 1),
                        x0_mod10=G["x0"] % 10, y1_mod10=G["y1"] % 10,
                        aligned_to_native_lattice=ok))
    return out
