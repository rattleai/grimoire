# API endpoints — variant-BOM operations

REST endpoints for parts, placements, and BomItems. All require `products:read` for GET and `products:write` for POST/PUT/PATCH/DELETE. Full reference: `rattle-api/references/api-reference.md`.

> **Validation gate.** Every shape below is enforced server-side by Pydantic schemas in `app/schemas/v1/part.py` with `extra="forbid"`. Any field not listed here will be rejected with HTTP 422 (RFC 9457 problem details). Quantities are bounded `gt=0, le=1e9` — **never POST `quantity: 0`**.

## Parts

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/parts` | List parts (filters: `search`, `status`, `part_type`; pagination: `cursor`, `limit`). The route in `app/routes/api_v1/parts.py` does NOT honour `make_or_buy` or `bom_structure` as query params — filter on those fields client-side. |
| POST | `/api/v1/parts` | Create a part |
| GET | `/api/v1/parts/{id}` | Get a part |
| PUT | `/api/v1/parts/{id}` | Replace a part |
| PATCH | `/api/v1/parts/{id}` | Partially update a part |
| DELETE | `/api/v1/parts/{id}` | Delete a part |
| GET | `/api/v1/parts/{id}/placements` | List placements of a part |
| POST | `/api/v1/parts/{id}/placements` | Create a placement |
| GET | `/api/v1/parts/{id}/bom` | List the parent's BOM children |
| POST | `/api/v1/parts/{id}/bom` | Create a BomItem |
| GET | `/api/v1/parts/{id}/bom/tree` | Hierarchical explosion tree |
| GET | `/api/v1/parts/{id}/bom/flat` | Flat explosion list |
| POST | `/api/v1/parts/{id}/bom/explode` | Explode the BOM (configuration-aware) |
| GET | `/api/v1/parts/{id}/ghost/status` | Phantom-resolution status |
| POST | `/api/v1/parts/{id}/ghost/resolve` | Resolve a phantom assembly |
| POST | `/api/v1/parts/{id}/ghost/materialize` | Materialise a resolved phantom |
| GET | `/api/v1/parts/export` | Bulk export (returns JSON document) |

> **There is no `POST /api/v1/parts/import` endpoint.** Bulk authoring goes through repeated calls to the create endpoints above (or via the idempotent `ensure_*` operations from `rattle-apply-config` + the BOM operation grammar in `agents/rattle-config-builder.md`). The only sibling export route is `GET /api/v1/parts/export`.

Body (Create part) — every field accepted by `PartCreateRequest` (`extra="forbid"`):

```json
{
  "part_number": "AX-55",
  "part_name": "Axis assembly",
  "part_cost": 1950,
  "part_type": "assembly",
  "part_description": "Top-level assembly for the X axis",
  "make_or_buy": "make",
  "commodity_code": null,
  "weight": 12.5,
  "weight_unit": "kg",
  "status": "active",
  "bom_structure": "normal",
  "phantom_resolve_mode": "smart_reuse",
  "custom_fields": {},
  "integration_metadata": null
}
```

| Field | Required | Type | Notes |
|---|---|---|---|
| `part_number` | yes | string (1..255) | Unique within company |
| `part_name` | yes | string (1..255) | |
| `part_cost` | no | int (default 0, `ge=0`) | **Integer**, not numeric — currency unit per company config |
| `part_type` | no | string\|null (≤ 32) | Enum (validator): `{"raw", "purchased", "manufactured", "assembly", "consumable"}` |
| `part_description` | no | string\|null (≤ 5000) | |
| `make_or_buy` | no | string\|null (≤ 8) | Enum (validator): `{"make", "buy"}` |
| `commodity_code` | no | string\|null (≤ 64) | HS / ECCN code |
| `weight` | no | float\|null (`ge=0, le=1e9`) | |
| `weight_unit` | no | string (≤ 8, default `"kg"`) | |
| `status` | no | string (≤ 32, default `"active"`) | Enum (validator): `{"active", "inactive", "deprecated"}` |
| `bom_structure` | no | string (≤ 16, default `"normal"`) | Enum (validator): `{"normal", "ghost"}` |
| `phantom_resolve_mode` | no | string (≤ 24, default `"smart_reuse"`) | Enum (validator): `{"smart_reuse", "always_new", "dissolve"}`. Only honoured when `bom_structure="ghost"`. |
| `custom_fields` | no | JSON object (default `{}`) | Tenant-defined extensions; ≤ 16 KB serialised, ≤ 100 keys, key pattern `[a-zA-Z0-9][a-zA-Z0-9_]{0,49}` |
| `integration_metadata` | no | JSON object\|null | ERP / external-system pass-through |

> **Notable absences from the create schema.** `PartCreateRequest` does NOT accept `part_img`. The field is exposed on `PartResponse` (resolved as a URL) but **there is no public REST upload route for `Part.part_img` today** — `app/routes/api_v1/images.py` only has upload routes for products, areas, and options. `part_img` is set only by the connector ingest pipeline (`app/connectors/engine.py`); for parts created via the public API, the field stays NULL. `extra="forbid"` returns 422 on any unknown field on POST/PATCH. Ghost parts (`bom_structure="ghost"`) are forced to `part_cost=0` server-side; cost rolls up from children at explosion time.

## Part placements

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/parts/{id}/placements` | Create a placement (also see Parts table) |
| PUT | `/api/v1/parts/placements/{placement_id}` | Replace |
| PATCH | `/api/v1/parts/placements/{placement_id}` | Partial update |
| DELETE | `/api/v1/parts/placements/{placement_id}` | Delete |

> The path is `/parts/placements/{id}` (under the parts namespace), **not** `/part-placements/{id}`. There is **no** standalone `GET /parts/placements/{id}` — list placements via `GET /parts/{id}/placements` instead.

Body (Create):

```json
{
  "part_id": 9001,
  "area_id": 42,
  "order_index": 0,
  "quantity": 1.0,
  "uom": "pcs",
  "ghost_part": false,
  "usage_subclauses": [],
  "option_scalings": {}
}
```

| Field | Required | Notes |
|---|---|---|
| `part_id` | yes | FK Part |
| `area_id` | yes | FK Area |
| `quantity` | no (default `1.0`) | `gt=0, le=1e9` — **must be > 0** even when `option_scalings` will override at explosion time |
| `uom` | no (default `"pcs"`) | length ≤ 16 |
| `usage_subclauses` | no (default `[]`) | See `usage-subclauses.md` |
| `option_scalings` | no (default `{}`) | See `option-scalings.md` |
| `ghost_part` | no (default `false`) | |

Body (Update / Patch): same fields, all optional; `extra="forbid"` rejects unknown fields.

## BOM items (`/parts/bom`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/parts/{id}/bom` | Create a BomItem under a parent |
| PUT | `/api/v1/parts/bom/{bom_id}` | Replace |
| PATCH | `/api/v1/parts/bom/{bom_id}` | Partial update |
| DELETE | `/api/v1/parts/bom/{bom_id}` | Delete |

> The path is `/parts/bom/{id}` (under the parts namespace), **not** `/bom-items/{id}`. There is **no** standalone `GET /parts/bom/{id}` — list children via `GET /parts/{id}/bom` instead.

Body (Create):

```json
{
  "parent_part_id": 9001,
  "child_part_id": 9120,
  "quantity": 1.0,
  "uom": "pcs",
  "scrap_percent": 0.0,
  "order_index": 0,
  "alt_group": null,
  "priority": 0,
  "effective_from": null,
  "effective_to": null,
  "note": null,
  "usage_subclauses": [],
  "option_scalings": {},
  "ghost_part": false
}
```

> **Do not include `part_group_id` on create or update.** The Pydantic `BomItemCreateRequest` / `BomItemUpdateRequest` schemas do not accept it (`extra="forbid"` returns 422). The field exists on the model and on `BomItemResponse` but is set out-of-band by the platform; treat it as read-only.

> Effective dates use ISO 8601 (`"2026-05-09"`).

## BOM explosion endpoint

`POST /api/v1/parts/{id}/bom/explode`

Body:

```json
{
  "configuration_id": 12345,
  "as_of": "2026-05-09",
  "resolve_ghosts": true
}
```

Response: the `rows`, `totals_by_part`, `ghost_resolutions`, `phantom_depth_warnings` shape from `bom-explosion.md`.

## Idempotent ensure operations (rattle-apply-config + builder grammar)

`rattle-apply-config` covers the configurator `ensure_*` set. The three BOM-tier operations live in the **builder agent** contract (`agents/rattle-config-builder.md` § "Document- and BOM-tier operations"):

| Operation | Idempotency key | REST endpoints used |
|---|---|---|
| `ensure_part` | `(company_id, part_number)` | `GET /parts?search=…` → POST/PATCH `/parts` |
| `ensure_part_placement` | `(part_id, area_id)` | `GET /parts/{id}/placements` → POST `/parts/{id}/placements` or PATCH `/parts/placements/{placement_id}` |
| `ensure_bom_item` | `(parent_part_id, child_part_id, alt_group, effective_from, effective_to)` | `GET /parts/{id}/bom` → POST `/parts/{id}/bom` or PATCH `/parts/bom/{bom_id}` |

These wrap the underlying REST endpoints (matching by name → create-or-PATCH). Always prefer them over raw POST/PUT for idempotent re-runs.

## Validation errors

The Pydantic schemas in `app/schemas/v1/part.py` enforce:

- `quantity > 0` and ≤ 1e9. **A POST with `quantity: 0` returns 422.** When you want a line whose only contribution comes from `option_scalings` (additive ratio or absolute range), still set `quantity: 1` (the validator script also flags `quantity ≤ 0` as ERR).
- `scrap_percent` in `[0, 100]`.
- `uom` length ≤ 16.
- `alt_group` length ≤ 50.
- `note` length ≤ 1000.
- `usage_subclauses` and `option_scalings` JSON fields ≤ a configured size limit.
- `extra="forbid"` on every request schema — unknown fields (including `part_group_id`, `is_purchased`, `lifecycle_state`, `tags`, `uom` on Part) return 422.

Validation errors return RFC 9457 problem details with `status: 422` and a `type` of `/problems/validation`.
