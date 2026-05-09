# API endpoints — variant-BOM operations

REST endpoints for parts, placements, and BomItems. All require `products:read` for GET and `products:write` for POST/PUT/PATCH/DELETE. Full reference: `rattle-api/references/api-reference.md`.

## Parts

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/parts` | List parts (with filters: `q`, `lifecycle_state`, `tag`) |
| POST | `/api/v1/parts` | Create a part |
| GET | `/api/v1/parts/{id}` | Get a part |
| PUT | `/api/v1/parts/{id}` | Replace a part |
| PATCH | `/api/v1/parts/{id}` | Partially update a part |
| DELETE | `/api/v1/parts/{id}` | Delete a part |
| GET | `/api/v1/parts/{id}/placements` | List placements of a part |
| POST | `/api/v1/parts/{id}/placements` | Create a placement |
| GET | `/api/v1/parts/{id}/bom` | List the parent's BOM children |
| POST | `/api/v1/parts/{id}/bom` | Create a BomItem |
| POST | `/api/v1/parts/{id}/bom/explode` | Explode the BOM (configuration-aware) |
| POST | `/api/v1/parts/import` | Bulk part import |
| POST | `/api/v1/parts/export` | Bulk part export |

## Part placements

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/part-placements/{id}` | Get a placement |
| PUT | `/api/v1/part-placements/{id}` | Replace |
| PATCH | `/api/v1/part-placements/{id}` | Partial update |
| DELETE | `/api/v1/part-placements/{id}` | Delete |

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

Body (Update / Patch): same fields, all optional.

## BOM items (`bom-items`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/bom-items/{id}` | Get a bom item |
| PUT | `/api/v1/bom-items/{id}` | Replace |
| PATCH | `/api/v1/bom-items/{id}` | Partial update |
| DELETE | `/api/v1/bom-items/{id}` | Delete |

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

## Idempotent ensure operations (rattle-apply-config)

`rattle-apply-config` exposes seven operation types. The three relevant for variant-BOM authoring:

| Operation | Idempotency key |
|---|---|
| `ensure_part` | `(company_id, part_number)` |
| `ensure_part_placement` | `(part_id, area_id)` |
| `ensure_bom_item` | `(parent_part_id, child_part_id, alt_group, effective_from, effective_to)` |

These wrap the underlying REST endpoints. Always prefer them over raw POST/PUT for idempotent re-runs. See `rattle-apply-config/SKILL.md` for the operation contracts.

## Bulk import / export

`POST /api/v1/parts/import` accepts a JSON document with parts + placements + bom items in one payload. Useful for:

- Mass authoring from a spreadsheet upload.
- Cloning a known-good variant BOM into a new product.
- Migration / restore from a backup snapshot.

Shape excerpt:

```json
{
  "parts": [
    {
      "part_number": "AX-55",
      "part_name": "Axis assembly",
      "part_cost": 1950,
      "placements": [
        {
          "area_id": 42,
          "quantity": 1.0,
          "usage_subclauses": [],
          "option_scalings": {}
        }
      ],
      "bom_items": [
        {
          "child_part_number": "BR-12",
          "quantity": 0,
          "option_scalings": {"119": {"opt": 4, "part": 1}}
        }
      ]
    }
  ]
}
```

## Validation errors

The Pydantic schemas in `app/schemas/v1/part.py` enforce:

- `quantity > 0` (≤ 1e9).
- `scrap_percent` in `[0, 100]`.
- `uom` length ≤ 16.
- `alt_group` length ≤ 50.
- `note` length ≤ 1000.
- `usage_subclauses` and `option_scalings` JSON fields ≤ a configured size limit.

Validation errors return RFC 9457 problem details with `status: 422`.
