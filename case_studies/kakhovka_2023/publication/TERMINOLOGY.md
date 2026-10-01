# Frozen terminology (Paper 3) — gate 1 of the consolidation review, 2026-09-26

Every text of this bundle (manuscript, claims, captions, tables README, dashboard, notebooks) uses these terms and no
synonyms. `tests/test_terminology_freeze.py` forbids the phrases in the last section.

## The reconstruction

| term | meaning | never |
|---|---|---|
| **observation-constrained terrain-connectivity reconstruction** (short: *terrain reconstruction*; until 2026-09-29 *observation-constrained terrain inundation reconstruction*) | the observed water-surface elevations (SWOT nodes + gauge, Paper-1 frame) projected on the seamless terrain–bed elevation model (FABDEM DTM outside the surveyed channel, bed inside; EVRF2019) with a connectivity rule evaluated once over the whole domain; no momentum or continuity equations | *physical reconstruction*, *hydrodynamic reconstruction*, *simulation* |
| **daily reconstructed series** / *daily estimates constrained by the available observations* | the per-day values 26 May – 10 July; between observation days they are interpolation + model | *daily observed* |
| **reconstructed areal maximum** | the day of maximum reconstructed newly inundated area (7 June, between S1 acquisitions) | *flood peak* without a noun (peak *stage* at Kherson is 8 June and is a different quantity) |

## The hierarchy of evidence and the result blocks (text pass 2026-09-29)

| level / block | what it may claim | never |
|---|---|---|
| 1 **terrain-connectivity reconstruction** and 2 its **uncertainty** (the maintainer's "physical reconstruction" level; the phrase itself is forbidden below because it suggests a hydraulic model) | the reported areas, depths and volumes (Monte-Carlo median, p05–p95), with support classes and structural sensitivities | *simulation*, *hydrodynamic* |
| 3 **independent validation and support** (withheld gauges, Sentinel-1 per date, ICESat-2, SWOT–gauge input check; the surface context RF20 / WorldCover / elevation above the surface explains the disagreement) | agreement, disagreement and its mechanism | *validates the map*, *ground truth* |
| 4 **weak-label ML diagnostics** (U-Net arms on the canonical labels v004, three training seeds) | behaviour under weak supervision | *accuracy*, *better ground truth* |

A lower level explains or diagnoses a higher one; it never overrides it.

## Weak labels and seeds

| term | meaning | never |
|---|---|---|
| **v004** | the canonical weak-label ontology (LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN) on the corrected M2 (out-of-fold threshold, no post-event TRACE feature) | *better ground truth* |
| **v002**, **v003_A** | historical initial and intermediate label versions; provenance and sensitivity only | a production label set |
| **v002_notrace** | the v002 rule on the corrected M2 (no REFERENCE_WATER class): the reference of the label comparison | |
| **M2 score** | the discrimination score of the optical component of the labels | *flood probability* |
| **three training seeds** | the minimum evidence unit of an arm comparison (every seed shown, with the seeds whose interval excludes zero) | a single-seed arm claim |

## Areas (always with both semantics)

| symbol | term | definition |
|---|---|---|
| **W_total** | **reconstructed total water-surface area** | all cells allowed by the water surface on the day, incl. pre-breach channels, lakes and reed beds |
| **A_new** | **reconstructed newly inundated area** | W_total minus the same-rule pre-breach regime (26 May – 5 June) and the observed pre-breach water |
| **V_new** | **reconstructed new-water volume** | depth above ground integrated over A_new (planar surface, no ponding) |
| **A_new,dry** | **new inundation of dry ground** | A_new on ground that was dry before the event (p95x ground class: no optical pre-breach water, outside the normal regime, neither WorldCover herbaceous wetland nor water); the strict new flooding (T12h) |
| **A_wet**, **ΔA_wet** | **wetland inside the event extent** and its **event increase** | A_wet(t) = W_total on the seasonally wet vegetated wetland (WorldCover herbaceous wetland, incl. reed beds above the normal surface, plus the model-only normally wet) — the event extent over the wetland; ΔA_wet(t) = A_wet(t) − A_wet(5 June) within each world (T12h) — a difference from the reconstructed pre-breach state that inherits its uncertainty. Model quantities: water under the reed canopy is not observed. Never added to A_new,dry as one "flooded area"; never called new flooding |
| agreement passport | every CSI / POD / FAR | goes only with: the reference product (id, date, semantics), the ground class or domain, the coverage (share decided or observed), the share of the reference water in UNKNOWN where a state mask is compared, the chance level (CSI of the same two areas placed independently, or Heidke skill) or the admissible interval over the undecided cells (T13 passport columns, T16b, T16c; `tests/test_agreement_metrics.py`). A CSI without these is not a result |
| pre-event ground classes | dry before the event / seasonally wet vegetated wetland / open reference water (p95x `ground_class`) | the wetland class rests on land cover and the normal regime; its seasonal Sentinel-1/2 evidence (T12j) is stratum-level, never a per-cell map of water on 5 June. Report the event extent and the pre-event state apart: *flood-extent agreement* (T16b/T16c, diagnostic) vs *baseline-state uncertainty* |
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
| **primary interval** | p05–p95 of the coherent Monte-Carlo worlds of p95e rev 2 (n in T12): per draw one terrain-error field over the whole domain (FABDEM cells, class NMAD × a unit field with the covariance fitted to the FABDEM − ICESat-2 residuals) and one water-surface realization (datum, gauge, SWOT, gap-dependent interpolation; every term once), the pre-breach regime rebuilt with it; W_total, A_new and volumes each from their own ensemble |
| **emulator (diagnostic)** | the 100 000-draw cluster-normal emulator (p95g): no connectivity, total built around the nominal total; a computational diagnostic outside the evidence path (T12d; D-EMU 2026-09-29) — never an uncertainty estimate, never quoted as a result |
| **full terrain-connectivity reconstruction** | the primary product: every cell the observed water surface reaches through the terrain with connectivity, whatever the distance of its SWOT support |
| **support classes** | distance of the nearest SWOT node of a newly inundated cell: *direct* ≤ 3 km, *extrapolated* 3–10 km, *weak* > 10 km (operational thresholds, not physical constants); flags: capped at the Kherson gauge, cross-river (Inhulets); **supported core** = direct + extrapolated (T11k) |
| volumes | always with their p05–p95 and MC median; the volume interval is not centred on the deterministic run |

## Reservoir balance (context, claim C14)

| term | never |
|---|---|
| **daily-mean effective release** = −dV_pool/dt + Q_in(DniproHES) | *breach discharge*, *peak breach outflow*, *instantaneous peak* |
| **most of the released volume was transmitted downstream rather than stored on the mapped floodplain** | *the rest went/passed to the liman* |
| **hypsometry gap** DEM vs design table (a result; FigS07, T22) | *a correction* |
| **Paper 4**: the reservoir bowl reconstructed on the historical bathymetry (next step, separate paper) | |

## Forbidden phrases (enforced by the test)

`physical reconstruction`, `better ground truth`, `false SAR water`, `false radar water`, `peak breach discharge`, `breach discharge was`, `breach discharge of`, `peak breach outflow`, `implied breach
outflow`, `passed to the liman`, `went to the liman`, `without loss of recall`, `without a detectable loss`, `without a
detectable recall loss`, `daily observed`, `flooded area = `.
