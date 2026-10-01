# Claims register (rendered from evidence_matrix.csv -- do not edit by hand)

Evidence levels: independent_physical > cross_sensor > weak_label_agreement > contextual. Every model number is agreement with weak reference labels, never flood-mapping accuracy. Areas carry their semantics (observed_S1 / mapped_UNet / terrain_reconstructed / literature_reported) and are named as 'reconstructed total water-surface area' (W_total) or 'reconstructed newly inundated area' (A_new). Primary uncertainty = 1000 coherent Monte-Carlo worlds (p95e rev 2; convergence with a second seed in T11c); the 100 000-draw emulator is a computational diagnostic outside the evidence path (T12d). Terminology is frozen in TERMINOLOGY.md. Each claim: claim -> evidence class -> table cell -> uncertainty -> limitation.

## Primary claims

### C01 [independent_physical] -- section 4.1 (formerly C01 (part))

**Statement.** In the daily terrain-connectivity reconstruction constrained by the observed water surface, the maximum of the aggregate newly inundated area (A_new, every cell outside the pre-breach regime) of the Dnipro corridor falls on 8 June 2023, the day of the peak stage at Kherson, in 53 % of the 1000 Monte-Carlo worlds and on 7 June in 38 % (seed = the pre-breach river network, D-SEED), between the available Sentinel-1 acquisitions (6 June partial, 9 June); it is a value of the reconstructed series, not an observation and not a validated flood map.

- **Independent:** yes -- water surface (SWOT nodes + gauge) x terrain; no EO flood mask enters; the timing between acquisitions is model-dependent
- **Result type / dataset:** observation-constrained terrain inundation reconstruction / SWOT RiverSP nodes 05-26..07-10 and the Kherson gauge 80805 in the validated vertical frame of Paper 1 v6, seamless terrain-bed elevation model (Paper 2, FABDEM part in Paper 1's production chain); p95 rev 7, p95e rev 2 Monte-Carlo (1000 coherent worlds)
- **Independent unit:** day; **n:** 16 key dates of the reconstructed series; 11 S1 dates
- **Value:** A_new 06-06 152, 06-07 234, 06-08 239 (maximum in most worlds), 06-09 201 km2; Kherson stage 06-07 5.65 m, 06-08 5.77 m (gauge maximum); **uncertainty:** Monte-Carlo p05-p95 on 06-07 216-254 km2; share of Monte-Carlo worlds with the areal maximum on 8 June 53% and on 7 June 38% (T12c)
- **Evidence:** tables T12, T12c, T17b, T01; figures Fig04, Fig07
- **Scope:** Dnipro corridor (Inhulets reported separately); connected_ceiling rule with the river-network seed (D-SEED 2026-09-30); closure kherson_paper1
- **Caveat:** static terrain-connectivity reconstruction: planar water surface per node neighbourhood, no momentum or continuity, no timing of filling and draining
- **Limitation:** the day of the maximum is set by the interpolated node series and the gauge; no scene verifies it; peak stage and peak area are different quantities (Lehnigk et al. 2026 report peak stages by 8 June)
- **Status:** TABLES_LINKED; RECOMPUTED 2026-09-30 in the vertical frame of Paper 1 v6 (p95 rev 7 / p95e rev 2); statement revised on the maintainer's direction 2026-09-29 / draft

### C02 [independent_physical] -- section 4.1 (formerly C01 (part))

**Statement.** In the full terrain-connectivity reconstruction the total water-surface area of the Dnipro corridor rises from 439 km2 in the pre-breach regime (5 June; Monte-Carlo median, p05-p95 410-465 km2) to 716 km2 on 7 June (686-744 km2). On 7 June 146 km2 (132-166 km2) of land classified as dry before the breach was newly inundated (A_new,dry, the headline flood expansion); separately, the inundated area within the vegetated wetland complex increased by 114 km2 (93-135 km2; dA_wet, the wetland response -- a difference from the reconstructed pre-breach state, whose nominal value of 83 km2 lies below the interval). The aggregate newly inundated area under the former state definition (A_new) is 234 km2 (216-254 km2), with a new-water volume of 603 hm3 (542-659 hm3), and is not the sum of the two reported quantities (T12hb); the deterministic nominal run (719 km2, 215 km2, 485 hm3) is a diagnostic, and 8 % of its new area on 7 June rests on water-surface support farther than 10 km (supported core 199 km2).

- **Independent:** yes -- as C01
- **Result type / dataset:** observation-constrained terrain inundation reconstruction / as C01 + p95e rev 2 Monte-Carlo (1000 coherent worlds)
- **Independent unit:** day; **n:** 16 key dates x 1000 coherent Monte-Carlo worlds (primary)
- **Value:** A_new,dry 06-07 MC median 146 km2 (132-166; nominal 160) -- the headline; dA_wet 114 km2 (93-135; nominal 83) -- the wetland response; A_new,dry + dA_wet - A_new = 26 km2 (T12hb); W_total 06-05 MC median 439 km2 (nominal run 461; pre-breach regime) -> 06-07 MC median 716 km2; aggregate A_new 06-07 MC median 234 km2 (sensitivity with the terrain as delivered, nominal run: 288); V_new 06-07 MC median 603 hm3; nominal runs 719 km2 / 215 km2 / 485 hm3; **uncertainty:** PRIMARY Monte-Carlo p05-p95: W_total 686-744 km2, A_new 216-254 km2, V_new 542-659 hm3; support: 8% of the nominal new area rests on water-surface support > 10 km (supported core 199 km2, T11k)
- **Evidence:** tables T12, T11b, T11k, T12h, T12hb; figures Fig04, Fig07
- **Scope:** Dnipro corridor; primary run (residual class bias removed on FABDEM cells); full reconstruction with its supported core (T11k)
- **Caveat:** total water-surface area and newly inundated area are two different quantities and are never called 'flooded area' without their semantics
- **Limitation:** residual terrain error of the FABDEM DTM under reeds, trees and buildings; the terrain-as-delivered run (reed beds counted as new) is a definitional sensitivity, not an error term; a quarter of the peak-day new area rests on water-surface support > 10 km (weakly constrained; the 10 km cap run is a sensitivity)
- **Status:** TABLES_LINKED; RECOMPUTED 2026-09-30 in the vertical frame of Paper 1 v6 (p95 rev 7 / p95e rev 2); statement revised on the maintainer's direction 2026-09-29 / draft

### C03 [independent_physical] -- section 4.1, 4.7 (formerly C01 (part), C07)

**Statement.** The reconstructed inundation recedes within two weeks of the breach in the Dnipro corridor, following the Kherson stage. The Inhulets valley, reported separately and never added to the corridor, is constrained by its own SWOT nodes only in its lower ~10 km: 93 % of its reconstructed new area on 7 June rests on water-surface support farther than 10 km, and the gauge Kalynivske, withheld from the reconstruction, exposes an early-event overestimation of the reconstructed water surface (+9.5 m on 6 June) and a three-day mismatch of the water-level maximum at the gauge (reconstruction 7 June, gauge 10 June), so the upper and central Inhulets values are weakly constrained.

- **Independent:** yes -- as C01; the Inhulets valley uses its own SWOT nodes
- **Result type / dataset:** reconstructed daily series per region / as C01; p42 CUT_RECTS; UkrHMC yearbook 2023 (Kalynivske 80575, withheld)
- **Independent unit:** day; **n:** 16 key dates x 2 regions
- **Value:** corridor A_new 06-09 201, 06-13 143, 06-18 45, 06-21 3 km2 (stage 0.73 m); Inhulets A_new maximum 50 km2 on 06-09, W_total 77 km2; **uncertainty:** corridor spatial MC 06-13 125-192 km2; Inhulets 06-09: terrain 19 vs S1 36 km2, POD 0.34, CSI 0.29
- **Evidence:** tables T12, T13 (INHULETS rows), T11k, T17c, T17d; figures Fig04, FigS06
- **Scope:** Dnipro corridor vs Inhulets valley rectangle
- **Caveat:** the reconstructed recession carries no draining time; at the withheld gauge it runs ahead of the valley
- **Limitation:** no tributary hydrograph or propagation time in a static reconstruction (hydraulic modelling needed, §5); HAND rule not applicable there; earlier Inhulets figures 0.78-0.98 (pre-baseline) withdrawn
- **Status:** TABLES_LINKED; RECOMPUTED 2026-09-30 in the vertical frame of Paper 1 v6 (p95 rev 7 / p95e rev 2); statement revised on the maintainer's direction 2026-09-29 / draft

### C04 [cross_sensor] -- section 4.2 (formerly C02)

**Statement.** Raw agreement between the reconstruction and Sentinel-1 new dark water on the observation domain is low (POD ~0.26, FAR ~0.62, CSI ~0.18 on 9 June) and is strongly conditioned by surface type and pre-existing wetness: most apparent terrain misses lie in predefined normally-wet or vegetation-dominated cells where SAR dark-water onset is not an appropriate binary reference; the conditional POD outside the normally-wet class (~0.96) is a diagnostic conditional agreement, not a corrected POD.

- **Independent:** partly -- the S1 dark-water rule is an independent observation but not ground truth
- **Result type / dataset:** cross-sensor agreement per acquisition date / S1 M3 per-scene masks, 11 dates
- **Independent unit:** acquisition date; **n:** 11 S1 dates (p42 floodplain footprint)
- **Value:** 06-09: POD 0.26, FAR 0.58, CSI 0.19; 06-13: POD 0.16; misses on normally-wet cells 146 of 149 km2; **uncertainty:** conditional POD outside the normally-wet class (diagnostic) 06-09 0.94, 06-13 0.91
- **Evidence:** tables T13; figures Fig04, Fig05
- **Scope:** p42 floodplain domain and corridor; S1 valid footprint per date
- **Caveat:** S1 blind under reeds, forest and buildings; the normally-wet class was fixed a priori
- **Limitation:** no probability-sample reference; POD/FAR/CSI measure agreement between two imperfect products
- **Status:** TABLES_LINKED / draft

### C05 [contextual] -- section 4.3 (formerly C03)

**Statement.** The disagreement on 9 June is mechanistic: terrain+/S1- (B) is dominated by forest, reed and built-up surfaces (SAR blind spots); S1+/terrain- (C) splits into ground within 2 m of the reconstructed surface (normally-wet reed beds: a submergence signal) and ground >= 5 m above it, which is topographically inconsistent with the reconstructed connected water surface (S1-only detections unsupported by the terrain/water-surface model).

- **Independent:** no -- decomposition uses WorldCover 2021 and p73 classes
- **Result type / dataset:** decomposition of disagreement / p95d agreement raster x WorldCover / p73 x elevation above WSE
- **Independent unit:** 20 m cell (area); **n:** 2 zones, 06-09 (also 06-13, 06-14)
- **Value:** A 59 km2; B 112 km2 (trees 36, wetland 19, built 24); C 260 km2 (normally wet 169; >= 5 m above the surface 54); **uncertainty:** mapped areas; class maps carry their own error
- **Evidence:** tables T14; figures Fig05
- **Scope:** both zones, S1 footprint of 06-09 (also 06-13, 06-14)
- **Caveat:** class maps are themselves products with error; areas are mapped areas
- **Limitation:** alternative explanations for S1-only detections >= 5 m above the surface (radar shadow, smooth non-water surfaces, local ponding, temporal mismatch, registration, water outside the assumed connectivity) are not individually tested
- **Status:** TABLES_LINKED / draft

### C06 [independent_physical] -- section 4.4, 4.5 (formerly C04, C05)

**Statement.** Independent altimetry constrains the terrain-error explanation of the disagreement: along the night ICESat-2 tracks that sample the S1-only cells >= 2 m above the reconstructed surface, the FABDEM-sourced terrain agrees with the ICESat-2 ground to a few centimetres (median) and essentially no segment lies below the surface; re-estimating the class bias without the checked passes moves that median by a few centimetres at most. The available ICESat-2 observations therefore provide no evidence for a terrain bias large enough to explain those detections (the agreement of the SWOT input with the gauges is part of the validated vertical frame of Paper 1 and is not re-tested here).

- **Independent:** yes -- altimetry independent of the terrain, the SAR and the reconstruction (the class bias is calibrated on the same corpus: pass hold-out in T15b/T15c)
- **Result type / dataset:** altimetric consistency check of the terrain along tracks / ICESat-2 ATL08 night ground segments 2019-2025 (Paper 2 chain, brought to Paper 1's production frame); the 06-09 agreement categories
- **Independent unit:** ICESat-2 pass (acquisition day; segments of one pass are not independent); **n:** ICESat-2: 3205 night segments on 17 passes (delta) + 1666 on 59 passes (floodway) on the S1-only >= 2 m cells (T15)
- **Value:** terrain - ICESat-2 median +0.03 m (delta), +0.02 m (floodway); ground - surface +13.5 m; share below the surface 0.0%; **uncertainty:** terrain - ICESat-2 p10-p90 -0.31 to +0.64 m; class-bias pass hold-out moves the corrected median by <= 0.04 m (T15b); supports, does not prove
- **Evidence:** tables T15, T15b, T15c; figures Fig08
- **Scope:** categories of the 06-09 agreement raster inside the Sentinel-1 valid footprint; FABDEM-sourced cells
- **Caveat:** track-based sampling: the tracks do not cover every cell of the category; this supports, it does not prove
- **Limitation:** a consistency check of the terrain and the surface along tracks, not a validation of the inundation map; the delta class bias depends on the epoch of the passes (T15c)
- **Status:** TABLES_LINKED / draft

### C07 [independent_physical] -- section 3.3, 4.1 (formerly new)

**Statement.** Propagated through 1000 coherent Monte-Carlo worlds, the vertical error budget gives the newly inundated area and the new-water volume relative half-widths (half the p05-p95 range over the median) of 5 % and 7 % on 7 June; the deterministic nominal run is a diagnostic and lies below the p05 of both on the peak days. That position arises primarily from nonlinear connectivity effects on the pre-event baseline: terrain perturbations reduce the connected pre-breach water (with the terrain alone perturbed, a rebuilt regime of 767.7 km2 against 801.0 km2 at the nominal) more strongly than the peak-event total water; volumes are therefore always reported with their interval and never centred on the nominal run.

- **Independent:** yes -- propagation of independent error terms
- **Result type / dataset:** uncertainty budget / p95e rev 2: 1000 coherent Monte-Carlo worlds (primary; second seed and ablation in T11c/T11d)
- **Independent unit:** draw; **n:** 1000 coherent Monte-Carlo worlds x 16 key dates
- **Value:** 06-07: A_new MC median 234 km2 [p05-p95 216-254]; V_new MC median 603 hm3 [p05-p95 542-659]; deterministic nominal run (diagnostic) 215 km2 / 485 hm3; **uncertainty:** MC relative half-width over the median: area 8 %, volume 10 %; the nominal run lies below the p05 on the peak days, attributed in T11d to the terrain acting on the connectivity of the pre-breach regime (497.7 km2 with the terrain alone perturbed against 532.5 km2 nominal)
- **Evidence:** tables T12, T11b, T11c, T11d; figures Fig04, FigS12
- **Scope:** Dnipro corridor, key dates
- **Caveat:** the Monte-Carlo ensemble is the only uncertainty interval; relative half-widths are taken over the median; the 100 000-draw emulator is a computational diagnostic outside the evidence path (T12d)
- **Limitation:** 1000 worlds (quantile sampling error in T11c); the daily node-median water surface carries no propagation timing, bed cells carry no stochastic term, and the structural choices (fallback distance, gap handling, rule) lie outside the budget (T12 sensitivities); the displacement, not the width, carries the vertical error
- **Status:** TABLES_LINKED; RECOMPUTED 2026-09-30 in the vertical frame of Paper 1 v6 (p95 rev 7 / p95e rev 2); statement revised on the maintainer's direction 2026-09-29 / draft

## Secondary claims

### C08 [cross_sensor] -- section 3.8, 4.6 (formerly C06)

**Statement.** Observed (S1), mapped (U-Net) and terrain-reconstructed areas are differently defined quantities (new vs total water; snapshot vs cumulative vs persistence); U-Net metrics quantify agreement with weak reference labels, never flood-mapping accuracy; the label contract is a persistence product describing the ~13 June regime, and the area mapped by a U-Net trained on it depends on the training seed; operational flooded-land figures (UNOSAT 6-9 June cumulative) are closer in kind to the newly inundated area than to the total water surface and are context, never validation.

- **Independent:** n/a -- definitional accounting
- **Result type / dataset:** area accounting / p93, p92 (U2b on v004, three training seeds), p95e + operational figures (context only)
- **Independent unit:** date / product; **n:** corridor accounting rows of T16
- **Value:** 06-09 S1 new dark water 300 km2 (observed_S1, snapshot); label recipe 168 km2 (persistence); U2b on v004 352, 297, 269 km2 (mapped_UNet, three seeds); A_new 06-09 201 km2 (terrain_reconstructed, MC median); **uncertainty:** literature rows VERIFY (UNOSAT 3616: ~620 km2 flooded land cumulative 6-9 June; 3623: ~180 km2 on 13 June); different AOI, temporal semantics and reference water
- **Evidence:** tables T16, T19; figures Fig04
- **Scope:** corridor and p42 domain
- **Caveat:** no probability-sample reference exists; no area here is an unbiased estimate of the true flooded area
- **Limitation:** literature rows VERIFY; different AOI, date semantics and reference water
- **Status:** TABLES_LINKED; text pass 2026-09-29 (v004, three seeds; reconstructed rows = Monte-Carlo medians) / draft

### C09 [weak_label_agreement] -- section 4.9 (formerly C08)

**Statement.** Changing the weak-label treatment of pre-event reference water produced a consistent model response across all three training seeds: predictions over reference-water areas decreased by 13.8-48.8 km2 under the v004 ontology. This demonstrates sensitivity of the learned flood representation to the weak-label definition of pre-event water rather than independent flood-mapping accuracy.

- **Independent:** no -- agreement with weak reference labels
- **Result type / dataset:** paired label comparison at fixed inputs, per training seed / U2 trained on v002_notrace (the v002 rule on the corrected M2, no REFERENCE_WATER class) vs U2 on v004; three training seeds; m6_split_v1 TEST, endpoints against v004
- **Independent unit:** 10 km spatial block (paired bootstrap, 2000 resamples per seed); the training seed; **n:** 3 training seeds x TEST blocks, paired bootstrap 2000 per seed
- **Value:** flood on REFERENCE_WATER, v004 - v002_notrace (U2): -13.8, -25.6, -48.8 km2 (3 of 3 intervals exclude zero); **uncertainty:** 95 % per seed [-35.3, -1.4], [-62.6, -3.7], [-111.3, -11.1]; EVENT_FLOOD recall interval excludes zero in 1 of 3 seeds
- **Evidence:** tables T07s, T07b; figures Fig03
- **Scope:** B1+B2 TEST blocks
- **Caveat:** global F1 not comparable across label sets; EVENT_FLOOD recall changed with an interval excluding zero in one of three seeds
- **Limitation:** agreement with weak labels on one frozen split; exploratory TEST; three seeds are the minimum evidence unit (D-SEEDS)
- **Status:** TABLES_LINKED; statement decided by the maintainer 2026-09-29 (D-C09) / draft

### C10 [weak_label_agreement] -- section 4.9 (formerly C10)

**Statement.** The apparent reduction in unlabelled-cropland predictions previously attributed to HAND did not reproduce under the corrected v004 ontology and three training seeds: the effect changed sign across seeds (+1.0, +7.6 and -3.8 km2), indicating that the earlier -9.6 km2 result was not robust to label revision and training stochasticity, so HAND should not be interpreted as independently demonstrated to suppress cropland false positives. Land cover supplied as an input (RF20, U1) did not act as a veto: it raised the unlabelled-cropland burden in all three seeds.

- **Independent:** no
- **Result type / dataset:** paired arm comparisons per training seed (a negative result for HAND) / U0d, U1, U2 on v004, three training seeds each; m6_split_v1 TEST
- **Independent unit:** 10 km spatial block (paired bootstrap per seed); the training seed; **n:** 3 training seeds x TEST blocks, paired bootstrap 2000 per seed
- **Value:** U2 - U0d unlabelled-cropland burden per seed +1.0, +7.6, -3.8 km2 (earlier single-seed v002 value -9.6 km2); U1 - U0d +6.8, +27.3, +21.1 km2; **uncertainty:** intervals excluding zero: HAND 1 of 3 (signs differ); RF20 input 3 of 3; seed range within an arm up to 20.8 km2 (T05s)
- **Evidence:** tables T06s, T05s; T06 (the superseded single-seed v002 value); figures Fig03, FigS01
- **Scope:** B1+B2 TEST blocks
- **Caveat:** the retracted statement (HAND reduces the cropland burden, -9.6 km2 on v002, one seed) is kept only as provenance (T06, T28)
- **Limitation:** agreement with weak labels on one frozen split; exploratory TEST; seed range of the cropland burden up to ~21 km2 within an arm (T05s)
- **Status:** TABLES_LINKED; statement decided by the maintainer 2026-09-29 (D-C10: retracted, negative result); the U1 sentence from T06s (three seeds) / draft

### C12 [contextual] -- section 4.8 (formerly C11)

**Statement.** The PRE-event RF20 surface classification agrees with ESA WorldCover 2021, its training reference, in spatial-block cross-validation well enough to serve as the context of the disagreement ontology and as evaluation strata; removing frame-overlap duplication had little effect on within-domain spatial CV but substantially reduced apparent B1->B2 transfer performance, showing that the overlap primarily biased estimates of geographic generalization; the WorldCover comparison is agreement, not validation.

- **Independent:** no -- WorldCover is the training reference
- **Result type / dataset:** classification agreement / p73 RF20, 5-fold spatial block CV, B1<->B2 transfer
- **Independent unit:** 20 m cell / block fold; **n:** 392420 CV samples (RF20 rev 2: global blocks, overlap counted once)
- **Value:** OA 0.938, macro F1 0.941 (0.929 with a 3.5 km buffer); transfer outside the overlap B1->B2 macro F1 0.848, B2->B1 0.907; **uncertainty:** agreement with WorldCover (training reference), not validation
- **Evidence:** tables T09, T10; figures FigS04
- **Scope:** B1, B2 20 m grid
- **Caveat:** WorldCover error; 7 documented limitations in the p73 QA verdict
- **Limitation:** not an independent land-cover accuracy
- **Status:** TABLES_LINKED; RECOMPUTED 2026-09-29 on RF20 rev 2 (F08); wording D-RF20 (maintainer 2026-09-29) / draft

### C13 [weak_label_agreement] -- section 3.7, 4.10 (formerly C12)

**Statement.** The level of agreement of U2 with the v004 weak labels is similar at 7.5, 10 and 15 km blocks and lower at 20 km, where few test blocks remain; each split has its own test geography, and with one arm and one seed per split the block size is a sensitivity of the level of agreement, not of the arm comparisons, which are drawn from the 10 km split only; a 5 km split is infeasible.

- **Independent:** no
- **Result type / dataset:** methodological sensitivity / U2 on v004 with m6_split at 7.5, 10, 15, 20 km (one seed per split)
- **Independent unit:** spatial block; **n:** 4 splits (7.5, 10, 15, 20 km), one seed each; 5 km infeasible
- **Value:** U2 v004 global F1: 10 km 0.931, 7.5 km 0.940, 15 km 0.932, 20 km 0.889; **uncertainty:** each split has its own TEST geography; intervals in T20
- **Evidence:** tables T03, T20; figures FigS05
- **Scope:** B1+B2
- **Caveat:** each split has its own TEST geography; only values and intervals are compared, never differences
- **Limitation:** one arm and one seed per split; the earlier sign statement had no support in T20 (narrowed in the text pass)
- **Status:** TABLES_LINKED; narrowed in the text pass 2026-09-29 / draft

### C14 [independent_physical] -- section 4.1 (formerly C13)

**Statement.** Under the sloped daily surface in the frame of Paper 1, the pool released about 14.6 km3 between 5 and 13 June (the 13 June pool an upper estimate) while keeping most of its area, which collapsed in the following week (Sentinel-2, 20 June); the daily-mean effective release (-dV/dt + Q_in) reached ~4x10^4 m3/s on 7 June -- a storage-balance estimate, not an instantaneous breach discharge; the new water stored downstream (Monte-Carlo medians, 605 hm3 in the corridor and 159 hm3 in the Inhulets valley on 8 June) is a few per cent of the release, implying that most of the released volume was transmitted downstream rather than stored on the mapped floodplain; the seamless-DEM hypsometry lies below the design table at equal levels (about 9 % at the full-pool level, 14-20 % at 13-11 m; the design table is undefined below 10 m), an open question for Paper 4 (the reservoir bowl on the historical bathymetry).

- **Independent:** yes -- gauges, SWOT, press levels, DEM, DniproHES releases; no EO flood mask
- **Result type / dataset:** storage balance (context) / p61 pool levels in Paper 1's frame (SWOT outlet production chain; G-REALM a check only; Nikopol censored bound), DniproHES releases, seamless DEM, p95e downstream volumes; Sentinel-2 20 June (p95h)
- **Independent unit:** day; **n:** 8 drawdown days with >= 2 level sources
- **Value:** pool volume 18.8 -> 4.2 km3 (upper estimate; released since 5 June 14.6 km3); water area 2132 -> 1790 km2, then 648 km2 of Sentinel-2 water on 20 June; largest daily volume change -3225 hm3; daily-mean effective release 40057 m3/s on 06-07 (inflow 2730); new water stored downstream on 06-08 (MC medians) corridor 595 + Inhulets 164 hm3; **uncertainty:** terrain hypsometry vs design table at 17.5 m: 19.3 vs 21.1 km3 (-9 %); surface interpolated between 3-4 level points, an upper bound at Nikopol on 12-13 June; independent estimates of a different quantity (initial breach flow) 5.7e4 (Yi 2025), 3.6e4 (Kadam 2024) m3/s
- **Evidence:** tables T21, T21b, T22, T23b, T12; figures Fig09, Fig10, Fig11, FigS07
- **Scope:** pool 2023-05-26..06-13; downstream corridor + Inhulets
- **Caveat:** sloped surface interpolated between 3-4 level points; an upper bound at Nikopol on 12-13 June; press levels; Nikopol/Rozumivka unavailable after 13 June; independent discharge estimates (Yi et al. 2025 initial 5.7e4 m3/s; Kadam et al. 2024 HEC-RAS 3.6e4 m3/s) are the same order of magnitude but different physical quantities -- context, not validation
- **Limitation:** not a hydrograph; the balance is bounded context for Paper 4 (historical bathymetry) and Paper 5 (HEC-RAS); the released volume inherits the hypsometry gap
- **Status:** TABLES_LINKED; RECOMPUTED 2026-09-30 (pool levels in Paper 1's frame, Nikopol bound, G-REALM a check only; Sentinel-2 exposure) / draft

## Exploratory claims

### C11 [weak_label_agreement] -- section 4.9 (formerly C09)

**Statement.** Adding the pre-event water term W_pre consistently reduced the unlabelled-cropland prediction burden across all three training seeds, while its effect over reference-water areas was consistent in two of three seeds. Because W_pre is itself a component of the weak-label construction, this result is interpreted as a diagnostic of label-induced model behaviour rather than independent evidence of improved flood discrimination.

- **Independent:** no -- input/label circularity
- **Result type / dataset:** paired arm comparison / U2 vs U2b on v004, three training seeds; m6_split_v1 TEST
- **Independent unit:** 10 km spatial block (paired bootstrap per seed); the training seed; **n:** 3 training seeds x TEST blocks, paired bootstrap 2000 per seed
- **Value:** U2b - U2 unlabelled-cropland burden -6.0, -8.6, -7.5 km2; flood on REFERENCE_WATER +7.45, -0.73, -0.77 km2; **uncertainty:** intervals excluding zero: cropland 3 of 3, reference water 2 of 3; not independent (W_pre circularity)
- **Evidence:** tables T06s, T07s, T07b; figures Fig03
- **Scope:** B1+B2 TEST blocks
- **Caveat:** circularity: W_pre is both an input and a label ingredient; report only as a diagnostic
- **Limitation:** a W_pre-free label sensitivity was not built
- **Status:** TABLES_LINKED; statement decided by the maintainer 2026-09-29 (D-C11) / draft
