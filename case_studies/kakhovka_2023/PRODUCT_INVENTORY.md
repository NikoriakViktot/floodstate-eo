# Map products of the Kakhovka case study — where they are

Generated 2026-10-02 03:46 by `workflows/paper/p104_product_inventory.py` from the files on disk; do not edit by hand. Bases: **BULK** = the bulk data root (`FLOODSTATE_DATA_ROOT`, here `/mnt/f/data_kakhovka_dem_swot`), **REPO** = this repository, **SIB** = the SWOT-DNIPRO sibling repository. One row per family and zone / frame; `y2017…y2026` = dates per year. Machine-readable: `tables/p104_product_inventory.csv`.

## 1. Index maps (continuous values)

### `zone_indices` — 7 indices int16 x10000 (NDVI, NDWI, MNDWI, NDMI, BSI, AWEIsh, NDTI; nodata -32768), one file per date
*Where:* `BULK/zone_spectral/*/*_indices.tif` · *producer:* SWOT-DNIPRO p25 (frozen) + p25x extension of 2026-10-02 · *grid:* 20 m zone grid, EPSG:32636

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ZONE_1_KAKHOVKA_LOWER_DNIPRO | 166 | 166 | 2017-07-01 | 2026-09-12 | 1 | 1 | 2 | 2 | 28 | 33 | 26 | 24 | 22 | 27 |
| ZONE_2_KHERSON_DELTA | 78 | 78 | 2017-04-30 | 2026-09-10 | 3 | 7 | 5 | 4 | 2 | 6 | 24 | 8 | 10 | 9 |
| ZONE_3_DNIPRO_BUG_ESTUARY | 97 | 97 | 2017-01-10 | 2026-09-05 | 7 | 9 | 9 | 4 | 7 | 7 | 25 | 10 | 12 | 7 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 72 | 72 | 2017-09-12 | 2026-09-09 | 2 | 2 | 6 | 0 | 3 | 2 | 35 | 8 | 8 | 6 |

### `frame_indices` — the same 7 indices int16 x10000, with <date>_valid.tif (cloud-free cells)
*Where:* `BULK/frames10/*/indices/20??-??-??.tif` · *producer:* floodstate-eo p54a (src/floodstate_eo/optical/p54a_frame_index_stacks_10m.py) · *grid:* 10 m canonical frames B1-B3

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B1 | 77 | 77 | 2022-02-13 | 2023-11-10 | 0 | 0 | 0 | 0 | 0 | 29 | 48 | 0 | 0 | 0 |
| B2 | 35 | 35 | 2022-02-13 | 2023-11-10 | 0 | 0 | 0 | 0 | 0 | 12 | 23 | 0 | 0 | 0 |
| B3 | 43 | 43 | 2022-02-13 | 2023-11-10 | 0 | 0 | 0 | 0 | 0 | 12 | 31 | 0 | 0 | 0 |

### `frame_composites` — window composites: median / min / max of the 7 indices for PRE (and PRE-seasonal), n_obs, pre_water_frac
*Where:* `BULK/frames10/*/composite_pre*.tif` · *producer:* floodstate-eo p54b · *grid:* 10 m canonical frames

| unit | n_files | examples |
|---|---|---|
| B1 | 2 | composite_preall.tif, composite_preseas.tif |
| B2 | 2 | composite_preall.tif, composite_preseas.tif |
| B3 | 2 | composite_preall.tif, composite_preseas.tif |

### `zone_regime_medians` — median of each index per regime PRE_BREACH / BREACH_DRAWDOWN / POST_BREACH
*Where:* `SIB/outputs/rasters/zone?/zone?_*_*_median_20m.tif` · *producer:* SWOT-DNIPRO p25 composites (frozen; p25x does not rebuild them) · *grid:* 20 m zone grid

| unit | n_files | examples |
|---|---|---|
| zone1 | 21 | zone1_AWEIsh_BREACH_DRAWDOWN_median_20m.tif, zone1_AWEIsh_POST_BREACH_median_20m.tif, zone1_AWEIsh_PRE_BREACH_median_20m.tif, zone1_BSI_BREACH_DRAWDOWN_median_20m.tif, zone1_BSI_POST_BREACH_median_20m.tif, zone1_BSI_PRE_BREACH_median_20m.tif |
| zone2 | 21 | zone2_AWEIsh_BREACH_DRAWDOWN_median_20m.tif, zone2_AWEIsh_POST_BREACH_median_20m.tif, zone2_AWEIsh_PRE_BREACH_median_20m.tif, zone2_BSI_BREACH_DRAWDOWN_median_20m.tif, zone2_BSI_POST_BREACH_median_20m.tif, zone2_BSI_PRE_BREACH_median_20m.tif |
| zone3 | 21 | zone3_AWEIsh_BREACH_DRAWDOWN_median_20m.tif, zone3_AWEIsh_POST_BREACH_median_20m.tif, zone3_AWEIsh_PRE_BREACH_median_20m.tif, zone3_BSI_BREACH_DRAWDOWN_median_20m.tif, zone3_BSI_POST_BREACH_median_20m.tif, zone3_BSI_PRE_BREACH_median_20m.tif |
| zone4 | 21 | zone4_AWEIsh_BREACH_DRAWDOWN_median_20m.tif, zone4_AWEIsh_POST_BREACH_median_20m.tif, zone4_AWEIsh_PRE_BREACH_median_20m.tif, zone4_BSI_BREACH_DRAWDOWN_median_20m.tif, zone4_BSI_POST_BREACH_median_20m.tif, zone4_BSI_PRE_BREACH_median_20m.tif |

### `tile_stacks_legacy` — per-scene index stacks of the reservoir side
*Where:* `BULK/spectral_indices/*_stack.tif` · *producer:* SWOT-DNIPRO k10e stacks (legacy) · *grid:* MGRS tile grids (eastern tiles)

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T36TWS | 28 | 28 | 2023-05-16 | 2025-11-01 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 10 | 11 | 0 |
| T36TWT | 28 | 28 | 2023-05-19 | 2025-11-01 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 10 | 11 | 0 |
| T36TXT | 30 | 30 | 2023-05-18 | 2025-10-29 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 10 | 11 | 0 |
| T36UXU | 3 | 3 | 2023-09-23 | 2023-11-07 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 |

## 2. Classified maps (classified indices, surface and land-cover classes)

### `k10e_by_date` — k10e surface classes from the indices of the date: 1 open water, 2 shallow/mixed water, 3 wet sediment, 4 dry bare sediment, 5 sparse herbaceous, 6 dense herbaceous, 7 reed / flooded vegetation, 8 built, 9 ambiguous; 0 = not observed (thresholds NDVI 0.15/0.3, NDMI 0.1, BSI 0.1)
*Where:* `BULK/zone_spectral/*/*_class.tif` · *producer:* SWOT-DNIPRO p25 (sentinel_preprocess.classify) + p25x · *grid:* 20 m zone grid

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ZONE_1_KAKHOVKA_LOWER_DNIPRO | 166 | 166 | 2017-07-01 | 2026-09-12 | 1 | 1 | 2 | 2 | 28 | 33 | 26 | 24 | 22 | 27 |
| ZONE_2_KHERSON_DELTA | 78 | 78 | 2017-04-30 | 2026-09-10 | 3 | 7 | 5 | 4 | 2 | 6 | 24 | 8 | 10 | 9 |
| ZONE_3_DNIPRO_BUG_ESTUARY | 97 | 97 | 2017-01-10 | 2026-09-05 | 7 | 9 | 9 | 4 | 7 | 7 | 25 | 10 | 12 | 7 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 72 | 72 | 2017-09-12 | 2026-09-09 | 2 | 2 | 6 | 0 | 3 | 2 | 35 | 8 | 8 | 6 |

### `k10e_regime_mode` — most frequent k10e class per regime
*Where:* `SIB/outputs/rasters/zone?/zone?_class_*_mode_20m.tif` · *producer:* SWOT-DNIPRO p25 composites (frozen) · *grid:* 20 m zone grid

| unit | n_files | examples |
|---|---|---|
| zone1 | 3 | zone1_class_BREACH_DRAWDOWN_mode_20m.tif, zone1_class_POST_BREACH_mode_20m.tif, zone1_class_PRE_BREACH_mode_20m.tif |
| zone2 | 3 | zone2_class_BREACH_DRAWDOWN_mode_20m.tif, zone2_class_POST_BREACH_mode_20m.tif, zone2_class_PRE_BREACH_mode_20m.tif |
| zone3 | 3 | zone3_class_BREACH_DRAWDOWN_mode_20m.tif, zone3_class_POST_BREACH_mode_20m.tif, zone3_class_PRE_BREACH_mode_20m.tif |
| zone4 | 3 | zone4_class_BREACH_DRAWDOWN_mode_20m.tif, zone4_class_POST_BREACH_mode_20m.tif, zone4_class_PRE_BREACH_mode_20m.tif |

### `index_display_classes_reservoir` — each of the 7 indices in display classes (e.g. NDVI <0.15 / 0.15-0.3 / 0.3-0.5 / >0.5) and k10e, the pool + 1 km
*Where:* `REPO/apps/dashboard/data/reservoir/s2/*_[A-Z]*.png` · *producer:* p98 from p95h (classify_index) · *grid:* PNG overlay, EPSG:4326

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 35 | 5 | 2023-05-06 | 2023-09-08 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 0 |

### `index_display_classes_figures` — cloud-free period composites of every index in display classes, k10e and S1 VV: delta and floodway, before / after
*Where:* `REPO/case_studies/kakhovka_2023/figures/m6_v003A/p95zm_*.png` · *producer:* p95zm · *grid:* figures

| unit | n_files | examples |
|---|---|---|
| all | 20 | p95zm_delta_AWEIsh.png, p95zm_delta_BSI.png, p95zm_delta_MNDWI.png, p95zm_delta_NDMI.png, p95zm_delta_NDTI.png, p95zm_delta_NDVI.png |

### `rf_by_date` — land-cover class 1 water, 2 cropland, 3 grass, 4 forest, 5 shrub, 6 wetland/reed, 7 built, 8 bare/sand, 9 other, 10 uncertain; <date>_rfp.tif = top-class probability
*Where:* `BULK/rf_by_date/*/*_rf.tif` · *producer:* floodstate-eo p102 (random forest on the indices of the date) · *grid:* 20 m zone grid

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ZONE_1_KAKHOVKA_LOWER_DNIPRO | 166 | 166 | 2017-07-01 | 2026-09-12 | 1 | 1 | 2 | 2 | 28 | 33 | 26 | 24 | 22 | 27 |
| ZONE_2_KHERSON_DELTA | 78 | 78 | 2017-04-30 | 2026-09-10 | 3 | 7 | 5 | 4 | 2 | 6 | 24 | 8 | 10 | 9 |
| ZONE_3_DNIPRO_BUG_ESTUARY | 97 | 97 | 2017-01-10 | 2026-09-05 | 7 | 9 | 9 | 4 | 7 | 7 | 25 | 10 | 12 | 7 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 72 | 72 | 2017-09-12 | 2026-09-09 | 2 | 2 | 6 | 0 | 3 | 2 | 35 | 8 | 8 | 6 |

### `rf20_pre_event` — RF20 land-cover classes from PRE-event composites (+ max score, uncertain, per-class scores)
*Where:* `BULK/frames10/*/p73_rf20*/surface_class_20m.tif` · *producer:* floodstate-eo p73 (rev 2 for B1, B2; rev 1 inference for B3) · *grid:* 20 m frame grid

| unit | n_files | examples |
|---|---|---|
| B1 | 2 | surface_class_20m.tif |
| B2 | 2 | surface_class_20m.tif |
| B3 | 1 | surface_class_20m.tif |

### `worldcover` — WorldCover 2020 and 2021 classes
*Where:* `BULK/worldcover_frames/*/wc_*_20m.tif` · *producer:* ESA WorldCover (fetched in SWOT-DNIPRO) · *grid:* 20 m zone grid

| unit | n_files | examples |
|---|---|---|
| ZONE_1_KAKHOVKA_LOWER_DNIPRO | 2 |  |
| ZONE_2_KHERSON_DELTA | 2 |  |
| ZONE_3_DNIPRO_BUG_ESTUARY | 2 |  |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 2 |  |

### `dynamic_world_annual` — annual class probabilities (11 bands)
*Where:* `BULK/dynamic_world_annual/dw_*.tif` · *producer:* Google Dynamic World (annual, fetched in SWOT-DNIPRO) · *grid:* EPSG:4326, ~30 m

| unit | n_files | examples |
|---|---|---|
| zone_1 | 10 |  |
| zone_2 | 10 |  |
| zone_3 | 2 |  |

### `dynamic_world_frames` — Dynamic World annual mode on the zone grid
*Where:* `BULK/dynamic_world_frames/*/dw_*_20m_from_annual.tif` · *producer:* SWOT-DNIPRO · *grid:* 20 m zone grid

| unit | n_files | examples |
|---|---|---|
| ZONE_1_KAKHOVKA_LOWER_DNIPRO | 7 |  |
| ZONE_2_KHERSON_DELTA | 7 |  |
| ZONE_3_DNIPRO_BUG_ESTUARY | 2 |  |

### `ground_class` — pre-event ground classes: dry before the event / vegetated wetland / open reference water / other
*Where:* `BULK/floodplain_dyn/_weak_labels/ground_class.tif` · *producer:* floodstate-eo p95x · *grid:* 20 m union grid

| unit | n_files | examples |
|---|---|---|
| all | 1 | ground_class.tif |

## 3a. Water masks -- Sentinel-2

### `zone_water3` — 0 land, 1 water, 255 not observed; water = NDWI > 0 AND MNDWI > 0 AND SCL permits water
*Where:* `BULK/zone_spectral/*/*_water3.tif` · *producer:* SWOT-DNIPRO p25 + p25x (frozen rule) · *grid:* 20 m zone grid

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ZONE_1_KAKHOVKA_LOWER_DNIPRO | 166 | 166 | 2017-07-01 | 2026-09-12 | 1 | 1 | 2 | 2 | 28 | 33 | 26 | 24 | 22 | 27 |
| ZONE_2_KHERSON_DELTA | 78 | 78 | 2017-04-30 | 2026-09-10 | 3 | 7 | 5 | 4 | 2 | 6 | 24 | 8 | 10 | 9 |
| ZONE_3_DNIPRO_BUG_ESTUARY | 97 | 97 | 2017-01-10 | 2026-09-05 | 7 | 9 | 9 | 4 | 7 | 7 | 25 | 10 | 12 | 7 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 72 | 72 | 2017-09-12 | 2026-09-09 | 2 | 2 | 6 | 0 | 3 | 2 | 35 | 8 | 8 | 6 |

### `zone_scl` — ESA Scene Classification of the date (cloud, shadow, water, ...)
*Where:* `BULK/zone_spectral/*/*_scl.tif` · *producer:* SWOT-DNIPRO p25 + p25x · *grid:* 20 m zone grid

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ZONE_1_KAKHOVKA_LOWER_DNIPRO | 165 | 165 | 2017-07-01 | 2026-09-12 | 1 | 1 | 2 | 2 | 28 | 33 | 26 | 23 | 22 | 27 |
| ZONE_2_KHERSON_DELTA | 78 | 78 | 2017-04-30 | 2026-09-10 | 3 | 7 | 5 | 4 | 2 | 6 | 24 | 8 | 10 | 9 |
| ZONE_3_DNIPRO_BUG_ESTUARY | 97 | 97 | 2017-01-10 | 2026-09-05 | 7 | 9 | 9 | 4 | 7 | 7 | 25 | 10 | 12 | 7 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 72 | 72 | 2017-09-12 | 2026-09-09 | 2 | 2 | 6 | 0 | 3 | 2 | 35 | 8 | 8 | 6 |

### `frame_water_layers` — new S2 water / water on pre-breach water per date (the GeoTIFF is not stored: the rule is applied on the fly)
*Where:* `REPO/apps/dashboard/data/s2/*_water.png` · *producer:* p98 (watermask rule on the p54a 10 m stacks, as p94) · *grid:* PNG overlay

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 23 | 23 | 2023-06-05 | 2023-08-27 | 0 | 0 | 0 | 0 | 0 | 0 | 23 | 0 | 0 | 0 |

### `zone1_crosscheck` — water + valid, reservoir crosscheck dates
*Where:* `BULK/ZONE_1_s2_crosscheck/*.npz` · *producer:* SWOT-DNIPRO p15 (frozen) · *grid:* 20 m ZONE_1 grid (cell centres)

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 24 | 24 | 2019-03-01 | 2023-09-23 | 0 | 0 | 2 | 0 | 0 | 8 | 14 | 0 | 0 | 0 |

### `prebreach_water_frequency` — percent of observed dates with water, per regime
*Where:* `SIB/outputs/rasters/zone?/zone?_water_frac_*_20m.tif` · *producer:* SWOT-DNIPRO p25 composites (frozen; p60 reads the PRE_BREACH ones) · *grid:* 20 m zone grid

| unit | n_files | examples |
|---|---|---|
| zone1 | 3 | zone1_water_frac_BREACH_DRAWDOWN_20m.tif, zone1_water_frac_POST_BREACH_20m.tif, zone1_water_frac_PRE_BREACH_20m.tif |
| zone2 | 3 | zone2_water_frac_BREACH_DRAWDOWN_20m.tif, zone2_water_frac_POST_BREACH_20m.tif, zone2_water_frac_PRE_BREACH_20m.tif |
| zone3 | 3 | zone3_water_frac_BREACH_DRAWDOWN_20m.tif, zone3_water_frac_POST_BREACH_20m.tif, zone3_water_frac_PRE_BREACH_20m.tif |
| zone4 | 3 | zone4_water_frac_BREACH_DRAWDOWN_20m.tif, zone4_water_frac_POST_BREACH_20m.tif, zone4_water_frac_PRE_BREACH_20m.tif |

### `water_occurrence_2022` — water occurrence 2022
*Where:* `BULK/lower_dnipro_water_occurrence/*.tif` · *producer:* SWOT-DNIPRO · *grid:* EPSG:4326, ~30 m

| unit | n_files | examples |
|---|---|---|
| all | 1 |  |

## 3b. Water masks -- Sentinel-1 (and the radar backscatter they come from)

### `s1_event_masks` — per-scene dark-water mask + valid footprint (event caches June 2023; _pre2023 = April-June 2023)
*Where:* `BULK/s1_zone_cache/*/per_scene_water.npz` · *producer:* SWOT-DNIPRO p0v/p0w M3 masks · *grid:* 20 m zone grids

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ZONE_2_KHERSON_DELTA_flood_june2023 | 1 | 11 | 2023-06-01 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | 0 |
| ZONE_2_KHERSON_DELTA_flood_june2023_pre2023 | 1 | 15 | 2023-04-15 | 2023-05-28 | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 0 | 0 | 0 |
| ZONE_3_DNIPRO_BUG_ESTUARY_flood_june2023 | 1 | 11 | 2023-06-01 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | 0 |
| ZONE_4_FLOODWAY_june2023_s20 | 1 | 11 | 2023-06-01 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | 0 |
| ZONE_4_FLOODWAY_june2023_s32 | 1 | 11 | 2023-06-01 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | 0 |
| ZONE_4_FLOODWAY_june2023_s32_pre2023 | 1 | 15 | 2023-04-15 | 2023-05-28 | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 0 | 0 | 0 |

### `s1_mask_variants` — per scene: V0, Vz*, Vf*, VL, VM, VS*, VT, VC* water-mask variants + valid
*Where:* `BULK/s1_variants/*/*.npz` · *producer:* SWOT-DNIPRO (S1 water-rule variants) · *grid:* 20 m zone grids

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ZONE_1_KAKHOVKA_LOWER_DNIPRO | 40 | 39 | 2019-02-17 | 2023-06-21 | 0 | 0 | 8 | 3 | 0 | 0 | 28 | 0 | 0 | 0 |
| ZONE_2_KHERSON_DELTA | 160 | 160 | 2017-03-21 | 2026-09-01 | 9 | 14 | 15 | 21 | 12 | 3 | 21 | 12 | 32 | 21 |
| ZONE_3_DNIPRO_BUG_ESTUARY | 192 | 192 | 2019-01-01 | 2023-11-29 | 0 | 0 | 106 | 25 | 22 | 18 | 21 | 0 | 0 | 0 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 119 | 119 | 2017-04-27 | 2026-08-29 | 3 | 5 | 6 | 14 | 6 | 4 | 37 | 13 | 17 | 14 |

### `s1_reservoir_vh` — VH dark surface (open water or smooth wet mud; per-date Otsu) + observed
*Where:* `BULK/reservoir_maps/s1/*.npz` · *producer:* floodstate-eo p95h · *grid:* 20 m reservoir grid

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 10 | 10 | 2023-06-01 | 2023-06-21 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 |

### `s1_backscatter` — calibrated VV / VH backscatter + coverage per scene (not a mask; the masks above are made from it)
*Where:* `BULK/s1_zone_cache/*/20??-??-??_orb*.npz` · *producer:* SWOT-DNIPRO S1 zone cache · *grid:* 20 m zone grids

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KAKHOVKA_DAM_TO_KHERSON_flood_june2023 | 11 | 11 | 2023-06-01 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | 0 |
| ZONE_1_KAKHOVKA_LOWER_DNIPRO | 75 | 74 | 2019-02-17 | 2023-11-24 | 0 | 0 | 8 | 3 | 1 | 14 | 48 | 0 | 0 | 0 |
| ZONE_1_reservoir_corrected | 33 | 32 | 2019-02-17 | 2023-06-21 | 0 | 0 | 8 | 0 | 0 | 1 | 23 | 0 | 0 | 0 |
| ZONE_2_KHERSON_DELTA | 150 | 150 | 2017-03-21 | 2026-09-01 | 9 | 14 | 15 | 21 | 12 | 3 | 11 | 12 | 32 | 21 |
| ZONE_2_KHERSON_DELTA_flood_june2023 | 11 | 11 | 2023-06-01 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | 0 |
| ZONE_2_KHERSON_DELTA_flood_june2023_pre2023 | 17 | 17 | 2023-04-15 | 2023-06-02 | 0 | 0 | 0 | 0 | 0 | 0 | 17 | 0 | 0 | 0 |
| ZONE_3_DNIPRO_BUG_ESTUARY | 182 | 182 | 2019-01-01 | 2023-11-29 | 0 | 0 | 106 | 25 | 22 | 18 | 11 | 0 | 0 | 0 |
| ZONE_3_DNIPRO_BUG_ESTUARY_flood_june2023 | 11 | 11 | 2023-06-01 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | 0 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 119 | 119 | 2017-04-27 | 2026-08-29 | 3 | 5 | 6 | 14 | 6 | 4 | 37 | 13 | 17 | 14 |
| ZONE_4_FLOODWAY_june2023_s20 | 11 | 11 | 2023-06-01 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | 0 |
| ZONE_4_FLOODWAY_june2023_s32 | 13 | 13 | 2023-06-01 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 0 | 0 | 0 |
| ZONE_4_FLOODWAY_june2023_s32_pre2023 | 21 | 21 | 2023-04-15 | 2023-06-02 | 0 | 0 | 0 | 0 | 0 | 0 | 21 | 0 | 0 | 0 |
| ZONE_4_grid_crosscheck_for_zone1 | 7 | 7 | 2019-03-08 | 2023-11-16 | 0 | 0 | 1 | 0 | 0 | 1 | 5 | 0 | 0 | 0 |

## 3c. Reconstruction, flood and state maps (terrain_reconstructed, Monte-Carlo, labels)

### `terrain_daily_new` — daily new inundation 26 May - 10 July 2023 (bit-packed) + baseline (normal regime) + normally_wet
*Where:* `BULK/floodplain_dyn/*_connected_ceiling/daily_new.npz` · *producer:* floodstate-eo p95 (primary run) · *grid:* 20 m zone grids

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ZONE_2_KHERSON_DELTA | 1 | 46 | 2023-05-26 | 2023-07-10 | 0 | 0 | 0 | 0 | 0 | 0 | 46 | 0 | 0 | 0 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 1 | 46 | 2023-05-26 | 2023-07-10 | 0 | 0 | 0 | 0 | 0 | 0 | 46 | 0 | 0 | 0 |

### `terrain_cellprob` — count of worlds with new inundation (P = count / 1000)
*Where:* `BULK/floodplain_dyn/*_connected_ceiling/p95e_cellprob*.tif` · *producer:* floodstate-eo p95e (1000 coherent worlds) · *grid:* 20 m zone grids

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ZONE_2_KHERSON_DELTA | 50 | 25 | 2023-06-06 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 0 | 0 | 0 |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 50 | 25 | 2023-06-06 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 0 | 0 | 0 |

### `terrain_summaries` — duration_days, first_day, last_day, max_depth_m, depth_2023-06-08_m of the nominal run
*Where:* `BULK/floodplain_dyn/*_connected_ceiling/[dfml]*_*.tif` · *producer:* floodstate-eo p95 · *grid:* 20 m zone grids

| unit | n_files | examples |
|---|---|---|
| ZONE_2_KHERSON_DELTA | 7 | depth_<date>_m.tif, duration_days.tif, first_day.tif, flood_envelope_class.tif, flood_envelope_pmax.tif, last_day.tif |
| ZONE_4_DAM_TO_KHERSON_FLOODWAY | 7 | depth_<date>_m.tif, duration_days.tif, first_day.tif, flood_envelope_class.tif, flood_envelope_pmax.tif, last_day.tif |

### `flood_envelope` — the full flood mask: envelope classes, max P, Sentinel-1 envelope; polygons of the total and of the new-inundation envelope
*Where:* `BULK/floodplain_dyn/_envelope/*` · *producer:* floodstate-eo p103 · *grid:* 20 m mosaic + GeoJSON (EPSG:4326)

| unit | n_files | examples |
|---|---|---|
| all | 5 | flood_envelope_class_20m.tif, flood_envelope_pmax_20m.tif, new_inundation_envelope.geojson, s1_observed_envelope_20m.tif, total_water_envelope.geojson |

### `state_masks` — WATER / DRY / UNKNOWN + source + flags per day
*Where:* `BULK/floodplain_dyn/_weak_labels/state_*.tif` · *producer:* floodstate-eo p95x · *grid:* 20 m union grid

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 25 | 25 | 2023-06-06 | 2023-06-30 | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 0 | 0 | 0 |

### `reservoir_model` — modelled pool water per day 26 May - 13 June 2023 (+ depth_<date>.tif, exposed_day.tif, exposed_day_observed.tif)
*Where:* `BULK/reservoir_maps/model/wet_daily.npz` · *producer:* floodstate-eo p95h / p95f · *grid:* 50 m pool grid

| unit | n_files | n_dates | first | last | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 1 | 19 | 2023-05-26 | 2023-06-13 | 0 | 0 | 0 | 0 | 0 | 0 | 19 | 0 | 0 | 0 |

### `weak_labels` — LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN (canonical: m6_labels_v004; the others are provenance)
*Where:* `BULK/frames10/*/m6_labels_*.tif` · *producer:* floodstate-eo p77 / p77d · *grid:* 10 m frames

| unit | n_files | examples |
|---|---|---|
| B1 | 7 | m6_labels_v002.tif, m6_labels_v002_notrace.tif, m6_labels_v003.tif, m6_labels_v003_A.tif, m6_labels_v003_B.tif, m6_labels_v003_final.tif |
| B2 | 7 | m6_labels_v002.tif, m6_labels_v002_notrace.tif, m6_labels_v003.tif, m6_labels_v003_A.tif, m6_labels_v003_B.tif, m6_labels_v003_final.tif |

### `unet_scores` — U-Net arm scores (thresholds in the tables)
*Where:* `BULK/frames10/*/m6/*_score.tif` · *producer:* floodstate-eo p86 / p88 · *grid:* 10 m frames

| unit | n_files | examples |
|---|---|---|
| B1 | 28 | U0d_score.tif, U0d_v003A_score.tif, U0d_v004_s20261001_score.tif, U0d_v004_s20261002_score.tif, U0d_v004_score.tif, U0z_score.tif |
| B2 | 28 | U0d_score.tif, U0d_v003A_score.tif, U0d_v004_s20261001_score.tif, U0d_v004_s20261002_score.tif, U0d_v004_score.tif, U0z_score.tif |

## 3d. External products

### `unosat_3614` — operational flood extents (ICEYE, Sentinel), literature_reported: context, never validation
*Where:* `BULK/external/unosat/3614/**/*.*` · *producer:* UNITAR-UNOSAT activation package FL20230606UKR · *grid:* shapefile / GeoJSON

| unit | n_files | examples |
|---|---|---|
| all | 547 | FL20230606UKR_SHP.zip, ICEYE_20230607_AffectedUrbanArea_KhersonskaOblast_UKR.CPG, ICEYE_20230607_AffectedUrbanArea_KhersonskaOblast_UKR.dbf, ICEYE_20230607_AffectedUrbanArea_KhersonskaOblast_UKR.prj, ICEYE_20230607_AffectedUrbanArea_KhersonskaOblast_UKR.sbn, ICEYE_20230607_AffectedUrbanArea_KhersonskaOblast_UKR.sbx |

## 4. Maps in the dashboard (pre-rendered PNG overlays, `apps/dashboard/data/`)

570 layers, 59.9 MB. Maps page: terrain, Monte-Carlo probability, support, envelope, S1 / S2 masks, U-Net, labels, RF20, RF by date, reservoir; Surface-context page: Sentinel-2 true colour of every archive date, RF20, RF by date, the p95zm maps.

| group | n_layers | n_dates | first | last | MB | example |
|---|---|---|---|---|---|---|
| context | 5 | 1 | 2022-06-13 | 2022-06-13 | 1.2 | gauges |
| envelope | 2 | 0 |  |  | 0.1 | terrain_envelope |
| labels | 2 | 0 |  |  | 0.2 | labels_v003A |
| reservoir_model | 19 | 14 | 2023-05-31 | 2023-06-13 | 0.4 | reservoir_model_2023-05-31 |
| reservoir_s1 | 8 | 8 | 2023-06-01 | 2023-06-21 | 0.2 | reservoir_s1_2023-06-01 |
| reservoir_s2_class | 5 | 5 | 2023-05-06 | 2023-09-08 | 0.5 | reservoir_s2_class_2023-05-06 |
| reservoir_s2_index | 35 | 5 | 2023-05-06 | 2023-09-08 | 2.7 | reservoir_s2_NDVI_2023-05-06 |
| reservoir_s2_rf | 44 | 44 | 2017-07-01 | 2026-09-12 | 4.2 | reservoir_s2_rf_2017-07-01 |
| reservoir_s2_water | 9 | 9 | 2023-05-06 | 2023-09-08 | 0.3 | reservoir_s2_water_2023-05-06 |
| rf | 1 | 0 |  |  | 0.2 | rf_p73 |
| s1_daily | 11 | 11 | 2023-06-01 | 2023-06-30 | 0.4 | s1_new_2023-06-01 |
| s1_footprint | 11 | 11 | 2023-06-01 | 2023-06-30 | 0.1 | s1_footprint_2023-06-01 |
| s2_daily | 23 | 23 | 2023-06-05 | 2023-08-27 | 0.2 | s2_water_2023-06-05 |
| s2_footprint | 23 | 23 | 2023-06-05 | 2023-08-27 | 0.4 | s2_footprint_2023-06-05 |
| s2_rf | 52 | 52 | 2017-04-30 | 2026-09-10 | 7.9 | s2_rf_2017-04-30 |
| s2_truecolour | 212 | 212 | 2017-01-10 | 2026-09-12 | 40.0 | s2_truecolour_2017-01-10 |
| support_daily | 46 | 46 | 2023-05-26 | 2023-07-10 | 0.3 | support_daily_2023-05-26 |
| terrain_daily | 46 | 46 | 2023-05-26 | 2023-07-10 | 0.3 | terrain_daily_2023-05-26 |
| terrain_prob | 9 | 9 | 2023-06-06 | 2023-06-21 | 0.3 | terrain_prob_2023-06-06 |
| terrain_summary | 3 | 0 |  |  | 0.1 | terrain_duration |
| unet | 4 | 0 |  |  | 0.1 | unet_U2b_v003A |

## 5. Map figures

| where | file | about |
|---|---|---|
| publication/figures | Fig01_study_area.png |  |
| publication/figures | Fig02_evidence_hierarchy.png |  |
| publication/figures | Fig03_unet_experiment.png |  |
| publication/figures | Fig04_daily_inundation.png |  |
| publication/figures | Fig05_disagreement_ontology.png |  |
| publication/figures | Fig06_water_surface.png |  |
| publication/figures | Fig07_event_scale_reconstruction.png |  |
| publication/figures | Fig08_icesat2_consistency.png |  |
| publication/figures | Fig09_reservoir_balance.png |  |
| publication/figures | Fig10_reservoir_depth.png |  |
| publication/figures | Fig11_reservoir_drawdown.png |  |
| publication/figures | FigS01_training_curves.png | training loss and validation patch F1 per arm. **FigS02** structural sensitivity of the daily corridor new area (nominal runs, T12): |
| publication/figures | FigS02_rule_closure_sensitivity.png | structural sensitivity of the daily corridor new area (nominal runs, T12): |
| publication/figures | FigS03_per_date_series.png | per-date S1 and reliable S2 |
| publication/figures | FigS04_rf20_agreement.png | RF20 (rev 2: global blocks, frame overlap counted once) row-normalised confusion (spatial-block CV) and per-class F1 |
| publication/figures | FigS05_block_sensitivity.png | block-size sensitivity of U2 on v003_A and on v004 (7.5 / 10 / 15 / 20 km; each split has its own TEST geography). |
| publication/figures | FigS06_inhulets_profile.png | Inhulets valley: mapped U2b new flood on land (v004 labels, three training seeds) and the v004 EVENT_FLOOD label per 2-km northing band. **FigS07** Re |
| publication/figures | FigS07_hypsometry_sensitivity.png | Reservoir hypsometry |
| publication/figures | FigS08_reservoir_drawdown_maps.png | The modelled pool and the Sentinel-1 view of it (p95h). (a–c) Modelled pool water on 7, 9 and 13 June: the p95f sloped |
| publication/figures | FigS08_reservoir_model_and_s1.png | The modelled pool and the Sentinel-1 view of it (p95h). (a–c) Modelled pool water on 7, 9 and 13 June: the p95f sloped |
| publication/figures | FigS09_reservoir_s2_indices.png | The seven Sentinel-2 indices (NDVI, NDWI, MNDWI, NDMI, BSI, AWEIsh, NDTI) over the pool (+1 km) in display classes |
| publication/figures | FigS10_reservoir_design_hypsometry.png | Design hypsometry of the Kakhovka reservoir and the observed 2023 levels read on it (p95i, T27; no DEM, nothing fitted). |
| publication/figures | FigS11_terrain_error_variogram.png | The terrain-error model of the Monte-Carlo (p95j, T18b/T18c). (a) Semivariograms of the FABDEM − night ICESat-2 |
| publication/figures | FigS12_mc_convergence.png | Convergence of the Monte-Carlo quantiles with the ensemble size (T11c): p05, p50 and p95 of the newly inundated |
| publication/figures | FigS13_wse_threshold_sensitivity.png | Sensitivity of the connected reconstruction to a uniform offset δ of the water surface on the nominal terrain |
| publication/figures | FigS14_support_domain.png |  |
| publication/figures | FigS15_withheld_gauges.png |  |
| publication/figures | FigS16_seed_classes.png |  |
| publication/figures | FigS17_inundation_probability.png |  |
| publication/figures | FigS18_saddle_audit.png |  |
| publication/figures | FigS19_s1_new_water_by_date.png |  |
| figures/m6_v003A | p95z_delta_indices.png |  |
| figures/m6_v003A | p95z_floodway_indices.png |  |
| figures/m6_v003A | p95zm_delta_AWEIsh.png |  |
| figures/m6_v003A | p95zm_delta_BSI.png |  |
| figures/m6_v003A | p95zm_delta_MNDWI.png |  |
| figures/m6_v003A | p95zm_delta_NDMI.png |  |
| figures/m6_v003A | p95zm_delta_NDTI.png |  |
| figures/m6_v003A | p95zm_delta_NDVI.png |  |
| figures/m6_v003A | p95zm_delta_NDWI.png |  |
| figures/m6_v003A | p95zm_delta_index_classes.png |  |
| figures/m6_v003A | p95zm_delta_k10e.png |  |
| figures/m6_v003A | p95zm_delta_s1_vv.png |  |
| figures/m6_v003A | p95zm_floodway_AWEIsh.png |  |
| figures/m6_v003A | p95zm_floodway_BSI.png |  |
| figures/m6_v003A | p95zm_floodway_MNDWI.png |  |
| figures/m6_v003A | p95zm_floodway_NDMI.png |  |
| figures/m6_v003A | p95zm_floodway_NDTI.png |  |
| figures/m6_v003A | p95zm_floodway_NDVI.png |  |
| figures/m6_v003A | p95zm_floodway_NDWI.png |  |
| figures/m6_v003A | p95zm_floodway_index_classes.png |  |
| figures/m6_v003A | p95zm_floodway_k10e.png |  |
| figures/m6_v003A | p95zm_floodway_s1_vv.png |  |
| figures/p102 | ZONE_1_KAKHOVKA_LOWER_DNIPRO_rf_by_date.png |  |
| figures/p102 | ZONE_1_KAKHOVKA_LOWER_DNIPRO_rf_class_series.png |  |
| figures/p102 | ZONE_1_pool_rf_vs_k10e.png |  |
| figures/p102 | ZONE_1_pool_transition.png |  |
| figures/p102 | ZONE_2_KHERSON_DELTA_rf_by_date.png |  |
| figures/p102 | ZONE_2_KHERSON_DELTA_rf_class_series.png |  |
| figures/p102 | ZONE_3_DNIPRO_BUG_ESTUARY_rf_by_date.png |  |
| figures/p102 | ZONE_3_DNIPRO_BUG_ESTUARY_rf_class_series.png |  |
| figures/p102 | ZONE_4_DAM_TO_KHERSON_FLOODWAY_rf_by_date.png |  |
| figures/p102 | ZONE_4_DAM_TO_KHERSON_FLOODWAY_rf_class_series.png |  |
| figures/p102 | confusion_spectral.png |  |
| figures/p102 | confusion_spectral_doy.png |  |
| figures | p103_flood_envelope.png |  |

## 6. What does not exist (gaps)

- **Classified-index GeoTIFFs per date**: the display classes of the indices exist as dashboard PNGs (the pool, 5 dates) and as the p95zm period figures (delta, floodway); per-date classified rasters are only the k10e class (`k10e_by_date`). Any index file can be classed with `p95h.classify_index` (bins in `p95h.INDEX_BINS`) on request.
- **Sentinel-2 water masks of the 10 m frames** are not stored as rasters: the frozen rule (NDWI > 0 AND MNDWI > 0 on valid cells) is applied to `frame_indices` on the fly (p94, p98); the 20 m zone masks (`zone_water3`) are stored for every zone-date.
- **2023-07-31 and 2024-05-25** have no zone stack: their downloaded zips are orbit-edge slivers (78; 47 and 64 MB) below p25's frozen 200 MB scene filter.
- The **p25x extension** (49 zone-dates, 17 dates of 15 June – 30 July 2023, `tables/p25x_zone_stack_extension.csv`) is stacked for the hydraulic-model products; the Paper 3 tables built on the zone stacks (p95h: T23–T25) exclude them on purpose.
