from __future__ import annotations

import streamlit as st

from lib import caption, figure, header, table

st.set_page_config(page_title="Surface context", layout="wide")
header("Surface context: RF20 PRE-event surface classification", "evaluation strata and disagreement classes; agreement with ESA WorldCover 2021 (the training reference), not validation")
st.caption(caption("T09")); st.dataframe(table("T09"), width="stretch", hide_index=True)
figure("FigS04")
c1, c2 = st.columns(2)
with c1:
    st.caption(caption("T10")); st.dataframe(table("T10"), width="stretch", hide_index=True)
with c2:
    st.caption(caption("T10b")); st.dataframe(table("T10b"), width="stretch", hide_index=True)
st.caption(caption("T10c")); st.dataframe(table("T10c"), width="stretch", hide_index=True)
