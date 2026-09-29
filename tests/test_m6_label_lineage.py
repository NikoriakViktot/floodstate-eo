"""Review F10: the label scripts guard their direct inputs by file name; the lineage follows what those inputs were made from.
v004 must not depend on the post-event TRACE window, neither directly nor through M2."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from floodstate_eo import _kakhovka_legacy_config as CFG

_P = Path(__file__).resolve().parents[1] / "case_studies/kakhovka_2023/workflows/m6/p77_m6_labels_v002.py"
_s = importlib.util.spec_from_file_location("p77", _P); P77 = importlib.util.module_from_spec(_s); _s.loader.exec_module(P77)


def test_the_guard_admits_the_corrected_m2_masks_and_still_forbids_trace():
    for ok in ("B1/labels.tif", "B1/flood_central.tif", "B1/flood_central_notrace.tif", "B2/flood_possible_notrace.tif"):
        P77._guard(Path(ok))
    for bad in ("B1/NDVI_trace_med.tif", "B1/flood_central_trace.tif", "B1/composite_trace.tif", "B1/p73_rf20/surface_class_20m.tif"):
        with pytest.raises(SystemExit):
            P77._guard(Path(bad))


def test_the_restored_feature_manifest_is_the_one_the_production_model_used():
    m = CFG.BULK_ROOT / "frames10" / "production_candidate_manifest.json"
    if not m.exists():
        pytest.skip("bulk production manifest not available")
    h = hashlib.sha256((CFG.TABLES / "p65a_feature_manifest.csv").read_bytes()).hexdigest()
    assert h == json.loads(m.read_text())["feature_manifest_hash"]


def test_the_v004_m2_has_no_trace_feature():
    p = CFG.TABLES / "p67b_features_notrace.csv"
    if not p.exists():
        pytest.skip("p67b --exclude trace not run yet")
    f = pd.read_csv(p).feature.tolist(); full = pd.read_csv(CFG.TABLES / "p65a_feature_manifest.csv").feature.tolist()
    assert not [x for x in f if "trace" in x.lower()] and set(f) <= set(full)
    assert len(f) == len(full) - sum("trace" in x.lower() for x in full)       # only the TRACE features were dropped


def test_the_lineage_table_marks_the_transitive_trace_dependency():
    p = CFG.TABLES / "m6_label_lineage.csv"
    if not p.exists():
        pytest.skip("p77f not run")
    L = pd.read_csv(p)
    old = L[L.label_version.isin(["v002", "v003_A"])]
    assert len(old) and old.uses_trace_transitively.all() and (old.m2_trace_features > 0).all()
    new = L[L.label_version.isin(["v002_notrace", "v004"])]
    assert (~new.uses_trace_transitively).all() and (new.m2_trace_features == 0).all() and (~new.label_script_read_test_prediction).all()
    assert not new.m2_windows.str.contains("trace").any()
