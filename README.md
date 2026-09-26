# FloodState-EO

**Status: v0.3.0-rc1 — canonical EO preprocessing and temporal-composite pipeline, plus the Kakhovka 2023 case study
of Paper 3: a physical daily-inundation reconstruction (SWOT + gauge water surface × terrain, with an uncertainty budget),
its cross-sensor and altimetric checks, an RF20 surface-context product, and U-Net experiments on frozen weak labels
(v002 / v003_A). A canonical multi-class FLOOD_STATE product still does not exist; every model number is agreement with
weak reference labels. See `case_studies/kakhovka_2023/publication/` (claims register, tables, figures, manuscript),
the notebooks under `case_studies/kakhovka_2023/notebooks/` and the Streamlit dashboard under `apps/dashboard/`.**

FloodState-EO is developed within the broader GeoHydroAI research ecosystem.

## Overview *(implemented + planned)*

A framework for reconstructing surface state during flood events from multisensor Earth observation evidence:
Sentinel-1 SAR and Sentinel-2 optical imagery, combined with a pre-event land-state context, to describe what a
piece of ground *was* before an event and what an optical/SAR *event response* on it does and does not support.

## Scientific motivation *(implemented)*

Binary water/not-water mapping is insufficient where the surface is ambiguous: bare sand and sediment behave
spectrally like water at some thresholds, flooded vegetation under reed does not look like open water at all, and
Sentinel-1 backscatter change has no single predictable sign (specular water lowers it, double-bounce under
standing vegetation can raise it). A pre-event context — what a pixel *was* — narrows what an event-window
response *can mean*, without asserting it proves inundation on its own.

## From water detection to flood-state reconstruction *(partial: preprocessing implemented, inference planned)*

The pipeline as designed: PRE + EVENT + TRACE temporal evidence + pre-event surface context + multisensor
agreement/disagreement → flood-state classes → an uncertainty statement per cell. Today, the PRE/EVENT/TRACE
optical composite stack and the pre-event surface-state layer (`BASE_CLASS`) exist and are frozen; a canonical,
multi-class flood-state output at 10 m does not yet exist (see docs/METHODS.md and the case study's own status
notes).

## Conceptual framework *(implemented: PRE/EVENT/TRACE, BASE_CLASS · planned: fusion, uncertainty)*

| Concept | Status |
|---|---|
| PRE / EVENT / TRACE temporal windows | implemented |
| Per-date Sentinel-2 index stacks (7 indices) on a canonical 10 m lattice | implemented |
| Temporal composites (median/min/max, signed change) | implemented |
| Observation-count semantics (`n_obs`, never a gate) | implemented |
| Pre-event surface-state layer (`BASE_CLASS`) | implemented |
| Sentinel-1 orbit-matched event-change channels | implemented (feature extraction only, no classifier reads them yet) |
| Sentinel-1/SAR interferometric coherence | implemented (engineering pilot; see the case study) |
| M2 (Sentinel-2-only) evidence layer, RF-based | implemented, on the 10 m canonical frames |
| Multi-class flood-state classifier (M0–M5) | **planned** — not defined in this repository yet |
| S1/S2 evidence fusion with uncertainty | **planned** — design only |

## Supported evidence sources *(implemented)*

Sentinel-2 L2A (indices, SCL-based validity, BOA-offset-corrected reflectance), Sentinel-1 IW GRD/SLC (orbit-aware
backscatter composites, event-change channels, interferometric coherence), ESA WorldCover 2021 (external pre-event
land-cover context).

## Surface-state context *(implemented)*

`BASE_CLASS`: a pre-breach land-state classification (open water / vegetation-agriculture / bare sand / built-up /
wetland / other-dry / uncertain), built exclusively from PRE-window evidence, deliberately blind to any event or
flood evidence, so that combining it with event evidence later is a genuine combination of two independent
statements.

## Multisensor EO *(implemented: separate S1 and S2 evidence · planned: combined)*

Sentinel-1 and Sentinel-2 evidence are currently produced and validated **separately**; they are not yet combined
into one flood-state product. See docs/METHODS.md §15 for the fusion design.

## Flood-state inference *(planned)*

Not yet part of the canonical package. See `case_studies/kakhovka_2023/` for the current best evidence products
(an M2 Sentinel-2-only score, and BASE_CLASS × M2 "event association", which is explicitly weaker than a flood
claim) and their limitations.

## Uncertainty *(planned)*

Design only: evidence-status codes are referenced in the methods literature this package draws on, not yet
implemented as a product.

## Validation *(implemented, case-study-specific)*

Nested nested spatial cross-validation (5 km blocks, block/buffered regimes, bootstrap over spatial blocks, never
over pixels) for the M2 evidence layer. See `case_studies/kakhovka_2023/README.md` and docs/METHODS.md §16–19.

## Repository structure

```
src/floodstate_eo/     event-agnostic framework code (io, optical, sar, spatial, fusion, surface_state,
                        validation, visualization)
case_studies/           one case study per event; Kakhovka 2023 is the first
docs/                   method, data-dictionary and reproducibility documentation
provenance/             migration manifest and source-commit provenance for every file in src/
tests/                  unit tests + the event-agnostic grep gate
```

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick start

No runnable end-to-end quick start exists yet — the case study's data is not bundled in this repository (see
`docs/REPRODUCIBILITY.md`). See `case_studies/kakhovka_2023/notebooks/00_kakhovka_flood_state_reconstruction.ipynb`
for the narrative walkthrough of what is implemented and what is planned.

## Case studies

- [Kakhovka 2023](case_studies/kakhovka_2023/README.md) — the dam-breach flood on the lower Dnipro, the first
  and currently only case study.

## Reproducibility

See `docs/REPRODUCIBILITY.md`.

## Data availability

No raw or bulk data ships in this repository. See `docs/REPRODUCIBILITY.md` and
`case_studies/kakhovka_2023/manifests/` (populated as Phase 6/data-policy work proceeds).

## Citation

See `CITATION.cff`.

## License

MIT — see `LICENSE`.

## Authors

Viktor Nikoriak
