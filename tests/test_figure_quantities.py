"""Review F15: a figure's plotted series is the quantity its caption names (Fig09c: effective release Q_in - dV/dt,
not -dV/dt; flows and storage on separate axes)."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("p97", ROOT / "case_studies/kakhovka_2023/workflows/paper/p97_paper_figures.py")
P97 = importlib.util.module_from_spec(_s); _s.loader.exec_module(P97)


def test_fig09c_bars_are_the_effective_release_named_in_the_caption():
    R = pd.read_csv(ROOT / "case_studies/kakhovka_2023/tables/p95f_reservoir_daily.csv"); R["t"] = pd.to_datetime(R.date)
    flows, stored = P97.fig09c_series(R)
    m = R.set_index("t").loc[flows.t]
    expected = (m.Q_in_hm3_day - m.dV_pool_hm3).to_numpy() / 1000          # Q_in - dV/dt, km3 per day
    assert np.allclose(flows.release_km3_day.to_numpy(), expected, atol=1e-3, equal_nan=True)
    ok = np.isfinite(m.Q_in_hm3_day.to_numpy()) & (m.Q_in_hm3_day.to_numpy() > 0)
    assert ok.any() and not np.allclose(flows.release_km3_day.to_numpy()[ok], (-m.dV_pool_hm3.to_numpy() / 1000)[ok])   # not -dV/dt
    assert set(stored.columns) == {"t", "stored_km3"} and "stored" not in "".join(flows.columns)   # volume never on the flow axis
    caption = (ROOT / "case_studies/kakhovka_2023/publication/captions.md").read_text()
    assert "Q_in − dV/dt" in caption and "VERIFY" not in caption.split("**Fig09")[1].split("**")[1]
