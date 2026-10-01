# Daily inundation after the Kakhovka dam breach reconstructed from the observed water surface and terrain: propagated uncertainty, independent checks against withheld gauges, Sentinel-1 and ICESat-2, and weak-label machine learning as a diagnostic

**Manuscript draft (Paper 3 of the Kakhovka series), generated from `manuscript_template.md` by `workflows/paper/fill_manuscript.py`.
Rewritten in one pass on 2026-09-29 after the scientific and code review of 2026-09-28; the changes (old / new / reason / effect on
the conclusions) are listed in table T28. Every number below is resolved from a committed publication table cell
(`publication/tables/T*.csv`, manifest with sha256); claim identifiers [C01]–[C14] refer to `evidence_matrix.csv`; terms are frozen
in `TERMINOLOGY.md`. Figure and table identifiers are internal and are renumbered at typesetting. Numbers are printed from the
table cells at the stated precision with round-half-to-even; the cell keeps the full value.**

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

The most direct observation of this flood is the water surface itself. Lehnigk et al. (2026) show with the daily SWOT water-surface elevations of the one-day calibration orbit — the data we use here — that two-dimensional outburst-flood simulations underestimate the observed peak stages by 1.4 to 6.1 m and misplace their timing unless reservoir and channel bathymetry are corrected, and even then reproduce neither stage nor timing fully; downstream stages reached 10–11 m by 8 June. Their question is whether a hydraulic model reproduces the observed stages. Ours is the converse: once the water surface is constrained by observations, what extent, depth and volume does it imply on every day, how unique is that answer, and where do the satellite flood masks and such a reconstruction disagree, and why? Terrain-based approaches that project a water surface or a mapped extent on a DEM — HAND (Rennó et al. 2008; Nobre et al. 2011), GeoFlood (Zheng et al. 2018), FwDET (Cohen et al. 2019) — are first-order products, not hydrodynamics: Johnson et al. (2019) find that a HAND-based method "does not accurately capture inundated cells" while it does highlight regions at risk. The static terrain-connectivity operator is established as well: c-HAND floods the cells whose elevation "is lower than the gage elevation" and which "are connected to the ocean" under "a static equilibrium assumption" (Wang et al. 2024), and flood-fill models retain terrain cells below an imposed water surface only when they are connected to the reference water network (Dale et al. 2026). The operator is therefore not our contribution. What this paper adds is its use with a spatially distributed, observation-constrained water surface H(x, y, t) from SWOT nodes and a gauge; a same-rule pre-breach baseline that separates new inundation from water that was already there; an uncertainty propagated through coherent realizations of the terrain and the water surface; and tests against gauges withheld from the reconstruction. Depth and extent from such a construction are sensitive to small vertical errors on low-relief floodplains, and because DEM error is spatially autocorrelated whereas accuracy statistics such as RMSE "assume error to [be] aspatial" (Hawker et al. 2018), it must be propagated with spatially correlated error realisations (Darnell et al. 2008; Le et al. 2026), not with independent noise.

Two well-known properties of satellite flood mapping make an independent reconstruction necessary. The area obtained by counting classified pixels is a *mapped* area, not an unbiased estimate of the true flooded area; the good-practice framework of Olofsson et al. (2014) requires an accuracy assessment "based on a sample of higher quality" reference data, which does not exist for this event. And a C-band dark-water rule does not see water under trees, between buildings or under emergent reeds: the backscatter of vegetated and urban targets with and without flood water "represents the biggest challenge for inundation detection" (Grimaldi et al. 2020), flood water under vegetation "could not be detected with the C-band Sentinel-1 SAR" in a paddy landscape (Singha et al. 2020), and detection beneath vegetation and in cities is "not yet satisfactory" (Shen et al. 2019; review of flooded vegetation in SAR: Tsyganskaya et al. 2018). Conversely, "smooth surfaces at the scale of the measuring wavelength and shadowed areas share almost identical scattering properties with water surfaces" (Shen et al. 2019) and sand returns backscatter as low as open water (Martinis et al. 2018), so smooth non-water surfaces and radar shadow can look like water; exclusion maps derived from SAR time series formalise where flood cannot be inferred from intensity (Zhao et al. 2021). A U-Net trained on labels derived from those masks inherits both limits (Maiti et al. 2022; weak supervision for flood mapping: He et al. 2024); its accuracy against such labels is agreement, not truth, and an input that also builds the label is label leakage (Apicella et al. 2025).

We therefore structure the study as a hierarchy of evidence (Fig02) and report the results in the same order. (1) The **observation-constrained terrain-connectivity reconstruction** of the daily inundation — extent, depth and volume below the dam, and the drawdown of the reservoir above it — is the main axis; it is a daily reconstructed series, not a hydrodynamic model. (2) Its **uncertainty**: coherent Monte-Carlo worlds, the observational support of the water surface and the structural choices that lie outside the budget. (3) **Independent validation and support**: two gauges withheld from the reconstruction, Sentinel-1 per acquisition date with the disagreement explained by the surface context (RF20 land-cover classes, WorldCover, elevation above the surface), night ICESat-2 ground heights and the SWOT–gauge comparison of the input. (4) **Weak-label machine-learning diagnostics**: what U-Net arms trained on the canonical weak-label ontology learn, with three training seeds as the minimum unit of evidence. A lower level explains or diagnoses a higher one; it never overrides it. Three principles hold throughout: model numbers are agreement with weak reference labels, never flood-mapping accuracy; "not observed is not dry"; and every area carries its semantics — observed by Sentinel-1, mapped by the U-Net, reconstructed from terrain, or reported in the literature.

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

- **SWOT** L2_HR_RiverSP v2.0 nodes on the one-day calibration orbit (Biancamaria et al. 2016), 26 May–10 July 2023, 42 days, 732 nodes/day median;
  node_q ≤ 1 and dark fraction < 0.5 as in Paper 1. Published comparisons place SWOT river heights at the centimetre-to-decimetre level against gauges and altimetric references (RMSE 0.02 m against Hydroweb-next on the Congo, Normandin et al. 2024; a global river error below 0.15 m, Yu et al. 2024), which is why the product's own node uncertainty wse_u (median 0.092 m here) is used as the per-node term of the Monte-Carlo (§3.4).
- **River gauges** of the 2023 yearbooks, daily, in the EVRF2019 frame of Paper 1: **Kherson 80805** (the input and anchor of the
  water surface; river-yearbook values through the recorder failure of 6 June – 8 July, as in Paper 1) and, withheld from the
  reconstruction as validation sites, **Inhulets – Kalynivske 80575** and **Southern Bug – Mykolaiv 98027** (the liman) (§3.6).
- **Seamless terrain–bed elevation model** (Paper 2): the kriged bathymetric bed inside the pre-breach water polygons and FABDEM v1.2 elsewhere — a bare-earth DTM derived from the Copernicus DEM with buildings and forests removed by machine learning (Hawker et al. 2022; residual mean absolute errors of 1.1–1.6 m remain in built-up areas, Iqbal et al. 2023) — on one 20 m grid in EVRF2019, with a source mask that records which cells are FABDEM and which are bed; the reconstruction refuses an input that does not declare its vertical frame (§3.2). HAND from the p42 workflow (FABDEM floored at the 1 m river level, WhiteboxTools) enters a rule sensitivity and one U-Net arm.
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
or drainage — is reported as a sensitivity and never as the primary (D-MEMORY; §4.2.4, T11p). Two other rules bracket it: the p42 rule (additionally HAND < WSE − 1 m, channel-connected through the mapped drainage; more restrictive, because the delta drainage is incompletely mapped) and the ceiling without connectivity. The connectivity requirement is not inherited from the terrain-index methods we build on: HAND-type methods "do not preserve hydraulic connectivity (i.e., floodplain cells lower than the channel water height are denoted as flooded whether or not there is a physical flow path to them)" (Bates 2022), and GeoFlood by design flags "local depressions such as ponds or waterbodies … even if they are not connected with the main stem river" (Zheng et al. 2018). Enforcing connectivity by connected-components analysis, as in coastal bathtub mapping (Kulp and Strauss 2019), is what turns the ceiling into a physically admissible extent; small channels that the 20 m grid does not resolve are a known control on floodplain connectivity (Neal et al. 2012), and in flat terrain the inferred flow path can differ from the real one (Guo et al. 2025) — the two reasons the rules are reported side by side rather than as one answer. The
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
their own category, because a Sentinel-1 dark-water onset there is a depth signal — the reeds are submerged — not the onset of inundation: in flooded vegetation the double bounce raises C-band backscatter above the non-flooded level, but once the water rises over the plants the signal turns dark (Grimaldi et al. 2020; Jarrett et al. 2023; review: Tsyganskaya et al. 2018), so the date on which a reed bed goes dark is the date its canopy went under, not the date water arrived. With the terrain as delivered (no residual bias removed) those reed beds sit above the normal surface and count as new inundation; we report
that run as a sensitivity (T12) and the two quantities — new inundation and wetland submergence — separately.

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

On each Sentinel-1 date the reconstruction is compared with the S1 new dark water (mask minus water on 1–2 June) on the S1
valid footprint, the owned zone area and outside the cut rectangles: hits, misses, terrain-only cells, POD, FAR and CSI (contingency-table measures, Schaefer 1990; raw agreement, primary, T13) — reported per date and per domain because binary pattern measures depend on the size of the flood and of the domain over which they are computed (Stephens et al. 2014); the *conditional POD outside the normally-wet class* — POD on the observable dry-background
domain, with the class fixed before any comparison was read — is a diagnostic conditional agreement, not a corrected POD. The
disagreement is decomposed into A (both), B (terrain only) and C (S1 only), by WorldCover and RF20 class and by ground elevation
relative to the reconstructed surface (< 0, 0–2, 2–5, ≥ 5 m; T14).

Night ICESat-2 ATL08 ground segments (Paper 2 chain) sampled on the 9 June categories (inside the S1 valid footprint only) give,
per category, the residual terrain − ICESat-2 on the FABDEM cells, as delivered and after the class-bias correction, and the
share of segments whose ground lies below the reconstructed surface (T15): an altimetric consistency check of the terrain and the
surface along tracks, not a validation of the inundation map. Because the same night corpus calibrates the class bias, the
corrected residual is also computed with the bias re-estimated without the passes being checked (a pass is one acquisition day;
one pass left out, five folds of whole passes, and the two epochs either side of the breach; T15b, T15c).

### 3.7 Surface context: RF20

A random forest (Breiman 2001; for its use in land-cover mapping see Belgiu and Drăguţ 2016) on PRE-event Sentinel-2 composite
predictors, trained on ESA WorldCover 2021 with a purity filter, classifies the surface at 20 m into water, cropland,
grass/low vegetation, forest, wetland/reed, built-up, bare sand and uncertain (p73). The 5 km cross-validation blocks are defined
from the map coordinates of the 20 m cells, so a physical cell lies in one block in both frames; where the frames overlap only B2
contributes training cells, so a physical cell enters the sample once; the cross-validation is repeated with a 3.5 km buffer
around the test blocks, and the frame transfers B1↔B2 are trained and tested outside the overlap. Per-class precision, recall and
F1 are agreement with the training reference (T09, T10), not validation. The classifier supplies the classes of the disagreement
ontology, the evaluation strata of the U-Net arms and the input of arm U1.

### 3.8 Weak labels and the U-Net diagnostics

*The optical component.* The weak labels combine Sentinel-1 persistence with an optical second opinion, M2: a random forest on
Sentinel-2 composite features trained on the Sentinel-1-derived weak labels of p60 — so it is not independent of Sentinel-1. Its
operating threshold T50 is the median of the five outer-fold thresholds of a nested spatial cross-validation on 5 km blocks for a
target recall of 0.90, calibrated on inner out-of-fold scores (fit and calibration cells disjoint, whole blocks), and an envelope
of more permissive fold thresholds marks weaker optical support (T02c). The canonical M2 uses the 67 features of the PRE and EVENT
windows and none from the post-event TRACE window. The M2 score is not interpreted as a flood probability.

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
decisions whose two class probabilities are close to equal (Bauer-Marschallinger et al. 2022; Roth et al. 2025).
Every version remains a weak label: v004 is the most consistent of the three, not a reference of higher quality, and agreement with it is not accuracy.

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

The liman gauge Mykolaiv (98027), also withheld, tests the western end of the domain. The liman rose by
1.05 m to 1.22 m EVRF2019 on 2023-06-08, a record for the station, on the day of the Kherson peak stage.
The reconstructed western delta takes its surface from the westernmost SWOT node of the Dnipro, which has no observation from
2023-06-06 .. 2023-06-22 and is interpolated flat across the flood, so at the gauge the reconstruction misses
the rise (-0.82 m on 2023-06-08 in absolute terms; T17e, T17f, FigS15). SWOT itself saw the liman: Paper 1 tracks the
post day by day with Southern Bug nodes (r = 0.987 over the event, 22 passes), which lie outside the Dnipro domain of this
reconstruction. The two withheld gauges expose two different structural limits — the propagation time of the tributary backwater
at Kalynivske and the sampling of the water surface in the western delta at Mykolaiv — which a single error statistic would
average away.

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
of this flood do not reproduce the observed stages and their timing without corrected bathymetry; here the stages come from the
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
Mykolaiv as the boundary that the western delta now lacks (§4.3.1). Such models of this event need corrected reservoir and channel
bathymetry before they reproduce the observed stages and their timing (Lehnigk et al. 2026), so they cannot replace the
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
not built; no probability-sample reference for any area; the UNOSAT product sheets behind the ~620 km² and ~180 km² figures were not
obtained (quoted as cited by OCHA and by Yailymov et al. 2025). The reservoir balance rests on three to four level points, an upper
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
