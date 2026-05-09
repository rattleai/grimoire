# Rattle data model — full reference

Source of truth for every entity, its key fields, primary endpoint, and relationships. Mirror of `rattle_api.knowledge.RATTLE_DATA_MODEL` and the live OpenAPI spec at `https://www.rattleapp.de/docs/api/interactive`.

## Hierarchy at a glance

```
Product
  ├── Areas                      (configurable sections — assigned via /products/{id}/areas)
  │   └── Groups                 (linked to areas via /groups/{id}/areas, is_multi)
  │       └── Options            (name, price, key, recommended; per-area overrides via option-area-config)
  ├── Parts                      (physical components)
  │   └── BOM items              (parent→child, quantity, usage_subclauses → options)
  ├── Constraints                (pair-level + conditional rule_json)
  └── Documents                  (replaces deprecated offer-sections)
      └── Document templates     (doc_type=offer/quote/technical_doc/ccms/custom)
          └── Structure blocks   (chapter / section / container / repeater / placeholder)
              └── Attachments
                  └── Content blocks  (static EditorJS or system-dynamic like 'dynamic:document_configuration')
```

---

## Product

Top-level entity representing a configurable product (machine, furniture piece, vehicle).

- **Endpoint**: `/products`
- **Key fields**: `id`, `name`, `description`, `base_price`, `currency`, `is_active`
- **Relationships**: `areas` (assigned via `/products/{id}/areas`), `parts`, `constraints`

---

## Area

A configurable section of a product. Areas are assigned to products and groups are linked to areas. Rich-text content (EditorJS blocks) is managed via `/areas/{id}/content`. Multiple areas per product (e.g. different configurable zones).

- **Endpoint**: `/areas`
- **Key fields**: `id`, `name`, `description`, `price`, `language`, `allow_disable`
- **Relationships**: `product`, `groups`
- **Rule**: every area must contain at least one group (see `no-empty-areas`).

---

## Group

Configuration group collecting related options (e.g. "Wheels", "Frässpindel", "Auftragsverwaltung IoT"). Groups are linked to areas (not directly to products) via `/groups/{id}/areas`. The `is_multi` field controls whether the user can select one option (single-select) or multiple (multi-select).

- **Endpoint**: `/groups`
- **Key fields**: `id`, `name`, `description`, `key`, `is_multi`, `area_ids`
- **Relationships**: `areas`, `options`
- **Reuse**: prefer one library group linked to many areas across products via `POST /groups/{id}/areas` rather than duplicating per product.

---

## Option

A single selectable choice within a group (e.g. "17 inch wheels", "19 inch wheels", "ohne", "mit"). Every variant — including the default/standard — must be an explicit option. The `recommended` flag marks the pre-selected default.

- **Endpoint**: `/options`
- **Key fields**: `id`, `name`, `description`, `price`, `key`, `recommended`, `group_id`
- **Relationships**: `group`
- **Per-area overrides**: `/options/{id}/area-config?area_id=X` overrides price, key, description, recommended flag — used to reuse one option across areas with per-area pricing instead of duplicating.

---

## Part

A physical component, sub-assembly, or finished good that can appear in a product's bill of materials.

- **Endpoint**: `/parts`
- **Key fields**: `id`, `part_number`, `part_name`, `part_cost`, `part_type`, `status`
- **Relationships**: `bom_items`, `placements`

---

## BOM item (`/parts/{id}/bom`)

A parent→child relationship in the hierarchical BOM. Each BOM item links a parent part to a child part with a quantity. The `usage_subclauses` array conditionally includes this BOM line based on selected options: each entry is `{"option_id": <id>, "factor": <multiplier>}`. When the referenced option is selected, this BOM line is active with `quantity × factor`. **This is the core mechanism that makes configuration drive the bill of materials.**

- **Endpoint**: `/parts/{id}/bom`
- **Key fields**: `id`, `parent_part_id`, `child_part_id`, `quantity`, `uom`, `usage_subclauses`, `option_scalings`
- **Relationships**: `parent_part`, `child_part`, options (via `usage_subclauses`)

Example (synthetic ids):
```json
{
  "parent_part_id": 100,
  "child_part_id": 250,
  "quantity": 4,
  "uom": "pcs",
  "usage_subclauses": [{"option_id": 301, "factor": 1.0}]
}
```
→ When option 301 ("19 inch wheels") is selected, include 4 × 1.0 = 4 of part 250 (the 19-inch wheel assy).

---

## Constraint

Forbidden option combinations. Two mechanisms.

### Pair-level

- **Endpoint**: `POST /constraints`
- **Behaviour**: ATOMICALLY REPLACES ALL pairs for the product in one call. Use the `X-Constraints-Version` header for optimistic concurrency (read the version on the prior `GET /constraints?product_id=…`, echo it back, retry once on **409 Conflict**).
- **Body shape**: `{"product_id": <id>, "forbidden": [{"option_id1": <a>, "option_id2": <b>}, ...]}`. The body field is `forbidden` (`ReplaceOptionConstraintsRequest.forbidden`); sending `pairs` returns 422.
- **Check (read-only)**: `POST /constraints/check {"product_id", "option_id1", "option_id2"}`.
- **Area-pair sibling**: `POST /constraints/area` with `X-Areas-Version` and body `{"product_id": <id>, "forbidden": [{"area_id1", "area_id2"}, ...]}`. `AreaForbiddenCombination.product_id` is required for new writes (allowed nullable on the model only for legacy migration); the constraint engine cannot evaluate area pairs without it.

### Rule-level

- **Endpoint**: `POST /constraints/rules`, `PATCH /constraints/rules/{id}`, `DELETE /constraints/rules/{id}`.
- **Shape**: `rule_json` is a single object `{"requires": [<clause>...], "invalid": [<option_id>...]}` — NOT an array, and NOT the legacy `{if, then}` shape some old OpenAPI examples show. Each clause uses `anyOf` (any of the listed option ids), `allOf` (all listed option ids), or `groupSelections` (map of stringified group_id → list of allowed option ids). Clauses are AND-folded by `app/utils/constraint_solver._rule_active`; ALL must be satisfied for the rule to fire. `invalid` is the set of option ids forbidden when `requires` is satisfied. The runtime evaluator is `app/models.py` `ForbiddenRule.violates`.
- **Scope**: `product_id` (required on create) and optionally `area_id`. `product_id` is immutable on update.

---

## Option area-config (`/options/{id}/area-config`)

Per-area override for an option. The same option (same id, same group) shows different attributes in different areas — the **primary tool for avoiding duplicated groups**.

- **Endpoint family**: `GET / PUT / DELETE /options/{option_id}/area-config?area_id=<area_id>` — the `?area_id=` query param is **required** on every method (missing returns 400).
- **9 REST-overridable fields** (the `OVERRIDE_FIELDS` set on `OptionAreaConfig`): `price`, `option_key`, `option_description`, `recommended`, `is_numbered`, `number_min`, `number_max`, `number_step`, `number_unit`. The field name is `option_description` (NOT `description` — `AreaConfigUpdateRequest` has `extra="forbid"`). The model also supports overriding `image` and `price_scalings`, but those are intentionally NOT exposed via the area-config REST endpoint (set them via the dedicated image-upload route and the option's own `price_scalings` field).
- **Clear semantics**: `DELETE /options/{id}/area-config?area_id=<a>&field=<field_name>` clears one specific override (must be in `OVERRIDE_FIELDS`); omit `?field=` to clear every override and remove the row.
- **NULL = inherit**: every override field is nullable on the model; NULL means "inherit from base Option". Sending `null` on a PUT is a no-op (use DELETE to clear).

When an option's price (or `recommended` flag, numbered-option bounds, description) varies by product tier or area, keep a single option and set per-area overrides via `PUT /options/{id}/area-config?area_id=…` — do **not** duplicate the option per tier.

---

## Documents system

The documents system replaces the deprecated offer-sections. It is the canonical home for product narrative and offer rendering.

### Document template (`/documents/templates`)

A reusable template that defines the structure of a document. The 5 canonical `doc_type` values are `offer`, `quote`, `technical_doc`, `ccms`, `custom` (legacy plurals `offers`/`quotes` accepted on writes; `technical_documentation` is a read-only legacy alias for `technical_doc`). Each template has an optional `product_id` binding, a tree of structure blocks, and an `is_published` / `status` lifecycle. `inheritance_mode` is one of `standalone | link | extend | fork` (default `standalone`). The string `datasheet` is NOT a registered doc_type; datasheet-style assets ride on `custom`.

- **Endpoint**: `/documents/templates`
- **Key fields**: `id`, `doc_type`, `name`, `product_id`, `is_published`, `status`, `inheritance_mode`
- **Assignment**: `/documents/templates/{id}/assign-products`
- **Critical contract**: the `offer` doc_type has `requires_configuration=true`. Its structure MUST contain an attachment referencing the system dynamic content block `dynamic:document_configuration`. Without it, an offer cannot be published.

### Document content block (`/documents/content-blocks`)

A reusable content unit referenced by document templates. Each content block has one or more locales; each locale holds **either** an EditorJS `blocks` array (static content) **or** a `template_name` string (dynamic content resolved at render time — the two fields are mutually exclusive). System-provided dynamic blocks have `is_dynamic=true` and a well-known key like `dynamic:document_configuration`.

- **Endpoint**: `/documents/content-blocks`
- **Key fields**: `id`, `key`, `title`, `is_dynamic`, `locales`, `tags`, `product_id`
- **Discover system blocks**: paginate `GET /documents/content-blocks?search=dynamic:` and filter on `is_dynamic=true && key='dynamic:<name>'` client-side. The route does NOT honour `?is_dynamic=` as a query param — `is_dynamic` is a COMPUTED field (membership in `DYNAMIC_BLOCK_KEYS`), not a stored column. Do NOT send `is_dynamic=true` on POST — use the canonical key (e.g. `dynamic:document_configuration`) instead.
- **Rule**: NEVER wrap a system dynamic block in a new content block — attach it by id (see `use-system-dynamic-blocks`).

### Document structure block (`/documents/templates/{id}/structure/blocks`)

A node in a document template's structure tree.

- `node_type` ∈ `chapter`, `section`, `container`, `repeater`, `placeholder`
- Chapters are top-level sections; sections nest inside chapters; placeholders are empty slots filled by attachments.
- Slugs must be unique per template.
- Content blocks are connected via attachments, not directly.

### Document attachment

Links a content block to a structure block in a document template. Multiple attachments per structure block are allowed (`order_index` controls order). `is_required=true` marks an attachment that must resolve for the document to publish — used for dynamic blocks like `dynamic:document_configuration` that the offer doc_type requires.

- **Endpoint**: `/documents/templates/{id}/structure/blocks/{block_id}/attachments`
- **Key fields**: `id`, `structure_id`, `content_block_id`, `order_index`, `is_active`, `is_required`

### Doc type layout (`/documents/doc-types`)

Machine-readable contract for a document type. `GET /documents/doc-types` returns each registered doc_type with a `default_layout` (list of `{slug, title, dynamic_key}`) and boolean flags like `requires_configuration` and `requires_quote`. **Consulting workflows should read this at runtime** and use it as the source of truth for which dynamic blocks a template must contain.

- **Endpoint**: `/documents/doc-types`
- **Key fields**: `key`, `label`, `default_layout`, `requires_configuration`, `requires_quote`, `supported_formats`

---

## API conventions

- **Base URL**: `https://www.rattleapp.de/api/v1` (override via `RATTLE_BASE_URL`)
- **Auth**: `Authorization: Bearer rk_live_…`
- **Content-Type**: `application/json` (image uploads use `multipart/form-data`)
- **Pagination**: cursor-based — `cursor` (opaque), `limit` (default 25, max 100). Some endpoints are not paginated.
- **Errors**: RFC 9457 problem-details JSON; 422 includes a per-field `errors` array.

For full endpoint listings see `../../rattle-api/SKILL.md` and `docs/API_REFERENCE.md`.
