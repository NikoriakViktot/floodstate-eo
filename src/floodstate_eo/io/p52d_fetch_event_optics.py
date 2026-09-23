# Provenance: SWOT-DNIPRO scripts/p52d_fetch_event_optics.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 5 (migration_phase=5).
#
# MIGRATION TODO / UNRESOLVED DEPENDENCY (provenance/UNRESOLVED_DEPENDENCIES.md): the source script loads
# `scripts/p1_targeted_fetch.py` via importlib for `verified()`, `KeepAuth`, `verify()` and `sidecar()` -- the
# hardened download/verify/atomic-publish helpers. That file is NOT in 19_MIGRATION_MANIFEST.csv (it is a
# general SWOT-DNIPRO fetch utility, not classified CANONICAL/CORE_LIBRARY for floodstate-eo), so it was not
# pulled in silently. `P1F` is left `None` below: `fetch()` will raise `AttributeError` if actually called,
# which is the honest behaviour for a dependency that has not been migrated yet, rather than a working stub
# that fakes integrity checking. Porting or reimplementing those four helpers is Phase 6 work.
"""P52d -- PASS 1: fetch the missing Sentinel-2 L2A scenes over B1/B2/B3 for the flood-event window.

p52b measured the binding constraint: EVENT-window optical coverage is 73.8 % of B1, 25.7 % of B2 and 2.9 % of B3.
p52c then asked Copernicus and found the shortfall is not the archive -- for B3 all twelve available event dates at
cloudCover <= 20 % are simply absent locally. The same class of mistake as a missing derived per-scene product: an
un-fetched product read as an un-observed place.

This is PASS 1 only: cloudCover <= 20 % over B1/B2/B3, event window. It is a QUERY-level ceiling on the whole product,
not a per-pixel decision -- SCL still decides every pixel afterwards. PASS 2 (20-60 % cloud, ranked by the incremental
clear coverage each product actually adds inside the frames) comes after the coverage of PASS 1 is measured, and B4
(the reservoir drawdown) is a separate stage that must not hold up the flood map.

Everything lands on the bulk volume, never the repository disk. Integrity is meant to follow the hardened path from
p1_targeted_fetch (see the MIGRATION TODO above): download to `.part`, verify the ZIP's per-member CRC, publish
atomically, memoise the verdict in a sidecar. An aborted download can never be mistaken for a cache hit.
Outputs: $BULK_ROOT/sentinel_event_2023/*.SAFE.zip (+ .verified.json), <case_study>/tables/p52d_fetch_ledger.csv
"""
from __future__ import annotations
import json, os, pathlib, sys, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
import pandas as pd, requests
from .. import _kakhovka_legacy_config as CFG

P1F = None  # MIGRATION TODO: scripts/p1_targeted_fetch.py not in migration scope -- see module header

ODATA = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
RAW = CFG.BULK_ROOT / "sentinel_event_2023"          # bulk volume only
LIST = CFG.TABLES / "p52d_pass1_download_list.csv"   # overridden by --list (PASS 2 uses p52f_b2_download_list.csv)
MAX_RETRIES = 6


def token() -> str:
    c = json.loads((pathlib.Path.home() / ".config/cdse/credentials.json").read_text())
    r = requests.post(TOKEN_URL, timeout=60, data={"client_id": "cdse-public", "username": c["username"],
                                                   "password": c["password"], "grant_type": "password"})
    r.raise_for_status()
    return r.json()["access_token"]


def fetch(row, tok_box):
    name = row["name"].replace(".SAFE", "")
    zpath = RAW / f"{name}.SAFE.zip"; part = zpath.with_name(zpath.name + ".part")
    if zpath.exists() and P1F.verified(zpath)["complete"]:
        return dict(status="ALREADY_CACHED", path=str(zpath), size_bytes=zpath.stat().st_size)
    url = f'{ODATA}({row["product_id"]})/$value'
    t0 = time.time()
    for attempt in range(1, MAX_RETRIES + 1):
        s = P1F.KeepAuth(); s.headers.update({"Authorization": f"Bearer {tok_box[0]}"})
        try:
            with s.get(url, stream=True, timeout=1800, allow_redirects=True) as resp:
                if resp.status_code in (401, 403):
                    tok_box[0] = token(); continue
                if resp.status_code == 429:
                    w = min(30 * attempt, 180); print(f"    429, backing off {w}s", flush=True); time.sleep(w); continue
                resp.raise_for_status()
                n = 0
                with open(part, "wb") as fh:
                    for ch in resp.iter_content(1 << 20):
                        if ch:
                            fh.write(ch); n += len(ch)
            break
        except Exception as exc:
            if attempt == MAX_RETRIES:
                return dict(status=f"FAILED:{type(exc).__name__}", path="", size_bytes=0)
            w = min(20 * attempt, 120)
            print(f"    {type(exc).__name__}, retry in {w}s ({attempt}/{MAX_RETRIES})", flush=True); time.sleep(w)
    else:
        return dict(status="FAILED:retries", path="", size_bytes=0)
    v = P1F.verify(part)
    dt = time.time() - t0
    if not v["complete"]:
        return dict(status=f"VERIFY_FAILED crc_ok={v['crc_ok']} bands={v['bands_present']}", path=str(part),
                    size_bytes=v["size_bytes"], seconds=round(dt, 1))
    os.replace(part, zpath)
    P1F.sidecar(zpath).write_text(json.dumps({**v, "mtime": zpath.stat().st_mtime}, indent=1))
    return dict(status="OK", path=str(zpath), size_bytes=v["size_bytes"], sha256=v["sha256"],
                bands=v["bands_present"], seconds=round(dt, 1), mb_s=round(v["size_bytes"] / 1e6 / max(dt, 1), 1))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default=str(LIST), help="download list CSV: name, product_id, date, tile, cloud, size_gb")
    ap.add_argument("--tag", default="PASS 1")
    a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    L = pd.read_csv(a.list).drop_duplicates("name").sort_values("date").reset_index(drop=True)
    print(f"{a.tag}: {len(L)} products, {L.size_gb.sum():.1f} GB -> {RAW}")
    print(f"frames B1/B2/B3, event window, cloudCover <= 20 % (a QUERY ceiling; SCL still decides per pixel)\n", flush=True)
    tok_box = [token()]; rows = []; t0 = time.time(); done_gb = 0.0
    for i, r in L.iterrows():
        print(f"[{i+1:2d}/{len(L)}] {r['date']} {r['tile']} cloud {r['cloud']:.1f} % {r['size_gb']:.2f} GB", flush=True)
        res = fetch(r, tok_box)
        rows.append({**{k: r[k] for k in ("name", "product_id", "date", "tile", "cloud", "size_gb", "frame")}, **res})
        done_gb += r["size_gb"]
        print(f"    -> {res['status']}" + (f"  {res.get('mb_s','')} MB/s" if res.get("mb_s") else "") +
              f"   [{done_gb:.1f}/{L.size_gb.sum():.1f} GB, {(time.time()-t0)/60:.0f} min]", flush=True)
        pd.DataFrame(rows).to_csv(CFG.TABLES / f"p52d_fetch_ledger_{a.tag.replace(chr(32),chr(95)).lower()}.csv", index=False)
    D = pd.DataFrame(rows)
    ok = (D.status == "OK").sum(); cached = (D.status == "ALREADY_CACHED").sum()
    print(f"\nOK {ok}, already cached {cached}, other {len(D)-ok-cached} of {len(D)}")
    bad = D[~D.status.isin(["OK", "ALREADY_CACHED"])]
    if len(bad):
        print("NOT COMPLETE:"); print(bad[["date", "tile", "name", "status"]].to_string(index=False))
    print(f"-> {RAW}\n-> <case_study>/tables/p52d_fetch_ledger.csv   ({(time.time()-t0)/60:.0f} min)")


if __name__ == "__main__":
    main()
