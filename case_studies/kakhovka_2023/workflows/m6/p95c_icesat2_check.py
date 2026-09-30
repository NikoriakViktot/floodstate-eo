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
Rev 2: the WSE comes from the p95 rev-4 node-based engine (load_engine), same closure as the reconstruction.
Verdict 2026-09-25 (tables/p95c_icesat2_check_0609.csv, first run, superseded chainage; re-run after rev 4): in category 5 the DEM matches ICESat-2 to +-0.3 m (median
residual 0.02 m) and the ground lies 5.6 m (Oleshky grass) to 30 m (cropland) ABOVE the 06-09 water surface, 0 % of
segments below it -> that S1 water is false SAR water on land, not a DEM error. Categories 2-4: 90-100 % of segments
below the surface, as the reconstruction assumes.

Rev 3 (review 2026-09-28, F12): categories inside the S1 valid footprint only (asserted); residuals of the raw and of the
class-bias-corrected terrain side by side; and a PASS HOLD-OUT of the class bias. The same p57 night corpus calibrates the
class bias b_c (p95j) and checks the corrected terrain, so the in-sample corrected residual is not independent. The hold-out
re-estimates b_c with the p95 rule (own-zone class median when N >= 500, else the pooled class median; 'other' = pooled) from
the calibration population of p95j WITHOUT the passes being checked, and applies it to the held-out passes only. A pass is one
acquisition day (the pulled parquet carries no RGT or beam id; the 100 m and 20 m pulls of one pass fall in the same fold).
Schemes: leave one pass out; five folds of whole passes; the two epochs either side of the breach (calibrate before, check
after, and the reverse). Reported next to the numbers of segments AND passes. ICESat-2 ground minus the water surface does
not involve b_c at all; the hold-out bears on the corrected-terrain residual and on the 2 m split of the S1-only categories.

Outputs: $BULK_ROOT/floodplain_dyn/_icesat_check/<ZONE>_{cat,wse}0609.tif, <case_study>/tables/p95c_icesat2_check_0609.csv,
         p95c_icesat2_bias_holdout.csv (zone x category x scheme), p95c_icesat2_bias_folds.csv (scheme x fold x zone x class)
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
ZONES = ("ZONE_2_KHERSON_DELTA", "ZONE_4_DAM_TO_KHERSON_FLOODWAY")
WC6 = {10: "trees", 30: "grass", 40: "cropland", 50: "built", 60: "bare", 90: "wetland"}    # p95 TERRAIN_CLASS = the p95j classes
N_MIN_CLASS = 500                                                   # p95: own-zone class row when N >= this, else the pooled row
BREACH = pd.Timestamp("2023-06-06")
SEED = 20260929


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def rasters():
    import rasterio
    from floodstate_eo import _kakhovka_legacy_config as CFG
    P95 = _ld("p95", HERE / "p95_hand_daily_inundation.py"); P = P95.load_p92()
    out = CFG.BULK_ROOT / "floodplain_dyn" / "_icesat_check"; out.mkdir(parents=True, exist_ok=True)
    W, dxm, dym, _ = P95.load_engine()
    for zone in P95.ZONES:
        L = P95.zone_layers(zone, P); G = L["G"]
        w = W.field(W.prepare(L), DATE, P95.SWOT_MARGIN_M)
        z = np.load(CFG.BULK_ROOT / "floodplain_dyn" / (zone + "_connected_ceiling") / "daily_new.npz")
        new = np.unpackbits(z[DATE], count=G["ny"] * G["nx"]).reshape(G["ny"], G["nx"]).astype(bool)
        v = L["V"][DATE] & L["own"] & ~L["cut"]; s1 = L["W"][DATE] & ~L["pre"] & v; dz = L["dem"] - w
        cat = np.zeros((G["ny"], G["nx"]), "u1"); cat[v] = 1; cat[v & new & ~s1] = 4; cat[s1 & new] = 3      # review F12: terrain-only inside the S1 footprint only
        cat[s1 & ~new & (dz < 2)] = 2; cat[s1 & ~new & (dz >= 2)] = 5
        assert not cat[~v].any(), "a category outside the S1 valid footprint (review F12)"
        prof = dict(driver="GTiff", height=G["ny"], width=G["nx"], count=1, crs=G["crs"], transform=G["transform"], compress="deflate")
        with rasterio.open(out / f"{zone}_cat0609.tif", "w", dtype="uint8", nodata=0, **prof) as o:
            o.write(cat, 1); o.update_tags(categories=str(CAT), producer="p95c_icesat2_check.py")
        with rasterio.open(out / f"{zone}_wse0609.tif", "w", dtype="float32", nodata=-9999, **prof) as o:
            o.write(np.where(np.isfinite(w), w, -9999).astype("f4"), 1)
        with rasterio.open(out / f"{zone}_terrain_corrected.tif", "w", dtype="float32", nodata=-9999, **prof) as o:   # the terrain the categories use
            o.write(np.where(np.isfinite(L["dem"]), L["dem"], -9999).astype("f4"), 1); o.update_tags(vertical_datum=P95.VERTICAL_DATUM,
                    meaning="seamless terrain-bed model minus the residual class bias on FABDEM-sourced cells (p95 rev 6)")
        print(zone, {CAT[k]: round(float((cat == k).sum()) * 4e-4, 1) for k in CAT}, flush=True)


def worldcover_cell(B, zone, x, y):
    """The WorldCover class p95 gives the terrain cell that contains each point (p95.worldcover_on: the 20 m WorldCover frame,
    whose grid is offset by half a cell from the terrain grid, resampled by nearest neighbour onto the terrain grid). It can
    differ from the class of the WorldCover pixel that contains the point (the p95j calibration class) along class edges."""
    import rasterio
    from rasterio.warp import Resampling, reproject
    with rasterio.open(B / "dem_seamless" / f"{zone}_dem_evrf2019_20m.tif") as t:
        T, ny, nx, crs = t.transform, t.height, t.width, t.crs
    with rasterio.open(B / "worldcover_frames" / zone / "wc_2021_20m.tif") as s:
        g = np.zeros((ny, nx), "u1")
        reproject(s.read(1), g, src_transform=s.transform, src_crs=s.crs, dst_transform=T, dst_crs=crs, resampling=Resampling.nearest)
    c, r = ~T * (x, y); c = np.floor(c).astype(int); r = np.floor(r).astype(int); ok = (c >= 0) & (c < nx) & (r >= 0) & (r < ny)
    out = np.full(len(x), -1, int); out[ok] = g[r[ok], c[ok]]
    return out


def class_bias(C, n_min=N_MIN_CLASS):
    """The p95 rule (terrain_residual_table on the p95j population) for a calibration set C (zone, wc, r): the own-zone class
    median when the class has >= n_min points, else the pooled class median (both zones, the six classes); 'other' = the
    pooled median of the six classes. Returns {zone: {wc code | 'other': bias}}, and the source of every entry."""
    six = C[C.wc.isin(list(WC6))]; pc = six.groupby("wc").r.median(); out, used = {}, {}
    for zone in ZONES:
        g = six[six.zone == zone].groupby("wc").r.agg(["median", "size"]); b, u = {}, {}
        for code in WC6:
            if code in g.index and g.loc[code, "size"] >= n_min:
                b[code] = float(g.loc[code, "median"]); u[code] = "own zone"
            elif code in pc.index:
                b[code] = float(pc[code]); u[code] = "pooled"
        b["other"] = float(six.r.median()); u["other"] = "pooled"; out[zone] = b; used[zone] = u
    return out, used


def bias_at(b, wc):
    """The bias of each FABDEM cell class; WorldCover codes without a row (water, shrub, ...) take 'other', as in p95."""
    return pd.Series(np.asarray(wc)).map({k: v for k, v in b.items() if k != "other"}).fillna(b["other"]).to_numpy(float)


def holdout_folds(days_all, days_check, seed=SEED):
    """(scheme, fold, held-out passes) over ALL passes of the calibration and check sets: leave one (checked) pass out; five
    folds of whole passes; the two epochs either side of the breach. A held-out pass leaves the calibration set entirely."""
    u = pd.DatetimeIndex(sorted(set(days_all) | set(days_check)))
    for d in pd.DatetimeIndex(sorted(set(days_check))):
        yield "leave_one_pass_out", str(d.date()), u[u == d]
    g = np.random.default_rng(seed).permutation(len(u)) % 5
    for k in range(5):
        yield "five_fold_passes", f"fold{k + 1}", u[g == k]
    yield "epoch", "calibrate_pre_check_post", u[u >= BREACH]
    yield "epoch", "calibrate_post_check_pre", u[u < BREACH]


def check_p95j(b_in):
    """The in-sample table must be the one p95 used (tables/p95j_terrain_residual_stats.csv, medians rounded to mm)."""
    S = pd.read_csv(ROOT / "tables" / "p95j_terrain_residual_stats.csv")
    for zone in ZONES:
        for code, nm in WC6.items():
            r = S[(S.zone == zone) & (S.wc_class == nm)]
            ref = r.iloc[0]["median"] if len(r) and r.iloc[0]["N"] >= N_MIN_CLASS else S[(S.zone == "POOLED") & (S.wc_class == nm)].iloc[0]["median"]
            assert abs(b_in[zone][code] - ref) < 6e-4, (zone, nm, b_in[zone][code], ref)
        ref = S[(S.zone == "POOLED") & (S.wc_class == "all")].iloc[0]["median"]
        assert abs(b_in[zone]["other"] - ref) < 6e-4, (zone, "other", b_in[zone]["other"], ref)


def bias_holdout(C, K):
    """Pass hold-out of the class bias. C: calibration population (p95j: FABDEM cells, WorldCover != water, per zone, deduplicated
    by date and position); K: FABDEM-sourced check segments (zone, cat, wc, res = seam - H_ice, wse, seam, H_ice, pass_day).
    Returns (per-segment hold-out bias for every scheme, fold table)."""
    b_in, used_in = class_bias(C); check_p95j(b_in)
    K = K.copy(); K["b_in"] = np.nan
    for zone in ZONES:
        m = (K.zone == zone).values; K.loc[m, "b_in"] = bias_at(b_in[zone], K.wc.values[m])
    frows = []
    for scheme, fold, held in holdout_folds(C.pass_day, K.pass_day):
        cal = C[~C.pass_day.isin(held)]; b, used = class_bias(cal); tgt = K.pass_day.isin(held).values
        for zone in ZONES:
            m = tgt & (K.zone == zone).values; K.loc[m, f"b_{scheme}"] = bias_at(b[zone], K.wc.values[m])
            for code in list(WC6) + ["other"]:
                if code not in b[zone]:
                    continue
                n_cls = cal[(cal.zone == zone) & (cal.wc == code)] if code != "other" else cal[cal.wc.isin(list(WC6))]
                frows.append(dict(scheme=scheme, fold=fold, zone=zone, wc_class=WC6.get(code, "other"), n_held_passes=len(held),
                                  n_check_segments=int(m.sum()), n_cal_points=len(n_cls), n_cal_passes=int(n_cls.pass_day.nunique()),
                                  row_used=used[zone][code], b_insample=round(b_in[zone][code], 4), b_holdout=round(b[zone][code], 4),
                                  delta=round(b[zone][code] - b_in[zone][code], 4)))
    return K, pd.DataFrame(frows), b_in, used_in


def holdout_rows(K):
    rows = []
    for (zone, cat), g in K.groupby(["zone", "cat"]):
        for scheme in ("leave_one_pass_out", "five_fold_passes", "epoch"):
            bh = g[f"b_{scheme}"]; assert bh.notna().all(), (zone, cat, scheme)
            r_in = g.res - g.b_in; r_h = g.res - bh; dz_in = g.seam - g.b_in - g.wse; dz_h = g.seam - bh - g.wse
            s1only = g.cat.isin([2, 5]).values
            rows.append(dict(zone=zone, category=CAT[int(cat)], scheme=scheme, N_segments=len(g), n_passes=int(g.pass_day.nunique()),
                             res_raw_median=round(float(g.res.median()), 2), res_insample_median=round(float(r_in.median()), 2),
                             res_holdout_median=round(float(r_h.median()), 2), median_change=round(float(r_h.median() - r_in.median()), 3),
                             median_change_abs=round(abs(float(r_h.median() - r_in.median())), 3), res_holdout_p10=round(float(r_h.quantile(.1)), 2),
                             res_holdout_p90=round(float(r_h.quantile(.9)), 2), max_abs_bias_shift=round(float((bh - g.b_in).abs().max()), 3),
                             share_terrain_insample_below_wse=round(float((dz_in < 0).mean()), 3), share_terrain_holdout_below_wse=round(float((dz_h < 0).mean()), 3),
                             share_ice_below_wse=round(float((g.H_ice < g.wse).mean()), 3),
                             n_s1only_across_2m_split=int(((dz_in[s1only] < 2) != (dz_h[s1only] < 2)).sum())))
    return pd.DataFrame(rows)


def icesat():
    sd = Path.home() / "repo/SWOT-DNIPRO"; sys.path.insert(0, str(sd / "src")); sys.path.insert(0, str(sd / "scripts"))
    P57 = _ld("p57", sd / "scripts/p57_dem_accuracy_night.py")
    from swot_dnipro import config as SCFG
    P, c = P57.load_points(); P = P[~P.in_former_pool].copy(); print("night points", len(P), flush=True)
    PF = _ld("paper1_frame", HERE / "paper1_frame.py"); P["H_ice"] = PF.icesat_ground_to_paper1(P.H_ice.values)      # Paper 1 v6 frame (2026-09-30)
    B = SCFG.BULK_ROOT; out = B / "floodplain_dyn" / "_icesat_check"; rows, cal, chk = [], [], []
    for zone in ZONES:
        cat = P57.sample(out / f"{zone}_cat0609.tif", P.x.values, P.y.values); wse = P57.sample(out / f"{zone}_wse0609.tif", P.x.values, P.y.values)
        seam = P57.sample(B / "dem_seamless" / f"{zone}_dem_evrf2019_20m.tif", P.x.values, P.y.values)
        corr = P57.sample(out / f"{zone}_terrain_corrected.tif", P.x.values, P.y.values)
        src = P57.sample(B / "dem_seamless" / f"{zone}_dem_source_20m.tif", P.x.values, P.y.values); seam = PF.fabdem_to_paper1(seam, src)
        wc = P57.sample(B / "worldcover_frames" / zone / "wc_2021_20m.tif", P.x.values, P.y.values)
        wcc = worldcover_cell(B, zone, P.x.values, P.y.values)                # the class p95 corrected the cell with
        c_ok = np.isfinite(src) & np.isin(src, (3, 4)) & np.isfinite(seam) & np.isfinite(wc) & (wc != 80)       # the p95j population
        cal.append(P[c_ok][["date", "x", "y", "H_ice"]].assign(r=seam[c_ok] - P.H_ice.values[c_ok], wc=wc[c_ok].astype(int), zone=zone).drop_duplicates(subset=["date", "x", "y"]))
        ok = np.isfinite(cat) & (cat > 0) & np.isfinite(seam) & np.isfinite(wse)
        D = P[ok].assign(cat=cat[ok].astype(int), wse=wse[ok], seam=seam[ok], terrain_corr=corr[ok], src=src[ok], wc=wc[ok], wc_cell=wcc[ok])
        D["fabdem"] = D.src.isin([3, 4])
        D["res"] = D.seam - D.H_ice; D["res_corr"] = D.terrain_corr - D.H_ice
        D["ice_below_wse"] = D.H_ice < D.wse; D["dem_below_wse"] = D.seam < D.wse; D["terrain_corr_below_wse"] = D.terrain_corr < D.wse
        x0, y0, x1, y1 = OLESHKY_BOX; D["oleshky_box"] = (D.x > x0) & (D.x < x1) & (D.y > y0) & (D.y < y1)
        def row(label, g):
            f = g[g.fabdem]                                                  # residual statistics of the FABDEM-sourced terrain (the modelled error)
            return dict(zone=zone, category=label, N=len(g), n_dates=int(g.date.dt.date.nunique()), n_fabdem_source=len(f), n_bed_source=int((~g.fabdem).sum()),
                        res_median=round(float(f.res.median()), 2) if len(f) else np.nan, res_p10=round(float(f.res.quantile(.1)), 2) if len(f) else np.nan,
                        res_p90=round(float(f.res.quantile(.9)), 2) if len(f) else np.nan,
                        res_corr_median=round(float(f.res_corr.median()), 2) if len(f) else np.nan, res_corr_p10=round(float(f.res_corr.quantile(.1)), 2) if len(f) else np.nan,
                        res_corr_p90=round(float(f.res_corr.quantile(.9)), 2) if len(f) else np.nan,
                        ice_minus_wse_median=round(float((g.H_ice - g.wse).median()), 2),
                        share_ice_below_wse=round(float(g.ice_below_wse.mean()), 3), share_dem_below_wse=round(float(g.dem_below_wse.mean()), 3),
                        share_terrain_corr_below_wse=round(float(g.terrain_corr_below_wse.mean()), 3))
        for k, g in D.groupby("cat"):
            rows.append(row(CAT[int(k)], g))
        for (box, w_), g in D[D.cat == 5].groupby(["oleshky_box", "wc"]):
            if len(g) >= 30:
                rows.append(row(f"S1_only_ge2m box={bool(box)} wc={P57.WCN.get(int(w_), int(w_))}", g))
        chk.append(D[D.fabdem].assign(zone=zone, wc_point=lambda q: np.where(np.isfinite(q.wc), q.wc, -1).astype(int), wc=lambda q: q.wc_cell)
                   [["zone", "cat", "wc", "wc_point", "res", "res_corr", "seam", "wse", "H_ice", "date"]])
    R = pd.DataFrame(rows); pd.set_option("display.width", 250); print(R.to_string(index=False))
    R.to_csv(ROOT / "tables" / "p95c_icesat2_check_0609.csv", index=False); print("-> tables/p95c_icesat2_check_0609.csv")
    C = pd.concat(cal, ignore_index=True); K = pd.concat(chk, ignore_index=True)
    C["pass_day"] = C.date.dt.normalize(); K["pass_day"] = K.date.dt.normalize()
    K, F, b_in, _ = bias_holdout(C, K)
    off = (K.res_corr - (K.res - K.b_in)).abs() > 0.01                     # the sampled corrected raster vs the rule re-applied
    print(f"in-sample bias = p95j table (asserted); corrected raster vs rule: {int(off.sum())} of {len(K)} segments differ by > 1 cm; "
          f"terrain-cell class != class of the pixel holding the segment (half-cell grid offset): {int((K.wc != K.wc_point).sum())}", flush=True)
    assert off.mean() < 0.01, "the corrected terrain raster does not follow the p95 class-bias rule"
    H = holdout_rows(K); H["note"] = ("pass = acquisition day; hold-out bias from the p95j population without the checked passes, p95 rule; "
                                      "ICESat-2 minus surface does not involve the bias")
    H.to_csv(ROOT / "tables" / "p95c_icesat2_bias_holdout.csv", index=False); F.to_csv(ROOT / "tables" / "p95c_icesat2_bias_folds.csv", index=False)
    print(H.drop(columns="note").to_string(index=False))
    print(F.groupby(["scheme", "zone", "wc_class"]).delta.agg(lambda d: round(float(d.abs().max()), 3)).rename("max_abs_delta").to_string())
    print(f"calibration population {len(C):,} points on {C.pass_day.nunique()} passes; check segments (FABDEM) {len(K):,} on {K.pass_day.nunique()} passes")
    print("-> tables/p95c_icesat2_bias_holdout.csv, p95c_icesat2_bias_folds.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--step", choices=["rasters", "icesat"], required=True); a = ap.parse_args()
    rasters() if a.step == "rasters" else icesat()
