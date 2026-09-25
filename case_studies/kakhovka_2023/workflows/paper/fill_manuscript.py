# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Resolves table placeholders in the manuscript template.
"""fill_manuscript -- every number in publication/manuscript.md comes from a publication table cell.

Template syntax (publication/manuscript_template.md):
    {{TID|col=value,col=value|column|agg|fmt}}      agg in first (default), sum, mean, min, max, count; fmt like .0f / .2f / +.1f
filters separated by ',' or, when a value contains a comma, by ';'.
e.g. {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_central_km2||.0f}}  or  {{T14|date=2023-06-09,category=C|km2_ground_ge5m_above|sum|.0f}}
Unresolvable placeholders are left as `[[MISSING: ...]]` and listed at the end so the text can never silently show a wrong number.
"""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd

PUB = Path(__file__).resolve().parents[2] / "publication"; PT = PUB / "tables"
PAT = re.compile(r"\{\{([A-Za-z0-9]+)\|([^|]*)\|([^|]+)\|([^|]*)\|([^}]*)\}\}")
_cache = {}


def table(tid):
    if tid not in _cache:
        _cache[tid] = pd.read_csv(PT / f"{tid}.csv")
    return _cache[tid]


def resolve(m):
    tid, filt, col, agg, fmt = m.groups(); agg = agg or "first"
    try:
        df = table(tid)
        for f in [x for x in (filt.split(";") if ";" in filt else filt.split(",")) if x.strip()]:
            k, v = f.split("=", 1); s = df[k].astype(str); df = df[s == v]
        if len(df) == 0 or col not in df.columns:
            return f"[[MISSING: {m.group(0)}]]"
        x = df[col]
        val = {"first": lambda: x.iloc[0], "sum": lambda: x.sum(), "mean": lambda: x.mean(), "min": lambda: x.min(), "max": lambda: x.max(), "count": lambda: len(x)}[agg]()
        return format(val, fmt) if fmt else str(val)
    except Exception as e:                                                   # noqa: BLE001
        return f"[[MISSING: {m.group(0)} ({e})]]"


def main():
    txt = (PUB / "manuscript_template.md").read_text(); out = PAT.sub(resolve, txt)
    missing = re.findall(r"\[\[MISSING: [^\]]*\]\]", out)
    (PUB / "manuscript.md").write_text(out + ("\n\n<!-- UNRESOLVED PLACEHOLDERS -->\n" + "\n".join(missing) if missing else ""))
    print(f"-> manuscript.md ({len(PAT.findall(txt))} placeholders, {len(missing)} unresolved)")
    for mm in missing:
        print("  ", mm)


if __name__ == "__main__":
    main()
