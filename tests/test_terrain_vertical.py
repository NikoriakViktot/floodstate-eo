"""Maintainer rule 2026-09-29: every height in ONE vertical frame, declared, not assumed."""
from __future__ import annotations

import pytest

from floodstate_eo.terrain.vertical import (
    VerticalFrameError,
    assert_same_vertical_frame,
)


def test_same_frame_passes_with_normalised_spelling():
    assert assert_same_vertical_frame({"terrain": "EVRF2019", "swot": "evrf 2019", "gauge": "EVRF-2019"}) == "EVRF2019"


def test_missing_or_different_frames_are_refused():
    with pytest.raises(VerticalFrameError):
        assert_same_vertical_frame({"terrain": "EVRF2019", "gauge": None})
    with pytest.raises(VerticalFrameError):
        assert_same_vertical_frame({"terrain": "EVRF2019", "swot": "EGM2008"})
    with pytest.raises(VerticalFrameError):
        assert_same_vertical_frame({})


def test_esri_ascii_grid_bilinear_sampling(tmp_path):
    from floodstate_eo.terrain.vertical import (
        read_esri_ascii_grid,
        sample_esri_ascii_grid,
    )
    f = tmp_path / "g.asc"
    f.write_text("ncols 3\nnrows 2\nxllcorner 30.0\nyllcorner 46.0\ncellsize 1.0\nNODATA_value -9999\n0.1 0.2 0.3\n0.4 0.5 0.6\n")
    z, h = read_esri_ascii_grid(f)
    assert z.shape == (2, 3) and z[0, 0] == 0.1                               # row 0 = north
    assert abs(float(sample_esri_ascii_grid(z, h, 30.5, 47.5)) - 0.1) < 1e-12   # centre of the NW cell
    assert abs(float(sample_esri_ascii_grid(z, h, 31.0, 47.0)) - 0.3) < 1e-12   # midway between 0.1 0.2 0.4 0.5
