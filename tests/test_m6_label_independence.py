"""m6_labels_v002 must be constructed without land-cover semantics, and p73 without flood evidence.

These are the two halves of one contract: p73 may become a U-Net INPUT only because it is not part of the TARGET, and
that is only true while p77 cannot read it (or BASE_CLASS, or WorldCover) and p73 cannot read the flood chain.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

M6 = Path(__file__).resolve().parents[1] / "case_studies" / "kakhovka_2023" / "workflows" / "m6"


def _load(name):
    s = importlib.util.spec_from_file_location(name, M6 / f"{name}.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_p77_guard_refuses_land_cover_and_flood_model_layers():
    P = _load("p77_m6_labels_v002")
    for bad in ("p69a_base_class.tif", "p69b_semantic_state.tif", "p73_surface_20m.tif", "wc_2021_20m.tif",
                "dw_2023_20m.tif", "ZONE_4_hand_m.tif", "u0_b2_score.tif", "cand_score.tif"):
        with pytest.raises(SystemExit):
            P._guard(Path("/x") / bad)
    for ok in ("labels.tif", "flood_central.tif", "flood_possible.tif", "per_scene_water.npz"):
        assert P._guard(Path("/x") / ok)


def test_p77_source_names_no_file_outside_the_allowlist():
    P = _load("p77_m6_labels_v002")
    src = (M6 / "p77_m6_labels_v002.py").read_text()
    lits = [n.value for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    files = [s for s in lits if s.endswith((".tif", ".npz")) and "\n" not in s and " " not in s]
    assert files, "expected the builder to name its inputs"
    for f in files:
        if f.startswith(("{", ".")) or "VERSION" in f:          # f-string fragments, not file names
            continue
        assert P.ALLOWED.search(f) or f.endswith("m6_labels_v002.tif"), f"p77 names a non-allowed file: {f}"
