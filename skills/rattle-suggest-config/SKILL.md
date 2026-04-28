---
name: rattle-suggest-config
description: Use this skill when the user is ready to turn a pricelist or feature spec into a concrete BOM-aware configuration recommendation for the Rattle platform — explicit groups, options, BOM rules with usage_subclauses, forbidden pairs, and conditional constraint rules. Reuses existing groups instead of duplicating, honours per-area pricing via option-area-config, and respects tenant memory preferences. Output is the JSON contract consumed by rattle-apply-config / RattleClient writes. Pair with rattle-configurator (knowledge) and rattle-api (writes).
license: MIT
---

# Rattle suggest configuration

Generates the BOM-aware configuration recommendation: explicit groups (one per configurable feature), explicit options for every variant including the standard, BOM rules with `usage_subclauses` linking parts to options, forbidden pairs, and conditional rules. Output is structured JSON ready for an idempotent builder to execute.

## When to use this skill

- The user has a pricelist or product spec and wants a concrete proposal for groups/options/BOM/constraints.
- The user has run `rattle-pricelist-analysis` and now wants the next-step recommendation.
- The user wants to review a draft restructure before applying it to the live tenant.

If the user wants to explore *whether* the input has issues, run `rattle-pricelist-analysis` first. If the user wants to push the recommendation to the live tenant, use `rattle-api` plus the apply-config workflow described in `rattle-configurator/references/system-prompts.md` (`system_prompt_apply_config`).

## Workflow

1. **Pre-load context.**
   - `rattle-configurator/references/configuration-rules.md` — every recommendation must satisfy these rules.
   - `rattle-configurator/references/anti-patterns.md` — make sure no proposed group itself reproduces an anti-pattern.
   - `rattle-configurator/references/system-prompts.md` § `system_prompt_suggest_configuration` — the prompt template you are following.

2. **Fetch the existing catalogue (if a tenant is named).** Call `GET /groups` (with options inlined or via `?include=options`) for the tenant. The first 50 groups go into the prompt's "Existing Groups & Options (MUST check for reuse)" section. When a proposed group's name matches or is very similar to an existing one, set:
   - `reuse_existing: true`
   - `existing_group_id: <id>`
   - `price_overrides`: a map of `area_name → option_name → price` for area-specific pricing differences (these become `option-area-config` writes downstream).

3. **For each product, propose explicit groups.** Apply the rules in priority order:
   - **Every configurable feature gets a group** (`explicit-options-for-all-variants`).
   - **Every variant is an explicit option, including the standard** — never an implicit baseline.
   - **Mark the standard option `recommended=true` and `price=0`.** Surcharges go on the upgrade options.
   - **Choose `is_multi`**: `false` for mutually-exclusive variants (one wheel size at a time), `true` for stackable choices (multiple software modules selectable in parallel).
   - **No custom `key`** unless the tenant memory profile explicitly opts in (`minimal-keys`).

4. **Plan the BOM.** For every option that affects physical parts, emit a `bom_rules` entry with `child_part_name` and `usage_subclauses: [{option_name, factor}]`. Software / services / cosmetic options can have no BOM rule — that is normal. Do **not** invent part numbers; if a part name is unclear, propose a placeholder and flag it in `notes`.

5. **Identify forbidden combinations.** Walk every pair of options across groups; flag combinations that are physically or contractually impossible. Output as `forbidden_pairs` (simple option-option exclusion → `POST /constraints` with pairs) or `constraint_rules` (conditional `if ... then forbid_options ...` → `POST /constraints/rules`).

6. **Honour tenant memory.** If the tenant profile specifies "always set German names verbatim", "never use custom keys", "doc_type=offer with X chapter", apply those overrides before producing the final JSON.

7. **Validate before returning.**
   - Every group has at least one option with `recommended=true` (or is multi-select with no default).
   - No two groups share the same lower-cased name (would violate `duplicate-group-names`).
   - No proposed area is empty of groups (`no-empty-areas`).
   - Every `usage_subclause` references an option that exists in the proposed groups.
   - `forbidden_pairs` reference options that exist.

## Output contract

```json
{
  "products": [
    {
      "name": "...",
      "groups": [
        {
          "name": "...",
          "is_multi": false,
          "description": "...",
          "options": [
            {"name": "...", "recommended": true, "price": 0, "description": "..."}
          ],
          "reuse_existing": false,
          "existing_group_id": null,
          "price_overrides": {}
        }
      ],
      "bom_rules": [
        {
          "child_part_name": "...",
          "usage_subclauses": [{"option_name": "...", "factor": 1.0}]
        }
      ],
      "forbidden_pairs": [
        {"option_name_1": "...", "option_name_2": "...", "reason": "..."}
      ],
      "constraint_rules": [
        {
          "description": "...",
          "rule_json": [
            {"if": {"option_selected": "name"}, "then": {"forbid_options": ["name"]}}
          ]
        }
      ]
    }
  ],
  "notes": [
    "Standard wheel size assumed to be 17-inch — please confirm before applying."
  ]
}
```

## Handing off to a builder

The output above is the input to `system_prompt_apply_config` (see `rattle-configurator/references/system-prompts.md`). That prompt converts the recommendation into a sequence of idempotent `ensure_*` operations matched by name:

- `ensure_product`, `ensure_area`, `ensure_group` (with `link_to_areas`), `ensure_option`, `ensure_area_config`, `ensure_constraint_pair`, `ensure_constraint_rule`.

A builder iterates these against the live API. The Python CLI's eventual `apply-config` subcommand is one such builder; non-Python clients can replicate the loop using `rattle-api/references/client-patterns.md` § "Idempotent ensure".

## How this maps to the existing CLI

```bash
rattle <tenant> ai-suggest-config source/<tenant>/pricelist.xlsx --language de --product "Widget Pro"
```

That command runs the canonical reference behaviour: it loads tenant memory, fetches existing groups, assembles the prompt, calls the configured AI provider, and prints the JSON above. This skill captures the workflow so any AI client (Claude.ai, Cursor, MCP) can reproduce it.

## Related skills

- `rattle-configurator` — knowledge backing every recommendation.
- `rattle-pricelist-analysis` — the prerequisite step.
- `rattle-document-templates` — for offer/document work, which often happens alongside config restructure.
- `rattle-api` — REST surface for actually writing the recommendation back.
