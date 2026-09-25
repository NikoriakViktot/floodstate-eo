from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import caption, header, layers, manifest, table

st.set_page_config(page_title="Data & provenance", layout="wide")
header("Data, provenance and licences", "every number on this dashboard resolves to a committed table cell; every layer to a manifest entry with sha256")
st.subheader("Data inventory (T01)"); st.caption(caption("T01")); st.dataframe(table("T01"), width="stretch", hide_index=True)
st.subheader("Area accounting with semantics (T16)"); st.caption(caption("T16")); st.dataframe(table("T16"), width="stretch", hide_index=True)
m = manifest(); L = layers()
st.subheader("Publication tables manifest"); st.write(f"generated {m['generated_utc']} · commit `{m['git_commit']}` · {len(m['tables'])} tables · {len(m['sources'])} source files")
st.dataframe(pd.DataFrame([dict(table=k, evidence_level=v["evidence_level"], rows=v["rows"], sha256=v["sha256"][:12], sources=", ".join(v["sources"][:3])) for k, v in m["tables"].items()]), width="stretch", hide_index=True)
st.subheader("Map layers manifest"); st.write(f"{L['n_layers']} layers, {L['total_bytes'] / 1e6:.1f} MB, generated {L['generated_utc']}")
st.dataframe(pd.DataFrame([dict(id=l["id"], group=l["group"], bytes=l["bytes"], sha256=l["sha256"][:12], source=l.get("source", "")) for l in L["layers"]]), width="stretch", hide_index=True)
st.subheader("Licences and attribution")
st.markdown(f"""
- Code: MIT (repository licence). Tables and figures: CC BY 4.0 with attribution to the authors.
- {L.get('licence_note', '')}
- Sentinel-1/2: Copernicus Sentinel data 2023. SWOT L2_HR_RiverSP v2.0: NASA/CNES via PO.DAAC. ICESat-2 ATL08: NASA NSIDC. ESA WorldCover 2021 v200: CC BY 4.0.
- The Kherson gauge series: UkrHMC river hydrological yearbook (see Paper 1). Reservoir polygon and zone geometries: SWOT-DNIPRO (sibling repository).
- Bulk rasters (10 m frames, 20 m terrain products, S1 caches) are not redistributed; see `docs/REPRODUCIBILITY.md` (three reproduction levels).
""")
