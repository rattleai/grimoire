---
description: Build a Rattle technical documentation (`doc_type=technical_doc` — write canonical; legacy alias `technical_documentation` accepted on filters only) from one or many input product manuals. Walks the inventory → audit → plan → build → translate workflow. Honours the 15-chapter normative structure (DIN EN ISO 20607, IEC/IEEE 82079-1) and the safety-notice / GHS / language rules. Produces a modular, reusable, ready-to-ship template with shared and product-specific content blocks.
argument-hint: <tenant> <input-dir-or-product-list> [--language de|en] [--directive mrl|mvo|mdr] [--targets de,en,fr]
---

# /rattle-build-techdoc

Build a Rattle technical documentation for the inputs at `$ARGUMENTS`.

## Workflow

1. **Spawn the author agent.** Delegate to `rattle-techdoc-author`. It loads the host skill (`skills/rattle-techdoc/SKILL.md`) plus the safety-notices, GHS, language sister skills, plus the API reference.

2. **Inventory.** For input directories, run `python skills/rattle-techdoc/scripts/inventory_techdocs.py <input-dir>`. The output is a coverage matrix + reusability candidates JSON.

3. **Audit each input.** Walk the 14 structural checks in `skills/rattle-techdoc/references/audit-checks.md` against every input manual (12 numbered + 10b `default-fallback-symbol` + 10c `mismatched-ghs-pictogram`). Surface every CRITICAL (missing-safety-chapter, missing-phase-safety-section, missing-residual-risks-table, missing-declaration-of-conformity) and HIGH (missing-signal-words-legend, missing-target-groups-matrix, missing-validity-section, unstructured-warnings, missing-disposal-section, mismatched-ghs-pictogram) finding before proposing structure.

4. **Plan the modular content.** Group input content by reusability:
   - **Shared (reusability=high)** — LOTO, signal-word legend, target groups, general safety rules, disposal, glossary stub. Built once at company level (`product_id=null`).
   - **Family (reusability=medium)** — typical safety overview for a product line. Tagged with the family.
   - **Product-specific (reusability=low)** — technical data, configuration-specific commissioning, EC declaration. Bound with `product_id`.

5. **Build the templates.** For each product, produce the JSON payload for:
   - `POST /documents/templates` (with `doc_type=technical_doc`, `name`, `product_id`).
   - For each canonical chapter (`ch-00-cover` … `ch-13-appendix`): `POST /documents/templates/{id}/structure/blocks`.
   - For each section: child `POST .../structure/blocks` with `parent_id`.
   - For each content attachment: either `POST .../attachments` with an existing `content_block_id`, or `POST /documents/content-blocks` then attach.
   - Use `POST /documents/templates/{id}/structure/batch` for bulk operations.

6. **Translate.** For every additional locale in `--targets`, plan a `POST /documents/templates/{id}/translate target_language=<locale>` call. Flag the chapters that require human review post-translation (Chapter 2 Safety, 9.1 LOTO, 11 Disposal).

7. **Publish.** Only after every audit check passes for every locale: `POST /documents/templates/{id}/publish`.

## Validation gates

Before flipping `is_published=true`, the agent must confirm:

- **All 15 canonical chapters present** (14 mandatory, 1 optional — Chapter 10 `ch-10-modifications` is the only OPT chapter; everything else in the 15-chapter scaffold is required for a CE-marked machine per ISO 20607 / MRL Annex I §1.7.4.2).
- **All life-cycle chapters (4–11) have their `.1` safety section.**
- **Section `sec-2-4-residual-risks` contains a residual-hazards table.**
- **Section `sec-1-6-symbols` contains the four-row signal-word legend (DANGER / WARNING / CAUTION / NOTICE) plus every ISO 7010 category used.**
- **Section `sec-13-1-declaration` contains the EC/EU Declaration of Conformity (or attaches the dynamic block).**
- **Cover bears the original-language marker** ("Originalbetriebsanleitung" / "Translation of the original instructions").
- **Every `safety_notice` block** has all of `level / title / hazard / consequences[] / avoidance[] / isoSymbol`.
- **Every `hp_statement` block** has valid `codes[]` resolvable in the target locales.

## Output

The agent produces:

1. **`inventory.json`** — coverage matrix + reusability candidates per input.
2. **`audit-techdoc.json`** — findings per input + per chapter (uses `domain: "techdoc"`).
3. **`techdoc-plan.json`** — modular content plan: shared blocks, product-specific blocks, attachment graph.
4. **`techdoc-template.json`** — the canonical JSON output contract from `skills/rattle-techdoc/SKILL.md` "Output contract".
5. **`translate-plan.json`** — per-locale translation calls + chapters requiring human review.

## Hand-off

For writes, delegate to `rattle-config-builder` with the `techdoc-template.json` payload. The builder agent's contract (`agents/rattle-config-builder.md` § "Document- and BOM-tier operations") covers the document-tier operation grammar — `ensure_template` (keyed by `(company_id, name)`; the GET route does NOT accept `?search=`, so the builder paginates `?doc_type=&product_id=` and filters on `name` client-side), `ensure_structure_block` / `ensure_chapter` (keyed by `(template_id, slug)` — `parent_id` is NOT in the unique constraint), `ensure_content_block` (keyed by `(company_id, key)`), `ensure_attachment` (keyed by `(structure_block_id, content_block_id)`; carries the `conditions: list[dict]` field for per-option visibility — **not** `condition_json`), `ensure_block_locale` (structure-block locale URL takes the language as a string segment; content-block locale upsert posts `{language, blocks|template_name}` to the locale collection and returns an integer `locale_id`). Each is upsert-by-natural-key — a second run is a safe no-op.

$ARGUMENTS
