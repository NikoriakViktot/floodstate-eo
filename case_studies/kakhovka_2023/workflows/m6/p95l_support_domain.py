# New in floodstate-eo, 2026-09-29 (maintainer decision D-SUPPORT after the Stage-1 review of the new numbers). STATUS: ACTIVE.
"""P95l -- the observational support of the reconstructed new inundation (nominal run of the primary rule).

Every newly inundated cell is classed by the distance of its nearest SWOT node (the node that serves it: for cells with a node
within 3 km the surface is the median of those nodes, beyond that the nearest node's level):
  DIRECT        <= 3 km    (the surface is observed around the cell)
  EXTRAPOLATED  3 - 10 km  (nearest-node fallback)
  WEAK          > 10 km    (weakly constrained)
with two independent flags: capped at the Kherson gauge (> 15 km from any node and west of the gauge; p95 WSE.far) and, in the
Inhulets valley, CROSS-RIVER (the nearest node is not an Inhulets node). The 3 and 10 km limits are operational thresholds,
not physical constants. The FULL terrain-connectivity reconstruction stays the primary product; the SUPPORTED CORE (<= 10 km)
and the weak share are reported next to it, with the 10 km cap run of p95 (`--fallback-max-km 10`) as a separate sensitivity
(the cap also changes the connectivity, so it is not the core).

Consistency: per zone, region and day the classes add up to the new area of the p95 table of the same run (asserted).

Outputs: <case_study>/tables/p95l_support_domain.csv (date x region x class x flags, km2),
         p95l_supported_core.csv (per date and region: full, direct, extrapolated, weak, core, weak share, cross-river, cap
         sensitivity), p95l_manifest.json
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio import features

from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
RULE = "connected_ceiling"
CLASSES = ((3.0, "direct"), (10.0, "extrapolated"), (np.inf, "weak"))       # upper distance limit (km) of each class
TRIBUTARY = ("INHULETS_VALLEY_rect", "Inhulets")                           # region with a river identity -> cross-river flag


def _ld(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def zone_regions(P95, P, zone, G):
    """The accounting regions of p95 (region_masks on owned cells) for one zone grid: corridor, Inhulets rectangle, p42 domain."""
    xs = G["transform"].c + P95.CELL_M * (np.arange(G["nx"]) + 0.5); ys = G["transform"].f - P95.CELL_M * (np.arange(G["ny"]) + 0.5)
    rect = lambda r: ((xs >= r[0]) & (xs < r[2]))[None, :] & ((ys >= r[1]) & (ys < r[3]))[:, None]
    own = np.ones((G["ny"], G["nx"]), bool)
    if zone != "ZONE_2_KHERSON_DELTA":                                        # ZONE_2 owns the overlap
        own &= ~rect(P95.ZONE2_BBOX)
    cut = np.zeros_like(own)
    for r in P.CUT_RECTS.values():
        cut |= rect(r)
    R = {"DNIPRO_CORRIDOR": own & ~cut, "INHULETS_VALLEY_rect": own & rect(P.CUT_RECTS["inhulets_valley"])}
    gj = Path(CFG._SWOT_DNIPRO_SIBLING) / "data/processed/domains/below_dam_floodplain_utm.geojson"
    if gj.exists():
        g = json.loads(gj.read_text())
        fp = features.rasterize([(ft["geometry"], 1) for ft in g["features"]], out_shape=(G["ny"], G["nx"]), transform=G["transform"],
                                fill=0, dtype="uint8").astype(bool)
        R["P42_FLOODPLAIN_DOMAIN"] = own & fp
    return R


def main():
    P95 = _ld("p95_hand_daily_inundation"); P = P95.load_p92(); W = P95.load_engine()[0]
    riv = np.array(W.river); ref = pd.read_csv(CFG.TABLES / f"p95_daily_area_{RULE}.csv").set_index(["zone", "date", "region"]).new_km2
    rows, checked = [], 0
    for zn in P95.ZONES:
        f = P95.DYN / f"{zn}_{RULE}" / "daily_new.npz"
        with rasterio.open(CFG.BULK_ROOT / "dem_seamless" / f"{zn}_dem_evrf2019_20m.tif") as s:
            G = dict(transform=s.transform, crs=s.crs, ny=s.height, nx=s.width)
        R = zone_regions(P95, P, zn, G)
        Z = W.prepare(G); up = lambda a: a.reshape(Z["shape_c"])[np.ix_(Z["ri"], Z["ci"])]
        dkm = up(Z["d1"]) / 1e3; capped = up(Z["far"]); cross = ~up(riv[Z["i1"]] == TRIBUTARY[1])
        cls = np.full(dkm.shape, len(CLASSES) - 1, "u1")
        for k in range(len(CLASSES) - 2, -1, -1):
            cls[dkm <= CLASSES[k][0]] = k
        npz = np.load(f); ny, nx = G["ny"], G["nx"]
        for dt in W.dates:
            ds = str(dt.date())
            if ds not in npz.files:
                continue
            new = np.unpackbits(npz[ds], count=ny * nx).reshape(ny, nx).astype(bool)
            for rn, m in R.items():
                nm = new & m; tot = float(nm.sum()) * P95.CELL_KM2
                r_ = ref.get((zn, ds, rn), np.nan)
                assert np.isnan(r_) or abs(round(tot, 1) - r_) <= 0.1 + 1e-9, (zn, ds, rn, tot, r_)
                checked += int(np.isfinite(r_))
                if not nm.any():
                    continue
                flags = [(c, x) for c in (False, True) for x in ((False, True) if rn == TRIBUTARY[0] else (None,))]
                for k, (_, name) in enumerate(CLASSES):
                    for cp, xr in flags:
                        mm = nm & (cls == k) & (capped == cp)
                        if xr is not None:
                            mm &= cross == xr
                        if mm.any():
                            rows.append(dict(date=ds, zone=zn, region=rn, support=name, gauge_capped=cp, cross_river=xr,
                                             new_km2=float(mm.sum()) * P95.CELL_KM2, node_km_median=float(np.median(dkm[mm]))))
    D = pd.DataFrame(rows)
    S = D.groupby(["date", "region", "support", "gauge_capped", "cross_river"], dropna=False, as_index=False).agg(new_km2=("new_km2", "sum"), node_km_median=("node_km_median", "max"))
    S["share_of_new"] = (S.new_km2 / S.groupby(["date", "region"]).new_km2.transform("sum")).round(4); S["new_km2"] = S.new_km2.round(2)
    S.to_csv(CFG.TABLES / "p95l_support_domain.csv", index=False)
    # supported core per date and region
    by = lambda q: D[q].groupby(["date", "region"]).new_km2.sum()
    C = pd.DataFrame({"A_full_km2": D.groupby(["date", "region"]).new_km2.sum()})
    for _, name in CLASSES:
        C[f"A_{name}_km2"] = by(D.support == name)
    C = C.fillna(0.0)
    C["A_core_le10km_km2"] = C.A_direct_km2 + C.A_extrapolated_km2; C["share_weak"] = (C.A_weak_km2 / C.A_full_km2).round(4)
    C["A_gauge_capped_km2"] = by(D.gauge_capped == True).reindex(C.index).fillna(0.0)  # noqa: E712 -- column of Python bools
    C["A_cross_river_km2"] = by(D.cross_river == True).reindex(C.index)                # noqa: E712 -- NaN outside the tributary
    C = C.reset_index()
    cap = CFG.TABLES / f"p95_daily_area_pooled_{RULE}_fallback10km.csv"
    if cap.exists():
        k = pd.read_csv(cap)[["date", "region", "new_km2"]].rename(columns={"new_km2": "A_cap10km_sensitivity_km2"})
        C = C.merge(k, on=["date", "region"], how="left")
    for c in C.columns:
        if c.endswith("_km2"):
            C[c] = C[c].round(2)
    C["note"] = ("nominal run of the primary rule; classes by the distance of the nearest SWOT node (direct <= 3 km, extrapolated 3-10 km, "
                 "weak > 10 km; operational thresholds); core = direct + extrapolated; the cap run recomputes the connectivity without "
                 "surfaces from nodes > 10 km and is a sensitivity, not the core")
    C.to_csv(CFG.TABLES / "p95l_supported_core.csv", index=False)
    man = dict(producer="p95l_support_domain.py", rule=RULE, classes={n: f"<= {u:g} km" for u, n in CLASSES}, flags=["gauge_capped (p95 WSE.far)", "cross_river (Inhulets region)"],
               consistency_rows_checked=checked, decision="D-SUPPORT (maintainer, 2026-09-29): full reconstruction primary; supported core and the cap run reported next to it")
    (CFG.TABLES / "p95l_manifest.json").write_text(json.dumps(man, indent=1))
    pd.set_option("display.width", 250)
    print(C[C.date.isin(["2023-06-07", "2023-06-09", "2023-06-13"])].drop(columns="note").to_string(index=False))
    print(f"consistency rows checked against p95: {checked}")


if __name__ == "__main__":
    main()
