# New in floodstate-eo, 2026-10-01 (maintainer: "a random-forest classification for every downloaded date, the reservoir included,
# 2024 and 2025 as well -- full coverage for the hydraulic model"). STATUS: ACTIVE. A product for the hydraulic-model work
# (Papers 4-5); no Paper 3 result rests on it.
"""P102 -- RF surface classes BY DATE: a random forest on the seven spectral indices of each Sentinel-2 date (the frozen p25 zone
stacks, 20 m) for every date of every zone -- the Kakhovka pool and lower Dnipro (ZONE_1), the Kherson delta (ZONE_2), the
Dnipro-Bug estuary (ZONE_3) and the floodway dam -> Kherson (ZONE_4), 2017 .. 2026.

WHAT IT IS. The per-date counterpart of RF20 (p73): the same nine land-cover classes with ESA WorldCover 2021 as the weak target,
but the predictors are the indices of ONE date (NDVI, NDWI, MNDWI, NDMI, BSI, AWEIsh, NDTI; optionally the day of year as
sin / cos), so that every observed date gets a class map -- including the drained reservoir bed of 2024-2026, which no
pre-event composite covers. The classes are land-cover classes (a bare field in winter is still CROPLAND); the per-date physical
surface state (bare, sparse, dense, reed, water) is the k10e rule map of the same stack, and the two are meant to be read together.

TARGET. WorldCover 2021 on the zone grid (the same 20 m lattice as the p25 stacks, asserted); a cell is a target only where its
3 x 3 WorldCover neighbourhood agrees (purity), and on a date only where the spectral evidence does not contradict the class
(WATER needs MNDWI > 0; the non-water classes need MNDWI < 0.3). Training dates: 2021-01-01 .. 2023-06-05 -- the reference year
of WorldCover and the pre-breach period; every earlier or later date is prediction only. Up to PER_CLASS_DATE cells per class,
zone and date; a cell may enter on several dates (its spectra differ), never twice on one date.

EVALUATION, fixed before the run. (i) 5-fold spatial-block CV on 5 km global UTM blocks over the training sample (a cell lies in
one block on every date, so no block leaks across folds); (ii) temporal hold-out: fit on 2021-2022, test on the 2023 pre-breach
dates. Both for both variants (spectral; spectral + day of year). The production model is the variant with the higher
temporal-hold-out macro F1, ties to the simpler one (spectral). Agreement with WorldCover is agreement with a weak reference
(~75 % global accuracy), never accuracy. UNCERTAIN (10) where the top-class probability is below 0.5, as in p73.

Outputs: $BULK/rf_by_date/<ZONE>/<date>_rf.tif (uint8 class 1..10, 0 = not observed), <date>_rfp.tif (top-class probability
x 100, 255 = not observed), <date>_rf.json (areas); $BULK/frames10/_m6/p102_rf_date_model.joblib;
<case_study>/tables/p102_rf_date_{inventory,metrics,class_area}.csv, p102_rf_date_confusion_<variant>.csv,
p102_rf_date_manifest.json; figures/p102/<ZONE>_rf_by_date.png and <ZONE>_rf_class_series.png.
Resumable: a date whose sidecar JSON exists is skipped unless --force. Steps: train, predict, tables, figures (default: all).
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio, rasterio.windows
from rasterio import features
from floodstate_eo import _kakhovka_legacy_config as CFG

ZONES = ["ZONE_1_KAKHOVKA_LOWER_DNIPRO", "ZONE_2_KHERSON_DELTA", "ZONE_3_DNIPRO_BUG_ESTUARY", "ZONE_4_DAM_TO_KHERSON_FLOODWAY"]
SHORT = {"ZONE_1_KAKHOVKA_LOWER_DNIPRO": "pool + lower Dnipro", "ZONE_2_KHERSON_DELTA": "Kherson delta",
         "ZONE_3_DNIPRO_BUG_ESTUARY": "Dnipro-Bug estuary", "ZONE_4_DAM_TO_KHERSON_FLOODWAY": "floodway dam -> Kherson"}
SPEC = CFG.BULK_ROOT / "zone_spectral"; WC = CFG.BULK_ROOT / "worldcover_frames"; OUT = CFG.BULK_ROOT / "rf_by_date"
MODEL = CFG.BULK_ROOT / "frames10" / "_m6" / "p102_rf_date_model.joblib"; FIG = CFG.FIG / "p102"
INDEX_NAMES = ("NDVI", "NDWI", "MNDWI", "NDMI", "BSI", "AWEIsh", "NDTI"); NODATA = -32768; CELL_KM2 = 0.0004
CLASSES = {1: "WATER", 2: "CROPLAND", 3: "GRASS_LOW_VEGETATION", 4: "FOREST", 5: "SHRUB", 6: "WETLAND_REED", 7: "BUILT_UP",
           8: "BARE_SAND", 9: "OTHER", 10: "UNCERTAIN"}
COLORS = {1: "#1b6ca8", 2: "#f2c14e", 3: "#b8d98d", 4: "#1e6f3f", 5: "#8c9a3a", 6: "#2a9d8f", 7: "#7d7d7d", 8: "#d9c58b", 9: "#c7522a", 10: "#e8e4d8"}
WC2P = {80: 1, 40: 2, 30: 3, 10: 4, 20: 5, 90: 6, 50: 7, 60: 8, 70: 9, 95: 9, 100: 9}       # as p73 (WorldCover code -> class)
TRAIN_START, TRAIN_END, HOLDOUT_FROM = "2021-01-01", "2023-06-05", "2023-01-01"
PER_CLASS_DATE = 1500; BLOCK_M = 5000.0; SEED = 20261001; UNCERTAIN_P = 0.5; STRIP = 512; CHUNK = 3_000_000
VARIANTS = ("spectral", "spectral+doy")
RF = dict(n_estimators=60, min_samples_leaf=20, max_features="sqrt", class_weight="balanced_subsample", max_samples=0.5)


def dates_of(z):
    return sorted(p.name[:10] for p in (SPEC / z).glob("*_class.tif"))


def doy(d):
    ang = 2.0 * np.pi * (pd.Timestamp(d).dayofyear - 1) / 365.25
    return float(np.sin(ang)), float(np.cos(ang))


def worldcover_target(z):
    """WorldCover 2021 -> class code where the 3 x 3 neighbourhood agrees; 0 elsewhere. Asserts the p25 lattice."""
    with rasterio.open(WC / z / "wc_2021_20m.tif") as s:
        wc = s.read(1); tr = s.transform
    with rasterio.open(SPEC / z / f"{dates_of(z)[0]}_indices.tif") as s:
        assert s.transform == tr and s.shape == wc.shape, f"{z}: WorldCover and the p25 stacks are not on one grid"
    pure = wc > 0
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di or dj:
                pure &= np.roll(np.roll(wc, di, 0), dj, 1) == wc
    pure[[0, -1], :] = False; pure[:, [0, -1]] = False
    y = np.zeros(wc.shape, np.uint8)
    for wv, pc in WC2P.items():
        y[pure & (wc == wv)] = pc
    return y, tr


def sample_date(z, d, y, tr, rng):
    """Up to PER_CLASS_DATE target cells per class on one date: features (n, 7), class, cell-centre x / y (UTM)."""
    with rasterio.open(SPEC / z / f"{d}_class.tif") as s:
        cand = (s.read(1) != 0) & (y > 0)
    if not cand.any():
        return None
    with rasterio.open(SPEC / z / f"{d}_indices.tif") as s:
        X = s.read()
    cand &= np.all(X != NODATA, axis=0); mndwi = X[2]
    cand &= ~((y == 1) & ~(mndwi > 0)); cand &= ~(np.isin(y, (2, 3, 4, 5, 7, 8)) & ~(mndwi < 3000))
    cf, yf = cand.ravel(), y.ravel(); idx = []
    for c in range(1, 10):
        w = np.flatnonzero(cf & (yf == c))
        if len(w):
            idx.append(rng.choice(w, size=min(PER_CLASS_DATE, len(w)), replace=False))
    if not idx:
        return None
    idx = np.concatenate(idx); rows, cols = np.divmod(idx, y.shape[1])
    return (X.reshape(len(INDEX_NAMES), -1)[:, idx].T.astype("f4") / 1e4, yf[idx].astype("u1"),
            tr.c + 20.0 * (cols + 0.5), tr.f - 20.0 * (rows + 0.5))


def rf(jobs):
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(n_jobs=jobs, random_state=SEED, **RF)


def metric_rows(ys, pred, labels, **tag):
    from sklearn.metrics import precision_recall_fscore_support
    P, R, F1, N = precision_recall_fscore_support(ys, pred, labels=labels, zero_division=0)
    rows = [dict(**tag, cls=CLASSES[c], precision=round(float(p_), 4), recall=round(float(r_), 4), F1=round(float(f_), 4), n=int(n_))
            for c, p_, r_, f_, n_ in zip(labels, P, R, F1, N)]
    rows.append(dict(**tag, cls="MACRO", precision=round(float(P.mean()), 4), recall=round(float(R.mean()), 4), F1=round(float(F1.mean()), 4), n=int(N.sum())))
    rows.append(dict(**tag, cls="OVERALL_ACCURACY", F1=round(float((pred == ys).mean()), 4), n=int(N.sum())))
    return rows


def build_sample():
    """The training sample of the run, deterministic (SEED): the same cells, folds and hold-out split for `train` and `evaluate`."""
    t0 = time.time(); rng = np.random.default_rng(SEED); parts = []; inv = []
    for z in ZONES:
        y, tr = worldcover_target(z)
        for d in dates_of(z):
            if not (TRAIN_START <= d <= TRAIN_END):
                continue
            r = sample_date(z, d, y, tr, rng)
            if r is None:
                inv.append(dict(zone=z, date=d, n=0)); continue
            X7, yy, xc, yc = r; s_, c_ = doy(d)
            parts.append(dict(X=X7, y=yy, xc=xc, yc=yc, zone=np.full(len(yy), ZONES.index(z), "u1"), year=np.full(len(yy), int(d[:4]), "i2"),
                              doy=np.column_stack([np.full(len(yy), s_, "f4"), np.full(len(yy), c_, "f4")])))
            inv.append(dict(zone=z, date=d, n=int(len(yy)), **{f"n_{CLASSES[c]}": int((yy == c).sum()) for c in range(1, 10)}))
    cat = lambda k: np.concatenate([p[k] for p in parts])
    X7, ys, xc, yc, zone, year, DOY = (cat(k) for k in ("X", "y", "xc", "yc", "zone", "year", "doy"))
    blk = np.floor(yc / BLOCK_M).astype("i8") * 100000 + np.floor(xc / BLOCK_M).astype("i8")
    ub = np.unique(blk); rng.shuffle(ub); fold = dict(zip(ub.tolist(), (np.arange(len(ub)) % 5).tolist())); fv = np.vectorize(fold.get)(blk)
    print(f"training sample {len(ys):,} cells, {len(ub)} blocks ({time.time() - t0:.0f} s)", flush=True)
    return dict(VAR={"spectral": X7, "spectral+doy": np.hstack([X7, DOY])}, ys=ys, zone=zone, year=year, fv=fv, n_blocks=len(ub),
                labels=[c for c in range(1, 10) if (ys == c).any()]), inv


def step_evaluate(a):
    """Confusion matrices and per-class scores of both evaluations, both variants, all zones and per zone (maintainer 2026-10-02: the matrix,
    not only macro F1). Re-runs the fixed evaluation on the deterministic sample; the production model is not refitted. Every number is
    agreement with the WorldCover-2021-derived weak reference: the 2023 hold-out (pre-breach dates) measures the temporal-transfer
    degradation relative to those labels, not an independently validated 2023 accuracy; post-breach dates have no reference at all."""
    from sklearn.metrics import confusion_matrix
    t0 = time.time(); S, _ = build_sample(); ys, zone, year, fv, labels = S["ys"], S["zone"], S["year"], S["fv"], S["labels"]
    tr_, te = year <= 2022, year >= 2023; met, conf = [], []

    def add(evaluation, var, yt, yp, zz):
        for zi, zn in [(None, "ALL")] + list(enumerate(ZONES)):
            m = np.ones(len(yt), bool) if zi is None else (zz == zi)
            if m.sum() < 100:
                continue
            lab = [c for c in labels if (yt[m] == c).any()]
            met.extend(metric_rows(yt[m], yp[m], lab, variant=var, evaluation=evaluation, zone=zn))
            C = confusion_matrix(yt[m], yp[m], labels=labels)
            conf.extend(dict(variant=var, evaluation=evaluation, zone=zn, reference=CLASSES[r], predicted=CLASSES[p], n=int(C[i, j]))
                        for i, r in enumerate(labels) for j, p in enumerate(labels))
    for var, X in S["VAR"].items():
        pred = np.zeros_like(ys)
        for k in range(5):
            m = rf(a.jobs).fit(X[fv != k], ys[fv != k]); pred[fv == k] = m.predict(X[fv == k])
        add("spatial_block_cv_5fold", var, ys, pred, zone)
        m = rf(a.jobs).fit(X[tr_], ys[tr_]); add("temporal_holdout_2023pre", var, ys[te], m.predict(X[te]), zone[te])
        print(f"  {var} evaluated ({time.time() - t0:.0f} s)", flush=True)
    M = pd.DataFrame(met); C = pd.DataFrame(conf)
    old = pd.read_csv(CFG.TABLES / "p102_rf_date_metrics.csv") if (CFG.TABLES / "p102_rf_date_metrics.csv").exists() else None
    if old is not None:                                                     # determinism check against the train run
        k = ["variant", "evaluation", "zone", "cls"]; j = old.merge(M, on=k, suffixes=("_train", "_eval"))
        print(f"  reproduces the train-step metrics: max |dF1| = {float((j.F1_train - j.F1_eval).abs().max()):.2e} over {len(j)} rows", flush=True)
    M.to_csv(CFG.TABLES / "p102_rf_date_metrics.csv", index=False); C.to_csv(CFG.TABLES / "p102_rf_date_confusion_long.csv", index=False)
    figure_confusion(C, M)
    print(f"-> tables/p102_rf_date_{{metrics,confusion_long}}.csv, figures/p102/confusion_*.png ({time.time() - t0:.0f} s)", flush=True)


def figure_confusion(C, M):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG.mkdir(parents=True, exist_ok=True)
    prod = json.loads((CFG.TABLES / "p102_rf_date_manifest.json").read_text())["features"]["production"] if (CFG.TABLES / "p102_rf_date_manifest.json").exists() else "spectral+doy"
    for var in VARIANTS:
        fig, axs = plt.subplots(1, 2, figsize=(15, 6.6))
        for ax, ev, title in ((axs[0], "spatial_block_cv_5fold", "5-fold spatial-block CV (5 km blocks), 2021 – 5 June 2023"),
                              (axs[1], "temporal_holdout_2023pre", "temporal hold-out: fit 2021–2022, test 1 Jan – 5 June 2023")):
            c = C[(C.variant == var) & (C.evaluation == ev) & (C.zone == "ALL")]
            P = c.pivot_table(index="reference", columns="predicted", values="n", aggfunc="sum").reindex(index=[CLASSES[k] for k in range(1, 10)], columns=[CLASSES[k] for k in range(1, 10)]).dropna(how="all").dropna(axis=1, how="all").fillna(0)
            R = P.div(P.sum(axis=1).replace(0, np.nan), axis=0) * 100
            ax.imshow(R.values, cmap="Blues", vmin=0, vmax=100)
            for i in range(R.shape[0]):
                for j in range(R.shape[1]):
                    v = R.values[i, j]
                    if v >= 0.5:
                        ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7, color="white" if v > 55 else "black")
            f1 = M[(M.variant == var) & (M.evaluation == ev) & (M.zone == "ALL")].set_index("cls").F1
            ax.set_xticks(range(R.shape[1]), [s.replace("_", " ").lower()[:14] for s in R.columns], rotation=45, ha="right", fontsize=7)
            ax.set_yticks(range(R.shape[0]), [f"{s.replace('_', ' ').lower()[:14]} · F1 {f1.get(s, np.nan):.2f} · n {int(P.loc[s].sum()):,}" for s in R.index], fontsize=7)
            ax.set_xlabel("RF class"); ax.set_ylabel("WorldCover 2021 class (weak reference)")
            ax.set_title(f"{title}\nmacro F1 {f1.get('MACRO', np.nan):.3f} · row % (recall on the diagonal)", fontsize=8, loc="left")
        fig.suptitle(f"p102 RF by date, variant {var}{' (production)' if var == prod else ''}: agreement with the WorldCover-2021-derived weak reference, never accuracy", fontsize=9)
        fig.tight_layout(); fig.savefig(FIG / f"confusion_{var.replace('+', '_')}.png", dpi=120); plt.close(fig)


#: growing-season periods of the transition matrices (season-matched so that phenology does not pass for change); the 2023 period
#: starts on the breach day
PERIODS = [("2021 May–Sep (WorldCover yr)", "2021-05-01", "2021-09-30"), ("2022 May–Sep", "2022-05-01", "2022-09-30"),
           ("2023 6 Jun–Sep (after the breach)", "2023-06-06", "2023-09-30"), ("2024 May–Sep", "2024-05-01", "2024-09-30"),
           ("2025 May–Sep", "2025-05-01", "2025-09-30"), ("2026 May–Sep", "2026-05-01", "2026-09-30")]
MIN_OBS = 2


def step_transition(a):
    """Transition matrices of the reservoir: WorldCover 2021 class (rows; the pre-breach state) x the dominant RF class of each growing
    season (columns), km², inside the pre-breach pool and, as a control, in ZONE_1 outside it (where land cover changed little, so the
    off-diagonal mass there is the classifier's year-to-year noise). Dominant class = the per-cell mode over the observed dates of the
    period, a cell needs >= MIN_OBS observations. This is where the transformation of the drained bed shows (water -> bare -> vegetation);
    the confusion matrices against WorldCover cannot show it, because WorldCover 2021 describes the state before the breach."""
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t0 = time.time(); z = "ZONE_1_KAKHOVKA_LOWER_DNIPRO"; wc, tr = None, None
    with rasterio.open(WC / z / "wc_2021_20m.tif") as s:
        wc = s.read(1); tr = s.transform
    ref = np.zeros(wc.shape, "u1")
    for wv, pc in WC2P.items():
        ref[wc == wv] = pc
    pool = pool_mask(z, wc.shape, tr); inside_zone = ref > 0
    strata = {"POOL_PREBREACH": pool & inside_zone, "ZONE1_OUTSIDE_POOL": ~pool & inside_zone}
    rows, krows = [], []; rr, cc = np.nonzero(pool); r0, r1, c0, c1 = rr.min(), rr.max() + 1, cc.min(), cc.max() + 1; pw = pool[r0:r1, c0:c1]
    K10E = {1: "OPEN_WATER", 2: "SHALLOW_OR_MIXED_WATER", 3: "WET_SEDIMENT", 4: "DRY_BARE_SEDIMENT", 5: "SPARSE_HERBACEOUS", 6: "DENSE_HERBACEOUS",
            7: "REED_OR_FLOODED_VEGETATION", 8: "BUILT_HARD_SURFACE", 9: "AMBIGUOUS"}
    for name, lo, hi in PERIODS:
        ds = [d for d in dates_of(z) if lo <= d <= hi and (OUT / z / f"{d}_rf.tif").exists()]
        cnt = np.zeros((11,) + wc.shape, "u1")
        for d in ds:
            with rasterio.open(OUT / z / f"{d}_rf.tif") as s:
                c = s.read(1)
            for k in range(1, 11):
                cnt[k] += (c == k)
        nobs = cnt.sum(0); mode = cnt.argmax(0).astype("u1"); mode[nobs < MIN_OBS] = 0; del cnt
        # the physical surface state of the same dates inside the pool (k10e rule classes of the p25 stacks): what each RF class on the bed is
        kc = np.zeros((10, r1 - r0, c1 - c0), "u1")
        for d in ds:
            with rasterio.open(SPEC / z / f"{d}_class.tif") as s:
                k = s.read(1, window=rasterio.windows.Window(c0, r0, c1 - c0, r1 - r0))
            for j in range(1, 10):
                kc[j] += (k == j)
        kmode = kc.argmax(0).astype("u1"); kmode[kc.sum(0) < MIN_OBS] = 0; del kc
        rm = mode[r0:r1, c0:c1]; ok = pw & (rm > 0) & (kmode > 0)
        if ok.any():
            H = np.zeros((11, 10), "i8"); np.add.at(H, (rm[ok], kmode[ok]), 1)
            krows += [dict(period=name, n_dates=len(ds), rf_class=CLASSES[i], k10e_class=K10E[j], km2=round(float(H[i, j]) * CELL_KM2, 2))
                      for i in range(1, 11) for j in range(1, 10) if H[i, j]]
        for sn, sm in strata.items():
            for rc in range(1, 10):
                m = sm & (ref == rc)
                if not m.any():
                    continue
                h = np.bincount(mode[m], minlength=11); obs = int(h[1:].sum())
                for k in range(0, 11):
                    rows.append(dict(stratum=sn, period=name, n_dates=len(ds), reference=CLASSES[rc], rf_class=CLASSES.get(k, "NOT_OBSERVED") if k else "NOT_OBSERVED",
                                     km2=round(float(h[k]) * CELL_KM2, 2), share_of_observed=round(float(h[k]) / obs, 4) if (k and obs) else None))
        print(f"  {name}: {len(ds)} dates ({time.time() - t0:.0f} s)", flush=True)
    T = pd.DataFrame(rows); T.to_csv(CFG.TABLES / "p102_rf_date_transition.csv", index=False)
    KT = pd.DataFrame(krows); KT.to_csv(CFG.TABLES / "p102_rf_date_rf_vs_k10e_pool.csv", index=False)
    # figure: the pool's WorldCover-water row by season (km²), and the row-normalised matrices of the latest season, pool vs control
    FIG.mkdir(parents=True, exist_ok=True); fig, axs = plt.subplots(1, 3, figsize=(18, 5.6), gridspec_kw=dict(width_ratios=[1.3, 1, 1]))
    w = T[(T.stratum == "POOL_PREBREACH") & (T.reference == "WATER") & (T.rf_class != "NOT_OBSERVED")]
    per = [p[0] for p in PERIODS]; bottom = np.zeros(len(per))
    for k in range(1, 11):
        v = np.array([w[(w.period == p) & (w.rf_class == CLASSES[k])].km2.sum() for p in per])
        if v.sum() > 0:
            axs[0].bar(range(len(per)), v, bottom=bottom, color=COLORS[k], label=CLASSES[k].replace("_", " ").lower()); bottom += v
    nd = [int(T[(T.period == p)].n_dates.iloc[0]) if len(T[T.period == p]) else 0 for p in per]
    axs[0].set_xticks(range(len(per)), [f"{p.split(' (')[0]}\n{n} dates" for p, n in zip(per, nd)], fontsize=7); axs[0].set_ylabel("km² (observed cells)")
    axs[0].set_title("the pre-breach reservoir (WorldCover 2021 = water): dominant RF class of each growing season", fontsize=8, loc="left"); axs[0].legend(fontsize=7, frameon=False)
    last = next((p for p in reversed(per) if T[(T.period == p) & (T.rf_class != "NOT_OBSERVED")].km2.sum() > 0), per[-1])
    for ax, sn in ((axs[1], "POOL_PREBREACH"), (axs[2], "ZONE1_OUTSIDE_POOL")):
        q = T[(T.stratum == sn) & (T.period == last) & (T.rf_class != "NOT_OBSERVED")]
        P = q.pivot_table(index="reference", columns="rf_class", values="km2", aggfunc="sum").reindex(index=[CLASSES[k] for k in range(1, 10)], columns=[CLASSES[k] for k in range(1, 11)]).fillna(0)
        P = P[P.sum(axis=1) > 0.5]; R = P.div(P.sum(axis=1), axis=0) * 100
        ax.imshow(R.values, cmap="Greens", vmin=0, vmax=100)
        for i in range(R.shape[0]):
            for j in range(R.shape[1]):
                if R.values[i, j] >= 1:
                    ax.text(j, i, f"{R.values[i, j]:.0f}", ha="center", va="center", fontsize=7, color="white" if R.values[i, j] > 55 else "black")
        ax.set_xticks(range(R.shape[1]), [s.replace("_", " ").lower()[:12] for s in R.columns], rotation=45, ha="right", fontsize=7)
        ax.set_yticks(range(R.shape[0]), [f"{s.replace('_', ' ').lower()[:14]} · {P.loc[s].sum():,.0f} km²" for s in R.index], fontsize=7)
        ax.set_title(f"{'pool' if sn.startswith('POOL') else 'control: ZONE_1 outside the pool'}, {last}: row %", fontsize=8, loc="left")
        ax.set_xlabel("dominant RF class"); ax.set_ylabel("WorldCover 2021 class")
    fig.suptitle("p102: the drained Kakhovka bed season by season (WorldCover 2021 = the pre-breach state; a transition, not an error). Contains modified Copernicus Sentinel data.", fontsize=9)
    fig.tight_layout(); fig.savefig(FIG / "ZONE_1_pool_transition.png", dpi=120); plt.close(fig)
    if len(KT):
        sel = [p[0] for p in PERIODS if p[1] >= "2023-06-06" and KT[KT.period == p[0]].km2.sum() > 0]
        fig, axs = plt.subplots(1, len(sel), figsize=(6.2 * len(sel), 5.4), squeeze=False)
        for ax, per_ in zip(axs[0], sel):
            q = KT[KT.period == per_]; P = q.pivot_table(index="rf_class", columns="k10e_class", values="km2", aggfunc="sum").reindex(
                index=[CLASSES[k] for k in range(1, 11)], columns=[K10E[k] for k in range(1, 10)]).fillna(0)
            P = P[P.sum(axis=1) > 0.5]; R = P.div(P.sum(axis=1), axis=0) * 100
            ax.imshow(R.values, cmap="Oranges", vmin=0, vmax=100)
            for i in range(R.shape[0]):
                for j in range(R.shape[1]):
                    if R.values[i, j] >= 1:
                        ax.text(j, i, f"{R.values[i, j]:.0f}", ha="center", va="center", fontsize=7, color="white" if R.values[i, j] > 55 else "black")
            ax.set_xticks(range(R.shape[1]), [s.replace("_", " ").lower()[:16] for s in R.columns], rotation=45, ha="right", fontsize=7)
            ax.set_yticks(range(R.shape[0]), [f"{s.replace('_', ' ').lower()[:12]} · {P.loc[s].sum():,.0f} km²" for s in R.index], fontsize=7)
            ax.set_title(f"pool, {per_}: RF class (rows) × k10e surface state (row %)", fontsize=8, loc="left"); ax.set_xlabel("dominant k10e class (rule on the indices)")
        fig.suptitle("p102: what the RF classes on the drained bed are physically -- WorldCover has no exposed-sediment class, so the forest assigns it to the nearest land-cover classes", fontsize=9)
        fig.tight_layout(); fig.savefig(FIG / "ZONE_1_pool_rf_vs_k10e.png", dpi=120); plt.close(fig)
    print(f"-> tables/p102_rf_date_{{transition,rf_vs_k10e_pool}}.csv, figures/p102/ZONE_1_pool_{{transition,rf_vs_k10e}}.png ({time.time() - t0:.0f} s)", flush=True)


def step_train(a):
    import joblib, sklearn
    from sklearn.metrics import confusion_matrix
    t0 = time.time(); rng = np.random.default_rng(SEED); parts = []; inv = []
    for z in ZONES:
        y, tr = worldcover_target(z)
        for d in dates_of(z):
            if not (TRAIN_START <= d <= TRAIN_END):
                continue
            r = sample_date(z, d, y, tr, rng)
            if r is None:
                inv.append(dict(zone=z, date=d, n=0)); continue
            X7, yy, xc, yc = r; s_, c_ = doy(d)
            parts.append(dict(X=X7, y=yy, xc=xc, yc=yc, zone=np.full(len(yy), ZONES.index(z), "u1"), year=np.full(len(yy), int(d[:4]), "i2"),
                              doy=np.column_stack([np.full(len(yy), s_, "f4"), np.full(len(yy), c_, "f4")])))
            inv.append(dict(zone=z, date=d, n=int(len(yy)), **{f"n_{CLASSES[c]}": int((yy == c).sum()) for c in range(1, 10)}))
            print(f"  sample {z[:6]} {d}: {len(yy):,} cells ({time.time() - t0:.0f} s)", flush=True)
    cat = lambda k: np.concatenate([p[k] for p in parts])
    X7, ys, xc, yc, zone, year, DOY = (cat(k) for k in ("X", "y", "xc", "yc", "zone", "year", "doy"))
    blk = np.floor(yc / BLOCK_M).astype("i8") * 100000 + np.floor(xc / BLOCK_M).astype("i8")
    VAR = {"spectral": X7, "spectral+doy": np.hstack([X7, DOY])}
    FEAT = {"spectral": list(INDEX_NAMES), "spectral+doy": list(INDEX_NAMES) + ["doy_sin", "doy_cos"]}
    labels = [c for c in range(1, 10) if (ys == c).any()]
    ub = np.unique(blk); rng.shuffle(ub); fold = dict(zip(ub.tolist(), (np.arange(len(ub)) % 5).tolist())); fv = np.vectorize(fold.get)(blk)
    tr_, te = year <= 2022, year >= 2023
    print(f"training sample {len(ys):,} cells, {len(ub)} blocks, hold-out 2023: {int(te.sum()):,} ({time.time() - t0:.0f} s)", flush=True)
    met, macro = [], {}
    for var, X in VAR.items():
        pred = np.zeros_like(ys)
        for k in range(5):
            m = rf(a.jobs).fit(X[fv != k], ys[fv != k]); pred[fv == k] = m.predict(X[fv == k])
        met += metric_rows(ys, pred, labels, variant=var, evaluation="spatial_block_cv_5fold", zone="ALL")
        m = rf(a.jobs).fit(X[tr_], ys[tr_]); pr = m.predict(X[te])
        rows = metric_rows(ys[te], pr, labels, variant=var, evaluation="temporal_holdout_2023pre", zone="ALL"); met += rows
        macro[var] = next(r_["F1"] for r_ in rows if r_["cls"] == "MACRO")
        for zi, z in enumerate(ZONES):
            mz = zone[te] == zi
            if mz.sum() > 100:
                met += metric_rows(ys[te][mz], pr[mz], [c for c in labels if (ys[te][mz] == c).any()], variant=var, evaluation="temporal_holdout_2023pre", zone=z)
        pd.DataFrame(confusion_matrix(ys[te], pr, labels=labels), index=[CLASSES[c] for c in labels], columns=[CLASSES[c] for c in labels]
                     ).to_csv(CFG.TABLES / f"p102_rf_date_confusion_{var.replace('+', '_')}.csv")
        print(f"  {var}: temporal hold-out macro F1 {macro[var]:.3f} ({time.time() - t0:.0f} s)", flush=True)
    best = max(VARIANTS, key=lambda v: (macro[v], -VARIANTS.index(v)))                  # ties -> the simpler (spectral)
    if abs(macro["spectral"] - macro["spectral+doy"]) < 1e-9:
        best = "spectral"
    M = rf(a.jobs).fit(VAR[best], ys)
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(dict(model=M, variant=best, features=FEAT[best], classes=CLASSES, uncertain_p=UNCERTAIN_P, train_window=[TRAIN_START, TRAIN_END],
                     n_samples=int(len(ys)), seed=SEED, rf=RF), MODEL, compress=3)
    pd.DataFrame(met).to_csv(CFG.TABLES / "p102_rf_date_metrics.csv", index=False)
    pd.DataFrame(inv).to_csv(CFG.TABLES / "p102_rf_date_training_sample.csv", index=False)
    man = dict(product="p102_rf_surface_by_date", status="ACTIVE (product for the hydraulic model; not a Paper 3 result)", git=_git(),
               created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               purpose="land-cover class per Sentinel-2 date on the four zones, 2017-2026, from the indices of that date; weak WorldCover target",
               features=dict(variants=FEAT, production=best, rule="production = higher temporal-hold-out macro F1, ties -> spectral (fixed before the run)"),
               target=dict(source="ESA WorldCover 2021 (wc_2021_20m per zone, same lattice as the p25 stacks)", crosswalk={str(k): CLASSES[v] for k, v in WC2P.items()},
                           purity="3 x 3 WorldCover neighbourhood agrees", consistency=["WATER needs MNDWI > 0 on the date", "non-water classes need MNDWI < 0.3 on the date"],
                           train_window=[TRAIN_START, TRAIN_END], per_class_per_zone_date=PER_CLASS_DATE),
               evaluation=dict(spatial="5-fold spatial-block CV, 5 km global UTM blocks", temporal="fit 2021-2022, test 2023 pre-breach", macro_f1_temporal=macro),
               random_forest=RF, seed=SEED, uncertainty=f"top-class probability < {UNCERTAIN_P} -> UNCERTAIN (10)",
               software=dict(sklearn=sklearn.__version__, numpy=np.__version__, rasterio=rasterio.__version__), model=dict(path=str(MODEL), sha256=_sha(MODEL)),
               outputs=dict(rasters=str(OUT / "<ZONE>" / "<date>_rf.tif"), probability=str(OUT / "<ZONE>" / "<date>_rfp.tif")))
    (CFG.TABLES / "p102_rf_date_manifest.json").write_text(json.dumps(man, indent=1, default=str))
    print(f"-> model {MODEL} ({best}); tables/p102_rf_date_{{metrics,training_sample,confusion_*,manifest}} ({time.time() - t0:.0f} s)", flush=True)


def pool_mask(z, shape, tr):
    if not z.startswith("ZONE_1"):
        return None
    return features.rasterize([(CFG.load_utm("reservoir_full_pool_prebreach").__geo_interface__, 1)], out_shape=shape, transform=tr, fill=0, dtype="uint8").astype(bool)


def predict_date(MD, z, d, pool, force=False):
    od = OUT / z; od.mkdir(parents=True, exist_ok=True)
    fc, fp, fj = od / f"{d}_rf.tif", od / f"{d}_rfp.tif", od / f"{d}_rf.json"
    if fj.exists() and not force:
        return json.loads(fj.read_text())
    M, var = MD["model"], MD["variant"]; s_, c_ = doy(d)
    with rasterio.open(SPEC / z / f"{d}_indices.tif") as si, rasterio.open(SPEC / z / f"{d}_class.tif") as sc:
        H, W, tr, crs = si.height, si.width, si.transform, si.crs; scenes = sc.tags().get("scenes", "")
        prof = dict(driver="GTiff", height=H, width=W, count=1, dtype="uint8", crs=crs, transform=tr, compress="deflate", tiled=True, blockxsize=512, blockysize=512)
        counts = np.zeros(11, "i8"); pcounts = np.zeros(11, "i8"); n_valid = 0; n_pool_valid = 0
        with rasterio.open(fc, "w", nodata=0, **prof) as oc, rasterio.open(fp, "w", nodata=255, **prof) as op:
            for r0 in range(0, H, STRIP):
                h = min(STRIP, H - r0); win = rasterio.windows.Window(0, r0, W, h)
                X = si.read(window=win); v = (sc.read(1, window=win) != 0) & np.all(X != NODATA, axis=0)
                cls = np.zeros((h, W), "u1"); prb = np.full((h, W), 255, "u1")
                if v.any():
                    f = X[:, v].T.astype("f4") / 1e4
                    if var == "spectral+doy":
                        f = np.hstack([f, np.full((len(f), 1), s_, "f4"), np.full((len(f), 1), c_, "f4")])
                    best = np.empty(len(f), "u1"); mx = np.empty(len(f), "f4")
                    for i in range(0, len(f), CHUNK):
                        pp = M.predict_proba(f[i:i + CHUNK]); best[i:i + CHUNK] = M.classes_[pp.argmax(1)]; mx[i:i + CHUNK] = pp.max(1)
                    best[mx < UNCERTAIN_P] = 10; cls[v] = best; prb[v] = np.round(mx * 100)
                oc.write(cls, 1, window=win); op.write(prb, 1, window=win)
                counts += np.bincount(cls.ravel(), minlength=11); n_valid += int(v.sum())
                if pool is not None:
                    pm = pool[r0:r0 + h]; pcounts += np.bincount(cls[pm].ravel(), minlength=11); n_pool_valid += int((v & pm).sum())
            tags = dict(producer="p102_rf_surface_by_date.py", date=d, zone=z, classes=json.dumps(CLASSES), features=",".join(MD["features"]), variant=var,
                        uncertain_rule=f"top-class probability < {UNCERTAIN_P} -> 10", target="ESA WorldCover 2021 (weak reference)", model_sha256=MD["sha"],
                        meaning="land-cover class from the indices of this date; 0 = not observed (cloud / outside the scene)")
            oc.update_tags(**tags); op.update_tags(**{**tags, "meaning": "top-class probability x 100; 255 = not observed"})
    side = dict(zone=z, date=d, n_cells=int(H * W), n_valid=int(n_valid), valid_share=round(n_valid / (H * W), 4), scenes=scenes,
                km2={CLASSES[c]: round(float(counts[c]) * CELL_KM2, 2) for c in range(1, 11)})
    if pool is not None:
        side["pool"] = dict(n_cells=int(pool.sum()), n_valid=int(n_pool_valid), observed_share=round(n_pool_valid / max(int(pool.sum()), 1), 4),
                            km2={CLASSES[c]: round(float(pcounts[c]) * CELL_KM2, 2) for c in range(1, 11)})
    fj.write_text(json.dumps(side)); return side


def step_predict(a):
    import joblib
    MD = joblib.load(MODEL); MD["sha"] = _sha(MODEL); MD["model"].n_jobs = a.jobs; t0 = time.time(); n = 0
    for z in (a.zones or ZONES):
        ds = [d for d in dates_of(z) if (a.since is None or d >= a.since) and (a.until is None or d <= a.until)]
        ds = sorted(ds, key=lambda d: (d < "2023-01-01", d))                              # 2023 .. 2026 first, then the archive
        with rasterio.open(SPEC / z / f"{ds[0]}_indices.tif") as s:
            pool = pool_mask(z, s.shape, s.transform)
        for d in ds:
            t1 = time.time(); side = predict_date(MD, z, d, pool, a.force); n += 1
            print(f"  {z[:6]} {d}: valid {side['valid_share']:.1%}" + (f", pool observed {side['pool']['observed_share']:.1%}" if "pool" in side else "") + f" ({time.time() - t1:.0f} s; total {time.time() - t0:.0f} s)", flush=True)
    print(f"-> {n} zone-dates in {OUT} ({time.time() - t0:.0f} s)", flush=True)


def step_tables(a):
    rows, inv = [], []
    for z in ZONES:
        for fj in sorted((OUT / z).glob("*_rf.json")) if (OUT / z).exists() else []:
            s = json.loads(fj.read_text()); d = s["date"]
            inv.append(dict(zone=z, date=d, year=int(d[:4]), valid_share=s["valid_share"], n_valid=s["n_valid"], in_training=TRAIN_START <= d <= TRAIN_END,
                            pool_observed_share=s.get("pool", {}).get("observed_share"), scenes=s["scenes"], raster=str(OUT / z / f"{d}_rf.tif")))
            rows.append(dict(zone=z, date=d, year=int(d[:4]), stratum="ZONE", observed_share=s["valid_share"], **{f"{k}_km2": v for k, v in s["km2"].items()}))
            if "pool" in s:
                rows.append(dict(zone=z, date=d, year=int(d[:4]), stratum="POOL_PREBREACH", observed_share=s["pool"]["observed_share"], **{f"{k}_km2": v for k, v in s["pool"]["km2"].items()}))
    pd.DataFrame(inv).to_csv(CFG.TABLES / "p102_rf_date_inventory.csv", index=False)
    pd.DataFrame(rows).to_csv(CFG.TABLES / "p102_rf_date_class_area.csv", index=False)
    I = pd.DataFrame(inv)
    print(f"-> tables/p102_rf_date_{{inventory,class_area}}.csv: {len(I)} zone-dates; per year: {I.groupby('year').size().to_dict()}", flush=True)


def step_figures(a):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Patch
    FIG.mkdir(parents=True, exist_ok=True)
    A = pd.read_csv(CFG.TABLES / "p102_rf_date_class_area.csv"); I = pd.read_csv(CFG.TABLES / "p102_rf_date_inventory.csv")
    cmap = ListedColormap(["#ffffff"] + [COLORS[c] for c in range(1, 11)]); norm = BoundaryNorm(np.arange(-0.5, 11.5, 1), cmap.N)
    for z in ZONES:
        iz = I[(I.zone == z)].copy(); iz["q"] = iz.date.str[:4] + "Q" + ((pd.to_datetime(iz.date).dt.month - 1) // 3 + 1).astype(str)
        share = "pool_observed_share" if z.startswith("ZONE_1") else "valid_share"
        pick = iz[iz[share] >= 0.2].sort_values(share, ascending=False).drop_duplicates("q").sort_values("date")
        pick = pick[pick.date >= "2021-01-01"]
        if len(pick):
            n = len(pick); nc = 4; nr = int(np.ceil(n / nc)); fig, axs = plt.subplots(nr, nc, figsize=(4.2 * nc, 3.6 * nr), squeeze=False)
            for ax, (_, r) in zip(axs.ravel(), pick.iterrows()):
                with rasterio.open(r.raster) as s:
                    f = max(1, int(np.ceil(max(s.height, s.width) / 1200))); c = s.read(1, out_shape=(s.height // f, s.width // f))
                ax.imshow(c, cmap=cmap, norm=norm, interpolation="nearest"); ax.set_title(f"{r.date} · observed {r[share]:.0%}", fontsize=8, loc="left"); ax.set_axis_off()
            for ax in axs.ravel()[n:]:
                ax.set_axis_off()
            fig.legend(handles=[Patch(color=COLORS[c], label=CLASSES[c].replace("_", " ").lower()) for c in range(1, 11)], loc="lower center", ncol=5, fontsize=8, frameon=False)
            fig.suptitle(f"RF surface classes by date, {SHORT[z]} ({z}): the best-observed date of each quarter (p102; WorldCover 2021 as the weak target). Contains modified Copernicus Sentinel data.", fontsize=9)
            fig.tight_layout(rect=(0, 0.05, 1, 0.97)); fig.savefig(FIG / f"{z}_rf_by_date.png", dpi=110); plt.close(fig)
        st = "POOL_PREBREACH" if z.startswith("ZONE_1") else "ZONE"
        az = A[(A.zone == z) & (A.stratum == st) & (A.observed_share >= 0.5)].sort_values("date")
        if len(az) >= 3:
            cols = [f"{CLASSES[c]}_km2" for c in range(1, 11)]; tot = az[cols].sum(axis=1).replace(0, np.nan)
            fig, ax = plt.subplots(figsize=(11, 4)); t = pd.to_datetime(az.date)
            ax.stackplot(t, *[az[c] / tot * 100 for c in cols], colors=[COLORS[c] for c in range(1, 11)], labels=[CLASSES[c].replace("_", " ").lower() for c in range(1, 11)], step="post")
            ax.axvline(pd.Timestamp("2023-06-06"), color="#e34948", ls="--", lw=1); ax.set_ylim(0, 100); ax.set_ylabel("share of the observed cells, %")
            ax.set_title(f"RF classes over time, {SHORT[z]}" + (" (pre-breach pool)" if st != "ZONE" else "") + f": dates observing >= 50 % ({len(az)} dates)", fontsize=9, loc="left")
            ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=7, frameon=False); fig.tight_layout(); fig.savefig(FIG / f"{z}_rf_class_series.png", dpi=120); plt.close(fig)
    print(f"-> {FIG}", flush=True)


def _sha(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(16 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _git():
    root = Path(__file__).resolve().parents[4]
    run = lambda *x: subprocess.run(["git", *x], cwd=root, capture_output=True, text=True).stdout.strip()
    return dict(commit=run("rev-parse", "HEAD"), dirty_tracked=bool(run("status", "--porcelain", "--untracked-files=no")))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--step", choices=["train", "predict", "tables", "figures", "evaluate", "transition", "all"], default="all")
    ap.add_argument("--zones", nargs="*", choices=ZONES); ap.add_argument("--since"); ap.add_argument("--until"); ap.add_argument("--force", action="store_true")
    ap.add_argument("--jobs", type=int, default=24)
    a = ap.parse_args()
    if a.step in ("train", "all"):
        step_train(a)
    if a.step in ("predict", "all"):
        step_predict(a)
    if a.step in ("tables", "all"):
        step_tables(a)
    if a.step in ("figures", "all"):
        step_figures(a)
    if a.step in ("evaluate", "all"):
        step_evaluate(a)
    if a.step in ("transition", "all"):
        step_transition(a)


if __name__ == "__main__":
    main()
