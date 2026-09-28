from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import C, INDICES, caption, figure, fmt_ref, header, raw, refs, table

st.set_page_config(page_title="Reconstruction", layout="wide")
header("Observation-constrained terrain inundation reconstruction: the daily reconstructed series",
       "SWOT node heights (gauge-anchored, Paper-1 closure) + Kherson gauge → connected terrain rule → daily area, depth, volume")

d = raw("p95_daily_area_pooled_connected_ceiling.csv"); d["t"] = pd.to_datetime(d.date)
h = raw("p95_daily_area_pooled.csv"); h["t"] = pd.to_datetime(h.date)
u = table("T12")
s1 = raw("p94_flood_dynamics_s1.csv"); s1["t"] = pd.to_datetime(s1.date)
region = st.selectbox("region", ["DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect"], format_func=lambda r: {"DNIPRO_CORRIDOR": "Dnipro corridor (Inhulets excluded)", "P42_FLOODPLAIN_DOMAIN": "p42 floodplain domain", "INHULETS_VALLEY_rect": "Inhulets valley (backwater)"}[r])
s = d[d.region == region]; uu = u[u.region == region].copy(); uu["t"] = pd.to_datetime(uu.date); uu = uu.sort_values("t")
fig = go.Figure()
if "A_p05_km2" in uu.columns and uu.A_p05_km2.notna().any():
    fig.add_trace(go.Scatter(x=list(uu.t) + list(uu.t[::-1]), y=list(uu.A_p95_km2) + list(uu.A_p05_km2[::-1]), fill="toself", fillcolor="rgba(42,120,214,0.18)", line=dict(width=0), name="PRIMARY: spatial Monte-Carlo p05–p95 (40 draws), newly inundated area", hoverinfo="skip"))
fig.add_trace(go.Scatter(x=s.t, y=s.new_km2, mode="lines", line=dict(color=C["terrain"], width=3), name="reconstructed newly inundated area (central run)", hovertemplate="%{x|%d %b}: %{y:.0f} km²"))
fig.add_trace(go.Scatter(x=s.t, y=s.potential_km2, mode="lines", line=dict(color=C["terrain"], width=1.5, dash="dashdot"), name="reconstructed total water-surface area (incl. pre-breach water)", hovertemplate="%{x|%d %b}: %{y:.0f} km²"))
try:
    g = raw("p95g_mc_daily.csv"); gg = g[g.region == region].copy(); gg["t"] = pd.to_datetime(gg.date)
    fig.add_trace(go.Candlestick(x=gg.t, open=gg.W_total_km2_p25, close=gg.W_total_km2_p75, low=gg.W_total_km2_p05, high=gg.W_total_km2_p95, name="SENSITIVITY: 100 000-draw emulator envelope (p05–p95, p25–p75)", increasing_line_color="#2a78d6", decreasing_line_color="#2a78d6", opacity=0.5))
    fig.update_layout(xaxis_rangeslider_visible=False)
except FileNotFoundError:
    pass
if "W_total_p05_km2" in uu.columns and uu.W_total_p05_km2.notna().any():
    tt = uu.dropna(subset=["W_total_p05_km2"])
    fig.add_trace(go.Scatter(x=list(tt.t) + list(tt.t[::-1]), y=list(tt.W_total_p95_km2) + list(tt.W_total_p05_km2[::-1]), fill="toself", fillcolor="rgba(42,120,214,0.28)", line=dict(width=0), name="PRIMARY: spatial Monte-Carlo p05–p95 (40 draws), total water-surface area", hoverinfo="skip"))
hh = h[h.region == region]; fig.add_trace(go.Scatter(x=hh.t, y=hh.new_km2, mode="lines", line=dict(color=C["terrain"], width=1.5, dash="dash"), name="p42 HAND rule (lower bound)"))
o = s1[s1.region == region]
fig.add_trace(go.Scatter(x=o.t, y=o.new_water_km2, mode="markers", marker=dict(color=C["s1"], size=9, symbol=["circle" if c >= 0.9 else "circle-open" for c in o.coverage]), name="Sentinel-1 observed new dark water (open = partial coverage)", hovertemplate="%{x|%d %b}: %{y:.0f} km² (coverage %{customdata:.0%})", customdata=o.coverage))
fig.add_trace(go.Scatter(x=o.t, y=o.water_km2, mode="markers", marker=dict(color=C["s1"], size=8, symbol="diamond-open"), name="Sentinel-1 total dark water", hovertemplate="%{x|%d %b}: %{y:.0f} km²"))
fig.add_vline(x=pd.Timestamp("2023-06-06"), line=dict(color="#e34948", dash="dash"))
fig.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="km²", legend=dict(orientation="h", y=-0.15), xaxis=dict(range=["2023-05-31", "2023-07-05"]))
st.plotly_chart(fig, width="stretch")
refs(["terrain", "water_surface", "Twele_2016", "Martinis_2022"], "📚 Literature: terrain reconstruction (HAND, DEM), water surface (SWOT, Paper 1) and the S1 check")

c1, c2 = st.columns(2)
with c1:
    g = go.Figure(); g.add_trace(go.Scatter(x=s.t, y=s.kherson_gauge_m, mode="lines", line=dict(color=C["gauge"], width=2), name="Kherson stage, m (EVRF2019)"))
    g.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="m", title="Kherson gauge 80805 (daily)"); st.plotly_chart(g, width="stretch")
with c2:
    vv = go.Figure(); vv.add_trace(go.Scatter(x=s.t, y=s.new_volume_hm3 / 1000, mode="lines", line=dict(color=C["terrain"], width=2), name="volume, km³"))
    if "V_p05_hm3" in uu.columns and uu.V_p05_hm3.notna().any():
        vv.add_trace(go.Scatter(x=list(uu.t) + list(uu.t[::-1]), y=list(uu.V_p95_hm3 / 1000) + list(uu.V_p05_hm3[::-1] / 1000), fill="toself", fillcolor="rgba(42,120,214,0.18)", line=dict(width=0), name="PRIMARY: spatial MC p05–p95"))
    vv.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="km³", title="terrain-reconstructed water volume above ground (planar surface, no ponding)"); st.plotly_chart(vv, width="stretch")

st.subheader("Key dates (T12)"); st.caption(caption("T12"))
cols = [c for c in ["date", "W_total_central_km2", "W_total_p05_km2", "W_total_p95_km2", "A_central_km2", "A_p05_km2", "A_p50_km2", "A_p95_km2", "V_central_hm3", "V_p05_hm3", "V_p95_hm3", "A_hand_and_ceiling_km2", "A_ceiling_only_km2", "kherson_gauge_m"] if c in uu.columns]
st.dataframe(uu[cols], width="stretch", hide_index=True)
st.subheader("Uncertainty components (T11b) and constants (T11)"); st.caption(caption("T11b")); st.dataframe(table("T11b"), width="stretch", hide_index=True)
st.dataframe(table("T11"), width="stretch", hide_index=True)
refs(["Olofsson_2014", "Hawker_2022", "Paper2_Nikoriak_2026"], "📚 Literature: uncertainty of reconstructed areas and the DEM error model")
st.subheader("Water surface (Fig06)"); figure("Fig06")
refs(["water_surface"], "📚 Literature: SWOT RiverSP, SWORD and the Paper-1 vertical frame")

st.subheader("Reservoir side of the balance (T21, T22, Fig09)")
try:
    R = table("T21"); R["t"] = pd.to_datetime(R.date); ok = R.V_pool_km3.notna()
    f1 = go.Figure(); f1.add_trace(go.Scatter(x=R.t, y=R.H_outlet_m, mode="lines+markers", name="outlet (SWOT)", line=dict(color=C["terrain"])))
    f1.add_trace(go.Scatter(x=R.t, y=R.H_nikopol_m, mode="markers", name="Nikopol (press)", marker=dict(color="#eda100"))); f1.add_trace(go.Scatter(x=R.t, y=R.H_rozumivka_m, mode="lines+markers", name="Rozumivka gauge", line=dict(color=C["rf"])))
    f1.add_trace(go.Scatter(x=R.t, y=R.kherson_stage_m, mode="lines", name="Kherson stage (downstream)", line=dict(color=C["gauge"])))
    f1.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="m", title="pool and downstream levels"); st.plotly_chart(f1, width="stretch")
    c1, c2 = st.columns(2)
    with c1:
        f2 = go.Figure(); f2.add_trace(go.Scatter(x=R.t[ok], y=R.V_pool_km3[ok], mode="lines+markers", name="pool volume, km³", line=dict(color=C["terrain"])))
        f2.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="km³", title="pool volume under the sloped surface"); st.plotly_chart(f2, width="stretch")
    with c2:
        dd = R[ok & (R.t >= "2023-06-05")]
        f3 = go.Figure(); f3.add_trace(go.Bar(x=dd.t, y=-dd.dV_pool_hm3 / 1000, name="released from the pool, km³/day", marker_color=C["terrain"]))
        f3.add_trace(go.Scatter(x=dd.t, y=dd.Q_in_hm3_day / 1000, mode="lines+markers", name="DniproHES inflow, km³/day", line=dict(color=C["rf"])))
        f3.add_trace(go.Scatter(x=R.t, y=R.downstream_new_volume_hm3 / 1000, mode="lines+markers", name="new water stored downstream, km³", line=dict(color=C["s1"])))
        f3.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="km³", title="daily balance"); st.plotly_chart(f3, width="stretch")
    st.dataframe(R, width="stretch", hide_index=True)
    refs(["Paper1_Nikoriak_2026", "Paper2_Nikoriak_2026", "Yi_2025", "Vyshnevskyi_2023", "Shumilova_2025", "Kadam_2024", "Lehnigk_2026"], "📚 Literature: reservoir levels, bathymetry and the breach discharge")
except FileNotFoundError:
    st.info("reservoir tables not built")
try:
    M = table("T23"); M["t"] = pd.to_datetime(M.date); st.markdown(caption("T23"))
    st.markdown("**Reservoir drawdown maps** — see *Maps → Reservoir drawdown* (model by day, S1 VH, S2 classes and the 7 classed indices). "
                "Pool water area by source: MODEL is *terrain_reconstructed*; S1 / S2 are *observed* and count observed cells only "
                "(S1 dark = open water **or** smooth wet mud, so it exceeds the model on exposed flats after ~13 June).")
    f4 = go.Figure()
    for src_, col, mode in (("MODEL", C["terrain"], "lines+markers"), ("S1", C["s1"], "markers"), ("S2_WATER3", C["rf"], "markers"), ("S2_CROSSCHECK", C["unet"], "markers")):
        q = M[(M.source == src_) & (M.observed_frac >= 0.5)]
        f4.add_trace(go.Scatter(x=q.t, y=q.water_km2, mode=mode, name=f"{src_} (≥ 50 % of the pool observed)", line=dict(color=col), marker=dict(color=col, size=8)))
    yi = M.dropna(subset=["yi2025_S1_km2"]).drop_duplicates("date")
    f4.add_trace(go.Scatter(x=yi.t, y=yi.yi2025_S1_km2, mode="markers", name="Yi 2025 S1 (literature_reported, VERIFY)", marker=dict(symbol="x", color=C["gauge"], size=9)))
    f4.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="km²", title="pool water area: model vs observations"); st.plotly_chart(f4, width="stretch")
    st.dataframe(M.drop(columns="t"), width="stretch", hide_index=True)
    refs(["reservoir", "Otsu_1979", "Twele_2016", "McFeeters_1996", "Xu_2006", "Main-Knorn_2017"], "📚 Literature: the drained Kakhovka reservoir, S1 VH thresholding and the S2 water rule")
except FileNotFoundError:
    st.info("p95h reservoir maps not built")
try:
    I = table("T25"); I["t"] = pd.to_datetime(I.date); K = table("T24")
    st.markdown("**Sentinel-2 indices and surface classes over the pool (T25, T24)** — frozen p25 products; strata from the modelled day of exposure.")
    c1, c2 = st.columns(2)
    with c1:
        ix = st.selectbox("index", sorted(I["index"].unique()), index=sorted(I["index"].unique()).index("MNDWI"))
    with c2:
        strata = st.multiselect("strata", list(I.stratum.unique()), default=list(I.stratum.unique()))
    if ix in INDICES:
        fo, what, rk, used = INDICES[ix]
        st.markdown(f"**{ix}** = `{fo}` — responds to {what}; here: {used}.  \n" + "  \n".join(f"<small>{fmt_ref(r)}</small>" for r in rk), unsafe_allow_html=True)
    f5 = go.Figure()
    for sn, col in zip(strata, [C["terrain"], "#d9a441", C["rf"]]):
        q = I[(I["index"] == ix) & (I.stratum == sn)].sort_values("t")
        f5.add_trace(go.Scatter(x=list(q.t) + list(q.t[::-1]), y=list(q.p90) + list(q.p10[::-1]), fill="toself", fillcolor=col, opacity=0.15, line=dict(width=0), showlegend=False, hoverinfo="skip"))
        f5.add_trace(go.Scatter(x=q.t, y=q.p50, mode="lines+markers", name=f"{sn} median (band p10–p90)", line=dict(color=col), customdata=q.observed_frac,
                                hovertemplate="%{x|%Y-%m-%d}: %{y:.3f} (observed %{customdata:.0%})"))
    f5.add_vline(x=pd.Timestamp("2023-06-06").timestamp() * 1000, line=dict(color="#e34948", dash="dash", width=1))
    f5.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), yaxis_title=ix, title=f"{ix} inside the pool by date"); st.plotly_chart(f5, width="stretch")
    st.markdown(caption("T25")); st.dataframe(I[(I["index"] == ix) & I.stratum.isin(strata)].drop(columns="t"), width="stretch", hide_index=True)
    st.markdown(caption("T24")); st.dataframe(K[K.stratum.isin(strata)], width="stretch", hide_index=True)
    refs(["indices", "k10e", "reservoir"], "📚 Literature: the 7 spectral indices, the k10e rule classes and studies of the drained Kakhovka bed")
except FileNotFoundError:
    st.info("reservoir index tables (T24, T25) not built")
