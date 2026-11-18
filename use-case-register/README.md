# FG-TIDA Use-Case Register

> This is an initial implementation for review, not an agreed FG-TIDA
> process. It's here to make the idea concrete so it can be discussed and
> changed.

GitHub Issues in this repository stay the way use cases are submitted.
This register pulls those issues into a small local database so FG-TIDA can
see statistics, map use cases to themes and working groups, and track
recurring standards gaps over time — without asking submitters to classify
their own use case up front.

See `docs/design.md` for the full rationale and `docs/reviewer-workflow.md`
for how a reviewer curates a synced use case.

## Quickstart

```bash
cd use-case-register
pip install -r requirements.txt
cp examples/.env.example .env   # fill in GITHUB_TOKEN

python scripts/init_db.py              # creates register.db, seeds themes/WGs
python scripts/sync_github_issues.py   # pulls issues labeled "use-case"

python scripts/review_use_case.py --list-unreviewed
python scripts/review_use_case.py --issue 12 --status mapped \
    --summary "..." --reviewer alice --add-theme Delegation --add-wg wg1-ra-aai
# ^ also writes curation/mappings.yaml — commit that file so CI picks it up

python scripts/export_register_csv.py --out register-export.csv

python scripts/load_curation.py                              # rebuild-from-git check
python scripts/generate_dashboard.py --out dashboard/index.html
```

## What's here

```
schema/     SQLite DDL + seed data (themes, wg1-ra-aai)
scripts/    sync, reviewer CLI, curation loader, dashboard generator, CSV export
curation/   mappings.yaml — committed, human-reviewed reviewer tagging (source of truth)
docs/       design notes, reviewer workflow, dashboard
examples/   .env template and a sample export
```

`register.db` and `dashboard/` are gitignored — both are rebuilt from
GitHub + `curation/mappings.yaml` every time, by you locally or by the
scheduled GitHub Action. A live, no-terminal-needed dashboard is published
via GitHub Pages — see `docs/dashboard.md`. Reviewer tagging still goes
through the CLI above; the dashboard is read-only.
