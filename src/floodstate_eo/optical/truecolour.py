# New in floodstate-eo, 2026-09-30. Event-agnostic: a Sentinel-2 L2A true-colour basemap on any target grid.
"""Sentinel-2 L2A true colour (B04 / B03 / B02) mosaicked on a target grid, cloud-masked with the scene classification.

Scenes are taken in the order given (the caller's priority: the cleanest date first); a later scene fills only the cells
that no earlier scene observed cloud-free. Reflectance carries the BOA offset of each scene's own metadata
(`sentinel_preprocess.read_scene_bands`), so scenes of different processing baselines mix correctly. The stretch is fixed
and recorded by the caller (reproducible figures), never a per-image percentile.

    rgb, filled = truecolour_mosaic(zip_paths, grid, cell=20.0, stretch=(0.0, 0.30), gamma=1.0)

`rgb` is uint8 (3, ny, nx) with 0 where nothing was observed cloud-free; `filled` is uint8 (ny, nx): 0 = no data,
k = the k-th scene of the list supplied the cell. A basemap for figures and dashboards: not an input of any product.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np

#: SCL classes that never contribute to a basemap: no data, saturated / defective, cloud shadow, cloud (medium, high),
#: thin cirrus, snow / ice.
CLOUD_SCL = (0, 1, 3, 8, 9, 10, 11)
RGB_BANDS = ("B04", "B03", "B02")


def to_uint8(rgb: np.ndarray, valid: np.ndarray, stretch=(0.0, 0.30), gamma: float = 1.0) -> np.ndarray:
    """Linear stretch of reflectance `stretch[0]..stretch[1]` to 0..255 with an optional gamma (< 1 brightens); 0 outside `valid`."""
    lo, hi = float(stretch[0]), float(stretch[1])
    if hi <= lo:
        raise ValueError("stretch must be (lo, hi) with hi > lo")
    x = np.clip((rgb.astype("f4") - lo) / (hi - lo), 0.0, 1.0)
    if gamma != 1.0:
        x = x ** float(gamma)
    out = np.rint(x * 255.0).astype("u1")
    out[:, ~valid] = 0
    return out


def truecolour_mosaic(zip_paths: list[Path], grid: dict, cell: float = 20.0, stretch=(0.0, 0.30), gamma: float = 1.0,
                      cloud_scl=CLOUD_SCL, reader: Callable | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Cloud-masked true-colour mosaic on `grid` (dict with `transform`, `ny`, `nx`, `crs`), scenes in priority order.

    `reader(zip_path, cell)` must return a dict with reflectance arrays for B04/B03/B02, an integer `SCL`, and the source
    `transform` and `crs` (the contract of `sentinel_preprocess.read_scene_bands`, the default)."""
    from rasterio.enums import Resampling
    from rasterio.warp import reproject

    if reader is None:
        from . import sentinel_preprocess as SP
        reader = SP.read_scene_bands
    ny, nx = int(grid["ny"]), int(grid["nx"])
    rgb = np.zeros((3, ny, nx), "f4"); filled = np.zeros((ny, nx), "u1")
    for k, zp in enumerate(zip_paths, 1):
        r = reader(zp, cell)
        scl = np.zeros((ny, nx), "i2")
        reproject(source=np.asarray(r["SCL"], "i2"), destination=scl, src_transform=r["transform"], src_crs=r["crs"],
                  dst_transform=grid["transform"], dst_crs=grid["crs"], resampling=Resampling.nearest, src_nodata=0, dst_nodata=0)
        ok = (scl > 0) & ~np.isin(scl, cloud_scl) & (filled == 0)
        if not ok.any():
            continue
        for i, b in enumerate(RGB_BANDS):
            dst = np.full((ny, nx), np.nan, "f4")
            reproject(source=np.asarray(r[b], "f4"), destination=dst, src_transform=r["transform"], src_crs=r["crs"],
                      dst_transform=grid["transform"], dst_crs=grid["crs"], resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
            ok &= np.isfinite(dst)
            rgb[i][ok] = dst[ok]
        filled[ok] = k
    return to_uint8(rgb, filled > 0, stretch, gamma), filled
