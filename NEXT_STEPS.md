# Where floodstate-eo stands, and what's next

Written 2026-09-23, at the end of the session that created this repository's first real commit. This is
the "what stage are we at, what do we do when we come back" record — read this before doing anything else
in this repo.

## UPDATE 2026-10-02 — zone stacks extended (option A), the RF matrices, the product inventory, the p25 migration plan

- **Option A done**: SWOT-DNIPRO's frozen p25, unchanged, run on the event store through `workflows/m6/p25x_zone_stack_extension.py`
  (driver: adds `sentinel_event_2023` to the SAFE stores, skips the frozen regime composites). 49 new zone-dates (ZONE_1 6, ZONE_2 13,
  ZONE_3 17, ZONE_4 13) = 17 of the 19 unstacked dates; 2023-07-31 (78 MB) and 2024-05-25 (47 / 64 MB) are orbit-edge slivers below
  p25's 200 MB filter and stay unstacked. The sibling's p25 manifests (and their hard-linked `deliverables` copies) were restored to
  their committed content; the record is `tables/p25x_zone_stack_extension.csv`. **p95h pins its date set** (`EXTENSION_DATES`): T23–T25
  do not change. p102 predicted the new zone-dates; tables, figures and dashboard layers rebuilt.
- **RF wording** (maintainer, after a literature check): 0.764 (spatial-block CV) → 0.698 (2023 hold-out, pre-breach dates) is a
  temporal-transfer degradation relative to the WorldCover-2021-derived weak reference, not a validated 2023 accuracy; no agreement is
  reported after the breach or for 2024–2026. The forwarded sources (ESA WorldCover v200 validation 76.7 %, Xu et al. 2024 RSE,
  a cross-year Sentinel-2 transfer study with 2.3–14.9 pp, Tavus et al. 2026) are **not verified yet** -- check them against the
  primary text before any citation (rule of 2026-10-01).
- **The matrices** (maintainer: "the matrix must be in the plan"): `p102 --step evaluate` -- confusion matrices and per-class
  precision / recall / F1 of both evaluations, both variants, all zones and per zone (`tables/p102_rf_date_{metrics,confusion_long}.csv`,
  `figures/p102/confusion_*.png`); `p102 --step transition` -- WorldCover 2021 class × dominant RF class of each growing season
  (2021, 2022, 2023 after the breach, 2024, 2025, 2026) inside the pre-breach pool, and outside it as the control of the classifier's
  year-to-year noise (`tables/p102_rf_date_transition.csv`, `figures/p102/ZONE_1_pool_transition.png`). The transformation of the
  drained bed shows in the transition matrices, not in the confusion matrices (WorldCover 2021 describes the pre-breach state).
- **What the matrices show.** Confusion (production variant, F1 spatial CV / 2023 hold-out): water 0.98 / 0.94, bare 0.87 / 0.85,
  forest 0.74 / 0.67, wetland 0.70 / 0.63, grass 0.69 / 0.61, built 0.69 / 0.66, cropland 0.69 / 0.55 (30 % of WorldCover cropland
  goes to grass in the hold-out); hold-out macro F1 by zone 0.678 (pool zone), 0.728 (delta), 0.688 (estuary); the evaluation step
  reproduced the training-step metrics exactly. Transition, pre-breach pool (WorldCover water 2,106 km²): water 2,088 km² in the
  2021 and 2022 seasons → 2023 after the breach water 305, bare 626, "built-up" 668, wetland 118, uncertain 328 → 2026 wetland 824,
  forest 227, "built-up" 166, water 169, uncertain 575. **Ontology gap**: the RF's "built-up" on the bed is, by the k10e state of the
  same dates, dry bare sediment (34 %) and sparse herbaceous (25 %) -- WorldCover has no exposed-sediment class; the RF's "forest" on
  the bed is k10e reed / flooded vegetation (76–97 %) -- the spectra do not separate willow thickets from reed. Before the hydraulic
  model uses the pool classes (decisions for the maintainer): (a) BUILT_UP → EXPOSED_SEDIMENT inside the pre-breach pool (no buildings
  exist there), (b) roughness classes from RF and k10e together, (c) canopy height from ICESat-2 ATL08 / GEDI to separate forest from
  reed (`BULK/gedi` exists). `tables/p102_rf_date_rf_vs_k10e_pool.csv`, `figures/p102/ZONE_1_pool_rf_vs_k10e.png`.
- **Product inventory** (`workflows/paper/p104_product_inventory.py` → `case_studies/kakhovka_2023/PRODUCT_INVENTORY.md`,
  `tables/p104_product_inventory.csv`): every index map, classified map, water mask, flood / state map, dashboard layer group and map
  figure, with paths, producers, grids and dates per year; generated from the files on disk.
- **Bed classes and p74** (maintainer, 2026-10-02): option (b) RF + k10e together and (c) canopy height, not (a); p102 unchanged;
  the reclassification is a separate step here, p74 "hydraulic surface state", on top of p43 (SWOT-DNIPRO roughness states) and
  p102; no classified-index GeoTIFFs per date; nothing rebuilt. **Then moved out (maintainer, 2026-10-02, later): the hydraulic
  surface state is not a task of this repository -- it will be built in a separate repository; nothing is built here.**
  `docs/P74_HYDRAULIC_SURFACE_STATE.md` stays as the hand-off blueprint (open points: file name, canopy thresholds, the
  ambiguous woody / reed class).
- **p25 stays out of floodstate-eo** (maintainer, 2026-10-02): a separate repository will host the zone spectral stacks; nothing
  is copied here. `provenance/PLAN_P25_MIGRATION.md` is kept as the blueprint for that repository; floodstate-eo reads
  `BULK/zone_spectral` as an external product (SWOT-DNIPRO p25 now, the new repository later).
- Still open: push to origin; FABDEM licence on data.bris, He 2024, Zheng / Monti pages.

## UPDATE 2026-10-01 (evening) — products for the hydraulic model, the dashboard session, the article without working names

Maintainer requests of the day and what was done:
- **The article text carries results, not working names** (commit 7733488): script ids, label-set versions (v002 / v003_A / v004 →
  "the canonical labels", "the no-reference-water labels", "the intermediate set"), D-/C-tags, split names and seed values removed
  from the abstract on, in both languages; the Methods give every formula used as 17 numbered equations (water surface, connectivity
  rule, normal regime, areas / volumes, terrain bias, ground-class split, Monte-Carlo perturbations, effective release, gauge errors,
  agreement scores with chance and UNKNOWN bounds, indices, U-Net loss). `tests/test_manuscript_production_text.py` pins both.
  Assembled proofreading DOCX (uk, en) rebuilt with p101.
- **Dashboard session** (`apps/dashboard/lib.py`: `session`, `persist`, `opt`): every page carries `?sid=` in the URL; widget choices
  are restored from a server-side store (memory + `.sessions/<sid>.json`, git-ignored) before the widgets are built and saved after
  them, so a page switch, a reload and a server restart come back to the same choices. `tests/test_dashboard_session.py`.
- **The full flood mask (p103)**: the envelope of the primary reconstruction (pre-breach water / normally wet / nominal new / MC
  median world only / marginal) + max P + the Sentinel-1 envelope of the event dates, per zone and as a mosaic with GeoJSON polygons
  in `floodplain_dyn/_envelope/` (bulk); `tables/p103_flood_envelope.csv`; dashboard layers (Maps page). Corridor: total water
  envelope 867 km², new inundation 264 (nominal) / 267 (median world) km².
- **RF surface classes by date (p102)**: a random forest on the seven indices of each Sentinel-2 date, WorldCover 2021 as the weak
  target, for every date of the four p25 zones 2017–2026 (the pool included; 2024–2026 = the drained bed). Training / evaluation run;
  the wall-to-wall prediction of all zone-dates runs for hours (resumable; `--group rf_by_date`). Tables, figures and dashboard layers
  (best-observed date per month) follow the prediction. **Gap**: 19 downloaded SAFE dates (18 of 15 Jun – 31 Jul 2023, 2024-05-25)
  have no p25 zone stack → no class map; running the frozen SWOT-DNIPRO p25 on them is the maintainer's call.
- Not done / open: push to origin (local main ahead); FABDEM licence on data.bris, He 2024 full text, Zheng / Monti pages.

## UPDATE 2026-09-30 — D-SEED: the event source of the connectivity is the river network; everything regenerated

The QA of the weak-support blobs (`workflows/m6/p95o_component_qa.py`) found that seeding the connectivity from EVERY
pre-breach water cell let isolated ponds "flood" ~40 km² of terrace cropland under the Kokan' level 14 km away (corridor 7 June:
245 = 199 river-connected + 47 isolated-never km²). Maintainer decisions: **D-SEED_PRIMARY** = seed from the largest connected
component of the pre-breach water map (p95 rev 8; the old rule = provenance variant `_seed_allprewater`); **D-MEMORY** = retained
water is the `_memory` sensitivity only. A 30 m label gap at the zone boundary that split the network at Kherson is fixed
(frames composed where they have labels). Level 2 (p95, variants, p95e 1000 worlds, p95o QA) and level 1 regenerated; T28 rows
A47–A49; new tables T11m–T11p, FigS16; Sentinel-2 true colour of 13 June 2022 (own archive, `paper/p97b_s2_basemap.py`) is the
basemap of Fig07 / FigS14 / FigS16 and an overlay of the dashboard (basemaps Gray / OpenStreetMap / EOX S2 cloudless 2022 / Esri
World Imagery, live tiles with attribution). Headline numbers before this update are history (T28).
Same day, two more products: **P(new inundation) per cell** over the same 1000 worlds (`p95e --mode cellprob`; T12g, FigS17,
dashboard layer `terrain_prob_<date>`; the median world P >= 0.5 is the map product of the ensemble -- D-CELLPROB: the ensemble, not a
hand cut, decides marginal components) and a **saddle audit** of the floodplain lowland south of Krynky, 10 km east of Kozachi Laheri (`p95p_saddle_audit.py`, three
steps, the ICESat-2 step in the SWOT-DNIPRO venv; T15d-T15f, FigS18; Copernicus GLO-30 tiles under `$BULK/copdem/`): the sill at
8.85 m is confirmed by ICESat-2 night ground (r +0.13 m, NMAD 0.37, n 35 at the terrace edge); head +0.68 m on 7 June, +0.13 m on
8 June; the lowland stays in the median world on 7 June (P 0.83) and is marginal on 8 June (P 0.55). First rev-8 numbers: corridor
A_new 7 June 219 [203-235] km2, 8 June 223 [179-246]; the areal maximum falls on 8 June in 58 % of the worlds (7 June 30 %).
A **post-event wetness test** of the same lowland (`m6/p95q_moisture_trace.py`, diagnostic, not in the manuscript): Sentinel-2 NDMI / NDVI /
SWIR contrast (B11-B12)/(B11+B12) per pixel against the matched 2022 dates, Sentinel-1 gamma0 same-orbit pairs, against an unflooded terrace
control and two references (multi-day flood seen dark by S1 on 9 June; brief flood drained by then). No optical trace in the lowland
(first clear view 15 June); the multi-day reference shows a strong vegetation-damage trace -> the optics exclude a multi-day flood.
Sentinel-1 on 9 June (first look after the peak): the flooded cells are brighter than never-flooded cells of the same cover inside the
same box (+1.9 dB on bare, pre-breach fire-scar ground; +0.4-0.5 dB on forest and grass), fading by 21 June -> a transient wet-soil
signal that supports the brief 7-8 June inundation (one image, no same-orbit pre-breach scene, no rain data). Level-1 tail after the
rev-8 chain: p96 --check OK, 0 unresolved placeholders, notebooks executed, pytest 124 passed.
Local checks of 7 June (diagnostics, not in the manuscript): `m6/p95r_local_daily_maps.py` (daily maps and areas of Kozachi Laheri, Krynky
and the lowland; OSM state of 5 June 2023) and `m6/p95s_unosat_crosscheck.py` (UNOSAT 3614 / ICEYE 7 June 12:18-13:01 UTC; convert step in
the SWOT-DNIPRO venv): corridor new-water CSI 0.53 (total water 0.73), wetland POD 0.49 is the main miss; at Michurina street the ICEYE edge
(134 m) and the reconstruction (134 m) agree; the lowland south of Krynky shows little open water at ICEYE midday but Landsat-9 water inside
the reconstructed footprint on 9 June -> timing / retained water.
EO recession test (`m6/p95t_eo_recession.py`; UNOSAT 7/9/13/21 June vs the frozen primary, memory and ensemble; nothing fitted): corridor
model too slow 9->13 June and without the open-ground tail of 21 June; wetland plateau vs an observed peak; Krynky shape matches; the lowland
south of Krynky fills later and drains with tau ~2 d, which neither variant reproduces -> a storage-drainage formulation is the next model
step (calibrate on own S1/S2 series, keep UNOSAT as the test), then p95u (wetland misses).
DEPRESSION_STORAGE v1 (`m6/p95v_depression_storage.py`, diagnostic, one depression, prior-predictive): mass balance through the p95p sill and
the 11-km terrace (Manning, DEM cross-sections) vs a short weir; UNOSAT stays the hold-out. The weir (fast fill, like the primary) is rejected
on every date; the friction path reproduces the empty ICEYE midday and the 13 June residual but gives too little water on 9 June and drains
too slowly by 21 June: v1 does NOT pass the quantitative hold-out (2 of 2000 prior samples pass all dates). It rejects the instantaneous
high-conveyance connection and narrows the admissible mechanisms (finite conveyance + transient storage); the single reservoir is
inadequate. Next: distributed storage cells with inter-cell fluxes (the rim opens only in the NW corner: 40 m at 8.9 m, 5.8 km at 9.5 m),
losses from soil / drainage -- before any calibration.
DEPRESSION_STORAGE v2 (`m6/p95w_storage_cells.py`; subgrid storage cells, local inertial face fluxes, 100 prior runs at 200 m and 100 m on the
GPU): 0/100 pass the hold-out at both resolutions. The 9 June area is reproduced (100 m: 98/100 runs within x2), but water enters too early
(7 June) and the closed depression does not drain (13 / 21 June), whatever the losses up to 100 mm/d; observed water reached farther from the
entry than modelled. Not converged (100 m areas 0.57-0.74 x 200 m). STOPPED here (maintainer 2026-09-30): no 50 m run, no v3. p95p-p95w
are kept as diagnostic / limitation tests that empirically define the domain of validity of the weak-reference reconstruction (the hold-out
rejects instant filling AND a closed depression without an outlet); the flow physics goes to HEC-RAS separately.
p95 rev 9 (maintainer 2026-09-30): the pre-breach baseline is the optically observed pre-breach water (p60 Sentinel-2 frequency >= 20 %)
plus the same-rule normal wetness. Sentinel-1 darkness of 1-2 June (403 km2 of the domain, mostly dry cropland / grass in later EO) is no
longer reference water; it only masks the S1 "new water" of the checks (p94 S1, p95, p95c, p95d, p95o). S2 new water (p94, dashboard) uses
the optical reference. Level 2 regenerated (all steps exit 0; `p95e_cellprob_daily` now `--workers 4`: 16 dates x 2 counters filled 23 GB
with 8) and level 1 (CHECK OK, 0 unresolved, pytest 124). Corridor 7 June: A_new nominal 199.9 -> 214.8 km2, MC median 219.2 [202.5-235.0]
-> 233.7 [216.0-253.7], W_total unchanged 716.2, V_new 576 -> 603 hm3 (T28 row A51). Of the 29 km2 S1-only cells under the 7 June surface,
15 became new and 14 normally wet; S2 in July-August sees water on ~2.6 % of the 15 km2, so the gain is event water, not ponds. p95q holds
(burnt +1.89 / +0.89 dB, forest +0.43 / -0.10, grass +0.62 / -0.07 on 9 / 21 June); p95w still 0/100 at 200 m and 100 m.
p95e cellprob also writes P(water) (`p95e_cellprob_water[_daily]_<date>.tif`).
State mask between the EO dates (`m6/p95x_weak_label_quality.py`, rewritten on the maintainer's review: best state + metadata, never
uncertainty -> UNKNOWN): per day state DRY / WATER / UNKNOWN, source EO_S1 / EO_S2 / MODEL_STRONG / MODEL_WEAK / REFERENCE, flags
STORAGE_SENSITIVE / WEAK_CONNECTIVITY / SENSOR_BLIND / REFERENCE_UNCERTAIN / RECESSION_UNCERTAIN, reference band. Same-day EO -> its state;
else P(water) >= 0.8 WATER, <= 0.05 DRY, otherwise UNKNOWN; between an EO WATER and the next EO DRY the model's dryness is not accepted.
Dark S1 is water only where P(water) > 0.05 that day or on reference water (the lowland south of Krynky showed 10 km2 of S1 "water" on
21 June that S2 on 18/20/23 June and UNOSAT's own S1 did not). UNKNOWN 91-316 km2 per day (500-650 in the first version). 7 June vs ICEYE
(no own EO, every state a model state): 91 % decided, accuracy 0.967, POD 0.94, FAR 0.08, CSI 0.87; MODEL_STRONG 1543 km2 accuracy 0.98 /
CSI 0.91; MODEL_WEAK 54 km2 accuracy 0.65; storage-sensitive cells accuracy 0.56 (the lowland fills too early, as p95p-p95w showed).
Late-June UNKNOWN is mostly model-only normally-wet reeds near the normal level (30 June: 223 of 309 km2 on that reference ground).
A falling WATER curve is not drying (maintainer 2026-10-01): of the 291 km2 that were WATER on non-reference ground, on 30 June 6 km2
are still WATER, 96 km2 DRY confirmed by EO since their last WATER (grass, crop), 126 km2 DRY by the model only (trees 41, reeds 35,
built-up 23: EO cannot confirm dryness there) and 64 km2 UNKNOWN (reeds 49) -- p95x_transitions.csv. On the EO-decided cells of the
same ground, EO and model water agree in area (9 June 107 vs 99 km2, 74 in both; p95x_eo_vs_model.csv).
Audit of the external comparisons (`m6/p95y_disagreement_audit.py`, reviewer 2026-10-01; diagnostic comparison with external products,
not an untouched independent test -- UNOSAT informed the baseline fix and the S1 screen): 7 June vs ICEYE on event ground (no
normally-wet reeds): CSI 0.72 on decided cells; all UNKNOWN as DRY 0.49, as WATER 0.67; TRUE bounds over every UNKNOWN assignment
0.41-0.81. 35 % of the ICEYE water lies in UNKNOWN, and UNKNOWN covers 34 % of the ICEYE water-edge cells against 7 % elsewhere. The
0.87 first reported included 277 km2 of normally-wet reeds (CSI 0.97 alone). Cumulative 6-9 June vs UNOSAT's composite (ICEYE 7 June +
S3 6-9 June + S2 8 June = the ~620 km2 of product 3616; read from the activation package FL20230606UKR served from the 3614 folder --
not "3614 cumulative"): CSI 0.77 (both 460, ours only 52, UNOSAT only 85 km2). UNOSAT flood lies 272 km2 on normally-wet ground and
273 km2 on event ground (ours 250): the area gap to our new water is mostly that reference, but 73 km2 of UNOSAT-only flood is on event
ground (49 of it our UNKNOWN), so "all of the gap is the reference" is NOT shown. S1 9 June misses outside the normally-wet ground
(67 km2 in the domain): 27 km2 Landsat-9 also water (reeds 0.2-0.4 m above the modelled surface: edge water the model misses), 39 km2
grass / cropland 5-20 m above the surface without L9 water (S1 dark on dry ground). p95w 0/100 = rejection under its criterion (area
within x2 on 7, 9, 13 and 21 June), not a passed check.
Pre-event state of the reed marsh (`p95y` part 4, `m6/p95z_delta_indices.py`): open water seen before the breach on 2-7 % of the
model-only normally-wet ground only (S2 frequency, UNOSAT S2 3-5 June, S1 dark). Optics never see water under the reeds (June 2022 and
March 2023 MNDWI / NDWI / AWEIsh like dry-footed reeds; denser, wetter canopy: NDMI +0.31 vs +0.12) -- water shows optically only on
8 June when the canopy was submerged. C-band does: spring 2023 (17 scenes) VV -7.9 dB in the normally-wet reeds and -8.1 in the
event-only reeds vs -11.1 in dry-footed reeds (VV-VH +7.4 / +6.9 vs +5.5): the double-bounce signature of vegetation standing in
water (or saturated, denser stands), dark when submerged on 9 June, brighter than spring on 14 June as the water dropped beneath the
canopy. The radar does not see the DEM line between "normally wet" (baseline) and "event" reeds: both look alike before the breach.
Two physically different quantities (maintainer 2026-10-01; reviewer's reading of p95z): p95x writes `ground_class.tif` (dry before the
event / vegetated wetland = WorldCover herbaceous wetland or model-only normally wet / optical open water / other water) and the metadata
flag VEGETATED_WETLAND; the daily mask stays WATER / DRY / UNKNOWN. `m6/p95e_split_areas.py` replays the same 1000 worlds (gate: sum =
T12 A_new to 0.01 km2) -> T12h. Corridor 7 June: A_new on dry-before-event ground 145.9 [132.5-166.1] km2 (nominal 160.0); wetland
complex under water 317.8 km2, 205.0 already on 5 June, event increase 113.7 [93.0-134.6]; with the Inhulets 181.4 [167.8-202.0] dry
and 121.5 [100.3-144.2] wetland increase; 8 June 147.8 / 114.9 (corridor). 7 June vs ICEYE on dry ground: coverage 94.6 %, CSI 0.64 on
decided cells, UNKNOWN->DRY 0.51, ->WATER 0.54, admissible interval 0.38-0.72; wetland CSI 0.96 (coverage 76.5 %). Cumulative 6-9 June,
corridor + Inhulets, like for like: dry ground UNOSAT 171.5 vs ours 164.7 km2, both 119.8, CSI 0.55; vegetated wetland UNOSAT 370.8 vs
ours 344.1, both 337.5, CSI 0.89 -- two thirds of UNOSAT's flood in our region is the wetland complex.
Manuscript (2026-10-01, maintainer's literature check and wetland framing): §3.3 defines three pre-event ground classes (dry before the
event / seasonally wet vegetated wetland / open reference water), A_new,dry, A_wet(t) (wetland inside the event extent) and dA_wet (a
difference from the reconstructed 5 June state) with Martinis 2022, Lefebvre 2019, Slagter 2020, Oakes 2023. §4.1.1 reads the event
extent and the pre-event state apart: A_wet 7 June 318 [304-334] km2 (robust), 5 June wetland water 205 [179-228] vs nominal 231 ->
dA_wet 114 [93-135] is baseline-dependent. UNOSAT diagnostic per ground class (T16b, T16c): wetland CSI 0.89 but 0.79 by chance at the
same coverage, Heidke 0.52 (92 % / 85 % of the wetland flooded in UNOSAT / ours) -> the wetland is inside the event extent without
contradiction (UNOSAT-only 33 km2: 31 in our UNKNOWN, 0 EO-DRY, 2 model-DRY); the boundary is tested on dry ground (CSI 0.55, chance
0.02, Heidke 0.70). Seasonal evidence p95z now covers the delta AND the floodway dam->Kherson (T12j compact, T12i windows): spring 2023
S1 VV of normally-wet reeds -8.1 (delta) / -4.1 dB (floodway, VV-VH 10.6) vs -11.2 / -9.8 above the reach; event-only reeds -8.2 in
both (delta = same as normally wet, floodway = in between); floodway S2 May - 5 June 2023: normally-wet reeds MNDWI -0.29 vs -0.46/-0.48
(water shows through, not open water); 18 June NDVI 0.32 / 0.18 vs 0.78 / 0.76 normal. p95zm: cloud-free maps of the classified indices (p95h display
bins) per zone -- single optical dates are useless here (the delta has no scene 5 March - 5 June 2023; 8 June clear 26 % delta / 18 %
floodway), so each period is the per-cell median of the clear observations (normal year May-June 2022; last before the breach; recession
16-30 June; July), the peak is mapped with Sentinel-1 orbit 14 (spring median / 9 June / 21 June) and k10e on the best-covered dates. UNKNOWN of the label ontology cites Bauer-Marschallinger 2022 / Roth 2025; T28 A52; TERMINOLOGY.
The abstract, the conclusions and the claims still carry the old A_new as the headline -- switching them is the maintainer's decision.
Process fix 2026-10-01 (maintainer: 'why does this go in circles, why never the full picture'): the record showed eight rework cycles
caused by (1) no written specification of the full answer, (2) no check of what each sensor observed before drawing a diagnostic,
(3) agreement numbers without their passport. Now: `p95u_evidence_inventory` (T01b: zone x stratum x period x sensor -- scenes,
clear share, best scene; the gate of p95zm, which refuses a period composite below 50 % clear without --allow-partial);
`p96b_wetland_evidence` -> `publication/WETLAND_EVIDENCE.md` (the full picture generated from the tables: availability matrix,
quantities, pre-event evidence, UNOSAT diagnostic with chance level, maps, open decisions); the agreement passport (TERMINOLOGY;
T13 gains footprint / coverage / CSI_chance / heidke_skill from the p94 footprint, T16b a coverage note; `tests/test_agreement_metrics.py`);
`rebuild.py --group wetland_evidence` runs the chain p95x -> p95e_split -> p95z -> p95zm -> p95y -> p95u -> p96 -> fill -> p96b -> pytest;
FigS19 = the Sentinel-1 new dark water by date as a paper figure (the p94 maps were a diagnostic only). Rule: write the matrix,
check the inventory, deliver every cell or name the gaps, numbers with passports.
Dashboard (maintainer 2026-10-01, Surface-context page): `p97c_s2_truecolour_dates` renders the Sentinel-2 true colour of every archive
date over the lower Dnipro (224 dates 2017-2026, tiles TUS/TUT/TVS/TVT/TWS/TWT) on the dashboard box, clouds as photographed, clear
share from SCL in the label, < 2 % clear not rendered (`apps/dashboard/data/s2rgb/`, side manifest registered by `p98 --only context`
as group s2_truecolour); the page gets a year / date browser with RF20, S2 water and nearest-S1 overlays, and a 'Satellite maps'
section showing the p95zm composites, the S1 orbit-14 series, k10e and FigS19. Bundle limit 100 MB (test_dashboard_bundle).
Theme (maintainer 2026-10-01): `.streamlit/config.toml` now carries `[theme.light]` and `[theme.dark]` (Streamlit 1.64); the viewer
chooses light / dark / system in the app menu (Settings -> Theme), the maps default to the Esri Dark Gray Canvas under the dark theme (CARTO tiles need an API key since 2026, replaced by Esri canvases)
(`lib.theme_type`, `basemap_index`, `ink` for chart lines); test_theme_config_has_light_and_dark_variants.
Forwarded literature that did NOT check out: 'GFM CSI 0.11-0.81 across events' (Roth 2025 gives 0.03-0.97,
> 0.70 in 10 of 18 and in all large-scale events), 'Sen1Floods11 hand labels with uncertain areas removed' (not in the paper);
unread: Pulvirenti 2021 mechanism, Cohen 2022 'uncertain area', the Lefebvre Phragmites number (references_to_verify.md).
DONE 2026-10-01 (maintainer's freeze): headline switched to A_new,dry = 146 [132-166] km2 with dA_wet = 114 [93-135] km2 beside it, A_new = 234
kept as the aggregate under the former state definition (T12hb checks the identities per world: A_new,dry + dA_wet - A_new = +26 [12-40] km2,
the regime wetland dry on 5 June). Literature audit: Crossref/DataCite metadata of every VERIFY entry checked, DOIs added to the classic
references, UNOSAT 3616 / 3623 product sheets and Kadam 2024 read (T16 rows verified), UNEP 2023 PDF read with printed pages in the bib
note (source PDFs under literature_audit/_work/, git-ignored). Still VERIFY: content quotations to locate in Hawker, Johnson, Olofsson,
Giustarini, Maiti, Zheng, Lehnigk, Yi, Monti; Pulvirenti / Cohen / Lefebvre full texts unreachable by script (none of their numbers is in the
text); Rikimaru 2002 and Pedregosa 2011 have no Crossref record (cite as is). No new science for Paper 3 (maintainer 2026-10-01).
Proofreading copies 2026-10-01: `publication/manuscript_uk.md` (Ukrainian translation, numbers copied from the English build and
compared automatically) and `p101_assemble_doc.py` -> `publication/assembled/manuscript_{uk,en}_assembled.{docx,md}` (every figure
and table inserted at its first mention; DOCX and image copies git-ignored, needs python-docx). Citation corrections from the
maintainer's full-text verification (`literature/citation_verification.md`) applied: Hawker 1.61 -> 1.12 m, Lehnigk (corrected
bathymetry still reproduces neither stage nor timing together), Zheng 'limitation, not by design'; Pulvirenti 2021 and Cohen 2022 cited.
OPEN for the maintainer: the remaining 73 km2 of
UNOSAT-only flood on event ground; whether the p95x state mask and the ICEYE comparison enter the paper (with coverage and
admissible interval, as a diagnostic comparison); verify the literature values marked VERIFY in T16 (3616, 3623, Kadam et al. 2024).

## UPDATE 2026-09-23 (late) — read this first; it supersedes the S1-coherence and ordering parts below

**SWOT-DNIPRO no longer owns any of this chain.** Its commit `9419ea3` removed the flood-state branch; everything
below runs from floodstate-eo. Source of truth for anything missing: SWOT-DNIPRO commit `f3e3e1a`.

- **Coherence (p80–p83): CLOSED — `OPTIONAL_LATER_ABLATION` (U6).** Two p82 gate attempts on orbit 65 pair 1 both hit
  `Java heap space` at -Xmx16G under a 24 GB WSL2 cap (single graph; then staged one-JVM-per-subswath, still OOM
  inside IW2 ESD, ~17 h/pair projected). Stopped; failure products kept, renamed `FAILED_*`, with
  `/home/niko/data_s1_coh/_stage/orb65/2023-04-26_2023-05-08/FAILED_README.txt`. p82 now writes transactionally
  (validate → `.ok.json` → atomic rename); a `.tif` without a matching `.ok.json` is refused. Do not restart p82,
  fetch orbits 14/87/138, or tune `-q`, without an explicit decision to reopen coherence.
- **M6 recovered** into `case_studies/kakhovka_2023/workflows/m6/` (13 scripts, provenance headers, rows in
  `provenance/MIGRATION_MANIFEST.csv` with `m6_status`/`reason`), runs into `case_studies/kakhovka_2023/runs/`
  (`.pt` git-ignored). Status: `U0_B2` = SUPERSEDED (linear gamma0), **`U0_B2_CORRECTED` = ACTIVE_REFERENCE (frozen,
  do not retrain)**, `U0b_B2` = CONTAMINATED (do not re-run as an ablation). Torch deps: `pip install -e ".[m6]"`.
- **U0_B2_CORRECTED diagnostics** (`workflows/m6/p75d_u0_inference_diagnostics.py` → `runs/U0_B2_CORRECTED/diagnostics/`):
  reproduction gate EXACT (TP/FP/FN/TN identical to the frozen numbers). Report every number as *agreement with
  held-out weak reference labels*, never flood-mapping accuracy. Test WETLAND F1 0.979, VEG_AGRI 0.393, BUILT_UP
  P 0.059; 268 isolated field-shaped components (25.8 km²); 44 km² predicted on PRE_EXISTING_WATER (unlabelled, so
  invisible to metrics); disputed: 110 of 394 km² ≥ 0.57 (MODEL-SUPPORTED DISPUTED CANDIDATES). Note the frozen
  patch-protocol counts include overlapping patches (stride 128), so pixels are counted several times; the
  unique-pixel full-frame TEST F1 is 0.955.
- **p71 B1 built** (`s1_change.tif`, same 15 channels/order/units/dtype/nodata as B2). B1 long cache has no recorded
  georeference; recovered and verified by content (`p71.LONG_GRID`). Event 2023-06-08 orb167_DES excluded (2 matched
  pre scenes; pooled baselines forbidden). Caveats: 16 % of B1 (980 km², west strip) has no event; B1 baselines are
  6–15 scenes vs B2's 18–23, so **z_* channels are not value-comparable across frames** (overlap Pearson z_vv_max
  0.43, medians 3.8 vs 2.5; d_* channels 0.79–0.94) — `tables/p71_B1_B2_overlap_semantics.csv`. B3 NOT built.
- **m6_labels_v002 built for B1, B2** (`workflows/m6/p77_m6_labels_v002.py`; reads only labels.tif, flood_central,
  flood_possible, per_scene_water — enforced and recorded in tags; `tests/test_m6_label_independence.py`).
  Finding: v002 differs from v001 by < 1 % (B2: +0.76 km² FLOOD, 7.1 km² NON_FLOOD→IGNORE), and BASE_CLASS still
  ranks v002 at AUC 0.927 (v001 0.923). So the old U0b problem was **not mainly construction circularity** — it is
  label-population structure: 52.6 of 57.5 km² B2 FLOOD labels are WETLAND, 4.0 km² VEG_AGRI, while NON_FLOOD is
  ~80 % VEG_AGRI. A surface-context model can learn "field ⇒ dry" from these labels regardless of how they were built.
  Any U1 claim must be made WITHIN strata (esp. VEG_AGRI), not from global F1. B1 has more flooded-field labels
  (25.7 km²) and matters for this.
- **p73 RF20** (`workflows/m6/p73_rf20_surface.py`): PRE-only S2 predictors, WorldCover 2021 target with 4-cell purity
  + PRE-S2 consistency, global 20 m grid. **P73_RF20_FROZEN** (see step 0 below); U-Net input only in U1.

### DECISIONS (maintainer, 2026-09-23) — binding for the next experiments
**D1 — U1 is evaluated WITHIN strata, and B1 is mandatory.** The primary test is U0 → U1 at a fixed land-cover class:
separately for VEG_AGRI, WETLAND_REED, BUILT_UP, BARE_SAND, PRE_EXISTING_WATER (BASE_CLASS/p73 used there for
stratification only, after labels are frozen).
- VEG_AGRI primary endpoints: precision, recall, F1/IoU and FP area (km²), on two sub-populations reported
  separately: *confirmed-flooded fields* and *stably dry fields*.
- WETLAND: recall/IoU plus fragmentation (component count, largest-component share).
- Global F1 is SECONDARY. If U1 improves only global F1 and nothing inside VEG_AGRI, that is a surface-class shortcut,
  not better flood segmentation.
- Split is frozen BEFORE U1 and must put both flood-agriculture and dry-agriculture into the test geography
  (B1 carries ~25.7 km² flooded fields vs ~4 km² in B2). U0 and U1 use the same spatial blocks; comparisons use a
  paired spatial-block bootstrap CI.

**D2 — z_* channels do not enter the main cross-frame model as they are, and B2 is not impoverished.**
- `U0d` (main cross-frame SAR baseline) = d_vv / d_vh / d_vvvh channels + support channels, no z_*.
  Support channels stay (`n_valid_pre_matched`, `n_valid_event`, `n_orbits_event`) so the network sees how reliable
  each anomaly estimate is.
- `U0z` = U0d + z_vv / z_vh — an ablation on the normalisation domain shift. z_* stays only if +z improves held-out
  performance in BOTH frames AND within strata.
- Matched-depth B2 (deterministically trimming B2's baseline to B1-like 6–15 scenes and checking whether z converges
  on the overlap) is a SENSITIVITY experiment only, never the production pipeline.

**Scientific route**
```
B1+B2 m6_labels_v002
   ├── U0d = S1 d_* + support          ← main cross-frame SAR baseline
   ├── U0z = U0d + robust z_*          ← ablation on domain shift
   └── U1  = best U0 + p73 RF20        ← surface-context test
```
The U1 question: **does p73 reduce false flood on dry fields without killing recall on genuinely flooded fields in B1?**

### M6 status 2026-09-24 (after p89 audit and U2)
Arms on the frozen m6_split_v1 (same labels v002, recipe and D1(+A1/A2) harness): U0d (ACTIVE baseline), U0z
(rejected by D2), U1 (+p73), U2 (+HAND). Comparisons: runs/compare_*; audit: tables/p89_*.
- **Wording (binding for logs and paper):** "None of the audited 19.2 km² cropland-associated candidates showed
  positive evidence consistent with breach-induced inundation under the available SAR, optical and terrain
  constraints." They are *cropland-associated SAR candidates*, not "false water".
  A (7.3 km²) = real SAR water present BEFORE 06-06 → a TEMPORAL ATTRIBUTION error, not a spatial false positive;
  B (8.0 km²) = spectral/SAR confusion on elevated cropland; D (3.9 km²) = UNRESOLVED (no S1 water product there is
  not a negative observation).
- **Canonical failure cases** for the paper figure U0 → U1 → U2 → U2b: candidate 22 (B1, E499570 N5205430, group A,
  pre-existing water) and candidate 78 (B2, E440926 N5184734, group D, high-HAND agricultural SAR response).
- **U1** (+p73): land cover is context, not a veto — CROPLAND ≠ not water. Retains 78–91 % of the candidate area.
- **U2** (+HAND, continuous feature + has_hand): A2 −9.6 km² [−14.8, −5.1], A1 −0.42 km² [−1.17, −0.01], B recall
  +0.04 [−0.005, +0.18], B IoU +0.08 [+0.0005, +0.23]; cost: BUILT_UP FP +0.37 km² [+0.04, +1.03]. Retention of U0d
  candidate area: A 0.43, B 0.55, D 0.56. **A is not a clean negative control here**: the group-A fields are also
  elevated (HAND ~50 m, irrigated plateau), so HAND removes them as elevated land, not by temporal reasoning.
- **U2b blocker (label contract):** 0 labelled v002 pixels have pre-breach S1 water (p60 requires land dry in every
  observed pre-breach event), so a W_pre input can never be supervised under v002. U2b needs a label-contract
  decision (e.g. v003 with an explicit "water before the event → not event flood" negative class) before training.
- **Gate:** `U3_BLOCKED_UNTIL_P72_REBUILD = TRUE` — every d* band of s2_sparse_support.tif is invalid
  (workflows/m6/KNOWN_ISSUES.md). Fix = symmetric scaling before clipping; add a sanity test (|Δ| ≤ 2, ~0 % at int16
  limits, nodata preserved).
- **Route:** p89 audit → U2 (+HAND) ✅ → U2b (+pre-event SAR state; needs label decision) → fix/rebuild p72 → U3
  (+optical change) → U4/full fusion.

### M6 status 2026-09-25 -- v003_A arms trained (U0d, U2, U2b); NOT frozen, v003_A still a CANDIDATE label set
Trainer p86 rev 2: `--labels {v002,v003_A}` (v003_A ontology -> EVENT_FLOOD 1, LAND + REFERENCE_WATER 0, UNKNOWN 255)
and arm **U2b = U2 + W_pre** (S1 06-01/06-02 water state + has_wpre, read from the v003_A observation bands). Runs live in
`runs/<ARM>_B1B2_v003A/`, scores in `frames10/<F>/m6/<ARM>_v003A_score.tif`; every v1 run is untouched. Same split,
recipe, seed; ~3 min per arm on the A4000. New evaluators: p90 (v003_A attribution endpoints for ANY finished run at its
own frozen threshold: predicted flood on REFERENCE_WATER, EVENT_FLOOD recall, LAND FP, UNKNOWN burden; paired block
bootstrap across label sets), p91 (maps + curves), p92 (dam -> liman area on the B1 u B2 mosaic with the maintainer's
p42 CUT_RECTS separating the Inhulets valley / terraces from the Dnipro corridor). Tables `tables/p90_*`, `p92_*`;
figures `figures/m6_v003A/`.
- **Label effect (U2 v002 -> U2 v003_A, same inputs):** predicted flood on TEST REFERENCE_WATER 15.3 -> 1.3 km²
  (paired -13.4 [-29.5, -2.5]); EVENT_FLOOD recall 0.956 -> 0.928 (-0.028 [-0.042, +0.006], not significant); the
  drained-reservoir wedge NE of the dam appears at U2 v003_A's low threshold 0.37 and not in U2b (0.78).
- **Input effect (U2 -> U2b, both v003_A):** REFERENCE_WATER 1.27 -> 0.61 km² (-0.62 [-1.28, -0.13]); EVENT_FLOOD
  recall +0.011 [-0.016, +0.016]; D1 endpoints all overlap zero except A dry-cropland FP -0.08 [-0.22, -0.001];
  BU FP +0.19 [-0.07, +0.55]. Global F1 on the v003_A test: U0d 0.929, U2 0.931, U2b 0.937 (NOT comparable with the
  v002 0.945/0.938: different negatives). CAVEAT recorded before training: v003_A EVENT_FLOOD is defined with
  w_pre = 0, so W_pre is also a label ingredient; U2b shows the network uses the channel, not that W_pre is
  independently informative. An independent evaluation reference (step 4 below) is still missing.
- **Dam -> liman (U2b, B1 u B2, one pixel once):** Dnipro corridor (outside CUT_RECTS) 241 km², of which 189 km² inside
  the p42 terrain-eligible floodplain (116 km² on EVENT_FLOOD labels, 65 km² UNKNOWN) and 52 km² outside it (42 km²
  UNKNOWN = the cropland-associated SAR candidates of the p89 audit). Inhulets valley rectangle 30 km² (24 km² on
  EVENT_FLOOD labels, i.e. observed S1+optical water, a 0.5-1.5 km wide strip up to the frame edge at N 5212 km) --
  reported separately, never added to the Dnipro reach. 211 km² of the mosaic have no S1 event (unobserved, not dry).
- Decision needed: freeze v003_A (or revise) before any arm on it is called ACTIVE; U2b then replaces U2 as the
  base for U3 (+optical change, p72 rebuilt) only if the maintainer accepts the W_pre circularity caveat.

### 2026-09-25 (later) -- dynamics and the terrain pillar (p93, p94, p95, p95b); paper = U-Net + RF + terrain, HEC-RAS later
Maintainer decision: the paper is a closed three-pillar study (U-Net M6 arms, RF p73 surface context, terrain/HAND daily
reconstruction); HEC-RAS 2D (p44 package in SWOT-DNIPRO, never run) builds on it afterwards.
- **Why M6 areas are below the published 600-800 km2** (p93): m6 labels are a PERSISTENCE product (S1 water on >= 2 of
  06-09/13/14), i.e. water still standing on 13-14 June (~180 km2 in the literature by 13 June), not the 6-9 June peak
  (~620 km2 UNOSAT). The single 06-09 scene already shows 300 km2 of new dark water in the corridor; peak 7-8 June had no
  scene; ~590 km2 of pre-breach water (1-2 June, incl. sand false water) is subtracted; B3 (delta+liman) not built; the
  dark-water rule is blind under reeds/forest/buildings.
- **p94 per-date series** (11 S1 dates, S2 to end of August, estuary zone 3 on its own grid): inside the p42 floodplain the
  S1 series follows the Kherson recession (203 -> 152 -> 74 -> 22 -> 5 km2); corridor numbers after 06-18 (155, 99 km2) are
  scattered dark fields/sand, not flood. S2 (NDWI>0 & MNDWI>0) adds almost nothing. Coverage is relative to the union of
  the S1 zone footprints (orbit 138 dates = 62 %).
- **p95 terrain reconstruction, daily 05-26..07-10**: WSE H(s,t) from SWOT nodes (p59, exported to
  tables/p59_swot_flood_nodes.csv via the SWOT-DNIPRO venv) + Kherson gauge, projected on the p55 seamless DEM with p42
  constants. Rules: `hand_and_ceiling` (p42, channel-connected lower bound), `ceiling_only`, `connected_ceiling`
  (DEM < WSE, 8-connected to the optical pre-breach water network; PRIMARY). Baseline = same-rule potential on pre-breach
  days (fixed 0.5 m margin) + observed pre water; the model-only part ("normally wet" low reed beds) is its own validation
  category. Sensitivity: event-day margin 0.3 / 0.8 m. Outputs `$BULK_ROOT/floodplain_dyn/<ZONE>[_rule]/`, tables
  `p95_*`, `p95b_dynamics_summary.csv`, figure `hand_dyn_summary.png`.
  Findings (connected, 0.5 m, Dnipro corridor): peak 293 km2 on 06-07, 253 on 06-08, 230 on 06-09, 169 on 06-13,
  74 on 06-18, ~0 by 06-22; volume 0.76 km3 at the peak (planar surface, no ponding, so the recession is a lower bound).
  Validation on 06-09 in the p42 floodplain: POD 0.39 raw, **0.96 excluding S1 onset on normally-wet reeds** (118 of 122
  km2 of "misses" are reed beds below the normal water surface where S1 dark-water onset means submergence, a depth
  signal); S1 "new water" >= 5 m above the water surface (54 km2 on 06-09, cropland/grass/sand) is the sensor's false
  water; terrain-only area (forest 44+13, built-up 12+15, reeds 16+20 km2) is the sensor's blind spot. Inhulets under the
  backwater assumption: POD 0.78-0.98, CSI 0.65-0.85 (ceiling rules); the HAND rule gives ~0 there (HAND measured to the
  Dnipro, not the Inhulets).
- Limits to state: planar WSE per reach (no momentum, no timing), DEM under reeds/forest (FABDEM canopy), SWOT nodes on the
  channel only, no scene at the peak; the U-Net concept (S1 dark-water onset) and the terrain concept (new inundation
  extent) differ in reed wetlands -- report both "new inundation" and "wetland submergence".
- **Oleshky / left bank checked with ICESat-2 (p95c, night ATL08 via SWOT-DNIPRO p57):** where S1 sees water but the
  terrain says the ground is >= 2 m above the 06-09 surface (33 + 27 km2), the seamless DEM matches ICESat-2 to +-0.3 m
  and the ground is 5.6 m (Oleshky grass) to 30 m (cropland) above the water surface, 0 % of segments below it. So this
  is false SAR water on land, NOT a DEM error; the Oleshky terraces above ~11 m were not flooded. Where terrain and S1
  agree, 98-100 % of ICESat-2 ground lies below the surface. `tables/p95c_icesat2_check_0609.csv`.
- Next: freeze v003_A or revise; decide the paper's primary terrain variant (connected_ceiling proposed); B3 frame for the
  liman; HEC-RAS 2D with the p44 package using p95 as the calibration target (SWOT profiles + S1 dates + gauge).

### 2026-09-25 (evening) -- terrain reconstruction rev 3/4: closure and chainage corrections; Inhulets numbers withdrawn
Supervisor review of the paper plan (recorded in memory and in the approved plan): the manuscript is Paper 3 of a series
(Paper 1 = vertical frame + slopes, Paper 2 = bathymetry/terrain, Paper 5 = HEC-RAS); evidence hierarchy physical
reconstruction -> independent/cross-sensor checks -> surface context -> ML under weak labels; claims-first
(`publication/evidence_matrix.csv`, Paper-1 schema, rendered to `claims.md`); area semantics; U2b diagnostic only;
uncertainty budget; three-level reproducibility; release snapshot.
- **Closure (rev 3):** p59 had applied the mean RESERVOIR closure residual (-0.173 m) plus a free2mean term (-0.036 m) to
  the downstream reach, i.e. SWOT heights 0.209 m too low, hidden by the old +0.5 m margin. Paper 1 measured c ~ 0 at Kherson
  (+0.9 cm RiverSP, -2.6 cm PIXC, +1.9 cm in the breach fortnight, NMAD 4-5 cm). p95 now uses
  H = wse + geoid_hght - zeta_EGG2015 + c_Kherson (0.00 m, NMAD 0.05 m) with margin 0 as the central value; the old
  configuration survives only as `--closure p59_reservoir --margin 0.5` (suffix `_closure_p59_m050`, sensitivity).
- **Chainage (rev 4):** the p59 `s_km` (SWORD p_dist_out) is NOT comparable across branches -- Inhulets reaches run
  -1.9..31 km while lying 42-48 km from the dam, Kokan' and the Kherson side channels start their own count -- so the
  1-km-binned H(s,t) table mixed reaches. The water surface is now NODE-BASED: median of the 5 nearest SWOT nodes within 3 km
  per day, per-node time interpolation, the gauge as one more node, gauge cap only beyond 15 km west of the gauge
  (`p95.WSE`, shared by p95c/p95d/p95e via `load_engine`). `p95_wse_table*.csv` are gone; `p95_wse_profile_display.csv`
  (straight-line distance, main stem, observed only) exists for the figure only. The p59 5-km binned profiles carry the same
  chainage problem (note for Paper 1/2).
- **Effect (connected_ceiling, corridor):** peak 347 km2 on 06-07 (was 293 under the old closure+margin+baseline), 337 on
  06-08, 295 on 06-09, 233 on 06-13, 111 on 06-18, ~0 by 06-22; peak volume 0.93 km3. 06-09 vs S1 in the p42 floodplain:
  POD 0.68 raw / 0.90 excluding normally-wet, FAR 0.45, CSI 0.44 (was 0.39 / 0.96 / 0.56 / 0.33). The Inhulets now has its own
  SWOT nodes: POD 0.46-0.54 raw, CSI 0.39-0.47 (06-09..06-14). **The earlier "Inhulets POD 0.78-0.98, CSI 0.65-0.85" came from
  runs before the rule-consistent baseline and is WITHDRAWN; cite only the current p95_validation_s1* tables.**
- New: p95d (disagreement ontology A/B/C x WorldCover x p73 x elevation-above-surface bins, committed tables), p95e (Monte-Carlo
  uncertainty of area/volume: closure, gauge, SWOT wse_u, per-node interpolation, class-wise DEM error field), p95c re-run on
  the rev-4 surface. The `_m030/_m080` margin variants are deleted (replaced by p95e).

### 2026-09-25 (night) -- rev 5: DEM class-bias correction; the reed-bed definition dominates; publication bundle built
- **Rev 5 (p95):** the seamless DEM enters minus its class-median residual against night ICESat-2 (Paper 2 / p57: trees
  +1.5-2 m, wetland ~+0.5, grass ~+0.4, cropland ~0), so the Monte-Carlo band (p95e, class NMAD as sigma, correlated 500 m
  field) is centred on the reported central run; `--dem-bias none` keeps the uncorrected DEM as a sensitivity
  (suffix `_dem_uncorrected`). Consequence: the delta reed beds now sit at or below the NORMAL water surface and belong to the
  pre-breach regime, so the corridor peak on 06-07 drops from ~350 km2 (DEM as delivered) to ~235 km2 (central), and the
  Sentinel-1 "misses" inside the p42 floodplain are almost entirely normally-wet cells (POD raw ~0.26, POD_excl ~0.96).
  This is a DEFINITION (new inundation vs wetland submergence), not a metric error, and the paper reports both quantities.
- **Publication bundle:** `publication/{evidence_matrix.csv, claims.md, manuscript_template.md -> manuscript.md, captions.md,
  references_to_verify.md, tables/, figures/}`; scripts `workflows/paper/{p96, p97, p98, p99, fill_manuscript, fill_evidence,
  render_claims}`; `src/floodstate_eo/visualization/figstyle.py`; notebooks 00 (filled) + 01/02/03 (executable from tables);
  Streamlit dashboard `apps/dashboard` (layers 1.9 MB); tests `test_figstyle`, `test_paper_tables`, `test_dashboard_bundle`.
- **Block-size sensitivity (D1):** 5 km infeasible (no validation patch survives the buffers); 7.5 / 15 / 20 km splits built
  (`m6_split_s7p5/s15/s20`) and U2 v003_A retrained on each (`runs/U2_B1B2_v003A_s*`); T20/FigS05.
- Docs: METHODS items 22-26, DATA_DICTIONARY Paper-3 products, REPRODUCIBILITY in three levels, README/CITATION/project.json
  to v0.2.0-alpha, CLAUDE.md (repo public after the push), UNRESOLVED #2 resolved (figstyle).
- Open before submission: verify every `VERIFY` bib entry and the literature area figures; decide the wording for the
  reed-bed definition in the abstract; B3 frame; HEC-RAS (Paper 5) on the p95 daily surfaces.

### 2026-09-26 -- scientific consolidation (supervisor review): six hard gates before the manuscript is frozen
Stage change: exploration -> consolidation. No new experiments; reduce the possibility of misreading the results. Implemented
in this commit; enforced by `tests/test_terminology_freeze.py` and `publication/TERMINOLOGY.md`.
1. **Terminology frozen**: "observation-constrained terrain inundation reconstruction" (no momentum/continuity equations; never
   "physical reconstruction"); "reconstructed total water-surface area" (W_total) vs "reconstructed newly inundated area" (A_new);
   "daily reconstructed series", never "daily observed"; temporal semantics on every area (T16: snapshot / cumulative /
   persistence). UNOSAT ~620 km2 is cumulative flooded LAND 6-9 June (reference water separate): closer in kind to A_new than to
   W_total; the earlier sentence "779 + 69 ~ 850 km2 comparable with 600-800" is withdrawn.
2. **54 km2 S1-only >= 5 m above the surface**: "topographically unsupported by the reconstructed connected water surface; the
   available ICESat-2 observations give no evidence for a DEM bias large enough to explain it" -- never "false SAR water"
   (tracks do not sample every cell; radar shadow, smooth surfaces, local ponding, timing, registration are untested alternatives).
3. **Uncertainty hierarchy**: the 40 spatial MC draws (p95e) are the PRIMARY interval of every area and volume (T12
   `W_total_p05/p95_km2` = central + new-area deviations, `A_*`, `V_*`); the 100 000-draw emulator (p95g) is a SENSITIVITY
   envelope of the AREA only (`*_emu_*`). Found while wiring it: the emulator's volume draws are ~3x the spatial MC (raw,
   unanchored, symmetric DEM error under canopy) -> dropped from T12. Found too: the MC half-widths of area and volume are
   similar (4 vs 5 % on 06-07) but the volume distribution is displaced above the deterministic run by ~2x the area's shift
   (+12 vs +5 %); C07 states this instead of the expected "area uncertainty << volume uncertainty" (`rel_halfwidth_*`,
   `mc_shift_*` in T12). Volumes always carry p05-p95 and the MC median.
4. **Reservoir**: T21 `Q_release_eff_daily_mean_m3s` = -dV/dt + Q_in is a daily-MEAN effective release, never a breach
   discharge; "most of the released volume was transmitted downstream rather than stored on the mapped floodplain", not "went to
   the liman". Hypsometry gap DEM vs design (T22 `dV_rel_pct`, FigS07): ~-9 % at full pool, -15..-20 % at 11-13 m, undefined below
   10 m -- shown as a result. Yi 2025 (initial breach flow 5.7e4 m3/s) and Kadam 2024 (HEC-RAS 3.6e4) are cited as different
   quantities, context only (VERIFY).
5. **Claims axis C01-C14** (evidence_matrix.csv with `former_id` and `limitation`): C01 areal maximum 7 June between acquisitions,
   distinct from the 8 June peak stage; C02 W_total 488 -> 779, A_new 235, V 509 with primary intervals; C03 recession + Inhulets;
   C04 raw S1 agreement conditioned by surface type (conditional POD = diagnostic, `POD_cond_outside_normally_wet`); C05 ontology;
   C06 ICESat-2 + SWOT-gauge constrain the vertical-error explanation; C07 area vs volume uncertainty; C08 area semantics /
   agreement not accuracy; C09 label effect ("no statistically resolved change in recall"); C10 HAND/context; C11 U2b diagnostic;
   C12 RF20; C13 block size; C14 reservoir balance (context).
6. **Release candidate** `v0.3.0-rc1` tagged after this commit; no further analysis in Paper 3.

**Next step (maintainer decision 2026-09-26): Paper 4 = the reservoir bowl reconstructed on the historical (pre-impoundment /
design-survey) bathymetry**, a separate paper. The p95f balance and the hypsometry gap of T22/FigS07 are the hand-over; p95f is
not extended further here. Paper 5 (HEC-RAS) then uses Paper 3's daily surfaces as the calibration target and Paper 4's bowl.

Remaining before submission (not scientific-quality blockers): VERIFY bibliography entries (`references_to_verify.md`),
Zenodo DOI from the release, Streamlit Cloud deploy, the sidebar label "streamlit app" (file name), notebook 01 file name still
says "physical_reconstruction" (title corrected; renaming breaks links in docs -- do it with the docs at release).

### 2026-09-25 (late) -- headline = TOTAL water surface; 100 000-draw emulator; reservoir balance
Maintainer: "the flood zone is all the water, not only the new water". Corrected everywhere: T12 carries W_total_* (total
water surface on the day) next to A_* (new inundation); Fig04 shows the total with candles and the daily change as bars.
- p95g cluster-normal emulator: 100 000 draws per day of new area / volume from the margin histograms per WorldCover class
  (class NMAD x the cell-level std of the p95e field, clusters of 625 cells) and a scalar water-surface offset; the total's
  draws = deterministic total + new-area deviations (the pre-breach water is observed, not propagated); the raw emulator
  total is inflated by the symmetric DEM error under trees and kept only for transparency. Checked against the 40 spatial
  draws (p95g_vs_p95e.csv): emulator p05-p95 wider than p95e (e.g. 214-293 vs 247-255 km2 on 06-07), p50 +7 %.
- p95f reservoir balance: sloped daily pool surface (SWOT outlet, Nikopol press, Rozumivka gauge, ICESat-2, G-REALM; p61 of
  SWOT-DNIPRO), integrated on the seamless 50 m DEM inside the pool polygon; pre-breach 18.9 km3 (design table 21.1 at the
  same level: DEM hypsometry 8-12 % low), 4.5 km3 on 13 June, 14.7 km3 released, implied peak breach outflow ~40 000 m3/s
  on 06-07 (DniproHES inflow ~2 700); downstream stored new water peaks at 0.65 km3 (~4-5 % of the release). Not defined
  after 13 June (the pool is a river). Claim C13, T21/T22, Fig09.
- Totals (corridor, deterministic): 488 km2 normal regime (06-05) -> 779 (06-07) -> 724 (06-09) -> 632 (06-13) -> 517 (06-21);
  Inhulets 21 -> 69 -> 76 -> 63 -> 22; S1 total dark water 06-09: 682 + 68 km2. These are the numbers comparable in kind with
  the 600-800 km2 of operational products (which still differ in AOI -- no B3/liman here -- and reference water).

### 2026-09-28 -- reservoir drawdown maps (p95h, FigS08/FigS09, dashboard); context only, no claim
Maintainer: "також мають бути карти спустошення водосховища ... також S2 то всі класифіковані індекси".
- p95f refactored into helpers (load_levels / load_pool / day_points / sloped_wse); p95f tables byte-identical after the change.
- `workflows/m6/p95h_reservoir_maps.py`: MODEL wet mask per day (05-26..06-13) + day of exposure ($BULK/reservoir_maps/model);
  S1 water from `s1_zone_cache/ZONE_1_reservoir_corrected` = **VH** dB < per-date Otsu over all covered cells, clamped
  [-24, -15] dB (VV-in-pool Otsu failed: wind-roughened water, IoU 0.61); S2 = frozen SWOT-DNIPRO p25 k10e/water3/7-index
  stacks + p15 crosscheck water, not re-classified. Tables `p95h_reservoir_maps.csv`, `p95h_s2_classes.csv`.
- Agreement with the model: S2 06-05 IoU 0.98; S1 0.98 / 0.97 / 0.93 / 0.85 on 06-01 / 06-08 / 06-09 / 06-13. **S1 VH dark
  = water or wet mud**: from ~06-13 it overcounts (06-20: S1 1702, S2 648 km2; Yi et al. 2025 ~845 km2 from their text,
  S1 + S2 -- the 825 km2 in T23 is digitised from their figure, see below) -- do not use S1 as a water area after the drawdown.
- Literature audit 2026-09-28 (GeoHydroAI, literature_audit_paper3): the Yi 2025 areas (2089 / 1849 / 825 / 369 km2,
  SWOT-DNIPRO p61_yi2025_reservoir_area.csv, fractional days + assumed hour) are NOT in Yi's text -- digitised from a figure
  of their S1 + S2 mapping. Column renamed `yi2025_digitised_km2` (p95h, T23), FigS08 caption, Fig09 legend and dashboard
  relabelled. OPEN: the figure number; the T12 `definition_note` fix named in the audit's 06_unresolved.md; the maintainer's
  decision on reporting the MC median [p05-p95] with the deterministic run in brackets (deterministic < own MC p05:
  A_new 235 vs 247 [238-255] km2, W_total 779 vs 790 [781-799], V_new 509 vs 566 [545-596] hm3).
- **Maintainer decision 2026-09-28: the reported central value is the MC MEDIAN [p05-p95], the deterministic nominal run in
  brackets.** p95e now runs every post-breach day (`--days all`, default; the 9 key dates reproduce exactly, the RNG is consumed
  per draw); T12 leads with *_p50_*, new T12b = the daily series (median, p05-p95, nominal, flag nominal < p05); manuscript
  template, fill_evidence (C01-C03, C07), C02 statement, dashboard headline, Fig04 (median line, nominal dotted) switched.
  Cause of the nominal-below-p05 offset NOT diagnosed -- say so, never explain it away.
- **Design hypsometry (maintainer: "старі проєктні дані водосховища", monograph Table 19 / Figs 13-15):** p95i =
  Table 19 (pool + 5 reaches, design levels NUF/NPG/UNS/GMO) + Table 21, both datums (BS, +0.185 EVRF), and the observed
  2023 levels (T21) read on the design curve -> design volume at the outlet and at Rozumivka (sloped surface -> a range),
  released volume from the design curve, undefined once the outlet < 10.0 m (from 06-09). T27/T27b, FigS10. NO DEM, no
  soundings, nothing fitted: a first version that compared the seamless DEM and the datum-fitted soundings was rejected
  by the maintainer ("повна хірня") -- the soundings agree with Table 19 by construction of the hist2 datum fit, and the
  daily sloped-surface points are not comparable with level-surface curves; do not bring that back.
  Then extended (maintainer: "словами ... ухил, до-проривні рівні за 2-3 місяці ... скиди ДніпроГЕС"): p95i reads 1 Feb - 10 Jul
  2023 (Rozumivka 80959 terms 08/20 from k5 -- the only 2023 daily gauge series; Nova Kakhovka / Nikopol / Plavni end in 2021;
  G-REALM, ICESat-2, SWOT outlet as checks) + dniprohes_releases.csv. Findings (design curve, no DEM): filling from 13.5 km3
  (14.0 m EVRF, 8 Feb) to 21.3 km3 (17.6 m, 5 May) = +7.9 km3 of 22.7 km3 DniproHES inflow (35 % stored; HPP outflow
  1.4-3.7 x 10^3 m3/s); plateau ~17.5 m in May; -0.4 m in the last 10 days before the breach (21.3 -> 20.1 km3). Drawdown:
  Rozumivka-level balance 12 / 38 / 20 / 19 x 10^3 m3/s on 06-06..06-09 (T21 sloped-surface: ~40 000 on 06-07); the
  outlet-level balance is unusable on 06-06 (111 000: the outlet fell 5 m in a day, the pool did not). CAVEAT: the pre-breach
  SWOT outlet value in p95f is HELD (few passes), so the pre-breach "gradient" of -0.45 m is an artefact, flagged in T27b.
  T27 (Table 19), T27b (daily), T27c (weekly), FigS10.
- **Literature audit (GeoHydroAI, 2026-09-28)** is in `case_studies/kakhovka_2023/literature_audit/` (deliverables 01-10,
  02_thesis_evidence.csv, 07 verified bibs, revisions.yaml, article/Paper3_final.md = the audited text with the 36 + 4 revisions;
  figures/tables copies and the .docx are git-ignored). Round 1 and 2 actions: `docs/AUDIT_ACTIONS_2026-09-28*.md`, closure in
  `publication/VALIDATION_2026-09-28.md`. Round 3 (same evening): the 49 corpus keys (`07d_corpus_references.bib`) are merged
  into `docs/references.bib` (135 keys) and all 26 remaining audit revisions are in `manuscript_template.md` (table numbers as
  placeholders) -- the bundle manuscript and the audited article now carry the same literature; `Paper3_final.md` is the
  audit's assembled copy (figures + tables inline), `manuscript.md` the bundle's source of truth. Still open: Yi 2025 figure
  number; "19 m near the dam" (no source); attribution of the nominal-below-p05 offset to the error terms (diagnostic run). S2 dates with >= 50 % of the pool observed: 05-06, 06-05, 07-05, 08-17, 09-08 (06-30, 07-25,
  08-27 are < 7 %). The drawdown week (06-06..06-20) has S2 water only (crosscheck), no index stacks -- a gap if needed later.
- p98 `--only reservoir`: 73 reservoir layers on their own EPSG:4326 box, clipped to the pool + 1 km (4 MB); Maps page has
  "zoom to" and a Reservoir drawdown block; Reconstruction page shows model vs S1/S2/Yi areas. FigS08, FigS09 (supplement).
- Tables (maintainer: "додай таблиці це важливо ... таблиці по індексах"): T23 pool water area by source; T24 k10e classes;
  T25 index statistics (mean, std, p10..p90); T26 index display classes -- every 2023 p25 date observing >= 50 % of the pool
  (02-10, 05-06, 05-11, 06-05, 07-05, 08-17, 09-08, 09-23, 09-28, 10-03, 11-07), strata POOL / EXPOSED_BY_0613 /
  WET_ON_0613. Findings: all water indices flip sign after the breach (MNDWI p50 +0.33 -> -0.26 on 07-05), BSI peaks on
  07-05 (+0.13); by September reed / flooded vegetation covers 47-50 % of the bed exposed first and 34-37 % of the rest, and
  NDVI p50 there is 0.44 vs 0.26. Autumn dates observe only ~52-65 % of the pool (one tile).
- Dashboard literature (maintainer: "посилання на пейпери ... до кожного пункту ... особливо по індексам та класифікації";
  "класифікація random forest нижньої частини"): `apps/dashboard/lib.py` reads `docs/references.bib` (TOPICS, INDICES, CLASSIFIERS,
  SERIES); every page section has a literature expander, Maps shows the literature of the layers switched on; new page
  7_Literature (series + repos, classifications, index formulas, METHOD_REFERENCES table, bibliography by topic, p100 theses);
  Surface context = RF20 map of B1+B2, class areas, method from the p73 manifest, QA panels. Bibliography 52 -> 85 entries,
  every new DOI Crossref/DataCite-verified (Yi_2025 corrected to 8 authors); Rikimaru_2002 (BSI) and Pedregosa_2011 have no DOI.

### 2026-09-29 -- response to the scientific / code review of 2026-09-28 (F01-F20), Stage 1: the uncertainty engine
Review and literature notes moved to `case_studies/kakhovka_2023/reviews/`; action ledger `docs/CODE_REVIEW_ACTIONS_2026-09-29.md`
(every finding checked against 06441cf: F01-F19 confirmed; decisions D-BIAS, D-BED, D-CORR, D-INTERP, D-MC1, D-N, D-SEAM,
D-RULE, D-VERT; D-EMU open). Maintainer scope: Stage 1 now, then STOP for the new numbers; Stage 2 = F09 -> labels v004 ->
arms retrained, F10, F08 with the RF20 production refit (new freeze), F11, F12 hold-out; Stage 3 = F13-F19 + the text pass.
Conceptual corrections: FABDEM is a bare-earth DTM; the terrain layer is the seamless terrain-bed model (FABDEM outside the
surveyed channel, bed inside, source mask 1-5); the WorldCover class median is a RESIDUAL terrain-elevation bias (FABDEM cells
only, never on bed); everything in EVRF2019 (asserted); no new physics while answering the review.
- New event-agnostic core `src/floodstate_eo/terrain/` (fields, connectivity, mosaic, interp, vertical) with tests.
- p95 rev 6: union mosaic (ownership for accounting), Hmat-only error contract, per-zone FABDEM-only residual table, support
  flags, `connected_ceiling` default with explicit suffixes, repository gauge copy, legacy mode = exact rev-5 reproduction gate
  (all 138 / 276 / 33 rows identical); attribution T11h (A_new 06-07 nominal 235.3 -> 243.2 km2, almost all from the terrain
  table; the mosaic changes nothing on the real rasters, T11i).
- p95j: FABDEM - ICESat-2 residuals per zone/class (T18b) and the semivariogram of the standardized residual: pooled robust nested
  fit nugget 0.08 + 0.50 exp(-h/123 m) + 0.42 exp(-h/1172 m) (T18c, FigS11).
- p95e rev 2: coherent worlds (one terrain field over the mosaic, one water-surface realization, baseline rebuilt), W_total /
  A_new / volumes from their own ensembles, gap-matched interpolation CV (T11f), 1000 worlds + convergence (2 seeds, T11c) +
  ablation (T11d) + day-of-maximum distribution (T12c) + WSE-offset sensitivity (T11e). np.nanmedian replaced by a bit-identical
  row median (its per-row warnings were 40 % of the run time); exact cropping to the base bounding box.
- p95c: F12 mask fixed (ZONE_4 terrain-only 6764 -> 4821 ICESat-2 segments), raw and corrected residuals, n_dates.
- Structural finding for the maintainer: the delta far from the SWOT nodes takes the nearest node's level; dropping nodes with a
  > 3-day gap raises the corridor A_new on 9 June from 188 to 252 km2 (7 June unchanged) -- not in the Monte-Carlo budget.
- Monte-Carlo, 1000 coherent worlds (seed 20260929; gate: draw 0 == the p95 nominal run on 276/276 rows, identical cell counts;
  field std 1.000, 0.985-1.016; new area 0 before the breach in every world): corridor 7 June A_new 262 [250-278] km2 (nominal
  243, below p05), W_total 791 [767-819] (nominal 797 inside), V_new 627 [585-674] hm3; areal maximum on 7 June in 77 % of the
  worlds, 8 June in 23 %. Convergence (2nd seed), ablation and WSE-offset runs: see the ledger / T11c-T11e.
- Independent gauges (p95k, T17c-T17f). The maintainer's check of the cm-above-zero conversion found a SIGN error: Kalynivske
  80575 has its zero at -1.34 m BS (yearbook sheet header), p95k had +1.34 -- every Kalynivske level was 2.68 m too high;
  corrected, zeros now read from the sheet headers (80564 is 56.34, not 56.44). Table 1.2 holds daily MEANS: peaks, rises and
  records now use the yearbook's highest level ('Вищий'): Kalynivske 772 cm = 6.59 m EVRF2019 on 10 June (record since 1927),
  Mykolaiv 602 cm = 1.22 m on 8 June (record since 1963, rise 1.05 m); the Kherson series of the engine equals the yearbook.
- D-INHULETS DECIDED (maintainer): Kalynivske withheld from the primary, kept as an independent tributary validation site
  (e_abs, e_rise, peak timing, recession); the gauge-node run is a separate sensitivity (it lowers the valley's new area on
  7 June 41.4 -> 19.2 km2 and raises the S1 CSI on every event date). Results: e_abs +9.5 m on 6 June, peak -3 d, e_rise
  -0.72 m on 14 June (the reconstruction drains ahead of the valley; the close absolute agreement on 13-18 June is a
  coincidence of two errors), support at the gauge constant (Dnipro node 39.5 km). 86 % of the valley's new area on 7 June
  comes from nodes > 20 km away (27 % cross-river): claims above the lower valley are weakly constrained -- the exact
  restriction criterion is for the text pass (C03).
- Liman (Mykolaiv 98027): the serving node of the western delta (E 457.6 km) is unobserved 6-22 June and interpolated flat
  across the flood (-0.82 m vs the liman on 8 June): F05 confirmed by an independent gauge; Mykolaiv is the second withheld
  validation site (Kherson = input/anchor).
- Maintainer's review of the numbers (same day) -> Stage 1 FROZEN after these decisions: D-SUPPORT = full reconstruction
  primary + support classes direct <= 3 km / extrapolated 3-10 km / weak > 10 km (cross-river and gauge-capped as flags; p95l,
  T11k/T11l; corridor 7 June: 25 % weak, core 182 of 243 km2, the 10 km cap run 180 km2); D-EMU = the emulator is a diagnostic
  only (T12d); claims C01-C03/C07 rewritten with the rev-6 numbers and the baseline-connectivity mechanism; the full draw
  tables are release assets (checksums in tables/p95e_draws_checksums.csv); no gravity layer (z < H already carries it);
  manuscript §3.2 states the static model and §5 why hydraulic modelling (Paper 5) is needed, with the withheld gauges as
  evidence (Dale 2026, Kasmalkar 2024, Barnes 2021 added, Crossref-verified).
- Figures, maps and the dashboard for these results: FigS14 (map of the support classes of the new inundation on 7 June with
  the SWOT nodes and the three gauges; daily full vs supported core; weak share), FigS15 (the two withheld gauges: levels,
  e_abs, e_rise); dashboard: daily support overlays + gauge markers on the Maps page, an observational-support section on the
  Reconstruction page, a withheld-gauge section on the Checks page. README and apps/dashboard/README link the live app
  https://floodstate-eo.streamlit.app -- it becomes live when the maintainer deploys `apps/dashboard/streamlit_app.py` from
  `main` on Streamlit Community Cloud with the App URL `floodstate-eo` (after the Stage-1 branch is merged and pushed).
- c-HAND (Wang et al. 2024, Frontiers in Water; verified) cited as the static terrain-connectivity precedent (§3.2, Limitations,
  §5); claims C01-C03/C07 checked against the tables, four precision fixes. Stage 1 FROZEN; the branch
  `review-2026-09-28-stage1` is merged/pushed only after the maintainer has reviewed C01-C03/C07.
- NEXT: Stage 2 = F09 (inner out-of-fold M2 threshold -> labels v004 -> arms retrained) -> F10 (label contracts, lineage) ->
  F08 (global blocks, overlap dedup, RF20 production refit, new freeze) -> F11 -> F12 hold-out.

### 2026-09-29 (afternoon) -- Stage 2 of the review response: independence and ML (F09 -> F10 -> F08 -> F11 -> F12)
Branch `review-2026-09-28-stage2` (from the frozen Stage 1, 7795cad; code 214bf93). Record of every check:
`case_studies/kakhovka_2023/publication/VALIDATION_2026-09-29_stage2.md`; ledger rows F08-F12 in `docs/CODE_REVIEW_ACTIONS_2026-09-29.md`.
- F09: the M2 operating threshold now comes from inner out-of-fold scores (p65b `inner_oof_threshold`, fit and calibration disjoint;
  the in-sample rule kept per fold as `threshold_insample_superseded`). The corrected M2 (maintainer decision: WITHOUT the
  post-event TRACE window, 67 features) -- block CV pooled AP 0.924; median threshold 0.266 (OOF) vs 0.446 (in-sample), outer recall
  0.928 vs 0.860 for the target 0.90 (T02c). Production p67b `--exclude trace`: T50 0.2661 (was 0.5358), overlap QA 0 mismatches.
- F10: labels v002_notrace and **v004** (the v002 / v003_A rules on that M2); lineage table + contracts + test: v004 does not depend
  on TRACE. v004 EVENT_FLOOD B1 128.9 -> 141.9, B2 57.5 -> 75.2 km2 (nothing leaves EVENT_FLOOD; T02d); v002 DISPUTED shrinks
  (285.8 -> 122.9, 337.6 -> 100.4 km2). CAVEAT: without TRACE the M2 scores pre-event open water as flood-like (98 % of PRE-water
  cells >= 0.5 in B2/B3; B3 23.9 % of all cells vs 1.3 % for the original model) -- outside M2's training domain; the labels are
  guarded (FLOOD needs pre-breach land), but the M2 masks must not be shown as a flood map on permanent water.
- F08: RF20 rev 2 (global UTM blocks, B2 owns the overlap, buffered CV, transfers outside the overlap): CV macro F1 0.943 -> 0.941
  (buffered 0.929); the rev-1 B1->B2 transfer was inflated by the overlap: 0.904 -> 0.848. The map hardly changes (96.9 % / 96.8 %
  of cells). Consumers switched (U1 input and strata of every stage-2 arm, p95d/T14, T09/T10/T10d, FigS04, dashboard, notebooks);
  QA verdict `tables/p73_rf20_rev2_qa/QA_VERDICT.md`; FROZEN after the clean-tree gate (8 product rasters bitwise, acf190c).
- F11: NaN for undefined ratios (m6_eval, p90) with n_defined; 15 arms on the corrected labels with three seeds (U0d, U2, U2b,
  U1 on v004; U2 on v002_notrace for the label effect) + U2 v004 block-size runs. Seed noise is large (cropland burden range up
  to 20.8 km2 within one arm). Across seeds: the label effect on REFERENCE_WATER holds (3/3; C09); the HAND reduction of the
  cropland burden does NOT replicate (C10); RF20 context lowers built-up FP (3/3 same sign) but raises the cropland burden (3/3);
  W_pre lowers the cropland burden (3/3) -- C09-C11 marked "re-tested, statement pending review".
- F12: pass hold-out of the class bias (T15b/T15c): S1-only >= 2 m median moves <= 0.035 m; epochs <= 0.24 m in the delta; the
  delta class biases rest on few passes (wetland +0.22 m pre-breach vs +0.59 m post-breach passes; not propagated in the MC).
- Found on the way: T09's MACRO_MEAN also averaged the p73 MACRO / OVERALL_ACCURACY rows (n counted 3x; C12 "1177260 CV samples"
  -> 392420); the WorldCover frames sit half a cell off the terrain grid (6.9 % of the ICESat-2 check segments get another class).
- Figures: Fig03 on v004 with one marker per seed and (review F15) areas and recall on separate axes; FigS01 v004 seeds;
  FigS04 rev 2; FigS05 v003_A + v004. The manuscript §3.5/§4.4/§4.8 carry the stage-2 numbers; §3.6 and §4.9 (labels, arms)
  still describe the v002 / v003_A arms and wait for the maintainer's decision on C09-C11 (text pass).
- NEXT: the maintainer's review of the stage-2 numbers (C09-C11 statements; whether v004 becomes the paper's label version in
  the text); v004 labels and RF20 rev 2 are FROZEN (both clean-tree gates bitwise); the with-TRACE comparison CV (T02c row of
  the original model); then Stage 3 (F13-F19 + the text pass). No merge / push without the maintainer.

### 2026-09-29/30 -- Stage 3 (F13-F19), the text pass, the drawdown maps and the alignment with Paper 1 v6
Branch `review-2026-09-28-stage3` (commits 7bcc4ae .. c146db5 for F13-F19 and D-DEPTH; this pass on top). Ledger section "The text
pass, the drawdown maps and the alignment with Paper 1 v6" in `docs/CODE_REVIEW_ACTIONS_2026-09-29.md`; record of the checks in
`case_studies/kakhovka_2023/publication/VALIDATION_2026-09-30_stage3.md`.
- F13-F19 done (bounded hypsometry, weekly balance, figure/caption quantities, rebuild DAG + tiny geodomain + input manifest + lock,
  one version 0.3.0rc2 + link check, p71 orbit count, p76 guard) and D-DEPTH (Fig07a maximum depth, Fig10 reservoir depth).
- The manuscript rewritten in one pass (four result blocks; decided wordings; C13 narrowed); T28 = what changed after the audit;
  TERMINOLOGY: *observation-constrained terrain-connectivity reconstruction*; claims C06-C14 restated.
- Drawdown maps (maintainer: "no drawdown on the maps"): main-text Fig11 now from Sentinel-2 (water by date, the day the bed fell dry,
  bed classes, area over time); the first week lowered the pool in depth (Sentinel-2 confirms the model, IoU 0.85-0.90), the area
  collapsed by 20 June; the Nikopol censored bound and G-REALM fixed in p95f.
- D-PAPER1 (maintainer 2026-09-30): Paper 3 matches Paper 1 v6 and does not repeat the vertical validation. Kherson gauge +0.2076 m
  (was +0.22), pool outlet in the production chain (+0.073 m; reproduces 17.61 -> 5.71 m), FABDEM and ICESat-2 ground +0.038 m
  (Paper 2's chain; note for SWOT-DNIPRO). Reconstruction rev 7, full physical chain recomputed with 1000 worlds.
- NEXT: the maintainer's review (the U1 sentence of C10; Paper 2's chain at the source); then merge -> main -> push -> tag
  (v0.3.0-rc2 or the maintainer's name) -> Streamlit redeploy -> Zenodo DOI. No merge / push / tag without the maintainer.

### DECISION D3 (maintainer, 2026-09-25) -- m6_labels_v003_A is FROZEN
- **Frozen product:** `$BULK_ROOT/frames10/{B1,B2}/m6_labels_v003_A.tif` (ontology 0 LAND / 1 EVENT_FLOOD / 2 REFERENCE_WATER /
  255 UNKNOWN + 10 evidence bands), built by p77d rev 2 variant A. Record: `tables/m6_labels_v003_A_FROZEN.json` (p77e:
  sha256 of both rasters and of the two S1 source caches, build commit, freeze commit, reproducibility gate).
  Test `tests/test_m6_labels_v003A_frozen.py` fails if the record, the build manifest or the rasters on disk drift.
- **What it means:** STATUS, NOT PROMOTION -- weak reference labels for supervision and scoring; every number stays
  "agreement with weak reference labels". EVENT_FLOOD is pixel-identical to v002 FLOOD; the change is the negative side
  (REFERENCE_WATER = recurrent May-2023 S1 water on >= 3 admitted dates) and the UNKNOWN domain.
- **Consequences:** `U0d/U2/U2b_B1B2_v003A` are now the reference arms; U2b (+W_pre) is the base for U3 (+optical change,
  p72 rebuilt). The v002 arms (U0d/U0z/U1/U2 _v1) stay frozen history, never retrained. Variant B stays SENSITIVITY_ONLY.
  Any change of rule, scene QA or sources is v004, never an edit of v003_A. The W_pre circularity caveat (input and
  label ingredient) is accepted and must be stated wherever U2b is reported.

### Ordered next steps (replaces the list at the bottom where they conflict)
0. ✅ **p73 RF20 FROZEN** (2026-09-23, products of `5f875ce`, clean-worktree reproducibility gate bitwise PASS;
   `tables/p73_rf20_manifest.json`, `tables/p73_rf20_qa/QA_VERDICT.md` — read its 7 limitations before using p73).
   Old VEGETATION_AGRICULTURE = CROPLAND ~64 %, GRASS ~20 %, FOREST 7–10 %, WETLAND_REED 0.4 %, UNCERTAIN ~5 %.
   Optional: B3 by pure inference (`--infer B3`).
1. Freeze the B1+B2 split per D1 (flood-agri and dry-agri in test geography; same blocks for every arm).
2. U0d, then U0z (D2). Evaluation harness per D1 (strata, sub-populations, FP km², paired block bootstrap).
3. U1 = best U0 + p73. Later U2 +HAND/distance to water, U3 +S2 06-08, U4 +S2 06-18, U5 +TRACE;
   U6 +coherence only if the baseline works.
4. Independent evaluation reference: observations that took no part in label construction (none exists yet).
5. B3 p71 only after the B1 caveats above are accepted.
6. Still uncommitted from the earlier session (not part of the M6 commits): the `_kakhovka_legacy_config.py` CRS fix,
   `case_studies/kakhovka_2023/manifests/*.csv`, `provenance/UNRESOLVED_DEPENDENCIES.md` #7/#8, `CLAUDE.md`.

## Current state, precisely

- **Committed** (`86cf8a6` on `main`, local only — **not pushed** to `git@github.com:NikoriakViktot/floodstate-eo.git`):
  Migration Phase 5 ("copy canonical code with provenance headers") — 59 files. 20 Kakhovka-specific
  scripts + 8 core-library modules copied from SWOT-DNIPRO (frozen at commit
  `f3e3e1afe91902a82a73f3c09354d1f9eb847766`) with real provenance headers (source path, source commit SHA,
  sha256) and package-import fixes only — logic byte-identical to source. `config.py`/`spatial_domains.py`
  scoped-extracted into 7 YAMLs under `case_studies/kakhovka_2023/config/` plus a generic
  `spatial/domains.py`. Docs shipped: root + case-study README, `docs/METHODS.md`, `docs/DATA_DICTIONARY.md`,
  `docs/REPRODUCIBILITY.md`, a 26-section narrative notebook skeleton, `CITATION.cff`. Tests: 2 migrated +
  1 new event-agnostic grep-gate test, **13/13 passing** (verified independently in a fresh venv, not just
  the migration agent's self-report).
- **Uncommitted, in the working tree right now** (review before committing):
  - `src/floodstate_eo/_kakhovka_legacy_config.py` — a real bug fix. `load_utm('reservoir_full_pool_prebreach')`
    was silently returning an area of 2.6e-7 km² instead of ~2000 km², because the reservoir source file
    (`Kakhovka_SA_2.geojson`, CRS84/lon-lat) was being treated as already-EPSG:32636 like the zone file is.
    Fixed with CRS detection + reprojection; verified the corrected area (2174.7 km²) matches the real
    Kakhovka reservoir full-pool extent. Found by actually testing data access, not by inspection — worth
    remembering as a reason to keep testing data access, not just import success.
  - `case_studies/kakhovka_2023/manifests/{s1_scenes,s2_scenes,external}.csv` and `data/README.md` — the
    data-source registry `08_DATA_POLICY.md` called for but the code migration never produced. Built from
    real SWOT-DNIPRO tables (30 S1 SLC rows from `p80_c1_frozen_products.csv`, sha256 `TBD` — never computed
    anywhere; 44 S2 rows from `p52d_fetch_ledger*.csv` with real sha256/sizes). Found and corrected the
    pre-migration draft's dataset list along the way: Dynamic World and HAND are **not** used anywhere in
    `src/floodstate_eo/**` (dropped); ESA WorldCover 2021 turned out to be a **required, load-bearing**
    input (`surface_state/p69a_base_class.py:84`), not optional context as the draft assumed.
  - `provenance/UNRESOLVED_DEPENDENCIES.md` — two new entries (#7, #8): a whole S1 GRD/RTC NPZ-cache input
    that `sar/p71_s1_event_change.py` reads has no fetch code anywhere in this repo (the code that built it,
    `p0o`/`p0v`/`p0w`, was legacy and never migrated); FABDEM's licence (CC BY-NC-SA) may conflict with
    redistributing anything derived from it.

  **First thing to do next session**: review these three diffs, then commit them (they're good — reviewed
  once already this session — but the review was mine, not yet a second pair of eyes) and decide on `git push`.

## What Phase 5 did NOT do (by design — read before assuming code works end-to-end)

`tests/test_event_agnostic_gate.py::KNOWN_EXCEPTIONS` lists 23 files under `src/floodstate_eo/**` that are
still Kakhovka-specific — the 20 migrated scripts plus `canonical_grid.py`, `optical_catalogue.py`, and the
new `_kakhovka_legacy_config.py` shim. That shim exists **only** because Phase 6 ("replace hard-coding with
config") hasn't run: every migrated script still calls `CFG.TABLES`, `CFG.BULK_ROOT`, `CFG.BREACH_DATE`, etc.
instead of reading the YAMLs in `case_studies/kakhovka_2023/config/`. Until Phase 6 runs, this package is a
relocated copy of SWOT-DNIPRO's Kakhovka branch with clean provenance — not yet a reusable, event-agnostic
framework. That's the honest state; `provenance/KNOWN_GATE_EXCEPTIONS.md` explains each file.

Two unreconciled flood-state "bridges" exist and neither is canonical: the legacy `p51_rf_flood_optical.py`
RF classifier (20 m zone grid — deliberately **not migrated**, still only in SWOT-DNIPRO) and the newer
`fusion/p65b_m2_spatial_cv.py` → `fusion/p66_production_m2.py` / `fusion/p67b_production_candidate.py` M2
chain feeding `surface_state/p69a_base_class.py` → `fusion/p69b_event_association.py` (migrated, on the
canonical 10 m B1/B2/B3 frames, but `p66_production_m2.py` and `p67b_production_candidate.py` are
themselves two different fits of the same model, not reconciled to one canonical M2 output — see
`docs/DATA_DICTIONARY.md` row for `cand_score.tif`/`flood_score.tif`). Migrating the code did not resolve
which bridge is real; that's a science decision, not a file-organisation one.

M0–M5 (the flood-state class matrix referenced in `03_SCIENTIFIC_CORE.md`) is **not defined anywhere** —
still only mentioned as future work. No script here computes FLOOD_STATE, URBAN_SCORE, UNCERTAINTY, or
FINAL_FLOOD_MASK; `docs/DATA_DICTIONARY.md` marks all four `PROPOSED / NOT YET CANONICAL`.

The SWOT-DNIPRO source of `sar/p82_coherence_graph.py` (identical code here) is currently **blocked**: two
attempts at orbit 65 pair 1 both failed with `Java heap space` inside SNAP's ESD/Back-Geocoding stage, even
after retuning `-q`/`-c`/`-x`. Root cause traced to WSL2 capping this host's VM at ~15 GB against the
Windows host's ~32 GB (no `.wslconfig` override). Whoever runs this script from floodstate-eo will hit the
identical failure until that's fixed — raising the WSL2 memory cap (`.wslconfig`, `memory=24GB`+, then
`wsl --shutdown`) is the real fix, not a code change. 0 of the 4 orbits' coherence pairs have a valid output;
only orbit 65's SLC data has even been fetched.

## Ordered next steps (migration phases from the original audit, `07_MIGRATION_PLAN.md`)

1. **Now**: review + commit the three pending diffs above (CRS fix, data registry, unresolved-deps update).
2. **Phase 6 — replace hard-coding with config.** Rewire the 20 migrated scripts to read
   `case_studies/kakhovka_2023/config/*.yaml` instead of `_kakhovka_legacy_config.CFG`, one script at a
   time; `KNOWN_EXCEPTIONS` in the gate test shrinks as each one is done (that shrinkage is the acceptance
   criterion — don't remove an entry without actually fixing the file, the companion test
   `test_known_exceptions_still_exist_and_still_violate` will catch that). Also resolve: the two RNG seeds
   (`model.yaml`'s `seed_note`), the three temporal-window variants, and vendor or fetch the zone/reservoir
   geometries properly instead of reading them from sibling-repo paths (`provenance/UNRESOLVED_DEPENDENCIES.md` #3).
3. **Reconcile the two flood-state bridges** (p51 legacy vs. M2) — a science decision, likely needs
   `outputs/planning/19_P51_METHODOLOGY_REWRITE.md`'s open items resolved first (in SWOT-DNIPRO, since p51
   itself stayed there). This blocks Phase 9.
4. ~~Unblock the S1 coherence chain~~ — **CLOSED 2026-09-23** (see the update at the top): coherence is an
   optional later ablation, not on the critical path.
5. **Phase 7 — tests.** Currently only unit-level (`test_composites.py`) + the gate test. No integration or
   regression tests exist yet (`docs/DATA_DICTIONARY.md`'s testing-strategy note).
6. **Phase 8/9 — minimal case, then canonical B1/B2/B3 reproduction.** Actually run the pipeline end-to-end
   from this repo on real data and confirm outputs match SWOT-DNIPRO's (the invariants in
   `provenance/` / the original audit's `17_MIGRATION_INVARIANTS.md`).
7. **Phase 10/11 — fill in the notebook and docs** with real results once Phase 9 produces them (right now
   the notebook's later sections are placeholder markdown cells by design).
8. **Phase 12-15** (publication bundle, Zenodo metadata, GeoHydroAI integration, public release) — not
   started, don't start before 6-9 are done.
9. **`git push`** — only once the maintainer has reviewed at least the Phase-5 commit and decided the repo
   is ready to be visible on GitHub (currently local-only).
