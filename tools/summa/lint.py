#!/usr/bin/env python3
"""Check an Indonesian Summa translation against its Latin source.

    python3 tools/summa/lint.py i 2

Checks: the structure mirrors the Latin, no empty paragraphs, the fixed formulas are
used, labels are left to the renderer, the source hash and glossary version are current,
and no Latin paragraph was left untranslated. Exits non-zero on any failure.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def glossary_version():
    m = re.search(r"\*\*Versi:\*\*\s*([\d.]+)", (ROOT / "docs/summa/glosarium.md").read_text())
    return m.group(1) if m else None


def lint(pars, q):
    src = json.loads((ROOT / f"sources/summa/{pars}/q{q:03d}.json").read_text())
    path = ROOT / f"translations/summa/{pars}/q{q:03d}.json"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    tr = json.loads(path.read_text())
    errs = []

    if tr.get("source_sha256") != src["source_sha256"]:
        errs.append("source_sha256 differs from source (source changed, or not copied)")
    if tr.get("glossary_version") != glossary_version():
        errs.append(f"glossary_version {tr.get('glossary_version')} != {glossary_version()}")
    if not tr.get("title"):
        errs.append("question title missing")
    for i, n in enumerate(tr.get("editorial_notes", [])):  # published as "Catatan redaksi"
        if not (isinstance(n, dict) and n.get("at") and str(n.get("text", "")).startswith("Catatan redaksi")):
            errs.append(f"editorial_notes[{i}]: must be {{at, text: 'Catatan redaksi: …'}}; "
                        "internal notes belong in translator_notes")

    def same_shape(where, la, idn):
        if len(la) != len(idn):
            errs.append(f"{where}: {len(la)} Latin paragraphs, {len(idn)} Indonesian")
        for i, p in enumerate(idn):
            if not p.strip():
                errs.append(f"{where}[{i}]: empty")

    same_shape("prooemium", src["prooemium"]["la"], tr.get("prooemium", []))

    la_arts = {a["a"]: a["la"] for a in src["articles"]}
    tr_arts = {a["a"]: a for a in tr.get("articles", [])}
    if set(la_arts) != set(tr_arts):
        errs.append(f"articles: Latin {sorted(la_arts)}, Indonesian {sorted(tr_arts)}")

    for n in sorted(set(la_arts) & set(tr_arts)):
        L, T, w = la_arts[n], tr_arts[n], f"a{n}"
        if not T.get("title", "").endswith("?"):
            errs.append(f"{w}.title: should be a question ending in '?'")
        if len(L["objections"]) != len(T.get("objections", [])):
            errs.append(f"{w}: {len(L['objections'])} objections, {len(T.get('objections', []))} translated")
        for i, (lo, to) in enumerate(zip(L["objections"], T.get("objections", []))):
            same_shape(f"{w}.objections[{i}]", lo, to)
            if to and re.match(r"^\*{0,2}Keberatan", to[0]):
                errs.append(f"{w}.objections[{i}]: remove the label, the renderer adds it")
        same_shape(f"{w}.sed_contra", L["sed_contra"], T.get("sed_contra", []))
        same_shape(f"{w}.respondeo", L["respondeo"], T.get("respondeo", []))
        if T.get("sed_contra") and not T["sed_contra"][0].startswith("Sebaliknya"):
            errs.append(f"{w}.sed_contra: must start with 'Sebaliknya' (glossary §A)")
        if T.get("respondeo") and not T["respondeo"][0].startswith("Aku menjawab"):
            errs.append(f"{w}.respondeo: must start with 'Aku menjawab' (glossary §A)")
        la_r = [r["n"] for r in L["replies"]]
        tr_r = [r.get("n") for r in T.get("replies", [])]
        if la_r != tr_r:
            errs.append(f"{w}.replies: Latin {la_r}, Indonesian {tr_r}")
        for lr, trr in zip(L["replies"], T.get("replies", [])):
            same_shape(f"{w}.replies{lr['n']}", lr["la"], trr.get("paras", []))
            if trr.get("paras") and re.match(r"^\*{0,2}Jawaban atas", trr["paras"][0]):
                errs.append(f"{w}.replies{lr['n']}: remove the label, the renderer adds it")

    # Latin left untranslated: long runs of common Latin function words
    text = json.dumps(tr, ensure_ascii=False)
    for m in re.finditer(r"(?:\b(?:quod|est|enim|autem|sicut|dicendum|videtur)\b\W+\w+\W+){3,}", text):
        errs.append(f"possible untranslated Latin: …{m.group(0)[:60]}…")
    return errs


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    errs = lint(sys.argv[1], int(sys.argv[2]))
    for e in errs:
        print(e)
    print("lint OK" if not errs else f"lint FAILED ({len(errs)})")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
