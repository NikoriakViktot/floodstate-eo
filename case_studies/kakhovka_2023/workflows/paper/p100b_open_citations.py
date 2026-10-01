# New in floodstate-eo, 2026-10-01 (maintainer: "a file with the open quotations for the knowledge graph"). STATUS: ACTIVE.
"""p100b_open_citations -- the citations of the manuscript that are not yet verified against their source, as knowledge-graph input.

Reads docs/references.bib (entries whose `note` still carries VERIFY) and publication/manuscript_template.md; for every such reference
it lists the sentence(s) of the manuscript that cite it (author-year forms), the words quoted in them, the section, the DOI and what
must be checked in the source (from the bib note). Two papers forwarded by the maintainer but neither cited nor reachable
(Pulvirenti 2021, Cohen 2022) are appended as open items. Companion of p100_literature_theses (same node / edge style).

Outputs (publication/literature/): open_citations.json (items + nodes Reference / Quotation / OpenItem / Section + edges QUOTED_FROM,
IN_SECTION, NEEDS_VERIFICATION), open_citations.csv (one row per citing sentence), open_citations.md (readable).
"""
from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CS = HERE.parents[1]; REPO = CS.parents[1]; PUB = CS / "publication"; OUT = PUB / "literature"
ABBREV = ("et al.", "e.g.", "i.e.", "vs.", "cf.", "Fig.", "Figs.", "Eq.", "No.", "approx.", "ca.", "p.", "pp.", "St.", "Dr.")
EXTRA = [dict(key="Pulvirenti_2021", author="Pulvirenti, Luca and Squicciarino, Giuseppe and Fiori, Elisabetta and Ferraris, Luca and Puca, Silvia",
              title="A Tool for Pre-Operational Daily Mapping of Floods and Permanent Water Using Sentinel-1 Data", journal="Remote Sensing", year="2021", volume="13", pages="1342", doi="10.3390/rs13071342",
              note="not cited in the manuscript; forwarded claims (double bounce, no unique SAR signature of flooded vegetation) NOT checked -- the abstract only says flood maps have gaps from undetected flooded vegetation; full text unreachable by script (MDPI blocks)"),
         dict(key="Cohen_2022", author="Cohen, Juval and Heinilä, Kirsikka and Huokuna, Mikko and Metsämäki, Sari and Heilimo, Jyri and Sane, Mikko",
              title="Satellite-based flood mapping in the boreal region for improving situational awareness", journal="Journal of Flood Risk Management", year="2022", volume="15", pages="e12744", doi="10.1111/jfr3.12744",
              note="not cited in the manuscript; forwarded claim of an 'uncertain area' class for semi-forested terrain NOT checked; the abstract only says EMS and the S1 interpretation 'did not detect floods in forests'; full text unreachable by script (Wiley blocks)")]
NO_RECORD = ("Rikimaru_2002", "Pedregosa_2011")


def field(ch, name):
    m = re.search(r"\b" + name + r"\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}", ch, flags=re.S | re.I)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def read_bib():
    refs = {}
    for ch in re.split(r"\n(?=@)", (REPO / "docs" / "references.bib").read_text()):
        m = re.match(r"@(\w+)\{([^,]+),", ch)
        if not m:
            continue
        key = m.group(2).strip()
        refs[key] = dict(key=key, type=m.group(1), author=field(ch, "author"), title=field(ch, "title"), journal=field(ch, "journal") or field(ch, "booktitle") or field(ch, "howpublished"),
                         year=field(ch, "year"), volume=field(ch, "volume"), pages=field(ch, "pages"), doi=field(ch, "doi").replace("https://doi.org/", ""), note=field(ch, "note"))
    return refs


def surname(author):
    a = author.split(" and ")[0].strip().replace("{", "").replace("}", "")
    return (a.split(",")[0] if "," in a else a.split()[-1]).strip()


def protect(text):
    for ab in ABBREV:
        text = text.replace(ab, ab[:-1] + "․")                      # one-dot leader: never a sentence end
    return text


def unprotect(text):
    return text.replace("․", ".")


def citing_sentences(man, heads, sur, year):
    """Sentences of the template that cite `sur` + `year` (et al. / and X / & X; year in parentheses or not), with the section."""
    pat = re.compile(r"\b" + re.escape(sur) + r"(?: et al\.?| and [A-Z][a-z]+| & [A-Z][a-z]+)?\s*\(?" + re.escape(year) + r"\)?")
    out, seen = [], set()
    for m in pat.finditer(man):
        a = man.rfind("\n\n", 0, m.start()); a = a + 2 if a >= 0 else 0; b = man.find("\n\n", m.end()); b = b if b >= 0 else len(man)
        para = protect(man[a:b]); rel = m.start() - a
        ends = [x.end() for x in re.finditer(r"[.!?](?=\s|$)", para)]
        st = max([0] + [e for e in ends if e <= rel]); en = min([e for e in ends if e > rel] + [len(para)])
        sent = unprotect(re.sub(r"\s+", " ", para[st:en]).strip()); quotes = re.findall(r"[\"“]([^\"”]{8,})[\"”]", sent)
        if sent[:120] in seen:
            continue
        seen.add(sent[:120])
        sec = "front matter"
        for p, h in heads:
            if p <= m.start():
                sec = h
            else:
                break
        out.append(dict(section=sec, sentence=sent, quotations=quotes, has_table_placeholders=bool(re.search(r"\{\{T", sent))))
    return out


def main():
    t0 = time.time(); refs = read_bib(); man = (PUB / "manuscript_template.md").read_text()
    heads = [(m.start(), m.group(0).strip("# ").strip()) for m in re.finditer(r"^#{2,4} .+$", man, flags=re.M)]
    keys = [k for k, r in refs.items() if "VERIFY" in r["note"]]
    items = []
    for key in keys + [e["key"] for e in EXTRA]:
        r = refs.get(key) or next(e for e in EXTRA if e["key"] == key)
        cites = citing_sentences(man, heads, surname(r["author"]), r["year"]) if key in refs else []
        what = re.sub(r"^.*?VERIFY[:,]?\s*", "", r["note"]) if "VERIFY" in r["note"] else r["note"]
        status = ("no Crossref record; cite as is" if key in NO_RECORD else "not in the manuscript; full text unreachable" if key not in refs
                  else "full text unreachable; the number is only in a bib note" if key == "Lefebvre_2019" else "content quotation to locate in the source")
        ref = f"{r['author']} ({r['year']}). {r['title']}. {r['journal']}" + (f" {r['volume']}" if r["volume"] else "") + (f", {r['pages']}" if r["pages"] else "") + "."
        items.append(dict(key=key, status=status, reference=ref, doi=r["doi"], url=("https://doi.org/" + r["doi"]) if r["doi"] else "", what_to_verify=what, bib_note=r["note"],
                          n_citing_sentences=len(cites), citations=cites))
    nodes, edges, rows = [], [], []
    for it in items:
        nodes.append(dict(id=it["key"], type="Reference", label=it["reference"][:160], doi=it["doi"], url=it["url"], status=it["status"], what_to_verify=it["what_to_verify"]))
        if not it["citations"]:
            qid = f"Q-{it['key']}-0"; nodes.append(dict(id=qid, type="OpenItem", label=it["what_to_verify"][:200], section="(not cited in the manuscript text)", quotations=[]))
            edges.append(dict(source=qid, target=it["key"], relation="NEEDS_VERIFICATION"))
            rows.append(dict(key=it["key"], status=it["status"], section="", sentence="", quotations="", what_to_verify=it["what_to_verify"], doi=it["doi"], url=it["url"], reference=it["reference"]))
        for i, c in enumerate(it["citations"], 1):
            qid = f"Q-{it['key']}-{i}"
            nodes.append(dict(id=qid, type="Quotation", label=c["sentence"][:220], section=c["section"], quotations=c["quotations"], has_table_placeholders=c["has_table_placeholders"]))
            edges += [dict(source=qid, target=it["key"], relation="QUOTED_FROM"), dict(source=qid, target="SEC:" + c["section"], relation="IN_SECTION")]
            rows.append(dict(key=it["key"], status=it["status"], section=c["section"], sentence=c["sentence"], quotations=" | ".join(c["quotations"]), what_to_verify=it["what_to_verify"], doi=it["doi"], url=it["url"], reference=it["reference"]))
    for sec in sorted({e["target"] for e in edges if e["target"].startswith("SEC:")}):
        nodes.append(dict(id=sec, type="Section", label=sec[4:]))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "open_citations.json").write_text(json.dumps(dict(generated=time.strftime("%Y-%m-%d"), producer="p100b_open_citations.py",
                                                             purpose="open (unverified) citations of the manuscript: the sentence and the words quoted, where, and what must be checked in the source",
                                                             items=items, nodes=nodes, edges=edges), ensure_ascii=False, indent=1), encoding="utf-8")
    with (OUT / "open_citations.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "status", "section", "sentence", "quotations", "what_to_verify", "doi", "url", "reference"]); w.writeheader(); w.writerows(rows)
    md = [f"# Open citations to verify (generated {time.strftime('%Y-%m-%d')} by p100b from docs/references.bib and the manuscript template)", "",
          "One block per reference: the sentence(s) of the manuscript that cite it, the words quoted in them, the section, and what must be checked in the source.", ""]
    for it in items:
        md += [f"## {it['key']} — {it['status']}", f"- **Reference:** {it['reference']}" + (f" DOI [{it['doi']}]({it['url']})" if it["doi"] else ""), f"- **To verify:** {it['what_to_verify']}"]
        md += [f"- **{c['section']}:** {c['sentence']}" + ("  \n  quoted: " + " | ".join(f"“{q}”" for q in c["quotations"]) if c["quotations"] else "") for c in it["citations"]] or ["- (not cited in the manuscript text)"]
        md.append("")
    (OUT / "open_citations.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{len(items)} references, {sum(len(i['citations']) for i in items)} citing sentences, {len(rows)} rows -> {OUT}/open_citations.{{json,csv,md}} ({round(time.time() - t0, 1)} s)")
    for it in items:
        print(f"  {it['key']:20s} {it['n_citing_sentences']} | {it['status']}")


if __name__ == "__main__":
    main()
