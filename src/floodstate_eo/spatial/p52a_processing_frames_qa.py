# Provenance: SWOT-DNIPRO scripts/p52a_processing_frames_qa.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 2 (migration_phase=5).
# Import block only: `sys.path`/`swot_dnipro` package imports -> floodstate_eo package imports (ROOT now means
# case_studies/kakhovka_2023; SD.load_utm resolved via the Kakhovka legacy loader shim, same call signature).
# KNOWN EVENT-AGNOSTIC GATE EXCEPTION: this script IS the Kakhovka frame definition; it is a case-study
# script placed under src/floodstate_eo/spatial per the migration manifest, not event-agnostic framework code.
"""P52a -- the three PROCESSING FRAMES, fixed by the user 2026-09-21, drawn once for visual checking.

The geography of the flood task is now FIXED and is not to be re-derived. Three axis-aligned rectangles in EPSG:32636 are
the processing domain; everything else -- HAND, basin polygons, water masks, the FABDEM ceiling, persistent water, the old
CUT_RECTS -- is information ABOUT a cell, never a reason to remove one. Every cell inside a frame goes through the pipeline
and gets an explicit status; there is no silent NoData inside a frame.

This figure exists only so the geography can be checked by eye before the recompute: the three frames, the settlements
that must be covered, the OLD p42 domain and the OLD CUT_RECTS as separate outlines so it is visible what used to be cut.
Outputs: <case_study>/figures/p52a_processing_frames.png/.pdf, <case_study>/tables/p52a_processing_frames.csv
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, pyproj, rasterio
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from shapely.geometry import box, MultiLineString
from .. import _kakhovka_legacy_config as CFG
from .. import _kakhovka_legacy_config as SD          # .load_utm(name) -- see that module's docstring
ROOT = CFG.ROOT

# THE PROCESSING DOMAIN. Confirmed by the user 2026-09-21. Do not re-derive, do not shrink, do not add a fourth.
FRAMES = {
    # B1 tightened 2026-09-21 on the user's call ("завелика"): east edge 9.8 km past the dam instead of 41 km into the
    # reservoir, north/south trimmed. Chosen by MEASUREMENT, not by eye -- 99.96 % of the S1 new water at the June peak
    # stays inside; the 0.04 % dropped is a handful of cells east of 538 km, already inside the pool.
    "B1": dict(zone="ZONE_4_DAM_TO_KHERSON_FLOODWAY", label="B1 · dam -> Kherson",
               bbox=(455680.0, 5138000.0, 538000.0, 5212000.0), colour="#1a9850"),
    "B2": dict(zone="ZONE_2_KHERSON_DELTA", label="B2 · Kherson -> delta",
               bbox=(438000.0, 5135002.0, 475685.0, 5211567.0), colour="#2166ac"),
    # B3 extended EAST to 465000 (user 2026-09-21): the old edge at 448000 stopped in the middle of the delta and left
    # Hola Prystan out. Only the east edge moved; north, west and south are unchanged.
    "B3": dict(zone="ZONE_3_DNIPRO_BUG_ESTUARY", label="B3 · delta with the liman",
               bbox=(374260.0, 5107360.0, 465000.0, 5267000.0), colour="#6a51a3"),
}
# The OLD exclusion boxes. Kept as a diagnostic overlay ONLY: they must never clip a processing frame again.
CUT_RECTS = ((462000.0, 5175000.0, 481000.0, 5300000.0),
             (481000.0, 5180000.0, 503000.0, 5300000.0),
             (503000.0, 5187000.0, 530000.0, 5300000.0))
TOWNS = {"Kakhovka dam": (33.3700, 46.7780), "Kherson": (32.6178, 46.6354),
         "Oleshky": (32.7100, 46.6300), "Hola Prystan": (32.5200, 46.5200),
         "Ochakiv": (31.5450, 46.6130), "Mykolaiv": (31.9946, 46.9750)}
TO_M = pyproj.Transformer.from_crs("EPSG:4326", CFG.CRS_METRIC, always_xy=True).transform


def outline(ax, geom, colour, lw, ls="-", z=6):
    b = geom.boundary
    for ln in (list(b.geoms) if isinstance(b, MultiLineString) else [b]):
        x, y = ln.xy; ax.plot(x, y, color=colour, lw=lw, ls=ls, zorder=z)


def main():
    rows = []
    union = None
    for fid, f in FRAMES.items():
        g = box(*f["bbox"])
        union = g if union is None else union.union(g)
        rows.append(dict(rectangle_id=fid, name=f["label"], zone=f["zone"],
                         xmin=f["bbox"][0], ymin=f["bbox"][1], xmax=f["bbox"][2], ymax=f["bbox"][3],
                         crs="EPSG:32636", width_km=round((f["bbox"][2] - f["bbox"][0]) / 1e3, 2),
                         height_km=round((f["bbox"][3] - f["bbox"][1]) / 1e3, 2),
                         area_km2=round(g.area / 1e6, 1)))
    T = pd.DataFrame(rows)
    ov = round(sum(box(*FRAMES[a]["bbox"]).intersection(box(*FRAMES[b]["bbox"])).area for a, b in
                   (("B1", "B2"), ("B1", "B3"), ("B2", "B3"))) / 1e6, 1)
    T.loc[len(T)] = dict(rectangle_id="UNION", name="geometric union of B1|B2|B3", zone="-",
                         xmin=union.bounds[0], ymin=union.bounds[1], xmax=union.bounds[2], ymax=union.bounds[3],
                         crs="EPSG:32636", width_km=round((union.bounds[2] - union.bounds[0]) / 1e3, 2),
                         height_km=round((union.bounds[3] - union.bounds[1]) / 1e3, 2),
                         area_km2=round(union.area / 1e6, 1))
    T.to_csv(CFG.TABLES / "p52a_processing_frames.csv", index=False)
    pd.set_option("display.width", 220); print(T.to_string(index=False))
    print(f"\npairwise overlap between the frames: {ov} km2 (counted ONCE in the union: "
          f"{T[T.rectangle_id=='UNION'].area_km2.iloc[0]} km2 vs {T[T.rectangle_id!='UNION'].area_km2.sum():.1f} summed)")

    x0, y0, x1, y1 = union.bounds
    pad = 0.04 * (x1 - x0); x0 -= pad; x1 += pad; y0 -= pad; y1 += pad
    fig, ax = plt.subplots(figsize=(17, 12))
    p = CFG.BULK_ROOT / "terrain" / "ZONE_4_DAM_TO_KHERSON_FLOODWAY" / "fabdem_evrf2019_20m.tif"
    if p.exists():
        with rasterio.open(p) as ds:
            a = ds.read(1, out_shape=(ds.height // 8, ds.width // 8)).astype("f4")
            if ds.nodata is not None:
                a[a == ds.nodata] = np.nan
            ext = (ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top)
        ls = LightSource(315, 45)
        rgb = ls.shade(np.nan_to_num(a, nan=float(np.nanmedian(a))), cmap=plt.get_cmap("Greys_r"),
                       blend_mode="soft", vert_exag=4, dx=160, dy=160)
        ax.imshow(rgb, extent=ext, zorder=1, alpha=0.75)
    try:
        outline(ax, SD.load_utm("reservoir_full_pool_prebreach"), "#4292c6", 1.2, z=4)
        ax.plot([], [], color="#4292c6", lw=1.2, label="pre-breach reservoir pool")
    except Exception:
        pass
    # MIGRATION TODO: this diagnostic overlay reads a SWOT-DNIPRO-local geojson not vendored here; resolved via
    # the sibling-repo path in the legacy shim if that repo checkout is present, else silently skipped as before.
    old = SD._SWOT_DNIPRO_SIBLING / "data/processed/domains/below_dam_floodplain_utm.geojson"
    if old.exists():
        import geopandas as gpd
        og = gpd.read_file(old).to_crs(CFG.CRS_METRIC).union_all()
        outline(ax, og, "#d73027", 1.6, z=5)
        ax.plot([], [], color="#d73027", lw=1.6, label=f"OLD p42 domain ({og.area/1e6:.0f} km²) — no longer clips anything")
    for r in CUT_RECTS:
        ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], fill=False, ec="#b2182b",
                               lw=1.3, ls=":", zorder=5))
    ax.plot([], [], color="#b2182b", lw=1.3, ls=":", label="OLD CUT_RECTS (diagnostic overlay only)")
    for fid, f in FRAMES.items():
        b = f["bbox"]
        ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec=f["colour"],
                               lw=3.0, zorder=8))
        ax.text(b[0] + 0.012 * (x1 - x0), b[3] - 0.018 * (y1 - y0), f["label"], color=f["colour"],
                fontsize=12, fontweight="bold", zorder=9,
                bbox=dict(fc="w", ec=f["colour"], lw=1.0, alpha=0.9, pad=2))
        ax.plot([], [], color=f["colour"], lw=3.0, label=f'{f["label"]}  ({box(*b).area/1e6:,.0f} km²)')
    for nm, (lo, la) in TOWNS.items():
        mx, my = TO_M(lo, la)
        inside = [k for k, f in FRAMES.items() if box(*f["bbox"]).contains(__import__("shapely").geometry.Point(mx, my))]
        ax.plot(mx, my, "o", ms=8, mfc="#ffff33", mec="k", mew=1.5, zorder=11)
        ax.text(mx, my, f"  {nm} [{'+'.join(inside) if inside else 'OUTSIDE'}]", fontsize=9.5, zorder=11,
                bbox=dict(fc="w", ec="k", lw=0.5, alpha=0.85, pad=1.2))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.grid(alpha=0.25, lw=0.5, ls=":"); ax.set_xlabel("easting, m (EPSG:32636)"); ax.set_ylabel("northing, m")
    ax.set_title("P52a — the three PROCESSING FRAMES (fixed 2026-09-21). Every cell inside a frame is classified;\n"
                 "HAND, basin polygons, water masks and the old CUT_RECTS are information, never a reason to remove a cell.",
                 fontsize=12)
    L = 20000.0; xa = x0 + 0.05 * (x1 - x0); ya = y0 + 0.05 * (y1 - y0)
    ax.add_patch(Rectangle((xa, ya), L, 0.008 * (y1 - y0), fc="k", ec="k", zorder=12))
    ax.add_patch(Rectangle((xa + L / 2, ya), L / 2, 0.008 * (y1 - y0), fc="w", ec="k", zorder=12))
    ax.text(xa + L / 2, ya + 0.014 * (y1 - y0), "20 km", ha="center", fontsize=9, zorder=12,
            bbox=dict(fc="w", ec="none", alpha=0.8, pad=1))
    ax.annotate("", xy=(x1 - 0.05 * (x1 - x0), y0 + 0.14 * (y1 - y0)), xytext=(x1 - 0.05 * (x1 - x0), y0 + 0.05 * (y1 - y0)),
                arrowprops=dict(arrowstyle="-|>", color="k", lw=1.6), zorder=12)
    ax.text(x1 - 0.05 * (x1 - x0), y0 + 0.15 * (y1 - y0), "N", ha="center", fontsize=11, fontweight="bold", zorder=12)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.94)
    fig.tight_layout()
    fig.savefig(CFG.FIG / "p52a_processing_frames.png", dpi=150)
    fig.savefig(CFG.FIG / "p52a_processing_frames.pdf")
    print("-> <case_study>/figures/p52a_processing_frames.png/.pdf; <case_study>/tables/p52a_processing_frames.csv")


if __name__ == "__main__":
    main()
