# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Publication figures (main text Fig01-Fig08, supplement FigS01-FigS06).
"""P97 -- publication figures for Paper 3, 300 dpi PNG + PDF, one style (floodstate_eo.visualization.figstyle).

Main text (claims decide the figures):
  Fig01 study area (hillshade, frames, p42 floodplain, cut rectangles, SWOT nodes, gauge, dam)               [bulk]
  Fig02 evidence hierarchy / method schematic                                                                  [tables]
  Fig03 U-Net weak-label experiment: flood-state maps (U2b) + paired differences (label effect, input effects) [bulk]
  Fig04 daily terrain-reconstructed inundation with the Monte-Carlo band, S1 observations, U-Net line, gauge   [tables]
  Fig05 disagreement ontology on 2023-06-09: map A/B/C + decomposition bars                                    [bulk]
  Fig06 water surface: H(d,t) display profile + SWOT-input vs gauge at Kherson                                 [tables]
  Fig07 event-scale spatial result: peak-day depth and duration, dam -> liman                                  [bulk]
  Fig08 ICESat-2 altimetric consistency check                                                                  [tables]
  Fig09 reservoir drawdown (levels, area, volume, daily balance vs DniproHES inflow and downstream storage)     [tables]
Supplement: FigS01 training curves, FigS02 rule / closure sensitivity, FigS03 per-date S1/S2 series, FigS04 RF20 confusion
and per-class F1, FigS05 block-size sensitivity, FigS06 Inhulets profile, FigS07 hypsometry sensitivity,
FigS08 reservoir drawdown maps (model / S1 / S2 classes / day of exposure, p95h) [bulk], FigS09 the 7 S2 indices over the pool [bulk].
`--only FigNN`, `--tables-only`. Bulk figures are rendered once locally and committed.
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LightSource
from matplotlib.patches import Patch, Rectangle, FancyBboxPatch, FancyArrowPatch
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.visualization import figstyle as FS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]; M6 = ROOT / "workflows" / "m6"
T = ROOT / "tables"; PT = ROOT / "publication" / "tables"; FIG = ROOT / "publication" / "figures"; RUNS = ROOT / "runs"
BULK = CFG.BULK_ROOT
ZONES = {"ZONE_4_DAM_TO_KHERSON_FLOODWAY": "B1", "ZONE_2_KHERSON_DELTA": "B2"}
BREACH = pd.Timestamp("2023-06-06")
REG_TITLE = {"DNIPRO_CORRIDOR": "Dnipro corridor (Inhulets excluded)", "P42_FLOODPLAIN_DOMAIN": "p42 floodplain domain", "INHULETS_VALLEY_rect": "Inhulets valley (backwater)"}


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def km_ext(G):
    return [G["transform"].c / 1e3, (G["transform"].c + 20 * G["nx"]) / 1e3, (G["transform"].f - 20 * G["ny"]) / 1e3, G["transform"].f / 1e3]


def zone_mosaic(arrays: dict, fill):
    """Mosaic two 20 m zone arrays (dict zone -> (array, G)) onto their union grid; ZONE_2 owns the overlap."""
    import rasterio
    Gs = {z: g for z, (a, g) in arrays.items()}
    x0 = min(g["transform"].c for g in Gs.values()); y1 = max(g["transform"].f for g in Gs.values())
    x1 = max(g["transform"].c + 20 * g["nx"] for g in Gs.values()); y0 = min(g["transform"].f - 20 * g["ny"] for g in Gs.values())
    nx, ny = int(round((x1 - x0) / 20)), int(round((y1 - y0) / 20))
    out = np.full((ny, nx), fill, dtype=np.asarray(next(iter(arrays.values()))[0]).dtype); done = np.zeros((ny, nx), bool)
    for z in ("ZONE_2_KHERSON_DELTA", "ZONE_4_DAM_TO_KHERSON_FLOODWAY"):
        if z not in arrays:
            continue
        a, g = arrays[z]; r = int(round((y1 - g["transform"].f) / 20)); c = int(round((g["transform"].c - x0) / 20))
        sl = (slice(r, r + a.shape[0]), slice(c, c + a.shape[1])); m = ~done[sl]; out[sl][m] = a[m]; done[sl] |= True
    return out, [x0 / 1e3, x1 / 1e3, y0 / 1e3, y1 / 1e3]


def read_zone(path, band=1):
    import rasterio
    with rasterio.open(path) as s:
        a = s.read(band).astype("f4"); nd = s.nodata
        if nd is not None:
            a[a == nd] = np.nan
        G = dict(transform=s.transform, ny=s.height, nx=s.width)
    return a, G


def furniture(ax, ext, scale_km=10):
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal")
    ax.set_xlabel("easting, km (UTM 36N)", fontsize=7); ax.set_ylabel("northing, km", fontsize=7); ax.tick_params(labelsize=6)
    FS.scale_bar(ax, scale_km * 1000, units_per_m=1e-3); FS.north_arrow(ax); FS.graticule(ax, "EPSG:32636", units_per_m=1e-3)


# ---- Fig01 -----------------------------------------------------------------------------------------------------------
def fig01():
    import rasterio
    from rasterio import features
    P92 = _ld("p92", M6 / "p92_flood_area_dam_to_liman.py")
    with rasterio.open(BULK / "dem_seamless" / "dem_seamless_evrf2019_50m.tif") as s:
        dem = s.read(1).astype("f4"); dem[dem == s.nodata] = np.nan; tr = s.transform
        ext = [tr.c / 1e3, (tr.c + tr.a * s.width) / 1e3, (tr.f + tr.e * s.height) / 1e3, tr.f / 1e3]
    hs = LightSource(azdeg=315, altdeg=40).hillshade(np.nan_to_num(dem, nan=0), vert_exag=3, dx=50, dy=50)
    fig, ax = plt.subplots(figsize=(7.2, 6.4), constrained_layout=True)
    ax.imshow(hs, cmap="gray", extent=ext, vmin=0, vmax=1, alpha=0.85, interpolation="bilinear", rasterized=True)
    ax.imshow(np.ma.masked_where(~(np.nan_to_num(dem, nan=99) < 1.0), np.ones_like(dem)), cmap=ListedColormap(["#b9c7d6"]), extent=ext, alpha=0.9, interpolation="nearest", rasterized=True)
    gj = Path(CFG._SWOT_DNIPRO_SIBLING) / "data/processed/domains/below_dam_floodplain_utm.geojson"
    if gj.exists():
        g = json.loads(gj.read_text())
        for ft in g["features"]:
            geom = ft["geometry"]; polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            for poly in polys:
                xy = np.array(poly[0]) / 1e3; ax.plot(xy[:, 0], xy[:, 1], color=FS.PALETTE["terrain"], lw=0.8)
    from floodstate_eo.spatial import canonical_grid as CG
    for f, c in (("B1", "#4a3aa7"), ("B2", "#1baf7a")):
        F = CG.frame_grid(f); t = F["transform"]
        ax.add_patch(Rectangle((t.c / 1e3, (t.f - 10 * F["ny"]) / 1e3), 10 * F["nx"] / 1e3, 10 * F["ny"] / 1e3, fill=False, ec=c, lw=1.2))
        ax.text(t.c / 1e3 + 1, (t.f - 10 * F["ny"]) / 1e3 + 1.5, f"frame {f}", color=c, fontsize=8, fontweight="bold", va="bottom")
    for nm, (x0, y0, x1, y1) in P92.CUT_RECTS.items():
        ax.add_patch(Rectangle((x0 / 1e3, y0 / 1e3), (x1 - x0) / 1e3, (min(y1, 5225000) - y0) / 1e3, fill=False, ec="#e34948", lw=0.8, ls="--"))
    n = pd.read_csv(T / "p59_swot_flood_nodes.csv", usecols=["node_id", "x", "y", "river_name"]).drop_duplicates("node_id")
    main = ~n.river_name.isin(["Inhulets", "Kokan'"])
    ax.scatter(n.x[main] / 1e3, n.y[main] / 1e3, s=2, color=FS.PALETTE["terrain"], label="SWOT nodes, Dnipro"); ax.scatter(n.x[~main] / 1e3, n.y[~main] / 1e3, s=2, color=FS.PALETTE["s2"], label="SWOT nodes, tributaries / side channels")
    from pyproj import Transformer
    tfm = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True)
    kx, ky = tfm.transform(32.612026, 46.623750); dx, dy = tfm.transform(33.3667, 46.7783)
    ax.plot(kx / 1e3, ky / 1e3, "s", color=FS.PALETTE["gauge"], ms=6, label="Kherson gauge 80805"); ax.plot(dx / 1e3, dy / 1e3, "^", color="#e34948", ms=7, label="Kakhovka dam")
    ax.set_xlim(436, 540); ax.set_ylim(5133, 5215); furniture(ax, [436, 540, 5133, 5215], 20)
    ax.legend(handles=[Patch(fc="#b9c7d6", label="terrain below 1 m (water / channels)"), Patch(fc="none", ec=FS.PALETTE["terrain"], label="p42 terrain-eligible floodplain"),
                       Patch(fc="none", ec="#e34948", ls="--", label="cut rectangles (Inhulets valley, terraces)"), *ax.get_legend_handles_labels()[0]], loc="lower right", fontsize=6.5, ncol=2, bbox_to_anchor=(0.995, 0.06))
    ax.set_title("Study area: lower Dnipro from the Kakhovka dam to the Dnipro–Buh liman", fontsize=9, loc="left")
    FS.save(fig, "Fig01_study_area", FIG)


# ---- Fig02 -----------------------------------------------------------------------------------------------------------
def fig02():
    fig, ax = plt.subplots(figsize=(7.2, 4.2)); ax.axis("off")
    boxes = [(0.02, 0.62, "Observation-constrained terrain\ninundation reconstruction\nSWOT node WSE + Kherson gauge\n× seamless DEM, connectivity\n→ daily reconstructed area, depth, volume", FS.PALETTE["terrain"]),
             (0.35, 0.62, "Independent / cross-sensor checks\nS1 per date (POD / FAR / CSI)\nICESat-2 altimetric consistency\nSWOT vs gauge (Paper 1)", FS.PALETTE["s1"]),
             (0.68, 0.62, "Surface context\nRF20 classes, WorldCover,\nelevation above the surface\n→ blind spots, topographically\nunsupported S1-only detections", FS.PALETTE["rf"]),
             (0.35, 0.12, "ML under weak labels\nU-Net arms U0d → U2b, labels v002 / v003_A\n→ what EO inputs recover\n(agreement, not accuracy)", FS.PALETTE["unet"])]
    for x, y, txt, c in boxes:
        ax.add_patch(FancyBboxPatch((x, y), 0.30, 0.30, boxstyle="round,pad=0.01", fc="white", ec=c, lw=1.6, transform=ax.transAxes))
        ax.text(x + 0.15, y + 0.15, txt, ha="center", va="center", fontsize=7.2, transform=ax.transAxes)
    for (x0, y0), (x1, y1), lab in [((0.32, 0.77), (0.35, 0.77), "checked by"), ((0.65, 0.77), (0.68, 0.77), "disagreement\nexplained by"), ((0.50, 0.62), (0.50, 0.42), "labels, strata,\nblind spots inform")]:
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12, color=FS.PALETTE["ink2"], transform=ax.transAxes, lw=1.0))
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.03, lab, ha="center", va="bottom", fontsize=6, color=FS.PALETTE["ink2"], transform=ax.transAxes)
    ax.text(0.02, 0.05, "Evidence levels: independent_physical › cross_sensor › weak_label_agreement › contextual.  Areas: observed_S1 / mapped_UNet / terrain_reconstructed / literature_reported.",
            fontsize=6.5, transform=ax.transAxes, color=FS.PALETTE["ink2"])
    FS.save(fig, "Fig02_evidence_hierarchy", FIG)


# ---- Fig03 -----------------------------------------------------------------------------------------------------------
def fig03():
    P91 = _ld("p91", M6 / "p91_m6_maps_v003A.py")
    fig = plt.figure(figsize=(7.2, 8.0)); gs = fig.add_gridspec(2, 2, height_ratios=[1.35, 1], hspace=0.32, wspace=0.18, bottom=0.08)
    cm = ListedColormap([c for _, c in FS.STATE_COLOURS.values()])
    for j, fid in enumerate(("B1", "B2")):
        ax = fig.add_subplot(gs[0, j]); L = P91.load(fid); sc, thr = P91.score(fid, "U2b_B1B2_v003A"); pred = sc >= thr
        st = np.zeros(sc.shape, "u1"); st[L["has"]] = 1; st[L["has"] & (L["ont"] == 2)] = 2; st[pred & L["has"]] = 5; st[pred & (L["ont"] == 1)] = 4; st[pred & (L["ont"] == 2)] = 3
        ax.imshow(st, cmap=cm, vmin=-0.5, vmax=5.5, extent=L["ext"], interpolation="nearest", rasterized=True); P91.test_outline(ax, L["role"], L["ext"])
        furniture(ax, L["ext"], 10); FS.panel_label(ax, "ab"[j]); ax.set_title(f"frame {fid}: U2b (v003_A), score ≥ {thr:.2f}", fontsize=8, loc="left")
    ax = fig.add_subplot(gs[1, :])
    pb = pd.read_csv(PT / "T06.csv"); pb7 = pd.read_csv(PT / "T07b.csv")
    rows = []
    for comp, lab, ep, name in [("U2 - U0d", "v002", "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2", "U0d→U2 (+HAND): unlabelled-cropland burden, km²"),
                                ("U2 - U0d", "v002", "B_recall_flooded_open_low_veg", "U0d→U2 (+HAND): recall on flooded open low vegetation"),
                                ("U1 - U0d", "v002", "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2", "U0d→U1 (+RF20 context): unlabelled-cropland burden, km²")]:
        r = pb[(pb.comparison == comp) & (pb.labels == lab) & (pb.endpoint == ep)]
        if len(r):
            rows.append((name, float(r["median"].iloc[0]), float(r.ci_lo.iloc[0]), float(r.ci_hi.iloc[0]), FS.PALETTE["unet"]))
    for A, B, ep, name in [("U2_B1B2_v1", "U2_B1B2_v003A", "R_pred_on_reference_water_km2", "label effect v002→v003_A (U2): flood on reference water, km²"),
                           ("U2_B1B2_v1", "U2_B1B2_v003A", "E_recall_event_flood", "label effect v002→v003_A (U2): EVENT_FLOOD recall"),
                           ("U2_B1B2_v003A", "U2b_B1B2_v003A", "R_pred_on_reference_water_km2", "U2→U2b (+W_pre, diagnostic): flood on reference water, km²"),
                           ("U2_B1B2_v003A", "U2b_B1B2_v003A", "E_recall_event_flood", "U2→U2b (+W_pre, diagnostic): EVENT_FLOOD recall")]:
        r = pb7[(pb7.A == A) & (pb7.B == B) & (pb7.endpoint == ep)]
        if len(r):
            rows.append((name, float(r["median"].iloc[0]), float(r.lo.iloc[0]), float(r.hi.iloc[0]), FS.PALETTE["muted"] if "diagnostic" in name else FS.PALETTE["unet"]))
    labels = [r[0] for r in rows]; y = np.arange(len(rows))[::-1]
    for (name, m, lo, hi, c), yy in zip(rows, y):
        ax.hlines(yy, lo, hi, color=c, lw=1.6); ax.plot(m, yy, "o", color=c, ms=5)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=6.5); ax.axvline(0, color=FS.PALETTE["ink2"], lw=0.8, ls=":"); ax.grid(axis="x", color=FS.PALETTE["grid"])
    ax.set_xlabel("paired difference on identical spatial blocks (median, 95 % interval); km² or recall", fontsize=7); FS.panel_label(ax, "c")
    ax.set_title("Paired arm comparisons on the frozen TEST blocks (agreement with weak labels; grey = not independent, W_pre is a label ingredient)", fontsize=7.5, loc="left")
    fig.legend(handles=[Patch(fc=c, ec="#c3c2b7", label=n) for n, c in FS.STATE_COLOURS.values()] + [Patch(fc="none", ec="#0b0b0b", ls="--", label="TEST blocks")],
               loc="lower center", bbox_to_anchor=(0.5, -0.01), ncol=4, fontsize=6.2, frameon=False)
    FS.save(fig, "Fig03_unet_experiment", FIG)


# ---- Fig04 -----------------------------------------------------------------------------------------------------------
def fig04():
    """Daily reconstructed series, dam -> liman: total water-surface area with the PRIMARY spatial-MC band and the emulator
    sensitivity envelope as candles, daily change of the newly inundated area as bars, S1, U-Net, gauge."""
    d = pd.read_csv(T / "p95_daily_area_pooled_connected_ceiling.csv"); d["t"] = pd.to_datetime(d.date)
    t12 = pd.read_csv(PT / "T12.csv") if (PT / "T12.csv").exists() else None
    g = pd.read_csv(T / "p95g_mc_daily.csv") if (T / "p95g_mc_daily.csv").exists() else None
    s1 = pd.read_csv(T / "p94_flood_dynamics_s1.csv"); s1["t"] = pd.to_datetime(s1.date)
    p92 = pd.read_csv(T / "p92_flood_area_dam_to_liman.csv"); u2b = p92[p92.run == "U2b_B1B2_v003A"].set_index("region").predicted_flood_km2
    regs = ["DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect"]
    fig, axs = plt.subplots(3, 3, figsize=(7.4, 7.6), gridspec_kw=dict(height_ratios=[3, 1.4, 1.0]), sharex="col", constrained_layout=True)
    for j, r in enumerate(regs):
        a, b, c = axs[0, j], axs[1, j], axs[2, j]; s = d[d.region == r].sort_values("t")
        if g is not None:
            gg = g[g.region == r].copy(); gg["t"] = pd.to_datetime(gg.date); gg = gg.sort_values("t")
            for _, q in gg.iterrows():                                              # candles: p05-p95 whisker, p25-p75 body, p50 tick
                a.plot([q.t, q.t], [q.W_total_km2_p05, q.W_total_km2_p95], color=FS.PALETTE["terrain"], lw=0.7, alpha=0.8)
                a.add_patch(Rectangle((q.t - pd.Timedelta(hours=9), q.W_total_km2_p25), pd.Timedelta(hours=18), q.W_total_km2_p75 - q.W_total_km2_p25, fc="#b9d1ee", ec=FS.PALETTE["terrain"], lw=0.5))
                a.plot([q.t - pd.Timedelta(hours=9), q.t + pd.Timedelta(hours=9)], [q.W_total_km2_p50] * 2, color=FS.PALETTE["terrain"], lw=1.0)
        if t12 is not None and "W_total_p05_km2" in t12.columns:
            tt = t12[t12.region == r].dropna(subset=["W_total_p05_km2"]).copy(); tt["t"] = pd.to_datetime(tt.date); tt = tt.sort_values("t")
            a.fill_between(tt.t, tt.W_total_p05_km2, tt.W_total_p95_km2, color=FS.PALETTE["terrain"], alpha=0.28, lw=0, label="PRIMARY: spatial Monte-Carlo p05–p95 (40 draws)", zorder=3)
        a.plot(s.t, s.potential_km2, color=FS.PALETTE["ink"], lw=1.6, label="reconstructed total water-surface area, central run")
        pun = T / "p95_daily_area_pooled_connected_ceiling_dem_uncorrected.csv"
        if pun.exists():
            un = pd.read_csv(pun); un = un[un.region == r]; a.plot(pd.to_datetime(un.date), un.potential_km2, color=FS.PALETTE["s2"], lw=1, ls="-", label="total, DEM as delivered")
        o = s1[s1.region == r]; full, part = o[o.coverage >= 0.9], o[o.coverage < 0.9]
        a.plot(full.t, full.water_km2, "D", color=FS.PALETTE["s1"], ms=4.5, label="S1 total dark water"); a.plot(part.t, part.water_km2, "D", color=FS.PALETTE["s1"], ms=4.5, mfc="white", label="S1, partial coverage")
        a.set_title(REG_TITLE[r], fontsize=7.5, loc="left"); a.set_ylabel("reconstructed total water-surface area, km²", fontsize=6.5); FS.panel_label(a, "abc"[j], x=0.02, y=0.98)
        # daily change of NEW inundation as bars (+ filling, - draining)
        inc = s.new_km2.diff().fillna(0)
        b.bar(s.t, inc, width=0.8, color=np.where(inc >= 0, FS.PALETTE["terrain"], FS.PALETTE["s1"]), lw=0)
        b.plot(s.t, s.new_km2, color=FS.PALETTE["ink"], lw=1.0, label="reconstructed newly inundated area"); b.axhline(0, color=FS.PALETTE["ink2"], lw=0.5)
        if r in u2b.index:
            b.axhline(u2b[r], color=FS.PALETTE["unet"], lw=1, ls=":", label="U-Net U2b persistent event flood")
        b.set_ylabel("newly inundated area, km²\n(bars: daily change)", fontsize=6.5); FS.panel_label(b, "def"[j], x=0.02, y=0.98)
        c.plot(s.t, s.kherson_gauge_m, color=FS.PALETTE["gauge"], lw=1.3); c.set_ylabel("Kherson\nstage, m", fontsize=6.5)
        for ax in (a, b, c):
            FS.date_axis(ax, BREACH, every_days=7); ax.tick_params(labelsize=6); ax.set_xlim(pd.Timestamp("2023-05-31"), pd.Timestamp("2023-07-05"))
        a.set_ylim(0, None)
    h, l = axs[0, 0].get_legend_handles_labels(); h2, l2 = axs[1, 0].get_legend_handles_labels()
    fig.legend(h + [Patch(fc="#b9d1ee", ec=FS.PALETTE["terrain"], label="emulator sensitivity envelope")] + h2, l + ["SENSITIVITY: 100 000-draw emulator per day (p05–p95 whisker, p25–p75 body, median)"] + l2,
               loc="lower center", ncol=3, fontsize=5.8, frameon=False, bbox_to_anchor=(0.5, -0.09))
    FS.save(fig, "Fig04_daily_inundation", FIG)


# ---- Fig05 -----------------------------------------------------------------------------------------------------------
def fig05():
    arrs = {}
    for z in ZONES:
        a, G = read_zone(BULK / "floodplain_dyn" / "_icesat_check" / f"{z}_cat0609.tif"); arrs[z] = (np.nan_to_num(a, nan=0).astype("u1"), G)
    cat, ext = zone_mosaic(arrs, np.uint8(0))
    # categories: 1 neither, 2 S1-only <2 m, 3 both, 4 terrain-only, 5 S1-only >=2 m
    cm = ListedColormap(["#ffffff", "#efece6", "#f2b57a", FS.AGREEMENT_COLOURS["A"][1], FS.AGREEMENT_COLOURS["B"][1], FS.AGREEMENT_COLOURS["C"][1]])
    fig = plt.figure(figsize=(7.2, 6.6)); gs = fig.add_gridspec(2, 2, height_ratios=[1.4, 1], hspace=0.3, wspace=0.25)
    ax = fig.add_subplot(gs[0, :]); ax.imshow(cat[::2, ::2], cmap=cm, vmin=-0.5, vmax=5.5, extent=ext, interpolation="nearest", rasterized=True)
    furniture(ax, [ext[0], min(ext[1], 540), 5136, ext[3]], 10); FS.panel_label(ax, "a")
    ax.set_title("2023-06-09: terrain reconstruction (connected ceiling) vs Sentinel-1 new dark water, on the S1 footprint", fontsize=8, loc="left")
    ax.legend(handles=[Patch(fc=FS.AGREEMENT_COLOURS["A"][1], label="A  both"), Patch(fc=FS.AGREEMENT_COLOURS["B"][1], label="B  terrain only"),
                       Patch(fc="#f2b57a", label="C  S1 only, ground < 2 m above the surface"), Patch(fc=FS.AGREEMENT_COLOURS["C"][1], label="C  S1 only, ground ≥ 2 m above"), Patch(fc="#efece6", label="neither")],
              loc="upper left", fontsize=6.2, ncol=1, bbox_to_anchor=(0.0, 1.0))
    S = pd.read_csv(PT / "T14.csv"); s9 = S[S.date == "2023-06-09"].groupby("category").sum(numeric_only=True)
    b1 = fig.add_subplot(gs[1, 0]); comp = ["km2_wc_trees", "km2_wc_wetland", "km2_wc_built", "km2_wc_cropland", "km2_wc_grass", "km2_wc_bare"]
    vals = [float(s9.loc["B", c]) for c in comp]; other = float(s9.loc["B", "km2"]) - sum(vals)
    b1.barh(["trees", "wetland", "built-up", "cropland", "grass", "bare", "other"], vals + [other], color=FS.AGREEMENT_COLOURS["B"][1]); b1.invert_yaxis()
    b1.set_xlabel("km²", fontsize=7); b1.set_title(f"B terrain-only ({float(s9.loc['B', 'km2']):.0f} km²) by WorldCover class", fontsize=7.5, loc="left"); FS.panel_label(b1, "b"); b1.tick_params(labelsize=6.5)
    b2 = fig.add_subplot(gs[1, 1]); bins = ["km2_ground_below_surface", "km2_ground_0_2m_above", "km2_ground_2_5m_above", "km2_ground_ge5m_above"]
    v2 = [float(s9.loc["C", c]) for c in bins]; nw = float(s9.loc["C", "km2_normally_wet"])
    b2.barh(["below the surface", "0–2 m above", "2–5 m above", "≥ 5 m above"], v2, color=FS.AGREEMENT_COLOURS["C"][1]); b2.invert_yaxis()
    b2.set_xlabel("km²", fontsize=7); b2.set_title(f"C S1-only ({float(s9.loc['C', 'km2']):.0f} km²) by ground elevation vs surface\n({nw:.0f} km² normally wet; ≥ 5 m = topographically unsupported S1-only, ICESat-2 Fig08)", fontsize=7, loc="left"); FS.panel_label(b2, "c"); b2.tick_params(labelsize=6.5)
    FS.save(fig, "Fig05_disagreement_ontology", FIG)


# ---- Fig06 -----------------------------------------------------------------------------------------------------------
def fig06():
    import matplotlib.dates as mdates
    H = pd.read_csv(T / "p95_wse_profile_display.csv", index_col=0, parse_dates=True); H.columns = H.columns.astype(int)
    Hm = H.loc[:, (H.columns >= 0) & (H.columns <= 80)]
    fig = plt.figure(figsize=(7.2, 5.2)); gs = fig.add_gridspec(2, 2, width_ratios=[1.6, 1], hspace=0.35, wspace=0.3)
    ax = fig.add_subplot(gs[0, :]); im = ax.imshow(Hm.values, aspect="auto", cmap=FS.SEQ_SCORE, interpolation="nearest",
                                                    extent=[Hm.columns.min(), Hm.columns.max() + 1, mdates.date2num(Hm.index[-1]), mdates.date2num(Hm.index[0])], rasterized=True)
    ax.yaxis_date(); ax.yaxis.set_major_formatter(mdates.DateFormatter("%d %b")); ax.set_xlabel("straight-line distance from the dam, km", fontsize=7); ax.tick_params(labelsize=6.5)
    ax.axhline(mdates.date2num(BREACH), color="#e34948", lw=0.8, ls="--")
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.01); cb.set_label("water surface, m", fontsize=6.5); cb.ax.tick_params(labelsize=6)
    ax.set_title("Observed SWOT node medians per 1 km of distance from the dam (main stem, gauge-anchored EGG2015-referenced heights; white = no observation)", fontsize=7, loc="left"); FS.panel_label(ax, "a", x=0.01, y=0.97)
    d = pd.read_csv(PT / "T17b.csv", parse_dates=["date"])
    a2 = fig.add_subplot(gs[1, 0]); a2.plot(d.date, d.H_gauge_evrf, color=FS.PALETTE["gauge"], lw=1.5, label="Kherson gauge (daily, EVRF2019)")
    a2.plot(d.date, d.swot_p50, "o", color=FS.PALETTE["terrain"], ms=3.5, label="SWOT nodes ≤ 3 km, daily median (re-anchored)"); FS.date_axis(a2, BREACH, every_days=7)
    a2.set_ylabel("m", fontsize=7); a2.legend(fontsize=6); a2.tick_params(labelsize=6.5); FS.panel_label(a2, "b")
    a3 = fig.add_subplot(gs[1, 1]); r = d.gauge_minus_swot.dropna()
    a3.hist(r, bins=15, color=FS.PALETTE["terrain"], alpha=0.8); a3.axvline(0, color=FS.PALETTE["ink2"], lw=0.8, ls=":")
    a3.set_xlabel("gauge − SWOT, m", fontsize=7); a3.set_ylabel("days", fontsize=7); a3.tick_params(labelsize=6.5); FS.panel_label(a3, "c")
    a3.text(0.98, 0.95, f"n = {len(r)} days\nmedian {r.median():+.2f} m\nNMAD {FS.nmad(r):.2f} m", ha="right", va="top", fontsize=6.5, transform=a3.transAxes)
    FS.save(fig, "Fig06_water_surface", FIG)


# ---- Fig07 -----------------------------------------------------------------------------------------------------------
def fig07():
    dep, dur = {}, {}
    for z in ZONES:
        a, G = read_zone(BULK / "floodplain_dyn" / f"{z}_connected_ceiling" / "depth_2023-06-08_m.tif"); dep[z] = (a, G)
        b, G2 = read_zone(BULK / "floodplain_dyn" / f"{z}_connected_ceiling" / "duration_days.tif"); dur[z] = (b, G2)
    D, ext = zone_mosaic(dep, np.float32(np.nan)); U, _ = zone_mosaic(dur, np.float32(0))
    fig, axs = plt.subplots(2, 1, figsize=(7.2, 8.0), constrained_layout=True)
    a = axs[0]; im = a.imshow(D[::2, ::2], cmap=FS.SEQ_DEPTH, vmin=0, vmax=6, extent=ext, interpolation="nearest", rasterized=True)
    furniture(a, [ext[0], min(ext[1], 540), 5136, ext[3]], 10); fig.colorbar(im, ax=a, shrink=0.6, pad=0.01).set_label("depth of new inundation, m (2023-06-08)", fontsize=6.5); FS.panel_label(a, "a")
    a.set_title("Terrain-reconstructed new inundation on 2023-06-08 (no satellite scene): depth above ground", fontsize=8, loc="left")
    b = axs[1]; im2 = b.imshow(np.ma.masked_where(U[::2, ::2] == 0, U[::2, ::2]), cmap=FS.SEQ_DAYS, vmin=1, vmax=20, extent=ext, interpolation="nearest", rasterized=True)
    furniture(b, [ext[0], min(ext[1], 540), 5136, ext[3]], 10); fig.colorbar(im2, ax=b, shrink=0.6, pad=0.01).set_label("days with new inundation (26 May – 10 Jul)", fontsize=6.5); FS.panel_label(b, "b")
    b.set_title("Duration of terrain-reconstructed new inundation", fontsize=8, loc="left")
    FS.save(fig, "Fig07_event_scale_reconstruction", FIG)


# ---- Fig08 -----------------------------------------------------------------------------------------------------------
def fig08():
    D = pd.read_csv(PT / "T15.csv"); D = D[~D.category.str.contains("box=")]
    order = ["observed_neither", "both", "terrain_only", "S1_only_ground_lt2m_above", "S1_only_ground_ge2m_above"]
    lab = {"observed_neither": "neither", "both": "A both", "terrain_only": "B terrain only", "S1_only_ground_lt2m_above": "C S1 only, < 2 m", "S1_only_ground_ge2m_above": "C S1 only, ≥ 2 m"}
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True)
    for j, zone in enumerate(sorted(D.zone.unique())):
        g = D[D.zone == zone].set_index("category").reindex(order); y = np.arange(len(order))[::-1]
        ax = axs[j]; ax.hlines(y, g.res_p10, g.res_p90, color=FS.PALETTE["terrain"], lw=1.6); ax.plot(g.res_median, y, "o", color=FS.PALETTE["terrain"], ms=5)
        for yy, (k, r) in zip(y, g.iterrows()):
            ax.text(2.1, yy, f"ground − surface {r.ice_minus_wse_median:+.1f} m\n{100 * r.share_ice_below_wse:.0f} % below; n = {int(r.N)}", fontsize=5.4, va="center", color=FS.PALETTE["ink2"])
        ax.set_yticks(y); ax.set_yticklabels([lab[k] for k in order], fontsize=6.5); ax.axvline(0, color=FS.PALETTE["ink2"], lw=0.8, ls=":"); ax.set_xlim(-1.7, 5.0)
        ax.set_xlabel("seamless DEM − ICESat-2 ground, m (median, p10–p90)", fontsize=6.5); ax.set_title(zone.replace("_", " ").title(), fontsize=7.5, loc="left"); FS.panel_label(ax, "ab"[j]); ax.tick_params(labelsize=6)
    fig.suptitle("ICESat-2 altimetric consistency check on the 2023-06-09 agreement categories (night ATL08 ground segments)", fontsize=8)
    FS.save(fig, "Fig08_icesat2_consistency", FIG)


# ---- Fig09 -----------------------------------------------------------------------------------------------------------
def fig09():
    R = pd.read_csv(T / "p95f_reservoir_daily.csv"); R["t"] = pd.to_datetime(R.date); H = pd.read_csv(T / "p95f_hypsometry_dem.csv")
    lv = pd.read_csv(Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p61_pool_levels_2023.csv", parse_dates=["date"])
    lv = lv[(lv.date >= "2023-05-26") & (lv.date <= "2023-07-10")]
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 6.2), constrained_layout=True)
    a = axs[0, 0]
    for src, c, mk, lab in [("SWOT_OUTLET", FS.PALETTE["terrain"], "o", "SWOT outlet (0 km)"), ("NIKOPOL_UHE", FS.PALETTE["s2"], "s", "Nikopol post (160 km, press)"),
                            ("ROZUMIVKA_GAUGE", FS.PALETTE["rf"], "^", "Rozumivka gauge (248 km)"), ("ICESAT2_ATL13", FS.PALETTE["unet"], "x", "ICESat-2 passes"), ("GREALM_S6A", FS.PALETTE["muted"], "d", "G-REALM (111 km)")]:
        q = lv[lv.source == src]; a.plot(q.date, q.H_evrf2019, mk, color=c, ms=4, label=lab, lw=0)
    a.plot(R.t, R.kherson_stage_m, color=FS.PALETTE["gauge"], lw=1.3, label="Kherson stage (downstream)"); FS.date_axis(a, BREACH, every_days=7)
    a.set_ylabel("water level, m (gauge-anchored EGG2015 / EVRF2019)", fontsize=6.5); a.legend(fontsize=5.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.13), frameon=False, handletextpad=0.4, columnspacing=1.0); a.tick_params(labelsize=6); FS.panel_label(a, "a")
    b = axs[0, 1]; ok = R.V_pool_km3.notna()
    b.plot(R.t[ok], R.V_pool_km3[ok], "o-", color=FS.PALETTE["terrain"], ms=3, lw=1.5, label="pool volume under the sloped surface (DEM, km³)")
    b2 = b.twinx(); b2.plot(R.t[ok], R.A_pool_km2[ok], "s--", color=FS.PALETTE["rf"], ms=3, lw=1, label="pool water area (DEM, km²)"); b2.set_ylabel("area, km²", fontsize=6.5); b2.tick_params(labelsize=6)
    ya = pd.read_csv(Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p61_yi2025_reservoir_area.csv")
    b2.plot(pd.Timestamp("2023-06-06") + pd.to_timedelta(ya.day_after_breach, unit="D"), ya.area_km2_S1, "v", color=FS.PALETTE["s1"], ms=5, label="S1 water area (Yi 2025, VERIFY)")
    b.set_ylabel("volume, km³", fontsize=6.5); FS.date_axis(b, BREACH, every_days=7); b.tick_params(labelsize=6); h1, l1 = b.get_legend_handles_labels(); h2, l2 = b2.get_legend_handles_labels(); b.legend(h1 + h2, l1 + l2, fontsize=5.5); FS.panel_label(b, "b")
    b.set_xlim(pd.Timestamp("2023-05-31"), pd.Timestamp("2023-06-15"))
    c = axs[1, 0]; dd = R[ok & (R.t >= "2023-06-05")]
    c.bar(dd.t, -dd.dV_pool_hm3 / 1000, width=0.8, color=FS.PALETTE["terrain"], label="released from the pool (−dV/dt)")
    c.plot(dd.t, dd.Q_in_hm3_day / 1000, "s-", color=FS.PALETTE["rf"], ms=3, lw=1, label="DniproHES inflow")
    c.plot(R.t, R.downstream_new_volume_hm3 / 1000, "o-", color=FS.PALETTE["s1"], ms=3, lw=1.2, label="new water stored downstream\n(corridor + Inhulets)")
    c.set_ylabel("km³ per day (bars, inflow) / km³ stored (line)", fontsize=6.5); FS.date_axis(c, BREACH, every_days=7); c.legend(fontsize=5.5, loc="upper right"); c.tick_params(labelsize=6); FS.panel_label(c, "c"); c.set_xlim(pd.Timestamp("2023-06-03"), pd.Timestamp("2023-06-24"))
    dax = axs[1, 1]; dax.plot(H.level_evrf2019_m, H.V_dem_km3, color=FS.PALETTE["terrain"], lw=1.6, label="seamless DEM, level surface"); dax.plot(H.level_evrf2019_m, H.V_table19_km3, color=FS.PALETTE["gauge"], lw=1.2, ls="--", label="design Table 19 (BS-77 + 0.185 m)")
    dax.set_xlabel("pool level, m", fontsize=6.5); dax.set_ylabel("volume, km³", fontsize=6.5); dax.legend(fontsize=5.5); dax.tick_params(labelsize=6); dax.grid(color=FS.PALETTE["grid"]); FS.panel_label(dax, "d")
    fig.suptitle("Reservoir drawdown and the downstream flood: levels, pool area/volume, daily balance and the hypsometry used", fontsize=8)
    FS.save(fig, "Fig09_reservoir_balance", FIG)


# ---- Supplement ------------------------------------------------------------------------------------------------------
def figS01():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.8), constrained_layout=True)
    for run, c in [("U2_B1B2_v1", FS.PALETTE["s1"]), ("U0d_B1B2_v003A", FS.PALETTE["rf"]), ("U2_B1B2_v003A", FS.PALETTE["terrain"]), ("U2b_B1B2_v003A", FS.PALETTE["unet"])]:
        p = RUNS / run / "training_history.csv"
        if p.exists():
            h = pd.read_csv(p); a1.plot(h.epoch, h.train_loss, color=c, lw=1.5, label=run); a2.plot(h.epoch, h.val_patch_F1_at_0p5, color=c, lw=1.5, label=run)
    a1.set_title("train loss (masked BCE + Dice)", fontsize=7.5, loc="left"); a2.set_title("validation patch F1 @ 0.5 (weak labels)", fontsize=7.5, loc="left")
    for ax in (a1, a2):
        ax.set_xlabel("epoch", fontsize=7); ax.grid(color=FS.PALETTE["grid"]); ax.tick_params(labelsize=6.5)
    a1.legend(fontsize=6); FS.save(fig, "FigS01_training_curves", FIG)


def figS02():
    fig, ax = plt.subplots(figsize=(7.2, 3.2), constrained_layout=True)
    for sfx, lab, c, ls in [("_connected_ceiling", "connected ceiling, DEM class-bias corrected (primary)", FS.PALETTE["terrain"], "-"), ("", "p42 HAND rule", FS.PALETTE["terrain"], "--"), ("_ceiling_only", "ceiling only", FS.PALETTE["terrain"], ":"),
                            ("_connected_ceiling_dem_uncorrected", "connected ceiling, DEM as delivered (reed beds count as new)", FS.PALETTE["s2"], "-"),
                            ("_connected_ceiling_closure_p59_m050", "superseded closure (+0.5 m margin)", FS.PALETTE["muted"], "-")]:
        p = T / f"p95_daily_area_pooled{sfx}.csv"
        if p.exists():
            d = pd.read_csv(p); d = d[d.region == "DNIPRO_CORRIDOR"]; ax.plot(pd.to_datetime(d.date), d.new_km2, color=c, ls=ls, lw=1.6, label=lab)
    FS.date_axis(ax, BREACH, every_days=7); ax.set_ylabel("new inundation, km² (Dnipro corridor)", fontsize=7); ax.legend(fontsize=6.5); ax.tick_params(labelsize=6.5)
    ax.set_xlim(pd.Timestamp("2023-05-31"), pd.Timestamp("2023-07-05")); FS.save(fig, "FigS02_rule_closure_sensitivity", FIG)


def figS03():
    s = pd.read_csv(PT / "T19.csv"); s["t"] = pd.to_datetime(s.date)
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.8), constrained_layout=True)
    for j, r in enumerate(["DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect"]):
        ax = axs[j]; a = s[(s.region == r) & (s.sensor == "S1")]; b = s[(s.region == r) & (s.sensor == "S2")]
        ax.plot(a.t, a.new_water_km2, "o-", color=FS.PALETTE["s1"], ms=3.5, lw=1, label="S1 new dark water"); ax.plot(b.t, b.new_water_km2, "s", color=FS.PALETTE["s2"], ms=3.5, label="S2 (NDWI>0 & MNDWI>0)")
        FS.date_axis(ax, BREACH, every_days=14); ax.set_title(REG_TITLE[r], fontsize=7, loc="left"); ax.tick_params(labelsize=6); FS.panel_label(ax, "abc"[j])
    axs[0].set_ylabel("km²", fontsize=7); axs[0].legend(fontsize=6); FS.save(fig, "FigS03_per_date_series", FIG)


def figS04():
    cm = pd.read_csv(PT / "T10.csv", index_col=0); m = pd.read_csv(PT / "T09.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.2), constrained_layout=True, gridspec_kw=dict(width_ratios=[1.1, 1]))
    C = cm.values.astype(float); Cn = C / C.sum(1, keepdims=True)
    im = a.imshow(Cn, cmap=FS.SEQ_SCORE, vmin=0, vmax=1); a.set_xticks(range(len(cm.columns))); a.set_xticklabels(cm.columns, rotation=60, ha="right", fontsize=5.5); a.set_yticks(range(len(cm.index))); a.set_yticklabels(cm.index, fontsize=5.5)
    for i in range(C.shape[0]):
        for j in range(C.shape[1]):
            a.text(j, i, f"{Cn[i, j]:.2f}", ha="center", va="center", fontsize=5, color="white" if Cn[i, j] > 0.5 else FS.PALETTE["ink"])
    a.set_xlabel("predicted (RF20)", fontsize=7); a.set_ylabel("reference (WorldCover 2021)", fontsize=7); a.set_title("row-normalised confusion, spatial-block CV", fontsize=7.5, loc="left"); FS.panel_label(a, "a", x=-0.35)
    mm = m[m.cls != "MACRO_MEAN"]; ev = list(mm.evaluation.unique()); w = 0.8 / len(ev); cls = list(mm[mm.evaluation == ev[0]].cls)
    for k, e in enumerate(ev):
        g = mm[mm.evaluation == e].set_index("cls").reindex(cls); b.bar(np.arange(len(cls)) + k * w, g.F1, w, label=e, color=[FS.PALETTE["rf"], FS.PALETTE["terrain"], FS.PALETTE["s2"]][k % 3])
    b.set_xticks(np.arange(len(cls)) + 0.4 - w / 2); b.set_xticklabels(cls, rotation=60, ha="right", fontsize=5.5); b.set_ylabel("F1 vs WorldCover", fontsize=7); b.legend(fontsize=5.5); b.tick_params(labelsize=6); FS.panel_label(b, "b", x=-0.2)
    FS.save(fig, "FigS04_rf20_agreement", FIG)


def figS05():
    d = pd.read_csv(PT / "T20.csv"); d = d[d.status.str.contains("trained")]
    if len(d) == 0:
        return
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.6), constrained_layout=True)
    for ax, k, lab in zip(axs, ["G_F1", "A_FP_area_dry_cropland_km2", "B_recall_flooded_open_low_veg"], ["global F1 (weak labels)", "dry-cropland FP, km²", "recall, flooded open low veg."]):
        ax.errorbar(d.block_km, d[k], yerr=[d[k] - d[f"{k}_lo"], d[f"{k}_hi"] - d[k]], fmt="o", color=FS.PALETTE["unet"], capsize=3); ax.set_xlabel("block size, km", fontsize=7); ax.set_title(lab, fontsize=7.5, loc="left"); ax.tick_params(labelsize=6.5)
    fig.suptitle("Block-size sensitivity (U2, v003_A): each split has its own TEST geography; values and intervals only", fontsize=7.5); FS.save(fig, "FigS05_block_sensitivity", FIG)


def figS06():
    p = pd.read_csv(T / "p92_inhulets_profile.csv"); p = p[p.run == "U2b_B1B2_v003A"]
    fig, ax = plt.subplots(figsize=(4.5, 2.8), constrained_layout=True)
    ax.plot(p.northing_km, p.predicted_new_on_land_km2, "o-", color=FS.PALETTE["unet"], ms=3, lw=1, label="U2b mapped new flood on land"); ax.plot(p.northing_km, p.EVENT_FLOOD_label_km2, "s-", color=FS.PALETTE["s1"], ms=3, lw=1, label="EVENT_FLOOD label (S1 ≥ 2 peak dates)")
    ax.set_xlabel("northing, km (2-km bands up the Inhulets valley)", fontsize=7); ax.set_ylabel("km² per band", fontsize=7); ax.legend(fontsize=6); ax.tick_params(labelsize=6.5)
    FS.save(fig, "FigS06_inhulets_profile", FIG)


def figS07():
    """Hypsometry sensitivity: V_DEM(H) vs V_design(H) and dV/V_design (T22) -- the basis of the released volume in T21."""
    H = pd.read_csv(PT / "T22.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True)
    a.plot(H.level_evrf2019_m, H.V_dem_km3, color=FS.PALETTE["terrain"], lw=1.8, label="seamless DEM, level surface")
    a.plot(H.level_evrf2019_m, H.V_table19_km3, color=FS.PALETTE["ink2"], lw=1.5, ls="--", label="design Table 19 (BS-77 + 0.185 m)")
    a.set_xlabel("pool level, m (EVRF2019)", fontsize=7); a.set_ylabel("volume, km³", fontsize=7); a.legend(fontsize=6); a.tick_params(labelsize=6.5); a.grid(color=FS.PALETTE["grid"]); FS.panel_label(a, "a")
    ok = H.V_table19_km3 > 7.0
    b.plot(H.level_evrf2019_m[ok], H.dV_rel_pct[ok], color=FS.PALETTE["terrain"], lw=1.8, label="ΔV / V_design")
    b.plot(H.level_evrf2019_m[ok], H.dA_rel_pct[ok], color=FS.PALETTE["s1"], lw=1.4, ls=":", label="ΔA / A_design")
    b.axhline(0, color=FS.PALETTE["ink2"], lw=0.6); b.axvspan(5.6, 17.6, color=FS.PALETTE["gauge"], alpha=0.07, lw=0)
    b.set_xlabel("pool level, m (EVRF2019)", fontsize=7); b.set_ylabel("DEM − design, % of design", fontsize=7); b.legend(fontsize=6); b.tick_params(labelsize=6.5); b.grid(color=FS.PALETTE["grid"]); FS.panel_label(b, "b")
    fig.suptitle("Reservoir hypsometry: seamless DEM vs design table (shaded: drawdown range 5–13 June); open question for Paper 4 (historical bathymetry)", fontsize=7)
    FS.save(fig, "FigS07_hypsometry_sensitivity", FIG)


# ---- FigS08 / FigS09: reservoir drawdown maps (p95h) ------------------------------------------------------------------
def _res_ctx(step_m=60.0):
    """Shared frame for the reservoir maps: p95h module, pool (+1 km) geometry, extent in km, hillshade backdrop."""
    import rasterio
    from rasterio import features
    H = _ld("p95h", M6 / "p95h_reservoir_maps.py"); pool = CFG.load_utm("reservoir_full_pool_prebreach"); zone = pool.buffer(1000.0)
    x0, y0, x1, y1 = zone.bounds; ext = [x0 / 1e3, x1 / 1e3, y0 / 1e3, y1 / 1e3]
    with rasterio.open(BULK / "dem_seamless" / "dem_seamless_evrf2019_50m.tif") as s:
        win = rasterio.windows.from_bounds(x0, y0, x1, y1, transform=s.transform)
        dem = s.read(1, window=win, out_shape=(int(win.height // 2), int(win.width // 2))).astype("f4"); dem[dem == s.nodata] = np.nan
    hs = LightSource(azdeg=315, altdeg=40).hillshade(np.nan_to_num(dem, nan=np.nanmedian(dem)), vert_exag=8, dx=100, dy=100)

    def read(path, band=1, fill=0):
        """Read a 20 m tif on the frame window at ~step_m; cells outside pool + 1 km -> `fill`. Returns (array, extent km)."""
        from affine import Affine
        with rasterio.open(path) as s:
            w = rasterio.windows.from_bounds(x0, y0, x1, y1, transform=s.transform).round_offsets().round_lengths(); f = s.res[0] / step_m
            a = s.read(band, window=w, out_shape=(max(1, int(round(w.height * f))), max(1, int(round(w.width * f)))))
            tr = rasterio.windows.transform(w, s.transform) * Affine.scale(w.width / a.shape[1], w.height / a.shape[0])
        inside = features.rasterize([(zone.__geo_interface__, 1)], out_shape=a.shape, transform=tr, fill=0, dtype="uint8").astype(bool)
        a = a.copy(); a[~inside] = fill
        return a, [tr.c / 1e3, (tr.c + tr.a * a.shape[1]) / 1e3, (tr.f + tr.e * a.shape[0]) / 1e3, tr.f / 1e3]
    return H, pool, zone, ext, hs, read


def _res_panel(ax, ctx, arr, arr_ext, colours, title, first=False):
    H, pool, zone, ext, hs, read = ctx
    ax.imshow(hs, extent=ext, cmap="Greys_r", vmin=0, vmax=1, alpha=0.35, interpolation="bilinear")
    n = len(colours); m = np.ma.masked_equal(arr, 0)
    ax.imshow(m, extent=arr_ext, cmap=ListedColormap(colours), vmin=0.5, vmax=n + 0.5, interpolation="nearest")
    for g in getattr(pool, "geoms", [pool]):
        xs, ys = g.exterior.xy; ax.plot(np.asarray(xs) / 1e3, np.asarray(ys) / 1e3, color=FS.PALETTE["ink2"], lw=0.35)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(True); sp.set_color("#c3c2b7"); sp.set_linewidth(0.5)
    ax.set_title(title, fontsize=6.3, loc="left")
    if first:
        FS.scale_bar(ax, 20000, units_per_m=1e-3); FS.north_arrow(ax, x=0.08, y=0.80)


def _leg(ax, colours, labels, title=None, loc="center left", y=0.5):
    """Legend in a dedicated (axis-off) legend column; several legends per axis stack via add_artist."""
    ax.axis("off")
    lg = ax.legend([Patch(facecolor=c, edgecolor="#999", lw=0.3) for c in colours], labels, title=title, title_fontsize=5.8, fontsize=5.5, loc=loc,
                   bbox_to_anchor=(0.0, y), frameon=False, handlelength=1.0, alignment="left")
    ax.add_artist(lg)


def figS08():
    """Reservoir drawdown maps: modelled pool (p95f surface) + day of exposure, S1 VH dark surface, S2 k10e classes and water (p95h)."""
    import rasterio
    from affine import Affine
    ctx = _res_ctx(); H, pool, zone, ext, hs, read = ctx
    R = pd.read_csv(T / "p95h_reservoir_maps.csv"); RM = BULK / "reservoir_maps"
    fig, axs = plt.subplots(3, 5, figsize=(7.4, 5.0), constrained_layout=True, gridspec_kw=dict(width_ratios=[1, 1, 1, 1, 0.78])); lab = iter("abcdefghijkl")
    km = lambda tr, shp: [tr.c / 1e3, (tr.c + tr.a * shp[1]) / 1e3, (tr.f + tr.e * shp[0]) / 1e3, tr.f / 1e3]
    # row 1: model 06-07, 06-09, 06-13 + day of exposure
    z = np.load(RM / "model" / "wet_daily.npz"); shp = tuple(int(v) for v in z["shape"]); mtr = Affine(*z["transform"])
    un = lambda k: np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
    ref = un("2023-06-05"); mc = ["#1b6ca8", "#d9a441"]
    for j, d in enumerate(["2023-06-07", "2023-06-09", "2023-06-13"]):
        w = un(d); c = np.zeros(shp, "u1"); c[w] = 1; c[ref & ~w] = 2
        a = R[(R.source == "MODEL") & (R.date == d)].water_km2.iloc[0]
        _res_panel(axs[0, j], ctx, c, km(mtr, shp), mc, f"({next(lab)}) model {d[5:]}\n{a:.0f} km² water", first=(j == 0))
    with rasterio.open(RM / "model" / "exposed_day.tif") as s:
        e = s.read(1); etr = s.transform
    c = np.zeros(e.shape, "u1")
    for k, (lo, hi) in enumerate([(6, 6), (7, 7), (8, 8), (9, 10), (11, 13)], 1):
        c[(e >= lo) & (e <= hi)] = k
    c[e == 255] = 6; ec = ["#7d1d1d", "#c7522a", "#e08214", "#eda100", "#f2d98a", "#1b6ca8"]
    _res_panel(axs[0, 3], ctx, c, km(etr, e.shape), ec, f"({next(lab)}) model: day the\nbed falls dry")
    _leg(axs[0, 4], mc, ["pool water", "bed exposed since 06-05"], "model (p95f surface)", loc="upper left", y=1.0)
    _leg(axs[0, 4], ec, ["06-06", "06-07", "06-08", "06-09–10", "06-11–13", "still wet 06-13"], "day of exposure", loc="lower left", y=0.0)
    # row 2: S1
    sc = ["#1b6ca8", "#d9a441", "#c3c2b7"]
    for j, d in enumerate(["2023-06-01", "2023-06-08", "2023-06-13", "2023-06-21"]):
        z1 = np.load(RM / "s1" / f"{d}.npz"); sshp = tuple(int(v) for v in z1["shape"]); s_tr = Affine(*z1["transform"])
        u1 = lambda k: np.unpackbits(z1[k], count=sshp[0] * sshp[1]).reshape(sshp).astype(bool)
        if j == 0:
            d0 = u1("water"); spool = H.pool_on(s_tr, sshp)
        w, o = u1("water"), u1("observed"); c = np.zeros(sshp, "u1"); c[w & spool] = 1; c[o & ~w & d0 & spool] = 2; c[spool & ~o] = 3
        r = R[(R.source == "S1") & (R.date == d)].iloc[0]
        iou = f", IoU {r.iou_vs_model:.2f}" if np.isfinite(r.get("iou_vs_model", np.nan)) else ""
        _res_panel(axs[1, j], ctx, c[::2, ::2], km(s_tr, sshp), sc, f"({next(lab)}) S1 {d[5:]}\n{r.water_km2:.0f} km² dark{iou}")
    _leg(axs[1, 4], sc, ["VH dark: open water\nor smooth wet mud", "dark on 06-01, not now", "pool not observed"], "Sentinel-1 (VH, Otsu)")
    # row 3: S2 k10e classes + S2 water on 06-20 (p15 crosscheck, fully observed)
    for j, d in enumerate(["2023-06-05", "2023-07-05", "2023-09-08"]):
        c, cext = read(H.S2DIR / f"{d}_class.tif")
        r = R[(R.source == "S2_WATER3") & (R.date == d)].iloc[0]
        _res_panel(axs[2, j], ctx, c, cext, [H.K10E[k][1] for k in range(1, 10)], f"({next(lab)}) S2 classes {d[5:]}\n{r.observed_frac:.0%} observed")
    ztr, zshp = H.s2_grid(); xtr = H.xc_transform(ztr); z2 = np.load(H.S2XC / "2023-06-20.npz")
    u2 = lambda k: np.unpackbits(z2[k], count=zshp[0] * zshp[1]).reshape(zshp).astype(bool)
    w, v = u2("water"), u2("valid"); c = np.zeros(zshp, "u1"); c[v & ~w] = 2; c[w] = 1
    from rasterio import features
    c[~features.rasterize([(zone.__geo_interface__, 1)], out_shape=zshp, transform=xtr, fill=0, dtype="uint8").astype(bool)] = 0
    r = R[(R.source == "S2_CROSSCHECK") & (R.date == "2023-06-20")].iloc[0]
    _res_panel(axs[2, 3], ctx, c[::3, ::3], km(xtr, zshp), ["#1b6ca8", "#efece6"], f"({next(lab)}) S2 water 06-20\n{r.water_km2:.0f} km²")
    _leg(axs[2, 4], [H.K10E[k][1] for k in range(1, 10)] + ["#efece6"], [H.K10E[k][0].replace("_", " ").lower() for k in range(1, 10)] + ["observed, not water (l)"], "Sentinel-2 (p25 k10e)")
    fig.suptitle("Kakhovka pool drawdown: modelled surface (terrain-reconstructed) vs Sentinel-1 and Sentinel-2 observations; not observed is not dry", fontsize=7)
    FS.save(fig, "FigS08_reservoir_drawdown_maps", FIG)


def figS09():
    """All seven S2 indices over the pool in display classes: before the breach, drawdown, after (frozen p25 stacks)."""
    ctx = _res_ctx(); H, pool, zone, ext, hs, read = ctx
    dates = ["2023-06-05", "2023-07-05", "2023-09-08"]
    fig, axs = plt.subplots(len(H.INDEX_NAMES), len(dates) + 1, figsize=(6.6, 11.6), constrained_layout=True, gridspec_kw=dict(width_ratios=[1] * len(dates) + [0.45]))
    for i, nm in enumerate(H.INDEX_NAMES):
        edges, labels, cols = H.INDEX_BINS[nm]
        for j, d in enumerate(dates):
            v, vext = read(H.S2DIR / f"{d}_indices.tif", band=i + 1, fill=-32768); v = v.astype("f4"); v[v == -32768] = np.nan; v /= 1e4
            _res_panel(axs[i, j], ctx, H.classify_index(v, nm), vext, cols, f"{nm} · {d}", first=(i == 0 and j == 0))
        _leg(axs[i, -1], cols, labels, nm)
    fig.suptitle("Sentinel-2 indices over the Kakhovka pool (+1 km), display classes; 06-05 pre-breach, 07-05 drawdown, 09-08 after; blank = not observed", fontsize=7)
    FS.save(fig, "FigS09_reservoir_s2_indices", FIG)


ALL = {"Fig01": (fig01, True), "Fig02": (fig02, False), "Fig03": (fig03, True), "Fig04": (fig04, False), "Fig05": (fig05, True), "Fig06": (fig06, False), "Fig07": (fig07, True), "Fig08": (fig08, False), "Fig09": (fig09, False),
       "FigS01": (figS01, False), "FigS02": (figS02, False), "FigS03": (figS03, False), "FigS04": (figS04, False), "FigS05": (figS05, False), "FigS06": (figS06, False), "FigS07": (figS07, False),
       "FigS08": (figS08, True), "FigS09": (figS09, True)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--only", nargs="*"); ap.add_argument("--tables-only", action="store_true"); a = ap.parse_args()
    FS.use_style(); FIG.mkdir(parents=True, exist_ok=True)
    for name, (fn, bulk) in ALL.items():
        if a.only and name not in a.only:
            continue
        if a.tables_only and bulk:
            continue
        try:
            fn(); print("ok", name, flush=True)
        except Exception as e:                                             # noqa: BLE001
            print("FAILED", name, repr(e), flush=True)


if __name__ == "__main__":
    main()
