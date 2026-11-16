#!/usr/bin/env python3
"""Sync open+closed GitHub Issues labeled 'use-case' into the register.

Only the raw columns on use_cases (title/body/labels/state/updated_at/...)
are written. Reviewer-curated columns (review_status, summary, notes,
priority, reviewer, reviewed_at) are set to their defaults on first insert
only, and are never touched on subsequent syncs.

Usage: python scripts/sync_github_issues.py
Requires GITHUB_TOKEN in the environment or use-case-register/.env.
"""

import os
import sqlite3
import sys

import requests

from _env import db_path, load_env

API_ROOT = "https://api.github.com"
USE_CASE_LABEL = "use-case"


def fetch_issues(repo, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    issues = []
    page = 1
    while True:
        resp = requests.get(
            f"{API_ROOT}/repos/{repo}/issues",
            headers=headers,
            params={"state": "all", "per_page": 100, "page": page},
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        issues.extend(batch)
        page += 1
    return issues


def is_use_case_issue(issue):
    if "pull_request" in issue:
        return False
    labels = [label["name"] for label in issue.get("labels", [])]
    return USE_CASE_LABEL in labels


def upsert(conn, issue):
    labels = ",".join(label["name"] for label in issue.get("labels", []))
    author = (issue.get("user") or {}).get("login")

    conn.execute(
        """
        INSERT INTO use_cases (
            github_issue_number, github_issue_url, title, body, labels,
            state, author, created_at, updated_at, review_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
        ON CONFLICT(github_issue_number) DO UPDATE SET
            github_issue_url = excluded.github_issue_url,
            title            = excluded.title,
            body             = excluded.body,
            labels           = excluded.labels,
            state            = excluded.state,
            author           = excluded.author,
            updated_at       = excluded.updated_at
        """,
        (
            issue["number"],
            issue["html_url"],
            issue["title"],
            issue.get("body"),
            labels,
            issue["state"],
            author,
            issue["created_at"],
            issue["updated_at"],
        ),
    )


def main():
    load_env()
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO", "fg-tida-wg0/use-cases")
    if not token:
        print("FATAL: GITHUB_TOKEN not set (see examples/.env.example)", file=sys.stderr)
        return 1

    issues = [i for i in fetch_issues(repo, token) if is_use_case_issue(i)]

    conn = sqlite3.connect(db_path())
    try:
        for issue in issues:
            upsert(conn, issue)
        conn.commit()
    finally:
        conn.close()

    print(f"synced {len(issues)} use-case issue(s) from {repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
