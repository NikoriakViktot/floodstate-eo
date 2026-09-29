"""Review F17: one version -- pyproject.toml, the package and the README status line agree."""
import re
from pathlib import Path

import floodstate_eo

ROOT = Path(__file__).resolve().parents[1]


def test_one_version_everywhere():
    py = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M).group(1)
    assert floodstate_eo.__version__ == py
    m = re.match(r"(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?$", py); assert m
    tag = f"v{m[1]}.{m[2]}.{m[3]}" + ({"a": "-alpha", "b": "-beta", "rc": f"-rc{m[5]}"}[m[4]] if m[4] else "")
    assert tag in (ROOT / "README.md").read_text().split("**Status:")[1][:120], tag
