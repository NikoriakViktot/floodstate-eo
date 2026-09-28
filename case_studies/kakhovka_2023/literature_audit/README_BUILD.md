# Literature audit of Paper 3 (Kakhovka daily inundation) — how the package was built and how to rebuild it

Everything here was produced from the frozen floodstate-eo bundle `case_studies/kakhovka_2023/publication/`
(commit 38e3375; the 21ba34c and 26 Sep versions are kept in `_work/publication_audited_21ba34c/` and `_work/publication_audited_20260926/`) and the GeoHydroAI corpus
(5 027 normalized papers). Nothing in `publication/` was edited; every text change is a documented entry in
`revisions.yaml` and appears in `10_change_log.md`.

## What is in this directory

| file | what it is |
|---|---|
| `01_scientific_audit.md` | reviewer-style audit: CHECK A–H, Kakhovka comparators, verdicts, novelty, re-audits of 21ba34c (§10) and 2dca5ae/38e3375 (§11) |
| `02_thesis_evidence.csv` | one row per (atomic claim × retained source): role, status, quote, chunk/page, route, lane |
| `03_source_ledger.csv` | every source touched (3 767): metadata, corpus provenance, CrossRef/OpenAlex status |
| `04_search_log.jsonl` | per atomic claim: queries (original / extra / counter), hits per route, retained, rejected + reason |
| `05_claim_citation_matrix.md` | C01–C14 and TH-* → role → best sources → strength → caveat; novelty NQ1–NQ5 with denominators |
| `06_unresolved.md` | everything not closed: absent sources, grey products, internal contradictions, T23/Yi, re-audit §G |
| `07_references_verified.bib` / `07b_…md` | the 85-key bibliography re-verified (73 verified; 12 grey/unresolved) |
| `07c_method_references*.{md,csv,bib}` | method/index first sources (26 CrossRef-verified; formulas checked in the code) |
| `07d_corpus_references.bib`, `07d_unresolved.md` | the 49 corpus-only citation keys of the article that `docs/references.bib` (86 keys) lacks — CrossRef fields, ready to append |
| `revisions_for_template.md` | for every remaining revision: the line span in `manuscript_template.md` and how many `{{…}}` placeholders the span holds |
| `08_literature_synthesis.md` | synthesis by theme A–H (established / disagreement / closest / how Paper 3 differs / not established) |
| `09_manuscript_literature_revised.md`, `09b_captions_revised.md` | the revised text and captions (built by `revise`) |
| `10_change_log.md` | every change: original → revised, reason, thesis ids, references, type |
| `article/` | **the final article**: `Paper3_final.md` and `Paper3_final.docx` (text + 19 figures + 39 tables + references), `figures/` (PNG), `tables/` (all CSVs + the metric README), `final_model.json` (what was placed where) |
| `atomic_claims.yaml`, `theses_supplement.yaml`, `supplementary_pairs.csv` | the audited claims (51 theses → 97 atomic claims; TH-RES-16..18 for T23–T26) |
| `overrides.yaml`, `novelty_verdicts.yaml`, `citation_keys.yaml`, `revisions.yaml` | the human decisions (roles, statuses, verdicts, citation keys, text edits) |
| `kakhovka_numbers.csv` | every km²/m³ s⁻¹/km³ statement in the Kakhovka papers with its semantics; `human_verified` rows were read |
| `run_manifest.json`, `completion_report.md` | corpus size, query hashes, rule versions, counts |

## Rebuild (from the GeoHydroAI repo, `/home/niko/projects/knoweledg_graf`, WSL distro "Ubuntu")

```bash
# 0. services: docker start course-neo4j   (Neo4j is optional: the KG route is logged as route_unavailable when down)
#    Gemini key in .env (GEMINI_API_KEY); Ollama only as a fallback (weaker: 19 % rejected quotes vs 0–2 %)
# 1. sync the frozen bundle from floodstate-eo (Ubuntu-24.04) into paper_unet-case-kakhovka/publication/
#    wsl.exe -d Ubuntu-24.04 --cd /home/niko/repo/floodstate-eo/case_studies/kakhovka_2023/publication -- bash -c 'cat <file>'
P=.venv/bin/python3; A="$P tools/paper3_literature_audit.py"
$A prepare              # validates atomic_claims.yaml (+ theses_supplement.yaml), runtime corpus index, bib snapshot, manifest
$A retrieve             # exact refs → SPECTER2 chunks → OpenAlex citation neighbours → KG → full-text density; 04_search_log
$A select               # density-ranked quotas (high 12 / medium 8 / low 5) + supplementary_pairs.csv (route expert_named)
$A screen --lane gemini-3.1-flash-lite --shard 0/2 &   # 8-role prompt, verbatim-quote gate; one model per process
$A screen --lane gemini-3.5-flash-lite --shard 1/2 &   # 480 calls/day/model; per-lane raw + quota files
$A screen --lane gemini-3.5-flash-lite                 # leftovers (failed 503s, late-added pairs); or --llm ollama
$A kakhovka-numbers     # km²/m³/s statements of the Kakhovka papers (then mark human_verified by reading)
$A references           # CrossRef/OpenAlex verification of docs/references.bib → 07 / 07b
$A enrich-retained      # CrossRef metadata for retained corpus papers lacking year/journal
$A checks               # deterministic manuscript checks A–H → _work/checks_findings.{json,md}
$A export               # 02 / 03 / 05 + statuses (rules R1–R6, then overrides.yaml)
$A report               # novelty verdicts into 05, thesis table, completion_report.md
$A revise               # publication/manuscript.md + revisions.yaml → 09, 09b, 10
$P -c "from tools.paper3_audit import rebase; rebase.run('<commit>')"   # after a new bundle: moves applied entries to superseded, writes revisions_for_template.md
$P -c "from tools.paper3_audit import bib_delta; from pathlib import Path; bib_delta.build(Path('…/references.bib'))"   # 07d
$P -c "from tools.paper3_audit import final_article, docx_build; final_article.run(); docx_build.run()"   # article/Paper3_final.{md,docx}
$P -m pytest tests/test_tools_paper3_audit.py -q   # 22 tests, no live stores
```

Manual steps that no script does: writing `atomic_claims.yaml`, reading every retained passage of the high-priority
claims and recording the decisions in `overrides.yaml`, marking `human_verified` in `kakhovka_numbers.csv`, writing
`novelty_verdicts.yaml`, and writing the prose of 01 / 06 / 08 and the entries of `revisions.yaml`.

## The article

`article/Paper3_final.md` = 09 (bundle 38e3375 + the 26 audit revisions of `10_change_log.md`; 20 earlier entries are recorded as superseded because the bundle applied them) + the final-assembly edits
(FA-01…FA-03, logged at the end of `10_change_log.md`: bundle build note removed, `VERIFY` flags of the resolved
literature values dropped, the bundle's References stub removed; FA-04 — Fig03 / T06 / T07b cited in §4.9 — is now in the bundle itself) + every figure of the
bundle placed after its first mention (supplementary figures in their own section) + every table placed after its first
mention: 25 tables printed in full, 5 wide ones as a compact column view (T12, T14, T20, T21, T24 — the dropped columns are
named under the table), 9 long ones (> 60 rows: T05, T06, T07, T12b, T13, T19, T25, T26, T27b) cited by caption and shipped
as CSV; the 13 tables the text never cites are in "Supplementary tables". Table identifiers are the bundle's (T01…T27c) and
no cell was altered. The reference list holds every verified key (07, 07c, corpus records: 123) and the 12 unresolved
grey-literature keys separately.

`article/Paper3_final.docx` is the same content rendered with python-docx (A4; images 16 cm; tables with ≥ 9 columns on
landscape pages; long tables as the CSV pointer). To regenerate after editing the markdown:
`$P -c "from tools.paper3_audit import docx_build; docx_build.run()"`. LibreOffice/pandoc are not installed on either
WSL distro, so the docx was verified by re-opening it with python-docx (368 paragraphs, 19 images, 30 tables, 33 sections),
not by rendering — open it once in Word and check the landscape table pages.

Open wording that stays in the article on purpose (see `06_unresolved.md`): the figure number of the digitised Yi et al.
(2025) series ("figure number VERIFY" in T23 / FigS08 / Fig09 captions) needs their PDF; the UNOSAT product sheets are
listed under unresolved references.
