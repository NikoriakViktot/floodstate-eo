# New in floodstate-eo, 2026-09-28. STATUS: ACTIVE. Reservoir drawdown maps: modelled pool, Sentinel-1 water, Sentinel-2 classes/indices.
"""P95h -- maps of the Kakhovka pool emptying, day by day, from three independent sources on their own grids.

  MODEL  the p95f sloped daily surface over the 50 m seamless DEM inside the pre-breach pool polygon (terrain-reconstructed,
         2023-05-26 .. 06-13; after 13 June the pool is a river and has no pool surface). Wet = DEM below the surface.
         Day of exposure = the first day after the breach on which a cell wet on 06-05 is dry.
  S1     VH backscatter (s1_zone_cache/ZONE_1_reservoir_corrected, 20 m, SWOT-DNIPRO hist25b grid): water = VH dB below a
         per-date Otsu threshold over ALL covered cells (pool + surrounding land; clamped to [-24, -15] dB), 3x3 majority.
         VH, not VV: wind-roughened open water in VV (median -17.7 dB on 06-01) overlaps land, and an Otsu inside the pool
         alone splits the water mode (IoU vs model 0.61 with VV-in-pool, 0.98 with VH-all). Dark = open water OR smooth
         wet mud, so S1 can exceed the model on exposed flats. Not covered = NOT OBSERVED, never dry. Scenes observing
         < 10 % of the pool (orbit 87 edge strips) are tabulated but not mapped.
  S2     the frozen SWOT-DNIPRO p25 products on the ZONE_1 20 m grid (zone_spectral/ZONE_1_KAKHOVKA_LOWER_DNIPRO: 7 indices,
         k10e class, water3 = NDWI>0 & MNDWI>0 & SCL-permitted) plus the p15 ZONE_1_s2_crosscheck water masks for the
         drawdown week. Nothing is re-classified here; the classed index bins below are for display only.

Semantics: model areas are terrain_reconstructed, S1/S2 areas are observed_S1 / observed_S2 inside the pool polygon; areas
count observed cells only and carry the observed fraction. The reservoir remains context in Paper 3 (Paper 4 decision).

Tables for every 2023 S2 date observing >= 50 % of the pool, per stratum (POOL; EXPOSED_BY_0613 / WET_ON_0613 from the modelled
day of exposure): k10e class areas and shares, the 7 index statistics (mean, std, p10..p90) and index display-class areas.

Outputs: <case_study>/tables/p95h_reservoir_maps.csv, p95h_s2_classes.csv, p95h_s2_index_stats.csv, p95h_s2_index_classes.csv,
         p95h_manifest.json
         $BULK/reservoir_maps/model/{wet_daily.npz, exposed_day.tif}, $BULK/reservoir_maps/s1/<date>.npz (water, observed)
"""
from __future__ import annotations
import importlib.util, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from affine import Affine
from rasterio import features
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from scipy import ndimage
from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


P95F = _ld("p95f", HERE / "p95f_reservoir_balance.py")
OUT = CFG.BULK_ROOT / "reservoir_maps"
S1DIR = CFG.S1_CACHE / "ZONE_1_reservoir_corrected"
S2DIR = CFG.BULK_ROOT / "zone_spectral" / "ZONE_1_KAKHOVKA_LOWER_DNIPRO"
S2XC = CFG.BULK_ROOT / "ZONE_1_s2_crosscheck"
SD_SRC = Path(CFG._SWOT_DNIPRO_SIBLING) / "src"
CRS_UTM = "EPSG:32636"
MODEL_DATES = pd.date_range("2023-05-26", "2023-06-13", freq="D")
REF_DAY = pd.Timestamp("2023-06-05")                           # last full-pool day
S1_CELL = 20.0
S1_CLAMP_DB = (-24.0, -15.0)
S1_MIN_OBS = 0.10                                              # map a scene only if it observes >= 10 % of the pool
S2_DATES = ["2023-05-06", "2023-06-05", "2023-07-05", "2023-08-17", "2023-09-08"]   # >= 50 % of the pool observed (06-30, 07-25, 08-27: < 7 %)
S2_TABLE_MIN_OBS = 0.50                                        # class / index tables: every 2023 p25 date observing >= 50 % of the pool
S2XC_DATES =["2023-06-08", "2023-06-13", "2023-06-15", "2023-06-20"]
INDEX_NAMES = ("NDVI", "NDWI", "MNDWI", "NDMI", "BSI", "AWEIsh", "NDTI")
_WATER_RAMP = ["#8c6d31", "#d9c58b", "#9cc0ea", "#1b6ca8"]
_TRI_RAMP = ["#c7522a", "#f2efe6", "#2a78d6"]
INDEX_BINS = {                                                 # display classes only: edges (inner), labels, colours
    "NDWI":   ([-0.3, 0.0, 0.3], ["< −0.3", "−0.3–0", "0–0.3", "> 0.3"], _WATER_RAMP),
    "MNDWI":  ([-0.3, 0.0, 0.3], ["< −0.3", "−0.3–0", "0–0.3", "> 0.3"], _WATER_RAMP),
    "AWEIsh": ([-0.3, 0.0, 0.3], ["< −0.3", "−0.3–0", "0–0.3", "> 0.3"], _WATER_RAMP),
    "NDVI":   ([0.15, 0.3, 0.5], ["< 0.15", "0.15–0.3", "0.3–0.5", "> 0.5"], ["#e8d8a0", "#b8d98d", "#4c9a2a", "#1e6f3f"]),
    "NDMI":   ([-0.1, 0.1], ["< −0.1", "−0.1–0.1", "> 0.1"], _TRI_RAMP),
    "BSI":    ([-0.1, 0.1], ["< −0.1", "−0.1–0.1", "> 0.1"], ["#2a78d6", "#f2efe6", "#c7522a"]),
    "NDTI":   ([-0.1, 0.1], ["< −0.1", "−0.1–0.1", "> 0.1"], ["#2a78d6", "#f2efe6", "#8c6d31"]),
}
K10E = {1: ("OPEN_WATER", "#1b6ca8"), 2: ("SHALLOW_OR_MIXED_WATER", "#7fb3d5"), 3: ("WET_SEDIMENT", "#8c6d31"), 4: ("DRY_BARE_SEDIMENT", "#d9c58b"),
        5: ("SPARSE_HERBACEOUS", "#b8d98d"), 6: ("DENSE_HERBACEOUS", "#4c9a2a"), 7: ("REED_OR_FLOODED_VEGETATION", "#1e6f3f"),
        8: ("BUILT_HARD_SURFACE", "#7d7d7d"), 9: ("AMBIGUOUS", "#e08214")}          # SWOT-DNIPRO plotting/maps.CLASS_COLORS


def classify_index(v, name):
    """float index (NaN = not observed) -> uint8 display class 1..n, 0 = not observed."""
    edges = INDEX_BINS[name][0]; c = (np.digitize(v, edges) + 1).astype("u1"); c[~np.isfinite(v)] = 0
    return c


def s1_grid():
    """The hist25b gate-6 grid of the S1 reservoir cache: reservoir core U former-reservoir transition, 20 m."""
    sys.path.insert(0, str(SD_SRC))
    from swot_dnipro import spatial_domains as SD
    from shapely.ops import unary_union
    fp = unary_union([SD.load_subzone_utm("KAKHOVKA_RESERVOIR_CORE"), SD.load_subzone_utm("FORMER_RESERVOIR_TRANSITION")])
    x0, y0 = np.floor(fp.bounds[0] / S1_CELL) * S1_CELL, np.floor(fp.bounds[1] / S1_CELL) * S1_CELL
    x1, y1 = np.ceil(fp.bounds[2] / S1_CELL) * S1_CELL, np.ceil(fp.bounds[3] / S1_CELL) * S1_CELL
    return from_origin(x0, y1, S1_CELL, S1_CELL), (int((y1 - y0) / S1_CELL), int((x1 - x0) / S1_CELL))


def s2_grid():
    with rasterio.open(S2DIR / f"{S2_DATES[1]}_class.tif") as s:
        return s.transform, (s.height, s.width)


def xc_transform(tr):
    """p15 wrote the crosscheck masks on from_origin(gx[0], gy[-1]) (cell centres) -- half a cell from the p25 tifs."""
    return tr * Affine.translation(0.5, -0.5)


def pool_on(tr, shape):
    return features.rasterize([(CFG.load_utm("reservoir_full_pool_prebreach").__geo_interface__, 1)], out_shape=shape, transform=tr, fill=0, dtype="uint8").astype(bool)


def s1_dates():
    out = {}
    for p in sorted(S1DIR.glob("2023-0[5-7]-*_orb*.npz")):
        out.setdefault(p.name[:10], []).append(p)
    return out


def otsu(x, lo=-30.0, hi=5.0, step=0.1):
    h, e = np.histogram(x, bins=np.arange(lo, hi + step, step)); c = 0.5 * (e[1:] + e[:-1]); w = h.astype("f8")
    w0 = np.cumsum(w); w1 = w0[-1] - w0; m0 = np.cumsum(w * c) / np.maximum(w0, 1); m1 = (np.sum(w * c) - np.cumsum(w * c)) / np.maximum(w1, 1)
    return float(c[np.argmax(w0 * w1 * (m0 - m1) ** 2)])


def s1_water(paths):
    """Union over same-day orbits; returns water, observed (bool), VH threshold dB."""
    vh = None
    for p in paths:
        z = np.load(p); a = z["vh"]; cov = z["cov"]
        if vh is None:
            vh = np.where(cov, a, np.nan).astype("f4")
        else:
            new = cov & ~np.isfinite(vh); vh[new] = a[new]
    obs = np.isfinite(vh) & (vh > 0)
    db = np.full(vh.shape, np.nan, "f4"); db[obs] = 10 * np.log10(vh[obs])
    thr = float(np.clip(otsu(db[obs][::5]), *S1_CLAMP_DB))
    w = obs & (db < thr); w = ndimage.uniform_filter(w.astype("f4"), 3) > 0.5; w &= obs
    return w, obs, thr


def model_maps():
    daily, extra, fixed = P95F.load_levels(); dem, mask, tr, crs, xs, ys = P95F.load_pool(); chain = P95F.chainage_grid(xs, ys)
    wet = {}
    for d in MODEL_DATES:
        pts = P95F.day_points(d, daily, extra, fixed)
        if len(pts) >= 2:
            wet[str(d.date())] = mask & (dem < P95F.sloped_wse(pts, chain))
    ref = wet[str(REF_DAY.date())]; exp = np.where(ref, 255, 0).astype("u1")
    for k in sorted(wet):
        if pd.Timestamp(k) > REF_DAY:
            first = ref & ~wet[k] & (exp == 255); exp[first] = pd.Timestamp(k).day
    return wet, exp, mask, tr, crs


def to_grid(a, src_tr, dst_tr, shape, fill=0):
    d = np.full(shape, fill, "u1")
    reproject(a.astype("u1"), d, src_transform=src_tr, src_crs=CRS_UTM, dst_transform=dst_tr, dst_crs=CRS_UTM, resampling=Resampling.nearest)
    return d


def main():
    t0 = time.time(); (OUT / "model").mkdir(parents=True, exist_ok=True); (OUT / "s1").mkdir(parents=True, exist_ok=True)
    wet, exp, mask, mtr, mcrs = model_maps(); cell_m = abs(mtr.a * mtr.e) / 1e6
    np.savez_compressed(OUT / "model" / "wet_daily.npz", shape=np.array(mask.shape), transform=np.array(mtr)[:6], pool=np.packbits(mask),
                        **{k: np.packbits(v) for k, v in wet.items()})
    with rasterio.open(OUT / "model" / "exposed_day.tif", "w", driver="GTiff", height=exp.shape[0], width=exp.shape[1], count=1, dtype="uint8", crs=mcrs, transform=mtr,
                       compress="deflate", nodata=0) as s:
        s.write(exp, 1); s.update_tags(values="day of June 2023 on which a cell wet on 06-05 is first dry under the p95f surface; 255 = still wet on 06-13; 0 = dry on 06-05 or outside the pool")
    p95f = pd.read_csv(CFG.TABLES / "p95f_reservoir_daily.csv").set_index("date").A_pool_km2
    rows = []
    for k, v in wet.items():
        a = round(float(v.sum()) * cell_m, 1); assert abs(a - p95f.get(k, a)) <= 0.1, (k, a, p95f.get(k))
        rows.append(dict(date=k, source="MODEL", semantics="terrain_reconstructed", water_km2=a, observed_frac=1.0))
    yi = pd.read_csv(Path(CFG._SWOT_DNIPRO_SIBLING) / "outputs/tables/p61_yi2025_reservoir_area.csv")
    yi = dict(zip((pd.Timestamp("2023-06-06") + pd.to_timedelta(yi.day_after_breach, unit="D")).dt.strftime("%Y-%m-%d"), yi.area_km2_S1))
    # ---- S1 ----
    str_, sshape = s1_grid(); spool = pool_on(str_, sshape); s1km = S1_CELL ** 2 / 1e6; thr_s1 = {}
    for d, paths in s1_dates().items():
        with np.load(paths[0]) as z:
            assert z["vv"].shape == sshape, f"S1 cache {paths[0].name} on {z['vv'].shape}, grid is {sshape}: grid mismatch, abort"
        w, obs, thr = s1_water(paths); thr_s1[d] = thr
        np.savez_compressed(OUT / "s1" / f"{d}.npz", water=np.packbits(w), observed=np.packbits(obs), shape=np.array(sshape), transform=np.array(str_)[:6], threshold_db=thr)
        o = obs & spool; r = dict(date=d, source="S1", semantics="observed_S1", water_km2=round(float((w & spool).sum()) * s1km, 1), observed_frac=round(float(o.sum()) / spool.sum(), 3),
                                  vh_threshold_db=round(thr, 2), mapped=bool(o.sum() >= S1_MIN_OBS * spool.sum()), orbits="|".join(p.name[11:-4] for p in paths))
        if d in wet:
            m = to_grid(wet[d], mtr, str_, sshape).astype(bool); u = (m | w) & o
            r["iou_vs_model"] = round(float((m & w & o).sum()) / max(int(u.sum()), 1), 3); r["model_km2_on_observed"] = round(float((m & o).sum()) * s1km, 1)
        rows.append(r); print("S1", d, r, flush=True)
    # ---- S2 ----
    ztr, zshape = s2_grid(); zpool = pool_on(ztr, zshape); zkm = 20.0 ** 2 / 1e6; crows, irows, krows = [], [], []
    mref = to_grid(wet[str(REF_DAY.date())], mtr, ztr, zshape).astype(bool)
    ez = to_grid(exp, mtr, ztr, zshape)                                     # strata on the S2 grid from the modelled day of exposure
    strata = {"POOL": zpool, "EXPOSED_BY_0613": zpool & (ez >= 6) & (ez <= 13), "WET_ON_0613": zpool & (ez == 255)}
    for d in sorted(p.name[:10] for p in S2DIR.glob("2023-*_class.tif")):
        with rasterio.open(S2DIR / f"{d}_class.tif") as s:
            cl = s.read(1); regime = s.tags().get("regime", "")
        with rasterio.open(S2DIR / f"{d}_water3.tif") as s:
            w3 = s.read(1)
        obs = (w3 != 255) & zpool; w = (w3 == 1) & zpool
        r = dict(date=d, source="S2_WATER3", semantics="observed_S2", water_km2=round(float(w.sum()) * zkm, 1), observed_frac=round(float(obs.sum()) / zpool.sum(), 3), regime=regime,
                 mapped=d in S2_DATES)
        if d == str(REF_DAY.date()):
            u = (mref | w) & obs; r["iou_vs_model"] = round(float((mref & w).sum()) / max(int(u.sum()), 1), 3); r["model_km2_on_observed"] = round(float((mref & obs).sum()) * zkm, 1)
        rows.append(r); print("S2", d, r["observed_frac"], r["water_km2"], flush=True)
        if r["observed_frac"] < S2_TABLE_MIN_OBS:
            continue
        for sn, sm in strata.items():                                        # k10e classes per stratum (observed cells only)
            o = (cl > 0) & sm; no = int(o.sum())
            crows.append(dict(date=d, regime=regime, stratum=sn, stratum_km2=round(float(sm.sum()) * zkm, 1), observed_km2=round(no * zkm, 1), observed_frac=round(no / max(int(sm.sum()), 1), 3),
                              **{f"{K10E[k][0]}_km2": round(float(((cl == k) & sm).sum()) * zkm, 1) for k in K10E},
                              **{f"{K10E[k][0]}_pct": round(100 * float(((cl == k) & sm).sum()) / max(no, 1), 1) for k in K10E}))
        with rasterio.open(S2DIR / f"{d}_indices.tif") as s:
            for i, nm in enumerate(INDEX_NAMES, 1):
                v = s.read(i).astype("f4"); v[v == -32768] = np.nan; v /= 1e4
                for sn, sm in strata.items():
                    x = v[sm]; x = x[np.isfinite(x)]
                    if x.size == 0:
                        continue
                    q = np.percentile(x, [10, 25, 50, 75, 90])
                    irows.append(dict(date=d, regime=regime, stratum=sn, index=nm, observed_km2=round(x.size * zkm, 1), observed_frac=round(x.size / max(int(sm.sum()), 1), 3),
                                      mean=round(float(x.mean()), 4), std=round(float(x.std()), 4), p10=round(q[0], 4), p25=round(q[1], 4), p50=round(q[2], 4), p75=round(q[3], 4), p90=round(q[4], 4)))
                    edges, labels, _ = INDEX_BINS[nm]; k = np.digitize(x, edges)
                    for j, lab in enumerate(labels):
                        n = int((k == j).sum()); krows.append(dict(date=d, regime=regime, stratum=sn, index=nm, index_class=lab, km2=round(n * zkm, 1), pct_of_observed=round(100 * n / x.size, 1)))
        print("S2 tables", d, flush=True)
    xtr = xc_transform(ztr)
    for d in S2XC_DATES:
        z = np.load(S2XC / f"{d}.npz"); shp = tuple(int(v) for v in z["shape"]); assert shp == zshape, (d, shp, zshape)
        un = lambda k: np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
        w, v = un("water"), un("valid")
        w = to_grid(w, xtr, ztr, zshape).astype(bool) & zpool; v = to_grid(v, xtr, ztr, zshape).astype(bool) & zpool
        rows.append(dict(date=d, source="S2_CROSSCHECK", semantics="observed_S2", water_km2=round(float(w.sum()) * zkm, 1), observed_frac=round(float(v.sum()) / zpool.sum(), 3)))
        print("S2xc", d, rows[-1], flush=True)
    R = pd.DataFrame(rows); R["yi2025_S1_km2"] = R.date.map(yi); R = R.sort_values(["date", "source"])
    R.to_csv(CFG.TABLES / "p95h_reservoir_maps.csv", index=False); pd.DataFrame(crows).to_csv(CFG.TABLES / "p95h_s2_classes.csv", index=False)
    pd.DataFrame(irows).to_csv(CFG.TABLES / "p95h_s2_index_stats.csv", index=False); pd.DataFrame(krows).to_csv(CFG.TABLES / "p95h_s2_index_classes.csv", index=False)
    man = dict(sources=dict(model="p95f sloped daily surface (load_levels/load_pool/day_points/sloped_wse), dem_seamless_evrf2019_50m.tif", s1=str(S1DIR), s2=str(S2DIR), s2_crosscheck=str(S2XC),
                            pool="reservoir_full_pool_prebreach (Kakhovka_SA_2.geojson)", yi2025="SWOT-DNIPRO outputs/tables/p61_yi2025_reservoir_area.csv (VERIFY)"),
               s1_method=f"VH dB < per-date Otsu over all covered cells, clamped to {list(S1_CLAMP_DB)} dB, 3x3 majority; uncovered = not observed; dark = open water or smooth wet mud; mapped if >= {S1_MIN_OBS:.0%} of the pool observed", s1_thresholds_db=thr_s1,
               s2_method="frozen SWOT-DNIPRO p25 k10e class and water3 (NDWI>0 & MNDWI>0 & SCL-permitted); p15 crosscheck water for the drawdown week; no re-classification",
               index_display_bins={k: dict(edges=v[0], labels=v[1]) for k, v in INDEX_BINS.items()}, s2_table_min_observed_frac=S2_TABLE_MIN_OBS,
               strata=dict(POOL="pre-breach pool polygon", EXPOSED_BY_0613="model: wet on 06-05, dry by 06-13 (exposed_day 6..13)", WET_ON_0613="model: still wet on 06-13"), ref_day=str(REF_DAY.date()), pool_cells_model=int(mask.sum()),
               pool_km2_s1_grid=round(float(spool.sum()) * s1km, 1), pool_km2_s2_grid=round(float(zpool.sum()) * zkm, 1), seconds=round(time.time() - t0))
    (CFG.TABLES / "p95h_manifest.json").write_text(json.dumps(man, indent=1))
    pd.set_option("display.width", 250); print(R.to_string(index=False)); print(pd.DataFrame(crows).to_string(index=False)); print("->", OUT, "tables/p95h_*", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
