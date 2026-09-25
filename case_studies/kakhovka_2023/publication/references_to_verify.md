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
| Lopes_1990, Otsu_1979, McFeeters_1996, Xu_2006 | the S1 speckle/threshold and the S2 water-index rules |
| Olofsson_2014 | area-estimation good practice: the reason areas carry semantics and are never called unbiased estimates |
| Roberts_2017, Pohjankukka_2017 | blocked cross-validation; Pohjankukka is already cited in Paper 1 |
| Lehnigk_2026 | GRL 10.1029/2025gl120832 — what exactly they mapped from SWOT during the Kakhovka flood; position Paper 3 against it |
| Vyshnevskyi_2023, Shumilova_2025, Kadam_2024 | Kakhovka literature reused from Paper 1's bibliography |
| CEOBS_2023, REACH_2023, UNEP_2023 | the ~620 km² (6–9 June) and ~180 km² (13 June) flooded-area figures: exact source (UNOSAT product id), AOI, date and reference-water definition; T16 flags these rows `literature_reported` |
| Lindsay_2016 | WhiteboxTools citation for the HAND computation (p42) |
| Paper1_Nikoriak_2026, Paper2_Nikoriak_2026 | series papers: final titles, status, DOIs |

Also verify in the text: the Kherson gauge source (UkrHMC river yearbook 80805; 6–12 June flagged in the sea yearbook, Paper 1
§5.12), the EPSG:9902 offset at Kherson (0.216 m; p59 uses 0.22 m), and the SWOT overpass time (~11:00 UTC) vs the date-only gauge.
