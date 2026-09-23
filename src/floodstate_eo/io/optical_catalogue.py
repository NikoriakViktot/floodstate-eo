# Provenance: SWOT-DNIPRO src/swot_dnipro/optical_catalogue.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CORE_LIBRARY, per 19_MIGRATION_MANIFEST.csv row 26 (migration_phase=5).
# KNOWN EVENT-AGNOSTIC GATE EXCEPTION (provenance/KNOWN_GATE_EXCEPTIONS.md): the module-level `ZONES` tuple
# hard-codes Kakhovka zone names. Needed by p54a/p54c as migrated; splitting it out is Phase 6 work.
"""Which Sentinel-2 acquisition a date is built from, and at what native resolution.

WHY THIS MODULE EXISTS. An earlier catalogue function searched exactly ONE directory for SAFE archives and
silently fell back to legacy per-zone 20 m index stacks for every other date. Measured consequence on the
10 m rebuild:

    window   dates the catalogue saw   of those read from native SAFE   dates with SAFE actually on disk
    pre      19                        0                                51
    event    23                        18                               23
    trace    20                        0                                24

So PRE and TRACE were built ENTIRELY from legacy products, and five EVENT dates too. That is not a coverage
detail, it is a lineage split inside one feature vector:

  * a legacy stack is `cell_m = 20.0`: B02/B03/B04/B08 were resampled to 20 m BEFORE the index was computed,
    so NDVI/NDWI/NDTI carry 20 m information, not 10 m;
  * it sits on the zone-grid cell-centre registration, x0 = 10 (mod 20) -- the half-cell grid the whole move
    to 10 m was ordered to escape. Replicating it 1->2 with nearest is geometrically exact, but it re-imports
    the 20 m radiometry the frame lattice was supposed to leave behind.

`d_med`, `d_ext` and `d_trace` difference EVENT against PRE. With the split above, every one of those features
would have differenced a true 10 m statistic against a 20 m-derived one, and the residual would look like
change along every shoreline.

RULE. Per date, one lineage. If any native SAFE exists for that date, the date is built from SAFE alone and
any legacy stack for it is recorded as superseded; a legacy stack is used ONLY where no SAFE exists, and then
the date is tagged LEGACY_20M so the manifest and every downstream reader can see it. Never mix the two
within a date.
"""
from __future__ import annotations
import re
from collections import defaultdict
from pathlib import Path

from .. import _kakhovka_legacy_config as CFG

ZONES = ("ZONE_4_DAM_TO_KHERSON_FLOODWAY", "ZONE_2_KHERSON_DELTA", "ZONE_3_DNIPRO_BUG_ESTUARY")
#: directories that hold no science product, only provenance experiments
EXCLUDE = ("provenance_probe",)
_SAFE_RE = re.compile(r"S2[AB]_MSIL2A_(\d{8})T(\d{6})_N(\d{4})_R\d{3}_T(\d{2}[A-Z]{3})_")

SAFE_10M = "SAFE_10M"
LEGACY_20M = "LEGACY_20M"


def safe_roots() -> list[Path]:
    """Every root that may hold SAFE archives. Discovery is by search, not by a hard-coded directory -- one
    hard-coded directory is precisely how 51 pre-breach dates became 19."""
    return [p for p in (CFG.BULK_ROOT, CFG.DATA_RAW) if p.exists()]


def scan_safes() -> dict[str, list[Path]]:
    """{date: [zip, ...]}, deduplicated by (sensing time, tile): the same acquisition sits in more than one fetch
    directory, and counting it twice would double its weight in a median."""
    best: dict[tuple, tuple] = {}
    for root in safe_roots():
        for z in root.rglob("S2*_MSIL2A_*.zip"):
            if any(x in z.parts for x in EXCLUDE):
                continue
            m = _SAFE_RE.search(z.name)
            if not m:
                continue
            d, t, base, tile = m.groups()
            key = (d, t, tile)
            prev = best.get(key)
            if prev is None or (int(base), z.stat().st_size) > (int(prev[0]), prev[1].stat().st_size):
                best[key] = (base, z)          # higher processing baseline wins, then the larger file
    out: dict[str, list[Path]] = defaultdict(list)
    for (d, _t, _tile), (_b, z) in sorted(best.items()):
        out[f"{d[:4]}-{d[4:6]}-{d[6:]}"].append(z)
    return dict(out)


def scan_stacks() -> dict[str, list[tuple[str, Path]]]:
    """{date: [(zone, path), ...]} of the legacy 20 m per-zone index stacks."""
    out: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    for z in ZONES:
        dz = CFG.BULK_ROOT / "zone_spectral" / z
        if not dz.exists():
            continue
        for p in sorted(dz.glob("*_indices.tif")):
            out[p.name[:10]].append((z, p))
    return dict(out)


def catalogue(lo: str, hi: str) -> dict[str, dict]:
    """{date: dict(safes=[...], stacks=[(zone, path), ...], lineage=..., native_m=..., superseded_stacks=[...])}.

    `safes` is populated from every archive root, and `stacks` is EMPTY whenever SAFE exists for that date.
    """
    safes, stacks = scan_safes(), scan_stacks()
    out = {}
    for d in sorted(set(safes) | set(stacks)):
        if not (lo <= d <= hi):
            continue
        if safes.get(d):
            out[d] = dict(safes=list(safes[d]), stacks=[], lineage=SAFE_10M, native_m=10,
                          superseded_stacks=[p for _z, p in stacks.get(d, [])])
        else:
            out[d] = dict(safes=[], stacks=list(stacks[d]), lineage=LEGACY_20M, native_m=20, superseded_stacks=[])
    return out


def summary(windows: dict[str, tuple[str, str]]) -> list[dict]:
    """One row per window: how many dates, and how many of them carry which lineage."""
    rows = []
    for w, (lo, hi) in windows.items():
        cat = catalogue(lo, hi)
        s = [d for d, v in cat.items() if v["lineage"] == SAFE_10M]
        g = [d for d, v in cat.items() if v["lineage"] == LEGACY_20M]
        rows.append(dict(window=w, lo=lo, hi=hi, n_dates=len(cat), n_safe_10m=len(s), n_legacy_20m=len(g),
                         n_zips=sum(len(v["safes"]) for v in cat.values()),
                         n_superseded_stacks=sum(len(v["superseded_stacks"]) for v in cat.values()),
                         legacy_dates=";".join(g)))
    return rows
