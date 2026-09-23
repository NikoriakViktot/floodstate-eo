# Provenance: SWOT-DNIPRO scripts/p82_coherence_graph.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 20 (migration_phase=5).
# Import block only: swot_dnipro package import -> floodstate_eo. SLC/WORK absolute host paths, the docker
# image name and the memory-safety flags (-q 2 -c 1024M -x, added the same session as this migration after a
# live "Java heap space" incident on this machine's WSL2 memory cap) are left exactly as in the source --
# machine-specific, listed as Phase 6 config work in 06_CONFIGURATION_DESIGN.md.
# LOGIC CHANGED in floodstate-eo on 2026-09-23 (no longer byte-identical to source): execution topology split
# from one graph into one JVM per subswath + one Merge/TC JVM, after the single graph exhausted -Xmx16G inside
# ESD <- SliceAssembly on orbit 65 pair 1; plus transactional output (validate, then .ok.json, then atomic rename).
# Operators and every operator parameter are unchanged.
"""P82 -- the SNAP interferometric-coherence chain for one 12-day pair. STAGED: ONE JVM PER SUBSWATH.

    per subswath, own JVM:  SliceAssembly -> Apply-Orbit-File -> TOPSAR-Split(sw)
                            -> Back-Geocoding -> Enhanced-Spectral-Diversity -> Coherence(10x3) -> TOPSAR-Deburst
                            -> BEAM-DIMAP checkpoint (validated)
    then, own JVM:          TOPSAR-Merge (when more than one) -> Terrain-Correction (EPSG:32636, 20 m)

The staging changes where the graph is cut, not what is computed: Merge still precedes a single Terrain-Correction.
The pre-staging single-graph design ("ONE GRAPH, ONE PASS") ran out of heap; bitwise equivalence with it is not
demonstrated, since it never produced a complete product.

MERGE BEFORE TERRAIN CORRECTION, NOT AFTER. The TOPS interferometric operators work on one split subswath at a
time, and TOPSAR-Merge exists to rejoin debursted consecutive subswaths. Terrain-correcting IW2 and IW3
separately and mosaicking the results afterwards would put an extra seam and a second resampling into the very
feature being measured -- and this project has already spent a full rebuild on a resampling defect that metrics
could not see. One Terrain-Correction, once, at the end.

SUBSWATH SELECTION IS DATA, NOT A CONSTANT, AND THIS WAS NOT A PRECAUTION. An earlier version of this file
hard-coded SUBSWATHS = ("IW2", "IW3") from the orbit-65 pilot. Measuring the other three (p80_subswath_coverage.csv,
from annotation metadata, no bulk download) showed:

    orbit  14 ASC   IW1  99.0 %   IW2 0.0 %   IW3 0.0 %
    orbit  65 DES   IW1   0.0 %   IW2 11.5 %  IW3 98.5 %
    orbit  87 ASC   IW1   0.0 %   IW2 59.4 %  IW3 59.6 %
    orbit 138 DES   IW1 100.0 %   IW2 0.0 %   IW3 0.0 %

Two of the four orbits see frame B2 through IW1 alone. The hard-coded pair would have produced an empty product
for half the experiment -- or worse, a coherence layer over no ground that then got explained physically. A
product footprint intersecting the frame is not evidence of burst coverage, and one orbit's geometry is not
another's. The table is read per orbit; there is no default.

THE COHERENCE WINDOW IS THE STANDARD ONE, NOT A TUNED ONE. 10 range x 3 azimuth is the window of the standard
Sentinel-1 TOPSAR interferometry workflow in SNAP; with IW slant-range spacing ~2.3 m and azimuth ~14.1 m it
gives roughly square ground support. Methods must say "consistent with the standard workflow", never "we selected
10x3". A 5x3 / 10x3 / 15x3 sensitivity check is held back unless the effect returns something worth explaining;
it does not belong in the primary experiment.

ESD IS NOT OPTIONAL. Enhanced-Spectral-Diversity uses burst overlaps to refine azimuth coregistration after
Back-Geocoding. Without it, insufficient coregistration lowers coherence through geometric error, which we would
then read as surface change. Its estimated shifts are captured per pair as provenance (p82_esd_diagnostics.csv):
an anomalous shift means that pair's low coherence cannot be attributed to flooding.

VV AND VH STAY SEPARATE. Both polarisations are carried through as distinct bands and never averaged here. The
model decides whether cross-pol coherence adds anything; averaging first would discard that before it is asked.

STOPPING RULE, BINDING: **technical failure can stop the experiment; scientific effect size cannot.**
The first pair is an ENGINEERING gate and answers only five questions -- does the graph complete; is coherence in
[0, 1] with adequate valid coverage of the frame; are there seams between bursts, subswaths or slices; does ESD
report anomalous coregistration; does scratch space actually return when the container exits. Processing may be
halted on any of those. It may NOT be halted because coherence over agriculture "does not look promising" on one
orbit. Looking at part of the outcome and then deciding how much data to include, before estimating that same
effect, is optional stopping -- a selection bias we would build ourselves after spending this much effort
removing others.

ALL FOUR ORBITS, AND THE SUBSWATH FINDING IS WHY. Orbits 14 and 138 view B2 through IW1 while 65 and 87 use
IW2+IW3, so the four orbits are four genuinely different viewing geometries. Coherence over crops depends on
crop development and on acquisition geometry, and one study that separated the observables found intensity
carrying irrigated agriculture while coherence carried built-up. A result from a single orbit could therefore be
real and still not representative of B2. Running all four tests whether the complementarity of coherence to
intensity TRANSFERS ACROSS VIEWING GEOMETRIES, which is a materially stronger claim than one orbit can support.
A day of CPU is a small price beside that.

INTERMEDIATES ARE NOT PROVENANCE. Back-Geocoding and ESD temporaries are deterministically reproducible from the
immutable SAFE plus this graph, so deleting them after the final raster passes QC costs nothing. What is kept:
the SAFE archives, the frozen pair manifest, this graph and the SNAP version, the processing parameters, the ESD
and QC logs, the geocoded coherence rasters, the feature stack, and hashes.
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, time
from pathlib import Path
import numpy as np, pandas as pd
from .. import _kakhovka_legacy_config as CFG

SLC = Path("/home/niko/data_s1_slc")
WORK = Path("/home/niko/data_s1_coh")
IMAGE = "flood-snap:latest"
GPT = "/opt/snap/bin/gpt"
COVERAGE = "p80_subswath_coverage.csv"        # measured per orbit; there is no module-level subswath default
POLS = "VV,VH"
COH_RANGE, COH_AZIMUTH = 10, 3
PIXEL_M = 20.0


def _side(tag, zips, sw):
    n = [f'  <node id="read_{tag}{i}"><operator>Read</operator>'
         f'<parameters><file>{z}</file></parameters></node>' for i, z in enumerate(zips)]
    if len(zips) > 1:
        srcs = "".join(f'<sourceProduct refid="read_{tag}0"/>' if i == 0
                       else f'<sourceProduct.{i} refid="read_{tag}{i}"/>' for i in range(len(zips)))
        n.append(f'  <node id="asm_{tag}"><operator>SliceAssembly</operator>'
                 f'<sources>{srcs}</sources>'
                 f'<parameters><selectedPolarisations>{POLS}</selectedPolarisations></parameters></node>')
        last = f"asm_{tag}"
    else:
        last = f"read_{tag}0"
    n.append(f'  <node id="orb_{tag}"><operator>Apply-Orbit-File</operator>'
             f'<sources><sourceProduct refid="{last}"/></sources>'
             f'<parameters><orbitType>Sentinel Precise (Auto Download)</orbitType>'
             f'<continueOnFail>false</continueOnFail></parameters></node>')
    n.append(f'  <node id="spl_{tag}_{sw}"><operator>TOPSAR-Split</operator>'
             f'<sources><sourceProduct refid="orb_{tag}"/></sources>'
             f'<parameters><subswath>{sw}</subswath>'
             f'<selectedPolarisations>{POLS}</selectedPolarisations></parameters></node>')
    return n


def _graph_xml(nodes):
    return '<graph id="coh">\n  <version>1.0</version>\n' + "\n".join(nodes) + "\n</graph>\n"


def graph_subswath(master_zips, slave_zips, sw, out_dim):
    """Stage A/B: one subswath, Read..Deburst, written as a BEAM-DIMAP checkpoint. Operators and parameters are
    exactly those of the former single graph; only the subswath set per JVM changed."""
    nodes = _side("m", master_zips, sw) + _side("s", slave_zips, sw)
    nodes += [
        f'  <node id="bgc_{sw}"><operator>Back-Geocoding</operator>'
        f'<sources><sourceProduct refid="spl_m_{sw}"/><sourceProduct.1 refid="spl_s_{sw}"/></sources>'
        f'<parameters><demName>SRTM 1Sec HGT</demName>'
        f'<resamplingType>BISINC_5_POINT_INTERPOLATION</resamplingType>'
        f'<maskOutAreaWithoutElevation>false</maskOutAreaWithoutElevation></parameters></node>',
        f'  <node id="esd_{sw}"><operator>Enhanced-Spectral-Diversity</operator>'
        f'<sources><sourceProduct refid="bgc_{sw}"/></sources><parameters/></node>',
        f'  <node id="coh_{sw}"><operator>Coherence</operator>'
        f'<sources><sourceProduct refid="esd_{sw}"/></sources>'
        f'<parameters><cohWinRg>{COH_RANGE}</cohWinRg><cohWinAz>{COH_AZIMUTH}</cohWinAz>'
        f'<singleMaster>true</singleMaster><subtractFlatEarthPhase>true</subtractFlatEarthPhase>'
        f'</parameters></node>',
        f'  <node id="deb_{sw}"><operator>TOPSAR-Deburst</operator>'
        f'<sources><sourceProduct refid="coh_{sw}"/></sources>'
        f'<parameters><selectedPolarisations>{POLS}</selectedPolarisations></parameters></node>',
        f'  <node id="write"><operator>Write</operator>'
        f'<sources><sourceProduct refid="deb_{sw}"/></sources>'
        f'<parameters><file>{out_dim}</file><formatName>BEAM-DIMAP</formatName></parameters></node>']
    return _graph_xml(nodes)


def graph_merge_tc(dims, out):
    """Stages C+D: read only the debursted coherence checkpoints -> TOPSAR-Merge (when >1) -> ONE
    Terrain-Correction. No Back-Geocoding/ESD working set exists in this JVM."""
    nodes = [f'  <node id="read_{i}"><operator>Read</operator><parameters><file>{d}</file></parameters></node>'
             for i, d in enumerate(dims)]
    if len(dims) > 1:
        srcs = "".join(f'<sourceProduct refid="read_{i}"/>' if i == 0 else f'<sourceProduct.{i} refid="read_{i}"/>'
                       for i in range(len(dims)))
        nodes.append(f'  <node id="mrg"><operator>TOPSAR-Merge</operator>'
                     f'<sources>{srcs}</sources>'
                     f'<parameters><selectedPolarisations>{POLS}</selectedPolarisations></parameters></node>')
        pre_tc = "mrg"
    else:
        pre_tc = "read_0"
    nodes += [
        f'  <node id="tc"><operator>Terrain-Correction</operator>'
        f'<sources><sourceProduct refid="{pre_tc}"/></sources>'
        f'<parameters><demName>SRTM 1Sec HGT</demName>'
        f'<imgResamplingMethod>BILINEAR_INTERPOLATION</imgResamplingMethod>'
        f'<pixelSpacingInMeter>{PIXEL_M}</pixelSpacingInMeter>'
        f'<mapProjection>EPSG:32636</mapProjection>'
        f'<nodataValueAtSea>false</nodataValueAtSea></parameters></node>',
        f'  <node id="write"><operator>Write</operator>'
        f'<sources><sourceProduct refid="tc"/></sources>'
        f'<parameters><file>{out}</file><formatName>GeoTIFF</formatName></parameters></node>']
    return _graph_xml(nodes)


def subswaths_for(orbit):
    """Read the measured subswath set for this orbit, and refuse to guess if it was never measured."""
    p = CFG.TABLES / COVERAGE
    if not p.exists():
        raise SystemExit(f"{COVERAGE} missing -- measure subswath coverage before processing, do not assume it")
    T = pd.read_csv(p)
    row = T[T.rel_orbit == orbit]
    if row.empty:
        raise SystemExit(f"orbit {orbit} absent from {COVERAGE} -- measure it first")
    r = row.iloc[0]
    sw = [x for x in str(r.subswaths).split(",") if x]
    if not sw or float(r.coverage) < 0.95:
        raise SystemExit(f"orbit {orbit}: measured coverage {float(r.coverage):.1%} with subswaths {sw} -- "
                         f"below 95 % of the frame; resolve the geometry rather than processing a partial frame")
    print(f"  orbit {orbit}: subswaths {'+'.join(sw)} covering {float(r.coverage):.1%} of B2 (measured)",
          flush=True)
    return sw


def esd_rows(log, orbit, m, s, sws):
    """Capture the azimuth/range shifts ESD estimated. Provenance, not a feature.

    A pair whose estimated shift is an outlier has low coherence for a geometric reason, and its Dgamma must not
    be read as inundation. Recorded per pair so that judgement is possible later rather than guessed at.
    """
    out = []
    for sw in sws:
        az = re.findall(rf"{sw}.*?[Aa]zimuth shift[^\-\d]*(-?\d+\.?\d*)", log, re.S)
        rg = re.findall(rf"{sw}.*?[Rr]ange shift[^\-\d]*(-?\d+\.?\d*)", log, re.S)
        out.append(dict(rel_orbit=orbit, pre_date=m, event_date=s, subswath=sw,
                        azimuth_shift=float(az[0]) if az else None,
                        range_shift=float(rg[0]) if rg else None,
                        shift_reported=bool(az or rg)))
    return out


def _utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def quarantine(*paths):
    """A failed or unvalidated product is renamed, never deleted and never left under a name a later run could
    mistake for a finished one."""
    tag = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    for p in paths:
        if p.exists():
            q = p.with_name(f"FAILED_PARTIAL_{tag}_{p.name}")
            p.rename(q)
            print(f"     quarantined {p.name} -> {q.name}", flush=True)


def run_gpt(gx, log, snaplog, memory):
    """One graph, one fresh container, one fresh JVM. The SNAP log dir is mounted so ESD's shift files survive
    the --rm container as provenance."""
    snaplog.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    # -q 2 (not the CLI default of 32) and -c/-x cap and evict the JAI tile cache; kept from the single-graph
    # version. Its failure at -Xmx16G under a 24 GB WSL2 cap (2026-09-23, orbit 65 pair 1: "Java heap space" in
    # ESD <- SliceAssembly, WSL still ~4 GB free) is why each subswath now gets its own JVM.
    r = subprocess.run(["docker", "run", "--rm", "-v", f"{SLC}:{SLC}:ro", "-v", f"{WORK}:{WORK}",
                        "-v", f"{snaplog}:/root/.snap/var/log",
                        IMAGE, GPT, str(gx), f"-J-Xmx{memory}", "-q", "2", "-c", "1024M", "-x"],
                       capture_output=True, text=True)
    log.write_text(r.stdout + "\n" + r.stderr)
    return r, time.time() - t0


def _coh_stats(a, problems, name):
    """Shared value checks: something finite and non-zero, and nothing outside [0, 1] (p83's G2 threshold)."""
    f = a[np.isfinite(a)]
    nz = f[f != 0]
    out01 = float(((f < 0) | (f > 1)).mean()) if f.size else 1.0
    st = dict(n=int(a.size), finite_frac=round(f.size / max(a.size, 1), 4),
              nonzero_frac=round(nz.size / max(a.size, 1), 4), frac_outside_0_1=out01,
              median_nonzero=round(float(np.median(nz)), 4) if nz.size else None)
    if nz.size == 0:
        problems.append(f"{name}: no finite non-zero coherence")
    if out01 >= 1e-6:
        problems.append(f"{name}: {out01:.2e} of finite values outside [0, 1]")
    return st


def validate_dim(dim):
    """A subswath checkpoint is accepted only if every coherence band is present, un-truncated and plausible."""
    import rasterio
    from rasterio.windows import Window
    problems, bands = [], []
    data = dim.with_suffix(".data")
    imgs = sorted(data.glob("coh_*.img")) if data.is_dir() else []
    npol = len(POLS.split(","))
    if not dim.exists():
        problems.append(f"{dim.name} missing")
    if len(imgs) != npol:
        problems.append(f"{len(imgs)} coherence bands in {data.name}, expected {npol} ({POLS})")
    shapes = set()
    for img in imgs:
        with rasterio.open(img) as s:
            w, h = s.width, s.height
            expect = w * h * np.dtype(s.dtypes[0]).itemsize
            got = img.stat().st_size
            if w <= 0 or h <= 0:
                problems.append(f"{img.name}: empty raster {w}x{h}")
                continue
            if got != expect:
                problems.append(f"{img.name}: {got} B on disk vs {expect} B from header -- truncated")
            s.read(1, window=Window(0, h - 1, w, 1))      # last row must be readable
            a = s.read(1, out_shape=(max(1, h // 4), max(1, w // 4))).astype("f4")
        shapes.add((w, h))
        bands.append(dict(band=img.stem, width=w, height=h, bytes=got, **_coh_stats(a, problems, img.stem)))
    if len(shapes) > 1:
        problems.append(f"coherence bands disagree in shape: {sorted(shapes)}")
    return dict(dim=dim.name, bands=bands), problems


def validate_final(tif):
    """The merged, terrain-corrected raster is accepted only against the frozen target: EPSG:32636, PIXEL_M,
    one coherence band per polarisation, fully readable, values in [0, 1]."""
    import hashlib, rasterio
    from rasterio.windows import Window
    problems = []
    with rasterio.open(tif) as s:
        rep = dict(crs=str(s.crs), width=s.width, height=s.height, count=s.count, dtype=s.dtypes[0],
                   res=[round(abs(x), 4) for x in s.res], nodata=s.nodata,
                   descriptions=[d or "" for d in s.descriptions], bands=[])
        if s.crs is None or s.crs.to_epsg() != 32636:
            problems.append(f"CRS {s.crs}, expected EPSG:32636")
        if any(abs(abs(x) - PIXEL_M) > 1e-3 for x in s.res):
            problems.append(f"pixel {s.res}, expected {PIXEL_M} m")
        if s.count != len(POLS.split(",")):
            problems.append(f"{s.count} bands, expected {len(POLS.split(','))} ({POLS})")
        if not (100 <= s.width <= 50000 and 100 <= s.height <= 50000):
            problems.append(f"implausible size {s.width}x{s.height}")
        if s.nodata is not None and 0 < s.nodata <= 1:
            problems.append(f"nodata {s.nodata} lies inside the coherence range")
        for b in range(1, s.count + 1):
            s.read(b, window=Window(0, s.height - 1, s.width, 1))
            a = s.read(b).astype("f4")
            if s.nodata is not None and np.isfinite(s.nodata):
                a[a == s.nodata] = np.nan
            rep["bands"].append(dict(band=b, **_coh_stats(a, problems, f"band {b}")))
            del a
    h = hashlib.sha256()
    with open(tif, "rb") as fh:
        for c in iter(lambda: fh.read(8 << 20), b""):
            h.update(c)
    rep.update(bytes=tif.stat().st_size, sha256=h.hexdigest())
    return rep, problems


def _checked(fn, path):
    """A validator that cannot even read the product has found a failure, not raised an excuse to skip one."""
    try:
        return fn(path)
    except Exception as e:
        return None, [f"{path.name} unreadable: {type(e).__name__}: {e}"]


def _append_esd(rows):
    # written immediately, not batched to the end of the orbit loop: a crash between stages must not cost the
    # diagnostics for stages that already finished (lost once for orb65/2023-04-26_2023-05-08)
    p = CFG.TABLES / "p82_esd_diagnostics.csv"
    old = pd.read_csv(p) if p.exists() else pd.DataFrame()
    pd.concat([old, pd.DataFrame(rows)]).drop_duplicates(
        ["rel_orbit", "pre_date", "event_date", "subswath"], keep="last").to_csv(p, index=False)
    return p


def _fail(r, what, problems=()):
    if r is not None and r.returncode != 0:
        print(r.stdout[-1500:]); print(r.stderr[-1500:])
    for x in problems:
        print(f"     FAIL: {x}", flush=True)
    raise SystemExit(f"{what} failed -- stopping rather than leaving a gap in the chain")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orbit", type=int, required=True)
    ap.add_argument("--pairs", type=int, default=0, help="0 = every consecutive 12-day pair on the orbit")
    ap.add_argument("--memory", default="16G")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    prod = pd.read_csv(CFG.TABLES / "p80_c1_frozen_products.csv")
    acq = pd.read_csv(CFG.TABLES / "p80_c1_frozen_acquisitions.csv")
    dates = list(acq[acq.rel_orbit == a.orbit].sort_values("date").date)
    if len(dates) < 2:
        raise SystemExit(f"orbit {a.orbit}: {len(dates)} acquisitions -- no pair")
    pairs = [(dates[i], dates[i + 1]) for i in range(len(dates) - 1)]
    if a.pairs:
        pairs = pairs[:a.pairs]
    WORK.mkdir(parents=True, exist_ok=True)
    zips = {d: sorted(str(SLC / f"{n}.zip") for n in prod[(prod.rel_orbit == a.orbit) & (prod.date == d)].name)
            for d in dates}
    absent = sorted(d for d, v in zips.items() if any(not Path(z).exists() for z in v))
    if absent:
        raise SystemExit(f"orbit {a.orbit}: SAFE not on disk for {absent} -- do not start SNAP on a partial set")
    sw_list = subswaths_for(a.orbit)
    print(f"orbit {a.orbit}: {len(dates)} acquisitions -> {len(pairs)} consecutive 12-day pairs; "
          f"{'+'.join(sw_list)} staged one JVM per subswath"
          f"{', merged' if len(sw_list) > 1 else ''} before one terrain correction", flush=True)
    for m, s in pairs:
        role = "EVENT" if s == dates[-1] else "PRE"
        out = WORK / f"coh_orb{a.orbit}_{m}_{s}.tif"
        ok_out = out.with_name(out.name + ".ok.json")
        dt = (pd.Timestamp(s) - pd.Timestamp(m)).days
        print(f"  [{role}] {m} -> {s}  ({dt} d)", flush=True)
        # A .tif on disk is NOT success. Only a validated product carries an .ok.json whose recorded size matches.
        if out.exists() or ok_out.exists():
            if out.exists() and ok_out.exists() and json.loads(ok_out.read_text())["final"]["bytes"] == out.stat().st_size:
                print("     validated product exists, skipping", flush=True); continue
            raise SystemExit(f"{out.name}: output without a matching validation record -- quarantine or delete it "
                             f"by hand; it must never satisfy the completion gate")
        # stage dir sits outside p83's top-level coh_orb*.tif glob
        pdir = WORK / "_stage" / f"orb{a.orbit}" / f"{m}_{s}"
        pdir.mkdir(parents=True, exist_ok=True)
        record = dict(rel_orbit=a.orbit, pre_date=m, event_date=s, subswaths=sw_list, memory=a.memory,
                      image=IMAGE, stages=[])
        dims = []
        for sw in sw_list:
            dim = pdir / f"{sw.lower()}_deburst.dim"
            ok = pdir / f"{sw.lower()}_deburst.ok.json"
            if dim.exists() and ok.exists():
                print(f"     {sw}: validated checkpoint exists, reusing", flush=True)
                record["stages"].append(json.loads(ok.read_text())); dims.append(dim); continue
            quarantine(dim, dim.with_suffix(".data"), ok)
            gx = pdir / f"graph_{sw}.xml"
            gx.write_text(graph_subswath(zips[m], zips[s], sw, str(dim)))
            dims.append(dim)
            if a.dry_run:
                continue
            t_start = _utc()
            print(f"     {sw}: Back-Geocoding -> ESD -> Coherence -> Deburst  (start {t_start})", flush=True)
            r, el = run_gpt(gx, pdir / f"log_{sw}.txt", pdir / f"snaplog_{sw}", a.memory)
            rep, problems = _checked(validate_dim, dim) if r.returncode == 0 else (None, [f"gpt exit {r.returncode}"])
            if problems:
                quarantine(dim, dim.with_suffix(".data"))
                _fail(r, f"{sw} stage for {out.name}", problems)
            st = dict(stage=sw, start_utc=t_start, end_utc=_utc(), elapsed_s=round(el), validation=rep)
            ok.write_text(json.dumps(st, indent=1))
            record["stages"].append(st)
            p = _append_esd(esd_rows(r.stdout + r.stderr, a.orbit, m, s, [sw]))
            print(f"     {sw}: PASS in {el:.0f}s -> {dim.name}; ESD -> {p.name}", flush=True)
        staged = pdir / "merged_tc.tif"
        quarantine(staged)
        gx = pdir / "graph_merge_tc.xml"
        gx.write_text(graph_merge_tc([str(d) for d in dims], str(staged)))
        if a.dry_run:
            continue
        t_start = _utc()
        print(f"     {'TOPSAR-Merge -> ' if len(dims) > 1 else ''}Terrain-Correction  (start {t_start})", flush=True)
        r, el = run_gpt(gx, pdir / "log_merge_tc.txt", pdir / "snaplog_merge_tc", a.memory)
        rep, problems = _checked(validate_final, staged) if r.returncode == 0 and staged.exists() else \
            (None, [f"gpt exit {r.returncode}" if r.returncode else "no output written"])
        if problems:
            quarantine(staged)
            _fail(r, f"merge/TC for {out.name}", problems)
        record["stages"].append(dict(stage="merge_tc", start_utc=t_start, end_utc=_utc(), elapsed_s=round(el)))
        record["final"] = rep
        # record first, then the atomic rename: a crash in between leaves an .ok.json with no .tif, which the
        # completion gate above refuses -- never a .tif that looks finished without having been validated
        ok_out.write_text(json.dumps(record, indent=1))
        os.replace(staged, out)
        print(f"     PASS {out.stat().st_size/1e9:.2f} GB in {el:.0f}s -> {out.name}", flush=True)
    print(f"-> {WORK}")


if __name__ == "__main__":
    main()
