from __future__ import annotations

import json

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from lib import BASEMAPS, CS, DATA, FM6, S2RGB_TEXT, SATMAP_KINDS, SATMAPS, T, base_map, basemap_index, caption, figure, header, layers, opt, persist, raw, refs, session, table

st.set_page_config(page_title="Surface context", layout="wide")
header("Surface context: RF20 PRE-event surface classification of the lower Dnipro (frames B1 + B2)",
       "random forest on PRE-event Sentinel-2 composites, trained on ESA WorldCover 2021; agreement with the training reference, not validation; not flood detection")
session("ctx_")

REV = "_rev2" if (T / "p73_rf20_rev2_manifest.json").exists() else ""       # the RF20 in use: rev 2 after the review (F08)
QA = T / f"p73_rf20{REV}_qa"
man = json.loads((T / f"p73_rf20{REV}_manifest.json").read_text()) if (T / f"p73_rf20{REV}_manifest.json").exists() else {}

# ---- the map --------------------------------------------------------------------------------------------------------
st.subheader("RF20 surface classes — map")
L = layers(); rf = next((l for l in L["layers"] if l["id"] == "rf_p73"), None)
if rf:
    c1, c2 = st.columns([3, 1])
    with c2:
        op = st.slider("opacity", 0.2, 1.0, step=0.05, **opt("ctx_op", value=0.8))
        show_fp = st.checkbox("terrain-eligible floodplain outline", **opt("ctx_fp", value=True))
        basemap = st.radio("basemap", list(BASEMAPS), **opt("ctx_basemap", list(BASEMAPS), index=basemap_index()))
        st.markdown("**Legend** (area as mapped on the 4326 overlay)")
        for k, lab in rf["legend"].items():
            st.markdown(f"<span style='display:inline-block;width:14px;height:14px;background:{rf['palette'][k]};border:1px solid #999'></span> {lab.replace('_', ' ').lower()} — {rf['area_km2_by_class'].get(k, '')} km²", unsafe_allow_html=True)
    with c1:
        m = base_map([46.72, 32.85], 9, basemap)
        folium.raster_layers.ImageOverlay(str(DATA / rf["file"]), bounds=rf["bounds"], opacity=op, name="RF20 classes", interactive=False, zindex=5).add_to(m)
        ctx = DATA / "context" / "frames_and_points.geojson"
        if ctx.exists():
            folium.GeoJson(json.loads(ctx.read_text()), name="frames B1/B2, gauge, dam", style_function=lambda f: dict(color="#4a3aa7", weight=1.2, fill=False),
                           tooltip=folium.GeoJsonTooltip(fields=["name"])).add_to(m)
        fp = DATA / "context" / "p42_floodplain.geojson"
        if show_fp and fp.exists():
            folium.GeoJson(json.loads(fp.read_text()), name="p42 floodplain", style_function=lambda f: dict(color="#2a78d6", weight=1, fill=False)).add_to(m)
        folium.LayerControl(collapsed=True).add_to(m)
        st_folium(m, use_container_width=True, height=560, returned_objects=[])
else:
    st.info("RF20 layer not rendered (p98)")

# ---- Sentinel-2 true colour, every date of the archive ---------------------------------------------------------------
st.subheader("Sentinel-2 true colour — every date of the archive over the lower Dnipro")
S2RGB = sorted([l for l in L["layers"] if l["group"] == "s2_truecolour"], key=lambda l: l["id"])
if S2RGB:
    by_date = {l["id"].replace("s2_truecolour_", ""): l for l in S2RGB}; dates = sorted(by_date); by_id = {l["id"]: l for l in L["layers"]}
    years = sorted({d[:4] for d in dates})
    c1, c2 = st.columns([3, 1])
    with c2:
        yr = st.selectbox("year", ["all"] + years, **opt("ctx_year", ["all"] + years, index=(["all"] + years).index("2023") if "2023" in years else 0))
        opts = [d for d in dates if yr == "all" or d.startswith(yr)]
        default = "2023-06-08" if "2023-06-08" in opts else opts[-1]
        d = st.select_slider("date", options=opts, **opt("ctx_date", opts, value=default), format_func=lambda x: f"{x} · clear {by_date[x].get('clear_share', 0):.0%}")
        e = by_date[d]
        st.markdown(f"**{d}** — tiles {', '.join(e.get('tiles', []))}; {e.get('note', '')}")
        rgb_basemap = st.radio("basemap under the image", list(BASEMAPS), **opt("ctx_rgb_basemap", list(BASEMAPS), index=basemap_index()))
        ov_rf = st.checkbox("RF20 surface classes", **opt("ctx_rgb_rf", value=False)); ov_fp = st.checkbox("terrain-eligible floodplain outline", **opt("ctx_rgb_fp", value=True))
        ov_s2w = st.checkbox(f"S2 water of {d}", **opt("ctx_rgb_s2w", value=False)) if f"s2_water_{d}" in by_id else False
        s1_dates = sorted(l["id"].replace("s1_new_", "") for l in L["layers"] if l["group"] == "s1_daily")
        near = min(s1_dates, key=lambda x: abs(pd.Timestamp(x) - pd.Timestamp(d))) if s1_dates else None
        ov_s1 = st.checkbox(f"S1 new water of {near} (nearest radar date)", **opt("ctx_rgb_s1", value=False)) if near and abs((pd.Timestamp(near) - pd.Timestamp(d)).days) <= 6 else False
        ov_op = st.slider("overlay opacity", 0.2, 1.0, step=0.05, **opt("ctx_rgb_op", value=0.7))
        st.caption(S2RGB_TEXT + f". Rendered {len(dates)} dates of the archive; dates with < 2 % clear sky are not rendered.")
    with c1:
        m = base_map([46.72, 32.85], 9, rgb_basemap)
        folium.raster_layers.ImageOverlay(str(DATA / e["file"]), bounds=e["bounds"], opacity=1.0, name=f"Sentinel-2 {d}", interactive=False, cross_origin=False, zindex=2).add_to(m)
        if ov_rf and rf:
            folium.raster_layers.ImageOverlay(str(DATA / rf["file"]), bounds=rf["bounds"], opacity=ov_op, name="RF20 classes", interactive=False, zindex=5).add_to(m)
        if ov_s2w:
            l = by_id[f"s2_water_{d}"]; folium.raster_layers.ImageOverlay(str(DATA / l["file"]), bounds=l["bounds"], opacity=ov_op, name=f"S2 water {d}", interactive=False, zindex=6).add_to(m)
        if ov_s1:
            l = by_id[f"s1_new_{near}"]; folium.raster_layers.ImageOverlay(str(DATA / l["file"]), bounds=l["bounds"], opacity=ov_op, name=f"S1 new water {near}", interactive=False, zindex=6).add_to(m)
        fp = DATA / "context" / "p42_floodplain.geojson"
        if ov_fp and fp.exists():
            folium.GeoJson(json.loads(fp.read_text()), name="p42 floodplain", style_function=lambda f: dict(color="#2a78d6", weight=1, fill=False)).add_to(m)
        folium.LayerControl(collapsed=True).add_to(m)
        st_folium(m, use_container_width=True, height=560, returned_objects=[], key="rgb_map")
else:
    st.info("Sentinel-2 true-colour dates not rendered (p97c, then p98 --only context)")

# ---- satellite maps: classified indices and radar before / after the breach -------------------------------------------
st.subheader("Satellite maps: classified indices and radar before and after the breach (p95zm; display classes, not a classifier)")
c1, c2 = st.columns([1, 3])
with c1:
    zone = st.radio("zone", list(SATMAPS), **opt("ctx_sat_zone", list(SATMAPS), index=0), format_func=lambda z: SATMAPS[z])
    kind = st.selectbox("map", list(SATMAP_KINDS), **opt("ctx_sat_kind", list(SATMAP_KINDS), index=0))
    st.caption("Sentinel-2: per-cell median of the clear observations of each period (normal year May–June 2022; the last period before the breach; "
               "recession 16–30 June 2023; July 2023) in the display bins of the reservoir maps. The peak (7–9 June) has no usable optical view "
               "(8 June: 26 % of the delta, 12 % of the floodway clear) and is shown with Sentinel-1 VV on orbit 14. Black line = event extent 7 June. "
               "Evidence of the pre-event state of the reed beds (T12i–T12m); contains modified Copernicus Sentinel data 2022–2023.")
with c2:
    stem = SATMAP_KINDS[kind]
    p = FM6 / (f"p95z_{zone}_indices.png" if stem == "p95z" else f"p95zm_{zone}_{stem}.png")
    if p.exists():
        st.image(str(p), width="stretch")
    else:
        st.info(f"{p.name} not rendered (p95zm)")
st.markdown("**Sentinel-1 new dark water by date (FigS19)** — what the radar sees on the day it looks: new dark water minus the pre-breach water, with the reconstruction of the same day as a line.")
figure("FigS19")

# ---- RF surface classes by date (p102): every Sentinel-2 date of the archive, the pool included ----------------------
st.subheader("RF surface classes by date (p102): every Sentinel-2 date of the archive, the reservoir included")
st.caption("The per-date counterpart of RF20: a random forest on the seven indices of ONE date (WorldCover 2021 as the weak target; the same nine classes), "
           "so that every observed date of 2017–2026 has a class map — the drained reservoir bed of 2024–2026 included, which no pre-event composite covers. "
           "Land-cover classes (a bare field in winter is still cropland); the per-date physical state is the k10e rule map of the same stack. "
           "A product for the hydraulic-model work (Papers 4–5), not a result of Paper 3; agreement with WorldCover is never accuracy.")
try:
    A = raw("p102_rf_date_class_area.csv"); A["t"] = pd.to_datetime(A.date); I = raw("p102_rf_date_inventory.csv")
    RFL = [l for l in L["layers"] if l["group"] in ("s2_rf", "reservoir_s2_rf")]; pal = RFL[0]["palette"] if RFL else {}; leg = RFL[0]["legend"] if RFL else {}
    ZL = {"ZONE_1_KAKHOVKA_LOWER_DNIPRO": "Kakhovka pool (pre-breach pool polygon)", "ZONE_4_DAM_TO_KHERSON_FLOODWAY": "floodway dam → Kherson", "ZONE_2_KHERSON_DELTA": "Kherson delta", "ZONE_3_DNIPRO_BUG_ESTUARY": "Dnipro–Bug estuary"}
    c1, c2 = st.columns([1, 3])
    with c1:
        zsel = st.selectbox("zone", list(ZL), **opt("ctx_rf_zone", list(ZL), index=0), format_func=lambda z: ZL[z])
        minobs = st.slider("minimum observed share of the zone / pool", 0.2, 0.9, step=0.1, **opt("ctx_rf_minobs", value=0.5))
        iz = I[I.zone == zsel]; st.markdown(f"**{len(iz)} dates** with a class map; per year: " + ", ".join(f"{y}: {n}" for y, n in iz.groupby("year").size().items()))
        st.caption("Rasters (20 m, GeoTIFF class + probability per date) live in the bulk data root (rf_by_date/<ZONE>/); the dashboard renders the best-observed date of each month.")
    with c2:
        st_ = "POOL_PREBREACH" if zsel.startswith("ZONE_1") else "ZONE"
        az = A[(A.zone == zsel) & (A.stratum == st_) & (A.observed_share >= minobs)].sort_values("t")
        cols = [c for c in az.columns if c.endswith("_km2")]
        if len(az) >= 2:
            tot = az[cols].sum(axis=1).replace(0, float("nan")); f = go.Figure()
            code = {v: k for k, v in leg.items()}
            for c in cols:
                nm = c[:-4]; f.add_trace(go.Bar(x=az.t, y=az[c] / tot * 100, name=nm.replace("_", " ").lower(), marker_color=pal.get(code.get(nm, ""), "#999"), hovertemplate="%{x|%Y-%m-%d}: %{y:.0f} %"))
            f.add_vline(x=pd.Timestamp("2023-06-06").timestamp() * 1000, line=dict(color="#e34948", dash="dash", width=1))
            f.update_layout(barmode="stack", height=360, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="share of the observed cells, %", title=f"RF classes over time — {ZL[zsel]} ({len(az)} dates observing ≥ {minobs:.0%})", legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(f, width="stretch")
        else:
            st.info("fewer than two dates pass the observed-share filter")
    fz = CS / "figures" / "p102" / f"{zsel}_rf_by_date.png"
    if fz.exists():
        with st.expander(f"map panels: the best-observed date of each quarter, {ZL[zsel]}", expanded=False):
            st.image(str(fz), width="stretch")
    rl = sorted(l["id"] for l in RFL if l["group"] == ("reservoir_s2_rf" if zsel.startswith("ZONE_1") else "s2_rf"))
    if rl:
        c1, c2 = st.columns([3, 1])
        with c2:
            rid = st.select_slider("rendered date", options=rl, **opt("ctx_rf_date", rl, value=rl[-1]), format_func=lambda x: x.split("_")[-1])
            rb = st.radio("basemap", list(BASEMAPS), **opt("ctx_rf_basemap", list(BASEMAPS), index=basemap_index()))
            rop = st.slider("opacity", 0.2, 1.0, step=0.05, **opt("ctx_rf_op", value=0.75))
            lr = by_id[rid]; st.caption(lr.get("note", ""))
            for k, lab in lr["legend"].items():
                st.markdown(f"<span style='display:inline-block;width:14px;height:14px;background:{lr['palette'][k]};border:1px solid #999'></span> {lab.replace('_', ' ').lower()} — {lr['area_km2_by_class'].get(k, '')} km²", unsafe_allow_html=True)
        with c1:
            ctr = [47.3, 34.3] if zsel.startswith("ZONE_1") else [46.72, 32.85]
            m = base_map(ctr, 9, rb); folium.raster_layers.ImageOverlay(str(DATA / lr["file"]), bounds=lr["bounds"], opacity=rop, name=rid, interactive=False, zindex=5).add_to(m)
            folium.LayerControl(collapsed=True).add_to(m); st_folium(m, use_container_width=True, height=520, returned_objects=[], key="ctx_rf_map")
    else:
        st.info("RF-by-date layers not rendered (p98 --only rf_date)")
    st.markdown(f"<small>Classes and areas of every date: `tables/p102_rf_date_class_area.csv`; metrics (spatial-block CV and the 2023 hold-out, both variants): `tables/p102_rf_date_metrics.csv`.</small>", unsafe_allow_html=True)
except FileNotFoundError:
    st.info("RF classes by date not built (workflows/m6/p102_rf_surface_by_date.py)")

# ---- class areas ----------------------------------------------------------------------------------------------------
ca = T / f"p73_rf20{REV}_class_area.csv"
if ca.exists():
    A = pd.read_csv(ca); A = A[A.km2 > 0]
    pal = rf["palette"] if rf else {}; code = {v: k for k, v in rf["legend"].items()} if rf else {}
    st.subheader("Class areas per frame (20 m native grid)")
    c1, c2 = st.columns([2, 1])
    with c1:
        f = go.Figure()
        for cls in A.p73_class.unique():
            q = A[A.p73_class == cls]
            f.add_trace(go.Bar(x=q.frame, y=q.km2, name=cls.replace("_", " ").lower(), marker_color=pal.get(code.get(cls, ""), "#999")))
        f.update_layout(barmode="stack", height=340, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="km²", title="RF20 classes, B1 (dam → Kherson) and B2 (Kherson delta)")
        st.plotly_chart(f, width="stretch")
    with c2:
        P = A.pivot_table(index="p73_class", columns="frame", values="km2", aggfunc="sum").fillna(0)
        P["B1 + B2"] = P.sum(axis=1); st.dataframe(P.round(1).sort_values("B1 + B2", ascending=False), width="stretch")
    st.caption("B1 and B2 overlap near Kherson, so B1 + B2 double-counts the overlap. UNCERTAIN = top-class probability < 0.5 (fixed before any result).")

# ---- method ---------------------------------------------------------------------------------------------------------
st.subheader("Method")
rfp = man.get("random_forest", {}); sp = man.get("split", {}); tg = man.get("target", {})
feat = man.get("features", {}); feat = feat.get("order", []) if isinstance(feat, dict) else []
st.markdown(f"""
- **Classifier:** random forest (Breiman 2001) — {rfp.get('n_estimators', 200)} trees, min samples per leaf {rfp.get('min_samples_leaf', 5)}, class weight `{rfp.get('class_weight', 'balanced_subsample')}`, seed {rfp.get('random_state', '')}.
- **Predictors (PRE-event only, enforced at read time):** Sentinel-2 composites of the 7 indices (NDVI, NDWI, MNDWI, NDMI, BSI, AWEIsh, NDTI) as median / min / max over the pre-event window{f' — {len(feat)} features' if feat else ''}. No flood label, S1 change, HAND or event band can enter.
- **Target:** {tg.get('source', 'ESA WorldCover 2021')} (Zanaga et al. 2022; ~75 % global overall accuracy — a *weak* reference); a cell gets a target only if all four half-cell-shifted WorldCover cells agree, then PRE-S2 consistency filters.
- **Evaluation:** {sp.get('cv', '5-fold spatial-block CV')} on {int(sp.get('block_m', 5000) / 1000)} km blocks (Roberts et al. 2017; Valavi et al. 2019) plus transfer {sp.get('transfer', 'B1→B2, B2→B1')}; {sp.get('sample_per_class_per_frame', 30000)} samples per class and frame.
- **Status:** {man.get('status', 'P73_RF20_FROZEN')} — used as *context* (why the sensor and the reconstruction disagree), never in flood-label construction.
""")
if feat:
    with st.expander(f"feature list ({len(feat)})"):
        st.code(", ".join(feat))
refs(["rf", "Tucker_1979", "McFeeters_1996", "Xu_2006", "Wilson_Sader_2002", "Rikimaru_2002", "Feyisa_2014", "Lacaux_2007"], "📚 Literature: random forest, WorldCover, spatial CV and the 7 predictor indices")

# ---- agreement tables -----------------------------------------------------------------------------------------------
st.subheader("Agreement with WorldCover (the training reference)")
st.caption(caption("T09")); st.dataframe(table("T09"), width="stretch", hide_index=True)
figure("FigS04")
c1, c2 = st.columns(2)
with c1:
    st.caption(caption("T10")); st.dataframe(table("T10"), width="stretch", hide_index=True)
with c2:
    st.caption(caption("T10b")); st.dataframe(table("T10b"), width="stretch", hide_index=True)
st.caption(caption("T10c")); st.dataframe(table("T10c"), width="stretch", hide_index=True)
refs(["Olofsson_2014", "Zanaga_2022", "Roberts_2017", "Pohjankukka_2017"], "📚 Literature: accuracy / agreement assessment and blocked validation")

# ---- QA panels ------------------------------------------------------------------------------------------------------
if QA.exists():
    st.subheader(f"Visual QA (p73q, RF20 {'rev 2' if REV else 'rev 1'})")
    v = QA / "QA_VERDICT.md"
    if v.exists():
        with st.expander("QA verdict"):
            st.markdown(v.read_text())
    imgs = sorted(QA.glob("*.png"))
    pick = st.selectbox("QA panel", [p.stem for p in imgs], **opt("ctx_qa", [p.stem for p in imgs], index=0))
    st.image(str(QA / f"{pick}.png"), width="stretch")
    st.caption("B1/B2_classes_vs_worldcover: RF20 against WorldCover per frame; Z1–Z6: zoom panels (disputed fields, flooded fields, reed, Oleshky sands, Kherson built-up, pre-existing water shore).")
persist("ctx_")
