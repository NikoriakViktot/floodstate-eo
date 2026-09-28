# Validation of the 2026-09-28 additions (reservoir drawdown, design hypsometry, MC median, literature audit)

Scope: everything added or changed on 2026-09-28 (commits `7932bd0` → this one). Each item names the check, the result and where
the item lands in Paper 3. Rule of the bundle: every number in the manuscript resolves to a table cell (`fill_manuscript.py`);
tables are rebuilt from committed inputs only (`p96 --check`); claims are rendered from `evidence_matrix.csv`.

## 1. Automatic checks (all run after the last edit)

| check | command | result |
|---|---|---|
| tables reproduce from inputs | `p96_paper_tables.py --check` | OK (39 tables, 93 sources) |
| manuscript placeholders | `fill_manuscript.py` | 190 placeholders, 0 unresolved |
| claims register | `fill_evidence.py`, `render_claims.py` | filled, 14 claims, no unresolved |
| test suite (incl. terminology freeze, gate, tables manifest) | `pytest` | 45 passed |
| terminology test now whitespace-insensitive | `tests/test_terminology_freeze.py` | Fig05 caption reworded; no forbidden phrase in any file |
| dashboard pages | Streamlit `AppTest` on all 8 pages | no exceptions; headline metrics 790 / 247 km² (MC median) |
| Monte-Carlo reproduction | p95e `--days all` vs the committed 9-key-date run | max abs difference 0.0 on all 27 (date, region) rows; components identical |
| lint on changed files | `ruff --select F,E9` | clean except two pre-existing unused imports (`fill_evidence.py: re`, `streamlit_app.py: C`) |

## 2. Numbers in prose vs tables (hand-checked)

| statement | source cell | value | status |
|---|---|---|---|
| A_new maximum 247 [238–255] km², nominal 235 | T12 corridor 06-07 | 246.7 / 237.6 / 254.9 / 235.3 | OK |
| W_total 790 [781–799], nominal 779 | T12 | 790.5 / 781.4 / 798.7 / 779.1 | OK |
| V_new 566 [545–596], nominal 509 | T12 | 565.9 / 545.4 / 595.7 / 509.0 | OK |
| nominal below MC p05 on the peak days | T12b corridor | 12 of 46 days flagged, 06-06 … 06-17 | OK (stated as undiagnosed) |
| C02 statement (hand-written) | evidence_matrix | 488 → ~790; ~247; ~566; nominal in brackets | OK |
| S1 vs model IoU 0.98 / 0.97 / 0.93 / 0.85 | T23 | 06-01 0.98, 06-08 0.97, 06-09 0.93, 06-13 0.85 | OK |
| S1 dark vs S2 water 20–21 June | T23 | S1 1702 (06-20), 2077 (06-21); S2 648 (06-20) | caption corrected (was "2077 vs 648") |
| Yi 2025 areas | T23 `yi2025_digitised_km2` | digitised from a figure, S1+S2 | renamed + captioned; figure number VERIFY |
| filling 13.5 → 21.3 km³, 7.9 of 22.7 km³ stored | p95i manifest / T27b 02-08, 05-05 | 13.48 → 21.33; 7.85 / 22.68 (34.6 %) | OK |
| design-curve release 12 / 38 / 20 / 19 ×10³ m³/s | T27b `Q_out_design_rozumivka_m3s` 06-06..09 | 11 797 / 37 811 / 20 051 / 19 334 | OK |
| sloped-surface release ~40 ×10³ | T21 06-07 | 40 057 | OK |
| head across the dam 16.7 → 6.0 → 1.5 m | T27b 05-31, 06-06, 06-14 | 16.70 / 6.03 / 1.53 | OK |
| hypsometry gap −9 / −14 / −20 % | T22 17.5 / 13 / 11 m | −8.5 / −14.4 / −20.4 | C14, FigS07 caption, T22 caption aligned (README said 8–12 %) |
| reach volumes add up to Table 19 | T27 `reach_sum_minus_total_km3` | max |diff| 0.01 km³ | transcription OK |

## 3. Every new figure and table is referenced

Before this validation the manuscript cited none of T23–T27c and FigS08–FigS10 (orphans). Added to §4.1 (two context
paragraphs after the reservoir balance) and §6 (limitations). Now: T12b (§4.1 uncertainty paragraph), T21–T22 (balance), T23–T26 +
FigS08–FigS09 (drawdown seen from orbit), T27–T27c + FigS10 (design curve), all cited. Older supplementary items FigS01–S04, S06 and
T02–T08b, T10b–c, T17b are cited in captions.md and the tables README but not in the manuscript body — pre-existing, listed here
for the next pass, not changed.

## 4. Where each addition lands in Paper 3

| addition | place | status in the paper |
|---|---|---|
| MC median as the reported central value; daily MC (T12b); nominal run in brackets | Abstract, §4.1, §4.1 uncertainty paragraph, C01–C03, C07, Fig04, dashboard | **result** (changes the headline numbers: 247 / 790 km², 566 hm³) |
| offset nominal < p05 | §4.1 uncertainty paragraph, §6 | stated, cause undiagnosed |
| design hypsometry (Table 19 / Figs 13–15, reaches, design levels) — T27, FigS10 a–b | §4.1 "design curve as the classical reference" | **context**, no DEM, nothing fitted |
| spring filling on the design curve with the DniproHES balance — T27c, FigS10 c | same paragraph | context; the HPP outflow is a residual |
| design-curve release during the drawdown (Rozumivka level) — T27b | same paragraph, next to the T21 figure | context / cross-check of the same order (38 vs 40 ×10³ m³/s); not a validation |
| outlet = pool above the dam; head across the dam; Kherson alongside — T27b | same paragraph | context |
| drawdown maps: model / S1 / S2 — T23, FigS08 | §4.1 "drawdown seen from orbit" | context, no claim (audit TH-RES-16: PARTIAL for "wet mud = dark") |
| S2 k10e classes, 7 indices, strata by day of exposure — T24–T26, FigS09 | same paragraph | context; hand-over to Paper 4 (TH-RES-17/18 PARTIAL) |
| Yi 2025 areas digitised, S1+S2 | T23, FigS08 caption, Fig09 legend | corrected per audit |
| T12 `definition_note`; Yale HRL row dropped; hypsometry-gap wording; Kherson peak spread 0.1 m (Gleick 2023) | T12, T16, T22/C14/FigS07, §4.1 | corrected per audit |
| bibliography 52 → 86 entries, all new DOIs Crossref/DataCite-verified; Literature page; RF20 page | dashboard, `docs/references.bib`, `docs/METHOD_REFERENCES.md` | supporting |

## 4b. Audit round 2 (`docs/AUDIT_ACTIONS_2026-09-28_round2.md`), applied the same evening

Items 1–7, 9, 12, 13 applied to `manuscript_template.md` / `README.md`: §3.3 mechanism vs "not diagnosed" reconciled
(mechanism known, attribution to error terms open); "dark-water rule, not the flood" replaced by the untested-cause wording
(Shen et al. 2019); "validated against ICESat-2" → "assessed"; VERIFY dropped where the audit read the source (Lehnigk, Yi);
no "peak" without a noun; abstract gives both T15 statistics; README C01–C14; Fig03 cited in §4.9. Item 8 (196 vs 196.5):
half-up rounding was tried and reverted — it also turns 488/790/682 into 489/791/683 and breaks the dashboard, C02 and every
written 790; the rounding rule (half-to-even) is now stated in the manuscript preamble instead. Item 10 was already closed. The
literature list of the audit (B-01 … B-22) is NOT yet in the manuscript body or `references.bib` — next pass.

## 5. Open items (not closed by this validation)

- Figure number of the digitised Yi 2025 series (needs the PDF).
- Pre-breach outlet level is the held 31 May SWOT value (flagged in T27b); the pre-breach gradient is not a measurement.
- Rozumivka from 10 June sits at ~13.8 m (upstream river regime): the Rozumivka-based design volume no longer describes the pool.
- No source in the corpus separates wet sediment from water in C-band (audit TH-RES-16.A): keep "open water or smooth wet mud".
- Why the nominal run lies below its own MC p05 (connectivity? DEM error under canopy?) — a diagnostic run, not a wording fix.
- Reports of ~19 m near the dam before the breach: no such value in any source here (SWOT 17.53 on 31 May at 0 km; ICESat-2 17.09 at
  18 km on 2 June); frame or source to be identified before it is used.
- Older supplementary figures/tables not cited in the manuscript body (§3).
