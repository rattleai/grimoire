# Apply-config operations contract

The `rattle-config-builder` agent speaks **15 idempotent `ensure_*` operation types across 3 tiers**:

| Tier | Operations | Source SKILL / agent |
|---|---|---|
| **Configurator** (this file) | 7 ops: `ensure_product`, `ensure_area`, `ensure_group`, `ensure_option`, `ensure_area_config`, `ensure_constraint_pair`, `ensure_constraint_rule` | `rattle-suggest-config` → `rattle-apply-config` |
| **BOM** | 3 ops: `ensure_part`, `ensure_part_placement`, `ensure_bom_item` | `rattle-bom-architect` → `agents/rattle-config-builder.md` § BOM tier |
| **Documents** | 5 ops: `ensure_template`, `ensure_structure_block`, `ensure_attachment`, `ensure_content_block`, `ensure_block_locale` | `rattle-techdoc-author` → `agents/rattle-config-builder.md` § Document tier |

This file documents the **configurator tier** in detail. The BOM and document tiers are documented in `agents/rattle-config-builder.md`. Each operation is idempotent (get-or-create-or-PATCH matched by natural key). A second run is a safe no-op.

## Order of execution (configurator tier)

1. `ensure_product`
2. `ensure_area`
3. `ensure_group` (one per distinct group name across all products)
4. `ensure_option`
5. `ensure_area_config`
6. `ensure_constraint_pair`
7. `ensure_constraint_rule`

When mixed with BOM / document operations, the full dependency order is: products → areas → groups → options → area-configs → constraints → parts → placements → bom_items → templates → structure_blocks → content_blocks → attachments → block_locales.

## 1. `ensure_product`

```json
{
  "type": "ensure_product",
  "name": "Widget Pro",
  "base_price": "0.00",
  "description": "..."
}
```

Match by `name` (case-insensitive). Create if absent; PATCH `base_price`/`description` if they differ. `base_price` is serialised as a decimal string on the wire (Numeric(10,2) column). The builder accepts either a string or a number and coerces.

REST: `GET /products?search=<name>` (the route accepts only `cursor`, `limit`, `search`, `status` — there is no `?name=` parameter; `?search=` does case-insensitive ILIKE on `name` and `description`), `POST /products`, `PATCH /products/{id}`.

## 2. `ensure_area`

```json
{
  "type": "ensure_area",
  "name": "Widget Pro — Configuration",
  "description": "...",
  "price": "0.00",
  "language": "DE",
  "allow_disable": false,
  "parent_product": "Widget Pro"
}
```

Match by `name`. Create if absent. **Two ways to attach the area to a product:** (a) include `product_id` (or the `parent_product` name shortcut, which the builder resolves to an id) on the `POST /areas` body — `AreaCreateRequest.product_id` does the link in one shot; or (b) create the area first with no product and link separately via `POST /products/{productId}/areas {"area_id": <new_id>}`. Use option (a) for new areas; option (b) only when adding an existing area to a second product.

REST: `GET /areas?search=<name>` (filters: `cursor`, `limit`, `search`, `product_id`), `POST /areas`, `POST /products/{productId}/areas`.

## 3. `ensure_group`

```json
{
  "type": "ensure_group",
  "name": "Wheels",
  "is_multi": false,
  "description": "...",
  "language": "DE",
  "link_to_areas": ["Widget Pro — Configuration", "Widget Pro Mini — Configuration"]
}
```

**Critical:** `link_to_areas` lists every area across **all** products that need this group. Emit ONE `ensure_group` per distinct group name (the `reuse-over-duplicate` rule), not one per product. The link step batches all areas in a single call.

REST: `GET /groups?search=<name>` (filters: `cursor`, `limit`, `search`), `POST /groups`, then **one** `POST /groups/{id}/areas` with body `{"area_ids": [<area_id>, …]}` — note the **plural array** field. The endpoint links every area in one round-trip; do not loop per area.

## 4. `ensure_option`

```json
{
  "type": "ensure_option",
  "name": "17 inch",
  "price": "0.00",
  "recommended": true,
  "description": "...",
  "group": "Wheels",
  "is_numbered": false,
  "number_min": null,
  "number_max": null,
  "number_step": null,
  "number_unit": "",
  "price_scalings": {}
}
```

Match by `(group_name, option_name)` — option uniqueness within a group is a **builder convention**, not a backend invariant (no `UniqueConstraint(group_id, name)` on the model). Honour the tenant `minimal-keys` preference: omit `key` unless the tenant profile opts in.

Numbered options carry a numeric input (`is_numbered=true` + `number_min/max/step` bounds + `number_unit` display unit) and `price_scalings` for quantity-driven pricing. The same descriptor shapes (legacy bare numeric, ratio `{opt, part}`, range `{areas: [{min, max, part}]}`) used for `option_scalings` apply here for price — see `skills/rattle-bom-builder/references/option-scalings.md`.

REST: `GET /options?group_id=<id>` (filters: `cursor`, `limit`, `search`, `group_id`, `area_id`), `POST /options`, `PATCH /options/{id}`.

## 5. `ensure_area_config`

```json
{
  "type": "ensure_area_config",
  "option": "17 inch",
  "area": "Widget Pro — Configuration",
  "price": "200.00",
  "option_description": "Per-area override of Option.description",
  "recommended": true,
  "is_numbered": false,
  "number_min": null,
  "number_max": null,
  "number_step": null,
  "number_unit": ""
}
```

Per-area override for an option. Used when the same option has different price / `recommended` / numbered-option bounds / description in different areas — the `area-config-for-scaled-prices` rule. Skip if every override field matches the base option.

> **Field name precision.** The schema field is **`option_description`**, NOT `description` — `AreaConfigUpdateRequest` has `extra="forbid"` and rejects `description` with 422. The 9 REST-overridable fields are: `price`, `option_key`, `option_description`, `recommended`, `is_numbered`, `number_min`, `number_max`, `number_step`, `number_unit`. (The model also supports `image` and `price_scalings` overrides, but those are not exposed via the area-config REST endpoint — set them via the dedicated image-upload route and the option's own `price_scalings` field, respectively.)

REST: `PUT /options/{option_id}/area-config?area_id=<area_id>` (the `?area_id=` query param is **required** — missing returns 400). DELETE the same path with optional `?field=<field_name>` (must be one of the 9 fields above) to clear a single override; omit `?field=` to clear every override and remove the row.

## 6. `ensure_constraint_pair`

```json
{
  "type": "ensure_constraint_pair",
  "product": "Widget Pro",
  "option_1": "19 inch",
  "option_2": "Off-road tires"
}
```

Simple option-option exclusion. **Batch all pairs for a product into one `POST /constraints` call** with optimistic concurrency:

1. `GET /constraints?product_id=<id>` → record `X-Constraints-Version` header.
2. Compute desired set of pairs (existing + new, deduplicated).
3. `POST /constraints` with `X-Constraints-Version: <version>` and body `{"product_id": <id>, "forbidden": [...]}`. The `ReplaceOptionConstraintsRequest` schema (`app/schemas/v1/constraint.py`) names the array `forbidden` — sending `pairs` returns 422.
4. On **409 Conflict** (the server returns 409 with `detail` containing `Version conflict:` for stale-version, NOT 412), re-read and retry once.

REST: `GET /constraints` (filter: `product_id`), `POST /constraints` (atomic replace). The same OCC pattern + `X-Areas-Version` applies to `POST /constraints/area`.

## 7. `ensure_constraint_rule`

```json
{
  "type": "ensure_constraint_rule",
  "product": "Widget Pro",
  "description": "Off-road tires require all-terrain suspension",
  "rule_json": {
    "requires": [
      {"anyOf": ["Off-road tires"]}
    ],
    "invalid": ["Sport suspension", "Comfort suspension"]
  }
}
```

Conditional rule. Match by `description` within the product. Create if absent; PATCH `rule_json` if it differs.

> **`rule_json` shape (CRITICAL).** The runtime evaluator (`app/utils/constraint_solver._rule_active` and `app/models.py` `ForbiddenRule.violates`) consumes a single object **`{requires: [<clause>...], invalid: [<option_id>...]}`** — NOT an array, and NOT the legacy `{if, then}` shape that some older OpenAPI examples show. A rule with the legacy shape will save (the column accepts any JSON) but the solver will never fire it. Each clause in `requires` uses one of `anyOf` (any of the listed option ids satisfies), `allOf` (all listed option ids must be selected), or `groupSelections` (map of stringified group_id → list of allowed option ids). The clauses are AND-folded; ALL must be satisfied for the rule to trigger. The builder resolves option/group names to ids before submitting.

REST: `GET /constraints/rules?product_id=<id>`, `POST /constraints/rules`, `PATCH /constraints/rules/{id}`.

## Rejected operation types

Refuse any operation type not in the configurator tier (above) AND not in the BOM/document tiers documented in `agents/rattle-config-builder.md`. In particular:

- `delete_*` — destructive; require a separate explicit user request and a separate workflow.
- `replace_all_*` — not idempotent in the get-or-create sense; misuse risk.
- `bulk_import` — bypasses the per-entity validation; not appropriate for consulting workflows.

If a payload includes a rejected type, abort with a clear error and ask the user to revise.
