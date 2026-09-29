# New in floodstate-eo, 2026-09-23. STATUS: ACTIVE. One trainer for every M6 arm on the frozen m6_split_v1.
# Rev 2 (2026-09-25): --labels {v002,v003_A} and arm U2b (+W_pre). v002 runs (<ARM>_B1B2_v1) are untouched:
#   a v003_A run lives in <ARM>_B1B2_v003A and writes <ARM>_v003A_score.tif. Geography, recipe, seed unchanged.
# Rev 3 (2026-09-29, review F09/F10/F11): --labels v004 (the v003_A rule on the corrected M2: no TRACE feature, inner
#   out-of-fold thresholds; runs/<ARM>_B1B2_v004[_s<seed>]); --seed for training-seed replicates (F11; the default seed
#   keeps every existing run name); W_pre is read from the chosen label product's S1 bands.
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
- Labels: v002 (default, FLOOD / NON_FLOOD / IGNORE) or v003_A (p77d ontology: EVENT_FLOOD -> 1, LAND and
  REFERENCE_WATER -> 0, UNKNOWN -> 255). v003_A is FROZEN (2026-09-25, tables/m6_labels_v003_A_FROZEN.json); its positives are identical to
  v002's, its negatives add recurrent May-2023 water (REFERENCE_WATER) and drop v002 NON_FLOOD pixels without
  >= 3 admitted May dates. U2b requires v003_A: under v002 no labelled pixel has pre-breach water, so W_pre cannot be
  supervised (NEXT_STEPS, U2b blocker).

Outputs: runs/<ARM>_B1B2_v1/{config.json, normalization.json, training_history.csv, validation_threshold.json,
         eval_d1a/{endpoints,endpoints_ci,by_frame,blocks,a2_curve}.csv, model_best.pt, model_last.pt}
         $BULK_ROOT/frames10/<F>/m6/<ARM>_score.tif (uint16 x10000, nodata 65535)
         with --labels v003_A: runs/<ARM>_B1B2_v003A/ and m6/<ARM>_v003A_score.tif
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
    # best U0 by the pre-registered D2 rule is U0d (compare_U0d_vs_U0z), so U1 builds on U0d
    "U1": dict(s1=D_CH + SUPPORT, p73=True,
               note="U0d + frozen p73 RF20 surface class as one-hot INPUT context (never in labels)."),
    # H1: terrain removes elevated cropland false positives. HAND is a FEATURE (continuous metres, TRAIN median/IQR
    # normalisation, explicit has_hand indicator for its nodata domain), never a hand-made mask. Fixed before training.
    "U2": dict(s1=D_CH + SUPPORT, p73=False, hand=True,
               note="U0d + HAND (floodplain/<zone>_hand_m.tif, metres) + has_hand. NO p73, NO z_*, NO S2, NO TRACE."),
    # H2: the immediate pre-event S1 water state (06-01 / 06-02, the last observations before the breach) separates
    # event flood from water that was already there. W_pre is an OBSERVATION channel (0 dry / 1 water on any valid
    # date, unobserved -> 0 + explicit has_wpre); it is read from bands w_pre_state / w_pre_valid of the v003_A label
    # product, which are pure S1 layers (never a label). CAVEAT (recorded before training): v003_A EVENT_FLOOD is
    # defined with w_pre_state = 0, so W_pre is also a label ingredient -- U2b tests whether the network USES the
    # channel, not whether W_pre is informative in general.
    "U2b": dict(s1=D_CH + SUPPORT, p73=False, hand=True, wpre=True,
                note="U2 + W_pre (S1 06-01/06-02 water state) + has_wpre. Requires --labels v003_A."),
}
LABELS = {
    "v002": dict(file="m6_labels_v002.tif", band=1, map=None, run="v1", tag=""),
    "v003_A": dict(file="m6_labels_v003_A.tif", band=1, map={0: 0, 1: 1, 2: 0, 255: 255}, run="v003A", tag="_v003A"),
    "v004": dict(file="m6_labels_v004.tif", band=1, map={0: 0, 1: 1, 2: 0, 255: 255}, run="v004", tag="_v004"),
    "v002_notrace": dict(file="m6_labels_v002_notrace.tif", band=1, map=None, run="v002nt", tag="_v002nt"),   # the v002 rule on the corrected M2 (F09/F10)
}
STAGE2_LABELS = ("v004", "v002_notrace")                              # labels on the corrected M2: RF20 rev 2 by default (F08)
HANDZ = {"B1": "ZONE_4_DAM_TO_KHERSON_FLOODWAY", "B2": "ZONE_2_KHERSON_DELTA"}


def hand_10m(fid, F):
    """HAND (m) on the frame lattice, nearest from its own 20 m transform (origin half a cell off the S2 grid);
    NaN outside its domain."""
    from rasterio.enums import Resampling
    from rasterio.warp import reproject
    with rasterio.open(CFG.BULK_ROOT / "floodplain" / HANDZ[fid] / f"{HANDZ[fid]}_hand_m.tif") as s:
        h = s.read(1).astype("f4"); h[h == s.nodata] = np.nan
        d = np.full((F["ny"], F["nx"]), np.nan, "f4")
        reproject(source=h, destination=d, src_transform=s.transform, src_crs=s.crs, dst_transform=F["transform"],
                  dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
    return d
#: p73 input encoding, fixed before U1 was trained: one-hot of the frozen class, SHRUB/OTHER omitted (never
#: predicted), p73 nodata -> all zeros; 20 m -> 10 m by exact 2x2 replication (the grids nest).
P73_ONEHOT = [(1, "p73_WATER"), (2, "p73_CROPLAND"), (3, "p73_GRASS_LOW_VEGETATION"), (4, "p73_FOREST"),
              (6, "p73_WETLAND_REED"), (7, "p73_BUILT_UP"), (8, "p73_BARE_SAND"), (10, "p73_UNCERTAIN")]


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


def wpre_10m(fid, lab="v003_A"):
    """W_pre channel (0/1) and its validity mask from the S1 observation bands of the label product (never the ontology band)."""
    with rasterio.open(OUT / fid / LABELS[lab]["file"]) as s:
        d = list(s.descriptions)
        st = s.read(d.index("w_pre_state") + 1); nv = s.read(d.index("w_pre_valid") + 1)
    return (st == 1).astype("f4"), (nv > 0)


def labels_10m(fid, lab):
    y, _ = read(fid, LABELS[lab]["file"], LABELS[lab]["band"])
    if LABELS[lab]["map"]:
        z = np.full(y.shape, 255, np.uint8)
        for k, v in LABELS[lab]["map"].items():
            z[y == k] = v
        y = z
    return y.astype(np.uint8)


def main():
    global SPLIT
    ap = argparse.ArgumentParser(); ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--labels", default="v002", choices=sorted(LABELS))
    ap.add_argument("--split", default=SPLIT, help="split version; m6_split_v1 (frozen) or m6_split_sNN (block-size sensitivity)")
    ap.add_argument("--epochs", type=int, default=60); ap.add_argument("--batch", type=int, default=6)
    ap.add_argument("--lr", type=float, default=3e-4); ap.add_argument("--stride", type=int, default=256)
    ap.add_argument("--smoke", action="store_true", help="pipeline check: separate dir, stops BEFORE test is read")
    ap.add_argument("--seed", type=int, default=SEED, help="training seed; a non-default seed gets its own run directory and score (_s<seed>)")
    ap.add_argument("--p73-rev", type=int, default=None, choices=[1, 2], help="RF20 version for U1 input and the evaluation strata; default 2 for v004 / v002_notrace (F08), else 1")
    a = ap.parse_args()
    import torch, torch.nn as nn, segmentation_models_pytorch as smp
    E = _load("m6_eval"); P84 = _load("p84_m6_split_b1b2")
    SPLIT = a.split; SSFX = "" if a.split == "m6_split_v1" else "_" + a.split.split("_")[-1]
    L = LABELS[a.labels]; SEEDSFX = "" if a.seed == SEED else f"_s{a.seed}"
    P73REV = a.p73_rev or (2 if a.labels in STAGE2_LABELS else 1)
    if ARMS[a.arm].get("wpre") and a.labels in ("v002", "v002_notrace"):
        raise SystemExit("U2b cannot be supervised under v002 (0 labelled pixels with pre-breach water); use --labels v003_A")
    RUN = ROOT / "runs" / (f"_smoke_{a.arm}{L['tag']}" if a.smoke else f"{a.arm}_B1B2_{L['run']}{SSFX}{SEEDSFX}")
    if a.smoke and RUN.exists():
        import shutil; shutil.rmtree(RUN)
    if RUN.exists():
        raise SystemExit(f"{RUN} exists -- a run directory is immutable (TEST must not be evaluated twice)")
    RUN.mkdir(parents=True)
    rng = np.random.default_rng(a.seed); torch.manual_seed(a.seed)
    man = json.loads((CFG.TABLES / f"{SPLIT}_manifest.json").read_text())
    C = pd.read_csv(CFG.TABLES / f"{SPLIT}_patches.csv")
    D = {}
    for f in FRAMES:
        F = CG.frame_grid(f)
        X, has = frame_tensor(f, a.arm)
        if ARMS[a.arm].get("hand"):
            X = np.concatenate([X, hand_10m(f, F)[None]], 0)
        role, _ = read(f, f"{SPLIT}_role.tif", 1)
        y = labels_10m(f, a.labels)
        y = np.where(np.isin(role, (1, 2, 3)) & has, y, 255).astype(np.uint8)
        if ARMS[a.arm].get("wpre"):
            D[f] = dict(wpre=wpre_10m(f, a.labels))
        else:
            D[f] = {}
        p73 = P84.p73_10m(f, F, P73REV)
        gx = F["transform"].c + 10.0 * np.arange(F["nx"]); gy = F["transform"].f - 10.0 * np.arange(F["ny"])
        BM = float(man.get("block_m", P84.BLOCK_M))
        blk = np.floor(gy / BM).astype("i8")[:, None] * 100000 + np.floor(gx / BM).astype("i8")[None, :]
        D[f].update(F=F, X=X, has=has, role=role, y=y, p73=p73, blk=blk)
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
        extra = [D[f]["has"][None].astype("f4")]
        if ARMS[a.arm].get("hand"):
            extra.append(np.isfinite(D[f]["X"][-1])[None].astype("f4"))      # has_hand, from the raw (pre-norm) HAND
        if ARMS[a.arm]["p73"]:
            extra.append(np.stack([(D[f]["p73"] == k).astype("f4") for k, _ in P73_ONEHOT]))
        if ARMS[a.arm].get("wpre"):
            wp, wv = D[f].pop("wpre")
            extra += [wp[None], wv[None].astype("f4")]                    # W_pre (unnormalised 0/1) + has_wpre
        D[f]["X"] = np.concatenate([Z] + extra, 0)
    chans = (ARMS[a.arm]["s1"] + (["hand_m"] if ARMS[a.arm].get("hand") else []) + ["has_event"]
             + (["has_hand"] if ARMS[a.arm].get("hand") else []) + ([n for _, n in P73_ONEHOT] if ARMS[a.arm]["p73"] else [])
             + (["w_pre_state", "has_wpre"] if ARMS[a.arm].get("wpre") else []))
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
        with rasterio.open(OUT / f / "m6" / f"{a.arm}{L['tag']}{SSFX}{SEEDSFX}_score.tif", "w", driver="GTiff", height=F["ny"], width=F["nx"],
                           count=1, dtype="uint16", nodata=65535, crs=CFG.CRS_METRIC, transform=F["transform"],
                           compress="deflate", tiled=True, blockxsize=512, blockysize=512) as o:
            o.write(q, 1); o.update_tags(arm=a.arm, split=SPLIT, labels=L["file"],
                                         meaning="weak-label U-Net score, not flood probability")

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

    # ---- TEST, once: D1 + amendment (A1/A2) through the one harness ----------------------------------------------
    for f in FRAMES:
        D[f].pop("X")                                                   # free memory; scores are all that is needed
    ep, byf, curve = E.evaluate_arm(RUN, a.arm, D, thr)
    json.dump(dict(arm=a.arm, channels=chans, note=ARMS[a.arm]["note"], split=SPLIT, split_manifest=man.get("version"),
                   labels=L["file"].replace(".tif", ""), label_map=L["map"],
                   wpre_source=(f"{L['file']} bands w_pre_state/w_pre_valid (S1 2023-06-01/02 observation layers)"
                                if ARMS[a.arm].get("wpre") else None),
                   epochs=a.epochs, batch=a.batch, lr=a.lr, seed=a.seed, stride=a.stride, p73_rev=P73REV,
                   architecture="smp.Unet resnet34, encoder_weights=None", loss="masked BCE + Dice",
                   meaning="agreement with held-out weak reference labels; NOT flood-mapping accuracy",
                   seconds=round(time.time() - t0)), open(RUN / "config.json", "w"), indent=2)
    print(pd.Series(ep).to_string()); print(byf.to_string(index=False))
    print(curve.to_string(index=False))
    print(f"-> {RUN.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
