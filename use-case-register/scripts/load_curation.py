#!/usr/bin/env python3
"""Apply curation/mappings.yaml onto the sqlite cache.

Run this after sync_github_issues.py (which populates the raw use_cases
rows this needs to attach curated data to) and before
generate_dashboard.py. This is what makes the sqlite db a rebuildable
cache: GitHub (raw issues) + this file (curated tagging) fully determine
its contents.

Usage: python scripts/load_curation.py
"""

import sqlite3
import sys

import _curation as curation
from _env import db_path


def main():
    mappings = curation.load_mappings()
    conn = sqlite3.connect(db_path())
    conn.execute("PRAGMA foreign_keys = ON")

    applied, skipped = 0, 0
    for issue_number_str, entry in mappings.items():
        if curation.apply_entry(conn, int(issue_number_str), entry):
            applied += 1
        else:
            skipped += 1

    conn.commit()
    conn.close()
    print(f"applied curation for {applied} use case(s), skipped {skipped} (not yet synced)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
