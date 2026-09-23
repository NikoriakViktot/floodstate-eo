# New in floodstate-eo, 2026-09-23. STATUS: ACTIVE_DIAGNOSTIC. Reads the frozen U0_B2_CORRECTED run; retrains nothing.
"""P75d -- full-frame inference and failure diagnostics for the frozen U0_B2_CORRECTED model.

NOTHING IS REFITTED OR RE-TUNED. The weights, the TRAIN-only normalisation and the VALIDATION threshold (0.57) are read
from runs/U0_B2_CORRECTED and asserted, never chosen here.

WHAT THE NUMBERS MEAN. Every metric below is AGREEMENT WITH HELD-OUT WEAK REFERENCE LABELS (label contract v001, which
p75 builds from p60 labels x S1 peak water x p69b), not flood-mapping accuracy. BASE_CLASS (p69a) is read ONLY to
stratify the diagnosis; it never touches a prediction or the threshold. The disputed population (S1 peak water that M2
does not claim) stays out of every metric and is reported as MODEL-SUPPORTED DISPUTED CANDIDATES, never as recovered
flood.

STEP 0 IS A REPRODUCTION GATE. The frozen TEST patches are rescored exactly as p75 scored them; the confusion counts
must match runs/U0_B2_CORRECTED/test_metrics.json, or the recovered model/normalisation/labels are not the ones that
produced the frozen numbers and nothing after it is meaningful.

FULL-FRAME SCORES ARE A BLEND, NOT THE TEST PROTOCOL. Sliding 512 windows at stride 256 with a smooth centre weight;
metrics from the full-frame map are reported beside, never instead of, the frozen patch-based TEST numbers.

Outputs: $BULK_ROOT/frames10/B2/u0_b2_score.tif (uint16 score x 10000, nodata 65535)
         $BULK_ROOT/frames10/B2/u0_b2_class_thr057.tif (uint8 1 flood / 0 not / 255 no S1 input)
         runs/U0_B2_CORRECTED/diagnostics/*.csv, *.json, *.png
"""
from __future__ import annotations
import argparse, importlib.util, json, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from scipy import ndimage
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                       # case_studies/kakhovka_2023
RUN = ROOT / "runs" / "U0_B2_CORRECTED"
DIAG = RUN / "diagnostics"
OUT = CFG.BULK_ROOT / "frames10"
FID, PATCH, SCALE, ND = "B2", 512, 100.0, -32768
FROZEN_THR = 0.57
BASE = {0: "PRE_EXISTING_WATER", 1: "VEG_AGRI", 2: "BARE_SAND", 3: "BUILT_UP", 4: "WETLAND", 5: "OTHER_DRY",
        6: "UNCERTAIN_BASE"}
PX_KM2 = 1e-4                                 # 10 m cell
#: "large isolated field component": the agricultural false-water shape this model is suspected of. Declared up front.
ISO_MIN_KM2, ISO_AGRI_SHARE, ISO_MIN_DIST_M = 0.01, 0.8, 500.0


def _p75():
    s = importlib.util.spec_from_file_location("p75", HERE / "p75_u0_b2_full.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def read1(name, band=1):
    with rasterio.open(OUT / FID / name) as s:
        return s.read(band)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--batch", type=int, default=6)
    ap.add_argument("--stride", type=int, default=256); a = ap.parse_args()
    import torch, segmentation_models_pytorch as smp
    P75 = _p75(); DIAG.mkdir(parents=True, exist_ok=True)
    thr = json.loads((RUN / "validation_threshold.json").read_text())["threshold"]
    assert abs(thr - FROZEN_THR) < 1e-9, f"validation threshold {thr} is not the frozen {FROZEN_THR}"
    norm = json.loads((RUN / "normalization.json").read_text())
    F = CG.frame_grid(FID)
    with rasterio.open(OUT / FID / "s1_change.tif") as s:
        CH = list(s.descriptions); X = s.read().astype("f4")
    assert CH == norm["channels"], "s1_change.tif channel order differs from the frozen normalisation"
    nos1 = np.all(X == ND, axis=0)
    X[X == ND] = np.nan
    for i, c in enumerate(CH):
        if not c.startswith("n_"):
            X[i] /= SCALE
    med = np.array(norm["median"], "f4")[:, None, None]; iqr = np.array(norm["iqr"], "f4")[:, None, None]
    X = np.nan_to_num((X - med) / iqr, nan=0.0).astype("f4")

    # ---- labels exactly as p75 builds them (contract v001) ------------------------------------------------------
    lab = read1("labels.tif"); sem = read1("p69b_semantic_state.tif"); bc = read1("p69a_base_class.tif")
    pre_wf = read1("labels.tif", 8).astype("f4")          # p60 band 8: pre-breach S2 water frequency, % (no land cover)
    s1w = P75.s1_peak(F); m2 = np.isin(sem, (1, 2, 3, 4, 5))
    y = np.full((F["ny"], F["nx"]), 255, np.uint8)
    y[lab == 0] = 0; y[(lab == 1) & s1w & m2] = 1
    disputed = s1w & ~m2; y[disputed] = 255
    C = pd.read_csv(RUN / "split_manifest.csv"); half = PATCH // 2

    dev = "cuda"
    net = smp.Unet("resnet34", encoder_weights=None, in_channels=len(CH), classes=1).to(dev)
    net.load_state_dict(torch.load(RUN / "model_best.pt", map_location=dev)); net.eval()

    # ---- STEP 0: reproduce the frozen TEST numbers on the frozen TEST patches ------------------------------------
    te = C[C.split == "test"].reset_index(drop=True)
    S, Y = [], []
    with torch.no_grad(), torch.amp.autocast("cuda"):
        for i in range(0, len(te), a.batch):
            rs = te.iloc[i:i + a.batch]
            xb = np.stack([X[:, r.row - half:r.row + half, r.col - half:r.col + half] for r in rs.itertuples()])
            S.append(torch.sigmoid(net(torch.from_numpy(xb).to(dev)).squeeze(1)).float().cpu().numpy())
            Y.append(np.stack([y[r.row - half:r.row + half, r.col - half:r.col + half] for r in rs.itertuples()]))
    S, Y = np.concatenate(S), np.concatenate(Y); T = Y != 255
    rep = P75.metrics(Y[T], S[T] >= thr)
    frozen = json.loads((RUN / "test_metrics.json").read_text())
    diff = {k: rep[k] - frozen[k] for k in ("TP", "FP", "FN", "TN")}
    repro = dict(reproduced=rep, frozen={k: frozen[k] for k in rep}, count_difference=diff,
                 exact=all(v == 0 for v in diff.values()),
                 max_abs_count_diff_share=max(abs(v) for v in diff.values()) / max(frozen["TP"], 1))
    (DIAG / "reproduction_gate.json").write_text(json.dumps(repro, indent=2))
    print(f"reproduction gate: {'EXACT' if repro['exact'] else 'NOT EXACT'}; count diff {diff}", flush=True)
    if repro["max_abs_count_diff_share"] > 1e-3:
        raise SystemExit("recovered model does not reproduce the frozen TEST confusion within 0.1 % -- stop")

    # ---- full-frame sliding-window inference ---------------------------------------------------------------------
    t0 = time.time()
    w1 = np.hanning(PATCH).astype("f4") + 1e-3; W = np.outer(w1, w1)
    acc = np.zeros((F["ny"], F["nx"]), "f4"); wsum = np.zeros_like(acc)
    rows = sorted(set(list(range(0, F["ny"] - PATCH + 1, a.stride)) + [F["ny"] - PATCH]))
    cols = sorted(set(list(range(0, F["nx"] - PATCH + 1, a.stride)) + [F["nx"] - PATCH]))
    tiles = [(r, c) for r in rows for c in cols]
    with torch.no_grad(), torch.amp.autocast("cuda"):
        for i in range(0, len(tiles), a.batch):
            tb = tiles[i:i + a.batch]
            xb = np.stack([X[:, r:r + PATCH, c:c + PATCH] for r, c in tb])
            sb = torch.sigmoid(net(torch.from_numpy(xb).to(dev)).squeeze(1)).float().cpu().numpy()
            for (r, c), s_ in zip(tb, sb):
                acc[r:r + PATCH, c:c + PATCH] += s_ * W; wsum[r:r + PATCH, c:c + PATCH] += W
    score = acc / np.maximum(wsum, 1e-9); del acc, wsum
    score[nos1] = np.nan
    pred = (score >= thr) & ~nos1
    print(f"full-frame inference: {len(tiles)} tiles in {time.time()-t0:.0f}s", flush=True)
    sp = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=1, crs=CFG.CRS_METRIC, transform=F["transform"],
              compress="deflate", tiled=True, blockxsize=512, blockysize=512)
    q = np.where(np.isfinite(score), np.round(score * 10000), 65535).astype("u2")
    tags = dict(model="U0_B2_CORRECTED model_best.pt", threshold=f"{thr:.2f} (VALIDATION, frozen)",
                blend=f"512 windows, stride {a.stride}, Hann centre weight",
                meaning="score of a SAR-only U-Net trained on weak labels (v001); NOT validated flood probability",
                producer="p75d_u0_inference_diagnostics.py")
    for nm, arr, dt, nd, desc in (("u0_b2_score.tif", q, "uint16", 65535, "u0_score_x10000"),
                                  ("u0_b2_class_thr057.tif", np.where(nos1, 255, pred).astype("u1"), "uint8", 255,
                                   "u0_class_thr057")):
        tmp = OUT / FID / (nm + ".part")
        with rasterio.open(tmp, "w", dtype=dt, nodata=nd, **sp) as d:
            d.write(arr, 1); d.set_band_description(1, desc); d.update_tags(**tags)
        tmp.replace(OUT / FID / nm)
    del q

    # ---- split role per pixel (10 km blocks, same assignment as p75) ---------------------------------------------
    role = np.zeros((F["ny"], F["nx"]), np.uint8)
    for code, sp_ in ((1, "train"), (2, "val"), (3, "test")):
        for r in C[C.split == sp_].itertuples():
            role[r.row - half:r.row + half, r.col - half:r.col + half] = code
    test_px = role == 3
    lbl = y != 255

    # ---- A: pixel metrics on labelled TEST pixels (full-frame map; frozen patch numbers are in reproduction_gate) --
    A = [dict(scope="TEST_patch_protocol_frozen", **{k: frozen[k] for k in ("TP", "FP", "FN", "TN", "precision",
                                                                              "recall", "F1", "IoU")}),
         dict(scope="TEST_fullframe_blend", **P75.metrics(y[test_px & lbl], pred[test_px & lbl]))]
    pd.DataFrame(A).to_csv(DIAG / "A_pixel_metrics.csv", index=False)

    # ---- B: semantic strata (BASE_CLASS for DIAGNOSIS ONLY) ------------------------------------------------------
    B = []
    for code, nm in BASE.items():
        m = test_px & lbl & (bc == code)
        allm = (bc == code) & ~nos1
        row = dict(stratum=nm, test_labelled_km2=round(float(m.sum()) * PX_KM2, 2),
                   predicted_flood_km2_fullframe=round(float((pred & allm).sum()) * PX_KM2, 2))
        if m.sum() >= 1000:
            row.update(P75.metrics(y[m], pred[m]))
        B.append(row)
    pd.DataFrame(B).to_csv(DIAG / "B_strata_test.csv", index=False)

    # ---- C: connected components of the predicted flood ----------------------------------------------------------
    t0 = time.time()
    comp, n = ndimage.label(pred, structure=np.ones((3, 3)))
    objs = ndimage.find_objects(comp)
    prew = pre_wf >= 20.0                                   # p60's own pre-water rule (S2 frequency), no land cover
    dist = ndimage.distance_transform_edt(~prew) * 10.0 if prew.any() else np.full(pred.shape, np.inf, "f4")
    R = []
    for k, sl in enumerate(objs, 1):
        m = comp[sl] == k
        area = int(m.sum())
        pad = np.pad(m, 1)
        perim_px = int((pad[1:, :] != pad[:-1, :]).sum() + (pad[:, 1:] != pad[:, :-1]).sum())
        rr, cc = np.nonzero(m)
        if area >= 3:
            cov = np.cov(np.vstack([rr, cc]).astype("f8"))
            ev_, evec = np.linalg.eigh(cov); ev_ = np.clip(ev_, 1e-9, None)
            elong = float(np.sqrt(ev_[1] / ev_[0]))
            proj = np.vstack([rr, cc]).T @ evec
            ext = (proj.max(0) - proj.min(0) + 1).prod()
            rect = float(area / ext) if ext > 0 else np.nan
        else:
            elong, rect = 1.0, np.nan
        sub = lambda arr: arr[sl][m]
        yy, bb, rl = sub(y), sub(bc), sub(role)
        bvals, bcnt = np.unique(bb, return_counts=True)
        dom = int(bvals[np.argmax(bcnt)])
        R.append(dict(component=k, area_px=area, area_km2=area * PX_KM2, perimeter_m=perim_px * 10.0,
                      bbox_row0=sl[0].start, bbox_col0=sl[1].start, bbox_rows=sl[0].stop - sl[0].start,
                      bbox_cols=sl[1].stop - sl[1].start, elongation=round(elong, 3),
                      compactness=round(4 * np.pi * area / max(perim_px, 1) ** 2, 4),
                      rectangularity_pca=round(rect, 4) if np.isfinite(rect) else None,
                      min_dist_to_prewater_m=float(sub(dist).min()),
                      px_label_flood=int((yy == 1).sum()), px_label_nonflood=int((yy == 0).sum()),
                      px_disputed=int(sub(disputed).sum()),
                      dominant_base_class=BASE.get(dom, str(dom)),
                      share_veg_agri=float((bb == 1).mean()), share_wetland=float((bb == 4).mean()),
                      split=("test" if (rl == 3).mean() > 0.5 else "val" if (rl == 2).mean() > 0.5
                             else "train" if (rl == 1).mean() > 0.5 else "outside_patches")))
    K = pd.DataFrame(R); K.to_csv(DIAG / "C_components.csv", index=False)
    print(f"{n} predicted components in {time.time()-t0:.0f}s", flush=True)

    # ---- D: agricultural false water -----------------------------------------------------------------------------
    ag = bc == 1
    iso = K[(K.area_km2 >= ISO_MIN_KM2) & (K.share_veg_agri >= ISO_AGRI_SHARE) & (K.px_label_flood == 0)
            & (K.min_dist_to_prewater_m > ISO_MIN_DIST_M)]
    agK = K[K.dominant_base_class == "VEG_AGRI"]
    D = dict(veg_agri_predicted_flood_km2=round(float((pred & ag).sum()) * PX_KM2, 2),
             test_veg_agri_TP_km2=round(float((pred & ag & test_px & (y == 1)).sum()) * PX_KM2, 3),
             test_veg_agri_FP_km2=round(float((pred & ag & test_px & (y == 0)).sum()) * PX_KM2, 3),
             all_labelled_veg_agri_TP_km2=round(float((pred & ag & (y == 1)).sum()) * PX_KM2, 3),
             all_labelled_veg_agri_FP_km2=round(float((pred & ag & (y == 0)).sum()) * PX_KM2, 3),
             n_components_dominant_veg_agri=int(len(agK)),
             median_component_km2_dominant_veg_agri=float(agK.area_km2.median()) if len(agK) else None,
             isolated_field_rule=f"area >= {ISO_MIN_KM2} km2, VEG_AGRI share >= {ISO_AGRI_SHARE}, no labelled FLOOD "
                                 f"pixel, min distance to pre-water (p60 S2 freq >= 20 %) > {ISO_MIN_DIST_M} m",
             n_isolated_field_components=int(len(iso)),
             isolated_field_km2=round(float(iso.area_km2.sum()), 3),
             isolated_field_median_rectangularity=float(iso.rectangularity_pca.median()) if len(iso) else None,
             isolated_field_by_split=iso.split.value_counts().to_dict())
    (DIAG / "D_agriculture_false_water.json").write_text(json.dumps(D, indent=2, default=str))

    # ---- E: delta / wetland --------------------------------------------------------------------------------------
    wm = bc == 4
    wK = K[K.dominant_base_class == "WETLAND"].sort_values("area_km2", ascending=False)
    E = dict(test=P75.metrics(y[test_px & lbl & wm], pred[test_px & lbl & wm]),
             predicted_flood_km2_fullframe=round(float((pred & wm).sum()) * PX_KM2, 2),
             n_components_dominant_wetland=int(len(wK)),
             largest_component_share_of_wetland_dominant_area=float(wK.area_km2.iloc[0] / wK.area_km2.sum())
             if len(wK) else None)
    (DIAG / "E_wetland.json").write_text(json.dumps(E, indent=2))

    # ---- F: disputed -- MODEL-SUPPORTED DISPUTED CANDIDATES ------------------------------------------------------
    v = score[disputed & np.isfinite(score)]
    hist, edges = np.histogram(v, bins=20, range=(0, 1))
    dc, dn = ndimage.label(pred & disputed, structure=np.ones((3, 3)))
    dsz = np.bincount(dc.ravel())[1:] * PX_KM2 if dn else np.array([])
    Fd = dict(name="MODEL-SUPPORTED DISPUTED CANDIDATES (never supervised; not recovered flood)",
              disputed_km2=round(float(disputed.sum()) * PX_KM2, 2),
              score_quantiles={q_: round(float(np.quantile(v, q_ / 100)), 4) for q_ in (10, 25, 50, 75, 90)},
              area_ge_thr_km2=round(float((v >= thr).sum()) * PX_KM2, 2),
              share_ge_thr=round(float((v >= thr).mean()), 4),
              histogram=dict(edges=edges.round(2).tolist(), counts=hist.tolist()),
              n_components=int(dn), component_km2_quantiles={q_: round(float(np.quantile(dsz, q_ / 100)), 4)
                                                             for q_ in (50, 90, 99)} if dn else None,
              by_split={nm: round(float((pred & disputed & (role == c)).sum()) * PX_KM2, 2)
                        for c, nm in ((1, "train"), (2, "val"), (3, "test"), (0, "outside_patches"))})
    (DIAG / "F_disputed_candidates.json").write_text(json.dumps(Fd, indent=2))

    # ---- maps ----------------------------------------------------------------------------------------------------
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    st = 4
    fig, ax = plt.subplots(1, 3, figsize=(18, 12))
    ax[0].imshow(score[::st, ::st], vmin=0, vmax=1, cmap="viridis"); ax[0].set_title("U0 score (B2)")
    ov = np.zeros(pred[::st, ::st].shape + (3,), "f4")
    ov[..., 0] = (pred & ag)[::st, ::st]; ov[..., 2] = (pred & wm)[::st, ::st]; ov[..., 1] = (pred & ~ag & ~wm)[::st, ::st]
    ax[1].imshow(ov); ax[1].set_title(f"pred >= {thr:.2f}: red VEG_AGRI, blue WETLAND, green other")
    dd = np.zeros_like(ov); dd[..., 0] = (disputed & pred)[::st, ::st]; dd[..., 2] = (disputed & ~pred)[::st, ::st]
    ax[2].imshow(dd); ax[2].set_title("disputed: red model-supported candidate, blue not")
    for x_ in ax:
        x_.set_axis_off()
    fig.tight_layout(); fig.savefig(DIAG / "maps_overview.png", dpi=110); plt.close(fig)
    print(json.dumps(dict(A=A, D={k: D[k] for k in list(D)[:9]}, E=E["test"], F_share=Fd["share_ge_thr"]),
                     indent=1, default=str))
    print(f"-> {DIAG.relative_to(ROOT)}/ and {OUT / FID}/u0_b2_*.tif")


if __name__ == "__main__":
    main()
