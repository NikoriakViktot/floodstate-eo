# New in floodstate-eo, 2026-09-30 (maintainer: daily maps of Kozachi Laheri with the new-water and the total flooded area). STATUS: ACTIVE. Diagnostic.
"""P95r -- daily maps of the primary reconstruction over a local window, with the area of new water and of total water per day.

Default window: the left bank between Kozachi Laheri (the village on the Konka; point 32.9832 E 46.7084 N given by the maintainer, OSM
32.9906 E 46.7108 N) and Krynky (33.1190 E 46.7465 N), with the floodplain lowland south of Krynky tested in p95p / p95q (33.12 E 46.665 N;
named 'kozachi_laheri_lowland' in those scripts, it lies 10 km ESE of the village).

Water of a day (nominal world of the primary run, p95 rev 8):
  total water  = the reconstruction's water surface P_t -- the river network and the pre-breach water connected to it plus the new water --
                 recomputed per day exactly as p95 builds it (the p95o path: union mosaic, the water-surface engine of the run's manifest,
                 potential_mosaic), with the gate new = P_t minus baseline == daily_new.npz (<= 0.1 km2 over the grid). A plain label of
                 (new | baseline) over-counts terrace ponds that touch new water but lie above H_t (+49 km2 in the corridor on 7 June);
  new water    = P_t minus the pre-breach regime (the A_new of the paper), with the median world of the ensemble (P >= 0.5) and the expected
                 area (sum of P) where p95e --mode cellprob computed the day.
Units: the window, the lowland box of p95p / p95q, and the residential areas of Kozachi Laheri and of Krynky (OpenStreetMap landuse =
residential, (c) OpenStreetMap contributors, ODbL) in their OSM state of 5 June 2023: the Overpass reply (cached under $BULK_ROOT/context/
with its query and timestamp) checked element by element against the OSM API history -- all 56 ways / relations existed on that date with the
same node lists; 4 of 669 nodes moved later (<= 25 m, Krynky polygons) and get their 2023 positions back).
Map layers: own Sentinel-2 true colour of 13 June 2022 (p97b); pre-breach water inside P_t; new water; weak support (p95l codes 3/4,
hatched); the median-world outline; same-day Sentinel-1 water where a scene covers >= 20 % of the window; residential areas, Michurina
street (the street named in the reports on Kozachi Laheri), settlements.
Outputs: tables/p95r_daily_areas_<name>.csv, p95r_michurina_street_<name>.csv, p95r_manifest_<name>.json;
         figures/m6_v003A/p95r_daily_<name>.png (overview with the daily areas), p95r_daily_<name>_kozachi_laheri_zoom.png
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
from rasterio import features
from rasterio.warp import transform as tf_transform

from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.terrain.connectivity import largest_component

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = ROOT / "figures" / "m6_v003A"
OSM_CACHE = CFG.BULK_ROOT / "context" / "osm_kozachi_krynky.json"                     # the Overpass reply (current OSM)
OSM_DATE = "2023-06-05T00:00:00Z"                                                           # the event: map the OSM state of that date
OSM_STATE = CFG.BULK_ROOT / "context" / "osm_kozachi_krynky_state_2023-06-05.json"      # the reply with node positions restored to OSM_DATE
OSM_QUERY = ('[out:json][timeout:60];(way["landuse"="residential"](around:3500,46.7083793,32.9831722);relation["landuse"="residential"]'
             '(around:3500,46.7083793,32.9831722);way["landuse"="residential"](around:3000,46.7464790,33.1189690);relation["landuse"="residential"]'
             '(around:3000,46.7464790,33.1189690);way["highway"]["name"~"Мічуріна"](around:4000,46.7083793,32.9831722);'
             'node["place"~"^(village|hamlet|town)$"](46.58,32.88,46.78,33.30););out geom;')
VILLAGES = {"Kozachi Laheri": (32.9831722, 46.7083793), "Krynky": (33.1189690, 46.7464790)}      # the residential units (lon, lat)
LOWLAND = dict(lon=33.12, lat=46.665, half_km=(6.5, 7.0))                                          # = p95p / p95q defaults
COL = dict(pre="#16324f", new="#2a78d6", weak="#eb6834", p50="#ffd23f", s1="#7cfc00", res="#ffffff", street="#e0249a", box="#e34948")


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def fetch_osm():
    """Run OSM_QUERY on the Overpass API once and cache the reply (its osm3s timestamp dates the OSM state used)."""
    import urllib.parse
    import urllib.request
    req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": OSM_QUERY}).encode(),
                                 headers={"User-Agent": "floodstate-eo (flood reconstruction research)", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read()
    json.loads(body)                                                                  # refuse to cache an HTML error page
    OSM_CACHE.parent.mkdir(parents=True, exist_ok=True); OSM_CACHE.write_bytes(body)


def osm_state(date=OSM_DATE):
    """The OSM state of `date` for the elements of the cached reply: every way / relation must have existed on the date with the same node
    (member) list as now -- else the check fails loudly; nodes changed after the date get their position of the date back (OSM API history).
    Writes OSM_STATE and <context>/osm_history_check_<day>.json. (Overpass attic queries for this area failed on 2026-09-30: out of memory /
    dispatcher errors -- hence the per-element API history.)"""
    import math
    import urllib.request
    ua = {"User-Agent": "floodstate-eo (flood reconstruction research; OSM history check)"}; api = "https://api.openstreetmap.org/api/0.6"

    def get(url):
        for k in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=ua), timeout=60) as r:
                    return json.loads(r.read())
            except Exception as e:                                                    # transient API errors: retry, then fail
                err = e; time.sleep(2 * (k + 1))
        raise err
    cur = json.loads(OSM_CACHE.read_text()); rows, nodes = [], set()
    for e in cur["elements"]:
        if e["type"] not in ("way", "relation"):
            continue
        h = sorted(get(f"{api}/{e['type']}/{e['id']}/history.json")["elements"], key=lambda v: v["version"]); key = "nodes" if e["type"] == "way" else "members"
        ok = [v for v in h if v["timestamp"] <= date]
        rows.append(dict(type=e["type"], id=e["id"], created=h[0]["timestamp"][:10], existed=bool(ok), same=bool(ok) and ok[-1].get(key) == h[-1].get(key)))
        nodes |= set(e.get("nodes", []))
    bad = [r for r in rows if not (r["existed"] and r["same"])]
    if bad:
        raise SystemExit(f"OSM elements not in their current form on {date}: {bad}")
    restored, ids = {}, sorted(nodes)
    for i in range(0, len(ids), 150):
        for n in get(f"{api}/nodes.json?nodes=" + ",".join(map(str, ids[i:i + 150])))["elements"]:
            if n["timestamp"] > date:
                o = [v for v in get(f"{api}/node/{n['id']}/history.json")["elements"] if v["timestamp"] <= date]
                if not o:
                    raise SystemExit(f"node {n['id']} did not exist on {date}")
                o = o[-1]; restored[n["id"]] = dict(lat=o["lat"], lon=o["lon"], shift_m=round(math.hypot((n["lat"] - o["lat"]) * 111320, (n["lon"] - o["lon"]) * 111320 * math.cos(math.radians(n["lat"]))), 1))
    for e in cur["elements"]:
        for k, nid in enumerate(e.get("nodes", [])):
            if nid in restored:
                e["geometry"][k] = {"lat": restored[nid]["lat"], "lon": restored[nid]["lon"]}
    cur["derived"] = dict(state_on=date, elements_checked=len(rows), nodes_checked=len(ids), nodes_restored={str(k): v for k, v in restored.items()})
    OSM_STATE.write_text(json.dumps(cur))
    (OSM_STATE.parent / f"osm_history_check_{date[:10]}.json").write_text(json.dumps(dict(date=date, elements=rows, nodes_restored=restored), indent=1))


def osm_layers(to_xy):
    """Residential polygons (x, y rings in metres) per village, Michurina street lines, settlement points, from the cached Overpass reply."""
    d = json.loads(OSM_STATE.read_text())
    vxy = {nm: to_xy(*ll) for nm, ll in VILLAGES.items()}
    polys = {nm: [] for nm in VILLAGES}; streets, places = [], []
    for e in d["elements"]:
        t = e.get("tags", {})
        if e["type"] == "node" and "place" in t:
            places.append((t.get("name:en") or t.get("name"), *to_xy(e["lon"], e["lat"]))); continue
        rings = [e["geometry"]] if e["type"] == "way" else [m["geometry"] for m in e.get("members", []) if m.get("role") == "outer" and m.get("geometry")]
        for g in rings:
            xy = [to_xy(p["lon"], p["lat"]) for p in g]
            if t.get("highway"):
                streets.append(np.array(xy)); continue
            if len(xy) < 4:
                continue
            cx, cy = np.mean([p[0] for p in xy]), np.mean([p[1] for p in xy])
            nm = min(vxy, key=lambda k: np.hypot(cx - vxy[k][0], cy - vxy[k][1]))
            if np.hypot(cx - vxy[nm][0], cy - vxy[nm][1]) <= 4500:
                polys[nm].append(xy)
    return polys, streets, places, d.get("osm3s", {}).get("timestamp_osm_base")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="kozachi_laheri_krynky"); ap.add_argument("--sfx", default="_connected_ceiling")
    ap.add_argument("--bbox", type=float, nargs=4, default=[32.90, 46.595, 33.23, 46.78], help="lon0 lat0 lon1 lat1 of the window")
    ap.add_argument("--zoom", type=float, nargs=4, default=[32.925, 46.690, 33.025, 46.726], help="lon0 lat0 lon1 lat1 of the Kozachi Laheri zoom")
    ap.add_argument("--start", default="2023-06-01"); ap.add_argument("--end", default="2023-06-30")
    ap.add_argument("--fetch-osm", action="store_true", help="re-run the Overpass query and refresh the cache before mapping")
    ap.add_argument("--panels", nargs="*", default=None, help="dates to map (default: 2023-06-05 and every day from 06-06 with > 0.2 km2 new water, max 15)")
    a = ap.parse_args(); t0 = time.time(); TAB = ROOT / "tables"
    if a.fetch_osm or not OSM_CACHE.exists():
        fetch_osm()
    if a.fetch_osm or not OSM_STATE.exists():
        osm_state()
    O = _ld("p95o", HERE / "p95o_component_qa.py"); P95 = O._ld("p95_hand_daily_inundation"); P = P95.load_p92()
    man = O.load_manifest(a.sfx); c = man["constants"]; conn = int(c.get("connectivity", 8)); margin = float(c.get("margin_m", 0.0))
    M = P95.mosaic_layers(P, with_s1=True); g = M["grid"]
    W, dxm, _ = O.engine_for(P95, man, a.sfx); M["base"] = M["base_geom"] & P95.dam_mask(M, dxm)
    seed = largest_component(M["seed"], conn) if c.get("seed_network", "main_stem") == "main_stem" else M["seed"]
    Z = W.prepare(M); baseline = O.compose_npz(M, a.sfx, "baseline"); support = O.compose_tif(M, a.sfx, "support_class.tif")
    print("mosaic + engine", round(time.time() - t0), "s", flush=True)
    # ---- the window on the union grid ------------------------------------------------------------------------------------------
    to_xy = lambda lon, lat: tuple(float(v[0]) for v in tf_transform("EPSG:4326", CFG.CRS_METRIC, [lon], [lat]))
    (x0, y0), (x1, y1) = to_xy(a.bbox[0], a.bbox[1]), to_xy(a.bbox[2], a.bbox[3])
    xs, ys = M["xs"], M["ys"]; cs = np.nonzero((xs >= x0) & (xs <= x1))[0]; rs = np.nonzero((ys >= y0) & (ys <= y1))[0]
    Wn = (slice(rs.min(), rs.max() + 1), slice(cs.min(), cs.max() + 1)); tr = g.transform * g.transform.translation(cs.min(), rs.min())
    shape = (rs.max() - rs.min() + 1, cs.max() - cs.min() + 1); cell_km2 = P95.CELL_KM2
    ext = (tr.c / 1e3, (tr.c + shape[1] * g.cell) / 1e3, (tr.f - shape[0] * g.cell) / 1e3, tr.f / 1e3)
    lx, ly = to_xy(LOWLAND["lon"], LOWLAND["lat"]); X = xs[Wn[1]][None, :]; Y = ys[Wn[0]][:, None]
    box = (np.abs(X - lx) <= LOWLAND["half_km"][0] * 1e3) & (np.abs(Y - ly) <= LOWLAND["half_km"][1] * 1e3)
    polys, streets, places, osm_ts = osm_layers(to_xy)
    units = {"window": np.ones(shape, bool), "lowland box (p95p/p95q)": box}
    for nm, pl in polys.items():
        units[f"{nm} residential (OSM)"] = features.rasterize([({"type": "Polygon", "coordinates": [p]}, 1) for p in pl], out_shape=shape, transform=tr, fill=0, dtype="uint8").astype(bool)
    # ---- the days ----------------------------------------------------------------------------------------------------------------
    days = [str(d.date()) for d in P95.DATES if a.start <= str(d.date()) <= a.end]
    cp_n = {}; rows, store = [], {}
    base_W = baseline[Wn]; foot = {k: np.zeros(shape, bool) for k in units}
    for ds in days:
        pot, _w = P95.potential_mosaic(M, W, Z, ds, "connected_ceiling", margin=margin, connectivity=conn, seed=seed)
        new = pot & ~baseline; stored = O.compose_npz(M, a.sfx, ds)
        if stored is not None:
            diff = float((stored ^ new).sum()) * cell_km2
            assert diff <= 0.1 + 1e-9, (ds, "recomputed new water differs from daily_new.npz by", diff, "km2")
        potW, newW = pot[Wn], new[Wn]
        Pw = None; cpf = CFG.BULK_ROOT / "floodplain_dyn" / f"ZONE_4_DAM_TO_KHERSON_FLOODWAY{a.sfx}" / f"p95e_cellprob_{ds}.tif"
        if cpf.exists():
            with rasterio.open(cpf) as s:
                cp_n[ds] = float(s.tags().get("n_draws", 1000))
            Pw = O.compose_tif(M, a.sfx, f"p95e_cellprob_{ds}.tif", 0, "u2")[Wn].astype("f4") / cp_n[ds]
        s1 = O.s1_layers(M, ds)
        s1W = (s1[0][Wn], s1[1][Wn]) if s1 is not None else None
        store[ds] = dict(pot=potW, new=newW, P=Pw, s1=s1W)
        for k, u in units.items():
            foot[k] |= newW & u
            rows.append(dict(date=ds, unit=k, unit_km2=round(float(u.sum()) * cell_km2, 2), new_km2=round(float((newW & u).sum()) * cell_km2, 2),
                             total_water_km2=round(float((potW & u).sum()) * cell_km2, 2), prebreach_water_in_total_km2=round(float((potW & base_W & u).sum()) * cell_km2, 2),
                             new_median_world_km2=round(float((u & (Pw >= 0.5)).sum()) * cell_km2, 2) if Pw is not None else np.nan,
                             new_expected_km2=round(float(Pw[u].sum()) * cell_km2, 2) if Pw is not None else np.nan,
                             new_share_of_unit=round(float((newW & u).sum() / max(u.sum(), 1)), 3),
                             s1_same_day_window_observed=round(float(s1W[0].mean()), 3) if s1W is not None else np.nan))
        print(ds, {k: r["new_km2"] for k, r in zip(units, rows[-len(units):])}, "total window", rows[-len(units)]["total_water_km2"], round(time.time() - t0), "s", flush=True)
    T = pd.DataFrame(rows)
    fp = pd.DataFrame([dict(date="event footprint (union of daily new water)", unit=k, unit_km2=round(float(units[k].sum()) * cell_km2, 2),
                            new_km2=round(float(foot[k].sum()) * cell_km2, 2)) for k in units])
    pd.concat([T, fp], ignore_index=True).to_csv(TAB / f"p95r_daily_areas_{a.name}.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    print(T.pivot_table(index="date", columns="unit", values=["new_km2", "total_water_km2"]).round(2).to_string())
    print(fp.to_string(index=False))

    # ---- Michurina street: how close does the reconstructed water come? ----------------------------------------------------------
    from scipy import ndimage
    street = np.zeros(shape, bool)
    if streets:
        street = features.rasterize([({"type": "LineString", "coordinates": s_.tolist()}, 1) for s_ in streets], out_shape=shape, transform=tr, fill=0, all_touched=True, dtype="uint8").astype(bool)
    mrows = []
    for ds in days:
        st = store[ds]; r = dict(date=ds, street_cells=int(street.sum()))
        for nm, m in (("new", st["new"]), ("total_water", st["pot"])):
            if street.any() and m.any():
                dist = ndimage.distance_transform_edt(~m) * g.cell
                r[f"min_distance_to_{nm}_m"] = round(float(dist[street].min()), 0); r[f"street_share_within_40m_of_{nm}"] = round(float((dist[street] <= 40.0).mean()), 3)
            else:
                r[f"min_distance_to_{nm}_m"] = np.nan; r[f"street_share_within_40m_of_{nm}"] = 0.0
        if st["P"] is not None and street.any():                                      # the ensemble: how many worlds bring new water to the street
            r["P_max_on_street"] = round(float(st["P"][street].max()), 3)
            for thr in (0.05, 0.25, 0.5):
                m = st["P"] >= thr
                r[f"min_distance_to_P{thr}_m"] = round(float((ndimage.distance_transform_edt(~m) * g.cell)[street].min()), 0) if m.any() else np.nan
        mrows.append(r)
    MS = pd.DataFrame(mrows); MS.to_csv(TAB / f"p95r_michurina_street_{a.name}.csv", index=False)
    print(MS[MS.date.between("2023-06-05", "2023-06-12")].to_string(index=False))

    # ---- figures -----------------------------------------------------------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch, Rectangle
    from floodstate_eo.visualization import figstyle as FS
    win = T[T.unit == "window"].set_index("date")
    panels = a.panels or (["2023-06-05"] + [d for d in days if "2023-06-06" <= d <= "2023-06-15"])
    rgb = []
    for i in range(3):
        arrs = {}
        for z in M["names"]:
            with rasterio.open(CFG.BULK_ROOT / "truecolour" / f"{z}_s2_2022-06-13_20m.tif") as s:
                arrs[z] = s.read(i + 1)
        rgb.append(g.compose(arrs, 0, order=M["names"], dtype="u1")[Wn])
    rgb = np.stack(rgb, -1); wk = np.isin(support[Wn], (3, 4)); kx, ky = to_xy(*VILLAGES["Kozachi Laheri"])

    def sub_of(bb):
        """Row/column slices and extent (km) of a lon/lat box inside the window."""
        (sx0, sy0), (sx1, sy1) = to_xy(bb[0], bb[1]), to_xy(bb[2], bb[3])
        c0 = max(int((sx0 - tr.c) // g.cell), 0); c1 = min(int(np.ceil((sx1 - tr.c) / g.cell)), shape[1])
        r0 = max(int((tr.f - sy1) // g.cell), 0); r1 = min(int(np.ceil((tr.f - sy0) / g.cell)), shape[0])
        return (slice(r0, r1), slice(c0, c1)), ((tr.c + c0 * g.cell) / 1e3, (tr.c + c1 * g.cell) / 1e3, (tr.f - r1 * g.cell) / 1e3, (tr.f - r0 * g.cell) / 1e3)

    def draw(ax, ds, sl, ex, zoom=False):
        st = store[ds]; cut = lambda A: A[sl]
        ax.imshow(cut(rgb), extent=ex, interpolation="bilinear" if not zoom else "nearest", zorder=0)
        ax.imshow(np.where(cut(st["pot"] & base_W), 1, np.nan), extent=ex, cmap=ListedColormap([COL["pre"]]), alpha=0.85, interpolation="nearest", zorder=1)
        ax.imshow(np.where(cut(st["new"]), 1, np.nan), extent=ex, cmap=ListedColormap([COL["new"]]), alpha=0.75 if zoom else 0.8, interpolation="nearest", zorder=2)
        m = cut(st["new"] & wk).astype("f4")
        if m.any():
            h = ax.contourf(m, levels=[0.5, 1.5], colors="none", hatches=["//////"], extent=ex, origin="upper", zorder=3); h.set_edgecolor(COL["weak"]); h.set_linewidth(0.0)
        if st["P"] is not None and cut(st["P"] >= 0.5).any():
            ax.contour(cut(st["P"] >= 0.5).astype("f4"), levels=[0.5], colors=[COL["p50"]], linewidths=0.7 if zoom else 0.55, extent=ex, origin="upper", zorder=4)
        note = ""
        if st["s1"] is not None and cut(st["s1"][0]).mean() >= 0.2:
            ax.contour(cut(st["s1"][1] & st["s1"][0]).astype("f4"), levels=[0.5], colors=[COL["s1"]], linewidths=0.6 if zoom else 0.45, extent=ex, origin="upper", zorder=5)
            note = f"; S1 same day ({cut(st['s1'][0]).mean():.0%} observed)"
        for pl in polys.values():
            for p_ in pl:
                q = np.array(p_) / 1e3; ax.plot(q[:, 0], q[:, 1], color=COL["res"], lw=0.8 if zoom else 0.35, zorder=6)
        for s_ in streets:
            q = s_ / 1e3; ax.plot(q[:, 0], q[:, 1], color=COL["street"], lw=2.2 if zoom else 1.3, zorder=7)
        if not zoom:
            ax.add_patch(Rectangle(((lx - LOWLAND["half_km"][0] * 1e3) / 1e3, (ly - LOWLAND["half_km"][1] * 1e3) / 1e3), 2 * LOWLAND["half_km"][0], 2 * LOWLAND["half_km"][1],
                                   fill=False, ec=COL["box"], lw=0.8, ls="--", zorder=6))
            for nm, px, py in places:
                if ex[0] < px / 1e3 < ex[1] and ex[2] < py / 1e3 < ex[3] and nm != "Kozachi Laheri":
                    ax.plot(px / 1e3, py / 1e3, "o", ms=2.5, mfc="white", mec="k", mew=0.5, zorder=8)
                    ax.annotate(nm, (px / 1e3, py / 1e3), xytext=(3, 2), textcoords="offset points", fontsize=5, zorder=8, bbox=dict(fc="white", ec="none", alpha=0.6, pad=0.3))
        ax.plot(kx / 1e3, ky / 1e3, "*", ms=9 if zoom else 7, mfc="white", mec="k", mew=0.6, zorder=9)
        ax.annotate("Kozachi Laheri", (kx / 1e3, ky / 1e3), xytext=(4, 3), textcoords="offset points", fontsize=6.5 if zoom else 6, fontweight="bold", zorder=9,
                    bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.3))
        r = T[T.date == ds].set_index("unit"); kl = r.loc["Kozachi Laheri residential (OSM)"]; kr = r.loc["Krynky residential (OSM)"]
        if zoom:
            ms_ = MS.set_index("date").loc[ds]
            txt = (f"Kozachi Laheri residential: new water {kl.new_km2:.2f} of {kl.unit_km2:.2f} km2 ({kl.new_share_of_unit:.0%})"
                   + (f"\nMichurina street: nearest new water {ms_.min_distance_to_new_m:.0f} m; {ms_.street_share_within_40m_of_new:.0%} of the street within 40 m of it"
                      if np.isfinite(ms_.min_distance_to_new_m) else "\nMichurina street: no new water in the window"))
        else:
            txt = (f"window: new {r.loc['window', 'new_km2']:.1f} km2 · total water {r.loc['window', 'total_water_km2']:.1f} km2"
                   + (f"\nmedian world new {r.loc['window', 'new_median_world_km2']:.1f} km2" if np.isfinite(r.loc['window', 'new_median_world_km2']) else "")
                   + f"\nKozachi Laheri: new {kl.new_km2:.2f} km2 ({kl.new_share_of_unit:.0%} of residential)\nKrynky: new {kr.new_km2:.2f} km2 ({kr.new_share_of_unit:.0%} of residential)")
        ax.text(0.01, 0.99, txt, transform=ax.transAxes, va="top", ha="left", fontsize=5.6 if not zoom else 6.2, zorder=10, bbox=dict(fc="white", ec="none", alpha=0.82, pad=1.5))
        ax.set_xlim(ex[0], ex[1]); ax.set_ylim(ex[2], ex[3]); ax.set_aspect("equal"); ax.tick_params(labelsize=5)
        ax.set_title(("pre-breach state (" + ds + ")" if ds < "2023-06-06" else ds) + note, fontsize=7.5)
        FS.scale_bar(ax, 1000 if zoom else 5000, units_per_m=1e-3)

    handles = [Patch(fc=COL["pre"], label="pre-breach water inside the reconstruction's water surface (river network)"),
               Patch(fc=COL["new"], label="new water, nominal world (p95 rev 8 primary)"),
               Patch(fc="none", ec=COL["weak"], hatch="//////", label="weak or cross-river support of the water surface (p95l)"),
               Line2D([], [], color=COL["p50"], lw=1, label="median world of the ensemble (P >= 0.5, p95e; days where computed)"),
               Line2D([], [], color=COL["s1"], lw=1, label="Sentinel-1 water, same day (where a scene covers the window)"),
               Line2D([], [], color=COL["res"], lw=1, label="residential areas (OSM)"), Line2D([], [], color=COL["street"], lw=1.5, label="Michurina street, Kozachi Laheri (OSM)"),
               Patch(fc="none", ec=COL["box"], ls="--", label="lowland box of the saddle and wetness tests (p95p, p95q)")]
    credit = ("Basemap: Sentinel-2 L2A 13 June 2022 (contains modified Copernicus Sentinel data 2022); residential areas, streets and settlements "
              "(c) OpenStreetMap contributors (ODbL)")
    # overview: the pre-breach day, the event days and the daily areas
    ncol = 4; nrow = int(np.ceil((len(panels) + 1) / ncol))
    fig, axs = plt.subplots(nrow, ncol, figsize=(4.6 * ncol, 4.6 * nrow * shape[0] / shape[1] + 1.2), constrained_layout=True, squeeze=False); axs = axs.ravel()
    for ax, ds in zip(axs, panels):
        draw(ax, ds, (slice(None), slice(None)), ext)
    ax = axs[len(panels)]; tt = pd.to_datetime(win.index)
    ax.plot(tt, win.total_water_km2, color=COL["pre"], lw=1.4, label="window: total water (river network + new)")
    ax.plot(tt, win.new_km2, color=COL["new"], lw=1.6, label="window: new water")
    bx = T[T.unit == "lowland box (p95p/p95q)"].set_index("date"); ax.plot(tt, bx.new_km2, color=COL["box"], lw=1.2, ls="--", label="lowland box: new water")
    mw = win.new_median_world_km2.dropna(); ax.plot(pd.to_datetime(mw.index), mw, "o", ms=3, color=COL["p50"], mec="k", mew=0.4, label="window: new water, median world (P >= 0.5)")
    ax2 = ax.twinx()
    for nm, colr in (("Kozachi Laheri", "#1baf7a"), ("Krynky", "#8e6bbf")):
        u = T[T.unit == f"{nm} residential (OSM)"].set_index("date"); ax2.plot(tt, u.new_km2, color=colr, lw=1.2, label=f"{nm} residential: new water (right axis)")
    ax.set_ylabel("km2", fontsize=7); ax2.set_ylabel("km2 (residential areas)", fontsize=7); ax.tick_params(labelsize=6); ax2.tick_params(labelsize=6)
    ax.set_xlim(pd.Timestamp("2023-06-03"), pd.Timestamp("2023-06-24")); ax.grid(alpha=0.3); ax.set_title("areas per day (nominal world)", fontsize=7.5)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=5.3, loc="upper right")
    for lab_ in ax.get_xticklabels():
        lab_.set_rotation(30); lab_.set_ha("right")
    for ax in axs[len(panels) + 1:]:
        ax.axis("off")
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=6.5, frameon=False, bbox_to_anchor=(0.5, -0.045))
    fig.suptitle("Left bank between Kozachi Laheri and Krynky and the floodplain lowland south of Krynky: reconstructed water by day. " + credit, fontsize=7.5)
    FIG.mkdir(parents=True, exist_ok=True); out = FIG / f"p95r_daily_{a.name}.png"; fig.savefig(out, dpi=170, bbox_inches="tight"); plt.close(fig)
    # zoom on the village of Kozachi Laheri
    sl, ex = sub_of(a.zoom)
    zp = [d for d in ("2023-06-05", "2023-06-06", "2023-06-07", "2023-06-08", "2023-06-09", "2023-06-10") if d in store]
    zs = (sl[0].stop - sl[0].start, sl[1].stop - sl[1].start)
    fig, axs = plt.subplots(3, 2, figsize=(2 * 6.4, 3 * 6.4 * zs[0] / zs[1] + 1.0), constrained_layout=True, squeeze=False); axs = axs.ravel()
    for ax, ds in zip(axs, zp):
        draw(ax, ds, sl, ex, zoom=True)
    fig.legend(handles=[h_ for h_ in handles if "lowland box" not in h_.get_label()], loc="lower center", ncol=2, fontsize=6.5, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Kozachi Laheri (village on the Konka): reconstructed water and Michurina street, 5-10 June 2023. 20 m cells: a street-level reading is at the "
                 "limit of the terrain model. " + credit, fontsize=7)
    outz = FIG / f"p95r_daily_{a.name}_kozachi_laheri_zoom.png"; fig.savefig(outz, dpi=170, bbox_inches="tight"); plt.close(fig)
    (TAB / f"p95r_manifest_{a.name}.json").write_text(json.dumps(dict(
        producer="p95r_local_daily_maps.py", run=a.sfx, rev=man.get("rev"), bbox_lonlat=a.bbox, zoom_lonlat=a.zoom,
        window_utm_m=[float(tr.c), float(tr.f - shape[0] * g.cell), float(tr.c + shape[1] * g.cell), float(tr.f)],
        lowland_box=LOWLAND, villages=VILLAGES, osm=dict(cache=str(OSM_CACHE), state=str(OSM_STATE), state_on=OSM_DATE, query=OSM_QUERY, timestamp_osm_base=osm_ts, history_check="every element existed on the state date with the same node list; nodes changed later restored (OSM API history)", licence="(c) OpenStreetMap contributors, ODbL 1.0"),
        days=days, panels=panels, cellprob_days=sorted(cp_n), gate="recomputed P_t minus baseline == daily_new.npz (<= 0.1 km2 over the grid) on every day",
        total_water="P_t of the day: river network and connected pre-breach water plus new water (the W_total of p95e, here on the window)",
        michurina="distance from the rasterised street (all touched 20 m cells) to the nearest cell of new / total water; share of street cells within 40 m"), indent=1))
    print("->", out, outz, round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
