"""FloodState-EO — Kakhovka 2023: daily inundation reconstruction, cross-sensor checks and weak-label experiments.

Streamlit Cloud entry point (main file: apps/dashboard/streamlit_app.py). Reads committed tables, publication figures and
the pre-rendered layers in apps/dashboard/data only.
"""
from __future__ import annotations

import streamlit as st

from lib import SERIES, caption, figure, header, layers, manifest, refs, session, table

st.set_page_config(page_title="FloodState-EO · Kakhovka 2023", page_icon="🌊", layout="wide")
header("Kakhovka 2023 — inundation after the dam breach",
       "Paper 3 of the Kakhovka series: observation-constrained terrain-connectivity reconstruction and its uncertainty → independent validation and support → weak-label ML diagnostics")
session("home_")                                                       # ?sid=... : the viewer's choices on every page survive reloads

st.markdown("""
**How to read this dashboard.** The main axis is the *observation-constrained terrain-connectivity reconstruction* — a daily reconstructed series, not daily observations — of the inundation from the observed
water surface (SWOT nodes + Kherson gauge, Paper-1 vertical frame) projected on the terrain, with its Monte-Carlo uncertainty. Two
withheld gauges, Sentinel-1 per-date masks and ICESat-2 are *checks* of it; the RF20 surface classes *explain* where the sensor and the
reconstruction disagree; the U-Net arms, trained on the canonical weak labels v004 with three seeds, are *diagnostics of weak
supervision*. Nothing here is a validated flood map.
""")
with st.expander("📄 The Kakhovka series — earlier papers and code", expanded=True):
    for name, title, status, links, key in SERIES:
        ln = " · ".join(f"[{t}]({u})" for t, u in links)
        st.markdown(f"**{name}** — {title} *({status})*" + (f" — {ln}" if ln else ""))
    st.caption("Manuscripts have no DOI yet; the repositories are the public record. Method-by-method literature: Literature page.")
refs(["event"], "📚 Literature: the 2023 breach, its consequences and the operational flood products")

d12 = table("T12"); corr = d12[d12.region == "DNIPRO_CORRIDOR"].set_index("date")
d13 = table("T13"); v = d13[(d13.variant == "connected_ceiling") & (d13.region == "P42_FLOODPLAIN_DOMAIN") & (d13.date == "2023-06-09")]
d7 = table("T07s"); lab = d7[(d7.comparison == "v004 - v002_notrace (U2)") & (d7.endpoint == "R_pred_on_reference_water_km2")]   # D-C09, three seeds
pk = (corr.A_p50_km2 if "A_p50_km2" in corr.columns and corr.A_p50_km2.notna().any() else corr.A_central_km2).idxmax()   # areal maximum of the MC median

st.markdown("**Primary result — the reconstructed series (terrain_reconstructed, daily snapshots)**")
c1, c2 = st.columns(2)
c1.metric("Reconstructed TOTAL water-surface area, Dnipro corridor, areal maximum (MC median)", f"{corr.loc[pk, 'W_total_p50_km2']:.0f} km²",
          f"PRIMARY Monte-Carlo p05–p95 {corr.loc[pk, 'W_total_p05_km2']:.0f}–{corr.loc[pk, 'W_total_p95_km2']:.0f} km² · nominal run {corr.loc[pk, 'W_total_central_km2']:.0f} · on {pk}", delta_color="off")
c2.metric("Reconstructed NEWLY inundated area (not water before the breach; MC median)", f"{corr.loc[pk, 'A_p50_km2']:.0f} km²",
          f"PRIMARY Monte-Carlo p05–p95 {corr.loc[pk, 'A_p05_km2']:.0f}–{corr.loc[pk, 'A_p95_km2']:.0f} km² · nominal run {corr.loc[pk, 'A_central_km2']:.0f} · volume {corr.loc[pk, 'V_p50_hm3']:.0f} hm³ ({corr.loc[pk, 'V_p05_hm3']:.0f}–{corr.loc[pk, 'V_p95_hm3']:.0f}; nominal {corr.loc[pk, 'V_central_hm3']:.0f})", delta_color="off")
st.caption(f"Central values are Monte-Carlo medians of {int(corr.loc[pk, 'n_draws'])} coherent Monte-Carlo worlds (one terrain and one water-surface realization per draw); the deterministic nominal run is a diagnostic, given only for reference.")
st.caption("Secondary — checks and weak-label agreement (never accuracy)")
c3, c4, c5 = st.columns(3)
c3.metric("Raw agreement with Sentinel-1 on 2023-06-09 (p42 floodplain)", f"POD {float(v.POD.iloc[0]):.2f} · CSI {float(v.CSI.iloc[0]):.2f}" if len(v) else "n/a", "cross_sensor, S1 footprint; conditioned by surface type")
if len(lab):
    r7 = lab.iloc[0]
    c4.metric("Weak-label treatment of reference water (U2, v004 vs the same rule without REFERENCE_WATER): predicted flood on reference water",
              f"{-float(r7.max_median):.1f}–{-float(r7.min_median):.1f} km² less",
              f"three training seeds, {int(r7.n_seeds_excluding_zero)} of 3 intervals exclude zero · weak_label_agreement, not accuracy", delta_color="off")
try:                                                                 # D-SUPPORT: how much of the new area rests on distant water-surface support
    sk = table("T11k"); sk = sk[(sk.region == "DNIPRO_CORRIDOR") & (sk.date == pk)]
    c5.metric("New area on the areal maximum with water-surface support > 10 km (weakly constrained)", f"{float(sk.share_weak.iloc[0]):.0%}" if len(sk) else "n/a",
              f"supported core <= 10 km: {float(sk.A_core_le10km_km2.iloc[0]):.0f} of {float(sk.A_full_km2.iloc[0]):.0f} km² (nominal run, T11k)" if len(sk) else "", delta_color="off")
except FileNotFoundError:
    pass
n05 = corr.loc["2023-06-05", "W_total_central_km2"] if "W_total_central_km2" in corr.columns and "2023-06-05" in corr.index else None
if n05 is not None:
    st.caption(f"Normal regime on 2023-06-05: {n05:.0f} km² of water in the corridor; the Inhulets valley is reported separately (Reconstruction page).")

st.divider()
col1, col2 = st.columns([1.4, 1])
with col1:
    figure("Fig04")
    st.caption(caption("T12"))
with col2:
    figure("Fig02")
    st.markdown("**Pages** — Reconstruction · Maps · Checks · Surface context · U-Net experiments · Data & provenance · Literature (left sidebar).")
    m = manifest(); L = layers()
    st.caption(f"tables generated at {m['generated_utc']} from commit {m['git_commit'][:7]} · {L['n_layers']} map layers, {L['total_bytes'] / 1e6:.1f} MB")
