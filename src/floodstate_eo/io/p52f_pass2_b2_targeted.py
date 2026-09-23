# Provenance: SWOT-DNIPRO scripts/p52f_pass2_b2_targeted.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 7 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo; importlib loads of p52a/p52b/p52c -> package imports.
"""P52f -- PASS 2, targeted at B2 only: rank 20-60 % cloud products by the clear coverage they can ADD inside the frame.

After PASS 1 the event-window coverage is 99.88 / 99.75 / 99.96 % of B1 / B2 / B3, so a blanket 20-60 % sweep would be
tens of gigabytes for a few tens of km2. One weakness remains and it is temporal, not spatial: B2 has NO cell with six
or more valid observations (max 4, median 3, and 6.0 % of the frame seen only once), while B1 and B3 both have a third
of their area at 6+. A cell seen once cannot support a change statistic.

So this pass asks only for B2, and it does not download on sight. Each candidate is scored by what it could add:

    expected_new_clear_km2 = area(footprint INTERSECT B2 INTERSECT cells currently below the target count)
                             x (1 - cloudCover/100)

cloudCover is tile-wide, so this is an EXPECTATION, not a measurement -- the real gain is measured from SCL after the
fetch, and the ranking exists only to spend bandwidth in the right order. Products on dates already in the record score
lower on purpose: a new date buys temporal independence, a duplicate date mostly buys the same pixels again.
Outputs: <case_study>/tables/p52f_b2_candidates.csv, p52f_b2_download_list.csv
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, pyproj, rasterio
from shapely import wkt as shp_wkt
from shapely.geometry import box, shape
from shapely.ops import transform as shp_transform
from .. import _kakhovka_legacy_config as CFG
from . import p52c_cdse_optical_gap as P52C
from ..spatial import p52a_processing_frames_qa as P52A
from ..spatial import p52b_frame_sensor_inventory as P52B

FID = "B2"
BBOX = P52A.FRAMES[FID]["bbox"]
EVENT = ("2023-06-07", "2023-07-31")
CLOUD_LO, CLOUD_HI = 20.0, 60.0
TARGET_OBS = 6                 # the count B1 and B3 reach and B2 does not
TO_M = pyproj.Transformer.from_crs("EPSG:4326", CFG.CRS_METRIC, always_xy=True).transform


def main():
    frame = box(*BBOX)
    F = P52B.frame_grid(BBOX)
    cov = CFG.BULK_ROOT / "frames" / FID / "s2_event_obs_count_pass1.tif"
    with rasterio.open(cov) as ds:
        c = ds.read(1)
    thin = c < TARGET_OBS                       # where another observation actually buys something
    px = 20.0 * 20.0 / 1e6
    print(f"{FID}: {frame.area/1e6:,.0f} km2; cells below {TARGET_OBS} observations: "
          f"{thin.sum()*px:,.0f} km2 ({100*thin.mean():.1f} %); median now {int(np.median(c))}, max {int(c.max())}\n")

    have = set(pd.read_csv(CFG.TABLES / "p52e_event_coverage_by_date.csv").date)
    tok = P52C.token()
    rows = P52C.query(FID, BBOX, EVENT[0], EVENT[1], tok, cloud_max=CLOUD_HI)
    A = pd.DataFrame(rows)
    A = A[(A.cloud > CLOUD_LO) & (A.cloud <= CLOUD_HI)].copy()
    if A.empty:
        print("no 20-60 % products over B2 in the event window"); return
    print(f"CDSE: {len(A)} products at {CLOUD_LO:.0f}-{CLOUD_HI:.0f} % cloud, {A.date.nunique()} distinct dates", flush=True)

    # footprint of each product, intersected with the frame and with the cells that are still thin
    foot, exp = [], []
    for _, r in A.iterrows():
        g = None
        try:
            fp = r.get("footprint") or ""
            if fp:
                g = shp_wkt.loads(fp.split(";")[-1]) if ";" in fp else shp_wkt.loads(fp)
        except Exception:
            g = None
        if g is None:
            inter = frame                                   # no geometry returned -> assume it covers the frame
        else:
            inter = shp_transform(TO_M, g).intersection(frame)
        foot.append(round(inter.area / 1e6, 1))
        # how much of that intersection is still below the target count
        if inter.is_empty:
            exp.append(0.0); continue
        from rasterio import features as rf
        m = rf.rasterize([(inter, 1)], out_shape=(F["ny"], F["nx"]), transform=F["transform"], fill=0,
                         dtype="uint8").astype(bool) & thin
        exp.append(round(m.sum() * px * (1.0 - float(r["cloud"]) / 100.0), 1))
    A["frame_overlap_km2"] = foot
    A["expected_new_clear_km2"] = exp
    A["date_is_new"] = ~A.date.isin(have)
    A["score"] = A.expected_new_clear_km2 * np.where(A.date_is_new, 1.0, 0.35)
    A = A.sort_values("score", ascending=False)
    A.to_csv(CFG.TABLES / "p52f_b2_candidates.csv", index=False)
    pd.set_option("display.width", 240)
    print("\nRANKED CANDIDATES (score = expected new clear km2, x0.35 if the date is already in the record)")
    print(A[["date", "tile", "cloud", "size_gb", "frame_overlap_km2", "expected_new_clear_km2",
             "date_is_new", "score"]].head(20).to_string(index=False))
    pick = A[(A.score >= 50.0)].drop_duplicates("name")
    pick.to_csv(CFG.TABLES / "p52f_b2_download_list.csv", index=False)
    print(f"\nselected (score >= 50 km2): {len(pick)} products, {pick.size_gb.sum():.1f} GB, "
          f"{pick.date.nunique()} dates, {int(pick.date_is_new.sum())} of them on NEW dates")
    print("-> <case_study>/tables/p52f_b2_{candidates,download_list}.csv")


if __name__ == "__main__":
    main()
