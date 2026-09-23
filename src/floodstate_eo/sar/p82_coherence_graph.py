# Provenance: SWOT-DNIPRO scripts/p82_coherence_graph.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CANONICAL, per 19_MIGRATION_MANIFEST.csv row 20 (migration_phase=5).
# Import block only: swot_dnipro package import -> floodstate_eo. SLC/WORK absolute host paths, the docker
# image name and the memory-safety flags (-q 2 -c 1024M -x, added the same session as this migration after a
# live "Java heap space" incident on this machine's WSL2 memory cap) are left exactly as in the source --
# machine-specific, listed as Phase 6 config work in 06_CONFIGURATION_DESIGN.md.
"""P82 -- the frozen SNAP interferometric-coherence chain for one 12-day pair. ONE GRAPH, ONE PASS.

    SliceAssembly -> Apply-Orbit-File -> TOPSAR-Split(measured subswaths)
      -> per subswath: Back-Geocoding -> Enhanced-Spectral-Diversity -> Coherence(10x3) -> TOPSAR-Deburst
      -> TOPSAR-Merge (when more than one) -> Terrain-Correction (EPSG:32636, 20 m)

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
import argparse, re, subprocess, sys, time
from pathlib import Path
import pandas as pd
from .. import _kakhovka_legacy_config as CFG

SLC = Path("/home/niko/data_s1_slc")
WORK = Path("/home/niko/data_s1_coh")
IMAGE = "flood-snap:latest"
GPT = "/opt/snap/bin/gpt"
COVERAGE = "p80_subswath_coverage.csv"        # measured per orbit; there is no module-level subswath default
POLS = "VV,VH"
COH_RANGE, COH_AZIMUTH = 10, 3
PIXEL_M = 20.0


def _side(tag, zips, sw_list):
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
    for sw in sw_list:
        n.append(f'  <node id="spl_{tag}_{sw}"><operator>TOPSAR-Split</operator>'
                 f'<sources><sourceProduct refid="orb_{tag}"/></sources>'
                 f'<parameters><subswath>{sw}</subswath>'
                 f'<selectedPolarisations>{POLS}</selectedPolarisations></parameters></node>')
    return n


def graph(master_zips, slave_zips, out, sw_list):
    nodes = _side("m", master_zips, sw_list) + _side("s", slave_zips, sw_list)
    for sw in sw_list:
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
            f'<parameters><selectedPolarisations>{POLS}</selectedPolarisations></parameters></node>']
    if len(sw_list) > 1:
        srcs = "".join(f'<sourceProduct refid="deb_{sw}"/>' if i == 0 else f'<sourceProduct.{i} refid="deb_{sw}"/>'
                       for i, sw in enumerate(sw_list))
        nodes.append(f'  <node id="mrg"><operator>TOPSAR-Merge</operator>'
                     f'<sources>{srcs}</sources>'
                     f'<parameters><selectedPolarisations>{POLS}</selectedPolarisations></parameters></node>')
        pre_tc = "mrg"
    else:
        pre_tc = f"deb_{sw_list[0]}"
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
    return '<graph id="coh">\n  <version>1.0</version>\n' + "\n".join(nodes) + "\n</graph>\n"


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orbit", type=int, required=True)
    ap.add_argument("--pairs", type=int, default=0, help="0 = every consecutive 12-day pair on the orbit")
    ap.add_argument("--memory", default="12G")
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
          f"{'+'.join(sw_list)}"
          f"{' merged' if len(sw_list) > 1 else ''} before one terrain correction", flush=True)
    diag = []
    for m, s in pairs:
        role = "EVENT" if s == dates[-1] else "PRE"
        out = WORK / f"coh_orb{a.orbit}_{m}_{s}.tif"
        dt = (pd.Timestamp(s) - pd.Timestamp(m)).days
        print(f"  [{role}] {m} -> {s}  ({dt} d)", flush=True)
        if out.exists():
            print("     exists, skipping", flush=True); continue
        gx = WORK / f"graph_orb{a.orbit}_{m}_{s}.xml"
        gx.write_text(graph(zips[m], zips[s], str(out), sw_list))
        if a.dry_run:
            continue
        t0 = time.time()
        # -q 2 (not the CLI default of 32) and -c/-x cap and evict the JAI tile cache: this host's WSL2 VM
        # is capped at ~15 GB total (half of the Windows host's ~32 GB, no .wslconfig override), and a
        # 12G heap plus default-parallelism tile caching for a merged IW2+IW3 VV+VH product exhausted it --
        # observed as repeated "Java heap space" and the JAI tile scheduler silently re-running whole ESD
        # block passes from scratch instead of terminating. Raising the WSL2 memory cap is the real fix
        # (outputs/planning note); this is the workaround that fits inside the cap in the meantime.
        r = subprocess.run(["docker", "run", "--rm", "-v", f"{SLC}:{SLC}:ro", "-v", f"{WORK}:{WORK}",
                            IMAGE, GPT, str(gx), f"-J-Xmx{a.memory}", "-q", "2", "-c", "1024M", "-x"],
                           capture_output=True, text=True)
        (WORK / f"log_orb{a.orbit}_{m}_{s}.txt").write_text(r.stdout + "\n" + r.stderr)
        if r.returncode != 0 or not out.exists():
            print(r.stdout[-1500:]); print(r.stderr[-1500:])
            raise SystemExit(f"gpt failed on {out.name} -- stopping rather than leaving a gap in the chain")
        pair_diag = esd_rows(r.stdout + r.stderr, a.orbit, m, s, sw_list)
        diag += pair_diag
        # written immediately, not batched to the end of the orbit loop: a crash between pairs must not
        # cost the diagnostics for pairs that already finished (lost once for orb65/2023-04-26_2023-05-08)
        p = CFG.TABLES / "p82_esd_diagnostics.csv"
        old = pd.read_csv(p) if p.exists() else pd.DataFrame()
        pd.concat([old, pd.DataFrame(pair_diag)]).drop_duplicates(
            ["rel_orbit", "pre_date", "event_date", "subswath"], keep="last").to_csv(p, index=False)
        print(f"     {out.stat().st_size/1e9:.2f} GB in {time.time()-t0:.0f}s -> {p}", flush=True)
    print(f"-> {WORK}")


if __name__ == "__main__":
    main()
