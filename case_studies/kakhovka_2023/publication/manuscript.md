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
seamless terrain–bed elevation model (the FABDEM bare-earth DTM outside the surveyed channel, the surveyed bed inside; all heights
in EVRF2019), with the residual class-dependent terrain bias against ICESat-2 ground removed on the FABDEM cells, with a
connectivity rule evaluated once over the whole domain and a same-rule pre-breach baseline, so that the *reconstructed newly inundated area* is water on ground that was not water in the normal regime and the
*reconstructed total water-surface area* is all water on the day. This is an observation-constrained terrain inundation
reconstruction, not a hydrodynamic model: no momentum or continuity equations are solved, and values between observation days
are reconstructed, not observed. A Monte-Carlo budget of 1000 coherent worlds (the primary interval) — one terrain-error and
one water-surface realization per draw over the whole domain, the pre-breach regime rebuilt with each — propagates the datum
closure, gauge, SWOT, gap-dependent interpolation and spatially correlated class-wise terrain errors, with a covariance fitted to
the FABDEM − ICESat-2 residuals, and every newly inundated cell is classed by the distance of its SWOT support. Two river
gauges withheld from the reconstruction, Sentinel-1 dark-water masks on 11 dates, the disagreement between them and the
reconstruction decomposed by surface class and elevation, and night ICESat-2 ground heights are used as checks. RF20 surface classes supply the context; U-Net arms trained on two frozen weak-label contracts on a
frozen spatial-block split show what EO inputs recover.

**Results.** In the Dnipro corridor (Inhulets excluded) the reconstructed newly inundated area reaches its maximum of
262 km² on 7 June 2023 (Monte-Carlo median; primary p05–p95
250–278 km²; deterministic nominal run 243 km²), between the Sentinel-1 acquisitions of 6 June (partial)
and 9 June, one day before the peak stage at Kherson (5.78 m on 8 June in the river yearbook; the sources differ by ~0.1 m, §4.1); with the terrain as
delivered (no residual bias removed), i.e. with the reed beds counted as new, the nominal run gives 348 km² (against 243 km² nominal). The
reconstructed total water-surface area rises from 501 km² in the pre-breach regime (5 June)
to 791 km² on 7 June (median; p05–p95 767–819 km²; nominal run 797 km²),
with a further 70 km² in the Inhulets valley; the
reconstructed new-water volume is 627 hm³ (median; p05–p95 585–674 hm³; nominal run 514 hm³).
Reported central values are Monte-Carlo medians: on the peak days the deterministic nominal new area and volume lie below their own p05 — an effect of the terrain perturbation acting through the connectivity of the pre-breach regime (T11d) — while the nominal total water-surface area lies inside its interval. The maximum falls on 7 June in 77% of the Monte-Carlo worlds and on 8 June in 23%; 25% of the nominal new area on 7 June rests on water-surface support farther than 10 km.
The withheld Inhulets gauge shows the reconstructed surface metres too high while the backwater travelled up the tributary and its maximum 3 days early; the static reconstruction does not represent propagation time, which needs hydraulic modelling.
The newly inundated area falls to 136 km² on 13 June and 2 km² on 21 June.
On 9 June, inside the terrain-eligible floodplain, the raw agreement with Sentinel-1 new dark water is low
(POD 0.25, FAR 0.64) and strongly conditioned by surface type:
177 km² of Sentinel-1 "new water" lies on normally-wet reed beds below
the pre-breach surface (a submergence signal, not inundation onset); 54 km²
lies ≥ 5 m above the reconstructed surface and is topographically unsupported by the connected water surface, and along the
night ICESat-2 tracks that sample it the DEM agrees with the altimetry to a few centimetres in the median (p10–p90 spread of a few decimetres), so the available ICESat-2
observations give no evidence for a DEM bias large enough to explain it; 126 km² allowed
by the terrain is invisible to the dark-water rule, 45 km² of it under trees and
24 km² in built-up areas. Changing the weak-label contract from v002 to
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

The destruction of the Kakhovka dam on 6 June 2023 released the largest reservoir of the Dnipro cascade — 18.2 km³ at its normal retention level of 16.0 m, 19.8 km³ at the 16.76 m held on the eve of the breach (Vyshnevskyi et al. 2023) — into a ~90 km reach with a densely populated left bank, a reed-wetland delta and the Dnipro–Buh liman (Vyshnevskyi et al. 2023; Shumilova et al. 2025). Within days operational products reported the flooded *land*: about 620 km² over 6–9 June and about 180 km² on 13 June in the UNOSAT products relayed by OCHA (CEOBS 2023), figures that later studies cite (Yailymov et al. 2025). The published studies of the event are of three kinds. Satellite mappings give areas with their own definitions: Yailymov et al. (2025) map 473 km² of flooded land as of 9 June by land-cover class, 294 km² of it wetlands, against a pre-flood water map of 5 June; Zuo et al. (2024) follow the water-surface area at 300 m in Sentinel-3 OLCI scenes, which doubled within three days and was largest around 9 June; Monti et al. (2024) map the flooding along ~80 km of river with Sentinel-1 change detection; Jiao et al. (2025) use the event to test a Sentinel-1 flood-extraction method. Hydrodynamic models give scenario extents and stages: Kadam et al. (2024) obtain 823 km² and a peak of 3.6 × 10⁴ m³ s⁻¹ for a 300 m breach in HEC-RAS; Agerbeek et al. (2024) ran a near-real-time model checked against ICEYE extents and geolocated photographs; and Lehnigk et al. (2026) show with the daily SWOT water-surface elevations of the one-day calibration orbit — the data we use here — that two-dimensional outburst-flood simulations underestimate the observed peak stages by 1.4 to 6.1 m and misplace their timing unless reservoir and channel bathymetry are corrected, and even then reproduce neither stage nor timing fully; downstream stages reached 10–11 m by 8 June. Reservoir-side balances give the volume released: Yi et al. (2025) derive an initial breach flow of (5.7 ± 0.8) × 10⁴ m³ s⁻¹ and 20.4 ± 1.4 km³ lost in 30 days from gravimetry, altimetry and imagery; Shumilova et al. (2025) model about 16.4 km³ over two weeks. What none of these gives is a description of the inundation that depends neither on which sensor happened to look on which day nor on a hydrodynamic model whose bathymetry is unknown: an extent, a depth and a volume for every day, tied to the observed water surface, with an uncertainty, and an account of where the satellite flood masks and such a reconstruction disagree and why. Terrain-based approaches that project a water surface or a mapped extent on a DEM — HAND (Rennó et al. 2008; Nobre et al. 2011), GeoFlood (Zheng et al. 2018), FwDET (Cohen et al. 2019) — are first-order products, not hydrodynamics: Johnson et al. (2019) find that a HAND-based method "does not accurately capture inundated cells" while it does highlight regions at risk. Their depth and extent are sensitive to small vertical errors on low-relief floodplains, and because DEM error is spatially autocorrelated whereas accuracy statistics such as RMSE "assume error to [be] aspatial" (Hawker et al. 2018), it must be propagated with spatially correlated error realisations (Darnell et al. 2008; Le et al. 2026), not with independent noise.

Two well-known properties of satellite flood mapping make this necessary. The area obtained by counting classified pixels is a *mapped* area, not an unbiased estimate of the true flooded area; the good-practice framework of Olofsson et al. (2014) requires an accuracy assessment "based on a sample of higher quality" reference data, which does not exist for this event. And a C-band dark-water rule does not see water under trees, between buildings or under emergent reeds: the backscatter of vegetated and urban targets with and without flood water "represents the biggest challenge for inundation detection" (Grimaldi et al. 2020), flood water under vegetation "could not be detected with the C-band Sentinel-1 SAR" in a paddy landscape (Singha et al. 2020), and detection beneath vegetation and in cities is "not yet satisfactory" (Shen et al. 2019; review of flooded vegetation in SAR: Tsyganskaya et al. 2018). Conversely, "smooth surfaces at the scale of the measuring wavelength and shadowed areas share almost identical scattering properties with water surfaces" (Shen et al. 2019) and sand returns backscatter as low as open water (Martinis et al. 2018), so smooth non-water surfaces and radar shadow can look like water; exclusion maps derived from SAR time series formalise where flood cannot be inferred from intensity (Zhao et al. 2021). A U-Net trained on labels derived
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
- **Sentinel-2** L2A scenes (Sen2Cor processing, Main-Knorn et al. 2017) as index stacks per date at 10 m — NDWI (McFeeters 1996), MNDWI (Xu 2006), NDVI (Tucker 1979), NDMI (Gao 1996), BSI (Rikimaru et al. 2002, Tropical Ecology 43, 39–47), AWEIsh (Feyisa et al. 2014) and the turbidity index NDTI (Lacaux et al. 2007) — and PRE/EVENT/TRACE composites.
- **SWOT** L2_HR_RiverSP v2.0 nodes on the one-day calibration orbit (Biancamaria et al. 2016), 26 May–10 July 2023, 42 days, 732 nodes/day median;
  node_q ≤ 1 and dark fraction < 0.5 as in Paper 1. Published comparisons place SWOT river heights at the centimetre-to-decimetre level against gauges and altimetric references (RMSE 0.02 m against Hydroweb-next on the Congo, Normandin et al. 2024; a global river error below 0.15 m, Yu et al. 2024), which is why the product's own node uncertainty wse_u (median 0.092 m here) is used as the per-node term of the Monte-Carlo (§3.3).
- **Kherson gauge 80805**, daily, river yearbook, BS-77 → EVRF2019 by the official EPSG:9902 operation (+0.216 m at the post);
  6–12 June are flagged in the sea yearbook (recorder failure) and the river-yearbook values are used, as in Paper 1 §5.12.
- **Seamless terrain–bed elevation model** (Paper 2): the kriged bathymetric bed inside the pre-breach water polygons and FABDEM v1.2 elsewhere — a bare-earth DTM derived from the Copernicus DEM with buildings and forests removed by machine learning (Hawker et al. 2022; residual mean absolute errors of 1.1–1.6 m remain in built-up areas, Iqbal et al. 2023) — on one 20 m grid in EVRF2019, with a source mask that records which cells are FABDEM and which are bed. EVRF2019 is the vertical frame of every height in this paper: the SWOT, gauge and ICESat-2 chains of Papers 1 and 2 end in it, and the reconstruction refuses an input that does not declare it. Against night ICESat-2 ground the FABDEM cells keep a class-dependent residual bias, estimated per zone and land-cover class and removed on the FABDEM cells only (§3.2, T18b);
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
node at its coordinates, and cells farther than 15 km from any node and west of the gauge are capped at the gauge level. A node
is held at its first and last observation beyond them, and a cell without a node within 3 km takes the nearest node of the day:
on 7 June 371 km² of the reconstructed water surface take their height from
nodes within 3 km and 426 km² from the nearest node farther away (T11g; the
observed / interpolated / held flags of every node-day are kept and enter the uncertainty budget, §3.3). Each newly inundated
cell is also classed by the distance of its nearest SWOT node: *direct* (≤ 3 km, the surface is observed around the cell),
*extrapolated* (3–10 km) or *weak* (> 10 km, weakly constrained), with two independent flags — capped at the Kherson gauge, and,
in the Inhulets valley, served by a node of another river (*cross-river*). The 3 and 10 km limits are operational thresholds,
not physical constants: the full reconstruction remains the primary product, its *supported core* (direct + extrapolated) is
reported next to it (T11k, T11l, FigS14), and a run with no surface from nodes farther than 10 km is a separate sensitivity.
After re-anchoring, the daily median of the nodes within 3 km of the gauge differs from the gauge by
+0.01 m (NMAD 0.07 m, RMSE 0.06 m,
n = 36 days; T17, Fig06) — an input-consistency check; the frame validation is Paper 1.

### 3.2 Terrain rule, baseline and the definition of "new inundation"

The reconstruction is a static terrain-connectivity model rather than a dynamic hydraulic simulation. Gravitational control is
represented implicitly through the terrain elevation relative to the imposed water-surface elevation and through topographic
connectivity; the method does not solve momentum or continuity equations and therefore does not represent finite flood-wave
propagation, frictional losses or transient backwater dynamics (§5). The inundation operator follows the static
terrain-connectivity principle of topography-based flood mapping such as c-HAND, which floods the cells whose elevation "is
lower than the gage elevation" and which "are connected to the ocean" under "a static equilibrium assumption" (Wang et al.
2024), and the flood-fill procedure of Dale et al. (2026): terrain cells below the imposed water surface are retained only
when topographically connected to the reference water network. Here this principle is extended from a spatially uniform or
locally estimated water level to a spatially distributed, observation-constrained water surface H(x, y, t) derived from the
SWOT nodes and the gauge, with a same-rule pre-breach baseline that separates new inundation from pre-existing water, and a
propagated uncertainty (§3.3).

A cell is water on day t if its terrain lies below the water surface and it is 8-connected, through such cells, to the pre-breach
optical water network (p60 pre-water frequency ≥ 20 %), within 10 km of pre-breach water and downstream of the dam
(*connected ceiling*). Two other rules bound it: the p42 rule (additionally HAND < WSE − 1 m, channel-connected through the mapped drainage; a lower bound because the delta drainage is incompletely mapped) and the ceiling without connectivity. The connectivity requirement is not inherited from the terrain-index methods we build on: HAND-type methods "do not preserve hydraulic connectivity (i.e., floodplain cells lower than the channel water height are denoted as flooded whether or not there is a physical flow path to them)" (Bates 2022), and GeoFlood by design flags "local depressions such as ponds or waterbodies … even if they are not connected with the main stem river" (Zheng et al. 2018). Enforcing connectivity by connected-components analysis, as in coastal bathtub mapping (Kulp and Strauss 2019), is what turns the ceiling into a lower-biased but physically admissible extent; small channels that the 20 m grid does not resolve are a known control on floodplain connectivity (Neal et al. 2012), and in flat terrain the inferred flow path can differ from the real one (Guo et al. 2025) — the two reasons the p42 and connected-ceiling rules are reported as bounds rather than as one answer. The
rule is evaluated once on the union of the two zone grids, so that a connection may cross the zone boundary; the overlap is
attributed to the delta zone only for accounting (a per-zone evaluation with the ownership applied before the connectivity finds
0.0 km² of difference on 7 June, T11i). On the FABDEM cells the terrain enters after
subtraction of the residual class-dependent terrain-elevation bias, estimated per zone and WorldCover class from FABDEM − ICESat-2
ground differences (T18b; pooled medians: trees +1.65 m, wetland
+0.56 m, grass +0.32 m, cropland
+0.09 m); FABDEM is already a bare-earth DTM, so this is a residual bias, not a
canopy correction, and the bed cells are used as surveyed. The *normal regime* is the union of the same rule over the pre-breach days 26 May–5 June plus the observed
pre-breach water (Sentinel-1 1–2 June, p60); **new inundation** is water on day t outside that regime. Cells of the model-only
normal regime ("normally wet": low reed beds below the normal surface that no optical or SAR mask lists as water) are kept as
their own category, because a Sentinel-1 dark-water onset there is a depth signal — the reeds are submerged — not the onset of inundation: in flooded vegetation the double bounce raises C-band backscatter above the non-flooded level, but once the water rises over the plants the signal turns dark (Grimaldi et al. 2020; Jarrett et al. 2023; review: Tsyganskaya et al. 2018), so the date on which a reed bed goes dark is the date its canopy went under, not the date water arrived. With the terrain as delivered (no residual bias removed) those reed beds sit above the normal surface and count as new inundation; we report
that run as a sensitivity (T12) and the two quantities — new inundation and wetland submergence — separately.

### 3.3 Uncertainty budget

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
the pre-breach water, and 99.5% of the new area on 7 June is on FABDEM
cells, T11j). These 1000 draws are the **primary uncertainty interval**
of every reconstructed area and volume: p05–p95 reported next to the Monte-Carlo median. The stability of the quantiles against
the ensemble size and a second seed is shown in T11c and FigS12 (finite ensembles carry their own sampling uncertainty of tail
quantiles, Roy and Gupta 2021), the attribution of the width and of the median's position relative to the nominal run to the
error components in T11d, and the sensitivity of the connected area to a uniform water-surface offset in T11e and FigS13. A
cluster-normal emulator with 100 000 draws per day (p95g) is kept only as a computational diagnostic (T12d): it has no
connectivity and its total water-surface envelope is built around the nominal total, so it is not an uncertainty estimate and
no reported number rests on it. The planar-surface assumption, the absence of timing (filling and draining) and the support
distance of §3.1 are outside the budget.

### 3.4 Checks: Sentinel-1 per date, disagreement ontology, ICESat-2

On each Sentinel-1 date the reconstruction is compared with the S1 new dark water (mask minus water on 1–2 June) on the S1
valid footprint, the owned zone area and outside the cut rectangles: hits, misses, terrain-only cells, POD, FAR and CSI (contingency-table measures, Schaefer 1990; raw agreement, primary, T13) — reported per date and per domain because binary pattern measures depend on the size of the flood and of the domain over which they are computed (Stephens et al. 2014); the *conditional POD outside the normally-wet class* — POD on the observable dry-background
domain, with the class fixed before any comparison was read — is a diagnostic conditional agreement, not a corrected POD. The disagreement is decomposed into A (both), B (terrain only) and C (S1 only), by WorldCover and RF20
class and by ground elevation relative to the reconstructed surface (< 0, 0–2, 2–5, ≥ 5 m; T14). Night ICESat-2 ATL08 ground
segments (Paper 2 chain) sampled on the 9 June categories (inside the S1 valid footprint only) give, per category, the
residual terrain − ICESat-2 on the FABDEM cells, as delivered and after the class-bias correction, and the share of segments
whose ground lies below the reconstructed surface (T15): an altimetric consistency check of the terrain and the surface along
tracks, not a validation of the inundation map — the same night corpus also calibrates the class bias. Three river gauges of
the 2023 hydrological yearbook have distinct roles: Kherson (80805) is an input and the anchor of the water surface; the
Inhulets gauge Kalynivske (80575) and the liman gauge Mykolaiv (98027) are withheld from the reconstruction and serve as
independent validation sites for two different failure modes — the tributary backwater and the western delta. Their daily
means (cm above the gauge zero, the zero read from the yearbook sheet, EVRF2019 by the EPSG:9902 grid step) are compared with
the reconstructed surface at the gauge as an absolute error and as an event-relative error, (H_rec − H_rec,pre) −
(H_gauge − H_gauge,pre), which is free of any constant datum offset between the two series; peaks and rises use the yearbook's
highest level of the year (T17c–T17f).

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
203 km² on 6 June and reaches its maximum of
262 km² on 7 June (Monte-Carlo median; primary p05–p95
250–278 km²; deterministic nominal run 243 km²),
a day between the Sentinel-1 acquisitions that no scene covers [C01]. Across the 1000
Monte-Carlo worlds the maximum of the reconstructed new inundation falls on 7 June in
77% of the realizations and on 8 June in
23% (T12c). The Kherson stage reaches its maximum one day later
(5.78 m on 8 June, the daily value of the river yearbook used here;
the operational record gives 5.68 m at 15:00 on 8 June (Gleick et al. 2023) and Lehnigk et al. 2026 cite 5.6 m, a ~0.1 m spread
between sources; the peak stages by 8 June that Lehnigk et al. 2026 report from the same SWOT data are consistent with it) — the areal maximum and the peak stage are different quantities, and the day of the
areal maximum is a property of the reconstructed series, not an observation. It is 216 km² on 9 June,
136 km² on 13 June,
44 km² on 18 June and
2 km² on 21 June, when the Kherson stage is back at
0.74 m (Fig04, T12) [C03]. The reconstructed new-water volume
reaches 627 hm³ (median; p05–p95
585–674 hm³;
deterministic nominal run 514 hm³) [C02]. All areas and volumes after 5 June are Monte-Carlo medians unless marked as a nominal run.
These values describe the full terrain-connectivity reconstruction. Its support is uneven (§3.1, T11k): of the nominal new area on
7 June, 73 km² are directly supported by nodes within 3 km,
108 km² extrapolated from nodes 3–10 km away, and
25% rests on water-surface support farther than 10 km (weakly
constrained); the supported core is 182 km² of the nominal
243 km², and a run with no surface from nodes beyond 10 km — which also
changes the connectivity — gives 180 km² (FigS02, FigS14). The
weak share falls to 7% on 9 June and
2% on 13 June, and inside the p42 floodplain domain it is
6% on 7 June: the distant support concerns mainly the first
days of the event and the ground outside the terrain-eligible floodplain.
The rule and terrain sensitivities are deterministic runs and compare with the nominal connected run (243 km²), not with the median:
the p42 HAND rule gives 248 km² at the reconstructed areal maximum; the
ceiling without connectivity 262 km². The largest single
term is definitional: with the terrain as delivered (no residual bias removed), the reed beds count as new inundation and the areal maximum is
348 km². Inside the p42 floodplain
domain the areal maximum is 171 km²; the Inhulets valley, treated as
backwater with its own SWOT nodes in the lower valley only (§4.7), peaks at 48 km² on 9 June.
The depth and duration maps (Fig07) show the 7–8 June water more than 4 m deep on the right-bank floodplain below the dam and
the delta channels, and inundation lasting more than a week only in the floodplain lows and the delta.

**Reconstructed total water-surface area [C02].** The newly inundated area is the water that was not there before; the total
water-surface area is all water on the day, including the pre-breach channels, lakes and reed beds. In the corridor it is 501 km²
in the normal regime (5 June, nominal run; Monte-Carlo median 473 km², p05–p95 445–498 km²), 791 km² on 7 June (median; primary p05–p95
767–819 km²; nominal run 797 km²),
741 km² on 9 June and
634 km² on 13 June (with the terrain as delivered:
310 →
714 km²); the Inhulets valley adds
70 km² on 7 June. Sentinel-1 saw
682 km² of dark water in the corridor on 9 June and
68 km² in the Inhulets valley. Neither total is comparable
with the operational figures: the UNOSAT ~620 km² of 9 June is cumulative satellite-detected flooded *land* over 6–9 June with the
pre-existing water as a separate class (T16, literature_reported, VERIFY), a quantity closer in kind to the newly inundated area
than to the total water-surface area, and it differs further in AOI (the liman reach, frame B3, is not part of this domain),
in temporal semantics (cumulative vs daily snapshot) and in reference water (§4.6).

**Uncertainty per day [C07].** On 7 June the Monte-Carlo worlds give relative half-widths of
6 % for the newly inundated area, 3 % for the
total water-surface area and 9 % for the volume; the quantiles are stable against the ensemble
size and a second seed (T11c, FigS12: p05–p95 of the new area 250–278 km²
with 1000 worlds, 249–280 km² with the second seed). The deterministic
nominal run is a diagnostic: the medians of the new area and of the volume lie +8 % and
+22 % above it (T12b flags the days on which it falls below the p05). The ablation attributes the
offset (T11d): with the terrain alone perturbed the median new area on 7 June is
267 km², with the water surface alone
239 km², and with both perturbed but the pre-breach regime held at the nominal
248 km² (nominal 243 km²). The upward
shift of the stochastic new-inundation distribution relative to the nominal reconstruction arises primarily from nonlinear
connectivity effects on the pre-event baseline: terrain perturbations reduce the connected baseline water (with the terrain alone perturbed, a rebuilt regime of
775.2 km² against
810.5 km² at the nominal) more strongly than the peak-event total water,
and the cells so released, deep under water at the flood stage, count as new and add depth (Darnell et al. 2008; Hawker et al.
2018). Connectivity is a nonlinear operator of the terrain, so a zero-mean terrain error need not leave the median area at the
nominal one; the same threshold behaviour appears in the response to a uniform water-surface offset (T11e, FigS13). The daily
change of the newly inundated area (bars in Fig04) shows the filling on 6–7 June and the draining at 30–40 km² per day between
10 and 18 June.

**Reservoir side of the balance [C14] (context).** Under the sloped daily surface (outlet SWOT nodes, Nikopol press values, Rozumivka gauge)
the pool held 18.9 km³ on 5 June (design table at the same outlet level:
21.1 km³) and 4.5 km³ on 13 June, i.e.
14.7 km³ released in eight days, with the largest daily volume change of
-3225 hm³ on 7 June. The corresponding daily-mean effective release, −dV/dt + Q_in, is
40057 m³ s⁻¹ against a DniproHES inflow of
2730 m³ s⁻¹: a storage-balance estimate on a surface interpolated between three or
four level points, a daily mean and not an instantaneous breach discharge. Published estimates are different physical quantities of the same order and are context, not validation: the *initial* breach flow of Yi et al. (2025) from a gravimetry–altimetry–imagery discharge model is (5.7 ± 0.8) × 10⁴ m³ s⁻¹, the HEC-RAS scenario peaks of Kadam et al. (2024) are 3.6 × 10⁴ m³ s⁻¹ (300 m breach) and 4.8 × 10⁴ m³ s⁻¹ (600 m), and Shumilova et al. (2025) model a release of about 16.4 km³ over two weeks. The released volume itself is period- and hypsometry-dependent in the literature: Yi et al. (2025) obtain 20.4 ± 1.4 km³ in 30 days from a pre-breach volume of 21.0 km³ (17.3 m), Vyshnevskyi et al. (2023) give 19.8 km³ at 16.76 m from the operation rules, Monti et al. (2024) about 7.5 km³, and Lehnigk et al. (2026) cite ∼8 km³; our 14.7 km³ over 5–13 June sits inside that spread, and the -9 % hypsometry gap below is of the same size as the spread among the published pre-breach volumes (18.2–21.1 km³). The surface gradient across the pool reached 5.0 m on 10 June. Downstream, the reconstructed new water stored above ground reaches its maximum on 9 June — 642 hm³ in the nominal run (corridor 447 hm³, MC median 561, p05–p95 517–610; Inhulets 195 hm³, MC median 194, p05–p95 181–208; T12) — a few per cent of the release, implying that most of the released volume was transmitted downstream rather than stored on the mapped floodplain (Fig09, T21). The seamless-DEM hypsometry
lies below the design table at equal levels — -9 % at 17.5 m,
-14 % at 13 m, -20 % at 11 m; the design table
is undefined below 10 m (T22, FigS07) — so the released volume inherits this gap; its origin (datum, present morphology, the
underwater part of the seamless DEM, shoreline geometry, the original survey) is the subject of Paper 4, which reconstructs the
bowl on the historical bathymetry.

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
index statistics per stratum in T25–T26). The modelled full pool of 2132 km² on 5 June lies within the published pre-breach areas (2091 km² on 5 June from Sentinel-2, Magas et al. 2023; 2125 km² on 30 May, Yi et al. 2025; design 2155 km² at the normal impoundment level, T27). The wet-mud reading of the post-13-June dark surface is consistent with the documented look-alike behaviour of smooth bare surfaces in C-band (Shen et al. 2019), although no study in the literature reviewed measures it for wet reservoir sediment. Published remnant areas differ by definition rather than by error: about 845 km² by 20 June from the decreases reported by Yi et al. (2025), 655.9 km² on 17 June in the state estimate quoted by Novitskyi et al. (2024), 379.7 km² on 8 September including the restored channel (Magas et al. 2023), and 1.63 km² of open water on 6 September with 110 km² still wet (Tsiupa et al. 2023). Dry bare sediment covers 49 % of the observed pool on 5 July (T24); the recolonisation by September is what field surveys report — the number of vascular plant taxa rising about sevenfold between June and October 2023, mainly willow establishing (Kuzemko et al. 2024, 2025; Vyshnevskyi 2024) — and what index-based studies document from Sentinel-2 (Tutova et al. 2025; 135 thousand ha of vegetated bed in 2023–2024, Pichura and Potravka 2025). These are observations of the bed, not results of this paper; they are the hand-over to Paper 4.

### 4.2 Raw agreement with Sentinel-1 on the observation domain [C04]

On 9 June, in the p42 floodplain domain and on the Sentinel-1 footprint, the reconstruction allows
136 km² of new water and Sentinel-1
reports 201 km²; they share
49 km² (POD
0.25, FAR
0.64, CSI
0.17). Of the
152 km² that Sentinel-1 reports and
the reconstruction does not, 150 km²
lie on normally-wet cells. The raw agreement is therefore low, and most apparent terrain misses occur in predefined normally-wet
or vegetation-dominated cells where SAR dark-water onset is not an appropriate binary reference; the conditional POD outside the
normally-wet class is 0.97,
a diagnostic conditional agreement, not a corrected POD. On 13 June the raw POD is
0.15 and the conditional POD
0.93. After 18 June the
Sentinel-1 "new water" outside the floodplain domain (155 km²
on 21 June in the corridor) is scattered on fields and sand while the gauge is at its pre-breach level and the reconstruction is
at 2 km²: these detections are not supported as connected breach-induced inundation by the available terrain and water-surface constraints. Their pattern — fields and sand far above any water surface of the event — is consistent with a known C-band look-alike behaviour (smooth or wet bare surfaces and shadow scatter like water; Shen et al. 2019), but whether they are non-water, local ponding after rain or water outside the assumed connectivity is not tested here (§4.3). The large-scale
recession seen by Sentinel-1 inside the floodplain (T19) follows the reconstruction and the gauge (Fig04).

### 4.3 The disagreement is mechanistic [C05]

On 9 June the two zones together give A = 56 km², B (terrain only) =
126 km² and C (Sentinel-1 only) = 263 km²
(T14, Fig05). B lies entirely below the reconstructed surface and is dominated by surfaces the dark-water rule cannot see:
45 km² trees, 19 km²
wetland and 24 km² built-up. C splits by ground elevation:
170 km² below the surface and
33 km² within 2 m above it, of which
177 km² are normally-wet reed beds — the submergence of emergent
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
1665) in the floodway; the ICESat-2 ground lies
+13.5 m above the surface in the delta and
essentially no segment (0.0%) lies below it.
The available ICESat-2 observations therefore provide no evidence for a DEM bias large enough to explain those S1-only
detections; they support the reading of §4.3 without proving it, because the tracks (listed with their dates in T15) sample
the category along lines, not every cell of the 54 km². Where the
reconstruction and Sentinel-1 agree, 99.5% of the segments lie
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
reconstruction 216 km² on 9 June and
262 km² at the reconstructed areal maximum (terrain_reconstructed). The label contract
is a persistence product and therefore describes the regime around 13 June. The operational figures — UNOSAT product 3616,
~620 km² of satellite-detected flooded land cumulative over 6–9 June with the pre-existing water as a separate class,
preliminary and not field-validated; product 3623, ~180 km² on 13 June against the reference water of 3/5 June (T16,
literature_reported, VERIFY) — are flooded *land*, closer in kind to the newly inundated area than to the total water-surface
area, and differ in AOI, temporal semantics (cumulative vs snapshot) and reference water; they are context, not validation. Two peer-reviewed mappings of the same flood carry their own definitions as well: Yailymov et al. (2025) count 473 km² of flooded land as of 9 June across the Kherson region including the Inhulets valley, relative to a pre-flood water map of 5 June, of which 294 km² are wetlands — the class in which this paper's submergence category lives — and Zuo et al. (2024) follow the total water-surface area at 300 m resolution, largest around 9 June. Neither is the corridor snapshot of this paper. Our reading is that the large wetland share of Yailymov et al. points the same way as §4.3, where most Sentinel-1 "new water" on 9 June lies on normally-wet reed beds. T16 carries the area, quantity and temporal semantics of every row.

### 4.7 Withheld gauges: the Inhulets backwater and the western delta [C03]

The Inhulets valley has its own SWOT nodes and responds as backwater — Lehnigk et al. (2026) trace the flood pulse at least 150 km up the tributary, and confluence backwater is a known control on tributary stage and flood-wave timing (De Paiva et al. 2013): on 9 June the reconstruction allows
18 km² against
36 km² seen by Sentinel-1
(POD 0.33, CSI
0.28); the p42 HAND rule, which measures
HAND to the Dnipro, is not applicable there. The valley is never added to the Dnipro reach. Its own SWOT nodes, however, stop about
10 km above the mouth (N 5180 km): of the valley's reconstructed new area on 7 June
(41.4 km², nominal run) only 0.4 km² is directly supported by a node
within 3 km, 93% is weakly constrained (nearest node farther than 10 km), and
11.3 km² takes its surface from a Dnipro node (cross-river flag; T11k). Distance, not only the
river of the node, limits the constraint: the Inhulets nodes of the lower valley also stood metres above the tributary upstream
on the first day of the event. The gauge Inhulets – Kalynivske (80575), about 40 km up the valley, is withheld from the
reconstruction and kept as an independent tributary validation site. It recorded the backwater —
0.58 m EVRF2019 before the breach and 6.59 m EVRF2019 on 2023-06-10 at its highest level, a record for the
station, with the upstream posts unchanged (80568: 289-303; 80564: 402-404) and high water on 7–18 June according to the
yearbook remark. At the gauge the reconstructed surface is the level of one Dnipro node below the dam,
39.5 km away, on 46 of 46 days. While the backwater was still travelling up the
valley the absolute error reached +9.50 m on 2023-06-06; the reconstruction peaks
3 days before the gauge and rises by +9.28 m against
+5.87 m at the gauge (daily means). The event-relative error, free of any constant datum offset
between the two series, shows that the close absolute agreement after the peak (+0.04 .. +0.92 m) is a
coincidence of the pre-breach offset and a recession that runs ahead of the valley
(-0.72 m on 2023-06-14); the two agree within ±0.25 m only from 2023-06-26 (T17c, T17d, FigS15).
Because the support never changed, the error follows the hydraulic state: large during the transient, small once main stem and
valley stand at one level. A separate gauge-assisted sensitivity, not used for any reported number, adds the gauge as a
local water-surface node: the valley's reconstructed new area on 7 June falls from
41.4 to
19.2 km², and the agreement with
the independent Sentinel-1 observations on 9 June rises from CSI
0.28 to
0.32: adding a local
tributary water-level constraint systematically reduced the reconstructed early-event inundation and improved the agreement
with Sentinel-1. The Inhulets areas of this paper are therefore observation-constrained only in the lower valley; above it,
where the surface comes from distant nodes, they are reported as weakly constrained.

The liman gauge Mykolaiv (98027), also withheld, tests the western end of the domain. The liman rose by
1.05 m to 1.22 m EVRF2019 on 2023-06-08, a record for the station, on the day of the Kherson peak stage;
the reconstructed western delta takes its surface from the westernmost SWOT node, which has no observation from
2023-06-06 .. 2023-06-22 and is interpolated flat across the flood, so at the gauge the reconstruction misses
the rise (-0.82 m on 2023-06-08 in absolute terms; T17e, T17f, FigS15). The two withheld gauges expose two different
structural limits — the propagation time of the tributary backwater at Kalynivske and the sampling of the water surface in the
western delta at Mykolaiv — which a single error statistic would average away.

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

**Why the reconstruction needs a hydraulic model.** The reconstruction is static (§3.2): gravity is present only implicitly —
a cell floods when its terrain lies below the water surface and a connected path leads to it — and scaling both heights by *g*
changes nothing (*gz* < *gH* exactly when *z* < *H*), so a separate potential or gravity layer would add no information. What
it lacks is dynamics. Flood-fill and bathtub models assume "zero flow resistance and instantaneous water propagation, leading to
highly non-linear relationships between water surface elevation and inundated flood area" (Dale et al. 2026) — the threshold
behaviour of FigS13 and of the Monte-Carlo shift (T11d) — and they "may overestimate floods because they do not capture some of
the relevant underlying hydrodynamic processes that govern flood propagation on land" (Kasmalkar et al. 2024); c-HAND, the
closest static analogue of our operator, over-predicts the inundated area of a hydrodynamic simulation by about 27 % while
finding 99 % of its flooded cells (Wang et al. 2024). The withheld
Inhulets gauge measures this limit directly: while the backwater travelled up the tributary, the reconstructed surface, taken
from the main stem, stood above the gauge by +9.50 m on 2023-06-06; the reconstructed maximum came
3 days before the observed one; and in the recession the reconstruction drained ahead of the valley
(-0.72 m on 2023-06-14 in event-relative terms), so that the close absolute agreement after the peak is a
coincidence of two errors (§4.7, FigS15). Adding the gauge as a water-surface node improves the reconstruction (T12, T13) but cannot
give it a clock. Nor can the lighter extensions of the geometric method: path-based attenuation damps depths along the flow
paths to mimic friction and a transient forcing (Kasmalkar et al. 2024), and depression routing such as Fill–Spill–Merge
conserves the volume that fills and spills between depressions (Barnes et al. 2021), but neither resolves time. Propagation,
storage, friction and transient backwater require the continuity and momentum equations — a two-dimensional shallow-water
model driven by the water-surface gradient over the corridor, the delta and the Inhulets valley, with the Dnipro stage at the
confluence as the tributary's downstream boundary, since backwater at confluences controls tributary stage and flood-wave
timing (De Paiva et al. 2013), and with the liman stage at Mykolaiv as the boundary that the western delta now lacks (§4.7).
Such models of this event need corrected reservoir and channel bathymetry before they reproduce the observed stages and their
timing (Lehnigk et al. 2026), so they cannot replace the observation-constrained reconstruction — and the reconstruction cannot
replace them. The two are complementary: the daily reconstructed extents and volumes with their support classes, the SWOT
water-surface profiles, the Sentinel-1 dates and the two withheld gauges are the calibration and validation targets of the
hydraulic model of the follow-up study (Paper 5), and the hydraulic model is what can give the reconstructed daily states their
timing.

The three areas of §4.6 are not three estimates of one quantity. The dark-water rule counts water it can see on the day it
looks; the label contract counts water that persisted over three peak dates and therefore describes the recession, not the
areal maximum; the reconstruction counts ground the observed water surface can reach. Their disagreement on 9 June is not
noise: it falls into surfaces the radar cannot see (forest, buildings, emergent reeds), reed beds that were already at the water
level in the normal regime and became dark only when submerged, and dark fields far above any water surface of the event, which
are topographically unsupported by the reconstruction and for which the independent altimetry gives no evidence of a DEM error
large enough to explain them. The most useful product of the comparison is therefore not a single accuracy but the map of where each source is blind. Operational SAR flood services have reached the same conclusion from the sensor side: exclusion maps derived from C-band time series mark where flood cannot be inferred from intensity (Zhao et al. 2021), the Copernicus EMS ensemble delivers "an exclusion mask indicating the regions where the detection is prevented" next to its flood layer (Amitrano et al. 2024), and the Sentinel-1 data-cube architecture behind the Global Flood Monitoring service was designed to carry "masks showing where Sentinel-1 cannot detect floods due to physical reasons" (Wagner et al. 2020). What the terrain reconstruction adds to such masks is the other half of the picture — where the radar reports water that the observed water surface cannot reach — and, through ICESat-2, a test of whether the terrain itself is at fault there.

The reconstruction's largest uncertainty is definitional rather than metric: whether the reed beds of the delta, which the
class-bias-corrected DEM places at or below the normal water surface, are "new inundation" or "wetland submergence" changes the reconstructed areal maximum by about a third (T12). We report both, with the submergence quantified from the Sentinel-1 onset on normally-wet
cells (T13, T14). The metric uncertainty (the primary Monte-Carlo interval) is narrow by comparison, and enters the volume
mainly as a displacement; the planar surface and the absence of timing are outside it and make the recession a lower bound,
which Paper 5 will address with a two-dimensional model calibrated on these daily surfaces. The reservoir balance of §4.1 is
context: a daily-mean effective release from a sloped surface between three or four level points on a DEM whose hypsometry sits
below the design table; Paper 4 will rebuild the bowl on the historical bathymetry before that balance can be more than an
order-of-magnitude check against the published breach-flow estimates.

The U-Net experiments say what an EO product can and cannot learn from such labels: changing the negative class (reference
water) removes a measurable reference-water artefact with no statistically resolved change in recall; terrain as an input suppresses part of the cropland burden; land cover as an input does not act as a veto; and pre-event water as an input helps but cannot be evaluated independently while it also defines the label. Every one of these statements is agreement with weak labels on a frozen spatial split — labels of the kind that the flood-mapping literature now trains on routinely (Sentinel-1/2 threshold classifications as weak labels: Bonafilia et al. 2020; Katiyar et al. 2021; Sharma et al. 2025) and whose errors a model "still ends up learning" (Garg et al. 2023). The direction of the terrain effect is not general either: with HAND used as a Bayesian prior rather than an input channel, Tupas et al. (2023) reduced false negatives "at the cost of slightly increasing false positives", the opposite trade-off to the cropland result here, so what terrain does to a SAR flood product depends on how it enters the model and on which label it is scored against.

## 6. Limitations

A daily reconstructed series, not daily observations: between observation days the values are interpolation and model. A static
reconstruction: as in other static equilibrium terrain-connectivity approaches (Wang et al. 2024; Dale et al. 2026), it does
not solve momentum or continuity equations and therefore does not simulate finite propagation time, frictional losses,
transient storage or backwater dynamics, and its water surface is planar per node neighbourhood — the withheld gauges show where
this matters and why a hydraulic model is the next step (§5); a residual terrain error of the
FABDEM DTM under reeds, trees and buildings (under trees a class median of +1.7 m and an
NMAD of 1.7 m, T18b) and no stochastic term on the surveyed bed; SWOT nodes on channels
only, with the gauge cap beyond 15 km, and cells without a node within 3 km taking the nearest node of the day (T11g) — a
structural choice outside the Monte-Carlo, to which the delta on 9–13 June is sensitive (with nodes unavailable beyond a
3-day gap the corridor's new area on 9 June is 252 km²
against 188 km² nominal; with the fallback capped at 10 km the
corridor's new area on 7 June is 180 km² against
243 km², the p42 floodplain domain changing much less) and which leaves the
upper Inhulets valley weakly constrained (water surface from distant nodes; the withheld gauge Kalynivske, T17c, T17d); the westernmost SWOT node of the delta has no
observation from 2023-06-06 .. 2023-06-22, so the western delta keeps a pre-breach water surface while the liman
at Mykolaiv rose by 1.05 m to 1.22 m EVRF2019 on 2023-06-08, a record for the station (T17e, T17f); no satellite scene on the day of the reconstructed areal maximum; the date-only gauge against 11:00 UTC SWOT passes; weak labels whose positives are a persistence product;
W_pre circularity of U2b; frame B3 (delta with the liman) not built; no probability-sample reference for any area; literature figures verified against the source texts where these were available (the UNOSAT product sheets behind the ~620 km² of cumulative flooded land over 6–9 June and the ~180 km² of flooded land on 13 June, reference water separate, were not obtained; those two figures are quoted as cited by OCHA and by Yailymov et al. 2025); the Inhulets backwater constrained by its own SWOT nodes only in the lower ~10 km of the valley; the reservoir balance rests on three to four level points and a DEM hypsometry below the design table; the
design-curve reading assumes a level pool and, before the breach, holds the last SWOT outlet value between passes; the
Sentinel-1 dark surface over the drained bed is not a water area (no source separates wet sediment from water in C-band);
the deterministic nominal new area and volume lie below their Monte-Carlo p05 on the days of the areal maximum, an effect of the terrain perturbation acting through the pre-breach regime (T11d); the
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
DOI to be minted from the release); interactive dashboard: https://floodstate-eo.streamlit.app. The full Monte-Carlo draw tables
are release assets (checksums in `tables/p95e_draws_checksums.csv`). Processed rasters (≈ 100 GB) are documented in `docs/REPRODUCIBILITY.md` (three levels);
FABDEM-derived rasters are not redistributed (CC BY-NC-SA 4.0). SWOT (PO.DAAC), ICESat-2 (NSIDC), Sentinel (Copernicus) and
WorldCover (ESA) are open archives; gauge data from the UkrHMC yearbooks as in Paper 1.

## References

`docs/references.bib`; entries added for this paper carry `note = {VERIFY}` until checked (`references_to_verify.md`).
