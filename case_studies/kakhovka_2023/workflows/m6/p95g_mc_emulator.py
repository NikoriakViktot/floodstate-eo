# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. 100 000-draw Monte-Carlo emulator of the daily inundation (area, volume).
"""P95g -- a vertical-error emulator that gives 100 000 possible values per day of the TOTAL water surface, the NEW inundation
and the volume, validated against the 40 full spatial draws of p95e.

Why an emulator: one full spatial draw (connectivity on 26 M cells) costs ~10 s; 10^5 draws per day are only possible if the
spatial part is fixed and the vertical errors are sampled. Per zone and day the emulator precomputes, on the cells that the
central run ever connects during the event (the connected candidate set), the margin m = DEM_corrected - WSE_day per
WorldCover class as 1-cm histograms. A draw is: one water-surface offset d_wse ~ N(0, sigma_wse) for the day (closure, gauge,
SWOT node noise averaged over the 5 nearest nodes, interpolation, all summed in quadrature) applied to every cell, plus a
per-cell DEM error of class sigma_c organised in independent clusters of KCELL = 625 cells (the 500 m correlation length of
the p95e field). For that error model the count of water cells per class has expectation E(d_wse) = sum_i Phi((d_wse - m_i)/
sigma_c) and variance KCELL * sum_i p_i (1 - p_i), both tabulated from the margin histograms, so each draw is a Gaussian
cluster-count around the smoothed expectation (a cluster-normal emulator; the fully-correlated class-offset limit was tried
first and is far too wide and biased). The normal-regime area uses the same draw on the pre-breach maximum surface; new area =
total - normal; the volume follows E[(d - m)^+]. The reported TOTAL water surface draws are the deterministic total plus the
deviation of the new-area draws (the normal-regime water is observed pre-breach water and is not propagated); the raw
emulator total, inflated by the symmetric DEM error under trees, is kept as W_total_emulator_raw_p50_km2 for transparency. The emulator is compared with the 40 full spatial draws of p95e
(p95g_vs_p95e.csv). Boxplots per day are the "candles" of the paper.

Outputs: <case_study>/tables/p95g_mc_daily.csv (per region x date: total / new area and volume: mean, p05, p25, p50, p75, p95,
         central), p95g_mc_sigmas.csv, p95g_vs_p95e.csv (emulator vs the full spatial draws on the p95e key dates)
"""
from __future__ import annotations
import argparse, importlib.util, json, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio.warp import reproject, Resampling
from scipy import ndimage
from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
N_DRAWS = 100_000
BIN = 0.01                                     # histogram bin, m
MMAX = 8.0                                     # margins above +8 m never flood within the sampled errors
CELL_KM2 = 0.0004
SIGMA_CLOSURE, SIGMA_GAUGE = 0.05, 0.05
BED = 254                                      # pseudo-class of the bed cells of the seamless terrain-bed model
KCELL_FALLBACK = 625                           # cells per independent terrain-error cluster, (500 m / 20 m)^2 -- only without a p95j fit


def _ld(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=N_DRAWS); ap.add_argument("--seed", type=int, default=20260925); a = ap.parse_args()
    t0 = time.time(); P95 = _ld("p95_hand_daily_inundation"); P = P95.load_p92(); rng = np.random.default_rng(a.seed)
    W, dxm, dym, nodes = P95.load_engine()
    E, _ = P95.dem_error_table(); sig_swot = float(nodes.wse_u.median())
    comp = pd.read_csv(CFG.TABLES / "p95e_uncertainty_components.csv") if (CFG.TABLES / "p95e_uncertainty_components.csv").exists() else None
    ci = comp[comp.component.isin(["interpolation_gap_cv", "H(s,t)_interpolation"])] if comp is not None else None
    sig_interp = float(ci.sigma_m.iloc[0]) if ci is not None and len(ci) else 0.054        # p95e rev 2: the 1-day gap-matched NMAD
    sig_wse = float(np.sqrt(SIGMA_CLOSURE ** 2 + SIGMA_GAUGE ** 2 + (sig_swot / np.sqrt(P95.WSE.K)) ** 2 + sig_interp ** 2))
    # rev 2 (2026-09-29): p95e draws a UNIT-variance field (review F02), so the class NMAD is the cell sigma (FIELD_STD = 1);
    # the cluster size follows the fitted correlation (sum of w_i L_i^2 over the nested structures, in cells); bed cells (p55
    # source 1/2/5) carry no FABDEM statistics -> a negligible sigma
    FIELD_STD = 1.0
    mf = CFG.TABLES / "p95j_manifest.json"
    cm = json.loads(mf.read_text()).get("correlation_model_for_p95e") if mf.exists() else None
    KCELL = max(1, int(round(sum(w * r * r for w, r, _ in cm["structures"]) / 400.0))) if cm and cm.get("structures") else KCELL_FALLBACK
    classes = {c: v["sigma"] * FIELD_STD for c, v in E.items() if c != "other"}; classes[0] = E["other"]["sigma"] * FIELD_STD; classes[BED] = 1e-3
    pd.DataFrame([dict(component="wse_total_per_day", sigma_m=round(sig_wse, 3), note="closure 0.05 + gauge 0.05 + swot wse_u/sqrt(5) + interpolation, in quadrature; one offset per day per draw")] +
                 [dict(component=f"dem_class_{c}", sigma_m=round(s, 3), note=f"class NMAD (FABDEM - ICESat-2, p95j) x unit field; clusters of {KCELL} cells from the p95j correlation model; bed cells sigma ~0") for c, s in classes.items()]).to_csv(CFG.TABLES / "p95g_mc_sigmas.csv", index=False)
    edges = np.arange(-MMAX, MMAX + BIN, BIN); centres = edges[:-1] + BIN / 2
    pre_days = [d for d in P95.DATES if d <= pd.Timestamp(P95.BASELINE_DATE)]
    rows = []
    # class offsets shared across zones/regions within a draw; per day a fresh wse offset
    gclass = {c: rng.standard_normal(a.n).astype("f4") for c in classes}      # per-class standard normal for the cluster-count noise
    dwse_day = {str(d.date()): rng.normal(0, sig_wse, a.n).astype("f4") for d in P95.DATES}
    dwse_base = rng.normal(0, sig_wse, a.n).astype("f4")
    acc = {}   # (region, date) -> dict of arrays summed over zones
    for zone in P95.ZONES:
        L = P95.zone_layers(zone, P); G = L["G"]; Z = W.prepare(L)
        base = np.isfinite(L["dem"]) & (L["dist"] <= P95.DIST_MAX_M) & (L["xs"] < dxm - P95.DAM_BUFFER_M)[None, :] & L["own"]
        with rasterio.open(CFG.BULK_ROOT / "worldcover_frames" / zone / "wc_2021_20m.tif") as s:
            wc = np.zeros((G["ny"], G["nx"]), "u1"); reproject(s.read(1), wc, src_transform=s.transform, src_crs=s.crs, dst_transform=G["transform"], dst_crs=G["crs"], resampling=Resampling.nearest)
        wcl = np.where(np.isin(wc, list(c for c in classes if c and c != BED)), wc, 0)
        wcl = np.where(L["is_fabdem"], wcl, BED).astype("u1")                # bed cells: no FABDEM statistics
        zz = np.load(CFG.BULK_ROOT / "floodplain_dyn" / f"{zone}_connected_ceiling" / "daily_new.npz")
        ever = np.zeros(base.shape, bool)
        for k in zz.files:
            if k.startswith("2023"):
                ever |= np.unpackbits(zz[k], count=G["ny"] * G["nx"]).reshape(G["ny"], G["nx"]).astype(bool)
        # candidate set: ever new-connected in the central run, plus the observed pre-breach water and the normal regime
        wpre_max = np.max([W.field(Z, d, 0.0) for d in pre_days], axis=0)
        normal = base & (L["dem"] < wpre_max)                               # ceiling-only normal regime (connectivity dropped in the emulator)
        cand = base & (ever | normal | L["pre"]); cand = ndimage.binary_dilation(cand, iterations=2) & base
        regions = {"DNIPRO_CORRIDOR": L["own"] & ~L["cut"], "INHULETS_VALLEY_rect": L["own"] & L["inh"]}
        if L["fp"] is not None:
            regions["P42_FLOODPLAIN_DOMAIN"] = L["own"] & L["fp"]
        print(zone, "candidate cells", int(cand.sum()), round(time.time() - t0), "s", flush=True)
        def hist_by_class(m, mask):
            H, S = {}, {}
            for c in classes:
                sel = mask & (wcl == c); v = np.clip(m[sel], -MMAX, MMAX - 1e-6)
                h, _ = np.histogram(v, bins=edges); H[c] = np.cumsum(h).astype("f8")
                sm, _ = np.histogram(v, bins=edges, weights=v); S[c] = np.cumsum(sm).astype("f8")
            return H, S
        from scipy.stats import norm
        DGRID = np.arange(-0.8, 0.8001, 0.005)                                # water-surface offset grid for the expectation tables
        def tables(m, mask):
            """Per class: E[count](delta) and Var[count](delta) on DGRID, and E[volume](delta), from 1-cm histograms of the
            margin m and a Gaussian per-cell DEM error of sigma_c with cluster size KCELL (correlated field)."""
            out = {}
            for c, sc in classes.items():
                sel = mask & (wcl == c); v = np.clip(m[sel], -MMAX, MMAX - 1e-6); h, _ = np.histogram(v, bins=edges)
                z = (DGRID[:, None] - centres[None, :]) / sc; Phi = norm.cdf(z); phi = norm.pdf(z)
                Ec = (h[None, :] * Phi).sum(1); Vc = (h[None, :] * Phi * (1 - Phi)).sum(1) * KCELL
                Ev = (h[None, :] * (sc * phi + (DGRID[:, None] - centres[None, :]) * Phi)).sum(1)
                out[c] = (Ec, Vc, Ev)
            return out
        def evaluate(T, d_wse):
            area = np.zeros(a.n); vol = np.zeros(a.n)
            for c, (Ec, Vc, Ev) in T.items():
                mu = np.interp(d_wse, DGRID, Ec); sd = np.sqrt(np.maximum(np.interp(d_wse, DGRID, Vc), 0))
                cnt = mu + sd * gclass[c]; area += cnt; vol += np.interp(d_wse, DGRID, Ev) * np.where(mu > 0, cnt / np.maximum(mu, 1e-9), 1.0)
            return np.maximum(area, 0) * CELL_KM2, np.maximum(vol, 0) * 400 / 1e6
        for nm, reg in regions.items():
            mask = cand & reg
            if not mask.any():
                continue
            # normal regime per draw (pre-breach maximum surface + observed pre water fixed)
            m_base = (L["dem"] - wpre_max).astype("f4"); Tb = tables(m_base, mask & ~L["pre"])
            a_norm, _ = evaluate(Tb, dwse_base); a_norm = a_norm + float((mask & L["pre"]).sum()) * CELL_KM2
            for d in P95.DATES:
                ds = str(d.date()); w = W.field(Z, ds, 0.0); m = (L["dem"] - w).astype("f4")
                Td = tables(m, mask & ~L["pre"]); a_tot, v_tot = evaluate(Td, dwse_day[ds])
                a_tot = a_tot + float((mask & L["pre"]).sum()) * CELL_KM2
                a_new = np.maximum(a_tot - a_norm, 0.0)
                key = (nm, ds); z = acc.setdefault(key, dict(tot=np.zeros(a.n), new=np.zeros(a.n), vol=np.zeros(a.n)))
                z["tot"] += a_tot; z["new"] += a_new; z["vol"] += v_tot
        print(zone, "done", round(time.time() - t0), "s", flush=True)
    central = pd.read_csv(CFG.TABLES / "p95_daily_area_pooled_connected_ceiling.csv")
    q = lambda x: dict(mean=float(x.mean()), p05=float(np.percentile(x, 5)), p25=float(np.percentile(x, 25)), p50=float(np.median(x)), p75=float(np.percentile(x, 75)), p95=float(np.percentile(x, 95)))
    for (nm, ds), z in acc.items():
        c = central[(central.region == nm) & (central.date == ds)]
        r = dict(region=nm, date=ds, n_draws=a.n, area_semantics="terrain_reconstructed")
        for k, lab in (("new", "A_new_km2"), ("vol", "V_new_hm3")):
            r.update({f"{lab}_{kk}": round(v, 2) for kk, v in q(z[k]).items()})
        r["W_total_central_km2"] = float(c.potential_km2.iloc[0]) if len(c) else np.nan
        r["A_new_central_km2"] = float(c.new_km2.iloc[0]) if len(c) else np.nan
        # the TOTAL water surface = observed normal-regime water (not propagated) + new inundation: its draws are the
        # deterministic total shifted by the deviation of each new-area draw from the deterministic new area
        tot = r["W_total_central_km2"] + (z["new"] - r["A_new_central_km2"])
        r.update({f"W_total_km2_{kk}": round(v, 2) for kk, v in q(tot).items()}); r["W_total_emulator_raw_p50_km2"] = round(float(np.median(z["tot"])), 1)
        rows.append(r)
    D = pd.DataFrame(rows).sort_values(["region", "date"]); D.to_csv(CFG.TABLES / "p95g_mc_daily.csv", index=False)
    pe = CFG.TABLES / "p95e_area_volume_uncertainty.csv"
    if pe.exists():
        e = pd.read_csv(pe); m = e.merge(D, on=["region", "date"], how="inner")
        m[["region", "date", "A_p05_km2", "A_p50_km2", "A_p95_km2", "A_new_km2_p05", "A_new_km2_p50", "A_new_km2_p95", "A_central_km2", "A_new_central_km2"]].to_csv(CFG.TABLES / "p95g_vs_p95e.csv", index=False)
    pd.set_option("display.width", 250)
    print(D[D.region == "DNIPRO_CORRIDOR"][["date", "W_total_central_km2", "W_total_km2_p05", "W_total_km2_p50", "W_total_km2_p95", "A_new_central_km2", "A_new_km2_p05", "A_new_km2_p50", "A_new_km2_p95", "V_new_hm3_p50"]].to_string(index=False))
    print(f"-> tables/p95g_*.csv ({round(time.time() - t0)} s)")


if __name__ == "__main__":
    main()
