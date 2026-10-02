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
17. **Threshold selection** — fold-wise threshold at target recall (0.90), frozen and applied once to the outer test fold. Since 2026-09-29 (review F09) the threshold comes from **inner out-of-fold scores**: for each of the three inner block folds a forest with the fold's best hyperparameters is fit on the other two and scores the held-out blocks (fit and calibration cells disjoint, asserted; whole spatial blocks); the pooled out-of-fold scores give the threshold. The former rule — the refit forest scoring cells of its own fit set — is kept in the fold table as `threshold_insample_superseded` with the outer-test recall it reached (it undershoots the target). Fold thresholds vary across spatial folds; T50 of the label masks is their median (p68). `[implemented: fusion/p65b_m2_spatial_cv.py (inner_oof_threshold), tests/test_p65b_threshold_oof.py]`
17a. **Feature restriction** — `--exclude <regex>` drops features by name in the nested CV (p65b) and in the production fit (p67b); outputs are tagged `_no<regex>`. The corrected M2 behind labels v004 excludes the 17 post-event TRACE features (`p67b_features_notrace.csv`) and accepts only EVENT observations for prediction validity (review F10; lineage in `tables/m6_label_lineage.csv`, contracts in `docs/LABEL_CONTRACTS.md`). `[implemented: fusion/p65b_m2_spatial_cv.py, fusion/p67b_production_candidate.py, workflows/m6/p77f_label_lineage.py]`
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
   [Tupas_2023]. The single-seed reduction of the unlabelled-cropland burden on the historical v002 labels (−9.6 km²) did NOT
   reproduce on the canonical v004 labels with three training seeds (+1.0, +7.6, −3.8 km²; maintainer decision D-C10, a negative
   result): HAND is not demonstrated to suppress cropland false positives.
6. **Urban** `[proposed]`. Separate treatment: absolute backscatter is hard to interpret among buildings; multi-temporal
   change is required [Giustarini_2013]. On v004 with three seeds HAND leaves the built-up false positives without a consistent
   change, while the RF20 classes as an input (U1) lower them in every seed and raise the cropland burden (T06s).
7. **Evaluation.** Frozen B1+B2 split (m6_split_v1), agreement with held-out weak labels — not flood-mapping accuracy.
   D1 endpoints within land-cover strata, A1 (labelled dry cropland) vs A2 (unlabelled cropland: "predicted flood
   burden", never called false positives), paired spatial-block bootstrap.
8. **Wording rule.** "None of the audited 19.2 km² cropland-associated candidates showed positive evidence consistent
   with breach-induced inundation under the available SAR, optical and terrain constraints" — an audit of the historical v002
   arms (T08), kept as provenance.

## Paper 3 pipeline (Kakhovka 2023) — implemented 2026-09-23..25

22. **RF20 surface context (p73)** `[implemented, frozen: workflows/m6/p73_rf20_surface.py]`. PRE-only Sentinel-2 composite
    predictors, ESA WorldCover 2021 as training reference, 20 m, 5-fold spatial-block CV and B1↔B2 transfers. Used as
    evaluation strata and as the class layer of the disagreement ontology; its WorldCover comparison is agreement with the
    training reference, never validation. Tables T09/T10.
23. **Weak labels v004 and the U-Net arms** `[implemented: p77/p77d on the corrected M2 (FROZEN), p84 (split, --block-m sensitivity), p86, p88, p90, p86s]`.
    v004 is the canonical weak-label ontology (LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN; the v003_A rules on the M2 without
    the post-event TRACE window and with an out-of-fold threshold; D-LABELS); v002 and v003_A are provenance. Arms U0d, U1 (+RF20),
    U2 (+HAND), U2b (+W_pre) on v004 and U2 on v002_notrace, three training seeds each (D-SEEDS: three seeds are the minimum
    evidence unit of an arm claim); paired spatial-block bootstrap on identical blocks per seed. U2b is a diagnostic because
    W_pre is also a label ingredient. Every number is agreement with weak labels. Tables T02–T08, T05s/T06s/T07s, T20;
    `docs/LABEL_CONTRACTS.md`.
24. **Terrain reconstruction of the daily inundation (p95)** `[implemented: workflows/m6/p95_hand_daily_inundation.py, rev 7 (2026-09-30: the vertical frame of Paper 1 v6 — the Kherson gauge at the post's own EPSG:9902 step, the FABDEM part of the terrain and the ICESat-2 ground raised by the chain difference, workflows/m6/paper1_frame.py; rev 6 = 2026-09-29, code-review response)]`.
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
    to it. The 100 000-draw emulator (p95g) is a computational diagnostic outside the evidence path (T12d; D-EMU).
    Seed of the connectivity (D-SEED, 2026-09-30; p95 rev 8): the event source is the pre-breach RIVER NETWORK — the largest
    connected component of the pre-breach water map (Dnipro with delta and side channels, Inhulets, Kokan'; the two frames'
    maps composed where each has labels, which closes a 30 m label gap that had split the network at Kherson). Seeding from
    every pre-breach water cell (the earlier rule) let isolated ponds "flood" ~40 km² of terrace cropland under the Kokan'
    level 14 km away; that run is kept as the provenance variant `_seed_allprewater` and audited by p95o (three classes:
    river-connected / trapped / isolated-never; lineage by a day-to-day overlap graph; T11m–T11o, FigS16). Retained water
    after a lost connection is the `_memory` sensitivity (D-MEMORY; T11p), never the primary. The model is
    static: no momentum or continuity, no propagation time; hydraulic modelling is the next step (manuscript §5).
    Pre-breach baseline (p95 rev 9, maintainer 2026-09-30): the optically observed pre-breach water (p60 Sentinel-2 water
    frequency >= 20 %) plus the same-rule normal wetness. Sentinel-1 darkness on 1–2 June is NOT reference water (dry sand
    and smooth fields are dark in C-band; 403 km² of the domain, mostly dry in later EO); it masks the Sentinel-1 new dark
    water of the checks only (p94 S1, p95, p95c, p95d, p95o). S2 new water (p94, dashboard) uses the optical reference only.
    Daily state mask between the EO dates (p95x, `[implemented]`): same-day EO, else the ensemble P(water) — WATER >= 0.8,
    DRY <= 0.05, UNKNOWN between, and UNKNOWN in a recession between an EO WATER and the next EO DRY — with the source
    (EO_S1, EO_S2, MODEL_STRONG, MODEL_WEAK, REFERENCE) and quality flags as metadata (storage-sensitive depressions, weak
    connectivity, sensor-blind, reference-uncertain, recession-uncertain); UNOSAT 3614 is a check, never a label source.
    Ground class before the event (p95x `ground_class.tif`, `[implemented]`): dry before the event / vegetated wetland complex
    (WorldCover herbaceous wetland incl. reed beds above the normal surface, plus the model-only normally wet) / optical reference
    water / other water. `p95e_split_areas` replays the p95e worlds per class (T12h): A_new,dry (new inundation of dry ground) and
    the wetland's water-covered area and event increase over 5 June, reported apart and never summed; `p95z` (T12i) gives the
    delta strata evidence (no optical water under the reeds in a normal June; spring C-band double bounce in normally-wet and
    event-only reeds alike, in the delta and the floodway); `p95zm` maps the classified indices (p95h display bins) as cloud-free
    period composites (per-cell median of clear observations), the peak with Sentinel-1 orbit 14, and k10e on the best-covered
    dates -- single optical dates are not usable for the reed beds around the peak. Manuscript §3.3 / §4.1.1; the abstract still
    reports the combined A_new (`[partial]`).
    **Wetland evidence chain** (one product, one order; `rebuild.py --group wetland_evidence`): p95x ground classes -> p95e_split
    (T12h) -> p95z strata evidence (T12i, T12j) -> p95zm cloud-free class maps (T12k-m; gated by the inventory) -> p95y UNOSAT
    diagnostic (T16b, T16c) -> p95u observation inventory (T01b: zone x stratum x period x sensor, the gate of every diagnostic)
    -> p96b `publication/WETLAND_EVIDENCE.md` (the full picture, generated from the tables). No new reed-bed scripts; changes
    go inside these. Agreement metrics carry a passport (TERMINOLOGY; `tests/test_agreement_metrics.py`).
    Independent in-situ checks (p95k, T17c–T17f; not inputs): Inhulets – Kalynivske 80575, withheld from the primary water surface
    as a tributary validation site (absolute error, event-relative error free of a constant datum offset, peak timing, recession;
    the valley's new area split by the distance and river of its serving SWOT node), and the liman gauge Mykolaiv 98027. Yearbook
    table 1.2 daily means in cm above the gauge zero, the zero read from the sheet header, EVRF2019 by the EPSG:9902 grid step;
    peaks, rises and records from the yearbook's highest level of the year.
25. **Checks and disagreement ontology** `[implemented: p94, p95c, p95d, p95k, p96 T13–T19]`. The vertical frame is the validated
    input of Paper 1 (not re-validated here; T17 is an input check). Two withheld gauges (Kalynivske 80575, Mykolaiv 98027);
    Sentinel-1 per acquisition date (POD/FAR/CSI on the S1 observation domain; conditional POD outside the normally-wet class as a
    diagnostic); A/B/C ontology by WorldCover/RF20 class and ground elevation above the surface; ICESat-2 altimetric consistency
    check (night ATL08 vs the terrain and the 06-09 surface, with a pass hold-out of the class bias).
26. **Publication assembly** `[implemented: workflows/paper/p96–p99, render_claims]`. Claims register
    (`publication/evidence_matrix.csv`, Paper-1 schema + evidence_level/tier) → tables T01–T28 with manifest (T28: what changed
    after the review of 2026-09-28) → figures Fig01–Fig11 + supplement (FigS01–S15) → three executable notebooks → Streamlit
    dashboard (`apps/dashboard`). One command per reproducibility level (`workflows/paper/rebuild.py`, `docs/REPRODUCIBILITY.md`). Terminology frozen in `publication/TERMINOLOGY.md` (enforced by `tests/test_terminology_freeze.py`; consolidation review 2026-09-26). Wording rules: model
    numbers are agreement with weak labels; not observed is not dry; area semantics named; cropland-associated SAR candidates.

27. **Reservoir side (p95f, p95h, p95m, p95i)** `[implemented; context]`. Daily pool surface interpolated along the chainage between
    the SWOT outlet (in Paper 1's frame), the Nikopol post and the Rozumivka gauge (a censored upper bound caps its day: 12–13 June
    are upper estimates); G-REALM is a plotted check, not an anchor. Pool area, volume, depth (Fig10) and the daily-mean effective
    release (T21); the design curve bounded to its table (T27); the day the bed fell dry from the model (6–13 June) and Sentinel-2
    on 20 June (Fig11, T23b); the model extent and Sentinel-1 (wet mud) in FigS08.

28. **RF surface classes by date (p102)** `[implemented 2026-10-01: workflows/m6/p102_rf_surface_by_date.py; a product for the
    hydraulic-model work (Papers 4–5), not a Paper 3 result]`. The per-date counterpart of RF20: a random forest (60 trees, min leaf
    20, balanced subsample, half-sample bootstrap) on the seven indices of ONE Sentinel-2 date (the frozen p25 zone stacks, 20 m;
    optionally day-of-year sin/cos), ESA WorldCover 2021 as the weak target on the same lattice (3 × 3 purity; on the date WATER needs
    MNDWI > 0 and the non-water classes MNDWI < 0.3), training dates 2021-01-01 .. 2023-06-05, up to 1 500 cells per class, zone and
    date. Evaluation fixed before the run: 5-fold spatial-block CV (5 km global UTM blocks) and a temporal hold-out (fit 2021–2022,
    test 2023 pre-breach) for both variants; the production variant is the higher temporal-hold-out macro F1 (ties → spectral).
    UNCERTAIN where the top probability < 0.5. One class + one probability GeoTIFF per date for the four zones (pool + lower
    Dnipro, delta, estuary, floodway), 2017–2026 — the drained reservoir bed of 2024–2026 included — in the bulk root
    (`rf_by_date/<ZONE>/`); `tables/p102_rf_date_{inventory,metrics,class_area}.csv`; `figures/p102/`; dashboard layers of the
    best-observed date of each month (Maps, Surface context). Land-cover classes, read together with the k10e surface-state map of
    the same date. Agreement with the WorldCover-2021-derived weak reference fell from a spatially blocked macro F1 of 0.764 to 0.698
    in the 2023 temporal hold-out (dates 1 January – 5 June 2023, before the breach): a temporal-transfer degradation relative to the
    reference labels -- RF error, real change 2021→2023, WorldCover label error and season together -- not an independently validated
    2023 land-cover accuracy. After the breach no reference exists (WorldCover 2021 shows the pool as water), so for post-breach dates
    and 2024–2026 the classes are predictions in the WorldCover-trained ontology and no agreement is reported. Confusion matrices and
    per-class scores of both evaluations (`p102 --step evaluate`: `tables/p102_rf_date_{metrics,confusion_long}.csv`,
    `figures/p102/confusion_*.png`) and the transition matrices of the drained bed (`--step transition`: WorldCover 2021 class ×
    dominant RF class of each growing season, inside the pre-breach pool and outside it as a control; `tables/p102_rf_date_transition.csv`,
    `figures/p102/ZONE_1_pool_transition.png`), with the k10e state of the same dates as the physical reading of each RF class on the
    bed (`tables/p102_rf_date_rf_vs_k10e_pool.csv`): WorldCover has no exposed-sediment class, so the forest labels much of the
    exposed bed "built-up" (k10e: dry bare sediment, sparse herbaceous), and its "forest" on the bed is k10e reed / flooded vegetation
    -- the classes inside the pool are not usable for roughness without a rule (see NEXT_STEPS 2026-10-02). Stacks of 17 more dates (49 zone-dates of 15 June – 30 July 2023) were added on
    2026-10-02 by running SWOT-DNIPRO's frozen p25 unchanged on the event store (`workflows/m6/p25x_zone_stack_extension.py`,
    `tables/p25x_zone_stack_extension.csv`); 2023-07-31 and 2024-05-25 stay without a stack (orbit-edge slivers below p25's 200 MB
    scene filter). The Paper 3 tables built on the stacks (p95h: T23–T25) exclude the extension dates.
29. **The full flood mask (p103)** `[implemented 2026-10-01: workflows/m6/p103_flood_envelope.py]`. The envelope of the primary
    reconstruction over the whole event, packaged from frozen products: classes pre-breach water (optical), normally wet
    (model-only part of the normal regime), new inundation of the nominal run on ≥ 1 day (26 May – 10 July), of the Monte-Carlo
    median world only (P ≥ 0.5 on an evaluated day), marginal (0.05 ≤ P < 0.5); max P per cell; the Sentinel-1 envelope of the event
    dates (new dark water / observed never dark / dark already on 1–2 June / never observed). Per zone and as a mosaic (ZONE_2 owns
    the overlap) with GeoJSON polygons of the total and of the new-inundation envelope (`floodplain_dyn/_envelope/`, bulk);
    `tables/p103_flood_envelope.csv` (corridor: total water envelope 867 km², new inundation 264 nominal / 267 median world);
    `figures/p103_flood_envelope.png`; dashboard layers `terrain_envelope`, `s1_envelope`. first_day / last_day / duration /
    max_depth of the nominal run sit next to it. Terrain-reconstructed, not an observation; the hydraulic model's wetted-extent input.

### Key references
- Wagner et al. 2026, RSE 333:115108 — CEMS Global Flood Monitoring; observed flood vs reference water. `Wagner_2026`
- Martinis et al. 2022, RSE 278:113077 — S1/S2 seasonal + permanent reference water. `Martinis_2022`
- Bonafilia et al. 2020, CVPRW 835–845 — Sen1Floods11; permanent / flood / total water. `Bonafilia_2020`
- Bai et al. 2021, Remote Sensing 13:2220 — S1+S2 deep learning for permanent vs temporary water. `Bai_2021`
- Bioresita et al. 2019, IJRS 40:9026–9049 — S1+S2 time-series fusion, permanent and temporary water. `Bioresita_2019`
- Twele et al. 2016, IJRS 37:2990–3004 — fully automated S1 flood processing chain. `Twele_2016`
- Tupas et al. 2023, Water 15:4034 — HAND/topographic prior for S1 flood maps. `Tupas_2023`
- Giustarini et al. 2013, IEEE TGRS 51:2417–2430 — SAR change detection for urban flooding. `Giustarini_2013`
