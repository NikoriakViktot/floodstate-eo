# Provenance: SWOT-DNIPRO scripts/p69c_maps.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 16 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo.
"""P69c -- maps of the event-association product, and of what the optical model does NOT recover.

Two figures per frame:
  1. semantic_state over an MNDWI event-maximum backdrop, with decision stability shown by opacity
  2. the recovery map: where Sentinel-1 saw water on land at the peak, and where M2 agrees, misses or adds

The second one is the point. Sentinel-1 observed 552.9 km2 of water on non-water BASE_CLASS during the peak events
(09, 13, 14 June); the optical product maps 278.3 km2, half of it, and the recovery rate is 62 % in B1, 23 % in B2
and 13 % in B3. A map says where that half went in a way no table can.
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from .. import _kakhovka_legacy_config as CFG
from ..spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
FR = ("B1", "B2", "B3")
SRC = {"B1": "ZONE_4_FLOODWAY_june2023_s32", "B2": "ZONE_2_KHERSON_DELTA_flood_june2023",
       "B3": "ZONE_3_DNIPRO_BUG_ESTUARY_flood_june2023"}
PEAK = ("2023-06-09", "2023-06-13", "2023-06-14")
SEMC = {0: ("#2b6cb0", "pre-existing water"), 1: ("#48bb78", "flood-assoc. vegetation/agri"),
        2: ("#d69e2e", "flood-assoc. wetland"), 3: ("#e53e3e", "flood-assoc. built-up"),
        4: ("#ed8936", "flood-assoc. bare/sand"), 5: ("#9f7aea", "flood-assoc. other dry"),
        6: ("#e2e8f0", "non-flooded"), 7: ("#a0aec0", "uncertain base state")}
PX = 1e-4


def owner(fid):
    F = CG.frame_grid(fid); own = np.ones((F["ny"], F["nx"]), bool)
    for prev in FR[:FR.index(fid)]:
        GP = CG.frame_grid(prev)
        x0, x1 = max(F["x0"], GP["x0"]), min(F["x1"], GP["x1"])
        y0, y1 = max(F["y0"], GP["y0"]), min(F["y1"], GP["y1"])
        if x1 <= x0 or y1 <= y0:
            continue
        c0 = int(round((x0 - F["x0"]) / 10)); c1 = int(round((x1 - F["x0"]) / 10))
        r0 = int(round((F["y1"] - y1) / 10)); r1 = int(round((F["y1"] - y0) / 10))
        own[r0:r1, c0:c1] = False
    return own


def s1_peak(fid, F):
    z = np.load(CFG.S1_CACHE / SRC[fid] / "per_scene_water.npz", allow_pickle=True)
    shp = tuple(int(v) for v in z["shape"]); cell = float(z["cell"])
    tr = from_origin(float(z["x0"]), float(z["y1"]), cell, cell)
    wet = np.zeros(shp, bool)
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
    return d.astype(bool)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=list(FR)); a = ap.parse_args()
    for fid in a.frames:
        F = CG.frame_grid(fid)
        st = max(1, int(max(F["ny"], F["nx"]) / 1700))
        with rasterio.open(OUT / fid / "p69b_semantic_state.tif") as s:
            sem = s.read(1)[::st, ::st]
        with rasterio.open(OUT / fid / "p69b_decision_stability5.tif") as s:
            stab = s.read(1)[::st, ::st]
        with rasterio.open(OUT / fid / "composite_preall.tif") as s:
            bg = s.read(list(s.descriptions).index("MNDWI_event_max") + 1)[::st, ::st].astype("f4")
        bg[bg <= -3.2767e4] = np.nan; bg /= 1e4

        # ---- figure 1: semantic state ------------------------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(11, 11 * sem.shape[0] / sem.shape[1]), dpi=130)
        ax.imshow(bg, cmap="Greys_r", vmin=-0.6, vmax=0.6, interpolation="nearest")
        cmap = ListedColormap([SEMC[k][0] for k in sorted(SEMC)])
        ov = np.full(sem.shape, np.nan)
        for i, k in enumerate(sorted(SEMC)):
            ov[sem == k] = i
        al = np.where(np.isin(sem, (1, 2, 3, 4, 5)), 0.95, np.where(sem == 0, 0.55, 0.30))
        al[sem == 255] = 0
        ax.imshow(ov, cmap=cmap, vmin=-0.5, vmax=len(SEMC) - 0.5, alpha=al, interpolation="nearest")
        ax.set_title(f"{fid} — semantic state (M2 central threshold 0.5358)\n"
                     f"FLOOD_ASSOCIATED means an optical event response on a known pre-event surface, "
                     f"not proof of open water", fontsize=9)
        ax.legend(handles=[Patch(facecolor=c, label=l) for _, (c, l) in sorted(SEMC.items())],
                  loc="lower left", fontsize=7, framealpha=0.9)
        ax.set_xticks([]); ax.set_yticks([])
        fig.tight_layout(); fig.savefig(CFG.FIG / f"p69c_semantic_{fid}.png", bbox_inches="tight"); plt.close(fig)

        # ---- figure 2: what the optical product does not recover ---------------------------------------------------
        with rasterio.open(OUT / fid / "p69a_base_class.tif") as s:
            bc_full = s.read(1)
        s1 = s1_peak(fid, F) & (bc_full != 0)
        own = owner(fid)
        with rasterio.open(OUT / fid / "p69b_semantic_state.tif") as s:
            sem_full = s.read(1)
        m2 = np.isin(sem_full, (1, 2, 3, 4, 5))
        agree = float((s1 & m2 & own).sum()) * PX
        miss = float((s1 & ~m2 & own).sum()) * PX
        add = float((~s1 & m2 & own).sum()) * PX
        cmp_ = np.zeros(sem.shape, np.uint8)
        s1s, m2s = s1[::st, ::st], m2[::st, ::st]
        cmp_[s1s & m2s] = 1; cmp_[s1s & ~m2s] = 2; cmp_[~s1s & m2s] = 3
        fig, ax = plt.subplots(figsize=(11, 11 * sem.shape[0] / sem.shape[1]), dpi=130)
        ax.imshow(bg, cmap="Greys_r", vmin=-0.6, vmax=0.6, interpolation="nearest")
        cc = ListedColormap(["#00000000", "#2f855a", "#c53030", "#3182ce"])
        ax.imshow(cmp_, cmap=cc, vmin=-0.5, vmax=3.5, alpha=np.where(cmp_ > 0, 0.95, 0.0),
                  interpolation="nearest")
        ax.set_title(f"{fid} — what the optical model recovers of the Sentinel-1 peak observation\n"
                     f"green both {agree:,.1f} km² · red S1 only (missed) {miss:,.1f} km² · "
                     f"blue M2 only {add:,.1f} km²", fontsize=9)
        ax.legend(handles=[Patch(facecolor="#2f855a", label="S1 peak water AND M2 flood-associated"),
                           Patch(facecolor="#c53030", label="S1 peak water, M2 does NOT map it"),
                           Patch(facecolor="#3182ce", label="M2 flood-associated, no S1 peak water")],
                  loc="lower left", fontsize=7, framealpha=0.9)
        ax.set_xticks([]); ax.set_yticks([])
        fig.tight_layout(); fig.savefig(CFG.FIG / f"p69c_recovery_{fid}.png", bbox_inches="tight"); plt.close(fig)
        print(f"  {fid}: both {agree:,.1f}, S1-only {miss:,.1f}, M2-only {add:,.1f} km2 "
              f"-> p69c_semantic_{fid}.png, p69c_recovery_{fid}.png", flush=True)
        del sem, stab, bg, bc_full, s1, m2, own, sem_full


if __name__ == "__main__":
    main()
