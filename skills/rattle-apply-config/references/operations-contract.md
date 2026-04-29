# Apply-config operations contract

Seven operation types. Each is idempotent (get-or-create matched by name). Order matters — emit in the sequence shown so dependencies exist before they're referenced.

## Order of execution

1. `ensure_product`
2. `ensure_area`
3. `ensure_group` (one per distinct group name across all products)
4. `ensure_option`
5. `ensure_area_config`
6. `ensure_constraint_pair`
7. `ensure_constraint_rule`

## 1. `ensure_product`

```json
{
  "type": "ensure_product",
  "name": "Widget Pro",
  "base_price": 0,
  "description": "..."
}
```

Match by `name` (case-insensitive). Create if absent; PATCH `base_price`/`description` if they differ.

REST: `GET /products?name=…` (or paginate), `POST /products`, `PATCH /products/{id}`.

## 2. `ensure_area`

```json
{
  "type": "ensure_area",
  "name": "Widget Pro — Configuration",
  "description": "...",
  "parent_product": "Widget Pro"
}
```

Match by `name`. Create if absent. After create, link to product via `POST /products/{productId}/areas {"area_id": <new_id>}`.

REST: `GET /areas?name=…`, `POST /areas`, `POST /products/{productId}/areas`.

## 3. `ensure_group`

```json
{
  "type": "ensure_group",
  "name": "Wheels",
  "is_multi": false,
  "description": "...",
  "link_to_areas": ["Widget Pro — Configuration", "Widget Pro Mini — Configuration"]
}
```

**Critical:** `link_to_areas` lists every area across **all** products that need this group. Emit ONE `ensure_group` per distinct group name (the `reuse-over-duplicate` rule), not one per product. The link step is per-area.

REST: `GET /groups?name=…`, `POST /groups`, then for each area `POST /groups/{id}/areas {"area_id": <area_id>}`.

## 4. `ensure_option`

```json
{
  "type": "ensure_option",
  "name": "17 inch",
  "price": 0,
  "recommended": true,
  "description": "...",
  "group": "Wheels"
}
```

Match by `(group_name, option_name)` — option names are unique within a group, not globally. Honour the tenant `minimal-keys` preference: omit `key` unless the tenant profile opts in.

REST: `GET /options?group_id=<id>` (then filter by name), `POST /options`, `PATCH /options/{id}`.

## 5. `ensure_area_config`

```json
{
  "type": "ensure_area_config",
  "option": "17 inch",
  "area": "Widget Pro — Configuration",
  "price": 200,
  "description": "..."
}
```

Per-area override for an option. Used when the same option has different prices in different areas/tiers — the `area-config-for-scaled-prices` rule. Skip if `price` matches the option's base price.

REST: `PUT /options/{option_id}/area-config?area_id=<area_id>`.

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
3. `POST /constraints` with `X-Constraints-Version: <version>` and body `{"product_id": <id>, "pairs": [...]}`.
4. On `412 Precondition Failed`, re-read and retry once.

REST: `GET /constraints`, `POST /constraints` (atomic replace).

## 7. `ensure_constraint_rule`

```json
{
  "type": "ensure_constraint_rule",
  "product": "Widget Pro",
  "description": "Off-road tires require all-terrain suspension",
  "rule_json": [
    {"if": {"option_selected": "Off-road tires"}, "then": {"forbid_options": ["Sport suspension", "Comfort suspension"]}}
  ]
}
```

Conditional rule. Match by `description` within the product. Create if absent; PATCH `rule_json` if it differs.

REST: `GET /constraints/rules?product_id=<id>`, `POST /constraints/rules`, `PATCH /constraints/rules/{id}`.

## Rejected operation types

Refuse any operation that is not in the seven above. In particular:

- `delete_*` — destructive; require a separate explicit user request and a separate workflow.
- `replace_all_*` — not idempotent in the get-or-create sense; misuse risk.
- `bulk_import` — bypasses the per-entity validation; not appropriate for consulting workflows.

If a recommendation includes a rejected type, abort with a clear error and ask the user to revise.

## Tenant memory overrides

Before emitting any operation, check `memory/<tenant>/profile.md`:

- `- **custom-keys**: never` → strip `key` from `ensure_group` and `ensure_option`.
- `- **option-standard-variant**: always present` → reject any `ensure_group` whose options do not include exactly one with `recommended=true` (already enforced by the recommendation validator).
- Tenant-specific naming rules → enforce in `name` casing/format before write.

The tenant memory check is mandatory — never apply recommendations without consulting it first.

## Failure handling

On any 4xx/5xx response:

1. Log the failed operation (type, name, request_id, problem-details body).
2. Stop further execution.
3. Return the partial `applied` list and the failed operation in `errors`.
4. Ask the user how to proceed (retry, skip, abort).

Never auto-retry on 4xx (those are usually input problems). Auto-retry once on transient 5xx (timeouts, gateway errors) with exponential backoff.
