"""Dashboard bundle: every layer in the manifest exists with its sha256, bounds are sane, the bundle stays under 100 MB,
requirements are pinned, and the app scripts execute headlessly (streamlit AppTest) without exceptions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "apps" / "dashboard"
DATA = APP / "data"


def test_manifest_layers_exist_and_match():
    man = json.loads((DATA / "manifest.json").read_text())
    assert man["n_layers"] == len(man["layers"]) >= 60
    total = 0
    for layer in man["layers"]:
        p = DATA / layer["file"]; assert p.exists(), layer["id"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == layer["sha256"], layer["id"]
        total += p.stat().st_size
        if layer["bounds"] is not None:
            (s, w), (n, e) = layer["bounds"]; assert s < n and w < e and 46 < s < 48 and 31 < w < 34
    assert total <= 100 * 1024 * 1024


def test_requirements_pinned():
    lines = [ln.strip() for ln in (APP / "requirements.txt").read_text().splitlines() if ln.strip()]
    assert lines and all("==" in ln for ln in lines)
    assert any(ln.startswith("streamlit==") for ln in lines) and any(ln.startswith("streamlit-folium==") for ln in lines)


@pytest.mark.parametrize("script", ["streamlit_app.py", "pages/1_Reconstruction.py", "pages/3_Checks.py", "pages/4_Surface_context.py", "pages/5_UNet_experiments.py", "pages/6_Data_and_provenance.py"])
def test_pages_run_headless(script, monkeypatch):
    st_testing = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.syspath_prepend(str(APP))
    at = st_testing.AppTest.from_file(str(APP / script), default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
