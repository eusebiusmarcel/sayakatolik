#!/usr/bin/env python3
"""Side-by-side spot-check page: Indonesian translation next to the 1920 English,
with the Latin (the authority) in a collapsible row under each unit.

    python3 tools/summa/compare.py i 1-2 [out.html]

Default output: sources/summa/raw/compare-<pars>-<range>.html (gitignored).
"""

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CSS = """
:root { --bg:#fbfaf7; --fg:#1d1d1b; --muted:#6b6862; --line:#e4e0d8; --head:#f1ede4; --accent:#7a2e1d; }
@media (prefers-color-scheme: dark) { :root { --bg:#181715; --fg:#e8e5de; --muted:#9d998f; --line:#34312c; --head:#23211e; --accent:#e0a48f; } }
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
@media (max-width: 760px) { .unit { grid-template-columns:1fr; } details { grid-column:1; } .cols-head { display:none; } .en::before { content:"English"; display:block; font:600 .75rem system-ui; color:var(--muted); margin-top:.5rem; } }
"""


def paras(ps):
    return "".join(f"<p>{html.escape(p)}</p>" for p in ps)


def unit(label, idn, en, la):
    return (f'<div class="unit"><div class="label">{html.escape(label)}</div>'
            f'<div class="id">{paras(idn)}</div><div class="en">{paras(en)}</div>'
            f'<details><summary>Latin</summary>{paras(la)}</details></div>')


def question(pars, q):
    src = json.loads((ROOT / f"sources/summa/{pars}/q{q:03d}.json").read_text())
    tr = json.loads((ROOT / f"translations/summa/{pars}/q{q:03d}.json").read_text())
    out = [f'<h1 id="q{q}">STh {src["pars"]} q.{q} — {html.escape(tr["title"])}</h1>',
           f'<p class="sub">{html.escape(src["title_en"])}</p>',
           '<div class="unit cols-head"><div></div><div>Indonesia</div><div>English (1920)</div></div>',
           unit("Pengantar", tr["prooemium"], src["prooemium"]["en"], src["prooemium"]["la"])]
    src_arts = {a["a"]: a for a in src["articles"]}
    for ta in tr["articles"]:
        sa = src_arts[ta["a"]]
        L, E = sa["la"], sa["en"]
        out.append(f'<h2 id="q{q}a{ta["a"]}">Artikel {ta["a"]} — {html.escape(ta["title"])}'
                   f'<br><span class="sub">{html.escape(sa["title_en"])}</span></h2>')
        for i, o in enumerate(ta["objections"]):
            en = E["objections"][i] if i < len(E["objections"]) else ["(tidak ada padanan di edisi Inggris)"]
            out.append(unit(f"Keberatan {i + 1}", o, en, L["objections"][i]))
        # English objections beyond the Latin count (editions divide differently)
        for i in range(len(ta["objections"]), len(E["objections"])):
            out.append(unit(f"(EN obj. {i + 1})", [], E["objections"][i], []))
        out.append(unit("Sebaliknya", ta["sed_contra"], E["sed_contra"], L["sed_contra"]))
        out.append(unit("Aku menjawab", ta["respondeo"], E["respondeo"], L["respondeo"]))
        en_replies = {tuple(r["n"]): r["en"] for r in E["replies"]}
        for tr_r, la_r in zip(ta["replies"], L["replies"]):
            n = tuple(tr_r["n"])
            en = en_replies.pop(n, ["(tidak ada padanan terpisah di edisi Inggris)"])
            out.append(unit(f"Jawaban {', '.join(map(str, n))}", tr_r["paras"], en, la_r["la"]))
        for n, en in en_replies.items():
            out.append(unit(f"(EN reply {', '.join(map(str, n))})", [], en, []))
    notes = [n for n in tr.get("editorial_notes", [])]
    if notes:
        out.append('<div class="notes"><strong>Catatan redaksi</strong>'
                   + "".join(f"<p>[{html.escape(n['at'])}] {html.escape(n['text'])}</p>" for n in notes) + "</div>")
    return "\n".join(out)


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    pars = sys.argv[1]
    lo, _, hi = sys.argv[2].partition("-")
    qs = list(range(int(lo), int(hi or lo) + 1))
    out = Path(sys.argv[3]) if len(sys.argv) == 4 else ROOT / f"sources/summa/raw/compare-{pars}-{sys.argv[2]}.html"
    nav = "".join(f'<a href="#q{q}">q.{q}</a>' for q in qs)
    body = "\n".join(question(pars, q) for q in qs)
    out.write_text(f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Summa {pars.upper()} q.{sys.argv[2]} — cek terjemahan</title><style>{CSS}</style></head>
<body><main><p class="sub">Spot-check: Indonesia ↔ English (Fathers of the English Dominican Province, 1920).
Latin (Leonine, the authority) under each unit. <nav>{nav}</nav></p>{body}</main></body></html>""", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
