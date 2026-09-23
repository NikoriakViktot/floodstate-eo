# Provenance: SWOT-DNIPRO scripts/p52c_cdse_optical_gap.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 4 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo; importlib load of p52a -> package import.
"""P52c -- what Copernicus actually holds over the three frames during the event, and what we are missing. QUERY ONLY.

The p52b inventory showed the binding constraint is EVENT-window optics: B1 73.8 %, B2 25.7 %, B3 2.9 % of the frame has
at least one valid Sentinel-2 observation between 2023-06-07 and 2023-07-31. Before accepting that, ask the archive:
Copernicus Data Space is queried per frame with an OData spatial intersect and a cloud-cover ceiling, and the result is
compared against what is already on disk. Nothing is downloaded here -- this call only produces the gap list.

The reservoir itself is included as a fourth area (B4): the drawdown of the Kakhovka pool is the other half of the water
balance, and its shrinking water surface needs the same optical record as the flood below the dam.

Cloud ceiling is a QUERY filter, not a per-pixel decision: a 20 % scene still has its own SCL and contributes only the
pixels it actually saw. A scene above the ceiling is not "bad", it is simply not requested first.
Outputs: <case_study>/tables/p52c_cdse_available.csv, p52c_download_gap.csv
"""
from __future__ import annotations
import json, pathlib, sys, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, pyproj, requests
from shapely.geometry import box
from shapely.ops import transform as shp_transform
from .. import _kakhovka_legacy_config as CFG
from ..spatial import p52a_processing_frames_qa as P52A

ODATA = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CLOUD_MAX = 20.0                      # the user's ceiling for the first pass
WINDOWS = {"event": ("2023-06-07", "2023-07-31"),
           "drawdown": ("2023-06-06", "2023-09-30"),   # B4: the pool emptying
           "pre": ("2023-04-01", "2023-06-05")}
TO_LL = pyproj.Transformer.from_crs(CFG.CRS_METRIC, "EPSG:4326", always_xy=True).transform


def token() -> str:
    c = json.loads((pathlib.Path.home() / ".config/cdse/credentials.json").read_text())
    r = requests.post(TOKEN_URL, timeout=60, data={"client_id": "cdse-public", "username": c["username"],
                                                   "password": c["password"], "grant_type": "password"})
    r.raise_for_status()
    return r.json()["access_token"]


def wkt_ll(bbox):
    g = shp_transform(TO_LL, box(*bbox))
    x, y = g.exterior.coords.xy
    return "POLYGON((" + ", ".join(f"{a:.4f} {b:.4f}" for a, b in zip(x, y)) + "))"


def query(fid, bbox, lo, hi, tok, cloud_max=CLOUD_MAX):
    rows, skip = [], 0
    while True:
        f = (f"Collection/Name eq 'SENTINEL-2' and contains(Name,'MSIL2A') "
             f"and OData.CSC.Intersects(area=geography'SRID=4326;{wkt_ll(bbox)}') "
             f"and ContentDate/Start gt {lo}T00:00:00.000Z and ContentDate/Start lt {hi}T23:59:59.999Z "
             f"and Attributes/OData.CSC.DoubleAttribute/any(a:a/Name eq 'cloudCover' and "
             f"a/OData.CSC.DoubleAttribute/Value le {cloud_max:.2f})")
        r = requests.get(ODATA, params={"$filter": f, "$top": 200, "$skip": skip,
                                        "$expand": "Attributes", "$orderby": "ContentDate/Start"},
                         headers={"Authorization": f"Bearer {tok}"}, timeout=180)
        r.raise_for_status()
        vals = r.json().get("value", [])
        for v in vals:
            att = {a["Name"]: a.get("Value") for a in v.get("Attributes", [])}
            nm = v["Name"]
            rows.append(dict(frame=fid, name=nm, product_id=v["Id"],
                             date=v["ContentDate"]["Start"][:10], sensing=v["ContentDate"]["Start"],
                             tile=nm.split("_")[5] if len(nm.split("_")) > 5 else "",
                             cloud=att.get("cloudCover"), size_gb=round(int(v.get("ContentLength") or 0) / 1e9, 2),
                             online=v.get("Online", True)))
        if len(vals) < 200:
            break
        skip += 200
    return rows


def main():
    frames = {fid: f["bbox"] for fid, f in P52A.FRAMES.items()}
    pool = CFG.load_utm("reservoir_full_pool_prebreach").bounds
    frames["B4"] = (float(pool[0]), float(pool[1]), float(pool[2]), float(pool[3]))
    print(f"B4 (Kakhovka pool, for the drawdown / shrinking water surface): "
          f"x {pool[0]:.0f}..{pool[2]:.0f} y {pool[1]:.0f}..{pool[3]:.0f} = {box(*pool).area/1e6:,.0f} km2\n")

    have = {}
    for z in ("ZONE_4_DAM_TO_KHERSON_FLOODWAY", "ZONE_2_KHERSON_DELTA", "ZONE_3_DNIPRO_BUG_ESTUARY",
              "ZONE_1_KAKHOVKA_LOWER_DNIPRO"):
        d = CFG.BULK_ROOT / "zone_spectral" / z
        have[z] = sorted(p.name[:10] for p in d.glob("*_indices.tif")) if d.exists() else []
    on_disk = sorted({x for v in have.values() for x in v})
    print("dates already processed into index stacks, per zone: " +
          ", ".join(f"{z.split('_')[1]}={len(v)}" for z, v in have.items()))

    tok = token(); print("CDSE token acquired", flush=True)
    rows = []
    for fid, bbox in frames.items():
        wins = ("drawdown", "pre") if fid == "B4" else ("event", "pre")
        for w in wins:
            lo, hi = WINDOWS[w]
            try:
                got = query(fid, bbox, lo, hi, tok)
            except Exception as e:
                print(f"  {fid}/{w}: query failed {type(e).__name__}: {str(e)[:120]}", flush=True); continue
            for g in got:
                g["window"] = w
            rows += got
            u = sorted({g["date"] for g in got})
            print(f"  {fid}/{w:8s} {lo}..{hi}: {len(got):4d} products, {len(u):3d} distinct dates, "
                  f"{len([x for x in u if x not in on_disk]):3d} of them NOT in any local stack", flush=True)
    A = pd.DataFrame(rows)
    if A.empty:
        print("no products returned"); return
    A.to_csv(CFG.TABLES / "p52c_cdse_available.csv", index=False)
    A["already_processed"] = A.date.isin(on_disk)
    gap = (A[~A.already_processed].groupby(["frame", "window", "date"])
           .agg(products=("name", "size"), tiles=("tile", lambda s: "|".join(sorted(set(s)))),
                cloud_min=("cloud", "min"), cloud_max=("cloud", "max"), gb=("size_gb", "sum"))
           .reset_index().sort_values(["frame", "window", "date"]))
    gap.to_csv(CFG.TABLES / "p52c_download_gap.csv", index=False)
    pd.set_option("display.width", 240)
    print("\nMISSING DATES (cloud <= %.0f %%), by frame and window:" % CLOUD_MAX)
    for fid in frames:
        g = gap[gap.frame == fid]
        if not len(g):
            print(f"  {fid}: nothing missing"); continue
        print(f"\n  {fid}: {len(g)} dates, {g.products.sum()} products, {g.gb.sum():.1f} GB")
        print(g[["window", "date", "products", "tiles", "cloud_min", "cloud_max", "gb"]].to_string(index=False))
    print(f"\ntotal to fetch: {gap.products.sum()} products, {gap.gb.sum():.1f} GB")
    print("-> <case_study>/tables/p52c_{cdse_available,download_gap}.csv")


if __name__ == "__main__":
    main()
