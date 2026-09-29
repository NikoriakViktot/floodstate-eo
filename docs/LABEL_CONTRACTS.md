# Weak-label contracts of the M6 experiments: v002, v003_A and v004

Review of 2026-09-28, finding F10: the manuscript reduced the label contract to "S1 on ≥ 2 of 3 peak dates" and the
reference-water operations; the full contract also depends on the optical model M2, and the filename guard of the label
scripts did not check transitive dependencies. This document is the complete contract, taken from the code
(`workflows/m6/p77_m6_labels_v002.py`, `workflows/m6/p77d_m6_labels_v003_final.py`, `src/floodstate_eo/fusion/p65b…`,
`p67b…`, `workflows/m6/p68_threshold_uncertainty.py`), and the dependency graph down to the satellite windows.
Every label is a **weak label**: agreement with it is weak-label agreement, never an independent accuracy.

## 1. Inputs and windows

| input | producer | content | window / dates |
|---|---|---|---|
| S1 dark-water per scene | S1 cache (p0* / p58) | water and valid masks per acquisition, 20 m | June 2023 scenes; peak dates 06-09, 06-13, 06-14; May 2023 (04-15 … 05-31); 06-01 / 06-02 |
| `labels.tif` (p60) | `p60_reference_labels.py` | band 1 p60 label, band 3 `n_pos_peak`, band 4 `n_post_obs`, band 8 `pre_water_frac` | S1 peak dates; pre-breach S1 events; pre-breach S2 water frequency |
| optical composites | `optical/p54b_frame_composites_10m.py` | 8 indices (NDVI, NDWI, MNDWI, NDMI, BSI, AWEIsh, NDTI, NDBI): median/min/max per window, TRACE median, signed changes, observation counts | **PRE** 2022-01-01 … 2023-06-05; **EVENT** 2023-06-07 … 2023-07-31; **TRACE** 2023-08-01 … 2023-11-30 (post-event) |
| M2 score `cand_score*.tif` | `fusion/p67b_production_candidate.py` | random-forest discrimination score (not a probability), 10 m | features from the composites; trained on the p60 weak labels of B1+B2 |
| M2 masks `flood_central*.tif`, `flood_possible*.tif` | `m6/p68_threshold_uncertainty.py` | score ≥ T50 (median of the five PRE_ALL/BLOCK outer-fold thresholds) / score ≥ the smallest of them | thresholds from the nested spatial CV of `fusion/p65b` |

**M2 is itself trained on S1-derived labels (p60).** The optical "second opinion" in the labels is therefore not
independent of S1: M2 learned to reproduce an S1 rule from optical features.

## 2. v002 (`m6_labels_v002.tif`, band 1) — built 2026-09-23; the supervision of the v1 arms

`m2` code: 255 no optical prediction support (either mask nodata); 0 flood at no threshold of the envelope (`flood_possible = 0`);
1 flood only at permissive thresholds (`flood_possible = 1`, `flood_central = 0`); 2 flood at T50 (`flood_central = 1`).
`s1w` = S1 water AND valid on any of the three peak dates.

| label | condition (evaluated in this order; later rows override) |
|---|---|
| NON_FLOOD 0 | p60 label = 0 (dry in every observed post-breach S1 event, ≥ 6 observed) AND `m2` ∈ {0, 255} |
| FLOOD 1 | p60 label = 1 (S1 water on ≥ 2 of 3 peak dates AND pre-breach land: S1 dry in every observed pre-breach event, pre-breach S2 water frequency < 20 %) AND `s1w` AND `m2` = 2 |
| IGNORE 255 (DISPUTED) | `s1w` AND optical support AND `m2` ≠ 2 — the S1 water that M2 does not call at T50 |
| IGNORE 255 | everything else |

## 3. v003_A (`m6_labels_v003_A.tif`, band 1) — frozen 2026-09-25 (`tables/m6_labels_v003_A_FROZEN.json`)

Reference state from **May 2023 S1 only** (scene QA A admits GOOD and MARGINAL scenes): REFERENCE_WATER if anchored,
≥ 3 admitted valid dates, ≥ 2 water dates and water fraction ≥ 0.50; LAND if anchored, ≥ 3 valid dates and ≤ 1 water date;
otherwise UNKNOWN (reasons: insufficient May support, mixed evidence, extrapolated, unobserved). `w_pre_state` from S1
06-01/06-02: 0 dry on every valid date, 1 water on any valid date, 255 unobserved.

| quantity | rule |
|---|---|
| event water 0 | v002 = NON_FLOOD |
| event water 1 (overrides) | `n_pos_peak` ≥ 2 AND (M2 `flood_central` = 1 OR reference state = REFERENCE_WATER) |
| LAND 0 | event water = 0 AND reference state = LAND |
| REFERENCE_WATER 2 | reference state = REFERENCE_WATER AND not EVENT_FLOOD |
| EVENT_FLOOD 1 (overrides) | event water = 1 AND `w_pre_state` = 0 AND v002 = FLOOD |
| UNKNOWN 255 | everything else |

Training map (`p86`): EVENT_FLOOD → 1; LAND and REFERENCE_WATER → 0; UNKNOWN → 255 (ignored).
v003_A **inherits v002** (FLOOD and NON_FLOOD) and reads M2 `flood_central` a second time (event water).

## 4. The transitive dependency on TRACE (review F10, established 2026-09-29)

The v002 contract lists TRACE as FORBIDDEN, and the scripts enforce it on file names. The M2 behind `flood_central`
and `flood_possible`, however, was fit on 84 features (`tables/p65a_feature_manifest.csv`, sha256 `35f43a21…6faa`,
identical to the hash recorded in both production manifests), and **17 of them come from the post-event TRACE window
(2023-08-01 … 11-30)**: the eight `*_trace_med`, the eight `*_d_trace` and `n_obs_trace`; prediction validity also
accepted TRACE observations in place of EVENT ones. v002 and v003_A therefore depend on TRACE evidence through M2.
The operating thresholds were, in addition, calibrated on in-sample scores (F09).

## 5. v004 (`m6_labels_v004.tif`) — the v003_A rule on the corrected M2 (maintainer decision 2026-09-29); frozen 2026-09-29 (`tables/m6_labels_v004_FROZEN.json`)

Identical rules to §2–§3, with M2 replaced by `M2_PRODUCTION_CANDIDATE_CORRECTED10M_NOTRACE`:

- features: the 67 PRE and EVENT features (`tables/p67b_features_notrace.csv`; no TRACE feature, tested);
- prediction validity: PRE observations AND EVENT observations (TRACE no longer substitutes);
- hyperparameters: best median inner AP of the equally restricted nested CV (`p65b_m2_tuning_notrace.csv`);
- thresholds: T50 and the envelope from **inner out-of-fold** scores of the PRE_ALL/BLOCK outer folds (F09;
  `p65b_m2_folds_notrace.csv`, `p68_threshold_registry_notrace.csv`);
- the v002 rule on this M2 is written as `m6_labels_v002_notrace.tif` and feeds v004 exactly as v002 feeds v003_A;
- no label step reads a TEST prediction (the pre-registered U0d TEST look of v003 is not run for v004, F11).

Built and frozen 2026-09-29: production M2 threshold T50 = 0.2661 (envelope 0.2167 … 0.3924); a clean-tree rebuild at e1fad3e
reproduced both versions bit for bit (the reproducibility gate of the freeze record). What changed against v003_A (T02, T02d):
EVENT_FLOOD B1 128.9 → 141.9 km², B2 57.5 → 75.2 km² (from UNKNOWN and a little from REFERENCE_WATER; < 0.1 km² leaves it), LAND
−2 to −3 % (to UNKNOWN), REFERENCE_WATER unchanged; v002 DISPUTED B1 285.8 → 122.9, B2 337.6 → 100.4 km². Without TRACE the M2
scores pre-event open water as flood-like (outside its training domain); the rules keep it out of FLOOD (p60 pre-breach land)
and out of NON_FLOOD / LAND, so the labels are unaffected — the M2 masks themselves must not be read as a flood map there.

v002 and v003_A stay frozen as history; every arm trained on them keeps its label version in its run name.

## 6. Dependency graph

```
S1 June scenes ─┬─> p60 labels.tif ──────────────┬──────────────> v002 ──> v003_A / v004
                │        │ (weak training labels) │                 ▲          ▲
                │        ▼                        │                 │          │
optical PRE ────┼─> p54b composites ─> M2 (p65b nested CV, p67b fit) ─> p68 masks (T50, envelope)
optical EVENT ──┤                         ▲
optical TRACE ──┘ (original M2 only; not in the v004 M2)
S1 May scenes ──> reference state ──────────────────────────────────────> v003_A / v004
S1 06-01/06-02 ─> w_pre_state ──────────────────────────────────────────> v003_A / v004
```

Machine-readable lineage per label version: `tables/m6_label_lineage.csv` (`workflows/m6/p77f_label_lineage.py`).
