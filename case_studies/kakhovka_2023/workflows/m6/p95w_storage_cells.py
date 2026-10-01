# New in floodstate-eo, 2026-09-30 (maintainer: DEPRESSION_STORAGE v2 -- distributed storage cells, full ensemble). STATUS: ACTIVE.
# Diagnostic: one floodplain lowland, prior-predictive, NOT the reconstruction product.
"""P95w -- DEPRESSION_STORAGE v2: distributed storage cells with finite inter-cell fluxes for the floodplain lowland south of Krynky, tested
without calibration against the satellite-observed new water of 7, 9, 13 and 21 June 2023 (UNOSAT 3614, the p95t masks, kept as hold-out).

Why v2: v1 (p95v, one reservoir with a single level h(t)) reproduced the order of states but failed the quantitative hold-out (2 of 2000
prior samples); the observed water of 9 June spreads from the entry (the rim opens in the NW corner only: 40 m at 8.9 m, 5.8 km at 9.5 m;
Landsat-9 water centroid 4 km SE of it), which one level cannot represent.

Model (storage cells, Hunter et al. 2005, doi:10.1016/j.advwatres.2005.03.007; local inertial fluxes, Bates et al. 2010,
doi:10.1016/j.jhydrol.2010.03.027):
  cells     200 m; each cell stores water over its own 20 m terrain (sub-grid hypsometry V_i(eta), A_i(eta)); a cell is inactive where
            its lowest 20 m terrain lies above 10 m (never wet in June 2023);
  faces     4-neighbour faces; each crossing is one pair of adjacent 20 m cells across the shared edge, z_max,k = the higher of the two;
            wetted face area A_face(eta) = sum_k max(eta - z_max,k, 0) dx_sub, prestored with the wet width w(eta) before the run, ONE
            local-inertial flux per face with d = A_face / w (the subgrid local-inertial formulation of Nithila Devi & Kuiry 2024,
            doi:10.1029/2023WR035334; subgrid connectivity: Neal et al. 2012, doi:10.1029/2012WR012514; Milzow & Kinzelbach 2010,
            doi:10.1029/2009WR008088; a subgrid model still depends on the computational resolution: van Ormondt et al. 2025,
            doi:10.5194/gmd-18-843-2025 -> the 200 m vs 100 m test on the same parameter sets, --cell-m / --run-ids / --convergence);
  flux      q <- (q - g d dt (eta_b - eta_a)/dx) / (1 + g dt n^2 |q| / d^(7/3)),  Q = q * wet width   (per unit width, m2/s)
  mass      V_i += dt (sum Q_in - sum Q_out) - dt (ET + k) A_i(eta_i); outflow limited to the cell's volume; V_i >= 0
  boundary  cells outside the depression whose median terrain is below 3 m (the Dnipro floodplain) carry the reconstruction's water
            surface (p95 engine, nominal, daily at 12:00 UTC, linear in time): every rim section opens by itself when the river rises
  time step adaptive, dt = 0.7 dx / sqrt(g d_max), at most 300 s
Priors (Latin hypercube, nothing fitted): Manning n logU(0.03, 0.15); floor offset of the lowland bowl (depression cells with median
terrain < 8.2 m) U(-1.2, 0) m (model 1.1 m above ICESat-2 ground there, p95p); rim / terrace offset U(-0.1, 0.1) m (sill verified +-0.1 m);
ET U(3, 7) mm/d; infiltration + local drainage k logU(1, 100) mm/d. A required loss is 'not intrinsically incompatible' with sandy
substrates but is not attributed to infiltration: soil, groundwater and artificial drainage are unconstrained.
Test (hold-out, the p95v masks): new water on the ground of the depression that the sensor observed and that was dry before the breach in
both references, per 20 m cell (a 20 m cell is wet when its terrain lies below its 200 m cell's level): area, CSI, and where the water is on
9 June (centroid, distance from the sill) -- against the observations and the frozen primary / memory variants.
Outputs (per cell size): tables/p95w_cells_runs_<m>m.csv, p95w_cells_summary_<m>m.csv, p95w_manifest_<m>m.json, figures/m6_v003A/p95w_storage_cells_<m>m.png;
         --convergence: tables/p95w_convergence.csv (the same parameter sets at 200 m and 100 m)
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
TARGET_XY = (509170.0, 5167950.0); SILL_XY = (504930.0, 5174670.0); SILL_Z = 8.85
OBS_TIMES = {"07_ICEYE": "2023-06-07T12:40", "09_L9": "2023-06-09T08:30", "13_S2": "2023-06-13T08:57", "21_S1": "2023-06-21T16:05"}
T0, T1 = "2023-06-05T12:00", "2023-06-22T00:00"
G = 9.81; ALPHA = 0.7; DT_MAX = 300.0; WET_TOP = 10.0; BOWL_TOP = 8.2; BC_MEDIAN = 3.0
LVL = np.round(np.arange(3.0, 11.0001, 0.02), 3)


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def lhs(n, k, rng):
    """Latin hypercube in [0, 1)^k."""
    u = (np.argsort(rng.random((k, n)), axis=1).T + rng.random((n, k))) / n
    return u


def integrate_torch(L):
    """The time loop of main() in torch on the GPU: the same equations, tables and order of operations as the numpy loop (float64).
    Returns (snaps, day_snaps, nsteps) with numpy arrays, as the numpy loop leaves them."""
    import pandas as pd
    import torch
    dev = torch.device("cuda"); f64 = torch.float64
    torch.use_deterministic_algorithms(True)                                                   # index_add_ sorted, not atomic: repeatable runs
    T_ = lambda x, dt_=f64: torch.as_tensor(np.ascontiguousarray(x), device=dev, dtype=dt_)
    N, nF, nCells, dxc, t_end = L["N"], L["nF"], L["nCells"], L["dxc"], L["t_end"]
    Vtab, Atab, Wtab, Dtab = T_(L["Vtab"]), T_(L["Atab"]), T_(L["Wtab"]), T_(L["Dtab"]); LV = T_(LVL); L0 = float(LVL[0]); nL = LVL.size
    zmin, sc, sf = T_(L["zmin"]), T_(L["shift_c"]), T_(L["shift_f"])
    fa, fb, bidx = T_(L["fa"], torch.long), T_(L["fb"], torch.long), T_(L["bidx"], torch.long)
    Hb, t_day = T_(L["Hb"]), L["t_day"]; act = T_(L["act"], torch.bool)[None, :]
    n2 = (T_(L["prm"]["n"]) ** 2)[:, None]; loss = T_(L["prm"]["ET"] + L["prm"]["k"])[:, None]
    V = torch.zeros((N, nCells), dtype=f64, device=dev); q = torch.zeros((N, nF), dtype=f64, device=dev)
    eta = zmin[None, :] + sc; jidx = ((eta - sc - L0) / 0.02).long().clamp(0, nL - 2)
    fr_ = torch.arange(nF, device=dev)[None, :].expand(N, nF); cr_ = torch.arange(nCells, device=dev)[None, :].expand(N, nCells)
    obs_t, day_t, T0_ = L["obs_t"], L["day_t"], pd.Timestamp(T0)
    snaps, day_snaps = {}, {}; tt, nsteps, last = 0.0, 0, time.time()
    while tt < t_end:
        iday = int(np.clip(np.searchsorted(t_day, tt, side="right") - 1, 0, t_day.size - 2)); wd = float(np.clip((tt - t_day[iday]) / (t_day[iday + 1] - t_day[iday]), 0, 1))
        eta[:, bidx] = (Hb[iday] * (1 - wd) + Hb[iday + 1] * wd)[None, :]
        up = torch.maximum(eta[:, fa], eta[:, fb]); lf = ((up - sf - L0) / 0.02).long().clamp(0, nL - 1)
        w = Wtab[fr_, lf]; d = Dtab[fr_, lf]
        dmax = float(torch.where(w > 0, d, torch.zeros_like(d)).max())
        dt = min(DT_MAX, ALPHA * dxc / np.sqrt(G * max(dmax, 0.05)), t_end - tt)
        for kk, tk in obs_t.items():
            if kk not in snaps and tt + dt >= tk:
                snaps[kk] = eta.cpu().numpy().copy()
        for dd, tk in day_t:
            if str(dd.date()) not in day_snaps and tt + dt >= tk and tk <= t_end:
                day_snaps[str(dd.date())] = eta.cpu().numpy().copy()
        slope = (eta[:, fb] - eta[:, fa]) / dxc; wet = (w > 0) & (d > 1e-3)
        qn = (q - G * d * dt * slope) / (1.0 + G * dt * n2 * q.abs() / torch.where(wet, d, torch.ones_like(d)) ** (7.0 / 3.0))
        q = torch.where(wet, qn, torch.zeros_like(qn)); Q = q * w
        out = torch.zeros((N, nCells), dtype=f64, device=dev).index_add_(1, fa, Q.clamp(min=0)).index_add_(1, fb, (-Q).clamp(min=0))
        lim = torch.where(out * dt > V, V / (out * dt).clamp(min=1e-12), torch.ones_like(V)); lim[:, bidx] = 1.0
        Q = torch.where(Q > 0, Q * lim[:, fa], Q * lim[:, fb]); q = torch.where(w > 0, Q / torch.where(w > 0, w, torch.ones_like(w)), torch.zeros_like(Q))
        dV = torch.zeros((N, nCells), dtype=f64, device=dev).index_add_(1, fb, Q).index_add_(1, fa, -Q)
        li = ((eta - sc - L0) / 0.02).long().clamp(0, nL - 1); Ai = Atab[cr_, li]
        V = torch.where(act, (V + dt * (dV - loss * Ai)).clamp(min=0), torch.zeros_like(V))
        for _ in range(4):
            vj = Vtab[cr_, jidx]; vj1 = Vtab[cr_, jidx + 1]
            jidx = (jidx + (V > vj1).long() - (V < vj).long()).clamp(0, nL - 2)
        vj = Vtab[cr_, jidx]; vj1 = Vtab[cr_, jidx + 1]
        fr = torch.where(vj1 > vj, ((V - vj) / (vj1 - vj).clamp(min=1e-12)).clamp(0, 1), torch.zeros_like(V))
        eta_new = LV[jidx] + 0.02 * fr + sc
        eta = torch.where(act, torch.where(V > 0, eta_new, zmin[None, :] + sc), eta)
        tt += dt; nsteps += 1
        if time.time() - last > 60:
            print(f"  [cuda] t = {T0_ + pd.Timedelta(seconds=tt)}  steps {nsteps}  dt {dt:.1f} s  d_max {dmax:.2f} m", flush=True); last = time.time()
    return snaps, day_snaps, nsteps


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--runs", type=int, default=100, help="size of the Latin hypercube"); ap.add_argument("--seed", type=int, default=20260930)
    ap.add_argument("--run-ids", type=int, nargs="*", default=None, help="integrate only these rows of the hypercube (same parameter sets across cell sizes)")
    ap.add_argument("--cell-m", type=int, default=200, choices=[100, 200, 400]); ap.add_argument("--margin-km", type=float, default=1.6)
    ap.add_argument("--convergence", action="store_true", help="compare the runs of 200 m and 100 m that share parameter sets, then exit")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="cuda: the same integration in torch on the GPU (same equations; 4 test runs agree with cpu within 0.17 km2 / CSI 0.006)")
    ap.add_argument("--out-tag", default="", help="suffix of the output names (e.g. a GPU check that must not overwrite the ensemble)")
    a = ap.parse_args(); t_start = time.time(); F = a.cell_m // 20; tag = f"{a.cell_m}m{a.out_tag}"
    if a.convergence:
        import pandas as pd
        A_, B_ = (pd.read_csv(ROOT / "tables" / f"p95w_cells_runs_{m}m.csv") for m in (200, 100))
        J = A_.merge(B_[["run", "eo", "A_model_km2", "CSI", "dist_from_sill_km"]], on=["run", "eo"], suffixes=("_200m", "_100m"))
        J["A_ratio_100_to_200"] = (J.A_model_km2_100m / J.A_model_km2_200m.replace(0, np.nan)).round(3)
        J.to_csv(ROOT / "tables" / "p95w_convergence.csv", index=False)
        pd.set_option("display.width", 250)
        print(J.groupby("eo")[["A_model_km2_200m", "A_model_km2_100m", "CSI_200m", "CSI_100m", "dist_from_sill_km_200m", "dist_from_sill_km_100m", "A_ratio_100_to_200"]].median().round(3).to_string())
        return
    import pandas as pd
    from rasterio import features
    from scipy import ndimage
    from shapely.geometry import shape
    from shapely.ops import unary_union
    from floodstate_eo import _kakhovka_legacy_config as CFG
    TAB = ROOT / "tables"; FIG = ROOT / "figures" / "m6_v003A"
    O = _ld("p95o", HERE / "p95o_component_qa.py"); P95 = O._ld("p95_hand_daily_inundation"); P = P95.load_p92(); T = _ld("p95t", HERE / "p95t_eo_recession.py")
    man = O.load_manifest(SFX); margin = float(man["constants"].get("margin_m", 0.0))
    M = P95.mosaic_layers(P, with_s1=False); g = M["grid"]; tr = g.transform; dem_full = np.nan_to_num(M["dem"], nan=99.0)
    W_eng, dxm, _ = O.engine_for(P95, man, SFX); M["base"] = M["base_geom"] & P95.dam_mask(M, dxm); Z = W_eng.prepare(M)
    baseline = O.compose_npz(M, SFX, "baseline")
    rc = lambda x, y: (int((tr.f - y) // g.cell), int((x - tr.c) // g.cell))
    lab, _n = ndimage.label(dem_full < SILL_Z, structure=np.ones((3, 3), bool)); D_full = lab == lab[rc(*TARGET_XY)]
    # ---- the 200 m domain around the depression ------------------------------------------------------------------------------
    rr, cc = np.nonzero(D_full); mg = int(a.margin_km * 1000 / g.cell)
    r0, c0 = max(rr.min() - mg, 0), max(cc.min() - mg, 0); nR = (rr.max() + mg - r0) // F + 1; nC = (cc.max() + mg - c0) // F + 1
    Wn = (slice(r0, r0 + nR * F), slice(c0, c0 + nC * F)); dem = dem_full[Wn]; Dw = D_full[Wn]; Bw = baseline[Wn]
    sub = dem.reshape(nR, F, nC, F).transpose(0, 2, 1, 3).reshape(nR * nC, F * F)            # the 20 m terrain of every 200 m cell
    Dcell = Dw.reshape(nR, F, nC, F).transpose(0, 2, 1, 3).reshape(nR * nC, F * F).mean(1) > 0.5
    med = np.median(sub, 1); zmin = sub.min(1)
    x0w, y1w = tr.c + g.cell * c0, tr.f - g.cell * r0; dxc = F * g.cell
    xc = x0w + dxc * (np.arange(nR * nC) % nC + 0.5); yc = y1w - dxc * (np.arange(nR * nC) // nC + 0.5)
    bc = (~Dcell) & (med < BC_MEDIAN)                                                          # the Dnipro floodplain: forced by the river surface
    act = (~bc) & (zmin < WET_TOP)                                                             # prognostic cells
    print(f"domain {nR} x {nC} cells of {dxc:.0f} m; prognostic {act.sum()}, boundary {bc.sum()}, depression cells {Dcell.sum()}", flush=True)
    # sub-grid tables on LVL (base terrain; per-run offsets are applied as level shifts)
    zs = np.sort(sub, 1)
    Vtab = np.zeros((nR * nC, LVL.size)); Atab = np.zeros_like(Vtab)
    for j0 in range(0, LVL.size, 50):
        L = LVL[j0:j0 + 50]; wet = zs[:, :, None] < L[None, None, :]
        Atab[:, j0:j0 + 50] = wet.sum(1) * g.cell ** 2; Vtab[:, j0:j0 + 50] = ((L[None, None, :] - zs[:, :, None]) * wet).sum(1) * g.cell ** 2
    # faces: east and south neighbours between active / boundary cells
    idx = np.arange(nR * nC).reshape(nR, nC); cells_on = act | bc
    fa, fb, fz = [], [], []
    subg = sub.reshape(nR, nC, F, F)
    for (da, db, get) in ((idx[:, :-1], idx[:, 1:], lambda A, B: np.maximum(subg[A // nC, A % nC][:, :, -1], subg[B // nC, B % nC][:, :, 0])),
                          (idx[:-1, :], idx[1:, :], lambda A, B: np.maximum(subg[A // nC, A % nC][:, -1, :], subg[B // nC, B % nC][:, 0, :]))):
        A_, B_ = da.ravel(), db.ravel(); keep = (cells_on[A_] & cells_on[B_]) & ~(bc[A_] & bc[B_])
        A_, B_ = A_[keep], B_[keep]; zc = get(A_, B_); low = zc.min(1) < WET_TOP
        fa.append(A_[low]); fb.append(B_[low]); fz.append(zc[low])
    fa, fb, fz = np.concatenate(fa), np.concatenate(fb), np.concatenate(fz); nF = fa.size
    Wtab = np.zeros((nF, LVL.size)); Dtab = np.zeros_like(Wtab)
    for j0 in range(0, LVL.size, 50):
        L = LVL[j0:j0 + 50]; dep = np.clip(L[None, None, :] - fz[:, :, None], 0, None); wet = dep > 0
        n_w = wet.sum(1); Wtab[:, j0:j0 + 50] = n_w * g.cell; Dtab[:, j0:j0 + 50] = np.where(n_w > 0, dep.sum(1) / np.maximum(n_w, 1), 0.0)
    from scipy import sparse
    Inc = sparse.csr_matrix((np.concatenate([-np.ones(nF), np.ones(nF)]), (np.concatenate([fa, fb]), np.concatenate([np.arange(nF)] * 2))), shape=(nR * nC, nF))
    Ia = sparse.csr_matrix((np.ones(nF), (fa, np.arange(nF))), shape=(nR * nC, nF)); Ib = sparse.csr_matrix((np.ones(nF), (fb, np.arange(nF))), shape=(nR * nC, nF))
    print(f"faces {nF}; tables built {round(time.time() - t_start)} s", flush=True)
    # ---- the river surface on the boundary cells ------------------------------------------------------------------------------
    days = pd.date_range("2023-06-05", "2023-06-23", freq="D"); bidx = np.nonzero(bc)[0]
    br = ((y1w - yc[bidx]) // g.cell).astype(int) + r0; bcc = ((xc[bidx] - x0w) // g.cell).astype(int) + c0
    Hb = np.stack([W_eng.field(Z, str(d.date()), margin)[br, bcc] for d in days])            # (days, boundary cells)
    t_day = (days + pd.Timedelta(hours=12) - pd.Timestamp(T0)).total_seconds().to_numpy()
    print("river surface on the boundary, median per day:", dict(zip([str(d.date())[5:] for d in days], np.round(np.median(Hb, 1), 2))), flush=True)
    # ---- priors --------------------------------------------------------------------------------------------------------------
    rng = np.random.default_rng(a.seed); U = lhs(a.runs, 5, rng); run_ids = np.array(a.run_ids if a.run_ids else range(a.runs)); U = U[run_ids]; N = run_ids.size
    prm = dict(n=np.exp(np.log(0.03) + U[:, 0] * np.log(0.15 / 0.03)), dz=-1.2 * U[:, 1], drim=-0.1 + 0.2 * U[:, 2],
               ET=(3 + 4 * U[:, 3]) / 1000.0 / 86400.0, k=np.exp(np.log(1) + U[:, 4] * np.log(100)) / 1000.0 / 86400.0)
    bowl = Dcell & (med < BOWL_TOP)
    shift_c = np.where(bowl[None, :], prm["dz"][:, None], prm["drim"][:, None]) * act[None, :]     # per run, per cell
    shift_f = 0.5 * (shift_c[:, fa] + shift_c[:, fb])
    # ---- state -----------------------------------------------------------------------------------------------------------------
    nCells = nR * nC
    V = np.zeros((N, nCells)); q = np.zeros((N, nF)); eta = np.broadcast_to(zmin[None, :] + shift_c, (N, nCells)).copy()
    jidx = np.clip(((eta - shift_c - LVL[0]) / 0.02).astype(int), 0, LVL.size - 2)
    tt, t_end = 0.0, (pd.Timestamp(T1) - pd.Timestamp(T0)).total_seconds()
    obs_t = {k: (pd.Timestamp(v) - pd.Timestamp(T0)).total_seconds() for k, v in OBS_TIMES.items()}; snaps = {}
    day_t = [(d, (pd.Timestamp(str(d.date())) + pd.Timedelta(hours=12) - pd.Timestamp(T0)).total_seconds()) for d in days]
    day_snaps = {}; nsteps = 0; last_print = time.time()
    actm = act[None, :]
    if a.device == "cuda":
        snaps, day_snaps, nsteps = integrate_torch(locals())
        tt = t_end
    while tt < t_end:
        iday = int(np.clip(np.searchsorted(t_day, tt, side="right") - 1, 0, t_day.size - 2)); wd = np.clip((tt - t_day[iday]) / (t_day[iday + 1] - t_day[iday]), 0, 1)
        eta[:, bidx] = (Hb[iday] * (1 - wd) + Hb[iday + 1] * wd)[None, :]
        # faces
        up = np.maximum(eta[:, fa], eta[:, fb]); lf = np.clip(((up - shift_f - LVL[0]) / 0.02).astype(int), 0, LVL.size - 1)
        w = Wtab[np.arange(nF)[None, :], lf]; d = Dtab[np.arange(nF)[None, :], lf]
        dmax = float(np.max(np.where(w > 0, d, 0.0)))
        dt = min(DT_MAX, ALPHA * dxc / np.sqrt(G * max(dmax, 0.05)), t_end - tt)
        for kk, tk in obs_t.items():
            if kk not in snaps and tt + dt >= tk:
                snaps[kk] = eta.copy()
        for dd, tk in day_t:
            if str(dd.date()) not in day_snaps and tt + dt >= tk and tk <= t_end:
                day_snaps[str(dd.date())] = eta.copy()
        slope = (eta[:, fb] - eta[:, fa]) / dxc; wet = (w > 0) & (d > 1e-3)
        with np.errstate(divide="ignore", invalid="ignore"):
            qn = (q - G * d * dt * slope) / (1.0 + G * dt * prm["n"][:, None] ** 2 * np.abs(q) / np.where(wet, d, 1.0) ** (7.0 / 3.0))
        q = np.where(wet, qn, 0.0); Q = q * w
        # mass limiter: a cell cannot give more than it holds
        out = (Ia @ np.clip(Q, 0, None).T + Ib @ np.clip(-Q, 0, None).T).T
        lim = np.where(out * dt > V, V / np.maximum(out * dt, 1e-12), 1.0); lim[:, bidx] = 1.0
        Q = np.where(Q > 0, Q * lim[:, fa], Q * lim[:, fb]); q = np.where(w > 0, Q / np.where(w > 0, w, 1.0), 0.0)
        dV = (Inc @ Q.T).T
        li = np.clip(((eta - shift_c - LVL[0]) / 0.02).astype(int), 0, LVL.size - 1); Ai = Atab[np.arange(nCells)[None, :], li]
        V = np.where(actm, np.maximum(V + dt * (dV - (prm["ET"] + prm["k"])[:, None] * Ai), 0.0), 0.0)
        # level from volume: local search on the base table at the shifted level
        for _ in range(4):
            vj = Vtab[np.arange(nCells)[None, :], jidx]; vj1 = Vtab[np.arange(nCells)[None, :], jidx + 1]
            jidx = np.clip(jidx + (V > vj1) - (V < vj), 0, LVL.size - 2)
        vj = Vtab[np.arange(nCells)[None, :], jidx]; vj1 = Vtab[np.arange(nCells)[None, :], jidx + 1]
        fr = np.where(vj1 > vj, np.clip((V - vj) / np.maximum(vj1 - vj, 1e-12), 0, 1), 0.0)
        eta_new = LVL[jidx] + 0.02 * fr + shift_c
        eta = np.where(actm, np.where(V > 0, eta_new, zmin[None, :] + shift_c), eta)
        tt += dt; nsteps += 1
        if time.time() - last_print > 60:
            print(f"  t = {pd.Timestamp(T0) + pd.Timedelta(seconds=tt)}  steps {nsteps}  dt {dt:.1f} s  d_max {dmax:.2f} m  {round(time.time() - t_start)} s", flush=True); last_print = time.time()
    print(f"integration done: {nsteps} steps, {round(time.time() - t_start)} s", flush=True)
    # ---- 20 m wet masks and the hold-out ---------------------------------------------------------------------------------------
    ras = lambda nm: features.rasterize([(unary_union([shape(f_["geometry"]) for f_ in json.loads((T.utm_dir(CFG.BULK_ROOT) / f"{nm}.geojson").read_text())["features"]]), 1)],
                                        out_shape=g.shape, transform=tr, fill=0, dtype="uint8").astype(bool)[Wn]
    dry = Dw & ~Bw & ~ras(T.REF)
    cell_of = (np.arange(nR * F)[:, None] // F) * nC + (np.arange(nC * F)[None, :] // F)            # 20 m -> 200 m cell index
    bowl20 = bowl[cell_of]; ys20 = y1w - g.cell * (np.arange(nR * F) + 0.5); xs20 = x0w + g.cell * (np.arange(nC * F) + 0.5)

    def wet20(eta_run, run):
        sh = np.where(bowl20, prm["dz"][run], prm["drim"][run])
        return (dem + sh < eta_run[cell_of]) & act[cell_of]
    rows = []; ca = g.cell ** 2 / 1e6
    eo_info = {}
    for k, (dday, sensor, wl, al, cl) in T.EO.items():
        if k not in OBS_TIMES:
            continue
        ob = ras(al) & dry
        if cl:
            ob &= ~ras(cl)
        eo = ras(wl) & ob; nom = O.compose_npz(M, SFX, dday)[Wn] & ob; mem = O.compose_npz(M, "_connected_ceiling_memory", dday)[Wn] & ob
        cen = lambda m: (float(xs20[np.nonzero(m)[1]].mean()), float(ys20[np.nonzero(m)[0]].mean())) if m.any() else (np.nan, np.nan)
        csi = lambda mm: float((mm & eo).sum() / max((mm | eo).sum(), 1))
        eo_info[k] = dict(date=dday, sensor=sensor, observed_dry_km2=round(ob.sum() * ca, 2), A_EO_km2=round(eo.sum() * ca, 2), eo_centroid=cen(eo),
                          A_primary_km2=round(nom.sum() * ca, 2), CSI_primary=round(csi(nom), 3), A_memory_km2=round(mem.sum() * ca, 2), CSI_memory=round(csi(mem), 3))
        for run in range(N):
            wm = wet20(snaps[k][run], run) & ob; cx, cy = cen(wm)
            rows.append(dict(run=int(run_ids[run]), eo=k, A_model_km2=round(wm.sum() * ca, 3), CSI=round(csi(wm), 3), centroid_E_km=round(cx / 1e3, 2) if np.isfinite(cx) else np.nan,
                             centroid_N_km=round(cy / 1e3, 2) if np.isfinite(cy) else np.nan,
                             dist_from_sill_km=round(np.hypot(cx - SILL_XY[0], cy - SILL_XY[1]) / 1e3, 2) if np.isfinite(cx) else np.nan))
    R = pd.DataFrame(rows); PR = pd.DataFrame({k_: v for k_, v in prm.items()}); PR["ET"] *= 86400e3; PR["k"] *= 86400e3; PR.insert(0, "run", run_ids)
    R = R.merge(PR, on="run")
    ok = np.ones(N, bool)
    for k in OBS_TIMES:
        ae = eo_info[k]["A_EO_km2"]; am_ = R[R.eo == k].set_index("run").loc[run_ids].A_model_km2.to_numpy()
        ok &= (am_ <= 0.5) if ae < 0.25 else (np.abs(np.log(np.maximum(am_, 1e-3) / ae)) <= np.log(2.0))
    R["consistent_all_dates"] = R.run.map(dict(zip(run_ids, ok)))
    R["cell_m"] = a.cell_m; R.to_csv(TAB / f"p95w_cells_runs_{tag}.csv", index=False)
    srows = []
    for k, inf in eo_info.items():
        sub_ = R[R.eo == k]; q = np.nanpercentile(sub_.A_model_km2, [5, 25, 50, 75, 95]); qc = np.nanpercentile(sub_.CSI, [5, 50, 95])
        ex, ey = inf["eo_centroid"]
        srows.append(dict(eo=k, date=inf["date"], sensor=inf["sensor"], observed_dry_km2=inf["observed_dry_km2"], A_EO_km2=inf["A_EO_km2"],
                          A_primary_km2=inf["A_primary_km2"], CSI_primary=inf["CSI_primary"], A_memory_km2=inf["A_memory_km2"], CSI_memory=inf["CSI_memory"],
                          A_p05=round(q[0], 2), A_p25=round(q[1], 2), A_p50=round(q[2], 2), A_p75=round(q[3], 2), A_p95=round(q[4], 2),
                          CSI_p05=round(qc[0], 3), CSI_p50=round(qc[1], 3), CSI_p95=round(qc[2], 3),
                          EO_dist_from_sill_km=round(np.hypot(ex - SILL_XY[0], ey - SILL_XY[1]) / 1e3, 2) if np.isfinite(ex) else np.nan,
                          model_dist_from_sill_km_p50=round(float(np.nanmedian(sub_.dist_from_sill_km)), 2),
                          share_runs_consistent_all_dates=round(float(ok.mean()), 3)))
    SUM = pd.DataFrame(srows); SUM["cell_m"] = a.cell_m; SUM.to_csv(TAB / f"p95w_cells_summary_{tag}.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30)
    print(SUM.drop(columns=["sensor"]).to_string(index=False))
    good = PR[ok]
    print(f"\nruns consistent with all four dates: {ok.sum()} of {N}" + (f"; their medians: n {good.n.median():.3f}, dz {good.dz.median():.2f} m, drim {good.drim.median():.2f} m, "
          f"ET {good.ET.median():.1f} mm/d, k {good.k.median():.1f} mm/d" if len(good) else ""))
    # ---- figure ----------------------------------------------------------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    fig = plt.figure(figsize=(17, 9.4), constrained_layout=True); gs = fig.add_gridspec(2, 4)
    ax = fig.add_subplot(gs[0, :2])
    dsorted = sorted(day_snaps); A_day = np.array([[(wet20(day_snaps[dd][run], run) & Dw & ~Bw).sum() * ca for dd in dsorted] for run in range(N)])
    tday = pd.to_datetime(dsorted) + pd.Timedelta(hours=12); qd = np.percentile(A_day, [5, 50, 95], axis=0)
    ax.fill_between(tday, qd[0], qd[2], color="#2a78d6", alpha=0.2); ax.plot(tday, qd[1], color="#2a78d6", lw=1.6, label="storage cells v2: new water in the depression (median, 5-95 %)")
    if ok.any():
        ax.plot(tday, A_day[ok].T, color="#1baf7a", lw=0.8, alpha=0.8)
        ax.plot([], [], color="#1baf7a", lw=0.8, label=f"runs consistent with all four dates ({ok.sum()})")
    nomA = [(O.compose_npz(M, SFX, dd)[Wn] & Dw & ~Bw).sum() * ca for dd in dsorted]; memA = [(O.compose_npz(M, "_connected_ceiling_memory", dd)[Wn] & Dw & ~Bw).sum() * ca for dd in dsorted]
    ax.plot(tday, nomA, "s-", color="#16324f", ms=3, lw=1.1, label="primary (daily)"); ax.plot(tday, memA, "^--", color="#7f7f7f", ms=3, lw=1.1, label="memory (daily)")
    ax.set_ylabel("new water on the dry-before ground of the depression, km2", fontsize=7); ax.grid(alpha=0.3); ax.legend(fontsize=6.5); ax.tick_params(labelsize=7)
    ax.set_title("areas over time (whole depression)", fontsize=8)
    ax = fig.add_subplot(gs[0, 2:])
    for j, k in enumerate(OBS_TIMES):
        inf = eo_info[k]; v = R[R.eo == k].A_model_km2
        ax.boxplot([v], positions=[j], widths=0.3, whis=(5, 95), showfliers=False, patch_artist=True, boxprops=dict(facecolor="#2a78d6", alpha=0.5), medianprops=dict(color="k"))
        ax.plot(j, inf["A_EO_km2"], "o", color="k", ms=8, label="observed (UNOSAT)" if j == 0 else None)
        ax.plot(j - 0.3, inf["A_primary_km2"], "s", color="#16324f", label="primary" if j == 0 else None); ax.plot(j + 0.3, inf["A_memory_km2"], "^", color="#7f7f7f", label="memory" if j == 0 else None)
    ax.set_xticks(range(len(OBS_TIMES))); ax.set_xticklabels([f"{OBS_TIMES[k][5:10]} {k[3:]}" for k in OBS_TIMES], fontsize=7); ax.set_yscale("symlog", linthresh=0.5)
    ax.set_ylabel("new water, observed dry-before ground, km2", fontsize=7); ax.grid(alpha=0.3); ax.legend(fontsize=6.5); ax.set_title("hold-out at the acquisition times", fontsize=8)
    ext = (x0w / 1e3, (x0w + dxc * nC) / 1e3, (y1w - dxc * nR) / 1e3, y1w / 1e3)
    freq = {k: np.mean([wet20(snaps[k][run], run) for run in range(N)], axis=0) for k in ("09_L9", "13_S2")}
    for j, k in enumerate(("09_L9", "13_S2")):
        ax = fig.add_subplot(gs[1, 2 * j:2 * j + 2]); dday, sensor, wl, al, cl = T.EO[k]
        ob = ras(al) & dry
        if cl:
            ob &= ~ras(cl)
        eo = ras(wl) & ob
        ax.imshow(np.where(Dw, 1, np.nan), extent=ext, cmap=ListedColormap(["#eeeeee"]), interpolation="nearest")
        im = ax.imshow(np.where(freq[k] > 0.02, freq[k], np.nan), extent=ext, cmap="Blues", vmin=0, vmax=1, interpolation="nearest")
        ax.contour(eo.astype("f4"), levels=[0.5], colors=["#e0249a"], linewidths=0.6, extent=ext, origin="upper")
        ax.plot(SILL_XY[0] / 1e3, SILL_XY[1] / 1e3, "v", color="#e34948", ms=8, label="sill (entry)")
        ax.set_title(f"{OBS_TIMES[k][:10]}: share of runs wet (blue) vs observed water (magenta outline), depression grey", fontsize=7.5)
        ax.tick_params(labelsize=6); plt.colorbar(im, ax=ax, shrink=0.7, label="share of runs wet").ax.tick_params(labelsize=6); ax.legend(fontsize=6, loc="lower left")
    fig.suptitle(f"DEPRESSION_STORAGE v2: {dxc:.0f} m storage cells with sub-grid terrain, local inertial fluxes, river surface on the floodplain boundary; "
                 f"{N} prior runs, nothing fitted; UNOSAT 7/9/13/21 June = hold-out", fontsize=8)
    FIG.mkdir(parents=True, exist_ok=True); fig.savefig(FIG / f"p95w_storage_cells_{tag}.png", dpi=150); plt.close(fig)
    (TAB / f"p95w_manifest_{tag}.json").write_text(json.dumps(dict(run_ids=[int(r) for r in run_ids], lhs_size=a.runs,
        producer="p95w_storage_cells.py", version="v2 (distributed storage cells, prior-predictive)", runs=N, seed=a.seed, cell_m=dxc, sub_cell_m=g.cell,
        domain_cells=[int(nR), int(nC)], prognostic_cells=int(act.sum()), boundary_cells=int(bc.sum()), faces=int(nF), steps=nsteps, window=[T0, T1], obs_times=OBS_TIMES,
        priors=dict(n="logU(0.03, 0.15)", bowl_offset="U(-1.2, 0) m", rim_offset="U(-0.1, 0.1) m", ET_mm_d="U(3, 7)", k_mm_d="logU(1, 100)"), sampling="Latin hypercube",
        device=a.device, scheme="local inertial (Bates et al. 2010) on sub-grid storage cells; outflow limited to cell volume; dt = 0.7 dx / sqrt(g d_max) <= 300 s",
        boundary=f"cells outside the depression with median terrain < {BC_MEDIAN} m carry the reconstruction's surface (daily at 12:00 UTC, linear)",
        consistency="within a factor 2 of the observed area on 7, 9, 13 and 21 June (<= 0.5 km2 where observed < 0.25) -- a check, not a fit",
        not_modelled="rain; groundwater; culverts / drainage structures; sub-daily river surface; vegetation-specific roughness"), indent=1))
    print("->", TAB / f"p95w_cells_summary_{tag}.csv", round(time.time() - t_start), "s")


if __name__ == "__main__":
    main()
