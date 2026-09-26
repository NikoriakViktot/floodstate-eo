from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from lib import C, caption, figure, header, table

st.set_page_config(page_title="Checks", layout="wide")
header("Independent and cross-sensor checks of the reconstruction",
       "Sentinel-1 per date (raw POD / FAR / CSI on the observation domain; conditional POD is diagnostic) · disagreement ontology · ICESat-2 altimetric consistency · SWOT-input vs gauge · DEM accuracy (Paper 2)")

st.subheader("Terrain vs Sentinel-1 per acquisition date (T13)"); st.caption(caption("T13"))
d = table("T13"); variant = st.selectbox("variant", sorted(d.variant.unique()), index=sorted(d.variant.unique()).index("connected_ceiling") if "connected_ceiling" in set(d.variant) else 0)
region = st.selectbox("region", ["P42_FLOODPLAIN_DOMAIN", "DNIPRO_CORRIDOR", "INHULETS_VALLEY_rect"])
v = d[(d.variant == variant) & (d.region == region)]
fig = go.Figure()
for k, c in [("POD", C["terrain"]), ("FAR", C["s1"]), ("CSI", C["rf"]), ("POD_cond_outside_normally_wet", C["muted"])]:
    fig.add_trace(go.Scatter(x=v.date, y=v[k], mode="lines+markers", name=("conditional POD outside normally-wet class (diagnostic)" if "cond" in k else k), line=dict(color=c, dash="dot" if "cond" in k else None)))
fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), yaxis=dict(range=[0, 1])); st.plotly_chart(fig, width="stretch")
st.dataframe(v[["date", "s1_new_km2", "hand_new_km2", "hit_km2", "miss_km2", "miss_on_normally_wet_km2", "hand_only_km2", "POD", "FAR", "CSI", "POD_cond_outside_normally_wet"]], width="stretch", hide_index=True)

st.subheader("Disagreement ontology (T14, Fig05)"); st.caption(caption("T14"))
o = table("T14"); date = st.selectbox("date", sorted(o.date.unique()))
oo = o[o.date == date].groupby("category").sum(numeric_only=True)
c1, c2 = st.columns(2)
with c1:
    b = oo.loc["B"] if "B" in oo.index else None
    if b is not None:
        f1 = go.Figure(go.Bar(x=["trees", "wetland", "built", "cropland", "grass", "bare"], y=[b.km2_wc_trees, b.km2_wc_wetland, b.km2_wc_built, b.km2_wc_cropland, b.km2_wc_grass, b.km2_wc_bare], marker_color="#7fb3e6"))
        f1.update_layout(title=f"B terrain-only ({b.km2:.0f} km²) by WorldCover class", height=300, margin=dict(l=10, r=10, t=40, b=10), yaxis_title="km²"); st.plotly_chart(f1, width="stretch")
with c2:
    cc = oo.loc["C"] if "C" in oo.index else None
    if cc is not None:
        f2 = go.Figure(go.Bar(x=["below surface", "0–2 m above", "2–5 m above", "≥ 5 m above"], y=[cc.km2_ground_below_surface, cc.km2_ground_0_2m_above, cc.km2_ground_2_5m_above, cc.km2_ground_ge5m_above], marker_color=C["s1"]))
        f2.update_layout(title=f"C S1-only ({cc.km2:.0f} km²) by ground elevation vs surface ({cc.km2_normally_wet:.0f} km² normally wet)", height=300, margin=dict(l=10, r=10, t=40, b=10), yaxis_title="km²"); st.plotly_chart(f2, width="stretch")
figure("Fig05")

st.subheader("ICESat-2 altimetric consistency check (T15, Fig08)"); st.caption(caption("T15")); st.dataframe(table("T15"), width="stretch", hide_index=True); figure("Fig08")
st.subheader("SWOT input vs Kherson gauge (T17) and DEM accuracy (T18, Paper 2)"); st.caption(caption("T17")); st.dataframe(table("T17"), width="stretch", hide_index=True)
st.caption(caption("T18")); st.dataframe(table("T18"), width="stretch", hide_index=True)
