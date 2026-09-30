"""fill_manuscript: the `neg` format prefix prints the negated cell (a 'decrease by x' from a cell of -x), any table getter works."""
import importlib.util
from pathlib import Path

import pandas as pd

_P = Path(__file__).resolve().parents[1] / "case_studies/kakhovka_2023/workflows/paper/fill_manuscript.py"
_s = importlib.util.spec_from_file_location("fill_manuscript", _P); FM = importlib.util.module_from_spec(_s); _s.loader.exec_module(FM)


def test_neg_format_and_getter():
    T = {"TX": pd.DataFrame(dict(k=["a", "b"], v=[-13.81, 2.5]))}
    res = FM.make_resolver(lambda t: T[t])
    txt = "decreased by {{TX|k=a|v||neg.1f}} km2, then {{TX|k=b|v||+.1f}}; missing {{TX|k=z|v||.1f}}"
    out = FM.PAT.sub(res, txt)
    assert "decreased by 13.8 km2" in out and "then +2.5" in out and "[[MISSING" in out
