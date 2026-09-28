# Literature-audit actions for floodstate-eo (from the GeoHydroAI audit, 2026-09-28)

Source: `knoweledg_graf/paper_unet-case-kakhovka/literature_audit_paper3/` (WSL distro **Ubuntu**, not Ubuntu-24.04;
from Windows: `\\wsl.localhost\Ubuntu\home\niko\projects\knoweledg_graf\paper_unet-case-kakhovka\literature_audit_paper3\`).
Only the items that need a change in THIS repo are listed; each quotes the current text and the proposed fix.

## 1. T12 `definition_note` contradicts TERMINOLOGY.md (MAJOR) — `p96_paper_tables.py`

Current (T12.csv, every row):
> A_* = NEW inundation (cells allowed by the water surface outside the same-rule pre-breach regime); W_total_* = TOTAL
> water surface on the day (all cells allowed by the water surface, incl. channels, lakes, reed beds) -- **the quantity
> comparable with operational 'flooded area' products**; wetland submergence is in T13/T14

TERMINOLOGY.md L26–27 and T16 say the opposite: operational *flooded land* (UNOSAT 3616, ~620 km² cumulative 6–9 June,
pre-existing water separate) is closer in kind to **A_new**, and is context, never validation.

Proposed:
> A_* = NEW inundation (…); W_total_* = TOTAL water surface on the day (…); operational 'flooded land' figures
> (e.g. UNOSAT 3616) exclude pre-existing water and are closer in kind to A_*, but differ in AOI, date and temporal
> semantics — context, never validation; wetland submergence is in T13/T14

## 2. Yi et al. 2025 in T23 / FigS08 / Fig09

- The ~845 km² by 20 June is **verified in Yi's text** (corpus record of Yi et al. 2025, WRR 61, e2024WR038314), exact
  sentence: "The inundation area started to reduce by about 280 km 2 in the first 4 days (6-10th June), by about 1,000
  km 2 in the next 10 days (11-20th June), and by about 460 km 2 in the last 10 days (21-30th June)." — with "the
  reservoir had an area of 2,125 km 2" on 30 May (same paper). 2125 − 280 − 1000 = 845 km². The VERIFY on "~845" can
  be dropped; the figure number of the digitised series still needs a look at the PDF.
- Water maps: "the Sentinel-1 Dual-Polarized Water Index (SDWI) was used for Sentinel-1 SAR data and the modified
  Normalized Difference of Water Index (mNDWI) was used for Sentinel-2 optical imagery" — S1 **and** S2, as you changed.

## 3. Reporting of the central value (decision for the author)

Nominal run below its own MC p05 on 7 June (T12, DNIPRO_CORRIDOR): A_new 235.3 vs 237.6/246.7/254.9; W_total 779.1 vs
781.4/790.5/798.7; V_new 509.0 vs 545.4/565.9/595.7. Audit recommendation: "MC median [p05–p95] (nominal run X)"; the
alternative is to keep the nominal value and say every time that the interval is not centred on it. Revised text using
the recommendation: `09_manuscript_literature_revised.md` (changes A-01…A-05, list in `10_change_log.md`).

## 4. Smaller consistency items

- Hypsometry gap stated four ways: text −9 % (17.5 m), −14 % (13 m), −20 % (11 m) = T22; C14 and the FigS07 caption
  "15–20 % at 11–13 m"; tables/README T22 "8-12 % less volume" (line 66) — the README wording does not match T22.
- `publication/README.md` L5 says "C01–C12" (claims run to C14).
- `tests/test_terminology_freeze.py` matches line by line; "false\nSAR water" in captions.md Fig05 escapes it —
  collapse whitespace (`re.sub(r"\s+", " ", text)`) before matching. The audit's revised caption is in `09b_captions_revised.md`.
- T16 row "Yale HRL 2023, 520 km²": no source and unknown semantics — document or drop.
- Kherson peak by source: river yearbook 5.78 m (used); operational 5.68 m at 15:00 on 8 June (Gleick et al. 2023,
  Earth's Future); 5.6 m cited by Lehnigk et al. 2026. State the 0.1 m spread.

## 5. TH-RES-16…18 (reservoir drawdown; audit statuses)

- TH-RES-16 (T23): published pool areas — VERIFIED (Magas 2023: 2091.48 km² on 5 June, 379.742 km² on 8 Sept incl.
  channel 133 km²; Tsiupa 2023: 1.63 km² open water + 110 km² wet on 6 Sept; Novitskyi 2024: 655.9 km² on 17 June,
  state estimate). IoU as metric — VERIFIED. Wet mud as a C-band water look-alike — PARTIAL: no source for wet
  sediment; only smooth bare soil / sand are documented (Shen et al. 2019).
- TH-RES-17 (T24): revegetation of the bed — PARTIAL/VERIFIED on Kakhovka (Kuzemko et al. 2024 preprint and 2025 Ukr.
  Bot. J.: vascular taxa ×7 June→October, ×14 in a year; Vyshnevskyi 2024: willow; Pichura & Potravka 2025: 135
  thousand ha vegetated in 2023–2024); no precedent outside Kakhovka in the corpus.
- TH-RES-18 (T25/T26): Sentinel-2 indices on the drained bed — PARTIAL (Tutova et al. 2025; Magas 2023; Pichura 2025).
- Audit recommendation: keep them as supplementary context (FigS08 already says "context, no claim"); do not add C-claims.
