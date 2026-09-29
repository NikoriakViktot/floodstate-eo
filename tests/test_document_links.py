"""Review F17: every relative image / table / document link of the published documents resolves inside the repository."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ["README.md", "apps/dashboard/README.md", "case_studies/kakhovka_2023/publication/manuscript.md",
        "case_studies/kakhovka_2023/publication/captions.md", "case_studies/kakhovka_2023/publication/claims.md",
        "case_studies/kakhovka_2023/literature_audit/article/Paper3_final.md"]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")


@pytest.mark.parametrize("doc", DOCS)
def test_relative_links_resolve(doc):
    p = ROOT / doc
    if not p.exists():
        pytest.skip(f"{doc} not present")
    bad = []
    for target in LINK.findall(p.read_text()):
        if re.match(r"^(https?:|mailto:|#)", target):
            continue
        t = target.split("#")[0]
        if t and not (p.parent / t).resolve().exists():
            bad.append(target)
    assert not bad, f"{doc}: unresolved links {bad[:10]}"
