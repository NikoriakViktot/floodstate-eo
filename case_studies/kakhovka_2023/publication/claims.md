# Claims register (rendered from evidence_matrix.csv -- do not edit by hand)

Evidence levels: independent_physical > cross_sensor > weak_label_agreement > contextual. Every model number is agreement with weak reference labels, never flood-mapping accuracy. Areas carry their semantics (observed_S1 / mapped_UNet / terrain_reconstructed / literature_reported) and are named as 'reconstructed total water-surface area' (W_total) or 'reconstructed newly inundated area' (A_new). Primary uncertainty = 1000 coherent Monte-Carlo worlds (p95e rev 2; convergence with a second seed in T11c); the 100 000-draw emulator is a computational diagnostic outside the evidence path (T12d). Terminology is frozen in TERMINOLOGY.md. Each claim: claim -> evidence class -> table cell -> uncertainty -> limitation.

## Primary claims

### C01 [independent_physical] -- section 4.1 (formerly C01 (part))

**Statement.** In the daily terrain-connectivity reconstruction constrained by the observed water surface, the maximum of the newly inundated area of the Dnipro corridor falls on 7 June 2023 in 77 % of the 1000 Monte-Carlo worlds and on 8 June in 23 %, between the available Sentinel-1 acquisitions (6 June partial, 9 June) and apart from the peak stage at Kherson (gauge maximum on 8 June); it is a value of the reconstructed series, not an observation and not a validated flood map.

- **Independent:** yes -- water surface (SWOT nodes + gauge) x terrain; no EO flood mask enters; the timing between acquisitions is model-dependent
- **Result type / dataset:** observation-constrained terrain inundation reconstruction / SWOT RiverSP nodes 05-26..07-10, Kherson gauge 80805, seamless terrain-bed elevation model (Paper 2); p95e rev 2 Monte-Carlo (1000 coherent worlds)
- **Independent unit:** day; **n:** 16 key dates of the reconstructed series; 11 S1 dates
- **Value:** A_new 06-06 203, 06-07 262 (maximum), 06-08 257, 06-09 216 km2; Kherson stage 06-07 5.66 m, 06-08 5.78 m (gauge maximum); **uncertainty:** Monte-Carlo p05-p95 on 06-07 250-278 km2; share of Monte-Carlo worlds with the areal maximum on 7 June 77% (T12c)
- **Evidence:** tables T12, T12c, T17b, T01; figures Fig04, Fig07
- **Scope:** Dnipro corridor (Inhulets excluded); connected_ceiling rule; closure kherson_paper1
- **Caveat:** static terrain-connectivity reconstruction: planar water surface per node neighbourhood, no momentum or continuity, no timing of filling and draining
- **Limitation:** the day of the maximum is set by the interpolated node series and the gauge; no scene verifies it; peak stage and peak area are different quantities (Lehnigk et al. 2026 report peak stages by 8 June)
- **Status:** TABLES_LINKED; RECOMPUTED 2026-09-29 (p95 rev 6 / p95e rev 2); statement revised on the maintainer's direction 2026-09-29 / draft

### C02 [independent_physical] -- section 4.1 (formerly C01 (part))

**Statement.** In the full terrain-connectivity reconstruction the total water-surface area of the Dnipro corridor rises from 501 km2 in the pre-breach regime (5 June, nominal run; Monte-Carlo median 473 km2) to 791 km2 on 7 June (Monte-Carlo median; p05-p95 767-819 km2), while the newly inundated area reaches 262 km2 (250-278 km2) with a new-water volume of 627 hm3 (585-674 hm3); the deterministic nominal run (797 km2, 243 km2, 514 hm3) is a diagnostic, and 25 % of its new area on 7 June rests on water-surface support farther than 10 km (supported core 182 km2).

- **Independent:** yes -- as C01
- **Result type / dataset:** observation-constrained terrain inundation reconstruction / as C01 + p95e rev 2 Monte-Carlo (1000 coherent worlds)
- **Independent unit:** day; **n:** 16 key dates x 1000 coherent Monte-Carlo worlds (primary)
- **Value:** W_total 06-05 501 (observed regime) -> 06-07 MC median 791 km2; A_new 06-07 MC median 262 km2 (terrain as delivered, nominal run: 348); V_new 06-07 MC median 627 hm3; nominal runs 797 km2 / 243 km2 / 514 hm3; **uncertainty:** PRIMARY Monte-Carlo p05-p95: W_total 767-819 km2, A_new 250-278 km2, V_new 585-674 hm3; support: 25% of the nominal new area rests on water-surface support > 10 km (supported core 182 km2, T11k)
- **Evidence:** tables T12, T11b, T11k; figures Fig04, Fig07
- **Scope:** Dnipro corridor; primary run (residual class bias removed on FABDEM cells); full reconstruction with its supported core (T11k)
- **Caveat:** total water-surface area and newly inundated area are two different quantities and are never called 'flooded area' without their semantics
- **Limitation:** residual terrain error of the FABDEM DTM under reeds, trees and buildings; the terrain-as-delivered run (reed beds counted as new) is a definitional sensitivity, not an error term; a quarter of the peak-day new area rests on water-surface support > 10 km (weakly constrained; the 10 km cap run is a sensitivity)
- **Status:** TABLES_LINKED; RECOMPUTED 2026-09-29 (p95 rev 6 / p95e rev 2); statement revised on the maintainer's direction 2026-09-29 / draft

### C03 [independent_physical] -- section 4.1, 4.7 (formerly C01 (part), C07)

**Statement.** The reconstructed inundation recedes within two weeks of the breach in the Dnipro corridor, following the Kherson stage. The Inhulets valley, reported separately and never added to the corridor, is constrained by its own SWOT nodes only in its lower ~10 km: 93 % of its reconstructed new area on 7 June rests on water-surface support farther than 10 km, and the gauge Kalynivske, withheld from the reconstruction, exposes an early-event overestimation of the reconstructed surface (+9.5 m on 6 June) and a three-day timing mismatch of the maximum (7 vs 10 June), so the upper and central Inhulets values are weakly constrained.

- **Independent:** yes -- as C01; the Inhulets valley uses its own SWOT nodes
- **Result type / dataset:** reconstructed daily series per region / as C01; p42 CUT_RECTS; UkrHMC yearbook 2023 (Kalynivske 80575, withheld)
- **Independent unit:** day; **n:** 16 key dates x 2 regions
- **Value:** corridor A_new 06-09 216, 06-13 136, 06-18 44, 06-21 2 km2 (stage 0.74 m); Inhulets A_new maximum 48 km2 on 06-09, W_total 77 km2; **uncertainty:** corridor spatial MC 06-13 119-187 km2; Inhulets 06-09: terrain 18 vs S1 36 km2, POD 0.33, CSI 0.28
- **Evidence:** tables T12, T13 (INHULETS rows), T11k, T17c, T17d; figures Fig04, FigS06
- **Scope:** Dnipro corridor vs Inhulets valley rectangle
- **Caveat:** the reconstructed recession carries no draining time; at the withheld gauge it runs ahead of the valley
- **Limitation:** no tributary hydrograph or propagation time in a static reconstruction (hydraulic modelling needed, §5); HAND rule not applicable there; earlier Inhulets figures 0.78-0.98 (pre-baseline) withdrawn
- **Status:** TABLES_LINKED; RECOMPUTED 2026-09-29 (p95 rev 6 / p95e rev 2); statement revised on the maintainer's direction 2026-09-29 / draft

### C04 [cross_sensor] -- section 4.2 (formerly C02)

**Statement.** Raw agreement between the reconstruction and Sentinel-1 new dark water on the observation domain is low (POD ~0.26, FAR ~0.62, CSI ~0.18 on 9 June) and is strongly conditioned by surface type and pre-existing wetness: most apparent terrain misses lie in predefined normally-wet or vegetation-dominated cells where SAR dark-water onset is not an appropriate binary reference; the conditional POD outside the normally-wet class (~0.96) is a diagnostic conditional agreement, not a corrected POD.

- **Independent:** partly -- the S1 dark-water rule is an independent observation but not ground truth
- **Result type / dataset:** cross-sensor agreement per acquisition date / S1 M3 per-scene masks, 11 dates
- **Independent unit:** acquisition date; **n:** 11 S1 dates (p42 floodplain footprint)
- **Value:** 06-09: POD 0.25, FAR 0.64, CSI 0.17; 06-13: POD 0.15; misses on normally-wet cells 150 of 152 km2; **uncertainty:** conditional POD outside the normally-wet class (diagnostic) 06-09 0.97, 06-13 0.93
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
- **Value:** A 56 km2; B 126 km2 (trees 45, wetland 19, built 24); C 263 km2 (normally wet 177; >= 5 m above the surface 54); **uncertainty:** mapped areas; class maps carry their own error
- **Evidence:** tables T14; figures Fig05
- **Scope:** both zones, S1 footprint of 06-09 (also 06-13, 06-14)
- **Caveat:** class maps are themselves products with error; areas are mapped areas
- **Limitation:** alternative explanations for S1-only detections >= 5 m above the surface (radar shadow, smooth non-water surfaces, local ponding, temporal mismatch, registration, water outside the assumed connectivity) are not individually tested
- **Status:** TABLES_LINKED / draft

### C06 [independent_physical] -- section 4.4, 4.5 (formerly C04, C05)

**Statement.** Independent altimetry constrains the vertical-error explanation of the disagreement: along the night ICESat-2 tracks that sample the S1-only cells >= 2 m above the surface, the seamless DEM agrees with the ICESat-2 ground to a few centimetres (median) and essentially no segment lies below the reconstructed surface, so the available ICESat-2 observations provide no evidence for a DEM bias large enough to explain those detections; the SWOT node surface used as input agrees with the Kherson gauge at day level (median +0.01 m, NMAD 0.07 m).

- **Independent:** yes -- altimetry independent of DEM, SAR and the reconstruction; gauge independent of SWOT
- **Result type / dataset:** altimetric consistency check + input consistency / ICESat-2 ATL08 night segments 2019-2025 (p57 chain); p59 nodes near Kherson vs gauge
- **Independent unit:** segment (tracks listed) / day; **n:** ICESat-2: 3205 + 1665 night segments on the S1-only >= 2 m cells (tracks and dates in T15); SWOT vs gauge 36 days
- **Value:** DEM - ICESat-2 median +0.03 m (delta), +0.02 m (floodway); ground - surface +13.5 m; share below surface 0.0%; gauge - SWOT median +0.01 m, NMAD 0.07 m; **uncertainty:** DEM - ICESat-2 p10-p90 -0.31 to +0.64 m; DEM class NMAD 0.39 m over 841752 segments (Paper 2); supports, does not prove
- **Evidence:** tables T15, T17, T18; figures Fig08, Fig06
- **Scope:** categories of the 06-09 agreement raster; Oleshky left-bank box; breach fortnight and full window
- **Caveat:** track-based sampling: the tracks do not cover every cell of the 54 km2; this supports, it does not prove
- **Limitation:** a consistency check of the DEM and the surface along tracks, not a validation of the inundation map; SWOT 11:00 UTC vs date-only gauge
- **Status:** TABLES_LINKED / draft

### C07 [independent_physical] -- section 3.3, 4.1 (formerly new)

**Statement.** Propagated through 1000 coherent Monte-Carlo worlds, the vertical error budget gives the newly inundated area and the new-water volume relative p05-p95 half-widths of 6 % and 9 % on 7 June and places their medians 8 % and 22 % above the deterministic nominal run. The upward shift arises primarily from nonlinear connectivity effects on the pre-event baseline: terrain perturbations reduce the connected pre-breach water (a rebuilt regime of 775 km2 against 810.5 km2 nominal) more strongly than the peak-event total water; volumes are therefore always reported with their interval and never centred on the nominal run.

- **Independent:** yes -- propagation of independent error terms
- **Result type / dataset:** uncertainty budget / p95e rev 2: 1000 coherent Monte-Carlo worlds (primary; second seed and ablation in T11c/T11d)
- **Independent unit:** draw; **n:** 1000 coherent Monte-Carlo worlds x 16 key dates
- **Value:** 06-07: A_new MC median 262 km2 [p05-p95 250-278] (nominal run 243); V_new MC median 627 hm3 [p05-p95 585-674] (nominal run 514); **uncertainty:** MC relative half-width: area 6 %, volume 9 %; MC median relative to the deterministic nominal run: area +8 %, volume +22 % (06-07; attribution to the error components in T11d: the pre-breach regime of the perturbed worlds 775 km2 against 810 km2 nominal)
- **Evidence:** tables T12, T11b, T11c, T11d; figures Fig04, FigS12
- **Scope:** Dnipro corridor, key dates
- **Caveat:** the Monte-Carlo ensemble is the only uncertainty interval; the 100 000-draw emulator is a computational diagnostic outside the evidence path (T12d)
- **Limitation:** 1000 worlds (quantile sampling error in T11c); the daily node-median water surface carries no propagation timing, bed cells carry no stochastic term, and the structural choices (fallback distance, gap handling, rule) lie outside the budget (T12 sensitivities); the displacement, not the width, carries the vertical error
- **Status:** TABLES_LINKED; RECOMPUTED 2026-09-29 (p95 rev 6 / p95e rev 2); statement revised on the maintainer's direction 2026-09-29 / draft

## Secondary claims

### C08 [cross_sensor] -- section 3.8, 4.6 (formerly C06)

**Statement.** Observed (S1), mapped (U-Net) and terrain-reconstructed areas are differently defined quantities (new vs total water; snapshot vs cumulative vs persistence); U-Net metrics quantify agreement with weak reference labels, never flood-mapping accuracy; the label contract is a persistence product describing the ~13 June regime; operational flooded-land figures (UNOSAT 6-9 June cumulative) are closer in kind to the newly inundated area than to the total water surface and are context, never validation.

- **Independent:** n/a -- definitional accounting
- **Result type / dataset:** area accounting / p93, p92, p94 + operational figures (context only)
- **Independent unit:** date / product; **n:** corridor accounting rows of T16
- **Value:** 06-09 S1 new dark water 300 km2 (observed_S1, snapshot); label recipe 168 km2 (persistence); U2b 241 km2 (mapped_UNet); A_new 06-09 216 km2 (terrain_reconstructed, snapshot); **uncertainty:** literature rows VERIFY (UNOSAT 3616: ~620 km2 flooded land cumulative 6-9 June; 3623: ~180 km2 on 13 June); different AOI, temporal semantics and reference water
- **Evidence:** tables T16, T19; figures Fig04
- **Scope:** corridor and p42 domain
- **Caveat:** no probability-sample reference exists; no area here is an unbiased estimate of the true flooded area
- **Limitation:** literature rows VERIFY; different AOI, date semantics and reference water
- **Status:** TABLES_LINKED / draft

### C09 [weak_label_agreement] -- section 4.9 (formerly C08)

**Statement.** Changing the label contract from v002 to v003_A with identical inputs removes a measurable reference-water artefact (predicted flood on recurrent May water on the test blocks) with no statistically resolved change in EVENT_FLOOD recall under the paired spatial-block bootstrap (interval crosses zero).

- **Independent:** no -- agreement with weak reference labels
- **Result type / dataset:** paired arm comparison / U2 v1 vs U2 v003A, m6_split_v1 TEST
- **Independent unit:** 10 km spatial block (paired bootstrap, 2000); **n:** TEST blocks, paired bootstrap 2000
- **Value:** flood on REFERENCE_WATER 15.3 -> 1.3 km2; paired -13.4 km2; EVENT_FLOOD recall diff -0.028; **uncertainty:** 95 % [-29.5, -2.5]; recall [-0.042, +0.006] (crosses zero: no statistically resolved change)
- **Evidence:** tables T07, T06; figures Fig03
- **Scope:** B1+B2 TEST blocks
- **Caveat:** global F1 not comparable across label sets (different negatives)
- **Limitation:** 'no statistically resolved change' is not 'unchanged'
- **Status:** TABLES_LINKED / draft

### C10 [weak_label_agreement] -- section 4.9 (formerly C10)

**Statement.** Terrain (HAND) and surface-context inputs modify U-Net behaviour in physically interpretable ways: HAND reduces the predicted-flood burden on unlabelled cropland; land cover supplied as input context does not act as a veto; none of the audited cropland-associated SAR candidates showed positive evidence consistent with breach-induced inundation under the available SAR, optical and terrain constraints.

- **Independent:** no
- **Result type / dataset:** paired arm comparison + audit / U0d/U1/U2 v002 arms; p89 audit
- **Independent unit:** 10 km spatial block; candidate component; **n:** TEST blocks; 19.2 km2 audited candidates
- **Value:** U0d -> U2 unlabelled-cropland burden -9.6 km2; BU FP +0.37 km2; U1 retention A 0.78, B 0.85, D 0.91; **uncertainty:** 95 % [-14.8, -5.1]
- **Evidence:** tables T06, T08; figures Fig03, FigS
- **Scope:** B1+B2 TEST blocks
- **Caveat:** wording rule binding; group-A fields are elevated so HAND removes them as elevated land
- **Limitation:** agreement with weak labels on one frozen split
- **Status:** TABLES_LINKED / draft

### C12 [contextual] -- section 4.8 (formerly C11)

**Statement.** The PRE-event RF20 surface classification reaches spatial-block cross-validated per-class precision/recall/F1 and overall agreement with ESA WorldCover 2021 (the training reference) that support its use as evaluation strata and context; the frame transfers B1<->B2 show its stability across spatial frames; the WorldCover comparison is agreement, not validation.

- **Independent:** no -- WorldCover is the training reference
- **Result type / dataset:** classification agreement / p73 RF20, 5-fold spatial block CV, B1<->B2 transfer
- **Independent unit:** 20 m cell / block fold; **n:** 1177260 CV samples
- **Value:** OA 0.940, macro F1 0.943; transfer B1->B2 macro F1 0.906, B2->B1 0.932; **uncertainty:** agreement with WorldCover (training reference), not validation
- **Evidence:** tables T09, T10; figures FigS04
- **Scope:** B1, B2 20 m grid
- **Caveat:** WorldCover error; 7 documented limitations in the p73 QA verdict
- **Limitation:** not an independent land-cover accuracy
- **Status:** TABLES_LINKED / draft

### C13 [weak_label_agreement] -- section 3.7, 4.10 (formerly C12)

**Statement.** Conclusions of the arm comparisons are stable across the tested spatial-block scales: 7.5, 10, 15 and 20 km blocks (larger than the local object scale, comparable to or exceeding the spatial correlation length, and exceeding the 5.12 km patch plus buffers) give the same signs; a 5 km split is infeasible.

- **Independent:** no
- **Result type / dataset:** methodological sensitivity / U2 on v003A with m6_split at 7.5, 10, 15, 20 km
- **Independent unit:** spatial block; **n:** 4 splits (7.5, 10, 15, 20 km); 5 km infeasible
- **Value:** U2 v003_A global F1: 10 km 0.931, 7.5 km 0.956, 15 km 0.937, 20 km 0.876; **uncertainty:** each split has its own TEST geography; intervals in T20
- **Evidence:** tables T03, T20; figures FigS05
- **Scope:** B1+B2
- **Caveat:** each split has its own TEST geography; only values and intervals compared
- **Limitation:** one arm only
- **Status:** TABLES_LINKED / draft

### C14 [independent_physical] -- section 4.1 (formerly C13)

**Statement.** Under the sloped daily surface the pool released about fourteen cubic kilometres between 6 and 13 June; the daily-mean effective release (-dV/dt + Q_in) reached ~4x10^4 m3/s on 7 June -- a storage-balance estimate, not an instantaneous breach discharge; the peak floodplain storage of new water downstream (~0.65 km3) is only a few per cent of the release, implying that most of the released volume was transmitted downstream rather than stored on the mapped floodplain; the seamless-DEM hypsometry lies below the design table at equal levels (about 9 % at the full-pool level, 14-20 % at 13-11 m; the design table is undefined below 10 m), an open question for Paper 4 (the reservoir bowl on the historical bathymetry).

- **Independent:** yes -- gauges, SWOT, press levels, DEM, DniproHES releases; no EO flood mask
- **Result type / dataset:** storage balance (context) / p61 pool levels, dniprohes_releases, seamless DEM, p95 downstream volume
- **Independent unit:** day; **n:** 8 drawdown days with >= 2 level sources
- **Value:** pool volume 18.9 -> 4.5 km3 (released 14.7 km3); largest daily volume change -3225 hm3; daily-mean effective release 40057 m3/s on 06-07 (inflow 2730); downstream stored new water peak 642 hm3; **uncertainty:** DEM hypsometry vs design table at 17.5 m: 19.3 vs 21.1 km3 (-9 %); surface interpolated between 3-4 points; independent estimates of a different quantity (initial breach flow) 5.7e4 (Yi 2025), 3.6e4 (Kadam 2024) m3/s -- VERIFY
- **Evidence:** tables T21, T22; figures Fig09, FigS07
- **Scope:** pool 2023-05-26..06-13; downstream corridor + Inhulets
- **Caveat:** sloped surface interpolated between 3-4 level points; press levels; Nikopol/Rozumivka unavailable after 13 June; independent discharge estimates (Yi et al. 2025 initial 5.7e4 m3/s; Kadam et al. 2024 HEC-RAS 3.6e4 m3/s) are the same order of magnitude but different physical quantities -- context, not validation
- **Limitation:** not a hydrograph; the balance is bounded context for Paper 4 (historical bathymetry) and Paper 5 (HEC-RAS); the released volume inherits the hypsometry gap
- **Status:** TABLES_LINKED / draft

## Exploratory claims

### C11 [weak_label_agreement] -- section 4.9 (formerly C09)

**Statement.** Adding the immediate pre-event water state (W_pre) as an input increases agreement with v003_A, but the comparison is not independent because W_pre also enters the label ontology (label leakage); U2b is therefore a diagnostic upper bound, not a best model.

- **Independent:** no -- input/label circularity
- **Result type / dataset:** paired arm comparison / U2 vs U2b on v003A
- **Independent unit:** 10 km spatial block (paired bootstrap); **n:** TEST blocks, paired bootstrap 2000
- **Value:** U2 -> U2b flood on REFERENCE_WATER -0.62 km2; **uncertainty:** 95 % [-1.28, -0.13]; not independent
- **Evidence:** tables T07, T06; figures Fig03
- **Scope:** B1+B2 TEST blocks
- **Caveat:** circularity; report only as diagnostic
- **Limitation:** a W_pre-free label sensitivity was not built
- **Status:** TABLES_LINKED / draft
