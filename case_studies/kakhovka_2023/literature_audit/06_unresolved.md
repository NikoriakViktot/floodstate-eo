# 06 — Unresolved items (nothing here was silently repaired)

Written 2026-09-28. Each item names what is missing, what was checked, and what the authors must decide.
Statuses per thesis are in `02_thesis_evidence.csv`; this file lists only what the audit could **not** close.

## A. Sources named in the bundle that are not in the corpus (text unread → status capped)

| key / placeholder | needed by | what was checked | consequence |
|---|---|---|---|
| Zhao_2021 (exclusion maps, RSE 265) | TH-INT-06.C, TH-MET-09, TH-DIS-03 | CrossRef+OpenAlex resolve the DOI (07); no corpus record by DOI or title | METHOD_FROM/DEFINITION for "exclusion maps" rests on the verified citation only → `SOURCE_FOUND_METADATA_UNVERIFIED` unless the paper is read |
| Martinis_2022 (reference water, RSE) | TH-DAT-01.C, TH-MET-05.A, TH-RES-10.A | DOI resolves; not in corpus | as above |
| Wagner_2026 (GFM service, RSE) | TH-DAT-01.C, TH-MET-05.A, TH-DIS-03.A | DOI resolves; not in corpus | as above |
| Valavi_2019 (blockCV) | TH-MET-14.A, TH-RES-13.A | DOI resolves (title ratio 0.906); not in corpus | as above |
| Pohjankukka_2017, Ploton_2020, Karasiak_2022, Wadoux_2021 | TH-MET-14.A, TH-RES-13.A | Pohjankukka DOI resolves; Ploton/Karasiak/Wadoux no bib entry and no corpus record | spatial-CV block-size argument rests on Roberts 2017 (in corpus, verified quote) |
| Poulter & Halpin 2008, Williams & Luck-Vogel 2020 | TH-MET-03.A/B | no bib entry, no corpus record | connectivity-bathtub precedent must be cited from outside the corpus or dropped |
| Wechsler_2007, Fisher & Tate 2006, Darnell_2008 | TH-INT-10.B, TH-MET-06.A | Darnell DOI resolves; none in corpus; Hawker 2018 (in corpus) covers the DEM-simulation argument | cite Hawker 2018 (read) + Darnell (metadata only) |
| Neuenschwander_2019 (ATL08), Liu_2021 | TH-DAT-05.B, TH-MET-10.A, TH-RES-06.A | Neuenschwander DOI found via OpenAlex title search; not in corpus | ATL08 accuracy statements rest on secondary citations in corpus papers |
| Altenau_2021 (SWORD), SWOT_RiverSP_v2 (dataset) | TH-DAT-03.A, TH-MET-01.C | Altenau DOI found via OpenAlex; product document has no DOI | dataset documentation must cite the PO.DAAC record with CRID and access date |
| Kaufman_2012, Apicella_2025 | TH-INT-08.A, TH-RES-12.A | Apicella: no DOI found in CrossRef/OpenAlex (arXiv 2401.13796 in the bib note); Kaufman not in corpus | leakage definition cited from outside the corpus; keep the wording "not independent" |
| Schaefer_1990, Milletari_2016, Denker_2015 (EGG2015), EVRF2019/BKG, EPSG:9902, UkrHMC yearbooks, Lindsay_2016, Iakubovskii_2019 | definitions / dataset documentation | not in corpus (Lindsay DOI found via OpenAlex) | cite as standard references; nothing to verify in text |
| Kulp & Strauss 2018 (CoastalDEM), Zhao 2018, MERIT (Yamazaki) | TH-DAT-05.C | not in corpus; the vegetation-bias claim is supported by corpus papers (07 verified quotes) | fine without them |

## B. Operational / grey sources (no DOI; product semantics unverified)

| item | what the bundle says | what was verified | decision needed |
|---|---|---|---|
| UNOSAT product 3616 (~620 km², 6–9 June) | cumulative satellite-detected flooded land, pre-existing water separate (via CEOBS 2023 / OCHA FU6) | CEOBS URL reachable (http 200); the figure is *cited* in three corpus papers (Yailymov 2025, Kallas 2025, KhNU 2025); the product sheet (sensors ICEYE/S3/S2?, AOI polygon, reference-water dates) was **not** obtained | obtain the UNOSAT/HDX product sheet (FL20230606UKR) and cite it with product id + access date; until then T16 row 36 stays `VERIFY` |
| UNOSAT 3623 (~180 km², 13 June, reference 3/5 June) | via OCHA FU7 | not obtained | as above |
| NASA Harvest / Planet 410–420 km² (7 June) | TH-INT-02.B | no source in corpus or bib | either find the note (NASA Harvest blog, 2023) and cite it as grey literature, or drop the figure from the paper (it is not in the manuscript now) |
| "Yale HRL 2023, 520 km²" (T16 row 39) | unknown semantics | no bib entry, nothing in corpus | drop from T16 or document the report |
| REACH_2023, UNEP_2023 | situational overview / rapid assessment | not obtained | cite only if the report is in hand |
| Truth Hounds / PEJ 405 km², Ibatullin et al. 650 km² | cited in Yailymov 2025 | primary sources not in corpus | cite as "cited in Yailymov et al. 2025" or omit |
| Ukrhydroenergo daily releases, G-REALM, Nikopol press levels | TH-RES-14.C | no documentation in corpus (Mon23-147 gives 16.79 m BS on 5 June; Monti 2024 mentions Theia/altimetry series) | add dataset citations (G-REALM DOI, Ukrhydroenergo source) to the data statement |

## C. Contradictions and inconsistencies inside the bundle (author decision; tables not edited here)

1. **T12 `definition_note`** says W_total is "the quantity comparable with operational 'flooded area' products" —
   TERMINOLOGY.md L26–27 and T16 say the opposite (flooded *land* ≈ A_new). Fix in `p96_paper_tables.py`.
2. **Hypsometry gap stated four ways** (−9/−14/−20 % in text; "15–20 % at 11–13 m" in C14/FigS07; "8–12 %" in
   tables/README T22). The revised manuscript quotes the T22 values; README/T22 must be reconciled by the generator.
3. **Nominal run outside its MC interval** (A_new 235 < p05 238; W_total 779 < 781; V_new 509 < 545): a reporting
   choice (see 01 §2); the revised manuscript uses "MC median [p05–p95] (nominal run X)". Authors must confirm this
   scheme or the alternative and regenerate the Abstract/Fig04 caption/T12 note accordingly.
4. **Released volume 14.7 km³ (5→13 June)** vs Shumilova 16.4 km³ (two weeks), Yi 20.4 ± 1.4 km³ (30 days, from 21.0),
   Lehnigk's cited ~8 km³, Monti 7.5 km³: not a contradiction (different periods/hypsometries) but the manuscript
   must say so next to C14 (done in 09) and Paper 4 must resolve the hypsometry.
5. **Reservoir volume on the eve of the breach**: 18.9 km³ (manuscript, sloped surface on the seamless DEM) vs 19.8 km³
   (Operation Rules at 16.76 m, Vyshnevskyi 2023), 19.9 km³ at 16.79 m BS (Mon23-147), 21.0 km³ at 17.3 m (Yi 2025),
   design 21.1 km³ at the same outlet level (T21). The −9 % gap at full pool is therefore also visible against the
   published operation-rules numbers — say so.
6. **Abstract "within a few decimetres" vs C06 "few centimetres (median)"** — both true (median vs p10–p90); one
   sentence must carry both statistics (done in 09).
7. **publication/README.md** still says "C01–C12".
8. **Terminology test** (`tests/test_terminology_freeze.py`, floodstate-eo): scans line by line; "false\nSAR water"
   in captions.md Fig05 escapes it. Collapse whitespace before matching (`re.sub(r"\s+", " ", text)`).
9. **references_to_verify.md vs theses.csv** status tags disagree for Maiti/He/Apicella/Yi/Vyshnevskyi/Shumilova;
   `07_references_verified.bib` supersedes both.
10. **Monti 2024 pages**: CrossRef gives "50-50" (an article number in a page field); Lehnigk et al.: CrossRef year
    2026, vol. 53, e2025GL120832 (the corpus record has no year; the corpus id says 2025 from the DOI prefix).
11. **Yi_2025 author list**: the bib names six authors; CrossRef lists eight (Yi, Li, Han, Sneeuw, Yuan, Song, Yeo,
    McCullough). `07_references_verified.bib` carries CrossRef's list; `docs/references.bib` should be corrected.
12. **Shumilova_2025**: the corpus record `shumilova_farewell_to_a_dam_adn8655` is the accepted manuscript (Science
    adn8655) under its preprint title, with a mis-parsed DOI (Nature Ecol Evol). Quote from it only with the caveat
    that page/figure numbering differs from the Science version; cite the Science DOI from 07.

## D. Claims that should be weakened, removed or re-scoped (see 01 §3 and 09)

- L319 "the dark-water rule, not the flood" → not supported as connected breach-induced inundation; cause not tested.
- Any sentence quoting 235 / 779 / 509 with its interval must carry the MC median (247 / 790 / 566) and the
  non-centring statement.
- TH-INT-02 NASA Harvest figure and T16 "Yale HRL" row: no provenance → not in the revised manuscript.
- TH-MET-03 connectivity precedent: cite Poulter & Halpin / Williams & Luck-Vogel only if the authors have the papers;
  the corpus supports "planar inundation over-predicts without connectivity" only through review-level statements
  (see 02 for the retained rows).
- TH-MET-14 / TH-RES-13 block-size choice: Roberts 2017 supports blocking by autocorrelation range (verified quote);
  the Ploton/Karasiak/Valavi statements are not verifiable in the corpus — cite them as metadata-verified only.

## E. Open scientific questions the literature does not settle (for the Discussion)

- Whether the 54 km² of S1-only detections ≥ 5 m above the reconstructed surface are non-water (look-alikes) or
  disconnected water: the literature establishes the mechanisms (wet soil, sand, shadow — see TH-INT-06.B /
  TH-RES-04.B rows) but not this site; ICESat-2 constrains only the DEM-bias explanation along tracks.
- Whether the areal maximum fell on 7 June: no acquisition observes it; Zuo et al. (300 m OLCI) see the water-area
  maximum "around 9 June", Lehnigk et al. see stage maxima by 8 June — a *stage/extent lag* the reconstruction
  implies and no published series resolves at daily resolution.
- The pre-breach reservoir volume (18.9–21.1 km³ across sources) and hence the released volume: Paper 4.

## F. Reservoir-drawdown results added 2026-09-28 (T23–T26, FigS08–S09; theses TH-RES-16..18)

Screened with local Ollama (mistral-nemo) because both Gemini lanes returned 503 "high demand" and the daily quota was
nearly spent; the quote gate rejected 5 of 27 SUPPORTS quotes (19 %, vs 0–2 % for Gemini) and several retained rows were
irrelevant — every row was re-read and corrected in `overrides.yaml`.

1. **T23 column `yi2025_S1_km2` (2089.2 / 1848.84 / 824.76 / 369.42 km²) is not in Yi et al.'s text.** The text gives
   2125 km² on 30 May and decreases of ~280 / ~1000 / ~460 km² for 6–10 / 11–20 / 21–30 June (→ ~1845 / ~845 / ~385 km²),
   and the water maps are Sentinel-1 SDWI **and** Sentinel-2 mNDWI, not S1 only. If the values were digitised from a
   figure, name the figure and say "digitised"; otherwise replace them with the text values. The FigS08 caption in 09b
   now quotes the text (B-21). Fix in the floodstate-eo table generator.
2. **Wet mud as a SAR look-alike** (TH-RES-16.A) has no source in the corpus: a whole-corpus sentence probe (mudflat /
   exposed sediment / lake bed × SAR × water-like) found 0 papers. 09 labels it as consistent with the documented
   behaviour of smooth bare surfaces (Shen et al. 2019), not as established. Candidate literature to obtain: SAR studies
   of intertidal flats and drained lake beds.
3. **Published remnant areas disagree by definition:** Magas et al. 2023 379.7 km² (8 Sept, incl. channel 133 km²),
   Tsiupa et al. 2023 1.63 km² open water + 110 km² wet (6 Sept), Novitskyi et al. 2024 ~430 km² (August) and 655.9 km²
   (17 June, a state estimate). The two Monitoring-2023 conference papers have no DOI in the corpus record — cite with the
   conference name or drop.
4. **General revegetation precedent** (TH-RES-17.B): only the Kakhovka case is in the corpus; a dam-removal precedent
   (e.g. Elwha) would have to come from outside.

## G. Re-audit of the floodstate-eo bundle 21ba34c (2026-09-28, evening)

Closed upstream (no action left): T12 `definition_note` now matches TERMINOLOGY (§C.1); MC median as the central value
with the nominal run in brackets, daily T12b (§C.3); Fig05 caption uses the frozen term (§C.8 wording); FigS08 caption
quotes Yi's text (~845 km² by 20 June, S1 and S2) and T23's column is `yi2025_digitised_km2` (§F.1); the "Yale HRL"
row is gone from T16; Kherson peak spread (5.78 / 5.68 / 5.6 m) is stated (§C.6 analogue); Lehnigk/Yi numbers quoted
correctly. All numbers of the two new §4.1 paragraphs were checked against T12b, T23, T24, T27, T27b: they match.

Still open in the bundle (applied in 09 / 09b, listed in 10):
1. §4.2 "the dark-water rule, not the flood" (D-01) — categorical attribution.
2. §1 "validated it against night ICESat-2" (F-01).
3. VERIFY flags on Lehnigk 2026 (§4.1, §5) and Yi 2025 (§1) — both read and quote-verified in the corpus; only the
   UNOSAT flags should stay.
4. **New internal contradiction**: §3.3 states the mechanism of the median shift (correlated DEM noise opens
   connections and adds depth) while §4.1 and §6 say "the cause of the offset is not yet diagnosed" (S-01, S-02
   reconcile: mechanism known, per-term attribution open).
5. Bare "peak" ×4 (§4.1, §4.6) — E-04…E-07.
6. `publication/README.md` still says "C01–C12"; hypsometry gap now stated as "14–20 %" in one place and −9/−14/−20 %
   in another (T22 values are the reference).
7. Rounding: A_new on 9 June is written 196 km² (T12b p50 196.5) while every other value rounds half up (189, 247, 118,
   39, 3) — use 197 or state the rule.

## H. Re-audit of bundle 2dca5ae / 38e3375 (2026-09-28, late)

Closed upstream: §G items 1–5 except the two bare "peak" of E-02/E-03; item 6 (README); item 7 accepted as
round-half-to-even with the rule stated in the preamble. Newly found: Fig08 caption "within a few decimetres" (F-03);
§6 L-01 sentence now false after the reference verification; FigS07 caption rounding of the T22 gap. The B-* literature
paragraphs and A-06/A-07 remain outside the bundle — see `revisions_for_template.md`. Four citation years corrected to
CrossRef (Bates 2022, Tuan 2021, Refice 2018, Arcos González 2024); `07d_corpus_references.bib` supplies the 49 keys
`references.bib` lacks. Still open as before: the figure number of Yi et al.'s digitised series; "19 m near the dam"
has no source; the nominal-below-p05 attribution needs a diagnostic run.
