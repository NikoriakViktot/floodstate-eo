# Validation of the Stage-1 response to the code review of 2026-09-28 (terrain reconstruction rev 6, Monte-Carlo rev 2)

Scope: the uncertainty engine of the terrain reconstruction (review findings F01–F07, F20; the F12 mask; the F16 gauge path),
recomputed end to end on 2026-09-29. Ledger of every finding and decision: `docs/CODE_REVIEW_ACTIONS_2026-09-29.md`.
Rule of the bundle unchanged: every number in the manuscript resolves to a table cell; tables are rebuilt from committed inputs.

## 1. Code-level checks (no bulk data)

| check | where | result |
|---|---|---|
| unit-variance field, stated correlation, nested structures, nugget, seed reproducibility | `tests/test_terrain_fields.py` | pass (std 1 ± 3 %, correlation at one range e⁻¹ ± 0.05) |
| superseded bilinear-zoom field (the reviewer's diagnostic) | same | std 0.66 reproduced |
| connectivity on the whole graph (reviewer's 6-cell example) | `tests/test_terrain_connectivity.py` | mosaic 6 cells, zonal 3 |
| union lattice, owner pasted last, misaligned grids refused | `tests/test_terrain_mosaic.py` | pass |
| bounded interpolation (F13 helper) | `tests/test_terrain_interp.py` | NaN outside the table |
| vertical frame declared and identical; EPSG:9902 grid sampling | `tests/test_terrain_vertical.py` | pass |
| every water-surface term once (+0.1 m closure → +0.1 m on an active cap) | `tests/test_p95_wse_field.py` | pass |
| row median bit-identical to `np.nanmedian` | same | pass |
| MC contract: coherent draws, new ⊆ potential, total quantiles from the total ensemble, pre-breach new = 0, seam pocket connected, no perturbation on bed cells | `tests/test_p95e_contract.py` | pass |

## 2. Reproduction gate and attribution (real data, nominal runs)

| check | result |
|---|---|
| rev-6 code in legacy mode vs the committed rev-5 tables | 138/138 pooled, 276/276 zone and 33/33 S1-validation rows identical, every cell |
| + lattice anchored in map coordinates | A_new 7 June 235.3 → 235.6 km² |
| + connectivity on the union mosaic | 235.6 → 235.6 km² (seam check T11i: 0.0 km² difference on 7, 9, 13 June) |
| + FABDEM-only residual table per zone, bed uncorrected | 235.6 → 243.2 km² (rev 6 nominal); W_total 779.4 → 796.6; regime 5 June 488.7 → 501.3 |
| fast row median and exact cropping in p95e | stored draws 0 and 5 recomputed: max difference 0.0 |

## 3. Terrain-error model (p95j)

FABDEM-sourced cells only (source 3/4; 630 446 night ICESat-2 segments; bed segments excluded): pooled medians trees +1.65 m,
wetland +0.56, grass +0.32, built +0.17, bare +0.28, cropland +0.09 m; NMAD 1.69 / 0.43 / 0.61 / 0.63 / 0.99 / 0.29 m (T18b).
Consistent in sign and order with Paper 2's 'A FABDEM, WorldCover' rows (which pool the estuary frame as well). Standardized
residual, robust estimator: nugget 0.08 + 0.50 exp(−h/123 m) + 0.42 exp(−h/1172 m), relative misfit 1.1 % (single exponential:
9.3 %); sill 0.96 ≈ 1, so the NMAD scale is consistent (T18c, FigS11).

## 4. Checks recomputed

| check | result |
|---|---|
| F12 mask (terrain-only inside the S1 footprint) | ZONE_4 terrain-only 6 764 → 4 821 ICESat-2 segments; S1-only ≥ 2 m: residual median +0.03 / +0.02 m as delivered, −0.02 / −0.15 m corrected; ≤ 0.7 % of segments below the surface (T15) |
| water-surface support 7 June | 371 km² of water from nodes within 3 km, 426 km² from the nearest node farther away (T11g) |
| 3-day maximum gap (sensitivity) | 7 June unchanged; delta corridor 9 June 86 → 150 km², 13 June 68 → 130 km² (structural, not in the MC) |
| gauge zeros from the yearbook sheet headers (maintainer's check of the cm-above-zero conversion) | 80575 Kalynivske **−1.34 m BS** (the first p95k run used +1.34: every level 2.68 m too high — corrected, all Kalynivske numbers recomputed); 80564 56.34 (passport 56.44); 80568 27.57, 80561 81.99, 98027 −5.00, 80805 −5.00 as used; the Kherson series of the engine = yearbook daily values exactly (max diff 0.00 m) |
| daily means vs highest levels (table 1.2) | peaks, rises and records now from the yearbook's highest level ('Вищий', cross-checked with the ingested monthly maxima): Kalynivske 772 cm (daily-mean max 758), Mykolaiv 602 cm (596), Kherson 1056 cm (= its 8 June daily value) |
| Inhulets gauge Kalynivske 80575 (independent) | backwater 0.58 → 6.59 m EVRF2019 (highest level, 10 June; record since 1927); reconstruction at the gauge +0.77 m before the breach, +0.04 … +9.50 m on 6–20 June (metres too high on 6–9 June: a Dnipro node 39.5 km away), maximum 7 instead of 10 June (T17c/T17d) |
| Kalynivske withheld (D-INHULETS): event-relative error, timing, recession | e_rise +8.74 m on 6 June, +0.69 m on the gauge maximum, −0.72 m on 14 June (the reconstruction drains ahead of the valley), within ±0.25 m only from 26 June; peak 3 days early; rise +9.28 vs +5.87 m; the decimetre absolute agreement on 13–18 June is a coincidence of the +0.77 m pre-breach offset and the recession lag; support at the gauge constant (one Dnipro node, 39.5 km, 46 of 46 days) (T17c/T17d) |
| support of the Inhulets valley's new area, 7 June (nominal) | 41.4 km²: within 3 km of a node 0.4 km² (1 %), nearest node > 20 km away 35.6 km² (86 %), cross-river (Dnipro) fallback 11.3 km² (27 %) (T17d, T17g, T17h) |
| Kalynivske as an extra water-surface node (sensitivity) | S1 CSI in the Inhulets valley up on every event date (0.285 → 0.317 on 9 June); valley new area 7 June 41.4 → 19.2 km²; corridor unchanged (T12, T13) |
| liman gauge Mykolaiv 98027 (independent) | 0.17 → 1.22 m EVRF2019 (highest level, 8 June; record since 1963; rise 1.05 m); the serving Dnipro node (E 457.6 km) unobserved 6–22 June → reconstruction flat at ~0.34 m, −0.82 m on 8 June (T17e/T17f) |

## 5. Monte-Carlo (p95e rev 2; 1000 coherent worlds, seed 20260929)

| check | result |
|---|---|
| gate: draw 0 (nominal, unperturbed) vs the p95 nominal run | 276 / 276 zone-date-region rows; new area and volume identical; total area identical in cells (one row differs by 0.1 km² only through the rounding of the tie 147.05) |
| terrain-error field on the base cells | std 1.000 (0.985–1.016 over the worlds); bed cells unperturbed (asserted) |
| before the breach | new area 0 in every world and zone (asserted) |
| corridor, 7 June | A_new 262.4 [250.3–277.8] km² (nominal 243.2, below p05); W_total 791.2 [767.3–819.4] km² (nominal 796.6, inside); V_new 626.8 [585.0–674.0] hm³ (nominal 514.5) |
| corridor, 9 / 13 June | A_new 216.1 [201.3–236.0] / 136.0 [119.1–186.8] km²; W_total 741.3 [703.4–779.3] / 633.5 [561.1–712.0] km² |
| corridor, 5 June (pre-breach) | W_total 472.7 [444.9–498.2] km², nominal 501.3 ABOVE p95: terrain noise disconnects part of the shallow pre-breach water (connectivity is nonlinear in the noise) |
| day of the areal maximum (corridor A_new) | 7 June in 766 worlds, 8 June in 234 (T12c) |
| Inhulets valley / p42 domain, 7 June | A_new 41.3 [39.0–43.3] / 170.7 [159.2–184.3] km² |

### Ablation (T11d; 250 worlds per variant, corridor, 7 June; nominal A_new 243.2 km², nominal regime 810.5 km²)

| variant | A_new median [p05–p95], km² | W_total, km² | pre-breach regime (median), km² | V_new median, hm³ |
|---|---|---|---|---|
| full budget | 262.4 [250.8–276.0] | 790.5 [767.0–817.9] | 787.6 | 626 |
| terrain only | 266.9 [255.9–279.7] | 790.3 [775.6–810.2] | 775.2 | 646 |
| water surface only | 239.4 [236.1–244.6] | 795.6 [775.1–825.4] | 827.4 | 500 |
| baseline fixed at the nominal regime | 248.2 [234.2–265.3] | 790.5 [767.0–817.9] | 810.5 | 542 |
| + per-day SWOT term 0.05 m | 258.7 [245.4–276.4] | 791.5 [764.8–820.1] | 792.7 | 614 |
| without the interpolation term | 262.3 [250.9–276.4] | 789.2 [770.4–816.0] | 786.4 | 628 |
| without the nugget | 262.0 [249.7–278.3] | 790.5 [766.5–820.5] | 787.4 | 625 |
| interpolation error scaled by the RMSE (heavy tails) | 258.3 [235.0–310.1] | 786.8 [713.7–873.7] | 811.9 | 611 |
| single exponential instead of the nested covariance | 262.1 [254.0–273.9] | 791.1 [770.0–817.8] | 788.4 | 627 |

Reading: the nominal run lies below the ensemble because of the terrain term acting through the connectivity. With the terrain
perturbed the pre-breach regime shrinks (775 vs 810.5 km²; consistent with zero-mean noise disconnecting shallow pre-breach water
from the seed network, since connectivity is nonlinear in the terrain — the corridor's W_total on
5 June is 472.7 [444.9–498.2] km² against the nominal 501.3), while on the peak days the water stands metres above the floodplain
and W_total barely moves; the new area of each world is therefore larger. The water-surface term alone reproduces the nominal
median (239 vs 243 km²) and widens W_total; it enlarges the regime (827 km²), as expected for a union over eleven pre-breach days
with independent day-to-day node errors (a maximum over noisy days is biased upward). Fixing the regime
at the nominal removes most of the offset (248 km²). The width of A_new on the peak day is mainly terrain, that of W_total mainly
water surface; the upper tail on 13 June is the interpolation term (p95 186.7 → 138.9 km² without it). The heavy-tailed RMSE
scaling of the interpolation error (instead of the NMAD) is the single largest sensitivity of the budget (W_total 7 June
713.7–873.7 km²): the choice of the scale estimator matters and is reported, not hidden.

### Convergence (T11c, FigS12; corridor, 7 June; two independent seeds, 1000 worlds each)

| quantity | seed 20260929, n = 1000 | seed 20261001, n = 1000 | n = 40 (seed 1) |
|---|---|---|---|
| A_new p05 / p50 / p95, km² | 250.3 / 262.4 / 277.8 | 248.9 / 263.0 / 279.9 | 252.9 / 265.0 / 276.2 |
| W_total p05 / p50 / p95, km² | 767.3 / 791.2 / 819.4 | 767.1 / 791.0 / 820.4 | 771.5 / 791.8 / 823.2 |
| V_new p05 / p50 / p95, hm³ | 585.0 / 626.8 / 674.0 | 581.9 / 628.9 / 679.0 | 586.3 / 626.5 / 668.1 |
| bootstrap 95 % of the A_new p95 estimator | 276.8–278.6 | 278.5–281.8 | 272.4–284.4 |
| worlds with the areal maximum on 7 / 8 June | 76.6 / 23.4 % | 75.2 / 24.8 % | 75 / 25 % |

The two seeds agree within 2.1 km² (A_new), 1.0 km² (W_total) and 5 hm³ (V_new) at every quantile; the tail quantiles
are the slowest (13 June A_new p95: 186.8 vs 190.0 km²). 1000 worlds is the publication ensemble; the nominal run is a
diagnostic (draw 0).

### Water-surface offset sensitivity (T11e, FigS13; nominal terrain, nominal regime; corridor, 7 June)

| offset δ, m | −0.20 | −0.10 | −0.05 | 0 | +0.05 | +0.10 | +0.20 |
|---|---|---|---|---|---|---|---|
| W_total, km² | 754.6 | 776.0 | 785.1 | 796.6 | 808.3 | 818.8 | 839.8 |
| A_new, km² | 228.9 | 237.0 | 240.2 | 243.2 | 247.4 | 250.8 | 268.9 |

W_total responds almost linearly (~210–230 km² per metre: 0.1 m ≈ 21 km², 2.7 %); A_new responds with 62–76 km² per metre
around the nominal surface and 181 km² per metre above +0.1 m, where further low ground connects — a threshold behaviour of the
connectivity, not a new model.

## 6. Old (06441cf, rev 5, 40 draws) vs new (rev 6, 1000 coherent worlds); corridor

| date | quantity | rev 5: MC median [p05–p95] (nominal) | rev 6: MC median [p05–p95] (nominal) |
|---|---|---|---|
| 5 June | W_total, km² | — (488.5) | 472.7 [444.9–498.2] (501.3) |
| 7 June | A_new, km² | 246.7 [237.6–254.9] (235.3) | 262.4 [250.3–277.8] (243.2) |
| 7 June | W_total, km² | 790.5 [781.4–798.7] (779.1) — shifted interval | 791.2 [767.3–819.4] (796.6) — own ensemble |
| 7 June | V_new, hm³ | 565.9 [545.4–595.7] (509.0) | 626.8 [585.0–674.0] (514.5) |
| 9 June | A_new, km² | 196.5 [190.5–207.9] (182.8) | 216.1 [201.3–236.0] (187.9) |
| 13 June | A_new, km² | 117.9 [114.3–128.7] (108.4) | 136.0 [119.1–186.8] (107.7) |

Why: the rev-5 field had a marginal std of 0.66 instead of 1 (F02) and each zone its own world (F01); W_total's interval was a
shift of the nominal total by the new-area quantiles (F04); the interpolation error came from one-day triplets only (F05). The
rev-6 intervals are about twice as wide for A_new and three times for W_total; the medians move up by 8 % (A_new) and 11 %
(V_new) at the peak, the W_total median is unchanged.

## 7. Decisions after the maintainer's review of these numbers (Stage 1 frozen)

| check / decision | result |
|---|---|
| support classes of the new area (p95l; direct ≤ 3 km, extrapolated 3–10 km, weak > 10 km) | classes add up to the p95 new area on 276 / 276 zone-region-day rows (asserted); corridor 7 June: direct 73.1, extrapolated 108.5, weak 61.7 km² (25 %), supported core 181.5 km² vs the 10 km cap run 180.2 km²; weak share 7 % on 9 June, 2 % on 13 June; p42 domain 6 %; Inhulets 93 % (cross-river 11.3 km²) (T11k, T11l) |
| D-SUPPORT | full reconstruction = primary; supported core and cap run reported next to it; no hard cutoff |
| D-EMU | emulator = computational diagnostic outside the evidence path (T12d); absent from T12 (asserted by `tests/test_terminology_freeze.py`), Fig04, claims, dashboard headline |
| claims C01–C03, C07 | statements rewritten with the rev-6 numbers, the day-of-maximum distribution, the support classes, the withheld gauge and the baseline-connectivity mechanism |
| full draw tables | release assets; `tables/p95e_draws_checksums.csv` in git (sha256, rows, seed, code commit) |
| hydraulic modelling | manuscript §3.2 (static model) and §5 (why a hydraulic model is needed; Dale et al. 2026, Kasmalkar et al. 2024, Barnes et al. 2021 — Crossref-verified, quotes checked against the article page / Europe PMC / Crossref abstracts) |
| figures and dashboard | FigS14 (support map on 7 June; daily core vs full; weak share) and FigS15 (withheld gauges) rendered from the committed tables and the p95l raster; dashboard AppTest: 8 / 8 pages without exception, the Maps page also with the support colouring on; notebook 01: 18 / 18 cells executed |

Stage 2 (F09 → F10 → F08 → F11 → F12 hold-out) and Stage 3 (F13–F19, text pass) are separate passes.
