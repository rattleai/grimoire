# Grimoire Roadmap

Forward-looking backlog of skills, agents, and slash commands needed to make the Grimoire bundle a complete expert across the full Rattle value chain. Drafted from the PR #14 gap audit (2026-05-09).

> **Status conventions.** P0 = value chain is broken without it. P1 = significant gap that blocks production for a class of tenant. P2 = nice-to-have / quality-of-life. **Not yet greenlit.** Each item below is a proposal, not a commitment — review and approve per PR.

---

## Today's coverage (after PR #14)

The bundle currently ships expert depth in three domains:

- **Variant BOM** — `rattle-bom-builder` + `rattle-bom-architect` cover usage_subclauses, option_scalings (legacy / ratio / range), numbered-option scaling, alt_group, ghost depth-transparency, BOM explosion semantics.
- **Technical documentation** — `rattle-techdoc` + `rattle-techdoc-author` + `rattle-techdoc-auditor`, plus the safety-notice / GHS / language sister skills, cover the 15-chapter ISO 20607 scaffold, ISO 7010 + CLP pictograms, IEC/IEEE 82079-1 Clause 5 quality attributes, MVO Article 10(7) digital provision.
- **Configurator (basics)** — `rattle-configurator` + `rattle-suggest-config` + `rattle-pricelist-analysis` + `rattle-apply-config` + `rattle-audit` cover the #1 rule, anti-patterns, structural checks.

The bundle is **solid but thin** in: shared groups, area option-overrides, multi-select groups, offer-template authoring (offer-only — quote / ccms / custom are undocumented).

The bundle has **significant gaps** in: numbered options on the sales/UX side, quote / ccms / custom doc_types, pricing strategy, CRM/quote lifecycle, i18n governance, constraint authoring, document block-conditions, onboarding, webhooks/connectors, change management.

---

## P0 — Block PR / unblock the value chain

### P0-1. `rattle-numbered-options` skill *(sales-side counterpart to BOM scaling)*

**Scope.** When and how to model a configurable feature as a numbered option (`is_numbered: true`) vs N discrete options vs a multi-select group. Covers the configurator-stage fields the BOM skill consumes: `number_min`, `number_max`, `number_step`, `number_unit`, `price_scalings`. Decision rules: discrete vs numeric, single vs multi, when `is_numbered + is_multi` makes sense.

**Why a new skill.** The current `rattle-suggest-config` recommendation-output schema has no fields for `is_numbered` / `number_min/max/step/unit` / `price_scalings`, so an AI agent can't even *propose* a numbered option — the user has to author it by hand and then dispatch to `rattle-bom-architect` post-hoc. This is the single largest gap on the sales/configurator side.

**Includes.**
- Skill body: when to choose numeric vs discrete, validation bounds, UX implications, interaction with constraints (a numbered option cannot be a member of a forbidden-pair).
- Reference `references/numbered-pricing.md`: `price_scalings` (same descriptor shapes as `option_scalings` — legacy, ratio, range — but for price). Multi-currency considerations.
- Schema patch for `rattle-suggest-config` recommendation contract to expose the new fields.
- Pricelist anti-pattern: "per-meter pricing as a separate row" → should become a numbered option. Heuristic for `rattle-pricelist-analysis` to detect this.
- Examples: panel count, run length, surface area, opening count, custom-cut linear-foot pricing, weight-based shipping cost.

**Priority.** P0 — without it the configurator tier cannot recommend a numbered option, breaking the most common BOM-scaling use case end-to-end.

### P0-2. `rattle-document-templates` restructure → split per doc_type

**Scope.** The skill today documents only the **offer** flow and names a phantom `datasheet` doc_type that does not exist in the backend registry. The real backend doc_types are `offer`, `quote`, `technical_doc`, `ccms`, `custom` (per `app/services/document_types.py`); each has a different `default_layout` (`quote` requires `dynamic:document_line_items`; `offer` requires `dynamic:document_configuration`; `ccms` / `custom` are open-ended) and different `requires_quote` / `requires_configuration` flags.

**Why now.** Sales operations cannot author a quote template using the current skill. `rattle-build-offer` is a slash command — there is no `/rattle-build-quote` or `/rattle-build-ccms`.

**Approach (pick one).**
1. **Restructure in place.** Rename `rattle-document-templates` → `rattle-documents`, split body into per-doc-type sections, add references for each doc_type's `default_layout`, dynamic-block contracts, and worked example. Add `/rattle-build-quote` slash command.
2. **Split into separate skills.** `rattle-offer-templates`, `rattle-quote-templates`, `rattle-custom-templates`. Higher discoverability; more files for the user to maintain.

**Includes.**
- Real backend doc_type registry walk (kill the phantom `datasheet`).
- Per-doc-type `default_layout` table.
- Cross-doc-type EditorJS block compatibility note (`safety_notice` and `hp_statement` work in offer / quote templates too — currently undocumented).
- Block conditions (`condition_json`) for per-option attachment visibility — overlaps with P1-5.

**Priority.** P0 — quote authoring is a shipping product feature with zero skill coverage today.

---

## P1 — Significant gaps; production-ready needs them

### P1-1. `rattle-pricing-strategy` skill

**Scope.** `PriceList`, `PriceListVersion`, `PricingAdjustmentPreset`, area / option / product price-overrides, currency handling, volume-discount tiers, customer-specific pricing, version pinning per quote.

**Why a new skill.** Pricing crosses configurator + offer + quote; no existing skill owns it. `rattle-configurator` strains scope already.

**Includes.** Decision tree for "where does this discount belong?" (option vs price-list vs quote-time adjustment). Audit rule: detect price-list drift across product variants.

### P1-2. `rattle-crm-quotes` skill (and optional `rattle-quote-author` agent)

**Scope.** `Customer`, `CustomerLink`, `CustomerContactPerson`, `Opportunity`, `Quote`, `QuoteVersion`, `primary_quote_id`. The lifecycle: configuration → quote → published offer → accepted → ordered.

**Why.** The entire CRM/quote layer is invisible to all 6 current agents. Tenants who use Rattle as their quote engine (not just the configurator) get no guidance.

### P1-3. `rattle-i18n` skill

**Scope.** `TranslationDictionaryEntry` (glossary lock — terms that must never be AI-translated), `TranslationText` (per-entity translation cache), translation-memory pattern, segment-lock heuristics, AI-translate-vs-resolve-vs-glossary fallback chain. Per-customer language for offers (`Configuration.offer_language`).

**Why.** A locked term ("Spindel" not "Spindle") in a brand glossary needs the dictionary; the current `rattle-techdoc-language` skill mentions translation policy generally but does not document the dictionary or the fallback chain. Multilingual offer rendering has zero coverage.

### P1-4. `rattle-constraint-authoring` skill

**Scope.** Natural-language → pair-constraint + rule_json conversion. Constraint solver mental model. Edge cases: n-way XOR, conditional cross-group exclusions, constraints involving numbered options. Validation against existing options. Refactoring overlapping pair constraints into a single rule.

**Why.** Constraints are the most common thing tenants get wrong. `rattle-suggest-config` can propose `forbidden_pair`s but neither it nor `rattle-consultant` walks the user through the conversion of a natural-language exclusion spec into the right combination of pairs vs rules.

**Optional companion agent.** `rattle-constraint-author` for batch authoring against an existing tenant.

### P1-5. `rattle-block-conditions` skill

**Scope.** `document_block_conditions` — per-option attachment visibility, per-area chapter visibility, condition_json grammar. "Show this attachment only when option X is selected" / "hide chapter 9 when this is a service variant".

**Why.** Backend feature exists (`tests/test_document_block_conditions.py` confirms). Cross-cuts offer + techdoc + ccms. Zero skill coverage today.

### P1-6. `rattle-onboarding` skill (and `rattle-onboarder` agent)

**Scope.** First-time tenant setup: load areas template library, set offer language, register first product, create first configuration, run baseline audit, populate `memory/<tenant>/profile.md`. Bootstraps the workflow that every other agent assumes already happened.

**Why.** Highest-value AI-assisted workflow for a new customer. Backend has `Company.onboarding_completed` field; no skill walks the bootstrap.

---

## P2 — Nice-to-have / quality-of-life

### P2-1. `rattle-bom-builder` references — promote `alt_group` and `ghost-parts`

**Scope.** Today both are covered in SKILL.md sections. Promote each to a dedicated reference (`references/alt-group.md`, `references/ghost-parts.md`) the way `numbered-options.md` is structured. Worked examples: make-or-buy alt_group, region-specific alt_group, alt_group + numbered-option-driven tier selection, 3-level ghost expansion.

### P2-2. `rattle-spare-parts` skill

**Scope.** Spare-parts catalogue (distinct from manufacturing BOM — published list with images, order numbers, replacement intervals). Maps to `Part` + `BomItem` but with a different "explosion view" — flatten to user-replaceable level. Output: customer-facing spare-parts PDF / web list.

### P2-3. `rattle-change-management` skill

**Scope.** `ChangeRequest`, `ChangeOrder`, `ItemRevision`, `Branch`, `PullRequest`, `Baseline`. Git-like revision-control for parts/BOM. Critical for regulated/aerospace/medical tenants; invisible to all 6 current agents.

### P2-4. `rattle-webhooks-and-connectors` skill

**Scope.** `WebhookSubscription`, `WebhookDelivery`, `CompanyConnectorSettings`, the `connectors/` package. ERP integration patterns, retry semantics, signature verification, dead-letter handling.

### P2-5. `rattle-pdf-rendering` skill

**Scope.** `pdf_orchestrator.py` integration. Page-break rules. ToC generation. Header/footer customisation. Watermarks. Print-vs-screen layouts.

### P2-6. `rattle-cad-assets` skill

**Scope.** `PartDocument` + `PartDocumentLink`. Supported CAD formats. Where assets surface in offers / techdocs (cover image, exploded view, 3D viewer embed). STEP / DWG / DXF handling.

---

## Recommended consolidations (don't grow the bundle for its own sake)

- **`rattle-pricelist-analysis` + `rattle-suggest-config`** could be merged. The boundary is artificial; the workflows are sequential; activating the suggest-config skill always activates pricelist-analysis anyway. Reduces context load on AI clients.
- **`rattle-document-templates`** should be either restructured per-doc-type (P0-2) or split. Status-quo overstates coverage.

---

## Tracking

Each P0 / P1 / P2 item should land as its own PR with:
- New skill folder under `skills/` (with `SKILL.md` frontmatter, references, scripts).
- Optional agent under `agents/`.
- Optional slash command under `commands/`.
- Plugin manifest update (`.claude-plugin/plugin.json` + `marketplace.json`).
- AGENTS.md / CLAUDE.md table entry.
- Cross-references from / to related skills.

The audits in PR #14 found the bundle is "an expert in 3 domains, solid in 4, missing in 7". Closing P0+P1 takes the bundle to "expert in 6 domains, solid in 8, missing in 3". Closing P2 puts it at "expert in 12+ domains" — a plausible end state for the next 6–9 months of grimoire development.
