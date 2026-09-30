# New in floodstate-eo, 2026-09-29 (review F02 / F07, maintainer's terrain-model correction). STATUS: ACTIVE.
"""P95j -- FABDEM-DTM residual statistics and the empirical semivariogram against night ICESat-2 ground, per zone and
WorldCover class, on FABDEM-SOURCED cells of the seamless terrain-bed model only.

The terrain layer of the reconstruction is FABDEM (a bare-earth DTM) outside the surveyed channel and the observed /
reconstructed bed inside it (p55 source codes 3/4 vs 1/2/5). The two are different products with different error structures,
so the residual population that feeds the terrain-uncertainty model of p95/p95e is restricted to source in (3, 4): the
floodplain terrain that the FABDEM residual statistics can describe. Bed cells get no FABDEM statistics (a stated limitation).

    r_i      = z_FABDEM(x_i) - z_ICESat2,ground(x_i)                (both EVRF2019; p57 QC: night, gnd_ph_count >= 8, snow-free,
                                                                     outside the former pool, WorldCover != water)
    b_c      = median(r_i | class c)          residual class-dependent terrain-elevation bias (removed in p95, FABDEM cells only)
    sigma_c  = NMAD(r_i | class c)            marginal scale of the perturbed terrain realizations (p95e)
    gamma(h) = 0.5 E[(r'_i - r'_j)^2 | |x_i - x_j| = h],  r' = r - b_c, pairs of the SAME acquisition date (along-track),
               lags 20 m .. 3 km; fitted with gamma(h) = c0 + s2 (1 - exp(-h / L)): L = correlation range used by p95e
    r''      = (r - b_c) / sigma_c           standardized residual: the unit field F of the perturbation model eps = sigma_c F
The correlation structure used by p95e is fitted to the POOLED standardized residuals with the robust Cressie-Hawkins
estimator (consistent with the NMAD scale; its sill should come out near 1): range L and nugget share c0 / (c0 + s2).
Class-specific (classical) fits are reported; sigma_c per class with the pooled correlation is a stated modelling
assumption, not a measured class-specific covariance. The nugget includes the ICESat-2 segment noise and the point-to-cell
support mismatch, so it is an upper bound of the cell-level white error (p95e ablation: no nugget). 500 m only as a fallback.

Consistency: the pooled per-zone statistics are printed next to the p57 (Paper 2) rows 'A source DEM, <zone>' and 'A FABDEM,
WorldCover <class>' -- same chain, but p57 pools its frames (incl. the estuary) and samples the p56 FABDEM raster, so the
numbers are expected to agree in sign and order, not to the last digit.

Runs in the SWOT-DNIPRO environment (p57 needs geopandas): PYTHONPATH=src $SWOT_DNIPRO_ROOT/.venv/bin/python -m ... or
    PYTHONPATH=src ~/repo/SWOT-DNIPRO/.venv/bin/python case_studies/kakhovka_2023/workflows/m6/p95j_terrain_variogram.py
Outputs: <case_study>/tables/p95j_terrain_residual_stats.csv (zone x class + POOLED; N, median, NMAD, RMSE, n_dates),
         p95j_terrain_residual_variogram.csv (bins), p95j_terrain_variogram_fit.csv (c0, s2, L per zone/class + pooled),
         p95j_manifest.json; <case_study>/figures/m6_v003A/p95j_variogram.png
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from scipy.optimize import curve_fit
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.terrain.vertical import assert_same_vertical_frame

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = ROOT / "figures" / "m6_v003A"
ZONES = ("ZONE_4_DAM_TO_KHERSON_FLOODWAY", "ZONE_2_KHERSON_DELTA")
WC = {10: "trees", 30: "grass", 40: "cropland", 50: "built", 60: "bare", 90: "wetland"}
FABDEM_SOURCES = (3, 4)
BINS_M = np.array([0, 30, 50, 75, 100, 150, 200, 300, 400, 500, 700, 1000, 1500, 2000, 3000.0])
MAX_PAIRS_PER_DATE = 4_000_000


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def nmad(r):
    r = np.asarray(r, float); return float(1.4826 * np.median(np.abs(r - np.median(r))))


def stats(r, **k):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    return dict(N=int(len(r)), median=round(float(np.median(r)), 3) if len(r) else np.nan, NMAD=round(nmad(r), 3) if len(r) else np.nan,
                RMSE=round(float(np.sqrt((r ** 2).mean())), 3) if len(r) else np.nan, mean=round(float(r.mean()), 3) if len(r) else np.nan, **k)


def semivariogram(x, y, r, dates, rng, max_pairs=MAX_PAIRS_PER_DATE):
    """Empirical semivariograms of r over pairs of the SAME date within BINS_M: classical (Matheron) and robust
    (Cressie-Hawkins). Returns (bin lo, hi, gamma_classical, gamma_robust, n_pairs)."""
    n = len(BINS_M) - 1; num = np.zeros(n); num_ch = np.zeros(n); cnt = np.zeros(n, "i8")
    for d in np.unique(dates):
        m = dates == d
        if m.sum() < 2:
            continue
        pts = np.c_[x[m], y[m]]; rr = r[m]; tree = cKDTree(pts)
        pairs = tree.query_pairs(BINS_M[-1], output_type="ndarray")
        if len(pairs) == 0:
            continue
        if len(pairs) > max_pairs:
            pairs = pairs[rng.choice(len(pairs), max_pairs, replace=False)]
        h = np.hypot(pts[pairs[:, 0], 0] - pts[pairs[:, 1], 0], pts[pairs[:, 0], 1] - pts[pairs[:, 1], 1])
        dr = rr[pairs[:, 0]] - rr[pairs[:, 1]]
        b = np.digitize(h, BINS_M) - 1; ok = (b >= 0) & (b < n)
        num += np.bincount(b[ok], weights=0.5 * dr[ok] ** 2, minlength=n); num_ch += np.bincount(b[ok], weights=np.sqrt(np.abs(dr[ok])), minlength=n)
        cnt += np.bincount(b[ok], minlength=n)
    with np.errstate(invalid="ignore", divide="ignore"):
        gam = num / cnt
        gam_ch = (num_ch / cnt) ** 4 / (2.0 * (0.457 + 0.494 / cnt))          # Cressie & Hawkins (1980), semivariance
    return BINS_M[:-1], BINS_M[1:], gam, gam_ch, cnt


def _wls_sigma(gam, cnt):
    """Cressie (1985) weighted least squares: weight N(h) / gamma(h)^2, i.e. curve_fit sigma = gamma / sqrt(N)."""
    return np.maximum(gam, 1e-6) / np.sqrt(cnt)


def fit_exponential(h, gam, cnt, sigma2_hint):
    """gamma(h) = c0 + s2 (1 - exp(-h / L)) by Cressie WLS; returns dict(c0, s2, L_m, fit_rmse, n_bins, status)."""
    ok = np.isfinite(gam) & (cnt >= 200)
    if ok.sum() < 4:
        return dict(c0=np.nan, s2=np.nan, L_m=np.nan, fit_rmse=np.nan, n_bins=int(ok.sum()), status="too few bins")
    f = lambda hh, c0, s2, L: c0 + s2 * (1.0 - np.exp(-hh / L))
    try:
        p, _ = curve_fit(f, h[ok], gam[ok], p0=[0.0, max(sigma2_hint, 1e-3), 300.0], bounds=([0.0, 0.0, 10.0], [np.inf, np.inf, 20000.0]),
                         sigma=_wls_sigma(gam[ok], cnt[ok]), maxfev=20000)
    except RuntimeError as e:                                                # noqa: BLE001
        return dict(c0=np.nan, s2=np.nan, L_m=np.nan, fit_rmse=np.nan, n_bins=int(ok.sum()), status=f"fit failed: {e}")
    res = (gam[ok] - f(h[ok], *p)) / gam[ok]
    return dict(c0=round(float(p[0]), 4), s2=round(float(p[1]), 4), L_m=round(float(p[2]), 1), fit_rmse=round(float(np.sqrt((res ** 2).mean())), 4), n_bins=int(ok.sum()), status="ok")


def fit_nested(h, gam, cnt):
    """gamma(h) = c0 + s1 (1 - exp(-h / L1)) + s2 (1 - exp(-h / L2)), L1 in [10, 300] m, L2 in [300, 20000] m, Cressie WLS.
    fit_rmse = RMS of the RELATIVE residual (as for the single model), so the two are comparable."""
    ok = np.isfinite(gam) & (cnt >= 200)
    if ok.sum() < 6:
        return dict(c0=np.nan, s1=np.nan, L1_m=np.nan, s2=np.nan, L2_m=np.nan, fit_rmse=np.nan, n_bins=int(ok.sum()), status="too few bins")
    f = lambda hh, c0, s1, L1, s2, L2: c0 + s1 * (1.0 - np.exp(-hh / L1)) + s2 * (1.0 - np.exp(-hh / L2))
    g = gam[ok]
    try:
        p, _ = curve_fit(f, h[ok], g, p0=[0.3 * g.min(), 0.4 * g.max(), 60.0, 0.5 * g.max(), 1000.0], bounds=([0.0, 0.0, 10.0, 0.0, 300.0], [np.inf, np.inf, 300.0, np.inf, 20000.0]),
                         sigma=_wls_sigma(g, cnt[ok]), maxfev=40000)
    except RuntimeError as e:                                                # noqa: BLE001
        return dict(c0=np.nan, s1=np.nan, L1_m=np.nan, s2=np.nan, L2_m=np.nan, fit_rmse=np.nan, n_bins=int(ok.sum()), status=f"fit failed: {e}")
    res = (g - f(h[ok], *p)) / g
    return dict(c0=round(float(p[0]), 4), s1=round(float(p[1]), 4), L1_m=round(float(p[2]), 1), s2=round(float(p[3]), 4), L2_m=round(float(p[4]), 1),
                fit_rmse=round(float(np.sqrt((res ** 2).mean())), 4), n_bins=int(ok.sum()), status="ok")


def variograms(zone, D, rng, vrows, frows, t0):
    """Classical fits per class and for all classes (residual after the class median, metres) and the classical + robust fits
    of the STANDARDIZED residual (all classes; dimensionless) -- the latter is the correlation model of p95e."""
    dates = D.date.values.astype("datetime64[D]").astype("i8")
    jobs = [("all", "rc", np.ones(len(D), bool))] + [(WC[code], "rc", (D.wc == code).values) for code in WC] + [("all_standardized", "rs", np.isfinite(D.rs.values))]
    for nm, col, sel in jobs:
        if sel.sum() < 2000:
            continue
        v = D[col].values
        lo, hi, gam, gam_ch, cnt = semivariogram(D.x.values[sel], D.y.values[sel], v[sel], dates[sel], rng)
        for l_, h_, g_, gc_, c_ in zip(lo, hi, gam, gam_ch, cnt):
            vrows.append(dict(zone=zone, wc_class=nm, lag_lo_m=l_, lag_hi_m=h_, lag_mid_m=(l_ + h_) / 2, gamma_m2=round(float(g_), 5) if np.isfinite(g_) else np.nan,
                              gamma_robust=round(float(gc_), 5) if np.isfinite(gc_) else np.nan, n_pairs=int(c_), units="1 (standardized)" if col == "rs" else "m2"))
        for est, g in (("classical", gam), ("cressie_hawkins", gam_ch)):
            if est == "cressie_hawkins" and col != "rs":
                continue
            fit = fit_exponential((lo + hi) / 2, g, cnt, nmad(v[sel]) ** 2)
            ok = fit["status"] == "ok" and (fit["c0"] + fit["s2"]) > 0
            frows.append(dict(zone=zone, wc_class=nm, estimator=est, model="exponential+nugget", N=int(sel.sum()), NMAD_after_bias=round(nmad(v[sel]), 3),
                              nugget_share=round(fit["c0"] / (fit["c0"] + fit["s2"]), 3) if ok else np.nan, **fit))
            print(zone, nm, est, "single", fit, round(time.time() - t0), "s", flush=True)
            if col == "rs":
                nf = fit_nested((lo + hi) / 2, g, cnt); okn = nf["status"] == "ok"
                sill = (nf["c0"] + nf["s1"] + nf["s2"]) if okn else np.nan
                frows.append(dict(zone=zone, wc_class=nm, estimator=est, model="nested_2exp+nugget", N=int(sel.sum()), NMAD_after_bias=round(nmad(v[sel]), 3),
                                  nugget_share=round(nf["c0"] / sill, 3) if okn and sill > 0 else np.nan, **nf))
                print(zone, nm, est, "nested", nf, flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=20260929); a = ap.parse_args()
    t0 = time.time(); rng = np.random.default_rng(a.seed)
    sd = Path(CFG._SWOT_DNIPRO_SIBLING); sys.path.insert(0, str(sd / "src")); sys.path.insert(0, str(sd / "scripts"))
    P57 = _ld("p57", sd / "scripts/p57_dem_accuracy_night.py")
    P, c = P57.load_points(); P = P[~P.in_former_pool].copy()
    PF = _ld("paper1_frame", Path(__file__).with_name("paper1_frame.py")); P["H_ice"] = PF.icesat_ground_to_paper1(P.H_ice.values)   # Paper 1 v6 frame
    print(f"night QC segments outside the former pool: {len(P):,} (c_EGG2015->EVRF2019 {c:+.3f}) {round(time.time() - t0)} s", flush=True)
    B = CFG.BULK_ROOT; rows, vrows, frows = [], [], []
    manifest = dict(seed=a.seed, qc="p57 load_points: night, gnd_ph_count >= 8, snow-free, |h_te| < 500 m, outside the former pool; WorldCover != water; source in (3, 4)",
                    support="ATL08 100 m segments (kakhovka pull) and 20 m segments (lower_dnipro / liman pulls) vs 20 m terrain cells")
    pooled = []
    for zone in ZONES:
        with rasterio.open(B / "dem_seamless" / f"{zone}_dem_evrf2019_20m.tif") as s:
            tag = s.tags().get("vertical_datum")
        assert_same_vertical_frame({"terrain raster tag": tag, "ICESat-2 ground (p57 chain)": "EVRF2019"})
        src = P57.sample(B / "dem_seamless" / f"{zone}_dem_source_20m.tif", P.x.values, P.y.values)
        seam = PF.fabdem_to_paper1(P57.sample(B / "dem_seamless" / f"{zone}_dem_evrf2019_20m.tif", P.x.values, P.y.values), src)
        wc = P57.sample(B / "worldcover_frames" / zone / "wc_2021_20m.tif", P.x.values, P.y.values)
        ok = np.isfinite(src) & np.isin(src, FABDEM_SOURCES) & np.isfinite(seam) & np.isfinite(wc) & (wc != 80)
        D = P[ok].copy(); D["r"] = seam[ok] - D.H_ice.values; D["wc"] = wc[ok].astype(int); D["src"] = src[ok].astype(int)
        D = D.drop_duplicates(subset=["date", "x", "y"])
        manifest[zone] = dict(n_points=int(len(D)), n_dates=int(D.date.dt.date.nunique()), by_source={int(k): int(v) for k, v in D.src.value_counts().items()},
                              bed_points_excluded=int((np.isfinite(src) & np.isin(src, (1, 2, 5))).sum()))
        rows.append(dict(zone=zone, wc_class="all", **stats(D.r, n_dates=int(D.date.dt.date.nunique()))))
        D["rc"] = np.nan
        for code, nm in WC.items():
            g = D[D.wc == code]
            if len(g) == 0:
                continue
            st = stats(g.r, n_dates=int(g.date.dt.date.nunique())); rows.append(dict(zone=zone, wc_class=nm, wc_code=code, **st))
            D.loc[g.index, "rc"] = g.r - st["median"]                        # class-median removed: the residual of the perturbation model
        D = D[np.isfinite(D.rc)].copy()
        sc = {code: nmad(D.rc.values[(D.wc == code).values]) for code in WC if (D.wc == code).any()}
        D["rs"] = D.rc / D.wc.map(sc)                                          # standardized: the unit field of eps = sigma_c F
        variograms(zone, D, rng, vrows, frows, t0)
        pooled.append(D.assign(zone=zone))
    PD = pd.concat(pooled, ignore_index=True)
    rows.append(dict(zone="POOLED", wc_class="all", **stats(PD.r, n_dates=int(PD.date.dt.date.nunique()))))
    for code, nm in WC.items():
        g = PD[PD.wc == code]
        if len(g):
            rows.append(dict(zone="POOLED", wc_class=nm, wc_code=code, **stats(g.r, n_dates=int(g.date.dt.date.nunique()))))
    variograms("POOLED", PD, rng, vrows, frows, t0)                          # standardized with each zone's own class scales
    S = pd.DataFrame(rows); S["population"] = "FABDEM-sourced cells of the seamless terrain-bed model (source 3/4), night ICESat-2 ground, EVRF2019"
    S.to_csv(CFG.TABLES / "p95j_terrain_residual_stats.csv", index=False)
    V = pd.DataFrame(vrows); V.to_csv(CFG.TABLES / "p95j_terrain_residual_variogram.csv", index=False)
    F = pd.DataFrame(frows); F["note"] = "pairs of the same date (along-track), isotropy assumed; class-median bias removed; Cressie WLS; fit_rmse = RMS relative residual"
    F.to_csv(CFG.TABLES / "p95j_terrain_variogram_fit.csv", index=False)
    p57 = pd.read_csv(CFG.TABLES / "p57_dem_accuracy_night.csv")
    manifest["p57_reference_rows"] = p57[p57.set.str.startswith("A ")][["set", "N", "median", "NMAD", "RMSE"]].to_dict("records")
    base = F[(F.zone == "POOLED") & (F.wc_class == "all_standardized") & (F.estimator == "cressie_hawkins") & (F.status == "ok")]
    single, nested = base[base.model == "exponential+nugget"], base[base.model == "nested_2exp+nugget"]
    use_nested = len(nested) and (not len(single) or float(nested.fit_rmse.iloc[0]) < 0.5 * float(single.fit_rmse.iloc[0]))
    if use_nested:
        r = nested.iloc[0]; sill = r.c0 + r.s1 + r.s2
        cm = dict(model="nested_2exp+nugget", nugget_share=round(float(r.c0 / sill), 4), structures=[[round(float(r.s1 / sill), 4), float(r.L1_m), "exponential"], [round(float(r.s2 / sill), 4), float(r.L2_m), "exponential"]],
                  sill_standardized=round(float(sill), 4), fit_rmse_rel=float(r.fit_rmse), single_fit_rmse_rel=float(single.fit_rmse.iloc[0]) if len(single) else None)
    elif len(single):
        r = single.iloc[0]; sill = r.c0 + r.s2
        cm = dict(model="exponential+nugget", nugget_share=round(float(r.c0 / sill), 4), structures=[[round(float(r.s2 / sill), 4), float(r.L_m), "exponential"]],
                  sill_standardized=round(float(sill), 4), fit_rmse_rel=float(r.fit_rmse))
    else:
        cm = dict(model="fallback", nugget_share=0.0, structures=[[1.0, 500.0, "exponential"]], sill_standardized=None)
    cm.update(source="POOLED standardized residual (r - b_c) / sigma_c, Cressie-Hawkins estimator, Cressie WLS fit; the nested model is used when its relative RMS misfit is < half that of the single exponential",
              note="p95e: sigma_c per class (marginal) x a unit field with these structures and nugget -- a stated modelling assumption; the nugget includes ICESat-2 segment noise and point-to-cell support mismatch (upper bound of the cell-level white error)")
    manifest["correlation_model_for_p95e"] = cm
    (CFG.TABLES / "p95j_manifest.json").write_text(json.dumps(manifest, indent=1, default=str))
    FIG.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(1, 4, figsize=(20, 4.2), constrained_layout=True)
    for ax, zone in zip(axs, list(ZONES) + ["POOLED"]):
        for nm, col in [("all", "#0b0b0b"), ("cropland", "#eda100"), ("grass", "#1baf7a"), ("wetland", "#2a78d6"), ("trees", "#4a3aa7"), ("built", "#eb6834")]:
            v = V[(V.zone == zone) & (V.wc_class == nm) & (V.n_pairs >= 200)]; f = F[(F.zone == zone) & (F.wc_class == nm) & (F.estimator == "classical") & (F.model == "exponential+nugget")]
            if len(v) == 0:
                continue
            ax.plot(v.lag_mid_m, v.gamma_m2, "o", ms=3.5, color=col, label=f"{nm}" + (f" (L = {f.L_m.iloc[0]:.0f} m)" if len(f) and np.isfinite(f.L_m.iloc[0]) else ""))
            if len(f) and np.isfinite(f.L_m.iloc[0]):
                hh = np.linspace(0, 3000, 200); ax.plot(hh, f.c0.iloc[0] + f.s2.iloc[0] * (1 - np.exp(-hh / f.L_m.iloc[0])), "-", lw=1, color=col)
        ax.set_title(f"{zone}: FABDEM - ICESat-2 ground residual after the class median, same-date pairs", fontsize=8, loc="left")
        ax.set_xlabel("lag, m", fontsize=8); ax.set_ylabel("semivariance, m²", fontsize=8); ax.set_xscale("log"); ax.grid(color="#efece6"); ax.tick_params(labelsize=7); ax.legend(fontsize=6.5, frameon=False)
    ax = axs[3]
    for zone, col in ((ZONES[0], "#2a78d6"), (ZONES[1], "#1baf7a"), ("POOLED", "#0b0b0b")):
        v = V[(V.zone == zone) & (V.wc_class == "all_standardized") & (V.n_pairs >= 200)]
        f = F[(F.zone == zone) & (F.wc_class == "all_standardized") & (F.estimator == "cressie_hawkins") & (F.model == "exponential+nugget")]
        if len(v) == 0:
            continue
        ax.plot(v.lag_mid_m, v.gamma_robust, "o", ms=3.5, color=col, label=f"{zone} robust" + (f" (L = {f.L_m.iloc[0]:.0f} m, nugget {f.nugget_share.iloc[0]:.2f})" if len(f) and np.isfinite(f.L_m.iloc[0]) else ""))
        ax.plot(v.lag_mid_m, v.gamma_m2, "x", ms=3, color=col, alpha=0.5)
        fn = F[(F.zone == zone) & (F.wc_class == "all_standardized") & (F.estimator == "cressie_hawkins") & (F.model == "nested_2exp+nugget")]
        hh = np.linspace(1, 3000, 400)
        if len(f) and np.isfinite(f.L_m.iloc[0]):
            ax.plot(hh, f.c0.iloc[0] + f.s2.iloc[0] * (1 - np.exp(-hh / f.L_m.iloc[0])), ":", lw=0.9, color=col)
        if len(fn) and fn.status.iloc[0] == "ok":
            q = fn.iloc[0]; ax.plot(hh, q.c0 + q.s1 * (1 - np.exp(-hh / q.L1_m)) + q.s2 * (1 - np.exp(-hh / q.L2_m)), "-", lw=1.2, color=col,
                                    label=f"  nested: nugget {q.nugget_share:.2f}, L1 {q.L1_m:.0f} m, L2 {q.L2_m:.0f} m")
    ax.axhline(1.0, color="#52514e", lw=0.6, ls=":")
    ax.set_title("standardized residual (r - b_c) / sigma_c: robust (o) and classical (x); nested fit (solid), single exponential (dotted)", fontsize=8, loc="left")
    ax.set_xlabel("lag, m", fontsize=8); ax.set_ylabel("semivariance (standardized)", fontsize=8); ax.set_xscale("log"); ax.grid(color="#efece6"); ax.tick_params(labelsize=7); ax.legend(fontsize=6.5, frameon=False)
    fig.savefig(FIG / "p95j_variogram.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    pd.set_option("display.width", 250); print(S.to_string(index=False)); print(F.drop(columns="note").to_string(index=False))
    print(f"-> tables/p95j_*.csv, figures/m6_v003A/p95j_variogram.png ({round(time.time() - t0)} s)")


if __name__ == "__main__":
    main()
