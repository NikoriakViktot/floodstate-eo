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
FM6 = CS / "figures" / "m6_v003A"                         # diagnostic figures of the m6 chain (p95zm satellite maps)
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
    st.caption("Theme: light / dark / system — app menu (top right) → Settings → Theme; maps follow with a dark basemap.")


# ---- literature ------------------------------------------------------------------------------------------------------
BIB = REPO / "docs" / "references.bib"
GH = "https://github.com/NikoriakViktot"
SERIES = [  # the Kakhovka series; manuscripts have no DOI yet -- the code repositories are the public record
    ("Paper 1", "Post-breach transformation of the Kakhovka Reservoir: water-surface slopes from ICESat-2, SWOT and gauge observations",
     "manuscript v4", [("SWOT-DNIPRO (levels, slopes, vertical frame)", f"{GH}/SWOT-DNIPRO"), ("icesat2-atl13-kakhovka (ICESat-2 ATL13 water levels)", f"{GH}/icesat2-atl13-kakhovka")], "Paper1_Nikoriak_2026"),
    ("Paper 2", "Bathymetry and a seamless terrain model of the former Kakhovka Reservoir and the lower Dnipro", "in preparation",
     [("SWOT-DNIPRO (seamless DEM, bathymetric bed)", f"{GH}/SWOT-DNIPRO")], "Paper2_Nikoriak_2026"),
    ("Paper 3", "Daily inundation after the Kakhovka dam breach: observation-constrained terrain reconstruction, cross-sensor checks, surface context and weak-label ML (this dashboard)",
     "in preparation", [("floodstate-eo (this repository)", f"{GH}/floodstate-eo")], None),
    ("Paper 4", "The Kakhovka reservoir bowl reconstructed on the historical bathymetry (reservoir water balance)", "planned", [], None),
    ("Paper 5", "HEC-RAS hydrodynamic model calibrated on the daily reconstructed surfaces", "planned", [], None)]
TOPICS = {  # dashboard section -> bibliography keys (docs/references.bib); every entry keeps its VERIFY status visible
    "series": ["Paper1_Nikoriak_2026", "Paper2_Nikoriak_2026"],
    "event": ["Vyshnevskyi_2023", "Gleick_2023", "Shumilova_2025", "Kadam_2024", "Yi_2025", "Monti_2024", "Lehnigk_2026", "UNOSAT_3616_2023", "UNOSAT_3623_2023", "UNEP_2023", "CEOBS_2023", "REACH_2023"],
    "terrain": ["Paper2_Nikoriak_2026", "Hawker_2022", "Hawker_2018", "Matheron_1963", "Renno_2008", "Nobre_2011", "Johnson_2019", "Zheng_2018", "Cohen_2019", "Lindsay_2016", "Rosenfeld_Pfaltz_1966", "Hohle_2009", "Olofsson_2014"],
    "water_surface": ["Paper1_Nikoriak_2026", "Biancamaria_2016", "SWOT_RiverSP_v2", "Altenau_2021", "ATL13_v6", "Denker_2013", "Lehnigk_2026"],
    "s1_flood": ["Torres_2012", "Small_2011", "Lee_1980", "Twele_2016", "Martinis_2022", "Bioresita_2019", "Giustarini_2013", "Tupas_2023", "Wagner_2026", "Lopes_1990", "Otsu_1979", "Shen_2019", "Zhao_2021", "Grimaldi_2020", "Monti_2024"],
    "s2_water": ["Drusch_2012", "Main-Knorn_2017", "McFeeters_1996", "Xu_2006", "Feyisa_2014", "Pekel_2016"],
    "indices": ["Tucker_1979", "McFeeters_1996", "Xu_2006", "Gao_1996", "Wilson_Sader_2002", "Rikimaru_2002", "Diek_2017", "Feyisa_2014", "Lacaux_2007", "Main-Knorn_2017"],
    "k10e": ["Tucker_1979", "McFeeters_1996", "Xu_2006", "Wilson_Sader_2002", "Rikimaru_2002", "Main-Knorn_2017"],
    "rf": ["Breiman_2001", "Belgiu_Dragut_2016", "Pedregosa_2011", "Zanaga_2022", "Valavi_2019", "Roberts_2017", "Pohjankukka_2017", "Olofsson_2014"],
    "unet": ["Ronneberger_2015", "He_2016", "Iakubovskii_2019", "Milletari_2016", "Bonafilia_2020", "Bai_2021", "He_2024", "Maiti_2022", "Apicella_2025", "Roberts_2017", "Valavi_2019"],
    "checks": ["Neuenschwander_2019", "ATL13_v6", "Schaefer_1990", "Stephens_2014", "Hohle_2009", "Efron_1979", "Efron_Tibshirani_1993", "Paper1_Nikoriak_2026", "Paper2_Nikoriak_2026", "Cohen_2019", "Le_2026", "Darnell_2008"],
    "reservoir": ["Paper1_Nikoriak_2026", "Paper2_Nikoriak_2026", "Yi_2025", "Vyshnevskyi_2023", "Shumilova_2025", "Kozlova_2024", "Pichura_2024", "Pichura_2025", "Maksymenko_2026", "Magas_2026", "Hryshchenko_2024", "Lehnigk_2026"],
}
METHOD_REFS = REPO / "docs" / "method_references.csv"   # method -> source -> DOI -> verification status (docs/METHOD_REFERENCES.md)
TOPIC_TITLES = {"series": "Kakhovka series", "event": "The 2023 event and operational products", "terrain": "Terrain, DEM and HAND", "water_surface": "Water surface: SWOT and gauges",
                "s1_flood": "Sentinel-1 flood / water mapping", "s2_water": "Sentinel-2 water mapping", "indices": "Spectral indices", "k10e": "k10e rule-based surface classes (reservoir)",
                "rf": "Random forest surface classification (RF20)", "unet": "U-Net and learning from weak labels", "checks": "Independent checks (ICESat-2, terrain)", "reservoir": "Kakhovka reservoir: drawdown and the exposed bed"}
INDICES = {  # formula on Sentinel-2 L2A bands (offset-corrected reflectance), what it responds to, the reference, how it is used here
    "NDVI": ("(B08 − B04) / (B08 + B04)", "green vegetation (chlorophyll, canopy)", ["Tucker_1979"], "RF20 feature; k10e vegetation thresholds 0.15 / 0.3; revegetation of the reservoir bed (T25)"),
    "NDWI": ("(B03 − B08) / (B03 + B08)", "open water (McFeeters)", ["McFeeters_1996"], "S2 water rule NDWI > 0 (with MNDWI > 0 and SCL); RF20 feature"),
    "MNDWI": ("(B03 − B11) / (B03 + B11)", "open water, suppresses built-up (Xu)", ["Xu_2006"], "S2 water rule MNDWI > 0; RF20 feature; T25 drawdown signal"),
    "NDMI": ("(B08 − B11) / (B08 + B11)", "vegetation / surface moisture (Gao's NIR–SWIR 'NDWI')", ["Gao_1996", "Wilson_Sader_2002"], "k10e moisture threshold 0.1 (wet sediment, reed); RF20 feature"),
    "BSI": ("((B11 + B04) − (B08 + B02)) / ((B11 + B04) + (B08 + B02))", "bare soil / exposed sediment", ["Rikimaru_2002", "Diek_2017"], "k10e bare-sediment threshold 0.1; RF20 feature; the exposed bed after 06-06"),
    "AWEIsh": ("B02 + 2.5·B03 − 1.5·(B08 + B11) − 0.25·B12", "water with shadow suppression (Feyisa)", ["Feyisa_2014"], "RF20 feature; display classes only (not normalised)"),
    "NDTI": ("(B04 − B03) / (B04 + B03)", "water turbidity (Lacaux)", ["Lacaux_2007"], "RF20 feature; turbid shallow water on the drained bed"),
}
CLASSIFIERS = [  # product, method, reference / target, where, literature
    ("S2 water (water3)", "rule: NDWI > 0 AND MNDWI > 0 AND SCL permits water; not observed → NODATA", "none (physical thresholds)", "downstream frames, reservoir (T23, Fig11)", ["McFeeters_1996", "Xu_2006", "Main-Knorn_2017"]),
    ("k10e surface classes", "rule-based on offset-corrected indices: NDVI 0.15 / 0.3, NDMI 0.1, BSI 0.1, water3 → 9 classes", "none (thresholds fixed a priori, not yet validated against samples)", "reservoir (T24, Fig11 f–g)", ["Tucker_1979", "Wilson_Sader_2002", "Rikimaru_2002", "McFeeters_1996", "Xu_2006"]),
    ("RF20 surface classes", "random forest, 200 trees, min leaf 5, balanced subsample; PRE-event S2 composites (7 indices, med/min/max); UNCERTAIN if top-class probability < 0.5", "ESA WorldCover 2021 (weak reference); 5-fold spatial-block CV on 5 km blocks + B1↔B2 transfer", "lower Dnipro frames B1 + B2 (T09–T10c, FigS04)", ["Breiman_2001", "Belgiu_Dragut_2016", "Pedregosa_2011", "Zanaga_2022", "Roberts_2017", "Valavi_2019"]),
    ("S1 dark water (downstream)", "per-scene VV/VH dark-water mask (M3), minus pre-breach water", "none (thresholds)", "downstream frames (T13, Fig04)", ["Torres_2012", "Small_2011", "Lee_1980", "Lopes_1990", "Otsu_1979", "Twele_2016", "Martinis_2022"]),
    ("S1 VH dark surface (reservoir)", "VH dB < per-date Otsu over all covered cells, clamped [−24, −15] dB, 3×3 majority; = open water OR smooth wet mud", "none (thresholds)", "reservoir (T23, FigS08 e–h)", ["Otsu_1979", "Twele_2016", "Bioresita_2019"]),
    ("U-Net flood state", "U-Net (ResNet encoder) on S1/S2 inputs, trained on weak labels v003_A; frozen validation threshold", "weak reference labels (agreement, never accuracy)", "frames B1 + B2 (T04–T08, Fig03)", ["Ronneberger_2015", "He_2016", "Iakubovskii_2019", "Milletari_2016", "He_2024", "Maiti_2022"]),
    ("Terrain reconstruction", "connected DEM < WSE rule on the seamless DEM with HAND domain, SWOT + gauge water surface", "independent physical (ICESat-2, S1 as checks)", "Dnipro corridor (T11–T12, Fig04, Fig07)", ["Renno_2008", "Nobre_2011", "Zheng_2018", "Hawker_2022", "Paper1_Nikoriak_2026", "Paper2_Nikoriak_2026"]),
]


def _parse_bib(text: str) -> dict:
    """Minimal BibTeX reader: {key: {type, field: value}}; braces nest, values keep their text."""
    out, i, n = {}, 0, len(text)
    while True:
        i = text.find("@", i)
        if i < 0:
            break
        j = text.find("{", i); typ = text[i + 1:j].strip().lower(); k = text.find(",", j); key = text[j + 1:k].strip()
        depth, p = 1, j + 1
        while p < n and depth:
            depth += {"{": 1, "}": -1}.get(text[p], 0); p += 1
        body, e, q = text[k + 1:p - 1], {"type": typ}, 0
        while q < len(body):
            eq = body.find("=", q)
            if eq < 0:
                break
            name = body[q:eq].strip(" ,\n\t").lower(); r = eq + 1
            while r < len(body) and body[r] in " \t\n":
                r += 1
            if r < len(body) and body[r] in "{\"":
                close = "}" if body[r] == "{" else "\""; d, s = 1, r + 1
                while s < len(body) and d:
                    if close == "}":
                        d += {"{": 1, "}": -1}.get(body[s], 0)
                    elif body[s] == "\"":
                        d = 0
                    s += 1
                val = body[r + 1:s - 1]
            else:
                s = body.find(",", r); s = len(body) if s < 0 else s; val = body[r:s]
            e[name] = " ".join(val.replace("{", "").replace("}", "").replace("\\&", "&").split()); q = s + 1
        out[key] = e; i = p
    return out


@st.cache_data(show_spinner=False)
def bib() -> dict:
    return _parse_bib(BIB.read_text()) if BIB.exists() else {}


def fmt_ref(key: str) -> str:
    e = bib().get(key)
    if e is None:
        return f"`{key}` — not in docs/references.bib"
    names = [a.strip() for a in e.get("author", "").split(" and ") if a.strip()]
    fam = [a.split(",")[0].strip() if "," in a else a for a in names]              # no comma: corporate or single-token author, keep whole
    au = (fam[0] + " et al." if len(fam) > 2 else " & ".join(fam)) if fam else e.get("institution", e.get("publisher", key))
    venue = e.get("journal") or e.get("booktitle") or e.get("publisher") or e.get("howpublished") or ""
    vol = f" {e['volume']}" if e.get("volume") else ""; pg = f", {e['pages'].replace('--', '–')}" if e.get("pages") else ""
    doi = e.get("doi"); url = f"https://doi.org/{doi}" if doi else e.get("url", "")
    link = f" [{('doi:' + doi) if doi else 'link'}]({url})" if url else ""
    flag = " ⚠️ *VERIFY*" if "VERIFY" in e.get("note", "") else ""
    src = f" *{venue}*{vol}{pg}." if venue else (f" {e['note'].split(';')[0]}." if e.get("note") else "")
    return f"{au} ({e.get('year', 'n.d.')}). {e.get('title', '')}.{src}{link}{flag}"


def refs(keys, title: str = "📚 Relevant literature", expanded: bool = False, where=None):
    """Expander with formatted references for the keys (topic names from TOPICS are expanded)."""
    ks = []
    for k in keys:
        for kk in TOPICS.get(k, [k]):
            if kk not in ks:
                ks.append(kk)
    box = (where or st).expander(title, expanded=expanded)
    box.markdown("\n".join(f"- {fmt_ref(k)}" for k in ks))
    return box

# ---- basemaps (live tiles; attribution shown next to the map) and styled overlays ------------------------------------
BASEMAPS = {
    # CARTO's basemap tiles require an API key since 2026 (the tiles come back as an 'API KEY REQUIRED' placeholder), so the
    # gray and dark canvases are Esri's, which need no key; both stop at zoom 16 (max_native_zoom, upscaled beyond)
    "Gray (Esri Light Gray Canvas)": dict(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
                                          attr="Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors, and the GIS User Community", max_native_zoom=16,
                                          text="Basemap: Esri World Light Gray Canvas (c) Esri -- Esri, HERE, Garmin, (c) OpenStreetMap contributors, and the GIS User Community; live tiles, never cached"),
    "Dark (Esri Dark Gray Canvas)": dict(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
                                         attr="Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors, and the GIS User Community", max_native_zoom=16,
                                         text="Basemap: Esri World Dark Gray Canvas (c) Esri -- Esri, HERE, Garmin, (c) OpenStreetMap contributors, and the GIS User Community; live tiles, never cached"),
    "OpenStreetMap": dict(tiles="OpenStreetMap", attr=None, text="Basemap: (c) OpenStreetMap contributors (ODbL)"),
    "Satellite: Sentinel-2 cloudless 2022 (EOX)": dict(
        tiles="https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2022_3857/default/g/{z}/{y}/{x}.jpg",
        attr='<a href="https://s2maps.eu">Sentinel-2 cloudless</a> by <a href="https://eox.at">EOX IT Services GmbH</a> '
             "(CC BY-NC-SA 4.0; contains modified Copernicus Sentinel data 2022)",
        text="Basemap: Sentinel-2 cloudless (https://s2maps.eu) by EOX IT Services GmbH, CC BY-NC-SA 4.0, contains modified Copernicus "
             "Sentinel data 2022 -- the year before the breach; live WMTS, non-commercial use"),
    "Satellite: Esri World Imagery": dict(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
        text="Basemap: Esri World Imagery (c) Esri -- Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community; "
             "live tiles, acquisition dates vary and may postdate the breach; never cached or redistributed by this app"),
}
S2RGB_TEXT = ("Overlay: Sentinel-2 L2A true colour of the selected date, clouds as photographed, processed by the authors (p97c); "
              "contains modified Copernicus Sentinel data; a viewing product, not an input of any result")
#: the satellite maps of the reed-bed evidence (p95zm): zone -> label, kind -> file stem
SATMAPS = {"delta": "Kherson delta (ZONE_2)", "floodway": "floodway dam -> Kherson (ZONE_4)"}
SATMAP_KINDS = {"every index (cloud-free period composites)": "index_classes", "Sentinel-1 VV, orbit 14 (spring median / 9 June / 21 June)": "s1_vv",
                "k10e surface classes (best-covered dates)": "k10e", "NDVI": "NDVI", "NDWI": "NDWI", "MNDWI": "MNDWI", "NDMI": "NDMI", "BSI": "BSI", "AWEIsh": "AWEIsh", "NDTI": "NDTI",
                "every index and backscatter by stratum and day of year (p95z)": "p95z"}
OWN_S2 = dict(id="s2_truecolour_2022-06-13", file="context/s2_truecolour_2022-06-13.jpg",
              name="Sentinel-2 true colour 13/20 June 2022 (own processing, as in the paper)",
              text="Overlay: Sentinel-2 L2A true colour, 13 and 20 June 2022 (one year before the breach), processed by the authors; "
                   "contains modified Copernicus Sentinel data 2022")
#: how the support classes of the new inundation are drawn ON TOP of the blue flood layer: one physical category (new water),
#: reliability as pattern -- weak = orange hatch, cross-river = red outline, retained water (memory sensitivity) = grey hatch
SUPPORT_STYLE = {3: ("hatch", (237, 161, 0)), 4: ("outline", (227, 73, 72)), 6: ("hatch", (120, 128, 138))}


def theme_type() -> str:
    """'light' or 'dark': the theme the viewer chose in the app menu (Settings -> Theme; .streamlit/config.toml defines both)."""
    try:
        t = st.context.theme
        return (getattr(t, "type", None) or "light")
    except Exception:                                                        # no browser context (tests, bare mode)
        return "light"


def ink() -> str:
    """The line colour that reads on the active theme: near-black on light, near-white on dark (Plotly follows the Streamlit theme)."""
    return "#f0f0f0" if theme_type() == "dark" else "#0b0b0b"


def basemap_index() -> int:
    """Default basemap of the maps: the dark tiles under the dark theme, the gray ones otherwise."""
    return list(BASEMAPS).index("Dark (Esri Dark Gray Canvas)" if theme_type() == "dark" else "Gray (Esri Light Gray Canvas)")


def base_map(location, zoom, choice: str):
    import folium
    b = BASEMAPS[choice]
    m = folium.Map(location=location, zoom_start=zoom, tiles=None, control_scale=True)
    folium.TileLayer(tiles=b["tiles"], attr=b["attr"], name=choice, control=False, max_zoom=18, max_native_zoom=b.get("max_native_zoom", 18)).add_to(m)
    return m


@st.cache_data(show_spinner=False)
def styled_overlay(file: str, mtime: float, scale: int = 2):
    """RGBA array (scale x the PNG) drawing the support classes of a palette PNG as hatch / outline over transparency.
    Rendered in the app from the class PNG the dashboard already carries -- no new data file."""
    import numpy as np
    from PIL import Image
    a = np.array(Image.open(DATA / file).convert("P"))
    codes = np.repeat(np.repeat(a, scale, 0), scale, 1)
    H, W = codes.shape; out = np.zeros((H, W, 4), "u1")
    ii, jj = np.indices((H, W)); stripes = ((ii + jj) % 8) < 3
    for code, (kind, rgb) in SUPPORT_STYLE.items():
        m = codes == code
        if not m.any():
            continue
        if kind == "hatch":
            sel = m & stripes
        else:                                                                # outline: cells of the class minus their interior
            inner = m.copy(); inner[1:, :] &= m[:-1, :]; inner[:-1, :] &= m[1:, :]; inner[:, 1:] &= m[:, :-1]; inner[:, :-1] &= m[:, 1:]
            sel = m & ~inner
        out[sel, :3] = rgb; out[sel, 3] = 230
    return out
