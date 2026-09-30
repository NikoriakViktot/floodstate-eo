# New in floodstate-eo, 2026-09-30. STATUS: ACTIVE. The Kherson gauge series in the frame of Paper 1 (release v6).
"""P59k -- rewrites the EVRF2019 column of tables/p59_swot_vs_kherson.csv with the EPSG:9902 step of Paper 1 v6 at the post's own
coordinates (+0.2076 m; the extracted p59 table had carried +0.22 m, so every Kherson level of Paper 3 stood 1.24 cm above Paper 1's).
The BS-77 stage (river yearbook, water_level_m_abs) is untouched; swot_minus_gauge follows the new column. Idempotent.

Outputs: <case_study>/tables/p59_swot_vs_kherson.csv (H_gauge_evrf, swot_minus_gauge), tables/p59k_kherson_frame.json
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from floodstate_eo import _kakhovka_legacy_config as CFG

_s = importlib.util.spec_from_file_location("paper1_frame", Path(__file__).with_name("paper1_frame.py")); PF = importlib.util.module_from_spec(_s); _s.loader.exec_module(PF)


def main():
    import pandas as pd
    p = CFG.TABLES / "p59_swot_vs_kherson.csv"; g = pd.read_csv(p)
    old = float((g.H_gauge_evrf - g.water_level_m_abs).median())
    g["H_gauge_evrf"] = (g.water_level_m_abs + PF.KHERSON_DELTA_EPSG9902_M).round(4)
    g["swot_minus_gauge"] = g.swot_p50 - g.H_gauge_evrf
    g.to_csv(p, index=False)
    man = dict(table=str(p.relative_to(CFG.CASE_STUDY_ROOT)) if hasattr(CFG, "CASE_STUDY_ROOT") else p.name, delta_epsg9902_m=PF.KHERSON_DELTA_EPSG9902_M,
               previous_step_m=round(old, 4), source="Paper 1 v6 (SWOT-DNIPRO release paper1-v6): EPSG:9902 grid at the post's own coordinates",
               stage="river yearbook BS-77 stage (water_level_m_abs), unchanged")
    (CFG.TABLES / "p59k_kherson_frame.json").write_text(json.dumps(man, indent=1)); print(json.dumps(man))


if __name__ == "__main__":
    main()
