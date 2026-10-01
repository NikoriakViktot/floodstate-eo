# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Area summary + maps from finished runs; trains nothing.
"""P92 -- predicted flood area from the dam to the liman (B1 u B2 mosaic, one physical pixel once), per run,
split into the Dnipro corridor and the Inhulets valley.

The Inhulets is NOT Dnipro floodplain and must not be averaged into the main-channel reach (SWOT-DNIPRO
spatial_domains.yaml: INHULETS_TRIBUTARY "joins from the north with its own regime"). The cut uses the maintainer's
own rectangles drawn 2026-09-19 (SWOT-DNIPRO scripts/p42_below_dam_floodplain.py CUT_RECTS, copied verbatim below):
west of the Inhulets mouth north of the cut line, the Inhulets valley itself, and isolated terrace fragments NE of
the mouth. Everything outside those rectangles is the DNIPRO corridor (dam -> Kherson -> delta -> liman).
The rectangles are REPORTING regions, not masks (maintainer, 2026-09-30): every reconstruction and map covers the Inhulets valley;
only the accounting keeps it apart from the corridor total.

Per run and region: predicted flood (score >= that run's frozen validation threshold) in km2, and its decomposition
by v003_A ontology (EVENT_FLOOD label / REFERENCE_WATER / LAND / UNKNOWN) and by pre-breach water (labels.tif
pre_water_frac >= 20 % = channel or pond that already held water before 2023-06-06). "New flood on land" =
predicted, not pre-breach water, not REFERENCE_WATER. Observed / unobserved area is reported next to it: where no
S1 event exists (B1 west strip) nothing is predicted -- not observed is not dry.

Outputs: <case_study>/tables/p92_flood_area_dam_to_liman.csv, p92_inhulets_profile.csv
         <case_study>/figures/m6_v003A/mosaic_dam_to_liman_<run>.png, <F>_flood_map_compare.png
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd, rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, Rectangle
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = CFG.BULK_ROOT / "frames10"
FIG = ROOT / "figures" / "m6_v003A"
PX = 1e-4
FRAMES = ("B1", "B2")
OWNER = ("B2", "B1")                     # B2 owns the overlap (m6_split_v1 rule)
# SWOT-DNIPRO scripts/p42_below_dam_floodplain.py CUT_RECTS (x0, y0, x1, y1; EPSG:32636 metres), maintainer 2026-09-19
CUT_RECTS = {"west_of_inhulets_mouth": (462000.0, 5175000.0, 481000.0, 5300000.0),
             "inhulets_valley": (481000.0, 5180000.0, 503000.0, 5300000.0),
             "terrace_fragments_ne": (503000.0, 5187000.0, 530000.0, 5300000.0)}
PRE_WATER_PCT = 20
RUN_COLOR = {"U2_B1B2_v1": "#eb6834", "U0d_B1B2_v003A": "#1baf7a", "U2_B1B2_v003A": "#2a78d6", "U2b_B1B2_v003A": "#4a3aa7",
             "U2_B1B2_v004": "#2a78d6", "U2b_B1B2_v004": "#4a3aa7"}                # arms on the corrected labels (review stage 2)
DS = 4


def mosaic_grid():
    G = {f: CG.frame_grid(f) for f in FRAMES}
    x0 = min(G[f]["transform"].c for f in FRAMES); y1 = max(G[f]["transform"].f for f in FRAMES)
    x1 = max(G[f]["transform"].c + 10 * G[f]["nx"] for f in FRAMES); y0 = min(G[f]["transform"].f - 10 * G[f]["ny"] for f in FRAMES)
    nx, ny = int(round((x1 - x0) / 10)), int(round((y1 - y0) / 10))
    off = {f: (int(round((y1 - G[f]["transform"].f) / 10)), int(round((G[f]["transform"].c - x0) / 10))) for f in FRAMES}
    return dict(x0=x0, y0=y0, x1=x1, y1=y1, nx=nx, ny=ny, off=off, G=G)


def place(M, layers, fill):
    """Mosaic per-frame arrays; later frames in OWNER order never overwrite earlier ones (B2 owns the overlap)."""
    out = np.full((M["ny"], M["nx"]), fill, dtype=np.asarray(next(iter(layers.values()))).dtype)
    done = np.zeros(out.shape, bool)
    for f in OWNER:
        r, c = M["off"][f]; a = layers[f]; h, w = a.shape
        sl = (slice(r, r + h), slice(c, c + w))
        m = ~done[sl]
        out[sl][m] = a[m]; done[sl] |= True
    return out


def rect_mask(M, rect):
    x0, y0, x1, y1 = rect
    gx = M["x0"] + 10.0 * (np.arange(M["nx"]) + 0.5); gy = M["y1"] - 10.0 * (np.arange(M["ny"]) + 0.5)
    return ((gy >= y0) & (gy < y1))[:, None] & ((gx >= x0) & (gx < x1))[None, :]


def load_layers(M):
    """S1 observation, reference ontologies (v003_A; v004 when built), pre-breach water, ownership on the mosaic."""
    has, ont, ont4, pre, owned = {}, {}, {}, {}, {}
    for f in FRAMES:
        with rasterio.open(OUT / f / "s1_change.tif") as s:
            d = list(s.descriptions); ne = s.read(d.index("n_valid_event") + 1); d0 = s.read(1)
        has[f] = (ne > 0) & (d0 != -32768)
        with rasterio.open(OUT / f / "m6_labels_v003_A.tif") as s:
            ont[f] = s.read(1)
        if (OUT / f / "m6_labels_v004.tif").exists():
            with rasterio.open(OUT / f / "m6_labels_v004.tif") as s:
                ont4[f] = s.read(1)
        with rasterio.open(OUT / f / "labels.tif") as s:
            d = list(s.descriptions); w = s.read(d.index("pre_water_frac") + 1)
        pre[f] = w >= PRE_WATER_PCT
        owned[f] = np.ones(has[f].shape, bool)
    return dict(has=place(M, has, False), ont=place(M, ont, np.uint8(255)), pre=place(M, pre, False),
                owned=place(M, owned, False), ont_v004=place(M, ont4, np.uint8(255)) if len(ont4) == len(FRAMES) else None)


def run_layers(L, run):
    """The layers with the reference ontology of the run's own label version (review stage 2): v004 for the arms on the
    corrected labels (v004, v002_notrace), v003_A for the historical arms. Returns (layers, ontology name)."""
    lab = json.loads((ROOT / "runs" / run / "config.json").read_text()).get("labels", "")
    if lab in ("m6_labels_v004", "m6_labels_v002_notrace"):
        assert L["ont_v004"] is not None, "m6_labels_v004.tif not built"
        return dict(L, ont=L["ont_v004"]), "v004"
    return L, "v003_A"


def load_pred(M, run):
    arm, suffix = run.split("_B1B2_")
    name = f"{arm}_score.tif" if suffix == "v1" else f"{arm}_{suffix}_score.tif"
    thr = json.loads((ROOT / "runs" / run / "validation_threshold.json").read_text())["threshold"]
    P = {}
    for f in FRAMES:
        with rasterio.open(OUT / f / "m6" / name) as s:
            q = s.read(1)
        P[f] = (q != 65535) & (q / 1e4 >= thr)
    return place(M, P, False), thr


def floodplain_domain(M):
    """Optional: the p42 terrain-eligible floodplain (SWOT-DNIPRO below_dam_floodplain_utm.geojson) as a mask."""
    p = Path(CFG._SWOT_DNIPRO_SIBLING) / "data/processed/domains/below_dam_floodplain_utm.geojson"
    if not p.exists():
        return None, None
    try:
        from rasterio import features
        from rasterio.transform import from_origin
        gj = json.loads(p.read_text())
        crs = str(gj.get("crs", {}).get("properties", {}).get("name", ""))
        assert "32636" in crs, f"expected EPSG:32636 GeoJSON, got {crs!r}"
        tr = from_origin(M["x0"], M["y1"], 10.0, 10.0)
        m = features.rasterize([(ft["geometry"], 1) for ft in gj["features"]], out_shape=(M["ny"], M["nx"]),
                               transform=tr, fill=0, dtype="uint8").astype(bool)
        return m, str(p)
    except Exception as e:                                                   # noqa: BLE001
        print("floodplain domain not loaded:", e)
        return None, None


def summarise(L, pred, region, name, run, thr, onto="v003_A"):
    obs = region & L["owned"] & L["has"]; unobs = region & L["owned"] & ~L["has"]
    p = pred & obs
    return dict(run=run, threshold=thr, region=name, ontology=onto,
                area_km2=round(float((region & L["owned"]).sum()) * PX, 1),
                observed_km2=round(float(obs.sum()) * PX, 1), unobserved_no_s1_event_km2=round(float(unobs.sum()) * PX, 1),
                predicted_flood_km2=round(float(p.sum()) * PX, 1),
                on_EVENT_FLOOD_label_km2=round(float((p & (L["ont"] == 1)).sum()) * PX, 1),
                on_REFERENCE_WATER_km2=round(float((p & (L["ont"] == 2)).sum()) * PX, 1),
                on_LAND_label_km2=round(float((p & (L["ont"] == 0)).sum()) * PX, 1),
                on_UNKNOWN_km2=round(float((p & (L["ont"] == 255)).sum()) * PX, 1),
                on_pre_breach_water_km2=round(float((p & L["pre"]).sum()) * PX, 1),
                new_flood_on_land_km2=round(float((p & ~L["pre"] & (L["ont"] != 2)).sum()) * PX, 1),
                EVENT_FLOOD_label_total_km2=round(float((obs & (L["ont"] == 1)).sum()) * PX, 1))


def inhulets_profile(M, L, pred, run, onto="v003_A"):
    """How far up the Inhulets the predicted flood reaches: per 2 km northing band inside the valley rectangle,
    predicted flood on land (not pre-breach water) and the EVENT_FLOOD label area."""
    R = rect_mask(M, CUT_RECTS["inhulets_valley"]) & L["owned"] & L["has"]
    gy = M["y1"] - 10.0 * (np.arange(M["ny"]) + 0.5)
    rows = []
    for y in np.arange(5180000.0, M["y1"], 2000.0):
        band = R & ((gy >= y) & (gy < y + 2000))[:, None]
        if not band.any():
            continue
        p = pred & band
        rows.append(dict(run=run, ontology=onto, northing_km=y / 1e3, observed_km2=round(float(band.sum()) * PX, 2),
                         predicted_km2=round(float(p.sum()) * PX, 2),
                         predicted_on_pre_water_km2=round(float((p & L["pre"]).sum()) * PX, 2),
                         predicted_new_on_land_km2=round(float((p & ~L["pre"] & (L["ont"] != 2)).sum()) * PX, 2),
                         EVENT_FLOOD_label_km2=round(float((band & (L["ont"] == 1)).sum()) * PX, 2)))
    return rows


def mosaic_map(M, L, pred, run, thr, cut, fp):
    ds = lambda a: a[::DS, ::DS]
    st = np.zeros((M["ny"], M["nx"]), "u1"); st[L["owned"] & L["has"]] = 1
    st[L["owned"] & L["has"] & (L["ont"] == 2)] = 2
    st[pred & L["owned"] & L["has"]] = 3
    st[pred & L["owned"] & L["has"] & cut] = 4
    cm = ListedColormap(["#ffffff", "#efece6", "#b9c7d6", RUN_COLOR[run], "#eda100"])
    ext = [M["x0"] / 1e3, M["x1"] / 1e3, M["y0"] / 1e3, M["y1"] / 1e3]
    fig, ax = plt.subplots(figsize=(11, 11 * M["ny"] / M["nx"] + 1.5), constrained_layout=True)
    ax.imshow(ds(st), cmap=cm, vmin=-0.5, vmax=4.5, extent=ext, interpolation="nearest")
    if fp is not None:
        ax.contour(np.linspace(ext[0], ext[1], ds(fp).shape[1]), np.linspace(ext[3], ext[2], ds(fp).shape[0]),
                   ds(fp).astype(float), levels=[0.5], colors="#52514e", linewidths=0.5)
    for nm, (x0, y0, x1, y1) in CUT_RECTS.items():
        ax.add_patch(Rectangle((x0 / 1e3, y0 / 1e3), (x1 - x0) / 1e3, (min(y1, M["y1"]) - y0) / 1e3, fill=False,
                               ec="#e34948", lw=1.0, ls="--"))
    a = lambda m: float(m.sum()) * PX
    ax.set_title(f"Dam -> liman (B1 u B2, one pixel once) -- {run}, thr {thr:.2f}\n"
                 f"predicted flood: Dnipro corridor {a(pred & L['has'] & L['owned'] & ~cut):,.0f} km²  ·  "
                 f"inside the Inhulets / terrace cut rectangles {a(pred & L['has'] & L['owned'] & cut):,.0f} km²  ·  "
                 f"unobserved (no S1 event) {a(L['owned'] & ~L['has']):,.0f} km²", fontsize=9, loc="left")
    ax.set_xlabel("UTM 36N easting, km", fontsize=8); ax.set_ylabel("northing, km", fontsize=8); ax.tick_params(labelsize=7)
    ax.set_aspect("equal")
    ax.legend(handles=[Patch(fc=RUN_COLOR[run], label="predicted flood, Dnipro corridor"),
                       Patch(fc="#eda100", label="predicted flood inside the cut rectangles (Inhulets valley / terraces)"),
                       Patch(fc="#b9c7d6", label="REFERENCE_WATER (recurrent May-2023 S1 water), not predicted"),
                       Patch(fc="#efece6", label="S1 event observed, not predicted"),
                       Patch(fc="#ffffff", ec="#c3c2b7", label="no S1 event / outside frames"),
                       Patch(fc="none", ec="#e34948", ls="--", label="p42 CUT_RECTS (not Dnipro floodplain)"),
                       Patch(fc="none", ec="#52514e", label="p42 terrain-eligible floodplain (SWOT-DNIPRO)")],
              loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=2, fontsize=7, frameon=False)
    fig.savefig(FIG / f"mosaic_dam_to_liman_{run}.png", dpi=110, bbox_inches="tight"); plt.close(fig)


def frame_compare(M, L, preds, cut):
    """Per frame: the map runs side by side in the same style, each on its own label version's ontology."""
    ds = lambda a: a[::DS, ::DS]
    for f in FRAMES:
        r, c = M["off"][f]; G = M["G"][f]; sl = (slice(r, r + G["ny"]), slice(c, c + G["nx"]))
        ext = [G["transform"].c / 1e3, (G["transform"].c + 10 * G["nx"]) / 1e3,
               (G["transform"].f - 10 * G["ny"]) / 1e3, G["transform"].f / 1e3]
        fig, axs = plt.subplots(1, len(preds), figsize=(5.5 * len(preds), 5.5 * G["ny"] / G["nx"] + 1.6),
                                constrained_layout=True)
        for ax, (run, (pred, thr)) in zip(np.atleast_1d(axs), preds.items()):
            Lr = run_layers(L, run)[0]                                   # each panel on its own label version's ontology
            st = np.zeros((M["ny"], M["nx"]), "u1"); st[Lr["has"]] = 1; st[Lr["has"] & (Lr["ont"] == 2)] = 2
            st[pred & L["has"]] = 3; st[pred & L["has"] & cut] = 4
            cm = ListedColormap(["#ffffff", "#efece6", "#b9c7d6", RUN_COLOR[run], "#eda100"])
            ax.imshow(ds(st[sl]), cmap=cm, vmin=-0.5, vmax=4.5, extent=ext, interpolation="nearest")
            for nm, (x0, y0, x1, y1) in CUT_RECTS.items():
                ax.add_patch(Rectangle((x0 / 1e3, y0 / 1e3), (x1 - x0) / 1e3, (min(y1, M["y1"]) - y0) / 1e3,
                                       fill=False, ec="#e34948", lw=0.8, ls="--"))
            ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal")
            own = np.zeros((M["ny"], M["nx"]), bool); own[sl] = True
            a = lambda m: float((m & own & L["has"]).sum()) * PX
            ax.set_title(f"{f} -- {run} (thr {thr:.2f})\nDnipro corridor {a(pred & ~cut):,.0f} km² · "
                         f"cut rectangles {a(pred & cut):,.0f} km² (whole frame incl. overlap)", fontsize=9, loc="left")
            ax.set_xlabel("UTM 36N easting, km", fontsize=7); ax.set_ylabel("northing, km", fontsize=7); ax.tick_params(labelsize=6)
        fig.legend(handles=[Patch(fc="#7f7f7f", label="predicted flood (arm colour)"),
                            Patch(fc="#eda100", label="predicted flood inside cut rectangles"),
                            Patch(fc="#b9c7d6", label="REFERENCE_WATER, not predicted"),
                            Patch(fc="#efece6", label="observed, not predicted"), Patch(fc="#ffffff", ec="#c3c2b7", label="no S1 event"),
                            Patch(fc="none", ec="#e34948", ls="--", label="p42 CUT_RECTS")],
                   loc="lower center", ncol=3, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.03))
        fig.savefig(FIG / f"{f}_flood_map_compare.png", dpi=110, bbox_inches="tight"); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", default=["U2_B1B2_v1", "U2_B1B2_v003A", "U2b_B1B2_v003A"])
    ap.add_argument("--map-runs", nargs="+", default=["U2_B1B2_v1", "U2b_B1B2_v003A"])
    a = ap.parse_args()
    FIG.mkdir(parents=True, exist_ok=True)
    M = mosaic_grid(); L = load_layers(M)
    cut = np.zeros((M["ny"], M["nx"]), bool)
    for r in CUT_RECTS.values():
        cut |= rect_mask(M, r)
    fp, fp_src = floodplain_domain(M)
    regions = {"ALL_B1uB2": np.ones(cut.shape, bool), "DNIPRO_CORRIDOR": ~cut, "CUT_RECTS_total": cut,
               "INHULETS_VALLEY_rect": rect_mask(M, CUT_RECTS["inhulets_valley"]),
               "WEST_OF_MOUTH_rect": rect_mask(M, CUT_RECTS["west_of_inhulets_mouth"]),
               "TERRACE_NE_rect": rect_mask(M, CUT_RECTS["terrace_fragments_ne"])}
    if fp is not None:
        regions["P42_FLOODPLAIN_DOMAIN"] = fp; regions["DNIPRO_CORRIDOR_outside_p42_domain"] = ~cut & ~fp
    rows, prof, preds = [], [], {}
    for run in a.runs:
        pred, thr = load_pred(M, run); preds[run] = (pred, thr); Lr, onto = run_layers(L, run)
        for nm, reg in regions.items():
            rows.append(summarise(Lr, pred, reg, nm, run, thr, onto))
        prof += inhulets_profile(M, Lr, pred, run, onto)
        if run in a.map_runs:
            mosaic_map(M, Lr, pred, run, thr, cut, fp)
    T = CFG.TABLES
    S = pd.DataFrame(rows); S.to_csv(T / "p92_flood_area_dam_to_liman.csv", index=False)
    Pf = pd.DataFrame(prof); Pf.to_csv(T / "p92_inhulets_profile.csv", index=False)
    (T / "p92_flood_area_manifest.json").write_text(json.dumps(dict(
        cut_rects=CUT_RECTS, cut_rects_source="SWOT-DNIPRO scripts/p42_below_dam_floodplain.py CUT_RECTS (2026-09-19)",
        pre_water_rule=f"labels.tif pre_water_frac >= {PRE_WATER_PCT}", floodplain_domain=fp_src, owner_rule="B2 owns overlap",
        meaning="predicted flood = U-Net score >= frozen validation threshold; agreement with weak labels, not accuracy"),
        indent=1))
    frame_compare(M, L, {r: preds[r] for r in a.map_runs}, cut)
    pd.set_option("display.width", 250)
    print(S[S.region.isin(["ALL_B1uB2", "DNIPRO_CORRIDOR", "INHULETS_VALLEY_rect", "P42_FLOODPLAIN_DOMAIN"])].to_string(index=False))
    print(Pf[Pf.run == a.runs[-1]].to_string(index=False))
    print(f"-> tables/p92_*, {FIG.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
