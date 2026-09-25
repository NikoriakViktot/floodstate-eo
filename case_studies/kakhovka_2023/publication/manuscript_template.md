# Daily inundation after the Kakhovka dam breach reconstructed from the observed water surface and terrain, checked against Sentinel-1 and ICESat-2, and what EO-based flood products recover under weak labels

**Manuscript draft (Paper 3 of the Kakhovka series), generated 2026-09-25 from `manuscript_template.md` by
`workflows/paper/fill_manuscript.py`. Every number below is resolved from a committed publication table cell
(`publication/tables/T*.csv`, manifest with sha256); claim identifiers [C01]–[C12] refer to `evidence_matrix.csv`.
Literature values are context and are flagged VERIFY in `references_to_verify.md`.**

## Abstract

**Background.** On 6 June 2023 the Kakhovka dam on the lower Dnipro was breached and the reservoir drained within days. The
flood below the dam has been described mainly from satellite water masks, whose areas depend on the sensor, the date and the
definition of "flooded". Paper 1 of this series established one vertical frame for the gauges, ICESat-2 and SWOT; Paper 2 a
seamless terrain model. Here we ask what that water-surface geometry, projected on the terrain, says about the inundation on
every day of the event, including the peak that no satellite image covers, and how far Sentinel-1 flood observations and
U-Net flood products recover it.

**Methods.** The daily water surface is built from SWOT L2_HR_RiverSP node heights (EGG2015-referenced, shifted by the
Kherson-local closure residual of Paper 1) and the Kherson gauge, without an along-channel chainage; it is projected on the
seamless DEM, corrected for its class-median bias against ICESat-2, with a connectivity rule and a same-rule pre-breach
baseline, so that "new inundation" is water on ground that was not water in the normal regime. A Monte-Carlo budget
propagates closure, gauge, SWOT, interpolation and class-wise DEM errors. Sentinel-1 dark-water masks on 11 dates, the
disagreement between them and the reconstruction decomposed by surface class and elevation, and night ICESat-2 ground
heights are used as checks. RF20 surface classes supply the context; U-Net arms trained on two frozen weak-label contracts on a
frozen spatial-block split show what EO inputs recover.

**Results.** In the Dnipro corridor (Inhulets excluded) the reconstructed new inundation peaks at
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_central_km2||.0f}} km² on 7 June
(Monte-Carlo p05–p95 {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_p05_km2||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_p95_km2||.0f}} km²;
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_connected_ceiling_dem_uncorrected_km2||.0f}} km² with the DEM as delivered, i.e.
with the reed beds counted as new), falls to {{T12|region=DNIPRO_CORRIDOR,date=2023-06-13|A_central_km2||.0f}} km² on 13 June and to
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-21|A_central_km2||.0f}} km² on 21 June; the peak water volume above ground is
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_central_hm3||.0f}} hm³. On 9 June, inside the terrain-eligible floodplain,
the reconstruction and Sentinel-1 agree on {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|hit_km2||.0f}} km²
(POD {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|POD||.2f}}, FAR
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|FAR||.2f}}); the disagreement is not random:
{{T14|date=2023-06-09,category=C|km2_normally_wet|sum|.0f}} km² of Sentinel-1 "new water" lies on normally-wet reed beds
below the pre-breach surface (a submergence signal), {{T14|date=2023-06-09,category=C|km2_ground_ge5m_above|sum|.0f}} km² lies
≥ 5 m above the reconstructed surface on cropland and grass where night ICESat-2 confirms the DEM to within a few decimetres
(false SAR water), and {{T14|date=2023-06-09,category=B|km2|sum|.0f}} km² allowed by the terrain is invisible to the dark-water
rule, {{T14|date=2023-06-09,category=B|km2_wc_trees|sum|.0f}} km² of it under trees and
{{T14|date=2023-06-09,category=B|km2_wc_built|sum|.0f}} km² in built-up areas. Changing the weak-label contract from v002 to
v003_A at fixed inputs changed the U-Net flood on reference water on the test blocks by
{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|median||.1f}} km²
(95 % block bootstrap {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|lo||.1f}} to
{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|hi||.1f}}) without a detectable loss of
event-flood recall.

The TOTAL water surface on the peak day — the quantity that operational "flooded area" products report — is
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_central_km2||.0f}} km² in the corridor plus
{{T12|region=INHULETS_VALLEY_rect,date=2023-06-07|W_total_central_km2||.0f}} km² in the Inhulets valley, against
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-05|W_total_central_km2||.0f}} km² of water in the normal regime on 5 June; Sentinel-1 saw
{{T19|date=2023-06-09,region=DNIPRO_CORRIDOR,sensor=S1|water_km2||.0f}} km² of dark water in the corridor on 9 June.

**Conclusions.** The mapped flood of a SAR mask, the persistent flood learned by a U-Net and the terrain-reconstructed
inundation are three different quantities. The reconstruction recovers the day-by-day extent, depth and volume that the
observations cannot, and the observations show where the reconstruction and the sensors are blind. We report every area
with its semantics and every model number as agreement with weak reference labels, not as flood-mapping accuracy.

**Keywords:** dam breach; inundation dynamics; SWOT; ICESat-2; Sentinel-1; HAND; weak supervision; U-Net; Kakhovka

## 1. Introduction

The destruction of the Kakhovka dam on 6 June 2023 released the largest reservoir of the Dnipro cascade into a 90 km reach
with a densely populated left bank, a reed-wetland delta and the Dnipro–Buh liman (Vyshnevskyi et al. 2023; Shumilova et al.
2025). Operational products reported the flooded area within days (UNOSAT via CEOBS 2023; REACH 2023), hydrodynamic
reconstructions of the breach followed (Kadam et al. 2024), and the SWOT mission, on its one-day calibration orbit, observed
the reach daily through the event (Lehnigk et al. 2026; Paper 1 of this series). What is still missing is a description of
the inundation that does not depend on which sensor happened to look on which day: an extent, a depth and a volume for every
day, tied to the observed water surface, with an uncertainty, and an account of where the satellite flood masks and such a
reconstruction disagree and why.

Two well-known properties of satellite flood mapping make this necessary. The area obtained by counting classified pixels is a
*mapped* area, not an unbiased estimate of the true flooded area; the good-practice framework of Olofsson et al. (2014) asks
for a probability-sample reference that does not exist here. And a Sentinel-1 dark-water rule does not see water under trees,
between buildings or under emergent reeds, while it does see smooth dark fields as water. A U-Net trained on labels derived
from those masks inherits both limits; its accuracy against such labels is agreement, not truth. We therefore structure the
study as a hierarchy of evidence (Fig02): a **physical reconstruction** of the daily inundation from the gauge-constrained,
SWOT-supported water-surface geometry and terrain connectivity is the main axis; **independent and cross-sensor
observations** (Sentinel-1 per acquisition date, night ICESat-2 ground heights, the SWOT–gauge comparison of Paper 1) check
it; the **surface context** (RF20 land-cover classes, WorldCover, elevation above the surface) explains the disagreements;
and controlled **U-Net experiments** under two frozen weak-label contracts show what EO inputs recover. Three principles hold
throughout: model numbers are agreement with weak reference labels, never flood-mapping accuracy; "not observed is not dry";
and every area carries its semantics — observed by Sentinel-1, mapped by the U-Net, reconstructed from terrain, or reported
in the literature.

This is Paper 3 of a series. Paper 1 reduced seven gauges, ICESat-2 ATL13 and SWOT to one local vertical frame and
measured the post-breach water-surface slopes; Paper 2 built the seamless terrain model (bathymetric bed and FABDEM, EVRF2019)
and validated it against night ICESat-2; Paper 5 will use the reconstruction presented here as the calibration target of a
two-dimensional hydraulic model. We inherit the vertical conventions of Paper 1 without re-validating them: satellite heights
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
rebuilt per draw. Bands are p05–p95 over draws on nine key dates; the draw median lies a few per cent above the deterministic central run because correlated DEM noise opens additional connections, so the band is reported next to the central value rather than centred on it; the planar-surface assumption and the absence of timing
(filling and draining) are not in the budget and make the recession a lower bound.

### 3.4 Checks: Sentinel-1 per date, disagreement ontology, ICESat-2

On each Sentinel-1 date the reconstruction is compared with the S1 new dark water (mask minus water on 1–2 June) on the S1
valid footprint, the owned zone area and outside the cut rectangles: hits, misses, terrain-only cells, POD, FAR and CSI
(primary, T13); POD after excluding the normally-wet cells is a sensitivity whose exclusion rule was fixed before any
comparison was read. The disagreement is decomposed into A (both), B (terrain only) and C (S1 only), by WorldCover and RF20
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

### 4.1 Daily terrain-reconstructed inundation [C01]

In the Dnipro corridor the reconstructed new inundation rises from zero on 5 June to
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-06|A_central_km2||.0f}} km² on 6 June and peaks at
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_central_km2||.0f}} km² on 7 June (p05–p95
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_p05_km2||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_p95_km2||.0f}} km²),
a day no satellite scene covers; it is {{T12|region=DNIPRO_CORRIDOR,date=2023-06-09|A_central_km2||.0f}} km² on 9 June,
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-13|A_central_km2||.0f}} km² on 13 June,
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-18|A_central_km2||.0f}} km² on 18 June and
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-21|A_central_km2||.0f}} km² on 21 June, when the Kherson stage is back at
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-21|kherson_gauge_m||.2f}} m (Fig04, T12). The water volume above ground peaks at
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_central_hm3||.0f}} hm³ (p05–p95
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_p05_hm3||.0f}}–{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_p95_hm3||.0f}}).
The p42 HAND rule gives {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_hand_and_ceiling_km2||.0f}} km² at the peak; the
ceiling without connectivity {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_ceiling_only_km2||.0f}} km². The largest single
term is definitional: with the DEM as delivered, the reed beds count as new inundation and the peak is
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_connected_ceiling_dem_uncorrected_km2||.0f}} km². Inside the p42 floodplain
domain the peak is {{T12|region=P42_FLOODPLAIN_DOMAIN,date=2023-06-07|A_central_km2||.0f}} km²; the Inhulets valley, treated as
backwater with its own SWOT nodes, peaks at {{T12|region=INHULETS_VALLEY_rect,date=2023-06-09|A_central_km2||.0f}} km² on 9 June.
The depth and duration maps (Fig07) show the 7–8 June water more than 4 m deep on the right-bank floodplain below the dam and
the delta channels, and inundation lasting more than a week only in the floodplain lows and the delta.

**Total water surface.** New inundation is the water that was not there before; the flood *zone* that operational products
report is the total water surface on the day. In the corridor it is {{T12|region=DNIPRO_CORRIDOR,date=2023-06-05|W_total_central_km2||.0f}} km²
in the normal regime (5 June), {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_central_km2||.0f}} km² on 7 June,
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-09|W_total_central_km2||.0f}} km² on 9 June and
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-13|W_total_central_km2||.0f}} km² on 13 June (with the DEM as delivered:
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-05|W_total_connected_ceiling_dem_uncorrected_km2||.0f}} →
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_connected_ceiling_dem_uncorrected_km2||.0f}} km²); the Inhulets valley adds
{{T12|region=INHULETS_VALLEY_rect,date=2023-06-07|W_total_central_km2||.0f}} km² on 7 June. Sentinel-1 saw
{{T19|date=2023-06-09,region=DNIPRO_CORRIDOR,sensor=S1|water_km2||.0f}} km² of dark water in the corridor on 9 June and
{{T19|date=2023-06-09,region=INHULETS_VALLEY_rect,sensor=S1|water_km2||.0f}} km² in the Inhulets valley. These totals are the numbers
comparable in kind with the 600–800 km² reported by operational products (T16, literature_reported), which differ further in AOI
(the liman reach, frame B3, is not part of this domain) and in the reference water they subtract.

### 4.2 Agreement with Sentinel-1 on the observation domain [C02]

On 9 June, in the p42 floodplain domain and on the Sentinel-1 footprint, the reconstruction allows
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|hand_new_km2||.0f}} km² of new water and Sentinel-1
reports {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|s1_new_km2||.0f}} km²; they share
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|hit_km2||.0f}} km² (POD
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|POD||.2f}}, FAR
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|FAR||.2f}}, CSI
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|CSI||.2f}}). Of the
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|miss_km2||.0f}} km² that Sentinel-1 reports and
the reconstruction does not, {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|miss_on_normally_wet_km2||.0f}} km²
lie on normally-wet cells; excluding them (sensitivity) POD is
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|POD_excl_normally_wet||.2f}}. On 13 June the
numbers are POD {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-13|POD||.2f}} /
{{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-13|POD_excl_normally_wet||.2f}}. After 18 June the
Sentinel-1 "new water" outside the floodplain domain ({{T19|date=2023-06-21,region=DNIPRO_CORRIDOR,sensor=S1|new_water_km2||.0f}} km²
on 21 June in the corridor) is scattered on fields and sand while the gauge is at its pre-breach level and the reconstruction is
at {{T12|region=DNIPRO_CORRIDOR,date=2023-06-21|A_central_km2||.0f}} km²: the dark-water rule, not the flood. The large-scale
recession seen by Sentinel-1 inside the floodplain (T19) follows the reconstruction and the gauge (Fig04).

### 4.3 The disagreement is mechanistic [C03]

On 9 June the two zones together give A = {{T14|date=2023-06-09,category=A|km2|sum|.0f}} km², B (terrain only) =
{{T14|date=2023-06-09,category=B|km2|sum|.0f}} km² and C (Sentinel-1 only) = {{T14|date=2023-06-09,category=C|km2|sum|.0f}} km²
(T14, Fig05). B lies entirely below the reconstructed surface and is dominated by surfaces the dark-water rule cannot see:
{{T14|date=2023-06-09,category=B|km2_wc_trees|sum|.0f}} km² trees, {{T14|date=2023-06-09,category=B|km2_wc_wetland|sum|.0f}} km²
wetland and {{T14|date=2023-06-09,category=B|km2_wc_built|sum|.0f}} km² built-up. C splits by ground elevation:
{{T14|date=2023-06-09,category=C|km2_ground_below_surface|sum|.0f}} km² below the surface and
{{T14|date=2023-06-09,category=C|km2_ground_0_2m_above|sum|.0f}} km² within 2 m above it, of which
{{T14|date=2023-06-09,category=C|km2_normally_wet|sum|.0f}} km² are normally-wet reed beds — the submergence of emergent
vegetation, a depth signal; and {{T14|date=2023-06-09,category=C|km2_ground_ge5m_above|sum|.0f}} km² at least 5 m above the
surface, on cropland and grass, which no water surface of this event can reach.

### 4.4 ICESat-2 altimetric consistency [C04]

Where Sentinel-1 reports water at least 2 m above the reconstructed surface, the seamless DEM agrees with night ICESat-2 ground
heights to {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_median||+.2f}} m (p10–p90
{{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_p10||+.2f}} to
{{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_p90||+.2f}} m, n =
{{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|N||.0f}} segments) in the delta and
{{T15|zone=ZONE_4_DAM_TO_KHERSON_FLOODWAY,category=S1_only_ground_ge2m_above|res_median||+.2f}} m (n =
{{T15|zone=ZONE_4_DAM_TO_KHERSON_FLOODWAY,category=S1_only_ground_ge2m_above|N||.0f}}) in the floodway; the ICESat-2 ground lies
{{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|ice_minus_wse_median||+.1f}} m above the surface in the delta and
essentially no segment ({{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|share_ice_below_wse||.1%}}) lies below it.
That water is false SAR water on land, not a DEM error. Where the reconstruction and Sentinel-1 agree,
{{T15|zone=ZONE_2_KHERSON_DELTA,category=both|share_ice_below_wse||.1%}} of the segments lie below the surface (T15, Fig08).
This is a track-based consistency check of the DEM and the surface, not a validation of the map.

### 4.5 Water-surface input and DEM accuracy [C05]

After re-anchoring to the Kherson-local closure the SWOT input agrees with the gauge at day level (median
{{T17|period=all days|median_m||+.2f}} m, NMAD {{T17|period=all days|NMAD_m||.2f}} m; during the rise and peak
{{T17|period=rise and peak 06-06..06-14|median_m||+.2f}} m over {{T17|period=rise and peak 06-06..06-14|n_days||.0f}} days),
consistent with Paper 1's +1.9 cm through the breach fortnight. The DEM error model of the Monte-Carlo is the class table of
Paper 2 (T18).

### 4.6 Three areas, three definitions [C06]

For the same corridor the 9 June Sentinel-1 scene contains {{T16|quantity=S1 new dark water, 06-09 scene;region=DNIPRO_CORRIDOR|km2||.0f}} km²
of new dark water (observed_S1), the label recipe (water on ≥ 2 of 3 peak dates) {{T16|quantity=S1 new dark water, >= 2 of 3 peak dates (label recipe);region=DNIPRO_CORRIDOR|km2||.0f}} km²,
the U-Net arm U2b {{T16|quantity=U2b predicted event flood (persistent concept);region=DNIPRO_CORRIDOR|km2||.0f}} km² (mapped_UNet), and the
reconstruction {{T12|region=DNIPRO_CORRIDOR,date=2023-06-09|A_central_km2||.0f}} km² on 9 June and
{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_central_km2||.0f}} km² at the peak (terrain_reconstructed). The label contract
is a persistence product and therefore describes the regime around 13 June; operational figures for 6–9 June and 13 June
(T16, literature_reported, VERIFY) differ in AOI, date and reference water and are context, not validation.

### 4.7 Inhulets backwater [C07]

The Inhulets valley has its own SWOT nodes and responds as backwater: on 9 June the reconstruction allows
{{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|hand_new_km2||.0f}} km² against
{{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|s1_new_km2||.0f}} km² seen by Sentinel-1
(POD {{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|POD||.2f}}, CSI
{{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|CSI||.2f}}); the p42 HAND rule, which measures
HAND to the Dnipro, is not applicable there. The valley is never added to the Dnipro reach.

### 4.8 Surface context [C11]

RF20 reaches an overall agreement of {{T09|evaluation=spatial_block_cv_5fold,cls=MACRO_MEAN|OA_spatial_cv||.3f}} with WorldCover
in spatial-block cross-validation (macro F1 {{T09|evaluation=spatial_block_cv_5fold,cls=MACRO_MEAN|F1||.3f}}), wetland/reed F1
{{T09|evaluation=spatial_block_cv_5fold,cls=WETLAND_REED|F1||.3f}} and built-up F1 {{T09|evaluation=spatial_block_cv_5fold,cls=BUILT_UP|F1||.3f}};
the transfers B1→B2 and B2→B1 are in T09. These are agreement numbers against the training reference.

### 4.9 What EO inputs recover under weak labels [C08–C10]

*Label effect.* At fixed inputs, U2 predicts {{T07|run=U2_B1B2_v1,endpoint=R_pred_on_reference_water_km2|value||.1f}} km² of flood on
the test-block REFERENCE_WATER under v002 and {{T07|run=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|value||.1f}} km² under
v003_A (paired difference {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|median||.1f}} km²,
95 % {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|lo||.1f}} to
{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|hi||.1f}}), while EVENT_FLOOD recall changes by
{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|median||+.3f}}
({{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|lo||+.3f}} to
{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|hi||+.3f}}). Global F1 is not comparable across label sets.
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
independent, because pre-event water information also contributes to the label ontology, and U2b is reported as a diagnostic
upper bound, not as a best model.

### 4.10 Block-size sensitivity [C12]

U2 on v003_A gives global F1 {{T20|split=m6_split_v1|G_F1||.3f}} on the frozen 10 km split,
{{T20|split=m6_split_s7p5|G_F1||.3f}} at 7.5 km, {{T20|split=m6_split_s15|G_F1||.3f}} at 15 km and
{{T20|split=m6_split_s20|G_F1||.3f}} at 20 km (each with its own test geography and interval, T20, FigS05); a 5 km split
leaves no validation patch inside the buffers. The conclusions of §4.9 are drawn from the 10 km split only.

## 5. Discussion

The three areas of §4.6 are not three estimates of one quantity. The dark-water rule counts water it can see on the day it
looks; the label contract counts water that persisted over three peak dates and therefore describes the recession, not the
peak; the reconstruction counts ground the observed water surface can reach. Their disagreement on 9 June is not noise: it
falls into surfaces the radar cannot see (forest, buildings, emergent reeds), reed beds that were already at the water level
in the normal regime and became dark only when submerged, and dark fields far above any water surface of the event, which the
independent altimetry shows to be land. The most useful product of the comparison is therefore not a single accuracy but the
map of where each source is blind.

The reconstruction's largest uncertainty is definitional rather than metric: whether the reed beds of the delta, which the
class-bias-corrected DEM places at or below the normal water surface, are "new inundation" or "wetland submergence" changes
the peak by about a third (T12). We report both, with the submergence quantified from the Sentinel-1 onset on normally-wet
cells (T13, T14). The metric uncertainty (Monte-Carlo band) is narrow by comparison; the planar surface and the absence of
timing are outside it and make the recession a lower bound, which Paper 5 will address with a two-dimensional model calibrated
on these daily surfaces.

The U-Net experiments say what an EO product can and cannot learn from such labels: changing the negative class (reference
water) removes attribution errors without loss of recall; terrain as an input suppresses part of the cropland burden; land
cover as an input does not act as a veto; and pre-event water as an input helps but cannot be evaluated independently while it
also defines the label. Every one of these statements is agreement with weak labels on a frozen spatial split.

## 6. Limitations

Planar water surface per node neighbourhood, no momentum and no timing of filling and draining; DEM under canopy and reeds
(FABDEM residuals of 1.5–2 m under trees); SWOT nodes on channels only, with the gauge cap beyond 15 km; no satellite scene on
the peak day; the date-only gauge against 11:00 UTC SWOT passes; weak labels whose positives are a persistence product;
W_pre circularity of U2b; frame B3 (delta with the liman) not built; no probability-sample reference for any area; literature
figures not verified against their sources; the Inhulets backwater treated with its own nodes but without a tributary
hydrograph.

## 7. Conclusions

See the claims register (`claims.md`, C01–C12). In one sentence: the observed water surface, projected on a bias-corrected
terrain with connectivity, gives a daily inundation extent, depth and volume with a stated uncertainty for the Kakhovka flood;
Sentinel-1 confirms it where the sensor can see and reveals, with ICESat-2, exactly where it cannot; and U-Net products trained
on such observations recover the persistent flood but inherit the sensor's blind spots unless the label contract names them.

## Data and code availability

Code, tables, figures, notebooks and the dashboard: https://github.com/NikoriakViktot/floodstate-eo (tag `v0.2.0-alpha`; Zenodo
DOI to be minted from the release). Processed rasters (≈ 100 GB) are documented in `docs/REPRODUCIBILITY.md` (three levels);
FABDEM-derived rasters are not redistributed (CC BY-NC-SA 4.0). SWOT (PO.DAAC), ICESat-2 (NSIDC), Sentinel (Copernicus) and
WorldCover (ESA) are open archives; gauge data from the UkrHMC yearbooks as in Paper 1.

## References

`docs/references.bib`; entries added for this paper carry `note = {VERIFY}` until checked (`references_to_verify.md`).
