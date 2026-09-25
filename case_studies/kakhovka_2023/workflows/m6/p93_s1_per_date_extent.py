# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Diagnostic: per-date S1 water extent on the B1 u B2 mosaic.
"""P93 -- why the M6 area is smaller than the published peak: per-acquisition-date S1 dark-water extent (p0v/p0w M3
per-scene masks, 20 m -> mosaic by nearest), split into water that already existed before the breach (S1 water on
2023-06-01/02 OR p60 pre_water_frac >= 20 %) and NEW water, for the Dnipro corridor (outside p42 CUT_RECTS), the p42
terrain-eligible floodplain and the Inhulets rectangle. Also the label recipe (>= 2 of the 3 peak dates 06-09/13/14),
the single peak scene 06-09 and the M6 prediction, side by side.

The m6 labels are a PERSISTENCE product (water on >= 2 of 06-09 / 06-13 / 06-14), so an arm trained on them maps water
that was still standing on 13-14 June, not the 6-9 June peak. Published peak figures (UNOSAT ~620 km2 for 6-9 June;
~180 km2 by 13 June) are single-date extents with their own reference-water definition and cover the delta and the
liman coast (frame B3, not built here) as well.

Output: <case_study>/tables/p93_s1_per_date_extent.csv, p93_peak_vs_label_vs_model.csv
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np, pandas as pd
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
ZONE = {"B1": "ZONE_4_FLOODWAY_june2023_s32", "B2": "ZONE_2_KHERSON_DELTA_flood_june2023"}
DATES = ["2023-06-01", "2023-06-02", "2023-06-06", "2023-06-09", "2023-06-13", "2023-06-14", "2023-06-18",
         "2023-06-21", "2023-06-25", "2023-06-30"]
PEAK = ("2023-06-09", "2023-06-13", "2023-06-14")
PX = 1e-4


def main():
    s = importlib.util.spec_from_file_location("p92", HERE / "p92_flood_area_dam_to_liman.py")
    P = importlib.util.module_from_spec(s); s.loader.exec_module(P)
    M = P.mosaic_grid(); L = P.load_layers(M)
    cut = np.zeros((M["ny"], M["nx"]), bool)
    for r in P.CUT_RECTS.values():
        cut |= P.rect_mask(M, r)
    fp, _ = P.floodplain_domain(M)
    trM = from_origin(M["x0"], M["y1"], 10.0, 10.0)

    def to_mosaic(a, tr):
        d = np.zeros((M["ny"], M["nx"]), "u1")
        reproject(a.astype("u1"), d, src_transform=tr, src_crs="EPSG:32636", dst_transform=trM, dst_crs="EPSG:32636",
                  resampling=Resampling.nearest)
        return d.astype(bool)
    W = {d: np.zeros((M["ny"], M["nx"]), bool) for d in DATES}; V = {d: np.zeros((M["ny"], M["nx"]), bool) for d in DATES}
    for f in ("B2", "B1"):
        z = np.load(CFG.S1_CACHE / ZONE[f] / "per_scene_water.npz", allow_pickle=True); shp = tuple(int(v) for v in z["shape"])
        tr = from_origin(float(z["x0"]), float(z["y1"]), float(z["cell"]), float(z["cell"]))
        un = lambda k: np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
        for k in z.files:
            if k[:10] in DATES and not k.startswith("valid"):
                w, v = un(k), un("valid_" + k); d = k[:10]
                W[d] |= to_mosaic(w & v, tr); V[d] |= to_mosaic(v, tr)
    pre = L["pre"] | W["2023-06-01"] | W["2023-06-02"]
    own = L["owned"]
    reg = {"DNIPRO_CORRIDOR": own & ~cut, "INHULETS_VALLEY_rect": own & P.rect_mask(M, P.CUT_RECTS["inhulets_valley"])}
    if fp is not None:
        reg["P42_FLOODPLAIN_DOMAIN"] = own & fp
    rows = []
    for d in DATES:
        for nm, m in reg.items():
            rows.append(dict(date=d, region=nm, valid_km2=round(float((V[d] & m).sum()) * PX, 1),
                             s1_water_km2=round(float((W[d] & m).sum()) * PX, 1),
                             new_water_not_pre_breach_km2=round(float((W[d] & m & ~pre).sum()) * PX, 1)))
    T = CFG.TABLES
    pd.DataFrame(rows).to_csv(T / "p93_s1_per_date_extent.csv", index=False)
    two = sum(W[d].astype(int) for d in PEAK) >= 2; anyp = W[PEAK[0]] | W[PEAK[1]] | W[PEAK[2]]
    env = W["2023-06-06"] | anyp | W["2023-06-18"]
    pred, thr = P.load_pred(M, "U2b_B1B2_v003A")
    cmp_ = []
    for nm, m in reg.items():
        a = lambda x: round(float((x & m).sum()) * PX, 1)
        cmp_.append(dict(region=nm, pre_breach_water_km2=a(pre), peak_0609_total_water_km2=a(W["2023-06-09"]),
                         peak_0609_new_water_km2=a(W["2023-06-09"] & ~pre), label_recipe_2of3_new_km2=a(two & ~pre),
                         any_of_3_peak_new_km2=a(anyp & ~pre), union_0606_0618_new_km2=a(env & ~pre),
                         U2b_predicted_km2=a(pred & L["has"]), U2b_threshold=thr,
                         U2b_pred_or_peak_0609_water_km2=a(pred | W["2023-06-09"])))
    C = pd.DataFrame(cmp_); C.to_csv(T / "p93_peak_vs_label_vs_model.csv", index=False)
    pd.set_option("display.width", 250); print(C.to_string(index=False)); print("-> tables/p93_*.csv")


if __name__ == "__main__":
    main()
