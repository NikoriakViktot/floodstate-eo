# FloodState-EO · Kakhovka 2023 dashboard (Streamlit)

**Live app: <https://floodstate-eo.streamlit.app>** (Streamlit Community Cloud, deployed from `NikoriakViktot/floodstate-eo`,
branch `main`, main file `apps/dashboard/streamlit_app.py`, custom subdomain `floodstate-eo`; the repository README links here).

Reads only committed tables (`case_studies/kakhovka_2023/{tables,publication}`) and the pre-rendered layers in
`apps/dashboard/data/` (classed PNG overlays in EPSG:4326 + GeoJSON context, manifest with sha256). No bulk data, no
rasterio, no FABDEM-derived numeric raster is served.

Run locally: `pip install -r apps/dashboard/requirements.txt && streamlit run apps/dashboard/streamlit_app.py`
Rebuild layers (needs the bulk root): `python case_studies/kakhovka_2023/workflows/paper/p98_dashboard_layers.py`
(reservoir layers only: `... p98_dashboard_layers.py --only reservoir`, after `workflows/m6/p95h_reservoir_maps.py`).
Reservoir drawdown (Maps page, "zoom to → reservoir"): modelled pool by day and day of exposure (p95h/p95f), S1 VH dark surface
(open water or wet mud) by date, S2 k10e classes, water and the 7 indices in display classes (frozen p25 products), all on
the pool + 1 km.
Deploy (Streamlit Community Cloud, share.streamlit.io → Create app → "Deploy a public app from GitHub"): repository
`NikoriakViktot/floodstate-eo`, branch `main`, main file `apps/dashboard/streamlit_app.py`, App URL `floodstate-eo`
(→ https://floodstate-eo.streamlit.app, the address the README links to), Advanced settings → Python 3.12, no secrets.
Every push to `main` redeploys the app; the pages read only committed files, so what the app shows is what `main` holds. If the platform does not pick up this directory's
`requirements.txt`, add a root `requirements.txt` containing `-r apps/dashboard/requirements.txt`.

Licence note: terrain layers derive from FABDEM v1.2 (Hawker et al. 2022, CC BY-NC-SA 4.0) through the seamless DEM and are
provided as rendered classed images for non-commercial use with attribution; they are not covered by the repository's MIT licence.
