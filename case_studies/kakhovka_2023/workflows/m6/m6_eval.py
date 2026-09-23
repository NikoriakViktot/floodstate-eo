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
    """Arm B minus arm A on IDENTICAL resampled blocks (both must come from the same frozen split)."""
    key = ["frame", "block"]
    a = blocks_a.set_index(key).sort_index(); b = blocks_b.set_index(key).sort_index()
    assert a.index.equals(b.index), "arms were not evaluated on identical blocks"
    cols = [c for c in a.columns if c.endswith("_px")]
    A, Bm = a[cols].to_numpy(), b[cols].to_numpy(); rng = np.random.default_rng(seed); out = []
    for _ in range(n):
        i = rng.integers(0, len(A), len(A))
        ea, eb = endpoints(dict(zip(cols, A[i].sum(0)))), endpoints(dict(zip(cols, Bm[i].sum(0))))
        out.append({k: (eb[k] - ea[k]) for k in ea if isinstance(ea[k], (int, float)) and isinstance(eb[k], (int, float))})
    D = pd.DataFrame(out)
    return pd.DataFrame(dict(median=D.median(), lo=D.quantile(0.025), hi=D.quantile(0.975)))
