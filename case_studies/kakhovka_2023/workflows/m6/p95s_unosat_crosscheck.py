# New in floodstate-eo, 2026-09-30 (maintainer: cross-check the 7 June reconstruction against the UNOSAT / ICEYE flood extent). STATUS: ACTIVE. Diagnostic.
"""P95s -- the reconstruction of 7 June against the UNOSAT flood extent from ICEYE of the same day (independent, satellite-observed).

Source: UNOSAT product 3614, activation FL20230606UKR (https://unosat.org/static/unosat_filesystem/3614/FL20230606UKR_SHP.zip; the archive holds
every layer of the activation; UNOSAT products on HDX are CC BY-SA). Layers used here:
  ICEYE_20230607_AnalysisExtent   the analysed area (2097 km2), acquisitions 12:18, 12:48 and 13:01 UTC on 7 June 2023;
  ICEYE_20230607_FloodExtent      'Flood Water / New Water or Water Increase' (520 km2) -- compared with our NEW water (A_new);
  ICEYE_20230607_WaterExtent      all water seen on 7 June (699 km2) -- compared with our TOTAL water P_t;
  ST2_20230603_20230605_WaterExtent  UNOSAT's pre-event reference water (Sentinel-2) -- with our baseline, the pre-event water of either side.
Steps:
  convert (SWOT-DNIPRO venv: geopandas) -> $BULK_ROOT/external/unosat/3614/utm/<layer>.geojson in EPSG:32636, clipped to the union grid;
  compare (floodstate-eo venv) -> the nominal P_t of 7 June recomputed exactly as p95 builds it (gate against daily_new.npz), the ensemble P of
      p95e cellprob, both rasterised with the UNOSAT layers on the 20 m union grid (cell centres), inside the ICEYE analysis extent and the
      reconstruction domain.
Scores per window (corridor, Kozachi Laheri village, Krynky + the lowland south of Krynky) and per WorldCover stratum (open ground, trees,
built-up, wetland): POD = TP/(TP+FN), FAR = FP/(TP+FP), CSI = TP/(TP+FP+FN) (for binary maps CSI is the IoU), F1 and the area bias. New water
is scored on the ground that was dry before the breach in both references (our baseline and UNOSAT's Sentinel-2 reference), so a difference
between the two pre-event masks is not counted as a flood error. X-band SAR misses water under forest and in built-up areas (UNOSAT maps urban
flooding in separate layers): the strata keep those apart. Michurina street (Kozachi Laheri; OSM state of 5 June 2023, p95r) is measured on
the vectors: the distance from the street to the nearest ICEYE flood / water polygon.
Outputs: tables/p95s_unosat_scores.csv, p95s_unosat_michurina.csv, p95s_unosat_villages.csv, p95s_unosat_later_layers.csv (Landsat-9 water
         of 9 June and the multi-sensor flood of 6-9 June of the same product against our 7-8 June new water, the primary and the memory
         variant of 9 June), p95s_unosat_manifest.json;
         figures/m6_v003A/p95s_unosat_20230607.png
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRODUCT = "3614"
URL = "https://unosat.org/static/unosat_filesystem/3614/FL20230606UKR_SHP.zip"
LAYERS = {"aoi": "ICEYE_20230607_AnalysisExtent_KhersonskaOblast_UKR", "flood": "ICEYE_20230607_FloodExtent_KhersonskaOblast_UKR",
          "water": "ICEYE_20230607_WaterExtent_KhersonskaOblast_UKR", "outside_bed": "ICEYE_20230607_WaterExtentOutsideRiverBed_KhersonskaOblast_UKR",
          "ref_water": "ST2_20230603_20230605_WaterExtent_KhersonskaOblast_UKR",
          "urban_affected": "ICEYE_20230607_AffectedUrbanArea_KhersonskaOblast_UKR", "urban_analysed": "ICEYE_20230607_AnalysedUrbanArea_KhersonskaOblast_UKR",
          "l9_0609_water": "L9_20230609_WaterExtent_KhersonskaOblast_UKR",
          "cumulative_0606_0609": "ST3_20230606_20230607_20230609_ST2_20230608_ICEYE_20230607_FloodExtent_KhersonskaOblast"}
WINDOWS = {"corridor (ICEYE analysis extent)": None, "Kozachi Laheri village": (32.925, 46.690, 33.025, 46.726),
           "Krynky + lowland south of Krynky": (33.03, 46.595, 33.23, 46.78), "Krynky village": (33.07, 46.728, 33.17, 46.765),
           "lowland box (p95p/p95q)": ("box", 33.12, 46.665, 6.5, 7.0)}
STRATA = {"all": None, "open ground (grass, cropland, bare)": (30, 40, 60), "trees and shrub": (10, 20), "built-up": (50,), "wetland": (90,)}


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def bulk_root() -> Path:
    from floodstate_eo import _kakhovka_legacy_config as CFG
    return CFG.BULK_ROOT


def step_convert(bulk: Path):
    """SWOT-DNIPRO venv (geopandas + pyogrio): the used layers to EPSG:32636 GeoJSON, with the product's areas and the archive sha256."""
    import geopandas as gpd
    base = bulk / "external" / "unosat" / PRODUCT; zp = base / "FL20230606UKR_SHP.zip"; shp = base / "FL20230606UKR_SHP"
    if not zp.exists():
        raise SystemExit(f"download {URL} to {zp} first")
    out = base / "utm"; out.mkdir(parents=True, exist_ok=True); info = dict(product=PRODUCT, url=URL, sha256=hashlib.sha256(zp.read_bytes()).hexdigest(), layers={})
    for k, nm in LAYERS.items():
        g = gpd.read_file(shp / f"{nm}.shp"); gu = g.to_crs(32636)
        row = g.drop(columns="geometry").iloc[0].to_dict()
        info["layers"][k] = dict(name=nm, area_km2=round(float(gu.area.sum()) / 1e6, 2), attributes={a: str(v) for a, v in row.items()})
        gu[["geometry"]].to_file(out / f"{k}.geojson", driver="GeoJSON")
        print(k, nm, info["layers"][k]["area_km2"], "km2", flush=True)
    fl, wa = (gpd.read_file(out / f"{k}.geojson").union_all() for k in ("flood", "water"))
    info["flood_minus_water_km2"] = round(fl.difference(wa).area / 1e6, 2); info["water_minus_flood_km2"] = round(wa.difference(fl).area / 1e6, 2)
    print("flood not in water:", info["flood_minus_water_km2"], "km2; water not in flood:", info["water_minus_flood_km2"], "km2")
    (out / "layers.json").write_text(json.dumps(info, indent=1))


def scores(model, ref, valid):
    tp = int((model & ref & valid).sum()); fp = int((model & ~ref & valid).sum()); fn = int((~model & ref & valid).sum())
    c = 0.0004                                                                          # km2 per 20 m cell
    return dict(model_km2=round((tp + fp) * c, 2), unosat_km2=round((tp + fn) * c, 2), TP_km2=round(tp * c, 2), FP_km2=round(fp * c, 2), FN_km2=round(fn * c, 2),
                POD=round(tp / (tp + fn), 3) if tp + fn else np.nan, FAR=round(fp / (tp + fp), 3) if tp + fp else np.nan,
                CSI=round(tp / (tp + fp + fn), 3) if tp + fp + fn else np.nan, F1=round(2 * tp / (2 * tp + fp + fn), 3) if tp + fp + fn else np.nan,
                area_bias=round((tp + fp) / (tp + fn), 3) if tp + fn else np.nan)


def step_compare(bulk: Path, day: str):
    import pandas as pd
    import rasterio
    from rasterio import features
    from rasterio.warp import transform as tf_transform
    from shapely.geometry import LineString, shape
    from shapely.ops import unary_union
    from floodstate_eo import _kakhovka_legacy_config as CFG
    from floodstate_eo.terrain.connectivity import largest_component
    t0 = time.time(); TAB = ROOT / "tables"; FIG = ROOT / "figures" / "m6_v003A"; sfx = "_connected_ceiling"
    O = _ld("p95o", HERE / "p95o_component_qa.py"); P95 = O._ld("p95_hand_daily_inundation"); P = P95.load_p92(); R = _ld("p95r", HERE / "p95r_local_daily_maps.py")
    man = O.load_manifest(sfx); c = man["constants"]; conn = int(c.get("connectivity", 8)); margin = float(c.get("margin_m", 0.0))
    M = P95.mosaic_layers(P, with_s1=False); g = M["grid"]
    W, dxm, _ = O.engine_for(P95, man, sfx); M["base"] = M["base_geom"] & P95.dam_mask(M, dxm)
    seed = largest_component(M["seed"], conn) if c.get("seed_network", "main_stem") == "main_stem" else M["seed"]
    Z = W.prepare(M); baseline = O.compose_npz(M, sfx, "baseline")
    pot, _w = P95.potential_mosaic(M, W, Z, day, "connected_ceiling", margin=margin, connectivity=conn, seed=seed); new = pot & ~baseline
    stored = O.compose_npz(M, sfx, day); diff = float((stored ^ new).sum()) * P95.CELL_KM2
    assert diff <= 0.1 + 1e-9, (day, "recomputed new water differs from daily_new.npz by", diff, "km2")
    n_draws = 1000.0
    with rasterio.open(bulk / "floodplain_dyn" / f"ZONE_4_DAM_TO_KHERSON_FLOODWAY{sfx}" / f"p95e_cellprob_{day}.tif") as s:
        n_draws = float(s.tags().get("n_draws", 1000))
    Pm = O.compose_tif(M, sfx, f"p95e_cellprob_{day}.tif", 0, "u2").astype("f4") / n_draws
    wc = g.compose({z: L["wc"] for z, L in M["zones"].items()}, 0, order=M["names"], dtype="u1")
    print("P_t of", day, "recomputed; gate", round(diff, 3), "km2;", round(time.time() - t0), "s", flush=True)
    # ---- the UNOSAT layers on the union grid ------------------------------------------------------------------------------------
    gj = {k: json.loads((bulk / "external" / "unosat" / PRODUCT / "utm" / f"{k}.geojson").read_text()) for k in LAYERS}
    geo = {k: unary_union([shape(f["geometry"]) for f in v["features"]]) for k, v in gj.items()}
    ras = {k: features.rasterize([(v, 1)], out_shape=g.shape, transform=g.transform, fill=0, dtype="uint8").astype(bool) for k, v in geo.items()}
    dom = M["base"] & ras["aoi"]                                                        # scored: the ICEYE analysis extent inside the reconstruction domain
    dry_both = ~baseline & ~ras["ref_water"]                                           # ground that was dry before the breach in both references
    xs, ys = M["xs"], M["ys"]; to_xy = lambda lon, lat: tuple(float(v[0]) for v in tf_transform("EPSG:4326", CFG.CRS_METRIC, [lon], [lat]))
    rows = []
    for wn, bb in WINDOWS.items():
        win = np.ones(g.shape, bool)
        if bb is not None:
            if bb[0] == "box":
                cx, cy = to_xy(bb[1], bb[2]); x0, x1, y0, y1 = cx - bb[3] * 1e3, cx + bb[3] * 1e3, cy - bb[4] * 1e3, cy + bb[4] * 1e3
            else:
                (x0, y0), (x1, y1) = to_xy(bb[0], bb[1]), to_xy(bb[2], bb[3])
            win = ((xs >= x0) & (xs <= x1))[None, :] & ((ys >= y0) & (ys <= y1))[:, None]
        for sn, codes in STRATA.items():
            st = np.ones(g.shape, bool) if codes is None else np.isin(wc, codes)
            v = dom & win & st
            if v.sum() < 25:
                continue
            for comp, model, ref, extra in (("new water vs ICEYE FloodExtent (pre-event dry in both references)", new, ras["flood"], dry_both),
                                            ("new water, ensemble P >= 0.05 vs ICEYE FloodExtent (same ground)", Pm >= 0.05, ras["flood"], dry_both),
                                            ("total water P_t vs ICEYE WaterExtent", pot, ras["water"], np.ones(g.shape, bool))):
                r = dict(window=wn, stratum=sn, comparison=comp, scored_km2=round(float((v & extra).sum()) * P95.CELL_KM2, 2)); r.update(scores(model, ref, v & extra)); rows.append(r)
    S = pd.DataFrame(rows); S.to_csv(TAB / "p95s_unosat_scores.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(S[S.stratum == "all"].drop(columns=["stratum"]).to_string(index=False))
    print(S[(S.stratum != "all") & S.comparison.str.startswith("new water vs")].drop(columns=["comparison"]).to_string(index=False))
    # ---- Michurina street on the vectors ---------------------------------------------------------------------------------------
    polys, streets, places, _ts = R.osm_layers(to_xy)
    mich = unary_union([LineString(s_) for s_ in streets]); mrows = []
    for k in ("flood", "water", "outside_bed", "urban_affected", "urban_analysed"):
        gk = geo[k]; inter = mich.intersection(gk)
        mrows.append(dict(source=f"UNOSAT {PRODUCT} / ICEYE {day} 12:18-13:01 UTC", layer=LAYERS[k], street_length_m=round(mich.length, 0), street_inside_m=round(inter.length, 0),
                          min_distance_m=round(mich.distance(gk), 1)))
    from scipy import ndimage
    sraster = features.rasterize([(mich, 1)], out_shape=g.shape, transform=g.transform, fill=0, all_touched=True, dtype="uint8").astype(bool)
    for nm_, m_ in (("reconstruction new water (nominal, 20 m cells)", new), ("reconstruction total water P_t (nominal)", pot), ("reconstruction new water, ensemble P >= 0.05", Pm >= 0.05)):
        rs_, cs_ = np.nonzero(sraster); r0, r1, c0, c1 = max(rs_.min() - 200, 0), rs_.max() + 200, max(cs_.min() - 200, 0), cs_.max() + 200
        d_ = ndimage.distance_transform_edt(~m_[r0:r1, c0:c1]) * g.cell
        mrows.append(dict(source=f"p95 rev 8, {day}", layer=nm_, street_length_m=round(mich.length, 0), street_inside_m=round(float((m_ & sraster).sum()) * g.cell, 0),
                          min_distance_m=round(float(d_[sraster[r0:r1, c0:c1]].min()), 1)))
    MS = pd.DataFrame(mrows); MS.to_csv(TAB / "p95s_unosat_michurina.csv", index=False); print(MS.to_string(index=False))
    # ---- residential areas of the two villages (OSM state of 5 June 2023): share under water -------------------------------------
    from shapely.geometry import Polygon
    vrows = []
    for vn, pl in polys.items():
        rp = unary_union([Polygon(p_).buffer(0) for p_ in pl]); rr = features.rasterize([(rp, 1)], out_shape=g.shape, transform=g.transform, fill=0, dtype="uint8").astype(bool)
        row = dict(village=vn, residential_km2=round(rp.area / 1e6, 3))
        for k in ("flood", "urban_affected"):
            row[f"ICEYE_{k}_share"] = round(rp.intersection(geo[k]).area / rp.area, 3)
        row["ICEYE_flood_or_urban_affected_share"] = round(rp.intersection(unary_union([geo["flood"], geo["urban_affected"]])).area / rp.area, 3)
        row["reconstruction_new_share"] = round(float((new & rr).sum() / rr.sum()), 3); row["reconstruction_total_share"] = round(float((pot & rr).sum() / rr.sum()), 3)
        row["ensemble_P>=0.05_share"] = round(float(((Pm >= 0.05) & rr).sum() / rr.sum()), 3); vrows.append(row)
    VS = pd.DataFrame(vrows); VS.to_csv(TAB / "p95s_unosat_villages.csv", index=False); print(VS.to_string(index=False))
    # ---- later layers of the same product: Landsat-9 water of 9 June, the multi-sensor flood of 6-9 June (maximum observed) -----------
    days_ = {}
    for dd in ("2023-06-08", "2023-06-09"):
        pt, _ = P95.potential_mosaic(M, W, Z, dd, "connected_ceiling", margin=margin, connectivity=conn, seed=seed); days_[dd] = pt
    mem9 = O.compose_npz(M, "_connected_ceiling_memory", "2023-06-09")                  # D-MEMORY sensitivity: retained water (never primary)
    ever78 = new | (days_["2023-06-08"] & ~baseline)
    lrows = []
    for wn, bb in WINDOWS.items():
        win = np.ones(g.shape, bool)
        if bb is not None:
            if bb[0] == "box":
                cx, cy = to_xy(bb[1], bb[2]); x0, x1, y0, y1 = cx - bb[3] * 1e3, cx + bb[3] * 1e3, cy - bb[4] * 1e3, cy + bb[4] * 1e3
            else:
                (x0, y0), (x1, y1) = to_xy(bb[0], bb[1]), to_xy(bb[2], bb[3])
            win = ((xs >= x0) & (xs <= x1))[None, :] & ((ys >= y0) & (ys <= y1))[:, None]
        a = lambda m: round(float((m & win & M["base"]).sum()) * P95.CELL_KM2, 2)
        for k in ("l9_0609_water", "cumulative_0606_0609"):
            r = ras[k]
            lrows.append(dict(window=wn, layer=LAYERS[k], observed_km2=a(r), on_prebreach_water_km2=a(r & baseline), in_our_new_water_7_or_8_june_km2=a(r & ever78),
                              in_primary_total_water_9_june_km2=a(r & days_["2023-06-09"]), in_memory_variant_9_june_km2=(a(r & mem9) if mem9 is not None else np.nan),
                              elsewhere_km2=a(r & ~ever78 & ~baseline), our_new_7_or_8_june_km2=a(ever78), share_of_our_7_8_june_new_covered=round(a(r & ever78) / max(a(ever78), 1e-9), 3)))
    LS = pd.DataFrame(lrows); LS.to_csv(TAB / "p95s_unosat_later_layers.csv", index=False); print(LS.to_string(index=False))
    pot_poly = None
    # ---- figure: the two local windows ------------------------------------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from floodstate_eo.visualization import figstyle as FS
    rgb = []
    for i in range(3):
        arrs = {}
        for z in M["names"]:
            with rasterio.open(bulk / "truecolour" / f"{z}_s2_2022-06-13_20m.tif") as s:
                arrs[z] = s.read(i + 1)
        rgb.append(g.compose(arrs, 0, order=M["names"], dtype="u1"))
    rgb = np.stack(rgb, -1)
    code = np.zeros(g.shape, "u1"); m_ = dom & dry_both
    code[m_ & new & ras["flood"]] = 1; code[m_ & new & ~ras["flood"]] = 2; code[m_ & ~new & ras["flood"]] = 3; code[(pot & baseline) & dom] = 4
    code[new & M["base"] & ~ras["aoi"]] = 5                                             # outside the ICEYE analysis extent: not scored
    cols = {1: "#2a78d6", 2: "#eda100", 3: "#e0249a", 4: "#16324f", 5: "#a6cee3"}
    fig, axs = plt.subplots(1, 2, figsize=(16, 7.4), constrained_layout=True)
    kx, ky = to_xy(32.9831722, 46.7083793)
    for ax, wn in zip(axs, ("Kozachi Laheri village", "Krynky + lowland south of Krynky")):
        bb = WINDOWS[wn]; (x0, y0), (x1, y1) = to_xy(bb[0], bb[1]), to_xy(bb[2], bb[3])
        cs_ = np.nonzero((xs >= x0) & (xs <= x1))[0]; rs_ = np.nonzero((ys >= y0) & (ys <= y1))[0]; sl = (slice(rs_.min(), rs_.max() + 1), slice(cs_.min(), cs_.max() + 1))
        ext = (xs[cs_.min()] / 1e3 - 0.01, xs[cs_.max()] / 1e3 + 0.01, ys[rs_.max()] / 1e3 - 0.01, ys[rs_.min()] / 1e3 + 0.01)
        ax.imshow(rgb[sl], extent=ext, interpolation="nearest", zorder=0)
        for k_, col in cols.items():
            ax.imshow(np.where(code[sl] == k_, 1, np.nan), extent=ext, cmap=ListedColormap([col]), alpha=0.8, interpolation="nearest", zorder=1)
        ax.contour(ras["aoi"][sl].astype("f4"), levels=[0.5], colors=["k"], linewidths=1.0, linestyles="--", extent=ext, origin="upper", zorder=2)
        if "lowland" in wn:
            bx = WINDOWS["lowland box (p95p/p95q)"]; cx, cy = to_xy(bx[1], bx[2])
            ax.add_patch(__import__("matplotlib.patches", fromlist=["Rectangle"]).Rectangle(((cx - bx[3] * 1e3) / 1e3, (cy - bx[4] * 1e3) / 1e3), 2 * bx[3], 2 * bx[4],
                                                                                           fill=False, ec="#e34948", lw=1.0, ls=":", zorder=3))
        for p_ in [q for pl in polys.values() for q in pl]:
            q = np.array(p_) / 1e3; ax.plot(q[:, 0], q[:, 1], color="white", lw=0.5, zorder=3)
        for s_ in streets:
            q = s_ / 1e3; ax.plot(q[:, 0], q[:, 1], color="#ff3b30", lw=2.0, zorder=4)
        ax.plot(kx / 1e3, ky / 1e3, "*", ms=9, mfc="white", mec="k", zorder=5)
        r_ = S[(S.window == wn) & (S.stratum == "all") & S.comparison.str.startswith("new water vs")].iloc[0]
        ax.text(0.01, 0.99, f"{wn}, {day}: our new water vs ICEYE flood (dry-before ground)\nPOD {r_.POD:.2f}  FAR {r_.FAR:.2f}  CSI (IoU) {r_.CSI:.2f}  "
                f"area bias {r_.area_bias:.2f}\nours {r_.model_km2:.2f} km2, ICEYE {r_.unosat_km2:.2f} km2", transform=ax.transAxes, va="top", fontsize=7,
                bbox=dict(fc="white", ec="none", alpha=0.85), zorder=6)
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.tick_params(labelsize=6); ax.set_title(wn, fontsize=8)
        FS.scale_bar(ax, 1000 if "village" in wn else 5000, units_per_m=1e-3)
    fig.legend(handles=[Patch(fc=cols[1], label="new water in both (hit)"), Patch(fc=cols[2], label="new water in the reconstruction only (false alarm or SAR-blind)"),
                        Patch(fc=cols[3], label="ICEYE flood only (miss)"), Patch(fc=cols[4], label="pre-breach water inside P_t"),
                        Patch(fc=cols[5], label="new water outside the ICEYE analysis extent (not scored)"), Line2D([], [], color="k", ls="--", lw=1, label="ICEYE analysis extent"),
                        Line2D([], [], color="#e34948", ls=":", lw=1, label="lowland box (p95p, p95q)"),
                        Line2D([], [], color="#ff3b30", lw=2, label="Michurina street (OSM, state of 5 June 2023)"), Line2D([], [], color="white", lw=1, label="residential areas (OSM)")],
               loc="lower center", ncol=3, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.08))
    fig.suptitle(f"Reconstruction (p95 rev 8, nominal world) vs UNOSAT flood extent from ICEYE, {day} 12:18-13:01 UTC (product {PRODUCT}, CC BY-SA). "
                 "Basemap: Sentinel-2 L2A 13 June 2022 (contains modified Copernicus Sentinel data 2022); OSM (c) OpenStreetMap contributors (ODbL)", fontsize=7.5)
    FIG.mkdir(parents=True, exist_ok=True); fig.savefig(FIG / f"p95s_unosat_{day.replace('-', '')}.png", dpi=170, bbox_inches="tight"); plt.close(fig)
    info = json.loads((bulk / "external" / "unosat" / PRODUCT / "utm" / "layers.json").read_text())
    (TAB / "p95s_unosat_manifest.json").write_text(json.dumps(dict(producer="p95s_unosat_crosscheck.py", day=day, product=info, windows=WINDOWS, strata=STRATA,
        scored="ICEYE analysis extent inside the reconstruction domain; new water on ground dry before the breach in our baseline AND UNOSAT's Sentinel-2 reference",
        gate=f"recomputed new water == daily_new.npz ({diff:.3f} km2)", grid="20 m union grid, cell centres (rasterio.features.rasterize)", unused=pot_poly), indent=1))
    print("->", TAB / "p95s_unosat_scores.csv", round(time.time() - t0), "s")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--step", choices=["convert", "compare"], required=True); ap.add_argument("--day", default="2023-06-07")
    ap.add_argument("--bulk", default=None, help="bulk root (the convert step runs in the SWOT-DNIPRO venv, where floodstate_eo may not import)")
    a = ap.parse_args()
    bulk = Path(a.bulk) if a.bulk else bulk_root()
    step_convert(bulk) if a.step == "convert" else step_compare(bulk, a.day)


if __name__ == "__main__":
    main()
