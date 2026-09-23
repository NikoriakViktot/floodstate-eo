# Provenance: SWOT-DNIPRO scripts/p83_coherence_qc.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 21 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo; WORK stays the same machine-specific
# absolute path as p82 writes to.
"""P83 -- the ENGINEERING gate on a coherence raster. Five technical questions, and no scientific ones.

    G1  the graph completed and the product opens with the expected coherence bands
    G2  coherence lies in [0, 1] -- values outside it mean the estimator or the export is wrong
    G3  valid pixels cover enough of frame B2 to anchor a frame-wide layer
    G4  no seam between subswaths, slices or bursts: a step at a processing boundary is an artefact
    G5  ESD reported a coregistration shift, and it is not an outlier

THIS GATE MAY STOP THE EXPERIMENT. THE SCIENCE MAY NOT. Nothing here looks at labels, at land cover, or at whether
coherence separates flooded from dry. Deciding how much data to process after glimpsing the effect, and then
estimating that same effect, is optional stopping. G1-G5 are about whether the raster is a valid measurement, not
whether it is a useful one.

G4 IS THE ONE WORTH EXPLAINING. Frames 65 and 87 merge IW2 and IW3; 14 and 138 use IW1 alone. A subswath merge
that went wrong shows up as a discontinuity along a near-vertical line in range, and a slice assembly that went
wrong shows up along a near-horizontal one. Both are detected the same way -- compare the mean of adjacent column
(and row) strips and look for a step far larger than the local noise. A regular structure at a processing
boundary is an implementation artefact, never geography.

Outputs: <case_study>/tables/p83_coherence_qc.csv  (one row per raster, with the verdict and every measured quantity)
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio.warp import reproject
from rasterio.enums import Resampling
from .. import _kakhovka_legacy_config as CFG
from ..spatial import canonical_grid as CG

WORK = Path("/home/niko/data_s1_coh")
MIN_COVER = 0.60          # a frame-wide layer needs most of the frame; below this the pair cannot anchor one
SEAM_SIGMA = 6.0          # a step this many local standard deviations across a boundary is not terrain
STRIP = 8                 # columns/rows averaged either side of a candidate seam


def seam_scan(a, axis):
    """Largest step between adjacent strips, expressed in local standard deviations.

    Returns (z, index). A merge or assembly artefact produces one large isolated step; real terrain produces many
    small ones, so the maximum z over all positions is the discriminating statistic rather than the mean.
    """
    m = np.nanmean(a, axis=1 - axis)                      # profile across the axis of interest
    if m.size < 4 * STRIP:
        return np.nan, -1
    k = np.convolve(np.nan_to_num(m), np.ones(STRIP) / STRIP, "same")
    d = np.abs(np.diff(k))
    s = np.nanstd(d)
    if not np.isfinite(s) or s == 0:
        return np.nan, -1
    i = int(np.nanargmax(d))
    return float(d[i] / s), i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="coh_orb*.tif")
    a = ap.parse_args()
    F = CG.frame_grid("B2")
    files = sorted(WORK.glob(a.glob))
    if not files:
        raise SystemExit(f"no rasters matching {a.glob} in {WORK}")
    esd_p = CFG.TABLES / "p82_esd_diagnostics.csv"
    esd = pd.read_csv(esd_p) if esd_p.exists() else pd.DataFrame()
    rows = []
    for f in files:
        r = dict(raster=f.name, size_gb=round(f.stat().st_size / 1e9, 3))
        try:
            with rasterio.open(f) as s:
                desc = [d or "" for d in s.descriptions]
                idx = [i + 1 for i, d in enumerate(desc) if "coh" in d.lower()] or list(range(1, s.count + 1))
                r["n_bands"] = s.count
                r["coh_bands"] = ",".join(desc[i - 1] for i in idx) or "(unnamed)"
                r["G1_opens"] = True
                arr = np.stack([s.read(i, masked=True).filled(np.nan) for i in idx])
                src_tr, src_crs = s.transform, s.crs
        except Exception as e:
            rows.append({**r, "G1_opens": False, "verdict": f"FAIL_OPEN: {type(e).__name__}"}); continue

        v = arr[np.isfinite(arr)]
        r["n_valid_px"] = int(v.size)
        if v.size == 0:
            rows.append({**r, "verdict": "FAIL_EMPTY: no finite coherence values"}); continue
        r["coh_min"] = round(float(v.min()), 4); r["coh_max"] = round(float(v.max()), 4)
        r["coh_median"] = round(float(np.median(v)), 4)
        out01 = float(((v < 0) | (v > 1)).mean())
        r["frac_outside_0_1"] = round(out01, 6)
        r["G2_range_ok"] = bool(out01 < 1e-6)

        # G3 -- reproject the valid mask onto the canonical frame and measure real coverage of B2
        m = np.zeros((F["ny"], F["nx"]), "u1")
        reproject(source=np.isfinite(arr[0]).astype("u1"), destination=m,
                  src_transform=src_tr, src_crs=src_crs,
                  dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC,
                  resampling=Resampling.nearest, src_nodata=0, dst_nodata=0)
        cov = float(m.mean())
        r["b2_valid_cover"] = round(cov, 4)
        r["G3_cover_ok"] = bool(cov >= MIN_COVER)

        zc, ic = seam_scan(arr[0], 0)
        zr, ir = seam_scan(arr[0], 1)
        r["seam_z_range"] = round(zc, 2) if np.isfinite(zc) else None
        r["seam_z_azimuth"] = round(zr, 2) if np.isfinite(zr) else None
        r["G4_no_seam"] = bool((not np.isfinite(zc) or zc < SEAM_SIGMA)
                               and (not np.isfinite(zr) or zr < SEAM_SIGMA))

        orb = int(f.name.split("_orb")[1].split("_")[0])
        pre, ev = f.name.replace(".tif", "").split("_")[-2:]
        e = esd[(esd.rel_orbit == orb) & (esd.pre_date == pre) & (esd.event_date == ev)] if len(esd) else esd
        if len(e):
            r["esd_azimuth_shift"] = float(e.azimuth_shift.dropna().abs().max()) if e.azimuth_shift.notna().any() else None
            r["G5_esd_ok"] = bool(e.shift_reported.all()
                                  and (r["esd_azimuth_shift"] is None or r["esd_azimuth_shift"] < 0.5))
        else:
            r["esd_azimuth_shift"] = None
            r["G5_esd_ok"] = None                          # not measured is not passed
        gates = [r.get(k) for k in ("G1_opens", "G2_range_ok", "G3_cover_ok", "G4_no_seam", "G5_esd_ok")]
        failed = [k for k, val in zip(("G1", "G2", "G3", "G4", "G5"), gates) if val is False]
        unknown = [k for k, val in zip(("G1", "G2", "G3", "G4", "G5"), gates) if val is None]
        r["verdict"] = ("PASS" if not failed and not unknown else
                        ("FAIL: " + ",".join(failed)) if failed else "INCOMPLETE: " + ",".join(unknown))
        rows.append(r)
    T = pd.DataFrame(rows)
    T.to_csv(CFG.TABLES / "p83_coherence_qc.csv", index=False)
    cols = [c for c in ("raster", "size_gb", "n_bands", "coh_median", "coh_min", "coh_max",
                        "frac_outside_0_1", "b2_valid_cover", "seam_z_range", "seam_z_azimuth",
                        "esd_azimuth_shift", "verdict") if c in T.columns]
    print(T[cols].to_string(index=False))
    print(f"\nthresholds: coverage >= {MIN_COVER:.0%}, seam z < {SEAM_SIGMA}, |ESD azimuth shift| < 0.5 px")
    print("This gate is technical. It does not look at labels and cannot be used to decide whether the "
          "scientific effect is worth pursuing.")
    print(f"-> <case_study>/tables/p83_coherence_qc.csv")
    if (T.verdict != "PASS").any():
        raise SystemExit("not every raster passed -- resolve before processing the remaining pairs")


if __name__ == "__main__":
    main()
