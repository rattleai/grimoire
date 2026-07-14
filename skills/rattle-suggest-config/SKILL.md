---
name: rattle-suggest-config
description: Use this skill when the user is ready to turn a pricelist or feature spec into a concrete BOM-aware configuration recommendation for the Rattle platform — explicit groups, options (discrete, multi-select, and NUMBERED options with is_numbered / number_min / number_max / number_step / number_unit / price_scalings), BOM rules with usage_subclauses and option_scalings, forbidden pairs, and conditional constraint rules. Reuses existing groups instead of duplicating, honours per-area pricing via option-area-config, and respects tenant memory preferences. Output is the JSON contract consumed by rattle-apply-config / RattleClient writes. Pair with rattle-configurator (knowledge) and rattle-api (writes).
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

2. **Fetch the existing catalogue (if a tenant is named).** Call `GET /groups` (paginated with `?cursor=` / `?limit=`; the route does NOT accept `?include=options`). For each group, fetch options separately via `GET /groups/{id}/options`, OR fetch the whole product graph in one shot via `GET /products/{id}?expand=areas.groups.options`. The first 50 groups go into the prompt's "Existing Groups & Options (MUST check for reuse)" section. When a proposed group's name matches or is very similar to an existing one, set:
   - `reuse_existing: true`
   - `existing_group_id: <id>`
   - `price_overrides`: a map of `area_name → option_name → price` for area-specific pricing differences (these become `option-area-config` writes downstream).

3. **For each product, propose explicit groups.** Apply the rules in priority order:
   - **Every configurable feature gets a group** (`explicit-options-for-all-variants`).
   - **Every variant is an explicit option, including the standard** — never an implicit baseline.
   - **Mark the standard option `recommended=true` and `price=0`.** Surcharges go on the upgrade options.
   - **Choose `is_multi`**: `false` for mutually-exclusive variants (one wheel size at a time), `true` for stackable choices (multiple software modules selectable in parallel).
   - **No custom `key`** unless the tenant memory profile explicitly opts in (`minimal-keys`).

4. **Decide each feature's option shape — discrete, multi-select, or numbered.** Do this *before* writing the group. A feature the customer answers with a **number** (24 panels, 450 cm of run, 12 openings) is ONE numbered option (`is_numbered: true`), not N discrete options and not a multi-select group. Getting this wrong is unrecoverable downstream: `option_scalings` on a BOM line can only scale against a numbered option. Full decision rule and field contract: § "Numbered options (numeric quantities)" below.

5. **Plan the BOM.** For every option that affects physical parts, emit a `bom_rules` entry with `child_part_name` and `usage_subclauses: [{option_name, factor}]`. For every part whose *quantity* moves with a numbered option, add `option_scalings` on the same rule (`usage_subclauses` says **whether**, `option_scalings` says **how much** — they are independent). Software / services / cosmetic options can have no BOM rule — that is normal. Do **not** invent part numbers; if a part name is unclear, propose a placeholder and flag it in `notes`.

6. **Identify forbidden combinations.** Walk every pair of options across groups; flag combinations that are physically or contractually impossible. Output as `forbidden` (simple option-option exclusion — apply-config submits as `POST /constraints` body `{product_id, forbidden: [{option_id1, option_id2}, ...]}` atomic-replace; the body field is `forbidden`, not the legacy `forbidden_pairs` or `pairs`) or `constraint_rules` (conditional rule whose `rule_json` body is `{requires: [<clause>...], invalid: [<option_id>...]}` evaluated by `app/utils/constraint_solver._rule_active` and `ForbiddenRule.violates` — NOT the legacy `[{if, then}]` shape).

7. **Honour tenant memory.** If the tenant profile specifies "always set German names verbatim", "never use custom keys", "doc_type=offer with X chapter", apply those overrides before producing the final JSON.

8. **Validate before returning.**
   - Every group has at least one option with `recommended=true` (or is multi-select with no default).
   - No two groups share the same lower-cased name (would violate `duplicate-group-names`).
   - No proposed area is empty of groups (`no-empty-areas`).
   - Every `usage_subclause` references an option that exists in the proposed groups.
   - `forbidden` (formerly `forbidden_pairs`) references options that exist.
   - Every option referenced by an `option_scalings` or `price_scalings` key is `is_numbered: true` — a scaling entry against a boolean option is a silent no-op (it carries no amount).
   - Every numbered option has `number_min ≤ number_max`, an integer `number_step ≥ 1`, and a `number_unit` that matches the `uom` of the parts it scales.
   - Every range descriptor (`{areas: [{min, max, part}]}`) stays inside `[number_min, number_max]` — a range the input can never reach is dead code.

## Numbered options (numeric quantities)

A **numbered option** (`is_numbered: true`) renders a numeric input instead of a checkbox. The number the customer enters flows through the runtime as `option_amounts[option_id]`, and every BOM edge whose `option_scalings` references that option id resolves with it plugged in. A boolean option carries **presence only** — there is no amount to scale against, so `option_scalings` on it is a silent no-op.

This is the mechanic behind the most common BOM-scaling requirement in a real configurator ("24 panels, each needs 3 brackets"; "ribbon length scales with run length"). If the recommendation never proposes a numbered option, that requirement cannot be expressed at all.

### The decision rule

| Shape | Use when | What you emit |
|---|---|---|
| **N discrete options** in a single-select group (`is_multi: false`) | The variant space is a **closed enumeration** and the variants differ in *kind* — different part, different name, non-proportional price. 17 inch vs 19 inch. Standard vs premium spindle. | N options, exactly one `recommended: true` at `price: 0`. |
| **Multi-select group** (`is_multi: true`) | The choices are **independent booleans that stack** — each is present or absent, and there is no quantity. Software modules. Accessory kits. | N options, presence only. |
| **ONE numbered option** (`is_numbered: true`) | The customer answers with a **number** — count, length, area, weight — and the price and/or a BOM quantity move with that number. | One option carrying `number_min` / `number_max` / `number_step` / `number_unit` (+ `price_scalings`), plus `option_scalings` on every BOM rule it drives. |

Decide with these three tests, in order:

1. **The enumeration test.** If modelling it as discrete options would force you to write "1 ×, 2 ×, 3 × …" — it is a numbered option. A group of 48 options named after integers is always wrong.
2. **The price test.** If the price is `unit_price × n` (per metre, per piece, per unit), it is a numbered option with a **ratio** `price_scalings`. If the price is bracketed by quantity (1–10 → 900, 11–50 → 1600), it is still a numbered option, with a **range** `price_scalings`. A pricelist row priced per unit (anti-pattern `per-unit-priced-row`) is the tell — see `rattle-pricelist-analysis`.
3. **The kind test.** If two variants differ in *kind* (different physical part, different name the customer recognises), they are discrete options — even when a quantity is also involved. Model the kind as a discrete group and the quantity as a *separate* numbered option; do not fuse them.

Numbered options do not escape the #1 rule (`explicit-options-for-all-variants`). The option is explicit and lives in an explicit group. **Never model "feature absent" as amount 0** — presence and amount are independent (`rattle-bom-builder/references/numbered-options.md` § Runtime contract), so a selected numbered option still satisfies a presence clause whatever number it carries. Give absence its own option (or a `none` variant in a sibling group) so a `usage_subclause` can switch the BOM line off.

### The field contract

Verified against `OptionCreateRequest` / `OptionUpdateRequest` in `docs/openapi.json`:

| Field | Type | Notes |
|---|---|---|
| `is_numbered` | bool, default `false` | Turns the numeric input on. Required before any `option_scalings` / `price_scalings` key can reference this option. |
| `number_min` / `number_max` | **integer** 0…1 000 000, nullable | Bounds of the input. The wire schema is `integer` — a fractional bound is a 422. |
| `number_step` | **integer** 1…1 000 000, nullable | Granularity. There is no fractional step: for sub-unit granularity pick a finer `number_unit` (`cm` instead of `m`, `mm` instead of `cm`) and convert in the scaling ratio (`{"opt": 100, "part": 1}` turns cm into m). |
| `number_unit` | string ≤ 32 | Display unit: `pcs`, `m`, `mm`, `kg`, `m²`, `°`. **Match it to the `uom` of every part it scales** or cost reports become meaningless. |
| `price_scalings` | dict, keyed by stringified option id | Quantity-driven **price**. Same three descriptor shapes as `option_scalings` — legacy bare numeric, ratio `{opt, part}`, range `{areas: [{min, max, part}]}`. |

The option's own `price` stays the **fixed** component (charged once); `price_scalings` carries the **per-unit** component (the pricing engine resolves additively: `total = base + Σ contributions` — `rattle-bom-builder/references/option-scalings.md` § "Multiplicative vs additive resolution"). Put a flat setup fee on `price`, the per-metre rate in `price_scalings`, and say which is which in `notes`.

At **recommendation** time you do not have option ids. Key `option_scalings` and `price_scalings` by **option name**; apply-config resolves names → stringified ids on write (`schemas/recommendation.schema.json` § `bom_rule.option_scalings`). For `price_scalings` the key is the numbered option's own name (a self-reference).

The BOM side — 12 worked scaling patterns (one-to-one, many-to-one, one-to-many, length-scaled, stair-stepped, threshold breakpoint, multi-option composition, floors and ceilings) — is **not** repeated here. Read `rattle-bom-builder/references/numbered-options.md` and `references/option-scalings.md`, and hand the BOM design to `rattle-bom-architect` when it gets past one or two lines.

### Interaction with constraints

**The constraint DSL is presence-based only.** Pair constraints are `{option_id1, option_id2}`; rule clauses are `anyOf` / `allOf` / `groupSelections` over option ids (`schemas/apply-operations.schema.json` § `rule_clause`, `rattle-apply-config/references/operations-contract.md` § 7). **No clause can read `option_amounts`.** Therefore:

- A numbered option can participate in a constraint only as *selected / not selected*. You **cannot** express "forbidden when panels > 20", "requires the heavy frame above 15 m", or any other quantity threshold as a constraint.
- Express quantity limits with `number_min` / `number_max` (per-area via `ensure_area_config`, which can override the bounds per area). Express a quantity-driven **part swap** with a range descriptor or two alternate BOM lines (`alt_group` + `priority`) — not with constraints.

> **Caution, not a rule.** Whether the backend *accepts* a numbered option as a member of a forbidden pair is not documented anywhere in this repo, and nothing in the pair schema (`ForbiddenCombinationResponse`: `{option_id1, option_id2}`) excludes it. Do not design around it either way: if a pair involving a numbered option is unavoidable, verify it against the live tenant before committing, and flag the assumption in `notes`.

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
        },
        {
          "name": "Panels",
          "is_multi": false,
          "description": "Panel count — numeric input, drives bracket and brace quantities.",
          "options": [
            {
              "name": "Panel count",
              "price": 0,
              "recommended": true,
              "description": "Number of panels, 1–48.",
              "is_numbered": true,
              "number_min": 1,
              "number_max": 48,
              "number_step": 1,
              "number_unit": "pcs",
              "price_scalings": {"Panel count": {"opt": 1, "part": 120}}
            }
          ],
          "reuse_existing": false,
          "existing_group_id": null
        }
      ],
      "bom_rules": [
        {
          "child_part_name": "...",
          "usage_subclauses": [{"option_name": "...", "factor": 1.0}]
        },
        {
          "child_part_name": "Panel bracket",
          "parent_part_name": "Frame assembly",
          "quantity": 1,
          "uom": "pcs",
          "usage_subclauses": [{"option_name": "Panel count", "factor": 1.0}],
          "option_scalings": {"Panel count": {"opt": 1, "part": 3}},
          "note": "3 brackets per panel. quantity=1 is the API minimum (Pydantic gt=0) — it is the baseline, the scaled contribution is added on top."
        }
      ],
      "forbidden": [
        {"option_name_1": "...", "option_name_2": "...", "reason": "..."}
      ],
      "constraint_rules": [
        {
          "description": "...",
          "rule_json": {
            "requires": [{"anyOf": ["option name"]}],
            "invalid": ["option name"]
          }
        }
      ]
    }
  ],
  "notes": [
    "Standard wheel size assumed to be 17-inch — please confirm before applying.",
    "Panel count priced at 120 per panel via price_scalings (ratio); option price 0 = no fixed component."
  ]
}
```

> **`rule_json` is a single object `{requires, invalid}` — not an array, and never the legacy `[{if, then}]` / `forbid_options` shape.** The legacy shape saves (the column accepts any JSON) but `app/utils/constraint_solver._rule_active` never fires it. `option_scalings` / `price_scalings` keys are option **names** at recommendation time and stringified option **ids** after apply.

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
- `rattle-bom-builder` — the BOM mechanics behind `usage_subclauses` / `option_scalings` / numbered options. Load it whenever a recommendation proposes a numbered option or a non-trivial BOM rule.
- `rattle-document-templates` — for offer/document work, which often happens alongside config restructure.
- `rattle-api` — REST surface for actually writing the recommendation back.
