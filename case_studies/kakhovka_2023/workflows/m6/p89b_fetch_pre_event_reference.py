# New in floodstate-eo, 2026-09-24. STATUS: ACTIVE. Pre-event S1 reference-water observations for label v003.
"""P89b -- fetch Sentinel-1 RTC scenes from BEFORE the June caches (2023-04-15..2023-05-31) for B1/B2 and classify
water with EXACTLY the method that produced the June per_scene_water masks.

WHY. The p89 audit showed group-A field candidates are water on 06-01/06-02 (before the breach) with no independent
confirmation in the repository. Those two dates are the planned U2b INPUT (W_pre); a label for "water before the event"
built from them would be circular. Earlier S1 (e.g. 2023-05-16 and 05-28, used by SERTIT for Kakhovka) is an
independent observation of the same pre-event state.

SAME SOURCE, SAME GRID, SAME CLASSIFIER, PROVEN, NOT ASSUMED
- source: Planetary Computer `sentinel-1-rtc` (as p0o / hist25b_gate6_event_qualification.build_event): every asset of
  one overpass averaged onto the cache grid, mosaicked in datetime order, seam discrepancy measured
- grid: taken from the June cache's own per_scene_water.npz (x0, y1, cell, shape) -- not rebuilt from today's
  geometries, which have changed since the cache was made
- classifier: p0r `water_mask` -- VV/VH dB linear discriminant fitted on fixed anchors (water: dnipro_water_domain
  buffered -200 m; land: domain minus 6 km around the water), parts < 0.05 km2 removed, valid = coverage & domain
- REPRODUCTION GATE: 06-01 and 06-02 are fetched fresh and classified the same way; the result must agree with the
  cached June masks (valid agreement and water IoU above GATE) or no pre-event mask is written.
Note: dnipro_water_domain is WorldCover-derived and anchors the S1 classifier exactly as it already did for every June
mask (and hence for p60 / v002); it is not a new land-cover input to the labels.

Outputs: $S1_CACHE/<JUNE>_pre2023/<event>.npz (vv, vh, cov, seam) and per_scene_water.npz (June layout: shape, cell,
         x0, y1, <event>, valid_<event> packed); <case_study>/tables/p89b_{scenes,reproduction_gate}.csv
"""
from __future__ import annotations
import argparse, json, time, urllib.request
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.windows import from_bounds
from scipy import ndimage
from shapely.geometry import shape
from shapely.ops import unary_union
from pyproj import Transformer
from floodstate_eo import _kakhovka_legacy_config as CFG

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
SAS = "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-1-rtc"
DOM = CFG._SWOT_DNIPRO_SIBLING / "data" / "processed" / "domains"
JUNE = {"B1": "ZONE_4_FLOODWAY_june2023_s32", "B2": "ZONE_2_KHERSON_DELTA_flood_june2023"}
WINDOW = ("2023-04-15", "2023-06-02")         # includes 06-01/06-02 for the reproduction gate only
GATE_DATES = ("2023-06-01", "2023-06-02")
GATE = dict(valid_agreement=0.97, water_iou=0.85)
MIN_PART_KM2, CELL = 0.05, 20.0


def geom_of(fid):
    zones = json.loads((DOM / "analysis_zones_utm.geojson").read_text())["features"]
    zone = lambda n: unary_union([shape(f["geometry"]) for f in zones if f["properties"]["analysis_zone"] == n])
    if fid == "B2":                                            # p0w: z = ZONE_2
        return zone("ZONE_2_KHERSON_DELTA")
    subs = json.loads((DOM / "analysis_subzones_utm.geojson").read_text())["features"]
    core = unary_union([shape(f["geometry"]) for f in subs
                        if f["properties"]["analysis_subzone"] == "KAKHOVKA_DAM_TO_KHERSON"])
    return core.buffer(32_000.0).intersection(zone("ZONE_1_KAKHOVKA_LOWER_DNIPRO"))   # p0v: s32


def grid_of(fid):
    z = np.load(CFG.S1_CACHE / JUNE[fid] / "per_scene_water.npz", allow_pickle=True)
    ny, nx = (int(v) for v in z["shape"]); cell = float(z["cell"]); x0, y1 = float(z["x0"]), float(z["y1"])
    tr = from_origin(x0, y1, cell, cell)
    # read_asset windows on (x0, y0, x1, y1) with x1/y0 the LAST cell-centre coordinates, exactly as p0o built G
    return dict(x0=x0, y1=y1, x1=x0 + cell * (nx - 1), y0=y1 - cell * (ny - 1), nx=nx, ny=ny, tr=tr, cell=cell), z


def http_json(url, payload=None, tries=6, timeout=180):
    last = None
    for a in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload else None,
                                         headers={"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        except Exception as ex:
            last = ex; time.sleep(min(60, 4 * 2 ** a))
    raise RuntimeError(f"{type(last).__name__}: {last}")


def token():
    return http_json(SAS)["token"]


def catalogue(bbox):
    feats, body = [], {"collections": ["sentinel-1-rtc"], "bbox": bbox, "limit": 200,
                       "datetime": f"{WINDOW[0]}T00:00:00Z/{WINDOW[1]}T23:59:59Z"}
    while True:
        j = http_json(STAC, body); feats += j["features"]
        nxt = [l for l in j.get("links", []) if l.get("rel") == "next"]
        if not nxt or not nxt[0].get("body", {}).get("token"):
            break
        body = {**body, "token": nxt[0]["body"]["token"]}
    ev = {}
    for f in feats:
        p = f["properties"]; st = str(p.get("sat:orbit_state", "")).lower()
        st = "ASC" if st.startswith("asc") else "DES" if st.startswith("des") else None
        if st is None:
            raise ValueError(f"unrecognised orbit state in {f['id']}")
        ev.setdefault((p["datetime"][:10], int(p["sat:relative_orbit"]), st), []).append(f)
    return ev


def read_asset(item, tok, G, pol):
    with rasterio.open(item["assets"][pol]["href"] + "?" + tok) as ds:
        arr = ds.read(1, window=from_bounds(G["x0"], G["y0"], G["x1"], G["y1"], ds.transform),
                      out_shape=(G["ny"], G["nx"]), resampling=Resampling.average, boundless=True, fill_value=np.nan)
    return arr.astype(np.float32)


def build_event(items, tok, G):
    db = lambda a: 10 * np.log10(np.maximum(a, 1e-6))
    vv = np.full((G["ny"], G["nx"]), np.nan, np.float32); vh = vv.copy(); seams = []
    for it in sorted(items, key=lambda f: f["properties"]["datetime"]):
        a_vv, a_vh = read_asset(it, tok, G, "vv"), read_asset(it, tok, G, "vh")
        m = np.isfinite(a_vv) & (a_vv > 0) & np.isfinite(a_vh) & (a_vh > 0)
        ov = m & np.isfinite(vv)
        if ov.sum() > 5000:
            seams.append(float(np.median(np.abs(db(a_vv[ov]) - db(vv[ov])))))
        new = m & ~np.isfinite(vv); vv[new] = a_vv[new]; vh[new] = a_vh[new]
    return vv, vh, np.isfinite(vv) & np.isfinite(vh), (float(np.median(seams)) if seams else np.nan)


def water_mask(vv, vh, cov, anchor_w, anchor_l):
    """p0r_zone2_flood_envelope.water_mask, verbatim logic."""
    d_vv = 10 * np.log10(np.maximum(vv, 1e-6)); d_vh = 10 * np.log10(np.maximum(vh, 1e-6))
    aw = anchor_w & cov & np.isfinite(d_vv) & np.isfinite(d_vh)
    al = anchor_l & cov & np.isfinite(d_vv) & np.isfinite(d_vh)
    if aw.sum() < 2000 or al.sum() < 2000:
        return None, np.nan
    Xw, Xl = np.c_[d_vv[aw], d_vh[aw]], np.c_[d_vv[al], d_vh[al]]
    mw, ml = Xw.mean(0), Xl.mean(0)
    S = np.cov(Xw.T) + np.cov(Xl.T) + np.eye(2) * 1e-6
    w = np.linalg.solve(S, ml - mw); cut = 0.5 * (w @ mw + w @ ml)
    disc = np.full(vv.shape, np.nan, np.float32); ok = cov & np.isfinite(d_vv) & np.isfinite(d_vh)
    disc[ok] = (np.c_[d_vv[ok], d_vh[ok]] @ w) - cut
    if np.nanmedian(disc[aw]) > np.nanmedian(disc[al]):
        disc = -disc
    m = (disc < 0) & ok
    px = CELL ** 2 / 1e6
    lab, n = ndimage.label(m, structure=np.ones((3, 3), int))
    if n:
        sz = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)) * px
        keep = np.zeros(n + 1, bool); keep[1:] = sz >= MIN_PART_KM2; m = keep[lab]
    return m, float(np.nanmedian(disc[al]) - np.nanmedian(disc[aw]))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=["B1", "B2"]); a = ap.parse_args()
    wdom_all = unary_union([shape(f["geometry"]) for f in
                            json.loads((DOM / "dnipro_water_domain_utm.geojson").read_text())["features"]])
    to4326 = Transformer.from_crs(32636, 4326, always_xy=True)
    scenes, gate = [], []
    for fid in a.frames:
        G, cached = grid_of(fid); z = geom_of(fid)
        shp_ = (G["ny"], G["nx"])
        inside = rasterize([(z, 1)], out_shape=shp_, transform=G["tr"], fill=0, dtype="uint8").astype(bool)
        wdom = wdom_all.intersection(z)
        anchor_w = rasterize([(wdom.buffer(-200.0), 1)], out_shape=shp_, transform=G["tr"], fill=0, dtype="uint8").astype(bool)
        anchor_l = rasterize([(z.difference(wdom.buffer(6000.0)), 1)], out_shape=shp_, transform=G["tr"], fill=0,
                             dtype="uint8").astype(bool)
        # the cached valid masks must sit inside the domain we rebuilt -- otherwise the domain is not the June one
        cv = np.zeros(shp_, bool)
        for k in [k for k in cached.keys() if k.startswith("valid_")]:
            cv |= np.unpackbits(cached[k], count=shp_[0] * shp_[1]).reshape(shp_).astype(bool)
        outside = float((cv & ~inside).sum() / max(cv.sum(), 1))
        print(f"{fid}: grid {shp_}, domain check: {outside:.4%} of cached valid pixels fall outside the rebuilt domain",
              flush=True)
        if outside > 0.01:
            raise SystemExit(f"{fid}: rebuilt domain does not contain the June cache's valid pixels -- stop")
        xs, ys = to4326.transform([G["x0"], G["x1"]], [G["y0"], G["y1"]])
        ev = catalogue([min(xs), min(ys), max(xs), max(ys)])
        cdir = CFG.S1_CACHE / f"{JUNE[fid]}_pre2023"; cdir.mkdir(exist_ok=True)
        tok, t_tok = token(), time.time(); packed = {}
        for (date, orb, st), items in sorted(ev.items()):
            eid = f"{date}_orb{orb}_{st}"
            if time.time() - t_tok > 1500:
                tok, t_tok = token(), time.time()
            npz = cdir / f"{eid}.npz"
            if npz.exists():
                zz = np.load(npz); vv, vh, cov, seam = zz["vv"], zz["vh"], zz["cov"], float(zz["seam"])
            else:
                t0 = time.time()
                vv, vh, cov, seam = build_event(items, tok, G)
                np.savez_compressed(npz, vv=vv, vh=vh, cov=cov, seam=seam)
                print(f"  {fid} {eid}: {len(items)} granule(s) fetched in {time.time() - t0:.0f}s", flush=True)
            valid = cov & inside
            if valid.mean() < 0.01 * inside.mean():
                npz.unlink(missing_ok=True); continue
            m, sep = water_mask(vv, vh, valid, anchor_w, anchor_l)
            if m is None:
                continue
            scenes.append(dict(frame=fid, event=eid, date=date, rel_orbit=orb, state=st, granules=len(items),
                               valid_km2=round(float(valid.sum()) * 4e-4, 1), water_km2=round(float((m & valid).sum()) * 4e-4, 1),
                               lda_separation=round(sep, 3), seam_db=round(seam, 3) if np.isfinite(seam) else None,
                               role="GATE" if date in GATE_DATES else "PRE_REFERENCE"))
            if date in GATE_DATES:
                key = next((k for k in cached.keys() if k.startswith(eid)), None)
                if key is None:
                    continue
                cw = np.unpackbits(cached[key], count=shp_[0] * shp_[1]).reshape(shp_).astype(bool)
                cvv = np.unpackbits(cached["valid_" + key], count=shp_[0] * shp_[1]).reshape(shp_).astype(bool)
                both = cvv & valid
                gate.append(dict(frame=fid, event=eid,
                                 valid_agreement=round(float((cvv == valid)[inside].mean()), 4),
                                 water_agreement_on_common_valid=round(float((cw == m)[both].mean()), 4),
                                 water_iou=round(float((cw & m & both).sum() / max(((cw | m) & both).sum(), 1)), 4)))
                print(f"  GATE {fid} {eid}: {gate[-1]}", flush=True)
                continue
            packed[eid] = np.packbits((m & valid).ravel()); packed["valid_" + eid] = np.packbits(valid.ravel())
        G_ = [g for g in gate if g["frame"] == fid]
        ok = G_ and all(g["valid_agreement"] >= GATE["valid_agreement"] and g["water_iou"] >= GATE["water_iou"] for g in G_)
        if not ok:
            print(f"{fid}: REPRODUCTION GATE FAILED {G_} -- pre-event masks NOT written", flush=True)
            continue
        np.savez_compressed(cdir / "per_scene_water.npz", shape=np.array(shp_), cell=G["cell"], x0=G["x0"], y1=G["y1"],
                            **packed)
        print(f"{fid}: reproduction gate PASS; {len([k for k in packed if not k.startswith('valid_')])} pre-event "
              f"masks -> {cdir / 'per_scene_water.npz'}", flush=True)
    pd.DataFrame(scenes).to_csv(CFG.TABLES / "p89b_scenes.csv", index=False)
    pd.DataFrame(gate).to_csv(CFG.TABLES / "p89b_reproduction_gate.csv", index=False)


if __name__ == "__main__":
    main()
