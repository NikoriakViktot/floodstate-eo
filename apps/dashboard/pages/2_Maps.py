from __future__ import annotations

import json

import folium
import streamlit as st
from streamlit_folium import st_folium

from lib import DATA, INDICES, fmt_ref, header, layers, refs

st.set_page_config(page_title="Maps", layout="wide")
header("Maps: terrain-reconstructed inundation by day, Sentinel-1 by date, U-Net, labels, surface classes, reservoir drawdown",
       "pre-rendered classed overlays (~76 × 80 m); no numeric raster is served")

L = layers(); by_id = {l["id"]: l for l in L["layers"]}
daily = sorted(l for l in by_id if l.startswith("terrain_daily_")); s1d = sorted(l for l in by_id if l.startswith("s1_new_"))
rmod = sorted(l.replace("reservoir_model_", "") for l in by_id if l.startswith("reservoir_model_"))
rs1 = sorted(l.replace("reservoir_s1_", "") for l in by_id if l.startswith("reservoir_s1_"))
rs2 = sorted({l.split("_")[-1] for l in by_id if l.startswith("reservoir_s2_") and not l.startswith("reservoir_s2_water_")})
rs2w = sorted(l.replace("reservoir_s2_water_", "") for l in by_id if l.startswith("reservoir_s2_water_"))
rdep = sorted(l.replace("reservoir_depth_", "") for l in by_id if l.startswith("reservoir_depth_"))
UNET = [u for u in ("unet_U2b_v004", "unet_U2_v004", "unet_U2b_v003A", "unet_U2_v1") if u in by_id]          # v004 canonical; v003_A / v1 history
LABELS = [u for u in ("labels_v004", "labels_v003A") if u in by_id]
S2_LAYERS = ["k10e classes", "water", "NDVI", "NDWI", "MNDWI", "NDMI", "BSI", "AWEIsh", "NDTI"]
VIEWS = {"downstream (dam → liman)": ([46.68, 32.9], 9), "reservoir (Kakhovka pool)": ([47.3, 34.3], 9), "both": ([47.1, 33.6], 8)}
with st.sidebar:
    view = st.radio("zoom to", list(VIEWS), index=0)
    st.markdown("**Terrain reconstruction**")
    day = st.select_slider("day", options=[d.replace("terrain_daily_", "") for d in daily], value="2023-06-08")
    show_terrain = st.checkbox("show terrain new inundation for this day", True)
    by_support = st.checkbox("colour it by water-surface support (direct / extrapolated / weak)", False,
                             help="Distance of the nearest SWOT node: direct <= 3 km, extrapolated 3-10 km, weak > 10 km (operational thresholds); "
                                  "cross-river = Inhulets valley served by a node of another river. The full reconstruction stays the primary product (T11k).")
    summary = st.selectbox("terrain summary layer", ["none", "terrain_duration", "terrain_max_depth", "terrain_depth_20230608"])
    st.markdown("**Sentinel-1**")
    s1date = st.selectbox("S1 date", ["none"] + [d.replace("s1_new_", "") for d in s1d], index=4)
    s1foot = st.checkbox("S1 valid footprint", False)
    st.markdown("**Other products**")
    hist = lambda x: x + (" (history)" if ("v003A" in x or x.endswith("_v1")) else "")
    unet = st.selectbox("U-Net prediction (canonical labels v004, first training seed)", ["none"] + UNET, format_func=hist)
    lab = st.selectbox("weak labels", ["none"] + LABELS, format_func=hist); rf = st.checkbox("RF20 surface classes", False)
    if rmod:
        st.markdown("**Reservoir drawdown**")
        rday = st.select_slider("model day (p95f surface over the DEM)", options=["none"] + rmod, value="none")
        rexp = st.checkbox("day the bed fell dry (model 6-13 June + Sentinel-2 20 June)", False)
        rdd = st.selectbox("water depth in the pool (model)", ["none"] + rdep) if rdep else "none"
        rs1date = st.selectbox("S1 date (VH dark surface)", ["none"] + rs1)
        s2l = st.selectbox("S2 layer", ["none"] + S2_LAYERS)
        s2opts = rs2w if s2l == "water" else rs2
        rs2date = st.selectbox("S2 date", s2opts, index=min(1, len(s2opts) - 1)) if s2l != "none" and s2opts else None
    opacity = st.slider("overlay opacity", 0.2, 1.0, 0.75, 0.05)
    st.caption("Terrain layers derive from FABDEM v1.2 (CC BY-NC-SA 4.0) via the seamless DEM; non-commercial use with attribution.")

m = folium.Map(location=VIEWS[view][0], zoom_start=VIEWS[view][1], tiles="OpenStreetMap", control_scale=True)
def add(lid, op=None, name=None):
    l = by_id[lid]; folium.raster_layers.ImageOverlay(str(DATA / l["file"]), bounds=l["bounds"], opacity=op or opacity, name=name or lid, interactive=False, cross_origin=False, zindex=5).add_to(m)
    return l
legend = []
if rf: legend.append(add("rf_p73", 0.55, "RF20 classes"))
if lab != "none": legend.append(add(lab, 0.6, hist(lab)))
if summary != "none": legend.append(add(summary, opacity, summary))
if s1foot and s1date != "none": add(f"s1_footprint_{s1date}", 0.25, "S1 footprint")
if unet != "none": legend.append(add(unet, opacity, unet))
if s1date != "none": legend.append(add(f"s1_new_{s1date}", opacity, f"S1 new water {s1date}"))
if show_terrain:
    sid = f"support_daily_{day}"
    legend.append(add(sid, opacity, f"support of the new inundation {day}") if by_support and sid in by_id else add(f"terrain_daily_{day}", opacity, f"terrain {day}"))
if rmod:
    if s2l != "none" and rs2date:
        sid = {"k10e classes": f"reservoir_s2_class_{rs2date}", "water": f"reservoir_s2_water_{rs2date}"}.get(s2l, f"reservoir_s2_{s2l}_{rs2date}")
        if sid in by_id:
            legend.append(add(sid, opacity, f"S2 {s2l} {rs2date}"))
    if rs1date != "none": legend.append(add(f"reservoir_s1_{rs1date}", opacity, f"S1 reservoir {rs1date}"))
    if rdd != "none": legend.append(add(f"reservoir_depth_{rdd}", opacity, f"pool water depth {rdd} (model)"))
    if rexp: legend.append(add("reservoir_exposed_day", opacity, "day the bed fell dry"))
    if rday != "none": legend.append(add(f"reservoir_model_{rday}", opacity, f"model pool {rday}"))
rp = DATA / "context" / "reservoir_pool.geojson"
if rp.exists():
    folium.GeoJson(json.loads(rp.read_text()), name="Kakhovka pool before the breach", style_function=lambda f: dict(color="#1b6ca8", weight=1, fill=False, dashArray="3")).add_to(m)
ctx = DATA / "context" / "frames_and_points.geojson"
if ctx.exists():
    folium.GeoJson(json.loads(ctx.read_text()), name="frames, cut rectangles, gauge, dam", style_function=lambda f: dict(color="#e34948" if f["properties"]["kind"] == "cut_rect" else "#4a3aa7", weight=1.2, fill=False, dashArray="4" if f["properties"]["kind"] == "cut_rect" else None),
                   tooltip=folium.GeoJsonTooltip(fields=["name"])).add_to(m)
fp = DATA / "context" / "p42_floodplain.geojson"
if fp.exists():
    folium.GeoJson(json.loads(fp.read_text()), name="p42 terrain-eligible floodplain", style_function=lambda f: dict(color="#2a78d6", weight=1, fill=False)).add_to(m)
gp = DATA / "context" / "gauges.geojson"
if gp.exists():
    fg = folium.FeatureGroup(name="river gauges (Kherson = input; Kalynivske, Mykolaiv = withheld)")
    for f in json.loads(gp.read_text())["features"]:
        lon, lat = f["geometry"]["coordinates"]; withheld = f["properties"]["role"].startswith("withheld")
        folium.CircleMarker([lat, lon], radius=7, color="#0b0b0b", weight=2, fill=True, fill_color="#ffffff" if withheld else "#0b0b0b", fill_opacity=1,
                            tooltip=f"{f['properties']['name']}: {f['properties']['role']}").add_to(fg)
    fg.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, use_container_width=True, height=620, returned_objects=[])

st.subheader("Legend")
cols = st.columns(max(len(legend), 1))
for col, l in zip(cols, legend):
    with col:
        st.markdown(f"**{l['id']}**  \n<small>{l['source']}</small>", unsafe_allow_html=True)
        for k, lab_ in l["legend"].items():
            st.markdown(f"<span style='display:inline-block;width:14px;height:14px;background:{l['palette'][k]};border:1px solid #999'></span> {lab_} — {l['area_km2_by_class'].get(k, '')} km² (mapped)", unsafe_allow_html=True)


def layer_refs(lid: str) -> list:
    """Literature for a map layer id (the method each overlay rests on)."""
    if lid.startswith("reservoir_s2_"):
        part = lid.split("_")[2]
        if part in INDICES:
            return INDICES[part][2] + ["Drusch_2012", "Main-Knorn_2017"]
        return {"class": ["k10e"], "water": ["s2_water"]}.get(part, ["s2_water"])
    for pre, keys in (("reservoir_s1_", ["Otsu_1979", "Twele_2016", "Bioresita_2019", "Torres_2012"]), ("reservoir_", ["reservoir", "Paper1_Nikoriak_2026", "Paper2_Nikoriak_2026"]),
                      ("terrain_", ["terrain", "water_surface"]), ("s1_", ["s1_flood"]), ("unet_", ["Ronneberger_2015", "He_2016", "Iakubovskii_2019", "He_2024", "Maiti_2022"]),
                      ("labels_", ["He_2024", "Maiti_2022", "Apicella_2025", "Bonafilia_2020"]), ("rf_", ["rf"])):
        if lid.startswith(pre):
            return keys
    return []


if legend:
    keys = []
    for l in legend:
        for k in layer_refs(l["id"]):
            if k not in keys:
                keys.append(k)
    refs(keys, "📚 Literature for the layers shown", expanded=True)
    ix = [l["id"].split("_")[2] for l in legend if l["id"].startswith("reservoir_s2_") and l["id"].split("_")[2] in INDICES]
    for i in ix:
        st.markdown(f"**{i}** = `{INDICES[i][0]}` — responds to {INDICES[i][1]}. <small>{' · '.join(fmt_ref(r) for r in INDICES[i][2])}</small>", unsafe_allow_html=True)
