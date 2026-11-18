#!/usr/bin/env python3
"""Export the register as RST for Sphinx-based publishing.

Mirrors export_register_csv.py's query/CLI shape. Unlike the CSV export,
this also carries the Markdown prose fields (body, summary, review_notes)
converted to RST via pandoc, since GitHub Issues (the source of truth for
submissions) only ever produce Markdown — there's no RST issue template.

Usage:
  python scripts/export_register_rst.py --out register-export.rst
  python scripts/export_register_rst.py --out mapped.rst --status mapped

Requires the `pandoc` binary on PATH.
"""

import argparse
import shutil
import sqlite3
import subprocess
import sys

from _env import db_path

QUERY = """
SELECT
    uc.github_issue_number,
    uc.title,
    uc.github_issue_url,
    uc.state,
    uc.review_status,
    uc.priority,
    uc.reviewer,
    uc.body,
    uc.summary,
    uc.review_notes,
    (SELECT GROUP_CONCAT(t.name, '; ') FROM use_case_theme_links l
        JOIN themes t ON t.id = l.theme_id WHERE l.use_case_id = uc.id) AS themes,
    (SELECT GROUP_CONCAT(w.slug, '; ') FROM use_case_working_group_links l
        JOIN working_groups w ON w.id = l.working_group_id WHERE l.use_case_id = uc.id) AS working_groups,
    (SELECT GROUP_CONCAT(x.term, '; ') FROM use_case_taxonomy_links l
        JOIN taxonomy_terms x ON x.id = l.taxonomy_term_id WHERE l.use_case_id = uc.id) AS taxonomy_terms,
    (SELECT GROUP_CONCAT(g.title, '; ') FROM use_case_standards_gap_links l
        JOIN standards_gaps g ON g.id = l.standards_gap_id WHERE l.use_case_id = uc.id) AS standards_gaps
FROM use_cases uc
{where}
ORDER BY uc.github_issue_number
"""

COLUMNS = [
    "github_issue_number", "title", "github_issue_url", "state",
    "review_status", "priority", "reviewer", "body", "summary",
    "review_notes", "themes", "working_groups", "taxonomy_terms",
    "standards_gaps",
]


def markdown_to_rst(text):
    """Convert one Markdown field to RST via pandoc. Empty input stays empty.

    Shifts any headings in the field down one level, since the use-case issue
    template is itself full of Markdown headings ("## 1. Identification", ...)
    and pandoc converts each field in isolation with no knowledge of the
    surrounding document's heading levels. Without this, headings from the
    submission body can collide with this script's own section headings
    (Summary / Review notes / Submission) once multiple use cases are
    concatenated into one file, which docutils/Sphinx treats as a build error.
    """
    if not text:
        return ""
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "rst", "--shift-heading-level-by=1"],
        input=text, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pandoc failed: {result.stderr}")
    return result.stdout.strip()


def rst_section(row):
    values = dict(zip(COLUMNS, row))
    title = f"#{values['github_issue_number']} — {values['title']}"

    lines = [title, "=" * len(title), ""]
    lines += [
        f":GitHub issue: {values['github_issue_url']}",
        f":State: {values['state']}",
        f":Review status: {values['review_status']}",
        f":Priority: {values['priority'] or ''}",
        f":Reviewer: {values['reviewer'] or ''}",
        f":Themes: {values['themes'] or ''}",
        f":Working groups: {values['working_groups'] or ''}",
        f":Taxonomy terms: {values['taxonomy_terms'] or ''}",
        f":Standards gaps: {values['standards_gaps'] or ''}",
        "",
    ]

    if values["summary"]:
        lines += ["Summary", "-------", "", markdown_to_rst(values["summary"]), ""]
    if values["review_notes"]:
        lines += ["Review notes", "------------", "", markdown_to_rst(values["review_notes"]), ""]
    if values["body"]:
        lines += ["Submission", "----------", "", markdown_to_rst(values["body"]), ""]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="output RST path")
    parser.add_argument("--status", help="filter by review_status")
    args = parser.parse_args()

    if shutil.which("pandoc") is None:
        print("error: pandoc is required (not found on PATH)", file=sys.stderr)
        return 1

    where = ""
    params = ()
    if args.status:
        where = "WHERE uc.review_status = ?"
        params = (args.status,)

    conn = sqlite3.connect(db_path())
    rows = conn.execute(QUERY.format(where=where), params).fetchall()
    conn.close()

    sections = [rst_section(row) for row in rows]

    with open(args.out, "w") as f:
        f.write("\n\n".join(sections))
        f.write("\n")

    print(f"wrote {len(rows)} use case(s) to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
