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
      └── Document templates     (doc_type=offer/datasheet/…)
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
- **Behaviour**: atomically replaces all pairs for a product. Use the `X-Constraints-Version` header for optimistic concurrency.
- **Shape**: each pair is `{option_id1, option_id2}` — selecting one forbids the other.
- **Check**: `POST /constraints/check {"product_id", "option_id1", "option_id2"}`.

### Rule-level

- **Endpoint**: `/constraints/rules`
- **Shape**: each rule has `rule_json: [{"if": {"option_selected": X}, "then": {"forbid_options": [Y, Z]}}]`.
- **Scope**: `product_id` and optionally `area_id`.

---

## Option area-config (`/options/{id}/area-config`)

Per-area override for an option's price, key, description, or `recommended` flag. Allows reusing the same group/option across areas while adjusting properties per area. **Primary tool for avoiding duplicated groups.**

- **Endpoint**: `/options/{id}/area-config?area_id=X`
- **Key fields**: `option_id`, `area_id`, `price`, `key`, `description`, `recommended`
- **Relationships**: `option`, `area`

When an option's price varies by product tier or area, keep a single option and set per-area prices via `PUT /options/{id}/area-config?area_id=…` — do **not** duplicate the option per tier.

---

## Documents system

The documents system replaces the deprecated offer-sections. It is the canonical home for product narrative and offer rendering.

### Document template (`/documents/templates`)

A reusable template that defines the structure of a document (offer, quote, datasheet, …). Each template has a `doc_type` (e.g. `offer`), an optional `product_id` binding, a tree of structure blocks, and an `is_published` / `status` lifecycle.

- **Endpoint**: `/documents/templates`
- **Key fields**: `id`, `doc_type`, `name`, `product_id`, `is_published`, `status`, `inheritance_mode`
- **Assignment**: `/documents/templates/{id}/assign-products`
- **Critical contract**: the `offer` doc_type has `requires_configuration=true`. Its structure MUST contain an attachment referencing the system dynamic content block `dynamic:document_configuration`. Without it, an offer cannot be published.

### Document content block (`/documents/content-blocks`)

A reusable content unit referenced by document templates. Each content block has one or more locales; each locale holds **either** an EditorJS `blocks` array (static content) **or** a `template_name` string (dynamic content resolved at render time — the two fields are mutually exclusive). System-provided dynamic blocks have `is_dynamic=true` and a well-known key like `dynamic:document_configuration`.

- **Endpoint**: `/documents/content-blocks`
- **Key fields**: `id`, `key`, `title`, `is_dynamic`, `locales`, `tags`, `product_id`
- **Discover system blocks**: `GET /documents/content-blocks?is_dynamic=true`
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
