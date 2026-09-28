# Completion report — 2026-09-28

- corpus searched: 5027 normalized papers (1354158 SPECTER2 chunks; 3844 with OpenAlex ids; queries sha256 c64f78645eb6ae5c…)
- theses processed: 54 (atomic claims: 97)
- thesis statuses: {'VERIFIED_PARTIAL': 27, 'SOURCE_FOUND_METADATA_UNVERIFIED': 10, 'VERIFIED_COMPARATOR_ONLY': 6, 'NO_EVIDENCE_IN_CORPUS': 4, 'VERIFIED_SUPPORTED': 4, 'CONTRADICTED_OR_QUALIFIED': 3}
- atomic-claim statuses: {'VERIFIED_PARTIAL': 43, 'VERIFIED_SUPPORTED': 29, 'SOURCE_FOUND_METADATA_UNVERIFIED': 11, 'VERIFIED_COMPARATOR_ONLY': 7, 'NO_EVIDENCE_IN_CORPUS': 4, 'CONTRADICTED_OR_QUALIFIED': 3}
- candidate pairs recorded: 46619 (3292 prefilter-pass, 965 screened-selected)
- unique papers screened by LLM (Gemini 3.1/3.5 flash-lite; Ollama mistral-nemo for TH-RES-16..18, 46 pairs): 407 (976 pair judgements; 385 retained; quotes verified: 383)
- unique papers retained as evidence (02): 225; sources in the ledger (03): 3767
- unresolved high-priority theses: 7 → TH-INT-02, TH-MET-01, TH-MET-03, TH-MET-06, TH-MET-08, TH-RES-04, TH-RES-14
- files created in literature_audit_paper3/: 01_scientific_audit.md, 02_thesis_evidence.csv, 03_source_ledger.csv, 04_search_log.jsonl, 05_claim_citation_matrix.md, 06_unresolved.md, 07_references_verified.bib, 07b_references_unresolved.md, 07c_method_references.csv, 07c_method_references.md, 07c_method_references_table.csv, 07c_method_references_table.md, 07c_method_references_verified.bib, 08_literature_synthesis.md, 09_manuscript_literature_revised.md, 09b_captions_revised.md, 10_change_log.md, atomic_claims.yaml, citation_keys.yaml, completion_report.md, kakhovka_numbers.csv, novelty_verdicts.yaml, overrides.yaml, revisions.yaml, run_manifest.json, supplementary_pairs.csv, theses_supplement.yaml
- re-audit of floodstate-eo 2dca5ae/38e3375 (2026-09-28, late): 26 revisions applied to 09/09b, 20 superseded by the bundle; 07d_corpus_references.bib 49 entries (0 unresolved); revisions_for_template.md maps every remaining entry to manuscript_template.md
