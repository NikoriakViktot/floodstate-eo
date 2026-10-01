"""Every agreement metric in the publication tables carries its passport (maintainer 2026-10-01, "why never the full picture"):
a table with a CSI column must say what was compared (a domain / ground / region column), how much of it was observed (a coverage
column) and what the number is worth (a chance level or Heidke skill, or an admissible interval over the undecided cells)."""
from pathlib import Path

import pandas as pd

PT = Path(__file__).resolve().parents[1] / "case_studies/kakhovka_2023/publication/tables"
DOMAIN_COLS = ("observation_domain", "ground", "region")
COVERAGE_COLS = ("coverage", "coverage_of_observable_domain")
WORTH_COLS = (("CSI_chance",), ("heidke_skill",), ("CSI_min", "CSI_max"))


def _csi_tables():
    out = []
    for p in sorted(PT.glob("T*.csv")):
        cols = pd.read_csv(p, nrows=0).columns
        if any(c == "CSI" or c.startswith("CSI_") for c in cols):
            out.append((p.name, set(cols)))
    return out


def test_every_csi_table_has_a_passport():
    tabs = _csi_tables()
    assert tabs, "no table with a CSI column found"
    for name, cols in tabs:
        assert any(c in cols for c in DOMAIN_COLS), f"{name}: no domain column"
        assert any(c in cols for c in COVERAGE_COLS), f"{name}: no coverage column"
        assert any(all(c in cols for c in group) for group in WORTH_COLS), f"{name}: no chance level, Heidke skill or admissible interval"


def test_t13_passport_values_are_defined_where_water_exists():
    D = pd.read_csv(PT / "T13.csv")
    has = D[(D.s1_new_km2 + D.hand_new_km2) > 0]
    assert has.CSI_chance.notna().all() and has.heidke_skill.notna().all()
    assert ((has.CSI_chance >= 0) & (has.CSI_chance <= 1)).all() and (has.coverage_of_observable_domain <= 1).all()
