# p73 RF20 — QA verdict: PASS with documented limitations → P73_RF20_FROZEN (2026-09-23)

Producing commit `5f875ce` (clean worktree, `dirty_tracked: false`); model sha256 in `../p73_rf20_manifest.json`.

## Reproducibility gate — PASS
The clean-worktree runs at `dd8c096` and `5f875ce` reproduce the development result (produced on a dirty tree at
`a875e99`) **bit for bit** — class and max-score rasters, both frames, 0 differing cells. p73 does not depend on the
uncommitted `_kakhovka_legacy_config.py` CRS fix / manifests / UNRESOLVED_DEPENDENCIES diffs.

## Statistical QA (evaluation against WorldCover 2021, itself a weak reference — not ground truth)
| | CROPLAND F1 | WETLAND_REED F1 | BUILT_UP F1 | BARE_SAND F1 | WATER F1 | OA |
|---|---|---|---|---|---|---|
| 5-fold 5 km spatial-block CV | 0.924 | 0.953 | 0.938 | 0.979 | 0.998 | 0.940 |
| transfer B1 → B2 | 0.901 | 0.946 | 0.923 | 0.780 (n=2 420) | 0.999 | 0.923 |
| transfer B2 → B1 | 0.895 | 0.949 | 0.942 | 0.993 | 0.998 | 0.933 |

Wall-to-wall agreement on 4-cell-pure WorldCover (every pure cell, not a balanced sample): CROPLAND recall 0.93/0.91,
precision 0.99/0.99 (B1/B2); WETLAND_REED 0.93/0.93, 0.92/0.95; WATER recall 0.86/0.94; BUILT_UP precision
0.82/0.84; BARE_SAND precision 0.40/0.05 (see limitation 2). UNCERTAIN: 353 km² (5.8 %) B1, 169 km² (5.9 %) B2,
18 % of cells whose WorldCover 2×2 is mixed vs 3–9 % of pure cells — i.e. at class boundaries.

## Visual QA — six data-chosen zones (`Z*.png`) + frame maps (`B*_classes_vs_worldcover.png`)
- A. B1 fields with S1-disputed "water": contiguous CROPLAND, villages BUILT_UP, field edges/roads UNCERTAIN — PASS.
- B. B1 flooded fields (meander floodplain): CROPLAND vs floodplain GRASS separated; narrow channel not WATER — PASS*.
- C. B2 delta: contiguous WETLAND_REED, lakes WATER, high confidence — PASS.
- D. Oleshky sands: coherent BARE_SAND with GRASS in hollows, pine plantation FOREST — PASS (physically meaningful
  where WorldCover itself is speckled bare/grass).
- E. Kherson: BUILT_UP city, Dnipro WATER, islands WETLAND_REED — PASS.
- F. Coast: sea WATER, coastal reed WETLAND_REED, fields CROPLAND — PASS.

## The product this step exists for — old VEGETATION_AGRICULTURE decomposed (tables/p73_rf20_baseclass_crosswalk.csv)
| p73 class | B1 km² | B1 % | B2 km² | B2 % |
|---|---|---|---|---|
| CROPLAND | 3291.7 | 63.7 | 1471.8 | 65.1 |
| GRASS_LOW_VEGETATION | 997.6 | 19.3 | 453.3 | 20.1 |
| FOREST | 516.1 | 10.0 | 164.9 | 7.3 |
| SHRUB | 0 | 0 | 0 | 0 |
| WETLAND_REED | 18.4 | 0.4 | 8.1 | 0.4 |
| UNCERTAIN | 269.0 | 5.2 | 126.5 | 5.6 |
| other (built, bare, water) | 72.8 | 1.4 | 35.6 | 1.6 |

## Documented limitations (binding for every use of p73)
1. **Narrow rivers are not WATER at 20 m** (mixed pixels): WATER recall vs WorldCover 0.86 in B1; channels < ~40 m
   come out UNCERTAIN/WETLAND_REED. Pre-existing water for U-Net context should not rely on p73 alone for small channels.
2. **BARE_SAND "precision vs WorldCover" is not a valid error measure here**: WorldCover's bare/grass is speckled in
   the sand massifs, so few pure bare cells exist; p73 maps the massifs coherently. Treat BARE_SAND as p73's own claim.
3. **SHRUB and OTHER are never predicted** — no training targets in either frame (WorldCover has none pure here).
4. **BUILT_UP slightly over-called** for small settlements/roads relative to WorldCover (precision 0.82/0.84).
5. **Cross-frame agreement 1.0 on the 1 471 km² overlap is not an independent stability test**: both frames' composites
   are cut from the same per-date stacks, so the overlap features are identical.
6. **CV/transfer numbers are optimistic by construction**: balanced samples of PURE cells against a weak reference.
7. UNCERTAIN definition (top probability < 0.5) is frozen; it must not be changed after inspecting flood results.

## Use rule
p73 is FROZEN as an independent PRE-event surface product. It may enter a U-Net only as INPUT context in the U1
ablation, after the B1+B2 split is frozen; it never enters label construction (enforced by p77's guard).
B3: pure inference only (`p73_rf20_surface.py --infer B3`), no training/tuning/selection on B3.
