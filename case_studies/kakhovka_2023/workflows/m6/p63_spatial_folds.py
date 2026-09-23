# Provenance: SWOT-DNIPRO scripts/p63_spatial_folds.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: ACTIVE -- spatial block folds (folds.tif; band 5 = 10 km blocks used by p75's split).
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P63 -- ONE global spatial block lattice over the union of B1 and B2, and five outer folds. Built once, frozen.

WHY THIS EXISTS AND WHY IT IS BUILT ONCE. Random CV over spatially autocorrelated data understates prediction error
(Roberts et al. 2017, SRC-46); spatial k-fold is the geodata remedy (Pohjankukka et al. 2017, SRC-47); and the block
size should follow the autocorrelation scale of the predictors rather than a round number (Valavi et al. 2019,
SRC-48). Every model M0-M5 and every pre-baseline uses THESE folds, so a difference between models is never a
difference between partitions.

THE LATTICE IS GLOBAL, NOT PER FRAME. Blocks are defined on absolute EPSG:32636 coordinates -- `floor(x / s)`,
`floor(y / s)` -- so a block straddling the B1/B2 seam is ONE block and cannot land in two different folds. A
per-frame lattice would have let neighbouring cells 10 m apart sit in train and test at once, which is the exact
leak spatial blocking exists to prevent.

OVERLAP IS COUNTED ONCE. B1 and B2 share 1 472 km2. Each cell is owned by B1 where B1 covers it and by B2 otherwise,
so the evaluation population contains every patch of ground exactly once. Without this the shared strip would be
both trained on and tested against itself.

BLOCK SIZE. 5 km is primary: the measured predictor autocorrelation range is about 3.5 km, and 5 km > 3.5 km. The
2 km and 10 km lattices are written alongside it so the sensitivity analysis needs no repartitioning -- block size
is the parameter that matters most in a spatial CV design, so it is reported, not assumed.

FOLD ASSIGNMENT is deterministic and balances the POSITIVE count across folds: blocks are taken in descending order
of positives and each goes to the fold currently holding the fewest. With a prevalence near 0.07 and positives
concentrated in wetland, an unbalanced draw can leave a fold with almost no positives and make its AP meaningless.
This uses the label to define the partition, which is ordinary stratification of the CV design, not leakage: no
model sees a test fold, and the assignment is fixed before any fitting.

WHAT IS NOT HERE. B3 is absent from the population entirely -- positives and negatives alike (p61 label gate).

Outputs: $BULK_ROOT/frames10/<FID>/folds.tif (owner, outer_fold, blk2, blk5, blk10),
         outputs/tables/p63_fold_{summary,blocks,sensitivity_lattices}.csv
"""
from __future__ import annotations
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
PX = CG.CELL * CG.CELL / 1e6
FRAMES = ("B1", "B2")
SIZES = {"blk2": 2000.0, "blk5": 5000.0, "blk10": 10000.0}
PRIMARY = "blk5"
N_OUTER = 5
TIER = {0: "UNOBSERVED", 1: "SINGLE_SOURCE", 2: "CONSENSUS_NEGATIVE", 3: "CONSENSUS_POSITIVE", 4: "SOURCE_CONFLICT"}


def owner_mask(fid, i):
    """True where this frame is the sole owner of the cell (earlier frames win the shared ground)."""
    F = CG.frame_grid(fid)
    own = np.ones((F["ny"], F["nx"]), bool)
    for prev in FRAMES[:i]:
        GP = CG.frame_grid(prev)
        x0, x1 = max(F["x0"], GP["x0"]), min(F["x1"], GP["x1"])
        y0, y1 = max(F["y0"], GP["y0"]), min(F["y1"], GP["y1"])
        if x1 <= x0 or y1 <= y0:
            continue
        c0 = int(round((x0 - F["x0"]) / CG.CELL)); c1 = int(round((x1 - F["x0"]) / CG.CELL))
        r0 = int(round((F["y1"] - y1) / CG.CELL)); r1 = int(round((F["y1"] - y0) / CG.CELL))
        own[r0:r1, c0:c1] = False
    return own


def block_ids(fid, size):
    """Global block index from absolute coordinates, so the lattice is continuous across the frame seam."""
    F = CG.frame_grid(fid)
    xs = F["x0"] + (np.arange(F["nx"]) + 0.5) * CG.CELL
    ys = F["y1"] - (np.arange(F["ny"]) + 0.5) * CG.CELL
    ix = np.floor(xs / size).astype(np.int64)
    iy = np.floor(ys / size).astype(np.int64)
    return (iy[:, None] * 1_000_000 + ix[None, :]).astype(np.int64)


def main():
    lab, own, blk = {}, {}, {}
    for i, fid in enumerate(FRAMES):
        with rasterio.open(OUT / fid / "labels.tif") as s:
            lab[fid] = s.read(1)
        own[fid] = owner_mask(fid, i)
        blk[fid] = {k: block_ids(fid, v) for k, v in SIZES.items()}
        n = int(((lab[fid] >= 0) & (lab[fid] <= 1) & own[fid]).sum())
        print(f"{fid}: {n:,} labelled cells owned here ({n*PX:,.1f} km2)", flush=True)

    # ---- per-block positive / negative counts on the PRIMARY lattice ---------------------------------------------
    rows = []
    for fid in FRAMES:
        m = own[fid] & ((lab[fid] == 0) | (lab[fid] == 1))
        b = blk[fid][PRIMARY][m]; y = lab[fid][m]
        d = pd.DataFrame(dict(block=b, y=y)).groupby("block").agg(n=("y", "size"), pos=("y", "sum"))
        d["frame"] = fid
        rows.append(d.reset_index())
    B = pd.concat(rows).groupby("block").agg(n=("n", "sum"), pos=("pos", "sum"),
                                             frames=("frame", lambda s: "|".join(sorted(set(s))))).reset_index()
    B["neg"] = B.n - B.pos
    print(f"\n{len(B):,} blocks of {SIZES[PRIMARY]/1000:.0f} km hold labelled cells; "
          f"{int((B.pos > 0).sum()):,} contain at least one positive", flush=True)

    # ---- deterministic, positive-balanced assignment of WHOLE blocks ----------------------------------------------
    B = B.sort_values(["pos", "n", "block"], ascending=[False, False, True]).reset_index(drop=True)
    load = np.zeros(N_OUTER, np.int64); loadn = np.zeros(N_OUTER, np.int64)
    fold = np.zeros(len(B), np.int32)
    for i, r in enumerate(B.itertuples()):
        # A block carrying positives goes to the fold with the fewest positives; a block with NONE goes to the fold
        # with the fewest cells. Balancing everything on positives alone leaves the currently-poorest fold permanently
        # poorest -- a zero-positive block never raises its count -- so it absorbs every remaining block. That is not
        # hypothetical: it put 82 of 179 blocks and 988 km2 into fold 1 at prevalence 0.031 against 0.10 elsewhere,
        # and per-fold metrics computed at different prevalences are not comparable (SRC-68).
        if int(r.pos) > 0:
            k = int(np.lexsort((loadn, load))[0])
        else:
            k = int(np.lexsort((load, loadn))[0])
        fold[i] = k + 1; load[k] += int(r.pos); loadn[k] += int(r.n)
    B["outer_fold"] = fold
    B.to_csv(CFG.TABLES / "p63_fold_blocks.csv", index=False)

    f2f = dict(zip(B.block.to_numpy(), B.outer_fold.to_numpy()))
    summ = []
    for fid in FRAMES:
        F = CG.frame_grid(fid)
        m = own[fid] & ((lab[fid] == 0) | (lab[fid] == 1))
        fo = np.zeros((F["ny"], F["nx"]), np.int32)
        bb = blk[fid][PRIMARY]
        uniq = np.unique(bb[m])
        lut = {int(u): int(f2f.get(int(u), 0)) for u in uniq}
        flat = bb[m]
        fo[m] = np.array([lut[int(v)] for v in flat], np.int32) if len(flat) else 0
        prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=5, dtype="int32", crs=CFG.CRS_METRIC,
                    transform=F["transform"], compress="deflate", tiled=True, blockxsize=512, blockysize=512,
                    nodata=0, BIGTIFF="IF_SAFER")
        p = OUT / fid / "folds.tif"; part = p.with_suffix(".tif.part")
        with rasterio.open(part, "w", **prof) as dst:
            for i, (nm, arr) in enumerate([("owner", own[fid].astype(np.int32)), ("outer_fold", fo),
                                           ("blk2", blk[fid]["blk2"].astype(np.int32)),
                                           ("blk5", blk[fid]["blk5"].astype(np.int32)),
                                           ("blk10", blk[fid]["blk10"].astype(np.int32))], 1):
                dst.write(arr, i); dst.set_band_description(i, nm)
            dst.update_tags(primary_block_km=str(SIZES[PRIMARY] / 1000), n_outer_folds=str(N_OUTER),
                            lattice="global, floor(x/s) and floor(y/s) on absolute EPSG:32636 coordinates",
                            overlap_rule="B1 owns the shared ground; B2 owns the rest -- every cell counted once",
                            assignment="whole blocks, deterministic, balanced on positive count",
                            excluded="B3 entirely (p61 label gate)",
                            sensitivity_lattices="blk2 / blk5 / blk10 written so block size needs no repartition",
                            producer="p63_spatial_folds.py")
        with rasterio.open(part) as chk:
            assert chk.count == 5 and (chk.height, chk.width) == (F["ny"], F["nx"])
        os.replace(part, p)

        with rasterio.open(OUT / fid / "label_confidence.tif") as s:
            T = s.read(1)
        for k in range(1, N_OUTER + 1):
            mm = m & (fo == k)
            if not mm.any():
                continue
            summ.append(dict(frame=fid, outer_fold=k, n_cells=int(mm.sum()), km2=round(float(mm.sum()) * PX, 1),
                             n_pos=int((lab[fid][mm] == 1).sum()), n_neg=int((lab[fid][mm] == 0).sum()),
                             prevalence=round(float((lab[fid][mm] == 1).mean()), 4),
                             n_blocks=int(len(np.unique(bb[mm]))),
                             consensus_pos=int((T[mm] == 3).sum()), consensus_neg=int((T[mm] == 2).sum()),
                             conflict=int((T[mm] == 4).sum())))
        print(f"  -> {p.name}", flush=True)

    S = pd.DataFrame(summ)
    tot = S.groupby("outer_fold").agg(km2=("km2", "sum"), n_pos=("n_pos", "sum"), n_neg=("n_neg", "sum"),
                                      n_blocks=("n_blocks", "sum"), consensus_pos=("consensus_pos", "sum"),
                                      consensus_neg=("consensus_neg", "sum")).reset_index()
    tot["prevalence"] = (tot.n_pos / (tot.n_pos + tot.n_neg)).round(4)
    S.to_csv(CFG.TABLES / "p63_fold_summary.csv", index=False)

    # ---- how many blocks each sensitivity lattice would give ------------------------------------------------------
    sens = []
    for k, sz in SIZES.items():
        u = set()
        for fid in FRAMES:
            m = own[fid] & ((lab[fid] == 0) | (lab[fid] == 1))
            u |= set(np.unique(blk[fid][k][m]).tolist())
        sens.append(dict(lattice=k, block_km=sz / 1000, n_blocks_with_labels=len(u),
                         mean_labelled_km2_per_block=round(float(S.km2.sum()) / max(len(u), 1), 3),
                         is_primary=(k == PRIMARY)))
    pd.DataFrame(sens).to_csv(CFG.TABLES / "p63_fold_sensitivity_lattices.csv", index=False)

    print("\nOUTER FOLDS (deduplicated union of B1 and B2):")
    print(tot.to_string(index=False))
    print("\nblock-size lattices available without repartitioning:")
    print(pd.DataFrame(sens).to_string(index=False))
    print("\n-> outputs/tables/p63_fold_{summary,blocks,sensitivity_lattices}.csv")
    print("FOLDS FROZEN. Every model M0-M5 and every pre-baseline uses exactly these.")


if __name__ == "__main__":
    main()
