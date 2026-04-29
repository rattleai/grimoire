---
name: rattle-document-templates
description: Use this skill when the user is building, auditing, or restructuring an offer/quote/datasheet document template in Rattle's documents system. Knows the doc_type contract (offer requires a 'dynamic:document_configuration' attachment), the structure-block tree (chapters → sections → attachments → content blocks), how to reuse system dynamic blocks instead of wrapping them, and how to fetch the live doc_type contract via GET /documents/doc-types. Pair with rattle-configurator (rules) and rattle-api (REST writes).
license: MIT
---

# Rattle document templates

Document templates produce offer PDFs, datasheets, quotes, and other rendered documents. The documents system replaces the deprecated offer-sections. Every offer template MUST attach the system dynamic content block `dynamic:document_configuration` — without it, the live product configuration is missing from the rendered offer.

## When to use this skill

- The user is building an offer, datasheet, or quote template for a product.
- The user has a "Description" or "Overview" area in the configurator and wants to migrate the narrative into a proper document template (`description-area-smell` correction).
- The user is auditing existing offer templates for the missing-configuration anti-pattern (`offer-template-missing-configuration`).
- The user wants to add a new chapter, attach a new content block, or reorganise the structure tree.

## Workflow

1. **Read the doc_type contract.** Always start with `GET /documents/doc-types`. Find the entry for the target doc_type (usually `offer`). It returns:
   - `key` (e.g. `offer`)
   - `default_layout`: list of `{slug, title, dynamic_key}` defining the canonical chapter shape.
   - `requires_configuration` (bool): the offer doc_type has this `true` and so MUST include `dynamic:document_configuration`.
   - `requires_quote` (bool): some doc_types additionally require `dynamic:document_line_items`.

2. **Discover system dynamic blocks.** `GET /documents/content-blocks?is_dynamic=true`. Every dynamic block in the `default_layout` (pricing, configuration, company_contacts, document_summary, document_line_items, document_agreements, …) is registered here with a stable `key` like `dynamic:document_configuration`. Reference these by `id` in attachments — never wrap them in a new content block (`use-system-dynamic-blocks`).

3. **Plan the structure tree.** A minimum offer template:
   - Chapter 1: **Product Overview** (`node_type=chapter`, `slug=product-overview`)
     - Attachment: a static EditorJS content block carrying the narrative (intro, mechanics/sensors/electronics/software sub-sections, core-features table, hero image).
   - Chapter 2: **Configuration** (`node_type=chapter`, `slug=configuration`)
     - Attachment: the system `dynamic:document_configuration` block (`is_required=true`).
   - Optional further chapters per the `default_layout` (Pricing → `dynamic:document_line_items`, Agreements → `dynamic:document_agreements`, etc.).

4. **Static content blocks: prefer reusing.** If the tenant already has a "Product Overview" content block for the same product or a sibling product line, link it via `attachments.content_block_id` and update only the structure block. Static blocks are cheap to share — duplicating just to tweak one paragraph creates the same fragmentation problem as duplicating groups.

5. **Validate before publishing.** Before flipping `is_published=true`:
   - Every dynamic key listed in `default_layout` is present somewhere in the structure tree as an attachment.
   - All `is_required=true` attachments resolve to an existing content block (no dangling references).
   - Slugs are unique within the template.
   - No content block whose only locale wraps a `dynamic:*` template_name (`duplicate-dynamic-wrappers`).

6. **For audits.** Run the structural check `offer-template-missing-configuration` (see `rattle-configurator/references/structural-checks.md`). Fix any flagged template by adding a chapter with an attachment to the `dynamic:document_configuration` system block id.

## Output contract

```json
{
  "template_name": "Widget Pro — Offer",
  "doc_type": "offer",
  "product_id": null,
  "chapters": [
    {
      "slug": "product-overview",
      "title": "Product Overview",
      "order_index": 0,
      "attachments": [
        {
          "content_block_id": null,
          "content_block_proposal": {
            "title": "Widget Pro — Overview",
            "locale_de": {"editorjs_blocks": "..."}
          },
          "dynamic_key": null,
          "is_required": false
        }
      ]
    },
    {
      "slug": "configuration",
      "title": "Configuration",
      "order_index": 1,
      "attachments": [
        {
          "content_block_id": null,
          "dynamic_key": "dynamic:document_configuration",
          "is_required": true
        }
      ]
    }
  ],
  "notes": [
    "Use system dynamic block id from GET /documents/content-blocks?is_dynamic=true&key=dynamic:document_configuration"
  ]
}
```

The downstream builder resolves `dynamic_key` to a real `content_block_id` at execution time by looking it up in the system blocks list. Static content-block proposals (`content_block_proposal`) are created via `POST /documents/content-blocks` then attached.

## Common corrections this skill handles

| Symptom | Fix |
|---|---|
| `description-area-smell` (narrative-only configurator area) | Migrate the narrative into a static content block; create offer template with Product Overview + Configuration chapters. |
| `offer-template-missing-configuration` | Add a chapter with an attachment to system `dynamic:document_configuration`. |
| `duplicate-dynamic-wrappers` | Find every attachment pointing at the wrapper; rewrite to point at the system block id; delete the wrapper. |
| Per-product offer drift | Use shared static content blocks across product lines; let dynamic blocks render per-product variation automatically. |

## Related skills

- `rattle-configurator` — knowledge: rules, anti-patterns, structural checks.
- `rattle-api` — REST surface: `/documents/templates`, `/documents/content-blocks`, `/documents/doc-types`, structure-block sub-resources.
- `rattle-suggest-config` — sometimes runs alongside this skill when a customer's "Description" area is being migrated to documents.
