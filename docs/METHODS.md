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

---

## M6 — breach-induced inundation as water retrieval + event attribution (design adopted 2026-09-24)

Status: **design adopted, partially implemented**. References are keys in `docs/references.bib`.

**Formulation.** Breach-induced inundation is not mapped as direct binary flood / non-flood classification. It is
split into (1) retrieval of surface water at the event date and (2) attribution of that water to the event. A binary
flood classifier trained only where land was dry before the event (label contract v002) never sees water that already
existed, and cannot be asked to tell such water apart from new inundation (p89 audit, group A). Operational and
benchmark practice separates the same quantities: observed water, observed flood and reference water in CEMS GFM
[Wagner_2026]; permanent vs flood vs total surface water in Sen1Floods11 [Bonafilia_2020] and in S1+S2 fusion
[Bai_2021; Bioresita_2019].

1. **Stage 1 — event water retrieval** `[proposed]`. P(W_t) from Sentinel-1 VV/VH and orbit-matched dB change
   (p71), Sentinel-2 NDWI/MNDWI/NDVI and their change (p72, after the 2026-09-24 scaling fix), HAND and context.
   Target: LAND / WATER. SAR water detection follows the automated S1 chain logic of [Twele_2016]; S1+S2 fusion
   follows [Bai_2021; Bioresita_2019].
2. **Stage 2 — immediate pre-event water** `[implemented as data: S1 06-01 / 06-02 masks]`. W_pre from the last two
   S1 acquisitions before the breach. Used in attribution, NOT as a model input: a label built from W_pre and a model
   fed W_pre would reproduce the label rule (circularity).
3. **Stage 3 — reference / seasonal water** `[implemented as data: p89b]`. W_ref from an independent, earlier time
   window: 13 S1 RTC scenes 2023-04-15..05-28 per frame (5 orbits), classified with exactly the June water classifier
   (reproduction gate: fresh 06-01/06-02 masks identical to the cached ones, IoU 1.0), plus S2 late-pre and
   multi-year S2 water frequency. Seasonal reference water reduces flood over-estimation [Martinis_2022; Wagner_2026].
4. **Stage 4 — event attribution** `[proposed]`. EVENT_FLOOD = W_t ∧ ¬W_pre; W_t ∧ W_ref → REFERENCE_WATER.
   Product ontology: LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN (never-observed stays UNKNOWN, not LAND).
5. **Terrain** `[implemented: U2 arm, p86]`. HAND is a plausibility feature, not a water detector and not a hard mask
   [Tupas_2023]. On the frozen split U2 (+HAND) reduced predicted flood on unlabelled cropland by 9.6 km²
   (95 % block-bootstrap CI −14.8 to −5.1) with no statistically resolved change in recall (interval crosses zero).
6. **Urban** `[proposed]`. Separate treatment: absolute backscatter is hard to interpret among buildings; multi-temporal
   change is required [Giustarini_2013]. U2 moved errors into BUILT_UP (+0.37 km²).
7. **Evaluation.** Frozen B1+B2 split (m6_split_v1), agreement with held-out weak labels — not flood-mapping accuracy.
   D1 endpoints within land-cover strata, A1 (labelled dry cropland) vs A2 (unlabelled cropland: "predicted flood
   burden", never called false positives), paired spatial-block bootstrap.
8. **Wording rule.** "None of the audited 19.2 km² cropland-associated candidates showed positive evidence consistent
   with breach-induced inundation under the available SAR, optical and terrain constraints."

## Paper 3 pipeline (Kakhovka 2023) — implemented 2026-09-23..25

22. **RF20 surface context (p73)** `[implemented, frozen: workflows/m6/p73_rf20_surface.py]`. PRE-only Sentinel-2 composite
    predictors, ESA WorldCover 2021 as training reference, 20 m, 5-fold spatial-block CV and B1↔B2 transfers. Used as
    evaluation strata and as the class layer of the disagreement ontology; its WorldCover comparison is agreement with the
    training reference, never validation. Tables T09/T10.
23. **Weak labels v003_A and the U-Net arms** `[implemented: p77d (FROZEN, D3), p84 (split, --block-m sensitivity), p86, p88, p90]`.
    Ontology LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN; arms U0d, U0z, U1 (+RF20), U2 (+HAND) on v002 and U0d, U2, U2b
    (+W_pre) on v003_A; paired spatial-block bootstrap on identical blocks. U2b is a diagnostic upper bound because W_pre is
    also a label ingredient. Every number is agreement with weak labels. Tables T02–T08, T20.
24. **Terrain reconstruction of the daily inundation (p95)** `[implemented: workflows/m6/p95_hand_daily_inundation.py, rev 6 (2026-09-29, code-review response)]`.
    Water surface per day from SWOT L2_HR_RiverSP nodes (EGG2015-referenced heights shifted by the Kherson-local closure of
    Paper 1; node-based interpolation with observed / interpolated / held flags, no chainage) and the Kherson gauge; projected on
    the seamless terrain–bed elevation model of Paper 2 (FABDEM bare-earth DTM outside the surveyed channel, bed inside; source
    mask), with the residual class-dependent terrain bias against night ICESat-2 ground removed on FABDEM cells only (per zone,
    p95j); every height in EVRF2019, asserted from declarations (`floodstate_eo.terrain.vertical`). Rules: connected ceiling
    (primary, CLI default), p42 HAND rule, ceiling only; evaluated once on the union mosaic of the zones
    (`floodstate_eo.terrain.mosaic`), ownership for accounting only; same-rule pre-breach baseline. Sensitivities: 4-connectivity,
    main-stem seed, 3-day maximum gap, river-aware median, terrain as delivered, superseded closure, no surface from nodes > 10 km
    away, the Kalynivske gauge as an extra water-surface node (the gauge then an input). A legacy mode reproduces rev 5
    exactly (reproduction gate, T11h). Uncertainty (p95e rev 2): coherent Monte-Carlo worlds — one terrain-error field over the
    mosaic (unit-variance FFT field, `floodstate_eo.terrain.fields`, covariance fitted in p95j) and one water-surface realization
    per draw, every error term once; W_total, A_new and volumes from their own ensembles; 1000 draws with convergence (two
    seeds), ablation and the distribution of the day of the maximum. Tables T11–T11j, T12–T12c, T18b/T18c; rasters under
    `$BULK_ROOT/floodplain_dyn/` (not redistributed). Response ledger: `docs/CODE_REVIEW_ACTIONS_2026-09-29.md`.
    Support of the new inundation (p95l, T11k/T11l; D-SUPPORT): every newly inundated cell classed by the distance of its nearest
    SWOT node — direct ≤ 3 km, extrapolated 3–10 km, weak > 10 km (operational thresholds) — with gauge-capped and cross-river
    flags; the full reconstruction is the primary product, the supported core (≤ 10 km) and the 10 km cap run are reported next
    to it. The 100 000-draw emulator (p95g) is a computational diagnostic outside the evidence path (T12d; D-EMU). The model is
    static: no momentum or continuity, no propagation time; hydraulic modelling is the next step (manuscript §5).
    Independent in-situ checks (p95k, T17c–T17f; not inputs): Inhulets – Kalynivske 80575, withheld from the primary water surface
    as a tributary validation site (absolute error, event-relative error free of a constant datum offset, peak timing, recession;
    the valley's new area split by the distance and river of its serving SWOT node), and the liman gauge Mykolaiv 98027. Yearbook
    table 1.2 daily means in cm above the gauge zero, the zero read from the sheet header, EVRF2019 by the EPSG:9902 grid step;
    peaks, rises and records from the yearbook's highest level of the year.
25. **Checks and disagreement ontology** `[implemented: p94, p95c, p95d, p96 T13–T19]`. Sentinel-1 per acquisition date
    (POD/FAR/CSI on the S1 observation domain; POD excluding normally-wet cells as an a-priori sensitivity); A/B/C ontology by
    WorldCover/RF20 class and ground elevation above the surface; ICESat-2 altimetric consistency check (night ATL08 vs DEM
    and the 06-09 surface); SWOT-input vs gauge at day level; DEM accuracy by class from Paper 2.
26. **Publication assembly** `[implemented: workflows/paper/p96–p99, render_claims]`. Claims register
    (`publication/evidence_matrix.csv`, Paper-1 schema + evidence_level/tier) → tables T01–T22 with manifest → figures
    Fig01–Fig09 + supplement (FigS01–S07) → three executable notebooks → Streamlit dashboard (`apps/dashboard`). Terminology frozen in `publication/TERMINOLOGY.md` (enforced by `tests/test_terminology_freeze.py`; consolidation review 2026-09-26). Wording rules: model
    numbers are agreement with weak labels; not observed is not dry; area semantics named; cropland-associated SAR candidates.

### Key references
- Wagner et al. 2026, RSE 333:115108 — CEMS Global Flood Monitoring; observed flood vs reference water. `Wagner_2026`
- Martinis et al. 2022, RSE 278:113077 — S1/S2 seasonal + permanent reference water. `Martinis_2022`
- Bonafilia et al. 2020, CVPRW 835–845 — Sen1Floods11; permanent / flood / total water. `Bonafilia_2020`
- Bai et al. 2021, Remote Sensing 13:2220 — S1+S2 deep learning for permanent vs temporary water. `Bai_2021`
- Bioresita et al. 2019, IJRS 40:9026–9049 — S1+S2 time-series fusion, permanent and temporary water. `Bioresita_2019`
- Twele et al. 2016, IJRS 37:2990–3004 — fully automated S1 flood processing chain. `Twele_2016`
- Tupas et al. 2023, Water 15:4034 — HAND/topographic prior for S1 flood maps. `Tupas_2023`
- Giustarini et al. 2013, IEEE TGRS 51:2417–2430 — SAR change detection for urban flooding. `Giustarini_2013`
