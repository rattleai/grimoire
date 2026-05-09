---
name: rattle-document-templates
description: Use this skill when the user is building, auditing, or restructuring an offer/quote/custom document template in Rattle's documents system. Knows the doc_type contract — backend registers exactly five doc_types (offer, quote, technical_doc, ccms, custom; legacy plurals offers/quotes also accepted; technical_documentation is a read-only legacy alias for technical_doc) — the offer requires a 'dynamic:document_configuration' attachment, the quote requires a 'dynamic:document_line_items' attachment, the structure-block tree (chapters → sections → attachments → content blocks), how to reuse system dynamic blocks instead of wrapping them, and how to fetch the live doc_type contract via GET /documents/doc-types. Pair with rattle-configurator (rules), rattle-api (REST writes), and rattle-techdoc (separate skill for the doc_type=technical_doc 15-chapter scaffold).
license: MIT
---

# Rattle document templates

Document templates produce offer PDFs, quotes, ccms outputs, and other rendered documents. The documents system replaces the deprecated offer-sections. Every offer template MUST attach the system dynamic content block `dynamic:document_configuration`; every quote template MUST attach `dynamic:document_line_items` — without these, the live configuration / line items are missing from the rendered output.

> **Backend doc_type registry.** `app/services/document_types.py` registers exactly five canonical doc_types: `offer`, `quote`, `technical_doc`, `ccms`, `custom` (plus the legacy plurals `offers`/`quotes` and the read-only legacy alias `technical_documentation` accepted on GET filters but rejected on POST). **The string `datasheet` is NOT a backend doc_type.** Datasheet-style assets ride on `doc_type=custom` (or `offer` if they ship with a configuration). For technical documentations / Betriebsanleitungen, use the dedicated `rattle-techdoc` skill instead — it covers the 15-chapter ISO 20607 / IEC 82079-1 scaffold.

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

2. **Discover system dynamic blocks.** `GET /documents/content-blocks?search=dynamic:` (the route does NOT honour `is_dynamic` as a query param — supported filters are `cursor`, `limit`, `product_id`, `directory_id`, `tag`, `search`, `is_active`; paginate the result and inspect each block's `is_dynamic` field client-side). Every dynamic block in the `default_layout` (pricing, configuration, company_contacts, document_summary, document_line_items, document_agreements, …) is registered with a stable `key` like `dynamic:document_configuration`. Reference these by `id` in attachments — never wrap them in a new content block (`use-system-dynamic-blocks`).

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
    "Resolve the system dynamic block id by paginating GET /documents/content-blocks?search=dynamic:document_configuration and matching the response's is_dynamic=true && key=dynamic:document_configuration entry (the route does not honour ?is_dynamic= as a filter — search + client-side filter is the supported pattern)."
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
