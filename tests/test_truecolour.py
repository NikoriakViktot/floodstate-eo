"""Invariants of floodstate_eo.optical.truecolour (cloud-masked true-colour mosaic on a target grid)."""
from __future__ import annotations

import numpy as np
import pytest
from rasterio.transform import from_origin

from floodstate_eo.optical import truecolour as TC

GRID = dict(transform=from_origin(1000.0, 2000.0, 20.0, 20.0), ny=4, nx=5, crs="EPSG:32636")


def _scene(value, scl):
    """A scene on the target lattice itself: three constant reflectance bands and the given SCL."""
    scl = np.asarray(scl, "i2")
    return {"B04": np.full(scl.shape, value, "f4"), "B03": np.full(scl.shape, value * 0.8, "f4"), "B02": np.full(scl.shape, value * 0.6, "f4"),
            "SCL": scl, "transform": GRID["transform"], "crs": GRID["crs"]}


def test_first_clear_scene_wins_and_clouds_are_filled_by_later_scenes():
    scl1 = np.full((4, 5), 4, "i2"); scl1[0, :] = 9                     # row 0: cloud (high probability) in scene 1
    scl1[3, 4] = 0                                                       # one no-data cell in scene 1
    scl2 = np.full((4, 5), 5, "i2"); scl2[3, 4] = 3                      # scene 2 has a cloud shadow on that cell
    scenes = {"a": _scene(0.15, scl1), "b": _scene(0.30, scl2)}
    rgb, filled = TC.truecolour_mosaic(["a", "b"], GRID, reader=lambda zp, cell: scenes[zp])
    assert rgb.shape == (3, 4, 5) and rgb.dtype == np.uint8
    assert (filled[1:3, :] == 1).all() and (filled[0, :] == 2).all()    # rows 1-2 from scene 1, the cloudy row from scene 2
    assert filled[3, 4] == 0 and (rgb[:, 3, 4] == 0).all()               # observed by no clear scene -> 0
    assert rgb[0, 1, 0] == round(0.15 / 0.30 * 255) and rgb[0, 0, 0] == 255


def test_stretch_and_gamma():
    valid = np.ones((1, 2), bool); x = np.array([[[0.0, 0.15]]], "f4")
    assert TC.to_uint8(x, valid, (0.0, 0.30)).tolist() == [[[0, 128]]]
    assert TC.to_uint8(x, valid, (0.0, 0.30), gamma=0.5)[0, 0, 1] == round(np.sqrt(0.5) * 255)
    assert TC.to_uint8(x, np.zeros((1, 2), bool), (0.0, 0.30)).sum() == 0
    with pytest.raises(ValueError):
        TC.to_uint8(x, valid, (0.3, 0.3))
