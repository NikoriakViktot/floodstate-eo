# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is (and isn't yet)

FloodState-EO (v0.1.0-alpha) is a Sentinel-1/2 flood-state reconstruction framework being **extracted from the
SWOT-DNIPRO repo** (`~/repo/SWOT-DNIPRO`, frozen at source commit `f3e3e1afe91902a82a73f3c09354d1f9eb847766`).
Only migration Phase 5 ("copy canonical code with provenance headers") is done. Until Phase 6 ("replace
hard-coding with config") runs, `src/floodstate_eo/` is mostly a relocated copy of SWOT-DNIPRO's Kakhovka
scripts, not an event-agnostic framework. **Read `NEXT_STEPS.md` first** — it records current state, pending
uncommitted work and the ordered phase plan.

No multi-class flood-state classifier (M0–M5), S1/S2 fusion, or uncertainty product exists. `FLOOD_STATE`,
`URBAN_SCORE`, `UNCERTAINTY`, `FINAL_FLOOD_MASK` are `PROPOSED / NOT YET CANONICAL` in `docs/DATA_DICTIONARY.md`.
Don't describe planned things as implemented; docs tag every section with implemented/partial/planned status.

## Commands

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # pytest + ruff

pytest                                             # all tests (testpaths = tests)
pytest tests/test_composites.py::test_mode_ignores_invalid_votes   # single test
ruff check src tests
```

Pipeline stages are standalone scripts with `argparse` mains, run as modules, e.g.
`python -m floodstate_eo.fusion.p66_production_m2 --fit-n N`. They need the case-study bulk data (>100 GB, not in
the repo); no end-to-end run has yet been executed from this repo's layout. The notebook in
`case_studies/kakhovka_2023/notebooks/` is a narrative skeleton and does not execute end-to-end.

## Architecture

**Two kinds of code under `src/floodstate_eo/`:**
- *Core library modules* (event-agnostic or nearly so): `optical/composites.py`, `optical/watermask.py`,
  `optical/sentinel_preprocess.py`, `spatial/canonical_grid.py`, `spatial/domains.py`, `io/optical_catalogue.py`,
  `visualization/maps.py`.
- *Numbered pipeline scripts* `pNN*.py`, named after their SWOT-DNIPRO originals and filed by concern. Rough
  data flow:
  - Optical: `spatial/p52a,p52b` (frames QA, sensor inventory) → `io/p52c–p52f` (CDSE fetch/coverage) →
    `optical/p54a` (per-date 10 m index stacks, 7 indices) → `optical/p54b` (PRE/EVENT/TRACE composites) →
    `validation/p54c` (freeze gate).
  - M2 evidence (S2-only RF): `fusion/p65b` (nested spatial CV, 5 km blocks) → `fusion/p66` and `fusion/p67b`
    (two *unreconciled* production fits of the same model).
  - Surface state: `surface_state/p69a` (`BASE_CLASS`, built only from PRE-window evidence + ESA WorldCover 2021;
    deliberately blind to event evidence) → `fusion/p69b` (BASE_CLASS × M2 "event association", weaker than a
    flood claim) → `visualization/p69c` (maps).
  - SAR: `sar/p71` (orbit-matched S1 event-change channels, no consumer yet); `sar/p80` → `io/p81` →
    `sar/p82` (SNAP `gpt` coherence in Docker; currently blocked by Java heap OOM under the WSL2 memory cap) →
    `validation/p83`.
- All work is on the canonical 10 m B1/B2/B3 frames (`canonical_grid.frame_grid()`), not SWOT-DNIPRO's legacy
  20 m zone grid. The legacy `p51` RF was intentionally not migrated.

**Config shim.** Migrated scripts read `CFG.*` from `src/floodstate_eo/_kakhovka_legacy_config.py`, not yet the
YAMLs in `case_studies/kakhovka_2023/config/` (which are the Phase 6 target; each shim constant is commented with
its YAML destination). Key paths: outputs go under `case_studies/kakhovka_2023/{tables,figures,outputs}`; bulk
data comes from `FLOODSTATE_DATA_ROOT` (fallback `SWOT_DNIPRO_BULK_ROOT`, then `/mnt/f/data_kakhovka_dem_swot`,
then `case_studies/kakhovka_2023/data`). Zone/reservoir geometries are still read from sibling repos
(`SWOT_DNIPRO_ROOT`, `SWOT_DNIPRO_ICESAT_ROOT`) — see `provenance/UNRESOLVED_DEPENDENCIES.md` #3.

**Semantics that the code enforces and edits must preserve:** `n_obs` is observation count, never a validity
gate; "not observed is not dry" — cells without optical observation get NODATA, never a score or zero
(`prediction_valid.tif`); validation bootstraps over spatial blocks, never pixels; M2 scores are continuous
(`flood_score.tif` uint16 ×10000, nodata 65535), thresholding is a separate later step.

## Event-agnostic gate (the key invariant)

`tests/test_event_agnostic_gate.py` forbids `Kakhovka|Kherson|Oleshky|Hola Prystan|B1|B2|B3|ZONE_\d|/mnt/` in
any `src/floodstate_eo/**/*.py` except an explicit `KNOWN_EXCEPTIONS` allowlist (documented per-file in
`provenance/KNOWN_GATE_EXCEPTIONS.md`).
- New code under `src/` must not contain these literals; case-study specifics belong in `case_studies/<event>/`.
- Never add a file to `KNOWN_EXCEPTIONS` to make the test pass, and never narrow the scan.
- When a Phase 6 refactor removes all forbidden literals from a file, remove it from `KNOWN_EXCEPTIONS` — the
  companion test fails if a listed file no longer violates (or no longer exists). Shrinking this list is the
  Phase 6 acceptance criterion.

## Provenance conventions

- Every migrated file starts with a `# Provenance:` header (source path, source commit SHA, copy date, manifest
  row, and exactly what was changed — usually "import block only"). Keep and update it when modifying such files;
  logic was copied byte-identical to source.
- `provenance/MIGRATION_MANIFEST.csv` tracks every copied file (source sha256, target path, category, phase,
  status). `provenance/UNRESOLVED_DEPENDENCIES.md` lists what was deliberately not migrated or is unresolved
  (fetch helpers, p51, two RNG seeds, three temporal-window variants, WorldCover fetch code, FABDEM licence).
- Data policy: no raw/bulk data in git. Data sources are registered as manifests in
  `case_studies/kakhovka_2023/manifests/*.csv` (use `TBD` for unknown sha256, never invent values).

## Working rules for this repo

- The repo is local-only (not pushed). Don't push, rewrite history, or copy more files from SWOT-DNIPRO without
  the maintainer's explicit go-ahead.
- Distinguish verified behaviour from design docs: a design in `docs/METHODS.md` (e.g. §15 fusion) is not
  implemented code. Verify data access by actually loading data, not just by imports succeeding.
