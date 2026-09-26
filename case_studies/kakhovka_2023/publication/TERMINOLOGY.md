# Frozen terminology (Paper 3) — gate 1 of the consolidation review, 2026-09-26

Every text of this bundle (manuscript, claims, captions, tables README, dashboard, notebooks) uses these terms and no
synonyms. `tests/test_terminology_freeze.py` forbids the phrases in the last section.

## The reconstruction

| term | meaning | never |
|---|---|---|
| **observation-constrained terrain inundation reconstruction** (short: *terrain reconstruction*) | the observed water-surface elevations (SWOT nodes + gauge, Paper-1 frame) projected on the seamless DEM with a connectivity rule; no momentum or continuity equations | *physical reconstruction*, *hydrodynamic reconstruction*, *simulation* |
| **daily reconstructed series** / *daily estimates constrained by the available observations* | the per-day values 26 May – 10 July; between observation days they are interpolation + model | *daily observed* |
| **reconstructed areal maximum** | the day of maximum reconstructed newly inundated area (7 June, between S1 acquisitions) | *flood peak* without a noun (peak *stage* at Kherson is 8 June and is a different quantity) |

## Areas (always with both semantics)

| symbol | term | definition |
|---|---|---|
| **W_total** | **reconstructed total water-surface area** | all cells allowed by the water surface on the day, incl. pre-breach channels, lakes and reed beds |
| **A_new** | **reconstructed newly inundated area** | W_total minus the same-rule pre-breach regime (26 May – 5 June) and the observed pre-breach water |
| **V_new** | **reconstructed new-water volume** | depth above ground integrated over A_new (planar surface, no ponding) |
| observed_S1 | Sentinel-1 dark water on that date (total, or minus the 1–2 June water: *new dark water*) | |
| mapped_UNet | U-Net score above the frozen validation threshold (a persistence concept) | |
| literature_reported | an operational/published figure with its own AOI, date, reference water and temporal semantics | |

Temporal semantics accompany every area: `daily_snapshot_<date>`, `cumulative_<from>..<to>`, `persistence_<rule>`,
`reference_<dates>`. Operational *flooded land* (UNOSAT 3616: ~620 km² cumulative 6–9 June, reference water separate) is
closer in kind to A_new than to W_total and is context, never validation. Never write "flooded area = 779 km²".

## Agreement statistics

| term | definition |
|---|---|
| **raw agreement** POD / FAR / CSI | on the S1 observation domain of the date; primary |
| **conditional POD outside the normally-wet class** (`POD_cond_outside_normally_wet`) | hit / (hit + miss − miss_on_normally_wet); a *diagnostic conditional agreement*, never a "corrected" POD; the class was fixed a priori |
| **agreement with weak reference labels** | every U-Net number; never *accuracy* |
| **agreement with the training reference** | every RF20 number against WorldCover; never *validation* |
| **no statistically resolved change** | a paired-bootstrap interval that crosses zero; never *unchanged*, *without loss* |

## Disagreement categories

| term | never |
|---|---|
| **S1-only detections topographically unsupported by the reconstructed connected water surface** (ground ≥ 5 m above it) | *false SAR water*, *false radar water* |
| **submergence of normally-wet reed beds** (S1 onset where the ground is below the normal surface: a depth signal) | *new inundation* |
| **SAR blind spots** (terrain-only under trees, reeds, buildings) | *terrain errors* |
| ICESat-2 **altimetric consistency check** along tracks: *supports*; provides *no evidence for a DEM bias large enough to explain* the discrepancy | *proves*, *validates the map* |

## Uncertainty

| term | definition |
|---|---|
| **primary interval** | p05–p95 of the 40 full spatial Monte-Carlo draws (p95e): correlated DEM error field, closure, gauge, SWOT, interpolation |
| **emulator sensitivity envelope** | p05–p95 (p25–p75) of the 100 000-draw cluster-normal emulator (p95g), area only: a broader parameter space; never the primary interval |
| volumes | always with their p05–p95 and MC median; the volume interval is not centred on the deterministic run |

## Reservoir balance (context, claim C14)

| term | never |
|---|---|
| **daily-mean effective release** = −dV_pool/dt + Q_in(DniproHES) | *breach discharge*, *peak breach outflow*, *instantaneous peak* |
| **most of the released volume was transmitted downstream rather than stored on the mapped floodplain** | *the rest went/passed to the liman* |
| **hypsometry gap** DEM vs design table (a result; FigS07, T22) | *a correction* |
| **Paper 4**: the reservoir bowl reconstructed on the historical bathymetry (next step, separate paper) | |

## Forbidden phrases (enforced by the test)

`physical reconstruction`, `false SAR water`, `false radar water`, `peak breach discharge`, `breach discharge was`, `breach discharge of`, `peak breach outflow`, `implied breach
outflow`, `passed to the liman`, `went to the liman`, `without loss of recall`, `without a detectable loss`, `without a
detectable recall loss`, `daily observed`, `flooded area = `.
