-- FG-TIDA use-case register: initial schema (SQLite).
--
-- Portability note: this targets SQLite for zero-setup local/dev use.
-- A Postgres port would need: INTEGER PRIMARY KEY AUTOINCREMENT -> SERIAL/
-- BIGSERIAL, TEXT timestamps -> TIMESTAMPTZ, and the comma-joined `labels`
-- column -> TEXT[] or JSONB. See docs/design.md.

CREATE TABLE IF NOT EXISTS use_cases (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Raw fields synced from GitHub Issues. sync_github_issues.py owns
    -- these columns and overwrites them on every sync.
    github_issue_number INTEGER NOT NULL UNIQUE,
    github_issue_url    TEXT NOT NULL,
    title               TEXT NOT NULL,
    body                TEXT,
    labels              TEXT,       -- comma-separated
    state               TEXT,       -- GitHub issue state: open/closed
    author              TEXT,
    created_at          TEXT,
    updated_at          TEXT,

    -- Reviewer-curated fields. review_use_case.py owns these; sync never
    -- touches them after the row's first insert.
    review_status       TEXT NOT NULL DEFAULT 'new',
    summary             TEXT,
    review_notes        TEXT,
    priority            TEXT,
    reviewer            TEXT,
    reviewed_at         TEXT
);

CREATE TABLE IF NOT EXISTS themes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS working_groups (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT NOT NULL UNIQUE,   -- e.g. wg1-ra-aai
    name        TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS taxonomy_terms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    term        TEXT NOT NULL UNIQUE,
    definition  TEXT,
    category    TEXT,
    aliases     TEXT,
    status      TEXT NOT NULL DEFAULT 'candidate',
    notes       TEXT
);

CREATE TABLE IF NOT EXISTS standards_gaps (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS use_case_theme_links (
    use_case_id INTEGER NOT NULL REFERENCES use_cases(id),
    theme_id    INTEGER NOT NULL REFERENCES themes(id),
    PRIMARY KEY (use_case_id, theme_id)
);

CREATE TABLE IF NOT EXISTS use_case_working_group_links (
    use_case_id      INTEGER NOT NULL REFERENCES use_cases(id),
    working_group_id INTEGER NOT NULL REFERENCES working_groups(id),
    PRIMARY KEY (use_case_id, working_group_id)
);

CREATE TABLE IF NOT EXISTS use_case_taxonomy_links (
    use_case_id      INTEGER NOT NULL REFERENCES use_cases(id),
    taxonomy_term_id INTEGER NOT NULL REFERENCES taxonomy_terms(id),
    PRIMARY KEY (use_case_id, taxonomy_term_id)
);

CREATE TABLE IF NOT EXISTS use_case_standards_gap_links (
    use_case_id      INTEGER NOT NULL REFERENCES use_cases(id),
    standards_gap_id INTEGER NOT NULL REFERENCES standards_gaps(id),
    PRIMARY KEY (use_case_id, standards_gap_id)
);

CREATE TABLE IF NOT EXISTS theme_working_group_links (
    theme_id         INTEGER NOT NULL REFERENCES themes(id),
    working_group_id INTEGER NOT NULL REFERENCES working_groups(id),
    PRIMARY KEY (theme_id, working_group_id)
);

-- Symmetric self-link: (a, b) and (b, a) are the same relationship.
-- Reviewers add one row; queries should check both directions or the
-- helper view below.
CREATE TABLE IF NOT EXISTS related_use_case_links (
    use_case_id_a INTEGER NOT NULL REFERENCES use_cases(id),
    use_case_id_b INTEGER NOT NULL REFERENCES use_cases(id),
    PRIMARY KEY (use_case_id_a, use_case_id_b),
    CHECK (use_case_id_a <> use_case_id_b)
);
