# Provenance: SWOT-DNIPRO scripts/p80_slc_pairing_manifest.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 18 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo.
"""P80 -- SLC availability and interferometric pairing manifest for frame B2. NOTHING IS DOWNLOADED OR PROCESSED.

WHY A MANIFEST BEFORE A PIPELINE. Coherence is only defined between acquisitions of the same relative orbit and
compatible geometry, and its magnitude is governed by temporal decorrelation: temporal baseline was the dominant
decorrelation factor in Zhao et al. (2024), with the shortest baselines giving the best results. Over agriculture
the situation is worse still -- coherence is itself a function of crop development and phenology (Villarroya-Carpio
et al., 2022), so a pre-event reference pooled over several years mixes phenological states, and pre-flood
coherence over crops may already be low enough that inundation has little room to lower it (Hotaki et al., 2026).
Deciding which pairs exist, and at what baseline, is therefore part of the experimental design and not a detail of
execution. This file produces that table and stops.

THE HYPOTHESIS HAS NO PREDICTED SIGN. This experiment is not "coherence improves agricultural flood detection". It
is: coherence carries information complementary to intensity, with an effect conditional on land cover and temporal
baseline. One study found agricultural baseline coherence already low; another found intensity, not coherence,
carrying irrigated agriculture while coherence carried built-up. The result is reported per stratum and per
baseline without an expected direction.

WHAT THIS CAN AND CANNOT ESTABLISH BEFORE DOWNLOAD. The catalogue gives a product-level footprint, so "coverage"
here is the fraction of the B2 frame inside that footprint. Burst and sub-swath geometry lives in the SAFE
manifest and cannot be checked without fetching it; that check belongs to the next step and is named here rather
than silently assumed.

Outputs: <case_study>/tables/p80_slc_inventory.csv        one row per catalogue product
         <case_study>/tables/p80_slc_pairs.csv            admissible interferometric pairs with temporal baseline
"""
from __future__ import annotations
import argparse, re, sys, time
from pathlib import Path
import numpy as np, pandas as pd, requests
from shapely import wkt as shwkt
from shapely.geometry import box
from pyproj import Transformer
from .. import _kakhovka_legacy_config as CFG
from ..spatial import canonical_grid as CG

ODATA = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
FID = "B2"
LONG = "ZONE_2_KHERSON_DELTA"; JUNE = "ZONE_2_KHERSON_DELTA_flood_june2023"
BREACH = "2023-06-06"; PEAK_LO, PEAK_HI = "2023-06-06", "2023-06-14"
MIN_COVER = 0.20          # a product covering less than this of B2 cannot anchor a frame-wide coherence layer
#: Reported separately rather than filtered: Sentinel-1 repeat is 6 d with two satellites and 12 d with one, and
#: S1B failed in December 2021, so pre-2022 pairs can reach 6 d while 2023 pairs cannot. Mixing those into one
#: feature population would confound baseline with epoch.
BASELINE_BINS = [(0, 6), (7, 12), (13, 24), (25, 10000)]


def frame_lonlat():
    F = CG.frame_grid(FID)
    t = Transformer.from_crs(CFG.CRS_METRIC, "EPSG:4326", always_xy=True)
    x0, y0 = t.transform(F["x0"], F["y0"]); x1, y1 = t.transform(F["x1"], F["y1"])
    return box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def wanted_window(lo, hi):
    """Every calendar day in a window, so the catalogue -- not our intensity cache -- decides what exists.

    THE CACHE IS THE WRONG SAMPLING FRAME FOR COHERENCE. The pre-event scenes in the intensity cache were selected
    to support a robust per-orbit median over years; they are sparse, and restricting pairs to those dates gave
    shortest baselines of 96 and 120 days on two of four orbits. Sentinel-1A alone repeats every 12 days, so a
    12-day pre-event partner exists for every event acquisition and was simply absent from the cache. Searching a
    window recovers it. Baselines of 96-120 days over cropland in the growing season would be measuring crop
    phenology, not inundation.
    """
    d = pd.date_range(lo, hi, freq="D")
    return pd.DataFrame(dict(date=[x.strftime("%Y-%m-%d") for x in d],
                             rel_orbit=-1, direction="", role="WINDOW"))


def wanted():
    """The exact acquisitions the S1 change/coherence chain consumes, taken from the caches."""
    out = []
    for cache, tag in ((LONG, "PRE"), (JUNE, "EVENT")):
        for p in sorted((CFG.S1_CACHE / cache).glob("*.npz")):
            if p.name == "per_scene_water.npz":
                continue
            m = re.search(r"^(\d{4}-\d{2}-\d{2})_orb(\d+)_(ASC|DES)", p.name)
            if not m:
                continue
            dt, orb, dirn = m.group(1), int(m.group(2)), m.group(3)
            if tag == "PRE" and dt >= BREACH:
                continue
            if tag == "EVENT" and not (PEAK_LO <= dt <= PEAK_HI):
                continue
            out.append(dict(date=dt, rel_orbit=orb, direction=dirn, role=tag))
    return pd.DataFrame(out).drop_duplicates(["date", "rel_orbit"]).reset_index(drop=True)


def query_day(day, geom_wkt, session):
    f = (f"Collection/Name eq 'SENTINEL-1' and "
         f"OData.CSC.Intersects(area=geography'SRID=4326;{geom_wkt}') and "
         f"ContentDate/Start gt {day}T00:00:00.000Z and ContentDate/Start lt {day}T23:59:59.999Z and "
         f"contains(Name,'SLC')")
    for attempt in range(5):
        try:
            r = session.get(ODATA, params={"$filter": f, "$top": "50", "$expand": "Attributes"}, timeout=90)
            if r.status_code == 200:
                return r.json().get("value", [])
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(3 * (attempt + 1)); continue
            r.raise_for_status()
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
    return None                                   # distinguished from [] -- a failed query is not an empty result


def attr(p, name):
    for a in p.get("Attributes", []):
        if a.get("Name") == name:
            return a.get("Value")
    return None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sleep", type=float, default=0.4)
    ap.add_argument("--window", nargs=2, metavar=("LO", "HI"),
                    help="scan every day in this range instead of the intensity-cache dates")
    a = ap.parse_args()
    B2 = frame_lonlat(); gw = B2.wkt
    W = wanted_window(*a.window) if a.window else wanted()
    print(f"{FID}: {len(W)} acquisitions consumed by the S1 change/coherence chain "
          f"({(W.role == 'PRE').sum()} pre, {(W.role == 'EVENT').sum()} event) on "
          f"{W.rel_orbit.nunique()} relative orbits", flush=True)
    s = requests.Session(); s.headers["Accept"] = "application/json"
    rows = []; failed = []
    for i, r in enumerate(W.itertuples()):
        v = query_day(r.date, gw, s)
        if v is None:
            failed.append(r.date); continue
        for p in v:
            try:
                fp = shwkt.loads(p["Footprint"].split(";")[-1].strip("'"))
                cov = fp.intersection(B2).area / B2.area
            except Exception:
                cov = np.nan
            ro = attr(p, "relativeOrbitNumber")
            rows.append(dict(date=r.date, role=r.role, cache_rel_orbit=r.rel_orbit, cache_direction=r.direction,
                             product_id=p.get("Id"), name=p.get("Name"),
                             sensing_start=p.get("ContentDate", {}).get("Start"),
                             rel_orbit=int(ro) if ro is not None else None,
                             direction=attr(p, "orbitDirection"), mode=attr(p, "operationalMode"),
                             polarisation=attr(p, "polarisationChannels"),
                             platform=attr(p, "platformSerialIdentifier"),
                             online=p.get("Online"), size_gb=round((p.get("ContentLength") or 0) / 1e9, 2),
                             b2_footprint_cover=round(float(cov), 4) if np.isfinite(cov) else np.nan))
        time.sleep(a.sleep)
        if (i + 1) % 20 == 0:
            print(f"  queried {i+1}/{len(W)}", flush=True)
    if failed:
        print(f"WARNING: {len(failed)} catalogue queries failed and are NOT recorded as absent: "
              f"{failed[:6]}{' ...' if len(failed) > 6 else ''}", flush=True)
    I = pd.DataFrame(rows)
    if I.empty:
        raise SystemExit("no SLC products returned -- do not proceed as though none exist; re-run the query")
    if a.window:
        I["role"] = np.where(I.date >= PEAK_LO, np.where(I.date <= PEAK_HI, "EVENT", "POST"), "PRE")
        I["orbit_matches_cache"] = True
    else:
        I["orbit_matches_cache"] = I.rel_orbit == I.cache_rel_orbit
    I["usable"] = (I.b2_footprint_cover >= MIN_COVER) & I.orbit_matches_cache & (I["mode"] == "IW")
    I.to_csv(CFG.TABLES / "p80_slc_inventory.csv", index=False)
    print(f"\ninventory: {len(I)} products, {int(I.usable.sum())} usable "
          f"(IW, orbit matches the intensity cache, >= {MIN_COVER:.0%} of B2)")
    print(I[I.usable].groupby(["rel_orbit", "direction", "role"]).size().to_string())

    U = I[I.usable]
    pairs = []
    for (ro, dr), g in U.groupby(["rel_orbit", "direction"]):
        ev = g[g.role == "EVENT"]; pre = g[g.role == "PRE"]
        for e in ev.itertuples():
            for p in pre.itertuples():
                dt = (pd.Timestamp(e.date) - pd.Timestamp(p.date)).days
                pairs.append(dict(rel_orbit=ro, direction=dr, event_date=e.date, pre_date=p.date,
                                  temporal_baseline_days=dt,
                                  event_id=e.product_id, pre_id=p.product_id,
                                  same_platform=e.platform == p.platform,
                                  min_cover=round(min(e.b2_footprint_cover, p.b2_footprint_cover), 4)))
    P = pd.DataFrame(pairs)
    if P.empty:
        raise SystemExit("no admissible pairs -- coherence cannot be formed; stop rather than relax the geometry")
    P["baseline_bin"] = pd.cut(P.temporal_baseline_days,
                               bins=[b[0] - 1 for b in BASELINE_BINS] + [BASELINE_BINS[-1][1]],
                               labels=[f"{lo}-{hi}d" for lo, hi in BASELINE_BINS])
    P = P.sort_values(["rel_orbit", "event_date", "temporal_baseline_days"]).reset_index(drop=True)
    P.to_csv(CFG.TABLES / "p80_slc_pairs.csv", index=False)
    print(f"\n{len(P)} admissible pairs (same relative orbit, same direction, both covering B2)")
    print(P.groupby(["rel_orbit", "baseline_bin"], observed=True).size().unstack(fill_value=0).to_string())
    print("\nshortest baseline available per orbit (shortest is best):")
    print(P.loc[P.groupby("rel_orbit").temporal_baseline_days.idxmin(),
                ["rel_orbit", "event_date", "pre_date", "temporal_baseline_days", "same_platform"]]
          .to_string(index=False))
    print("\nNOT ESTABLISHED HERE: burst and sub-swath compatibility, which needs the SAFE manifest.")
    print("-> <case_study>/tables/p80_slc_inventory.csv, p80_slc_pairs.csv")


if __name__ == "__main__":
    main()
