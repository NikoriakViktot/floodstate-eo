# Plan: migrating the zone spectral stacks (p25) from SWOT-DNIPRO into floodstate-eo

Status: **PLAN, not started** (2026-10-02). Copying code from SWOT-DNIPRO needs the maintainer's explicit go-ahead (CLAUDE.md);
nothing below has been copied yet. The 2026-10-02 extension of the stacks (`workflows/m6/p25x_zone_stack_extension.py`) ran
SWOT-DNIPRO's frozen script unchanged from its own environment; this plan replaces that arrangement.

## Why

Every per-date index map, k10e class map and 20 m Sentinel-2 water mask of the four zones (`BULK/zone_spectral/<ZONE>/`, 2017-2026)
comes from `SWOT-DNIPRO/scripts/p25_zone_spectral_stacks.py`. floodstate-eo reads those files (p95h -> T23-T25, p102 RF by date,
p104 inventory, the dashboard) but cannot produce them: a new date needs the sibling repository, its Python environment, its tables
(p10 scene manifests, `water_mask_summary.csv`) and run-time patching (p25x). The regime composites p60 reads
(`SWOT-DNIPRO/outputs/rasters/zone<N>/zone<N>_water_frac_PRE_BREACH_20m.tif`) live there too.

## What p25 consists of, and where each piece stands

| piece | in SWOT-DNIPRO | in floodstate-eo today | action |
|---|---|---|---|
| science: BOA offset, 7 indices, valid mask, frozen water rule, k10e classes, mosaic onto a grid, writers | `src/swot_dnipro/sentinel_preprocess.py` | migrated: `src/floodstate_eo/optical/sentinel_preprocess.py` (copy of f3e3e1a, manifest row 22; import block and `zone_grid` lookup changed) | none; the logic differs from the sibling HEAD only in comments (checked 2026-10-02); neither the engine nor p25 changed after f3e3e1a |
| water rule | `src/swot_dnipro/watermask.py` | migrated: `optical/watermask.py` | none |
| zone grid | `spatial_domains.build_grid` + `data/processed/domains/analysis_zones_utm.geojson` | `spatial/domains.build_grid` migrated; the four zone polygons still read from the sibling (UNRESOLVED #3) | vendor the four polygons as one small GeoJSON under `case_studies/kakhovka_2023/config/` with its sha256 |
| driver: scene plan, per-date processing, CACHED skip, composites, CLI | `scripts/p25_zone_spectral_stacks.py` | **not migrated** | split (below) |
| scene lists | `outputs/tables/p10_zone_{2,3,4}_*_s2_manifest.csv` (+ `_freeze.json`), `outputs/tables/water_mask_summary.csv` (ZONE_1 'frag'), the eastern-tile enumeration (ZONE_1 'all') | not migrated; p25x adds dates on the command line | one manifest `case_studies/kakhovka_2023/manifests/s2_zone_stack_dates.csv` (zone, date, tiles, store, source = p10 / water_mask_summary / all / p25x), generated once from those tables and `tables/p25x_zone_stack_extension.csv` |
| SAFE stores | hard-coded `SAFE_DIRS` (two in the bulk root, one in the sibling's `data/raw`) + p25x's `sentinel_event_2023` | - | `sensors.yaml: s2_safe_stores` (ordered: first store wins) |
| scene filters | 200 MB (manifest zones), 50 MB (eastern tiles): orbit-edge slivers | - | `sensors.yaml`, with the reason; 2023-07-31 and 2024-05-25 stay excluded unless the maintainer lowers the filter |
| regimes | PRE_BREACH < 2023-06-06 <= BREACH_DRAWDOWN < 2023-09-01 <= POST_BREACH | UNRESOLVED #6 (three window variants) | `temporal_windows.yaml: regimes`, documented, not reconciled with PRE/EVENT/TRACE (a science decision) |
| per-date outputs | `BULK/zone_spectral/<ZONE>/<date>_{indices,class,water3,scl}.tif` | read by p95h, p102, p104, p98 | unchanged path and names; the migrated producer writes the same files |
| regime composites | `SWOT-DNIPRO/outputs/rasters/zone<N>/` (frozen; p60 reads PRE_BREACH water_frac) | read by p60 | stay frozen in the sibling; the migrated driver builds composites only on request and only into `BULK/zone_spectral/_composites/`, never over the frozen ones |

## Steps

0. **Go-ahead** from the maintainer (the copy policy), and the choice of the commit to copy from (`f3e3e1a`, the frozen source of
   this repository; p25 is identical at the sibling HEAD).
1. **Reference fingerprints first.** sha256 of every existing `zone_spectral` file (BULK) and of the sibling's regime composites ->
   `provenance/zone_spectral_sha256.csv`. Values are computed, never typed (`TBD` where a file is unreadable).
2. **Copy with provenance**, split by the event-agnostic gate:
   - `src/floodstate_eo/optical/zone_stacks.py` -- event-agnostic engine: `stack_date(zips, grid, out_dir, tags)` (= `process_date`
     without the plan), `regime_composites(files, grid, out_dir, regimes)` (= `composites`), `plan_from_manifest(rows, stores, filters)`
     (= `scene_plan`/`find_zip` driven by a table). No zone names, no paths: the gate test stays green and `KNOWN_EXCEPTIONS` untouched.
   - `case_studies/kakhovka_2023/workflows/optical/p25_zone_spectral_stacks.py` -- the Kakhovka driver: zones, stores, filters,
     regimes from the YAML, the date manifest of step 3; `--zone`, `--dates`, `--composites-to`, CACHED skip as before.
   - `# Provenance:` header in both (source path, f3e3e1a, copy date, manifest row, exactly what changed), rows in
     `provenance/MIGRATION_MANIFEST.csv` (source sha256, target, category CORE_LIBRARY / CASE_STUDY_DRIVER, phase 5b).
3. **Config and manifests**: the date manifest, `sensors.yaml` (stores, filters), `temporal_windows.yaml` (regimes), the zone
   polygons (step table above); `_kakhovka_legacy_config` gains nothing new.
4. **Parity gate (acceptance)**: re-stack into a temporary root two dates per zone and regime, one p25x date among them, and compare
   with the existing files -- indices, class, water3, SCL arrays identical (`np.array_equal`), same transform, CRS, nodata; tags equal
   except `producer`. Composites of ZONE_2 (the smallest) into a temporary directory against the frozen sibling composites: identical
   arrays. `tests/test_zone_stacks_parity.py` (skips without the bulk data) and a synthetic unit test of `stack_date` on a tiny fake
   L2A product for CI. Any mismatch stops the migration (a library-version drift in `mosaic_to_grid` is the likely cause).
5. **Switch**: p25x is retired (the migrated driver handles any store and date); p95h, p102, p104 and the data dictionary name the new
   producer; the sibling script stays untouched and frozen. p60 keeps reading the frozen sibling composites (re-pointing it is a
   separate decision after the parity gate).
6. **Docs**: DATA_DICTIONARY (producer), METHODS (the optical chain: stacks -> k10e / water3 -> p95h, p102), UNRESOLVED_DEPENDENCIES
   (p25 closed; #3 resolved for the zone polygons; #6 documented), NEXT_STEPS, CHANGELOG.
7. **Optional, separate**: fetching new dates (CDSE) needs `p1_targeted_fetch` (UNRESOLVED #1), not part of this plan.

## What does not change

No Paper 3 number: p95h excludes the p25x dates (`EXTENSION_DATES`), the composites p60 reads are not rebuilt, and the parity gate
requires byte-identical arrays before any consumer switches. Effort: about one working day plus the parity runs (minutes per date).
