# Provenance: SWOT-DNIPRO scripts/p54b_frame_composites_10m.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 9 (migration_phase=5).
# Import block only: swot_dnipro package imports -> floodstate_eo package imports.
"""P54b -- temporal composites on the canonical 10 m lattice: the fixed-length feature vector future
classifiers will read.

Stage 2 of the 10 m recompute, under the same production contract as p54a: block processing, BIGTIFF, atomic
publication after a read-back, peak RSS logged. A B3 composite is 24 GB uncompressed at 83 bands, so BIGTIFF is not
optional -- a classic TIFF stops at 4 GB.

Per-pixel statistics over WHATEVER was validly observed, so a cell seen once and a cell seen fifteen times produce a
vector of the same length and neither is dropped. Observation counts are FEATURES, not a gate.

    PRE    what the surface WAS before the breach -- BASE_CLASS is built from this window
    EVENT  what happened to it
    TRACE  the footprint it left behind: evidence for a retrospective reconstruction, never a direct observation
           of the peak

Per index: median / min / max in PRE and EVENT, median in TRACE, and signed change against the PRE median
(d_med, d_ext = the event extreme furthest from the pre median with its sign, d_trace).

TWO DEFECTS THIS CARRIES FIXED, both caught by QA before they reached a classifier:
  * n_obs counts OBSERVATIONS, from the validity masks alone. It used to count dates with a finite NDVI, and NDVI is
    undefined where B08+B04 == 0, so observed pixels went uncounted.
  * n_obs is stored as a PLAIN COUNT. Writing it with the index scale (x1e4, clipped at 32767) saturated every value
    above 3, which is exactly what an independent reconstruction exposed: stored max 3 against a rebuilt max of 17.
  * NDBI is derived as -NDMI with the extremes TRANSPOSED: NDBI_min = -NDMI_max, NDBI_max = -NDMI_min. Negating in
    place would silently swap the built-up extremes on every pixel.
Outputs: $BULK_ROOT/frames10/<FID>/composite.tif, <case_study>/tables/p54b_composite_bands.csv, p54b_build_log.csv
"""
from __future__ import annotations
import argparse, os, resource, sys, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
os.environ.setdefault("GDAL_CACHEMAX", "256")
import numpy as np, pandas as pd, rasterio
from rasterio.windows import Window
from .. import _kakhovka_legacy_config as CFG
from . import sentinel_preprocess as SP
from ..spatial import canonical_grid as CG

IDX = list(SP.INDEX_NAMES)
WIN = {"pre": ("2022-01-01", "2023-06-05"), "event": ("2023-06-07", "2023-07-31"), "trace": ("2023-08-01", "2023-11-30")}
OUT = CFG.BULK_ROOT / "frames10"
SCALE = SP.INDEX_SCALE
ND = SP.INDEX_NODATA
BLOCK = 96
BUDGET = 600_000_000        # bytes for the date cube; see block_rows()

#: TWO BASELINES, BUILT FROM THE SAME PER-DATE STACKS. The event window is June-July. A pre-breach median taken over
#: every available season therefore differences July vegetation against, among others, February vegetation, and for
#: NDVI / BSI / NDMI / NDBI that difference is large with no flood anywhere in it. So the composite is produced twice,
#: differing ONLY in which dates fill the pre slot:
#:
#:   SET A  pre_all   every pre-breach date on record -- the stable general baseline, the definition in force
#:   SET B  pre_seas  the same phenological season as the event -- May..August, and only before the breach
#:
#: Set B is an ablation, not a replacement: it becomes canonical only if validation shows a stable gain. Both files
#: carry the SAME 84-band plan so A and B can be scored on identical spatial folds without any remapping.
SEASON_MONTHS = (5, 6, 7, 8)
BREACH = "2023-06-06"       # a post-breach acquisition can never enter PRE, however well it fits the calendar season
PRE_SETS = {"preall": "PRE_ALL", "preseas": "PRE_SEASONAL"}


def dates_in(fid, lo, hi):
    d = OUT / fid / "indices"
    return sorted(p.stem for p in d.glob("*.tif")
                  if not p.stem.endswith("_valid") and lo <= p.stem <= hi and p.stat().st_size > 0)


def pre_dates(fid, kind: str) -> list[str]:
    """The pre-breach dates that fill the pre slot for this set.

    PRE_SEASONAL is `month in May..August AND date < 2023-06-06`, applied to acquisitions, not to a nominal window.
    The breach cut is asserted rather than assumed: the pre window already ends 2023-06-05, but a baseline that could
    silently absorb a post-breach June date is not a baseline, and this assert is cheaper than discovering it in a
    change map.

    There is NO fallback to PRE_ALL when seasonal dates are scarce. Substituting one semantics for another because
    the intended one is thin is how "not observed" becomes "dry"; scarcity is reported as n_obs_pre_seas and as a
    seasonal-support column in the build log, and stays visible.
    """
    al = dates_in(fid, *WIN["pre"])
    out = al if kind == "preall" else [d for d in al if int(d[5:7]) in SEASON_MONTHS]
    assert all(d < BREACH for d in out), f"{fid}: post-breach date in PRE: {[d for d in out if d >= BREACH]}"
    return out


def lineages(fid, dates) -> dict[str, str]:
    """What each per-date stack says it was built from.

    A composite that averages a native 10 m date with a date replicated from a 20 m legacy product is not a composite
    of one thing, and the change bands difference the two windows directly. The first full rebuild was killed for
    exactly this, so the composite refuses to be built on a mixed set rather than recording the mixture and carrying
    on."""
    out = {}
    for dt in dates:
        with rasterio.open(OUT / fid / "indices" / f"{dt}.tif") as s:
            out[dt] = s.tags().get("lineage", "UNKNOWN")
    return out


def band_plan():
    names = []
    for w in ("pre", "event", "trace"):
        for nm in IDX + ["NDBI"]:
            names.append(f"{nm}_{w}_med")
            if w != "trace":
                names += [f"{nm}_{w}_min", f"{nm}_{w}_max"]
    for nm in IDX + ["NDBI"]:
        names += [f"{nm}_d_med", f"{nm}_d_ext", f"{nm}_d_trace"]
    # n_obs_pre_seas is present in BOTH sets and is always counted over the seasonal dates. In set B it equals
    # n_obs_pre; in set A it is the seasonal support behind an all-season baseline, which is exactly the number needed
    # to judge that baseline and would otherwise have to be inferred from a different file.
    return names + ["n_obs_pre", "n_obs_event", "n_obs_trace", "n_obs_pre_seas"]


def peak_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6


def block_rows(nx: int, ndates: int, cap: int) -> int:
    """Rows per block, sized so the date cube stays inside BUDGET.

    The cube is (ndates, 7, rows, nx) float32 and np.nanmedian copies the slice it reduces, so the true peak is roughly
    BUDGET plus one index plane. A frame is NOT a unit of memory here: B3 has 145 Mpx and the pre window holds the most
    dates, so a fixed row count would be sized for the smallest case and killed on the largest.
    """
    if ndates <= 0:
        return cap
    return int(max(8, min(cap, BUDGET // (ndates * len(IDX) * nx * 4))))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frames", nargs="*", default=list(CG.FRAME_BBOX))
    ap.add_argument("--block", type=int, default=BLOCK)
    ap.add_argument("--sets", nargs="*", default=list(PRE_SETS), choices=list(PRE_SETS),
                    help="preall = the baseline in force; preseas = the season-matched ablation")
    a = ap.parse_args()
    names = band_plan()
    pd.DataFrame(dict(band=range(1, len(names) + 1), name=names)).to_csv(CFG.TABLES / "p54b_composite_bands.csv", index=False)
    print(f"{len(names)} bands per frame\n")
    log = []
    for fid in a.frames:
      F = CG.frame_grid(fid)
      seas = pre_dates(fid, "preseas")
      for kind in a.sets:
        t0 = time.time()
        dts = {w: dates_in(fid, *WIN[w]) for w in WIN}
        dts["pre"] = pre_dates(fid, kind)
        print(f"{fid} [{PRE_SETS[kind]}]: {F['ny']}x{F['nx']} = {F['ny']*F['nx']/1e6:.1f} Mpx | "
              + ", ".join(f"{w} {len(v)}" for w, v in dts.items())
              + f" | seasonal support {len(seas)}", flush=True)
        lin = {w: lineages(fid, v) for w, v in dts.items()}
        seen = sorted({x for v in lin.values() for x in v.values()})
        if seen != ["SAFE_10M"]:
            bad = {w: sorted({d: l for d, l in v.items() if l != "SAFE_10M"}) for w, v in lin.items()}
            print(f"   REFUSED: lineage is {seen}, not SAFE_10M only -> {bad}", flush=True)
            log.append(dict(frame=fid, pre_set=PRE_SETS[kind], bands=len(names), dates_pre=len(dts["pre"]),
                            dates_pre_seas=len(seas), dates_event=len(dts["event"]), dates_trace=len(dts["trace"]),
                            seconds=0, peak_rss_gb=0.0, size_gb=0.0,
                            status=f"REFUSED_MIXED_LINEAGE:{'|'.join(seen)}"))
            continue
        if not dts["pre"]:
            # No substitution. An empty seasonal baseline yields NODATA pre bands and n_obs_pre = 0, and the change
            # bands are NODATA with it -- which is the honest statement that this frame has no season-matched baseline.
            print(f"   WARNING: {PRE_SETS[kind]} is empty for {fid}; pre and change bands will be NODATA", flush=True)
        print(f"   lineage {seen[0]} on all {sum(len(v) for v in dts.values())} dates", flush=True)
        out = OUT / fid / f"composite_{kind}.tif"; part = out.with_suffix(".tif.part")
        # THE WRITE WINDOW AND THE TILE ROW MUST BE THE SAME HEIGHT.
        # A DEFLATE tile cannot be updated in place once its compressed length changes, so libtiff appends the new
        # copy and orphans the old one. Writing 96-row windows into 512-row tiles touches each tile about six times,
        # across 84 bands: the first attempt at B2 reached 52 GB of real blocks (du, not apparent size) at ~1 % of
        # rows, for a product whose uncompressed size is 4.85 GB, and was still growing at 1.7 GB/min. Matching the
        # tile height to the write height means every tile is written exactly once.
        nd_max = max(len(v) for v in dts.values())
        nrows = max(16, (block_rows(F["nx"], nd_max, a.block) // 16) * 16)   # TIFF tile length: multiple of 16
        prof = SP._profile(F, len(names), "int16", ND)
        prof.update(BIGTIFF="IF_SAFER", blockxsize=512, blockysize=nrows)
        with rasterio.open(part, "w", **prof) as dst:
            for i, nm in enumerate(names, 1):
                dst.set_band_description(i, nm)
            dst.update_tags(scale=f"value/{SCALE} EXCEPT n_obs_* which are plain counts", nodata=str(ND), frame=fid,
                            cell_m=str(CG.CELL), resampling=str(CG.RESAMPLING),
                            windows="|".join(f"{w}:{WIN[w][0]}..{WIN[w][1]}" for w in WIN),
                            dates="|".join(f"{w}:{len(dts[w])}" for w in WIN),
                            pre_definition=PRE_SETS[kind],
                            pre_rule=("every pre-breach acquisition" if kind == "preall" else
                                      f"month in {SEASON_MONTHS} and date < {BREACH}"),
                            pre_acquisitions=";".join(dts["pre"]),
                            pre_seas_acquisitions=";".join(seas),
                            ndbi="derived as -NDMI with min/max transposed",
                            n_obs="distinct acquisition dates with a valid scene observation",
                            lineage=seen[0],
                            producer="p54b_frame_composites_10m.py")
            print(f"   block {nrows} rows = tile height (cube {nd_max}x{len(IDX)}x{nrows}x{F['nx']} f4 = "
                  f"{nd_max*len(IDX)*nrows*F['nx']*4/1e9:.2f} GB)", flush=True)
            for r0 in range(0, F["ny"], nrows):
                r1 = min(r0 + nrows, F["ny"]); h = r1 - r0
                win = Window(0, r0, F["nx"], h)
                stats = {}
                for w, ds_ in dts.items():
                    med = np.full((len(IDX), h, F["nx"]), np.nan, "f4")
                    lo_ = np.full_like(med, np.nan); hi_ = np.full_like(med, np.nan)
                    n = np.zeros((h, F["nx"]), "f4")
                    if ds_:
                        S = np.empty((len(ds_), len(IDX), h, F["nx"]), "f4")
                        for k, dt in enumerate(ds_):
                            with rasterio.open(OUT / fid / "indices" / f"{dt}.tif") as src:
                                arr = src.read(window=win).astype("f4")
                            arr[arr == ND] = np.nan
                            S[k] = arr / SCALE
                            with rasterio.open(OUT / fid / "indices" / f"{dt}_valid.tif") as vsrc:
                                n += (vsrc.read(1, window=win) == 1)
                        del arr
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            for j in range(len(IDX)):          # per index: nanmedian copies what it reduces
                                sj = S[:, j]
                                med[j] = np.nanmedian(sj, 0); lo_[j] = np.nanmin(sj, 0); hi_[j] = np.nanmax(sj, 0)
                        del S
                    stats[w] = dict(med=med, min=lo_, max=hi_, n=n)
                buf = {}
                jm = IDX.index("NDMI")
                for w in ("pre", "event", "trace"):
                    s_ = stats[w]
                    for j, nm in enumerate(IDX):
                        buf[f"{nm}_{w}_med"] = s_["med"][j]
                        if w != "trace":
                            buf[f"{nm}_{w}_min"] = s_["min"][j]; buf[f"{nm}_{w}_max"] = s_["max"][j]
                    buf[f"NDBI_{w}_med"] = -s_["med"][jm]
                    if w != "trace":
                        buf[f"NDBI_{w}_min"] = -s_["max"][jm]; buf[f"NDBI_{w}_max"] = -s_["min"][jm]
                for nm in IDX + ["NDBI"]:
                    pm = buf[f"{nm}_pre_med"]
                    dlo = buf[f"{nm}_event_min"] - pm; dhi = buf[f"{nm}_event_max"] - pm
                    buf[f"{nm}_d_med"] = buf[f"{nm}_event_med"] - pm
                    buf[f"{nm}_d_ext"] = np.where(np.abs(np.nan_to_num(dhi)) >= np.abs(np.nan_to_num(dlo)), dhi, dlo)
                    buf[f"{nm}_d_trace"] = buf[f"{nm}_trace_med"] - pm
                for w in WIN:
                    buf[f"n_obs_{w}"] = stats[w]["n"]
                ns = np.zeros((h, F["nx"]), "f4")           # always the seasonal count, in BOTH sets
                for d in seas:
                    with rasterio.open(OUT / fid / "indices" / f"{d}_valid.tif") as vsrc:
                        ns += (vsrc.read(1, window=win) == 1)
                buf["n_obs_pre_seas"] = ns
                for i, nm in enumerate(names, 1):
                    v = buf[nm]
                    if nm.startswith("n_obs_"):
                        q = np.clip(np.round(np.nan_to_num(v, nan=0.0)), 0, 32767).astype("i2")
                    else:
                        q = np.where(np.isfinite(v), np.clip(np.round(v * SCALE), -32767, 32767), ND).astype("i2")
                    dst.write(q, i, window=win)
                del stats, buf
                if (r0 // nrows) % 20 == 0:
                    gb = part.stat().st_size / 1e9
                    exp = F["ny"] * F["nx"] * len(names) * 2 / 1e9
                    print(f"   rows {r0}-{r1} ({100*r1/F['ny']:.0f} %)  {time.time()-t0:.0f}s  "
                          f"peakRSS {peak_gb():.2f} GB  file {gb:.2f} GB of {exp:.2f} GB uncompressed", flush=True)
        try:
            with rasterio.open(part) as chk:
                assert (chk.height, chk.width) == (F["ny"], F["nx"]), "shape"
                assert chk.count == len(names), "band count"
                assert chk.dtypes[0] == "int16", "dtype"
                assert max(abs(x - y) for x, y in zip(chk.transform[:6], F["transform"][:6])) < 1e-9, "transform"
                for bn, nd_ in (("n_obs_event", len(dts["event"])), ("n_obs_pre", len(dts["pre"])),
                                ("n_obs_pre_seas", len(seas))):
                    probe = chk.read(names.index(bn) + 1, window=Window(0, F["ny"] // 2, min(4096, F["nx"]), 64))
                    assert probe.max() <= nd_, f"{bn} exceeds its number of dates"
        except Exception as ex:
            print(f"   READ-BACK FAILED ({ex}); left as {part.name}", flush=True); continue
        os.replace(part, out)
        log.append(dict(frame=fid, pre_set=PRE_SETS[kind], bands=len(names), dates_pre=len(dts["pre"]),
                        dates_pre_seas=len(seas), dates_event=len(dts["event"]), dates_trace=len(dts["trace"]),
                        seconds=round(time.time() - t0), peak_rss_gb=round(peak_gb(), 2),
                        size_gb=round(out.stat().st_size / 1e9, 2), status="OK"))
        print(f"   -> {out.name}  {log[-1]['size_gb']} GB, {log[-1]['seconds']}s, "
              f"peakRSS {log[-1]['peak_rss_gb']} GB", flush=True)
        pd.DataFrame(log).to_csv(CFG.TABLES / "p54b_build_log.csv", index=False)
    print("\n-> <case_study>/tables/p54b_{composite_bands,build_log}.csv")


if __name__ == "__main__":
    main()
