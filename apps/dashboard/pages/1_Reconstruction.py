from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import C, caption, figure, header, raw, table

st.set_page_config(page_title="Reconstruction", layout="wide")
header("Physical reconstruction: daily inundation from the observed water surface",
       "SWOT node heights (gauge-anchored, Paper-1 closure) + Kherson gauge → connected terrain rule → daily area, depth, volume")

d = raw("p95_daily_area_pooled_connected_ceiling.csv"); d["t"] = pd.to_datetime(d.date)
h = raw("p95_daily_area_pooled.csv"); h["t"] = pd.to_datetime(h.date)
u = table("T12")
s1 = raw("p94_flood_dynamics_s1.csv"); s1["t"] = pd.to_datetime(s1.date)
region = st.selectbox("region", ["DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect"], format_func=lambda r: {"DNIPRO_CORRIDOR": "Dnipro corridor (Inhulets excluded)", "P42_FLOODPLAIN_DOMAIN": "p42 floodplain domain", "INHULETS_VALLEY_rect": "Inhulets valley (backwater)"}[r])
s = d[d.region == region]; uu = u[u.region == region].copy(); uu["t"] = pd.to_datetime(uu.date); uu = uu.sort_values("t")
fig = go.Figure()
if "A_p05_km2" in uu.columns and uu.A_p05_km2.notna().any():
    fig.add_trace(go.Scatter(x=list(uu.t) + list(uu.t[::-1]), y=list(uu.A_p95_km2) + list(uu.A_p05_km2[::-1]), fill="toself", fillcolor="rgba(42,120,214,0.18)", line=dict(width=0), name="Monte-Carlo p05–p95", hoverinfo="skip"))
fig.add_trace(go.Scatter(x=s.t, y=s.new_km2, mode="lines", line=dict(color=C["terrain"], width=3), name="terrain-reconstructed (connected, central)", hovertemplate="%{x|%d %b}: %{y:.0f} km²"))
hh = h[h.region == region]; fig.add_trace(go.Scatter(x=hh.t, y=hh.new_km2, mode="lines", line=dict(color=C["terrain"], width=1.5, dash="dash"), name="p42 HAND rule (lower bound)"))
o = s1[s1.region == region]
fig.add_trace(go.Scatter(x=o.t, y=o.new_water_km2, mode="markers", marker=dict(color=C["s1"], size=9, symbol=["circle" if c >= 0.9 else "circle-open" for c in o.coverage]), name="Sentinel-1 observed new dark water (open = partial coverage)", hovertemplate="%{x|%d %b}: %{y:.0f} km² (coverage %{customdata:.0%})", customdata=o.coverage))
fig.add_vline(x=pd.Timestamp("2023-06-06"), line=dict(color="#e34948", dash="dash"))
fig.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="new inundation, km²", legend=dict(orientation="h", y=-0.15), xaxis=dict(range=["2023-05-31", "2023-07-05"]))
st.plotly_chart(fig, width="stretch")

c1, c2 = st.columns(2)
with c1:
    g = go.Figure(); g.add_trace(go.Scatter(x=s.t, y=s.kherson_gauge_m, mode="lines", line=dict(color=C["gauge"], width=2), name="Kherson stage, m (EVRF2019)"))
    g.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="m", title="Kherson gauge 80805 (daily)"); st.plotly_chart(g, width="stretch")
with c2:
    vv = go.Figure(); vv.add_trace(go.Scatter(x=s.t, y=s.new_volume_hm3 / 1000, mode="lines", line=dict(color=C["terrain"], width=2), name="volume, km³"))
    if "V_p05_hm3" in uu.columns and uu.V_p05_hm3.notna().any():
        vv.add_trace(go.Scatter(x=list(uu.t) + list(uu.t[::-1]), y=list(uu.V_p95_hm3 / 1000) + list(uu.V_p05_hm3[::-1] / 1000), fill="toself", fillcolor="rgba(42,120,214,0.18)", line=dict(width=0), name="MC p05–p95"))
    vv.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="km³", title="terrain-reconstructed water volume above ground (planar surface, no ponding)"); st.plotly_chart(vv, width="stretch")

st.subheader("Key dates (T12)"); st.caption(caption("T12"))
cols = [c for c in ["date", "A_central_km2", "A_p05_km2", "A_p50_km2", "A_p95_km2", "V_central_hm3", "V_p05_hm3", "V_p95_hm3", "A_hand_and_ceiling_km2", "A_ceiling_only_km2", "kherson_gauge_m"] if c in uu.columns]
st.dataframe(uu[cols], width="stretch", hide_index=True)
st.subheader("Uncertainty components (T11b) and constants (T11)"); st.caption(caption("T11b")); st.dataframe(table("T11b"), width="stretch", hide_index=True)
st.dataframe(table("T11"), width="stretch", hide_index=True)
st.subheader("Water surface (Fig06)"); figure("Fig06")
