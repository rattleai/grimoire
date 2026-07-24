---
name: rattle-configurator
description: Use this skill whenever the user is building, auditing, restructuring, or asking questions about a product configuration on the Rattle SaaS platform (rattleapp.de). Activates for pricelist analysis, BOM-aware configuration design, areas/groups/options modelling, constraints, document/offer templates, and any "Rattle" or "configurator" task. Encodes the #1 rule (explicit options for ALL variants), the full data model, configuration rules, anti-patterns, and structural checks. Load this skill before any Rattle API work or consulting recommendation.
license: MIT
---

# Rattle Configurator Consulting

You are advising on the **Rattle product configurator** (rattleapp.de) — a SaaS platform where products are decomposed into Areas → Groups → Options, with a Bill-of-Materials driven by `usage_subclauses` linking parts to options. This skill encodes the consulting expertise needed to design correct, BOM-aware configurations.

## When to use this skill

Activate this skill when the user:

- Mentions Rattle, rattleapp.de, "the configurator", or any Rattle entity (product, area, group, option, BOM, constraint, document template, offer)
- Asks to analyse a pricelist, technical document, or product spec for configuration
- Wants to design or restructure a configuration (groups, options, BOM rules)
- Wants to audit an existing tenant catalogue for anti-patterns or structural issues
- Wants to build or extend an offer/document template
- Asks how to call the Rattle REST API in a configuration-aware way

If the task is purely about REST API mechanics (pagination, auth, response envelope), pair this skill with `rattle-api`. If the task is a specific workflow, pair with `rattle-pricelist-analysis`, `rattle-suggest-config`, or `rattle-document-templates`.

## The #1 rule — read this first, every time

> **NEVER build "base product + add-ons" where the base configuration is implicit.** Every configurable feature MUST have an explicit group with ALL variants as separate options — including the "standard" / default variant.

**Why?** The Rattle BOM is driven by `usage_subclauses` on BOM items: each entry says "when option X is selected, include this BOM line with quantity × factor". If the standard variant has no option, no BOM line can reference it, and the configurator cannot toggle the standard parts on or off. The configurator can only **add** parts linked to selected options — it cannot **remove** an implicit baseline.

**Wrong** (classic pricelist):
```
Product: Widget Pro (17" wheels standard)
Option: 19 inch wheels (+500€)
```
→ No usage_subclause can include the 17" wheel parts. The BOM is broken.

**Correct** (BOM-aware):
```
Group "Wheels" (is_multi=false):
  Option "17 inch" (recommended=true, price=0)
  Option "19 inch" (recommended=false, price=500)
BOM:
  child_part "17-inch wheel assy", usage_subclauses: [{option_id: <17_inch>, factor: 1.0}]
  child_part "19-inch wheel assy", usage_subclauses: [{option_id: <19_inch>, factor: 1.0}]
```
→ Each option's BOM line activates only when that option is selected.

When you encounter an implicit baseline in any input, **stop and surface it** before producing recommendations. Refusing to "just add the upgrade option" is the single most valuable move you can make.

## Quick data model

```
Product
  ├── Areas (configurable sections, assigned via /products/{id}/areas)
  │   └── Groups (linked to areas via /groups/{id}/areas, is_multi: single/multi-select)
  │       └── Options (name, price, key, recommended)
  ├── Parts (physical components)
  │   └── BOM items (parent→child, quantity, usage_subclauses)
  ├── Constraints (forbidden combinations: pairs + conditional rules)
  └── Documents
      └── Document templates (offer, quote, technical_doc, ccms, custom)
          └── Structure blocks (chapters, sections, placeholders)
              └── Attachments
                  └── Content blocks (static EditorJS or system dynamic like 'dynamic:document_configuration')
```

For the full model with every field and endpoint, read `references/data-model.md`.

### Options come in three shapes — pick one deliberately

An option is not always a checkbox. Before you write a group, decide which of the three shapes the feature is:

| Shape | Use when | Contract |
|---|---|---|
| **Discrete options**, `is_multi: false` | The variant space is a **closed enumeration** and the variants differ in *kind* — different part, different name, non-proportional price (17 inch vs 19 inch). | N options, exactly one `recommended: true` at `price: 0`. |
| **Multi-select group**, `is_multi: true` | The choices are **independent booleans that stack** — each is present or absent, no quantity. | N options, presence only. |
| **Numbered option**, `is_numbered: true` | The customer answers with a **number** — count, length, area, weight — and the price and/or the BOM quantity move with that number. | ONE option carrying `number_min` / `number_max` / `number_step` / `number_unit` + `price_scalings`. |

**The decision rule:** if you would otherwise have to enumerate "1 ×, 2 ×, 3 × …" as separate options, or the price is `unit_price × n`, it is a **numbered option** — not N discrete options. Per-metre / per-piece / per-unit pricing in a pricelist is the tell (anti-pattern `per-unit-priced-row`).

A numbered option is still bound by the #1 rule: it is an **explicit** option inside an explicit group. Presence and amount are independent — `usage_subclauses` decide *whether* a BOM line is active, `option_scalings` decide *how much*. Never model "feature absent" as amount 0; give absence its own option so a subclause can switch the line off.

Depth lives elsewhere: `rattle-suggest-config/SKILL.md` § "Numbered options (numeric quantities)" for the sales-side design decision, `rattle-bom-builder/references/numbered-options.md` for the 12 BOM scaling patterns, `rattle-bom-builder/references/option-scalings.md` for the three descriptor shapes.

## How to use this skill

When asked to do anything Rattle-related, work in this order:

1. **Ground in the model**: confirm which entities the task touches (areas, groups, options, BOM, constraints, documents). If unclear, ask one targeted question.
2. **Check the rules**: every recommendation must satisfy the rules in `references/configuration-rules.md`. The non-negotiable ones are `explicit-options-for-all-variants`, `no-empty-areas`, and `offer-requires-configuration-block`.
3. **Scan for anti-patterns**: before designing, look for the patterns in `references/anti-patterns.md`. If the input contains implicit-base-config or addon-only-options indicators, surface them first and propose explicit-option restructuring.
4. **Reuse before you create**: per the `reuse-over-duplicate` rule, prefer linking an existing group to a new area (and using option area-config for per-area price overrides) over creating a duplicate group. When the user has an existing catalogue, ask to see it (or load it) before proposing new groups.
5. **Plan the BOM at the same time as the configuration**: each option that affects physical parts must have a `usage_subclauses` plan. Options for software, services, or pure-cosmetics may have empty BOM rules — that is normal and expected.
6. **Consider constraints**: identify forbidden combinations. Use pair-level constraints — `POST /constraints` body `{"product_id": <id>, "forbidden": [{"option_id1": <a>, "option_id2": <b>}, ...]}` (atomic-replace; uses `X-Constraints-Version` OCC header → 409 on conflict) — for simple exclusions; use conditional rules (`POST /constraints/rules` with `rule_json: {"requires": [...], "invalid": [...]}`) for "if A then forbid B and C". Both shapes are detailed in `references/data-model.md`.
7. **For offer/document work**: the `offer` doc_type **requires** a structure block attachment to the system dynamic content block `dynamic:document_configuration`. Read `references/structural-checks.md` for the full contract.

## Reference files

Read these on demand — they hold the full detail.

| File | Use when |
|---|---|
| `references/data-model.md` | You need the full schema of any Rattle entity |
| `references/configuration-rules.md` | You need to cite or apply a specific rule |
| `references/anti-patterns.md` | You're scanning an input for problems |
| `references/structural-checks.md` | You're auditing a live tenant catalogue |
| `references/system-prompts.md` | You're constructing a prompt for a downstream task or LLM call |

## Universal output expectations

When you produce a configuration recommendation, structure it as JSON with these top-level keys (mirrors the existing `tasks.suggest_configuration` contract):

```json
{
  "products": [
    {
      "name": "string",
      "groups": [
        {
          "name": "string",
          "is_multi": false,
          "description": "string",
          "options": [
            {"name": "string", "recommended": true, "price": 0, "description": "string"}
          ],
          "reuse_existing": false,
          "existing_group_id": null
        }
      ],
      "bom_rules": [
        {"child_part_name": "string", "usage_subclauses": [{"option_name": "string", "factor": 1.0}]}
      ],
      "forbidden": [
        {"option_name_1": "string", "option_name_2": "string", "reason": "string"}
      ],
      "constraint_rules": [
        {"description": "string", "rule_json": {"requires": [{"anyOf": ["option name"]}], "invalid": ["option name"]}}
      ]
    }
  ]
}
```

For an audit, return `{summary, fixes: [{check_id, entity_id, severity, fix_description, related_rules}]}`.
For an offer template, return `{template_name, chapters: [{slug, title, order_index, attachments: [{content_block_id, dynamic_key, is_required}]}]}`.

## Tenant memory

Some tenants override defaults (e.g. "never set custom keys", "always set German product names verbatim"). The Python execution layer (`rattle_api.memory.TenantMemory`) loads `memory/<tenant>/profile.md` and injects it as a `## Tenant preferences` section in every system prompt. When the user mentions a specific tenant, ask if there is a profile to honour, and respect those preferences over the defaults in this skill.

## Related skills

- `rattle-api` — REST API surface (auth, pagination, 472 operations across 260 paths)
- `rattle-pricelist-analysis` — workflow for analysing pricelists
- `rattle-suggest-config` — workflow for generating BOM-aware recommendations
- `rattle-document-templates` — workflow for building offer templates
