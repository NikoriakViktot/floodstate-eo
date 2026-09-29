# New in floodstate-eo, 2026-09-29 (review 2026-09-28, F10). STATUS: ACTIVE.
"""P77f -- the transitive lineage of every M6 label version, down to the satellite windows (docs/LABEL_CONTRACTS.md).

The label scripts guard their direct inputs by file name; this script follows what those inputs were made from. For each
label version it records the M2 variant named in the label raster's tags, that M2's feature list (the p65a manifest for
the original model, the p67b feature table for a restricted one), how many of those features come from the post-event
TRACE window, the composite windows they span, where the operating thresholds came from, and whether a TEST prediction
was read by the label script (v003: a pre-registered diagnostic look at the U0d TEST prediction, review F11).
`uses_trace_transitively` is computed from the feature list, never typed.

Outputs: <case_study>/tables/m6_label_lineage.csv
"""
from __future__ import annotations

import importlib
import json

import pandas as pd
import rasterio

from floodstate_eo import _kakhovka_legacy_config as CFG

OUT = CFG.BULK_ROOT / "frames10"
VERSIONS = {"v002": "m6_labels_v002.tif", "v003_A": "m6_labels_v003_A.tif", "v002_notrace": "m6_labels_v002_notrace.tif", "v004": "m6_labels_v004.tif"}
M2 = {"": dict(model="M2_PRODUCTION_CANDIDATE_CORRECTED10M", features="p65a_feature_manifest.csv", folds="p65b_m2_folds.csv",
               thresholds="in-sample scores of the outer-train forest (superseded, review F09)"),
      "_notrace": dict(model="M2_PRODUCTION_CANDIDATE_CORRECTED10M_NOTRACE", features="p67b_features_notrace.csv", folds="p65b_m2_folds_notrace.csv",
                       thresholds="inner out-of-fold scores, fit and calibration cells disjoint (review F09)")}


def windows():
    return importlib.import_module("floodstate_eo.optical.p54b_frame_composites_10m").WIN     # PRE / EVENT / TRACE dates


def main():
    W = windows(); rows = []
    for ver, fn in VERSIONS.items():
        for fid in ("B1", "B2"):
            p = OUT / fid / fn
            if not p.exists():
                continue
            with rasterio.open(p) as s:
                tags = s.tags()
            v = tags.get("m2_variant", "")
            m2_tag = "_notrace" if "_notrace" in v else ""                  # untagged rasters predate the variant tag
            M = M2[m2_tag]; f = pd.read_csv(CFG.TABLES / M["features"]).feature.tolist()
            trace = [x for x in f if "trace" in x.lower()]
            used = sorted({w for x in f for w in ("pre", "event", "trace") if f"_{w}" in x.lower()})
            rows.append(dict(label_version=ver, frame=fid, file=fn, direct_inputs=tags.get("inputs_read", "labels.tif, flood_central, v002 raster, S1 May / 06-01..02 / peak scenes"),
                             m2_model=M["model"], m2_n_features=len(f), m2_trace_features=len(trace), m2_windows="|".join(used),
                             windows_dates="; ".join(f"{w} {W[w][0]}..{W[w][1]}" for w in used if w in W),
                             threshold_source=M["thresholds"], threshold_table=M["folds"],
                             uses_trace_transitively=bool(trace), label_script_read_test_prediction=ver.startswith("v003"),   # v003: a diagnostic look; F11
                             s1_derived_training_labels_of_m2=True))
    D = pd.DataFrame(rows); D.to_csv(CFG.TABLES / "m6_label_lineage.csv", index=False)
    print(D[["label_version", "frame", "m2_model", "m2_n_features", "m2_trace_features", "uses_trace_transitively", "label_script_read_test_prediction"]].to_string(index=False))
    print(json.dumps({"-> tables": "m6_label_lineage.csv"}))


if __name__ == "__main__":
    main()
