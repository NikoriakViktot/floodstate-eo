# Where floodstate-eo stands, and what's next

Written 2026-09-23, at the end of the session that created this repository's first real commit. This is
the "what stage are we at, what do we do when we come back" record — read this before doing anything else
in this repo.

## UPDATE 2026-09-23 (late) — read this first; it supersedes the S1-coherence and ordering parts below

**SWOT-DNIPRO no longer owns any of this chain.** Its commit `9419ea3` removed the flood-state branch; everything
below runs from floodstate-eo. Source of truth for anything missing: SWOT-DNIPRO commit `f3e3e1a`.

- **Coherence (p80–p83): CLOSED — `OPTIONAL_LATER_ABLATION` (U6).** Two p82 gate attempts on orbit 65 pair 1 both hit
  `Java heap space` at -Xmx16G under a 24 GB WSL2 cap (single graph; then staged one-JVM-per-subswath, still OOM
  inside IW2 ESD, ~17 h/pair projected). Stopped; failure products kept, renamed `FAILED_*`, with
  `/home/niko/data_s1_coh/_stage/orb65/2023-04-26_2023-05-08/FAILED_README.txt`. p82 now writes transactionally
  (validate → `.ok.json` → atomic rename); a `.tif` without a matching `.ok.json` is refused. Do not restart p82,
  fetch orbits 14/87/138, or tune `-q`, without an explicit decision to reopen coherence.
- **M6 recovered** into `case_studies/kakhovka_2023/workflows/m6/` (13 scripts, provenance headers, rows in
  `provenance/MIGRATION_MANIFEST.csv` with `m6_status`/`reason`), runs into `case_studies/kakhovka_2023/runs/`
  (`.pt` git-ignored). Status: `U0_B2` = SUPERSEDED (linear gamma0), **`U0_B2_CORRECTED` = ACTIVE_REFERENCE (frozen,
  do not retrain)**, `U0b_B2` = CONTAMINATED (do not re-run as an ablation). Torch deps: `pip install -e ".[m6]"`.
- **U0_B2_CORRECTED diagnostics** (`workflows/m6/p75d_u0_inference_diagnostics.py` → `runs/U0_B2_CORRECTED/diagnostics/`):
  reproduction gate EXACT (TP/FP/FN/TN identical to the frozen numbers). Report every number as *agreement with
  held-out weak reference labels*, never flood-mapping accuracy. Test WETLAND F1 0.979, VEG_AGRI 0.393, BUILT_UP
  P 0.059; 268 isolated field-shaped components (25.8 km²); 44 km² predicted on PRE_EXISTING_WATER (unlabelled, so
  invisible to metrics); disputed: 110 of 394 km² ≥ 0.57 (MODEL-SUPPORTED DISPUTED CANDIDATES). Note the frozen
  patch-protocol counts include overlapping patches (stride 128), so pixels are counted several times; the
  unique-pixel full-frame TEST F1 is 0.955.
- **p71 B1 built** (`s1_change.tif`, same 15 channels/order/units/dtype/nodata as B2). B1 long cache has no recorded
  georeference; recovered and verified by content (`p71.LONG_GRID`). Event 2023-06-08 orb167_DES excluded (2 matched
  pre scenes; pooled baselines forbidden). Caveats: 16 % of B1 (980 km², west strip) has no event; B1 baselines are
  6–15 scenes vs B2's 18–23, so **z_* channels are not value-comparable across frames** (overlap Pearson z_vv_max
  0.43, medians 3.8 vs 2.5; d_* channels 0.79–0.94) — `tables/p71_B1_B2_overlap_semantics.csv`. B3 NOT built.
- **m6_labels_v002 built for B1, B2** (`workflows/m6/p77_m6_labels_v002.py`; reads only labels.tif, flood_central,
  flood_possible, per_scene_water — enforced and recorded in tags; `tests/test_m6_label_independence.py`).
  Finding: v002 differs from v001 by < 1 % (B2: +0.76 km² FLOOD, 7.1 km² NON_FLOOD→IGNORE), and BASE_CLASS still
  ranks v002 at AUC 0.927 (v001 0.923). So the old U0b problem was **not mainly construction circularity** — it is
  label-population structure: 52.6 of 57.5 km² B2 FLOOD labels are WETLAND, 4.0 km² VEG_AGRI, while NON_FLOOD is
  ~80 % VEG_AGRI. A surface-context model can learn "field ⇒ dry" from these labels regardless of how they were built.
  Any U1 claim must be made WITHIN strata (esp. VEG_AGRI), not from global F1. B1 has more flooded-field labels
  (25.7 km²) and matters for this.
- **p73 RF20** (`workflows/m6/p73_rf20_surface.py`): PRE-only S2 predictors, WorldCover 2021 target with 4-cell purity
  + PRE-S2 consistency, global 20 m grid. DEVELOPMENT status; must not enter a U-Net yet.

### DECISIONS (maintainer, 2026-09-23) — binding for the next experiments
**D1 — U1 is evaluated WITHIN strata, and B1 is mandatory.** The primary test is U0 → U1 at a fixed land-cover class:
separately for VEG_AGRI, WETLAND_REED, BUILT_UP, BARE_SAND, PRE_EXISTING_WATER (BASE_CLASS/p73 used there for
stratification only, after labels are frozen).
- VEG_AGRI primary endpoints: precision, recall, F1/IoU and FP area (km²), on two sub-populations reported
  separately: *confirmed-flooded fields* and *stably dry fields*.
- WETLAND: recall/IoU plus fragmentation (component count, largest-component share).
- Global F1 is SECONDARY. If U1 improves only global F1 and nothing inside VEG_AGRI, that is a surface-class shortcut,
  not better flood segmentation.
- Split is frozen BEFORE U1 and must put both flood-agriculture and dry-agriculture into the test geography
  (B1 carries ~25.7 km² flooded fields vs ~4 km² in B2). U0 and U1 use the same spatial blocks; comparisons use a
  paired spatial-block bootstrap CI.

**D2 — z_* channels do not enter the main cross-frame model as they are, and B2 is not impoverished.**
- `U0d` (main cross-frame SAR baseline) = d_vv / d_vh / d_vvvh channels + support channels, no z_*.
  Support channels stay (`n_valid_pre_matched`, `n_valid_event`, `n_orbits_event`) so the network sees how reliable
  each anomaly estimate is.
- `U0z` = U0d + z_vv / z_vh — an ablation on the normalisation domain shift. z_* stays only if +z improves held-out
  performance in BOTH frames AND within strata.
- Matched-depth B2 (deterministically trimming B2's baseline to B1-like 6–15 scenes and checking whether z converges
  on the overlap) is a SENSITIVITY experiment only, never the production pipeline.

**Scientific route**
```
B1+B2 m6_labels_v002
   ├── U0d = S1 d_* + support          ← main cross-frame SAR baseline
   ├── U0z = U0d + robust z_*          ← ablation on domain shift
   └── U1  = best U0 + p73 RF20        ← surface-context test
```
The U1 question: **does p73 reduce false flood on dry fields without killing recall on genuinely flooded fields in B1?**

### Ordered next steps (replaces the list at the bottom where they conflict)
1. Freeze the B1+B2 split per D1 (flood-agri and dry-agri in test geography; same blocks for every arm).
2. U0d, then U0z (D2). Evaluation harness per D1 (strata, sub-populations, FP km², paired block bootstrap).
3. p73: review CV/transfer tables (current CV is on balanced PURE pixels — optimistic); then freeze.
4. U1 = best U0 + p73. Later U2 +HAND/distance to water, U3 +S2 06-08, U4 +S2 06-18, U5 +TRACE;
   U6 +coherence only if the baseline works.
5. Independent evaluation reference: observations that took no part in label construction (none exists yet).
6. B3 p71 only after the B1 caveats above are accepted.
7. Still uncommitted from the earlier session (not part of the M6 commits): the `_kakhovka_legacy_config.py` CRS fix,
   `case_studies/kakhovka_2023/manifests/*.csv`, `provenance/UNRESOLVED_DEPENDENCIES.md` #7/#8, `CLAUDE.md`.

## Current state, precisely

- **Committed** (`86cf8a6` on `main`, local only — **not pushed** to `git@github.com:NikoriakViktot/floodstate-eo.git`):
  Migration Phase 5 ("copy canonical code with provenance headers") — 59 files. 20 Kakhovka-specific
  scripts + 8 core-library modules copied from SWOT-DNIPRO (frozen at commit
  `f3e3e1afe91902a82a73f3c09354d1f9eb847766`) with real provenance headers (source path, source commit SHA,
  sha256) and package-import fixes only — logic byte-identical to source. `config.py`/`spatial_domains.py`
  scoped-extracted into 7 YAMLs under `case_studies/kakhovka_2023/config/` plus a generic
  `spatial/domains.py`. Docs shipped: root + case-study README, `docs/METHODS.md`, `docs/DATA_DICTIONARY.md`,
  `docs/REPRODUCIBILITY.md`, a 26-section narrative notebook skeleton, `CITATION.cff`. Tests: 2 migrated +
  1 new event-agnostic grep-gate test, **13/13 passing** (verified independently in a fresh venv, not just
  the migration agent's self-report).
- **Uncommitted, in the working tree right now** (review before committing):
  - `src/floodstate_eo/_kakhovka_legacy_config.py` — a real bug fix. `load_utm('reservoir_full_pool_prebreach')`
    was silently returning an area of 2.6e-7 km² instead of ~2000 km², because the reservoir source file
    (`Kakhovka_SA_2.geojson`, CRS84/lon-lat) was being treated as already-EPSG:32636 like the zone file is.
    Fixed with CRS detection + reprojection; verified the corrected area (2174.7 km²) matches the real
    Kakhovka reservoir full-pool extent. Found by actually testing data access, not by inspection — worth
    remembering as a reason to keep testing data access, not just import success.
  - `case_studies/kakhovka_2023/manifests/{s1_scenes,s2_scenes,external}.csv` and `data/README.md` — the
    data-source registry `08_DATA_POLICY.md` called for but the code migration never produced. Built from
    real SWOT-DNIPRO tables (30 S1 SLC rows from `p80_c1_frozen_products.csv`, sha256 `TBD` — never computed
    anywhere; 44 S2 rows from `p52d_fetch_ledger*.csv` with real sha256/sizes). Found and corrected the
    pre-migration draft's dataset list along the way: Dynamic World and HAND are **not** used anywhere in
    `src/floodstate_eo/**` (dropped); ESA WorldCover 2021 turned out to be a **required, load-bearing**
    input (`surface_state/p69a_base_class.py:84`), not optional context as the draft assumed.
  - `provenance/UNRESOLVED_DEPENDENCIES.md` — two new entries (#7, #8): a whole S1 GRD/RTC NPZ-cache input
    that `sar/p71_s1_event_change.py` reads has no fetch code anywhere in this repo (the code that built it,
    `p0o`/`p0v`/`p0w`, was legacy and never migrated); FABDEM's licence (CC BY-NC-SA) may conflict with
    redistributing anything derived from it.

  **First thing to do next session**: review these three diffs, then commit them (they're good — reviewed
  once already this session — but the review was mine, not yet a second pair of eyes) and decide on `git push`.

## What Phase 5 did NOT do (by design — read before assuming code works end-to-end)

`tests/test_event_agnostic_gate.py::KNOWN_EXCEPTIONS` lists 23 files under `src/floodstate_eo/**` that are
still Kakhovka-specific — the 20 migrated scripts plus `canonical_grid.py`, `optical_catalogue.py`, and the
new `_kakhovka_legacy_config.py` shim. That shim exists **only** because Phase 6 ("replace hard-coding with
config") hasn't run: every migrated script still calls `CFG.TABLES`, `CFG.BULK_ROOT`, `CFG.BREACH_DATE`, etc.
instead of reading the YAMLs in `case_studies/kakhovka_2023/config/`. Until Phase 6 runs, this package is a
relocated copy of SWOT-DNIPRO's Kakhovka branch with clean provenance — not yet a reusable, event-agnostic
framework. That's the honest state; `provenance/KNOWN_GATE_EXCEPTIONS.md` explains each file.

Two unreconciled flood-state "bridges" exist and neither is canonical: the legacy `p51_rf_flood_optical.py`
RF classifier (20 m zone grid — deliberately **not migrated**, still only in SWOT-DNIPRO) and the newer
`fusion/p65b_m2_spatial_cv.py` → `fusion/p66_production_m2.py` / `fusion/p67b_production_candidate.py` M2
chain feeding `surface_state/p69a_base_class.py` → `fusion/p69b_event_association.py` (migrated, on the
canonical 10 m B1/B2/B3 frames, but `p66_production_m2.py` and `p67b_production_candidate.py` are
themselves two different fits of the same model, not reconciled to one canonical M2 output — see
`docs/DATA_DICTIONARY.md` row for `cand_score.tif`/`flood_score.tif`). Migrating the code did not resolve
which bridge is real; that's a science decision, not a file-organisation one.

M0–M5 (the flood-state class matrix referenced in `03_SCIENTIFIC_CORE.md`) is **not defined anywhere** —
still only mentioned as future work. No script here computes FLOOD_STATE, URBAN_SCORE, UNCERTAINTY, or
FINAL_FLOOD_MASK; `docs/DATA_DICTIONARY.md` marks all four `PROPOSED / NOT YET CANONICAL`.

The SWOT-DNIPRO source of `sar/p82_coherence_graph.py` (identical code here) is currently **blocked**: two
attempts at orbit 65 pair 1 both failed with `Java heap space` inside SNAP's ESD/Back-Geocoding stage, even
after retuning `-q`/`-c`/`-x`. Root cause traced to WSL2 capping this host's VM at ~15 GB against the
Windows host's ~32 GB (no `.wslconfig` override). Whoever runs this script from floodstate-eo will hit the
identical failure until that's fixed — raising the WSL2 memory cap (`.wslconfig`, `memory=24GB`+, then
`wsl --shutdown`) is the real fix, not a code change. 0 of the 4 orbits' coherence pairs have a valid output;
only orbit 65's SLC data has even been fetched.

## Ordered next steps (migration phases from the original audit, `07_MIGRATION_PLAN.md`)

1. **Now**: review + commit the three pending diffs above (CRS fix, data registry, unresolved-deps update).
2. **Phase 6 — replace hard-coding with config.** Rewire the 20 migrated scripts to read
   `case_studies/kakhovka_2023/config/*.yaml` instead of `_kakhovka_legacy_config.CFG`, one script at a
   time; `KNOWN_EXCEPTIONS` in the gate test shrinks as each one is done (that shrinkage is the acceptance
   criterion — don't remove an entry without actually fixing the file, the companion test
   `test_known_exceptions_still_exist_and_still_violate` will catch that). Also resolve: the two RNG seeds
   (`model.yaml`'s `seed_note`), the three temporal-window variants, and vendor or fetch the zone/reservoir
   geometries properly instead of reading them from sibling-repo paths (`provenance/UNRESOLVED_DEPENDENCIES.md` #3).
3. **Reconcile the two flood-state bridges** (p51 legacy vs. M2) — a science decision, likely needs
   `outputs/planning/19_P51_METHODOLOGY_REWRITE.md`'s open items resolved first (in SWOT-DNIPRO, since p51
   itself stayed there). This blocks Phase 9.
4. ~~Unblock the S1 coherence chain~~ — **CLOSED 2026-09-23** (see the update at the top): coherence is an
   optional later ablation, not on the critical path.
5. **Phase 7 — tests.** Currently only unit-level (`test_composites.py`) + the gate test. No integration or
   regression tests exist yet (`docs/DATA_DICTIONARY.md`'s testing-strategy note).
6. **Phase 8/9 — minimal case, then canonical B1/B2/B3 reproduction.** Actually run the pipeline end-to-end
   from this repo on real data and confirm outputs match SWOT-DNIPRO's (the invariants in
   `provenance/` / the original audit's `17_MIGRATION_INVARIANTS.md`).
7. **Phase 10/11 — fill in the notebook and docs** with real results once Phase 9 produces them (right now
   the notebook's later sections are placeholder markdown cells by design).
8. **Phase 12-15** (publication bundle, Zenodo metadata, GeoHydroAI integration, public release) — not
   started, don't start before 6-9 are done.
9. **`git push`** — only once the maintainer has reviewed at least the Phase-5 commit and decided the repo
   is ready to be visible on GitHub (currently local-only).
