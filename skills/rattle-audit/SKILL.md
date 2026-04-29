---
name: rattle-audit
description: Use this skill to audit a live Rattle tenant catalogue against the 6 structural checks (areas-without-groups, duplicate-group-names, offer-template-missing-configuration, duplicate-dynamic-wrappers, options-with-custom-keys, options-with-conflicting-area-overrides). Produces a prioritised findings list with related rule ids and minimum-fix recommendations. Read-only — handing fixes off to rattle-apply-config. Pair with rattle-api (REST mechanics) and rattle-configurator (rules).
license: MIT
---

# Rattle audit

Scan a live tenant catalogue for structural problems. Read-only — this skill never writes. Fixes are produced as recommendations and handed off to `rattle-apply-config`.

## When to use this skill

- Onboarding a new tenant and need a baseline of issues to fix.
- Periodic health-check before a release, demo, or customer-facing change.
- After a large bulk import where humans may have introduced duplicates or empty areas.
- Following up on a `rattle-suggest-config` apply run, to confirm the result is clean.

If the user wants to scan a *pricelist* (offline document) instead of a live tenant, use `rattle-pricelist-analysis` instead.

## Workflow

1. **Read the check runbook.** `skills/rattle-configurator/references/structural-checks.md` lists every check with its endpoints, predicate, severity, and minimum fix. Use it as the per-check spec.

2. **Resolve the tenant.**
   - Validate that `RATTLE_API_KEY_<TENANT>` is set in env. If not, abort with a clear message.
   - Read `memory/<tenant>/profile.md` (if it exists) to detect opt-in checks (notably `options-with-custom-keys` is opt-in via tenant memory).

3. **Run the checks deterministically.** Use:
   ```
   python skills/rattle-audit/scripts/audit_runner.py <tenant> [--checks <id1,id2,...>]
   ```
   Or replicate the loop in your own client per `references/audit-runner.md`. Each check:
   - Lists entities at the documented endpoint (paginated via `client-patterns.md` § 2).
   - Optionally fetches a per-entity sub-resource (e.g. `/areas/{id}/groups`).
   - Applies the `flag_when` predicate and emits one finding per hit.

4. **Prioritise findings.**
   - `error` (must fix to keep catalogue functional)
   - `warning` (should fix to keep catalogue maintainable)
   - `info` (only when the tenant explicitly opted in)

5. **Generate fix recommendations.** For each finding, copy the matching "Fix." section from `structural-checks.md` and adapt it to the specific entity. Cite the related rule id from `configuration-rules.md`. The output must be in the canonical findings shape (see "Output contract" below).

6. **Hand off to apply.** When the user is ready to fix, the findings can be transformed into `ensure_*` operations:
   - `areas-without-groups` → either an `ensure_group` to fill the area, or a delete recommendation (out of scope here; user must approve).
   - `duplicate-group-names` → a series of "merge into the canonical id" steps; cannot be auto-translated, must be user-confirmed.
   - `offer-template-missing-configuration` → an `ensure_attachment {structure_block, content_block_id: <dynamic_configuration_id>, is_required: true}` (custom op type — see `rattle-document-templates`).
   - The `rattle-suggest-config` skill can take the findings and produce a recommendation for the user to review.

7. **Persist (only on explicit user consent).** If the user asks, append a record to `memory/<tenant>/audit_history.jsonl` via:
   ```
   rattle <tenant> memory record-decision "<summary>"
   ```
   File shape: line-delimited JSON `{"timestamp": "<ISO 8601 UTC>", "text": "..."}`. Never write silently.

## Output contract

```json
{
  "tenant": "acme",
  "ran_at": "<ISO 8601 UTC>",
  "summary": {"errors": 0, "warnings": 0, "info": 0},
  "findings": [
    {
      "check_id": "areas-without-groups",
      "severity": "error",
      "entity_type": "area",
      "entity_id": 42,
      "entity_name": "Widget Pro — Description",
      "message": "Area has 0 groups",
      "related_rules": ["no-empty-areas"],
      "minimum_fix": "Add at least one group to this area, OR migrate the narrative to a document template (see narrative-in-documents-system) and delete the area."
    }
  ]
}
```

The shape is consumed by `agents/rattle-auditor.md`, the `/rattle-audit` command, and any non-Claude client that loads this skill. Keep it stable.

## Bundled scripts

- `scripts/audit_runner.py` — language-agnostic runner. Reads check specs from `skills/rattle-configurator/references/structural-checks.md` (so Markdown stays the source of truth), executes against a live tenant via the Rattle REST API, and emits the findings JSON above. Requires `RATTLE_API_KEY_<TENANT>` env var. Runs without any AI keys.

## Boundaries

- **Read-only.** No PATCH, POST, PUT, DELETE.
- **Never modify** `memory/<tenant>/*` — only read.
- **Do not skip** checks even if a previous run showed zero findings; the catalogue can have drifted.
- **Honour opt-in checks** — `options-with-custom-keys` runs only if the tenant profile contains `- **custom-keys**: never` (or equivalent opt-in marker). Skipping silently is the correct behaviour when no opt-in exists.

## Related skills

- `rattle-configurator` — the rules that the checks enforce, plus the run-book for each check.
- `rattle-api` — REST surface; `references/client-patterns.md` § 2 (list-all loop).
- `rattle-apply-config` — applies fixes derived from audit findings.
- `rattle-suggest-config` — converts findings into a richer remediation recommendation.
- `rattle-tenant-memory` — opt-in check configuration lives there.
