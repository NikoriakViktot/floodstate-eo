"""The event-agnostic gate (14_TESTING_STRATEGY.md of the migration audit): src/floodstate_eo/** must not name
Kakhovka, its frames or its towns -- that is what keeps the framework reusable for a second event.

THIS TEST DOES NOT PASS BY EXCLUDING EVERYTHING THAT FAILS IT. Migration Phase 5 (this commit) copied 20
Kakhovka-specific scripts and two core-library modules (`canonical_grid.py`, `optical_catalogue.py`) into
`src/floodstate_eo/**` verbatim, with provenance headers, because the manifest's own target-path column put them
there and because splitting Kakhovka literals out of them is Phase 6 work ("replace hard-coding with config"),
not this one (see provenance/KNOWN_GATE_EXCEPTIONS.md). Those exact files are therefore named below as a frozen
allowlist. The gate still does real work: any OTHER file added under src/floodstate_eo/** that starts leaking a
Kakhovka literal fails this test today, which is the leakage this gate exists to catch. Shrinking
KNOWN_EXCEPTIONS toward empty is the acceptance criterion for Phase 6, not a reason to touch this test.
"""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "floodstate_eo"

FORBIDDEN = re.compile(r"Kakhovka|Kherson|Oleshky|Hola Prystan|\bB1\b|\bB2\b|\bB3\b|ZONE_\d|/mnt/", re.IGNORECASE)

#: See provenance/KNOWN_GATE_EXCEPTIONS.md for why each of these is here and what removing it requires.
KNOWN_EXCEPTIONS = {
    "_kakhovka_legacy_config.py",
    # otherwise event-agnostic; each imports `_kakhovka_legacy_config` for exactly one function
    # (zone_grid / zone_outline / fig_size) that needs a case-study zone-geometry loader -- see
    # provenance/KNOWN_GATE_EXCEPTIONS.md
    "optical/sentinel_preprocess.py",
    "visualization/maps.py",
    "spatial/canonical_grid.py",
    "spatial/p52a_processing_frames_qa.py",
    "spatial/p52b_frame_sensor_inventory.py",
    "io/optical_catalogue.py",
    "io/p52c_cdse_optical_gap.py",
    "io/p52d_fetch_event_optics.py",
    "io/p52e_event_coverage.py",
    "io/p52f_pass2_b2_targeted.py",
    "io/p81_fetch_slc.py",
    "optical/p54a_frame_index_stacks_10m.py",
    "optical/p54b_frame_composites_10m.py",
    "validation/p54c_composites_10m_freeze_gate.py",
    "fusion/p65b_m2_spatial_cv.py",
    "fusion/p66_production_m2.py",
    "fusion/p67b_production_candidate.py",
    "fusion/p69b_event_association.py",
    "surface_state/p69a_base_class.py",
    "visualization/p69c_maps.py",
    "sar/p71_s1_event_change.py",
    "sar/p80_slc_pairing_manifest.py",
    "sar/p82_coherence_graph.py",
    "validation/p83_coherence_qc.py",
}


def test_no_new_kakhovka_leakage_outside_the_known_exceptions():
    violations = []
    for p in SRC.rglob("*.py"):
        rel = p.relative_to(SRC).as_posix()
        if rel in KNOWN_EXCEPTIONS:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        hit = FORBIDDEN.search(text)
        if hit:
            violations.append(f"{rel}: {hit.group(0)!r}")
    assert not violations, "event-agnostic gate failed outside the known exceptions:\n" + "\n".join(violations)


def test_known_exceptions_still_exist_and_still_violate():
    """If a listed file no longer violates the gate (or no longer exists), the allowlist is stale -- shrink it
    rather than leaving a dead entry that hides a real regression check."""
    stale = []
    for rel in sorted(KNOWN_EXCEPTIONS):
        p = SRC / rel
        if not p.exists():
            stale.append(f"{rel}: file no longer exists -- remove from KNOWN_EXCEPTIONS"); continue
        if not FORBIDDEN.search(p.read_text(encoding="utf-8", errors="ignore")):
            stale.append(f"{rel}: no longer contains a forbidden token -- remove from KNOWN_EXCEPTIONS")
    assert not stale, "KNOWN_EXCEPTIONS is stale:\n" + "\n".join(stale)
