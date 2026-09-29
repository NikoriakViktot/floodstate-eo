# Response to the scientific / code review of 2026-09-28 (F01–F20) — action ledger

Review: `case_studies/kakhovka_2023/reviews/2026-09-28_scientific_code_review.md` (commit `06441cf`, major revision).
Literature notes on the same findings: `case_studies/kakhovka_2023/reviews/2026-09-29_literature_notes.md`.
Every finding was first checked against the code at `06441cf`; all of F01–F19 were confirmed (F20 from the draw table).

**Scope decided by the maintainer (2026-09-29).** Stage 1 (this pass) = the uncertainty engine of the terrain reconstruction
(F01–F07, F20; the F12 mask; the F16 gauge path), recomputed end to end, then a STOP for review of the new numbers.
Stage 2 = independence and ML (F09 → labels v004 → arms retrained; F10; F08 with the RF20 production refit and a new
freeze; F11; the rest of F12). Stage 3 = balance, figures, release (F13–F19) and the text pass (novelty / introduction after
the literature notes). Conceptual corrections of 2026-09-29: FABDEM is a bare-earth DTM, the terrain layer is a seamless
terrain–bed elevation model (FABDEM outside the surveyed channel, bed inside), the WorldCover class median is a *residual*
terrain-elevation bias (not a canopy correction), FABDEM statistics apply only where the source is FABDEM, every height is in
one vertical frame (EVRF2019), and no new physics (fill–spill–merge, flow-tub, Manning, SWE) enters while answering the review.

Status: **done** = implemented, tested and recomputed; **stage 2 / stage 3** = planned, decided; **text** = the text pass.

| # | Finding | Action | Status | Evidence |
|---|---|---|---|---|
| F01 | MC draws regenerated per zone; no shared realization | p95e rev 2: the draw loop is outermost; ONE terrain field over the union mosaic and ONE water-surface realization over all nodes and days per draw; the baseline rebuilt with the same realization | done | `workflows/m6/p95e_uncertainty_mc.py` (`run_draw`), `tests/test_p95e_contract.py` (a) |
| F02 | bilinear-zoomed white noise, std ≈ 0.66, arbitrary 500 m | `floodstate_eo.terrain.fields.FieldSynthesizer`: FFT field with UNIT marginal variance and a stated covariance; the covariance (nugget + nested exponentials) fitted to the standardized FABDEM − ICESat-2 residuals of same-date pairs (p95j, robust estimator, Cressie WLS); class NMAD as the marginal scale on FABDEM cells only | done | `tests/test_terrain_fields.py`, `workflows/m6/p95j_terrain_variogram.py`, T18b/T18c, FigS11 |
| F03 | closure added twice under the far gauge cap | `WSE.field` takes every stochastic term through the perturbed node heights (`Hmat`) and adds nothing else; the gauge row carries the gauge error once (local node and far cap) | done | `tests/test_p95_wse_field.py` (+0.1 → +0.1 on an active cap) |
| F04 | total-water interval = shifted new-area interval | p95e stores potential (total), baseline, new, total and new volume per draw; T12/T12b quantiles of W_total from the total ensemble; the shift construction removed from p96 | done | `p96_paper_tables.py` (T12, T12b), `tests/test_p95e_contract.py` (c) |
| F05 | interpolation / held ends / long gaps under-described; one σ from 1-day triplets | observed / interpolated / held flags and gap length per node-day; gap-matched cross-validation (all observations closer than d removed, d = 1…8 days) → σ(gap, kind); one standard normal per node and gap run; `--max-gap-days` sensitivity; RMSE-scale ablation; support per cell (T11g) | done | T11f, T11g, T11d (`interpolation_rmse_scale`), sensitivity `_maxgap3` |
| F06 | ownership applied before connectivity | connectivity on the union mosaic (`floodstate_eo.terrain.mosaic.UnionGrid`); ownership for accounting and the per-zone rasters only; seam check against the per-zone evaluation | done | `tests/test_terrain_connectivity.py` (6 vs 3 cells), T11i (seam check: 0.0 km² difference on 7, 9, 13 June) |
| F07 | fallback without distance limit, 100 m field, seeds, 8-neighbourhood, ZONE_2 statistics on ZONE_4, "lower bound" | per-zone FABDEM-only residual table (p95j; own zone where N ≥ 500, else pooled, flagged); bed cells uncorrected and unperturbed; sensitivities 4-connectivity, main-stem seed, river-aware median, 3-day maximum gap; primary rule `connected_ceiling` as the CLI default with explicit suffixes; "lower bound" → wording in the text pass | done (code); text | T11, T12 sensitivity columns, T11h (attribution), T11g |
| F08 | RF20 blocks frame-local | `p73 --rev 2`: global UTM block IDs, B2 owns the overlap before sampling (unique cells asserted), CV with and without a 3.5 km buffer, transfers outside the overlap, production refit (rev 2 products, QA verdict); rev-2 strata / U1 input for every stage-2 arm; p95d, T09/T10/T10d, FigS04, dashboard on rev 2 | done; **rev 2 FROZEN** (clean-tree gate bitwise, acf190c) | T09: block CV macro F1 0.943 → 0.941, buffered 0.929; **transfer B1→B2 0.904 → 0.848 outside the overlap** (B2→B1 0.932 → 0.907); map 96.9 % / 96.8 % of cells unchanged; T14 splits ≤ 4.7 km² |
| F09 | M2 threshold from training data | `p65b.inner_oof_threshold`: per outer fold the target-recall threshold from pooled inner out-of-fold scores (fit and calibration disjoint, whole blocks); the in-sample rule kept per fold as `threshold_insample_superseded`; production (p67b) and masks (p68) from the corrected CV → labels **v004** → arms retrained (3 seeds) | done (arms: see F11) | T02c: block median threshold 0.266 (OOF) vs 0.446 (in-sample), outer recall 0.928 vs 0.860 (target 0.90); buffered 0.209 vs 0.458, recall 0.808 vs 0.575; `tests/test_p65b_threshold_oof.py` |
| F10 | label contract incomplete in the text; transitive dependencies | `docs/LABEL_CONTRACTS.md` truth tables; `p77f_label_lineage.py` (lineage down to the composite windows); M2 without the post-event TRACE window (maintainer, 2026-09-29) → v002_notrace and **v004**; `p77g` transitions; §3.6 in the text pass | done (text: stage 3) | `tables/m6_label_lineage.csv` (v002/v003_A: 17 TRACE features via M2; v004: 0); T02/T02d: EVENT_FLOOD B1 128.9 → 141.9, B2 57.5 → 75.2 km²; `tests/test_m6_label_lineage.py` |
| F11 | TEST reused for decisions; empty-support bootstrap | `m6_eval._m` and p90: undefined (NaN) for empty denominators, bootstraps report `n_defined`; no v004 label step reads a TEST prediction; three training seeds per arm on v004 (U0d, U2, U2b, U1) and for U2 on v002_notrace (`p86 --seed`, `p86s_seed_summary.py`); exploratory wording of TEST in the text pass | done (text: stage 3) | `tests/test_m6_eval_undefined_metrics.py`; T05s/T06s: seed range of the unlabelled-cropland burden up to 20.8 km² (U1) and 9.0 km² (U0d); the v002 HAND effect (−9.6 km²) does not replicate on v004 (1/3 seeds, signs differ) |
| F12 | terrain-only category outside the S1 footprint; not independent | **mask fixed** (`cat[v & new & ~s1] = 4`, assertion `cat[~v] == 0`); raw and corrected residuals on FABDEM cells, `n_dates`, bed segments excluded; **pass hold-out of the class bias** (stage 2): b_c re-estimated with the p95 rule without the checked passes — one pass out, five folds of passes, the two epochs either side of the breach; passes reported next to segments | done | T15 (ZONE_4 terrain-only 6764 → 4821 segments; C06 numbers unchanged in substance); T15b/T15c: S1-only ≥ 2 m median moves ≤ 0.04 m, ≤ 2 segments per zone cross the 2 m split; all categories ≤ 0.04 m (pass folds), ≤ 0.24 m (epochs, delta); delta wetland b_c 0.22 m (6 pre-breach passes) vs 0.59 m (post-breach) |
| F13 | endpoint plateau of the design hypsometry | `floodstate_eo.terrain.interp.bounded_interp` (NaN outside the table) exists and is tested; p95f switch in stage 3 | stage 3 | `tests/test_terrain_interp.py` |
| F14 | weekly balance from mean storages; source switch | stage 3 | stage 3 | — |
| F15 | figure/caption mismatches | Fig07 title ("no full-coverage scene of the corridor") and Fig04 labels done with the rerun; Fig03c, Fig09c in stage 3 | partly done | `p97_paper_figures.py` |
| F16 | not reproducible from scratch | gauge read from the repository copy (identical to the sibling source, checked); synthetic end-to-end domain in `tests/test_p95e_contract.py`; DAG, manifests, geojson vendoring in stage 3 | partly done | `p95.load_gauge` |
| F17 | versions / links drift | stage 3 | stage 3 | — |
| F18 | `n_orbits_event` counts scenes | stage 3 | stage 3 | — |
| F19 | undefined `lk` in p76 | stage 3 | stage 3 | — |
| F20 | 40 draws; quantile stability; median shift unexplained | 1000 coherent worlds (publication ensemble); convergence at n = 40 / 100 / 250 / 500 / 1000 for two seeds with bootstrap intervals of the quantile estimators; ablation of every component; distribution of the day of the maximum | done | T11c, FigS12, T11d, T12c |

## Reproduction gate and attribution (nominal runs, Dnipro corridor)

The rev-6 code run in legacy mode (`--terrain-table legacy_c_seamless --evaluation zonal_legacy --coarse-anchor grid_legacy`)
reproduces the committed rev-5 tables **exactly**: 138 of 138 pooled rows, 276 of 276 zone rows and 33 of 33 S1-validation
rows, every cell identical. One change at a time (T11h), A_new on 7 June: rev 5 235.3 km² → + water-surface lattice anchored in
map coordinates 235.6 → + connectivity on the union mosaic 235.6 → + FABDEM-only residual table per zone, bed cells
uncorrected = rev 6 **243.2 km²**; W_total 779.1 → 796.6 km², pre-breach regime 488.5 → 501.3 km². The nominal change is the
terrain residual model; the mosaic changes nothing measurable on the real rasters (T11i), the lattice +0.3 km².

## Results of the recomputation (final, 2026-09-29; details and every check in `publication/VALIDATION_2026-09-29.md`)

- **Gate:** draw 0 of the ensemble reproduces the nominal p95 run on 276 / 276 rows (identical cell counts); the terrain field
  has std 1.000 (0.985–1.016); new area 0 before the breach in every world; T12 W_total quantiles = the ensemble's (difference 0.0).
- **Corridor, 7 June (1000 coherent worlds):** A_new 262.4 [250.3–277.8] km² (nominal 243.2), W_total 791.2 [767.3–819.4] km²
  (nominal 796.6), V_new 626.8 [585.0–674.0] hm³ (nominal 514.5); areal maximum on 7 June in 77 % of the worlds, 8 June in 23 %.
  Rev 5 (40 draws): 246.7 [237.6–254.9], 790.5 [781.4–798.7] (shifted interval), 565.9 [545.4–595.7].
- **Convergence (T11c):** two seeds agree within 2.1 km² (A_new), 1.0 km² (W_total), 5 hm³ (V_new) at p05/p50/p95 at n = 1000.
- **Ablation (T11d):** the nominal run lies below the ensemble through the terrain term acting on the connectivity — perturbed
  terrain shrinks the pre-breach regime (775 vs 810.5 km²) while the peak-day total barely moves; the water-surface term alone
  reproduces the nominal median (239 vs 243 km²); fixing the regime removes most of the offset (248 km²). A_new width = mainly
  terrain, W_total width = mainly water surface, the 13 June upper tail = the interpolation term; the RMSE-scaled interpolation
  error is the largest single sensitivity (W_total 7 June 714–874 km²).
- **Water-surface offset (T11e):** W_total ~210–230 km² per metre; A_new 62–76 km² per metre near the nominal surface and
  181 km² per metre above +0.1 m (connectivity threshold).

## Maintainer's review of the Stage-1 numbers (2026-09-29) and the decisions that freeze Stage 1

Verdict: **Stage 1 — technically validated; scientific results accepted subject to support-domain qualification and claim
revision**, both done in this pass. The central reconstruction survived the new Monte-Carlo; what changed is the weight of the
spatial support of the water surface and of the nonlinearity of the connectivity.

- **D-SUPPORT (decided):** no hard 10 km cutoff in the primary. The FULL terrain-connectivity reconstruction stays the primary
  product; each newly inundated cell is classed by the distance of its nearest SWOT node — **direct** ≤ 3 km, **extrapolated**
  3–10 km, **weak** > 10 km (operational thresholds, not physical constants) — with **cross-river** (Inhulets) and gauge-capped
  as independent flags, not as definitions of "weak" (p95l, T11k/T11l). Reported next to the primary: the **supported core**
  (≤ 10 km) and the 10 km cap run as a sensitivity. Corridor, 7 June (nominal): 243.2 km² = direct 73.1 + extrapolated 108.5
  + weak 61.7 km² → **25 %** weak, core 181.5 km² (the cap run: 180.2 km²); 9 June 7 %, 13 June 2 %; p42 domain 6 %; Inhulets
  93 % weak (cross-river 11.3 km²). The classes add up to the p95 new area on all 276 zone-region-day rows (asserted).
- **C03 / support ontology (decided):** as above; the Inhulets claims are restricted by the support classes (distance first;
  the lower-valley nodes also stood metres above the tributary on 6 June), cross-river is a flag.
- **D-EMU (decided):** the emulator leaves the evidence path — a computational diagnostic only (T12d); removed from T12,
  Fig04, the claims, the dashboard headline and the abstract; `test_terminology_freeze` now asserts the absence.
- **Claims C01–C03 and C07 (revised):** C01 = a reconstruction, not a validated flood map, with the day of the maximum as a
  distribution (7 June in 77 %, 8 June in 23 % of the 1000 worlds); C02 = the rev-6 numbers and the weak share; C03 = the upper
  and central Inhulets weakly constrained, the withheld gauge exposing the early overestimation and the three-day timing
  mismatch; C07 = 1000 worlds and the mechanism through the draw-specific baseline connectivity (the rev-5 "noise adds depth and
  connections" is withdrawn).
- **Mykolaiv (decided):** a second withheld validation site (never an input) — Kherson is the input/anchor, Kalynivske tests
  the tributary propagation, Mykolaiv the western-delta interpolation (−0.82 m on 8 June).
- **Full Monte-Carlo draw tables (decided):** release assets (GitHub release / Zenodo), not in git; git keeps the summaries, the
  manifest and `tables/p95e_draws_checksums.csv` (sha256, rows, seed, code commit). The two commits of this pass were rebuilt
  before any push so that the draw files never enter the history.
- **Gravity / hydraulics (decided):** no gravity or potential layer (it duplicates z < H); the reconstruction is stated as a
  static terrain-connectivity model in §3.2, and the Discussion (§5) states that propagation, storage, friction and transient
  backwater need hydraulic modelling (Dale et al. 2026; Kasmalkar et al. 2024; Barnes et al. 2021 — Crossref-verified, quotes
  checked), with the withheld gauges as the evidence and the reconstruction as the calibration target (Paper 5).
- **Figures, maps, dashboard (maintainer's request):** FigS14 (support map + daily core), FigS15 (withheld gauges); the dashboard
  shows the support classes by day on the Maps page, the gauges with their roles, an observational-support section and a
  withheld-gauge section; the README links the live app (https://floodstate-eo.streamlit.app, deployed from `main` by the
  maintainer on Streamlit Community Cloud).
- **c-HAND (maintainer's lead, verified):** Wang, Passalacqua, Cai & Dawson (2024), Frontiers in Water 6:1329109 — Crossref and
  full text checked: cells "lower than the gage elevation" and "connected to the ocean", depth = gauge − cell, "a static
  equilibrium assumption"; against ADCIRC 99 % of the flooded cells found, the area over-predicted by about 27 %. Cited in §3.2
  (the operator's precedent, extended here to a distributed, observation-constrained H(x, y, t) with a baseline and an
  uncertainty), in the Limitations and in §5.
- **Claims C01–C03, C07 checked against the tables and the corrected method** (every number matches T12/T12c/T11k/T11d/T17d);
  four precision fixes: C01 — 8 June (23 % of the worlds) is the Kherson peak-stage day; C02 — the pre-breach start is the
  Monte-Carlo median (473 km², nominal 501 km² above its p95) so both ends come from the ensemble; C03 — the three-day
  mismatch is of the water-level maximum at the gauge, not of the valley's areal maximum (9 June); C07 — 775.2 km² is the
  regime with the terrain alone perturbed (the full budget: 787.6 km²).
- **Next:** Stage 1 frozen (this commit); merge/push to `main` after the maintainer's review of C01–C03/C07; then Stage 2 =
  F09 → F10 → F08.

## Decisions recorded (Stage 1)

- **D-BIAS** class residual statistics (b_c, σ_c) from FABDEM-sourced cells only, per zone (p95j); the former "C seamless" rows
  are no longer used (legacy mode only).
- **D-BED** bed cells (source 1/2/5): no stochastic term in Stage 1 — a stated limitation (T11j: 0 % of the new area on 7 June).
- **D-CORR** terrain-field covariance = pooled robust nested fit (nugget 0.08, 0.50 × exp(−h/123 m) + 0.42 × exp(−h/1172 m));
  the single exponential (nugget 0.16, 315 m) and no nugget are ablations.
- **D-INTERP** interpolation scale = gap-matched NMAD (primary); RMSE scale (heavy tails during the rise) = ablation.
- **D-MC1** per-day SWOT term shared by all nodes: OFF in the primary budget, 0.05 m as an ablation.
- **D-N** 1000 coherent worlds = the publication ensemble; the nominal run is draw 0, a diagnostic.
- **D-SEAM** connectivity on the union mosaic (per-zone only as the seam check).
- **D-RULE** `connected_ceiling` is the CLI default; every output carries an explicit rule suffix.
- **D-VERT** EVRF2019 for every height, asserted from declarations (terrain raster tag, SWOT chain, gauge column, ICESat-2 chain).
- **D-EMU** decided 2026-09-29: the emulator is a computational diagnostic outside the evidence path (T12d).

## Findings of Stage 1 that the maintainer should see before the text pass

- **Water-surface support is structural, not only statistical.** On 7 June 371 km² of the reconstructed water surface take
  their height from SWOT nodes within 3 km and 426 km² from the nearest node farther away (T11g). Declaring a node unavailable
  beyond a 3-day gap leaves 7 June unchanged but raises the delta's new area on 9 June from 86 to 150 km² and on 13 June from 68
  to 130 km² (outside the p42 floodplain; the corridor maximum moves to 9 June): the fallback surface of the delta far from the
  nodes, not the interpolation noise, dominates those days. The Monte-Carlo budget does not contain this structural choice.
- **Fallback distance (F07), quantified.** Capping the nearest-node fallback at 10 km (cells farther from every node get no
  surface unless capped at the Kherson gauge; sensitivity `_fallback10km`, T12) lowers the corridor's new area on 7 June from
  243.2 to 180.2 km² (−26 %) and W_total from 796.6 to 667.4 km², while the p42 terrain-eligible floodplain barely moves
  (152.7 → 142.9 km²) and the Inhulets valley drops from 41.4 to 3.0 km². A quarter of the corridor's reconstructed new area
  rests on water-surface heights taken from nodes more than 10 km away — a structural dependence much larger than the
  Monte-Carlo width. **D-FALLBACK (open):** keep and report, cap in the primary, or report the p42 domain as the main region.
- **The liman gauge Mykolaiv (98027) and the western delta** (maintainer's station list, 2026-09-29; p95k, T17e/T17f,
  `figures/m6_v003A/p95k_liman_mykolaiv.png`). Yearbook 2023 table 1.2 (daily means in cm above the zero; zero −5.00 m BS-77 in the sheet header, so ~500 cm above the zero
  is ~0 m BS-77): the liman rose from 497 cm = 0.17 m EVRF2019 to its highest level of 602 cm = 1.22 m EVRF2019 on 8 June (the
  highest since 1963; rise 1.05 m; highest daily mean 596 cm, +0.99 m), the day of the Kherson peak stage (+5.18 m there; Kherson − Mykolaiv head +0.40 m before the
  breach, +4.62 m at the peak), and was still +0.16 m in late June (inside the ±0.3–0.5 m wind-setup regime). The westernmost SWOT
  node of the delta (E 457.6 km, N 5156.4 km) has no observation from 6 to 22 June: its interpolated level stays at ~0.33 m through the
  flood, so the reconstructed western delta keeps a pre-breach surface (0.82 m below the liman's daily mean on 8 June). The 3-day
  maximum-gap sensitivity, which drops that node, over-corrects towards the Kherson level (+64 km² in the delta on 9 June): the
  truth is bracketed by Kherson and Mykolaiv. Together with Kalynivske this argues for using the independent gauges as boundary
  observations (with along-channel interpolation) where SWOT is silent — or for excluding those parts from the claims. **D-SUPPORT
  (open for the corridor fallback and the western delta; the Inhulets part is decided as D-INHULETS below).** The yearbook flag '/' on 6–16 June at Mykolaiv is to be confirmed from the legend.
- **Inhulets: an independent gauge shows the upper valley is unconstrained** (maintainer's request of 2026-09-29;
  `workflows/m6/p95k_inhulets_gauge_check.py`, T17c/T17d, `figures/m6_v003A/p95k_inhulets_kalynivske.png`). Kalynivske 80575
  (yearbook 2023 table 1.2: daily MEANS in cm above the gauge zero; zero **−1.34 m BS** from the sheet header, EPSG:9902 step
  +0.209 m). **Correction (2026-09-29, found when the maintainer asked to re-check the cm-above-zero conversion and to use the
  highest instead of the mean levels): the first p95k run used +1.34 m, so every Kalynivske level was 2.68 m too high; the
  numbers below replace the earlier ones, including the earlier verdict on the gauge-node sensitivity.** The gauge recorded the
  backwater: 0.58 m EVRF2019 before the breach (≈ Kherson), highest level 772 cm = 6.59 m EVRF2019 on 10 June (yearbook
  '(772*)', the highest since 1927; highest daily mean 758 cm = 6.45 m; rise 6.01 m; 62 cm above the passport maximum of 710 cm;
  7 days at or above the floodplain exit of 490 cm = 3.77 m EVRF2019, consistent with the floodplain terrain around the post,
  p25 4.11 m; maximum 2 days after the Kherson peak stage); the upstream posts 80568 / 80564 stayed flat, so the rise is Dnipro
  backwater. The SWOT nodes of the Inhulets stop at N 5179.7 km, the gauge is at N 5218 km: the reconstructed surface there is a
  Dnipro node 17.6 km below the dam (39.5 km away) — +0.77 m before the breach, +9.5 m on 6 June, +8.3 m on 7 June, +5.2 m on
  8 June, +2.6 m on 9 June, +0.04 … +0.31 m on 13–18 June; maximum on 7 instead of 10 June; the floodplain around the post is
  flooded in the reconstruction from 6 June, by the gauge level from 9 June (F07 quantified by an independent observation).
  **With the correct zero the gauge as an extra water-surface node (sensitivity `_inhulets_gauge_node`) improves the S1
  agreement in the valley on every event date** (CSI 0.285 → 0.317 on 9 June, 0.325 → 0.365 on 13 June, 0.286 → 0.328 on
  14 June, 0.118 → 0.159 on 18 June; terrain-only area on 6 June 11.4 → 4.9 km²) and lowers the valley's new area on 7 June from
  41.4 to 19.2 km² (8 June 45.4 → 39.4 km²; 9–13 June within ±2.3 km²); the Dnipro corridor is unaffected (243.2 km² either way).
  Open detail: in quiet conditions (before the breach, after 18 June) the gauge reads 0.3–0.4 m below the uppermost Inhulets
  SWOT nodes 38 km downstream (median −0.37 m before the breach), which a draining tributary cannot do — a decimetre offset of
  the gauge zero (header 'БС', not 'БС-77'; pile No. 5 re-levelled during the event) or of the SWOT chain in the Inhulets;
  irrelevant at the metre scale of the event; it enters e_abs and cancels in e_rise (the reason for reporting both). Claim C03 (Inhulets numbers) must be
  reconsidered in the text pass. **D-INHULETS (DECIDED by the maintainer, 2026-09-29):** Kalynivske 80575 is withheld from the primary WSE
  reconstruction and retained as an independent tributary validation site. Its observations are used to evaluate absolute WSE,
  event-relative stage change, peak timing and recession. A separate gauge-assisted sensitivity run quantifies the effect of
  adding local tributary information but is not used for the primary reconstruction. Primary inundation claims for the
  Inhulets are restricted according to observational-support diagnostics; areas/times controlled only by distant fallback are
  reported as weakly constrained rather than interpreted as equally reliable reconstruction. Implemented in p95k (T17c/T17d,
  new tables `p95k_inhulets_support_split.csv`, `p95k_inhulets_support_distance.csv`, two-panel figure) and §4.7:
  - e_abs = H_rec − H_gauge: +0.77 m before the breach, +9.50 m on 6 June (rising limb), +1.46 m on the gauge maximum,
    +0.04 … +0.92 m in the recession to 20 June. e_rise = (H_rec − H_rec,pre) − (H_gauge − H_gauge,pre): +8.74 m on 6 June,
    +0.69 m on the gauge maximum, below zero from 12 June, −0.72 m on 14 June (the reconstruction drains ahead of the valley),
    within ±0.25 m for good only from 26 June. Peak timing −3 d (7 vs 10 June); rise +9.28 m vs +5.87 m (daily means).
    The close absolute agreement on 13–18 June is therefore a coincidence of the +0.77 m pre-breach offset and the −0.5…−0.7 m
    recession lag, not hydraulic agreement — visible only in e_rise.
  - The support at the gauge did NOT change over the event: all 46 days the nearest-node fallback from the same Dnipro node
    (22511300080231, 39.5 km; observed on 42 days; nearest Inhulets node 40.8 km). The error decay after the peak is hydraulic
    (main stem and valley converging), not a support change — the maintainer's "if confirmed" hypothesis of better support
    after 12–13 June is not what happens; the diagnostic flags the place, the gauge shows when that support fails (transient).
  - Support of the valley's new area (nominal primary): on 7 June 41.4 km² = within 3 km of a node 0.4 km² (1 %), same-river
    fallback 29.8 km² (serving node median 32 km), cross-river fallback 11.3 km² (27 %, 40 km); by distance 1 / 6 / 7 / 21 / 65 %
    for 0–3 / 3–10 / 10–20 / 20–30 / > 30 km (9 and 13 June alike). Distance, not only the river, limits the constraint: the
    mouth nodes stood 2.6 m above the gauge on 6 June too. **Open for the text pass (C03):** the restriction criterion — cross-river
    fallback only (18–27 %) or a distance threshold (e.g. > 10 km: 93 %), which would leave essentially the lower valley.
- The literature notes' recommendations for the text (Lehnigk 2026, Dale 2026, Penton & Overton 2007, FLEXTH, c-HAND, Barnes,
  Kasmalkar, Roberts 2017, Olofsson 2014, Dwork 2015 / Feldman 2019) are for the text pass; Roy & Gupta 2021 (Crossref-verified)
  is already cited for the convergence check in §3.3.
