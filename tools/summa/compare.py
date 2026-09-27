#!/usr/bin/env python3
"""Side-by-side spot-check page: Indonesian translation next to the 1920 English,
with the Latin (the authority) in a collapsible row under each unit.

    python3 tools/summa/compare.py i 1-2 [out.html]
    python3 tools/summa/compare.py i 1-2 --with-en-translation   # vs. qNNN.from-en.json + qNNN.diff.json

Default output: sources/summa/raw/compare-<pars>-<range>.html (gitignored).
"""

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CSS = """
:root { --bg:#fbfaf7; --fg:#1d1d1b; --muted:#6b6862; --line:#e4e0d8; --head:#f1ede4; --accent:#7a2e1d; --makna:#fbeceb; --maknanote:#f6d5d2; --gaya:#fbf3d9; }
@media (prefers-color-scheme: dark) { :root { --bg:#181715; --fg:#e8e5de; --muted:#9d998f; --line:#34312c; --head:#23211e; --accent:#e0a48f; --makna:#2e1f1d; --maknanote:#4a2622; --gaya:#3a3320; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.6 Georgia, "Times New Roman", serif; }
main { max-width:1200px; margin:0 auto; padding:24px 16px 64px; }
h1 { font-size:1.6rem; margin:2rem 0 .25rem; color:var(--accent); }
h2 { font-size:1.2rem; margin:2rem 0 .5rem; padding-top:1rem; border-top:2px solid var(--line); }
.sub { color:var(--muted); margin:0 0 1rem; }
nav a { color:var(--accent); margin-right:.75rem; }
.unit { display:grid; grid-template-columns:9rem 1fr 1fr; gap:0 1.25rem; border-bottom:1px solid var(--line); padding:.6rem 0; }
.label { font:600 .8rem/1.4 system-ui, sans-serif; color:var(--muted); text-transform:uppercase; letter-spacing:.03em; padding-top:.25rem; }
.cols-head { position:sticky; top:0; background:var(--head); font:600 .85rem system-ui, sans-serif; z-index:1; }
.unit p { margin:0 0 .6rem; }
details { grid-column:2 / 4; margin-top:.25rem; }
summary { cursor:pointer; font:.8rem system-ui, sans-serif; color:var(--muted); }
details p { font-style:italic; color:var(--muted); }
.notes { background:var(--head); padding:.75rem 1rem; border-radius:6px; font-size:.9rem; }
main:has(.three) { max-width:1600px; }
.unit.three { grid-template-columns:7rem 1fr 1fr 1fr; }
.unit.three .la p { font-style:italic; color:var(--muted); }
.unit.three details { grid-column:2 / 5; }
.unit.makna { background:var(--makna); }
.diff { grid-column:2 / 5; font:.85rem/1.45 system-ui, sans-serif; padding:.4rem .6rem; margin-top:.35rem; border-radius:4px; }
.diff.makna { background:var(--maknanote); border-left:3px solid #c0392b; }
.diff.gaya { background:var(--gaya); border-left:3px solid #c9a227; }
@media (max-width: 760px) { .unit, .unit.three { grid-template-columns:1fr; } details, .unit.three details, .diff { grid-column:1; } .cols-head { display:none; } .en::before { content:"English"; display:block; font:600 .75rem system-ui; color:var(--muted); margin-top:.5rem; } }
"""


INTRO2 = ("Spot-check: Indonesia ↔ English (Fathers of the English Dominican Province, 1920). "
          "Latin (Leonine, the authority) under each unit.")
INTRO3 = ("Eksperimen: terjemahan dari Latin ↔ terjemahan langsung dari Inggris (1920), dengan Latin sebagai "
          "otoritas. Bagian yang berlatar merah berbeda <strong>makna</strong>; kuning = beda gaya.")


def paras(ps):
    return "".join(f"<p>{html.escape(p)}</p>" for p in ps)


def unit(label, idn, en, la, from_en=None, diffs=()):
    """One row. Two-column mode: Indonesia | English, Latin collapsible.
    Three-column mode (from_en given): Indonesia from Latin | Indonesia from English | Latin,
    English collapsible, with the meaning differences from diff.json listed underneath."""
    makna = any(d.get("jenis") == "makna" for d in diffs)
    cls = "unit three" + (" makna" if makna else "") if from_en is not None else "unit"
    row = f'<div class="{cls}"><div class="label">{html.escape(label)}</div><div class="id">{paras(idn)}</div>'
    if from_en is None:
        row += f'<div class="en">{paras(en)}</div><details><summary>Latin</summary>{paras(la)}</details>'
    else:
        row += (f'<div class="fromen">{paras(from_en)}</div><div class="la">{paras(la)}</div>'
                f'<details><summary>English (1920)</summary>{paras(en)}</details>')
        for d in diffs:
            side = {"latin": "terjemahan dari Latin", "inggris": "terjemahan dari Inggris"}.get(
                d.get("mana_lebih_setia_pada_latin"), "keduanya setara")
            row += (f'<div class="diff {html.escape(d.get("jenis", ""))}"><strong>{html.escape(d.get("jenis", "").upper())}</strong> '
                    f'{html.escape(d.get("ringkasan", ""))} <em>Lebih setia: {side}.</em></div>')
    return row + "</div>"


def question(pars, q, with_en_translation=False):
    src = json.loads((ROOT / f"sources/summa/{pars}/q{q:03d}.json").read_text())
    tr = json.loads((ROOT / f"translations/summa/{pars}/q{q:03d}.json").read_text())
    fe, diffs = None, {}
    if with_en_translation:
        fe = json.loads((ROOT / f"translations/summa/{pars}/q{q:03d}.from-en.json").read_text())
        dpath = ROOT / f"translations/summa/{pars}/q{q:03d}.diff.json"
        for d in (json.loads(dpath.read_text()).get("diffs", []) if dpath.exists() else []):
            diffs.setdefault(d["at"], []).append(d)
    fe_arts = {a["a"]: a for a in fe["articles"]} if fe else {}

    def u(key, label, idn, en, la, fe_paras):
        return unit(label, idn, en, la, fe_paras if fe else None, diffs.get(key, ()))

    head = ('<div class="unit three cols-head"><div></div><div>Indonesia (dari Latin)</div>'
            '<div>Indonesia (dari Inggris)</div><div>Latin</div></div>' if fe else
            '<div class="unit cols-head"><div></div><div>Indonesia</div><div>English (1920)</div></div>')
    out = [f'<h1 id="q{q}">STh {src["pars"]} q.{q} — {html.escape(tr["title"])}</h1>',
           f'<p class="sub">{html.escape(src["title_en"])}'
           + (f' · dari Inggris: {html.escape(fe["title"])}' if fe else "") + "</p>", head,
           u("prooemium", "Pengantar", tr["prooemium"], src["prooemium"]["en"], src["prooemium"]["la"],
             fe["prooemium"] if fe else None)]
    src_arts = {a["a"]: a for a in src["articles"]}
    for ta in tr["articles"]:
        n_a = ta["a"]
        sa, fa = src_arts[n_a], fe_arts.get(n_a, {})
        L, E = sa["la"], sa["en"]
        out.append(f'<h2 id="q{q}a{n_a}">Artikel {n_a} — {html.escape(ta["title"])}'
                   f'<br><span class="sub">{html.escape(sa["title_en"])}'
                   + (f' · dari Inggris: {html.escape(fa.get("title", ""))}' if fe else "") + "</span></h2>")
        for d in diffs.get(f"a{n_a}.title", ()):
            out.append(unit("Judul", [], [], [], [], [d]))
        fobj = fa.get("objections", [])
        for i, o in enumerate(ta["objections"]):
            en = E["objections"][i] if i < len(E["objections"]) else ["(tidak ada padanan di edisi Inggris)"]
            out.append(u(f"a{n_a}.objections[{i}]", f"Keberatan {i + 1}", o, en,
                         L["objections"][i] if i < len(L["objections"]) else ["(tidak ada padanan terpisah di Latin)"],
                         fobj[i] if i < len(fobj) else []))
        for i in range(len(ta["objections"]), len(E["objections"])):
            out.append(u(f"a{n_a}.objections[{i}]", f"(EN obj. {i + 1})", [], E["objections"][i], [],
                         fobj[i] if i < len(fobj) else []))
        out.append(u(f"a{n_a}.sed_contra", "Sebaliknya", ta["sed_contra"], E["sed_contra"], L["sed_contra"],
                     fa.get("sed_contra", [])))
        out.append(u(f"a{n_a}.respondeo", "Aku menjawab", ta["respondeo"], E["respondeo"], L["respondeo"],
                     fa.get("respondeo", [])))
        en_replies = {tuple(r["n"]): r["en"] for r in E["replies"]}
        fe_replies = {tuple(r["n"]): r["paras"] for r in fa.get("replies", [])}
        la_by_n = {tuple(r["n"]): r["la"] for r in L["replies"]}
        for tr_r in ta["replies"]:
            n = tuple(tr_r["n"])
            la_r = {"la": la_by_n.get(n, ["(tidak ada padanan terpisah di Latin)"])}
            en = en_replies.pop(n, ["(tidak ada padanan terpisah di edisi Inggris)"])
            key = f"a{n_a}.replies[{','.join(map(str, n))}]"
            out.append(u(key, f"Jawaban atas Keberatan {', '.join(map(str, n))}", tr_r["paras"], en, la_r["la"],
                         fe_replies.pop(n, [])))
        for n, en in en_replies.items():
            out.append(u(f"a{n_a}.replies[{','.join(map(str, n))}]", f"(EN reply {', '.join(map(str, n))})",
                         [], en, [], fe_replies.pop(n, [])))
    notes = [n for n in tr.get("editorial_notes", [])]
    if notes:
        out.append('<div class="notes"><strong>Catatan redaksi</strong>'
                   + "".join(f"<p>[{html.escape(n['at'])}] {html.escape(n['text'])}</p>" for n in notes) + "</div>")
    return "\n".join(out)


def main():
    args = [a for a in sys.argv[1:] if a != "--with-en-translation"]
    three = len(args) != len(sys.argv) - 1
    if len(args) not in (2, 3):
        sys.exit(__doc__)
    sys.argv = [sys.argv[0]] + args
    pars = sys.argv[1]
    lo, _, hi = sys.argv[2].partition("-")
    qs = list(range(int(lo), int(hi or lo) + 1))
    out = Path(sys.argv[3]) if len(sys.argv) == 4 else ROOT / f"sources/summa/raw/compare-{pars}-{sys.argv[2]}{'-en' if three else ''}.html"
    nav = "".join(f'<a href="#q{q}">q.{q}</a>' for q in qs)
    body = "\n".join(question(pars, q, three) for q in qs)
    out.write_text(f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Summa {pars.upper()} q.{sys.argv[2]} — cek terjemahan</title><style>{CSS}</style></head>
<body><main><p class="sub">{INTRO3 if three else INTRO2} <nav>{nav}</nav></p>{body}</main></body></html>""", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
