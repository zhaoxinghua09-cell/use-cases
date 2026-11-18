#!/usr/bin/env python3
"""Create/refresh the use-case register SQLite database from schema/*.sql.

Usage: python scripts/init_db.py
"""

import sqlite3
import sys
from pathlib import Path

from _env import db_path

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"


def main():
    path = db_path()
    conn = sqlite3.connect(path)
    try:
        for sql_file in sorted(SCHEMA_DIR.glob("*.sql")):
            conn.executescript(sql_file.read_text())
            print(f"applied {sql_file.name}")
        conn.commit()
    finally:
        conn.close()
    print(f"database ready at {path}")


if __name__ == "__main__":
    sys.exit(main())
