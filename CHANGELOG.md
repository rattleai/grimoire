# Changelog — Rattle AI Workspace

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-05-09

### Added — variant-BOM expert layer

- **`skills/rattle-bom-builder/`** — absolute-expert skill for configurable variant-BOM definition. Documents every field, every DSL operator, and every scaling mode the runtime evaluator and BOM-explosion engine actually use. Includes 6 references:
  - `references/usage-subclauses.md` — full conditional-inclusion DSL (groupSelections, areaStatuses, areaSubclauses, AND/OR fold) with 9 worked examples.
  - `references/option-scalings.md` — three scaling descriptors (legacy numeric, ratio `{opt, part}`, range `{areas: [...]}`), additive vs. multiplicative resolution, area-scoped lookup, clamping, 12 worked examples.
  - `references/numbered-options.md` — 12 numbered-option scaling patterns (one-to-one, many-to-one, length-scaled, threshold-stepped, multi-option composition, area-scoped, …).
  - `references/bom-explosion.md` — runtime semantics: per-edge evaluation order, `alt_group` selection, ghost depth-transparency, aggregation.
  - `references/data-model.md` — every field of `Part` / `PartPlacement` / `BomItem` / `BomLineRev` / `Option` lifted from `app/models.py`.
  - `references/api-endpoints.md` — REST endpoints, idempotent ensure operations, bulk import / export, validation errors.
- `scripts/validate_variant_bom.py` — pre-flight validator for the `variant-bom.json` payload (clause well-formedness, scaling-descriptor shapes, range overlap detection, alt_group priority uniqueness, effective-date order, self-reference check).
- **`agents/rattle-bom-architect.md`** — senior variant-BOM architect subagent. Walks parts → placements → bom_items → validation; refuses to author around implicit baselines.
- **`commands/rattle-build-bom.md`** — `/rattle-build-bom` slash command with explicit validation gates before live application.

### Added — `ROADMAP.md`

Prioritised backlog (P0 / P1 / P2) of skills, agents, and slash commands needed to close the value-chain gaps the PR #14 audits identified:
- **P0** — `rattle-numbered-options` skill (sales-side counterpart to BOM scaling), `rattle-document-templates` restructure or split per doc_type (drop phantom `datasheet`).
- **P1** — `rattle-pricing-strategy`, `rattle-crm-quotes`, `rattle-i18n`, `rattle-constraint-authoring`, `rattle-block-conditions`, `rattle-onboarding`.
- **P2** — `rattle-bom-builder` references (alt_group / ghost-parts), `rattle-spare-parts`, `rattle-change-management`, `rattle-webhooks-and-connectors`, `rattle-pdf-rendering`, `rattle-cad-assets`.

### Changed — round-3 precision audit (production-grade correctness)

Three parallel audits (endpoint coverage, Pydantic + SQLAlchemy schema precision, untouched-skills + JSON-schemas) found CRITICAL issues that earlier rounds had not touched. All findings verified directly against rattleapp source before fixing.

**OCC error code corrected**: server returns `409 Conflict` for stale-version on `POST /constraints`, `POST /constraints/area`, `POST /price-lists/*` — **not** `412 Precondition Failed` (agents wired to retry on `412` previously never retried). Documented OCC headers expanded from one (`X-Constraints-Version`) to three (`X-Areas-Version`, `X-Price-Lists-Version`).

**JSON Schemas rewritten to match the live API**:
- `schemas/apply-operations.schema.json` — extended from 7 configurator-only ops to **15 ops across 3 tiers** (configurator + BOM + documents). Added `rule_clause`, `decimal_string`, `usage_subclauses`, `option_scalings` definitions.
- `schemas/recommendation.schema.json` — renamed `forbidden_pairs` → `forbidden`; added `is_numbered` / `number_min` / `number_max` / `number_step` / `number_unit` / `price_scalings` to options; added `option_scalings`, `alt_group`, `priority`, `scrap_percent`, `ghost_part`, `note`, `area_name` discriminator to bom_rules; added `area_overrides` for the 9 REST-overridable area-config fields; rewrote `constraint_rule` from legacy `[{if, then}]` to canonical `{requires, invalid}` (the runtime evaluator rejects the legacy shape).
- `schemas/audit-findings.schema.json` — split into `oneOf {configurator, techdoc}` so the techdoc auditor's 14 check_ids + CRITICAL/HIGH/MEDIUM/LOW ladder validate.
- `schemas/offer-template.schema.json` — `doc_type` enum now `{offer, quote, custom, ccms, offers, quotes}` (dropped phantom `datasheet`).

**Configurator-family fixes** (skills not touched in earlier rounds):
- `rule_json` shape `{if, then}` → `{requires, invalid}` across `data-model.md`, configurator/SKILL.md, `examples/recommendation.json`, system-prompts.md.
- `POST /constraints` body wrap (atomic-replace semantics + `forbidden` field + 409) clarified.
- `OptionAreaConfig` — full 9 REST-overridable fields documented (was 4); `?area_id=` required on every method; `DELETE`-with-`?field=` clear semantics; `NULL` = inherit.
- Drop phantom `datasheet` doc_type from data-model.md and configurator/SKILL.md; backend registers `{offer, quote, technical_doc, ccms, custom}`.
- `?include=options` does not exist — paginate `/groups` + `GET /groups/{id}/options` or use `?expand=areas.groups.options` on product.
- 12 configuration rules → **11** (actual count).
- `catalogue_state.json` was documented but never implemented — removed from tenant-memory layout.

**`audit_runner.py` fixes**:
- `has_next` → `has_more` (the pagination meta key mismatch silently stopped iteration after page 1).
- `check_options_with_conflicting_area_overrides` rewritten to call `GET /options/{id}/area-config?area_id=...` per area (route returns 400 without `?area_id=`).
- `check_duplicate_dynamic_wrappers` now passes `?include_locales=true` (without it the loop walked an always-empty array).

**`apply-config` precision**:
- Drop the "seven operation types" cap — both SKILL and operations-contract describe the 3-tier (15-op) builder reality.
- Fix `?name=` → `?search=` for `/products`, `/areas`, `/groups` list filters.
- Fix `POST /groups/{id}/areas` body `{area_id: <id>}` → `{area_ids: [...]}`.
- Fix `ensure_area_config` field description → `option_description` (the `AreaConfigUpdateRequest` schema uses `option_description`, not `description`; `extra=forbid` rejects the wrong name).
- `validate_recommendation.py` accepts both `forbidden` (canonical) and `forbidden_pairs` (legacy alias).
- Examples: rename `forbidden_pairs` → `forbidden`; swap `dynamic:document_line_items` → `dynamic:document_pricing` in `offer-template.json` (line_items belongs to quote, pricing to offer).

**BOM tier defect documented**: `effective_from` / `effective_to` are silently dropped on `BomItem` POST and PATCH (parts.py:633-647 + :691-737), so the natural key collapses to `(NULL, NULL)` until the route handler is patched.

### Changed — round-2 precision audit (speak the API's language byte-for-byte)

CRITICAL backend corrections verified directly against rattleapp Pydantic schemas / route definitions:
- `/documents/templates GET` does **not** accept `?search=` — paginate `?doc_type=&product_id=` and filter on name client-side.
- `ensure_structure_block` natural key is `(template_id, slug)`, not `(template_id, slug, parent_id)` — verified `UniqueConstraint` on `StructureBlock.__table_args__`.
- Content-block locale endpoints corrected: real routes are `POST /content-blocks/{id}/locales` (upsert by body field `language`) then `PUT/PATCH` by integer `locale_id`.
- `AttachmentCreateRequest` field is `conditions: list[dict]` (max 200), not `condition_json`; `extra="forbid"`.
- Content-block locale wire field is `blocks` (or `template_name`), not `block_json` (model column is `block_json` — wire vs storage).
- `Part.part_img`: dropped from create example + field table — `PartCreateRequest` does **not** accept it (`extra="forbid"`).
- `Part.status` enum is `{active, inactive, deprecated}`, default `"active"` (was incorrectly `"Released"` in `{Draft, Review, Released, Obsolete}`).
- Dropped `make_or_buy` and `bom_structure` from `/parts` query-param list — the route ignores them (filter client-side).
- Documented `part_type` / `make_or_buy` / `bom_structure` / `phantom_resolve_mode` enum members per the field_validator constants.

### Changed — round-1 review findings (legal + structural correctness)

- **`doc_type=technical_doc` is the canonical write value.** The Pydantic create/update validator (`app/schemas/v1/document.py:81 _validate_doc_type`, with `extra="forbid"`) accepts `{offer, quote, technical_doc, ccms, custom}` plus the legacy plurals. The string `technical_documentation` is **rejected on POST/PUT** even though some seeded rows in the database still carry it. Always send `technical_doc` on writes; use either form on `GET ?doc_type=…` filters.
- **MDR / IVDR firmly out of scope.** The 15-chapter machinery scaffold is **not** an MDR-compliant Instructions for Use (IFU). Refuse the machinery scaffold for medical devices and flag the scope mismatch (a future `rattle-techdoc-medical` skill would own ISO 20417 + ISO 15223-1 + IEC 62366-1).
- **MVO Article 10(7) digital-provision rule encoded** — consumer-machinery paper mandate (safety-essential information must be on paper for non-professional use), online availability for the expected lifetime of the machinery and at minimum 10 years, paper version free within one month on request.
- **IEC/IEEE 82079-1 references corrected** — the seven quality attributes live in **Clause 5** (not §7); subclauses 7.5 (warnings) and 7.6 (graphical/textual symbols) drive the cross-reference with ISO 3864-2 / ANSI Z535.6.
- **CLP statement provenance** — every shipped statement should be checkable against ECHA's published Annex III/IV/VI translations on EUR-Lex; `mhchem/hpstatements` data is derived from those.
- **MRL Annex I §1.7.4.2 (a)–(v)** — corrected the lettered-content reference from "(a-x)" to "(a-v)" per the consolidated text.
- **MRL effective dates** — applies until 19 January 2027 (inclusive); MVO from 20 January 2027 (Article 53(2)).

## [0.5.0] - 2026-05-09

### Added — technical-documentation expert tier

- **`skills/rattle-techdoc/`** — host skill for the 15-chapter normative technical-documentation structure (DIN EN ISO 20607, IEC/IEEE 82079-1, MRL/MVO). Includes 4 reference docs:
  - `references/chapter-reference.md` — every canonical chapter and section with mandatory content callouts and norm refs.
  - `references/audit-checks.md` — 14 structural checks (CRITICAL / HIGH / MEDIUM / LOW).
  - `references/editorjs-blocks.md` — every EditorJS block type used in tech docs with shape, validation, ordering.
  - `references/legal-basis.md` — MRL 2006/42, MVO (EU) 2023/1230, MDR (out-of-scope), CLP, harmonised standards reference.
- `scripts/inventory_techdocs.py` — extract chapter map and reusability candidates from input PDF/Word manuals.
- **`skills/rattle-safety-notices/`** — ISO 7010 + ISO 3864-2 + ANSI Z535.6 expertise. EditorJS `safety_notice` block contract. 5 ISO 7010 categories (warning W*, prohibition P*, mandatory M*, safe-condition E*, fire-protection F*) plus the separate CLP/GHS pictogram set. SAFE-principle authoring (Signalwort, Art und Quelle, Folgen, Entkommen). 32-locale signal-word catalogue.
- **`skills/rattle-ghs-statements/`** — CLP Regulation EC 1272/2008 H/P/EUH statements + 9 GHS pictograms. EditorJS `hp_statement` block contract. 24-locale resolution. Combined and enhanced statements.
- **`skills/rattle-techdoc-language/`** — IEC/IEEE 82079-1 Clause 5 quality attributes (complete, correct, concise, consistent, comprehensible, accessible, plus minimalism). Imperative-mood instructions, original-language obligation per MRL §1.7.4.1, MVO 2023/1230 Article 10(7) digital provision (consumer-machinery paper mandate).
- **`agents/rattle-techdoc-author.md`** — senior technical-writer subagent. Walks inventory → audit → plan → build → translate when given N input manuals.
- **`agents/rattle-techdoc-auditor.md`** — read-only compliance auditor running the 14 structural checks plus safety-notice + GHS + language quality rules.
- **`commands/rattle-build-techdoc.md`** — `/rattle-build-techdoc` slash command.
- **`commands/rattle-audit-techdoc.md`** — `/rattle-audit-techdoc` slash command.

### Added — safety-logos and hp-statements API integration

The rattleapp backend now exposes 4 read-only endpoints that let agents pick the correct ISO 7010 / GHS symbol and resolve CLP H/P/EUH codes from the live catalogue instead of falling back to defaults:

- `GET /api/v1/safety-logos[?category=...]` — ISO 7010 + GHS catalogue with EN+DE descriptions.
- `GET /api/v1/hp-statements[?locale=...&include_ghs_map=...]` — full CLP dictionary + pictogram map.
- `GET /api/v1/hp-statements/{code}[?locale=...&slot_1=...&slot_2=...]` — resolve a single code (supports combined keys + slot placeholders).
- `GET /api/v1/safety-notices/signal-words[?locale=...]` — list ANSI/ISO signal words for one or all locales.

The author and auditor agents now call these endpoints before emitting any safety_notice or hp_statement block. New audit rules: `default-fallback-symbol` (MEDIUM, `W001_general_warning_sign.svg` used despite a better API match) and `mismatched-ghs-pictogram` (HIGH, image GHS pictogram disagrees with API-resolved one).

### Changed

- README refreshed with the two-domain (configurator + technical-documentation) ASCII diagram, "What you can do with it" section (9 concrete actions), and "The technical-documentation domain" section parallel to "The #1 rule".
- `CLAUDE.md` and `AGENTS.md` register all new skills, agents, commands, and references.
- Plugin manifest version bumped to 0.5.0 (12 skills · 5 subagents · 6 slash commands at the time).

## [0.4.0] - 2026-04-28

### Changed — workspace renamed to **Grimoire**

- **Project name** is now **Grimoire**. The Rattle product configurator (rattleapp.de) is the *target* of the workspace; Grimoire is the workspace itself.
- **GitHub repo** moved to `rattleai/grimoire` (was `mngapps/rattle_api`). Old URL still redirects, but new clones should use the canonical location.
- **npm package** renamed to `@rattleai/grimoire` (was `@rattle/ai-workspace`). Install: `npx @rattleai/grimoire install`.
- **PyPI distribution** renamed to `grimoire` (was `rattle-ai-workspace`). Install: `pip install grimoire`. The `rattle` console script keeps its name — it is the CLI for the Rattle API.
- **Claude Code plugin** renamed to `grimoire`. Install: `/plugin marketplace add rattleai/grimoire` then `/plugin install grimoire`.
- **Installer script** renamed `bin/rattle-skills-install.mjs` → `bin/grimoire.mjs`. The two `bin` entries are now `grimoire` and `grimoire-install`.
- All cross-references updated in `AGENTS.md`, `CLAUDE.md`, `SETUP.md`, `CONTRIBUTING.md`, `README.md`, and the runtime error messages in `rattle_api/source.py`.

### Added

- `PUBLISHING.md` — release runbook for npm, PyPI, the Claude Code marketplace, and GitHub releases.
- `package.json` `publishConfig.access: "public"` so `npm publish` works for the scoped package by default.

### Migration notes

- Skill ids (`rattle-configurator`, `rattle-api`, `rattle-pricelist-analysis`, etc.) are **unchanged** — they describe the *target product* (Rattle), not the workspace. Bookmarks and slash commands keep working.
- Commit `5adde19` was the last 0.3.0 commit. Anyone who installed from that commit can stay on it; the rename is documentation/distribution-only.

## [0.3.0] - 2026-04-28

### Added

- Three new Anthropic-format Skills completing the workflow chain:
  - `skills/rattle-apply-config/` — idempotent `ensure_*` operations applier with `references/operations-contract.md` and `scripts/validate_recommendation.py` (deterministic recommendation validator).
  - `skills/rattle-audit/` — live-tenant structural auditor with `references/audit-runner.md` (language-agnostic spec) and `scripts/audit_runner.py` (stdlib-only Python implementation of all 6 checks).
  - `skills/rattle-tenant-memory/` — discoverable skill for the file-based tenant memory model.
- Four JSON Schemas (`schemas/`) — machine-validatable contracts for every workflow output: `recommendation.schema.json`, `audit-findings.schema.json`, `offer-template.schema.json`, `apply-operations.schema.json`.
- Golden I/O examples (`examples/`) — synthetic Widget Pro / acme tenant pairs for every workflow plus `tenant-profile.md` template.
- npm installer copies `schemas/` and `examples/` alongside skills and stays at the project root in `claude` / `user` layouts.

### Changed

- `package.json` `files` array extended; version bumped to `0.3.0`.
- `.claude-plugin/plugin.json` and `marketplace.json` describe 8 skills (previously 5) and 7 idempotent ensure_* operation types.
- `AGENTS.md` and `CLAUDE.md` knowledge tables list the new skills, schemas, and examples.

## [0.2.0] - 2026-04-28

### Added

- Five Anthropic-format Skills (`skills/rattle-configurator/`, `rattle-api/`, `rattle-pricelist-analysis/`, `rattle-suggest-config/`, `rattle-document-templates/`) bundling consulting knowledge in a model-agnostic format.
- Three Claude Code subagents (`agents/rattle-consultant.md`, `rattle-auditor.md`, `rattle-config-builder.md`).
- Four Claude Code slash commands (`/rattle-analyse`, `/rattle-suggest-config`, `/rattle-audit`, `/rattle-build-offer`).
- Cross-platform `AGENTS.md` for Cursor, Codex, Aider, Continue.
- Claude Code plugin manifest (`.claude-plugin/plugin.json` + `marketplace.json`) — installable via `/plugin marketplace add mngapps/rattle_api`.
- npm installer (`@rattle/ai-workspace` + `bin/rattle-skills-install.mjs`) with `flat`, `claude`, and `user` layouts.

### Changed

- README repositioned to lead with the AI-native workspace story; Python CLI is one of three install channels.
- `pyproject.toml` keywords expanded.

## [0.1.0] - 2026-03-21

### Added

- Initial public release.
- AI-agnostic provider abstraction supporting OpenAI, Anthropic, Ollama, and custom HTTP endpoints.
- CLI commands: `test-connection`, `list-sources`, `ai-describe`, `ai-classify`, `ai-transform`, `ai-analyse`, `ai-providers`.
- Data interchange transformation between formats (Datanorm, eCl@ss, BMEcat, Rattle).
- Image processing utilities for product data.
- Comprehensive documentation, contributing guide, and CI pipeline.
