# p74 — hydraulic surface state (design)

Status: **NOT A TASK OF THIS REPOSITORY** (maintainer, 2026-10-02, after the decisions below): the hydraulic surface state will
be built in a separate repository, together with the zone stacks. Nothing here is implemented or will be; this document is kept
only as the hand-off blueprint (decisions, inputs, rule draft, open points), like `provenance/PLAN_P25_MIGRATION.md`. Where it
says "here", read the new repository. floodstate-eo keeps p102 and p103 as products and reads p43 / zone stacks as external data.

## Decisions (maintainer, 2026-10-02)

- Classes on the drained bed: **(b) RF and k10e together + (c) canopy height**; not (a) — no blanket relabelling of the RF's
  "built-up" on the bed.
- **p102 is not changed.** The reclassification is a separate step, p74 "hydraulic surface state" (planned here, then moved out, see Status), built on top of **p43**
  (SWOT-DNIPRO's Manning roughness states) and **p102** (RF by date).
- No classified-index GeoTIFFs per date: the indices exist (`zone_spectral`), and p74 is the final product for the hydraulic model.
- Nothing is rebuilt: p25 stacks, p43 and p102 products are read as they are. The zone stacks belong to a separate repository.

## Inputs (read-only)

| source | what p74 uses | where | grid |
|---|---|---|---|
| p43 (SWOT-DNIPRO, external) | 15 roughness classes per state, n low / base / high, uncertainty; bed recession zoning; ATL08 canopy >= 2 m counts per 250 m cell | `SWOT-DNIPRO/outputs/rasters/roughness/{pool,below_dam_floodplain}/<grid>_*`; class → n and sources in `SWOT-DNIPRO/config/roughness_classes.yaml` | `zone1_poolwin` = window of the ZONE_1 zone grid (offset 3086 columns, 444 rows; same 20 m lattice); `zone2`, `zone4` = the zone grids |
| p102 (here) | RF land-cover class and top-class probability per date | `BULK/rf_by_date/<ZONE>/<date>_{rf,rfp}.tif` | zone grids (identical to p43's) |
| k10e (p25 stacks, external) | surface state per date | `BULK/zone_spectral/<ZONE>/<date>_class.tif` | zone grids |
| canopy (external) | ATL08 20 m canopy segments (leaf-on); GEDI L2A shots of the pool 2024, 2025 | `SWOT-DNIPRO/audit_runs/20260918T175108Z/pilots/icesat2/out/canopy_segments_20m.parquet`; `BULK/gedi/gedi02a_pool_{2024,2025}.parquet` | points → cells |

States: the six p43 states (BREACH_2023_bed, BREACH_2023, FIRST_EXPOSURE_2023, STATE_2024, STATE_2025, CURRENT_2026) with the
same windows as p40 / p43; p102 and k10e are aggregated per state window to the dominant class over the observed dates
(>= 2 observations, as in the p102 transition step).

## What the inputs say today (why the rule is needed)

- Pool, p43: young_woody_dense 461 km² (2024), 1 362 (2025), 1 481 (2026 state); reed_tall_herb 624 / 143 / 168 km².
- Pool, p102 dominant class of the growing season (WorldCover-water cells): forest 208 / 513 / 227 km², wetland-reed
  376 / 183 / 824, uncertain 498 / 798 / 575 (2024 / 2025 / 2026).
- k10e reads the cells the RF calls forest as reed / flooded vegetation (76–97 %), and those it calls built-up as dry bare sediment
  and sparse herbaceous (`tables/p102_rf_date_rf_vs_k10e_pool.csv`).
- Canopy height separates only tall woody cover: GEDI rh98 p50 (leaf-on 2024) is 3.21 m on reed_tall_herb, 3.32–3.35 m on young
  woody, 5.04 m on mature woody, and 2.68 m over open water (the instrument floor); ATL08 canopy-OK segments are rare on the bed
  (430 of 31 845 segments in 2025). Young willow and tall reed (2–4 m) overlap in height.

## Decision matrix per cell and state (draft)

| question | decided by | rule |
|---|---|---|
| water, intermittent water, wet sediment, bare sand / silt; bed zoning (p43 codes 1–4, 13–15) | p43 (k10e rules + hydroperiod) | kept; p102 never decides here (its WorldCover ontology has no sediment class) |
| built, cropland (11, 12) | p43 (Dynamic World / WorldCover) | kept outside the pool; never inside it (p43's rule) |
| vegetation density: sparse / dense herbaceous / reed (5–7) | k10e, as in p43 | kept |
| woody or not — (b) | p43 (DW woody label / probability, legacy woody) × p102 (forest or shrub dominant in the window) | both woody → p43's woody class; both not woody → p43's herbaceous / reed class; disagree → **AMBIGUOUS_WOODY_REED** |
| woody or not — (c), where canopy is measured | GEDI rh98 or ATL08 h_canopy, leaf-on, in the cell | >= 5 m → woody (overrides (b)); ATL08 h_canopy < 2 m → not woody (overrides (b)); 2–5 m → no decision |
| Manning n | class → n_low / n_base / n_high from `roughness_classes.yaml` | AMBIGUOUS_WOODY_REED: n_low 0.045 (reed), n_base 0.080, n_high 0.160 (young woody dense) — a bounding range, LITERATURE_PRIOR_ONLY |

## Outputs (planned)

Per domain and state: class raster (p43 codes 0–15 + 16 = AMBIGUOUS_WOODY_REED), n_low / n_base / n_high rasters, a decision-code
raster (p43 kept / (b) agree woody / (b) agree not woody / (c) canopy woody / (c) canopy not woody / ambiguous); tables of class
areas, the p43 × p102 agreement per state, decision shares and Δn against p43; one figure per domain; a dashboard layer later.
QA gates: grid alignment asserted; class areas close to the valid domain; nothing written over p43 or p102 products.

## Open points (to confirm before building)

1. **File name.** `p74` is taken in this repository (`workflows/m6/p74_m6_smoke_b2.py`, the M6 U-Net smoke test, tables
   `p74_smoke_*`). Proposed: `workflows/m6/p74h_hydraulic_surface_state.py`, outputs `p74h_*`.
2. **Canopy thresholds**: >= 5 m woody, < 2 m not woody, 2–5 m no decision.
3. **AMBIGUOUS_WOODY_REED** as its own class with the bounding n range above, rather than forcing p43's class.
