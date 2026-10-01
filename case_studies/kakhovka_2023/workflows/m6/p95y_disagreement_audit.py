# New in floodstate-eo, 2026-10-01 (reviewer's questions on the p95 rev-9 / p95x report). STATUS: ACTIVE. Diagnostic, nothing is fitted.
"""P95y -- what the external comparisons can and cannot show: four audits of the rev-9 reconstruction and the p95x state mask.

1. CSI on 7 June (ICEYE, no own EO): the true bounds over every assignment of the UNKNOWN cells (min: UNKNOWN on ICEYE water -> DRY,
   UNKNOWN on ICEYE dry -> WATER; max: the reverse), the two simple scenarios (all UNKNOWN DRY / all WATER), the share of the ICEYE water
   that falls into UNKNOWN, and whether UNKNOWN concentrates at the ICEYE water edge. Ground: ICEYE analysis extent inside the
   reconstruction domain, without the optical pre-breach water and UNOSAT's reference water; split into event ground and the model-only
   normally-wet ground.
2. Cumulative 6-9 June against UNOSAT's composite (ICEYE 7 June + Sentinel-3 6-9 June + Sentinel-2 8 June; the ~620 km2 of UNOSAT product
   3616; the layer is read from the activation's shapefile package FL20230606UKR, which UNOSAT serves from the folder of product 3614):
   where the two agree and where not -- is the UNOSAT-only flood on the model-only normally-wet ground (the reference-definition
   explanation) or on event ground the reconstruction leaves dry or UNKNOWN?
3. Sentinel-1 9 June new dark water that the reconstruction misses OUTSIDE the normally-wet ground (T13 leaves ~90 km2 unexplained):
   Landsat-9 (same morning) and ICEYE (7 June) agreement, land cover, the ensemble P(water), storage-sensitive depressions, height
   above the day's water surface and distance to the reconstructed water.
4. The pre-event state of the model-only normally-wet ground (what the data say, not the model): Sentinel-2 pre-breach water frequency
   (p60), UNOSAT's Sentinel-2 reference of 3-5 June, Sentinel-1 dark water and VV/VH backscatter of 17 spring-2023 scenes
   (15 April - 2 June; flooded reeds brighten VV by double bounce, open water is dark), compared with reeds on higher ground and with
   open water; and the terrain probability of lying under the pre-breach surface (terrain class sigma + water-surface sigma).
Outputs: tables/p95y_csi_bounds.csv, p95y_cumulative_overlap.csv, p95y_s1_residual_misses.csv, p95y_marsh_pre_event.csv, p95y_manifest.json
"""
from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SFX = "_connected_ceiling"
WSE_TERMS = ("datum_closure_kherson", "gauge_daily", "swot_node_wse_u", "interpolation_gap_cv")
WCN = {10: "trees", 20: "shrub", 30: "grass", 40: "cropland", 50: "built-up", 60: "bare", 80: "water", 90: "reeds (herbaceous wetland)", 0: "none"}
PRE_CACHES = {"ZONE_2_KHERSON_DELTA": "ZONE_2_KHERSON_DELTA_flood_june2023_pre2023", "ZONE_4_DAM_TO_KHERSON_FLOODWAY": "ZONE_4_FLOODWAY_june2023_s32_pre2023"}


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def csi_bounds(tp, fp, fn, uw, ud):
    """CSI on the decided cells, the two scenarios and the true bounds over every assignment of the UNKNOWN cells.
    uw / ud = UNKNOWN cells where the reference is water / dry. A UNKNOWN-on-water cell adds to TP (WATER) or FN (DRY); a UNKNOWN-on-dry
    cell adds to FP (WATER) or nothing (DRY); so the minimum takes FN for uw and FP for ud, the maximum TP for uw and nothing for ud."""
    f = lambda a, b: a / b if b else np.nan
    return dict(CSI_decided=f(tp, tp + fp + fn), CSI_unknown_as_dry=f(tp, tp + fp + fn + uw), CSI_unknown_as_water=f(tp + uw, tp + uw + fp + ud + fn),
                CSI_min=f(tp, tp + fp + fn + uw + ud), CSI_max=f(tp + uw, tp + uw + fp + fn))


def main():
    t0 = time.time()
    import pandas as pd
    import rasterio
    from floodstate_eo import _kakhovka_legacy_config as CFG
    from floodstate_eo.terrain.connectivity import largest_component
    from rasterio import features
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.warp import reproject
    from scipy import ndimage
    from shapely.geometry import shape
    from shapely.ops import unary_union
    TAB = ROOT / "tables"
    O = _ld("p95o", HERE / "p95o_component_qa.py"); P95 = O._ld("p95_hand_daily_inundation"); T = _ld("p95t", HERE / "p95t_eo_recession.py")
    P = P95.load_p92(); man = O.load_manifest(SFX)
    if int(man.get("rev", 0)) < 9:
        raise SystemExit("p95y audits the rev-9 reconstruction")
    M = P95.mosaic_layers(P, with_s1=True); g = M["grid"]; tr = g.transform; shp = g.shape; crs = M["G"]["crs"]; CK = P95.CELL_KM2
    W_eng, dxm, _ = O.engine_for(P95, man, SFX); M["base"] = M["base_geom"] & P95.dam_mask(M, dxm); dom = M["base"]; Z = W_eng.prepare(M)
    seed = largest_component(M["seed"], int(man["constants"].get("connectivity", 8)))
    corr = M["regions"]["DNIPRO_CORRIDOR"]; inh = M["regions"]["INHULETS_VALLEY_rect"]
    B = O.compose_npz(M, SFX, "baseline"); opt = M["pre"] & B; nw = B & ~M["pre"]
    wc = g.compose({z: L["wc"] for z, L in M["zones"].items()}, 0, order=M["names"], dtype="u1"); lc = lambda m: pd.Series(wc[m]).map(WCN).value_counts().mul(CK).round(1).head(5).to_dict()
    OUT = CFG.BULK_ROOT / "floodplain_dyn" / "_weak_labels"
    def ras(nm):
        fc = json.loads((T.utm_dir(CFG.BULK_ROOT) / f"{nm}.geojson").read_text())["features"]
        return features.rasterize([(unary_union([shape(f_["geometry"]) for f_ in fc]), 1)], out_shape=shp, transform=tr, fill=0, dtype="uint8").astype(bool)
    def state(d):
        with rasterio.open(OUT / f"state_{d}.tif") as s:
            return s.read(1), s.read(4)
    uref = ras(T.REF); k = lambda m: round(float(m.sum()) * CK, 2)
    print(f"setup {round(time.time() - t0)} s", flush=True)

    # ---- 1. CSI on 7 June: coverage, the two scenarios and the admissible interval, per ground class --------------------------------
    st7, rf = state("2023-06-07"); aoi = ras("ICEYE_20230607_AnalysisExtent_KhersonskaOblast_UKR"); ice = ras("ICEYE_20230607_WaterExtent_KhersonskaOblast_UKR")
    with rasterio.open(OUT / "ground_class.tif") as s:
        gcl = s.read(1)                                                  # p95x: 0 dry before the event, 1 vegetated wetland, 2 optical water, 3 other water
    ground = aoi & dom & ~uref & (rf != 1); edge = ndimage.binary_dilation(ice, iterations=2) & ~ndimage.binary_erosion(ice, iterations=2)
    rows = []
    for gname, sel in (("dry-before-event ground", ground & (gcl == 0)), ("dry-before-event ground, open land", ground & (gcl == 0) & np.isin(wc, (30, 40, 60))),
                       ("vegetated wetland", ground & (gcl == 1)), ("non-optical-reference ground (as first reported)", ground),
                       ("event ground of the first audit (no model-only normally-wet)", ground & (rf == 0))):
        un = ice & sel; w, d_, u = sel & (st7 == 1), sel & (st7 == 0), sel & (st7 == 2)
        tp, fp, fn = float((w & un).sum()), float((w & ~un).sum()), float((d_ & un).sum()); uw, ud = float((u & un).sum()), float((u & ~un).sum())
        r = dict(ground=gname, km2=k(sel), ICEYE_water_km2=k(un), coverage=round(1 - float(u.sum() / max(sel.sum(), 1)), 3), UNKNOWN_km2=k(u),
                 ICEYE_water_in_UNKNOWN_share=round(uw / max(uw + tp + fn, 1), 3), UNKNOWN_cells_ICEYE_water_share=round(uw / max(uw + ud, 1), 3),
                 UNKNOWN_share_at_ICEYE_edge=round(float((u & edge & sel).sum() / max((edge & sel).sum(), 1)), 3),
                 UNKNOWN_share_off_edge=round(float((u & ~edge & sel).sum() / max((~edge & sel).sum(), 1)), 3))
        r.update({kk: round(v, 3) for kk, v in csi_bounds(tp, fp, fn, uw, ud).items()}); rows.append(r)
    C1 = pd.DataFrame(rows); C1.to_csv(TAB / "p95y_csi_bounds.csv", index=False); print(C1.to_string(index=False), flush=True)

    # ---- 2. cumulative 6-9 June against UNOSAT's composite, like for like per ground class ------------------------------------------
    cum_un = ras("cumulative_0606_0609_flood")
    analysed = (aoi | ras("ST3_20230609_ST2_20230608_AnalysisExtent_KhersonskaOblast_UKR")) & dom & ~uref & (rf != 1)
    ours = np.zeros(shp, bool); ours_u = np.zeros(shp, bool); ever_eo_dry = np.zeros(shp, bool); ever_unk = np.zeros(shp, bool)
    for d in ("2023-06-06", "2023-06-07", "2023-06-08", "2023-06-09"):
        s_, r_ = state(d); ours |= s_ == 1; ours_u |= (s_ == 1) | (s_ == 2); ever_unk |= s_ == 2
        with rasterio.open(OUT / f"state_{d}.tif") as s:
            src = s.read(2)
        ever_eo_dry |= (s_ == 0) & ((src == 1) | (src == 2))
    rows = []
    for rname, rg in (("corridor + Inhulets", corr | inh), ("corridor", corr)):
        for gname, gsel in (("dry-before-event ground", gcl == 0), ("vegetated wetland", gcl == 1), ("all non-optical-reference ground", np.ones(shp, bool))):
            a_ = analysed & rg & gsel; U_ = cum_un & a_; O_ = ours & a_
            both, oo, uo = U_ & O_, O_ & ~U_, U_ & ~O_
            rows.append(dict(region=rname, ground=gname, analysed_km2=k(a_), UNOSAT_km2=k(U_), ours_WATER_km2=k(O_), ours_WATER_or_UNKNOWN_km2=k(ours_u & a_),
                             both_km2=k(both), ours_only_km2=k(oo), UNOSAT_only_km2=k(uo), CSI=round(float(both.sum() / max((U_ | O_).sum(), 1)), 3),
                             POD_ours_vs_UNOSAT=round(float(both.sum() / max(U_.sum(), 1)), 3), FAR_ours_vs_UNOSAT=round(float(oo.sum() / max(O_.sum(), 1)), 3),
                             UNOSAT_only_where_ours_UNKNOWN_km2=k(uo & ever_unk), UNOSAT_only_where_ours_EO_dry_km2=k(uo & ever_eo_dry & ~ever_unk),
                             UNOSAT_only_where_ours_model_dry_km2=k(uo & ~ever_unk & ~ever_eo_dry), UNOSAT_only_landcover=str(lc(uo)), ours_only_landcover=str(lc(oo))))
    C2 = pd.DataFrame(rows); C2.to_csv(TAB / "p95y_cumulative_overlap.csv", index=False); print(C2.T.to_string(), flush=True)

    # ---- 3. Sentinel-1 9 June misses outside the normally-wet ground --------------------------------------------------------------------
    d9 = "2023-06-09"; z0 = lambda L: np.zeros((L["G"]["ny"], L["G"]["nx"]), bool)
    V9 = g.compose({z: L["V"].get(d9, z0(L)) for z, L in M["zones"].items()}, False, order=M["names"], dtype=bool)
    W9 = g.compose({z: L["W"].get(d9, z0(L)) for z, L in M["zones"].items()}, False, order=M["names"], dtype=bool)
    s1new = W9 & V9 & ~(M["pre"] | M["s1_pre_dark"]) & corr & dom                   # the T13 domain: the reconstruction base, corridor
    new9 = O.compose_npz(M, SFX, d9); pot9, H9 = P95.potential_mosaic(M, W_eng, Z, d9, "connected_ceiling", margin=float(man["constants"].get("margin_m", 0)), connectivity=8, seed=seed)
    miss = s1new & ~new9; resid = miss & ~nw
    l9 = ras("L9_20230609_WaterExtent_KhersonskaOblast_UKR"); l9_ob = ras("ST3_20230609_ST2_20230608_AnalysisExtent_KhersonskaOblast_UKR")
    zdir = CFG.BULK_ROOT / "floodplain_dyn" / f"{M['names'][0]}{SFX}"
    with rasterio.open(zdir / f"p95e_cellprob_water_{d9}.tif") as s:
        nd_ = float(s.tags()["n_draws"])
    pw = O.compose_tif(M, SFX, f"p95e_cellprob_water_{d9}.tif", 65535, "u2"); pw = np.where(pw < 65535, pw / nd_, 0.0)
    with rasterio.open(OUT / "storage_sensitive.tif") as s:
        storage = s.read(1).astype(bool)
    dist = ndimage.distance_transform_edt(~pot9) * g.cell; dz = np.nan_to_num(M["dem"] - H9, nan=np.nan)
    rows = [dict(item="S1 new dark water 9 June, corridor", km2=k(s1new)), dict(item="reconstructed new water 9 June (nominal), corridor", km2=k(new9 & corr)),
            dict(item="missed by the reconstruction", km2=k(miss)), dict(item="  of which on model-only normally-wet ground", km2=k(miss & nw)),
            dict(item="  of which elsewhere (the residual)", km2=k(resid)),
            dict(item="residual: Landsat-9 9 June water there (analysed by L9)", km2=k(resid & l9), share=round(float((resid & l9).sum() / max((resid & l9_ob).sum(), 1)), 3)),
            dict(item="residual: ICEYE 7 June water there (analysed by ICEYE)", km2=k(resid & ice), share=round(float((resid & ice).sum() / max((resid & aoi).sum(), 1)), 3)),
            dict(item="residual: ensemble P(water) >= 0.8", km2=k(resid & (pw >= 0.8))), dict(item="residual: 0.05 < P(water) < 0.8", km2=k(resid & (pw > 0.05) & (pw < 0.8))),
            dict(item="residual: P(water) <= 0.05", km2=k(resid & (pw <= 0.05))), dict(item="residual: in storage-sensitive depressions", km2=k(resid & storage)),
            dict(item="residual: within 100 m of the reconstructed water", km2=k(resid & (dist <= 100))),
            dict(item="residual: > 1 km from the reconstructed water", km2=k(resid & (dist > 1000))),
            dict(item="residual: terrain > 1 m above the 9 June surface", km2=k(resid & (dz > 1))),
            dict(item="residual: terrain > 1 m above the surface, no L9 water, analysed by L9", km2=k(resid & (dz > 1) & ~l9 & l9_ob))]
    for name, m in (("residual", resid), ("residual with L9 water", resid & l9), ("residual without L9 water (analysed)", resid & ~l9 & l9_ob)):
        rows.append(dict(item=f"{name}: land cover", km2=k(m), note=str(lc(m))))
        q = np.nanpercentile(dz[m], [25, 50, 75]) if m.any() else [np.nan] * 3
        rows.append(dict(item=f"{name}: terrain minus 9 June surface, m (p25 / p50 / p75)", note=" / ".join(f"{v:.2f}" for v in q)))
    C3 = pd.DataFrame(rows); C3.to_csv(TAB / "p95y_s1_residual_misses.csv", index=False); print(C3.to_string(index=False), flush=True)

    # ---- 4. the pre-event state of the model-only normally-wet ground --------------------------------------------------------------------
    # Sentinel-2 pre-breach water frequency (p60 labels, 10 m -> 20 m average)
    wf20 = np.full(shp, np.nan, "f4")
    for fid in ("B1", "B2"):
        with rasterio.open(CFG.BULK_ROOT / "frames10" / fid / "labels.tif") as s:
            dsc = list(s.descriptions); wf = s.read(dsc.index("pre_water_frac") + 1).astype("f4"); t10 = s.transform
        dst = np.full(shp, np.nan, "f4")
        reproject(wf, dst, src_transform=t10, src_crs=crs, dst_transform=tr, dst_crs=crs, resampling=Resampling.average, src_nodata=np.nan, dst_nodata=np.nan)
        wf20 = np.where(np.isnan(wf20), dst, wf20)
    # spring-2023 Sentinel-1: dark-water frequency and mean VV / VH (dB) on the union grid
    sums = {kk: np.full(shp, np.nan, "f4") for kk in ("n", "dark", "vv", "vh")}
    for zname in M["names"]:                                            # OWNER_ORDER: the delta zone is written last and wins the overlap
        cdir = CFG.S1_CACHE / PRE_CACHES[zname]; zz = np.load(cdir / "per_scene_water.npz", allow_pickle=True)
        zs = tuple(int(v) for v in zz["shape"]); ztr = from_origin(float(zz["x0"]), float(zz["y1"]), float(zz["cell"]), float(zz["cell"]))
        un_ = lambda kk: np.unpackbits(zz[kk], count=zs[0] * zs[1]).reshape(zs).astype(bool)
        acc = {kk: np.zeros(zs, "f4") for kk in sums}
        scenes = sorted(kk for kk in zz.files if kk.startswith("2023") and kk[:10] <= "2023-06-02")
        for sc in scenes:
            v, w = un_("valid_" + sc), un_(sc)
            with np.load(cdir / f"{sc}.npz") as b:
                vv, vh, cov = b["vv"], b["vh"], b["cov"]
            ok = v & cov & (vv > 0) & (vh > 0)
            acc["n"] += ok; acc["dark"] += ok & w; acc["vv"] += np.where(ok, 10 * np.log10(np.maximum(vv, 1e-6)), 0); acc["vh"] += np.where(ok, 10 * np.log10(np.maximum(vh, 1e-6)), 0)
        dst = {}
        for kk, arr in acc.items():
            dst[kk] = np.full(shp, np.nan, "f4")
            reproject(arr, dst[kk], src_transform=ztr, src_crs=crs, dst_transform=tr, dst_crs=crs, resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
        have = np.nan_to_num(dst["n"]) > 0
        for kk in sums:
            sums[kk][have] = dst[kk][have]
        print(f"  spring S1 {zname}: {len(scenes)} scenes; {round(time.time() - t0)} s", flush=True)
    n_ = np.nan_to_num(sums["n"]); obs = n_ >= 5
    dark_frac = np.where(obs, sums["dark"] / np.maximum(n_, 1), np.nan); vv_db = np.where(obs, sums["vv"] / np.maximum(n_, 1), np.nan); vh_db = np.where(obs, sums["vh"] / np.maximum(n_, 1), np.nan)
    uc = pd.read_csv(TAB / "p95e_uncertainty_components.csv").set_index("component").sigma_m; sH = float(np.sqrt(sum(float(uc[t]) ** 2 for t in WSE_TERMS)))
    H_pre = np.asarray(W_eng.field(Z, P95.BASELINE_DATE, 0.0), "f4"); sig = np.sqrt(np.nan_to_num(M["sig"]) ** 2 + sH ** 2)
    from scipy.stats import norm
    p_under = norm.cdf((H_pre - M["dem"]) / sig)
    reeds = wc == 90
    groups = {"model-only normally wet (all)": dom & nw, "model-only normally wet, reeds": dom & nw & reeds,
              "reeds on higher ground (not normally wet, > 0.5 m above the pre-breach surface)": dom & reeds & ~B & ((M["dem"] - H_pre) > 0.5),
              "optical pre-breach open water": dom & opt}
    rows = []
    for gname, m in groups.items():
        mo = m & obs
        rows.append(dict(group=gname, km2=k(m), landcover=str(lc(m)), S2_prebreach_water_freq_gt0_share=round(float(np.nanmean(wf20[m] > 0)), 3) if m.any() else np.nan,
                         S2_prebreach_water_freq_median_pct=round(float(np.nanmedian(wf20[m])), 1) if m.any() else np.nan,
                         UNOSAT_S2_reference_water_share=round(float(uref[m].mean()), 3) if m.any() else np.nan,
                         S1_spring_observed_km2=k(mo), S1_spring_scenes_median=float(np.nanmedian(n_[mo])) if mo.any() else np.nan,
                         S1_spring_dark_ever_share=round(float(np.mean(dark_frac[mo] > 0)), 3) if mo.any() else np.nan,
                         S1_spring_dark_half_share=round(float(np.mean(dark_frac[mo] >= 0.5)), 3) if mo.any() else np.nan,
                         S1_spring_VV_dB_median=round(float(np.nanmedian(vv_db[mo])), 2) if mo.any() else np.nan,
                         S1_spring_VH_dB_median=round(float(np.nanmedian(vh_db[mo])), 2) if mo.any() else np.nan,
                         S1_spring_VV_minus_VH_dB_median=round(float(np.nanmedian((vv_db - vh_db)[mo])), 2) if mo.any() else np.nan,
                         terrain_P_under_prebreach_surface_median=round(float(np.nanmedian(p_under[m])), 3) if m.any() else np.nan,
                         terrain_P_under_ge_0p8_share=round(float(np.nanmean(p_under[m] >= 0.8)), 3) if m.any() else np.nan,
                         ICEYE_0607_water_share=round(float((ice & m & aoi).sum() / max((m & aoi).sum(), 1)), 3)))
    C4 = pd.DataFrame(rows); C4.to_csv(TAB / "p95y_marsh_pre_event.csv", index=False); print(C4.T.to_string(), flush=True)
    (TAB / "p95y_manifest.json").write_text(json.dumps(dict(
        producer="p95y_disagreement_audit.py", p95_rev=man.get("rev"), questions="reviewer 2026-10-01: CSI bounds and ICEYE water in UNKNOWN; spatial overlap of the "
        "cumulative 6-9 June masks; the S1 9 June residual misses; the pre-event state of the model-only normally-wet ground",
        unosat_source="activation FL20230606UKR shapefile package served from unosat_filesystem/3614 (layers of several products; the cumulative 6-9 June "
                      "composite ICEYE 7 June + S3 6-9 June + S2 8 June corresponds to product 3616, ~620 km2)",
        s1_spring=dict(caches=PRE_CACHES, window="2023-04-15 .. 2023-06-02", min_valid_scenes=5, note="mean of dB over valid scenes; dark = the cache's per-scene water mask"),
        terrain_sigma=dict(sigma_H_m=round(sH, 3), terms=list(WSE_TERMS), terrain="p95e class sigma per cell"), nothing_fitted=True), indent=1, default=str))
    print("->", TAB / "p95y_*", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
