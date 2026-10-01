<!-- manuscript_en_assembled.md: assembled by workflows/paper/p101_assemble_doc.py from manuscript.md; figures from publication/figures (downscaled copies in img/), tables from publication/tables (first 25 rows x 10 columns), captions from captions.md and tables/manifest.json. The filled manuscript is the source of truth. -->

# Daily inundation after the Kakhovka dam breach reconstructed from the observed water surface and terrain: propagated uncertainty, independent checks against withheld gauges, Sentinel-1 and ICESat-2, and weak-label machine learning as a diagnostic

**Manuscript draft (Paper 3 of the Kakhovka series), generated from `manuscript_template.md` by `workflows/paper/fill_manuscript.py`.
Rewritten in one pass on 2026-09-29 after the scientific and code review of 2026-09-28; the changes (old / new / reason / effect on
the conclusions) are listed in table T28. Every number below is resolved from a committed publication table cell
(`publication/tables/T*.csv`, manifest with sha256); claim identifiers [C01]–[C14] refer to `evidence_matrix.csv`; terms are frozen
in `TERMINOLOGY.md`. Figure and table identifiers are internal and are renumbered at typesetting. Numbers are printed from the
table cells at the stated precision with round-half-to-even; the cell keeps the full value.**

**Table T28.** What changed after the scientific and code review of 2026-09-28 (findings F01-F20) and the maintainer's decisions of 2026-09-29: per item the old and the new treatment or value, the reason, and the effect on the conclusion, ordered by the vertical frame of Paper 1 (taken as validated input) and then the evidence hierarchy (terrain reconstruction -> uncertainty -> independent validation / support -> weak-label ML -> release). New values are resolved from the table cells of this build; old values from the superseded rows the tables keep (T02c, T06, T07b, T08b, T09 rev 1) or from the dated records named in the evidence column. A revision record, not a result table. [mixed] *(25 of 52 rows and 9 of 9 columns shown; full table: publication/tables/T28.csv)*

| id | block | item | old | new | reason | impact_on_conclusion | review_ref | evidence |
|---|---|---|---|---|---|---|---|---|
| A01 | 0 vertical frame (Paper 1) | Vertical validation in the flood paper | the manuscript re-reported closure values of an earlier Pape | the vertical frame is the validated input of Paper 1 v6 (at  | the vertical frame is validated in Paper 1; the flood paper  | no conclusion changes; the Methods and Results no longer rep | maintainer 2026-09-30 | Paper 1 v6 Sec. 5, S1, S3.9 |
| A02 | 0 vertical frame (Paper 1) | Kherson gauge BS-77 -> EVRF2019 | +0.22 m (the table carried over from the extraction) | +0.2076 m, the EPSG:9902 step at the post's own coordinates  | every Kherson level stood 1.24 cm above Paper 1's | the anchor and cap of the water surface 1.24 cm lower; the r | Paper 1 v6 alignment | T11, T17, p59k |
| A03 | 0 vertical frame (Paper 1) | Reservoir SWOT outlet levels | wse + geoid_hght + free2mean - zeta + the tide-free closure  | Paper 1's production chain (no permanent-tide term for SWOT, | a superseded chain carried over from the extraction | pool levels +0.073 m; the 7 June effective release 40057 m3/ | Paper 1 v6 alignment | T21, p95f |
| A04 | 0 vertical frame (Paper 1) | G-REALM altimetry as a pool anchor | an anchor at 111 km, held for two days after each observatio | a plotted check only (Fig09a) | not part of Paper 1's frame; on 9 June 0.5 m above the Nikop | the daily release series no longer has the spurious peak | Paper 1 v6 alignment; check of 2026-09-30 | T21, Fig09 |
| A05 | 0 vertical frame (Paper 1) | Terrain and ICESat-2 ground in the vertical frame | Paper 2's chain: FABDEM and ICESat-2 ground converted with + | both raised by 0.0377 m to Paper 1's production chain (the s | the terrain sat 3.8 cm low against the water surface of Pape | the reconstruction recomputed (rev 7): the terrain is higher | Paper 1 v6 alignment (maintainer 2026-09-30) | T11, paper1_frame.py |
| A06 | 1 terrain reconstruction | Residual terrain model | the WorldCover class medians of one zone ('C seamless', ZONE | FABDEM-only residual table per zone and class (own zone wher | FABDEM is a bare-earth DTM; its statistics apply only where  | nominal A_new on 7 June 235.3 -> 214.8 km2, the whole nomina | F07; D-BIAS | T11h, T18b; ledger: reproduction gate |
| A07 | 1 terrain reconstruction | Connectivity across the zone boundary | ownership of the frame overlap applied before the connectivi | connectivity once on the union mosaic, ownership for account | a connection may cross the zone boundary (F06, D-SEAM) | none measurable on the real rasters; correct by construction | F06; D-SEAM | T11i; tests/test_terrain_connectivity.py |
| A08 | 1 terrain reconstruction | Error terms under the far gauge cap | the datum closure added twice on cells capped at the Kherson | every error term enters once, through the perturbed node hei | double count (F03) | part of the recomputed numbers; no separate effect on a clai | F03 | tests/test_p95_wse_field.py |
| A09 | 1 terrain reconstruction | Primary rule | command-line default hand_and_ceiling while the text named t | connected_ceiling is the default; every output carries its r | ambiguity (F07, D-RULE) | none on the numbers | F07; D-RULE | p95 manifest |
| A10 | 1 terrain reconstruction | Vertical frame | EVRF2019 assumed for every height | EVRF2019 asserted from the declarations of the terrain raste | an assumption made explicit (D-VERT) | none | D-VERT | floodstate_eo.terrain.vertical; tests |
| A11 | 1 terrain reconstruction | Depth maps | depth on 7-8 June only, as figure panels | maximum depth of the new inundation over the event (Fig07a;  | maintainer decision D-DEPTH | new results (nominal-world geometry, captioned so; areas and | D-DEPTH | T12e, T21b, Fig07, Fig10 |
| A12 | 1 terrain reconstruction | Reservoir drawdown maps | supplementary FigS08: modelled pool on 7/9/13 June and its d | main-text Fig11: Sentinel-2 water on 5/8/13/20 June (not obs | maintainer 2026-09-30: the maps showed no drawdown; the mode | the emptying is shown by the observation that separates wate | maintainer 2026-09-30 | Fig11, FigS08, T23, T23b |
| A13 | 1 terrain reconstruction | Nikopol level on 12-13 June | the 11 June level carried over 12-13 June, above the post's  | the bound caps 13 June and 12 June is interpolated towards i | a censored observation ignored by a forward fill | C14: the 13 June area, volume and depth are upper estimates | check of the drawdown maps 2026-09-30 | T21, T21b, p95f |
| A14 | 2 uncertainty | Monte-Carlo design | 40 draws; terrain field and water-surface errors regenerated | 1000 coherent worlds: one unit-variance terrain field over t | no coherent world, variance lost, arbitrary correlation, uns | C07 rewritten; the two seeds agree within a few km2 at n = 1 | F01, F02, F20; D-N; D-CORR | T11b, T11c, T18c; tests/test_p95e_contract.py |
| A15 | 2 uncertainty | Reconstructed newly inundated area, corridor, 7 June | 246.7 [237.6-254.9] km2 (40 draws) | 233.7 [216.0-253.7] km2 (Monte-Carlo median, p05-p95) | coherent ensemble (F01-F05, F20) | C01-C02 kept: the areal maximum stays on 7 June (38% of the  | F01-F05; F20 | T12, T12c; ledger: results of the recomputation (rev 5) |
| A16 | 2 uncertainty | Reconstructed total water-surface area, corridor, 7 June | 790.5 [781.4-798.7] km2: the new-area interval shifted onto  | 716.2 [685.9-743.6] km2 from the total-water ensemble itself | the total had no ensemble of its own (F04) | C02 kept; the interval is about three times wider | F04 | T12; ledger: results of the recomputation (rev 5) |
| A17 | 2 uncertainty | Reconstructed new-water volume, corridor, 7 June | 565.9 [545.4-595.7] hm3 (40 draws) | 602.6 [541.6-658.7] hm3 | coherent ensemble (F01-F05, F20) | C02, C07: volumes always with their interval, never centred  | F01-F05; F20 | T12; ledger: results of the recomputation (rev 5) |
| A18 | 2 uncertainty | Central value and the nominal run | nominal run reported next to the ensemble without an explana | Monte-Carlo median = reported value, nominal run = diagnosti | median shift unexplained; nominal-centred reporting (F20; te | C07 rewritten: no interval is centred on the nominal run | F20; C07; text pass | T11d, T12 |
| A19 | 2 uncertainty | Interpolation of the node series | one error scale from 1-day triplets; interpolation in both d | gap-matched cross-validation: NMAD 0.07 m for 1 day to 1.15  | long gaps and held ends under-described (F05, D-INTERP) | the 13 June upper tail is the interpolation term; the 3-day  | F05; D-INTERP | T11f, T11d, T12 |
| A20 | 2 uncertainty | 100 000-draw emulator | used for the total water-surface envelope and the headline | computational diagnostic outside the evidence path (T12d) | no connectivity; total built around the nominal total (D-EMU | no reported number rests on it | D-EMU | T12d |
| A21 | 2 uncertainty | Observational support of the new inundation | the full reconstruction reported without the distance of its | support classes per newly inundated cell: 8% of the corridor | support is structural, not only statistical (F07, D-SUPPORT) | C02 and C03 qualified; the full reconstruction stays the pri | F07; D-SUPPORT | T11k, T11l, FigS14 |
| A22 | 2 uncertainty | Nearest-node fallback distance | no distance limit, not quantified | a structural sensitivity: capped at 10 km, the corridor's ne | F07 | the structural dependence exceeds the Monte-Carlo width; sta | F07 | T12 sensitivity columns, FigS02 |
| A23 | 3 independent validation / support | Withheld gauges | no in-situ check outside Kherson; the Inhulets valley report | Kalynivske (80575) and Mykolaiv (98027) withheld as validati | the only in-situ test of the tributary and the western delta | C03 restricted: upper and central Inhulets weakly constraine | D-INHULETS | T17c-T17f, FigS15 |
| A24 | 3 independent validation / support | ICESat-2 class bias and the check | class bias calibrated and checked on the same night passes;  | pass hold-out (one pass, five folds, the two epochs): the S1 | not independent; mask error (F12) | C06 unchanged in substance; the epoch dependence of the delt | F12 | T15, T15b, T15c |
| A25 | 3 independent validation / support | Design hypsometry end points | design Table 19 clamped at its end points: 1443 km2 / 6.95 k | undefined (NaN) outside the table (bounded interpolation) | plateau artefact (F13) | C14 unchanged; the hypsometry gap is -9 % at 17.5 m | F13 | T22, FigS07; tests/test_terrain_interp.py |

## Abstract

**Background.** On 6 June 2023 the Kakhovka dam on the lower Dnipro was breached and the reservoir drained within days. The
flood below the dam has been described mainly from satellite water masks, whose areas depend on the sensor, the date and the
definition of "flooded", while two-dimensional hydraulic models of the event reproduce neither the observed stages nor their
timing without corrected bathymetry. We ask what the observed water surface itself, projected on the terrain, implies for the
inundation on every day of the event; how uncertain that is; what independent observations confirm or contradict; and what EO
flood models learn from weak labels of the same flood.

**Methods.** The study follows a hierarchy of evidence in which a lower level explains or diagnoses a higher one but never
overrides it. (1) An *observation-constrained terrain-connectivity reconstruction*: the daily water surface from SWOT
L2_HR_RiverSP node heights and the Kherson gauge, in the vertical frame validated in Paper 1 of this series (EVRF2019), is projected
on a seamless terrain–bed elevation model (the FABDEM
bare-earth DTM outside the surveyed channel, the surveyed bed inside); terrain below the surface is retained where it is
connected to the pre-event water network, and a same-rule pre-breach baseline separates the *reconstructed newly inundated
area* from the *reconstructed total water-surface area*; depth and volume follow from the same geometry. No momentum or
continuity equations are solved. (2) Its uncertainty: 1000 coherent
Monte-Carlo worlds, each with one terrain-error field whose covariance is fitted to FABDEM − ICESat-2 residuals and one
water-surface realization, the baseline rebuilt in every world; every newly inundated cell is classed by the distance of its
SWOT support. (3) Independent checks: two river gauges withheld from the reconstruction, Sentinel-1 dark-water masks on 11
dates with the disagreement decomposed by surface class and elevation, and night ICESat-2 ground heights with a pass hold-out of
the terrain bias. (4) Weak-label diagnostics: U-Net arms trained with three seeds each on the canonical weak-label ontology v004,
built after the operating threshold of its optical component was recalibrated out of fold and its post-event features were
removed.

**Results.** On 7 June 2023, 146 km² of land classified as dry before the breach
was newly inundated in the Dnipro corridor below the dam (Monte-Carlo median; p05–p95
132–166 km²). Separately, the
inundated area within the vegetated wetland complex increased by 114 km²
(93–135 km²);
the latter estimate is more sensitive to uncertainty in the pre-event wetland state, whereas the event inundation boundary across the
wetland showed strong spatial agreement with external satellite mapping. The aggregate newly inundated area under the former state
definition — every cell outside the pre-breach regime counted alike, not the sum of the two — is 234 km²
on 7 June and 239 km² on 8 June (216–254 and
186–263 km²), between the Sentinel-1 acquisitions of 6 June (partial) and
9 June; its maximum falls on 8 June, the day of the peak stage at Kherson, in
53% of the worlds and on 7 June in
38%. The reconstructed
total water-surface area rises from 439 km² in the pre-breach
regime to 716 km²
(686–744 km²),
the reconstructed new-water volume reaches 603 hm³
(542–659 hm³),
and the aggregate newly inundated area recedes to 143 km² on 13 June and
3 km² on 21 June. The maximum depth that the new inundation reached
has a median of 2.22 m and exceeds 2 m on
56% of the cells. Above the dam the pool fell from
18.8 km³ on 5 June to 4.2 km³ on 13 June, its mean depth from
8.8 m to 2.4 m, with a daily-mean effective release of
40057 m³ s⁻¹ on 7 June. 8%
of the corridor's new area on 7 June rests on water-surface support farther than 10 km, and structural choices of that kind move
the peak area by more than the Monte-Carlo width. The withheld Inhulets gauge shows the reconstructed surface
+9.50 m on 2023-06-06 too high while the backwater travelled up the tributary and its maximum
3 days early; at the withheld liman gauge the reconstructed western delta stands
-0.82 m on 2023-06-08 relative to the liman's maximum. The raw agreement with Sentinel-1 on 9 June is low (POD
0.26, FAR
0.58) and mechanistic:
169 km² of Sentinel-1 "new water" lie on normally-wet reed beds (a
submergence signal), 54 km² lie at least 5 m above the reconstructed
surface, where night ICESat-2 provides no evidence for a terrain bias large enough to explain them, and
112 km² allowed by the terrain are hidden from the radar under trees, reeds and
buildings. Under weak supervision, the treatment of pre-event reference water changed the learned flood representation
consistently across three seeds (13.8–48.8
km² less predicted flood on reference water), whereas an earlier effect of HAND on the cropland burden did not reproduce
(+1.0,
+7.6 and
-3.8 km²
across seeds).

**Conclusions.** Even with SWOT, the step from an observed water surface to a flood extent is not unique: it depends on the
terrain, on the water that was already there, on how far the surface is carried from its observations and on what the sensor
can see, and its uncertainty is dominated by structural rather than metric terms. The reconstruction gives the day-by-day
extent, depth and volume that discrete acquisitions cannot, with a stated interval and support; the withheld gauges locate where
a static reconstruction fails; the disagreement with Sentinel-1 maps where each source is blind; and weak-label models are
diagnostics of their labels, not flood maps. Every area is reported with its semantics.

**Keywords:** dam breach; inundation reconstruction; SWOT; terrain connectivity; Monte-Carlo uncertainty; ICESat-2; Sentinel-1;
weak supervision; Kakhovka

## 1. Introduction

The destruction of the Kakhovka dam on 6 June 2023 released the largest reservoir of the Dnipro cascade — 18.2 km³ at its normal retention level of 16.0 m, 19.8 km³ at the 16.76 m held on the eve of the breach (Vyshnevskyi et al. 2023) — into a ~90 km reach with a densely populated left bank, a reed-wetland delta and the Dnipro–Buh liman (Vyshnevskyi et al. 2023; Shumilova et al. 2025). Within days operational products reported the flooded *land*: about 620 km² over 6–9 June and about 180 km² on 13 June in the UNOSAT products relayed by OCHA (CEOBS 2023), figures that later studies cite (Yailymov et al. 2025). The published studies of the event are of three kinds. Satellite mappings give areas with their own definitions: Yailymov et al. (2025) map 473 km² of flooded land as of 9 June by land-cover class, 294 km² of it wetlands, against a pre-flood water map of 5 June; Zuo et al. (2024) follow the water-surface area at 300 m in Sentinel-3 OLCI scenes, which doubled within three days and was largest around 9 June; Monti et al. (2024) map the flooding along ~80 km of river with Sentinel-1 change detection; Jiao et al. (2025) use the event to test a Sentinel-1 flood-extraction method. Hydrodynamic models give scenario extents and stages: Kadam et al. (2024) obtain 823 km² and a peak of 3.6 × 10⁴ m³ s⁻¹ for a 300 m breach in HEC-RAS, and Agerbeek et al. (2024) ran a near-real-time model checked against ICEYE extents and geolocated photographs. Reservoir-side balances give the volume released: Yi et al. (2025) derive an initial breach flow of (5.7 ± 0.8) × 10⁴ m³ s⁻¹ and 20.4 ± 1.4 km³ lost in 30 days from gravimetry, altimetry and imagery; Shumilova et al. (2025) model about 16.4 km³ over two weeks.

The most direct observation of this flood is the water surface itself. Lehnigk et al. (2026) show with the daily SWOT water-surface elevations of the one-day calibration orbit — the data we use here — that two-dimensional outburst-flood simulations underestimate the observed peak stages by 5.8–6.1 m with globally available bathymetry and still by 1.4 m with geomorphologically corrected reservoir and channel bathymetry, and reproduce neither stage nor timing together; downstream stages reached 10–11 m by 8 June. Their question is whether a hydraulic model reproduces the observed stages. Ours is the converse: once the water surface is constrained by observations, what extent, depth and volume does it imply on every day, how unique is that answer, and where do the satellite flood masks and such a reconstruction disagree, and why? Terrain-based approaches that project a water surface or a mapped extent on a DEM — HAND (Rennó et al. 2008; Nobre et al. 2011), GeoFlood (Zheng et al. 2018), FwDET (Cohen et al. 2019) — are first-order products, not hydrodynamics: Johnson et al. (2019) find that a HAND-based method "does not accurately capture inundated cells" while it does highlight regions at risk. The static terrain-connectivity operator is established as well: c-HAND floods the cells whose elevation "is lower than the gage elevation" and which "are connected to the ocean" under "a static equilibrium assumption" (Wang et al. 2024), and flood-fill models retain terrain cells below an imposed water surface only when they are connected to the reference water network (Dale et al. 2026). The operator is therefore not our contribution. What this paper adds is its use with a spatially distributed, observation-constrained water surface H(x, y, t) from SWOT nodes and a gauge; a same-rule pre-breach baseline that separates new inundation from water that was already there; an uncertainty propagated through coherent realizations of the terrain and the water surface; and tests against gauges withheld from the reconstruction. Depth and extent from such a construction are sensitive to small vertical errors on low-relief floodplains, and because DEM error is spatially autocorrelated whereas accuracy statistics such as RMSE "assume error to [be] aspatial" (Hawker et al. 2018), it must be propagated with spatially correlated error realisations (Darnell et al. 2008; Le et al. 2026), not with independent noise.

Two well-known properties of satellite flood mapping make an independent reconstruction necessary. The area obtained by counting classified pixels is a *mapped* area, not an unbiased estimate of the true flooded area; the good-practice framework of Olofsson et al. (2014) requires an accuracy assessment "based on a sample of higher quality" reference data, which does not exist for this event. And a C-band dark-water rule does not see water under trees, between buildings or under emergent reeds: the backscatter of vegetated and urban targets with and without flood water "represents the biggest challenge for inundation detection" (Grimaldi et al. 2020), flood water under vegetation "could not be detected with the C-band Sentinel-1 SAR" in a paddy landscape (Singha et al. 2020), and detection beneath vegetation and in cities is "not yet satisfactory" (Shen et al. 2019; review of flooded vegetation in SAR: Tsyganskaya et al. 2018). Conversely, "smooth surfaces at the scale of the measuring wavelength and shadowed areas share almost identical scattering properties with water surfaces" (Shen et al. 2019) and sand returns backscatter as low as open water (Martinis et al. 2018), so smooth non-water surfaces and radar shadow can look like water; exclusion maps derived from SAR time series formalise where flood cannot be inferred from intensity (Zhao et al. 2021). A U-Net trained on labels derived from those masks inherits both limits (label errors in the training labels lower the performance of a segmentation model: Maiti et al. 2022; weak supervision for flood mapping: He et al. 2024); its accuracy against such labels is agreement, not truth, and an input that also builds the label is label leakage (Apicella et al. 2025).

We therefore structure the study as a hierarchy of evidence (Fig02) and report the results in the same order. (1) The **observation-constrained terrain-connectivity reconstruction** of the daily inundation — extent, depth and volume below the dam, and the drawdown of the reservoir above it — is the main axis; it is a daily reconstructed series, not a hydrodynamic model. (2) Its **uncertainty**: coherent Monte-Carlo worlds, the observational support of the water surface and the structural choices that lie outside the budget. (3) **Independent validation and support**: two gauges withheld from the reconstruction, Sentinel-1 per acquisition date with the disagreement explained by the surface context (RF20 land-cover classes, WorldCover, elevation above the surface), night ICESat-2 ground heights and the SWOT–gauge comparison of the input. (4) **Weak-label machine-learning diagnostics**: what U-Net arms trained on the canonical weak-label ontology learn, with three training seeds as the minimum unit of evidence. A lower level explains or diagnoses a higher one; it never overrides it. Three principles hold throughout: model numbers are agreement with weak reference labels, never flood-mapping accuracy; "not observed is not dry"; and every area carries its semantics — observed by Sentinel-1, mapped by the U-Net, reconstructed from terrain, or reported in the literature.

![Fig02](img/Fig02.jpg)

**Fig02 Evidence hierarchy.** Four levels, top = strongest: (1) the observation-constrained terrain-connectivity reconstruction (the validated water surface of Paper 1 — SWOT nodes and the Kherson gauge — over the seamless terrain–bed model, connectivity to the pre-event water network, a same-rule pre-event baseline; no momentum or continuity equations) and its uncertainty (1000 coherent Monte-Carlo worlds, SWOT support classes); (2) independent observations (two withheld gauges, Sentinel-1 per acquisition date, night ICESat-2 ground heights); (3) the surface context that explains their disagreement (RF20, WorldCover, elevation above the surface); (4) weak-label ML diagnostics (U-Net arms on the canonical labels v004, three training seeds). A lower level explains or diagnoses a higher one; it never overrides it.

This is Paper 3 of a series, and it rests on a vertical framework that is validated elsewhere. Paper 1 (Nikoriak et al. 2026)
brought gauges, ICESat-2, SWOT and the historical hydrography into one vertical frame, validated it through measured closure
residuals and cross-sensor tests, and used it to show how the former reservoir reorganised from a level pool into a sloping,
fragmented river; Paper 2 built the seamless terrain–bed model. Here the validated water-surface observations are the input:
the question is what inundation — extent, depth and volume, day by day — they imply once projected on the terrain, and how
uncertain that reconstruction is. The vertical validation is therefore not repeated; only the checks that this reconstruction
needs are reported (the support of the water surface, two withheld gauges and the propagated uncertainty). Paper 4 will
reconstruct the reservoir bowl on the historical bathymetry, resolving the hypsometry gap reported in §4.1.3, and Paper 5 will use
the daily surfaces presented here as the calibration target of a two-dimensional hydraulic model.

## 2. Study area and data

The study reach runs from the Kakhovka dam (46.78° N, 33.37° E) to the Dnipro–Buh liman (Fig01). Two frames on one 10 m lattice
carry the EO products: B1 (dam → Kherson) and B2 (Kherson delta); the terrain reconstruction runs on the 20 m zone grids of
Paper 2 (ZONE_4 dam-to-Kherson floodway, ZONE_2 Kherson delta), evaluated as one mosaic. The Inhulets tributary joins from the
north with its own regime. The Inhulets valley was included in the terrain-connectivity reconstruction over the full model domain;
its reconstructed new-water extent is displayed in full (Fig01, Fig07), but reported separately from the Dnipro-corridor total
because the tributary has distinct hydraulic behaviour and substantially weaker local water-surface support. The reporting
rectangles that separate its valley and the terrace fragments were fixed in Paper 2 before any result of this paper existed; they
split the accounting and mask nothing. A combined corridor + Inhulets total is given only date-matched, within each Monte-Carlo
world (T12f); the northern edge of the reconstruction domain cuts the valley, so its area is a lower bound. Table T01 lists every dataset with its role and evidence level:

![Fig01](img/Fig01.jpg)

**Fig01 Study area.** Lower Dnipro from the Kakhovka dam to the Dnipro–Buh liman: hillshade of the seamless DEM (Paper 2), terrain below 1 m (channels, lakes), frames B1 (dam → Kherson) and B2 (Kherson delta) on one 10 m lattice, the p42 terrain-eligible floodplain, the maximum extent of the reconstructed new water over the event (one layer for the Dnipro and the Inhulets), the reporting regions (dashed; the Inhulets valley is included in the reconstruction and reported separately, the two smaller rectangles are terrace fragments and the reach west of its mouth; they mask nothing), the northern edge of the reconstruction domain (dotted), SWOT RiverSP nodes (main stem vs tributaries and side channels), the Kherson gauge 80805, the withheld Inhulets validation gauge Kalynivske 80575 and the dam.

![Fig07](img/Fig07.jpg)

**Fig07 Event-scale spatial result below the dam.** (a) Maximum depth of the reconstructed new inundation over the event (26 May – 10 July; per cell, the largest daily depth), (b) depth on 8 June, one day after the areal maximum and without a full-coverage satellite scene of the corridor (SWOT observed the channel nodes that day), (c) number of days with new inundation. Depth = the reconstructed water surface minus the seamless terrain–bed model on new-inundation cells (connected-ceiling rule, the nominal world on the union mosaic: the geometry of one world, while the areas and volumes quoted as results come from the Monte-Carlo ensemble, T12; depth statistics per region in T12e). The Inhulets valley is shown in full; hatching marks cells whose water surface rests on weak (> 10 km) or cross-river support (p95l, FigS14) -- a statement of reliability, not a mask. Dashed: the reporting regions; dotted: the northern edge of the reconstruction domain, which cuts the Inhulets valley (its area is a lower bound); triangle: the withheld gauge Kalynivske 80575. Rasters derived from FABDEM through the seamless terrain–bed model (not redistributed).

**Table T12f.** Optional event-domain total: Dnipro corridor + Inhulets valley, DATE-MATCHED (summed within each coherent Monte-Carlo world of p95e and day, then the median [p05-p95]; draw 0 = nominal run, a diagnostic). The two regions stay reported separately (T12, T12b); their maxima fall on different days (corridor 7 June, Inhulets 9 June), so they are never added as maxima. [independent_physical] *(25 of 46 rows and 10 of 17 columns shown; full table: publication/tables/T12f.csv)*

| date | region | A_p05_km2 | A_p50_km2 | A_p95_km2 | A_central_km2 | W_total_p05_km2 | W_total_p50_km2 | W_total_p95_km2 | W_total_central_km2 |
|---|---|---|---|---|---|---|---|---|---|
| 2023-05-26 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 455.7 | 483.9 | 510.1 | 516.9 |
| 2023-05-27 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 450.6 | 479.0 | 505.1 | 513.8 |
| 2023-05-28 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 450.2 | 480.0 | 506.2 | 513.4 |
| 2023-05-29 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 457.1 | 486.1 | 512.4 | 522.1 |
| 2023-05-30 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 457.5 | 485.2 | 510.4 | 519.7 |
| 2023-05-31 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 452.8 | 482.5 | 508.5 | 515.8 |
| 2023-06-01 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 460.6 | 488.4 | 513.9 | 521.0 |
| 2023-06-02 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 465.1 | 492.5 | 517.9 | 526.8 |
| 2023-06-03 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 458.3 | 487.5 | 514.0 | 523.2 |
| 2023-06-04 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 419.9 | 450.9 | 479.3 | 470.6 |
| 2023-06-05 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 429.1 | 459.3 | 487.4 | 483.9 |
| 2023-06-06 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 174.2 | 186.7 | 200.7 | 167.2 | 673.5 | 690.2 | 708.1 | 692.2 |
| 2023-06-07 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 257.4 | 276.7 | 296.5 | 257.1 | 755.2 | 785.6 | 813.1 | 788.3 |
| 2023-06-08 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 232.5 | 285.8 | 311.3 | 273.0 | 718.0 | 785.6 | 835.5 | 804.5 |
| 2023-06-09 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 235.3 | 251.3 | 280.5 | 220.9 | 719.1 | 753.0 | 797.8 | 747.2 |
| 2023-06-10 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 223.7 | 244.5 | 292.6 | 207.2 | 675.7 | 738.3 | 806.3 | 733.7 |
| 2023-06-11 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 206.2 | 227.3 | 276.0 | 191.3 | 658.7 | 721.0 | 787.5 | 718.3 |
| 2023-06-12 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 185.8 | 206.0 | 254.3 | 171.1 | 637.3 | 699.6 | 766.8 | 697.8 |
| 2023-06-13 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 162.3 | 181.2 | 229.5 | 149.2 | 611.0 | 674.6 | 742.8 | 675.8 |
| 2023-06-14 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 131.8 | 152.8 | 199.3 | 121.3 | 580.5 | 645.6 | 714.7 | 647.7 |
| 2023-06-15 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 105.0 | 126.4 | 169.6 | 85.5 | 553.0 | 616.8 | 688.2 | 608.3 |
| 2023-06-16 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 82.9 | 99.8 | 141.5 | 70.0 | 528.5 | 591.1 | 655.9 | 592.5 |
| 2023-06-17 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 63.7 | 78.1 | 119.0 | 56.8 | 507.1 | 569.8 | 632.5 | 578.8 |
| 2023-06-18 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 44.1 | 55.5 | 95.5 | 44.0 | 483.8 | 546.0 | 610.0 | 564.7 |
| 2023-06-19 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 27.5 | 33.7 | 49.8 | 31.3 | 493.7 | 529.2 | 566.7 | 551.4 |

**Table T01.** Data inventory: acquisition dates, coverage of the Sentinel-1 observable domain, and the role of every dataset. [mixed] *(25 of 28 rows and 5 of 5 columns shown; full table: publication/tables/T01.csv)*

| dataset | date | detail | coverage_of_observable_domain | evidence_level |
|---|---|---|---|---|
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-01 | orb65_DES | 1.0 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-02 | orb87_ASC | 0.951 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-06 | orb138_DES | 0.619 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-09 | orb14_ASC | 0.938 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-13 | orb65_DES | 1.0 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-14 | orb87_ASC | 0.951 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-18 | orb138_DES | 0.618 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-21 | orb14_ASC | 0.937 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-25 | orb65_DES | 1.0 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-26 | orb87_ASC | 0.952 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-30 | orb138_DES | 0.619 | cross_sensor |
| Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0) | 2023-06-05 | B1 | 0.33 | cross_sensor |
| Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0) | 2023-06-18 | B1,B2 | 0.69 | cross_sensor |
| Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0) | 2023-06-23 | B1,B2 | 0.527 | cross_sensor |
| Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0) | 2023-06-28 | B1,B2 | 0.648 | cross_sensor |
| Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0) | 2023-06-30 | B1 | 0.376 | cross_sensor |
| Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0) | 2023-07-03 | B1,B2 | 0.912 | cross_sensor |
| Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0) | 2023-07-08 | B1,B2 | 0.808 | cross_sensor |
| Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0) | 2023-08-04 | B1 | 0.324 | cross_sensor |
| Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0) | 2023-08-07 | B1,B2 | 0.707 | cross_sensor |
| Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0) | 2023-08-17 | B1,B2 | 0.778 | cross_sensor |
| Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0) | 2023-08-27 | B1,B2 | 0.974 | cross_sensor |
| SWOT L2_HR_RiverSP v2.0 nodes (1-day orbit), accepted | 2023-05-26..2023-07-10 | 42 days, 732 nodes/day median |  | independent_physical |
| Kherson gauge 80805 (river yearbook), daily | 2023-05-25..2023-07-10 | 47 days; BS77 -> EVRF2019 +0.22 m; 6-12 June flagged in the  |  | independent_physical |
| S1 reference scenes 2023-04-15..05-28 (May reference water,  | 2023-04-15..2023-05-28 | 30 admitted of 30 scenes (variant A QA) |  | cross_sensor |

- **SWOT** L2_HR_RiverSP v2.0 nodes on the one-day calibration orbit (Biancamaria et al. 2016), 26 May–10 July 2023, 42 days, 732 nodes/day median;
  node_q ≤ 1 and dark fraction < 0.5 as in Paper 1. Published comparisons place SWOT river heights at the centimetre-to-decimetre level against gauges and altimetric references (RMSE 0.02 m against Hydroweb-next on the Congo, Normandin et al. 2024; a global river error below 0.15 m, Yu et al. 2024), which is why the product's own node uncertainty wse_u (median 0.092 m here) is used as the per-node term of the Monte-Carlo (§3.4).
- **River gauges** of the 2023 yearbooks, daily, in the EVRF2019 frame of Paper 1: **Kherson 80805** (the input and anchor of the
  water surface; river-yearbook values through the recorder failure of 6 June – 8 July, as in Paper 1) and, withheld from the
  reconstruction as validation sites, **Inhulets – Kalynivske 80575** and **Southern Bug – Mykolaiv 98027** (the liman) (§3.6).
- **Seamless terrain–bed elevation model** (Paper 2): the kriged bathymetric bed inside the pre-breach water polygons and FABDEM v1.2 elsewhere — a bare-earth DTM derived from the Copernicus DEM with buildings and forests removed by machine learning (Hawker et al. 2022; the removal reduces the mean absolute vertical error in built-up areas from 1.61 to 1.12 m) — on one 20 m grid in EVRF2019, with a source mask that records which cells are FABDEM and which are bed; the reconstruction refuses an input that does not declare its vertical frame (§3.2). HAND from the p42 workflow (FABDEM floored at the 1 m river level, WhiteboxTools) enters a rule sensitivity and one U-Net arm.
- **Night ICESat-2 ATL08 ground segments** (2019–2025, Paper 2 chain) give the terrain accuracy by land-cover class (T18; robust
  statistics after Höhle and Höhle 2009): RMSE
  1.04 m, NMAD
  0.39 m over
  841752 segments, with trees the worst class;
  on the FABDEM cells they calibrate the residual class bias and the terrain-error covariance of the Monte-Carlo (§3.4).
- **Sentinel-1** (Torres et al. 2012) GRD, radiometrically terrain-corrected (Small 2011), eleven acquisitions 1–30 June 2023 (orbits 14, 65, 87, 138), per-scene dark-water masks (M3 rule of
  Paper 1's water classifier, 20 m); orbit-138 dates cover 62 % of the observable domain. Orbit-matched dB change channels (p71)
  are the U-Net inputs. A second set of thirteen reference scenes (15 April–28 May 2023) defines recurrent May water.
- **Sentinel-2** L2A scenes (Sen2Cor processing, Main-Knorn et al. 2017) as index stacks per date at 10 m — NDWI (McFeeters 1996), MNDWI (Xu 2006), NDVI (Tucker 1979), NDMI (Gao 1996), BSI (Rikimaru et al. 2002, Tropical Ecology 43, 39–47), AWEIsh (Feyisa et al. 2014) and the turbidity index NDTI (Lacaux et al. 2007) — and window composites: PRE (2022-01-01 … 2023-06-05), EVENT (2023-06-07 … 07-31) and TRACE (2023-08-01 … 11-30); the post-event TRACE window is not used by the canonical weak labels (§3.8).
- **ESA WorldCover 2021** (10 m): the training reference of the RF20 surface classes and the classes of the disagreement ontology.
- **Reservoir**: pool levels from the SWOT outlet nodes, the Nikopol post (press values) and the Rozumivka gauge; the DniproHES
  release as inflow; the design level–area–volume table of the reservoir monograph (Table 19; T27).

**Table T18.** Seamless terrain-bed model accuracy against night ICESat-2 ground segments (Paper 2 / p57): RMSE, MAE, bias, median, LE90, LE95, NMAD by zone and WorldCover class, all sources together (context; the uncertainty model uses the FABDEM-only rows of T18b). [independent_physical] *(16 of 16 rows and 10 of 12 columns shown; full table: publication/tables/T18.csv)*

| set | N | RMSE | MAE | bias | median | LE90 | LE95 | NMAD | product |
|---|---|---|---|---|---|---|---|---|---|
| C seamless DEM (p55) -- ALL night points (land below dam + e | 841752 | 1.044 | 0.495 | 0.266 | 0.085 | 1.033 | 1.773 | 0.39 | C |
| C seamless, ZONE_2_KHERSON_DELTA | 153342 | 1.11 | 0.458 | 0.199 | -0.002 | 0.982 | 1.655 | 0.299 | C |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover trees | 8066 | 3.024 | 2.085 | 1.952 | 1.481 | 4.741 | 6.169 | 1.603 | C |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover grass | 29227 | 1.329 | 0.653 | 0.372 | 0.107 | 1.422 | 2.22 | 0.491 | C |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover cropland | 95454 | 0.408 | 0.198 | -0.035 | -0.059 | 0.404 | 0.537 | 0.195 | C |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover built | 7850 | 1.901 | 0.818 | 0.252 | 0.151 | 1.764 | 2.581 | 0.696 | C |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover bare | 287 | 3.375 | 1.969 | -0.819 | -0.574 | 4.621 | 9.297 | 1.188 | C |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover wetland | 12409 | 1.131 | 0.675 | 0.437 | 0.509 | 1.244 | 1.552 | 0.477 | C |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY | 476545 | 1.125 | 0.551 | 0.408 | 0.225 | 1.153 | 2.017 | 0.385 | C |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover trees | 30020 | 2.929 | 2.19 | 2.079 | 1.693 | 4.639 | 5.791 | 1.715 | C |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover grass | 98908 | 1.524 | 0.85 | 0.676 | 0.385 | 1.867 | 2.784 | 0.622 | C |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover cropl | 307176 | 0.363 | 0.268 | 0.157 | 0.151 | 0.54 | 0.672 | 0.296 | C |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover built | 15288 | 1.517 | 0.691 | 0.227 | 0.17 | 1.47 | 2.09 | 0.597 | C |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover bare | 3525 | 1.42 | 0.903 | 0.309 | 0.307 | 1.852 | 2.388 | 0.935 | C |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover wetla | 21543 | 1.239 | 0.764 | 0.577 | 0.584 | 1.304 | 1.729 | 0.416 | C |
| C seamless, low terrain (< 5 m) incl. exposed bed | 81853 | 0.862 | 0.635 | 0.357 | 0.344 | 1.367 | 1.782 | 0.686 | C |

**Table T27.** Design hypsometry of the Kakhovka reservoir from the Dnipro-reservoirs monograph (Table 19, Figs 13-15; transcribed from photographed pages in SWOT-DNIPRO): water level (historical Baltic, and +0.185 m to EVRF2019), surface area and volume of the whole pool and of the five reaches (dam - Babyne - Nikopol - Verkhnia Tarasivka - Blahovishchenka - Dnipro HPP) at 17 levels, with the design levels (NUF highest forced 17.5, NPG normal impoundment 16.0, UNS navigation drawdown 14.0, GMO dead volume 12.7 m) and the transcription check that the reaches add up to the total. Design data as published; nothing measured or fitted here. FigS10. [contextual] *(17 of 17 rows and 10 of 12 columns shown; full table: publication/tables/T27.csv)*

| level_bs_m | level_evrf2019_m | A_km2 | V_km3 | design_level | V_reach1_km3 | V_reach2_km3 | V_reach3_km3 | V_reach4_km3 | V_reach5_km3 |
|---|---|---|---|---|---|---|---|---|---|
| 18.0 | 18.185 | 2222 | 22.57 |  |  |  |  |  |  |
| 17.5 | 17.685 | 2205 | 21.46 | NUF - highest forced level |  |  |  |  |  |
| 17.0 | 17.185 | 2188 | 20.36 |  |  |  |  |  |  |
| 16.5 | 16.685 | 2172 | 19.27 |  | 6.9 | 5.64 | 2.79 | 3.56 | 0.38 |
| 16.0 | 16.185 | 2155 | 18.19 | NPG - normal impoundment level | 6.65 | 5.38 | 2.6 | 3.21 | 0.35 |
| 15.5 | 15.685 | 2133 | 17.12 |  | 6.4 | 5.12 | 2.42 | 2.86 | 0.32 |
| 15.0 | 15.185 | 2110 | 16.06 |  | 6.16 | 4.85 | 2.24 | 2.52 | 0.29 |
| 14.5 | 14.685 | 2077 | 15.01 |  | 5.92 | 4.59 | 2.06 | 2.18 | 0.26 |
| 14.0 | 14.185 | 2041 | 13.98 | UNS - navigation drawdown level | 5.68 | 4.32 | 1.88 | 1.87 | 0.23 |
| 13.5 | 13.685 | 1984 | 12.98 |  | 5.44 | 4.06 | 1.71 | 1.57 | 0.2 |
| 13.0 | 13.185 | 1916 | 12.0 |  | 5.2 | 3.8 | 1.55 | 1.27 | 0.18 |
| 12.7 | 12.885 | 1876 | 11.44 | GMO - dead-volume level | 5.06 | 3.65 | 1.45 | 1.12 | 0.16 |
| 12.0 | 12.185 | 1774 | 10.15 |  | 4.73 | 3.29 | 1.22 | 0.78 | 0.13 |
| 11.5 | 11.685 | 1693 | 9.28 |  | 4.5 | 3.03 | 1.06 | 0.58 | 0.11 |
| 11.0 | 11.185 | 1613 | 8.46 |  | 4.28 | 2.78 | 0.92 | 0.4 | 0.09 |
| 10.5 | 10.685 | 1528 | 7.67 |  | 4.04 | 2.52 | 0.78 | 0.26 | 0.07 |
| 10.0 | 10.185 | 1443 | 6.95 |  | 3.82 | 2.27 | 0.65 | 0.15 | 0.06 |

## 3. Methods

### 3.1 Evidence hierarchy, area semantics and the result blocks

The four levels of Fig02 fix what each kind of evidence may claim. The terrain reconstruction (level 1) and its uncertainty
produce the reported areas, depths and volumes; independent observations (level 2) check them and never enter them; the surface
context (level 3) explains where the reconstruction and the sensors disagree; weak-label models (level 4) show what EO inputs
recover and are scored only against weak labels. Every table carries its evidence level (independent_physical, cross_sensor,
contextual or weak_label_agreement), and the Results follow the same order in four blocks (§4.1–§4.4). Every area in this paper
is one of: observed_S1 (dark water on that date minus pre-breach water and minus cells already dark on 1–2 June), mapped_UNet (score above the frozen threshold),
terrain_reconstructed (allowed by the water surface and connectivity, outside the normal regime) or literature_reported (an
operational figure with its own AOI, date and reference water; context, never validation). No probability-sample reference
exists, so none of them is an unbiased estimate of the true flooded area (Olofsson et al. 2014).

### 3.2 The validated vertical frame, the daily water surface and its support

*The vertical frame is an input.* Every height in this paper is in the vertical reference framework that Paper 1 established and
validated: gauge stages are carried from BS-77 into EVRF2019 by the EPSG:9902 grid step at each post's own coordinates, satellite
heights are EGG2015-referenced heights (SWOT h = wse + geoid_hght; ICESat-2 with the permanent-tide term restored), and the two
branches are joined by a measured local closure residual c = gauge − satellite. Paper 1 tests this framework — the gauge
transformation, the closure residuals at the reservoir gauges and at Kherson, the agreement of SWOT and ICESat-2 and the Kherson
record through the breach fortnight — and those tests are not repeated here. At Kherson the SWOT RiverSP closure residual is
+1.3 cm [−0.7, +2.7] (Paper 1), indistinguishable from zero, so the water surface takes c = 0.00 m with σ = 0.05 m; the gauge
enters at its EPSG:9902 step of 0.208 m. The FABDEM part of the
terrain model and the night ICESat-2 ground heights of Paper 2 are brought into the same production chain: they are raised by
0.038 m, the difference between the tide-free closure they had been paired
with and the production closure of Paper 1 (the surveyed bed came through the gauge branch and is unchanged). What remains of
the vertical uncertainty — the closure, the SWOT node heights, the gauge and the interpolation between observations — is
propagated through the reconstruction (§3.4).

*The daily water surface.* For every node H = wse + geoid_hght − ζ_EGG2015 + c_Kherson. The SWORD chainage distributed with the
nodes is not comparable across branches (the Inhulets reaches, the Kokan' channel and the side channels at Kherson start
their own counts), so the water surface is built without chainage: each cell takes the median height of its five nearest
nodes within 3 km on the day, each node is interpolated in time between its own observations, the gauge enters as one more
node at its coordinates, and cells farther than 15 km from any node and west of the gauge are capped at the gauge level. A node
is held at its first and last observation beyond them, and a cell without a node within 3 km takes the nearest node of the day:
on 7 June 369 km² of the reconstructed water surface take their height from
nodes within 3 km and 349 km² from the nearest node farther away (T11g; the
observed / interpolated / held flags of every node-day are kept and enter the uncertainty budget, §3.4). Each newly inundated
cell is also classed by the distance of its nearest SWOT node: *direct* (≤ 3 km, the surface is observed around the cell),
*extrapolated* (3–10 km) or *weak* (> 10 km, weakly constrained), with two independent flags — capped at the Kherson gauge, and,
in the Inhulets valley, served by a node of another river (*cross-river*). The 3 and 10 km limits are operational thresholds,
not physical constants: the full reconstruction remains the primary product, its *supported core* (direct + extrapolated) is
reported next to it (T11k, T11l, FigS14), and a run with no surface from nodes farther than 10 km is a separate sensitivity.

![FigS14](img/FigS14.jpg)

**FigS14 Observational support of the terrain-connectivity reconstruction (D-SUPPORT).** (a) Newly inundated area on 7 June 2023 (nominal run) coloured by the distance of its nearest SWOT node: direct (≤ 3 km), extrapolated (3–10 km), weak (> 10 km); cross-river: cells of the Inhulets valley served by a node of another river. SWOT nodes (grey; Inhulets green), the Kherson gauge (input and anchor) and the two withheld gauges Kalynivske and Mykolaiv. (b) Daily new area of the Dnipro corridor: full reconstruction (the primary product), supported core (≤ 10 km), direct part, and the run without surfaces from nodes farther than 10 km (a sensitivity that also changes the connectivity). (c) Share of the new area with weak support per region. The 3 and 10 km limits are operational thresholds, not physical constants (T11k, T11l).

**Table T11g.** Support of the reconstructed water surface on the key dates: share of the corridor base cells whose surface is the median of nodes within 3 km, the nearest-node fallback beyond 3 km, or capped at the Kherson gauge (> 15 km from a node, west of the gauge), with the water cells in each class, and the number of SWOT nodes observed / interpolated / held at an end on the day. [independent_physical] *(25 of 48 rows and 10 of 13 columns shown; full table: publication/tables/T11g.csv)*

| date | support_kind | km2 | share_of_corridor_base | km2_water | km2_gauge_capped | n_nodes | n_observed | n_interpolated | n_held |
|---|---|---|---|---|---|---|---|---|---|
| 2023-06-05 | nodes_within_3km | 644.1 | 0.1353 | 264.1 | 0.0 | 777 | 749 | 26 | 2 |
| 2023-06-05 | nearest_node_fallback | 4116.8 | 0.8647 | 197.2 | 1404.2 | 777 | 749 | 26 | 2 |
| 2023-06-05 | no_water_surface | 0.0 | 0.0 | 0.0 | 0.0 | 777 | 749 | 26 | 2 |
| 2023-06-06 | nodes_within_3km | 644.1 | 0.1353 | 348.2 | 0.0 | 777 | 639 | 138 | 0 |
| 2023-06-06 | nearest_node_fallback | 4116.8 | 0.8647 | 281.7 | 1404.2 | 777 | 639 | 138 | 0 |
| 2023-06-06 | no_water_surface | 0.0 | 0.0 | 0.0 | 0.0 | 777 | 639 | 138 | 0 |
| 2023-06-07 | nodes_within_3km | 644.1 | 0.1353 | 369.3 | 0.0 | 777 | 355 | 422 | 0 |
| 2023-06-07 | nearest_node_fallback | 4116.8 | 0.8647 | 349.4 | 1404.2 | 777 | 355 | 422 | 0 |
| 2023-06-07 | no_water_surface | 0.0 | 0.0 | 0.0 | 0.0 | 777 | 355 | 422 | 0 |
| 2023-06-08 | nodes_within_3km | 644.1 | 0.1353 | 370.9 | 0.0 | 777 | 353 | 424 | 0 |
| 2023-06-08 | nearest_node_fallback | 4116.8 | 0.8647 | 359.9 | 1404.2 | 777 | 353 | 424 | 0 |
| 2023-06-08 | no_water_surface | 0.0 | 0.0 | 0.0 | 0.0 | 777 | 353 | 424 | 0 |
| 2023-06-09 | nodes_within_3km | 644.1 | 0.1353 | 365.2 | 0.0 | 777 | 674 | 103 | 0 |
| 2023-06-09 | nearest_node_fallback | 4116.8 | 0.8647 | 305.1 | 1404.2 | 777 | 674 | 103 | 0 |
| 2023-06-09 | no_water_surface | 0.0 | 0.0 | 0.0 | 0.0 | 777 | 674 | 103 | 0 |
| 2023-06-10 | nodes_within_3km | 644.1 | 0.1353 | 358.7 | 0.0 | 777 | 615 | 162 | 0 |
| 2023-06-10 | nearest_node_fallback | 4116.8 | 0.8647 | 300.3 | 1404.2 | 777 | 615 | 162 | 0 |
| 2023-06-10 | no_water_surface | 0.0 | 0.0 | 0.0 | 0.0 | 777 | 615 | 162 | 0 |
| 2023-06-11 | nodes_within_3km | 644.1 | 0.1353 | 351.8 | 0.0 | 777 | 657 | 120 | 0 |
| 2023-06-11 | nearest_node_fallback | 4116.8 | 0.8647 | 294.5 | 1404.2 | 777 | 657 | 120 | 0 |
| 2023-06-11 | no_water_surface | 0.0 | 0.0 | 0.0 | 0.0 | 777 | 657 | 120 | 0 |
| 2023-06-12 | nodes_within_3km | 644.1 | 0.1353 | 347.1 | 0.0 | 777 | 746 | 31 | 0 |
| 2023-06-12 | nearest_node_fallback | 4116.8 | 0.8647 | 281.8 | 1404.2 | 777 | 746 | 31 | 0 |
| 2023-06-12 | no_water_surface | 0.0 | 0.0 | 0.0 | 0.0 | 777 | 746 | 31 | 0 |
| 2023-06-13 | nodes_within_3km | 644.1 | 0.1353 | 341.2 | 0.0 | 777 | 714 | 63 | 0 |

**Table T11k.** Observational support of the reconstructed new inundation (nominal run of the primary rule; maintainer decision D-SUPPORT): per region and key date the FULL terrain-connectivity reconstruction (the primary product), its DIRECT (nearest SWOT node <= 3 km), EXTRAPOLATED (3-10 km) and WEAK (> 10 km) parts, the SUPPORTED CORE (<= 10 km), the weak share, the parts capped at the Kherson gauge and, in the Inhulets valley, served by a node of another river (cross-river flag), and the 10 km cap run of p95 as a sensitivity (it recomputes the connectivity; it is not the core). The 3 and 10 km limits are operational thresholds, not physical constants. [independent_physical] *(25 of 42 rows and 10 of 12 columns shown; full table: publication/tables/T11k.csv)*

| date | region | A_full_km2 | A_direct_km2 | A_extrapolated_km2 | A_weak_km2 | A_core_le10km_km2 | share_weak | A_gauge_capped_km2 | A_cross_river_km2 |
|---|---|---|---|---|---|---|---|---|---|
| 2023-06-06 | DNIPRO_CORRIDOR | 132.14 | 59.73 | 68.86 | 3.55 | 128.59 | 0.0269 | 0.0 |  |
| 2023-06-06 | INHULETS_VALLEY_rect | 35.02 | 0.31 | 1.91 | 32.79 | 2.23 | 0.9364 | 0.0 | 11.01 |
| 2023-06-06 | P42_FLOODPLAIN_DOMAIN | 107.09 | 53.68 | 52.9 | 0.51 | 106.58 | 0.0047 | 0.0 |  |
| 2023-06-07 | DNIPRO_CORRIDOR | 214.86 | 80.45 | 118.16 | 16.25 | 198.61 | 0.0756 | 0.0 |  |
| 2023-06-07 | INHULETS_VALLEY_rect | 42.26 | 0.45 | 2.67 | 39.15 | 3.12 | 0.9263 | 0.0 | 11.26 |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | 170.54 | 67.71 | 92.74 | 10.08 | 160.46 | 0.0591 | 0.0 |  |
| 2023-06-08 | DNIPRO_CORRIDOR | 226.61 | 81.68 | 130.29 | 14.63 | 211.97 | 0.0646 | 0.0 |  |
| 2023-06-08 | INHULETS_VALLEY_rect | 46.39 | 0.58 | 3.21 | 42.6 | 3.79 | 0.9184 | 0.0 | 10.83 |
| 2023-06-08 | P42_FLOODPLAIN_DOMAIN | 181.11 | 67.54 | 104.44 | 9.14 | 171.98 | 0.0504 | 0.0 |  |
| 2023-06-09 | DNIPRO_CORRIDOR | 171.26 | 75.71 | 88.03 | 7.51 | 163.74 | 0.0439 | 0.0 |  |
| 2023-06-09 | INHULETS_VALLEY_rect | 49.59 | 0.7 | 3.73 | 45.16 | 4.43 | 0.9106 | 0.0 | 10.34 |
| 2023-06-09 | P42_FLOODPLAIN_DOMAIN | 124.65 | 60.81 | 63.1 | 0.74 | 123.91 | 0.006 | 0.0 |  |
| 2023-06-10 | DNIPRO_CORRIDOR | 159.79 | 69.02 | 82.08 | 8.7 | 151.1 | 0.0544 | 0.0 |  |
| 2023-06-10 | INHULETS_VALLEY_rect | 47.41 | 0.65 | 3.41 | 43.36 | 4.06 | 0.9144 | 0.0 | 9.75 |
| 2023-06-10 | P42_FLOODPLAIN_DOMAIN | 118.38 | 56.76 | 60.79 | 0.82 | 117.55 | 0.007 | 0.0 |  |
| 2023-06-11 | DNIPRO_CORRIDOR | 146.55 | 62.01 | 78.1 | 6.43 | 140.11 | 0.0439 | 0.0 |  |
| 2023-06-11 | INHULETS_VALLEY_rect | 44.71 | 0.58 | 2.92 | 41.22 | 3.5 | 0.9218 | 0.0 | 8.98 |
| 2023-06-11 | P42_FLOODPLAIN_DOMAIN | 111.87 | 51.69 | 59.47 | 0.71 | 111.16 | 0.0064 | 0.0 |  |
| 2023-06-12 | DNIPRO_CORRIDOR | 129.54 | 57.22 | 68.43 | 3.89 | 125.65 | 0.03 | 0.0 |  |
| 2023-06-12 | INHULETS_VALLEY_rect | 41.6 | 0.51 | 2.57 | 38.52 | 3.08 | 0.9261 | 0.0 | 7.93 |
| 2023-06-12 | P42_FLOODPLAIN_DOMAIN | 102.04 | 48.32 | 53.13 | 0.59 | 101.45 | 0.0058 | 0.0 |  |
| 2023-06-13 | DNIPRO_CORRIDOR | 112.15 | 51.28 | 59.02 | 1.85 | 110.3 | 0.0165 | 0.0 |  |
| 2023-06-13 | INHULETS_VALLEY_rect | 37.01 | 0.44 | 2.19 | 34.38 | 2.62 | 0.9291 | 0.0 | 6.31 |
| 2023-06-13 | P42_FLOODPLAIN_DOMAIN | 91.49 | 44.31 | 46.81 | 0.37 | 91.12 | 0.0041 | 0.0 |  |
| 2023-06-14 | DNIPRO_CORRIDOR | 90.07 | 44.29 | 44.77 | 1.01 | 89.06 | 0.0112 | 0.0 |  |

**Table T11l.** The support classes of T11k with their flags and the median distance of the serving node, per region and key date. [independent_physical] *(25 of 138 rows and 8 of 8 columns shown; full table: publication/tables/T11l.csv)*

| date | region | support | gauge_capped | cross_river | new_km2 | node_km_median | share_of_new |
|---|---|---|---|---|---|---|---|
| 2023-06-06 | DNIPRO_CORRIDOR | direct | False |  | 59.73 | 1.2121323279115526 | 0.452 |
| 2023-06-06 | DNIPRO_CORRIDOR | extrapolated | False |  | 68.86 | 6.681046656193996 | 0.5211 |
| 2023-06-06 | DNIPRO_CORRIDOR | weak | False |  | 3.55 | 10.474558053313336 | 0.0269 |
| 2023-06-06 | INHULETS_VALLEY_rect | direct | False | False | 0.31 | 1.8121925010810789 | 0.009 |
| 2023-06-06 | INHULETS_VALLEY_rect | extrapolated | False | False | 1.31 | 7.340343492157582 | 0.0373 |
| 2023-06-06 | INHULETS_VALLEY_rect | extrapolated | False | True | 0.61 | 4.79203985178481 | 0.0173 |
| 2023-06-06 | INHULETS_VALLEY_rect | weak | False | False | 22.39 | 30.20337479849561 | 0.6393 |
| 2023-06-06 | INHULETS_VALLEY_rect | weak | False | True | 10.4 | 40.19942466457319 | 0.297 |
| 2023-06-06 | P42_FLOODPLAIN_DOMAIN | direct | False |  | 53.68 | 1.2188073143974931 | 0.5013 |
| 2023-06-06 | P42_FLOODPLAIN_DOMAIN | extrapolated | False |  | 52.9 | 6.214021725988421 | 0.494 |
| 2023-06-06 | P42_FLOODPLAIN_DOMAIN | weak | False |  | 0.51 | 10.226392616167502 | 0.0047 |
| 2023-06-07 | DNIPRO_CORRIDOR | direct | False |  | 80.45 | 1.3835660743972027 | 0.3744 |
| 2023-06-07 | DNIPRO_CORRIDOR | extrapolated | False |  | 118.16 | 6.727191484615815 | 0.5499 |
| 2023-06-07 | DNIPRO_CORRIDOR | weak | False |  | 16.25 | 11.133307850619763 | 0.0756 |
| 2023-06-07 | INHULETS_VALLEY_rect | direct | False | False | 0.45 | 1.8469005931401192 | 0.0106 |
| 2023-06-07 | INHULETS_VALLEY_rect | extrapolated | False | False | 1.98 | 7.242019235157073 | 0.0468 |
| 2023-06-07 | INHULETS_VALLEY_rect | extrapolated | False | True | 0.69 | 4.820373820947019 | 0.0163 |
| 2023-06-07 | INHULETS_VALLEY_rect | weak | False | False | 28.58 | 32.5911038439511 | 0.6763 |
| 2023-06-07 | INHULETS_VALLEY_rect | weak | False | True | 10.57 | 40.18586603557991 | 0.25 |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | direct | False |  | 67.71 | 1.3556917896496758 | 0.3971 |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | extrapolated | False |  | 92.74 | 6.275558525638603 | 0.5438 |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | weak | False |  | 10.08 | 11.057985741918698 | 0.0591 |
| 2023-06-08 | DNIPRO_CORRIDOR | direct | False |  | 81.68 | 1.38144733017172 | 0.3605 |
| 2023-06-08 | DNIPRO_CORRIDOR | extrapolated | False |  | 130.29 | 6.754295174754575 | 0.575 |
| 2023-06-08 | DNIPRO_CORRIDOR | weak | False |  | 14.63 | 10.966757836804108 | 0.0646 |

### 3.3 Terrain-connectivity rule, pre-breach baseline, depth and volume

The reconstruction is a static terrain-connectivity model rather than a dynamic hydraulic simulation. Gravitational control is
represented implicitly through the terrain elevation relative to the imposed water-surface elevation and through topographic
connectivity; the method does not solve momentum or continuity equations and therefore does not represent finite flood-wave
propagation, frictional losses or transient backwater dynamics (§5). The inundation operator follows the static
terrain-connectivity principle of topography-based flood mapping such as c-HAND (Wang et al. 2024) and the flood-fill procedure
of Dale et al. (2026): terrain cells below the imposed water surface are retained only when topographically connected to the
reference water network. Here this principle is applied with a spatially distributed, observation-constrained water surface
H(x, y, t) derived from the SWOT nodes and the gauge, with a same-rule pre-breach baseline that separates new inundation from
pre-existing water, and a propagated uncertainty (§3.4).

A cell is water on day t if its terrain lies below the water surface and it is 8-connected, through such cells, to the
**pre-breach river network** — the largest connected component of the pre-breach optical water map (p60 pre-water frequency
≥ 20 %): the Dnipro from the dam to the liman with its delta and side channels, the Inhulets and the Kokan' — within 10 km of
pre-breach water and downstream of the dam (*connected ceiling*, the primary rule; decision D-SEED). The event source is the
river network, not every pre-existing water body: seeding the connectivity from all pre-breach water cells — the earlier form
of this rule, kept as the provenance variant *all-prewater seeding* (T12, T13, FigS16) — let a few pond and canal cells "flood"
42 km² of WorldCover cropland on the left-bank sandy
terrace under the Kokan' level extrapolated 14 km, with no terrain path to the river on any day (§4.2.3) — the case that
terrain-index methods list as their limitation (Zheng et al. 2018) and that the connectivity requirement exists to exclude. The
pre-breach water maps of the two frames are composed where each frame has labels, so that the network is one graph across the
zone boundary (a 30 m strip without labels at the boundary had split it in two at Kherson). Water that entered a depression
while it was connected and stays after the connection is lost is not held by a static rule; a *memory* variant — a cell
inundated on day t − 1 stays inundated on day t while it is still below the surface, a storage hypothesis without infiltration
or drainage — is reported as a sensitivity and never as the primary (D-MEMORY; §4.2.4, T11p). Two other rules bracket it: the p42 rule (additionally HAND < WSE − 1 m, channel-connected through the mapped drainage; more restrictive, because the delta drainage is incompletely mapped) and the ceiling without connectivity. The connectivity requirement is not inherited from the terrain-index methods we build on: HAND-type methods "do not preserve hydraulic connectivity (i.e., floodplain cells lower than the channel water height are denoted as flooded whether or not there is a physical flow path to them)" (Bates 2022), and GeoFlood's authors state as a limitation that "local depressions such as ponds or waterbodies … can be identified as flooded with GeoFlood even if they are not connected with the main stem river" (Zheng et al. 2018). Enforcing connectivity by connected-components analysis, as in coastal bathtub mapping (Kulp and Strauss 2019), is what turns the ceiling into a physically admissible extent; small channels that the 20 m grid does not resolve are a known control on floodplain connectivity (Neal et al. 2012), and in flat terrain the inferred flow path can differ from the real one (Guo et al. 2025) — the two reasons the rules are reported side by side rather than as one answer. The
rule is evaluated once on the union of the two zone grids, so that a connection may cross the zone boundary; the overlap is
attributed to the delta zone only for accounting (a per-zone evaluation with the ownership applied before the connectivity finds
0.0 km² of difference on 7 June, T11i). On the FABDEM cells the terrain enters after
subtraction of the residual class-dependent terrain-elevation bias, estimated per zone and WorldCover class from FABDEM − ICESat-2
ground differences (T18b; pooled medians: trees +1.65 m, wetland
+0.56 m, grass +0.32 m, cropland
+0.09 m); FABDEM is already a bare-earth DTM, so this is a residual bias, not a
canopy correction, and the bed cells are used as surveyed. The *normal regime* is the union of the same rule over the pre-breach days 26 May–5 June plus the optically
observed pre-breach water (water in at least 20 % of the pre-breach Sentinel-2 observations, p60); **new inundation** is water on day t outside that regime.
Sentinel-1 darkness on 1–2 June is not part of the regime: a dark C-band return over dry sand or a smooth field is not water, and most of
that ground was dry in the later images (T28); it only masks the Sentinel-1 new dark water of the checks, where the sensor was already dark. Cells of the model-only
normal regime ("normally wet": low reed beds below the normal surface that no optical or SAR mask lists as water) are kept as
their own category, because a Sentinel-1 dark-water onset there is a depth signal — the reeds are submerged — not the onset of inundation: in flooded vegetation the double bounce raises C-band backscatter above the non-flooded level, but once the water rises over the plants the signal turns dark (Grimaldi et al. 2020; Jarrett et al. 2023; review: Tsyganskaya et al. 2018; flooded vegetation "does not generally have a clear and unique radar signature", Pulvirenti et al. 2021), so the date on which a reed bed goes dark is the date its canopy went under, not the date water arrived. With the terrain as delivered (no residual bias removed) those reed beds sit above the normal surface and count as new inundation; we report
that run as a sensitivity (T12) and the two quantities — new inundation and wetland submergence — separately.

![FigS16](img/FigS16.jpg)

**FigS16 Seed classes of the superseded all-prewater seeding and the retained-water decision tree (D-SEED, D-MEMORY).** (a–c) New inundation on 6, 9 and 15 June 2023 under the superseded rule that seeded the connectivity from every pre-breach water cell, on the Sentinel-2 true-colour image of 13/20 June 2022 (one year before the breach): the event-source network of the primary rule (dark; the largest connected component of the pre-breach water map), river-connected new water (blue), trapped after an earlier connection (violet; retained-water candidates) and isolated components never connected along their day-to-day lineage (red, black outline; seeded by ponds and canals — not event inundation). The three areas over all regions are given in each title (p95o, T11n). On 6 June the two large components east of the floodplain are isolated-never; the largest (41 km², WorldCover cropland on the sandy terrace of the left bank) hangs on four pond cells under the Kokan' level 14 km away. (d) 18 June 2023 on the Sentinel-2 image of that day: the primary reconstruction (river-network seed) and the retained water of the memory sensitivity (memory minus primary) classed by the same-day Sentinel-1 scene — water (plausible retained water), open ground without a water signal (likely drained), no usable observation (uncertain; T11p). Contains modified Copernicus Sentinel data 2022/2023.

**Table T12.** Daily terrain-reconstructed inundation per region and key date, REPORTED AS the Monte-Carlo median [p05-p95] of the coherent Monte-Carlo worlds (p95e rev 2; n_draws per row) with the deterministic nominal run (*_central_*, draw 0, a diagnostic) alongside: reconstructed TOTAL water-surface area (W_total_*: all water on the day incl. pre-breach channels, lakes and reed beds; quantiles of the total-water ensemble), reconstructed NEWLY INUNDATED area (A_*), the volume of new water (V_*) and of all water (Vtot_*), and the draw's own pre-breach baseline (baseline_*). Relative half-widths rel_halfwidth_* = (p95 - p05) / 2 over the Monte-Carlo median. The 100 000-draw emulator is not part of this table (a diagnostic, T12d). Sensitivities (nominal runs): p42 HAND rule, ceiling only, terrain as delivered (no residual bias removed), superseded closure, 4-connectivity, main-stem seed, 3-day maximum gap, river-aware water surface, the Kalynivske gauge as an extra water-surface node (the gauge then an input), nearest-node fallback capped at 10 km. Daily reconstructed series, not daily observations. [independent_physical] *(25 of 48 rows and 10 of 53 columns shown; full table: publication/tables/T12.csv)*

| date | region | A_p50_km2 | A_p05_km2 | A_p95_km2 | A_central_km2 | W_total_p50_km2 | W_total_p05_km2 | W_total_p95_km2 | W_total_central_km2 |
|---|---|---|---|---|---|---|---|---|---|
| 2023-06-05 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 439.4 | 410.4 | 465.1 | 461.3 |
| 2023-06-05 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 20.0 | 16.2 | 24.8 | 22.6 |
| 2023-06-05 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 262.9 | 243.4 | 280.1 | 295.3 |
| 2023-06-06 | DNIPRO_CORRIDOR | 151.6 | 140.3 | 165.1 | 132.2 | 628.5 | 612.3 | 645.7 | 629.9000000000001 |
| 2023-06-06 | INHULETS_VALLEY_rect | 34.6 | 32.0 | 38.7 | 35.0 | 61.6 | 59.5 | 63.5 | 62.3 |
| 2023-06-06 | P42_FLOODPLAIN_DOMAIN | 126.3 | 115.2 | 139.5 | 107.1 | 425.4 | 418.8 | 430.8 | 436.6 |
| 2023-06-07 | DNIPRO_CORRIDOR | 233.7 | 216.0 | 253.7 | 214.8 | 716.2 | 685.9 | 743.6 | 718.6 |
| 2023-06-07 | INHULETS_VALLEY_rect | 42.5 | 40.0 | 46.3 | 42.3 | 69.4 | 68.7 | 70.3 | 69.6 |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | 189.3 | 171.8 | 205.1 | 170.6 | 492.8 | 482.2 | 508.0 | 505.8 |
| 2023-06-08 | DNIPRO_CORRIDOR | 239.3 | 186.0 | 263.4 | 226.6 | 712.2 | 644.5 | 761.7 | 730.8 |
| 2023-06-08 | INHULETS_VALLEY_rect | 46.7 | 44.2 | 50.4 | 46.4 | 73.7 | 73.1 | 74.4 | 73.7 |
| 2023-06-08 | P42_FLOODPLAIN_DOMAIN | 189.9 | 142.6 | 208.3 | 181.1 | 494.0 | 442.0 | 509.6 | 516.5999999999999 |
| 2023-06-09 | DNIPRO_CORRIDOR | 200.9 | 185.9 | 230.4 | 171.3 | 676.1 | 642.6 | 721.7 | 670.2 |
| 2023-06-09 | INHULETS_VALLEY_rect | 49.9 | 47.4 | 53.5 | 49.6 | 76.8 | 76.2 | 77.5 | 76.9 |
| 2023-06-09 | P42_FLOODPLAIN_DOMAIN | 150.9 | 137.7 | 174.3 | 124.7 | 448.7 | 441.7 | 478.6 | 454.7000000000001 |
| 2023-06-10 | DNIPRO_CORRIDOR | 196.2 | 177.0 | 244.3 | 159.8 | 663.8 | 601.2 | 731.6 | 659.0 |
| 2023-06-10 | INHULETS_VALLEY_rect | 47.7 | 45.1 | 51.4 | 47.4 | 74.6 | 73.9 | 75.3 | 74.8 |
| 2023-06-10 | P42_FLOODPLAIN_DOMAIN | 144.6 | 131.5 | 159.3 | 118.4 | 441.5 | 432.1 | 449.3 | 448.3 |
| 2023-06-11 | DNIPRO_CORRIDOR | 181.4 | 162.3 | 230.7 | 146.60000000000002 | 649.6 | 586.8 | 715.6 | 646.3 |
| 2023-06-11 | INHULETS_VALLEY_rect | 44.9 | 42.4 | 48.6 | 44.7 | 71.9 | 71.1 | 72.7 | 72.0 |
| 2023-06-11 | P42_FLOODPLAIN_DOMAIN | 137.1 | 124.3 | 151.1 | 111.8 | 434.1 | 424.7 | 440.8 | 442.3 |
| 2023-06-12 | DNIPRO_CORRIDOR | 163.5 | 144.7 | 211.7 | 129.5 | 630.7 | 568.7 | 698.5 | 628.9 |
| 2023-06-12 | INHULETS_VALLEY_rect | 41.8 | 39.1 | 45.6 | 41.6 | 68.7 | 67.8 | 69.6 | 68.9 |
| 2023-06-12 | P42_FLOODPLAIN_DOMAIN | 127.3 | 115.1 | 141.3 | 102.0 | 423.8 | 414.5 | 431.6 | 431.8 |
| 2023-06-13 | DNIPRO_CORRIDOR | 143.2 | 125.4 | 192.4 | 112.1 | 610.6 | 547.1 | 679.2 | 611.4000000000001 |

**Table T13.** Terrain reconstruction vs Sentinel-1 new dark water per acquisition date, region and variant: hit / miss / miss-on-normally-wet / terrain-only km2, POD, FAR, CSI (raw agreement, primary) and the conditional POD outside the normally-wet class (diagnostic). [cross_sensor] *(25 of 396 rows and 10 of 20 columns shown; full table: publication/tables/T13.csv)*

| variant | date | region | s1_new_km2 | hand_new_km2 | hit_km2 | miss_km2 | miss_on_normally_wet_km2 | hand_only_km2 | POD |
|---|---|---|---|---|---|---|---|---|---|
| connected_ceiling | 2023-06-01 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| connected_ceiling | 2023-06-01 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| connected_ceiling | 2023-06-01 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| connected_ceiling | 2023-06-02 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| connected_ceiling | 2023-06-02 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| connected_ceiling | 2023-06-02 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| connected_ceiling | 2023-06-06 | DNIPRO_CORRIDOR | 30.3 | 99.2 | 0.9 | 29.4 | 7.300000000000001 | 98.2 | 0.03 |
| connected_ceiling | 2023-06-06 | INHULETS_VALLEY_rect | 4.7 | 12.3 | 0.1 | 4.5 | 0.3 | 12.2 | 0.022 |
| connected_ceiling | 2023-06-06 | P42_FLOODPLAIN_DOMAIN | 8.5 | 79.4 | 0.9 | 7.5 | 7.1 | 78.5 | 0.107 |
| connected_ceiling | 2023-06-09 | DNIPRO_CORRIDOR | 319.4 | 170.8 | 58.9 | 260.5 | 169.5 | 111.9 | 0.184 |
| connected_ceiling | 2023-06-09 | INHULETS_VALLEY_rect | 36.2 | 19.4 | 12.4 | 23.8 | 15.8 | 7.0 | 0.343 |
| connected_ceiling | 2023-06-09 | P42_FLOODPLAIN_DOMAIN | 201.2 | 124.4 | 51.8 | 149.39999999999998 | 146.39999999999998 | 72.6 | 0.257 |
| connected_ceiling | 2023-06-13 | DNIPRO_CORRIDOR | 164.89999999999998 | 111.7 | 24.6 | 140.3 | 128.6 | 87.1 | 0.149 |
| connected_ceiling | 2023-06-13 | INHULETS_VALLEY_rect | 27.0 | 14.7 | 10.3 | 16.7 | 16.3 | 4.5 | 0.381 |
| connected_ceiling | 2023-06-13 | P42_FLOODPLAIN_DOMAIN | 147.3 | 91.2 | 23.700000000000003 | 123.6 | 121.1 | 67.5 | 0.161 |
| connected_ceiling | 2023-06-14 | DNIPRO_CORRIDOR | 99.3 | 89.7 | 12.1 | 87.2 | 63.6 | 77.80000000000001 | 0.122 |
| connected_ceiling | 2023-06-14 | INHULETS_VALLEY_rect | 25.4 | 13.7 | 8.8 | 16.7 | 15.8 | 4.9 | 0.345 |
| connected_ceiling | 2023-06-14 | P42_FLOODPLAIN_DOMAIN | 74.0 | 76.30000000000001 | 11.8 | 62.2 | 58.900000000000006 | 64.5 | 0.159 |
| connected_ceiling | 2023-06-18 | DNIPRO_CORRIDOR | 53.6 | 27.9 | 0.2 | 53.400000000000006 | 4.199999999999999 | 27.6 | 0.004 |
| connected_ceiling | 2023-06-18 | INHULETS_VALLEY_rect | 18.1 | 7.8 | 2.9 | 15.2 | 6.3 | 4.9 | 0.16 |
| connected_ceiling | 2023-06-18 | P42_FLOODPLAIN_DOMAIN | 9.9 | 24.6 | 0.2 | 9.8 | 3.8 | 24.3 | 0.02 |
| connected_ceiling | 2023-06-21 | DNIPRO_CORRIDOR | 186.3 | 4.0 | 0.1 | 186.3 | 10.0 | 4.0 | 0.001 |
| connected_ceiling | 2023-06-21 | INHULETS_VALLEY_rect | 32.6 | 0.0 | 0.0 | 32.6 | 1.0 | 0.0 | 0.0 |
| connected_ceiling | 2023-06-21 | P42_FLOODPLAIN_DOMAIN | 22.6 | 3.6 | 0.1 | 22.5 | 9.4 | 3.5 | 0.004 |
| connected_ceiling | 2023-06-25 | DNIPRO_CORRIDOR | 112.7 | 0.0 | 0.0 | 112.7 | 7.1 | 0.0 | 0.0 |

**Table T11p.** D-MEMORY sensitivity (retained water): per day and region the new inundation of the primary (instantaneous river-connected reconstruction), of the memory variant (a cell inundated on day t-1 stays inundated on day t while still below the surface -- a storage hypothesis without infiltration or drainage) and their difference, the retained water classed by the same-day Sentinel-1 scene (water = plausible retained water; open ground without a water signal = likely drained; no usable same-day observation = uncertain) and the date and lag of the next scene when there is none. A sensitivity, never the primary. [cross_sensor] *(25 of 138 rows and 10 of 12 columns shown; full table: publication/tables/T11p.csv)*

| date | region | A_new_a_km2 | A_new_b_km2 | retained_km2 | lost_km2 | retained_s1_water_km2 | retained_s1_open_no_water_km2 | retained_s1_uncertain_km2 | s1_same_day |
|---|---|---|---|---|---|---|---|---|---|
| 2023-05-26 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-26 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-26 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-27 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-27 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-27 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-28 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-28 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-28 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-29 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-29 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-29 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-30 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-30 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-30 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-31 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-31 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-05-31 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |
| 2023-06-01 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | True |
| 2023-06-01 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | True |
| 2023-06-01 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | True |
| 2023-06-02 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | True |
| 2023-06-02 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | True |
| 2023-06-02 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | True |
| 2023-06-03 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | False |

**Table T11i.** Seam check (review F06): water-surface-allowed area on 7, 9 and 13 June per zone and region, evaluated on the union mosaic versus the superseded per-zone evaluation (ownership applied before the connectivity), with the cells found by only one of the two. [independent_physical]

| date | zone | region | mosaic_km2 | zonal_legacy_km2 | mosaic_only_km2 | zonal_only_km2 |
|---|---|---|---|---|---|---|
| 2023-06-07 | ZONE_4_DAM_TO_KHERSON_FLOODWAY | DNIPRO_CORRIDOR | 334.35 | 382.31 | 0.0 | 47.96 |
| 2023-06-07 | ZONE_4_DAM_TO_KHERSON_FLOODWAY | INHULETS_VALLEY_rect | 69.58 | 69.58 | 0.0 | 0.0 |
| 2023-06-07 | ZONE_4_DAM_TO_KHERSON_FLOODWAY | P42_FLOODPLAIN_DOMAIN | 297.51 | 297.51 | 0.0 | 0.0 |
| 2023-06-07 | ZONE_2_KHERSON_DELTA | DNIPRO_CORRIDOR | 384.32 | 405.1 | 0.0 | 20.78 |
| 2023-06-07 | ZONE_2_KHERSON_DELTA | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-07 | ZONE_2_KHERSON_DELTA | P42_FLOODPLAIN_DOMAIN | 208.33 | 214.53 | 0.0 | 6.19 |
| 2023-06-09 | ZONE_4_DAM_TO_KHERSON_FLOODWAY | DNIPRO_CORRIDOR | 277.71 | 317.88 | 0.0 | 40.16 |
| 2023-06-09 | ZONE_4_DAM_TO_KHERSON_FLOODWAY | INHULETS_VALLEY_rect | 76.94 | 76.94 | 0.0 | 0.0 |
| 2023-06-09 | ZONE_4_DAM_TO_KHERSON_FLOODWAY | P42_FLOODPLAIN_DOMAIN | 243.26 | 281.9 | 0.0 | 38.64 |
| 2023-06-09 | ZONE_2_KHERSON_DELTA | DNIPRO_CORRIDOR | 392.52 | 414.12 | 0.0 | 21.61 |
| 2023-06-09 | ZONE_2_KHERSON_DELTA | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-09 | ZONE_2_KHERSON_DELTA | P42_FLOODPLAIN_DOMAIN | 211.37 | 218.35 | 0.0 | 6.98 |
| 2023-06-13 | ZONE_4_DAM_TO_KHERSON_FLOODWAY | DNIPRO_CORRIDOR | 236.31 | 236.38 | 0.0 | 0.07 |
| 2023-06-13 | ZONE_4_DAM_TO_KHERSON_FLOODWAY | INHULETS_VALLEY_rect | 64.32 | 64.32 | 0.0 | 0.0 |
| 2023-06-13 | ZONE_4_DAM_TO_KHERSON_FLOODWAY | P42_FLOODPLAIN_DOMAIN | 218.72 | 218.79 | 0.0 | 0.07 |
| 2023-06-13 | ZONE_2_KHERSON_DELTA | DNIPRO_CORRIDOR | 375.12 | 396.72 | 0.0 | 21.6 |
| 2023-06-13 | ZONE_2_KHERSON_DELTA | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-13 | ZONE_2_KHERSON_DELTA | P42_FLOODPLAIN_DOMAIN | 202.44 | 209.43 | 0.0 | 6.99 |

**Table T18b.** FABDEM-DTM residual against night ICESat-2 ground on FABDEM-sourced cells of the seamless terrain-bed model (p55 source 3/4), per zone and WorldCover class and pooled: N, median (the residual class-dependent terrain-elevation bias removed on FABDEM cells), NMAD (the marginal scale of the perturbed terrain realizations), RMSE, mean, acquisition dates. FABDEM is a bare-earth DTM: the class median is a residual bias, not a canopy correction. [independent_physical]

| zone | wc_class | N | median | NMAD | RMSE | mean | n_dates | wc_code | population |
|---|---|---|---|---|---|---|---|---|---|
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | all | 477213 | 0.225 | 0.385 | 1.08 | 0.414 | 92 |  | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | trees | 30023 | 1.698 | 1.711 | 2.88 | 2.093 | 84 | 10.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | grass | 98993 | 0.385 | 0.621 | 1.5 | 0.681 | 86 | 30.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | cropland | 307849 | 0.151 | 0.295 | 0.351 | 0.158 | 90 | 40.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | built | 15309 | 0.172 | 0.597 | 1.116 | 0.261 | 84 | 50.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | bare | 3525 | 0.307 | 0.936 | 1.421 | 0.31 | 45 | 60.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | wetland | 21514 | 0.589 | 0.412 | 0.974 | 0.628 | 45 | 90.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_2_KHERSON_DELTA | all | 153233 | -0.002 | 0.298 | 0.969 | 0.21 | 23 |  | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_2_KHERSON_DELTA | trees | 8064 | 1.486 | 1.596 | 2.86 | 1.983 | 19 | 10.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_2_KHERSON_DELTA | grass | 29225 | 0.107 | 0.491 | 1.274 | 0.377 | 21 | 30.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_2_KHERSON_DELTA | cropland | 95454 | -0.059 | 0.195 | 0.281 | -0.031 | 21 | 40.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_2_KHERSON_DELTA | built | 7848 | 0.156 | 0.698 | 1.25 | 0.311 | 20 | 50.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_2_KHERSON_DELTA | bare | 287 | -0.607 | 1.16 | 3.377 | -0.817 | 15 | 60.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| ZONE_2_KHERSON_DELTA | wetland | 12355 | 0.519 | 0.474 | 0.77 | 0.486 | 19 | 90.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| POOLED | all | 630446 | 0.167 | 0.387 | 1.054 | 0.364 | 98 |  | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| POOLED | trees | 38087 | 1.651 | 1.693 | 2.876 | 2.07 | 88 | 10.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| POOLED | grass | 128218 | 0.322 | 0.606 | 1.452 | 0.612 | 92 | 30.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| POOLED | cropland | 403303 | 0.085 | 0.293 | 0.336 | 0.113 | 96 | 40.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| POOLED | built | 23157 | 0.168 | 0.634 | 1.163 | 0.278 | 88 | 50.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| POOLED | bare | 3812 | 0.278 | 0.986 | 1.651 | 0.225 | 49 | 60.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |
| POOLED | wetland | 33869 | 0.563 | 0.43 | 0.905 | 0.576 | 49 | 90.0 | FABDEM-sourced cells of the seamless terrain-bed model (sour |

*New inundation of dry ground and the response of the wetland complex.* The reed beds of the delta and of the floodplain were wetland,
not dry ground, before the breach, and their inundation is a different physical quantity from the flooding of dry ground, so the two are
reported apart. Flood mapping separates the event from the normally present water with a reference-water state, and taking its
seasonal part into account reduces a potential over-estimation of the inundation extent (Martinis et al. 2022). Under emergent
vegetation that state cannot be observed with the sensors used here: standard optical water indices systematically underestimate
the flooding duration under a vegetation cover (Lefebvre et al. 2019), subcanopy flooding in high-vegetated wetlands could not be
detected with Sentinel-1 VV/VH (Slagter et al. 2020), and in tropical herbaceous wetlands inundated vegetation can account for over
three quarters of the inundated area, which open-water mapping does not detect (Oakes et al. 2023). Every cell therefore carries one
of three pre-event ground classes (p95x): *dry before the event* — no optical pre-breach water, outside the normal regime, neither
WorldCover herbaceous wetland nor water; the *seasonally wet vegetated wetland* — WorldCover herbaceous wetland (the reed beds,
including those above the normal surface) and the model-only normally-wet ground, whose low reed beds carry a seasonal C-band
signature of wet emergent vegetation before the breach (T12j) but for which no observation gives a binary map of water under the
canopy on any given day; and *open reference water* — the optical pre-breach water (a few km² of other WorldCover water are kept
apart). The **new inundation of dry ground** A_new,dry is the new inundation on the first class. On the wetland the event extent and
the pre-event state are read apart: A_wet(t) is the part of the wetland inside the water extent on day t, and the **event increase**
ΔA_wet(t) = A_wet(t) − A_wet(5 June), taken within each world, is a difference from the reconstructed pre-breach state — it attributes
part of the inundated wetland to new inundation and inherits the uncertainty of that state. All are counted in the same coherent
Monte-Carlo worlds as A_new (§3.4, T12h); world by world A_new is the sum of A_new,dry, its part on the wetland and a remainder on
other water. A_wet and ΔA_wet are model quantities — no observation used here confirms or excludes water under the reed canopy — and
they are never added to A_new,dry as one flooded area.

**Table T12j.** Seasonal evidence of the pre-event ground classes (p95z, compact): per zone and stratum the median NDVI, NDMI and MNDWI of 13 June 2022 (same season, normal year) and of the last optical scene before the breach, and the 2023 spring Sentinel-1 VV, VH and VV - VH (median of the scene medians). Strata: NW_REEDS / NW_TREES = model-only normally wet reeds / floodplain forest; HIGH_REEDS = reeds > 0.5 m above the pre-breach surface and not reached on 7 June (P(water) < 0.05); OPEN_WATER = optical pre-breach water; EVENT_REEDS = reeds outside the normal regime that the ensemble floods on 7 June (P(water) >= 0.8); DRY_LAND = grass / cropland > 2 m above the 8 June surface. Observations, nothing fitted; a C-band double-bounce signature is consistent with wet or inundated emergent vegetation and establishes neither open water nor a depth; stratum-level evidence, not a map of water under the canopy on any day. [cross_sensor] *(10 of 10 rows and 10 of 17 columns shown; full table: publication/tables/T12j.csv)*

| zone | stratum | description | pre_event_class | stratum_km2 | S2_jun2022_NDVI | S2_jun2022_NDMI | S2_jun2022_MNDWI | S2_last_pre_NDVI | S2_last_pre_NDMI |
|---|---|---|---|---|---|---|---|---|---|
| delta | DRY_LAND | dry ground: grass / cropland > 2 m above the 8 June surface | dry before the event | 1949.24 | 0.352 | -0.065 | -0.519 | 0.268 | -0.239 |
| delta | HIGH_REEDS | dry reeds: > 0.5 m above the pre-breach surface, not reached | vegetated wetland (WorldCover), outside the event | 13.79 | 0.653 | 0.118 | -0.523 | 0.263 | -0.208 |
| delta | NW_REEDS | seasonally wet reeds below the normal surface (model-only no | vegetated wetland | 116.12 | 0.775 | 0.308 | -0.45 | 0.245 | -0.16 |
| delta | EVENT_REEDS | reeds reached only by the event (P(water) >= 0.8 on 7 June) | vegetated wetland | 39.06 | 0.775 | 0.307 | -0.479 | 0.254 | -0.182 |
| delta | OPEN_WATER | open reference water (optical, >= 20 % of pre-breach scenes) | open reference water | 194.32 | -0.107 | 0.082 | 0.278 | -0.132 | 0.236 |
| floodway | DRY_LAND | dry ground: grass / cropland > 2 m above the 8 June surface | dry before the event | 2436.4 | 0.383 | -0.047 | -0.522 | 0.551 | 0.077 |
| floodway | HIGH_REEDS | dry reeds: > 0.5 m above the pre-breach surface, not reached | vegetated wetland (WorldCover), outside the event | 7.9 | 0.773 | 0.213 | -0.571 | 0.688 | 0.184 |
| floodway | NW_REEDS | seasonally wet reeds below the normal surface (model-only no | vegetated wetland | 98.6 | 0.759 | 0.29 | -0.46 | 0.679 | 0.273 |
| floodway | EVENT_REEDS | reeds reached only by the event (P(water) >= 0.8 on 7 June) | vegetated wetland | 12.87 | 0.743 | 0.247 | -0.5 | 0.698 | 0.199 |
| floodway | OPEN_WATER | open reference water (optical, >= 20 % of pre-breach scenes) | open reference water | 69.2 | -0.149 | -0.035 | 0.208 | -0.377 | -0.198 |

**Table T12h.** Areas split by ground class (p95e_split_areas, the same coherent Monte-Carlo worlds as T12; nominal = draw 0, a diagnostic; median [p05-p95] of draws 1..n): new inundation on DRY-BEFORE-EVENT ground (no optical pre-breach water, no reed / wetland complex, not WorldCover water) -- the new flooding of dry ground; water on the VEGETATED_WETLAND complex (WorldCover herbaceous wetland or model-only normally wet), its pre-breach value (5 June) and the event increase over it -- the inundation of wetland vegetation that before the breach already shows a C-band signature consistent with wet or inundated emergent vegetation (p95z); 'all' = the A_new of T12 (gate); other_water = WorldCover water outside the optical reference (the remainder of A_new). Corridor + Inhulets summed within each world (date-matched). [independent_physical] *(25 of 120 rows and 10 of 16 columns shown; full table: publication/tables/T12h.csv)*

| date | region | ground | n_draws | new_km2_nominal | new_km2_p05 | new_km2_p50 | new_km2_p95 | water_km2_nominal | water_km2_p05 |
|---|---|---|---|---|---|---|---|---|---|
| 2023-06-05 | DNIPRO_CORRIDOR | all | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 461.29 | 410.4 |
| 2023-06-05 | DNIPRO_CORRIDOR | dry_before_event | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 3.88 |
| 2023-06-05 | DNIPRO_CORRIDOR | other_water | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.2 |
| 2023-06-05 | DNIPRO_CORRIDOR | vegetated_wetland | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 230.98 | 179.16 |
| 2023-06-05 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | all | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 483.88 | 429.11 |
| 2023-06-05 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | dry_before_event | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4.49 |
| 2023-06-05 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | other_water | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.21 |
| 2023-06-05 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | vegetated_wetland | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 248.67 | 193.39 |
| 2023-06-05 | INHULETS_VALLEY_rect | all | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 22.6 | 16.24 |
| 2023-06-05 | INHULETS_VALLEY_rect | dry_before_event | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.24 |
| 2023-06-05 | INHULETS_VALLEY_rect | other_water | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-05 | INHULETS_VALLEY_rect | vegetated_wetland | 1000 | 0.0 | 0.0 | 0.0 | 0.0 | 17.69 | 12.55 |
| 2023-06-06 | DNIPRO_CORRIDOR | all | 1000 | 132.14 | 140.34 | 151.65 | 165.08 | 629.88 | 612.29 |
| 2023-06-06 | DNIPRO_CORRIDOR | dry_before_event | 1000 | 82.89 | 67.23 | 72.09 | 76.86 | 82.89 | 73.29 |
| 2023-06-06 | DNIPRO_CORRIDOR | other_water | 1000 | 2.43 | 2.03 | 2.11 | 2.18 | 2.43 | 2.49 |
| 2023-06-06 | DNIPRO_CORRIDOR | vegetated_wetland | 1000 | 46.83 | 65.41 | 77.61 | 91.11 | 308.07 | 298.82 |
| 2023-06-06 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | all | 1000 | 167.16 | 174.18 | 186.68 | 200.66 | 692.19 | 673.5 |
| 2023-06-06 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | dry_before_event | 1000 | 113.83 | 94.84 | 100.49 | 105.71 | 113.83 | 103.17 |
| 2023-06-06 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | other_water | 1000 | 4.47 | 3.68 | 3.95 | 4.12 | 4.47 | 4.28 |
| 2023-06-06 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | vegetated_wetland | 1000 | 48.85 | 69.18 | 82.44 | 96.36 | 331.17 | 321.85 |
| 2023-06-06 | INHULETS_VALLEY_rect | all | 1000 | 35.02 | 32.04 | 34.62 | 38.72 | 62.31 | 59.54 |
| 2023-06-06 | INHULETS_VALLEY_rect | dry_before_event | 1000 | 30.95 | 26.45 | 28.27 | 30.28 | 30.95 | 28.49 |
| 2023-06-06 | INHULETS_VALLEY_rect | other_water | 1000 | 2.04 | 1.6 | 1.85 | 1.99 | 2.04 | 1.73 |
| 2023-06-06 | INHULETS_VALLEY_rect | vegetated_wetland | 1000 | 2.03 | 2.95 | 4.53 | 7.23 | 23.09 | 23.0 |
| 2023-06-07 | DNIPRO_CORRIDOR | all | 1000 | 214.86 | 216.0 | 233.71 | 253.73 | 718.67 | 685.94 |

The depth of a newly inundated cell on day t is H − z of the seamless terrain–bed model, and the *reconstructed new-water volume*
V_new is its integral over the newly inundated area. The per-cell maximum of the daily depth over 26 May–10 July (Fig07a) is a
depth envelope, not the state of any single day, and therefore has no volume. The maps show the geometry of the nominal world
(unperturbed inputs); the areas and volumes quoted as results come from the Monte-Carlo ensemble (§3.4).

### 3.4 Uncertainty: coherent Monte-Carlo worlds

One Monte-Carlo draw is one possible world over the whole domain (T11b): one realization of the terrain error over the union
of the zone grids and one realization of the water surface over all nodes and days; the pre-breach regime is rebuilt from the
same realization before the event days are evaluated, and the total water-surface area, the regime, the new inundation and both
volumes are stored per draw and summarised each from its own ensemble. The water-surface realization perturbs the node heights
once: a datum-closure offset shared by every SWOT node and day (σ 0.05 m,
Paper 1), the SWOT node height on observed node-days (median wse_u 0.092 m), the
interpolation error on interpolated and end-held node-days — one standard normal per node and gap, scaled by the robust spread
of a gap-matched cross-validation that grows with the gap length, from
0.07 m for one day to 1.15 m for
five to eight days (T11f) — and the gauge (σ 0.05 m), which is both a node and the cap
of the far cells and enters once. The terrain realization multiplies the class-wise NMAD of the FABDEM − ICESat-2 residual
(T18b) by a unit-variance Gaussian field whose covariance — a nugget share of
0.08 and exponential structures of
123 m and
1172 m — is fitted to the
standardized residuals of same-date ICESat-2 pairs (T18c, FigS11); DEM error is spatially autocorrelated, and treating it as
aspatial understates its effect on inundation (Hawker et al. 2018; Darnell et al. 2008), and correlated and uncorrelated error
fields propagate differently into hydrological outputs (Cunha et al. 2012). One pooled correlation with class-wise scales is a
modelling assumption, not a measured class-specific covariance, and the nugget contains the ICESat-2 segment noise, so it bounds
the cell-level white error from above. The bed cells of the terrain model carry no stochastic term (a limitation; they lie inside
the pre-breach water, and 99.4% of the new area on 7 June is on FABDEM
cells, T11j).

![FigS11](img/FigS11.jpg)

**FigS11.** The terrain-error model of the Monte-Carlo (p95j, T18b/T18c). (a) Semivariograms of the FABDEM − night ICESat-2 ground residual after the class median, per WorldCover class (pooled zones, same-date pairs; FABDEM-sourced cells only), with single-exponential fits. (b) The standardized residual (r − b_c)/σ_c, robust (Cressie–Hawkins) and classical estimators, with the nested fit used by the Monte-Carlo (a nugget plus two exponential structures) and the single exponential for comparison; the dotted line marks unit variance. One pooled correlation with class-wise scales is a modelling assumption.

**Table T11b.** Uncertainty components of the terrain reconstruction (Monte-Carlo inputs, p95e rev 2): datum closure of the SWOT chain, gauge, SWOT node height, gap-dependent interpolation error, the correlation model of the terrain-error field (nugget + nested exponential structures fitted to the standardized FABDEM - ICESat-2 residuals, p95j) and the class-wise FABDEM residual scale per zone (own zone where N >= 500, else pooled and flagged transferred); bed cells of the seamless terrain-bed model carry no stochastic term (limitation). [independent_physical] *(19 of 19 rows and 10 of 14 columns shown; full table: publication/tables/T11b.csv)*

| component | sigma_m | applied | source | sigma_by_gap_m | range_m | nugget_share | structures | model | zone |
|---|---|---|---|---|---|---|---|---|---|
| datum_closure_kherson | 0.05 | one scalar per draw, every SWOT node and day (the closure of | Paper 1 Table 5 / Sec. 5.12 (NMAD 4-5 cm at Kherson) |  |  |  |  |  |  |
| gauge_daily | 0.05 | one scalar per draw on the gauge node (local node AND far ca | date-only daily values; two yearbooks differ by NMAD 1.5 cm  |  |  |  |  |  |  |
| swot_node_wse_u | 0.092 | observed node-days, independent per node-day | p59 nodes, median wse_u |  |  |  |  |  |  |
| interpolation_gap_cv | 0.066 | interpolated / held node-days: one standard normal per node  | p95e gap_cv (gap-matched) | 1-1 d: interp 0.066 / held 0.089; 2-2 d: interp 0.118 / held |  |  |  |  |  |
| pass_level_swot | 0.0 | per-day scalar shared by all SWOT nodes; 0 in the primary bu | Paper 1 daily closure scatter |  |  |  |  |  |  |
| terrain_field_correlation |  | unit-variance FFT field on the union mosaic, one realization | POOLED standardized residual (r - b_c) / sigma_c, Cressie-Ha |  | 1172.0 | 0.08 | 0.50 x exp(-h/123 m); 0.42 x exp(-h/1172 m) | nested_2exp+nugget |  |
| terrain_trees | 1.711 | class NMAD as the marginal sigma of the correlated field on  | ZONE_4_DAM_TO_KHERSON_FLOODWAY (FABDEM - ICESat-2 ground, ni |  |  |  |  |  | ZONE_4_DAM_TO_KHERSON_FLOODWAY |
| terrain_grass | 0.621 | class NMAD as the marginal sigma of the correlated field on  | ZONE_4_DAM_TO_KHERSON_FLOODWAY (FABDEM - ICESat-2 ground, ni |  |  |  |  |  | ZONE_4_DAM_TO_KHERSON_FLOODWAY |
| terrain_cropland | 0.295 | class NMAD as the marginal sigma of the correlated field on  | ZONE_4_DAM_TO_KHERSON_FLOODWAY (FABDEM - ICESat-2 ground, ni |  |  |  |  |  | ZONE_4_DAM_TO_KHERSON_FLOODWAY |
| terrain_built | 0.597 | class NMAD as the marginal sigma of the correlated field on  | ZONE_4_DAM_TO_KHERSON_FLOODWAY (FABDEM - ICESat-2 ground, ni |  |  |  |  |  | ZONE_4_DAM_TO_KHERSON_FLOODWAY |
| terrain_bare | 0.936 | class NMAD as the marginal sigma of the correlated field on  | ZONE_4_DAM_TO_KHERSON_FLOODWAY (FABDEM - ICESat-2 ground, ni |  |  |  |  |  | ZONE_4_DAM_TO_KHERSON_FLOODWAY |
| terrain_wetland | 0.412 | class NMAD as the marginal sigma of the correlated field on  | ZONE_4_DAM_TO_KHERSON_FLOODWAY (FABDEM - ICESat-2 ground, ni |  |  |  |  |  | ZONE_4_DAM_TO_KHERSON_FLOODWAY |
| terrain_trees | 1.596 | class NMAD as the marginal sigma of the correlated field on  | ZONE_2_KHERSON_DELTA (FABDEM - ICESat-2 ground, night) |  |  |  |  |  | ZONE_2_KHERSON_DELTA |
| terrain_grass | 0.491 | class NMAD as the marginal sigma of the correlated field on  | ZONE_2_KHERSON_DELTA (FABDEM - ICESat-2 ground, night) |  |  |  |  |  | ZONE_2_KHERSON_DELTA |
| terrain_cropland | 0.195 | class NMAD as the marginal sigma of the correlated field on  | ZONE_2_KHERSON_DELTA (FABDEM - ICESat-2 ground, night) |  |  |  |  |  | ZONE_2_KHERSON_DELTA |
| terrain_built | 0.698 | class NMAD as the marginal sigma of the correlated field on  | ZONE_2_KHERSON_DELTA (FABDEM - ICESat-2 ground, night) |  |  |  |  |  | ZONE_2_KHERSON_DELTA |
| terrain_bare | 0.986 | class NMAD as the marginal sigma of the correlated field on  | POOLED (FABDEM - ICESat-2 ground, night) |  |  |  |  |  | ZONE_2_KHERSON_DELTA |
| terrain_wetland | 0.474 | class NMAD as the marginal sigma of the correlated field on  | ZONE_2_KHERSON_DELTA (FABDEM - ICESat-2 ground, night) |  |  |  |  |  | ZONE_2_KHERSON_DELTA |
| terrain_bed | 0.0 | bed cells (source 1/2/5): no stochastic model in this budget | p55 source mask |  |  |  |  |  |  |

**Table T11f.** Error of the per-node time interpolation from a whole-date hold-out: residual NMAD / RMSE by gap length (1, 2, 3-4, 5-8, > 8 days) for interpolated and end-held node-days; the superseded one-day triplet estimate for comparison. [independent_physical]

| kind | gap_lo_days | gap_hi_days | n | NMAD_m | RMSE_m | median_m | p05_m | p95_m |
|---|---|---|---|---|---|---|---|---|
| interpolated | 1 | 1 | 25099 | 0.0662 | 0.7455 | 0.0096 | -0.6253 | 0.1814 |
| interpolated | 2 | 2 | 23382 | 0.1176 | 1.2062 | 0.0288 | -1.4381 | 1.857 |
| interpolated | 3 | 4 | 42156 | 0.3272 | 1.7908 | 0.1226 | -4.4506 | 3.2916 |
| interpolated | 5 | 8 | 73692 | 1.1464 | 2.6028 | 0.3869 | -5.8465 | 2.8341 |
| interpolated | 9 | 8 | 0 |  |  |  |  |  |
| held | 1 | 1 | 1462 | 0.0885 | 0.1328 | -0.0572 | -0.1809 | 0.1088 |
| held | 2 | 2 | 2866 | 0.0628 | 0.1148 | 0.0131 | -0.092 | 0.1432 |
| held | 3 | 4 | 8340 | 0.0755 | 0.1603 | 0.0158 | -0.1127 | 0.1977 |
| held | 5 | 8 | 26753 | 0.2533 | 2.811 | 0.1542 | -0.1586 | 7.5859 |
| held | 9 | 8 | 0 |  |  |  |  |  |
| interpolated (assigned) | 9 | 999 | 0 | 1.1464 | 2.6028 |  |  |  |
| held (assigned) | 9 | 999 | 0 | 0.2533 | 2.811 |  |  |  |
| all (gap-matched) | 1 | 8 | 203750 | 0.2974 | 2.0948 | 0.0673 | -4.7177 | 3.0914 |
| superseded triplet leave-one-out (rev 1) | 1 | 1 | 17313 | 0.0544 |  |  |  |  |

**Table T18c.** Spatial structure of the FABDEM-DTM residual (p95j): empirical semivariograms of same-date ICESat-2 pairs, fitted per zone and class (classical estimator, residual after the class median, m2) and for the standardized residual (r - b_c) / sigma_c (classical and robust Cressie-Hawkins estimators; single exponential + nugget and nested two-exponential + nugget models, Cressie WLS). The pooled robust nested fit is the correlation model of the Monte-Carlo terrain field (T11b); its nugget includes ICESat-2 segment noise and point-to-cell support mismatch. [independent_physical] *(25 of 32 rows and 10 of 17 columns shown; full table: publication/tables/T18c.csv)*

| zone | wc_class | estimator | model | N | NMAD_after_bias | nugget_share | c0 | s2 | L_m |
|---|---|---|---|---|---|---|---|---|---|
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | all | classical | exponential+nugget | 477213 | 0.367 | 0.129 | 0.0748 | 0.5055 | 435.4 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | trees | classical | exponential+nugget | 30023 | 1.711 | 0.016 | 0.0476 | 2.8443 | 332.7 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | grass | classical | exponential+nugget | 98993 | 0.621 | 0.063 | 0.0997 | 1.4803 | 514.0 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | cropland | classical | exponential+nugget | 307849 | 0.295 | 0.043 | 0.0024 | 0.0528 | 130.8 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | built | classical | exponential+nugget | 15309 | 0.597 | 0.041 | 0.0758 | 1.7855 | 468.1 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | bare | classical | exponential+nugget | 3525 | 0.936 | 0.0 | 0.0 | 0.8214 | 32.5 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | wetland | classical | exponential+nugget | 21514 | 0.412 | 0.066 | 0.0127 | 0.1787 | 315.6 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | all_standardized | classical | exponential+nugget | 477213 | 1.0 | 0.147 | 0.2179 | 1.2663 | 311.5 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | all_standardized | classical | nested_2exp+nugget | 477213 | 1.0 | 0.036 | 0.0556 | 0.8729 |  |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | all_standardized | cressie_hawkins | exponential+nugget | 477213 | 1.0 | 0.08 | 0.0562 | 0.6442 | 282.6 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | all_standardized | cressie_hawkins | nested_2exp+nugget | 477213 | 1.0 | 0.018 | 0.0141 | 0.3539 |  |
| ZONE_2_KHERSON_DELTA | all | classical | exponential+nugget | 153233 | 0.274 | 0.125 | 0.057 | 0.3972 | 338.5 |
| ZONE_2_KHERSON_DELTA | trees | classical | exponential+nugget | 8064 | 1.596 | 0.0 | 0.0 | 3.4988 | 321.5 |
| ZONE_2_KHERSON_DELTA | grass | classical | exponential+nugget | 29225 | 0.491 | 0.058 | 0.0506 | 0.8211 | 228.5 |
| ZONE_2_KHERSON_DELTA | cropland | classical | exponential+nugget | 95454 | 0.195 | 0.067 | 0.0045 | 0.0631 | 199.0 |
| ZONE_2_KHERSON_DELTA | built | classical | exponential+nugget | 7848 | 0.698 | 0.035 | 0.0729 | 2.0331 | 394.1 |
| ZONE_2_KHERSON_DELTA | wetland | classical | exponential+nugget | 12355 | 0.474 | 0.068 | 0.0112 | 0.1542 | 249.2 |
| ZONE_2_KHERSON_DELTA | all_standardized | classical | exponential+nugget | 153233 | 1.0 | 0.126 | 0.2698 | 1.8736 | 207.7 |
| ZONE_2_KHERSON_DELTA | all_standardized | classical | nested_2exp+nugget | 153233 | 1.0 | 0.036 | 0.0812 | 0.8992 |  |
| ZONE_2_KHERSON_DELTA | all_standardized | cressie_hawkins | exponential+nugget | 153233 | 1.0 | 0.062 | 0.079 | 1.1881 | 315.5 |
| ZONE_2_KHERSON_DELTA | all_standardized | cressie_hawkins | nested_2exp+nugget | 153233 | 1.0 | 0.017 | 0.0223 | 0.7142 |  |
| POOLED | all | classical | exponential+nugget | 630446 | 0.346 | 0.126 | 0.0672 | 0.4641 | 405.4 |
| POOLED | trees | classical | exponential+nugget | 38087 | 1.686 | 0.0 | 0.0 | 3.2504 | 314.8 |
| POOLED | grass | classical | exponential+nugget | 128218 | 0.589 | 0.063 | 0.0814 | 1.2005 | 382.4 |
| POOLED | cropland | classical | exponential+nugget | 403303 | 0.27 | 0.161 | 0.0107 | 0.0556 | 161.8 |

**Table T11j.** Terrain source of the reconstructed newly inundated area (corridor, key dates): FABDEM DTM (p55 source 3), FABDEM tapered at a bathymetric edge (4), surveyed or reconstructed bed (1, 2) and gap fill (5). The terrain-error model perturbs FABDEM-sourced cells only; the bed share is the part of the new area without a stochastic terrain term. [independent_physical] *(25 of 28 rows and 6 of 6 columns shown; full table: publication/tables/T11j.csv)*

| date | region | terrain_source | source_code | new_km2 | share_of_new |
|---|---|---|---|---|---|
| 2023-06-06 | DNIPRO_CORRIDOR | FABDEM | 3 | 130.85 | 0.9902 |
| 2023-06-06 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 1.29 | 0.0098 |
| 2023-06-07 | DNIPRO_CORRIDOR | FABDEM | 3 | 213.51 | 0.9937 |
| 2023-06-07 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 1.35 | 0.0063 |
| 2023-06-08 | DNIPRO_CORRIDOR | FABDEM | 3 | 225.21 | 0.9939 |
| 2023-06-08 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 1.39 | 0.0061 |
| 2023-06-09 | DNIPRO_CORRIDOR | FABDEM | 3 | 169.85 | 0.9918 |
| 2023-06-09 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 1.41 | 0.0082 |
| 2023-06-10 | DNIPRO_CORRIDOR | FABDEM | 3 | 158.37 | 0.9911 |
| 2023-06-10 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 1.43 | 0.0089 |
| 2023-06-11 | DNIPRO_CORRIDOR | FABDEM | 3 | 145.09 | 0.9901 |
| 2023-06-11 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 1.45 | 0.0099 |
| 2023-06-12 | DNIPRO_CORRIDOR | FABDEM | 3 | 128.08 | 0.9887 |
| 2023-06-12 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 1.46 | 0.0112 |
| 2023-06-13 | DNIPRO_CORRIDOR | FABDEM | 3 | 110.7 | 0.9871 |
| 2023-06-13 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 1.45 | 0.0129 |
| 2023-06-14 | DNIPRO_CORRIDOR | FABDEM | 3 | 88.64 | 0.9841 |
| 2023-06-14 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 1.43 | 0.0159 |
| 2023-06-15 | DNIPRO_CORRIDOR | FABDEM | 3 | 57.97 | 0.9766 |
| 2023-06-15 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 1.39 | 0.0233 |
| 2023-06-16 | DNIPRO_CORRIDOR | FABDEM | 3 | 49.15 | 0.974 |
| 2023-06-16 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 1.31 | 0.026 |
| 2023-06-18 | DNIPRO_CORRIDOR | FABDEM | 3 | 32.97 | 0.9728 |
| 2023-06-18 | DNIPRO_CORRIDOR | FABDEM_tapered_edge | 4 | 0.92 | 0.0272 |
| 2023-06-21 | DNIPRO_CORRIDOR | FABDEM | 3 | 3.87 | 0.9481 |

These 1000 draws are the **primary uncertainty interval** of every
reconstructed area and volume: the Monte-Carlo median is the reported central value, p05–p95 is reported next to it, and relative
half-widths are taken over the median. The deterministic nominal run (draw 0, unperturbed inputs) is a diagnostic; its position
relative to the ensemble and the width of the interval are attributed to the error components by an ablation (T11d). The
stability of the quantiles against the ensemble size and a second seed is shown in T11c and FigS12 (finite ensembles carry their
own sampling uncertainty of tail quantiles, Roy and Gupta 2021), the day of the areal maximum is reported as a distribution over
the worlds (T12c), and the sensitivity of the connected area to a uniform water-surface offset is given in T11e and FigS13. A
cluster-normal emulator with 100 000 draws per day (p95g) is kept only as a computational diagnostic (T12d): it has no
connectivity and its total water-surface envelope is built around the nominal total, so it is not an uncertainty estimate and no
reported number rests on it. The structural choices — the rule, the terrain as delivered, the fallback distance, the handling of
gaps in the node series, the seed network, the connectivity neighbourhood — are outside the budget and are reported as
deterministic sensitivities (T12, FigS02), as are the planar surface and the absence of timing.

![FigS12](img/FigS12.jpg)

**FigS12.** Convergence of the Monte-Carlo quantiles with the ensemble size (T11c): p05, p50 and p95 of the newly inundated area, the total water-surface area and the new-water volume on 7 June from the first n = 40 … 1000 worlds of two independent seeds (solid / dashed), with a bootstrap 95 % interval of each quantile estimator (shaded).

![FigS13](img/FigS13.jpg)

**FigS13.** Sensitivity of the connected reconstruction to a uniform offset δ of the water surface on the nominal terrain (T11e): (a) newly inundated area of the Dnipro corridor on 7, 9 and 13 June for δ = −0.20 … +0.20 m; (b) the local derivative dA/dH. It shows where the connected area is sensitive to the water surface (connectivity thresholds); it is not a new model.

![FigS02](img/FigS02.jpg)

**FigS02.** structural sensitivity of the daily corridor new area (nominal runs, T12): the rule (connected ceiling with the river-network seed = primary, p42 HAND rule, ceiling only), the superseded seeding from every pre-breach water cell (ponds and canals; D-SEED), the memory variant (retained water; D-MEMORY sensitivity), the terrain as delivered (no residual bias removed), 4-connectivity, nodes unavailable beyond a 3-day gap, a river-aware water surface, no water surface from nodes more than 10 km away, and the superseded p59 closure with a +0.5 m margin. None of these is in the Monte-Carlo budget.

**Table T11d.** Ablation of the uncertainty budget (250 draws per variant, key dates): the full budget; terrain only; water surface only; baseline fixed at the nominal regime; with a per-day SWOT term of 0.05 m; without the interpolation term; without the nugget; with a single exponential instead of the nested covariance -- attribution of the width and of the offset between the nominal run and the ensemble median. [independent_physical] *(25 of 243 rows and 10 of 26 columns shown; full table: publication/tables/T11d.csv)*

| variant | date | region | area_semantics | A_central_km2 | A_p05_km2 | A_p50_km2 | A_p95_km2 | V_central_hm3 | V_p05_hm3 |
|---|---|---|---|---|---|---|---|---|---|
| full | 2023-06-06 | DNIPRO_CORRIDOR | terrain_reconstructed | 132.1416 | 141.3 | 151.3 | 163.6 | 300.6551 | 350.5 |
| full | 2023-06-06 | INHULETS_VALLEY_rect | terrain_reconstructed | 35.0164 | 32.3 | 34.5 | 38.9 | 85.4529 | 80.6 |
| full | 2023-06-06 | P42_FLOODPLAIN_DOMAIN | terrain_reconstructed | 107.0864 | 115.7 | 126.0 | 138.4 | 269.8931 | 313.1 |
| full | 2023-06-07 | DNIPRO_CORRIDOR | terrain_reconstructed | 214.862 | 214.9 | 233.8 | 251.6 | 484.5814 | 546.4 |
| full | 2023-06-07 | INHULETS_VALLEY_rect | terrain_reconstructed | 42.2636 | 40.2 | 42.5 | 46.4 | 126.2833 | 117.7 |
| full | 2023-06-07 | P42_FLOODPLAIN_DOMAIN | terrain_reconstructed | 170.5392 | 172.2 | 189.3 | 204.0 | 432.507 | 478.6 |
| full | 2023-06-08 | DNIPRO_CORRIDOR | terrain_reconstructed | 226.6052 | 184.1 | 239.4 | 266.1 | 497.7795 | 497.6 |
| full | 2023-06-08 | INHULETS_VALLEY_rect | terrain_reconstructed | 46.3884 | 44.4 | 46.8 | 50.5 | 160.5684 | 150.3 |
| full | 2023-06-08 | P42_FLOODPLAIN_DOMAIN | terrain_reconstructed | 181.1112 | 140.5 | 189.6 | 207.4 | 434.5268 | 425.6 |
| full | 2023-06-09 | DNIPRO_CORRIDOR | terrain_reconstructed | 171.258 | 185.0 | 201.2 | 229.7 | 445.0134 | 516.5 |
| full | 2023-06-09 | INHULETS_VALLEY_rect | terrain_reconstructed | 49.5932 | 47.5 | 49.9 | 53.7 | 198.85 | 186.8 |
| full | 2023-06-09 | P42_FLOODPLAIN_DOMAIN | terrain_reconstructed | 124.6536 | 137.1 | 150.4 | 170.1 | 362.0621 | 421.0 |
| full | 2023-06-11 | DNIPRO_CORRIDOR | terrain_reconstructed | 146.5456 | 161.2 | 180.6 | 231.6 | 341.2579 | 393.1 |
| full | 2023-06-11 | INHULETS_VALLEY_rect | terrain_reconstructed | 44.714 | 42.6 | 44.9 | 48.6 | 134.1546 | 124.4 |
| full | 2023-06-11 | P42_FLOODPLAIN_DOMAIN | terrain_reconstructed | 111.872 | 124.0 | 137.0 | 150.8 | 282.6471 | 325.6 |
| full | 2023-06-13 | DNIPRO_CORRIDOR | terrain_reconstructed | 112.1536 | 124.1 | 142.6 | 193.9 | 168.4162 | 200.6 |
| full | 2023-06-13 | INHULETS_VALLEY_rect | terrain_reconstructed | 37.006 | 34.6 | 37.3 | 40.8 | 70.4317 | 63.4 |
| full | 2023-06-13 | P42_FLOODPLAIN_DOMAIN | terrain_reconstructed | 91.4928 | 102.4 | 114.6 | 125.9 | 145.7323 | 171.9 |
| full | 2023-06-14 | DNIPRO_CORRIDOR | terrain_reconstructed | 90.0672 | 99.3 | 119.6 | 166.8 | 108.4043 | 127.4 |
| full | 2023-06-14 | INHULETS_VALLEY_rect | terrain_reconstructed | 31.212 | 29.1 | 31.4 | 35.5 | 48.4237 | 42.6 |
| full | 2023-06-14 | P42_FLOODPLAIN_DOMAIN | terrain_reconstructed | 76.5916 | 85.6 | 98.5 | 110.5 | 96.1026 | 111.0 |
| full | 2023-06-18 | DNIPRO_CORRIDOR | terrain_reconstructed | 33.8936 | 35.4 | 45.2 | 87.5 | 11.2059 | 11.8 |
| full | 2023-06-18 | INHULETS_VALLEY_rect | terrain_reconstructed | 10.0996 | 6.8 | 9.4 | 13.1 | 4.8518 | 3.1 |
| full | 2023-06-18 | P42_FLOODPLAIN_DOMAIN | terrain_reconstructed | 30.57 | 32.1 | 38.4 | 45.0 | 10.3684 | 10.9 |
| full | 2023-06-21 | DNIPRO_CORRIDOR | terrain_reconstructed | 4.0848 | 1.8 | 2.6 | 4.2 | 0.242 | 0.1 |

**Table T11c.** Convergence of the Monte-Carlo quantiles with the ensemble size (corridor; 7, 9 and 13 June): p05 / p50 / p95 and the p05-p95 width of A_new, W_total and V_new from the first n = 40, 100, 250, 500, 1000 draws of two independent seeds, with a bootstrap 95 % interval of each quantile estimator and the share of draws with the areal maximum on 7 / 8 June (finite ensembles carry their own sampling uncertainty of tail quantiles). [independent_physical] *(25 of 30 rows and 10 of 36 columns shown; full table: publication/tables/T11c.csv)*

| seed | n_draws | date | region | share_max_on_0607 | share_max_on_0608 | A_p05 | A_p05_boot_lo | A_p05_boot_hi | A_p50 |
|---|---|---|---|---|---|---|---|---|---|
| 20260929 | 40 | 2023-06-07 | DNIPRO_CORRIDOR | 0.525 | 0.4 | 223.4 | 183.2 | 225.5 | 236.5 |
| 20260929 | 40 | 2023-06-09 | DNIPRO_CORRIDOR | 0.525 | 0.4 | 186.7 | 181.9 | 192.4 | 199.5 |
| 20260929 | 40 | 2023-06-13 | DNIPRO_CORRIDOR | 0.525 | 0.4 | 125.1 | 123.2 | 128.7 | 141.6 |
| 20260929 | 100 | 2023-06-07 | DNIPRO_CORRIDOR | 0.44 | 0.48 | 188.7 | 177.7 | 221.7 | 233.0 |
| 20260929 | 100 | 2023-06-09 | DNIPRO_CORRIDOR | 0.44 | 0.48 | 186.4 | 182.9 | 189.0 | 201.0 |
| 20260929 | 100 | 2023-06-13 | DNIPRO_CORRIDOR | 0.44 | 0.48 | 125.5 | 123.2 | 128.5 | 143.2 |
| 20260929 | 250 | 2023-06-07 | DNIPRO_CORRIDOR | 0.368 | 0.544 | 214.9 | 183.2 | 221.0 | 233.8 |
| 20260929 | 250 | 2023-06-09 | DNIPRO_CORRIDOR | 0.368 | 0.544 | 185.0 | 182.8 | 187.0 | 201.2 |
| 20260929 | 250 | 2023-06-13 | DNIPRO_CORRIDOR | 0.368 | 0.544 | 124.1 | 120.9 | 125.8 | 142.6 |
| 20260929 | 500 | 2023-06-07 | DNIPRO_CORRIDOR | 0.384 | 0.536 | 217.0 | 190.1 | 220.5 | 233.9 |
| 20260929 | 500 | 2023-06-09 | DNIPRO_CORRIDOR | 0.384 | 0.536 | 185.7 | 184.0 | 187.3 | 200.7 |
| 20260929 | 500 | 2023-06-13 | DNIPRO_CORRIDOR | 0.384 | 0.536 | 125.4 | 124.0 | 126.5 | 142.7 |
| 20260929 | 1000 | 2023-06-07 | DNIPRO_CORRIDOR | 0.378 | 0.533 | 216.0 | 190.7 | 218.8 | 233.7 |
| 20260929 | 1000 | 2023-06-09 | DNIPRO_CORRIDOR | 0.378 | 0.533 | 185.9 | 185.0 | 187.1 | 200.9 |
| 20260929 | 1000 | 2023-06-13 | DNIPRO_CORRIDOR | 0.378 | 0.533 | 125.4 | 124.2 | 126.0 | 143.2 |
| 20261001 | 40 | 2023-06-07 | DNIPRO_CORRIDOR | 0.5 | 0.5 | 221.5 | 210.2 | 226.0 | 234.9 |
| 20261001 | 40 | 2023-06-09 | DNIPRO_CORRIDOR | 0.5 | 0.5 | 181.5 | 179.9 | 190.1 | 197.6 |
| 20261001 | 40 | 2023-06-13 | DNIPRO_CORRIDOR | 0.5 | 0.5 | 125.2 | 116.4 | 131.9 | 139.3 |
| 20261001 | 100 | 2023-06-07 | DNIPRO_CORRIDOR | 0.43 | 0.56 | 218.5 | 208.5 | 221.6 | 233.5 |
| 20261001 | 100 | 2023-06-09 | DNIPRO_CORRIDOR | 0.43 | 0.56 | 185.8 | 180.2 | 189.0 | 200.3 |
| 20261001 | 100 | 2023-06-13 | DNIPRO_CORRIDOR | 0.43 | 0.56 | 125.7 | 123.7 | 129.6 | 142.6 |
| 20261001 | 250 | 2023-06-07 | DNIPRO_CORRIDOR | 0.412 | 0.54 | 215.8 | 189.7 | 219.2 | 234.1 |
| 20261001 | 250 | 2023-06-09 | DNIPRO_CORRIDOR | 0.412 | 0.54 | 185.7 | 184.7 | 187.8 | 200.7 |
| 20261001 | 250 | 2023-06-13 | DNIPRO_CORRIDOR | 0.412 | 0.54 | 126.2 | 124.6 | 127.9 | 141.9 |
| 20261001 | 500 | 2023-06-07 | DNIPRO_CORRIDOR | 0.39 | 0.556 | 214.2 | 187.7 | 218.4 | 234.1 |

**Table T12c.** Day of the reconstructed areal maximum across the Monte-Carlo worlds: for A_new and W_total per region, the share of draws with the maximum on each day, and the day of the nominal run. A distribution conditional on the uncertainty model, not a probability of the true day. [independent_physical]

| region | quantity | date_of_maximum | n_draws_with_maximum | share | n_draws | nominal_date_of_maximum |
|---|---|---|---|---|---|---|
| DNIPRO_CORRIDOR | new_km2 | 2023-06-08 | 533 | 0.533 | 1000 | 2023-06-08 |
| DNIPRO_CORRIDOR | new_km2 | 2023-06-07 | 378 | 0.378 | 1000 | 2023-06-08 |
| DNIPRO_CORRIDOR | new_km2 | 2023-06-10 | 58 | 0.058 | 1000 | 2023-06-08 |
| DNIPRO_CORRIDOR | new_km2 | 2023-06-09 | 31 | 0.031 | 1000 | 2023-06-08 |
| INHULETS_VALLEY_rect | new_km2 | 2023-06-09 | 1000 | 1.0 | 1000 | 2023-06-09 |
| P42_FLOODPLAIN_DOMAIN | new_km2 | 2023-06-07 | 531 | 0.531 | 1000 | 2023-06-08 |
| P42_FLOODPLAIN_DOMAIN | new_km2 | 2023-06-08 | 434 | 0.434 | 1000 | 2023-06-08 |
| P42_FLOODPLAIN_DOMAIN | new_km2 | 2023-06-09 | 35 | 0.035 | 1000 | 2023-06-08 |
| DNIPRO_CORRIDOR | potential_km2 | 2023-06-08 | 475 | 0.475 | 1000 | 2023-06-08 |
| DNIPRO_CORRIDOR | potential_km2 | 2023-06-07 | 443 | 0.443 | 1000 | 2023-06-08 |
| DNIPRO_CORRIDOR | potential_km2 | 2023-06-10 | 56 | 0.056 | 1000 | 2023-06-08 |
| DNIPRO_CORRIDOR | potential_km2 | 2023-06-09 | 26 | 0.026 | 1000 | 2023-06-08 |
| INHULETS_VALLEY_rect | potential_km2 | 2023-06-09 | 1000 | 1.0 | 1000 | 2023-06-09 |
| P42_FLOODPLAIN_DOMAIN | potential_km2 | 2023-06-07 | 540 | 0.54 | 1000 | 2023-06-08 |
| P42_FLOODPLAIN_DOMAIN | potential_km2 | 2023-06-08 | 425 | 0.425 | 1000 | 2023-06-08 |
| P42_FLOODPLAIN_DOMAIN | potential_km2 | 2023-06-09 | 33 | 0.033 | 1000 | 2023-06-08 |
| P42_FLOODPLAIN_DOMAIN | potential_km2 | 2023-06-10 | 2 | 0.002 | 1000 | 2023-06-08 |

**Table T11e.** Sensitivity of the connected reconstruction to a uniform offset of the water surface (-0.20 ... +0.20 m) on the nominal terrain with the nominal baseline: W_total, A_new, V_new and the local derivatives dA/dH, dW/dH (corridor, Inhulets, p42 domain; 7, 9, 13 June). A sensitivity of the connectivity thresholds, not a new model. [independent_physical] *(25 of 63 rows and 9 of 9 columns shown; full table: publication/tables/T11e.csv)*

| date | region | delta_m | W_total_km2 | A_new_km2 | V_new_hm3 | dA_dH_km2_per_m | dW_dH_km2_per_m | note |
|---|---|---|---|---|---|---|---|---|
| 2023-06-07 | DNIPRO_CORRIDOR | -0.2 | 682.3 | 202.0 | 439.7 | 79.0 | 209.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | INHULETS_VALLEY_rect | -0.2 | 68.6 | 41.2 | 117.8 | 6.0 | 5.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | -0.2 | 489.6 | 164.7 | 397.2 | 39.0 | 112.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | DNIPRO_CORRIDOR | -0.1 | 703.2 | 209.9 | 463.1 | 59.7 | 172.3 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | INHULETS_VALLEY_rect | -0.1 | 69.1 | 41.8 | 122.1 | 4.7 | 4.3 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | -0.1 | 500.8 | 168.6 | 415.4 | 26.3 | 80.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | DNIPRO_CORRIDOR | -0.05 | 710.9 | 212.4 | 473.7 | 50.0 | 155.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | INHULETS_VALLEY_rect | -0.05 | 69.3 | 42.0 | 124.2 | 5.0 | 5.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | -0.05 | 504.0 | 169.6 | 423.9 | 19.0 | 50.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | DNIPRO_CORRIDOR | 0.0 | 718.7 | 214.9 | 484.6 | 49.0 | 178.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | INHULETS_VALLEY_rect | 0.0 | 69.6 | 42.3 | 126.3 | 5.0 | 5.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | 0.0 | 505.8 | 170.5 | 432.5 | 20.0 | 36.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | DNIPRO_CORRIDOR | 0.05 | 728.7 | 217.3 | 495.5 | 52.0 | 199.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | INHULETS_VALLEY_rect | 0.05 | 69.8 | 42.5 | 128.4 | 4.0 | 5.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | 0.05 | 507.6 | 171.6 | 441.1 | 23.0 | 32.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | DNIPRO_CORRIDOR | 0.1 | 738.6 | 220.1 | 506.7 | 96.0 | 203.7 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | INHULETS_VALLEY_rect | 0.1 | 70.1 | 42.7 | 130.5 | 4.3 | 5.3 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | 0.1 | 509.0 | 172.8 | 449.8 | 21.3 | 25.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | DNIPRO_CORRIDOR | 0.2 | 760.1 | 237.7 | 530.2 | 176.0 | 215.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | INHULETS_VALLEY_rect | 0.2 | 70.5 | 43.2 | 134.8 | 5.0 | 4.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | 0.2 | 510.9 | 174.4 | 467.3 | 16.0 | 19.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-09 | DNIPRO_CORRIDOR | -0.2 | 640.0 | 162.7 | 407.1 | 27.0 | 143.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-09 | INHULETS_VALLEY_rect | -0.2 | 76.2 | 48.9 | 189.0 | 3.0 | 4.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-09 | P42_FLOODPLAIN_DOMAIN | -0.2 | 442.7 | 121.1 | 334.4 | 10.0 | 70.0 | sensitivity of the connected inundation to a uniform water-s |
| 2023-06-09 | DNIPRO_CORRIDOR | -0.1 | 654.3 | 165.4 | 423.6 | 67.7 | 174.3 | sensitivity of the connected inundation to a uniform water-s |

**Table T12d.** Computational diagnostic, not evidence (maintainer decision D-EMU, 2026-09-29): the 100 000-draw cluster-normal emulator (p95g) per region and key date. It has no connectivity, its total water-surface envelope is built around the nominal total, and its volumes are unanchored; it is not an uncertainty estimate and no reported number rests on it. The primary interval is the Monte-Carlo ensemble (T12). [contextual] *(25 of 48 rows and 10 of 26 columns shown; full table: publication/tables/T12d.csv)*

| region | date | n_draws | area_semantics | A_new_km2_mean | A_new_km2_p05 | A_new_km2_p25 | A_new_km2_p50 | A_new_km2_p75 | A_new_km2_p95 |
|---|---|---|---|---|---|---|---|---|---|
| DNIPRO_CORRIDOR | 2023-06-05 | 100000 | terrain_reconstructed | 2.19 | 0.0 | 0.0 | 0.0 | 0.0 | 16.66 |
| DNIPRO_CORRIDOR | 2023-06-06 | 100000 | terrain_reconstructed | 165.33 | 128.99 | 149.69 | 164.77 | 180.29 | 203.4 |
| DNIPRO_CORRIDOR | 2023-06-07 | 100000 | terrain_reconstructed | 237.34 | 201.22 | 221.77 | 236.67 | 252.38 | 275.54 |
| DNIPRO_CORRIDOR | 2023-06-08 | 100000 | terrain_reconstructed | 238.46 | 202.19 | 222.8 | 237.97 | 253.48 | 276.75 |
| DNIPRO_CORRIDOR | 2023-06-09 | 100000 | terrain_reconstructed | 227.48 | 191.32 | 211.87 | 226.9 | 242.46 | 265.48 |
| DNIPRO_CORRIDOR | 2023-06-10 | 100000 | terrain_reconstructed | 202.48 | 166.52 | 187.08 | 201.97 | 217.3 | 240.13 |
| DNIPRO_CORRIDOR | 2023-06-11 | 100000 | terrain_reconstructed | 175.52 | 140.04 | 160.23 | 174.88 | 190.23 | 212.97 |
| DNIPRO_CORRIDOR | 2023-06-12 | 100000 | terrain_reconstructed | 151.1 | 116.09 | 135.93 | 150.54 | 165.5 | 188.35 |
| DNIPRO_CORRIDOR | 2023-06-13 | 100000 | terrain_reconstructed | 129.67 | 94.55 | 114.5 | 129.07 | 144.19 | 166.85 |
| DNIPRO_CORRIDOR | 2023-06-14 | 100000 | terrain_reconstructed | 109.21 | 73.95 | 93.93 | 108.63 | 123.86 | 146.73 |
| DNIPRO_CORRIDOR | 2023-06-15 | 100000 | terrain_reconstructed | 93.91 | 58.24 | 78.52 | 93.31 | 108.68 | 131.58 |
| DNIPRO_CORRIDOR | 2023-06-16 | 100000 | terrain_reconstructed | 77.59 | 41.57 | 62.14 | 77.05 | 92.48 | 115.51 |
| DNIPRO_CORRIDOR | 2023-06-18 | 100000 | terrain_reconstructed | 41.97 | 11.27 | 24.45 | 40.42 | 56.81 | 80.61 |
| DNIPRO_CORRIDOR | 2023-06-21 | 100000 | terrain_reconstructed | 7.75 | 0.0 | 0.0 | 0.0 | 10.68 | 37.3 |
| DNIPRO_CORRIDOR | 2023-06-25 | 100000 | terrain_reconstructed | 2.73 | 0.0 | 0.0 | 0.0 | 0.0 | 18.6 |
| DNIPRO_CORRIDOR | 2023-06-30 | 100000 | terrain_reconstructed | 4.26 | 0.0 | 0.0 | 0.0 | 4.47 | 23.94 |
| INHULETS_VALLEY_rect | 2023-06-05 | 100000 | terrain_reconstructed | 0.05 | 0.0 | 0.0 | 0.0 | 0.0 | 0.19 |
| INHULETS_VALLEY_rect | 2023-06-06 | 100000 | terrain_reconstructed | 33.87 | 30.94 | 32.65 | 33.85 | 35.07 | 36.88 |
| INHULETS_VALLEY_rect | 2023-06-07 | 100000 | terrain_reconstructed | 41.48 | 38.85 | 40.37 | 41.45 | 42.56 | 44.22 |
| INHULETS_VALLEY_rect | 2023-06-08 | 100000 | terrain_reconstructed | 45.51 | 42.87 | 44.4 | 45.48 | 46.59 | 48.24 |
| INHULETS_VALLEY_rect | 2023-06-09 | 100000 | terrain_reconstructed | 48.49 | 45.85 | 47.37 | 48.47 | 49.58 | 51.23 |
| INHULETS_VALLEY_rect | 2023-06-10 | 100000 | terrain_reconstructed | 46.4 | 43.75 | 45.28 | 46.37 | 47.48 | 49.14 |
| INHULETS_VALLEY_rect | 2023-06-11 | 100000 | terrain_reconstructed | 43.84 | 41.2 | 42.72 | 43.81 | 44.93 | 46.59 |
| INHULETS_VALLEY_rect | 2023-06-12 | 100000 | terrain_reconstructed | 40.91 | 38.26 | 39.79 | 40.87 | 41.99 | 43.66 |
| INHULETS_VALLEY_rect | 2023-06-13 | 100000 | terrain_reconstructed | 36.56 | 33.81 | 35.4 | 36.53 | 37.69 | 39.42 |

### 3.5 The reservoir: sloped pool surface, depth and storage balance

Above the dam, the daily pool surface is interpolated along the river chainage between the SWOT outlet nodes, the Nikopol post
and the Rozumivka gauge (three or four level points per day) and integrated over the seamless terrain–bed model (50 m) inside the
pre-breach pool polygon: pool water area and volume (T21), and water depth as surface minus terrain on the wet cells (Fig10,
T21b). The storage balance gives the *daily-mean effective release*, −dV/dt + Q_in, with the DniproHES release as the inflow
Q_in — a daily mean, not an instantaneous breach discharge. As a classical, terrain-free reference the design level–volume curve
(Table 19 of the reservoir monograph; T27) is read at the observed levels; it is defined between 10 and 18 m (BS-77) and left
undefined outside that range, and weekly storage changes are sums of the daily changes over the same days, one series per level
source (T27b, T27c). The pool levels are in Paper 1's frame (the SWOT outlet with the reservoir closure of Paper 1, so that the pool surface falls
from 17.61 m on 31 May to 5.71 m on 13 June at the outlet, as in
Paper 1); a Sentinel-6A altimetry series (G-REALM) is plotted as a check but not used as an anchor, because its vertical chain is
not part of that frame and on 9 June it stood above the Nikopol post 50 km upstream. On 13 June the Nikopol post reported only an
upper bound (the level had fallen below it), so the pool surface, area, volume and depth of 12–13 June are upper estimates. The
reservoir side is context for the downstream reconstruction; Sentinel-2, observing the whole pool on 20 June, is its
cross-sensor check (§4.3.5).

![Fig10](img/Fig10.jpg)

**Fig10 Water depth in the Kakhovka reservoir: the full pool and the drawdown.** Depth = the daily sloped water surface of the pool (SWOT outlet nodes, Nikopol post and Rozumivka gauge interpolated along the river chainage; p95f) minus the 50 m seamless terrain–bed model inside the pre-breach pool polygon: (a) 5 June, the full pool the day before the breach; (b) 7 June; (c) 9 June; (d) 13 June, when the pool had become a river. Titles give the wet area, the volume (the pool volume of T21) and the mean depth (T21b). Terrain-reconstructed, not observed depth; the pool surface sloped by up to 4 m during the drawdown, so a level-pool reading of the design curve brackets the same days (T27b). The 13 June values are upper estimates (the Nikopol post reported only an upper bound). The emptying of the pool in area is mapped from Sentinel-2 in Fig11.

**Table T21.** Kakhovka pool during the drawdown, per day: levels at the outlet (SWOT), Nikopol (press) and Rozumivka (gauge), surface gradient, pool water area and volume under the sloped surface (seamless DEM inside the pre-breach pool polygon), daily volume change, DniproHES inflow, the daily-mean effective release (-dV/dt + Q_in; not an instantaneous breach discharge), and the downstream new-water volume and total water surface (terrain reconstruction) with the Kherson stage. surface_upper_bound = True on the days whose sloped surface rests on the censored upper bound of the Nikopol post (12-13 June: the level had fallen below the post): pool area, volume and depth of those days are upper estimates and the effective release a lower estimate. [independent_physical] *(25 of 46 rows and 10 of 23 columns shown; full table: publication/tables/T21.csv)*

| date | n_level_sources | H_outlet_m | H_nikopol_m | H_rozumivka_m | gradient_m | A_pool_km2 | V_pool_km3 | A_table19_at_outlet_km2 | Q_in_dniprohes_m3s |
|---|---|---|---|---|---|---|---|---|---|
| 2023-05-26 | 2 | 17.605319994880173 |  | 17.49358757607012 | -0.1117324188100532 | 2136.6 | 19.338 | 2202.290879825926 | 3370.0 |
| 2023-05-27 | 2 | 17.605319994880173 |  | 17.47858757607012 | -0.1267324188100538 | 2136.5 | 19.318 | 2202.290879825926 | 3330.0 |
| 2023-05-28 | 2 | 17.605319994880173 |  | 17.388587576070115 | -0.2167324188100572 | 2136.0 | 19.193 | 2202.290879825926 | 2700.0 |
| 2023-05-29 | 3 | 17.605319994880173 |  | 17.398587576070117 | -0.2067324188100556 | 2135.7 | 18.92 | 2202.290879825926 | 2550.0 |
| 2023-05-30 | 2 | 17.605319994880173 |  | 17.40858757607012 | -0.1967324188100541 | 2136.1 | 19.221 | 2202.290879825926 | 2610.0 |
| 2023-05-31 | 2 | 17.605319994880173 |  | 17.378587576070117 | -0.2267324188100552 | 2135.9 | 19.179 | 2202.290879825926 | 2540.0 |
| 2023-06-01 | 2 | 17.605319994880173 |  | 17.353587576070115 | -0.2517324188100573 | 2135.8 | 19.145 | 2202.290879825926 | 2470.0 |
| 2023-06-02 | 3 | 17.605319994880173 |  | 17.323587576070118 | -0.2817324188100549 | 2135.0 | 18.716 | 2202.290879825926 | 2570.0 |
| 2023-06-03 | 2 | 17.605319994880173 |  | 17.258587576070116 | -0.3467324188100562 | 2135.0 | 19.014 | 2202.290879825926 | 2190.0 |
| 2023-06-04 | 3 | 17.605319994880173 |  | 17.073587576070118 | -0.531732418810055 | 2115.2 | 18.554 | 2202.290879825926 | 1660.0 |
| 2023-06-05 | 2 | 17.605319994880173 |  | 17.083587576070116 | -0.5217324188100569 | 2132.0 | 18.772 | 2202.290879825926 | 1750.0 |
| 2023-06-06 | 3 | 12.576460601213077 | 16.611511191859286 | 16.693587576070115 | 4.11712697485704 | 2092.0 | 15.932 | 1831.041401891048 | 1960.0 |
| 2023-06-07 | 3 | 12.127531501213074 | 14.581511191859288 | 15.278587576070116 | 3.151056074857042 | 2054.2 | 12.707 | 1764.6901031965178 | 2730.0 |
| 2023-06-08 | 4 | 10.965197150583164 | 13.221511191859287 | 14.528587576070116 | 3.5633904254869506 | 2012.5 | 10.441 | 1575.633515599138 | 1880.0 |
| 2023-06-09 | 3 | 10.130542775898125 | 11.911511191859288 | 13.778587576070114 | 3.6480448001719896 | 1956.5 | 8.32 |  | 1730.0 |
| 2023-06-10 | 3 | 8.897195725898122 | 10.371511191859286 | 13.793587576070117 | 4.8963918501719945 | 1894.2 | 6.391 |  | 1940.0 |
| 2023-06-11 | 3 | 7.833892767459805 | 9.521511191859286 | 13.838587576070116 | 6.004694808610312 | 1837.5 | 5.251 |  | 1930.0 |
| 2023-06-12 | 3 | 6.770589809021487 | 9.346511191859284 | 13.838587576070116 | 7.067997767048629 | 1815.0 | 4.73 |  | 2450.0 |
| 2023-06-13 | 3 | 5.70728685058317 | 9.171511191859286 | 13.838587576070116 | 8.131300725486946 | 1790.0 | 4.218 |  | 2110.0 |
| 2023-06-14 | 1 | 4.916517825898124 |  |  |  |  |  |  | 1720.0 |
| 2023-06-15 | 1 | 4.280141325898122 |  |  |  |  |  |  | 1380.0 |
| 2023-06-16 | 1 | 3.64376482589812 |  |  |  |  |  |  | 1580.0 |
| 2023-06-17 | 1 | 3.2143825258981216 |  |  |  |  |  |  | 1300.0 |
| 2023-06-18 | 1 | 2.4898126505831715 |  |  |  |  |  |  | 1140.0 |
| 2023-06-19 | 1 | 2.154598963240646 |  |  |  |  |  |  | 1290.0 |

**Table T21b.** Water depth in the Kakhovka pool from the p95f model (daily sloped surface over the 50 m seamless terrain-bed model, the wet mask of p95h / Fig11): the full pool on 5 June and the drawdown on 7, 9 and 13 June -- wet area, volume (reproduces T21 to 1e-3 km3), mean / median / p95 / maximum depth, the share deeper than 5 m and the surface at the outlet and upstream. Terrain-reconstructed, not observed depth; maps in Fig10. [contextual] *(4 of 4 rows and 10 of 13 columns shown; full table: publication/tables/T21b.csv)*

| date | n_level_sources | wet_km2 | volume_km3 | V_pool_p95f_km3 | depth_mean_m | depth_median_m | depth_p95_m | depth_max_m | share_wet_deeper_than_5m |
|---|---|---|---|---|---|---|---|---|---|
| 2023-06-05 | 2 | 2132.0 | 18.772 | 18.772 | 8.8 | 8.09 | 15.26 | 32.62 | 0.832 |
| 2023-06-07 | 3 | 2054.2 | 12.707 | 12.707 | 6.19 | 5.78 | 10.77 | 27.29 | 0.59 |
| 2023-06-09 | 3 | 1956.5 | 8.32 | 8.32 | 4.25 | 3.74 | 8.58 | 25.26 | 0.372 |
| 2023-06-13 | 3 | 1790.0 | 4.218 | 4.218 | 2.36 | 2.07 | 5.01 | 20.93 | 0.05 |

**Table T27b.** The observed 2023 levels, 1 February - 10 July, read on the design curve of T27 (level - 0.185 m -> historical Baltic): before the breach the Rozumivka gauge 80959 (terms 08/20 averaged; the only 2023 daily series; the pool was level, so one gauge reads the whole pool), with G-REALM, ICESat-2 and the SWOT outlet as checks; from 26 May the p95f daily levels (the pre-breach outlet value is HELD, not observed daily -- flagged). 'Outlet' = SWOT nodes at 0 km, the pool just above the dam; for comparison the SWOT level 0.5 km below the dam (p59/p60) and the Kherson gauge 80805, with the head across the dam and pool-minus-Kherson. Design volume and area at the Rozumivka and at the outlet level (during the drawdown the surface sloped by up to 4 m, so the two readings bracket the pool), the volume released from the design curve, and the storage balance with the DniproHES inflow, computed separately for each level source and never switched inside a series (review F14): Q_out = Q_in - dV_design/dt on the Rozumivka series (the whole period; the upper-bound level during the drawdown) and on the outlet series (from 26 May; the lower-bound level) = the outflow through the Kakhovka HPP before the breach and the daily-mean effective release after it (design-curve counterpart of T21; a residual without lateral inflow, evaporation or withdrawals); rozumivka_source names the source of every level used. NaN once a level is below 10.0 m BS, the lowest level of Table 19 (never the endpoint value). Context for Paper 4. [independent_physical] *(25 of 160 rows and 10 of 41 columns shown; full table: publication/tables/T27b.csv)*

| date | H_rozumivka_m | H_grealm_m | H_icesat2_m | H_outlet_m | H_nikopol_m | H_kherson_m | H_below_dam_0_5km_m | head_across_dam_m | pool_minus_kherson_m |
|---|---|---|---|---|---|---|---|---|---|
| 2023-02-01 | 14.129 |  |  |  |  |  |  |  |  |
| 2023-02-02 | 14.134 |  |  |  |  |  |  |  |  |
| 2023-02-03 | 14.089 |  |  |  |  |  |  |  |  |
| 2023-02-04 | 14.059 |  |  |  |  |  |  |  |  |
| 2023-02-05 | 14.029 |  |  |  |  |  |  |  |  |
| 2023-02-06 | 14.009 |  |  |  |  |  |  |  |  |
| 2023-02-07 | 13.979 |  |  |  |  |  |  |  |  |
| 2023-02-08 | 13.934 |  |  |  |  |  |  |  |  |
| 2023-02-09 | 14.109 |  |  |  |  |  |  |  |  |
| 2023-02-10 | 14.069 |  |  |  |  |  |  |  |  |
| 2023-02-11 | 14.119 |  |  |  |  |  |  |  |  |
| 2023-02-12 | 13.959 |  |  |  |  |  |  |  |  |
| 2023-02-13 | 14.009 |  |  |  |  |  |  |  |  |
| 2023-02-14 | 14.154 |  |  |  |  |  |  |  |  |
| 2023-02-15 | 14.134 |  |  |  |  |  |  |  |  |
| 2023-02-16 | 14.264 |  |  |  |  |  |  |  |  |
| 2023-02-17 | 14.244 |  |  |  |  |  |  |  |  |
| 2023-02-18 | 14.199 |  |  |  |  |  |  |  |  |
| 2023-02-19 | 14.179 |  |  |  |  |  |  |  |  |
| 2023-02-20 | 14.224 |  |  |  |  |  |  |  |  |
| 2023-02-21 | 14.399 |  |  |  |  |  |  |  |  |
| 2023-02-22 | 14.324 |  |  |  |  |  |  |  |  |
| 2023-02-23 | 14.384 |  |  |  |  |  |  |  |  |
| 2023-02-24 | 14.284 |  |  |  |  |  |  |  |  |
| 2023-02-25 | 14.374 |  |  |  |  |  |  |  |  |

**Table T27c.** The filling of the Kakhovka reservoir in spring 2023, week by week on the design curve (Rozumivka series only; the pool was level before the breach). Every term of a week covers the same days (review F14): the change of storage is the sum of the week's daily changes, i.e. V on the week's last day minus V on the previous week's last day; inflow = DniproHES releases summed over those days; outflow through the Kakhovka HPP = inflow minus the change of storage (a residual: lateral inflow, evaporation and withdrawals are not in it). A week with a missing day has no balance (complete = False). Levels and means are descriptive. From 13.93 m / 13.48 km3 on 2023-02-08 to 17.62 m / 21.33 km3 on 2023-05-05 (7.85 km3 stored out of 22.68 km3 of inflow); 17.08 m / 20.14 km3 on 5 June. Design data + gauge + releases; no DEM. [contextual] *(19 of 19 rows and 10 of 20 columns shown; full table: publication/tables/T27c.csv)*

| week | date_first | date_last | n_days | n_days_dV | n_days_inflow | H_rozumivka_mean_m | H_rozumivka_last_m | H_grealm_mean_m | H_icesat2_mean_m |
|---|---|---|---|---|---|---|---|---|---|
| 2023-01-30 | 2023-02-01 | 2023-02-05 | 5 | 4 | 5 | 14.088 | 14.029 |  |  |
| 2023-02-06 | 2023-02-06 | 2023-02-12 | 7 | 7 | 7 | 14.025 | 13.959 |  |  |
| 2023-02-13 | 2023-02-13 | 2023-02-19 | 7 | 7 | 7 | 14.169 | 14.179 |  |  |
| 2023-02-20 | 2023-02-20 | 2023-02-26 | 7 | 7 | 7 | 14.336 | 14.364 |  |  |
| 2023-02-27 | 2023-02-27 | 2023-03-05 | 7 | 7 | 7 | 14.558 | 14.544 |  |  |
| 2023-03-06 | 2023-03-06 | 2023-03-12 | 7 | 7 | 7 | 14.66 | 14.659 |  |  |
| 2023-03-13 | 2023-03-13 | 2023-03-19 | 7 | 7 | 7 | 14.682 | 14.724 |  |  |
| 2023-03-20 | 2023-03-20 | 2023-03-26 | 7 | 7 | 7 | 14.777 | 14.834 |  |  |
| 2023-03-27 | 2023-03-27 | 2023-04-02 | 7 | 7 | 7 | 14.939 | 15.014 |  |  |
| 2023-04-03 | 2023-04-03 | 2023-04-09 | 7 | 7 | 7 | 15.305 | 15.359 |  |  |
| 2023-04-10 | 2023-04-10 | 2023-04-16 | 7 | 7 | 7 | 15.818 | 16.084 |  |  |
| 2023-04-17 | 2023-04-17 | 2023-04-23 | 7 | 7 | 7 | 16.495 | 16.514 |  |  |
| 2023-04-24 | 2023-04-24 | 2023-04-30 | 7 | 7 | 7 | 16.933 | 17.219 |  |  |
| 2023-05-01 | 2023-05-01 | 2023-05-07 | 7 | 7 | 7 | 17.495 | 17.434 |  |  |
| 2023-05-08 | 2023-05-08 | 2023-05-14 | 7 | 7 | 7 | 17.529 | 17.514 | 17.482 |  |
| 2023-05-15 | 2023-05-15 | 2023-05-21 | 7 | 7 | 7 | 17.475 | 17.429 | 17.502 |  |
| 2023-05-22 | 2023-05-22 | 2023-05-28 | 7 | 7 | 7 | 17.459 | 17.389 |  | 17.223 |
| 2023-05-29 | 2023-05-29 | 2023-06-04 | 7 | 7 | 7 | 17.314 | 17.074 | 17.472 | 17.112 |
| 2023-06-05 | 2023-06-05 | 2023-06-05 | 1 | 1 | 1 | 17.084 | 17.084 |  |  |

### 3.6 Independent checks: withheld gauges, Sentinel-1 and the disagreement ontology, ICESat-2

Three river gauges of the 2023 hydrological yearbook have distinct roles: Kherson (80805) is an input and the anchor of the water
surface; the Inhulets gauge Kalynivske (80575) and the liman gauge Mykolaiv (98027) are withheld from the reconstruction and serve
as independent validation sites for two different failure modes — the tributary backwater and the western delta. Their daily
means (cm above the gauge zero, the zero read from the yearbook sheet, EVRF2019 by the EPSG:9902 grid step) are compared with
the reconstructed surface at the gauge as an absolute error and as an event-relative error, (H_rec − H_rec,pre) −
(H_gauge − H_gauge,pre), which is free of any constant datum offset between the two series; peaks and rises use the yearbook's
highest level of the year (T17c–T17f). The agreement of the SWOT input with the Kherson gauge through the breach fortnight
is part of Paper 1's validation (+1.9 cm, NMAD 6.4 cm over 13 June – 8 July; −8.8 cm on the peak days 6–12 June) and is not
repeated; T17 lists the same comparison on this paper's node selection as an input check.

**Table T17c.** Inhulets gauge Kalynivske (80575; UkrHMC yearbook 2023 table 1.2, daily means in cm above the gauge zero, zero -1.34 m BS from the sheet header -> EVRF2019 by the EPSG:9902 grid step) per day against the reconstructed water surface at the gauge (not an input of the reconstruction; in the gauge-node sensitivity it is), with the support of that surface (nearest SWOT node, river, distance), the Kherson gauge, the upstream Inhulets posts (Kryvyi Rih 80568, Iskrivka 80564: no flood from upstream, i.e. the rise is Dnipro backwater), the terrain at the gauge cell and the days with reconstructed new inundation there. Gauge position 47°6'59" N 32°57'38" E (station catalogue, Kakhovka hydrometeorological observatory); date-only daily values (means of more frequent observations during the event). The yearbook remark (vol. 2, item 114) attributes the maximum to the destruction of the Kakhovka HPP, gives high water on 7-18 June with houses and the road bridge 0.75 km upstream flooded, and notes that the levelling of pile No. 5 changed during the hazard (a possible datum step of unknown size and date: post-event levels are not comparable with pre-event levels without it). [independent_physical] *(25 of 46 rows and 10 of 30 columns shown; full table: publication/tables/T17c.csv)*

| date | post_id | lat | lon | stage_cm | zero_bs77_m | delta_epsg9902_m | H_evrf2019_m | H_reconstructed_primary_m | support_primary |
|---|---|---|---|---|---|---|---|---|---|
| 2023-05-26 | 80575 | 47.11638888888889 | 32.96055555555556 | 174.0 | -1.34 | 0.209 | 0.609 | 1.324 | nearest_node_fallback |
| 2023-05-27 | 80575 | 47.11638888888889 | 32.96055555555556 | 174.0 | -1.34 | 0.209 | 0.609 | 1.39 | nearest_node_fallback |
| 2023-05-28 | 80575 | 47.11638888888889 | 32.96055555555556 | 173.0 | -1.34 | 0.209 | 0.599 | 1.295 | nearest_node_fallback |
| 2023-05-29 | 80575 | 47.11638888888889 | 32.96055555555556 | 167.0 | -1.34 | 0.209 | 0.539 | 1.341 | nearest_node_fallback |
| 2023-05-30 | 80575 | 47.11638888888889 | 32.96055555555556 | 167.0 | -1.34 | 0.209 | 0.539 | 1.408 | nearest_node_fallback |
| 2023-05-31 | 80575 | 47.11638888888889 | 32.96055555555556 | 167.0 | -1.34 | 0.209 | 0.539 | 1.39 | nearest_node_fallback |
| 2023-06-01 | 80575 | 47.11638888888889 | 32.96055555555556 | 171.0 | -1.34 | 0.209 | 0.579 | 1.352 | nearest_node_fallback |
| 2023-06-02 | 80575 | 47.11638888888889 | 32.96055555555556 | 174.0 | -1.34 | 0.209 | 0.609 | 1.376 | nearest_node_fallback |
| 2023-06-03 | 80575 | 47.11638888888889 | 32.96055555555556 | 172.0 | -1.34 | 0.209 | 0.589 | 1.325 | nearest_node_fallback |
| 2023-06-04 | 80575 | 47.11638888888889 | 32.96055555555556 | 164.0 | -1.34 | 0.209 | 0.509 | 1.315 | nearest_node_fallback |
| 2023-06-05 | 80575 | 47.11638888888889 | 32.96055555555556 | 161.0 | -1.34 | 0.209 | 0.479 | 1.22 | nearest_node_fallback |
| 2023-06-06 | 80575 | 47.11638888888889 | 32.96055555555556 | 185.0 | -1.34 | 0.209 | 0.719 | 10.218 | nearest_node_fallback |
| 2023-06-07 | 80575 | 47.11638888888889 | 32.96055555555556 | 341.0 | -1.34 | 0.209 | 2.279 | 10.621 | nearest_node_fallback |
| 2023-06-08 | 80575 | 47.11638888888889 | 32.96055555555556 | 576.0 | -1.34 | 0.209 | 4.629 | 9.781 | nearest_node_fallback |
| 2023-06-09 | 80575 | 47.11638888888889 | 32.96055555555556 | 743.0 | -1.34 | 0.209 | 6.299 | 8.857 | nearest_node_fallback |
| 2023-06-10 | 80575 | 47.11638888888889 | 32.96055555555556 | 758.0 | -1.34 | 0.209 | 6.449 | 7.906 | nearest_node_fallback |
| 2023-06-11 | 80575 | 47.11638888888889 | 32.96055555555556 | 710.0 | -1.34 | 0.209 | 5.969 | 6.888 | nearest_node_fallback |
| 2023-06-12 | 80575 | 47.11638888888889 | 32.96055555555556 | 653.0 | -1.34 | 0.209 | 5.399 | 5.968 | nearest_node_fallback |
| 2023-06-13 | 80575 | 47.11638888888889 | 32.96055555555556 | 591.0 | -1.34 | 0.209 | 4.779 | 5.039 | nearest_node_fallback |
| 2023-06-14 | 80575 | 47.11638888888889 | 32.96055555555556 | 529.0 | -1.34 | 0.209 | 4.159 | 4.204 | nearest_node_fallback |
| 2023-06-15 | 80575 | 47.11638888888889 | 32.96055555555556 | 468.0 | -1.34 | 0.209 | 3.549 | 3.619 | nearest_node_fallback |
| 2023-06-16 | 80575 | 47.11638888888889 | 32.96055555555556 | 408.0 | -1.34 | 0.209 | 2.949 | 3.033 | nearest_node_fallback |
| 2023-06-17 | 80575 | 47.11638888888889 | 32.96055555555556 | 350.0 | -1.34 | 0.209 | 2.369 | 2.559 | nearest_node_fallback |
| 2023-06-18 | 80575 | 47.11638888888889 | 32.96055555555556 | 295.0 | -1.34 | 0.209 | 1.819 | 2.132 | nearest_node_fallback |
| 2023-06-19 | 80575 | 47.11638888888889 | 32.96055555555556 | 244.0 | -1.34 | 0.209 | 1.309 | 1.878 | nearest_node_fallback |

**Table T17f.** Summary of T17e: the liman's highest level of the year (instantaneous, from the yearbook) and highest daily mean, its rise and timing against Kherson, the Kherson - Mykolaiv head, and the reconstructed surface at the liman, which comes from the westernmost SWOT node (E 457.6 km), unobserved from 6 to 22 June and therefore interpolated flat across the flood. [independent_physical]

| id | item | value |
|---|---|---|
| gauge_max | liman maximum at Mykolaiv: the yearbook's highest level | 602 cm above the gauge zero = +1.02 m BS-77 = 1.22 m EVRF201 |
| gauge_max_daily_mean | highest daily mean | 596 cm = 1.16 m EVRF2019 on 2023-06-08 |
| pre_breach_level | pre-breach level 26 May - 5 June (median of the daily means) | 497 cm = -0.03 m BS-77 = 0.17 m EVRF2019 |
| rise | rise to the highest level (in daily means) | 1.05 m (0.99 m); Kherson: 5.18 m (daily values = yearbook 80 |
| pre_breach_evrf | pre-breach level, m EVRF2019 | 0.17 m EVRF2019 |
| highest_evrf | highest level, m EVRF2019 and date | 1.22 m EVRF2019 on 2023-06-08 |
| rise_m | rise to the highest level, m | 1.05 m |
| lag_after_kherson | lag of the liman maximum after the Kherson peak stage | 0 d |
| late_june | 21-30 June above the pre-breach level (median) | +0.16 m |
| kherson_minus_mykolaiv | Kherson - Mykolaiv water level: pre-breach median / on the K | +0.39 m / +4.61 m |
| reconstruction_support | reconstructed surface at the gauge: nearest SWOT node / Kher | 22511100040015 (Dnipro), 59.5 km; capped at the Kherson gaug |
| serving_node_unobserved | that node without observation | 2023-06-06 .. 2023-06-22 |
| serving_node_gap | observations of that node around the event | E 457.6 km, N 5156.4 km (EPSG:32636): last observed 2023-06- |
| recon_minus_gauge | reconstruction - gauge: pre-breach median / 6-20 June median | +0.20 m / -0.15 m (-0.82 .. +0.03) |
| e_rise_at_max | event-relative error (reconstructed rise - gauge rise) on th | -1.06 m on 2023-06-08 (reconstructed rise -0.07 m) |
| e_abs_at_max | absolute error (reconstruction - gauge, daily means) on the  | -0.82 m on 2023-06-08 |
| role | role of the gauge | withheld validation site (never an input): tests the water s |
| flags | days flagged in the yearbook | 2023-06-06 '/', 2023-06-07 '/', 2023-06-08 '/', 2023-06-09 ' |
| caveats | caveats | graph zero -5.00 m BS-77 is a rounded nominal (absorbs a zer |

**Table T17.** SWOT-input consistency at Kherson after re-anchoring: nodes within 3 km of the gauge, daily median vs the daily gauge (river yearbook, EVRF2019). The frame validation itself is Paper 1; this only checks the p95 input. [independent_physical] *(4 of 4 rows and 10 of 11 columns shown; full table: publication/tables/T17.csv)*

| period | n_days | bias_m | median_m | MAE_m | RMSE_m | NMAD_m | min_m | max_m | independent_unit |
|---|---|---|---|---|---|---|---|---|---|
| all days | 36 | 0.004 | -0.006 | 0.048 | 0.06 | 0.066 | -0.093 | 0.163 | day (one 11:00 UTC overpass vs a date-only daily gauge value |
| pre-breach 05-26..06-05 | 11 | -0.009 | -0.021 | 0.045 | 0.063 | 0.051 | -0.083 | 0.163 | day (one 11:00 UTC overpass vs a date-only daily gauge value |
| rise and peak 06-06..06-14 | 7 | 0.07 | 0.09 | 0.07 | 0.079 | 0.022 | -0.003 | 0.105 | day (one 11:00 UTC overpass vs a date-only daily gauge value |
| recession 06-15..07-10 | 18 | -0.014 | -0.019 | 0.041 | 0.047 | 0.048 | -0.093 | 0.064 | day (one 11:00 UTC overpass vs a date-only daily gauge value |

On each Sentinel-1 date the reconstruction is compared with the S1 new dark water (mask minus water on 1–2 June) on the S1
valid footprint, the owned zone area and outside the cut rectangles: hits, misses, terrain-only cells, POD, FAR and CSI (contingency-table measures, Schaefer 1990; raw agreement, primary, T13) — reported per date and per domain because binary pattern measures depend on the size of the flood and of the domain over which they are computed (Stephens et al. 2014); the *conditional POD outside the normally-wet class* — POD on the observable dry-background
domain, with the class fixed before any comparison was read — is a diagnostic conditional agreement, not a corrected POD. The
disagreement is decomposed into A (both), B (terrain only) and C (S1 only), by WorldCover and RF20 class and by ground elevation
relative to the reconstructed surface (< 0, 0–2, 2–5, ≥ 5 m; T14).

**Table T14.** Disagreement ontology terrain x Sentinel-1 by zone and date: category areas split by ground elevation relative to the water surface, normally-wet flag, WorldCover and RF20 classes (km2). [contextual] *(24 of 24 rows and 10 of 21 columns shown; full table: publication/tables/T14.csv)*

| zone | date | category | km2 | km2_ground_below_surface | km2_ground_0_2m_above | km2_ground_2_5m_above | km2_ground_ge5m_above | km2_normally_wet | km2_wc_trees |
|---|---|---|---|---|---|---|---|---|---|
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-09 | A | 24.1 | 24.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.8 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-09 | B | 57.86 | 57.86 | 0.0 | 0.0 | 0.0 | 0.0 | 20.07 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-09 | C | 110.79 | 76.98 | 1.51 | 3.59 | 28.71 | 75.96 | 2.91 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-09 | N | 1879.37 | 322.61 | 97.47 | 207.32 | 1251.63 | 67.75 | 258.42 |
| ZONE_2_KHERSON_DELTA | 2023-06-09 | A | 34.84 | 34.84 | 0.0 | 0.0 | 0.0 | 0.0 | 0.51 |
| ZONE_2_KHERSON_DELTA | 2023-06-09 | B | 53.97 | 53.97 | 0.0 | 0.0 | 0.0 | 0.0 | 15.89 |
| ZONE_2_KHERSON_DELTA | 2023-06-09 | C | 149.69 | 87.46 | 34.23 | 3.03 | 24.97 | 93.49 | 1.75 |
| ZONE_2_KHERSON_DELTA | 2023-06-09 | N | 882.51 | 167.25 | 52.01 | 36.12 | 620.38 | 39.8 | 116.88 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-13 | A | 11.9 | 11.9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.71 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-13 | B | 27.42 | 27.42 | 0.0 | 0.0 | 0.0 | 0.0 | 10.55 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-13 | C | 78.66 | 74.37 | 0.59 | 0.86 | 2.84 | 73.91 | 3.49 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-13 | N | 1954.14 | 271.16 | 42.58 | 142.51 | 1497.55 | 63.17 | 267.45 |
| ZONE_2_KHERSON_DELTA | 2023-06-13 | A | 10.55 | 10.55 | 0.0 | 0.0 | 0.0 | 0.0 | 0.08 |
| ZONE_2_KHERSON_DELTA | 2023-06-13 | B | 57.46 | 57.46 | 0.0 | 0.0 | 0.0 | 0.0 | 11.89 |
| ZONE_2_KHERSON_DELTA | 2023-06-13 | C | 63.79 | 57.37 | 3.44 | 0.25 | 2.73 | 58.39 | 0.82 |
| ZONE_2_KHERSON_DELTA | 2023-06-13 | N | 1158.11 | 280.69 | 105.08 | 59.99 | 704.67 | 91.98 | 137.24 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-14 | A | 5.41 | 5.41 | 0.0 | 0.0 | 0.0 | 0.0 | 0.34 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-14 | B | 23.96 | 23.96 | 0.0 | 0.0 | 0.0 | 0.0 | 9.1 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-14 | C | 53.78 | 48.26 | 1.08 | 0.69 | 3.75 | 47.42 | 2.09 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-14 | N | 1234.56 | 179.72 | 27.8 | 119.37 | 907.33 | 89.66 | 244.05 |
| ZONE_2_KHERSON_DELTA | 2023-06-14 | A | 5.83 | 5.83 | 0.0 | 0.0 | 0.0 | 0.0 | 0.03 |
| ZONE_2_KHERSON_DELTA | 2023-06-14 | B | 50.33 | 50.33 | 0.0 | 0.0 | 0.0 | 0.0 | 9.75 |
| ZONE_2_KHERSON_DELTA | 2023-06-14 | C | 34.28 | 17.75 | 3.38 | 2.39 | 10.75 | 18.28 | 0.37 |
| ZONE_2_KHERSON_DELTA | 2023-06-14 | N | 1199.46 | 320.82 | 111.36 | 60.15 | 699.46 | 132.09 | 139.89 |

Night ICESat-2 ATL08 ground segments (Paper 2 chain) sampled on the 9 June categories (inside the S1 valid footprint only) give,
per category, the residual terrain − ICESat-2 on the FABDEM cells, as delivered and after the class-bias correction, and the
share of segments whose ground lies below the reconstructed surface (T15): an altimetric consistency check of the terrain and the
surface along tracks, not a validation of the inundation map. Because the same night corpus calibrates the class bias, the
corrected residual is also computed with the bias re-estimated without the passes being checked (a pass is one acquisition day;
one pass left out, five folds of whole passes, and the two epochs either side of the breach; T15b, T15c).

**Table T15.** ICESat-2 altimetric consistency check per zone and agreement category on 9 June (categories inside the S1 valid footprint only, review F12): residual of the FABDEM-sourced terrain minus night ICESat-2 ground, raw (res_*) and after the class-bias correction used by the reconstruction (res_corr_*; median, p10, p90), ICESat-2 ground minus water surface, share of segments below the surface; N segments on n_dates passes (acquisition days: the independent units, far fewer than the segments), n_bed_source segments on bed-sourced cells (excluded from the residual statistics). The same p57 night corpus also calibrates the class bias, so the corrected residual here is in-sample; its pass hold-out is T15b. A consistency check, not an independent validation. [independent_physical] *(16 of 16 rows and 10 of 17 columns shown; full table: publication/tables/T15.csv)*

| zone | category | N | n_dates | n_fabdem_source | n_bed_source | res_median | res_p10 | res_p90 | res_corr_median |
|---|---|---|---|---|---|---|---|---|---|
| ZONE_2_KHERSON_DELTA | observed_neither | 90424 | 19 | 78664 | 11760 | 0.06 | -0.41 | 1.31 | -0.02 |
| ZONE_2_KHERSON_DELTA | S1_only_ground_lt2m_above | 12099 | 17 | 12099 | 0 | 0.42 | -0.24 | 0.8 | -0.1 |
| ZONE_2_KHERSON_DELTA | both | 4228 | 13 | 4228 | 0 | 0.84 | -0.02 | 1.41 | 0.35 |
| ZONE_2_KHERSON_DELTA | terrain_only | 8094 | 14 | 8094 | 0 | 0.8 | -0.26 | 2.04 | 0.23 |
| ZONE_2_KHERSON_DELTA | S1_only_ground_ge2m_above | 3205 | 17 | 3205 | 0 | 0.03 | -0.31 | 0.64 | -0.02 |
| ZONE_2_KHERSON_DELTA | S1_only_ge2m box=False wc=grass | 1646 | 17 | 1646 | 0 | 0.03 | -0.32 | 0.97 | -0.08 |
| ZONE_2_KHERSON_DELTA | S1_only_ge2m box=False wc=cropland | 1067 | 12 | 1067 | 0 | -0.02 | -0.32 | 0.39 | 0.04 |
| ZONE_2_KHERSON_DELTA | S1_only_ge2m box=True wc=grass | 386 | 11 | 386 | 0 | 0.14 | -0.17 | 0.7 | 0.01 |
| ZONE_2_KHERSON_DELTA | S1_only_ge2m box=True wc=cropland | 90 | 3 | 90 | 0 | 0.32 | -0.28 | 0.93 | 0.38 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | observed_neither | 103198 | 66 | 101661 | 1537 | 0.23 | -0.25 | 1.55 | -0.04 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | S1_only_ground_lt2m_above | 6825 | 31 | 6825 | 0 | 0.58 | -0.05 | 0.99 | -0.01 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | both | 2217 | 29 | 2217 | 0 | 0.49 | -0.14 | 1.44 | 0.1 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | terrain_only | 3751 | 30 | 3751 | 0 | 0.55 | -0.26 | 2.15 | 0.03 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | S1_only_ground_ge2m_above | 1666 | 59 | 1666 | 0 | 0.02 | -0.25 | 1.73 | -0.15 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | S1_only_ge2m box=False wc=grass | 472 | 46 | 472 | 0 | 0.81 | -0.04 | 7.24 | 0.43 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | S1_only_ge2m box=False wc=cropland | 1171 | 49 | 1171 | 0 | -0.06 | -0.28 | 0.25 | -0.21 |

**Table T15b.** Pass hold-out of the class-bias correction (review F12), FABDEM-sourced check segments only: the class bias is re-estimated with the reconstruction's rule from the ICESat-2 calibration population WITHOUT the passes being checked (a pass = one acquisition day; leave one pass out, five folds of whole passes, and the two epochs either side of the breach) and applied to the held-out passes. Per zone, category and scheme: N segments and n_passes, raw, in-sample and hold-out corrected residual (median; hold-out p10-p90 = spread of the sampled residuals, not a confidence interval), the largest bias shift met by a checked segment, the share of segments whose terrain lies below the 06-09 surface in-sample and with the hold-out bias, the share of ICESat-2 ground below the surface (does not involve the bias), and the number of S1-only segments that change side of the 2 m split. [independent_physical] *(25 of 30 rows and 10 of 18 columns shown; full table: publication/tables/T15b.csv)*

| zone | category | scheme | N_segments | n_passes | res_raw_median | res_insample_median | res_holdout_median | median_change | median_change_abs |
|---|---|---|---|---|---|---|---|---|---|
| ZONE_2_KHERSON_DELTA | observed_neither | leave_one_pass_out | 78664 | 19 | 0.06 | -0.02 | -0.02 | -0.0 | 0.0 |
| ZONE_2_KHERSON_DELTA | observed_neither | five_fold_passes | 78664 | 19 | 0.06 | -0.02 | -0.02 | -0.001 | 0.001 |
| ZONE_2_KHERSON_DELTA | observed_neither | epoch | 78664 | 19 | 0.06 | -0.02 | -0.03 | -0.004 | 0.004 |
| ZONE_2_KHERSON_DELTA | S1_only_ground_lt2m_above | leave_one_pass_out | 12099 | 17 | 0.42 | -0.1 | -0.11 | -0.013 | 0.013 |
| ZONE_2_KHERSON_DELTA | S1_only_ground_lt2m_above | five_fold_passes | 12099 | 17 | 0.42 | -0.1 | -0.13 | -0.04 | 0.04 |
| ZONE_2_KHERSON_DELTA | S1_only_ground_lt2m_above | epoch | 12099 | 17 | 0.42 | -0.1 | 0.14 | 0.237 | 0.237 |
| ZONE_2_KHERSON_DELTA | both | leave_one_pass_out | 4228 | 13 | 0.84 | 0.35 | 0.37 | 0.018 | 0.018 |
| ZONE_2_KHERSON_DELTA | both | five_fold_passes | 4228 | 13 | 0.84 | 0.35 | 0.37 | 0.019 | 0.019 |
| ZONE_2_KHERSON_DELTA | both | epoch | 4228 | 13 | 0.84 | 0.35 | 0.59 | 0.238 | 0.238 |
| ZONE_2_KHERSON_DELTA | terrain_only | leave_one_pass_out | 8094 | 14 | 0.8 | 0.23 | 0.24 | 0.007 | 0.007 |
| ZONE_2_KHERSON_DELTA | terrain_only | five_fold_passes | 8094 | 14 | 0.8 | 0.23 | 0.23 | 0.003 | 0.003 |
| ZONE_2_KHERSON_DELTA | terrain_only | epoch | 8094 | 14 | 0.8 | 0.23 | 0.31 | 0.077 | 0.077 |
| ZONE_2_KHERSON_DELTA | S1_only_ground_ge2m_above | leave_one_pass_out | 3205 | 17 | 0.03 | -0.02 | -0.02 | -0.001 | 0.001 |
| ZONE_2_KHERSON_DELTA | S1_only_ground_ge2m_above | five_fold_passes | 3205 | 17 | 0.03 | -0.02 | -0.02 | -0.006 | 0.006 |
| ZONE_2_KHERSON_DELTA | S1_only_ground_ge2m_above | epoch | 3205 | 17 | 0.03 | -0.02 | -0.05 | -0.035 | 0.035 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | observed_neither | leave_one_pass_out | 101661 | 66 | 0.23 | -0.04 | -0.04 | 0.002 | 0.002 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | observed_neither | five_fold_passes | 101661 | 66 | 0.23 | -0.04 | -0.04 | 0.001 | 0.001 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | observed_neither | epoch | 101661 | 66 | 0.23 | -0.04 | -0.04 | 0.0 | 0.0 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | S1_only_ground_lt2m_above | leave_one_pass_out | 6825 | 31 | 0.58 | -0.01 | -0.0 | 0.005 | 0.005 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | S1_only_ground_lt2m_above | five_fold_passes | 6825 | 31 | 0.58 | -0.01 | -0.01 | -0.005 | 0.005 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | S1_only_ground_lt2m_above | epoch | 6825 | 31 | 0.58 | -0.01 | -0.01 | -0.004 | 0.004 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | both | leave_one_pass_out | 2217 | 29 | 0.49 | 0.1 | 0.1 | 0.001 | 0.001 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | both | five_fold_passes | 2217 | 29 | 0.49 | 0.1 | 0.1 | 0.002 | 0.002 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | both | epoch | 2217 | 29 | 0.49 | 0.1 | 0.1 | -0.002 | 0.002 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | terrain_only | leave_one_pass_out | 3751 | 30 | 0.55 | 0.03 | 0.03 | -0.001 | 0.001 |

**Table T15c.** Stability of the class residual bias b_c across the pass hold-out folds of T15b (FABDEM - ICESat-2 ground, p95 rule): per scheme, zone and WorldCover class the in-sample b_c, the largest |shift| over the folds, the fewest calibration passes left in a fold, whether the own-zone or the pooled row was used, and b_c estimated from the pre-breach and from the post-breach passes alone. b_c enters the reconstruction as a fixed correction (not perturbed in the Monte-Carlo ensemble). [independent_physical] *(25 of 42 rows and 10 of 10 columns shown; full table: publication/tables/T15c.csv)*

| scheme | zone | wc_class | b_insample | n_folds | max_abs_delta | min_cal_passes | row_used | b_post_breach_passes | b_pre_breach_passes |
|---|---|---|---|---|---|---|---|---|---|
| epoch | ZONE_2_KHERSON_DELTA | bare | 0.2781 | 2 | 0.058 | 4 | pooled | 0.2301 | 0.336 |
| epoch | ZONE_2_KHERSON_DELTA | built | 0.1564 | 2 | 0.138 | 7 | own zone | 0.2334 | 0.0189 |
| epoch | ZONE_2_KHERSON_DELTA | cropland | -0.0586 | 2 | 0.006 | 7 | own zone | -0.0607 | -0.0529 |
| epoch | ZONE_2_KHERSON_DELTA | grass | 0.1067 | 2 | 0.082 | 7 | own zone | 0.0843 | 0.1886 |
| epoch | ZONE_2_KHERSON_DELTA | other | 0.1667 | 2 | 0.01 | 42 | pooled | 0.1589 | 0.177 |
| epoch | ZONE_2_KHERSON_DELTA | trees | 1.4858 | 2 | 0.012 | 6 | own zone | 1.491 | 1.474 |
| epoch | ZONE_2_KHERSON_DELTA | wetland | 0.5187 | 2 | 0.304 | 6 | own zone | 0.5871 | 0.2151 |
| epoch | ZONE_4_DAM_TO_KHERSON_FLOODWAY | bare | 0.3071 | 2 | 0.008 | 21 | own zone | 0.2986 | 0.3145 |
| epoch | ZONE_4_DAM_TO_KHERSON_FLOODWAY | built | 0.1722 | 2 | 0.075 | 34 | own zone | 0.2272 | 0.0972 |
| epoch | ZONE_4_DAM_TO_KHERSON_FLOODWAY | cropland | 0.1505 | 2 | 0.017 | 37 | own zone | 0.1668 | 0.1334 |
| epoch | ZONE_4_DAM_TO_KHERSON_FLOODWAY | grass | 0.3845 | 2 | 0.021 | 35 | own zone | 0.3639 | 0.4055 |
| epoch | ZONE_4_DAM_TO_KHERSON_FLOODWAY | other | 0.1667 | 2 | 0.01 | 42 | pooled | 0.1589 | 0.177 |
| epoch | ZONE_4_DAM_TO_KHERSON_FLOODWAY | trees | 1.6975 | 2 | 0.04 | 34 | own zone | 1.7294 | 1.6581 |
| epoch | ZONE_4_DAM_TO_KHERSON_FLOODWAY | wetland | 0.5894 | 2 | 0.023 | 21 | own zone | 0.6055 | 0.5668 |
| five_fold_passes | ZONE_2_KHERSON_DELTA | bare | 0.2781 | 5 | 0.064 | 9 | pooled | 0.2301 | 0.336 |
| five_fold_passes | ZONE_2_KHERSON_DELTA | built | 0.1564 | 5 | 0.07 | 15 | own zone | 0.2334 | 0.0189 |
| five_fold_passes | ZONE_2_KHERSON_DELTA | cropland | -0.0586 | 5 | 0.015 | 15 | own zone | -0.0607 | -0.0529 |
| five_fold_passes | ZONE_2_KHERSON_DELTA | grass | 0.1067 | 5 | 0.038 | 15 | own zone | 0.0843 | 0.1886 |
| five_fold_passes | ZONE_2_KHERSON_DELTA | other | 0.1667 | 5 | 0.02 | 78 | pooled | 0.1589 | 0.177 |
| five_fold_passes | ZONE_2_KHERSON_DELTA | trees | 1.4858 | 5 | 0.176 | 14 | own zone | 1.491 | 1.474 |
| five_fold_passes | ZONE_2_KHERSON_DELTA | wetland | 0.5187 | 5 | 0.079 | 13 | own zone | 0.5871 | 0.2151 |
| five_fold_passes | ZONE_4_DAM_TO_KHERSON_FLOODWAY | bare | 0.3071 | 5 | 0.046 | 34 | own zone | 0.2986 | 0.3145 |
| five_fold_passes | ZONE_4_DAM_TO_KHERSON_FLOODWAY | built | 0.1722 | 5 | 0.03 | 66 | own zone | 0.2272 | 0.0972 |
| five_fold_passes | ZONE_4_DAM_TO_KHERSON_FLOODWAY | cropland | 0.1505 | 5 | 0.029 | 71 | own zone | 0.1668 | 0.1334 |
| five_fold_passes | ZONE_4_DAM_TO_KHERSON_FLOODWAY | grass | 0.3845 | 5 | 0.021 | 68 | own zone | 0.3639 | 0.4055 |

### 3.7 Surface context: RF20

A random forest (Breiman 2001; for its use in land-cover mapping see Belgiu and Drăguţ 2016) on PRE-event Sentinel-2 composite
predictors, trained on ESA WorldCover 2021 with a purity filter, classifies the surface at 20 m into water, cropland,
grass/low vegetation, forest, wetland/reed, built-up, bare sand and uncertain (p73). The 5 km cross-validation blocks are defined
from the map coordinates of the 20 m cells, so a physical cell lies in one block in both frames; where the frames overlap only B2
contributes training cells, so a physical cell enters the sample once; the cross-validation is repeated with a 3.5 km buffer
around the test blocks, and the frame transfers B1↔B2 are trained and tested outside the overlap. Per-class precision, recall and
F1 are agreement with the training reference (T09, T10), not validation. The classifier supplies the classes of the disagreement
ontology, the evaluation strata of the U-Net arms and the input of arm U1.

**Table T09.** RF20 surface classification: per-class precision / recall / F1 with support, macro means (over the classes) and overall agreement, spatial-block 5-fold CV (rev 2 also with a 3.5 km buffer around the test blocks) and frame transfers (rev 2: outside the B1/B2 overlap). Reference = WorldCover 2021, the training reference. Rev 2 is the product in use (review F08); rev 1 rows are the superseded model. [contextual] *(25 of 70 rows and 10 of 12 columns shown; full table: publication/tables/T09.csv)*

| rev | evaluation | cls | precision | recall | F1 | n | train_kept_share_per_fold | OA_spatial_cv | kappa_spatial_cv_csv_only |
|---|---|---|---|---|---|---|---|---|---|
| 2 | spatial_block_cv_5fold | WATER | 0.9977 | 0.9984 | 0.9981 | 60000 |  | 0.9381 | 0.9274 |
| 2 | spatial_block_cv_5fold | CROPLAND | 0.9187 | 0.9247 | 0.9217 | 60000 |  | 0.9381 | 0.9274 |
| 2 | spatial_block_cv_5fold | GRASS_LOW_VEGETATION | 0.8679 | 0.873 | 0.8704 | 60000 |  | 0.9381 | 0.9274 |
| 2 | spatial_block_cv_5fold | FOREST | 0.9303 | 0.93 | 0.9301 | 60000 |  | 0.9381 | 0.9274 |
| 2 | spatial_block_cv_5fold | WETLAND_REED | 0.9663 | 0.928 | 0.9467 | 60000 |  | 0.9381 | 0.9274 |
| 2 | spatial_block_cv_5fold | BUILT_UP | 0.9202 | 0.9563 | 0.9379 | 60000 |  | 0.9381 | 0.9274 |
| 2 | spatial_block_cv_5fold | BARE_SAND | 0.9942 | 0.9712 | 0.9826 | 32420 |  | 0.9381 | 0.9274 |
| 2 | spatial_block_cv_5fold | MACRO | 0.9422 | 0.9402 | 0.9411 | 392420 |  | 0.9381 | 0.9274 |
| 2 | spatial_block_cv_5fold | OVERALL_ACCURACY |  |  | 0.9381 | 392420 |  | 0.9381 | 0.9274 |
| 2 | spatial_block_cv_5fold_buffered | WATER | 0.9952 | 0.9977 | 0.9964 | 60000 |  | 0.9262 | 0.9134 |
| 2 | spatial_block_cv_5fold_buffered | CROPLAND | 0.902 | 0.9129 | 0.9074 | 60000 |  | 0.9262 | 0.9134 |
| 2 | spatial_block_cv_5fold_buffered | GRASS_LOW_VEGETATION | 0.8533 | 0.8542 | 0.8537 | 60000 |  | 0.9262 | 0.9134 |
| 2 | spatial_block_cv_5fold_buffered | FOREST | 0.9161 | 0.9145 | 0.9153 | 60000 |  | 0.9262 | 0.9134 |
| 2 | spatial_block_cv_5fold_buffered | WETLAND_REED | 0.9585 | 0.9128 | 0.9351 | 60000 |  | 0.9262 | 0.9134 |
| 2 | spatial_block_cv_5fold_buffered | BUILT_UP | 0.9011 | 0.9502 | 0.925 | 60000 |  | 0.9262 | 0.9134 |
| 2 | spatial_block_cv_5fold_buffered | BARE_SAND | 0.9918 | 0.9536 | 0.9723 | 32420 |  | 0.9262 | 0.9134 |
| 2 | spatial_block_cv_5fold_buffered | MACRO | 0.9311 | 0.928 | 0.9293 | 392420 | [0.3387, 0.4934, 0.4823, 0.3227, 0.357] | 0.9262 | 0.9134 |
| 2 | spatial_block_cv_5fold_buffered | OVERALL_ACCURACY |  |  | 0.9262 | 392420 |  | 0.9262 | 0.9134 |
| 2 | transfer_B1_to_B2 | WATER | 0.9963 | 0.9976 | 0.997 | 22372 |  |  |  |
| 2 | transfer_B1_to_B2 | CROPLAND | 0.9384 | 0.7831 | 0.8538 | 15798 |  |  |  |
| 2 | transfer_B1_to_B2 | GRASS_LOW_VEGETATION | 0.7278 | 0.8939 | 0.8023 | 13822 |  |  |  |
| 2 | transfer_B1_to_B2 | FOREST | 0.9695 | 0.9011 | 0.934 | 14766 |  |  |  |
| 2 | transfer_B1_to_B2 | WETLAND_REED | 0.9357 | 0.8973 | 0.9161 | 9788 |  |  |  |
| 2 | transfer_B1_to_B2 | BUILT_UP | 0.6707 | 0.9059 | 0.7707 | 4845 |  |  |  |
| 2 | transfer_B1_to_B2 | BARE_SAND | 0.9975 | 0.4917 | 0.6587 | 1627 |  |  |  |

**Table T10.** RF20 confusion matrix (spatial-block CV, counts; rev 2). [contextual]

| reference \ predicted | WATER | CROPLAND | GRASS_LOW_VEGETATION | FOREST | WETLAND_REED | BUILT_UP | BARE_SAND |
|---|---|---|---|---|---|---|---|
| WATER | 59905 | 0 | 0 | 0 | 78 | 2 | 15 |
| CROPLAND | 3 | 55483 | 3851 | 171 | 175 | 316 | 1 |
| GRASS_LOW_VEGETATION | 16 | 3718 | 52382 | 1464 | 558 | 1855 | 7 |
| FOREST | 0 | 287 | 1412 | 55801 | 1083 | 1417 | 0 |
| WETLAND_REED | 87 | 472 | 1274 | 1964 | 55678 | 524 | 1 |
| BUILT_UP | 0 | 429 | 1401 | 584 | 50 | 57377 | 159 |
| BARE_SAND | 33 | 1 | 37 | 0 | 0 | 864 | 31485 |

### 3.8 Weak labels and the U-Net diagnostics

*The optical component.* The weak labels combine Sentinel-1 persistence with an optical second opinion, M2: a random forest on
Sentinel-2 composite features trained on the Sentinel-1-derived weak labels of p60 — so it is not independent of Sentinel-1. Its
operating threshold T50 is the median of the five outer-fold thresholds of a nested spatial cross-validation on 5 km blocks for a
target recall of 0.90, calibrated on inner out-of-fold scores (fit and calibration cells disjoint, whole blocks), and an envelope
of more permissive fold thresholds marks weaker optical support (T02c). The canonical M2 uses the 67 features of the PRE and EVENT
windows and none from the post-event TRACE window. The M2 score is not interpreted as a flood probability.

**Table T02c.** The optical model M2 behind the weak labels (review F09/F10): nested spatial cross-validation on 5 km blocks (PRE_ALL baseline; outer folds block and buffered). Per outer fold, the operating threshold for a target recall of 0.90 set on the forest's own fit cells (in-sample, superseded) and on inner out-of-fold scores (fit and calibration cells disjoint, whole blocks), and the recall each reaches on the outer TEST blocks; the fold median gives T50 of the label masks. Original model (84 features incl. 17 from the post-event TRACE window, labels v002 / v003_A) next to the corrected model (67 PRE + EVENT features, labels v004). M2 is trained on S1-derived weak labels (p60): agreement with them, not accuracy. [weak_label_agreement] *(18 of 18 rows and 10 of 15 columns shown; full table: publication/tables/T02c.csv)*

| model | model_id | regime | outer_fold | n_test | test_prevalence | inner_AP | AP | threshold_insample_superseded | recall_at_insample_superseded |
|---|---|---|---|---|---|---|---|---|---|
| M2 original (84 features, 17 from the post-event TRACE windo | original_trace | block | 1 | 4435424 | 0.0689 | 0.88882 | 0.96431 | 0.5131 | 0.9251 |
| M2 original (84 features, 17 from the post-event TRACE windo | original_trace | block | 2 | 4434572 | 0.0689 | 0.91329 | 0.9319 | 0.4667 | 0.85194 |
| M2 original (84 features, 17 from the post-event TRACE windo | original_trace | block | 3 | 4435500 | 0.0689 | 0.90767 | 0.92926 | 0.5358 | 0.75266 |
| M2 original (84 features, 17 from the post-event TRACE windo | original_trace | block | 4 | 4434452 | 0.0689 | 0.90151 | 0.94974 | 0.6429 | 0.82136 |
| M2 original (84 features, 17 from the post-event TRACE windo | original_trace | block | 5 | 4434460 | 0.0689 | 0.92364 | 0.9214 | 0.6636 | 0.87693 |
| M2 original (84 features, 17 from the post-event TRACE windo | original_trace | block | median | 22174408 |  | 0.90767 | 0.9319 | 0.5358 | 0.85194 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | block | 1 | 4435424 | 0.0689 | 0.87698 | 0.95743 | 0.328 | 0.90643 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | block | 2 | 4434572 | 0.0689 | 0.8984 | 0.92532 | 0.41 | 0.8601 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | block | 3 | 4435500 | 0.0689 | 0.88875 | 0.90992 | 0.6411 | 0.78357 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | block | 4 | 4434452 | 0.0689 | 0.89362 | 0.94133 | 0.601 | 0.81389 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | block | 5 | 4434460 | 0.0689 | 0.91078 | 0.90639 | 0.4463 | 0.88635 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | buffered | 1 | 4435424 | 0.0689 | 0.89128 | 0.89466 | 0.4584 | 0.44435 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | buffered | 2 | 4434572 | 0.0689 | 0.90975 | 0.8833 | 0.5818 | 0.82311 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | buffered | 3 | 4435500 | 0.0689 | 0.91471 | 0.82002 | 0.5697 | 0.57473 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | buffered | 4 | 4434452 | 0.0689 | 0.88799 | 0.92719 | 0.4297 | 0.78999 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | buffered | 5 | 4434460 | 0.0689 | 0.86832 | 0.70708 | 0.4495 | 0.53164 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | block | median | 22174408 |  | 0.89362 | 0.92532 | 0.4463 | 0.8601 |
| M2 corrected (67 PRE + EVENT features; labels v004) | corrected_notrace | buffered | median | 22174408 |  | 0.89128 | 0.8833 | 0.4584 | 0.57473 |

*The label versions.* Three label versions exist; only the last is used for the analyses of this paper, and the other two are
kept as provenance. **v002**, the historical initial version, marks FLOOD where Sentinel-1 saw water on at least two of the three
peak dates (9, 13, 14 June) on land that was dry before the breach and where M2 calls flood at T50, NON_FLOOD where every observed
post-breach date was dry and M2 does not, and IGNORE elsewhere. **v003_A**, an intermediate redesign prompted by failure cases,
keeps these positives and adds an explicit ontology: REFERENCE_WATER — recurrent water on at least three admitted May dates — as a
negative class, LAND, and UNKNOWN for insufficient, mixed or extrapolated evidence, with the immediate pre-event state W_pre
(1–2 June) entering the ontology. Both were built on an M2 that used 17 features of the post-event TRACE window and whose
threshold was calibrated on the forest's own training predictions. **v004** applies the v003_A rules to the corrected M2: v004 is
the final weak-label ontology used for manuscript analyses after correcting threshold calibration and removing TRACE dependence
from the M2 label pathway (T02, T02c, T02d; truth tables and the lineage down to the composite windows in
`docs/LABEL_CONTRACTS.md`). The v002 rule applied to the corrected M2 (v002_notrace), which has no REFERENCE_WATER class, is the
reference of the label comparison of §4.4.4. For training, EVENT_FLOOD is 1, LAND and REFERENCE_WATER are 0 and UNKNOWN is ignored.
Withholding the decision where the evidence is ambiguous follows operational practice: Bayesian Sentinel-1 flood mapping excludes
decisions whose two class probabilities are close to equal (Bauer-Marschallinger et al. 2022; Roth et al. 2025), and an operational boreal flood product classes "areas identified as non-flooded in semi-forested areas" as uncertain (Cohen et al. 2022).
Every version remains a weak label: v004 is the most consistent of the three, not a reference of higher quality, and agreement with it is not accuracy.

**Table T02.** Weak reference labels per frame, km2: v002 (FLOOD / NON_FLOOD / IGNORE) and v003_A (LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN), built on the original M2 (with the post-event TRACE window, in-sample threshold; frozen history), and v002_notrace and v004, the same rules on the corrected M2 (no TRACE, out-of-fold threshold; review F09/F10). EVENT_FLOOD is pixel-identical to the FLOOD of the v002 version it inherits. [weak_label_agreement] *(2 of 2 rows and 10 of 16 columns shown; full table: publication/tables/T02.csv)*

| frame | v002_FLOOD_km2 | v002_NON_FLOOD_km2 | v002_IGNORE_km2 | v003A_EVENT_FLOOD_km2 | v003A_LAND_km2 | v003A_REFERENCE_WATER_km2 | v003A_UNKNOWN_km2 | v002_notrace_FLOOD_km2 | v002_notrace_NON_FLOOD_km2 |
|---|---|---|---|---|---|---|---|---|---|
| B2 | 57.5 | 736.16 | 2092.26 | 57.49 | 663.09 | 283.85 | 1881.49 | 75.16 | 714.02 |
| B1 | 128.9 | 1753.1 | 4209.68 | 128.9 | 1544.3 | 258.47 | 4160.01 | 141.92 | 1720.31 |

**Table T02d.** What the corrected M2 changed in the weak labels: pixel transitions v003_A -> v004 and v002 -> v002_notrace per frame (km2 and share of the source class). The S1 inputs, the May reference state and W_pre are identical in both versions of a pair, so every change comes from the M2 masks (review F09/F10). [weak_label_agreement] *(25 of 33 rows and 6 of 6 columns shown; full table: publication/tables/T02d.csv)*

| pair | frame | from | to | km2 | share_of_from |
|---|---|---|---|---|---|
| v003_A -> v004 | B1 | LAND | LAND | 1513.685 | 0.9802 |
| v003_A -> v004 | B1 | LAND | UNKNOWN | 30.61 | 0.0198 |
| v003_A -> v004 | B1 | EVENT_FLOOD | EVENT_FLOOD | 128.822 | 0.9994 |
| v003_A -> v004 | B1 | EVENT_FLOOD | REFERENCE_WATER | 0.0 | 0.0 |
| v003_A -> v004 | B1 | EVENT_FLOOD | UNKNOWN | 0.082 | 0.0006 |
| v003_A -> v004 | B1 | REFERENCE_WATER | EVENT_FLOOD | 0.723 | 0.0028 |
| v003_A -> v004 | B1 | REFERENCE_WATER | REFERENCE_WATER | 257.75 | 0.9972 |
| v003_A -> v004 | B1 | UNKNOWN | LAND | 0.025 | 0.0 |
| v003_A -> v004 | B1 | UNKNOWN | EVENT_FLOOD | 12.373 | 0.003 |
| v003_A -> v004 | B1 | UNKNOWN | UNKNOWN | 4147.608 | 0.997 |
| v003_A -> v004 | B2 | LAND | LAND | 642.509 | 0.969 |
| v003_A -> v004 | B2 | LAND | UNKNOWN | 20.58 | 0.031 |
| v003_A -> v004 | B2 | EVENT_FLOOD | EVENT_FLOOD | 57.438 | 0.999 |
| v003_A -> v004 | B2 | EVENT_FLOOD | UNKNOWN | 0.056 | 0.001 |
| v003_A -> v004 | B2 | REFERENCE_WATER | EVENT_FLOOD | 1.991 | 0.007 |
| v003_A -> v004 | B2 | REFERENCE_WATER | REFERENCE_WATER | 281.86 | 0.993 |
| v003_A -> v004 | B2 | UNKNOWN | LAND | 0.021 | 0.0 |
| v003_A -> v004 | B2 | UNKNOWN | EVENT_FLOOD | 15.724 | 0.0084 |
| v003_A -> v004 | B2 | UNKNOWN | UNKNOWN | 1865.744 | 0.9916 |
| v002 -> v002_notrace | B1 | NON_FLOOD | NON_FLOOD | 1720.285 | 0.9813 |
| v002 -> v002_notrace | B1 | NON_FLOOD | IGNORE | 32.813 | 0.0187 |
| v002 -> v002_notrace | B1 | FLOOD | FLOOD | 128.822 | 0.9994 |
| v002 -> v002_notrace | B1 | FLOOD | IGNORE | 0.083 | 0.0006 |
| v002 -> v002_notrace | B1 | IGNORE | NON_FLOOD | 0.025 | 0.0 |
| v002 -> v002_notrace | B1 | IGNORE | FLOOD | 13.097 | 0.0031 |

*The arms.* U-Net arms (ResNet-34 encoder from scratch, 512-px patches, masked binary cross-entropy + Dice loss (Milletari et al.
2016), 60 epochs) differ only in their inputs: U0d (Sentinel-1 orbit-matched change channels + support), U1 (+ RF20 one-hot), U2
(+ HAND) and U2b (+ W_pre). Each arm is trained with three seeds (20260923, 20261001, 20261002), and each run's threshold is frozen
on the validation blocks before the test blocks are read. U2b is a diagnostic: W_pre is both an input and a label ingredient, so
its comparison is not independent.

### 3.9 Spatial blocking, training seeds and statistics

The split m6_split_v1 assigns 10 km blocks of the global lattice to train, validation and test with 640 m eroded buffers and
pure 512-px footprints (T03; {'train': 64, 'val': 15, 'test': 20} blocks). The block size exceeds the patch plus two
buffers (5.12 + 1.28 km), the minimum for which a validation patch exists (a 5 km split leaves none); 7.5, 15 and 20 km splits
retrain U2 as a sensitivity (T20). Endpoints are computed on unique test pixels against the v004 labels and compared between arms
by a paired bootstrap over identical physical blocks (2000 resamples); an endpoint without support in a resample is undefined,
not zero, and the number of defined resamples is reported. Three training seeds are the minimum evidence unit for any claim
about an arm difference: every comparison is reported per seed, with the number of seeds whose interval excludes zero and whether
their signs agree (T06s, T07s); a production raster may come from one frozen model. The test blocks were read for comparisons at
several stages of this study (including one diagnostic look at a test prediction during the v003_A redesign), so the arm
comparisons are exploratory rather than confirmatory. Per-day statistics of the water surface use the day as the independent
unit, ICESat-2 statistics the pass.

**Table T03.** Frozen spatial-block split m6_split_v1: geometry, counts and rationale. [weak_label_agreement]

| item | value |
|---|---|
| block size (m) | 10000.0 |
| buffer (px / m) | 64 / 640 |
| patch (px / km) | 512 / 5.12 |
| blocks train/val/test | {'train': 64, 'val': 15, 'test': 20} |
| patches train/val/test | {'train': 556, 'test': 164, 'val': 28} |
| accepted draw / seed | 1 / 20260923 |
| selection reads | m6_labels_v002 + frozen p73 only; never U0/U1 scores, model  |
| anti-leakage | pure 512x512 footprints (centre >= 2.56 km from axis-aligned |
| minimum feasible block | patch + 2 x buffer = 5.12 + 1.28 km; a 5 km split leaves no  |

**Table T20.** Block-size sensitivity (U2 on v003_A and on the corrected v004 labels): the same recipe on splits with 7.5, 10 (frozen), 15 and 20 km blocks; each split has its own TEST geography, so only the endpoint values and intervals are compared, never differences. [weak_label_agreement] *(9 of 9 rows and 10 of 31 columns shown; full table: publication/tables/T20.csv)*

| labels | split | block_km | status | n_blocks | n_patches | G_F1 | G_F1_lo | G_F1_hi | G_IoU |
|---|---|---|---|---|---|---|---|---|---|
| v003_A | m6_split_v1 | 10.0 | U2 v003_A trained and evaluated | {'train': 64, 'val': 15, 'test': 20} | {'train': 556, 'test': 164, 'val': 28} | 0.9306 | 0.72898 | 0.9422025 | 0.8702 |
| v003_A | m6_split_s5 | 5.0 | split infeasible (no validation patch survives the buffer) |  |  |  |  |  |  |
| v003_A | m6_split_s7p5 | 7.5 | U2 v003_A trained and evaluated | {'train': 95, 'val': 22, 'test': 29} | {'train': 393, 'test': 24, 'val': 15} | 0.9561 | 0.8783774999999999 | 0.9707025 | 0.9159 |
| v003_A | m6_split_s15 | 15.0 | U2 v003_A trained and evaluated | {'train': 28, 'val': 6, 'test': 8} | {'train': 989, 'val': 270, 'test': 154} | 0.9366 | 0.0 | 0.9455075 | 0.8807 |
| v003_A | m6_split_s20 | 20.0 | U2 v003_A trained and evaluated | {'train': 20, 'val': 4, 'test': 6} | {'train': 825, 'test': 379, 'val': 209} | 0.8764 | 0.7361 | 0.9384 | 0.7799 |
| v004 | m6_split_v1 | 10.0 | U2 v004 trained and evaluated | {'train': 64, 'val': 15, 'test': 20} | {'train': 556, 'test': 164, 'val': 28} | 0.9309 | 0.6738725000000001 | 0.951 | 0.8707 |
| v004 | m6_split_s7p5 | 7.5 | U2 v004 trained and evaluated | {'train': 95, 'val': 22, 'test': 29} | {'train': 393, 'test': 24, 'val': 15} | 0.94 | 0.7998700000000001 | 0.9643025 | 0.8868 |
| v004 | m6_split_s15 | 15.0 | U2 v004 trained and evaluated | {'train': 28, 'val': 6, 'test': 8} | {'train': 989, 'val': 270, 'test': 154} | 0.9316 | 0.0 | 0.942315 | 0.8719 |
| v004 | m6_split_s20 | 20.0 | U2 v004 trained and evaluated | {'train': 20, 'val': 4, 'test': 6} | {'train': 825, 'test': 379, 'val': 209} | 0.8886 | 0.8052 | 0.9382 | 0.7996 |

**Table T06s.** Paired arm comparisons (B minus A) on the v004 labels for each training seed: median and 95 % block-bootstrap interval per seed, the number of seeds whose interval excludes zero, and whether all seeds agree in sign (review F11). [weak_label_agreement] *(25 of 84 rows and 10 of 15 columns shown; full table: publication/tables/T06s.csv)*

| labels | comparison | endpoint | n_seeds | s20260923_median | s20260923_lo | s20260923_hi | s20261001_median | s20261001_lo | s20261001_hi |
|---|---|---|---|---|---|---|---|---|---|
| v004 | U2 - U0d | A_FP_area_dry_cropland_km2 | 3 | 0.1582 | -0.032505 | 0.489679999999999 | 0.29225 | 0.0384 | 0.7540374999999998 |
| v004 | U2 - U0d | A_FP_rate_dry_cropland | 3 | 0.0006245 | -0.000180025 | 0.0017860249999999 | 0.0011635 | 0.000203975 | 0.0028573249999999 |
| v004 | U2 - U0d | A_evaluated_dry_cropland_km2 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| v004 | U2 - U0d | B_recall_flooded_open_low_veg | 3 | 0.0045 | -0.0409324999999999 | 0.074005 | 0.0055999999999999 | -0.0831999999999999 | 0.0855049999999999 |
| v004 | U2 - U0d | B_IoU_open_low_veg | 3 | -0.0004 | -0.0602075 | 0.0628025 | -0.00895 | -0.122415 | 0.0709224999999998 |
| v004 | U2 - U0d | B_FN_area_km2 | 3 | -0.0312000000000001 | -0.3970400000000002 | 0.2350474999999996 | -0.0336999999999998 | -0.4885100000000001 | 0.2294 |
| v004 | U2 - U0d | B_reference_km2 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| v004 | U2 - U0d | C_recall_flooded_cropland_LOWN | 3 | -0.0102499999999999 | -0.0213999999999999 | 0.0780324999999998 | -0.0092999999999999 | -0.0282999999999999 | 0.0245199999999998 |
| v004 | U2 - U0d | C_FN_area_km2 | 3 | 0.0063 | -0.0105999999999999 | 0.0302999999999999 | 0.0052499999999999 | -0.0020025 | 0.0188024999999999 |
| v004 | U2 - U0d | C_reference_km2 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| v004 | U2 - U0d | W_precision | 3 | 0.021 | 0.0084999999999999 | 0.1317374999999997 | 0.0097 | 0.0048975 | 0.0206074999999999 |
| v004 | U2 - U0d | W_recall | 3 | -0.0108 | -0.0173999999999999 | -0.0008 | -0.0083 | -0.0276074999999999 | -0.0045999999999999 |
| v004 | U2 - U0d | W_IoU | 3 | 0.0088 | 0.0038 | 0.0937025 | 0.0013999999999999 | -0.0076999999999999 | 0.0031000000000001 |
| v004 | U2 - U0d | BU_FP_area_km2 | 3 | -0.0475 | -0.1718125 | 0.0602349999999998 | -0.0382 | -0.1848025 | 0.0547074999999999 |
| v004 | U2 - U0d | BU_precision | 3 | 0.0312999999999999 | -0.0048 | 0.325875 | 0.0016999999999999 | -0.0537175 | 0.1146574999999999 |
| v004 | U2 - U0d | BS_FP_area_km2 | 3 | -0.0069 | -0.0201 | 0.0 | -0.0079 | -0.0237 | 0.0 |
| v004 | U2 - U0d | G_F1 | 3 | 0.0047 | -0.0047999999999999 | 0.0148099999999998 | -0.0009 | -0.0384049999999999 | 0.0041024999999999 |
| v004 | U2 - U0d | G_IoU | 3 | 0.0081999999999999 | -0.006505 | 0.0230999999999999 | -0.0015499999999999 | -0.049405 | 0.0073 |
| v004 | U2 - U0d | G_precision | 3 | 0.0201999999999999 | -0.0075049999999999 | 0.0491099999999998 | 0.0061999999999999 | -0.0806225 | 0.0152999999999999 |
| v004 | U2 - U0d | G_recall | 3 | -0.0099 | -0.0211999999999999 | 0.0026 | -0.0077 | -0.0171999999999999 | 0.0012024999999999 |
| v004 | U2 - U0d | A1_isolated_field_FP_km2 | 3 | 0.1713 | -0.0294 | 0.5273124999999993 | 0.17895 | 0.0131999999999999 | 0.4739 |
| v004 | U2 - U0d | A2_pred_flood_on_nonflood_cropland_km2 | 3 | 0.1582 | -0.032505 | 0.489679999999999 | 0.29225 | 0.0384 | 0.7540374999999998 |
| v004 | U2 - U0d | A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2 | 3 | 0.98205 | -0.5844624999999996 | 3.027985 | 7.62375 | 2.48486 | 14.85624 |
| v004 | U2 - U0d | A2_unlabelled_cropland_evaluated_km2 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| v004 | U2 - U0d | A2_frac_unlabelled_cropland_above_thr | 3 | 0.0020799999999999 | -0.00153075 | 0.00562 | 0.01613 | 0.0069879999999999 | 0.0263432499999999 |

**Table T07s.** Attribution comparisons of the arms on the canonical v004 labels per training seed (D-SEEDS: three seeds are the minimum evidence unit): the label effect at fixed inputs (U2 trained on v002_notrace -- the v002 rule on the corrected M2, without a REFERENCE_WATER class -- vs U2 on v004), the HAND input (U2 - U0d) and the W_pre input (U2b - U2; not independent, W_pre is a label ingredient). Per seed the median and 95 % block-bootstrap interval (2000 paired resamples on identical TEST blocks; both runs of a pair share the seed), the number of seeds whose interval excludes zero, sign agreement and the range of the seed medians. Endpoints against the v004 labels; agreement with weak labels, not accuracy. [weak_label_agreement] *(25 of 39 rows and 10 of 17 columns shown; full table: publication/tables/T07s.csv)*

| comparison | endpoint | n_seeds | s20260923_median | s20260923_lo | s20260923_hi | s20261001_median | s20261001_lo | s20261001_hi | s20261002_median |
|---|---|---|---|---|---|---|---|---|---|
| v004 - v002_notrace (U2) | R_pred_on_reference_water_km2 | 3 | -13.8151 | -35.34035 | -1.37068 | -25.60965 | -62.59644 | -3.65778 | -48.8048 |
| v004 - v002_notrace (U2) | R_pred_on_reference_water_wpre_water_km2 | 3 | -13.45285 | -34.61422 | -1.31832 | -25.37655 | -62.37634 | -3.56379 | -48.57435 |
| v004 - v002_notrace (U2) | R_pred_on_reference_water_wpre_dry_km2 | 3 | -0.3609 | -0.99521 | -0.0202 | -0.2222 | -0.49059 | -0.04319 | -0.2297 |
| v004 - v002_notrace (U2) | R_frac_reference_water_above_thr | 3 | -0.09881 | -0.1678 | -0.0165 | -0.18665 | -0.27711 | -0.04498 | -0.34783 |
| v004 - v002_notrace (U2) | R_reference_water_evaluated_km2 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| v004 - v002_notrace (U2) | E_recall_event_flood | 3 | -0.0336 | -0.0481 | -0.0089 | -0.0019 | -0.0216 | 0.0091 | -0.0055 |
| v004 - v002_notrace (U2) | E_FN_km2 | 3 | 1.71735 | 0.0976 | 4.2603 | 0.0918 | -0.1676 | 0.43371 | 0.2782 |
| v004 - v002_notrace (U2) | E_reference_km2 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| v004 - v002_notrace (U2) | L_FP_on_land_km2 | 3 | -3.4679 | -8.76609 | 0.21652 | -3.4566 | -7.15437 | -0.98744 | -2.3795 |
| v004 - v002_notrace (U2) | L_FP_rate_land | 3 | -0.00743 | -0.02103 | 0.00046 | -0.00752 | -0.01572 | -0.00207 | -0.00515 |
| v004 - v002_notrace (U2) | L_evaluated_km2 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| v004 - v002_notrace (U2) | U_pred_on_unknown_km2 | 3 | -15.3496 | -31.58246 | -3.56875 | -23.2692 | -32.77757 | -14.77345 | -24.8255 |
| v004 - v002_notrace (U2) | U_evaluated_km2 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| U2 - U0d (v004) | R_pred_on_reference_water_km2 | 3 | -0.5973 | -1.49527 | -0.01259 | -0.33405 | -0.91512 | 0.03091 | 0.19315 |
| U2 - U0d (v004) | R_pred_on_reference_water_wpre_water_km2 | 3 | -0.5234 | -1.23741 | -0.0083 | -0.3096 | -0.83321 | 0.0318 | 0.14405 |
| U2 - U0d (v004) | R_pred_on_reference_water_wpre_dry_km2 | 3 | -0.0954 | -0.2813 | -0.0003 | -0.02685 | -0.07741 | 0.0002 | 0.0434 |
| U2 - U0d (v004) | R_frac_reference_water_above_thr | 3 | -0.00409 | -0.01573 | -0.00013 | -0.0022 | -0.00894 | 0.00032 | 0.0013 |
| U2 - U0d (v004) | R_reference_water_evaluated_km2 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| U2 - U0d (v004) | E_recall_event_flood | 3 | -0.0099 | -0.0212 | 0.0026 | -0.0077 | -0.0172 | 0.0012 | 0.0088 |
| U2 - U0d (v004) | E_FN_km2 | 3 | 0.47155 | -0.09601 | 1.51007 | 0.3458 | -0.04021 | 1.04301 | -0.418 |
| U2 - U0d (v004) | E_reference_km2 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| U2 - U0d (v004) | L_FP_on_land_km2 | 3 | -0.41245 | -1.45192 | 0.32193 | -0.0378 | -0.61442 | 0.72393 | -0.94775 |
| U2 - U0d (v004) | L_FP_rate_land | 3 | -0.00089 | -0.00352 | 0.00071 | -8e-05 | -0.00147 | 0.00141 | -0.00202 |
| U2 - U0d (v004) | L_evaluated_km2 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| U2 - U0d (v004) | U_pred_on_unknown_km2 | 3 | -4.0125 | -10.23297 | 0.82619 | 6.15965 | -0.1662 | 14.46098 | -5.05355 |

## 4. Results

The results follow the hierarchy of evidence: the reconstruction (§4.1), its uncertainty and support (§4.2), independent
validation and the surface context that explains the disagreement (§4.3), and what weak-label models learn (§4.4). Areas and
volumes of the reconstruction are Monte-Carlo medians with their p05–p95 unless marked otherwise; maps show the geometry of the
nominal world.

### 4.1 The terrain-connectivity reconstruction [C01–C03, C14]

#### 4.1.1 The daily series below the dam

In the Dnipro corridor the reconstructed newly inundated area rises from zero on 5 June to
152 km² on 6 June and reaches
234 km² on 7 June (p05–p95
216–254 km²),
a day between the Sentinel-1 acquisitions that no full-coverage scene of the corridor covers [C01]; it is
239 km² on 8 June and
201 km² on 9 June (Fig04, T12). The Kherson stage peaks one day later
(5.77 m on 8 June, the daily value of the river yearbook; the
operational record gives 5.68 m at 15:00 on 8 June (Gleick et al. 2023) and Lehnigk et al. (2026) cite 5.6 m, a ~0.1 m spread
between sources; the peak stages by 8 June that Lehnigk et al. (2026) report from the same SWOT data are consistent with it) —
the areal maximum and the peak stage are different quantities, and the day of the areal maximum is a property of the
reconstructed series, not an observation. The reconstructed total water-surface area — all water on the day, including the
pre-breach channels, lakes and reed beds — rises from 439 km² in
the pre-breach regime (5 June; p05–p95
410–465 km²)
to 716 km² on 7 June
(686–744 km²),
and the reconstructed new-water volume reaches 603 hm³
(542–659 hm³) [C02].
The newly inundated area then recedes with the Kherson stage:
143 km² on 13 June,
45 km² on 18 June and
3 km² on 21 June, when the stage is back at
0.73 m (Fig04) [C03]. Inside the p42 floodplain domain the maximum
is 190 km² on 8 June. The Inhulets valley, reported separately and
never added to the corridor, peaks at 50 km² on 9 June; how well
that is constrained is the subject of §4.2.3 and §4.3.1.

![Fig04](img/Fig04.jpg)

**Fig04 Daily reconstructed series, dam → liman.** (a–c) Reconstructed total water-surface area per day (all water on the day, including pre-breach channels, lakes and reed beds) for the Dnipro corridor, the p42 floodplain domain and the Inhulets valley: Monte-Carlo median (black) and deterministic nominal run (dotted), the PRIMARY interval (shaded: p05–p95 of the coherent Monte-Carlo worlds of the total water surface itself, every day; n in T12b), the terrain-as-delivered sensitivity (orange; no residual bias removed) and the Sentinel-1 total dark water per acquisition (diamonds; open = partial coverage). (d–f) Reconstructed newly inundated area A_new — the aggregate over all ground under the former state definition; the headline A_new,dry and the wetland response ΔA_wet are in T12h — (Monte-Carlo median, black; shaded p05–p95) with its daily change as bars (blue filling, orange draining) and the range of the U-Net U2b persistent-event-flood area over its three training seeds (labels v004; mapped_UNet, a persistence quantity). (g–i) Kherson stage. Values between observation days are reconstructed, not observed; the reconstructed areal maximum (8 June in most worlds, 7 June in the others — days set by the interpolated node series and the gauge) lies between the Sentinel-1 acquisitions. Areas are terrain_reconstructed or observed_S1 (T12, T19).

Split by the pre-event ground class (§3.3, T12h), the new inundation of ground that was dry before the event is
146 km² in the corridor on 7 June (p05–p95
132–166 km²;
nominal world 160 km²),
148 km² on 8 June and
52 km² on 13 June; with the Inhulets valley,
summed within each world, it is 181 km²
on 7 June (168–202 km²).
The rest of A_new lies on the wetland (85 km² on 7 June) and on other water
(3 km²). Within every world A_new is exactly the sum of these three parts (T12hb). The two
reported quantities are not additive: A_new,dry + ΔA_wet exceeds A_new by 26 km²
(12–40 km²) on 7 June, because ΔA_wet also
counts the part of the normally-wet regime that was dry on 5 June in that world and under water on the day
(29 km²), which A_new excludes by definition. A_new is therefore the aggregate produced under
the former state definition — kept as the series of Fig04 and T12 and as the gate of the split — and never the sum of the two new
quantities: the headline flood expansion of this paper is A_new,dry, the wetland response is ΔA_wet.

**Table T12hb.** Accounting identities of the split (p95e_split_draws, per world; medians and p05-p95 over the Monte-Carlo worlds, nominal = draw 0): A_new = A_new,dry + A_new,wet + other holds exactly in every world (partition_max_abs_diff_km2); A_new,dry + dA_wet exceeds A_new by dAwet_minus_Anew_wet -- the part of the normally-wet regime that is dry on 5 June in that world and under water on the day, which dA_wet counts and A_new excludes by definition (inside the baseline). The legacy aggregate A_new is therefore not the sum of the two reported quantities and is never presented as such. [independent_physical] *(25 of 40 rows and 10 of 11 columns shown; full table: publication/tables/T12hb.csv)*

| date | region | partition_max_abs_diff_km2 | dry_plus_dAwet_minus_Anew_nominal | dry_plus_dAwet_minus_Anew_p05 | dry_plus_dAwet_minus_Anew_p50 | dry_plus_dAwet_minus_Anew_p95 | dAwet_minus_Anew_wet_p50 | dAwet_minus_Anew_wet_p05 | dAwet_minus_Anew_wet_p95 |
|---|---|---|---|---|---|---|---|---|---|
| 2023-06-05 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-05 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-05 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-05 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-06 | DNIPRO_CORRIDOR | 0.0 | 27.84 | 15.28 | 26.63 | 37.29 | 28.73 | 17.42 | 39.45 |
| 2023-06-06 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 29.18 | 16.19 | 27.97 | 39.26 | 31.93 | 20.18 | 43.19 |
| 2023-06-06 | INHULETS_VALLEY_rect | 0.0 | 1.34 | -1.04 | 1.38 | 3.93 | 3.19 | 0.81 | 5.68 |
| 2023-06-06 | P42_FLOODPLAIN_DOMAIN | 0.0 | 25.81 | 20.82 | 24.99 | 29.46 | 26.94 | 22.75 | 31.45 |
| 2023-06-07 | DNIPRO_CORRIDOR | 0.0 | 27.77 | 12.16 | 26.28 | 39.92 | 28.85 | 14.79 | 42.47 |
| 2023-06-07 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 28.79 | 12.63 | 26.98 | 41.04 | 31.76 | 17.51 | 45.81 |
| 2023-06-07 | INHULETS_VALLEY_rect | 0.0 | 1.02 | -1.43 | 0.99 | 3.5 | 3.19 | 0.81 | 5.68 |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | 0.0 | 25.57 | 20.3 | 24.67 | 29.39 | 27.06 | 22.67 | 31.75 |
| 2023-06-08 | DNIPRO_CORRIDOR | 0.0 | 28.13 | 0.7 | 25.52 | 44.55 | 27.96 | 3.32 | 47.2 |
| 2023-06-08 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 29.0 | 1.42 | 26.17 | 45.8 | 31.04 | 6.38 | 50.78 |
| 2023-06-08 | INHULETS_VALLEY_rect | 0.0 | 0.87 | -1.61 | 0.79 | 3.35 | 3.19 | 0.81 | 5.68 |
| 2023-06-08 | P42_FLOODPLAIN_DOMAIN | 0.0 | 25.7 | 19.11 | 24.5 | 29.55 | 26.76 | 21.28 | 31.92 |
| 2023-06-09 | DNIPRO_CORRIDOR | 0.0 | 28.79 | 1.21 | 25.65 | 45.0 | 27.99 | 3.49 | 47.33 |
| 2023-06-09 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 29.55 | 1.7 | 26.23 | 45.92 | 31.1 | 6.52 | 50.82 |
| 2023-06-09 | INHULETS_VALLEY_rect | 0.0 | 0.76 | -1.73 | 0.69 | 3.24 | 3.19 | 0.81 | 5.68 |
| 2023-06-09 | P42_FLOODPLAIN_DOMAIN | 0.0 | 26.15 | 19.35 | 24.74 | 29.82 | 26.81 | 21.39 | 31.93 |
| 2023-06-11 | DNIPRO_CORRIDOR | 0.0 | 29.3 | -12.02 | 22.26 | 45.4 | 24.5 | -9.9 | 47.81 |
| 2023-06-11 | DNIPRO_CORRIDOR+INHULETS_VALLEY_rect | 0.0 | 30.18 | -11.34 | 22.81 | 46.82 | 27.49 | -6.71 | 51.78 |
| 2023-06-11 | INHULETS_VALLEY_rect | 0.0 | 0.87 | -1.62 | 0.79 | 3.34 | 3.19 | 0.81 | 5.68 |
| 2023-06-11 | P42_FLOODPLAIN_DOMAIN | 0.0 | 26.24 | 16.0 | 23.29 | 29.27 | 25.3 | 17.97 | 31.29 |
| 2023-06-13 | DNIPRO_CORRIDOR | 0.0 | 29.82 | -11.81 | 22.51 | 45.72 | 24.55 | -9.85 | 48.05 |

On the seasonally wet vegetated wetland the event extent and the pre-event state are separate questions. Inside the event extent on
7 June lie 318 km² of the wetland (p05–p95
304–334 km²; nominal world
314 km²), a number the worlds agree on. The reconstructed pre-breach
state of the same wetland does not: 205 km²
(179–228 km²) under water on
5 June against 231 km² in the nominal world, because on flat reed beds near
the pre-breach water level the errors of terrain and water surface leave part of them dry on 5 June in almost every world, while the
much higher event surface covers them again on 7 June. The event increase ΔA_wet,
114 km²
(93–135 km²;
nominal world 83 km²), is therefore a difference from a
reconstructed baseline, not an observed change: which part of the inundated wetland was newly flooded and which was already
seasonally wet is the uncertain part of the result — not its extent.

The comparison with the UNOSAT flood of 6–9 June (T16b; a diagnostic comparison, not validation) agrees with this reading. Over
the corridor and the Inhulets valley UNOSAT places 92% of the analysed wetland inside its flood
and our daily states 85%; the two disagree on 33 km² — of which
31 km² are cells our state mask leaves UNKNOWN,
0 km² where an observation decides DRY and
2 km² where the model does — and on 7 km² the
other way (CSI 0.89). With so much of the wetland flooded in both, the same two areas placed at random within it would
already give CSI 0.79 (Heidke skill 0.52): the comparison shows that the reconstruction puts the
wetland inside the event extent without contradicting UNOSAT there, while the position of the flood boundary is tested on the dry
ground — CSI 0.55 against 0.02 by chance (Heidke skill 0.70). Against the ICEYE-based
layer of 7 June alone the decided wetland cells agree at CSI 0.96, with 76% of the wetland
decided and an admissible interval of 0.73–0.97 over every assignment of the UNKNOWN cells; on the dry
ground 0.64 on 95% decided, interval 0.38–0.72 (T16c).

**Table T16b.** Diagnostic comparison with the UNOSAT flood of 6-9 June (activation FL20230606UKR, the layers of product 3616: ICEYE 7 June, Sentinel-3 6-9 June at 300 m, Sentinel-2 8 June; preliminary, not field-validated) per pre-event ground class (p95y): our daily state mask WATER on any of 6-9 June against the UNOSAT flood, both outside the optical reference water. CSI_chance = the CSI of the same two areas placed independently within the ground class; heidke_skill = Heidke skill score (Cohen's kappa) of the 2x2 table. Where most of a class is flooded in both (the vegetated wetland), a high CSI is largely prevalence; the flood boundary is tested on the dry-before-event ground. UNOSAT shaped earlier fixes of the reconstruction: a diagnostic, not validation. [contextual] *(6 of 6 rows and 10 of 21 columns shown; full table: publication/tables/T16b.csv)*

| region | ground | analysed_km2 | UNOSAT_km2 | ours_WATER_km2 | ours_WATER_or_UNKNOWN_km2 | both_km2 | ours_only_km2 | UNOSAT_only_km2 | CSI |
|---|---|---|---|---|---|---|---|---|---|
| corridor + Inhulets | dry-before-event ground | 4632.7 | 171.49 | 164.7 | 272.85 | 119.75 | 44.95 | 51.74 | 0.553 |
| corridor + Inhulets | vegetated wetland | 403.9 | 370.79 | 344.12 | 378.02 | 337.51 | 6.61 | 33.28 | 0.894 |
| corridor + Inhulets | all non-optical-reference ground | 5041.65 | 545.25 | 511.88 | 654.18 | 459.79 | 52.1 | 85.46 | 0.77 |
| corridor | dry-before-event ground | 4026.45 | 151.35 | 146.63 | 251.89 | 103.18 | 43.45 | 48.17 | 0.53 |
| corridor | vegetated wetland | 385.21 | 352.31 | 325.48 | 359.38 | 319.02 | 6.45 | 33.28 | 0.889 |
| corridor | all non-optical-reference ground | 4415.68 | 505.81 | 474.38 | 613.74 | 424.06 | 50.32 | 81.75 | 0.763 |

**Table T16c.** 7 June against the UNOSAT ICEYE-based flood layer, per pre-event ground class (p95y): coverage of the cells our state mask decides (WATER or DRY), CSI on the decided cells, the two scenarios (UNKNOWN as DRY / as WATER) and the admissible interval over every assignment of the UNKNOWN cells (min = TP/(TP+FP+FN+U_water+U_dry), max = (TP+U_water)/(TP+U_water+FP+FN)); the share of ICEYE water that falls in UNKNOWN and how much of UNKNOWN lies at the ICEYE water edge. A diagnostic comparison, not validation. [contextual] *(5 of 5 rows and 10 of 14 columns shown; full table: publication/tables/T16c.csv)*

| ground | km2 | ICEYE_water_km2 | coverage | UNKNOWN_km2 | ICEYE_water_in_UNKNOWN_share | UNKNOWN_cells_ICEYE_water_share | UNKNOWN_share_at_ICEYE_edge | UNKNOWN_share_off_edge | CSI_decided |
|---|---|---|---|---|---|---|---|---|---|
| dry-before-event ground | 1381.95 | 116.51 | 0.946 | 75.25 | 0.252 | 0.39 | 0.334 | 0.04 | 0.642 |
| dry-before-event ground, open land | 1047.67 | 72.21 | 0.972 | 29.68 | 0.277 | 0.673 | 0.299 | 0.02 | 0.699 |
| vegetated wetland | 375.32 | 360.92 | 0.765 | 88.03 | 0.236 | 0.968 | 0.216 | 0.236 | 0.959 |
| non-optical-reference ground (as first reported) | 1760.29 | 479.91 | 0.907 | 163.69 | 0.239 | 0.702 | 0.304 | 0.081 | 0.869 |
| event ground of the first audit (no model-only normally-wet) | 1483.18 | 210.9 | 0.919 | 120.5 | 0.349 | 0.611 | 0.343 | 0.067 | 0.718 |

The seasonal observations show why the pre-event state is the uncertain part (T12j; every window in T12i), in the delta and in
the floodway between the dam and Kherson, the two zones that hold the wetland of the corridor. In the same season of a normal year
(13 June 2022) the normally-wet reed beds were dense, moist vegetation without optically visible water in both (median NDVI
0.78 and 0.76, MNDWI
-0.45 and -0.46), and the last optical scene before
the breach shows none either: 5 March 2023 in the delta (MNDWI -0.51), 5 June 2023, the day
before the breach, in the floodway (MNDWI -0.38 on the
25 km² seen through the clouds). The five floodway scenes of 6 May – 5 June
2023 place the normally-wet reed beds at a higher MNDWI than the other reeds
(-0.29 against -0.46 where only the
event reaches and -0.48 above its reach): water shows through the young canopy,
but not as open water. C-band separates the strata more clearly. In the spring of 2023 the normally-wet reed beds had a VV of
-8.1 dB in the delta and -4.1 dB in
the floodway, against -11.2 and -9.8 dB
on the reed beds above the reach of the flood and -11.6 and
-12.0 dB on dry ground, with a larger VV − VH difference
(7.2 and 10.6 dB
against 5.4 and 6.3 dB)
— a signature consistent with wet or inundated emergent vegetation (the double bounce, §3.3) that establishes neither open water
nor a depth. The reed beds that only the event reaches in the reconstruction are as bright as the normally-wet ones in the delta
(-8.2 dB) and in between in the floodway
(-8.2 dB): the radar does not support the terrain model's line between them in
the delta, so all reed beds are counted with the wetland. On 8 June the normally-wet reed beds of the delta read as open water
(MNDWI +0.51, NDVI -0.11;
47 km² observed through the clouds; the floodway was cloud-covered), and on
18 June, with the median MNDWI back below zero (-0.45 and
-0.24), their NDVI was 0.32 and
0.18 against 0.78 and
0.76 in the normal year, while the reed beds above the reach of the flood kept their
normal-year state (NDVI 0.66 and 0.78).
Seasonal Sentinel-1 and same-season Sentinel-2 observations thus indicate that much of the reed complex was already hydrologically
wet before the breach, but they do not provide a reliable binary map of open water beneath emergent vegetation on 5 June 2023: the
event turned wet emergent vegetation into a submerged canopy — a canopy-inundation transition, not the flooding of dry ground.

**Table T12i.** Reed-bed strata of the Kherson delta (Sentinel-2 frame B2) and of the floodway between the dam and Kherson (frame B1, west of 538 km) by window (p95z): 10 m Sentinel-2 indices and C-band backscatter of the zone caches, the median of the scene medians -- the same season of a normal year (13 June 2022), the spring 2023 scenes before the breach (Sentinel-2 in the floodway only, Sentinel-1 in both), the last optical scene before the breach (delta 5 March 2023, floodway 5 June 2023), the peak (8 June, partly cloudy: observed_km2) and the recession (18 June). Strata: NW_REEDS / NW_TREES = model-only normally wet reeds / floodplain forest; HIGH_REEDS = reeds > 0.5 m above the pre-breach surface and not reached on 7 June (P(water) < 0.05); OPEN_WATER = optical pre-breach water; EVENT_REEDS = reeds outside the normal regime that the ensemble floods on 7 June (P(water) >= 0.8); DRY_LAND = grass / cropland > 2 m above the 8 June surface. Observations, nothing fitted; a C-band double-bounce signature is consistent with wet or inundated emergent vegetation and establishes neither open water nor a depth; stratum-level evidence, not a map of water under the canopy on any day. [cross_sensor] *(25 of 407 rows and 10 of 10 columns shown; full table: publication/tables/T12i.csv)*

| zone | window | sensor | index | stratum | median | n_scenes | first | last | observed_km2 |
|---|---|---|---|---|---|---|---|---|---|
| delta | normal_year | S2 | AWEIsh | DRY_LAND | -0.546 | 1 | 2022-06-13 | 2022-06-13 | 1918.12 |
| delta | normal_year | S2 | AWEIsh | EVENT_REEDS | -0.611 | 1 | 2022-06-13 | 2022-06-13 | 35.14 |
| delta | normal_year | S2 | AWEIsh | HIGH_REEDS | -0.562 | 1 | 2022-06-13 | 2022-06-13 | 13.37 |
| delta | normal_year | S2 | AWEIsh | NW_REEDS | -0.579 | 1 | 2022-06-13 | 2022-06-13 | 90.84 |
| delta | normal_year | S2 | AWEIsh | NW_TREES | -0.604 | 1 | 2022-06-13 | 2022-06-13 | 10.35 |
| delta | normal_year | S2 | AWEIsh | OPEN_WATER | 0.055 | 1 | 2022-06-13 | 2022-06-13 | 179.27 |
| delta | normal_year | S2 | BSI | DRY_LAND | 0.128 | 1 | 2022-06-13 | 2022-06-13 | 1918.12 |
| delta | normal_year | S2 | BSI | EVENT_REEDS | -0.254 | 1 | 2022-06-13 | 2022-06-13 | 35.14 |
| delta | normal_year | S2 | BSI | HIGH_REEDS | -0.069 | 1 | 2022-06-13 | 2022-06-13 | 13.37 |
| delta | normal_year | S2 | BSI | NW_REEDS | -0.257 | 1 | 2022-06-13 | 2022-06-13 | 90.84 |
| delta | normal_year | S2 | BSI | NW_TREES | -0.295 | 1 | 2022-06-13 | 2022-06-13 | 10.35 |
| delta | normal_year | S2 | BSI | OPEN_WATER | -0.048 | 1 | 2022-06-13 | 2022-06-13 | 179.27 |
| delta | normal_year | S2 | MNDWI | DRY_LAND | -0.519 | 1 | 2022-06-13 | 2022-06-13 | 1918.12 |
| delta | normal_year | S2 | MNDWI | EVENT_REEDS | -0.479 | 1 | 2022-06-13 | 2022-06-13 | 35.14 |
| delta | normal_year | S2 | MNDWI | HIGH_REEDS | -0.523 | 1 | 2022-06-13 | 2022-06-13 | 13.37 |
| delta | normal_year | S2 | MNDWI | NW_REEDS | -0.45 | 1 | 2022-06-13 | 2022-06-13 | 90.84 |
| delta | normal_year | S2 | MNDWI | NW_TREES | -0.476 | 1 | 2022-06-13 | 2022-06-13 | 10.35 |
| delta | normal_year | S2 | MNDWI | OPEN_WATER | 0.278 | 1 | 2022-06-13 | 2022-06-13 | 179.27 |
| delta | normal_year | S2 | NDMI | DRY_LAND | -0.065 | 1 | 2022-06-13 | 2022-06-13 | 1918.12 |
| delta | normal_year | S2 | NDMI | EVENT_REEDS | 0.307 | 1 | 2022-06-13 | 2022-06-13 | 35.14 |
| delta | normal_year | S2 | NDMI | HIGH_REEDS | 0.118 | 1 | 2022-06-13 | 2022-06-13 | 13.37 |
| delta | normal_year | S2 | NDMI | NW_REEDS | 0.308 | 1 | 2022-06-13 | 2022-06-13 | 90.84 |
| delta | normal_year | S2 | NDMI | NW_TREES | 0.341 | 1 | 2022-06-13 | 2022-06-13 | 10.35 |
| delta | normal_year | S2 | NDMI | OPEN_WATER | 0.082 | 1 | 2022-06-13 | 2022-06-13 | 179.27 |
| delta | normal_year | S2 | NDTI | DRY_LAND | 0.104 | 1 | 2022-06-13 | 2022-06-13 | 1918.12 |

#### 4.1.2 Depth and duration

In the nominal world whose geometry the maps show, the maximum depth that the new inundation reached during the event has a
median of 2.22 m in the corridor, exceeds 2 m on
56% and 4 m on
14% of the cells ever newly inundated, and reaches
11.3 m in the deepest floodplain lows (Fig07a, T12e). The
deepest water lay on the right-bank floodplain below the dam and in the delta channels; on 8 June the median depth of the newly
inundated cells was 1.85 m (Fig07b). The backwater of the
Inhulets valley was deeper (median maximum depth
4.6 m). Inundation lasted more than a week only in
the floodplain lows and the delta (Fig07c). The per-cell maximum is an envelope of the event, not the state of any single day,
and carries no volume; the volumes of §4.1.1 are daily.

**Table T12e.** Depth of the terrain-reconstructed new inundation below the dam (water surface minus the seamless terrain-bed model; connected_ceiling, the nominal world -- its geometry, while areas and volumes as results come from the ensemble, T12): per accounting region, the maximum depth over 26 May - 10 July per cell and the depth on 8 June -- area, mean / median / p90 / p95 / maximum depth, the share of cells deeper than 1, 2 and 4 m, and on 8 June the volume. Maps in Fig07. [independent_physical] *(6 of 6 rows and 10 of 13 columns shown; full table: publication/tables/T12e.csv)*

| quantity | region | area_km2 | volume_km3 | depth_mean_m | depth_median_m | depth_p90_m | depth_p95_m | depth_max_m | share_gt_1m |
|---|---|---|---|---|---|---|---|---|---|
| depth_2023-06-08 | DNIPRO_CORRIDOR | 226.6 | 0.498 | 2.2 | 1.85 | 4.3 | 6.49 | 9.69 | 0.748 |
| depth_2023-06-08 | INHULETS_VALLEY_rect | 46.4 | 0.161 | 3.46 | 3.52 | 5.4 | 6.01 | 10.36 | 0.915 |
| depth_2023-06-08 | P42_FLOODPLAIN_DOMAIN | 181.1 | 0.435 | 2.4 | 2.01 | 4.79 | 6.86 | 9.69 | 0.796 |
| max_depth_event | DNIPRO_CORRIDOR | 263.8 |  | 2.52 | 2.22 | 4.72 | 6.58 | 11.27 | 0.801 |
| max_depth_event | INHULETS_VALLEY_rect | 50.6 |  | 4.3 | 4.58 | 6.17 | 6.72 | 11.15 | 0.931 |
| max_depth_event | P42_FLOODPLAIN_DOMAIN | 196.1 |  | 2.85 | 2.49 | 5.25 | 7.37 | 11.27 | 0.877 |

#### 4.1.3 The reservoir: emptying, depth and storage balance

Above the dam the pool emptied first in depth and then in area (Fig09–Fig11). Between 5 and 13 June the surface at the outlet
fell from 17.61 m to 5.71 m, the pool volume from
18.8 km³ to 4.2 km³ and the mean water depth from
8.8 m to 2.4 m, while the water area under the
sloped surface shrank only from 2132 km² to 1790 km² (the 13 June
values are upper estimates, §3.5): in the first week the broad pool became shallow rather than dry — the share of it deeper than
5 m fell from 83% to 5%
(Fig10, T21, T21b) — and Sentinel-2 confirms this wherever the clouds allowed it to see (§4.3.5). The area collapsed in the
following week, which the level records no longer cover: by 20 June, when Sentinel-2 observed the whole pool, a further
1166 km² (55% of the pre-breach water) had fallen dry and
646 km² (30%) remained water, along the old river channel and in
the broad north-eastern reach (Fig11d, e; T23b). By 5 July Sentinel-2 records dry bare sediment and shallow water over most of
the bed, and by 8 September recolonising vegetation (Fig11f, g; T24).

![Fig09](img/Fig09.jpg)

**Fig09 Reservoir drawdown and the downstream flood.** (a) Water levels in one frame: SWOT outlet nodes, Nikopol post (press values), Rozumivka gauge, ICESat-2 passes, G-REALM, and the Kherson stage downstream. (b) Pool volume and water area under the sloped daily surface integrated on the seamless DEM inside the pre-breach pool polygon; the Sentinel-1 reservoir areas of Yi et al. (2025) for comparison, read from the authors' code archive (Zenodo 14639520, `observations.mat`, obs.A; their day axis placed from 00:00 on 6 June). (c) Daily balance — left axis, flows in km³ per day: bars, the daily-mean effective release from the pool Q_in − dV/dt (a storage-balance estimate, not an instantaneous breach discharge), and the DniproHES inflow Q_in; right axis, volume in km³: the reconstructed new water stored downstream (corridor + Inhulets, sum of the Monte-Carlo medians; band: sum of the regional p05 and p95, a conservative envelope). Levels in the frame of Paper 1 (the SWOT outlet with the reservoir closure of Paper 1); G-REALM (Sentinel-6A) is shown as a check and is not an anchor of the pool surface; on 12–13 June the pool surface rests on the upper bound of the Nikopol post (upper estimates, T21). (d) Hypsometry of the seamless DEM against the design Table 19, which is defined from 10 m BS up and left blank below (T21, T22; FigS07 for the relative gap).

![Fig11](img/Fig11.jpg)

**Fig11 The emptying of the Kakhovka reservoir.** (a–d) Sentinel-2 water inside the pre-breach pool: (a) 5 June, the day before the breach (frozen p25 water3, 99 % observed); (b) 8 June and (c) 13 June, partly observed under clouds (p15 crosscheck; the IoU with the modelled pool on the cells Sentinel-2 observed in the titles); (d) 20 June, the whole pool observed. Not observed is not dry. (e) The day the bed fell dry: the model (p95f sloped surface) for 6–13 June where Sentinel-2 sees no water on 20 June; "by 20 June" where the model is still wet on 13 June and Sentinel-2, observing the whole pool, sees no water on 20 June; and "water on 20 June" wherever Sentinel-2 sees water — the observation overrides the model (T23b). (f, g) Sentinel-2 bed classes (frozen p25 k10e) on 5 July and 8 September: bare sediment, then recolonising vegetation (T24). (h) Pool water area over time as a share of the pool: the model (26 May – 13 June; open circles: upper estimates on 12–13 June), Sentinel-2 with the pool observed (filled) and the water share of the observed part on the partly observed dates (open), and the Sentinel-1 reservoir areas of Yi et al. (2025) from the authors' archive (Zenodo 14639520). In the first week the pool lost most of its volume while keeping most of its area (Fig10); the area collapsed in the second week. ## Supplementary figures

**Table T23b.** The day the Kakhovka bed fell dry (maintainer's check of the drawdown maps, 2026-09-30), on the Sentinel-2 grid inside the cells wet under the model on 5 June: the model day for 6-13 June where Sentinel-2 sees no water on 20 June; 'dry by 06-20' where the model is still wet on 13 June and Sentinel-2, observing the whole pool on 20 June, sees no water; 'water on 06-20' wherever Sentinel-2 sees water (the observation overrides the model). km2 and share of the 5 June pool water. Map: Fig11e. [cross_sensor]

| code | by | exposure | km2 | share_of_pool_0605 |
|---|---|---|---|---|
| 6 | model | 06-06 (model) | 35.7 | 0.0168 |
| 7 | model | 06-07 (model) | 36.1 | 0.017 |
| 8 | model | 06-08 (model) | 40.4 | 0.019 |
| 9 | model | 06-09 (model) | 53.6 | 0.0252 |
| 10 | model | 06-10 (model) | 58.3 | 0.0274 |
| 11 | model | 06-11 (model) | 51.6 | 0.0242 |
| 12 | model | 06-12 (model) | 19.5 | 0.0092 |
| 13 | model | 06-13 (model) | 21.5 | 0.0101 |
| 20 | Sentinel-2 | dry by 06-20 (Sentinel-2; wet under the model on 06-13) | 1165.6 | 0.5475 |
| 253 | not observed | still wet 06-13, not observed 06-20 | 0.2 | 0.0001 |
| 254 | Sentinel-2 | water on 06-20 (Sentinel-2) | 646.4 | 0.3036 |

**Table T24.** Sentinel-2 k10e surface classes inside the pool per date (every 2023 date observing >= 50 % of the pool) and stratum: POOL; EXPOSED_BY_0613 (model: wet on 06-05, dry by 06-13); WET_ON_0613 (model: still wet on 06-13). km2 and % of the observed cells per class; frozen SWOT-DNIPRO p25 products, not re-classified. Context for the drawdown and recolonisation of the bed (FigS08 i-k). [contextual] *(25 of 33 rows and 10 of 24 columns shown; full table: publication/tables/T24.csv)*

| date | regime | stratum | stratum_km2 | observed_km2 | observed_frac | OPEN_WATER_km2 | SHALLOW_OR_MIXED_WATER_km2 | WET_SEDIMENT_km2 | DRY_BARE_SEDIMENT_km2 |
|---|---|---|---|---|---|---|---|---|---|
| 2023-02-10 | PRE_BREACH | POOL | 2174.7 | 1908.6 | 0.878 | 1786.1 | 52.5 | 9.1 | 26.3 |
| 2023-02-10 | PRE_BREACH | EXPOSED_BY_0613 | 339.5 | 240.3 | 0.708 | 176.2 | 22.4 | 5.9 | 18.6 |
| 2023-02-10 | PRE_BREACH | WET_ON_0613 | 1789.4 | 1647.1 | 0.92 | 1608.6 | 27.6 | 1.5 | 5.2 |
| 2023-05-06 | PRE_BREACH | POOL | 2174.7 | 2162.0 | 0.994 | 2092.2 | 18.3 | 3.3 | 3.1 |
| 2023-05-06 | PRE_BREACH | EXPOSED_BY_0613 | 339.5 | 339.1 | 0.999 | 307.8 | 11.0 | 2.4 | 1.9 |
| 2023-05-06 | PRE_BREACH | WET_ON_0613 | 1789.4 | 1785.8 | 0.998 | 1779.8 | 2.5 | 0.4 | 0.3 |
| 2023-05-11 | PRE_BREACH | POOL | 2174.7 | 1171.4 | 0.539 | 1107.9 | 35.0 | 1.9 | 1.3 |
| 2023-05-11 | PRE_BREACH | EXPOSED_BY_0613 | 339.5 | 159.3 | 0.469 | 141.1 | 10.5 | 1.3 | 0.6 |
| 2023-05-11 | PRE_BREACH | WET_ON_0613 | 1789.4 | 988.1 | 0.552 | 964.1 | 21.7 | 0.4 | 0.1 |
| 2023-06-05 | PRE_BREACH | POOL | 2174.7 | 2161.9 | 0.994 | 2087.2 | 19.3 | 2.1 | 3.2 |
| 2023-06-05 | PRE_BREACH | EXPOSED_BY_0613 | 339.5 | 339.1 | 0.999 | 304.1 | 12.2 | 1.5 | 1.9 |
| 2023-06-05 | PRE_BREACH | WET_ON_0613 | 1789.4 | 1785.8 | 0.998 | 1779.5 | 2.7 | 0.2 | 0.3 |
| 2023-07-05 | BREACH_DRAWDOWN | POOL | 2174.7 | 2027.5 | 0.932 | 399.7 | 354.8 | 35.3 | 1000.6 |
| 2023-07-05 | BREACH_DRAWDOWN | EXPOSED_BY_0613 | 339.5 | 313.4 | 0.923 | 28.3 | 29.3 | 2.8 | 194.3 |
| 2023-07-05 | BREACH_DRAWDOWN | WET_ON_0613 | 1789.4 | 1684.4 | 0.941 | 371.0 | 324.6 | 32.2 | 801.0 |
| 2023-08-17 | BREACH_DRAWDOWN | POOL | 2174.7 | 1159.2 | 0.533 | 180.8 | 153.0 | 24.8 | 340.5 |
| 2023-08-17 | BREACH_DRAWDOWN | EXPOSED_BY_0613 | 339.5 | 163.0 | 0.48 | 13.3 | 10.0 | 2.2 | 59.5 |
| 2023-08-17 | BREACH_DRAWDOWN | WET_ON_0613 | 1789.4 | 989.1 | 0.553 | 167.6 | 142.8 | 22.3 | 279.4 |
| 2023-09-08 | POST_BREACH | POOL | 2174.7 | 2158.4 | 0.993 | 183.1 | 132.7 | 73.0 | 356.8 |
| 2023-09-08 | POST_BREACH | EXPOSED_BY_0613 | 339.5 | 338.0 | 0.995 | 13.8 | 15.6 | 7.5 | 71.6 |
| 2023-09-08 | POST_BREACH | WET_ON_0613 | 1789.4 | 1783.3 | 0.997 | 169.1 | 116.8 | 64.5 | 283.6 |
| 2023-09-23 | POST_BREACH | POOL | 2174.7 | 1187.4 | 0.546 | 56.7 | 13.6 | 27.1 | 311.0 |
| 2023-09-23 | POST_BREACH | EXPOSED_BY_0613 | 339.5 | 227.2 | 0.669 | 3.6 | 1.9 | 3.2 | 59.5 |
| 2023-09-23 | POST_BREACH | WET_ON_0613 | 1789.4 | 920.6 | 0.514 | 50.9 | 11.5 | 23.5 | 249.9 |
| 2023-09-28 | POST_BREACH | POOL | 2174.7 | 1181.2 | 0.543 | 75.6 | 48.3 | 28.9 | 223.3 |

Between 5 and 13 June the pool released 14.6 km³, with the largest daily volume
change of -3225 hm³ on 7 June. The corresponding daily-mean effective release, −dV/dt + Q_in,
is 40057 m³ s⁻¹ against a DniproHES inflow of
2730 m³ s⁻¹ (Fig09c, T21): a storage-balance estimate on a surface interpolated
between three or four level points, a daily mean and not an instantaneous breach discharge. Published estimates are different
physical quantities of the same order and are context, not validation: the *initial* breach flow of Yi et al. (2025) from a
gravimetry–altimetry–imagery discharge model is (5.7 ± 0.8) × 10⁴ m³ s⁻¹, the HEC-RAS scenario peaks of Kadam et al. (2024) are
3.6 × 10⁴ m³ s⁻¹ (300 m breach) and 4.8 × 10⁴ m³ s⁻¹ (600 m), and Shumilova et al. (2025) model a release of about 16.4 km³ over
two weeks. The released volume itself is period- and hypsometry-dependent in the literature: Yi et al. (2025) obtain
20.4 ± 1.4 km³ in 30 days from a pre-breach volume of 21.0 km³ (17.3 m), Vyshnevskyi et al. (2023) give 19.8 km³ at 16.76 m from
the operation rules, Monti et al. (2024) about 7.5 km³, and Lehnigk et al. (2026) cite ∼8 km³; our release over 5–13 June sits
inside that spread. The surface gradient across the pool reached 4.9 m on 10 June.
Downstream, the reconstructed new water stored above ground on 8 June was
595 hm³ in the corridor (p05–p95
504–662 hm³)
and 164 hm³ in the Inhulets valley — a few per cent of the
release, implying that most of the released volume was transmitted downstream rather than stored on the mapped floodplain
(Fig09c) [C14]. The seamless-DEM hypsometry lies below the design table at equal levels —
-9 % at 17.5 m, -14 % at 13 m,
-20 % at 11 m; the design table is undefined below 10 m (T22, FigS07) — so the released
volume inherits this hypsometry gap; its origin (datum, present morphology, the underwater part of the terrain model, shoreline
geometry, the original survey) is the subject of Paper 4. Read on the design level–volume curve (Table 19 of the monograph; T27,
FigS10) at the Rozumivka gauge, the classical terrain-free reference gives 21.3 km³ at
17.62 m on 5 May after the spring filling and 20.1 km³ on
5 June, and a daily-mean effective release of 37811 m³ s⁻¹ on 7 June — the same
order as the sloped-surface balance; after the breach the pool sloped by up to 4.9 m, so a
level-pool curve gives a range rather than a number (T27b, T27c).

![FigS07](img/FigS07.jpg)

**FigS07.** Reservoir hypsometry sensitivity: (a) V_DEM(H) against V_design(H) (Table 19, BS-77 + 0.185 m); (b) the relative gap ΔV/V_design and ΔA/A_design per level over the drawdown range (shaded), −9 % at the full-pool level (17.5 m), −14 % at 13 m and −20 % at 11 m; the design table is undefined below 10 m. The released volume of T21 inherits this gap; resolving it on the historical bathymetry is the subject of Paper 4 (T22).

![FigS10](img/FigS10.jpg)

**FigS10.** Design hypsometry of the Kakhovka reservoir and the observed 2023 levels read on it (p95i, T27; no DEM, nothing fitted). (a) Level–volume of the whole pool (monograph Table 19, Figs 13–15) with the volume of the five reaches stacked (dam → Babyne → Nikopol → Verkhnia Tarasivka → Blahovishchenka → Dnipro HPP) and the design levels (NUF 17.5, NPG 16.0, UNS 14.0, GMO 12.7 m historical Baltic; right axis EVRF2019 = +0.185 m). (b) Level–area, with the observed outlet level before the breach and on 6–13 June read on the design curve. (c) The design volume from 1 February to 20 June read at the observed levels: before the breach at the Rozumivka gauge (the pool was level) — the spring filling from ~13.5 km³ (14.0 m, early February) to 21.3 km³ (17.6 m, 5 May) during the April–May DniproHES release (shaded, right axis; 7.9 km³ of 22.7 km³ of inflow stored, the rest passed the Kakhovka HPP), a plateau at ~17.5 m through May and ~0.4 m lower in the last ten days before the breach; after the breach at the outlet (SWOT) and at the Rozumivka level — the surface sloped by up to 4 m, so the design curve, which assumes a level pool, gives a range, not one number; shaded where the outlet falls below 10.0 m and Table 19 is undefined. The storage balance on the design curve at the Rozumivka level gives a daily-mean effective release of ~12 000 / 38 000 / 20 000 / 19 000 m³/s on 6–9 June (T27b), the design-curve counterpart of the ~40 000 m³/s of T21 on 7 June. The released volume on the sloped surface of Paper 3 is T21/Fig09.

**Table T22.** Pool hypsometry from the seamless DEM (level surface) against the design Table 19 (BS-77 levels + 0.185 m), with the relative difference dV/V_design and dA/A_design per level: the seamless DEM gives less volume at the same level: -8.5 % at the full-pool level (17.5 m), -14 % at 13 m, -20 % at 11 m (open question for Paper 4: reservoir bowl on the historical bathymetry). [independent_physical] *(25 of 27 rows and 8 of 8 columns shown; full table: publication/tables/T22.csv)*

| level_evrf2019_m | A_dem_km2 | V_dem_km3 | level_bs77_m | A_table19_km2 | V_table19_km3 | dV_rel_pct | dA_rel_pct |
|---|---|---|---|---|---|---|---|
| 5.0 | 460.5 | 0.902 | 4.82 |  |  |  |  |
| 5.5 | 541.1 | 1.151 | 5.32 |  |  |  |  |
| 6.0 | 623.8 | 1.444 | 5.82 |  |  |  |  |
| 6.5 | 703.3 | 1.775 | 6.32 |  |  |  |  |
| 7.0 | 777.7 | 2.145 | 6.82 |  |  |  |  |
| 7.5 | 843.1 | 2.551 | 7.32 |  |  |  |  |
| 8.0 | 911.6 | 2.989 | 7.82 |  |  |  |  |
| 8.5 | 975.6 | 3.462 | 8.32 |  |  |  |  |
| 9.0 | 1045.0 | 3.966 | 8.82 |  |  |  |  |
| 9.5 | 1127.8 | 4.509 | 9.32 |  |  |  |  |
| 10.0 | 1247.7 | 5.101 | 9.82 |  |  |  |  |
| 10.5 | 1414.2 | 5.765 | 10.32 | 1497.4 | 7.4108 | -22.208128677065908 | -5.556297582476295 |
| 11.0 | 1543.7 | 6.507 | 10.82 | 1582.4 | 8.175600000000001 | -20.4095112285337 | -2.4456521739130466 |
| 11.5 | 1644.8 | 7.305 | 11.32 | 1664.2 | 8.9848 | -18.69601994479566 | -1.1657252734046444 |
| 12.0 | 1747.9 | 8.153 | 11.82 | 1744.84 | 9.8368 | -17.1173552374756 | 0.1753742463492454 |
| 12.5 | 1833.6 | 9.048 | 12.32 | 1820.628571428572 | 10.739714285714289 | -15.751948708398759 | 0.7124697906531098 |
| 13.0 | 1923.2 | 9.987 | 12.82 | 1892.0 | 11.664 | -14.3775720164609 | 1.6490486257928143 |
| 13.5 | 1997.4 | 10.969 | 13.32 | 1959.52 | 12.6272 | -13.131969082615313 | 1.93312647995428 |
| 14.0 | 2028.2 | 11.976 | 13.82 | 2020.48 | 13.62 | -12.070484581497785 | 0.3820874247703529 |
| 14.5 | 2049.9 | 12.996 | 14.32 | 2064.04 | 14.6392 | -11.224657085086617 | -0.6850642429410222 |
| 15.0 | 2067.0 | 14.025 | 14.82 | 2098.12 | 15.682 | -10.566254304297921 | -1.4832326082397524 |
| 15.5 | 2078.8 | 15.062 | 15.32 | 2124.72 | 16.738400000000002 | -10.015294173875656 | -2.1612259497721875 |
| 16.0 | 2089.4 | 16.104 | 15.82 | 2147.08 | 17.8048 | -9.55248023005033 | -2.686439257037457 |
| 16.5 | 2098.8 | 17.151 | 16.32 | 2165.88 | 18.8812 | -9.163612482257484 | -3.097124494431821 |
| 17.0 | 2109.1 | 18.203 | 16.82 | 2182.24 | 19.9676 | -8.837316452653306 | -3.3516020236087636 |

### 4.2 Uncertainty and support of the reconstruction [C01, C02, C07]

#### 4.2.1 The Monte-Carlo interval

On 7 June the 1000 coherent worlds give relative half-widths (half the
p05–p95 range over the median) of 8 % for the newly
inundated area, 4 % for the total water-surface area
and 10 % for the volume (T12). The quantiles are stable
against the ensemble size and a second seed (T11c, FigS12: p05–p95 of the new area
216–254 km²
with the primary seed, 216–256 km²
with the second). The areal maximum falls on 8 June in
53% of the worlds and on 7 June in
38% (T12c) [C01]; the two days share the maximum
because on 8 June a large part of the left bank hangs on a sill a few decimetres below the surface (T11e, FigS17). By the ablation (T11d), the
width of the new area comes mainly from the terrain term, that of the total water-surface area mainly from the water surface, and
the upper tail on 13 June from the interpolation between node observations.

![FigS17](img/FigS17.jpg)

**FigS17 Inundation probability of the coherent Monte-Carlo worlds.** P(new inundation) per cell on 7, 8, 9 and 13 June 2023 over the 1000 coherent worlds of the primary ensemble (p95e cellprob; the same worlds as T12) on the Sentinel-2 true-colour image of 13/20 June 2022: the classes P ≥ 0.95, 0.75–0.95 and 0.50–0.75 together are the median world — the map product of the ensemble — and 0.25–0.50 and 0.05–0.25 are the marginal cells whose connection hangs on a sill within the water-surface or terrain uncertainty. Titles give, for the Dnipro corridor, the area of the median world, of the nominal world (draw 0; the geometry of Fig07) and the expected area (the sum of P), and the area of every cell with P ≥ 0.05 (T12g). A marginal component appears here with its probability instead of being cut by hand. Contains modified Copernicus Sentinel data 2022.

#### 4.2.2 The nominal run is a diagnostic

The deterministic nominal run — draw 0, with unperturbed inputs — lies below the p05 of the new area and of the volume on the
peak days (215 km² and
485 hm³ on 7 June; T12b flags every such day), while its total
water-surface area lies inside its interval. The ablation attributes this position (T11d): with the terrain alone perturbed the
median new area on 7 June is 238 km², with the
water surface alone 211 km², and with both
perturbed but the pre-breach regime held at the nominal
217 km². Terrain perturbations shrink the
connected pre-breach water (a rebuilt regime of
497.7 km² with the terrain alone perturbed,
against 532.5 km² at the nominal) more
strongly than the peak-event total water, and the cells so released, deep under water at the flood stage, count as new and add
depth (Darnell et al. 2008; Hawker et al. 2018) [C07]. Connectivity is a nonlinear operator of the terrain, so a zero-mean terrain
error need not leave the median area at the nominal one; the same threshold behaviour appears in the response to a uniform
water-surface offset (T11e, FigS13). No interval in this paper is centred on the nominal run.

**Table T12b.** The daily reconstructed series, every day 26 May - 10 July 2023 and region: Monte-Carlo median [p05-p95] of the coherent Monte-Carlo worlds (p95e rev 2, every day) for new inundation A, total water surface W_total (its own ensemble, also before the breach) and new-water volume V, with the deterministic nominal run (*_central_*) and a flag where it lies below its own MC p05. Before the breach A = V = 0 by construction. Daily reconstructed series, not daily observations. [independent_physical] *(25 of 138 rows and 10 of 19 columns shown; full table: publication/tables/T12b.csv)*

| date | region | A_p50_km2 | A_p05_km2 | A_p95_km2 | A_central_km2 | W_total_p50_km2 | W_total_p05_km2 | W_total_p95_km2 | W_total_central_km2 |
|---|---|---|---|---|---|---|---|---|---|
| 2023-05-26 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 460.7 | 434.6 | 485.6 | 491.8 |
| 2023-05-27 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 461.6 | 434.2 | 486.5 | 492.9 |
| 2023-05-28 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 461.1 | 433.6 | 485.4 | 491.2 |
| 2023-05-29 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 464.8 | 437.4 | 488.7 | 498.1 |
| 2023-05-30 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 464.1 | 437.7 | 488.4 | 496.4 |
| 2023-05-31 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 460.6 | 431.6 | 484.5 | 491.4 |
| 2023-06-01 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 465.4 | 438.9 | 488.9 | 495.9 |
| 2023-06-02 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 468.0 | 442.0 | 491.5 | 500.7000000000001 |
| 2023-06-03 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 466.2 | 438.3 | 490.9 | 499.0 |
| 2023-06-04 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 431.0 | 400.9 | 457.3 | 447.9 |
| 2023-06-05 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 439.4 | 410.4 | 465.1 | 461.3 |
| 2023-06-06 | DNIPRO_CORRIDOR | 151.6 | 140.3 | 165.1 | 132.2 | 628.5 | 612.3 | 645.7 | 629.9000000000001 |
| 2023-06-07 | DNIPRO_CORRIDOR | 233.7 | 216.0 | 253.7 | 214.8 | 716.2 | 685.9 | 743.6 | 718.6 |
| 2023-06-08 | DNIPRO_CORRIDOR | 239.3 | 186.0 | 263.4 | 226.6 | 712.2 | 644.5 | 761.7 | 730.8 |
| 2023-06-09 | DNIPRO_CORRIDOR | 200.9 | 185.9 | 230.4 | 171.3 | 676.1 | 642.6 | 721.7 | 670.2 |
| 2023-06-10 | DNIPRO_CORRIDOR | 196.2 | 177.0 | 244.3 | 159.8 | 663.8 | 601.2 | 731.6 | 659.0 |
| 2023-06-11 | DNIPRO_CORRIDOR | 181.4 | 162.3 | 230.7 | 146.60000000000002 | 649.6 | 586.8 | 715.6 | 646.3 |
| 2023-06-12 | DNIPRO_CORRIDOR | 163.5 | 144.7 | 211.7 | 129.5 | 630.7 | 568.7 | 698.5 | 628.9 |
| 2023-06-13 | DNIPRO_CORRIDOR | 143.2 | 125.4 | 192.4 | 112.1 | 610.6 | 547.1 | 679.2 | 611.4000000000001 |
| 2023-06-14 | DNIPRO_CORRIDOR | 120.6 | 100.7 | 167.2 | 90.0 | 586.8 | 521.9 | 656.3 | 589.1 |
| 2023-06-15 | DNIPRO_CORRIDOR | 100.2 | 79.3 | 143.5 | 59.400000000000006 | 564.7 | 500.7 | 635.2 | 554.9 |
| 2023-06-16 | DNIPRO_CORRIDOR | 79.7 | 63.6 | 121.3 | 50.5 | 544.3 | 482.6 | 609.3 | 545.6 |
| 2023-06-17 | DNIPRO_CORRIDOR | 62.8 | 49.3 | 103.2 | 42.3 | 528.5 | 465.4 | 590.5 | 537.0 |
| 2023-06-18 | DNIPRO_CORRIDOR | 45.4 | 35.5 | 85.2 | 33.9 | 511.0 | 448.4 | 573.9 | 528.3 |
| 2023-06-19 | DNIPRO_CORRIDOR | 28.0 | 22.4 | 44.0 | 25.0 | 497.9 | 462.9 | 534.7 | 519.0 |

#### 4.2.3 Observational support

The full reconstruction is the primary product; its support is uneven (§3.2, T11k). Of the corridor's new area on 7 June
(nominal world), 80 km² are directly supported by nodes within
3 km, 118 km² are extrapolated from nodes 3–10 km away, and
8% rests on water-surface support farther than 10 km (weakly
constrained); the supported core is 199 km² of
215 km², and a run with no surface from nodes beyond 10 km — which also
changes the connectivity — gives 199 km² (FigS02,
FigS14). The weak share falls to 4% on 9 June and
2% on 13 June, and inside the p42 floodplain domain it is
6% on 7 June: the distant support concerns mainly the first days
of the event and the ground outside the terrain-eligible floodplain. In the Inhulets valley, whose own SWOT nodes stop about 10 km
above the mouth, 93% of the new area on 7 June is weakly
constrained and 11.3 km² take their surface from a Dnipro
node (cross-river flag); distance, not only the river of the node, limits the constraint.

Distance is one axis of support; the seed of the connectivity is another. Every newly inundated component is classed by the
seed its potential component hangs on and by its day-to-day lineage (overlap graph, ancestry by backward traversal; p95o, T11n):
*river-connected* (it touches the river network on that day), *trapped* (not today, but it or an ancestor did on an earlier day)
or *isolated, never connected*. Under the superseded all-prewater seeding,
47 km² of the corridor's
261 km² on 7 June
(18%) and
61 km² of
192 km² on 6 June never touched the
river network along their lineage: they hung on isolated pre-breach ponds and canals. The largest of them
(42 km² on 6–8 June; FigS16) is classified predominantly as
cropland by WorldCover (82% of its cells) rather than
bare or sparse land, although it lies within the broader sandy terrace landscape of the left bank; its water surface was the
Kokan' level 19 km away, its potential component
held 1 seed bodies of
0.003 km² in total, the nearest river-connected
component lay 16460 m away across ground above
the surface, and the Sentinel-1 scenes saw no water in the part of it they observed (T11m). Neither 4-connectivity nor a
one-cell erosion of the potential mask is the mechanism (T11n). This is the case the connectivity requirement exists to exclude
(§3.3); the primary rule therefore seeds from the river network, under which the isolated class is empty by construction
(0 km² on 7 June), and the
all-prewater run is kept as the provenance variant. On the recession the superseded run also held
34 km² on 9 June and
14 km² on 15 June in components
that had been river-connected earlier and had lost the connection — retained water that only the memory variant keeps (T11p,
§4.2.4). Land cover is not geomorphology: a WorldCover class of cropland or trees on the terrace says nothing about the sand
beneath, which is why the maps of Fig07 and FigS16 are drawn on a Sentinel-2 true-colour image of the year before the breach.
Where a Sentinel-1 scene exists on the same day, the new area on open ground (grass, cropland, bare) that the scene observed and
showed without a water signal is also counted (T11n): 31 km²
of 55 km² observed
on 9 June — a disagreement on ground where SAR sees water (forest, reed and built-up are not informative and are not counted),
read with the timing caveat of §4.3.2 and never as a validation; a later scene does not contradict an earlier day. The floodplain lowland
south of Krynky, 10 km east of Kozachi Laheri (33.12° E, 46.67° N; forest and grass at 7–8 m under a surface taken from side-channel nodes 5 km away)
is the case in point: river-connected on 7–8 June and disconnected from 9 June, when the same-day scene shows its open ground
without water, it is kept in the primary while connected and dropped once disconnected — the same rule as everywhere else, with
the 9 June scene as a constraint on the recession, not as evidence about the peak two days earlier. A local audit of its sill
(T15d–T15f, FigS18) finds the connection real within the terrain data: the lowest path from the river network climbs from the
floodplain onto a terrace at 8.85 m and follows it for 6 km,
the ICESat-2 night ground at the terrace edge lies -0.02 m from the model terrain
(median of 576 segments in the 200 m strip along the path, NMAD
0.88 m), and the head of the water surface over the sill is
+0.68 m on 7 June and
+0.13 m on 8 June. Without the residual class bias
the sill is 10.41 m and there is no connection; the ICESat-2 residual
of FABDEM as delivered in the same strip, +0.70 m, is the bias the model removes.
Copernicus DEM GLO-30 is a surface model — +5.1 m above the ground under forest here (T15e) —
and offers no path below the surface; it does not arbitrate. The two sills are not the same cells: the correction opens a different
corridor (route overlap 0.15, T15g), along which FABDEM as delivered
reaches 10.55 m in the forest of the terrace interior, where no ICESat-2 segment
verifies the -1.7 m the class correction removes (T15h); the sill itself, at the terrace edge,
is verified. Along the same path the class-median correction is locally wrong in both directions — the floodplain forest and wetland
sit -0.6 and -0.4 m below the ICESat-2 ground, the
grass of the lowland interior +1.0 m above it (T15i): a single class median is the expected
residual of the class, not the residual of the cell, which is what the terrain term of the Monte-Carlo represents as random error.
What terrain error can do is decide 8 June, not 7 June: the per-cell probability of the ensemble carries exactly that (T12g, FigS17).
The remaining question for this lowland is no longer terrain but conveyance — whether the connecting channels could deliver, in the
hours the surface stood above the sill, the volume that fills it — which only a hydraulic model answers (§5).
Under the superseded seeding the trapped area of 9 June splits by that same-day verdict into
1 km² with water (plausible
retained water), 19 km²
of open ground without water (likely drained) and
14 km² without a usable
observation — which is why retention stays a sensitivity (D-MEMORY) and not a rule.

![FigS18](img/FigS18.jpg)

**FigS18 Saddle audit of the floodplain lowland south of Krynky, 10 km east of Kozachi Laheri (T15d–T15f).** The lowest path (minimax, 8-neighbours) from the pre-breach river network to the lowland on the model terrain: the model terrain (seamless terrain–bed model, residual FABDEM class bias removed), FABDEM as delivered, Copernicus DEM GLO-30 (a surface model: metres above the ground under forest), the channel bed of the model, the water surfaces of 7 and 8 June and the ICESat-2 ATL08 night ground segments within 100 m of the path. The path leaves the floodplain at ~9 km and runs along a terrace at 8.5–8.9 m (the sill) for 6 km before descending into the lowland; at the terrace edge the ICESat-2 ground lies 0.1 m below the model terrain (median, NMAD 0.4 m) — the sill is real within the data — so the head of the water surface over the sill, +0.7 m on 7 June and +0.1 m on 8 June, is what the ensemble sees: a connection that terrain error alone cannot remove on 7 June and can on 8 June (FigS17). Inside the lowland the model terrain is 1.1 m above the ICESat-2 ground.

**Table T11n.** Three semantic classes of the daily new inundation per region and run (p95o): A_full = A_river_connected + A_trapped + A_isolated_never. river_connected = the component touches the event-source network (largest connected component of the pre-breach water map) on that day; trapped = not today, but it or an ancestor was on an earlier day (retained water that a static model cannot hold); isolated_never = seeded by isolated pre-breach water only (ponds, canals; the artefact of the superseded seeding). Under the primary (D-SEED) isolated_never is 0 by construction and trapped water is absent (D-MEMORY sensitivity, T11p). Also the new area whose river link does not survive 4-connectivity or one 20 m erosion (morphological sensitivities), and -- on days with a same-day Sentinel-1 scene -- the new area on open ground (WorldCover grass, cropland, bare) that the scene observed and the part of it without a water signal: an open surface without water is a disagreement where SAR sees water, whereas forest, reed and built-up are not informative and are not counted; a later scene never contradicts an earlier day. The trapped area is split by the same-day verdict of the retained-water decision tree: water (plausible retained water), open surface without water (likely drained), no usable observation (uncertain). [independent_physical] *(25 of 276 rows and 10 of 22 columns shown; full table: publication/tables/T11n.csv)*

| date | region | A_full_km2 | A_s1_sameday_observed_open_km2 | A_s1_sameday_open_no_water_km2 | A_trapped_s1_water_km2 | A_trapped_s1_open_no_water_km2 | A_trapped_s1_uncertain_km2 | A_river_connected_km2 | A_trapped_km2 |
|---|---|---|---|---|---|---|---|---|---|
| 2023-05-26 | DNIPRO_CORRIDOR | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-26 | INHULETS_VALLEY_rect | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-26 | P42_FLOODPLAIN_DOMAIN | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-27 | DNIPRO_CORRIDOR | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-27 | INHULETS_VALLEY_rect | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-27 | P42_FLOODPLAIN_DOMAIN | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-28 | DNIPRO_CORRIDOR | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-28 | INHULETS_VALLEY_rect | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-28 | P42_FLOODPLAIN_DOMAIN | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-29 | DNIPRO_CORRIDOR | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-29 | INHULETS_VALLEY_rect | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-29 | P42_FLOODPLAIN_DOMAIN | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-30 | DNIPRO_CORRIDOR | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-30 | INHULETS_VALLEY_rect | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-30 | P42_FLOODPLAIN_DOMAIN | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-31 | DNIPRO_CORRIDOR | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-31 | INHULETS_VALLEY_rect | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-05-31 | P42_FLOODPLAIN_DOMAIN | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-01 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-01 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-01 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-02 | DNIPRO_CORRIDOR | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-02 | INHULETS_VALLEY_rect | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-02 | P42_FLOODPLAIN_DOMAIN | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2023-06-03 | DNIPRO_CORRIDOR | 0.0 |  |  | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

**Table T11m.** Seed-class QA of the SUPERSEDED all-prewater seeding (p95o on the provenance variant): every lineage of newly inundated components >= 1 km2 (day-to-day overlap graph, ancestry by backward traversal), its verdict (RIVER_CONNECTED / ISOLATED_NEVER = never linked to the event-source network along its lineage / CONNECTED_THEN_TRAPPED), the WorldCover mix of its own cells and of a 2 km context ring (land cover is not geomorphology: cropland or pine on the sandy terrace stays 'cropland' / 'trees'), terrain and water surface, the nearest SWOT node (river, km), the seed bodies inside its potential component, the 4-connectivity and erosion-disconnect sensitivities (a morphological test, not a width) and the Sentinel-1 class with its date and lag: S1_WATER (dark water on >= 20 % of the observed cells), S1_OPEN_SURFACE_NO_WATER (>= 30 % open ground -- grass, cropland, bare -- at least half of it observed and <= 5 % dark: no water signal where SAR sees water), S1_NO_WATER_SIGNAL_VEGETATED (forest, reed or built-up dominate: SAR not informative), S1_INCONCLUSIVE, S1_UNOBSERVED; prefix LATER_ when the scene is not of the same day, because a later scene never contradicts an earlier day. Trapped components carry the retained-water verdict of the same-day scene: RETAINED_PLAUSIBLE (water), LIKELY_DRAINED (open surface without water), RETAINED_UNCERTAIN. [independent_physical] *(25 of 34 rows and 10 of 41 columns shown; full table: publication/tables/T11m.csv)*

| lineage_id | first_day | last_day | n_days | max_km2 | max_day | classes | verdict | first_connected_day | merged_from |
|---|---|---|---|---|---|---|---|---|---|
| 2112 | 2023-06-06 | 2023-06-22 | 17 | 173.643 | 2023-06-08 | RIVER_CONNECTED;TRAPPED | CONNECTED_THEN_TRAPPED | 2023-06-06 | 809;1352;1365;1460;1469;1470;2129;2131;2134;2153;2492;2503;3 |
| 809 | 2023-06-06 | 2023-06-17 | 12 | 77.207 | 2023-06-07 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 1345;1643;1665;1946;2043;2095;2103;2117;2147 |
| 1706 | 2023-06-06 | 2023-06-08 | 3 | 41.711 | 2023-06-06 | ISOLATED_NEVER | ISOLATED_NEVER |  |  |
| 1 | 2023-06-06 | 2023-06-20 | 15 | 18.958 | 2023-06-08 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 2;4;11;12;14;19;20;21;22;23;24;25;26;27;28;30;33;34;38;39;41 |
| 1469 | 2023-06-06 | 2023-06-06 | 1 | 9.584 | 2023-06-06 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 |  |
| 1643 | 2023-06-06 | 2023-06-06 | 1 | 9.468 | 2023-06-06 | ISOLATED_NEVER | ISOLATED_NEVER |  |  |
| 1717 | 2023-06-06 | 2023-06-22 | 17 | 7.656 | 2023-06-09 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 2132;2189;2195;2212;2221 |
| 2 | 2023-06-06 | 2023-06-07 | 2 | 6.147 | 2023-06-07 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 3;6;7;17;18 |
| 2220 | 2023-06-06 | 2023-06-22 | 17 | 5.638 | 2023-06-10 | RIVER_CONNECTED;TRAPPED | CONNECTED_THEN_TRAPPED | 2023-06-06 | 2300;2416;3537 |
| 36 | 2023-06-06 | 2023-06-20 | 15 | 5.371 | 2023-06-09 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 44;47;48;49;50;64;65;67;68;70;83 |
| 16 | 2023-06-06 | 2023-06-20 | 15 | 4.308 | 2023-06-09 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 13;15;52;54;57 |
| 2019 | 2023-06-06 | 2023-06-10 | 5 | 2.816 | 2023-06-06 | ISOLATED_NEVER | ISOLATED_NEVER |  |  |
| 1825 | 2023-06-06 | 2023-06-10 | 5 | 2.419 | 2023-06-06 | ISOLATED_NEVER | ISOLATED_NEVER |  |  |
| 81 | 2023-06-06 | 2023-06-20 | 15 | 2.138 | 2023-06-09 | RIVER_CONNECTED;TRAPPED | CONNECTED_THEN_TRAPPED | 2023-06-06 | 80;91;98;99;100;101;103;104;105;3450;3455;3456;3457;3590 |
| 119 | 2023-06-06 | 2023-06-20 | 15 | 1.92 | 2023-06-09 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 126;162;163;164;165;3591 |
| 193 | 2023-06-06 | 2023-06-20 | 15 | 1.917 | 2023-06-09 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 191;192;212;217;218;219;220;233;243 |
| 1963 | 2023-06-06 | 2023-06-21 | 16 | 1.86 | 2023-06-11 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 |  |
| 3 | 2023-06-06 | 2023-06-06 | 1 | 1.633 | 2023-06-06 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 |  |
| 3424 | 2023-06-06 | 2023-06-10 | 5 | 1.593 | 2023-06-10 | ISOLATED_NEVER | ISOLATED_NEVER |  | 3352;3353;3355;3357;3358;3360;3361;3362;3363;3364;3371;3377; |
| 1722 | 2023-06-06 | 2023-06-21 | 16 | 1.561 | 2023-06-09 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 1713;3624 |
| 2574 | 2023-06-06 | 2023-06-08 | 3 | 1.517 | 2023-06-06 | ISOLATED_NEVER | ISOLATED_NEVER |  |  |
| 413 | 2023-06-06 | 2023-06-20 | 15 | 1.516 | 2023-06-07 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 681;691;728;746;749;755;849 |
| 158 | 2023-06-06 | 2023-06-20 | 15 | 1.39 | 2023-06-09 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 160;172;173;174;175 |
| 97 | 2023-06-06 | 2023-06-20 | 15 | 1.268 | 2023-06-09 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 | 94;95;96;123;127;130;132 |
| 913 | 2023-06-06 | 2023-06-20 | 15 | 1.244 | 2023-06-07 | RIVER_CONNECTED | RIVER_CONNECTED | 2023-06-06 |  |

**Table T15d.** Saddle audit of the floodplain lowland south of Krynky (10 km east of Kozachi Laheri) (p95p): the lowest path (minimax, 8-neighbours) from the pre-breach river network to the lowland on three terrain surfaces -- the model terrain (seamless terrain-bed model, residual FABDEM class bias removed), FABDEM as delivered, and Copernicus DEM GLO-30 on the land cells with the bed kept -- with the saddle height, the water surface at the saddle on 7 and 8 June and their difference (positive = connected in the nominal world), the saddle's land cover, terrain source and nearest SWOT node; the datum step that moves the EGM2008 tiles into the frame of the model. GLO-30 is a surface model: under forest it lies metres above the ground and no path exists below the water surface. [independent_physical] *(6 of 6 rows and 10 of 17 columns shown; full table: publication/tables/T15d.csv)*

| surface | day | z_saddle_m | H_saddle_m | delta_H_saddle_m | saddle_x | saddle_y | saddle_wc | saddle_source | saddle_node_river |
|---|---|---|---|---|---|---|---|---|---|
| model_terrain_bias_removed | 2023-06-07 | 8.85 | 9.529 | 0.679 | 504930.0 | 5174670.0 | grass | FABDEM | no_data |
| model_terrain_bias_removed | 2023-06-08 | 8.85 | 8.98 | 0.13 | 504930.0 | 5174670.0 | grass | FABDEM | no_data |
| fabdem_uncorrected | 2023-06-07 | 10.407 | 9.522 | -0.885 | 505010.0 | 5173410.0 | trees | FABDEM | no_data |
| fabdem_uncorrected | 2023-06-08 | 10.407 | 8.968 | -1.44 | 505010.0 | 5173410.0 | trees | FABDEM | no_data |
| glo30_on_land_bed_kept | 2023-06-07 |  |  |  |  |  |  |  |  |
| glo30_on_land_bed_kept | 2023-06-08 |  |  |  |  |  |  |  |  |

**Table T15f.** FABDEM minus GLO-30 (both EGM2008) in the audit window by class (p95p): the vegetation and building correction of FABDEM relative to the Copernicus surface model, and the residual class bias the model removes on top of it. [contextual]

| cls | n_cells | dz_fabdem_minus_glo30_median_m | dz_nmad_m | dz_p10_m | dz_p90_m | bias_removed_by_model_median_m |
|---|---|---|---|---|---|---|
| forest | 406496 | -3.246 | 3.643 | -9.057 | -0.132 | 1.698 |
| open_ground | 1189750 | 0.024 | 0.373 | -0.747 | 0.58 | 0.385 |
| wetland | 90608 | 0.03 | 0.228 | -0.362 | 0.399 | 0.589 |
| saddle_strip_200m | 19434 | -0.877 | 1.755 | -7.53 | 0.419 | 1.698 |
| shoreline_strip_200m | 78530 | 0.0 | 0.242 | -4.745 | 0.24 | 0.167 |
| all_fabdem_cells | 1810350 | -0.079 | 0.558 | -3.958 | 0.491 | 0.385 |

**Table T15e.** ICESat-2 ATL08 night ground segments in the audit window (p95p, Paper-1 frame): residuals of the model terrain, of FABDEM as delivered and of GLO-30 (median, NMAD, n) by class -- forest, open ground, wetland, the 200 m strip along the lowest path (the sill), the 200 m shoreline strip of the river network, all land cells. The sill is real within the data when the model residual in the path strip is near zero. [independent_physical]

| cls | n_points | n_dates | r_model_median_m | r_model_nmad_m | r_fabdem_median_m | r_fabdem_nmad_m | r_glo30_median_m | r_glo30_nmad_m |
|---|---|---|---|---|---|---|---|---|
| forest | 5456 | 5436 | 0.182 | 1.735 | 1.88 | 1.735 | 5.135 | 3.696 |
| open_ground | 23756 | 23428 | 0.243 | 0.432 | 0.503 | 0.433 | 0.474 | 0.364 |
| wetland | 2360 | 2359 | -0.037 | 0.467 | 0.552 | 0.467 | 0.484 | 0.505 |
| saddle_strip_200m | 576 | 576 | -0.021 | 0.882 | 0.705 | 0.736 | 0.701 | 0.784 |
| shoreline_strip_200m | 493 | 493 | -0.025 | 0.885 | 0.647 | 0.7 | 1.18 | 1.271 |
| all_land | 32441 | 31962 | 0.214 | 0.538 | 0.571 | 0.55 | 0.593 | 0.541 |

**Table T15g.** Cross-test of the saddle (p95p): the sill of every terrain surface evaluated along every route (the lowest path found on the model terrain and the one found on FABDEM as delivered), the water surface at the model sill, and the overlap of the two routes (Jaccard). The saddles of the two surfaces are NOT the same cells: the class-bias correction opens a different corridor, and along it FABDEM as delivered is 1.7 m higher at its highest point. [independent_physical] *(2 of 2 rows and 10 of 12 columns shown; full table: publication/tables/T15g.csv)*

| path_found_on | n_cells | length_km | sill_of_model_along_path_m | sill_of_model_at_km | sill_of_raw_along_path_m | sill_of_raw_at_km | sill_of_glo30_along_path_m | sill_of_glo30_at_km | H_2023-06-07_at_model_sill_m |
|---|---|---|---|---|---|---|---|---|---|
| model | 797 | 15.94 | 8.85 | 7.4 | 10.55 | 10.1 | 21.15 | 11.2 | 9.53 |
| raw | 419 | 8.38 | 10.0 | 3.3 | 10.41 | 2.6 | 22.14 | 4.5 | 9.52 |

**Table T15h.** Along the fixed lowest path of the model terrain, per 1 km bin: FABDEM as delivered, the model terrain, the class correction applied, the land cover, and the ICESat-2 night ground segments within 100 m (their median height and the residuals of the model and of FABDEM as delivered). Where the correction is verified and where it is not: the terrace edge (the sill) is verified to +0.1 m, the forest interior of the terrace has no segments, the floodplain forest and wetland are over-corrected by 0.4-0.6 m, the lowland interior is under-corrected by up to 1.5 m. [independent_physical] *(21 of 21 rows and 10 of 16 columns shown; full table: publication/tables/T15h.csv)*

| bin_km | n_cells | z_raw_median_m | z_model_median_m | correction_median_m | wc_mode | share_forest | share_wetland | share_bed | n_icesat |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 40 | 1.22 | -0.43 | -1.7 | trees | 0.78 | 0.23 | 0.0 | 0 |
| 1 | 41 | 0.58 | -0.69 | -1.7 | trees | 0.51 | 0.49 | 0.0 | 0 |
| 2 | 41 | 0.77 | -0.7 | -1.7 | trees | 0.54 | 0.39 | 0.0 | 0 |
| 3 | 40 | 1.08 | -0.62 | -1.7 | trees | 1.0 | 0.0 | 0.0 | 0 |
| 4 | 40 | 1.4 | -0.3 | -1.7 | trees | 1.0 | 0.0 | 0.0 | 0 |
| 5 | 36 | 0.93 | -0.77 | -1.7 | trees | 1.0 | 0.0 | 0.0 | 0 |
| 6 | 38 | 1.05 | -0.44 | -1.7 | trees | 0.79 | 0.03 | 0.0 | 51 |
| 7 | 40 | 0.38 | -0.25 | -0.59 | wetland | 0.25 | 0.65 | 0.0 | 145 |
| 8 | 37 | 1.17 | -0.14 | -1.7 | trees | 0.65 | 0.3 | 0.0 | 56 |
| 9 | 39 | 9.7 | 8.24 | -1.7 | trees | 0.59 | 0.0 | 0.0 | 0 |
| 10 | 37 | 9.87 | 8.31 | -1.7 | trees | 0.7 | 0.0 | 0.0 | 29 |
| 11 | 37 | 8.98 | 8.22 | -0.39 | grass | 0.43 | 0.0 | 0.0 | 6 |
| 12 | 40 | 10.12 | 8.65 | -1.7 | trees | 0.8 | 0.0 | 0.0 | 0 |
| 13 | 42 | 10.37 | 8.68 | -1.7 | trees | 1.0 | 0.0 | 0.0 | 0 |
| 14 | 37 | 9.89 | 8.2 | -1.7 | trees | 1.0 | 0.0 | 0.0 | 0 |
| 15 | 37 | 9.63 | 7.93 | -1.7 | trees | 1.0 | 0.0 | 0.0 | 0 |
| 16 | 39 | 9.16 | 8.76 | -0.39 | grass | 0.21 | 0.0 | 0.0 | 0 |
| 17 | 35 | 8.55 | 8.16 | -0.39 | grass | 0.0 | 0.0 | 0.0 | 65 |
| 18 | 35 | 7.33 | 6.89 | -0.39 | grass | 0.23 | 0.0 | 0.0 | 19 |
| 19 | 36 | 7.58 | 6.58 | -1.7 | trees | 0.64 | 0.0 | 0.0 | 14 |
| 20 | 30 | 7.82 | 6.19 | -1.7 | trees | 0.8 | 0.0 | 0.0 | 0 |

**Table T15i.** ICESat-2 residuals of the model terrain and of FABDEM as delivered along the fixed path by land-cover class (p95p): a single class-median correction over-corrects the forest and wetland of the floodplain and under-corrects the grass of the lowland here -- the local sign of the class residual is not constant, which the Monte-Carlo terrain term carries as random error, not as local bias. [independent_physical]

| wc_path | n | r_model_median_m | r_raw_median_m | r_model_nmad_m |
|---|---|---|---|---|
| trees | 103 | -0.62 | 1.08 | 0.45 |
| grass | 111 | 0.98 | 1.37 | 1.02 |
| water | 6 | -0.23 | -0.06 | 0.07 |
| wetland | 165 | -0.38 | 0.21 | 0.43 |

**Table T12g.** Per-cell inundation probability of the coherent Monte-Carlo worlds (p95e cellprob, the same worlds as T12): per key date and region the nominal area (draw 0), the expected area (sum of P = mean over the worlds), the area of the cells inundated in at least 5 / 25 / 50 / 75 / 95 % of the worlds (P >= 0.5 = the median world, the map product of the ensemble; its area is not the median of the areas), the share of the nominal cells with P >= 0.5, and the ensemble quantiles of the area for reference. A marginal component -- one that hangs on a sill within the water-surface or terrain uncertainty -- appears here with its probability instead of being cut by hand. [independent_physical] *(25 of 27 rows and 10 of 15 columns shown; full table: publication/tables/T12g.csv)*

| date | region | n_draws | A_nominal_km2 | A_expected_km2 | A_P_ge_0.05_km2 | A_P_ge_0.25_km2 | A_P_ge_0.50_km2 | A_P_ge_0.75_km2 | A_P_ge_0.95_km2 |
|---|---|---|---|---|---|---|---|---|---|
| 2023-06-06 | DNIPRO_CORRIDOR | 1000 | 132.14 | 152.08 | 335.39 | 209.1 | 124.15 | 81.27 | 43.32 |
| 2023-06-06 | INHULETS_VALLEY_rect | 1000 | 35.02 | 34.89 | 52.54 | 42.91 | 35.09 | 26.94 | 16.42 |
| 2023-06-06 | P42_FLOODPLAIN_DOMAIN | 1000 | 107.09 | 126.8 | 283.29 | 174.69 | 101.28 | 66.97 | 38.09 |
| 2023-06-07 | DNIPRO_CORRIDOR | 1000 | 214.86 | 233.12 | 458.79 | 306.02 | 206.13 | 145.62 | 77.73 |
| 2023-06-07 | INHULETS_VALLEY_rect | 1000 | 42.26 | 42.76 | 58.33 | 49.41 | 42.72 | 35.81 | 28.13 |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | 1000 | 170.54 | 188.11 | 360.25 | 244.09 | 166.23 | 123.48 | 68.16 |
| 2023-06-08 | DNIPRO_CORRIDOR | 1000 | 226.61 | 230.48 | 469.92 | 315.12 | 198.18 | 116.17 | 72.73 |
| 2023-06-08 | INHULETS_VALLEY_rect | 1000 | 46.39 | 46.99 | 62.06 | 53.47 | 47.09 | 40.3 | 32.48 |
| 2023-06-08 | P42_FLOODPLAIN_DOMAIN | 1000 | 181.11 | 181.22 | 366.41 | 255.73 | 158.21 | 87.64 | 57.51 |
| 2023-06-09 | DNIPRO_CORRIDOR | 1000 | 171.26 | 203.18 | 411.01 | 259.03 | 167.71 | 123.98 | 80.65 |
| 2023-06-09 | INHULETS_VALLEY_rect | 1000 | 49.59 | 50.09 | 65.04 | 56.54 | 50.13 | 43.53 | 35.5 |
| 2023-06-09 | P42_FLOODPLAIN_DOMAIN | 1000 | 124.65 | 152.29 | 319.98 | 199.12 | 122.98 | 90.16 | 59.42 |
| 2023-06-11 | DNIPRO_CORRIDOR | 1000 | 146.55 | 187.84 | 448.28 | 234.31 | 143.73 | 103.0 | 64.63 |
| 2023-06-11 | INHULETS_VALLEY_rect | 1000 | 44.71 | 45.15 | 60.44 | 51.8 | 45.27 | 38.22 | 30.32 |
| 2023-06-11 | P42_FLOODPLAIN_DOMAIN | 1000 | 111.87 | 137.3 | 300.18 | 185.44 | 109.87 | 77.11 | 48.8 |
| 2023-06-13 | DNIPRO_CORRIDOR | 1000 | 112.15 | 149.93 | 417.29 | 201.74 | 104.66 | 58.14 | 25.52 |
| 2023-06-13 | INHULETS_VALLEY_rect | 1000 | 37.01 | 37.44 | 54.24 | 44.78 | 37.57 | 29.94 | 21.09 |
| 2023-06-13 | P42_FLOODPLAIN_DOMAIN | 1000 | 91.49 | 114.79 | 287.57 | 168.53 | 86.08 | 47.25 | 22.09 |
| 2023-06-14 | DNIPRO_CORRIDOR | 1000 | 90.07 | 126.51 | 401.69 | 173.18 | 79.73 | 34.58 | 5.39 |
| 2023-06-14 | INHULETS_VALLEY_rect | 1000 | 31.21 | 31.75 | 49.66 | 39.43 | 31.79 | 23.84 | 14.6 |
| 2023-06-14 | P42_FLOODPLAIN_DOMAIN | 1000 | 76.59 | 98.7 | 279.34 | 151.06 | 68.46 | 30.39 | 4.66 |
| 2023-06-18 | DNIPRO_CORRIDOR | 1000 | 33.89 | 52.83 | 316.79 | 47.02 | 1.82 | 0.0 | 0.0 |
| 2023-06-18 | INHULETS_VALLEY_rect | 1000 | 10.1 | 9.64 | 29.09 | 17.14 | 4.86 | 1.15 | 0.0 |
| 2023-06-18 | P42_FLOODPLAIN_DOMAIN | 1000 | 30.57 | 38.34 | 219.93 | 44.18 | 1.7 | 0.0 | 0.0 |
| 2023-06-21 | DNIPRO_CORRIDOR | 1000 | 4.08 | 2.75 | 3.48 | 0.01 | 0.0 | 0.0 | 0.0 |

#### 4.2.4 Structural choices outside the budget

The structural choices of the reconstruction are deterministic runs and are compared with the nominal run of the primary rule
(215 km² on 7 June), not with the median (FigS02, T12): the p42 HAND
rule gives 269 km², the ceiling without connectivity
286 km², 4-connectivity
215 km², the superseded seeding from every
pre-breach water cell 260 km²
(§4.2.3), the memory variant (retained water)
215 km² on 7 June and
116 km² on 13 June (nominal
112 km²; the Sentinel-1 evidence on the retained cells in T11p)
and a surface only from nodes within
10 km 199 km²; declaring nodes unavailable
beyond a 3-day gap leaves 7 June at 215 km² but
raises 9 June to 229 km² (nominal
171 km²), in the delta far from the nodes. The largest single term is
definitional: with the terrain as delivered (no residual bias removed) the reed beds of the delta count as new inundation and the
areal maximum is 288 km² (§3.3). Several of
these choices move the peak area by more than the Monte-Carlo width: the uncertainty of the reconstruction is dominated by
structural and definitional choices, which are reported as sensitivities next to the interval rather than folded into it.

### 4.3 Independent validation and support [C03–C06, C12]

#### 4.3.1 Withheld gauges: the Inhulets backwater and the western delta

The Inhulets gauge Kalynivske (80575), about 40 km up the valley and withheld from the reconstruction, recorded the backwater —
0.58 m EVRF2019 before the breach and 6.59 m EVRF2019 on 2023-06-10 at its highest level, a record for the
station, with the upstream posts unchanged (80568: 289-303; 80564: 402-404) and high water on 7–18 June according to the
yearbook remark. At the gauge the reconstructed surface is the level of one Dnipro node below the dam,
39.5 km away, on 46 of 46 days. While the backwater was still travelling up the valley
the absolute error reached +9.50 m on 2023-06-06; the reconstruction peaks 3 days before the
gauge and rises by +9.28 m against +5.87 m at the gauge (daily means).
The event-relative error, free of any constant datum offset between the two series, shows that the close absolute agreement after
the peak (+0.04 .. +0.92 m) is a coincidence of the pre-breach offset and a recession that runs ahead of the
valley (-0.72 m on 2023-06-14); the two agree within ±0.25 m only from 2023-06-26 (T17c,
T17d, FigS15) [C03]. Because the support never changed, the error follows the hydraulic state: large during the transient, small
once main stem and valley stand at one level. A gauge-assisted sensitivity, not used for any reported number, adds the gauge as a
local water-surface node: the valley's new area on 7 June falls from
42.3 to
19.9 km² (nominal runs), and the
agreement with the independent Sentinel-1 observations on 9 June rises from CSI
0.29 to
0.31. The Inhulets areas are
therefore observation-constrained only in the lower valley; above it they are weakly constrained.

![FigS15](img/FigS15.jpg)

**FigS15 The two withheld gauges.** (a) Inhulets – Kalynivske 80575 and (b) Southern Bug – Mykolaiv 98027 (liman): yearbook daily means (EVRF2019; star: the highest level of the year), the reconstructed water surface at the gauge and the Kherson gauge (input). (c, d) Absolute error e_abs = reconstruction − gauge and event-relative error e_rise = (H_rec − H_rec,pre) − (H_gauge − H_gauge,pre), free of any constant datum offset. Neither gauge is an input; at Kalynivske the static reconstruction is metres too high while the backwater travels up the tributary and peaks three days early, at Mykolaiv the westernmost SWOT node is interpolated flat across the flood (T17c–T17f; §4.7, §5). ## Tables See `tables/README.md` (generated): T01 data inventory · T02/T02b labels and transition · T03/T03b/T03c split · T04 arms · T05 D1 endpoints with intervals · T05s/T06s/T07s the v004 arms per training seed · T06 paired comparisons · T07/T07b attribution endpoints · T08/T08b audit and retention (v002 arms, provenance) · T09/T10/T10b/T10c RF20 · T11/T11b terrain constants and uncertainty components · T11c Monte-Carlo convergence · T11d ablation of the budget · T11e water-surface offset sensitivity · T11f gap-matched interpolation error · T11g water-surface support · T11h rev 5 → rev 6 attribution (reproduction gate) · T11i seam check · T11j terrain source of the new area · T11k/T11l observational support of the new area (direct / extrapolated / weak, supported core, cross-river flag) · T12 daily area/volume with the Monte-Carlo band · T12c day of the areal maximum across the worlds · T12d emulator (computational diagnostic, not evidence) · T12f optional event-domain total, Dnipro corridor + Inhulets, date-matched within each Monte-Carlo world · T11m seed-class QA of the superseded all-prewater seeding: lineages of newly inundated components (river-connected / isolated-never / trapped) · T11n daily new inundation by seed class and run · T11o WorldCover class of the new inundation by seed class · T11p retained water of the memory sensitivity vs Sentinel-1 · T12g per-cell inundation probability of the Monte-Carlo worlds: areas by probability threshold, the median world (P ≥ 0.5) vs the nominal · T15d saddle audit of the lowland south of Krynky: lowest path, saddle and head on three terrain surfaces · T15e ICESat-2 night ground residuals of FABDEM and GLO-30 by class in the audit window · T15f FABDEM minus GLO-30 by class · T15g saddle cross-test: every surface along every route, route overlap · T15h the fixed path per kilometre: FABDEM as delivered, model terrain, correction, ICESat-2 ground · T15i ICESat-2 residuals along the path by land cover · T13 terrain vs S1 (raw POD/FAR/CSI; conditional POD diagnostic) · T14 disagreement ontology · T15 ICESat-2 · T16 area accounting with area, quantity and temporal semantics · T17/T17b SWOT-input vs gauge · T17c/T17d Inhulets gauge Kalynivske (withheld, independent validation site) vs the reconstruction · T17e/T17f liman gauge Mykolaiv (independent) vs the reconstructed surface · T18 terrain accuracy (Paper 2) · T18b FABDEM − ICESat-2 residual by zone and class · T18c residual semivariograms and fits · T19 per-date series · T20 block-size sensitivity · T21 reservoir balance (daily-mean effective release) · T22 hypsometry with the relative gap · T23 pool water area by source (model / S1 / S2 / Yi 2025, observed fraction, IoU vs model) · T24 S2 k10e classes in the pool by date and stratum · T25 S2 index statistics (7 indices, mean, p10–p90) by date and stratum · T26 S2 index display classes · T27 design hypsometry (monograph Table 19, whole pool and reaches, design levels) · T27b the observed 2023 levels (1 Feb – 10 Jul) read on the design curve with the DniproHES balance · T27c the spring filling week by week · T12b the daily series, MC median [p05–p95] with the nominal run · T12e flood depth below the dam · T21b water depth in the pool · T23b the day the bed fell dry (model + Sentinel-2) · T28 what changed after the review of 2026-09-28 (old / new / reason / effect on the conclusion).

**Table T17d.** Summary of T17c. Kalynivske is withheld from the primary water surface and kept as an independent tributary validation site (maintainer decision D-INHULETS, 2026-09-29): the backwater hydrograph (the yearbook's highest level of the year -- an instantaneous value, not a daily mean -- and the highest daily mean, rise, days above the floodplain exit, record exceedance, lag after the Kherson peak stage), the validation of the reconstruction at the gauge (absolute error e_abs; event-relative error e_rise, free of any constant datum offset; peak timing; recession), the water-surface support at the gauge, and the water-surface support at the gauge (the support of the valley's whole new area is classified in T11k/T11l). [independent_physical] *(25 of 39 rows and 3 of 3 columns shown; full table: publication/tables/T17d.csv)*

| id | item | value |
|---|---|---|
| gauge_max | gauge maximum: the yearbook's highest level | 772 cm above the gauge zero = +6.38 m BS-77 = 6.59 m EVRF201 |
| gauge_max_daily_mean | highest daily mean | 758 cm = 6.45 m EVRF2019 on 2023-06-10 |
| pre_breach_level | pre-breach level 26 May - 5 June (median of the daily means) | 171 cm = +0.37 m BS-77 = 0.58 m EVRF2019 |
| rise | rise to the highest level (in daily means) | 601 cm (587 cm) |
| pre_breach_evrf | pre-breach level, m EVRF2019 | 0.58 m EVRF2019 |
| highest_evrf | highest level, m EVRF2019 and date | 6.59 m EVRF2019 on 2023-06-10 |
| rise_m | rise to the highest level, m | 6.01 m |
| largest_daily_rise | largest daily rise | 235 cm on 2023-06-08 |
| days_above_floodplain_exit | days at or above the floodplain exit (490 cm) | 7 (2023-06-08 .. 2023-06-14) |
| record_exceedance | multi-year maximum of the passport (710 cm) exceeded: highes | by 62 cm (48 cm); the yearbook marks (772*) as the highest o |
| lag_after_kherson | lag of the gauge maximum after the Kherson peak stage | 2 d (Kherson maximum 2023-06-08) |
| upstream_posts | upstream posts 80568 / 80564 during 1-20 June (range, cm) | 80568: 289-303; 80564: 402-404 |
| nearest_node | nearest SWOT node to the gauge | 22511300080231 (Dnipro), 39.5 km; nodes within 3 km: 0 |
| recon_minus_gauge_pre | reconstruction - gauge, pre-breach (median) | +0.77 m |
| recon_minus_gauge_event | reconstruction - gauge, 6-20 June (median; range) | +0.57 m; +0.04 .. +9.50 m |
| day_of_max | day of the maximum: gauge / reconstruction | 2023-06-10 / 2023-06-07 |
| e_abs | absolute error e_abs = H_reconstructed - H_gauge (daily mean | pre-breach median +0.77 m; rising limb 2023-06-06 .. 2023-06 |
| e_rise | event-relative error e_rise = (H_rec - H_rec,pre) - (H_gauge | pre-breach median +0.01 m; rising limb 2023-06-06 .. 2023-06 |
| peak_timing | day of the maximum: reconstruction - gauge | -3 d (reconstruction 2023-06-07, gauge 2023-06-10) |
| rise_amplitude | rise to the maximum: reconstruction / gauge | +9.28 m / +5.87 m (daily means; +6.01 m to the highest level |
| recession | recession: e_rise after the gauge maximum | the reconstructed rise falls below the gauge's on 2023-06-12 |
| e_abs_rising_max | largest absolute error on the rising limb | +9.50 m on 2023-06-06 |
| e_abs_recession | absolute error from the day after the gauge maximum to 20 Ju | +0.04 .. +0.92 m |
| e_rise_at_gauge_max | event-relative error on the day of the gauge maximum | +0.69 m |
| e_rise_recession_min | most negative event-relative error after the gauge maximum | -0.72 m on 2023-06-14 |

The liman gauge Mykolaiv (98027), also withheld, tests the western end of the domain. The liman rose by
1.05 m to 1.22 m EVRF2019 on 2023-06-08, a record for the station, on the day of the Kherson peak stage.
The reconstructed western delta takes its surface from the westernmost SWOT node of the Dnipro, which has no observation from
2023-06-06 .. 2023-06-22 and is interpolated flat across the flood, so at the gauge the reconstruction misses
the rise (-0.82 m on 2023-06-08 in absolute terms; T17e, T17f, FigS15). SWOT itself saw the liman: Paper 1 tracks the
post day by day with Southern Bug nodes (r = 0.987 over the event, 22 passes), which lie outside the Dnipro domain of this
reconstruction. The two withheld gauges expose two different structural limits — the propagation time of the tributary backwater
at Kalynivske and the sampling of the water surface in the western delta at Mykolaiv — which a single error statistic would
average away.

**Table T17e.** The Dnipro-Buh liman at Mykolaiv (Southern Bug 98027; UkrHMC yearbook 2023 table 1.2, daily means in cm above the gauge zero, zero -5.00 m BS in the sheet header, EPSG:9902 grid step to EVRF2019; station catalogue position) per day, with the Kherson gauge and the reconstructed water surface extrapolated to the gauge (outside the terrain domain: water surface only; not an input of the reconstruction). The event days carry the yearbook flag '/' (meaning to be confirmed from the legend); wind setup / setdown of +-0.3-0.5 m is part of the regime. [independent_physical] *(25 of 46 rows and 10 of 21 columns shown; full table: publication/tables/T17e.csv)*

| date | post_id | lat | lon | stage_cm | flag | zero_bs77_m | delta_epsg9902_m | H_evrf2019_m | H_reconstructed_primary_m |
|---|---|---|---|---|---|---|---|---|---|
| 2023-05-26 | 98027 | 46.984375 | 31.97207222222222 | 503.0 |  | -5.0 | 0.1997 | 0.23 | 0.405 |
| 2023-05-27 | 98027 | 46.984375 | 31.97207222222222 | 502.0 |  | -5.0 | 0.1997 | 0.22 | 0.405 |
| 2023-05-28 | 98027 | 46.984375 | 31.97207222222222 | 500.0 |  | -5.0 | 0.1997 | 0.2 | 0.405 |
| 2023-05-29 | 98027 | 46.984375 | 31.97207222222222 | 496.0 |  | -5.0 | 0.1997 | 0.16 | 0.455 |
| 2023-05-30 | 98027 | 46.984375 | 31.97207222222222 | 496.0 |  | -5.0 | 0.1997 | 0.16 | 0.428 |
| 2023-05-31 | 98027 | 46.984375 | 31.97207222222222 | 496.0 |  | -5.0 | 0.1997 | 0.16 | 0.408 |
| 2023-06-01 | 98027 | 46.984375 | 31.97207222222222 | 502.0 |  | -5.0 | 0.1997 | 0.22 | 0.415 |
| 2023-06-02 | 98027 | 46.984375 | 31.97207222222222 | 510.0 |  | -5.0 | 0.1997 | 0.3 | 0.422 |
| 2023-06-03 | 98027 | 46.984375 | 31.97207222222222 | 497.0 |  | -5.0 | 0.1997 | 0.17 | 0.429 |
| 2023-06-04 | 98027 | 46.984375 | 31.97207222222222 | 486.0 |  | -5.0 | 0.1997 | 0.06 | 0.258 |
| 2023-06-05 | 98027 | 46.984375 | 31.97207222222222 | 495.0 |  | -5.0 | 0.1997 | 0.15 | 0.342 |
| 2023-06-06 | 98027 | 46.984375 | 31.97207222222222 | 514.0 | / | -5.0 | 0.1997 | 0.34 | 0.341 |
| 2023-06-07 | 98027 | 46.984375 | 31.97207222222222 | 568.0 | / | -5.0 | 0.1997 | 0.88 | 0.34 |
| 2023-06-08 | 98027 | 46.984375 | 31.97207222222222 | 596.0 | / | -5.0 | 0.1997 | 1.16 | 0.339 |
| 2023-06-09 | 98027 | 46.984375 | 31.97207222222222 | 595.0 | / | -5.0 | 0.1997 | 1.15 | 0.338 |
| 2023-06-10 | 98027 | 46.984375 | 31.97207222222222 | 581.0 | / | -5.0 | 0.1997 | 1.01 | 0.337 |
| 2023-06-11 | 98027 | 46.984375 | 31.97207222222222 | 559.0 | / | -5.0 | 0.1997 | 0.79 | 0.336 |
| 2023-06-12 | 98027 | 46.984375 | 31.97207222222222 | 544.0 | / | -5.0 | 0.1997 | 0.64 | 0.335 |
| 2023-06-13 | 98027 | 46.984375 | 31.97207222222222 | 537.0 | / | -5.0 | 0.1997 | 0.57 | 0.334 |
| 2023-06-14 | 98027 | 46.984375 | 31.97207222222222 | 528.0 | / | -5.0 | 0.1997 | 0.48 | 0.333 |
| 2023-06-15 | 98027 | 46.984375 | 31.97207222222222 | 524.0 | / | -5.0 | 0.1997 | 0.44 | 0.332 |
| 2023-06-16 | 98027 | 46.984375 | 31.97207222222222 | 520.0 | / | -5.0 | 0.1997 | 0.4 | 0.331 |
| 2023-06-17 | 98027 | 46.984375 | 31.97207222222222 | 514.0 |  | -5.0 | 0.1997 | 0.34 | 0.33 |
| 2023-06-18 | 98027 | 46.984375 | 31.97207222222222 | 510.0 |  | -5.0 | 0.1997 | 0.3 | 0.329 |
| 2023-06-19 | 98027 | 46.984375 | 31.97207222222222 | 510.0 |  | -5.0 | 0.1997 | 0.3 | 0.328 |

#### 4.3.2 Sentinel-1 per acquisition date [C04]

On 9 June, in the p42 floodplain domain and on the Sentinel-1 footprint, the reconstruction allows
124 km² of new water and Sentinel-1
reports 201 km²; they share
52 km² (POD
0.26, FAR
0.58, CSI
0.19). Of the
149 km² that Sentinel-1 reports and the
reconstruction does not, 146 km²
lie on normally-wet cells. The raw agreement is therefore low, and most apparent terrain misses occur in predefined normally-wet or
vegetation-dominated cells where SAR dark-water onset is not an appropriate binary reference; the conditional POD outside the
normally-wet class is 0.94,
a diagnostic conditional agreement, not a corrected POD. On 13 June the raw POD is
0.16 and the conditional POD
0.91. After 18 June the
Sentinel-1 "new water" outside the floodplain domain (155 km²
on 21 June in the corridor) is scattered on fields and sand while the gauge is at its pre-breach level and the reconstruction is at
3 km²: these detections are not supported as connected breach-induced
inundation by the available terrain and water-surface constraints; whether they are non-water, local ponding after rain or water
outside the assumed connectivity is not tested here. The large-scale recession seen by Sentinel-1 inside the floodplain (T19)
follows the reconstruction and the gauge (Fig04).

**Table T19.** Per-acquisition-date new water (not water before the breach) inside the Sentinel-1 observable domain, with coverage; S2 only where >= 30 % of the region was cloud-free; estuary zone on its own grid. [cross_sensor] *(25 of 77 rows and 9 of 9 columns shown; full table: publication/tables/T19.csv)*

| date | sensor | orbit | region | coverage | water_km2 | new_water_km2 | new_water_common_footprint_km2 | area_semantics |
|---|---|---|---|---|---|---|---|---|
| 2023-06-01 | S1 | orb65_DES | DNIPRO_CORRIDOR | 1.0 | 465.0 | 0.0 | 0.0 | observed_S1 |
| 2023-06-01 | S1 | orb65_DES | INHULETS_VALLEY_rect | 1.0 | 47.0 | 0.0 | 0.0 | observed_S1 |
| 2023-06-01 | S1 | orb65_DES | P42_FLOODPLAIN_DOMAIN | 1.0 | 122.5 | 0.0 | 0.0 | observed_S1 |
| 2023-06-02 | S1 | orb87_ASC | DNIPRO_CORRIDOR | 0.951 | 506.1 | 0.0 | 0.0 | observed_S1 |
| 2023-06-02 | S1 | orb87_ASC | INHULETS_VALLEY_rect | 1.0 | 80.4 | 0.0 | 0.0 | observed_S1 |
| 2023-06-02 | S1 | orb87_ASC | P42_FLOODPLAIN_DOMAIN | 1.0 | 126.2 | 0.0 | 0.0 | observed_S1 |
| 2023-06-06 | S1 | orb138_DES | DNIPRO_CORRIDOR | 0.619 | 365.5 | 30.3 | 27.2 | observed_S1 |
| 2023-06-06 | S1 | orb138_DES | INHULETS_VALLEY_rect | 0.829 | 22.9 | 4.7 | 4.6 | observed_S1 |
| 2023-06-06 | S1 | orb138_DES | P42_FLOODPLAIN_DOMAIN | 0.623 | 84.3 | 8.6 | 8.5 | observed_S1 |
| 2023-06-09 | S1 | orb14_ASC | DNIPRO_CORRIDOR | 0.938 | 682.5 | 299.6 | 250.3 | observed_S1 |
| 2023-06-09 | S1 | orb14_ASC | INHULETS_VALLEY_rect | 1.0 | 67.6 | 36.1 | 33.5 | observed_S1 |
| 2023-06-09 | S1 | orb14_ASC | P42_FLOODPLAIN_DOMAIN | 0.991 | 329.6 | 202.9 | 162.6 | observed_S1 |
| 2023-06-13 | S1 | orb65_DES | DNIPRO_CORRIDOR | 1.0 | 548.3 | 170.1 | 129.9 | observed_S1 |
| 2023-06-13 | S1 | orb65_DES | INHULETS_VALLEY_rect | 1.0 | 36.2 | 27.0 | 26.8 | observed_S1 |
| 2023-06-13 | S1 | orb65_DES | P42_FLOODPLAIN_DOMAIN | 1.0 | 279.4 | 152.3 | 115.2 | observed_S1 |
| 2023-06-14 | S1 | orb87_ASC | DNIPRO_CORRIDOR | 0.951 | 510.3 | 97.4 | 63.2 | observed_S1 |
| 2023-06-14 | S1 | orb87_ASC | INHULETS_VALLEY_rect | 1.0 | 36.5 | 25.4 | 25.4 | observed_S1 |
| 2023-06-14 | S1 | orb87_ASC | P42_FLOODPLAIN_DOMAIN | 1.0 | 196.0 | 74.2 | 44.1 | observed_S1 |
| 2023-06-18 | S1 | orb138_DES | DNIPRO_CORRIDOR | 0.618 | 404.6 | 51.7 | 46.0 | observed_S1 |
| 2023-06-18 | S1 | orb138_DES | INHULETS_VALLEY_rect | 0.822 | 36.3 | 18.1 | 18.1 | observed_S1 |
| 2023-06-18 | S1 | orb138_DES | P42_FLOODPLAIN_DOMAIN | 0.622 | 88.0 | 10.2 | 10.1 | observed_S1 |
| 2023-06-21 | S1 | orb14_ASC | DNIPRO_CORRIDOR | 0.937 | 528.5 | 154.7 | 112.0 | observed_S1 |
| 2023-06-21 | S1 | orb14_ASC | INHULETS_VALLEY_rect | 1.0 | 58.7 | 32.6 | 29.2 | observed_S1 |
| 2023-06-21 | S1 | orb14_ASC | P42_FLOODPLAIN_DOMAIN | 0.991 | 144.6 | 22.3 | 11.1 | observed_S1 |
| 2023-06-25 | S1 | orb65_DES | DNIPRO_CORRIDOR | 1.0 | 538.9 | 98.9 | 44.2 | observed_S1 |

#### 4.3.3 The disagreement is mechanistic, and the surface context explains it [C05, C12]

On 9 June the two zones together give A = 59 km², B (terrain only) =
112 km² and C (Sentinel-1 only) = 260 km²
(T14, Fig05; the Sentinel-1 new dark water of every full-coverage date is mapped in FigS19). B lies entirely below the reconstructed surface and is dominated by surfaces the dark-water rule cannot see:
36 km² trees, 19 km²
wetland and 24 km² built-up. C splits by ground elevation:
164 km² below the surface and
36 km² within 2 m above it, of which
169 km² are normally-wet reed beds — the submergence of emergent vegetation,
a depth signal; and 54 km² at least 5 m above the surface, on cropland
and grass: S1-only detections that are topographically inconsistent with the reconstructed connected water surface. Whether they
are smooth non-water surfaces, radar shadow, local ponding after rain, water outside the assumed connectivity, timing or
registration effects is not tested here; what §4.3.4 tests is whether a terrain error could explain them.

![Fig05](img/Fig05.jpg)

**Fig05 Disagreement ontology on 2023-06-09.** (a) Agreement between the reconstruction and Sentinel-1 on the S1 footprint: A both, B terrain only, C S1 only split by ground elevation relative to the reconstructed surface. (b) B by WorldCover class: forest, wetland and built-up dominate (SAR blind spots). (c) C by ground elevation: cells below or within 2 m of the surface are mostly normally-wet reed beds where S1 dark-water onset is a submergence signal; S1-only detections on ground ≥ 5 m above the reconstructed connected water surface are topographically unsupported (Fig08). Km² are mapped areas (T14).

![FigS19](img/FigS19.jpg)

**FigS19 Sentinel-1 new dark water by acquisition date (observed_S1).** The dark-water mask of each Sentinel-1 scene that covers the corridor fully (6, 9, 13, 14, 18 and 21 June 2023; orbit in the panel title) minus the optical pre-breach water (p60) and minus the cells already dark on 1–2 June, on the Sentinel-2 image of June 2022: new dark water in blue, the pre-breach water in grey, the ground the scene did not observe hatched, and the terrain-reconstructed new inundation of the same day as a black line (nominal world). Coverage of the observable domain and the corridor area in the titles (T19). What the radar sees on the day it looks — not water under trees, in built-up land or under emergent reeds (Fig05, T14).

The surface classes of this decomposition come from RF20, whose agreement with its training reference, WorldCover, is
0.938 overall in spatial-block cross-validation (macro
F1 0.941; 0.929
with a 3.5 km buffer; wetland/reed F1 0.947, built-up F1
0.938; T09, FigS04). Removing frame-overlap duplication had little
effect on within-domain spatial CV (macro F1 0.943 before,
0.941 after) but substantially reduced apparent B1→B2 transfer
performance (0.904 → 0.848;
B2→B1 0.907), showing that the overlap primarily biased estimates of
geographic generalization [C12]. These are agreement numbers against the training reference, not an independent land-cover
accuracy.

![FigS04](img/FigS04.jpg)

**FigS04.** RF20 (rev 2: global blocks, frame overlap counted once) row-normalised confusion (spatial-block CV) and per-class F1 for the CV without and with a 3.5 km buffer and for the transfers outside the overlap.

#### 4.3.4 ICESat-2 altimetric consistency [C06]

Where Sentinel-1 reports water at least 2 m above the reconstructed surface, the FABDEM-sourced terrain agrees with night
ICESat-2 ground heights to +0.03 m in the delta
(p10–p90 -0.31 to
+0.64 m;
3205 segments on
17 passes) and
+0.02 m in the floodway
(1666 segments on
59 passes); the ICESat-2 ground lies
+13.5 m above the surface in the delta and
essentially no segment (0.0%) lies below it.
The passes, not the segments, are the independent units. Because the same night corpus calibrates the class bias, the bias was
re-estimated without the checked passes: the median of this category moves by at most
0.04 m in any hold-out scheme (T15b), and calibrating on the passes
of one epoch and checking the other changes the corrected medians by up to 0.24 m in the
delta, whose class biases rest on few passes (T15c). The available ICESat-2 observations therefore provide no evidence for a terrain
bias large enough to explain those S1-only detections; they support the reading of §4.3.3 without proving it, because the passes
sample the category along lines, not every cell. Where the reconstruction and Sentinel-1 agree,
99.6% of the segments lie below the surface (T15, Fig08). This is a
track-based consistency check of the terrain and the surface, not a validation of the map.

![Fig08](img/Fig08.jpg)

**Fig08 ICESat-2 altimetric consistency check.** FABDEM-sourced terrain minus night ICESat-2 ATL08 ground height (median, p10–p90) per agreement category of 2023-06-09 (categories inside the Sentinel-1 valid footprint only), as delivered (circles) and after the residual class-bias correction used by the reconstruction (diamonds), with the ground elevation relative to the reconstructed surface and the share of segments below it. ATL08 night passes 2019–2025; n segments and passes (acquisition days, the independent units) in T15. The p10–p90 bars are the spread of the sampled residuals, not a confidence interval of the median and not a map-wide uncertainty. The same night corpus calibrates the class bias, so the diamonds are in-sample; with the bias re-estimated without the checked passes (T15b) the medians of the S1-only ≥ 2 m category move by a few centimetres at most. Where S1 reports water ≥ 2 m above the surface the DEM agrees with the altimetry to a few centimetres in the median (p10–p90 spread of a few decimetres) along the tracks and essentially no segment lies below the water, so the available ICESat-2 observations give no evidence for a DEM bias large enough to explain those S1-only detections. A track-based consistency check that supports this reading; it does not sample every cell and does not validate the map.

#### 4.3.5 The reservoir from orbit

Where Sentinel-2 could see through the clouds during the drawdown week it agrees with the modelled pool: on 8 June it observed
37% of the pool, mostly the broad middle reach, and found
709 km² of water, with an IoU of
0.90 against the model on the same cells; on 13 June
(17% observed) the IoU is
0.85, with 43 km²
that the model keeps wet and Sentinel-2 sees dry (Fig11b, c; T23). On 20 June, with the whole pool observed, Sentinel-2 finds
648 km² of water; the Sentinel-1 reservoir areas of Yi et al. (2025, read
from the authors' archive) fall from 2089 km² on 8 June to
825 km² on 20 June, the same sequence (Fig11h). Our own Sentinel-1 VH dark
surface agrees with the modelled pool until 13 June (IoU 0.97 on 8 June,
0.84 on 13 June) but afterwards it is open water *or* smooth wet sediment and no
longer a water area (1702 km² dark on 20 June; FigS08); the wet-mud reading is
consistent with the documented look-alike behaviour of smooth bare surfaces in C-band (Shen et al. 2019), although no study in the
literature reviewed measures it for wet reservoir sediment. Published remnant areas differ by definition rather than by error: about
845 km² by 20 June from the decreases reported by Yi et al. (2025), 655.9 km² on 17 June in the state estimate quoted by Novitskyi
et al. (2024), 379.7 km² on 8 September including the restored channel (Magas et al. 2023), and 1.63 km² of open water on
6 September with 110 km² still wet (Tsiupa et al. 2023). By 8 September reed or flooded vegetation covers
46 % of the bed exposed first and
34 % of the rest (T24); the recolonisation is what field
surveys report — the number of vascular plant taxa rising about sevenfold between June and October 2023, mainly willow establishing
(Kuzemko et al. 2024, 2025; Vyshnevskyi 2024) — and what index-based studies document from Sentinel-2 (Tutova et al. 2025; 135
thousand ha of vegetated bed in 2023–2024, Pichura and Potravka 2025). These are observations of the bed, the hand-over to Paper 4.

![FigS08](img/FigS08.jpg)

**FigS08.** The modelled pool and the Sentinel-1 view of it (p95h). (a–c) Modelled pool water on 7, 9 and 13 June: the p95f sloped daily surface over the seamless DEM inside the pre-breach pool (*terrain_reconstructed*; 13 June an upper estimate); (d) the day a cell wet on 5 June first falls dry under the modelled surface within 6–13 June (after 13 June the level records end: Fig11e). (e–h) Sentinel-1 VH dark surface, per-date Otsu over all covered cells (*observed_S1*), with the IoU against the model on observed cells. VH dark means open water **or** smooth wet mud, so after ~13 June Sentinel-1 is no longer a water area on the exposed flats (dark surface on 20–21 June against 648 km² of Sentinel-2 water on 20 June, T23). Not observed is not dry.

**Table T23.** Kakhovka pool water area by source and date inside the pre-breach pool polygon: MODEL (p95f sloped surface over the seamless DEM, terrain_reconstructed, 05-26..06-13), Sentinel-1 VH dark surface (per-date Otsu; open water or smooth wet mud), Sentinel-2 water (frozen p25 water3 and p15 crosscheck), with the observed fraction of the pool, IoU against the model on observed cells, and Yi et al. 2025 (literature_reported; the Sentinel-1 reservoir areas of the authors' code archive, Zenodo 14639520, observations.mat obs.A -- read from the archive, not digitised, not quoted from their text). Areas count observed cells only; not observed is not dry. On the S2 crosscheck dates with a model surface (8 and 13 June) the model is compared on the cells S2 observed (IoU, model km2, model wet where S2 sees no water). Maps: Fig11 (Sentinel-2, day of exposure) and FigS08 (model extent, Sentinel-1). [cross_sensor] *(25 of 53 rows and 10 of 14 columns shown; full table: publication/tables/T23.csv)*

| date | source | semantics | water_km2 | observed_frac | iou_vs_model | model_km2_on_observed | model_wet_s2_dry_km2 | vh_threshold_db | orbits |
|---|---|---|---|---|---|---|---|---|---|
| 2023-05-26 | MODEL | terrain_reconstructed | 2136.6 | 1.0 |  |  |  |  |  |
| 2023-05-27 | MODEL | terrain_reconstructed | 2136.5 | 1.0 |  |  |  |  |  |
| 2023-05-28 | MODEL | terrain_reconstructed | 2136.0 | 1.0 |  |  |  |  |  |
| 2023-05-29 | MODEL | terrain_reconstructed | 2135.7 | 1.0 |  |  |  |  |  |
| 2023-05-30 | MODEL | terrain_reconstructed | 2136.1 | 1.0 |  |  |  |  |  |
| 2023-05-31 | MODEL | terrain_reconstructed | 2135.9 | 1.0 |  |  |  |  |  |
| 2023-06-01 | MODEL | terrain_reconstructed | 2135.8 | 1.0 |  |  |  |  |  |
| 2023-06-02 | MODEL | terrain_reconstructed | 2135.0 | 1.0 |  |  |  |  |  |
| 2023-06-03 | MODEL | terrain_reconstructed | 2135.0 | 1.0 |  |  |  |  |  |
| 2023-06-04 | MODEL | terrain_reconstructed | 2115.2 | 1.0 |  |  |  |  |  |
| 2023-06-05 | MODEL | terrain_reconstructed | 2132.0 | 1.0 |  |  |  |  |  |
| 2023-06-06 | MODEL | terrain_reconstructed | 2092.0 | 1.0 |  |  |  |  |  |
| 2023-06-07 | MODEL | terrain_reconstructed | 2054.2 | 1.0 |  |  |  |  |  |
| 2023-06-08 | MODEL | terrain_reconstructed | 2012.5 | 1.0 |  |  |  |  |  |
| 2023-06-09 | MODEL | terrain_reconstructed | 1956.5 | 1.0 |  |  |  |  |  |
| 2023-06-10 | MODEL | terrain_reconstructed | 1894.2 | 1.0 |  |  |  |  |  |
| 2023-06-11 | MODEL | terrain_reconstructed | 1837.5 | 1.0 |  |  |  |  |  |
| 2023-06-12 | MODEL | terrain_reconstructed | 1815.0 | 1.0 |  |  |  |  |  |
| 2023-06-13 | MODEL | terrain_reconstructed | 1790.0 | 1.0 |  |  |  |  |  |
| 2023-06-01 | S1 | observed_S1 | 1964.1 | 0.929 | 0.984 | 1979.0 |  | -17.25 | orb65_DES |
| 2023-06-02 | S1 | observed_S1 | 36.1 | 0.017 | 0.986 | 36.3 |  | -17.75 | orb87_ASC |
| 2023-06-04 | S1 | observed_S1 | 1495.4 | 0.714 | 0.973 | 1494.8 |  | -17.75 | orb116_ASC |
| 2023-06-08 | S1 | observed_S1 | 1704.6 | 0.791 | 0.967 | 1654.3 |  | -19.05 | orb167_DES |
| 2023-06-09 | S1 | observed_S1 | 2087.1 | 1.0 | 0.925 | 1955.9 |  | -18.75 | orb14_ASC |
| 2023-06-13 | S1 | observed_S1 | 1937.5 | 0.929 | 0.836 | 1650.4 |  | -16.95 | orb65_DES |

### 4.4 Weak-label ML diagnostics [C08–C13]

#### 4.4.1 The optical component behind the labels

The previous threshold-selection procedure used predictions from samples also used to fit the classifier and failed to achieve its
nominal 0.90 recall target on held-out data. Replacing it with out-of-fold threshold calibration restored the intended recall (T02c):
for the original model the in-sample rule gave a block-median threshold of
0.536 and an outer-test recall of
0.852, out-of-fold calibration
0.306 and
0.931; for the canonical model without the post-event
window, 0.446 and
0.860 against
0.266 and
0.928. With a 3.5 km buffer around the outer test
blocks the out-of-fold threshold reaches a recall of
0.808 (in-sample
0.575): distance from the
calibration data still costs recall. The M2 score is not interpreted as a flood probability. Without the post-event window, M2
scores pre-event open water as flood-like — open water lies outside the pre-breach land on which it is trained — and the label rules
keep that water out of EVENT_FLOOD (only 0.7 and
2.0 km² of REFERENCE_WATER in B1 and B2 change to
EVENT_FLOOD, T02d). High scores over permanent open water demonstrate that M2 separates the training classes used for weak-label
construction but is not a standalone flood classifier.

#### 4.4.2 The canonical label ontology v004

v004 labels 141.9 km² of EVENT_FLOOD in B1 and 75.2 km² in
B2, with 1514 and 643 km² of LAND and
258 and 282 km² of REFERENCE_WATER; everything
else is UNKNOWN (T02). Against the intermediate v003_A, the corrected optical component adds
12.4 and
15.7 km² of EVENT_FLOOD from UNKNOWN in B1 and B2, moves
2.0% and
3.1% of LAND to UNKNOWN and leaves REFERENCE_WATER almost
unchanged (T02d): the correction moved the weak labels at their margins, not at their core.

#### 4.4.3 Training-seed variability

Three training seeds of the same arm on the same split and labels differ by as much as
20.8 km² in the predicted-flood
burden on unlabelled cropland (U1; U0d 9.0 km²,
U2 4.1 km²), while the global agreement
with the weak labels varies little (U2: F1 0.931–0.935;
T05s, FigS01). This training noise is the scale that a difference between arms must exceed to be reported.

![FigS01](img/FigS01.jpg)

**FigS01.** training loss and validation patch F1 per arm.

**Table T05s.** Training-seed variability of the U-Net arms on the corrected labels (v004; U2 also on v002_notrace): D1 endpoints of three seeds per arm on the frozen TEST blocks (same split, labels and recipe; each run at its own frozen validation threshold), with mean, SD and range across seeds -- the training noise a between-arm difference has to exceed (review F11). Agreement with weak labels, not accuracy. [weak_label_agreement] *(25 of 190 rows and 10 of 12 columns shown; full table: publication/tables/T05s.csv)*

| labels | arm | endpoint | n_seeds | s20260923 | s20261001 | s20261002 | mean | sd | min |
|---|---|---|---|---|---|---|---|---|---|
| v004 | U0d | A_FP_area_dry_cropland_km2 | 3 | 0.5397 | 0.2942 | 1.247 | 0.6936333333333334 | 0.4947004784041889 | 0.2942 |
| v004 | U0d | A_FP_rate_dry_cropland | 3 | 0.002135 | 0.001164 | 0.004933 | 0.002744 | 0.0019569110863807 | 0.001164 |
| v004 | U0d | A_evaluated_dry_cropland_km2 | 3 | 252.77 | 252.77 | 252.77 | 252.77 | 0.0 | 252.77 |
| v004 | U0d | B_recall_flooded_open_low_veg | 3 | 0.6032 | 0.6429 | 0.6326 | 0.6262333333333333 | 0.0206015371594775 | 0.6032 |
| v004 | U0d | B_IoU_open_low_veg | 3 | 0.5462 | 0.6017 | 0.5204 | 0.5560999999999999 | 0.0415443136903235 | 0.5204 |
| v004 | U0d | B_FN_area_km2 | 3 | 2.5702 | 2.313 | 2.3795 | 2.4209 | 0.1335044194025049 | 2.313 |
| v004 | U0d | B_reference_km2 | 3 | 6.477 | 6.477 | 6.477 | 6.477 | 0.0 | 6.477 |
| v004 | U0d | C_recall_flooded_cropland_LOWN | 3 | 0.7725 | 0.7807 | 0.7796 | 0.7776 | 0.0044508426168535 | 0.7725 |
| v004 | U0d | C_FN_area_km2 | 3 | 0.1462 | 0.1409 | 0.1416 | 0.1429 | 0.0028792360097775 | 0.1409 |
| v004 | U0d | C_reference_km2 | 3 | 0.643 | 0.643 | 0.643 | 0.643 | 0.0 | 0.643 |
| v004 | U0d | W_precision | 3 | 0.9677 | 0.9712 | 0.9698 | 0.9695666666666666 | 0.0017616280348964 | 0.9677 |
| v004 | U0d | W_recall | 3 | 0.9795 | 0.9859 | 0.9798 | 0.9817333333333332 | 0.0036115555282084 | 0.9795 |
| v004 | U0d | W_IoU | 3 | 0.9485 | 0.958 | 0.9508 | 0.9524333333333334 | 0.0049561409718987 | 0.9485 |
| v004 | U0d | BU_FP_area_km2 | 3 | 0.3561 | 0.4655 | 0.5279 | 0.4498333333333333 | 0.0869648971328853 | 0.3561 |
| v004 | U0d | BU_precision | 3 | 0.5292 | 0.5051 | 0.4581 | 0.4974666666666666 | 0.0361594155557488 | 0.4581 |
| v004 | U0d | BS_FP_area_km2 | 3 | 0.0076 | 0.0131 | 0.0043 | 0.0083333333333333 | 0.0044455970727601 | 0.0043 |
| v004 | U0d | G_F1 | 3 | 0.9261 | 0.9336 | 0.9228 | 0.9275 | 0.0055344376408086 | 0.9228 |
| v004 | U0d | G_IoU | 3 | 0.8624 | 0.8755 | 0.8567 | 0.8648666666666666 | 0.0096396749599419 | 0.8567 |
| v004 | U0d | G_precision | 3 | 0.9305 | 0.9319 | 0.9187 | 0.9270333333333332 | 0.0072507470879443 | 0.9187 |
| v004 | U0d | G_recall | 3 | 0.9217 | 0.9354 | 0.927 | 0.9280333333333334 | 0.0069082076787929 | 0.9217 |
| v004 | U0d | A1_isolated_field_FP_km2 | 3 | 0.4253 | 0.2613 | 0.9852 | 0.5572666666666667 | 0.3795644916655578 | 0.2613 |
| v004 | U0d | A2_pred_flood_on_nonflood_cropland_km2 | 3 | 0.5397 | 0.2942 | 1.247 | 0.6936333333333334 | 0.4947004784041889 | 0.2942 |
| v004 | U0d | A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2 | 3 | 6.4036 | 3.7814 | 12.7773 | 7.6541 | 4.626485371207824 | 3.7814 |
| v004 | U0d | A2_unlabelled_cropland_evaluated_km2 | 3 | 474.6 | 474.6 | 474.6 | 474.6000000000001 | 6.961868572213853e-14 | 474.6 |
| v004 | U0d | A2_frac_unlabelled_cropland_above_thr | 3 | 0.01349 | 0.00797 | 0.02692 | 0.0161266666666666 | 0.0097462625315211 | 0.00797 |

#### 4.4.4 What the arms show under weak supervision

*Reference water in the labels [C09].* Changing the weak-label treatment of pre-event reference water produced a consistent model
response across all three training seeds: predictions over reference-water areas decreased by
13.8–48.8
km² under the v004 ontology (U2 trained on v002_notrace, the same rule without a REFERENCE_WATER class, against U2 on v004 at fixed
inputs; per seed -13.8
[-35.3,
-1.4],
-25.6
[-62.6,
-3.7] and
-48.8
[-111.3,
-11.1] km²; T07s). This demonstrates
sensitivity of the learned flood representation to the weak-label definition of pre-event water rather than independent
flood-mapping accuracy. EVENT_FLOOD recall changed by
-0.034,
-0.002 and
-0.005, with an interval excluding zero in
1 of the three seeds. Global F1
is not comparable across label sets.

*Terrain as an input [C10].* The apparent reduction in unlabelled-cropland predictions previously attributed to HAND did not
reproduce under the corrected v004 ontology and three training seeds. The effect changed sign across seeds
(+1.0,
+7.6, and
-3.8 km²),
indicating that the earlier
-9.6 km² result was not
robust to label revision and training stochasticity. HAND also left the flood on reference water and the built-up false positives
without a consistent change (intervals excluding zero in
1 and
0 of three seeds; T06s, T07s).

*Land cover as an input [C10].* Supplying the RF20 classes as an input (U1) did not act as a veto: it raised the unlabelled-cropland
burden in all three seeds
(+6.8,
+27.3 and
+21.1 km²;
3 of
three intervals exclude zero) while lowering the built-up false positives
(-0.23,
-0.34 and
-0.36 km², the same sign in every seed).

*Pre-event water as an input [C11].* Adding the pre-event water term W_pre consistently reduced the unlabelled-cropland prediction
burden across all three training seeds
(-6.0,
-8.6 and
-7.5 km²),
while its effect over reference-water areas was consistent in two of three seeds
(+7.45,
-0.73 and
-0.77 km²; intervals excluding zero in
2). Because W_pre is itself a
component of the weak-label construction, this result is interpreted as a diagnostic of label-induced model behaviour rather than
independent evidence of improved flood discrimination.

#### 4.4.5 Block size [C13]

U2 on v004 reaches a global F1 against the weak labels of 0.931 on the frozen 10 km split,
0.940 at 7.5 km, 0.932 at 15 km and
0.889 at 20 km (each split with its own test geography and interval, one arm and one seed
per split; T20, FigS05); a 5 km split leaves no validation patch inside the buffers. The tested range is meaningful because every
block is larger than the local object scale (fields, reed beds), comparable to or larger than the spatial correlation length of the
change channels, and larger than the 5.12 km patch plus buffers (Roberts et al. 2017; Valavi et al. 2019). The level of agreement
drops mainly at 20 km, where few test blocks remain; the arm comparisons of §4.4.4 are drawn from the 10 km split only.

![FigS05](img/FigS05.jpg)

**FigS05.** block-size sensitivity of U2 on v003_A and on v004 (7.5 / 10 / 15 / 20 km; each split has its own TEST geography).

#### 4.4.6 Three areas, three definitions [C08]

For the same corridor the 9 June Sentinel-1 scene contains 300 km² of new dark
water (observed_S1), the label recipe (water on ≥ 2 of 3 peak dates) 168 km²,
the U-Net arm U2b on v004 352,
297 and 269 km²
with its three seeds (mapped_UNet), and the reconstruction 201 km² on 9 June
and 239 km² at the reconstructed areal maximum (terrain_reconstructed,
Monte-Carlo medians). The label contract is a persistence product and describes the regime around 13 June, and the mapped area of a
model trained on it depends on the training seed. The operational figures — UNOSAT product 3616, ~620 km² of satellite-detected
flooded land cumulative over 6–9 June with the pre-existing water as a separate class, preliminary and not field-validated; product
3623, ~180 km² on 13 June against the reference water of 3/5 June (T16, literature_reported; both product sheets read) — are flooded *land*, closer in
kind to the newly inundated area than to the total water-surface area, and differ in AOI, temporal semantics (cumulative vs
snapshot) and reference water; they are context, not validation. Two peer-reviewed mappings of the same flood carry their own
definitions as well: Yailymov et al. (2025) count 473 km² of flooded land as of 9 June across the Kherson region including the
Inhulets valley, relative to a pre-flood water map of 5 June, of which 294 km² are wetlands — the class in which this paper's
submergence category lives — and Zuo et al. (2024) follow the total water-surface area at 300 m resolution, largest around 9 June.
Neither is the corridor snapshot of this paper. T16 carries the area, quantity and temporal semantics of every row.

**Table T16.** Area accounting with explicit semantics: observed (S1), mapped (U-Net: the canonical v004 labels with three training seeds; v003_A as provenance), terrain-reconstructed (Monte-Carlo median with p05-p95; the nominal run only as a diagnostic column) and literature-reported figures are different quantities (new vs total water; snapshot vs cumulative vs persistence) and are never compared as validation. row_id addresses a row. [mixed] *(25 of 59 rows and 10 of 13 columns shown; full table: publication/tables/T16.csv)*

| row_id | region | quantity | km2 | area_semantics | quantity_semantics | temporal_semantics | unobserved_km2 | km2_p05 | km2_p95 |
|---|---|---|---|---|---|---|---|---|---|
| s1_new_0609 | DNIPRO_CORRIDOR | S1 new dark water, 06-09 scene | 299.6 | observed_S1 | new_water (pre-breach water excluded) | snapshot_2023-06-09 |  |  |  |
| s1_label_recipe | DNIPRO_CORRIDOR | S1 new dark water, >= 2 of 3 peak dates (label recipe) | 167.8 | observed_S1 | new_water (pre-breach water excluded) | persistence_2of3_(06-09,06-13,06-14) |  |  |  |
| s1_total_0609 | DNIPRO_CORRIDOR | S1 total dark water, 06-09 (incl. pre-breach water) | 682.5 | observed_S1 | total_water | snapshot_2023-06-09 |  |  |  |
| pre_breach_water | DNIPRO_CORRIDOR | pre-breach water (S1 06-01/02 or p60 pre_water_frac >= 20 %) | 594.4 | observed_S1 | reference_water | reference_2023-06-01/02 |  |  |  |
| s1_new_0609 | INHULETS_VALLEY_rect | S1 new dark water, 06-09 scene | 36.1 | observed_S1 | new_water (pre-breach water excluded) | snapshot_2023-06-09 |  |  |  |
| s1_label_recipe | INHULETS_VALLEY_rect | S1 new dark water, >= 2 of 3 peak dates (label recipe) | 27.2 | observed_S1 | new_water (pre-breach water excluded) | persistence_2of3_(06-09,06-13,06-14) |  |  |  |
| s1_total_0609 | INHULETS_VALLEY_rect | S1 total dark water, 06-09 (incl. pre-breach water) | 67.6 | observed_S1 | total_water | snapshot_2023-06-09 |  |  |  |
| pre_breach_water | INHULETS_VALLEY_rect | pre-breach water (S1 06-01/02 or p60 pre_water_frac >= 20 %) | 91.0 | observed_S1 | reference_water | reference_2023-06-01/02 |  |  |  |
| s1_new_0609 | P42_FLOODPLAIN_DOMAIN | S1 new dark water, 06-09 scene | 202.9 | observed_S1 | new_water (pre-breach water excluded) | snapshot_2023-06-09 |  |  |  |
| s1_label_recipe | P42_FLOODPLAIN_DOMAIN | S1 new dark water, >= 2 of 3 peak dates (label recipe) | 148.2 | observed_S1 | new_water (pre-breach water excluded) | persistence_2of3_(06-09,06-13,06-14) |  |  |  |
| s1_total_0609 | P42_FLOODPLAIN_DOMAIN | S1 total dark water, 06-09 (incl. pre-breach water) | 329.6 | observed_S1 | total_water | snapshot_2023-06-09 |  |  |  |
| pre_breach_water | P42_FLOODPLAIN_DOMAIN | pre-breach water (S1 06-01/02 or p60 pre_water_frac >= 20 %) | 153.0 | observed_S1 | reference_water | reference_2023-06-01/02 |  |  |  |
| u2b_v004_s20260923 | ALL_B1uB2 | U2b predicted flood (p92 accounting; v004 labels (canonical) | 388.6 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 211.2 |  |  |
| u2b_v004_s20260923 | DNIPRO_CORRIDOR | U2b predicted flood (p92 accounting; v004 labels (canonical) | 352.5 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 209.6 |  |  |
| u2b_v004_s20260923 | CUT_RECTS_total | U2b predicted flood (p92 accounting; v004 labels (canonical) | 36.1 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 1.6 |  |  |
| u2b_v004_s20260923 | INHULETS_VALLEY_rect | U2b predicted flood (p92 accounting; v004 labels (canonical) | 33.5 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 0.0 |  |  |
| u2b_v004_s20260923 | WEST_OF_MOUTH_rect | U2b predicted flood (p92 accounting; v004 labels (canonical) | 2.6 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 1.6 |  |  |
| u2b_v004_s20260923 | TERRACE_NE_rect | U2b predicted flood (p92 accounting; v004 labels (canonical) | 0.0 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 0.0 |  |  |
| u2b_v004_s20260923 | P42_FLOODPLAIN_DOMAIN | U2b predicted flood (p92 accounting; v004 labels (canonical) | 212.5 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 0.0 |  |  |
| u2b_v004_s20260923 | DNIPRO_CORRIDOR_outside_p42_domain | U2b predicted flood (p92 accounting; v004 labels (canonical) | 140.0 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 209.6 |  |  |
| u2b_v004_s20261001 | ALL_B1uB2 | U2b predicted flood (p92 accounting; v004 labels (canonical) | 337.9 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 211.2 |  |  |
| u2b_v004_s20261001 | DNIPRO_CORRIDOR | U2b predicted flood (p92 accounting; v004 labels (canonical) | 297.4 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 209.6 |  |  |
| u2b_v004_s20261001 | CUT_RECTS_total | U2b predicted flood (p92 accounting; v004 labels (canonical) | 40.5 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 1.6 |  |  |
| u2b_v004_s20261001 | INHULETS_VALLEY_rect | U2b predicted flood (p92 accounting; v004 labels (canonical) | 35.7 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 0.0 |  |  |
| u2b_v004_s20261001 | WEST_OF_MOUTH_rect | U2b predicted flood (p92 accounting; v004 labels (canonical) | 4.8 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 1.6 |  |  |

## 5. Discussion

Discrete EO acquisitions undersample the event hydrograph: the reconstructed areal maximum (8 June in
53% of the worlds, 7 June in
38%) lies between the Sentinel-1 acquisitions of
6 and 9 June. In most worlds it coincides with the day of the peak stage at Kherson (8 June; Lehnigk et al. 2026 report downstream
peak stages by 8 June from the same SWOT data), but not in all: maximum extent and maximum stage are different quantities whose timing
changes along a 100 km reach — floodplain storage and drainage produce hysteresis between extent, volume and stage (Fassoni-Andrade
et al. 2023) — and the day of the areal maximum is the most model-dependent number of this paper: on 8 June a water surface a few
decimetres lower disconnects tens of km² of the left bank (T11e, FigS17), which is why the two days share the maximum across the
worlds. It is where the water-surface-constrained reconstruction adds what no acquisition can give, and where Paper 5's hydraulic
model will be tested. The reservoir makes the same
point from the other side: in the first week the pool lost most of its volume while keeping most of its area, and the area collapse
that a satellite mask would call "the drawdown" came a week later (§4.1.3).

**Even with SWOT, the step from a water surface to a flood extent is not unique.** Lehnigk et al. (2026) show that hydraulic models
of this flood do not reproduce the observed stages and their timing together, even with corrected bathymetry; here the stages come from the
observations, validated in Paper 1, and what remains uncertain is how they project onto the ground. The coherent Monte-Carlo budget of
the metric errors is narrow — a relative half-width of
8 % of the peak new area — while the structural and
definitional choices are not: whether reed beds below the normal surface are new inundation or submergence, how far a node's height
is carried, how gaps in the node series are bridged, and which water network seeds the connectivity each move the peak area by more
than the interval (§4.2.4). A reconstruction of this kind should therefore be reported with its support classes and structural
sensitivities next to its interval, and read as the extent implied by the observed surface under stated rules rather than as a
measured flood map.

**External consistency is qualitative.** The rapid assessment of UNEP (2023) collects the operational and modelled figures of
this flood: about 620 km² of flooded land on 9 June within a 19 000 km² analysed area (UNOSAT; over 630 km² per MEPNR) falling to
about 40 km² by 3–5 July, a maximum observed extent between 6 and 9 June, an Inhulets flooded by "an inflow of water and
blocking of the river's outflow", culmination depths of 6–10 m on the islands and floodplain between the dam and the Inhulets,
4–6 m from the Inhulets to Kherson and 2–4.5 m from Kherson to the estuary in the DHI MIKE 21 simulation, and 14.4 km³ (72.5 %)
of the reservoir lost by 13 June. Each of these agrees in kind with the reconstruction — the timing of the maximum, the
backwater in the Inhulets (§4.3.1), the depth gradient along the reach (T12e) and the pool volume that fell from
18.8 to 4.2 km³ between 5 and 13 June (T21) — but none
of them validates it: the areas differ in semantics and domain (flooded land in a much larger area against new inundation
relative to a same-rule baseline in a terrain-connectivity domain, §3.1), the simulation is uncalibrated and its recession was
"not correctly simulated" by the authors' own account, and the operational products are preliminary. One external figure is
a warning rather than a check: UK CEH classified less than 2 % (about 871 ha) of the inundated land as cropland, whereas the
superseded all-prewater seeding had placed a single 41 km² (4 100 ha) component of WorldCover cropland on the left-bank terrace
(§4.2.3). Ukrainian officials indicate that the Oleshky Sands National Nature Park, "located well above the Dnipro
floodplain", avoided flooding; the reconstruction places no new water on bare or sparse land there, while cropland and pine
on the sandy terrace below the park are a different question that only the Sentinel-2 image answers.

**Why the reconstruction needs a hydraulic model.** The reconstruction is static (§3.3): gravity is present only implicitly — a cell
floods when its terrain lies below the water surface and a connected path leads to it — and scaling both heights by *g* changes
nothing (*gz* < *gH* exactly when *z* < *H*), so a separate potential or gravity layer would add no information. What it lacks is
dynamics. Flood-fill and bathtub models assume "zero flow resistance and instantaneous water propagation, leading to highly
non-linear relationships between water surface elevation and inundated flood area" (Dale et al. 2026) — the threshold behaviour of
FigS13 and of the Monte-Carlo offset (T11d) — and they "may overestimate floods because they do not capture some of the relevant
underlying hydrodynamic processes that govern flood propagation on land" (Kasmalkar et al. 2024); c-HAND, the closest static analogue
of our operator, over-predicts the inundated area of a hydrodynamic simulation by about 27 % while finding 99 % of its flooded cells
(Wang et al. 2024). The withheld Inhulets gauge measures this limit directly: while the backwater travelled up the tributary, the
reconstructed surface, taken from the main stem, stood above the gauge by +9.50 m on 2023-06-06; the reconstructed
maximum came 3 days before the observed one; and in the recession the reconstruction drained ahead of the
valley (-0.72 m on 2023-06-14 in event-relative terms), so that the close absolute agreement after the peak is a
coincidence of two errors (§4.3.1, FigS15). Adding the gauge as a water-surface node improves the reconstruction (T12, T13) but cannot
give it a clock. Nor can the lighter extensions of the geometric method: path-based attenuation damps depths along the flow paths to
mimic friction and a transient forcing (Kasmalkar et al. 2024), and depression routing such as Fill–Spill–Merge conserves the volume
that fills and spills between depressions (Barnes et al. 2021), but neither resolves time. Propagation, storage, friction and transient
backwater require the continuity and momentum equations — a two-dimensional shallow-water model driven by the water-surface gradient
over the corridor, the delta and the Inhulets valley, with the Dnipro stage at the confluence as the tributary's downstream boundary,
since backwater at confluences controls tributary stage and flood-wave timing (De Paiva et al. 2013), and with the liman stage at
Mykolaiv as the boundary that the western delta now lacks (§4.3.1). Such models of this event improve with corrected reservoir and channel bathymetry but still reproduce neither the peak stage nor
its timing together (Lehnigk et al. 2026), so they cannot replace the
observation-constrained reconstruction — and the reconstruction cannot replace them. The daily reconstructed extents and volumes with
their support classes, the SWOT water-surface profiles, the Sentinel-1 dates and the two withheld gauges are the calibration and
validation targets of the hydraulic model of Paper 5, and the hydraulic model is what can give the reconstructed daily states their
timing.

**The disagreement map is the product.** The dark-water rule counts water it can see on the day it looks; the label contract counts
water that persisted over three peak dates and therefore describes the recession, not the areal maximum; the reconstruction counts
ground the observed water surface can reach. Their disagreement on 9 June is not noise: it falls into surfaces the radar cannot see
(forest, buildings, emergent reeds), reed beds that were already at the water level in the normal regime and became dark only when
submerged, and dark fields far above any water surface of the event, which are topographically unsupported by the reconstruction and
for which the independent altimetry gives no evidence of a terrain error large enough to explain them. Operational SAR flood services
have reached the same conclusion from the sensor side: exclusion maps derived from C-band time series mark where flood cannot be
inferred from intensity (Zhao et al. 2021), the Copernicus EMS ensemble delivers "an exclusion mask indicating the regions where the
detection is prevented" next to its flood layer (Amitrano et al. 2024), and the Sentinel-1 data-cube architecture behind the Global
Flood Monitoring service was designed to carry "masks showing where Sentinel-1 cannot detect floods due to physical reasons" (Wagner
et al. 2020). What the terrain reconstruction adds to such masks is the other half of the picture — where the radar reports water that
the observed water surface cannot reach — and, through ICESat-2, a test of whether the terrain itself is at fault there.

**Weak-label models are diagnostics of their labels.** Correcting the threshold calibration of the optical component and removing its
post-event features changed the labels only at their margins (§4.4.2), yet retraining with three seeds changed which conclusions
survive: the label treatment of reference water moves the learned representation consistently, whereas the reduction of the cropland
burden that a single seed had attributed to HAND did not reproduce. HAND therefore should not be interpreted as independently
demonstrated to suppress cropland false positives. Land cover as an input raised the cropland burden rather than vetoing it, and the
pre-event water input improves agreement only with labels that already contain it. How terrain enters a model matters as well: with
HAND as a Bayesian prior rather than an input channel, Tupas et al. (2023) reduced false negatives "at the cost of slightly increasing
false positives". Every one of these statements is agreement with weak labels on a frozen spatial split — labels of the kind that the
flood-mapping literature now trains on routinely (Sentinel-1/2 threshold classifications as weak labels: Bonafilia et al. 2020;
Katiyar et al. 2021; Sharma et al. 2025) and whose errors a model "still ends up learning" (Garg et al. 2023) — and single-seed
differences of the size reported earlier lie within the training noise (§4.4.3). The mapped U-Net area, a persistence quantity, is not
an estimate of the reconstructed newly inundated area (§4.4.6).

**The reservoir balance is context.** It is a daily-mean effective release from a sloped surface between three or four level points on
a terrain model whose hypsometry sits below the design table; Paper 4 will rebuild the bowl on the historical bathymetry before that
balance can be more than an order-of-magnitude check against the published breach-flow estimates.

## 6. Limitations

A daily reconstructed series, not daily observations: between observation days the values are interpolation and model. A static
reconstruction: as in other static equilibrium terrain-connectivity approaches (Wang et al. 2024; Dale et al. 2026), it does not solve
momentum or continuity equations and therefore does not simulate finite propagation time, frictional losses, transient storage or
backwater dynamics, and its water surface is planar per node neighbourhood — the withheld gauges show where this matters (§5). The
vertical frame is taken from Paper 1 and not re-validated here; the terrain model of Paper 2 had been converted with the tide-free
closure paired with the permanent-tide term, and its FABDEM part and the ICESat-2 ground heights are raised by
0.038 m to the production chain of Paper 1 (§3.2); Paper 2 should carry the same
correction. A residual terrain error of the FABDEM DTM under reeds, trees and buildings (under trees a class median of
+1.7 m and an NMAD of 1.7 m, T18b), no stochastic
term on the surveyed bed, and a class bias in the delta that depends on the epoch of the passes (T15c) and is not propagated. SWOT nodes
on channels only, with the gauge cap beyond 15 km and the nearest-node fallback — structural choices outside the Monte-Carlo, to which
the delta on 9–13 June is sensitive (§4.2.4) and which leave the upper Inhulets valley weakly constrained; the westernmost SWOT node of
the delta has no observation from 2023-06-06 .. 2023-06-22. The event inundation boundary across the vegetated wetland complex was reproduced well, whereas the pre-event hydrological state
beneath emergent vegetation remained uncertain; consequently the uncertainty affects the attribution of the inundated wetland area to
newly flooded versus seasonally wet conditions, rather than the reconstructed event footprint itself (§4.1.1, T12h, T12hb). No
full-coverage satellite scene on the day of the
reconstructed areal maximum; the date-only gauge against 11:00 UTC SWOT passes. Weak labels whose positives are a persistence product,
whose optical component is trained on Sentinel-1-derived labels, three training seeds per arm, test blocks read at several stages
(exploratory comparisons), the W_pre circularity of U2b, and one event (no transfer to another flood). The primary rule has no
storage memory: water that entered a depression while connected is dropped on the day the connection is lost (the memory
variant keeps it, as a sensitivity, T11p); and the seed network is the largest connected component of a 20 m pre-breach water
map, so a water body linked to the river only by a channel narrower than the grid is a source only once the flood itself
connects it. The residual terrain correction is a class median: along the audited path it over-corrects the floodplain forest and
wetland by 0.4–0.6 m and under-corrects the lowland grass by 1–1.5 m (T15h, T15i), so local depths and volumes carry a bias of
that order that the Monte-Carlo terrain term represents only as random error; a track-based local calibration of the residual
against ICESat-2 is the terrain improvement this audit points to. Frame B3 (delta with the liman)
not built; no probability-sample reference for any area; the UNOSAT product sheets behind the ~620 km² and ~180 km² figures were
read (products 3616 and 3623), and both remain preliminary analyses not validated in the field. The reservoir balance rests on three to four level points, an upper
bound at Nikopol on 12–13 June and a terrain hypsometry below the design table; the pool model ends on 13 June, and the later emptying
is observed by Sentinel-2 only; the Sentinel-1 dark surface over the drained bed is not a water area. The S1-only detections above
the surface are shown to be topographically unsupported, not attributed to a cause.

## 7. Conclusions

1. *Reconstruction.* The observed water surface, taken from the validated vertical frame of Paper 1 and projected on a bias-corrected
   seamless terrain model with connectivity and a same-rule baseline, gives a daily reconstructed extent, depth and volume for the
   Kakhovka flood: on 7 June, 146 km²
   (132–166 km²) of land classified as dry
   before the breach was newly inundated in the Dnipro corridor, between the available acquisitions, and the inundation receded within
   two weeks; separately, the inundated area within the vegetated wetland complex increased by
   114 km² (93–135 km²),
   a quantity that depends on the reconstructed pre-event state; the aggregate under the former state definition,
   234 km², is not their sum; above the dam the pool lost most of its volume in the first week and most of its area in the second, and most of the
   released water was transmitted downstream rather than stored on the mapped floodplain.
2. *Uncertainty.* The coherent Monte-Carlo interval is narrow
   (132–166 km² for the new inundation of
   dry ground on 7 June); the structural and definitional choices — the support of the water surface, the handling of gaps, the reed beds — are
   larger and are reported as such, with the support class of every newly inundated cell; the nominal run is a diagnostic.
3. *Independent validation.* The withheld gauges show where a static reconstruction fails — a tributary backwater running metres above
   the gauge and peaking three days early, and a western delta without an observed surface; Sentinel-1 agrees where it can see, and
   its disagreement with the reconstruction is mechanistic — radar blind spots, submerged reed beds and topographically unsupported
   detections for which ICESat-2 finds no terrain bias large enough.
4. *Weak-label machine learning.* U-Net arms trained on the canonical weak labels are diagnostics of those labels: the treatment of
   reference water changes what they learn consistently across seeds, the earlier HAND effect did not reproduce, and no model number
   is flood-mapping accuracy.

The claims register (`claims.md`, C01–C14) names the evidence class, table cells, uncertainty and limitation of each claim. The next
steps are the reservoir bowl on the historical bathymetry (Paper 4) and a two-dimensional hydraulic model calibrated on these daily
surfaces (Paper 5).

## Data and code availability

Code, tables, figures, notebooks and the dashboard: https://github.com/NikoriakViktot/floodstate-eo (package version 0.3.0rc2; the
release tag and the Zenodo DOI are minted from the release); interactive dashboard: https://floodstate-eo.streamlit.app. One command per
reproducibility level (`docs/REPRODUCIBILITY.md`, `workflows/paper/rebuild.py`), a tiny open geodomain that runs the reconstruction and
Monte-Carlo chain on synthetic inputs (`examples/tiny_geodomain`), a manifest of the load-bearing inputs with sha256
(`manifests/load_bearing_inputs.csv`) and an environment lock (`requirements-lock.txt`). The full Monte-Carlo draw tables are release
assets (checksums in `tables/p95e_draws_checksums.csv`). The changes made after the scientific and code review of 28 September 2026 —
old and new value, reason and effect on the conclusions — are listed in table T28. The vertical reference framework is that of Paper 1
(release paper1-v6 of https://github.com/NikoriakViktot/SWOT-DNIPRO). Processed rasters (≈ 100 GB) are documented in
`docs/REPRODUCIBILITY.md`; FABDEM-derived rasters are not redistributed (CC BY-NC-SA 4.0). SWOT (PO.DAAC), ICESat-2 (NSIDC), Sentinel
(Copernicus) and WorldCover (ESA) are open archives; gauge data from the UkrHMC yearbooks as in Paper 1.

## References

`docs/references.bib`; entries added for this paper carry `note = {VERIFY}` until checked (`references_to_verify.md`).
