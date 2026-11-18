#!/usr/bin/env python3
"""Reviewer CLI: curate a use case's status, notes, and mappings.

Stands in for a dashboard mapping UI until one exists. Every update is
applied to the local sqlite cache AND written back to
curation/mappings.yaml, which is the durable, git-committed source of
truth for curated data (see docs/design.md). Commit that file after
reviewing so CI's dashboard build picks up your changes.

See docs/reviewer-workflow.md for the review process this supports.

Examples:
  python scripts/review_use_case.py --list-unmapped
  python scripts/review_use_case.py --list-unreviewed
  python scripts/review_use_case.py --issue 12 --status mapped \\
      --summary "Cross-border delegation of a payment mandate" \\
      --reviewer alice --add-theme Delegation --add-wg wg1-ra-aai
  python scripts/review_use_case.py --issue 12 --add-taxonomy-term "mandate"
  python scripts/review_use_case.py --issue 12 --add-standards-gap \\
      "No standard for cross-border mandate revocation propagation"
  python scripts/review_use_case.py --issue 12 --related-to 7
"""

import argparse
import sqlite3
import sys

import _curation as curation
from _env import db_path

REVIEW_STATUSES = {"new", "needs_review", "mapped", "wg_input", "parked", "closed"}


def list_query(conn, description, sql):
    rows = conn.execute(sql).fetchall()
    print(f"{description} ({len(rows)}):")
    for issue_number, title in rows:
        print(f"  #{issue_number}\t{title}")


def read_current_entry(conn, issue_number):
    """Current curated state for an issue, in curation/mappings.yaml shape."""
    row = conn.execute(
        """SELECT id, review_status, summary, review_notes, priority, reviewer, reviewed_at
           FROM use_cases WHERE github_issue_number = ?""",
        (issue_number,),
    ).fetchone()
    use_case_id = row[0]
    entry = {
        "review_status": row[1],
        "summary": row[2],
        "review_notes": row[3],
        "priority": row[4],
        "reviewer": row[5],
        "reviewed_at": row[6],
    }

    entry["themes"] = [r[0] for r in conn.execute(
        """SELECT t.name FROM use_case_theme_links l JOIN themes t ON t.id = l.theme_id
           WHERE l.use_case_id = ? ORDER BY t.name""", (use_case_id,)).fetchall()]
    entry["working_groups"] = [r[0] for r in conn.execute(
        """SELECT w.slug FROM use_case_working_group_links l JOIN working_groups w ON w.id = l.working_group_id
           WHERE l.use_case_id = ? ORDER BY w.slug""", (use_case_id,)).fetchall()]
    entry["taxonomy_terms"] = [r[0] for r in conn.execute(
        """SELECT x.term FROM use_case_taxonomy_links l JOIN taxonomy_terms x ON x.id = l.taxonomy_term_id
           WHERE l.use_case_id = ? ORDER BY x.term""", (use_case_id,)).fetchall()]
    entry["standards_gaps"] = [r[0] for r in conn.execute(
        """SELECT g.title FROM use_case_standards_gap_links l JOIN standards_gaps g ON g.id = l.standards_gap_id
           WHERE l.use_case_id = ? ORDER BY g.title""", (use_case_id,)).fetchall()]
    entry["related_use_cases"] = [r[0] for r in conn.execute(
        """SELECT uc.github_issue_number FROM related_use_case_links l
           JOIN use_cases uc ON uc.id = CASE WHEN l.use_case_id_a = ? THEN l.use_case_id_b ELSE l.use_case_id_a END
           WHERE l.use_case_id_a = ? OR l.use_case_id_b = ?
           ORDER BY uc.github_issue_number""",
        (use_case_id, use_case_id, use_case_id)).fetchall()]

    return entry


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--issue", type=int, help="GitHub issue number to update")
    parser.add_argument("--status", choices=sorted(REVIEW_STATUSES))
    parser.add_argument("--summary")
    parser.add_argument("--notes")
    parser.add_argument("--priority")
    parser.add_argument("--reviewer")
    parser.add_argument("--add-theme", action="append", default=[], metavar="NAME")
    parser.add_argument("--add-wg", action="append", default=[], metavar="SLUG")
    parser.add_argument("--add-taxonomy-term", action="append", default=[], metavar="TERM")
    parser.add_argument("--add-standards-gap", action="append", default=[], metavar="TITLE")
    parser.add_argument("--related-to", type=int, metavar="ISSUE_NUMBER")
    parser.add_argument("--list-unmapped", action="store_true")
    parser.add_argument("--list-unreviewed", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(db_path())
    conn.execute("PRAGMA foreign_keys = ON")

    if args.list_unmapped:
        list_query(
            conn,
            "unmapped use cases",
            """
            SELECT uc.github_issue_number, uc.title FROM use_cases uc
            WHERE uc.id NOT IN (SELECT use_case_id FROM use_case_theme_links)
              AND uc.id NOT IN (SELECT use_case_id FROM use_case_working_group_links)
            ORDER BY uc.github_issue_number
            """,
        )
    if args.list_unreviewed:
        list_query(
            conn,
            "unreviewed use cases",
            """
            SELECT github_issue_number, title FROM use_cases
            WHERE review_status = 'new'
            ORDER BY github_issue_number
            """,
        )
    if args.list_unmapped or args.list_unreviewed:
        conn.close()
        return 0

    if args.issue is None:
        parser.error("--issue is required unless using --list-unmapped/--list-unreviewed")

    use_case_id = curation.get_use_case_id(conn, args.issue)
    if use_case_id is None:
        sys.exit(f"no use case found for issue #{args.issue}")

    updates, params = [], []
    for field, value in (
        ("review_status", args.status),
        ("summary", args.summary),
        ("review_notes", args.notes),
        ("priority", args.priority),
        ("reviewer", args.reviewer),
    ):
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    if updates:
        if args.reviewer or args.status:
            updates.append("reviewed_at = datetime('now')")
        params.append(use_case_id)
        conn.execute(f"UPDATE use_cases SET {', '.join(updates)} WHERE id = ?", params)

    for theme in args.add_theme:
        curation.apply_theme_link(conn, use_case_id, theme)

    for wg_slug in args.add_wg:
        if not curation.apply_working_group_link(conn, use_case_id, wg_slug):
            sys.exit(f"unknown working group slug '{wg_slug}' — add it to schema/002_seed_reference_data.sql first")

    for term in args.add_taxonomy_term:
        curation.apply_taxonomy_link(conn, use_case_id, term)

    for gap_title in args.add_standards_gap:
        curation.apply_standards_gap_link(conn, use_case_id, gap_title)

    if args.related_to is not None:
        if not curation.apply_related_link(conn, use_case_id, args.related_to):
            sys.exit(f"no use case found for issue #{args.related_to}")

    conn.commit()

    mappings = curation.load_mappings()
    mappings[str(args.issue)] = read_current_entry(conn, args.issue)
    curation.save_mappings(mappings)

    conn.close()
    print(f"updated issue #{args.issue} (curation/mappings.yaml written — remember to commit it)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
