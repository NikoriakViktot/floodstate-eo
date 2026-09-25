"""Shared loaders and constants for the FloodState-EO Kakhovka dashboard (no floodstate_eo import, no bulk data)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

APP = Path(__file__).resolve().parent
REPO = APP.parents[1]
CS = REPO / "case_studies" / "kakhovka_2023"
T = CS / "tables"
PT = CS / "publication" / "tables"
PF = CS / "publication" / "figures"
DATA = APP / "data"
C = {"terrain": "#2a78d6", "s1": "#eb6834", "unet": "#4a3aa7", "rf": "#1baf7a", "gauge": "#52514e", "muted": "#95a5a6"}
RULES = ("Every model number is *agreement with weak reference labels*, never flood-mapping accuracy. "
         "*Not observed is not dry.* Areas carry their semantics: observed_S1 · mapped_UNet · terrain_reconstructed · literature_reported. "
         "Evidence levels: independent_physical › cross_sensor › weak_label_agreement › contextual.")


@st.cache_data(show_spinner=False)
def table(tid: str) -> pd.DataFrame:
    return pd.read_csv(PT / f"{tid}.csv")


@st.cache_data(show_spinner=False)
def raw(name: str) -> pd.DataFrame:
    return pd.read_csv(T / name)


@st.cache_data(show_spinner=False)
def manifest() -> dict:
    return json.loads((PT / "manifest.json").read_text())


@st.cache_data(show_spinner=False)
def layers() -> dict:
    return json.loads((DATA / "manifest.json").read_text())


def caption(tid: str) -> str:
    m = manifest()["tables"].get(tid, {})
    return f"**{tid}** · *{m.get('evidence_level', '')}* — {m.get('caption', '')}"


def figure(stem: str, width="stretch"):
    p = next(PF.glob(stem + "*.png"), None)
    if p is None:
        st.info(f"figure {stem} not rendered")
    else:
        st.image(str(p), width=width)


def header(title: str, sub: str = ""):
    st.title(title)
    if sub:
        st.caption(sub)
    st.markdown(f"<small>{RULES}</small>", unsafe_allow_html=True)
