# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Uncertainty of the terrain reconstruction (rev 2, 2026-09-29: coherent worlds).
"""P95e -- Monte-Carlo uncertainty of the daily terrain-connectivity reconstruction (claim C01-C03, C07): ONE POSSIBLE WORLD
per draw, evaluated on the union mosaic of the zones (review F01-F05, F20).

One draw k:
    1. one terrain-error realization over the ENTIRE mosaic:  z^(k) = z_terrain + eps_z^(k),  eps_z^(k) = sigma_c(x) * F^(k)(x),
       F^(k) a unit-variance Gaussian random field whose covariance (a white nugget plus nested exponential structures) is
       fitted to the standardized FABDEM - ICESat-2 ground residuals (p95j: pooled, robust estimator; class-wise marginal
       sigma_c = NMAD with a pooled correlation -- a stated modelling assumption), applied ONLY to FABDEM-sourced cells
       (bed cells: sigma = 0, a stated limitation);
    2. one water-surface realization over all nodes and dates, entering through Hmat and nothing else (F03):
       H^(k) = H + off_datum (one scalar: the closure of the SWOT chain to the gauge datum) + eps_swot (observed node-days,
       independent, sigma = median wse_u) + eps_interp (interpolated / held node-days: one standard normal per node per gap
       run, scaled by sigma_gap(gap length, kind) from the whole-date hold-out cross-validation of the interpolation)
       [+ eps_pass(day), a per-day term shared by all SWOT nodes: OFF in the primary budget, an ablation];
       the gauge node: gauge + eps_gauge (one scalar; it is the cap AND the local node);
    3. the pre-breach baseline rebuilt with the SAME realization (same rule, same margin);
    4. every day evaluated with the SAME realization:  P_t^(k) = Connected_S[z^(k) < H^(k)(., t)],  N_t^(k) = P_t^(k) \\ B^(k);
    5. the areas and volumes stored DIRECTLY per draw: potential (= total water surface), baseline, new, potential volume,
       new volume -- quantiles of the total come from the total ensemble, never from a shift of the new-area interval (F04).
Draw 0 = the nominal (unperturbed) world, kept for the record and the reproduction gate (== p95 central tables); it is NOT
part of the quantiles. The publication ensemble is 1000 draws (D-N); `--mode convergence` (a second seed) and the cumulative
quantiles at n = 40 / 100 / 250 / 500 / 1000 document its stability (Roy & Gupta 2021: finite Monte-Carlo estimates of tail
quantiles carry their own sampling uncertainty). `--mode ablation`: terrain-only / water-surface-only / baseline-fixed /
pass-term (component attribution of the nominal-vs-median offset). `--mode peak`: the distribution of the day of maximum.
`--mode wse-threshold`: H + delta on the nominal terrain -- the sensitivity of the connected inundation to the water
surface (not a new model).

Outputs: <case_study>/tables/p95e_uncertainty_components.csv (T11b), p95e_area_volume_uncertainty.csv (date x region:
         A / W_total / V / Vtot / baseline p05 p50 p95 + the nominal run), p95e_draws<tag>.csv.gz (every draw; a release asset, not
         in git: its sha256, size, rows, seed and code commit go to p95e_draws_checksums.csv), p95e_interp_cv.csv,
         p95e_peak_date.csv (T12c), p95e_convergence.csv (T11c), p95e_ablation.csv (T11d), p95e_wse_threshold_sensitivity.csv (T11e),
         p95e_manifest<tag>.json
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, multiprocessing as mp, os, subprocess, time
from pathlib import Path
import numpy as np, pandas as pd
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.terrain.connectivity import largest_component
from floodstate_eo.terrain.fields import FieldSynthesizer

HERE = Path(__file__).resolve().parent
KEY_DATES = ["2023-06-06", "2023-06-07", "2023-06-08", "2023-06-09", "2023-06-11", "2023-06-13", "2023-06-14", "2023-06-18", "2023-06-21"]
CONV_DATES = ["2023-06-07", "2023-06-09", "2023-06-13"]
CONV_N = [40, 100, 250, 500, 1000]
SIGMA_DATUM_M, SIGMA_GAUGE_M = 0.05, 0.05
FALLBACK_RANGE_M = 500.0
GAP_BINS = [(1, 1), (2, 2), (3, 4), (5, 8), (9, 10 ** 6)]
CELL_KM2 = 0.0004
REGIONS = ["DNIPRO_CORRIDOR", "INHULETS_VALLEY_rect", "P42_FLOODPLAIN_DOMAIN"]
_G = {}     # process-wide state inherited by forked workers


def _ld(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


# ---- interpolation error from a whole-date hold-out ----------------------------------------------------------------------
def gap_bin(g):
    for i, (lo, hi) in enumerate(GAP_BINS):
        if lo <= g <= hi:
            return i
    return len(GAP_BINS) - 1


def gap_cv(W, dmax=8):
    """Gap-matched cross-validation of the per-node time interpolation (review F05). For every observed node-day and every gap
    length d = 1..dmax, all observations of that node closer than d days are removed and the day is re-estimated as the engine
    does (linear between the remaining observations, held at the ends); the residual is booked under the ACTUAL distance to
    the nearest remaining observation and under 'interpolated' (observations on both sides) or 'held' (one side only).
    Returns (table, sigma lookup [kind][bin] = NMAD in m, rmse lookup [kind][bin], the superseded triplet NMAD)."""
    H, obs = W.H, W.obs; days = np.arange(H.shape[1]); res = []
    for i in range(H.shape[0] - 1):                                          # SWOT nodes; the gauge row is not interpolated here
        o = days[obs[i]]
        if len(o) < 3:
            continue
        hv = H[i, o]
        for jj, j in enumerate(o):
            dist = np.abs(o - j)
            for d in range(1, dmax + 1):
                keep = dist >= d
                if keep.sum() < 1:
                    break
                ro, rv = o[keep], hv[keep]
                gap = int(np.abs(ro - j).min())
                if gap != d:                                                 # this node offers no observation at exactly d: book only exact gaps
                    continue
                kind = 1 if (ro.min() < j < ro.max()) else 2
                res.append((kind, gap, float(np.interp(j, ro, rv) - hv[jj]), int(j)))
    R = pd.DataFrame(res, columns=["kind", "gap_days", "residual_m", "day_index"])
    rows, sig, rmse = [], {1: {}, 2: {}}, {1: {}, 2: {}}
    nm = lambda r: float(1.4826 * np.median(np.abs(r - np.median(r))))
    for kind, kn in ((1, "interpolated"), (2, "held")):
        for b_, (lo, hi) in enumerate(GAP_BINS):
            r = R[(R.kind == kind) & (R.gap_days >= lo) & (R.gap_days <= hi)].residual_m.values
            if len(r) >= 30:
                sig[kind][b_] = nm(r); rmse[kind][b_] = float(np.sqrt((r ** 2).mean()))
            rows.append(dict(kind=kn, gap_lo_days=lo, gap_hi_days=min(hi, dmax), n=int(len(r)), NMAD_m=round(sig[kind].get(b_, np.nan), 4),
                             RMSE_m=round(float(np.sqrt((r ** 2).mean())), 4) if len(r) else np.nan, median_m=round(float(np.median(r)), 4) if len(r) else np.nan,
                             p05_m=round(float(np.quantile(r, .05)), 4) if len(r) else np.nan, p95_m=round(float(np.quantile(r, .95)), 4) if len(r) else np.nan))
    for kind in (1, 2):                                                      # bins without 30 samples (and > dmax days) take the longest filled bin
        for b_ in range(len(GAP_BINS)):
            if b_ not in sig[kind]:
                filled = sorted(sig[kind]) or sorted(sig[3 - kind])
                src = sig[kind] if sig[kind] else sig[3 - kind]; srm = rmse[kind] if rmse[kind] else rmse[3 - kind]
                ref = max(x for x in filled if x <= b_) if any(x <= b_ for x in filled) else min(filled)
                sig[kind][b_] = src[ref]; rmse[kind][b_] = srm[ref]
                rows.append(dict(kind=("interpolated" if kind == 1 else "held") + " (assigned)", gap_lo_days=GAP_BINS[b_][0], gap_hi_days=min(GAP_BINS[b_][1], 999), n=0,
                                 NMAD_m=round(sig[kind][b_], 4), RMSE_m=round(rmse[kind][b_], 4), median_m=np.nan, p05_m=np.nan, p95_m=np.nan))
    tri = [H[i, j] - 0.5 * (H[i, j - 1] + H[i, j + 1]) for i in range(H.shape[0]) for j in range(1, H.shape[1] - 1) if obs[i, j] and obs[i, j - 1] and obs[i, j + 1]]
    tri = np.array(tri); s_tri = nm(tri) if len(tri) else np.nan
    allr = R.residual_m.values
    rows.append(dict(kind="all (gap-matched)", gap_lo_days=1, gap_hi_days=dmax, n=int(len(allr)), NMAD_m=round(nm(allr), 4), RMSE_m=round(float(np.sqrt((allr ** 2).mean())), 4),
                     median_m=round(float(np.median(allr)), 4), p05_m=round(float(np.quantile(allr, .05)), 4), p95_m=round(float(np.quantile(allr, .95)), 4)))
    rows.append(dict(kind="superseded triplet leave-one-out (rev 1)", gap_lo_days=1, gap_hi_days=1, n=int(len(tri)), NMAD_m=round(s_tri, 4) if np.isfinite(s_tri) else np.nan,
                     RMSE_m=np.nan, median_m=np.nan, p05_m=np.nan, p95_m=np.nan))
    return pd.DataFrame(rows), sig, rmse, s_tri


def correlation_model(a):
    """The unit-field covariance for the terrain perturbation: the p95j manifest (nested model when supported), a command-line
    single range, or the 500 m fallback. Also carries the single-exponential alternative for the ablation."""
    fb = dict(model="fallback exponential 500 m", nugget_share=0.0, structures=[(1.0, FALLBACK_RANGE_M, "exponential")], source="FALLBACK 500 m (no p95j fit)")
    if a.range_m:
        return dict(model="exponential (command line)", nugget_share=0.0, structures=[(1.0, float(a.range_m), "exponential")], source="command line")
    mf = CFG.TABLES / "p95j_manifest.json"
    if not mf.exists():
        return fb
    cm = json.loads(mf.read_text()).get("correlation_model_for_p95e")
    if not cm or cm.get("model") == "fallback":
        return fb
    out = dict(model=cm["model"], nugget_share=float(cm["nugget_share"]), structures=[(float(w), float(r), m) for w, r, m in cm["structures"]], source=cm["source"])
    F = pd.read_csv(CFG.TABLES / "p95j_terrain_variogram_fit.csv")
    s = F[(F.zone == "POOLED") & (F.wc_class == "all_standardized") & (F.estimator == "cressie_hawkins") & (F.model == "exponential+nugget") & (F.status == "ok")]
    if len(s):
        sill = float(s.c0.iloc[0] + s.s2.iloc[0])
        out["single"] = dict(nugget_share=float(s.c0.iloc[0]) / sill, structures=[(float(s.s2.iloc[0]) / sill, float(s.L_m.iloc[0]), "exponential")])
    if a.no_nugget:
        out["nugget_share"] = 0.0; out["model"] += " (nugget off)"
    return out


def gap_runs(W):
    """Per SWOT node: the contiguous runs of non-observed, available node-days (kind 1 or 2) -> [(node, start, stop, kinds, gaps)]."""
    runs = []
    for i in range(W.H.shape[0] - 1):
        k = W.kind[i]; j = 0
        while j < len(k):
            if k[j] in (1, 2):
                s = j
                while j < len(k) and k[j] in (1, 2):
                    j += 1
                runs.append((i, s, j))
            else:
                j += 1
    return runs


# ---- one world ------------------------------------------------------------------------------------------------------------
def draw_hmat(W, prm, rng, runs):
    """The perturbed node-height matrix of one draw: every water-surface term enters here, once."""
    Hm = W.H.copy(); n = Hm.shape[0] - 1; nd = Hm.shape[1]
    off = float(rng.normal(0, prm["sigma_datum"]))
    e_sw = rng.normal(0, prm["sigma_swot"], (n, nd)).astype("f4") * W.obs[:-1]
    e_it = np.zeros((n, nd), "f4")
    z = rng.standard_normal(len(runs))
    for (i, s, e), zz in zip(runs, z):
        for j in range(s, e):
            e_it[i, j] = zz * prm["sigma_gap"][int(W.kind[i, j])][gap_bin(int(W.gap[i, j]))]
    e_pass = rng.normal(0, prm["sigma_pass"], nd).astype("f4") if prm["sigma_pass"] > 0 else np.zeros(nd, "f4")
    Hm[:-1] += off + e_pass[None, :] + e_sw + e_it
    e_g = float(rng.normal(0, prm["sigma_gauge"])); Hm[-1] += e_g
    return Hm, dict(off_datum=off, e_gauge=e_g)


def _accounting(pot, new, w, dem):
    """Areas and volumes per (zone, region) from the base-cell code array: one gather + a few bincounts per day."""
    bidx, rc = _G["bidx"], _G["rc"]
    pb = pot.ravel()[bidx]; nb = new.ravel()[bidx]
    d = (w.ravel()[bidx] - dem.ravel()[bidx]).astype("f8")
    out = {}
    out["pot"] = np.bincount(rc[pb], minlength=64); out["new"] = np.bincount(rc[nb], minlength=64)
    out["vpot"] = np.bincount(rc[pb], weights=d[pb], minlength=64); out["vnew"] = np.bincount(rc[nb], weights=d[nb], minlength=64)
    return out


def _decode(counts, quantity):
    """(zone_id, region) sums from the code bincount: code = zone_id * 8 + corridor + 2 inh + 4 p42."""
    res = {}
    for zid in _G["zone_ids"]:
        for r, bit in (("DNIPRO_CORRIDOR", 1), ("INHULETS_VALLEY_rect", 2), ("P42_FLOODPLAIN_DOMAIN", 4)):
            if r not in _G["regions"]:
                continue
            codes = [zid * 8 + c for c in range(8) if c & bit]
            res[(zid, r)] = float(sum(counts[quantity][c] for c in codes))
    return res


def crop_mosaic(M, P95):
    """Crop every mosaic layer to the bounding box of the base cells. Exact: candidates are a subset of the base, the water
    surface is anchored in map coordinates, and the terrain field is still synthesised on the FULL union lattice and cropped
    (`_G["crop"]`), so every draw is identical to the uncropped evaluation -- only the memory traffic shrinks."""
    b = M["base"]; rr = np.where(b.any(1))[0]; cc = np.where(b.any(0))[0]
    r0, r1, c0, c1 = int(rr.min()), int(rr.max()) + 1, int(cc.min()), int(cc.max()) + 1
    for k, v in list(M.items()):
        if isinstance(v, np.ndarray) and v.ndim == 2 and v.shape == b.shape:
            M[k] = np.ascontiguousarray(v[r0:r1, c0:c1])
    M["xs"], M["ys"] = M["xs"][c0:c1], M["ys"][r0:r1]
    tr = M["G"]["transform"]
    M["G"] = dict(M["G"], transform=type(tr)(tr.a, tr.b, tr.c + c0 * tr.a, tr.d, tr.e, tr.f + r0 * tr.e), ny=r1 - r0, nx=c1 - c0)
    M["regions"] = P95.region_masks(M)
    return (r0, r1, c0, c1)


def run_draw(k):
    """Rows of one world (k = 0: nominal). Uses the forked globals `_G`."""
    M, W, Z, prm = _G["M"], _G["W"], _G["Z"], _G["prm"]; P95 = _G["P95"]
    rng = np.random.default_rng([prm["seed"], k])
    info = {}
    if k == 0 or not prm["terrain"]:
        dem = M["dem"]
    else:
        r0, r1, c0, c1 = _G["crop"]
        F = _G["syns"][prm["field"]].draw(rng)[r0:r1, c0:c1]                # synthesised on the full union lattice, then cropped
        eps = (F * M["sig"]).astype("f4"); dem = (M["dem"] + eps).astype("f4")
        assert not eps[~M["is_fabdem"]].any(), "terrain perturbation leaked onto bed cells"
        info["eps_std_fabdem"] = float(eps[M["is_fabdem"] & M["base"]].std()); info["field_std"] = float(F[M["base"]].std()); del F, eps
    Hmat = None
    if k > 0 and prm["wse"]:
        Hmat, info_h = draw_hmat(W, prm, rng, _G["runs"]); info.update(info_h)
    rows = []
    if prm["baseline_fixed"] and k > 0:
        baseline = _G["baseline0"]
    else:
        baseline = M["pre"].copy()
    for day in prm["base_dates"]:
        pot, w = P95.potential_mosaic(M, W, Z, day, prm["rule"], dem, Hmat, P95.BASE_MARGIN_M, prm["connectivity"], _G["seed"])
        if not (prm["baseline_fixed"] and k > 0):
            baseline |= pot
        if day in prm["days"]:                                               # pre-breach day: new = 0 by construction, the total counts
            c = _accounting(pot, np.zeros_like(pot), w, dem); rows.append((day, c))
    base_cnt = np.bincount(_G["rc"][baseline.ravel()[_G["bidx"]]], minlength=64)
    for day in prm["days"]:
        if day in prm["base_dates"]:
            continue
        pot, w = P95.potential_mosaic(M, W, Z, day, prm["rule"], dem, Hmat, prm["margin"], prm["connectivity"], _G["seed"])
        new = pot & ~baseline
        rows.append((day, _accounting(pot, new, w, dem)))
    out = []
    bl = _decode({"b": base_cnt}, "b")
    for day, c in rows:
        A, N, VP, VN = _decode(c, "pot"), _decode(c, "new"), _decode(c, "vpot"), _decode(c, "vnew")
        for (zid, r), a in A.items():
            out.append(dict(zone=_G["zone_name"][zid], draw=k, date=day, region=r, potential_km2=round(a * CELL_KM2, 4), baseline_km2=round(bl[(zid, r)] * CELL_KM2, 4),
                            new_km2=round(N[(zid, r)] * CELL_KM2, 4), potential_volume_hm3=round(VP[(zid, r)] * 400 / 1e6, 4), new_volume_hm3=round(VN[(zid, r)] * 400 / 1e6, 4)))
    return k, out, info


def _worker(k):
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    return run_draw(k)


# ---- summaries ------------------------------------------------------------------------------------------------------------
def pooled(D):
    """Zones summed (the overlap is owned by one zone): draw x date x region."""
    return D.groupby(["draw", "date", "region"], as_index=False)[["potential_km2", "baseline_km2", "new_km2", "potential_volume_hm3", "new_volume_hm3"]].sum()


def summarise(Pd):
    rows = []
    for (d, r), g in Pd.groupby(["date", "region"]):
        c = g[g.draw == 0]; s = g[g.draw > 0]
        q = lambda col, p: round(float(s[col].quantile(p)), 1)
        rows.append(dict(date=d, region=r, area_semantics="terrain_reconstructed",
                         A_central_km2=float(c.new_km2.iloc[0]), A_p05_km2=q("new_km2", .05), A_p50_km2=q("new_km2", .5), A_p95_km2=q("new_km2", .95),
                         V_central_hm3=float(c.new_volume_hm3.iloc[0]), V_p05_hm3=q("new_volume_hm3", .05), V_p50_hm3=q("new_volume_hm3", .5), V_p95_hm3=q("new_volume_hm3", .95),
                         W_total_central_km2=float(c.potential_km2.iloc[0]), W_total_p05_km2=q("potential_km2", .05), W_total_p50_km2=q("potential_km2", .5), W_total_p95_km2=q("potential_km2", .95),
                         Vtot_central_hm3=float(c.potential_volume_hm3.iloc[0]), Vtot_p05_hm3=q("potential_volume_hm3", .05), Vtot_p50_hm3=q("potential_volume_hm3", .5), Vtot_p95_hm3=q("potential_volume_hm3", .95),
                         baseline_central_km2=float(c.baseline_km2.iloc[0]), baseline_p05_km2=q("baseline_km2", .05), baseline_p50_km2=q("baseline_km2", .5), baseline_p95_km2=q("baseline_km2", .95),
                         n_draws=int(s.draw.nunique())))
    return pd.DataFrame(rows)


def peak_dates(Pd, quantity="new_km2"):
    rows = []
    for r, g in Pd.groupby("region"):
        s = g[g.draw > 0]; am = s.loc[s.groupby("draw")[quantity].idxmax()]
        vc = am.date.value_counts(); n = int(s.draw.nunique())
        nom = g[g.draw == 0]; nom_day = nom.loc[nom[quantity].idxmax(), "date"] if len(nom) else None
        for d, cnt in vc.items():
            rows.append(dict(region=r, quantity=quantity, date_of_maximum=d, n_draws_with_maximum=int(cnt), share=round(float(cnt / n), 4), n_draws=n, nominal_date_of_maximum=nom_day))
    return pd.DataFrame(rows)


def convergence(Pd, seed, rng_seed=1):
    """Cumulative quantiles of the first n draws (n in CONV_N) on CONV_DATES, corridor, with a bootstrap CI of the quantile estimator."""
    rng = np.random.default_rng(rng_seed); rows = []
    g = Pd[(Pd.region == "DNIPRO_CORRIDOR") & (Pd.draw > 0)]
    nmax = int(g.draw.max())
    for n in [x for x in CONV_N if x <= nmax] + ([nmax] if nmax not in CONV_N else []):
        sub = g[g.draw <= n]
        pk = sub.loc[sub.groupby("draw").new_km2.idxmax()].date.value_counts(normalize=True)
        for d in CONV_DATES:
            s = sub[sub.date == d]
            row = dict(seed=seed, n_draws=n, date=d, region="DNIPRO_CORRIDOR", share_max_on_0607=round(float(pk.get("2023-06-07", 0.0)), 4), share_max_on_0608=round(float(pk.get("2023-06-08", 0.0)), 4))
            for col, nm in (("new_km2", "A"), ("potential_km2", "W_total"), ("new_volume_hm3", "V")):
                v = s[col].values
                for p, lab in ((.05, "p05"), (.5, "p50"), (.95, "p95")):
                    row[f"{nm}_{lab}"] = round(float(np.quantile(v, p)), 1)
                    b = np.quantile(rng.choice(v, (2000, len(v)), replace=True), p, axis=1)
                    row[f"{nm}_{lab}_boot_lo"] = round(float(np.quantile(b, .025)), 1); row[f"{nm}_{lab}_boot_hi"] = round(float(np.quantile(b, .975)), 1)
                row[f"{nm}_width90"] = round(row[f"{nm}_p95"] - row[f"{nm}_p05"], 1)
            rows.append(row)
    return pd.DataFrame(rows)


# ---- main -----------------------------------------------------------------------------------------------------------------
def setup(a):
    P95 = _ld("p95_hand_daily_inundation"); P = P95.load_p92()
    W, dxm, dym, nodes = P95.load_engine(max_gap_days=a.max_gap_days)
    M = P95.mosaic_layers(P, with_s1=False); M["base"] = M["base_geom"] & P95.dam_mask(M, dxm)
    for k in ("zones", "dem_raw", "bias", "base_geom"):                   # not used by the draws: free before the workers fork
        M.pop(k, None)
    if a.rule == "hand_and_ceiling":
        M["base"] &= np.isfinite(M["hand"])
    full_shape = M["dem"].shape
    M["seed_net"] = largest_component(M["seed"]) if a.seed_network == "main_stem" else M["seed"]
    crop = crop_mosaic(M, P95)
    Z = W.prepare(M); seed = M["seed_net"]
    # accounting codes on the base cells: zone_id * 8 + corridor + 2 inh + 4 p42
    R = M["regions"]; code = (M["own_id"].astype("i4") * 8 + R["DNIPRO_CORRIDOR"] + 2 * R["INHULETS_VALLEY_rect"] + (4 * R["P42_FLOODPLAIN_DOMAIN"] if "P42_FLOODPLAIN_DOMAIN" in R else 0)).astype("u1")
    bidx = np.flatnonzero(M["base"] & (M["own_id"] > 0)); rc = code.ravel()[bidx]
    sig_swot = float(nodes.wse_u.median()); cvtab, sig_gap, rmse_gap, s_tri = gap_cv(W)
    corr = correlation_model(a)
    syns = {"primary": FieldSynthesizer(full_shape, 20.0, structures=corr["structures"], nugget=corr["nugget_share"])}
    if a.mode == "ablation":
        syns["no_nugget"] = FieldSynthesizer(full_shape, 20.0, structures=corr["structures"], nugget=0.0)
        if corr.get("single"):
            syns["single_exponential"] = FieldSynthesizer(full_shape, 20.0, structures=corr["single"]["structures"], nugget=corr["single"]["nugget_share"])
    range_m = max(r for _, r, _ in corr["structures"]); range_src = corr["source"]
    prm = dict(seed=a.seed, rule=a.rule, margin=P95.SWOT_MARGIN_M, connectivity=a.connectivity, sigma_datum=a.sigma_datum, sigma_gauge=a.sigma_gauge, sigma_swot=sig_swot,
               sigma_gap=sig_gap, sigma_gap_rmse=rmse_gap, sigma_pass=a.pass_term, range_m=range_m, range_source=range_src, nugget=corr["nugget_share"], corr=corr, field="primary",
               terrain=True, wse=True, baseline_fixed=False,
               base_dates=[str(d.date()) for d in P95.DATES if d <= pd.Timestamp(P95.BASELINE_DATE)],
               days=[str(d.date()) for d in P95.DATES] if a.days == "all" else KEY_DATES)
    _G.update(M=M, W=W, Z=Z, prm=prm, P95=P95, seed=seed, bidx=bidx, rc=rc, zone_ids=sorted(M["zone_id"].values()), zone_name={v: k for k, v in M["zone_id"].items()},
              regions=set(R), runs=gap_runs(W), syns=syns, crop=crop)
    comp = [dict(component="datum_closure_kherson", sigma_m=a.sigma_datum, applied="one scalar per draw, every SWOT node and day (the closure of the SWOT chain to the gauge datum)", source="Paper 1 Table 5 / Sec. 5.12 (NMAD 4-5 cm at Kherson)"),
            dict(component="gauge_daily", sigma_m=a.sigma_gauge, applied="one scalar per draw on the gauge node (local node AND far cap; never added twice)", source="date-only daily values; two yearbooks differ by NMAD 1.5 cm (Paper 1 Sec. 5.12)"),
            dict(component="swot_node_wse_u", sigma_m=round(sig_swot, 3), applied="observed node-days, independent per node-day", source="p59 nodes, median wse_u"),
            dict(component="interpolation_gap_cv", sigma_m=round(float(sig_gap[1][0]), 3), sigma_by_gap_m="; ".join(f"{GAP_BINS[b][0]}-{GAP_BINS[b][1] if GAP_BINS[b][1] < 999 else '...'} d: interp {sig_gap[1][b]:.3f} / held {sig_gap[2][b]:.3f}" for b in range(len(GAP_BINS))),
                 applied="interpolated / held node-days: one standard normal per node per gap run x NMAD(gap length, kind) from the gap-matched CV (T11f); RMSE-based scale as an ablation; rev-1 triplet NMAD %.3f m for comparison" % s_tri, source="p95e gap_cv (gap-matched)"),
            dict(component="pass_level_swot", sigma_m=a.pass_term, applied="per-day scalar shared by all SWOT nodes; 0 in the primary budget (maintainer decision D-MC1), an ablation", source="Paper 1 daily closure scatter"),
            dict(component="terrain_field_correlation", sigma_m=np.nan, range_m=round(range_m, 1), nugget_share=round(corr["nugget_share"], 3),
                 structures="; ".join(f"{w:.2f} x exp(-h/{r:.0f} m)" for w, r, _ in corr["structures"]), model=corr["model"],
                 applied="unit-variance FFT field on the union mosaic, one realization per draw, x class sigma on FABDEM cells", source=range_src)]
    E, esrc = P95.terrain_residual_table(None)
    for z in M["names"]:
        Ez, _ = P95.terrain_residual_table(z)
        for code_, v in Ez.items():
            if code_ == "other":
                continue
            comp.append(dict(component=f"terrain_{v['cls']}", zone=z, sigma_m=round(v["sigma"], 3), bias_m=round(v["bias"], 3), rmse_m=round(v["rmse"], 3), n=v["n"], transferred=v["transferred"],
                             applied="class NMAD as the marginal sigma of the correlated field on FABDEM-sourced cells; the class median (residual terrain-elevation bias) is removed in p95", source=f"{v['zone_used']} (FABDEM - ICESat-2 ground, night)"))
    comp.append(dict(component="terrain_bed", sigma_m=0.0, applied="bed cells (source 1/2/5): no stochastic model in this budget (limitation)", source="p55 source mask"))
    return P95, M, W, prm, pd.DataFrame(comp), cvtab


FINGERPRINT_FILES = ("p95_hand_daily_inundation.py", "paper1_frame.py", "p95e_uncertainty_mc.py")
FINGERPRINT_TABLES = ("p59_swot_vs_kherson.csv", "p59_swot_flood_nodes.csv", "p95j_terrain_residual_stats.csv", "p95j_terrain_variogram_fit.csv")


def input_fingerprint(prm) -> str:
    """What the draws depend on: the parameters, the reconstruction code (incl. the vertical frame of Paper 1) and the input tables.
    The chunk cache of a run is valid only under the same fingerprint (2026-09-30: a rerun after the Paper-1 frame change had
    silently resumed from draws of the previous inputs)."""
    h = hashlib.sha256(json.dumps(prm, sort_keys=True, default=str).encode())
    for f in [HERE / n for n in FINGERPRINT_FILES] + [CFG.TABLES / n for n in FINGERPRINT_TABLES]:
        h.update(f.name.encode()); h.update(hashlib.sha256(f.read_bytes()).digest() if f.exists() else b"missing")
    return h.hexdigest()[:16]


def run_ensemble(a, prm, tag, n, seed):
    prm = dict(prm, seed=seed); _G["prm"] = prm
    chunks = CFG.TABLES / "_p95e_chunks" / (tag or "primary"); chunks.mkdir(parents=True, exist_ok=True)
    fp, fpf = input_fingerprint(prm), chunks / "fingerprint.txt"
    if not fpf.exists() or fpf.read_text().strip() != fp:                  # different inputs: the cached draws are not this ensemble
        stale = list(chunks.glob("draw_*.csv"))
        for f in stale:
            f.unlink()
        fpf.write_text(fp + "\n"); print(f"  {tag or 'primary'}: input fingerprint {fp}; {len(stale)} cached draws of other inputs removed", flush=True)
    todo = [k for k in range(n + 1) if not (chunks / f"draw_{k:05d}.csv").exists()]
    t0 = time.time(); infos = {}
    if todo:
        ctx = mp.get_context("fork")
        with ctx.Pool(a.workers) as pool:
            for i, (k, rows, info) in enumerate(pool.imap_unordered(_worker, todo, chunksize=1), 1):
                pd.DataFrame(rows).to_csv(chunks / f"draw_{k:05d}.csv", index=False); infos[k] = info
                if i % 25 == 0 or i == len(todo):
                    print(f"  {tag or 'primary'}: {i}/{len(todo)} draws, {round(time.time() - t0)} s", flush=True)
    D = pd.concat([pd.read_csv(chunks / f"draw_{k:05d}.csv") for k in range(n + 1)], ignore_index=True)
    return D, infos, round(time.time() - t0)


def record_draws(path: Path, n: int, seed: int, mode: str, days: str, code_commit: str | None = None):
    """Checksum row of a draws file (the file itself is a release asset, not in git), upserted by file name."""
    if code_commit is None:
        r = lambda *c: subprocess.run(["git", *c], capture_output=True, text=True, cwd=str(HERE)).stdout.strip()
        code_commit = r("rev-parse", "--short=12", "HEAD") + ("-dirty" if r("status", "--porcelain", "--", str(HERE)) else "")
    row = dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size,
               rows=int(pd.read_csv(path, usecols=["draw"]).shape[0]), n_draws=n, seed=seed, mode=mode, days=days, code_commit=code_commit,
               location="release asset (GitHub release / Zenodo), not in git")
    ck = CFG.TABLES / "p95e_draws_checksums.csv"
    old = pd.read_csv(ck) if ck.exists() else pd.DataFrame(columns=list(row))
    pd.concat([old[old.file != row["file"]], pd.DataFrame([row])], ignore_index=True).to_csv(ck, index=False)
    return row


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=1000); ap.add_argument("--seed", type=int, default=20260929); ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--rule", default="connected_ceiling"); ap.add_argument("--days", choices=["all", "key"], default="all")
    ap.add_argument("--mode", default="primary", choices=["primary", "convergence", "ablation", "peak", "wse-threshold"])
    ap.add_argument("--sigma-datum", type=float, default=SIGMA_DATUM_M); ap.add_argument("--sigma-gauge", type=float, default=SIGMA_GAUGE_M)
    ap.add_argument("--pass-term", type=float, default=0.0, help="per-day SWOT term shared by all nodes (m); 0 = off (primary)")
    ap.add_argument("--range-m", type=float, default=None, help="override the fitted correlation range"); ap.add_argument("--no-nugget", action="store_true")
    ap.add_argument("--connectivity", type=int, default=8, choices=[4, 8]); ap.add_argument("--seed-network", default="all_prewater", choices=["all_prewater", "main_stem"])
    ap.add_argument("--max-gap-days", type=int, default=None); ap.add_argument("--tag", default="")
    a = ap.parse_args(); t0 = time.time()
    P95, M, W, prm, comp, cvtab = setup(a)
    print(f"setup {round(time.time() - t0)} s: mosaic {M['dem'].shape}, base cells {len(_G['bidx']):,}, range {prm['range_m']:.0f} m ({prm['range_source']}), nugget {prm['nugget']:.3f}", flush=True)
    tag = a.tag
    if a.mode == "primary":
        comp.to_csv(CFG.TABLES / "p95e_uncertainty_components.csv", index=False); cvtab.to_csv(CFG.TABLES / "p95e_interp_cv.csv", index=False)
        print(comp.to_string(index=False), flush=True)
        D, infos, secs = run_ensemble(a, prm, tag, a.n, a.seed)
        D.to_csv(CFG.TABLES / f"p95e_draws{tag}.csv.gz", index=False, compression="gzip"); record_draws(CFG.TABLES / f"p95e_draws{tag}.csv.gz", a.n, a.seed, "primary", a.days)
        Pd = pooled(D); R = summarise(Pd); R.to_csv(CFG.TABLES / f"p95e_area_volume_uncertainty{tag}.csv", index=False)
        pk = pd.concat([peak_dates(Pd, "new_km2"), peak_dates(Pd, "potential_km2")], ignore_index=True); pk.to_csv(CFG.TABLES / f"p95e_peak_date{tag}.csv", index=False)
        cv = convergence(Pd, a.seed); cv.to_csv(CFG.TABLES / f"p95e_convergence{tag}.csv", index=False)
        fs = [v.get("field_std") for v in infos.values() if v.get("field_std")]
        man = dict(mode="primary", n_draws=a.n, seed=a.seed, workers=a.workers, seconds=secs, rule=a.rule, days=a.days, params={k: (v if k != "sigma_gap" else {kk: vv for kk, vv in v.items()}) for k, v in prm.items() if k not in ("base_dates", "days")},
                   field_std_on_base_cells=dict(mean=float(np.mean(fs)), min=float(np.min(fs)), max=float(np.max(fs))) if fs else None,
                   eps_std_fabdem_mean=float(np.mean([v["eps_std_fabdem"] for v in infos.values() if "eps_std_fabdem" in v])) if infos else None,
                   nominal_is_draw0="draw 0 = unperturbed world, excluded from the quantiles; == p95 central tables (gate)")
        (CFG.TABLES / f"p95e_manifest{tag}.json").write_text(json.dumps(man, indent=1, default=str))
        pd.set_option("display.width", 250); print(R[R.region == "DNIPRO_CORRIDOR"][["date", "A_central_km2", "A_p05_km2", "A_p50_km2", "A_p95_km2", "W_total_central_km2", "W_total_p05_km2", "W_total_p50_km2", "W_total_p95_km2", "V_p50_hm3"]].to_string(index=False))
        print(pk.to_string(index=False)); print(cv.to_string(index=False))
    elif a.mode == "convergence":
        tag = tag or f"_seed{a.seed}"
        D, infos, secs = run_ensemble(a, prm, tag, a.n, a.seed); D.to_csv(CFG.TABLES / f"p95e_draws{tag}.csv.gz", index=False, compression="gzip")
        record_draws(CFG.TABLES / f"p95e_draws{tag}.csv.gz", a.n, a.seed, "convergence", a.days)
        cv = convergence(pooled(D), a.seed); p = CFG.TABLES / "p95e_convergence.csv"
        old = pd.read_csv(p) if p.exists() else pd.DataFrame(); old = old[old.seed != a.seed] if len(old) else old
        pd.concat([old, cv], ignore_index=True).to_csv(p, index=False); print(cv.to_string(index=False))
    elif a.mode == "ablation":
        rows = []
        base_prm = dict(prm)
        _G["prm"] = base_prm
        # the nominal baseline for the baseline-fixed variant
        M0 = _G["M"]; W0 = _G["W"]; Z0 = _G["Z"]; bl = M0["pre"].copy()
        for day in base_prm["base_dates"]:
            bl |= P95.potential_mosaic(M0, W0, Z0, day, base_prm["rule"], None, None, P95.BASE_MARGIN_M, base_prm["connectivity"], _G["seed"])[0]
        _G["baseline0"] = bl
        variants = {"terrain_only": dict(wse=False), "water_surface_only": dict(terrain=False), "baseline_fixed": dict(baseline_fixed=True), "pass_term_0.05": dict(sigma_pass=0.05),
                    "no_interpolation_term": dict(sigma_gap={1: {b: 0.0 for b in range(len(GAP_BINS))}, 2: {b: 0.0 for b in range(len(GAP_BINS))}}),
                    "no_nugget": dict(field="no_nugget"), "interpolation_rmse_scale": dict(sigma_gap=base_prm["sigma_gap_rmse"])}
        if "single_exponential" in _G["syns"]:
            variants["single_exponential"] = dict(field="single_exponential")
        for nm, ch in variants.items():
            vp = dict(base_prm, **ch, days=KEY_DATES); D, _, secs = run_ensemble(a, vp, f"_abl_{nm}", a.n, a.seed)
            Pd = pooled(D); S = summarise(Pd); S.insert(0, "variant", nm); S["seconds"] = secs; rows.append(S)
            print(nm, secs, "s", flush=True)
        prim = CFG.TABLES / "_p95e_chunks" / "primary"                   # 'full' = draws 0..n of the primary (same seed, same per-draw streams)
        files = [prim / f"draw_{k:05d}.csv" for k in range(a.n + 1)]
        if all(f.exists() for f in files):
            D = pd.concat([pd.read_csv(f) for f in files], ignore_index=True); D = D[D.date.isin(KEY_DATES)]
            S = summarise(pooled(D)); S.insert(0, "variant", "full"); S["seconds"] = np.nan; rows.insert(0, S)
        else:
            D, _, secs = run_ensemble(a, dict(base_prm, days=KEY_DATES), "_abl_full", a.n, a.seed)
            S = summarise(pooled(D)); S.insert(0, "variant", "full"); S["seconds"] = secs; rows.insert(0, S)
        A = pd.concat(rows, ignore_index=True); A.to_csv(CFG.TABLES / "p95e_ablation.csv", index=False)
        print(A[A.region == "DNIPRO_CORRIDOR"][["variant", "date", "A_central_km2", "A_p05_km2", "A_p50_km2", "A_p95_km2", "W_total_p50_km2", "V_p50_hm3"]].to_string(index=False))
    elif a.mode == "peak":
        D = pd.read_csv(CFG.TABLES / f"p95e_draws{tag}.csv.gz"); Pd = pooled(D)
        pk = pd.concat([peak_dates(Pd, "new_km2"), peak_dates(Pd, "potential_km2")], ignore_index=True); pk.to_csv(CFG.TABLES / f"p95e_peak_date{tag}.csv", index=False); print(pk.to_string(index=False))
    elif a.mode == "wse-threshold":
        rows = []; M0 = _G["M"]; W0 = _G["W"]; Z0 = _G["Z"]; bl = M0["pre"].copy()
        for day in prm["base_dates"]:
            bl |= P95.potential_mosaic(M0, W0, Z0, day, prm["rule"], None, None, P95.BASE_MARGIN_M, prm["connectivity"], _G["seed"])[0]
        for day in CONV_DATES:
            for delta in (-0.20, -0.10, -0.05, 0.0, 0.05, 0.10, 0.20):
                pot, w = P95.potential_mosaic(M0, W0, Z0, day, prm["rule"], None, None, prm["margin"] + delta, prm["connectivity"], _G["seed"]); new = pot & ~bl
                c = _accounting(pot, new, w, M0["dem"]); A, N, VN = _decode(c, "pot"), _decode(c, "new"), _decode(c, "vnew")
                for r in _G["regions"]:
                    rows.append(dict(date=day, region=r, delta_m=delta, W_total_km2=round(sum(v for (z, rr), v in A.items() if rr == r) * CELL_KM2, 1),
                                     A_new_km2=round(sum(v for (z, rr), v in N.items() if rr == r) * CELL_KM2, 1), V_new_hm3=round(sum(v for (z, rr), v in VN.items() if rr == r) * 400 / 1e6, 1)))
        T = pd.DataFrame(rows)
        for (d, r), g in T.groupby(["date", "region"]):
            g = g.sort_values("delta_m"); dA = np.gradient(g.A_new_km2.values, g.delta_m.values); T.loc[g.index, "dA_dH_km2_per_m"] = np.round(dA, 1)
            dW = np.gradient(g.W_total_km2.values, g.delta_m.values); T.loc[g.index, "dW_dH_km2_per_m"] = np.round(dW, 1)
        T["note"] = "sensitivity of the connected inundation to a uniform water-surface offset on the nominal terrain (baseline fixed); not a new model"
        T.to_csv(CFG.TABLES / "p95e_wse_threshold_sensitivity.csv", index=False); print(T[T.region == "DNIPRO_CORRIDOR"].to_string(index=False))
    print(f"-> tables/p95e_* ({round(time.time() - t0)} s)")


if __name__ == "__main__":
    main()
