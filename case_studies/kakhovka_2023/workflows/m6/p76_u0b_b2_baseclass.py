# Provenance: SWOT-DNIPRO scripts/p76_u0b_b2_baseclass.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: CONTAMINATED -- U0b = U0 + BASE_CLASS; BASE_CLASS is an ingredient of the v001 label (p69b = BASE_CLASS x M2): CONTAMINATED_BY_LABEL_CONSTRUCTION. Kept for forensic reproducibility only; must not be re-run as an ablation.
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P76 -- U0b: does pre-event semantic context recover the agricultural flood that U0 misses?

CONTROLLED ABLATION, NOT A NEW MODEL. U0b is U0 plus one thing: the pre-event surface class (p69a BASE_CLASS) as a
one-hot input. Seed, block split, patch manifest, loss, epochs, batch, lr, augmentation and threshold procedure are
byte-for-byte the procedure of p75. Anything else that differed would make the comparison uninterpretable, so the
split manifest is ASSERTED equal to U0's rather than assumed.

THE ENDPOINT IS NOT GLOBAL F1 (the user's specification). U0's global test F1 of 0.941 is a wetland metric: WETLAND
holds 95.6 % of the positive test support, so a change there moves the global number and a change on agriculture
does not. The primary endpoint is

    dR_VEG_AGRI  --  while simultaneously controlling dP_VEG_AGRI and dR_WETLAND.

A recall gain on agriculture bought by lowering precision on agriculture, or by loosening the decision everywhere
(visible as a recall move on wetland), is not evidence that pre-event context helps. All three are reported with a
PAIRED spatial-block bootstrap: the same test blocks are resampled for both models and the difference is formed
inside each resample, because comparing two independent confidence intervals is not a test of their difference.

THE LEAKAGE CONTROL THIS RUN EXISTS TO SURVIVE. The weak label y is not independent of BASE_CLASS: p69b builds the
semantic state as BASE_CLASS x M2, and y = 1 requires a flood-associated semantic state. BASE_CLASS therefore
cannot be handed to the network without first measuring how much of y it explains ON ITS OWN. U0b_LOOKUP does
exactly that -- per-class positive rates fitted on TRAIN patches and applied as a constant map on TEST. If that
table alone scores highly, any U0b gain is label structure and not pre-event physics, and the ablation is reported
as contaminated rather than as a result.

Outputs: runs/U0b_B2/{config.json,split_check.json,normalization.json,training_history.csv,
         validation_threshold.json,test_metrics.json,challenge_metrics.csv,leakage_control.json,
         paired_endpoint.csv,disputed_score_stats.csv,model_best.pt,model_last.pt}
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
U0 = ROOT / "runs" / "U0_B2"
RUN = ROOT / "runs" / "U0b_B2"
FID = "B2"; PATCH = 512; STRIDE = 128; SCALE = 100.0; ND = -32768
SPLIT_BAND = 5
PEAK = ("2023-06-09", "2023-06-13", "2023-06-14")
SEED = 20260923                      # identical to p75 -- the split must reproduce, and it is checked, not trusted
#: p69a codes. UNCERT is carried as its own channel rather than folded into a class: an unknown pre-event surface is
#: not the same evidence as a known dry one, and collapsing it would be the "absence of a veto is not permission"
#: mistake in input form.
BCn = {0: "PRE_WATER", 1: "VEG_AGRI", 2: "BARE_SAND", 3: "BUILT_UP", 4: "WETLAND", 5: "OTHER_DRY", 6: "UNCERT"}
NB = len(BCn)
BOOT = 2000


def s1_peak(F):
    z = np.load(CFG.S1_CACHE / "ZONE_2_KHERSON_DELTA_flood_june2023" / "per_scene_water.npz", allow_pickle=True)
    shp = tuple(int(v) for v in z["shape"]); cell = float(z["cell"])
    tr = from_origin(float(z["x0"]), float(z["y1"]), cell, cell); wet = np.zeros(shp, bool)
    for k in [k for k in z.keys() if k[:4] == "2023" and not k.startswith("valid_")]:
        if k[:10] not in PEAK:
            continue
        w = np.unpackbits(z[k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
        v = np.unpackbits(z["valid_" + k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
        wet |= (w & v)
    d = np.zeros((F["ny"], F["nx"]), "u1")
    reproject(source=wet.astype("u1"), destination=d, src_transform=tr, src_crs=CFG.CRS_METRIC,
              dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest,
              src_nodata=0, dst_nodata=0)
    return d.astype(bool)


def metrics(yt, pr):
    tp = int((pr & (yt == 1)).sum()); fp = int((pr & (yt == 0)).sum()); fn = int((~pr & (yt == 1)).sum())
    tn = int((~pr & (yt == 0)).sum())
    P = tp / max(tp + fp, 1); R = tp / max(tp + fn, 1)
    return dict(TP=tp, FP=fp, FN=fn, TN=tn, precision=round(P, 5), recall=round(R, 5),
                F1=round(2 * P * R / max(P + R, 1e-9), 5), IoU=round(tp / max(tp + fp + fn, 1), 5))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--batch", type=int, default=6); ap.add_argument("--lr", type=float, default=3e-4)
    a = ap.parse_args()
    import torch, torch.nn as nn, segmentation_models_pytorch as smp
    RUN.mkdir(parents=True, exist_ok=True)
    F = CG.frame_grid(FID)
    with rasterio.open(OUT / FID / "s1_change.tif") as s:
        CH = list(s.descriptions); X = s.read().astype("f4")
    NS1 = len(CH)
    X[X == ND] = np.nan
    for i, c in enumerate(CH):
        if not c.startswith("n_"):
            X[i] /= SCALE
    with rasterio.open(OUT / FID / "labels.tif") as s:
        lab = s.read(1)
    with rasterio.open(OUT / FID / "p69b_semantic_state.tif") as s:
        sem = s.read(1)
    with rasterio.open(OUT / FID / "folds.tif") as s:
        blk = s.read(SPLIT_BAND)
    with rasterio.open(OUT / FID / "p69a_base_class.tif") as s:
        bc = s.read(1)
    s1w = s1_peak(F); m2 = np.isin(sem, (1, 2, 3, 4, 5))
    y = np.full((F["ny"], F["nx"]), 255, np.uint8)
    y[lab == 0] = 0
    y[(lab == 1) & s1w & m2] = 1
    disputed = s1w & ~m2
    y[disputed] = 255

    # ---- split: reproduce p75 exactly, then ASSERT it -----------------------------------------------------------
    rng = np.random.default_rng(SEED)
    ub = np.unique(blk[blk > 0]); rng.shuffle(ub)
    n_te = max(1, len(ub) // 5); test_b = set(ub[:n_te].tolist())
    rest = ub[n_te:]; n_va = max(1, len(rest) // 5); val_b = set(rest[:n_va].tolist())
    train_b = set(rest[n_va:].tolist())
    assert not (train_b & val_b) and not (train_b & test_b) and not (val_b & test_b)
    role = np.zeros_like(blk, np.uint8)
    role[np.isin(blk, list(train_b))] = 1; role[np.isin(blk, list(val_b))] = 2
    role[np.isin(blk, list(test_b))] = 3

    half = PATCH // 2; cand = []
    for r in range(half, F["ny"] - half, STRIDE):
        for c in range(half, F["nx"] - half, STRIDE):
            sl = (slice(r - half, r + half), slice(c - half, c + half))
            rr = role[sl]; u = set(np.unique(rr[rr > 0]).tolist())
            if len(u) != 1:
                continue
            if np.isnan(X[0][sl]).mean() > 0.5:
                continue
            yy = y[sl]
            cand.append(dict(row=r, col=c, split={1: "train", 2: "val", 3: "test"}[u.pop()],
                             block=int(np.bincount(blk[sl].ravel()[blk[sl].ravel() > 0]).argmax()),
                             flood_px=int((yy == 1).sum()), neg_px=int((yy == 0).sum()),
                             disputed_px=int(disputed[sl].sum())))
    C = pd.DataFrame(cand); C = C[(C.flood_px + C.neg_px) > 0].reset_index(drop=True)
    U0C = pd.read_csv(U0 / "split_manifest.csv")
    same = (len(C) == len(U0C) and
            C[["row", "col", "split"]].sort_values(["row", "col"]).reset_index(drop=True)
            .equals(U0C[["row", "col", "split"]].sort_values(["row", "col"]).reset_index(drop=True)))
    json.dump(dict(patches_u0b=len(C), patches_u0=len(U0C), identical_split=bool(same)),
              open(RUN / "split_check.json", "w"), indent=2)
    if not same:
        raise SystemExit("split does not reproduce p75 -- a paired ablation on a different split is meaningless")
    C.to_csv(RUN / "split_manifest.csv", index=False)
    print(f"split reproduces U0 exactly: {len(C)} patches", flush=True)

    tr_df = C[C.split == "train"].reset_index(drop=True)
    va_df = C[C.split == "val"].reset_index(drop=True)
    te_df = C[C.split == "test"].reset_index(drop=True)
    w = np.where(tr_df.flood_px.values > 0, 4.0, 1.0); w /= w.sum()

    # ---- leakage control BEFORE training: how much of y does BASE_CLASS explain alone? ---------------------------
    trmask = np.zeros((F["ny"], F["nx"]), bool)
    for r in tr_df.itertuples():
        trmask[r.row - half:r.row + half, r.col - half:r.col + half] = True
    temask = np.zeros((F["ny"], F["nx"]), bool)
    for r in te_df.itertuples():
        temask[r.row - half:r.row + half, r.col - half:r.col + half] = True
    # MEASURE RANKING POWER, NOT ACCURACY AT AN ARBITRARY THRESHOLD. The first version of this control thresholded
    # the rate map at 0.5 and reported F1. At a prevalence of 0.16 no class rate reaches 0.5, so the rule predicted
    # all-negative and returned F1 = 0.0000 -- which reads as "no leakage" and means nothing at all. A feature leaks
    # by RANKING the label, so the control is AP against the no-skill AP (the prevalence) and AUC against 0.5.
    from sklearn.metrics import average_precision_score, roc_auc_score
    rate = {}
    for k in BCn:
        s_ = trmask & (bc == k) & (y != 255)
        rate[k] = float((y[s_] == 1).mean()) if s_.sum() else 0.0
    Tm = temask & (y != 255)
    yt = (y[Tm] == 1).astype("u1")
    sc = np.array([rate[k] for k in range(NB)], "f4")[bc[Tm]]
    prev = float(yt.mean()); ap = float(average_precision_score(yt, sc)); auc = float(roc_auc_score(yt, sc))
    contaminated = bool(auc >= 0.75 or ap >= 3.0 * prev)
    json.dump(dict(train_positive_rate_by_base_class={BCn[k]: round(v, 5) for k, v in rate.items()},
                   test_prevalence=round(prev, 5), lookup_AP=round(ap, 5), no_skill_AP=round(prev, 5),
                   lookup_AUC=round(auc, 5), ap_lift=round(ap / max(prev, 1e-9), 3),
                   criterion="AUC >= 0.75 or AP >= 3x prevalence",
                   interpretation="BASE_CLASS alone, as a constant per-class positive-rate map fitted on TRAIN and "
                                  "applied to TEST. The weak label y is built as (reference AND S1 peak AND "
                                  "flood-associated semantic state), and the semantic state is itself BASE_CLASS x "
                                  "M2, so BASE_CLASS is an INGREDIENT OF THE LABEL, not an independent covariate. "
                                  "If it ranks the label on its own, U0b measures how well the network reproduces "
                                  "the label's construction rule, not whether pre-event context helps.",
                   contaminated=contaminated),
              open(RUN / "leakage_control.json", "w"), indent=2)
    print(f"leakage control -- BASE_CLASS-only lookup on TEST: AP {ap:.4f} (no-skill {prev:.4f}, "
          f"lift x{ap/max(prev,1e-9):.2f}), AUC {auc:.4f} -> "
          f"{'CONTAMINATED' if contaminated else 'usable'}", flush=True)

    # ---- normalisation: S1 channels from TRAIN geography only; one-hot channels are left at 0/1 ------------------
    rr, cc = np.nonzero(trmask)
    take = rng.choice(len(rr), size=min(2_000_000, len(rr)), replace=False)
    samp = X[:, rr[take], cc[take]]
    med = np.nanmedian(samp, axis=1)[:, None, None]
    iqr = (np.nanpercentile(samp, 75, axis=1) - np.nanpercentile(samp, 25, axis=1))[:, None, None]
    iqr[iqr < 1e-6] = 1.0
    del samp, rr, cc, take, trmask, temask
    X = np.nan_to_num((X - med) / iqr, nan=0.0).astype("f4")
    json.dump(dict(channels=CH + [f"onehot_{BCn[k]}" for k in BCn],
                   median=med.ravel().tolist(), iqr=iqr.ravel().tolist(),
                   source="TRAIN patch geography only, 2M-pixel sample; one-hot channels not normalised"),
              open(RUN / "normalization.json", "w"), indent=2)

    def cutx(df, idx):
        """S1 block plus the one-hot expansion, built per patch so the frame is never held twice."""
        xs = np.empty((len(idx), NS1 + NB, PATCH, PATCH), "f4")
        ys = np.empty((len(idx), PATCH, PATCH), "u1")
        for j, i in enumerate(idx):
            r = df.iloc[i]; sl = (slice(r.row - half, r.row + half), slice(r.col - half, r.col + half))
            xs[j, :NS1] = X[:, sl[0], sl[1]]
            b = bc[sl]
            for q, k in enumerate(BCn):
                xs[j, NS1 + q] = (b == k)
            ys[j] = y[sl]
        return xs, ys

    dev = "cuda"; torch.manual_seed(SEED)
    net = smp.Unet("resnet34", encoder_weights=None, in_channels=NS1 + NB, classes=1).to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr)
    scaler = torch.amp.GradScaler("cuda"); bce = nn.BCEWithLogitsLoss(reduction="none")
    hist = []; best = -1; t0 = time.time()
    for ep in range(a.epochs):
        net.train()
        idx = rng.choice(len(tr_df), size=min(len(tr_df), 64), replace=True, p=w)
        tot = 0.0; nb = 0
        for i in range(0, len(idx), a.batch):
            xnp, ynp = cutx(tr_df, idx[i:i + a.batch])
            xb = torch.from_numpy(xnp).to(dev); yb = torch.from_numpy(ynp.astype("i8")).to(dev)
            if rng.random() < 0.5:
                xb = torch.flip(xb, [-1]); yb = torch.flip(yb, [-1])
            if rng.random() < 0.5:
                xb = torch.flip(xb, [-2]); yb = torch.flip(yb, [-2])
            v = (yb != 255); t = torch.where(v, yb, torch.zeros_like(yb)).float()
            if v.sum() == 0:
                continue
            opt.zero_grad()
            with torch.amp.autocast("cuda"):
                o = net(xb).squeeze(1)
                lb = (bce(o, t) * v).sum() / v.sum()
                p = torch.sigmoid(o) * v
                dl = 1 - (2 * (p * t).sum() + 1) / (p.sum() + (t * v).sum() + 1)
                loss = lb + dl
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update()
            tot += loss.detach().item(); nb += 1
        net.eval(); sc = []; yl = []
        with torch.no_grad(), torch.amp.autocast("cuda"):
            for i in range(0, len(va_df), a.batch):
                xnp, ynp = cutx(va_df, range(i, min(i + a.batch, len(va_df))))
                sc.append(torch.sigmoid(net(torch.from_numpy(xnp).to(dev)).squeeze(1)).float().cpu().numpy())
                yl.append(ynp)
        S = np.concatenate(sc); Yva = np.concatenate(yl); V = Yva != 255
        f1 = metrics(Yva[V], (S[V] >= 0.5))["F1"]
        hist.append(dict(epoch=ep, train_loss=round(tot / max(nb, 1), 5), val_F1_at_0p5=f1,
                         vram_gb=round(torch.cuda.max_memory_allocated() / 1e9, 2)))
        if f1 > best:
            best = f1; torch.save(net.state_dict(), RUN / "model_best.pt")
        if ep % 5 == 0 or ep == a.epochs - 1:
            print(f"  ep {ep:3d}  loss {hist[-1]['train_loss']:.4f}  val F1@0.5 {f1:.4f}  best {best:.4f}",
                  flush=True)
    torch.save(net.state_dict(), RUN / "model_last.pt")
    pd.DataFrame(hist).to_csv(RUN / "training_history.csv", index=False)

    net.load_state_dict(torch.load(RUN / "model_best.pt")); net.eval()

    def score(model, df, nch):
        o = []; yl = []
        with torch.no_grad(), torch.amp.autocast("cuda"):
            for i in range(0, len(df), a.batch):
                xnp, ynp = cutx(df, range(i, min(i + a.batch, len(df))))
                o.append(torch.sigmoid(model(torch.from_numpy(xnp[:, :nch]).to(dev)).squeeze(1))
                         .float().cpu().numpy())
                yl.append(ynp)
        return np.concatenate(o), np.concatenate(yl)

    Sva, Yva = score(net, va_df, NS1 + NB); V = Yva != 255
    grid = np.arange(0.05, 0.96, 0.01)
    f1s = [metrics(Yva[V], (Sva[V] >= t))["F1"] for t in grid]
    thr = float(grid[int(np.argmax(f1s))])
    json.dump(dict(threshold=thr, criterion="max F1 on VALIDATION patches (identical procedure to U0)",
                   val_F1=max(f1s)), open(RUN / "validation_threshold.json", "w"), indent=2)
    print(f"\nthreshold frozen on validation: {thr:.2f} (val F1 {max(f1s):.4f})", flush=True)

    Ste, Yte = score(net, te_df, NS1 + NB); T = Yte != 255
    m = metrics(Yte[T], Ste[T] >= thr); m["threshold"] = thr
    json.dump(m, open(RUN / "test_metrics.json", "w"), indent=2)
    print("TEST U0b: " + ", ".join(f"{k} {v}" for k, v in m.items()
                                   if k in ("precision", "recall", "F1", "IoU")), flush=True)

    # ---- U0 scored on the SAME patches, so the comparison is paired ---------------------------------------------
    net0 = smp.Unet("resnet34", encoder_weights=None, in_channels=NS1, classes=1).to(dev)
    net0.load_state_dict(torch.load(U0 / "model_best.pt")); net0.eval()
    thr0 = json.load(open(U0 / "validation_threshold.json"))["threshold"]
    S0, _ = score(net0, te_df, NS1)

    Bte = np.stack([bc[r.row - half:r.row + half, r.col - half:r.col + half] for r in te_df.itertuples()])
    ch = []
    for k, nm in BCn.items():
        sel = T & (Bte == k)
        if sel.sum() < 1000:
            continue
        a0 = metrics(Yte[sel], S0[sel] >= thr0); a1 = metrics(Yte[sel], Ste[sel] >= thr)
        ch.append(dict(stratum=nm, n_px=int(sel.sum()), km2=round(float(sel.sum()) * 1e-4, 1),
                       n_positive=int((Yte[sel] == 1).sum()),
                       U0_P=a0["precision"], U0_R=a0["recall"], U0_F1=a0["F1"],
                       U0b_P=a1["precision"], U0b_R=a1["recall"], U0b_F1=a1["F1"],
                       dP=round(a1["precision"] - a0["precision"], 5),
                       dR=round(a1["recall"] - a0["recall"], 5),
                       support_limited=bool((Yte[sel] == 1).sum() < 5000)))
    pd.DataFrame(ch).to_csv(RUN / "challenge_metrics.csv", index=False)

    # ---- paired spatial-block bootstrap on the DIFFERENCE -------------------------------------------------------
    # Resample TEST BLOCKS, not patches: patches overlap and share ground, so a patch bootstrap would treat the same
    # pixels as independent draws. The difference is formed INSIDE each resample -- two separate CIs are not a test.
    tb = te_df.block.values; ublk = np.unique(tb)
    rows = []
    for k, nm in BCn.items():
        sel_all = T & (Bte == k)
        if sel_all.sum() < 1000:
            continue
        per = []
        for b in ublk:
            w_ = np.isin(tb, [b])
            s_ = sel_all[w_]
            if s_.sum() == 0:
                per.append(None); continue
            yy = Yte[w_][s_]; p0 = S0[w_][s_] >= thr0; p1 = Ste[w_][s_] >= thr
            per.append((int((p0 & (yy == 1)).sum()), int((p0 & (yy == 0)).sum()), int((yy == 1).sum()),
                        int((p1 & (yy == 1)).sum()), int((p1 & (yy == 0)).sum())))
        ok = [i for i, v in enumerate(per) if v is not None]
        if len(ok) < 3:
            continue
        dR = np.empty(BOOT); dP = np.empty(BOOT)
        for it in range(BOOT):
            pick = rng.choice(ok, size=len(ok), replace=True)
            t0_ = sum(per[i][0] for i in pick); f0_ = sum(per[i][1] for i in pick)
            pos = sum(per[i][2] for i in pick)
            t1_ = sum(per[i][3] for i in pick); f1_ = sum(per[i][4] for i in pick)
            dR[it] = t1_ / max(pos, 1) - t0_ / max(pos, 1)
            dP[it] = t1_ / max(t1_ + f1_, 1) - t0_ / max(t0_ + f0_, 1)
        rows.append(dict(stratum=nm, n_blocks=len(ok),
                         dR=round(float(np.mean(dR)), 5),
                         dR_lo=round(float(np.percentile(dR, 2.5)), 5),
                         dR_hi=round(float(np.percentile(dR, 97.5)), 5),
                         dR_excludes_zero=bool(np.percentile(dR, 2.5) > 0 or np.percentile(dR, 97.5) < 0),
                         dP=round(float(np.mean(dP)), 5),
                         dP_lo=round(float(np.percentile(dP, 2.5)), 5),
                         dP_hi=round(float(np.percentile(dP, 97.5)), 5),
                         dP_excludes_zero=bool(np.percentile(dP, 2.5) > 0 or np.percentile(dP, 97.5) < 0)))
    E = pd.DataFrame(rows); E.to_csv(RUN / "paired_endpoint.csv", index=False)
    print("\npaired spatial-block bootstrap, U0b - U0 (2000 resamples of TEST blocks):")
    for r in rows:
        print(f"  {r['stratum']:10s} dR {r['dR']:+.4f} [{r['dR_lo']:+.4f},{r['dR_hi']:+.4f}]"
              f"{'*' if r['dR_excludes_zero'] else ' '}   "
              f"dP {r['dP']:+.4f} [{r['dP_lo']:+.4f},{r['dP_hi']:+.4f}]"
              f"{'*' if r['dP_excludes_zero'] else ' '}", flush=True)

    va = E[E.stratum == "VEG_AGRI"]; we = E[E.stratum == "WETLAND"]
    verdict = "INCONCLUSIVE"
    if contaminated:
        # The endpoint is still computed and published -- it describes what the network does when handed the
        # label's own ingredient -- but it CANNOT answer whether pre-event context helps, and must not be quoted
        # as if it did. The clean form of the question needs an input outside the label chain.
        verdict = "CONTAMINATED_BY_LABEL_CONSTRUCTION_not_an_answer_to_the_hypothesis"
    elif len(va) and len(we):
        v = va.iloc[0]; wv = we.iloc[0]
        if v.dR > 0 and v.dR_excludes_zero and not (v.dP < 0 and v.dP_excludes_zero) and not wv.dR_excludes_zero:
            verdict = "PRE_EVENT_CONTEXT_HELPS_AGRICULTURE"
        elif v.dR > 0 and v.dR_excludes_zero:
            verdict = "AGRI_RECALL_GAIN_NOT_ISOLATED"     # bought with precision or with a global loosening
        elif not v.dR_excludes_zero:
            verdict = "NO_DETECTABLE_EFFECT_ON_AGRICULTURE"
    json.dump(dict(model="U0b", inputs=f"p71 orbit-safe S1 ({NS1} ch) + p69a BASE_CLASS one-hot ({NB} ch)",
                   ablation_of="U0 (p75) -- identical seed, split, patches, loss, schedule and threshold rule",
                   primary_endpoint="dR_VEG_AGRI controlling dP_VEG_AGRI and dR_WETLAND",
                   verdict=verdict, leakage_control_F1=lk["F1"],
                   epochs=a.epochs, batch=a.batch, lr=a.lr, seed=SEED,
                   disputed_policy="IGNORE in loss, threshold, early stopping and tuning"),
              open(RUN / "config.json", "w"), indent=2)
    print(f"\nVERDICT: {verdict}")
    print(f"{time.time()-t0:.0f}s -> runs/U0b_B2/")


if __name__ == "__main__":
    main()
