---
name: summa-translate
description: Translate questions of Aquinas's Summa Theologiae from Latin into Indonesian for sayakatolik.com, with a fresh-context theological review. Use when asked to translate, re-translate or review Summa questions, e.g. "/summa-translate i 1-2" or "terjemahkan STh I-II q.3".
---

# summa-translate

Translates the Summa **one question at a time**: Latin is the source, the English
Dominican translation is a reference only. Policy lives in
`docs/adr/0001-summa-theologiae-translation.md`. Read it once per session.

**Arguments:** `<pars> <range>`, where pars is `i`, `i-ii`, `ii-ii` or `iii`, and the
range is `N` or `N-M`. Add `--force` to re-translate questions whose manifest entry is
already up to date.

## Files

| Path | Role |
|---|---|
| `sources/summa/<pars>/qNNN.json` | Latin units and English reference, from `tools/summa/ingest.py` |
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
2. **Translate.** Spawn the `summa-translator` agent with the source path and the
   output path. It writes `translations/summa/<pars>/qNNN.json`.
3. **Lint.** Run `python3 tools/summa/lint.py <pars> <q>`. On failure, send the lint
   output back to the translator agent (SendMessage) and lint again, at most twice.
4. **Review.** Spawn a **new** `summa-reviewer` agent. It never sees the translator's
   reasoning, only the files. It writes `qNNN.review.json`.
5. **Revise.** If the review has any `major` or `critical` findings, send them to the
   translator agent to fix, then lint again. If a `critical` finding is still open after
   one revision, set the status to `needs-human` and move on.
5a. **Edit the language.** Spawn a **new** `summa-editor` agent. It makes the
   Indonesian readable for general readers (`docs/summa/gaya-bahasa.md`), edits the
   translation in place, and writes `qNNN.edits.json`. It never writes `editorial_notes`. Send any `needs_translator`
   items to the translator agent.
5b. **Check the edits.** Spawn a **new** `summa-reviewer` in *delta mode*: it checks
   only the edits in `qNNN.edits.json` against the Latin, and appends any findings to
   `qNNN.review.json` with `"stage": "edit"`. It reverts or fixes an edit that changed
   the meaning. Lint again.
6. **Record.** Run `python3 tools/summa/record.py <pars> <q> <status> [open_findings]`.
   It does the following:
   - Update the manifest entry:
     `{status: "ai-reviewed" | "needs-human", source_sha256, glossary_version, reviewed_at, open_findings}`.
   - Append the reviewer's `lessons` and the editor's `style_lessons` to
     `docs/summa/pelajaran.md`, skipping any lesson already there.
   - Append its `glossary_proposals` to `docs/summa/glosarium-usulan.md`.
   - **Never edit `glosarium.md` yourself**: only the owner approves terms.

At the end, report a table: question, status, open findings, and new glossary
proposals. Ask the owner to spot-check questions tagged `needs-human` first.

## Output schema (`translations/summa/<pars>/qNNN.json`)

The Latin structure is mirrored exactly: the same number of articles, objections,
paragraphs per unit, and replies with the same `n`.

```json
{
  "pars": "I", "q": 2,
  "source_sha256": "<from source>", "glossary_version": "0.1",
  "title": "Apakah Allah Ada",
  "prooemium": ["…"],
  "articles": [{
    "a": 3,
    "title": "Apakah Allah ada?",
    "objections": [["Tampaknya Allah tidak ada. …"], ["Selanjutnya, …"]],
    "sed_contra": ["Sebaliknya, …"],
    "respondeo": ["Aku menjawab: harus dikatakan bahwa …", "…"],
    "replies": [{"n": [1], "paras": ["Harus dikatakan bahwa …"]}]
  }],
  "editorial_notes": [{"at": "a3.respondeo", "text": "Catatan redaksi: …"}],
  "translator_notes": ["short notes for the reviewer, not published"]
}
```

The renderer (Phase 4) adds the labels **Keberatan N.** and **Jawaban atas keberatan N.**,
so the paragraphs never contain them.
