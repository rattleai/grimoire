---
name: rattle-techdoc
description: Use this skill whenever the user is building, auditing, restructuring, or translating a technical documentation (Betriebsanleitung / operating manual / instructions for use) on the Rattle SaaS platform. Activates for any "technical documentation", "Betriebsanleitung", "Bedienungsanleitung", "instructions for use", "user manual", "operating manual" task — and for any input of multiple product manuals that must be unified into modular, ready-to-ship documentation. Encodes the 15-chapter normative structure (DIN EN ISO 20607, IEC/IEEE 82079-1), the doc_type contract (`doc_type=technical_doc` — the legacy alias `technical_documentation` is accepted on GET filters but rejected on POST/PUT), the EditorJS block taxonomy (paragraph, list, table, warning, quote, delimiter, safety_notice, hp_statement, image, header), and the legal basis (Maschinenrichtlinie 2006/42/EG, Maschinenverordnung (EU) 2023/1230). Pair with rattle-safety-notices, rattle-ghs-statements, rattle-techdoc-language, rattle-document-templates, and rattle-api.
license: MIT
---

# Rattle technical documentation

You are advising on **technical documentation** for products configured in Rattle (rattleapp.de). Technical documentation in this context is the binding deliverable that travels with every physical product placed on the EU market: the operating manual (`Betriebsanleitung`), assembly instructions, maintenance manual, or full instructions for use. It is **legally mandatory** for every machine or other product covered by an applicable CE directive / regulation — primarily the Machinery Directive 2006/42/EC and (from 20 January 2027) the Machinery Regulation (EU) 2023/1230, plus where relevant the Low Voltage Directive 2014/35/EU, the EMC Directive 2014/30/EU, ATEX 2014/34/EU, the Pressure Equipment Directive 2014/68/EU, and the Radio Equipment Directive 2014/53/EU.

> **Out of scope.** Medical devices (MDR (EU) 2017/745, IVDR (EU) 2017/746) and *in vitro* diagnostics need a different scaffold (ISO 20417 + ISO 15223-1 + IEC 62366-1 usability engineering). The 15-chapter machinery scheme below is **not** an MDR-compliant IFU. Refuse the machinery scaffold for medical devices and flag the scope mismatch to the user — a future `rattle-techdoc-medical` skill will own that scope.

This skill encodes the consulting expertise needed to design and build a full Rattle `doc_type=technical_doc` template: the 15-chapter normative structure, the EditorJS block taxonomy, and the rules for splitting general vs. phase-specific safety, residual risks, conformity, and disposal.

> **doc_type canonical value.** The Pydantic create/update validator (`app/schemas/v1/document.py:81` `_validate_doc_type`, with `extra="forbid"`) accepts `{offer, quote, technical_doc, ccms, custom}` plus the legacy plurals (`offers`/`quotes`). The string `technical_documentation` is **rejected on POST/PUT** even though some seeded rows in the database still carry it (the seeder writes it directly via `app/utils/techdoc_seeder.py`). Always send `technical_doc` on writes; use either form on `GET ?doc_type=…` filters.

## When to use this skill

Activate this skill whenever the user:

- Says **"technical documentation"**, **"Betriebsanleitung"**, **"Bedienungsanleitung"**, **"Originalbetriebsanleitung"**, **"instructions for use"**, **"operating manual"**, **"user manual"**, **"IFU"**, **"Wartungsanleitung"**, **"Montageanleitung"**, **"Servicehandbuch"**.
- Provides one or many **existing product manuals** (PDF, Word, scanned) and asks to extract, modularise, harmonise, or rebuild them as a Rattle template.
- Asks how to satisfy normative requirements: **DIN EN ISO 20607**, **IEC/IEEE 82079-1**, **ISO 12100**, **MRL 2006/42/EG**, **MVO (EU) 2023/1230**, **ISO 3864-2**, **ISO 7010**, **ANSI Z535.6**, **CLP (EC) 1272/2008**.
- Asks to design **modular content blocks** that can be re-used across product variants (e.g. a single "Lockout/Tagout" block referenced from every machine).
- Asks for **safety chapter** structure, **residual risk** tables, **EC declaration of conformity**, **target group** matrix, **signal word legend**, **glossary**, or **index**.
- Asks how to add **safety notices**, **hazard pictograms** (ISO 7010), **GHS pictograms**, or **H&P statements** to a chapter.
- Wants to **translate** a technical documentation into another EU language while preserving normative wording.

If the request is purely about an offer/quote/datasheet, use `rattle-document-templates` instead. If it is about safety symbols only, pair with `rattle-safety-notices`. If it is about GHS / H&P codes, pair with `rattle-ghs-statements`. For language and tone questions, pair with `rattle-techdoc-language`. For REST API mechanics (auth, pagination, errors), pair with `rattle-api`.

## The #1 rule for technical documentation

> **Safety information lives in two places: a global Safety chapter (Chapter 2) AND a phase-specific Safety section (.1) at the start of every life-cycle chapter (4–11).** Never collapse the global safety into the phase-specific safety, and never leave a life-cycle chapter without its own `.1` safety section.

**Why?** ISO 20607 (5.5) and ISO 12100 (6.4.1) require that each life-cycle phase (transport, assembly, commissioning, operation, troubleshooting, maintenance, decommissioning) carry its **own** safety information that addresses the hazards specific to that phase. The global Chapter 2 covers cross-cutting rules (intended use, residual risks, PPE, personnel qualification, warning structure). Removing either side creates a legal gap and is the most common audit finding.

## The 15-chapter normative structure

Every Rattle `technical_doc` template follows this canonical chapter order. Chapter slugs match the seed data in `app/utils/techdoc_seed_data.py` of rattleapp and the live API `default_layout`. Chapters marked **OPT** are optional; everything else is **mandatory** for a CE-marked machine.

| # | Slug | Title (DE / EN) | Norm refs | Status |
|---|------|-----------------|-----------|--------|
| — | `ch-00-cover` | Deckblatt / Cover Page | ISO 20607 (5.1), IEC/IEEE 82079-1 (6.1) | required |
| — | `ch-00-toc` | Inhaltsverzeichnis / Table of Contents | IEC/IEEE 82079-1 | required |
| 1 | `ch-01-about-document` | Zu diesem Dokument / About This Document | IEC/IEEE 82079-1 (6.1, 6.2), ISO 20607 (5.2) | required |
| 2 | `ch-02-safety` | Sicherheit / Safety | ISO 20607 (5), ISO 12100 (6.4), MRL Anh. I 1.7.4.2 | required |
| 3 | `ch-03-product-description` | Produkt- und Systembeschreibung / Product and System Description | ISO 20607, IEC/IEEE 82079-1 | required |
| 4 | `ch-04-transport` | Transport, Anlieferung und Lagerung / Transport, Delivery and Storage | ISO 20607 (Tab. 1) | required |
| 5 | `ch-05-assembly` | Montage und Installation / Assembly and Installation | ISO 20607, IEC 60204-1 | required |
| 6 | `ch-06-commissioning` | Inbetriebnahme und Einstellungen / Commissioning and Settings | ISO 20607 | required |
| 7 | `ch-07-operation` | Bedienung und Betrieb / Operation | ISO 20607, IEC/IEEE 82079-1 | required |
| 8 | `ch-08-troubleshooting` | Störungen und Fehlerbehebung / Troubleshooting | ISO 20607 | required |
| 9 | `ch-09-maintenance` | Reinigung, Wartung, Inspektion und Reparatur / Cleaning, Maintenance, Inspection, Repair | ISO 20607, MRL Anh. I 1.6.1 | required |
| 10 | `ch-10-modifications` | Umbauten, Erweiterungen, Modernisierung / Modifications, Extensions, Modernisation | ISO 20607, MVO 2023/1230 Art. 18 | **OPT** |
| 11 | `ch-11-decommissioning` | Außerbetriebnahme, Demontage, Entsorgung / Decommissioning, Disassembly, Disposal | ISO 20607, ISO 12100 | required |
| 12 | `ch-12-conformity` | Konformität, Normen und rechtliche Hinweise / Conformity, Standards, Legal | ISO 20607, MRL Anh. I+II | required |
| 13 | `ch-13-appendix` | Anhang / Appendix | ISO 20607, IEC/IEEE 82079-1 | required |

Full chapter reference (all 100+ sections with mandatory content, suggested wording, norm references, EditorJS scaffolds) lives in `references/chapter-reference.md`. The reference is bilingual DE/EN and is the master template every audit must reconcile against.

## Rattle data model for technical documentation

```
DocumentTemplate (doc_type = "technical_doc")   ← canonical write value
  └── StructureBlock (chapter / section / sub-section)
       └── Locales (DE, EN, FR, …) — title only
       └── Attachments
            └── ContentBlock (master)
                 └── Locales (DE, EN, …)
                      └── EditorJS blocks (block_json)
                           ├── paragraph
                           ├── header
                           ├── list (unordered / ordered / checklist)
                           ├── table (withHeadings)
                           ├── warning (Editorial / Mandatory note)
                           ├── quote (suggested wording)
                           ├── delimiter
                           ├── image
                           ├── safety_notice  ← see rattle-safety-notices
                           └── hp_statement   ← see rattle-ghs-statements
```

Reuse is the central pattern: a **content block** is created once and **attached** to many structure blocks (across products, across templates). Examples of high-reuse blocks:

- `loto-procedure` — Lockout/Tagout protocol (referenced from every Maintenance chapter)
- `signal-words-legend` — Signal word legend (every "About This Document" chapter)
- `target-groups` — Target audience matrix (every "About This Document" chapter)
- `general-safety-rules` — Cross-cutting safety rules (every Safety chapter)
- `disposal-electronics` — WEEE-compliant electronic disposal (every Decommissioning chapter)

**Rule:** never duplicate a content block to tweak one paragraph. If a tenant already has a block for the same purpose, link it via `attachments.content_block_id`. Use **conditions** on the attachment (selected options / configuration variants) to vary inclusion, never duplication.

## Workflow — building a technical documentation from input manuals

This is the workflow you walk a user through when they hand you 1…N existing manuals and ask "build a Rattle technical documentation".

### Step 1 — Inventory the input

For every input file (PDF, Word, scan), extract:

1. **Identification**: product name, type, manufacturer, document number, issue date, language(s).
2. **Chapter map**: list every existing chapter heading and map it to the canonical slug from the 15-chapter structure. Flag anything that does not map (e.g. marketing chapter, sales pitch).
3. **Coverage matrix**: for each canonical chapter, mark `present / partial / missing`. The output is a coverage table per product × chapter.
4. **Reusability candidates**: text that is identical or near-identical across multiple input manuals (LOTO, general safety rules, target groups, signal word legend) → these are reusable content blocks.

A short Python helper for inventorying lives at `scripts/inventory_techdocs.py`. For PDF text extraction it uses `pypdfium2` or `pdfplumber`, or it can call any AI provider with the existing `analyse_data` task.

### Step 2 — Audit per the structural checks

Run every input manual against the audit checks in `references/audit-checks.md`. The 12 checks include:

- `missing-safety-chapter`
- `missing-phase-safety-section`
- `missing-residual-risks-table`
- `missing-signal-words-legend`
- `missing-target-groups-matrix`
- `missing-declaration-of-conformity`
- `missing-disposal-section`
- `unstructured-warnings` (warnings without DANGER/WARNING/CAUTION/NOTICE level)
- `non-normative-warning-words` (e.g. "Achtung!", "Wichtig!" without ISO 3864-2 level)
- `addressless-pictogram` (ISO 7010 symbol used without code reference)
- `unlabeled-original-language` (no statement of original-language version)
- `missing-validity-section` (no serial-number / software-version scope)

Each check has an `id`, `severity` (CRITICAL / HIGH / MEDIUM / LOW), `evidence` shape, and `correction` shape. Use the same JSON output contract as the configurator audit (`schemas/audit-findings.schema.json` is reused).

### Step 3 — Plan the modular content

Group the input content into three buckets:

1. **Reusable across all products** (`reusability=high`): generic chapters that don't depend on the product (signal word legend, LOTO, target groups, glossary stub, disposal-electronics). Build these once as content blocks at the **company** level (no `product_id`).
2. **Reusable across a product family** (`reusability=medium`): content that varies by product line but not by individual variant (typical safety overview for a class of machine). Tag with the product family.
3. **Product-specific** (`reusability=low`): content that is unique per SKU (technical data tables, configuration-specific commissioning steps). Bind with `product_id`.

Encode the plan as a JSON object that the next step (`build`) consumes:

```json
{
  "company_id": 42,
  "products": [
    {"id": 101, "name": "PFM-3200", "input_files": ["BA-PFM3200-DE.pdf"]},
    {"id": 102, "name": "PFM-3500", "input_files": ["BA-PFM3500-DE.pdf"]}
  ],
  "shared_blocks": [
    {"key": "loto-procedure", "title_de": "Lockout/Tagout-Verfahren", "reusability": "high",
     "attached_to_chapters": ["ch-09-maintenance"]},
    {"key": "signal-words-legend", "title_de": "Signalwörter und Symbole", "reusability": "high",
     "attached_to_chapters": ["ch-01-about-document"]}
  ],
  "products_blocks": [
    {"product_id": 101, "chapter_slug": "ch-03-product-description", "key": "pfm3200-tech-data",
     "reusability": "low"}
  ]
}
```

### Step 4 — Build the templates

For each product, create a `DocumentTemplate` (`doc_type=technical_doc`) and seed the canonical 15-chapter structure with `POST /documents/templates/{id}/structure/batch`. The seeded reference content (Editorial notes, suggested wording, mandatory-content callouts) for every chapter is available in `references/chapter-reference.md` as DE/EN EditorJS arrays — copy, do not invent.

The build sequence is:

1. `POST /documents/templates` with `doc_type=technical_doc`, `name`, `product_id`.
2. For each chapter in canonical order, `POST /documents/templates/{id}/structure/blocks` with `node_type=chapter`, `slug`, `order_index`, locale titles in DE+EN.
3. For each section under a chapter, `POST .../structure/blocks` with `node_type=section`, `parent_id`, `slug`, `order_index`, locale titles.
4. For each section's content, either:
   - **Reuse**: `POST .../attachments` with `content_block_id` of an existing block.
   - **Create**: `POST /documents/content-blocks` with the EditorJS block array, then attach it.
5. For dynamic content (configuration tables, line items, technical data fed from product attributes), use system dynamic blocks (`dynamic:document_configuration`, `dynamic:document_line_items`). Discover them via `GET /documents/content-blocks` (the route honours `cursor`, `limit`, `product_id`, `directory_id`, `tag`, `search`, `is_active` query params; **`is_dynamic` is not a server-side filter** — paginate the response and inspect each block's `is_dynamic` field client-side).
6. After every product is built, `POST /documents/templates/{id}/publish` (only after the audit checks for the template all pass).

For idempotent re-runs, use the document-tier `ensure_*` operations on the **`rattle-config-builder` agent** (not `rattle-apply-config`, which only ships the configurator-tier set). The builder grammar covers `ensure_template`, `ensure_chapter` / `ensure_structure_block`, `ensure_attachment`, `ensure_content_block` — each upsert-by-natural-key (template by `(company_id, name)`, structure block by `(template_id, slug, parent_id)`, content block by `(company_id, key)`). See `agents/rattle-config-builder.md` § "Document- and BOM-tier operations" for the full operation contract.

### Step 5 — Translate

Use `POST /documents/templates/{id}/translate` with `target_language=en` (or any of the 30+ supported locales — see `rattle-techdoc-language/references/locales.md`). The endpoint uses the configured AI provider plus DeepL if available. **Normative content (signal words, GHS H/P texts, declaration of conformity wording) is NOT translated by AI** — it is resolved from the official locale tables in `rattle-safety-notices/references/signal-words.md` and `rattle-ghs-statements/references/hp-statement-locales.md`. Always validate normative wording against those references after translation.

## Output contract — `techdoc-template.json`

When this skill produces a build plan (without yet calling the API), output:

```json
{
  "template_name": "PFM-3200 — Originalbetriebsanleitung",
  "doc_type": "technical_doc",
  "product_id": 101,
  "primary_locale": "de",
  "additional_locales": ["en"],
  "norm_refs": ["DIN EN ISO 20607:2019", "IEC/IEEE 82079-1:2019",
                "MRL 2006/42/EG", "MVO (EU) 2023/1230"],
  "chapters": [
    {
      "slug": "ch-00-cover",
      "title_de": "Deckblatt",
      "title_en": "Cover Page",
      "order_index": 0,
      "sections": [],
      "attachments": [
        {"content_block_proposal": {
            "key": "pfm3200-cover",
            "title_de": "Deckblatt PFM-3200",
            "reusability": "low",
            "locale_de": {"editorjs_blocks": [...]},
            "locale_en": {"editorjs_blocks": [...]}
        }}
      ]
    },
    {
      "slug": "ch-02-safety",
      "title_de": "Sicherheit",
      "title_en": "Safety",
      "order_index": 3,
      "sections": [
        {"slug": "sec-2-1-intended-use", "title_de": "Bestimmungsgemäße Verwendung",
         "title_en": "Intended Use", "order_index": 0,
         "attachments": [...]}
      ]
    }
  ],
  "shared_block_refs": [
    {"key": "loto-procedure", "attach_to": ["ch-09-maintenance.sec-9-1-loto"]}
  ],
  "audit_findings": [],
  "notes": []
}
```

## Common corrections this skill handles

| Symptom | Correction |
|---|---|
| User pasted a single "Sicherheit" chapter that mixes general + assembly + maintenance hazards | Split into Chapter 2 (cross-cutting) + a `.1 Safety` section under each life-cycle chapter (4–11). |
| Manual uses "Achtung!" without ISO 3864-2 signal word | Replace each warning with a `safety_notice` EditorJS block at the correct level (DANGER / WARNING / CAUTION / NOTICE). |
| Manual lists chemicals without H/P codes | Insert `hp_statement` EditorJS blocks; the skill `rattle-ghs-statements` resolves the official text + GHS pictogram. |
| 12 manuals all repeat the same 4-page LOTO description | Create one `loto-procedure` content block; attach to every Maintenance chapter via `content_block_id`. |
| Manual was written in German only — customer wants EN, FR, IT | Build DE first, then `POST /documents/templates/{id}/translate` for each target. Normative text is locale-resolved, not AI-translated. |
| Customer asks "what about Konformitätserklärung?" | Chapter 12 (`ch-12-conformity`) and Chapter 13 (`ch-13-appendix.sec-13-1-declaration`) — these are mandatory under MRL Annex II A. Section 13.1 holds the EC/EU Declaration. |
| Manual has no signal-word legend | `ch-01-about-document.sec-1-6-symbols` is mandatory per IEC/IEEE 82079-1:2019 §7.5 + §7.6 and ISO 3864-2:2016. Insert the four-row table (DANGER/WARNING/CAUTION/NOTICE) plus all ISO 7010 categories used. |

## Related skills and references

- `rattle-safety-notices/SKILL.md` — DIN ISO 7010 + ISO 3864-2 safety symbols, signal-word locales, EditorJS `safety_notice` block contract.
- `rattle-ghs-statements/SKILL.md` — CLP H/P/EUH codes, 9 GHS pictograms, EditorJS `hp_statement` block contract.
- `rattle-techdoc-language/SKILL.md` — language, tone, mood, terminology, original-language obligation, MVO 2023/1230 digital provision rules.
- `rattle-document-templates/SKILL.md` — offer/quote/datasheet templates (different doc_type contract).
- `rattle-api/SKILL.md` — REST API auth, pagination, error envelope; `references/api-reference.md` lists every documents endpoint.
- `references/chapter-reference.md` — all 15 chapters with EditorJS scaffolds (DE/EN), mandatory content callouts, norm references.
- `references/audit-checks.md` — 12 structural checks for technical documentations.
- `references/editorjs-blocks.md` — every EditorJS block type used in technical documentations with shape, validation, rendering notes.
- `references/legal-basis.md` — MRL/MVO/IEC/ISO standards, when each applies, what each requires.
- `scripts/inventory_techdocs.py` — extract chapter map and reusability candidates from input PDF/Word manuals.
