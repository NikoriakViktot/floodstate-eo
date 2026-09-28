# New in floodstate-eo, 2026-09-26. STATUS: ACTIVE. Theses of Paper 3 that need literature support, for a knowledge graph.
"""p100_literature_theses -- every statement of the manuscript that must be traced to a source (background, data, method,
result comparator, interpretation), with the candidate references already in docs/references.bib, their verification
status, what still has to be found, and ready-to-run search queries.

Outputs (publication/literature/):
  theses.json   list of thesis objects (graph-ready: nodes = Thesis / Reference / Section; edges in `relations`)
  theses.csv    one row per thesis (flat, for spreadsheets or a CSV loader)
  theses.md     human-readable table by section
  graph.graphml GraphML (yEd / Gephi / networkx) with the same nodes and edges
  graph.json    explicit node/edge lists (Thesis -[SUPPORTED_BY|COMPARATOR|METHOD_FROM|CONTRASTS_WITH|NEEDS_SOURCE]-> Reference)

Values quoted in the theses are the current numbers of the committed publication tables (T-ids given) -- they are
context for the search, the tables remain the source of truth.
"""
from __future__ import annotations
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "publication" / "literature"
BIB = ROOT.parents[1] / "docs" / "references.bib"

# relation vocabulary
SUP, CMP, MTH, CON, NEED = "SUPPORTED_BY", "COMPARATOR", "METHOD_FROM", "CONTRASTS_WITH", "NEEDS_SOURCE"

T = []  # noqa: N816


def th(tid, section, category, thesis, needs, refs, queries, priority="medium", tables="", quantitative=""):
    """refs: list of (bib_key_or_placeholder, relation). A placeholder starts with '?' when no entry exists yet."""
    T.append(dict(id=tid, section=section, category=category, thesis=thesis, quantitative=quantitative, tables=tables,
                  needs=needs, refs=[dict(key=k, relation=r) for k, r in refs], search_queries=queries, priority=priority))


# ------------------------------------------------------------------ 1. Introduction / background
th("TH-INT-01", "1 Introduction", "background",
   "The breach of the Kakhovka dam on 6 June 2023 released the largest reservoir of the Dnipro cascade into a ~90 km reach with a densely populated left bank, a reed-wetland delta and the Dnipro-Buh liman.",
   "Confirm reach length, reservoir design volume (18.2 km3) and the descriptive facts against the two event papers.",
   [("Vyshnevskyi_2023", SUP), ("Shumilova_2025", SUP)],
   ["Kakhovka dam destruction 6 June 2023 consequences reservoir volume", "Kakhovka reservoir design full-pool volume 18.2 km3 area 2155 km2"], "high")
th("TH-INT-02", "1 Introduction", "comparator",
   "Operational products reported the flooded area within days: UNOSAT ~620 km2 of cumulative satellite-detected flooded land for 6-9 June and ~180 km2 on 13 June; NASA Harvest ~410-420 km2 on 7 June. These are flooded-land figures with their own AOI, dates and reference water.",
   "Product sheets (UNOSAT product ids, sensors, reference-water definition, AOI); the NASA Harvest / Planet note; any other published extent with its definition.",
   [("UNOSAT_3616_2023", CMP), ("UNOSAT_3623_2023", CMP), ("CEOBS_2023", CMP), ("REACH_2023", CMP), ("?NASA_Harvest_2023", NEED)],
   ["UNOSAT Kakhovka satellite detected flood water extent 9 June 2023 product", "NASA Harvest Kakhovka dam flooded area 7 June 2023 Planet", "Kakhovka flood extent km2 satellite estimate comparison 2023"], "high", "T16")
th("TH-INT-03", "1 Introduction", "background",
   "SWOT, on its one-day calibration orbit, observed the reach daily through the event; with those data Lehnigk et al. (2026) show that 2-D outburst-flood simulations miss the observed stage and timing unless the bathymetry is corrected, and underestimate the peak stage even then (best bathymetry ~1.4 m low, others 5.8-6.1 m); downstream peak stages of 10-11 m were reached by 8 June.",
   "Read the paper: exact numbers quoted (stage errors, 8 June timing, Kherson 5.6 m), how ATL08 on the exposed bed was used, what was mapped from SWOT.",
   [("Lehnigk_2026", SUP), ("Biancamaria_2016", SUP)],
   ["SWOT calibration orbit 1-day repeat 2023 water surface elevation Kakhovka", "Lehnigk Pavelsky Lang SWOT Kakhovka outburst flood model bathymetry"], "high")
th("TH-INT-04", "1 Introduction", "comparator",
   "Independent reconstructions of the reservoir drainage exist: Yi et al. (2025) derive an initial breach flow of 5.7 +- 0.8 x 10^4 m3/s, a 12.6 +- 1.1 m level drop and 20.4 +- 1.4 km3 lost in 30 days from altimetry, SAR/optical and gravimetry; Kadam et al. (2024) simulate a 300 m breach with HEC-RAS (35 962 m3/s, 823 km2).",
   "Verify every quoted value in the two papers; note that 'initial breach discharge' and 'scenario peak' are different quantities from our daily-mean effective release.",
   [("Yi_2025", CMP), ("Kadam_2024", CMP)],
   ["Kakhovka dam breach discharge estimate m3/s satellite", "Kakhovka breach HEC-RAS 2D simulation flood extent km2"], "high", "T21")
th("TH-INT-05", "1 Introduction", "method",
   "A pixel-counted area from a classified map is a mapped area, not an unbiased estimate of the true flooded area; good practice requires a probability-sample reference that does not exist here, so every area carries its semantics (observed_S1 / mapped_UNet / terrain_reconstructed / literature_reported).",
   "Olofsson et al. 2014 (add DOI 10.1016/j.rse.2014.02.015); a flood-specific accuracy-assessment paper using stratified sampling would strengthen it.",
   [("Olofsson_2014", SUP), ("?flood_area_estimation_probability_sample", NEED)],
   ["Olofsson 2014 good practices estimating area and assessing accuracy land change", "flood extent area estimation stratified random sample unbiased area SAR"], "high", "T16")
th("TH-INT-06", "1 Introduction", "method",
   "A C-band dark-water rule does not see water under trees, between buildings or under emergent reeds (SAR blind spots), and smooth non-water surfaces or radar shadow can look like water (look-alikes); exclusion maps formalise where flood cannot be inferred from intensity.",
   "Exact statements in Zhao 2021 (exclusion-map classes), Shen 2019 (false positives), Grimaldi 2020 (vegetation); a review on flooded-vegetation detection (Tsyganskaya 2018) and on look-alikes (Martinis) would complete it.",
   [("Zhao_2021", SUP), ("Shen_2019", SUP), ("Grimaldi_2020", SUP), ("?Tsyganskaya_2018", NEED), ("?Martinis_lookalikes", NEED)],
   ["SAR flood mapping look-alikes smooth surfaces radar shadow sand false positives", "Tsyganskaya 2018 SAR-based detection of flooded vegetation review", "C-band Sentinel-1 flooded vegetation double bounce detection limits"], "high", "T14")
th("TH-INT-07", "1 Introduction", "method",
   "A U-Net trained on labels derived from SAR masks inherits the sensor's limits; label noise changes segmentation metrics; its accuracy against such labels is agreement with weak labels, not truth.",
   "Maiti 2022 (label-noise effects), He 2024 (weak supervision for flood mapping); one more general label-noise survey in RS (e.g. Burgert/ Sumbul) would help.",
   [("Maiti_2022", SUP), ("He_2024", SUP), ("Bonafilia_2020", SUP), ("?label_noise_RS_survey", NEED)],
   ["label noise semantic segmentation remote sensing effect deep learning", "weakly supervised flood mapping SAR U-Net noisy labels Sen1Floods11"], "medium", "T05")
th("TH-INT-08", "1 Introduction", "method",
   "An input that also builds the label is label leakage: the comparison of such a model is not independent (the U2b / W_pre case).",
   "Apicella et al. 2025 (add article number/DOI); Kaufman et al. 2012 'Leakage in data mining' as the classic reference.",
   [("Apicella_2025", SUP), ("?Kaufman_2012", NEED)],
   ["Kaufman Rosset Perlich leakage in data mining formulation detection avoidance", "target leakage feature derived from label machine learning evaluation"], "medium")
th("TH-INT-09", "1 Introduction", "method",
   "Terrain-based inundation methods (HAND; GeoFlood; FwDET) that project a water surface or a mapped extent on a DEM are first-order products, not hydrodynamics; HAND has known limits.",
   "DOIs for Renno 2008, Nobre 2011, Johnson 2019; exact framing of GeoFlood/FwDET as simplified approaches.",
   [("Renno_2008", MTH), ("Nobre_2011", MTH), ("Johnson_2019", SUP), ("Zheng_2018", MTH), ("Cohen_2019", MTH)],
   ["HAND height above nearest drainage flood inundation mapping limitations", "GeoFlood terrain analysis inundation mapping simplified vs hydrodynamic", "FwDET floodwater depth estimation tool DEM limitations"], "high")
th("TH-INT-10", "1 Introduction", "method",
   "On low-relief floodplains small vertical DEM errors strongly change depth and extent; spatially correlated error realisations are the correct way to propagate them.",
   "Darnell 2008, Le 2026; a DEM-uncertainty review (Wechsler 2007) and Hawker 2018 'perspectives on DEM simulation for flood modeling'.",
   [("Darnell_2008", SUP), ("Le_2026", SUP), ("?Wechsler_2007", NEED), ("?Hawker_2018", NEED)],
   ["Wechsler 2007 uncertainties associated with digital elevation models for hydrologic applications", "Hawker 2018 perspectives on DEM simulation flood modeling absence of high-accuracy global DEM", "spatially correlated DEM error Monte Carlo flood extent uncertainty"], "high", "T11b")
th("TH-INT-11", "1 Introduction", "background",
   "Series conventions inherited from Paper 1: satellite heights are EGG2015-referenced heights shifted by the empirical local closure residual into the gauge-anchored EVRF2019 frame; the residual sign is gauge - satellite; one overpass or one day is the independent unit.",
   "Paper 1 draft (internal); EGG2015 quasigeoid reference (Denker 2015); EVRF2019 definition (BKG).",
   [("Paper1_Nikoriak_2026", SUP), ("?Denker_2015_EGG2015", NEED), ("?EVRF2019_BKG", NEED)],
   ["European Gravimetric Quasigeoid EGG2015 Denker", "EVRF2019 European Vertical Reference Frame realisation BKG"], "medium")

# ------------------------------------------------------------------ 2. Data
th("TH-DAT-01", "2 Data", "data",
   "Sentinel-1 GRD/RTC scenes (11 acquisitions 1-30 June, orbits 14/65/87/138) classified with a per-scene dark-water rule (Lee/Lopes speckle filter, Otsu threshold); orbit-matched dB change channels are the U-Net inputs; 13 April-May scenes define recurrent reference water.",
   "References for RTC/terrain flattening (SNAP; Small 2011), Otsu 1979, Lopes 1990 (DOIs), change-detection flood mapping (Twele 2016; Martinis 2015) and reference-water/seasonal water (Martinis 2022; Wagner 2026 GFM).",
   [("Lopes_1990", MTH), ("Otsu_1979", MTH), ("Twele_2016", MTH), ("Martinis_2022", MTH), ("Wagner_2026", MTH), ("?Small_2011_RTC", NEED)],
   ["Sentinel-1 radiometric terrain correction Small 2011 flattening gamma", "Sentinel-1 change detection flood mapping Otsu threshold automatic Twele 2016", "reference water mask seasonal water Sentinel-1 flood exclusion Martinis"], "medium", "T01, T19")
th("TH-DAT-02", "2 Data", "data",
   "Sentinel-2 L2A index stacks per date (NDWI, MNDWI, NDVI, NDMI, BSI, AWEIsh, NDTI) with the water rule NDWI > 0 and MNDWI > 0; PRE/EVENT/TRACE composites.",
   "McFeeters 1996, Xu 2006 (DOIs); AWEI (Feyisa 2014); BSI/NDTI sources.",
   [("McFeeters_1996", MTH), ("Xu_2006", MTH), ("?Feyisa_2014_AWEI", NEED)],
   ["Feyisa 2014 automated water extraction index AWEI Landsat", "NDWI MNDWI water rule Sentinel-2 threshold zero flood"], "low", "T01")
th("TH-DAT-03", "2 Data", "data",
   "SWOT L2_HR_RiverSP v2.0 nodes on the one-day calibration orbit, 26 May-10 July 2023, filtered by node_q <= 1 and dark fraction < 0.5; SWORD v16 defines the nodes; node wse_u is the per-node uncertainty used in the Monte-Carlo.",
   "Product citation with CRID; SWORD (Altenau 2021 DOI); SWOT river-height validation papers (cal/val 2024-2025) to justify wse_u and the quality flags.",
   [("SWOT_RiverSP_v2", SUP), ("Altenau_2021", SUP), ("Biancamaria_2016", SUP), ("?SWOT_RiverSP_validation_2024", NEED)],
   ["SWOT L2_HR_RiverSP node water surface elevation validation gauges 2024 calibration orbit", "SWORD river database Altenau 2021 nodes reaches", "SWOT node_q quality flag dark water fraction RiverSP"], "high", "T01, T17")
th("TH-DAT-04", "2 Data", "data",
   "Kherson gauge 80805, daily river-yearbook stages, BS-77 -> EVRF2019 by the official EPSG:9902 transformation (+0.216 m at the post); 6-12 June are flagged in the sea yearbook (recorder failure) so the river yearbook is used.",
   "EPSG:9902 registry entry / Ukrainian geodetic regulation for the BS-77 to EVRF2019 offset; the UkrHMC yearbook citation form.",
   [("Paper1_Nikoriak_2026", SUP), ("?EPSG_9902", NEED), ("?UkrHMC_yearbook_2023", NEED)],
   ["EPSG 9902 Baltic 1977 height to EVRF2019 Ukraine transformation", "Ukrainian Hydrometeorological Center river yearbook Kherson gauge Dnipro 2023"], "medium")
th("TH-DAT-05", "2 Data", "data",
   "The seamless DEM (Paper 2) merges a kriged bathymetric bed inside the pre-breach water polygons with FABDEM v1.2 elsewhere (EVRF2019, 20 m); night ICESat-2 ATL08 ground segments (2019-2025) give its accuracy by land-cover class (RMSE 1.04 m, NMAD 0.39 m; trees the worst class, +1.5-2 m residual).",
   "FABDEM accuracy under forest/buildings (Hawker 2022 numbers); ATL08 ground-height accuracy literature (Neuenschwander 2019/2020; Liu 2021); vegetation bias of global DEMs (Kulp & Strauss 2018 CoastalDEM; Zhao 2018).",
   [("Hawker_2022", SUP), ("Neuenschwander_2019", SUP), ("Paper2_Nikoriak_2026", SUP), ("?Liu_2021_ATL08", NEED), ("?Kulp_Strauss_2018", NEED)],
   ["FABDEM accuracy forest removal residual bias ICESat-2 validation", "ICESat-2 ATL08 terrain height accuracy night vegetation Liu 2021", "global DEM vegetation bias correction coastal floodplain CoastalDEM"], "high", "T18")
th("TH-DAT-06", "2 Data", "data",
   "HAND is computed from FABDEM floored at the 1 m river level with WhiteboxTools (p42 workflow).",
   "WhiteboxTools citation (Lindsay 2016 DOI or the software DOI).",
   [("Lindsay_2016", MTH)], ["WhiteboxTools Lindsay elevation above stream HAND algorithm citation"], "low")
th("TH-DAT-07", "2 Data", "data",
   "ESA WorldCover 2021 (10 m) is the training reference of the RF20 surface classes and the classes of the disagreement ontology; its comparison with RF20 is agreement, not validation.",
   "WorldCover 2021 v200 product and its validation report (OA ~76.7 % global) to bound what 'agreement with WorldCover' means.",
   [("Zanaga_2022", SUP), ("?WorldCover_validation_report", NEED)],
   ["ESA WorldCover 2021 v200 validation report overall accuracy", "WorldCover 10 m land cover accuracy wetland built-up class"], "medium", "T09")

# ------------------------------------------------------------------ 3. Methods
th("TH-MET-01", "3.1 Water surface", "method",
   "The daily water surface is built without chainage: each cell takes the median height of its five nearest SWOT nodes within 3 km on the day, nodes are interpolated in time between their own observations, the gauge enters as one more node, and cells farther than 15 km from any node west of the gauge are capped at the gauge level.",
   "Precedents for node-based / gauge-fused water-surface interpolation from SWOT or altimetry (e.g. SWOT-derived water-surface slopes, gauge-altimetry fusion, 'water surface elevation interpolation floodplain'); the SWORD chainage caveat across branches.",
   [("Lehnigk_2026", MTH), ("Paper1_Nikoriak_2026", MTH), ("?WSE_interpolation_precedent", NEED)],
   ["water surface elevation interpolation from satellite altimetry nodes floodplain inundation", "SWOT river node interpolation water surface slope flood", "gauge and satellite altimetry fusion water level time series interpolation"], "high", "T11, T17")
th("TH-MET-02", "3.1 Water surface", "method",
   "The Kherson-local closure residual is ~0 (+0.9 cm RiverSP, -2.6 cm PIXC pre-breach; +1.9 cm through the breach fortnight; NMAD 4-5 cm), so c = 0 with sigma 0.05 m; an earlier chain that applied the mean reservoir closure (-0.173 m) plus a permanent-tide term is a superseded sensitivity.",
   "Paper 1 numbers; a reference on local geoid/datum closure residuals for satellite-gauge comparisons; permanent-tide conventions (IERS).",
   [("Paper1_Nikoriak_2026", SUP), ("?permanent_tide_IERS", NEED)],
   ["satellite altimetry gauge datum closure residual local geoid offset river", "permanent tide system mean tide zero tide height conversion IERS conventions"], "medium", "T11, T17")
th("TH-MET-03", "3.2 Terrain rule", "method",
   "A cell is water on day t if its DEM lies below the water surface and it is 8-connected through such cells to the pre-breach optical water network, within 10 km of pre-breach water and downstream of the dam ('connected ceiling'); the p42 HAND rule (HAND < WSE - 1 m, channel-connected) is a lower bound and the ceiling without connectivity an upper variant.",
   "Precedents for connectivity-constrained 'bathtub' inundation (Poulter & Halpin 2008; Williams & Luck-Vogel 2020), FwDET/GeoFlood connectivity, and the known over-prediction of unconstrained planar surfaces.",
   [("Zheng_2018", MTH), ("Cohen_2019", MTH), ("Johnson_2019", SUP), ("?Poulter_Halpin_2008", NEED), ("?Williams_LuckVogel_2020", NEED)],
   ["bathtub inundation model hydrological connectivity eight-connected Poulter Halpin 2008", "connectivity constrained planar water surface inundation DEM overestimation", "Williams Luck-Vogel 2020 bathtub model connectivity coastal inundation comparison"], "high", "T11, T12")
th("TH-MET-04", "3.2 Terrain rule", "method",
   "The DEM enters after subtraction of its class-median residual against night ICESat-2 (trees +1.5-2 m, wetland ~+0.5 m, cropland ~0); with the DEM as delivered the delta reed beds sit above the normal surface and count as new inundation, so that run is a definitional sensitivity.",
   "Precedents for land-cover-stratified bias correction of DEMs with ICESat-2 (e.g. FABDEM, MERIT, CoastalDEM, 'ICESat-2 DEM correction random forest'), and the reed-bed canopy bias specifically.",
   [("Hawker_2022", MTH), ("Neuenschwander_2019", MTH), ("?ICESat2_DEM_bias_correction", NEED)],
   ["ICESat-2 ATL08 DEM bias correction land cover class stratified", "reed wetland canopy bias digital elevation model correction ICESat-2", "MERIT DEM vegetation bias removal ICESat GLAS"], "high", "T18")
th("TH-MET-05", "3.2 Terrain rule", "method",
   "The normal regime is the union of the same rule over the pre-breach days 26 May-5 June plus the observed pre-breach water; the reconstructed newly inundated area is water outside it; model-only normal cells ('normally wet' low reed beds) are kept as their own category because a SAR dark-water onset there is a submergence (depth) signal, not inundation onset.",
   "Reference-water definitions in operational products (GFM reference water, Martinis 2022 seasonal reference); flooded-vegetation submergence literature.",
   [("Martinis_2022", MTH), ("Wagner_2026", MTH), ("Grimaldi_2020", SUP), ("?Tsyganskaya_2018", NEED)],
   ["reference water layer definition flood mapping normal water extent Sentinel-1", "emergent vegetation submergence SAR backscatter drop water level rise reed"], "high", "T12, T13")
th("TH-MET-06", "3.3 Uncertainty", "method",
   "A 40-draw spatial Monte-Carlo propagates the closure (sigma 0.05 m), the date-only gauge (0.05 m), the SWOT node height (median wse_u), the per-node time interpolation (leave-one-out NMAD) and a spatially correlated (500 m) DEM error field with the class NMAD; the normal regime is rebuilt per draw; this is the primary interval.",
   "Correlated-field DEM error simulation (Darnell 2008; Wechsler 2007; Hawker 2018); the 500 m correlation length needs a semivariogram reference or our own estimate; number-of-draws justification (convergence).",
   [("Darnell_2008", MTH), ("Le_2026", SUP), ("?Wechsler_2007", NEED), ("?Hawker_2018", NEED), ("?Fisher_Tate_2006", NEED)],
   ["sequential Gaussian simulation DEM error correlation length flood inundation uncertainty", "Fisher Tate 2006 causes and consequences of error in digital elevation models", "number of Monte Carlo realisations DEM uncertainty convergence flood extent"], "high", "T11b, T12")
th("TH-MET-07", "3.3 Uncertainty", "method",
   "A cluster-normal emulator with 100 000 draws per day over the class-wise DEM and water-surface error parameters gives a broader sensitivity envelope of the area (a different distribution: parameter-space propagation); it is never the primary interval and its volume draws are not used.",
   "Precedents for emulators / surrogate propagation of DEM and stage uncertainty in flood mapping; if none fits, keep as our own construction with a clear statement.",
   [("?emulator_flood_uncertainty", NEED)],
   ["emulator surrogate model flood inundation uncertainty propagation DEM error stage", "analytical propagation DEM error flood area binomial cells correlated clusters"], "low", "T12")
th("TH-MET-08", "3.4 Checks", "method",
   "On each Sentinel-1 date the reconstruction is compared with the S1 new dark water on the S1 valid footprint (hits, misses, terrain-only): POD, FAR, CSI are the raw agreement; the conditional POD outside the a-priori normally-wet class is a diagnostic conditional agreement, not a corrected POD.",
   "Definitions of POD/FAR/CSI (Schaefer 1990; Wilks) and flood-map comparison metrics (Bates & De Roo 2000 F; Stephens 2014 on binary performance measures); precedent for conditional/stratified agreement.",
   [("?Schaefer_1990_CSI", NEED), ("?Bates_DeRoo_2000", NEED), ("?Stephens_2014", NEED)],
   ["critical success index threat score Schaefer 1990 definition", "flood inundation model performance binary measures F statistic Bates De Roo 2000", "Stephens Bates Freer 2014 problems with binary pattern measures flood"], "high", "T13")
th("TH-MET-09", "3.4 Checks", "method",
   "The disagreement is decomposed into A (both), B (terrain only), C (S1 only) by WorldCover and RF20 class and by ground elevation relative to the reconstructed surface (< 0, 0-2, 2-5, >= 5 m).",
   "Precedents that stratify flood-map disagreement by land cover / height above water (e.g. Landuyt 2019 S1 method comparison; GFM validation by land cover; Tarpanelli).",
   [("Zhao_2021", MTH), ("?Landuyt_2019", NEED), ("?GFM_validation_landcover", NEED)],
   ["Landuyt 2019 flood mapping based on synthetic aperture radar comparison methods Sentinel-1", "flood map disagreement stratified by land cover height above water surface", "Global Flood Monitoring validation land cover class Sentinel-1"], "medium", "T14")
th("TH-MET-10", "3.4 Checks", "method",
   "Night ICESat-2 ATL08 ground segments sampled on the 9 June disagreement categories give, per category, the residual DEM - ICESat-2 and the share of segments below the reconstructed surface: an altimetric consistency check along tracks, not a validation of the map.",
   "Lehnigk 2026 used ATL08 on the exposed reservoir bed (precedent on this very site); ATL08 night-vs-day accuracy; track-sampling limits.",
   [("Lehnigk_2026", MTH), ("Neuenschwander_2019", MTH), ("?Liu_2021_ATL08", NEED)],
   ["ICESat-2 ATL08 night acquisitions terrain accuracy vs day background noise", "ICESat-2 ground tracks sampling bias validation raster products"], "medium", "T15")
th("TH-MET-11", "3.5 RF20", "method",
   "A random forest on PRE-event Sentinel-2 composite predictors, trained on WorldCover 2021 with a purity filter, classifies the surface at 20 m (8 classes); spatial-block 5-fold CV and frame transfers B1<->B2 give agreement with the training reference, used as evaluation strata and ontology classes.",
   "RF for land cover (Belgiu & Dragut 2016); training on global LC products as labels (label purity filtering); spatial CV (Roberts 2017, Pohjankukka 2017, Valavi 2019).",
   [("Roberts_2017", MTH), ("Pohjankukka_2017", MTH), ("Valavi_2019", MTH), ("?Belgiu_Dragut_2016", NEED), ("?training_on_global_LC_labels", NEED)],
   ["Belgiu Dragut 2016 random forest remote sensing review", "training land cover classifier with global land cover product labels purity filter noisy labels", "spatial block cross validation land cover classification autocorrelation"], "medium", "T09, T10")
th("TH-MET-12", "3.6 Labels", "method",
   "Label contract v002: FLOOD where S1 saw water on >= 2 of the 3 peak dates on land dry on every pre-breach date; NON_FLOOD where every post-breach date was dry; IGNORE elsewhere. v003_A adds REFERENCE_WATER (recurrent water on >= 3 admitted May dates) and UNKNOWN; W_pre (1-2 June) enters its ontology.",
   "Weak-label datasets from SAR for flood segmentation (Sen1Floods11 Bonafilia 2020; Bai 2021) and reference-water handling (Martinis 2022); DOIs for Bonafilia/Bai.",
   [("Bonafilia_2020", MTH), ("Bai_2021", MTH), ("Martinis_2022", MTH)],
   ["Sen1Floods11 weak labels Sentinel-1 flood segmentation dataset", "persistent flood label multiple dates SAR water mask training labels"], "medium", "T02")
th("TH-MET-13", "3.6 U-Net", "method",
   "U-Net with a ResNet-34 encoder trained from scratch on 512-px patches with masked BCE + Dice for 60 epochs (seed fixed); arms differ only in inputs (U0d, U0z, U1, U2 on v002; U0d, U2, U2b on v003_A); thresholds frozen on validation.",
   "Ronneberger 2015, He 2016, segmentation_models.pytorch (DOIs / version); Dice loss (Milletari 2016); precedent for masked losses with IGNORE labels.",
   [("Ronneberger_2015", MTH), ("He_2016", MTH), ("Iakubovskii_2019", MTH), ("?Milletari_2016_Dice", NEED)],
   ["Milletari 2016 V-Net Dice loss segmentation", "masked loss ignore label semantic segmentation partial annotations remote sensing"], "low", "T04")
th("TH-MET-14", "3.7 Blocking", "method",
   "10 km spatial blocks with 640 m eroded buffers and pure 512-px footprints; block size exceeds patch + two buffers (6.4 km) and is the smallest for which a validation patch exists (5 km leaves none); 7.5/15/20 km splits retrain U2 as a sensitivity; arms are compared by a paired bootstrap over identical blocks (2000 resamples).",
   "Block-size selection by autocorrelation range (Roberts 2017; Valavi 2019; Ploton 2020; Karasiak 2022); block/cluster bootstrap for map-accuracy intervals.",
   [("Roberts_2017", MTH), ("Valavi_2019", MTH), ("Pohjankukka_2017", MTH), ("?Ploton_2020", NEED), ("?Karasiak_2022", NEED), ("?block_bootstrap_map_accuracy", NEED)],
   ["Ploton 2020 spatial validation reveals poor predictive performance large-scale ecological mapping", "Karasiak 2022 spatial dependence between training and test sets remote sensing", "cluster bootstrap spatial blocks confidence interval classification accuracy"], "high", "T03, T20")

# ------------------------------------------------------------------ 4. Results (comparators and interpretation)
th("TH-RES-01", "4.1 Areal maximum", "result",
   "The reconstructed newly inundated area of the Dnipro corridor reaches its maximum on 7 June 2023, between the Sentinel-1 acquisitions of 6 June (partial) and 9 June; the Kherson stage peaks one day later (8 June); the areal maximum and the peak stage are different quantities.",
   "Independent timing evidence: Lehnigk 2026 (stages by 8 June), UNOSAT product of 7 June 13:01 UTC (HDX FL20230606UKR), any daily optical/ICEYE series; literature on extent-vs-stage lag in flood waves.",
   [("Lehnigk_2026", CMP), ("UNOSAT_3616_2023", CMP), ("?HDX_FL20230606UKR", NEED), ("?extent_stage_lag_floodwave", NEED)],
   ["Kakhovka flood extent 7 June 2023 satellite ICEYE Planet daily", "flood extent maximum vs peak stage lag floodplain storage hysteresis", "SWOT Kakhovka water surface elevation peak 8 June Kherson gauge 5.6 m"], "high", "T12, T17b")
th("TH-RES-02", "4.1 Totals", "result",
   "The reconstructed total water-surface area of the corridor rises from 488 km2 (5 June) to 779 km2 (7 June; primary p05-p95 781-799), plus 69 km2 in the Inhulets valley; the newly inundated area is 235 km2 (238-255) and 347 km2 with the DEM as delivered; the new-water volume is 509 hm3 (545-596).",
   "Every published Kakhovka extent with its definition (UNOSAT 620 cumulative land; NASA Harvest 410-420; Kadam 823 model; Monti 2024 S1 series; Shumilova/Vyshnevskyi figures) to place these numbers as different quantities, never as validation.",
   [("UNOSAT_3616_2023", CMP), ("Kadam_2024", CMP), ("Monti_2024", CMP), ("Shumilova_2025", CMP), ("Vyshnevskyi_2023", CMP), ("?NASA_Harvest_2023", NEED)],
   ["Kakhovka flood inundated area km2 published estimates comparison definition", "Monti 2024 Nova Kakhovka Sentinel-1 flooded area time series km2"], "high", "T12, T16")
th("TH-RES-03", "4.1 Recession", "result",
   "The corridor recedes to 183 km2 (9 June), 108 (13 June), 34 (18 June) and 4 km2 (21 June) with the stage back at 0.74 m; the Inhulets valley responds as backwater with its maximum (50 km2 new) on 9 June.",
   "UNOSAT 13 June (180 km2) and 21 June products; Monti 2024 dates; backwater flooding of tributaries at confluences (precedent for the Inhulets treatment).",
   [("UNOSAT_3623_2023", CMP), ("Monti_2024", CMP), ("?tributary_backwater_flooding", NEED)],
   ["Kakhovka flood recession 13 June 21 June 2023 satellite extent", "tributary backwater inundation confluence main-stem stage imposed flood mapping"], "medium", "T12, T13")
th("TH-RES-04", "4.2 S1 agreement", "result",
   "Raw agreement with Sentinel-1 new dark water on 9 June inside the floodplain domain is low (POD 0.26, FAR 0.62, CSI 0.18) and 148 of 150 km2 of apparent terrain misses lie on normally-wet cells; the conditional POD outside that class is 0.96 (diagnostic only); after 18 June S1 'new water' on fields and sand is the dark-water rule, not the flood.",
   "Typical agreement levels between terrain-based extents and SAR masks (GeoFlood/FwDET/HAND evaluations; Johnson 2019), and SAR wetland misses; look-alike false positives after rain on bare fields.",
   [("Johnson_2019", CMP), ("Zheng_2018", CMP), ("Shen_2019", SUP), ("Zhao_2021", SUP)],
   ["HAND inundation map vs SAR flood map agreement critical success index evaluation", "Sentinel-1 false water detection wet bare soil after rainfall low backscatter"], "high", "T13")
th("TH-RES-05", "4.3 Ontology", "result",
   "On 9 June B (terrain-only) = 120 km2, dominated by trees (43), wetland (20) and built-up (23); C (S1-only) = 261 km2, of which 173 km2 are normally-wet reed beds (submergence) and 54 km2 lie >= 5 m above the reconstructed surface (topographically unsupported S1-only detections).",
   "Quantitative literature on SAR omission under forest/reeds/urban and on look-alike commission (percent of area) for comparison; radar shadow and smooth-surface causes.",
   [("Grimaldi_2020", SUP), ("Zhao_2021", SUP), ("Shen_2019", SUP), ("Giustarini_2013", SUP), ("?Tsyganskaya_2018", NEED)],
   ["SAR flood omission error forest urban wetland percentage Sentinel-1 validation", "Giustarini 2013 change detection approach urban flood SAR"], "medium", "T14")
th("TH-RES-06", "4.4 ICESat-2", "result",
   "Along the night ICESat-2 tracks that sample the S1-only cells >= 2 m above the surface, the DEM agrees with the altimetry to +0.03 m (delta) / +0.02 m (floodway) median (p10-p90 -0.31 to +0.64 m) and 0.0 % of segments lie below the surface: no evidence for a DEM bias large enough to explain those detections (supports, does not prove).",
   "ATL08 accuracy over cropland/grass (Liu 2021; Neuenschwander 2020) to show the check is sensitive enough; Lehnigk's ATL08 use on the site.",
   [("Lehnigk_2026", SUP), ("Neuenschwander_2019", SUP), ("?Liu_2021_ATL08", NEED)],
   ["ICESat-2 ATL08 terrain accuracy cropland grassland RMSE bias", "ATL08 vs lidar DEM validation vegetation height error flat terrain"], "medium", "T15")
th("TH-RES-07", "4.5 SWOT vs gauge", "result",
   "After re-anchoring, the SWOT node surface agrees with the Kherson gauge at day level (median +0.01 m, NMAD 0.07 m, RMSE 0.06 m over 36 days; +0.10 m median through the rise and peak), consistent with Paper 1's +1.9 cm through the breach fortnight.",
   "SWOT RiverSP node-vs-gauge accuracy in the literature (cal/val papers, 2024-2025) for context; the 11:00 UTC pass vs date-only gauge issue.",
   [("Paper1_Nikoriak_2026", SUP), ("?SWOT_RiverSP_validation_2024", NEED)],
   ["SWOT river node water surface elevation accuracy versus in situ gauges centimetres 2024 2025", "SWOT science orbit calibration phase river height validation"], "medium", "T17")
th("TH-RES-08", "4.6 Three areas", "result",
   "For the same corridor on 9 June: S1 new dark water 300 km2 (snapshot), label recipe 168 km2 (persistence), U2b 241 km2 (mapped), reconstructed new 183 km2 (snapshot); the label contract describes the ~13 June regime; UNOSAT flooded land (620 cumulative; 180 on 13 June) is a fifth definition.",
   "Any paper discussing definitional (not metric) differences between flood-extent products of one event (e.g. multi-product comparisons of a flood; GFM vs CEMS).",
   [("Olofsson_2014", SUP), ("UNOSAT_3616_2023", CMP), ("UNOSAT_3623_2023", CMP), ("?multi_product_flood_extent_comparison", NEED)],
   ["comparison of flood extent products same event different definitions cumulative snapshot reference water", "Copernicus EMS vs Global Flood Monitoring extent comparison definitions"], "medium", "T16")
th("TH-RES-09", "4.8 RF20", "result",
   "RF20 reaches OA 0.940 and macro F1 0.943 against WorldCover in spatial-block CV; the frame transfers B1->B2 and B2->B1 give macro F1 0.906 and 0.932 (stability across frames); these are agreement with the training reference.",
   "Typical OA/F1 of S2 random-forest land cover against reference products; WorldCover's own accuracy.",
   [("Zanaga_2022", CMP), ("?Belgiu_Dragut_2016", NEED), ("?WorldCover_validation_report", NEED)],
   ["Sentinel-2 random forest land cover classification overall accuracy WorldCover labels agreement"], "low", "T09")
th("TH-RES-10", "4.9 Label effect", "result",
   "Changing the label contract from v002 to v003_A at fixed inputs removes a reference-water artefact (-13.4 km2 of flood on recurrent May water, 95 % [-29.5, -2.5]) with no statistically resolved change in EVENT_FLOOD recall (-0.028, [-0.042, +0.006]).",
   "Reference/seasonal water as a negative class in flood ML (Martinis 2022; GFM); label-noise effects on recall (Maiti 2022).",
   [("Martinis_2022", SUP), ("Wagner_2026", SUP), ("Maiti_2022", SUP)],
   ["permanent water reference class flood segmentation false positives seasonal water training labels"], "medium", "T07, T07b")
th("TH-RES-11", "4.9 HAND input", "result",
   "HAND as an input reduces the predicted-flood burden on unlabelled cropland by 9.6 km2 (95 % [-14.8, -5.1]) and moves +0.37 km2 into built-up false positives; land cover as input context retains 78-91 % of the candidate area (not a veto); none of the audited cropland candidates showed positive evidence of breach-induced inundation.",
   "HAND / terrain as a feature in flood ML (Tupas 2023; Sen1Floods11 baselines with HAND; 'HAND-guided' models); cropland look-alikes in SAR.",
   [("Tupas_2023", SUP), ("Bonafilia_2020", SUP), ("?HAND_feature_flood_ML", NEED)],
   ["HAND terrain feature deep learning flood mapping reduces false positives cropland", "Tupas 2023 HAND plausibility feature flood mapping"], "medium", "T06, T08")
th("TH-RES-12", "4.9 U2b", "result",
   "Adding the pre-event water state W_pre as an input increases agreement with v003_A (-0.62 km2 flood on reference water, [-1.28, -0.13]) but is not independent because W_pre also enters the label ontology (label leakage): a diagnostic upper bound.",
   "Apicella 2025; Kaufman 2012.", [("Apicella_2025", SUP), ("?Kaufman_2012", NEED)],
   ["label leakage input feature derived from label evaluation optimistic bias"], "low", "T07b")
th("TH-RES-13", "4.10 Block size", "result",
   "U2 on v003_A gives global F1 0.931 (10 km), 0.956 (7.5), 0.937 (15) and 0.876 (20 km), each with its own test geography; a 5 km split leaves no validation patch; the tested range exceeds the object scale, the correlation length and the patch footprint.",
   "Ploton 2020, Karasiak 2022, Roberts 2017 on choosing block size relative to autocorrelation range and receptive field.",
   [("Roberts_2017", SUP), ("Valavi_2019", SUP), ("?Ploton_2020", NEED), ("?Karasiak_2022", NEED)],
   ["block size selection spatial cross-validation autocorrelation range semivariogram deep learning patches"], "medium", "T20")
th("TH-RES-14", "4.1 Reservoir (context)", "result",
   "Under the sloped daily surface the pool held 18.9 km3 on 5 June (design table 21.1 km3 at the same outlet level) and 4.5 km3 on 13 June: 14.7 km3 released; the largest daily volume change was -3225 hm3 on 7 June, a daily-mean effective release (-dV/dt + Q_in) of ~40 000 m3/s against a DniproHES inflow of 2730 m3/s; downstream new-water storage peaks at 653 hm3 (a few per cent), so most of the release was transmitted downstream.",
   "Yi 2025 (20.4 km3 in 30 days; 5.7e4 initial), Kadam 2024, Vyshnevskyi 2023 (design volume 18.2 km3), G-REALM / Nikopol press levels sources, DniproHES daily releases (Ukrhydroenergo); storage-balance discharge estimation precedents for dam breaches.",
   [("Yi_2025", CMP), ("Kadam_2024", CMP), ("Vyshnevskyi_2023", CMP), ("?Ukrhydroenergo_releases_2023", NEED), ("?GREALM_source", NEED), ("?dam_breach_storage_balance_discharge", NEED)],
   ["dam breach outflow estimation from reservoir storage change daily water balance altimetry", "Kakhovka reservoir level Nikopol June 2023 daily drawdown", "G-REALM Kakhovka reservoir Sentinel-6 water level 2023"], "high", "T21")
th("TH-RES-15", "4.1 Hypsometry", "result",
   "The seamless-DEM hypsometry lies below the design Table 19 at equal levels: -9 % at 17.5 m, -14 % at 13 m, -20 % at 11 m; the design table is undefined below 10 m; the released volume inherits this gap, which Paper 4 will resolve on the historical bathymetry.",
   "Published Kakhovka area-volume relations (design tables; Vyshnevskyi; Yi's altimetry+SAR hypsometry; 'Kakhovka Sea before and after' 2025; post-drainage DEM/ICESat-2 bed surveys) to bracket the gap.",
   [("Vyshnevskyi_2023", CMP), ("Yi_2025", CMP), ("Lehnigk_2026", CMP), ("?Kakhovka_bathymetry_historical", NEED), ("?Kakhovka_Sea_before_after_2025", NEED)],
   ["Kakhovka reservoir bathymetry historical survey area volume curve", "Kakhovka reservoir hypsometric curve stage area volume table design 1956", "exposed Kakhovka reservoir bed DEM ICESat-2 sedimentation volume loss"], "high", "T22")

# ------------------------------------------------------------------ 5. Discussion
th("TH-DIS-01", "5 Discussion", "interpretation",
   "Discrete EO acquisitions undersample the event hydrograph: the reconstructed areal maximum falls between acquisitions; a water-surface-constrained reconstruction adds what no acquisition can give, and that day is the most model-dependent number of the paper.",
   "Literature on satellite revisit vs flood-peak sampling (e.g. probability of observing the peak; GFM temporal sampling; Tarpanelli 2022 on constellations).",
   [("?revisit_flood_peak_sampling", NEED), ("Lehnigk_2026", SUP)],
   ["satellite revisit time probability of capturing flood peak extent Sentinel-1 sampling", "temporal undersampling flood hydrograph satellite observations constellation revisit"], "high")
th("TH-DIS-02", "5 Discussion", "interpretation",
   "The largest uncertainty of the reconstruction is definitional, not metric: whether the delta reed beds are 'new inundation' or 'wetland submergence' changes the maximum by about a third; the metric (Monte-Carlo) interval is narrow and enters the volume mainly as a displacement.",
   "Flooded-vegetation ambiguity literature (Tsyganskaya 2018; Grimaldi 2020); definitional uncertainty in wetland flood mapping.",
   [("Grimaldi_2020", SUP), ("?Tsyganskaya_2018", NEED)],
   ["wetland inundation definition submergence versus flooding emergent vegetation mapping ambiguity"], "medium", "T12, T13")
th("TH-DIS-03", "5 Discussion", "interpretation",
   "The most useful product of the comparison is not a single accuracy but the map of where each source is blind (radar under canopy/urban/reeds; terrain without timing; labels as persistence).",
   "Exclusion maps (Zhao 2021) and uncertainty/exclusion layers in operational services (GFM, Wagner 2026).",
   [("Zhao_2021", SUP), ("Wagner_2026", SUP)],
   ["flood map exclusion layer uncertainty layer operational service Sentinel-1 GFM"], "medium")
th("TH-DIS-04", "5 Discussion", "interpretation",
   "Bathymetry controls stage and timing in outburst-flood modelling (Lehnigk 2026); the reservoir balance is bounded context until Paper 4 rebuilds the bowl on the historical bathymetry, and Paper 5 calibrates a 2-D model on these daily surfaces.",
   "Lehnigk 2026 bathymetry sensitivity numbers; dam-break modelling calibration on observed extents/stages (HEC-RAS 2D precedents).",
   [("Lehnigk_2026", SUP), ("Kadam_2024", CMP)],
   ["dam break 2D hydrodynamic model calibration observed flood extent satellite water surface elevation"], "medium")


def bib_keys():
    if not BIB.exists():
        return {}
    txt = BIB.read_text(encoding="utf-8")
    return {k: ("verified" if re.search(r"verified", n, re.I) and "VERIFY " not in n else "VERIFY")
            for k, n in re.findall(r"@\w+\{([^,]+),.*?note=\{([^}]*)\}", txt, flags=re.S)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    kb = bib_keys()
    for t in T:
        for r in t["refs"]:
            r["status"] = "missing (search)" if r["key"].startswith("?") else kb.get(r["key"], "in bib, no status note")
    (OUT / "theses.json").write_text(json.dumps(T, ensure_ascii=False, indent=1), encoding="utf-8")
    with (OUT / "theses.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id", "section", "category", "priority", "tables", "thesis", "needs", "refs", "search_queries"])
        for t in T:
            w.writerow([t["id"], t["section"], t["category"], t["priority"], t["tables"], t["thesis"], t["needs"],
                        "; ".join(f"{r['key']}[{r['relation']}:{r['status']}]" for r in t["refs"]), " | ".join(t["search_queries"])])
    nodes = [dict(id=t["id"], type="Thesis", label=t["thesis"][:120], section=t["section"], category=t["category"], priority=t["priority"]) for t in T]
    seen = set(); edges = []
    for t in T:
        for r in t["refs"]:
            if r["key"] not in seen:
                seen.add(r["key"]); nodes.append(dict(id=r["key"], type="Reference", status=r["status"]))
            edges.append(dict(source=t["id"], target=r["key"], relation=r["relation"]))
        for q in t["search_queries"]:
            edges.append(dict(source=t["id"], target=q, relation="SEARCH_QUERY"))
    (OUT / "graph.json").write_text(json.dumps(dict(nodes=nodes, edges=edges), ensure_ascii=False, indent=1), encoding="utf-8")
    # GraphML (no networkx dependency): node keys type/label/section/category/priority/status, edge key relation
    from xml.sax.saxutils import escape
    g = ['<?xml version="1.0" encoding="UTF-8"?>', '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">']
    for k in ("type", "label", "section", "category", "priority", "status", "thesis", "needs"):
        g.append(f'<key id="{k}" for="node" attr.name="{k}" attr.type="string"/>')
    g.append('<key id="relation" for="edge" attr.name="relation" attr.type="string"/>'); g.append('<graph id="paper3_theses" edgedefault="directed">')
    full = {t["id"]: t for t in T}
    for n in nodes:
        g.append(f'<node id="{escape(n["id"])}">' + "".join(f'<data key="{k}">{escape(str(v))}</data>' for k, v in n.items() if k != "id")
                 + ("".join(f'<data key="{k}">{escape(full[n["id"]][k])}</data>' for k in ("thesis", "needs")) if n["type"] == "Thesis" else "") + "</node>")
    qn = set()
    for e in edges:
        if e["relation"] == "SEARCH_QUERY" and e["target"] not in qn:
            qn.add(e["target"]); g.append(f'<node id="{escape(e["target"])}"><data key="type">SearchQuery</data><data key="label">{escape(e["target"])}</data></node>')
    for i, e in enumerate(edges):
        g.append(f'<edge id="e{i}" source="{escape(e["source"])}" target="{escape(e["target"])}"><data key="relation">{e["relation"]}</data></edge>')
    g += ["</graph>", "</graphml>"]
    (OUT / "graph.graphml").write_text("\n".join(g), encoding="utf-8")
    md = ["# Theses of Paper 3 that need literature support", "",
          "Generated by `workflows/paper/p100_literature_theses.py` (2026-09-26). One row per thesis: what the manuscript states, what has to be found, "
          "the candidate references already in `docs/references.bib` with their verification status, and search queries to run in the knowledge graph. "
          "Keys starting with `?` are placeholders for sources still to be found. Numbers are the current table values (T-ids) and are context, not the source of truth.", ""]
    for sec in dict.fromkeys(t["section"] for t in T):
        md += [f"## {sec}", "", "| id | prio | thesis | needs | references (relation:status) | search queries |", "|---|---|---|---|---|---|"]
        for t in [x for x in T if x["section"] == sec]:
            refs = "<br>".join(f"`{r['key']}` {r['relation']}: {r['status']}" for r in t["refs"])
            qs = "<br>".join(f"`{q}`" for q in t["search_queries"])
            md.append(f"| {t['id']} | {t['priority']} | {t['thesis']} | {t['needs']} | {refs} | {qs} |")
        md.append("")
    n_missing = sum(1 for t in T for r in t["refs"] if r["key"].startswith("?"))
    md += ["## Summary", "", f"- {len(T)} theses; {sum(1 for t in T if t['priority']=='high')} high priority.",
           f"- {len(seen)} distinct reference nodes, of which {n_missing} placeholders still to be found.",
           "- Relations: SUPPORTED_BY (source states the thesis), COMPARATOR (source gives a value to compare with, never validation), METHOD_FROM (method precedent), CONTRASTS_WITH, NEEDS_SOURCE (placeholder).", ""]
    (OUT / "theses.md").write_text("\n".join(md), encoding="utf-8")
    print(f"-> {OUT}: {len(T)} theses, {len(seen)} references ({n_missing} placeholders)")


if __name__ == "__main__":
    main()
