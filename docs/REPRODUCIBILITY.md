# Reproducibility

## Quick reproduction (minutes)

Not currently possible: no release bundle (small prepared feature crops, metrics tables, simplified vectors,
manifests) has been assembled yet. `case_studies/kakhovka_2023/notebooks/00_kakhovka_flood_state_reconstruction.ipynb`
is a narrative walkthrough with `[planned]`-tagged cells for anything that would require the bundle; it does not
execute end-to-end today.

## Full reproduction (hours–days)

Raw S1/S2 → preprocessing → 10 m stacks → composites → freeze gate → BASE_CLASS → M2 → event association →
(classification, fusion, validation of a real flood-state product: not yet implemented) → products.

Resource facts carried over from the source repository's audit (NOT re-measured on this package):
`frames10` ≈ 8.5 GB, legacy 20 m `frames` ≈ 18 GB, S1 cache ≈ 82 GB, a B3 composite ≈ 24 GB uncompressed
(BIGTIFF required; the 10 m composite build is strip-wise/memory-bounded because its 20 m predecessor ran out of
memory). Total working data > 100 GB.

- CPU: multi-core; RAM: dictated by strip-wise processing (`TBD`, not measured on this package); disk: ≥ 200 GB
  working space (estimate, `TBD`).
- GPU: **optional**. The M2 Random Forest (`fusion/`) is scikit-learn, CPU-only. The SAR coherence pilot
  (`sar/p82_coherence_graph.py`) runs SNAP's `gpt` in a Docker container, also CPU-only, but is memory-sensitive
  (see that module's header comment on a live "Java heap space" incident and its `-q`/`-c`/`-x` mitigation).
- Stack: Python ≥ 3.10 (record actual version at freeze — `TBD`), numpy, pandas, rasterio, scipy, scikit-learn,
  pyproj, shapely, requests, python-dotenv. SNAP + Docker only for the SAR coherence pilot. Exact versions:
  pin in `environment.yml` from a frozen environment — `TBD`.
- OS: developed on Linux/WSL2; not tested elsewhere.
- Determinism: fixed seeds recorded per script (see `case_studies/kakhovka_2023/config/model.yaml`'s note on the
  two different seed values used in different scripts, not yet reconciled); non-deterministic steps (network
  fetch retries, WSL2 memory-pressure retries) are documented where they occur but not eliminated.

## What this repository cannot reproduce yet

- Raw data fetch: several `io/` scripts depend on credentials (`.env` with CDSE username/password) and on a
  `p1_targeted_fetch`-equivalent download/verify helper that was not migrated (see
  `provenance/UNRESOLVED_DEPENDENCIES.md`).
- The Kakhovka zone/reservoir domain geometries (`ZONE_1..4`, the pre-breach reservoir pool) are not vendored
  into this repository; `src/floodstate_eo/_kakhovka_legacy_config.py` reads them from sibling repository
  checkouts as a temporary bridge (see that module's docstring).
- A full end-to-end run from raw scenes to `semantic_state` has not been executed inside this repository's own
  layout — only migrated, not re-run.
