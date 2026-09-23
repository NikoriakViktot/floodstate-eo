# New in floodstate-eo, 2026-09-23. STATUS: ACTIVE. One trainer for every M6 arm on the frozen m6_split_v1.
"""P86 -- train and evaluate one M6 arm (U0d, U0z, U1, ...) on B1+B2, frozen geography, D1 harness.

ARMS differ ONLY in their input channels (ARMS below). Everything else is identical and inherited from the frozen
p75 recipe: U-Net resnet34 from scratch, masked BCE + Dice, 60 epochs x 64 weighted patch draws, batch 6, AdamW 3e-4,
flips, seed 20260923.

- Geography, patches and ownership: m6_split_v1 (p84), read, never re-derived. Loss sees only owned, labelled pixels
  with >= 1 S1 event; everything else is IGNORE.
- Unavailable is not zero: where an S1 channel is nodata (no event, B1 west strip) the normalised value is set to 0
  AND an explicit `has_event` channel says so, so the network can tell "median change" from "not observed".
- Normalisation (median / IQR) from TRAIN patch pixels only.
- Model selection by validation-patch F1@0.5 (as p75). Threshold: max F1 on ALL owned, labelled VALIDATION pixels of
  the full-frame blended score (unique pixels). TEST is evaluated once, after the threshold is written to disk.
- A run directory is immutable: re-running an existing arm refuses, so TEST cannot be looked at twice by accident.

Outputs: runs/<ARM>_B1B2_v1/{config.json, normalization.json, training_history.csv, validation_threshold.json,
         test_endpoints.csv, test_endpoints_ci.csv, test_by_frame.csv, test_blocks.csv, model_best.pt, model_last.pt}
         $BULK_ROOT/frames10/<F>/m6/<ARM>_score.tif (uint16 x10000, nodata 65535)
"""
from __future__ import annotations
import argparse, importlib.util, json, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = CFG.BULK_ROOT / "frames10"
SPLIT = "m6_split_v1"
FRAMES = ("B1", "B2")
PATCH, SCALE, ND, SEED = 512, 100.0, -32768, 20260923
D_CH = ["d_vv_min", "d_vh_min", "d_vv_max", "d_vh_max", "d_vv_mean", "d_vh_mean", "d_vvvh_min", "d_vvvh_max"]
SUPPORT = ["n_valid_pre_matched", "n_valid_event", "n_orbits_event"]
ARMS = {
    "U0d": dict(s1=D_CH + SUPPORT, p73=False,
                note="S1 d_* + support + has_event. NO z_*, NO p73, NO HAND, NO S2, NO TRACE."),
    "U0z": dict(s1=D_CH + ["z_vv_min", "z_vh_min", "z_vv_max", "z_vh_max"] + SUPPORT, p73=False,
                note="U0d + robust z_* (domain-shift ablation)."),
}


def _load(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def read(fid, name, band=None):
    with rasterio.open(OUT / fid / name) as s:
        return s.read(band) if band else s.read(), list(s.descriptions)


def frame_tensor(fid, arm):
    with rasterio.open(OUT / fid / "s1_change.tif") as s:
        desc = list(s.descriptions)
        idx = [desc.index(c) + 1 for c in ARMS[arm]["s1"]]
        X = s.read(idx).astype("f4")
    has = (X[ARMS[arm]["s1"].index("n_valid_event")] > 0) & (X[0] != ND)
    X[X == ND] = np.nan
    for i, c in enumerate(ARMS[arm]["s1"]):
        if not c.startswith("n_"):
            X[i] /= SCALE
    return X, has


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--epochs", type=int, default=60); ap.add_argument("--batch", type=int, default=6)
    ap.add_argument("--lr", type=float, default=3e-4); ap.add_argument("--stride", type=int, default=256)
    ap.add_argument("--smoke", action="store_true", help="pipeline check: separate dir, stops BEFORE test is read")
    a = ap.parse_args()
    import torch, torch.nn as nn, segmentation_models_pytorch as smp
    E = _load("m6_eval"); P84 = _load("p84_m6_split_b1b2")
    RUN = ROOT / "runs" / (f"_smoke_{a.arm}" if a.smoke else f"{a.arm}_B1B2_v1")
    if a.smoke and RUN.exists():
        import shutil; shutil.rmtree(RUN)
    if RUN.exists():
        raise SystemExit(f"{RUN} exists -- a run directory is immutable (TEST must not be evaluated twice)")
    RUN.mkdir(parents=True)
    rng = np.random.default_rng(SEED); torch.manual_seed(SEED)
    man = json.loads((CFG.TABLES / f"{SPLIT}_manifest.json").read_text())
    C = pd.read_csv(CFG.TABLES / f"{SPLIT}_patches.csv")
    D = {}
    for f in FRAMES:
        F = CG.frame_grid(f)
        X, has = frame_tensor(f, a.arm)
        role, _ = read(f, f"{SPLIT}_role.tif", 1)
        y, _ = read(f, "m6_labels_v002.tif", 1)
        y = np.where(np.isin(role, (1, 2, 3)) & has, y, 255).astype(np.uint8)
        p73 = P84.p73_10m(f, F)
        gx = F["transform"].c + 10.0 * np.arange(F["nx"]); gy = F["transform"].f - 10.0 * np.arange(F["ny"])
        blk = np.floor(gy / P84.BLOCK_M).astype("i8")[:, None] * 100000 + np.floor(gx / P84.BLOCK_M).astype("i8")[None, :]
        D[f] = dict(F=F, X=X, has=has, role=role, y=y, p73=p73, blk=blk)
    half = PATCH // 2

    # ---- normalisation from TRAIN patch pixels only -------------------------------------------------------------
    samp = []
    for f in FRAMES:
        tr = C[(C.frame == f) & (C.split == "train")]
        m = np.zeros(D[f]["role"].shape, bool)
        for q in tr.itertuples():
            m[q.row - half:q.row + half, q.col - half:q.col + half] = True
        rr, cc = np.nonzero(m & D[f]["has"])
        k = rng.choice(len(rr), size=min(1_000_000, len(rr)), replace=False)
        samp.append(D[f]["X"][:, rr[k], cc[k]])
    samp = np.concatenate(samp, 1)
    med = np.nanmedian(samp, 1)[:, None, None]
    iqr = (np.nanpercentile(samp, 75, 1) - np.nanpercentile(samp, 25, 1))[:, None, None]; iqr[iqr < 1e-6] = 1.0
    del samp
    for f in FRAMES:
        Z = np.nan_to_num((D[f]["X"] - med) / iqr, nan=0.0).astype("f4")
        D[f]["X"] = np.concatenate([Z, D[f]["has"][None].astype("f4")], 0)
    chans = ARMS[a.arm]["s1"] + ["has_event"]
    json.dump(dict(channels=chans, median=med.ravel().tolist(), iqr=iqr.ravel().tolist(),
                   source="TRAIN patch pixels with an S1 event, both frames, 1M-pixel sample per frame",
                   has_event="appended unnormalised (1 = >= 1 S1 event observed)"),
              open(RUN / "normalization.json", "w"), indent=2)

    def batch(df, idx):
        xs = np.stack([D[df.iloc[i].frame]["X"][:, df.iloc[i].row - half:df.iloc[i].row + half,
                                                 df.iloc[i].col - half:df.iloc[i].col + half] for i in idx])
        ys = np.stack([D[df.iloc[i].frame]["y"][df.iloc[i].row - half:df.iloc[i].row + half,
                                                df.iloc[i].col - half:df.iloc[i].col + half] for i in idx])
        return xs, ys
    tr_df = C[C.split == "train"].reset_index(drop=True); va_df = C[C.split == "val"].reset_index(drop=True)
    w = np.where(tr_df.flood_px.values > 0, 4.0, 1.0); w /= w.sum()

    dev = "cuda"
    net = smp.Unet("resnet34", encoder_weights=None, in_channels=len(chans), classes=1).to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr)
    scaler = torch.amp.GradScaler("cuda"); bce = nn.BCEWithLogitsLoss(reduction="none")
    hist, best, t0 = [], -1.0, time.time()
    for ep in range(a.epochs):
        net.train(); idx = rng.choice(len(tr_df), size=min(len(tr_df), 64), replace=True, p=w); tot = nb = 0
        for i in range(0, len(idx), a.batch):
            xnp, ynp = batch(tr_df, idx[i:i + a.batch])
            xb = torch.from_numpy(xnp).to(dev); yb = torch.from_numpy(ynp.astype("i8")).to(dev)
            if rng.random() < 0.5:
                xb = torch.flip(xb, [-1]); yb = torch.flip(yb, [-1])
            if rng.random() < 0.5:
                xb = torch.flip(xb, [-2]); yb = torch.flip(yb, [-2])
            v = yb != 255; t = torch.where(v, yb, torch.zeros_like(yb)).float()
            if v.sum() == 0:
                continue
            opt.zero_grad()
            with torch.amp.autocast("cuda"):
                o = net(xb).squeeze(1); lb = (bce(o, t) * v).sum() / v.sum()
                p = torch.sigmoid(o) * v
                loss = lb + 1 - (2 * (p * t).sum() + 1) / (p.sum() + (t * v).sum() + 1)
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); tot += loss.item(); nb += 1
        net.eval(); S, Y = [], []
        with torch.no_grad(), torch.amp.autocast("cuda"):
            for i in range(0, len(va_df), a.batch):
                xnp, ynp = batch(va_df, range(i, min(i + a.batch, len(va_df))))
                S.append(torch.sigmoid(net(torch.from_numpy(xnp).to(dev)).squeeze(1)).float().cpu().numpy()); Y.append(ynp)
        S, Y = np.concatenate(S), np.concatenate(Y); V = Y != 255
        tp = int(((S >= 0.5) & (Y == 1) & V).sum()); fp = int(((S >= 0.5) & (Y == 0) & V).sum())
        fn = int(((S < 0.5) & (Y == 1) & V).sum()); f1 = 2 * tp / max(2 * tp + fp + fn, 1)
        hist.append(dict(epoch=ep, train_loss=round(tot / max(nb, 1), 5), val_patch_F1_at_0p5=round(f1, 5)))
        if f1 > best:
            best = f1; torch.save(net.state_dict(), RUN / "model_best.pt")
        if ep % 5 == 0 or ep == a.epochs - 1:
            print(f"  ep {ep:3d} loss {hist[-1]['train_loss']:.4f} val F1@0.5 {f1:.4f} best {best:.4f}", flush=True)
    torch.save(net.state_dict(), RUN / "model_last.pt"); pd.DataFrame(hist).to_csv(RUN / "training_history.csv", index=False)

    # ---- full-frame blended scores (both frames) ------------------------------------------------------------------
    net.load_state_dict(torch.load(RUN / "model_best.pt")); net.eval()
    w1 = np.hanning(PATCH).astype("f4") + 1e-3; Wt = np.outer(w1, w1)
    for f in FRAMES:
        F = D[f]["F"]; acc = np.zeros((F["ny"], F["nx"]), "f4"); ws = np.zeros_like(acc)
        rows = sorted(set(list(range(0, F["ny"] - PATCH + 1, a.stride)) + [F["ny"] - PATCH]))
        cols = sorted(set(list(range(0, F["nx"] - PATCH + 1, a.stride)) + [F["nx"] - PATCH]))
        tiles = [(r, c) for r in rows for c in cols]
        with torch.no_grad(), torch.amp.autocast("cuda"):
            for i in range(0, len(tiles), a.batch):
                tb = tiles[i:i + a.batch]
                xb = np.stack([D[f]["X"][:, r:r + PATCH, c:c + PATCH] for r, c in tb])
                sb = torch.sigmoid(net(torch.from_numpy(xb).to(dev)).squeeze(1)).float().cpu().numpy()
                for (r, c), s_ in zip(tb, sb):
                    acc[r:r + PATCH, c:c + PATCH] += s_ * Wt; ws[r:r + PATCH, c:c + PATCH] += Wt
        sc = acc / np.maximum(ws, 1e-9); sc[~D[f]["has"]] = np.nan; D[f]["score"] = sc
        (OUT / f / "m6").mkdir(exist_ok=True)
        q = np.where(np.isfinite(sc), np.round(sc * 10000), 65535).astype("u2")
        with rasterio.open(OUT / f / "m6" / f"{a.arm}_score.tif", "w", driver="GTiff", height=F["ny"], width=F["nx"],
                           count=1, dtype="uint16", nodata=65535, crs=CFG.CRS_METRIC, transform=F["transform"],
                           compress="deflate", tiled=True, blockxsize=512, blockysize=512) as o:
            o.write(q, 1); o.update_tags(arm=a.arm, split=SPLIT, meaning="weak-label U-Net score, not flood probability")

    # ---- threshold on VALIDATION unique pixels, written BEFORE test is read ---------------------------------------
    sv, yv = [], []
    for f in FRAMES:
        m = (D[f]["role"] == 2) & (D[f]["y"] != 255) & np.isfinite(D[f]["score"])
        sv.append(D[f]["score"][m]); yv.append(D[f]["y"][m] == 1)
    sv, yv = np.concatenate(sv), np.concatenate(yv)
    grid = np.arange(0.05, 0.96, 0.01)
    f1s = [2 * ((sv >= t) & yv).sum() / max(2 * ((sv >= t) & yv).sum() + ((sv >= t) & ~yv).sum() + ((sv < t) & yv).sum(), 1)
           for t in grid]
    thr = float(round(grid[int(np.argmax(f1s))], 2))
    (RUN / "validation_threshold.json").write_text(json.dumps(dict(
        threshold=thr, criterion="max F1 on all owned, labelled VALIDATION pixels (full-frame blend, unique pixels)",
        val_F1=round(float(max(f1s)), 4), n_val_px=int(len(sv)), never_used=["test", "disputed", "B3"]), indent=2))
    print(f"threshold frozen on validation: {thr:.2f} (val F1 {max(f1s):.4f})", flush=True)
    if a.smoke:
        print("SMOKE: stopping before TEST"); return

    # ---- TEST, once ---------------------------------------------------------------------------------------------
    from sklearn.metrics import average_precision_score
    rows, blocks, ss, yy = [], [], [], []
    for f in FRAMES:
        d = D[f]; test = d["role"] == 3
        pred = (d["score"] >= thr) & test & d["has"]
        r, b, (s_, y_) = E.evaluate_frame(pred, np.nan_to_num(d["score"]), d["y"], d["p73"], test & d["has"], d["blk"])
        rows.append(dict(frame=f, **r)); b.insert(0, "frame", f); blocks.append(b); ss.append(s_); yy.append(y_)
    Bt = pd.concat(blocks, ignore_index=True); Bt.to_csv(RUN / "test_blocks.csv", index=False)
    R = pd.DataFrame(rows)
    tot = R[[c for c in R.columns if c.endswith("_px")]].sum()
    ep_all = E.endpoints(tot)
    ep_all.update(A_n_fp_components=int(R.A_n_fp_components.sum()),
                  A_n_isolated_field_components=int(R.A_n_isolated_field_components.sum()),
                  A_isolated_field_km2=round(float(R.A_isolated_field_px.sum()) * E.PX_KM2, 4),
                  B_n_ref_components=int(R.B_n_ref_components.sum()), B_n_recovered=int(R.B_n_recovered.sum()),
                  C_n_ref_components_LOWN=int(R.C_n_ref_components.sum()), C_n_recovered_LOWN=int(R.C_n_recovered.sum()),
                  W_pred_components=int(R.W_pred_components.sum()),
                  G_PR_AUC=round(float(average_precision_score(np.concatenate(yy), np.concatenate(ss))), 4),
                  threshold=thr)
    pd.Series(ep_all).to_csv(RUN / "test_endpoints.csv", header=["value"])
    # a 10 km block cut by the B1/B2 ownership line is ONE physical resampling unit
    E.bootstrap(Bt.drop(columns=["frame"]).groupby("block").sum()).to_csv(RUN / "test_endpoints_ci.csv")
    byf = pd.DataFrame([dict(frame=r_["frame"], **E.endpoints(r_), A_n_fp_components=r_["A_n_fp_components"],
                             B_n_ref_components=r_["B_n_ref_components"], B_n_recovered=r_["B_n_recovered"],
                             W_largest_component_share=r_["W_largest_component_share"]) for r_ in rows])
    byf.to_csv(RUN / "test_by_frame.csv", index=False)
    json.dump(dict(arm=a.arm, channels=chans, note=ARMS[a.arm]["note"], split=SPLIT, split_manifest=man.get("version"),
                   labels="m6_labels_v002", epochs=a.epochs, batch=a.batch, lr=a.lr, seed=SEED, stride=a.stride,
                   architecture="smp.Unet resnet34, encoder_weights=None", loss="masked BCE + Dice",
                   meaning="agreement with held-out weak reference labels; NOT flood-mapping accuracy",
                   seconds=round(time.time() - t0)), open(RUN / "config.json", "w"), indent=2)
    print(pd.Series(ep_all).to_string()); print(byf.to_string(index=False))
    print(f"-> {RUN.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
