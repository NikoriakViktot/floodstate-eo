# New in floodstate-eo, 2026-09-29 (maintainer decision D-DEPTH). STATUS: ACTIVE. Reads the p95f model; changes nothing upstream.
"""P95m -- water depth in the Kakhovka pool: the full pool before the breach and the drawdown, from the same model as p95f/p95h.

Depth = the p95f sloped daily water surface (levels of the day interpolated along the SWORD chainage) minus the 50 m seamless
terrain-bed model, on the cells below that surface inside the pre-breach pool polygon -- exactly the wet mask of p95h (FigS08, model extent
a-c) and the volume of p95f (T21). Dates: 5 June (full pool, the day before the breach) and 7, 9 and 13 June (drawdown).
Consistency: the depth integrated over the wet cells reproduces p95f's V_pool_km3 of the date (asserted to 1e-3 km3).
It is the geometry of one surface model (the pool was not level during the drawdown; a range of design volumes for the same
days is in T27b), with the bed of the seamless model inside the pool (Paper 2) -- terrain_reconstructed, not observed depth.

Outputs: $BULK/reservoir_maps/model/depth_<date>.tif (float32 m, nodata -9999), <case_study>/tables/p95m_reservoir_depth.csv
         (per date: wet area, volume, mean / median / p95 / max depth, and the p95f volume it reproduces)
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
DATES = ("2023-06-05", "2023-06-07", "2023-06-09", "2023-06-13")
OUT = CFG.BULK_ROOT / "reservoir_maps" / "model"


def _ld(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def main():
    F = _ld("p95f_reservoir_balance")
    daily, extra, fixed = F.load_levels()
    dem, mask, tr, crs, xs, ys = F.load_pool()
    chain = F.chainage_grid(xs, ys); cell_km2 = abs(tr.a * tr.e) / 1e6
    V = pd.read_csv(CFG.TABLES / "p95f_reservoir_daily.csv").set_index("date")
    OUT.mkdir(parents=True, exist_ok=True); rows = []
    for d in DATES:
        pts = F.day_points(pd.Timestamp(d), daily, extra, fixed)
        wse = F.sloped_wse(pts, chain); wet = mask & (dem < wse)
        depth = np.where(wet, wse - dem, np.nan).astype("f4")
        vol = float(np.nansum(depth)) * cell_km2 * 1e6 / 1e9
        v95f = float(V.loc[d, "V_pool_km3"])
        assert abs(vol - v95f) < 1e-3, (d, vol, v95f)                      # the same model as p95f
        prof = dict(driver="GTiff", height=dem.shape[0], width=dem.shape[1], count=1, dtype="float32", crs=crs, transform=tr, nodata=-9999.0, compress="deflate")
        with rasterio.open(OUT / f"depth_{d}.tif", "w", **prof) as o:
            o.write(np.where(np.isfinite(depth), depth, -9999.0).astype("f4"), 1)
            o.update_tags(producer="p95m_reservoir_depth.py", meaning="p95f sloped daily surface minus the 50 m seamless terrain-bed model, wet pool cells; terrain_reconstructed", date=d)
        dd = depth[np.isfinite(depth)]
        rows.append(dict(date=d, n_level_sources=len(pts), wet_km2=round(float(wet.sum()) * cell_km2, 1), volume_km3=round(vol, 3), V_pool_p95f_km3=v95f,
                         depth_mean_m=round(float(dd.mean()), 2), depth_median_m=round(float(np.median(dd)), 2), depth_p95_m=round(float(np.percentile(dd, 95)), 2),
                         depth_max_m=round(float(dd.max()), 2), share_wet_deeper_than_5m=round(float((dd > 5).mean()), 3),
                         surface_outlet_m=round(float(pts[0][1]), 2), surface_upstream_m=round(float(pts[-1][1]), 2)))
        print(rows[-1], flush=True)
    D = pd.DataFrame(rows); D["semantics"] = "terrain_reconstructed (p95f surface over the seamless model); not observed depth"
    D.to_csv(CFG.TABLES / "p95m_reservoir_depth.csv", index=False); print(f"-> {OUT}/depth_<date>.tif, tables/p95m_reservoir_depth.csv")


if __name__ == "__main__":
    main()
