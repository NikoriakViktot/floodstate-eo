# New in floodstate-eo, 2026-09-30 (maintainer: multi-date EO recession test of the frozen variants, no parameter fitted). STATUS: ACTIVE. Diagnostic.
"""P95t -- the recession of new water after the peak: satellite-observed (UNOSAT 3614 layers of 7, 9, 13 and 21 June 2023) against the frozen
reconstruction variants (the primary 'connected_ceiling', the D-MEMORY sensitivity 'connected_ceiling_memory' and the ensemble expectation of
p95e cellprob). Nothing is tuned on these observations: the test asks which existing mechanism reproduces the observed decay.

Observations (one sensor per date; the product holds the whole activation FL20230606UKR):
  7 June   ICEYE X-band SAR, 12:18-13:01 UTC          analysis extent of the product
  9 June   Landsat-9 optical 30 m                     NO analysis extent / cloud layer in the product: the 9 June analysis extent of the
                                                      activation (Sentinel-3 / Sentinel-2) is taken as its footprint -- an assumption
           Sentinel-3 optical 300 m (sensitivity)     same extent; coarse
  13 June  Sentinel-2 optical, 08:57 UTC              analysis extent minus the product's cloud obstruction
  21 June  Sentinel-1 C-band SAR                      analysis extent
New water (EO and model alike) = water on ground dry before the breach in both references (our baseline and UNOSAT's Sentinel-2 pre-event water),
inside the reconstruction domain. Masks: per date (what that sensor observed), common to all four dates, and common to 9, 13 and 21 June (the
post-connection phase; far larger in the lowland, whose north only ICEYE saw). Units: the corridor (whole domain), the floodplain lowland south
of Krynky (the p95p / p95q box), Krynky village; corridor strata: open ground (grass, cropland, bare), wetland, trees and shrub, built-up.
Per series: A(t), R(t) = A(t) / max_t A, and the e-folding time tau of ln A(t) after the series' maximum (>= 2 positive points; with four
dates and four sensors tau is indicative only). Sensors differ (SAR is blind under canopy, optical under cloud and canopy): read the
open-ground stratum first; the areas are exact on the 20 m union grid (cell centres).
Outputs: tables/p95t_recession_series.csv, p95t_recession_tau.csv, p95t_manifest.json; figures/m6_v003A/p95t_recession.png, p95t_lowland_maps.png
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRODUCT = "3614"
EO = {  # key: (date, sensor, water layer, analysis-extent layer or None, cloud layer or None)
    "07_ICEYE": ("2023-06-07", "ICEYE X-band SAR 12:18-13:01 UTC", "ICEYE_20230607_WaterExtent_KhersonskaOblast_UKR", "ICEYE_20230607_AnalysisExtent_KhersonskaOblast_UKR", None),
    "09_L9": ("2023-06-09", "Landsat-9 optical 30 m", "L9_20230609_WaterExtent_KhersonskaOblast_UKR", "ST3_20230609_ST2_20230608_AnalysisExtent_KhersonskaOblast_UKR", None),
    "09_S3": ("2023-06-09", "Sentinel-3 optical 300 m (sensitivity)", "ST3_20230609_WaterExtent_KhersonskaOblast_UKR", "ST3_20230609_ST2_20230608_AnalysisExtent_KhersonskaOblast_UKR", None),
    "13_S2": ("2023-06-13", "Sentinel-2 optical 08:57 UTC", "ST2_20230613_WaterExtent_KhersonskaOblast_UKR", "ST2_20230613_AnalysisExtent_KhersonskaOblast_UKR",
              "ST2_20230613_CloudObstruction_KhersonskaOblast_UKR"),
    "21_S1": ("2023-06-21", "Sentinel-1 C-band SAR", "ST1_20230621_WaterExtent_KhersonskarOblast_UKR", "ST1_20230621_AnalysisExtent_KhersonskarOblast_UKR", None),
}
PRIMARY = ("07_ICEYE", "09_L9", "13_S2", "21_S1"); POST = ("09_L9", "13_S2", "21_S1")
REF = "ST2_20230603_20230605_WaterExtent_KhersonskaOblast_UKR"
STRATA = {"all": None, "open ground": (30, 40, 60), "wetland": (90,), "trees and shrub": (10, 20), "built-up": (50,)}


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def utm_dir(bulk):
    return bulk / "external" / "unosat" / PRODUCT / "utm"


def step_convert(bulk: Path):
    import geopandas as gpd
    shp = bulk / "external" / "unosat" / PRODUCT / "FL20230606UKR_SHP"; out = utm_dir(bulk); out.mkdir(parents=True, exist_ok=True)
    names = {REF} | {v for e in EO.values() for v in e[2:] if v}
    for nm in sorted(names):
        g = gpd.read_file(shp / f"{nm}.shp").to_crs(32636); g[["geometry"]].to_file(out / f"{nm}.geojson", driver="GeoJSON")
        print(nm, round(float(g.area.sum()) / 1e6, 1), "km2", flush=True)


def tau_fit(days, A, floor=0.05):
    """e-folding time (days) of ln A after the series' maximum, from the positive points (>= floor km2)."""
    days, A = np.asarray(days, float), np.asarray(A, float)
    if not np.isfinite(A).any():
        return np.nan, 0
    k = int(np.nanargmax(A)); t, a = days[k:], A[k:]; ok = np.isfinite(a) & (a >= floor)
    if ok.sum() < 2:
        return np.nan, int(ok.sum())
    b = np.polyfit(t[ok], np.log(a[ok]), 1)[0]
    return (round(float(-1.0 / b), 1) if b < 0 else np.inf), int(ok.sum())


def step_compare(bulk: Path):
    import pandas as pd
    from rasterio import features
    from rasterio.warp import transform as tf_transform
    from shapely.geometry import shape
    from shapely.ops import unary_union
    from floodstate_eo import _kakhovka_legacy_config as CFG
    t0 = time.time(); TAB = ROOT / "tables"; FIG = ROOT / "figures" / "m6_v003A"; sfx = "_connected_ceiling"
    O = _ld("p95o", HERE / "p95o_component_qa.py"); P95 = O._ld("p95_hand_daily_inundation"); P = P95.load_p92()
    man = O.load_manifest(sfx); M = P95.mosaic_layers(P, with_s1=False); g = M["grid"]
    _W, dxm, _ = O.engine_for(P95, man, sfx); M["base"] = M["base_geom"] & P95.dam_mask(M, dxm)
    baseline = O.compose_npz(M, sfx, "baseline"); wc = g.compose({z: L["wc"] for z, L in M["zones"].items()}, 0, order=M["names"], dtype="u1")
    ras = lambda nm: features.rasterize([(unary_union([shape(f["geometry"]) for f in json.loads((utm_dir(bulk) / f"{nm}.geojson").read_text())["features"]]), 1)],
                                        out_shape=g.shape, transform=g.transform, fill=0, dtype="uint8").astype(bool)
    dry_both = ~baseline & ~ras(REF) & M["base"]
    obs, water = {}, {}
    for k, (d, sensor, wl, al, cl) in EO.items():
        water[k] = ras(wl) & dry_both
        o = ras(al) if al else np.ones(g.shape, bool)
        if cl:
            o &= ~ras(cl)
        obs[k] = o & dry_both
        print(k, sensor, "observed dry-before km2", round(float(obs[k].sum()) * P95.CELL_KM2, 1), "EO new water km2", round(float((water[k] & obs[k]).sum()) * P95.CELL_KM2, 1), flush=True)
    model = {}
    for d in sorted({e[0] for e in EO.values()}):
        nom = O.compose_npz(M, sfx, d); mem = O.compose_npz(M, "_connected_ceiling_memory", d)
        n_draws = 1000.0
        import rasterio
        with rasterio.open(bulk / "floodplain_dyn" / f"ZONE_4_DAM_TO_KHERSON_FLOODWAY{sfx}" / f"p95e_cellprob_{d}.tif") as s:
            n_draws = float(s.tags().get("n_draws", 1000))
        Pm = O.compose_tif(M, sfx, f"p95e_cellprob_{d}.tif", 0, "u2").astype("f4") / n_draws
        model[d] = dict(nominal=nom, memory=mem, P=Pm)
    common_all = np.logical_and.reduce([obs[k] for k in PRIMARY]); common_post = np.logical_and.reduce([obs[k] for k in POST])
    to_xy = lambda lon, lat: tuple(float(v[0]) for v in tf_transform("EPSG:4326", CFG.CRS_METRIC, [lon], [lat]))
    xs, ys = M["xs"], M["ys"]; cx, cy = to_xy(33.12, 46.665)
    (kx0, ky0), (kx1, ky1) = to_xy(33.07, 46.728), to_xy(33.17, 46.765)
    units = {"corridor": np.ones(g.shape, bool),
             "lowland south of Krynky (box)": (np.abs(xs - cx) <= 6500)[None, :] & (np.abs(ys - cy) <= 7000)[:, None],
             "Krynky village": ((xs >= kx0) & (xs <= kx1))[None, :] & ((ys >= ky0) & (ys <= ky1))[:, None]}
    c = P95.CELL_KM2; rows = []
    for un, um in units.items():
        for sn, codes in STRATA.items():
            if un != "corridor" and sn not in ("all", "open ground"):
                continue
            st = np.ones(g.shape, bool) if codes is None else np.isin(wc, codes)
            for mt, mm in (("per date", None), ("common 7-9-13-21", common_all), ("common 9-13-21", common_post)):
                for k, (d, sensor, *_r) in EO.items():
                    if mt == "common 9-13-21" and k == "07_ICEYE":
                        continue
                    dom = um & st & (obs[k] if mm is None else mm & obs[k])
                    if dom.sum() < 25:
                        continue
                    e = water[k] & dom; r = dict(unit=un, stratum=sn, mask=mt, date=d, eo=k, sensor=sensor, observed_km2=round(float(dom.sum()) * c, 2), A_EO_km2=round(float(e.sum()) * c, 2))
                    for vn in ("nominal", "memory"):
                        mdl = model[d][vn] & dom; tp = float((mdl & e).sum()); fp = float((mdl & ~e).sum()); fn = float((~mdl & e).sum())
                        r[f"A_{vn}_km2"] = round(float(mdl.sum()) * c, 2); r[f"CSI_{vn}"] = round(tp / (tp + fp + fn), 3) if tp + fp + fn else np.nan
                        r[f"POD_{vn}"] = round(tp / (tp + fn), 3) if tp + fn else np.nan; r[f"FAR_{vn}"] = round(fp / (tp + fp), 3) if tp + fp else np.nan
                    r["A_ensemble_expected_km2"] = round(float(model[d]["P"][dom].sum()) * c, 2); r["A_ensemble_P50_km2"] = round(float((model[d]["P"][dom] >= 0.5).sum()) * c, 2)
                    rows.append(r)
    S = pd.DataFrame(rows); S.to_csv(TAB / "p95t_recession_series.csv", index=False)
    # R(t) and tau on the common masks, the primary EO series (L9 on 9 June) and the S3 sensitivity
    day_of = lambda d: (pd.Timestamp(d) - pd.Timestamp("2023-06-07")).days
    trows = []
    for (un, sn, mt), gdf in S[S["mask"] != "per date"].groupby(["unit", "stratum", "mask"]):
        for var, eo_keys in (("primary (9 June = Landsat-9)", PRIMARY if mt == "common 7-9-13-21" else POST),
                             ("sensitivity (9 June = Sentinel-3)", tuple("09_S3" if k == "09_L9" else k for k in (PRIMARY if mt == "common 7-9-13-21" else POST)))):
            sub = gdf[gdf.eo.isin(eo_keys)].sort_values("date")
            if len(sub) < 2:
                continue
            days = [day_of(d) for d in sub.date]
            for col, lab in (("A_EO_km2", "EO"), ("A_nominal_km2", "nominal"), ("A_memory_km2", "memory"), ("A_ensemble_expected_km2", "ensemble expected")):
                A = sub[col].to_numpy(float); tau, npts = tau_fit(days, A); amax = np.nanmax(A)
                trows.append(dict(unit=un, stratum=sn, mask=mt, eo_series=var, series=lab, **{f"A_{d[5:]}": a for d, a in zip(sub.date, A)},
                                  **{f"R_{d[5:]}": (round(a / amax, 3) if amax > 0 else np.nan) for d, a in zip(sub.date, A)}, tau_days=tau, tau_points=npts))
    TT = pd.DataFrame(trows); TT.to_csv(TAB / "p95t_recession_tau.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 300); pd.set_option("display.max_columns", 30)
    show = TT[TT.eo_series.str.startswith("primary")].drop(columns=["eo_series"])
    print(show.to_string(index=False))
    # ---- figures ----------------------------------------------------------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    panels = [("lowland south of Krynky (box)", "all", "common 9-13-21"), ("lowland south of Krynky (box)", "open ground", "common 9-13-21"),
              ("Krynky village", "all", "common 7-9-13-21"), ("corridor", "open ground", "common 7-9-13-21"), ("corridor", "wetland", "common 7-9-13-21"),
              ("corridor", "all", "common 7-9-13-21")]
    sty = {"A_EO_km2": ("k", "o", "-", "observed (UNOSAT: ICEYE 7, Landsat-9 9, S2 13, S1 21 June)"), "A_nominal_km2": ("#2a78d6", "s", "-", "reconstruction, primary"),
           "A_memory_km2": ("#7f7f7f", "^", "--", "reconstruction, retained water (D-MEMORY)"), "A_ensemble_expected_km2": ("#eda100", "d", ":", "ensemble expectation (sum of P)")}
    fig, axs = plt.subplots(2, 3, figsize=(15, 8.4), constrained_layout=True); axs = axs.ravel()
    for ax, (un, sn, mt) in zip(axs, panels):
        sub = S[(S.unit == un) & (S.stratum == sn) & (S["mask"] == mt) & S.eo.isin(PRIMARY)].sort_values("date")
        s3 = S[(S.unit == un) & (S.stratum == sn) & (S["mask"] == mt) & (S.eo == "09_S3")]
        t = pd.to_datetime(sub.date)
        for col, (colr, mk, ls, lab) in sty.items():
            ax.plot(t, sub[col], color=colr, marker=mk, ls=ls, lw=1.5, ms=5, label=lab)
        if len(s3):
            ax.plot(pd.to_datetime(s3.date), s3.A_EO_km2, "x", color="k", ms=7, label="observed 9 June, Sentinel-3 300 m (sensitivity)")
        ax.set_title(f"{un} | {sn} | mask {mt} ({sub.observed_km2.max():.0f} km2 observed, dry before)", fontsize=7.5)
        ax.set_ylabel("new water, km2", fontsize=7); ax.tick_params(labelsize=6.5); ax.grid(alpha=0.3); ax.set_ylim(bottom=0)
    axs[0].legend(fontsize=6, loc="upper right")
    fig.suptitle("Recession of new water after the peak: satellite observations (UNOSAT 3614) vs the frozen reconstruction variants -- nothing fitted. "
                 "One sensor per date: read the open-ground panels first (SAR and optical are both blind under canopy).", fontsize=8)
    FIG.mkdir(parents=True, exist_ok=True); fig.savefig(FIG / "p95t_recession.png", dpi=160); plt.close(fig)
    # lowland maps on the post-connection dates
    from matplotlib.colors import ListedColormap
    rs_, cs_ = np.nonzero(units["lowland south of Krynky (box)"]); sl = (slice(rs_.min(), rs_.max() + 1), slice(cs_.min(), cs_.max() + 1))
    ext = (xs[cs_.min()] / 1e3, xs[cs_.max()] / 1e3, ys[rs_.max()] / 1e3, ys[rs_.min()] / 1e3)
    fig, axs = plt.subplots(1, 4, figsize=(17, 5.2), constrained_layout=True)
    for ax, k in zip(axs, PRIMARY):
        d = EO[k][0]; nom, mem = model[d]["nominal"][sl], model[d]["memory"][sl]; e = water[k][sl]; ob = obs[k][sl]
        ax.imshow(np.where(~ob, 1, np.nan), extent=ext, cmap=ListedColormap(["#e6e6e6"]), interpolation="nearest")
        ax.imshow(np.where(mem & ~nom, 1, np.nan), extent=ext, cmap=ListedColormap(["#9e9e9e"]), interpolation="nearest")
        ax.imshow(np.where(nom, 1, np.nan), extent=ext, cmap=ListedColormap(["#2a78d6"]), interpolation="nearest")
        ax.imshow(np.where(e & ob, 1, np.nan), extent=ext, cmap=ListedColormap(["#e0249a"]), alpha=0.75, interpolation="nearest")
        r = S[(S.unit == "lowland south of Krynky (box)") & (S.stratum == "all") & (S["mask"] == "per date") & (S.eo == k)].iloc[0]
        ax.set_title(f"{d}: {EO[k][1]}\nobserved {r.A_EO_km2:.1f} | primary {r.A_nominal_km2:.1f} | memory {r.A_memory_km2:.1f} km2 (on {r.observed_km2:.0f} km2 seen)", fontsize=7)
        ax.tick_params(labelsize=6)
    fig.legend(handles=[matplotlib.patches.Patch(fc="#e0249a", alpha=0.75, label="observed new water (UNOSAT)"), matplotlib.patches.Patch(fc="#2a78d6", label="primary reconstruction"),
                        matplotlib.patches.Patch(fc="#9e9e9e", label="retained water, memory variant only"), matplotlib.patches.Patch(fc="#e6e6e6", label="not observed by that sensor / cloud / pre-event water")],
               loc="lower center", ncol=4, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.07))
    fig.suptitle("Lowland south of Krynky (p95p/p95q box): new water per date, observed vs the frozen variants", fontsize=8)
    fig.savefig(FIG / "p95t_lowland_maps.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    (TAB / "p95t_manifest.json").write_text(json.dumps(dict(producer="p95t_eo_recession.py", product=PRODUCT, eo={k: list(v) for k, v in EO.items()}, reference=REF,
        primary_series=PRIMARY, post_series=POST, strata=STRATA, masks="per date / common to 7-9-13-21 / common to 9-13-21, all on ground dry before the breach in both references",
        assumption="Landsat-9 has no analysis extent or cloud layer in the product: the 9 June analysis extent of the activation stands for it",
        fitted="nothing: frozen variants (primary, D-MEMORY sensitivity, p95e ensemble) compared as they are"), indent=1))
    print("->", TAB / "p95t_recession_series.csv", round(time.time() - t0), "s")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--step", choices=["convert", "compare"], required=True)
    ap.add_argument("--bulk", default=None, help="bulk root (the convert step runs in the SWOT-DNIPRO venv)")
    a = ap.parse_args()
    if a.bulk:
        bulk = Path(a.bulk)
    else:
        from floodstate_eo import _kakhovka_legacy_config as CFG
        bulk = CFG.BULK_ROOT
    step_convert(bulk) if a.step == "convert" else step_compare(bulk)


if __name__ == "__main__":
    main()
