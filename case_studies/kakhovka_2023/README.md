# Case study: Kakhovka 2023

## Scientific objectives

Reconstruct the surface-state response of the lower Dnipro to the 2023-06-06 Kakhovka dam breach from Sentinel-1
and Sentinel-2 evidence, distinguishing what the pre-breach surface *was* from what the event response *shows*,
without over-claiming that an optical or SAR event signal alone proves open-water inundation.

## Study area

Three axis-aligned processing frames in EPSG:32636, fixed 2026-09-21 (`config/study_area.yaml`): B1 (dam to
Kherson), B2 (Kherson to the delta) and B3 (the delta with the liman). Every cell inside a frame is processed and
carries an explicit status; nothing is silently excluded.

## Event

The 2023-06-06 Kakhovka HPP dam breach and the resulting flood on the lower Dnipro floodplain and delta.

## Processing frames (from `p52a_processing_frames_qa.py`)

| Frame | Extent | Legacy zone overlap |
|---|---|---|
| B1 | dam → Kherson | ZONE_4_DAM_TO_KHERSON_FLOODWAY |
| B2 | Kherson → delta | ZONE_2_KHERSON_DELTA |
| B3 | delta with the liman | ZONE_3_DNIPRO_BUG_ESTUARY |

## Temporal windows

PRE 2022-01-01..2023-06-05, EVENT 2023-06-07..2023-07-31, TRACE 2023-08-01..2023-11-30
(`config/temporal_windows.yaml`; two other window definitions exist elsewhere in the source repository and were
not reconciled with this one before migration — see that file's note).

## Input datasets

Sentinel-2 L2A (native SAFE archives preferred; legacy 20 m per-zone stacks used only where no native archive
exists, and lineage-tagged so the two are never mixed within one date), Sentinel-1 IW GRD orbit-aware backscatter
caches, Sentinel-1 IW SLC (for the coherence pilot), ESA WorldCover 2021. See `docs/DATA_DICTIONARY.md` and
`docs/REPRODUCIBILITY.md`; scene manifests are not yet populated under `manifests/`.

## Why the problem is difficult

Sand and bare sediment produce false water under simple spectral thresholds; flooded vegetation under reed cover
does not look like open water optically or in SAR; permanent/pre-existing water must not be counted as new flood;
observation coverage is incomplete and uneven across the three frames and must never be conflated with "dry";
Sentinel-1 and Sentinel-2 disagree substantially on what they each recover (see `p69c_maps.py`'s recovery figures:
optical recovery of the Sentinel-1 peak observation is 62% in B1, 23% in B2, 13% in B3).

## Sentinel-1 workflow

Orbit-aware backscatter composites; per-scene event-change channels differenced against each event scene's own
relative-orbit median in dB (never linear gamma0 — see `sar/p71_s1_event_change.py`'s docstring for the measured
consequence of getting that wrong); an interferometric-coherence engineering pilot over frame B2 across all four
relative orbits (`sar/p80_slc_pairing_manifest.py`–`p83_coherence_qc.py`).

## Sentinel-2 workflow

Per-date index stacks (7 indices, BOA-offset-corrected) on the canonical 10 m lattice, strip-processed to stay
memory-bounded; PRE/EVENT/TRACE temporal composites (84 bands per frame, including two pre-event baseline
variants); an independent freeze gate that recomputes every stored value from the per-date stacks rather than
trusting the builder's own claims (`validation/p54c_composites_10m_freeze_gate.py`).

## Surface-state context

`BASE_CLASS` (`surface_state/p69a_base_class.py`): a pre-breach-only land-state classification, forbidden from
reading any event, TRACE or Sentinel-1 evidence.

## Flood-state classification

**Two unreconciled evidence paths exist in the migrated code, and neither is the canonical flood-state product:**

- A legacy Random Forest on the 20 m zone grid (`p51_rf_flood_optical.py` in the source repository) — **not
  migrated into this repository.** Numbers from it, if cited anywhere, must be labelled "legacy 20 m zone grid,
  not comparable."
- M2 (`fusion/p65b_m2_spatial_cv.py`, `fusion/p66_production_m2.py`, `fusion/p67b_production_candidate.py`): a
  Sentinel-2-only Random Forest score on the canonical 10 m frames, spatially cross-validated, with a
  `PRODUCTION_CANDIDATE` status — explicitly not final.

Neither path is a multi-class flood-state classifier; neither implements the M0–M5 design referenced elsewhere as
future work.

## Evidence fusion

`fusion/p69b_event_association.py` combines the frozen `BASE_CLASS` with the frozen M2 candidate's threshold
masks into `semantic_state` (e.g. `FLOOD_ASSOCIATED_VEGETATION_AGRICULTURE`) — deliberately named weaker than
"flood": it states that a known pre-event surface shows a flood-associated event response, not that open water
was observed on it. Pre-existing water is always excluded from this headline and reported as a separate
diagnostic. This is NOT the doc-19-§11 multisensor fusion design (S1 draws / S2 edits, evidence codes 2–6) —
that design is not implemented in any migrated file.

## Spatial validation

Nested spatial cross-validation for M2: 5 km blocks, 5 outer folds × 3 inner folds, a "buffered" regime that
removes training cells within 3.5 km of the test population, bootstrap confidence intervals over spatial blocks.
See `config/validation.yaml`.

## Uncertainty

Not implemented for this case study; design only (see root README).

## Output classes

`BASE_CLASS` (8 classes, PRE-only) and `semantic_state` (9 classes, event-association) are real, frozen products.
`FLOOD_STATE`, `URBAN_SCORE`, `UNCERTAINTY` and `FINAL_FLOOD_MASK` are **PROPOSED / NOT YET CANONICAL**.

## Publication products

Not yet assembled in this repository; see `publication/` (currently empty).

## Limitations

See `docs/METHODS.md`'s per-section `[implemented]`/`[proposed]` tags and `docs/DATA_DICTIONARY.md`'s
per-product status column for the authoritative, itemised list. In summary: no multi-class flood-state
classifier exists; the two evidence paths (legacy RF, M2) are not reconciled; M2's own recall is unstable under
spatial transfer; optical recovery of Sentinel-1's peak observation is well under half in two of three frames.

## Reproduction

See `docs/REPRODUCIBILITY.md`. No raw or bulk data ships with this repository.

## Citation

See the root `CITATION.cff`.
