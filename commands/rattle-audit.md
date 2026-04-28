---
description: Audit a live Rattle tenant against the 6 structural checks (areas-without-groups, duplicate-group-names, offer-template-missing-configuration, duplicate-dynamic-wrappers, options-with-custom-keys, options-with-conflicting-area-overrides). Produces a prioritised findings list with related rule ids and minimum-fix recommendations.
argument-hint: <tenant>
---

# /rattle-audit

Run the six structural checks against the named tenant (`$ARGUMENTS`) and report findings.

## Workflow

1. **Read the check runbook** — `skills/rattle-configurator/references/structural-checks.md` lists every check with its endpoints, predicate, severity, and minimum fix.

2. **Resolve the tenant** — Validate that `RATTLE_API_KEY_<TENANT>` is set in env and that `memory/<tenant>/profile.md` is readable. Note any check-specific opt-ins (notably `options-with-custom-keys` is opt-in via tenant memory).

3. **Delegate to `rattle-auditor`** — Spawn the `rattle-auditor` subagent with the tenant name. It performs the data fetch, applies each predicate, and returns the findings list. The subagent does **not** write anything.

4. **Triage findings** — When the subagent returns, summarise:
   - Errors first (must fix to keep the catalogue functional)
   - Warnings second (should fix to keep the catalogue maintainable)
   - Info last (only when the tenant opted in)

5. **Offer next steps** — For each finding, point at the matching fix recipe in `structural-checks.md`. If the user wants to apply fixes, hand off to `/rattle-suggest-config` (for restructure work) or directly to the `rattle-config-builder` agent (for targeted writes).

6. **Persist (only on explicit user consent)** — If the user asks to save the findings, append a record to `memory/<tenant>/audit_history.jsonl` via:
   ```
   rattle <tenant> memory record-decision "<summary>"
   ```
   Do not write to that file silently.

## Boundaries

- The slash command itself does not write to the API. Writes happen only through `rattle-config-builder` after explicit confirmation.
- Always cite check ids and rule ids in findings. They are the keys downstream tools use to track progress over time.

$ARGUMENTS
