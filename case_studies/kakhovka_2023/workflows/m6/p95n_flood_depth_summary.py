# New in floodstate-eo, 2026-09-29 (maintainer decision D-DEPTH). STATUS: ACTIVE. Summarises p95 rasters; changes nothing.
"""P95n -- depth of the reconstructed new inundation below the dam: the event maximum and 8 June, per accounting region.

Reads the per-zone rasters of the primary run (connected_ceiling, nominal world): max_depth_m.tif (per cell, the largest depth
of new inundation over 26 May - 10 July) and depth_2023-06-08_m.tif; owned cells only (ZONE_2 owns the overlap) and the p95
accounting regions (p95l.zone_regions: Dnipro corridor, Inhulets rectangle, p42 floodplain domain). Depth = water surface minus
the seamless terrain-bed model on new-inundation cells. This is the geometry of one world (the nominal run, a diagnostic); the
areas and volumes quoted as results come from the Monte-Carlo ensemble (T12). Committed so that the paper layer needs no bulk data.

Outputs: <case_study>/tables/p95n_flood_depth_summary.csv
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
QUANT = {"max_depth_event": "max_depth_m.tif", "depth_2023-06-08": "depth_2023-06-08_m.tif"}


def _ld(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def main():
    L95l = _ld("p95l_support_domain"); P95 = L95l._ld("p95_hand_daily_inundation"); P = P95.load_p92()
    acc = {}
    for zn in P95.ZONES:
        d = P95.DYN / f"{zn}_connected_ceiling"
        with rasterio.open(d / QUANT["max_depth_event"]) as s:
            G = dict(transform=s.transform, crs=s.crs, ny=s.height, nx=s.width)
        R = L95l.zone_regions(P95, P, zn, G)
        for q, fn in QUANT.items():
            with rasterio.open(d / fn) as s:
                a = s.read(1).astype("f4"); nd = s.nodata
            if nd is not None:
                a[a == nd] = np.nan
            a[~(a > 0)] = np.nan
            for rn, m in R.items():
                acc.setdefault((q, rn), []).append(a[m & np.isfinite(a)])
    rows = []
    for (q, rn), parts in acc.items():
        v = np.concatenate(parts)
        if not len(v):
            continue
        vol = round(float(v.sum()) * P95.CELL_KM2 * 1e6 / 1e9, 3) if q.startswith("depth_") else np.nan   # per-cell maxima of different days are no volume
        rows.append(dict(quantity=q, region=rn, area_km2=round(len(v) * P95.CELL_KM2, 1), volume_km3=vol,
                         depth_mean_m=round(float(v.mean()), 2), depth_median_m=round(float(np.median(v)), 2), depth_p90_m=round(float(np.percentile(v, 90)), 2),
                         depth_p95_m=round(float(np.percentile(v, 95)), 2), depth_max_m=round(float(v.max()), 2),
                         share_gt_1m=round(float((v > 1).mean()), 3), share_gt_2m=round(float((v > 2).mean()), 3), share_gt_4m=round(float((v > 4).mean()), 3)))
    D = pd.DataFrame(rows).sort_values(["quantity", "region"])
    D["semantics"] = "terrain_reconstructed, nominal world (connected_ceiling); owned cells; results for areas / volumes: the ensemble (T12)"
    D.to_csv(CFG.TABLES / "p95n_flood_depth_summary.csv", index=False)
    pd.set_option("display.width", 250); print(D.drop(columns="semantics").to_string(index=False)); print("-> tables/p95n_flood_depth_summary.csv")


if __name__ == "__main__":
    main()
