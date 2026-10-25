# Verifier-side challenge reference

This folder is the executable reference material for the UC-4 / UC-6 verification
question that FG-TIDA/themes #13 and FG-TIDA/use-cases #22 raise.

It links to a publicly resolvable, independently checkable artefact —
[`silent-failure-catalog`](https://github.com/zhaoxinghua09-cell/silent-failure-catalog) —
which contains the executable entries SF-005, SF-006 and SF-011 named in the #13
correspondence (dakleyer, 2026-09-29).

## Why this is executable material rather than a description

- **Runnable offline from the record alone** — each entry ships a detection
  recipe that needs only the standard library and no network access.
- **Integrity recorded in the repository** — a manifest records the SHA-256 of
  every file, so you can check integrity without contacting the author.
- **Negative-control workflow** — CI records which checks actually ran, which is
  the same "reported success while checking nothing" failure shape that this
  material documents.
- **Reproducible** — clone the catalogue, run its self-test, and it fails loudly
  whenever a gate is broken.

## Entries referenced from #13

| Entry | Link |
|---|---|
| SF-005 neutral-marker-not-counted | [failures/SF-005-neutral-marker-not-counted.md](https://github.com/zhaoxinghua09-cell/silent-failure-catalog/blob/v0.1.1/failures/SF-005-neutral-marker-not-counted.md) |
| SF-006 undeclared-not-checked | [failures/SF-006-undeclared-not-checked.md](https://github.com/zhaoxinghua09-cell/silent-failure-catalog/blob/v0.1.1/failures/SF-006-undeclared-not-checked.md) |
| SF-011 always-green-oracle | [failures/SF-011-always-green-oracle.md](https://github.com/zhaoxinghua09-cell/silent-failure-catalog/blob/v0.1.1/failures/SF-011-always-green-oracle.md) |

See [UC4_UC6_MAPPING.md](./UC4_UC6_MAPPING.md) for how each entry maps to the
UC-4 / UC-6 questions.

This is material for discussion. It complements the negative conformance vectors
in FG-TIDA/themes #7 but does not replace them.
