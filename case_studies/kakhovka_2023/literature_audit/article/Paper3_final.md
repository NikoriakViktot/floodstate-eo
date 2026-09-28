<!-- Paper3_final.md — assembled 2026-09-28 by tools/paper3_audit/final_article.py: floodstate-eo bundle 21ba34c (manuscript.md filled from publication/tables by fill_manuscript.py) + 36 literature-audit revisions (10_change_log.md) + 4 final-assembly edits (FA-*); figures from publication/figures, tables from publication/tables, references from 07/07c and corpus records. -->

# Daily inundation after the Kakhovka dam breach reconstructed from the observed water surface and terrain, checked against Sentinel-1 and ICESat-2, and what EO-based flood products recover under weak labels

## Abstract

**Background.** On 6 June 2023 the Kakhovka dam on the lower Dnipro was breached and the reservoir drained within days. The
flood below the dam has been described mainly from satellite water masks, whose areas depend on the sensor, the date and the
definition of "flooded". Paper 1 of this series established one vertical frame for the gauges, ICESat-2 and SWOT; Paper 2 a
seamless terrain model. Here we ask what that water-surface geometry, projected on the terrain, says about the inundation on
every day of the event — a daily reconstructed series constrained by the observations, including the areal maximum that
no satellite image covers — and how far Sentinel-1 flood observations and U-Net flood products recover it.

**Methods.** The daily water surface is built from SWOT L2_HR_RiverSP node heights (EGG2015-referenced, shifted by the
Kherson-local closure residual of Paper 1) and the Kherson gauge, without an along-channel chainage; it is projected on the
seamless DEM, corrected for its class-median bias against ICESat-2, with a connectivity rule and a same-rule pre-breach
baseline, so that the *reconstructed newly inundated area* is water on ground that was not water in the normal regime and the
*reconstructed total water-surface area* is all water on the day. This is an observation-constrained terrain inundation
reconstruction, not a hydrodynamic model: no momentum or continuity equations are solved, and values between observation days
are reconstructed, not observed. A spatial Monte-Carlo budget (40 draws, the primary interval) propagates closure, gauge, SWOT,
interpolation and spatially correlated class-wise DEM errors; a 100 000-draw emulator gives a broader sensitivity envelope. Sentinel-1 dark-water masks on 11 dates, the
disagreement between them and the reconstruction decomposed by surface class and elevation, and night ICESat-2 ground
heights are used as checks. RF20 surface classes supply the context; U-Net arms trained on two frozen weak-label contracts on a
frozen spatial-block split show what EO inputs recover.

**Results.** In the Dnipro corridor (Inhulets excluded) the reconstructed newly inundated area reaches its maximum of
247 km² on 7 June 2023 (Monte-Carlo median; primary p05–p95
238–255 km²; deterministic nominal run 235 km²), between the Sentinel-1 acquisitions of 6 June (partial)
and 9 June, one day before the peak stage at Kherson (5.78 m on 8 June in the river yearbook; the sources differ by ~0.1 m, §4.1); with the DEM as
delivered, i.e. with the reed beds counted as new, the nominal run gives 347 km² (against 235 km² nominal). The
reconstructed total water-surface area rises from 488 km² in the pre-breach regime (5 June)
to 790 km² on 7 June (median; p05–p95 781–799 km²; nominal run 779 km²),
with a further 68 km² in the Inhulets valley; the
reconstructed new-water volume is 566 hm³ (median; p05–p95 545–596 hm³; nominal run 509 hm³).
Reported central values are Monte-Carlo medians: on the peak days the deterministic nominal run lies below its own p05.
The newly inundated area falls to 118 km² on 13 June and 3 km² on 21 June.
On 9 June, inside the terrain-eligible floodplain, the raw agreement with Sentinel-1 new dark water is low
(POD 0.26, FAR 0.62) and strongly conditioned by surface type:
173 km² of Sentinel-1 "new water" lies on normally-wet reed beds below
the pre-breach surface (a submergence signal, not inundation onset); 54 km²
lies ≥ 5 m above the reconstructed surface and is topographically unsupported by the connected water surface, and along the
night ICESat-2 tracks that sample it the DEM agrees with the altimetry to a few centimetres in the median (with a
p10–p90 spread of a few decimetres), so the available ICESat-2 observations give no evidence for a DEM bias large
enough to explain it — an altimetric consistency check along tracks, not a validation of the map;
 120 km² allowed
by the terrain is invisible to the dark-water rule, 43 km² of it under trees and
23 km² in built-up areas. Changing the weak-label contract from v002 to
v003_A at fixed inputs changed the U-Net flood on reference water on the test blocks by
-13.4 km²
(95 % block bootstrap -29.5 to
-2.5) with no statistically resolved change in
event-flood recall.

**Conclusions.** Discrete EO acquisitions undersample the event: the reconstructed areal maximum falls between them. The
observed_S1 flood of a SAR mask, the mapped_UNet persistent flood and the terrain-reconstructed newly inundated and total
water-surface areas are different quantities. The reconstruction gives the day-by-day extent, depth and volume that the
observations cannot, with a stated primary interval, and the observations show where the reconstruction and the sensors are blind. We report every area
with its semantics and every model number as agreement with weak reference labels, not as flood-mapping accuracy.

**Keywords:** dam breach; inundation dynamics; SWOT; ICESat-2; Sentinel-1; HAND; weak supervision; U-Net; Kakhovka

## 1. Introduction

The destruction of the Kakhovka dam on 6 June 2023 released the largest reservoir of the Dnipro cascade — 18.2 km³ at its
normal retention level of 16.0 m, 19.8 km³ at the 16.76 m held on the eve of the breach (Vyshnevskyi et al. 2023) — into
a ~90 km reach with a densely populated left bank, a reed-wetland delta and the Dnipro–Buh liman (Vyshnevskyi et al. 2023;
Shumilova et al. 2025). Within days operational products reported the flooded *land*: about 620 km² over 6–9 June and about
180 km² on 13 June in the UNOSAT products relayed by OCHA (CEOBS 2023), figures that later studies cite (Yailymov et al.
2025). The published studies of the event are of three kinds. Satellite mappings give areas with their own definitions:
Yailymov et al. (2025) map 473 km² of flooded land as of 9 June by land-cover class, 294 km² of it wetlands, against a
pre-flood water map of 5 June; Zuo et al. (2024) follow the water-surface area at 300 m in Sentinel-3 OLCI scenes, which
doubled within three days and was largest around 9 June; Monti et al. (2024) map the flooding along ~80 km of river with
Sentinel-1 change detection; Jiao et al. (2025) use the event to test a Sentinel-1 flood-extraction method. Hydrodynamic
models give scenario extents and stages: Kadam et al. (2024) obtain 823 km² and a peak of 3.6 × 10⁴ m³ s⁻¹ for a 300 m
breach in HEC-RAS; Agerbeek et al. (2024) ran a near-real-time model checked against ICEYE extents and geolocated
photographs; and Lehnigk et al. (2026) show with the daily SWOT water-surface elevations of the one-day calibration orbit
— the data we use here — that two-dimensional outburst-flood simulations underestimate the observed peak stages by 1.4 to
6.1 m and misplace their timing unless reservoir and channel bathymetry are corrected, and even then reproduce neither
stage nor timing fully; downstream stages reached 10–11 m by 8 June. Reservoir-side balances give the volume released:
Yi et al. (2025) derive an initial breach flow of (5.7 ± 0.8) × 10⁴ m³ s⁻¹ and 20.4 ± 1.4 km³ lost in 30 days from
gravimetry, altimetry and imagery; Shumilova et al. (2025) model about 16.4 km³ over two weeks. What none of these gives is
a description of the inundation that depends neither on which sensor happened to look on which day nor on a hydrodynamic
model whose bathymetry is unknown: an extent, a depth and a volume for every day, tied to the observed water surface, with
an uncertainty, and an account of where the satellite flood masks and such a reconstruction disagree and why.
Terrain-based approaches that project a water surface or a mapped extent on a DEM — HAND (Rennó et al. 2008; Nobre et al.
2011), GeoFlood (Zheng et al. 2018), FwDET (Cohen et al. 2019) — are first-order products, not hydrodynamics: Johnson et
al. (2019) find that a HAND-based method "does not accurately capture inundated cells" while it does highlight regions at
risk. Their depth and extent are sensitive to small vertical errors on low-relief floodplains, and because DEM error is
spatially autocorrelated whereas accuracy statistics such as RMSE "assume error to [be] aspatial" (Hawker et al. 2018), it
must be propagated with spatially correlated error realisations (Darnell et al. 2008; Le et al. 2026), not with
independent noise.

Two well-known properties of satellite flood mapping make this necessary. The area obtained by counting classified pixels is a
*mapped* area, not an unbiased estimate of the true flooded area; the good-practice framework of Olofsson et al. (2014)
requires an accuracy assessment "based on a sample of higher quality" reference data, which does not exist for this event.
And a C-band dark-water rule does not see water under trees, between buildings or under emergent reeds: the backscatter of
vegetated and urban targets with and without flood water "represents the biggest challenge for inundation detection"
(Grimaldi et al. 2020), flood water under vegetation "could not be detected with the C-band Sentinel-1 SAR" in a paddy
landscape (Singha et al. 2020), and detection beneath vegetation and in cities is "not yet satisfactory" (Shen et al. 2019;
review of flooded vegetation in SAR: Tsyganskaya et al. 2018). Conversely, "smooth surfaces at the scale of the measuring
wavelength and shadowed areas share almost identical scattering properties with water surfaces" (Shen et al. 2019) and
sand returns backscatter as low as open water (Martinis et al. 2018), so smooth non-water surfaces and radar shadow can
look like water; exclusion maps derived from SAR time series formalise where flood cannot be inferred from intensity
(Zhao et al. 2021).
 A U-Net trained on labels derived
from those masks inherits both limits (Maiti et al. 2022; weak supervision for flood mapping: He et al. 2024); its accuracy against such labels is agreement, not
truth, and an input that also builds the label is label leakage (Apicella et al. 2025). We therefore structure the study
as a hierarchy of evidence (Fig02): an **observation-constrained terrain inundation reconstruction** of the daily inundation
from the gauge-constrained, SWOT-supported water-surface geometry and terrain connectivity — a daily reconstructed series, not
a hydrodynamic model — is the main axis; **independent and cross-sensor
observations** (Sentinel-1 per acquisition date, night ICESat-2 ground heights, the SWOT–gauge comparison of Paper 1) check
it; the **surface context** (RF20 land-cover classes, WorldCover, elevation above the surface) explains the disagreements;
and controlled **U-Net experiments** under two frozen weak-label contracts show what EO inputs recover. Three principles hold
throughout: model numbers are agreement with weak reference labels, never flood-mapping accuracy; "not observed is not dry";
and every area carries its semantics — observed by Sentinel-1, mapped by the U-Net, reconstructed from terrain, or reported
in the literature.

![Fig02](figures/Fig02_evidence_hierarchy.png)

**Fig02. Evidence hierarchy.** The observation-constrained terrain inundation reconstruction (gauge-anchored SWOT water surface × terrain connectivity; no momentum or continuity equations) is the main axis; Sentinel-1 per date, ICESat-2 and the SWOT–gauge comparison check it; the RF20 surface classes and the elevation above the surface explain the disagreements; the U-Net arms show what EO inputs recover under weak labels.

This is Paper 3 of a series. Paper 1 reduced seven gauges, ICESat-2 ATL13 and SWOT to one local vertical frame and
measured the post-breach water-surface slopes; Paper 2 built the seamless terrain model (bathymetric bed and FABDEM, EVRF2019)
and assessed it against night ICESat-2 ground heights by land-cover class; Paper 4 will reconstruct the reservoir bowl on the historical (pre-impoundment and
design-survey) bathymetry, resolving the hypsometry gap reported in §4.1; Paper 5 will use the daily surfaces presented here
as the calibration target of a two-dimensional hydraulic model. We inherit the vertical conventions of Paper 1 without re-validating them: satellite heights
are EGG2015-referenced heights shifted by the empirical local closure residual into the gauge-anchored frame, the sign of a
residual is gauge − satellite, and one overpass or one day is the independent unit.

## 2. Study area and data

The study reach runs from the Kakhovka dam (46.78° N, 33.37° E) to the Dnipro–Buh liman (Fig01). Two frames on one 10 m lattice
carry the EO products: B1 (dam → Kherson) and B2 (Kherson delta); the terrain reconstruction runs on the 20 m zone grids of
Paper 2 (ZONE_4 dam-to-Kherson floodway, ZONE_2 Kherson delta), with the delta owning the overlap. The Inhulets tributary
joins from the north with its own regime and is reported separately; the cut rectangles that isolate its valley and the
terrace fragments were fixed in Paper 2 before any result of this paper existed. Table T01 lists every dataset with its
role and evidence level:

![Fig01](figures/Fig01_study_area.png)

**Fig01. Study area.** Lower Dnipro from the Kakhovka dam to the Dnipro–Buh liman: hillshade of the seamless DEM (Paper 2), terrain below 1 m (channels, lakes), frames B1 (dam → Kherson) and B2 (Kherson delta) on one 10 m lattice, the p42 terrain-eligible floodplain, the cut rectangles that separate the Inhulets valley and the terraces from the Dnipro reach, SWOT RiverSP nodes (main stem vs tributaries and side channels), the Kherson gauge 80805 and the dam.

**T01.** Data inventory: acquisition dates, coverage of the Sentinel-1 observable domain, and the role of every dataset.
*Evidence level: mixed.*

| dataset | date | detail | coverage_of_observable_domain | evidence_level |
|---|---|---|---|---|
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-01 | orb65_DES | 1 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-02 | orb87_ASC | 0.951 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-06 | orb138_DES | 0.619 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-09 | orb14_ASC | 0.938 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-13 | orb65_DES | 1 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-14 | orb87_ASC | 0.951 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-18 | orb138_DES | 0.618 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-21 | orb14_ASC | 0.937 | cross_sensor |
| Sentinel-1 GRD/RTC, dark-water mask (M3) | 2023-06-25 | orb65_DES | 1 | cross_sensor |
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
| SWOT L2_HR_RiverSP v2.0 nodes (1-day orbit), accepted | 2023-05-26..2023-07-10 | 42 days, 732 nodes/day median | nan | independent_physical |
| Kherson gauge 80805 (river yearbook), daily | 2023-05-25..2023-07-10 | 47 days; BS77 -> EVRF2019 +0.22 m; 6-12 June flagged in the sea yearbook (Paper 1) | nan | independent_physical |
| S1 reference scenes 2023-04-15..05-28 (May reference water, p89b/p89c) | 2023-04-15..2023-05-28 | 30 admitted of 30 scenes (variant A QA) | nan | cross_sensor |
| Seamless DEM (p55): bathymetric bed + FABDEM v1.2, EVRF2019, 20 m | 2019-2022 bed; FABDEM 2011-2015 epoch | Paper 2 | nan | independent_physical |
| ICESat-2 ATL08 night ground segments (p57 chain) | 2019-2025 | altimetric consistency check (Paper 2 chain) | nan | independent_physical |
| ESA WorldCover 2021 v200, 10 m | 2021 | RF20 training reference and decomposition classes | nan | contextual |

- **Sentinel-1** (Torres et al. 2012) GRD, radiometrically terrain-corrected (Small 2011), eleven acquisitions 1–30 June 2023 (orbits 14, 65, 87, 138), per-scene dark-water masks (M3 rule of
  Paper 1's water classifier, 20 m); orbit-138 dates cover 62 % of the observable domain. Orbit-matched dB change channels (p71)
  are the U-Net inputs. A second set of thirteen reference scenes (15 April–28 May 2023) defines recurrent May water.
- **Sentinel-2** L2A scenes (Sen2Cor processing, Main-Knorn et al. 2017) as index stacks per date at 10 m — NDWI (McFeeters
  1996), MNDWI (Xu 2006), NDVI (Tucker 1979), NDMI (Gao 1996), BSI (Rikimaru et al. 2002, Tropical Ecology 43, 39–47),
  AWEIsh (Feyisa et al. 2014) and the turbidity index NDTI (Lacaux et al. 2007) — and PRE/EVENT/TRACE composites.
- **SWOT** L2_HR_RiverSP v2.0 nodes on the one-day calibration orbit (Biancamaria et al. 2016), 26 May–10 July 2023, 42 days,
  732 nodes/day median; node_q ≤ 1 and dark fraction < 0.5 as in Paper 1. Published comparisons place SWOT river heights at
  the centimetre-to-decimetre level against gauges and altimetric references (RMSE 0.02 m against Hydroweb-next on the
  Congo, Normandin et al. 2024; a global river error below 0.15 m, Yu et al. 2024), which is why the product's own node
  uncertainty wse_u (median 0.092 m here) is used as the per-node term of the Monte-Carlo (§3.3).
- **Kherson gauge 80805**, daily, river yearbook, BS-77 → EVRF2019 by the official EPSG:9902 operation (+0.216 m at the post);
  6–12 June are flagged in the sea yearbook (recorder failure) and the river-yearbook values are used, as in Paper 1 §5.12.
- **Seamless DEM** (Paper 2): kriged bathymetric bed inside the pre-breach water polygons, FABDEM v1.2 elsewhere (a Copernicus
  DEM with buildings and forests removed by machine learning, Hawker et al. 2022; residual mean absolute errors of 1.1–1.6 m
  remain in built-up areas, Iqbal et al. 2023), EVRF2019, 20 m. Global DEMs carry a positive canopy bias on vegetated
  floodplains that has to be removed before inundation modelling (Baugh et al. 2013; Yamazaki et al. 2019), which is why
  the class-median residual against ICESat-2 is subtracted (§3.2);
  HAND from the p42 workflow (FABDEM floored at the 1 m river level, WhiteboxTools). Night ICESat-2 ATL08 ground segments
  (2019–2025, Paper 2 chain) give its accuracy by land-cover class (T18; robust statistics after Höhle and Höhle 2009): RMSE
  1.04 m, NMAD
  0.39 m over
  841752 segments, with trees the worst class.
- **ESA WorldCover 2021** (10 m): the training reference of the RF20 surface classes and the classes of the disagreement ontology.

**T18.** Seamless DEM accuracy against night ICESat-2 ground segments (Paper 2): RMSE, MAE, bias, median, LE90, LE95, NMAD by zone and WorldCover class; the class rows feed the DEM error model of T11b.
*Evidence level: independent_physical.*

| set | N | RMSE | MAE | bias | median | LE90 | LE95 | NMAD | product | zone | source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C seamless DEM (p55) -- ALL night points (land below dam + exposed bed) | 841752 | 1.044 | 0.495 | 0.266 | 0.085 | 1.033 | 1.773 | 0.39 | C | nan | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_2_KHERSON_DELTA | 153342 | 1.11 | 0.458 | 0.199 | -0.002 | 0.982 | 1.655 | 0.299 | C | ZONE_2_KHERSON_DELTA | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover trees | 8066 | 3.024 | 2.085 | 1.952 | 1.481 | 4.741 | 6.169 | 1.603 | C | ZONE_2_KHERSON_DELTA | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover grass | 29227 | 1.329 | 0.653 | 0.372 | 0.107 | 1.422 | 2.22 | 0.491 | C | ZONE_2_KHERSON_DELTA | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover cropland | 95454 | 0.408 | 0.198 | -0.035 | -0.059 | 0.404 | 0.537 | 0.195 | C | ZONE_2_KHERSON_DELTA | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover built | 7850 | 1.901 | 0.818 | 0.252 | 0.151 | 1.764 | 2.581 | 0.696 | C | ZONE_2_KHERSON_DELTA | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover bare | 287 | 3.375 | 1.969 | -0.819 | -0.574 | 4.621 | 9.297 | 1.188 | C | ZONE_2_KHERSON_DELTA | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_2_KHERSON_DELTA, WorldCover wetland | 12409 | 1.131 | 0.675 | 0.437 | 0.509 | 1.244 | 1.552 | 0.477 | C | ZONE_2_KHERSON_DELTA | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY | 476545 | 1.125 | 0.551 | 0.408 | 0.225 | 1.153 | 2.017 | 0.385 | C | ZONE_4_DAM_TO_KHERSON_FLOODWAY | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover trees | 30020 | 2.929 | 2.19 | 2.079 | 1.693 | 4.639 | 5.791 | 1.715 | C | ZONE_4_DAM_TO_KHERSON_FLOODWAY | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover grass | 98908 | 1.524 | 0.85 | 0.676 | 0.385 | 1.867 | 2.784 | 0.622 | C | ZONE_4_DAM_TO_KHERSON_FLOODWAY | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover cropland | 307176 | 0.363 | 0.268 | 0.157 | 0.151 | 0.54 | 0.672 | 0.296 | C | ZONE_4_DAM_TO_KHERSON_FLOODWAY | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover built | 15288 | 1.517 | 0.691 | 0.227 | 0.17 | 1.47 | 2.09 | 0.597 | C | ZONE_4_DAM_TO_KHERSON_FLOODWAY | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover bare | 3525 | 1.42 | 0.903 | 0.309 | 0.307 | 1.852 | 2.388 | 0.935 | C | ZONE_4_DAM_TO_KHERSON_FLOODWAY | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, ZONE_4_DAM_TO_KHERSON_FLOODWAY, WorldCover wetland | 21543 | 1.239 | 0.764 | 0.577 | 0.584 | 1.304 | 1.729 | 0.416 | C | ZONE_4_DAM_TO_KHERSON_FLOODWAY | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |
| C seamless, low terrain (< 5 m) incl. exposed bed | 81853 | 0.862 | 0.635 | 0.357 | 0.344 | 1.367 | 1.782 | 0.686 | C | nan | Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here |

## 3. Methods

### 3.1 Daily water surface

For every node we take H = wse + geoid_hght − ζ_EGG2015 + c_Kherson, where wse and geoid_hght are the SWOT product fields, ζ the
EGG2015 quasigeoid and c_Kherson the local closure residual, which Paper 1 measured as a few centimetres at Kherson
(+0.9 cm RiverSP, −2.6 cm PIXC before the breach; +1.9 cm through the breach fortnight; NMAD 4–5 cm); we use c = 0.00 m with
σ = 0.05 m. An earlier chain (p59) had applied the mean reservoir closure (−0.173 m) and a permanent-tide term to the downstream
reach; the resulting −0.21 m offset is recorded as a superseded sensitivity (T11). The SWORD chainage distributed with the
nodes is not comparable across branches (the Inhulets reaches, the Kokan' channel and the side channels at Kherson start
their own counts), so the water surface is built without chainage: each cell takes the median height of its five nearest
nodes within 3 km on the day, each node is interpolated in time between its own observations, the gauge enters as one more
node at its coordinates, and cells farther than 15 km from any node and west of the gauge are capped at the gauge level.
After re-anchoring, the daily median of the nodes within 3 km of the gauge differs from the gauge by
+0.01 m (NMAD 0.07 m, RMSE 0.06 m,
n = 36 days; T17, Fig06) — an input-consistency check; the frame validation is Paper 1.

![Fig06](figures/Fig06_water_surface.png)

**Fig06. Water surface.** (a) Observed SWOT node medians per 1 km of straight-line distance from the dam (main stem), gauge-anchored EGG2015-referenced heights; the reconstruction itself is node-based (no chainage). (b) Daily median of the SWOT nodes within 3 km of the Kherson gauge against the gauge after re-anchoring to the Kherson-local closure of Paper 1. (c) Residuals gauge − SWOT (T17).

**T11.** Terrain reconstruction: rules, closure, constants and the water-surface method per variant. The superseded closure row is kept for traceability.
*Evidence level: independent_physical.*

| variant | suffix | rule | closure | closure_offset_vs_p59_m | margin_m | river_floor_m | swot_max_dist_m | dist_to_prewater_max_m | baseline_until | wse_method | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hand_and_ceiling | (default) | hand_and_ceiling | kherson_paper1 | 0.2086 | 0 | 1 | 15000 | 10000 | 2023-06-05 | node-based: median of K=5 nearest SWOT nodes within 3 km, per-node time interpolation, gauge as a node, gauge cap beyond 15 km west of the gauge (rev 4; the p59 chainage is not comparable across SWORD branches) | current |
| ceiling_only | _ceiling_only | ceiling_only | kherson_paper1 | 0.2086 | 0 | 1 | 15000 | 10000 | 2023-06-05 | node-based: median of K=5 nearest SWOT nodes within 3 km, per-node time interpolation, gauge as a node, gauge cap beyond 15 km west of the gauge (rev 4; the p59 chainage is not comparable across SWORD branches) | current |
| connected_ceiling | _connected_ceiling | connected_ceiling | kherson_paper1 | 0.2086 | 0 | 1 | 15000 | 10000 | 2023-06-05 | node-based: median of K=5 nearest SWOT nodes within 3 km, per-node time interpolation, gauge as a node, gauge cap beyond 15 km west of the gauge (rev 4; the p59 chainage is not comparable across SWORD branches) | current |
| connected_ceiling_dem_uncorrected | _connected_ceiling_dem_uncorrected | connected_ceiling | kherson_paper1 | 0.2086 | 0 | 1 | 15000 | 10000 | 2023-06-05 | node-based: median of K=5 nearest SWOT nodes within 3 km, per-node time interpolation, gauge as a node, gauge cap beyond 15 km west of the gauge (rev 4; the p59 chainage is not comparable across SWORD branches) | current |
| connected_ceiling (superseded closure, +0.5 m) | _connected_ceiling_closure_p59_m050 | connected_ceiling | p59_reservoir | 0 | 0.5 | 1 | 15000 | 10000 | 2023-06-05 | node-based: median of K=5 nearest SWOT nodes within 3 km, per-node time interpolation, gauge as a node, gauge cap beyond 15 km west of the gauge (rev 4; the p59 chainage is not comparable across SWORD branches) | superseded |

**T17.** SWOT-input consistency at Kherson after re-anchoring: nodes within 3 km of the gauge, daily median vs the daily gauge (river yearbook, EVRF2019). The frame validation itself is Paper 1; this only checks the p95 input.
*Evidence level: independent_physical.*

| period | n_days | bias_m | median_m | MAE_m | RMSE_m | NMAD_m | min_m | max_m | independent_unit | sign |
|---|---|---|---|---|---|---|---|---|---|---|
| all days | 36 | 0.016 | 0.006 | 0.048 | 0.062 | 0.066 | -0.081 | 0.175 | day (one 11:00 UTC overpass vs a date-only daily gauge value) | gauge - satellite (Paper 1 convention); satellite = EGG2015-referenced SWOT height with c_Kherson = 0 |
| pre-breach 05-26..06-05 | 11 | 0.003 | -0.008 | 0.041 | 0.063 | 0.051 | -0.07 | 0.175 | day (one 11:00 UTC overpass vs a date-only daily gauge value) | gauge - satellite (Paper 1 convention); satellite = EGG2015-referenced SWOT height with c_Kherson = 0 |
| rise and peak 06-06..06-14 | 7 | 0.082 | 0.103 | 0.082 | 0.09 | 0.022 | 0.01 | 0.118 | day (one 11:00 UTC overpass vs a date-only daily gauge value) | gauge - satellite (Paper 1 convention); satellite = EGG2015-referenced SWOT height with c_Kherson = 0 |
| recession 06-15..07-10 | 18 | -0.002 | -0.007 | 0.038 | 0.045 | 0.048 | -0.081 | 0.076 | day (one 11:00 UTC overpass vs a date-only daily gauge value) | gauge - satellite (Paper 1 convention); satellite = EGG2015-referenced SWOT height with c_Kherson = 0 |

### 3.2 Terrain rule, baseline and the definition of "new inundation"

A cell is water on day t if its DEM lies below the water surface and it is 8-connected, through such cells, to the pre-breach
optical water network (p60 pre-water frequency ≥ 20 %), within 10 km of pre-breach water and downstream of the dam
(*connected ceiling*). Two other rules bound it: the p42 rule (additionally HAND < WSE − 1 m, channel-connected through the
mapped drainage; a lower bound because the delta drainage is incompletely mapped) and the ceiling without connectivity.
The connectivity requirement is not inherited from the terrain-index methods we build on: HAND-type methods "do not
preserve hydraulic connectivity (i.e., floodplain cells lower than the channel water height are denoted as flooded
whether or not there is a physical flow path to them)" (Bates 2021), and GeoFlood by design flags "local depressions such
as ponds or waterbodies … even if they are not connected with the main stem river" (Zheng et al. 2018). Enforcing
connectivity by connected-components analysis, as in coastal bathtub mapping (Kulp and Strauss 2019), is what turns the
ceiling into a lower-biased but physically admissible extent; small channels that the 20 m grid does not resolve are a
known control on floodplain connectivity (Neal et al. 2012), and in flat terrain the inferred flow path can differ from
the real one (Guo et al. 2025) — the two reasons the p42 and connected-ceiling rules are reported as bounds rather than
as one answer.
 The
DEM enters after subtraction of its class-median residual against night ICESat-2 (T18; trees +1.5–2 m, wetland ≈ +0.5 m,
cropland ≈ 0). The *normal regime* is the union of the same rule over the pre-breach days 26 May–5 June plus the observed
pre-breach water (Sentinel-1 1–2 June, p60); **new inundation** is water on day t outside that regime. Cells of the model-only
normal regime ("normally wet": low reed beds below the normal surface that no optical or SAR mask lists as water) are kept as
their own category, because a Sentinel-1 dark-water onset there is a depth signal — the reeds are submerged — not the onset of
inundation: in flooded vegetation the double bounce raises C-band backscatter above the non-flooded level, but once the water
rises over the plants the signal turns dark (Grimaldi et al. 2020; Jarrett et al. 2023; review: Tsyganskaya et al. 2018), so
the date on which a reed bed goes dark is the date its canopy went under, not the date water arrived.
 With the DEM as delivered those reed beds sit above the normal surface and count as new inundation; we report
that run as a sensitivity (T12) and the two quantities — new inundation and wetland submergence — separately.

**T12.** Daily terrain-reconstructed inundation per region and key date, REPORTED AS the Monte-Carlo median [p05-p95] of the 40 spatial draws (p95e) with the deterministic nominal run (*_central_*) alongside -- on the peak days the nominal run lies below its own MC p05, so the interval is not centred on it: reconstructed TOTAL water-surface area (W_total_*: all water on the day incl. pre-breach channels, lakes and reed beds) and reconstructed NEWLY INUNDATED area (A_*) with the volume of new water (V_*). PRIMARY intervals p05/p50/p95 from the 40 spatial Monte-Carlo draws (p95e); *_emu_* = 100 000-draw emulator sensitivity envelope (p95g). Central run (DEM class-bias corrected), p42 HAND rule, ceiling-only, uncorrected-DEM and superseded-closure sensitivities. Daily reconstructed series, not daily observations.
*Evidence level: independent_physical.*

| date | region | A_p50_km2 | A_p05_km2 | A_p95_km2 | A_central_km2 | W_total_p50_km2 | W_total_p05_km2 | W_total_p95_km2 | W_total_central_km2 | V_p50_hm3 | V_p05_hm3 | V_p95_hm3 | V_central_hm3 | kherson_gauge_m |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023-06-05 | DNIPRO_CORRIDOR | nan | nan | nan | 0 | nan | nan | nan | 488.5 | nan | nan | nan | 0 | 0.54 |
| 2023-06-05 | INHULETS_VALLEY_rect | nan | nan | nan | 0 | nan | nan | nan | 20.9 | nan | nan | nan | 0 | 0.54 |
| 2023-06-05 | P42_FLOODPLAIN_DOMAIN | nan | nan | nan | 0 | nan | nan | nan | 303.9 | nan | nan | nan | 0 | 0.54 |
| 2023-06-06 | DNIPRO_CORRIDOR | 189 | 184.3 | 199.7 | 180.1 | 719.1 | 714.4 | 729.8 | 710.2 | 411.5 | 399.7 | 434.1 | 373.08 | 3.09 |
| 2023-06-06 | INHULETS_VALLEY_rect | 34.1 | 31.7 | 36.4 | 34.7 | 59.5 | 57.1 | 61.8 | 60.1 | 82.9 | 76.6 | 88 | 82.89 | 3.09 |
| 2023-06-06 | P42_FLOODPLAIN_DOMAIN | 118.6 | 114.6 | 127.5 | 110.2 | 459.9 | 455.9 | 468.8 | 451.5 | 314.7 | 299.8 | 336.2 | 278.15 | 3.09 |
| 2023-06-07 | DNIPRO_CORRIDOR | 246.7 | 237.6 | 254.9 | 235.3 | 790.5 | 781.4 | 798.7 | 779.1 | 565.9 | 545.4 | 595.7 | 509.01 | 5.66 |
| 2023-06-07 | INHULETS_VALLEY_rect | 42.6 | 41.3 | 43.9 | 43 | 68.2 | 66.9 | 69.5 | 68.6 | 122.6 | 117 | 129.6 | 124.73 | 5.66 |
| 2023-06-07 | P42_FLOODPLAIN_DOMAIN | 162.8 | 158 | 172 | 153.9 | 517.2 | 512.4 | 526.4 | 508.3 | 454.2 | 436.3 | 481.1 | 407.09 | 5.66 |
| 2023-06-08 | DNIPRO_CORRIDOR | 237.1 | 226.4 | 249.6 | 224.7 | 782.9 | 772.2 | 795.4 | 770.5 | 534.7 | 510.6 | 560 | 472.88 | 5.78 |
| 2023-06-08 | INHULETS_VALLEY_rect | 47.1 | 45.5 | 48.4 | 47.3 | 72.8 | 71.2 | 74.1 | 73 | 158.9 | 148.6 | 170.5 | 160.59 | 5.78 |
| 2023-06-08 | P42_FLOODPLAIN_DOMAIN | 164.3 | 154.1 | 174.1 | 151.5 | 521.8 | 511.6 | 531.6 | 509 | 449.8 | 423.8 | 475.3 | 393.97 | 5.78 |
| 2023-06-09 | DNIPRO_CORRIDOR | 196.5 | 190.5 | 207.9 | 182.8 | 738.2 | 732.2 | 749.6 | 724.5 | 512.2 | 487.5 | 539.3 | 452.92 | 5.37 |
| 2023-06-09 | INHULETS_VALLEY_rect | 50.2 | 48.6 | 51.2 | 50.4 | 76 | 74.4 | 77 | 76.2 | 199.4 | 189.7 | 206.7 | 200.31 | 5.37 |
| 2023-06-09 | P42_FLOODPLAIN_DOMAIN | 150.4 | 145.5 | 161.3 | 139.1 | 504 | 499.1 | 514.9 | 492.7 | 428.4 | 407.1 | 457.6 | 374.98 | 5.37 |
| 2023-06-10 | DNIPRO_CORRIDOR | 170.2 | 162 | 178.4 | 156.1 | 697.1 | 688.9 | 705.3 | 683 | 455.2 | 431.2 | 479.8 | 406.45 | 4.8 |
| 2023-06-10 | INHULETS_VALLEY_rect | 48 | 46.5 | 49.4 | 48.3 | 73.7 | 72.2 | 75.1 | 74 | 166.3 | 159.9 | 176.2 | 168.89 | 4.8 |
| 2023-06-10 | P42_FLOODPLAIN_DOMAIN | 129.4 | 121.7 | 138.1 | 116.2 | 468.2 | 460.5 | 476.9 | 455 | 377.8 | 356.9 | 404.5 | 332.9 | 4.8 |
| 2023-06-11 | DNIPRO_CORRIDOR | 156 | 149.7 | 163.9 | 143 | 681.3 | 675 | 689.2 | 668.3 | 373.9 | 353 | 397.3 | 333.83 | 4.24 |
| 2023-06-11 | INHULETS_VALLEY_rect | 45.3 | 43.6 | 46.8 | 45.3 | 71 | 69.3 | 72.5 | 71 | 132.9 | 125.1 | 139.2 | 133.73 | 4.24 |
| 2023-06-11 | P42_FLOODPLAIN_DOMAIN | 121.4 | 115.2 | 130.4 | 109.3 | 459 | 452.8 | 468 | 446.9 | 315.1 | 294.2 | 338.4 | 277.72 | 4.24 |
| 2023-06-12 | DNIPRO_CORRIDOR | 139.9 | 133.1 | 148.8 | 128.5 | 663.8 | 657 | 672.7 | 652.4 | 275.6 | 254.5 | 293.3 | 244.03 | 3.64 |
| 2023-06-12 | INHULETS_VALLEY_rect | 42 | 40.6 | 43.4 | 42.3 | 67.7 | 66.3 | 69.1 | 68 | 99.5 | 92.6 | 105.8 | 101.63 | 3.64 |
| 2023-06-12 | P42_FLOODPLAIN_DOMAIN | 112.7 | 106.7 | 122 | 101.9 | 449.4 | 443.4 | 458.7 | 438.6 | 237.2 | 218.6 | 256.3 | 207.65 | 3.64 |
| 2023-06-13 | DNIPRO_CORRIDOR | 117.9 | 114.3 | 128.7 | 108.4 | 641.3 | 637.7 | 652.1 | 631.8 | 189.2 | 177.5 | 204 | 165.09 | 3.04 |
| 2023-06-13 | INHULETS_VALLEY_rect | 37.2 | 35.3 | 38.7 | 37.4 | 62.8 | 60.9 | 64.3 | 63 | 70.4 | 62.3 | 75 | 70.07 | 3.04 |
| 2023-06-13 | P42_FLOODPLAIN_DOMAIN | 99.7 | 95 | 108.5 | 89.6 | 436 | 431.3 | 444.8 | 425.9 | 166 | 154.7 | 179.1 | 144.21 | 3.04 |
| 2023-06-14 | DNIPRO_CORRIDOR | 97.6 | 92.9 | 106.8 | 87.6 | 620.7 | 616 | 629.9 | 610.7 | 122.9 | 111.6 | 133.4 | 106.71 | 2.55 |
| 2023-06-14 | INHULETS_VALLEY_rect | 30.9 | 29.3 | 32.4 | 31.4 | 56.4 | 54.8 | 57.9 | 56.9 | 46.8 | 40.8 | 52.1 | 48.2 | 2.55 |
| 2023-06-14 | P42_FLOODPLAIN_DOMAIN | 85.2 | 80.2 | 95 | 75.2 | 421.3 | 416.3 | 431.1 | 411.3 | 109.7 | 98.9 | 119.5 | 95.1 | 2.55 |
| 2023-06-15 | DNIPRO_CORRIDOR | 83.4 | 77.5 | 91.3 | 73.8 | 606.2 | 600.3 | 614.1 | 596.6 | 84.7 | 75 | 92 | 73.22 | 2.15 |
| 2023-06-15 | INHULETS_VALLEY_rect | 24.8 | 23.5 | 27 | 25.9 | 50.2 | 48.9 | 52.4 | 51.3 | 29.9 | 26 | 35.3 | 31.43 | 2.15 |
| 2023-06-15 | P42_FLOODPLAIN_DOMAIN | 73.7 | 69.1 | 81.3 | 64.4 | 409.4 | 404.8 | 417 | 400.1 | 76.2 | 68.6 | 83.2 | 65.82 | 2.15 |
| 2023-06-16 | DNIPRO_CORRIDOR | 68.1 | 61.7 | 75.4 | 58.6 | 590.3 | 583.9 | 597.6 | 580.8 | 52 | 45 | 57.3 | 44.58 | 1.8 |
| 2023-06-16 | INHULETS_VALLEY_rect | 19.1 | 17.4 | 20.9 | 18.6 | 44.4 | 42.7 | 46.2 | 43.9 | 18.1 | 15 | 21.8 | 17.89 | 1.8 |
| 2023-06-16 | P42_FLOODPLAIN_DOMAIN | 62.4 | 55.7 | 68.8 | 52.2 | 397.7 | 391 | 404.1 | 387.5 | 47 | 41.4 | 52 | 40.66 | 1.8 |
| 2023-06-18 | DNIPRO_CORRIDOR | 38.8 | 33.1 | 42.2 | 34.5 | 559.3 | 553.6 | 562.7 | 555 | 12.2 | 9.8 | 13.4 | 11.49 | 1.15 |
| 2023-06-18 | INHULETS_VALLEY_rect | 9 | 7.5 | 10.9 | 9.9 | 33.6 | 32.1 | 35.5 | 34.5 | 4.3 | 3.4 | 6.2 | 4.72 | 1.15 |
| 2023-06-18 | P42_FLOODPLAIN_DOMAIN | 35.6 | 30.3 | 39.4 | 30.7 | 369.3 | 364 | 373.1 | 364.4 | 11.1 | 9.1 | 12.1 | 10.49 | 1.15 |
| 2023-06-21 | DNIPRO_CORRIDOR | 2.8 | 1.7 | 4 | 4 | 515.6 | 514.5 | 516.8 | 516.8 | 0.2 | 0.1 | 0.4 | 0.22 | 0.74 |
| 2023-06-21 | INHULETS_VALLEY_rect | 0 | 0 | 0 | 0 | 22.1 | 22.1 | 22.1 | 22.1 | 0 | 0 | 0 | 0 | 0.74 |
| 2023-06-21 | P42_FLOODPLAIN_DOMAIN | 2.4 | 1.6 | 3.5 | 3.4 | 329 | 328.2 | 330.1 | 330 | 0.2 | 0.1 | 0.4 | 0.18 | 0.74 |
| 2023-06-25 | DNIPRO_CORRIDOR | 0.1 | 0 | 0.7 | 0 | 471 | 470.9 | 471.6 | 470.9 | 0 | 0 | 0.1 | 0 | 0.56 |
| 2023-06-25 | INHULETS_VALLEY_rect | 0 | 0 | 0 | 0 | 18.1 | 18.1 | 18.1 | 18.1 | 0 | 0 | 0 | 0 | 0.56 |
| 2023-06-25 | P42_FLOODPLAIN_DOMAIN | 0 | 0 | 0.2 | 0 | 280.7 | 280.7 | 280.9 | 280.7 | 0 | 0 | 0 | 0 | 0.56 |
| 2023-06-30 | DNIPRO_CORRIDOR | 0.2 | 0.1 | 2 | 0.1 | 488.7 | 488.6 | 490.5 | 488.6 | 0 | 0 | 0.1 | 0 | 0.53 |
| 2023-06-30 | INHULETS_VALLEY_rect | 0 | 0 | 0 | 0 | 18.4 | 18.4 | 18.4 | 18.4 | 0 | 0 | 0 | 0 | 0.53 |
| 2023-06-30 | P42_FLOODPLAIN_DOMAIN | 0.2 | 0 | 0.5 | 0 | 290.9 | 290.7 | 291.2 | 290.7 | 0 | 0 | 0.1 | 0 | 0.53 |

*Compact view: 15 of 43 columns; the columns area_semantics, n_draws, rel_halfwidth_A_pct, rel_halfwidth_V_pct, mc_shift_A_pct, mc_shift_V_pct, W_total_emu_km2_p05, W_total_emu_km2_p25, W_total_emu_km2_p50, W_total_emu_km2_p75, W_total_emu_km2_p95, A_emu_km2_p05, A_emu_km2_p25, A_emu_km2_p50, A_emu_km2_p75, A_emu_km2_p95, n_draws_emulator, A_hand_and_ceiling_km2, W_total_hand_and_ceiling_km2, A_ceiling_only_km2, W_total_ceiling_only_km2, A_connected_ceiling_dem_uncorrected_km2, W_total_connected_ceiling_dem_uncorrected_km2, A_connected_ceiling_superseded_km2, W_total_connected_ceiling_superseded_km2, uncertainty_note, definition_note, central_value_note are in `tables/T12.csv`.*

### 3.3 Uncertainty budget

A Monte-Carlo of 40 draws propagates (T11b): the closure residual (σ 0.05 m, one offset per draw), the date-only gauge
(σ 0.05 m, cap cells), the SWOT node height (median wse_u 0.092 m, per node-day),
the per-node time interpolation (NMAD of leave-one-out residuals on observed node-days,
0.054 m, interpolated node-days only) and a spatially correlated (500 m) DEM
error field with the class NMAD of T18 (wetland 0.48 m, trees
1.60 m, cropland 0.20 m). The correlated field follows the
DEM-simulation practice reviewed by Hawker et al. (2018) — DEM error is spatially autocorrelated, and treating it as
aspatial understates its effect on inundation — and the stochastic conditional simulation of Darnell et al. (2008);
correlated and uncorrelated error fields are known to propagate differently into hydrological outputs (Cunha et al. 2012),
which is the reason the draw median is displaced from the nominal run rather than centred on it. The normal regime is
rebuilt per draw.
 These 40 spatial draws are the **primary uncertainty interval** of every reconstructed area and volume:
p05–p95 over draws on the key dates, reported next to the central value rather than centred on it, because the draw median lies
above the deterministic run (correlated DEM noise opens additional connections and adds depth; the shift is about twice as
large for the volume as for the area, T12). The total water-surface area inherits the new-area deviations only (the pre-breach
water is observed, not propagated). A second construction, a cluster-normal **emulator** with 100 000 draws per day over the
class-wise DEM and water-surface error parameters (p95g), gives a broader **sensitivity envelope** of the area over the parameter
space; it represents a different distribution, is wider than the spatial draws, and is never used as the primary interval (its
volume draws are unanchored and are not used). The planar-surface assumption and the absence of timing (filling and draining)
are in neither budget and make the recession a lower bound.

**T11b.** Uncertainty components of the terrain reconstruction (Monte-Carlo inputs): closure, gauge, SWOT node height, per-node time interpolation, DEM error by WorldCover class (Paper 2 / p57).
*Evidence level: independent_physical.*

| component | sigma_m | applied | source | bias_m | rmse_m | n |
|---|---|---|---|---|---|---|
| closure_kherson | 0.05 | one offset per draw, all cells | Paper 1 Table 5 / Sec. 5.12 (NMAD 4-5 cm at Kherson) | nan | nan | nan |
| gauge_daily | 0.05 | per draw, cells > 15 km from a node (gauge cap) | date-only daily values; two yearbooks differ by NMAD 1.5 cm (Paper 1 Sec. 5.12) | nan | nan | nan |
| swot_node_wse_u | 0.092 | per (day, 1-km bin), 5-km smoothed field | p59 nodes, median wse_u | nan | nan | nan |
| H(s,t)_interpolation | 0.054 | interpolated cells only, per (day, bin), 5-km smoothed | leave-one-out NMAD on 17313 observed cells | nan | nan | nan |
| dem_trees | 1.603 | class-wise sigma, spatially correlated field (500 m) per draw; class median bias removed in p95 rev 5 | /home/niko/repo/floodstate-eo/case_studies/kakhovka_2023/tables/p57_dem_accuracy_night.csv (C seamless by WorldCover class) | 1.481 | 3.024 | 8066 |
| dem_grass | 0.491 | class-wise sigma, spatially correlated field (500 m) per draw; class median bias removed in p95 rev 5 | /home/niko/repo/floodstate-eo/case_studies/kakhovka_2023/tables/p57_dem_accuracy_night.csv (C seamless by WorldCover class) | 0.107 | 1.329 | 29227 |
| dem_cropland | 0.195 | class-wise sigma, spatially correlated field (500 m) per draw; class median bias removed in p95 rev 5 | /home/niko/repo/floodstate-eo/case_studies/kakhovka_2023/tables/p57_dem_accuracy_night.csv (C seamless by WorldCover class) | -0.059 | 0.408 | 95454 |
| dem_built | 0.696 | class-wise sigma, spatially correlated field (500 m) per draw; class median bias removed in p95 rev 5 | /home/niko/repo/floodstate-eo/case_studies/kakhovka_2023/tables/p57_dem_accuracy_night.csv (C seamless by WorldCover class) | 0.151 | 1.901 | 7850 |
| dem_bare | 1.188 | class-wise sigma, spatially correlated field (500 m) per draw; class median bias removed in p95 rev 5 | /home/niko/repo/floodstate-eo/case_studies/kakhovka_2023/tables/p57_dem_accuracy_night.csv (C seamless by WorldCover class) | -0.574 | 3.375 | 287 |
| dem_wetland | 0.477 | class-wise sigma, spatially correlated field (500 m) per draw; class median bias removed in p95 rev 5 | /home/niko/repo/floodstate-eo/case_studies/kakhovka_2023/tables/p57_dem_accuracy_night.csv (C seamless by WorldCover class) | 0.509 | 1.131 | 12409 |
| dem_all | 0.299 | class-wise sigma, spatially correlated field (500 m) per draw; class median bias removed in p95 rev 5 | /home/niko/repo/floodstate-eo/case_studies/kakhovka_2023/tables/p57_dem_accuracy_night.csv (C seamless by WorldCover class) | -0.002 | 1.11 | 153342 |

### 3.4 Checks: Sentinel-1 per date, disagreement ontology, ICESat-2

On each Sentinel-1 date the reconstruction is compared with the S1 new dark water (mask minus water on 1–2 June) on the S1
valid footprint, the owned zone area and outside the cut rectangles: hits, misses, terrain-only cells, POD, FAR and CSI
(contingency-table measures, Schaefer 1990; raw agreement, primary, T13) — reported per date and per domain because
binary pattern measures depend on the size of the flood and of the domain over which they are computed (Stephens et al.
2014);
 the *conditional POD outside the normally-wet class* — POD on the observable dry-background
domain, with the class fixed before any comparison was read — is a diagnostic conditional agreement, not a corrected POD. The disagreement is decomposed into A (both), B (terrain only) and C (S1 only), by WorldCover and RF20
class and by ground elevation relative to the reconstructed surface (< 0, 0–2, 2–5, ≥ 5 m; T14). Night ICESat-2 ATL08 ground
segments (Paper 2 chain) sampled on the 9 June categories give, per category, the residual DEM − ICESat-2 and the share of
segments whose ground lies below the reconstructed surface (T15): an altimetric consistency check of the DEM and the surface
along tracks, not a validation of the inundation map.

**T13.** Terrain reconstruction vs Sentinel-1 new dark water per acquisition date, region and variant: hit / miss / miss-on-normally-wet / terrain-only km2, POD, FAR, CSI (raw agreement, primary) and the conditional POD outside the normally-wet class (diagnostic).
*Evidence level: cross_sensor.*

*Table T13 has 165 rows × 15 columns and is supplied as `tables/T13.csv` (Supplementary Data); it is not printed here.*

**T14.** Disagreement ontology terrain x Sentinel-1 by zone and date: category areas split by ground elevation relative to the water surface, normally-wet flag, WorldCover and RF20 classes (km2).
*Evidence level: contextual.*

| zone | date | category | km2 | km2_ground_below_surface | km2_ground_0_2m_above | km2_ground_2_5m_above | km2_ground_ge5m_above | km2_normally_wet | category_meaning |
|---|---|---|---|---|---|---|---|---|---|
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-09 | A | 25.82 | 25.82 | 0 | 0 | 0 | 0 | terrain+ / S1+ |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-09 | B | 66.28 | 66.28 | 0 | 0 | 0 | 0 | terrain+ / S1- (sensor blind spot or reconstruction excess) |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-09 | C | 109.07 | 75.09 | 1.44 | 3.46 | 29.08 | 74.29 | terrain- / S1+ (submergence signal on normally-wet ground, or S1-only detections topographically unsupported by the reconstructed surface) |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-09 | N | 1870.95 | 305.79 | 96.6 | 199.53 | 1268.69 | 57.96 | neither |
| ZONE_2_KHERSON_DELTA | 2023-06-09 | A | 32.98 | 32.98 | 0 | 0 | 0 | 0 | terrain+ / S1+ |
| ZONE_2_KHERSON_DELTA | 2023-06-09 | B | 53.39 | 53.39 | 0 | 0 | 0 | 0 | terrain+ / S1- (sensor blind spot or reconstruction excess) |
| ZONE_2_KHERSON_DELTA | 2023-06-09 | C | 151.55 | 91.47 | 32.09 | 3.02 | 24.96 | 99.2 | terrain- / S1+ (submergence signal on normally-wet ground, or S1-only detections topographically unsupported by the reconstructed surface) |
| ZONE_2_KHERSON_DELTA | 2023-06-09 | N | 883.09 | 168.62 | 51.5 | 36.28 | 619.94 | 36.41 | neither |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-13 | A | 12.55 | 12.55 | 0 | 0 | 0 | 0 | terrain+ / S1+ |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-13 | B | 26.64 | 26.64 | 0 | 0 | 0 | 0 | terrain+ / S1- (sensor blind spot or reconstruction excess) |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-13 | C | 78.01 | 73.28 | 0.93 | 0.86 | 2.94 | 71.72 | terrain- / S1+ (submergence signal on normally-wet ground, or S1-only detections topographically unsupported by the reconstructed surface) |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-13 | N | 1954.93 | 269.34 | 37.29 | 137.81 | 1510.13 | 60.52 | neither |
| ZONE_2_KHERSON_DELTA | 2023-06-13 | A | 10.88 | 10.88 | 0 | 0 | 0 | 0 | terrain+ / S1+ |
| ZONE_2_KHERSON_DELTA | 2023-06-13 | B | 57.86 | 57.86 | 0 | 0 | 0 | 0 | terrain+ / S1- (sensor blind spot or reconstruction excess) |
| ZONE_2_KHERSON_DELTA | 2023-06-13 | C | 63.46 | 56.9 | 3.57 | 0.25 | 2.73 | 57.93 | terrain- / S1+ (submergence signal on normally-wet ground, or S1-only detections topographically unsupported by the reconstructed surface) |
| ZONE_2_KHERSON_DELTA | 2023-06-13 | N | 1157.71 | 277.95 | 107.27 | 60.07 | 704.75 | 90.16 | neither |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-14 | A | 5.77 | 5.77 | 0 | 0 | 0 | 0 | terrain+ / S1+ |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-14 | B | 24.74 | 24.74 | 0 | 0 | 0 | 0 | terrain+ / S1- (sensor blind spot or reconstruction excess) |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-14 | C | 53.42 | 47.17 | 1.77 | 0.62 | 3.87 | 46.39 | terrain- / S1+ (submergence signal on normally-wet ground, or S1-only detections topographically unsupported by the reconstructed surface) |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2023-06-14 | N | 1233.79 | 176.38 | 27.01 | 110.23 | 919.82 | 85.85 | neither |
| ZONE_2_KHERSON_DELTA | 2023-06-14 | A | 5.97 | 5.97 | 0 | 0 | 0 | 0 | terrain+ / S1+ |
| ZONE_2_KHERSON_DELTA | 2023-06-14 | B | 50.79 | 50.79 | 0 | 0 | 0 | 0 | terrain+ / S1- (sensor blind spot or reconstruction excess) |
| ZONE_2_KHERSON_DELTA | 2023-06-14 | C | 34.14 | 17.53 | 3.46 | 2.4 | 10.75 | 18.06 | terrain- / S1+ (submergence signal on normally-wet ground, or S1-only detections topographically unsupported by the reconstructed surface) |
| ZONE_2_KHERSON_DELTA | 2023-06-14 | N | 1199.01 | 317.92 | 113.64 | 60.26 | 699.53 | 130.03 | neither |

*Compact view: 10 of 20 columns; the columns km2_wc_trees, km2_wc_wetland, km2_wc_built, km2_wc_cropland, km2_wc_grass, km2_wc_bare, km2_p73_reed, km2_p73_forest, km2_p73_built, km2_p73_cropland are in `tables/T14.csv`.*

**T15.** ICESat-2 altimetric consistency check per zone and agreement category: residual seamless DEM minus ICESat-2 (median, p10, p90), ICESat-2 ground minus water surface, share of segments below the surface.
*Evidence level: independent_physical.*

| zone | category | N | res_median | res_p10 | res_p90 | ice_minus_wse_median | share_ice_below_wse | share_dem_below_wse | check_type |
|---|---|---|---|---|---|---|---|---|---|
| ZONE_2_KHERSON_DELTA | observed_neither | 90625 | -0.02 | -1.54 | 1.17 | 13.26 | 0.229 | 0.206 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_2_KHERSON_DELTA | S1_only_ground_lt2m_above | 12297 | 0.42 | -0.24 | 0.81 | -2.92 | 0.857 | 0.796 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_2_KHERSON_DELTA | both | 4030 | 0.85 | 0.04 | 1.42 | -3.01 | 0.994 | 0.995 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_2_KHERSON_DELTA | terrain_only | 7893 | 0.81 | -0.23 | 2.03 | -2.25 | 0.97 | 0.924 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_2_KHERSON_DELTA | S1_only_ground_ge2m_above | 3205 | 0.03 | -0.31 | 0.64 | 13.5 | 0 | 0 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_2_KHERSON_DELTA | S1_only_ge2m box=False wc=grass | 1646 | 0.03 | -0.32 | 0.97 | 12.94 | 0 | 0 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_2_KHERSON_DELTA | S1_only_ge2m box=False wc=cropland | 1067 | -0.02 | -0.32 | 0.39 | 28.89 | 0 | 0 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_2_KHERSON_DELTA | S1_only_ge2m box=True wc=grass | 386 | 0.14 | -0.17 | 0.7 | 5.82 | 0 | 0 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_2_KHERSON_DELTA | S1_only_ge2m box=True wc=cropland | 90 | 0.32 | -0.28 | 0.93 | 30.7 | 0 | 0 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | observed_neither | 102676 | 0.22 | -0.28 | 1.52 | 16.75 | 0.135 | 0.107 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | S1_only_ground_lt2m_above | 6656 | 0.58 | -0.06 | 0.98 | -6.71 | 0.985 | 0.984 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | both | 2365 | 0.52 | -0.11 | 1.47 | -3.67 | 1 | 0.998 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | terrain_only | 6764 | 0.49 | -0.32 | 1.88 | -2.84 | 0.971 | 0.883 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | S1_only_ground_ge2m_above | 1687 | 0.02 | -0.25 | 1.63 | 38.86 | 0.007 | 0 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | S1_only_ge2m box=False wc=grass | 493 | 0.76 | -0.05 | 7.11 | 3.33 | 0.02 | 0 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | S1_only_ge2m box=False wc=cropland | 1171 | -0.06 | -0.28 | 0.25 | 44.67 | 0 | 0 | altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map |

### 3.5 Surface context: RF20

A random forest (Breiman 2001; for its use in land-cover mapping see Belgiu and Drăguţ 2016) on PRE-event Sentinel-2 composite predictors, trained on ESA WorldCover 2021 with a purity filter, classifies
the surface at 20 m into water, cropland, grass/low vegetation, forest, wetland/reed, built-up, bare sand and uncertain
(p73, frozen before any arm was trained). Its per-class precision, recall and F1 in spatial-block 5-fold cross-validation and in
the frame transfers B1↔B2 are agreement with the training reference (T09, T10), not validation. It supplies the evaluation
strata of the arms and the classes of the ontology.

**T09.** RF20 surface classification: per-class precision / recall / F1 with support, macro means and overall agreement, spatial-block 5-fold CV and frame transfers. Reference = WorldCover 2021, the training reference.
*Evidence level: contextual.*

| evaluation | cls | precision | recall | F1 | n | OA_spatial_cv | kappa_spatial_cv_csv_only | reference |
|---|---|---|---|---|---|---|---|---|
| spatial_block_cv_5fold | WATER | 0.9983 | 0.9986 | 0.9984 | 60000 | 0.9404 | 0.9301 | ESA WorldCover 2021 (training reference; agreement, not validation) |
| spatial_block_cv_5fold | CROPLAND | 0.9196 | 0.9284 | 0.924 | 60000 | 0.9404 | 0.9301 | ESA WorldCover 2021 (training reference; agreement, not validation) |
| spatial_block_cv_5fold | GRASS_LOW_VEGETATION | 0.8735 | 0.8753 | 0.8744 | 60000 | 0.9404 | 0.9301 | ESA WorldCover 2021 (training reference; agreement, not validation) |
| spatial_block_cv_5fold | FOREST | 0.9372 | 0.9319 | 0.9345 | 60000 | 0.9404 | 0.9301 | ESA WorldCover 2021 (training reference; agreement, not validation) |
| spatial_block_cv_5fold | WETLAND_REED | 0.969 | 0.9372 | 0.9528 | 60000 | 0.9404 | 0.9301 | ESA WorldCover 2021 (training reference; agreement, not validation) |
| spatial_block_cv_5fold | BUILT_UP | 0.918 | 0.9594 | 0.9382 | 60000 | 0.9404 | 0.9301 | ESA WorldCover 2021 (training reference; agreement, not validation) |
| spatial_block_cv_5fold | BARE_SAND | 0.9961 | 0.9618 | 0.9786 | 32420 | 0.9404 | 0.9301 | ESA WorldCover 2021 (training reference; agreement, not validation) |
| spatial_block_cv_5fold | MACRO | 0.9445 | 0.9418 | 0.943 | 392420 | 0.9404 | 0.9301 | ESA WorldCover 2021 (training reference; agreement, not validation) |
| spatial_block_cv_5fold | OVERALL_ACCURACY | nan | nan | 0.9404 | 392420 | 0.9404 | 0.9301 | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B1_to_B2 | WATER | 0.9978 | 0.9992 | 0.9985 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B1_to_B2 | CROPLAND | 0.9344 | 0.8707 | 0.9014 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B1_to_B2 | GRASS_LOW_VEGETATION | 0.8184 | 0.8913 | 0.8533 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B1_to_B2 | FOREST | 0.9539 | 0.8963 | 0.9242 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B1_to_B2 | WETLAND_REED | 0.9505 | 0.9414 | 0.9459 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B1_to_B2 | BUILT_UP | 0.8913 | 0.9578 | 0.9233 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B1_to_B2 | BARE_SAND | 0.977 | 0.6496 | 0.7803 | 2420 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B1_to_B2 | MACRO | 0.9319 | 0.8866 | 0.9039 | 182420 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B1_to_B2 | OVERALL_ACCURACY | nan | nan | 0.9225 | 182420 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B2_to_B1 | WATER | 0.9985 | 0.9984 | 0.9984 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B2_to_B1 | CROPLAND | 0.843 | 0.9541 | 0.8952 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B2_to_B1 | GRASS_LOW_VEGETATION | 0.8992 | 0.765 | 0.8267 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B2_to_B1 | FOREST | 0.8966 | 0.9437 | 0.9195 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B2_to_B1 | WETLAND_REED | 0.9675 | 0.9302 | 0.9485 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B2_to_B1 | BUILT_UP | 0.9365 | 0.9475 | 0.942 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B2_to_B1 | BARE_SAND | 0.9971 | 0.989 | 0.993 | 30000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B2_to_B1 | MACRO | 0.9341 | 0.9326 | 0.9319 | 210000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B2_to_B1 | OVERALL_ACCURACY | nan | nan | 0.9326 | 210000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| spatial_block_cv_5fold | MACRO_MEAN | 0.9445 | 0.9418 | 0.9427 | 1177260 | 0.9404 | 0.9301 | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B1_to_B2 | MACRO_MEAN | 0.9319 | 0.8866 | 0.9059 | 547260 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |
| transfer_B2_to_B1 | MACRO_MEAN | 0.9341 | 0.9326 | 0.932 | 630000 | nan | nan | ESA WorldCover 2021 (training reference; agreement, not validation) |

**T10.** RF20 confusion matrix (spatial-block CV, counts).
*Evidence level: contextual.*

| reference \ predicted | WATER | CROPLAND | GRASS_LOW_VEGETATION | FOREST | WETLAND_REED | BUILT_UP | BARE_SAND |
|---|---|---|---|---|---|---|---|
| WATER | 59917 | 0 | 0 | 0 | 57 | 1 | 25 |
| CROPLAND | 0 | 55703 | 3694 | 191 | 186 | 225 | 1 |
| GRASS_LOW_VEGETATION | 12 | 3700 | 52518 | 1417 | 536 | 1808 | 9 |
| FOREST | 0 | 307 | 1388 | 55914 | 976 | 1415 | 0 |
| WETLAND_REED | 84 | 461 | 1175 | 1560 | 56231 | 489 | 0 |
| BUILT_UP | 0 | 401 | 1323 | 581 | 46 | 57561 | 88 |
| BARE_SAND | 8 | 0 | 26 | 0 | 0 | 1206 | 31180 |

### 3.6 Weak labels and U-Net arms

Label contract v002 marks FLOOD where Sentinel-1 saw water on at least two of the three peak dates (9, 13, 14 June) on land
that was dry on every pre-breach date, NON_FLOOD where every post-breach date was dry, IGNORE elsewhere. Contract v003_A
(frozen 25 September 2026) keeps the same positives and adds REFERENCE_WATER — recurrent water on at least three admitted May
dates — as a negative class, with UNKNOWN for insufficient or extrapolated evidence; the immediate pre-event state W_pre
(1–2 June) enters its ontology. U-Net (ResNet-34 encoder from scratch, 512-px patches, masked binary cross-entropy + Dice loss (Milletari et al. 2016), 60 epochs, seed
20260923) arms differ only in inputs: U0d (S1 change channels + support), U0z (+ robust z channels), U1 (+ RF20 one-hot),
U2 (+ HAND) on v002; U0d, U2 and U2b (+ W_pre) on v003_A. Thresholds are frozen on validation before the test blocks are read.
U2b is a diagnostic upper bound: W_pre is both an input and a label ingredient, so its comparison is not independent.

### 3.7 Spatial blocking and statistics

The split m6_split_v1 assigns 10 km blocks of the global lattice to train, validation and test with 640 m eroded buffers and
pure 512-px footprints (T03; {'train': 64, 'val': 15, 'test': 20} blocks). The block size exceeds the patch plus two
buffers (5.12 + 1.28 km), the minimum for which a validation patch exists (a 5 km split leaves none); 7.5, 15 and 20 km splits
retrain U2 as a sensitivity (T20). Endpoints are computed on unique test pixels and compared between arms by a paired bootstrap
over identical physical blocks (2000 resamples). Per-day statistics of the water surface use the day as the independent unit.

**T03.** Frozen spatial-block split m6_split_v1: geometry, counts and rationale.
*Evidence level: weak_label_agreement.*

| item | value |
|---|---|
| block size (m) | 10000.0 |
| buffer (px / m) | 64 / 640 |
| patch (px / km) | 512 / 5.12 |
| blocks train/val/test | {'train': 64, 'val': 15, 'test': 20} |
| patches train/val/test | {'train': 556, 'test': 164, 'val': 28} |
| accepted draw / seed | 1 / 20260923 |
| selection reads | m6_labels_v002 + frozen p73 only; never U0/U1 scores, model errors or target metrics |
| anti-leakage | pure 512x512 footprints (centre >= 2.56 km from axis-aligned split boundaries) + 640 m eroded buffer; both asserted on the frozen patch list |
| minimum feasible block | patch + 2 x buffer = 5.12 + 1.28 km; a 5 km split leaves no validation patch (p84 rebuild, 2026-09-25) |

**T20.** Block-size sensitivity (U2 on v003_A): the same recipe on splits with 7.5, 10 (frozen), 15 and 20 km blocks; each split has its own TEST geography, so only the endpoint values and intervals are compared, never differences.
*Evidence level: weak_label_agreement.*

| split | block_km | status | n_blocks | n_patches | G_F1 | G_F1_lo | G_F1_hi | G_IoU | G_IoU_lo | G_IoU_hi | G_PR_AUC | G_PR_AUC_lo | G_PR_AUC_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| m6_split_v1 | 10 | U2 v003_A trained and evaluated | {'train': 64, 'val': 15, 'test': 20} | {'train': 556, 'test': 164, 'val': 28} | 0.9306 | 0.72898 | 0.942203 | 0.8702 | 0.57353 | 0.890703 | 0.9613 | nan | nan |
| m6_split_s5 | 5 | split infeasible (no validation patch survives the buffer) | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| m6_split_s7p5 | 7.5 | U2 v003_A trained and evaluated | {'train': 95, 'val': 22, 'test': 29} | {'train': 393, 'test': 24, 'val': 15} | 0.9561 | 0.878377 | 0.970703 | 0.9159 | 0.783162 | 0.943102 | 0.9808 | nan | nan |
| m6_split_s15 | 15 | U2 v003_A trained and evaluated | {'train': 28, 'val': 6, 'test': 8} | {'train': 989, 'val': 270, 'test': 154} | 0.9366 | 0 | 0.945507 | 0.8807 | 0 | 0.896612 | 0.9816 | nan | nan |
| m6_split_s20 | 20 | U2 v003_A trained and evaluated | {'train': 20, 'val': 4, 'test': 6} | {'train': 825, 'test': 379, 'val': 209} | 0.8764 | 0.7361 | 0.9384 | 0.7799 | 0.5823 | 0.884 | 0.9373 | nan | nan |

*Compact view: 14 of 30 columns; the columns A_FP_area_dry_cropland_km2, A_FP_area_dry_cropland_km2_lo, A_FP_area_dry_cropland_km2_hi, B_recall_flooded_open_low_veg, B_recall_flooded_open_low_veg_lo, B_recall_flooded_open_low_veg_hi, W_IoU, W_IoU_lo, W_IoU_hi, BU_FP_area_km2, BU_FP_area_km2_lo, BU_FP_area_km2_hi, A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2, A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2_lo, A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2_hi, threshold are in `tables/T20.csv`.*

### 3.8 Area semantics

Every area in this paper is one of: observed_S1 (dark water on that date minus pre-breach water), mapped_UNet (score above
the frozen threshold), terrain_reconstructed (allowed by the water surface and connectivity, outside the normal regime) or
literature_reported (an operational figure with its own AOI, date and reference water; context, never validation). No
probability-sample reference exists, so none of them is an unbiased estimate of the true flooded area.

## 4. Results

### 4.1 The daily reconstructed series [C01–C03, C07, C14]

In the Dnipro corridor the reconstructed newly inundated area rises from zero on 5 June to
189 km² on 6 June and reaches its maximum of
247 km² on 7 June (Monte-Carlo median; primary p05–p95
238–255 km²; deterministic nominal run 235 km²),
a day between the Sentinel-1 acquisitions that no scene covers [C01]; the Kherson stage reaches its maximum one day later
(5.78 m on 8 June, the daily value of the river yearbook used here;
the operational record gives 5.68 m at 15:00 on 8 June (Gleick et al. 2023) and Lehnigk et al. 2026 cite 5.6 m, a ~0.1 m spread
between sources; the downstream peak stages of 10–11 m by 8 June that Lehnigk et al. 2026 report from the same SWOT data are consistent with it) — the areal maximum and the peak stage are different quantities, and the day of the
areal maximum is a property of the reconstructed series, not an observation. It is 196 km² on 9 June,
118 km² on 13 June,
39 km² on 18 June and
3 km² on 21 June, when the Kherson stage is back at
0.74 m (Fig04, T12) [C03]. The reconstructed new-water volume
reaches 566 hm³ (median; p05–p95
545–596 hm³;
deterministic nominal run 509 hm³) [C02]. All areas and volumes after 5 June are Monte-Carlo medians unless marked as a nominal run.
The rule and DEM sensitivities are deterministic runs and compare with the nominal connected run (235 km²), not with the median:
the p42 HAND rule gives 247 km² at the reconstructed areal maximum (a numerical coincidence with the connected-ceiling median, not the same quantity); the
ceiling without connectivity 254 km². The largest single
term is definitional: with the DEM as delivered, the reed beds count as new inundation and the areal maximum is
347 km². Inside the p42 floodplain
domain the areal maximum is 163 km²; the Inhulets valley, treated as
backwater with its own SWOT nodes, peaks at 50 km² on 9 June.
The depth and duration maps (Fig07) show the 7–8 June water more than 4 m deep on the right-bank floodplain below the dam and
the delta channels, and inundation lasting more than a week only in the floodplain lows and the delta.

![Fig04](figures/Fig04_daily_inundation.png)

**Fig04. Daily reconstructed series, dam → liman.** (a–c) Reconstructed total water-surface area per day (all water on the day, including pre-breach channels, lakes and reed beds) for the Dnipro corridor, the p42 floodplain domain and the Inhulets valley: central run (black), the PRIMARY interval (shaded: p05–p95 of the 40 spatial Monte-Carlo draws, key dates), the emulator sensitivity envelope (candles: 100 000 draws per day, p05–p95 whisker, p25–p75 body, median; area only, a broader parameter space), the DEM-as-delivered sensitivity (orange) and the Sentinel-1 total dark water per acquisition (diamonds; open = partial coverage). (d–f) Reconstructed newly inundated area (black) with its daily change as bars (blue filling, orange draining) and the U-Net U2b persistent-event-flood area. (g–i) Kherson stage. Values between observation days are reconstructed, not observed; the reconstructed areal maximum (7 June, a day set by the interpolated node series and the gauge) lies between the Sentinel-1 acquisitions. Areas are terrain_reconstructed or observed_S1 (T12, T19).

![Fig07](figures/Fig07_event_scale_reconstruction.png)

**Fig07. Event-scale spatial result.** (a) Depth of the reconstructed newly inundated area on 2023-06-08, one day after the reconstructed areal maximum and without a satellite scene. (b) Number of days with new inundation between 26 May and 10 July. Connected-ceiling rule, central run; rasters derived from FABDEM through the seamless DEM (not redistributed).

**Reconstructed total water-surface area [C02].** The newly inundated area is the water that was not there before; the total
water-surface area is all water on the day, including the pre-breach channels, lakes and reed beds. In the corridor it is 488 km²
in the normal regime (5 June; observed regime, no draws), 790 km² on 7 June (median; primary p05–p95
781–799 km²; nominal run 779 km²),
738 km² on 9 June and
641 km² on 13 June (with the DEM as delivered:
310 →
714 km²); the Inhulets valley adds
68 km² on 7 June. Sentinel-1 saw
682 km² of dark water in the corridor on 9 June and
68 km² in the Inhulets valley. Neither total is comparable
with the operational figures: the UNOSAT ~620 km² of 9 June is cumulative satellite-detected flooded *land* over 6–9 June with the
pre-existing water as a separate class (T16, literature_reported), a quantity closer in kind to the newly inundated area
than to the total water-surface area, and it differs further in AOI (the liman reach, frame B3, is not part of this domain),
in temporal semantics (cumulative vs daily snapshot) and in reference water (§4.6).

**T16.** Area accounting with explicit semantics: observed (S1), mapped (U-Net), terrain-reconstructed and literature-reported figures are different quantities (new vs total water; snapshot vs cumulative vs persistence) and are never compared as validation.
*Evidence level: mixed.*

| region | quantity | km2 | area_semantics | quantity_semantics | temporal_semantics | unobserved_km2 | verify | comparability_note |
|---|---|---|---|---|---|---|---|---|
| DNIPRO_CORRIDOR | S1 new dark water, 06-09 scene | 299.6 | observed_S1 | new_water (pre-breach water excluded) | snapshot_2023-06-09 | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| DNIPRO_CORRIDOR | S1 new dark water, >= 2 of 3 peak dates (label recipe) | 167.8 | observed_S1 | new_water (pre-breach water excluded) | persistence_2of3_(06-09,06-13,06-14) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| DNIPRO_CORRIDOR | S1 total dark water, 06-09 (incl. pre-breach water) | 682.5 | observed_S1 | total_water | snapshot_2023-06-09 | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| DNIPRO_CORRIDOR | pre-breach water (S1 06-01/02 or p60 pre_water_frac >= 20 %) | 594.4 | observed_S1 | reference_water | reference_2023-06-01/02 | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| DNIPRO_CORRIDOR | U2b predicted event flood (persistent concept) | 241 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| INHULETS_VALLEY_rect | S1 new dark water, 06-09 scene | 36.1 | observed_S1 | new_water (pre-breach water excluded) | snapshot_2023-06-09 | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| INHULETS_VALLEY_rect | S1 new dark water, >= 2 of 3 peak dates (label recipe) | 27.2 | observed_S1 | new_water (pre-breach water excluded) | persistence_2of3_(06-09,06-13,06-14) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| INHULETS_VALLEY_rect | S1 total dark water, 06-09 (incl. pre-breach water) | 67.6 | observed_S1 | total_water | snapshot_2023-06-09 | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| INHULETS_VALLEY_rect | pre-breach water (S1 06-01/02 or p60 pre_water_frac >= 20 %) | 91 | observed_S1 | reference_water | reference_2023-06-01/02 | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| INHULETS_VALLEY_rect | U2b predicted event flood (persistent concept) | 30.4 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| P42_FLOODPLAIN_DOMAIN | S1 new dark water, 06-09 scene | 202.9 | observed_S1 | new_water (pre-breach water excluded) | snapshot_2023-06-09 | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| P42_FLOODPLAIN_DOMAIN | S1 new dark water, >= 2 of 3 peak dates (label recipe) | 148.2 | observed_S1 | new_water (pre-breach water excluded) | persistence_2of3_(06-09,06-13,06-14) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| P42_FLOODPLAIN_DOMAIN | S1 total dark water, 06-09 (incl. pre-breach water) | 329.6 | observed_S1 | total_water | snapshot_2023-06-09 | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| P42_FLOODPLAIN_DOMAIN | pre-breach water (S1 06-01/02 or p60 pre_water_frac >= 20 %) | 153 | observed_S1 | reference_water | reference_2023-06-01/02 | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| P42_FLOODPLAIN_DOMAIN | U2b predicted event flood (persistent concept) | 188.8 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| ALL_B1uB2 | U2b predicted flood (p92 accounting) | 274.6 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 211.2 | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| DNIPRO_CORRIDOR | U2b predicted flood (p92 accounting) | 241 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 209.6 | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| CUT_RECTS_total | U2b predicted flood (p92 accounting) | 33.6 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 1.6 | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| INHULETS_VALLEY_rect | U2b predicted flood (p92 accounting) | 30.4 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 0 | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| WEST_OF_MOUTH_rect | U2b predicted flood (p92 accounting) | 3.2 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 1.6 | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| TERRACE_NE_rect | U2b predicted flood (p92 accounting) | 0 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 0 | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| P42_FLOODPLAIN_DOMAIN | U2b predicted flood (p92 accounting) | 188.8 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 0 | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| DNIPRO_CORRIDOR_outside_p42_domain | U2b predicted flood (p92 accounting) | 52.2 | mapped_UNet | new_water (label concept) | persistence (label concept ~13 June regime) | 209.6 | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| DNIPRO_CORRIDOR | reconstructed newly inundated area, areal maximum 2023-06-07 | 235.3 | terrain_reconstructed | new_water (outside the same-rule pre-breach regime) | daily_snapshot_2023-06-07 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| DNIPRO_CORRIDOR | reconstructed newly inundated area, 06-09 | 182.8 | terrain_reconstructed | new_water (outside the same-rule pre-breach regime) | daily_snapshot_2023-06-09 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| DNIPRO_CORRIDOR | reconstructed total water-surface area, 2023-06-07 | 779.1 | terrain_reconstructed | total_water (incl. pre-breach channels, lakes, reed beds) | daily_snapshot_2023-06-07 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| DNIPRO_CORRIDOR | reconstructed total water-surface area, normal regime 06-05 | 488.5 | terrain_reconstructed | total_water (incl. pre-breach channels, lakes, reed beds) | daily_snapshot_2023-06-05 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| P42_FLOODPLAIN_DOMAIN | reconstructed newly inundated area, areal maximum 2023-06-07 | 153.9 | terrain_reconstructed | new_water (outside the same-rule pre-breach regime) | daily_snapshot_2023-06-07 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| P42_FLOODPLAIN_DOMAIN | reconstructed newly inundated area, 06-09 | 139.1 | terrain_reconstructed | new_water (outside the same-rule pre-breach regime) | daily_snapshot_2023-06-09 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| P42_FLOODPLAIN_DOMAIN | reconstructed total water-surface area, 2023-06-07 | 508.3 | terrain_reconstructed | total_water (incl. pre-breach channels, lakes, reed beds) | daily_snapshot_2023-06-07 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| P42_FLOODPLAIN_DOMAIN | reconstructed total water-surface area, normal regime 06-05 | 303.9 | terrain_reconstructed | total_water (incl. pre-breach channels, lakes, reed beds) | daily_snapshot_2023-06-05 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| INHULETS_VALLEY_rect | reconstructed newly inundated area, areal maximum 2023-06-09 | 50.4 | terrain_reconstructed | new_water (outside the same-rule pre-breach regime) | daily_snapshot_2023-06-09 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| INHULETS_VALLEY_rect | reconstructed newly inundated area, 06-09 | 50.4 | terrain_reconstructed | new_water (outside the same-rule pre-breach regime) | daily_snapshot_2023-06-09 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| INHULETS_VALLEY_rect | reconstructed total water-surface area, 2023-06-09 | 76.2 | terrain_reconstructed | total_water (incl. pre-breach channels, lakes, reed beds) | daily_snapshot_2023-06-09 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| INHULETS_VALLEY_rect | reconstructed total water-surface area, normal regime 06-05 | 20.9 | terrain_reconstructed | total_water (incl. pre-breach channels, lakes, reed beds) | daily_snapshot_2023-06-05 (reconstructed series) | nan | nan | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| reported AOI (differs) | UNOSAT product 3616 (9 June 2023): flooded LAND, cumulative satellite-detected 6-9 June (ICEYE, Sentinel-3, Sentinel-2); pre-existing water is a separate reference class; preliminary, not field-validated | 620 | literature_reported | flooded_land_new (reference water excluded) | cumulative_2023-06-06..09 | nan | VERIFY: product id, AOI, reference-water definition (via CEOBS 2023 / REACH 2023) | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| reported AOI (differs) | UNOSAT product 3623 (13 June 2023): land that appears flooded on 13 June vs reference water of 3/5 June | 180 | literature_reported | flooded_land_new (reference water excluded) | snapshot_2023-06-13 | nan | VERIFY: product id and AOI | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |
| reported AOI (differs) | Kadam et al. 2024 (HEC-RAS 1D/2D, 300 m breach scenario): modelled flood extent (scenario, not an observation) | 823 | literature_reported | model_extent (definition per source) | scenario maximum | nan | VERIFY: extent definition, AOI, scenario | quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation |

**Uncertainty per day [C07].** On 7 June the primary spatial draws give relative half-widths of
4 % for the area and
5 % for the volume. The deterministic nominal run lies below its own
interval: the medians are +5 % (area) and
+11 % (volume) above it, and the nominal area and volume fall below the p05 on the peak days
(T12b flags every such day). The interval is therefore not centred on the nominal run, and the reported central value is the
Monte-Carlo median with p05–p95, the nominal run in brackets. The mechanism is the one of §3.3 — the spatially correlated DEM perturbations open additional connections and add depth, an asymmetry that correlated error fields are known to produce (Cunha et al. 2012; Hawker et al. 2018) — but which error term carries most of the shift has not been attributed. The emulator sensitivity envelope (§3.3) is wider — newly inundated area
214–293 km²
(p25–p75 235–268 km²),
total water-surface area 758–837 km²
(Fig04, candles) — and represents a different distribution (parameter-space propagation); the two are never mixed. The daily
change of the newly inundated area (bars in Fig04) shows the filling on 6–7 June and the draining at 30–40 km² per day between
10 and 18 June.

**T12b.** The daily reconstructed series, every day 26 May - 10 July 2023 and region: Monte-Carlo median [p05-p95] of the 40 spatial draws (p95e, run on every post-breach day) for new inundation A, total water surface W_total and new-water volume V, with the deterministic nominal run (*_central_*) and a flag where it lies below its own MC p05. Before the breach A = V = 0 by construction. Daily reconstructed series, not daily observations.
*Evidence level: independent_physical.*

*Table T12b has 138 rows × 19 columns and is supplied as `tables/T12b.csv` (Supplementary Data); it is not printed here.*

**Reservoir side of the balance [C14] (context).** Under the sloped daily surface (outlet SWOT nodes, Nikopol press values, Rozumivka gauge)
the pool held 18.9 km³ on 5 June (design table at the same outlet level:
21.1 km³) and 4.5 km³ on 13 June, i.e.
14.7 km³ released in eight days, with the largest daily volume change of
-3225 hm³ on 7 June. The corresponding daily-mean effective release, −dV/dt + Q_in, is
40057 m³ s⁻¹ against a DniproHES inflow of
2730 m³ s⁻¹: a storage-balance estimate on a surface interpolated between three or
four level points, a daily mean and not an instantaneous breach discharge. Published estimates are different physical quantities of
the same order and are context, not validation: the *initial* breach flow of Yi et al. (2025) from a
gravimetry–altimetry–imagery discharge model is (5.7 ± 0.8) × 10⁴ m³ s⁻¹, the HEC-RAS scenario peaks of Kadam et al.
(2024) are 3.6 × 10⁴ m³ s⁻¹ (300 m breach) and 4.8 × 10⁴ m³ s⁻¹ (600 m), and Shumilova et al. (2025) model a release of
about 16.4 km³ over two weeks. The released volume itself is period- and hypsometry-dependent in the literature:
Yi et al. (2025) obtain 20.4 ± 1.4 km³ in 30 days from a pre-breach volume of 21.0 km³ (17.3 m), Vyshnevskyi et al.
(2023) give 19.8 km³ at 16.76 m from the operation rules, Monti et al. (2024) about 7.5 km³, and Lehnigk et al.
(2026) cite ∼8 km³; our 14.7 km³ over 5–13 June sits inside that spread, and the −9 % hypsometry gap below is of the
same size as the spread among the published pre-breach volumes (18.2–21.1 km³). The surface gradient across the
pool reached 5.0 m on 10 June. Downstream, the reconstructed new water stored above ground reaches its maximum on
9 June — 653 hm³ in the nominal run (corridor 453 hm³, MC median 512, p05–p95 488–539; Inhulets 200 hm³, MC median
199, p05–p95 190–207; T12) — a few per cent of the release, implying that most of the released volume was
transmitted downstream rather than stored on the mapped floodplain (Fig09, T21).
 The seamless-DEM hypsometry
lies below the design table at equal levels — −9 % at 17.5 m, −14 % at 13 m, −20 % at 11 m (T22; FigS07 rounds
these to −9 % at full pool and −15…−20 % at 11–13 m); the design table is undefined below 10 m — so the released
volume inherits this gap;
 its origin (datum, present morphology, the
underwater part of the seamless DEM, shoreline geometry, the original survey) is the subject of Paper 4, which reconstructs the
bowl on the historical bathymetry.

![Fig09](figures/Fig09_reservoir_balance.png)

**Fig09. Reservoir drawdown and the downstream flood.** (a) Water levels in one frame: SWOT outlet nodes, Nikopol post (press values), Rozumivka gauge, ICESat-2 passes, G-REALM, and the Kherson stage downstream. (b) Pool volume and water area under the sloped daily surface integrated on the seamless DEM inside the pre-breach pool polygon; Sentinel-1 water areas of Yi et al. (2025) for comparison (VERIFY). (c) Daily balance: daily-mean effective release from the pool (−dV/dt + Q_in; a storage-balance estimate, not an instantaneous breach discharge), DniproHES inflow and the reconstructed new water stored downstream (corridor + Inhulets). (d) Hypsometry of the seamless DEM against the design Table 19 (T21, T22; FigS07 for the relative gap).

**T21.** Kakhovka pool during the drawdown, per day: levels at the outlet (SWOT), Nikopol (press) and Rozumivka (gauge), surface gradient, pool water area and volume under the sloped surface (seamless DEM inside the pre-breach pool polygon), daily volume change, DniproHES inflow, the daily-mean effective release (-dV/dt + Q_in; not an instantaneous breach discharge), and the downstream new-water volume and total water surface (terrain reconstruction) with the Kherson stage.
*Evidence level: independent_physical.*

| date | H_outlet_m | H_nikopol_m | H_rozumivka_m | gradient_m | A_pool_km2 | V_pool_km3 | Q_in_dniprohes_m3s | kherson_stage_m | downstream_new_volume_hm3 | downstream_total_water_km2 | Q_release_eff_hm3_day | Q_release_eff_daily_mean_m3s | cum_released_km3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023-05-26 | 17.5319 | nan | 17.4936 | -0.0383369 | 2136.4 | 19.242 | 3370 | 0.6 | 0 | 540.6 | nan | nan | 0 |
| 2023-05-27 | 17.5319 | nan | 17.4786 | -0.0533369 | 2136.4 | 19.227 | 3330 | 0.61 | 0 | 538.9 | 302.7 | 3503 | 0.015 |
| 2023-05-28 | 17.5319 | nan | 17.3886 | -0.143337 | 2135.9 | 19.142 | 2700 | 0.6 | 0 | 538.3 | 318.3 | 3684 | 0.1 |
| 2023-05-29 | 17.5319 | nan | 17.3986 | -0.133337 | 2135.9 | 19.091 | 2550 | 0.61 | 0 | 545.9 | 271.3 | 3140 | 0.151 |
| 2023-05-30 | 17.5319 | nan | 17.4086 | -0.123337 | 2136 | 19.161 | 2610 | 0.62 | 0 | 544.2 | 155.5 | 1800 | 0.081 |
| 2023-05-31 | 17.5319 | nan | 17.3786 | -0.153337 | 2135.8 | 19.133 | 2540 | 0.59 | 0 | 539.3 | 247.5 | 2865 | 0.109 |
| 2023-06-01 | 17.5319 | nan | 17.3536 | -0.178337 | 2135.7 | 19.109 | 2470 | 0.6 | 0 | 545.6 | 237.4 | 2748 | 0.133 |
| 2023-06-02 | 17.5319 | nan | 17.3236 | -0.208337 | 2135.3 | 18.981 | 2570 | 0.65 | 0 | 550.9 | 350 | 4051 | 0.261 |
| 2023-06-03 | 17.5319 | nan | 17.2586 | -0.273337 | 2135 | 19.019 | 2190 | 0.64 | 0 | 547.1 | 151.2 | 1750 | 0.223 |
| 2023-06-04 | 17.5319 | nan | 17.0736 | -0.458337 | 2116.2 | 18.677 | 1660 | 0.54 | 0 | 492.4 | 485.4 | 5618 | 0.565 |
| 2023-06-05 | 17.5319 | nan | 17.0836 | -0.448337 | 2132.1 | 18.854 | 1750 | 0.54 | 0 | 509.4 | -25.8 | -299 | 0.388 |
| 2023-06-06 | 12.5031 | 16.6115 | 16.6936 | 4.19052 | 2091.8 | 15.905 | 1960 | 3.09 | 455.97 | 770.3 | 3118.3 | 36091 | 3.337 |
| 2023-06-07 | 12.0541 | 14.5815 | 15.2786 | 3.22445 | 2053.8 | 12.68 | 2730 | 5.66 | 633.74 | 847.7 | 3460.9 | 40057 | 6.562 |
| 2023-06-08 | 10.8918 | 13.2215 | 14.5286 | 3.63679 | 2012.3 | 10.428 | 1880 | 5.78 | 633.47 | 843.5 | 2414.4 | 27944 | 8.814 |
| 2023-06-09 | 10.0571 | 11.9115 | 13.7786 | 3.72144 | 1964.6 | 8.833 | 1730 | 5.37 | 653.23 | 800.7 | 1744.5 | 20191 | 10.409 |
| 2023-06-10 | 8.8238 | 10.3715 | 13.7936 | 4.96979 | 1915.7 | 7.604 | 1940 | 4.8 | 575.34 | 757 | 1396.6 | 16164 | 11.638 |
| 2023-06-11 | 7.7605 | 9.52151 | 13.8386 | 6.07809 | 1871.1 | 6.891 | 1930 | 4.24 | 467.56 | 739.3 | 879.8 | 10183 | 12.351 |
| 2023-06-12 | 6.69719 | 9.52151 | 13.8386 | 7.14139 | 1829.4 | 4.866 | 2450 | 3.64 | 345.66 | 720.4 | 2236.7 | 25888 | 14.376 |
| 2023-06-13 | 5.63389 | 9.52151 | 13.8386 | 8.2047 | 1820.8 | 4.51 | 2110 | 3.04 | 235.16 | 694.8 | 538.3 | 6230 | 14.732 |
| 2023-06-14 | 4.84312 | nan | nan | nan | nan | nan | 1720 | 2.55 | 154.91 | 667.6 | nan | nan | nan |
| 2023-06-15 | 4.20675 | nan | nan | nan | nan | nan | 1380 | 2.15 | 104.65 | 647.9 | nan | nan | nan |
| 2023-06-16 | 3.57037 | nan | nan | nan | nan | nan | 1580 | 1.8 | 62.47 | 624.7 | nan | nan | nan |
| 2023-06-17 | 3.14099 | nan | nan | nan | nan | nan | 1300 | 1.43 | 34.99 | 608.1 | nan | nan | nan |
| 2023-06-18 | 2.41642 | nan | nan | nan | nan | nan | 1140 | 1.15 | 16.21 | 589.5 | nan | nan | nan |
| 2023-06-19 | 2.0812 | nan | nan | nan | nan | nan | 1290 | 0.96 | 7.33 | 574.4 | nan | nan | nan |
| 2023-06-20 | 1.74599 | nan | nan | nan | nan | nan | 917 | 0.81 | 1.65 | 556.8 | nan | nan | nan |
| 2023-06-21 | 1.31013 | nan | nan | nan | nan | nan | 1170 | 0.74 | 0.22 | 538.9 | nan | nan | nan |
| 2023-06-22 | 0.874271 | nan | nan | nan | nan | nan | 1090 | 0.65 | 0.02 | 518.2 | nan | nan | nan |
| 2023-06-23 | 0.884321 | nan | nan | nan | nan | nan | 1330 | 0.58 | 0 | 492 | nan | nan | nan |
| 2023-06-24 | 0.894371 | nan | nan | nan | nan | nan | 1270 | 0.58 | 0 | 495.2 | nan | nan | nan |
| 2023-06-25 | 0.904421 | nan | nan | nan | nan | nan | 1090 | 0.56 | 0 | 489 | nan | nan | nan |
| 2023-06-26 | nan | nan | nan | nan | nan | nan | 1150 | 0.55 | 0 | 488.7 | nan | nan | nan |
| 2023-06-27 | nan | nan | nan | nan | nan | nan | 1560 | 0.45 | 0 | 483.5 | nan | nan | nan |
| 2023-06-28 | nan | nan | nan | nan | nan | nan | 1470 | 0.51 | 0 | 493.7 | nan | nan | nan |
| 2023-06-29 | nan | nan | nan | nan | nan | nan | 1140 | 0.51 | 0 | 501.9 | nan | nan | nan |
| 2023-06-30 | nan | nan | nan | nan | nan | nan | 1060 | 0.53 | 0 | 507 | nan | nan | nan |
| 2023-07-01 | 0.964721 | nan | nan | nan | nan | nan | 1050 | 0.48 | 0.01 | 512.9 | nan | nan | nan |
| 2023-07-02 | 0.964721 | nan | nan | nan | nan | nan | 582 | 0.43 | 0 | 489.1 | nan | nan | nan |
| 2023-07-03 | 0.964721 | nan | nan | nan | nan | nan | 921 | 0.41 | 0 | 482.5 | nan | nan | nan |
| 2023-07-04 | 0.964721 | nan | nan | nan | nan | nan | 1290 | 0.34 | 0 | 454.3 | nan | nan | nan |
| 2023-07-05 | nan | nan | nan | nan | nan | nan | 1310 | 0.33 | 0 | 425.2 | nan | nan | nan |
| 2023-07-06 | nan | nan | nan | nan | nan | nan | 1120 | 0.26 | 0 | 403.1 | nan | nan | nan |
| 2023-07-07 | nan | nan | nan | nan | nan | nan | 514 | 0.33 | 0 | 401.3 | nan | nan | nan |
| 2023-07-08 | nan | nan | nan | nan | nan | nan | 676 | 0.33 | 0 | 406.9 | nan | nan | nan |
| 2023-07-09 | nan | nan | nan | nan | nan | nan | 720 | 0.19 | 0 | 351.5 | nan | nan | nan |
| 2023-07-10 | nan | nan | nan | nan | nan | nan | 773 | 0.35 | 0 | 396.9 | nan | nan | nan |

*Compact view: 14 of 21 columns; the columns n_level_sources, A_table19_at_outlet_km2, phase, dV_pool_hm3, Q_in_hm3_day, area_semantics, Q_definition are in `tables/T21.csv`.*

**T22.** Pool hypsometry from the seamless DEM (level surface) against the design Table 19 (BS-77 levels + 0.185 m), with the relative difference dV/V_design and dA/A_design per level: the seamless DEM gives less volume at the same level: -8.5 % at the full-pool level (17.5 m), -14 % at 13 m, -20 % at 11 m (open question for Paper 4: reservoir bowl on the historical bathymetry).
*Evidence level: independent_physical.*

| level_evrf2019_m | A_dem_km2 | V_dem_km3 | level_bs77_m | A_table19_km2 | V_table19_km3 | dV_rel_pct | dA_rel_pct |
|---|---|---|---|---|---|---|---|
| 5 | 460.5 | 0.902 | 4.82 | 1443 | 6.95 | -87.0216 | -68.0873 |
| 5.5 | 541.1 | 1.151 | 5.32 | 1443 | 6.95 | -83.4388 | -62.5017 |
| 6 | 623.8 | 1.444 | 5.82 | 1443 | 6.95 | -79.223 | -56.7706 |
| 6.5 | 703.3 | 1.775 | 6.32 | 1443 | 6.95 | -74.4604 | -51.2613 |
| 7 | 777.7 | 2.145 | 6.82 | 1443 | 6.95 | -69.1367 | -46.1053 |
| 7.5 | 843.1 | 2.551 | 7.32 | 1443 | 6.95 | -63.295 | -41.5731 |
| 8 | 911.6 | 2.989 | 7.82 | 1443 | 6.95 | -56.9928 | -36.8261 |
| 8.5 | 975.6 | 3.462 | 8.32 | 1443 | 6.95 | -50.1871 | -32.3909 |
| 9 | 1045 | 3.966 | 8.82 | 1443 | 6.95 | -42.9353 | -27.5814 |
| 9.5 | 1127.8 | 4.509 | 9.32 | 1443 | 6.95 | -35.1223 | -21.8434 |
| 10 | 1247.7 | 5.101 | 9.82 | 1443 | 6.95 | -26.6043 | -13.5343 |
| 10.5 | 1414.2 | 5.765 | 10.32 | 1497.4 | 7.4108 | -22.2081 | -5.5563 |
| 11 | 1543.7 | 6.507 | 10.82 | 1582.4 | 8.1756 | -20.4095 | -2.44565 |
| 11.5 | 1644.8 | 7.305 | 11.32 | 1664.2 | 8.9848 | -18.696 | -1.16573 |
| 12 | 1747.9 | 8.153 | 11.82 | 1744.84 | 9.8368 | -17.1174 | 0.175374 |
| 12.5 | 1833.6 | 9.048 | 12.32 | 1820.63 | 10.7397 | -15.7519 | 0.71247 |
| 13 | 1923.2 | 9.987 | 12.82 | 1892 | 11.664 | -14.3776 | 1.64905 |
| 13.5 | 1997.4 | 10.969 | 13.32 | 1959.52 | 12.6272 | -13.132 | 1.93313 |
| 14 | 2028.2 | 11.976 | 13.82 | 2020.48 | 13.62 | -12.0705 | 0.382087 |
| 14.5 | 2049.9 | 12.996 | 14.32 | 2064.04 | 14.6392 | -11.2247 | -0.685064 |
| 15 | 2067 | 14.025 | 14.82 | 2098.12 | 15.682 | -10.5663 | -1.48323 |
| 15.5 | 2078.8 | 15.062 | 15.32 | 2124.72 | 16.7384 | -10.0153 | -2.16123 |
| 16 | 2089.4 | 16.104 | 15.82 | 2147.08 | 17.8048 | -9.55248 | -2.68644 |
| 16.5 | 2098.8 | 17.151 | 16.32 | 2165.88 | 18.8812 | -9.16361 | -3.09712 |
| 17 | 2109.1 | 18.203 | 16.82 | 2182.24 | 19.9676 | -8.83732 | -3.3516 |
| 17.5 | 2136.5 | 19.268 | 17.32 | 2198.88 | 21.064 | -8.5264 | -2.8369 |
| 18 | 2139.3 | 20.337 | 17.82 | 2215.88 | 22.1704 | -8.26958 | -3.45596 |

The modelled pool is checked, not validated, against the sensors inside the pre-breach pool polygon (T23, FigS08,
context): the modelled pool of 2132 km² on 5 June agrees with Sentinel-2 water at IoU 0.98 and lies within the published
pre-breach areas (2091 km² on 5 June from Sentinel-2, Magas et al. 2023; 2125 km² on 30 May, Yi et al. 2025; design
2155 km²), and the Sentinel-1 VH dark surface agrees with the model at IoU 0.98, 0.97, 0.93 and 0.85 on 1, 8, 9 and
13 June on the cells each scene observed. After about 13 June the VH dark surface also covers the exposed flats (2077 km²
on 21 June against 648 km² of Sentinel-2 water on 20 June), which we read as smooth wet mud rather than water — consistent
with the documented look-alike behaviour of smooth bare surfaces in C-band (Shen et al. 2019), although no study in the
literature reviewed measures it for wet reservoir sediment. Published remnant areas differ by definition rather than by
error: about 845 km² by 20 June from the decreases reported by Yi et al. (2025), 655.9 km² on 17 June in the state
estimate quoted by Novitskyi et al. (2024), 379.7 km² on 8 September including the restored channel (Magas et al. 2023),
and 1.63 km² of open water on 6 September with 110 km² still wet (Tsiupa et al. 2023). On the bed, Sentinel-2 surface
classes (T24) show dry bare sediment on 49 % of the observed pool on 5 July and reed or flooded vegetation on 36 % by
8 September (47 % of the flats exposed by 13 June) — the rapid recolonisation that field surveys report, with the number
of vascular plant taxa rising about sevenfold between June and October 2023 and mainly willow establishing (Kuzemko et
al. 2024, 2025; Vyshnevskyi 2024), and that index-based studies document from Sentinel-2 (Tutova et al. 2025; 135
thousand ha of vegetated bed in 2023–2024, Pichura and Potravka 2025). These are context for Paper 4, not claims of
this paper.

**T23.** Kakhovka pool water area by source and date inside the pre-breach pool polygon: MODEL (p95f sloped surface over the seamless DEM, terrain_reconstructed, 05-26..06-13), Sentinel-1 VH dark surface (per-date Otsu; open water or smooth wet mud), Sentinel-2 water (frozen p25 water3 and p15 crosscheck), with the observed fraction of the pool, IoU against the model on observed cells, and Yi et al. 2025 (literature_reported; DIGITISED from a figure of their S1 + S2 water mapping, not quoted in their text; figure number VERIFY). Areas count observed cells only; not observed is not dry. Maps: FigS08.
*Evidence level: cross_sensor.*

| date | source | semantics | water_km2 | observed_frac | iou_vs_model | model_km2_on_observed | vh_threshold_db | orbits | regime | mapped | yi2025_digitised_km2 | area_note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023-02-10 | S2_WATER3 | observed_S2 | 1835.9 | 0.878 | nan | nan | nan | nan | PRE_BREACH | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-05-06 | S2_WATER3 | observed_S2 | 2110.1 | 0.994 | nan | nan | nan | nan | PRE_BREACH | 1 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-05-11 | S2_WATER3 | observed_S2 | 1142.4 | 0.539 | nan | nan | nan | nan | PRE_BREACH | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-05-16 | S2_WATER3 | observed_S2 | 22.6 | 0.013 | nan | nan | nan | nan | PRE_BREACH | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-05-18 | S2_WATER3 | observed_S2 | 0 | 0 | nan | nan | nan | nan | PRE_BREACH | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-05-19 | S2_WATER3 | observed_S2 | 349.1 | 0.161 | nan | nan | nan | nan | PRE_BREACH | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-05-26 | MODEL | terrain_reconstructed | 2136.4 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-05-27 | MODEL | terrain_reconstructed | 2136.4 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-05-28 | MODEL | terrain_reconstructed | 2135.9 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-05-29 | MODEL | terrain_reconstructed | 2135.9 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-05-30 | MODEL | terrain_reconstructed | 2136 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-05-31 | MODEL | terrain_reconstructed | 2135.8 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-01 | MODEL | terrain_reconstructed | 2135.7 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-01 | S1 | observed_S1 | 1964.1 | 0.929 | 0.984 | 1978.9 | -17.25 | orb65_DES | nan | 1 | nan | VH dark surface = open water OR smooth wet mud, observed cells only; not a water area after ~06-13 |
| 2023-06-02 | MODEL | terrain_reconstructed | 2135.3 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-02 | S1 | observed_S1 | 36.1 | 0.017 | 0.986 | 36.3 | -17.75 | orb87_ASC | nan | 0 | nan | VH dark surface = open water OR smooth wet mud, observed cells only; not a water area after ~06-13 |
| 2023-06-03 | MODEL | terrain_reconstructed | 2135 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-04 | MODEL | terrain_reconstructed | 2116.2 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-04 | S1 | observed_S1 | 1495.4 | 0.714 | 0.973 | 1495.7 | -17.75 | orb116_ASC | nan | 1 | nan | VH dark surface = open water OR smooth wet mud, observed cells only; not a water area after ~06-13 |
| 2023-06-05 | MODEL | terrain_reconstructed | 2132.1 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-05 | S2_WATER3 | observed_S2 | 2106.2 | 0.994 | 0.984 | 2125 | nan | nan | PRE_BREACH | 1 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-06-06 | MODEL | terrain_reconstructed | 2091.8 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-07 | MODEL | terrain_reconstructed | 2053.8 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-08 | MODEL | terrain_reconstructed | 2012.3 | 1 | nan | nan | nan | nan | nan | nan | 2089.2 | pool water under the p95f sloped surface (whole pool) |
| 2023-06-08 | S1 | observed_S1 | 1704.6 | 0.791 | 0.967 | 1654.2 | -19.05 | orb167_DES | nan | 1 | 2089.2 | VH dark surface = open water OR smooth wet mud, observed cells only; not a water area after ~06-13 |
| 2023-06-08 | S2_CROSSCHECK | observed_S2 | 708.9 | 0.369 | nan | nan | nan | nan | nan | nan | 2089.2 | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-06-09 | MODEL | terrain_reconstructed | 1964.6 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-09 | S1 | observed_S1 | 2087.1 | 1 | 0.928 | 1963.8 | -18.75 | orb14_ASC | nan | 1 | nan | VH dark surface = open water OR smooth wet mud, observed cells only; not a water area after ~06-13 |
| 2023-06-10 | MODEL | terrain_reconstructed | 1915.7 | 1 | nan | nan | nan | nan | nan | nan | 1848.84 | pool water under the p95f sloped surface (whole pool) |
| 2023-06-11 | MODEL | terrain_reconstructed | 1871.1 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-12 | MODEL | terrain_reconstructed | 1829.4 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-13 | MODEL | terrain_reconstructed | 1820.8 | 1 | nan | nan | nan | nan | nan | nan | nan | pool water under the p95f sloped surface (whole pool) |
| 2023-06-13 | S1 | observed_S1 | 1937.5 | 0.929 | 0.851 | 1680.9 | -16.95 | orb65_DES | nan | 1 | nan | VH dark surface = open water OR smooth wet mud, observed cells only; not a water area after ~06-13 |
| 2023-06-13 | S2_CROSSCHECK | observed_S2 | 287.8 | 0.171 | nan | nan | nan | nan | nan | nan | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-06-14 | S1 | observed_S1 | 35.8 | 0.017 | nan | nan | -17.45 | orb87_ASC | nan | 0 | nan | VH dark surface = open water OR smooth wet mud, observed cells only; not a water area after ~06-13 |
| 2023-06-15 | S2_CROSSCHECK | observed_S2 | 140.2 | 0.077 | nan | nan | nan | nan | nan | nan | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-06-16 | S1 | observed_S1 | 1487 | 0.714 | nan | nan | -17.05 | orb116_ASC | nan | 1 | nan | VH dark surface = open water OR smooth wet mud, observed cells only; not a water area after ~06-13 |
| 2023-06-20 | S1 | observed_S1 | 1702.4 | 0.791 | nan | nan | -18.15 | orb167_DES | nan | 1 | 824.76 | VH dark surface = open water OR smooth wet mud, observed cells only; not a water area after ~06-13 |
| 2023-06-20 | S2_CROSSCHECK | observed_S2 | 647.6 | 1 | nan | nan | nan | nan | nan | nan | 824.76 | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-06-21 | S1 | observed_S1 | 2077.2 | 1 | nan | nan | -18.15 | orb14_ASC | nan | 1 | nan | VH dark surface = open water OR smooth wet mud, observed cells only; not a water area after ~06-13 |
| 2023-06-30 | S2_WATER3 | observed_S2 | 73.8 | 0.07 | nan | nan | nan | nan | BREACH_DRAWDOWN | 0 | 369.42 | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-07-05 | S2_WATER3 | observed_S2 | 720.9 | 0.932 | nan | nan | nan | nan | BREACH_DRAWDOWN | 1 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-07-25 | S2_WATER3 | observed_S2 | 0 | 0 | nan | nan | nan | nan | BREACH_DRAWDOWN | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-08-04 | S2_WATER3 | observed_S2 | 349.7 | 0.48 | nan | nan | nan | nan | BREACH_DRAWDOWN | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-08-06 | S2_WATER3 | observed_S2 | 0 | 0 | nan | nan | nan | nan | BREACH_DRAWDOWN | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-08-12 | S2_WATER3 | observed_S2 | 44.8 | 0.051 | nan | nan | nan | nan | BREACH_DRAWDOWN | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-08-17 | S2_WATER3 | observed_S2 | 314.8 | 0.533 | nan | nan | nan | nan | BREACH_DRAWDOWN | 1 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-08-27 | S2_WATER3 | observed_S2 | 58.8 | 0.07 | nan | nan | nan | nan | BREACH_DRAWDOWN | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-09-08 | S2_WATER3 | observed_S2 | 298.1 | 0.993 | nan | nan | nan | nan | POST_BREACH | 1 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-09-23 | S2_WATER3 | observed_S2 | 70.3 | 0.546 | nan | nan | nan | nan | POST_BREACH | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-09-28 | S2_WATER3 | observed_S2 | 115.3 | 0.543 | nan | nan | nan | nan | POST_BREACH | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-10-03 | S2_WATER3 | observed_S2 | 22.7 | 0.546 | nan | nan | nan | nan | POST_BREACH | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |
| 2023-11-07 | S2_WATER3 | observed_S2 | 138.5 | 0.545 | nan | nan | nan | nan | POST_BREACH | 0 | nan | S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only |

**T24.** Sentinel-2 k10e surface classes inside the pool per date (every 2023 date observing >= 50 % of the pool) and stratum: POOL; EXPOSED_BY_0613 (model: wet on 06-05, dry by 06-13); WET_ON_0613 (model: still wet on 06-13). km2 and % of the observed cells per class; frozen SWOT-DNIPRO p25 products, not re-classified. Context for the drawdown and recolonisation of the bed (FigS08 i-k).
*Evidence level: contextual.*

| date | regime | stratum | stratum_km2 | observed_km2 | observed_frac | OPEN_WATER_km2 | SHALLOW_OR_MIXED_WATER_km2 | WET_SEDIMENT_km2 | DRY_BARE_SEDIMENT_km2 | SPARSE_HERBACEOUS_km2 | DENSE_HERBACEOUS_km2 | REED_OR_FLOODED_VEGETATION_km2 | BUILT_HARD_SURFACE_km2 | AMBIGUOUS_km2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023-02-10 | PRE_BREACH | POOL | 2174.7 | 1908.6 | 0.878 | 1786.1 | 52.5 | 9.1 | 26.3 | 26.3 | 6.1 | 0.3 | 0 | 1.9 |
| 2023-02-10 | PRE_BREACH | EXPOSED_BY_0613 | 308.8 | 218.5 | 0.708 | 155.4 | 21.8 | 5.9 | 18.4 | 13.7 | 1.9 | 0.1 | 0 | 1.3 |
| 2023-02-10 | PRE_BREACH | WET_ON_0613 | 1820.2 | 1668.9 | 0.917 | 1629.5 | 28.2 | 1.5 | 5.4 | 3.7 | 0.2 | 0 | 0 | 0.4 |
| 2023-05-06 | PRE_BREACH | POOL | 2174.7 | 2162 | 0.994 | 2092.2 | 18.3 | 3.3 | 3.1 | 6.1 | 3.9 | 35 | 0 | 0 |
| 2023-05-06 | PRE_BREACH | EXPOSED_BY_0613 | 308.8 | 308.4 | 0.999 | 277.1 | 11 | 2.4 | 1.9 | 4.8 | 2.1 | 9.1 | 0 | 0 |
| 2023-05-06 | PRE_BREACH | WET_ON_0613 | 1820.2 | 1816.6 | 0.998 | 1810.6 | 2.6 | 0.5 | 0.3 | 0.6 | 0.3 | 1.8 | 0 | 0 |
| 2023-05-11 | PRE_BREACH | POOL | 2174.7 | 1171.4 | 0.539 | 1107.9 | 35 | 1.9 | 1.3 | 2.2 | 1.3 | 21.8 | 0 | 0.2 |
| 2023-05-11 | PRE_BREACH | EXPOSED_BY_0613 | 308.8 | 150.6 | 0.488 | 133 | 10 | 1.3 | 0.6 | 1.6 | 0.4 | 3.8 | 0 | 0.1 |
| 2023-05-11 | PRE_BREACH | WET_ON_0613 | 1820.2 | 996.9 | 0.548 | 972.2 | 22.3 | 0.4 | 0.1 | 0.2 | 0.1 | 1.4 | 0 | 0 |
| 2023-06-05 | PRE_BREACH | POOL | 2174.7 | 2161.9 | 0.994 | 2087.2 | 19.3 | 2.1 | 3.2 | 2.4 | 4.8 | 42.8 | 0 | 0.1 |
| 2023-06-05 | PRE_BREACH | EXPOSED_BY_0613 | 308.8 | 308.4 | 0.999 | 273.4 | 12.2 | 1.5 | 1.9 | 1.6 | 2.8 | 14.9 | 0 | 0.1 |
| 2023-06-05 | PRE_BREACH | WET_ON_0613 | 1820.2 | 1816.6 | 0.998 | 1810.3 | 2.7 | 0.2 | 0.3 | 0.2 | 0.4 | 2.6 | 0 | 0 |
| 2023-07-05 | BREACH_DRAWDOWN | POOL | 2174.7 | 2027.5 | 0.932 | 399.7 | 354.8 | 35.3 | 1000.6 | 148.1 | 27.3 | 49.4 | 0 | 12.3 |
| 2023-07-05 | BREACH_DRAWDOWN | EXPOSED_BY_0613 | 308.8 | 282.7 | 0.916 | 24.8 | 25.8 | 2.6 | 173.3 | 27.8 | 10.5 | 16.5 | 0 | 1.3 |
| 2023-07-05 | BREACH_DRAWDOWN | WET_ON_0613 | 1820.2 | 1715.2 | 0.942 | 374.6 | 328.1 | 32.4 | 822.1 | 117.3 | 12.9 | 16.9 | 0 | 10.9 |
| 2023-08-17 | BREACH_DRAWDOWN | POOL | 2174.7 | 1159.2 | 0.533 | 180.8 | 153 | 24.8 | 340.5 | 213.5 | 98.8 | 136.2 | 0 | 11.6 |
| 2023-08-17 | BREACH_DRAWDOWN | EXPOSED_BY_0613 | 308.8 | 143.3 | 0.464 | 11.2 | 8.1 | 1.9 | 50.1 | 20.7 | 14.8 | 36 | 0 | 0.4 |
| 2023-08-17 | BREACH_DRAWDOWN | WET_ON_0613 | 1820.2 | 1008.8 | 0.554 | 169.6 | 144.6 | 22.5 | 288.8 | 191.7 | 83 | 97.4 | 0 | 11.1 |
| 2023-09-08 | POST_BREACH | POOL | 2174.7 | 2158.4 | 0.993 | 183.1 | 132.7 | 73 | 356.8 | 376.5 | 218.7 | 785.4 | 0 | 32.2 |
| 2023-09-08 | POST_BREACH | EXPOSED_BY_0613 | 308.8 | 307.3 | 0.995 | 12.3 | 13.7 | 6.9 | 62.4 | 40.2 | 24.3 | 144.4 | 0 | 3.1 |
| 2023-09-08 | POST_BREACH | WET_ON_0613 | 1820.2 | 1814.1 | 0.997 | 170.7 | 118.7 | 65.2 | 292.9 | 334.1 | 180.3 | 623.3 | 0 | 29 |
| 2023-09-23 | POST_BREACH | POOL | 2174.7 | 1187.4 | 0.546 | 56.7 | 13.6 | 27.1 | 311 | 190 | 134.9 | 454 | 0 | 0.2 |
| 2023-09-23 | POST_BREACH | EXPOSED_BY_0613 | 308.8 | 201.4 | 0.652 | 2.9 | 1.6 | 2.8 | 49.5 | 24.2 | 22.5 | 97.8 | 0 | 0 |
| 2023-09-23 | POST_BREACH | WET_ON_0613 | 1820.2 | 946.5 | 0.52 | 51.6 | 11.8 | 23.9 | 260 | 164.1 | 93.9 | 341 | 0 | 0.1 |
| 2023-09-28 | POST_BREACH | POOL | 2174.7 | 1181.2 | 0.543 | 75.6 | 48.3 | 28.9 | 223.3 | 197.9 | 122.5 | 465.5 | 0 | 19.3 |
| 2023-09-28 | POST_BREACH | EXPOSED_BY_0613 | 308.8 | 196.5 | 0.637 | 4.9 | 5.6 | 3.5 | 35.2 | 24.9 | 22 | 98.8 | 0 | 1.7 |
| 2023-09-28 | POST_BREACH | WET_ON_0613 | 1820.2 | 945.1 | 0.519 | 68.3 | 42.4 | 25 | 187 | 170.9 | 81.7 | 352.3 | 0 | 17.5 |
| 2023-10-03 | POST_BREACH | POOL | 2174.7 | 1186.8 | 0.546 | 13.2 | 9.6 | 104.3 | 242.2 | 253.4 | 100.9 | 462.9 | 0 | 0.3 |
| 2023-10-03 | POST_BREACH | EXPOSED_BY_0613 | 308.8 | 201.3 | 0.652 | 0.9 | 0.9 | 9.1 | 38.9 | 33.1 | 21.4 | 97 | 0 | 0 |
| 2023-10-03 | POST_BREACH | WET_ON_0613 | 1820.2 | 945.9 | 0.52 | 10.2 | 8.5 | 94.5 | 202.3 | 215.9 | 63.9 | 350.4 | 0 | 0.3 |
| 2023-11-07 | POST_BREACH | POOL | 2174.7 | 1184.3 | 0.545 | 84.7 | 70.7 | 29.2 | 153.1 | 171.2 | 221.9 | 414 | 0 | 39.4 |
| 2023-11-07 | POST_BREACH | EXPOSED_BY_0613 | 308.8 | 200.6 | 0.649 | 5.9 | 9.5 | 3.2 | 32.4 | 27 | 52.1 | 65.4 | 0 | 5.1 |
| 2023-11-07 | POST_BREACH | WET_ON_0613 | 1820.2 | 944.3 | 0.519 | 76.6 | 60.7 | 25.7 | 119.7 | 141.5 | 141.2 | 344.8 | 0 | 34.1 |

*Compact view: 15 of 24 columns; the columns OPEN_WATER_pct, SHALLOW_OR_MIXED_WATER_pct, WET_SEDIMENT_pct, DRY_BARE_SEDIMENT_pct, SPARSE_HERBACEOUS_pct, DENSE_HERBACEOUS_pct, REED_OR_FLOODED_VEGETATION_pct, BUILT_HARD_SURFACE_pct, AMBIGUOUS_pct are in `tables/T24.csv`.*

**The design curve as the classical reference (context, no DEM).** Read on the design level–volume curve of the monograph
(Table 19; T27, FigS10) at the Rozumivka gauge — the only 2023 daily series, and the pool was level before the breach — the
reservoir held 13.5 km³ at 13.9 m on 8 February and
was filled by the April–May DniproHES release to 21.3 km³ at
17.62 m on 5 May (just below the highest forced level), held near 17.5 m through May and
lowered by ~0.4 m in the last ten days before the breach (20.1 km³ on 5 June; the filling
week by week, with the inflow and the outflow through the Kakhovka HPP implied by the design-curve balance, in T27c). After the
breach the surface sloped by up to 5.0 m, so the design curve, which assumes a level pool,
gives a range rather than a number: at the Rozumivka level the design-curve balance with the DniproHES inflow yields a daily-mean
effective release of 37811 m³ s⁻¹ on 7 June, the same order as the
40057 m³ s⁻¹ of the sloped-surface balance above; at the outlet level the
curve is undefined from 9 June (outlet below 10 m). "Outlet" here is the pool just above the dam (SWOT nodes at 0 km); the head
across the dam fell from 16.7 m on 31 May to 6.0 m
on 6 June and 1.5 m on 14 June (T27b, with the Kherson stage alongside).

**T27.** Design hypsometry of the Kakhovka reservoir from the Dnipro-reservoirs monograph (Table 19, Figs 13-15; transcribed from photographed pages in SWOT-DNIPRO): water level (historical Baltic, and +0.185 m to EVRF2019), surface area and volume of the whole pool and of the five reaches (dam - Babyne - Nikopol - Verkhnia Tarasivka - Blahovishchenka - Dnipro HPP) at 17 levels, with the design levels (NUF highest forced 17.5, NPG normal impoundment 16.0, UNS navigation drawdown 14.0, GMO dead volume 12.7 m) and the transcription check that the reaches add up to the total. Design data as published; nothing measured or fitted here. FigS10.
*Evidence level: contextual.*

| level_bs_m | level_evrf2019_m | A_km2 | V_km3 | design_level | V_reach1_km3 | V_reach2_km3 | V_reach3_km3 | V_reach4_km3 | V_reach5_km3 | V_reaches_sum_km3 | reach_sum_minus_total_km3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 18 | 18.185 | 2222 | 22.57 | nan | nan | nan | nan | nan | nan | nan | nan |
| 17.5 | 17.685 | 2205 | 21.46 | NUF - highest forced level | nan | nan | nan | nan | nan | nan | nan |
| 17 | 17.185 | 2188 | 20.36 | nan | nan | nan | nan | nan | nan | nan | nan |
| 16.5 | 16.685 | 2172 | 19.27 | nan | 6.9 | 5.64 | 2.79 | 3.56 | 0.38 | 19.27 | -0 |
| 16 | 16.185 | 2155 | 18.19 | NPG - normal impoundment level | 6.65 | 5.38 | 2.6 | 3.21 | 0.35 | 18.19 | 0 |
| 15.5 | 15.685 | 2133 | 17.12 | nan | 6.4 | 5.12 | 2.42 | 2.86 | 0.32 | 17.12 | 0 |
| 15 | 15.185 | 2110 | 16.06 | nan | 6.16 | 4.85 | 2.24 | 2.52 | 0.29 | 16.06 | 0 |
| 14.5 | 14.685 | 2077 | 15.01 | nan | 5.92 | 4.59 | 2.06 | 2.18 | 0.26 | 15.01 | 0 |
| 14 | 14.185 | 2041 | 13.98 | UNS - navigation drawdown level | 5.68 | 4.32 | 1.88 | 1.87 | 0.23 | 13.98 | 0 |
| 13.5 | 13.685 | 1984 | 12.98 | nan | 5.44 | 4.06 | 1.71 | 1.57 | 0.2 | 12.98 | 0 |
| 13 | 13.185 | 1916 | 12 | nan | 5.2 | 3.8 | 1.55 | 1.27 | 0.18 | 12 | 0 |
| 12.7 | 12.885 | 1876 | 11.44 | GMO - dead-volume level | 5.06 | 3.65 | 1.45 | 1.12 | 0.16 | 11.44 | -0 |
| 12 | 12.185 | 1774 | 10.15 | nan | 4.73 | 3.29 | 1.22 | 0.78 | 0.13 | 10.15 | 0 |
| 11.5 | 11.685 | 1693 | 9.28 | nan | 4.5 | 3.03 | 1.06 | 0.58 | 0.11 | 9.28 | 0 |
| 11 | 11.185 | 1613 | 8.46 | nan | 4.28 | 2.78 | 0.92 | 0.4 | 0.09 | 8.47 | 0.01 |
| 10.5 | 10.685 | 1528 | 7.67 | nan | 4.04 | 2.52 | 0.78 | 0.26 | 0.07 | 7.67 | 0 |
| 10 | 10.185 | 1443 | 6.95 | nan | 3.82 | 2.27 | 0.65 | 0.15 | 0.06 | 6.95 | 0 |

**T27c.** The filling of the Kakhovka reservoir in spring 2023, week by week on the design curve: Rozumivka level (EVRF2019), design volume and area, weekly change, DniproHES inflow (mean discharge and volume) and the outflow through the Kakhovka HPP implied by the design-curve balance. From ~14.0 m / 13.5 km3 in early February to 17.6 m / 21.3 km3 on 5 May (7.9 km3 stored out of 22.7 km3 of inflow), held at ~17.5 m through May, then ~0.4 m lower in the last ten days before the breach. Design data + gauge + releases; no DEM.
*Evidence level: independent_physical.*

| week | H_rozumivka_m | H_grealm_m | H_icesat2_m | H_outlet_swot_m | V_design_km3 | A_design_km2 | Q_in_dniprohes_m3s | Q_in_km3 | Q_out_design_m3s | n_days | dV_week_km3 | dH_week_m | Q_out_design_km3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023-01-30 | 14.09 | nan | nan | nan | 13.79 | 2030 | 1604 | 0.69 | 2256 | 5 | nan | nan | nan |
| 2023-02-06 | 14.03 | nan | nan | nan | 13.66 | 2022.71 | 2042.86 | 1.24 | 2274.57 | 7 | -0.13 | -0.06 | 1.37 |
| 2023-02-13 | 14.17 | nan | nan | nan | 13.95 | 2038.14 | 2188.57 | 1.32 | 1460.71 | 7 | 0.29 | 0.14 | 1.03 |
| 2023-02-20 | 14.34 | nan | nan | nan | 14.29 | 2051.86 | 2080 | 1.26 | 1450.14 | 7 | 0.34 | 0.17 | 0.92 |
| 2023-02-27 | 14.56 | nan | nan | nan | 14.75 | 2067.71 | 2181.43 | 1.32 | 1568 | 7 | 0.46 | 0.22 | 0.86 |
| 2023-03-06 | 14.66 | nan | nan | nan | 14.96 | 2075 | 1928.57 | 1.17 | 1538.43 | 7 | 0.21 | 0.1 | 0.96 |
| 2023-03-13 | 14.68 | nan | nan | nan | 15 | 2076.71 | 2117.14 | 1.28 | 1892.14 | 7 | 0.04 | 0.02 | 1.24 |
| 2023-03-20 | 14.78 | nan | nan | nan | 15.2 | 2083.29 | 2221.43 | 1.34 | 1839.57 | 7 | 0.2 | 0.1 | 1.14 |
| 2023-03-27 | 14.94 | nan | nan | nan | 15.54 | 2093.71 | 2541.43 | 1.54 | 1916.14 | 7 | 0.34 | 0.16 | 1.2 |
| 2023-04-03 | 15.31 | nan | nan | nan | 16.32 | 2115.43 | 3292.86 | 1.99 | 2089.29 | 7 | 0.78 | 0.37 | 1.21 |
| 2023-04-10 | 15.82 | nan | nan | nan | 17.41 | 2138.71 | 4535.71 | 2.74 | 1981.14 | 7 | 1.09 | 0.51 | 1.65 |
| 2023-04-17 | 16.5 | nan | nan | nan | 18.86 | 2165.71 | 5138.57 | 3.11 | 3605.57 | 7 | 1.45 | 0.68 | 1.66 |
| 2023-04-24 | 16.93 | nan | nan | nan | 19.81 | 2179.86 | 4514.29 | 2.73 | 1978 | 7 | 0.95 | 0.43 | 1.78 |
| 2023-05-01 | 17.49 | nan | nan | nan | 21.04 | 2198.57 | 4175.71 | 2.53 | 3393.71 | 7 | 1.23 | 0.56 | 1.3 |
| 2023-05-08 | 17.53 | 17.48 | nan | nan | 21.12 | 2199.57 | 3320 | 2.01 | 3029 | 7 | 0.08 | 0.04 | 1.93 |
| 2023-05-15 | 17.47 | 17.5 | nan | nan | 21 | 2197.86 | 3417.14 | 2.07 | 3726.14 | 7 | -0.12 | -0.06 | 2.19 |
| 2023-05-22 | 17.46 | nan | 17.22 | 17.53 | 20.96 | 2197.43 | 3331.43 | 2.01 | 3477.14 | 7 | -0.04 | -0.01 | 2.05 |
| 2023-05-29 | 17.31 | 17.47 | 17.11 | 17.53 | 20.64 | 2192.57 | 2370 | 1.43 | 3512.14 | 7 | -0.32 | -0.15 | 1.75 |
| 2023-06-05 | 17.08 | nan | nan | 17.53 | 20.14 | 2185 | 1750 | 0.15 | 1495 | 1 | -0.5 | -0.23 | 0.65 |

**T27b.** The observed 2023 levels, 1 February - 10 July, read on the design curve of T27 (level - 0.185 m -> historical Baltic): before the breach the Rozumivka gauge 80959 (terms 08/20 averaged; the only 2023 daily series; the pool was level, so one gauge reads the whole pool), with G-REALM, ICESat-2 and the SWOT outlet as checks; from 26 May the p95f daily levels (the pre-breach outlet value is HELD, not observed daily -- flagged). 'Outlet' = SWOT nodes at 0 km, the pool just above the dam; for comparison the SWOT level 0.5 km below the dam (p59/p60) and the Kherson gauge 80805, with the head across the dam and pool-minus-Kherson. Design volume and area at the Rozumivka and at the outlet level (during the drawdown the surface sloped by up to 4 m, so the two readings bracket the pool), the volume released from the design curve, and the storage balance with the DniproHES inflow: Q_out = Q_in - dV_design/dt = the outflow through the Kakhovka HPP before the breach and the daily-mean effective release after it (design-curve counterpart of T21; a residual without lateral inflow, evaporation or withdrawals). NaN once the outlet is below 10.0 m, the lowest level of Table 19. Context for Paper 4.
*Evidence level: independent_physical.*

*Table T27b has 160 rows × 40 columns and is supplied as `tables/T27b.csv` (Supplementary Data); it is not printed here.*

**The drawdown of the pool seen from orbit (context, no claim).** Maps of the emptying pool from three sources are in the
supplement (T23–T26, FigS08–FigS09): the modelled pool under the sloped surface, the Sentinel-1 VH dark surface and the frozen
Sentinel-2 index and class products of the SWOT-DNIPRO chain (p25, not re-classified here). Sentinel-2 agrees with the modelled full pool on 5 June at IoU
0.98; Sentinel-1 agrees at
0.98 on 1 June, 0.97 on 8 June and
0.85 on 13 June, after which the VH dark surface is open water *or* smooth wet
sediment and is no longer a water area (1702 km² dark against
648 km² of Sentinel-2 water on 20 June). By 8 September reed or flooded
vegetation covers 47 % of the bed exposed first
(6–13 June) and 34 % of the rest (T24; the seven
index statistics per stratum in T25–T26). These are observations of the bed, not results of this paper; they are the hand-over to
Paper 4.

**T26.** Sentinel-2 index display classes inside the pool per date, stratum and index: km2 and % of observed cells per class (bins: NDWI/MNDWI/AWEIsh -0.3/0/0.3; NDVI 0.15/0.3/0.5; NDMI/BSI/NDTI -0.1/0.1). Display classes, not a classifier (the frozen classifier is k10e, T24). FigS09.
*Evidence level: contextual.*

*Table T26 has 825 rows × 7 columns and is supplied as `tables/T26.csv` (Supplementary Data); it is not printed here.*

**T25.** Sentinel-2 index statistics inside the pool per date, stratum and index (NDVI, NDWI, MNDWI, NDMI, BSI, AWEIsh, NDTI; offset-corrected reflectance, 20 m, frozen p25 stacks): observed km2 and fraction, mean, std and percentiles p10/p25/p50/p75/p90 over observed cells. Strata as T24. FigS09.
*Evidence level: contextual.*

*Table T25 has 231 rows × 13 columns and is supplied as `tables/T25.csv` (Supplementary Data); it is not printed here.*

### 4.2 Raw agreement with Sentinel-1 on the observation domain [C04]

On 9 June, in the p42 floodplain domain and on the Sentinel-1 footprint, the reconstruction allows
136 km² of new water and Sentinel-1
reports 201 km²; they share
52 km² (POD
0.26, FAR
0.62, CSI
0.18). Of the
150 km² that Sentinel-1 reports and
the reconstruction does not, 148 km²
lie on normally-wet cells. The raw agreement is therefore low, and most apparent terrain misses occur in predefined normally-wet
or vegetation-dominated cells where SAR dark-water onset is not an appropriate binary reference; the conditional POD outside the
normally-wet class is 0.96,
a diagnostic conditional agreement, not a corrected POD. On 13 June the raw POD is
0.15 and the conditional POD
0.88. After 18 June the
Sentinel-1 "new water" outside the floodplain domain (155 km²
on 21 June in the corridor) is scattered on fields and sand while the gauge is at its pre-breach level and the reconstruction is at 3 km²: these detections are not supported as connected breach-induced inundation by the
available terrain and water-surface constraints. Their pattern — fields and sand far above any water surface of the
event — is consistent with a known C-band look-alike behaviour (smooth or wet bare surfaces and shadow scatter like
water; Shen et al. 2019), but whether they are non-water, local ponding after rain or water outside the assumed
connectivity is not tested here (§4.3).
 The large-scale
recession seen by Sentinel-1 inside the floodplain (T19) follows the reconstruction and the gauge (Fig04).

**T19.** Per-acquisition-date new water (not water before the breach) inside the Sentinel-1 observable domain, with coverage; S2 only where >= 30 % of the region was cloud-free; estuary zone on its own grid.
*Evidence level: cross_sensor.*

*Table T19 has 77 rows × 9 columns and is supplied as `tables/T19.csv` (Supplementary Data); it is not printed here.*

### 4.3 The disagreement is mechanistic [C05]

On 9 June the two zones together give A = 59 km², B (terrain only) =
120 km² and C (Sentinel-1 only) = 261 km²
(T14, Fig05). B lies entirely below the reconstructed surface and is dominated by surfaces the dark-water rule cannot see:
43 km² trees, 20 km²
wetland and 23 km² built-up. C splits by ground elevation:
167 km² below the surface and
34 km² within 2 m above it, of which
173 km² are normally-wet reed beds — the submergence of emergent
vegetation, a depth signal; and 54 km² at least 5 m above the
surface, on cropland and grass: S1-only detections that are topographically inconsistent with the reconstructed connected water
surface. Whether they are smooth non-water surfaces, radar shadow, local ponding after rain, water outside the assumed
connectivity, timing or registration effects is not tested here; what §4.4 tests is whether a DEM error could explain them.

![Fig05](figures/Fig05_disagreement_ontology.png)

**Fig05. Disagreement ontology on 2023-06-09.** (a) Agreement between the reconstruction and Sentinel-1 on the S1 footprint: A both, B terrain only, C S1 only split by ground elevation relative to the reconstructed surface. (b) B by WorldCover class: forest, wetland and built-up dominate (SAR blind spots). (c) C by ground elevation: cells below or within 2 m of the surface are mostly normally-wet reed beds where S1 dark-water onset is a submergence signal; S1-only detections on ground ≥ 5 m above the reconstructed connected water surface are topographically unsupported (Fig08). Km² are mapped areas (T14).

### 4.4 ICESat-2 altimetric consistency [C06]

Where Sentinel-1 reports water at least 2 m above the reconstructed surface, the seamless DEM agrees with night ICESat-2 ground
heights to +0.03 m (p10–p90
-0.31 to
+0.64 m, n =
3205 segments) in the delta and
+0.02 m (n =
1687) in the floodway; the ICESat-2 ground lies
+13.5 m above the surface in the delta and
essentially no segment (0.0%) lies below it.
The available ICESat-2 observations therefore provide no evidence for a DEM bias large enough to explain those S1-only
detections; they support the reading of §4.3 without proving it, because the tracks (listed with their dates in T15) sample
the category along lines, not every cell of the 54 km². Where the
reconstruction and Sentinel-1 agree, 99.4% of the segments lie
below the surface (T15, Fig08). This is a track-based consistency check of the DEM and the surface, not a validation of the map.

![Fig08](figures/Fig08_icesat2_consistency.png)

**Fig08. ICESat-2 altimetric consistency check.** Seamless DEM minus night ICESat-2 ATL08 ground height (median, p10–p90) per agreement category of 2023-06-09, with the ground elevation relative to the reconstructed surface and the share of segments below it (n segments and tracks in T15): where S1 reports water ≥ 2 m above the surface the DEM agrees with the altimetry to within a few decimetres along the tracks and essentially no segment lies below the water, so the available ICESat-2 observations give no evidence for a DEM bias large enough to explain those S1-only detections. A track-based consistency check that supports this reading; it does not sample every cell and does not validate the map.

### 4.5 Water-surface input and DEM accuracy [C06]

After re-anchoring to the Kherson-local closure the SWOT input agrees with the gauge at day level (median
+0.01 m, NMAD 0.07 m; during the rise and peak
+0.10 m over 7 days),
consistent with Paper 1's +1.9 cm through the breach fortnight. The DEM error model of the Monte-Carlo is the class table of
Paper 2 (T18).

### 4.6 Three areas, three definitions [C08]

For the same corridor the 9 June Sentinel-1 scene contains 300 km²
of new dark water (observed_S1), the label recipe (water on ≥ 2 of 3 peak dates) 168 km²,
the U-Net arm U2b 241 km² (mapped_UNet), and the
reconstruction 196 km² on 9 June and
247 km² at the reconstructed areal maximum (terrain_reconstructed). The label contract
is a persistence product and therefore describes the regime around 13 June. The operational figures — UNOSAT product 3616,
~620 km² of satellite-detected flooded land cumulative over 6–9 June with the pre-existing water as a separate class,
preliminary and not field-validated; product 3623, ~180 km² on 13 June against the reference water of 3/5 June (T16,
literature_reported) — are flooded *land*, closer in kind to the newly inundated area than to the total water-surface
area, and differ in AOI, temporal semantics (cumulative vs snapshot) and reference water; they are context, not validation.
Two peer-reviewed mappings of the same flood carry their own definitions as well: Yailymov et al. (2025) count 473 km² of
flooded land as of 9 June across the Kherson region including the Inhulets valley, relative to a pre-flood water map of
5 June, of which 294 km² are wetlands — the class in which this paper's submergence category lives — and Zuo et al. (2024)
follow the total water-surface area at 300 m resolution, largest around 9 June. Neither is the corridor snapshot of this
paper. Our reading is that the large wetland share of Yailymov et al. points the same way as §4.3, where most Sentinel-1
"new water" on 9 June lies on normally-wet reed beds. T16 carries the area, quantity and temporal semantics of every row.

### 4.7 Inhulets backwater [C03]

The Inhulets valley has its own SWOT nodes and responds as backwater — Lehnigk et al. (2026) trace the flood pulse at least 150 km up the tributary, and confluence backwater is a known control on tributary stage and flood-wave timing (De Paiva et al. 2013): on 9 June the reconstruction allows
20 km² against
36 km² seen by Sentinel-1
(POD 0.40, CSI
0.34); the p42 HAND rule, which measures
HAND to the Dnipro, is not applicable there. The valley is never added to the Dnipro reach.

### 4.8 Surface context [C12]

RF20 reaches an overall agreement of 0.940 with WorldCover
in spatial-block cross-validation (macro F1 0.943), wetland/reed F1
0.953 and built-up F1 0.938;
the frame transfers B1→B2 and B2→B1 reach macro F1 0.906 and
0.932 (T09), which speaks to stability across spatial frames more than the
overall agreement does. These are agreement numbers against the training reference, not an independent land-cover accuracy.

### 4.9 What EO inputs recover under weak labels [C09–C11]

*Label effect* (Fig03; paired differences in T06 and T07b). At fixed inputs, U2 predicts 15.3 km² of flood on
the test-block REFERENCE_WATER under v002 and 1.3 km² under
v003_A (paired difference -13.4 km²,
95 % -29.5 to
-2.5), while EVENT_FLOOD recall changes by
-0.028
(-0.042 to
+0.006), an interval that crosses zero: no statistically
resolved change in recall under this bootstrap design, which is not the same as "unchanged". Global F1 is not comparable across
label sets.
*Terrain as input.* On v002, adding HAND to U0d changes the predicted-flood burden on unlabelled cropland by
-9.6 km²
(-14.8 to
-5.1) and the
built-up false positives by +0.37 km²; land cover as an
input (U1) retains 78%–91% of the U0d candidate area — context,
not a veto. None of the audited cropland-associated candidates showed positive evidence consistent with breach-induced
inundation under the available SAR, optical and terrain constraints (T08). *Pre-event water as input.* U2b reduces the flood on
reference water by a further -0.62 km²
(-1.28 to
-0.13); this comparison is not
independent, because pre-event water information also contributes to the label ontology (label leakage), and U2b is reported as
a diagnostic upper bound, not as a best model.

![Fig03](figures/Fig03_unet_experiment.png)

**Fig03. U-Net weak-label experiment.** (a, b) Flood-state map of arm U2b (labels v003_A) on frames B1 and B2 at its frozen validation threshold: predicted flood on labelled EVENT_FLOOD, on REFERENCE_WATER (attribution candidates) and elsewhere; TEST blocks outlined. (c) Paired differences on identical spatial blocks (median, 95 % block-bootstrap interval): the HAND and RF20 inputs on v002, the label effect v002 → v003_A at fixed inputs, and the W_pre input (grey: not independent, W_pre is a label ingredient). All numbers are agreement with weak reference labels (T06, T07b).

**T06.** Paired arm comparisons (B minus A) on identical spatial blocks, 2000 resamples, 95 % intervals.
*Evidence level: weak_label_agreement.*

*Table T06 has 140 rows × 9 columns and is supplied as `tables/T06.csv` (Supplementary Data); it is not printed here.*

**T07b.** Paired differences (B minus A) of the v003_A attribution endpoints across label sets and inputs.
*Evidence level: weak_label_agreement.*

| A | B | endpoint | median | lo | hi | excludes_zero | independent |
|---|---|---|---|---|---|---|---|
| U2_B1B2_v1 | U2_B1B2_v003A | R_pred_on_reference_water_km2 | -13.4128 | -29.5266 | -2.45226 | True | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | R_pred_on_reference_water_wpre_water_km2 | -13.0828 | -29.1855 | -2.397 | True | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | R_pred_on_reference_water_wpre_dry_km2 | -0.2549 | -0.71302 | -0.0164 | True | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | R_frac_reference_water_above_thr | -0.09737 | -0.14481 | -0.02741 | True | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | R_reference_water_evaluated_km2 | 0 | 0 | 0 | False | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | E_recall_event_flood | -0.0276 | -0.0416 | 0.0062 | False | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | E_FN_km2 | 1.13785 | -0.0156 | 3.19471 | False | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | E_reference_km2 | 0 | 0 | 0 | False | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | L_FP_on_land_km2 | -1.96795 | -5.05441 | 0.06957 | False | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | L_FP_rate_land | -0.00394 | -0.01145 | 0.00013 | False | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | L_evaluated_km2 | 0 | 0 | 0 | False | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | U_pred_on_unknown_km2 | -5.7961 | -22.7978 | 20.9206 | False | weak-label |
| U2_B1B2_v1 | U2_B1B2_v003A | U_evaluated_km2 | 0 | 0 | 0 | False | weak-label |
| U2_B1B2_v003A | U2b_B1B2_v003A | R_pred_on_reference_water_km2 | -0.62125 | -1.27661 | -0.13365 | True | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | R_pred_on_reference_water_wpre_water_km2 | -0.65865 | -1.30767 | -0.1628 | True | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | R_pred_on_reference_water_wpre_dry_km2 | 0.0304 | -0.0138 | 0.112 | False | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | R_frac_reference_water_above_thr | -0.00428 | -0.01202 | -0.00102 | True | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | R_reference_water_evaluated_km2 | 0 | 0 | 0 | False | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | E_recall_event_flood | 0.0112 | -0.01641 | 0.0162 | False | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | E_FN_km2 | -0.46985 | -1.39841 | 0.12742 | False | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | E_reference_km2 | 0 | 0 | 0 | False | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | L_FP_on_land_km2 | 0.6138 | -0.24033 | 1.91501 | False | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | L_FP_rate_land | 0.00126 | -0.00047 | 0.00437 | False | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | L_evaluated_km2 | 0 | 0 | 0 | False | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | U_pred_on_unknown_km2 | -7.63045 | -29.3419 | 4.38763 | False | no (W_pre circularity) |
| U2_B1B2_v003A | U2b_B1B2_v003A | U_evaluated_km2 | 0 | 0 | 0 | False | no (W_pre circularity) |
| U0d_B1B2_v003A | U2_B1B2_v003A | R_pred_on_reference_water_km2 | 0.0798 | -0.28572 | 0.62324 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | R_pred_on_reference_water_wpre_water_km2 | 0.11005 | -0.26244 | 0.64036 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | R_pred_on_reference_water_wpre_dry_km2 | -0.027 | -0.10731 | 0.017 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | R_frac_reference_water_above_thr | 0.00055 | -0.00258 | 0.00404 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | R_reference_water_evaluated_km2 | 0 | 0 | 0 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | E_recall_event_flood | 0.0004 | -0.0066 | 0.0367 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | E_FN_km2 | -0.01515 | -0.40713 | 0.3468 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | E_reference_km2 | 0 | 0 | 0 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | L_FP_on_land_km2 | -0.2599 | -1.16622 | 0.46895 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | L_FP_rate_land | -0.00054 | -0.00282 | 0.00099 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | L_evaluated_km2 | 0 | 0 | 0 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | U_pred_on_unknown_km2 | 0.2795 | -14.3863 | 24.7901 | False | weak-label |
| U0d_B1B2_v003A | U2_B1B2_v003A | U_evaluated_km2 | 0 | 0 | 0 | False | weak-label |

**T08.** Cropland-associated SAR candidates (p89 audit): groups A (water before the breach), B (wet/irrigated agriculture), D (unresolved / likely SAR artefact) per arm and frame.
*Evidence level: weak_label_agreement.*

| arm | frame | group | group_name | n | km2 | area_semantics |
|---|---|---|---|---|---|---|
| U0d | B1 | A | PRE_EXISTING_OR_IRRIGATION_WATER | 36 | 6.122 | mapped_UNet |
| U0d | B1 | B | WET_OR_IRRIGATED_AGRICULTURE | 7 | 1.952 | mapped_UNet |
| U0d | B1 | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 4 | 0.05 | mapped_UNet |
| U0d | B2 | A | PRE_EXISTING_OR_IRRIGATION_WATER | 10 | 1.17 | mapped_UNet |
| U0d | B2 | B | WET_OR_IRRIGATED_AGRICULTURE | 32 | 6.069 | mapped_UNet |
| U0d | B2 | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 27 | 3.815 | mapped_UNet |
| U0z | B1 | A | PRE_EXISTING_OR_IRRIGATION_WATER | 22 | 1.955 | mapped_UNet |
| U0z | B1 | B | WET_OR_IRRIGATED_AGRICULTURE | 2 | 0.42 | mapped_UNet |
| U0z | B1 | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 3 | 0.036 | mapped_UNet |
| U0z | B2 | A | PRE_EXISTING_OR_IRRIGATION_WATER | 9 | 1.199 | mapped_UNet |
| U0z | B2 | B | WET_OR_IRRIGATED_AGRICULTURE | 31 | 6.788 | mapped_UNet |
| U0z | B2 | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 23 | 5.364 | mapped_UNet |
| U1 | B1 | A | PRE_EXISTING_OR_IRRIGATION_WATER | 34 | 5.555 | mapped_UNet |
| U1 | B1 | B | WET_OR_IRRIGATED_AGRICULTURE | 8 | 1.506 | mapped_UNet |
| U1 | B1 | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 3 | 0.1 | mapped_UNet |
| U1 | B2 | A | PRE_EXISTING_OR_IRRIGATION_WATER | 10 | 1.341 | mapped_UNet |
| U1 | B2 | B | WET_OR_IRRIGATED_AGRICULTURE | 32 | 9.008 | mapped_UNet |
| U1 | B2 | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 20 | 4.637 | mapped_UNet |
| U2 | B1 | A | PRE_EXISTING_OR_IRRIGATION_WATER | 39 | 2.792 | mapped_UNet |
| U2 | B1 | B | WET_OR_IRRIGATED_AGRICULTURE | 4 | 0.311 | mapped_UNet |
| U2 | B1 | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 1 | 0.164 | mapped_UNet |
| U2 | B2 | A | PRE_EXISTING_OR_IRRIGATION_WATER | 11 | 0.608 | mapped_UNet |
| U2 | B2 | B | WET_OR_IRRIGATED_AGRICULTURE | 28 | 3.596 | mapped_UNet |
| U2 | B2 | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 24 | 2.985 | mapped_UNet |
| U0d | ALL | A | PRE_EXISTING_OR_IRRIGATION_WATER | 46 | 7.292 | mapped_UNet |
| U0d | ALL | B | WET_OR_IRRIGATED_AGRICULTURE | 39 | 8.02 | mapped_UNet |
| U0d | ALL | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 31 | 3.865 | mapped_UNet |
| U0z | ALL | A | PRE_EXISTING_OR_IRRIGATION_WATER | 31 | 3.154 | mapped_UNet |
| U0z | ALL | B | WET_OR_IRRIGATED_AGRICULTURE | 33 | 7.208 | mapped_UNet |
| U0z | ALL | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 26 | 5.4 | mapped_UNet |
| U1 | ALL | A | PRE_EXISTING_OR_IRRIGATION_WATER | 44 | 6.896 | mapped_UNet |
| U1 | ALL | B | WET_OR_IRRIGATED_AGRICULTURE | 40 | 10.515 | mapped_UNet |
| U1 | ALL | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 23 | 4.737 | mapped_UNet |
| U2 | ALL | A | PRE_EXISTING_OR_IRRIGATION_WATER | 50 | 3.4 | mapped_UNet |
| U2 | ALL | B | WET_OR_IRRIGATED_AGRICULTURE | 32 | 3.907 | mapped_UNet |
| U2 | ALL | D | UNRESOLVED_OR_LIKELY_SAR_ARTIFACT | 25 | 3.149 | mapped_UNet |

### 4.10 Block-size sensitivity [C13]

U2 on v003_A gives global F1 0.931 on the frozen 10 km split,
0.956 at 7.5 km, 0.937 at 15 km and
0.876 at 20 km (each with its own test geography and interval, T20, FigS05); a 5 km split
leaves no validation patch inside the buffers. The tested range is meaningful because every block is larger than the local
object scale (fields, reed beds), comparable to or larger than the spatial correlation length of the change channels, and larger
than the 5.12 km patch plus buffers (the receptive footprint); across it the signs of the paired comparisons are unchanged
(Roberts et al. 2017; Valavi et al. 2019). The conclusions of §4.9 are drawn from the 10 km split only.

## 5. Discussion

Discrete EO acquisitions undersample the event hydrograph: the reconstructed areal maximum (7 June) lies between the
Sentinel-1 acquisitions of 6 and 9 June, and it is not the day of the peak stage at Kherson (8 June; Lehnigk et al. 2026
report downstream peak stages by 8 June from the same SWOT data). This is a general property of satellite flood observation,
not of this event: the 6- and 12-day Sentinel-1 revisit intervals "are not sufficient to accurately track flood progression
over time" (DeVries et al. 2020), acquisitions can fall hours before the flood peak (Giordan et al. 2018), and even with two
constellations and both orbit directions the share of European flood events that can be observed at all rises only to
about 58 % for Sentinel-1 (Tarpanelli et al. 2022). The closest instrument the literature offers for the maximum between
two images is InSAR coherence, which acts "as a sort of persistent change detector, registering the maximum extent of
inundation" between acquisitions (Refice et al. 2017) — a detector of where water passed, not of when or how deep. Maximum
    extent and maximum stage are different quantities whose timing changes along a 100 km reach — floodplain storage and
    drainage produce hysteresis between extent, volume and stage (Fassoni-Andrade et al. 2023): Zuo et al. (2024) see the
largest Sentinel-3 water-surface area around 9 June at 300 m resolution and Lehnigk et al. (2026) the stage maxima by
8 June; neither observes an areal maximum on 7 June and neither excludes it. The day of the areal maximum is therefore the
most model-dependent number of this paper: it is where the water-surface-constrained reconstruction adds what no
acquisition can give, and where Paper 5's hydraulic model will be tested.

The three areas of §4.6 are not three estimates of one quantity. The dark-water rule counts water it can see on the day it
looks; the label contract counts water that persisted over three peak dates and therefore describes the recession, not the
areal maximum; the reconstruction counts ground the observed water surface can reach. Their disagreement on 9 June is not
noise: it falls into surfaces the radar cannot see (forest, buildings, emergent reeds), reed beds that were already at the water
level in the normal regime and became dark only when submerged, and dark fields far above any water surface of the event, which
are topographically unsupported by the reconstruction and for which the independent altimetry gives no evidence of a DEM error
large enough to explain them. The most useful product of the comparison is therefore not a single accuracy but the map of where
each source is blind. Operational SAR flood services have reached the same conclusion from the sensor side: exclusion
maps derived from C-band time series mark where flood cannot be inferred from intensity (Zhao et al. 2021), the
Copernicus EMS ensemble delivers "an exclusion mask indicating the regions where the detection is prevented" next to its
flood layer (Amitrano et al. 2024), and the Sentinel-1 data-cube architecture behind the Global Flood Monitoring service was
designed to carry "masks showing where Sentinel-1 cannot detect floods due to physical reasons" (Wagner et al. 2020).
What the terrain reconstruction adds to such masks is the other half of the picture — where the radar reports water that
the observed water surface cannot reach — and, through ICESat-2, a test of whether the terrain itself is at fault there.

The reconstruction's largest uncertainty is definitional rather than metric: whether the reed beds of the delta, which the
class-bias-corrected DEM places at or below the normal water surface, are "new inundation" or "wetland submergence" changes
    the reconstructed areal maximum by about a third (T12). We report both, with the submergence quantified from the Sentinel-1 onset on normally-wet
cells (T13, T14). The metric uncertainty (the primary Monte-Carlo interval) is narrow by comparison, and enters the volume
mainly as a displacement; the planar surface and the absence of timing are outside it and make the recession a lower bound,
which Paper 5 will address with a two-dimensional model calibrated on these daily surfaces. The reservoir balance of §4.1 is
context: a daily-mean effective release from a sloped surface between three or four level points on a DEM whose hypsometry sits
below the design table; Paper 4 will rebuild the bowl on the historical bathymetry before that balance can be more than an
order-of-magnitude check against the published breach-flow estimates.

The U-Net experiments say what an EO product can and cannot learn from such labels: changing the negative class (reference
water) removes a measurable reference-water artefact with no statistically resolved change in recall; terrain as an input
suppresses part of the cropland burden; land cover as an input does not act as a veto; and pre-event water as an input helps
but cannot be evaluated independently while it also defines the label. Every one of these statements is agreement with
weak labels on a frozen spatial split — labels of the kind that the flood-mapping literature now trains on routinely
(Sentinel-1/2 threshold classifications as weak labels: Bonafilia et al. 2020; Katiyar et al. 2021; Sharma et al. 2025)
and whose errors a model "still ends up learning" (Garg et al. 2023). The direction of the terrain effect is not general
either: with HAND used as a Bayesian prior rather than an input channel, Tupas et al. (2023) reduced false negatives "at
the cost of slightly increasing false positives", the opposite trade-off to the cropland result here, so what terrain does
to a SAR flood product depends on how it enters the model and on which label it is scored against.

## 6. Limitations

A daily reconstructed series, not daily observations: between observation days the values are interpolation and model. Planar
water surface per node neighbourhood, no momentum and no timing of filling and draining; DEM under canopy and reeds
(FABDEM residuals of 1.5–2 m under trees); SWOT nodes on channels only, with the gauge cap beyond 15 km; no satellite scene on
    the day of the reconstructed areal maximum; the date-only gauge against 11:00 UTC SWOT passes; weak labels whose positives are a persistence product;
W_pre circularity of U2b; frame B3 (delta with the liman) not built; no probability-sample reference for any area; literature
    figures verified against the source texts where these were available (the UNOSAT product sheets behind the ~620 km² of cumulative flooded land over 6–9 June and the ~180 km² of flooded land on 13 June, reference water separate, were not obtained; those two figures are quoted as cited by OCHA and by Yailymov et al. 2025); the Inhulets backwater treated with its own nodes but without a tributary
hydrograph; the reservoir balance rests on three to four level points and a DEM hypsometry below the design table; the
design-curve reading assumes a level pool and, before the breach, holds the last SWOT outlet value between passes; the
Sentinel-1 dark surface over the drained bed is not a water area (no source separates wet sediment from water in C-band);
the deterministic nominal run lies below its own Monte-Carlo p05 on the peak days — the mechanism is the connection-opening effect of correlated DEM perturbations (§3.3), but its attribution to the individual error terms is open; the
S1-only detections above the surface are shown to be topographically unsupported, not attributed to a cause.

## 7. Conclusions

See the claims register (`claims.md`, C01–C14; each claim names its evidence class, table cells, uncertainty and limitation).
In one sentence: the observed water surface, projected on a bias-corrected terrain with connectivity, gives a daily reconstructed
inundation extent, depth and volume with a stated primary interval for the Kakhovka flood, with the areal maximum between the
available acquisitions; Sentinel-1 agrees with it where the sensor can see and reveals, with ICESat-2, where it cannot; and U-Net
products trained on such observations recover the persistent flood but inherit the sensor's blind spots unless the label
contract names them. The next step is a separate paper (Paper 4) that reconstructs the reservoir bowl on the historical
bathymetry, followed by the hydraulic model (Paper 5).

## Data and code availability

Code, tables, figures, notebooks and the dashboard: https://github.com/NikoriakViktot/floodstate-eo (release candidate `v0.3.0-rc1`; Zenodo
DOI to be minted from the release). Processed rasters (≈ 100 GB) are documented in `docs/REPRODUCIBILITY.md` (three levels);
FABDEM-derived rasters are not redistributed (CC BY-NC-SA 4.0). SWOT (PO.DAAC), ICESat-2 (NSIDC), Sentinel (Copernicus) and
WorldCover (ESA) are open archives; gauge data from the UkrHMC yearbooks as in Paper 1.

## Supplementary figures

![FigS01](figures/FigS01_training_curves.png)

**FigS01.** training loss and validation patch F1 per arm.

![FigS02](figures/FigS02_rule_closure_sensitivity.png)

**FigS02.** rule and closure sensitivity of the daily corridor area (connected, HAND, ceiling only, superseded p59 closure with +0.5 m margin, uncorrected DEM).

![FigS03](figures/FigS03_per_date_series.png)

**FigS03.** per-date S1 and reliable S2 new-water series per region.

![FigS04](figures/FigS04_rf20_agreement.png)

**FigS04.** RF20 row-normalised confusion (spatial-block CV) and per-class F1 for CV and transfers.

![FigS05](figures/FigS05_block_sensitivity.png)

**FigS05.** block-size sensitivity of U2 on v003_A (7.5 / 10 / 15 / 20 km; each split has its own TEST geography).

![FigS06](figures/FigS06_inhulets_profile.png)

**FigS06.** Inhulets valley: mapped U2b new flood and EVENT_FLOOD label per 2-km northing band.

![FigS07](figures/FigS07_hypsometry_sensitivity.png)

**FigS07.** Reservoir hypsometry sensitivity: (a) V_DEM(H) against V_design(H) (Table 19, BS-77 + 0.185 m); (b) the relative gap ΔV/V_design and ΔA/A_design per level over the drawdown range (shaded), about −9 % at the full-pool level and −14…−20 % at 13–11 m; the design table is undefined below 10 m. The released volume of T21 inherits this gap; resolving it on the historical bathymetry is the subject of Paper 4 (T22).

![FigS08](figures/FigS08_reservoir_drawdown_maps.png)

**FigS08.** Reservoir drawdown maps (p95h; context, no claim). (a–c) Modelled pool on 7, 9 and 13 June: the p95f sloped daily surface over the seamless DEM inside the pre-breach pool (*terrain_reconstructed*); (d) the day on which a cell wet on 5 June first falls dry; the upper (north-eastern) pool empties first. (e–h) Sentinel-1 VH dark surface, per-date Otsu over all covered cells (*observed_S1*); IoU against the model on observed cells 0.98 (1 June), 0.97 (8 June), 0.93 (9 June), 0.85 (13 June). VH dark means open water **or** smooth wet mud, so after ~13 June S1 exceeds the Sentinel-2 water area on the exposed flats (S1 dark 1702 km² on 20 June and 2077 km² on 21 June against 648 km² of S2 water on 20 June, T23) and is not a water area there. (i–k) Sentinel-2 k10e surface classes (frozen p25 products, *observed_S2*) before the breach, during the drawdown and in September (bare sediment, then recolonising vegetation); (l) Sentinel-2 water on 20 June (p15 crosscheck, fully observed, 648 km²). For comparison, Yi et al. (2025) map the reservoir from Sentinel-1 **and** Sentinel-2; their text gives 2125 km² on 30 May and decrements that imply ~845 km² around 20 June (*literature_reported*, VERIFY); the 2089 / 1849 / 825 / 369 km² in T23 are **digitised from their figure** (figure number VERIFY), not quoted from their text. S2 on 5 June agrees with the modelled full pool at IoU 0.98. Not observed is not dry.

![FigS09](figures/FigS09_reservoir_s2_indices.png)

**FigS09.** The seven Sentinel-2 indices (NDVI, NDWI, MNDWI, NDMI, BSI, AWEIsh, NDTI) over the pool (+1 km) in display classes on 5 June (pre-breach), 5 July (drawdown) and 8 September 2023; frozen p25 stacks (offset-corrected reflectance, 20 m); the bins are for display only and are not a classifier; blank = not observed.

![FigS10](figures/FigS10_reservoir_design_hypsometry.png)

**FigS10.** Design hypsometry of the Kakhovka reservoir and the observed 2023 levels read on it (p95i, T27; no DEM, nothing fitted). (a) Level–volume of the whole pool (monograph Table 19, Figs 13–15) with the volume of the five reaches stacked (dam → Babyne → Nikopol → Verkhnia Tarasivka → Blahovishchenka → Dnipro HPP) and the design levels (NUF 17.5, NPG 16.0, UNS 14.0, GMO 12.7 m historical Baltic; right axis EVRF2019 = +0.185 m). (b) Level–area, with the observed outlet level before the breach and on 6–13 June read on the design curve. (c) The design volume from 1 February to 20 June read at the observed levels: before the breach at the Rozumivka gauge (the pool was level) — the spring filling from ~13.5 km³ (14.0 m, early February) to 21.3 km³ (17.6 m, 5 May) during the April–May DniproHES release (shaded, right axis; 7.9 km³ of 22.7 km³ of inflow stored, the rest passed the Kakhovka HPP), a plateau at ~17.5 m through May and ~0.4 m lower in the last ten days before the breach; after the breach at the outlet (SWOT) and at the Rozumivka level — the surface sloped by up to 4 m, so the design curve, which assumes a level pool, gives a range, not one number; shaded where the outlet falls below 10.0 m and Table 19 is undefined. The storage balance on the design curve at the Rozumivka level gives a daily-mean effective release of ~12 000 / 38 000 / 20 000 / 19 000 m³/s on 6–9 June (T27b), the design-curve counterpart of the ~40 000 m³/s of T21 on 7 June. The released volume on the sloped surface of Paper 3 is T21/Fig09.

## Supplementary tables

Tables of the publication bundle not cited in the main text (their identifiers are the bundle's, `tables/README.md` defines every metric and semantics column). All 39 tables are supplied as CSV in `tables/`.

**T02.** Weak reference labels per frame: v002 (FLOOD / NON_FLOOD / IGNORE) and v003_A (LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN), km2. EVENT_FLOOD is pixel-identical to v002 FLOOD.
*Evidence level: weak_label_agreement.*

| frame | v002_FLOOD_km2 | v002_NON_FLOOD_km2 | v002_IGNORE_km2 | v003A_EVENT_FLOOD_km2 | v003A_LAND_km2 | v003A_REFERENCE_WATER_km2 | v003A_UNKNOWN_km2 | area_semantics |
|---|---|---|---|---|---|---|---|---|
| B2 | 57.5 | 736.16 | 2092.26 | 57.49 | 663.09 | 283.85 | 1881.49 | weak_reference_label |
| B1 | 128.9 | 1753.1 | 4209.68 | 128.9 | 1544.3 | 258.47 | 4160.01 | weak_reference_label |

**T02b.** Transition v002 -> v003_A per frame, km2 (the change is on the negative side and in the UNKNOWN domain).
*Evidence level: weak_label_agreement.*

| frame | v002 | EVENT_FLOOD | LAND | REFERENCE_WATER | UNKNOWN |
|---|---|---|---|---|---|
| B1 | FLOOD | 128.9 | 0 | 0 | 0 |
| B1 | IGNORE | 0 | 0 | 250.79 | 3958.88 |
| B1 | NON_FLOOD | 0 | 1544.3 | 7.68 | 201.12 |
| B2 | FLOOD | 57.49 | 0 | 0 | 0 |
| B2 | IGNORE | 0 | 0 | 280.06 | 1812.21 |
| B2 | NON_FLOOD | 0 | 663.09 | 3.79 | 69.28 |

**T03b.** Stratum shares of the frozen split (train / validation / test), km2.
*Evidence level: weak_label_agreement.*

| stratum | total_km2 | train_share | val_share | test_share | train_km2 | val_km2 | test_km2 |
|---|---|---|---|---|---|---|---|
| DRY_CROPLAND | 1019.01 | 0.506 | 0.126 | 0.368 | 515.6 | 128.62 | 374.78 |
| FLOODED_OPEN_LOW_VEGETATION | 20.12 | 0.503 | 0.167 | 0.33 | 10.13 | 3.35 | 6.64 |
| FLOODED_WETLAND | 127.8 | 0.561 | 0.101 | 0.338 | 71.7 | 12.91 | 43.2 |
| DRY_WETLAND_OR_VEGETATION | 859.73 | 0.597 | 0.164 | 0.239 | 512.88 | 141.4 | 205.46 |
| FLOOD_BOUNDARY | 13.24 | 0.626 | 0.088 | 0.285 | 8.29 | 1.17 | 3.78 |
| FLOODED_CROPLAND | 3.1 | 0.594 | 0.16 | 0.246 | 1.84 | 0.5 | 0.76 |

**T03c.** Composition of the frozen split per frame, km2.
*Evidence level: weak_label_agreement.*

| frame | split | area_km2 | FLOOD_km2 | NON_FLOOD_km2 | IGNORE_km2 |
|---|---|---|---|---|---|
| B1 | train | 2558.1 | 55.9 | 727.68 | 1774.54 |
| B1 | val | 606.9 | 9.78 | 157.15 | 439.96 |
| B1 | test | 840 | 26.38 | 407.64 | 405.97 |
| B1 | buffer | 614.5 | 9.58 | 214.25 | 390.72 |
| B2 | train | 1518.6 | 22.86 | 365.42 | 1130.27 |
| B2 | val | 364.9 | 5.31 | 94.3 | 265.26 |
| B2 | test | 523.8 | 17.97 | 156.77 | 349.08 |
| B2 | buffer | 478.7 | 11.35 | 119.68 | 347.65 |

**T04.** U-Net arms: inputs, labels, frozen validation threshold and training settings. U2b is a diagnostic experiment (W_pre is also a label ingredient).
*Evidence level: weak_label_agreement.*

| arm | labels | run | n_channels | channels | note | threshold | val_F1 | epochs | batch | lr | seed | seconds | diagnostic_only |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| U0d | v002 | U0d_B1B2_v1 | 12 | d_vv_min d_vh_min d_vv_max d_vh_max d_vv_mean d_vh_mean d_vvvh_min d_vvvh_max n_valid_pre_matched n_valid_event n_orbits_event has_event | S1 d_* + support + has_event. NO z_*, NO p73, NO HAND, NO S2, NO TRACE. | 0.56 | 0.8998 | 60 | 6 | 0.0003 | 20260923 | 131 | False |
| U0z | v002 | U0z_B1B2_v1 | 16 | d_vv_min d_vh_min d_vv_max d_vh_max d_vv_mean d_vh_mean d_vvvh_min d_vvvh_max z_vv_min z_vh_min z_vv_max z_vh_max n_valid_pre_matched n_valid_event n_orbits_event has_event | U0d + robust z_* (domain-shift ablation). | 0.59 | 0.9179 | 60 | 6 | 0.0003 | 20260923 | 187 | False |
| U1 | v002 | U1_B1B2_v1 | 20 | d_vv_min d_vh_min d_vv_max d_vh_max d_vv_mean d_vh_mean d_vvvh_min d_vvvh_max n_valid_pre_matched n_valid_event n_orbits_event has_event p73_WATER p73_CROPLAND p73_GRASS_LOW_VEGETATION p73_FOREST p73_WETLAND_REED p73_BUILT_UP p73_BARE_SAND p73_UNCERTAIN | U0d + frozen p73 RF20 surface class as one-hot INPUT context (never in labels). | 0.31 | 0.9271 | 60 | 6 | 0.0003 | 20260923 | 196 | False |
| U2 | v002 | U2_B1B2_v1 | 14 | d_vv_min d_vh_min d_vv_max d_vh_max d_vv_mean d_vh_mean d_vvvh_min d_vvvh_max n_valid_pre_matched n_valid_event n_orbits_event hand_m has_event has_hand | U0d + HAND (floodplain/<zone>_hand_m.tif, metres) + has_hand. NO p73, NO z_*, NO S2, NO TRACE. | 0.5 | 0.9109 | 60 | 6 | 0.0003 | 20260923 | 178 | False |
| U0d | v003_A | U0d_B1B2_v003A | 12 | d_vv_min d_vh_min d_vv_max d_vh_max d_vv_mean d_vh_mean d_vvvh_min d_vvvh_max n_valid_pre_matched n_valid_event n_orbits_event has_event | S1 d_* + support + has_event. NO z_*, NO p73, NO HAND, NO S2, NO TRACE. | 0.65 | 0.8955 | 60 | 6 | 0.0003 | 20260923 | 180 | False |
| U2 | v003_A | U2_B1B2_v003A | 14 | d_vv_min d_vh_min d_vv_max d_vh_max d_vv_mean d_vh_mean d_vvvh_min d_vvvh_max n_valid_pre_matched n_valid_event n_orbits_event hand_m has_event has_hand | U0d + HAND (floodplain/<zone>_hand_m.tif, metres) + has_hand. NO p73, NO z_*, NO S2, NO TRACE. | 0.37 | 0.8786 | 60 | 6 | 0.0003 | 20260923 | 182 | False |
| U2b | v003_A | U2b_B1B2_v003A | 16 | d_vv_min d_vh_min d_vv_max d_vh_max d_vv_mean d_vh_mean d_vvvh_min d_vvvh_max n_valid_pre_matched n_valid_event n_orbits_event hand_m has_event has_hand w_pre_state has_wpre | U2 + W_pre (S1 06-01/06-02 water state) + has_wpre. Requires --labels v003_A. | 0.78 | 0.9047 | 60 | 6 | 0.0003 | 20260923 | 189 | True |

**T05.** D1 endpoints per arm on the frozen TEST blocks with 95 % spatial-block bootstrap intervals (2000 resamples).
*Evidence level: weak_label_agreement.*

*Table T05 has 266 rows × 7 columns and is supplied as `tables/T05.csv` (Supplementary Data); it is not printed here.*

**T07.** v003_A attribution endpoints per finished run at its own frozen threshold: predicted flood on TEST REFERENCE_WATER, EVENT_FLOOD recall, LAND false positives, UNKNOWN burden; 95 % block-bootstrap intervals.
*Evidence level: weak_label_agreement.*

*Table T07 has 65 rows × 7 columns and is supplied as `tables/T07.csv` (Supplementary Data); it is not printed here.*

**T08b.** Retention of U0d candidate area by the other v002 arms (fraction of km2).
*Evidence level: weak_label_agreement.*

| group | U0d_area_km2 | retained_km2_U0z | retained_km2_U1 | retained_km2_U2 | retention_U0z | retention_U1 | retention_U2 |
|---|---|---|---|---|---|---|---|
| A | 7.292 | 2.963 | 5.687 | 3.156 | 0.406 | 0.78 | 0.433 |
| B | 8.02 | 5.684 | 6.838 | 4.373 | 0.709 | 0.853 | 0.545 |
| D | 3.865 | 3.366 | 3.525 | 2.143 | 0.871 | 0.912 | 0.555 |

**T10b.** RF20 class areas per frame, km2 (mapped areas of a context product).
*Evidence level: contextual.*

| frame | p73_class | km2 | share_pct |
|---|---|---|---|
| B1 | WATER | 152.42 | 2.5 |
| B1 | CROPLAND | 3304.25 | 54.24 |
| B1 | GRASS_LOW_VEGETATION | 1044.65 | 17.15 |
| B1 | FOREST | 552.81 | 9.07 |
| B1 | SHRUB | 0 | 0 |
| B1 | WETLAND_REED | 293.35 | 4.82 |
| B1 | BUILT_UP | 275.05 | 4.52 |
| B1 | BARE_SAND | 116.03 | 1.9 |
| B1 | OTHER | 0 | 0 |
| B1 | UNCERTAIN | 353.13 | 5.8 |
| B2 | WATER | 178.02 | 6.17 |
| B2 | CROPLAND | 1476.3 | 51.18 |
| B2 | GRASS_LOW_VEGETATION | 481.54 | 16.69 |
| B2 | FOREST | 181.71 | 6.3 |
| B2 | SHRUB | 0 | 0 |
| B2 | WETLAND_REED | 229.4 | 7.95 |
| B2 | BUILT_UP | 145.31 | 5.04 |
| B2 | BARE_SAND | 23.49 | 0.81 |
| B2 | OTHER | 0 | 0 |
| B2 | UNCERTAIN | 169 | 5.86 |

**T10c.** RF20 vs WorldCover wall-to-wall agreement on WorldCover-pure cells (recall / precision vs the training reference).
*Evidence level: contextual.*

| frame | p73_class | worldcover | wc_pure_km2 | recall_vs_wc | precision_vs_wc |
|---|---|---|---|---|---|
| B1 | WATER | water | 173.5 | 0.864 | 0.9956 |
| B1 | CROPLAND | cropland | 3397.2 | 0.9324 | 0.9873 |
| B1 | GRASS_LOW_VEGETATION | grass | 918.4 | 0.7962 | 0.8535 |
| B1 | FOREST | tree | 448.8 | 0.9281 | 0.9436 |
| B1 | SHRUB | shrub | 0 | 0 | 0 |
| B1 | WETLAND_REED | herb_wetland | 239.5 | 0.93 | 0.9217 |
| B1 | BUILT_UP | built | 140.8 | 0.9431 | 0.8205 |
| B1 | BARE_SAND | bare | 27.2 | 0.9935 | 0.3989 |
| B1 | OTHER | snow | 0 | 0 | 0 |
| B1 | OTHER | mangrove | 0 | 0 | 0 |
| B1 | OTHER | moss | 0 | 0 | 0 |
| B2 | WATER | water | 185.3 | 0.9432 | 0.9974 |
| B2 | CROPLAND | cropland | 1562.1 | 0.9077 | 0.991 |
| B2 | GRASS_LOW_VEGETATION | grass | 369.3 | 0.8068 | 0.7705 |
| B2 | FOREST | tree | 146.8 | 0.9077 | 0.9452 |
| B2 | SHRUB | shrub | 0 | 0 | 0 |
| B2 | WETLAND_REED | herb_wetland | 202.8 | 0.9302 | 0.9538 |
| B2 | BUILT_UP | built | 77.7 | 0.9465 | 0.841 |
| B2 | BARE_SAND | bare | 1 | 0.9552 | 0.0487 |
| B2 | OTHER | snow | 0 | 0 | 0 |
| B2 | OTHER | mangrove | 0 | 0 | 0 |
| B2 | OTHER | moss | 0 | 0 | 0 |

**T17b.** Daily values behind T17.
*Evidence level: independent_physical.*

| date | swot_p50 | n_nodes | H_gauge_evrf | gauge_minus_swot |
|---|---|---|---|---|
| 2023-05-26 | 0.659 | 25 | 0.6 | -0.059 |
| 2023-05-27 | 0.653 | 36 | 0.61 | -0.043 |
| 2023-05-28 | 0.608 | 37 | 0.6 | -0.008 |
| 2023-05-29 | 0.602 | 45 | 0.61 | 0.008 |
| 2023-05-30 | 0.635 | 45 | 0.62 | -0.015 |
| 2023-05-31 | 0.602 | 45 | 0.59 | -0.012 |
| 2023-06-01 | 0.425 | 2 | 0.6 | 0.175 |
| 2023-06-02 | 0.72 | 6 | 0.65 | -0.07 |
| 2023-06-03 | 0.641 | 45 | 0.64 | -0.001 |
| 2023-06-04 | 0.505 | 45 | 0.54 | 0.035 |
| 2023-06-05 | 0.514 | 45 | 0.54 | 0.026 |
| 2023-06-06 | 3.08 | 45 | 3.09 | 0.01 |
| 2023-06-09 | 5.302 | 12 | 5.37 | 0.068 |
| 2023-06-10 | 4.682 | 34 | 4.8 | 0.118 |
| 2023-06-11 | 4.131 | 45 | 4.24 | 0.109 |
| 2023-06-12 | 3.537 | 42 | 3.64 | 0.103 |
| 2023-06-13 | 2.989 | 30 | 3.04 | 0.051 |
| 2023-06-14 | 2.435 | 42 | 2.55 | 0.115 |
| 2023-06-17 | 1.394 | 39 | 1.43 | 0.036 |
| 2023-06-18 | 1.133 | 45 | 1.15 | 0.017 |
| 2023-06-20 | 0.812 | 45 | 0.81 | -0.002 |
| 2023-06-23 | 0.504 | 45 | 0.58 | 0.076 |
| 2023-06-24 | 0.525 | 45 | 0.58 | 0.055 |
| 2023-06-25 | 0.5 | 45 | 0.56 | 0.06 |
| 2023-06-26 | 0.481 | 45 | 0.55 | 0.069 |
| 2023-06-27 | 0.488 | 45 | 0.45 | -0.038 |
| 2023-06-29 | 0.538 | 45 | 0.51 | -0.028 |
| 2023-07-01 | 0.535 | 45 | 0.48 | -0.055 |
| 2023-07-02 | 0.485 | 45 | 0.43 | -0.055 |
| 2023-07-03 | 0.491 | 35 | 0.41 | -0.081 |
| 2023-07-05 | 0.344 | 30 | 0.33 | -0.014 |
| 2023-07-06 | 0.3 | 44 | 0.26 | -0.04 |
| 2023-07-07 | 0.325 | 45 | 0.33 | 0.005 |
| 2023-07-08 | 0.342 | 45 | 0.33 | -0.012 |
| 2023-07-09 | 0.223 | 45 | 0.19 | -0.033 |
| 2023-07-10 | 0.343 | 45 | 0.35 | 0.007 |

## References

Verified against CrossRef/OpenAlex on 2026-09-28 (`07_references_verified.bib`, `07c_method_references_verified.bib`); corpus records were read in the GeoHydroAI corpus. Keys in square brackets are the bibliography keys.

- [ATL13_v6] Jasinski, Michael and Stoll, Jeremy and Hancock, David and Robbins, John and Nattala, Jyothi and Pavelsky, Tamlin and Morison, Jamie and Jones, Benjamin and Ondrusek, Michael and Parrish, Christopher and Carabajal, Claudia and the ICESat-2 Science Team (2023). ATLAS/ICESat-2 L3A Along Track Inland Surface Water Data, Version 6. NASA National Snow and Ice Data Center Distributed Active Archive Center. https://doi.org/10.5067/ATLAS/ATL13.006
- [Agerbeek_2024] Agerbeek, Bas; Knepflé, Maxim; Witsenburg, Florian; Jonkman, Sebastiaan (2024). Near real-time flood risk modelling in response to increasing uncertainties in flood predictions: Insights from the Kakhovka Dam breach in Ukraine. Journal of Coastal and Riverine Flood Risk. https://doi.org/10.59490/jcrfr.2024.0016 [corpus record, text read; metadata from CrossRef/corpus]
- [Altenau_2021] Altenau, Elizabeth H. and Pavelsky, Tamlin M. and Durand, Michael T. and Yang, Xiao and Frasson, Renato Prata de Moraes and Bendezu, Liam (2021). The Surface Water and Ocean Topography (SWOT) Mission River Database (SWORD): A Global River Network for Satellite Data Products. Water Resources Research, 57, e2021WR030054. https://doi.org/10.1029/2021WR030054
- [Amitrano_2024] Amitrano, Donato; Di Martino, Gerardo; Di Simone, Alessio; Imperatore, Pasquale (2024). Flood Detection with SAR: A Review of Techniques and Datasets. Remote Sensing. https://doi.org/10.3390/rs16040656 [corpus record, text read; metadata from CrossRef/corpus]
- [ArcosGonzalez_2026] Arcos González, Pedro; Gan, Rick; Alsua, Carlos; Aregay, Aron; Assaf Msc, Denise; Bruni, Emanuele (2026). Exploring Cascading Disaster Risk During Complex Emergencies: Chemical Industry Disaster Risk Assessment in the Aftermath of the Kakhovka Dam Bombing in Ukraine. Disaster Medicine and Public Health Preparedness. https://doi.org/10.1017/dmp.2024.41 [corpus record, text read; metadata from CrossRef/corpus]
- [Bai_2021] Bai, Yanbing and Wu, Wenqi and Yang, Zhengxin and Yu, Jinze and Zhao, Bo and Liu, Xing and Yang, Hanfang and Mas, Erick and Koshimura, Shunichi (2021). Enhancement of Detecting Permanent Water and Temporary Water in Flood Disasters by Fusing Sentinel-1 and Sentinel-2 Imagery Using Deep Learning Algorithms: Demonstration of Sen1Floods11 Benchmark Datasets. Remote Sensing, 13, 2220. https://doi.org/10.3390/rs13112220
- [Bates_2021] Bates, Paul (2021). Annual Review of Fluid Mechanics Flood Inundation Prediction. . https://doi.org/10.1146/annurev-fluid-030121- [corpus record, text read; metadata from CrossRef/corpus]
- [Bates_DeRoo_2000] Bates, P; De Roo, A (2000). A simple raster-based model for flood inundation simulation. Journal of Hydrology. https://doi.org/10.1016/s0022-1694(00)00278-x [corpus record, text read; metadata from CrossRef/corpus]
- [Baugh_2013] Baugh, Calum; Bates, Paul; Schumann, Guy; Trigg, Mark (2013). SRTM vegetation removal and hydrodynamic modeling accuracy. Water Resources Research. https://doi.org/10.1002/wrcr.20412 [corpus record, text read; metadata from CrossRef/corpus]
- [Bekele_2022] Bekele, Tilaye; Haile, Alemseged; Trigg, Mark; Walsh, Claire (2022). Evaluating a new method of remote sensing for flood mapping in the urban and peri-urban areas: Applied to Addis Ababa and the Akaki catchment in Ethiopia. Natural Hazards Research. https://doi.org/10.1016/j.nhres.2022.03.001 [corpus record, text read; metadata from CrossRef/corpus]
- [Belgiu_Dragut_2016] Belgiu, Mariana and Drăguţ, Lucian (2016). Random forest in remote sensing: A review of applications and future directions. ISPRS Journal of Photogrammetry and Remote Sensing, 114, 24-31. https://doi.org/10.1016/j.isprsjprs.2016.01.011
- [Betterle_2024] Betterle, Andrea; Salamon, Peter (2024). Water depth estimate and flood extent enhancement for satellite-based inundation maps. Natural Hazards and Earth System Sciences. https://doi.org/10.5194/nhess-24-2817-2024 [corpus record, text read; metadata from CrossRef/corpus]
- [Biancamaria_2016] Biancamaria, Sylvain and Lettenmaier, Dennis P. and Pavelsky, Tamlin M. (2016). The SWOT Mission and Its Capabilities for Land Hydrology. Surveys in Geophysics, 37, 307-337. https://doi.org/10.1007/s10712-015-9346-y
- [Bioresita_2019] Bioresita, Filsa and Puissant, Anne and Stumpf, André and Malet, Jean-Philippe (2019). Fusion of Sentinel-1 and Sentinel-2 image time series for permanent and temporary surface water mapping. International Journal of Remote Sensing, 40, 9026-9049. https://doi.org/10.1080/01431161.2019.1624869
- [Bonafilia_2020] Bonafilia, Derrick and Tellman, Beth and Anderson, Tyler and Issenberg, Erica (2020). Sen1Floods11: a georeferenced dataset to train and test deep learning flood algorithms for Sentinel-1. 2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW), 835-845. https://doi.org/10.1109/cvprw50498.2020.00113
- [Breiman_2001] Breiman, Leo (2001). Random Forests. Machine Learning, 45, 5-32. https://doi.org/10.1023/A:1010933404324
- [Cohen_2019] Cohen, Sagy and Raney, Austin and Munasinghe, Dinuke and Loftis, J. Derek and Molthan, Andrew and Bell, Jordan and Rogers, Laura and Galantowicz, John and Brakenridge, G. Robert and Kettner, Albert J. and Huang, Yu-Fen and Tsang, Yin-Phan (2019). The Floodwater Depth Estimation Tool (FwDET v2.0) for improved remote sensing analysis of coastal flooding. Natural Hazards and Earth System Sciences, 19, 2053-2065. https://doi.org/10.5194/nhess-19-2053-2019
- [Cunha_2012] Cunha, Luciana; Mandapaka, Pradeep; Krajewski, Witold; Mantilla, Ricardo; Bradley, Allen (2012). Impact of radar‐rainfall error structure on estimated flood magnitude across scales: An investigation based on a parsimonious distributed hydrological model. Water Resources Research. https://doi.org/10.1029/2012wr012138 [corpus record, text read; metadata from CrossRef/corpus]
- [Darnell_2008] Darnell, Amii R. and Tate, Nicholas J. and Brunsdon, Chris (2008). Improving user assessment of error implications in digital elevation models. Computers, Environment and Urban Systems, 32, 268-277. https://doi.org/10.1016/j.compenvurbsys.2008.02.003
- [DePaiva_2013] De Paiva, Rodrigo; Buarque, Diogo; Collischonn, Walter; Bonnet, Marie‐paule; Frappart, Frédéric; Calmant, Stephane; Bulhões Mendes, Carlos (2013). Large‐scale hydrologic and hydrodynamic modeling of the Amazon River basin. Water Resources Research. https://doi.org/10.1002/wrcr.20067 [corpus record, text read; metadata from CrossRef/corpus]
- [DeVries_2020] Devries, Ben; Huang, Chengquan; Armston, John; Huang, Wenli; Jones, John; Lang, Megan (2020). Rapid and robust monitoring of flood events using Sentinel-1 and Landsat data on the Google Earth Engine. Remote Sensing of Environment. https://doi.org/10.1016/j.rse.2020.111664 [corpus record, text read; metadata from CrossRef/corpus]
- [Denker_2013] Denker, Heiner (2013). Regional Gravity Field Modeling: Theory and Practical Results. Sciences of Geodesy - II, 185-291. https://doi.org/10.1007/978-3-642-28000-9_5
- [Diek_2017] Diek, Sanne and Fornallaz, Fabio and Schaepman, Michael E. and De Jong, Rogier (2017). Barest Pixel Composite for Agricultural Areas Using Landsat Time Series. Remote Sensing, 9, 1245. https://doi.org/10.3390/rs9121245
- [Drusch_2012] Drusch, M. and Del Bello, U. and Carlier, S. and Colin, O. and Fernandez, V. and Gascon, F. and Hoersch, B. and Isola, C. and Laberinti, P. and Martimort, P. and Meygret, A. and Spoto, F. and Sy, O. and Marchese, F. and Bargellini, P. (2012). Sentinel-2: ESA's Optical High-Resolution Mission for GMES Operational Services. Remote Sensing of Environment, 120, 25-36. https://doi.org/10.1016/j.rse.2011.11.026
- [Efron_1979] Efron, B. (1979). Bootstrap Methods: Another Look at the Jackknife. The Annals of Statistics, 7. https://doi.org/10.1214/aos/1176344552
- [Efron_Tibshirani_1993] Efron, Bradley and Tibshirani, R.J. (1994). An Introduction to the Bootstrap. . https://doi.org/10.1201/9780429246593
- [FassoniAndrade_2023] César Fassoni-Andrade, Alice; Cauduro Dias De Paiva, Rodrigo; Wongchuig, Sly; Barbosa, Cláudio; Durand, Fabien; Sanna Freire Silva, Thiago (2023). Expressive fluxes over Amazon floodplain revealed by 2D hydrodynamic modelling. Journal of Hydrology. https://doi.org/10.1016/j.jhydrol.2023.130122 [corpus record, text read; metadata from CrossRef/corpus]
- [Feyisa_2014] Feyisa, Gudina L. and Meilby, Henrik and Fensholt, Rasmus and Proud, Simon R. (2014). Automated Water Extraction Index: A new technique for surface water mapping using Landsat imagery. Remote Sensing of Environment, 140, 23-35. https://doi.org/10.1016/j.rse.2013.08.029
- [Gao_1996] Gao, Bo-cai (1996). NDWI—A normalized difference water index for remote sensing of vegetation liquid water from space. Remote Sensing of Environment, 58, 257-266. https://doi.org/10.1016/S0034-4257(96)00067-3
- [Garg_2023] Garg, Shubhika; Feinstein, Ben; Timnat, Shahar; Batchu, Vishal; Dror, Gideon; Rosenthal, Adi; Gulshan, Varun (2023). Cross-modal distillation for flood extent mapping. Environmental Data Science. https://doi.org/10.1017/eds.2023.34 [corpus record, text read; metadata from CrossRef/corpus]
- [Giordan_2018] Giordan, Daniele; Notti, Davide; Villa, Alfredo; Zucca, Francesco; Calò, Fabiana; Pepe, Antonio; Dutto, Furio; Pari, Paolo; Baldo, Marco; Allasia, Paolo (2018). Low cost, multiscale and multi-sensor application for flooded area mapping. Natural Hazards and Earth System Sciences. https://doi.org/10.5194/nhess-18-1493-2018 [corpus record, text read; metadata from CrossRef/corpus]
- [Giustarini_2013] Giustarini, Laura and Hostache, Renaud and Matgen, Patrick and Schumann, Guy J.-P. and Bates, Paul D. and Mason, David C. (2013). A Change Detection Approach to Flood Mapping in Urban Areas Using TerraSAR-X. IEEE Transactions on Geoscience and Remote Sensing, 51, 2417-2430. https://doi.org/10.1109/tgrs.2012.2210901
- [Gleick_2023] Gleick, Peter; Vyshnevskyi, Viktor; Shevchuk, Serhii (2023). Rivers and Water Systems as Weapons and Casualties of the Russia‐Ukraine War. Earth's Future. https://doi.org/10.1029/2023ef003910 [corpus record, text read; metadata from CrossRef/corpus]
- [Grimaldi_2020] Grimaldi, S. and Xu, J. and Li, Y. and Pauwels, V.R.N. and Walker, J.P. (2020). Flood mapping under vegetation using single SAR acquisitions. Remote Sensing of Environment, 237, 111582. https://doi.org/10.1016/j.rse.2019.111582
- [Guo_2025] Guo, Xinqi; Wang, Q; Western, Andrew; Ryu, Dongryeol; Sharples, Wendy; Hou, Jiawei (2025). Flood monitoring: A hydrologically guided method for infilling incomplete flood inundation maps derived from satellite images. Journal of Hydrology. https://doi.org/10.1016/j.jhydrol.2025.133365 [corpus record, text read; metadata from CrossRef/corpus]
- [Hawker_2018] Hawker, Laurence and Bates, Paul and Neal, Jeffrey and Rougier, Jonathan (2018). Perspectives on Digital Elevation Model (DEM) Simulation for Flood Modeling in the Absence of a High-Accuracy Open Access Global DEM. Frontiers in Earth Science, 6, 233. https://doi.org/10.3389/feart.2018.00233
- [Hawker_2022] Hawker, Laurence and Uhe, Peter and Paulo, Luntadila and Sosa, Jeison and Savage, James and Sampson, Christopher and Neal, Jeffrey (2022). A 30 m global map of elevation with forests and buildings removed. Environmental Research Letters, 17, 024016. https://doi.org/10.1088/1748-9326/ac4d4f
- [He_2016] He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian (2016). Deep Residual Learning for Image Recognition. 2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 770-778. https://doi.org/10.1109/cvpr.2016.90
- [He_2024] He, Yongjun and Wang, Jinfei and Zhang, Ying and Liao, Chunhua (2024). An efficient urban flood mapping framework towards disaster response driven by weakly supervised semantic segmentation with decoupled training samples. ISPRS Journal of Photogrammetry and Remote Sensing, 207, 338-358. https://doi.org/10.1016/j.isprsjprs.2023.12.009
- [Hohle_2009] Höhle, Joachim and Höhle, Michael (2009). Accuracy assessment of digital elevation models by means of robust statistical methods. ISPRS Journal of Photogrammetry and Remote Sensing, 64, 398-406. https://doi.org/10.1016/j.isprsjprs.2009.02.003
- [Hryshchenko_2024] Hryshchenko, O. and Palamarchuk, R. and Tsyhanov, I. and Syrovatko, V. and Yatsenko, Yu. (2024). Content of heavy metals in bottom sediments of drained Kakhovka Reservoir. Agroecological journal, 53-65. https://doi.org/10.33730/2077-4893.1.2024.299939
- [Iqbal_2023] Iqbal, Ashik; Mondal, M; Veerbeek, William; Khan, M; Hakvoort, Hans (2023). Effectiveness of <scp>UAV</scp>‐based <scp>DTM</scp> and satellite‐based <scp>DEMs</scp> for local‐level flood modeling in <scp>Jamuna</scp> floodplain. Journal of Flood Risk Management. https://doi.org/10.1111/jfr3.12937 [corpus record, text read; metadata from CrossRef/corpus]
- [Islam_2022] Tazmul Islam, Md; Meng, Qingmin (2022). An exploratory study of Sentinel-1 SAR for rapid urban flood mapping on Google Earth Engine. International Journal of Applied Earth Observation and Geoinformation. https://doi.org/10.1016/j.jag.2022.103002 [corpus record, text read; metadata from CrossRef/corpus]
- [Jarrett_2023] Jarrett, Sean; Hölbling, Daniel (2023). Spatial Evaluation of a Natural Flood Management Project Using SAR Change Detection. Water. https://doi.org/10.3390/w15122182 [corpus record, text read; metadata from CrossRef/corpus]
- [Jiao_2025] Jiao, Zhijun; Zhang, Zhimei; Chen, Biyan; Mahmood, Syed; Wu, Lixin (2025). Knowledge-Driven Flood Intelligent Monitoring (KDFIM) Method: Analyzing the Kakhovka Dam Destruction Incident. IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing. https://doi.org/10.1109/jstars.2025.3594119 [corpus record, text read; metadata from CrossRef/corpus]
- [Johnson_2019] Johnson, J. Michael and Munasinghe, Dinuke and Eyelade, Damilola and Cohen, Sagy (2019). An integrated evaluation of the National Water Model (NWM)–Height Above Nearest Drainage (HAND) flood mapping methodology. Natural Hazards and Earth System Sciences, 19, 2405-2420. https://doi.org/10.5194/nhess-19-2405-2019
- [Kadam_2024] Kadam, Piyusha B. and Thakur, Praveen K. and Dwivedi, Sanjay K. and Garg, Vaibhav and Dhote, Pankja R. (2024). Dam Breach Analysis and Damage Assessment of Nova Kakhovka Dam using Satellite data and 1D and 2D Hydrodynamic Modeling. The International Archives of the Photogrammetry, Remote Sensing and Spatial Information Sciences, XLVIII-3-2024, 251-256. https://doi.org/10.5194/isprs-archives-xlviii-3-2024-251-2024
- [Katiyar_2021] Katiyar, Vaibhav; Tamkuan, Nopphawan; Nagai, Masahiko (2021). Near-Real-Time Flood Mapping Using Off-the-Shelf Models with SAR Imagery and Deep Learning. Remote Sensing. https://doi.org/10.3390/rs13122334 [corpus record, text read; metadata from CrossRef/corpus]
- [Kozlova_2024] Kozlova, A. and Lischenko, L. and Andreiev, A. and Lubskyi, M. and Lysenko, A. (2024). Water Occurrence Mapping of Kakhovka Reservoir after the Dam Destruction. International Conference of Young Professionals «GeoTerrace-2024», 1-5. https://doi.org/10.3997/2214-4609.2024510066
- [Kulp_Strauss_2019] Kulp, Scott; Strauss, Benjamin (2019). New elevation data triple estimates of global vulnerability to sea-level rise and coastal flooding. Nature Communications. https://doi.org/10.1038/s41467-019-12808-z [corpus record, text read; metadata from CrossRef/corpus]
- [Kuzemko_2024] Kuzemko, Anna; Prylutskyi, Oleh; Kolomytsev, Grygoriy; Didukh, Yakiv; Moysiyenko, Ivan; Borsukevych, Liubov; Chusova, Olga; Splodytel, Anastasiia; Khodosovtsev, Oleksandr (2024). Reach the bottom: plant cover of the former Kakhovka Reservoir, Ukraine. . https://doi.org/10.21203/rs.3.rs-4137799/v1 [corpus record, text read; metadata from CrossRef/corpus]
- [Kuzemko_2025] Kuzemko, Anna; Prylutskyi, Oleh; Kolomytsev, Gryg; Didukh, Ya.; Moysiyenko, Ivan; Borsukevych, Li; Chusova, Olga; Khodosovtsev, Oleksandr (2025). Initial stages of revegetation at the bottom of the drained Kakhovka Reservoir (Ukraine): synthesis of field surveys and remote sensing. Ukrainian Botanical Journal. https://doi.org/10.15407/ukrbotj82.05.488 [corpus record, text read; metadata from CrossRef/corpus]
- [Lacaux_2007] Lacaux, J.P. and Tourre, Y.M. and Vignolles, C. and Ndione, J.A. and Lafaye, M. (2007). Classification of ponds from high-spatial resolution remote sensing: Application to Rift Valley Fever epidemics in Senegal. Remote Sensing of Environment, 106, 66-74. https://doi.org/10.1016/j.rse.2006.07.012
- [Landuyt_2019] Landuyt, Lisa; Van Wesemael, Alexandra; Schumann, Null-; Hostache, Renaud; Verhoest, Niko; Van Coillie, Frieke (2019). Flood Mapping Based on Synthetic Aperture Radar: An Assessment of Established Approaches. IEEE Transactions on Geoscience and Remote Sensing. https://doi.org/10.1109/tgrs.2018.2860054 [corpus record, text read; metadata from CrossRef/corpus]
- [Le_2026] Le, Xuan-Hien and Koyama, Naoki and Yamada, Tadashi (2026). Impacts of elevation bias and topographic uncertainty on flood modeling: model robustness and floodplain sensitivity mapping in a lowland River Basin. Journal of Hydrology, 666, 134832. https://doi.org/10.1016/j.jhydrol.2025.134832
- [Lee_1980] Lee, Jong-Sen (1980). Digital Image Enhancement and Noise Filtering by Use of Local Statistics. IEEE Transactions on Pattern Analysis and Machine Intelligence, PAMI-2, 165-168. https://doi.org/10.1109/TPAMI.1980.4766994
- [Lehnigk_2026] Lehnigk, K. E. and Pavelsky, T. M. and Lang, K. A. (2026). SWOT Satellite Observations of the Kakhovka Dam Break Flood Highlight Limitations of Outburst Flood Models. Geophysical Research Letters, 53, e2025GL120832. https://doi.org/10.1029/2025gl120832
- [Lindsay_2016] Lindsay, J.B. (2016). Whitebox GAT: A case study in geomorphometric analysis. Computers \&amp; Geosciences, 95, 75-84. https://doi.org/10.1016/j.cageo.2016.07.003
- [Lopes_1990] Lopes, A. and Touzi, R. and Nezry, E. (1990). Adaptive speckle filters and scene heterogeneity. IEEE Transactions on Geoscience and Remote Sensing, 28, 992-1000. https://doi.org/10.1109/36.62623
- [Magas_2023] Magas, N; Yakovenko, M; Shevchenko, Taras (2023). Comparative analysis of the shallowing of the Kakhovska reservoir based on the data of RS (remote sensing). . [conference paper (Monitoring 2023, Kyiv); no DOI in the corpus record] [corpus record, text read; metadata from CrossRef/corpus]
- [Magas_2026] Magas, Nataliia I. (2026). Post-Breach Landscape Transformation of the Former Kakhovka Reservoir Bed. Journal of Landscape Ecology. https://doi.org/10.2478/jlecol-2026-0039
- [Main-Knorn_2017] Main-Knorn, Magdalena and Pflug, Bringfried and Louis, Jerome and Debaecker, Vincent and Müller-Wilm, Uwe and Gascon, Ferran (2017). Sen2Cor for Sentinel-2. Image and Signal Processing for Remote Sensing XXIII, 3. https://doi.org/10.1117/12.2278218
- [Maiti_2022] Maiti, A. and Oude Elberink, S. J. and Vosselman, G. (2022). EFFECT OF LABEL NOISE IN SEMANTIC SEGMENTATION OF HIGH RESOLUTION AERIAL IMAGES AND HEIGHT DATA. ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences, V-2-2022, 275-282. https://doi.org/10.5194/isprs-annals-V-2-2022-275-2022
- [Maksymenko_2026] Maksymenko, V. O. and Bezsonnyi, V. L. (2026). Remote sensing assessment of the spatio-temporal transformation of the Kakhovka reservoir after dam destruction using Sentinel-2 data. Man and Environment Issues of Neoecology, 79. https://doi.org/10.26565/1992-4224-2026-45-07
- [Martinis_2015] Martinis, Sandro; Kuenzer, Claudia; Wendleder, Anna; Huth, Juliane; Twele, André; Roth, Achim; Dech, Stefan (2015). Comparing four operational SAR-based water and flood detection approaches. International Journal of Remote Sensing. https://doi.org/10.1080/01431161.2015.1060647 [corpus record, text read; metadata from CrossRef/corpus]
- [Martinis_2022] Martinis, Sandro and Groth, Sandro and Wieland, Marc and Knopp, Lisa and Rättich, Michaela (2022). Towards a global seasonal and permanent reference water product from Sentinel-1/2 data for improved flood mapping. Remote Sensing of Environment, 278, 113077. https://doi.org/10.1016/j.rse.2022.113077
- [Martinis_Plank_2018] Martinis, Sandro; Plank, Simon; Ćwik, Kamila (2018). The Use of Sentinel-1 Time-Series Data to Improve Flood Monitoring in Arid Areas. Remote Sensing. https://doi.org/10.3390/rs10040583 [corpus record, text read; metadata from CrossRef/corpus]
- [Matheron_1963] Matheron, Georges (1963). Principles of geostatistics. Economic Geology, 58, 1246-1266. https://doi.org/10.2113/gsecongeo.58.8.1246
- [McFeeters_1996] McFEETERS, S. K. (1996). The use of the Normalized Difference Water Index (NDWI) in the delineation of open water features. International Journal of Remote Sensing, 17, 1425-1432. https://doi.org/10.1080/01431169608948714
- [Milletari_2016] Milletari, Fausto and Navab, Nassir and Ahmadi, Seyed-Ahmad (2016). V-Net: Fully Convolutional Neural Networks for Volumetric Medical Image Segmentation. 2016 Fourth International Conference on 3D Vision (3DV), 565-571. https://doi.org/10.1109/3DV.2016.79
- [Misra_2025] Misra, Amit; White, Kevin; Nsutezo, Simone; Straka, William; Lavista, Juan (2025). Mapping global floods with 10 years of satellite radar data. Nature Communications. https://doi.org/10.1038/s41467-025-60973-1 [corpus record, text read; metadata from CrossRef/corpus]
- [Monti_2024] Monti, Roberto and Rossi, Lorenzo and Reguzzoni, Mirko (2024). The Nova Kakhovka dam collapse flooding as seen from Sentinel-1 SAR satellite images. Advances in Geodesy and Geoinformation, 50-50. https://doi.org/10.24425/agg.2023.146162
- [Neal_2012] Neal, Jeffrey; Schumann, Guy; Bates, Paul (2012). A subgrid channel model for simulating river hydraulics and floodplain inundation over large and data sparse areas. Water Resources Research. https://doi.org/10.1029/2012wr012514 [corpus record, text read; metadata from CrossRef/corpus]
- [Neuenschwander_2019] Neuenschwander, Amy and Pitts, Katherine (2019). The ATL08 land and vegetation product for the ICESat-2 Mission. Remote Sensing of Environment, 221, 247-259. https://doi.org/10.1016/j.rse.2018.11.005
- [Nobre_2011] Nobre, A.D. and Cuartas, L.A. and Hodnett, M. and Rennó, C.D. and Rodrigues, G. and Silveira, A. and Waterloo, M. and Saleska, S. (2011). Height Above the Nearest Drainage – a hydrologically relevant new terrain model. Journal of Hydrology, 404, 13-29. https://doi.org/10.1016/j.jhydrol.2011.03.051
- [Normandin_2024] Normandin, Cassandra; Frappart, Frédéric; Baghdadi, Nicolas; Bourrel, Luc; Luque, Santiago; Ygorra, Bertrand; Kitambo, Benjamin; Papa, Fabrice; Riazanoff, Serge; Wigneron, Jean-Pierre; Zeng, Jiangyuan; Xu, Nan; Huang, Qi (2024). First results of the surface water ocean topography (SWOT) observations to rivers elevation profiles in the Cuvette Centrale of the Congo Basin. Frontiers in Remote Sensing. https://doi.org/10.3389/frsen.2024.1466695 [corpus record, text read; metadata from CrossRef/corpus]
- [Novitskyi_2024] Novitskyi, Roman; Hapich, Hennadii; Maksymenko, Maksym; Kutishchev, Pavlo; Gasso, Viktor; Afanasyev, Sergiy; Banaduc, Doru; Blaga, Lucian; Sellheim, Nikolas (2024). Losses in fishery ecosystem services of the Dnipro river Delta and the Kakhovske reservoir area caused by military actions in Ukraine. Frontiers in Environmental Science. https://doi.org/10.3389/fenvs.2024.1301435 [corpus record, text read; metadata from CrossRef/corpus]
- [Nuth_2011] Nuth, C; Kääb, A (2011). Co-registration and bias corrections of satellite elevation data sets for quantifying glacier thickness change. The Cryosphere. https://doi.org/10.5194/tc-5-271-2011 [corpus record, text read; metadata from CrossRef/corpus]
- [Olofsson_2014] Olofsson, Pontus and Foody, Giles M. and Herold, Martin and Stehman, Stephen V. and Woodcock, Curtis E. and Wulder, Michael A. (2014). Good practices for estimating area and assessing accuracy of land change. Remote Sensing of Environment, 148, 42-57. https://doi.org/10.1016/j.rse.2014.02.015
- [Otsu_1979] Otsu, Nobuyuki (1979). A Threshold Selection Method from Gray-Level Histograms. IEEE Transactions on Systems, Man, and Cybernetics, 9, 62-66. https://doi.org/10.1109/TSMC.1979.4310076
- [Pekel_2016] Pekel, Jean-François and Cottam, Andrew and Gorelick, Noel and Belward, Alan S. (2016). High-resolution mapping of global surface water and its long-term changes. Nature, 540, 418-422. https://doi.org/10.1038/nature20584
- [Pichura_2024] Pichura, Vitalii and Potravka, Larysa and Dudiak, Nataliia and Bahinskyi, Oleksandr (2024). Natural and Climatic Transformation of the Kakhovka Reservoir after the Destruction of the Dam. Journal of Ecological Engineering, 25, 82-104. https://doi.org/10.12911/22998993/187961
- [Pichura_2025] Pichura, Vitalii and Potravka, Larysa and Boiko, Pavlo (2025). Climatic and hydrological conditions for the formation of vegetation cover in the drained Kakhovka reservoir’s territory. Ecological Engineering \&amp; Environmental Technology, 26, 357-373. https://doi.org/10.12912/27197050/202227
- [Pohjankukka_2017] Pohjankukka, Jonne and Pahikkala, Tapio and Nevalainen, Paavo and Heikkonen, Jukka (2017). Estimating the prediction performance of spatial models via spatial k-fold cross validation. International Journal of Geographical Information Science, 31, 2001-2019. https://doi.org/10.1080/13658816.2017.1346255
- [Refice_2017] Refice, Alberto; D’addabbo, Annarita; Capolongo, Domenico (2017). Methods, Techniques and Sensors for Precision Flood Monitoring Through Remote Sensing. . https://doi.org/10.1007/978-3-319-63959-8_1 [corpus record, text read; metadata from CrossRef/corpus]
- [Renno_2008] Rennó, Camilo Daleles and Nobre, Antonio Donato and Cuartas, Luz Adriana and Soares, João Vianei and Hodnett, Martin G. and Tomasella, Javier and Waterloo, Maarten J. (2008). HAND, a new terrain descriptor using SRTM-DEM: Mapping terra-firme rainforest environments in Amazonia. Remote Sensing of Environment, 112, 3469-3481. https://doi.org/10.1016/j.rse.2008.03.018
- [Roberts_2017] Roberts, David R. and Bahn, Volker and Ciuti, Simone and Boyce, Mark S. and Elith, Jane and Guillera‐Arroita, Gurutzeta and Hauenstein, Severin and Lahoz‐Monfort, José J. and Schröder, Boris and Thuiller, Wilfried and Warton, David I. and Wintle, Brendan A. and Hartig, Florian and Dormann, Carsten F. (2017). Cross‐validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography, 40, 913-929. https://doi.org/10.1111/ecog.02881
- [Ronneberger_2015] Ronneberger, Olaf and Fischer, Philipp and Brox, Thomas (2015). U-Net: Convolutional Networks for Biomedical Image Segmentation. Lecture Notes in Computer Science, 234-241. https://doi.org/10.1007/978-3-319-24574-4_28
- [Rosenfeld_Pfaltz_1966] Rosenfeld, Azriel and Pfaltz, John L. (1966). Sequential Operations in Digital Picture Processing. Journal of the ACM, 13, 471-494. https://doi.org/10.1145/321356.321357
- [Schaefer_1990] Schaefer, Joseph T. (1990). The Critical Success Index as an Indicator of Warning Skill. Weather and Forecasting, 5, 570-575. https://doi.org/10.1175/1520-0434(1990)005<0570:TCSIAA>2.0.CO;2
- [Sharma_2025] Sharma, Nirdesh; Saharia, Manabendra (2025). DeepSARFlood: Rapid and automated SAR-based flood inundation mapping using vision transformer-based deep ensembles with uncertainty estimates. Science of Remote Sensing. https://doi.org/10.1016/j.srs.2025.100203 [corpus record, text read; metadata from CrossRef/corpus]
- [Shen_2019] Shen, Xinyi and Wang, Dacheng and Mao, Kebiao and Anagnostou, Emmanouil and Hong, Yang (2019). Inundation Extent Mapping by Synthetic Aperture Radar: A Review. Remote Sensing, 11, 879. https://doi.org/10.3390/rs11070879
- [Shumilova_2025] Shumilova, O. and Sukhodolov, A. and Osadcha, N. and Oreshchenko, A. and Constantinescu, G. and Afanasyev, S. and Koken, M. and Osadchyi, V. and Rhoads, B. and Tockner, K. and Monaghan, M. T. and Schröder, B. and Nabyvanets, J. and Wolter, C. and Lietytska, O. and van de Koppel, J. and Magas, N. and Jähnig, S. C. and Lakisova, V. and Trokhymenko, G. and Venohr, M. and Komorin, V. and Stepanenko, S. and Khilchevskyi, V. and Domisch, S. and Blettler, M. and Gleick, P. and De Meester, L. and Grossart, H.-P. (2025). Environmental effects of the Kakhovka Dam destruction by warfare in Ukraine. Science, 387, 1181-1186. https://doi.org/10.1126/science.adn8655
- [Silwal_2026] Silwal, Abinash; Subedi, Anil; Tamrakar, Rajee; Dahal, Kshitij; Dahal, Dewasis; Ekpetere, Kenneth; Zhran, Mohamed (2026). A Comprehensive Review of Machine Learning and Deep Learning Methods for Flood Inundation Mapping. Earth. https://doi.org/10.3390/earth7020044 [corpus record, text read; metadata from CrossRef/corpus]
- [Singha_2020] Singha, Mrinal; Dong, Jinwei; Sarmah, Sangeeta; You, Nanshan; Zhou, Yan; Zhang, Geli; Doughty, Russell; Xiao, Xiangming (2020). Identifying floods and flood-affected paddy rice fields in Bangladesh based on Sentinel-1 imagery and Google Earth Engine. ISPRS Journal of Photogrammetry and Remote Sensing. https://doi.org/10.1016/j.isprsjprs.2020.06.011 [corpus record, text read; metadata from CrossRef/corpus]
- [Small_2011] Small, David (2011). Flattening Gamma: Radiometric Terrain Correction for SAR Imagery. IEEE Transactions on Geoscience and Remote Sensing, 49, 3081-3093. https://doi.org/10.1109/TGRS.2011.2120616
- [Stephens_2014] Stephens, Elisabeth and Schumann, Guy and Bates, Paul (2014). Problems with binary pattern measures for flood model evaluation. Hydrological Processes, 28, 4928-4937. https://doi.org/10.1002/hyp.9979
- [Tarpanelli_2022] Tarpanelli, Angelica; Mondini, Alessandro; Camici, Stefania (2022). Effectiveness of Sentinel-1 and Sentinel-2 for flood detection assessment in Europe. Natural Hazards and Earth System Sciences. https://doi.org/10.5194/nhess-22-2473-2022 [corpus record, text read; metadata from CrossRef/corpus]
- [Torres_2012] Torres, Ramon and Snoeij, Paul and Geudtner, Dirk and Bibby, David and Davidson, Malcolm and Attema, Evert and Potin, Pierre and Rommen, BjÖrn and Floury, Nicolas and Brown, Mike and Traver, Ignacio Navas and Deghaye, Patrick and Duesmann, Berthyl and Rosich, Betlem and Miranda, Nuno and Bruno, Claudio and L'Abbate, Michelangelo and Croci, Renato and Pietropaolo, Andrea and Huchler, Markus and Rostan, Friedhelm (2012). GMES Sentinel-1 mission. Remote Sensing of Environment, 120, 9-24. https://doi.org/10.1016/j.rse.2011.05.028
- [Tsiupa_2023] Tsiupa, I; Shevchenko, Taras; Plichko, L (2023). Study of dynamics of changes in the Kakhovka reservoir based on remote sensing data. . [conference paper (Monitoring 2023, Kyiv); no DOI in the corpus record] [corpus record, text read; metadata from CrossRef/corpus]
- [Tsyganskaya_2018] Tsyganskaya, Viktoriya; Martinis, Sandro; Marzahn, Philip; Ludwig, Ralf (2018). SAR-based detection of flooded vegetation – a review of characteristics and approaches. International Journal of Remote Sensing. https://doi.org/10.1080/01431161.2017.1420938 [corpus record, text read; metadata from CrossRef/corpus]
- [Tuan_2020] Tuan, Vu; Quang, Nguyen; Hang, Le (2020). Optimizing flood mapping using multi-synthetic aperture radar images for regions of the lower mekong basin in Vietnam. European Journal of Remote Sensing. https://doi.org/10.1080/22797254.2020.1859340 [corpus record, text read; metadata from CrossRef/corpus]
- [Tucker_1979] Tucker, Compton J. (1979). Red and photographic infrared linear combinations for monitoring vegetation. Remote Sensing of Environment, 8, 127-150. https://doi.org/10.1016/0034-4257(79)90013-0
- [Tupas_2023] Tupas, Mark Edwin and Roth, Florian and Bauer-Marschallinger, Bernhard and Wagner, Wolfgang (2023). Improving Sentinel-1 Flood Maps Using a Topographic Index as Prior in Bayesian Inference. Water, 15, 4034. https://doi.org/10.3390/w15234034
- [Tutova_2025] Tutova, H; Lisovets, O; Kunakh, O; Zhukov, O; Khmelnitsky, Bogdan; Honchar, Oles (2025). Procrustean analysis of the set of spectral indices reveals the transformations in plant community hemeroby and functional structure induced by anthropogenic disasters. Biosystems Diversity. https://doi.org/10.15421/012528 [corpus record, text read; metadata from CrossRef/corpus]
- [Twele_2016] Twele, André and Cao, Wenxi and Plank, Simon and Martinis, Sandro (2016). Sentinel-1-based flood mapping: a fully automated processing chain. International Journal of Remote Sensing, 37, 2990-3004. https://doi.org/10.1080/01431161.2016.1192304
- [Valavi_2019] Valavi, Roozbeh and Elith, Jane and Lahoz‐Monfort, José J. and Guillera‐Arroita, Gurutzeta (2019). <scp>block</scp> <scp>CV</scp> : An <scp>r</scp> package for generating spatially or environmentally separated folds for <i>k</i> ‐fold cross‐validation of species distribution models. Methods in Ecology and Evolution, 10, 225-232. https://doi.org/10.1111/2041-210X.13107
- [Vyshnevskyi_2023] Vyshnevskyi, Viktor and Shevchuk, Serhii and Komorin, Viktor and Oleynik, Yurii and Gleick, Peter (2023). The destruction of the Kakhovka dam and its consequences. Water International, 48, 631-647. https://doi.org/10.1080/02508060.2023.2247679
- [Vyshnevskyi_2024] Vyshnevskyi, Viktor (2024). NATURAL PROCESSES IN THE AREA OF THE FORMER KAKHOVSKE RESERVOIR AFTER THE DESTRUCTION OF THE KAKHOVKA HPP. Journal of Landscape Ecology. https://doi.org/10.2478/jlecol-2024-0014 [corpus record, text read; metadata from CrossRef/corpus]
- [Wagner_2020] Wagner, W; Freeman, V; Cao, S; Matgen, P; Chini, M; Salamon, P; Mccormick, N; Martinis, S; Bauer-Marschallinger, B; Navacchi, C; Schramm, M; Reimer, C; Briese, C (2020). DATA PROCESSING ARCHITECTURES FOR MONITORING FLOODS USING SENTINEL-1. ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences. https://doi.org/10.5194/isprs-annals-v-3-2020-641-2020 [corpus record, text read; metadata from CrossRef/corpus]
- [Wagner_2026] Wagner, Wolfgang and Bauer-Marschallinger, Bernhard and Roth, Florian and Raiger-Stachl, Tobias and Reimer, Christoph and McCormick, Niall and Matgen, Patrick and Chini, Marco and Li, Yu and Martinis, Sandro and Wieland, Marc and Kraft, Franziska and Festa, Davide and Hassaan, Muhammed and Tupas, Mark Edwin and Zhao, Jie and Seewald, Michaela and Riffler, Michael and Molini, Luca and Kidd, Richard and Briese, Christian and Salamon, Peter (2026). The fully-automatic Sentinel-1 Global Flood Monitoring service: Scientific challenges and future directions. Remote Sensing of Environment, 333, 115108. https://doi.org/10.1016/j.rse.2025.115108
- [Wilson_Sader_2002] Wilson, Emily Hoffhine and Sader, Steven A (2002). Detection of forest harvest type using multiple dates of Landsat TM imagery. Remote Sensing of Environment, 80, 385-396. https://doi.org/10.1016/S0034-4257(01)00318-2
- [Xu_2006] Xu, Hanqiu (2006). Modification of normalised difference water index (NDWI) to enhance open water features in remotely sensed imagery. International Journal of Remote Sensing, 27, 3025-3033. https://doi.org/10.1080/01431160600589179
- [Yailymov_2025] Yailymov, Bohdan; Yailymova, Hanna; Kolotii, Andrii; Shelestov, Andrii; Skakun, Sergii; Baber, Sheila; Becker-Reshef, Inbal; Kussul, Nataliia (2025). Flooded and Irrigation Area Monitoring After the Kakhovka Dam Disaster Based on Machine Learning and Satellite Data. IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing. https://doi.org/10.1109/jstars.2025.3592368 [corpus record, text read; metadata from CrossRef/corpus]
- [Yamazaki_2017] Yamazaki, Dai; Ikeshima, Daiki; Tawatari, Ryunosuke; Yamaguchi, Tomohiro; O'loughlin, Fiachra; Neal, Jeffery; Sampson, Christopher; Kanae, Shinjiro; Bates, Paul (2017). A high‐accuracy map of global terrain elevations. Geophysical Research Letters. https://doi.org/10.1002/2017gl072874 [corpus record, text read; metadata from CrossRef/corpus]
- [Yamazaki_2019] Yamazaki, Dai; Ikeshima, Daiki; Sosa, Jeison; Bates, Paul; Allen, George; Pavelsky, Tamlin (2019). MERIT Hydro: A High‐Resolution Global Hydrography Map Based on Latest Topography Dataset. Water Resources Research. https://doi.org/10.1029/2019wr024873 [corpus record, text read; metadata from CrossRef/corpus]
- [Yi_2025] Yi, Shuang and Li, Hao‐si and Han, Shin‐Chan and Sneeuw, Nico and Yuan, Chunyu and Song, Chunqiao and Yeo, In‐Young and McCullough, Christopher M. (2025). Quantification of the Flood Discharge Following the 2023 Kakhovka Dam Breach Using Satellite Remote Sensing. Water Resources Research, 61, e2024WR038314. https://doi.org/10.1029/2024WR038314
- [Yu_2024] Yu, Linpeng; Zhang, Haowei; Gong, Wei; Ma, Xin (2024). Validation of Mainland Water Level Elevation Products From SWOT Satellite. IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing. https://doi.org/10.1109/jstars.2024.3435363 [corpus record, text read; metadata from CrossRef/corpus]
- [Zanaga_2022] Zanaga, Daniele and Van De Kerchove, Ruben and Daems, Dirk and De Keersmaecker, Wanda and Brockmann, Carsten and others (2022). ESA WorldCover 10 m 2021 v200. Zenodo. https://doi.org/10.5281/zenodo.7254221
- [Zhao_2021] Zhao, Jie and Pelich, Ramona and Hostache, Renaud and Matgen, Patrick and Cao, Senmao and Wagner, Wolfgang and Chini, Marco (2021). Deriving exclusion maps from C-band SAR time-series in support of floodwater mapping. Remote Sensing of Environment, 265, 112668. https://doi.org/10.1016/j.rse.2021.112668
- [Zhao_2025] Zhao, Jie; Li, Ming; Li, Yu; Matgen, Patrick; Chini, Marco (2025). Urban Flood Mapping Using Satellite Synthetic Aperture Radar Data: A review of characteristics, approaches, and datasets. IEEE Geoscience and Remote Sensing Magazine. https://doi.org/10.1109/mgrs.2024.3496075 [corpus record, text read; metadata from CrossRef/corpus]
- [Zheng_2018] Zheng, Xing and Maidment, David R. and Tarboton, David G. and Liu, Yan Y. and Passalacqua, Paola (2018). GeoFlood: Large‐Scale Flood Inundation Mapping Based on High‐Resolution Terrain Analysis. Water Resources Research, 54. https://doi.org/10.1029/2018WR023457
- [Zuo_2024] Zuo, Chen; Zhang, Haowei; Ma, Xin; Gong, Wei (2024). Impact Assessment of Flood Events Based on Multisource Satellite Remote Sensing: The Case of Kahovka Dam. IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing. https://doi.org/10.1109/jstars.2024.3490756 [corpus record, text read; metadata from CrossRef/corpus]

### Unresolved (grey literature, datasets, software — no DOI)

- [Iakubovskii_2019] Iakubovskii, Pavel (2019). Segmentation Models Pytorch. GitHub repository. — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
- [SWOT_RiverSP_v2] JPL D-56413 (2023). SWOT Level 2 River Single-Pass Vector Data Product, Version 2.0. PO.DAAC. — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
- [CEOBS_2023] Conflict and Environment Observatory (2023). Analysing the environmental consequences of the Kakhovka dam collapse. \urlhttps://ceobs.org/analysing-the-environmental-consequences-of-the-kakhovka-dam-collapse/. — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
- [REACH_2023] REACH Initiative (2023). Ukraine situational overview: Kakhovka Dam breach (16 June 2023). ReliefWeb. — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
- [UNEP_2023] UNEP (2023). Rapid environmental assessment of Kakhovka Dam breach, Ukraine, 2023. . — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
- [Paper1_Nikoriak_2026] Nikoriak, Viktor (2026). Post-breach transformation of the Kakhovka Reservoir: water-surface slopes from ICESat-2, SWOT and gauge observations. . — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
- [Paper2_Nikoriak_2026] Nikoriak, Viktor (2026). Bathymetry and a seamless terrain model of the former Kakhovka Reservoir and the lower Dnipro. . — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
- [Apicella_2025] Apicella, Andrea and Isgr\`o, Francesco and Prevete, Roberto (2025). Don't push the button! Exploring data leakage risks in machine learning and transfer learning. Artificial Intelligence Review, 58. — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
- [UNOSAT_3616_2023] UNOSAT (2023). Kakhovka dam breach: satellite-detected flood water extent, Kherson oblast, Ukraine, as of 9 June 2023 (product 3616). UNOSAT / UNITAR; dataset on HDX: Satellite flood water extent between the Nova Kakhovka dam wall and the Dnipro river mouth, Khersonska oblast, Ukraine (FL20230606UKR); the 620 km2 figure is quoted in OCHA Flash Update 6 (14 June 2023). — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
- [UNOSAT_3623_2023] UNOSAT (2023). Kakhovka dam breach: satellite-detected flood water extent as of 13 June 2023 (product 3623). UNOSAT / UNITAR; HDX dataset FL20230606UKR; the 180 km2 figure is quoted in OCHA Flash Update 7 (16 June 2023). — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
- [Rikimaru_2002] Rikimaru, Atsushi and Roy, P. S. and Miyatake, S. (2002). Tropical forest cover density mapping. Tropical Ecology, 43, 39--47. — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
- [Pedregosa_2011] Pedregosa, Fabian and Varoquaux, Gaël and Gramfort, Alexandre and Michel, Vincent and Thirion, Bertrand and Grisel, Olivier and Blondel, Mathieu and Prettenhofer, Peter and Weiss, Ron and Dubourg, Vincent and Vanderplas, Jake and Passos, Alexandre and Cournapeau, David and Brucher, Matthieu and Perrot, Matthieu and Duchesnay, Édouard (2011). Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12, 2825--2830. — NOT resolvable in CrossRef/OpenAlex (07b): cite with access date or drop
