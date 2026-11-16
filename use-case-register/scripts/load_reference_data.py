#!/usr/bin/env python3
"""Load the known working groups and starter themes from
curation/reference-data.yaml into the sqlite cache.

Deliberately decoupled from schema/*.sql: this is living reference data
(the roster of chartered Working Groups, and a starter theme list), not
structure. It changes by editing and committing this file, never by
adding a new numbered schema migration -- see docs/design.md.

Run this after init_db.py and before review_use_case.py / load_curation.py.

Usage: python scripts/load_reference_data.py
"""
import sqlite3
import sys
from pathlib import Path

import yaml

from _env import db_path

REFERENCE_DATA_PATH = Path(__file__).resolve().parent.parent / "curation" / "reference-data.yaml"


def main():
    data = yaml.safe_load(REFERENCE_DATA_PATH.read_text()) or {}
    conn = sqlite3.connect(db_path())

    for wg in data.get("working_groups", []):
        conn.execute(
            "INSERT OR IGNORE INTO working_groups (slug, name, description) VALUES (?, ?, ?)",
            (wg["slug"], wg["name"], wg.get("description")),
        )

    for theme in data.get("themes", []):
        name = theme if isinstance(theme, str) else theme["name"]
        description = None if isinstance(theme, str) else theme.get("description")
        conn.execute(
            "INSERT OR IGNORE INTO themes (name, description) VALUES (?, ?)",
            (name, description),
        )

    conn.commit()
    conn.close()
    print(f"loaded reference data from {REFERENCE_DATA_PATH}")


if __name__ == "__main__":
    sys.exit(main())
