#!/usr/bin/env python3
"""Check the Scripture references in a Summa translation, and give each one a link to
the Catholic Indonesian Bible (TB with the Deuterocanonical books) on imankatolik.or.id.

    python3 tools/summa/ayat.py i 1            # writes translations/summa/i/q001.ayat.json
    python3 tools/summa/ayat.py --ref "Sir 3:21"

Policy (ADR 0001 §4): quotations are translated from Thomas's text and never pasted
from the TB. The TB text fetched here is only for **checking** that a reference points
at the verse Thomas quotes. It is not published; the site links to it instead.
Responses are cached in sources/summa/raw/ayat/ (gitignored).
"""

import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "sources/summa/raw/ayat"
BASE = "https://www.imankatolik.or.id/alkitab.php"

# TB abbreviations; imankatolik's book code is the same, lower-cased.
BOOKS = ("Kej Kel Im Bil Ul Yos Hak Rut 1Sam 2Sam 1Raj 2Raj 1Taw 2Taw Ezr Neh Tob Ydt Est Ayb "
         "Mzm Ams Pkh Kid Keb Sir Yes Yer Rat Bar Yeh Dan Hos Yl Am Ob Yun Mi Nah Hab Zef Hag Za "
         "Mal 1Mak 2Mak Mat Mrk Luk Yoh Kis Rm 1Kor 2Kor Gal Ef Flp Kol 1Tes 2Tes 1Tim 2Tim Tit "
         "Flm Ibr Yak 1Ptr 2Ptr 1Yoh 2Yoh 3Yoh Yud Why").split()

REF = re.compile(r"(?<![\w-])(" + "|".join(sorted(BOOKS, key=len, reverse=True))
                 + r") (\d+)(?::(\d+)(?:[-–](\d+))?)?(?![\w:])")


def url_for(book, chapter, v1=None, v2=None):
    q = {"k": book.lower(), "b": chapter}
    if v1:
        q.update(a1=v1, a2=v2 or v1)
    return BASE + "?" + urllib.parse.urlencode(q)


def lookup(book, chapter, v1=None, v2=None):
    url = url_for(book, chapter, v1, v2)
    path = CACHE / f"{book}_{chapter}_{v1 or ''}_{v2 or ''}.json"
    if path.exists():
        return json.loads(path.read_text())
    time.sleep(0.5)  # be polite
    page = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                                  timeout=30).read().decode("utf-8", "replace")
    rows = re.findall(r'<b>([\w ]+?)&nbsp;(\d+):(\d+)</b></td><td[^>]*>(.*?)</td>', page, re.S)
    verses = [(int(v), re.sub(r"\(\d+-\d+\)\s*", "", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip())
              for b, c, v, t in rows if b.lower() == book.lower() and c == str(chapter)]
    result = {"status": "ok" if verses else "tidak-ditemukan", "url": url,
              "text": " ".join(f"[{v}] {t}" for v, t in verses) if v1 else None}
    if not v1:  # chapter-only reference: just confirm the chapter exists
        result["text"] = f"(pasal {chapter} ada)" if verses else None
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False))
    return result


def refs_in(obj, at=""):
    if isinstance(obj, str):
        for m in REF.finditer(obj):
            yield at, m
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from refs_in(v, f"{at}[{i}]")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k != "translator_notes":
                yield from refs_in(v, f"{at}.{k}" if at else k)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--ref":
        m = REF.search(sys.argv[2])
        if not m:
            sys.exit(f"unrecognised reference: {sys.argv[2]}")
        print(json.dumps(lookup(*m.groups()), ensure_ascii=False, indent=2))
        return
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pars, q = sys.argv[1], int(sys.argv[2])
    tr = json.loads((ROOT / f"translations/summa/{pars}/q{q:03d}.json").read_text())
    out, seen = [], {}
    for at, m in refs_in(tr):
        k = m.groups()
        if k not in seen:
            seen[k] = lookup(*k)
        out.append({"at": at, "ref": m.group(0), **seen[k]})
    path = ROOT / f"translations/summa/{pars}/q{q:03d}.ayat.json"
    path.write_text(json.dumps({"source": "Alkitab (TB + Deuterokanonika) via imankatolik.or.id; "
                                          "for checking and linking only, not for quoting",
                                "refs": out}, ensure_ascii=False, indent=2) + "\n")
    bad = [r for r in out if r["status"] != "ok"]
    print(f"{path.relative_to(ROOT)}: {len(out)} references, {len(bad)} not found")
    for r in bad:
        print(f"    {r['at']}: {r['ref']}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
