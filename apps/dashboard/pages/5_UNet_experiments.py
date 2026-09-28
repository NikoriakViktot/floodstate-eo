from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from lib import C, caption, figure, header, refs, table

st.set_page_config(page_title="U-Net experiments", layout="wide")
header("What EO inputs recover under weak labels: the U-Net arm experiments",
       "agreement with frozen weak labels on the frozen spatial-block split; U2b (+W_pre) is a diagnostic upper bound because W_pre is also a label ingredient")

st.subheader("Arms (T04)"); st.caption(caption("T04")); st.dataframe(table("T04").drop(columns=["channels"]), width="stretch", hide_index=True)
st.subheader("Paired comparisons on identical blocks (T06, T07b)"); st.caption(caption("T06"))
p = table("T06"); ep = st.selectbox("endpoint", sorted(p.endpoint.unique()), index=sorted(p.endpoint.unique()).index("A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2"))
pp = p[p.endpoint == ep]
fig = go.Figure()
for _, r in pp.iterrows():
    fig.add_trace(go.Scatter(x=[r.ci_lo, r.ci_hi], y=[f"{r.comparison} ({r.labels})"] * 2, mode="lines", line=dict(color=C["muted"] if r.independent == "no" else C["unet"], width=4), showlegend=False))
    fig.add_trace(go.Scatter(x=[r["median"]], y=[f"{r.comparison} ({r.labels})"], mode="markers", marker=dict(color=C["muted"] if r.independent == "no" else C["unet"], size=10), showlegend=False, hovertemplate="median %{x:.3f}"))
fig.add_vline(x=0, line=dict(color="#52514e", dash="dot")); fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10), xaxis_title=f"{ep}: B − A (median, 95 % block bootstrap); grey = not independent")
st.plotly_chart(fig, width="stretch")
st.caption(caption("T07b")); st.dataframe(table("T07b"), width="stretch", hide_index=True)
figure("Fig03")
st.subheader("D1 endpoints (T05)"); st.caption(caption("T05"))
e = table("T05"); pick = st.multiselect("endpoints", sorted(e.endpoint.unique()), default=["G_F1", "G_PR_AUC", "A_FP_area_dry_cropland_km2", "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2", "B_recall_flooded_open_low_veg", "W_IoU", "BU_FP_area_km2"])
st.dataframe(e[e.endpoint.isin(pick)].pivot_table(index=["arm", "labels"], columns="endpoint", values="value").round(4), width="stretch")
st.subheader("Cropland-associated SAR candidates (T08)"); st.caption(caption("T08")); st.dataframe(table("T08"), width="stretch", hide_index=True); st.dataframe(table("T08b"), width="stretch", hide_index=True)
st.subheader("Labels and split (T02, T03, T20)"); st.dataframe(table("T02"), width="stretch", hide_index=True); st.dataframe(table("T03"), width="stretch", hide_index=True)
st.caption(caption("T20")); st.dataframe(table("T20"), width="stretch", hide_index=True); figure("FigS05"); figure("FigS01")
refs(["unet"], "📚 Literature: U-Net, ResNet encoders, S1/S2 flood benchmarks, learning from weak / noisy labels and spatial validation", expanded=True)
