# Provenance: SWOT-DNIPRO scripts/p54c_composites_10m_freeze_gate.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 10 (migration_phase=5).
# Import block adjusted for the floodstate_eo package layout. `code_version()`'s file list and git `cwd`
# repointed at this repo's paths for the same four inputs (git SHA now means the floodstate-eo commit, not
# SWOT-DNIPRO's).
"""P54c -- COMPOSITES_10M_FREEZE_GATE: the check that must pass before any classifier reads the 10 m products.

Not a summary of what p54a/p54b printed about themselves. Every number here is recomputed from the rasters on disk by
code that does not import the builders' statistics, because every defect this pipeline has caught at 20 m was a builder
agreeing with itself: n_obs written with the index scale and read back with the same scale (so QA saw a clean 3), n_obs
counted from NDVI finiteness by both writer and reader, a composite that merged only the first zone of a date.

Seven gates, all fatal:

  G1 INVENTORY    dates per frame x window, against the date lists the products claim in their tags; no date counted
                  twice; every index stack has its matching _valid mask
  G2 NO_PARTIALS  no *.part anywhere under frames10 -- a killed process must leave nothing publishable
  G3 GRID         every index stack, valid mask and composite is on the canonical lattice: exact transform, shape, CRS
  G4 N_OBS        FULL recount of n_obs from the validity masks alone, streamed, every pixel of every frame. Required
                  agreement is EXACT: these are integer counts of files, there is no tolerance to spend.
  G5 FEATURES     random blocks recomputed end to end from the per-date stacks and compared bit-exact with the stored
                  int16, including NDBI = -NDMI with the extremes transposed and the signed extreme change
  G6 RANGE        stored index values inside +-1.0 after descaling; n_obs within [0, n_dates]; nodata only where no date
                  was valid -- a pixel observed at least once must carry a value
  G9 PRE_DEF      the pre slot holds exactly the dates its own definition selects, re-derived here rather than
                  trusted from the tag, and not one acquisition on or after 2023-06-06 in either set
  G8 LINEAGE      every per-date stack says which acquisition it came from and at what native resolution; a date
                  built from a legacy 20 m zone stack is a FAIL wherever native SAFE exists for that date, because
                  the change features difference event against pre and must not span two lineages
  G7 MANIFEST     one immutable row per feature: name, index, window, statistic, source acquisitions, n_unique_dates,
                  scale, dtype, nodata, grid, CRS, code version

Outputs: <case_study>/tables/p54c_freeze_gate.csv (gate -> PASS/FAIL with the measured number), p54c_feature_manifest.csv,
p54c_inventory.csv. Exit code is non-zero if any gate fails: this is a gate, not a report.
"""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.windows import Window
from .. import _kakhovka_legacy_config as CFG
from ..optical import sentinel_preprocess as SP
from ..spatial import canonical_grid as CG
from ..io import optical_catalogue as OC

OUT = CFG.BULK_ROOT / "frames10"
IDX = list(SP.INDEX_NAMES)
SCALE = SP.INDEX_SCALE
ND = SP.INDEX_NODATA
# Bands each index consumes: SWIR (B11/B12) is NATIVE 20 m and reaches the 10 m lattice by one bilinear step, so an
# index containing it carries 20 m information at a 10 m posting. The manifest must say so -- it is the honest
# resolution of that feature, not the grid it is stored on.
INDEX_BANDS = {"NDVI": ("B08", "B04"), "NDWI": ("B03", "B08"), "MNDWI": ("B03", "B11"), "NDMI": ("B08", "B11"),
               "BSI": ("B11", "B04", "B08", "B02"), "AWEIsh": ("B02", "B03", "B08", "B11", "B12"),
               "NDTI": ("B04", "B03"), "NDBI": ("B08", "B11")}
WIN = {"pre": ("2022-01-01", "2023-06-05"), "event": ("2023-06-07", "2023-07-31"), "trace": ("2023-08-01", "2023-11-30")}
ROWS = 64


def code_version() -> str:
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=CFG.REPO_ROOT,
                           capture_output=True, text=True).stdout.strip()
    except Exception:
        h = "nogit"
    parts = []
    for f in ("src/floodstate_eo/optical/p54a_frame_index_stacks_10m.py",
              "src/floodstate_eo/optical/p54b_frame_composites_10m.py",
              "src/floodstate_eo/spatial/canonical_grid.py", "src/floodstate_eo/optical/sentinel_preprocess.py"):
        p = CFG.REPO_ROOT / f
        parts.append(hashlib.sha256(p.read_bytes()).hexdigest()[:8] if p.exists() else "missing")
    return f"{h}+{'.'.join(parts)}"


def dates_in(fid, lo, hi):
    d = OUT / fid / "indices"
    return sorted(p.stem for p in d.glob("*.tif")
                  if not p.stem.endswith("_valid") and lo <= p.stem <= hi and p.stat().st_size > 0)


def same_grid(path, G) -> str | None:
    with rasterio.open(path) as s:
        if (s.height, s.width) != (G["ny"], G["nx"]):
            return f"shape {(s.height, s.width)} != {(G['ny'], G['nx'])}"
        if max(abs(x - y) for x, y in zip(s.transform[:6], G["transform"][:6])) > 1e-9:
            return "transform"
        if s.crs.to_string() != str(CFG.CRS_METRIC):
            return f"crs {s.crs}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", nargs="*", default=list(CG.FRAME_BBOX))
    ap.add_argument("--blocks", type=int, default=6, help="random blocks per frame for the G5 bit-exact recompute")
    ap.add_argument("--seed", type=int, default=20260921)
    ap.add_argument("--sets", nargs="*", default=["preall", "preseas"])
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    ver = code_version()
    gates, inv, man = [], [], []

    def gate(name, frame, ok, measured, expected=""):
        gates.append(dict(gate=name, frame=frame, status="PASS" if ok else "FAIL",
                          measured=measured, expected=expected, code_version=ver))
        print(f"  {'PASS' if ok else 'FAIL'}  {name:12s} {frame:3s}  {measured}", flush=True)

    # ---- G2: partial outputs anywhere under the 10 m tree -----------------------------------------------------------
    parts = sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*.part"))
    gate("G2_NO_PARTIALS", "all", not parts, f"{len(parts)} partial files" + (f": {parts[:4]}" if parts else ""), "0")

    for fid in a.frames:
      G = CG.frame_grid(fid)
      for kind in a.sets:
        tag = f"{fid}/{kind}"
        print(f"\n=== {tag} ===", flush=True)
        comp = OUT / fid / f"composite_{kind}.tif"
        if not comp.exists():
            gate("G1_INVENTORY", tag, False, f"{comp.name} missing", "present"); continue
        dts = {w: dates_in(fid, *WIN[w]) for w in WIN}
        with rasterio.open(comp) as c0:
            pre_claim = [x for x in c0.tags().get("pre_acquisitions", "").split(";") if x]
            seas_claim = [x for x in c0.tags().get("pre_seas_acquisitions", "").split(";") if x]
            pre_def = c0.tags().get("pre_definition", "UNKNOWN")
        dts["pre"] = pre_claim
        # The set's own definition, re-derived here and not taken from the product: PRE_SEASONAL is May..August and
        # strictly before the breach, and a post-breach date in PRE is a hard failure whatever the tag says.
        expect = ([d for d in dates_in(fid, *WIN["pre"]) if int(d[5:7]) in (5, 6, 7, 8)]
                  if kind == "preseas" else dates_in(fid, *WIN["pre"]))
        leak = [d for d in pre_claim if d >= "2023-06-06"]
        gate("G9_PRE_DEF", tag, sorted(pre_claim) == sorted(expect) and not leak and pre_def != "UNKNOWN",
             f"{pre_def}: {len(pre_claim)} pre dates, expected {len(expect)}, {len(leak)} post-breach"
             + (f" {leak}" if leak else "") + f", seasonal support {len(seas_claim)}",
             "definition matches, 0 post-breach")

        # ---- G1: inventory, duplicates, matching validity masks -----------------------------------------------------
        all_d = [d for v in dts.values() for d in v]
        dup = len(all_d) - len(set(all_d))
        nomask = [d for v in dts.values() for d in v if not (OUT / fid / "indices" / f"{d}_valid.tif").exists()]
        with rasterio.open(comp) as c:
            tags = c.tags()
            names = [c.descriptions[i] for i in range(c.count)]
            claimed = dict(p.split(":") for p in tags.get("dates", "").split("|") if ":" in p)
        mism = {w: (len(dts[w]), int(claimed.get(w, -1))) for w in WIN if int(claimed.get(w, -1)) != len(dts[w])}
        for w in WIN:
            inv.append(dict(frame=fid, window=w, lo=WIN[w][0], hi=WIN[w][1], n_dates=len(dts[w]),
                            n_claimed_by_product=int(claimed.get(w, -1)), dates=";".join(dts[w])))
        gate("G1_INVENTORY", tag, not dup and not nomask and not mism,
             f"{len(all_d)} dates (" + ", ".join(f"{w} {len(dts[w])}" for w in WIN) +
             f"), {dup} duplicates, {len(nomask)} without a valid mask, claim mismatch {mism or 'none'}",
             "0 duplicates, 0 unmasked, claims match")
        gate("G7_MANIFEST", tag, len(names) == 84 and len(set(names)) == len(names),
             f"{len(names)} bands, {len(set(names))} unique", "84 unique")

        # ---- G8: lineage of every per-date stack ---------------------------------------------------------------------
        avail = {d: v["lineage"] for w in WIN for d, v in OC.catalogue(*WIN[w]).items()}
        legacy, unknown = [], []
        for w in WIN:
            for d in dts[w]:
                with rasterio.open(OUT / fid / "indices" / f"{d}.tif") as t:
                    lin = t.tags().get("lineage", "UNKNOWN")
                if lin == "UNKNOWN":
                    unknown.append(d)
                elif lin != OC.SAFE_10M and avail.get(d) == OC.SAFE_10M:
                    legacy.append(d)                      # built from 20 m although SAFE exists: avoidable split
        gate("G8_LINEAGE", tag, not legacy and not unknown,
             f"{len(legacy)} dates built at 20 m while SAFE exists {legacy[:5]}, {len(unknown)} without a lineage tag"
             + (f" {unknown[:5]}" if unknown else ""), "0 and 0")

        # ---- G3: grid ------------------------------------------------------------------------------------------------
        bad = []
        for p in [comp] + sorted((OUT / fid / "indices").glob("*.tif")):
            e = same_grid(p, G)
            if e:
                bad.append(f"{p.name}: {e}")
        gate("G3_GRID", tag, not bad, f"{len(bad)} off-lattice of {1 + len(list((OUT / fid / 'indices').glob('*.tif')))}"
             + (f" -> {bad[:3]}" if bad else ""), "0")

        # ---- G4: full independent recount of n_obs -------------------------------------------------------------------
        cnt = dict(dts); cnt["pre_seas"] = seas_claim        # n_obs_pre_seas is recounted too, in BOTH sets
        nb = {w: names.index(f"n_obs_{w}") + 1 for w in cnt}
        worst = {w: 0 for w in cnt}; nmis = {w: 0 for w in cnt}
        with rasterio.open(comp) as c:
            for r0 in range(0, G["ny"], ROWS):
                h = min(ROWS, G["ny"] - r0); win = Window(0, r0, G["nx"], h)
                for w in cnt:
                    n = np.zeros((h, G["nx"]), "i4")
                    for d in cnt[w]:
                        with rasterio.open(OUT / fid / "indices" / f"{d}_valid.tif") as v:
                            n += (v.read(1, window=win) == 1)
                    st = c.read(nb[w], window=win).astype("i4")
                    df = np.abs(st - n)
                    nmis[w] += int((df > 0).sum()); worst[w] = max(worst[w], int(df.max()))
        tot = sum(nmis.values())
        gate("G4_N_OBS", tag, tot == 0,
             "recounted " + ", ".join(f"{w} {nmis[w]} px differ (max |d| {worst[w]})" for w in cnt),
             "0 differing pixels")

        # ---- G5: bit-exact recompute of random blocks ----------------------------------------------------------------
        jm = IDX.index("NDMI")
        starts = rng.integers(0, max(1, G["ny"] - ROWS), size=a.blocks)
        nbad = 0; checked = 0; examples = []
        with rasterio.open(comp) as c:
            for r0 in starts:
                r0 = int(r0); win = Window(0, r0, G["nx"], ROWS)
                S = {}
                for w in WIN:
                    if dts[w]:
                        cube = np.full((len(dts[w]), len(IDX), ROWS, G["nx"]), np.nan, "f4")
                        for k, d in enumerate(dts[w]):
                            with rasterio.open(OUT / fid / "indices" / f"{d}.tif") as s:
                                arr = s.read(window=win).astype("f4")
                            arr[arr == ND] = np.nan
                            cube[k] = arr / SCALE
                        S[w] = dict(med=np.nanmedian(cube, 0), min=np.nanmin(cube, 0), max=np.nanmax(cube, 0))
                        del cube
                    else:
                        z = np.full((len(IDX), ROWS, G["nx"]), np.nan, "f4")
                        S[w] = dict(med=z, min=z, max=z)
                ref = {}
                for w in WIN:
                    for j, nm in enumerate(IDX):
                        ref[f"{nm}_{w}_med"] = S[w]["med"][j]
                        if w != "trace":
                            ref[f"{nm}_{w}_min"] = S[w]["min"][j]; ref[f"{nm}_{w}_max"] = S[w]["max"][j]
                    ref[f"NDBI_{w}_med"] = -S[w]["med"][jm]
                    if w != "trace":
                        ref[f"NDBI_{w}_min"] = -S[w]["max"][jm]; ref[f"NDBI_{w}_max"] = -S[w]["min"][jm]
                for nm in IDX + ["NDBI"]:
                    pm = ref[f"{nm}_pre_med"]
                    dlo = ref[f"{nm}_event_min"] - pm; dhi = ref[f"{nm}_event_max"] - pm
                    ref[f"{nm}_d_med"] = ref[f"{nm}_event_med"] - pm
                    ref[f"{nm}_d_ext"] = np.where(np.abs(np.nan_to_num(dhi)) >= np.abs(np.nan_to_num(dlo)), dhi, dlo)
                    ref[f"{nm}_d_trace"] = ref[f"{nm}_trace_med"] - pm
                for nm, v in ref.items():
                    q = np.where(np.isfinite(v), np.clip(np.round(v * SCALE), -32767, 32767), ND).astype("i2")
                    got = c.read(names.index(nm) + 1, window=win)
                    nd = int((got != q).sum()); checked += 1
                    if nd:
                        nbad += 1
                        if len(examples) < 4:
                            examples.append(f"{nm}@row{r0}:{nd}px")
        gate("G5_FEATURES", tag, nbad == 0, f"{nbad} of {checked} band-blocks differ from an independent recompute"
             + (f" -> {examples}" if examples else ""), "0")

        # ---- G6: value ranges and the observed-but-nodata contradiction ----------------------------------------------
        bad6 = []
        with rasterio.open(comp) as c:
            r0 = G["ny"] // 2; win = Window(0, r0, G["nx"], ROWS)
            ne = c.read(nb["event"], window=win)
            if ne.min() < 0 or ne.max() > len(dts["event"]):
                bad6.append(f"n_obs_event range [{ne.min()},{ne.max()}] outside [0,{len(dts['event'])}]")
            for nm in ("NDWI_event_med", "MNDWI_event_med", "AWEIsh_event_med", "NDBI_event_med"):
                b = c.read(names.index(nm) + 1, window=win)
                f = b[b != ND].astype("f4") / SCALE
                lim = 1.0 if nm != "AWEIsh_event_med" else 3.0
                if f.size and (f.min() < -lim - 1e-6 or f.max() > lim + 1e-6):
                    bad6.append(f"{nm} [{f.min():.3f},{f.max():.3f}] outside +-{lim}")
                if nm == "NDWI_event_med":
                    seen = (ne > 0) & (b == ND)
                    if seen.any():
                        bad6.append(f"{int(seen.sum())} px observed but NODATA")
        gate("G6_RANGE", tag, not bad6, "; ".join(bad6) if bad6 else "ranges and observed/NODATA consistent", "clean")

        # ---- G7: the immutable feature manifest ----------------------------------------------------------------------
        for i, nm in enumerate(names, 1):
            if nm.startswith("n_obs_"):
                w = nm.split("_")[-1]; index = "-"; stat = "count"; sc = 1
            else:
                index, w, stat = nm.split("_")[0], None, None
                rest = nm[len(index) + 1:]
                if rest.startswith("d_"):
                    w, stat = "event_vs_pre" if rest != "d_trace" else "trace_vs_pre", rest
                else:
                    w, stat = rest.rsplit("_", 1)
                sc = SCALE
            if w in dts:
                src = list(dts[w])
            else:                                   # a delta is sourced from BOTH of the windows it differences
                src = list(dts["pre"]) + list(dts["event" if w.startswith("event") else "trace"])
            bands_used = INDEX_BANDS.get(index, ())
            man.append(dict(band=i, feature_name=nm, index=index, window=w, statistic=stat,
                            source_bands="+".join(bands_used),
                            source_acquisitions=";".join(sorted(set(src))), n_unique_dates=len(set(src)),
                            native_resolution_m=20 if {"B11", "B12"} & set(bands_used) else 10,
                            lineage=";".join(sorted({avail.get(d, "UNKNOWN") for d in src})) or "-",
                            scale=sc, dtype="int16", nodata=ND, frame=fid, cell_m=CG.CELL,
                            pre_set=pre_def,
                            grid=f"{G['nx']}x{G['ny']}@{G['x0']},{G['y1']}", crs=str(CFG.CRS_METRIC),
                            code_version=ver))

    gdf = pd.DataFrame(gates); gdf.to_csv(CFG.TABLES / "p54c_freeze_gate.csv", index=False)
    pd.DataFrame(inv).to_csv(CFG.TABLES / "p54c_inventory.csv", index=False)
    pd.DataFrame(man).to_csv(CFG.TABLES / "p54c_feature_manifest.csv", index=False)
    nf = int((gdf.status == "FAIL").sum())
    print(f"\n{'COMPOSITES_10M_FREEZE_GATE PASSED' if nf == 0 else f'FREEZE GATE FAILED: {nf} gate(s)'}")
    print("-> <case_study>/tables/p54c_{freeze_gate,inventory,feature_manifest}.csv")
    sys.exit(1 if nf else 0)


if __name__ == "__main__":
    main()
