from __future__ import annotations

import json

import folium
import streamlit as st
from streamlit_folium import st_folium

from lib import DATA, header, layers

st.set_page_config(page_title="Maps", layout="wide")
header("Maps: terrain-reconstructed inundation by day, Sentinel-1 by date, U-Net, labels, surface classes",
       "pre-rendered classed overlays (~76 × 80 m); no numeric raster is served")

L = layers(); by_id = {l["id"]: l for l in L["layers"]}
daily = sorted(l for l in by_id if l.startswith("terrain_daily_")); s1d = sorted(l for l in by_id if l.startswith("s1_new_"))
with st.sidebar:
    st.markdown("**Terrain reconstruction**")
    day = st.select_slider("day", options=[d.replace("terrain_daily_", "") for d in daily], value="2023-06-08")
    show_terrain = st.checkbox("show terrain new inundation for this day", True)
    summary = st.selectbox("terrain summary layer", ["none", "terrain_duration", "terrain_max_depth", "terrain_depth_20230608"])
    st.markdown("**Sentinel-1**")
    s1date = st.selectbox("S1 date", ["none"] + [d.replace("s1_new_", "") for d in s1d], index=4)
    s1foot = st.checkbox("S1 valid footprint", False)
    st.markdown("**Other products**")
    unet = st.selectbox("U-Net prediction", ["none", "unet_U2b_v003A", "unet_U2_v1"])
    lab = st.checkbox("labels v003_A (frozen)", False); rf = st.checkbox("RF20 surface classes", False)
    opacity = st.slider("overlay opacity", 0.2, 1.0, 0.75, 0.05)
    st.caption("Terrain layers derive from FABDEM v1.2 (CC BY-NC-SA 4.0) via the seamless DEM; non-commercial use with attribution.")

m = folium.Map(location=[46.68, 32.9], zoom_start=9, tiles="OpenStreetMap", control_scale=True)
def add(lid, op=None, name=None):
    l = by_id[lid]; folium.raster_layers.ImageOverlay(str(DATA / l["file"]), bounds=l["bounds"], opacity=op or opacity, name=name or lid, interactive=False, cross_origin=False, zindex=5).add_to(m)
    return l
legend = []
if rf: legend.append(add("rf_p73", 0.55, "RF20 classes"))
if lab: legend.append(add("labels_v003A", 0.6, "labels v003_A"))
if summary != "none": legend.append(add(summary, opacity, summary))
if s1foot and s1date != "none": add(f"s1_footprint_{s1date}", 0.25, "S1 footprint")
if unet != "none": legend.append(add(unet, opacity, unet))
if s1date != "none": legend.append(add(f"s1_new_{s1date}", opacity, f"S1 new water {s1date}"))
if show_terrain: legend.append(add(f"terrain_daily_{day}", opacity, f"terrain {day}"))
ctx = DATA / "context" / "frames_and_points.geojson"
if ctx.exists():
    folium.GeoJson(json.loads(ctx.read_text()), name="frames, cut rectangles, gauge, dam", style_function=lambda f: dict(color="#e34948" if f["properties"]["kind"] == "cut_rect" else "#4a3aa7", weight=1.2, fill=False, dashArray="4" if f["properties"]["kind"] == "cut_rect" else None),
                   tooltip=folium.GeoJsonTooltip(fields=["name"])).add_to(m)
fp = DATA / "context" / "p42_floodplain.geojson"
if fp.exists():
    folium.GeoJson(json.loads(fp.read_text()), name="p42 terrain-eligible floodplain", style_function=lambda f: dict(color="#2a78d6", weight=1, fill=False)).add_to(m)
folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, use_container_width=True, height=620, returned_objects=[])

st.subheader("Legend")
cols = st.columns(max(len(legend), 1))
for col, l in zip(cols, legend):
    with col:
        st.markdown(f"**{l['id']}**  \n<small>{l['source']}</small>", unsafe_allow_html=True)
        for k, lab_ in l["legend"].items():
            st.markdown(f"<span style='display:inline-block;width:14px;height:14px;background:{l['palette'][k]};border:1px solid #999'></span> {lab_} — {l['area_km2_by_class'].get(k, '')} km² (mapped)", unsafe_allow_html=True)
