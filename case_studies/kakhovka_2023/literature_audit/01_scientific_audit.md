# 01 — Scientific audit of the Paper 3 manuscript (Kakhovka daily inundation reconstruction)

Reviewer-style audit written 2026-09-28 by Claude (Fable 5.1) for V. Nikoriak, before any manuscript text was
revised. Inputs: `publication/manuscript.md` (493 lines, generated 2026-09-25), `claims.md` (C01–C14),
`TERMINOLOGY.md`, `captions.md`, `tables/T*.csv`, `literature/theses.csv` (51 theses) and the local GeoHydroAI corpus
(**5 027 normalized papers counted at run time**, 1 354 158 SPECTER2 chunks in `flood_papers_768d`; 3 844 papers
with OpenAlex ids, 212 927 OpenAlex reference edges). Severity: **CRITICAL** = must be resolved before submission;
**MAJOR** = a reviewer will raise it; **MINOR** = wording/consistency; **INFO** = for the authors' record.

The literature verdicts (§6–§8) rest on `02_thesis_evidence.csv` / `03_source_ledger.csv` and the reading log in
`04_search_log.jsonl`; nothing below cites a paper that is not in those files or in `07b_references_unresolved.md`.

---

## 1. What the paper is, in one paragraph (auditor's reading)

The empirical spine is sound and unusual: a daily water surface built from SWOT RiverSP nodes and the Kherson gauge
(Paper 1's frame), projected on a class-bias-corrected seamless DEM (Paper 2) with an 8-connectivity rule and a
same-rule pre-breach regime, giving a *daily reconstructed series* of total water surface, newly inundated area, depth
and volume for 26 May – 10 July 2023, with a 40-draw spatial Monte-Carlo as the primary interval. Sentinel-1 dark-water
masks (11 dates), a disagreement ontology by surface class and height above the surface, night ICESat-2 ATL08 ground
heights along tracks, and the SWOT–gauge comparison are checks. RF20 surface classes and U-Net arms under two frozen
weak-label contracts show what EO products recover. The reservoir balance (C14) is bounded context. The manuscript
already states the evidence hierarchy (independent_physical > cross_sensor > weak_label_agreement > contextual) and
uses the frozen vocabulary almost everywhere. The problems found are of reporting and attribution, not of design.

## 2. CHECK A — the nominal run lies outside its own Monte-Carlo interval (MAJOR, reporting)

**Observed (T12, DNIPRO_CORRIDOR, 2023-06-07):**

| quantity | deterministic (nominal run) | MC p05 | MC p50 | MC p95 | MC shift of the median |
|---|---|---|---|---|---|
| A_new | 235.3 km² | 237.6 | **246.7** | 254.9 | +4.8 % |
| W_total | 779.1 km² | 781.4 | **790.5** | 798.7 | (+1.5 %) |
| V_new | 509.0 hm³ | 545.4 | **565.9** | 595.7 | +11.2 % |

All three nominal values lie **below the p05** of their own 40-draw distribution. The manuscript explains the mechanism
once (§3.3 L169–171: correlated DEM noise opens additional connections and adds depth, so the draw median lies above the
deterministic run and the interval is "reported next to the central value rather than centred on it"; C07 quantifies
the shift as +5 % area / +11 % volume). This is a *deliberate, documented nonlinear displacement*, not an error — but the
way the numbers are quoted hides it: the Abstract (L29–31, L35, L37) and §4.1 (L228–230, L253–254) write
"235 km² … (primary Monte-Carlo p05–p95 238–255 km²)" and a reader takes 235 to be the centre of 238–255. **The A_new
MC median (247 km²) appears nowhere in the manuscript** (it is only in claims.md C07); the "247 km²" at L242 is the HAND
variant — a different number that happens to coincide.

**Reviewer note / recommendation.** Two defensible reporting schemes exist; the paper must choose one and apply it
everywhere (Abstract, §4.1, Fig04 caption, T12 note, claims C01/C02/C07):

1. *(recommended)* **Report the MC median with its p05–p95 as the uncertainty-based estimate** — "A_new 247 km²
   [238–255] (MC median [p05–p95]; nominal run 235 km²)" — because the MC distribution is the only quantity that carries
   the error budget, and its median is the estimate a reader should carry away. The nominal run is then named
   separately as the *deterministic reference realisation* used for the maps and the per-cell products.
2. Keep the nominal value as the headline, but then every quotation must say what the interval is: "235 km² (nominal
   run; the 40-draw p05–p95 is 238–255 km² with median 247 km² — the interval is not centred on the nominal run because
   correlated DEM perturbations open additional connections)". Silence about the non-centring is what a reviewer will
   object to.

Either way the volume rule of TERMINOLOGY.md L54 ("always with their p05–p95 **and MC median**") must also hold for the
areas, since the same displacement applies. Until one scheme is applied consistently this stays **MAJOR**. The revised
manuscript (`09_…`) applies scheme 1 and records every change in `10_change_log.md`. The table values are untouched.

## 3. CHECK B–H findings (deterministic scan, `tools/paper3_audit/checks.py`)

| # | check | severity | location | finding | fix applied in 09 |
|---|---|---|---|---|---|
| 1 | B | MAJOR | manuscript.md:37 (Abstract) | V_new "509 hm³ (p05–p95 545–596 hm³)" **without the MC median 566 hm³** — violates TERMINOLOGY L54; §4.1 L238–241 is compliant | yes |
| 2 | B | MINOR | manuscript.md:291 | "653 hm³ on 9 June" (corridor + Inhulets, T21) with no interval; T12 has V p05–p95 for 9 June (corridor 487.5–539.3; Inhulets 189.7–206.7) | yes (interval from T12 rows stated per region) |
| 3 | C | MAJOR | captions.md:35–36 (Fig05) | forbidden phrase **"false SAR water"**, split across a line break ("false\nSAR water"); `tests/test_terminology_freeze.py` of floodstate-eo lowercases but does not collapse whitespace, so it passes silently | yes (caption rewritten in 09; the test should collapse whitespace — noted in 06) |
| 4 | C | MINOR | literature/theses.md:12, theses.csv TH-INT-04 | "breach discharge of" — describes Yi's quantity; not publication text but inside the freeze scope | wording noted; theses not edited (frozen input) |
| 5 | D | MAJOR | manuscript.md:319 | "the dark-water rule, not the flood" — a categorical cause for S1 'new water' after 18 June on fields and sand; no site-specific evidence (rain, ponding, registration, smooth surfaces, shadow) is tested (the paper itself says so at L334–335 and L472) | yes: "not supported as connected breach-induced inundation by the available terrain/WSE constraints; consistent with a known C-band look-alike behaviour on wet fields and sand; whether it is non-water is not tested here" |
| 6 | E | MINOR | manuscript.md:242, 244, 246, 368, 449 | bare noun "the peak" (five times) where TERMINOLOGY L12 wants a noun ("areal maximum" ≠ "peak stage") | yes |
| 7 | E | INFO | manuscript.md:29–32, 228–234, 432–436 | the 7 June maximum **is** written as reconstructed and between acquisitions; the Kherson stage maximum (8 June) is separated — compliant. The wording "the reconstructed areal maximum (7 June)" is kept; the revised text adds that the exact day is interpolation-dependent | strengthened |
| 8 | F | MAJOR→MINOR | manuscript.md:98 | "Paper 2 … validated it against night ICESat-2" — refers to the DEM of Paper 2, not to this paper's map, so it is admissible; but next to L186–187 ("not a validation of the inundation map") it invites confusion | yes: "assessed the DEM against night ICESat-2" |
| 9 | F | MINOR | Abstract L44 / Fig08 caption vs C06 | "within a few decimetres" (manuscript) vs "to a few centimetres (median)" (claims) — both are true of different statistics (median +0.02/+0.03 m; p10–p90 −0.31…+0.64 m, T15) | yes: "median agreement of a few centimetres, p10–p90 spread of a few decimetres" |
| 10 | G | INFO | §4.1 L285–290, C14, Fig09 caption | the ~4×10⁴ m³ s⁻¹ figure is named "daily-mean effective release … not an instantaneous breach discharge" everywhere; Yi 2025 and Kadam 2024 are called "different physical quantities" — **compliant** | kept |
| 11 | G | MINOR | §4.1 L294–295 / C14 / FigS07 caption / tables/README T22 | the hypsometry gap is stated four ways: −9 % at 17.5 m, −14 % at 13 m, −20 % at 11 m (text); "15–20 % at 11–13 m" (C14, FigS07); "8–12 % less volume" (tables/README T22) | yes: the T22 values are quoted once in 09; README/T22 discrepancy listed in 06 for the table generator |
| 12 | H | MAJOR | tables/T12.csv `definition_note` | "W_total = TOTAL water surface … the quantity comparable with operational 'flooded area' products" — contradicts TERMINOLOGY L26–27 and T16 ("operational flooded LAND is closer in kind to A_new, never validation") | cannot be edited here (generated table); listed in 06 for `p96_paper_tables.py` |
| 13 | H | MINOR | manuscript.md:227 | "180 km² … on 6 June" — this is our A_new, wrongly caught by the scanner as an external figure; the genuine UNOSAT ~180 km² (13 June) at L371 carries its semantics | no change |
| 14 | H | INFO | manuscript / T16 | NASA Harvest 410–420 km² (TH-INT-02) and Monti 2024 appear in the theses but not in the manuscript or T16; "Yale HRL 2023, 520 km²" sits in T16 row 39 with unknown semantics and **no bibliography entry** | 09 cites only sources with verified provenance; Yale HRL and NASA Harvest stay in 06 |
| 15 | — | MINOR | publication/README.md L5 | still says "C01–C12" (claims.md has C01–C14) | listed in 06 |
| 16 | — | MINOR | references_to_verify.md vs theses.csv | status disagreements: Maiti_2022, He_2024, Apicella_2025, Yi_2025 are "verified" in one file and "VERIFY" in the other; Vyshnevskyi_2023 / Shumilova_2025 the reverse | superseded by `07_references_verified.bib` / `07b` |

## 4. Kakhovka comparators — what quantity each published number is (CHECK H, C14)

Every value below was read in the corpus text (`kakhovka_numbers.csv`, `human_verified = yes`, number ids in
brackets). None of them is a validation of the reconstruction; each is a different quantity, AOI, date or definition.

**Downstream extents**

| source | value | what it is | AOI / date | reference water | comparable to |
|---|---|---|---|---|---|
| UNOSAT product 3616 (via CEOBS 2023; cited in Yailymov 2025 [N00364], KhNU 2025 [N00126], Kallas 2025 [N00343]) | ~620 km² | cumulative satellite-detected flooded **land** | Kherson oblast AOI, 6–9 June | pre-existing water separate | A_new (cumulative), not W_total; product sheet still unverified (07b) |
| UNOSAT 3623 (via OCHA Flash Update 7) | ~180 km² | flooded land on one date | 13 June vs reference 3/5 June | separate | A_new 13 June (108 km², p05–p95 114–129) — different AOI |
| Yailymov et al. 2025 (JSTARS) [N00356] | 473 km² (47 330 ha) | flooded land **as of 9 June**, by land-cover class (wetlands 29 400 ha, grassland 12 300, settlements 1 850, cropland 1 670, forest 970) | Kherson region below the dam incl. Inhulets; map of 5 June (pre) vs 9 June | pre-flood water map (S1 12-day composites, S2, Landsat-9) | A_new 9 June (183 km² corridor + 50 km² Inhulets) — note their "wetlands" class is where our *submergence* category lives |
| Kadam et al. 2024 [N00235/237/239] | 823 / 874 / 681 km² | HEC-RAS 2-D scenario maxima (300 m / 600 m breach) and 1-D maximum (8 June 16:00) | model domain, unspecified | n/a (model, includes channel?) | not an observation; the 823 km² "matched … remote sensing" without a metric |
| Zuo et al. 2024 (JSTARS) [N00379–383] | ~200 km² wetlands+crops, ~20 km² buildings damaged | Sentinel-3 OLCI NDWI change within three days; "water flow area more than twice" the pre-breach area, maximum around 9 June, back to previous level ~23 June | ~8 km either side of the river | NDWI water of the pre-event scene | a coarse (300 m) snapshot series — timing comparator (maximum around 9 June at 300 m) |
| Truth Hounds / PEJ, Ibatullin et al. (cited in Yailymov) [N00365/366] | 405 / 650 km² | affected / flooded area | unspecified | unspecified | context only; primary sources not in corpus |
| HDX (cited in Yailymov) [N00367] | 20 km² | remaining flooded 21 June | unspecified | unspecified | A_new 21 June 4 km² (1.7–4.0) — different AOI |

**Reservoir side**

| source | value | what it is |
|---|---|---|
| Vyshnevskyi et al. 2023 [N00010/011/027] | 2 155 km², 18.2 km³ at NRL 16.0 m; 22.6 km³ at 18.0 m; 11.4 km³ / 1 917 km² at 12.7 m; **19.8 km³ at 16.76 m on 6 June** (Operation Rules table) | design / operation-rules stage–area–volume |
| Yi et al. 2025 [N00439/414/440–442] | 21.0 km³ before the breach (17.3 m); **20.4 ± 1.4 km³ lost in 30 days**, 12.6 ± 1.1 m drop; initial breach flow (5.7 ± 0.8)×10⁴ m³ s⁻¹; reservoir area −280 km² (6–10 June), −1 000 (11–20), −460 (21–30) | gravimetry+altimetry+imagery discharge model — a 30-day total and an *initial* rate |
| Shumilova et al. (adn8655) [N00513/518] | **16.4 km³ released over two weeks**; 1 944 km² of bed exposed | modelled release (their Fig. S22) |
| KhNU 2025 [N00125] | 16.4 km³ to the sea in two weeks; flood flow 24 500–29 000 m³ s⁻¹ (citing [19]) | secondary |
| Lehnigk et al. (GRL) [N00002] | "∼8 km³" (citing Naddaf 2023); their GLOBathy simulation drained 14.5 km³ | secondary / model |
| Monti et al. 2024 [N00096] | "about 7.50 km³" released | derivation not in the text |
| Xu et al. 2024 [N00001] | 18 km³ | secondary (= design volume) |
| Novitskyi et al. 2024 [N00188/177] | 655.9 km² remaining on 17 June (31.8 %); ~430 km² after two months | reservoir remnant surface |

Consequence for C14: the manuscript's **14.7 km³ released in eight days (5→13 June)** sits between Shumilova's 16.4 km³
(two weeks) and Lehnigk's cited 8 km³, and below Yi's 20.4 km³ (30 days, nearly complete depletion from 21.0 km³).
These are different periods and different hypsometries; the manuscript's DEM hypsometry gap (−9 % at 17.5 m) is of the
same order as the spread between the published pre-breach volumes (18.2 design at 16.0 m; 19.8 at 16.76 m; 21.0 at
17.3 m). C14 must stay contextual and should say this explicitly (done in 09).

**Timing comparators for C01**: Lehnigk et al.: downstream stages rose from 1.5 m (3 June) to 10–11 m by 8 June;
Kherson 5.6 m on 8 June (SWOT 5–5.3 m); WSE back within 10 % of pre-flood after 350–375 h (≈21 June); backwater
≥150 km up the Inhulets. Zuo et al.: OLCI water area maximum "around 9 June". Kadam: 1-D peak 8 June 16:00; Kherson
depth 5 m on 8 June. None observes an areal maximum on 7 June; none contradicts it either — the 7 June areal maximum
remains a property of the reconstruction and must be reported as such (compliant in the draft; strengthened in 09).

## 5. Reference audit (`07_references_verified.bib`, `07b_references_unresolved.md`)

Of the 52 keys in floodstate-eo `docs/references.bib`: **37 verified** (36 CrossRef+OpenAlex with title/year match;
Zanaga_2022 via OpenAlex only — a DataCite DOI), of which 11 had no DOI in the bib and were resolved through the corpus
record's DOI (Rennó 2008, Nobre 2011, Johnson 2019, Ronneberger 2015, He 2016, Biancamaria 2016, McFeeters 1996,
Xu 2006, Olofsson 2014, Roberts 2017) or an OpenAlex title match (Altenau 2021, Lopes 1990, Otsu 1979, Neuenschwander
2019, Lindsay 2016 — see flags in `_work/references_verified.csv`). **15 unresolved**: the UNOSAT/CEOBS/REACH/UNEP
products, SWOT_RiverSP_v2 (dataset), Iakubovskii (software), Apicella 2025 (no DOI found), Paper1/Paper2 (series
manuscripts). Not one DOI was invented; unresolved keys may be cited only as grey literature with an access date.

**Method and index sources (07c).** The manuscript names 35 methods/indices/tools; 20 had no bibliography key at
all (NDVI, NDMI, BSI, AWEIsh, NDTI, Sen2Cor, random forest, Dice loss, RTC, Lee filter, kriging, bootstrap, POD/FAR/CSI,
NMAD, ATL13, EGG2015, EVRF2019, EPSG:9902, 8-connectivity, scikit-learn). Canonical first sources were checked against
the index formulas in `floodstate-eo/src/floodstate_eo/optical/sentinel_preprocess.py` and against CrossRef by DOI with
a title match: **26 verified** (7 also in the corpus), 5 grey (Rouse 1974, Rikimaru 2002, EVRF2019 report, EPSG entry,
EGG2015 release note), 1 not found (Pedregosa 2011, JMLR — no DOI). NDTI is the *turbidity* index of Lacaux et al. 2007
(the code says so), not the tillage index; BSI is the Rikimaru form (no DOI). Table: `07c_method_references_table.md`
(also written to `floodstate-eo/docs/METHOD_REFERENCES.md`); citations added in 09 (B-10 … B-15).

Corpus presence of the Kakhovka set: Yi 2025, Lehnigk (GRL 2025), Kadam 2024 (twice), Monti 2024, Vyshnevskyi 2023 and
2024, Shumilova et al. (as the accepted manuscript `adn8655` under its preprint title "A Farewell to a Dam…" — the DOI
field of that record is mis-parsed and must not be cited from the corpus metadata), Zuo 2024, Yailymov 2025,
Jiao 2025, Xu 2024, Gleick 2023, Novitskyi 2024, Kallas 2025, KhNU 2025. Shen 2019 (`remotesensing-11-00879`) and
Grimaldi 2020 (`10.1016_j.rse.2019.111582`) are in the corpus (the bundle's status file had them as "verified" from
CrossRef only). **Absent from the corpus**: UNOSAT/CEOBS/REACH/NASA Harvest products, Yale HRL, Zhao 2021,
Pohjankukka 2017, Altenau 2021, Neuenschwander 2019, Darnell 2008, Lindsay 2016, Tulbure 2022 — for these the audit
can verify metadata (07) but not read text; the corresponding claims cannot rise above
`SOURCE_FOUND_METADATA_UNVERIFIED` on their account.

## 6. Literature verdicts — what the screening changed

Screening: 91 atomic claims, 889 selected (atomic claim, paper) pairs, two Gemini lanes (3.1 / 3.5 flash-lite) plus a
leftover pass; every SUPPORTS/CONTRASTS row carries a quote verified verbatim against the corpus text (2 rejected of
~150 attempted, 1 %); all retained rows of the high-priority claims were read by the auditor; role changes are in
`overrides.yaml` with justifications. Statuses are rule-assigned (`02`, column `status_rule`); the per-thesis table is
in §9. Three findings changed the science, not just the citations:

1. **TH-MET-03.C is contradicted.** The manuscript implied that GeoFlood/FwDET/HAND-type tools impose drainage
   connectivity. They do not: HAND-type methods "do not preserve hydraulic connectivity" (Bates 2021, Annu. Rev. Fluid
   Mech.) and GeoFlood flags depressions "even if they are not connected with the main stem river" (Zheng et al. 2018).
   The paper's 8-connectivity rule is therefore its own addition to the index methods; 09 says so (B-09) and cites the
   connected-components precedent of Kulp & Strauss 2019 and the subgrid-connectivity result of Neal et al. 2012.
2. **TH-RES-11.A is qualified.** "Terrain as an input suppresses part of the cropland burden" is this paper's result;
   with HAND as a Bayesian prior, Tupas et al. (2023) found the opposite trade-off (fewer misses, slightly more false
   positives). 09 (B-16) states that the direction of the terrain effect depends on how terrain enters the model and on
   the label it is scored against.
3. **The Kherson peak differs by source.** The river yearbook gives 5.78 m; Gleick et al. (2023) report 5.68 m at
   15:00 on 8 June from the operational service; Lehnigk et al. (2026) cite 5.6 m (Naddaf 2023) and observe 5–5.3 m
   with SWOT. The 0.1 m spread is now stated (B-17) — it is of the same size as the closure residual budget (σ 0.05 m).

Lesser qualifications: reference-water definitions vary across products (JRC seasonality > 5 months in DeepSARFlood;
a global permanent-water mask in Martinis et al. 2015; a pre-flood optical map in Yailymov et al. 2025; recurrent May
water on ≥ 3 dates here) — 09 keeps "reference water" as a named choice; Yi et al. (2025) state that reservoir
bathymetry is "unavailable" — the hypsometry gap of §4.1 has no published bathymetry to be checked against, which is
exactly the Paper 4 question.

## 7. Overclaims, logic and novelty

**Overclaims found (all fixed in 09, logged in 10):** the categorical "dark-water rule, not the flood" (D-01); the
unqualified nominal values next to non-centred intervals (A-01…A-05); "peak" without a noun; "validated it against
night ICESat-2" (F-01); the implicit inheritance of connectivity from HAND/GeoFlood (B-09). No "first", "novel",
"proves", "validates the map" or "ground truth" statement exists in the draft or in 09; U-Net metrics remain "agreement
with weak reference labels"; C14 remains "daily-mean effective release"; the 7 June maximum remains reconstructed.

**Logic.** The evidence hierarchy holds. Two chains are weaker than the text suggests and are now labelled: (i) the
submergence category rests on the physical argument (double bounce → dark once the canopy is under; Grimaldi 2020;
Jarrett et al. 2023) and on the a-priori normally-wet class — no site measurement of reed submergence exists; (ii) the
areal maximum on 7 June rests on interpolated node heights between the 6 and 9 June scenes — no observation and no
published series resolves it, and the stage/extent hysteresis that makes it plausible is a general floodplain property
(Fassoni-Andrade et al. 2023), not a Kakhovka measurement.

**Novelty (brief §14; wording never "first").** NQ1 — NO EVIDENCE FOUND IN CORPUS (8 of 82 title/abstract Kakhovka
papers hit the four vocabularies; all read; the daily series that exist are model outputs: Agerbeek 2024, Kadam 2024;
Lehnigk 2026 use the SWOT surfaces to evaluate a model; Zuo 2024 is an observed 300 m water-area series). NQ2 — PARTIAL
(InSAR coherence registers *where* the maximum lay between acquisitions, Refice et al. 2017; no extent/depth/volume on a
day). NQ3 — NO EVIDENCE (6 of 82 keyword hits; Yailymov 2025 separates land-cover classes of one flooded-land quantity).
NQ4 — NO EVIDENCE (1 of 82 mention ICESat-2: Lehnigk on the exposed bed). NQ5 — NO EVIDENCE (0 of 4 838 corpus papers
combine weak flood labels with spatially blocked evaluation; Sen1Floods11 studies block by event). Full statements
with denominators and closest papers: `novelty_verdicts.yaml` and `05` §C. The admissible wording is "to our knowledge
within the literature reviewed (5 027 papers; 146 on Kakhovka)"; a corpus is not the literature.

## 8. What should move to the Supplement

- RF20 detail (§3.5, §4.8, T09/T10/FigS04): agreement with the training reference only; keep one sentence in Methods.
- U-Net arm mechanics (§3.6 hyper-parameters, seed, loss; §4.10 block-size table): keep the three conclusions of §4.9
  in the main text, move the arm table and block-size sensitivity to the Supplement (C13 is methodological).
- Reservoir balance (§4.1 "Reservoir side", Fig09, FigS07, T21/T22): keep as *one bounded paragraph* of context with
  the comparator table of §4 above; the hypsometry discussion belongs to Paper 4.
- Superseded closure chain (§3.1 p59 sensitivity, T11): Supplement.

## 9. Per-thesis verdicts

(appended after screening and reading — see the end of this file)

## 10. Re-audit of bundle 21ba34c (2026-09-28, evening)

floodstate-eo rebuilt the manuscript with the Monte-Carlo median as the central value (T12b), added the design-curve
paragraph (T27–T27c, FigS10) and the drawdown paragraph (T23–T26, FigS08–S09), and extended the Limitations. Verdict:
- **Numbers**: every value in the two new paragraphs reproduces from the synced tables (13.48 km³ at 13.93 m on 8 Feb;
  21.33 at 17.62 m on 5 May; 20.14 on 5 June; 37 811 m³ s⁻¹ on 7 June from the Rozumivka design-curve balance; head
  16.70 / 6.03 / 1.53 m; IoU 0.98/0.97/0.85; 1702 vs 648 km²; reeds 47 % / 34 %). CHECK A is closed by the new reporting
  scheme; the 37 811 vs 40 057 m³ s⁻¹ comparison is correctly labelled "same order", not validation.
- **Logic**: one new contradiction — the mechanism of the median displacement is stated in §3.3 but called "not yet
  diagnosed" in §4.1 and §6 (S-01/S-02). The design-curve paragraph honestly states its two assumptions (level pool;
  held SWOT outlet value) and gives a range where the surface is sloped — acceptable as context.
- **Terminology**: forbidden phrases 0; "dark-water rule, not the flood" and "validated … ICESat-2" remain (D-01, F-01);
  four bare "peak" (E-04…E-07). VERIFY on Lehnigk/Yi can be dropped (A-02b); UNOSAT VERIFY stays.
- **Literature**: the new paragraphs cite no literature; 09 carries the drawdown context with the corpus-verified
  comparators (Magas 2023; Tsiupa 2023; Novitskyi 2024; Kuzemko 2024/2025; Tutova 2025; Pichura & Potravka 2025) and
  the look-alike caveat (no source for wet sediment; B-22).
`09_manuscript_literature_revised.md` is now built on 21ba34c: 36 documented changes; 9 earlier entries are recorded as
superseded because the bundle applied them itself.
