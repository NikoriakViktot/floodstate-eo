# New in floodstate-eo, 2026-09-29 (review 2026-09-28, F09/F10). STATUS: ACTIVE. Compares label rasters; changes nothing.
"""P77g -- what the corrected M2 changed in the weak labels: pixel transitions v003_A -> v004 and v002 -> v002_notrace.

v004 applies the v003_A rule to the M2 without the post-event TRACE window and with the out-of-fold operating threshold
(docs/LABEL_CONTRACTS.md); v002_notrace is the v002 rule on the same M2. Any difference between the two versions of a pair
is caused by the M2 masks (flood_central / flood_possible) alone: the S1 inputs, the May reference state and W_pre are the
same. Per frame, band 1 of both rasters is cross-tabulated over every frame pixel (10 m; 1e-4 km2 each); the B1/B2 overlap is
counted in both frames, as in T02.

Outputs: <case_study>/tables/p77g_label_transitions.csv (pair, frame, from, to, km2, share_of_from)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import rasterio

from floodstate_eo import _kakhovka_legacy_config as CFG

OUT = CFG.BULK_ROOT / "frames10"
PX_KM2 = 1e-4
PAIRS = {"v003_A -> v004": ("m6_labels_v003_A.tif", "m6_labels_v004.tif", {0: "LAND", 1: "EVENT_FLOOD", 2: "REFERENCE_WATER", 255: "UNKNOWN"}),
         "v002 -> v002_notrace": ("m6_labels_v002.tif", "m6_labels_v002_notrace.tif", {0: "NON_FLOOD", 1: "FLOOD", 255: "IGNORE"})}


def transitions(a, b, names):
    """Cross-tabulation of two label bands as (from, to, pixels) rows, every code pair that occurs."""
    k = a.astype(np.int64) * 256 + b.astype(np.int64); u, n = np.unique(k, return_counts=True)
    return [(names.get(int(x // 256), int(x // 256)), names.get(int(x % 256), int(x % 256)), int(c)) for x, c in zip(u, n)]


def main():
    rows = []
    for pair, (fa, fb, names) in PAIRS.items():
        for fid in ("B1", "B2"):
            pa, pb = OUT / fid / fa, OUT / fid / fb
            if not (pa.exists() and pb.exists()):
                print("missing", pa if not pa.exists() else pb); continue
            with rasterio.open(pa) as s:
                a = s.read(1)
            with rasterio.open(pb) as s:
                b = s.read(1)
            assert a.shape == b.shape, (fid, a.shape, b.shape)
            for f, t, n in transitions(a, b, names):
                rows.append(dict(pair=pair, frame=fid, **{"from": f, "to": t}, km2=round(n * PX_KM2, 3)))
    D = pd.DataFrame(rows)
    D["share_of_from"] = (D.km2 / D.groupby(["pair", "frame", "from"]).km2.transform("sum")).round(4)
    D.to_csv(CFG.TABLES / "p77g_label_transitions.csv", index=False)
    pd.set_option("display.width", 200); print(D[D["from"] != D["to"]].to_string(index=False))
    print("-> tables/p77g_label_transitions.csv")


if __name__ == "__main__":
    main()
