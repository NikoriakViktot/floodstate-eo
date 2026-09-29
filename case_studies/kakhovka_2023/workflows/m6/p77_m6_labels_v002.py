# New in floodstate-eo, 2026-09-23. STATUS: ACTIVE. Supersedes label contract v001 for every context-model ablation.
# 2026-09-29 (review F09/F10): `--m2-tag _notrace` reads the M2 masks of the model without the post-event TRACE window and
# the inner out-of-fold thresholds, and writes <VERSION><tag>.tif (the v002 rule on the corrected M2, the input of v004);
# the guard now forbids 'trace' except in that explicit variant tag. Defaults reproduce v002 unchanged.
"""P77 -- m6_labels_v002: three-state weak supervision whose construction reads NO land-cover semantics.

WHY A NEW VERSION. Contract v001 (built inside p75) set FLOOD = p60 positive AND S1 peak water AND
p69b_semantic_state in {1..5}; p69b is BASE_CLASS x M2, so BASE_CLASS decided part of the target (it excluded
UNCERTAIN_BASE_STATE cells and ranked the labels alone at AUC 0.955). Any model later given pre-event surface context
would then be scored against a target that already encodes that context. v002 removes land cover from the target
entirely; land cover may be used only AFTER the labels are frozen, for stratification and diagnosis.

WHAT IT READS -- and nothing else (enforced by ALLOWED + FORBIDDEN below, recorded in the output's tags):
    labels.tif        p60: S1 peak water (>= 2 of 06-09/06-13/06-14), pre-breach land (S1 dry in every observed
                      pre-breach event, pre-breach S2 water frequency < 20 %), post-breach dryness counts
    flood_central.tif p68: M2 optical decision at the frozen central threshold T50 (cand_score >= 0.5358)
    flood_possible.tif p68: M2 at the most permissive threshold of the frozen envelope (for stable-dry agreement)
    per_scene_water.npz  the frame's June S1 cache, peak dates only (as p75)
FORBIDDEN: p69a / BASE_CLASS, p69b, p73, WorldCover, Dynamic World, HAND, UNOSAT, TRACE, any U-Net output.

THE RULE
    FLOOD (1)      p60 positive AND S1 peak water AND M2 central flood                 -- two sensors agree
    NON_FLOOD (0)  p60 negative (dry in every observed post-breach S1 event, >= 6 observed) AND M2 does NOT call
                   flood even at the most permissive frozen threshold (or has no optical support: then S1 alone,
                   recorded as n_supporting_sources = 1)
    IGNORE (255)   everything else: sensor disagreement, insufficient observation, and the DISPUTED population
                   (S1 peak water that M2 does not call at T50) -- kept out of supervision as the challenge set.
Relative to v001 the only substantive changes are (i) no BASE_CLASS condition on FLOOD, (ii) a p60 negative that
M2 contradicts becomes IGNORE instead of NON_FLOOD. Both are measured and reported against v001, not assumed small.

THESE ARE STILL WEAK LABELS. They are training supervision, not an independent evaluation reference: M2 and S1 are
the same evidence families a model may be given as input. Real-world accuracy needs observations that took no part
in constructing them.

Outputs: $BULK_ROOT/frames10/<F>/m6_labels_v002.tif (uint8, 7 bands, see BANDS)
         <case_study>/tables/p77_labels_v002_summary.csv
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
JUNE = {"B1": "ZONE_4_FLOODWAY_june2023_s32", "B2": "ZONE_2_KHERSON_DELTA_flood_june2023"}
PEAK = ("2023-06-09", "2023-06-13", "2023-06-14")
VERSION = "m6_labels_v002"
BANDS = ("label", "evidence_s1_n_pos_peak", "evidence_m2", "evidence_external", "stable_dry_n_post_obs",
         "n_supporting_sources", "disputed")
#: evidence_m2 codes: 0 no flood even at the most permissive threshold, 1 flood only at permissive thresholds,
#: 2 flood at T50 (central), 255 no optical prediction support
ALLOWED = re.compile(r"(labels\.tif|flood_central(_notrace)?\.tif|flood_possible(_notrace)?\.tif|per_scene_water\.npz)$")
FORBIDDEN = re.compile(r"p69a|p69b|base_class|p73|worldcover|wc_20|dw_20|dynamic_world|hand|unosat|(?<!_no)trace|u0_",
                       re.IGNORECASE)
M2_TAG = ""                                                                  # set by --m2-tag
_opened: list[str] = []


def _guard(p: Path) -> Path:
    s = str(p)
    if FORBIDDEN.search(Path(s).name) or not ALLOWED.search(s):
        raise SystemExit(f"{VERSION}: refusing to read {s} -- not an allowed label input")
    _opened.append(s)
    return p


def read_band(fid, name, band=1):
    with rasterio.open(_guard(OUT / fid / name)) as s:
        return s.read(band), s.nodata


def s1_peak(fid, F):
    z = np.load(_guard(CFG.S1_CACHE / JUNE[fid] / "per_scene_water.npz"), allow_pickle=True)
    shp = tuple(int(v) for v in z["shape"]); cell = float(z["cell"])
    tr = from_origin(float(z["x0"]), float(z["y1"]), cell, cell); wet = np.zeros(shp, bool)
    for k in [k for k in z.keys() if k[:4] == "2023" and not k.startswith("valid_")]:
        if k[:10] in PEAK:
            w = np.unpackbits(z[k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
            v = np.unpackbits(z["valid_" + k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
            wet |= (w & v)
    d = np.zeros((F["ny"], F["nx"]), "u1")
    reproject(source=wet.astype("u1"), destination=d, src_transform=tr, src_crs=CFG.CRS_METRIC,
              dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest,
              src_nodata=0, dst_nodata=0)
    return d.astype(bool)


def build(fid):
    F = CG.frame_grid(fid)
    lab, _ = read_band(fid, "labels.tif", 1)
    npos, _ = read_band(fid, "labels.tif", 3)            # p60 n_pos_peak
    npost, _ = read_band(fid, "labels.tif", 4)           # p60 n_post_obs
    cen, cen_nd = read_band(fid, f"flood_central{M2_TAG}.tif")
    pos, pos_nd = read_band(fid, f"flood_possible{M2_TAG}.tif")
    s1w = s1_peak(fid, F)
    m2_ok = (cen != 255) & (pos != 255)
    m2 = np.full(lab.shape, 255, np.uint8)
    m2[m2_ok & (pos == 0)] = 0; m2[m2_ok & (pos == 1) & (cen == 0)] = 1; m2[m2_ok & (cen == 1)] = 2

    y = np.full(lab.shape, 255, np.uint8)
    flood = (lab == 1) & s1w & (m2 == 2)
    nonflood = (lab == 0) & (m2 != 1) & (m2 != 2)
    disputed = s1w & m2_ok & (m2 != 2)
    y[nonflood] = 0; y[flood] = 1; y[disputed] = 255
    nsup = np.zeros(lab.shape, np.uint8)
    nsup[flood] = 2
    nsup[nonflood & (m2 == 0)] = 2; nsup[nonflood & (m2 == 255)] = 1
    stable = np.where((lab == 0) & (npost >= 0), np.minimum(npost, 254), 255).astype("u1")
    ext = np.full(lab.shape, 255, np.uint8)             # no external/reference observation enters v002

    prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=len(BANDS), dtype="uint8", nodata=None,
                crs=CFG.CRS_METRIC, transform=F["transform"], compress="deflate", tiled=True,
                blockxsize=512, blockysize=512)
    p = OUT / fid / f"{VERSION}{M2_TAG}.tif"
    with rasterio.open(p.with_suffix(".tif.part"), "w", **prof) as d:
        for i, (nm, arr) in enumerate(zip(BANDS, (y, np.where(npos < 0, 255, np.clip(npos, 0, 254)).astype("u1"), m2, ext, stable, nsup,
                                                    disputed.astype("u1"))), 1):
            d.write(arr, i); d.set_band_description(i, nm)
        d.update_tags(version=VERSION + M2_TAG, codes="label: 1 FLOOD, 0 NON_FLOOD, 255 IGNORE", m2_variant=M2_TAG or "original (84 features incl. TRACE)",
                      inputs_read=json.dumps(sorted(set(_opened))),
                      forbidden_not_read="p69a/BASE_CLASS, p69b, p73, WorldCover, Dynamic World, HAND, UNOSAT, TRACE",
                      meaning="weak supervision, NOT ground truth and NOT an independent evaluation reference",
                      producer="p77_m6_labels_v002.py")
    p.with_suffix(".tif.part").replace(p)
    PX = 1e-4
    summ = dict(frame=fid, flood_km2=round(float(flood.sum()) * PX, 2),
                nonflood_km2=round(float(nonflood.sum()) * PX, 2),
                ignore_km2=round(float((y == 255).sum()) * PX, 2),
                disputed_km2=round(float(disputed.sum()) * PX, 2),
                nonflood_s1_only_km2=round(float((nonflood & (m2 == 255)).sum()) * PX, 2),
                prevalence=round(float(flood.sum()) / max(float(flood.sum() + nonflood.sum()), 1), 4))
    print(f"{fid}: " + ", ".join(f"{k} {v}" for k, v in summ.items() if k != "frame"), flush=True)
    return summ


def main():
    global M2_TAG
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=["B2", "B1"])
    ap.add_argument("--m2-tag", default="", choices=["", "_notrace"], help="M2 mask variant (p68 --tag)"); a = ap.parse_args()
    M2_TAG = a.m2_tag
    S = [build(fid) for fid in a.frames]
    pd.DataFrame(S).to_csv(CFG.TABLES / f"p77_labels_v002_summary{M2_TAG}.csv", index=False)
    print("-> <case_study>/tables/p77_labels_v002_summary.csv  (compare with v001: p77b_labels_v002_vs_v001.py)")


if __name__ == "__main__":
    main()
