# Claims register (rendered from evidence_matrix.csv -- do not edit by hand)

Evidence levels: independent_physical > cross_sensor > weak_label_agreement > contextual. Every model number is agreement with weak reference labels, never flood-mapping accuracy. Areas carry their semantics (observed_S1 / mapped_UNet / terrain_reconstructed / literature_reported) and are named as 'reconstructed total water-surface area' (W_total) or 'reconstructed newly inundated area' (A_new). Primary uncertainty = 40 spatial Monte-Carlo draws; the 100 000-draw emulator is a sensitivity envelope. Terminology is frozen in TERMINOLOGY.md. Each claim: claim -> evidence class -> table cell -> uncertainty -> limitation.

## Primary claims

### C01 [independent_physical] -- section 4.1 (formerly C01 (part))

**Statement.** The maximum reconstructed newly inundated area of the Dnipro corridor occurs on 7 June 2023, between the available Sentinel-1 acquisitions (6 June partial, 9 June); this areal maximum is distinct from the peak-stage timing at Kherson (gauge maximum on 8 June) and is a value of the daily reconstructed series, not an observation.

- **Independent:** yes -- water surface (SWOT nodes + gauge) x terrain; no EO flood mask enters; the timing between acquisitions is model-dependent
- **Result type / dataset:** observation-constrained terrain inundation reconstruction / SWOT RiverSP nodes 05-26..07-10, Kherson gauge 80805, seamless DEM (Paper 2)
- **Independent unit:** day; **n:** 16 key dates of the reconstructed series; 11 S1 dates
- **Value:** A_new 06-06 189, 06-07 247 (maximum), 06-08 237, 06-09 196 km2; Kherson stage 06-07 5.66 m, 06-08 5.78 m (gauge maximum); **uncertainty:** spatial MC p05-p95 on 06-07 238-255 km2; the day of the maximum is not itself bootstrapped
- **Evidence:** tables T12, T17b, T01; figures Fig04, Fig07
- **Scope:** Dnipro corridor (Inhulets excluded); connected_ceiling rule; closure kherson_paper1
- **Caveat:** planar water surface per node neighbourhood; no momentum or timing of filling and draining
- **Limitation:** the day of the maximum is set by the interpolated node series and the gauge; no scene verifies it; peak stage and peak area are different quantities (Lehnigk et al. 2026 report peak stages by 8 June)
- **Status:** TABLES_LINKED / draft

### C02 [independent_physical] -- section 4.1 (formerly C01 (part))

**Statement.** The reconstructed total water-surface area of the Dnipro corridor rises from ~488 km2 in the pre-breach regime (5 June, observed) to ~790 km2 at the areal maximum (7 June), while the reconstructed newly inundated area reaches ~247 km2 with a new-water volume of ~566 hm3; each value is the Monte-Carlo median with its primary p05-p95 interval, the deterministic nominal run (779 km2, 235 km2, 509 hm3) lying below that interval.

- **Independent:** yes -- as C01
- **Result type / dataset:** observation-constrained terrain inundation reconstruction / as C01 + p95e spatial Monte-Carlo (40 draws)
- **Independent unit:** day; **n:** 16 key dates x 40 spatial draws (primary); 100 000 emulator draws (sensitivity)
- **Value:** W_total 06-05 488 (observed regime) -> 06-07 MC median 790 km2; A_new 06-07 MC median 247 km2 (DEM as delivered, nominal run: 347); V_new 06-07 MC median 566 hm3; nominal runs 779 km2 / 235 km2 / 509 hm3; **uncertainty:** PRIMARY spatial MC p05-p95: W_total 781-799 km2, A_new 238-255 km2, V_new 545-596 hm3; emulator envelope (sensitivity): W_total 758-837, A_new 214-293 km2
- **Evidence:** tables T12, T11b; figures Fig04, Fig07
- **Scope:** Dnipro corridor; central run (DEM class-bias corrected)
- **Caveat:** total water-surface area and newly inundated area are two different quantities and are never called 'flooded area' without their semantics
- **Limitation:** DEM under canopy and reeds; the DEM-as-delivered run (reed beds counted as new) is a definitional sensitivity, not an error term
- **Status:** TABLES_LINKED / draft

### C03 [independent_physical] -- section 4.1, 4.7 (formerly C01 (part), C07)

**Statement.** The reconstructed inundation recedes rapidly in the two weeks after the breach, with a strong spatial contrast between the Dnipro corridor (fast recession following the Kherson stage) and the Inhulets valley (backwater with a later maximum on 9 June), which is reported separately and never added to the corridor.

- **Independent:** yes -- as C01; the Inhulets valley uses its own SWOT nodes
- **Result type / dataset:** reconstructed daily series per region / as C01; p42 CUT_RECTS
- **Independent unit:** day; **n:** 16 key dates x 2 regions
- **Value:** corridor A_new 06-09 196, 06-13 118, 06-18 39, 06-21 3 km2 (stage 0.74 m); Inhulets A_new maximum 50 km2 on 06-09, W_total 76 km2; **uncertainty:** corridor spatial MC 06-13 114-129 km2; Inhulets 06-09: terrain 20 vs S1 36 km2, POD 0.40, CSI 0.34
- **Evidence:** tables T12, T13 (INHULETS rows); figures Fig04, FigS06
- **Scope:** Dnipro corridor vs Inhulets valley rectangle
- **Caveat:** recession is a lower bound (no timing of draining)
- **Limitation:** the Inhulets backwater is treated without a tributary hydrograph; HAND rule not applicable there; earlier Inhulets figures 0.78-0.98 (pre-baseline) withdrawn
- **Status:** TABLES_LINKED / draft

### C04 [cross_sensor] -- section 4.2 (formerly C02)

**Statement.** Raw agreement between the reconstruction and Sentinel-1 new dark water on the observation domain is low (POD ~0.26, FAR ~0.62, CSI ~0.18 on 9 June) and is strongly conditioned by surface type and pre-existing wetness: most apparent terrain misses lie in predefined normally-wet or vegetation-dominated cells where SAR dark-water onset is not an appropriate binary reference; the conditional POD outside the normally-wet class (~0.96) is a diagnostic conditional agreement, not a corrected POD.

- **Independent:** partly -- the S1 dark-water rule is an independent observation but not ground truth
- **Result type / dataset:** cross-sensor agreement per acquisition date / S1 M3 per-scene masks, 11 dates
- **Independent unit:** acquisition date; **n:** 11 S1 dates (p42 floodplain footprint)
- **Value:** 06-09: POD 0.26, FAR 0.62, CSI 0.18; 06-13: POD 0.15; misses on normally-wet cells 148 of 150 km2; **uncertainty:** conditional POD outside the normally-wet class (diagnostic) 06-09 0.96, 06-13 0.88
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
- **Value:** A 59 km2; B 120 km2 (trees 43, wetland 20, built 23); C 261 km2 (normally wet 173; >= 5 m above the surface 54); **uncertainty:** mapped areas; class maps carry their own error
- **Evidence:** tables T14; figures Fig05
- **Scope:** both zones, S1 footprint of 06-09 (also 06-13, 06-14)
- **Caveat:** class maps are themselves products with error; areas are mapped areas
- **Limitation:** alternative explanations for S1-only detections >= 5 m above the surface (radar shadow, smooth non-water surfaces, local ponding, temporal mismatch, registration, water outside the assumed connectivity) are not individually tested
- **Status:** TABLES_LINKED / draft

### C06 [independent_physical] -- section 4.4, 4.5 (formerly C04, C05)

**Statement.** Independent altimetry constrains the vertical-error explanation of the disagreement: along the night ICESat-2 tracks that sample the S1-only cells >= 2 m above the surface, the seamless DEM agrees with the ICESat-2 ground to a few centimetres (median) and essentially no segment lies below the reconstructed surface, so the available ICESat-2 observations provide no evidence for a DEM bias large enough to explain those detections; the SWOT node surface used as input agrees with the Kherson gauge at day level (median +0.01 m, NMAD 0.07 m).

- **Independent:** yes -- altimetry independent of DEM, SAR and the reconstruction; gauge independent of SWOT
- **Result type / dataset:** altimetric consistency check + input consistency / ICESat-2 ATL08 night segments 2019-2025 (p57 chain); p59 nodes near Kherson vs gauge
- **Independent unit:** segment (tracks listed) / day; **n:** ICESat-2: 3205 + 1687 night segments on the S1-only >= 2 m cells (tracks and dates in T15); SWOT vs gauge 36 days
- **Value:** DEM - ICESat-2 median +0.03 m (delta), +0.02 m (floodway); ground - surface +13.5 m; share below surface 0.0%; gauge - SWOT median +0.01 m, NMAD 0.07 m; **uncertainty:** DEM - ICESat-2 p10-p90 -0.31 to +0.64 m; DEM class NMAD 0.39 m over 841752 segments (Paper 2); supports, does not prove
- **Evidence:** tables T15, T17, T18; figures Fig08, Fig06
- **Scope:** categories of the 06-09 agreement raster; Oleshky left-bank box; breach fortnight and full window
- **Caveat:** track-based sampling: the tracks do not cover every cell of the 54 km2; this supports, it does not prove
- **Limitation:** a consistency check of the DEM and the surface along tracks, not a validation of the inundation map; SWOT 11:00 UTC vs date-only gauge
- **Status:** TABLES_LINKED / draft

### C07 [independent_physical] -- section 3.3, 4.1 (formerly new)

**Statement.** The vertical error budget affects the reconstructed new-water volume differently from the area: the p05-p95 half-widths of the 40 spatial draws are similar (a few per cent of the central value for both), but the Monte-Carlo distribution of the volume is displaced above the deterministic run by about twice the relative shift of the area (correlated DEM noise adds depth and connections); volumes are therefore always reported with their p05-p95 and MC median, and the deterministic volume is not centred in its interval. The hypothesis that area uncertainty is materially smaller than volume uncertainty is not confirmed at 40 draws.

- **Independent:** yes -- propagation of independent error terms
- **Result type / dataset:** uncertainty budget / p95e 40 spatial draws (primary); p95g emulator (sensitivity)
- **Independent unit:** draw; **n:** 40 spatial draws x 16 key dates
- **Value:** 06-07: A_new MC median 247 km2 [p05-p95 238-255] (nominal run 235); V_new MC median 566 hm3 [p05-p95 545-596] (nominal run 509); **uncertainty:** MC relative half-width: area 4 %, volume 5 %; MC median above the deterministic nominal run (which lies below the MC p05): area +5 %, volume +11 % (06-07); emulator AREA envelope A_new 214-293 km2 (sensitivity); emulator volume draws not used (unanchored)
- **Evidence:** tables T12, T11b; figures Fig04
- **Scope:** Dnipro corridor, key dates
- **Caveat:** the spatial MC is the primary interval; the 100 000-draw emulator is a broader sensitivity envelope of the AREA only (its volume draws are unanchored and not used); the two represent different distributions and are never mixed
- **Limitation:** 40 draws; planar surface, timing and canopy DEM error outside the budget; the displacement, not the width, carries the vertical error
- **Status:** TABLES_LINKED / draft

## Secondary claims

### C08 [cross_sensor] -- section 3.8, 4.6 (formerly C06)

**Statement.** Observed (S1), mapped (U-Net) and terrain-reconstructed areas are differently defined quantities (new vs total water; snapshot vs cumulative vs persistence); U-Net metrics quantify agreement with weak reference labels, never flood-mapping accuracy; the label contract is a persistence product describing the ~13 June regime; operational flooded-land figures (UNOSAT 6-9 June cumulative) are closer in kind to the newly inundated area than to the total water surface and are context, never validation.

- **Independent:** n/a -- definitional accounting
- **Result type / dataset:** area accounting / p93, p92, p94 + operational figures (context only)
- **Independent unit:** date / product; **n:** corridor accounting rows of T16
- **Value:** 06-09 S1 new dark water 300 km2 (observed_S1, snapshot); label recipe 168 km2 (persistence); U2b 241 km2 (mapped_UNet); A_new 06-09 196 km2 (terrain_reconstructed, snapshot); **uncertainty:** literature rows VERIFY (UNOSAT 3616: ~620 km2 flooded land cumulative 6-9 June; 3623: ~180 km2 on 13 June); different AOI, temporal semantics and reference water
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
- **Value:** pool volume 18.9 -> 4.5 km3 (released 14.7 km3); largest daily volume change -3225 hm3; daily-mean effective release 40057 m3/s on 06-07 (inflow 2730); downstream stored new water peak 653 hm3; **uncertainty:** DEM hypsometry vs design table at 17.5 m: 19.3 vs 21.1 km3 (-9 %); surface interpolated between 3-4 points; independent estimates of a different quantity (initial breach flow) 5.7e4 (Yi 2025), 3.6e4 (Kadam 2024) m3/s -- VERIFY
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
