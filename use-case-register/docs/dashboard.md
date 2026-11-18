# Dashboard

A read-only, no-login, no-terminal view of the register, published as a
static page via GitHub Pages. It shows the same views the CLI's queue
commands and CSV export cover, in a browser:

- Summary cards: total use cases, unreviewed, mapped, themes with support,
  standards gaps identified.
- Tables: all use cases, unreviewed, unmapped, by theme, by working group,
  candidate taxonomy terms.
- Related use cases: explicitly linked by a reviewer, plus groupings by
  shared theme, taxonomy term, or standards gap. No embeddings or automated
  similarity — see `design.md` for why that's deliberate for now.

Nothing on this page can be edited from the browser. Tagging still happens
through `review_use_case.py` (see `reviewer-workflow.md`).

## How it stays up to date

`.github/workflows/update-dashboard.yml` runs once a day (and on-demand via
the "Run workflow" button on the Actions tab) and:

1. Builds a fresh SQLite cache (`init_db.py`).
2. Loads the Working Group/theme roster from `curation/reference-data.yaml`
   (`load_reference_data.py`).
3. Syncs raw issue data from GitHub (`sync_github_issues.py`).
4. Applies committed reviewer curation from `curation/mappings.yaml`
   (`load_curation.py`).
5. Renders the static page (`generate_dashboard.py`).
6. Publishes it to GitHub Pages.

The SQLite file itself is never committed — it's rebuilt from scratch every
run, from GitHub (raw issues) and `curation/mappings.yaml` (reviewer
tagging), which is the actual source of truth for curated data.

## One-time setup (repo admin)

GitHub Pages needs to be pointed at Actions once:
**Settings → Pages → Source → GitHub Actions**.

Until that's done, the workflow will fail at the `deploy-pages` step with a
"Pages not enabled" error — that's expected and not a bug in the workflow.
