# Known event-agnostic gate exceptions

`04_CORE_VS_CASE_STUDY.md` of the migration audit requires `src/floodstate_eo/**` to be event-agnostic: no
`Kakhovka`, `B1|B2|B3`, `Kherson`, `Oleshky`, `Hola Prystan`, `ZONE_`, or `/mnt/` literal. `tests/test_event_agnostic_gate.py`
enforces this with an explicit, named allowlist rather than by narrowing its scan silently. Every file on that
allowlist is listed here with why it's there and what removing it requires.

## Why these files exist under `src/floodstate_eo/**` at all

`19_MIGRATION_MANIFEST.csv`'s own `target_path` column put 20 Kakhovka-specific scripts and two core-library
modules (`canonical_grid.py`, `optical_catalogue.py`) directly under `src/floodstate_eo/**`, tagged
`migration_phase=5` ("copy canonical code with provenance headers"). Splitting each one into a truly
event-agnostic core plus a case-study-specific residue is `migration_phase=6` ("replace hard-coding with
config") — not run in this commit. Copying them verbatim, honestly flagged, was judged better than a half
refactor that silently drops fidelity to the source.

## The list (see `tests/test_event_agnostic_gate.py::KNOWN_EXCEPTIONS` for the exact, machine-checked set)

- **`_kakhovka_legacy_config.py`** — a Phase-5 compatibility shim (`CFG.TABLES`, `CFG.BULK_ROOT`,
  `CFG.BREACH_DATE`, etc.) so the 20 scripts below still import successfully as a package. Removing it requires
  rewiring every one of those 20 scripts to read `case_studies/kakhovka_2023/config/*.yaml` instead (Phase 6).
- **`spatial/canonical_grid.py`** — hard-codes the B1/B2/B3 bboxes and the string "Kherson" (`FRAME_LABEL`).
  Depended on by `CG.frame_grid()` in essentially every migrated script. Removing it requires splitting the
  generic snap/grid mechanics from the frame constants and rewiring every caller — `study_area.yaml` already
  stages the frame data as a target.
- **`io/optical_catalogue.py`** — hard-codes the `ZONES` tuple. Needed by `p54a`/`p54c` as migrated.
- **`optical/sentinel_preprocess.py`**, **`visualization/maps.py`** — otherwise event-agnostic; each imports
  `_kakhovka_legacy_config` inside exactly one function (`zone_grid()`, `zone_outline()`/`fig_size()`
  respectively) that needs a case-study zone-geometry loader. Removing the exception requires either injecting
  the loader as a parameter (so the function stops importing a named case study by itself) or moving that one
  function out to a case-study module — a smaller, well-scoped Phase 6 task compared to the scripts below.
- **The 20 Kakhovka-specific scripts** (`spatial/p52a*`, `spatial/p52b*`, `io/p52c*`–`p52f*`, `io/p81*`,
  `optical/p54a*`, `optical/p54b*`, `validation/p54c*`, `fusion/p65b*`, `fusion/p66*`, `fusion/p67b*`,
  `fusion/p69b*`, `surface_state/p69a*`, `visualization/p69c*`, `sar/p71*`, `sar/p80*`, `sar/p82*`,
  `validation/p83*`) — each one IS the Kakhovka-specific processing logic; there is no event-agnostic residue to
  keep once the Kakhovka literals are removed, because the whole script only makes sense for this event. What
  Phase 6 would actually do here is closer to `05_PROPOSED_REPOSITORY_TREE.md`'s plan: extract the reusable
  *shape* of each script (a `flood_state`/`surface_state`/`fusion` module that takes a frame/window/threshold
  config) into `src/floodstate_eo/`, and leave a thin, Kakhovka-specific `workflows/` entry point that calls it
  with this case study's config. That is new design work, not a mechanical split, and is explicitly out of
  scope for this migration commit.

## Acceptance criterion for Phase 6

`KNOWN_EXCEPTIONS` in `tests/test_event_agnostic_gate.py` shrinks toward empty as each file above is genuinely
split into event-agnostic framework code + case-study configuration/workflow. `tests/test_event_agnostic_gate.py::test_known_exceptions_still_exist_and_still_violate`
fails loudly if an entry is removed from the allowlist while the file itself hasn't actually changed, so the list
cannot go stale silently in either direction.
