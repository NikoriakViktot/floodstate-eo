from __future__ import annotations

import json

import folium
import streamlit as st
from streamlit_folium import st_folium

from lib import base_map, basemap_index, BASEMAPS, DATA, fmt_ref, header, INDICES, layers, opt, OWN_S2, persist, refs, session, styled_overlay

st.set_page_config(page_title="Maps", layout="wide")
header("Maps: terrain-reconstructed inundation by day, Sentinel-1 by date, U-Net, labels, surface classes, reservoir drawdown",
       "pre-rendered classed overlays (~76 × 80 m); no numeric raster is served")
session("maps_")                                                       # the choices below survive a page switch and a reload (?sid=)

L = layers(); by_id = {l["id"]: l for l in L["layers"]}
daily = sorted(l for l in by_id if l.startswith("terrain_daily_")); s1d = sorted(l for l in by_id if l.startswith("s1_new_")); s2d = sorted(l for l in by_id if l.startswith("s2_water_"))
rmod = sorted(l.replace("reservoir_model_", "") for l in by_id if l.startswith("reservoir_model_"))
rs1 = sorted(l.replace("reservoir_s1_", "") for l in by_id if l.startswith("reservoir_s1_"))
rs2 = sorted({l.split("_")[-1] for l in by_id if l.startswith("reservoir_s2_") and not l.startswith("reservoir_s2_water_")})
rs2w = sorted(l.replace("reservoir_s2_water_", "") for l in by_id if l.startswith("reservoir_s2_water_"))
rdep = sorted(l.replace("reservoir_depth_", "") for l in by_id if l.startswith("reservoir_depth_"))
UNET = [u for u in ("unet_U2b_v004", "unet_U2_v004", "unet_U2b_v003A", "unet_U2_v1") if u in by_id]          # v004 canonical; v003_A / v1 history
LABELS = [u for u in ("labels_v004", "labels_v003A") if u in by_id]
S2_LAYERS = ["k10e classes", "water", "NDVI", "NDWI", "MNDWI", "NDMI", "BSI", "AWEIsh", "NDTI"]
VIEWS = {"downstream (dam → liman)": ([46.68, 32.9], 9), "reservoir (Kakhovka pool)": ([47.3, 34.3], 9), "both": ([47.1, 33.6], 8)}
RFD = sorted(l.replace("s2_rf_", "") for l in by_id if l.startswith("s2_rf_"))                       # p102 RF classes by date, lower Dnipro
RRFD = sorted(l.replace("reservoir_s2_rf_", "") for l in by_id if l.startswith("reservoir_s2_rf_"))     # ... and the pool
with st.sidebar:
    view = st.radio("zoom to", list(VIEWS), **opt("maps_view", list(VIEWS), index=0))
    basemap = st.radio("basemap", list(BASEMAPS), **opt("maps_basemap", list(BASEMAPS), index=basemap_index()), help="Live tiles with their own licences (attribution under the map). "
                       "The paper figures use the project's own Sentinel-2 true colour of June 2022 (overlay below).")
    own_s2 = st.checkbox(OWN_S2["name"], **opt("maps_own_s2", value=False)) if (DATA / OWN_S2["file"]).exists() else False
    st.markdown("**Terrain reconstruction**")
    days = [d.replace("terrain_daily_", "") for d in daily]
    day = st.select_slider("day", options=days, **opt("maps_day", days, value="2023-06-08" if "2023-06-08" in days else days[0]))
    probd = sorted(l.replace("terrain_prob_", "") for l in by_id if l.startswith("terrain_prob_"))
    prob = st.selectbox("inundation probability (Monte-Carlo worlds, key dates)", ["none"] + probd, **opt("maps_prob", ["none"] + probd, index=0),
                        help="Share of the 1000 coherent Monte-Carlo worlds in which the cell is new inundation on the day (p95e cellprob, T12g). "
                             "P >= 0.5 = the median world, the map product of the ensemble; the nominal daily map is one world.") if probd else "none"
    RVIEWS = ["flood only", "flood + support", "support only"]
    rview = st.radio("reconstruction view", RVIEWS, **opt("maps_rview", RVIEWS, index=1),
                     help="flood = reconstructed new water (blue, one physical category). support = its reliability drawn on top: weak "
                          "water-surface support (> 10 km to the nearest SWOT node) as orange hatch, cross-river (Inhulets valley served by a node "
                          "of another river) as red outline, retained water of the memory sensitivity (not in the primary) as grey hatch. "
                          "support only = the solid support classes (direct / extrapolated / weak). Operational thresholds; the full "
                          "reconstruction stays the primary product (T11k).")
    show_terrain = rview != "support only"; by_support = rview == "support only"; with_hatch = rview == "flood + support"
    SUMM = ["none", "terrain_duration", "terrain_max_depth", "terrain_depth_20230608"]
    summary = st.selectbox("terrain summary layer", SUMM, **opt("maps_summary", SUMM, index=0))
    envelope = st.checkbox("full flood mask: envelope of the whole event (p103)", **opt("maps_envelope", value=False),
                           help="Every cell reconstructed as water on at least one day: pre-breach water, normally wet, new inundation of the nominal run, "
                                "of the Monte-Carlo median world only, and marginal (P < 0.5). The input of a hydraulic model; GeoTIFF + GeoJSON in floodplain_dyn/_envelope.") if "terrain_envelope" in by_id else False
    s1env = st.checkbox("Sentinel-1 envelope: dark water on any event date (6-30 June)", **opt("maps_s1env", value=False)) if "s1_envelope" in by_id else False
    st.markdown("**Sentinel-1 / Sentinel-2 masks** (observations to compare with the reconstruction; not observed is not dry)")
    S1O = ["none"] + [d.replace("s1_new_", "") for d in s1d]
    s1date = st.selectbox("S1 date", S1O, **opt("maps_s1date", S1O, index=min(4, len(S1O) - 1)))
    s1foot = st.checkbox("S1 valid footprint", **opt("maps_s1foot", value=False))
    S2O = ["none"] + [d.replace("s2_water_", "") for d in s2d]
    s2date = st.selectbox("S2 date (NDWI > 0 & MNDWI > 0; cloud-free cells only)", S2O, **opt("maps_s2date", S2O, index=0),
                          format_func=lambda d: d if d == "none" else d + ("" if "reliable (" in by_id[f"s2_water_{d}"].get("note", "") else "  (unreliable: < 30 % observed)"))
    s2foot = st.checkbox("S2 valid footprint", **opt("maps_s2foot", value=False))
    st.markdown("**Other products**")
    hist = lambda x: x + (" (history)" if ("v003A" in x or x.endswith("_v1")) else "")
    unet = st.selectbox("U-Net prediction (canonical labels, first training seed)", ["none"] + UNET, **opt("maps_unet", ["none"] + UNET, index=0), format_func=hist)
    lab = st.selectbox("weak labels", ["none"] + LABELS, **opt("maps_labels", ["none"] + LABELS, index=0), format_func=hist)
    rf = st.checkbox("RF20 surface classes (pre-event composites)", **opt("maps_rf", value=False))
    rfdate = st.selectbox("RF surface classes by date, lower Dnipro (p102)", ["none"] + RFD, **opt("maps_rfdate", ["none"] + RFD, index=0),
                          help="A random forest on the seven indices of the date (WorldCover 2021 as the weak target); the best-observed date of each month is rendered. Land-cover classes, not surface state.") if RFD else "none"
    if rmod:
        st.markdown("**Reservoir drawdown**")
        rday = st.select_slider("model day (sloped surface over the DEM)", options=["none"] + rmod, **opt("maps_rday", ["none"] + rmod, value="none"))
        rexp = st.checkbox("day the bed fell dry (model 6-13 June + Sentinel-2 20 June)", **opt("maps_rexp", value=False))
        rdd = st.selectbox("water depth in the pool (model)", ["none"] + rdep, **opt("maps_rdd", ["none"] + rdep, index=0)) if rdep else "none"
        rs1date = st.selectbox("S1 date (VH dark surface)", ["none"] + rs1, **opt("maps_rs1date", ["none"] + rs1, index=0))
        s2l = st.selectbox("S2 layer", ["none"] + S2_LAYERS, **opt("maps_s2l", ["none"] + S2_LAYERS, index=0))
        s2opts = rs2w if s2l == "water" else rs2
        rs2date = st.selectbox("S2 date", s2opts, **opt("maps_rs2date", s2opts, index=min(1, len(s2opts) - 1))) if s2l != "none" and s2opts else None
        rrfdate = st.selectbox("RF surface classes by date, the pool (p102)", ["none"] + RRFD, **opt("maps_rrfdate", ["none"] + RRFD, index=0),
                               help="The pool and 1 km around it; the best-observed date of each month with >= 50 % of the pool observed.") if RRFD else "none"
    opacity = st.slider("overlay opacity", 0.2, 1.0, step=0.05, **opt("maps_opacity", value=0.75))
    st.caption("Terrain layers derive from FABDEM v1.2 (CC BY-NC-SA 4.0) via the seamless DEM; non-commercial use with attribution.")
persist("maps_")

m = base_map(VIEWS[view][0], VIEWS[view][1], basemap)
if own_s2:
    grid = L["grid"]; folium.raster_layers.ImageOverlay(str(DATA / OWN_S2["file"]), bounds=grid["bounds"], opacity=1.0, name=OWN_S2["name"], interactive=False, cross_origin=False, zindex=2).add_to(m)
def add(lid, op=None, name=None):
    l = by_id[lid]; folium.raster_layers.ImageOverlay(str(DATA / l["file"]), bounds=l["bounds"], opacity=op or opacity, name=name or lid, interactive=False, cross_origin=False, zindex=5).add_to(m)
    return l
legend = []
if rf: legend.append(add("rf_p73", 0.55, "RF20 classes"))
if rfdate != "none": legend.append(add(f"s2_rf_{rfdate}", 0.6, f"RF classes {rfdate}"))
if lab != "none": legend.append(add(lab, 0.6, hist(lab)))
if envelope: legend.append(add("terrain_envelope", opacity, "full flood mask (envelope)"))
if s1env: legend.append(add("s1_envelope", opacity, "S1 envelope (event dates)"))
if summary != "none": legend.append(add(summary, opacity, summary))
if s1foot and s1date != "none": add(f"s1_footprint_{s1date}", 0.25, "S1 footprint")
if unet != "none": legend.append(add(unet, opacity, unet))
if s1date != "none": legend.append(add(f"s1_new_{s1date}", opacity, f"S1 new water {s1date}"))
if s2foot and s2date != "none": add(f"s2_footprint_{s2date}", 0.25, "S2 footprint")
if s2date != "none": legend.append(add(f"s2_water_{s2date}", opacity, f"S2 water {s2date}"))
if prob != "none": legend.append(add(f"terrain_prob_{prob}", opacity, f"P(new inundation) {prob}"))
sid = f"support_daily_{day}"
if by_support and sid in by_id:
    legend.append(add(sid, opacity, f"support of the new inundation {day}"))
elif show_terrain:
    legend.append(add(f"terrain_daily_{day}", opacity, f"terrain {day}"))
    if with_hatch and sid in by_id:
        sp = by_id[sid]; rgba = styled_overlay(sp["file"], (DATA / sp["file"]).stat().st_mtime)
        folium.raster_layers.ImageOverlay(rgba, bounds=sp["bounds"], opacity=1.0, name=f"support pattern {day}", interactive=False, cross_origin=False,
                                          mercator_project=False, pixelated=True, zindex=6).add_to(m)
if rmod:
    if s2l != "none" and rs2date:
        sid = {"k10e classes": f"reservoir_s2_class_{rs2date}", "water": f"reservoir_s2_water_{rs2date}"}.get(s2l, f"reservoir_s2_{s2l}_{rs2date}")
        if sid in by_id:
            legend.append(add(sid, opacity, f"S2 {s2l} {rs2date}"))
    if rs1date != "none": legend.append(add(f"reservoir_s1_{rs1date}", opacity, f"S1 reservoir {rs1date}"))
    if rrfdate != "none": legend.append(add(f"reservoir_s2_rf_{rrfdate}", opacity, f"RF classes, pool {rrfdate}"))
    if rdd != "none": legend.append(add(f"reservoir_depth_{rdd}", opacity, f"pool water depth {rdd} (model)"))
    if rexp: legend.append(add("reservoir_exposed_day", opacity, "day the bed fell dry"))
    if rday != "none": legend.append(add(f"reservoir_model_{rday}", opacity, f"model pool {rday}"))
rp = DATA / "context" / "reservoir_pool.geojson"
if rp.exists():
    folium.GeoJson(json.loads(rp.read_text()), name="Kakhovka pool before the breach", style_function=lambda f: dict(color="#1b6ca8", weight=1, fill=False, dashArray="3")).add_to(m)
ctx = DATA / "context" / "frames_and_points.geojson"
if ctx.exists():
    folium.GeoJson(json.loads(ctx.read_text()), name="frames, reporting regions, gauge, dam", style_function=lambda f: dict(color="#e34948" if f["properties"]["kind"] in ("reporting_region", "cut_rect") else "#4a3aa7", weight=1.2, fill=False, dashArray="4" if f["properties"]["kind"] in ("reporting_region", "cut_rect") else None),
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
st.caption(BASEMAPS[basemap]["text"] + ((" · " + OWN_S2["text"]) if own_s2 else ""))
if show_terrain and with_hatch:
    st.markdown("<small><b>support pattern over the blue new water:</b> "
                "<span style='display:inline-block;width:14px;height:14px;background:repeating-linear-gradient(45deg,#eda100 0 3px,transparent 3px 8px);border:1px solid #999'></span> weak (> 10 km to the nearest SWOT node) · "
                "<span style='display:inline-block;width:14px;height:14px;border:2px solid #e34948'></span> cross-river (Inhulets valley, node of another river) · "
                "<span style='display:inline-block;width:14px;height:14px;background:repeating-linear-gradient(45deg,#78808a 0 3px,transparent 3px 8px);border:1px solid #999'></span> retained water (memory sensitivity; not in the primary)</small>",
                unsafe_allow_html=True)

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
    for pre, keys in (("reservoir_s1_", ["Otsu_1979", "Twele_2016", "Bioresita_2019", "Torres_2012"]), ("reservoir_s2_rf_", ["rf"]), ("s2_rf_", ["rf"]),
                      ("reservoir_", ["reservoir", "Paper1_Nikoriak_2026", "Paper2_Nikoriak_2026"]),
                      ("terrain_", ["terrain", "water_surface"]), ("s1_", ["s1_flood"]), ("s2_", ["s2_water", "indices"]), ("unet_", ["Ronneberger_2015", "He_2016", "Iakubovskii_2019", "He_2024", "Maiti_2022"]),
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
