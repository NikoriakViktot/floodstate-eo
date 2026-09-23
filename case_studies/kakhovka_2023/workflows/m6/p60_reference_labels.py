# Provenance: SWOT-DNIPRO scripts/p60_reference_labels.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: ACTIVE -- weak reference labels (S1 peak water x pre-breach S2 water frequency x post-breach dryness); reads NO land cover -- the land-cover-free base of both v001 and m6_labels_v002. Reads outputs/rasters/zone*/zone*_water_frac_PRE_BREACH_20m.tif relative to ROOT, which is NOT present in floodstate-eo (data dependency, unresolved).
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P60 -- WEAK REFERENCE LABELS for B1/B2/B3, constructed but NOT yet frozen.

WEAK REFERENCE IS NOT GROUND TRUTH (Bonafilia et al. 2020, SRC-45). These labels come from a Sentinel-1 rule, so they
are automatically generated supervision with their own failure modes, and they are named that way everywhere.

THE RULE, unchanged from p51 and applied identically to all three frames:
    land_pre = observed in >= 1 pre-breach S1 event AND dry in every observed pre-breach event
               AND pre-breach Sentinel-2 water frequency < 20 %          (not the river, not the lakes)
    positive = land_pre AND S1 water in >= 2 of the peak events (2023-06-09 / 06-13 / 06-14)
    negative = land_pre AND dry in every observed post-breach event AND >= 6 post-breach events OBSERVED
    unlabelled = everything else -- predicted, never scored. NOT OBSERVED IS NOT DRY.

NO PER-ZONE TUNING. Identical thresholds on all three frames is the experiment, not an oversight: B3's cross-zone QA
already shows twice the false-water rate of B1/B2 on a known-land anchor (24.1 % against 11.8 / 11.7 %), and
compensating for that by moving a threshold would destroy the transferability measurement it is evidence for
(SRC-54, leave-one-location-out). If B3 fails the label gate, that is a result to report, not a defect to patch.

OBSERVATION OPPORTUNITY IS NOT THE SAME OPERATOR EVERYWHERE, and the provenance says so per pixel. `>= 2 of 3 peak
events` means something different where all three peak dates are seen and where only two are: in ZONE_3 orbit 14 ASC
covers 7 % of the zone, so 06-09 and 06-21 are effectively absent and the rule collapses to `06-13 AND 06-14`. Same
code, same threshold, different statistical operator. Hence `n_valid_peak` and `n_pos_peak` are written as BANDS, so
a later analysis can separate a method-transfer failure from an observation-opportunity shift.

LABELS ARE NATIVE 20 m. The S1 water masks live on the zone grids at 20 m; the labels are computed there and
replicated to the 10 m lattice with nearest neighbour, which is exact because a 20 m zone cell is exactly two lattice
cells per axis. No label information is invented at 10 m, and the tag `label_native_m=20` records it.

ONE CACHE PER FRAME, coverage gaps reported rather than patched from a neighbouring zone's cache -- the same
one-lineage-per-product rule the optical side is frozen under.

Outputs: $BULK_ROOT/frames10/<FID>/labels.tif (8 bands), outputs/tables/p60_label_{summary,provenance,by_date}.csv
"""
from __future__ import annotations
import argparse, os, sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

PEAK = ("2023-06-09", "2023-06-13", "2023-06-14")
BREACH = "2023-06-06"
PRE_WF_MAX = 20.0          # pre-breach Sentinel-2 water frequency, %: above this the cell is water, not flooded land
N_PEAK_REQUIRED = 2
N_POST_OBS_REQUIRED = 6
OUT = CFG.BULK_ROOT / "frames10"

#: frame -> (S1 per-scene water cache, pre-breach S2 water-frequency raster). One cache per frame.
SRC = {
    "B1": ("ZONE_4_FLOODWAY_june2023_s32", "outputs/rasters/zone4/zone4_water_frac_PRE_BREACH_20m.tif"),
    "B2": ("ZONE_2_KHERSON_DELTA_flood_june2023", "outputs/rasters/zone2/zone2_water_frac_PRE_BREACH_20m.tif"),
    "B3": ("ZONE_3_DNIPRO_BUG_ESTUARY_flood_june2023", "outputs/rasters/zone3/zone3_water_frac_PRE_BREACH_20m.tif"),
}
BANDS = ("label", "n_valid_peak", "n_pos_peak", "n_post_obs", "n_post_wet", "n_pre_obs", "n_pre_wet", "pre_water_frac")


def load_events(cache_name):
    """{event_id: (water, valid)} on the cache's own 20 m grid, plus that grid."""
    p = CFG.S1_CACHE / cache_name / "per_scene_water.npz"
    z = np.load(p, allow_pickle=True)
    shp = tuple(int(v) for v in z["shape"]); cell = float(z["cell"])
    tr = from_origin(float(z["x0"]), float(z["y1"]), cell, cell)
    ev = {}
    for k in [k for k in z.keys() if k[:4] == "2023" and not k.startswith("valid_")]:
        vk = "valid_" + k
        if vk not in z:
            raise SystemExit(f"{p}: {k} has no {vk} -- dry cannot be told from unobserved. Rebuild the cache.")
        ev[k] = (np.unpackbits(z[k], count=shp[0] * shp[1]).astype(bool).reshape(shp),
                 np.unpackbits(z[vk], count=shp[0] * shp[1]).astype(bool).reshape(shp))
    return ev, shp, tr, cell


def to_frame(src, tr, F, dtype, nodata, resampling=Resampling.nearest):
    dst = np.full((F["ny"], F["nx"]), nodata, dtype)
    reproject(source=src.astype(dtype), destination=dst, src_transform=tr, src_crs=CFG.CRS_METRIC,
              dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC, resampling=resampling,
              src_nodata=nodata, dst_nodata=nodata)
    return dst


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=list(CG.FRAME_BBOX))
    a = ap.parse_args()
    summary, prov, bydate = [], [], []
    for fid in a.frames:
        F = CG.frame_grid(fid)
        cache, wf_path = SRC[fid]
        ev, shp, tr, cell = load_events(cache)
        assert abs(tr.c % cell) < 1e-9 and abs(tr.f % cell) < 1e-9, "cache grid is not on its own cell multiple"
        dates = sorted(ev)
        pre_d = [d for d in dates if d[:10] < BREACH]
        post_d = [d for d in dates if d[:10] > BREACH]
        peak_d = [d for d in dates if d[:10] in PEAK]
        print(f"\n=== {fid} ({cache}) ===")
        print(f"  {len(dates)} events: {len(pre_d)} pre, {len(post_d)} post, {len(peak_d)} peak", flush=True)

        z = np.zeros(shp, "u1")
        n_pre_obs = z.copy(); n_pre_wet = z.copy(); n_post_obs = z.copy(); n_post_wet = z.copy()
        n_valid_peak = z.copy(); n_pos_peak = z.copy()
        for k in dates:
            w, v = ev[k]
            d = k[:10]
            if d < BREACH:
                n_pre_obs += v; n_pre_wet += (w & v)
            elif d > BREACH:
                n_post_obs += v; n_post_wet += (w & v)
            if d in PEAK:
                n_valid_peak += v; n_pos_peak += (w & v)
            bydate.append(dict(frame=fid, cache=cache, event_id=k, date=d,
                               phase="PRE" if d < BREACH else ("BREACH_DAY" if d == BREACH else "POST"),
                               is_peak=d in PEAK, valid_fraction_cache=round(float(v.mean()), 4),
                               water_fraction_of_valid=round(float(w[v].mean()), 4) if v.any() else np.nan))

        with rasterio.open(ROOT / wf_path) as s:
            wf = s.read(1).astype("f4"); wf[wf == s.nodata] = np.nan if s.nodata is not None else np.nan
            wf_on_cache = np.full(shp, np.nan, "f4")
            reproject(source=wf, destination=wf_on_cache, src_transform=s.transform, src_crs=s.crs,
                      dst_transform=tr, dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest,
                      src_nodata=np.nan, dst_nodata=np.nan)

        # a missing water-frequency value must not silently pass the "< 20 %" test
        land_pre = (n_pre_obs >= 1) & (n_pre_wet == 0) & (np.nan_to_num(wf_on_cache, nan=100.0) < PRE_WF_MAX)
        pos = land_pre & (n_pos_peak >= N_PEAK_REQUIRED)
        neg = land_pre & (n_post_wet == 0) & (n_post_obs >= N_POST_OBS_REQUIRED)
        lab = np.full(shp, 2, "u1"); lab[neg] = 0; lab[pos] = 1        # 2 = unlabelled, inside S1 coverage
        lab[n_pre_obs + n_post_obs == 0] = 255                          # never observed by S1 at all

        px20 = cell * cell / 1e6
        print(f"  on the cache grid: pos {int(pos.sum()):,} px ({pos.sum()*px20:,.1f} km2), "
              f"neg {int(neg.sum()):,} px ({neg.sum()*px20:,.0f} km2), "
              f"land_pre {land_pre.sum()*px20:,.0f} km2", flush=True)

        bands = dict(label=lab, n_valid_peak=n_valid_peak, n_pos_peak=n_pos_peak, n_post_obs=n_post_obs,
                     n_post_wet=n_post_wet, n_pre_obs=n_pre_obs, n_pre_wet=n_pre_wet)
        prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=len(BANDS), dtype="int16",
                    crs=CFG.CRS_METRIC, transform=F["transform"], compress="deflate", predictor=2, tiled=True,
                    blockxsize=512, blockysize=512, nodata=-32768, BIGTIFF="IF_SAFER")
        out = OUT / fid / "labels.tif"; part = out.with_suffix(".tif.part")
        with rasterio.open(part, "w", **prof) as dst:
            for i, nm in enumerate(BANDS, 1):
                dst.set_band_description(i, nm)
                if nm == "pre_water_frac":
                    arr = to_frame(np.nan_to_num(wf_on_cache, nan=-32768.0), tr, F, "f4", -32768.0)
                    dst.write(np.round(arr).astype("i2"), i)
                else:
                    src = bands[nm]
                    nd = 255 if nm == "label" else 0
                    arr = to_frame(src, tr, F, "u1", nd)
                    out16 = arr.astype("i2")          # WIDEN FIRST, then substitute.
                    if nm == "label":
                        # np.where(arr == 255, -32768, arr) on a uint8 array keeps uint8 under NEP 50 and wraps:
                        # -32768 mod 256 == 0, so every cell NO SENSOR EVER SAW became label 0 = NEGATIVE, a
                        # confident dry vote over 979 km2 of B1 alone. Not observed is not dry -- the rule this
                        # pipeline is built on, defeated by an integer width.
                        out16[arr == 255] = -32768
                    dst.write(out16, i)
            dst.update_tags(
                rule=f"pos: land_pre & n_pos_peak >= {N_PEAK_REQUIRED}; "
                     f"neg: land_pre & n_post_wet == 0 & n_post_obs >= {N_POST_OBS_REQUIRED}; "
                     f"land_pre: n_pre_obs >= 1 & n_pre_wet == 0 & pre_water_frac < {PRE_WF_MAX}",
                label_values="0 negative, 1 positive, 2 unlabelled (inside S1 coverage), -32768 no S1 observation",
                label_kind="WEAK REFERENCE from Sentinel-1, not ground truth (SRC-45)",
                label_native_m=str(int(cell)), replication="nearest, exact: one 20 m cell = 2x2 lattice cells",
                s1_cache=cache, pre_water_frac_source=wf_path, frame=fid,
                candidate_peak_dates="|".join(PEAK), usable_peak_dates="|".join(sorted({d[:10] for d in peak_d})),
                n_peak_required=str(N_PEAK_REQUIRED), n_post_obs_required=str(N_POST_OBS_REQUIRED),
                no_per_zone_tuning="thresholds identical on B1/B2/B3 by design",
                producer="p60_reference_labels.py")
        with rasterio.open(part) as chk:
            assert (chk.height, chk.width) == (F["ny"], F["nx"]) and chk.count == len(BANDS)
            L = chk.read(1)
        os.replace(part, out)

        px10 = CG.CELL * CG.CELL / 1e6
        npos = int((L == 1).sum()); nneg = int((L == 0).sum()); nun = int((L == 2).sum()); nno = int((L == -32768).sum())
        summary.append(dict(frame=fid, cache=cache, n_events=len(dates), n_pre=len(pre_d), n_post=len(post_d),
                            n_peak_candidate=len(PEAK), n_peak_usable=len({d[:10] for d in peak_d}),
                            n_positive=npos, n_negative=nneg, n_unlabelled=nun, n_no_s1=nno,
                            km2_positive=round(npos * px10, 2), km2_negative=round(nneg * px10, 1),
                            km2_unlabelled=round(nun * px10, 1), km2_no_s1=round(nno * px10, 1),
                            frame_km2=round(F["nx"] * F["ny"] * px10, 1),
                            s1_coverage_pct=round(100 * (1 - nno / (F["nx"] * F["ny"])), 2),
                            prevalence=round(npos / max(npos + nneg, 1), 4)))
        print(f"  on the frame lattice: pos {npos:,} ({npos*px10:,.1f} km2), neg {nneg:,} ({nneg*px10:,.0f} km2), "
              f"unlabelled {nun*px10:,.0f} km2, no S1 {nno*px10:,.0f} km2 "
              f"({summary[-1]['s1_coverage_pct']:.1f} % of the frame has S1)", flush=True)
        for d in sorted({x[:10] for x in peak_d}):
            prov.append(dict(frame=fid, peak_date=d, present=True))
        for d in PEAK:
            if d not in {x[:10] for x in peak_d}:
                prov.append(dict(frame=fid, peak_date=d, present=False))

    pd.DataFrame(summary).to_csv(CFG.TABLES / "p60_label_summary.csv", index=False)
    pd.DataFrame(prov).to_csv(CFG.TABLES / "p60_label_provenance.csv", index=False)
    pd.DataFrame(bydate).to_csv(CFG.TABLES / "p60_label_by_date.csv", index=False)
    print("\n" + pd.DataFrame(summary)[["frame", "n_peak_usable", "n_positive", "km2_positive", "n_negative",
                                        "km2_negative", "s1_coverage_pct", "prevalence"]].to_string(index=False))
    print("\n-> outputs/tables/p60_label_{summary,provenance,by_date}.csv")
    print("LABELS ARE CONSTRUCTED, NOT FROZEN. The p61 label-QA gate decides.")


if __name__ == "__main__":
    main()
