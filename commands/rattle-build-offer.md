---
description: Build or audit an offer/quote/custom document template for a Rattle product. Honours the doc_type contract (offer requires a 'dynamic:document_configuration' attachment; quote requires 'dynamic:document_line_items'), reuses system dynamic blocks instead of wrapping them, and produces the canonical chapter+attachment JSON. Backend doc_type registry: offer / quote / technical_doc / ccms / custom (datasheet rides on custom; technical documentations use the dedicated /rattle-build-techdoc command instead).
argument-hint: <tenant> <product-name> [--doc-type offer|quote|custom|ccms] [--language de|en]
---

# /rattle-build-offer

Propose a document template for the named product (`$ARGUMENTS`).

## Workflow

1. **Load context** — Read `skills/rattle-document-templates/SKILL.md` and `skills/rattle-configurator/references/structural-checks.md` (specifically `offer-template-missing-configuration` and `duplicate-dynamic-wrappers`).

2. **Read the runtime contract** — Always start with:
   ```
   GET /documents/doc-types
   ```
   Find the entry matching the requested `doc_type` (default `offer`). Note `requires_configuration`, `requires_quote`, and the `default_layout` chapter list.

3. **Discover system dynamic blocks** — The route does NOT honour `?is_dynamic=` as a query param. Use:
   ```
   GET /documents/content-blocks?search=dynamic:
   ```
   then paginate the response (cursor-based, `limit ≤ 100`) and filter on `is_dynamic=true && key=dynamic:<name>` client-side. Use the resolved `id` in attachments. NEVER wrap a system dynamic block in a new content block.

4. **Plan the structure tree** — Minimum offer template:
   - Chapter 1 "Product Overview" — static EditorJS content block (intro, mechanics/sensors/electronics/software, core-features table, hero image).
   - Chapter 2 "Configuration" — required attachment to `dynamic:document_configuration`.
   - Optional further chapters per `default_layout` (Pricing → `dynamic:document_line_items`, Agreements → `dynamic:document_agreements`, etc.).

5. **Reuse static content blocks** — If the tenant already has a "Product Overview" content block for the same product or a sibling product line, reference its `id` rather than proposing a new one. Static block reuse is cheap and prevents drift.

6. **Validate before publishing** — Walk the validation checklist in `skills/rattle-document-templates/SKILL.md` § Workflow step 5: every dynamic key in `default_layout` is present, all `is_required=true` attachments resolve, slugs are unique, no `duplicate-dynamic-wrappers`.

7. **Output the canonical JSON shape** — As documented in `skills/rattle-document-templates/SKILL.md` § Output contract.

8. **Hand off** — For writes, delegate to the `rattle-config-builder` agent. It will refuse to flip `is_published=true` until all required attachments resolve.

$ARGUMENTS
