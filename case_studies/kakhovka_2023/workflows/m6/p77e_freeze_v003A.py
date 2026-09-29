# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Writes the freeze record of m6_labels_v003_A; builds nothing.
# 2026-09-29: `--version v004` writes the freeze record of m6_labels_v004 (the v003_A rule on the corrected M2, review
# F09/F10) from its own build manifest; the default keeps the v003_A record exactly as before.
"""P77e -- freeze m6_labels_v003_A (maintainer decision 2026-09-25).

STATUS, NOT PROMOTION (same wording as p62): the labels stay WEAK REFERENCE. Freezing fixes which pixels supervise and
score the M6 arms; it does not make an S1 x optical rule ground truth. Variant B stays SENSITIVITY_ONLY and is not frozen.

The record binds: the p77d build manifest (rules, source sha256, output sha256), the sha256 of the rasters as they are on
disk NOW (must equal the manifest), the git commit of this repository, the reproducibility gate result passed in with
--gate (a clean-tree rebuild that reproduces both rasters bit for bit), and the arms trained on these labels.
Any change to the rule, the scene QA or the sources is a NEW version (v004), never an edit of v003_A.

Output: <case_study>/tables/m6_labels_v003_A_FROZEN.json
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, time
from pathlib import Path
from floodstate_eo import _kakhovka_legacy_config as CFG

ROOT = Path(__file__).resolve().parents[2]
OUT = CFG.BULK_ROOT / "frames10"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(16 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--gate", required=True, help="reproducibility gate result, e.g. 'PASS: clean tree at <sha> bitwise identical'")
    ap.add_argument("--version", default="v003_A", choices=["v003_A", "v004"]); a = ap.parse_args()
    if a.version == "v004":
        return freeze_v004(a.gate)
    man = json.loads((CFG.TABLES / "p77d_v003_A_manifest.json").read_text())
    on_disk = {f: sha(OUT / f / "m6_labels_v003_A.tif") for f in ("B1", "B2")}
    for f, s in on_disk.items():
        assert s == man["output_sha256"][f], f"{f}: raster on disk ({s[:12]}) differs from the p77d manifest ({man['output_sha256'][f][:12]}); refuse to freeze"
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True).stdout.strip()
    rec = dict(product="m6_labels_v003_A", status="M6_LABELS_V003_A_FROZEN", frozen_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               set_by="maintainer decision 2026-09-25 (session note in NEXT_STEPS.md, D3)",
               meaning="WEAK REFERENCE labels, frozen for supervision and scoring; not ground truth; not flood-mapping accuracy",
               rasters={f: str(OUT / f / "m6_labels_v003_A.tif") for f in on_disk}, sha256=on_disk,
               build_manifest="tables/p77d_v003_A_manifest.json", build_commit=man["code_commit"], build_created_utc=man["created_utc"],
               sources_sha256=man["sources_sha256"], freeze_commit=git, freeze_tree_dirty_tracked=bool(dirty),
               reproducibility_gate=a.gate,
               ontology="0 LAND, 1 EVENT_FLOOD, 2 REFERENCE_WATER, 255 UNKNOWN (band 1); bands 2-11 see p77d",
               positives_note="EVENT_FLOOD is pixel-identical to m6_labels_v002 FLOOD (transition table p77d_v003_A_transition_v002.csv)",
               arms_on_these_labels=["U0d_B1B2_v003A", "U2_B1B2_v003A", "U2b_B1B2_v003A"],
               variant_B="SENSITIVITY_ONLY, not frozen (June-referenced scene QA lets event-period behaviour filter the PRE reference)",
               change_policy="any change of rule, scene QA or sources = v004; v003_A is never edited",
               known_caveats=["W_pre (S1 06-01/02) is both an input of U2b and an ingredient of EVENT_FLOOD (w_pre_state = 0)",
                              "REFERENCE_WATER needs >= 3 admitted May dates; EXTRAPOLATED and UNOBSERVED domains are UNKNOWN",
                              "S1 dark-water onset on reed beds below the normal water surface is a depth signal (p95)"])
    p = CFG.TABLES / "m6_labels_v003_A_FROZEN.json"; p.write_text(json.dumps(rec, indent=1)); print("->", p)


def freeze_v004(gate):
    man = json.loads((CFG.TABLES / "p77d_v004_manifest.json").read_text())
    on_disk = {f: sha(OUT / f / "m6_labels_v004.tif") for f in ("B1", "B2")}
    for f, s in on_disk.items():
        assert s == man["output_sha256"][f], f"{f}: raster on disk ({s[:12]}) differs from the p77d manifest; refuse to freeze"
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True).stdout.strip()
    rec = dict(product="m6_labels_v004", status="M6_LABELS_V004_FROZEN", frozen_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               set_by="maintainer decisions 2026-09-29 (Stage 2 of the response to the 2026-09-28 review: F09 inner out-of-fold "
                      "thresholds; M2 without the post-event TRACE window)",
               meaning="WEAK REFERENCE labels, frozen for supervision and scoring; not ground truth; not flood-mapping accuracy",
               rule="the frozen v003_A rule (docs/LABEL_CONTRACTS.md) on M2_PRODUCTION_CANDIDATE_CORRECTED10M_NOTRACE and the v002 rule on it",
               rasters={f: str(OUT / f / "m6_labels_v004.tif") for f in on_disk}, sha256=on_disk,
               build_manifest="tables/p77d_v004_manifest.json", build_commit=man["code_commit"], build_created_utc=man["created_utc"],
               sources_sha256=man["sources_sha256"], freeze_commit=git, freeze_tree_dirty_tracked=bool(dirty),
               reproducibility_gate=gate, lineage="tables/m6_label_lineage.csv (uses_trace_transitively = False)",
               test_prediction_read_by_the_label_script=False,
               change_policy="any change of rule, scene QA, M2 or sources = a new version; v004 is never edited")
    p = CFG.TABLES / "m6_labels_v004_FROZEN.json"; p.write_text(json.dumps(rec, indent=1)); print("->", p)


if __name__ == "__main__":
    main()
