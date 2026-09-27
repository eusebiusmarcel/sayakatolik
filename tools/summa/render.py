#!/usr/bin/env python3
"""Render reviewed Summa translations into Hugo pages under content/id/summa/.

    python3 tools/summa/render.py            # every question with a reviewed manifest entry
    python3 tools/summa/render.py i 0-2      # only these

Only questions whose manifest status is "ai-reviewed" or "spot-checked" are published.
q.0 (the prologue) becomes prolog.md; q.N becomes qN.md (URL /summa/i/qN/).
The generated files are overwritten on every run: edit the translation JSON, not them.

Labels follow glossary §A (Keberatan N: / Sebaliknya, / Aku menjawab bahwa /
Jawaban atas Keberatan N:). Every paragraph that opens a unit gets an anchor:
#a3, #a3-ob1, #a3-sc, #a3-co, #a3-ad1. Scripture references become links to the
Catholic Bible on imankatolik.or.id (ADR 0001 §4). The Latin is not published.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ayat import REF, url_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "content/id/summa"
PUBLISHED = ("ai-reviewed", "spot-checked")
PARS_ID = {"i": "I", "i-ii": "I-II", "ii-ii": "II-II", "iii": "III"}
HEADER = "# Dibuat oleh tools/summa/render.py dari translations/summa/. Jangan disunting langsung."


def link_refs(text):
    return REF.sub(lambda m: f"[{m.group(0)}]({url_for(*m.groups())})", text)


def toml_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def unit(paras, anchor, label=None, bold_lead=None, notes=()):
    """Markdown for one unit: the label (or the bolded opening words) on the first paragraph,
    a block-attribute anchor after it, then any editorial notes for this unit."""
    out = []
    for i, p in enumerate(paras):
        p = link_refs(p)
        if i == 0:
            if label:
                p = f"**{label}** {p}"
            elif bold_lead and p.startswith(bold_lead):
                p = f"**{bold_lead}**{p[len(bold_lead):]}"
            out.append(f"{p}\n{{#{anchor}}}")
        else:
            out.append(p)
    for n in notes:
        text = re.sub(r"^Catatan redaksi:\s*", "", n["text"])
        out.append(f"> **Catatan redaksi:** {link_refs(text)}\n{{.catatan-redaksi}}")
    return out


def render(pars, q, tr, status):
    notes = {}
    for n in tr.get("editorial_notes", []):
        notes.setdefault(n["at"], []).append(n)
    ref = f"STh {PARS_ID[pars]}, prolog" if q == 0 else f"STh {PARS_ID[pars]}, q. {q}"
    fm = [
        "+++",
        HEADER,
        f"title = {toml_str(tr['title'])}",
        f"linkTitle = {toml_str('Prolog' if q == 0 else f'Pertanyaan {q}: ' + tr['title'])}",
        f"weight = {q + 1}",  # Hugo sorts weight 0 last, so the prologue (q.0) gets 1
        f"summa_ref = {toml_str(ref)}",
        f"summa_status = {toml_str(status)}",
        f"glossary_version = {toml_str(tr.get('glossary_version', ''))}",
        f"toc = {'true' if tr['articles'] else 'false'}",
        "+++",
    ]
    body = [p for p in (link_refs(x) for x in tr["prooemium"])]
    body += [p for n in notes.get("prooemium", []) for p in unit([], "", notes=[n])]
    for a in tr["articles"]:
        n_a = a["a"]
        body.append(f"## Artikel {n_a}: {a['title']} {{#a{n_a}}}")
        for i, o in enumerate(a["objections"]):
            body += unit(o, f"a{n_a}-ob{i + 1}", label=f"Keberatan {i + 1}:",
                         notes=notes.get(f"a{n_a}.objections[{i}]", ()))
        body += unit(a["sed_contra"], f"a{n_a}-sc", bold_lead="Sebaliknya,",
                     notes=notes.get(f"a{n_a}.sed_contra", ()))
        body += unit(a["respondeo"], f"a{n_a}-co", bold_lead="Aku menjawab bahwa",
                     notes=notes.get(f"a{n_a}.respondeo", ()))
        for r in a["replies"]:
            nums = " dan ".join(map(str, r["n"]))
            key = f"a{n_a}.replies[{','.join(map(str, r['n']))}]"
            body += unit(r["paras"], f"a{n_a}-ad{r['n'][0]}", label=f"Jawaban atas Keberatan {nums}:",
                         notes=notes.get(key, ()))
    name = "prolog.md" if q == 0 else f"q{q}.md"
    path = OUT / pars / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(fm) + "\n\n" + "\n\n".join(body) + "\n", encoding="utf-8")
    return path


def main():
    manifest = json.loads((ROOT / "translations/summa/manifest.json").read_text())
    want = None
    if len(sys.argv) == 3:
        lo, _, hi = sys.argv[2].partition("-")
        want = (sys.argv[1], set(range(int(lo), int(hi or lo) + 1)))
    for key, entry in sorted(manifest.items()):
        pars, qname = key.split("/")
        q = int(qname[1:])
        if want and (pars != want[0] or q not in want[1]):
            continue
        if entry["status"] not in PUBLISHED:
            print(f"skip {key}: status {entry['status']}")
            continue
        tr = json.loads((ROOT / f"translations/summa/{key}.json").read_text())
        if tr["source_sha256"] != entry["source_sha256"]:
            print(f"skip {key}: translation changed since it was reviewed")
            continue
        print(render(pars, q, tr, entry["status"]).relative_to(ROOT))


if __name__ == "__main__":
    main()
