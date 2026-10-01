"""The production text after the text pass of 2026-09-29/30 (maintainer): no retracted or superseded statement comes back, the
decided wordings are present, and the vertical frame is taken from Paper 1 rather than re-validated."""
import re
from pathlib import Path

CS = Path(__file__).resolve().parents[1] / "case_studies/kakhovka_2023"
TEXT = (CS / "publication/manuscript_template.md").read_text(encoding="utf-8")
FLAT = re.sub(r"\s+", " ", TEXT)


def test_no_retracted_or_superseded_statement():
    for bad in ("HAND reduces", "suppresses part of the cropland", "40 draws", "40 Monte-Carlo", "+0.216 m", "(−0.173 m)",
                "two frozen weak-label contracts", "30–40 km² per day", "signs of the paired comparisons are unchanged"):
        assert bad not in FLAT, bad


def test_decided_wordings_present():
    for good in ("did not reproduce under the corrected canonical ontology and three training seeds",
                 "This demonstrates sensitivity of the learned flood representation to the weak-label definition of pre-event water",
                 "is interpreted as a diagnostic of label-induced model behaviour",
                 "Removing frame-overlap duplication had little effect on within-domain spatial CV",
                 "Replacing it with out-of-fold threshold calibration restored the intended recall",
                 "The M2 score is not interpreted as a flood probability",
                 "The canonical weak labels used for every analysis of this paper",
                 "HAND therefore should not be interpreted as independently demonstrated to suppress cropland false positives"):
        assert good in FLAT, good


def test_no_internal_identifiers_in_the_article_body():
    """Maintainer, 2026-10-01: the article text carries results, not the repository's working names -- no script ids, label-set
    versions, decision tags, claim tags, split names or seed values from the abstract on (the build note before it may keep them)."""
    body = re.sub(r"\{\{[^}]*\}\}", "#", TEXT.split("## Abstract", 1)[1])       # table placeholders resolve to numbers; their filters are not text
    for pat in (r"\bv00[234]\w*", r"\b(p42|p60|p71|p73|p94|p95[a-z]+)\b", r"\bm6_split\w*", r"\bD-(SEED|MEMORY)\b", r"\[C\d{2}",
                r"\b2026(092\d|100\d)\b", r"claims\.md", r"references_to_verify"):
        assert not re.search(pat, body), (pat, re.search(pat, body).group(0))


def test_methods_give_the_formulas():
    for eq in ("(1) H_k(t) =", "(3) W_t = C_8(", "(7) A_new,dry(t) =", "(8) H_k^(j)(t) =", "(9) z^(j)(x) =", "(11) Q_eff(t) =", "(12) e_abs(t) =",
               "(13) POD = TP / (TP + FN)", "(14) CSI_chance = e / (a + b − e)", "(16) NDVI = (B08 − B04)/(B08 + B04)", "(17) L = BCE_masked"):
        assert eq in FLAT, eq


def test_vertical_frame_is_an_input_from_paper1():
    assert "The vertical frame is an input" in FLAT and "those tests are not repeated here" in FLAT
    for sec in ("## 4. Results", "## 5. Discussion"):
        assert sec in TEXT
    results = TEXT.split("## 4. Results")[1].split("## 5. Discussion")[0]
    assert "Water-surface input" not in results                       # the SWOT-gauge check is Paper 1's validation (T17 = input check)
    for block in ("### 4.1 The terrain-connectivity reconstruction", "### 4.2 Uncertainty and support", "### 4.3 Independent validation and support",
                  "### 4.4 Weak-label ML diagnostics"):
        assert block in results, block
