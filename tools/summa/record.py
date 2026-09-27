#!/usr/bin/env python3
"""Record a reviewed Summa question (step 6 of the summa-translate skill).

    python3 tools/summa/record.py i 2 ai-reviewed [open_findings]

Updates translations/summa/manifest.json, appends the reviewer's new lessons to
docs/summa/pelajaran.md and its glossary proposals to docs/summa/glosarium-usulan.md.
Never touches glosarium.md.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from lint import glossary_version  # noqa: E402


def main():
    if len(sys.argv) not in (4, 5) or sys.argv[3] not in ("ai-reviewed", "needs-human", "spot-checked"):
        sys.exit(__doc__)
    pars, q, status = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    open_findings = int(sys.argv[4]) if len(sys.argv) == 5 else 0
    base = ROOT / f"translations/summa/{pars}/q{q:03d}"
    tr = json.loads(base.with_suffix(".json").read_text())
    review = json.loads(Path(f"{base}.review.json").read_text())
    ref = f"STh {tr['pars']} q.{q}"

    manifest_path = ROOT / "translations/summa/manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    counts = {}
    for f in review.get("findings", []):
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    manifest[f"{pars}/q{q:03d}"] = {
        "status": status,
        "source_sha256": tr["source_sha256"],
        "glossary_version": glossary_version(),
        "reviewed_at": date.today().isoformat(),
        "review_findings": counts,
        "open_findings": open_findings,
    }
    manifest_path.write_text(json.dumps(dict(sorted(manifest.items())), indent=2, ensure_ascii=False) + "\n")

    lessons_path = ROOT / "docs/summa/pelajaran.md"
    existing = lessons_path.read_text()
    edits_path = Path(f"{base}.edits.json")
    style = json.loads(edits_path.read_text()).get("style_lessons", []) if edits_path.exists() else []
    lessons = [re.sub(r"^\[asal:[^\]]*\]\s*", "", l.strip()) for l in review.get("lessons", []) + style]
    new = [l for l in lessons if l and l not in existing]
    if new:
        lessons_path.write_text(existing.rstrip("\n") + "\n" + "".join(f"- [asal: {ref}] {l}\n" for l in new))

    props_path = ROOT / "docs/summa/glosarium-usulan.md"
    props = props_path.read_text()
    rows = []
    for p in review.get("glossary_proposals", []):
        cell = lambda s: str(s or "").replace("|", "/").replace("\n", " ")
        if f"| {cell(p.get('latin'))} |" not in props:
            rows.append(f"| {cell(p.get('latin'))} | {cell(p.get('indonesia'))} | {cell(p.get('alasan'))} "
                        f"| {cell(p.get('rujukan'))} | {ref} |\n")
    if rows:
        props_path.write_text(props.rstrip("\n") + "\n" + "".join(rows))

    print(f"{ref}: {status}; {len(new)} lessons, {len(rows)} glossary proposals added")


if __name__ == "__main__":
    main()
