# Provenance: SWOT-DNIPRO scripts/p71_s1_event_change.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 17 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo. `to_db()` is what
# tests/test_p71_change_domain.py imports (from floodstate_eo.sar.p71_s1_event_change import to_db).
"""P71 -- Sentinel-1 event CHANGE channels for a segmentation network, not a classifier.

This file no longer decides anything. It builds the physical evidence a later model will learn from, and it
exists because feeding raw S1 water masks to a segmentation network would teach it to reproduce rectangular
agricultural fields as water.

THE SIGN OF THE CHANGE IS NOT PRESCRIBED. Open water lowers backscatter through specular reflection; water under
standing vegetation can RAISE it through double bounce, and how much depends on vegetation structure, polarization,
incidence angle and the state of the water surface. So both extremes and the signed differences are written out and
the network decides. No rule of the form "dVV > 0 means flooded vegetation" appears anywhere in this file -- that
was a hypothesis, and hypotheses belong in the features, not in the code.

THE BASELINE IS MATCHED BY RELATIVE ORBIT, and this is not a refinement -- it is a correctness requirement. SAR
change detection compares acquisitions of the same viewing geometry: same relative orbit, same pass direction, same
polarization. The four peak acquisitions over the delta come from FOUR DIFFERENT orbits -- 06-06 on 138_DES, 06-09
on 14_ASC, 06-13 on 65_DES, 06-14 on 87_ASC -- so a single pooled pre-event median across all 79 pre-breach scenes
would difference ascending against descending and return a geometry artefact on every field, with no water
involved. Each event scene is therefore differenced against the median of ITS OWN orbit, and the per-scene
differences are only then aggregated.

A RECENT-ONLY BASELINE IS NOT AVAILABLE, and the reason is worth recording rather than glossing. Restricting to
2022 onward leaves 1 to 4 scenes per orbit (138_DES 1, 65_DES 1, 14_ASC 2, 87_ASC 4) -- too few for a median, let
alone a MAD. The earlier plan to compare a "seasonal" recent baseline against a long one dies here: it was also
misnamed, since 2022-plus is RECENT, not season-matched. Only LONG_MATCHED, 18 to 23 scenes per orbit, survives.

B2 FIRST, DELIBERATELY. The delta is where the optical model recovered only 23 % of the S1 candidates, where the
disputed area sits at HAND ~ 0 in large connected masses rather than on a plateau, and where flooding is under reed
rather than in the open. It is also the only frame whose long and June caches share a grid exactly (3830 x 1887),
so no resampling enters the difference. B1's caches do NOT share a grid and will need an explicit reprojection step
-- the same operation that was got wrong once already, so it is done separately and not rushed here.

Outputs: $BULK_ROOT/frames10/<FRAME>/s1_change.tif  (channels below, on the canonical 10 m lattice)
         <case_study>/tables/p71_s1_change_manifest.csv
"""
from __future__ import annotations
import argparse, os, re, sys, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from .. import _kakhovka_legacy_config as CFG
from ..spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
LONG = {"B2": "ZONE_2_KHERSON_DELTA", "B3": "ZONE_3_DNIPRO_BUG_ESTUARY",
        "B1": "ZONE_4_DAM_TO_KHERSON_FLOODWAY"}
JUNE = {"B2": "ZONE_2_KHERSON_DELTA_flood_june2023", "B3": "ZONE_3_DNIPRO_BUG_ESTUARY_flood_june2023",
        "B1": "ZONE_4_FLOODWAY_june2023_s32"}
BREACH = "2023-06-06"
PEAK_LO, PEAK_HI = "2023-06-06", "2023-06-14"
SCALE = 100          # dB * 100 in int16
ND = -32768
ROWS = 512
#: NO RAW BACKSCATTER IS AGGREGATED ACROSS ORBITS. Every channel below is either a per-scene difference against the
#: median of that scene's OWN relative orbit -- already normalised before any aggregation -- or a plain count.
#: An earlier version of this list carried `vv_event_min/max` and an orbit-averaged `pre_med`, which would have
#: compared 138_DES against 14_ASC directly and handed the network a geometry signal it could learn instead of
#: water. Raw per-orbit channels can be added later as separate, explicitly named bands; they are not worth the
#: risk in the first tensor.
CH = ["d_vv_min", "d_vh_min", "d_vv_max", "d_vh_max", "d_vv_mean", "d_vh_mean",
      "d_vvvh_min", "d_vvvh_max",
      "z_vv_min", "z_vh_min", "z_vv_max", "z_vh_max",
      "n_valid_pre_matched", "n_valid_event", "n_orbits_event"]


#: THE CACHES HOLD LINEAR gamma0, NOT dB. Measured on both ZONE_2 caches: VV median 0.066 (long) and 0.083 (June),
#: minimum 0.0013 -- power, not decibels. Until 2026-09-23 (in the source repository) this file differenced those
#: linear values directly while documenting its channels as "dB x 100", with two consequences measured on the
#: delivered product:
#:   * separability halved. Same scene (2023-06-13 orb65_DES), same 18-scene matched baseline, same labels:
#:     d' on VEG_AGRI -0.216 linear against -0.542 in dB (x2.51), on WETLAND -0.768 against -1.533 (x2.00).
#:     Backscatter change is MULTIPLICATIVE, so the natural change operator is a ratio -- a difference of logs.
#:     A linear difference makes the magnitude of a change depend on the absolute level and therefore
#:     systematically under-weights change over dark surfaces, which is most of what a flood produces.
#:   * the MAD floor below stopped being a floor. In linear gamma0 the per-pixel MAD is p50 0.0255, so the 0.1
#:     guard bound 98.97 % of pixels and z collapsed to d/0.1 -- the four z_* channels were a rescaled copy of the
#:     d_* channels, not a robust per-pixel normalisation (measured median z/d on the product: 9.83). In dB the
#:     same MAD is p50 1.53 and 0.00 % of pixels reach the floor, which is what the guard was written for.
#: Conversion happens ONCE, on load, before any median, MAD, difference or order statistic.
def to_db(a):
    """Linear gamma0 -> dB. Non-positive input becomes NaN, never a substituted floor.

    An earlier version clipped to 1e-6 before the log. On the source archive that clip never fired (0
    non-positive values in 444,894,564 cov-valid samples, so the two agree bitwise there), but a clip turns an
    invalid measurement into a confident -60 dB reading, which is a silent failure mode rather than a missing
    one. Invalidity is propagated as NaN so that nanmedian, MAD and the order statistics all drop it by
    construction.
    """
    a = np.asarray(a, "f4")
    out = np.full(a.shape, np.nan, "f4")
    ok = np.isfinite(a) & (a > 0)
    out[ok] = 10.0 * np.log10(a[ok])
    return out


def scenes(cache, lo=None, hi=None, pre=False):
    d = CFG.S1_CACHE / cache
    out = []
    for p in sorted(d.glob("*.npz")):
        if p.name == "per_scene_water.npz":
            continue
        dt = p.name[:10]
        if pre and dt >= BREACH:
            continue
        if lo and not (lo <= dt <= hi):
            continue
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=["B2"])
    ap.add_argument("--rows", type=int, default=ROWS); a = ap.parse_args()
    man = []
    for fid in a.frames:
        t0 = time.time()
        pre_all = scenes(LONG[fid], pre=True)
        pre_22 = [p for p in pre_all if p.name[:10] >= "2022-01-01"]
        ev = scenes(JUNE[fid], PEAK_LO, PEAK_HI)
        z0 = np.load(pre_all[0]); shp = z0["vv"].shape
        ze = np.load(ev[0])
        if ze["vv"].shape != shp:
            print(f"{fid}: SKIP -- long cache {shp} and June cache {ze['vv'].shape} are on different grids; "
                  f"an explicit reprojection step is required and is deliberately not improvised here")
            continue
        F = CG.frame_grid(fid)
        # the zone cache grid, taken from per_scene_water so the geometry is the recorded one
        w = np.load(CFG.S1_CACHE / JUNE[fid] / "per_scene_water.npz", allow_pickle=True)
        cell = float(w["cell"]); ztr = from_origin(float(w["x0"]), float(w["y1"]), cell, cell)
        print(f"{fid}: {len(pre_all)} pre-breach scenes ({len(pre_22)} from 2022), {len(ev)} peak scenes "
              f"{PEAK_LO}..{PEAK_HI}; zone grid {shp} at {cell:.0f} m", flush=True)
        def orbit(pth):
            m = re.search(r"_orb(\d+)_(ASC|DES)", pth.name)
            return f"{m.group(1)}_{m.group(2)}" if m else "?"
        ev_orb = {p_: orbit(p_) for p_ in ev}
        need = sorted(set(ev_orb.values()))
        by_orb = {o: [p_ for p_ in pre_all if orbit(p_) == o] for o in need}
        for o in need:
            print(f"    orbit {o:9s}: {len(by_orb[o]):2d} pre-breach scenes for the matched baseline", flush=True)
            if len(by_orb[o]) < 5:
                raise SystemExit(f"orbit {o} has only {len(by_orb[o])} matched pre-breach scenes -- too few for a "
                                 f"median and MAD; do NOT substitute a pooled baseline")
        acc = {c: np.full(shp, np.nan, "f4") for c in CH}
        for r0 in range(0, shp[0], a.rows):
            r1 = min(r0 + a.rows, shp[0]); h = r1 - r0
            def stack(paths, band):
                A = np.full((len(paths), h, shp[1]), np.nan, "f4")
                for i, p_ in enumerate(paths):
                    z = np.load(p_)
                    v = z[band][r0:r1].astype("f4"); c = z["cov"][r0:r1]
                    v[~c] = np.nan
                    A[i] = to_db(v)
                return A
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                base = {}
                for o in need:
                    for band in ("vv", "vh"):
                        P = stack(by_orb[o], band)
                        m_ = np.nanmedian(P, 0)
                        base[(o, band, "med")] = m_
                        # 0.1 dB floor: a guard against a degenerate MAD on pixels whose pre-event series barely
                        # varies, NOT a normalisation. It binds 0.00 % of pixels in dB (p50 MAD 1.53 dB); it bound
                        # 98.97 % when this ran on linear gamma0. Any future change of units must revisit it.
                        base[(o, band, "mad")] = np.maximum(np.nanmedian(np.abs(P - m_), 0), 0.1)
                        base[(o, band, "n")] = np.isfinite(P).sum(0)
                        del P
                # per EVENT scene, differenced against ITS OWN orbit, then aggregated
                dvv, dvh, zvv, zvh, evv, evh, dr = [], [], [], [], [], [], []
                nv = np.zeros((h, shp[1]), "f4"); no = np.zeros((h, shp[1]), "f4")
                for p_ in ev:
                    o = ev_orb[p_]
                    z = np.load(p_)
                    c = z["cov"][r0:r1]
                    vv = z["vv"][r0:r1].astype("f4"); vv[~c] = np.nan; vv = to_db(vv)
                    vh = z["vh"][r0:r1].astype("f4"); vh[~c] = np.nan; vh = to_db(vh)
                    evv.append(vv); evh.append(vh)
                    dvv.append(vv - base[(o, "vv", "med")]); dvh.append(vh - base[(o, "vh", "med")])
                    zvv.append((vv - base[(o, "vv", "med")]) / base[(o, "vv", "mad")])
                    zvh.append((vh - base[(o, "vh", "med")]) / base[(o, "vh", "mad")])
                    dr.append((vv - vh) - (base[(o, "vv", "med")] - base[(o, "vh", "med")]))
                    nv += np.isfinite(vv); no += np.isfinite(vv)
                S = lambda L: np.stack(L)
                acc["d_vv_min"][r0:r1] = np.nanmin(S(dvv), 0); acc["d_vv_max"][r0:r1] = np.nanmax(S(dvv), 0)
                acc["d_vh_min"][r0:r1] = np.nanmin(S(dvh), 0); acc["d_vh_max"][r0:r1] = np.nanmax(S(dvh), 0)
                acc["d_vv_mean"][r0:r1] = np.nanmean(S(dvv), 0); acc["d_vh_mean"][r0:r1] = np.nanmean(S(dvh), 0)
                acc["d_vvvh_min"][r0:r1] = np.nanmin(S(dr), 0); acc["d_vvvh_max"][r0:r1] = np.nanmax(S(dr), 0)
                acc["z_vv_min"][r0:r1] = np.nanmin(S(zvv), 0); acc["z_vv_max"][r0:r1] = np.nanmax(S(zvv), 0)
                acc["z_vh_min"][r0:r1] = np.nanmin(S(zvh), 0); acc["z_vh_max"][r0:r1] = np.nanmax(S(zvh), 0)
                acc["n_valid_event"][r0:r1] = nv
                acc["n_orbits_event"][r0:r1] = np.minimum(no, len(need))
                # only the COUNT of matched pre-event observations is averaged over orbits: a count carries no
                # geometry, unlike a backscatter level
                acc["n_valid_pre_matched"][r0:r1] = np.nanmean(
                    np.stack([base[(o, "vv", "n")].astype("f4") for o in need]), 0)
                del base, dvv, dvh, zvv, zvh, evv, evh, dr

        prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=len(CH), dtype="int16",
                    crs=CFG.CRS_METRIC, transform=F["transform"], compress="deflate", predictor=2, tiled=True,
                    blockxsize=512, blockysize=128, nodata=ND, BIGTIFF="IF_SAFER")
        p = OUT / fid / "s1_change.tif"
        with rasterio.open(p.with_suffix(".tif.part"), "w", **prof) as dst:
            for i, c in enumerate(CH, 1):
                # EXPLICIT reprojection with both transforms -- the decimated-read shortcut is what put a 10 m
                # shift into every SWIR index once already
                d10 = np.full((F["ny"], F["nx"]), np.nan, "f4")
                reproject(source=acc[c], destination=d10, src_transform=ztr, src_crs=CFG.CRS_METRIC,
                          dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC,
                          resampling=Resampling.nearest if c.startswith("n_") else Resampling.bilinear,
                          src_nodata=np.nan, dst_nodata=np.nan)
                q = np.where(np.isfinite(d10), np.clip(np.round(d10 * (1 if c.startswith("n_") else SCALE)),
                                                       -32767, 32767), ND).astype("i2")
                dst.write(q, i); dst.set_band_description(i, c)
                man.append(dict(frame=fid, band=i, channel=c,
                                scale=1 if c.startswith("n_") else SCALE,
                                units="count" if c.startswith("n_") else
                                      ("robust z" if c.startswith("z_") else "dB x 100"),
                                baseline="LONG_MATCHED per relative orbit",
                                orbits="|".join(sorted(set(ev_orb.values()))),
                                n_pre_matched_min=min(len(v) for v in by_orb.values()),
                                n_pre_matched_max=max(len(v) for v in by_orb.values()), n_event=len(ev)))
                del d10, q
            dst.update_tags(peak_window=f"{PEAK_LO}..{PEAK_HI}", n_pre_all=str(len(pre_all)),
                            n_pre_2022=str(len(pre_22)), n_event=str(len(ev)),
                            purpose="INPUT CHANNELS for a downstream segmentation model; this file classifies nothing",
                            sign_note="both event minimum and maximum and signed differences are provided; the "
                                      "sign of a flood response is NOT prescribed anywhere",
                            baseline="LONG_MATCHED: per-relative-orbit median and MAD over the pre-breach series. "
                                     "RECENT_2022PLUS is impossible (1-4 scenes per orbit) and SEASON_MATCHED_LONG "
                                     "was measured and is also impossible (orbit 138_DES yields 1/4/4 scenes at "
                                     "DOY +-21/30/45 d), so LONG_MATCHED is not a preference but the only option",
                            orbit_safety="no raw backscatter is aggregated across relative orbits; every channel is "
                                         "an orbit-matched anomaly or a count",
                            orbits="|".join(sorted(set(ev_orb.values()))),
                            resampling="explicit reproject with source and destination transforms",
                            producer="p71_s1_event_change.py")
        os.replace(p.with_suffix(".tif.part"), p)
        print(f"  -> {p.name} {len(CH)} channels, {p.stat().st_size/1e9:.2f} GB, {time.time()-t0:.0f}s", flush=True)
        del acc
    pd.DataFrame(man).to_csv(CFG.TABLES / "p71_s1_change_manifest.csv", index=False)
    print("-> <case_study>/tables/p71_s1_change_manifest.csv")


if __name__ == "__main__":
    main()
