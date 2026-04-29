---
description: Generate a BOM-aware Rattle configuration recommendation from a pricelist or analysis. Outputs explicit groups, options (including the standard variant), bom_rules with usage_subclauses, forbidden pairs, and conditional constraint rules in the canonical JSON shape.
argument-hint: <file path | tenant + source filename> [--product <name>] [--language de|en]
---

# /rattle-suggest-config

Produce a configuration recommendation for the input the user names (`$ARGUMENTS`).

## Workflow

1. **Load context** — Read `skills/rattle-suggest-config/SKILL.md`, `skills/rattle-configurator/references/configuration-rules.md`, and `skills/rattle-configurator/references/anti-patterns.md`. Validate every proposed group against the rules.

2. **Resolve tenant and input** — If the user names a tenant, resolve `source/<tenant>/<filename>` and load `memory/<tenant>/profile.md` for preferences. Honour every preference there.

3. **Fetch existing groups (if a tenant is named)** — Either:
   - Run `rattle <tenant> ai-suggest-config <source-relative-path> --language de [--product <name>]` (the canonical reference behaviour — it auto-loads memory and existing groups), or
   - Manually GET `/groups` (paginated) and pass the first 50 into the system prompt's "Existing Groups & Options (MUST check for reuse)" section.

4. **Generate the recommendation** — Apply the workflow steps in `skills/rattle-suggest-config/SKILL.md`:
   - Every configurable feature gets an explicit group with all variants as options.
   - Mark the standard option `recommended=true`, `price=0`.
   - Plan BOM rules for physical options.
   - Identify forbidden pairs and conditional rules.
   - Set `reuse_existing=true` whenever an existing group matches.

5. **Validate** — Walk the validation checklist in `skills/rattle-suggest-config/SKILL.md` § Workflow step 7 before returning.

6. **Output the canonical JSON shape** — As documented in `skills/rattle-suggest-config/SKILL.md` § Output contract.

7. **Offer next steps** — Suggest `/rattle-build-offer` if the recommendation surfaces narrative-area smell, or instruct the user to invoke the `rattle-config-builder` agent to apply the recommendation to the live tenant.

## Delegation

For multi-product recommendations or when reuse-detection across the entire catalogue matters, delegate to the `rattle-consultant` subagent.

$ARGUMENTS
