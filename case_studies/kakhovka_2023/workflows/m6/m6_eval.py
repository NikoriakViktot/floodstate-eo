# New in floodstate-eo, 2026-09-23. STATUS: ACTIVE. The ONE evaluation harness for every M6 arm (D1 final design).
"""m6_eval -- D1 evaluation on the frozen m6_split_v1 TEST (or VALIDATION) geography.

Every number is AGREEMENT WITH HELD-OUT WEAK REFERENCE LABELS (m6_labels_v002), not flood-mapping accuracy.
Strata come from the frozen p73 RF20 surface class (2x2-replicated to 10 m); p73 never touches a label or a
prediction here. Pixels are counted once (overlap owned by B2), buffer pixels never count, and pixels with no S1
event are unavailable.

PRIMARY A  dry-CROPLAND false flood: FP km2, FP rate, FP components, large isolated field-like components
PRIMARY B  flooded OPEN_LOW_VEGETATION (CROPLAND u GRASS_LOW_VEGETATION): recall, IoU, FN km2, component recovery
SECONDARY  flooded CROPLAND only (LOW-N): recall, FN km2, reference / recovered components
OTHER      WETLAND_REED P/R/IoU + fragmentation; BUILT_UP FP km2 + precision; BARE_SAND FP km2; global F1/IoU/PR-AUC

Per-block counts are written for every endpoint, so any two arms can be compared with a PAIRED spatial-block
bootstrap on identical blocks (`paired_bootstrap`).
"""
from __future__ import annotations
import numpy as np, pandas as pd
from scipy import ndimage

PX_KM2 = 1e-4
CROP, GRASS, WET, BUILT, BARE = 2, 3, 6, 7, 8
ISO_MIN_KM2, ISO_CROP_SHARE = 0.01, 0.8          # large isolated field-like FP component (declared before any run)
RECOVER_FRAC = 0.5                               # a reference component is recovered if >= 50 % of it is predicted
EIGHT = np.ones((3, 3), bool)


def _m(tp, fp, fn):
    P = tp / max(tp + fp, 1); R = tp / max(tp + fn, 1)
    return dict(TP=int(tp), FP=int(fp), FN=int(fn), precision=round(P, 4), recall=round(R, 4),
                F1=round(2 * P * R / max(P + R, 1e-9), 4), IoU=round(tp / max(tp + fp + fn, 1), 4))


def evaluate_frame(pred, score, y, p73, role_mask, blk):
    """Counts for one frame. `role_mask` selects the evaluated geography (e.g. role == 3), already owned/non-buffer;
    y: 1 FLOOD, 0 NON_FLOOD, 255 unavailable. Returns (row dict, per-block DataFrame, pooled score/label sample)."""
    lab = role_mask & (y != 255)
    fl, dr = lab & (y == 1), lab & (y == 0)
    olv = np.isin(p73, (CROP, GRASS))
    S = dict(
        A_dry_crop=dr & (p73 == CROP), B_flood_olv=fl & olv, B_dry_olv=dr & olv, C_flood_crop=fl & (p73 == CROP),
        W_flood=fl & (p73 == WET), W_dry=dr & (p73 == WET), BU_dry=dr & (p73 == BUILT), BU_flood=fl & (p73 == BUILT),
        BS_dry=dr & (p73 == BARE), G_flood=fl, G_dry=dr)
    r = {}
    for k, m in S.items():
        r[f"{k}_px"] = int(m.sum()); r[f"{k}_pred_px"] = int((pred & m).sum())
    # primary A components (FP on dry cropland) and large isolated field-like components in the evaluated geography
    fpc, nfp = ndimage.label(pred & S["A_dry_crop"], structure=EIGHT)
    r["A_n_fp_components"] = int(nfp)
    comp, n = ndimage.label(pred & role_mask, structure=EIGHT)
    iso_px = n_iso = 0
    if n:
        idx = np.arange(1, n + 1)
        area = ndimage.sum(np.ones_like(comp), comp, idx)
        crop = ndimage.sum((p73 == CROP).astype("f4"), comp, idx)
        hasfl = ndimage.maximum(fl.astype("u1"), comp, idx)
        sel = (area * PX_KM2 >= ISO_MIN_KM2) & (crop / np.maximum(area, 1) >= ISO_CROP_SHARE) & (hasfl == 0)
        n_iso, iso_px = int(sel.sum()), int(area[sel].sum())
    r["A_n_isolated_field_components"], r["A_isolated_field_px"] = n_iso, iso_px
    # component recovery for primary B and secondary C
    for key, ref in (("B", S["B_flood_olv"]), ("C", S["C_flood_crop"])):
        rc, rn = ndimage.label(ref, structure=EIGHT)
        if rn:
            idx = np.arange(1, rn + 1)
            frac = ndimage.mean(pred.astype("f4"), rc, idx)
            r[f"{key}_n_ref_components"], r[f"{key}_n_recovered"] = int(rn), int((frac >= RECOVER_FRAC).sum())
        else:
            r[f"{key}_n_ref_components"] = r[f"{key}_n_recovered"] = 0
    # wetland fragmentation of the prediction inside the WETLAND_REED stratum
    wc, wn = ndimage.label(pred & role_mask & (p73 == WET), structure=EIGHT)
    r["W_pred_components"] = int(wn)
    r["W_largest_component_share"] = float(np.bincount(wc.ravel())[1:].max() / max((wc > 0).sum(), 1)) if wn else None
    # per-block table (every count needed to recompute any endpoint on a resampled set of blocks)
    rows = []
    for b in np.unique(blk[role_mask]):
        mb = blk == b
        d = dict(block=int(b))
        for k, m in S.items():
            d[f"{k}_px"] = int((m & mb).sum()); d[f"{k}_pred_px"] = int((pred & m & mb).sum())
        rows.append(d)
    samp = np.flatnonzero(lab.ravel())
    return r, pd.DataFrame(rows), (score.ravel()[samp], (y.ravel()[samp] == 1))


def endpoints(c):
    """D1 endpoints from summed counts (a dict or a Series with the *_px / *_pred_px keys)."""
    g = lambda k: float(c[k])
    A_fp = g("A_dry_crop_pred_px")
    B = _m(g("B_flood_olv_pred_px"), g("B_dry_olv_pred_px"), g("B_flood_olv_px") - g("B_flood_olv_pred_px"))
    C = _m(g("C_flood_crop_pred_px"), 0, g("C_flood_crop_px") - g("C_flood_crop_pred_px"))
    W = _m(g("W_flood_pred_px"), g("W_dry_pred_px"), g("W_flood_px") - g("W_flood_pred_px"))
    G = _m(g("G_flood_pred_px"), g("G_dry_pred_px"), g("G_flood_px") - g("G_flood_pred_px"))
    return dict(
        A_FP_area_dry_cropland_km2=round(A_fp * PX_KM2, 4),
        A_FP_rate_dry_cropland=round(A_fp / max(g("A_dry_crop_px"), 1), 6),
        A_evaluated_dry_cropland_km2=round(g("A_dry_crop_px") * PX_KM2, 2),
        B_recall_flooded_open_low_veg=B["recall"], B_IoU_open_low_veg=B["IoU"],
        B_FN_area_km2=round(B["FN"] * PX_KM2, 4), B_reference_km2=round(g("B_flood_olv_px") * PX_KM2, 3),
        C_recall_flooded_cropland_LOWN=C["recall"], C_FN_area_km2=round(C["FN"] * PX_KM2, 4),
        C_reference_km2=round(g("C_flood_crop_px") * PX_KM2, 3),
        W_precision=W["precision"], W_recall=W["recall"], W_IoU=W["IoU"],
        BU_FP_area_km2=round(g("BU_dry_pred_px") * PX_KM2, 4),
        BU_precision=_m(g("BU_flood_pred_px"), g("BU_dry_pred_px"), 0)["precision"] if g("BU_flood_px") else None,
        BS_FP_area_km2=round(g("BS_dry_pred_px") * PX_KM2, 4),
        G_F1=G["F1"], G_IoU=G["IoU"], G_precision=G["precision"], G_recall=G["recall"])


def bootstrap(blocks: pd.DataFrame, n=2000, seed=20260923):
    """Spatial-block bootstrap CI (2.5/97.5 %) of every endpoint for ONE arm."""
    rng = np.random.default_rng(seed); cols = [c for c in blocks.columns if c.endswith("_px")]
    B = blocks[cols].to_numpy(); out = []
    for _ in range(n):
        s = B[rng.integers(0, len(B), len(B))].sum(0)
        out.append(endpoints(dict(zip(cols, s))))
    D = pd.DataFrame(out)
    return pd.DataFrame(dict(lo=D.quantile(0.025, numeric_only=True), hi=D.quantile(0.975, numeric_only=True)))


def paired_bootstrap(blocks_a: pd.DataFrame, blocks_b: pd.DataFrame, n=2000, seed=20260923):
    """Arm B minus arm A on IDENTICAL resampled physical blocks (same frozen split). Covers D1 + amendment (A1/A2).
    Blocks cut by the B1/B2 ownership line are summed across frames first: one physical resampling unit."""
    a = blocks_a.drop(columns=["frame"]).groupby("block").sum().sort_index()
    b = blocks_b.drop(columns=["frame"]).groupby("block").sum().sort_index()
    assert a.index.equals(b.index), "arms were not evaluated on identical blocks"
    cols = [c for c in a.columns if c.endswith("_px")]
    A, Bm = a[cols].to_numpy(), b[cols].to_numpy(); rng = np.random.default_rng(seed); out = []
    full = lambda s: {**endpoints(s), **(a2_endpoints(s) if "A2_ignore_crop_px" in s else {})}
    for _ in range(n):
        i = rng.integers(0, len(A), len(A))
        ea, eb = full(dict(zip(cols, A[i].sum(0)))), full(dict(zip(cols, Bm[i].sum(0))))
        out.append({k: (eb[k] - ea[k]) for k in ea if isinstance(ea[k], (int, float)) and isinstance(eb[k], (int, float))})
    D = pd.DataFrame(out)
    return pd.DataFrame(dict(median=D.median(), lo=D.quantile(0.025), hi=D.quantile(0.975)))


# =====================================================================================================================
# D1 AMENDMENT (maintainer, 2026-09-24): endpoint A is split into A1 (supervised) and A2 (challenge / diagnostic).
# A1 is unchanged: CROPLAND x v002 NON_FLOOD -- confirmed disagreement with the weak dry reference.
# A2 = CROPLAND x v002 != FLOOD, ALWAYS reported separately for NON_FLOOD and IGNORE. Predictions on IGNORE are NOT
#      false positives (unknown != dry); they are "PREDICTED FLOOD BURDEN ON UNLABELLED CROPLAND" / "UNRESOLVED
#      CROPLAND CANDIDATE AREA". A2 also carries a threshold curve so that a change between arms can be told apart
#      from a small shift of the operating point.
# =====================================================================================================================
A2_CURVE = np.round(np.arange(0.30, 0.91, 0.05), 2)
SIZE_BINS_KM2 = [0.01, 0.05, 0.1, 0.5, 1.0, np.inf]


def _isolated(pred, geo, p73, fl):
    """Large isolated field-like components of `pred` inside `geo` (rule declared at module top). Returns label image
    and a boolean per component id (index 0 unused)."""
    comp, n = ndimage.label(pred & geo, structure=EIGHT)
    if not n:
        return comp, np.zeros(1, bool), np.zeros(1)
    idx = np.arange(1, n + 1)
    area = ndimage.sum(np.ones_like(comp), comp, idx)
    crop = ndimage.sum((p73 == CROP).astype("f4"), comp, idx)
    hasfl = ndimage.maximum(fl.astype("u1"), comp, idx)
    sel = (area * PX_KM2 >= ISO_MIN_KM2) & (crop / np.maximum(area, 1) >= ISO_CROP_SHARE) & (hasfl == 0)
    return comp, np.concatenate([[False], sel]), np.concatenate([[0], area])


def a1_a2_frame(score, thr, y, p73, geo, blk):
    """A1 additions + A2 for one frame on geography `geo` (test, owned, has_event)."""
    crop = geo & (p73 == CROP)
    nf, ig, fl = crop & (y == 0), crop & (y == 255), geo & (y == 1)
    pred = geo & (score >= thr)
    comp, sel, area = _isolated(pred, geo, p73, fl)
    iso = sel[comp]
    r = dict(A1_isolated_field_FP_px=int((iso & nf).sum()),
             A2_nonflood_crop_px=int(nf.sum()), A2_ignore_crop_px=int(ig.sum()),
             A2_pred_nonflood_crop_px=int((pred & nf).sum()), A2_pred_ignore_crop_px=int((pred & ig).sum()),
             A2_isolated_nonflood_px=int((iso & nf).sum()), A2_isolated_ignore_px=int((iso & ig).sum()),
             A2_isolated_total_px=int(iso.sum()), A2_n_isolated_components=int(sel.sum()))
    sizes = area[sel] * PX_KM2
    hist = np.histogram(sizes, bins=SIZE_BINS_KM2)[0] if len(sizes) else np.zeros(len(SIZE_BINS_KM2) - 1, int)
    r.update({f"A2_isolated_size_{SIZE_BINS_KM2[i]}_{SIZE_BINS_KM2[i + 1]}_km2_n": int(h) for i, h in enumerate(hist)})
    for nm, m in (("nonflood", nf), ("ignore", ig)):
        v = score[m]
        for q in (50, 75, 90, 99):
            r[f"A2_score_p{q}_{nm}"] = round(float(np.quantile(v, q / 100)), 4) if v.size else None
    curve = []
    for t in sorted(set(A2_CURVE.tolist() + [round(thr, 2)])):
        pt = geo & (score >= t)
        c_, s_, _ = _isolated(pt, geo, p73, fl)
        it = s_[c_]
        curve.append(dict(threshold=t, is_frozen=abs(t - thr) < 1e-9,
                          pred_nonflood_crop_px=int((pt & nf).sum()), pred_ignore_crop_px=int((pt & ig).sum()),
                          isolated_total_px=int(it.sum()), isolated_ignore_px=int((it & ig).sum())))
    rows = []
    for b in np.unique(blk[geo]):
        mb = blk == b
        rows.append(dict(block=int(b), A1_isolated_field_FP_px=int((iso & nf & mb).sum()),
                         A2_nonflood_crop_px=int((nf & mb).sum()), A2_ignore_crop_px=int((ig & mb).sum()),
                         A2_pred_nonflood_crop_px=int((pred & nf & mb).sum()),
                         A2_pred_ignore_crop_px=int((pred & ig & mb).sum()),
                         A2_isolated_total_px=int((iso & mb).sum()), A2_isolated_ignore_px=int((iso & ig & mb).sum())))
    return r, pd.DataFrame(rows), pd.DataFrame(curve)


def a2_endpoints(c):
    g = lambda k: float(c[k])
    return dict(
        A1_isolated_field_FP_km2=round(g("A1_isolated_field_FP_px") * PX_KM2, 4),
        A2_pred_flood_on_nonflood_cropland_km2=round(g("A2_pred_nonflood_crop_px") * PX_KM2, 4),
        A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2=round(g("A2_pred_ignore_crop_px") * PX_KM2, 4),
        A2_unlabelled_cropland_evaluated_km2=round(g("A2_ignore_crop_px") * PX_KM2, 2),
        A2_frac_unlabelled_cropland_above_thr=round(g("A2_pred_ignore_crop_px") / max(g("A2_ignore_crop_px"), 1), 5),
        A2_frac_nonflood_cropland_above_thr=round(g("A2_pred_nonflood_crop_px") / max(g("A2_nonflood_crop_px"), 1), 5),
        A2_isolated_field_like_km2=round(g("A2_isolated_total_px") * PX_KM2, 4),
        A2_isolated_field_like_on_unlabelled_km2=round(g("A2_isolated_ignore_px") * PX_KM2, 4))


def evaluate_arm(run_dir, arm, D, thr, out_name="eval_d1a", n_boot=2000):
    """Full D1 + amendment evaluation of one arm from its full-frame scores. D[f] needs score, y, p73, role, has, blk.
    Writes run_dir/out_name/{endpoints.csv, endpoints_ci.csv, by_frame.csv, blocks.csv, a2_curve.csv}."""
    from sklearn.metrics import average_precision_score
    od = run_dir / out_name; od.mkdir(exist_ok=True)
    rows, blocks, curves, ss, yy = [], [], [], [], []
    for f, d in D.items():
        geo = (d["role"] == 3) & d["has"]
        sc = np.nan_to_num(d["score"], nan=-1.0)
        pred = geo & (sc >= thr)
        r, b, (s_, y_) = evaluate_frame(pred, sc, d["y"], d["p73"], geo, d["blk"])
        r2, b2, cv = a1_a2_frame(sc, thr, d["y"], d["p73"], geo, d["blk"])
        b = b.merge(b2, on="block"); b.insert(0, "frame", f); blocks.append(b)
        cv.insert(0, "frame", f); curves.append(cv)
        rows.append(dict(frame=f, **r, **r2,
                         B_n_contributing_blocks=int((b.B_flood_olv_px > 0).sum()))); ss.append(s_); yy.append(y_)
    R = pd.DataFrame(rows); Bt = pd.concat(blocks, ignore_index=True)
    Bt.to_csv(od / "blocks.csv", index=False)
    Cv = pd.concat(curves, ignore_index=True)
    Cs = Cv.groupby(["threshold", "is_frozen"], as_index=False)[[c for c in Cv.columns if c.endswith("_px")]].sum()
    for c in [c for c in Cs.columns if c.endswith("_px")]:
        Cs[c.replace("_px", "_km2")] = (Cs[c] * PX_KM2).round(4)
    Cs.insert(0, "frame", "ALL"); Cv2 = Cv.copy()
    for c in [c for c in Cv2.columns if c.endswith("_px")]:
        Cv2[c.replace("_px", "_km2")] = (Cv2[c] * PX_KM2).round(4)
    pd.concat([Cv2, Cs], ignore_index=True).to_csv(od / "a2_curve.csv", index=False)
    tot = R[[c for c in R.columns if c.endswith("_px")]].sum()
    ep = {**endpoints(tot), **a2_endpoints(tot)}
    ep.update(A1_n_fp_components=int(R.A_n_fp_components.sum()),
              A2_n_isolated_field_like_components=int(R.A2_n_isolated_components.sum()),
              B_n_ref_components=int(R.B_n_ref_components.sum()), B_n_recovered=int(R.B_n_recovered.sum()),
              B_n_contributing_test_blocks=int((Bt.groupby("block").B_flood_olv_px.sum() > 0).sum()),
              B_status="PRIMARY SCIENTIFIC ENDPOINT, LOW EFFECTIVE SPATIAL SAMPLE SIZE",
              C_n_ref_components_LOWN=int(R.C_n_ref_components.sum()), C_n_recovered_LOWN=int(R.C_n_recovered.sum()),
              W_pred_components=int(R.W_pred_components.sum()),
              G_PR_AUC=round(float(average_precision_score(np.concatenate(yy), np.concatenate(ss))), 4),
              threshold=thr, arm=arm)
    pd.Series(ep).to_csv(od / "endpoints.csv", header=["value"])
    size_cols = [c for c in R.columns if c.startswith("A2_isolated_size_")]
    byf = pd.DataFrame([dict(frame=r_["frame"], **endpoints(r_), **a2_endpoints(r_),
                             B_n_contributing_blocks=r_["B_n_contributing_blocks"],
                             B_n_ref_components=r_["B_n_ref_components"], B_n_recovered=r_["B_n_recovered"],
                             W_largest_component_share=r_["W_largest_component_share"],
                             **{c: r_[c] for c in size_cols},
                             **{c: r_[c] for c in R.columns if c.startswith("A2_score_")}) for r_ in rows])
    byf.to_csv(od / "by_frame.csv", index=False)
    Bb = Bt.drop(columns=["frame"]).groupby("block").sum()
    cols = [c for c in Bb.columns if c.endswith("_px")]
    rng = np.random.default_rng(20260923); M = Bb[cols].to_numpy(); out = []
    for _ in range(n_boot):
        s = dict(zip(cols, M[rng.integers(0, len(M), len(M))].sum(0)))
        out.append({**endpoints(s), **a2_endpoints(s)})
    Dd = pd.DataFrame(out)
    pd.DataFrame(dict(lo=Dd.quantile(0.025, numeric_only=True), hi=Dd.quantile(0.975, numeric_only=True))).to_csv(
        od / "endpoints_ci.csv")
    return ep, byf, Cs
