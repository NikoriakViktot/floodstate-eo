# New in floodstate-eo, 2026-09-30 (maintainer: "the ground should have kept a moisture trace -- check it by the index"). STATUS: ACTIVE. Diagnostic.
"""P95q -- post-event wetness trace of a reconstructed component: did the ground that the reconstruction floods on the peak days keep
a moisture signal after the water left, relative to the same surface next to it that the reconstruction never floods?

Masks (20 m zone grid of the primary reconstruction):
  target          new water of --day inside the box (the component under test), also split by the ensemble probability of the day
                  (P >= 0.95 / 0.50-0.95 / < 0.50, p95e cellprob) and by the reconstructed maximum depth (< 0.5 / 0.5-1.5 / >= 1.5 m);
  control         cells in a ring 2-5 km around the box that are never new water and not pre-breach water (the unflooded neighbour);
  reference       new water of --day elsewhere within 30 km that the first Sentinel-1 scene after --day saw as dark water (observed,
                  multi-day inundation: what a strong flood trace looks like);
  reference_brief new water of --day elsewhere within 30 km that the reconstruction itself drains by that Sentinel-1 date.
Strata (every statistic is per stratum, never pooled): WorldCover 2021 class, and the pre-event NDVI of --pre (bare/sparse < 0.3, where
SWIR and VV respond to the soil; mixed 0.3-0.6; canopy > 0.6, where they respond to the vegetation); and the ground burnt or cleared
between June 2022 and --pre (dNBR = NBR_2022-06-03 - NBR_pre > 0.10, NBR = (B8A - B12)/(B8A + B12)) against the rest ("trees/grass
unburnt"): in the lowland south of Krynky (file names 'kozachi_laheri_lowland') the bare/sparse stratum is a pre-breach fire scar, and its regrowth, not the flood, drives the
largest Sentinel-1 change -- a like-with-like comparison needs the unburnt strata.
Signals:
  1. the 10 m index stacks of p54a (NDVI, NDWI, MNDWI, NDMI, BSI; cloud-free cells), 2022 and 2023;
  2. from the SAFE archives at native 20 m: the SWIR normalized contrast SWIR1112 = (B11 - B12)/(B11 + B12) -- mathematically identical to the
     Sentinel-2 implementation sometimes termed NSMI in the soil-moisture literature (Haubrock's NSMI used ~1800 and ~2120 nm; B11/B12 are
     1610/2190 nm), treated here as a SWIR wetness anomaly whose moisture-like behaviour is checked, not assumed -- with NDMI = (B8A - B11)/
     (B8A + B11), MSI = B11/B8A, NDVI, MNDWI, BSI; 2022 and 2023, and the matched-date year difference I_2023 - I_2022;
  3. Sentinel-1 VV / VH (linear gamma0 of the June 2023 cache, one pipeline, converted to dB): same-relative-orbit pairs before -> after the
     breach (orbit 65: 01 -> 13 and 25 June; orbit 87: 02 -> 14 and 26 June) and the later change of the post-peak scenes (orbit 14: 09 -> 21;
     orbit 167: 08 -> 20 June). No 2022 backscatter is in the cache, so the year difference exists for Sentinel-2 only.
Difference-in-differences: (target - control) after minus (target - control) before; the 2022 season gives the no-flood value of the same
difference; the references show the size of a real trace on the same strata; the co-location test asks whether the SWIR anomaly and the
VV change agree pixel by pixel on bare/sparse ground. Reading: qualitative; a trace of the reference's kind supports the peak inundation,
none argues against it; vegetated strata show canopy water; never a validation.

Outputs (tables/): p95q_moisture_trace_<name>.csv (10 m), p95q_moisture_20m_<name>.csv, p95q_moisture_yearpair_<name>.csv, p95q_moisture_s1_<name>.csv,
         p95q_moisture_s1_pairs_<name>.csv, p95q_moisture_coloc_<name>.csv, p95q_moisture_did_<name>.csv, p95q_moisture_manifest_<name>.json;
         figures/m6_v003A/p95q_moisture_<name>.png (time series), p95q_moisture_maps_<name>.png (anomaly maps).
"""
from __future__ import annotations

import argparse
import json
import re
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform as tf_transform
from scipy import ndimage, stats

from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.io import optical_catalogue as OC
from floodstate_eo.optical import sentinel_preprocess as SP
from floodstate_eo.optical import watermask as WM
from floodstate_eo.optical.truecolour import CLOUD_SCL

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = ROOT / "figures" / "m6_v003A"
ZONE, FRAME, CACHE = "ZONE_4_DAM_TO_KHERSON_FLOODWAY", "B1", "ZONE_4_FLOODWAY_june2023_s32"
WC = {10: "trees", 30: "grass", 40: "cropland", 90: "wetland"}
NDVI_BINS = (("ndvi<0.3 bare/sparse", -1.0, 0.3), ("ndvi0.3-0.6 mixed", 0.3, 0.6), ("ndvi>0.6 canopy", 0.6, 2.0))
IDX10 = ("NDVI", "NDWI", "MNDWI", "NDMI", "BSI")
IDX20 = ("SWIR1112", "NDMI", "MSI", "NDVI", "MNDWI", "BSI", "NBR")
BURN_REF, DNBR_BURNT = "2022-06-03", 0.10                          # dNBR = NBR(BURN_REF) - NBR(--pre) above this = burnt / cleared before the breach
BANDS20 = ("B02", "B03", "B04", "B8A", "B11", "B12")
TILES = ("T36TWS", "T36TVS")                                       # TWS first: it covers the whole box; the window lies south of the T squares
S1_PAIRS = [("2023-06-01_orb65_DES", "2023-06-13_orb65_DES"), ("2023-06-01_orb65_DES", "2023-06-25_orb65_DES"),
            ("2023-06-02_orb87_ASC", "2023-06-14_orb87_ASC"), ("2023-06-02_orb87_ASC", "2023-06-26_orb87_ASC"),
            ("2023-06-09_orb14_ASC", "2023-06-21_orb14_ASC"), ("2023-06-08_orb167_DES", "2023-06-20_orb167_DES")]
YEAR_PAIRS = [("2023-06-05", "2022-06-03"), ("2023-06-20", "2022-06-20"), ("2023-06-25", "2022-06-20"), ("2023-07-03", "2022-07-03"), ("2023-07-08", "2022-07-08")]
MIN_CELLS = 50                                                     # 20 m cells (= 2 ha) below which a stratum of a mask is not reported
REF_KM = 30.0


def tile_of(p: Path) -> str:
    m = re.search(r"_(T36[A-Z]{3})_", p.name); return m.group(1) if m else ""


def read20(zp: Path) -> dict:
    """B02/B03/B04/B8A/B11/B12/SCL at native 20 m from a SAFE zip; reflectance with the BOA offset of the scene's own metadata."""
    meta = SP.read_metadata(zp)
    with zipfile.ZipFile(str(zp)) as z:
        names = z.namelist()
    out = {}
    for b in BANDS20 + ("SCL",):
        m = WM._find(names, b, "20m")
        if m is None:
            raise RuntimeError(f"{zp.name}: missing {b}_20m")
        with rasterio.open(f"zip+file://{zp}!/{m}") as src:
            dn = src.read(1); out["transform"], out["crs"] = src.transform, src.crs
        if b == "SCL":
            out[b] = dn.astype("i2")
        else:
            off = meta.offsets.get(b, meta.offsets.get("B08", 0.0))               # one BOA_ADD_OFFSET per scene in practice
            out[b] = ((dn.astype("f4") + off) / meta.quantification).astype("f4")
    return out


def indices20(r: dict) -> dict:
    B02, B03, B04, B8A, B11, B12 = (r[b] for b in BANDS20)
    with np.errstate(invalid="ignore", divide="ignore"):
        return {"SWIR1112": SP._nd(B11, B12), "NDMI": SP._nd(B8A, B11), "MSI": (B11 / B8A).astype("f4"), "NDVI": SP._nd(B8A, B04),
                "MNDWI": SP._nd(B03, B11), "BSI": (((B11 + B04) - (B8A + B02)) / ((B11 + B04) + (B8A + B02))).astype("f4"), "NBR": SP._nd(B8A, B12)}


def medians(rows, date, masks, strata, valid, arrays, extra=None):
    """One row per (date, mask, stratum): the median of every array over the cloud-free (observed) cells of the stratum."""
    for k, m in masks.items():
        for sname, smask in strata.items():
            mm = m & smask; n = int(mm.sum())
            if n < MIN_CELLS:
                continue
            vv = mm & valid; row = dict(date=date, mask=k, stratum=sname, n_cells=n, valid_share=round(float(vv.sum() / n), 3))
            if extra:
                row.update(extra)
            for nm, arr in arrays.items():
                row[f"{nm}_median"] = round(float(np.nanmedian(arr[vv])), 4) if vv.any() else np.nan
            rows.append(row)


def did_table(D, indices, pre, day, min_valid):
    """target - control per date, its change from the pre-event date, the same for the references, and the 2022 same-season value."""
    out = []
    for sname in D.stratum.unique():
        for nm in indices:
            col = f"{nm}_median"
            g = D[(D.stratum == sname) & (D.valid_share >= min_valid)]
            piv = g.pivot_table(index="date", columns="mask", values=col)
            if "target" not in piv or "control" not in piv or pre not in piv.index:
                continue
            tc = piv["target"] - piv["control"]; base = tc.get(pre, np.nan)
            tc22 = tc[[d for d in tc.index if d.startswith("2022")]].dropna()
            for dt in piv.index:
                if dt <= day:
                    continue
                r = dict(stratum=sname, index=nm, date=dt, target_minus_control=round(float(tc[dt]), 4), DiD_vs_pre=round(float(tc[dt] - base), 4))
                if len(tc22):
                    doy = pd.Timestamp(dt).dayofyear; near = min(tc22.index, key=lambda d: abs(pd.Timestamp(d).dayofyear - doy))
                    if abs(pd.Timestamp(near).dayofyear - doy) <= 12:
                        r["same_season_2022_date"] = near; r["target_minus_control_2022"] = round(float(tc22[near]), 4); r["DiD_vs_2022"] = round(float(tc[dt] - tc22[near]), 4)
                for ref in ("reference", "reference_brief"):
                    if ref in piv and np.isfinite(piv.loc[dt].get(ref, np.nan)):
                        rc = piv.loc[dt, ref] - piv.loc[dt, "control"]; rb = (piv.loc[pre, ref] - piv.loc[pre, "control"]) if np.isfinite(piv.loc[pre].get(ref, np.nan)) else np.nan
                        r[f"{ref}_minus_control"] = round(float(rc), 4); r[f"DiD_{ref}"] = round(float(rc - rb), 4)
                out.append(r)
    return pd.DataFrame(out)


INBOX_STRATA = ("burnt dNBR>0.1", "trees unburnt", "grass unburnt")


def inbox_contrast(S1, min_valid, tab, name):
    """Sentinel-1 in-scene contrast C = median(target) - median(box_never_flooded) (dB) per acquisition and stratum, with its relative
    orbit and pass. Two readings, kept apart: C minus the mean C of the pre-breach scenes (orbits 65 / 87) -- a CROSS-ORBIT baseline for
    the scenes of other orbits; and the same-orbit changes C_after - C_first (first scene of that orbit as the anchor), which need no
    cross-orbit assumption (orbit 14 has no pre-breach scene in the cache: its test is 09 -> 21 June). Scenes of different relative
    orbits are separate acquisitions, never one temporal curve."""
    S = S1[S1.valid_share >= min_valid]; rows, same = [], []
    for st in INBOX_STRATA:
        for pol in ("VV", "VH"):
            piv = S[S.stratum == st].pivot_table(index="scene", columns="mask", values=f"{pol}_dB_median")
            if "target" not in piv or "box_never_flooded" not in piv:
                continue
            C = (piv["target"] - piv["box_never_flooded"]).dropna().sort_index()
            pre = [sc for sc in C.index if sc[:10] < "2023-06-06"]; base = C[pre].mean() if pre else np.nan
            for sc, v in C.items():
                rows.append(dict(stratum=st, pol=pol, date=sc[:10], relative_orbit=int(re.search(r"orb(\d+)", sc).group(1)), pass_dir=sc.rsplit("_", 1)[-1],
                                 phase="pre-breach" if sc in pre else "post-breach", contrast_dB=round(float(v), 2),
                                 minus_prebreach_mean_crossorbit_dB=round(float(v - base), 2), prebreach_scenes=" + ".join(p[:10] + " orb" + p.split("orb")[1][:3].rstrip("_") for p in pre)))
            for orb in sorted({sc[11:] for sc in C.index}):
                scs = [sc for sc in C.index if sc[11:] == orb]
                for sc in scs[1:]:
                    same.append(dict(stratum=st, pol=pol, relative_orbit=int(re.search(r"orb(\d+)", orb).group(1)), pass_dir=orb.rsplit("_", 1)[-1],
                                     first=scs[0][:10], later=sc[:10], first_is_prebreach=scs[0] in pre, change_dB=round(float(C[sc] - C[scs[0]]), 2)))
    A, B = pd.DataFrame(rows), pd.DataFrame(same)
    A.to_csv(tab / f"p95q_moisture_s1_inbox_{name}.csv", index=False); B.to_csv(tab / f"p95q_moisture_s1_inbox_sameorbit_{name}.csv", index=False)
    if len(A):
        print("\n== S1 in-box contrast (target - never flooded in the box), VV, per acquisition: contrast / minus the pre-breach mean (cross-orbit)")
        v = A[A.pol == "VV"]
        print(v.pivot_table(index=["date", "relative_orbit", "pass_dir"], columns="stratum", values="minus_prebreach_mean_crossorbit_dB").round(2).to_string())
        print("\n== same-orbit changes of the in-box contrast, VV (no cross-orbit assumption)")
        print(B[B.pol == "VV"].pivot_table(index=["relative_orbit", "pass_dir", "first", "later"], columns="stratum", values="change_dB").round(2).to_string())
    return A, B


def ndvi_strata(ndvi):
    return {name: (ndvi >= lo) & (ndvi < hi) for name, lo, hi in NDVI_BINS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="kozachi_laheri_lowland"); ap.add_argument("--lon", type=float, default=33.12); ap.add_argument("--lat", type=float, default=46.665)
    ap.add_argument("--box-km", type=float, nargs=2, default=[6.5, 7.0], help="half-sizes of the target box (E-W, N-S)")
    ap.add_argument("--ring-km", type=float, nargs=2, default=[2.0, 5.0]); ap.add_argument("--day", default="2023-06-07"); ap.add_argument("--pre", default="2023-06-05")
    ap.add_argument("--min-valid", type=float, default=0.3); ap.add_argument("--skip-safe", action="store_true"); ap.add_argument("--skip-s1", action="store_true")
    ap.add_argument("--contrast-only", action="store_true", help="recompute only the in-box S1 contrast tables from the saved per-scene table")
    a = ap.parse_args(); t0 = time.time(); TAB = ROOT / "tables"
    if a.contrast_only:
        inbox_contrast(pd.read_csv(TAB / f"p95q_moisture_s1_{a.name}.csv"), a.min_valid, TAB, a.name); return
    d = CFG.BULK_ROOT / "floodplain_dyn" / f"{ZONE}_connected_ceiling"
    zz = np.load(d / "daily_new.npz"); shp = tuple(int(v) for v in zz["shape"]); un = lambda k: np.unpackbits(zz[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
    with rasterio.open(d / "max_depth_m.tif") as s:
        tr20 = s.transform; crs = s.crs; depth = s.read(1).astype("f4"); depth[depth == s.nodata] = 0; ever = depth > 0
    new = un(a.day); base = un("baseline")
    with rasterio.open(d / f"p95e_cellprob_{a.day}.tif") as s:
        P = s.read(1).astype("f4") / float(s.tags().get("n_draws", 1000))
    with rasterio.open(CFG.BULK_ROOT / "worldcover_frames" / ZONE / "wc_2021_20m.tif") as s:
        wc = np.zeros(shp, "u1"); reproject(s.read(1), wc, src_transform=s.transform, src_crs=s.crs, dst_transform=tr20, dst_crs=crs, resampling=Resampling.nearest)
    x, y = tf_transform("EPSG:4326", CFG.CRS_METRIC, [a.lon], [a.lat]); x, y = float(x[0]), float(y[0])
    xs = tr20.c + 20 * (np.arange(shp[1]) + 0.5); ys = tr20.f - 20 * (np.arange(shp[0]) + 0.5)
    box = ((xs >= x - a.box_km[0] * 1e3) & (xs <= x + a.box_km[0] * 1e3))[None, :] & ((ys >= y - a.box_km[1] * 1e3) & (ys <= y + a.box_km[1] * 1e3))[:, None]
    dist_box = ndimage.distance_transform_edt(~box) * 20.0
    ring = (dist_box >= a.ring_km[0] * 1e3) & (dist_box <= a.ring_km[1] * 1e3); near = dist_box <= REF_KM * 1e3
    target = new & box; control = ring & ~ever & ~base
    z1 = np.load(CFG.S1_CACHE / CACHE / "per_scene_water.npz", allow_pickle=True); s1shp = tuple(int(v) for v in z1["shape"])
    t1 = from_origin(float(z1["x0"]), float(z1["y1"]), float(z1["cell"]), float(z1["cell"])); u1 = lambda k: np.unpackbits(z1[k], count=s1shp[0] * s1shp[1]).reshape(s1shp).astype(bool)
    k1 = sorted(k for k in z1.files if k.startswith("2023") and k[:10] > a.day)[0]

    def to20(src, tr, rs=Resampling.nearest, fill=0):
        # float rasters carry NaN as nodata; 0/1 masks get NO nodata arguments: src_nodata=None with dst_nodata=0 turned the whole
        # covered footprint of a mask into ones (measured 2026-09-30: 17.0 M cells from a 1.57 M-cell mask)
        o = np.full(shp, fill, src.dtype)
        kw = dict(src_nodata=np.nan, dst_nodata=np.nan) if np.issubdtype(src.dtype, np.floating) else {}
        reproject(src, o, src_transform=tr, src_crs=crs, dst_transform=tr20, dst_crs=crs, resampling=rs, **kw); return o
    src_dark = (u1(k1) & u1("valid_" + k1)).astype("u1"); dark = to20(src_dark, t1).astype(bool)
    assert dark.sum() <= 1.01 * src_dark.sum(), f"S1 dark-water mask inflated by the reprojection: {int(dark.sum())} vs {int(src_dark.sum())} source cells"
    drained = ~un(k1[:10]) if k1[:10] in zz.files else np.ones(shp, bool)
    reference = new & ~box & near & dark; reference_brief = new & ~box & near & ~dark & drained
    # box_never_flooded: the same surfaces inside the same box that the reconstruction never floods -- the sharpest control for Sentinel-1
    # (same scene, same incidence, same local weather): a flood-specific wet-soil signal separates it from the target, a regional one does not
    masks = {"target": target, "control": control, "reference": reference, "reference_brief": reference_brief, "box_never_flooded": box & ~ever & ~base,
             "target_P>=0.95": target & (P >= 0.95), "target_P0.5-0.95": target & (P >= 0.5) & (P < 0.95), "target_P<0.5": target & (P < 0.5),
             "target_d<0.5m": target & (depth < 0.5), "target_d0.5-1.5m": target & (depth >= 0.5) & (depth < 1.5), "target_d>=1.5m": target & (depth >= 1.5)}
    km2 = {k: round(float(v.sum()) * 4e-4, 2) for k, v in masks.items()}; print(km2, "km2; first S1 scene after the day:", k1, flush=True)
    m_any = target | control | reference | reference_brief; rr, cc = np.nonzero(m_any)
    r0, r1, c0, c1 = max(rr.min() - 5, 0), min(rr.max() + 6, shp[0]), max(cc.min() - 5, 0), min(cc.max() + 6, shp[1])          # the 20 m window of all masks
    W = (slice(r0, r1), slice(c0, c1)); trW = tr20 * tr20.translation(c0, r0); wshape = (r1 - r0, c1 - c0)
    rb, cb = np.nonzero((target | control)[W]); B = (slice(rb.min(), rb.max() + 1), slice(cb.min(), cb.max() + 1))             # the box + ring sub-window (maps)
    mW = {k: m[W] for k, m in masks.items()}; wcW = wc[W]; strata_wc = {nm: wcW == code for code, nm in WC.items()}
    safes = {} if a.skip_safe else OC.scan_safes()

    def safe_idx(dt):
        """The IDX20 indices of one date on the 20 m window: tiles in TILES order, a later tile fills only cells not yet observed cloud-free."""
        zips = sorted((p for p in safes[dt] if tile_of(p) in TILES), key=lambda p: TILES.index(tile_of(p)))
        idx = {nm: np.full(wshape, np.nan, "f4") for nm in IDX20}; filled = np.zeros(wshape, bool)
        for zp in zips:
            r = read20(zp); scl = np.zeros(wshape, "i2")
            reproject(r["SCL"], scl, src_transform=r["transform"], src_crs=r["crs"], dst_transform=trW, dst_crs=crs, resampling=Resampling.nearest, src_nodata=0, dst_nodata=0)
            ok = (scl > 0) & ~np.isin(scl, CLOUD_SCL) & ~filled
            if not ok.any():
                continue
            ind = indices20(r)
            for nm in IDX20:
                dst = np.full(wshape, np.nan, "f4")
                reproject(ind[nm], dst, src_transform=r["transform"], src_crs=r["crs"], dst_transform=trW, dst_crs=crs, resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
                idx[nm][ok] = dst[ok]
            filled |= ok & np.isfinite(idx["SWIR1112"])
        return idx, filled, zips

    # Strata of the pre-event state (20 m): NDVI classes of --pre, and the ground burnt or cleared between BURN_REF and --pre (dNBR). The
    # first run (2026-09-30) found the bare/sparse stratum of the target to be such ground: NDVI 0.52 in June 2022, 0.25 on 5 June 2023, dNBR
    # median +0.38 -- a pre-breach fire scar whose regrowth brightens Sentinel-1 on its own, compared with natural sand in the control.
    pre_cache = {}; strata20 = dict(strata_wc); strata_burn = {}
    if not a.skip_safe:
        pre_cache = {dt: safe_idx(dt) for dt in (a.pre, BURN_REF)}
        (ip, fp, _), (ir, fr, _) = pre_cache[a.pre], pre_cache[BURN_REF]
        clear = fp & fr; burnt = clear & ((ir["NBR"] - ip["NBR"]) > DNBR_BURNT)
        strata_burn = {"trees unburnt": (wcW == 10) & clear & ~burnt, "grass unburnt": (wcW == 30) & clear & ~burnt, f"burnt dNBR>{DNBR_BURNT}": burnt}
        strata20 = dict(strata_wc) | ndvi_strata(ip["NDVI"]) | strata_burn
        print("burnt/cleared before the breach (dNBR > %.2f): target %.1f km2, control %.1f km2" % (DNBR_BURNT, (mW["target"] & burnt).sum() * 4e-4, (mW["control"] & burnt).sum() * 4e-4), flush=True)

    # ---- 1. the 10 m index stacks of p54a, 2022 and 2023 ----------------------------------------------------------------------------
    idx_dir = CFG.BULK_ROOT / "frames10" / FRAME / "indices"
    dates10 = sorted(p.name[:10] for p in idx_dir.glob("202[23]-*.tif") if "_valid" not in p.name and (("2022-05-01" <= p.name[:10] <= "2022-09-30") or (a.pre <= p.name[:10] <= "2023-09-30")))
    with rasterio.open(idx_dir / f"{dates10[0]}.tif") as s:
        tr10 = s.transform; desc = list(s.descriptions); nd10 = s.nodata; H10, W10 = s.height, s.width
    x0, x1 = trW.c, trW.c + wshape[1] * 20; y1, y0 = trW.f, trW.f - wshape[0] * 20
    cc0 = max(int((x0 - tr10.c) / 10), 0); cc1 = min(int(np.ceil((x1 - tr10.c) / 10)), W10); rr0 = max(int((tr10.f - y1) / 10), 0); rr1 = min(int(np.ceil((tr10.f - y0) / 10)), H10)
    win = rasterio.windows.Window(cc0, rr0, cc1 - cc0, rr1 - rr0); tw = rasterio.windows.transform(win, tr10); w10 = (rr1 - rr0, cc1 - cc0)

    def to10(src):
        o = np.zeros(w10, src.dtype); reproject(src, o, src_transform=tr20, src_crs=crs, dst_transform=tw, dst_crs=crs, resampling=Resampling.nearest); return o
    m10 = {k: to10(m.astype("u1")).astype(bool) for k, m in masks.items()}; wc10 = to10(wc)
    with rasterio.open(idx_dir / f"{a.pre}.tif") as s:
        ndvi10 = s.read(desc.index("NDVI") + 1, window=win).astype("f4"); ndvi10[ndvi10 == nd10] = np.nan; ndvi10 /= 1e4
    strata10 = {nm: wc10 == code for code, nm in WC.items()} | ndvi_strata(ndvi10)
    for k, v in strata_burn.items():
        o = np.zeros(w10, "u1"); reproject(v.astype("u1"), o, src_transform=trW, src_crs=crs, dst_transform=tw, dst_crs=crs, resampling=Resampling.nearest); strata10[k] = o.astype(bool)
    rows = []
    for dt in dates10:
        with rasterio.open(idx_dir / f"{dt}.tif") as s:
            arr = s.read(window=win).astype("f4"); arr[arr == nd10] = np.nan; arr /= 1e4
        with rasterio.open(idx_dir / f"{dt}_valid.tif") as s:
            v = s.read(1, window=win) > 0
        medians(rows, dt, m10, strata10, v, {nm: arr[desc.index(nm)] for nm in IDX10})
    D10 = pd.DataFrame(rows); D10.to_csv(TAB / f"p95q_moisture_trace_{a.name}.csv", index=False); print("10 m stacks:", len(dates10), "dates", round(time.time() - t0), "s", flush=True)

    # ---- 2. SWIR1112 / NDMI(B8A) / MSI at 20 m from the SAFE archives, 2022 and 2023 -------------------------------------------------
    D20 = pd.DataFrame(); YP = pd.DataFrame(); keep = {}; used = {}
    if not a.skip_safe:
        rows = []; yrows = []
        want = sorted(dt for dt in safes if (("2022-05-15" <= dt <= "2022-08-15") or (a.pre <= dt <= "2023-08-15")) and any(tile_of(p) in TILES for p in safes[dt]))
        need = {a.pre} | {d for pr in YEAR_PAIRS for d in pr}
        for dt in want:
            idx, filled, zips = pre_cache.pop(dt) if dt in pre_cache else safe_idx(dt)
            used[dt] = [zp.name for zp in zips]
            if dt in need:
                keep[dt] = {nm: idx[nm].copy() for nm in ("SWIR1112", "NDMI", "MSI", "NDVI")}; keep[dt]["valid"] = filled.copy()
            medians(rows, dt, mW, strata20, filled, idx, extra=dict(scenes=len(zips)))
            print(" ", dt, [tile_of(zp) for zp in zips], "cloud-free share of the window", round(float(filled.mean()), 3), round(time.time() - t0), "s", flush=True)
        D20 = pd.DataFrame(rows); D20.to_csv(TAB / f"p95q_moisture_20m_{a.name}.csv", index=False)
        # the matched-date year difference I_2023 - I_2022 per pixel (the same relative orbit and season), and its change from the pre-event pair
        for d23, d22 in YEAR_PAIRS:
            if d23 in keep and d22 in keep:
                ok = keep[d23]["valid"] & keep[d22]["valid"]; dif = {nm: keep[d23][nm] - keep[d22][nm] for nm in ("SWIR1112", "NDMI", "MSI", "NDVI")}
                medians(yrows, f"{d23}-{d22}", mW, strata20, ok, dif, extra=dict(date_2023=d23, date_2022=d22))
        YP = pd.DataFrame(yrows); YP.to_csv(TAB / f"p95q_moisture_yearpair_{a.name}.csv", index=False)

    # ---- 3. Sentinel-1 VV / VH (dB; linear gamma0 of the cache), same-relative-orbit pairs --------------------------------------------
    S1 = pd.DataFrame(); PAIRS = pd.DataFrame(); s1maps = {}; cache = CFG.S1_CACHE / CACHE

    def s1db(key):
        z = np.load(cache / f"{key}.npz"); out = {}
        for pol in ("vv", "vh"):
            v = z[pol]; cov = z["cov"]
            with np.errstate(divide="ignore", invalid="ignore"):
                dbv = np.where(cov & (v > 0), 10 * np.log10(v), np.nan).astype("f4")
            out[f"{pol.upper()}_dB"] = to20(dbv, t1, fill=np.nan)[W]
        out["VVVH_dB"] = out["VV_dB"] - out["VH_dB"]; return out
    if not a.skip_s1:
        rows = []; prow = []
        for f in sorted(cache.glob("2023-*.npz")):
            key = f.stem; db = s1db(key); medians(rows, key[:10], mW, strata20, np.isfinite(db["VV_dB"]), db, extra=dict(scene=key, orbit=key[11:]))
        S1 = pd.DataFrame(rows); S1.to_csv(TAB / f"p95q_moisture_s1_{a.name}.csv", index=False)
        for before, after in S1_PAIRS:
            if not (cache / f"{before}.npz").exists() or not (cache / f"{after}.npz").exists():
                continue
            b, af = s1db(before), s1db(after); dif = {nm: af[nm] - b[nm] for nm in ("VV_dB", "VH_dB", "VVVH_dB")}
            medians(prow, f"{before[:10]}->{after[:10]}", mW, strata20, np.isfinite(dif["VV_dB"]), dif, extra=dict(orbit=after[11:]))
            if after[:10] in ("2023-06-13", "2023-06-14"):
                s1maps[f"{before[:10]}->{after[:10]} {after[11:]}"] = {nm: dif[nm] for nm in ("VV_dB", "VH_dB")}
        PAIRS = pd.DataFrame(prow); PAIRS.to_csv(TAB / f"p95q_moisture_s1_pairs_{a.name}.csv", index=False); print("S1 done", round(time.time() - t0), "s", flush=True)
        inbox_contrast(S1, a.min_valid, TAB, a.name)

    # ---- 4. co-location of the SWIR anomaly and the VV change, pixel by pixel, per NDVI stratum ------------------------------------
    CO = pd.DataFrame(); crow = []
    pairs_ok = [(d23, d22) for d23, d22 in YEAR_PAIRS if d23 in keep and d22 in keep and d23 > a.day]
    if pairs_ok and s1maps and ("2023-06-05" in keep) and ("2022-06-03" in keep):
        pre_dif = keep[a.pre]["SWIR1112"] - keep["2022-06-03"]["SWIR1112"]; pre_ok = keep[a.pre]["valid"] & keep["2022-06-03"]["valid"]
        for d23, d22 in pairs_ok:
            dswir = (keep[d23]["SWIR1112"] - keep[d22]["SWIR1112"]) - pre_dif; ok0 = keep[d23]["valid"] & keep[d22]["valid"] & pre_ok
            for skey, s1d in s1maps.items():
                dvv = s1d["VV_dB"]; ok = ok0 & np.isfinite(dvv)
                for sname, smask in strata20.items():
                    if not sname.startswith("ndvi"):
                        continue
                    for mk in ("target", "control", "reference", "reference_brief"):
                        m = mW[mk] & smask & ok; n = int(m.sum())
                        if n < MIN_CELLS:
                            continue
                        rho = stats.spearmanr(dswir[m], dvv[m]).correlation if n >= 30 else np.nan
                        crow.append(dict(swir_pair=f"{d23}-{d22} minus {a.pre}-2022-06-03", s1_pair=skey, stratum=sname, mask=mk, n_cells=n,
                                         dSWIR_DiD_median=round(float(np.median(dswir[m])), 4), dVV_dB_median=round(float(np.median(dvv[m])), 2),
                                         share_both_wetter=round(float(((dswir[m] > 0.02) & (dvv[m] > 1.0)).mean()), 3), share_swir_wetter=round(float((dswir[m] > 0.02).mean()), 3),
                                         share_vv_up=round(float((dvv[m] > 1.0).mean()), 3), spearman_dSWIR_dVV=round(float(rho), 3) if np.isfinite(rho) else np.nan))
        CO = pd.DataFrame(crow); CO.to_csv(TAB / f"p95q_moisture_coloc_{a.name}.csv", index=False)

    # ---- 5. summaries --------------------------------------------------------------------------------------------------------------
    Q10 = did_table(D10, IDX10, a.pre, a.day, a.min_valid); Q10.insert(0, "source", "p54a_10m")
    Q20 = did_table(D20, IDX20, a.pre, a.day, a.min_valid) if len(D20) else pd.DataFrame()
    if len(Q20):
        Q20.insert(0, "source", "SAFE_20m")
    Q = pd.concat([Q10, Q20], ignore_index=True); Q.to_csv(TAB / f"p95q_moisture_did_{a.name}.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 500); pd.set_option("display.max_columns", 30)
    for sname in ("grass", "trees", "grass unburnt", "trees unburnt", f"burnt dNBR>{DNBR_BURNT}", "ndvi<0.3 bare/sparse", "ndvi0.3-0.6 mixed", "ndvi>0.6 canopy"):
        for src, nm in (("SAFE_20m", "SWIR1112"), ("SAFE_20m", "NDMI"), ("SAFE_20m", "MSI"), ("p54a_10m", "NDMI")):
            g = Q[(Q.source == src) & (Q.stratum == sname) & (Q["index"] == nm)]
            if len(g):
                print(f"\n== {sname} | {nm} ({src})"); print(g.drop(columns=["source", "stratum", "index"]).to_string(index=False))
    if len(YP):
        print("\n== matched-date year difference 2023 - 2022 (medians per pixel)")
        for nm in ("SWIR1112", "NDMI", "NDVI"):
            piv = YP[YP.valid_share >= a.min_valid].pivot_table(index=["date", "stratum"], columns="mask", values=f"{nm}_median")
            cols = [c for c in ("target", "control", "box_never_flooded", "reference", "reference_brief", "target_P>=0.95", "target_d>=1.5m") if c in piv]; piv = piv[cols]
            piv["t-c"] = piv["target"] - piv["control"]; print(nm); print(piv.round(3).to_string())
    if len(PAIRS):
        print("\n== Sentinel-1 same-orbit change (dB, medians)")
        for nm in ("VV_dB", "VH_dB"):
            piv = PAIRS[PAIRS.valid_share >= a.min_valid].pivot_table(index=["date", "stratum"], columns="mask", values=f"{nm}_median")
            cols = [c for c in ("target", "control", "box_never_flooded", "reference", "reference_brief", "target_P>=0.95", "target_d>=1.5m") if c in piv]; piv = piv[cols]
            piv["t-c"] = piv["target"] - piv["control"]; print(nm); print(piv.round(2).to_string())
    if len(CO):
        print("\n== co-location of the SWIR anomaly (DiD vs 2022) and the VV change, per NDVI stratum"); print(CO.to_string(index=False))

    # ---- 6. figures ----------------------------------------------------------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG.mkdir(parents=True, exist_ok=True)
    STY = {"target": ("#2a78d6", "o", f"reconstructed new water {a.day} (target)"), "control": ("#8d6e63", "s", "never flooded neighbour (control)"),
           "reference": ("#eb6834", "^", f"new water seen dark by S1 {k1[:10]} (reference)"), "reference_brief": ("#9c6bbf", "v", "new water drained by then in the reconstruction (brief, elsewhere)")}
    cols_s = ["grass", "trees", "ndvi<0.3 bare/sparse"]
    panels = [("p54a_10m", D10, "NDMI"), ("p54a_10m", D10, "NDVI")] + ([("SAFE_20m", D20, "SWIR1112"), ("SAFE_20m", D20, "MSI")] if len(D20) else [])
    fig, axs = plt.subplots(len(panels), len(cols_s), figsize=(4.6 * len(cols_s), 2.6 * len(panels)), constrained_layout=True, squeeze=False)
    for j, sname in enumerate(cols_s):
        for i, (src, D, nm) in enumerate(panels):
            ax = axs[i, j]
            for k, (col, mk, lab) in STY.items():
                g = D[(D["mask"] == k) & (D.stratum == sname) & (D.valid_share >= a.min_valid)].sort_values("date")
                for yr, ls, al in (("2023", "-", 1.0), ("2022", ":", 0.7)):
                    gg = g[g.date.str.startswith(yr)]
                    if len(gg):
                        t = pd.to_datetime(gg.date).map(lambda ts: ts.replace(year=2023))
                        ax.plot(t, gg[f"{nm}_median"], marker=mk, ms=3.5, lw=1.1, ls=ls, alpha=al, color=col, label=f"{lab} {yr}" if (i == 0 and j == 0) else None)
            ax.axvline(pd.Timestamp(a.day), color="#e34948", lw=0.8, ls="--"); ax.set_title(f"{nm} median | {sname} ({src})", fontsize=8); ax.tick_params(labelsize=7); ax.grid(alpha=0.3)
            ax.set_xlim(pd.Timestamp("2023-05-25"), pd.Timestamp("2023-08-31"))
    axs[0, 0].legend(fontsize=5.5, loc="best")
    fig.suptitle(f"Post-event wetness trace of {a.name}: flooded target vs unflooded control vs S1-observed reference; 2023 solid, 2022 dotted (same calendar dates)", fontsize=8)
    fig.savefig(FIG / f"p95q_moisture_{a.name}.png", dpi=140); plt.close(fig)
    # anomaly maps on the box + ring sub-window
    if a.pre in keep:
        trB = trW * trW.translation(B[1].start, B[0].start); bshape = (B[0].stop - B[0].start, B[1].stop - B[1].start)
        ext = (trB.c, trB.c + bshape[1] * 20, trB.f - bshape[0] * 20, trB.f)
        newB = new[W][B]; boxB = box[W][B]; darkB = (dark & ~base)[W][B]; ndviB = keep[a.pre]["NDVI"][B]
        cls = np.full(bshape, np.nan, "f4"); cls[ndviB < 0.3] = 0; cls[(ndviB >= 0.3) & (ndviB < 0.6)] = 1; cls[ndviB >= 0.6] = 2
        items = [(f"NDVI strata {a.pre}: 0 bare/sparse, 1 mixed, 2 canopy", cls, "viridis", (0, 2)),
                 (f"SWIR1112 {a.pre} (pre-breach)", keep[a.pre]["SWIR1112"][B], "BrBG", (-0.2, 0.4))]
        for d23, d22 in pairs_ok:
            items.append((f"dSWIR1112 {d23} - {a.pre} (within 2023)", (keep[d23]["SWIR1112"] - keep[a.pre]["SWIR1112"])[B], "RdBu", (-0.1, 0.1)))
            if "2022-06-03" in keep:
                items.append((f"dSWIR1112 DiD: ({d23} - {d22}) - ({a.pre} - 2022-06-03)", ((keep[d23]["SWIR1112"] - keep[d22]["SWIR1112"]) - (keep[a.pre]["SWIR1112"] - keep["2022-06-03"]["SWIR1112"]))[B], "RdBu", (-0.1, 0.1)))
                items.append((f"dNDMI DiD: ({d23} - {d22}) - ({a.pre} - 2022-06-03)", ((keep[d23]["NDMI"] - keep[d22]["NDMI"]) - (keep[a.pre]["NDMI"] - keep["2022-06-03"]["NDMI"]))[B], "RdBu", (-0.2, 0.2)))
        for key, s1d in s1maps.items():
            items.append((f"S1 VV change {key} (dB)", s1d["VV_dB"][B], "RdBu", (-4, 4))); items.append((f"S1 VH change {key} (dB)", s1d["VH_dB"][B], "RdBu", (-4, 4)))
        n = len(items); nc = 3; nr = int(np.ceil(n / nc))
        fig, axs = plt.subplots(nr, nc, figsize=(5.4 * nc, 4.8 * nr), constrained_layout=True, squeeze=False); axs = axs.ravel()
        for ax, (ttl, arr, cmap, lim) in zip(axs, items):
            im = ax.imshow(arr, extent=ext, cmap=cmap, vmin=lim[0], vmax=lim[1], interpolation="nearest")
            ax.contour(newB.astype("u1"), levels=[0.5], colors="#0b3d91", linewidths=0.8, extent=ext, origin="upper")
            ax.contour(boxB.astype("u1"), levels=[0.5], colors="#e34948", linewidths=0.8, linestyles="--", extent=ext, origin="upper")
            if darkB.any():
                ax.contour(darkB.astype("u1"), levels=[0.5], colors="k", linewidths=0.5, extent=ext, origin="upper")
            ax.set_title(ttl, fontsize=7.5); ax.tick_params(labelsize=6); plt.colorbar(im, ax=ax, shrink=0.7).ax.tick_params(labelsize=6)
        for ax in axs[n:]:
            ax.axis("off")
        fig.suptitle(f"{a.name}: blue = reconstructed new water {a.day} (primary), red dashed = target box, black = S1 dark water {k1[:10]}; "
                     "blue tones = higher SWIR contrast / NDMI (wetter or more canopy water) or higher backscatter", fontsize=8)
        fig.savefig(FIG / f"p95q_moisture_maps_{a.name}.png", dpi=130); plt.close(fig)
    (TAB / f"p95q_moisture_manifest_{a.name}.json").write_text(json.dumps(dict(
        producer="p95q_moisture_trace.py", name=a.name, day=a.day, pre=a.pre, box_km=a.box_km, ring_km=a.ring_km, reference_within_km=REF_KM, masks_km2=km2,
        first_s1_scene_after_day=k1, s2_dates_10m=dates10, safe_scenes_20m=used, year_pairs=YEAR_PAIRS, s1_pairs=S1_PAIRS, min_valid=a.min_valid, min_cells_20m=MIN_CELLS,
        indices=dict(SWIR1112="(B11 - B12)/(B11 + B12) at native 20 m: the SWIR normalized contrast, mathematically identical to the Sentinel-2 implementation sometimes termed NSMI "
                              "(Haubrock's NSMI used ~1800 and ~2120 nm); read as a SWIR wetness anomaly whose moisture-like behaviour is checked, not assumed",
                     NDMI_20m="(B8A - B11)/(B8A + B11)", MSI="B11/B8A", NDVI_20m="(B8A - B04)/(B8A + B04)", NDMI_10m="(B08 - B11)/(B08 + B11) of p54a",
                     S1="linear gamma0 of the June 2023 cache (one pipeline, terrain-corrected), dB; pairs share the relative orbit"),
        strata="WorldCover 2021 class; pre-event NDVI of --pre: bare/sparse < 0.3, mixed 0.3-0.6, canopy > 0.6; "
               f"burnt/cleared before the breach: NBR({BURN_REF}) - NBR(--pre) > {DNBR_BURNT} (both dates cloud-free), else 'unburnt'",
        reading="qualitative difference-in-differences against the unflooded neighbour, the 2022 matched dates and the S1-observed reference; never a validation"), indent=1))
    print("->", TAB / f"p95q_moisture_did_{a.name}.csv", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
