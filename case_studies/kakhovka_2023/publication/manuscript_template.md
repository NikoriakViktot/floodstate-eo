# Daily inundation after the Kakhovka dam breach reconstructed from the observed water surface and terrain, checked against Sentinel-1 and ICESat-2, and what EO-based flood products recover under weak labels

**Manuscript draft (Paper 3 of the Kakhovka series), generated 2026-09-25 from `manuscript_template.md` by
`workflows/paper/fill_manuscript.py`. Every number below is resolved from a committed publication table cell
(`publication/tables/T*.csv`, manifest with sha256); claim identifiers [C01]–[C14] refer to `evidence_matrix.csv`; terms are frozen in `TERMINOLOGY.md`.
Literature values are context and are flagged VERIFY in `references_to_verify.md`.**

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
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_central_km2||.0f}} km² on 7 June 2023 (primary Monte-Carlo p05–p95
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_p05_km2||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_p95_km2||.0f}} km²), between the Sentinel-1 acquisitions of 6 June (partial)
and 9 June, one day before the peak stage at Kherson ({{T12|region=DNIPRO_CORRIDOR,date=2023-06-08|kherson_gauge_m||.2f}} m on 8 June); with the DEM as
delivered, i.e. with the reed beds counted as new, it is {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_connected_ceiling_dem_uncorrected_km2||.0f}} km². The
reconstructed total water-surface area rises from {{T12|region=DNIPRO_CORRIDOR,date=2023-06-05|W_total_central_km2||.0f}} km² in the pre-breach regime (5 June)
to {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_central_km2||.0f}} km² on 7 June (p05–p95 {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_p05_km2||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_p95_km2||.0f}} km²),
with a further {{T12|region=INHULETS_VALLEY_rect,date=2023-06-07|W_total_central_km2||.0f}} km² in the Inhulets valley; the
reconstructed new-water volume is {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_central_hm3||.0f}} hm³ (p05–p95 {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_p05_hm3||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_p95_hm3||.0f}} hm³).
The newly inundated area falls to {{T12|region=DNIPRO_CORRIDOR,date=2023-06-13|A_central_km2||.0f}} km² on 13 June and {{T12|region=DNIPRO_CORRIDOR,date=2023-06-21|A_central_km2||.0f}} km² on 21 June.
On 9 June, inside the terrain-eligible floodplain, the raw agreement with Sentinel-1 new dark water is low
(POD {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|POD||.2f}}, FAR {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|FAR||.2f}}) and strongly conditioned by surface type:
{{T14|date=2023-06-09,category=C|km2_normally_wet|sum|.0f}} km² of Sentinel-1 "new water" lies on normally-wet reed beds below
the pre-breach surface (a submergence signal, not inundation onset); {{T14|date=2023-06-09,category=C|km2_ground_ge5m_above|sum|.0f}} km²
lies ≥ 5 m above the reconstructed surface and is topographically unsupported by the connected water surface, and along the
night ICESat-2 tracks that sample it the DEM agrees with the altimetry to within a few decimetres, so the available ICESat-2
observations give no evidence for a DEM bias large enough to explain it; {{T14|date=2023-06-09,category=B|km2|sum|.0f}} km² allowed
by the terrain is invisible to the dark-water rule, {{T14|date=2023-06-09,category=B|km2_wc_trees|sum|.0f}} km² of it under trees and
{{T14|date=2023-06-09,category=B|km2_wc_built|sum|.0f}} km² in built-up areas. Changing the weak-label contract from v002 to
v003_A at fixed inputs changed the U-Net flood on reference water on the test blocks by
{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|median||.1f}} km²
(95 % block bootstrap {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|lo||.1f}} to
{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|hi||.1f}}) with no statistically resolved change in
event-flood recall.

**Conclusions.** Discrete EO acquisitions undersample the event: the reconstructed areal maximum falls between them. The
observed_S1 flood of a SAR mask, the mapped_UNet persistent flood and the terrain-reconstructed newly inundated and total
water-surface areas are different quantities. The reconstruction gives the day-by-day extent, depth and volume that the
observations cannot, with a stated primary interval, and the observations show where the reconstruction and the sensors are blind. We report every area
with its semantics and every model number as agreement with weak reference labels, not as flood-mapping accuracy.

**Keywords:** dam breach; inundation dynamics; SWOT; ICESat-2; Sentinel-1; HAND; weak supervision; U-Net; Kakhovka

## 1. Introduction

The destruction of the Kakhovka dam on 6 June 2023 released the largest reservoir of the Dnipro cascade into a 90 km reach
with a densely populated left bank, a reed-wetland delta and the Dnipro–Buh liman (Vyshnevskyi et al. 2023; Shumilova et al.
2025). Operational products reported the flooded area within days (UNOSAT via CEOBS 2023; REACH 2023), hydrodynamic
reconstructions of the breach followed (Kadam et al. 2024), and the SWOT mission, on its one-day calibration orbit, observed
the reach daily through the event (Lehnigk et al. 2026; Paper 1 of this series). Lehnigk et al. (2026) show with those daily
SWOT water-surface elevations that two-dimensional outburst-flood simulations miss the observed stage and timing unless the
bathymetry is right, and even then underestimate the peak stage (VERIFY); Yi et al. (2025) reconstruct the reservoir drainage
(an initial breach flow of order 5.7 × 10⁴ m³ s⁻¹, VERIFY); Kadam et al. (2024) give a HEC-RAS scenario extent. What is still
missing is a description of the inundation that does not depend on which sensor happened to look on which day: an extent, a
depth and a volume for every day, tied to the observed water surface, with an uncertainty, and an account of where the
satellite flood masks and such a reconstruction disagree and why. Terrain-based approaches that project a water surface or a
mapped extent on a DEM (HAND: Rennó et al. 2008, Nobre et al. 2011; GeoFlood: Zheng et al. 2018; FwDET: Cohen et al. 2019) are
first-order products, not hydrodynamics, and their depth and extent are sensitive to small vertical errors on low-relief
floodplains, which spatially correlated DEM-error realisations propagate correctly (Darnell et al. 2008; Le et al. 2025).

Two well-known properties of satellite flood mapping make this necessary. The area obtained by counting classified pixels is a
*mapped* area, not an unbiased estimate of the true flooded area; the good-practice framework of Olofsson et al. (2014) asks
for a probability-sample reference that does not exist here. And a C-band dark-water rule does not see water under trees,
between buildings or under emergent reeds (Grimaldi et al. 2020; Zhao et al. 2021 formalise such areas as exclusion maps),
while smooth non-water surfaces and radar shadow can look like water (Shen et al. 2019). A U-Net trained on labels derived
from those masks inherits both limits (He et al. 2024; Maiti et al. 2022); its accuracy against such labels is agreement, not
truth, and an input that also builds the label is label leakage (DataLeakage 2025, VERIFY). We therefore structure the study
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
and validated it against night ICESat-2; Paper 4 will reconstruct the reservoir bowl on the historical (pre-impoundment and
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

- **Sentinel-1** GRD/RTC, eleven acquisitions 1–30 June 2023 (orbits 14, 65, 87, 138), per-scene dark-water masks (M3 rule of
  Paper 1's water classifier, 20 m); orbit-138 dates cover 62 % of the observable domain. Orbit-matched dB change channels (p71)
  are the U-Net inputs. A second set of thirteen reference scenes (15 April–28 May 2023) defines recurrent May water.
- **Sentinel-2** L2A index stacks per date (NDWI, MNDWI, NDVI, NDMI, BSI, AWEIsh, NDTI, 10 m) and PRE/EVENT/TRACE composites.
- **SWOT** L2_HR_RiverSP v2.0 nodes on the one-day calibration orbit, 26 May–10 July 2023, {{T01|dataset=SWOT L2_HR_RiverSP v2.0 nodes (1-day orbit), accepted;|detail||}};
  node_q ≤ 1 and dark fraction < 0.5 as in Paper 1.
- **Kherson gauge 80805**, daily, river yearbook, BS-77 → EVRF2019 by the official EPSG:9902 operation (+0.216 m at the post);
  6–12 June are flagged in the sea yearbook (recorder failure) and the river-yearbook values are used, as in Paper 1 §5.12.
- **Seamless DEM** (Paper 2): kriged bathymetric bed inside the pre-breach water polygons, FABDEM v1.2 elsewhere, EVRF2019, 20 m;
  HAND from the p42 workflow (FABDEM floored at the 1 m river level, WhiteboxTools). Night ICESat-2 ATL08 ground segments
  (2019–2025, Paper 2 chain) give its accuracy by land-cover class (T18): RMSE
  {{T18|set=C seamless DEM (p55) -- ALL night points (land below dam + exposed bed)|RMSE||.2f}} m, NMAD
  {{T18|set=C seamless DEM (p55) -- ALL night points (land below dam + exposed bed)|NMAD||.2f}} m over
  {{T18|set=C seamless DEM (p55) -- ALL night points (land below dam + exposed bed)|N||.0f}} segments, with trees the worst class.
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
{{T17|period=all days|median_m||+.2f}} m (NMAD {{T17|period=all days|NMAD_m||.2f}} m, RMSE {{T17|period=all days|RMSE_m||.2f}} m,
n = {{T17|period=all days|n_days||.0f}} days; T17, Fig06) — an input-consistency check; the frame validation is Paper 1.

### 3.2 Terrain rule, baseline and the definition of "new inundation"

A cell is water on day t if its DEM lies below the water surface and it is 8-connected, through such cells, to the pre-breach
optical water network (p60 pre-water frequency ≥ 20 %), within 10 km of pre-breach water and downstream of the dam
(*connected ceiling*). Two other rules bound it: the p42 rule (additionally HAND < WSE − 1 m, channel-connected through the
mapped drainage; a lower bound because the delta drainage is incompletely mapped) and the ceiling without connectivity. The
DEM enters after subtraction of its class-median residual against night ICESat-2 (T18; trees +1.5–2 m, wetland ≈ +0.5 m,
cropland ≈ 0). The *normal regime* is the union of the same rule over the pre-breach days 26 May–5 June plus the observed
pre-breach water (Sentinel-1 1–2 June, p60); **new inundation** is water on day t outside that regime. Cells of the model-only
normal regime ("normally wet": low reed beds below the normal surface that no optical or SAR mask lists as water) are kept as
their own category, because a Sentinel-1 dark-water onset there is a depth signal — the reeds are submerged — not the onset of
inundation. With the DEM as delivered those reed beds sit above the normal surface and count as new inundation; we report
that run as a sensitivity (T12) and the two quantities — new inundation and wetland submergence — separately.

### 3.3 Uncertainty budget

A Monte-Carlo of 40 draws propagates (T11b): the closure residual (σ 0.05 m, one offset per draw), the date-only gauge
(σ 0.05 m, cap cells), the SWOT node height (median wse_u {{T11b|component=swot_node_wse_u|sigma_m||.3f}} m, per node-day),
the per-node time interpolation (NMAD of leave-one-out residuals on observed node-days,
{{T11b|component=H(s,t)_interpolation;|sigma_m||.3f}} m, interpolated node-days only) and a spatially correlated (500 m) DEM
error field with the class NMAD of T18 (wetland {{T11b|component=dem_wetland|sigma_m||.2f}} m, trees
{{T11b|component=dem_trees|sigma_m||.2f}} m, cropland {{T11b|component=dem_cropland|sigma_m||.2f}} m). The normal regime is
rebuilt per draw. These 40 spatial draws are the **primary uncertainty interval** of every reconstructed area and volume:
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
(raw agreement, primary, T13); the *conditional POD outside the normally-wet class* — POD on the observable dry-background
domain, with the class fixed before any comparison was read — is a diagnostic conditional agreement, not a corrected POD. The disagreement is decomposed into A (both), B (terrain only) and C (S1 only), by WorldCover and RF20
class and by ground elevation relative to the reconstructed surface (< 0, 0–2, 2–5, ≥ 5 m; T14). Night ICESat-2 ATL08 ground
segments (Paper 2 chain) sampled on the 9 June categories give, per category, the residual DEM − ICESat-2 and the share of
segments whose ground lies below the reconstructed surface (T15): an altimetric consistency check of the DEM and the surface
along tracks, not a validation of the inundation map.

### 3.5 Surface context: RF20

A random forest on PRE-event Sentinel-2 composite predictors, trained on ESA WorldCover 2021 with a purity filter, classifies
the surface at 20 m into water, cropland, grass/low vegetation, forest, wetland/reed, built-up, bare sand and uncertain
(p73, frozen before any arm was trained). Its per-class precision, recall and F1 in spatial-block 5-fold cross-validation and in
the frame transfers B1↔B2 are agreement with the training reference (T09, T10), not validation. It supplies the evaluation
strata of the arms and the classes of the ontology.

### 3.6 Weak labels and U-Net arms

Label contract v002 marks FLOOD where Sentinel-1 saw water on at least two of the three peak dates (9, 13, 14 June) on land
that was dry on every pre-breach date, NON_FLOOD where every post-breach date was dry, IGNORE elsewhere. Contract v003_A
(frozen 25 September 2026) keeps the same positives and adds REFERENCE_WATER — recurrent water on at least three admitted May
dates — as a negative class, with UNKNOWN for insufficient or extrapolated evidence; the immediate pre-event state W_pre
(1–2 June) enters its ontology. U-Net (ResNet-34 encoder from scratch, 512-px patches, masked BCE + Dice, 60 epochs, seed
20260923) arms differ only in inputs: U0d (S1 change channels + support), U0z (+ robust z channels), U1 (+ RF20 one-hot),
U2 (+ HAND) on v002; U0d, U2 and U2b (+ W_pre) on v003_A. Thresholds are frozen on validation before the test blocks are read.
U2b is a diagnostic upper bound: W_pre is both an input and a label ingredient, so its comparison is not independent.

### 3.7 Spatial blocking and statistics

The split m6_split_v1 assigns 10 km blocks of the global lattice to train, validation and test with 640 m eroded buffers and
pure 512-px footprints (T03; {{T03|item=blocks train/val/test|value||}} blocks). The block size exceeds the patch plus two
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
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-06|A_central_km2||.0f}} km² on 6 June and reaches its maximum of
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_central_km2||.0f}} km² on 7 June (primary p05–p95
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_p05_km2||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_p95_km2||.0f}} km²),
a day between the Sentinel-1 acquisitions that no scene covers [C01]; the Kherson stage reaches its maximum one day later
({{T12|region=DNIPRO_CORRIDOR,date=2023-06-08|kherson_gauge_m||.2f}} m on 8 June, consistent with the peak stages by 8 June that
Lehnigk et al. 2026 report from SWOT, VERIFY) — the areal maximum and the peak stage are different quantities, and the day of the
areal maximum is a property of the reconstructed series, not an observation. It is {{T12|region=DNIPRO_CORRIDOR,date=2023-06-09|A_central_km2||.0f}} km² on 9 June,
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-13|A_central_km2||.0f}} km² on 13 June,
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-18|A_central_km2||.0f}} km² on 18 June and
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-21|A_central_km2||.0f}} km² on 21 June, when the Kherson stage is back at
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-21|kherson_gauge_m||.2f}} m (Fig04, T12) [C03]. The reconstructed new-water volume
reaches {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_central_hm3||.0f}} hm³ (p05–p95
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_p05_hm3||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_p95_hm3||.0f}} hm³,
Monte-Carlo median {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_p50_hm3||.0f}} hm³) [C02].
The p42 HAND rule gives {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_hand_and_ceiling_km2||.0f}} km² at the peak; the
ceiling without connectivity {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_ceiling_only_km2||.0f}} km². The largest single
term is definitional: with the DEM as delivered, the reed beds count as new inundation and the peak is
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_connected_ceiling_dem_uncorrected_km2||.0f}} km². Inside the p42 floodplain
domain the peak is {{T12|region=P42_FLOODPLAIN_DOMAIN,date=2023-06-07|A_central_km2||.0f}} km²; the Inhulets valley, treated as
backwater with its own SWOT nodes, peaks at {{T12|region=INHULETS_VALLEY_rect,date=2023-06-09|A_central_km2||.0f}} km² on 9 June.
The depth and duration maps (Fig07) show the 7–8 June water more than 4 m deep on the right-bank floodplain below the dam and
the delta channels, and inundation lasting more than a week only in the floodplain lows and the delta.

**Reconstructed total water-surface area [C02].** The newly inundated area is the water that was not there before; the total
water-surface area is all water on the day, including the pre-breach channels, lakes and reed beds. In the corridor it is {{T12|region=DNIPRO_CORRIDOR,date=2023-06-05|W_total_central_km2||.0f}} km²
in the normal regime (5 June), {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_central_km2||.0f}} km² on 7 June (primary p05–p95
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_p05_km2||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_p95_km2||.0f}} km²),
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-09|W_total_central_km2||.0f}} km² on 9 June and
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-13|W_total_central_km2||.0f}} km² on 13 June (with the DEM as delivered:
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-05|W_total_connected_ceiling_dem_uncorrected_km2||.0f}} →
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_connected_ceiling_dem_uncorrected_km2||.0f}} km²); the Inhulets valley adds
{{T12|region=INHULETS_VALLEY_rect,date=2023-06-07|W_total_central_km2||.0f}} km² on 7 June. Sentinel-1 saw
{{T19|date=2023-06-09,region=DNIPRO_CORRIDOR,sensor=S1|water_km2||.0f}} km² of dark water in the corridor on 9 June and
{{T19|date=2023-06-09,region=INHULETS_VALLEY_rect,sensor=S1|water_km2||.0f}} km² in the Inhulets valley. Neither total is comparable
with the operational figures: the UNOSAT ~620 km² of 9 June is cumulative satellite-detected flooded *land* over 6–9 June with the
pre-existing water as a separate class (T16, literature_reported, VERIFY), a quantity closer in kind to the newly inundated area
than to the total water-surface area, and it differs further in AOI (the liman reach, frame B3, is not part of this domain),
in temporal semantics (cumulative vs daily snapshot) and in reference water (§4.6).

**Uncertainty per day [C07].** On 7 June the primary spatial draws give relative half-widths of
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|rel_halfwidth_A_pct||.0f}} % for the area and
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|rel_halfwidth_V_pct||.0f}} % for the volume, and Monte-Carlo medians displaced above
the deterministic run by {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|mc_shift_A_pct||+.0f}} % (area) and
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|mc_shift_V_pct||+.0f}} % (volume): the vertical error enters the volume mainly as a
shift, not as a wider band, so the deterministic volume is not centred in its interval and volumes are always quoted with p05–p95
and the median. The emulator sensitivity envelope (§3.3) is wider — newly inundated area
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_emu_km2_p05||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_emu_km2_p95||.0f}} km²
(p25–p75 {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_emu_km2_p25||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_emu_km2_p75||.0f}} km²),
total water-surface area {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_emu_km2_p05||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_emu_km2_p95||.0f}} km²
(Fig04, candles) — and represents a different distribution (parameter-space propagation); the two are never mixed. The daily
change of the newly inundated area (bars in Fig04) shows the filling on 6–7 June and the draining at 30–40 km² per day between
10 and 18 June.

**Reservoir side of the balance [C14] (context).** Under the sloped daily surface (outlet SWOT nodes, Nikopol press values, Rozumivka gauge)
the pool held {{T21|date=2023-06-05|V_pool_km3||.1f}} km³ on 5 June (design table at the same outlet level:
{{T22|level_evrf2019_m=17.5|V_table19_km3||.1f}} km³) and {{T21|date=2023-06-13|V_pool_km3||.1f}} km³ on 13 June, i.e.
{{T21|date=2023-06-13|cum_released_km3||.1f}} km³ released in eight days, with the largest daily volume change of
{{T21|date=2023-06-07|dV_pool_hm3||.0f}} hm³ on 7 June. The corresponding daily-mean effective release, −dV/dt + Q_in, is
{{T21|date=2023-06-07|Q_release_eff_daily_mean_m3s||.0f}} m³ s⁻¹ against a DniproHES inflow of
{{T21|date=2023-06-07|Q_in_dniprohes_m3s||.0f}} m³ s⁻¹: a storage-balance estimate on a surface interpolated between three or
four level points, a daily mean and not an instantaneous breach discharge; the initial breach flow of Yi et al. (2025,
5.7 ± 0.8 × 10⁴ m³ s⁻¹) and the HEC-RAS scenario of Kadam et al. (2024, 3.6 × 10⁴ m³ s⁻¹) are different physical quantities of the
same order (VERIFY; context, not validation). The surface gradient across the pool reached
{{T21|date=2023-06-10|gradient_m||.1f}} m on 10 June. Downstream, the reconstructed new water stored above ground peaks at
{{T21|date=2023-06-09|downstream_new_volume_hm3||.0f}} hm³ on 9 June, a few per cent of the release, implying that most of the
released volume was transmitted downstream rather than stored on the mapped floodplain (Fig09, T21). The seamless-DEM hypsometry
lies below the design table at equal levels — {{T22|level_evrf2019_m=17.5|dV_rel_pct||.0f}} % at 17.5 m,
{{T22|level_evrf2019_m=13.0|dV_rel_pct||.0f}} % at 13 m, {{T22|level_evrf2019_m=11.0|dV_rel_pct||.0f}} % at 11 m; the design table
is undefined below 10 m (T22, FigS07) — so the released volume inherits this gap; its origin (datum, present morphology, the
underwater part of the seamless DEM, shoreline geometry, the original survey) is the subject of Paper 4, which reconstructs the
bowl on the historical bathymetry.

### 4.2 Raw agreement with Sentinel-1 on the observation domain [C04]

On 9 June, in the p42 floodplain domain and on the Sentinel-1 footprint, the reconstruction allows
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|hand_new_km2||.0f}} km² of new water and Sentinel-1
reports {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|s1_new_km2||.0f}} km²; they share
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|hit_km2||.0f}} km² (POD
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|POD||.2f}}, FAR
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|FAR||.2f}}, CSI
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|CSI||.2f}}). Of the
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|miss_km2||.0f}} km² that Sentinel-1 reports and
the reconstruction does not, {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|miss_on_normally_wet_km2||.0f}} km²
lie on normally-wet cells. The raw agreement is therefore low, and most apparent terrain misses occur in predefined normally-wet
or vegetation-dominated cells where SAR dark-water onset is not an appropriate binary reference; the conditional POD outside the
normally-wet class is {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|POD_cond_outside_normally_wet||.2f}},
a diagnostic conditional agreement, not a corrected POD. On 13 June the raw POD is
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-13|POD||.2f}} and the conditional POD
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-13|POD_cond_outside_normally_wet||.2f}}. After 18 June the
Sentinel-1 "new water" outside the floodplain domain ({{T19|date=2023-06-21,region=DNIPRO_CORRIDOR,sensor=S1|new_water_km2||.0f}} km²
on 21 June in the corridor) is scattered on fields and sand while the gauge is at its pre-breach level and the reconstruction is
at {{T12|region=DNIPRO_CORRIDOR,date=2023-06-21|A_central_km2||.0f}} km²: the dark-water rule, not the flood. The large-scale
recession seen by Sentinel-1 inside the floodplain (T19) follows the reconstruction and the gauge (Fig04).

### 4.3 The disagreement is mechanistic [C05]

On 9 June the two zones together give A = {{T14|date=2023-06-09,category=A|km2|sum|.0f}} km², B (terrain only) =
{{T14|date=2023-06-09,category=B|km2|sum|.0f}} km² and C (Sentinel-1 only) = {{T14|date=2023-06-09,category=C|km2|sum|.0f}} km²
(T14, Fig05). B lies entirely below the reconstructed surface and is dominated by surfaces the dark-water rule cannot see:
{{T14|date=2023-06-09,category=B|km2_wc_trees|sum|.0f}} km² trees, {{T14|date=2023-06-09,category=B|km2_wc_wetland|sum|.0f}} km²
wetland and {{T14|date=2023-06-09,category=B|km2_wc_built|sum|.0f}} km² built-up. C splits by ground elevation:
{{T14|date=2023-06-09,category=C|km2_ground_below_surface|sum|.0f}} km² below the surface and
{{T14|date=2023-06-09,category=C|km2_ground_0_2m_above|sum|.0f}} km² within 2 m above it, of which
{{T14|date=2023-06-09,category=C|km2_normally_wet|sum|.0f}} km² are normally-wet reed beds — the submergence of emergent
vegetation, a depth signal; and {{T14|date=2023-06-09,category=C|km2_ground_ge5m_above|sum|.0f}} km² at least 5 m above the
surface, on cropland and grass: S1-only detections that are topographically inconsistent with the reconstructed connected water
surface. Whether they are smooth non-water surfaces, radar shadow, local ponding after rain, water outside the assumed
connectivity, timing or registration effects is not tested here; what §4.4 tests is whether a DEM error could explain them.

### 4.4 ICESat-2 altimetric consistency [C06]

Where Sentinel-1 reports water at least 2 m above the reconstructed surface, the seamless DEM agrees with night ICESat-2 ground
heights to {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_median||+.2f}} m (p10–p90
{{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_p10||+.2f}} to
{{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_p90||+.2f}} m, n =
{{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|N||.0f}} segments) in the delta and
{{T15|zone=ZONE_4_DAM_TO_KHERSON_FLOODWAY,category=S1_only_ground_ge2m_above|res_median||+.2f}} m (n =
{{T15|zone=ZONE_4_DAM_TO_KHERSON_FLOODWAY,category=S1_only_ground_ge2m_above|N||.0f}}) in the floodway; the ICESat-2 ground lies
{{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|ice_minus_wse_median||+.1f}} m above the surface in the delta and
essentially no segment ({{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|share_ice_below_wse||.1%}}) lies below it.
The available ICESat-2 observations therefore provide no evidence for a DEM bias large enough to explain those S1-only
detections; they support the reading of §4.3 without proving it, because the tracks (listed with their dates in T15) sample
the category along lines, not every cell of the {{T14|date=2023-06-09,category=C|km2_ground_ge5m_above|sum|.0f}} km². Where the
reconstruction and Sentinel-1 agree, {{T15|zone=ZONE_2_KHERSON_DELTA,category=both|share_ice_below_wse||.1%}} of the segments lie
below the surface (T15, Fig08). This is a track-based consistency check of the DEM and the surface, not a validation of the map.

### 4.5 Water-surface input and DEM accuracy [C06]

After re-anchoring to the Kherson-local closure the SWOT input agrees with the gauge at day level (median
{{T17|period=all days|median_m||+.2f}} m, NMAD {{T17|period=all days|NMAD_m||.2f}} m; during the rise and peak
{{T17|period=rise and peak 06-06..06-14|median_m||+.2f}} m over {{T17|period=rise and peak 06-06..06-14|n_days||.0f}} days),
consistent with Paper 1's +1.9 cm through the breach fortnight. The DEM error model of the Monte-Carlo is the class table of
Paper 2 (T18).

### 4.6 Three areas, three definitions [C08]

For the same corridor the 9 June Sentinel-1 scene contains {{T16|quantity=S1 new dark water, 06-09 scene;region=DNIPRO_CORRIDOR|km2||.0f}} km²
of new dark water (observed_S1), the label recipe (water on ≥ 2 of 3 peak dates) {{T16|quantity=S1 new dark water, >= 2 of 3 peak dates (label recipe);region=DNIPRO_CORRIDOR|km2||.0f}} km²,
the U-Net arm U2b {{T16|quantity=U2b predicted event flood (persistent concept);region=DNIPRO_CORRIDOR|km2||.0f}} km² (mapped_UNet), and the
reconstruction {{T12|region=DNIPRO_CORRIDOR,date=2023-06-09|A_central_km2||.0f}} km² on 9 June and
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_central_km2||.0f}} km² at the peak (terrain_reconstructed). The label contract
is a persistence product and therefore describes the regime around 13 June. The operational figures — UNOSAT product 3616,
~620 km² of satellite-detected flooded land cumulative over 6–9 June with the pre-existing water as a separate class,
preliminary and not field-validated; product 3623, ~180 km² on 13 June against the reference water of 3/5 June (T16,
literature_reported, VERIFY) — are flooded *land*, closer in kind to the newly inundated area than to the total water-surface
area, and differ in AOI, temporal semantics (cumulative vs snapshot) and reference water; they are context, not validation. T16
carries the area, quantity and temporal semantics of every row.

### 4.7 Inhulets backwater [C03]

The Inhulets valley has its own SWOT nodes and responds as backwater: on 9 June the reconstruction allows
{{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|hand_new_km2||.0f}} km² against
{{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|s1_new_km2||.0f}} km² seen by Sentinel-1
(POD {{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|POD||.2f}}, CSI
{{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|CSI||.2f}}); the p42 HAND rule, which measures
HAND to the Dnipro, is not applicable there. The valley is never added to the Dnipro reach.

### 4.8 Surface context [C12]

RF20 reaches an overall agreement of {{T09|evaluation=spatial_block_cv_5fold,cls=MACRO_MEAN|OA_spatial_cv||.3f}} with WorldCover
in spatial-block cross-validation (macro F1 {{T09|evaluation=spatial_block_cv_5fold,cls=MACRO_MEAN|F1||.3f}}), wetland/reed F1
{{T09|evaluation=spatial_block_cv_5fold,cls=WETLAND_REED|F1||.3f}} and built-up F1 {{T09|evaluation=spatial_block_cv_5fold,cls=BUILT_UP|F1||.3f}};
the frame transfers B1→B2 and B2→B1 reach macro F1 {{T09|evaluation=transfer_B1_to_B2,cls=MACRO_MEAN|F1||.3f}} and
{{T09|evaluation=transfer_B2_to_B1,cls=MACRO_MEAN|F1||.3f}} (T09), which speaks to stability across spatial frames more than the
overall agreement does. These are agreement numbers against the training reference, not an independent land-cover accuracy.

### 4.9 What EO inputs recover under weak labels [C09–C11]

*Label effect.* At fixed inputs, U2 predicts {{T07|run=U2_B1B2_v1,endpoint=R_pred_on_reference_water_km2|value||.1f}} km² of flood on
the test-block REFERENCE_WATER under v002 and {{T07|run=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|value||.1f}} km² under
v003_A (paired difference {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|median||.1f}} km²,
95 % {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|lo||.1f}} to
{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|hi||.1f}}), while EVENT_FLOOD recall changes by
{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|median||+.3f}}
({{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|lo||+.3f}} to
{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|hi||+.3f}}), an interval that crosses zero: no statistically
resolved change in recall under this bootstrap design, which is not the same as "unchanged". Global F1 is not comparable across
label sets.
*Terrain as input.* On v002, adding HAND to U0d changes the predicted-flood burden on unlabelled cropland by
{{T06|comparison=U2 - U0d,labels=v002,endpoint=A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2|median||.1f}} km²
({{T06|comparison=U2 - U0d,labels=v002,endpoint=A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2|ci_lo||.1f}} to
{{T06|comparison=U2 - U0d,labels=v002,endpoint=A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2|ci_hi||.1f}}) and the
built-up false positives by {{T06|comparison=U2 - U0d,labels=v002,endpoint=BU_FP_area_km2|median||+.2f}} km²; land cover as an
input (U1) retains {{T08b|group=A|retention_U1||.0%}}–{{T08b|group=D|retention_U1||.0%}} of the U0d candidate area — context,
not a veto. None of the audited cropland-associated candidates showed positive evidence consistent with breach-induced
inundation under the available SAR, optical and terrain constraints (T08). *Pre-event water as input.* U2b reduces the flood on
reference water by a further {{T07b|A=U2_B1B2_v003A,B=U2b_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|median||.2f}} km²
({{T07b|A=U2_B1B2_v003A,B=U2b_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|lo||.2f}} to
{{T07b|A=U2_B1B2_v003A,B=U2b_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|hi||.2f}}); this comparison is not
independent, because pre-event water information also contributes to the label ontology (label leakage), and U2b is reported as
a diagnostic upper bound, not as a best model.

### 4.10 Block-size sensitivity [C13]

U2 on v003_A gives global F1 {{T20|split=m6_split_v1|G_F1||.3f}} on the frozen 10 km split,
{{T20|split=m6_split_s7p5|G_F1||.3f}} at 7.5 km, {{T20|split=m6_split_s15|G_F1||.3f}} at 15 km and
{{T20|split=m6_split_s20|G_F1||.3f}} at 20 km (each with its own test geography and interval, T20, FigS05); a 5 km split
leaves no validation patch inside the buffers. The tested range is meaningful because every block is larger than the local
object scale (fields, reed beds), comparable to or larger than the spatial correlation length of the change channels, and larger
than the 5.12 km patch plus buffers (the receptive footprint); across it the signs of the paired comparisons are unchanged
(Roberts et al. 2017; Valavi et al. 2019). The conclusions of §4.9 are drawn from the 10 km split only.

## 5. Discussion

Discrete EO acquisitions undersample the event hydrograph: the reconstructed areal maximum (7 June) lies between the
Sentinel-1 acquisitions of 6 and 9 June, and it is not the day of the peak stage at Kherson (8 June; Lehnigk et al. 2026 report
downstream peak stages by 8 June from SWOT, VERIFY). Maximum extent and maximum stage are different quantities whose timing
changes along a 100 km reach, and the day of the areal maximum is the most model-dependent number of this paper: it is where the
water-surface-constrained reconstruction adds what no acquisition can give, and where Paper 5's hydraulic model will be tested.

The three areas of §4.6 are not three estimates of one quantity. The dark-water rule counts water it can see on the day it
looks; the label contract counts water that persisted over three peak dates and therefore describes the recession, not the
areal maximum; the reconstruction counts ground the observed water surface can reach. Their disagreement on 9 June is not
noise: it falls into surfaces the radar cannot see (forest, buildings, emergent reeds), reed beds that were already at the water
level in the normal regime and became dark only when submerged, and dark fields far above any water surface of the event, which
are topographically unsupported by the reconstruction and for which the independent altimetry gives no evidence of a DEM error
large enough to explain them. The most useful product of the comparison is therefore not a single accuracy but the map of where
each source is blind.

The reconstruction's largest uncertainty is definitional rather than metric: whether the reed beds of the delta, which the
class-bias-corrected DEM places at or below the normal water surface, are "new inundation" or "wetland submergence" changes
the peak by about a third (T12). We report both, with the submergence quantified from the Sentinel-1 onset on normally-wet
cells (T13, T14). The metric uncertainty (the primary Monte-Carlo interval) is narrow by comparison, and enters the volume
mainly as a displacement; the planar surface and the absence of timing are outside it and make the recession a lower bound,
which Paper 5 will address with a two-dimensional model calibrated on these daily surfaces. The reservoir balance of §4.1 is
context: a daily-mean effective release from a sloped surface between three or four level points on a DEM whose hypsometry sits
below the design table; Paper 4 will rebuild the bowl on the historical bathymetry before that balance can be more than an
order-of-magnitude check against the published breach-flow estimates.

The U-Net experiments say what an EO product can and cannot learn from such labels: changing the negative class (reference
water) removes a measurable reference-water artefact with no statistically resolved change in recall; terrain as an input
suppresses part of the cropland burden; land
cover as an input does not act as a veto; and pre-event water as an input helps but cannot be evaluated independently while it
also defines the label. Every one of these statements is agreement with weak labels on a frozen spatial split.

## 6. Limitations

A daily reconstructed series, not daily observations: between observation days the values are interpolation and model. Planar
water surface per node neighbourhood, no momentum and no timing of filling and draining; DEM under canopy and reeds
(FABDEM residuals of 1.5–2 m under trees); SWOT nodes on channels only, with the gauge cap beyond 15 km; no satellite scene on
the peak day; the date-only gauge against 11:00 UTC SWOT passes; weak labels whose positives are a persistence product;
W_pre circularity of U2b; frame B3 (delta with the liman) not built; no probability-sample reference for any area; literature
figures not verified against their sources; the Inhulets backwater treated with its own nodes but without a tributary
hydrograph; the reservoir balance rests on three to four level points and a DEM hypsometry below the design table; the
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
