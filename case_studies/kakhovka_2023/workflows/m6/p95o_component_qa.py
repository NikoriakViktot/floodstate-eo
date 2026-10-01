# New in floodstate-eo, 2026-09-30 (maintainer QA of the weak-support blobs; decision D-SEED). STATUS: ACTIVE.
"""P95o -- component QA of the daily terrain-connectivity reconstruction: which seed does every newly inundated component
hang on, and since when.

Background (2026-09-30). Under `seed_network=all_prewater` the connected_ceiling rule kept every component of `dem < H_t`
that touched ANY cell of the pre-breach water map -- ponds and canals included. A ~40 km2 component of WorldCover cropland
on the left-bank sandy terrace (33.25 E 46.64 N, terrain 9-11 m) was "flooded" by the Kokan' level 14 km away through a
handful of pond cells, with no terrain path to the river network on any day. Maintainer decision D-SEED_PRIMARY: the event
source is the connected river network (largest component of the pre-breach water map); this script documents the three
semantic classes of the old rule and verifies the new one.

Per day t of the nominal world (engine and layers exactly as p95 builds them; reproduction gate against daily_new.npz):
    pot_t components classed by their seed content (terrain.connectivity.seed_classes):
        river_connected  -- the component touches the event-source network (largest pre-breach water component)
        isolated         -- it touches other pre-breach water only (a pond, a canal)
    new-water components (8-connected, >= --min-km2) with a DAY-TO-DAY LINEAGE (overlap graph, ancestry by backward
    traversal; never the union of all days, which merges areas that were never simultaneously connected):
        RIVER_CONNECTED   river-connected today
        TRAPPED           not river-connected today, but this component or an ancestor was on an earlier day
        ISOLATED_NEVER    never river-connected along its lineage
    A_full = A_river_connected + A_trapped + A_isolated_never (asserted per day and region).
    Per component: area, centroid, region, WorldCover mix of its own cells and of a 2 km context ring (land cover is not
    geomorphology: cropland or pine on the sandy terrace stays 'cropland'/'trees'), terrain / water-surface / freeboard,
    support class shares (p95l), nearest SWOT node (river, km), seed bodies inside its pot component, the 4-connectivity
    outcome, the erosion-disconnect sensitivity (terrain.connectivity.erosion_disconnect_px -- a morphological test, not a
    width) and the Sentinel-1 evidence with its date and lag. S1 classes (maintainer, 2026-09-30): S1_WATER (dark water on
    >= 20 % of the observed cells); S1_OPEN_SURFACE_NO_WATER (the component is at least 30 % open ground -- grass, cropland,
    bare --, at least half of that open ground was observed and <= 5 % of it is dark: no water signal where SAR sees water);
    S1_NO_WATER_SIGNAL_VEGETATED (no dark water, but forest / reed / built-up dominate: SAR is not informative there);
    S1_INCONCLUSIVE; S1_UNOBSERVED. A later scene never contradicts an earlier day: its classes carry the prefix LATER_.
    Decision tree of the retained water (TRAPPED components, same-day scene only): S1_WATER -> RETAINED_PLAUSIBLE;
    S1_OPEN_SURFACE_NO_WATER -> LIKELY_DRAINED; otherwise RETAINED_UNCERTAIN.

Modes: default = one run (--sfx); --compare SFX2 = retained water of a memory variant (new_SFX2 minus new_SFX per day) with
its same-day Sentinel-1 verdict per cell (water / open surface without water / uncertain; written to
$BULK/floodplain_dyn/<ZONE><SFX2>/retained_class.npz for FigS16; no engine needed).

Outputs: <case_study>/tables/p95o_components<sfx>.csv, p95o_lineages<sfx>.csv, p95o_summary<sfx>.csv, p95o_landcover<sfx>.csv,
         p95o_seed_components<sfx>.csv, p95o_manifest<sfx>.json; $BULK/floodplain_dyn/<ZONE><sfx>/daily_component_class.npz
         (per day and class one bit-packed mask, keys <date>_c1 river-connected / _c2 trapped / _c3 isolated-never, as daily_new.npz);
         <case_study>/figures/m6_v003A/p95o_isolated_components<sfx>.png;  --compare: p95o_retained_<A>_vs_<B>.csv
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import transform as tf_transform
from scipy import ndimage

from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.terrain.connectivity import STRUCTURE, largest_component, link_components, seed_classes

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = ROOT / "figures" / "m6_v003A"
WC_NAMES = {10: "trees", 20: "shrub", 30: "grass", 40: "cropland", 50: "built", 60: "bare_sparse", 70: "snow", 80: "water", 90: "wetland", 95: "mangrove", 100: "moss"}
CLASS_CODE = {"RIVER_CONNECTED": 1, "TRAPPED": 2, "ISOLATED_NEVER": 3}
S1_VALID_MIN, S1_DARK_HI, S1_DARK_LO = 0.2, 0.2, 0.05
OPEN_WC = (30, 40, 60)                                                          # grass, cropland, bare / sparse: where C-band SAR sees water
OPEN_SHARE_MIN, OPEN_OBS_MIN = 0.3, 0.5
WEAK_SHARE = 0.8
RETAINED_CODE = {"RETAINED_PLAUSIBLE": 1, "LIKELY_DRAINED": 2, "RETAINED_UNCERTAIN": 3}
COL = dict(network="#3b4a5c", river="#2a78d6", trapped="#8e6bbf", isolated="#e34948", plausible="#2a78d6", drained="#e34948", uncertain="#9aa5b1")


def _ld(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def load_manifest(sfx):
    p = CFG.TABLES / f"p95_manifest{sfx}.json"
    if not p.exists():
        raise SystemExit(f"no p95 manifest for suffix '{sfx}': {p}")
    return json.loads(p.read_text())


def engine_for(P95, man, sfx):
    """The water-surface engine of a run, from its manifest and suffix (the flags p95 main() would have used)."""
    c = man["constants"]; lf = man.get("legacy_flags", {})
    if lf.get("evaluation", "mosaic") != "mosaic" or lf.get("coarse_anchor", "map") != "map" or lf.get("terrain_table", "fabdem_zone") != "fabdem_zone":
        raise SystemExit("p95o supports the mosaic evaluation on the map-anchored lattice only")
    fb = None
    if "_fallback" in sfx:
        fb = float(sfx.split("_fallback")[1].split("km")[0]) * 1000.0
    extra = P95.inhulets_gauge_node() if "_inhulets_gauge_node" in sfx else None
    W, dxm, _, nodes = P95.load_engine(man.get("closure", "kherson_paper1"), c.get("max_gap_days"), bool(c.get("wse_river_aware")), "map", extra, fb)
    return W, dxm, nodes


def compose_npz(M, sfx, key, dtype=bool):
    """One packed layer of daily_new.npz (or daily_component_class.npz) of every zone, composed on the union grid."""
    arrs = {}
    for z in M["names"]:
        f = CFG.BULK_ROOT / "floodplain_dyn" / f"{z}{sfx}" / "daily_new.npz"
        zz = np.load(f); shp = tuple(int(v) for v in zz["shape"])
        if key not in zz.files:
            return None
        arrs[z] = np.unpackbits(zz[key], count=shp[0] * shp[1]).reshape(shp).astype(dtype)
    return M["grid"].compose(arrs, False, order=M["names"], dtype=dtype)


def compose_tif(M, sfx, name, fill=0, dtype="u1"):
    arrs = {}
    for z in M["names"]:
        p = CFG.BULK_ROOT / "floodplain_dyn" / f"{z}{sfx}" / name
        if not p.exists():
            p = CFG.BULK_ROOT / "floodplain_dyn" / f"{z}_connected_ceiling" / name          # static per cell: the primary's raster serves every seed variant
        with rasterio.open(p) as s:
            arrs[z] = s.read(1).astype(dtype)
    return M["grid"].compose(arrs, fill, order=M["names"], dtype=dtype)


def s1_layers(M, date):
    """(valid, dark water) of the Sentinel-1 scene(s) of `date` on the union grid, or None."""
    if not any(date in L["W"] for L in M["zones"].values()):
        return None
    V = M["grid"].compose({z: L["V"].get(date, np.zeros((L["G"]["ny"], L["G"]["nx"]), bool)) for z, L in M["zones"].items()}, False, order=M["names"], dtype=bool)
    Wd = M["grid"].compose({z: L["W"].get(date, np.zeros((L["G"]["ny"], L["G"]["nx"]), bool)) for z, L in M["zones"].items()}, False, order=M["names"], dtype=bool)
    return V, Wd & ~(M["pre"] | M["s1_pre_dark"])                         # S1 new water: not where S1 was already dark (p95 rev 9)


def s1_match(day, s1_dates):
    """The Sentinel-1 date used for a day: the same day if a scene exists, else the next scene (lag > 0)."""
    later = [d for d in s1_dates if d >= day]
    return (later[0], (pd.Timestamp(later[0]) - pd.Timestamp(day)).days) if later else (None, None)


def s1_flags(lag, valid_share, dark_share, open_share=0.0, open_obs=0.0, open_dark=np.nan):
    """Sentinel-1 class of a component (see the module docstring); LATER_ prefix when the scene is not of the same day."""
    if lag is None or not np.isfinite(valid_share) or valid_share < S1_VALID_MIN:
        return "S1_UNOBSERVED"
    pre = "" if lag == 0 else "LATER_"
    if dark_share >= S1_DARK_HI:
        return pre + "S1_WATER"
    if open_share >= OPEN_SHARE_MIN and open_obs >= OPEN_OBS_MIN and np.isfinite(open_dark) and open_dark <= S1_DARK_LO:
        return pre + "S1_OPEN_SURFACE_NO_WATER"
    if valid_share >= 0.5 and dark_share <= S1_DARK_LO:
        return pre + "S1_NO_WATER_SIGNAL_VEGETATED"
    return pre + "S1_INCONCLUSIVE"


def retained_verdict(cls, flag):
    """The retained-water decision tree for TRAPPED components: same-day evidence only."""
    if cls != "TRAPPED":
        return ""
    return {"S1_WATER": "RETAINED_PLAUSIBLE", "S1_OPEN_SURFACE_NO_WATER": "LIKELY_DRAINED"}.get(flag, "RETAINED_UNCERTAIN")


def region_of(masks, cells):
    best, share = "OUTSIDE", 0.0
    for nm, m in masks.items():
        s = float(m[cells].mean())
        if s > share:
            best, share = nm, s
    return best, round(share, 3)


def wc_mix(wc, sel):
    u, c = np.unique(wc[sel], return_counts=True); n = max(int(c.sum()), 1)
    return {WC_NAMES.get(int(k), str(int(k))): round(float(v) / n, 4) for k, v in zip(u, c)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sfx", default="_connected_ceiling", help="suffix of the p95 run to audit (its manifest, tables and rasters)")
    ap.add_argument("--compare", default=None, help="suffix of a second run: retained water = new(second) minus new(--sfx) per day, with its S1 support")
    ap.add_argument("--min-km2", type=float, default=0.25, help="components smaller than this are aggregated as 'specks' (still classed in the rasters and sums)")
    ap.add_argument("--buffer-km", type=float, default=2.0, help="context ring around a component for the land-cover / terrain context")
    ap.add_argument("--max-erosion-px", type=int, default=3)
    ap.add_argument("--no-figure", action="store_true"); ap.add_argument("--limit-days", type=int, default=None, help="smoke test: only the first N days (partial outputs)")
    ap.add_argument("--start", default=None, help="smoke test: first day to process (lineage starts there)")
    a = ap.parse_args(); t0 = time.time(); sfx = a.sfx
    P95 = _ld("p95_hand_daily_inundation"); P = P95.load_p92()
    man = load_manifest(sfx); c = man["constants"]; conn = int(c.get("connectivity", 8)); margin = float(c.get("margin_m", 0.0))
    seed_network = c.get("seed_network", "all_prewater")
    if man.get("rule_variant", "connected_ceiling") != "connected_ceiling":
        raise SystemExit("p95o audits the connected_ceiling rule only")
    M = P95.mosaic_layers(P, with_s1=True); g = M["grid"]; names = M["names"]
    print("mosaic", M["G"]["ny"], "x", M["G"]["nx"], round(time.time() - t0), "s", flush=True)
    xs, ys = M["xs"], M["ys"]; R = M["regions"]; own = M["own_id"] > 0
    zone_of = M["own_id"]; zone_name = {v: k for k, v in M["zone_id"].items()}
    seed_all = M["seed"]; seed_river = largest_component(seed_all, conn)
    if a.compare:
        return compare_runs(M, sfx, a.compare, R, own)
    W, dxm, _ = engine_for(P95, man, sfx)
    M["base"] = M["base_geom"] & P95.dam_mask(M, dxm)
    seed = seed_river if seed_network == "main_stem" else seed_all
    Z = W.prepare(M); up = lambda v: np.asarray(v).reshape(Z["shape_c"])[np.ix_(Z["ri"], Z["ci"])]
    node_river = np.array(W.river); rnames, rcodes = np.unique(node_river, return_inverse=True)
    riv_grid = rcodes[up(Z["i1"])].astype("i2"); dkm_grid = (up(Z["d1"]) / 1e3).astype("f4")
    baseline = compose_npz(M, sfx, "baseline")
    if baseline is None:
        raise SystemExit("daily_new.npz without a baseline layer")
    wc = g.compose({z: L["wc"] for z, L in M["zones"].items()}, 0, order=names, dtype="u1")
    sc = compose_tif(M, sfx, "support_class.tif")
    ref = pd.read_csv(CFG.TABLES / f"p95_daily_area{sfx}.csv").set_index(["zone", "date", "region"]).new_km2
    s1_dates = sorted({d for L in M["zones"].values() for d in L["W"]})
    tf = lambda x, y: tf_transform(CFG.CRS_METRIC, "EPSG:4326", [x], [y])
    S8, S4 = STRUCTURE[conn], STRUCTURE[4]; buf = int(round(a.buffer_km * 1000 / P95.CELL_M)); min_cells = int(round(a.min_km2 / P95.CELL_KM2))

    # ---- the event-source network vs the SWOT nodes ------------------------------------------------------------------------
    nx_, ny_ = M["G"]["nx"], M["G"]["ny"]; tr = g.transform
    col = np.floor((W.xy[:, 0] - tr.c) / g.cell).astype(int); row = np.floor((tr.f - W.xy[:, 1]) / g.cell).astype(int)
    inside = (row >= 0) & (row < ny_) & (col >= 0) & (col < nx_)
    on_river = np.zeros(len(node_river), bool); on_river[inside] = seed_river[row[inside], col[inside]]
    near_river = np.zeros(len(node_river), bool)
    dist_river = ndimage.distance_transform_edt(~seed_river) * g.cell
    near_river[inside] = dist_river[row[inside], col[inside]] <= 100.0
    node_rows = []
    for rn in sorted(set(node_river)):
        m = (node_river == rn) & inside
        node_rows.append(dict(river=rn, n_nodes=int(m.sum()), share_on_source_network=round(float(on_river[m].mean()), 3) if m.any() else np.nan,
                              share_within_100m=round(float(near_river[m].mean()), 3) if m.any() else np.nan))
    print("nodes on the event-source network:", node_rows, flush=True)

    # ---- seed components outside the event-source network ---------------------------------------------------------------
    lab_seed, n_seed = ndimage.label(seed_all, S8)
    seed_sizes = np.bincount(lab_seed.ravel()); seed_sizes[0] = 0
    river_ids = set(np.unique(lab_seed[seed_river])) - {0}
    seed_km2 = {int(k): float(seed_sizes[k]) * P95.CELL_KM2 for k in range(1, n_seed + 1)}
    seeded_isolated = {}                                                          # seed component id -> isolated new area it seeded (km2 summed over days)

    # ---- daily loop with lineage --------------------------------------------------------------------------------------------
    comp_rows, sum_rows, lc_rows = [], [], []
    prev_lab = None; prev_state = {}                                              # prev component id -> dict(lineage, ever, first_day)
    next_lineage = 1; lineage_info = {}
    packed = {z: {} for z in names}
    s1_cache = {}
    days = [d for d in P95.DATES if a.start is None or str(d.date()) >= a.start]
    for k, d in enumerate(days):
        if a.limit_days is not None and k >= a.limit_days:
            break
        ds = str(d.date())
        pot, w = P95.potential_mosaic(M, W, Z, ds, "connected_ceiling", margin=margin, connectivity=conn, seed=seed)
        new = pot & ~baseline
        # reproduction gate against the stored daily_new (per zone and region, as p95l)
        stored = compose_npz(M, sfx, ds)
        if stored is not None:
            diff = float((stored ^ new).sum()) * P95.CELL_KM2
            assert diff <= 0.1 + 1e-9, (ds, "stored daily_new differs from the recomputed potential by", diff, "km2")
        for z in names:
            zid = M["zone_id"][z]
            for rn, m in R.items():
                tot = float((new & m & (zone_of == zid)).sum()) * P95.CELL_KM2; r_ = ref.get((z, ds, rn), np.nan)
                assert np.isnan(r_) or abs(round(tot, 1) - r_) <= 0.1 + 1e-9, (z, ds, rn, tot, r_)
        lab_pot, cls_pot = seed_classes(pot, seed_all, seed_river, conn); pot_sizes = np.bincount(lab_pot.ravel()); pobjs = ndimage.find_objects(lab_pot)
        lab_pot4, cls_pot4 = seed_classes(pot, seed_all, seed_river, 4)
        eroded = []; er = pot; source = pot & seed_river                     # the per-day, vectorised form of terrain.connectivity.erosion_disconnect_px
        for _ in range(a.max_erosion_px):
            er = ndimage.binary_erosion(er, structure=S4) | source
            eroded.append(seed_classes(er, seed_river, seed_river, conn) + (er,))
        river_pot = cls_pot[lab_pot] == 1                                           # cells of river-connected potential components
        gap_m = ndimage.distance_transform_edt(~river_pot) * g.cell if river_pot.any() else np.full(pot.shape, np.nan, "f4")
        lab_new, n_new = ndimage.label(new, S8)
        sizes = np.bincount(lab_new.ravel()); sizes[0] = 0
        # class of every new component from its pot component (a connected set of new cells lies in one pot component)
        first_cell = np.zeros(n_new + 1, "i8")
        idx_new = np.flatnonzero(lab_new.ravel()); first_cell[lab_new.ravel()[idx_new[::-1]]] = idx_new[::-1]      # any cell per label
        pot_id = lab_pot.ravel()[first_cell]; river_now = cls_pot[pot_id] == 1
        links = link_components(prev_lab, lab_new) if prev_lab is not None else np.zeros((0, 3), "i8")
        anc = {}
        for ip, i_n, cells in links:
            anc.setdefault(int(i_n), []).append((int(ip), int(cells)))
        state = {}; cls_new = np.zeros(n_new + 1, "u1")
        for i in range(1, n_new + 1):
            A = anc.get(i, [])
            ever_before = any(prev_state[ip]["ever"] for ip, _ in A)
            first_days = [prev_state[ip]["first_day"] for ip, _ in A if prev_state[ip]["first_day"] is not None]
            if river_now[i]:
                cl = "RIVER_CONNECTED"; first_day = min(first_days) if first_days else ds
            elif ever_before:
                cl = "TRAPPED"; first_day = min(first_days)
            else:
                cl = "ISOLATED_NEVER"; first_day = None
            if A:
                lin = prev_state[max(A, key=lambda t: t[1])[0]]["lineage"]
            else:
                lin = next_lineage; next_lineage += 1
            state[i] = dict(lineage=lin, ever=bool(river_now[i]) or ever_before, first_day=first_day, cls=cl)
            cls_new[i] = CLASS_CODE[cl]
            L = lineage_info.setdefault(lin, dict(lineage_id=lin, first_day=ds, last_day=ds, days=set(), max_km2=0.0, max_day=ds, classes=set(), first_connected_day=None,
                                                  merged_from=set(), max_row=None))
            L["last_day"] = ds; L["days"].add(ds); L["classes"].add(cl)
            if first_day is not None and (L["first_connected_day"] is None or first_day < L["first_connected_day"]):
                L["first_connected_day"] = first_day
            for ip, _ in A:
                if prev_state[ip]["lineage"] != lin:
                    L["merged_from"].add(prev_state[ip]["lineage"])
        class_grid = cls_new[lab_new]                                             # 0 outside new water
        for z in names:
            cz = g.extract(class_grid, z)
            for code in CLASS_CODE.values():                                      # one bit-packed mask per class (packbits keeps 0/1 only)
                packed[z][f"{ds}_c{code}"] = np.packbits(cz == code)
        # sums per region (all components, specks included)
        conn4_lost = new & (cls_pot4[lab_pot4] != 1) & (cls_pot[lab_pot] == 1)
        er1_lab, er1_cls, er1_mask = eroded[0]
        er1_lost = new & (cls_pot[lab_pot] == 1) & ~(er1_mask & (er1_cls[er1_lab] == 1))
        # same-day Sentinel-1 on OPEN ground (grass, cropland, bare): valid and not dark = observed dry; forest, wetland and built are
        # SAR blind spots and are not counted (the maintainer's caution: a later scene never contradicts an earlier day)
        S1_same = s1_layers(M, ds) if ds in s1_dates else None
        open_g = np.isin(wc, OPEN_WC)
        s1_obs_open = (new & S1_same[0] & open_g) if S1_same is not None else None
        s1_dry_open = (new & S1_same[0] & ~S1_same[1] & open_g) if S1_same is not None else None
        trapped_cells = class_grid == CLASS_CODE["TRAPPED"]
        if S1_same is not None:                                                    # the retained-water decision tree, cell-wise, same-day scene only
            tr_water = trapped_cells & S1_same[0] & S1_same[1]; tr_dry = trapped_cells & S1_same[0] & ~S1_same[1] & open_g
        else:
            tr_water = tr_dry = np.zeros_like(trapped_cells)
        tr_unc = trapped_cells & ~tr_water & ~tr_dry
        for rn, m in R.items():
            row_ = dict(date=ds, region=rn, A_full_km2=float((new & m).sum()) * P95.CELL_KM2)
            row_["A_s1_sameday_observed_open_km2"] = float((s1_obs_open & m).sum()) * P95.CELL_KM2 if s1_obs_open is not None else np.nan
            row_["A_s1_sameday_open_no_water_km2"] = float((s1_dry_open & m).sum()) * P95.CELL_KM2 if s1_dry_open is not None else np.nan
            row_["A_trapped_s1_water_km2"] = float((tr_water & m).sum()) * P95.CELL_KM2
            row_["A_trapped_s1_open_no_water_km2"] = float((tr_dry & m).sum()) * P95.CELL_KM2
            row_["A_trapped_s1_uncertain_km2"] = float((tr_unc & m).sum()) * P95.CELL_KM2
            for cl, code in CLASS_CODE.items():
                row_[f"A_{cl.lower()}_km2"] = float((new & m & (class_grid == code)).sum()) * P95.CELL_KM2
            row_["A_conn4_link_lost_km2"] = float((conn4_lost & m).sum()) * P95.CELL_KM2
            row_["A_erosion1px_link_lost_km2"] = float((er1_lost & m).sum()) * P95.CELL_KM2
            assert abs(row_["A_full_km2"] - sum(row_[f"A_{cl.lower()}_km2"] for cl in CLASS_CODE)) < 1e-6
            sum_rows.append(row_)
            for cl, code in CLASS_CODE.items():
                sel = new & m & (class_grid == code)
                if sel.any():
                    u, cnt = np.unique(wc[sel], return_counts=True)
                    for kk, v in zip(u, cnt):
                        lc_rows.append(dict(date=ds, region=rn, semantic_class=cl, worldcover=WC_NAMES.get(int(kk), str(int(kk))), km2=float(v) * P95.CELL_KM2))
        # the isolated new area attributed to the seed components that seeded it
        iso_pot = np.unique(pot_id[1:][(cls_pot[pot_id[1:]] == 2)])
        for pid in iso_pot:
            pw = pobjs[pid - 1]; cells = lab_pot[pw] == pid; sids = set(np.unique(lab_seed[pw][cells & seed_all[pw]])) - {0}
            area = float((new[pw] & cells).sum()) * P95.CELL_KM2
            for sid in sids:
                seeded_isolated[int(sid)] = seeded_isolated.get(int(sid), 0.0) + area / max(len(sids), 1)
        # per-component table (>= min cells); specks aggregated
        s1d, lag = s1_match(ds, s1_dates)
        if s1d is not None and s1d not in s1_cache:
            s1_cache = {s1d: s1_layers(M, s1d)}
        S1 = s1_cache.get(s1d) if s1d is not None else None
        depth = np.where(pot, w - M["dem"], np.nan)
        objs = ndimage.find_objects(lab_new)
        big = [i for i in range(1, n_new + 1) if sizes[i] >= min_cells]
        for i in big:
            sl = objs[i - 1]; win = (slice(max(sl[0].start - buf, 0), min(sl[0].stop + buf, ny_)), slice(max(sl[1].start - buf, 0), min(sl[1].stop + buf, nx_)))
            cm = lab_new[win] == i; rr, cc = np.nonzero(cm)
            cx, cy = float(xs[win[1]][cc].mean()), float(ys[win[0]][rr].mean()); lon, lat = tf(cx, cy)
            ring = ndimage.binary_dilation(cm, structure=STRUCTURE[8], iterations=buf) & ~cm
            reg, reg_share = region_of({rn: m[win] for rn, m in R.items()}, cm)
            zid = int(np.bincount(zone_of[win][cm]).argmax()); z = zone_name.get(zid, "OUTSIDE")
            demw, ww, dw, scw = M["dem"][win], w[win], depth[win], sc[win]
            pid = int(pot_id[i]); pcls = int(cls_pot[pid])
            seed_bodies, seed_km2_in, seed_dem = np.nan, np.nan, np.nan
            if pcls == 2:
                pw = pobjs[pid - 1]; pc = lab_pot[pw] == pid; ps = pc & seed_all[pw]; sids = set(np.unique(lab_seed[pw][ps])) - {0}
                seed_bodies = len(sids); seed_km2_in = float(sum(seed_km2[s] for s in sids)); seed_dem = float(np.nanmedian(M["dem"][pw][ps])) if ps.any() else np.nan
            ero = np.nan; conn4 = np.nan
            if pcls == 1:
                ero = a.max_erosion_px + 1
                for kk, (el, ec, em) in enumerate(eroded, 1):
                    if not (ec[el[win][cm & em[win]]] == 1).any():
                        ero = kk; break
                conn4 = bool((cls_pot4[lab_pot4[win][cm]] == 1).any())
            openc = np.isin(wc[win][cm], OPEN_WC); open_share = float(openc.mean())
            if S1 is not None:
                v_ = S1[0][win][cm]; vs = float(v_.mean()); dks = float((S1[1][win][cm] & v_).sum() / max(v_.sum(), 1))
                vo = v_ & openc; open_obs = float(vo.sum() / max(openc.sum(), 1)); open_dark = float((S1[1][win][cm] & vo).sum() / max(vo.sum(), 1)) if vo.any() else np.nan
            else:
                vs, dks, open_obs, open_dark = np.nan, np.nan, np.nan, np.nan
            mix = wc_mix(wc[win], cm); ctx = wc_mix(wc[win], ring)
            weak = float((scw[cm] == 3).mean()); cross = float((scw[cm] == 4).mean())
            rv, rc = np.unique(riv_grid[win][cm], return_counts=True)
            s1c = s1_flags(lag, vs, dks, open_share, open_obs, open_dark); verdict = retained_verdict(state[i]["cls"], s1c if lag == 0 else "")
            flags = [state[i]["cls"], s1c] + ([verdict] if verdict else [])
            if weak >= WEAK_SHARE:
                flags.append("WEAK_SURFACE")
            if pcls == 1 and ero == 1:
                flags.append("EROSION_1PX_DISCONNECTS")
            comp_rows.append(dict(date=ds, component=i, lineage_id=state[i]["lineage"], semantic_class=state[i]["cls"], first_connected_day=state[i]["first_day"],
                                  area_km2=round(float(sizes[i]) * P95.CELL_KM2, 3), lon=round(lon[0], 4), lat=round(lat[0], 4), x=round(cx, 1), y=round(cy, 1),
                                  region=reg, region_share=reg_share, zone=z, pot_component_class={1: "river", 2: "isolated", 0: "none"}[pcls], pot_component_km2=round(float(pot_sizes[pid]) * P95.CELL_KM2, 2),
                                  seed_bodies_in_pot_component=seed_bodies, seed_km2_in_pot_component=round(seed_km2_in, 4) if np.isfinite(seed_km2_in) else np.nan, seed_dem_p50_m=round(seed_dem, 2) if np.isfinite(seed_dem) else np.nan,
                                  wc_cropland=mix.get("cropland", 0.0), wc_trees=mix.get("trees", 0.0), wc_grass=mix.get("grass", 0.0), wc_wetland=mix.get("wetland", 0.0), wc_bare_sparse=mix.get("bare_sparse", 0.0),
                                  wc_built=mix.get("built", 0.0), wc_water=mix.get("water", 0.0),
                                  ctx_bare_sparse_2km=ctx.get("bare_sparse", 0.0), ctx_trees_2km=ctx.get("trees", 0.0), ctx_cropland_2km=ctx.get("cropland", 0.0),
                                  ctx_dem_p50_m=round(float(np.nanmedian(demw[ring])), 2) if ring.any() else np.nan,
                                  dem_p05_m=round(float(np.nanpercentile(demw[cm], 5)), 2), dem_p50_m=round(float(np.nanmedian(demw[cm])), 2), dem_p95_m=round(float(np.nanpercentile(demw[cm], 95)), 2),
                                  wse_p50_m=round(float(np.nanmedian(ww[cm])), 2), freeboard_p50_m=round(float(np.nanmedian(dw[cm])), 2), depth_max_m=round(float(np.nanmax(dw[cm])), 2),
                                  support_weak_share=round(weak, 3), support_cross_river_share=round(cross, 3), support_core_share=round(float(np.isin(scw[cm], (1, 2)).mean()), 3),
                                  nearest_node_river=str(rnames[rv[rc.argmax()]]), nearest_node_km_p50=round(float(np.median(dkm_grid[win][cm])), 1),
                                  survives_conn4=conn4, erosion_disconnect_px=ero, gap_to_river_component_m=round(float(gap_m[win][cm].min()), 0) if pcls != 1 else 0.0,
                                  s1_date=s1d, lag_days=lag, s1_valid_share=round(vs, 3) if np.isfinite(vs) else np.nan, s1_dark_share_of_valid=round(dks, 3) if np.isfinite(dks) else np.nan,
                                  open_ground_share=round(open_share, 3), s1_open_observed_share=round(open_obs, 3) if np.isfinite(open_obs) else np.nan,
                                  s1_open_dark_share=round(open_dark, 3) if np.isfinite(open_dark) else np.nan, s1_class=s1c, retained_verdict=verdict,
                                  flags=";".join(flags)))
            L = lineage_info[state[i]["lineage"]]
            if sizes[i] * P95.CELL_KM2 > L["max_km2"]:
                L["max_km2"] = float(sizes[i]) * P95.CELL_KM2; L["max_day"] = ds; L["max_row"] = comp_rows[-1]
        specks = [i for i in range(1, n_new + 1) if sizes[i] < min_cells]
        if specks:
            for cl, code in CLASS_CODE.items():
                area = float(sum(sizes[i] for i in specks if cls_new[i] == code)) * P95.CELL_KM2
                if area > 0:
                    comp_rows.append(dict(date=ds, component=0, lineage_id=0, semantic_class=cl, area_km2=round(area, 3), region="specks < min_km2", flags=cl + ";SPECKS_AGGREGATED",
                                          n_specks=int(sum(1 for i in specks if cls_new[i] == code))))
        prev_lab, prev_state = lab_new, state
        if k % 5 == 0:
            print(ds, f"new {new.sum() * P95.CELL_KM2:.0f} km2, components {n_new}, >= min {len(big)}, lineages {next_lineage - 1}", round(time.time() - t0), "s", flush=True)

    # ---- outputs ---------------------------------------------------------------------------------------------------------------
    for z in names:
        G_ = M["zones"][z]["G"]; od = CFG.BULK_ROOT / "floodplain_dyn" / f"{z}{sfx}"
        np.savez_compressed(od / "daily_component_class.npz", shape=np.array([G_["ny"], G_["nx"]]), codes=json.dumps(CLASS_CODE), **packed[z])
        with rasterio.open(od / "event_source_network.tif", "w", driver="GTiff", height=G_["ny"], width=G_["nx"], count=1, dtype="uint8", crs=G_["crs"],
                           transform=G_["transform"], nodata=0, compress="deflate", tiled=True) as o:            # the seed of the primary rule, for the figures
            o.write(g.extract(seed_river, z).astype("u1"), 1)
            o.update_tags(producer="p95o_component_qa.py", meaning="event-source network: largest 8-connected component of the pre-breach water map (frames composed where they have labels)")
    C = pd.DataFrame(comp_rows); C.to_csv(CFG.TABLES / f"p95o_components{sfx}.csv", index=False)
    S = pd.DataFrame(sum_rows)
    for col_ in S.columns:
        if col_.endswith("_km2"):
            S[col_] = S[col_].round(2)
    S["seed_network_of_run"] = seed_network
    for alt in ("_connected_ceiling_seed_mainstem", "_connected_ceiling_seed_allprewater", "_connected_ceiling_memory", "_connected_ceiling"):
        q = CFG.TABLES / f"p95_daily_area_pooled{alt}.csv"
        if alt != sfx and q.exists():
            k_ = pd.read_csv(q)[["date", "region", "new_km2"]].rename(columns={"new_km2": f"A_new{alt}_km2"}); S = S.merge(k_, on=["date", "region"], how="left")
    S.to_csv(CFG.TABLES / f"p95o_summary{sfx}.csv", index=False)
    L = pd.DataFrame(lc_rows, columns=["date", "region", "semantic_class", "worldcover", "km2"]); L["km2"] = L.km2.round(3); L.to_csv(CFG.TABLES / f"p95o_landcover{sfx}.csv", index=False)
    lin_rows = []
    for lin, info in lineage_info.items():
        mr = info["max_row"] or {}
        lin_rows.append(dict(lineage_id=lin, first_day=info["first_day"], last_day=info["last_day"], n_days=len(info["days"]), max_km2=round(info["max_km2"], 3), max_day=info["max_day"],
                             classes=";".join(sorted(info["classes"])), verdict=("ISOLATED_NEVER" if info["classes"] == {"ISOLATED_NEVER"} else "RIVER_CONNECTED" if info["classes"] == {"RIVER_CONNECTED"}
                                                                                 else "CONNECTED_THEN_TRAPPED" if "TRAPPED" in info["classes"] else "MIXED"),
                             first_connected_day=info["first_connected_day"], merged_from=";".join(str(x) for x in sorted(info["merged_from"])),
                             **{k_: mr.get(k_) for k_ in ("lon", "lat", "region", "zone", "wc_cropland", "wc_trees", "wc_grass", "wc_wetland", "wc_bare_sparse", "ctx_bare_sparse_2km", "ctx_trees_2km",
                                                        "dem_p50_m", "wse_p50_m", "nearest_node_river", "nearest_node_km_p50", "support_weak_share", "seed_bodies_in_pot_component", "seed_km2_in_pot_component",
                                                        "gap_to_river_component_m", "survives_conn4", "erosion_disconnect_px", "s1_date", "lag_days", "s1_valid_share", "s1_dark_share_of_valid",
                                                        "open_ground_share", "s1_open_observed_share", "s1_open_dark_share", "s1_class", "retained_verdict", "flags")}))
    Ld = pd.DataFrame(lin_rows, columns=["lineage_id", "first_day", "last_day", "n_days", "max_km2", "max_day", "classes", "verdict", "first_connected_day", "merged_from"] if not lin_rows else None)
    Ld = Ld.sort_values("max_km2", ascending=False) if len(Ld) else Ld; Ld.to_csv(CFG.TABLES / f"p95o_lineages{sfx}.csv", index=False)
    sc_rows = []
    for sid in sorted((k_ for k_ in seed_km2 if k_ not in river_ids), key=lambda k_: -seed_km2[k_])[:20]:
        cells = lab_seed == sid; rr, cc = np.nonzero(cells); lon, lat = tf(float(xs[cc].mean()), float(ys[rr].mean()))
        nodes_in = int(sum(1 for r_, c_, ok in zip(row, col, inside) if ok and cells[r_, c_]))
        sc_rows.append(dict(seed_component=int(sid), area_km2=round(seed_km2[sid], 3), lon=round(lon[0], 4), lat=round(lat[0], 4), swot_nodes_inside=nodes_in,
                            region=region_of(R, cells)[0], isolated_new_km2_seeded_sum_over_days=round(seeded_isolated.get(int(sid), 0.0), 2)))
    pd.DataFrame(sc_rows).to_csv(CFG.TABLES / f"p95o_seed_components{sfx}.csv", index=False)
    key = S[S.date.isin(["2023-06-06", "2023-06-07", "2023-06-09", "2023-06-13", "2023-06-15"]) & (S.region == "DNIPRO_CORRIDOR")]
    manifest = dict(producer="p95o_component_qa.py", run_suffix=sfx, seed_network_of_run=seed_network, connectivity=conn, min_km2=a.min_km2, buffer_km=a.buffer_km,
                    event_source_network="largest 8-connected component of the pre-breach water map (labels pre_water_frac >= 20 %)",
                    event_source_km2=round(float(seed_river.sum()) * P95.CELL_KM2, 2), all_prewater_km2=round(float(seed_all.sum()) * P95.CELL_KM2, 2), n_seed_components=int(n_seed),
                    nodes_vs_source_network=node_rows, classes=CLASS_CODE,
                    definitions=dict(RIVER_CONNECTED="new-water component whose potential component touches the event-source network on that day -> the primary reconstruction",
                                     TRAPPED="not river-connected on that day, but the component or an ancestor in the day-to-day overlap lineage was -> retained-water candidate, checked against same-day EO",
                                     ISOLATED_NEVER="no river-connected ancestor: seeded by isolated pre-breach water only -> not event inundation (the artefact of the superseded seeding)",
                                     erosion_disconnect_px="morphological sensitivity (4-neighbour erosions of the potential mask with the source network kept), not a geometric width",
                                     s1_classes="S1_WATER (dark water >= 20 % of observed cells); S1_OPEN_SURFACE_NO_WATER (>= 30 % open ground, >= 50 % of it observed, <= 5 % dark); S1_NO_WATER_SIGNAL_VEGETATED (forest / reed / built dominate: not informative); S1_INCONCLUSIVE; S1_UNOBSERVED; prefix LATER_ when the scene is not of the same day (a later scene never contradicts an earlier day)",
                                     retained_verdict="TRAPPED components, same-day scene only: S1_WATER -> RETAINED_PLAUSIBLE; S1_OPEN_SURFACE_NO_WATER -> LIKELY_DRAINED; otherwise RETAINED_UNCERTAIN"),
                    corridor_key_days=key.to_dict("records"), decision="D-SEED_PRIMARY (maintainer, 2026-09-30): the event source is the connected river network; all_prewater is a superseded provenance variant")
    (CFG.TABLES / f"p95o_manifest{sfx}.json").write_text(json.dumps(manifest, indent=1, default=str))
    pd.set_option("display.width", 250)
    print(key.drop(columns=[c_ for c_ in key.columns if c_.startswith("A_new_")], errors="ignore").to_string(index=False))
    print(Ld.head(12).to_string(index=False))
    if not a.no_figure:
        figure(M, sfx, packed, seed_river, W, a)
    print("->", f"tables/p95o_*{sfx}.csv, figures/m6_v003A/p95o_isolated_components{sfx}.png", round(time.time() - t0), "s")


def compare_runs(M, sfx_a, sfx_b, R, own):
    """Retained water of a memory variant: new(sfx_b) minus new(sfx_a) per day and region, with its Sentinel-1 support."""
    P95 = _ld("p95_hand_daily_inundation"); g = M["grid"]; names = M["names"]
    s1_dates = sorted({d for L in M["zones"].values() for d in L["W"]}); rows = []
    wc = g.compose({z: L["wc"] for z, L in M["zones"].items()}, 0, order=names, dtype="u1"); open_g = np.isin(wc, OPEN_WC)
    packed = {z: {} for z in names}
    for d in P95.DATES:
        ds = str(d.date()); A = compose_npz(M, sfx_a, ds); B = compose_npz(M, sfx_b, ds)
        if A is None or B is None:
            continue
        ret = B & ~A & own; lost = A & ~B & own
        S1 = s1_layers(M, ds) if ds in s1_dates else None                          # the verdict uses the same-day scene only
        if S1 is not None:
            water = ret & S1[0] & S1[1]; dry = ret & S1[0] & ~S1[1] & open_g
        else:
            water = dry = np.zeros_like(ret)
        unc = ret & ~water & ~dry
        for z in names:
            for code, mask in ((1, water), (2, dry), (3, unc)):
                packed[z][f"{ds}_c{code}"] = np.packbits(g.extract(mask, z))
        s1d, lag = s1_match(ds, s1_dates)
        for rn, m in R.items():
            r = ret & m; row = dict(date=ds, region=rn, A_new_a_km2=round(float((A & m).sum()) * P95.CELL_KM2, 2), A_new_b_km2=round(float((B & m).sum()) * P95.CELL_KM2, 2),
                                    retained_km2=round(float(r.sum()) * P95.CELL_KM2, 2), lost_km2=round(float((lost & m).sum()) * P95.CELL_KM2, 2),
                                    retained_s1_water_km2=round(float((water & m).sum()) * P95.CELL_KM2, 2), retained_s1_open_no_water_km2=round(float((dry & m).sum()) * P95.CELL_KM2, 2),
                                    retained_s1_uncertain_km2=round(float((unc & m).sum()) * P95.CELL_KM2, 2), s1_same_day=S1 is not None, next_s1_date=s1d, next_s1_lag_days=lag)
            rows.append(row)
    for z in names:
        G_ = M["zones"][z]["G"]
        np.savez_compressed(CFG.BULK_ROOT / "floodplain_dyn" / f"{z}{sfx_b}" / "retained_class.npz", shape=np.array([G_["ny"], G_["nx"]]), codes=json.dumps(RETAINED_CODE), **packed[z])
    D = pd.DataFrame(rows); out = CFG.TABLES / f"p95o_retained{sfx_b}_vs{sfx_a}.csv"; D.to_csv(out, index=False)
    print(D[D.region == "DNIPRO_CORRIDOR"].to_string(index=False)); print("->", out)


def class_layer(packed, ds, ny, nx):
    """The class code raster (0 none / 1 river-connected / 2 trapped / 3 isolated-never) of a day from the per-class packed masks."""
    out = np.zeros((ny, nx), "u1")
    for code in CLASS_CODE.values():
        k = f"{ds}_c{code}"
        if k in packed:
            out[np.unpackbits(packed[k], count=ny * nx).reshape(ny, nx).astype(bool)] = code
    return out


def figure(M, sfx, packed, seed_river, W, a):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource, ListedColormap
    from matplotlib.patches import Patch
    g = M["grid"]; names = M["names"]; ds_ = ("2023-06-06", "2023-06-09", "2023-06-15")
    dem = M["dem"][::4, ::4]; hs = LightSource(azdeg=315, altdeg=40).hillshade(np.nan_to_num(dem, nan=0), vert_exag=3, dx=80, dy=80)
    ext = [g.transform.c / 1e3, (g.transform.c + g.cell * g.shape[1]) / 1e3, (g.transform.f - g.cell * g.shape[0]) / 1e3, g.transform.f / 1e3]
    cm = ListedColormap(["#ffffff", COL["river"], COL["trapped"], COL["isolated"]])
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.6), constrained_layout=True)
    for ax, ds in zip(axs, ds_):
        cls = g.compose({z: class_layer(packed[z], ds, M["zones"][z]["G"]["ny"], M["zones"][z]["G"]["nx"]) for z in names}, 0, order=names, dtype="u1")
        km = {k: float((cls == c).sum()) * 4e-4 for k, c in CLASS_CODE.items()}
        ax.imshow(hs, cmap="gray", extent=ext, vmin=0, vmax=1, alpha=0.6, interpolation="bilinear")
        ax.imshow(np.ma.masked_where(~seed_river[::4, ::4], np.ones_like(dem)), cmap=ListedColormap([COL["network"]]), extent=ext, alpha=0.9, interpolation="nearest")
        ax.imshow(np.ma.masked_where(cls[::2, ::2] == 0, cls[::2, ::2]), cmap=cm, vmin=0, vmax=3, extent=ext, interpolation="nearest")
        iso = cls[::2, ::2] == CLASS_CODE["ISOLATED_NEVER"]
        if iso.any():
            ax.contour(iso.astype("f4"), levels=[0.5], colors=["#111111"], linewidths=0.6, extent=ext, origin="upper")
        ax.set_xlim(436, 540); ax.set_ylim(5133, 5226); ax.set_aspect("equal")
        ax.set_title(f"{ds}:  river-connected {km['RIVER_CONNECTED']:.0f}  |  trapped {km['TRAPPED']:.0f}  |  isolated-never {km['ISOLATED_NEVER']:.0f} km²  (all regions; run {sfx})", fontsize=8.5, loc="left")
        ax.set_xlabel("easting, km"); ax.set_ylabel("northing, km")
    axs[0].legend(handles=[Patch(fc=COL["network"], label="event-source network (largest connected component of the pre-breach water map)"), Patch(fc=COL["river"], label="river-connected: the flood"),
                           Patch(fc=COL["trapped"], label="trapped after an earlier connection: retained-water candidate"), Patch(fc=COL["isolated"], ec="#111111", label="isolated, never connected: seeded by ponds / canals -- not event inundation")],
                  loc="lower left", fontsize=7)
    FIG.mkdir(parents=True, exist_ok=True); fig.savefig(FIG / f"p95o_isolated_components{sfx}.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    main()
