# Reproducibility

Three levels, in increasing cost. Every number in the manuscript and the dashboard resolves to a committed table cell
(`case_studies/kakhovka_2023/publication/tables/manifest.json` lists the source file and sha256 behind every table).

## Level 1 — manuscript reproduction (minutes, no bulk data)

What: the publication tables T01–T22, the claims register, the table-only figures and the three executable notebooks,
from committed derived data only.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,paper]"
python case_studies/kakhovka_2023/workflows/paper/p96_paper_tables.py --check   # re-derives T01..T20 and diffs
python case_studies/kakhovka_2023/workflows/paper/render_claims.py            # claims.md from evidence_matrix.csv
python case_studies/kakhovka_2023/workflows/paper/p97_paper_figures.py --tables-only
python case_studies/kakhovka_2023/workflows/paper/p99_build_notebooks.py --build --execute
pytest                                                                         # incl. test_paper_tables, test_dashboard_bundle
```
Inputs: `case_studies/kakhovka_2023/tables/*.csv|json`, `runs/*/eval_d1a/*.csv`, `runs/compare_*/*.csv`, `publication/`.
The dashboard (`streamlit run apps/dashboard/streamlit_app.py`) also belongs to this level: it reads the same tables and the
pre-rendered layers in `apps/dashboard/data/` (1.9 MB, manifest with sha256).

## Level 2 — analytical reproduction (hours, documented processed datasets)

What: regenerate the metrics from the processed products that the case study keeps outside git under
`$FLOODSTATE_DATA_ROOT` (≈ 100 GB): 10 m frames (`frames10/<F>/`: S1 event-change channels `s1_change.tif`, index stacks,
composites, labels v002 / v003_A, U-Net scores, RF20 classes), the S1 per-scene water caches (`s1_zone_cache/`), the seamless
DEM, HAND and WorldCover frames, the terrain reconstruction products (`floodplain_dyn/`). Registry:
`case_studies/kakhovka_2023/manifests/*.csv` (sha256 where computed), `provenance/MIGRATION_MANIFEST.csv`.

Scripts, in order (each writes its own tables/manifest): `workflows/m6/p77d` (labels v003_A; frozen, reproduces bit for bit
on the committed tree, `tables/m6_labels_v003_A_FROZEN.json`) → `p84` (split; `--block-m` for the sensitivity splits) →
`p86 --arm … --labels …` (arms; ~3 min each on an RTX A4000) → `p88`, `p90` (comparisons) → `p92`, `p93`, `p94` (accounting,
per-date series) → `p95j` (FABDEM − ICESat-2 residual statistics and variogram; SWOT-DNIPRO environment for the ATL08 pull)
→ `p95` (terrain reconstruction, rev 6; primary `connected_ceiling`, sensitivities `--rule`, `--closure`, `--dem-bias`, `--margin`,
`--connectivity`, `--seed-network`, `--max-gap-days`, `--wse-river-aware`, `--fallback-max-km`, `--inhulets-gauge-node`; `--terrain-table legacy_c_seamless --evaluation
zonal_legacy --coarse-anchor grid_legacy --no-rasters` reproduces rev 5 exactly) → `p95k` (independent gauges Kalynivske / Mykolaiv from the UkrHMC 2023 yearbook store of icesat2-atl13-kakhovka; run once
before and once after `p95 --inhulets-gauge-node`, whose gauge node it supplies) → `p95c` (ICESat-2 check; the second step
needs the SWOT-DNIPRO environment) → `p95d` (disagreement ontology) → `p95e` (Monte-Carlo rev 2: `--n 1000` primary, `--mode
ablation --n 250`, `--mode convergence --seed 20261001 --days key`, `--mode wse-threshold`; forked workers, resumable chunks in
`tables/_p95e_chunks/`; about 50 s per world and core; the full draw tables `p95e_draws*.csv.gz` are release assets, not in git —
`tables/p95e_draws_checksums.csv` gives their sha256, rows, seed and code commit) → `p95l` (support classes of the new area) →
`p95g` (emulator, a diagnostic only), `p95b`, `p95f`, `p95i` → `p96`, `p97`, `p98`, `p99`.
Determinism: fixed seeds (20260923 for splits/bootstraps, 20260929 / 20261001 for the Monte-Carlo, one RNG stream per draw
index, so results do not depend on the number of workers; 20260929 for the p95j variogram pair sampling); GPU training is deterministic up to
cuDNN non-determinism (thresholds are re-frozen on validation per run and stored).

## Level 3 — full raw-data reproduction (days; licences)

What: rebuild the processed products from raw archives: Sentinel-1 GRD/RTC and Sentinel-2 L2A (Copernicus, CDSE credentials
in `.env`), SWOT L2_HR_RiverSP v2.0 (PO.DAAC), ICESat-2 ATL08/ATL13 (NSIDC), FABDEM v1.2 (CC BY-NC-SA 4.0), ESA WorldCover 2021,
the UkrHMC gauge yearbooks, the legacy bathymetry (Paper 2). Several producers of the processed inputs are not in this
repository (see `provenance/UNRESOLVED_DEPENDENCIES.md`: the S1 GRD/RTC NPZ cache builder, the M3 per-scene classifier,
the SWOT/ICESat-2 vertical chain of Paper 1 in SWOT-DNIPRO, the seamless DEM of Paper 2). This level is therefore a
cross-repository exercise; its data volume is > 100 GB and its compute is dominated by the 10 m composites and the
S1 caches. Not attempted end-to-end from this repository.

## Submission snapshot

Manuscript numbers are tied to a tagged release (`v0.3.0-rc1`) and its Zenodo DOI, never to the mutable `main` branch.
The tables manifest records the git commit that generated them.

## Environment facts

Developed on Linux / WSL2, Python 3.12, numpy 2.5, pandas 3.0, rasterio 1.5, torch 2.14 + segmentation_models_pytorch 0.5
(the `m6` extra), matplotlib 3.11; RTX A4000 16 GB for training. RAM ≥ 16 GB for the terrain reconstruction (20 m zone
rasters), ≥ 24 GB recommended for the 10 m U-Net arms.
