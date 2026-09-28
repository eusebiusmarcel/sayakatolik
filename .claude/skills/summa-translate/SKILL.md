---
name: summa-translate
description: Translate questions of Aquinas's Summa Theologiae into Indonesian for sayakatolik.com, from the 1920 English base text with a Latin meaning correction. Use when asked to translate, re-translate or review Summa questions, e.g. "/summa-translate i 1-2" or "terjemahkan STh I-II q.3".
---

# summa-translate

Translates the Summa **one question at a time**. The 1920 English Dominican translation
is the base text for wording and structure; the Latin is the authority for meaning. Policy lives in
`docs/adr/0001-summa-theologiae-translation.md`. Read it once per session.

**Arguments:** `<pars> <range>`, where pars is `i`, `i-ii`, `ii-ii` or `iii`, and the
range is `N` or `N-M`. Add `--force` to re-translate questions whose manifest entry is
already up to date.

## Files

| Path | Role |
|---|---|
| `sources/summa/<pars>/qNNN.json` | English base text and Latin, from `tools/summa/ingest.py` |
| `docs/summa/glosarium.md` | Terminology: binding. Its version is on line 3. |
| `docs/summa/pelajaran.md` | Lessons from past reviews: binding |
| `docs/summa/gaya-bahasa.md` | Indonesian style guide for general readers: binding |
| `translations/summa/<pars>/qNNN.edits.json` | Language editor's changes, for the delta review |
| `translations/summa/<pars>/qNNN.json` | Output: the Indonesian translation |
| `translations/summa/<pars>/qNNN.review.json` | Reviewer findings |
| `translations/summa/manifest.json` | Status per question |
| `docs/summa/glosarium-usulan.md` | Queue of proposed new terms, for the owner to approve |

## Per question

Run these steps in order for each question in the range. Several questions can run in
parallel, but a question's own steps never do.

1. **Preflight.**
   - If the source JSON is missing, run `python3 tools/summa/ingest.py <pars> <q>`.
   - If its `errors` list is non-empty, **stop on this question** and report the errors.
     Latin gaps are fixed by hand from a Leonine scan, never guessed.
   - Skip the question if the manifest shows the same `source_sha256` and glossary
     version with status `ai-reviewed` or later (unless `--force`).
2. **Translate.** Spawn the `summa-translator` agent (Opus) with the source path and
   the output path. It translates the English and writes
   `translations/summa/<pars>/qNNN.json`.
3. **Lint.** Run `python3 tools/summa/lint.py <pars> <q>`. On failure, send the lint
   output back to the translator agent (SendMessage) and lint again, at most twice.
3a. **Check references.** Run `python3 tools/summa/ayat.py <pars> <q>`. It writes
   `qNNN.ayat.json` with each Scripture reference's link and verse text (for checking
   only; never quoted).
4. **Correct against the Latin.** Spawn a **new** `summa-reviewer` in *koreksi mode*,
   and give it `qNNN.ayat.json` so it can check each reference against the verse text.
   It fixes every departure from the Latin in meaning directly in the translation,
   keeps the wording otherwise, and logs each fix in `qNNN.review.json`. Then run lint and
   `ayat.py` again, and send any failures back to the same reviewer.
   If it reports a `critical` finding it could not resolve, set the status to
   `needs-human`.
5. **Language edit (optional).** Only if the owner flagged the style, or the
   corrector's fixes read awkwardly: spawn `summa-editor`, then `summa-reviewer` in
   *delta mode* on its `qNNN.edits.json`, then lint.
6. **Record.** Run `python3 tools/summa/record.py <pars> <q> <status> [open_findings]`.
   It does the following:
   - Update the manifest entry:
     `{status: "ai-reviewed" | "needs-human", source_sha256, glossary_version, reviewed_at, open_findings}`.
   - Append the reviewer's `lessons` and the editor's `style_lessons` to
     `docs/summa/pelajaran.md`, skipping any lesson already there.
   - Append its `glossary_proposals` to `docs/summa/glosarium-usulan.md`.
   - **Never edit `glosarium.md` yourself**: only the owner approves terms.

7. **Render.** Run `python3 tools/summa/render.py <pars> <range>`. It writes the Hugo pages
   under `content/id/summa/<pars>/`, but only for questions whose manifest status is
   `ai-reviewed` or later. Never edit those pages by hand. Preview with
   `hugo server -D --renderToMemory` (see CLAUDE.md).

At the end, report a table: question, status, open findings, and new glossary
proposals. Ask the owner to spot-check questions tagged `needs-human` first.

## Output schema (`translations/summa/<pars>/qNNN.json`)

The **English** structure is mirrored exactly: the same number of articles, objections,
paragraphs per unit, and replies with the same `n`.

```json
{
  "pars": "I", "q": 2,
  "source_sha256": "<from source>", "glossary_version": "0.3",
  "title": "Adanya Allah",
  "prooemium": ["…"],
  "articles": [{
    "a": 3,
    "title": "Apakah Allah ada?",
    "objections": [["Tampaknya Allah tidak ada. …"], ["Selanjutnya, …"]],
    "sed_contra": ["Sebaliknya, …"],
    "respondeo": ["Aku menjawab bahwa …", "…"],
    "replies": [{"n": [1], "paras": ["(langsung isi jawabannya) …"]}]
  }],
  "editorial_notes": [{"at": "a3.respondeo", "text": "Catatan redaksi: …"}],
  "translator_notes": ["short notes for the reviewer, not published"]
}
```

The renderer (Phase 4) adds the labels **Keberatan N:** and **Jawaban atas Keberatan N:**,
so the paragraphs never contain them.
