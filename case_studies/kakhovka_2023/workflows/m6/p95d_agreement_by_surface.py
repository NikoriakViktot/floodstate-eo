# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Disagreement ontology terrain x S1 by surface class and elevation.
"""P95d -- the disagreement ontology of the paper (claim C03), as a committed table instead of diagnostic stdout.

For an S1 acquisition date (default 2023-06-09; also 06-13, 06-14) and the p95 connected_ceiling reconstruction:
    A  terrain+ / S1+      both call new water
    B  terrain+ / S1-      terrain allows, the dark-water rule does not see it  (SAR blind spots? drained? DEM?)
    C  terrain- / S1+      S1 dark water where the reconstruction has no new water
    N  neither             observed by S1 on that date, dry in both
each decomposed by ESA WorldCover 2021 class, by the frozen p73 RF20 class, and by the ground elevation relative to the
reconstructed water surface (bins < 0, 0-2, 2-5, >= 5 m). "Normally wet" (model-only part of the pre-breach baseline) is kept
as its own flag so that C splits into reed submergence (ground below or within 2 m of the surface) and false SAR water on
land (ground >= 5 m above). Everything is inside the S1 valid footprint of the date, the owned zone area and outside the p42
cut rectangles (corridor), one 20 m cell once (ZONE_2 owns the overlap).

Reads (bulk): p95 rev-4 daily_new.npz + the WSE of the date from the same node-based engine (p95.load_engine),
seamless DEM, S1 zone caches, WorldCover frames, p73 classes; the same-rule pre-breach baseline is rebuilt from the table.
RF20 classes: rev 2 (review F08 refit: global blocks, overlap owned by B2; `--p73-rev 1` = the superseded rev-1 products).
Outputs: <case_study>/tables/p95d_agreement_<date>.csv (zone x category x worldcover x p73 x elev_bin x normally_wet x km2)
         <case_study>/tables/p95d_agreement_<date>_summary.csv (zone x category x km2 + the paper's headline splits)
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio.warp import reproject, Resampling
from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
WC = {10: "trees", 20: "shrub", 30: "grass", 40: "cropland", 50: "built", 60: "bare", 70: "snow", 80: "water", 90: "wetland",
      95: "mangrove", 100: "moss"}
P73 = {1: "WATER", 2: "CROPLAND", 3: "GRASS_LOW_VEGETATION", 4: "FOREST", 5: "SHRUB", 6: "WETLAND_REED", 7: "BUILT_UP",
       8: "BARE_SAND", 9: "OTHER", 10: "UNCERTAIN", 255: "nodata"}
BINS = [(-99, 0, "below_surface"), (0, 2, "0-2m_above"), (2, 5, "2-5m_above"), (5, 999, ">=5m_above")]
CELL_KM2 = 0.0004


def _ld(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default="2023-06-09"); ap.add_argument("--rule", default="connected_ceiling")
    ap.add_argument("--p73-rev", type=int, default=2, choices=[1, 2], help="RF20 products: 2 = the F08 refit (default), 1 = superseded")
    a = ap.parse_args(); d = a.date; sub73 = "p73_rf20" if a.p73_rev == 1 else "p73_rf20_rev2"
    P95 = _ld("p95_hand_daily_inundation"); P = P95.load_p92()
    W, dxm, dym, _ = P95.load_engine()
    mp = CFG.TABLES / f"p95_manifest_{a.rule}.json"                   # rev 6: the rule suffix is always explicit
    margin = float(json.loads(mp.read_text())["constants"]["margin_m"])
    rows, summ = [], []
    for zone in P95.ZONES:
        L = P95.zone_layers(zone, P); G = L["G"]; Z = W.prepare(L)
        def wse_on(day, mg):
            return W.field(Z, day, mg)
        base = np.isfinite(L["dem"])
        # rev 6: new inundation AND the normally-wet class come from the p95 run itself (evaluated on the union mosaic), so the
        # decomposition uses exactly the reconstruction it describes -- no second, per-zone implementation of the rule (review F06)
        z = np.load(CFG.BULK_ROOT / "floodplain_dyn" / (zone + f"_{a.rule}") / "daily_new.npz")
        un = lambda k: np.unpackbits(z[k], count=G["ny"] * G["nx"]).reshape(G["ny"], G["nx"]).astype(bool)
        new, normally_wet = un(d), un("normally_wet")
        w = wse_on(d, margin); dz = L["dem"] - w
        v = L["V"][d] & L["own"] & ~L["cut"]; s1 = L["W"][d] & ~L["pre"] & v
        cat = np.full(base.shape, "", dtype="U1"); cat[v] = "N"; cat[v & new & ~s1] = "B"; cat[v & s1 & ~new] = "C"; cat[v & s1 & new] = "A"
        with rasterio.open(CFG.BULK_ROOT / "worldcover_frames" / zone / "wc_2021_20m.tif") as s:
            wc = np.full((G["ny"], G["nx"]), 0, "u1"); reproject(s.read(1), wc, src_transform=s.transform, src_crs=s.crs, dst_transform=G["transform"], dst_crs=G["crs"], resampling=Resampling.nearest)
        with rasterio.open(P.OUT / L["frame"] / sub73 / "surface_class_20m.tif") as s:
            p73 = np.full((G["ny"], G["nx"]), 255, "u1"); reproject(s.read(1), p73, src_transform=s.transform, src_crs=s.crs, dst_transform=G["transform"], dst_crs=G["crs"], resampling=Resampling.nearest)
        ebin = np.full(base.shape, "", dtype="U16")
        for lo, hi, nm in BINS:
            ebin[(dz >= lo) & (dz < hi)] = nm
        m = v
        df = pd.DataFrame(dict(category=cat[m], worldcover=[WC.get(int(k), str(k)) for k in wc[m]], p73=[P73.get(int(k), str(k)) for k in p73[m]],
                               elev_bin=ebin[m], normally_wet=normally_wet[m]))
        g = df.groupby(["category", "worldcover", "p73", "elev_bin", "normally_wet"]).size().reset_index(name="cells")
        g["km2"] = (g.cells * CELL_KM2).round(3); g.insert(0, "zone", zone); g.insert(1, "date", d); g["p73_rev"] = a.p73_rev; rows.append(g)
        for c in "ABCN":
            mc = cat == c
            summ.append(dict(zone=zone, date=d, category=c, km2=round(float(mc.sum()) * CELL_KM2, 2),
                             km2_ground_below_surface=round(float((mc & (dz < 0)).sum()) * CELL_KM2, 2),
                             km2_ground_0_2m_above=round(float((mc & (dz >= 0) & (dz < 2)).sum()) * CELL_KM2, 2),
                             km2_ground_2_5m_above=round(float((mc & (dz >= 2) & (dz < 5)).sum()) * CELL_KM2, 2),
                             km2_ground_ge5m_above=round(float((mc & (dz >= 5)).sum()) * CELL_KM2, 2),
                             km2_normally_wet=round(float((mc & normally_wet).sum()) * CELL_KM2, 2),
                             km2_wc_trees=round(float((mc & (wc == 10)).sum()) * CELL_KM2, 2), km2_wc_wetland=round(float((mc & (wc == 90)).sum()) * CELL_KM2, 2),
                             km2_wc_built=round(float((mc & (wc == 50)).sum()) * CELL_KM2, 2), km2_wc_cropland=round(float((mc & (wc == 40)).sum()) * CELL_KM2, 2),
                             km2_wc_grass=round(float((mc & (wc == 30)).sum()) * CELL_KM2, 2), km2_wc_bare=round(float((mc & (wc == 60)).sum()) * CELL_KM2, 2),
                             km2_p73_reed=round(float((mc & (p73 == 6)).sum()) * CELL_KM2, 2), km2_p73_forest=round(float((mc & (p73 == 4)).sum()) * CELL_KM2, 2),
                             km2_p73_built=round(float((mc & (p73 == 7)).sum()) * CELL_KM2, 2), km2_p73_cropland=round(float((mc & (p73 == 2)).sum()) * CELL_KM2, 2),
                             p73_rev=a.p73_rev))
        print(zone, {c: round(float((cat == c).sum()) * CELL_KM2, 1) for c in "ABC"}, flush=True)
    tag = d.replace("-", "")
    pd.concat(rows, ignore_index=True).to_csv(CFG.TABLES / f"p95d_agreement_{tag}.csv", index=False)
    S = pd.DataFrame(summ); S.to_csv(CFG.TABLES / f"p95d_agreement_{tag}_summary.csv", index=False)
    pd.set_option("display.width", 250); print(S.to_string(index=False)); print(f"-> tables/p95d_agreement_{tag}*.csv")


if __name__ == "__main__":
    main()
