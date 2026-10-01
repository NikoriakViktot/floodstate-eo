# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Diagnostic time series from per-date observations; no model.
"""P94 -- flood dynamics, every acquisition date: S1 dark-water (p0v/p0w M3 per-scene masks, 11 dates 2023-06-01..06-30)
and S2 optical water (p54a 10 m index stacks, NDWI > 0 AND MNDWI > 0 -- the repo's watermask convention) on the B1 u B2
mosaic (one pixel once), per region: Dnipro corridor (outside p42 CUT_RECTS), p42 terrain-eligible floodplain,
Inhulets valley rectangle -- all INSIDE the S1 observable domain (union of the 11 zone-cache footprints; the
rectangular frames extend beyond the zone polygons and are not observed there); plus the ZONE_3 estuary S1 cache on its own 20 m grid (west of B2, x < 438 km) so the
liman reach is not silently missing.

Per date: valid (observed) area, total water, NEW water = water that was not water before the breach (S2: p60 pre_water_frac
>= 20 % only -- maintainer 2026-09-30, dark Sentinel-1 is not water; S1: also not where S1 was dark on 06-01/02, the sensor
cannot show new water there), and NEW water inside the COMMON S1 footprint (pixels valid on all 11 S1
dates), so dates from the partial orbit 138 (06-06, 06-18, 06-30) can be compared with the full-coverage dates.
NOT OBSERVED IS NOT DRY: a date's number is only for its valid footprint; the coverage column says how much that is.
S2 dates with < 30 % valid coverage of a region are kept in the table but flagged unreliable and not drawn.

Outputs: <case_study>/tables/p94_flood_dynamics_s1.csv, p94_flood_dynamics_s2.csv, p94_flood_dynamics_estuary_s1.csv
         <case_study>/figures/m6_v003A/flood_dynamics.png, flood_dynamics_maps_s1.png
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = CFG.BULK_ROOT / "frames10"
FIG = ROOT / "figures" / "m6_v003A"
ZONE = {"B1": "ZONE_4_FLOODWAY_june2023_s32", "B2": "ZONE_2_KHERSON_DELTA_flood_june2023"}
ESTUARY = "ZONE_3_DNIPRO_BUG_ESTUARY_flood_june2023"
B2_WEST_X = 438000.0
S2_WINDOW = ("2023-06-01", "2023-08-31")
S2_MIN_VALID = 0.30
PX = 1e-4
C_S1, C_S2 = "#2a78d6", "#eb6834"          # fixed: S1 = slot 1 blue, S2 = slot 2 orange


def load_s1(M, trM):
    W, V = {}, {}
    for f in ("B2", "B1"):
        z = np.load(CFG.S1_CACHE / ZONE[f] / "per_scene_water.npz", allow_pickle=True); shp = tuple(int(v) for v in z["shape"])
        tr = from_origin(float(z["x0"]), float(z["y1"]), float(z["cell"]), float(z["cell"]))
        un = lambda k: np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
        for k in sorted(z.files):
            if not k.startswith("2023"):
                continue
            w, v = un(k), un("valid_" + k); d = k[:10]
            for D, a in ((W, w & v), (V, v)):
                m = np.zeros((M["ny"], M["nx"]), "u1")
                reproject(a.astype("u1"), m, src_transform=tr, src_crs="EPSG:32636", dst_transform=trM,
                          dst_crs="EPSG:32636", resampling=Resampling.nearest)
                D[d] = D.get(d, np.zeros((M["ny"], M["nx"]), bool)) | m.astype(bool)
    orbit = {}
    for f in ("B1",):
        z = np.load(CFG.S1_CACHE / ZONE[f] / "per_scene_water.npz", allow_pickle=True)
        for k in z.files:
            if k.startswith("2023"):
                orbit[k[:10]] = k[11:]
    return W, V, orbit


def s2_water(fid, date):
    p = OUT / fid / "indices" / f"{date}.tif"
    if not p.exists():
        return None, None
    with rasterio.open(p) as s:
        d = list(s.descriptions); ndwi = s.read(d.index("NDWI") + 1); mndwi = s.read(d.index("MNDWI") + 1)
        nd = s.nodata
    with rasterio.open(OUT / fid / "indices" / f"{date}_valid.tif") as s:
        v = s.read(1) > 0
    v &= (ndwi != nd) & (mndwi != nd)
    return (ndwi > 0) & (mndwi > 0) & v, v


def main():
    s = importlib.util.spec_from_file_location("p92", HERE / "p92_flood_area_dam_to_liman.py")
    P = importlib.util.module_from_spec(s); s.loader.exec_module(P)
    FIG.mkdir(parents=True, exist_ok=True)
    M = P.mosaic_grid(); L = P.load_layers(M); trM = from_origin(M["x0"], M["y1"], 10.0, 10.0)
    cut = np.zeros((M["ny"], M["nx"]), bool)
    for r in P.CUT_RECTS.values():
        cut |= P.rect_mask(M, r)
    fp, _ = P.floodplain_domain(M)
    own = L["owned"]
    reg = {"DNIPRO_CORRIDOR": own & ~cut, "INHULETS_VALLEY_rect": own & P.rect_mask(M, P.CUT_RECTS["inhulets_valley"])}
    if fp is not None:
        reg["P42_FLOODPLAIN_DOMAIN"] = own & fp
    W, V, orbit = load_s1(M, trM)
    dates = sorted(W)
    pre = L["pre"] | W["2023-06-01"] | W["2023-06-02"]       # S1 new water: not optical pre-breach water, not where S1 was already dark
    pre_opt = L["pre"]                                         # S2 new water: optical pre-breach water only (maintainer 2026-09-30: dark S1 is not water)
    common = np.logical_and.reduce([V[d] for d in dates])
    obs = np.logical_or.reduce([V[d] for d in dates])          # observable domain = union of the S1 zone footprints
    reg = {k: m & obs for k, m in reg.items()}                  # every number below is inside that domain (S2 too)
    rows = []
    for d in dates:
        for nm, m in reg.items():
            val = V[d] & m
            rows.append(dict(date=d, sensor="S1", orbit=orbit.get(d, ""), region=nm, region_km2=round(float(m.sum()) * PX, 1),
                             valid_km2=round(float(val.sum()) * PX, 1), coverage=round(float(val.sum() / max(m.sum(), 1)), 3),
                             coverage_note="fraction of the S1 observable domain (union of all 11 footprints) seen on this date",
                             water_km2=round(float((W[d] & m).sum()) * PX, 1),
                             new_water_km2=round(float((W[d] & m & ~pre).sum()) * PX, 1),
                             common_footprint_km2=round(float((common & m).sum()) * PX, 1),
                             new_water_common_footprint_km2=round(float((W[d] & m & ~pre & common).sum()) * PX, 1),
                             pre_breach_water_in_footprint_km2=round(float((pre & val).sum()) * PX, 1)))
    S1 = pd.DataFrame(rows); S1.to_csv(CFG.TABLES / "p94_flood_dynamics_s1.csv", index=False)
    # ---- ZONE_3 estuary, own grid, west of B2 only ---------------------------------------------------------------------
    z = np.load(CFG.S1_CACHE / ESTUARY / "per_scene_water.npz", allow_pickle=True); shp = tuple(int(v) for v in z["shape"])
    un = lambda k: np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
    gx = float(z["x0"]) + float(z["cell"]) * (np.arange(shp[1]) + 0.5); west = (gx < B2_WEST_X)[None, :].repeat(shp[0], 0)
    ks = sorted(k for k in z.files if k.startswith("2023")); ZW, ZV = {}, {}
    for k in ks:
        w, v = un(k), un("valid_" + k); d = k[:10]
        ZW[d] = ZW.get(d, np.zeros(shp, bool)) | (w & v); ZV[d] = ZV.get(d, np.zeros(shp, bool)) | v
    zpre = ZW.get("2023-06-01", np.zeros(shp, bool)) | ZW.get("2023-06-02", np.zeros(shp, bool))
    zcom = np.logical_and.reduce([ZV[d] for d in ZV]); cell_km2 = float(z["cell"]) ** 2 * 1e-6
    west &= np.logical_or.reduce([ZV[d] for d in ZV])
    erows = [dict(date=d, sensor="S1", region="ESTUARY_ZONE3_west_of_B2", region_km2=round(float(west.sum()) * cell_km2, 1),
                  valid_km2=round(float((ZV[d] & west).sum()) * cell_km2, 1),
                  coverage=round(float((ZV[d] & west).sum() / max(west.sum(), 1)), 3),
                  water_km2=round(float((ZW[d] & west).sum()) * cell_km2, 1),
                  new_water_km2=round(float((ZW[d] & west & ~zpre).sum()) * cell_km2, 1),
                  new_water_common_footprint_km2=round(float((ZW[d] & west & ~zpre & zcom).sum()) * cell_km2, 1))
             for d in sorted(ZW)]
    E = pd.DataFrame(erows); E.to_csv(CFG.TABLES / "p94_flood_dynamics_estuary_s1.csv", index=False)
    # ---- S2 optical water per date -----------------------------------------------------------------------------------
    s2dates = sorted({p.name[:10] for f in ("B1", "B2") for p in (OUT / f / "indices").glob("2023-*.tif")
                      if "_valid" not in p.name and S2_WINDOW[0] <= p.name[:10] <= S2_WINDOW[1]})
    rows = []
    for d in s2dates:
        Wd, Vd = {}, {}
        for f in ("B1", "B2"):
            w, v = s2_water(f, d)
            Wd[f] = w if w is not None else np.zeros((M["G"][f]["ny"], M["G"][f]["nx"]), bool)
            Vd[f] = v if v is not None else np.zeros_like(Wd[f])
        w = P.place(M, Wd, False); v = P.place(M, Vd, False)
        for nm, m in reg.items():
            val = v & m; cov = float(val.sum() / max(m.sum(), 1))
            rows.append(dict(date=d, sensor="S2", region=nm, valid_km2=round(float(val.sum()) * PX, 1), coverage=round(cov, 3),
                             reliable=cov >= S2_MIN_VALID, water_km2=round(float((w & m).sum()) * PX, 1),
                             new_water_km2=round(float((w & m & ~pre_opt).sum()) * PX, 1),
                             new_water_common_s1_footprint_km2=round(float((w & m & ~pre_opt & common).sum()) * PX, 1),
                             frames=",".join(f for f in ("B1", "B2") if (OUT / f / "indices" / f"{d}.tif").exists())))
        print("S2", d, rows[-1]["coverage"], flush=True)
    S2 = pd.DataFrame(rows); S2.to_csv(CFG.TABLES / "p94_flood_dynamics_s2.csv", index=False)
    # ---- chart: new water per date, per region (one axis each; coverage in its own row) -----------------------------
    regions = [r for r in ("DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect") if r in reg] + ["ESTUARY_ZONE3_west_of_B2"]
    fig, axs = plt.subplots(2, len(regions), figsize=(4.6 * len(regions), 6.2), constrained_layout=True,
                            gridspec_kw=dict(height_ratios=[3, 1]))
    for j, r in enumerate(regions):
        a, b = axs[0, j], axs[1, j]
        s1 = (E if r.startswith("ESTUARY") else S1[S1.region == r]).copy(); s1["t"] = pd.to_datetime(s1.date)
        full = s1[s1.coverage >= 0.9]; part = s1[s1.coverage < 0.9]
        a.plot(s1.t, s1.new_water_common_footprint_km2, color=C_S1, lw=1.2, ls=":", label="S1, common footprint")
        a.plot(full.t, full.new_water_km2, color=C_S1, lw=2, marker="o", ms=5, label="S1 new water (full coverage)")
        a.plot(part.t, part.new_water_km2, color=C_S1, lw=0, marker="o", ms=6, mfc="white", label="S1, partial coverage (orbit 138)")
        b.plot(s1.t, s1.coverage, color=C_S1, lw=1.5, marker="o", ms=3)
        if not r.startswith("ESTUARY"):
            s2 = S2[(S2.region == r) & S2.reliable].copy(); s2["t"] = pd.to_datetime(s2.date)
            a.plot(s2.t, s2.new_water_km2, color=C_S2, lw=0, marker="s", ms=5, label="S2 new water (NDWI>0 & MNDWI>0, valid >= 30 %)")
            s2a = S2[S2.region == r].copy(); s2a["t"] = pd.to_datetime(s2a.date)
            b.plot(s2a.t, s2a.coverage, color=C_S2, lw=0, marker="s", ms=3)
        for i, q in full.iterrows():
            a.annotate(f"{q.new_water_km2:.0f}", (q.t, q.new_water_km2), fontsize=6.5, color="#52514e", xytext=(0, 5),
                       textcoords="offset points", ha="center")
        a.axvline(pd.Timestamp("2023-06-06"), color="#e34948", lw=0.8, ls="--"); a.text(pd.Timestamp("2023-06-06"), a.get_ylim()[1] * 0.98 if a.get_ylim()[1] > 0 else 1,
                                                                                    " breach 06-06", fontsize=6.5, color="#e34948", va="top")
        a.set_title(f"{r}  ({s1.region_km2.iloc[0]:,.0f} km²)", fontsize=9, loc="left"); a.set_ylabel("new water, km²", fontsize=8)
        b.set_ylabel("coverage", fontsize=8); b.set_ylim(0, 1.05)
        for ax in (a, b):
            ax.grid(color="#efece6", lw=0.8); ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=7)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d")); ax.set_xlim(pd.Timestamp("2023-05-30"), pd.Timestamp(S2_WINDOW[1]))
    axs[0, 0].legend(fontsize=6.5, frameon=False, loc="upper right")
    fig.suptitle("Kakhovka 2023 -- water that was NOT water before the breach, per acquisition date (observed footprint only; "
                 "not observed is not dry)", fontsize=10)
    fig.savefig(FIG / "flood_dynamics.png", dpi=120, bbox_inches="tight"); plt.close(fig)
    # ---- small-multiple S1 maps ----------------------------------------------------------------------------------------
    DS = 8; ds = lambda a: a[::DS, ::DS]
    ext = [M["x0"] / 1e3, M["x1"] / 1e3, M["y0"] / 1e3, M["y1"] / 1e3]
    cm = ListedColormap(["#ffffff", "#efece6", "#b9c7d6", C_S1])
    n = len(dates); nc = 4; nr = int(np.ceil(n / nc))
    fig, axs = plt.subplots(nr, nc, figsize=(4.2 * nc, 3.4 * nr), constrained_layout=True)
    for ax, d in zip(axs.ravel(), dates):
        st = np.zeros((M["ny"], M["nx"]), "u1"); st[V[d] & own] = 1; st[V[d] & own & pre] = 2; st[W[d] & own & ~pre] = 3
        ax.imshow(ds(st), cmap=cm, vmin=-0.5, vmax=3.5, extent=ext, interpolation="nearest"); ax.set_aspect("equal")
        r = S1[(S1.date == d) & (S1.region == "DNIPRO_CORRIDOR")].iloc[0]
        ax.set_title(f"{d} {orbit.get(d, '')}\ncorridor new water {r.new_water_km2:.0f} km² · coverage {r.coverage:.0%}", fontsize=8, loc="left")
        ax.tick_params(labelsize=6)
    for ax in axs.ravel()[n:]:
        ax.axis("off")
    fig.legend(handles=[Patch(fc=C_S1, label="new water (not water before the breach)"), Patch(fc="#b9c7d6", label="pre-breach water"),
                        Patch(fc="#efece6", label="observed, dry"), Patch(fc="#ffffff", ec="#c3c2b7", label="not observed on this date")],
               loc="lower center", ncol=4, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.savefig(FIG / "flood_dynamics_maps_s1.png", dpi=100, bbox_inches="tight"); plt.close(fig)
    pd.set_option("display.width", 250)
    print(S1[S1.region == "DNIPRO_CORRIDOR"][["date", "orbit", "coverage", "water_km2", "new_water_km2", "new_water_common_footprint_km2"]].to_string(index=False))
    print(S2[S2.region == "DNIPRO_CORRIDOR"][["date", "coverage", "reliable", "water_km2", "new_water_km2", "frames"]].to_string(index=False))
    print(E[["date", "coverage", "water_km2", "new_water_km2"]].to_string(index=False))
    print(f"-> tables/p94_*, {FIG.relative_to(ROOT)}/flood_dynamics*.png")


if __name__ == "__main__":
    main()
