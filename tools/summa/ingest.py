#!/usr/bin/env python3
"""Fetch and align the Latin and English texts of the Summa Theologiae.

Latin:   la.wikisource (Leonine text, public domain)
English: Project Gutenberg (Fathers of the English Dominican Province, public domain)

Writes one JSON file per question to sources/summa/<pars>/qNNN.json, with every
structural unit (prooemium, objections, sed contra, respondeo, replies) holding
both "la" and "en". Raw downloads are cached in sources/summa/raw/ (gitignored).

Usage:
    python3 tools/summa/ingest.py i 1-2        # Prima Pars, questions 1 to 2
    python3 tools/summa/ingest.py i-ii 1-5

Exits non-zero if any question fails the Latin/English alignment check.
"""

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "sources" / "summa"
RAW = OUT / "raw"

PARTES = {
    "i": {"en_id": "I", "la_title": "Prima pars", "gutenberg": 17611},
    "i-ii": {"en_id": "I-II", "la_title": "Prima secundae pars", "gutenberg": 17897},
    "ii-ii": {"en_id": "II-II", "la_title": "Secunda secundae pars", "gutenberg": 18755},
    "iii": {"en_id": "III", "la_title": "Tertia pars", "gutenberg": 19950},
    # "suppl": Latin source not yet chosen; English is on en.wikisource. See ADR 0001.
}

LA_ORDINALS = {
    "primum": 1, "secundum": 2, "tertium": 3, "quartum": 4, "quintum": 5,
    "sextum": 6, "septimum": 7, "octavum": 8, "nonum": 9, "decimum": 10,
    "undecimum": 11, "duodecimum": 12, "decimumtertium": 13, "decimumquartum": 14,
}

UA = "sayakatolik-summa-ingest/0.1 (https://sayakatolik.com)"


def roman(n):
    out = ""
    for v, s in [(100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
                 (5, "V"), (4, "IV"), (1, "I")]:
        while n >= v:
            out += s
            n -= v
    return out


def fetch(url, cache_name):
    path = RAW / cache_name
    if path.exists():
        return path.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    time.sleep(0.5)  # be polite to wikisource
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- Latin


def clean_wikitext(t):
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t, flags=re.S)  # templates
    t = re.sub(r"</?div[^>]*>", "", t)
    t = re.sub(r"\[\[[a-z]{2,3}:[^\]]*\]\]", "", t)  # interlanguage links
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = t.replace("'''", "").replace("''", "")
    return t


def paragraphs(block):
    return [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", block) if p.strip()]


def la_reply_numbers(p):
    m = re.match(r"Ad (\w+)(?: (?:et|ergo et) (\w+))?(?: et (\w+))?", p)
    if not m:
        return None
    nums = [LA_ORDINALS.get(w) for w in m.groups() if w]
    return nums if nums and all(nums) else None


# Corpus Thomisticum locators that prefix many wikisource paragraphs,
# e.g. "Iª q. 4 a. 2 arg. 1", "Iª-IIae q. 3 a. 1 s. c.", "IIIª q. 2 a. 3 ad 2".
LA_LOC = re.compile(r"^(?:\[\]\s*)?[IV]+ª(?:-[IV]+ae)?\s+q\.\s*\d+\s+(?:a\.\s*\d+\s+)?"
                    r"(arg\.\s*(\d+)|s\.\s*c\.|co\.|ad\s*(\d+)|pr\.)\s*")


def parse_la_article(paras):
    art = {"objections": [], "sed_contra": [], "respondeo": [], "replies": []}
    state = "obj"
    for p in paras:
        loc = LA_LOC.match(p)
        new_unit = False
        if loc:
            p = p[loc.end():]
            tag = loc.group(1)
            if tag.startswith("arg"):
                state, new_unit = "obj", True
            elif tag.startswith("s"):
                state = "sed"
            elif tag.startswith("co"):
                state = "resp"
            elif tag.startswith("ad"):
                state, new_unit = "reply", True
                n = la_reply_numbers(p) or [int(loc.group(3))]
        elif re.match(r"^(Sed contra|Contra|Sed in contrarium|In contrarium)\b", p):
            state = "sed"
        elif p.startswith("Respondeo"):
            state = "resp"
        elif state in ("resp", "reply") and la_reply_numbers(p):
            state, new_unit, n = "reply", True, la_reply_numbers(p)
        elif state == "obj":
            new_unit = bool(re.match(r"^(\d+ |Ad \w+ sic proceditur|Praeterea)", p))
        p = re.sub(r"^\d+ ", "", p)
        if state == "obj":
            if new_unit or not art["objections"]:
                art["objections"].append([p])
            else:
                art["objections"][-1].append(p)
        elif state == "sed":
            art["sed_contra"].append(p)
        elif state == "resp":
            art["respondeo"].append(p)
        elif new_unit:
            art["replies"].append({"n": n, "la": [p]})
        else:
            art["replies"][-1]["la"].append(p)
    return art


def from_roman(r):
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    return sum(-vals[c] if vals[c] < vals.get(n, 0) else vals[c] for c, n in zip(r, r[1:] + " "))


def la_paragraphs(block):
    """Paragraphs, with a locator standing alone on its line joined to the text after it."""
    out = []
    for p in paragraphs(block):
        if out and LA_LOC.fullmatch(out[-1] + " "):
            out[-1] = out[-1] + " " + p
        else:
            out.append(p)
    return out


def parse_la_question(wikitext):
    t = clean_wikitext(wikitext)
    # every locator-tagged line is its own paragraph, even without a blank line between
    t = re.sub(r"\n(?=\s*(?:\[\]\s*)?[IV]+ª(?:-[IV]+ae)?\s+q\.)", "\n\n", t)
    parts = re.split(r"^={2,}\s*(.+?)\s*={2,}\s*$", t, flags=re.M)
    q = {"prooemium": [], "articles": {}}
    for head, body in zip(parts[1::2], parts[2::2]):
        paras = la_paragraphs(body)
        if head.lower().startswith("prooemium"):
            q["prooemium"] = [LA_LOC.sub("", p, count=1) for p in paras]
        else:
            m = re.match(r"Articulus ([\dIVXL]+)", head, re.I)
            if m:
                n = int(m.group(1)) if m.group(1).isdigit() else from_roman(m.group(1).upper())
                q["articles"][n] = parse_la_article(paras)
    if not q["articles"]:  # single-article question: no headings, prooemium folded into arg. 1
        paras = [p for p in la_paragraphs(t) if not re.match(r"^Quaestio \d+$", p, re.I)]
        q["articles"][1] = parse_la_article(paras)
    return q


# ---------------------------------------------------------------- English


def gutenberg_body(text):
    start = re.search(r"\*\*\* ?START OF.*?\*\*\*", text)
    end = re.search(r"\*\*\* ?END OF.*?\*\*\*", text)
    return text[start.end() if start else 0: end.start() if end else len(text)].replace("\r\n", "\n")


def en_reply_numbers(p):
    m = re.match(r"Reply Objs?\. ([\d, and]+?):", p)
    if not m:
        return None
    return [int(n) for n in re.findall(r"\d+", m.group(1))]


def parse_en_article(paras):
    art = {"title": paras[0] if paras else "", "objections": [], "sed_contra": [],
           "respondeo": [], "replies": []}
    state = "obj"
    for p in paras[1:]:
        if p.startswith("_On the contrary"):
            state = "sed"
        elif p.startswith("_I answer that"):
            state = "resp"
        elif en_reply_numbers(p):
            state = "reply"
            art["replies"].append({"n": en_reply_numbers(p), "en": [p]})
            continue
        if state == "obj":
            if re.match(r"^(Objection|Obj\.) \d+:", p) or not art["objections"]:
                art["objections"].append([p])
            else:
                art["objections"][-1].append(p)
        elif state == "sed":
            art["sed_contra"].append(p)
        elif state == "resp":
            art["respondeo"].append(p)
        else:
            art["replies"][-1]["en"].append(p)
    return art


EN_ORDINALS = {w: i + 1 for i, w in enumerate(
    "FIRST SECOND THIRD FOURTH FIFTH SIXTH SEVENTH EIGHTH NINTH TENTH ELEVENTH TWELFTH "
    "THIRTEENTH FOURTEENTH FIFTEENTH SIXTEENTH SEVENTEENTH EIGHTEENTH NINETEENTH TWENTIETH".split())}


def parse_en_part(text, en_id):
    """Return ({q: {"title", "prooemium", "articles": {a: {...}}}}, warnings) for a Gutenberg volume.

    The bracketed ids in the headings have typos ("[I. Q. 6, Art. 3]", duplicated or
    wrong numbers), and some "QUESTION n" lines are missing. So questions and articles
    are numbered by their order in the text; the ids are only cross-checked.
    """
    body = gutenberg_body(text).replace("\r", "")
    q1 = re.search(r"^QUESTION 1\s*$", body, re.M)
    if not q1:  # no heading (I-II): start at the title line above the first "(In N Articles)"
        q1 = list(re.finditer(r"^\S.*\n\(In .* Articles?\)\s*$", body[:body.index("FIRST ARTICLE")], re.M))[-1]
    body = re.sub(r"_{20,}", "_______________________", body[q1.start():])
    sep = "_______________________"
    marker = re.compile(r"^(?:QUESTION (?P<q>\d+)|(?P<ord>[A-Z]+) ARTICLE \[(?P<id>[^\]]*)\])\s*$", re.M)
    marks = list(marker.finditer(body))
    questions, warnings = {}, []
    qn = 0

    def open_question(n, head):
        head_paras = [p for p in paragraphs(head.split(sep)[0]) if not p.startswith("____")]
        title = head_paras[0] if head_paras else ""
        one = bool(re.search(r"\(in one article\)", head, re.I))
        rest = [p for p in head_paras[1:] if not re.match(r"^\(in .* articles?\)$", p, re.I)]
        q = {"title": title, "prooemium": rest, "articles": {}}
        if one:  # no article heading: the body is the single article, after the prooemium
            k = next((i for i, p in enumerate(rest) if re.match(r"^(Objection|Obj\.) \d+:", p)), len(rest))
            q["prooemium"] = rest[:k]
            q["articles"][1] = parse_en_article([title] + rest[k:])
        questions[n] = q

    for i, m in enumerate(marks):
        seg = body[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(body)]
        if m.group("q"):
            n = int(m.group("q"))
            if n == qn and not questions[qn]["articles"]:
                # a repeated "QUESTION n" line standing in for "FIRST ARTICLE"
                warnings.append(f"q.{qn} a.1: heading is 'QUESTION {n}'")
                questions[qn]["articles"][1] = parse_en_article(paragraphs(seg.split(sep)[0]))
                continue
            if n != qn + 1:
                warnings.append(f"QUESTION {n} heading after q.{qn}; using q.{qn + 1}")
            qn += 1
            open_question(qn, seg)
            continue
        an = EN_ORDINALS.get(m.group("ord"))
        if an == 1 and (qn == 0 or questions[qn]["articles"]):
            # FIRST ARTICLE with no QUESTION line before it: the head sits after the previous separator
            qn += 1
            prev = body[marks[i - 1].end() if i else 0: m.start()]
            open_question(qn, sep.join(prev.split(sep)[1:]) if i else prev)
            warnings.append(f"q.{qn}: missing QUESTION heading")
        ids = re.findall(r"\d+", m.group("id"))
        if len(ids) < 2 or (int(ids[0]), int(ids[1])) != (qn, an):
            warnings.append(f"q.{qn} a.{an}: heading says [{m.group('id')}]")
        questions[qn]["articles"][an] = parse_en_article(paragraphs(seg.split(sep)[0]))
    return questions, warnings


# ---------------------------------------------------------------- Merge


def merge(pars, qn, la, en):
    """Combine the texts. The Latin defines the translation units; the English is kept
    per article as a reference, since the two editions divide some articles differently.

    errors: Latin text gaps that must be fixed before translating.
    notes:  structural differences between the editions, passed on to the reviewer.
    """
    errors, notes = [], []
    if set(la["articles"]) != set(en["articles"]):
        errors.append(f"article sets differ: la={sorted(la['articles'])} en={sorted(en['articles'])}")
    if not la["prooemium"] and len(la["articles"]) > 1:
        errors.append("Latin prooemium missing")
    articles = []
    for a in sorted(set(la["articles"]) & set(en["articles"])):
        L, E = la["articles"][a], en["articles"][a]
        where = f"a.{a}"
        for key in ("objections", "sed_contra", "respondeo"):
            if E[key] and not L[key]:
                errors.append(f"{where}: Latin {key} missing (English has it)")
        if E["replies"] and not L["replies"]:
            errors.append(f"{where}: Latin replies missing (English has {len(E['replies'])})")
        if len(L["objections"]) != len(E["objections"]):
            notes.append(f"{where}: objections la={len(L['objections'])} en={len(E['objections'])}")
        la_r = [r["n"] for r in L["replies"]]
        en_r = [r["n"] for r in E["replies"]]
        if la_r != en_r:
            notes.append(f"{where}: replies la={la_r} en={en_r}")
        articles.append({"a": a, "title_en": E["title"], "la": L,
                         "en": {k: v for k, v in E.items() if k != "title"}})
    doc = {
        "pars": PARTES[pars]["en_id"],
        "q": qn,
        "title_en": en["title"],
        "prooemium": {"la": la["prooemium"], "en": en["prooemium"]},
        "articles": articles,
    }
    doc["source_sha256"] = sha(json.dumps(doc, ensure_ascii=False, sort_keys=True))
    doc["errors"], doc["notes"] = errors, notes
    return doc, errors, notes


def ingest_prologue(pars, cfg, en_text):
    """Write sources/summa/<pars>/q000.json: the part's prologue, with no articles."""
    title = f"Summa Theologiae/{cfg['la_title']}/Prooemium"
    url = "https://la.wikisource.org/w/index.php?" + urllib.parse.urlencode({"title": title, "action": "raw"})
    la_paras = [re.sub(r"^Summa theologiae, pr\.\s*", "", p) for p in la_paragraphs(clean_wikitext(
        fetch(url, f"la/{pars}/q000.wiki")))]
    body = gutenberg_body(en_text).replace("\r", "")
    heads = list(re.finditer(r"^PROLOGUE\s*$", body, re.M))
    if not heads or not la_paras:
        print(f"{pars} q.0: prologue not found", file=sys.stderr)
        return 1
    en_paras = paragraphs(re.split(r"_{20,}", body[heads[-1].end():])[0])
    doc = {"pars": cfg["en_id"], "q": 0, "title_en": "PROLOGUE",
           "prooemium": {"la": la_paras, "en": en_paras}, "articles": []}
    doc["source_sha256"] = sha(json.dumps(doc, ensure_ascii=False, sort_keys=True))
    doc["errors"], doc["notes"] = [], []
    doc["sources"] = {"la": url.replace("&action=raw", ""), "en": f"https://www.gutenberg.org/ebooks/{cfg['gutenberg']}"}
    out = OUT / pars / "q000.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{pars} q.0 (prologue): la {len(la_paras)} / en {len(en_paras)} paragraphs, OK")
    return 0


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in PARTES:
        sys.exit(__doc__)
    pars = sys.argv[1]
    lo, _, hi = sys.argv[2].partition("-")
    qs = range(int(lo), int(hi or lo) + 1)
    cfg = PARTES[pars]

    gid = cfg["gutenberg"]
    en_text = fetch(f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt", f"en/pg{gid}.txt")
    en_all, en_warnings = parse_en_part(en_text, cfg["en_id"])
    for w in en_warnings:
        print(f"note (English headings): {w}", file=sys.stderr)

    failed = 0
    for qn in qs:
        if qn == 0:  # q.0 = the part's prologue (for Part I, the prologue of the whole Summa)
            failed += ingest_prologue(pars, cfg, en_text)
            continue
        title = f"Summa Theologiae/{cfg['la_title']}/Quaestio {roman(qn)}"
        url = "https://la.wikisource.org/w/index.php?" + urllib.parse.urlencode(
            {"title": title, "action": "raw"})
        try:
            la = parse_la_question(fetch(url, f"la/{pars}/q{qn:03d}.wiki"))
        except urllib.error.HTTPError as e:
            print(f"{pars} q.{qn}: Latin page unavailable ({e.code}): {title}", file=sys.stderr)
            failed += 1
            continue
        if qn not in en_all:
            print(f"{pars} q.{qn}: not found in English text", file=sys.stderr)
            failed += 1
            continue
        doc, errors, notes = merge(pars, qn, la, en_all[qn])
        doc["sources"] = {"la": url.replace("&action=raw", ""),
                          "en": f"https://www.gutenberg.org/ebooks/{gid}"}
        out = OUT / pars / f"q{qn:03d}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        status = "ERROR" if errors else "OK"
        print(f"{pars} q.{qn}: {len(doc['articles'])} articles, {status}"
              + (f" ({len(notes)} notes)" if notes else ""))
        for e in errors:
            print(f"    {e}")
        failed += bool(errors)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
