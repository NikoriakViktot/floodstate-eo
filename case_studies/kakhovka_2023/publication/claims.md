# Claims register (rendered from evidence_matrix.csv -- do not edit by hand)

Evidence levels: independent_physical > cross_sensor > weak_label_agreement > contextual. Every model number is agreement with weak reference labels, never flood-mapping accuracy. Areas carry their semantics (observed_S1 / mapped_UNet / terrain_reconstructed / literature_reported).

## Primary claims

### C01 [independent_physical] -- section 5.1

**Statement.** Daily terrain-reconstructed new-inundation area and volume in the Dnipro corridor (dam -> liman, Inhulets excluded) peak on 2023-06-07, a day no satellite image covers, and recede to the pre-breach regime by ~22 June; central values carry a Monte-Carlo uncertainty band from DEM, SWOT, gauge and H(s,t)-interpolation errors.

- **Independent:** yes -- gauge + SWOT water surface x terrain; no EO flood mask enters
- **Result type / dataset:** terrain reconstruction / SWOT nodes 05-26..07-10, Kherson gauge 80805, p55 seamless DEM, HAND p42
- **Independent unit:** day; **n:** 16 key dates x 40 draws
- **Value:** peak 235 km2 on 2023-06-07 (DEM-uncorrected sensitivity 347); 06-13 108; 06-21 4; peak volume 509 hm3; TOTAL water surface 06-07 779 km2 (normal regime 06-05 488 km2); **uncertainty:** MC p05-p95 238-255 km2; volume 545-596 hm3; HAND lower bound 247 km2
- **Evidence:** tables T12, T11b; figures Fig04, Fig07
- **Scope:** Dnipro corridor; connected_ceiling rule; closure kherson_paper1
- **Caveat:** planar water surface per reach; no momentum or timing of filling/draining -> recession is a lower bound; DEM under canopy
- **Status:** TABLES_LINKED / draft

### C02 [cross_sensor] -- section 5.2

**Statement.** Inside the p42 floodplain domain the terrain reconstruction reproduces the recession pattern observed by Sentinel-1 on the S1 observation domain (POD/FAR/CSI per acquisition date); the disagreement on the peak scene is dominated by categories the sensor cannot see.

- **Independent:** partly -- S1 dark-water rule is an independent observation but not ground truth
- **Result type / dataset:** cross-sensor agreement / S1 M3 per-scene masks, 11 dates
- **Independent unit:** acquisition date; **n:** 11 S1 dates (p42 floodplain footprint)
- **Value:** 06-09: POD 0.26, FAR 0.62, CSI 0.18; 06-13: POD 0.15; **uncertainty:** POD excluding normally-wet cells (sensitivity) 06-09 0.96; misses on normally-wet 148 of 150 km2
- **Evidence:** tables T13; figures Fig04, Fig05
- **Scope:** p42 floodplain domain and corridor; S1 valid footprint per date
- **Caveat:** S1 blind under reeds/forest/buildings; POD_excl is a sensitivity with an a-priori exclusion rule (same-rule pre-breach potential)
- **Status:** TABLES_LINKED / draft

### C03 [contextual] -- section 5.3

**Statement.** Disagreement ontology on 2023-06-09: B (terrain+ / S1-) is dominated by forest, reed and built-up surfaces (SAR blind spots); C (terrain- / S1+) splits into ground within 2 m of the water surface (normally-wet reed beds: submergence, a depth signal) and ground >= 5 m above it (false SAR water on land).

- **Independent:** no -- decomposition uses WorldCover 2021 and p73 classes
- **Result type / dataset:** decomposition of disagreement / p95d agreement raster x WorldCover / p73 x elevation above WSE
- **Independent unit:** 20 m cell (area); **n:** 2 zones, 06-09 (also 06-13, 06-14)
- **Value:** A 59 km2; B 120 km2 (trees 43, wetland 20, built 23); C 261 km2 (normally wet 173; >= 5 m above 54); **uncertainty:** mapped areas; class maps carry their own error
- **Evidence:** tables T14; figures Fig05
- **Scope:** both zones, S1 footprint of 06-09 (also 06-13, 06-14)
- **Caveat:** class maps are themselves products with error; areas are mapped areas
- **Status:** TABLES_LINKED / draft

### C04 [independent_physical] -- section 5.4

**Statement.** Where Sentinel-1 reports water on ground >= 2 m above the reconstructed water surface, night ICESat-2 ATL08 ground heights agree with the seamless DEM within a few decimetres and lie above the surface in essentially all segments: that S1 water is false SAR water on land, not a DEM error.

- **Independent:** yes -- altimetry independent of DEM, SAR and the reconstruction
- **Result type / dataset:** altimetric consistency check / ICESat-2 ATL08 night segments (p57 chain), 2019-2025
- **Independent unit:** segment (tracks listed); **n:** 3205 + 1687 night segments
- **Value:** DEM - ICESat-2 median +0.03 m (delta), +0.02 m (floodway); ground - surface +13.5 m; share below surface 0.0%; **uncertainty:** p10-p90 -0.31 to +0.64 m
- **Evidence:** tables T15; figures Fig08
- **Scope:** categories of the 06-09 agreement raster; Oleshky left-bank box
- **Caveat:** track-based sampling does not validate the whole map; a consistency check, not a validation of the inundation model
- **Status:** TABLES_LINKED / draft

## Secondary claims

### C05 [independent_physical] -- section 4.6, 5.5

**Statement.** The SWOT node water surface used as input is consistent with the Kherson gauge at day level once anchored to the Kherson-local closure of Paper 1; the seamless DEM accuracy by land-cover class (Paper 2) sets the vertical error budget.

- **Independent:** yes
- **Result type / dataset:** input consistency / p59 nodes near Kherson vs gauge; p57 DEM vs ICESat-2 (Paper 2)
- **Independent unit:** day / segment; **n:** 36 days; DEM: 841752 segments (Paper 2)
- **Value:** gauge - SWOT median +0.01 m, NMAD 0.07 m, RMSE 0.06 m; DEM RMSE 1.04 m, NMAD 0.39 m; **uncertainty:** rise and peak: median +0.10 m over 7 days
- **Evidence:** tables T17, T18, T11b; figures Fig06
- **Scope:** breach fortnight and full window
- **Caveat:** frame validation itself is Paper 1; SWOT 11:00 UTC vs date-only gauge
- **Status:** TABLES_LINKED / draft

### C06 [cross_sensor] -- section 5.6

**Statement.** Observed (S1), mapped (U-Net) and terrain-reconstructed areas are three differently defined quantities; the M6 labels are a persistence product (water on >= 2 of 06-09/13/14) and therefore describe the ~13-June regime, not the 6-9 June peak reported in operational products.

- **Independent:** n/a -- definitional accounting
- **Result type / dataset:** area accounting / p93, p92, p94 + operational figures (context only)
- **Independent unit:** date / product; **n:** corridor accounting rows of T16
- **Value:** 06-09 S1 new dark water 300 km2 (observed_S1); label recipe 168 km2; U2b 241 km2 (mapped_UNet); terrain 06-09 183 km2; **uncertainty:** literature rows VERIFY; different AOI/date/reference water
- **Evidence:** tables T16, T19; figures FigS
- **Scope:** corridor and p42 domain
- **Caveat:** operational (UNOSAT/CEMS) figures differ in AOI, date and reference water and are context, never validation; no probability-sample reference exists
- **Status:** TABLES_LINKED / draft

### C07 [cross_sensor] -- section 5.7

**Statement.** The Inhulets valley responds as backwater (Dnipro level imposed at the mouth) and is reported separately from the Dnipro reach; agreement statistics are taken from T13 rows by rule and date only.

- **Independent:** partly
- **Result type / dataset:** backwater sub-domain / p95 Inhulets rectangle; S1
- **Independent unit:** acquisition date; **n:** 11 S1 dates (Inhulets rectangle)
- **Value:** 06-09: terrain 20 km2 vs S1 36 km2; POD 0.40, CSI 0.34; **uncertainty:** backwater assumption; earlier 0.78-0.98 figures withdrawn
- **Evidence:** tables T13 (INHULETS rows); figures FigS
- **Scope:** Inhulets valley rectangle (p42 CUT_RECTS)
- **Caveat:** backwater assumption; HAND rule not applicable there (HAND measured to the Dnipro); superseded pre-baseline numbers (0.78-0.98) withdrawn
- **Status:** TABLES_LINKED / draft

### C08 [weak_label_agreement] -- section 5.8

**Statement.** Changing the label contract from v002 to v003_A with identical inputs reduces predicted flood on reference (recurrent May) water on the test blocks without a detectable loss of EVENT_FLOOD recall.

- **Independent:** no -- agreement with weak reference labels
- **Result type / dataset:** paired arm comparison / U2 v1 vs U2 v003A, m6_split_v1 TEST
- **Independent unit:** 10 km spatial block (paired bootstrap, 2000); **n:** TEST blocks, paired bootstrap 2000
- **Value:** flood on REFERENCE_WATER 15.3 -> 1.3 km2; paired -13.4 km2; EVENT_FLOOD recall diff -0.028; **uncertainty:** 95 % [-29.5, -2.5]; recall [-0.042, +0.006]
- **Evidence:** tables T07, T06; figures Fig03
- **Scope:** B1+B2 TEST blocks
- **Caveat:** global F1 not comparable across label sets (different negatives)
- **Status:** TABLES_LINKED / draft

### C10 [weak_label_agreement] -- section 5.8

**Statement.** Terrain (HAND) as an input feature reduces the predicted-flood burden on unlabelled cropland; land cover supplied as context does not act as a veto; none of the audited cropland-associated SAR candidates showed positive evidence consistent with breach-induced inundation under the available SAR, optical and terrain constraints.

- **Independent:** no
- **Result type / dataset:** paired arm comparison + audit / U0d/U1/U2 v002 arms; p89 audit
- **Independent unit:** 10 km spatial block; candidate component; **n:** TEST blocks; 19.2 km2 audited candidates
- **Value:** U0d -> U2 unlabelled-cropland burden -9.6 km2; BU FP +0.37 km2; U1 retention A 0.78, B 0.85, D 0.91; **uncertainty:** 95 % [-14.8, -5.1]
- **Evidence:** tables T06, T08; figures Fig03, FigS
- **Scope:** B1+B2 TEST blocks
- **Caveat:** wording rule binding; group-A fields are elevated so HAND removes them as elevated land
- **Status:** TABLES_LINKED / draft

### C11 [contextual] -- section 4.7, 5.9

**Statement.** The PRE-event RF20 surface classification reaches spatial-block cross-validated per-class precision/recall/F1 and overall agreement with ESA WorldCover 2021 that support its use as evaluation strata and context; the WorldCover comparison is agreement with the training reference, not validation.

- **Independent:** no -- WorldCover is the training reference
- **Result type / dataset:** classification agreement / p73 RF20, 5-fold spatial block CV, B1<->B2 transfer
- **Independent unit:** 20 m cell / block fold; **n:** 1177260 CV samples
- **Value:** OA 0.940, macro F1 0.943; transfer B1->B2 macro F1 0.906, B2->B1 0.932; **uncertainty:** agreement with WorldCover (training reference), not validation
- **Evidence:** tables T09, T10; figures FigS
- **Scope:** B1, B2 20 m grid
- **Caveat:** WorldCover error; 7 documented limitations in the p73 QA verdict
- **Status:** TABLES_LINKED / draft

### C12 [weak_label_agreement] -- section 4.4, S

**Statement.** Conclusions of the arm comparisons do not depend on the 10 km spatial block size: the block size is justified by the autocorrelation range and the 5.12 km patch, and a 5 / 10 / 20 km sensitivity on one arm leaves the paired-comparison signs unchanged (or the change is reported).

- **Independent:** no
- **Result type / dataset:** methodological sensitivity / U2 on v003A with m6_split at 5, 10, 20 km
- **Independent unit:** spatial block; **n:** 4 splits (7.5, 10, 15, 20 km); 5 km infeasible
- **Value:** U2 v003_A global F1: 10 km 0.931, 7.5 km 0.956, 15 km 0.937, 20 km 0.876; **uncertainty:** each split has its own TEST geography; intervals in T20
- **Evidence:** tables T03, T20; figures FigS
- **Scope:** B1+B2
- **Caveat:** new splits change TEST geography; only signs and CIs compared
- **Status:** TABLES_LINKED / draft

## Exploratory claims

### C09 [weak_label_agreement] -- section 5.8

**Statement.** Adding the immediate pre-event water state (W_pre) as an input increases agreement with v003_A, but the comparison is not independent because W_pre also enters the label ontology; U2b is therefore a diagnostic upper bound, not a best model.

- **Independent:** no -- input/label circularity
- **Result type / dataset:** paired arm comparison / U2 vs U2b on v003A
- **Independent unit:** 10 km spatial block (paired bootstrap); **n:** TEST blocks, paired bootstrap 2000
- **Value:** U2 -> U2b flood on REFERENCE_WATER -0.62 km2; **uncertainty:** 95 % [-1.28, -0.13]; not independent
- **Evidence:** tables T07, T06 (+T21 if the W_pre-free label sensitivity is built); figures Fig03
- **Scope:** B1+B2 TEST blocks
- **Caveat:** circularity; report only as diagnostic
- **Status:** TABLES_LINKED / draft
