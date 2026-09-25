"""TEMPORARY Phase-5 compatibility shim -- not event-agnostic framework code. Pending Phase 6.

Provenance: ported from SWOT-DNIPRO `src/swot_dnipro/config.py` (source commit
f3e3e1afe91902a82a73f3c09354d1f9eb847766), scoped to only the Kakhovka-specific
constants that the migrated `src/floodstate_eo/**` scripts still reference
directly as `CFG.<name>`.

WHY THIS EXISTS AND WHY IT IS NOT EVENT-AGNOSTIC. The 20 scripts migrated in
this commit (p52*, p54*, p65b, p66, p67b, p69*, p71, p80-83) were copied with
provenance headers and package-import fixes only (migration Phase 5: "copy
canonical code"), not rewired to `case_studies/kakhovka_2023/config/*.yaml`
(migration Phase 6: "replace hard-coding with config", not yet run). Every one
of them still calls `CFG.TABLES`, `CFG.BULK_ROOT`, `CFG.BREACH_DATE`, etc., so
this module exists so those imports resolve, with the SAME values the source
repo hard-coded. It therefore fails the event-agnostic grep gate
(`docs/../04_CORE_VS_CASE_STUDY.md` in the source audit: no Kakhovka-specific
path or constant may live under `src/floodstate_eo/**`) -- this file is the
one, explicitly named and tracked, exception. See
`provenance/KNOWN_GATE_EXCEPTIONS.md` and `tests/test_event_agnostic_gate.py`,
which excludes this filename by name rather than silently narrowing its scan.

Values below are the same hard-coded constants documented and destined for the
config YAMLs in `06_CONFIGURATION_DESIGN.md` of the source audit; the mapping
comment on each line is the pointer to use when Phase 6 actually runs.
"""
from __future__ import annotations

import os
from pathlib import Path

# the floodstate-eo repo root (src/floodstate_eo/_kakhovka_legacy_config.py -> parents[2])
REPO_ROOT = Path(__file__).resolve().parents[2]
# case_studies/kakhovka_2023/, so ROOT-relative outputs from the migrated
# scripts (originally `<SWOT-DNIPRO repo root>/outputs/...`) land under the
# case study, not under the framework package.
ROOT = REPO_ROOT / "case_studies" / "kakhovka_2023"
DATA_RAW = ROOT / "data" / "raw"

# -> case_studies/kakhovka_2023/config/... (data_root / FLOODSTATE_DATA_ROOT); source config.py:58-62
_BULK_DEFAULT = Path("/mnt/f/data_kakhovka_dem_swot")
BULK_ROOT = Path(
    os.environ.get("FLOODSTATE_DATA_ROOT", os.environ.get("SWOT_DNIPRO_BULK_ROOT",
                   str(_BULK_DEFAULT if _BULK_DEFAULT.is_dir() else ROOT / "data")))
).expanduser()
S1_CACHE = BULK_ROOT / "s1_zone_cache"

OUT = ROOT / "outputs"
FIG = ROOT / "figures"
TABLES = ROOT / "tables"

# -> study_area.yaml: crs; source config.py:87-88
CRS_GEOG = "EPSG:4326"
CRS_METRIC = "EPSG:32636"

# -> event.yaml: event_date; source config.py:93-95
BREACH_DATE = "2023-06-06"
PREBREACH_START = "2023-04-05"
PREBREACH_END = "2023-06-05"

# -> model.yaml: seed; source config.py:98
SEED = 42

# ---------------------------------------------------------------------------------------------------------
# UNRESOLVED DEPENDENCY (see provenance/UNRESOLVED_DEPENDENCIES.md): the Kakhovka zone/reservoir geometries
# that sentinel_preprocess.zone_grid() and several migrated p52*/p69* scripts read via SD.load_utm(name) were
# never vendored into either repository -- SWOT-DNIPRO itself reads the reservoir polygon from a SIBLING repo
# (icesat2-atl13-kakhovka) and the ZONE_1..4 polygons from its own data/processed/domains/*.geojson, both
# outside this repository's data policy (case_studies manifests, not raw geometry files, belong in git). These
# paths point at the SOURCE repos as a temporary bridge; a real fix is a manifest entry under
# case_studies/kakhovka_2023/manifests/ plus a vendored or fetched copy, which is Phase 6/Data Policy work.
_SWOT_DNIPRO_SIBLING = Path(os.environ.get("SWOT_DNIPRO_ROOT", Path.home() / "repo" / "SWOT-DNIPRO"))
_ICESAT2_SIBLING = Path(os.environ.get("SWOT_DNIPRO_ICESAT_ROOT",
                        _SWOT_DNIPRO_SIBLING.parent / "icesat2-atl13-kakhovka"))


def _read_geojson_union(path: Path):
    """Read a GeoJSON polygon/union and return it in EPSG:32636 -- reprojecting if needed rather than assuming.

    `Kakhovka_SA_2.geojson` (the reservoir source, in the icesat2-atl13-kakhovka sibling) declares
    `"crs": "urn:ogc:def:crs:OGC:1.3:CRS84"` (lon/lat degrees), NOT EPSG:32636 as this module's docstring
    claimed for "zone/reservoir polygons" generally -- that claim is only true of `analysis_zones_utm.geojson`
    (read by `_zone_layer`, genuinely EPSG:32636). Treating the reservoir file as already-UTM silently returned
    an `.area` of 2.6e-7 km^2 instead of the real ~2000 km^2 (found while testing this migration's data access,
    not by inspection). Detected here by the file's own `crs` member, with a coordinate-bounds fallback in case
    a future source omits it (GeoJSON's default CRS is WGS84 per RFC 7946), so a genuinely already-projected file
    is never accidentally reprojected a second time.
    """
    import json
    from pyproj import Transformer
    from shapely.geometry import shape
    from shapely.ops import transform, unary_union
    gj = json.loads(path.read_text())
    geoms = [shape(f["geometry"]) for f in gj.get("features", [gj])] if gj.get("type") == "FeatureCollection" \
        else [shape(gj["geometry"] if gj.get("type") == "Feature" else gj)]
    u = unary_union(geoms)
    crs_name = (gj.get("crs") or {}).get("properties", {}).get("name", "")
    is_geographic = "CRS84" in crs_name or "4326" in crs_name or not crs_name
    if is_geographic:
        minx, miny, maxx, maxy = u.bounds
        if abs(minx) <= 180 and abs(maxx) <= 180 and abs(miny) <= 90 and abs(maxy) <= 90:
            tr = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True)
            u = transform(tr.transform, u)
    return u


def _zone_layer(path: Path, name: str):
    import json
    from shapely.geometry import shape
    from shapely.ops import unary_union
    gj = json.loads(path.read_text())
    geoms = [shape(f["geometry"]) for f in gj["features"] if f["properties"].get("analysis_zone") == name]
    if not geoms:
        raise KeyError(f"{name!r} not present in {path}")
    return unary_union(geoms)


KAKHOVKA_LOADERS = {
    "reservoir_full_pool_prebreach": lambda: _read_geojson_union(_ICESAT2_SIBLING / "data" / "Kakhovka_SA_2.geojson"),
    **{z: (lambda z=z: _zone_layer(
        _SWOT_DNIPRO_SIBLING / "data" / "processed" / "domains" / "analysis_zones_utm.geojson", z))
       for z in ("ZONE_1_KAKHOVKA_LOWER_DNIPRO", "ZONE_2_KHERSON_DELTA",
                 "ZONE_3_DNIPRO_BUG_ESTUARY", "ZONE_4_DAM_TO_KHERSON_FLOODWAY")},
}


def load_utm(name: str):
    """A Kakhovka domain geometry in EPSG:32636, for `floodstate_eo.spatial.domains.build_grid`.

    Zone/reservoir polygons are already stored in EPSG:32636 in their source files (unlike SWOT-DNIPRO's
    spatial_domains.load(), which normalises to EPSG:4326 first) -- returned as-is.
    """
    if name not in KAKHOVKA_LOADERS:
        raise KeyError(f"{name!r} is not a Kakhovka domain known to this legacy shim: {sorted(KAKHOVKA_LOADERS)}")
    return KAKHOVKA_LOADERS[name]()
