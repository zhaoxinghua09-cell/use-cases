"""Shared helpers for reading/writing curated use-case state.

Used by review_use_case.py (writes curation/mappings.yaml as a side effect
of a reviewer's CLI update) and load_curation.py (reads it back to rebuild
the sqlite cache, e.g. in CI). Keeping the get-or-create/link logic here
means neither script re-implements it.
"""

from pathlib import Path

import yaml

REGISTER_ROOT = Path(__file__).resolve().parent.parent
MAPPINGS_PATH = REGISTER_ROOT / "curation" / "mappings.yaml"

CURATED_FIELDS = [
    "review_status", "summary", "review_notes", "priority",
    "reviewer", "reviewed_at",
]
LINK_FIELDS = [
    "themes", "working_groups", "taxonomy_terms", "standards_gaps",
    "related_use_cases",
]


def load_mappings():
    if not MAPPINGS_PATH.exists():
        return {}
    return yaml.safe_load(MAPPINGS_PATH.read_text()) or {}


def save_mappings(mappings):
    MAPPINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    MAPPINGS_PATH.write_text(
        yaml.safe_dump(mappings, sort_keys=True, allow_unicode=True)
    )


def get_or_create(conn, table, name_column, name):
    row = conn.execute(
        f"SELECT id FROM {table} WHERE {name_column} = ?", (name,)
    ).fetchone()
    if row:
        return row[0]
    cur = conn.execute(f"INSERT INTO {table} ({name_column}) VALUES (?)", (name,))
    return cur.lastrowid


def link(conn, link_table, use_case_col, other_col, use_case_id, other_id):
    conn.execute(
        f"""INSERT OR IGNORE INTO {link_table} ({use_case_col}, {other_col})
            VALUES (?, ?)""",
        (use_case_id, other_id),
    )


def get_use_case_id(conn, issue_number):
    row = conn.execute(
        "SELECT id FROM use_cases WHERE github_issue_number = ?", (issue_number,)
    ).fetchone()
    return row[0] if row else None


def apply_working_group_link(conn, use_case_id, wg_slug):
    """Returns False (and links nothing) if the slug is unknown."""
    row = conn.execute("SELECT id FROM working_groups WHERE slug = ?", (wg_slug,)).fetchone()
    if row is None:
        return False
    link(conn, "use_case_working_group_links", "use_case_id", "working_group_id", use_case_id, row[0])
    return True


def apply_theme_link(conn, use_case_id, theme_name):
    theme_id = get_or_create(conn, "themes", "name", theme_name)
    link(conn, "use_case_theme_links", "use_case_id", "theme_id", use_case_id, theme_id)


def apply_taxonomy_link(conn, use_case_id, term):
    term_id = get_or_create(conn, "taxonomy_terms", "term", term)
    link(conn, "use_case_taxonomy_links", "use_case_id", "taxonomy_term_id", use_case_id, term_id)


def apply_standards_gap_link(conn, use_case_id, title):
    gap_id = get_or_create(conn, "standards_gaps", "title", title)
    link(conn, "use_case_standards_gap_links", "use_case_id", "standards_gap_id", use_case_id, gap_id)


def apply_related_link(conn, use_case_id, other_issue_number):
    other_id = get_use_case_id(conn, other_issue_number)
    if other_id is None:
        return False
    a, b = sorted((use_case_id, other_id))
    conn.execute(
        "INSERT OR IGNORE INTO related_use_case_links (use_case_id_a, use_case_id_b) VALUES (?, ?)",
        (a, b),
    )
    return True


def apply_entry(conn, issue_number, entry):
    """Apply one curation/mappings.yaml entry onto the use_cases row + link
    tables for that issue. Silently skips link targets that don't (yet)
    exist (e.g. a related_use_case not synced), same as a partial CLI run."""
    use_case_id = get_use_case_id(conn, issue_number)
    if use_case_id is None:
        return False

    updates, params = [], []
    for field in CURATED_FIELDS:
        value = entry.get(field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    if updates:
        params.append(use_case_id)
        conn.execute(f"UPDATE use_cases SET {', '.join(updates)} WHERE id = ?", params)

    for theme in entry.get("themes") or []:
        apply_theme_link(conn, use_case_id, theme)
    for wg_slug in entry.get("working_groups") or []:
        apply_working_group_link(conn, use_case_id, wg_slug)
    for term in entry.get("taxonomy_terms") or []:
        apply_taxonomy_link(conn, use_case_id, term)
    for gap in entry.get("standards_gaps") or []:
        apply_standards_gap_link(conn, use_case_id, gap)
    for other_issue in entry.get("related_use_cases") or []:
        apply_related_link(conn, use_case_id, other_issue)

    return True
