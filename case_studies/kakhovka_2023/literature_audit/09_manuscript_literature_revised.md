<!-- 09_manuscript_literature_revised.md — built 2026-09-28 from publication/manuscript.md (bundle of 2026-09-25/26) by tools/paper3_audit/revise.py; 24 documented changes (10_change_log.md). Table values unchanged. -->

# Daily inundation after the Kakhovka dam breach reconstructed from the observed water surface and terrain, checked against Sentinel-1 and ICESat-2, and what EO-based flood products recover under weak labels

**Manuscript draft (Paper 3 of the Kakhovka series), generated 2026-09-25 from `manuscript_template.md` by
`workflows/paper/fill_manuscript.py`. Every number below is resolved from a committed publication table cell
(`publication/tables/T*.csv`, manifest with sha256); claim identifiers [C01]–[C14] refer to `evidence_matrix.csv`; terms are frozen in `TERMINOLOGY.md`.
Literature values are context and are flagged VERIFY in `references_to_verify.md`. Numbers are printed from the table cells at the
stated precision with round-half-to-even (196.5 → 196, 790.5 → 790); the cell keeps the full value.**

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
night ICESat-2 tracks that sample it the DEM agrees with the altimetry to a few centimetres in the median (p10–p90 spread of a few decimetres), so the available ICESat-2
observations give no evidence for a DEM bias large enough to explain it; 120 km² allowed
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

### 3.2 Terrain rule, baseline and the definition of "new inundation"

A cell is water on day t if its DEM lies below the water surface and it is 8-connected, through such cells, to the pre-breach
optical water network (p60 pre-water frequency ≥ 20 %), within 10 km of pre-breach water and downstream of the dam
(*connected ceiling*). Two other rules bound it: the p42 rule (additionally HAND < WSE − 1 m, channel-connected through the
mapped drainage; a lower bound because the delta drainage is incompletely mapped) and the ceiling without connectivity.
The connectivity requirement is not inherited from the terrain-index methods we build on: HAND-type methods "do not
preserve hydraulic connectivity (i.e., floodplain cells lower than the channel water height are denoted as flooded
whether or not there is a physical flow path to them)" (Bates 2022), and GeoFlood by design flags "local depressions such
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

### 3.5 Surface context: RF20

A random forest (Breiman 2001; for its use in land-cover mapping see Belgiu and Drăguţ 2016) on PRE-event Sentinel-2 composite predictors, trained on ESA WorldCover 2021 with a purity filter, classifies
the surface at 20 m into water, cropland, grass/low vegetation, forest, wetland/reed, built-up, bare sand and uncertain
(p73, frozen before any arm was trained). Its per-class precision, recall and F1 in spatial-block 5-fold cross-validation and in
the frame transfers B1↔B2 are agreement with the training reference (T09, T10), not validation. It supplies the evaluation
strata of the arms and the classes of the ontology.

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
between sources; the peak stages by 8 June that Lehnigk et al. 2026 report from the same SWOT data are consistent with it) — the areal maximum and the peak stage are different quantities, and the day of the
areal maximum is a property of the reconstructed series, not an observation. It is 196 km² on 9 June,
118 km² on 13 June,
39 km² on 18 June and
3 km² on 21 June, when the Kherson stage is back at
0.74 m (Fig04, T12) [C03]. The reconstructed new-water volume
reaches 566 hm³ (median; p05–p95
545–596 hm³;
deterministic nominal run 509 hm³) [C02]. All areas and volumes after 5 June are Monte-Carlo medians unless marked as a nominal run.
The rule and DEM sensitivities are deterministic runs and compare with the nominal connected run (235 km²), not with the median:
the p42 HAND rule gives 247 km² at the reconstructed areal maximum; the
ceiling without connectivity 254 km². The largest single
term is definitional: with the DEM as delivered, the reed beds count as new inundation and the areal maximum is
347 km². Inside the p42 floodplain
domain the areal maximum is 163 km²; the Inhulets valley, treated as
backwater with its own SWOT nodes, peaks at 50 km² on 9 June.
The depth and duration maps (Fig07) show the 7–8 June water more than 4 m deep on the right-bank floodplain below the dam and
the delta channels, and inundation lasting more than a week only in the floodplain lows and the delta.

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
pre-existing water as a separate class (T16, literature_reported, VERIFY), a quantity closer in kind to the newly inundated area
than to the total water-surface area, and it differs further in AOI (the liman reach, frame B3, is not part of this domain),
in temporal semantics (cumulative vs daily snapshot) and in reference water (§4.6).

**Uncertainty per day [C07].** On 7 June the primary spatial draws give relative half-widths of
4 % for the area and
5 % for the volume. The deterministic nominal run lies below its own
interval: the medians are +5 % (area) and
+11 % (volume) above it, and the nominal area and volume fall below the p05 on the peak days
(T12b flags every such day). The interval is therefore not centred on the nominal run, and the reported central value is the
Monte-Carlo median with p05–p95, the nominal run in brackets. The mechanism is the one of §3.3 — correlated DEM perturbations open additional connections and add depth (Darnell et al. 2008; Hawker et al. 2018) — but which error term carries most of the shift has not been attributed. The emulator sensitivity envelope (§3.3) is wider — newly inundated area
214–293 km²
(p25–p75 235–268 km²),
total water-surface area 758–837 km²
(Fig04, candles) — and represents a different distribution (parameter-space propagation); the two are never mixed. The daily
change of the newly inundated area (bars in Fig04) shows the filling on 6–7 June and the draining at 30–40 km² per day between
10 and 18 June.

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
on 21 June in the corridor) is scattered on fields and sand while the gauge is at its pre-breach level and the reconstruction is
at 3 km²: these detections are not supported as connected breach-induced inundation by the available terrain and water-surface constraints. Their pattern — fields and sand far above any water surface of the event — is consistent with a known C-band look-alike behaviour (smooth or wet bare surfaces and shadow scatter like water; Shen et al. 2019), but whether they are non-water, local ponding after rain or water outside the assumed connectivity is not tested here (§4.3). The large-scale
recession seen by Sentinel-1 inside the floodplain (T19) follows the reconstruction and the gauge (Fig04).

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
literature_reported, VERIFY) — are flooded *land*, closer in kind to the newly inundated area than to the total water-surface
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

*Label effect (Fig03; paired differences in T06 and T07b).* At fixed inputs, U2 predicts 15.3 km² of flood on
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
Sentinel-1 acquisitions of 6 and 9 June, and it is not the day of the peak stage at Kherson (8 June; Lehnigk et al. 2026 report
downstream peak stages by 8 June from the same SWOT data). Maximum extent and maximum stage are different quantities whose timing
changes along a 100 km reach — floodplain storage and drainage produce hysteresis between extent, volume and stage (Fassoni-Andrade et al. 2023) — and the day of the areal maximum is the most model-dependent number of this paper: it is where the
water-surface-constrained reconstruction adds what no acquisition can give, and where Paper 5's hydraulic model will be tested.

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
the deterministic nominal run lies below its own Monte-Carlo p05 on the days of the areal maximum — the mechanism is the connection-opening effect of correlated DEM perturbations (§3.3), but its attribution to the individual error terms is open; the
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

## References

`docs/references.bib`; entries added for this paper carry `note = {VERIFY}` until checked (`references_to_verify.md`).

## References added or re-verified by the literature audit

Keys marked [verified] come from `07_references_verified.bib`; corpus records name the local file that was read. Entries already in `docs/references.bib` and unchanged by this audit are not repeated here.

- **Agerbeek_2024** — Agerbeek, Bas; Knepflé, Maxim; Witsenburg, Florian; Jonkman, Sebastiaan (2024). Near real-time flood risk modelling in response to increasing uncertainties in flood predictions: Insights from the Kakhovka Dam breach in Ukraine. *Journal of Coastal and Riverine Flood Risk*. doi:10.59490/jcrfr.2024.0016 [corpus record `10.59490_jcrfr.2024.0016`; text read; metadata CrossRef]
- **Amitrano_2024** — Amitrano, Donato; Di Martino, Gerardo; Di Simone, Alessio; Imperatore, Pasquale (2024). Flood Detection with SAR: A Review of Techniques and Datasets. *Remote Sensing*. doi:10.3390/rs16040656 [corpus record `remotesensing-16-00656-v2`; text read; metadata corpus]
- **Apicella_2025** — Apicella, Andrea and Isgr\`o, Francesco and Prevete, Roberto (2025). Don't push the button! Exploring data leakage risks in machine learning and transfer learning. Artificial Intelligence Review. [grey literature / no resolvable DOI — see 07b_references_unresolved.md; cite with access date]
- **Bates_2022** — Bates, Paul (2021). Annual Review of Fluid Mechanics Flood Inundation Prediction. **. doi:10.1146/annurev-fluid-030121-113138 [corpus record `annurev-fluid-030121-113138`; text read; metadata corpus]
- **Baugh_2013** — Baugh, Calum; Bates, Paul; Schumann, Guy; Trigg, Mark (2013). SRTM vegetation removal and hydrodynamic modeling accuracy. *Water Resources Research*. doi:10.1002/wrcr.20412 [corpus record `10.1002_wrcr.20412`; text read; metadata corpus]
- **Belgiu_Dragut_2016** — Belgiu, Mariana and Drăguţ, Lucian (2016). Random forest in remote sensing: A review of applications and future directions. *ISPRS Journal of Photogrammetry and Remote Sensing*, 114, 24-31. doi:10.1016/j.isprsjprs.2016.01.011 [verified: CrossRef/OpenAlex, 07]
- **Biancamaria_2016** — Biancamaria, Sylvain and Lettenmaier, Dennis P. and Pavelsky, Tamlin M. (2016). The SWOT Mission and Its Capabilities for Land Hydrology. *Surveys in Geophysics*, 37, 307-337. doi:10.1007/s10712-015-9346-y [verified: CrossRef/OpenAlex, 07]
- **Bonafilia_2020** — Bonafilia, Derrick and Tellman, Beth and Anderson, Tyler and Issenberg, Erica (2020). Sen1Floods11: a georeferenced dataset to train and test deep learning flood algorithms for Sentinel-1. *2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW)*, 835-845. doi:10.1109/cvprw50498.2020.00113 [verified: CrossRef/OpenAlex, 07]
- **Breiman_2001** — Breiman, Leo (2001). Random Forests. *Machine Learning*, 45, 5-32. doi:10.1023/A:1010933404324 [verified: CrossRef/OpenAlex, 07]
- **CEOBS_2023** — {Conflict and Environment Observatory} (2023). Analysing the environmental consequences of the Kakhovka dam collapse. \url{https://ceobs.org/analysing-the-environmental-consequences-of-the-kakhovka-dam-collapse/}. [grey literature / no resolvable DOI — see 07b_references_unresolved.md; cite with access date]
- **Cohen_2019** — Cohen, Sagy and Raney, Austin and Munasinghe, Dinuke and Loftis, J. Derek and Molthan, Andrew and Bell, Jordan and Rogers, Laura and Galantowicz, John and Brakenridge, G. Robert and Kettner, Albert J. and Huang, Yu-Fen and Tsang, Yin-Phan (2019). The Floodwater Depth Estimation Tool (FwDET v2.0) for improved remote sensing analysis of coastal flooding. *Natural Hazards and Earth System Sciences*, 19, 2053-2065. doi:10.5194/nhess-19-2053-2019 [verified: CrossRef/OpenAlex, 07]
- **Cunha_2012** — Cunha, Luciana; Mandapaka, Pradeep; Krajewski, Witold; Mantilla, Ricardo; Bradley, Allen (2012). Impact of radar‐rainfall error structure on estimated flood magnitude across scales: An investigation based on a parsimonious distributed hydrological model. *Water Resources Research*. doi:10.1029/2012wr012138 [corpus record `10.1029_2012wr012138`; text read; metadata corpus]
- **Darnell_2008** — Darnell, Amii R. and Tate, Nicholas J. and Brunsdon, Chris (2008). Improving user assessment of error implications in digital elevation models. *Computers, Environment and Urban Systems*, 32, 268-277. doi:10.1016/j.compenvurbsys.2008.02.003 [verified: CrossRef/OpenAlex, 07]
- **DePaiva_2013** — De Paiva, Rodrigo; Buarque, Diogo; Collischonn, Walter; Bonnet, Marie‐paule; Frappart, Frédéric; Calmant, Stephane; Bulhões Mendes, Carlos (2013). Large‐scale hydrologic and hydrodynamic modeling of the Amazon River basin. *Water Resources Research*. doi:10.1002/wrcr.20067 [corpus record `10.1002_wrcr.20067`; text read; metadata corpus]
- **FassoniAndrade_2023** — César Fassoni-Andrade, Alice; Cauduro Dias De Paiva, Rodrigo; Wongchuig, Sly; Barbosa, Cláudio; Durand, Fabien; Sanna Freire Silva, Thiago (2023). Expressive fluxes over Amazon floodplain revealed by 2D hydrodynamic modelling. *Journal of Hydrology*. doi:10.1016/j.jhydrol.2023.130122 [corpus record `model_hec_ras_0609`; text read; metadata corpus]
- **Feyisa_2014** — Feyisa, Gudina L. and Meilby, Henrik and Fensholt, Rasmus and Proud, Simon R. (2014). Automated Water Extraction Index: A new technique for surface water mapping using Landsat imagery. *Remote Sensing of Environment*, 140, 23-35. doi:10.1016/j.rse.2013.08.029 [verified: CrossRef/OpenAlex, 07]
- **Gao_1996** — Gao, Bo-cai (1996). NDWI—A normalized difference water index for remote sensing of vegetation liquid water from space. *Remote Sensing of Environment*, 58, 257-266. doi:10.1016/S0034-4257(96)00067-3 [verified: CrossRef/OpenAlex, 07]
- **Garg_2023** — Garg, Shubhika; Feinstein, Ben; Timnat, Shahar; Batchu, Vishal; Dror, Gideon; Rosenthal, Adi; Gulshan, Varun (2023). Cross-modal distillation for flood extent mapping. *Environmental Data Science*. doi:10.1017/eds.2023.34 [corpus record `cross-modal-distillation-for-flood-extent-mapping`; text read; metadata corpus]
- **Grimaldi_2020** — Grimaldi, S. and Xu, J. and Li, Y. and Pauwels, V.R.N. and Walker, J.P. (2020). Flood mapping under vegetation using single SAR acquisitions. *Remote Sensing of Environment*, 237, 111582. doi:10.1016/j.rse.2019.111582 [verified: CrossRef/OpenAlex, 07]
- **Guo_2025** — Guo, Xinqi; Wang, Q; Western, Andrew; Ryu, Dongryeol; Sharples, Wendy; Hou, Jiawei (2025). Flood monitoring: A hydrologically guided method for infilling incomplete flood inundation maps derived from satellite images. *Journal of Hydrology*. doi:10.1016/j.jhydrol.2025.133365 [corpus record `1-s2.0-S0022169425007036-main`; text read; metadata corpus]
- **Hawker_2018** — Hawker, Laurence and Bates, Paul and Neal, Jeffrey and Rougier, Jonathan (2018). Perspectives on Digital Elevation Model (DEM) Simulation for Flood Modeling in the Absence of a High-Accuracy Open Access Global DEM. *Frontiers in Earth Science*, 6, 233. doi:10.3389/feart.2018.00233 [verified: CrossRef/OpenAlex, 07]
- **Hawker_2022** — Hawker, Laurence and Uhe, Peter and Paulo, Luntadila and Sosa, Jeison and Savage, James and Sampson, Christopher and Neal, Jeffrey (2022). A 30 m global map of elevation with forests and buildings removed. *Environmental Research Letters*, 17, 024016. doi:10.1088/1748-9326/ac4d4f [verified: CrossRef/OpenAlex, 07]
- **He_2024** — He, Yongjun and Wang, Jinfei and Zhang, Ying and Liao, Chunhua (2024). An efficient urban flood mapping framework towards disaster response driven by weakly supervised semantic segmentation with decoupled training samples. *ISPRS Journal of Photogrammetry and Remote Sensing*, 207, 338-358. doi:10.1016/j.isprsjprs.2023.12.009 [verified: CrossRef/OpenAlex, 07]
- **Hohle_2009** — Höhle, Joachim and Höhle, Michael (2009). Accuracy assessment of digital elevation models by means of robust statistical methods. *ISPRS Journal of Photogrammetry and Remote Sensing*, 64, 398-406. doi:10.1016/j.isprsjprs.2009.02.003 [verified: CrossRef/OpenAlex, 07]
- **Iqbal_2023** — Iqbal, Ashik; Mondal, M; Veerbeek, William; Khan, M; Hakvoort, Hans (2023). Effectiveness of <scp>UAV</scp>‐based <scp>DTM</scp> and satellite‐based <scp>DEMs</scp> for local‐level flood modeling in <scp>Jamuna</scp> floodplain. *Journal of Flood Risk Management*. doi:10.1111/jfr3.12937 [corpus record `AshikIqbal_EffectivenessofDEMsforFloodModeling_jfr3.12937`; text read; metadata corpus]
- **Jarrett_2023** — Jarrett, Sean; Hölbling, Daniel (2023). Spatial Evaluation of a Natural Flood Management Project Using SAR Change Detection. *Water*. doi:10.3390/w15122182 [corpus record `water-15-02182`; text read; metadata corpus]
- **Jiao_2025** — Jiao, Zhijun; Zhang, Zhimei; Chen, Biyan; Mahmood, Syed; Wu, Lixin (2025). Knowledge-Driven Flood Intelligent Monitoring (KDFIM) Method: Analyzing the Kakhovka Dam Destruction Incident. *IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing*. doi:10.1109/jstars.2025.3594119 [corpus record `Knowledge-Driven_Flood_Intelligent_Monitoring_KDFIM_Method_Analyzing_the_Kakhovka_Dam_Destruction_Incident`; text read; metadata corpus]
- **Johnson_2019** — Johnson, J. Michael and Munasinghe, Dinuke and Eyelade, Damilola and Cohen, Sagy (2019). An integrated evaluation of the National Water Model (NWM)–Height Above Nearest Drainage (HAND) flood mapping methodology. *Natural Hazards and Earth System Sciences*, 19, 2405-2420. doi:10.5194/nhess-19-2405-2019 [verified: CrossRef/OpenAlex, 07]
- **Kadam_2024** — Kadam, Piyusha B. and Thakur, Praveen K. and Dwivedi, Sanjay K. and Garg, Vaibhav and Dhote, Pankja R. (2024). Dam Breach Analysis and Damage Assessment of Nova Kakhovka Dam using Satellite data and 1D and 2D Hydrodynamic Modeling. *The International Archives of the Photogrammetry, Remote Sensing and Spatial Information Sciences*, XLVIII-3-2024, 251-256. doi:10.5194/isprs-archives-xlviii-3-2024-251-2024 [verified: CrossRef/OpenAlex, 07]
- **Katiyar_2021** — Katiyar, Vaibhav; Tamkuan, Nopphawan; Nagai, Masahiko (2021). Near-Real-Time Flood Mapping Using Off-the-Shelf Models with SAR Imagery and Deep Learning. *Remote Sensing*. doi:10.3390/rs13122334 [corpus record `10.3390_rs13122334`; text read; metadata corpus]
- **Kulp_Strauss_2019** — Kulp, Scott; Strauss, Benjamin (2019). New elevation data triple estimates of global vulnerability to sea-level rise and coastal flooding. *Nature Communications*. doi:10.1038/s41467-019-12808-z [corpus record `10.1038_s41467-019-12808-z`; text read; metadata CrossRef]
- **Kuzemko_2024** — Kuzemko, Anna; Prylutskyi, Oleh; Kolomytsev, Grygoriy; Didukh, Yakiv; Moysiyenko, Ivan; Borsukevych, Liubov; Chusova, Olga; Splodytel, Anastasiia; Khodosovtsev, Oleksandr (2024). Reach the bottom: plant cover of the former Kakhovka Reservoir, Ukraine. **. doi:10.21203/rs.3.rs-4137799/v1 [corpus record `Reach_the_bottom_plant_cover_of_the_form`; text read; metadata CrossRef]
- **Kuzemko_2025** — Kuzemko, Anna; Prylutskyi, Oleh; Kolomytsev, Gryg; Didukh, Ya.; Moysiyenko, Ivan; Borsukevych, Li; Chusova, Olga; Khodosovtsev, Oleksandr (2025). Initial stages of revegetation at the bottom of the drained Kakhovka Reservoir (Ukraine): synthesis of field surveys and remote sensing. *Ukrainian Botanical Journal*. doi:10.15407/ukrbotj82.05.488 [corpus record `ukrbotj-2025-82-5-488`; text read; metadata corpus]
- **Lacaux_2007** — Lacaux, J.P. and Tourre, Y.M. and Vignolles, C. and Ndione, J.A. and Lafaye, M. (2007). Classification of ponds from high-spatial resolution remote sensing: Application to Rift Valley Fever epidemics in Senegal. *Remote Sensing of Environment*, 106, 66-74. doi:10.1016/j.rse.2006.07.012 [verified: CrossRef/OpenAlex, 07]
- **Le_2026** — Le, Xuan-Hien and Koyama, Naoki and Yamada, Tadashi (2026). Impacts of elevation bias and topographic uncertainty on flood modeling: model robustness and floodplain sensitivity mapping in a lowland River Basin. *Journal of Hydrology*, 666, 134832. doi:10.1016/j.jhydrol.2025.134832 [verified: CrossRef/OpenAlex, 07]
- **Lehnigk_2026** — Lehnigk, K. E. and Pavelsky, T. M. and Lang, K. A. (2026). SWOT Satellite Observations of the Kakhovka Dam Break Flood Highlight Limitations of Outburst Flood Models. *Geophysical Research Letters*, 53, e2025GL120832. doi:10.1029/2025gl120832 [verified: CrossRef/OpenAlex, 07]
- **Magas_2023** — Magas, N; Yakovenko, M; Shevchenko, Taras (2023). Comparative analysis of the shallowing of the Kakhovska reservoir based on the data of RS (remote sensing). **. doi: [corpus record `Mon23-147`; text read; metadata corpus; conference paper (Monitoring 2023, Kyiv); no DOI in the corpus record]
- **Main-Knorn_2017** — Main-Knorn, Magdalena and Pflug, Bringfried and Louis, Jerome and Debaecker, Vincent and Müller-Wilm, Uwe and Gascon, Ferran (2017). Sen2Cor for Sentinel-2. *Image and Signal Processing for Remote Sensing XXIII*, 3. doi:10.1117/12.2278218 [verified: CrossRef/OpenAlex, 07]
- **Maiti_2022** — Maiti, A. and Oude Elberink, S. J. and Vosselman, G. (2022). EFFECT OF LABEL NOISE IN SEMANTIC SEGMENTATION OF HIGH RESOLUTION AERIAL IMAGES AND HEIGHT DATA. *ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences*, V-2-2022, 275-282. doi:10.5194/isprs-annals-V-2-2022-275-2022 [verified: CrossRef/OpenAlex, 07]
- **Martinis_Plank_2018** — Martinis, Sandro; Plank, Simon; Ćwik, Kamila (2018). The Use of Sentinel-1 Time-Series Data to Improve Flood Monitoring in Arid Areas. *Remote Sensing*. doi:10.3390/rs10040583 [corpus record `remotesensing-10-00583`; text read; metadata corpus]
- **McFeeters_1996** — McFEETERS, S. K. (1996). The use of the Normalized Difference Water Index (NDWI) in the delineation of open water features. *International Journal of Remote Sensing*, 17, 1425-1432. doi:10.1080/01431169608948714 [verified: CrossRef/OpenAlex, 07]
- **Milletari_2016** — Milletari, Fausto and Navab, Nassir and Ahmadi, Seyed-Ahmad (2016). V-Net: Fully Convolutional Neural Networks for Volumetric Medical Image Segmentation. *2016 Fourth International Conference on 3D Vision (3DV)*, 565-571. doi:10.1109/3DV.2016.79 [verified: CrossRef/OpenAlex, 07]
- **Monti_2024** — Monti, Roberto and Rossi, Lorenzo and Reguzzoni, Mirko (2024). The Nova Kakhovka dam collapse flooding as seen from Sentinel-1 SAR satellite images. *Advances in Geodesy and Geoinformation*, 50-50. doi:10.24425/agg.2023.146162 [verified: CrossRef/OpenAlex, 07]
- **Neal_2012** — Neal, Jeffrey; Schumann, Guy; Bates, Paul (2012). A subgrid channel model for simulating river hydraulics and floodplain inundation over large and data sparse areas. *Water Resources Research*. doi:10.1029/2012wr012514 [corpus record `Water Resources Research - 2012 - Neal - A subgrid channel model for simulating river hydraulics and floodplain inundation`; text read; metadata corpus]
- **Nobre_2011** — Nobre, A.D. and Cuartas, L.A. and Hodnett, M. and Rennó, C.D. and Rodrigues, G. and Silveira, A. and Waterloo, M. and Saleska, S. (2011). Height Above the Nearest Drainage – a hydrologically relevant new terrain model. *Journal of Hydrology*, 404, 13-29. doi:10.1016/j.jhydrol.2011.03.051 [verified: CrossRef/OpenAlex, 07]
- **Normandin_2024** — Normandin, Cassandra; Frappart, Frédéric; Baghdadi, Nicolas; Bourrel, Luc; Luque, Santiago; Ygorra, Bertrand; Kitambo, Benjamin; Papa, Fabrice; Riazanoff, Serge; Wigneron, Jean-Pierre; Zeng, Jiangyuan; Xu, Nan; Huang, Qi (2024). First results of the surface water ocean topography (SWOT) observations to rivers elevation profiles in the Cuvette Centrale of the Congo Basin. *Frontiers in Remote Sensing*. doi:10.3389/frsen.2024.1466695 [corpus record `10.3389_frsen.2024.1466695`; text read; metadata CrossRef]
- **Novitskyi_2024** — Novitskyi, Roman; Hapich, Hennadii; Maksymenko, Maksym; Kutishchev, Pavlo; Gasso, Viktor; Afanasyev, Sergiy; Banaduc, Doru; Blaga, Lucian; Sellheim, Nikolas (2024). Losses in fishery ecosystem services of the Dnipro river Delta and the Kakhovske reservoir area caused by military actions in Ukraine. *Frontiers in Environmental Science*. doi:10.3389/fenvs.2024.1301435 [corpus record `10.3389_fenvs.2024.1301435`; text read; metadata CrossRef]
- **Olofsson_2014** — Olofsson, Pontus and Foody, Giles M. and Herold, Martin and Stehman, Stephen V. and Woodcock, Curtis E. and Wulder, Michael A. (2014). Good practices for estimating area and assessing accuracy of land change. *Remote Sensing of Environment*, 148, 42-57. doi:10.1016/j.rse.2014.02.015 [verified: CrossRef/OpenAlex, 07]
- **Pichura_2025** — Pichura, Vitalii and Potravka, Larysa and Boiko, Pavlo (2025). Climatic and hydrological conditions for the formation of vegetation cover in the drained Kakhovka reservoir’s territory. *Ecological Engineering \&amp; Environmental Technology*, 26, 357-373. doi:10.12912/27197050/202227 [verified: CrossRef/OpenAlex, 07]
- **Renno_2008** — Rennó, Camilo Daleles and Nobre, Antonio Donato and Cuartas, Luz Adriana and Soares, João Vianei and Hodnett, Martin G. and Tomasella, Javier and Waterloo, Maarten J. (2008). HAND, a new terrain descriptor using SRTM-DEM: Mapping terra-firme rainforest environments in Amazonia. *Remote Sensing of Environment*, 112, 3469-3481. doi:10.1016/j.rse.2008.03.018 [verified: CrossRef/OpenAlex, 07]
- **Schaefer_1990** — Schaefer, Joseph T. (1990). The Critical Success Index as an Indicator of Warning Skill. *Weather and Forecasting*, 5, 570-575. doi:10.1175/1520-0434(1990)005<0570:TCSIAA>2.0.CO;2 [verified: CrossRef/OpenAlex, 07]
- **Sharma_2025** — Sharma, Nirdesh; Saharia, Manabendra (2025). DeepSARFlood: Rapid and automated SAR-based flood inundation mapping using vision transformer-based deep ensembles with uncertainty estimates. *Science of Remote Sensing*. doi:10.1016/j.srs.2025.100203 [corpus record `1-s2.0-S2666017225000094-main`; text read; metadata corpus]
- **Shen_2019** — Shen, Xinyi and Wang, Dacheng and Mao, Kebiao and Anagnostou, Emmanouil and Hong, Yang (2019). Inundation Extent Mapping by Synthetic Aperture Radar: A Review. *Remote Sensing*, 11, 879. doi:10.3390/rs11070879 [verified: CrossRef/OpenAlex, 07]
- **Shumilova_2025** — Shumilova, O. and Sukhodolov, A. and Osadcha, N. and Oreshchenko, A. and Constantinescu, G. and Afanasyev, S. and Koken, M. and Osadchyi, V. and Rhoads, B. and Tockner, K. and Monaghan, M. T. and Schröder, B. and Nabyvanets, J. and Wolter, C. and Lietytska, O. and van de Koppel, J. and Magas, N. and Jähnig, S. C. and Lakisova, V. and Trokhymenko, G. and Venohr, M. and Komorin, V. and Stepanenko, S. and Khilchevskyi, V. and Domisch, S. and Blettler, M. and Gleick, P. and De Meester, L. and Grossart, H.-P. (2025). Environmental effects of the Kakhovka Dam destruction by warfare in Ukraine. *Science*, 387, 1181-1186. doi:10.1126/science.adn8655 [verified: CrossRef/OpenAlex, 07]
- **Singha_2020** — Singha, Mrinal; Dong, Jinwei; Sarmah, Sangeeta; You, Nanshan; Zhou, Yan; Zhang, Geli; Doughty, Russell; Xiao, Xiangming (2020). Identifying floods and flood-affected paddy rice fields in Bangladesh based on Sentinel-1 imagery and Google Earth Engine. *ISPRS Journal of Photogrammetry and Remote Sensing*. doi:10.1016/j.isprsjprs.2020.06.011 [corpus record `10.1016_j.isprsjprs.2020.06.011`; text read; metadata corpus]
- **Small_2011** — Small, David (2011). Flattening Gamma: Radiometric Terrain Correction for SAR Imagery. *IEEE Transactions on Geoscience and Remote Sensing*, 49, 3081-3093. doi:10.1109/TGRS.2011.2120616 [verified: CrossRef/OpenAlex, 07]
- **Stephens_2014** — Stephens, Elisabeth and Schumann, Guy and Bates, Paul (2014). Problems with binary pattern measures for flood model evaluation. *Hydrological Processes*, 28, 4928-4937. doi:10.1002/hyp.9979 [verified: CrossRef/OpenAlex, 07]
- **Torres_2012** — Torres, Ramon and Snoeij, Paul and Geudtner, Dirk and Bibby, David and Davidson, Malcolm and Attema, Evert and Potin, Pierre and Rommen, BjÖrn and Floury, Nicolas and Brown, Mike and Traver, Ignacio Navas and Deghaye, Patrick and Duesmann, Berthyl and Rosich, Betlem and Miranda, Nuno and Bruno, Claudio and L'Abbate, Michelangelo and Croci, Renato and Pietropaolo, Andrea and Huchler, Markus and Rostan, Friedhelm (2012). GMES Sentinel-1 mission. *Remote Sensing of Environment*, 120, 9-24. doi:10.1016/j.rse.2011.05.028 [verified: CrossRef/OpenAlex, 07]
- **Tsiupa_2023** — Tsiupa, I; Shevchenko, Taras; Plichko, L (2023). Study of dynamics of changes in the Kakhovka reservoir based on remote sensing data. **. doi: [corpus record `Mon23-170`; text read; metadata corpus; conference paper (Monitoring 2023, Kyiv); no DOI in the corpus record]
- **Tsyganskaya_2018** — Tsyganskaya, Viktoriya; Martinis, Sandro; Marzahn, Philip; Ludwig, Ralf (2018). SAR-based detection of flooded vegetation – a review of characteristics and approaches. *International Journal of Remote Sensing*. doi:10.1080/01431161.2017.1420938 [corpus record `10.1080_01431161.2017.1420938`; text read; metadata corpus]
- **Tucker_1979** — Tucker, Compton J. (1979). Red and photographic infrared linear combinations for monitoring vegetation. *Remote Sensing of Environment*, 8, 127-150. doi:10.1016/0034-4257(79)90013-0 [verified: CrossRef/OpenAlex, 07]
- **Tupas_2023** — Tupas, Mark Edwin and Roth, Florian and Bauer-Marschallinger, Bernhard and Wagner, Wolfgang (2023). Improving Sentinel-1 Flood Maps Using a Topographic Index as Prior in Bayesian Inference. *Water*, 15, 4034. doi:10.3390/w15234034 [verified: CrossRef/OpenAlex, 07]
- **Tutova_2025** — Tutova, H; Lisovets, O; Kunakh, O; Zhukov, O; Khmelnitsky, Bogdan; Honchar, Oles (2025). Procrustean analysis of the set of spectral indices reveals the transformations in plant community hemeroby and functional structure induced by anthropogenic disasters. *Biosystems Diversity*. doi:10.15421/012528 [corpus record `10.15421_012528`; text read; metadata CrossRef]
- **Vyshnevskyi_2023** — Vyshnevskyi, Viktor and Shevchuk, Serhii and Komorin, Viktor and Oleynik, Yurii and Gleick, Peter (2023). The destruction of the Kakhovka dam and its consequences. *Water International*, 48, 631-647. doi:10.1080/02508060.2023.2247679 [verified: CrossRef/OpenAlex, 07]
- **Vyshnevskyi_2024** — Vyshnevskyi, Viktor (2024). NATURAL PROCESSES IN THE AREA OF THE FORMER KAKHOVSKE RESERVOIR AFTER THE DESTRUCTION OF THE KAKHOVKA HPP. *Journal of Landscape Ecology*. doi:10.2478/jlecol-2024-0014 [corpus record `10.2478_jlecol-2024-0014`; text read; metadata CrossRef]
- **Wagner_2020** — Wagner, W; Freeman, V; Cao, S; Matgen, P; Chini, M; Salamon, P; Mccormick, N; Martinis, S; Bauer-Marschallinger, B; Navacchi, C; Schramm, M; Reimer, C; Briese, C (2020). DATA PROCESSING ARCHITECTURES FOR MONITORING FLOODS USING SENTINEL-1. *ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences*. doi:10.5194/isprs-annals-v-3-2020-641-2020 [corpus record `isprs-annals-V-3-2020-641-2020`; text read; metadata corpus]
- **Xu_2006** — Xu, Hanqiu (2006). Modification of normalised difference water index (NDWI) to enhance open water features in remotely sensed imagery. *International Journal of Remote Sensing*, 27, 3025-3033. doi:10.1080/01431160600589179 [verified: CrossRef/OpenAlex, 07]
- **Yailymov_2025** — Yailymov, Bohdan; Yailymova, Hanna; Kolotii, Andrii; Shelestov, Andrii; Skakun, Sergii; Baber, Sheila; Becker-Reshef, Inbal; Kussul, Nataliia (2025). Flooded and Irrigation Area Monitoring After the Kakhovka Dam Disaster Based on Machine Learning and Satellite Data. *IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing*. doi:10.1109/jstars.2025.3592368 [corpus record `Flooded_and_Irrigation_Area_Monitoring_After_the_Kakhovka_Dam_Disaster_Based_on_Machine_Learning_and_Satellite_Data`; text read; metadata corpus]
- **Yamazaki_2019** — Yamazaki, Dai; Ikeshima, Daiki; Sosa, Jeison; Bates, Paul; Allen, George; Pavelsky, Tamlin (2019). MERIT Hydro: A High‐Resolution Global Hydrography Map Based on Latest Topography Dataset. *Water Resources Research*. doi:10.1029/2019wr024873 [corpus record `10.1029_2019wr024873`; text read; metadata corpus]
- **Yi_2025** — Yi, Shuang and Li, Hao‐si and Han, Shin‐Chan and Sneeuw, Nico and Yuan, Chunyu and Song, Chunqiao and Yeo, In‐Young and McCullough, Christopher M. (2025). Quantification of the Flood Discharge Following the 2023 Kakhovka Dam Breach Using Satellite Remote Sensing. *Water Resources Research*, 61, e2024WR038314. doi:10.1029/2024WR038314 [verified: CrossRef/OpenAlex, 07]
- **Yu_2024** — Yu, Linpeng; Zhang, Haowei; Gong, Wei; Ma, Xin (2024). Validation of Mainland Water Level Elevation Products From SWOT Satellite. *IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing*. doi:10.1109/jstars.2024.3435363 [corpus record `Validation_of_Mainland_Water_Level_Elevation_Products_From_SWOT_Satellite`; text read; metadata corpus]
- **Zhao_2021** — Zhao, Jie and Pelich, Ramona and Hostache, Renaud and Matgen, Patrick and Cao, Senmao and Wagner, Wolfgang and Chini, Marco (2021). Deriving exclusion maps from C-band SAR time-series in support of floodwater mapping. *Remote Sensing of Environment*, 265, 112668. doi:10.1016/j.rse.2021.112668 [verified: CrossRef/OpenAlex, 07]
- **Zheng_2018** — Zheng, Xing and Maidment, David R. and Tarboton, David G. and Liu, Yan Y. and Passalacqua, Paola (2018). GeoFlood: Large‐Scale Flood Inundation Mapping Based on High‐Resolution Terrain Analysis. *Water Resources Research*, 54. doi:10.1029/2018WR023457 [verified: CrossRef/OpenAlex, 07]
- **Zuo_2024** — Zuo, Chen; Zhang, Haowei; Ma, Xin; Gong, Wei (2024). Impact Assessment of Flood Events Based on Multisource Satellite Remote Sensing: The Case of Kahovka Dam. *IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing*. doi:10.1109/jstars.2024.3490756 [corpus record `Impact_Assessment_of_Flood_Events_Based_on_Multisource_Satellite_Remote_Sensing_The_Case_of_Kahovka_Dam`; text read; metadata corpus]
