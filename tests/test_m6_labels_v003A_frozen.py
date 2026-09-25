"""m6_labels_v003_A is FROZEN (maintainer decision 2026-09-25): the freeze record, the build manifest and the rasters on
disk must agree. Rasters live in bulk storage, so that part is skipped when the data root is absent."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

TABLES = Path(__file__).resolve().parents[1] / "case_studies" / "kakhovka_2023" / "tables"
FROZEN = TABLES / "m6_labels_v003_A_FROZEN.json"
BUILD = TABLES / "p77d_v003_A_manifest.json"


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(16 << 20), b""):
            h.update(c)
    return h.hexdigest()


def test_freeze_record_exists_and_matches_build_manifest():
    rec = json.loads(FROZEN.read_text()); man = json.loads(BUILD.read_text())
    assert rec["status"] == "M6_LABELS_V003_A_FROZEN"
    assert len(rec["freeze_commit"]) == 40
    assert rec["sha256"] == man["output_sha256"]
    assert rec["sources_sha256"] == man["sources_sha256"]
    assert "PASS" in rec["reproducibility_gate"]


def test_frozen_rasters_unchanged_on_disk():
    rec = json.loads(FROZEN.read_text())
    paths = {f: Path(p) for f, p in rec["rasters"].items()}
    if not all(p.exists() for p in paths.values()):
        pytest.skip("bulk data root not mounted")
    for f, p in paths.items():
        assert _sha(p) == rec["sha256"][f], f"{f}: frozen raster changed on disk"
