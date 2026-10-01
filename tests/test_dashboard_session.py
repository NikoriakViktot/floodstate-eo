"""The dashboard session (maintainer 2026-10-01: "there is no session cache, everything disappears on a re-render -- make a session id"):
a page carries ?sid=... in the URL, its widget choices are saved under that id and come back on a reload, even after the in-memory
store is gone; a stored value that no longer matches the options is dropped instead of breaking the widget."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "apps" / "dashboard"
SID = "0123456789ab"


@pytest.fixture
def lib(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(APP))
    import lib as L
    monkeypatch.setattr(L, "SESS", tmp_path); L._store.clear()
    return L


def _run(script, sid=None):
    st_testing = pytest.importorskip("streamlit.testing.v1")
    at = st_testing.AppTest.from_file(str(APP / script), default_timeout=120)
    if sid:
        at.query_params["sid"] = sid
    return at.run()


def test_choice_survives_a_reload_through_the_session_file(lib, tmp_path):
    at = _run("pages/3_Checks.py", SID)
    assert not at.exception, [e.value for e in at.exception]
    assert at.query_params["sid"] in (SID, [SID])
    at.selectbox(key="chk_region").set_value("INHULETS_VALLEY_rect").run()
    saved = json.loads((tmp_path / f"{SID}.json").read_text())
    assert saved["chk_region"] == "INHULETS_VALLEY_rect"
    lib._store.clear()                                                      # a server restart: only the file remains
    at2 = _run("pages/3_Checks.py", SID)
    assert not at2.exception and at2.selectbox(key="chk_region").value == "INHULETS_VALLEY_rect"


def test_session_id_is_minted_when_missing(lib):
    at = _run("pages/3_Checks.py")
    assert not at.exception
    sid = at.query_params["sid"]; sid = sid[-1] if isinstance(sid, list) else sid; assert len(sid) == 12 and int(sid, 16) >= 0


def test_stale_stored_value_is_dropped(lib, tmp_path):
    (tmp_path / f"{SID}.json").write_text(json.dumps({"chk_region": "NO_SUCH_REGION", "chk_variant": "connected_ceiling"}))
    at = _run("pages/3_Checks.py", SID)
    assert not at.exception, [e.value for e in at.exception]
    assert at.selectbox(key="chk_region").value == "P42_FLOODPLAIN_DOMAIN" and at.selectbox(key="chk_variant").value == "connected_ceiling"
