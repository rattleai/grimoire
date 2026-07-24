# Changelog — Rattle AI Workspace

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed — API spec refreshed; several audit findings resolved upstream

Re-ran `scripts/build_api_reference.py` against the live spec. The surface grew, and — more consequentially — the backend shipped fixes for defects the skills had documented as workarounds. Leaving the skills untouched would have told agents to route around problems that no longer exist, or (worse) to refuse a task the API can now do.

| | was | now |
|---|---|---|
| operations | 463 | **472** |
| paths | 258 | **260** |
| schemas | 210 | **223** |

- **Path parameters renamed** across ~45 paths: `{id}` → resource-specific `{areaId}` / `{groupId}` / `{optionId}` / `{partId}` / `{priceListId}` / `{productId}` / `{quoteId}` / `{customerId}`; plus `{lang}` → `{localeId}` on document block locales (**still a language code, not an integer, despite the name**) and inbound `{suffix}` → `{triggerId}`. The generated reference + mirror carry the new forms; hand-written skill prose that used the old ones was updated.
- **New endpoints surfaced in the skills:** `POST /configurations` (the headless write path to a saved, finalizable, quotable configuration — **rattle-crm-quotes had explicitly stated this did not exist**), `POST /placements/batch`, and the declarative `PUT /parts/{partId}/bom` sync.
- **Resolved defects reflected in the skills** (these were active falsehoods that caused refuse-task / 422 / mis-map):
  - OCC/idempotency headers are now declared (`X-Constraints-Version`, `X-Price-Lists-Version`, `X-Idempotency-Key`) and `PriceListResponse` gained a `version` field — but the price-override `/replace` endpoints still declare neither a header nor a `409`, so that specific P0-1 danger stands (narrowed, not retired).
  - `advanced-prices` schemas are now named (`AdvancedPrice{Create,Update,Response}`) with `additionalProperties: false`; `PATCH` removed (PUT-only, and it can now re-scope `area_id`/`price_list_id`); precedence over an option price-override and null-scoping are now documented.
  - `Product.sku` now exists (ERP join key → flows to `QuoteLineItemResponse.product_sku`); part images now have an upload route (`POST /parts/{partId}/image` → `image_url`); `is_stale` now exists on `StructureBlockLocaleResponse`; configurator settings are now typed (`ConfiguratorSettings{Response,UpdateRequest}`, `additionalProperties: false`). The "does not exist / no route / spec doesn't match live" claims were corrected in `rattle-crm-quotes`, `rattle-ingest`, `rattle-i18n`, and `rattle-onboarding`.
  - `QuoteContactAddRequest.role` was removed from the write request (now read-only on `QuoteContactResponse`).
  - Constraint `rule_json` is formalized as `ForbiddenRuleJson` / `RuleClause`, with a new `at_most_n` cardinality rule type.
- **Surface counts updated** across README, CLAUDE.md, the MCP server tool descriptions, and skill descriptions. The point-in-time audit reports (`docs/API_AUDIT.md`, `docs/API_REMEDIATION.md`) were **left as the dated records they are** — their internal counts describe the audited snapshot and were not renumbered.

## [0.7.0] - 2026-07-14

The theme of this release is **making the bundle installable and usable by someone who is not us** — closing the gap between "a repo full of good knowledge" and "a system a stranger can install and point at their own data."

### Added — `rattle-ingest`: the missing first link

Until now nothing in the bundle mapped a customer's *raw* data onto Rattle entities. `rattle_api/source.py` only *read* files (Excel → rows, PDF → text); `rattle-pricelist-analysis` emitted *findings*, not a mapping. So the chain began one step too late — it assumed the data was already understood.

- **`skills/rattle-ingest/`** — the new first link. Raw spreadsheet / CSV / ERP export → a reviewable `source-mapping.json` → normalized rows the rest of the chain already consumes. The full chain is now:
  `rattle-ingest` → `rattle-pricelist-analysis` → `rattle-suggest-config` → `rattle-apply-config`.
  - `references/column-roles.md` — the column-role taxonomy (DE + EN header keywords, value-shape signals, target entity/field, confidence rules).
  - `references/sheet-shapes.md` — the five real-world sheet shapes and the normalization strategy for each, including the wide variant matrix (variants as columns, prices in cells).
  - `scripts/profile_source.py` — deterministic column profiler. Never guesses a column's meaning from its header alone; ranks candidate roles from cardinality, dtype and value samples.
- **`schemas/source-mapping.schema.json`** + `examples/source-mapping.json` — the reviewable contract. A human confirms the mapping *before* anything is built.
- **`commands/rattle-ingest.md`** — `/rattle-ingest`.

Ingestion is where the #1 rule is enforced **at the door**: a column of surcharges with no "standard" row is an `implicit-base-config` blocker. The skill surfaces the missing standard variant — it never invents one.

### Added — the Rattle MCP server (`mcp/server.mjs`)

Claude Code has a native Skills mechanism. Cursor, Windsurf, Claude Desktop and ChatGPT do not. The MCP server is how one bundle serves all of them.

- **Zero drift by construction.** The Rattle API has 443 operations across 245 paths. A server hand-declaring one tool per endpoint would rot the day rattleapp ships a new one. This server declares **no per-endpoint code at all**: `rattle_request` is a generic authenticated passthrough and `rattle_api_search` searches the bundled OpenAPI spec. A new endpoint works the day it ships.
- **Zero dependencies.** Claude Code loads a plugin by cloning it — there is no `npm install` step. The server speaks MCP's stdio transport (newline-delimited JSON-RPC 2.0) directly against Node's stdlib. Node ≥ 18 is the only requirement.
- **`rattle_knowledge_list` / `rattle_knowledge_get`** + an MCP resource surface hand the skills, references and schemas to clients that have no Skills mechanism of their own.
- **Read-only by default.** Every non-GET request is refused unless `allow_writes` is explicitly enabled. A live CPQ tenant is not a sandbox.
- `.mcp.json` at the repo root wires the same server into Cursor / Windsurf / Claude Desktop without the plugin.

### Added — `scripts/validate_bundle.py` + CI gates

Every check below exists because the corresponding defect actually shipped:

- Version drift across the four manifests (`package.json` said 0.4.0 and "8 skills, 3 subagents, 4 commands" while 13/6/7 were on disk and `plugin.json` said 0.6.0).
- `strict: false` in `marketplace.json`, which is a **hard load failure** the moment `plugin.json` declares any component.
- Compiled bytecode published to npm — `npm pack --dry-run` confirmed three `.pyc` files were shipping, because the `files` allowlist overrides `.gitignore`.
- A golden example silently drifting from the schema it claims to satisfy.
- An agent's `skills:` list naming a skill that does not exist (a silent no-op at load time, indistinguishable from "the agent just didn't use it").

Wired into `make check` and CI, alongside `scripts/mcp_smoke.mjs`, which drives the MCP server over its real stdio transport and asserts the read-only guarantee holds.

### Fixed

- **`rattle-suggest-config` contradicted itself.** The body stated the canonical `rule_json` shape is `{requires, invalid}` and that the legacy `[{if, then}]` array is wrong — then its own output-contract example used exactly that legacy shape. The legacy shape is **silently dropped** by the runtime evaluator, so a rule authored that way looks applied but never fires. Purged from `rattle-suggest-config`, `rattle-configurator`, `system-prompts.md`, `examples/apply-operations.json`, `CLAUDE.md`, and 5 sites in `rattle_api/knowledge.py`.
- **`examples/apply-operations.json` did not validate against its own schema** — it carried the legacy array shape. It now does, and CI enforces it.
- **Numbered options were unreachable.** `recommendation.schema.json` has supported `is_numbered` / `number_min` / `number_max` / `number_step` / `number_unit` / `price_scalings` all along, but the word `is_numbered` appeared **zero times** in `rattle-suggest-config` and `rattle-configurator` — so no AI following those skills could ever propose one, breaking the most common BOM-scaling case end to end. Both skills now teach the discrete / multi-select / numbered decision.
- **`numbered-options.md` Pattern 4 was unwireable.** It specified `number_min: 0.5, number_step: 0.1`, but `OptionCreateRequest.number_min/max/step` are **integers** — the API would 422. Corrected to integer bounds with a unit-conversion workaround, and carried through Patterns 5 and 7 for coherence.
- **The "read-only" auditors could write.** `rattle-auditor` and `rattle-techdoc-auditor` declared themselves read-only in prose while holding tools that permit writing. Now enforced by the `tools` allowlist + `disallowedTools`. Honest scope: `Bash` remains (they need it for the live-tenant CLI and the inventory script), so the *API* boundary is still prose — see each agent's `## Boundaries`.
- **Advisory agents promised delegation they could not perform.** `rattle-bom-architect` and `rattle-techdoc-author` said "spawn `rattle-techdoc-auditor`" / "hand off to `rattle-config-builder`" without the `Agent` tool. Kept toolless by design — an advisory agent that could spawn the only writer would defeat its own boundary — and the wording now says what actually happens.
- Removed `"category"` from `plugin.json` (not a recognized key — silently ignored).

### Changed

- All 6 subagents gained real frontmatter: `skills:` (preloading, replacing the prose "Loads X on activation" — a hope, not a mechanism), `model:`, and `disallowedTools:`. Bare skill names verified to resolve both as an installed plugin and when copied into `.claude/agents/`.
- `plugin.json` gained `userConfig` — the plugin now prompts for the API key, base URL, tenant and write-permission at install time and pipes them into the MCP server. No hand-edited `.env`.
- Versions unified at 0.7.0 across `package.json`, `pyproject.toml`, `plugin.json` and `marketplace.json`, with CI failing the build if they ever diverge again.

### Changed — the API spec is now fetched live, not trusted from disk

`scripts/build_api_reference.py` now **fetches the published spec by default** from <https://www.rattleapp.de/docs/api/openapi.json>; `--offline` renders from the checked-in copy for CI. A local spec goes stale invisibly — nobody finds out until an agent calls an endpoint that moved.

Refreshing against live immediately proved the point. The checked-in spec was **19 operations behind**:

| | was | now |
|---|---|---|
| operations | 443 | **462** |
| paths | 245 | **257** |
| resource groups | 36 | **37** |

Twelve paths were missing entirely, including several the skills already describe: `/parts/{id}/bom/explode`, `/parts/{id}/ghost/{materialize,resolve,status}`, `/parts/ghosts`, `/constraints/combination-rules`, and `/translations/dictionary/{entry_id}`. Counts updated across the README, AGENTS.md, CLAUDE.md, the API skill and the MCP server's tool descriptions.

### Fixed — the generator would have destroyed 197 lines of verified knowledge

`docs/API_REFERENCE.md` and its skill mirror are generated. Someone had hand-edited the **generated mirror** to correct the OCC status (`409 Conflict`, not `412 Precondition Failed`) and to add the entire Safety Reference section — which the `rattle-safety-notices` and `rattle-ghs-statements` skills tell the model to call *instead of guessing*. But CLAUDE.md instructs contributors to re-run the generator whenever the spec changes, and that run would have silently reverted the 409 and deleted the section outright.

Content the spec cannot express is now an **input** to the generator (`docs/api-supplement/`), never an edit to its output. `scripts/validate_bundle.py` fails the build if the two rendered copies ever diverge again.

The live refresh also resolved this cleanly: the four safety endpoints **now exist in the upstream spec** under a `Safety` tag, so the supplement was reduced to the consulting guidance the spec genuinely cannot carry (when a model must call these, and that a fallback symbol or hand-typed CLP text is a legal defect in a CE-marked document — not a cosmetic one).

### Fixed — `pip install grimoire` installed the wrong package

The PyPI name `grimoire` belongs to an unrelated bioinformatics library (KorfLab). `pyproject.toml` declared `name = "grimoire"`, so this project **could never be published** under it — and the README told users to run `pip install grimoire[all-ai,all-sources]`, which fetches a stranger's code.

Renamed to **`rattle-grimoire`**. The console script is still `rattle`; only the distribution name changed.

Install docs now state plainly what is and is not published:

- **Claude Code plugin** and **MCP server** work today with **nothing published** — the bundle is text plus a zero-dependency script, so a clone is a complete install.
- **npm** (`@rattleai/grimoire`) is unpublished; the installer runs from a clone in the meantime.
- **PyPI** is unpublished; `pip install -e .` from a clone in the meantime.

The `npx` installer's "Next steps" also listed only 4 of the 8 slash commands and never mentioned the MCP server. Both fixed.

### Resolved upstream

The previously-flagged legacy `{if, then}` / `forbid_options` example for `ForbiddenRuleCreateRequest` is **gone from the live spec**. The upstream fix has landed; nothing further is needed here.

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
  > **Corrected in 0.7.0 — the second half of this was wrong.** `?expand=areas.groups.options` returns **`400 — exceeds maximum depth of 2`**; it never worked. Verified against a live tenant 2026-07-14. The real ceiling is `?expand=areas.groups`, and **`options` is not expandable at any depth** — it is always N+1 (`GET /groups/{id}/options` per group). See `docs/API_AUDIT.md` § P1-7.
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
  > **Superseded in 0.7.0 — do not follow this.** The name `grimoire` was already taken on PyPI by an unrelated bioinformatics package, so this distribution was never publishable and `pip install grimoire` installs a stranger's code. Renamed to **`rattle-grimoire`**.
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
