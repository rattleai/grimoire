# BOM data model — every field of every edge

Authoritative field reference for `Part`, `PartPlacement`, `BomItem`, and `BomLineRev`. All four entities share the same JSON helpers (`get_usage_subclauses`, `get_option_scalings`). Source: `app/models.py`.

## Part

The product-independent master record.

| Field | Type | Notes |
|---|---|---|
| `id` | int | PK |
| `part_number` | string | Unique within company (the canonical identifier) |
| `part_name` | string | Display name |
| `part_cost` | numeric | Reference cost (currency from company) |
| `uom` | string | Default unit-of-measure (`pcs`, `m`, `kg`, …) |
| `lifecycle_state` | string | `Draft` / `Review` / `Released` / `Obsolete` |
| `is_purchased` / `is_made` / `is_service` | bool | Manufacturing classification |
| `tags` | JSON list | Free-form labels |

`Part` does not carry `usage_subclauses` itself — only its **edges** (`PartPlacement`, `BomItem`) do.

## PartPlacement (Part ↔ Area edge)

Connects a Part to an Area. Placements determine which parts a product surface contains.

| Field | Type | Default | Notes |
|---|---|---|---|
| `id` | int | — | PK |
| `part_id` | int (FK Part) | — | The placed part |
| `area_id` | int (FK Area) | — | The area the part is placed on |
| `order_index` | int | 0 | Display order |
| `quantity` | numeric(12,3) | 1 | Base quantity |
| `uom` | string(16) | `pcs` | Quantity unit |
| `usage_subclauses` | JSON list | `[]` | Conditional inclusion rules |
| `option_scalings` | JSON dict | `{}` | Quantity scaling on numbered options |
| `ghost_part` | bool | false | Phantom assembly flag |

Indexes: `(area_id, order_index)`, `(area_id, part_id)`.

JSON helpers: `set_usage_subclauses`, `get_usage_subclauses`, `set_option_scalings`, `get_option_scalings` — all clean / normalise on write and read.

## BomItem (Parent-Part ↔ Child-Part edge)

The structural BOM tree edge. Multi-level BOMs are pure traversals of these.

| Field | Type | Default | Notes |
|---|---|---|---|
| `id` | int | — | PK |
| `parent_part_id` | int (FK Part) | — | The parent assembly |
| `child_part_id` | int (FK Part) | — | The child component |
| `quantity` | numeric(12,3) | 1 | Base quantity per parent |
| `uom` | string(16) | `pcs` | Quantity unit |
| `scrap_percent` | numeric(5,2) | 0 | Scrap / waste allowance (0–100) |
| `order_index` | int | 0 | Display order under parent |
| `alt_group` | string(50) | null | Alternates: same code → choose one |
| `priority` | int | 0 | Within alt_group, lowest wins |
| `part_group_id` | int (FK PartGroup) | null | Optional grouping |
| `effective_from` / `effective_to` | date | null | Date validity window |
| `usage_subclauses` | JSON list | `[]` | Conditional inclusion |
| `option_scalings` | JSON dict | `{}` | Quantity scaling |
| `ghost_part` | bool | false | Phantom assembly flag |
| `note` | text | null | Free-form note |

Constraints:
- `parent_part_id <> child_part_id` (no self-reference).
- Unique `(parent_part_id, child_part_id, alt_group, effective_from, effective_to)` — prevents duplicate variant lines.

Indexes: `(parent_part_id, alt_group, priority, order_index)`.

## BomLineRev (Revisioned BOM line)

Same fields as `BomItem` but bound to **ItemRevision** rows instead of Parts. Used when the manufacturing ERP needs a revision-locked BOM (e.g. revision A vs. B of a mechanical drawing).

| Field | Type | Notes |
|---|---|---|
| `parent_rev_id` / `child_rev_id` | int (FK ItemRevision) | Revisions instead of parts |

All other fields (`quantity`, `uom`, `scrap_percent`, `order_index`, `alt_group`, `priority`, `effective_from/to`, `usage_subclauses`, `option_scalings`, `note`) are identical to `BomItem`.

## Option (used by usage_subclauses + option_scalings)

| Field | Type | Notes |
|---|---|---|
| `id` | int | Referenced by `groupSelections` and `option_scalings` keys |
| `option_name` | string | Display |
| `option_price` | numeric | Reference price |
| `option_key` | string | Stable code for external integrations |
| `is_numbered` | bool | Enables numeric input — required for `option_scalings` to scale |
| `number_min` / `number_max` / `number_step` | int | Bounds for numeric input |
| `number_unit` | string | Display unit (`m`, `pcs`, …) |
| `price_scalings` | JSON dict | Same shape as `option_scalings`, but for price |
| `recommended` | bool | Default-selected hint |
| `group_id` | int (FK Group) | Parent group |

Options of `is_numbered: true` flow through the runtime as `option_amounts[opt_id]` carrying the user's selected number; non-numbered options just carry presence.

## JSON shapes used in the API

| Field | Shape |
|---|---|
| `usage_subclauses` | `[<clause>, ...]` — see `usage-subclauses.md` |
| `option_scalings` | `{<opt_id_str>: <descriptor>, ...}` — see `option-scalings.md` |
| `price_scalings` | same shape as `option_scalings` |

API request / response schemas live in `app/schemas/v1/part.py`:

- `PartCreateRequest`, `PartUpdateRequest`, `PartResponse`
- `PartPlacementCreateRequest`, `PartPlacementUpdateRequest`, `PartPlacementResponse`
- `BomItemCreateRequest`, `BomItemUpdateRequest`, `BomItemResponse`

Validators enforce JSON-field size limits via `validate_json_field_size`.
