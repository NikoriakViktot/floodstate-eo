# p73 RF20 rev 2 — QA verdict: PASS → P73_RF20_REV2_FROZEN (2026-09-29; clean-tree reproducibility gate PASS)

Rev 2 answers review F08 (2026-09-28): 5 km blocks from the UTM coordinates of the 20 m cells (one physical cell, one block,
in both frames); B2 owns the B1/B2 overlap and B1 contributes no target there (3 093 025 B1 target cells dropped), so a
physical cell enters the sample once (asserted); the CV is reported without and with a 3.5 km buffer around the test blocks;
the frame transfers train and test outside the overlap only. Rev 1 (`../p73_rf20_qa/`, frozen 2026-09-23) is superseded.

Run: `p73_rf20_surface.py --rev 2 --jobs 12` on 2026-09-29 (15 min, 9.6 GB peak); the p73 code and every module it imports
are identical to commit 214bf93 (the working tree had uncommitted edits in other files); model sha256 in
`../p73_rf20_rev2_manifest.json`.

## Reproducibility gate — PASS
The clean-worktree re-run at `acf190c` (`dirty_tracked: false`, 14 min, 10.2 GB) reproduces all eight rev-2 product rasters
(class, max score, uncertain and scores; B1 and B2) **bit for bit** (sha256 before = after), after the stage-2 U-Net arms had
been trained on them. The persisted model file is not byte-reproducible (joblib sha256 `fd6d48f0…` → `f8e55fdb…`, the manifest
records the current one); its predictions are, on every valid cell of both frames.

## Statistical QA (against WorldCover 2021, itself a weak reference; balanced samples of pure cells)
| evaluation | CROPLAND F1 | WETLAND_REED F1 | BUILT_UP F1 | BARE_SAND F1 | WATER F1 | macro F1 | OA |
|---|---|---|---|---|---|---|---|
| 5-fold 5 km block CV (rev 2) | 0.922 | 0.947 | 0.938 | 0.983 | 0.998 | 0.941 | 0.938 |
| same, 3.5 km buffer (rev 2; 32–49 % of the training cells kept per fold) | 0.907 | 0.935 | 0.925 | 0.972 | 0.996 | 0.929 | 0.926 |
| transfer B1 → B2, outside the overlap (rev 2) | 0.854 | 0.916 | 0.771 | 0.659 (n = 1 627) | 0.997 | 0.848 | 0.895 |
| transfer B2 → B1 (rev 2) | 0.862 | 0.921 | 0.920 | 0.984 | 0.997 | 0.907 | 0.909 |
| rev 1: block CV / B1 → B2 / B2 → B1 (superseded) | 0.924 / 0.901 / 0.895 | 0.953 / 0.946 / 0.949 | 0.938 / 0.923 / 0.942 | 0.979 / 0.780 / 0.993 | 0.998 / 0.999 / 0.998 | 0.943 / 0.904 / 0.932 | 0.940 / 0.923 / 0.933 |

The frame-local block ids of rev 1 changed the CV little (macro F1 0.943 → 0.941); the rev-1 **B1 → B2 transfer was inflated
by the overlap** (B2's test set contained the 1 471 km² that B1 had trained on): 0.904 → 0.848 outside the overlap.

Wall-to-wall agreement on 4-cell-pure WorldCover within ±0.02 of rev 1 for every class (e.g. CROPLAND recall 0.930/0.904,
WETLAND_REED 0.936/0.927, WATER 0.884/0.952, B1/B2). UNCERTAIN 344 km² (5.6 %) B1, 169 km² (5.9 %) B2. SHRUB and OTHER are
never predicted (as in rev 1), so the U1 one-hot encoding loses no class. Cross-frame agreement on the overlap 1.0 (identical
features by construction; not an independent stability test).

## Agreement with rev 1, cell by cell
96.95 % (B1) and 96.78 % (B2) of the valid cells keep their class; 99.63 % / 99.52 % outside UNCERTAIN in either revision;
the changes sit in the UNCERTAIN margin (75 % of rev-1 UNCERTAIN cells stay UNCERTAIN). Class areas change by ≤ 12.5 km² per
class and frame. The visual QA of rev 1 therefore carries over; the frame maps and the six zone panels are regenerated here
(`B*_classes_vs_worldcover.png`, `Z*.png`) for inspection. Downstream: the disagreement ontology (p95d, T14) moves by ≤ 4.7 km²
in any RF20-class split; its category areas do not depend on RF20.

## Limitations and use rule
Those of rev 1 hold unchanged (narrow rivers not WATER at 20 m; BARE_SAND precision vs WorldCover not a valid error measure;
SHRUB/OTHER never predicted; BUILT_UP slightly over-called; CV numbers optimistic by construction; UNCERTAIN rule frozen).
Rev 2 is the RF20 of every stage-2 product (U1 input and evaluation strata of the v004 arms, p95d, T09/T10, dashboard); it
never enters label construction (p77 guard). B3: pure inference only.
