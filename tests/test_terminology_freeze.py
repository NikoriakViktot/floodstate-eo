"""Gate 1 of the 2026-09-26 consolidation review: the publication bundle, dashboard and notebook builder use the frozen
terminology of publication/TERMINOLOGY.md. Runs without bulk data."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CS = ROOT / "case_studies" / "kakhovka_2023"
FORBIDDEN = ["physical reconstruction", "false SAR water", "false radar water", "peak breach discharge", "breach discharge was", "breach discharge of", "peak breach outflow",
             "implied breach outflow", "passed to the liman", "went to the liman", "without loss of recall",
             "without a detectable loss", "without a detectable recall loss", "daily observed", "flooded area = "]
FILES = [CS / "publication" / "manuscript_template.md", CS / "publication" / "manuscript.md", CS / "publication" / "captions.md",
         CS / "publication" / "evidence_matrix.csv", CS / "publication" / "claims.md", CS / "publication" / "tables" / "README.md",
         CS / "workflows" / "paper" / "p96_paper_tables.py", CS / "workflows" / "paper" / "p97_paper_figures.py",
         CS / "workflows" / "paper" / "p99_build_notebooks.py", CS / "workflows" / "paper" / "fill_evidence.py",
         ROOT / "apps" / "dashboard" / "streamlit_app.py", *sorted((ROOT / "apps" / "dashboard" / "pages").glob("*.py")),
         ROOT / "docs" / "METHODS.md", ROOT / "README.md"]


def _hits(text: str):
    low = re.sub(r"\s+", " ", text).lower()                  # a phrase broken across lines is still the phrase (audit 2026-09-28)
    return [f for f in FORBIDDEN if f.lower() in low]


def test_no_forbidden_phrases_in_publication_text():
    bad = {}
    for f in FILES:
        if f.exists():
            h = _hits(f.read_text(encoding="utf-8"))
            if h:
                bad[str(f.relative_to(ROOT))] = h
    assert not bad, bad


def test_terminology_file_lists_every_forbidden_phrase():
    t = (CS / "publication" / "TERMINOLOGY.md").read_text(encoding="utf-8").replace("\n", " ")
    for f in FORBIDDEN:
        assert f in t, f


def test_t13_uses_conditional_pod_name():
    head = (CS / "publication" / "tables" / "T13.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "POD_cond_outside_normally_wet" in head and "POD_excl" not in head


def test_t12_has_primary_columns_and_no_emulator():
    # D-EMU (maintainer, 2026-09-29): the 100 000-draw emulator is a diagnostic outside the evidence path -- T12d, never T12
    head = (CS / "publication" / "tables" / "T12.csv").read_text(encoding="utf-8").splitlines()[0]
    for c in ("W_total_p05_km2", "W_total_p95_km2", "A_p05_km2", "V_p05_hm3", "uncertainty_note", "mc_shift_V_pct"):
        assert c in head, c
    assert "emu" not in head
    d = (CS / "publication" / "tables" / "T12d.csv").read_text(encoding="utf-8")
    assert "DIAGNOSTIC, not evidence" in d


def test_t21_release_is_named_daily_mean():
    head = (CS / "publication" / "tables" / "T21.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "Q_release_eff_daily_mean_m3s" in head and "breach" not in head.lower()


def test_claims_carry_limitation_and_former_id():
    rows = list(csv.DictReader((CS / "publication" / "evidence_matrix.csv").open(encoding="utf-8")))
    assert [r["claim_id"] for r in rows] == [f"C{i:02d}" for i in range(1, 15)]
    assert all(r["limitation"].strip() for r in rows) and all(r["former_id"].strip() for r in rows)
    assert re.search(r"7 June", rows[0]["claim"]) and "between" in rows[0]["claim"]
