# AGENTS.md — Rattle AI Workspace

This file follows the [agents.md](https://agents.md) convention so any AI agent (Claude Code, Cursor, Codex, Aider, Continue, Cline, etc.) can pick up the project conventions without bespoke configuration. Claude Code users get this same content layered with `CLAUDE.md`.

## What this repo is

An **AI-native workspace** for the Rattle product configurator (rattleapp.de). It bundles model-agnostic knowledge (Anthropic-format Skills under `skills/`), Claude-specific subagents and slash commands, and a Python CLI as one execution layer. The goal is that any AI model — Claude, GPT-4/5, Llama, Mistral — can produce correct, BOM-aware Rattle configurations by reading this repo.

## Where the knowledge lives

When the user asks anything Rattle-related, **read these files before answering**:

| File | Purpose |
|---|---|
| `skills/rattle-onboarding/SKILL.md` | **Day 0 — load this when the tenant is new or empty.** Every other skill assumes a tenant that already has products. Walks company → languages → **base price list (before any product)** → conventions → areas → configurator settings → first product → baseline audit → tenant profile. |
| `skills/rattle-ingest/SKILL.md` | **The first link of the data chain.** Raw customer file (Excel / CSV / ERP export) → column roles → `source-mapping.json` → normalized rows. Load this before pricelist-analysis whenever the columns have not been agreed. Includes `scripts/profile_source.py`, `references/column-roles.md` (24 roles), `references/sheet-shapes.md` (5 shapes). |
| `skills/rattle-configurator/SKILL.md` | The #1 rule + workflow entry point. Always load this first. |
| `skills/rattle-configurator/references/data-model.md` | Full schema for every entity. |
| `skills/rattle-configurator/references/configuration-rules.md` | 11 configuration rules with rationales. |
| `skills/rattle-configurator/references/anti-patterns.md` | 4 anti-patterns with indicator keywords. |
| `skills/rattle-configurator/references/structural-checks.md` | 6 live-tenant audit checks. |
| `skills/rattle-configurator/references/system-prompts.md` | Canonical prompt templates for any LLM. |
| `skills/rattle-api/SKILL.md` | REST API conventions (auth, pagination, errors). |
| `skills/rattle-api/references/api-reference.md` | Full reference for 462 operations across 257 paths (37 tags). Generated from `openapi.json` by `scripts/build_api_reference.py`. |
| `skills/rattle-api/references/openapi.json` | Raw OpenAPI 3.x spec. |
| `skills/rattle-api/references/client-patterns.md` | List-all, idempotent ensure, multipart upload, optimistic concurrency. |
| `skills/rattle-pricelist-analysis/SKILL.md` | Workflow: analyse a pricelist for anti-patterns. Includes `scripts/detect_anti_patterns.py`. |
| `skills/rattle-suggest-config/SKILL.md` | Workflow: produce a BOM-aware config recommendation. |
| `skills/rattle-document-templates/SKILL.md` | Workflow: build offer/quote/custom/ccms templates. (Use `rattle-techdoc` for `doc_type=technical_doc`; `datasheet` is not a registered backend doc_type — it rides on `custom`.) |
| `skills/rattle-techdoc/SKILL.md` | Workflow: build full technical documentations (`doc_type=technical_doc` — write canonical; legacy alias `technical_documentation` accepted on filters only) from input manuals. 15-chapter normative structure (DIN EN ISO 20607, IEC/IEEE 82079-1, MRL/MVO). Includes 4 reference files and `scripts/inventory_techdocs.py`. |
| `skills/rattle-techdoc/references/chapter-reference.md` | Master template — every canonical chapter and section, mandatory content callouts, norm refs, reusable content-block keys. |
| `skills/rattle-techdoc/references/audit-checks.md` | 14 structural checks for technical docs (12 numbered + 10b + 10c) (CRITICAL/HIGH/MEDIUM/LOW). |
| `skills/rattle-techdoc/references/editorjs-blocks.md` | Every EditorJS block type used in tech docs with shape, validation, ordering. |
| `skills/rattle-techdoc/references/legal-basis.md` | MRL 2006/42, MVO (EU) 2023/1230, MDR, CLP, harmonised standards reference. |
| `skills/rattle-safety-notices/SKILL.md` | Knowledge: ISO 7010 + ISO 3864-2 + ANSI Z535.6-2011 (R2017) safety notices. EditorJS `safety_notice` block contract. Signal-word locales (32), **5** ISO 7010 categories + the separate CLP/GHS pictogram set, SAFE-principle (Signalwort, Art und Quelle, Folgen, Entkommen). |
| `skills/rattle-ghs-statements/SKILL.md` | Knowledge: CLP Regulation EC 1272/2008 H/P/EUH statements + 9 GHS pictograms. EditorJS `hp_statement` block contract. 24-locale resolution, combined and enhanced statements. |
| `skills/rattle-techdoc-language/SKILL.md` | Knowledge: language, tone, mood, terminology rules per IEC/IEEE 82079-1:2019 Clause 5 (the seven quality attributes). Imperative-mood, original-language obligation, MVO Article 10(7) digital provision including consumer-machinery paper mandate. |
| `skills/rattle-bom-builder/SKILL.md` | Variant-BOM expert: usage_subclauses DSL, option_scalings (legacy / ratio / range), numbered-option scaling patterns, alt_group alternates, ghost depth-transparency, BOM explosion semantics. Includes 6 references and `scripts/validate_variant_bom.py`. |
| `skills/rattle-bom-builder/references/usage-subclauses.md` | Conditional-inclusion DSL — clauses, AND/OR fold, groupSelections, areaStatuses, areaSubclauses; 9 worked examples. |
| `skills/rattle-bom-builder/references/option-scalings.md` | Three scaling descriptors (legacy numeric, ratio opt:part, range areas[]); multiplicative vs. additive resolution; 12 worked examples. |
| `skills/rattle-bom-builder/references/numbered-options.md` | 12 numbered-option scaling patterns (one-to-one, many-to-one, length-scaled, threshold-stepped, multi-option composition, area-scoped). |
| `skills/rattle-bom-builder/references/bom-explosion.md` | Runtime semantics — per-edge evaluation order, alt_group selection, ghost depth-transparency, aggregation. |
| `skills/rattle-bom-builder/references/data-model.md` | Every field of Part / PartPlacement / BomItem / BomLineRev / Option lifted from `app/models.py`. |
| `skills/rattle-bom-builder/references/api-endpoints.md` | REST endpoints, idempotent ensure operations, bulk import / export, validation errors. |
| `skills/rattle-apply-config/SKILL.md` | Workflow: apply a recommendation idempotently via 7 `ensure_*` ops. Includes `scripts/validate_recommendation.py`. |
| `skills/rattle-audit/SKILL.md` | Workflow: scan a live tenant against the 6 structural checks. Includes `scripts/audit_runner.py`. |
| `skills/rattle-tenant-memory/SKILL.md` | Per-tenant preferences, decisions, audit history (file-based, explicit-write only). |
| `schemas/source-mapping.schema.json` | JSON Schema for `rattle-ingest` output (column roles, sheet shape, blockers). |
| `schemas/recommendation.schema.json` | JSON Schema for `rattle-suggest-config` output. |
| `schemas/audit-findings.schema.json` | JSON Schema for `rattle-audit` output. |
| `schemas/offer-template.schema.json` | JSON Schema for `rattle-document-templates` output. |
| `schemas/apply-operations.schema.json` | JSON Schema for `rattle-apply-config` operations array. |
| `schemas/variant-bom.schema.json` | JSON Schema for `rattle-bom-architect` output (parts, placements, bom_items). |
| `examples/` | Synthetic golden I/O for every workflow (Widget Pro, acme tenant). Every file validates against its schema; CI enforces it. |
| `mcp/server.mjs` | Rattle MCP server. Serves the skills *and* the live API to clients with no native Skills mechanism (Cursor, Windsurf, Claude Desktop, ChatGPT). Zero dependencies, zero per-endpoint code. Read-only unless `RATTLE_MCP_ALLOW_WRITES=1`. |

Tenant-specific style preferences live under `memory/<tenant>/profile.md` (gitignored). Always check this before producing recommendations for a named tenant.

## The #1 rule (read this every time)

> **Never build "base product + add-ons" where the base configuration is implicit.** Every configurable feature MUST have an explicit group with ALL variants as separate options — including the "standard" / default variant.

The Rattle BOM is driven by `usage_subclauses` on BOM items linking parts to options. If the standard variant has no option, no BOM line can reference it, and the configurator can't toggle the standard parts on or off. Surface implicit baselines as blockers before producing recommendations. Full rationale + wheels example: `skills/rattle-configurator/SKILL.md` "The #1 rule".

## How to work in this repo

### Adding new consulting knowledge

1. The source of truth for rules / anti-patterns / checks is **the Markdown reference files** under `skills/rattle-configurator/references/`. Edit them.
2. Mirror the same content in `rattle_api/knowledge.py` so the Python CLI's prompts stay in sync. The Markdown wins on conflicts.
3. If you add a new rule, add it to `configuration-rules.md`, cross-reference it in any matching anti-pattern (`anti-patterns.md`) and structural check (`structural-checks.md`).
4. Tests in `tests/test_knowledge.py` should reference the rule id; if you only edited Markdown, no test changes are needed, but please re-run `make test` to make sure the Python prompt builders still pass.

### Adding a new skill

1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`, optionally `license`).
2. Add references under `skills/<skill-name>/references/*.md` and bundled scripts under `skills/<skill-name>/scripts/`.
3. Cross-reference the skill from related skills' `## Related skills` sections.
4. Add it to the list above and to `.claude-plugin/plugin.json` keywords if relevant.

### Adding a new slash command (Claude-Code-specific)

1. Create `commands/<name>.md` with YAML frontmatter (`description`, optional `argument-hint`).
2. The body describes what the command should do; reference skills + agents the command uses.
3. Use `$ARGUMENTS` for the user's argument string.

### Adding a new subagent (Claude-Code-specific)

1. Create `agents/<name>.md` with frontmatter (`name`, `description`, `tools`).
2. Describe operating procedure, output contract, boundaries.
3. Subagents are spawned via the Agent tool with `subagent_type=<name>`.

### Adding a new AI-provider task

The Python execution layer's prompts already mirror `skills/rattle-configurator/references/system-prompts.md`. To add a new task:

1. Document the prompt in `system-prompts.md` first (input parameters, output contract).
2. Add a `system_prompt_<name>` builder in `rattle_api/knowledge.py` that produces the same prompt.
3. Add the task function in `rattle_api/tasks.py`.
4. Add the CLI subcommand in `rattle_api/main.py`.
5. Add tests in `tests/test_tasks.py` and `tests/test_knowledge.py`.

## Coding conventions

- **Python**: PEP 8, type annotations on all signatures, `ruff` for linting, `mypy` for type-checking, `pytest` for tests, `pytest-cov` for coverage. See `pyproject.toml` for exact config. Run `make check` before committing.
- **Imports**: relative inside the package (`from .config import …`), absolute from tests (`from rattle_api.provider import …`).
- **Tests**: `conftest.py` strips credentials with `clean_env` autouse fixture; tests run without network or real API keys; use `FakeAIProvider` for AI behaviour. Aim for 80%+ coverage.
- **Output JSON**: every CLI command writes JSON to stdout, progress to stderr, no interactive prompts. AI agents and shell pipelines depend on this.
- **No silent writes**: tasks never modify `memory/<tenant>/*` silently. All writes go through explicit `rattle <tenant> memory …` subcommands.
- **No mocking the API in tests**: the existing tests use a `FakeAIProvider` for LLM calls but exercise real parsers and prompt builders.

## Style and tone

- Concise. The user is usually a domain expert.
- Cite rule and anti-pattern ids in findings (`explicit-options-for-all-variants`, `implicit-base-config`) — they're the keys downstream tools track.
- Default to German output if the user writes in German or names a German-speaking tenant.
- Never invent part numbers or prices — propose placeholders and flag in `notes`.

## Security and secrets

- API keys live in `RATTLE_API_KEY_<TENANT>` env vars or a local `.env` (gitignored).
- Never log or echo `Bearer rk_live_…` tokens.
- Never commit `memory/<tenant>/*` (gitignored except `README.md` + `.gitkeep`).
- The repo contains no production tenant data. Examples use synthetic option/group names.

## The workflow chain

Every engagement runs the same chain. Skipping a link is the most common way to get a wrong configuration:

```
rattle-onboarding → rattle-ingest → rattle-pricelist-analysis → rattle-suggest-config → rattle-apply-config
   (day 0, once)      (per data drop) ─────────────────────────────────────────────────────────────────▶
```

- **Start at `rattle-onboarding`** if the tenant is new or empty. Every skill downstream assumes a tenant that already has a company profile, a **base price list** (currency lives there — a product's `currency` is silently ignored), languages, and areas. Get the order wrong and prices land in the wrong currency with no error.
- **Start at `rattle-ingest`** whenever the user hands over a file whose columns have not been explicitly agreed. Do not skip to pricelist-analysis because the headers "look obvious" — headers lie, abbreviate, and mix languages.
- **The chain is gated.** While `rattle-ingest` reports a non-empty `blockers[]`, `rattle-suggest-config` MUST NOT run. Answer the blocking question with the customer and re-ingest.
- **Never fabricate to clear a blocker.** Not a standard option, not a price, not a part number. Emit a placeholder plus the one question a human must answer. A guessed standard variant corrupts the BOM, the pricing, and every offer built on it.
- **BOM-shaped sheets branch off.** A `one-row-per-bom-line` sheet goes to `rattle-bom-builder`, not `rattle-suggest-config` — a BOM cannot be built before the options exist.

## Distribution

Four ways:

1. **Claude Code plugin** (richest — prompts for your API key at install, no `.env` to edit):
   ```
   /plugin marketplace add rattleai/grimoire
   /plugin install grimoire
   ```

2. **MCP** (Cursor, Windsurf, Claude Desktop, ChatGPT — the clients with no native Skills mechanism). Point them at `mcp/server.mjs`; see the root `.mcp.json`. Node ≥ 18, zero npm dependencies. Read-only until `RATTLE_MCP_ALLOW_WRITES=1`.

3. **npx installer** (drops skills + agents + MCP + AGENTS.md into any project). **Not yet on npm** — run it from a clone:
   ```
   git clone https://github.com/rattleai/grimoire.git
   node grimoire/bin/grimoire.mjs install --target ./my-project
   ```
   Becomes `npx @rattleai/grimoire install` once published.

4. **Python CLI** (optional execution layer — the skills do not need it). **Do not `pip install grimoire`**: that name belongs to an unrelated package. This project publishes as `rattle-grimoire`. Until released, install from a clone:
   ```
   git clone https://github.com/rattleai/grimoire.git && cd grimoire
   pip install -e ".[all-ai,all-sources]"
   rattle <tenant> ai-analyse-pricelist <file>
   ```

Paths 1 and 2 need **nothing published** — the bundle is text plus a zero-dependency script, so a clone is a complete install.

See `README.md` for full setup.

## Development workflow

```bash
make lint          # Ruff + format check
make type-check    # mypy
make test          # pytest (170+ tests, ~97% coverage)
make check         # all of the above
make format        # auto-format
```

Pre-commit hooks live in `.pre-commit-config.yaml`. Run `pre-commit install` once after cloning.
