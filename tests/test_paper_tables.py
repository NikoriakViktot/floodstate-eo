"""Publication tables: manifest integrity, load-bearing cells traceable to their sources, evidence levels present.
Runs without bulk data (reads committed tables only)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

CS = Path(__file__).resolve().parents[1] / "case_studies" / "kakhovka_2023"
PT = CS / "publication" / "tables"; T = CS / "tables"


def test_manifest_and_files():
    man = json.loads((PT / "manifest.json").read_text())
    assert len(man["git_commit"]) == 40 and len(man["tables"]) >= 25
    for tid, m in man["tables"].items():
        p = PT / f"{tid}.csv"; assert p.exists() and (PT / f"{tid}.md").exists()
        assert hashlib.sha256(p.read_bytes()).hexdigest() == m["sha256"], tid
        assert m["evidence_level"] in {"independent_physical", "cross_sensor", "weak_label_agreement", "contextual", "mixed"}


def test_area_semantics_present():
    for tid in ("T12", "T16", "T19"):
        df = pd.read_csv(PT / f"{tid}.csv"); assert "area_semantics" in df.columns and df.area_semantics.notna().all()


def test_t12_matches_p95_daily_table():
    t = pd.read_csv(PT / "T12.csv"); src = pd.read_csv(T / "p95_daily_area_pooled_connected_ceiling.csv")
    m = t.merge(src, on=["date", "region"], suffixes=("", "_src"))
    assert np.allclose(m.A_central_km2, m.new_km2) and len(m) == len(t)


def test_t09_overall_agreement_from_confusion():
    cm = pd.read_csv(T / "p73_rf20_confusion_matrix.csv", index_col=0).values.astype(float); oa = np.trace(cm) / cm.sum()
    t = pd.read_csv(PT / "T09.csv"); assert abs(float(t.OA_spatial_cv.dropna().iloc[0]) - oa) < 1e-3


def test_t18_is_a_faithful_copy_of_p57():
    t = pd.read_csv(PT / "T18.csv"); s = pd.read_csv(T / "p57_dem_accuracy_night.csv")
    row = t[t.set.str.contains("ALL night")].iloc[0]; src = s[s.set.str.contains("ALL night")].iloc[0]
    assert row.RMSE == src.RMSE and row.NMAD == src.NMAD


def test_t07b_paired_effects_from_p90():
    t = pd.read_csv(PT / "T07b.csv"); s = pd.read_csv(T / "p90_v003A_paired.csv")
    assert len(t) == len(s) and np.allclose(t["median"], s["median"])


def test_no_withdrawn_inhulets_numbers_in_claims():
    txt = (CS / "publication" / "claims.md").read_text() + (CS / "publication" / "evidence_matrix.csv").read_text()
    assert "0.78-0.98" not in txt.replace("–", "-") or "withdrawn" in txt.lower()
