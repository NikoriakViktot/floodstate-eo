# Provenance: SWOT-DNIPRO scripts/p78_null_pseudo_event.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: ACTIVE_DIAGNOSTIC -- null pseudo-event calibration of p71 channels and the MAD floor.
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P78 -- what "flood" does p71 manufacture from ordinary temporal and speckle variability?

THE NULL EXPERIMENT, and it needs no flood labels. Every pre-breach scene is promoted in turn to a pseudo-event
and pushed through p71's exact arithmetic against a baseline built from the REMAINING scenes of its own orbit:

    B_-j = median(S_o minus j)      MAD_-j = max(median|S_o minus j - B_-j|, 0.1)  d_j = S_j - B_-j
    z_j  = d_j / MAD_-j

No flood happened between those acquisitions, so whatever magnitude comes out is what the feature construction
produces from nothing. That is a far stronger statement than an ENL: it is measured in the units the network
actually sees, stratified by the surface that matters.

WHY THE ORDER STATISTICS GET THEIR OWN TEST. p71 does not hand the network d_j. It hands it min_j(d_j) and
max_j(d_j) over the event scenes. For X_j = mu + eps_j with E[eps] = 0 the mean is unbiased but
E[min] < mu < E[max]: min and max SELECT the noise tails by construction, and the selection grows with the number
of scenes. Where the change signal dwarfs the noise (open water, wetland) this is irrelevant. Where signal and
noise are comparable (agriculture) it may dominate. So the null is evaluated three ways -- one scene, the min over
a matched draw, the max over a matched draw -- with the draw matched to the REAL event: exactly one scene per
relative orbit, aggregated across orbits, which is what p71 does at the peak.

EVERYTHING IS IN dB. The caches hold linear gamma0; p71 converts once on load (see its DB_FLOOR/to_db note) and
this file imports that same function rather than re-deriving it, so the null cannot silently diverge from the
product it is meant to describe.

Reported per pre-event surface: median/p90/p95/p99 |d|, median/p95 |z|, P(|z|>2), P(|z|>3), for the single-scene
operator and for the matched min and max draws -- plus the same statistics for the REAL event, whose ratio to the
null is the diagnostic the whole exercise exists to produce.

Outputs: outputs/tables/p78_null_pseudo_event.csv
         outputs/tables/p78_null_vs_event_ratio.csv
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
import numpy as np, pandas as pd, rasterio, warnings
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

from floodstate_eo.sar.p71_s1_event_change import to_db                      # noqa: E402  -- one definition, not two

OUT = CFG.BULK_ROOT / "frames10"
LONG = {"B2": "ZONE_2_KHERSON_DELTA"}
JUNE = {"B2": "ZONE_2_KHERSON_DELTA_flood_june2023"}
BREACH = "2023-06-06"; PEAK_LO, PEAK_HI = "2023-06-06", "2023-06-14"
MAD_FLOOR = 0.1
#: THE FLOOR IS CALIBRATED ON THE PRE-ONLY NULL, NEVER ON FLOOD LABELS. 0.1 was inherited from a dB-era constant
#: and survived into the linear implementation, where it bound 98.97 % of pixels. In dB it binds ~none, but "it no
#: longer breaks things" is not evidence that it is right: a pixel whose pre-event series is genuinely stable
#: (MAD 0.03 dB) still gets z = 5 from a 0.5 dB observation-level wobble if the floor is 0.1. So the tail rates are
#: reported for a small fixed set of candidate floors on data containing no flood, and the choice is made from the
#: empirical null rather than from any downstream metric.
FLOORS = (0.1, 0.25, 0.5)
BCn = {0: "PRE_WATER", 1: "VEG_AGRI", 2: "BARE_SAND", 3: "BUILT_UP", 4: "WETLAND", 5: "OTHER_DRY"}
#: streamed histograms rather than retained samples: 28.9 M cells x 79 scenes will not be held in memory, and a
#: subsample would invite the question of whether the tail survived it.
EDG_D = np.linspace(0, 25, 501); EDG_Z = np.linspace(0, 25, 501)
NDRAW = 40


def orbit(p):
    m = re.search(r"_orb(\d+)_(ASC|DES)", p.name)
    return f"{m.group(1)}_{m.group(2)}"


def scenes(cache, lo=None, hi=None, pre=False):
    out = []
    for p in sorted((CFG.S1_CACHE / cache).glob("*.npz")):
        if p.name == "per_scene_water.npz":
            continue
        dt = p.name[:10]
        if pre and dt >= BREACH:
            continue
        if lo and not (lo <= dt <= hi):
            continue
        out.append(p)
    return out


def pct_from_hist(h, edges, q):
    c = np.cumsum(h)
    if c[-1] == 0:
        return np.nan
    return float(np.interp(q / 100.0 * c[-1], c, edges[1:]))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frame", default="B2")
    ap.add_argument("--band", default="vv"); ap.add_argument("--rows", type=int, default=256)
    a = ap.parse_args(); fid = a.frame
    F = CG.frame_grid(fid)
    w = np.load(CFG.S1_CACHE / JUNE[fid] / "per_scene_water.npz", allow_pickle=True)
    shp = tuple(int(v) for v in w["shape"]); cell = float(w["cell"])
    ztr = from_origin(float(w["x0"]), float(w["y1"]), cell, cell)
    ev = scenes(JUNE[fid], PEAK_LO, PEAK_HI); pre = scenes(LONG[fid], pre=True)
    need = sorted({orbit(p) for p in ev})
    by_orb = {o: [p for p in pre if orbit(p) == o] for o in need}
    print(f"{fid}: {len(ev)} event scenes on {len(need)} orbits; pseudo-events from "
          + ", ".join(f"{o} n={len(by_orb[o])}" for o in need), flush=True)
    for o in need:
        if len(by_orb[o]) < 6:
            raise SystemExit(f"orbit {o}: {len(by_orb[o])} pre scenes -- leave-one-out needs a baseline of >=5")

    def down(path, band=1):
        with rasterio.open(path) as s:
            arr = s.read(band)
        o = np.zeros(shp, arr.dtype)
        reproject(source=arr, destination=o, src_transform=F["transform"], src_crs=CFG.CRS_METRIC,
                  dst_transform=ztr, dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest)
        return o
    bc = down(OUT / fid / "p69a_base_class.tif")

    OPS = ["single", "min", "max"]
    H = {(k, op, v): np.zeros(len(EDG_D) - 1) for k in BCn for op in OPS for v in ("d", "z")}
    N = {(k, op): np.zeros(3) for k in BCn for op in OPS}          # n_valid, n |z|>2, n |z|>3
    HE = {(k, op, v): np.zeros(len(EDG_D) - 1) for k in BCn for op in ("min", "max") for v in ("d", "z")}
    NE = {(k, op): np.zeros(3) for k in BCn for op in ("min", "max")}
    FL = {(k, f): np.zeros(4) for k in BCn for f in FLOORS}     # n, |z|>2, |z|>3, n bound by the floor
    rng = np.random.default_rng(20260923)

    for r0 in range(0, shp[0], a.rows):
        r1 = min(r0 + a.rows, shp[0]); h = r1 - r0
        bcb = bc[r0:r1]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            D = {}; Z = {}
            for o in need:
                P = np.full((len(by_orb[o]), h, shp[1]), np.nan, "f4")
                for i, p in enumerate(by_orb[o]):
                    z = np.load(p); v = z[a.band][r0:r1].astype("f4"); v[~z["cov"][r0:r1]] = np.nan
                    P[i] = to_db(v)
                dl = []; zl = []
                for j in range(len(P)):
                    k = np.delete(np.arange(len(P)), j)
                    m_ = np.nanmedian(P[k], 0)
                    raw = np.nanmedian(np.abs(P[k] - m_), 0)
                    md = np.maximum(raw, MAD_FLOOR)
                    d = P[j] - m_
                    dl.append(d); zl.append(d / md)
                    for f in FLOORS:                       # floor sweep, pre-only, no labels involved
                        zf = np.abs(d / np.maximum(raw, f))
                        for kk in BCn:
                            mm = (bcb == kk) & np.isfinite(zf)
                            if not mm.any():
                                continue
                            v = zf[mm]
                            FL[(kk, f)] += (mm.sum(), (v > 2).sum(), (v > 3).sum(),
                                            (raw[mm] < f).sum() if np.isfinite(raw[mm]).all() else
                                            np.nansum(raw[mm] < f))
                D[o] = np.stack(dl); Z[o] = np.stack(zl)
                del P, dl, zl
            # ---- the REAL event, same arithmetic, for the ratio ------------------------------------------------
            ed = []; ez = []
            for p in ev:
                o = orbit(p)
                Pb = np.full((len(by_orb[o]), h, shp[1]), np.nan, "f4")
                for i, q in enumerate(by_orb[o]):
                    z = np.load(q); v = z[a.band][r0:r1].astype("f4"); v[~z["cov"][r0:r1]] = np.nan
                    Pb[i] = to_db(v)
                m_ = np.nanmedian(Pb, 0)
                md = np.maximum(np.nanmedian(np.abs(Pb - m_), 0), MAD_FLOOR)
                z = np.load(p); v = z[a.band][r0:r1].astype("f4"); v[~z["cov"][r0:r1]] = np.nan
                d = to_db(v) - m_
                ed.append(d); ez.append(d / md)
                del Pb
            ed = np.stack(ed); ez = np.stack(ez)

            def add(store, cnt, key, dv, zv):
                for k in BCn:
                    m = (bcb == k) & np.isfinite(dv) & np.isfinite(zv)
                    if not m.any():
                        continue
                    store[(k,) + key + ("d",)] += np.histogram(np.abs(dv[m]), EDG_D)[0]
                    store[(k,) + key + ("z",)] += np.histogram(np.abs(zv[m]), EDG_Z)[0]
                    az = np.abs(zv[m])
                    cnt[(k,) + key] += (m.sum(), (az > 2).sum(), (az > 3).sum())

            for o in need:                                         # single-scene null, every pseudo-event
                for j in range(D[o].shape[0]):
                    add(H, N, ("single",), D[o][j], Z[o][j])
            for _ in range(NDRAW):                                 # matched draw: one scene per orbit
                dd = np.stack([D[o][rng.integers(D[o].shape[0])] for o in need])
                zz = np.stack([Z[o][rng.integers(Z[o].shape[0])] for o in need])
                add(H, N, ("min",), np.nanmin(dd, 0), np.nanmin(zz, 0))
                add(H, N, ("max",), np.nanmax(dd, 0), np.nanmax(zz, 0))
            add(HE, NE, ("min",), np.nanmin(ed, 0), np.nanmin(ez, 0))
            add(HE, NE, ("max",), np.nanmax(ed, 0), np.nanmax(ez, 0))
            del D, Z, ed, ez
        print(f"  rows {r0}-{r1}", flush=True)

    rows = []
    for k, nm in BCn.items():
        for op in OPS:
            n, n2, n3 = N[(k, op)]
            if n < 10000:
                continue
            rows.append(dict(stratum=nm, source="NULL_pseudo_event", operator=op, n_px=int(n),
                             d_med=round(pct_from_hist(H[(k, op, "d")], EDG_D, 50), 3),
                             d_p90=round(pct_from_hist(H[(k, op, "d")], EDG_D, 90), 3),
                             d_p95=round(pct_from_hist(H[(k, op, "d")], EDG_D, 95), 3),
                             d_p99=round(pct_from_hist(H[(k, op, "d")], EDG_D, 99), 3),
                             z_med=round(pct_from_hist(H[(k, op, "z")], EDG_Z, 50), 3),
                             z_p95=round(pct_from_hist(H[(k, op, "z")], EDG_Z, 95), 3),
                             frac_z_gt2=round(float(n2 / n), 5), frac_z_gt3=round(float(n3 / n), 5)))
        for op in ("min", "max"):
            n, n2, n3 = NE[(k, op)]
            if n < 10000:
                continue
            rows.append(dict(stratum=nm, source="REAL_event", operator=op, n_px=int(n),
                             d_med=round(pct_from_hist(HE[(k, op, "d")], EDG_D, 50), 3),
                             d_p90=round(pct_from_hist(HE[(k, op, "d")], EDG_D, 90), 3),
                             d_p95=round(pct_from_hist(HE[(k, op, "d")], EDG_D, 95), 3),
                             d_p99=round(pct_from_hist(HE[(k, op, "d")], EDG_D, 99), 3),
                             z_med=round(pct_from_hist(HE[(k, op, "z")], EDG_Z, 50), 3),
                             z_p95=round(pct_from_hist(HE[(k, op, "z")], EDG_Z, 95), 3),
                             frac_z_gt2=round(float(n2 / n), 5), frac_z_gt3=round(float(n3 / n), 5)))
    T = pd.DataFrame(rows)
    T.to_csv(CFG.TABLES / "p78_null_pseudo_event.csv", index=False)

    # the diagnostic ratio: real anomaly magnitude over what the construction makes from nothing
    R = []
    for k, nm in BCn.items():
        for op in ("min", "max"):
            a_ = T[(T.stratum == nm) & (T.source == "REAL_event") & (T.operator == op)]
            b_ = T[(T.stratum == nm) & (T.source == "NULL_pseudo_event") & (T.operator == op)]
            s_ = T[(T.stratum == nm) & (T.source == "NULL_pseudo_event") & (T.operator == "single")]
            if not len(a_) or not len(b_):
                continue
            R.append(dict(stratum=nm, operator=op,
                          event_d_med=a_.d_med.iloc[0], null_d_med=b_.d_med.iloc[0],
                          ratio_d_med=round(a_.d_med.iloc[0] / max(b_.d_med.iloc[0], 1e-9), 3),
                          event_z_p95=a_.z_p95.iloc[0], null_z_p95=b_.z_p95.iloc[0],
                          ratio_z_p95=round(a_.z_p95.iloc[0] / max(b_.z_p95.iloc[0], 1e-9), 3),
                          null_single_d_p95=s_.d_p95.iloc[0] if len(s_) else np.nan,
                          null_order_stat_inflation=round(
                              b_.d_p95.iloc[0] / max(s_.d_p95.iloc[0], 1e-9), 3) if len(s_) else np.nan))
    pd.DataFrame(R).to_csv(CFG.TABLES / "p78_null_vs_event_ratio.csv", index=False)
    Q = []
    for k, nm in BCn.items():
        for f in FLOORS:
            n, n2, n3, nb = FL[(k, f)]
            if n < 10000:
                continue
            Q.append(dict(stratum=nm, mad_floor_db=f, n_px=int(n),
                          frac_bound_by_floor=round(float(nb / n), 5),
                          null_frac_z_gt2=round(float(n2 / n), 5), null_frac_z_gt3=round(float(n3 / n), 5)))
    QD = pd.DataFrame(Q); QD.to_csv(CFG.TABLES / "p78_mad_floor_null_calibration.csv", index=False)
    print("\nMAD floor calibration on the PRE-ONLY null (no flood labels used):")
    print(QD.to_string(index=False))
    print("\n" + T.to_string(index=False))
    print("\n" + pd.DataFrame(R).to_string(index=False))
    print("\n-> outputs/tables/p78_null_pseudo_event.csv, p78_null_vs_event_ratio.csv")


if __name__ == "__main__":
    main()
