# New in floodstate-eo, 2026-09-23. STATUS: ACTIVE. Produces the ONE frozen B1+B2 geography every M6 arm must use.
"""P84 -- m6_split_v1: the frozen B1+B2 train / validation / test geography for U0d, U0z, U1, U2, ...

GEOGRAPHY FIRST, PATCHES SECOND, AND ONE PHYSICAL PIXEL ONCE.
- B1 and B2 lie on the same global 10 m lattice. Their overlap is DEDUPLICATED before any geography is assigned:
  B2 owns its whole extent (deeper matched S1 baselines, full event coverage), B1 owns the rest of B1. A pixel is
  supervised, validated and tested only in its owner frame; the other frame may still SEE it as input context, but
  it is IGNORE there.
- Blocks are 10 km cells of the GLOBAL lattice (origin on multiples of 10 km), so both frames share them.
- Splits are assigned per block. A training/validation/test patch must lie entirely inside its split's region after
  that region is eroded by BUFFER_PX -- a 640 m exclusion band along every split boundary.

TEST GEOGRAPHY IS CHOSEN FOR WHAT IT MUST CONTAIN, NOT TO REPRODUCE PREVALENCE (decision D1). Required strata, from
m6_labels_v002 x the frozen p73 surface class (p73 only CHECKS composition; it never touches a label):
    DRY_CROPLAND, FLOODED_OPEN_LOW_VEGETATION (CROPLAND u GRASS_LOW_VEGETATION -- an evaluation stratum frozen
    before training, not a land-cover class), FLOODED_WETLAND, DRY_WETLAND_OR_VEGETATION, FLOOD_BOUNDARY
    and, where geographically available, FLOODED_CROPLAND (LOW-N: ~3 km2 in total).
Assignment: SEED-driven shuffles of the block list into ~20 % test / ~15 % validation / rest train (by block count);
the FIRST draw in which every required stratum has TEST share in [15 %, 45 %], VALIDATION share >= 8 % and TRAIN
share >= 35 %, and FLOODED_CROPLAND has a non-zero TEST share, is accepted; its draw index is recorded.
Selection reads m6_labels_v002 and the frozen p73 only -- never U0/U1 scores, previous model errors or target metrics.

ANTI-LEAKAGE, TWO GUARANTEES, BOTH ASSERTED ON THE FROZEN PATCH LIST: (1) every pixel of a 512x512 footprint has the
patch's own split (so a centre is >= 2.56 km from any axis-aligned split boundary); (2) the split regions are eroded
by BUFFER_PX first, so a footprint edge is >= 640 m from any pixel of another split.

Outputs: $BULK_ROOT/frames10/<F>/m6_split_v1_role.tif (uint8: 0 not owned / no block, 1 train, 2 val, 3 test,
         4 buffer -- owned but excluded from every patch), <case_study>/tables/m6_split_v1_{blocks,composition}.csv,
         m6_split_v1_patches.csv, m6_split_v1_manifest.json
"""
from __future__ import annotations
import argparse, json, time
import numpy as np, pandas as pd, rasterio
from scipy import ndimage
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
VERSION = "m6_split_v1"
FRAMES = ("B1", "B2")
OWNER_PRIORITY = ("B2", "B1")          # first listed frame owns overlap pixels
BLOCK_M = 10_000.0
BUFFER_PX = 64                         # 640 m
PATCH, STRIDE = 512, 128
SEED = 20260923
MAX_DRAWS = 20000
SHARE = dict(test=0.20, val=0.15)
RULE = dict(test_min=0.15, test_max=0.45, val_min=0.08, train_min=0.35)
P73 = {1: "WATER", 2: "CROPLAND", 3: "GRASS_LOW_VEGETATION", 4: "FOREST", 5: "SHRUB", 6: "WETLAND_REED",
       7: "BUILT_UP", 8: "BARE_SAND", 9: "OTHER", 10: "UNCERTAIN"}
PX_KM2 = 1e-4
#: D1 FINAL EVALUATION DESIGN (maintainer, 2026-09-23) -- frozen here, before any M6 arm is trained
D1 = dict(
    primary_A=dict(name="DRY CROPLAND false-flood suppression", stratum="v002 NON_FLOOD x p73 CROPLAND",
                   metrics=["FP_area_km2", "FP_rate = FP / evaluated dry cropland area", "n_FP_components",
                            "area in large isolated field-like components"]),
    primary_B=dict(name="FLOODED OPEN LOW VEGETATION", stratum="v002 FLOOD x p73 (CROPLAND u GRASS_LOW_VEGETATION)",
                   metrics=["recall", "IoU", "FN_area_km2", "component recovery"]),
    secondary=dict(name="FLOODED CROPLAND only", flag="LOW-N / LOW-POWER: no strong conclusion from it alone",
                   metrics=["recall", "FN_area_km2", "n_reference_components", "n_recovered"]),
    other=dict(WETLAND_REED=["precision", "recall", "IoU", "fragmentation"], BUILT_UP=["FP_area_km2", "precision"],
               BARE_SAND=["FP_area_km2"], GLOBAL=["F1", "IoU", "PR-AUC (secondary only)"],
               CROPLAND_precision="additional only (few positives)"),
    comparison="same blocks for every arm; paired spatial-block bootstrap CI")


def read(fid, name, band=1):
    with rasterio.open(OUT / fid / name) as s:
        return s.read(band)


def p73_10m(fid, F):
    """Frozen p73 (20 m) onto this frame's 10 m lattice by exact 2x2 replication (the grids nest)."""
    with rasterio.open(OUT / fid / "p73_rf20" / "surface_class_20m.tif") as s:
        c = s.read(1); t = s.transform
    r0 = int(round((F["transform"].f - t.f) / 10.0)); c0 = int(round((t.c - F["transform"].c) / 10.0))
    out = np.full((F["ny"], F["nx"]), 255, np.uint8)
    up = np.repeat(np.repeat(c, 2, 0), 2, 1)
    h, w = min(up.shape[0], F["ny"] - r0), min(up.shape[1], F["nx"] - c0)
    out[r0:r0 + h, c0:c0 + w] = up[:h, :w]
    return out


def main():
    global VERSION, BLOCK_M
    ap = argparse.ArgumentParser(); ap.add_argument("--inventory", action="store_true")
    ap.add_argument("--block-m", type=float, default=BLOCK_M, help="block size in metres; 10000 = the frozen m6_split_v1; other values write m6_split_sNN (block-size sensitivity, never replaces v1)")
    a = ap.parse_args()
    if abs(a.block_m - 10_000.0) > 1e-6:
        BLOCK_M = a.block_m; VERSION = "m6_split_s" + f"{a.block_m / 1000:g}".replace(".", "p")
        print(f"BLOCK-SIZE SENSITIVITY split: {VERSION} (block {BLOCK_M:.0f} m); m6_split_v1 untouched", flush=True)
    G = {f: CG.frame_grid(f) for f in FRAMES}
    # global canvas on the shared lattice
    x0 = min(G[f]["transform"].c for f in FRAMES); y1 = max(G[f]["transform"].f for f in FRAMES)
    off = {f: (int(round((y1 - G[f]["transform"].f) / 10)), int(round((G[f]["transform"].c - x0) / 10))) for f in FRAMES}
    for f in FRAMES:
        assert (y1 - G[f]["transform"].f) % 10 == 0 and (G[f]["transform"].c - x0) % 10 == 0, "frames not on one lattice"
    ny = max(off[f][0] + G[f]["ny"] for f in FRAMES); nx = max(off[f][1] + G[f]["nx"] for f in FRAMES)
    owner = np.zeros((ny, nx), np.uint8)                      # 0 none, 1 B1, 2 B2
    code = {"B1": 1, "B2": 2}
    for f in reversed(OWNER_PRIORITY):                        # later (higher priority) overwrite
        r, c = off[f]; owner[r:r + G[f]["ny"], c:c + G[f]["nx"]] = code[f]
    # global 10 km block ids
    gx = x0 + 10.0 * np.arange(nx); gy = y1 - 10.0 * np.arange(ny)
    bcol = np.floor(gx / BLOCK_M).astype("i8"); brow = np.floor(gy / BLOCK_M).astype("i8")

    # per-frame strata on owned pixels
    rows = []
    strata_px = {}
    for f in FRAMES:
        F = G[f]; r, c = off[f]
        own = owner[r:r + F["ny"], c:c + F["nx"]] == code[f]
        y = read(f, "m6_labels_v002.tif", 1)
        ev = read(f, "s1_change.tif", 14)                    # n_valid_event
        y = np.where(own & (ev > 0), y, 255)                  # no event observation -> unavailable, never dry
        p = p73_10m(f, F)
        fl, dr = y == 1, y == 0
        bnd = fl & ndimage.binary_dilation(dr, iterations=3)
        S = dict(FLOODED_CROPLAND=fl & (p == 2), DRY_CROPLAND=dr & (p == 2), FLOODED_WETLAND=fl & (p == 6),
                 FLOODED_OPEN_LOW_VEGETATION=fl & np.isin(p, (2, 3)),
                 DRY_WETLAND_OR_VEGETATION=dr & np.isin(p, (3, 4, 5, 6)), BUILT_UP=own & (p == 7),
                 BARE_SAND=own & (p == 8), FLOOD_BOUNDARY=bnd, FLOOD=fl, NON_FLOOD=dr, IGNORE=own & (y == 255),
                 OWNED=own)
        bid = brow[r:r + F["ny"], None] * 100000 + bcol[None, c:c + F["nx"]]
        for k, m in S.items():
            u, n = np.unique(bid[m], return_counts=True)
            for b_, n_ in zip(u, n):
                rows.append(dict(frame=f, block=int(b_), stratum=k, px=int(n_)))
        strata_px[f] = dict(bid=bid, own=own)
    Bk = pd.DataFrame(rows).groupby(["block", "stratum"]).px.sum().unstack(fill_value=0)
    Bk = Bk[Bk.OWNED > 0]
    REQ = ["DRY_CROPLAND", "FLOODED_OPEN_LOW_VEGETATION", "FLOODED_WETLAND", "DRY_WETLAND_OR_VEGETATION",
           "FLOOD_BOUNDARY"]
    LOWN = ["FLOODED_CROPLAND"]                               # required only to be present in TEST
    tot = Bk[REQ + LOWN].sum()
    print(f"{len(Bk)} owned 10 km blocks; stratum totals km2: " +
          ", ".join(f"{k} {v * PX_KM2:.1f}" for k, v in tot.items()), flush=True)
    print("blocks carrying each stratum: " + ", ".join(f"{k} {(Bk[k] > 0).sum()}" for k in REQ + LOWN), flush=True)
    if a.inventory:
        return

    # ---- seeded draws; first acceptable one wins ------------------------------------------------------------------
    rng = np.random.default_rng(SEED); blocks = Bk.index.to_numpy(); nb = len(blocks)
    n_te, n_va = int(round(SHARE["test"] * nb)), int(round(SHARE["val"] * nb))
    chosen = None
    for draw in range(MAX_DRAWS):
        perm = rng.permutation(blocks)
        te, va, tr = set(perm[:n_te]), set(perm[n_te:n_te + n_va]), set(perm[n_te + n_va:])
        sh = {k: {s_: Bk.loc[list(ss), k].sum() / max(tot[k], 1) for s_, ss in (("test", te), ("val", va), ("train", tr))}
              for k in REQ + LOWN}
        if all(RULE["test_min"] <= sh[k]["test"] <= RULE["test_max"] and sh[k]["val"] >= RULE["val_min"]
               and sh[k]["train"] >= RULE["train_min"] for k in REQ) and all(sh[k]["test"] > 0 for k in LOWN):
            chosen = (draw, te, va, tr, sh); break
    if chosen is None:
        raise SystemExit(f"no draw in {MAX_DRAWS} satisfies the D1 composition rule -- revisit the rule, do not hand-pick")
    draw, te, va, tr, sh = chosen
    role_of = {**{b: 1 for b in tr}, **{b: 2 for b in va}, **{b: 3 for b in te}}
    print(f"accepted draw {draw}: blocks train {len(tr)}, val {len(va)}, test {len(te)}", flush=True)

    # ---- per-frame role rasters with the boundary buffer; patches ----------------------------------------------------
    # Roles live on the GLOBAL canvas (both frames' owned pixels), and the buffer is eroded there with a SQUARE
    # structuring element, so it is a Chebyshev distance: corners and the B1/B2 ownership line are covered too.
    gbid = brow[:, None] * 100000 + bcol[None, :]
    graw = np.zeros((ny, nx), np.uint8)
    for b_, r_ in role_of.items():
        graw[(gbid == b_) & (owner > 0)] = r_
    gfinal = graw.copy()
    for r_ in (1, 2, 3):
        m = graw == r_
        core = ndimage.binary_erosion(m, structure=np.ones((3, 3), bool), iterations=BUFFER_PX, border_value=1)
        gfinal[m & ~core] = 4
    patches, comp = [], []
    for f in FRAMES:
        F = G[f]; own = strata_px[f]["own"]; r0f, c0f = off[f]
        final = np.where(own, gfinal[r0f:r0f + F["ny"], c0f:c0f + F["nx"]], 0).astype(np.uint8)
        prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=1, dtype="uint8", nodata=None,
                    crs=CFG.CRS_METRIC, transform=F["transform"], compress="deflate", tiled=True,
                    blockxsize=512, blockysize=512)
        p = OUT / f / f"{VERSION}_role.tif"
        with rasterio.open(p.with_suffix(".tif.part"), "w", **prof) as d:
            d.write(final, 1); d.set_band_description(1, "m6_split_v1_role")
            d.update_tags(codes="0 not owned, 1 train, 2 val, 3 test, 4 buffer (owned, excluded from patches)",
                          owner_priority="|".join(OWNER_PRIORITY), block_m=str(BLOCK_M), buffer_px=str(BUFFER_PX),
                          seed=str(SEED), draw=str(draw), producer="p84_m6_split_b1b2.py")
        p.with_suffix(".tif.part").replace(p)
        y = read(f, "m6_labels_v002.tif", 1)
        ev = read(f, "s1_change.tif", 14)
        y = np.where(own & (ev > 0), y, 255)
        half = PATCH // 2
        for r in range(half, F["ny"] - half + 1, STRIDE):
            for c in range(half, F["nx"] - half + 1, STRIDE):
                w = final[r - half:r + half, c - half:c + half]
                r_ = int(w[0, 0])
                if r_ not in (1, 2, 3) or not (w == r_).all():
                    continue
                yy = y[r - half:r + half, c - half:c + half]
                n1, n0 = int((yy == 1).sum()), int((yy == 0).sum())
                if n1 + n0 == 0 or (ev[r - half:r + half, c - half:c + half] > 0).mean() < 0.5:
                    continue
                patches.append(dict(frame=f, row=r, col=c, split={1: "train", 2: "val", 3: "test"}[r_],
                                    flood_px=n1, nonflood_px=n0))
        for r_, nm in ((1, "train"), (2, "val"), (3, "test"), (4, "buffer")):
            m = final == r_
            comp.append(dict(frame=f, split=nm, area_km2=round(float(m.sum()) * PX_KM2, 1),
                             FLOOD_km2=round(float((m & (y == 1)).sum()) * PX_KM2, 2),
                             NON_FLOOD_km2=round(float((m & (y == 0)).sum()) * PX_KM2, 2),
                             IGNORE_km2=round(float((m & (y == 255)).sum()) * PX_KM2, 2)))
    P = pd.DataFrame(patches); C = pd.DataFrame(comp)
    # ---- machine check of both anti-leakage guarantees on the frozen patch list -----------------------------------
    half = PATCH // 2
    for f in FRAMES:
        with rasterio.open(OUT / f / f"{VERSION}_role.tif") as s:
            fr = s.read(1)
        r0f, c0f = off[f]
        for q in P[P.frame == f].itertuples():
            r_ = {"train": 1, "val": 2, "test": 3}[q.split]
            fp = fr[q.row - half:q.row + half, q.col - half:q.col + half]
            assert (fp == r_).all(), f"{f} patch {q.row},{q.col}: footprint not pure {q.split}"
            R, Cc = q.row + r0f, q.col + c0f                    # footprint centre on the global canvas, both frames
            wide = graw[max(R - half - BUFFER_PX, 0):R + half + BUFFER_PX,
                        max(Cc - half - BUFFER_PX, 0):Cc + half + BUFFER_PX]
            assert not np.isin(wide, [x for x in (1, 2, 3) if x != r_]).any(), \
                f"{f} patch {q.row},{q.col}: another split within {BUFFER_PX} px of the footprint"
    print(f"anti-leakage asserted on {len(P)} patches: pure footprints, >= {BUFFER_PX * 10} m to any other split",
          flush=True)
    for sp in ("train", "val", "test"):
        if not (P.split == sp).any():
            raise SystemExit(f"{sp}: no patch survives the buffer -- do not proceed with an empty split")
    T = CFG.TABLES
    Bk.assign(role=[{1: "train", 2: "val", 3: "test"}[role_of[b]] for b in Bk.index]).to_csv(T / f"{VERSION}_blocks.csv")
    strat = pd.DataFrame([dict(stratum=k, total_km2=round(tot[k] * PX_KM2, 2),
                               **{f"{s_}_share": round(sh[k][s_], 3) for s_ in ("train", "val", "test")},
                               **{f"{s_}_km2": round(sh[k][s_] * tot[k] * PX_KM2, 2) for s_ in ("train", "val", "test")})
                          for k in REQ + LOWN])
    C.to_csv(T / f"{VERSION}_composition.csv", index=False)
    strat.to_csv(T / f"{VERSION}_strata.csv", index=False)
    P.to_csv(T / f"{VERSION}_patches.csv", index=False)
    man = dict(version=VERSION, status="FROZEN", created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               frames=FRAMES, overlap_owner="B2", owner_priority=OWNER_PRIORITY,
               ownership_rule="each physical 10 m pixel has exactly one source representation: B2 owns the B1/B2 "
                              "overlap (B1 there is input context only, IGNORE in loss and metrics)",
               anti_leakage="pure 512x512 footprints (centre >= 2.56 km from axis-aligned split boundaries) + "
                            f"{BUFFER_PX * 10} m eroded buffer; both asserted on the frozen patch list",
               selection_reads="m6_labels_v002 + frozen p73 only; never U0/U1 scores, model errors or target metrics",
               low_n_strata=LOWN,
               d1_final=D1, block_m=BLOCK_M, buffer_px=BUFFER_PX,
               patch=PATCH, stride=STRIDE, seed=SEED, accepted_draw=draw, block_share_target=SHARE, rule=RULE,
               required_strata=REQ, labels="m6_labels_v002 band 1, restricted to owned pixels with >= 1 S1 event",
               strata_source="p73 RF20 FROZEN (composition check only) x m6_labels_v002",
               n_blocks=dict(train=len(tr), val=len(va), test=len(te)),
               n_patches=P.split.value_counts().to_dict(),
               rule_for_every_arm="U0d, U0z, U1, U2 ... use exactly these role rasters and this patch list")
    (T / f"{VERSION}_manifest.json").write_text(json.dumps(man, indent=1, default=str))
    print(C.to_string(index=False)); print(strat.to_string(index=False))
    print(f"patches: {P.split.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
