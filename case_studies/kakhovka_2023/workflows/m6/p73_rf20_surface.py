# New in floodstate-eo, 2026-09-23. STATUS: P73_RF20_FROZEN (products of commit 5f875ce; QA: tables/p73_rf20_qa/QA_VERDICT.md).
# Rev 2 FROZEN 2026-09-29 (products reproduced bit for bit at acf190c; QA: tables/p73_rf20_rev2_qa/QA_VERDICT.md) -- the RF20 in use.
# May enter a U-Net only as INPUT context (U1) after the B1+B2 split is frozen; never in label construction.
# Rev 2 (2026-09-29, review 2026-09-28 F08; `--rev 2`, versioned outputs `_rev2`, rev 1 untouched): 5 km blocks from the
# UTM coordinates of the 20 m cells (one physical cell, one block, in both frames); B2 owns the B1/B2 overlap and B1
# contributes no target there, so a physical cell enters the sample once (asserted); the CV is reported without and with a
# 3.5 km buffer around the test blocks; the frame transfers train and test outside the overlap only.
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

Outputs: $BULK_ROOT/frames10/<F>/p73_rf20/{surface_class,surface_max_score,surface_uncertain,surface_scores}_20m.tif
         (20 m only; never upsampled here), $BULK_ROOT/frames10/_m6/p73_rf20_model.joblib,
         <case_study>/tables/p73_{inventory,target_filter}.csv, p73_rf20_{metrics,confusion_matrix,class_area}.csv,
         p73_rf20_manifest.json. `--infer B3` = pure inference with the persisted model (no training, no tuning).
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
BUFFER_M = 3500.0            # rev 2: the predictor autocorrelation range measured for the same S2 composites (p65b)
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
    ap.add_argument("--rev", type=int, default=1, choices=[1, 2], help="2: global UTM blocks, B2 owns the overlap before sampling, buffered CV, transfer outside the overlap (F08)")
    a = ap.parse_args()
    R2 = a.rev == 2; TG = "_rev2" if R2 else ""
    global MODEL
    if R2:
        MODEL = OUT / "_m6" / "p73_rf20_rev2_model.joblib"
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
    git0 = _git()          # captured BEFORE this run writes any tracked table, so "dirty" means the code state
    rng = np.random.default_rng(SEED)
    D, inv, filt = {}, [], []
    for fid in a.frames:
        t0 = time.time(); g = grid20(fid)
        X, names, nobs = predictors(fid, g)
        y, rows = target(fid, g, X, names); filt += rows
        ok = np.all(np.isfinite(X), axis=0) & (nobs >= 5)
        y[~ok] = 0
        by, bx = np.indices(y.shape)
        if R2:                                       # global UTM blocks; the overlap belongs to B2
            xc = g["transform"].c + 20.0 * (bx + 0.5); yc = g["transform"].f - 20.0 * (by + 0.5)
            blk = np.floor(yc / BLOCK_M).astype("i8") * 100000 + np.floor(xc / BLOCK_M).astype("i8")
            ovl = np.zeros(y.shape, bool)
            for other in (f for f in ("B1", "B2") if f != fid):
                go = grid20(other); X0, Y1 = go["transform"].c, go["transform"].f
                ovl |= (xc >= X0) & (xc < X0 + 20.0 * go["nx"]) & (yc <= Y1) & (yc > Y1 - 20.0 * go["ny"])
            n_drop = int(((y > 0) & ovl).sum()) if fid == "B1" else 0
            if fid == "B1":
                y[ovl] = 0
            D[fid] = dict(g=g, X=X, y=y, ok=ok, blk=blk, xc=xc, yc=yc, ovl=ovl, n_overlap_targets_dropped=n_drop)
        else:
            blk = (by * 20 // BLOCK_M).astype("i4") * 1000 + (bx * 20 // BLOCK_M).astype("i4")
            D[fid] = dict(g=g, X=X, y=y, ok=ok, blk=blk)
        inv.append(dict(frame=fid, ny20=g["ny"], nx20=g["nx"], row_offset_10m=g["r0"], col_offset_10m=g["c0"],
                        x0=g["transform"].c, y1=g["transform"].f, n_features=len(names),
                        valid_cells=int(ok.sum()), target_cells=int((y > 0).sum()),
                        **{f"target_{CLASSES[c]}": int((y == c).sum()) for c in range(1, 10)}))
        print(f"{fid}: 20 m grid {g['ny']}x{g['nx']} (offset {g['r0']},{g['c0']}), {len(names)} PRE features, "
              f"{int((y > 0).sum()):,} target cells, {time.time() - t0:.0f}s", flush=True)
    if R2:
        for r_ in inv:
            r_["overlap_targets_dropped_B2_owns"] = D[r_["frame"]]["n_overlap_targets_dropped"]
    pd.DataFrame(inv).to_csv(CFG.TABLES / f"p73_inventory{TG}.csv", index=False)
    pd.DataFrame(filt).to_csv(CFG.TABLES / f"p73_target_filter{TG}.csv", index=False)

    def sample(fid):
        d = D[fid]; idx = []
        for c in range(1, 10):
            w = np.flatnonzero(d["y"].ravel() == c)
            if len(w):
                idx.append(rng.choice(w, size=min(PER_CLASS, len(w)), replace=False))
        idx = np.concatenate(idx)
        if R2:
            return (d["X"].reshape(len(names), -1)[:, idx].T, d["y"].ravel()[idx], d["blk"].ravel()[idx],
                    d["xc"].ravel()[idx], d["yc"].ravel()[idx], d["ovl"].ravel()[idx])
        return d["X"].reshape(len(names), -1)[:, idx].T, d["y"].ravel()[idx], d["blk"].ravel()[idx] + \
            (0 if fid == "B1" else 10**6)
    S = {fid: sample(fid) for fid in D}
    Xs = np.concatenate([S[f][0] for f in S]); ys = np.concatenate([S[f][1] for f in S])
    gs = np.concatenate([S[f][2] for f in S])
    if R2:
        cx = np.concatenate([S[f][3] for f in S]); cy = np.concatenate([S[f][4] for f in S])
        key = np.round(cx).astype("i8") * 10_000_000 + np.round(cy).astype("i8")
        assert len(np.unique(key)) == len(key), "a physical cell entered the sample twice"

        def far_from(test):                          # training cells farther than BUFFER_M from every test block
            x0, y1 = cx.min() - BLOCK_M, cy.max() + BLOCK_M; cell = 100.0
            nx = int((cx.max() + BLOCK_M - x0) // cell) + 2; ny = int((y1 - cy.min() + BLOCK_M) // cell) + 2
            from scipy import ndimage
            ub_t = np.unique(gs[test]); gxx = x0 + cell * (np.arange(nx) + 0.5); gyy = y1 - cell * (np.arange(ny) + 0.5)
            gb = np.floor(gyy / BLOCK_M).astype("i8")[:, None] * 100000 + np.floor(gxx / BLOCK_M).astype("i8")[None, :]
            dist = ndimage.distance_transform_edt(~np.isin(gb, ub_t), sampling=cell)
            return dist[((y1 - cy) // cell).astype(int), ((cx - x0) // cell).astype(int)] >= BUFFER_M
    mk = lambda: RandomForestClassifier(n_estimators=a.trees, min_samples_leaf=5, n_jobs=a.jobs,
                                        class_weight="balanced_subsample", random_state=SEED)
    labels = [c for c in range(1, 10) if (ys == c).any()]

    # ---- 5-fold spatial-block CV (rev 2: also with a buffer around the test blocks) ------------------------------------
    ub = np.unique(gs); rng.shuffle(ub); fold = {b: i % 5 for i, b in enumerate(ub)}
    fv = np.vectorize(fold.get)(gs); met = []
    for ev, buffered in (("spatial_block_cv_5fold", False),) + ((("spatial_block_cv_5fold_buffered", True),) if R2 else ()):
        pred = np.zeros_like(ys); kept = []
        for k in range(5):
            tr = fv != k
            if buffered:
                tr &= far_from(fv == k); kept.append(round(float(tr.sum() / max((fv != k).sum(), 1)), 4))
            m = mk().fit(Xs[tr], ys[tr]); pred[fv == k] = m.predict(Xs[fv == k])
        P, R, F1, N = precision_recall_fscore_support(ys, pred, labels=labels, zero_division=0)
        met += [dict(evaluation=ev, cls=CLASSES[c], precision=round(p_, 4), recall=round(r_, 4),
                     F1=round(f_, 4), n=int(n_)) for c, p_, r_, f_, n_ in zip(labels, P, R, F1, N)]
        met.append(dict(evaluation=ev, cls="MACRO", precision=round(P.mean(), 4),
                        recall=round(R.mean(), 4), F1=round(F1.mean(), 4), n=int(N.sum()),
                        **({"train_kept_share_per_fold": str(kept)} if buffered else {})))
        met.append(dict(evaluation=ev, cls="OVERALL_ACCURACY", F1=round(float((pred == ys).mean()), 4),
                        n=int(N.sum())))
        pd.DataFrame(confusion_matrix(ys, pred, labels=labels), index=[CLASSES[c] for c in labels],
                     columns=[CLASSES[c] for c in labels]).to_csv(CFG.TABLES / f"p73_rf20_confusion_matrix{TG}{'_buffered' if buffered else ''}.csv")
    print(pd.DataFrame([r for r in met]).to_string(index=False), flush=True)

    # ---- geographic transfer between frames ----------------------------------------------------------------------
    if len(S) > 1:
        for src, dst in (("B1", "B2"), ("B2", "B1")):
            ms = ~S[src][5] if R2 else slice(None); md = ~S[dst][5] if R2 else slice(None)   # rev 2: outside the overlap only
            m = mk().fit(S[src][0][ms], S[src][1][ms]); pr = m.predict(S[dst][0][md])
            P, R, F1, N = precision_recall_fscore_support(S[dst][1][md], pr, labels=labels, zero_division=0)
            ev = f"transfer_{src}_to_{dst}"
            met += [dict(evaluation=ev, cls=CLASSES[c], precision=round(p_, 4), recall=round(r_, 4), F1=round(f_, 4),
                         n=int(n_)) for c, p_, r_, f_, n_ in zip(labels, P, R, F1, N)]
            met.append(dict(evaluation=ev, cls="MACRO", precision=round(P.mean(), 4), recall=round(R.mean(), 4),
                            F1=round(F1.mean(), 4), n=int(N.sum())))
            met.append(dict(evaluation=ev, cls="OVERALL_ACCURACY", F1=round(float((pr == S[dst][1][md]).mean()), 4),
                            n=int(N.sum())))
    pd.DataFrame(met).to_csv(CFG.TABLES / f"p73_rf20{TG}_metrics.csv" if R2 else CFG.TABLES / "p73_rf20_metrics.csv", index=False)

    # ---- final model on all sampled targets, persisted, then wall-to-wall prediction ----------------------------
    import joblib, sklearn
    M = mk().fit(Xs, ys)
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(dict(model=M, features=names, classes=CLASSES, uncertain_p=UNCERTAIN_P), MODEL, compress=3)
    areas = []
    for fid, d in D.items():
        areas += write_products(M, names, fid, d["g"], d["X"], d["ok"], sub="p73_rf20" + TG)
    pd.DataFrame(areas).to_csv(CFG.TABLES / f"p73_rf20{TG}_class_area.csv", index=False)

    rf = mk().get_params()
    man = dict(product="p73_rf20", status="FREEZE_CANDIDATE (set to P73_RF20_FROZEN only after visual + statistical QA)",
               git=git0, created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               purpose="PRE-event surface classification; not flood detection; not yet a U-Net input",
               grid={f: dict(crs=CFG.CRS_METRIC, cell_m=20.0, x0=d["g"]["transform"].c, y1=d["g"]["transform"].f,
                             ny=d["g"]["ny"], nx=d["g"]["nx"], row_offset_10m=d["g"]["r0"], col_offset_10m=d["g"]["c0"],
                             rule="global S2 20 m lattice (origin multiple of 20 m); strict 2x2 mean of the 10 m "
                                  "composite, any nodata sub-cell -> nodata") for f, d in D.items()},
               features=dict(order=names, n=len(names), source="composite_preall + composite_preseas *_pre_* bands, "
                             "value/10000; valid only where all features finite and n_obs_pre >= 5"),
               target=dict(source="ESA WorldCover 2021 (wc_2021_20m per zone)", crosswalk=P_WC(),
                           rule="all four half-cell-shifted WorldCover cells agree, then PRE-S2 consistency filters "
                                "(tables/p73_target_filter.csv); conflict -> IGNORE",
                           classes_without_targets=[CLASSES[c] for c in range(1, 10) if c not in labels]),
               split=dict(cv="5-fold spatial block CV" + (" (+ buffered)" if R2 else ""), block_m=BLOCK_M, block_to_fold="shuffled block ids, i % 5",
                          block_ids="UTM coordinates of the 20 m cell centres (global)" if R2 else "frame-local row/col, +1e6 for B2 (superseded, review F08)",
                          overlap="B2 owns; B1 contributes no target there; unique physical cells asserted" if R2 else "not deduplicated (superseded)",
                          buffer_m=BUFFER_M if R2 else None,
                          transfer="B1->B2 and B2->B1" + (", outside the overlap only" if R2 else ""), sample_per_class_per_frame=PER_CLASS),
               random_forest={k: rf[k] for k in ("n_estimators", "min_samples_leaf", "class_weight", "random_state")},
               seed=SEED, uncertainty=dict(rule=f"top class probability < {UNCERTAIN_P} -> UNCERTAIN (10)",
                                           fixed_before_results=True),
               software=dict(sklearn=sklearn.__version__, numpy=np.__version__, rasterio=rasterio.__version__),
               model=dict(path=str(MODEL), sha256=_sha(MODEL)),
               sources={p_: _sha(Path(p_)) for p_ in sorted(set(_opened))},
               products={f: [str(OUT / f / ("p73_rf20" + TG) / n) for n in PRODUCTS] for f in D}, rev=a.rev)
    (CFG.TABLES / f"p73_rf20{TG}_manifest.json").write_text(json.dumps(man, indent=1, default=str))
    print(f"-> tables/p73_rf20_{{metrics,confusion_matrix,class_area,manifest}}; model {MODEL}", flush=True)


PRODUCTS = ("surface_class_20m.tif", "surface_max_score_20m.tif", "surface_uncertain_20m.tif", "surface_scores_20m.tif")
MODEL = OUT / "_m6" / "p73_rf20_model.joblib"


def P_WC():
    return {str(k): CLASSES[v] for k, v in WC2P73.items()}


def _sha(p: Path):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(16 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _git():
    import subprocess
    root = Path(__file__).resolve().parents[4]
    run = lambda *a: subprocess.run(["git", *a], cwd=root, capture_output=True, text=True).stdout.strip()
    return dict(commit=run("rev-parse", "HEAD"), dirty_tracked=bool(run("status", "--porcelain", "--untracked-files=no")),
                worktree=str(root))


def write_products(M, names, fid, g, X, ok, sub="p73_rf20"):
    """Four 20 m products per frame. Never upsampled here."""
    flat = X.reshape(len(names), -1).T; okf = ok.ravel(); nc = len(M.classes_)
    cls = np.full(okf.shape, 255, np.uint8); top = np.full(okf.shape, 255, np.uint8)
    unc = np.full(okf.shape, 255, np.uint8); sc = np.full((nc, okf.size), 255, np.uint8)
    w = np.flatnonzero(okf)
    for i in range(0, len(w), 2_000_000):
        ii = w[i:i + 2_000_000]; pp = M.predict_proba(flat[ii])
        best = M.classes_[pp.argmax(1)].astype("u1"); mx = pp.max(1)
        u = mx < UNCERTAIN_P; best[u] = 10
        cls[ii] = best; top[ii] = np.round(mx * 100); unc[ii] = u; sc[:, ii] = np.round(pp.T * 100)
    d = OUT / fid / sub; d.mkdir(exist_ok=True)
    base = dict(driver="GTiff", height=g["ny"], width=g["nx"], dtype="uint8", nodata=255, crs=CFG.CRS_METRIC,
                transform=g["transform"], compress="deflate", tiled=True, blockxsize=512, blockysize=512)
    tags = dict(classes=json.dumps(CLASSES), uncertain_rule=f"top probability < {UNCERTAIN_P}", producer="p73_rf20_surface.py",
                meaning="PRE-event surface class from PRE-only S2 (weak WorldCover target); not flood evidence")
    for name, arrs, descs in (
            ("surface_class_20m.tif", [cls], ["p73_class"]),
            ("surface_max_score_20m.tif", [top], ["max_class_probability_x100"]),
            ("surface_uncertain_20m.tif", [unc], ["uncertain (1) / certain (0)"]),
            ("surface_scores_20m.tif", list(sc), [f"prob_x100_{CLASSES[int(c)]}" for c in M.classes_])):
        p_ = d / name
        with rasterio.open(p_.with_suffix(".tif.part"), "w", count=len(arrs), **base) as o:
            for b, (arr, ds) in enumerate(zip(arrs, descs), 1):
                o.write(arr.reshape(g["ny"], g["nx"]), b); o.set_band_description(b, ds)
            o.update_tags(**tags)
        p_.with_suffix(".tif.part").replace(p_)
    v = okf.sum(); rows = []
    for c, n in CLASSES.items():
        k = int((cls[okf] == c).sum())
        rows.append(dict(frame=fid, p73_class=n, km2=round(k * 4e-4, 2), share_pct=round(100 * k / max(v, 1), 2)))
    print(f"{fid} -> {d}: " + ", ".join(f"{r['p73_class']} {r['km2']:.0f} km2" for r in rows if r["km2"]), flush=True)
    return rows


def infer(frames):
    """PURE INFERENCE with the persisted frozen model (e.g. B3). No training, no threshold or configuration choice."""
    import joblib
    b = joblib.load(MODEL)
    rows = []
    for fid in frames:
        g = grid20(fid); X, names, nobs = predictors(fid, g)
        assert names == b["features"], "feature order differs from the frozen model"
        rows += write_products(b["model"], names, fid, g, X, np.all(np.isfinite(X), axis=0) & (nobs >= 5))
    pd.DataFrame(rows).to_csv(CFG.TABLES / f"p73_rf20_class_area_infer_{'_'.join(frames)}.csv", index=False)


if __name__ == "__main__":
    import sys as _s
    if "--infer" in _s.argv:
        infer([f for f in _s.argv[_s.argv.index("--infer") + 1:] if not f.startswith("-")])
    else:
        main()
