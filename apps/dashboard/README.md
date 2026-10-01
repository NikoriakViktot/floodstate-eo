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

## Theme

`.streamlit/config.toml` (repository root; Streamlit Community Cloud reads it) defines a light and a dark variant of the
app theme (`[theme.light]`, `[theme.dark]`, Streamlit >= 1.64). The viewer picks light / dark / system in the app menu
(top right -> Settings -> Theme); the choice is stored per browser. The maps follow: under the dark theme the default
basemap is Esri Dark Gray Canvas (`lib.basemap_index`, `st.context.theme`).

## Basemaps and overlays (Maps and Surface-context pages)

- **Basemaps** (live tiles, never cached or committed; attribution shown under the map): Gray (Esri Light Gray Canvas), OpenStreetMap
  (ODbL), *Sentinel-2 cloudless 2022* by EOX IT Services GmbH (https://s2maps.eu, CC BY-NC-SA 4.0, contains modified Copernicus
  Sentinel data 2022 -- the year before the breach; non-commercial use), *Esri World Imagery* (Esri, Maxar, Earthstar Geographics,
  and the GIS User Community; acquisition dates vary and may postdate the breach).
- **Sentinel-2 true colour of every archive date** (`data/s2rgb/<date>.jpg`, Surface-context page): L2A of every date whose tiles
  cover the lower Dnipro (T36TUS/TUT/TVS/TVT/TWS/TWT), rendered on the dashboard box with the clouds as photographed
  (`workflows/paper/p97c_s2_truecolour_dates.py`; clear share from the SCL mask in the date label; dates under 2 % clear are
  listed but not rendered). A viewing product -- not an input of any result; contains modified Copernicus Sentinel data.
- **Satellite maps of the reed-bed evidence** (Surface-context page): the p95zm cloud-free composites of the classified indices,
  the Sentinel-1 VV orbit-14 series and the k10e classes per zone (`case_studies/.../figures/m6_v003A/p95zm_*.png`), and FigS19.
- **Own Sentinel-2 true colour** (`data/context/s2_truecolour_2022-06-13.jpg`): L2A of 13 and 20 June 2022 processed by the
  authors (`workflows/paper/p97b_s2_basemap.py`; contains modified Copernicus Sentinel data 2022) -- the same image under the
  paper's Fig07 / FigS14 / FigS16, so the dashboard and the figures show one geomorphological context (a WorldCover class such as
  "cropland" says nothing about the sandy terrace beneath it).
- **Reconstruction view**: *flood only* = the reconstructed new water of the day (blue: one physical category); *flood + support*
  = the same, with its reliability drawn on top by the app from the class PNG (`lib.styled_overlay`): weak water-surface support
  (> 10 km to the nearest SWOT node) as orange hatch, cross-river (Inhulets valley served by a node of another river) as red
  outline, retained water of the memory sensitivity (not in the primary; D-MEMORY) as grey hatch; *support only* = the solid
  support classes. Thresholds are operational (T11k); the full reconstruction is the primary product.
- **Sensor masks on the same map** (Maps page, "Sentinel-1 / Sentinel-2 masks"): Sentinel-1 dark water per acquisition date (new
  dark water and dark water on pre-breach water, 20 m zone cache; blind spots under forest and reed, dry sand can be dark) and
  Sentinel-2 water per date (NDWI > 0 and MNDWI > 0 on cloud-free cells of the 10 m index stacks; new water and water on
  pre-breach water; dates with < 30 % of the corridor observed are marked unreliable), each with its valid footprint -- so a
  reconstructed component can be read against the observations and the imagery in one view. Not observed is not dry.
- **Inundation probability** (Maps page, "inundation probability"): P(new inundation) per cell over the 1000 coherent Monte-Carlo
  worlds for the key dates (p95e cellprob, T12g): P >= 0.95, 0.75-0.95, 0.50-0.75 together are the median world -- the map product
  of the ensemble; 0.25-0.50 and 0.05-0.25 are marginal cells whose connection hangs on a sill within the water-surface or terrain
  uncertainty. The daily terrain layer is the nominal world (one world, a diagnostic).
- Since D-SEED (2026-09-30) the primary reconstruction seeds the connectivity from the pre-breach river network; the superseded
  all-prewater seeding is documented in the paper's T11m-T11o and FigS16, not served as a layer.
