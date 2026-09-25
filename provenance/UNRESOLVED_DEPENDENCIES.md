# Unresolved dependencies

Things the migrated code (`src/floodstate_eo/**`) still needs that were not migrated in this commit, because they
are not in `19_MIGRATION_MANIFEST.csv` (the migration audit's authoritative scope) or are external to both
repositories. Each entry names the gap, why it was left open rather than silently filled, and what resolving it
requires.

## 1. `p1_targeted_fetch.py` (hardened download/verify/atomic-publish helpers)

**Where it's needed:** `src/floodstate_eo/io/p52d_fetch_event_optics.py` imports it (as `P1F`) for
`verified()`, `KeepAuth`, `verify()`, `sidecar()`. Left as `P1F = None`; calling `fetch()` will raise
`AttributeError`, which is the honest behaviour for an unmigrated dependency rather than a working stub that
fakes integrity checking.

**Why not pulled in:** it is a general SWOT-DNIPRO fetch utility, not classified CANONICAL/CORE_LIBRARY for
floodstate-eo in the manifest.

**To resolve:** port or reimplement the four helpers as Phase 6 work, or replace `p52d` with a
manifest-driven `workflows/fetch_*` CLI per `05_PROPOSED_REPOSITORY_TREE.md` / `08_DATA_POLICY.md`.

## 2. `style.py` (map furniture: scale bar, north arrow, a colour lookup)

**Where it's needed:** `src/floodstate_eo/visualization/maps.py`'s `finish()` (scale bar / north arrow, already
wrapped in `try/except` in the source) and `zone_outline()` (colour lookup, now falls back to a literal
default).

**Why not pulled in:** not in the manifest.

**RESOLVED 2026-09-25:** `src/floodstate_eo/visualization/figstyle.py` -- an event-agnostic adaptation of SWOT-DNIPRO
`plotting/style.py` (provenance header in the file; palette replaced by the evidence-hierarchy colours; scale bar, north
arrow, graticule, date axis, bands, forest plots, NMAD/bootstrap helpers). `maps.py` still uses its own literal fallback;
switching it to `figstyle` is a Phase-6 cleanup.

## 3. Kakhovka zone and reservoir domain geometries

**Where it's needed:** `src/floodstate_eo/_kakhovka_legacy_config.py`'s `KAKHOVKA_LOADERS` (used by
`optical/sentinel_preprocess.zone_grid()`, `visualization/maps.zone_outline()`, and several `p52*`/`p69a`
scripts that call `CFG.load_utm(zone)`).

**What it does today:** reads `ZONE_1..4` from `<SWOT_DNIPRO_ROOT>/data/processed/domains/analysis_zones_utm.geojson`
and the pre-breach reservoir pool from `<SWOT_DNIPRO_ICESAT_ROOT>/data/Kakhovka_SA_2.geojson` — i.e. it depends on
sibling-repository checkouts existing on disk, exactly like SWOT-DNIPRO's own `spatial_domains.py` did before it.

**Why not vendored:** these are geometry data files, not code; `08_DATA_POLICY.md`'s policy is manifest-based data
management (GitHub for code/small products, not raw geometry files) — vendoring them wholesale would violate that
policy before a manifest even exists.

**To resolve:** add `case_studies/kakhovka_2023/manifests/domains.csv` (source, checksum, licence) and either a
small vendored copy (if size/licence allow) or a `workflows/fetch_domains.py` that reconstructs them, per Phase 6.

## 4. `p51_rf_flood_optical.py` (legacy Random Forest, 20 m zone grid)

**Deliberately not migrated** — the manifest excludes it. It is one of the two unreconciled flood-state evidence
paths named in `00_EXECUTIVE_SUMMARY.md`'s addendum; migrating it without reconciling it against M2 would create
a third, not resolve the ambiguity. Its outputs must never be cited from this repository as comparable to M2's.

## 5. Two different RNG seeds across the M2 chain

`fusion/p65b_m2_spatial_cv.py` uses `SEED = 20260921`; `fusion/p66_production_m2.py` and
`fusion/p67b_production_candidate.py` use `SEED = 20260922`. Both values are cited verbatim from source, not
reconciled into one canonical seed. See `case_studies/kakhovka_2023/config/model.yaml`'s `seed_note`.

## 6. Three unreconciled temporal-window variants

`case_studies/kakhovka_2023/config/temporal_windows.yaml` documents the PRE/EVENT/TRACE windows the 10 m
pipeline uses (`p54b`'s `WIN`), but the source repository also has a legacy `p51` window set
(`EVENT_WINDOW`/`TRACE_WINDOW`/`PRE_YEARS`) and a `p25` regime-bounds variant, neither migrated nor reconciled
with this one. Flagged explicitly in `04_CORE_VS_CASE_STUDY.md` of the migration audit as "3 variants must be
reconciled" — a science-adjacent decision, out of scope for this Phase 5 copy.

## 7. ESA WorldCover 2021 fetch/tiling code

**Where it's needed:** `surface_state/p69a_base_class.py`'s `ancillary(frame, "wc")` (line 84) reads
`CFG.BULK_ROOT/"worldcover_frames"/<ZONE>/"wc_2021_20m.tif"` — this is a **required, load-bearing** input: several
`BASE_CLASS` rules key directly on WorldCover class codes (10/20/30/40/95/100, 60, 50, 90). `08_DATA_POLICY.md`'s
pre-migration draft listed Dynamic World as "used as context" and didn't mention WorldCover as load-bearing; a
post-migration grep of the actual `src/floodstate_eo/**` tree found the opposite (Dynamic World: zero references,
excluded; WorldCover: required). See `case_studies/kakhovka_2023/manifests/external.csv`.

**Why not pulled in:** the script that fetches/tiles WorldCover per zone onto `worldcover_frames/` is not in
`19_MIGRATION_MANIFEST.csv`.

**To resolve:** identify and port the WorldCover fetch/tiling script (or write a `workflows/fetch_worldcover.py`
against the public ESA WorldCover STAC/S3 endpoint) as Phase 6 work.

## 8. FABDEM licence compatibility with an open release

`spatial/p52a_processing_frames_qa.py` optionally reads a FABDEM raster (visualization-only, guarded by
`if p.exists()`; see `manifests/external.csv`). FABDEM's publisher licence is CC BY-NC-SA 4.0 — the NC clause has
not been checked against floodstate-eo's own release licence (`LICENSE` at repo root, not read as part of this
task). Not blocking (the dependency is optional and not required for the repository to function), but must be
resolved — verify or drop the FABDEM overlay — before any public/Zenodo release that bundles this figure.
