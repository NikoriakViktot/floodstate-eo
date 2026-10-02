# New in floodstate-eo, 2026-10-02 (maintainer, option A: "run the frozen p25 for the downloaded dates that have no zone stack").
# STATUS: ACTIVE (one-off extension, recorded). Runs SWOT-DNIPRO's frozen p25 UNCHANGED; must run under SWOT-DNIPRO's Python
# environment (it imports `swot_dnipro`): ~/repo/SWOT-DNIPRO/.venv/bin/python <this file> ...
"""P25x -- extension of the per-date zone spectral stacks (zone_spectral/<ZONE>/<date>_{indices,class,water3,scl}.tif) to the
downloaded Sentinel-2 dates that SWOT-DNIPRO's p25 never stacked, without touching anything p25 already wrote.

WHY THE DATES WERE MISSING. p25 scans three SAFE stores (s2_zone_fetch, data_swot/sentinel, sentinel_p1_targeted) and, for
ZONE_2/3/4, the dates of the frozen p10 manifests. The event-period scenes of 15 June - 31 July 2023 were fetched later into
`sentinel_event_2023` for the 10 m frames (p52d / p54a) and never reached the zone grids.

WHAT THIS DRIVER DOES. Loads `scripts/p25_zone_spectral_stacks.py` of the sibling repository as a module and changes two things
at run time, nothing in its file: (1) `sentinel_event_2023` is appended to the SAFE stores (first store wins, so a date that
already has zips keeps them), (2) the per-regime composite builder is replaced by a no-op, so the frozen regime composites in
SWOT-DNIPRO/outputs/rasters/zone<N>/ are NOT rebuilt (p60 reads zone<N>_water_frac_PRE_BREACH_20m.tif from there). p25 itself
skips every date whose files exist (CACHED), so only the new dates are written -- with p25's own science (sentinel_preprocess:
BOA offset, seven indices, frozen water rule, k10e classes).

    --zone ZONE_2_KHERSON_DELTA --extra-dates <dates>       manifest zones (2/3/4): the dates are added with the zone's tile set
    --zone ZONE_1_KAKHOVKA_LOWER_DNIPRO --dates all          ZONE_1: every eastern-tile SAFE zip of the stores, the event store included
    --record                                                 after the runs: the new rows of the regenerated p25 manifests ->
                                                             <case_study>/tables/p25x_zone_stack_extension.csv, and the sibling
                                                             manifests restored to their committed content (in place: the
                                                             outputs/deliverables copies are hard links of them)

Run of 2026-10-02: 49 zone-dates written (ZONE_1 6, ZONE_2 13, ZONE_3 17, ZONE_4 13) = 17 of the 19 unstacked dates; 2023-07-31
(R007, one 78 MB zip) and 2024-05-25 (47 and 64 MB) stay without a stack -- orbit-edge slivers below p25's frozen 200 MB scene filter. The Paper 3 tables that read these stacks (p95h: every 2023 date observing
>= 50 % of the pool) exclude the extension dates explicitly (p95h.EXTENSION_DATES), so the paper is unchanged; the extension
serves the products for the hydraulic model (p102 RF by date, the inventory).
"""
from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
from pathlib import Path

SIB = Path(os.environ.get("SWOT_DNIPRO_ROOT", Path.home() / "repo" / "SWOT-DNIPRO"))
CS = Path(__file__).resolve().parents[2]
ZONES = ("ZONE_1_KAKHOVKA_LOWER_DNIPRO", "ZONE_2_KHERSON_DELTA", "ZONE_3_DNIPRO_BUG_ESTUARY", "ZONE_4_DAM_TO_KHERSON_FLOODWAY")
EVENT_STORE = "sentinel_event_2023"


def run(argv):
    sys.path.insert(0, str(SIB / "src"))
    spec = importlib.util.spec_from_file_location("p25", SIB / "scripts" / "p25_zone_spectral_stacks.py")
    p25 = importlib.util.module_from_spec(spec); spec.loader.exec_module(p25)
    p25.SAFE_DIRS = tuple(p25.SAFE_DIRS) + (p25.CFG.BULK_ROOT / EVENT_STORE,)

    def _no_composites(zone, G, man):
        print("  composites skipped: p25x extension run -- the frozen regime composites are not rebuilt", flush=True)
        return []
    p25.composites = _no_composites
    sys.argv = ["p25_zone_spectral_stacks.py", *argv]
    p25.main()


def record():
    import pandas as pd
    rows = []
    for z in ZONES:
        rel = f"outputs/tables/p25_zone_spectral_manifest_{z}.csv"; path = SIB / rel
        head = subprocess.run(["git", "-C", str(SIB), "show", f"HEAD:{rel}"], capture_output=True, text=True, check=True).stdout
        old = pd.read_csv(io.StringIO(head)); new = pd.read_csv(path)
        add = new[~new.date.isin(set(old.date))].copy()
        if len(add):
            add.insert(0, "zone", z); rows.append(add)
        if path.read_text() != head:
            with open(path, "w") as f:                                       # in place: keeps the hard-linked deliverables copy in step
                f.write(head)
        print(f"{z}: {len(add)} new dates recorded; sibling manifest restored to HEAD", flush=True)
    out = CS / "tables" / "p25x_zone_stack_extension.csv"
    T = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    keep = [c for c in ("zone", "date", "regime", "status", "tiles_expected", "tiles_found", "n_scenes", "tiles_complete", "valid_frac_inside",
                        "water_frac_of_valid", "scenes", "processing_baselines", "seconds") if c in T.columns]
    T[keep].to_csv(out, index=False)
    print(f"-> {out}: {len(T)} zone-dates; per zone {T.groupby('zone').size().to_dict() if len(T) else {}}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--record"]:
        record()
    else:
        run(sys.argv[1:])
