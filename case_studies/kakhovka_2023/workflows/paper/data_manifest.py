# New in floodstate-eo, 2026-09-29 (review 2026-09-28, F16). STATUS: ACTIVE. Reads inputs, changes nothing.
"""data_manifest -- every load-bearing input of the paper's results with its location, source, version, licence, redistribution
status and sha256 (review F16: "data manifest with URL / version / licence / checksum for every load-bearing input").

Entries are declared here, not discovered: an input is load-bearing when a paper table or figure depends on it. Locations:
  repo:   this repository                      bulk:   $FLOODSTATE_DATA_ROOT (CFG.BULK_ROOT; > 100 GB, not in git)
  swot:   the SWOT-DNIPRO sibling repository   icesat: the ICESat-2 / hydrology sibling repository (CFG._ICESAT2_SIBLING)
A path may be a file, a directory (every file hashed, digest = sha256 of the sorted "relpath sha256" lines) or a glob (the same
digest over the matches). URL / version / licence are written only where the repository records them; unknown -> TBD (never
invented). Inputs that cannot be redistributed (FABDEM-derived rasters, national gauge records) say so; the way to rebuild
them is in `provenance/UNRESOLVED_DEPENDENCIES.md` and `docs/REPRODUCIBILITY.md`.

Outputs: <case_study>/manifests/load_bearing_inputs.csv
Run:     python case_studies/kakhovka_2023/workflows/paper/data_manifest.py [--max-gb 60]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import time
from pathlib import Path

import pandas as pd

from floodstate_eo import _kakhovka_legacy_config as CFG

REPO = Path(__file__).resolve().parents[4]
CS = REPO / "case_studies" / "kakhovka_2023"
BASES = {"repo": REPO, "bulk": CFG.BULK_ROOT, "swot": Path(CFG._SWOT_DNIPRO_SIBLING), "icesat": Path(CFG._ICESAT2_SIBLING)}
FAB = ("derived from FABDEM v1.2 (Hawker et al. 2022, doi 10.1088/1748-9326/ac4d4f; CC BY-NC-SA 4.0) and the Paper-2 bed",
       "CC BY-NC-SA 4.0 (FABDEM-derived)", "NO (FABDEM-derived numeric raster; rebuild with the Paper-2 chain)")
CDSE = "https://catalogue.dataspace.copernicus.eu"
# id, role, used_by, location, source, url, version, licence, redistributable, notes
E = [
    # ---- physical reconstruction -------------------------------------------------------------------------------------------
    ("terrain_zone4", "terrain-bed elevation, EVRF2019", "p95 p95e p95j p95c p95l", "bulk:dem_seamless/ZONE_4_DAM_TO_KHERSON_FLOODWAY_dem_evrf2019_20m.tif", FAB[0], "TBD", "Paper 2 seamless model", FAB[1], FAB[2], ""),
    ("terrain_source_zone4", "source mask of the terrain (1/2/5 bed, 3/4 FABDEM)", "p95 p95e p95j p95c", "bulk:dem_seamless/ZONE_4_DAM_TO_KHERSON_FLOODWAY_dem_source_20m.tif", "Paper 2 seamless model", "TBD", "Paper 2", FAB[1], FAB[2], ""),
    ("terrain_zone2", "terrain-bed elevation, EVRF2019", "p95 p95e p95j p95c p95l", "bulk:dem_seamless/ZONE_2_KHERSON_DELTA_dem_evrf2019_20m.tif", FAB[0], "TBD", "Paper 2 seamless model", FAB[1], FAB[2], ""),
    ("terrain_source_zone2", "source mask of the terrain", "p95 p95e p95j p95c", "bulk:dem_seamless/ZONE_2_KHERSON_DELTA_dem_source_20m.tif", "Paper 2 seamless model", "TBD", "Paper 2", FAB[1], FAB[2], ""),
    ("terrain_pool_50m", "pool bed + surroundings, EVRF2019 (reservoir side)", "p95f p95h", "bulk:dem_seamless/dem_seamless_evrf2019_50m.tif", FAB[0], "TBD", "Paper 2 seamless model", FAB[1], FAB[2], ""),
    ("worldcover_zone4", "land-cover class of the terrain bias and the strata", "p95 p95j p95c p95d p73", "bulk:worldcover_frames/ZONE_4_DAM_TO_KHERSON_FLOODWAY/wc_2021_20m.tif", "ESA WorldCover v200 (2021)", "https://esa-worldcover.org/en", "v200", "CC BY 4.0", "YES (attribution)", "resampled to 20 m per zone"),
    ("worldcover_zone2", "land-cover class of the terrain bias and the strata", "p95 p95j p95c p95d p73", "bulk:worldcover_frames/ZONE_2_KHERSON_DELTA/wc_2021_20m.tif", "ESA WorldCover v200 (2021)", "https://esa-worldcover.org/en", "v200", "CC BY 4.0", "YES (attribution)", "resampled to 20 m per zone"),
    ("s1_masks_zone4", "per-scene S1 dark-water masks (checks, labels)", "p95 p95b p95c p95d p60 p77", "bulk:s1_zone_cache/ZONE_4_FLOODWAY_june2023_s32", "Sentinel-1 GRD/RTC (Copernicus) -> M3 per-scene classifier (SWOT-DNIPRO, not migrated)", CDSE, "2023 scenes", "Copernicus Sentinel data (free, open)", "YES (derived masks)", "producer not in this repository (UNRESOLVED_DEPENDENCIES)"),
    ("s1_masks_zone2", "per-scene S1 dark-water masks (checks, labels)", "p95 p95b p95c p95d p60 p77", "bulk:s1_zone_cache/ZONE_2_KHERSON_DELTA_flood_june2023", "Sentinel-1 GRD/RTC (Copernicus) -> M3 per-scene classifier (SWOT-DNIPRO, not migrated)", CDSE, "2023 scenes", "Copernicus Sentinel data (free, open)", "YES (derived masks)", "producer not in this repository (UNRESOLVED_DEPENDENCIES)"),
    ("swot_nodes", "water-surface nodes (EVRF2019 chain of Paper 1)", "p95 p95e p96", "repo:case_studies/kakhovka_2023/tables/p59_swot_flood_nodes.csv", "SWOT L2_HR_RiverSP nodes (PO.DAAC) via the Paper-1 chain (SWOT-DNIPRO p59)", "TBD (PO.DAAC record)", "RiverSP v2.0", "NASA open data", "YES (derived table)", ""),
    ("kherson_gauge", "water-surface anchor (gauge 80805), EVRF2019", "p95 p95e p95k p96", "repo:case_studies/kakhovka_2023/tables/p59_swot_vs_kherson.csv", "UkrHMC gauge 80805 Kherson (daily)", "TBD", "2023", "TBD (national hydrometeorological record)", "TBD", "repository copy (review F16); BS-77 -> EVRF2019 by EPSG:9902"),
    ("icesat2_atl08_kakhovka", "night ground heights (terrain error model, ICESat-2 checks)", "p95j p95c (p57)", "bulk:data_swot/processed/atl08/kakhovka_atl08_terrain.parquet", "ICESat-2 ATL08 (NSIDC), Paper-2 pull", "TBD (NSIDC)", "TBD", "NASA open data", "YES", ""),
    ("icesat2_atl08_lower_dnipro", "night ground heights (20 m segments)", "p95j p95c (p57)", "bulk:data_swot/processed/atl08/lower_dnipro_atl08_20m_raw.parquet", "ICESat-2 ATL08 (NSIDC), Paper-2 pull", "TBD (NSIDC)", "TBD", "NASA open data", "YES", ""),
    ("icesat2_atl08_liman", "night ground heights (20 m segments)", "p95j p95c (p57)", "bulk:data_swot/processed/atl08/liman_atl08_20m_raw.parquet", "ICESat-2 ATL08 (NSIDC), Paper-2 pull", "TBD (NSIDC)", "TBD", "NASA open data", "YES", ""),
    ("egg2015", "quasigeoid of the vertical chain", "p57 p59 (SWOT-DNIPRO), p95j", "icesat:data/1_data/egg_2015.tif", "EGG2015 European Gravimetric Quasigeoid", "TBD", "2015", "TBD", "TBD", ""),
    ("epsg9902_grid", "BS-77 -> EVRF2019 grid (gauge zeros)", "p95k", "icesat:data/external/datum/ua_2019z.asc", "EPSG:9902 transformation grid", "TBD", "TBD", "TBD", "TBD", ""),
    ("p57_accuracy", "Paper-2 terrain accuracy table (T18)", "p96 p95 (fallback)", "repo:case_studies/kakhovka_2023/tables/p57_dem_accuracy_night.csv", "Paper 2 / SWOT-DNIPRO p57", "", "", "this repository", "YES", ""),
    ("floodplain_domain", "p42 terrain-eligible floodplain (accounting region)", "p95 p95l p92", "swot:data/processed/domains/below_dam_floodplain_utm.geojson", "SWOT-DNIPRO p42", "", "", "maintainer's", "TBD", "sibling repository (UNRESOLVED_DEPENDENCIES #3)"),
    ("yearbook_2023_daily", "withheld gauges Kalynivske 80575 / Mykolaiv 98027, daily", "p95k", "icesat:data/1_data/data/parquet/*/daily/post_id=*/year=2023/data.parquet", "UkrHMC hydrological yearbook 2023, vol. 2, table 1.2 (ingested)", "TBD", "2023", "TBD (national hydrometeorological record)", "TBD", ""),
    ("yearbook_2023_monthly", "withheld gauges: monthly highest levels", "p95k", "icesat:data/1_data/data/parquet/*/monthly/post_id=*/year=2023/data.parquet", "UkrHMC hydrological yearbook 2023 (ingested)", "TBD", "2023", "TBD (national hydrometeorological record)", "TBD", ""),
    # ---- reservoir side --------------------------------------------------------------------------------------------------
    ("dniprohes_releases", "inflow to the pool", "p95f p95i", "swot:outputs/tables/dniprohes_releases.csv", "DniproHES daily releases (post 80039)", "TBD", "2023", "TBD", "TBD", "sibling repository"),
    ("pool_levels_2023", "pool levels (SWOT outlet, Nikopol, Rozumivka, G-REALM, ICESat-2, Yi)", "p95f p95i p97", "swot:outputs/tables/p61_pool_levels_2023.csv", "SWOT-DNIPRO p61 (per-row sources)", "", "", "mixed (per row)", "TBD", "sibling repository"),
    ("k5_gauge_levels", "Rozumivka 80959 levels, EVRF2019", "p95i", "swot:outputs/tables/k5_gauge_levels_evrf2019.csv", "UkrHMC gauge records via SWOT-DNIPRO k5", "TBD", "2023", "TBD", "TBD", "sibling repository"),
    ("swot_outlet_drawdown", "SWOT 0.5 km below the dam", "p95i", "swot:outputs/tables/p60_swot_outlet_drawdown.csv", "SWOT-DNIPRO p60", "", "", "NASA open data (derived)", "TBD", "sibling repository"),
    ("design_hypsometry_table19", "design level-area-volume (Table 19)", "p95f p95i", "swot:outputs/tables/hist2_hypsometry.csv", "Dnipro-reservoirs monograph, Table 19 (transcribed)", "", "", "TBD (monograph)", "TBD", "sibling repository"),
    ("design_hypsometry_reaches", "design curve per reach (Tables 19/21)", "p95i", "swot:data/historical/historical_level_area_volume.csv", "Dnipro-reservoirs monograph (transcribed)", "", "", "TBD (monograph)", "TBD", "sibling repository"),
    ("reservoir_reaches", "reaches at NPG / GMO (Table 21)", "p95i", "swot:data/historical/historical_reservoir_reaches.csv", "Dnipro-reservoirs monograph (transcribed)", "", "", "TBD (monograph)", "TBD", "sibling repository"),
    ("yi2025_reservoir_area", "literature comparison (Fig09b, T23)", "p97 p96", "swot:outputs/tables/p61_yi2025_reservoir_area.csv", "Yi et al. 2025 (WRR), authors' archive Zenodo 14639520 (observations.mat obs.A, Sentinel-1)", "https://doi.org/10.5281/zenodo.14639520", "code_share_v2", "as published by the authors", "TBD", "context, not validation"),
    # ---- ML diagnostics --------------------------------------------------------------------------------------------------
    ("hand_zone4", "HAND input of U2/U2b; hand rule (sensitivity)", "p86 p95", "bulk:floodplain/ZONE_4_DAM_TO_KHERSON_FLOODWAY/ZONE_4_DAM_TO_KHERSON_FLOODWAY_hand_m.tif", FAB[0], "TBD", "Paper 2", FAB[1], FAB[2], ""),
    ("hand_zone2", "HAND input of U2/U2b; hand rule (sensitivity)", "p86 p95", "bulk:floodplain/ZONE_2_KHERSON_DELTA/ZONE_2_KHERSON_DELTA_hand_m.tif", FAB[0], "TBD", "Paper 2", FAB[1], FAB[2], ""),
    # ---- figure basemap (not an input of any result): own Sentinel-2 true colour, p97b (D-SEED text pass 2026-09-30) ----------------
    ("s2_truecolour_2022_r107", "Sentinel-2 L2A 13 June 2022 (R107, T36TUS/TUT/TVS/TVT) and 3 June 2022 fills: true-colour basemap of Fig07 / FigS14 / FigS16 and the dashboard overlay", "p97b p97 p98",
     "bulk:s2_zone_fetch/S2A_MSIL2A_202206[01]3T084611_N0510_R107_T36T[UV][ST]_*.SAFE.zip", 'Copernicus Sentinel-2 L2A (ESA) via CDSE', 'https://catalogue.dataspace.copernicus.eu', 'N0510', "Copernicus Sentinel data policy: free, full and open access; attribution 'contains modified Copernicus Sentinel data'", 'YES (public archives; the derived true-colour mosaic carries the attribution)', "cloud + shadow 2-6 % over the reach; SCL-masked; stretch 0-0.30, gamma 0.9 (tables/p97b_s2_basemap_manifest.json)"),
    ("s2_truecolour_2022_r064", "Sentinel-2 L2A 20 June 2022 (R064, T36TWS/TWT) and 3 June 2022 T36TWS: the W squares (Kozachi Laheri - dam) of the same basemap", "p97b p97 p98",
     "bulk:data_swot/sentinel/S2A_MSIL2A_20220[6]*_T36TW[ST]_*.SAFE.zip", 'Copernicus Sentinel-2 L2A (ESA) via CDSE', 'https://catalogue.dataspace.copernicus.eu', 'N0510', "Copernicus Sentinel data policy: free, full and open access; attribution 'contains modified Copernicus Sentinel data'", 'YES (public archives; the derived true-colour mosaic carries the attribution)', "0-2 % cloud over E 500-540 km"),
    ("s2_truecolour_2023_0618", "Sentinel-2 L2A 18 June 2023 (R107, T36TUS/TUT/TVS/TVT/TWT): the recession panel of FigS16", "p97b p97",
     "bulk:sentinel_event_2023/S2A_MSIL2A_20230618T084601_N0510_R107_T36T*_*.SAFE.zip", 'Copernicus Sentinel-2 L2A (ESA) via CDSE', 'https://catalogue.dataspace.copernicus.eu', 'N0510', "Copernicus Sentinel data policy: free, full and open access; attribution 'contains modified Copernicus Sentinel data'", 'YES (public archives; the derived true-colour mosaic carries the attribution)', "7-14 % cloud; no T36TWS of that week in the archive"),
    ("copdem_glo30", "Copernicus DEM GLO-30 tiles N46E032 / N46E033 (EGM2008): independent surface model in the saddle audit of the lowland south of Krynky (p95p, T15d-T15f, FigS18); not an input of any reconstruction", "p95p",
     "bulk:copdem/Copernicus_DSM_COG_10_N46_00_E03[23]_00_DEM.tif", "ESA Copernicus DEM (Airbus), AWS open data bucket copernicus-dem-30m", "https://copernicus-dem-30m.s3.amazonaws.com/", "2021 release (COG)",
     "Copernicus DEM licence (free use with attribution: 'produced using Copernicus WorldDEM-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA')", "YES (public tiles)", "downloaded 2026-09-30"),
    # ---- independent observations for diagnostic cross-checks (not inputs of any result), 2026-09-30 ------------------------------------------
    ("unosat_3614_fl20230606ukr", "UNOSAT product 3614, activation FL20230606UKR: ICEYE flood / water / urban layers of 7 June 2023 12:18-13:01 UTC, Landsat-9 water of 9 June, multi-sensor flood of 6-9 June -- the external cross-check of p95s", "p95s",
     "bulk:external/unosat/3614/FL20230606UKR_SHP.zip", "UNITAR / UNOSAT (ICEYE, Landsat-9, Sentinel-1/2/3 derived vectors)", "https://unosat.org/static/unosat_filesystem/3614/FL20230606UKR_SHP.zip", "archive of 2023-06-26",
     "CC BY-SA (UNOSAT products on HDX); cite UNITAR-UNOSAT", "YES (public)", "sha256 b2f65fd1edd8f7f18b044aa19b60842ee225f11bc9016a86a85857bceb33d570; downloaded 2026-09-30"),
    ("osm_kozachi_krynky_2023", "OpenStreetMap residential areas of Kozachi Laheri and Krynky, Michurina street, settlements: the state of 5 June 2023 (Overpass reply + OSM API history)", "p95r p95s",
     "bulk:context/osm_kozachi_krynky_state_2023-06-05.json", "OpenStreetMap contributors (Overpass API, OSM API 0.6 history)", "https://overpass-api.de/api/interpreter", "state of 2023-06-05",
     "ODbL 1.0, (c) OpenStreetMap contributors", "YES (public)", "56 elements existed on 2023-06-05 with the same node lists; 4 of 669 nodes restored to their 2023 positions"),
]
for f in ("B1", "B2"):
    E += [(f"composite_preall_{f}", "S2 PRE/EVENT/TRACE index composites (M2 features, RF20 predictors)", "p65a p67b p73", f"bulk:frames10/{f}/composite_preall.tif", "Sentinel-2 L2A (manifests/s2_scenes.csv) -> p54a/p54b", CDSE, "L2A", "Copernicus Sentinel data (free, open)", "YES (derived)", ""),
          (f"composite_preseas_{f}", "S2 PRE seasonal composites (RF20 predictors)", "p73", f"bulk:frames10/{f}/composite_preseas.tif", "Sentinel-2 L2A -> p54b", CDSE, "L2A", "Copernicus Sentinel data (free, open)", "YES (derived)", ""),
          (f"s1_change_{f}", "S1 event-change channels (U-Net inputs)", "p86", f"bulk:frames10/{f}/s1_change.tif", "Sentinel-1 -> p71", CDSE, "2023 scenes", "Copernicus Sentinel data (free, open)", "YES (derived)", ""),
          (f"p60_labels_{f}", "p60 weak labels (M2 training, v002/v004 ingredients)", "p65a p77 p77d", f"bulk:frames10/{f}/labels.tif", "p60 (S1 peak dates + pre-breach state)", "", "", "derived", "YES", ""),
          (f"labels_v004_{f}", "canonical weak labels (FROZEN)", "p86 p87 p90 p92", f"bulk:frames10/{f}/m6_labels_v004.tif", "p77d --m2-tag _notrace", "", "v004", "derived", "YES", "sha256 also in tables/m6_labels_v004_FROZEN.json"),
          (f"split_role_{f}", "frozen spatial-block split", "p86 p87 p90", f"bulk:frames10/{f}/m6_split_v1_role.tif", "p84", "", "m6_split_v1", "derived", "YES", ""),
          (f"rf20_rev2_{f}", "RF20 rev 2 classes (U1 input, strata; FROZEN)", "p86 p95d p87", f"bulk:frames10/{f}/p73_rf20_rev2/surface_class_20m.tif", "p73 --rev 2", "", "rev 2", "derived (WorldCover-trained)", "YES", "")]
E += [("m2_features", "p65a feature memmap (M2 nested CV and production fit)", "p65b p67b", "bulk:frames10/_ml/X_preall.i2", "p65a", "", "", "derived", "YES", "84 features; manifest tables/p65a_feature_manifest.csv (sha256 35f43a21...)"),
      ("m2_index", "p65a sample index (labels, blocks)", "p65b p67b", "bulk:frames10/_ml/index.parquet", "p65a", "", "", "derived", "YES", "")]


def sha(p, buf=1 << 24):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while (b := f.read(buf)):
            h.update(b)
    return h.hexdigest()


def locate(loc):
    base, rel = loc.split(":", 1)
    return BASES[base], rel


def measure(loc, max_bytes):
    base, rel = locate(loc)
    if any(c in rel for c in "*?["):
        files = sorted(Path(p) for p in glob.glob(str(base / rel)))
    elif (base / rel).is_dir():
        files = sorted(p for p in (base / rel).rglob("*") if p.is_file())
    elif (base / rel).is_file():
        files = [base / rel]
    else:
        return dict(exists=False, n_files=0, size_bytes=0, sha256="MISSING")
    size = sum(p.stat().st_size for p in files)
    if size > max_bytes:
        return dict(exists=True, n_files=len(files), size_bytes=size, sha256=f"TBD (not hashed: {size / 1e9:.1f} GB > limit)")
    if len(files) == 1 and not any(c in rel for c in "*?[") and not (base / rel).is_dir():
        return dict(exists=True, n_files=1, size_bytes=size, sha256=sha(files[0]))
    lines = "".join(f"{p.relative_to(base).as_posix()} {sha(p)}\n" for p in files)
    return dict(exists=True, n_files=len(files), size_bytes=size, sha256="digest:" + hashlib.sha256(lines.encode()).hexdigest())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--max-gb", type=float, default=60.0); a = ap.parse_args()
    t0 = time.time(); rows = []
    for (i, role, used, loc, src, url, ver, lic, redis, note) in E:
        m = measure(loc, a.max_gb * 1e9)
        rows.append(dict(input_id=i, role=role, used_by=used, location=loc, source=src, url=url or "", version=ver or "", licence=lic, redistributable=redis,
                         **m, notes=note))
        print(f"{i:28s} {m['n_files']:5d} files {m['size_bytes'] / 1e6:10.1f} MB  {m['sha256'][:24]}  ({time.time() - t0:.0f} s)", flush=True)
    D = pd.DataFrame(rows)
    head = ("# Load-bearing inputs of the paper's results (review F16). Generated by workflows/paper/data_manifest.py on "
            f"{time.strftime('%Y-%m-%d')}; sha256 of a file, or digest: = sha256 of the sorted 'relpath sha256' lines of a directory / glob. "
            "Locations: repo / bulk ($FLOODSTATE_DATA_ROOT) / swot (SWOT-DNIPRO) / icesat (hydrology sibling). TBD = not recorded, never invented.\n")
    out = CS / "manifests" / "load_bearing_inputs.csv"
    out.write_text(head + D.to_csv(index=False)); print(f"-> {out.relative_to(REPO)} ({len(D)} inputs, {int((~D.exists).sum())} missing, {time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
