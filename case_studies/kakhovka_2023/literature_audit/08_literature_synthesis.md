# 08 — Literature synthesis, organised around the manuscript's questions

Written 2026-09-28 from the evidence rows of `02_thesis_evidence.csv` (every SUPPORTS/CONTRASTS statement below has a
verbatim quote verified against the corpus text; METHOD/COMPARATOR/BACKGROUND statements name the paper that was read)
and from the auditor's own reading of the Kakhovka papers (`kakhovka_numbers.csv`, `human_verified = yes`). For each
theme: what is established, where the literature disagrees, the closest comparable methods or results, how Paper 3
differs, and what the literature does **not** establish. Absent papers (07b) are named only as metadata-verified
citations, never as evidence.

Corpus searched: 5 027 normalized papers (146 mention Kakhovka; 82 in title/abstract); 97 atomic claims (54 theses: 51 from theses.csv + 3 supplementary for T23–T26); screening
statistics in `run_manifest.json`.

---

## A. What has been published about the Kakhovka flood (cluster A)

**Established.** The breach (6 June 2023, ~02:30 local by seismic records — Yi et al. 2025) drained the largest
reservoir of the Dnipro cascade: design volume 18.2 km³ at 16.0 m, 19.8 km³ at the 16.76 m held on 6 June (Vyshnevskyi
et al. 2023, from the operation rules), 21.0 km³ at 17.3 m by Yi et al.'s area–height relation. Downstream water-surface
elevations rose from 1.5 m (3 June) to 10–11 m by 8 June along the ~125 km SWOT reach, 5.6 m at Kherson on 8 June
(SWOT 5–5.3 m), and returned to within 10 % of pre-flood levels by ≈21 June; the pulse propagated ≥150 km up the
Inhulets (Lehnigk et al. 2026, read in full). Published extents are: ~620 km² of cumulative flooded land 6–9 June and
~180 km² on 13 June (UNOSAT, relayed by OCHA/CEOBS and cited by Yailymov et al. 2025, Kallas 2025, KhNU 2025);
473 km² of flooded land as of 9 June by land-cover class, 294 km² of it wetlands (Yailymov et al. 2025); a Sentinel-3
OLCI water-surface area that doubled within three days and was largest around 9 June (Zuo et al. 2024); HEC-RAS
scenario maxima of 823/874 km² (2-D, 300/600 m breach) and 681 km² (1-D, 8 June 16:00) with peaks of 36 000–48 000
m³ s⁻¹ (Kadam et al. 2024); a near-real-time Tygron model checked against ICEYE extents (Agerbeek et al. 2024).
Reservoir-side: an *initial* breach flow of (5.7 ± 0.8)×10⁴ m³ s⁻¹ and 20.4 ± 1.4 km³ lost in 30 days (Yi et al. 2025);
about 16.4 km³ released over two weeks (Shumilova et al. 2025, accepted manuscript adn8655 in the corpus); "∼8 km³"
cited from a news source and 14.5 km³ from a GLOBathy-based simulation (Lehnigk et al. 2026); about 7.5 km³ (Monti et
al. 2024); 655.9 km² of reservoir water surface remaining on 17 June and ~430 km² after two months (Novitskyi et al.
2024); 1 944 km² of bed exposed (Shumilova et al. 2025).

**Disagreement.** The released volume ranges from ~8 to 20.4 km³ across sources because the periods (event / two weeks /
30 days), the hypsometries (design table, operation rules, satellite area–height relations, GLOBathy) and the
definitions (released vs lost vs passed to the sea) differ. Downstream extents range from 405 to 823 km² for the same
reason (AOI, date, cumulative vs snapshot, land vs total water, model vs observation). No two published numbers are the
same quantity; none is a validation datum for another.

**Closest comparable methods/results.** Lehnigk et al. (2026) are the only published use of the daily SWOT water
surfaces of this event; they use them to *evaluate* 2-D outburst-flood simulations (GeoClaw) and find peak-stage
underestimates of 1.4–6.1 m and arrival-time errors of 3–142 h depending on bathymetry; they also use ICESat-2 ATL08 on
the exposed bed (median offsets 8.6 / 6.1 m for two bathymetries). Agerbeek et al. (2024) and Kadam et al. (2024) are
model-based daily extents. Zuo et al. (2024) is the only published *observed* near-daily series (300 m OLCI + SWOT WSE
plots), without terrain projection.

**How Paper 3 differs.** It projects the observed water surface (SWOT nodes + gauge) on a bias-corrected terrain with a
connectivity rule, solving no flow equations, and reports every day with a primary Monte-Carlo interval; it separates
total water surface, newly inundated area, wetland submergence, snapshot S1 dark water and persistent weak-label flood,
which none of the Kakhovka papers does (keyword screen NQ3: 6 of 82 title/abstract papers hit ≥3 of the 4 vocabularies,
none on reading separates the quantities).

**What the literature does not establish.** The day of the areal maximum (Zuo: "around 9 June" at 300 m; Lehnigk:
stage maxima by 8 June; neither resolves an areal maximum at daily resolution); the pre-breach volume to better than
±10 %; the UNOSAT product semantics beyond what OCHA relayed (product sheets not obtained, 07b).

## B. Terrain-based inundation, connectivity and DEM uncertainty (cluster B)

**Established.** HAND is a terrain descriptor normalising elevation to the nearest drainage (Rennó et al. 2008; Nobre
et al. 2011 — DEFINITION quotes verified); HAND-based mapping "does not accurately capture inundated cells but is quite
capable of highlighting regions likely to be at risk" (Johnson et al. 2019, verified quote); FwDET "calculat[es] water
depth based solely on an inundation map with an associated DEM" (Cohen et al. 2019, verified); GeoFlood is "a
large-scale simplified flood model" tested against hydrodynamic and observed extents (Zheng et al. 2018; Tiber study
2022). DEM error is spatially autocorrelated and accuracy statistics that "assume error to [be] aspatial" understate its
effect on inundation (Hawker et al. 2018, verified); spatially correlated and uncorrelated error fields propagate
differently (Cunha et al. 2012, verified); vertical DEM error changes modelled extent and depth (Saksena & Merwade 2015;
Iqbal et al. 2023; Kabite 2017 — verified). Global DEMs carry a canopy bias on floodplains (Baugh et al. 2013; Yamazaki
et al. 2017, 2019; Luo et al. 2017 — verified), FABDEM removes buildings and forests with residual built-up errors of
1.1–1.6 m (Hawker et al. 2022; Iqbal et al. 2023 — verified), and ICESat/ICESat-2 is used for DEM assessment and
correction (Jarihani et al. 2015; Hawker et al. 2022 — verified).

**Disagreement / qualification found by the screen.** The manuscript's thesis that "FwDET, GeoFlood and HAND-based
tools impose drainage/stream connectivity" (TH-MET-03.C) is **contradicted**: HAND-type methods "do not preserve
hydraulic connectivity" (Bates 2022, Annu. Rev. Fluid Mech., verified) and GeoFlood flags depressions "even if they are
not connected with the main stem river" (Zheng et al. 2018, verified). Connectivity enforcement by connected-components
analysis is documented in coastal bathtub mapping (Kulp & Strauss 2019, verified) and subgrid channel connectivity is "a
strong control on the hydraulics of the floodplain" (Neal et al. 2012, verified); in flat terrain the inferred flow path
can differ from the real one (Guo et al. 2025, verified). The manuscript's connectivity rule is therefore an addition
to the index methods, not inherited from them (revision B-09).

**Closest comparable methods.** Connectivity-constrained bathtub mapping for sea-level rise (Kulp & Strauss 2019; the
Poulter & Halpin 2008 and Williams & Luck-Vogel 2020 papers named in the theses are not in the corpus); FwDET for depth
from an extent; GeoFlood/HAND for extent from a stage; DEM-simulation with correlated fields for uncertainty (Hawker
et al. 2018; Darnell et al. 2008 — the latter metadata-verified only).

**How Paper 3 differs.** The water surface is observed (SWOT + gauge) rather than a stage–discharge or model product;
the DEM is class-bias-corrected against ICESat-2 before projection; the correlated error field is propagated per day
with the normal regime rebuilt per draw; and the two bounding rules (HAND / ceiling) bracket the connected ceiling.

**Not established.** A published correlation length of DEM error (the 500 m used here has no corpus precedent — the
screen found no semivariogram range for FABDEM-class DEMs); the number of Monte-Carlo draws required for percentile
convergence (no corpus statement); any precedent for a same-rule pre-breach "normal regime" as the reference for new
inundation (the operational analogue is the reference-water layer of GFM/Martinis et al. 2022, which is not in the
corpus).

## C. What C-band SAR can and cannot see (cluster C)

**Established (verified quotes).** Backscatter interpretation in vegetated and urban areas "represents the biggest
challenge for inundation detection" (Grimaldi et al. 2020); flood water under vegetation "could not be detected with the
C-band Sentinel-1 SAR" (Singha et al. 2020); beneath-vegetation and urban detection are "not yet satisfactory" (Shen et
al. 2019); intensity methods "fail to detect certain flooded pixels in densely populated urban areas where backscatter
remains constant" (Zhao et al. 2025 review); in a flooded melaleuca forest "stable low backscatters (dark areas)
appeared … with no double-bounce effects" (Tuan et al. 2020). On the commission side, "smooth surfaces at the scale of
the measuring wavelength and shadowed areas share almost identical scattering properties with water" (Shen et al.
2019), sand returns backscatter "similar to open water" (Martinis et al. 2018), radar shadow "appear[s] in a dark tone
similar to floodwaters" (Mohsenifar et al. 2025), and impervious smooth surfaces are confused with water in cities (Islam
et al. 2022; Bekele et al. 2022). Exclusion masks are an operational answer (Amitrano et al. 2024; Wagner et al. 2020;
Zhao et al. 2021 — the last metadata-verified only).

**Disagreement.** The literature does not agree on whether C-band double bounce reliably marks flooded vegetation: the
review of Tsyganskaya et al. (2018) and the melaleuca case (Tuan et al. 2020) show both increased and decreased
backscatter depending on structure, density and water level; this is exactly the ambiguity behind the manuscript's
"submergence of normally-wet reed beds" category (TH-MET-05.B — the retained rows report both behaviours).

**How Paper 3 differs.** It does not classify the SAR better; it uses the terrain/water-surface reconstruction to say,
cell by cell, which S1 detections are topographically unsupported and which terrain-allowed cells the radar cannot see,
and it quantifies both (T14).

**Not established.** Any site-specific cause for the 54 km² of S1-only detections ≥5 m above the surface (the
mechanisms are documented; the attribution is not — CHECK D wording).

## D. Weak labels, label noise, leakage and spatial evaluation (cluster D)

**Established (verified quotes).** Flood segmentation models are routinely trained on weak labels — threshold
classifications of Sentinel-1/2 imagery (Sen1Floods11: "a weakly supervised training dataset using Sentinel-1 based
flood classifications as labels", Bonafilia et al. 2020; 4 370 tiles "not hand-labeled … which can serve as weakly
supervised" labels, Bai et al. 2021; Katiyar et al. 2021; Sharma et al. 2025 train "on weak flood labels generated from
concurrent optical imagery"); such a model "still ends up learning the label mistakes in those weak labels" (Garg et al.
2023); label-noise tolerance of CNNs depends on sample size and depth (Li et al. 2019). Training samples drawn from a
global land-cover product carry that product's errors (a WorldCover cropland layer "exhibits classification
uncertainties in small-scale regions", 2025 agricultural-flood study; Wang et al. 2022 integrate samples "automatically
derived from a global land cover product"). For evaluation, block cross-validation "can address" dependence structures
and, compared with random splits, models "consistently demonstrate larger errors" (Roberts et al. 2017); "the minimum
blocking distance should be the extent of autocorrelation in model residuals" (Roberts et al. 2017); spatial CV
"typically yields lower accuracy than random holdout splits due to spatial autocorrelation" (Silwal et al. 2026);
random forests "do not allow accounting for such dependence structures" (Roberts et al. 2017). Block bootstrapping is
used for confidence bounds under autocorrelation (Nature 2019 flood-trend study; McKeon et al. 2025). Target leakage is
recognised as a problem to be engineered against (CatBoost's ordered boosting "to overcome target leakage problems",
2025) — the definitional sources (Kaufman et al. 2012; Apicella et al. 2025) are not in the corpus.

**Disagreement / qualification.** What terrain does to a SAR flood product is design-specific: Tupas et al. (2023),
using HAND as a Bayesian prior, reduced false negatives "at the cost of slightly increasing false positives" — the
opposite trade-off to this paper's cropland result (HAND as an input channel reduces the unlabelled-cropland burden by
9.6 km²). A HAND-corrected surrogate cut false alarms in a forecasting setting (Silwal et al. 2026 review). The
reference-water definition also varies: JRC seasonality > 5 months (Sharma et al. 2025), a global permanent-water mask
(Martinis et al. 2015), a pre-flood optical map (Yailymov et al. 2025), recurrent May water on ≥ 3 dates (this paper).

**Closest comparable methods.** Sen1Floods11-style weak-label U-Nets evaluated on held-out *events* (Bonafilia et al.
2020; Katiyar et al. 2021); block CV in ecology and land-cover mapping (Roberts et al. 2017; Valavi et al. 2019 —
metadata only).

**How Paper 3 differs.** Two frozen label contracts on one frozen spatial-block split, paired block bootstrap over
identical blocks, and an explicit leakage diagnosis (U2b). Whole-corpus screen NQ5: **0 of 4 838** papers combine
weak/noisy flood labels with spatially blocked evaluation in their text; the closest are event-held-out Sen1Floods11
studies, which block by event rather than by space.

**Not established.** A published block-size rule for CNN patch models (Ploton 2020 / Karasiak 2022 absent); a label-noise
result specific to SAR flood masks (Maiti 2022 concerns aerial imagery; metadata-verified only).

## F. Agreement statistics and their limits

**Established (verified quotes).** POD/hit rate, FAR and CSI are contingency-table measures (definitions in Stephens
et al. 2014 citing Wilks; ADGEO 2017; WRR 2021; J. Hydrol. 2025 citing Schaefer 1990 — Schaefer 1990 itself verified in
07c); "binary pattern measures are not consistent for floods of different sizes, such that for the same vertical
error in water level, a model of a flood of large magnitude appears" to perform differently (Stephens et al. 2014), and
comparing observed and simulated flood areas "using traditional statistics can be" misleading (2025 review). Hence the
manuscript's per-date, per-domain reporting and the refusal to call the conditional POD a corrected accuracy.

**Disagreement.** Some evaluations use GSS/ETS or F-statistics instead of CSI (contingency-table variants), not a
contradiction. No paper in the corpus reports a *conditional* POD outside an a-priori class; the diagnostic is this
paper's own construction and is labelled as such.

**Not established.** Typical CSI values between terrain-based extents and single SAR masks for dam-break floods
(TH-RES-04.A found no directly comparable evaluation; Johnson 2019 and the GeoFlood Tiber study give HAND-vs-model
agreement, not HAND-vs-SAR).

## E. Revisit, temporal sampling and the maximum between acquisitions

**Established (verified quotes).** Sentinel-1's 6- and 12-day revisit intervals "are not sufficient to accurately
track flood progression over time" (DeVries et al. 2020); satellite temporal resolution "can be not sufficient to map
the maximum extension of the flood event when the evolution … covers a time span from some hours to a few days"
(Tarpanelli et al. 2022); acquisitions fall "some hour[s] before the flood peak" (Giordan et al. 2018); Sentinel-1
"cannot capture flood peaks due to the acquisition frequency" (Thammaboribal et al. 2025); with two constellations and
both orbit directions the share of European events potentially observed rises only to about 58 % for Sentinel-1
(Tarpanelli et al. 2022). Constellations and daily-revisit optical sensors raise the probability of co-flood data
(Notti et al. 2018; Giordan et al. 2018; Tarpanelli et al. 2022).

**Closest precedent for the maximum between two images.** InSAR coherence "acts as a sort of persistent change
detector, registering the maximum extent of inundation" between acquisitions (Refice et al. 2017) — where water passed,
not when or how deep. Whole-corpus screen NQ2: 3 of 4 838 papers co-locate a "between acquisitions" phrase with a
maximum-extent phrase; only Refice et al. is a method.

**How Paper 3 differs.** The maximum is reconstructed from the observed daily water surface and terrain, with depth and
volume, and is reported as reconstructed with its interval and the statement that its day is interpolation-dependent.

**Not established.** That the areal maximum of this event fell on 7 June (no observation), or the stage–extent lag on
this reach.

## F. Agreement statistics and their limits

[Stephens et al. 2014 and Bates & De Roo 2000 are in the corpus and were added as expert-named pairs; completed after
screening of TH-MET-08]

## G. SWOT, ICESat-2 and gauge data as inputs and checks

**Established (verified).** SWOT RiverSP nodes and reaches are defined on SWORD (Normandin et al. 2024; Beltrão et al.
2025 review; Ishikawa et al. 2026 use SWORD v17); SWOT river heights agree with references at the centimetre-to-
decimetre level (RMSE 0.02 m vs Hydroweb-next on the Congo, Normandin et al. 2024; global river error < 0.15 m, Yu et
al. 2024; "a few centimeters to a few decimeters", Beltrão et al. 2025); SWOT elevation accuracy ≈10 cm in Lehnigk et
al. (2026, citing Fu et al. 2024). FABDEM and ATL08 as above (B). Radar altimetry has long been fused with gauges for
level and discharge series (Papa et al. 2010; Schwatke et al. 2015; Ekeu-Wei & Whittaker 2018 — verified).

**How Paper 3 differs.** The one-day orbit gives daily nodes through the event; the gauge enters as a node; the
comparison with the gauge is an input-consistency check (+0.01 m median) and the ICESat-2 comparison an altimetric
consistency check along tracks — neither is a validation of the map, and the literature offers no published example of
either on a flood of this kind.

**Not established.** ATL08 night accuracy over cropland/grass at this site (Neuenschwander & Pitts 2019 and Liu et al.
2021 are not in the corpus; the numbers used come from Paper 2's own class table).

## H. The drained reservoir: pool area and the bed (T23–T26, added 2026-09-28)

**Established (read in the corpus).** Pre-breach pool areas cluster at 2091–2155 km² (Magas et al. 2023 from Sentinel-2 on
5 June; Yi et al. 2025, 2125 km² on 30 May; design 2155 km²). Yi et al. describe the shrinkage as ~280, ~1000 and ~460 km² over
6–10, 11–20 and 21–30 June from Sentinel-1 SDWI and Sentinel-2 mNDWI maps. The bed was recolonised within months: vascular
plant taxa rose about sevenfold from June to October 2023 (Kuzemko et al. 2024) and ~14-fold within the year (Kuzemko et al.
2025), with "very rapid overgrowth, primarily by willow" (Vyshnevskyi 2024) and hybrid willow Salix × rubens (Tutova et al.
2025); Pichura and Potravka (2025) report 135 thousand ha of vegetated bed in 2023–2024 from Sentinel-2 indices.

**Disagreement.** Remnant water areas in late summer range from 1.63 km² of open water (Tsiupa et al. 2023) to 379.7 km²
including the restored channel (Magas et al. 2023) and ~430 km² (Novitskyi et al. 2024) — a definitional spread (open water,
wet, channel, lakes), not measurement error.

**How Paper 3 differs.** The pool is reconstructed daily under a sloped observed surface and compared with S1/S2 per date on
observed cells (IoU 0.98 → 0.85 by 13 June); the S1 excess on the exposed flats after ~13 June is flagged as non-water.

**Not established.** Wet reservoir sediment as a C-band water look-alike (no corpus source; the mechanism is documented only
for smooth bare soil and sand); a revegetation precedent outside Kakhovka.
