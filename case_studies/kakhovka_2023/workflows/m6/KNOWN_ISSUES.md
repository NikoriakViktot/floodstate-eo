# Known issues in migrated M6 code (found after migration; source logic left unchanged until a decision)

## p72_s2_sparse_event_support.py — every d* band of s2_sparse_support.tif is invalid (found 2026-09-24, p89)
`d = vals[i] - pre[i]`: `vals` is divided by SCALE (index units) but `pre` (composite `*_pre_med`) is not
(still x10000). The difference is therefore ~ -pre_raw and saturates at +-32767 after `* SCALE` and clipping —
all 10 d* bands (dNDVI, dNDWI, dMNDWI, dNDMI, dBSI for 06-08 and 06-18) carry the saturated sign of the PRE index,
not a change. The absolute bands (NDVI_0608 ... BSI_0618) and valid_* are correct.
Impact: any use of d* (planned U3/U4 inputs) is invalid until p72 is fixed and s2_sparse_support.tif rebuilt.
Workaround used by p89: change = absolute event band / 1e4 - composite PRE median / 1e4.

## p76_u0b_b2_baseclass.py — undefined name `lk` at the config dump (F821)
CONTAMINATED script, not to be re-run; recorded for completeness.
