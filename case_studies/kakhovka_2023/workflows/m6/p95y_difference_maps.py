# New in floodstate-eo, 2026-10-01 (maintainer: maps of where the reconstruction and UNOSAT differ, over the satellite image of the flood).
# STATUS: ACTIVE. Diagnostic figures, nothing is fitted.
"""P95y maps -- where the p95x state mask and UNOSAT differ, drawn over Sentinel-2 true colour of the flood.

Backgrounds (own archive, Sentinel-2 L2A B04/B03/B02, fixed stretch 0-0.30 reflectance, gamma 0.9 as p97b): 8 June 2023 (T36TVS/TVT,
the scene of the flood peak; ~70 % cloud, the clouds are shown as they are) and 18 June 2023 (T36TUS/TUT/TVS/TVT/TWT, 7-14 % cloud,
twelve days after the breach). The south bank east of E 510 km has no scene on either day.
Overlays on the ground that was not water before the breach (optical pre-breach water and UNOSAT's reference water removed):
  cumulative 6-9 June  ours = WATER on any day 6-9 June; UNOSAT = the composite flood (ICEYE 7 June + Sentinel-3 6-9 June + Sentinel-2
                       8 June; product 3616)
  7 June               ours = the 7 June state (no own EO: every state is a model state); UNOSAT = ICEYE 7 June water, its analysis extent
categories            both water | ours only | UNOSAT only where ours is UNKNOWN | UNOSAT only where ours is DRY | ours UNKNOWN, UNOSAT no water
The white outline is the vegetated-wetland complex (p95x ground_class): differences inside it are about the reference semantics of the
reed marsh, differences outside it are about the new flooding of dry ground.
Zoom windows (10 km) are chosen where the cumulative disagreement on dry ground is largest (non-overlapping).
Outputs: figures/m6_v003A/p95y_difference_overview.png, p95y_difference_zooms.png; tables/p95y_difference_windows.csv
"""
from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SFX = "_connected_ceiling"
CAT = {1: ("water in both", "#00d1e0"), 2: ("water in ours only", "#1f4fff"), 3: ("UNOSAT only, ours UNKNOWN", "#ffd23f"),
       4: ("UNOSAT only, ours DRY", "#ff2d2d"), 5: ("ours UNKNOWN, UNOSAT no water", "#bdbdbd")}
STRETCH, GAMMA, WIN_KM, N_WIN = (0.0, 0.30), 0.9, 10.0, 4
ATTR = "Contains modified Copernicus Sentinel data 2023 (Sentinel-2 L2A, ESA), processed by the authors; flood layers: UNOSAT (FL20230606UKR)"


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def main():
    t0 = time.time()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    import rasterio
    from floodstate_eo import _kakhovka_legacy_config as CFG
    from floodstate_eo.io import optical_catalogue as OC
    from floodstate_eo.optical import truecolour as TC
    from matplotlib.colors import ListedColormap
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from rasterio import features
    from scipy import ndimage
    from shapely.geometry import shape
    from shapely.ops import unary_union
    TAB = ROOT / "tables"; FIG = ROOT / "figures" / "m6_v003A"
    O = _ld("p95o", HERE / "p95o_component_qa.py"); P95 = O._ld("p95_hand_daily_inundation"); T = _ld("p95t", HERE / "p95t_eo_recession.py")
    P = P95.load_p92(); man = O.load_manifest(SFX)
    M = P95.mosaic_layers(P, with_s1=False); g = M["grid"]; tr = g.transform; shp = g.shape; crs = M["G"]["crs"]; CK = P95.CELL_KM2
    W_eng, dxm, _ = O.engine_for(P95, man, SFX); M["base"] = M["base_geom"] & P95.dam_mask(M, dxm); dom = M["base"]
    OUT = CFG.BULK_ROOT / "floodplain_dyn" / "_weak_labels"
    def ras(nm):
        fc = json.loads((T.utm_dir(CFG.BULK_ROOT) / f"{nm}.geojson").read_text())["features"]
        return features.rasterize([(unary_union([shape(f_["geometry"]) for f_ in fc]), 1)], out_shape=shp, transform=tr, fill=0, dtype="uint8").astype(bool)
    def state(d):
        with rasterio.open(OUT / f"state_{d}.tif") as s:
            return s.read(1), s.read(4)
    with rasterio.open(OUT / "ground_class.tif") as s:
        gcl = s.read(1)
    uref = ras(T.REF); aoi = ras("ICEYE_20230607_AnalysisExtent_KhersonskaOblast_UKR"); ice = ras("ICEYE_20230607_WaterExtent_KhersonskaOblast_UKR")
    cum_un = ras("cumulative_0606_0609_flood"); ext_cum = (aoi | ras("ST3_20230609_ST2_20230608_AnalysisExtent_KhersonskaOblast_UKR"))
    st7, rf = state("2023-06-07"); ground = dom & ~uref & (rf != 1)
    ours = np.zeros(shp, bool); unk = np.zeros(shp, bool)
    for d in ("2023-06-06", "2023-06-07", "2023-06-08", "2023-06-09"):
        s_, _r = state(d); ours |= s_ == 1; unk |= s_ == 2
    unk &= ~ours

    def cats(ours_w, ours_u, un, sel):
        c = np.zeros(shp, "u1")
        c[sel & ours_w & un] = 1; c[sel & ours_w & ~un] = 2; c[sel & ~ours_w & ours_u & un] = 3; c[sel & ~ours_w & ~ours_u & un] = 4; c[sel & ours_u & ~un] = 5
        return c
    C_cum = cats(ours, unk, cum_un, ground & ext_cum); C_7 = cats(st7 == 1, st7 == 2, ice, ground & aoi)
    print(f"masks {round(time.time() - t0)} s", flush=True)

    # ---- true colour on the union grid: 8 June as photographed (clouds kept) and its clear mask; a late backdrop: 18 June, 25 June in the east
    S = OC.scan_safes(); grid = dict(transform=tr, ny=shp[0], nx=shp[1], crs=crs)
    rgb08, _f = TC.truecolour_mosaic(S["2023-06-08"], grid, cell=20.0, stretch=STRETCH, gamma=GAMMA, cloud_scl=(0,))
    _c, clear08 = TC.truecolour_mosaic(S["2023-06-08"], grid, cell=20.0, stretch=STRETCH, gamma=GAMMA); clear08 = clear08 > 0
    late = [z for z in S["2023-06-18"] if any(t in z.name for t in ("T36TUS", "T36TUT", "T36TVS", "T36TVT", "T36TWT"))] + [z for z in S["2023-06-25"] if "T36TWS" in z.name]
    rgbL, fillL = TC.truecolour_mosaic(late, grid, cell=20.0, stretch=STRETCH, gamma=GAMMA, cloud_scl=(0,))
    late_lab = lambda sl: "25 June" if (fillL[sl] == len(late)).mean() > 0.5 else "18 June"
    print(f"true colour {round(time.time() - t0)} s; 8 June clear share of the domain {float((clear08 & dom).sum() / dom.sum()):.2f}", flush=True)

    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.warp import reproject
    def s1_vv(cache, scene):
        zz = np.load(CFG.S1_CACHE / cache / "per_scene_water.npz", allow_pickle=True); ztr = from_origin(float(zz["x0"]), float(zz["y1"]), float(zz["cell"]), float(zz["cell"]))
        with np.load(CFG.S1_CACHE / cache / f"{scene}.npz") as b:
            vv = np.where(b["cov"] & (b["vv"] > 0), 10 * np.log10(np.maximum(b["vv"], 1e-6)), np.nan).astype("f4")
        dst = np.full(shp, np.nan, "f4")
        reproject(vv, dst, src_transform=ztr, src_crs=crs, dst_transform=tr, dst_crs=crs, resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
        return dst
    CACH = {"ZONE_4_DAM_TO_KHERSON_FLOODWAY": ("ZONE_4_FLOODWAY_june2023_s32_pre2023", "ZONE_4_FLOODWAY_june2023_s32"),
            "ZONE_2_KHERSON_DELTA": ("ZONE_2_KHERSON_DELTA_flood_june2023_pre2023", "ZONE_2_KHERSON_DELTA_flood_june2023")}
    vv_pre = np.full(shp, np.nan, "f4"); vv_post = np.full(shp, np.nan, "f4")
    for z in M["names"]:                                                 # the delta zone written last
        a_ = s1_vv(CACH[z][0], "2023-05-28_orb14_ASC"); b_ = s1_vv(CACH[z][1], "2023-06-09_orb14_ASC")
        vv_pre = np.where(np.isfinite(a_), a_, vv_pre); vv_post = np.where(np.isfinite(b_), b_, vv_post)
    sc = lambda x: np.clip((x + 25.0) / 25.0 * 255, 0, 255)
    s1rgb = np.stack([sc(vv_pre), sc(vv_post), sc(vv_post)]).astype("u1"); s1rgb[:, ~(np.isfinite(vv_pre) & np.isfinite(vv_post))] = 0
    s1vv = np.stack([sc(vv_post)] * 3).astype("u1"); s1vv[:, ~np.isfinite(vv_post)] = 0
    print(f"S1 change composite {round(time.time() - t0)} s", flush=True)
    to_img = lambda rgb, sl=(slice(None), slice(None)): np.moveaxis(rgb[:, sl[0], sl[1]], 0, -1)
    leg = [Patch(fc=c, ec="k", lw=0.3, label=n) for n, c in CAT.values()] + [Patch(fc="none", ec="white", label="vegetated-wetland complex")]
    leg_z = [Line2D([], [], color="#1f4fff", lw=1.4, label="our WATER (6-9 June) outline"), Line2D([], [], color="#ffd23f", lw=1.4, label="UNOSAT flood outline"),
             Patch(fc="#1f4fff", alpha=0.35, label="water in ours only"), Patch(fc="#ffd23f", alpha=0.45, label="UNOSAT only, ours UNKNOWN"),
             Patch(fc="#ff2d2d", alpha=0.45, label="UNOSAT only, ours DRY"), Patch(fc="#bdbdbd", alpha=0.45, label="ours UNKNOWN, UNOSAT no water"),
             Line2D([], [], color="white", lw=0.8, ls="--", label="vegetated-wetland complex")]
    def overlay(ax, rgb, C, sl, ext, title, alpha=0.55):
        ax.imshow(to_img(rgb, sl), extent=ext, interpolation="nearest")
        cc = C[sl].astype("f4"); cc[cc == 0] = np.nan
        ax.imshow(cc, cmap=ListedColormap([c for _n, c in CAT.values()]), vmin=0.5, vmax=5.5, alpha=alpha, extent=ext, interpolation="nearest")
        ax.contour((gcl[sl] == 1).astype("f4"), levels=[0.5], colors="white", linewidths=0.3, extent=ext, origin="upper")
        ax.set_title(title, fontsize=8); ax.tick_params(labelsize=6)
    def outlines(ax, rgb, C, ours_w, un, sl, ext, title):
        ax.imshow(to_img(rgb, sl), extent=ext, interpolation="nearest")
        for k, a_ in ((2, 0.35), (3, 0.45), (4, 0.45), (5, 0.45)):
            m = (C[sl] == k).astype("f4"); m[m == 0] = np.nan
            ax.imshow(m, cmap=ListedColormap([CAT[k][1]]), vmin=0.5, vmax=1.5, alpha=a_, extent=ext, interpolation="nearest")
        ax.contour(ours_w[sl].astype("f4"), levels=[0.5], colors="#1f4fff", linewidths=0.9, extent=ext, origin="upper")
        ax.contour(un[sl].astype("f4"), levels=[0.5], colors="#ffd23f", linewidths=0.9, extent=ext, origin="upper")
        ax.contour((gcl[sl] == 1).astype("f4"), levels=[0.5], colors="white", linewidths=0.5, linestyles="--", extent=ext, origin="upper")
        ax.set_title(title, fontsize=8); ax.tick_params(labelsize=6)

    # ---- overview -------------------------------------------------------------------------------------------------------------------
    rr = np.where(dom.any(1))[0]; cc_ = np.where(dom.any(0))[0]; stp = 3
    sl = (slice(rr.min(), rr.max() + 1, stp), slice(cc_.min(), cc_.max() + 1, stp))
    ext = ((tr.c + cc_.min() * tr.a) / 1e3, (tr.c + (cc_.max() + 1) * tr.a) / 1e3, (tr.f + (rr.max() + 1) * tr.e) / 1e3, (tr.f + rr.min() * tr.e) / 1e3)
    fig, axs = plt.subplots(2, 2, figsize=(22, 16), constrained_layout=True); axs = axs.ravel()
    axs[0].imshow(to_img(s1rgb, sl), extent=ext, interpolation="nearest")
    axs[0].set_title("Sentinel-1 VV, the same orbit 14 ASC: red = 28 May 2023, green / blue = 9 June ~16 UTC -> RED = became dark = new water (no clouds in radar)", fontsize=8)
    outlines(axs[1], s1rgb, np.zeros(shp, "u1"), ours, cum_un, sl, ext, "the same radar image with the outlines: ours WATER 6-9 June (blue), UNOSAT composite flood (yellow)")
    overlay(axs[2], s1rgb, C_cum, sl, ext, "cumulative 6-9 June: ours vs UNOSAT composite (ICEYE 7 June + S3 6-9 June + S2 8 June), on the radar image", alpha=0.5)
    overlay(axs[3], s1rgb, C_7, sl, ext, "7 June: ours (state, no own EO) vs ICEYE 7 June 12:18-13:01 UTC water, on the radar image", alpha=0.5)
    for ax in axs:
        ax.tick_params(labelsize=7)
    fig.legend(handles=leg, loc="lower center", ncol=6, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(f"P95y: where the reconstruction and UNOSAT differ, on ground that was not water before the breach, on Sentinel-1 radar (UTM 36N km). {ATTR}", fontsize=9)
    FIG.mkdir(parents=True, exist_ok=True); fig.savefig(FIG / "p95y_difference_overview.png", dpi=105, bbox_inches="tight"); plt.close(fig)

    # ---- zoom windows: where the 8 June photo can judge (>= 40 % clear) and the largest disagreement anywhere -------------------
    from rasterio.warp import transform as tf
    w = int(WIN_KM * 1000 / g.cell); dis = ((C_cum == 2) | (C_cum == 3) | (C_cum == 4)) & (gcl == 0)
    dens = ndimage.uniform_filter(dis.astype("f4"), size=w, mode="constant")
    taken = np.zeros(shp, bool); wins = []
    def pick(score, why):
        dd = np.where(taken, -1, score); r, c = np.unravel_index(int(np.argmax(dd)), shp)
        r0, c0 = max(r - w // 2, 0), max(c - w // 2, 0); r1, c1 = min(r0 + w, shp[0]), min(c0 + w, shp[1])
        taken[max(r0 - w // 2, 0):r1 + w // 2, max(c0 - w // 2, 0):c1 + w // 2] = True
        s2 = (slice(r0, r1), slice(c0, c1)); x0, y0 = tr.c + c0 * tr.a, tr.f + r0 * tr.e
        lon, lat = tf(crs, "EPSG:4326", [x0 + w * tr.a / 2], [y0 + w * tr.e / 2])
        row = dict(window=len(wins) + 1, chosen_for=why, centre_lon=round(lon[0], 4), centre_lat=round(lat[0], 4), x0_km=round(x0 / 1e3, 1), y0_km=round(y0 / 1e3, 1),
                   clear_0608_share=round(float(clear08[s2].mean()), 2), late_backdrop=late_lab(s2))
        for k, (nm, _c) in CAT.items():
            row[f"cumulative_{nm}_km2"] = round(float((C_cum[s2] == k).sum()) * CK, 2)
            row[f"dry_ground_{nm}_km2"] = round(float(((C_cum[s2] == k) & (gcl[s2] == 0)).sum()) * CK, 2)
        wins.append((s2, row))
    for _ in range(N_WIN):
        pick(dens, "largest disagreement on dry ground")
    TT = pd.DataFrame([r_ for _s, r_ in wins]); TT.to_csv(TAB / "p95y_difference_windows.csv", index=False); print(TT.T.to_string(), flush=True)
    fig, axs = plt.subplots(N_WIN, 3, figsize=(18, 6 * N_WIN), constrained_layout=True)
    for i, (s2, row) in enumerate(wins):
        ext = ((tr.c + s2[1].start * tr.a) / 1e3, (tr.c + s2[1].stop * tr.a) / 1e3, (tr.f + s2[0].stop * tr.e) / 1e3, (tr.f + s2[0].start * tr.e) / 1e3)
        lab = f"window {row['window']} ({row['centre_lat']:.3f} N, {row['centre_lon']:.3f} E; {row['chosen_for']})"
        axs[i, 0].imshow(to_img(s1rgb, s2), extent=ext, interpolation="nearest"); axs[i, 0].set_title(f"{lab}\nSentinel-1 orbit 14: red 28 May, green/blue 9 June (red = new water)", fontsize=8)
        axs[i, 0].tick_params(labelsize=6)
        outlines(axs[i, 1], s1rgb, C_cum, ours, cum_un, s2, ext, "cumulative 6-9 June: ours (blue line) vs UNOSAT (yellow line), disagreements filled, on the radar image")
        if row["clear_0608_share"] >= 0.6:
            outlines(axs[i, 2], rgb08, C_cum, ours, cum_un, s2, ext, f"the same on Sentinel-2 8 June ({row['clear_0608_share']:.0%} clear)")
        else:
            outlines(axs[i, 2], s1vv, C_cum, ours, cum_un, s2, ext, f"the same on Sentinel-1 VV 9 June alone (dark = water); 8 June optical only {row['clear_0608_share']:.0%} clear")
    fig.legend(handles=leg_z, loc="lower center", ncol=7, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle(f"P95y: the reconstruction vs UNOSAT where they differ most on dry ground, on Sentinel-1 radar (UTM 36N km). {ATTR}", fontsize=9)
    fig.savefig(FIG / "p95y_difference_zooms.png", dpi=100, bbox_inches="tight"); plt.close(fig)
    print("->", FIG / "p95y_difference_overview.png", FIG / "p95y_difference_zooms.png", round(time.time() - t0), "s")

if __name__ == "__main__":
    main()
