"""The one table of what changed after the review of 2026-09-28 (T28): every row has old / new / reason / effect, and every
placeholder of it was resolved from the tables of the same build."""
from pathlib import Path

import pandas as pd

PT = Path(__file__).resolve().parents[1] / "case_studies/kakhovka_2023/publication/tables"


def test_t28_complete_and_resolved():
    A = pd.read_csv(PT / "T28.csv", dtype=str).fillna("")
    assert len(A) >= 40 and {"old", "new", "reason", "impact_on_conclusion", "review_ref", "evidence"} <= set(A.columns)
    for c in ("item", "old", "new", "reason", "impact_on_conclusion"):
        assert (A[c].str.strip() != "").all(), c
    assert not A.apply(lambda r: "[[MISSING" in " ".join(r) or "{{" in " ".join(r), axis=1).any()
    assert A.id.is_unique and A.block.str.match(r"^[0-5] ").all()


def test_t28_records_the_retracted_and_narrowed_claims():
    A = pd.read_csv(PT / "T28.csv", dtype=str).fillna("")
    assert A.impact_on_conclusion.str.contains("RETRACTED").any()          # C10 (D-C10)
    assert A.item.str.contains("C13").any() and A.item.str.contains("C09").any()
