# Provenance: SWOT-DNIPRO scripts/p81_fetch_slc.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 19 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo; `.env` is now loaded from this repo's root
# (CFG.REPO_ROOT), not SWOT-DNIPRO's -- a floodstate-eo `.env` with the same CDSE credential variable names is
# required for this script to authenticate. DEST and SLC/WORK-style absolute host paths are left hard-coded
# exactly as in the source (per-machine data locations, listed as "to become config later" in
# 06_CONFIGURATION_DESIGN.md; Phase 6 work).
"""P81 -- fetch the frozen Sentinel-1 SLC set for the coherence experiment.

SCOPE IS FROZEN BEFORE DOWNLOAD, by p80: 5 acquisitions on each of 4 relative orbits, spaced at exactly 12 days
with no gap, giving per orbit three pre-only 12-day coherence pairs and one pre/event 12-day pair. 30 products,
237 GB. Nothing here re-derives that scope -- it reads p80_c1_frozen_products.csv and refuses anything not in it,
so the experiment cannot quietly grow a longer baseline or an extra orbit while data is being fetched.

WHY NOT THE BULK VOLUME. The designated bulk drive can run near capacity and is not necessarily viable for SNAP's
GeoTIFF writer (which seeks per row); the local ext4 root is used instead, and raw SAFE archives are kept, not
deleted after preprocessing, so that the provenance chain immutable SAFE -> SNAP graph -> derived coherence ->
model features can be re-walked later.

WHAT THIS DOES NOT DO: no unzip, no SNAP, no processing. Download and verify only. Burst and sub-swath
compatibility is checked after the pilot's SAFE manifests are on disk -- p80 could not establish it from the
catalogue and said so rather than assuming it.
"""
from __future__ import annotations
import argparse, os, sys, time
from pathlib import Path
import pandas as pd, requests
from dotenv import load_dotenv
from .. import _kakhovka_legacy_config as CFG

FROZEN = CFG.TABLES / "p80_c1_frozen_products.csv"
DEST = Path("/home/niko/data_s1_slc")
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
DOWNLOAD = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products({pid})/$value"
CHUNK = 8 << 20
#: keep this much ext4 free at all times; SNAP's coregistration products are several times the SAFE size and a
#: full disk during a large transfer costs the transfer, not just the margin
RESERVE_GB = 120


def token():
    load_dotenv(str(CFG.REPO_ROOT / ".env"))
    r = requests.post(TOKEN_URL, timeout=60, data={
        "client_id": "cdse-public", "grant_type": "password",
        "username": os.getenv("username_CDSE"), "password": os.getenv("password_CDSE")})
    r.raise_for_status()
    return r.json()["access_token"]


def free_gb(p: Path) -> float:
    s = os.statvfs(p)
    return s.f_bavail * s.f_frsize / 1e9


def open_authed(sess, url, hdr, max_hops=5):
    """Follow redirects MANUALLY, re-attaching Authorization on every hop.

    requests strips the Authorization header when a redirect crosses to a different host -- deliberate, and
    correct in general. Copernicus answers the catalogue URL with 301 to download.dataspace.copernicus.eu, so the
    bearer token is dropped exactly once and every product returns 401. Measured: allow_redirects=True gives 401
    with one 301 in .history; the same request followed by hand with the header re-attached gives 200 and a
    correctly sized body. A Range header must survive the hop too, or a resume silently restarts from zero.
    """
    u = url
    for _ in range(max_hops):
        r = sess.get(u, headers=hdr, stream=True, allow_redirects=False, timeout=(30, 300))
        if r.status_code in (301, 302, 303, 307, 308) and "Location" in r.headers:
            u = r.headers["Location"]; r.close(); continue
        return r
    raise RuntimeError(f"more than {max_hops} redirects for {url}")


def fetch(pid, name, want_gb, sess):
    out = DEST / f"{name}.zip"
    part = out.with_suffix(".zip.part")
    if out.exists() and abs(out.stat().st_size / 1e9 - want_gb) < 0.05:
        print(f"  {name[:56]}  already complete", flush=True)
        return True, out.stat().st_size
    have = part.stat().st_size if part.exists() else 0
    hdr = {"Authorization": f"Bearer {token()}"}
    if have:
        hdr["Range"] = f"bytes={have}-"
        print(f"  resuming at {have/1e9:.2f} GB", flush=True)
    t0 = time.time()
    r = open_authed(sess, DOWNLOAD.format(pid=pid), hdr)
    # MEASURED: the Copernicus download endpoint answers a Range request with 501 Not Implemented -- it does not
    # support partial content, so an interrupted transfer cannot be resumed and must start again. The retry is
    # explicit rather than a silent fall-through, because a server that ignored Range and replied 200 would
    # otherwise have appended a whole file onto a partial one and produced a corrupt archive that still had a
    # plausible size. Both failure modes are handled here: 501 restarts, and a 200 answer to a Range request
    # truncates rather than appends.
    if r.status_code == 501 and "Range" in hdr:
        r.close()
        print(f"  server refuses Range (501); restarting from 0, discarding {have/1e9:.2f} GB", flush=True)
        hdr.pop("Range"); have = 0
        part.unlink(missing_ok=True)
        r = open_authed(sess, DOWNLOAD.format(pid=pid), hdr)
    with r:
        if r.status_code not in (200, 206):
            print(f"  HTTP {r.status_code} for {name[:50]}", flush=True)
            return False, 0
        mode = "ab" if (have and r.status_code == 206) else "wb"
        if mode == "wb":
            have = 0
        with open(part, mode) as fh:
            n = have; last = t0
            for c in r.iter_content(CHUNK):
                fh.write(c); n += len(c)
                if time.time() - last > 60:
                    print(f"    {n/1e9:6.2f}/{want_gb:.2f} GB  {n/1e6/(time.time()-t0):6.1f} MB/s", flush=True)
                    last = time.time()
    got = part.stat().st_size
    # size is the only integrity signal the catalogue gives us here; a truncated transfer must not be renamed
    if abs(got / 1e9 - want_gb) > 0.05:
        print(f"  SIZE MISMATCH {got/1e9:.2f} GB vs catalogue {want_gb:.2f} GB -- left as .part", flush=True)
        return False, got
    part.rename(out)
    print(f"  {name[:56]}  {got/1e9:.2f} GB in {time.time()-t0:.0f}s", flush=True)
    return True, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orbits", nargs="*", type=int, help="restrict to these relative orbits (pilot: 65)")
    ap.add_argument("--jobs", type=int, default=4, help="concurrent transfers; capped at 4 by Copernicus policy")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    P = pd.read_csv(FROZEN)
    if a.orbits:
        P = P[P.rel_orbit.isin(a.orbits)]
    P = P.sort_values(["rel_orbit", "date"]).reset_index(drop=True)
    need = float(P.size_gb.sum())
    DEST.mkdir(parents=True, exist_ok=True)
    have = free_gb(DEST)
    print(f"{len(P)} products, {need:.1f} GB -> {DEST}")
    print(f"ext4 free {have:.0f} GB; after download {have-need:.0f} GB, reserve {RESERVE_GB} GB")
    if have - need < RESERVE_GB:
        raise SystemExit(f"refusing: would leave {have-need:.0f} GB, below the {RESERVE_GB} GB reserve that SNAP "
                         f"coregistration needs. Reduce the scope or free space first.")
    if a.dry_run:
        print(P[["rel_orbit", "date", "name", "size_gb"]].to_string(index=False)); return
    # Throughput varies by an order of magnitude between products and over time: a first serial sample sustained
    # only 2.3 MB/s, while a later transfer running alongside three others completed at 12.1 MB/s, with concurrent
    # streams observed anywhere from 3.2 to 12.1 MB/s -- server-side variability, NOT a per-connection cap.
    # Concurrency is still worth having, because several variable streams average out and a slow one no longer
    # blocks the queue; it is not a way around a throttle that does not exist. The pool is capped at four because
    # Copernicus publishes that quota, and never raised "just to see": exceeding a published quota is how an
    # account gets throttled for everyone using it.
    jobs = min(a.jobs, 4)
    ok = 0; got = 0
    from concurrent.futures import ThreadPoolExecutor, as_completed
    def one(i, r):
        s = requests.Session()
        print(f"[{i}/{len(P)}] orbit {r.rel_orbit} {r.date} start", flush=True)
        return fetch(r.product_id, r.name, float(r.size_gb), s)
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        fut = {ex.submit(one, i, r): r for i, r in enumerate(P.itertuples(), 1)}
        for f in as_completed(fut):
            good, n = f.result()
            ok += good; got += n
            if free_gb(DEST) < RESERVE_GB:
                for g in fut:
                    g.cancel()
                raise SystemExit(f"stopping: ext4 free fell to {free_gb(DEST):.0f} GB")
    print(f"\n{ok}/{len(P)} complete, {got/1e9:.1f} GB, ext4 free {free_gb(DEST):.0f} GB")
    if ok < len(P):
        raise SystemExit("incomplete -- re-run to resume; do not start SNAP on a partial set")


if __name__ == "__main__":
    main()
