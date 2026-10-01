# Validation record — Stage 3 closure, the text pass, the drawdown maps and the alignment with Paper 1 v6 (2026-09-29/30)

Branch `review-2026-09-28-stage3`. Every number below was read from a table or a log of this pass; the manuscript takes its numbers
from the regenerated tables through placeholders (0 unresolved is part of the check).

## 1. The drawdown maps (maintainer's check, 2026-09-30: "no drawdown on the maps")

Diagnostic of the p95f model against the Sentinel-2 crosscheck water on the cells Sentinel-2 observed (p95h, T23):

| S2 date | observed | where (chainage) | S2 water | model wet there | IoU | model wet, S2 dry |
|---|---|---|---|---|---|---|
| 8 June | 803 km² (37 %) | 109–181 km (broad middle) | 709 km² | 772 km² | 0.90 | 69 km² |
| 13 June | 371 km² (17 %) | 106–164 km | 288 km² | 321 km² | 0.85 | 43 km² |
| 20 June | whole pool | — | 648 km² | (model ends 13 June: 1789 km²) | — | — |

Verdict: the first week lowered the pool mostly in depth (mean depth 8.8 → 2.3 m, volume 18.8 → 4.2 km³, area 2132 → 1789 km²);
Sentinel-2 confirms that where it could see; the area collapsed between ~15 and 20 June (Sentinel-2: 648 km² of water on 20 June),
after the level records end. The Sentinel-1 VH dark surface is water or wet mud (2077 km² "dark" on 21 June) and cannot show the
exposure. Connectivity of the model water changes < 5 km² (tested). New Fig11 from Sentinel-2 + the observation-constrained day of
exposure (T23b: 317 km² dry by 13 June under the model, a further 1165 km² by 20 June, 646 km² still water on 20 June); model extent
and Sentinel-1 → FigS08.

Model defects found and fixed (p95f): the Nikopol level held over 12–13 June above the post's own censored upper bound (9.17 m on
13 June) — capped, 12–13 June flagged `surface_upper_bound`; G-REALM held over 10–11 June and, observed on 9 June, 0.5 m above the
Nikopol post 50 km upstream — no longer an anchor (the spurious release peak on 12 June disappears; 7 June unchanged).

## 2. Paper 1 v6 reproduced (D-PAPER1)

- Reservoir closures from the companion station table: tide-free −0.1730 m, production −0.1354 m (Paper 1: −0.173 / −0.135).
- Pool outlet in the production chain (+0.0734 m on the p61 values): 17.605 m on 31 May, 5.707 m on 13 June (Paper 1: 17.61, 5.71).
- Kherson gauge: +0.2076 m at the post's own coordinates (Paper 1's gauge parquet: identical on all 47 days); the extracted table had
  +0.22 m (+1.24 cm). Mykolaiv: identical to Paper 1's sea-yearbook series (EPSG:9902 step 0.1997 m), no change needed.
- The downstream SWOT chain (`wse + geoid_hght − ζ`, c = 0) was already Paper 1's.
- Paper 2's chain (p56 FABDEM, p57 ICESat-2 ground) pairs + free2mean with the tide-free closure: both 3.77 cm below Paper 1's frame;
  Paper 3 raises them (`paper1_frame.py`), residuals unchanged; note for SWOT-DNIPRO in `docs/NOTE_PAPER2_VERTICAL_CHAIN_2026-09-30.md`.

## 3. Recompute rev 7 (nominal runs, Dnipro corridor)

| date | A_new rev 6 → rev 7 | W_total rev 6 → rev 7 | V_new rev 6 → rev 7 |
|---|---|---|---|
| 5 June | 0 → 0 | 501.3 → 485.2 | 0 → 0 |
| 7 June | 243.2 → 245.1 | 796.6 → 787.4 | 514.5 → 519.8 |
| 9 June | 187.9 → 190.6 | 740.4 → 732.0 | 446.5 → 456.5 |
| 13 June | 107.7 → 110.9 | 640.4 → 633.1 | 157.9 → 163.8 |

The terrain is 3.8 cm higher against the water surface: less total water, the pre-breach regime shrinks more than the event water,
so the new area grows slightly. T11h keeps rev 6 as its own attribution step.

**Bug found in the recompute:** the p95e chunk cache was keyed by the draw number only; a rerun after an input change resumed from
the 1001 draws of the previous inputs (13 s instead of ~85 min). The cache is now valid only under an input fingerprint (parameters,
reconstruction code, frame module, input tables) and is cleared otherwise; the ensemble was then recomputed from scratch.

## 4. Monte-Carlo ensemble rev 7 (1000 coherent worlds; recomputed from scratch after the cache fix)

Dnipro corridor, Monte-Carlo median [p05–p95], rev 6 next to rev 7:

| quantity | rev 6 | rev 7 |
|---|---|---|
| A_new 7 June | 262.4 [250.3–277.8] km² | 264.3 [251.7–279.7] km² |
| W_total 7 June | 791.2 [767.3–819.4] km² | 785.0 [760.3–812.9] km² |
| V_new 7 June | 626.8 [585.0–674.0] hm³ | 634.6 [590.9–683.1] hm³ |
| W_total 5 June (pre-breach regime) | 472.7 km² | 463.7 [435.5–489.5] km² |
| day of the areal maximum | 7 June 77 %, 8 June 23 % | 7 June 76.5 %, 8 June 23.5 % |
| relative half-width over the median, A / V (7 June) | — (6 % / 9 % over the nominal) | 5.3 % / 7.3 % |

- Gate: world 0 reproduces the nominal p95 run on 276 / 276 zone–region–day rows (≤ 0.05 km², ≤ 0.005 hm³, the rounding of the
  tables); no world has new area before the breach.
- Convergence at n = 1000, seeds 20260929 / 20261001, 7 June: A_new p05/p50/p95 251.7/264.3/279.7 vs 250.8/264.9/282.2 km²;
  W_total 760.3/785.0/812.9 vs 761.2/784.6/813.6 km²; V_new p50 634.6 vs 636.7 hm³.
- Ablation (250 worlds per variant, 7 June): terrain only 269.1 km², water surface only 241.1 km², regime held at the nominal
  250.4 km²; the rebuilt regime with the terrain alone perturbed 767.7 km² against 801.0 km² at the nominal (rev 6: 775.2 vs 810.5).
- Support (nominal world, 7 June): 24.8 % of the corridor's new area weak (> 10 km), supported core 184.3 km² of 245.1 km², the
  10 km cap run 183.1 km²; Inhulets 92.8 % weak, 11.3 km² cross-river.
- The withheld gauges are unchanged in substance (Kalynivske: +9.50 m on 6 June, maximum 3 days early; Mykolaiv −0.82 m on 8 June).

## 5. Publication layer

- 69 tables (T28: 46 rows, every placeholder resolved in the same build); the manuscript: 324 placeholders, 0 unresolved; the
  claims register: no unresolved field; tests: 119 passed (13 new: the Paper 1 frame, T28, the fill, T07s, the production text).

