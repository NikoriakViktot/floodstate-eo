# Provenance: SWOT-DNIPRO scripts/p70a_disputed_fields_hand.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# migration_date=2026-09-23. M6 recovery (not in the Phase-5 manifest; removed from SWOT-DNIPRO by 9419ea3).
# STATUS: ACTIVE_DIAGNOSTIC -- disputed-area HAND diagnostic; reads p69b-era disputed definition (label contract v001).
# Import/path block only: swot_dnipro -> floodstate_eo; ROOT -> case_studies/kakhovka_2023. Logic unchanged.
"""P70a -- can the disputed fields physically flood? HAND asked as a QUESTION, never used as a veto.

347.2 km2 of the lower Dnipro is claimed as peak water by the Sentinel-1 masks and not mapped by the optical model.
In B1 most of it sits on cropland, in rectangular parcel-shaped patches, more than a kilometre from any pre-breach
water -- the signature of the false-water population this project has documented before. But "looks like a field"
is not evidence. Height Above Nearest Drainage is, because a surface that stands 15 m above the nearest channel
cannot be inundated by a river flood whatever the backscatter says.

HAND ERASES NOTHING HERE (SRC-55: HAND has systematic limits and is not a reliable pixel-level wet/dry classifier;
SRC-82: operational practice uses terrain as context and advisory, not as a veto). This script only compares
distributions and marks conflicts for review:

    agreed        both sensors -- the reference distribution of what flooding looks like here
    S1 only       the disputed area
    M2 only       optical response without an S1 peak observation

If the disputed area sits at the same HAND as the agreed flood, the field hypothesis is weak and those hectares may
be real inundation that the optical window missed. If it sits far higher, the S1 masks are claiming water on ground
the water could not reach.

Outputs: outputs/tables/p70a_disputed_hand.csv, outputs/figures/p70a_disputed_hand_<FRAME>.png
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]    # case_studies/kakhovka_2023 -- runs/ live here, as they did at the source repo root
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
FR = ("B1", "B2", "B3")
SRC = {"B1": "ZONE_4_FLOODWAY_june2023_s32", "B2": "ZONE_2_KHERSON_DELTA_flood_june2023",
       "B3": "ZONE_3_DNIPRO_BUG_ESTUARY_flood_june2023"}
HAND = {"B1": ("floodplain/ZONE_4_DAM_TO_KHERSON_FLOODWAY/ZONE_4_DAM_TO_KHERSON_FLOODWAY_hand_m.tif", "HAND"),
        "B2": ("floodplain/ZONE_2_KHERSON_DELTA/ZONE_2_KHERSON_DELTA_hand_m.tif", "HAND"),
        "B3": ("terrain/ZONE_3_DNIPRO_BUG_ESTUARY/hand_proxy_20m.tif", "HAND proxy")}
PEAK = ("2023-06-09", "2023-06-13", "2023-06-14")
BINS = [0, 1, 2, 3, 5, 10, 20, np.inf]
PX = 1e-4


def owner(fid):
    F = CG.frame_grid(fid); own = np.ones((F["ny"], F["nx"]), bool)
    for p in FR[:FR.index(fid)]:
        GP = CG.frame_grid(p)
        x0, x1 = max(F["x0"], GP["x0"]), min(F["x1"], GP["x1"])
        y0, y1 = max(F["y0"], GP["y0"]), min(F["y1"], GP["y1"])
        if x1 <= x0 or y1 <= y0:
            continue
        own[int(round((F["y1"] - y1) / 10)):int(round((F["y1"] - y0) / 10)),
            int(round((x0 - F["x0"]) / 10)):int(round((x1 - F["x0"]) / 10))] = False
    return own


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=list(FR)); a = ap.parse_args()
    rows = []
    for fid in a.frames:
        F = CG.frame_grid(fid); own = owner(fid)
        hp = CFG.BULK_ROOT / HAND[fid][0]
        if not hp.exists():
            print(f"  {fid}: no HAND ({hp.name}) -- skipped"); continue
        hand = np.full((F["ny"], F["nx"]), np.nan, "f4")
        with rasterio.open(hp) as s:
            src = s.read(1).astype("f4")
            nd = s.nodata if s.nodata is not None else -9999
            src[src == nd] = np.nan; src[src < -100] = np.nan
            reproject(source=src, destination=hand, src_transform=s.transform, src_crs=s.crs,
                      dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC, resampling=Resampling.bilinear,
                      src_nodata=np.nan, dst_nodata=np.nan)
        z = np.load(CFG.S1_CACHE / SRC[fid] / "per_scene_water.npz", allow_pickle=True)
        shp = tuple(int(v) for v in z["shape"]); cell = float(z["cell"])
        tr = from_origin(float(z["x0"]), float(z["y1"]), cell, cell); wet = np.zeros(shp, bool)
        for k in [k for k in z.keys() if k[:4] == "2023" and not k.startswith("valid_")]:
            if k[:10] not in PEAK:
                continue
            w = np.unpackbits(z[k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
            v = np.unpackbits(z["valid_" + k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
            wet |= (w & v)
        d = np.zeros((F["ny"], F["nx"]), "u1")
        reproject(source=wet.astype("u1"), destination=d, src_transform=tr, src_crs=CFG.CRS_METRIC,
                  dst_transform=F["transform"], dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest,
                  src_nodata=0, dst_nodata=0)
        s1 = d.astype(bool)
        with rasterio.open(OUT / fid / "p69a_base_class.tif") as s:
            bc = s.read(1)
        with rasterio.open(OUT / fid / "p69b_semantic_state.tif") as s:
            sem = s.read(1)
        land = (bc != 0) & (bc != 255)
        m2 = np.isin(sem, (1, 2, 3, 4, 5)) & own & land
        s1l = s1 & own & land
        groups = {"agreed": m2 & s1l, "S1_only": s1l & ~m2, "M2_only": m2 & ~s1l}
        for gname, g in groups.items():
            h = hand[g & np.isfinite(hand)]
            if h.size == 0:
                continue
            q = np.percentile(h, [10, 25, 50, 75, 90])
            r = dict(frame=fid, hand_source=HAND[fid][1], group=gname, km2=round(float(g.sum()) * PX, 1),
                     hand_p10=round(float(q[0]), 2), hand_p25=round(float(q[1]), 2),
                     hand_median=round(float(q[2]), 2), hand_p75=round(float(q[3]), 2),
                     hand_p90=round(float(q[4]), 2))
            for lo, hi in zip(BINS[:-1], BINS[1:]):
                r[f"km2_hand_{lo:g}-{hi:g}"] = round(float(((h >= lo) & (h < hi)).sum()) * PX, 1)
            rows.append(r)
        ag = [x for x in rows if x["frame"] == fid and x["group"] == "agreed"]
        lim = ag[0]["hand_p90"] if ag else np.nan          # where the flood the two sensors agree on actually sits
        conflict = groups["S1_only"] & np.isfinite(hand) & (hand > lim)
        rows[-1]["note"] = f"S1_only above the p90 HAND of the agreed flood ({lim:.2f} m): " \
                           f"{float(conflict.sum())*PX:,.1f} km2"
        print(f"  {fid}: agreed median HAND {ag[0]['hand_median'] if ag else np.nan:.2f} m, "
              f"S1_only median {[x for x in rows if x['frame']==fid and x['group']=='S1_only'][0]['hand_median']:.2f} m,"
              f" S1_only above agreed-p90: {float(conflict.sum())*PX:,.1f} km2", flush=True)

        st = max(1, int(max(F["ny"], F["nx"]) / 1600))
        cat = np.zeros((F["ny"], F["nx"]), np.uint8)
        cat[groups["agreed"]] = 1
        cat[groups["S1_only"] & np.isfinite(hand) & (hand <= lim)] = 2
        cat[conflict] = 3
        cat[groups["M2_only"]] = 4
        cs = cat[::st, ::st]; hs = hand[::st, ::st]
        fig, ax = plt.subplots(figsize=(11, 11 * cs.shape[0] / cs.shape[1]), dpi=130)
        ax.imshow(np.clip(hs, 0, 25), cmap="terrain_r", vmin=0, vmax=25, interpolation="nearest")
        cm = ListedColormap(["#00000000", "#2f855a", "#dd6b20", "#c53030", "#3182ce"])
        ax.imshow(cs, cmap=cm, vmin=-0.5, vmax=4.5, alpha=np.where(cs > 0, 0.95, 0.0), interpolation="nearest")
        a_low = float((cat == 2).sum()) * PX; a_hi = float((cat == 3).sum()) * PX
        ax.set_title(f"{fid} — disputed Sentinel-1 area against {HAND[fid][1]}\n"
                     f"green agreed flood · orange S1-only at floodable height ({a_low:,.1f} km²) · "
                     f"red S1-only ABOVE the agreed flood's p90 HAND = {lim:.1f} m ({a_hi:,.1f} km²) · "
                     f"blue M2 only\nbackground: HAND 0–25 m. HAND is a diagnostic here and deletes nothing.",
                     fontsize=8)
        ax.legend(handles=[Patch(facecolor="#2f855a", label="agreed flood (both sensors)"),
                           Patch(facecolor="#dd6b20", label="S1-only, topographically floodable"),
                           Patch(facecolor="#c53030", label="S1-only, above the agreed flood height"),
                           Patch(facecolor="#3182ce", label="M2 only")],
                  loc="lower left", fontsize=7, framealpha=0.9)
        ax.set_xticks([]); ax.set_yticks([])
        fig.tight_layout(); fig.savefig(CFG.FIG / f"p70a_disputed_hand_{fid}.png", bbox_inches="tight")
        plt.close(fig)
        del hand, s1, bc, sem, cat, own
    D = pd.DataFrame(rows); D.to_csv(CFG.TABLES / "p70a_disputed_hand.csv", index=False)
    print("\n" + D[["frame", "group", "km2", "hand_p10", "hand_median", "hand_p90"]].to_string(index=False))
    print("\n-> outputs/tables/p70a_disputed_hand.csv, outputs/figures/p70a_disputed_hand_*.png")


if __name__ == "__main__":
    main()
