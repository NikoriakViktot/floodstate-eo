# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Publication figures (main text Fig01-Fig08, supplement FigS01-FigS06).
"""P97 -- publication figures for Paper 3, 300 dpi PNG + PDF, one style (floodstate_eo.visualization.figstyle).

Main text (claims decide the figures):
  Fig01 study area (hillshade, frames, p42 floodplain, reconstructed new water, reporting regions, SWOT nodes, gauges, dam) [bulk]
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
FigS08 reservoir drawdown maps (model / S1 / S2 classes / day of exposure, p95h) [bulk], FigS09 the 7 S2 indices over the pool [bulk],
FigS10 the design level-area-volume curves (monograph Table 19) with the observed 2023 levels on them (p95i) [tables],
FigS11-FigS13 terrain-error variogram, Monte-Carlo convergence, water-surface offset sensitivity [tables],
FigS14 observational support of the new inundation: map of the support classes on 7 June with the SWOT nodes and the three
gauges, and the daily full reconstruction vs its supported core (p95l) [bulk], FigS15 the two withheld gauges (Kalynivske,
Mykolaiv): levels, absolute and event-relative errors (p95k) [tables].
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
from matplotlib.lines import Line2D
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.visualization import figstyle as FS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]; M6 = ROOT / "workflows" / "m6"
T = ROOT / "tables"; PT = ROOT / "publication" / "tables"; FIG = ROOT / "publication" / "figures"; RUNS = ROOT / "runs"
BULK = CFG.BULK_ROOT
ZONES = {"ZONE_4_DAM_TO_KHERSON_FLOODWAY": "B1", "ZONE_2_KHERSON_DELTA": "B2"}
BREACH = pd.Timestamp("2023-06-06")
REG_TITLE = {"DNIPRO_CORRIDOR": "Dnipro corridor (Inhulets reported separately)", "P42_FLOODPLAIN_DOMAIN": "p42 floodplain domain", "INHULETS_VALLEY_rect": "Inhulets valley (backwater)"}


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def km_ext(G):
    return [G["transform"].c / 1e3, (G["transform"].c + 20 * G["nx"]) / 1e3, (G["transform"].f - 20 * G["ny"]) / 1e3, G["transform"].f / 1e3]


def zone_mosaic(arrays: dict, fill):
    """Mosaic two 20 m zone arrays (dict zone -> (array, G)) onto their union grid; ZONE_2 owns the overlap."""
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


KALYNIVSKE_LONLAT = (32 + 57 / 60 + 38 / 3600, 47 + 6 / 60 + 59 / 3600)          # Inhulets gauge 80575 (p95k; withheld validation site)
REPORT_LABEL = "Inhulets reporting region: included in the reconstruction, reported separately"


def max_new_extent():
    """Maximum depth of new inundation over the event on the zone mosaic (nominal world, primary rule) and the northern edge of
    the reconstruction domain (km). No region mask: the Inhulets valley and every other cell of the domain are included."""
    mx = {z: read_zone(BULK / "floodplain_dyn" / f"{z}_connected_ceiling" / "max_depth_m.tif") for z in ZONES}
    X, ext = zone_mosaic(mx, np.float32(np.nan)); X[~(X > 0)] = np.nan
    return X, ext


def weak_support(ext_shape):
    """Cells whose water surface rests on weak (> 10 km) or cross-river support (p95l support_class.tif codes 3 and 4)."""
    arrs = {}
    for z in ZONES:
        with __import__("rasterio").open(BULK / "floodplain_dyn" / f"{z}_connected_ceiling" / "support_class.tif") as s:
            arrs[z] = (np.isin(s.read(1), (3, 4)).astype("u1"), dict(transform=s.transform, ny=s.height, nx=s.width))
    W, _ = zone_mosaic(arrs, np.uint8(0))
    assert W.shape == ext_shape, (W.shape, ext_shape)
    return W.astype(bool)


def reporting_overlay(ax, domain_top_km, P92=None):
    """The reporting regions (thin dashed; they split the tables, they mask nothing), the withheld Inhulets gauge and the
    northern edge of the reconstruction domain. Returns legend handles."""
    from matplotlib.lines import Line2D
    from pyproj import Transformer
    P92 = P92 or _ld("p92", M6 / "p92_flood_area_dam_to_liman.py")
    for nm, (x0, y0, x1, y1) in P92.CUT_RECTS.items():
        y1 = min(y1 / 1e3, domain_top_km)
        ax.add_patch(Rectangle((x0 / 1e3, y0 / 1e3), (x1 - x0) / 1e3, y1 - y0 / 1e3, fill=False, ec="#e34948",
                               lw=1.0 if nm == "inhulets_valley" else 0.5, ls="--", zorder=4))
    ax.axhline(domain_top_km, color=FS.PALETTE["ink2"], lw=0.6, ls=":", zorder=4)
    x, y = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True).transform(*KALYNIVSKE_LONLAT)
    ax.plot(x / 1e3, y / 1e3, "^", ms=6, mfc="white", mec=FS.PALETTE["ink"], mew=1.1, zorder=6)
    ax.annotate("Kalynivske 80575\n(withheld validation gauge)", (x / 1e3, y / 1e3), xytext=(6, -2), textcoords="offset points",
                fontsize=5.5, va="top", ha="left", zorder=6, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.4))
    return [Patch(fc="none", ec="#e34948", ls="--", label=REPORT_LABEL),
            Line2D([], [], color=FS.PALETTE["ink2"], lw=0.6, ls=":", label="northern edge of the reconstruction domain"),
            Line2D([], [], marker="^", ls="none", mfc="white", mec=FS.PALETTE["ink"], label="Kalynivske 80575 (withheld validation gauge)")]


S2_DATES = {"pre": "2022-06-13", "event": "2023-06-18"}                    # p97b: own Sentinel-2 L2A true colour on the 20 m zone grids


def s2_rgb(date_key="pre", step=2):
    """(rgb uint8 (H, W, 3), extent km) of the two zone mosaics of the own Sentinel-2 true colour (p97b), decimated by `step`
    (20 m -> 40 m at step 2); light grey where no cloud-free scene exists. Returns None when the basemap was not built."""
    arrs = {}
    for z in ZONES:
        p = BULK / "truecolour" / f"{z}_s2_{S2_DATES[date_key]}_20m.tif"
        if not p.exists():
            return None, None
        import rasterio
        with rasterio.open(p) as s:
            arrs[z] = (s.read(), dict(transform=s.transform, ny=s.height, nx=s.width))
    bands = []
    for i in range(3):
        b, ext = zone_mosaic({z: (a[i], G) for z, (a, G) in arrs.items()}, np.uint8(0)); bands.append(b[::step, ::step])
    rgb = np.stack(bands, -1); nod = rgb.max(-1) == 0; rgb[nod] = 235
    return rgb, ext


def s2_basemap(ax, date_key="pre", step=2, alpha=1.0):
    """Draw the own Sentinel-2 true colour under a map (contains modified Copernicus Sentinel data); falls back to nothing."""
    rgb, ext = s2_rgb(date_key, step)
    if rgb is None:
        return False
    ax.imshow(rgb, extent=ext, interpolation="bilinear", alpha=alpha, rasterized=True, zorder=0)
    return True


def hatch_mask(ax, mask, ext, color, hatch="//////", step=1, zorder=3, lw=0.0):
    """Coloured hatching over the True cells of `mask` (no fill), the reliability layer drawn on top of the water."""
    m = mask[::step, ::step].astype("f4")
    if not m.any():
        return
    cs = ax.contourf(m, levels=[0.5, 1.5], colors="none", hatches=[hatch], extent=ext, origin="upper", zorder=zorder)
    cs.set_edgecolor(color); cs.set_linewidth(lw)


def outline_mask(ax, mask, ext, color, step=1, lw=0.7, zorder=4):
    """Outline of the True cells of `mask`."""
    m = mask[::step, ::step].astype("f4")
    if not m.any():
        return
    ax.contour(m, levels=[0.5], colors=[color], linewidths=lw, extent=ext, origin="upper", zorder=zorder)


def furniture(ax, ext, scale_km=10):
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal")
    ax.set_xlabel("easting, km (UTM 36N)", fontsize=7); ax.set_ylabel("northing, km", fontsize=7); ax.tick_params(labelsize=6)
    FS.scale_bar(ax, scale_km * 1000, units_per_m=1e-3); FS.north_arrow(ax); FS.graticule(ax, "EPSG:32636", units_per_m=1e-3)


# ---- Fig01 -----------------------------------------------------------------------------------------------------------
def fig01():
    import rasterio
    P92 = _ld("p92", M6 / "p92_flood_area_dam_to_liman.py")
    with rasterio.open(BULK / "dem_seamless" / "dem_seamless_evrf2019_50m.tif") as s:
        dem = s.read(1).astype("f4"); dem[dem == s.nodata] = np.nan; tr = s.transform
        ext = [tr.c / 1e3, (tr.c + tr.a * s.width) / 1e3, (tr.f + tr.e * s.height) / 1e3, tr.f / 1e3]
    hs = LightSource(azdeg=315, altdeg=40).hillshade(np.nan_to_num(dem, nan=0), vert_exag=3, dx=50, dy=50)
    fig, ax = plt.subplots(figsize=(7.2, 7.6), constrained_layout=True)
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
    X, xext = max_new_extent()
    ax.imshow(np.ma.masked_where(np.isnan(X[::2, ::2]), np.ones_like(X[::2, ::2])), cmap=ListedColormap([FS.PALETTE["terrain"]]), extent=xext,
              alpha=0.45, interpolation="nearest", rasterized=True, zorder=2)
    rep = reporting_overlay(ax, xext[3], P92)
    n = pd.read_csv(T / "p59_swot_flood_nodes.csv", usecols=["node_id", "x", "y", "river_name"]).drop_duplicates("node_id")
    main = ~n.river_name.isin(["Inhulets", "Kokan'"])
    ax.scatter(n.x[main] / 1e3, n.y[main] / 1e3, s=2, color=FS.PALETTE["terrain"], label="SWOT nodes, Dnipro"); ax.scatter(n.x[~main] / 1e3, n.y[~main] / 1e3, s=2, color=FS.PALETTE["s2"], label="SWOT nodes, tributaries / side channels")
    from pyproj import Transformer
    tfm = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True)
    kx, ky = tfm.transform(32.612026, 46.623750); dx, dy = tfm.transform(33.3667, 46.7783)
    ax.plot(kx / 1e3, ky / 1e3, "s", color=FS.PALETTE["gauge"], ms=6, label="Kherson gauge 80805"); ax.plot(dx / 1e3, dy / 1e3, "^", color="#e34948", ms=7, label="Kakhovka dam")
    ax.set_xlim(436, 540); ax.set_ylim(5133, 5226); furniture(ax, [436, 540, 5133, 5226], 20)
    ax.legend(handles=[Patch(fc="#b9c7d6", label="terrain below 1 m (water / channels)"), Patch(fc=FS.PALETTE["terrain"], alpha=0.45, label="reconstructed new water, maximum extent over the event (Dnipro and Inhulets)"),
                       Patch(fc="none", ec=FS.PALETTE["terrain"], label="p42 terrain-eligible floodplain"),
                       *rep, *ax.get_legend_handles_labels()[0]], loc="upper center", fontsize=6, ncol=2, bbox_to_anchor=(0.5, -0.07), frameon=False)
    ax.set_title("Study area: lower Dnipro from the Kakhovka dam to the Dnipro–Buh liman", fontsize=9, loc="left")
    FS.save(fig, "Fig01_study_area", FIG)


# ---- Fig02 -----------------------------------------------------------------------------------------------------------
def fig02():
    """The hierarchy of evidence (maintainer, 2026-09-29): four levels, top = strongest; a lower level explains or diagnoses,
    it never overrides a higher one."""
    fig, ax = plt.subplots(figsize=(7.2, 5.8)); ax.axis("off")
    levels = [("1  Terrain-connectivity reconstruction and its uncertainty", FS.PALETTE["terrain"],
               ["SWOT node water surface + Kherson gauge (EVRF2019) over the seamless terrain–bed model;",
                "connectivity to the pre-event water network; the same-rule pre-event baseline",
                "→ daily new and total water area, depth and volume; 1000 coherent Monte-Carlo worlds; SWOT support classes"]),
              ("2  Independent observations", FS.PALETTE["s1"],
               ["withheld gauges Kalynivske (Inhulets) and Mykolaiv (liman); Sentinel-1 per acquisition date (POD / FAR / CSI);",
                "night ICESat-2 ground heights (pass hold-out of the class bias); SWOT vs the Kherson gauge (input consistency)"]),
              ("3  Surface-context diagnostics", FS.PALETTE["rf"],
               ["RF20 surface classes, WorldCover, ground elevation above the reconstructed surface",
                "→ where each source is blind; S1-only detections that the connected water surface cannot reach"]),
              ("4  Weak-label ML diagnostics", FS.PALETTE["unet"],
               ["U-Net arms on the canonical labels v004, three training seeds (v002 / v003_A as provenance)",
                "→ behaviour under weak supervision: agreement with weak labels, not flood-mapping accuracy"])]
    links = ["checked by", "disagreement explained by", "labels, strata and blind spots inform"]
    h, gap, top = 0.175, 0.055, 0.985
    for k, (title, c, lines) in enumerate(levels):
        y = top - h - k * (h + gap)
        ax.add_patch(FancyBboxPatch((0.02, y), 0.96, h, boxstyle="round,pad=0.008", fc="white", ec=c, lw=1.8, transform=ax.transAxes))
        ax.text(0.04, y + h - 0.028, title, ha="left", va="top", fontsize=8, fontweight="bold", color=c, transform=ax.transAxes)
        ax.text(0.04, y + h - 0.075, "\n".join(lines), ha="left", va="top", fontsize=6.3, transform=ax.transAxes, linespacing=1.35)
        if k < len(levels) - 1:
            ax.add_patch(FancyArrowPatch((0.5, y - 0.003), (0.5, y - gap + 0.004), arrowstyle="-|>", mutation_scale=11, color=FS.PALETTE["ink2"], transform=ax.transAxes, lw=1.0))
            ax.text(0.52, y - gap / 2, links[k], ha="left", va="center", fontsize=6.2, color=FS.PALETTE["ink2"], transform=ax.transAxes)
    ax.text(0.02, 0.0, "Evidence runs from top to bottom: a lower level explains or diagnoses, it never overrides a higher one.\n"
            "Areas carry their semantics: observed_S1 / mapped_UNet / terrain_reconstructed / literature_reported.", fontsize=6, transform=ax.transAxes,
            color=FS.PALETTE["ink2"], va="bottom")
    FS.save(fig, "Fig02_evidence_hierarchy", FIG)

# ---- Fig03 -----------------------------------------------------------------------------------------------------------
def fig03():
    """U-Net arms: (a, b) the U2b prediction in the reference ontology, (c) paired comparisons on identical TEST blocks.
    Arms on the corrected labels (v004, three training seeds; review F09/F10/F11) once trained, else the v003_A history."""
    P91 = _ld("p91", M6 / "p91_m6_maps_v003A.py")
    V4 = (RUNS / "U2b_B1B2_v004" / "validation_threshold.json").exists()
    LAB, RUNMAP = ("v004", "U2b_B1B2_v004") if V4 else ("v003_A", "U2b_B1B2_v003A")
    fig = plt.figure(figsize=(7.2, 9.6)); gs = fig.add_gridspec(3, 2, height_ratios=[1.35, 0.85, 0.55], hspace=0.38, wspace=0.18, bottom=0.07)
    cm = ListedColormap([c for _, c in FS.STATE_COLOURS.values()])
    for j, fid in enumerate(("B1", "B2")):
        ax = fig.add_subplot(gs[0, j]); L = P91.load(fid, LAB); sc, thr = P91.score(fid, RUNMAP); pred = sc >= thr
        st = np.zeros(sc.shape, "u1"); st[L["has"]] = 1; st[L["has"] & (L["ont"] == 2)] = 2; st[pred & L["has"]] = 5; st[pred & (L["ont"] == 1)] = 4; st[pred & (L["ont"] == 2)] = 3
        ax.imshow(st, cmap=cm, vmin=-0.5, vmax=5.5, extent=L["ext"], interpolation="nearest", rasterized=True); P91.test_outline(ax, L["role"], L["ext"])
        furniture(ax, L["ext"], 10); FS.panel_label(ax, "ab"[j]); ax.set_title(f"frame {fid}: U2b ({LAB}), score ≥ {thr:.2f}", fontsize=8, loc="left")
    pb = pd.read_csv(PT / "T06.csv"); pb7 = pd.read_csv(PT / "T07b.csv")
    rows = []                                                                   # (name, [(median, lo, hi), ...one per seed], colour)
    if V4:
        seeds = sorted(pb[pb.labels == "v004"].seed.dropna().unique())
        sfx = lambda sd: "" if sd == seeds[0] else f"_s{int(sd)}"
        for comp, ep, name in [("U2 - U0d", "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2", "U0d→U2 (+HAND): unlabelled-cropland burden, km²"),
                               ("U2 - U0d", "B_recall_flooded_open_low_veg", "U0d→U2 (+HAND): recall on flooded open low vegetation"),
                               ("U1 - U0d", "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2", "U0d→U1 (+RF20 context): unlabelled-cropland burden, km²")]:
            r = pb[(pb.comparison == comp) & (pb.labels == "v004") & (pb.endpoint == ep)].sort_values("seed")
            if len(r):
                rows.append((name, list(zip(r["median"], r.ci_lo, r.ci_hi)), FS.PALETTE["unet"]))
        for A, B, ep, name, col in [("U2_B1B2_v002nt", "U2_B1B2_v004", "R_pred_on_reference_water_km2", "label effect v002→v004 rule (U2): flood on reference water, km²", FS.PALETTE["unet"]),
                                    ("U2_B1B2_v002nt", "U2_B1B2_v004", "E_recall_event_flood", "label effect v002→v004 rule (U2): EVENT_FLOOD recall", FS.PALETTE["unet"]),
                                    ("U2_B1B2_v004", "U2b_B1B2_v004", "R_pred_on_reference_water_km2", "U2→U2b (+W_pre, diagnostic): flood on reference water, km²", FS.PALETTE["muted"]),
                                    ("U2_B1B2_v004", "U2b_B1B2_v004", "E_recall_event_flood", "U2→U2b (+W_pre, diagnostic): EVENT_FLOOD recall", FS.PALETTE["muted"])]:
            v = []
            for sd in seeds:
                r = pb7[(pb7.A == A + sfx(sd)) & (pb7.B == B + sfx(sd)) & (pb7.endpoint == ep)]
                if len(r):
                    v.append((float(r["median"].iloc[0]), float(r.lo.iloc[0]), float(r.hi.iloc[0])))
            if v:
                rows.append((name, v, col))
    else:
        for comp, lab, ep, name in [("U2 - U0d", "v002", "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2", "U0d→U2 (+HAND): unlabelled-cropland burden, km²"),
                                    ("U2 - U0d", "v002", "B_recall_flooded_open_low_veg", "U0d→U2 (+HAND): recall on flooded open low vegetation"),
                                    ("U1 - U0d", "v002", "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2", "U0d→U1 (+RF20 context): unlabelled-cropland burden, km²")]:
            r = pb[(pb.comparison == comp) & (pb.labels == lab) & (pb.endpoint == ep)]
            if len(r):
                rows.append((name, [(float(r["median"].iloc[0]), float(r.ci_lo.iloc[0]), float(r.ci_hi.iloc[0]))], FS.PALETTE["unet"]))
        for A, B, ep, name in [("U2_B1B2_v1", "U2_B1B2_v003A", "R_pred_on_reference_water_km2", "label effect v002→v003_A (U2): flood on reference water, km²"),
                               ("U2_B1B2_v1", "U2_B1B2_v003A", "E_recall_event_flood", "label effect v002→v003_A (U2): EVENT_FLOOD recall"),
                               ("U2_B1B2_v003A", "U2b_B1B2_v003A", "R_pred_on_reference_water_km2", "U2→U2b (+W_pre, diagnostic): flood on reference water, km²"),
                               ("U2_B1B2_v003A", "U2b_B1B2_v003A", "E_recall_event_flood", "U2→U2b (+W_pre, diagnostic): EVENT_FLOOD recall")]:
            r = pb7[(pb7.A == A) & (pb7.B == B) & (pb7.endpoint == ep)]
            if len(r):
                rows.append((name, [(float(r["median"].iloc[0]), float(r.lo.iloc[0]), float(r.hi.iloc[0]))], FS.PALETTE["muted"] if "diagnostic" in name else FS.PALETTE["unet"]))
    # review F15: areas (km²) and recall on separate axes -- one axis made the recall rows unreadable
    for k, (unit, sel) in enumerate((("km²", lambda n: "km²" in n), ("recall", lambda n: "km²" not in n))):
        rr = [r for r in rows if sel(r[0])]
        if not rr:
            continue
        ax = fig.add_subplot(gs[1 + k, :]); y = np.arange(len(rr))[::-1]
        for (name, v, c), yy in zip(rr, y):
            offs = np.linspace(-0.22, 0.22, len(v)) if len(v) > 1 else [0.0]
            for (m, lo, hi), dy in zip(v, offs):
                ax.hlines(yy + dy, lo, hi, color=c, lw=1.4 if len(v) > 1 else 1.6); ax.plot(m, yy + dy, "o", color=c, ms=4 if len(v) > 1 else 5)
        ax.set_yticks(y); ax.set_yticklabels([r[0].replace(", km²", "") for r in rr], fontsize=6.5); ax.axvline(0, color=FS.PALETTE["ink2"], lw=0.8, ls=":")
        ax.grid(axis="x", color=FS.PALETTE["grid"]); ax.tick_params(axis="x", labelsize=6.5); ax.set_ylim(-0.6, len(rr) - 0.4)
        ax.set_xlabel(f"paired difference B − A on identical spatial blocks, {unit} (median, 95 % interval)", fontsize=7); FS.panel_label(ax, "cd"[k])
        if k == 0:
            ax.set_title("Paired arm comparisons on the frozen TEST blocks (agreement with weak labels; grey = not independent, W_pre is a label ingredient)"
                         + ("; one marker per training seed" if V4 else ""), fontsize=7.5, loc="left")
    fig.legend(handles=[Patch(fc=c, ec="#c3c2b7", label=n) for n, c in FS.STATE_COLOURS.values()] + [Patch(fc="none", ec="#0b0b0b", ls="--", label="TEST blocks")],
               loc="lower center", bbox_to_anchor=(0.5, -0.01), ncol=4, fontsize=6.2, frameon=False)
    FS.save(fig, "Fig03_unet_experiment", FIG)

# ---- Fig04 -----------------------------------------------------------------------------------------------------------
def fig04():
    """Daily reconstructed series, dam -> liman: total water-surface area with the PRIMARY Monte-Carlo band, daily change of the
    newly inundated area as bars, S1, U-Net, gauge. The emulator is a diagnostic outside the evidence path (D-EMU) and is not drawn."""
    d = pd.read_csv(T / "p95_daily_area_pooled_connected_ceiling.csv"); d["t"] = pd.to_datetime(d.date)
    t12 = pd.read_csv(PT / "T12b.csv") if (PT / "T12b.csv").exists() else (pd.read_csv(PT / "T12.csv") if (PT / "T12.csv").exists() else None)   # T12b: every day
    s1 = pd.read_csv(T / "p94_flood_dynamics_s1.csv"); s1["t"] = pd.to_datetime(s1.date)
    p92 = pd.read_csv(T / "p92_flood_area_dam_to_liman.csv")                    # U2b on the canonical v004 labels, three training seeds (D-SEEDS)
    u2b = p92[p92.run.isin(["U2b_B1B2_v004", "U2b_B1B2_v004_s20261001", "U2b_B1B2_v004_s20261002"])].groupby("region").predicted_flood_km2.agg(["min", "max"])
    regs = ["DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect"]
    fig, axs = plt.subplots(3, 3, figsize=(7.4, 7.6), gridspec_kw=dict(height_ratios=[3, 1.4, 1.0]), sharex="col", constrained_layout=True)
    for j, r in enumerate(regs):
        a, b, c = axs[0, j], axs[1, j], axs[2, j]; s = d[d.region == r].sort_values("t")
        if t12 is not None and "W_total_p05_km2" in t12.columns:
            tt = t12[t12.region == r].dropna(subset=["W_total_p05_km2"]).copy(); tt["t"] = pd.to_datetime(tt.date); tt = tt.sort_values("t")
            nd = int(tt.n_draws.dropna().max()) if "n_draws" in tt.columns and tt.n_draws.notna().any() else 0
            a.fill_between(tt.t, tt.W_total_p05_km2, tt.W_total_p95_km2, color=FS.PALETTE["terrain"], alpha=0.28, lw=0, label=f"PRIMARY: Monte-Carlo p05–p95 ({nd} coherent worlds)", zorder=3)
        med = None
        if t12 is not None and "W_total_p50_km2" in t12.columns:
            med = t12[t12.region == r].dropna(subset=["W_total_p50_km2"]).copy(); med["t"] = pd.to_datetime(med.date); med = med.sort_values("t")
        if med is not None and len(med) > 20:                               # the reported series: MC median every day
            a.plot(med.t, med.W_total_p50_km2, color=FS.PALETTE["ink"], lw=1.6, label="reconstructed total water-surface area, MC median")
            a.plot(s.t, s.potential_km2, color=FS.PALETTE["ink"], lw=0.7, ls=":", label="deterministic nominal run")
        else:
            a.plot(s.t, s.potential_km2, color=FS.PALETTE["ink"], lw=1.6, label="reconstructed total water-surface area, nominal run")
        pun = T / "p95_daily_area_pooled_connected_ceiling_dem_uncorrected.csv"
        if pun.exists():
            un = pd.read_csv(pun); un = un[un.region == r]; a.plot(pd.to_datetime(un.date), un.potential_km2, color=FS.PALETTE["s2"], lw=1, ls="-", label="total, terrain as delivered (no residual bias removed)")
        o = s1[s1.region == r]; full, part = o[o.coverage >= 0.9], o[o.coverage < 0.9]
        a.plot(full.t, full.water_km2, "D", color=FS.PALETTE["s1"], ms=4.5, label="S1 total dark water"); a.plot(part.t, part.water_km2, "D", color=FS.PALETTE["s1"], ms=4.5, mfc="white", label="S1, partial coverage")
        a.set_title(REG_TITLE[r], fontsize=7.5, loc="left"); a.set_ylabel("reconstructed total water-surface area, km²", fontsize=6.5); FS.panel_label(a, "abc"[j], x=0.02, y=0.98)
        # daily change of NEW inundation as bars (+ filling, - draining)
        ser = (med.t, med.A_p50_km2) if med is not None and len(med) > 20 else (s.t, s.new_km2)
        inc = pd.Series(ser[1].values).diff().fillna(0).values
        b.bar(ser[0], inc, width=0.8, color=np.where(inc >= 0, FS.PALETTE["terrain"], FS.PALETTE["s1"]), lw=0)
        b.plot(ser[0], ser[1], color=FS.PALETTE["ink"], lw=1.0, label="reconstructed newly inundated area (MC median)" if ser[0] is not s.t else "reconstructed newly inundated area")
        if ser[0] is not s.t:
            b.fill_between(med.t, med.A_p05_km2, med.A_p95_km2, color=FS.PALETTE["terrain"], alpha=0.25, lw=0)
        b.axhline(0, color=FS.PALETTE["ink2"], lw=0.5)
        if r in u2b.index:
            b.axhspan(u2b.loc[r, "min"], u2b.loc[r, "max"], color=FS.PALETTE["unet"], alpha=0.18, lw=0, label="U-Net U2b persistent event flood (v004, three seeds: range)")
        b.set_ylabel("newly inundated area, km²\n(bars: daily change)", fontsize=6.5); FS.panel_label(b, "def"[j], x=0.02, y=0.98)
        c.plot(s.t, s.kherson_gauge_m, color=FS.PALETTE["gauge"], lw=1.3); c.set_ylabel("Kherson\nstage, m", fontsize=6.5)
        for ax in (a, b, c):
            FS.date_axis(ax, BREACH, every_days=7); ax.tick_params(labelsize=6); ax.set_xlim(pd.Timestamp("2023-05-31"), pd.Timestamp("2023-07-05"))
        a.set_ylim(0, None)
    h, l = axs[0, 0].get_legend_handles_labels(); h2, l2 = axs[1, 0].get_legend_handles_labels()
    fig.legend(h + h2, l + l2,
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
    """Event-scale spatial result below the dam (nominal world of the primary rule): (a) the maximum depth of new inundation over
    the event (decision D-DEPTH), (b) depth on 8 June (no full-coverage scene of the corridor), (c) duration."""
    mx, dep, dur = {}, {}, {}
    for z in ZONES:
        d = BULK / "floodplain_dyn" / f"{z}_connected_ceiling"
        mx[z] = read_zone(d / "max_depth_m.tif"); dep[z] = read_zone(d / "depth_2023-06-08_m.tif"); dur[z] = read_zone(d / "duration_days.tif")
    X, ext = zone_mosaic(mx, np.float32(np.nan)); D, _ = zone_mosaic(dep, np.float32(np.nan)); U, _ = zone_mosaic(dur, np.float32(0))
    X[~(X > 0)] = np.nan; D[~(D > 0)] = np.nan
    weak = weak_support(X.shape) & np.isfinite(X)                            # D-SUPPORT: shown as hatching over the water, never as a mask
    fig, axs = plt.subplots(3, 1, figsize=(7.2, 11.6), constrained_layout=True); box = [ext[0], min(ext[1], 540), 5136, ext[3]]
    P92 = _ld("p92", M6 / "p92_flood_area_dam_to_liman.py")

    def overlay(ax):
        hatch_mask(ax, weak, ext, FS.PALETTE["s2"], step=4)
        return [Patch(fc="none", ec=FS.PALETTE["s2"], hatch="//////", label="weak (> 10 km) or cross-river water-surface support (p95l)"),
                *reporting_overlay(ax, ext[3], P92)]
    for k, (ax, A, lab, title) in enumerate(((axs[0], X, "maximum depth of new inundation, m (26 May – 10 Jul)", "Maximum depth of new inundation over the event (26 May – 10 Jul)"),
                                             (axs[1], D, "depth of new inundation, m (2023-06-08)", "Depth of new inundation on 8 June (no full-coverage scene of the corridor)"))):
        s2_basemap(ax, "pre", step=2)
        im = ax.imshow(A[::2, ::2], cmap=FS.SEQ_DEPTH, vmin=0, vmax=6, extent=ext, interpolation="nearest", rasterized=True, zorder=2)
        furniture(ax, box, 10); cb = fig.colorbar(im, ax=ax, shrink=0.6, pad=0.01, extend="max"); cb.set_label(lab, fontsize=6.5); FS.panel_label(ax, "ab"[k])
        if k == 0:
            handles = overlay(ax)
        ax.set_title(title, fontsize=8, loc="left")
    c = axs[2]; s2_basemap(c, "pre", step=2)
    im2 = c.imshow(np.ma.masked_where(U[::2, ::2] == 0, U[::2, ::2]), cmap=FS.SEQ_DAYS, vmin=1, vmax=20, extent=ext, interpolation="nearest", rasterized=True, zorder=2)
    furniture(c, box, 10); fig.colorbar(im2, ax=c, shrink=0.6, pad=0.01).set_label("days with new inundation (26 May – 10 Jul)", fontsize=6.5); FS.panel_label(c, "c")
    overlay(c)
    fig.legend(handles=handles, loc="outside lower center", ncol=1, fontsize=6, frameon=False)
    c.set_title("Duration of terrain-reconstructed new inundation", fontsize=8, loc="left")
    FS.save(fig, "Fig07_event_scale_reconstruction", FIG)


def fig10():
    """Water depth in the Kakhovka pool (decision D-DEPTH): the full pool on 5 June and the drawdown on 7, 9 and 13 June (p95m:
    the p95f sloped surface minus the 50 m seamless terrain-bed model; the same model as the pool volume of T21)."""
    S = pd.read_csv(T / "p95m_reservoir_depth.csv").set_index("date")
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 6.4), constrained_layout=True)
    pool = CFG.load_utm("reservoir_full_pool_prebreach")
    for ax, d, lab in zip(axs.ravel(), ("2023-06-05", "2023-06-07", "2023-06-09", "2023-06-13"), "abcd"):
        A, G = read_zone(BULK / "reservoir_maps" / "model" / f"depth_{d}.tif"); tr = G["transform"]
        ext = [tr.c / 1e3, (tr.c + tr.a * G["nx"]) / 1e3, (tr.f + tr.e * G["ny"]) / 1e3, tr.f / 1e3]
        im = ax.imshow(A, cmap=FS.SEQ_DEPTH, vmin=0, vmax=20, extent=ext, interpolation="nearest", rasterized=True)
        xy = np.asarray(pool.exterior.coords) / 1e3 if hasattr(pool, "exterior") else None
        if xy is not None:
            ax.plot(xy[:, 0], xy[:, 1], color=FS.PALETTE["ink2"], lw=0.4)
        else:
            for g in pool.geoms:
                q = np.asarray(g.exterior.coords) / 1e3; ax.plot(q[:, 0], q[:, 1], color=FS.PALETTE["ink2"], lw=0.4)
        r = S.loc[d]; x0, y0, x1, y1 = (np.asarray(pool.bounds) / 1e3) + np.array([-4, -4, 4, 4])     # crop to the pool
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
        ax.set_title(f"{d}{' — full pool, before the breach' if d == '2023-06-05' else ''}\nwet {r.wet_km2:,.0f} km² · {r.volume_km3:.1f} km³ · mean depth {r.depth_mean_m:.1f} m",
                     fontsize=7, loc="left")
        ax.set_aspect("equal"); ax.tick_params(labelsize=6); ax.set_xlabel("easting, km (UTM 36N)", fontsize=6.5); ax.set_ylabel("northing, km", fontsize=6.5); FS.panel_label(ax, lab)
    fig.colorbar(im, ax=axs, shrink=0.55, pad=0.01, extend="max").set_label("water depth in the pool, m (terrain-reconstructed)", fontsize=7)
    fig.suptitle("Kakhovka reservoir water depth: the full pool and the drawdown (daily sloped surface over the seamless terrain–bed model)", fontsize=8)
    FS.save(fig, "Fig10_reservoir_depth", FIG)

# ---- Fig08 -----------------------------------------------------------------------------------------------------------
def fig08():
    D = pd.read_csv(PT / "T15.csv"); D = D[~D.category.str.contains("box=")]
    order = ["observed_neither", "both", "terrain_only", "S1_only_ground_lt2m_above", "S1_only_ground_ge2m_above"]
    lab = {"observed_neither": "neither", "both": "A both", "terrain_only": "B terrain only", "S1_only_ground_lt2m_above": "C S1 only, < 2 m", "S1_only_ground_ge2m_above": "C S1 only, ≥ 2 m"}
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True)
    for j, zone in enumerate(sorted(D.zone.unique())):
        g = D[D.zone == zone].set_index("category").reindex(order); y = np.arange(len(order))[::-1]
        ax = axs[j]; ax.hlines(y, g.res_p10, g.res_p90, color=FS.PALETTE["terrain"], lw=1.6); ax.plot(g.res_median, y, "o", color=FS.PALETTE["terrain"], ms=5, label="as delivered")
        if "res_corr_median" in g.columns:
            ax.hlines(y - 0.18, g.res_corr_p10, g.res_corr_p90, color=FS.PALETTE["rf"], lw=1.2); ax.plot(g.res_corr_median, y - 0.18, "D", color=FS.PALETTE["rf"], ms=3.5, label="after the residual class bias (used)")
            if j == 0:
                ax.legend(fontsize=5.5, loc="lower right")
        for yy, (k, r) in zip(y, g.iterrows()):
            nd = f", {int(r.n_dates)} dates" if "n_dates" in g.columns and np.isfinite(r.n_dates) else ""
            ax.text(2.1, yy, f"ground − surface {r.ice_minus_wse_median:+.1f} m\n{100 * r.share_ice_below_wse:.0f} % below; n = {int(r.N)}{nd}", fontsize=5.4, va="center", color=FS.PALETTE["ink2"])
        ax.set_yticks(y); ax.set_yticklabels([lab[k] for k in order], fontsize=6.5); ax.axvline(0, color=FS.PALETTE["ink2"], lw=0.8, ls=":"); ax.set_xlim(-1.7, 5.0)
        ax.set_xlabel("FABDEM-sourced terrain − ICESat-2 ground, m (median, p10–p90)", fontsize=6.5); ax.set_title(zone.replace("_", " ").title(), fontsize=7.5, loc="left"); FS.panel_label(ax, "ab"[j]); ax.tick_params(labelsize=6)
    fig.suptitle("ICESat-2 altimetric consistency check on the 2023-06-09 agreement categories (night ATL08 ground segments)", fontsize=8)
    FS.save(fig, "Fig08_icesat2_consistency", FIG)


# ---- Fig09 -----------------------------------------------------------------------------------------------------------
def fig09c_series(R, U=None):
    """The series of Fig09c, in the caption's quantities (review F15): daily-mean effective release from the pool
    Q_in - dV/dt and the DniproHES inflow Q_in (km³ per day), and the new water stored downstream (km³) -- the Monte-Carlo
    medians of the corridor and the Inhulets valley (T12b; text pass 2026-09-29: no nominal-run volumes), with the sum of their
    p05 and p95 as a conservative band."""
    dd = R[R.V_pool_km3.notna() & (R.t >= "2023-06-05")]
    U = pd.read_csv(PT / "T12b.csv") if U is None else U
    u = U[U.region.isin(["DNIPRO_CORRIDOR", "INHULETS_VALLEY_rect"])].groupby("date")[["V_p50_hm3", "V_p05_hm3", "V_p95_hm3"]].sum(min_count=2).reset_index()
    u["t"] = pd.to_datetime(u.date)
    return pd.DataFrame(dict(t=dd.t, release_km3_day=dd.Q_out_breach_est_hm3_day / 1000, inflow_km3_day=dd.Q_in_hm3_day / 1000)), \
        pd.DataFrame(dict(t=u.t, stored_km3=u.V_p50_hm3 / 1000, stored_p05_km3=u.V_p05_hm3 / 1000, stored_p95_km3=u.V_p95_hm3 / 1000))


def fig09():
    R = pd.read_csv(T / "p95f_reservoir_daily.csv"); R["t"] = pd.to_datetime(R.date); H = pd.read_csv(T / "p95f_hypsometry_dem.csv")
    lv = pd.read_csv(Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p61_pool_levels_2023.csv", parse_dates=["date"])
    lv = lv[(lv.date >= "2023-05-26") & (lv.date <= "2023-07-10")].copy()
    # the same levels as the model (p95f): Paper 1's frame for the SWOT outlet, the same quality rule (no FILLED_SUSPECT, ICE, CENSORED)
    P95F = _ld("p95f", M6 / "p95f_reservoir_balance.py"); PF = P95F.PF
    lv = lv[lv.quality.isin(P95F.GOOD_Q)].copy(); sw = lv.source == "SWOT_OUTLET"
    lv.loc[sw, "H_evrf2019"] = lv.loc[sw, "H_evrf2019"] - PF.free2mean(lv.loc[sw, "lat"]) + PF.mixed_chain_shift()
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 6.2), constrained_layout=True)
    a = axs[0, 0]
    for src, c, mk, lab in [("SWOT_OUTLET", FS.PALETTE["terrain"], "o", "SWOT outlet (0 km)"), ("NIKOPOL_UHE", FS.PALETTE["s2"], "s", "Nikopol post (160 km, press)"),
                            ("ROZUMIVKA_GAUGE", FS.PALETTE["rf"], "^", "Rozumivka gauge (248 km)"), ("ICESAT2_ATL13", FS.PALETTE["unet"], "x", "ICESat-2 passes"), ("GREALM_S6A", FS.PALETTE["muted"], "d", "G-REALM (111 km; a check, not an anchor)")]:
        q = lv[lv.source == src]; a.plot(q.date, q.H_evrf2019, mk, color=c, ms=4, label=lab, lw=0)
    a.plot(R.t, R.kherson_stage_m, color=FS.PALETTE["gauge"], lw=1.3, label="Kherson stage (downstream)"); FS.date_axis(a, BREACH, every_days=14)
    a.set_ylabel("water level, m EVRF2019 (Paper 1 frame)", fontsize=6.5); a.legend(fontsize=5.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.13), frameon=False, handletextpad=0.4, columnspacing=1.0); a.tick_params(labelsize=6); FS.panel_label(a, "a")
    b = axs[0, 1]; ok = R.V_pool_km3.notna()
    b.plot(R.t[ok], R.V_pool_km3[ok], "o-", color=FS.PALETTE["terrain"], ms=3, lw=1.5, label="pool volume under the sloped surface (DEM, km³)")
    b2 = b.twinx(); b2.plot(R.t[ok], R.A_pool_km2[ok], "s--", color=FS.PALETTE["rf"], ms=3, lw=1, label="pool water area (DEM, km²)"); b2.set_ylabel("area, km²", fontsize=6.5); b2.tick_params(labelsize=6)
    ya = pd.read_csv(Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p61_yi2025_reservoir_area.csv")
    b2.plot(pd.Timestamp("2023-06-06") + pd.to_timedelta(ya.day_after_breach, unit="D"), ya.area_km2_S1, "v", color=FS.PALETTE["s1"], ms=5,
            label="Yi et al. 2025, Sentinel-1 reservoir area\n(authors' archive, Zenodo 14639520)")             # review F15: obs.A of their main.m is Sentinel-1
    b.set_ylabel("volume, km³", fontsize=6.5); FS.date_axis(b, BREACH, every_days=7); b.tick_params(labelsize=6); h1, l1 = b.get_legend_handles_labels(); h2, l2 = b2.get_legend_handles_labels(); b.legend(h1 + h2, l1 + l2, fontsize=5.5, loc="upper center", bbox_to_anchor=(0.5, -0.13), frameon=False); FS.panel_label(b, "b")
    b.set_xlim(pd.Timestamp("2023-05-31"), pd.Timestamp("2023-06-15"))
    # review F15: the bars are the quantity the caption names -- daily-mean effective release Q_in - dV/dt (a storage balance,
    # not an instantaneous breach discharge) -- and flows (km³/day, left) and stored volume (km³, right) have separate axes
    c = axs[1, 0]; flows, stored = fig09c_series(R)
    c.bar(flows.t, flows.release_km3_day, width=0.8, color=FS.PALETTE["terrain"], label="effective release from the pool (Q_in − dV/dt)")
    c.plot(flows.t, flows.inflow_km3_day, "s-", color=FS.PALETTE["rf"], ms=3, lw=1, label="DniproHES inflow Q_in")
    c.set_ylabel("flow, km³ per day (daily mean)", fontsize=6.5); FS.date_axis(c, BREACH, every_days=7); c.tick_params(labelsize=6); FS.panel_label(c, "c")
    c2 = c.twinx(); c2.fill_between(stored.t, stored.stored_p05_km3, stored.stored_p95_km3, color=FS.PALETTE["s1"], alpha=0.18, lw=0)
    c2.plot(stored.t, stored.stored_km3, "o-", color=FS.PALETTE["s1"], ms=3, lw=1.2, label="new water stored downstream (corridor + Inhulets, MC medians)")
    c2.set_ylabel("stored downstream, km³", fontsize=6.5, color=FS.PALETTE["s1"]); c2.tick_params(labelsize=6, colors=FS.PALETTE["s1"])
    h1, l1 = c.get_legend_handles_labels(); h2, l2 = c2.get_legend_handles_labels(); c.legend(h1 + h2, l1 + l2, fontsize=5.5, loc="upper center", bbox_to_anchor=(0.5, -0.13), frameon=False)
    c.set_xlim(pd.Timestamp("2023-06-03"), pd.Timestamp("2023-06-24"))
    dax = axs[1, 1]; dax.plot(H.level_evrf2019_m, H.V_dem_km3, color=FS.PALETTE["terrain"], lw=1.6, label="seamless DEM, level surface"); dax.plot(H.level_evrf2019_m, H.V_table19_km3, color=FS.PALETTE["gauge"], lw=1.2, ls="--", label="design Table 19 (BS-77 + 0.185 m)")
    dax.set_xlabel("pool level, m", fontsize=6.5); dax.set_ylabel("volume, km³", fontsize=6.5); dax.legend(fontsize=5.5, loc="lower right"); dax.tick_params(labelsize=6); dax.grid(color=FS.PALETTE["grid"]); FS.panel_label(dax, "d")
    fig.suptitle("Reservoir drawdown and the downstream flood: levels, pool area/volume, daily balance and the hypsometry used", fontsize=8)
    FS.save(fig, "Fig09_reservoir_balance", FIG)


# ---- Supplement ------------------------------------------------------------------------------------------------------
def figS01():
    """Training curves: the v002 / v003_A history (top) and, once trained, the arms on the corrected labels v004 with three seeds
    each (bottom; the first seed solid, the others thin) -- the seed spread is the training noise (review F11)."""
    SEEDS = (20260923, 20261001, 20261002)
    v4 = [(arm, c) for arm, c in (("U0d", FS.PALETTE["rf"]), ("U2", FS.PALETTE["terrain"]), ("U2b", FS.PALETTE["unet"]), ("U1", FS.PALETTE["s2"]))
          if (RUNS / f"{arm}_B1B2_v004" / "training_history.csv").exists()]
    fig, axs = plt.subplots(2 if v4 else 1, 2, figsize=(7.2, 5.4 if v4 else 2.8), constrained_layout=True, squeeze=False)
    for run, c in [("U2_B1B2_v1", FS.PALETTE["s1"]), ("U0d_B1B2_v003A", FS.PALETTE["rf"]), ("U2_B1B2_v003A", FS.PALETTE["terrain"]), ("U2b_B1B2_v003A", FS.PALETTE["unet"])]:
        p = RUNS / run / "training_history.csv"
        if p.exists():
            h = pd.read_csv(p); axs[0, 0].plot(h.epoch, h.train_loss, color=c, lw=1.5, label=run); axs[0, 1].plot(h.epoch, h.val_patch_F1_at_0p5, color=c, lw=1.5, label=run)
    for arm, c in v4:
        for k, sd in enumerate(SEEDS):
            p = RUNS / (f"{arm}_B1B2_v004" + ("" if k == 0 else f"_s{sd}")) / "training_history.csv"
            if p.exists():
                h = pd.read_csv(p); kw = dict(color=c, lw=1.5 if k == 0 else 0.7, alpha=1.0 if k == 0 else 0.6, label=f"{arm} v004" if k == 0 else None)
                axs[1, 0].plot(h.epoch, h.train_loss, **kw); axs[1, 1].plot(h.epoch, h.val_patch_F1_at_0p5, **kw)
    for r, what in enumerate(["v002 / v003_A (original M2)"] + (["v004 (corrected M2), three seeds per arm"] if v4 else [])):
        axs[r, 0].set_title(f"train loss (masked BCE + Dice) -- {what}", fontsize=7.5, loc="left"); axs[r, 1].set_title(f"validation patch F1 @ 0.5 (weak labels) -- {what}", fontsize=7.5, loc="left")
        for ax in axs[r]:
            ax.set_xlabel("epoch", fontsize=7); ax.grid(color=FS.PALETTE["grid"]); ax.tick_params(labelsize=6.5)
        axs[r, 0].legend(fontsize=6)
    FS.save(fig, "FigS01_training_curves", FIG)

def figS02():
    fig, ax = plt.subplots(figsize=(7.2, 3.2), constrained_layout=True)
    for sfx, lab, c, ls in [("_connected_ceiling", "connected ceiling, river-network seed, residual terrain bias removed (primary)", FS.PALETTE["terrain"], "-"), ("_hand_and_ceiling", "p42 HAND rule", FS.PALETTE["terrain"], "--"), ("_ceiling_only", "ceiling only", FS.PALETTE["terrain"], ":"),
                            ("_connected_ceiling_dem_uncorrected", "connected ceiling, terrain as delivered (reed beds count as new)", FS.PALETTE["s2"], "-"),
                            ("_connected_ceiling_conn4", "4-connectivity", FS.PALETTE["unet"], ":"),
                            ("_connected_ceiling_seed_allprewater", "superseded seeding from every pre-breach water cell (ponds, canals)", FS.PALETTE["unet"], "--"),
                            ("_connected_ceiling_memory", "retained water (D-MEMORY sensitivity)", FS.PALETTE["s1"], "--"),
                            ("_connected_ceiling_maxgap3", "nodes unavailable beyond a 3-day gap", FS.PALETTE["rf"], ":"), ("_connected_ceiling_riveraware", "river-aware water surface", FS.PALETTE["rf"], "--"),
                            ("_connected_ceiling_fallback10km", "no water surface from nodes > 10 km away (Kherson cap kept)", FS.PALETTE["gauge"], "-."),
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
    rv = int(m.rev.max()) if "rev" in m.columns else 1; m = m[m.rev == rv] if "rev" in m.columns else m     # the RF20 in use (rev 2 after review F08)
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.2), constrained_layout=True, gridspec_kw=dict(width_ratios=[1.1, 1]))
    C = cm.values.astype(float); Cn = C / C.sum(1, keepdims=True)
    a.imshow(Cn, cmap=FS.SEQ_SCORE, vmin=0, vmax=1); a.set_xticks(range(len(cm.columns))); a.set_xticklabels(cm.columns, rotation=60, ha="right", fontsize=5.5); a.set_yticks(range(len(cm.index))); a.set_yticklabels(cm.index, fontsize=5.5)
    for i in range(C.shape[0]):
        for j in range(C.shape[1]):
            a.text(j, i, f"{Cn[i, j]:.2f}", ha="center", va="center", fontsize=5, color="white" if Cn[i, j] > 0.5 else FS.PALETTE["ink"])
    a.set_xlabel("predicted (RF20)", fontsize=7); a.set_ylabel("reference (WorldCover 2021)", fontsize=7); a.set_title(f"row-normalised confusion, spatial-block CV (rev {rv})", fontsize=7.5, loc="left"); FS.panel_label(a, "a", x=-0.35)
    mm = m[~m.cls.isin(["MACRO_MEAN", "OVERALL_ACCURACY"])]; ev = list(mm.evaluation.unique()); w = 0.8 / len(ev); cls = list(mm[mm.evaluation == ev[0]].cls)
    for k, e in enumerate(ev):
        g = mm[mm.evaluation == e].set_index("cls").reindex(cls)
        b.bar(np.arange(len(cls)) + k * w, g.F1, w, label=e.replace("spatial_block_cv_5fold", "block CV").replace("_buffered", ", 3.5 km buffer").replace("transfer_", "transfer "),
              color=[FS.PALETTE["rf"], FS.PALETTE["gauge"], FS.PALETTE["terrain"], FS.PALETTE["s2"]][k % 4])
    b.set_xticks(np.arange(len(cls)) + 0.4 - w / 2); b.set_xticklabels(cls, rotation=60, ha="right", fontsize=5.5); b.set_ylabel("F1 vs WorldCover", fontsize=7); b.legend(fontsize=5.5); b.tick_params(labelsize=6); FS.panel_label(b, "b", x=-0.2)
    FS.save(fig, "FigS04_rf20_agreement", FIG)


def figS05():
    d = pd.read_csv(PT / "T20.csv"); d = d[d.status.str.contains("trained")]
    if len(d) == 0:
        return
    if "labels" not in d.columns:
        d["labels"] = "v003_A"
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.6), constrained_layout=True)
    style = {"v003_A": (FS.PALETTE["muted"], -0.25, "v003_A (original M2)"), "v004": (FS.PALETTE["unet"], 0.25, "v004 (corrected M2)")}
    for ax, k, lab in zip(axs, ["G_F1", "A_FP_area_dry_cropland_km2", "B_recall_flooded_open_low_veg"], ["global F1 (weak labels)", "dry-cropland FP, km²", "recall, flooded open low veg."]):
        for lv, g in d.groupby("labels"):
            c, dx, name = style.get(lv, (FS.PALETTE["ink2"], 0.0, lv))
            ax.errorbar(g.block_km + dx, g[k], yerr=[g[k] - g[f"{k}_lo"], g[f"{k}_hi"] - g[k]], fmt="o", color=c, capsize=3, label=name)
        ax.set_xlabel("block size, km", fontsize=7); ax.set_title(lab, fontsize=7.5, loc="left"); ax.tick_params(labelsize=6.5); ax.grid(color=FS.PALETTE["grid"])
    axs[0].legend(fontsize=6, frameon=False)
    fig.suptitle("Block-size sensitivity (U2): each split has its own TEST geography; values and intervals only", fontsize=7.5); FS.save(fig, "FigS05_block_sensitivity", FIG)

def figS06():
    """Inhulets valley profile: mapped U2b new flood (v004, the three training seeds; review D-SEEDS) and the v004 EVENT_FLOOD label."""
    P = pd.read_csv(T / "p92_inhulets_profile.csv")
    fig, ax = plt.subplots(figsize=(4.5, 2.8), constrained_layout=True)
    for k, run in enumerate(("U2b_B1B2_v004", "U2b_B1B2_v004_s20261001", "U2b_B1B2_v004_s20261002")):
        p = P[P.run == run]
        if len(p):
            ax.plot(p.northing_km, p.predicted_new_on_land_km2, "o-", color=FS.PALETTE["unet"], ms=3 if k == 0 else 2, lw=1 if k == 0 else 0.6, alpha=1 if k == 0 else 0.6,
                    label="U2b (v004) mapped new flood on land, three seeds" if k == 0 else None)
    lab = P[P.run == "U2b_B1B2_v004"]
    ax.plot(lab.northing_km, lab.EVENT_FLOOD_label_km2, "s-", color=FS.PALETTE["s1"], ms=3, lw=1, label="EVENT_FLOOD label (v004)")
    ax.set_xlabel("northing, km (2-km bands up the Inhulets valley)", fontsize=7); ax.set_ylabel("km² per band", fontsize=7); ax.legend(fontsize=6); ax.tick_params(labelsize=6.5)
    FS.save(fig, "FigS06_inhulets_profile", FIG)

def figS07():
    """Hypsometry sensitivity: V_DEM(H) vs V_design(H) and dV/V_design (T22) -- the basis of the released volume in T21."""
    H = pd.read_csv(PT / "T22.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True)
    a.plot(H.level_evrf2019_m, H.V_dem_km3, color=FS.PALETTE["terrain"], lw=1.8, label="seamless DEM, level surface")
    a.plot(H.level_evrf2019_m, H.V_table19_km3, color=FS.PALETTE["ink2"], lw=1.5, ls="--", label="design Table 19 (BS-77 + 0.185 m)")
    a.set_xlabel("pool level, m (EVRF2019)", fontsize=7); a.set_ylabel("volume, km³", fontsize=7); a.legend(fontsize=6); a.tick_params(labelsize=6.5); a.grid(color=FS.PALETTE["grid"]); FS.panel_label(a, "a")
    lo = 10.0 + float((H.level_evrf2019_m - H.level_bs77_m).median())                # review F13: the design table starts at 10 m BS (= 10.185 m EVRF2019)
    a.axvspan(float(H.level_evrf2019_m.min()), lo, color=FS.PALETTE["grid"], alpha=0.6, lw=0); a.text(lo - 0.2, float(np.nanmax(H.V_dem_km3)) * 0.92, "design table\nundefined\n(< 10 m BS)", ha="right", va="top", fontsize=5.5, color=FS.PALETTE["ink2"])
    ok = np.isfinite(H.V_table19_km3)
    b.plot(H.level_evrf2019_m[ok], H.dV_rel_pct[ok], color=FS.PALETTE["terrain"], lw=1.8, label="ΔV / V_design")
    b.plot(H.level_evrf2019_m[ok], H.dA_rel_pct[ok], color=FS.PALETTE["s1"], lw=1.4, ls=":", label="ΔA / A_design")
    b.axhline(0, color=FS.PALETTE["ink2"], lw=0.6); b.axvspan(5.6, 17.6, color=FS.PALETTE["gauge"], alpha=0.07, lw=0)
    b.set_xlabel("pool level, m (EVRF2019)", fontsize=7); b.set_ylabel("DEM − design, % of design", fontsize=7); b.legend(fontsize=6); b.tick_params(labelsize=6.5); b.grid(color=FS.PALETTE["grid"]); FS.panel_label(b, "b")
    fig.suptitle("Reservoir hypsometry: seamless DEM vs design table (shaded: drawdown range 5–13 June); open question for Paper 4 (historical bathymetry)", fontsize=7)
    FS.save(fig, "FigS07_hypsometry_sensitivity", FIG)


# ---- FigS10: the DESIGN level-area-volume curves (monograph Table 19 / Figs 13-15) and the observed levels on them (p95i) ------
def figS10():
    """Design hypsometry of the Kakhovka reservoir (Table 19: pool and five reaches; design levels) and the observed 2023 levels
    read on it: design volume at the outlet and at the Rozumivka level (sloped surface -> a range). No DEM, no soundings."""
    D = pd.read_csv(T / "p95i_design_hypsometry.csv").sort_values("level_bs_m"); Q = pd.read_csv(T / "p95i_design_daily.csv"); Q["t"] = pd.to_datetime(Q.date)
    dl = D[D.design_level.fillna("") != ""]; reach = ["#0b2a5c", "#2a78d6", "#7fb3e6", "#b9d1ee", "#dbe9f8"]
    names = ["dam – Babyne", "Babyne – Nikopol", "Nikopol – V. Tarasivka", "V. Tarasivka – Blahovishchenka", "Blahovishchenka – Dnipro HPP"]
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.4, 3.4), constrained_layout=True)
    for ax in (a, b):
        for _, q in dl.iterrows():
            ax.axhline(q.level_bs_m, color="#c3c2b7", lw=0.7, ls=":", zorder=0)
            ax.text(0.99, q.level_bs_m, q.design_level.split(" - ")[0] + " ", transform=ax.get_yaxis_transform(), fontsize=5.2, va="bottom", ha="right", color=FS.PALETTE["ink2"])
    Dr = D.dropna(subset=["V_reach1_km3"]); base = np.zeros(len(Dr))
    for k in range(1, 6):
        v = Dr[f"V_reach{k}_km3"].values; a.fill_betweenx(Dr.level_bs_m, base, base + v, color=reach[k - 1], lw=0, label=f"reach {k}: {names[k - 1]}"); base = base + v
    a.plot(D.V_km3, D.level_bs_m, "o-", color=FS.PALETTE["ink"], ms=2.8, lw=1.4, label="whole pool, Table 19")
    a.set_xlabel("volume, km³", fontsize=7); a.set_ylabel("water level, m (historical Baltic)", fontsize=7); a.legend(fontsize=4.8, loc="upper left", bbox_to_anchor=(0.06, 0.985)); FS.panel_label(a, "a")
    b.plot(D.A_km2, D.level_bs_m, "o-", color=FS.PALETTE["ink"], ms=2.8, lw=1.4, label="surface area, Table 19")
    pre = Q[Q.phase == "pre-breach"]; dd = Q[(Q.phase == "drawdown") & Q.design_defined]
    b.plot(pre.A_design_at_outlet_km2, pre.outlet_level_bs_m, "s", color=FS.PALETTE["s2"], ms=3, mfc="white", label="observed outlet level before the breach (26 May – 5 June)")
    b.plot(dd.A_design_at_outlet_km2, dd.outlet_level_bs_m, "s-", color=FS.PALETTE["s2"], ms=3, lw=0.8, label="observed outlet level 6–13 June, read on the curve")
    b.set_xlabel("area, km²", fontsize=7); b.legend(fontsize=5, loc="upper left", bbox_to_anchor=(0.06, 0.985)); FS.panel_label(b, "b")
    a2 = a.twinx(); a2.set_ylim(np.array(a.get_ylim()) + 0.185); a2.set_ylabel("m EVRF2019 (+0.185 m)", fontsize=6.5); a2.tick_params(labelsize=6)
    qq = Q[Q.t <= "2023-06-20"]; pb = qq[qq.phase == "pre-breach"]; db = qq[qq.phase != "pre-breach"]
    c.plot(pb.t, pb.V_design_at_rozumivka_km3, "-", color=FS.PALETTE["ink"], lw=1.4, label="at the Rozumivka level (level pool), Feb – 5 Jun")
    c.fill_between(db.t, db.V_design_at_outlet_km3, db.V_design_at_rozumivka_km3, color=FS.PALETTE["s2"], alpha=0.25, lw=0, label="after the breach: outlet … Rozumivka (sloped)")
    c.plot(db.t, db.V_design_at_outlet_km3, "s-", color=FS.PALETTE["s2"], ms=2.5, lw=1.0, label="at the outlet level (SWOT)")
    c.plot(db.t, db.V_design_at_rozumivka_km3, "^-", color=FS.PALETTE["rf"], ms=2.5, lw=0.8, label="at the Rozumivka level")
    c3 = c.twinx(); c3.fill_between(qq.t, 0, qq.Q_in_dniprohes_m3s / 1000, color=FS.PALETTE["terrain"], alpha=0.15, lw=0, label="DniproHES release (right axis)"); c3.set_ylim(0, 24); c3.set_ylabel("DniproHES release, 10³ m³/s", fontsize=6.5); c3.tick_params(labelsize=6)
    und = qq[~qq.design_defined & (qq.phase != "pre-breach")]
    if len(und):
        c.axvspan(und.t.min(), qq.t.max(), color=FS.PALETTE["grid"], alpha=0.8, lw=0); c.text(und.t.min(), 8.9, " outlet\n below\n 10 m", fontsize=5, va="top", color=FS.PALETTE["ink2"])
    for _, q in dl.iterrows():
        c.axhline(D.set_index("level_bs_m").loc[q.level_bs_m, "V_km3"], color="#c3c2b7", lw=0.6, ls=":"); c.text(qq.t.max(), D.set_index("level_bs_m").loc[q.level_bs_m, "V_km3"], q.design_level.split(" - ")[0], fontsize=5, va="bottom", ha="right", color=FS.PALETTE["ink2"])
    import matplotlib.dates as mdates
    FS.date_axis(c, BREACH, every_days=30); c.xaxis.set_major_locator(mdates.MonthLocator()); c.xaxis.set_major_formatter(mdates.DateFormatter("%b")); c.set_xlim(pd.Timestamp("2023-02-01"), pd.Timestamp("2023-06-20"))
    c.set_ylabel("volume from the design curve, km³", fontsize=7); c.set_ylim(6, 23.2)
    h1, l1 = c.get_legend_handles_labels(); h2, l2 = c3.get_legend_handles_labels(); c.legend(h1 + h2, l1 + l2, fontsize=4.8, loc="upper left", bbox_to_anchor=(0.0, 0.43), title="design volume read", title_fontsize=5); c.tick_params(labelsize=6); FS.panel_label(c, "c", x=0.02, y=0.99)
    for ax in (a, b):
        ax.tick_params(labelsize=6); ax.grid(color=FS.PALETTE["grid"], lw=0.5)
    fig.suptitle("Kakhovka reservoir design hypsometry (monograph Table 19 / Figs 13–15) and the observed 2023 levels read on it — no DEM, nothing fitted", fontsize=7)
    FS.save(fig, "FigS10_reservoir_design_hypsometry", FIG)


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


def fig11():
    """The emptying of the Kakhovka reservoir as the observations show it (maintainer, 2026-09-30: the drawdown maps are mandatory
    and must show the drawdown): Sentinel-2 water on 5, 8, 13 and 20 June (not observed is not dry), the day on which the bed fell
    dry (the model for 6-13 June, Sentinel-2 on 20 June after that; S2 water overrides the model), the Sentinel-2 bed classes on
    5 July and 8 September, and the pool water area over time from every source as a share of the pool."""
    import matplotlib.dates as mdates
    from rasterio import features
    ctx = _res_ctx(); H, pool, zone, ext, hs, read = ctx
    R = pd.read_csv(T / "p95h_reservoir_maps.csv"); RM = BULK / "reservoir_maps"
    man = json.loads((T / "p95h_manifest.json").read_text()); pool_km2 = float(man["pool_km2_s2_grid"])
    fig = plt.figure(figsize=(7.4, 5.3), constrained_layout=True)
    gs = fig.add_gridspec(3, 5, width_ratios=[1, 1, 1, 1, 0.95], height_ratios=[1, 1, 0.78])
    ax = [[fig.add_subplot(gs[r, c]) for c in range(5)] for r in range(2)]
    km = lambda tr, shp: [tr.c / 1e3, (tr.c + tr.a * shp[1]) / 1e3, (tr.f + tr.e * shp[0]) / 1e3, tr.f / 1e3]
    wc = ["#1b6ca8", "#efece6", "#c3c2b7"]                                              # water / observed, not water / not observed
    ztr, zshp = H.s2_grid(); xtr = H.xc_transform(ztr)
    zin = features.rasterize([(zone.__geo_interface__, 1)], out_shape=zshp, transform=xtr, fill=0, dtype="uint8").astype(bool)
    # (a) 5 June: the p25 water3 product (the pool full, the day before the breach)
    w3, w3ext = read(H.S2DIR / "2023-06-05_water3.tif", fill=254)
    c = np.zeros(w3.shape, "u1"); c[w3 == 1] = 1; c[w3 == 0] = 2; c[w3 == 255] = 3
    r = R[(R.source == "S2_WATER3") & (R.date == "2023-06-05")].iloc[0]
    _res_panel(ax[0][0], ctx, c, w3ext, wc, f"(a) S2 water 06-05\n{r.water_km2:.0f} km² ({r.observed_frac:.0%} observed)\nthe day before the breach", first=True)
    # (b-d) the p15 crosscheck water of the drawdown: 8 and 13 June partly observed, 20 June the whole pool
    for j, d in enumerate(["2023-06-08", "2023-06-13", "2023-06-20"], 1):
        z2 = np.load(H.S2XC / f"{d}.npz"); u2 = lambda k: np.unpackbits(z2[k], count=zshp[0] * zshp[1]).reshape(zshp).astype(bool)
        w, v = u2("water"), u2("valid"); c = np.zeros(zshp, "u1"); c[v & ~w] = 2; c[w & v] = 1; c[~v] = 3; c[~zin] = 0
        r = R[(R.source == "S2_CROSSCHECK") & (R.date == d)].iloc[0]
        iou = f"\nIoU with the model {r.iou_vs_model:.2f}" if np.isfinite(r.get("iou_vs_model", np.nan)) else "\nthe model ends 06-13"
        _res_panel(ax[0][j], ctx, c[::3, ::3], km(xtr, zshp), wc, f"({'bcd'[j - 1]}) S2 water {d[5:]}\n{r.water_km2:.0f} km² ({r.observed_frac:.0%} observed){iou}")
    _leg(ax[0][4], wc, ["water", "observed, not water", "not observed (≠ dry)"], "Sentinel-2 water\n(a: p25 water3,\nb–d: p15 crosscheck)", loc="center left", y=0.5)
    # (e) the day the bed fell dry: the model for 6-13 June, Sentinel-2 on 20 June after that (S2 water overrides the model)
    e, eext = read(RM / "exposed_day_observed.tif")
    c = np.zeros(e.shape, "u1")
    for k, (lo, hi) in enumerate([(6, 7), (8, 9), (10, 11), (12, 13)], 1):
        c[(e >= lo) & (e <= hi)] = k
    c[e == 20] = 5; c[e == 254] = 6; c[e == 253] = 7
    ec = ["#7d1d1d", "#c7522a", "#e08214", "#f2c14e", "#bfa76f", "#1b6ca8", "#c3c2b7"]
    X = pd.read_csv(T / "p95h_exposure_observed.csv").set_index("code").km2
    _res_panel(ax[1][0], ctx, c, eext, ec, f"(e) day the bed fell dry\n{X.loc[6:13].sum():.0f} km² by 06-13 (model)\n+{X.get(20, np.nan):.0f} km² by 06-20 (S2)")
    # (f, g) Sentinel-2 bed classes after the drawdown
    for j, d in enumerate(["2023-07-05", "2023-09-08"], 1):
        cl, cext = read(H.S2DIR / f"{d}_class.tif")
        r = R[(R.source == "S2_WATER3") & (R.date == d)].iloc[0]
        _res_panel(ax[1][j], ctx, cl, cext, [H.K10E[k][1] for k in range(1, 10)], f"({'fg'[j - 1]}) S2 bed classes\n{d[5:]} ({r.observed_frac:.0%} observed)")
    _leg(ax[1][3], [H.K10E[k][1] for k in range(1, 10)], [H.K10E[k][0].replace("_", " ").lower() for k in range(1, 10)], "Sentinel-2 bed classes\n(f, g; p25 k10e)", loc="center left", y=0.5)
    _leg(ax[1][4], ec, ["06-06–07 (model)", "06-08–09 (model)", "06-10–11 (model)", "06-12–13 (model)", "by 06-20 (Sentinel-2)", "water on 06-20\n(Sentinel-2)", "not observed 06-20"],
         "day the bed fell dry (e)", loc="center left", y=0.5)
    # (h) pool water area over time, % of the pre-breach pool (whole-pool areas) or of the observed part (partly observed S2 dates)
    h = fig.add_subplot(gs[2, 0:4]); hl = fig.add_subplot(gs[2, 4]); hl.axis("off")
    M = R[R.source == "MODEL"].copy(); M["t"] = pd.to_datetime(M.date)
    ub = set(pd.read_csv(T / "p95f_reservoir_daily.csv").query("surface_upper_bound == True").date)
    h.plot(M.t, M.water_km2 / pool_km2 * 100, "-", color=FS.PALETTE["terrain"], lw=1.3, label="model (p95f sloped surface), 26 May – 13 June")
    mu = M[M.date.isin(ub)]; h.plot(mu.t, mu.water_km2 / pool_km2 * 100, "o", mfc="white", color=FS.PALETTE["terrain"], ms=3.5, label="model, upper estimate (Nikopol bound)")
    S = R[R.source.isin(["S2_WATER3", "S2_CROSSCHECK"])].copy(); S["t"] = pd.to_datetime(S.date); S["pct"] = S.water_km2 / (S.observed_frac * pool_km2) * 100
    full = S[(S.observed_frac >= 0.9) & (S.t >= "2023-06-01") & (S.t <= "2023-09-30")]
    part = S[(S.source == "S2_CROSSCHECK") & (S.observed_frac < 0.9) & (S.observed_frac >= 0.05)]
    h.plot(full.t, full.pct, "s", color=FS.PALETTE["s2"], ms=4, label="Sentinel-2, pool observed (≥ 90 %)")
    h.plot(part.t, part.pct, "s", mfc="white", color=FS.PALETTE["s2"], ms=4, label="Sentinel-2, water share of the observed part")
    Y = R.dropna(subset=["yi2025_S1_archive_km2"]).drop_duplicates("date").copy(); Y["t"] = pd.to_datetime(Y.date)
    h.plot(Y.t, Y.yi2025_S1_archive_km2 / pool_km2 * 100, "v", color=FS.PALETTE["s1"], ms=4, label="Yi et al. 2025, Sentinel-1 (authors' archive)")
    h.axvline(BREACH, color=FS.PALETTE["ink2"], lw=0.7, ls=":"); h.text(BREACH, 3, " breach", fontsize=5.5, color=FS.PALETTE["ink2"])
    h.set_ylim(0, 105); h.set_ylabel("water, % of the pool", fontsize=6.5); h.tick_params(labelsize=6)
    h.set_xlim(pd.Timestamp("2023-05-25"), pd.Timestamp("2023-09-15")); h.xaxis.set_major_locator(mdates.MonthLocator()); h.xaxis.set_minor_locator(mdates.DayLocator(bymonthday=[10, 20]))
    h.xaxis.set_major_formatter(mdates.DateFormatter("%b")); h.grid(color=FS.PALETTE["grid"])
    h.set_title("(h) pool water area over time", fontsize=6.3, loc="left")
    hh, ll = h.get_legend_handles_labels(); hl.legend(hh, ll, fontsize=5.3, loc="center left", frameon=False, handletextpad=0.4)
    fig.suptitle("The emptying of the Kakhovka reservoir: Sentinel-2 water, the day the bed fell dry and the bed afterwards (not observed is not dry)", fontsize=7)
    FS.save(fig, "Fig11_reservoir_drawdown", FIG)

def figS08():
    """The modelled pool extent (p95f surface; an upper estimate on 12-13 June) with its day of exposure within 6-13 June, and the
    Sentinel-1 VH dark surface -- open water OR smooth wet mud, so after ~13 June not a water area (Fig11 shows the drawdown)."""
    from affine import Affine
    import rasterio
    ctx = _res_ctx(); H, pool, zone, ext, hs, read = ctx
    R = pd.read_csv(T / "p95h_reservoir_maps.csv"); RM = BULK / "reservoir_maps"
    fig, axs = plt.subplots(2, 5, figsize=(7.4, 3.5), constrained_layout=True, gridspec_kw=dict(width_ratios=[1, 1, 1, 1, 0.78])); lab = iter("abcdefgh")
    km = lambda tr, shp: [tr.c / 1e3, (tr.c + tr.a * shp[1]) / 1e3, (tr.f + tr.e * shp[0]) / 1e3, tr.f / 1e3]
    z = np.load(RM / "model" / "wet_daily.npz"); shp = tuple(int(v) for v in z["shape"]); mtr = Affine(*z["transform"])
    un = lambda k: np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
    ref = un("2023-06-05"); mc = ["#1b6ca8", "#d9a441"]
    for j, d in enumerate(["2023-06-07", "2023-06-09", "2023-06-13"]):
        w = un(d); c = np.zeros(shp, "u1"); c[w] = 1; c[ref & ~w] = 2
        a = R[(R.source == "MODEL") & (R.date == d)].water_km2.iloc[0]
        _res_panel(axs[0, j], ctx, c, km(mtr, shp), mc, f"({next(lab)}) model {d[5:]}\n{a:.0f} km² water" + (" (upper est.)" if d == "2023-06-13" else ""), first=(j == 0))
    with rasterio.open(RM / "model" / "exposed_day.tif") as s:
        e = s.read(1); etr = s.transform
    c = np.zeros(e.shape, "u1")
    for k, (lo, hi) in enumerate([(6, 6), (7, 7), (8, 8), (9, 10), (11, 13)], 1):
        c[(e >= lo) & (e <= hi)] = k
    c[e == 255] = 6; ec = ["#7d1d1d", "#c7522a", "#e08214", "#eda100", "#f2d98a", "#1b6ca8"]
    _res_panel(axs[0, 3], ctx, c, km(etr, e.shape), ec, f"({next(lab)}) model: bed dry by\n06-13 (Fig11e after)")
    _leg(axs[0, 4], mc, ["pool water", "bed exposed since 06-05"], "model (p95f surface)", loc="upper left", y=1.0)
    _leg(axs[0, 4], ec, ["06-06", "06-07", "06-08", "06-09–10", "06-11–13", "wet on 06-13"], "day of exposure", loc="lower left", y=0.0)
    sc = ["#1b6ca8", "#d9a441", "#c3c2b7"]
    for j, d in enumerate(["2023-06-01", "2023-06-08", "2023-06-13", "2023-06-21"]):
        z1 = np.load(RM / "s1" / f"{d}.npz"); sshp = tuple(int(v) for v in z1["shape"]); s_tr = Affine(*z1["transform"])
        u1 = lambda k: np.unpackbits(z1[k], count=sshp[0] * sshp[1]).reshape(sshp).astype(bool)
        if j == 0:
            d0 = u1("water"); spool = H.pool_on(s_tr, sshp)
        w, o = u1("water"), u1("observed"); c = np.zeros(sshp, "u1"); c[w & spool] = 1; c[o & ~w & d0 & spool] = 2; c[spool & ~o] = 3
        r = R[(R.source == "S1") & (R.date == d)].iloc[0]
        iou = f", IoU {r.iou_vs_model:.2f}" if np.isfinite(r.get("iou_vs_model", np.nan)) else ", no model"
        _res_panel(axs[1, j], ctx, c[::2, ::2], km(s_tr, sshp), sc, f"({next(lab)}) S1 {d[5:]}\n{r.water_km2:.0f} km² dark{iou}")
    _leg(axs[1, 4], sc, ["VH dark: open water\nor smooth wet mud", "dark on 06-01, not now", "pool not observed"], "Sentinel-1 (VH, Otsu)")
    fig.suptitle("Kakhovka pool: the modelled water extent (terrain-reconstructed) and the Sentinel-1 VH dark surface, which after ~13 June is wet mud as well as water", fontsize=6.6)
    FS.save(fig, "FigS08_reservoir_model_and_s1", FIG)

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


def figS11():
    """The terrain-error model (p95j): FABDEM - ICESat-2 residual semivariograms per class and the standardized pooled fit used by p95e."""
    V = pd.read_csv(T / "p95j_terrain_residual_variogram.csv"); F = pd.read_csv(T / "p95j_terrain_variogram_fit.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True)
    cols = {"cropland": FS.PALETTE["s2"], "grass": FS.PALETTE["rf"], "wetland": FS.PALETTE["terrain"], "trees": FS.PALETTE["unet"], "built": FS.PALETTE["s1"]}
    hh = np.linspace(1, 3000, 300)
    for nm, c in cols.items():
        v = V[(V.zone == "POOLED") & (V.wc_class == nm) & (V.n_pairs >= 200)]; f = F[(F.zone == "POOLED") & (F.wc_class == nm) & (F.estimator == "classical") & (F.model == "exponential+nugget")]
        a.plot(v.lag_mid_m, v.gamma_m2, "o", ms=2.8, color=c, label=nm)
        if len(f) and f.status.iloc[0] == "ok":
            a.plot(hh, f.c0.iloc[0] + f.s2.iloc[0] * (1 - np.exp(-hh / f.L_m.iloc[0])), "-", lw=0.9, color=c)
    a.set_xscale("log"); a.set_xlabel("lag, m", fontsize=6.5); a.set_ylabel("semivariance, m²", fontsize=6.5); a.legend(fontsize=5.5); a.tick_params(labelsize=6); a.grid(color=FS.PALETTE["grid"]); FS.panel_label(a, "a")
    a.set_title("FABDEM − ICESat-2 residual after the class median (pooled)", fontsize=7, loc="left")
    v = V[(V.zone == "POOLED") & (V.wc_class == "all_standardized") & (V.n_pairs >= 200)]
    b.plot(v.lag_mid_m, v.gamma_robust, "o", ms=3, color=FS.PALETTE["ink"], label="robust (Cressie–Hawkins)"); b.plot(v.lag_mid_m, v.gamma_m2, "x", ms=3, color=FS.PALETTE["muted"], label="classical")
    fn = F[(F.zone == "POOLED") & (F.wc_class == "all_standardized") & (F.estimator == "cressie_hawkins") & (F.model == "nested_2exp+nugget")]
    fs = F[(F.zone == "POOLED") & (F.wc_class == "all_standardized") & (F.estimator == "cressie_hawkins") & (F.model == "exponential+nugget")]
    if len(fn):
        q = fn.iloc[0]; b.plot(hh, q.c0 + q.s1 * (1 - np.exp(-hh / q.L1_m)) + q.s2 * (1 - np.exp(-hh / q.L2_m)), "-", color=FS.PALETTE["terrain"], lw=1.4,
                               label=f"nested: nugget {q.nugget_share:.2f}, {q.L1_m:.0f} m + {q.L2_m:.0f} m (used)")
    if len(fs):
        q = fs.iloc[0]; b.plot(hh, q.c0 + q.s2 * (1 - np.exp(-hh / q.L_m)), ":", color=FS.PALETTE["s1"], lw=1.1, label=f"single exponential: nugget {q.nugget_share:.2f}, {q.L_m:.0f} m")
    b.axhline(1.0, color=FS.PALETTE["ink2"], lw=0.5, ls=":"); b.set_xscale("log"); b.set_xlabel("lag, m", fontsize=6.5); b.set_ylabel("semivariance of (r − b_c) / σ_c", fontsize=6.5)
    b.legend(fontsize=5.3); b.tick_params(labelsize=6); b.grid(color=FS.PALETTE["grid"]); FS.panel_label(b, "b"); b.set_title("standardized residual: the correlation model of the terrain field", fontsize=7, loc="left")
    FS.save(fig, "FigS11_terrain_error_variogram", FIG)


def figS12():
    """Convergence of the Monte-Carlo quantiles with the ensemble size (T11c)."""
    C = pd.read_csv(T / "p95e_convergence.csv")
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.6), constrained_layout=True, sharex=True)
    for ax, (q, lab) in zip(axs, (("A", "newly inundated area, km²"), ("W_total", "total water-surface area, km²"), ("V", "new-water volume, hm³"))):
        for (seed, d), g in C[C.date == "2023-06-07"].groupby(["seed", "date"]):
            g = g.sort_values("n_draws"); ls = "-" if seed == C.seed.min() else "--"
            for p_, c in (("p05", FS.PALETTE["terrain"]), ("p50", FS.PALETTE["ink"]), ("p95", FS.PALETTE["terrain"])):
                ax.plot(g.n_draws, g[f"{q}_{p_}"], ls, color=c, lw=1.1, marker="o", ms=2.5)
                ax.fill_between(g.n_draws, g[f"{q}_{p_}_boot_lo"], g[f"{q}_{p_}_boot_hi"], color=c, alpha=0.08, lw=0)
        ax.set_xscale("log"); ax.set_xlabel("ensemble size n", fontsize=6.5); ax.set_title(lab + ", 7 June", fontsize=6.8, loc="left"); ax.tick_params(labelsize=6); ax.grid(color=FS.PALETTE["grid"])
    fig.suptitle("Monte-Carlo quantiles p05 / p50 / p95 against the ensemble size (two seeds: solid / dashed; shaded: bootstrap 95 % of the quantile estimator)", fontsize=7)
    FS.save(fig, "FigS12_mc_convergence", FIG)


def figS13():
    """Sensitivity of the connected reconstruction to a uniform water-surface offset (T11e)."""
    S = pd.read_csv(T / "p95e_wse_threshold_sensitivity.csv"); S = S[S.region == "DNIPRO_CORRIDOR"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.8), constrained_layout=True)
    for d, c in (("2023-06-07", FS.PALETTE["terrain"]), ("2023-06-09", FS.PALETTE["s1"]), ("2023-06-13", FS.PALETTE["unet"])):
        g = S[S.date == d].sort_values("delta_m")
        a.plot(g.delta_m, g.A_new_km2, "o-", color=c, ms=3, lw=1.2, label=d); b.plot(g.delta_m, g.dA_dH_km2_per_m, "o-", color=c, ms=3, lw=1.2, label=d)
    a.set_xlabel("water-surface offset δ, m", fontsize=6.5); a.set_ylabel("newly inundated area, km² (corridor)", fontsize=6.5); a.legend(fontsize=6); FS.panel_label(a, "a")
    b.set_xlabel("water-surface offset δ, m", fontsize=6.5); b.set_ylabel("dA/dH, km² per m", fontsize=6.5); FS.panel_label(b, "b")
    for ax in (a, b):
        ax.axvline(0, color=FS.PALETTE["ink2"], lw=0.5, ls=":"); ax.tick_params(labelsize=6); ax.grid(color=FS.PALETTE["grid"])
    fig.suptitle("Connectivity thresholds: the reconstructed area under a uniform water-surface offset on the nominal terrain (a sensitivity, not a model)", fontsize=7)
    FS.save(fig, "FigS13_wse_threshold_sensitivity", FIG)


SUPPORT_COLOURS = {1: ("direct (nearest SWOT node ≤ 3 km)", "#0b2a5c"), 2: ("extrapolated (3–10 km)", "#5a93da"), 3: ("weak (> 10 km)", "#eda100"),
                   4: ("cross-river (Inhulets valley, node of another river)", "#e34948"), 5: ("capped at the Kherson gauge", "#4a3aa7")}
GAUGES = {"Kherson 80805\n(input, anchor)": (32.612026, 46.623750, "s", FS.PALETTE["ink"], FS.PALETTE["ink"], (-6, 10), "right"),
          "Kalynivske 80575\n(withheld)": (32 + 57 / 60 + 38 / 3600, 47 + 6 / 60 + 59 / 3600, "^", "white", FS.PALETTE["ink"], (7, -3), "left"),
          "Mykolaiv 98027\n(withheld)": (31 + 58 / 60 + 19.46 / 3600, 46 + 59 / 60 + 3.75 / 3600, "^", "white", FS.PALETTE["ink"], (7, -3), "left")}


def figS14(day="2023-06-07"):
    """D-SUPPORT: where the reconstructed new inundation of a day rests on direct, extrapolated or weak water-surface support."""
    import rasterio
    from pyproj import Transformer
    arrs = {}
    for z in ZONES:
        d = BULK / "floodplain_dyn" / f"{z}_connected_ceiling"
        with rasterio.open(d / "support_class.tif") as src:
            code = src.read(1); G = dict(transform=src.transform, ny=src.height, nx=src.width)
        nz = np.load(d / "daily_new.npz"); shp = tuple(int(v) for v in nz["shape"])
        new = np.unpackbits(nz[day], count=shp[0] * shp[1]).reshape(shp).astype(bool)
        arrs[z] = (np.where(new, code, 0).astype("u1"), G)
    K, ext = zone_mosaic(arrs, np.uint8(0))
    with rasterio.open(BULK / "dem_seamless" / "dem_seamless_evrf2019_50m.tif") as src:
        dem = src.read(1).astype("f4"); dem[dem == src.nodata] = np.nan; tr = src.transform
        dext = [tr.c / 1e3, (tr.c + tr.a * src.width) / 1e3, (tr.f + tr.e * src.height) / 1e3, tr.f / 1e3]
    hs = LightSource(azdeg=315, altdeg=40).hillshade(np.nan_to_num(dem, nan=0), vert_exag=3, dx=50, dy=50)
    C = pd.read_csv(T / "p95l_supported_core.csv")
    fig = plt.figure(figsize=(7.4, 8.2), constrained_layout=True); gs = fig.add_gridspec(2, 2, height_ratios=[2.3, 1.0])
    a = fig.add_subplot(gs[0, :])
    if not s2_basemap(a, "pre", step=2):
        a.imshow(hs, cmap="gray", extent=dext, vmin=0, vmax=1, alpha=0.55, interpolation="bilinear", rasterized=True)
    cm = ListedColormap(["#ffffff"] + [SUPPORT_COLOURS[k][1] for k in sorted(SUPPORT_COLOURS)])
    a.imshow(np.ma.masked_where(K[::2, ::2] == 0, K[::2, ::2]), cmap=cm, vmin=0, vmax=len(SUPPORT_COLOURS), extent=ext, interpolation="nearest", rasterized=True, zorder=2)
    n = pd.read_csv(T / "p59_swot_flood_nodes.csv", usecols=["node_id", "x", "y", "river_name"]).drop_duplicates("node_id")
    inh = n.river_name.eq("Inhulets")
    a.scatter(n.x[~inh] / 1e3, n.y[~inh] / 1e3, s=1.2, color=FS.PALETTE["ink2"], lw=0, label="SWOT nodes")
    a.scatter(n.x[inh] / 1e3, n.y[inh] / 1e3, s=1.2, color=FS.PALETTE["rf"], lw=0, label="SWOT nodes, Inhulets")
    tfm = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True)
    for nm, (lon, lat, mk, fc, ec, off, ha) in GAUGES.items():
        x, y = tfm.transform(lon, lat); a.plot(x / 1e3, y / 1e3, mk, ms=7, mfc=fc, mec=ec, mew=1.2, zorder=6)
        a.annotate(nm, (x / 1e3, y / 1e3), xytext=off, textcoords="offset points", fontsize=6, va="top", ha=ha, zorder=6,
                   bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
    view = [415, 545, 5130, 5226]; furniture(a, view, 20)
    c7 = C[(C.date == day) & (C.region == "DNIPRO_CORRIDOR")].iloc[0]
    a.text(0.99, 0.22, f"Dnipro corridor, nominal run, {day}:\ndirect {c7.A_direct_km2:.0f} km², extrapolated {c7.A_extrapolated_km2:.0f} km²,\n"
                        f"weak {c7.A_weak_km2:.0f} km² ({c7.share_weak:.0%}); supported core {c7.A_core_le10km_km2:.0f} of {c7.A_full_km2:.0f} km²",
           transform=a.transAxes, fontsize=6.3, va="bottom", ha="right", bbox=dict(fc="white", ec="#c3c2b7", alpha=0.9))
    h = [Patch(fc=col, label=lab) for k, (lab, col) in sorted(SUPPORT_COLOURS.items()) if k != 5] + a.get_legend_handles_labels()[0]
    a.legend(handles=h, loc="upper left", fontsize=6, frameon=True, framealpha=0.85, title=f"new inundation on {day} by water-surface support", title_fontsize=6.5)
    a.set_title("Observational support of the terrain-connectivity reconstruction (support classes: operational thresholds, T11k)", fontsize=8, loc="left"); FS.panel_label(a, "a")
    b = fig.add_subplot(gs[1, 0]); q = C[C.region == "DNIPRO_CORRIDOR"].copy(); q["t"] = pd.to_datetime(q.date); q = q.sort_values("t")
    b.plot(q.t, q.A_full_km2, color=FS.PALETTE["ink"], lw=1.6, label="full reconstruction (nominal)")
    b.plot(q.t, q.A_core_le10km_km2, color=FS.PALETTE["terrain"], lw=1.4, label="supported core (≤ 10 km)")
    b.plot(q.t, q.A_direct_km2, color=SUPPORT_COLOURS[1][1], lw=1.0, label="direct (≤ 3 km)")
    if "A_cap10km_sensitivity_km2" in q.columns:
        b.plot(q.t, q.A_cap10km_sensitivity_km2, color=FS.PALETTE["muted"], lw=1.2, ls="--", label="run without surfaces from nodes > 10 km")
    FS.date_axis(b, BREACH, every_days=7); b.set_xlim(pd.Timestamp("2023-06-03"), pd.Timestamp("2023-06-25")); b.set_ylim(0, None)
    b.set_ylabel("new inundation, km² (Dnipro corridor)", fontsize=6.5); b.tick_params(labelsize=6); b.legend(fontsize=5.8, frameon=False); FS.panel_label(b, "b")
    c = fig.add_subplot(gs[1, 1])
    for r, col in (("DNIPRO_CORRIDOR", FS.PALETTE["ink"]), ("P42_FLOODPLAIN_DOMAIN", FS.PALETTE["terrain"]), ("INHULETS_VALLEY_rect", FS.PALETTE["rf"])):
        w = C[C.region == r].copy(); w["t"] = pd.to_datetime(w.date); w = w.sort_values("t")
        c.plot(w.t, np.where(w.A_full_km2 >= 1.0, 100 * w.share_weak, np.nan), color=col, lw=1.4, marker="o", ms=2, label=REG_TITLE[r])  # < 1 km2: share undefined
    FS.date_axis(c, BREACH, every_days=7); c.set_xlim(pd.Timestamp("2023-06-03"), pd.Timestamp("2023-06-25")); c.set_ylim(0, 100)
    c.set_ylabel("share of the new area with support > 10 km, %", fontsize=6.5); c.tick_params(labelsize=6); c.legend(fontsize=5.8, frameon=False); FS.panel_label(c, "c")
    FS.save(fig, "FigS14_support_domain", FIG)


def figS16():
    """D-SEED / D-MEMORY: (a-c) the superseded all-prewater seeding on 6, 9 and 15 June 2023 by seed class (p95o lineage classes:
    river-connected / trapped after an earlier connection / isolated never connected) on the Sentinel-2 image of June 2022, with
    the three areas in every title; (d) 18 June 2023 on the Sentinel-2 image of that day: the primary reconstruction (river-network
    seed) and the retained water of the memory sensitivity classed by the same-day Sentinel-1 scene (plausible / likely drained /
    uncertain; p95o --compare)."""
    import rasterio
    from pyproj import Transformer
    from matplotlib.lines import Line2D
    old, mem = "_connected_ceiling_seed_allprewater", "_connected_ceiling_memory"
    COL = dict(network="#3b4a5c", river=FS.PALETTE["terrain"], trapped="#8e6bbf", isolated="#e34948", plausible="#8e6bbf", drained="#e34948", uncertain="#9aa5b1")

    def packed_layer(sfx, name, day, codes=(1, 2, 3)):
        arrs = {}
        for z in ZONES:
            d = BULK / "floodplain_dyn" / f"{z}{sfx}"; zz = np.load(d / name); shp = tuple(int(v) for v in zz["shape"]); out = np.zeros(shp, "u1")
            for code in codes:
                k = f"{day}_c{code}"
                if k in zz.files:
                    out[np.unpackbits(zz[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)] = code
            with rasterio.open(d / "duration_days.tif") as s_:
                arrs[z] = (out, dict(transform=s_.transform, ny=s_.height, nx=s_.width))
        return zone_mosaic(arrs, np.uint8(0))

    def new_water(sfx, day):
        arrs = {}
        for z in ZONES:
            d = BULK / "floodplain_dyn" / f"{z}{sfx}"; zz = np.load(d / "daily_new.npz"); shp = tuple(int(v) for v in zz["shape"])
            with rasterio.open(d / "duration_days.tif") as s_:
                arrs[z] = (np.unpackbits(zz[day], count=shp[0] * shp[1]).reshape(shp).astype(bool), dict(transform=s_.transform, ny=s_.height, nx=s_.width))
        return zone_mosaic(arrs, False)

    def network():
        arrs = {}
        for z in ZONES:
            p = BULK / "floodplain_dyn" / f"{z}_connected_ceiling" / "event_source_network.tif"
            if not p.exists():
                return None, None
            with rasterio.open(p) as s_:
                arrs[z] = (s_.read(1).astype(bool), dict(transform=s_.transform, ny=s_.height, nx=s_.width))
        return zone_mosaic(arrs, False)

    net, _ = network(); n = pd.read_csv(T / "p59_swot_flood_nodes.csv", usecols=["node_id", "x", "y"]).drop_duplicates("node_id")
    tfm = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True); kx, ky = tfm.transform(*KALYNIVSKE_LONLAT)
    fig = plt.figure(figsize=(7.4, 9.4), constrained_layout=True); gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.55])
    cm = ListedColormap(["#ffffff", COL["river"], COL["trapped"], COL["isolated"]]); box = None
    for k, day in enumerate(("2023-06-06", "2023-06-09", "2023-06-15")):
        K, ext = packed_layer(old, "daily_component_class.npz", day); box = [ext[0], min(ext[1], 540), 5136, ext[3]]
        km = {c: float((K == c).sum()) * 4e-4 for c in (1, 2, 3)}
        a = fig.add_subplot(gs[0, k]); s2_basemap(a, "pre", step=4)
        if net is not None:
            a.imshow(np.ma.masked_where(~net[::4, ::4], np.ones_like(net[::4, ::4], dtype="u1")), cmap=ListedColormap([COL["network"]]), extent=ext, alpha=0.9, interpolation="nearest", rasterized=True, zorder=1)
        a.imshow(np.ma.masked_where(K[::4, ::4] == 0, K[::4, ::4]), cmap=cm, vmin=0, vmax=3, extent=ext, interpolation="nearest", rasterized=True, zorder=2)
        outline_mask(a, K == 3, ext, "#111111", step=4, lw=0.5, zorder=4)
        a.set_xlim(box[0], box[1]); a.set_ylim(box[2], box[3]); a.set_aspect("equal"); a.tick_params(labelsize=5.5)
        a.set_title(f"{day[5:].replace('-', ' ')} Jun: river {km[1]:.0f} | trapped {km[2]:.0f} | isolated {km[3]:.0f} km²", fontsize=6.6, loc="left"); FS.panel_label(a, "abc"[k])
        if k == 0:
            a.set_ylabel("northing, km", fontsize=6)
        a.set_xlabel("easting, km", fontsize=6)
    fig.legend(handles=[Patch(fc=COL["network"], label="event-source network (largest connected component of the pre-breach water map): the seed of the primary rule"),
                        Patch(fc=COL["river"], label="river-connected on the day: the flood"),
                        Patch(fc=COL["trapped"], label="trapped after an earlier connection: retained-water candidate"),
                        Patch(fc=COL["isolated"], ec="#111111", label="isolated, never connected along its lineage: seeded by ponds / canals -- not event inundation")],
               loc="outside upper center", ncol=2, fontsize=5.6, frameon=False, title="superseded all-prewater seeding, new inundation by seed class (p95o); all regions", title_fontsize=6.2)
    d = fig.add_subplot(gs[1, :]); day = "2023-06-18"; new, ext = new_water("_connected_ceiling", day)
    if not s2_basemap(d, "event", step=2):
        s2_basemap(d, "pre", step=2)
    d.imshow(np.ma.masked_where(~new[::2, ::2], np.ones_like(new[::2, ::2], dtype="u1")), cmap=ListedColormap([COL["river"]]), extent=ext, alpha=0.9, interpolation="nearest", rasterized=True, zorder=2)
    handles = [Patch(fc=COL["river"], label=f"new inundation on {day}, primary (river-network seed)")]
    title = f"Recession, {day}: primary reconstruction"
    pm = BULK / "floodplain_dyn" / f"{list(ZONES)[0]}{mem}" / "retained_class.npz"
    if pm.exists():
        Rc, _ = packed_layer(mem, "retained_class.npz", day)
        rkm = {c: float((Rc == c).sum()) * 4e-4 for c in (1, 2, 3)}
        d.imshow(np.ma.masked_where(Rc[::2, ::2] == 0, Rc[::2, ::2]), cmap=ListedColormap(["#ffffff", COL["plausible"], COL["drained"], COL["uncertain"]]), vmin=0, vmax=3, extent=ext, alpha=0.9, interpolation="nearest", rasterized=True, zorder=3)
        handles += [Patch(fc=COL["plausible"], label="retained water (memory minus primary), same-day Sentinel-1 shows water: plausible"),
                    Patch(fc=COL["drained"], label="retained water on open ground the same-day scene shows without water: likely drained"),
                    Patch(fc=COL["uncertain"], label="retained water without a usable same-day observation: uncertain")]
        title += f" and retained water of the memory sensitivity: plausible {rkm[1]:.0f} | likely drained {rkm[2]:.0f} | uncertain {rkm[3]:.0f} km²"
    d.scatter(n.x / 1e3, n.y / 1e3, s=0.6, color="white", lw=0, zorder=5); d.plot(kx / 1e3, ky / 1e3, "^", ms=6, mfc="white", mec=FS.PALETTE["ink"], mew=1.1, zorder=6)
    handles += [Line2D([], [], marker="o", ls="none", color="white", markeredgecolor="#555", label="SWOT nodes"), Line2D([], [], marker="^", ls="none", mfc="white", mec=FS.PALETTE["ink"], label="Kalynivske 80575 (withheld gauge)")]
    reporting_overlay(d, ext[3]); furniture(d, box, 10); FS.panel_label(d, "d"); d.legend(handles=handles, loc="lower left", fontsize=5.4, framealpha=0.9)
    d.set_title(title, fontsize=6.6, loc="left")
    fig.text(0.01, 0.003, "Basemaps: Sentinel-2 L2A true colour (a-c 13 / 20 June 2022, d 18 June 2023), processed by the authors; contains modified Copernicus Sentinel data 2022 / 2023.", fontsize=5.3, color="#555")
    FS.save(fig, "FigS16_seed_classes", FIG)


def figS17():
    """The ensemble decides marginal components (maintainer, 2026-09-30): P(new inundation) per cell over the coherent Monte-Carlo
    worlds (p95e cellprob, T12g) on 7, 8, 9 and 13 June 2023, on the Sentinel-2 image of June 2022; the P >= 0.5 classes are
    the median world -- the map product of the ensemble; the nominal daily map (Fig07) is one world."""
    import rasterio
    PROB = [(0.95, "#0b2a5c", "P ≥ 0.95"), (0.75, "#2a78d6", "0.75 ≤ P < 0.95"), (0.5, "#7fb3e6", "0.50 ≤ P < 0.75 (in the median world)"),
            (0.25, "#eda100", "0.25 ≤ P < 0.50"), (0.05, "#f5d58a", "0.05 ≤ P < 0.25 (marginal: a sill within the uncertainty)")]
    S = pd.read_csv(T / "p95e_cellprob_summary.csv"); Sc = S[S.region == "DNIPRO_CORRIDOR"].set_index("date")
    days = [d for d in ("2023-06-07", "2023-06-08", "2023-06-09", "2023-06-13") if d in Sc.index]
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 7.6), constrained_layout=True); box = None
    for ax, day in zip(axs.ravel(), days):
        arrs = {}
        for z in ZONES:
            with rasterio.open(BULK / "floodplain_dyn" / f"{z}_connected_ceiling" / f"p95e_cellprob_{day}.tif") as s_:
                cnt = s_.read(1).astype("f4"); n = float(s_.tags().get("n_draws", 1000)); arrs[z] = (cnt / n, dict(transform=s_.transform, ny=s_.height, nx=s_.width))
        Pm, ext = zone_mosaic(arrs, np.float32(0)); box = [ext[0], min(ext[1], 540), 5136, ext[3]]
        cls = np.zeros(Pm.shape, "u1")
        for code, (lo, _, _) in enumerate(reversed(PROB), 1):                  # 1 = P >= 0.05 ... 5 = P >= 0.95
            cls[Pm >= lo] = code
        s2_basemap(ax, "pre", step=4)
        cm = ListedColormap(["#ffffff"] + [c for _, c, _ in reversed(PROB)])
        ax.imshow(np.ma.masked_where(cls[::4, ::4] == 0, cls[::4, ::4]), cmap=cm, vmin=0, vmax=5, extent=ext, interpolation="nearest", rasterized=True, zorder=2)
        r = Sc.loc[day]; furniture(ax, box, 10); ax.tick_params(labelsize=5.5); FS.panel_label(ax, "abcd"[days.index(day)])
        ax.set_title(f"{day}\nmedian world (P ≥ 0.5) {r['A_P_ge_0.50_km2']:.0f} km² · nominal {r.A_nominal_km2:.0f} · expected {r.A_expected_km2:.0f} · P ≥ 0.05: {r['A_P_ge_0.05_km2']:.0f} km²", fontsize=6.0, loc="left")
    fig.legend(handles=[Patch(fc=c, label=lab) for _, c, lab in PROB], loc="outside lower center", ncol=3, fontsize=5.8, frameon=False,
               title="P(new inundation on the day) over the 1000 coherent Monte-Carlo worlds (Dnipro corridor areas in the titles; T12g)", title_fontsize=6.2)
    fig.text(0.995, 0.995, "Basemap: Sentinel-2 L2A true colour, 13 / 20 June 2022, processed by the authors; contains modified Copernicus Sentinel data 2022.", fontsize=5.3, color="#555", ha="right", va="top")
    FS.save(fig, "FigS17_inundation_probability", FIG)


def figS18():
    """Saddle audit of the floodplain lowland south of Krynky (p95p, T15d-T15f): the lowest path from the river network, the terrain
    surfaces, the bed, the water surfaces of 7 and 8 June and the ICESat-2 night ground points along the path."""
    nm = "kozachi_laheri_lowland"; Pf = pd.read_csv(T / f"p95p_saddle_profile_{nm}.csv"); S = pd.read_csv(T / f"p95p_saddle_summary_{nm}.csv")
    ip = T / f"p95p_saddle_icesat_points_{nm}.csv"; pts = pd.read_csv(ip) if ip.exists() else None
    fig, ax = plt.subplots(figsize=(7.2, 3.6), constrained_layout=True); s_km = Pf.s_m / 1e3
    ax.plot(s_km, Pf.z_model_m, color=FS.PALETTE["ink"], lw=1.4, label="model terrain (seamless terrain–bed model, residual FABDEM class bias removed)")
    ax.plot(s_km, Pf.z_fabdem_uncorrected_m, color=FS.PALETTE["muted"], lw=0.9, ls="--", label="FABDEM as delivered")
    ax.plot(s_km, Pf.z_glo30_m, color=FS.PALETTE["s1"], lw=0.8, alpha=0.8, label="Copernicus DEM GLO-30 (surface model; same datum step)")
    ax.plot(s_km, Pf.z_bed_m, color="#8b5a2b", lw=2.0, label="channel bed of the model")
    for d, col, ls in zip([c for c in Pf.columns if c.startswith("H_")], (FS.PALETTE["terrain"], "#7fb3e6"), ("-.", ":")):
        ax.plot(s_km, Pf[d], color=col, lw=1.2, ls=ls, label=f"water surface {d[2:12]}")
    if pts is not None and len(pts):
        xy = Pf[["x", "y"]].values; sp = [float(Pf.s_m.iloc[int(np.argmin(np.hypot(xy[:, 0] - x, xy[:, 1] - y)))]) / 1e3 for x, y in zip(pts.x, pts.y)]
        ax.scatter(sp, pts.H_ice, s=7, color=FS.PALETTE["rf"], zorder=5, label=f"ICESat-2 ATL08 night ground within 100 m of the path (n = {len(pts)})")
    wcn = Pf.worldcover.values; y0 = float(np.nanmin(Pf[["z_model_m", "z_bed_m"]].min())) - 0.6
    for k in range(len(Pf) - 1):
        col = {"trees": "#2e7d32", "wetland": "#00897b", "grass": "#c0ca33", "cropland": "#f9a825", "water": "#1e88e5", "built": "#8d6e63"}.get(wcn[k], "#bdbdbd")
        ax.plot([s_km[k], s_km[k + 1]], [y0, y0], color=col, lw=5, solid_capstyle="butt")
    m = S[S.surface == "model_terrain_bias_removed"]
    ax.set_title("Lowest path from the river network to the floodplain lowland south of Krynky: saddle %.2f m; head at the saddle %s" %
                 (m.z_saddle_m.iloc[0], ", ".join(f"{r.day[5:]} {r.delta_H_saddle_m:+.2f} m" for r in m.itertuples())), fontsize=7.5, loc="left")
    ax.set_xlabel("distance along the path from the river network, km", fontsize=7); ax.set_ylabel("height, m EVRF2019", fontsize=7); ax.tick_params(labelsize=6.5)
    ax.legend(fontsize=5.6, loc="upper right"); ax.grid(alpha=0.3)
    ax.text(0.01, 0.02, "bar: WorldCover along the path (green forest, teal wetland, lime grass, orange cropland, blue water)", transform=ax.transAxes, fontsize=5.8, color="#555")
    FS.save(fig, "FigS18_saddle_audit", FIG)


def figS15():
    """The two withheld gauges: what the static reconstruction gets wrong in the tributary and in the western delta (p95k)."""
    K = pd.read_csv(PT / "T17c.csv"); L = pd.read_csv(PT / "T17e.csv"); man = json.loads((T / "p95k_manifest.json").read_text())
    for d in (K, L):
        d["t"] = pd.to_datetime(d.date)
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 5.6), sharex=True, height_ratios=(1.7, 1.0), constrained_layout=True)
    a = axs[0, 0]
    a.plot(K.t, K.kherson_gauge_m, color=FS.PALETTE["muted"], lw=1.0, label="Kherson gauge (input)")
    a.plot(K.t, K.H_reconstructed_primary_m, color=FS.PALETTE["terrain"], lw=1.6, label="reconstructed surface at the gauge")
    a.plot(K.t, K.H_evrf2019_m, "o-", color=FS.PALETTE["ink"], ms=2.5, lw=1.3, label="gauge Kalynivske, daily means (withheld)")
    hi = man.get("highest", {})
    if hi:
        a.plot(pd.Timestamp(hi["date"]), hi["H_evrf2019_m"], "*", color=FS.PALETTE["ink"], ms=8, label=f"highest level {hi['printed']} cm")
    a.set_ylabel("water level, m EVRF2019", fontsize=6.5); a.set_title("Inhulets – Kalynivske 80575 (tributary backwater)", fontsize=7.5, loc="left"); FS.panel_label(a, "a")
    b = axs[0, 1]; hl = man.get("liman", {}).get("highest", {})
    b.plot(L.t, L.kherson_gauge_m, color=FS.PALETTE["muted"], lw=1.0, label="Kherson gauge (input)")
    b.plot(L.t, L.H_reconstructed_primary_m, color=FS.PALETTE["terrain"], lw=1.6, label="reconstructed surface at the gauge")
    b.plot(L.t, L.H_evrf2019_m, "o-", color=FS.PALETTE["ink"], ms=2.5, lw=1.3, label="gauge Mykolaiv, daily means (withheld)")
    if hl:
        b.plot(pd.Timestamp(hl["date"]), hl["H_evrf2019_m"], "*", color=FS.PALETTE["ink"], ms=8, label=f"highest level {hl['printed']} cm")
    b.set_title("Southern Bug – Mykolaiv 98027 (liman, western delta)", fontsize=7.5, loc="left"); FS.panel_label(b, "b")
    for ax, D in ((axs[1, 0], K), (axs[1, 1], L)):
        ax.axhline(0, color=FS.PALETTE["ink2"], lw=0.6)
        ax.plot(D.t, D.recon_minus_gauge_m, color=FS.PALETTE["terrain"], lw=1.4, label="e_abs = reconstruction − gauge")
        ax.plot(D.t, D.e_rise_m, color=FS.PALETTE["s1"], lw=1.4, ls="--", label="e_rise = reconstructed rise − gauge rise")
        ax.set_ylabel("error at the gauge, m", fontsize=6.5)
    FS.panel_label(axs[1, 0], "c"); FS.panel_label(axs[1, 1], "d")
    for ax in axs.ravel():
        FS.date_axis(ax, BREACH, every_days=7); ax.set_xlim(pd.Timestamp("2023-05-28"), pd.Timestamp("2023-07-05")); ax.tick_params(labelsize=6); ax.legend(fontsize=5.6, frameon=False)
    FS.save(fig, "FigS15_withheld_gauges", FIG)


def figS19():
    """Maintainer 2026-10-01 ("where is a normal flood map from S1"): the Sentinel-1 new dark water of every date that covers the
    corridor fully, on the Sentinel-2 image of June 2022 -- what the radar sees on the day it looks (observed_S1; the masks of p94 /
    p95: dark water minus the optical pre-breach water minus the cells already dark on 1-2 June), with the terrain-reconstructed new
    inundation of the same day (nominal world) as a line."""
    P95 = _ld("p95", M6 / "p95_hand_daily_inundation.py"); O = _ld("p95o", M6 / "p95o_component_qa.py")
    P = P95.load_p92(); M = P95.mosaic_layers(P, with_s1=True); g = M["grid"]; tr = g.transform; ny, nx = g.shape
    ext = [tr.c / 1e3, (tr.c + tr.a * nx) / 1e3, (tr.f + tr.e * ny) / 1e3, tr.f / 1e3]
    own = (M["own_id"] > 0) & M["base_geom"]; pre = M["pre"]; dark = M["s1_pre_dark"]; corridor = own & ~M["cut"]
    S = pd.read_csv(T / "p94_flood_dynamics_s1.csv"); Sc = S[S.region == "DNIPRO_CORRIDOR"].set_index("date")
    def comp(key, d):                                                        # the S1 layers live per zone (p95 zone_layers): compose as p95x does
        return g.compose({z: L[key].get(d, np.zeros(L["pre"].shape, bool)) for z, L in M["zones"].items()}, False, order=M["names"], dtype=bool)
    have = {d for L in M["zones"].values() for d in L["W"]}
    obs = np.logical_or.reduce([comp("V", d) for d in sorted(have)]) & own          # the S1 observable domain (union of the footprints), as p94
    days = [d for d in ("2023-06-06", "2023-06-09", "2023-06-13", "2023-06-14", "2023-06-18", "2023-06-21") if d in have]
    C_S1 = "#2a78d6"                                                          # slot 1 blue = Sentinel-1 (p94, Fig05)
    fig, axs = plt.subplots(3, 2, figsize=(7.4, 10.4), constrained_layout=True); box = [ext[0], min(ext[1], 540), 5136, ext[3]]
    cm = ListedColormap(["#ffffff", "#b9c7d6", C_S1]); k = 4
    for ax, d in zip(axs.ravel(), days):
        W, V = comp("W", d) & own, comp("V", d) & own
        st = np.zeros((ny, nx), "u1"); st[V & pre] = 1; st[W & ~(pre | dark)] = 2
        s2_basemap(ax, "pre", step=k)
        ax.imshow(np.ma.masked_where(st[::k, ::k] == 0, st[::k, ::k]), cmap=cm, vmin=0, vmax=2, extent=ext, interpolation="nearest", rasterized=True, zorder=2)
        hatch_mask(ax, obs & ~V, ext, "#6f6f6f", hatch="////", step=2 * k)
        rec = O.compose_npz(M, "_connected_ceiling", d) & corridor
        ax.contour(rec[::k, ::k].astype("f4"), levels=[0.5], extent=ext, origin="upper", colors="k", linewidths=0.3, zorder=4)
        r = Sc.loc[d]; furniture(ax, box, 10); ax.tick_params(labelsize=5.5); FS.panel_label(ax, "abcdef"[days.index(d)])
        ax.set_title(f"{d} · {r.orbit} · coverage {r.coverage:.0%}\nS1 new dark water {r.new_water_km2:.0f} km² · reconstruction {float(rec.sum()) * P95.CELL_KM2:.0f} km² (corridor)", fontsize=6.0, loc="left")
    for ax in axs.ravel()[len(days):]:
        ax.axis("off")
    fig.legend(handles=[Patch(fc=C_S1, label="Sentinel-1 new dark water (not water before the breach; observed_S1)"), Patch(fc="#b9c7d6", label="pre-breach water (optical, p60)"),
                        Patch(fc="none", ec="#6f6f6f", hatch="////", label="not observed on this date"), Line2D([], [], color="k", lw=0.8, label="terrain-reconstructed new inundation of the day (nominal world)")],
               loc="outside lower center", ncol=2, fontsize=5.8, frameon=False)
    fig.suptitle("Basemap: Sentinel-2 L2A true colour, 13 / 20 June 2022, processed by the authors; contains modified Copernicus Sentinel data 2022.", fontsize=5.3, color="#555", x=0.99, ha="right")
    FS.save(fig, "FigS19_s1_new_water_by_date", FIG)



ALL = {"Fig01": (fig01, True), "Fig02": (fig02, False), "Fig03": (fig03, True), "Fig04": (fig04, False), "Fig05": (fig05, True), "Fig06": (fig06, False), "Fig07": (fig07, True), "Fig08": (fig08, False), "Fig09": (fig09, False),
       "FigS01": (figS01, False), "FigS02": (figS02, False), "FigS03": (figS03, False), "FigS04": (figS04, False), "FigS05": (figS05, False), "FigS06": (figS06, False), "FigS07": (figS07, False),
       "Fig11": (fig11, True), "FigS08": (figS08, True), "FigS09": (figS09, True), "FigS10": (figS10, False), "FigS11": (figS11, False), "FigS12": (figS12, False), "FigS13": (figS13, False),
       "FigS14": (figS14, True), "FigS15": (figS15, False), "FigS16": (figS16, True), "FigS17": (figS17, True), "FigS18": (figS18, False), "FigS19": (figS19, True), "Fig10": (fig10, True)}


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
