# References to verify before submission

Every entry added to `docs/references.bib` on 2026-09-25 carries `note = {VERIFY}`. Nothing was fabricated: titles, journals,
years and DOIs were written from the working knowledge of the authors and must be checked against the publisher record
before the manuscript leaves the repository. Remove the note once verified.

| key | what to verify |
|---|---|
| Hawker_2022 | FABDEM ERL 17:024016, DOI 10.1088/1748-9326/ac4d4f; the licence statement (CC BY-NC-SA 4.0) |
| Renno_2008, Nobre_2011 | HAND origin papers: volumes, pages |
| Johnson_2019 | NHESS 19, pages; the HAND-limits argument used in the Discussion |
| Zanaga_2022 | WorldCover 2021 v200 Zenodo DOI 10.5281/zenodo.7254221; licence CC BY 4.0 |
| Ronneberger_2015, He_2016, Iakubovskii_2019 | standard citations; smp version 0.5.0 |
| Neuenschwander_2019 | ATL08 RSE 221; note that Paper 1 used ATL13 for water and ATL08 for ground (p57) |
| Biancamaria_2016, SWOT_RiverSP_v2, Altenau_2021 | SWOT mission, the RiverSP v2.0 dataset citation with CRID, SWORD v16 |
| Lopes_1990, McFeeters_1996, Xu_2006 (Otsu_1979 Crossref-verified 2026-09-28) | the S1 speckle/threshold and the S2 water-index rules |
| Olofsson_2014 | area-estimation good practice: the reason areas carry semantics and are never called unbiased estimates |
| Roberts_2017, Pohjankukka_2017 | blocked cross-validation; Pohjankukka is already cited in Paper 1 |
| Lehnigk_2026 | GRL 10.1029/2025gl120832 — what exactly they mapped from SWOT during the Kakhovka flood; position Paper 3 against it |
| Vyshnevskyi_2023, Shumilova_2025, Kadam_2024 | Kakhovka literature reused from Paper 1's bibliography |
| CEOBS_2023, REACH_2023, UNEP_2023 | the ~620 km² (6–9 June) and ~180 km² (13 June) flooded-area figures: exact source (UNOSAT product id), AOI, date and reference-water definition; T16 flags these rows `literature_reported` |
| Lindsay_2016 | WhiteboxTools citation for the HAND computation (p42) |
| Paper1_Nikoriak_2026, Paper2_Nikoriak_2026 | series papers: final titles, status, DOIs |
| Yi_2025 | Crossref-verified 2026-09-28: **8 authors** (Yi, Li Hao-si, Han, Sneeuw, Yuan Chunyu, Song, Yeo, McCullough; the 2026-09-26 entry had 6 and two wrong given names); WRR 61, e2024WR038314; the initial breach flow 5.7 ± 0.8 × 10⁴ m³/s, 12.6 ± 1.1 m drop, 20.4 ± 1.4 km³ in 30 days — cited as a *different quantity* (initial breach discharge) next to our daily-mean effective release |
| Kadam_2024 | HEC-RAS 300 m breach scenario: 35 962 m³/s and 823 km² extent; extent definition/AOI |
| UNOSAT_3616_2023, UNOSAT_3623_2023 | 620 / 180 km2 web-verified via OCHA Flash Updates 6 and 7 and the HDX dataset FL20230606UKR; product ids still to confirm; ~620 km² = cumulative flooded LAND 6–9 June (ICEYE/S3/S2), pre-existing water separate, preliminary; ~180 km² on 13 June vs reference 3/5 June |
| Lehnigk_2026 (add) | peak stages 10–11 m by 8 June downstream, Kherson gauge 5.6 m on 8 June; bathymetry sets stage/timing; ICESat-2 ATL08 on the exposed bed; best bathymetry still ~1.4 m low at peak, worse ones 5.8–6.1 m |
| Monti_2024 | Crossref-verified 2026-09-26: "The Nova Kakhovka dam collapse flooding as seen from Sentinel-1 SAR satellite images"; first-author given name and pages VERIFY |
| Zhao_2021, Shen_2019, Grimaldi_2020 | Crossref-verified 2026-09-26 (Zhao et al. 2021 = "Deriving exclusion maps from C-band SAR time-series...", RSE 265, 112668) |
| Zheng_2018, Cohen_2019 | Crossref-verified 2026-09-26 (Zheng pages VERIFY) |
| Le_2026, Darnell_2008 | Crossref/web-verified 2026-09-26 (Le et al. 2026, J. Hydrol. 666, 134832; Darnell et al. 2008, CEUS 32, 268-277) |
| Valavi_2019, He_2024, Maiti_2022, Apicella_2025 | Crossref/web-verified 2026-09-26; note He_2024 is a weakly-supervised urban flood-mapping paper (ISPRS JPRS 207), not a label-noise survey; Apicella_2025 = Artificial Intelligence Review 58(10), article number/DOI still to add |

Also verify in the text: the Kherson gauge source (UkrHMC river yearbook 80805; 6–12 June flagged in the sea yearbook, Paper 1
§5.12), the EPSG:9902 offset at Kherson (0.216 m; p59 uses 0.22 m), and the SWOT overpass time (~11:00 UTC) vs the date-only gauge.
| Tucker_1979, Gao_1996, Wilson_2002, Feyisa_2014, Lacaux_2007, Breiman_2001, Belgiu_2016, MainKnorn_2017, Drusch_2012, Torres_2012, Pekel_2016 | Crossref-verified 2026-09-28 (index, classifier and sensor citations for the dashboard and T24–T26/FigS09) |
| Kozlova_2024, Pichura_2024, Pichura_2025, Maksymenko_2026, Magas_2026, Hryshchenko_2024 | Crossref-verified 2026-09-28: Kakhovka reservoir-bed literature (water occurrence, transformation, vegetation cover, sediments); read before citing them next to FigS08/S09 and T24–T25 — what each actually measured |
| Rikimaru_2002 | NOT in Crossref: Tropical Ecology 43(1):39–47 as commonly cited, the source of the Bare Soil Index; verify against the journal |
| Diek_2017, Milletari_2016, Small_2011, Lee_1980, Matheron_1963, Efron_1979, Efron_Tibshirani_1993, Schaefer_1990, Hohle_2009, Rosenfeld_Pfaltz_1966, ATL13_v6, Denker_2013, Stephens_2014, Hawker_2018; DOIs added to Lopes_1990, Lindsay_2016, Altenau_2021, Neuenschwander_2019 | merged 2026-09-28 from `docs/method_references_verified.bib` (method/index audit, `docs/METHOD_REFERENCES.md`); Crossref / DataCite verified; keys Wilson_Sader_2002, Belgiu_Dragut_2016, Main-Knorn_2017 adopted |
| Pedregosa_2011 | JMLR 12:2825–2830, no DOI, not in Crossref/OpenAlex — cite with the JMLR URL |
| EGG2015_release, EPSG_9902, Sacher_2019 | grey literature without DOI — listed in METHOD_REFERENCES.md only; add bib entries once the exact report / registry records are fixed |
