# Open citations to verify (generated 2026-10-01 by p100b from docs/references.bib and the manuscript template)

One block per reference: the sentence(s) of the manuscript that cite it, the words quoted in them, the section, and what must be checked in the source.

## Giustarini_2013 — content quotation to locate in the source
- **Reference:** Giustarini, Laura and Hostache, Renaud and Matgen, Patrick and Schumann, Guy J.-P. and Bates, Paul D. and Mason, David C. (2013). A Change Detection Approach to Flood Mapping in Urban Areas Using TerraSAR-X. IEEE Transactions on Geoscience and Remote Sensing 51, 2417–2430. DOI [10.1109/tgrs.2012.2210901](https://doi.org/10.1109/tgrs.2012.2210901)
- **To verify:** quotation to be located
- (not cited in the manuscript text)

## Hawker_2022 — content quotation to locate in the source
- **Reference:** Hawker, Laurence and Uhe, Peter and Paulo, Luntadila and Sosa, Jeison and Savage, James and Sampson, Christopher and Neal, Jeffrey (2022). A 30 m global map of elevation with forests and buildings removed. Environmental Research Letters 17, 024016. DOI [10.1088/1748-9326/ac4d4f](https://doi.org/10.1088/1748-9326/ac4d4f)
- **To verify:** licence statement CC BY-NC-SA 4.0 to confirm on the FABDEM record
- **2. Study area and data:** - **Seamless terrain–bed elevation model** (Paper 2): the kriged bathymetric bed inside the pre-breach water polygons and FABDEM v1.2 elsewhere — a bare-earth DTM derived from the Copernicus DEM with buildings and forests removed by machine learning (Hawker et al. 2022; residual mean absolute errors of 1.1–1.6 m remain in built-up areas, Iqbal et al. 2023) — on one 20 m grid in EVRF2019, with a source mask that records which cells are FABDEM and which are bed; the reconstruction refuses an input that does not declare its vertical frame (§3.2).

## Johnson_2019 — content quotation to locate in the source
- **Reference:** Johnson, J. Michael and Munasinghe, Dinuke and Eyelade, Damilola and Cohen, Sagy (2019). An integrated evaluation of the National Water Model (NWM)--Height Above Nearest Drainage (HAND) flood mapping methodology. Natural Hazards and Earth System Sciences 19, 2405--2420. DOI [10.5194/nhess-19-2405-2019](https://doi.org/10.5194/nhess-19-2405-2019)
- **To verify:** the HAND-limits argument of the Discussion to be located in the text
- **1. Introduction:** Terrain-based approaches that project a water surface or a mapped extent on a DEM — HAND (Rennó et al. 2008; Nobre et al. 2011), GeoFlood (Zheng et al. 2018), FwDET (Cohen et al. 2019) — are first-order products, not hydrodynamics: Johnson et al. (2019) find that a HAND-based method "does not accurately capture inundated cells" while it does highlight regions at risk.  
  quoted: “does not accurately capture inundated cells”

## Iakubovskii_2019 — content quotation to locate in the source
- **Reference:** Iakubovskii, Pavel (2019). Segmentation Models Pytorch. GitHub repository.
- **To verify:** version 0.5.0
- (not cited in the manuscript text)

## Biancamaria_2016 — content quotation to locate in the source
- **Reference:** Biancamaria, Sylvain and Lettenmaier, Dennis P. and Pavelsky, Tamlin M. (2016). The SWOT mission and its capabilities for land hydrology. Surveys in Geophysics 37, 307--337. DOI [10.1007/s10712-015-9346-y](https://doi.org/10.1007/s10712-015-9346-y)
- **To verify:** Crossref year 2015 (online), volume 37 is 2016
- **2. Study area and data:** - **SWOT** L2_HR_RiverSP v2.0 nodes on the one-day calibration orbit (Biancamaria et al. 2016), 26 May–10 July 2023, {{T01|dataset=SWOT L2_HR_RiverSP v2.0 nodes (1-day orbit), accepted;|detail||}}; node_q ≤ 1 and dark fraction < 0.5 as in Paper 1.

## Olofsson_2014 — content quotation to locate in the source
- **Reference:** Olofsson, Pontus and Foody, Giles M. and Herold, Martin and Stehman, Stephen V. and Woodcock, Curtis E. and Wulder, Michael A. (2014). Good practices for estimating area and assessing accuracy of land change. Remote Sensing of Environment 148, 42--57. DOI [10.1016/j.rse.2014.02.015](https://doi.org/10.1016/j.rse.2014.02.015)
- **To verify:** the 'sample of higher quality' quotation to be located
- **1. Introduction:** The area obtained by counting classified pixels is a *mapped* area, not an unbiased estimate of the true flooded area; the good-practice framework of Olofsson et al. (2014) requires an accuracy assessment "based on a sample of higher quality" reference data, which does not exist for this event.  
  quoted: “based on a sample of higher quality”
- **3.1 Evidence hierarchy, area semantics and the result blocks:** No probability-sample reference exists, so none of them is an unbiased estimate of the true flooded area (Olofsson et al. 2014).

## Pohjankukka_2017 — content quotation to locate in the source
- **Reference:** Pohjankukka, Jonne and Pahikkala, Tapio and Nevalainen, Paavo and Heikkonen, Jukka (2017). Estimating the prediction performance of spatial models via spatial k-fold cross validation. International Journal of Geographical Information Science 31, 2001--2019. DOI [10.1080/13658816.2017.1346255](https://doi.org/10.1080/13658816.2017.1346255)
- **To verify:** cited as in Paper 1
- (not cited in the manuscript text)

## Lehnigk_2026 — content quotation to locate in the source
- **Reference:** Lehnigk, K. E. and Pavelsky, T. M. and Lang, K. A. (2026). SWOT satellite observations of the Kakhovka dam break flood highlight limitations of outburst flood models. Geophysical Research Letters 53, e2025GL120832. DOI [10.1029/2025gl120832](https://doi.org/10.1029/2025gl120832)
- **To verify:** the quoted stages / bathymetry statements to be read (the quoted findings (peak stages by 8 June; bathymetry 1.4 m / 5.8-6.1 m stage errors; ATL08 on the exposed bed))
- **1. Introduction:** Lehnigk et al. (2026) show with the daily SWOT water-surface elevations of the one-day calibration orbit — the data we use here — that two-dimensional outburst-flood simulations underestimate the observed peak stages by 1.4 to 6.1 m and misplace their timing unless reservoir and channel bathymetry are corrected, and even then reproduce neither stage nor timing fully; downstream stages reached 10–11 m by 8 June.
- **4.1.1 The daily series below the dam:** The Kherson stage peaks one day later ({{T12|region=DNIPRO_CORRIDOR,date=2023-06-08|kherson_gauge_m||.2f}} m on 8 June, the daily value of the river yearbook; the operational record gives 5.68 m at 15:00 on 8 June (Gleick et al. 2023) and Lehnigk et al. (2026) cite 5.6 m, a ~0.1 m spread between sources; the peak stages by 8 June that Lehnigk et al. (2026) report from the same SWOT data are consistent with it) — the areal maximum and the peak stage are different quantities, and the day of the areal maximum is a property of the reconstructed series, not an observation.
- **4.1.3 The reservoir: emptying, depth and storage balance:** The released volume itself is period- and hypsometry-dependent in the literature: Yi et al. (2025) obtain 20.4 ± 1.4 km³ in 30 days from a pre-breach volume of 21.0 km³ (17.3 m), Vyshnevskyi et al. (2023) give 19.8 km³ at 16.76 m from the operation rules, Monti et al. (2024) about 7.5 km³, and Lehnigk et al. (2026) cite ∼8 km³; our release over 5–13 June sits inside that spread.
- **5. Discussion:** In most worlds it coincides with the day of the peak stage at Kherson (8 June; Lehnigk et al. 2026 report downstream peak stages by 8 June from the same SWOT data), but not in all: maximum extent and maximum stage are different quantities whose timing changes along a 100 km reach — floodplain storage and drainage produce hysteresis between extent, volume and stage (Fassoni-Andrade et al. 2023) — and the day of the areal maximum is the most model-dependent number of this paper: on 8 June a water surface a few decimetres lower disconnects tens of km² of the left bank (T11e, FigS17), which is why the two days share the maximum across the worlds.
- **5. Discussion:** **Even with SWOT, the step from a water surface to a flood extent is not unique.** Lehnigk et al. (2026) show that hydraulic models of this flood do not reproduce the observed stages and their timing without corrected bathymetry; here the stages come from the observations, validated in Paper 1, and what remains uncertain is how they project onto the ground.
- **5. Discussion:** Such models of this event need corrected reservoir and channel bathymetry before they reproduce the observed stages and their timing (Lehnigk et al. 2026), so they cannot replace the observation-constrained reconstruction — and the reconstruction cannot replace them.

## CEOBS_2023 — content quotation to locate in the source
- **Reference:** {Conflict and Environment Observatory} (2023). Analysing the environmental consequences of the Kakhovka dam collapse. \url{https://ceobs.org/analysing-the-environmental-consequences-of-the-kakhovka-dam-collapse/}.
- **To verify:** source of the ~620 / ~180 km2 flooded-area figures (UNOSAT)
- (not cited in the manuscript text)

## REACH_2023 — content quotation to locate in the source
- **Reference:** {REACH Initiative} (2023). Ukraine situational overview: Kakhovka Dam breach (16 June 2023). ReliefWeb.
- **To verify:** 
- (not cited in the manuscript text)

## Paper1_Nikoriak_2026 — content quotation to locate in the source
- **Reference:** Nikoriak, Viktor and others (2026). From impounded pool to river: quantifying the post-breach reorganisation of the former Kakhovka Reservoir from water-surface geometry. .
- **To verify:** 
- **1. Introduction:** Paper 1 (Nikoriak et al. 2026) brought gauges, ICESat-2, SWOT and the historical hydrography into one vertical frame, validated it through measured closure residuals and cross-sensor tests, and used it to show how the former reservoir reorganised from a level pool into a sloping, fragmented river; Paper 2 built the seamless terrain–bed model.

## Paper2_Nikoriak_2026 — content quotation to locate in the source
- **Reference:** Nikoriak, Viktor (2026). Bathymetry and a seamless terrain model of the former Kakhovka Reservoir and the lower Dnipro. .
- **To verify:** title
- **1. Introduction:** Paper 1 (Nikoriak et al. 2026) brought gauges, ICESat-2, SWOT and the historical hydrography into one vertical frame, validated it through measured closure residuals and cross-sensor tests, and used it to show how the former reservoir reorganised from a level pool into a sloping, fragmented river; Paper 2 built the seamless terrain–bed model.

## Yi_2025 — content quotation to locate in the source
- **Reference:** Yi, Shuang and Li, Hao‐si and Han, Shin‐Chan and Sneeuw, Nico and Yuan, Chunyu and Song, Chunqiao and Yeo, In‐Young and McCullough, Christopher M. (2025). Quantification of the Flood Discharge Following the 2023 Kakhovka Dam Breach Using Satellite Remote Sensing. Water Resources Research 61, e2024WR038314. DOI [10.1029/2024WR038314](https://doi.org/10.1029/2024WR038314)
- **To verify:** quantities as cited (initial breach discharge) to be read (the quoted values: initial discharge 5.7 x 10^4 m3/s, drop 12.6 +- 1.1 m, water loss 20.4 +- 1.4 km3 in 30 days)
- **1. Introduction:** Reservoir-side balances give the volume released: Yi et al. (2025) derive an initial breach flow of (5.7 ± 0.8) × 10⁴ m³ s⁻¹ and 20.4 ± 1.4 km³ lost in 30 days from gravimetry, altimetry and imagery; Shumilova et al. (2025) model about 16.4 km³ over two weeks.
- **4.1.3 The reservoir: emptying, depth and storage balance:** Published estimates are different physical quantities of the same order and are context, not validation: the *initial* breach flow of Yi et al. (2025) from a gravimetry–altimetry–imagery discharge model is (5.7 ± 0.8) × 10⁴ m³ s⁻¹, the HEC-RAS scenario peaks of Kadam et al. (2024) are 3.6 × 10⁴ m³ s⁻¹ (300 m breach) and 4.8 × 10⁴ m³ s⁻¹ (600 m), and Shumilova et al. (2025) model a release of about 16.4 km³ over two weeks.
- **4.1.3 The reservoir: emptying, depth and storage balance:** The released volume itself is period- and hypsometry-dependent in the literature: Yi et al. (2025) obtain 20.4 ± 1.4 km³ in 30 days from a pre-breach volume of 21.0 km³ (17.3 m), Vyshnevskyi et al. (2023) give 19.8 km³ at 16.76 m from the operation rules, Monti et al. (2024) about 7.5 km³, and Lehnigk et al. (2026) cite ∼8 km³; our release over 5–13 June sits inside that spread.
- **4.3.5 The reservoir from orbit:** On 20 June, with the whole pool observed, Sentinel-2 finds {{T23|date=2023-06-20,source=S2_CROSSCHECK|water_km2||.0f}} km² of water; the Sentinel-1 reservoir areas of Yi et al. (2025, read from the authors' archive) fall from {{T23|date=2023-06-08,source=S1|yi2025_S1_archive_km2||.0f}} km² on 8 June to {{T23|date=2023-06-20,source=S1|yi2025_S1_archive_km2||.0f}} km² on 20 June, the same sequence (Fig11h).
- **4.3.5 The reservoir from orbit:** Published remnant areas differ by definition rather than by error: about 845 km² by 20 June from the decreases reported by Yi et al. (2025), 655.9 km² on 17 June in the state estimate quoted by Novitskyi et al. (2024), 379.7 km² on 8 September including the restored channel (Magas et al. 2023), and 1.63 km² of open water on 6 September with 110 km² still wet (Tsiupa et al. 2023).

## Monti_2024 — content quotation to locate in the source
- **Reference:** Monti, R. and Rossi, L. and Reguzzoni, M. (2024). The Nova Kakhovka dam collapse flooding as seen from Sentinel-1 SAR satellite images. Advances in Geodesy and Geoinformation. DOI [10.24425/agg.2023.146162](https://doi.org/10.24425/agg.2023.146162)
- **To verify:** pages (50-50 in Crossref) and first-author given name (first-author given name and pages)
- **1. Introduction:** Satellite mappings give areas with their own definitions: Yailymov et al. (2025) map 473 km² of flooded land as of 9 June by land-cover class, 294 km² of it wetlands, against a pre-flood water map of 5 June; Zuo et al. (2024) follow the water-surface area at 300 m in Sentinel-3 OLCI scenes, which doubled within three days and was largest around 9 June; Monti et al. (2024) map the flooding along ~80 km of river with Sentinel-1 change detection; Jiao et al. (2025) use the event to test a Sentinel-1 flood-extraction method.
- **4.1.3 The reservoir: emptying, depth and storage balance:** The released volume itself is period- and hypsometry-dependent in the literature: Yi et al. (2025) obtain 20.4 ± 1.4 km³ in 30 days from a pre-breach volume of 21.0 km³ (17.3 m), Vyshnevskyi et al. (2023) give 19.8 km³ at 16.76 m from the operation rules, Monti et al. (2024) about 7.5 km³, and Lehnigk et al. (2026) cite ∼8 km³; our release over 5–13 June sits inside that spread.

## Zheng_2018 — content quotation to locate in the source
- **Reference:** Zheng, Xing and Maidment, David R. and Tarboton, David G. and Liu, Yan Y. and Passalacqua, Paola (2018). {GeoFlood}: large-scale flood inundation mapping based on high-resolution terrain analysis. Water Resources Research 54, 10013--10033. DOI [10.1029/2018WR023457](https://doi.org/10.1029/2018WR023457)
- **To verify:** pages 10013-10033 not in Crossref; the GeoFlood quotation to be located ())
- **1. Introduction:** Terrain-based approaches that project a water surface or a mapped extent on a DEM — HAND (Rennó et al. 2008; Nobre et al. 2011), GeoFlood (Zheng et al. 2018), FwDET (Cohen et al. 2019) — are first-order products, not hydrodynamics: Johnson et al. (2019) find that a HAND-based method "does not accurately capture inundated cells" while it does highlight regions at risk.  
  quoted: “does not accurately capture inundated cells”
- **3.3 Terrain-connectivity rule, pre-breach baseline, depth and volume:** The event source is the river network, not every pre-existing water body: seeding the connectivity from all pre-breach water cells — the earlier form of this rule, kept as the provenance variant *all-prewater seeding* (T12, T13, FigS16) — let a few pond and canal cells "flood" {{T11m|verdict=ISOLATED_NEVER,region=DNIPRO_CORRIDOR|max_km2|max|.0f}} km² of WorldCover cropland on the left-bank sandy terrace under the Kokan' level extrapolated 14 km, with no terrain path to the river on any day (§4.2.3) — the case that terrain-index methods list as their limitation (Zheng et al. 2018) and that the connectivity requirement exists to exclude.
- **3.3 Terrain-connectivity rule, pre-breach baseline, depth and volume:** The connectivity requirement is not inherited from the terrain-index methods we build on: HAND-type methods "do not preserve hydraulic connectivity (i.e., floodplain cells lower than the channel water height are denoted as flooded whether or not there is a physical flow path to them)" (Bates 2022), and GeoFlood by design flags "local depressions such as ponds or waterbodies … even if they are not connected with the main stem river" (Zheng et al. 2018).  
  quoted: “do not preserve hydraulic connectivity (i.e., floodplain cells lower than the channel water height are denoted as flooded whether or not there is a physical flow path to them)” | “local depressions such as ponds or waterbodies … even if they are not connected with the main stem river”

## He_2024 — content quotation to locate in the source
- **Reference:** He, Yongjun and Wang, Jinfei and Zhang, Ying and Liao, Chunhua (2024). An efficient urban flood mapping framework towards disaster response driven by weakly supervised semantic segmentation with decoupled training samples. ISPRS Journal of Photogrammetry and Remote Sensing 207, 338--358. DOI [10.1016/j.isprsjprs.2023.12.009](https://doi.org/10.1016/j.isprsjprs.2023.12.009)
- **To verify:** read as a weakly-supervised urban flood-mapping paper, not a label-noise survey (given names)
- **1. Introduction:** A U-Net trained on labels derived from those masks inherits both limits (Maiti et al. 2022; weak supervision for flood mapping: He et al. 2024); its accuracy against such labels is agreement, not truth, and an input that also builds the label is label leakage (Apicella et al. 2025).

## Maiti_2022 — content quotation to locate in the source
- **Reference:** Maiti, A. and Oude Elberink, S. and Vosselman, G. (2022). Effect of label noise in semantic segmentation of high resolution aerial images and height data. ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences V-2-2022, 275--282. DOI [10.5194/isprs-annals-V-2-2022-275-2022](https://doi.org/10.5194/isprs-annals-V-2-2022-275-2022)
- **To verify:** quotation to be located (pages/DOI)
- **1. Introduction:** A U-Net trained on labels derived from those masks inherits both limits (Maiti et al. 2022; weak supervision for flood mapping: He et al. 2024); its accuracy against such labels is agreement, not truth, and an input that also builds the label is label leakage (Apicella et al. 2025).

## Rikimaru_2002 — no Crossref record; cite as is
- **Reference:** Rikimaru, Atsushi and Roy, P. S. and Miyatake, S. (2002). Tropical forest cover density mapping. Tropical Ecology 43, 39--47.
- **To verify:** no Crossref record found 2026-09-28; the usual source of the Bare Soil Index (BSI)
- **2. Study area and data:** - **Sentinel-2** L2A scenes (Sen2Cor processing, Main-Knorn et al. 2017) as index stacks per date at 10 m — NDWI (McFeeters 1996), MNDWI (Xu 2006), NDVI (Tucker 1979), NDMI (Gao 1996), BSI (Rikimaru et al. 2002, Tropical Ecology 43, 39–47), AWEIsh (Feyisa et al. 2014) and the turbidity index NDTI (Lacaux et al. 2007) — and window composites: PRE (2022-01-01 … 2023-06-05), EVENT (2023-06-07 … 07-31) and TRACE (2023-08-01 … 11-30); the post-event TRACE window is not used by the canonical weak labels (§3.8).

## Pedregosa_2011 — no Crossref record; cite as is
- **Reference:** Pedregosa, Fabian and Varoquaux, Gaël and Gramfort, Alexandre and Michel, Vincent and Thirion, Bertrand and Grisel, Olivier and Blondel, Mathieu and Prettenhofer, Peter and Weiss, Ron and Dubourg, Vincent and Vanderplas, Jake and Passos, Alexandre and Cournapeau, David and Brucher, Matthieu and Perrot, Matthieu and Duchesnay, Édouard (2011). Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research 12, 2825--2830.
- **To verify:** no DOI (JMLR); not found in Crossref/OpenAlex 2026-09-28
- (not cited in the manuscript text)

## Lefebvre_2019 — full text unreachable; the number is only in a bib note
- **Reference:** Lefebvre, Ga{\"e}tan and Davranche, Aur{\'e}lie and Willm, Lo{\"i}c and Campagna, Julie and Redmond, Lauren and Merle, Cl{\'e}ment and Guelmami, Anis and Poulin, Brigitte (2019). Introducing {WIW} for Detecting the Presence of Water in Wetlands with Landsat and Sentinel Satellites. Remote Sensing 11, 2210. DOI [10.3390/rs11192210](https://doi.org/10.3390/rs11192210)
- **To verify:** the Phragmites 5 % / 71 % figure not read in the paper (before quoting it)
- **3.3 Terrain-connectivity rule, pre-breach baseline, depth and volume:** Under emergent vegetation that state cannot be observed with the sensors used here: standard optical water indices systematically underestimate the flooding duration under a vegetation cover (Lefebvre et al. 2019), subcanopy flooding in high-vegetated wetlands could not be detected with Sentinel-1 VV/VH (Slagter et al. 2020), and in tropical herbaceous wetlands inundated vegetation can account for over three quarters of the inundated area, which open-water mapping does not detect (Oakes et al. 2023).

## Pulvirenti_2021 — not in the manuscript; full text unreachable
- **Reference:** Pulvirenti, Luca and Squicciarino, Giuseppe and Fiori, Elisabetta and Ferraris, Luca and Puca, Silvia (2021). A Tool for Pre-Operational Daily Mapping of Floods and Permanent Water Using Sentinel-1 Data. Remote Sensing 13, 1342. DOI [10.3390/rs13071342](https://doi.org/10.3390/rs13071342)
- **To verify:** not cited in the manuscript; forwarded claims (double bounce, no unique SAR signature of flooded vegetation) NOT checked -- the abstract only says flood maps have gaps from undetected flooded vegetation; full text unreachable by script (MDPI blocks)
- (not cited in the manuscript text)

## Cohen_2022 — not in the manuscript; full text unreachable
- **Reference:** Cohen, Juval and Heinilä, Kirsikka and Huokuna, Mikko and Metsämäki, Sari and Heilimo, Jyri and Sane, Mikko (2022). Satellite-based flood mapping in the boreal region for improving situational awareness. Journal of Flood Risk Management 15, e12744. DOI [10.1111/jfr3.12744](https://doi.org/10.1111/jfr3.12744)
- **To verify:** not cited in the manuscript; forwarded claim of an 'uncertain area' class for semi-forested terrain NOT checked; the abstract only says EMS and the S1 interpretation 'did not detect floods in forests'; full text unreachable by script (Wiley blocks)
- (not cited in the manuscript text)
