# Methods

Generic method only; Kakhovka-specific constants live in `case_studies/kakhovka_2023/config/*.yaml` and that
case study's README. Each subsection is tagged `[implemented: file]` or `[proposed]`. This document reflects the
migration commit of 2026-09-23 (source SWOT-DNIPRO commit `f3e3e1afe91902a82a73f3c09354d1f9eb847766`); it will
drift from the code if not kept current — where in doubt, the code under `src/floodstate_eo/` is authoritative.

1. **Input data model** — S1 RTC/SLC scenes, S2 L2A + SCL, optional terrain/LULC (ESA WorldCover). `[implemented: optical/sentinel_preprocess.py]`
2. **CRS and grids** — canonical lattice snapped to the native S2 pixel lattice (not `floor(bbox/res)`); alignment verified against the native Sentinel-2 20 m tile origins. `[implemented: spatial/canonical_grid.py]`
3. **Temporal windows** — PRE / EVENT / TRACE as configurable intervals; a post-event date cannot enter PRE (asserted in code, not just configured). `[implemented: optical/p54b_frame_composites_10m.py, case_studies/kakhovka_2023/config/temporal_windows.yaml]`
4. **Observation validity** — SCL reject set {0,1,3,8,9,10,11}; observation = valid pixel; "not observed never votes". `[implemented: optical/watermask.py, optical/composites.py]`
5. **BOA offset handling** — `BOA_ADD_OFFSET` read from each scene's own `MTD_MSIL2A.xml` and applied before reflectance scaling; never assumed to be zero. `[implemented: optical/sentinel_preprocess.py]`
6. **Spectral features** — NDVI, NDWI, MNDWI, NDMI, BSI, AWEIsh, NDTI (+ NDBI = −NDMI, extremes transposed at composite time). `[implemented: optical/sentinel_preprocess.py, optical/p54b_frame_composites_10m.py]`
7. **SAR features** — VV/VH backscatter, orbit-matched event-change channels in dB (log-ratio, not a linear difference — see `tests/test_p71_change_domain.py`), interferometric coherence engineering pilot. `[implemented: sar/p71_s1_event_change.py, sar/p80-83]`
8. **Temporal composites** — median/min/max in PRE and EVENT, median in TRACE; d_med, d_ext (signed extreme furthest from pre median), d_trace. `[implemented: optical/p54b_frame_composites_10m.py]`
9. **Observation-count semantics** — n_obs = number of distinct valid dates, plain integer, derived from validity masks only; a feature, never a gate. Independently recounted end-to-end by the freeze gate. `[implemented: optical/p54b_frame_composites_10m.py, validation/p54c_composites_10m_freeze_gate.py]`
10. **Surface-state representation** — `BASE_CLASS`: 8-class pre-breach land state, built exclusively from PRE-window evidence, forbidden from reading any event/TRACE/Sentinel-1 evidence. `[implemented: surface_state/p69a_base_class.py]`
11. **Weak labels** — S1-based positive/negative/unlabelled rules (Sen1Floods11-style). `[NOT MIGRATED — the source `p51_rf_flood_optical.py` label-generation rule is not in this repository; see case_studies/kakhovka_2023/README.md]`
12. **Flood-state classes** — a true multi-class flood-state output does not exist. What does exist is `semantic_state` (9 classes: pre-existing water, five FLOOD_ASSOCIATED_* classes, non-flooded, uncertain-base, invalid), which is explicitly weaker than a flood claim. `[implemented (partial, non-canonical naming): fusion/p69b_event_association.py; proposed: a real FLOOD_STATE class set]`
13. **Random forest** — 300/500 trees (grid-searched), `balanced_subsample`, on the canonical 10 m frames (M2). `[implemented: fusion/p65b_m2_spatial_cv.py, fusion/p66_production_m2.py, fusion/p67b_production_candidate.py — status PRODUCTION_CANDIDATE_NOT_FINAL]`
14. **Clustering / texture / object refinement** — not implemented anywhere in the migrated code. `[proposed]`
15. **Sensor fusion** — `BASE_CLASS × M2` threshold masks combine into `semantic_state` (a real, frozen combination of two independent evidence layers). The doc-19-§11 design (S1 draws / S2 edits, evidence codes 2–6) is NOT implemented — no file produces evidence-status codes. `[implemented (different design): fusion/p69b_event_association.py; proposed: the evidence-code fusion design]`
16. **Spatial CV** — nested GroupKFold-style design: 5 km spatial blocks, 5 outer × 3 inner folds, a buffered regime removing training cells within 3.5 km of the test population; block-size sensitivity not implemented. `[implemented: fusion/p65b_m2_spatial_cv.py]`
17. **Threshold selection** — fold-wise threshold at target recall (0.90) on the inner split, frozen, applied once to the outer test fold. Fold thresholds are known to be unstable across spatial folds in the source repository's own reporting — document as a limitation, not re-verified in this migration. `[implemented: fusion/p65b_m2_spatial_cv.py]`
18. **Leave-one-zone-out** — a LEGACY `p51` concept on two 20 m zones. `[NOT MIGRATED]`
19. **Metrics** — PR-based (AP, F1, IoU, precision/recall at the frozen threshold), spatial-block bootstrap CIs. `[implemented: fusion/p65b_m2_spatial_cv.py]`
20. **Uncertainty** — evidence-status codes. `[proposed]`
21. **Provenance** — scene manifests, source commit, checksums. `[partial: provenance/MIGRATION_MANIFEST.csv covers the code migration; case-study scene manifests (S1/S2) are not yet populated]`

---

See `docs/DATA_DICTIONARY.md` for the per-product data dictionary (Appendix to this document in the source
audit's plan).
