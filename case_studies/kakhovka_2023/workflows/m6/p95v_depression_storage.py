# New in floodstate-eo, 2026-09-30 (maintainer: DEPRESSION_STORAGE = threshold connectivity + finite conveyance + depression storage +
# independent recession). STATUS: ACTIVE. Diagnostic v1: one depression, prior-predictive, NOT the reconstruction product.
"""P95v -- a mass-conserving storage model of a floodplain depression that the river reaches only over a sill, tested WITHOUT calibration
against the satellite-observed new water of 7, 9, 13 and 21 June 2023 (UNOSAT 3614; the p95t masks) -- v0 for the floodplain lowland south
of Krynky (the p95p / p95q case). v0 (same day) blocked the friction path by a straight water line below the terrace crests; v1 fixes it.

Concept (storage cell with a finite connection; Hunter et al. 2005, doi:10.1016/j.advwatres.2005.03.007; delayed filling and storage after
disconnection on large floodplains: Rudorff et al. 2014, doi:10.1002/2013WR014091 / 10.1002/2013WR014714; sill-defined connectivity: Lesack &
Marsh 2010, doi:10.1029/2010WR009607; floodplain residence times hours to days: Wohl 2021, doi:10.1029/2020RG000724):
    dV/dt = Q(H_up, h) - (ET + k) * A(h),                     V(h), A(h): hypsometry of the storage ground on the model terrain
  depression D  = the connected component of {terrain < sill} holding the lowland floor (66 km2); storage ground G = D minus the pre-breach
                  water (18.5 km2 of scattered wetland at 6.2-8.6 m, not a lake at the bottom); the store starts empty (v1);
  terrain error = the observed water of 9 June sits at every elevation of D (median 7.36 m vs 7.57 m of the observed ground): the
                  hypsometry is smoothed by a Gaussian terrain error sigma, areas are expected values (a bathtub cannot place the water
                  cell by cell on this terrain; areas and volumes are the test, CSI is reported as an expectation);
  H_up(t)       = the reconstruction's water surface (p95 engine, nominal) at the river-side foot of the terrace, daily values at 12:00 UTC,
                  linear in time;
  Q 'friction'  = steady 1-D Manning flow along the lowest path of p95p over the terrace (the sill at its river end), cross-section by
                  cross-section from the terrain (width and area of the contiguous section below the local water level, perpendicular to
                  the path), the water level linear along the path between H_up and max(h, downstream crest), never below the terrain + 5 cm:
                  Q = f_W / n * sqrt(dH / sum(dx/K^2)),
                  K = A^(5/3) / w^(2/3); reversed when the depression stands higher than the river;
  Q 'weir'      = the fast limit: a broad-crested sill of the same cross-section at the sill (C_d w (H_up - z_s)^1.5, Villemonte submergence).
Priors (nothing is fitted; UNOSAT stays a hold-out): sill U(8.75, 8.95) m (ICESat-2 verified 8.85, p95p; shifts the whole path); floor offset
U(-1.2, 0) m on the storage ground (model 1.1 m above ICESat-2 ground in the lowland, p95p); terrain sigma uniform on {0, 0.25, 0.5, 0.75, 1} m; Manning n logU(0.03, 0.15); width
factor f_W logU(0.3, 3) (parallel paths, cross-section error); C_d U(1.4, 1.7) (weir); ET U(3, 7) mm/d; infiltration + local drainage k
logU(1, 100) mm/d.
Comparison at the acquisition times (ICEYE 7 June 12:40, Landsat-9 9 June ~08:30, Sentinel-2 13 June 08:57, Sentinel-1 21 June ~16:05 UTC)
on the ground of D that the sensor observed and that was dry before the breach in both references: observed, primary, memory, and the
prior-predictive distribution of the two conveyance structures (areas and CSI).
Reading of v1 (maintainer, 2026-09-30): prior-predictive testing REJECTS an instantaneous high-conveyance connection (the weir, like the
primary, fails every date); the friction-limited single reservoir reproduces the ORDER of states (little water at ICEYE midday on 7 June,
more by 9 June, a residual on 13 June, recession after) but is QUANTITATIVELY INADEQUATE (2 of 2000 prior samples pass all four dates; 9 June
median 1.8 vs 6.1 km2; 21 June median 0.95 vs 0). The terrain sigma propagates DEM uncertainty; it is not a physical spreading mechanism: the
observed water spreads from the entry (rim sections in the NW corner, 40 m open at 8.9 m, 5.8 km at 9.5 m; Landsat-9 water centroid 4 km
SE of them), which a single level h(t) cannot represent -> distributed storage cells with inter-cell fluxes (Hunter et al. 2005; local
inertial fluxes, Bates et al. 2010, doi:10.1016/j.jhydrol.2010.03.027) are the next structure. A required effective loss (~90 mm/d) is not
intrinsically incompatible with permeable sandy substrates but cannot be attributed to infiltration while soil, groundwater and artificial
drainage are unconstrained.
Outputs: tables/p95v_storage_samples.csv, p95v_storage_summary.csv, p95v_storage_inputs.csv, p95v_manifest.json; figures/m6_v003A/p95v_depression_storage.png
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
SFX = "_connected_ceiling"
TARGET_XY = (509170.0, 5167950.0)                  # the lowland floor at the end of the p95p path (z 7.60 m)
OBS_TIMES = {"07_ICEYE": "2023-06-07T12:40", "09_L9": "2023-06-09T08:30", "13_S2": "2023-06-13T08:57", "21_S1": "2023-06-21T16:05"}
T0, T1, DT_S = "2023-06-05T12:00", "2023-06-22T00:00", 1800.0


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def cross_sections(dem, tr, pts, H_grid, half=4000.0, step=20.0):
    """Width and area (per level of H_grid) of the contiguous section below H through every path point, perpendicular to the path."""
    t = np.arange(-half, half + step, step); mid = t.size // 2; n = len(pts); W = np.zeros((n, H_grid.size)); A = np.zeros_like(W)
    for i in range(n):
        j0, j1 = max(i - 5, 0), min(i + 5, n - 1); dx, dy = pts[j1, 0] - pts[j0, 0], pts[j1, 1] - pts[j0, 1]; L = np.hypot(dx, dy) or 1.0
        px, py = pts[i, 0] - t * dy / L, pts[i, 1] + t * dx / L
        r = np.floor((tr.f - py) / step).astype(int); c = np.floor((px - tr.c) / step).astype(int)
        ok = (r >= 0) & (r < dem.shape[0]) & (c >= 0) & (c < dem.shape[1]); z = np.full(t.size, np.inf); z[ok] = dem[r[ok], c[ok]]; z = np.nan_to_num(z, nan=np.inf)
        m = z[None, :] < H_grid[:, None]
        lp = m[:, :mid][:, ::-1]; kl = np.where((~lp).any(1), np.argmax(~lp, 1), mid)
        rp = m[:, mid + 1:]; kr = np.where((~rp).any(1), np.argmax(~rp, 1), rp.shape[1])
        on = m[:, mid]; W[i] = np.where(on, (kl + kr + 1) * step, 0.0)
        depth = np.clip(H_grid[:, None] - z[None, :], 0, None); cs = np.cumsum(depth, 1)
        left, right = mid - kl, mid + kr
        A[i] = np.where(on, (cs[np.arange(H_grid.size), right] - np.where(left > 0, cs[np.arange(H_grid.size), np.maximum(left - 1, 0)], 0.0)) * step, 0.0)
    return W, A


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=2000); ap.add_argument("--seed", type=int, default=20260930)
    a = ap.parse_args(); t_start = time.time()
    import pandas as pd
    from rasterio import features
    from scipy import ndimage
    from shapely.geometry import shape
    from shapely.ops import unary_union
    from floodstate_eo import _kakhovka_legacy_config as CFG
    TAB = ROOT / "tables"; FIG = ROOT / "figures" / "m6_v003A"
    O = _ld("p95o", HERE / "p95o_component_qa.py"); P95 = O._ld("p95_hand_daily_inundation"); P = P95.load_p92(); T = _ld("p95t", HERE / "p95t_eo_recession.py")
    man = O.load_manifest(SFX); c = man["constants"]; margin = float(c.get("margin_m", 0.0))
    M = P95.mosaic_layers(P, with_s1=False); g = M["grid"]; tr = g.transform; dem = M["dem"]
    W_eng, dxm, _ = O.engine_for(P95, man, SFX); M["base"] = M["base_geom"] & P95.dam_mask(M, dxm); Z = W_eng.prepare(M)
    baseline = O.compose_npz(M, SFX, "baseline")
    rc = lambda x, y: (int((tr.f - y) // g.cell), int((x - tr.c) // g.cell))
    # ---- the path of p95p: sill, terrace, river-side foot ----------------------------------------------------------------------
    prof = pd.read_csv(TAB / "p95p_saddle_profile_kozachi_laheri_lowland.csv")
    zp = prof.z_model_m.to_numpy(); i_sill = int(np.argmax(np.where(prof.s_m.to_numpy() < 12000, zp, -np.inf))); z_sill0 = float(zp[i_sill])
    after = np.nonzero(zp[i_sill:] >= 8.0)[0]; i_edge = i_sill + int(after.max()); z_edge0 = float(zp[i_edge])
    i_foot = int(np.nonzero(zp[:i_sill] < 2.0)[0].max())
    seg = prof.iloc[i_sill:i_edge + 1]; pts = seg[["x", "y"]].to_numpy(float); zseg = seg.z_model_m.to_numpy(float)
    dxs = np.diff(seg.s_m.to_numpy(float), append=seg.s_m.iloc[-1] + 20.0)
    frac = (seg.s_m.to_numpy(float) - seg.s_m.iloc[0]) / max(seg.s_m.iloc[-1] - seg.s_m.iloc[0], 1.0)
    H_grid = np.round(np.arange(7.8, 10.81, 0.01), 2)
    Wxs, Axs = cross_sections(dem, tr, pts, H_grid)
    print(f"path: sill {z_sill0:.2f} m at s {seg.s_m.iloc[0]/1e3:.2f} km, edge {z_edge0:.2f} m at s {seg.s_m.iloc[-1]/1e3:.2f} km, terrace length "
          f"{(seg.s_m.iloc[-1]-seg.s_m.iloc[0])/1e3:.2f} km, {len(seg)} sections; foot at s {prof.s_m.iloc[i_foot]/1e3:.2f} km", flush=True)
    # ---- H_up(t): the reconstruction's surface at the river-side foot ------------------------------------------------------------
    fr, fc = rc(prof.x.iloc[i_foot], prof.y.iloc[i_foot]); days = pd.date_range("2023-06-05", "2023-06-23", freq="D")
    H_day = np.array([float(W_eng.field(Z, str(d.date()), margin)[fr, fc]) for d in days])
    t_day = (days + pd.Timedelta(hours=12) - pd.Timestamp(T0)).total_seconds().to_numpy()
    print("H_up daily:", dict(zip([str(d.date())[5:] for d in days], np.round(H_day, 2))), flush=True)
    # ---- the depression and its storage ground ----------------------------------------------------------------------------------
    # v1 (2026-09-30): the new water spreads over the ground of the depression that was dry before the breach (the pre-breach water of the
    # lowland is scattered wetland at 6.2-8.6 m, not a lake at the bottom), the depression starts empty, and the hypsometry is smoothed by
    # the terrain error sigma (the observed water of 9 June sits at every elevation of the depression: a bathtub on this terrain cannot
    # place it cell by cell; areas and volumes are the test).
    tr_r, tr_c = rc(*TARGET_XY); lab, _n = ndimage.label(np.nan_to_num(dem, nan=99.0) < z_sill0, structure=np.ones((3, 3), bool)); D = lab == lab[tr_r, tr_c]
    G = D & ~baseline; A_pre_cells = int((D & baseline).sum()); ca = g.cell ** 2
    print(f"depression: {D.sum()*ca/1e6:.1f} km2, pre-breach water {A_pre_cells*ca/1e6:.1f} km2, storage ground {G.sum()*ca/1e6:.1f} km2", flush=True)
    hg = np.round(np.arange(3.0, 11.0, 0.01), 2); SIG = (0.0, 0.25, 0.5, 0.75, 1.0)
    from scipy.stats import norm as _norm

    def exp_area_table(z, sig):
        """Expected flooded cells (sum of P(z_true < h)) of cells with terrain z, on hg, for a terrain error sigma."""
        hist, edges = np.histogram(z, bins=np.arange(3.0, 11.02, 0.01)); zc = 0.5 * (edges[:-1] + edges[1:])
        if sig == 0.0:
            return np.concatenate([[0], np.cumsum(hist)])[np.clip(np.searchsorted(zc, hg, side="right"), 0, hist.size)].astype(float)
        return (_norm.cdf((hg[:, None] - zc[None, :]) / sig) * hist[None, :]).sum(1)
    AG = {sg: exp_area_table(dem[G], sg) * ca for sg in SIG}
    VG = {sg: np.concatenate([[0.0], np.cumsum(0.5 * (AG[sg][1:] + AG[sg][:-1]) * 0.01)]) for sg in SIG}
    # ---- samples ----------------------------------------------------------------------------------------------------------------
    rng = np.random.default_rng(a.seed); N = a.n
    lu = lambda lo, hi, k: np.exp(rng.uniform(np.log(lo), np.log(hi), k))
    S = {"friction": {}, "weir": {}}
    for st in S:
        S[st] = dict(sill=rng.uniform(8.75, 8.95, N), dz=rng.uniform(-1.2, 0.0, N), sigma=rng.choice(SIG, N), n=lu(0.03, 0.15, N), fW=lu(0.3, 3.0, N),
                     Cd=rng.uniform(1.4, 1.7, N), ET=rng.uniform(3, 7, N) / 1000.0 / 86400.0, k=lu(1, 100, N) / 1000.0 / 86400.0)
    nsteps = int((pd.Timestamp(T1) - pd.Timestamp(T0)).total_seconds() // DT_S) + 1; tt = np.arange(nsteps) * DT_S
    Hup_t = np.interp(tt, t_day, H_day); obs_idx = {k: int(round((pd.Timestamp(v) - pd.Timestamp(T0)).total_seconds() / DT_S)) for k, v in OBS_TIMES.items()}
    zc_dn = float(zseg[seg.s_m.to_numpy(float) > seg.s_m.iloc[0] + 1000.0].max())                  # the downstream crest of the terrace
    print(f"downstream crest {zc_dn:.2f} m", flush=True)
    Vgrid = np.concatenate([[0.0], np.geomspace(1.0, 5e8, 3000)])
    rowsP = np.arange(len(zseg))[None, :]; res = {}
    for st, p in S.items():
        sh = p["sill"] - z_sill0; zcrest = zc_dn + sh; zsill = p["sill"]
        At = np.stack([np.interp(hg - p["dz"][i], hg, AG[p["sigma"][i]]) for i in range(N)])        # A(h) with the floor offset
        Vt = np.stack([np.interp(hg - p["dz"][i], hg, VG[p["sigma"][i]]) for i in range(N)])
        hinv = np.stack([np.interp(Vgrid, Vt[i] + 1e-9 * np.arange(hg.size), hg) for i in range(N)])
        V = np.zeros(N); h = hinv[:, 0].copy(); rec_h = np.zeros((N, nsteps), "f4"); rec_A = np.zeros((N, nsteps), "f4"); Qrec = np.zeros((N, nsteps), "f4")
        for s_ in range(nsteps):
            Hu = Hup_t[s_]
            inflow = Hu > np.maximum(h, zcrest)                      # river above the terrace crest and above the depression
            outflow = (h > zcrest) & (h > Hu)                         # depression above the crest and above the river
            Q = np.zeros(N)
            if st == "friction":
                Hhi = np.where(inflow, Hu, h); Hlo = np.where(inflow, np.maximum(h, zcrest), np.maximum(Hu, zsill)); dH = np.clip(Hhi - Hlo, 0, None)
                prof_ = np.where(inflow[:, None], Hhi[:, None] + (Hlo - Hhi)[:, None] * frac[None, :], Hlo[:, None] + (Hhi - Hlo)[:, None] * frac[None, :])
                Hi = np.maximum(prof_, zseg[None, :] + sh[:, None] + 0.05)                            # never below the terrain + 5 cm
                idx = np.clip(np.round((Hi - sh[:, None] - H_grid[0]) / 0.01).astype(int), 0, H_grid.size - 1)
                w = Wxs[rowsP, idx]; ar = Axs[rowsP, idx]
                with np.errstate(divide="ignore", invalid="ignore"):
                    K = np.where((w > 0) & (ar > 0), ar ** (5.0 / 3.0) / w ** (2.0 / 3.0), 0.0)
                    R = np.where(K > 0, dxs[None, :] / K ** 2, np.inf).sum(1)
                Q = np.where((inflow | outflow) & np.isfinite(R) & (dH > 0), p["fW"] / p["n"] * np.sqrt(dH / R), 0.0)
            else:
                Hhi = np.where(inflow, Hu, h); Hlo = np.where(inflow, h, Hu)
                idx = np.clip(np.round((Hhi - sh - H_grid[0]) / 0.01).astype(int), 0, H_grid.size - 1); w0 = Wxs[0, idx]
                h1 = np.clip(Hhi - zsill, 0, None); h2 = np.clip(Hlo - zsill, 0, None)
                with np.errstate(divide="ignore", invalid="ignore"):
                    sub = np.where(h1 > 0, np.clip(1 - (h2 / h1) ** 1.5, 0, 1) ** 0.385, 0.0)
                Q = np.where(inflow | outflow, p["Cd"] * p["fW"] * w0 * h1 ** 1.5 * sub, 0.0)
            Q = np.where(outflow, -np.minimum(Q, V / DT_S), Q)
            Anow = At[np.arange(N), np.clip(np.round((h - hg[0]) / 0.01).astype(int), 0, hg.size - 1)]
            V = np.maximum(V + DT_S * (Q - (p["ET"] + p["k"]) * Anow), 0.0)
            j = np.clip(np.searchsorted(Vgrid, V) - 1, 0, Vgrid.size - 2); f = np.clip((V - Vgrid[j]) / (Vgrid[j + 1] - Vgrid[j]), 0, 1)
            h = hinv[np.arange(N), j] * (1 - f) + hinv[np.arange(N), j + 1] * f
            rec_h[:, s_] = h; rec_A[:, s_] = Anow; Qrec[:, s_] = Q
        res[st] = dict(h=rec_h, A=rec_A, Q=Qrec, V_in_hm3=np.clip(Qrec, 0, None).sum(1) * DT_S / 1e6)
        print(st, "done; inflow volume hm3 p5/p50/p95", np.percentile(res[st]["V_in_hm3"], [5, 50, 95]).round(2), round(time.time() - t_start), "s", flush=True)
    # ---- the observations on the depression -----------------------------------------------------------------------------------
    ras = lambda nm: features.rasterize([(unary_union([shape(f_["geometry"]) for f_ in json.loads((T.utm_dir(CFG.BULK_ROOT) / f"{nm}.geojson").read_text())["features"]]), 1)],
                                        out_shape=g.shape, transform=tr, fill=0, dtype="uint8").astype(bool)
    dry = G & ~ras(T.REF)
    rows, srows = [], []
    for k, (d, sensor, wl, al, cl) in T.EO.items():
        if k not in OBS_TIMES:
            continue
        ob = ras(al) & dry
        if cl:
            ob &= ~ras(cl)
        eo = ras(wl) & ob; nom = O.compose_npz(M, SFX, d) & ob; mem = O.compose_npz(M, "_connected_ceiling_memory", d) & ob
        n_eo = int(eo.sum()); a_eo = n_eo * ca / 1e6
        TOB = {sg: exp_area_table(dem[ob], sg) for sg in SIG}; TTP = {sg: exp_area_table(dem[eo], sg) for sg in SIG}
        csi = lambda tp, am_, ae: tp / (am_ + ae - tp) if (am_ + ae - tp) > 0 else np.nan
        tpn, an = int((nom & eo).sum()), int(nom.sum()); tpm, am = int((mem & eo).sum()), int(mem.sum())
        base = dict(eo=k, date=d, sensor=sensor, observed_dry_km2=round(ob.sum() * ca / 1e6, 2), A_EO_km2=round(a_eo, 2), A_primary_km2=round(an * ca / 1e6, 2),
                    CSI_primary=round(csi(tpn, an, n_eo), 3), A_memory_km2=round(am * ca / 1e6, 2), CSI_memory=round(csi(tpm, am, n_eo), 3))
        for st, rr in res.items():
            hh = rr["h"][:, obs_idx[k]]; pp = S[st]
            am_ = np.array([np.interp(hh[i] - pp["dz"][i], hg, TOB[pp["sigma"][i]]) for i in range(N)])
            tp = np.array([np.interp(hh[i] - pp["dz"][i], hg, TTP[pp["sigma"][i]]) for i in range(N)])
            A_m = am_ * ca / 1e6; C_m = np.where(am_ + n_eo - tp > 0, tp / np.maximum(am_ + n_eo - tp, 1e-9), np.nan)
            rr[f"A_{k}"] = A_m; rr[f"CSI_{k}"] = C_m
            q = np.nanpercentile(A_m, [5, 25, 50, 75, 95]); qc = np.nanpercentile(C_m, [5, 50, 95])
            srows.append(dict(base, structure=st, A_p05=round(q[0], 2), A_p25=round(q[1], 2), A_p50=round(q[2], 2), A_p75=round(q[3], 2), A_p95=round(q[4], 2),
                              CSI_p05=round(qc[0], 3), CSI_p50=round(qc[1], 3), CSI_p95=round(qc[2], 3)))
        rows.append(base)
    SUM = pd.DataFrame(srows)
    # consistency with the hold-out: within a factor 2 of the observed area on 7, 9 and 13 June and <= 0.5 km2 on 21 June
    for st, rr in res.items():
        ok = np.ones(N, bool)
        for k in OBS_TIMES:
            ae = SUM[(SUM.eo == k) & (SUM.structure == st)].A_EO_km2.iloc[0]; am_ = rr[f"A_{k}"]
            ok &= (am_ <= 0.5) if ae < 0.25 else (np.abs(np.log(np.maximum(am_, 1e-3) / ae)) <= np.log(2.0))
        rr["consistent"] = ok
        SUM.loc[SUM.structure == st, "share_samples_consistent_all_dates"] = round(float(ok.mean()), 3)
    SUM.to_csv(TAB / "p95v_storage_summary.csv", index=False)
    samp = []
    for st, rr in res.items():
        dfp = pd.DataFrame({k_: v for k_, v in S[st].items()}); dfp["ET"] *= 86400e3; dfp["k"] *= 86400e3; dfp.insert(0, "structure", st)
        for k in OBS_TIMES:
            dfp[f"A_{k}_km2"] = np.round(rr[f"A_{k}"], 3); dfp[f"CSI_{k}"] = np.round(rr[f"CSI_{k}"], 3)
        dfp["inflow_hm3"] = np.round(rr["V_in_hm3"], 3); dfp["h_max_m"] = np.round(rr["h"].max(1), 3); dfp["consistent_all_dates"] = rr["consistent"]; samp.append(dfp)
    SA = pd.concat(samp, ignore_index=True); SA.to_csv(TAB / "p95v_storage_samples.csv", index=False)
    pd.DataFrame(dict(day=[str(d.date()) for d in days], H_up_m=np.round(H_day, 3))).assign(sill_m=z_sill0, edge_m=z_edge0, depression_km2=round(D.sum() * ca / 1e6, 2),
        prebreach_water_km2=round(A_pre_cells * ca / 1e6, 2)).to_csv(TAB / "p95v_storage_inputs.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(SUM.drop(columns=["sensor"]).to_string(index=False))
    for st in res:
        ok = SA[(SA.structure == st) & SA.consistent_all_dates]
        print(f"\n{st}: {len(ok)} of {N} prior samples consistent with all four dates" + (f"; their medians: n {ok.n.median():.3f}, f_W {ok.fW.median():.2f}, dz {ok.dz.median():.2f} m, "
              f"k {ok.k.median():.1f} mm/d, sigma {ok.sigma.median():.2f} m, inflow {ok.inflow_hm3.median():.1f} hm3" if len(ok) else ""))
    # ---- figure ----------------------------------------------------------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    time_ax = pd.Timestamp(T0) + pd.to_timedelta(tt, unit="s")
    fig, axs = plt.subplots(1, 3, figsize=(17, 5.2), constrained_layout=True)
    ax = axs[0]; ax.plot(time_ax, Hup_t, color="#16324f", lw=1.5, label="H_up: reconstruction surface, river-side foot")
    ax.axhline(z_sill0, color="#e34948", ls="--", lw=1, label=f"sill {z_sill0:.2f} m (p95p, ICESat-2 verified)")
    for st, colr in (("friction", "#2a78d6"), ("weir", "#eda100")):
        q = np.percentile(res[st]["h"], [5, 50, 95], axis=0); ax.fill_between(time_ax, q[0], q[2], color=colr, alpha=0.2); ax.plot(time_ax, q[1], color=colr, lw=1.3, label=f"depression level, {st} (median, 5-95 %)")
    ax.set_ylim(6.0, 10.0); ax.set_ylabel("m EVRF2019", fontsize=7); ax.legend(fontsize=6); ax.grid(alpha=0.3); ax.set_title("water levels", fontsize=8)
    ax = axs[1]; nomA, memA, dts = [], [], []
    for d in days:
        ds = str(d.date())
        if ds > T1[:10]:
            continue
        dts.append(pd.Timestamp(ds) + pd.Timedelta(hours=12)); nomA.append((O.compose_npz(M, SFX, ds) & D).sum() * ca / 1e6); memA.append((O.compose_npz(M, "_connected_ceiling_memory", ds) & D).sum() * ca / 1e6)
    ax.plot(dts, nomA, "s-", color="#16324f", ms=3, lw=1.2, label="primary (daily)"); ax.plot(dts, memA, "^--", color="#7f7f7f", ms=3, lw=1.2, label="memory (daily)")
    for st, colr in (("friction", "#2a78d6"), ("weir", "#eda100")):
        A_t = res[st]["A"] / 1e6
        q = np.percentile(A_t, [5, 50, 95], axis=0); ax.fill_between(time_ax, q[0], q[2], color=colr, alpha=0.2); ax.plot(time_ax, q[1], color=colr, lw=1.3, label=f"storage model, {st}")
    ax.set_ylabel("new water in the depression, km2 (whole depression)", fontsize=7); ax.legend(fontsize=6); ax.grid(alpha=0.3); ax.set_title(f"new water, depression {D.sum()*ca/1e6:.0f} km2", fontsize=8)
    ax = axs[2]; xs_ = np.arange(len(OBS_TIMES))
    for j, k in enumerate(OBS_TIMES):
        r0 = SUM[SUM.eo == k].iloc[0]
        ax.plot(j, r0.A_EO_km2, "o", color="k", ms=8, label="observed (UNOSAT)" if j == 0 else None)
        ax.plot(j - 0.25, r0.A_primary_km2, "s", color="#16324f", label="primary" if j == 0 else None); ax.plot(j + 0.25, r0.A_memory_km2, "^", color="#7f7f7f", label="memory" if j == 0 else None)
        for off, st, colr in ((-0.1, "friction", "#2a78d6"), (0.1, "weir", "#eda100")):
            v = res[st][f"A_{k}"]; ax.boxplot([v], positions=[j + off], widths=0.12, whis=(5, 95), showfliers=False, patch_artist=True,
                                               boxprops=dict(facecolor=colr, alpha=0.5), medianprops=dict(color="k"))
    ax.set_xticks(xs_); ax.set_xticklabels([f"{OBS_TIMES[k][5:10]}\n{k[3:]}" for k in OBS_TIMES], fontsize=7); ax.set_yscale("symlog", linthresh=0.5)
    ax.set_ylabel("new water on the observed, dry-before ground of the depression, km2", fontsize=7); ax.grid(alpha=0.3)
    ax.legend(handles=ax.get_legend_handles_labels()[0] + [matplotlib.patches.Patch(fc="#2a78d6", alpha=0.5, label="storage model, friction (5-95 %)"),
                                                          matplotlib.patches.Patch(fc="#eda100", alpha=0.5, label="storage model, weir (5-95 %)")], fontsize=6)
    ax.set_title("hold-out: observed vs frozen variants vs storage prior", fontsize=8)
    import matplotlib.dates as mdates
    for ax_ in axs[:2]:
        ax_.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m")); ax_.tick_params(axis="x", labelsize=7)
    fig.suptitle("DEPRESSION_STORAGE v1, lowland south of Krynky: mass balance through the p95p sill and terrace, uncalibrated priors; UNOSAT 7/9/13/21 June is the hold-out", fontsize=8)
    FIG.mkdir(parents=True, exist_ok=True); fig.savefig(FIG / "p95v_depression_storage.png", dpi=150); plt.close(fig)
    (TAB / "p95v_manifest.json").write_text(json.dumps(dict(
        producer="p95v_depression_storage.py", version="v1 (one depression, prior-predictive)", n_samples=N, seed=a.seed, dt_s=DT_S, window=[T0, T1], obs_times=OBS_TIMES,
        sill_m=z_sill0, edge_m=z_edge0, terrace_km=round((seg.s_m.iloc[-1] - seg.s_m.iloc[0]) / 1e3, 2), depression_km2=round(D.sum() * ca / 1e6, 2),
        prebreach_water_km2=round(A_pre_cells * ca / 1e6, 2), storage_ground_km2=round(G.sum() * ca / 1e6, 2), terrain_sigma_m=list(SIG),
        priors=dict(sill="U(8.75, 8.95)", floor_offset="U(-1.2, 0) on the storage ground", terrain_sigma="uniform on {0, 0.25, 0.5, 0.75, 1.0} m", n="logU(0.03, 0.15)", f_W="logU(0.3, 3)", C_d="U(1.4, 1.7)", ET_mm_d="U(3, 7)", k_mm_d="logU(1, 100)"),
        consistency="within a factor 2 of the observed area on 7, 9, 13 June (<= 0.5 km2 where observed < 0.25) -- a check, not a fit",
        not_modelled="rain; groundwater; parallel inflow paths other than the minimax path (f_W stands for them); sub-daily H_up (daily values at 12:00 UTC)"), indent=1))
    print("->", TAB / "p95v_storage_summary.csv", round(time.time() - t_start), "s")


if __name__ == "__main__":
    main()
