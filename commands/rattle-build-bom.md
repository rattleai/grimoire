---
description: Build a variant Bill of Materials (BOM) for a Rattle product — connect areas and options to parts via usage_subclauses, scale quantities by numbered options via option_scalings, model alternates via alt_group, and produce the canonical variant-bom.json that rattle-config-builder applies idempotently. Walks the design → validation → handoff pipeline. Honours the #1 configurator rule (every standard variant gets an explicit option) and the cardinal BOM rule (every option that affects physical parts has at least one BOM line referencing it).
argument-hint: <tenant> <product-id-or-name> [--from <recommendation.json>] [--inputs <parts-list.json>]
---

# /rattle-build-bom

Design / fix / validate a variant BOM for the configuration at `$ARGUMENTS`.

## Workflow

1. **Spawn the architect agent.** Delegate to `rattle-bom-architect`. It loads the host skill (`skills/rattle-bom-builder/SKILL.md`) plus all six references (data-model, usage-subclauses, option-scalings, numbered-options, bom-explosion, api-endpoints) plus the configurator + suggest-config + apply-config skills.

2. **Establish the configuration.** The architect needs:
   - The product id (and tenant).
   - The full set of groups and options (`GET /api/v1/groups?product_id=...` and `/options?group_id=...`).
   - For each numbered option: the `is_numbered`, `number_min`, `number_max`, `number_step`, `number_unit`.
   - The areas assigned to the product.

   If the configuration is incomplete (no explicit option for the standard variant of a feature, missing groups, …), surface the gap and refuse to design a BOM around it. Use `rattle-suggest-config` first.

3. **List the parts and their placements.** For every option that affects physical parts, identify:
   - The child part (the "added" part).
   - The parent (often the product's root assembly placeholder or an existing area-bound parent).
   - Whether the line is a `PartPlacement` (Part ↔ Area) or a `BomItem` (Parent ↔ Child).

4. **Author the variant-bom.json.** For each line, set:
   - `usage_subclauses` — the conditional inclusion (use empty `[]` for "always include").
   - `option_scalings` — quantity scaling for numbered options (ratio `{opt, part}` for proportional, range `{areas: [...]}` for bracketed).
   - `quantity` — base quantity. **Must be > 0** (Pydantic `BomItemCreateRequest.quantity` is `Field(1.0, gt=0, le=1e9)`; the API rejects `quantity=0` with 422 even when range-mode `option_scalings` would override at explosion time). Use `quantity=1` and document the absolute-vs-additive intent in the line's `note`.
   - `scrap_percent` — manufacturing scrap allowance (BomItem only).
   - `alt_group` + `priority` — for true alternates.
   - `ghost_part` — only for legitimate phantom assemblies.

   Follow the canonical patterns in `references/numbered-options.md` (12 patterns from one-to-one count scaling to length-with-overlap to threshold-stepped).

5. **Validate.** Run `python skills/rattle-bom-builder/scripts/validate_variant_bom.py <path>` (use `--strict` to fail on warnings). The validator catches:
   - Malformed clauses or scaling descriptors.
   - Range descriptors with overlapping intervals.
   - Ratio descriptors with `opt ≤ 0`.
   - alt_groups with duplicate priorities.
   - Legacy bare-numeric scalings (warn — prefer structured).
   - Self-referencing bom_items, bad effective-date order.

6. **Hand off to `rattle-config-builder`.** It applies idempotently via:
   - `ensure_part` (key: `(company_id, part_number)`)
   - `ensure_part_placement` (key: `(part_id, area_id)`)
   - `ensure_bom_item` (key: `(parent_part_id, child_part_id, alt_group, effective_from, effective_to)`)

## Validation gates (the architect enforces these before handoff)

Before flipping any BOM live, the architect must confirm:

- **Every option that affects physical parts is referenced by at least one `usage_subclause`.**
- **Every standard variant is its own explicit option** (the #1 rule from `rattle-configurator`).
- **Every numbered-option-driven quantity has the right scaling descriptor** (ratio or range, not bare numeric).
- **No alt_group has duplicate priorities** under the same parent.
- **No range descriptor has overlapping intervals.**
- **`is_numbered: true`** is set on every option referenced in `option_scalings`.
- **`uom`** matches between option (`number_unit`) and part for length / area scalings.

## Output

The agent produces:

1. **`variant-bom.json`** — the canonical contract (parts + placements + bom_items + validation summary). Shape documented in `skills/rattle-bom-builder/SKILL.md` "Output contract".
2. **Validation report** — errors and warnings from the validator.
3. **Notes** — any placeholder part numbers, ambiguities surfaced for user confirmation, or alt_group decisions made.

## Hand-off

For writes, delegate to `rattle-config-builder` with the `variant-bom.json` payload. The builder uses the idempotent `ensure_*` operations; reruns are safe.

For the actual BOM explosion preview (configuration-aware), use `POST /api/v1/parts/{id}/bom/explode` after the build is applied.

$ARGUMENTS
