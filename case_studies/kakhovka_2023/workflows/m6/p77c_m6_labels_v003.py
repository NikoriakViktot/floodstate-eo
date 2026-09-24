# New in floodstate-eo, 2026-09-24. STATUS: CANDIDATE (not frozen; decision pending). v002 and its arms stay frozen.
"""P77c -- m6_labels_v003: EVENT-ATTRIBUTION supervision ("did water APPEAR because of the event?").

WHY. The p89 audit found that v002 contains ZERO labelled pixels with pre-breach water: p60 keeps only land that was
dry in every observed pre-breach S1 event. A model can therefore never be supervised on "water that was already there
before 06-06 is not event flooding", and any pre-event-water input (U2b) would test nothing. The literature separates
event flooding from pre-existing / permanent / seasonal reference water explicitly; v003 does the same.

CLASSES (binary for training; the negative SUBTYPE is kept for evaluation)
    1   EVENT_FLOOD                 = v002 FLOOD, unchanged (dry pre, wet at peak, S1 + M2 agree)
    0   CONFIDENT_NON_FLOOD
          subtype 1 dry_negative              = v002 NON_FLOOD, unchanged
          subtype 2 preexisting_water_negative = water BEFORE the event, by CONSENSUS (below)
    255 IGNORE / UNKNOWN            everything else, incl. a 20 m band along every pre-water boundary (mixed pixels)
                                    and any conflict between sources

PRE-EXISTING WATER CONSENSUS -- deliberately broader than the U2b input feature, to avoid circularity. The feature
W_pre (U2b) is computed from S1 06-01/06-02 only. The label additionally REQUIRES optical agreement, so it cannot be
reproduced from the feature:
    rule S1+S2: S1 water on 06-01 and/or 06-02 with no dry observation on either date
                AND (S2 MNDWI > 0 on any valid S2 date 2023-05-01..06-05  OR  S2 pre-water frequency >= 20 %)
    rule PERM : S2 pre-water frequency >= 50 % (2022..2023 record) AND no S1 dry observation on 06-01/06-02
    conflict  : S1 water on 06-01/02 but S2 observed dry on every valid late-pre date -> IGNORE
Sources read: labels.tif (p60 incl. pre-water frequency), m6_labels_v002.tif, the June S1 per_scene_water.npz,
per-date S2 indices/<date>.tif + _valid.tif. NO land cover (p69a/p69b/p73/WorldCover), NO HAND, NO model output.
B2 has no S2 acquisition in 2023-05-01..06-05, so there the optical leg is the multi-year frequency only -- recorded.

Outputs: $BULK_ROOT/frames10/<F>/m6_labels_v003.tif (band 1 label, band 2 negative subtype 0/1/2, band 3 source
         bits: 1 S1_0601 wet, 2 S1_0602 wet, 4 S2 late-pre wet, 8 S2 freq>=20, 16 S2 freq>=50, 32 boundary-ignored,
         64 conflict), <case_study>/tables/p77c_labels_v003_summary.csv
"""
from __future__ import annotations
import argparse, json
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from scipy import ndimage
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
VERSION = "m6_labels_v003"
JUNE = {"B1": "ZONE_4_FLOODWAY_june2023_s32", "B2": "ZONE_2_KHERSON_DELTA_flood_june2023"}
S1_PRE = ("2023-06-01", "2023-06-02")
S2_LATE = ("2023-05-01", "2023-06-05")
BOUNDARY_PX = 2                                   # 20 m band along every pre-water boundary -> IGNORE
PX = 1e-4


def s1_pre(fid, F):
    """(wet, observed) per pre-breach June date on the frame lattice (nearest from the 20 m cache grid)."""
    z = np.load(CFG.S1_CACHE / JUNE[fid] / "per_scene_water.npz", allow_pickle=True)
    shp = tuple(int(v) for v in z["shape"]); tr = from_origin(float(z["x0"]), float(z["y1"]), float(z["cell"]),
                                                              float(z["cell"]))
    out = {}
    for k in [k for k in z.keys() if k[:10] in S1_PRE and not k.startswith("valid_")]:
        w = np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype("u1")
        v = np.unpackbits(z["valid_" + k], count=shp[0] * shp[1]).reshape(shp).astype("u1")
        res = []
        for a in (w & v, v):
            d = np.zeros((F["ny"], F["nx"]), "u1")
            reproject(a, d, src_transform=tr, src_crs=CFG.CRS_METRIC, dst_transform=F["transform"],
                      dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest)
            res.append(d.astype(bool))
        out[k[:10]] = tuple(res)
    return out


def s2_late(fid):
    """(any valid late-pre S2 date says water, any valid late-pre S2 date observed, dates used)."""
    idir = OUT / fid / "indices"
    dates = sorted(p.stem for p in idir.glob("2023-0*.tif") if not p.stem.endswith("_valid")
                   and S2_LATE[0] <= p.stem <= S2_LATE[1])
    wet = obs = None
    for d in dates:
        with rasterio.open(idir / f"{d}.tif") as s:
            m = s.read(list(s.descriptions).index("MNDWI") + 1)
        with rasterio.open(idir / f"{d}_valid.tif") as s:
            v = s.read(1) == 1
        w = v & (m != -32768) & (m > 0)
        wet = w if wet is None else (wet | w); obs = v if obs is None else (obs | v)
    return wet, obs, dates


def build(fid):
    F = CG.frame_grid(fid)
    with rasterio.open(OUT / fid / "m6_labels_v002.tif") as s:
        y2 = s.read(1)
    with rasterio.open(OUT / fid / "labels.tif") as s:
        wf = s.read(8).astype("f4"); wf[wf < 0] = np.nan
    S1 = s1_pre(fid, F)
    s1_wet = np.zeros(y2.shape, bool); s1_dry = np.zeros(y2.shape, bool)
    bits = np.zeros(y2.shape, np.uint8)
    for i, d in enumerate(S1_PRE):
        w, o = S1[d]; s1_wet |= w; s1_dry |= (o & ~w); bits |= (w.astype("u1") << i)
    s2w, s2o, dates = s2_late(fid)
    if s2w is None:
        s2w = s2o = np.zeros(y2.shape, bool)
    f20, f50 = np.nan_to_num(wf) >= 20, np.nan_to_num(wf) >= 50
    bits |= (s2w.astype("u1") << 2) | (f20.astype("u1") << 3) | (f50.astype("u1") << 4)
    rule_s1s2 = s1_wet & ~s1_dry & (s2w | f20)
    rule_perm = f50 & ~s1_dry
    conflict = s1_wet & ~s1_dry & s2o & ~s2w & ~f20
    pre = (rule_s1s2 | rule_perm) & ~conflict
    ring = pre & ~ndimage.binary_erosion(pre, iterations=BOUNDARY_PX, border_value=1)
    core = pre & ~ring
    bits |= (ring.astype("u1") << 5) | (conflict.astype("u1") << 6)

    y = np.full(y2.shape, 255, np.uint8); sub = np.zeros(y2.shape, np.uint8)
    y[y2 == 0] = 0; sub[y2 == 0] = 1
    y[y2 == 1] = 1
    newneg = core & (y2 == 255)                              # never overrides a v002 label (they are disjoint anyway)
    y[newneg] = 0; sub[newneg] = 2
    assert not (core & (y2 == 1)).any(), "pre-existing water overlaps v002 FLOOD -- contract violated"
    prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=3, dtype="uint8", nodata=None,
                crs=CFG.CRS_METRIC, transform=F["transform"], compress="deflate", tiled=True,
                blockxsize=512, blockysize=512)
    p = OUT / fid / f"{VERSION}.tif"
    with rasterio.open(p.with_suffix(".tif.part"), "w", **prof) as o:
        for b, (arr, nm) in enumerate(((y, "label"), (sub, "negative_subtype"), (bits, "source_bits")), 1):
            o.write(arr, b); o.set_band_description(b, nm)
        o.update_tags(version=VERSION, codes="label 1 EVENT_FLOOD, 0 CONFIDENT_NON_FLOOD, 255 IGNORE; subtype 1 "
                      "dry_negative, 2 preexisting_water_negative",
                      s2_late_dates=json.dumps(dates), s1_pre_dates=json.dumps(S1_PRE),
                      inputs="m6_labels_v002, labels.tif (p60 pre-water freq), June S1 per_scene_water, S2 indices",
                      forbidden_not_read="p69a/BASE_CLASS, p69b, p73, WorldCover, HAND, any model output",
                      meaning="weak event-attribution supervision; NOT ground truth", producer="p77c_m6_labels_v003.py")
    p.with_suffix(".tif.part").replace(p)
    r = dict(frame=fid, s2_late_dates="|".join(dates) or "none",
             event_flood_km2=round(float((y == 1).sum()) * PX, 2),
             dry_negative_km2=round(float((sub == 1).sum()) * PX, 2),
             preexisting_water_negative_km2=round(float((sub == 2).sum()) * PX, 2),
             via_rule_s1s2_km2=round(float((newneg & rule_s1s2).sum()) * PX, 2),
             via_rule_perm_only_km2=round(float((newneg & rule_perm & ~rule_s1s2).sum()) * PX, 2),
             boundary_ignored_km2=round(float(ring.sum()) * PX, 2), conflict_ignored_km2=round(float(conflict.sum()) * PX, 2),
             s1_pre_wet_km2=round(float(s1_wet.sum()) * PX, 2),
             s1_pre_wet_not_labelled_km2=round(float((s1_wet & ~newneg).sum()) * PX, 2))
    print(r, flush=True)
    return r


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=["B1", "B2"]); a = ap.parse_args()
    pd.DataFrame([build(f) for f in a.frames]).to_csv(CFG.TABLES / "p77c_labels_v003_summary.csv", index=False)


if __name__ == "__main__":
    main()
