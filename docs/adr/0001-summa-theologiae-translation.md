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

**Revised 2026-09-28: the English is the base text, and the Latin is the authority
for meaning.** The pilot first translated from the Latin. An experiment on I q.1–2 then
compared that with a direct translation from the 1920 English:

- The owner found the English-based text **clearer Indonesian**.
- A Latin comparison found **84 meaning differences**. The Latin-based text was more
  faithful in 80 of them, and 86 of the 90 errors in the English-based text were
  inherited from the 1920 English itself. The worst example is I q.2 a.1 obj. 3, where
  *concedit veritatem esse* ("admits that truth exists") had become "admits that truth
  does **not** exist". Scripture references were also wrong (Yes 66:4 for 64:4).

**Decision (owner):**
- Wording, paragraphing and formulas follow the **English base text**.
- A Latin **meaning correction** fixes every place where the English departs from the
  Latin in meaning, and only those places.
- The Latin is never shown on the site, and no Latin terms are added in brackets unless
  the English has them.

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

1. **Translator** (Opus): English (1920) → Indonesian, following
   `docs/summa/glosarium.md`, `gaya-bahasa.md` and `pelajaran.md`. It does not read
   the Latin. (Before 2026-09-28: Sonnet, from the Latin.)
2. **Latin corrector** (Opus, fresh context; `summa-reviewer` in *koreksi* mode):
   compares the Indonesian with the Latin unit by unit. It fixes **only meaning**:
   content, logic, scope, modality, negation, a term's sense, and Scripture references
   and their TB numbering. It keeps the translator's wording and style wherever the
   meaning is right, and logs every change in `qNNN.review.json`. **Tested 2026-09-28:**
   a Sonnet-model reviewer, run on held-out pre-correction drafts (q.7, q.8) against the
   Opus corrector's real findings on the same drafts, found only ~54% of the
   major/critical issues (7 of 13) — below a 90% bar — so the corrector stays Opus.
3. **Language edit** (`summa-editor`): only when the corrector's changes read
   awkwardly, or when the owner flags style.
   Then **lint**: checks that the structure mirrors the English, the §A formulas are
   used, and no Latin glosses were added.
4. `translations/summa/manifest.json` records, for each question, its status
   (`draft` → `ai-reviewed` → `spot-checked`), the source hash and the glossary version.
   A glossary change flags exactly which questions need translating again.

**Human review:** after the pilot, the AI reviewer plus spot checks by the owner.
Nothing enters the glossary until the owner approves it.

### 4. Scripture

Thomas quotes the Vulgate, often from memory, and his argument sometimes depends on its
wording. For example, Yes 64:4 is cited for "what You have prepared for those who
**love** You", where the TB reads "…bagi orang yang **menanti-nantikan** dia", and the
argument in I q.13 a.11 rests on Kel 3:14 "He who **is**", where the TB reads "AKU
ADALAH AKU". Quoting the TB would break such arguments.

**Decision (owner, 2026-09-28): quotations are translated from Thomas's text, and never
from the TB.** Each quotation is rendered from the English base text, and the Latin
corrector makes sure its meaning matches Thomas's Latin. The TB wording is never
pasted in. (Before this, on 2026-09-28, the owner had briefly asked for TB wording. It
was set aside for the reasons above and because of LAI's non-commercial limit of
**1,000 verses** without written permission, which the Summa far exceeds; see the
[LAI policy](https://www.alkitab.or.id/tentang-kami/penggunaan-teks).)

**References and links.**
- References use TB book abbreviations and the **numbering of the Indonesian Catholic
  Bible** (TB with the Deuterocanonical books), with the Vulgate number in brackets
  where it differs, joined by a semicolon inside one bracket: *(Mzm 53:1; Vulg. 52:2)*,
  *(Sir 3:21; Vulg. 3:22)*. The Vulgate count follows the Clementine edition, which
  numbers a psalm's title as verse 1. Always check the verse text with `ayat.py`; never
  convert Psalm numbers by formula.
- A quotation found only in the Vulgate is marked "(Vulg.)", with a "bdk." reference
  to the nearest verse.
- On the site, each reference is a **link to the verse on
  [imankatolik.or.id](https://www.imankatolik.or.id/alkitab.php)**, which has the full
  Catholic canon, e.g. `alkitab.php?k=sir&b=3&a1=21&a2=21`. Readers see the familiar
  TB text in one click, and linking is not quoting.
- `tools/summa/ayat.py` checks every reference against that site and saves the verse
  text **for checking only**. The Latin corrector compares that text with Thomas's
  quotation and fixes the reference where it points at the wrong verse. (The check
  showed that "Mzm 53:2" had to be Mzm 53:1, and that the Catholic Sir 24:31 is a
  different verse from Thomas's Vulgate Sir 24:31.)

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
