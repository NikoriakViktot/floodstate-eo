from __future__ import annotations

import json

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from lib import DATA, T, caption, figure, header, layers, refs, table

st.set_page_config(page_title="Surface context", layout="wide")
header("Surface context: RF20 PRE-event surface classification of the lower Dnipro (frames B1 + B2)",
       "random forest on PRE-event Sentinel-2 composites, trained on ESA WorldCover 2021; agreement with the training reference, not validation; not flood detection")

QA = T / "p73_rf20_qa"
man = json.loads((T / "p73_rf20_manifest.json").read_text()) if (T / "p73_rf20_manifest.json").exists() else {}

# ---- the map --------------------------------------------------------------------------------------------------------
st.subheader("RF20 surface classes — map")
L = layers(); rf = next((l for l in L["layers"] if l["id"] == "rf_p73"), None)
if rf:
    c1, c2 = st.columns([3, 1])
    with c2:
        op = st.slider("opacity", 0.2, 1.0, 0.8, 0.05)
        show_fp = st.checkbox("p42 floodplain outline", True)
        st.markdown("**Legend** (area as mapped on the 4326 overlay)")
        for k, lab in rf["legend"].items():
            st.markdown(f"<span style='display:inline-block;width:14px;height:14px;background:{rf['palette'][k]};border:1px solid #999'></span> {lab.replace('_', ' ').lower()} — {rf['area_km2_by_class'].get(k, '')} km²", unsafe_allow_html=True)
    with c1:
        m = folium.Map(location=[46.72, 32.85], zoom_start=9, tiles="OpenStreetMap", control_scale=True)
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

# ---- class areas ----------------------------------------------------------------------------------------------------
ca = T / "p73_rf20_class_area.csv"
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
    st.subheader("Visual QA (frozen, p73q)")
    v = QA / "QA_VERDICT.md"
    if v.exists():
        with st.expander("QA verdict"):
            st.markdown(v.read_text())
    imgs = sorted(QA.glob("*.png"))
    pick = st.selectbox("QA panel", [p.stem for p in imgs], index=0)
    st.image(str(QA / f"{pick}.png"), width="stretch")
    st.caption("B1/B2_classes_vs_worldcover: RF20 against WorldCover per frame; Z1–Z6: zoom panels (disputed fields, flooded fields, reed, Oleshky sands, Kherson built-up, pre-existing water shore).")
