# Reviewer Workflow

Only a small reviewer/curator group does this — not every submitter, and not
every field needs to be filled in.

## Statuses

```
new           -> just synced from GitHub, untouched
needs_review  -> a reviewer has looked but not finished mapping
mapped        -> theme/WG/taxonomy links are set
wg_input      -> handed to a working group as input
parked        -> valid but not actionable right now
closed        -> done, or the underlying GitHub issue was closed as invalid
```

Set with `review_use_case.py --issue N --status <status>`.

## What to check, in order

For each use case in the queue (`review_use_case.py --list-unreviewed`):

1. Is it valid and relevant to FG-TIDA's scope?
2. Which theme or working group does it support?
   `--add-theme "Delegation"` / `--add-wg wg1-ra-aai`
3. What standards gap does it reveal, if any?
   `--add-standards-gap "..."`
4. Does it introduce or reinforce a taxonomy term?
   `--add-taxonomy-term "mandate"`
5. Is it related to an existing use case?
   `--related-to <other issue number>`

Don't feel obliged to fill in every field — map what's clear, leave the rest
for a later pass or another reviewer.

## Commands

```bash
# queues
python scripts/review_use_case.py --list-unreviewed
python scripts/review_use_case.py --list-unmapped

# full pass on one issue
python scripts/review_use_case.py --issue 12 \
    --status mapped \
    --summary "Cross-border delegation of a payment mandate" \
    --reviewer alice \
    --add-theme Delegation --add-theme "Discovery and Cross-Border Trust" \
    --add-wg wg1-ra-aai \
    --add-taxonomy-term mandate \
    --add-standards-gap "No standard for cross-border mandate revocation propagation" \
    --related-to 7
```

`--add-theme` and `--add-taxonomy-term` create the row if it doesn't already
exist — new themes/terms are expected to emerge from real use cases.
`--add-wg` requires the working group to already exist in `working_groups`
(add it to `curation/reference-data.yaml` when FG-TIDA forms a new one, then
run `scripts/load_reference_data.py`).

## After running the CLI

Each update also rewrites `curation/mappings.yaml` — that file, not the
local sqlite db, is what other reviewers and the dashboard's daily rebuild
actually see. Commit and push it (or open a small PR) after a review pass:

```bash
git add curation/mappings.yaml
git commit -m "Review issue #12"
git push
```

The dashboard (`docs/dashboard.md`) picks up committed changes on its next
scheduled or manually triggered run.
