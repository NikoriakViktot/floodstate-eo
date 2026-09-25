# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Independent check of the terrain-vs-S1 disagreement with ICESat-2.
"""P95c -- is "S1 sees water, terrain says the ground is above the water surface" a DEM error or false SAR water?

Two steps, because the ICESat-2 pull lives in SWOT-DNIPRO (parquet + its vertical chain, p57):
  --step rasters   (floodstate-eo venv)  per zone, for 2023-06-09: agreement category raster of the p95 connected_ceiling
                   reconstruction vs the S1 scene (1 observed-neither, 2 S1-only with ground < 2 m above the surface,
                   3 both, 4 terrain-only, 5 S1-only with ground >= 2 m above the surface) and the WSE raster.
  --step icesat    (SWOT-DNIPRO venv: `~/repo/SWOT-DNIPRO/.venv/bin/python p95c_icesat2_check.py --step icesat`)
                   night ATL08 ground segments (p57.load_points: solar_elevation < 0, >= 8 ground photons, EVRF2019) sampled
                   on those rasters: residual seamless DEM - ICESat-2, ICESat-2 ground minus the 06-09 water surface, share
                   of segments whose ground lies below the water surface; per category, and for category 5 also inside the
                   Oleshky left-bank box (x 462-476 km, y 5148-5166 km) by WorldCover class.
Verdict 2026-09-25 (tables/p95c_icesat2_check_0609.csv): in category 5 the DEM matches ICESat-2 to +-0.3 m (median
residual 0.02 m) and the ground lies 5.6 m (Oleshky grass) to 30 m (cropland) ABOVE the 06-09 water surface, 0 % of
segments below it -> that S1 water is false SAR water on land, not a DEM error. Categories 2-4: 90-100 % of segments
below the surface, as the reconstruction assumes.

Outputs: $BULK_ROOT/floodplain_dyn/_icesat_check/<ZONE>_{cat,wse}0609.tif, <case_study>/tables/p95c_icesat2_check_0609.csv
"""
from __future__ import annotations
import argparse, importlib.util, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATE = "2023-06-09"
CAT = {1: "observed_neither", 2: "S1_only_ground_lt2m_above", 3: "both", 4: "terrain_only", 5: "S1_only_ground_ge2m_above"}
OLESHKY_BOX = (462000.0, 5148000.0, 476000.0, 5166000.0)


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def rasters():
    import rasterio
    from rasterio.warp import transform as tf
    from scipy.spatial import cKDTree
    from floodstate_eo import _kakhovka_legacy_config as CFG
    P95 = _ld("p95", HERE / "p95_hand_daily_inundation.py"); P = P95.load_p92()
    out = CFG.BULK_ROOT / "floodplain_dyn" / "_icesat_check"; out.mkdir(parents=True, exist_ok=True)
    H = pd.read_csv(CFG.TABLES / "p95_wse_table.csv", index_col=0, parse_dates=True); H.columns = H.columns.astype(int); bins = np.array(H.columns)
    nodes = pd.read_csv(CFG.TABLES / "p59_swot_flood_nodes.csv")
    N = nodes.groupby("node_id").agg(x=("x", "median"), y=("y", "median"), s_km=("s_km", "median")).reset_index()
    tree = cKDTree(np.c_[N.x, N.y]); kx, ky = tf("EPSG:4326", CFG.CRS_METRIC, [P95.KHERSON_LONLAT[0]], [P95.KHERSON_LONLAT[1]])
    s_kh = float(N.s_km.values[tree.query([kx[0], ky[0]])[1]])
    kh = pd.read_csv(Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p59_swot_vs_kherson.csv", parse_dates=["date"]).set_index("date").H_gauge_evrf
    for zone in P95.ZONES:
        L = P95.zone_layers(zone, P); G = L["G"]
        YY, XX = np.meshgrid(L["ys"], L["xs"], indexing="ij"); dn, ii = tree.query(np.c_[XX.ravel(), YY.ravel()])
        dn = dn.reshape(G["ny"], G["nx"]); sb = np.clip(np.floor(N.s_km.values[ii]).astype(int), bins.min(), bins.max()).reshape(G["ny"], G["nx"])
        far = (dn > P95.SWOT_MAX_DIST_M) & (sb >= s_kh)
        w = H.loc[pd.Timestamp(DATE)].values.astype("f4")[np.searchsorted(bins, sb)] + P95.SWOT_MARGIN_M
        w = np.where(far, np.minimum(w, kh[pd.Timestamp(DATE)] + P95.SWOT_MARGIN_M), w).astype("f4")
        z = np.load(CFG.BULK_ROOT / "floodplain_dyn" / (zone + "_connected_ceiling") / "daily_new.npz")
        new = np.unpackbits(z[DATE], count=G["ny"] * G["nx"]).reshape(G["ny"], G["nx"]).astype(bool)
        v = L["V"][DATE] & L["own"] & ~L["cut"]; s1 = L["W"][DATE] & ~L["pre"] & v; dz = L["dem"] - w
        cat = np.zeros((G["ny"], G["nx"]), "u1"); cat[v] = 1; cat[new & ~s1] = 4; cat[s1 & new] = 3
        cat[s1 & ~new & (dz < 2)] = 2; cat[s1 & ~new & (dz >= 2)] = 5
        prof = dict(driver="GTiff", height=G["ny"], width=G["nx"], count=1, crs=G["crs"], transform=G["transform"], compress="deflate")
        with rasterio.open(out / f"{zone}_cat0609.tif", "w", dtype="uint8", nodata=0, **prof) as o:
            o.write(cat, 1); o.update_tags(categories=str(CAT), producer="p95c_icesat2_check.py")
        with rasterio.open(out / f"{zone}_wse0609.tif", "w", dtype="float32", nodata=-9999, **prof) as o:
            o.write(np.where(np.isfinite(w), w, -9999).astype("f4"), 1)
        print(zone, {CAT[k]: round(float((cat == k).sum()) * 4e-4, 1) for k in CAT}, flush=True)


def icesat():
    sd = Path.home() / "repo/SWOT-DNIPRO"; sys.path.insert(0, str(sd / "src")); sys.path.insert(0, str(sd / "scripts"))
    P57 = _ld("p57", sd / "scripts/p57_dem_accuracy_night.py")
    from swot_dnipro import config as SCFG
    P, c = P57.load_points(); P = P[~P.in_former_pool].copy(); print("night points", len(P), flush=True)
    B = SCFG.BULK_ROOT; out = B / "floodplain_dyn" / "_icesat_check"; rows = []
    for zone in ("ZONE_2_KHERSON_DELTA", "ZONE_4_DAM_TO_KHERSON_FLOODWAY"):
        cat = P57.sample(out / f"{zone}_cat0609.tif", P.x.values, P.y.values); wse = P57.sample(out / f"{zone}_wse0609.tif", P.x.values, P.y.values)
        seam = P57.sample(B / "dem_seamless" / f"{zone}_dem_evrf2019_20m.tif", P.x.values, P.y.values)
        wc = P57.sample(B / "worldcover_frames" / zone / "wc_2021_20m.tif", P.x.values, P.y.values)
        ok = np.isfinite(cat) & (cat > 0) & np.isfinite(seam) & np.isfinite(wse)
        D = P[ok].assign(cat=cat[ok].astype(int), wse=wse[ok], seam=seam[ok], wc=wc[ok])
        D["res"] = D.seam - D.H_ice; D["ice_below_wse"] = D.H_ice < D.wse; D["dem_below_wse"] = D.seam < D.wse
        x0, y0, x1, y1 = OLESHKY_BOX; D["oleshky_box"] = (D.x > x0) & (D.x < x1) & (D.y > y0) & (D.y < y1)
        def row(label, g):
            return dict(zone=zone, category=label, N=len(g), res_median=round(float(g.res.median()), 2), res_p10=round(float(g.res.quantile(.1)), 2),
                        res_p90=round(float(g.res.quantile(.9)), 2), ice_minus_wse_median=round(float((g.H_ice - g.wse).median()), 2),
                        share_ice_below_wse=round(float(g.ice_below_wse.mean()), 3), share_dem_below_wse=round(float(g.dem_below_wse.mean()), 3))
        for k, g in D.groupby("cat"):
            rows.append(row(CAT[int(k)], g))
        for (box, w_), g in D[D.cat == 5].groupby(["oleshky_box", "wc"]):
            if len(g) >= 30:
                rows.append(row(f"S1_only_ge2m box={bool(box)} wc={P57.WCN.get(int(w_), int(w_))}", g))
    R = pd.DataFrame(rows); pd.set_option("display.width", 250); print(R.to_string(index=False))
    R.to_csv(ROOT / "tables" / "p95c_icesat2_check_0609.csv", index=False); print("-> tables/p95c_icesat2_check_0609.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--step", choices=["rasters", "icesat"], required=True); a = ap.parse_args()
    rasters() if a.step == "rasters" else icesat()
