# New in floodstate-eo, 2026-10-02 (maintainer: "where are the index maps and their classified indices; the list of available maps
# and the list of available water masks"). STATUS: ACTIVE. Reads names only (and the key lists of .npz archives); changes nothing.
"""P104 -- inventory of the map products: index maps, classified maps, water masks, flood / reconstruction maps, dashboard layers
and map figures -- where each family lives, its producer, grid, content, and how many dates per year it holds.

Generated, never hand-edited (the full-picture rule of 2026-10-01): rerun after any product changes. Paths are given relative to
their base: BULK = the bulk data root (FLOODSTATE_DATA_ROOT, here /mnt/f/data_kakhovka_dem_swot), REPO = this repository,
SIB = the SWOT-DNIPRO sibling repository.

Outputs: <case_study>/PRODUCT_INVENTORY.md, <case_study>/tables/p104_product_inventory.csv.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
from floodstate_eo import _kakhovka_legacy_config as CFG

CS = Path(__file__).resolve().parents[2]; REPO = CS.parents[1]
BASES = {"BULK": CFG.BULK_ROOT, "REPO": REPO, "SIB": Path(CFG._SWOT_DNIPRO_SIBLING)}
YEARS = list(range(2017, 2027))
DATE = re.compile(r"(20\d{2})-?(\d{2})-?(\d{2})")
KINDS = {"index": "1. Index maps (continuous values)", "class": "2. Classified maps (classified indices, surface and land-cover classes)",
         "water_s2": "3a. Water masks -- Sentinel-2", "water_s1": "3b. Water masks -- Sentinel-1 (and the radar backscatter they come from)",
         "flood": "3c. Reconstruction, flood and state maps (terrain_reconstructed, Monte-Carlo, labels)", "external": "3d. External products"}

# kind, family id, base, glob, unit rule, dates rule, producer, grid, content
FAMILIES = [
    ("index", "zone_indices", "BULK", "zone_spectral/*/*_indices.tif", "parent", "name",
     "SWOT-DNIPRO p25 (frozen) + p25x extension of 2026-10-02", "20 m zone grid, EPSG:32636",
     "7 indices int16 x10000 (NDVI, NDWI, MNDWI, NDMI, BSI, AWEIsh, NDTI; nodata -32768), one file per date"),
    ("index", "frame_indices", "BULK", "frames10/*/indices/20??-??-??.tif", "frame", "name",
     "floodstate-eo p54a (src/floodstate_eo/optical/p54a_frame_index_stacks_10m.py)", "10 m canonical frames B1-B3",
     "the same 7 indices int16 x10000, with <date>_valid.tif (cloud-free cells)"),
    ("index", "frame_composites", "BULK", "frames10/*/composite_pre*.tif", "frame", None,
     "floodstate-eo p54b", "10 m canonical frames", "window composites: median / min / max of the 7 indices for PRE (and PRE-seasonal), n_obs, pre_water_frac"),
    ("index", "zone_regime_medians", "SIB", "outputs/rasters/zone?/zone?_*_*_median_20m.tif", "zonefile", None,
     "SWOT-DNIPRO p25 composites (frozen; p25x does not rebuild them)", "20 m zone grid",
     "median of each index per regime PRE_BREACH / BREACH_DRAWDOWN / POST_BREACH"),
    ("index", "tile_stacks_legacy", "BULK", "spectral_indices/*_stack.tif", "tile", "name",
     "SWOT-DNIPRO k10e stacks (legacy)", "MGRS tile grids (eastern tiles)", "per-scene index stacks of the reservoir side"),
    ("class", "k10e_by_date", "BULK", "zone_spectral/*/*_class.tif", "parent", "name",
     "SWOT-DNIPRO p25 (sentinel_preprocess.classify) + p25x", "20 m zone grid",
     "k10e surface classes from the indices of the date: 1 open water, 2 shallow/mixed water, 3 wet sediment, 4 dry bare sediment, 5 sparse herbaceous, "
     "6 dense herbaceous, 7 reed / flooded vegetation, 8 built, 9 ambiguous; 0 = not observed (thresholds NDVI 0.15/0.3, NDMI 0.1, BSI 0.1)"),
    ("class", "k10e_regime_mode", "SIB", "outputs/rasters/zone?/zone?_class_*_mode_20m.tif", "zonefile", None,
     "SWOT-DNIPRO p25 composites (frozen)", "20 m zone grid", "most frequent k10e class per regime"),
    ("class", "index_display_classes_reservoir", "REPO", "apps/dashboard/data/reservoir/s2/*_[A-Z]*.png", "none", "name",
     "p98 from p95h (classify_index)", "PNG overlay, EPSG:4326", "each of the 7 indices in display classes (e.g. NDVI <0.15 / 0.15-0.3 / 0.3-0.5 / >0.5) and k10e, the pool + 1 km"),
    ("class", "index_display_classes_figures", "REPO", "case_studies/kakhovka_2023/figures/m6_v003A/p95zm_*.png", "none", None,
     "p95zm", "figures", "cloud-free period composites of every index in display classes, k10e and S1 VV: delta and floodway, before / after"),
    ("class", "rf_by_date", "BULK", "rf_by_date/*/*_rf.tif", "parent", "name",
     "floodstate-eo p102 (random forest on the indices of the date)", "20 m zone grid",
     "land-cover class 1 water, 2 cropland, 3 grass, 4 forest, 5 shrub, 6 wetland/reed, 7 built, 8 bare/sand, 9 other, 10 uncertain; <date>_rfp.tif = top-class probability"),
    ("class", "rf20_pre_event", "BULK", "frames10/*/p73_rf20*/surface_class_20m.tif", "frame", None,
     "floodstate-eo p73 (rev 2 for B1, B2; rev 1 inference for B3)", "20 m frame grid", "RF20 land-cover classes from PRE-event composites (+ max score, uncertain, per-class scores)"),
    ("class", "worldcover", "BULK", "worldcover_frames/*/wc_*_20m.tif", "parent", "name", "ESA WorldCover (fetched in SWOT-DNIPRO)", "20 m zone grid", "WorldCover 2020 and 2021 classes"),
    ("class", "dynamic_world_annual", "BULK", "dynamic_world_annual/dw_*.tif", "dwzone", "name", "Google Dynamic World (annual, fetched in SWOT-DNIPRO)", "EPSG:4326, ~30 m", "annual class probabilities (11 bands)"),
    ("class", "dynamic_world_frames", "BULK", "dynamic_world_frames/*/dw_*_20m_from_annual.tif", "parent", "name", "SWOT-DNIPRO", "20 m zone grid", "Dynamic World annual mode on the zone grid"),
    ("class", "ground_class", "BULK", "floodplain_dyn/_weak_labels/ground_class.tif", "none", None, "floodstate-eo p95x", "20 m union grid",
     "pre-event ground classes: dry before the event / vegetated wetland / open reference water / other"),
    ("water_s2", "zone_water3", "BULK", "zone_spectral/*/*_water3.tif", "parent", "name",
     "SWOT-DNIPRO p25 + p25x (frozen rule)", "20 m zone grid", "0 land, 1 water, 255 not observed; water = NDWI > 0 AND MNDWI > 0 AND SCL permits water"),
    ("water_s2", "zone_scl", "BULK", "zone_spectral/*/*_scl.tif", "parent", "name", "SWOT-DNIPRO p25 + p25x", "20 m zone grid", "ESA Scene Classification of the date (cloud, shadow, water, ...)"),
    ("water_s2", "frame_water_layers", "REPO", "apps/dashboard/data/s2/*_water.png", "none", "name",
     "p98 (watermask rule on the p54a 10 m stacks, as p94)", "PNG overlay", "new S2 water / water on pre-breach water per date (the GeoTIFF is not stored: the rule is applied on the fly)"),
    ("water_s2", "zone1_crosscheck", "BULK", "ZONE_1_s2_crosscheck/*.npz", "none", "name", "SWOT-DNIPRO p15 (frozen)", "20 m ZONE_1 grid (cell centres)", "water + valid, reservoir crosscheck dates"),
    ("water_s2", "prebreach_water_frequency", "SIB", "outputs/rasters/zone?/zone?_water_frac_*_20m.tif", "zonefile", None,
     "SWOT-DNIPRO p25 composites (frozen; p60 reads the PRE_BREACH ones)", "20 m zone grid", "percent of observed dates with water, per regime"),
    ("water_s2", "water_occurrence_2022", "BULK", "lower_dnipro_water_occurrence/*.tif", "none", "name", "SWOT-DNIPRO", "EPSG:4326, ~30 m", "water occurrence 2022"),
    ("water_s1", "s1_event_masks", "BULK", "s1_zone_cache/*/per_scene_water.npz", "parent", "npzkeys",
     "SWOT-DNIPRO p0v/p0w M3 masks", "20 m zone grids", "per-scene dark-water mask + valid footprint (event caches June 2023; _pre2023 = April-June 2023)"),
    ("water_s1", "s1_mask_variants", "BULK", "s1_variants/*/*.npz", "parent", "name",
     "SWOT-DNIPRO (S1 water-rule variants)", "20 m zone grids", "per scene: V0, Vz*, Vf*, VL, VM, VS*, VT, VC* water-mask variants + valid"),
    ("water_s1", "s1_reservoir_vh", "BULK", "reservoir_maps/s1/*.npz", "none", "name", "floodstate-eo p95h", "20 m reservoir grid",
     "VH dark surface (open water or smooth wet mud; per-date Otsu) + observed"),
    ("water_s1", "s1_backscatter", "BULK", "s1_zone_cache/*/20??-??-??_orb*.npz", "parent", "name", "SWOT-DNIPRO S1 zone cache", "20 m zone grids",
     "calibrated VV / VH backscatter + coverage per scene (not a mask; the masks above are made from it)"),
    ("flood", "terrain_daily_new", "BULK", "floodplain_dyn/*_connected_ceiling/daily_new.npz", "dynzone", "npzkeys",
     "floodstate-eo p95 (primary run)", "20 m zone grids", "daily new inundation 26 May - 10 July 2023 (bit-packed) + baseline (normal regime) + normally_wet"),
    ("flood", "terrain_cellprob", "BULK", "floodplain_dyn/*_connected_ceiling/p95e_cellprob*.tif", "dynzone", "name", "floodstate-eo p95e (1000 coherent worlds)", "20 m zone grids",
     "count of worlds with new inundation (P = count / 1000)"),
    ("flood", "terrain_summaries", "BULK", "floodplain_dyn/*_connected_ceiling/[dfml]*_*.tif", "dynzone", None, "floodstate-eo p95", "20 m zone grids",
     "duration_days, first_day, last_day, max_depth_m, depth_2023-06-08_m of the nominal run"),
    ("flood", "flood_envelope", "BULK", "floodplain_dyn/_envelope/*", "none", None, "floodstate-eo p103", "20 m mosaic + GeoJSON (EPSG:4326)",
     "the full flood mask: envelope classes, max P, Sentinel-1 envelope; polygons of the total and of the new-inundation envelope"),
    ("flood", "state_masks", "BULK", "floodplain_dyn/_weak_labels/state_*.tif", "none", "name", "floodstate-eo p95x", "20 m union grid",
     "WATER / DRY / UNKNOWN + source + flags per day"),
    ("flood", "reservoir_model", "BULK", "reservoir_maps/model/wet_daily.npz", "none", "npzkeys", "floodstate-eo p95h / p95f", "50 m pool grid",
     "modelled pool water per day 26 May - 13 June 2023 (+ depth_<date>.tif, exposed_day.tif, exposed_day_observed.tif)"),
    ("flood", "weak_labels", "BULK", "frames10/*/m6_labels_*.tif", "frame", None, "floodstate-eo p77 / p77d", "10 m frames",
     "LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN (canonical: m6_labels_v004; the others are provenance)"),
    ("flood", "unet_scores", "BULK", "frames10/*/m6/*_score.tif", "frame", None, "floodstate-eo p86 / p88", "10 m frames", "U-Net arm scores (thresholds in the tables)"),
    ("external", "unosat_3614", "BULK", "external/unosat/3614/**/*.*", "none", None, "UNITAR-UNOSAT activation package FL20230606UKR", "shapefile / GeoJSON",
     "operational flood extents (ICEYE, Sentinel), literature_reported: context, never validation"),
]


def unit_of(rule, p: Path, base: Path):
    rel = p.relative_to(base).parts
    if rule == "parent":
        return p.parent.name
    if rule == "frame":
        return rel[1] if len(rel) > 1 else "?"
    if rule == "zonefile":
        return p.name.split("_")[0]
    if rule == "dynzone":
        return p.parent.name.replace("_connected_ceiling", "")
    if rule == "dwzone":
        m = re.match(r"dw_(zone_\d)", p.name)
        return m.group(1) if m else "?"
    if rule == "tile":
        m = re.search(r"_(T\d{2}[A-Z]{3})_", p.name)
        return m.group(1) if m else "?"
    return "all"


def dates_of(rule, p: Path):
    if rule == "name":
        m = DATE.search(p.name)
        return [f"{m.group(1)}-{m.group(2)}-{m.group(3)}"] if m else []
    if rule == "npzkeys":
        try:
            keys = np.load(p, allow_pickle=True).files
        except Exception:
            return []
        return sorted({k[:10] for k in keys if re.match(r"20\d{2}-\d{2}-\d{2}", k)})
    return []


def scan():
    rows = []
    for kind, fam, base, pat, urule, drule, prod, grid, content in FAMILIES:
        b = BASES[base]; files = sorted(f for f in b.glob(pat) if f.is_file() and not f.name.endswith("_valid.tif") and not f.name.endswith(".aux.xml"))
        if fam == "s1_backscatter":
            files = [f for f in files if f.name != "per_scene_water.npz"]
        by_unit = {}
        for f in files:
            by_unit.setdefault(unit_of(urule, f, b), []).append(f)
        if not by_unit:
            rows.append(dict(kind=kind, family=fam, unit="-", n_files=0, n_dates=0, first="", last="", where=f"{base}/{pat}", producer=prod, grid=grid, content=content,
                             **{f"y{y}": 0 for y in YEARS}))
        for u, fs in sorted(by_unit.items()):
            ds = sorted({d for f in fs for d in dates_of(drule, f)}) if drule else []
            r = dict(kind=kind, family=fam, unit=u, n_files=len(fs), n_dates=len(ds), first=ds[0] if ds else "", last=ds[-1] if ds else "",
                     where=f"{base}/{pat}", producer=prod, grid=grid, content=content, **{f"y{y}": sum(d.startswith(str(y)) for d in ds) for y in YEARS})
            if not drule:
                r["examples"] = ", ".join(sorted({re.sub(r"(20\d{2})-(\d{2})-(\d{2})", "<date>", f.name) for f in fs})[:6])
            rows.append(r)
    return pd.DataFrame(rows)


def dashboard_groups():
    m = json.loads((REPO / "apps" / "dashboard" / "data" / "manifest.json").read_text()); out = []
    for g, ls in pd.DataFrame(m["layers"]).groupby("group"):
        ds = sorted({d for i in ls.id for d in [x.group(0) for x in re.finditer(r"20\d{2}-\d{2}-\d{2}", i)]})
        out.append(dict(group=g, n_layers=len(ls), first=ds[0] if ds else "", last=ds[-1] if ds else "", n_dates=len(ds), example=ls.id.iloc[0], MB=round(ls.bytes.sum() / 1e6, 1)))
    return pd.DataFrame(out), m


def figures():
    out = []
    caps = (CS / "publication" / "captions.md").read_text(encoding="utf-8") if (CS / "publication" / "captions.md").exists() else ""
    for f in sorted((CS / "publication" / "figures").glob("Fig*.png")):
        fid = f.name.split("_")[0]; m = re.search(r"\*\*" + re.escape(fid) + r"\*\*\.?\s*([^\n]{0,150})", caps)
        out.append(dict(where="publication/figures", file=f.name, about=(m.group(1).strip() if m else "")))
    for d in ("figures/m6_v003A", "figures/p102", "figures"):
        for f in sorted((CS / d).glob("*.png")):
            if re.match(r"(p95zm|p95z_|p102|p103|ZONE_)", f.name) or d == "figures/p102":
                out.append(dict(where=d, file=f.name, about=""))
    return pd.DataFrame(out).drop_duplicates("file")


def md_table(df, cols):
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in df[cols].itertuples(index=False):
        lines.append("| " + " | ".join(str(v).replace("|", "\\|") for v in r) + " |")
    return "\n".join(lines)


def main():
    t0 = time.time(); T = scan(); T.to_csv(CFG.TABLES / "p104_product_inventory.csv", index=False)
    G, man = dashboard_groups(); F = figures()
    yc = [f"y{y}" for y in YEARS]
    md = ["# Map products of the Kakhovka case study — where they are", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `workflows/paper/p104_product_inventory.py` from the files on disk; do not edit by hand. "
          "Bases: **BULK** = the bulk data root (`FLOODSTATE_DATA_ROOT`, here `" + str(CFG.BULK_ROOT) + "`), **REPO** = this repository, "
          "**SIB** = the SWOT-DNIPRO sibling repository. One row per family and zone / frame; `y2017…y2026` = dates per year. "
          "Machine-readable: `tables/p104_product_inventory.csv`.", ""]
    for kind, title in KINDS.items():
        K = T[T.kind == kind]
        if K.empty:
            continue
        md += [f"## {title}", ""]
        for fam, g in K.groupby("family", sort=False):
            r0 = g.iloc[0]
            md += [f"### `{fam}` — {r0.content}", f"*Where:* `{r0['where']}` · *producer:* {r0.producer} · *grid:* {r0.grid}", ""]
            if g.n_dates.sum() > 0:
                md += [md_table(g.rename(columns={c: c[1:] for c in yc}), ["unit", "n_files", "n_dates", "first", "last"] + [c[1:] for c in yc]), ""]
            else:
                md += [md_table(g.assign(examples=g.get("examples", "")).fillna(""), ["unit", "n_files", "examples"]), ""]
    md += ["## 4. Maps in the dashboard (pre-rendered PNG overlays, `apps/dashboard/data/`)", "",
           f"{man['n_layers']} layers, {man['total_bytes'] / 1e6:.1f} MB. Maps page: terrain, Monte-Carlo probability, support, envelope, S1 / S2 masks, U-Net, "
           "labels, RF20, RF by date, reservoir; Surface-context page: Sentinel-2 true colour of every archive date, RF20, RF by date, the p95zm maps.", "",
           md_table(G, ["group", "n_layers", "n_dates", "first", "last", "MB", "example"]), "",
           "## 5. Map figures", "", md_table(F, ["where", "file", "about"]), "",
           "## 6. What does not exist (gaps)", "",
           "- **Classified-index GeoTIFFs per date**: the display classes of the indices exist as dashboard PNGs (the pool, 5 dates) and as the p95zm "
           "period figures (delta, floodway); per-date classified rasters are only the k10e class (`k10e_by_date`). Any index file can be classed with "
           "`p95h.classify_index` (bins in `p95h.INDEX_BINS`) on request.",
           "- **Sentinel-2 water masks of the 10 m frames** are not stored as rasters: the frozen rule (NDWI > 0 AND MNDWI > 0 on valid cells) is applied "
           "to `frame_indices` on the fly (p94, p98); the 20 m zone masks (`zone_water3`) are stored for every zone-date.",
           "- **2023-07-31 and 2024-05-25** have no zone stack: their downloaded zips are orbit-edge slivers (78; 47 and 64 MB) below p25's frozen 200 MB scene filter.",
           "- The **p25x extension** (49 zone-dates, 17 dates of 15 June – 30 July 2023, `tables/p25x_zone_stack_extension.csv`) is stacked for the hydraulic-model "
           "products; the Paper 3 tables built on the zone stacks (p95h: T23–T25) exclude them on purpose.", ""]
    out = CS / "PRODUCT_INVENTORY.md"; out.write_text("\n".join(md), encoding="utf-8")
    print(f"-> {out} and tables/p104_product_inventory.csv: {len(T)} rows, {T.family.nunique()} families, {len(G)} dashboard groups, {len(F)} figures ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
