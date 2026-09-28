# 07c — Method and index references missing from `docs/references.bib`

Extracted 2026-09-28 from `publication/manuscript.md` (§2 L113–127, §3.5–3.7) and the `floodstate-eo` code (`src/floodstate_eo/optical/sentinel_preprocess.py`, `fusion/p65b_m2_spatial_cv.py`); each candidate first-source was checked against CrossRef by DOI with a title match (OpenAlex/DataCite for the NSIDC product). Nothing below is invented: `VERIFIED` = CrossRef returned the expected title (ratio ≥ 0.85); `NO_DOI` = grey literature to cite without a DOI; `DOI_FOUND_BY_TITLE` = found only by OpenAlex title search (confirm before use). Verified entries are in `07c_method_references_verified.bib`; `in_corpus = True` means the text is also in the local corpus.

## Sentinel-2 indices as implemented (formulas from the code)

| index | formula (Sentinel-2 bands) | canonical source | verdict |
|---|---|---|---|
| NDVI | `(B08−B04)/(B08+B04)` | Tucker_1979 (+ Rouse_1974 as the original, grey) | VERIFIED |
| NDWI | `(B03−B08)/(B03+B08)` | McFeeters_1996 (in bib) | (in bib) |
| MNDWI | `(B03−B11)/(B03+B11)` | Xu_2006 (in bib) | (in bib) |
| NDMI | `(B08−B11)/(B08+B11)` | Gao_1996 (the code comment names Gao 1996; Wilson_Sader_2002 is the harvest/moisture application) | VERIFIED |
| BSI | `((B11+B04)−(B08+B02))/((B11+B04)+(B08+B02))` | Rikimaru_2002 — the form used ((SWIR+Red)−(NIR+Blue)); NO DOI (Tropical Ecology 43:39–47) → cite as grey; Diek_2017 is a different bare-soil composite, not this formula | NO_DOI (grey literature) |
| AWEIsh | `B02 + 2.5·B03 − 1.5·(B08+B11) − 0.25·B12` | Feyisa_2014 (in corpus) | VERIFIED |
| NDTI | `(B04−B03)/(B04+B03)` | Lacaux_2007 (turbidity index; the code comment names it) — NOT the tillage NDTI of Van Deventer 1997 | VERIFIED |

## Methods and tools

| method / tool | where in the manuscript | proposed reference | DOI | CrossRef verdict | in corpus |
|---|---|---|---|---|---|
| Sen2Cor (Sentinel-2 L2A) | see extraction table below | Main-Knorn_2017: Sen2Cor for Sentinel-2 (2017) | 10.1117/12.2278218 | VERIFIED | False |
| Random forest | see extraction table below | Breiman_2001: Random Forests (2001) | 10.1023/A:1010933404324 | VERIFIED | True |
| Random forest in remote sensing | see extraction table below | Belgiu_Dragut_2016: Random forest in remote sensing: A review of applications and future directions (2016) | 10.1016/j.isprsjprs.2016.01.011 | VERIFIED | True |
| Dice loss | see extraction table below | Milletari_2016: V-Net: Fully Convolutional Neural Networks for Volumetric Medical Image Segmentation (2016) | 10.1109/3DV.2016.79 | VERIFIED | False |
| Radiometric terrain correction (terrain flattening) | see extraction table below | Small_2011: Flattening Gamma: Radiometric Terrain Correction for SAR Imagery (2011) | 10.1109/TGRS.2011.2120616 | VERIFIED | False |
| Lee speckle filter | see extraction table below | Lee_1980: Digital Image Enhancement and Noise Filtering by Use of Local Statistics (1980) | 10.1109/TPAMI.1980.4766994 | VERIFIED | True |
| Kriging | see extraction table below | Matheron_1963: Principles of geostatistics (1963) | 10.2113/gsecongeo.58.8.1246 | VERIFIED | False |
| Bootstrap | see extraction table below | Efron_1979: Bootstrap Methods: Another Look at the Jackknife (1979) | 10.1214/aos/1176344552 | VERIFIED | False |
| Bootstrap (book) | see extraction table below | Efron_Tibshirani_1993: An Introduction to the Bootstrap (1994) | 10.1201/9780429246593 | VERIFIED | False |
| CSI / POD / FAR | see extraction table below | Schaefer_1990: The Critical Success Index as an Indicator of Warning Skill (1990) | 10.1175/1520-0434(1990)005<0570:TCSIAA>2.0.CO;2 | VERIFIED | False |
| NMAD (robust DEM accuracy) | see extraction table below | Hohle_2009: Accuracy assessment of digital elevation models by means of robust statistical methods (2009) | 10.1016/j.isprsjprs.2009.02.003 | VERIFIED | False |
| Sentinel-1 mission / GRD | see extraction table below | Torres_2012: GMES Sentinel-1 mission (2012) | 10.1016/j.rse.2011.05.028 | VERIFIED | True |
| 8-connectivity / connected components | see extraction table below | Rosenfeld_Pfaltz_1966: Sequential Operations in Digital Picture Processing (1966) | 10.1145/321356.321357 | VERIFIED | False |
| ICESat-2 ATL13 inland water | see extraction table below | Jasinski_2021: Inland and Near-Shore Water Profiles Derived from the High-Altitude Multiple Altimeter Beam Experimental Lidar (MABEL) () | — | NO_DOI (grey literature) | False |
| ICESat-2 ATL13 product | see extraction table below | ATL13_v6: ATLAS/ICESat-2 L3A Along Track Inland Surface Water Data, Version 6 (2023) | 10.5067/ATLAS/ATL13.006 | VERIFIED_OPENALEX | False |
| ATL08 product | see extraction table below | Neuenschwander_2019: The ATL08 land and vegetation product for the ICESat-2 Mission (2019) | 10.1016/j.rse.2018.11.005 | VERIFIED | False |
| EGG (European gravimetric quasigeoid) modelling | see extraction table below | Denker_2013: Regional Gravity Field Modeling: Theory and Practical Results (2013) | 10.1007/978-3-642-28000-9_5 | VERIFIED | False |
| EVRF2019 | see extraction table below | Sacher_2019: EVRF2019 as new realization of EVRS () | — | NO_DOI (grey literature) | False |
| EPSG:9902 (Baltic 1977 height to EVRF2019) | see extraction table below | EPSG_9902: EPSG Geodetic Parameter Dataset () | — | NO_DOI (grey literature) | False |
| scikit-learn RandomForestClassifier (RF20) | see extraction table below | Pedregosa_2011: Scikit-learn: Machine Learning in Python () | — | NOT_FOUND |  |

## Extraction: every method/index/tool named in the manuscript and its bibliography state

| term | manuscript lines | bib key present | action |
|---|---|---|---|
| NDVI, NDMI, BSI, AWEIsh, NDTI | 116 | — | cite Tucker 1979 / Gao 1996 / Rikimaru 2002 (grey) / Feyisa 2014 / Lacaux 2007 (B-10) |
| Sentinel-2 L2A (Sen2Cor) | 116 | — | Main-Knorn 2017 (verified) |
| Random forest | 191 | — | Breiman 2001 + Belgiu & Drăguţ 2016 (both verified, in corpus); scikit-learn: Pedregosa 2011 (see CSV) |
| Dice loss | 203 | — | Milletari 2016 (verified) |
| masked BCE | 203 | — | no canonical source; describe |
| RTC / terrain flattening, GRD | 113 | — | Small 2011 (verified); Torres 2012 mission paper (verified, in corpus) |
| Lee/Lopes speckle filter | theses only | Lopes_1990 | Lee 1980 (verified, in corpus) if the Lee filter is meant |
| kriging (bathymetric bed, Paper 2) | 121 | — | Matheron 1963 (verified) — or leave to Paper 2 |
| ATL13 | 96 | — | NSIDC ATL13 v6 dataset DOI 10.5067/ATLAS/ATL13.006 (verified via DataCite/OpenAlex) |
| ATL08 | 122, 184 | Neuenschwander_2019 | DOI 10.1016/j.rse.2018.11.005 now verified (bib had none) |
| EGG2015 | 17, 101, 133 | — | no DOI found for EGG2015 itself; Denker 2013 (regional gravity field modelling, verified) is the methodological reference — grey citation of the EGG2015 release note needed |
| EVRF2019, EPSG:9902 | 97, 119 | — | grey: BKG/EVRS report (Sacher & Liebsch) and the EPSG dataset entry, with access dates |
| paired block bootstrap | 50, 213, 404 | — | Efron 1979 / Efron & Tibshirani 1993 (verified); block/cluster bootstrap for spatial units: see TH-MET-14.B rows |
| POD / FAR / CSI | 181, 307, 381 | — | Schaefer 1990 (verified); limits of binary measures: Stephens 2014 (in corpus) |
| NMAD | 124–166 | — | Höhle & Höhle 2009 (verified) |
| 8-connectivity | 148 | — | Rosenfeld & Pfaltz 1966 (verified) — optional |
| Monte-Carlo, cluster-normal emulator, purity filter | 23–30, 172, 191 | — | own constructions; DEM-error simulation precedent Hawker 2018 (in corpus) |

## Not resolvable (do not cite with a DOI)

- Rouse et al. 1974 (NASA SP-351) — NDVI original; grey.
- Rikimaru, Roy & Miyatake 2002, Tropical Ecology 43(1):39–47 — BSI; no DOI in CrossRef/OpenAlex.
- Sacher & Liebsch (BKG) EVRF2019 report; EPSG Geodetic Parameter Dataset entry 9902; EGG2015 release note (Denker 2015/16) — grey literature with access date.
- The `Jasinski_2021` probe used a wrong expected title (a MABEL paper) and is void; the ATL13 product DOI above is the citable item.
