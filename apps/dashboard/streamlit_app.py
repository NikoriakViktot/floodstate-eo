"""FloodState-EO — Kakhovka 2023: daily inundation reconstruction, cross-sensor checks and weak-label experiments.

Streamlit Cloud entry point (main file: apps/dashboard/streamlit_app.py). Reads committed tables, publication figures and
the pre-rendered layers in apps/dashboard/data only.
"""
from __future__ import annotations

import streamlit as st

from lib import C, caption, figure, header, layers, manifest, table

st.set_page_config(page_title="FloodState-EO · Kakhovka 2023", page_icon="🌊", layout="wide")
header("Kakhovka 2023 — inundation after the dam breach",
       "Paper 3 of the Kakhovka series: physical reconstruction → independent / cross-sensor checks → surface context → ML under weak labels")

st.markdown("""
**How to read this dashboard.** The main axis is the *physical reconstruction* of the daily inundation from the observed
water surface (SWOT nodes + Kherson gauge, Paper-1 vertical frame) projected on the terrain. Sentinel-1 per-date masks and
ICESat-2 are *checks* of it; the RF20 surface classes *explain* where the sensor and the reconstruction disagree; the U-Net
arms show *what EO inputs recover under weak labels*. Nothing here is a validated flood map.
""")

d12 = table("T12"); corr = d12[d12.region == "DNIPRO_CORRIDOR"].set_index("date")
d13 = table("T13"); v = d13[(d13.variant == "connected_ceiling") & (d13.region == "P42_FLOODPLAIN_DOMAIN") & (d13.date == "2023-06-09")]
d7 = table("T07b"); lab = d7[(d7.A == "U2_B1B2_v1") & (d7.B == "U2_B1B2_v003A") & (d7.endpoint == "R_pred_on_reference_water_km2")]
pk = corr.A_central_km2.idxmax()

c1, c2, c3, c4 = st.columns(4)
c1.metric("TOTAL water surface on the peak day, Dnipro corridor", f"{corr.loc[pk, 'W_total_central_km2']:.0f} km²" if "W_total_central_km2" in corr.columns else "n/a",
          (f"p05–p95 {corr.loc[pk, 'W_total_km2_p05']:.0f}–{corr.loc[pk, 'W_total_km2_p95']:.0f} km², 100 000 draws · on {pk}" if "W_total_km2_p05" in corr.columns else f"on {pk}"))
c2.metric("of which NEW inundation (not water before the breach)", f"{corr.A_central_km2.max():.0f} km²",
          (f"p05–p95 {corr.loc[pk, 'A_p05_km2']:.0f}–{corr.loc[pk, 'A_p95_km2']:.0f} km², 40 spatial draws · terrain_reconstructed" if "A_p05_km2" in corr.columns and corr.A_p05_km2.notna().any() else "terrain_reconstructed"))
c3.metric("Agreement with Sentinel-1 on 2023-06-09 (p42 floodplain)", f"POD {float(v.POD.iloc[0]):.2f} · CSI {float(v.CSI.iloc[0]):.2f}" if len(v) else "n/a", "cross_sensor, S1 footprint")
if len(lab):
    c4.metric("Label effect v002 → v003_A (U2): flood on reference water", f"{float(lab['median'].iloc[0]):+.1f} km²", f"95 % [{float(lab.lo.iloc[0]):.1f}, {float(lab.hi.iloc[0]):.1f}] · weak_label_agreement")
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
    st.markdown("**Pages** — Reconstruction · Maps · Checks · Surface context · U-Net experiments · Data & provenance (left sidebar).")
    m = manifest(); L = layers()
    st.caption(f"tables generated at {m['generated_utc']} from commit {m['git_commit'][:7]} · {L['n_layers']} map layers, {L['total_bytes'] / 1e6:.1f} MB")
