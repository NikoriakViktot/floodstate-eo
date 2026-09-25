# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Renders publication/claims.md from publication/evidence_matrix.csv.
"""render_claims -- the claims register is the CSV (same schema as Paper 1's manuscript_evidence_matrix.csv, plus
evidence_level and tier); claims.md is a rendering of it and is never edited by hand. Run after p96 fills n/value/uncertainty.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

PUB = Path(__file__).resolve().parents[2] / "publication"
ORDER = ["primary", "secondary", "exploratory"]


def main():
    M = pd.read_csv(PUB / "evidence_matrix.csv").fillna("")
    out = ["# Claims register (rendered from evidence_matrix.csv -- do not edit by hand)", "",
           "Evidence levels: independent_physical > cross_sensor > weak_label_agreement > contextual. "
           "Every model number is agreement with weak reference labels, never flood-mapping accuracy. "
           "Areas carry their semantics (observed_S1 / mapped_UNet / terrain_reconstructed / literature_reported).", ""]
    for tier in ORDER:
        out.append(f"## {tier.capitalize()} claims"); out.append("")
        for _, r in M[M.tier == tier].iterrows():
            out += [f"### {r.claim_id} [{r.evidence_level}] -- section {r.manuscript_section}", "",
                    f"**Statement.** {r.claim}", "",
                    f"- **Independent:** {r.independent}", f"- **Result type / dataset:** {r.result_type} / {r.dataset}",
                    f"- **Independent unit:** {r.independent_unit}; **n:** {r.n}",
                    f"- **Value:** {r.value}; **uncertainty:** {r.uncertainty}",
                    f"- **Evidence:** tables {r.source_table}; figures {r.source_figure}",
                    f"- **Scope:** {r.scope}", f"- **Caveat:** {r.caveat}",
                    f"- **Status:** {r.validation_status} / {r.publication_status}" + (f"; superseded by {r.superseded_by}" if r.superseded_by else ""), ""]
    (PUB / "claims.md").write_text("\n".join(out)); print("->", PUB / "claims.md", len(M), "claims")


if __name__ == "__main__":
    main()
