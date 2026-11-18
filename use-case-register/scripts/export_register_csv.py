#!/usr/bin/env python3
"""Export the register as a CSV for FG-TIDA meeting handouts.

Usage:
  python scripts/export_register_csv.py --out register-export.csv
  python scripts/export_register_csv.py --out mapped.csv --status mapped
"""

import argparse
import csv
import sqlite3
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
    uc.summary,
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
    "review_status", "priority", "reviewer", "summary",
    "themes", "working_groups", "taxonomy_terms", "standards_gaps",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="output CSV path")
    parser.add_argument("--status", help="filter by review_status")
    args = parser.parse_args()

    where = ""
    params = ()
    if args.status:
        where = "WHERE uc.review_status = ?"
        params = (args.status,)

    conn = sqlite3.connect(db_path())
    rows = conn.execute(QUERY.format(where=where), params).fetchall()
    conn.close()

    with open(args.out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)

    print(f"wrote {len(rows)} row(s) to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
