# Provenance: SWOT-DNIPRO scripts/p62_label_freeze.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: ACTIVE -- freezes labels.tif.
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P62 -- freeze the weak reference labels for B1 and B2, with confidence tiers. B3 is prediction-only.

STATUS, NOT PROMOTION. These stay WEAK_REFERENCE (SRC-45). Freezing fixes which cells supervise and score M0-M5; it
does not upgrade an S1 rule into ground truth, and nothing here may be reported as validated against field data.

CONFIDENCE TIERS. B1 and B2 overlap geographically but their labels come from different S1 caches (ZONE_4_s32,
ZONE_2) under an identical rule, so on shared ground the two sources can be compared directly -- and they agree on
positives at IoU 0.606, which is good for weak labels and far from perfect. That residual noise is recorded per cell
instead of being averaged away:

    CONSENSUS_POSITIVE   both sources observed the cell and both call it positive
    CONSENSUS_NEGATIVE   both observed it and both call it negative
    SOURCE_CONFLICT      both observed it and one says positive while the other says negative
    SINGLE_SOURCE        only one source supplies supervision here (including: the other observed it but left it
                         unlabelled, which is an absence of evidence, not a contradiction)
    UNOBSERVED           no S1 observation

Evaluation then runs in two layers over the SAME population for every model:
    PRIMARY    the consensus subset -- where two independent caches agree
    SECONDARY  all admissible weak labels of B1 and B2

B3 IS EXCLUDED FROM BOTH, positives and negatives alike. Its positive class failed the label gate (p61), and pooling
its 31.2 million easy negatives into a shared F1/AP would raise the score by arithmetic rather than by skill. B3 is
predicted wall-to-wall and reported qualitatively, as a negative-consistency diagnostic.

Outputs: $BULK_ROOT/frames10/<FID>/label_confidence.tif, outputs/tables/p62_label_freeze_{record,tiers}.csv
"""
from __future__ import annotations
import hashlib, itertools, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.windows import from_bounds
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
PX = CG.CELL * CG.CELL / 1e6
FROZEN = ("B1", "B2")                 # B3 is prediction-only: see outputs/planning/20_LABEL_QA_GATE_AND_B3_HOLD.md
TIER = {0: "UNOBSERVED", 1: "SINGLE_SOURCE", 2: "CONSENSUS_NEGATIVE", 3: "CONSENSUS_POSITIVE", 4: "SOURCE_CONFLICT"}


def sha256(p: Path, buf=1 << 24) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while (b := f.read(buf)):
            h.update(b)
    return h.hexdigest()


def main():
    git = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                         text=True).stdout.strip()
    lab = {}
    for fid in FROZEN:
        with rasterio.open(OUT / fid / "labels.tif") as s:
            lab[fid] = s.read(1)

    # ---- tier raster per frozen frame -------------------------------------------------------------------------------
    tiers, rec = [], []
    for fid in FROZEN:
        F = CG.frame_grid(fid)
        L = lab[fid]
        T = np.where(L == -32768, 0, 1).astype("u1")          # observed by this frame's own source -> SINGLE_SOURCE
        for other in FROZEN:
            if other == fid:
                continue
            GA, GB = CG.frame_grid(fid), CG.frame_grid(other)
            x0, x1 = max(GA["x0"], GB["x0"]), min(GA["x1"], GB["x1"])
            y0, y1 = max(GA["y0"], GB["y0"]), min(GA["y1"], GB["y1"])
            if x1 <= x0 or y1 <= y0:
                continue
            # the other frame's labels, read on THIS frame's lattice: both are on the same canonical grid, so the
            # windows line up cell for cell and no resampling is involved
            with rasterio.open(OUT / other / "labels.tif") as s:
                wo = from_bounds(x0, y0, x1, y1, transform=s.transform).round_offsets().round_lengths()
                O = s.read(1, window=wo)
            with rasterio.open(OUT / fid / "labels.tif") as s:
                ws = from_bounds(x0, y0, x1, y1, transform=s.transform).round_offsets().round_lengths()
            r0, c0 = int(ws.row_off), int(ws.col_off)
            h, w = min(int(ws.height), O.shape[0]), min(int(ws.width), O.shape[1])
            O = O[:h, :w]
            sub = L[r0:r0 + h, c0:c0 + w]
            both = (sub != -32768) & (O != -32768)
            t = T[r0:r0 + h, c0:c0 + w]
            t[both & (sub == 0) & (O == 0)] = 2
            t[both & (sub == 1) & (O == 1)] = 3
            t[both & (((sub == 1) & (O == 0)) | ((sub == 0) & (O == 1)))] = 4
            T[r0:r0 + h, c0:c0 + w] = t
        prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=1, dtype="uint8", crs=CFG.CRS_METRIC,
                    transform=F["transform"], compress="deflate", tiled=True, blockxsize=512, blockysize=512,
                    nodata=255, BIGTIFF="IF_SAFER")
        p = OUT / fid / "label_confidence.tif"; part = p.with_suffix(".tif.part")
        with rasterio.open(part, "w", **prof) as dst:
            dst.write(T, 1); dst.set_band_description(1, "confidence_tier")
            dst.update_tags(tiers="|".join(f"{k}={v}" for k, v in TIER.items()),
                            label_status="WEAK_REFERENCE, not ground truth (SRC-45)",
                            primary_population="CONSENSUS_POSITIVE + CONSENSUS_NEGATIVE",
                            secondary_population="every cell of B1/B2 with label 0 or 1",
                            excluded="B3 entirely, positives and negatives alike (p61 label gate)",
                            frozen_at=git, producer="p62_label_freeze.py")
        with rasterio.open(part) as chk:
            assert (chk.height, chk.width) == (F["ny"], F["nx"])
        os.replace(part, p)
        for k, nm in TIER.items():
            n = int((T == k).sum())
            if n:
                tiers.append(dict(frame=fid, tier=nm, n_cells=n, km2=round(n * PX, 2),
                                  pct_of_frame=round(100 * n / T.size, 3)))
        rec.append(dict(frame=fid, kind="labels", file="labels.tif", bytes=(OUT / fid / "labels.tif").stat().st_size,
                        sha256=sha256(OUT / fid / "labels.tif"), git=git, status="FROZEN_WEAK_REFERENCE"))
        rec.append(dict(frame=fid, kind="confidence", file="label_confidence.tif", bytes=p.stat().st_size,
                        sha256=sha256(p), git=git, status="FROZEN_WEAK_REFERENCE"))
        print(f"{fid}: " + ", ".join(f"{TIER[k]} {int((T==k).sum())*PX:,.1f} km2" for k in sorted(TIER)), flush=True)
    rec.append(dict(frame="B3", kind="labels", file="labels.tif",
                    bytes=(OUT / "B3" / "labels.tif").stat().st_size, sha256=sha256(OUT / "B3" / "labels.tif"),
                    git=git, status="LABEL_HOLD_PREDICTION_ONLY"))

    T1 = pd.DataFrame(tiers)
    T1["note"] = "per-frame; the B1/B2 overlap appears in BOTH rows -- see the deduplicated population below"
    T1.to_csv(CFG.TABLES / "p62_label_freeze_tiers.csv", index=False)
    pd.DataFrame(rec).to_csv(CFG.TABLES / "p62_label_freeze_record.csv", index=False)

    # ---- the two evaluation populations, DEDUPLICATED ----------------------------------------------------------------
    # The frames overlap, so the consensus cells of B1 and the consensus cells of B2 are THE SAME GROUND. Summing the
    # per-frame tier areas counts that ground twice -- 25.9 km2 of consensus positives is one patch of Earth, not two.
    # Every cell is therefore counted under exactly one owner: B1 where B1 covers it, otherwise B2. Both frames sit on
    # the same canonical lattice, so ownership is a window test with no resampling and no ambiguity.
    print()
    owned = {}
    for i, fid in enumerate(FROZEN):
        F = CG.frame_grid(fid)
        own = np.ones(lab[fid].shape, bool)
        for prev in FROZEN[:i]:
            GP = CG.frame_grid(prev)
            x0, x1 = max(F["x0"], GP["x0"]), min(F["x1"], GP["x1"])
            y0, y1 = max(F["y0"], GP["y0"]), min(F["y1"], GP["y1"])
            if x1 <= x0 or y1 <= y0:
                continue
            c0 = int(round((x0 - F["x0"]) / CG.CELL)); c1 = int(round((x1 - F["x0"]) / CG.CELL))
            r0 = int(round((F["y1"] - y1) / CG.CELL)); r1 = int(round((F["y1"] - y0) / CG.CELL))
            own[r0:r1, c0:c1] = False           # already counted under the earlier frame
        owned[fid] = own
    with_tier = {}
    for fid in FROZEN:
        with rasterio.open(OUT / fid / "label_confidence.tif") as s_:
            with_tier[fid] = s_.read(1)
    prim_p = sum(float(((with_tier[f] == 3) & owned[f]).sum()) * PX for f in FROZEN)
    prim_n = sum(float(((with_tier[f] == 2) & owned[f]).sum()) * PX for f in FROZEN)
    conf = sum(float(((with_tier[f] == 4) & owned[f]).sum()) * PX for f in FROZEN)
    sec_p = sum(float(((lab[f] == 1) & owned[f]).sum()) * PX for f in FROZEN)
    sec_n = sum(float(((lab[f] == 0) & owned[f]).sum()) * PX for f in FROZEN)
    dupe = sum(float((~owned[f]).sum()) * PX for f in FROZEN)
    print(f"deduplication: {dupe:,.0f} km2 of shared ground assigned to one owner (counted once, not twice)")
    print(f"PRIMARY   consensus: {prim_p:,.1f} km2 positive, {prim_n:,.1f} km2 negative "
          f"(prevalence {prim_p/max(prim_p+prim_n,1e-9):.4f})")
    print(f"SECONDARY all B1+B2: {sec_p:,.1f} km2 positive, {sec_n:,.1f} km2 negative "
          f"(prevalence {sec_p/max(sec_p+sec_n,1e-9):.4f})")
    print(f"CONFLICT  {conf:,.2f} km2 where the two caches contradict each other outright")
    print("\n-> outputs/tables/p62_label_freeze_{record,tiers}.csv")
    print("LABELS FROZEN for B1 and B2 as WEAK_REFERENCE. B3 is prediction-only and is scored in neither layer.")


if __name__ == "__main__":
    main()
