# Literature-audit actions for floodstate-eo — round 2 (bundle 21ba34c, 2026-09-28 evening)

Source: GeoHydroAI audit, `paper_unet-case-kakhovka/literature_audit_paper3/` (distro **Ubuntu**), copied here as
`case_studies/kakhovka_2023/literature_audit/`. Every change below is also applied in
`literature_audit/article/Paper3_final.md` / `.docx` (change log `10_change_log.md`, incl. the FA-* final-assembly edits).

Closed by 7231e21/21ba34c, nothing left: MC median as central value (T12b); T12 `definition_note`; Fig05 caption;
FigS08 caption + `yi2025_digitised_km2`; Yale HRL row; Kherson peak spread; all numbers of the two new §4.1 paragraphs
reproduce from T12b/T23/T24/T27/T27b.

## Open (12 items; item 11 closed)

| # | where | current text | proposed | why |
|---|---|---|---|---|
| 1 | §4.1 L276 | "the nominal run in brackets; the cause of the offset is not yet diagnosed." | "… in brackets. The mechanism is the one of §3.3 — correlated DEM perturbations open additional connections and add depth (Cunha et al. 2012; Hawker et al. 2018) — but which error term carries most of the shift has not been attributed." | §3.3 L170–171 already states the mechanism; §4.1/§6 contradict it (S-01) |
| 2 | §6 L505 | "… below its own Monte-Carlo p05 on the peak days for a reason not yet diagnosed;" | "… — the mechanism is the connection-opening effect of correlated DEM perturbations (§3.3), but its attribution to the individual error terms is open;" | same (S-02) |
| 3 | §4.2 L350 | "at 3 km²: the dark-water rule, not the flood." | "at 3 km²: these detections are not supported as connected breach-induced inundation by the available terrain and water-surface constraints. Their pattern — fields and sand far above any water surface of the event — is consistent with a known C-band look-alike behaviour (smooth or wet bare surfaces and shadow scatter like water; Shen et al. 2019), but whether they are non-water, local ponding after rain or water outside the assumed connectivity is not tested here (§4.3)." | categorical cause not tested (D-01; TERMINOLOGY §disagreement) |
| 4 | §1 L99 | "and validated it against night ICESat-2;" | "and assessed it against night ICESat-2 ground heights by land-cover class;" | next to "not a validation of the map" (F-01) |
| 5 | §1 L71–72 | "(VERIFY)" after Lehnigk stage error; "5.7 × 10⁴ m³ s⁻¹, VERIFY" after Yi | drop both VERIFY | read in the corpus: Lehnigk 1.4/5.8/6.1 m, stages 10–11 m by 8 June; Yi (5.7 ± 0.8)×10⁴ m³ s⁻¹ (quotes in 02_thesis_evidence.csv) |
| 6 | §4.1 L235, §5 L465 | "… Lehnigk et al. 2026 report from SWOT are consistent with it, VERIFY)"; "… peak stages by 8 June from SWOT, VERIFY)" | drop VERIFY; "from the same SWOT data" | verified (A-02b, B-04) |
| 7 | §4.1 L245, L247, L249; §4.6 L399 | "at the peak", "the peak is 347 km²", "the peak is 163 km²", "at the peak (terrain_reconstructed)" | "at the reconstructed areal maximum" / "the areal maximum is …" | TERMINOLOGY L12: never "peak" without a noun (E-04…E-07) |
| 8 | §4.1 L237 | "196 km² on 9 June" (T12b p50 = 196.5) | 197 km², or state the rounding rule | every other value rounds half up (189, 247, 118, 39, 3) |
| 9 | publication/README.md L5 | "C01–C12" | "C01–C14" | claims.md has 14 |
| 10 | §4.1 / FigS07 caption / tables/README T22 | gap as "14–20 %" and "8-12 % less volume" | quote T22 once: −9 % (17.5 m), −14 % (13 m), −20 % (11 m) | three wordings for one table |
| 11 | tests/test_terminology_freeze.py | — | **closed in 21ba34c** (VALIDATION §1: whitespace-insensitive) | — |
| 12 | Abstract L44 / C06 | "within a few decimetres" vs "to a few centimetres (median)" | "to a few centimetres in the median (p10–p90 spread of a few decimetres)" | both statistics of T15 (F-02) |
| 13 | §4.7–4.8 (U-Net) | Fig03 (U-Net weak-label experiment) is never cited in manuscript.md; captions.md defines it | cite it where T06/T07b are discussed — the final article does this in §4.9 ("*Label effect* (Fig03; paired differences in T06 and T07b)", edit FA-04) | a figure in `figures/` without a text reference |

## Literature to add (all corpus-read, quote-verified; keys in `literature_audit/07_references_verified.bib`,
`07c_method_references_verified.bib` and `citation_keys.yaml`)

- §1: Yailymov 2025 (473 km² flooded land 9 June), Zuo 2024 (Sentinel-3 series), Agerbeek 2024 (NRT model vs ICEYE),
  Johnson 2019 (HAND limits), Hawker 2018 (correlated DEM error) — B-01; Singha 2020, Martinis et al. 2018,
  Tsyganskaya 2018 — B-02.
- §2: Normandin 2024, Yu 2024 (SWOT accuracy) — B-05; Iqbal 2023, Baugh 2013, Yamazaki 2019 (FABDEM/canopy bias) —
  B-06; index and method sources — B-10…B-15.
- §3.2: Bates 2021 + Zheng 2018 (HAND/GeoFlood do NOT preserve connectivity → the 8-connectivity rule is this paper's
  addition; Kulp & Strauss 2019, Neal 2012, Guo 2025) — B-09; Grimaldi 2020 + Jarrett 2023 (submergence signal) — B-18.
- §3.3: Cunha 2012, Hawker 2018, Darnell 2008 — B-07. §3.4: Schaefer 1990, Stephens 2014 — B-14.
- §4.1 (drawdown context): Magas 2023, Tsiupa 2023, Novitskyi 2024, Kuzemko 2024/2025, Vyshnevskyi 2024, Tutova 2025,
  Pichura & Potravka 2025; no source for wet mud as a C-band look-alike — B-22.
- §4.6: Yailymov 2025, Zuo 2024 as literature_reported comparators — B-03.
- §5: DeVries 2020, Giordan 2018, Tarpanelli 2022, Refice 2017 (revisit undersampling; coherence as the closest
  precedent) — B-04; Fassoni-Andrade 2023 (hysteresis) — B-20; Tupas 2023 (opposite HAND trade-off), Garg 2023,
  Bonafilia 2020, Katiyar 2021, Sharma 2025 — B-16; Amitrano 2024, Wagner 2020 (exclusion masks) — B-08.

## The article and the audit package (what was copied)

`case_studies/kakhovka_2023/literature_audit/` — the ten deliverables 01–10 (+07b, 07c), the audited inputs
(`atomic_claims.yaml`, `theses_supplement.yaml`, `overrides.yaml`, `novelty_verdicts.yaml`, `citation_keys.yaml`,
`revisions.yaml`, `supplementary_pairs.csv`, `kakhovka_numbers.csv`), `run_manifest.json`, `completion_report.md`,
`README_BUILD.md` (how each file was made, the rebuild command sequence, what the article contains) and `article/`:
**`Paper3_final.md` and `Paper3_final.docx`** — the revised text with all 19 figures, all 39 tables (25 printed, 5 as
compact column views, 9 long ones as CSV pointers, 13 uncited ones under "Supplementary tables"), 123 verified references
and the 12 unresolved keys listed separately; `figures/` (PNG) and `tables/` (every CSV + the metric README). No table cell
was altered; text changes are the 36 audit revisions + 4 final-assembly edits, all in `10_change_log.md`. The `_work/`
intermediates (35 MB) stay in the GeoHydroAI repo.
