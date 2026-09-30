# floodstate-eo v0.3.0-rc2 — the response to the scientific and code review of 2026-09-28 (draft for the maintainer)

Package version `0.3.0rc2`; the tag name, the GitHub release and the Zenodo DOI are the maintainer's.

## What this release is

Paper 3 of the Kakhovka series (daily inundation after the dam breach, reconstructed from the observed water surface and terrain)
after a major revision: every finding of the review (F01–F20) answered in code, tests and tables, the manuscript rewritten in one
pass under a hierarchy of evidence, and all heights aligned with the validated vertical frame of Paper 1 (SWOT-DNIPRO release
`paper1-v6`). **What changed, with the old and new value, the reason and the effect on each conclusion: table T28**
(`case_studies/kakhovka_2023/publication/tables/T28.md`).

## Headline results (numbers from the tables of this release)

<!-- filled from T12 / T12c / T11k / T17d / T21 / T07s / T06s at release time -->

## Main changes since v0.3.0-rc1

- Uncertainty engine (F01–F07, F20): 1000 coherent Monte-Carlo worlds (one terrain field over the whole domain, one water-surface
  realization, the pre-breach baseline rebuilt per world), a terrain-error covariance fitted to FABDEM − ICESat-2 residuals, every
  error term once, the total water-surface interval from its own ensemble, convergence with a second seed, an ablation of every term;
  support classes of the new inundation; two withheld gauges (Kalynivske, Mykolaiv).
- Independence and ML (F08–F12): RF20 on global blocks without overlap duplication; the M2 threshold calibrated out of fold and without
  the post-event window → the canonical weak labels v004; every arm with three training seeds; the HAND effect on cropland retracted
  (did not reproduce); a pass hold-out of the ICESat-2 class bias.
- Consistency and release (F13–F19): bounded hypsometry, a consistent weekly balance, figure–caption quantities tested, one-command
  rebuild per reproducibility level, a tiny open geodomain, a load-bearing input manifest with sha256, an environment lock, one version.
- Depth maps (maximum depth of new inundation, reservoir depth) and the emptying of the reservoir from Sentinel-2 (Fig11).
- Paper 1 v6 alignment (rev 7): Kherson gauge at its own EPSG:9902 step, the pool outlet in the production chain, the FABDEM terrain and
  ICESat-2 ground raised to the production chain (Paper 2 to be corrected at the source).

## Reproduce

`docs/REPRODUCIBILITY.md`: level 0 (tiny geodomain, seconds), level 1 (tables, figures, manuscript from committed outputs, minutes),
level 2 (the full chain from the processed inputs). The full Monte-Carlo draw tables are release assets (checksums in
`case_studies/kakhovka_2023/tables/p95e_draws_checksums.csv`).
