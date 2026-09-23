"""p73 must be built without flood evidence (the other half of test_m6_label_independence.py).

These are the two halves of one contract: p73 may become a U-Net INPUT only because it is not part of the TARGET, and
that is only true while p77 cannot read it (or BASE_CLASS, or WorldCover) and p73 cannot read the flood chain.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

M6 = Path(__file__).resolve().parents[1] / "case_studies" / "kakhovka_2023" / "workflows" / "m6"


def _load(name):
    s = importlib.util.spec_from_file_location(name, M6 / f"{name}.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_p73_guard_refuses_the_flood_chain_and_non_pre_bands():
    P = _load("p73_rf20_surface")
    for bad in ("cand_score.tif", "flood_central.tif", "p69a_base_class.tif", "s1_change.tif", "labels.tif",
                "m6_labels_v002.tif", "hand_m.tif", "u0_b2_score.tif"):
        with pytest.raises(SystemExit):
            P._guard(Path("/x") / bad)
    for band in ("NDVI_event_med", "MNDWI_trace_max", "n_obs_event"):
        with pytest.raises(SystemExit):
            P._guard(Path("/x/composite_preall.tif"), [band])
    assert P._guard(Path("/x/composite_preall.tif"), ["NDVI_pre_med", "MNDWI_pre_max"])
