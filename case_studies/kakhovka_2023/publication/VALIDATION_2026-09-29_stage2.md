# Validation of the Stage-2 response to the code review of 2026-09-28 (independence and ML: F09, F10, F08, F11, F12)

Branch `review-2026-09-28-stage2` (from the frozen Stage 1, 7795cad). Code of F09/F10/F11/F08: 214bf93. Order of work as decided by
the maintainer: F09 → F10 → F08 → F11 → F12. Every number below was produced on this branch and is read from the committed
tables named next to it.

## F09 — M2 operating threshold from inner out-of-fold scores (T02c; `p65b_m2_*_notrace.csv`)

- Nested spatial CV of the corrected M2 (67 PRE + EVENT features; 5 km blocks, 5 outer × 3 inner folds, 36 hyperparameter
  combinations, PRE_ALL baseline; 2 h 06 min, 10.5 GB). For each outer fold the threshold at the target recall 0.90 now comes
  from the pooled inner out-of-fold scores (three inner block folds; fit and calibration cells disjoint, asserted); the
  former rule — the refit forest scoring cells of its own fit set — is kept per fold as `threshold_insample_superseded`.
- **Block regime:** outer AP 0.906–0.957 (pooled 0.924); median threshold **0.266 (out-of-fold) vs 0.446 (in-sample)**; outer
  test recall at those thresholds **0.928 vs 0.860** (target 0.90): the in-sample threshold undershoots the target on four
  of the five folds (0.784–0.906), the out-of-fold one meets it on four (0.876–0.942).
- **Buffered regime (3.5 km):** pooled AP 0.830; median threshold 0.209 vs 0.458; test recall 0.808 vs 0.575 — with the buffer
  even the out-of-fold threshold falls short (the inner folds are not buffered), the in-sample one by far.
- Tests `tests/test_p65b_threshold_oof.py` (disjoint fit and calibration cells, whole blocks, an in-sample threshold is higher).

## F10 — M2 without the post-event TRACE window; labels v002_notrace and v004 (T02, T02b, T02d; lineage)

- **Production model** `M2_PRODUCTION_CANDIDATE_CORRECTED10M_NOTRACE` (p67b `--exclude trace`): 67 of the 84 features (the 17
  TRACE features dropped, `p67b_features_notrace.csv`); hyperparameters by the best median inner AP of the equally restricted
  CV (300 trees, min_samples_leaf 5, max_features 0.5; median inner AP 0.891); state threshold T50 = 0.2661 (median of the
  five block out-of-fold thresholds; the original model used 0.5358 from in-sample thresholds). Population 22 174 408 cells,
  0 duplicates; overlap QA of score, state and validity: 0 mismatches on all three frame pairs → PASS.
- **Masks (p68 `--tag _notrace`):** envelope 0.2167 … 0.3924 around T50, overlap QA 0 mismatches.
- **Labels:** v002_notrace (the v002 rule) and v004 (the v003_A rule) on this M2 — T02 / T02d:
  | frame | v003_A EVENT_FLOOD → v004 | LAND | REFERENCE_WATER | v002 DISPUTED → v002_notrace |
  |---|---|---|---|---|
  | B1 | 128.9 → 141.9 km² (+12.4 from UNKNOWN, +0.7 from REFERENCE_WATER) | 1544.3 → 1513.7 (30.6 to UNKNOWN) | 258.5 → 257.8 | 285.8 → 122.9 |
  | B2 | 57.5 → 75.2 km² (+15.7 from UNKNOWN, +2.0 from REFERENCE_WATER) | 663.1 → 642.5 (20.6 to UNKNOWN) | 283.9 → 281.9 | 337.6 → 100.4 |
  Almost nothing leaves EVENT_FLOOD (< 0.1 km² per frame): v004 EVENT_FLOOD contains v003_A EVENT_FLOOD. The S1 water that the
  original M2 refused at its in-sample T50 (DISPUTED) is largely called now; LAND shrinks by 2–3 % because more cells reach the
  permissive end of the envelope (NON_FLOOD needs M2 = no flood at any threshold of the envelope).
- **Lineage (`tables/m6_label_lineage.csv`, test `tests/test_m6_label_lineage.py`):** v002 and v003_A depend on TRACE through M2
  (84 features, 17 TRACE); v002_notrace and v004 do not (67 features, 0 TRACE; windows PRE 2022-01-01..2023-06-05 and EVENT
  2023-06-07..07-31 only); no v004 label step read a TEST prediction.
- **Caveat found on the way (M2 as a stand-alone map, not the labels):** without TRACE the corrected M2 scores pre-event open
  water as flood-like — 98 % of the cells with PRE MNDWI > 0 score ≥ 0.5 in B2 and B3 (83 % in B1); in the unseen frame B3
  (estuary and sea) 23.9 % of all cells score ≥ 0.5 against 1.3 % for the original model. Permanent water lies outside M2's
  training domain (p60 FLOOD needs pre-breach land, NON_FLOOD dry post-breach S1 events), so the scores there are
  extrapolation; the TRACE window (water still present in autumn) had separated it. The labels are guarded (FLOOD needs p60 =
  pre-breach land; permanent water is IGNORE / UNKNOWN in every version); B3 enters no label, arm or result of the paper. The
  M2 masks must not be shown as a flood map on permanent water.

- **Freeze of v004 (and the v002_notrace rule behind it):** reproducibility gate PASS — from the clean tracked tree at e1fad3e,
  p77 `--m2-tag _notrace` and p77d `--variant A --m2-tag _notrace` rebuilt `m6_labels_v002_notrace.tif` and `m6_labels_v004.tif`
  (B1, B2) bitwise identical to the rasters the arms were trained on; freeze record `tables/m6_labels_v004_FROZEN.json` written
  from a clean tree (freeze commit c15b98f, `freeze_tree_dirty_tracked: false`).

## F08 — RF20 rev 2 (T09, T10, T10b–d, FigS04; `tables/p73_rf20_rev2_qa/QA_VERDICT.md`)

- Global UTM block ids; B2 owns the B1/B2 overlap (3 093 025 B1 target cells dropped; unique physical cells asserted); CV with
  and without a 3.5 km buffer (32–49 % of the training cells kept per buffered fold); transfers outside the overlap. 15 min,
  9.6 GB; code and imports identical to 214bf93.
- Block CV macro F1 0.941 / OA 0.938 (rev 1: 0.943 / 0.940); buffered 0.929 / 0.926. **The rev-1 B1 → B2 transfer was inflated
  by the overlap: 0.904 → 0.848 outside it** (B2 → B1 0.932 → 0.907).
- The map hardly changes: 96.9 % (B1) / 96.8 % (B2) of cells keep their class, 99.6 % / 99.5 % outside UNCERTAIN; class areas
  ±12.5 km²; SHRUB/OTHER never predicted (the U1 encoding loses nothing). T14 (p95d on rev 2): category areas unchanged, RF20
  splits ≤ 4.7 km². Reproducibility gate of rev 2: pending (after the U-Net arms, which read the products).

## F11 and the retrained arms — v004 × 3 seeds, U2 on v002_notrace × 3 seeds (T04, T05, T05s, T06, T06s, T07, T07b, T20)

- 15 arms (U0d, U2, U2b, U1 on v004; U2 on v002_notrace; seeds 20260923 / 20261001 / 20261002) + U2 v004 on the 7.5 / 15 / 20 km
  splits; ~4 min per arm on the A4000; 16 GB RAM peak per arm; RF20 rev 2 as U1 input and evaluation strata; smoke run first
  (stops before TEST); no failed run. Every run keeps its own frozen validation threshold (0.05–0.71 across seeds: the
  thresholds of a Dice + BCE network are not calibrated).
- **Seed noise** (T05s): global F1 per arm varies by 0.004 (U2) to 0.059 (U2b); the unlabelled-cropland burden by 1.7 km² (U2b),
  4.1 (U2), 9.0 (U0d), 20.8 (U1) and 23.5 km² (U2 on v002_notrace) between seeds of the same arm.
- **Paired effects across seeds** (T06s; median [95 %] per seed):
  | comparison | endpoint | seed 1 | seed 2 | seed 3 | verdict |
  |---|---|---|---|---|---|
  | U0d → U2 (+HAND) | unlabelled-cropland burden, km² | +0.98 [−0.58, 3.03] | +7.62 [2.49, 14.86] | −3.84 [−9.39, 0.32] | not robust (the v002 arm: −9.6 [−14.8, −5.1]) |
  | U0d → U1 (+RF20) | unlabelled-cropland burden, km² | +6.8 [1.3, 16.2] | +27.3 [12.3, 47.7] | +21.1 [7.1, 42.8] | higher in 3/3 |
  | U0d → U1 (+RF20) | built-up FP, km² | −0.23 [−0.55, −0.02] | −0.34 [−0.85, −0.03] | −0.36 [−0.94, 0.00] | lower, same sign 3/3 (v002: −0.32) |
  | U2 → U2b (+W_pre, diagnostic) | unlabelled-cropland burden, km² | −6.0 [−11.6, −1.2] | −8.6 [−17.2, −2.9] | −7.5 [−15.4, −2.3] | lower in 3/3 |
- **Label effect on the corrected M2** (T07b, v004 ontology, U2 on v002_notrace → v004 at fixed inputs): flood on
  REFERENCE_WATER −13.8 [−35.3, −1.4], −25.6 [−62.6, −3.7], −48.8 [−111.3, −11.1] km² (3/3 exclude zero; the v002 → v003_A arm:
  −13.4); EVENT_FLOOD recall −0.034 [−0.048, −0.009], −0.002 [−0.022, 0.009], −0.006 [−0.019, 0.013] (resolved in 1/3).
  W_pre on REFERENCE_WATER: +7.4 [−1.0, 23.7] (n.s.; the U2b seed with threshold 0.10), −0.73 [−1.96, −0.08], −0.77 [−1.98,
  −0.06] km² (v003_A arm: −0.62).
- **Mapped area** (p92, dam → liman, B1 ∪ B2): U2 v004 309 / 335 / 349 km² (v003_A: 394), U2b v004 389 / 338 / 307 km²
  (v003_A: 275) — a single seed does not fix the mapped area to better than ~±40 km². The old rows of p92 reproduce exactly.
- **Claims:** C09 (label effect) holds on the corrected labels for the reference-water artefact; C10 (HAND lowers the cropland
  burden) does not replicate; C11 (W_pre) holds in 2/3 seeds and stays non-independent — C09–C11 are marked "re-tested,
  statement pending review" in the evidence matrix; their statements and the §4.9 text are the maintainer's decision.
- Block-size sensitivity on v004 (T20, FigS05): the same picture as v003_A (F1 0.94 / 0.93 / 0.93 / 0.89 at 7.5 / 10 / 15 /
  20 km; the 15 km split has too few blocks for a usable interval).

## F12 — ICESat-2 check: pass hold-out of the class bias (T15, T15b, T15c)

- The category mask (`cat[v & new & ~s1] = 4`, assertion `cat[~v] == 0`) and the raw / corrected residuals were fixed in
  Stage 1; the main check table `p95c_icesat2_check_0609.csv` is **byte-identical** after the Stage-2 re-run.
- **In-sample equals p95j (asserted):** the class biases re-estimated from the calibration population (p95j: FABDEM cells,
  WorldCover ≠ water, per zone, deduplicated by date and position; 630 446 points on 98 passes) with the p95 rule reproduce
  `p95j_terrain_residual_stats.csv` to the millimetre; applied to the 222 410 FABDEM check segments (83 passes) they reproduce
  the corrected terrain raster to < 1 cm on **every** segment.
- **Observation (no effect on results):** the WorldCover frames sit half a cell (10 m) off the terrain grid; p95 gives a terrain
  cell the WorldCover class by nearest-neighbour resampling, which differs from the class of the pixel holding an ICESat-2
  segment for 15 447 of the 222 410 check segments (6.9 %, class edges). The hold-out uses the class p95 actually applied.
- **Independent units:** passes (acquisition days), not segments — e.g. S1-only ≥ 2 m: 3 205 segments on 17 passes (delta),
  1 665 on 59 passes (floodway).
- **Hold-out (T15b):** the class bias re-estimated without the checked passes (p95 rule) moves the corrected median of the
  S1-only ≥ 2 m category by ≤ 0.035 m (any scheme); ≤ 2 segments per zone change side of the 2 m split (epoch scheme only).
  Over all categories: one pass out ≤ 0.023 m, five folds of passes ≤ 0.041 m, the two epochs either side of the breach
  ≤ 0.237 m (delta, S1-only < 2 m).
- **Bias stability (T15c):** the delta class biases rest on few passes (19 in total; 6–7 before the breach): the delta wetland
  bias is +0.22 m from the pre-breach passes and +0.59 m from the post-breach passes (in-sample +0.52 m); floodway classes
  shift ≤ 0.08 m between epochs. The class bias is a fixed correction of the reconstruction; this epoch dependence is not
  propagated into the Monte-Carlo ensemble (stated in §4.4).
- Tests: `tests/test_p95c_bias_holdout.py` (4: a held-out pass never calibrates its own check and is checked once per scheme;
  epochs split at the breach over all passes; the class rule is the p95 rule; an anomalous pass cannot correct itself —
  in-sample shift 0.024 m vs 0.003 m held out).

## Table defect found and fixed on the way (T09, claim C12)

- T09 `MACRO_MEAN` averaged the per-class rows **and** the p73 `MACRO` and `OVERALL_ACCURACY` rows: n was counted three times
  (1 177 260 instead of 392 420 CV samples) and the B1→B2 transfer macro F1 read 0.906 instead of 0.904. Fixed (mean over the
  classes only; test `test_t09_macro_mean_is_over_the_classes_only`); C12 n and value corrected by `fill_evidence`.
