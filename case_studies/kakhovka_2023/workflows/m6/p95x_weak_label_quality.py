# New in floodstate-eo, 2026-09-30; rewritten the same day on the maintainer's review (best state estimate + quality metadata, not
# UNKNOWN wherever something is uncertain; the p95p-p95w branch defined where the daily timing is weak and stops there). STATUS: ACTIVE.
"""P95x -- the daily state mask between the EO observations: best state estimate + source + quality flags.

Per day t, 2023-06-06 .. 2023-06-30, on the 20 m union grid inside the reconstruction domain (255 outside it):
  band 1 state      0 DRY  1 WATER  2 UNKNOWN
  band 2 source     1 EO_S1  2 EO_S2  3 MODEL_STRONG  4 MODEL_WEAK  5 REFERENCE (optical pre-breach water, no same-day EO)  0 none
  band 3 flags      1 STORAGE_SENSITIVE  2 WEAK_CONNECTIVITY  4 SENSOR_BLIND  8 REFERENCE_UNCERTAIN  16 RECESSION_UNCERTAIN
                    32 VEGETATED_WETLAND
  band 4 reference  0 none  1 optical pre-breach water (p60 pre_water_frac >= 20 %)  2 normally wet by the model only (p95 baseline)
State (maintainer 2026-09-30):
  same-day EO                                   -> its state (source EO_S2 / EO_S1)
  optical pre-breach water, no same-day EO      -> WATER (source REFERENCE)
  otherwise P = P(water) of the p95e ensemble (1000 worlds; water = the day's connected water surface, new or baseline):
      P >= 0.8 -> WATER;  P <= 0.05 -> DRY;  otherwise UNKNOWN -- the only model case of UNKNOWN
  a day between an EO WATER observation and the next EO DRY observation of the cell (its nearest EO states before and after):
      RECESSION_UNCERTAIN, and the model's dryness is not accepted (losing connectivity is not drainage): WATER if P >= 0.8,
      else UNKNOWN
  a model state is MODEL_WEAK when STORAGE_SENSITIVE, WEAK_CONNECTIVITY or RECESSION_UNCERTAIN is set, else MODEL_STRONG
EO: own Sentinel-2 (p54a stacks, NDWI > 0 and MNDWI > 0, as p94) where valid: water anywhere; no-water is dryness except under
  trees, shrub, built-up or reeds (there SENSOR_BLIND and the model decides). Own Sentinel-1 June dark-water masks where S2 did
  not decide: dark is water only where the reconstruction allows water THAT day (P > 0.05) or on reference water -- dark S1 over
  dry sand, burnt or bare ground is not water (in the lowland south of Krynky S1 marked 10 km2 on 21 June where S2 on 18/20/23
  June and UNOSAT's own S1 saw none), so elsewhere dark S1 is SENSOR_BLIND; not-dark is dryness on open ground only.
  An EO state is the state at the acquisition time (S1 descending ~04 UTC, ascending ~16 UTC, S2 ~09 UTC; 6 June S1 = ~4 h after
  the breach); a model state is the day's water surface (daily gauge means + SWOT).
Flags are metadata, never a reason to drop a state:
  STORAGE_SENSITIVE   depressions only the flood connects (sill > 0.1 m above the pre-breach surface), >= 0.5 km2, >= 0.3 m deep,
                      reached by the reconstruction: arrival and drainage timing are not reconstructed there (p95p-p95w)
  WEAK_CONNECTIVITY   on ground the reconstruction can reach: weak or cross-river water-surface support (p95l codes 3, 4), or joined
                      to the river by diagonal links only (far terraces the water never reaches carry no support flag)
  SENSOR_BLIND        the day's sensor observed the cell but cannot confirm its state there
  REFERENCE_UNCERTAIN normally wet by the model only: the water state is fine, event water vs normal water is not known
  VEGETATED_WETLAND   the reed / wetland complex (maintainer 2026-10-01): WorldCover herbaceous wetland or model-only normally wet.
                      Before the breach its vegetation already shows a C-band signature consistent with wet or inundated emergent
                      vegetation (p95z), and the radar does not see the DEM line between normally-wet and event-only reeds, so the
                      complex is reported apart from the dry ground; the state there is kept (metadata, not a class).
Ground classes (ground_class.tif, static; the split of the paper's areas, p95e --mode split): 0 DRY_BEFORE_EVENT (no optical
  pre-breach water, no reed / wetland complex, not WorldCover water), 1 VEGETATED_WETLAND, 2 OPEN_WATER_REFERENCE (optical pre-breach
  water), 3 OTHER_WATER (WorldCover water outside both), 255 outside the domain. Transitions and the comparisons are given per class.
Event attributes (event_attributes.tif; WATER on non-reference ground; days from 2023-06-05, 255 = never): first_wet_day,
  last_wet_day, n_wet_days, first_dry_day (the first DRY after the last WATER).
Check, once, against UNOSAT 3614 (never a label source) on ground that was not water before the breach (optical reference and
  UNOSAT's own reference water removed): 7 June ICEYE is the test of the gap filling -- no own EO that day. 9 June Landsat-9,
  13 June S2 and 21 June S1 are reported too; UNOSAT's 21 June S1 is the satellite of our same-day S1.
Transitions (maintainer 2026-10-01: a falling WATER curve is not drying): every non-reference pixel that was WATER on some day is
  followed day by day -- still WATER / DRY confirmed by EO since its last WATER / DRY by the model only / UNKNOWN (p95x_transitions.csv).
  On EO days the EO state and the model's own state are compared on the same cells (EO-decided, non-reference: p95x_eo_vs_model.csv).
Outputs: $BULK_ROOT/floodplain_dyn/_weak_labels/state_<date>.tif, event_attributes.tif, storage_sensitive.tif, connection_level.npz
  (cache); tables/p95x_state_summary.csv, p95x_transitions.csv, p95x_eo_vs_model.csv, p95x_storage_depressions.csv,
  p95x_unosat_check.csv, p95x_manifest.json;
  figures/m6_v003A/p95x_state_mask.png, p95x_state_mask_krynky.png
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SFX = "_connected_ceiling"
STATE = {"DRY": 0, "WATER": 1, "UNKNOWN": 2}
SOURCE = {"EO_S1": 1, "EO_S2": 2, "MODEL_STRONG": 3, "MODEL_WEAK": 4, "REFERENCE": 5}
FLAG = {"STORAGE_SENSITIVE": 1, "WEAK_CONNECTIVITY": 2, "SENSOR_BLIND": 4, "REFERENCE_UNCERTAIN": 8, "RECESSION_UNCERTAIN": 16, "VEGETATED_WETLAND": 32}
GROUND = {"DRY_BEFORE_EVENT": 0, "VEGETATED_WETLAND": 1, "OPEN_WATER_REFERENCE": 2, "OTHER_WATER": 3}
WETLAND_WC = (90,)                           # WorldCover herbaceous wetland (reeds)
P_WET, P_DRY = 0.8, 0.05
WEAK_SUPPORT_CODES = (3, 4)                  # p95l: weak (> 10 km from a SWOT node), cross-river (Inhulets valley)
F_STEP, F_LO, F_HI = 0.1, -2.0, 20.0
DEP_EDGE, DEP_DEPTH, DEP_MIN_KM2, DEP_ABOVE_PRE = 0.15, 0.3, 0.5, 0.1
OPEN_WC = (30, 40, 60)                       # grass, cropland, bare: C-band not-dark is dryness there (p95o)
S2_BLIND_WC = (10, 20, 50, 90, 95)           # trees, shrub, built-up, reeds, mangrove: optical no-water is not dryness there
FRAMES = ("B1", "B2", "B3")
DAY0, NEVER, OUTSIDE = "2023-06-05", 255, 255
EO_NONE, EO_S1_WATER, EO_S1_DRY, EO_S2_WATER, EO_S2_DRY, EO_BLIND = 0, 1, 2, 3, 4, 5
KRYNKY_WINDOW = (32.90, 46.595, 33.23, 46.78)   # = p95r (lon0, lat0, lon1, lat1)


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def connection_level(dem, source, lo=F_LO, hi=F_HI, step=F_STEP):
    """F(x): the lowest level L (step grid) at which x lies in a component of {dem < L} (8-connected) that contains a source cell; inf if none."""
    from scipy import ndimage
    z = np.nan_to_num(dem, nan=np.inf); F = np.full(dem.shape, np.inf, "f4"); st = np.ones((3, 3), bool)
    for L in np.round(np.arange(lo + step, hi + step / 2, step), 3):
        below = z < L
        lab, n = ndimage.label(below, structure=st)
        hit = np.zeros(n + 1, bool); hit[np.unique(lab[source & below])] = True; hit[0] = False
        F[hit[lab] & ~np.isfinite(F)] = L
    return F


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--no-figure", action="store_true"); a = ap.parse_args(); t0 = time.time()
    import pandas as pd
    import rasterio
    from floodstate_eo import _kakhovka_legacy_config as CFG
    from floodstate_eo.terrain.connectivity import largest_component
    from rasterio import features
    from rasterio.enums import Resampling
    from rasterio.warp import reproject
    from rasterio.warp import transform as tf_transform
    from scipy import ndimage
    from shapely.geometry import shape
    from shapely.ops import unary_union
    TAB = ROOT / "tables"; FIG = ROOT / "figures" / "m6_v003A"; OUT = CFG.BULK_ROOT / "floodplain_dyn" / "_weak_labels"; OUT.mkdir(parents=True, exist_ok=True)
    O = _ld("p95o", HERE / "p95o_component_qa.py"); P95 = O._ld("p95_hand_daily_inundation"); T = _ld("p95t", HERE / "p95t_eo_recession.py")
    V = _ld("p95v", HERE / "p95v_depression_storage.py")
    days = [str(x.date()) for x in pd.date_range("2023-06-06", "2023-06-30", freq="D")]; CK = P95.CELL_KM2
    P = P95.load_p92(); man = O.load_manifest(SFX); c = man["constants"]
    if c.get("seed_network") != "main_stem" or int(man.get("rev", 0)) < 9:
        raise SystemExit("p95x needs the primary run with the river-network seed and the rev-9 baseline (optical pre-breach water only)")
    conn = int(c.get("connectivity", 8)); margin = float(c.get("margin_m", 0.0))
    M = P95.mosaic_layers(P, with_s1=True); g = M["grid"]; tr = g.transform; shp = g.shape; crs = M["G"]["crs"]
    W_eng, dxm, _ = O.engine_for(P95, man, SFX); M["base"] = M["base_geom"] & P95.dam_mask(M, dxm); Z = W_eng.prepare(M)
    seed = largest_component(M["seed"], conn); dom = M["base"]
    B = O.compose_npz(M, SFX, "baseline"); ref = np.zeros(shp, "u1"); ref[B & ~M["pre"]] = 2; ref[M["pre"]] = 1; ref[~dom] = 0
    weak_support = np.isin(O.compose_tif(M, SFX, "support_class.tif"), WEAK_SUPPORT_CODES)
    wc = g.compose({z: L["wc"] for z, L in M["zones"].items()}, 0, order=M["names"], dtype="u1"); open_g = np.isin(wc, OPEN_WC); s2_blind_g = np.isin(wc, S2_BLIND_WC)
    ground = np.full(shp, 255, "u1"); ground[dom] = GROUND["DRY_BEFORE_EVENT"]
    ground[dom & (np.isin(wc, WETLAND_WC) | (ref == 2))] = GROUND["VEGETATED_WETLAND"]
    ground[dom & (wc == 80) & (ground == GROUND["DRY_BEFORE_EVENT"])] = GROUND["OTHER_WATER"]
    ground[dom & (ref == 1)] = GROUND["OPEN_WATER_REFERENCE"]
    with rasterio.open(OUT / "ground_class.tif", "w", driver="GTiff", height=shp[0], width=shp[1], count=1, dtype="uint8", crs=crs, transform=tr,
                       nodata=255, compress="lzw", tiled=True, blockxsize=512, blockysize=512) as o:
        o.write(ground, 1); o.set_band_description(1, "ground_class"); o.update_tags(producer="p95x_weak_label_quality.py", classes=json.dumps(GROUND), outside="255")
    gkm = {gn: round(float((ground == gv).sum()) * CK, 1) for gn, gv in GROUND.items()}; print("ground classes km2:", gkm, flush=True)
    zdir = CFG.BULK_ROOT / "floodplain_dyn" / f"{M['names'][0]}{SFX}"
    print(f"grid {shp}, domain {dom.sum()*CK:.0f} km2; reference: optical {(ref == 1).sum()*CK:.0f} km2, model-only {(ref == 2).sum()*CK:.0f} km2; {round(time.time() - t0)} s", flush=True)

    def p_water(d):
        for nm in (f"p95e_cellprob_water_{d}.tif", f"p95e_cellprob_water_daily_{d}.tif"):
            if (zdir / nm).exists():
                with rasterio.open(zdir / nm) as s:
                    n_draws = float(s.tags()["n_draws"])
                cnt = O.compose_tif(M, SFX, nm, 65535, "u2")
                return np.where(dom & (cnt < 65535), cnt.astype("f4") / n_draws, 0.0).astype("f4"), nm
        raise SystemExit(f"no P(water) raster for {d}: run p95e --mode cellprob (rebuild steps p95e_cellprob, p95e_cellprob_daily)")

    s1_keys = {}
    for z in M["names"]:
        with np.load(CFG.S1_CACHE / P95.ZONES[z]["cache"] / "per_scene_water.npz", allow_pickle=True) as zz:
            s1_keys[z] = sorted(k for k in zz.files if k.startswith("2023"))
    s1_scenes = lambda d: sorted({f"{z.split('_')[0]}_{z.split('_')[1]}:{k[11:]}" for z, ks in s1_keys.items() for k in ks if k.startswith(d)})

    def s1_day(d):
        if not any(d in L["W"] for L in M["zones"].values()):
            return None, None
        z0 = lambda L: np.zeros((L["G"]["ny"], L["G"]["nx"]), bool)
        Vd = g.compose({z: L["V"].get(d, z0(L)) for z, L in M["zones"].items()}, False, order=M["names"], dtype=bool)
        Wd = g.compose({z: L["W"].get(d, z0(L)) for z, L in M["zones"].items()}, False, order=M["names"], dtype=bool)
        return Vd, Wd & Vd

    def s2_day(d):
        """(valid, water, frames) on the 20 m grid: the frame with the larger valid share of the 10 m pixels wins a cell; observed
        when >= 75 % of them are valid, water when >= 50 % of the valid ones are water."""
        best_v = np.zeros(shp, "f4"); best_w = np.zeros(shp, "f4"); used = []
        for fid in FRAMES:
            p = CFG.BULK_ROOT / "frames10" / fid / "indices" / f"{d}.tif"; pv = p.with_name(f"{d}_valid.tif")
            if not (p.exists() and pv.exists()):
                continue
            with rasterio.open(p) as s:
                dsc = list(s.descriptions); ndwi = s.read(dsc.index("NDWI") + 1); mndwi = s.read(dsc.index("MNDWI") + 1); nd = s.nodata; tr10, crs10 = s.transform, s.crs
            with rasterio.open(pv) as s:
                v = (s.read(1) > 0) & (ndwi != nd) & (mndwi != nd)
            w = v & (ndwi > 0) & (mndwi > 0); del ndwi, mndwi
            fr = []
            for src in (v, w):
                dst = np.full(shp, np.nan, "f4")
                reproject(src.astype("f4"), dst, src_transform=tr10, src_crs=crs10, dst_transform=tr, dst_crs=crs, resampling=Resampling.average,
                          src_nodata=np.nan, dst_nodata=np.nan)
                fr.append(np.nan_to_num(dst, nan=0.0))
            vf, wf = fr
            if vf.max() <= 0:
                continue
            assert vf.sum() * 4 <= 1.01 * v.sum() + 4, f"S2 {fid} {d}: the 20 m valid share exceeds the 10 m valid pixels (resampling inflation)"
            better = vf > best_v; best_v[better] = vf[better]; best_w[better] = wf[better]; used.append(fid)
        if not used:
            return None, None, used
        valid = best_v >= 0.75
        return valid, valid & (best_w >= 0.5 * best_v), used

    # ---- where the reconstruction can place water, and the storage-sensitive depressions -------------------------------------
    reach = np.zeros(shp, bool)
    for d in days:
        reach |= P95.potential_mosaic(M, W_eng, Z, d, "connected_ceiling", margin=margin, connectivity=conn, seed=seed)[0]
        reach |= p_water(d)[0] > P_DRY
    reach &= dom
    meta = dict(shape=[int(v) for v in shp], step=F_STEP, lo=F_LO, hi=F_HI, source="main_stem", connectivity=8)
    cache = OUT / "connection_level.npz"; F = None
    if cache.exists():
        zc = np.load(cache)
        if json.loads(str(zc["meta"])) == meta:
            F = zc["F"]
    if F is None:
        F = connection_level(M["dem"], seed); np.savez_compressed(cache, F=F, meta=json.dumps(meta))
    H_pre = np.asarray(W_eng.field(Z, P95.BASELINE_DATE, margin), "f4")
    depth_F = np.where(np.isfinite(F) & np.isfinite(M["dem"]), F - np.nan_to_num(M["dem"]), 0.0).astype("f4")
    cand = dom & (ref != 1) & (depth_F > DEP_EDGE)
    lab, n = ndimage.label(cand, structure=np.ones((3, 3), bool)); idx = np.arange(1, n + 1)
    dep = pd.DataFrame(dict(id=idx, km2=np.asarray(ndimage.sum(cand, lab, idx)) * CK, deepest_m=np.asarray(ndimage.maximum(depth_F, lab, idx)),
                            reached=np.asarray(ndimage.maximum(reach, lab, idx)) > 0, sill_m=np.asarray(ndimage.maximum(np.where(cand, F, -np.inf), lab, idx)),
                            pre_level_m=np.asarray(ndimage.median(np.nan_to_num(H_pre, nan=-99.0), lab, idx))))
    dep["storage_sensitive"] = (dep.km2 >= DEP_MIN_KM2) & (dep.deepest_m >= DEP_DEPTH) & dep.reached & (dep.sill_m > dep.pre_level_m + DEP_ABOVE_PRE)
    keep = np.zeros(n + 1, bool); keep[dep.id[dep.storage_sensitive].to_numpy()] = True; storage = keep[lab]
    com = np.asarray(ndimage.center_of_mass(cand, lab, idx)).reshape(-1, 2)
    dep["x_m"] = tr.c + (com[:, 1] + 0.5) * g.cell; dep["y_m"] = tr.f - (com[:, 0] + 0.5) * g.cell
    lowland = int(lab[int((tr.f - V.TARGET_XY[1]) / g.cell), int((V.TARGET_XY[0] - tr.c) / g.cell)])
    dep.sort_values("km2", ascending=False).to_csv(TAB / "p95x_storage_depressions.csv", index=False); del lab, depth_F, cand
    print(f"STORAGE_SENSITIVE {storage.sum()*CK:.1f} km2 in {int(dep.storage_sensitive.sum())} depressions; the lowland south of Krynky "
          f"{'included' if keep[lowland] else 'NOT included'}; {round(time.time() - t0)} s", flush=True)
    with rasterio.open(OUT / "storage_sensitive.tif", "w", driver="GTiff", height=shp[0], width=shp[1], count=1, dtype="uint8", crs=crs, transform=tr,
                       nodata=None, compress="lzw", tiled=True, blockxsize=512, blockysize=512) as o:
        o.write(storage.astype("u1"), 1); o.set_band_description(1, "storage_sensitive")

    # ---- pass 1: the EO state of every day (the recession rule looks at the next EO state) --------------------------------------
    eo = np.zeros((len(days), *shp), "u1"); eo_src = {}
    for i, d in enumerate(days):
        v1, w1 = s1_day(d); v2, w2, s2f = s2_day(d); e = eo[i]
        if v2 is not None:
            e[v2 & w2] = EO_S2_WATER; e[v2 & ~w2 & ~s2_blind_g] = EO_S2_DRY; e[v2 & ~w2 & s2_blind_g] = EO_BLIND
        if v1 is not None:
            free = v1 & ((e == EO_NONE) | (e == EO_BLIND)); plausible = (p_water(d)[0] > P_DRY) | (ref > 0)
            e[free & w1 & plausible] = EO_S1_WATER; e[free & ~w1 & open_g] = EO_S1_DRY
            e[free & ((w1 & ~plausible) | (~w1 & ~open_g))] = EO_BLIND
        e[~dom] = EO_NONE
        eo_src[d] = dict(s1_scenes=s1_scenes(d), s2_frames=s2f)
    print(f"EO states of {len(days)} days; {round(time.time() - t0)} s", flush=True)
    next_dry = np.zeros((len(days), *shp), bool); nxt = np.zeros(shp, "u1")      # nearest EO state AFTER day i: 1 water, 2 dry
    for i in range(len(days) - 1, -1, -1):
        next_dry[i] = nxt == 2
        e = eo[i]; nxt[(e == EO_S1_WATER) | (e == EO_S2_WATER)] = 1; nxt[(e == EO_S1_DRY) | (e == EO_S2_DRY)] = 2
    del nxt

    # ---- the UNOSAT layers of the check ----------------------------------------------------------------------------------------------
    def ras(nm):
        fc = json.loads((T.utm_dir(CFG.BULK_ROOT) / f"{nm}.geojson").read_text())["features"]
        return features.rasterize([(unary_union([shape(f_["geometry"]) for f_ in fc]), 1)], out_shape=shp, transform=tr, fill=0, dtype="uint8").astype(bool)
    U = {}; uref = ras(T.REF)
    for k in T.PRIMARY:
        dday, sensor, wl, al, cl = T.EO[k]
        ob = ras(al) & dom & (ref != 1) & ~uref
        if cl:
            ob &= ~ras(cl)
        U[dday] = dict(key=k, sensor=sensor, ob=ob, water=ras(wl) & ob)

    # ---- pass 2: states, sources, flags, event attributes ------------------------------------------------------------------------
    prev = np.zeros(shp, "u1")                                                    # nearest EO state BEFORE the day: 1 water, 2 dry
    first_wet = np.full(shp, NEVER, "u1"); last_wet = np.full(shp, NEVER, "u1"); n_wet = np.zeros(shp, "u1"); first_dry = np.full(shp, NEVER, "u1")
    prof = dict(driver="GTiff", height=shp[0], width=shp[1], count=4, dtype="uint8", crs=crs, transform=tr, nodata=OUTSIDE, compress="lzw", tiled=True, blockxsize=512, blockysize=512)
    rows, crows, pfiles, trows, vrows = [], [], {}, [], []; S_, SR, FL = STATE, SOURCE, FLAG
    wet_once = np.zeros(shp, bool); eo_dry_since = np.zeros(shp, bool); nonref = dom & np.isin(ground, (GROUND["DRY_BEFORE_EVENT"], GROUND["VEGETATED_WETLAND"]))
    GSPLIT = (("dry-before-event ground", GROUND["DRY_BEFORE_EVENT"]), ("vegetated wetland", GROUND["VEGETATED_WETLAND"]))
    for i, d in enumerate(days):
        k = int((pd.Timestamp(d) - pd.Timestamp(DAY0)).days); e = eo[i]
        p, pfile = p_water(d); pfiles[d] = pfile
        pot, _w = P95.potential_mosaic(M, W_eng, Z, d, "connected_ceiling", margin=margin, connectivity=conn, seed=seed)
        pot4, _w = P95.potential_mosaic(M, W_eng, Z, d, "connected_ceiling", margin=margin, connectivity=4, seed=seed); del _w
        fl = np.zeros(shp, "u1")
        fl[storage] |= FL["STORAGE_SENSITIVE"]; fl[(weak_support & reach) | (pot & ~pot4)] |= FL["WEAK_CONNECTIVITY"]; fl[e == EO_BLIND] |= FL["SENSOR_BLIND"]
        fl[ref == 2] |= FL["REFERENCE_UNCERTAIN"]; fl[ground == GROUND["VEGETATED_WETLAND"]] |= FL["VEGETATED_WETLAND"]
        noeo = (e == EO_NONE) | (e == EO_BLIND)
        rec = noeo & (prev == 1) & next_dry[i] & (ref != 1); fl[rec] |= FL["RECESSION_UNCERTAIN"]
        st = np.full(shp, S_["UNKNOWN"], "u1"); src = np.zeros(shp, "u1")
        st[p >= P_WET] = S_["WATER"]; st[(p <= P_DRY) & ~rec] = S_["DRY"]
        model = st != S_["UNKNOWN"]
        weakm = (fl & (FL["STORAGE_SENSITIVE"] | FL["WEAK_CONNECTIVITY"] | FL["RECESSION_UNCERTAIN"])) > 0
        src[model & ~weakm] = SR["MODEL_STRONG"]; src[model & weakm] = SR["MODEL_WEAK"]
        r1 = noeo & (ref == 1); st[r1] = S_["WATER"]; src[r1] = SR["REFERENCE"]
        for code, s_, so in ((EO_S1_WATER, "WATER", "EO_S1"), (EO_S1_DRY, "DRY", "EO_S1"), (EO_S2_WATER, "WATER", "EO_S2"), (EO_S2_DRY, "DRY", "EO_S2")):
            m = e == code; st[m] = S_[s_]; src[m] = SR[so]
        # transitions of the pixels that were WATER (non-reference) and the EO-vs-model comparison on the EO-decided cells
        wetn = nonref & (st == S_["WATER"]); eod = ((src == SR["EO_S1"]) | (src == SR["EO_S2"])) & (st == S_["DRY"])
        eo_dry_since[wetn] = False; wet_once |= wetn; eo_dry_since |= wet_once & eod
        km = lambda m: round(float(m.sum()) * CK, 2)
        for gname, gv in GSPLIT:
            f = wet_once & (ground == gv)
            trows.append(dict(date=d, ground=gname, ever_water_km2=km(f), WATER_km2=km(f & wetn), DRY_EO_confirmed_km2=km(f & (st == S_["DRY"]) & eo_dry_since),
                              DRY_model_only_km2=km(f & (st == S_["DRY"]) & ~eo_dry_since), UNKNOWN_km2=km(f & (st == S_["UNKNOWN"])),
                              UNKNOWN_after_EO_dry_km2=km(f & (st == S_["UNKNOWN"]) & eo_dry_since)))
        for gname, gv in GSPLIT:
            ed = (ground == gv) & ~noeo
            if not ed.any():
                continue
            ew, edr = ed & (st == S_["WATER"]), ed & (st == S_["DRY"]); mw, md = p >= P_WET, p <= P_DRY; mu = ~mw & ~md
            vrows.append(dict(date=d, ground=gname, eo_decided_km2=km(ed), EO_WATER_km2=km(ew), EO_DRY_km2=km(edr), model_WATER_km2=km(ed & mw),
                              model_DRY_km2=km(ed & md), model_UNKNOWN_km2=km(ed & mu), both_WATER_km2=km(ew & mw), both_DRY_km2=km(edr & md),
                              EO_WATER_model_DRY_km2=km(ew & md), EO_DRY_model_WATER_km2=km(edr & mw), EO_WATER_model_UNKNOWN_km2=km(ew & mu),
                              EO_DRY_model_UNKNOWN_km2=km(edr & mu)))
        st[~dom] = OUTSIDE; src[~dom] = OUTSIDE; fl[~dom] = OUTSIDE; rf = np.where(dom, ref, OUTSIDE).astype("u1")
        with rasterio.open(OUT / f"state_{d}.tif", "w", **prof) as o:
            for b, (arr, nm_) in enumerate(((st, "state"), (src, "source"), (fl, "flags"), (rf, "reference")), 1):
                o.write(arr, b); o.set_band_description(b, nm_)
            o.update_tags(producer="p95x_weak_label_quality.py", date=d, states=json.dumps(STATE), sources=json.dumps(SOURCE), flags=json.dumps(FLAG),
                          reference=json.dumps({"none": 0, "optical_pre_breach_water": 1, "normally_wet_model_only": 2}), outside=str(OUTSIDE),
                          p_water=pfile, s1_scenes=",".join(eo_src[d]["s1_scenes"]) or "none", s2_frames=",".join(eo_src[d]["s2_frames"]) or "none")
        # the nearest EO state before the next day, and the event attributes (WATER on non-reference ground)
        prev[(e == EO_S1_WATER) | (e == EO_S2_WATER)] = 1; prev[(e == EO_S1_DRY) | (e == EO_S2_DRY)] = 2
        wet = (st == S_["WATER"]) & (ref == 0) & dom; dry = (st == S_["DRY"]) & dom
        first_wet[wet & (first_wet == NEVER)] = k; last_wet[wet] = k; n_wet[wet] += 1; first_dry[wet] = NEVER
        first_dry[dry & (last_wet != NEVER) & (first_dry == NEVER)] = k
        # summary
        r = dict(date=d, p_water=pfile, s1_scenes=",".join(eo_src[d]["s1_scenes"]) or "none", s2_frames=",".join(eo_src[d]["s2_frames"]) or "none",
                 eo_observed_km2=round(float((dom & ~noeo).sum()) * CK, 1))
        for sn, sv in STATE.items():
            r[f"{sn}_km2"] = round(float((st == sv).sum()) * CK, 1)
        r["WATER_non_reference_km2"] = round(float(wet.sum()) * CK, 1)
        for so, sv in SOURCE.items():
            r[f"WATER_{so}_km2"] = round(float(((st == S_["WATER"]) & (src == sv)).sum()) * CK, 1)
            r[f"WATER_nonref_{so}_km2"] = round(float((wet & (src == sv)).sum()) * CK, 1)
            r[f"WATER_dry_{so}_km2"] = round(float(((st == S_["WATER"]) & (ground == GROUND["DRY_BEFORE_EVENT"]) & (src == sv)).sum()) * CK, 1)
        r["DRY_MODEL_km2"] = round(float(((st == S_["DRY"]) & ((src == SR["MODEL_STRONG"]) | (src == SR["MODEL_WEAK"]))).sum()) * CK, 1)
        r["UNKNOWN_ambiguous_P_km2"] = round(float(((st == S_["UNKNOWN"]) & ~rec).sum()) * CK, 1)
        r["UNKNOWN_nonref_km2"] = round(float(((st == S_["UNKNOWN"]) & (ref == 0) & dom).sum()) * CK, 1)
        for gname, gv in GSPLIT:
            r[f"WATER_{gname.replace(' ', '_').replace('-', '_')}_km2"] = round(float(((st == S_["WATER"]) & (ground == gv)).sum()) * CK, 1)
            r[f"UNKNOWN_{gname.replace(' ', '_').replace('-', '_')}_km2"] = round(float(((st == S_["UNKNOWN"]) & (ground == gv)).sum()) * CK, 1)
        r["UNKNOWN_normally_wet_ref_km2"] = round(float(((st == S_["UNKNOWN"]) & (ref == 2) & dom).sum()) * CK, 1)
        r["UNKNOWN_recession_km2"] = round(float(((st == S_["UNKNOWN"]) & rec).sum()) * CK, 1)
        for fn, fv in FLAG.items():
            r[f"flag_{fn}_km2"] = round(float((dom & ((fl & fv) > 0)).sum()) * CK, 1)
        rows.append(r)
        if d in U:
            u = U[d]; ob, un = u["ob"], u["water"]; wS, dS, uS = st == S_["WATER"], st == S_["DRY"], st == S_["UNKNOWN"]
            groups = [("all", ob), ("no own EO that day", ob & noeo), ("open ground, no own EO", ob & noeo & open_g),
                      ("source MODEL_STRONG", ob & (src == SR["MODEL_STRONG"])), ("source MODEL_WEAK", ob & (src == SR["MODEL_WEAK"])),
                      ("source EO (S1 or S2)", ob & ((src == SR["EO_S1"]) | (src == SR["EO_S2"])))]
            groups += [(f"flag {fn}", ob & ((fl & fv) > 0)) for fn, fv in FLAG.items()]
            groups += [(f"ground {gname}", ob & (ground == gv)) for gname, gv in GSPLIT] + [(f"ground {gname}, no own EO", ob & noeo & (ground == gv)) for gname, gv in GSPLIT]
            for gname, sel in groups:
                if not sel.any():
                    continue
                tp = float((sel & wS & un).sum()); fp = float((sel & wS & ~un).sum()); fn_ = float((sel & dS & un).sum()); tn = float((sel & dS & ~un).sum())
                crows.append(dict(date=d, unosat=u["key"], sensor=u["sensor"], group=gname, km2=round(float(sel.sum()) * CK, 1),
                                  decided_share=round((tp + fp + fn_ + tn) / float(sel.sum()), 3), UNKNOWN_share=round(float((sel & uS).sum() / sel.sum()), 3),
                                  accuracy=round((tp + tn) / max(tp + fp + fn_ + tn, 1), 3), POD=round(tp / (tp + fn_), 3) if tp + fn_ else np.nan,
                                  FAR=round(fp / (tp + fp), 3) if tp + fp else np.nan, CSI=round(tp / (tp + fp + fn_), 3) if tp + fp + fn_ else np.nan,
                                  unosat_water_km2=round(float((sel & un).sum()) * CK, 1), unosat_water_in_UNKNOWN_share=round(float((sel & un & uS).sum() / max((sel & un).sum(), 1)), 3)))
        print(f"  {d}: EO {r['eo_observed_km2']} | WATER {r['WATER_km2']} (non-reference {r['WATER_non_reference_km2']}) | DRY {r['DRY_km2']} | "
              f"UNKNOWN {r['UNKNOWN_km2']} (recession {r['UNKNOWN_recession_km2']})  ({round(time.time() - t0)} s)", flush=True)
    del eo, next_dry
    S = pd.DataFrame(rows); S.to_csv(TAB / "p95x_state_summary.csv", index=False)
    C = pd.DataFrame(crows); C.to_csv(TAB / "p95x_unosat_check.csv", index=False)
    TT = pd.DataFrame(trows); TT.to_csv(TAB / "p95x_transitions.csv", index=False); VV = pd.DataFrame(vrows); VV.to_csv(TAB / "p95x_eo_vs_model.csv", index=False)
    ev = dict(first_wet_day=first_wet, last_wet_day=last_wet, n_wet_days=n_wet, first_dry_day=first_dry)
    with rasterio.open(OUT / "event_attributes.tif", "w", **dict(prof, count=len(ev), nodata=None)) as o:
        for b, (nm_, arr) in enumerate(ev.items(), 1):
            o.write(arr, b); o.set_band_description(b, nm_)
        o.update_tags(producer="p95x_weak_label_quality.py", day_zero=DAY0, never=str(NEVER), meaning="WATER on non-reference ground; first_dry_day = the first DRY after the last WATER")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(C.drop(columns=["sensor"]).to_string(index=False))
    (TAB / "p95x_manifest.json").write_text(json.dumps(dict(
        producer="p95x_weak_label_quality.py", decision="maintainer 2026-09-30: best state estimate + source + quality flags; UNKNOWN only for 0.05 < P < 0.8 and the recession between EO anchors",
        days=days, states=STATE, sources=SOURCE, flags=FLAG, thresholds=dict(P_water_wet=P_WET, P_water_dry=P_DRY), p_water=pfiles, eo=eo_src,
        reference_km2=dict(optical=round(float((ref == 1).sum()) * CK, 1), model_only_normally_wet=round(float((ref == 2).sum()) * CK, 1)), ground_classes=GROUND, ground_km2=gkm,
        storage_sensitive=dict(km2=round(float(storage.sum()) * CK, 1), depressions=int(dep.storage_sensitive.sum()), lowland_south_of_krynky_included=bool(keep[lowland])),
        p95_rev=man.get("rev"), unosat="check only, never a label source"), indent=1, default=str))
    if not a.no_figure:
        figures(S, TT, OUT, FIG, storage, dom, tr, shp, crs, U, tf_transform)
    print("->", OUT, TAB / "p95x_state_summary.csv", round(time.time() - t0), "s")


def figures(S, TT, OUT, FIG, storage, dom, tr, shp, crs, U, tf_transform):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    import rasterio
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    # display: 0 DRY, 1 WATER (new ground), 2 UNKNOWN, 3 WATER on reference ground, 4 outside the domain
    cols = ["#efe6d2", "#2a78d6", "#e34948", "#16324f", "#d9d9d9"]; cmap = ListedColormap(cols)
    leg = [Patch(fc=cols[0], ec="k", lw=0.3, label="DRY"), Patch(fc=cols[1], ec="k", lw=0.3, label="WATER"), Patch(fc=cols[3], ec="k", lw=0.3, label="WATER, reference ground"),
           Patch(fc=cols[2], ec="k", lw=0.3, label="UNKNOWN"), Patch(fc=cols[4], ec="k", lw=0.3, label="outside the domain")]

    def disp(stt, rf):
        o = np.where(stt == 255, 4, stt).astype("u1"); o[(stt == 1) & (rf > 0) & (rf < 255)] = 3
        return o
    FIG.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(2, 3, figsize=(18, 11), constrained_layout=True); axs = axs.ravel(); stp = 4
    ext = (tr.c / 1e3, (tr.c + shp[1] * tr.a) / 1e3, (tr.f + shp[0] * tr.e) / 1e3, tr.f / 1e3)
    for ax, d in zip(axs, ("2023-06-07", "2023-06-09", "2023-06-13", "2023-06-21")):
        with rasterio.open(OUT / f"state_{d}.tif") as s:
            st_ = s.read(1)[::stp, ::stp]; rf_ = s.read(4)[::stp, ::stp]
        ax.imshow(disp(st_, rf_), cmap=cmap, vmin=-0.5, vmax=4.5, extent=ext, interpolation="nearest")
        ax.set_title(f"{d}: state" + (f" (UNOSAT {U[d]['key']} used only for the check)" if d in U else ""), fontsize=8); ax.tick_params(labelsize=6)
    TT = TT[TT.ground == "dry-before-event ground"]; ax = axs[4]; tt = pd.to_datetime(TT.date)
    parts = [("WATER_km2", "still WATER", "#2a78d6"), ("DRY_EO_confirmed_km2", "DRY, confirmed by EO since its last WATER", "#1baf7a"),
             ("DRY_model_only_km2", "DRY by the model only", "#c8b89a"), ("UNKNOWN_km2", "UNKNOWN", "#e34948")]
    ax.stackplot(tt, *[TT[c_] for c_, _l, _c in parts], labels=[l_ for _c, l_, _x in parts], colors=[x_ for _c, _l, x_ in parts], alpha=0.9)
    ax.legend(fontsize=6, loc="upper right"); ax.grid(alpha=0.3); ax.tick_params(labelsize=6)
    ax.set_title("dry-before-event ground: pixels that were WATER at least once, their state per day, km2", fontsize=8)
    ax = axs[5]; tt = pd.to_datetime(S.date); eo_day = (S.s1_scenes != "none") | (S.s2_frames != "none")
    ax.plot(tt, S.WATER_dry_before_event_ground_km2, color="#2a78d6", lw=1.6, label="WATER, dry-before-event ground")
    ax.plot(tt, S.WATER_vegetated_wetland_km2, color="#8e44ad", lw=1.6, label="WATER, vegetated wetland (reed complex)")
    ax.plot(tt, S.WATER_dry_MODEL_STRONG_km2, color="#2a78d6", lw=1, ls="--", label="dry ground: of which MODEL_STRONG")
    ax.plot(tt, S.WATER_dry_MODEL_WEAK_km2, color="#eb6834", lw=1, ls="--", label="dry ground: of which MODEL_WEAK")
    ax.plot(tt[eo_day], (S.WATER_dry_EO_S1_km2 + S.WATER_dry_EO_S2_km2)[eo_day], "o", ms=4, mfc="white", color="#16324f", label="dry ground: of which same-day EO")
    ax.plot(tt, S.UNKNOWN_dry_before_event_ground_km2, color="#e34948", lw=1.6, label="UNKNOWN, dry-before-event ground")
    ax.plot(tt, S.UNKNOWN_vegetated_wetland_km2, color="#e34948", lw=1, ls=":", label="UNKNOWN, vegetated wetland")
    ax.legend(fontsize=6); ax.grid(alpha=0.3); ax.set_ylim(bottom=0); ax.tick_params(labelsize=6)
    ax.set_title("area per day inside the reconstruction domain, km2 (curves on the same ground)", fontsize=8)
    fig.legend(handles=leg, loc="lower center", ncol=5, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.03))
    fig.suptitle("P95x daily state mask: same-day EO where observed, the ensemble P(water) where not (WATER >= 0.8, DRY <= 0.05), UNKNOWN in between; flags are metadata", fontsize=9)
    fig.savefig(FIG / "p95x_state_mask.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    lo0, la0, lo1, la1 = KRYNKY_WINDOW; xs, ys = tf_transform("EPSG:4326", crs, [lo0, lo1], [la0, la1])
    c0 = max(int((min(xs) - tr.c) / tr.a), 0); c1 = min(int((max(xs) - tr.c) / tr.a) + 1, shp[1]); r0 = max(int((max(ys) - tr.f) / tr.e), 0); r1 = min(int((min(ys) - tr.f) / tr.e) + 1, shp[0])
    wext = ((tr.c + c0 * tr.a) / 1e3, (tr.c + c1 * tr.a) / 1e3, (tr.f + r1 * tr.e) / 1e3, (tr.f + r0 * tr.e) / 1e3); win = ((r0, r1), (c0, c1))
    fig, axs = plt.subplots(2, 3, figsize=(18, 10), constrained_layout=True); axs = axs.ravel()
    for ax, d in zip(axs, ("2023-06-07", "2023-06-08", "2023-06-09", "2023-06-13", "2023-06-18", "2023-06-21")):
        with rasterio.open(OUT / f"state_{d}.tif") as s:
            st_ = s.read(1, window=win); fl_ = s.read(3, window=win); rf_ = s.read(4, window=win)
        ax.imshow(disp(st_, rf_), cmap=cmap, vmin=-0.5, vmax=4.5, extent=wext, interpolation="nearest")
        ax.contour(storage[r0:r1, c0:c1].astype("f4"), levels=[0.5], colors="#7a0019", linewidths=0.8, extent=wext, origin="upper")
        wk = (fl_ != 255) & ((fl_ & 16) > 0)
        if wk.any():
            ax.contourf(wk.astype("f4"), levels=[0.5, 1.5], colors="none", hatches=["////"], extent=wext, origin="upper")
        if d in U:
            ax.contour(U[d]["water"][r0:r1, c0:c1].astype("f4"), levels=[0.5], colors="#ffd23f", linewidths=0.6, extent=wext, origin="upper")
        ax.set_title(f"{d}" + (f" -- yellow: UNOSAT {U[d]['key']} water (check only)" if d in U else ""), fontsize=8); ax.tick_params(labelsize=6)
    fig.legend(handles=leg + [Patch(fc="none", ec="#7a0019", label="STORAGE_SENSITIVE"), Patch(fc="none", ec="k", hatch="////", label="RECESSION_UNCERTAIN")],
               loc="lower center", ncol=7, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.03))
    fig.suptitle("P95x state mask around Kozachi Laheri, Krynky and the lowland south of Krynky (UTM 36N km)", fontsize=9)
    fig.savefig(FIG / "p95x_state_mask_krynky.png", dpi=120, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    main()
