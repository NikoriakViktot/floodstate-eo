# New in floodstate-eo, 2026-09-29 (maintainer rule: every height in ONE vertical reference frame). STATUS: ACTIVE.
"""One vertical reference frame for every height that enters a comparison.

Water-surface elevations, terrain, bed and altimetric ground heights are compared to the centimetre; a datum mismatch of a
few decimetres is invisible in the code and fatal in the result. Every input therefore DECLARES its vertical datum (a raster
tag, a table column name, a manifest entry) and `assert_same_vertical_frame` refuses to proceed when one is missing or
when they differ. Silence is not consent.
"""
from __future__ import annotations

import re


class VerticalFrameError(ValueError):
    pass


def _norm(s) -> str:
    return re.sub(r"[\s_\-]+", "", str(s)).upper()


def assert_same_vertical_frame(declared: dict[str, str | None]) -> str:
    """`declared`: input name -> the vertical datum it declares (e.g. 'EVRF2019'). Returns the common datum.
    Raises VerticalFrameError if any input declares nothing or if the declarations differ."""
    if not declared:
        raise VerticalFrameError("no inputs declared")
    missing = [k for k, v in declared.items() if v is None or not str(v).strip()]
    if missing:
        raise VerticalFrameError(f"no vertical datum declared for: {missing}")
    frames = {k: _norm(v) for k, v in declared.items()}
    if len(set(frames.values())) != 1:
        raise VerticalFrameError("vertical datums differ: " + ", ".join(f"{k}={v}" for k, v in declared.items()))
    return str(next(iter(declared.values()))).strip()


def read_esri_ascii_grid(path):
    """(values with NaN for nodata, header dict) of an ESRI ASCII grid (row 0 = north)."""
    head, vals = {}, []
    with open(path) as fh:
        for _ in range(6):
            k, v = fh.readline().split(); head[k.lower()] = float(v)
        for line in fh:
            vals.extend(float(x) for x in line.split())
    import numpy as np
    z = np.array(vals, float).reshape(int(head["nrows"]), int(head["ncols"]))
    if "nodata_value" in head:
        z[z == head["nodata_value"]] = np.nan
    return z, head


def sample_esri_ascii_grid(z, head, lon, lat):
    """Bilinear sample of an ESRI ASCII grid at (lon, lat) -- e.g. the EPSG:9902 BS-77 -> EVRF2019 height-difference grid, the
    step H_EVRF2019 = H_BS77 + delta(lon, lat) used for every gauge of the series (Paper 1)."""
    import numpy as np
    cs, nc, nr = head["cellsize"], int(head["ncols"]), int(head["nrows"])
    x0 = head["xllcorner"] + cs / 2.0; ytop = head["yllcorner"] + cs * (nr - 0.5)
    fc = (np.asarray(lon, float) - x0) / cs; fr = (ytop - np.asarray(lat, float)) / cs
    c0 = np.clip(np.floor(fc).astype(int), 0, nc - 2); r0 = np.clip(np.floor(fr).astype(int), 0, nr - 2)
    dc, dr = fc - c0, fr - r0
    return (z[r0, c0] * (1 - dc) * (1 - dr) + z[r0, c0 + 1] * dc * (1 - dr) + z[r0 + 1, c0] * (1 - dc) * dr + z[r0 + 1, c0 + 1] * dc * dr)
