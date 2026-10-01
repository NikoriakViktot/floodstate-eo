# New in floodstate-eo, 2026-10-01 (maintainer: "the full picture of the delta in every index -- does water show through the vegetation?";
# extended the same day to the floodway reed beds upstream of Kherson: "where does the seasonal baseline evidence come from?").
# STATUS: ACTIVE. Diagnostic, nothing is fitted.
"""P95z -- every optical index and the C-band backscatter of the reed beds by surface stratum and date, in the Kherson delta and in the
floodway between the dam and Kherson: does water show through the vegetation of the ground the reconstruction calls normally wet
(model-only baseline), before, during and after the breach? This is the seasonal evidence for the pre-event ground class VEGETATED_WETLAND
of p95x -- stratum-level evidence, not a per-cell map of water under the canopy on any day.

Strata (cells of the zone inside the reconstruction domain, 20 m union grid, mapped onto each sensor grid):
  NW_REEDS      model-only normally wet, WorldCover herbaceous wetland (reeds)
  NW_TREES      model-only normally wet, tree cover (floodplain forest)
  HIGH_REEDS    reeds outside the baseline, > 0.5 m above the pre-breach surface and not reached on 7 June (P(water) < 0.05): dry-footed
  OPEN_WATER    optical pre-breach water (p60 pre_water_frac >= 20 %)
  EVENT_REEDS   reeds outside the baseline that the ensemble floods on 7 June (P(water) >= 0.8): wetted by the event only
  DRY_LAND      grass / cropland > 2 m above the 8 June surface (never reached)
Sentinel-2: the seven p54a indices (10 m; NDVI, NDWI, MNDWI, NDMI, BSI, AWEIsh, NDTI = (B04 - B03)/(B04 + B03), a turbidity index) of the
  zone's frame, every stacked date February 2022 - November 2023. The delta (frame B2) has no optical scene between 5 March and 5 June
  2023; the floodway (frame B1, west of 538 km) has five in May - 5 June 2023, the last on the day before the breach. 13 June 2022 gives
  the same season of a normal year in both. Water under a canopy raises MNDWI, NDWI and AWEIsh and lowers the SWIR; a wet canopy raises NDMI.
Sentinel-1: VV, VH (dB) and VV - VH of the zone caches, 15 April - 30 June 2023 (17 / 21 spring scenes before the breach in the delta /
  floodway). Emergent vegetation standing in water brightens VV by the double bounce (VV - VH rises); open water is dark in both.
Outputs: tables/p95z_strata_indices.csv (zone, date, sensor, index, stratum: p25 / median / p75); tables/p95z_strata_summary.csv (the
windows the manuscript quotes, T12i); tables/p95z_seasonal_baseline.csv (the compact seasonal evidence per zone and stratum, T12j);
`--summary-only` rebuilds the last two and the figures from the first; figures/m6_v003A/p95z_<zone>_indices.png
"""
from __future__ import annotations

import argparse
import importlib.util
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SFX = "_connected_ceiling"
STRATA = {1: "NW_REEDS", 2: "NW_TREES", 3: "HIGH_REEDS", 4: "OPEN_WATER", 5: "EVENT_REEDS", 6: "DRY_LAND"}
COLOR = {"NW_REEDS": "#8e44ad", "NW_TREES": "#2e8b57", "HIGH_REEDS": "#eb6834", "OPEN_WATER": "#16324f", "EVENT_REEDS": "#2a78d6", "DRY_LAND": "#c8b89a"}
INDICES = ("NDVI", "NDWI", "MNDWI", "NDMI", "BSI", "AWEIsh", "NDTI")
# zone -> (owned zone, Sentinel-2 frame, Sentinel-1 caches: spring before the breach, June 2023)
ZONES = {"delta": ("ZONE_2_KHERSON_DELTA", "B2", ("ZONE_2_KHERSON_DELTA_flood_june2023_pre2023", "ZONE_2_KHERSON_DELTA_flood_june2023")),
         "floodway": ("ZONE_4_DAM_TO_KHERSON_FLOODWAY", "B1", ("ZONE_4_FLOODWAY_june2023_s32_pre2023", "ZONE_4_FLOODWAY_june2023_s32"))}
BREACH = "2023-06-06"
# the windows the manuscript quotes (T12i); last_pre_breach = the zone's last optical scene before the breach (found per zone)
WINDOWS = (("normal_year", "S2", "2022-06-13", "2022-06-13"), ("spring_2023_S2", "S2", "2023-04-15", "2023-06-05"),
           ("spring_2023_S1", "S1", "2023-04-15", "2023-06-05"), ("peak", "S2", "2023-06-08", "2023-06-08"),
           ("recession", "S2", "2023-06-18", "2023-06-18"))
# the compact seasonal-evidence table (T12j): strata as pre-event classes, and the columns it quotes
BASELINE_ROWS = (("DRY_LAND", "dry ground: grass / cropland > 2 m above the 8 June surface", "dry before the event"),
                 ("HIGH_REEDS", "dry reeds: > 0.5 m above the pre-breach surface, not reached on 7 June", "vegetated wetland (WorldCover), outside the event"),
                 ("NW_REEDS", "seasonally wet reeds below the normal surface (model-only normal regime)", "vegetated wetland"),
                 ("EVENT_REEDS", "reeds reached only by the event (P(water) >= 0.8 on 7 June)", "vegetated wetland"),
                 ("OPEN_WATER", "open reference water (optical, >= 20 % of pre-breach scenes)", "open reference water"))
BASELINE_COLS = (("normal_year", "S2_jun2022", ("NDVI", "NDMI", "MNDWI")), ("last_pre_breach", "S2_last_pre", ("NDVI", "NDMI", "MNDWI")),
                 ("spring_2023_S1", "S1_spring2023", ("S1_VV_dB", "S1_VH_dB", "S1_VV_minus_VH_dB")))
TAB = ROOT / "tables"


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def summarize(D):
    """Per zone, window, index and stratum: the median of the scene medians, the scenes used and the median observed area; then the
    compact seasonal-evidence table."""
    import pandas as pd
    rows = []
    for zone, Dz in D.groupby("zone"):
        s2_pre = sorted(Dz[(Dz.sensor == "S2") & (Dz.date < BREACH)].date.unique())
        wins = list(WINDOWS) + [("last_pre_breach", "S2", s2_pre[-1], s2_pre[-1])]
        for win, sensor, d0, d1 in wins:
            x = Dz[Dz.sensor.str.startswith(sensor) & (Dz.date >= d0) & (Dz.date <= d1)]
            for (ix, st), g in x.groupby(["index", "stratum"]):
                rows.append(dict(zone=zone, window=win, sensor=sensor, index=ix, stratum=st, median=round(float(g["median"].median()), 3),
                                 n_scenes=int(g.date.nunique()), first=g.date.min(), last=g.date.max(), observed_km2=round(float(g.observed_km2.median()), 2)))
    S = pd.DataFrame(rows); S.to_csv(TAB / "p95z_strata_summary.csv", index=False)
    out = []
    for zone in S.zone.unique():
        for st, desc, gc in BASELINE_ROWS:
            r = dict(zone=zone, stratum=st, description=desc, pre_event_class=gc)
            sp = S[(S.zone == zone) & (S.window == "spring_2023_S1") & (S.stratum == st)]
            r["stratum_km2"] = float(sp.observed_km2.max()) if len(sp) else np.nan          # Sentinel-1 sees the whole zone
            for win, pre, ixs in BASELINE_COLS:
                for ix in ixs:
                    x = S[(S.zone == zone) & (S.window == win) & (S["index"] == ix) & (S.stratum == st)]
                    r[f"{pre}_{ix.replace('S1_', '')}"] = float(x["median"].iloc[0]) if len(x) else np.nan
                if win == "last_pre_breach":
                    x = S[(S.zone == zone) & (S.window == win)]
                    r["S2_last_pre_date"] = x["last"].iloc[0] if len(x) else ""
                    xs = S[(S.zone == zone) & (S.window == win) & (S.stratum == st)]
                    r["S2_last_pre_observed_km2"] = float(xs.observed_km2.max()) if len(xs) else 0.0
            r["S1_spring_scenes"] = int(sp.n_scenes.max()) if len(sp) else 0
            out.append(r)
    pd.DataFrame(out).to_csv(TAB / "p95z_seasonal_baseline.csv", index=False)
    return S


def strata_context(zones):
    """The reconstruction context on the 20 m union grid (rev-9 baseline, ensemble P(water) on 7 June) and, per zone, the domain cells
    of the zone and the strata code raster (STRATA; 0 = no stratum). Shared with p95zm (the classified index maps)."""
    import rasterio

    from floodstate_eo import _kakhovka_legacy_config as CFG
    O = _ld("p95o", HERE / "p95o_component_qa.py"); P95 = O._ld("p95_hand_daily_inundation")
    P = P95.load_p92(); man = O.load_manifest(SFX)
    if int(man.get("rev", 0)) < 9:
        raise SystemExit("p95z reads the rev-9 baseline")
    M = P95.mosaic_layers(P, with_s1=False); g = M["grid"]; tr = g.transform; shp = g.shape; crs = M["G"]["crs"]
    W_eng, dxm, _ = O.engine_for(P95, man, SFX); M["base"] = M["base_geom"] & P95.dam_mask(M, dxm); dom = M["base"]; Z = W_eng.prepare(M)
    B = O.compose_npz(M, SFX, "baseline"); nw = B & ~M["pre"]; opt = M["pre"] & B
    wc = g.compose({z: L["wc"] for z, L in M["zones"].items()}, 0, order=M["names"], dtype="u1")
    H_pre = np.asarray(W_eng.field(Z, P95.BASELINE_DATE, 0.0), "f4"); H_pk = np.asarray(W_eng.field(Z, "2023-06-08", 0.0), "f4")
    zdir = CFG.BULK_ROOT / "floodplain_dyn" / f"{M['names'][0]}{SFX}"
    with rasterio.open(zdir / "p95e_cellprob_water_2023-06-07.tif") as s:
        n_draws = float(s.tags()["n_draws"])
    pw7 = O.compose_tif(M, SFX, "p95e_cellprob_water_2023-06-07.tif", 65535, "u2"); pw7 = np.where(pw7 < 65535, pw7 / n_draws, 0.0)
    reeds = wc == 90; dz_pre = M["dem"] - H_pre
    C = dict(tr=tr, shp=shp, crs=crs, dom=dom, pw7=pw7, cell_km2=P95.CELL_KM2, zm={}, code={}, km2={})
    for zone in zones:
        zm = dom & (M["own_id"] == M["zone_id"][ZONES[zone][0]])
        code = np.zeros(shp, "u1")
        code[zm & np.isin(wc, (30, 40)) & ((M["dem"] - H_pk) > 2.0)] = 6
        code[zm & reeds & ~B & (pw7 >= 0.8)] = 5
        code[zm & reeds & ~B & (dz_pre > 0.5) & (pw7 < 0.05)] = 3
        code[zm & nw & (wc == 10)] = 2
        code[zm & nw & reeds] = 1
        code[zm & opt] = 4
        C["zm"][zone] = zm; C["code"][zone] = code
        C["km2"][zone] = {STRATA[c]: round(float((code == c).sum()) * P95.CELL_KM2, 1) for c in STRATA}
    return C


def figures(D, km2=None):
    """One figure per zone: every index by day of year, 2022 dashed / 2023 solid, the breach marked."""
    import matplotlib
    import pandas as pd
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG = ROOT / "figures" / "m6_v003A"
    D = D.copy(); D["d"] = pd.to_datetime(D.date); D["doy"] = D.d.dt.dayofyear; D["year"] = D.d.dt.year
    panels = list(INDICES) + ["S1_VV_dB", "S1_VH_dB", "S1_VV_minus_VH_dB"]; bdoy = pd.Timestamp(BREACH).dayofyear
    FIG.mkdir(parents=True, exist_ok=True)
    for zone, Dz in D.groupby("zone"):
        fig, axs = plt.subplots(2, 5, figsize=(26, 10), constrained_layout=True); axs = axs.ravel()
        for ax, ix in zip(axs, panels):
            for nm in STRATA.values():
                for yr, ls in ((2022, "--"), (2023, "-")):
                    s_ = Dz[(Dz["index"] == ix) & (Dz.stratum == nm) & (Dz.year == yr)].groupby("doy")[["median", "p25", "p75"]].median().sort_index()
                    if s_.empty:
                        continue
                    ax.plot(s_.index, s_["median"], ls, marker="o", ms=3, color=COLOR[nm], lw=1.2, label=f"{nm} {yr}" if ix == panels[0] else None)
                    if yr == 2023:
                        ax.fill_between(s_.index, s_["p25"], s_["p75"], color=COLOR[nm], alpha=0.10, lw=0)
            ax.axvline(bdoy, color="k", lw=0.8, ls=":"); ax.set_title(ix, fontsize=9); ax.grid(alpha=0.3); ax.tick_params(labelsize=7); ax.set_xlabel("day of year", fontsize=7)
        axs[0].legend(fontsize=6, ncol=2)
        fig.suptitle(f"P95z {ZONES[zone][0]} by stratum (median, 2023 IQR shaded): Sentinel-2 indices of frame {ZONES[zone][1]} 2022 (dashed) and "
                     f"2023 (solid); Sentinel-1 2023; dotted line = breach." + (f" Strata km2: {km2[zone]}" if km2 else ""), fontsize=9)
        fig.savefig(FIG / f"p95z_{zone}_indices.png", dpi=110, bbox_inches="tight"); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--summary-only", action="store_true", help="rebuild the summaries from the existing table")
    ap.add_argument("--zones", nargs="+", default=list(ZONES), choices=list(ZONES)); a = ap.parse_args()
    if a.summary_only:
        import pandas as pd
        D = pd.read_csv(TAB / "p95z_strata_indices.csv"); S = summarize(D); figures(D); print(S.to_string(index=False)); return
    t0 = time.time()
    import pandas as pd
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.warp import reproject
    from rasterio.windows import Window

    from floodstate_eo import _kakhovka_legacy_config as CFG
    C = strata_context(a.zones); tr, crs = C["tr"], C["crs"]
    rows = []; km2 = C["km2"]
    for zone in a.zones:
        _, frame, caches = ZONES[zone]
        code = C["code"][zone]
        print(zone, "strata km2:", km2[zone], f"{round(time.time() - t0)} s", flush=True)

        # ---- Sentinel-2, the zone's frame (windowed to the strata) ----------------------------------------------------------------------
        idir = CFG.BULK_ROOT / "frames10" / frame / "indices"
        dates = sorted(p.name[:10] for p in idir.glob("20*_valid.tif") if "2022-02-01" <= p.name[:10] <= "2023-11-30")
        with rasterio.open(idir / f"{dates[0]}.tif") as s:
            t10, s10 = s.transform, s.shape
        code10 = np.zeros(s10, "u1")
        reproject(code, code10, src_transform=tr, src_crs=crs, dst_transform=t10, dst_crs=crs, resampling=Resampling.nearest)
        rr, cc = np.nonzero(code10)
        win = Window(int(cc.min()), int(rr.min()), int(cc.max() - cc.min() + 1), int(rr.max() - rr.min() + 1))
        code10 = code10[win.row_off:win.row_off + win.height, win.col_off:win.col_off + win.width]
        sel10 = {c: code10 == c for c in STRATA}
        for d in dates:
            with rasterio.open(idir / f"{d}.tif") as s:
                dsc = list(s.descriptions); nd = s.nodata; arr = {b: s.read(dsc.index(b) + 1, window=win) for b in INDICES}
            with rasterio.open(idir / f"{d}_valid.tif") as s:
                v = s.read(1, window=win) > 0
            for c, nm in STRATA.items():
                m = sel10[c] & v
                if m.sum() < 2000:                                        # < 0.2 km2 observed: skip
                    continue
                for b in INDICES:
                    x = arr[b][m]; x = x[x != nd].astype("f4") / 1e4
                    if x.size:
                        q = np.percentile(x, [25, 50, 75])
                        rows.append(dict(zone=zone, date=d, sensor="S2", index=b, stratum=nm, observed_km2=round(m.sum() * 1e-4, 2), p25=round(float(q[0]), 4),
                                         median=round(float(q[1]), 4), p75=round(float(q[2]), 4)))
        print(f"  {zone} S2 {frame}: {len(dates)} dates, {round(time.time() - t0)} s", flush=True)

        # ---- Sentinel-1, the zone's caches -------------------------------------------------------------------------------------------
        seen = set()
        for cname in caches:
            cdir = CFG.S1_CACHE / cname; zz = np.load(cdir / "per_scene_water.npz", allow_pickle=True)
            zs = tuple(int(v) for v in zz["shape"]); ztr = from_origin(float(zz["x0"]), float(zz["y1"]), float(zz["cell"]), float(zz["cell"]))
            codeS = np.zeros(zs, "u1")
            reproject(code, codeS, src_transform=tr, src_crs=crs, dst_transform=ztr, dst_crs=crs, resampling=Resampling.nearest)
            for p in sorted(cdir.glob("2023-*.npz")):
                sc = p.stem
                if sc in seen or sc[:10] > "2023-06-30":
                    continue
                seen.add(sc)
                with np.load(p) as b:
                    vv, vh, cov = b["vv"], b["vh"], b["cov"]
                ok = cov & (vv > 0) & (vh > 0)
                vvd, vhd = 10 * np.log10(np.maximum(vv, 1e-6)), 10 * np.log10(np.maximum(vh, 1e-6))
                for c, nm in STRATA.items():
                    m = (codeS == c) & ok
                    if m.sum() < 500:
                        continue
                    for b_, x in (("S1_VV_dB", vvd[m]), ("S1_VH_dB", vhd[m]), ("S1_VV_minus_VH_dB", (vvd - vhd)[m])):
                        q = np.percentile(x, [25, 50, 75])
                        rows.append(dict(zone=zone, date=sc[:10], sensor=f"S1 {sc[11:]}", index=b_, stratum=nm, observed_km2=round(m.sum() * 4e-4, 2),
                                         p25=round(float(q[0]), 3), median=round(float(q[1]), 3), p75=round(float(q[2]), 3)))
            print(f"  {zone} S1 {cname}: {round(time.time() - t0)} s", flush=True)
    D = pd.DataFrame(rows); D.to_csv(TAB / "p95z_strata_indices.csv", index=False); summarize(D)

    figures(D, km2)
    print("->", TAB / "p95z_strata_indices.csv", TAB / "p95z_seasonal_baseline.csv", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
