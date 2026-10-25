# Mapping: SF-005 / SF-006 / SF-011 → UC-4 / UC-6 questions (#13)

From dakleyer's #13 correspondence (2026-09-29), the verifier-side challenge asks three questions. Each maps to an executable entry already in `silent-failure-catalog`.

| #13 challenge question | Our entry | Expected behaviour the entry demonstrates |
|---|---|---|
| Does missing required approval evidence affect the admission decision, or merely appear as a note beside an overall pass? | **SF-005** neutral-marker-not-counted | Shows a gate that reports "pass" while the required approval evidence is silently not counted — the legitimate-pass / missing-required-evidence shape. |
| Can participation/provenance checks expose a material contribution omitted from the declared record? | **SF-006** undeclared-not-checked | Shows a check that passes while an undeclared contribution is never inspected — the "undeclared not checked" gap. |
| Does the verifier still reject the deliberately invalid case after changes to rule/implementation/test? | **SF-011** always-green-oracle | The negative control: a deliberately invalid case that must be rejected; if it goes green, the verifier is an oracle that approves everything. |

## Proposed UC-4 selection (to table after today's call)

- **SF-011 = expected-rejection case** (the negative control every verifier must fail).
- **SF-005 = legitimate-pass case** (the case that should pass once required evidence is actually counted).
- **SF-006 = provenance-omission probe** (whether undeclared contributions are surfaced).

Each entry is runnable offline (stdlib only) and pinned via `manifest.sha256`; CI in `gates.yml` proves the checks actually execute. See `silent-failure-catalog` (tag `v0.1.1`, with `manifest.sha256` for integrity).
