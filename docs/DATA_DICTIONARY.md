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

## Paper 3 products (2026-09-25)

| Product | Producer | Status |
|---|---|---|
| `frames10/<F>/m6_labels_v003_A.tif` (11 bands: ontology, event water, reference state/reason/domain, May counts, W_pre state/valid, seasonal flag) | `workflows/m6/p77d_m6_labels_v003_final.py --variant A` | FROZEN (D3, `tables/m6_labels_v003_A_FROZEN.json`); weak reference labels |
| `frames10/<F>/m6/<ARM>[_v003A][_sNN]_score.tif` (uint16 ×10000, nodata 65535) | `workflows/m6/p86_m6_train_arm.py` | agreement with weak labels, not a flood probability |
| `frames10/<F>/m6_split_{v1,s7p5,s15,s20}_role.tif` | `workflows/m6/p84_m6_split_b1b2.py` | v1 FROZEN; sNN = block-size sensitivity |
| `frames10/<F>/p73_rf20/surface_class_20m.tif` | `workflows/m6/p73_rf20_surface.py` | FROZEN context product |
| `floodplain_dyn/<ZONE>[_rule][_variant]/{duration_days,first_day,last_day,max_depth_m,depth_2023-06-08_m}.tif, daily_new.npz` | `workflows/m6/p95_hand_daily_inundation.py` | terrain-reconstructed new inundation; FABDEM-derived, not redistributed |
| `floodplain_dyn/_icesat_check/<ZONE>_{cat,wse}0609.tif` | `workflows/m6/p95c_icesat2_check.py --step rasters` | diagnostic |
| `floodplain_dyn/<ZONE>_connected_ceiling/{flood_envelope_class,flood_envelope_pmax,s1_observed_envelope}.tif`; `floodplain_dyn/_envelope/{flood_envelope_class_20m,flood_envelope_pmax_20m,s1_observed_envelope_20m}.tif, {total_water_envelope,new_inundation_envelope}.geojson` | `workflows/m6/p103_flood_envelope.py` | the full flood mask: envelope of the primary reconstruction (classes 1–5), max P of the Monte-Carlo worlds, Sentinel-1 envelope of the event dates; mosaic + polygons (EPSG:4326) for the hydraulic model; FABDEM-derived, not redistributed |
| `zone_spectral/<ZONE>/<date>_{indices,class,water3,scl}.tif` | SWOT-DNIPRO `scripts/p25_zone_spectral_stacks.py` (frozen); 49 zone-dates of 15 Jun – 30 Jul 2023 added 2026-10-02 by `workflows/m6/p25x_zone_stack_extension.py` (the same script, unchanged, on the event store; `tables/p25x_zone_stack_extension.csv`) | per-date 7 indices (int16 ×10000), k10e class, water3 (0 land / 1 water / 255 not observed), SCL on the 20 m zone grids, 2017–2026; full list in `case_studies/kakhovka_2023/PRODUCT_INVENTORY.md` (p104); the paper's p95h tables exclude the extension dates |
| `rf_by_date/<ZONE>/<date>_{rf,rfp}.tif, <date>_rf.json`; `frames10/_m6/p102_rf_date_model.joblib` | `workflows/m6/p102_rf_surface_by_date.py` | RF surface (land-cover) class and top-class probability for every Sentinel-2 date of the four p25 zones, 2017–2026 (pool included); WorldCover 2021 weak target; product for the hydraulic model, not a Paper 3 result |
| `publication/tables/T*.csv` + `manifest.json` | `workflows/paper/p96_paper_tables.py` | committed, regenerated with `--check` |
| `apps/dashboard/data/**` (classed PNG overlays, GeoJSON, manifest) | `workflows/paper/p98_dashboard_layers.py` | committed, ≤ 100 MB |
