# ADR 0001 — Indonesian translation of the Summa Theologiae

- **Status:** Accepted (2026-09-27). One open point: the Latin source for I-II q.89–114, II-II, III and the Supplement (§1).
- **Deciders:** Eusebius Marcel

## Context

We want to publish St. Thomas Aquinas's *Summa Theologiae* in Bahasa Indonesia on
sayakatolik.com, for evangelization and catechesis (see `CONTEXT.md`). There is no
complete public-domain Indonesian translation. The work is large: about 512 questions,
roughly 2,600 articles and well over 1.5M words, plus the Supplement. So the
translation will be AI-assisted and done in stages.

## Decisions

### 1. Source texts (public domain only)

| Text | Source | Notes |
|---|---|---|
| **Latin (primary)**: Leonine edition (1888–1906) | la.wikisource `Summa Theologiae/<Pars>/Quaestio <N>` | Public domain. The Wikisource text comes from the Corpus Thomisticum transcription, whose *locators* (`Iª q. 4 a. 2 arg. 1`) we use as parsing anchors. We do **not** scrape corpusthomisticum.org itself; that site says "Iura omnia asservantur" (all rights reserved). |
| **English (reference)**: Fathers of the English Dominican Province, 2nd ed. 1920 / Benziger 1947 | Project Gutenberg #17611 (I), #17897 (I-II), #18755 (II-II), #19950 (III) | Public domain in the US and in Indonesia (life + 70; the main translator, L. Shapcote, died in 1947). The Gutenberg header and trademark text are removed. **Not** New Advent: it claims copyright on its digital edition. |
| **Supplement**: English | en.wikisource `Summa Theologiae/Supplement to the Third Part` | |
| **Supplement**: Latin | Not chosen yet. The candidate is Leonine vol. XII (1906) on archive.org (OCR). | Needed only when the Supplement is reached, which is last in the release order. |

**Latin coverage (checked 2026-09-27).** la.wikisource has **I q.1–119** and
**I-II q.1–88** only; all of these parse without errors. It has nothing for I-II
q.89–114, II-II, III or the Supplement. Its text is the Corpus Thomisticum
transcription: the CT locators prove it. **Open decision:** where to get the rest.
The options are (a) ask the Fundación Tomás de Aquino for permission to use the
Corpus Thomisticum text, which would also settle the question of provenance for the
Wikisource parts; or (b) OCR the public-domain Leonine or Marietti scans on
archive.org, which is much more work and error-prone. This does not block the release
order until II-II (step 4 of §6).

**The Latin is the authority.** The English is a cross-check and a reference. It is not
a second source to translate from. It is known to contain errors (for example, I q.1 a.1
cites "Isa. 66:4" where the Latin has *Isaiae LXIV*), and it divides some articles
differently from the Leonine text.

Other Indonesian translations are never used as input.

### 2. Ingestion

`tools/summa/ingest.py <pars> <range>` writes `sources/summa/<pars>/qNNN.json`. Each
file holds the Latin units (prooemium, objections, sed contra, respondeo, replies), the
English for each article, a `source_sha256`, and two lists:

- `errors`: Latin text gaps. These block translation until they are fixed.
- `notes`: places where the two editions divide an article differently. These are
  passed on to the reviewer.

Raw downloads are cached in `sources/summa/raw/`, which is gitignored.

### 3. Translation pipeline

A project skill `.claude/skills/summa-translate/` handles **one question per unit of
work**. The Summa's own structure decides how the text is divided; word counts are not
used. The skill borrows ideas from existing translation skills: the resumable hashed
manifest from translate-book, the Opus reviewer that checks for "no invented content"
from senshinji, and the human-approved glossary and decision log from
translation-workbench.

1. **Translator** (Sonnet): Latin → Indonesian, with the English as a reference,
   following `docs/summa/glosarium.md` and `docs/summa/pelajaran.md`.
2. **Reviewer** (Opus, fresh context): compares the Indonesian against the Latin
   paragraph by paragraph. It reports omissions, additions, glossary violations,
   doctrinal drift, and Scripture that wasn't handled correctly.
3. **Revision**, then **lint**: checks that the structure counts match the Latin and
   that glossary terms are used consistently.
4. `translations/summa/manifest.json` records, for each question, its status
   (`draft` → `ai-reviewed` → `spot-checked`), the source hash and the glossary version.
   A glossary change flags exactly which questions need translating again.

**Human review:** after the pilot, the AI reviewer plus spot checks by the owner.
Nothing enters the glossary until the owner approves it.

### 4. Scripture

Thomas quotes the Vulgate, often from memory, and his argument sometimes depends on
the Vulgate's wording. Rules:

- References follow TB book names and **TB (Hebrew) Psalm numbering**, with the
  Vulgate number in brackets: *Mzm 51:6 (Vulg. 50:8)*.
- Where Thomas's argument depends on the Vulgate's wording, translate his Latin
  literally and mark it "(Vulg.)".

**LAI quotation limit.** The [LAI text-use policy](https://www.alkitab.or.id/tentang-kami/penggunaan-teks)
allows non-commercial quotation of up to **1,000 verses** (and never a whole book)
without written permission. The Summa quotes far more than that. **Decision
(2026-09-27): every Scripture quotation is translated from Thomas's own Latin**, with
the TB reference given, and TB wording is never pasted in. This keeps us well within
LAI's terms and follows the text Thomas actually argued from. We will not ask LAI for
permission.

### 5. Doctrine and editorial notes

Translate Thomas faithfully, including positions the Church later settled differently
(for example III q.27 a.2 on the Immaculate Conception). Add a clearly marked
*Catatan redaksi* (editorial note) citing the KGK or magisterial document (here: KGK 491,
*Ineffabilis Deus*). The **Supplement** is labelled as compiled after Thomas's death
(traditionally by Reginald of Piperno), drawn from his Commentary on the Sentences.

### 6. Website

- Section `content/id/summa/`. URL `/summa/<pars>/q<N>/`, one page per question.
  Anchors `#a3` for an article and `#a3-ad1` for a reply. Citation style *STh I, q. 2, a. 3*.
- **The Latin is not shown on the site.** It stays in `sources/`.
- Every page shows its review status and an AI-assisted translation notice, and credits
  the source editions.
- Release order: I q.1–13 → I-II q.1–5 → I-II q.55–70 → II-II q.1–46 → III q.1–26 →
  III q.60–90 → the rest → Supplement.

## Consequences

- `CONTEXT.md`'s rule that Scripture uses the TB is relaxed for the Summa: Thomas's own
  (Vulgate) quotations are translated from his Latin. See §4.
- Latin text gaps found at ingestion must be fixed by hand from a Leonine scan and
  recorded, never guessed.
