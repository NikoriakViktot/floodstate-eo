# New in floodstate-eo, 2026-09-23. STATUS: ACTIVE (development). Must NOT enter any U-Net until m6_labels_v002 is frozen.
"""P73 -- RF20: PRE-EVENT SURFACE CLASSIFICATION on the global native-aligned 20 m Sentinel-2 grid. Not flood detection.

PURPOSE. U0 separates delta/wetland inundation well and agricultural false water badly (VEG_AGRI F1 0.39 against
WETLAND 0.98). p73 is meant to tell a later model "this is a field, that is reed" -- independently of every flood
label, so that when it becomes an INPUT (U1) it cannot also be part of the TARGET.

INDEPENDENCE, ENFORCED. Predictors are PRE-event Sentinel-2 composite bands only (every band read must be named
`*_pre_*` / `*_pre_seas_*`); the target is ESA WorldCover 2021. Refused at read time: M2 (cand_score/flood_*), p69a
BASE_CLASS, p69b, S1 change, flood labels (labels.tif, m6_labels_*), HAND, UNOSAT, TRACE and EVENT bands, any U-Net
output. BASE_CLASS is NOT the target because it is already entangled with the old flood-label chain.

THE GRID. 20 m cells with origin on multiples of 20 m in EPSG:32636 -- the lattice Sentinel-2's own 20 m bands live on
(tile ULX/ULY are multiples of 20). The 10 m composites sit on it exactly in B1; B2's lattice is offset by 10 m in y, so
its 20 m cells are the 2x2 blocks starting one row down. Aggregation is a strict 2x2 mean: a cell with any nodata
sub-cell is nodata. CAVEAT, recorded not hidden: the 10 m composites carry 20 m bands already bilinearly resampled once
(p54b), so 2x2-averaging them approximates but is not identical to native 20 m values.

THE TARGET, AND ITS HALF-CELL SHIFT. The local WorldCover rasters are 20 m but on an origin offset by 10 m in both axes
from the S2 grid. Rather than resample a categorical layer at a half-cell offset, each p73 cell takes a target only if
ALL FOUR WorldCover cells it overlaps agree (a 30 m purity footprint); otherwise IGNORE. Then conflicts with the
PRE-event S2 evidence become IGNORE too (rules in CONSISTENCY): a weak reference is not forced onto every pixel.

EVALUATION IS AS A LAND-COVER CLASSIFIER, against held-out WorldCover (itself a weak reference, ~75 % overall accuracy
globally): 5-fold spatial-block CV on 5 km blocks, plus B1 -> B2 and B2 -> B1 transfer. No flood metric appears here.

UNCERTAIN (code 10) is assigned where the forest's top-class probability is below 0.5 -- fixed before any result was
seen and never tuned on flood labels.

Outputs: $BULK_ROOT/frames10/<F>/p73_surface_20m.tif (band 1 class, band 2 top probability x100, band 3 margin x100)
         <case_study>/tables/p73_{inventory,target_filter,cv_by_class,cv_confusion,transfer}.csv
"""
from __future__ import annotations
import argparse, json, re, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio, rasterio.windows
from rasterio.transform import from_origin
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
WCZ = {"B1": "ZONE_4_DAM_TO_KHERSON_FLOODWAY", "B2": "ZONE_2_KHERSON_DELTA"}
CLASSES = {1: "WATER", 2: "CROPLAND", 3: "GRASS_LOW_VEGETATION", 4: "FOREST", 5: "SHRUB", 6: "WETLAND_REED",
           7: "BUILT_UP", 8: "BARE_SAND", 9: "OTHER", 10: "UNCERTAIN"}
WC2P73 = {80: 1, 40: 2, 30: 3, 10: 4, 20: 5, 90: 6, 50: 7, 60: 8, 70: 9, 95: 9, 100: 9}
UNCERTAIN_P = 0.5
BLOCK_M = 5000.0
PER_CLASS = 30000            # training cells per class per frame (a sample, never the whole population)
SEED = 20260923
FORBIDDEN = re.compile(r"cand_|flood_|p69|base_class|s1_change|labels|m6_label|hand|unosat|trace|event|u0_",
                       re.IGNORECASE)
_opened: list[str] = []


def _guard(p: Path, band_names=None):
    if FORBIDDEN.search(p.name):
        raise SystemExit(f"p73: refusing to read {p} -- forbidden input for a pre-event surface classifier")
    for b in band_names or []:
        if "_pre_" not in b or FORBIDDEN.search(b):
            raise SystemExit(f"p73: refusing band {b!r} of {p.name} -- only *_pre_* bands are predictors")
    _opened.append(str(p))
    return p


def grid20(fid):
    """The frame's cells on the global 20 m grid: (row offset, col offset) into the 10 m lattice, shape, transform."""
    F = CG.frame_grid(fid); t = F["transform"]
    r0 = int(round((t.f % 20.0) / 10.0)); c0 = int(round(((20.0 - t.c % 20.0) % 20.0) / 10.0))
    x0, y1 = t.c + c0 * 10.0, t.f - r0 * 10.0
    assert x0 % 20.0 == 0 and y1 % 20.0 == 0, (x0, y1)
    ny, nx = (F["ny"] - r0) // 2, (F["nx"] - c0) // 2
    return dict(r0=r0, c0=c0, ny=ny, nx=nx, transform=from_origin(x0, y1, 20.0, 20.0), F=F)


def agg2(a, g, nd):
    """Strict 2x2 mean onto the 20 m grid: any nodata sub-cell makes the cell nodata."""
    s = a[g["r0"]:g["r0"] + 2 * g["ny"], g["c0"]:g["c0"] + 2 * g["nx"]].astype("f4")
    bad = s == nd
    s[bad] = np.nan
    s = s.reshape(g["ny"], 2, g["nx"], 2)
    out = s.mean(axis=(1, 3))
    out[bad.reshape(g["ny"], 2, g["nx"], 2).any(axis=(1, 3))] = np.nan
    return out


def predictors(fid, g):
    X, names = [], []
    for comp in ("composite_preall.tif", "composite_preseas.tif"):
        p = OUT / fid / comp
        with rasterio.open(p) as s:
            d = list(s.descriptions)
            idx = [i + 1 for i, n in enumerate(d) if "_pre_" in n and not n.startswith("n_obs")]
            _guard(p, [d[i - 1] for i in idx])
            nd = s.nodata if s.nodata is not None else -32768
            nob = [i + 1 for i, n in enumerate(d) if n == "n_obs_pre"] if comp == "composite_preall.tif" else []
            want = idx + nob
            # PIXEL-INTERLEAVED, DEFLATE: one band at a time decompresses every block once PER BAND (48 full passes
            # over an 8.8 GB file on /mnt/f). Read all wanted bands per 128-row strip instead -- each block once.
            out = np.full((len(want), g["ny"], g["nx"]), np.nan, "f4")
            H = 128
            for k in range(0, g["ny"], H // 2):
                n20 = min(H // 2, g["ny"] - k)
                r = g["r0"] + 2 * k
                blk = s.read(want, window=rasterio.windows.Window(g["c0"], r, 2 * g["nx"], 2 * n20))
                sub = dict(r0=0, c0=0, ny=n20, nx=g["nx"])
                for j in range(len(want)):
                    out[j, k:k + n20] = agg2(blk[j], sub, nd)
            for j, i in enumerate(idx):
                X.append(out[j] / 10000.0); names.append(f"{comp.split('_')[1][:-4]}:{d[i - 1]}")
            if nob:
                nobs = out[len(idx)]
            del out
    return np.stack(X), names, nobs


def target(fid, g, X, names):
    """WorldCover -> p73 code where all four overlapping WorldCover cells agree AND the PRE S2 evidence does not
    contradict it; 0 = IGNORE. Returns the target and a per-rule count table."""
    p = CFG.BULK_ROOT / "worldcover_frames" / WCZ[fid] / "wc_2021_20m.tif"
    with rasterio.open(_guard(p)) as s:
        wc = s.read(1); wt = s.transform
    assert abs(wt.a - 20.0) < 1e-9 and abs(wt.e + 20.0) < 1e-9
    gt = g["transform"]
    sr, sc = (wt.f - gt.f) / 20.0, (gt.c - wt.c) / 20.0          # expected k + 0.5
    kr, kc = int(np.floor(sr)), int(np.floor(sc))
    assert abs(sr - kr - 0.5) < 1e-6 and abs(sc - kc - 0.5) < 1e-6, f"WorldCover offset {sr},{sc} is not a half cell"
    # W[i, j] = WorldCover cell (kr + i, kc + j); cells outside the WorldCover raster stay 0 (= no target)
    W = np.zeros((g["ny"] + 1, g["nx"] + 1), wc.dtype)
    r_a, r_b = max(kr, 0), min(kr + g["ny"] + 1, wc.shape[0])
    c_a, c_b = max(kc, 0), min(kc + g["nx"] + 1, wc.shape[1])
    if r_b > r_a and c_b > c_a:
        W[r_a - kr:r_b - kr, c_a - kc:c_b - kc] = wc[r_a:r_b, c_a:c_b]
    q = [W[i:i + g["ny"], j:j + g["nx"]] for i in (0, 1) for j in (0, 1)]
    pure = (q[0] == q[1]) & (q[0] == q[2]) & (q[0] == q[3]) & (q[0] > 0)
    y = np.zeros((g["ny"], g["nx"]), np.uint8)
    for wv, pc in WC2P73.items():
        y[pure & (q[0] == wv)] = pc
    rows = [dict(frame=fid, rule="worldcover_4cell_pure", kept=int((y > 0).sum()),
                 dropped=int(((q[0] > 0) & ~pure).sum()))]
    col = {n.split(":", 1)[1] + ("@seas" if n.startswith("preseas") else ""): i for i, n in enumerate(names)}
    mndwi, ndvi_max = X[col["MNDWI_pre_med"]], X[col["NDVI_pre_max"]]
    CONSISTENCY = [
        ("WATER needs MNDWI_pre_med > 0", (y == 1) & ~(mndwi > 0)),
        ("vegetated classes need NDVI_pre_max > 0.3", np.isin(y, (2, 3, 4, 5, 6)) & ~(ndvi_max > 0.3)),
        ("non-water classes need MNDWI_pre_med < 0.3", np.isin(y, (2, 3, 4, 5, 7, 8)) & ~(mndwi < 0.3)),
        ("BARE_SAND needs NDVI_pre_max < 0.4", (y == 8) & ~(ndvi_max < 0.4)),
    ]
    for nm, bad in CONSISTENCY:
        rows.append(dict(frame=fid, rule=nm, kept=None, dropped=int(bad.sum()))); y[bad] = 0
    rows.append(dict(frame=fid, rule="final_targets", kept=int((y > 0).sum()), dropped=None))
    return y, rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=["B1", "B2"])
    ap.add_argument("--trees", type=int, default=200); ap.add_argument("--jobs", type=int, default=16)
    a = ap.parse_args()
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
    rng = np.random.default_rng(SEED)
    D, inv, filt = {}, [], []
    for fid in a.frames:
        t0 = time.time(); g = grid20(fid)
        X, names, nobs = predictors(fid, g)
        y, rows = target(fid, g, X, names); filt += rows
        ok = np.all(np.isfinite(X), axis=0) & (nobs >= 5)
        y[~ok] = 0
        by, bx = np.indices(y.shape)
        blk = (by * 20 // BLOCK_M).astype("i4") * 1000 + (bx * 20 // BLOCK_M).astype("i4")
        D[fid] = dict(g=g, X=X, y=y, ok=ok, blk=blk)
        inv.append(dict(frame=fid, ny20=g["ny"], nx20=g["nx"], row_offset_10m=g["r0"], col_offset_10m=g["c0"],
                        x0=g["transform"].c, y1=g["transform"].f, n_features=len(names),
                        valid_cells=int(ok.sum()), target_cells=int((y > 0).sum()),
                        **{f"target_{CLASSES[c]}": int((y == c).sum()) for c in range(1, 10)},
                        seconds=round(time.time() - t0)))
        print(f"{fid}: 20 m grid {g['ny']}x{g['nx']} (offset {g['r0']},{g['c0']}), {len(names)} PRE features, "
              f"{int((y > 0).sum()):,} target cells", flush=True)
    pd.DataFrame(inv).to_csv(CFG.TABLES / "p73_inventory.csv", index=False)
    pd.DataFrame(filt).to_csv(CFG.TABLES / "p73_target_filter.csv", index=False)

    def sample(fid):
        d = D[fid]; idx = []
        for c in range(1, 10):
            w = np.flatnonzero(d["y"].ravel() == c)
            if len(w):
                idx.append(rng.choice(w, size=min(PER_CLASS, len(w)), replace=False))
        idx = np.concatenate(idx)
        return d["X"].reshape(len(names), -1)[:, idx].T, d["y"].ravel()[idx], d["blk"].ravel()[idx] + \
            (0 if fid == "B1" else 10**6)
    S = {fid: sample(fid) for fid in D}
    Xs = np.concatenate([S[f][0] for f in S]); ys = np.concatenate([S[f][1] for f in S])
    gs = np.concatenate([S[f][2] for f in S])
    mk = lambda: RandomForestClassifier(n_estimators=a.trees, min_samples_leaf=5, n_jobs=a.jobs,
                                        class_weight="balanced_subsample", random_state=SEED)
    labels = [c for c in range(1, 10) if (ys == c).any()]

    # ---- 5-fold spatial-block CV ---------------------------------------------------------------------------------
    ub = np.unique(gs); rng.shuffle(ub); fold = {b: i % 5 for i, b in enumerate(ub)}
    fv = np.vectorize(fold.get)(gs); pred = np.zeros_like(ys)
    for k in range(5):
        m = mk().fit(Xs[fv != k], ys[fv != k]); pred[fv == k] = m.predict(Xs[fv == k])
    P, R, F1, N = precision_recall_fscore_support(ys, pred, labels=labels, zero_division=0)
    cv = pd.DataFrame(dict(cls=[CLASSES[c] for c in labels], precision=P.round(4), recall=R.round(4),
                           F1=F1.round(4), n=N))
    cv.loc[len(cv)] = ["MACRO", P.mean().round(4), R.mean().round(4), F1.mean().round(4), int(N.sum())]
    cv.loc[len(cv)] = ["OVERALL_ACCURACY", None, None, round(float((pred == ys).mean()), 4), int(N.sum())]
    cv.to_csv(CFG.TABLES / "p73_cv_by_class.csv", index=False)
    pd.DataFrame(confusion_matrix(ys, pred, labels=labels), index=[CLASSES[c] for c in labels],
                 columns=[CLASSES[c] for c in labels]).to_csv(CFG.TABLES / "p73_cv_confusion.csv")
    print(cv.to_string(index=False), flush=True)

    # ---- geographic transfer between frames ----------------------------------------------------------------------
    tr = []
    if len(S) > 1:
        for src, dst in (("B1", "B2"), ("B2", "B1")):
            m = mk().fit(S[src][0], S[src][1]); pr = m.predict(S[dst][0])
            P, R, F1, N = precision_recall_fscore_support(S[dst][1], pr, labels=labels, zero_division=0)
            tr += [dict(train=src, test=dst, cls=CLASSES[c], precision=round(p_, 4), recall=round(r_, 4),
                        F1=round(f_, 4), n=int(n_)) for c, p_, r_, f_, n_ in zip(labels, P, R, F1, N)]
            tr.append(dict(train=src, test=dst, cls="OVERALL_ACCURACY", F1=round(float((pr == S[dst][1]).mean()), 4)))
        pd.DataFrame(tr).to_csv(CFG.TABLES / "p73_transfer.csv", index=False)

    # ---- final model on all sampled targets, wall-to-wall prediction ---------------------------------------------
    M = mk().fit(Xs, ys)
    for fid, d in D.items():
        g = d["g"]; flat = d["X"].reshape(len(names), -1).T; okf = d["ok"].ravel()
        cls = np.full(okf.shape, 255, np.uint8); top = np.full(okf.shape, 255, np.uint8)
        mar = np.full(okf.shape, 255, np.uint8)
        w = np.flatnonzero(okf)
        for i in range(0, len(w), 2_000_000):
            ii = w[i:i + 2_000_000]; pp = M.predict_proba(flat[ii])
            srt = np.sort(pp, axis=1); best = M.classes_[pp.argmax(1)].astype("u1")
            best[srt[:, -1] < UNCERTAIN_P] = 10
            cls[ii] = best; top[ii] = np.round(srt[:, -1] * 100); mar[ii] = np.round((srt[:, -1] - srt[:, -2]) * 100)
        prof = dict(driver="GTiff", height=g["ny"], width=g["nx"], count=3, dtype="uint8", nodata=255,
                    crs=CFG.CRS_METRIC, transform=g["transform"], compress="deflate", tiled=True,
                    blockxsize=512, blockysize=512)
        p = OUT / fid / "p73_surface_20m.tif"
        with rasterio.open(p.with_suffix(".tif.part"), "w", **prof) as o:
            for b, (arr, nm) in enumerate(((cls, "p73_class"), (top, "top_probability_x100"),
                                           (mar, "margin_x100")), 1):
                o.write(arr.reshape(g["ny"], g["nx"]), b); o.set_band_description(b, nm)
            o.update_tags(classes=json.dumps(CLASSES), uncertain_rule=f"top probability < {UNCERTAIN_P}",
                          predictors="PRE-event S2 composite bands only: " + ";".join(names),
                          target="ESA WorldCover 2021, 4-cell purity + PRE-S2 consistency (weak reference)",
                          inputs_read=json.dumps(sorted(set(_opened))),
                          forbidden_not_read="M2, p69a/BASE_CLASS, p69b, S1 change, flood labels, HAND, UNOSAT, "
                                             "TRACE/EVENT bands, U-Net outputs",
                          status="DEVELOPMENT: must not enter a U-Net before m6_labels_v002 is frozen",
                          producer="p73_rf20_surface.py")
        p.with_suffix(".tif.part").replace(p)
        u, c = np.unique(cls[okf], return_counts=True)
        print(f"{fid} -> {p.name}: " + ", ".join(f"{CLASSES.get(int(k), k)} {v * 4e-4:.0f} km2"
                                                 for k, v in zip(u, c)), flush=True)


if __name__ == "__main__":
    main()
