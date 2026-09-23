# Data dictionary

Per product: name, dtype, units, nodata, expected range, resolution, CRS, meaning, producer, inputs,
reusable/case-specific, canonical/legacy, **implementation status**. Nothing below is documented as existing
unless verified against the migrated code (source commit `f3e3e1afe91902a82a73f3c09354d1f9eb847766`); dtype/CRS
values not directly read with rasterio during this migration are marked UNVERIFIED.

| Product | Producer | Status |
|---|---|---|
| Per-date index stacks `frames10/<FID>/indices/<date>.tif` (+`_valid.tif`) | `optical/p54a_frame_index_stacks_10m.py` | exists; int16, `INDEX_SCALE=1e4`, nodata −32768 |
| `composite_<preall\|preseas>.tif` (84 bands, incl. `n_obs_*`) | `optical/p54b_frame_composites_10m.py` | exists; `n_obs_*` plain integer counts |
| `p54c_{freeze_gate,inventory,feature_manifest}.csv` | `validation/p54c_composites_10m_freeze_gate.py` | exists; independently recomputed QA, not a self-report |
| `p69a_base_class.tif` (BASE_CLASS, 8 classes) | `surface_state/p69a_base_class.py` | exists; PRE-only, canonical |
| `p69b_semantic_state.tif` (9 classes), `p69b_decision_stability5.tif` (5 classes) | `fusion/p69b_event_association.py` | exists; combination of BASE_CLASS and the frozen M2 candidate |
| `cand_score.tif`, `cand_state.tif`, `cand_valid.tif` (M2 candidate) | `fusion/p67b_production_candidate.py` | exists; status `PRODUCTION_CANDIDATE_NOT_FINAL`; score is a discrimination score, NOT a calibrated probability |
| `flood_score.tif`, `prediction_valid.tif` (M2 production) | `fusion/p66_production_m2.py` | exists; earlier production fit than `p67b`'s candidate — the two are not reconciled to one canonical M2 output |
| `s1_change.tif` (15 SAR event-change channels) | `sar/p71_s1_event_change.py` | exists; int16, dB×100 / robust-z / count, nodata −32768; INPUT channels only, feeds no classifier yet |
| `coh_orb<N>_<pre>_<event>.tif` (SAR coherence) | `sar/p82_coherence_graph.py` | exists as an engineering pilot (frame B2, 4 relative orbits); gated by `validation/p83_coherence_qc.py`, not yet a production layer |
| `p65b_m2_{main,folds,bootstrap,tuning,importance}.csv` | `fusion/p65b_m2_spatial_cv.py` | exists; the M2 validation record |
| `*_rf_flood_prob_20m.tif`, `*_rf_flood_class_20m.tif` (legacy p51, 20 m) | not migrated (`p51_rf_flood_optical.py` is not in this repository) | **NOT PRESENT in floodstate-eo** — cite only from the source repository, and only as "legacy 20 m zone grid, not comparable" |
| `S1_CANDIDATE` / per-scene S1 water masks | `sar/p71_s1_event_change.py` reads a per-scene cache; the cache-BUILDING code itself is not in this migration's scope | UNVERIFIED product name/format for the cache format `p71`/`p69c` consume |
| `<ZONE>_rf_evidence_status_20m.tif` (doc-19-§11 evidence codes 0–6) | none | **PROPOSED / NOT YET CANONICAL** — no migrated file produces this |
| FLOOD_STATE (multi-class) | none | **PROPOSED / NOT YET CANONICAL** |
| URBAN_SCORE | none | **PROPOSED / NOT YET CANONICAL** |
| UNCERTAINTY | none | **PROPOSED / NOT YET CANONICAL** |
| FINAL_FLOOD_MASK | none | **PROPOSED / NOT YET CANONICAL** |
