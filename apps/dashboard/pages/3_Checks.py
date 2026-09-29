from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import C, caption, figure, header, refs, table

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
refs(["s1_flood", "Cohen_2019", "Le_2026", "Darnell_2008"], "📚 Literature: Sentinel-1 flood mapping, where SAR cannot see (vegetation, exclusion maps) and urban flood")

st.subheader("ICESat-2 altimetric consistency check (T15, Fig08)"); st.caption(caption("T15")); st.dataframe(table("T15"), width="stretch", hide_index=True); figure("Fig08")
with st.expander("Pass hold-out of the class-bias correction (T15b, T15c)"):
    st.caption(caption("T15b")); st.dataframe(table("T15b"), width="stretch", hide_index=True)
    st.caption(caption("T15c")); st.dataframe(table("T15c"), width="stretch", hide_index=True)
refs(["Neuenschwander_2019", "Paper1_Nikoriak_2026", "Paper2_Nikoriak_2026", "Lehnigk_2026"], "📚 Literature: ICESat-2 ATL08 / ATL13 and its use in the series")
st.subheader("Withheld river gauges: independent validation of the reconstructed water surface (T17c–T17f, FigS15)")
st.caption("Kherson 80805 is an input (the anchor of the water surface). Kalynivske 80575 (Inhulets) and Mykolaiv 98027 (liman) are withheld: "
           "never inputs, they test two failure modes — the propagation of the tributary backwater and the water surface of the western delta. "
           "Daily means of the 2023 yearbook (cm above the gauge zero read from the sheet), EVRF2019; e_rise is free of any constant datum offset.")
def _val(tid, rid):
    t = table(tid); r = t[t.id == rid]
    return str(r.value.iloc[0]) if len(r) else "n/a"
gk, gm = st.columns(2)
for col, tid, sid, name, rows in ((gk, "T17c", "T17d", "Inhulets – Kalynivske 80575 (tributary backwater)",
                                   [("highest level", "highest_evrf"), ("maximum earlier than the gauge by", "peak_lag"), ("largest error on the rising limb", "e_abs_rising_max"),
                                    ("most negative event-relative error", "e_rise_recession_min")]),
                                  (gm, "T17e", "T17f", "Southern Bug – Mykolaiv 98027 (liman, western delta)",
                                   [("highest level", "highest_evrf"), ("rise to the highest level", "rise_m"), ("error on the liman's maximum day", "e_abs_at_max"),
                                    ("serving SWOT node without observation", "serving_node_unobserved")])):
    with col:
        st.markdown(f"**{name}**")
        for lab, rid in rows:
            st.markdown(f"- {lab}: **{_val(sid, rid)}**")
        g_ = table(tid).copy(); g_["t"] = pd.to_datetime(g_.date)
        fl = go.Figure()
        fl.add_trace(go.Scatter(x=g_.t, y=g_.kherson_gauge_m, mode="lines", line=dict(color=C["muted"], width=1.2), name="Kherson (input)"))
        fl.add_trace(go.Scatter(x=g_.t, y=g_.H_reconstructed_primary_m, mode="lines", line=dict(color=C["terrain"], width=2.5), name="reconstruction at the gauge"))
        fl.add_trace(go.Scatter(x=g_.t, y=g_.H_evrf2019_m, mode="lines+markers", line=dict(color="#0b0b0b", width=2), marker=dict(size=4), name="gauge (withheld)"))
        fl.add_vline(x=pd.Timestamp("2023-06-06"), line=dict(color="#e34948", dash="dash"))
        fl.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="m EVRF2019", legend=dict(orientation="h", y=-0.25), xaxis=dict(range=["2023-05-28", "2023-07-05"]))
        st.plotly_chart(fl, width="stretch")
        fe = go.Figure()
        fe.add_trace(go.Scatter(x=g_.t, y=g_.recon_minus_gauge_m, mode="lines", line=dict(color=C["terrain"], width=2), name="e_abs = reconstruction − gauge"))
        fe.add_trace(go.Scatter(x=g_.t, y=g_.e_rise_m, mode="lines", line=dict(color=C["s1"], width=2, dash="dash"), name="e_rise = reconstructed rise − gauge rise"))
        fe.add_hline(y=0, line=dict(color="#52514e", width=1)); fe.add_vline(x=pd.Timestamp("2023-06-06"), line=dict(color="#e34948", dash="dash"))
        fe.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="m", legend=dict(orientation="h", y=-0.3), xaxis=dict(range=["2023-05-28", "2023-07-05"]))
        st.plotly_chart(fe, width="stretch")
st.caption("The static reconstruction has no propagation time, friction or transient backwater: at Kalynivske it is metres too high while the backwater "
           "travels up the valley and peaks three days early; at Mykolaiv the westernmost SWOT node is interpolated flat across the flood. "
           "Why a hydraulic model is the next step: manuscript §5.")
with st.expander("FigS15 — the withheld gauges"):
    figure("FigS15")

st.subheader("SWOT input vs Kherson gauge (T17) and DEM accuracy (T18, Paper 2)"); st.caption(caption("T17")); st.dataframe(table("T17"), width="stretch", hide_index=True)
st.caption(caption("T18")); st.dataframe(table("T18"), width="stretch", hide_index=True)
refs(["water_surface", "terrain"], "📚 Literature: SWOT input, gauge frame and DEM accuracy (Paper 2, FABDEM)")
