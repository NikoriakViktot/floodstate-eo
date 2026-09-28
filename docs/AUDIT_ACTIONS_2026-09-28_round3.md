# Literature-audit actions for floodstate-eo — round 3 (bundle 2dca5ae / 38e3375, 2026-09-28, late)

Source: GeoHydroAI audit, copied as `case_studies/kakhovka_2023/literature_audit/` (01 §11, 06 §H, `10_change_log.md`,
`revisions_for_template.md`, `07d_corpus_references.bib`). Round 2 verified by diff: everything you listed as applied is
applied; the round-half-to-even rule is accepted now that the preamble states it.

## A. Merge the audit bibliography (your NEXT_STEPS item) — mechanical

1. `cat case_studies/kakhovka_2023/literature_audit/07d_corpus_references.bib >> docs/references.bib` — 49 entries, no key
   collides with the 86 present (checked). Every field is CrossRef's for the record's DOI; two DOIs (Magas 2023, Tsiupa
   2023, both 10.3997/2214-4609.2023520…) were found by OpenAlex title search at ratio 1.0; the Bates DOI was truncated in
   the corpus record and completed from the record's own name (CrossRef title match). `07_references_verified.bib` and
   `07c_method_references_verified.bib` add nothing: all their keys are already in `references.bib`.
2. Four keys carry the CrossRef year, not the corpus year — cite them as **Bates 2022** (Annu. Rev. Fluid Mech. 54),
   **Tuan 2021**, **Refice 2018**, **Arcos González 2024**. The audit files and the article were renamed accordingly.
3. Then your bib test / Literature page rebuild.

## B. Move the B-* sentences into `manuscript_template.md` — by hand, guided

`literature_audit/revisions_for_template.md` lists all 26 remaining entries with the template line span (located from the
sentence's first and last words) and the number of `{{…}}` placeholders inside that span. 22 spans have 0 placeholders:
replace the span with the "With:" text as is. Four spans carry placeholders — **A-06 (2), A-07 (3), B-05 (1), B-07 (3)** —
re-insert the placeholders in the "With:" text where the printed numbers stand; never type the numbers. C-02 and F-03 are
`captions.md` edits (Fig04, Fig08). Every entry's reason, thesis ids and citation keys are in the same file.

## C. Still open in the bundle after 2dca5ae (small)

| # | where | current | proposed | why |
|---|---|---|---|---|
| 1 | §5 L481 | "changes the peak by about a third (T12)" | "changes the reconstructed areal maximum by about a third (T12)" | bare "peak" (E-02) |
| 2 | §6 L499–500 | "no satellite scene on the peak day" | "no satellite scene on the day of the reconstructed areal maximum" | bare "peak" (E-03) |
| 3 | captions.md Fig08 | "within a few decimetres along the tracks" | "to a few centimetres in the median (p10–p90 spread of a few decimetres) along the tracks" | Abstract and C06 now give both T15 statistics; the caption lags (F-03) |
| 4 | §6 L501–502 | "literature figures not verified against their sources" | "literature figures cited with their own semantics; the operational product sheets (UNOSAT via CEOBS/REACH) are not independently verified" | 73 bundle keys + 49 corpus keys are CrossRef-verified now (L-01) |
| 5 | captions.md FigS07 | "−15…−20 % at 11–13 m" | "−14 % at 13 m, −20 % at 11 m" | T22: −14.4 / −20.4 (CHECK G) |
| 6 | literature/theses.md L12 | "breach discharge of" (describing Yi's quantity) | "initial breach flow of" | forbidden phrase in the literature folder (CHECK C; the test scans only the bundle files it names) |

Unchanged and still open (need data, not wording): Yi 2025 figure number for the digitised series; "19 m near the dam"
has no source; attribution of the nominal-below-p05 offset to the individual error terms.

## D. What changed in the audit package with this round

`revisions.yaml` 26 entries (20 superseded, listed with the commit that superseded them); 09 / 09b / 10 rebuilt on
38e3375; `article/Paper3_final.md` + `.docx` rebuilt (1 696 lines; 19 figures; 39 tables; 123 + 49 references);
`07d_corpus_references.bib`, `07d_unresolved.md` (empty), `revisions_for_template.md`, 01 §11, 06 §H, `README_BUILD.md`.
Tools added in GeoHydroAI: `tools/paper3_audit/rebase.py`, `bib_delta.py`.
