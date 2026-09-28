from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import CLASSIFIERS, CS, INDICES, METHOD_REFS, SERIES, TOPIC_TITLES, TOPICS, bib, fmt_ref, header

st.set_page_config(page_title="Literature", layout="wide")
header("Literature: the Kakhovka series, methods, spectral indices and classifications",
       "every method on this dashboard with the works it rests on; bibliography = docs/references.bib (⚠️ VERIFY = not yet checked against the publisher record)")

st.subheader("The Kakhovka series")
for name, title, status, links, key in SERIES:
    ln = " · ".join(f"[{t}]({u})" for t, u in links)
    st.markdown(f"**{name}** — {title} *({status})*" + (f"  \n{ln}" if ln else "") + (f"  \n<small>{fmt_ref(key)}</small>" if key else ""), unsafe_allow_html=True)

st.subheader("Classifications and water rules used here")
st.markdown("Each product with its method, its reference (what it is compared against) and the works it rests on. "
            "*Agreement with a weak reference is never accuracy; not observed is not dry.*")
for prod, method, ref, where, keys in CLASSIFIERS:
    with st.container(border=True):
        st.markdown(f"**{prod}** — {method}  \n*Reference:* {ref} · *Where:* {where}")
        st.markdown("\n".join(f"- {fmt_ref(k)}" for k in keys))

st.subheader("Spectral indices (Sentinel-2 L2A, offset-corrected reflectance)")
st.markdown("Band names: B02 blue, B03 green, B04 red, B08 NIR, B11 SWIR1, B12 SWIR2. The display classes on the Maps page and in T26 "
            "are bins for reading the maps, not a classifier; the frozen classifiers are water3, k10e and RF20 above.")
st.dataframe(pd.DataFrame([dict(index=k, formula=v[0], responds_to=v[1], used_here=v[3], reference="; ".join(fmt_ref(r).split(". [")[0] for r in v[2])) for k, v in INDICES.items()]),
             width="stretch", hide_index=True)
for k, v in INDICES.items():
    st.markdown(f"**{k}** `{v[0]}` — " + " · ".join(fmt_ref(r) for r in v[2]))

if METHOD_REFS.exists():
    st.subheader("Method → source → DOI → verification status")
    st.markdown("From `docs/METHOD_REFERENCES.md` (method/index citations of the manuscript, every DOI resolved in Crossref, DataCite for the NSIDC "
                "dataset, title match ≥ 0.85). *bib* = in `docs/references.bib`; *NEW* = added from the audit; *grey* = no DOI exists (cite with access date).")
    MR = pd.read_csv(METHOD_REFS)
    MR["link"] = MR.doi.map(lambda d: f"https://doi.org/{d}" if isinstance(d, str) and d.startswith("10.") else None)
    MR["in_bibliography"] = MR.key.map(lambda k: all(x.strip() in bib() for x in str(k).split(";")))
    st.dataframe(MR, width="stretch", hide_index=True, column_config={"link": st.column_config.LinkColumn("DOI link", display_text="doi"), "title": st.column_config.TextColumn(width="large")})

st.subheader("Bibliography by topic")
for t, keys in TOPICS.items():
    with st.expander(f"{TOPIC_TITLES.get(t, t)} ({len(keys)})"):
        st.markdown("\n".join(f"- {fmt_ref(k)}" for k in keys))

st.subheader("Full bibliography")
q = st.text_input("filter (author, title, journal, key)", "")
B = bib(); keys = sorted(B, key=lambda k: (B[k].get("year", "0"), k), reverse=True)
hits = [k for k in keys if not q or q.lower() in (k + " " + " ".join(B[k].values())).lower()]
st.caption(f"{len(hits)} of {len(B)} entries · ⚠️ VERIFY = {sum('VERIFY' in B[k].get('note', '') for k in B)}")
st.markdown("\n".join(f"- `{k}` {fmt_ref(k)}" for k in hits))

th = CS / "publication" / "literature" / "theses.csv"
if th.exists():
    st.subheader("Literature theses of Paper 3 (p100 knowledge graph)")
    T = pd.read_csv(th); sec = st.multiselect("section", sorted(T.section.unique()), [])
    st.dataframe(T[T.section.isin(sec)] if sec else T, width="stretch", hide_index=True, column_config={"thesis": st.column_config.TextColumn(width="large")})
