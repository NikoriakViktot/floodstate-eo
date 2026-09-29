"""Review F16: the whole reconstruction + Monte-Carlo chain runs end to end on an open synthetic geodomain (no bulk data)."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _run(tmp, draws=6):
    s = importlib.util.spec_from_file_location("tiny_run", ROOT / "examples/tiny_geodomain/run.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    S = m.main(["--draws", str(draws), "--out", str(tmp)])
    return S, pd.read_csv(tmp / "draws.csv")


def test_tiny_geodomain_end_to_end(tmp_path):
    S, R = _run(tmp_path / "a")
    pre = S[S.date < "2023-06-06"]
    assert (pre.A_central_km2 == 0).all() and (pre[["A_p05_km2", "A_p50_km2", "A_p95_km2"]] == 0).all().all()   # no new water before the event
    for q in ("A", "W_total"):
        lo, mid, hi = S[f"{q}_p05_km2"], S[f"{q}_p50_km2"], S[f"{q}_p95_km2"]
        assert ((lo <= mid + 1e-9) & (mid <= hi + 1e-9)).all()
    assert (R.new_km2 <= R.potential_km2 + 1e-9).all()                       # new water is part of the day's water
    assert S.loc[S.A_central_km2.idxmax(), "date"] == "2023-06-07"            # the areal maximum of the synthetic hydrograph
    assert (tmp_path / "a" / "summary.csv").exists()


def test_tiny_geodomain_is_reproducible(tmp_path):
    _, R1 = _run(tmp_path / "a", draws=3); _, R2 = _run(tmp_path / "b", draws=3)
    assert R1.equals(R2)
