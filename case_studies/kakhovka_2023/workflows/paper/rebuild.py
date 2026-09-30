# New in floodstate-eo, 2026-09-29 (review 2026-09-28, F16). STATUS: ACTIVE.
"""rebuild -- the order of the paper's computations as data (a DAG), and one command per reproducibility level.

  --level 0   the tiny open geodomain: the reconstruction + Monte-Carlo chain on synthetic inputs (seconds; no data)
  --level 1   the publication layer from the committed tables: tables T*, claims, manuscript fill, table-only figures, notebooks,
              tests (minutes; no bulk data)
  --level 2   the full chain from the processed inputs under $FLOODSTATE_DATA_ROOT (days; manifests/load_bearing_inputs.csv),
              ending with level 1
--list prints the DAG (id, level, needs, environment, command); --dry-run prints the commands of a level; --from ID resumes a
level at that step. Every executed step appends a run record (git commit, dirty flag, command, start, seconds, exit code) to
<case_study>/tables/rebuild_runs.jsonl. Steps marked env=swot run in the SWOT-DNIPRO environment ($SWOT_DNIPRO_ROOT/.venv,
PYTHONPATH=src), which the ICESat-2 pulls need (p57 geopandas chain).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
CS = "case_studies/kakhovka_2023"; M6 = f"{CS}/workflows/m6"; PAPER = f"{CS}/workflows/paper"
SEEDS = ("20260923", "20261001", "20261002")

# (id, level, needs, env, command) -- the order is the topological order
STEPS = [("tiny_geodomain", 0, [], "fs", ["examples/tiny_geodomain/run.py", "--draws", "100"])]
# ---- level 2: physical reconstruction --------------------------------------------------------------------------------------
STEPS += [
    ("p73_rev2", 2, [], "fs", [f"{M6}/p73_rf20_surface.py", "--rev", "2", "--jobs", "16"]),        # RF20: independent context, first
    ("p73q_rev2", 2, ["p73_rev2"], "fs", [f"{M6}/p73q_surface_qa.py", "--rev", "2"]),
    ("p59k", 2, [], "fs", [f"{M6}/p59k_kherson_frame.py"]),                          # the Kherson gauge in Paper 1's frame (v6)
    ("p95j", 2, [], "swot", [f"{M6}/p95j_terrain_variogram.py"]),
    ("p95", 2, ["p59k", "p95j"], "fs", [f"{M6}/p95_hand_daily_inundation.py", "--rule", "connected_ceiling", "--seam-check"]),
    ("p95k", 2, ["p95"], "fs", [f"{M6}/p95k_inhulets_gauge_check.py"]),
]
_P95 = f"{M6}/p95_hand_daily_inundation.py"
STEPS += [(f"p95_{k}", 2, ["p95"] + (["p95k"] if k == "inhulets_gauge_node" else []), "fs", [_P95, *args, "--no-rasters"]) for k, args in (   # structural sensitivities (T12, FigS02)
    ("hand_and_ceiling", ["--rule", "hand_and_ceiling"]), ("ceiling_only", ["--rule", "ceiling_only"]), ("dem_uncorrected", ["--dem-bias", "none"]),
    ("closure_p59", ["--closure", "p59_reservoir", "--margin", "0.5"]), ("conn4", ["--connectivity", "4"]), ("seed_mainstem", ["--seed-network", "main_stem"]),
    ("maxgap3", ["--max-gap-days", "3"]), ("riveraware", ["--wse-river-aware"]), ("fallback10km", ["--fallback-max-km", "10"]),
    ("inhulets_gauge_node", ["--inhulets-gauge-node"]))]
STEPS += [
    ("p95c_rasters", 2, ["p95"], "fs", [f"{M6}/p95c_icesat2_check.py", "--step", "rasters"]),
    ("p95c_icesat", 2, ["p95c_rasters", "p95j"], "swot", [f"{M6}/p95c_icesat2_check.py", "--step", "icesat"]),
    ("p95d", 2, ["p95", "p73_rev2"], "fs", [f"{M6}/p95d_agreement_by_surface.py", "--date", "2023-06-09"]),
    ("p95e", 2, ["p95", "p95j"], "fs", [f"{M6}/p95e_uncertainty_mc.py", "--n", "1000", "--workers", "8"]),
    ("p95e_convergence", 2, ["p95e"], "fs", [f"{M6}/p95e_uncertainty_mc.py", "--mode", "convergence", "--seed", "20261001", "--days", "key"]),
    ("p95e_ablation", 2, ["p95e"], "fs", [f"{M6}/p95e_uncertainty_mc.py", "--mode", "ablation", "--n", "250"]),
    ("p95e_wse_threshold", 2, ["p95e"], "fs", [f"{M6}/p95e_uncertainty_mc.py", "--mode", "wse-threshold"]),
    ("p95l", 2, ["p95"], "fs", [f"{M6}/p95l_support_domain.py"]),
    ("p95b", 2, ["p95"], "fs", [f"{M6}/p95b_hand_dyn_summary.py"]),
    ("p95f", 2, ["p95"], "fs", [f"{M6}/p95f_reservoir_balance.py"]),
    ("p95i", 2, ["p95f"], "fs", [f"{M6}/p95i_hypsometry_compare.py"]),
    ("p95h", 2, ["p95f"], "fs", [f"{M6}/p95h_reservoir_maps.py"]),                  # reservoir drawdown: exposure with Sentinel-2 (Fig11), model extent and S1 (FigS08)
    ("p95m", 2, ["p95f"], "fs", [f"{M6}/p95m_reservoir_depth.py"]),                  # reservoir water depth (Fig10, T21b)
    ("p95n", 2, ["p95", "p95l"], "fs", [f"{M6}/p95n_flood_depth_summary.py"]),      # flood depth below the dam (T12e)
    ("p95g", 2, ["p95e"], "fs", [f"{M6}/p95g_mc_emulator.py"]),
]
# ---- level 2: weak labels, surface context and the U-Net diagnostics ------------------------------------------------------------
STEPS += [
    ("p65b_notrace", 2, [], "fs", ["-m", "floodstate_eo.fusion.p65b_m2_spatial_cv", "--baselines", "preall", "--regimes", "block", "buffered", "--exclude", "trace"]),
    ("p65b_withtrace", 2, [], "fs", ["-m", "floodstate_eo.fusion.p65b_m2_spatial_cv", "--baselines", "preall", "--regimes", "block"]),
    ("p67b", 2, ["p65b_notrace"], "fs", ["-m", "floodstate_eo.fusion.p67b_production_candidate", "--exclude", "trace"]),
    ("p68", 2, ["p67b"], "fs", [f"{M6}/p68_threshold_uncertainty.py", "--tag", "_notrace"]),
    ("p77", 2, ["p68"], "fs", [f"{M6}/p77_m6_labels_v002.py", "--m2-tag", "_notrace"]),
    ("p77d", 2, ["p77"], "fs", [f"{M6}/p77d_m6_labels_v003_final.py", "--variant", "A", "--m2-tag", "_notrace"]),
    ("p77f", 2, ["p77d"], "fs", [f"{M6}/p77f_label_lineage.py"]),
    ("p77g", 2, ["p77d"], "fs", [f"{M6}/p77g_label_version_change.py"]),
]
for sd in SEEDS:
    for arm in ("U0d", "U2", "U2b", "U1"):
        STEPS.append((f"p86_{arm}_v004_{sd}", 2, ["p77d", "p73_rev2"], "fs", [f"{M6}/p86_m6_train_arm.py", "--arm", arm, "--labels", "v004", "--seed", sd]))
    STEPS.append((f"p86_U2_v002nt_{sd}", 2, ["p77", "p73_rev2"], "fs", [f"{M6}/p86_m6_train_arm.py", "--arm", "U2", "--labels", "v002_notrace", "--seed", sd]))
for sp in ("m6_split_s7p5", "m6_split_s15", "m6_split_s20"):
    STEPS.append((f"p86_U2_v004_{sp}", 2, ["p77d", "p73_rev2"], "fs", [f"{M6}/p86_m6_train_arm.py", "--arm", "U2", "--labels", "v004", "--split", sp]))
arms = [s[0] for s in STEPS if s[0].startswith("p86_")]
for sd, sfx in zip(SEEDS, ("", "_s20261001", "_s20261002")):
    for a, b in (("U0d", "U2"), ("U0d", "U1"), ("U2", "U2b")):
        STEPS.append((f"p88_{a}_{b}_v004{sfx}", 2, arms, "fs", [f"{M6}/p88_m6_compare_arms.py", a, b, "--run", f"v004{sfx}"]))
_runs = [f"{a}_B1B2_{lab}{sfx}" for sfx in ("", "_s20261001", "_s20261002") for a, lab in (("U0d", "v004"), ("U2", "v004"), ("U2b", "v004"), ("U1", "v004"), ("U2", "v002nt"))]
_pairs = [f"{x}{sfx}:{y}{sfx}" for sfx in ("", "_s20261001", "_s20261002") for x, y in (("U2_B1B2_v002nt", "U2_B1B2_v004"), ("U2_B1B2_v004", "U2b_B1B2_v004"), ("U0d_B1B2_v004", "U2_B1B2_v004"))]
STEPS += [
    ("p90_v004", 2, arms, "fs", [f"{M6}/p90_v003_refwater_endpoint.py", "--labels", "v004", "--runs", *_runs, "--pairs", *_pairs]),
    ("p86s", 2, [s[0] for s in STEPS if s[0].startswith("p88_")], "fs", [f"{M6}/p86s_seed_summary.py"]),
    ("p92", 2, arms, "fs", [f"{M6}/p92_flood_area_dam_to_liman.py", "--runs", "U2_B1B2_v1", "U2_B1B2_v003A", "U2b_B1B2_v003A",
                             *[f"{a}_B1B2_v004{sfx}" for sfx in ("", "_s20261001", "_s20261002") for a in ("U2", "U2b")],
                             "--map-runs", "U2_B1B2_v1", "U2b_B1B2_v003A", "U2b_B1B2_v004"]),
]
# ---- level 1: the publication layer ---------------------------------------------------------------------------------------------
L2_ALL = [s[0] for s in STEPS if s[1] == 2]
STEPS += [
    ("p96", 1, L2_ALL, "fs", [f"{PAPER}/p96_paper_tables.py"]),
    ("p96_check", 1, ["p96"], "fs", [f"{PAPER}/p96_paper_tables.py", "--check"]),
    ("fill_evidence", 1, ["p96"], "fs", [f"{PAPER}/fill_evidence.py"]),
    ("render_claims", 1, ["fill_evidence"], "fs", [f"{PAPER}/render_claims.py"]),
    ("fill_manuscript", 1, ["p96"], "fs", [f"{PAPER}/fill_manuscript.py"]),
    ("p97_tables_only", 1, ["p96"], "fs", [f"{PAPER}/p97_paper_figures.py", "--tables-only"]),
    ("p99", 1, ["p96"], "fs", [f"{PAPER}/p99_build_notebooks.py", "--build", "--execute"]),
    ("pytest", 1, ["p96", "fill_manuscript", "render_claims"], "fs", ["-m", "pytest", "-q"]),
]
CWD = {"fill_evidence": f"{PAPER}", "render_claims": f"{PAPER}"}           # these two import their sibling module by name


def _git():
    r = lambda *a: subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True).stdout.strip()
    return r("rev-parse", "HEAD"), bool(r("status", "--porcelain", "--untracked-files=no"))


def command(step):
    sid, _, _, env, cmd = step
    if env == "swot":
        py = Path(os.environ.get("SWOT_DNIPRO_ROOT", Path.home() / "repo" / "SWOT-DNIPRO")) / ".venv" / "bin" / "python"
    else:
        py = Path(sys.executable)
    args = [str(py), *cmd]
    if sid in CWD:                                                        # run from the paper directory with a relative script path
        args = [str(py), Path(cmd[0]).name, *cmd[1:]]
    return args


def run(level, dry=False, start=None, only=None):
    steps = [s for s in STEPS if s[1] == level or (level == 2 and s[1] == 1)] if only is None else [s for s in STEPS if s[0] in set(only)]
    if only is not None:
        missing = set(only) - {s[0] for s in steps}; assert not missing, f"unknown steps: {sorted(missing)}"
    if start:
        ids = [s[0] for s in steps]; steps = steps[ids.index(start):]
    log = REPO / CS / "tables" / "rebuild_runs.jsonl"
    for s in steps:
        args = command(s); cwd = REPO / CWD.get(s[0], ".")
        print(("DRY  " if dry else "RUN  ") + s[0] + ": " + " ".join(args), flush=True)
        if dry:
            continue
        env = dict(os.environ); env["PYTHONPATH"] = str(REPO / "src") + os.pathsep + env.get("PYTHONPATH", "")
        commit, dirty = _git(); t0 = time.time()
        rc = subprocess.run(args, cwd=cwd, env=env).returncode
        with open(log, "a") as f:
            f.write(json.dumps(dict(step=s[0], level=s[1], command=args, cwd=str(cwd.relative_to(REPO)), git_commit=commit, git_dirty_tracked=dirty,
                                    start_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)), seconds=round(time.time() - t0, 1), exit_code=rc)) + "\n")
        if rc != 0:
            raise SystemExit(f"step {s[0]} failed (exit {rc}); resume with --from {s[0]}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--level", type=int, choices=[0, 1, 2]); ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--from", dest="start")
    ap.add_argument("--steps", nargs="+", help="run exactly these steps, in DAG order (e.g. the physical reconstruction after an input change)"); a = ap.parse_args()
    ids = [s[0] for s in STEPS]
    for s in STEPS:                                                        # the DAG must be topologically ordered
        assert all(n in ids and ids.index(n) < ids.index(s[0]) for n in s[2]), f"{s[0]}: a dependency is missing or later"
    if a.steps:
        run(None, a.dry_run, a.start, only=a.steps); return
    if a.list or a.level is None:
        for s in STEPS:
            print(f"L{s[1]}  {s[0]:28s} env={s[3]:4s} needs={','.join(s[2][:4]) + (' ...' if len(s[2]) > 4 else '') or '-'}")
        return
    if a.level == 2 and not Path(os.environ.get("FLOODSTATE_DATA_ROOT", "/nonexistent")).exists() and not a.dry_run:
        from floodstate_eo import _kakhovka_legacy_config as CFG
        if not CFG.BULK_ROOT.exists():
            raise SystemExit("level 2 needs the processed inputs ($FLOODSTATE_DATA_ROOT); see manifests/load_bearing_inputs.csv")
    run(a.level, a.dry_run, a.start)


if __name__ == "__main__":
    main()
