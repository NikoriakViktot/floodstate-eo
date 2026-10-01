# New in floodstate-eo, 2026-10-01 (maintainer: "why does this go in circles, why never the full picture" -- the inventory of what each
# sensor observed, per zone, stratum and period, written once and consulted before any diagnostic is drawn). STATUS: ACTIVE.
"""P95u -- the observation inventory of the reed-bed question: for every zone x stratum x period x sensor, how many scenes exist, which
share of the stratum has at least one clear observation in the period, the mean clear share per scene, the best scene and the dates.
It is the gate of the diagnostics (p95zm refuses a composite below MIN_SHARE unless --allow-partial) and the first table of the
full picture (T01b, publication/WETLAND_EVIDENCE.md).

Zones: delta (ZONE_2), floodway (ZONE_4 west of the Inhulets rectangle included), inhulets (the Inhulets valley rectangle of p95,
  inside ZONE_4). Strata: the six p95z strata, the three pre-event ground classes of p95x (ground_class.tif) and ALL (domain cells).
Periods (PERIODS): normal_year 25 May - 30 Jun 2022; pre_breach_2023 1 Jan - 5 Jun 2023; spring_2023 15 Apr - 5 Jun 2023;
  peak 6 - 9 Jun 2023; recession 10 - 30 Jun 2023; july 2023.
Sensors: S2 = the p54a 10 m index stacks of the zone's frame (B2 for the delta, B1 for the floodway and the Inhulets; nothing east of
  538 km), clear = the p54a valid mask; S1_orb14 = the ascending orbit 14 scenes of the zone caches (the same-orbit series of the
  checks); S1_all = every orbit in the caches; k10e = the frozen SWOT-DNIPRO class products of the zone (observed = class > 0);
  UNOSAT = the layers of activation FL20230606UKR (dates only; their footprint per stratum is in p95y, not recomputed here).
Outputs: tables/p95u_evidence_inventory.csv, tables/p95u_manifest.json. `check(zone, period, sensor, min_share)` reads the table.
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
TAB = ROOT / "tables"
OUT = TAB / "p95u_evidence_inventory.csv"
PERIODS = (("normal_year", "2022-05-25", "2022-06-30"), ("pre_breach_2023", "2023-01-01", "2023-06-05"), ("spring_2023", "2023-04-15", "2023-06-05"),
           ("peak", "2023-06-06", "2023-06-09"), ("recession", "2023-06-10", "2023-06-30"), ("july", "2023-07-01", "2023-07-31"))
GROUND = {0: "GROUND_DRY_BEFORE_EVENT", 1: "GROUND_VEGETATED_WETLAND", 2: "GROUND_OPEN_WATER_REFERENCE"}
UNOSAT = (("2023-06-07", "ICEYE flood layer (product 3614)"), ("2023-06-06", "Sentinel-3 6-9 June, 300 m (composite 3616)"),
          ("2023-06-08", "Sentinel-2 8 June (composite 3616)"), ("2023-06-13", "Sentinel-1/2 13 June (product 3623)"))
MIN_SHARE = 0.5


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def check(zone, period, sensor, min_share=MIN_SHARE, stratum="ALL"):
    """(ok, share, row) for one cell of the inventory; ok is None when the inventory does not exist yet."""
    import pandas as pd
    if not OUT.exists():
        return None, None, None
    D = pd.read_csv(OUT); r = D[(D.zone == zone) & (D.period == period) & (D.sensor == sensor) & (D.stratum == stratum)]
    if r.empty:
        return None, None, None
    share = float(r.share_any_clear.iloc[0]); return share >= min_share, share, r.iloc[0]


def main():
    ap = argparse.ArgumentParser(); ap.parse_args(); t0 = time.time()
    import pandas as pd
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.warp import reproject
    from rasterio.windows import Window, from_bounds, intersection

    from floodstate_eo import _kakhovka_legacy_config as CFG
    Z = _ld("p95z", HERE / "p95z_delta_indices.py")
    C = Z.strata_context(list(Z.ZONES)); tr, shp, crs = C["tr"], C["shp"], C["crs"]
    P95 = Z._ld("p95_hand_daily_inundation", HERE / "p95_hand_daily_inundation.py"); P = P95.load_p92()
    with rasterio.open(CFG.BULK_ROOT / "floodplain_dyn" / "_weak_labels" / "ground_class.tif") as s:
        gc = s.read(1)
    assert gc.shape == shp
    xs = tr.c + tr.a * (np.arange(shp[1]) + 0.5); ys = tr.f + tr.e * (np.arange(shp[0]) + 0.5)
    x0, y0, x1, y1 = P.CUT_RECTS["inhulets_valley"]
    inh = ((xs >= x0) & (xs < x1))[None, :] & ((ys >= y0) & (ys < y1))[:, None]
    zones = {"delta": (Z.ZONES["delta"], C["zm"]["delta"], C["code"]["delta"]),
             "floodway": (Z.ZONES["floodway"], C["zm"]["floodway"] & ~inh, C["code"]["floodway"] * ~inh),
             "inhulets": (Z.ZONES["floodway"], C["zm"]["floodway"] & inh, C["code"]["floodway"] * inh)}
    print("context", round(time.time() - t0), "s", flush=True)

    def strata_of(zm, code):
        d = {"ALL": zm}
        d.update({nm: code == c for c, nm in Z.STRATA.items()})          # the ground classes are added by the caller on its grid
        return d

    def onto(a, dst_tr, dst_shape):
        out = np.zeros(dst_shape, "u1")
        reproject(a.astype("u1"), out, src_transform=tr, src_crs=crs, dst_transform=dst_tr, dst_crs=crs, resampling=Resampling.nearest)
        return out

    def window(t_full, shape_full, zm, step):
        r, c = np.nonzero(zm); bx0, by1 = tr * (c.min(), r.min()); bx1, by0 = tr * (c.max() + 1, r.max() + 1)
        w = intersection(from_bounds(bx0, by0, bx1, by1, transform=t_full).round_offsets().round_lengths(), Window(0, 0, shape_full[1], shape_full[0]))
        w = Window(int(w.col_off), int(w.row_off), int(w.width), int(w.height))
        ts = rasterio.windows.transform(w, t_full) * rasterio.Affine.scale(step); sh = (int(w.height // step), int(w.width // step))
        return w, ts, sh

    rows = []

    def tally(zone, sensor, strata, scenes, dates_in, note=""):
        """scenes: list of (date, clear bool array on the strata grid); strata: name -> bool array on the same grid."""
        for pname, d0, d1 in PERIODS:
            sel = [(d, v) for d, v in scenes if d0 <= d <= d1]
            for st, m in strata.items():
                if st.startswith("_"):
                    continue
                n_st = int(m.sum())
                if n_st == 0:
                    continue
                if sel:
                    anyc = np.zeros(m.shape, bool); shares = []
                    for d, v in sel:
                        anyc |= v; shares.append(float((v & m).sum() / n_st))
                    best = int(np.argmax(shares))
                    rows.append(dict(zone=zone, sensor=sensor, period=pname, stratum=st, stratum_km2=round(n_st * strata["_km2"], 2), n_scenes=len(sel),
                                     first=sel[0][0], last=sel[-1][0], share_any_clear=round(float((anyc & m).sum() / n_st), 4),
                                     mean_clear_share=round(float(np.mean(shares)), 4), best_scene=sel[best][0], best_scene_share=round(shares[best], 4), note=note))
                else:
                    rows.append(dict(zone=zone, sensor=sensor, period=pname, stratum=st, stratum_km2=round(n_st * strata["_km2"], 2), n_scenes=0, first="", last="",
                                     share_any_clear=0.0, mean_clear_share=0.0, best_scene="", best_scene_share=0.0,
                                     note=(note + "; " if note else "") + (f"no scene in the period (this archive holds {dates_in[0]} .. {dates_in[-1]})" if dates_in else "no scene")))

    for zone, ((zname, frame, caches), zm, code) in zones.items():
        # ---- Sentinel-2: the p54a valid masks of the frame, 20 m ----------------------------------------------------------------
        idir = CFG.BULK_ROOT / "frames10" / frame / "indices"; alld = sorted(p.name[:10] for p in idir.glob("20*_valid.tif"))
        with rasterio.open(idir / f"{alld[0]}_valid.tif") as s:
            t10, s10 = s.transform, s.shape
        w, ts, sh = window(t10, s10, zm, 2)
        st2 = strata_of(onto(zm, ts, sh) > 0, onto(code, ts, sh)); gc2 = onto(gc, ts, sh)
        st2.update({nm: st2["ALL"] & (gc2 == c) for c, nm in GROUND.items()}); st2["_km2"] = 4e-4
        scenes = []
        for d in alld:
            if not ("2022-01-01" <= d <= "2023-12-31"):
                continue
            with rasterio.open(idir / f"{d}_valid.tif") as s:
                v = s.read(1, window=w, out_shape=sh, resampling=Resampling.nearest) > 0
            scenes.append((d, v))
        tally(zone, "S2", st2, scenes, alld, note=f"frame {frame}; clear = p54a valid mask")
        print(f"  {zone} S2: {len(scenes)} scenes, {round(time.time() - t0)} s", flush=True)

        # ---- Sentinel-1: the zone caches, orbit 14 and all orbits ----------------------------------------------------------------
        s1 = {}; grids = set()
        for cname in caches:
            cdir = CFG.S1_CACHE / cname; zz = np.load(cdir / "per_scene_water.npz", allow_pickle=True)
            grids.add((float(zz["x0"]), float(zz["y1"]), float(zz["cell"]), tuple(int(v) for v in zz["shape"])))
            for p in sorted(cdir.glob("20*.npz")):
                s1.setdefault(p.stem, cdir)
        assert len(grids) == 1, grids
        gx0, gy1, gcell, gshape = next(iter(grids)); tS = from_origin(gx0, gy1, gcell, gcell)
        w, ts, sh = window(tS, gshape, zm, 1); cut = (slice(w.row_off, w.row_off + w.height), slice(w.col_off, w.col_off + w.width))
        stS = strata_of(onto(zm, ts, sh) > 0, onto(code, ts, sh)); gcS = onto(gc, ts, sh)
        stS.update({nm: stS["ALL"] & (gcS == c) for c, nm in GROUND.items()}); stS["_km2"] = 4e-4
        scenes = []
        for stem in sorted(s1):
            with np.load(s1[stem] / f"{stem}.npz") as b:
                cov = b["cov"][cut][:sh[0], :sh[1]]
            scenes.append((stem, cov.astype(bool)))
        tally(zone, "S1_all", stS, [(k[:10], v) for k, v in scenes], sorted(k[:10] for k in s1), note="every orbit of the zone caches; clear = covered")
        tally(zone, "S1_orb14", stS, [(k[:10], v) for k, v in scenes if k.endswith("orb14_ASC")], sorted(k[:10] for k in s1 if k.endswith("orb14_ASC")),
              note="ascending orbit 14 (~16 UTC), the same-orbit series of the checks")
        print(f"  {zone} S1: {len(scenes)} scenes, {round(time.time() - t0)} s", flush=True)

        # ---- k10e: the frozen class products of the zone -----------------------------------------------------------------------
        kdir = CFG.BULK_ROOT / "zone_spectral" / zname
        kd = sorted(p.name[:10] for p in kdir.glob("20*_class.tif") if "2022-01-01" <= p.name[:10] <= "2023-12-31")
        with rasterio.open(kdir / f"{kd[0]}_class.tif") as s:
            tk, sk = s.transform, s.shape
        w, ts, sh = window(tk, sk, zm, 1)
        stK = strata_of(onto(zm, ts, sh) > 0, onto(code, ts, sh)); gcK = onto(gc, ts, sh)
        stK.update({nm: stK["ALL"] & (gcK == c) for c, nm in GROUND.items()}); stK["_km2"] = 4e-4
        scenes = []
        for d in kd:
            with rasterio.open(kdir / f"{d}_class.tif") as s:
                k = s.read(1, window=w)[:sh[0], :sh[1]]
            scenes.append((d, k > 0))
        tally(zone, "k10e", stK, scenes, kd, note="frozen SWOT-DNIPRO p25 products, one tile per date; observed = class > 0")
        print(f"  {zone} k10e: {len(scenes)} dates, {round(time.time() - t0)} s", flush=True)

        # ---- UNOSAT: dates of the layers; the footprint per stratum lives in p95y ------------------------------------------------
        for pname, d0, d1 in PERIODS:
            sel = [(d, lab) for d, lab in UNOSAT if d0 <= d <= d1]
            rows.append(dict(zone=zone, sensor="UNOSAT", period=pname, stratum="ALL", stratum_km2=round(float(zm.sum()) * C["cell_km2"], 2), n_scenes=len(sel),
                             first=sel[0][0] if sel else "", last=sel[-1][0] if sel else "", share_any_clear=np.nan, mean_clear_share=np.nan,
                             best_scene="", best_scene_share=np.nan, note=("; ".join(lab for _, lab in sel) + " -- footprint per stratum not computed here (p95y, T16b/T16c)") if sel else "no UNOSAT layer in the period"))
    D = pd.DataFrame(rows); D.to_csv(OUT, index=False)
    facts = {}
    for z, p_, s_ in (("delta", "spring_2023", "S2"), ("delta", "peak", "S2"), ("floodway", "peak", "S2"), ("floodway", "spring_2023", "S2"), ("delta", "peak", "S1_orb14")):
        r = D[(D.zone == z) & (D.period == p_) & (D.sensor == s_) & (D.stratum == "ALL")].iloc[0]
        facts[f"{z}/{p_}/{s_}"] = dict(n_scenes=int(r.n_scenes), share_any_clear=None if pd.isna(r.share_any_clear) else float(r.share_any_clear), best=str(r.best_scene), best_share=None if pd.isna(r.best_scene_share) else float(r.best_scene_share))
    (TAB / "p95u_manifest.json").write_text(json.dumps(dict(producer="p95u_evidence_inventory.py", periods=PERIODS, min_share_gate=MIN_SHARE, zones=list(zones),
                                                            strata=["ALL", *Z.STRATA.values(), *GROUND.values()], sensors=["S2", "S1_all", "S1_orb14", "k10e", "UNOSAT"],
                                                            facts=facts, seconds=round(time.time() - t0)), indent=1, default=str))
    pd.set_option("display.width", 250)
    print(D[(D.stratum == "ALL") & (D.sensor != "UNOSAT")].pivot_table(index=["zone", "period"], columns="sensor", values="share_any_clear").round(2).to_string())
    print(json.dumps(facts, indent=1)); print("->", OUT, round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
