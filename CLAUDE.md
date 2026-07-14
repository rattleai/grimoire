# Rattle AI Workspace

AI-native workspace for the Rattle product configurator (rattleapp.de). The repo is **two layers**:

1. **AI knowledge layer** — Anthropic-format Skills (`skills/`), Claude Code subagents (`agents/`), slash commands (`commands/`), the `.claude-plugin/` manifest, and the cross-platform `AGENTS.md`. This is the part any AI model can read and use, regardless of language or runtime.
2. **Python execution layer** — `rattle_api/` package + `rattle` CLI, which calls a configured AI provider (OpenAI / Anthropic / Ollama / custom HTTP) using the same prompts the Skills describe. One reference implementation; non-Python clients can build their own using the Skills.

**Read first:** when answering anything Rattle-related, load `skills/rattle-configurator/SKILL.md`. It encodes the #1 rule, the data model, configuration rules, anti-patterns, and structural checks. The cross-platform `AGENTS.md` lists every reference file with a one-line purpose.

## Knowledge layer (AI-native artifacts)

| Path | Purpose |
|---|---|
| `.claude-plugin/plugin.json` + `marketplace.json` | Claude Code plugin / marketplace manifest. Installable via `/plugin marketplace add rattleai/grimoire`. |
| `skills/rattle-ingest/` | **First link in the chain.** Raw customer file (Excel / CSV / ERP export) → 24 column roles → 5 sheet shapes → reviewable `source-mapping.json` + normalized rows. Enforces the #1 rule at the door: a surcharge column with no standard sibling is a **blocker**, never a guess. Includes `scripts/profile_source.py`. |
| `skills/rattle-configurator/` | Core consulting knowledge. **Always load first.** |
| `skills/rattle-api/` | REST API surface (auth, pagination, 462 operations across 257 paths, OpenAPI spec). |
| `skills/rattle-pricelist-analysis/` | Workflow: scan input for anti-patterns. Includes `scripts/detect_anti_patterns.py`. |
| `skills/rattle-suggest-config/` | Workflow: produce BOM-aware configuration recommendation JSON. |
| `skills/rattle-document-templates/` | Workflow: build offer/quote/custom/ccms templates honouring the doc_type contract. (Use `rattle-techdoc` for `doc_type=technical_doc`; `datasheet` is not a registered backend doc_type.) |
| `skills/rattle-techdoc/` | Workflow: build full technical documentations (`doc_type=technical_doc` — write canonical; legacy alias `technical_documentation` accepted on filters only). 15-chapter normative structure (DIN EN ISO 20607, IEC/IEEE 82079-1). Includes `scripts/inventory_techdocs.py` and reference files for chapters, audit checks, EditorJS blocks, legal basis. |
| `skills/rattle-safety-notices/` | Knowledge: ISO 7010 + ISO 3864-2 + ANSI Z535.6-2011 (R2017) safety notices. EditorJS `safety_notice` block contract, signal-word locales (32 languages), **5** ISO 7010 categories + the separate CLP/GHS pictogram set, SAFE-principle authoring (Signalwort, Art und Quelle, Folgen, Entkommen). |
| `skills/rattle-ghs-statements/` | Knowledge: CLP Regulation EC 1272/2008 H/P/EUH statements + 9 GHS pictograms. EditorJS `hp_statement` block contract, 24-locale resolution, combined and enhanced statements. |
| `skills/rattle-techdoc-language/` | Knowledge: language, tone, mood, terminology rules per IEC/IEEE 82079-1:2019 Clause 5 (seven quality attributes). Imperative-mood instructions, original-language obligation, MVO 2023/1230 Article 10(7) digital provision including consumer-machinery paper mandate. |
| `skills/rattle-apply-config/` | Workflow: apply a recommendation idempotently. Includes `scripts/validate_recommendation.py`. |
| `skills/rattle-audit/` | Workflow: scan a live tenant against the 6 structural checks. Includes `scripts/audit_runner.py`. |
| `skills/rattle-tenant-memory/` | Per-tenant preferences and decisions (file-based, explicit-write only). |
| `skills/rattle-bom-builder/` | Variant-BOM expert: usage_subclauses DSL, option_scalings (legacy / ratio / range), numbered-option scaling patterns, alt_group + priority alternates, ghost depth-transparency, BOM explosion semantics. Includes `scripts/validate_variant_bom.py` and 6 reference docs. |
| `schemas/` | JSON Schemas for the 6 output contracts (source-mapping, recommendation, audit-findings, offer-template, apply-operations, variant-bom). Every golden example in `examples/` validates against its schema — CI enforces it. |
| `mcp/server.mjs` | Rattle MCP server. Zero dependencies (raw JSON-RPC over stdio, so it works on the plugin path where there is no `npm install`) and zero per-endpoint code (`rattle_request` is a generic passthrough; `rattle_api_search` reads the bundled OpenAPI spec) — so it cannot drift when the API grows. Also serves the skills to clients with no Skills mechanism. **Read-only unless `RATTLE_MCP_ALLOW_WRITES=1`.** |
| `scripts/validate_bundle.py` | The bundle gate. Fails the build on manifest version drift, a `strict:false` load conflict, bytecode in the npm tarball, unknown frontmatter keys, an agent naming a nonexistent skill, or an example that no longer satisfies its schema. Wired into `make check` + CI. |
| `examples/` | Synthetic golden I/O for every workflow. |
| `agents/rattle-consultant.md` | Senior consultant subagent — orchestrates strategic decisions. |
| `agents/rattle-auditor.md` | Live-tenant structural auditor. Read-only. |
| `agents/rattle-config-builder.md` | Idempotent builder. Only agent allowed to write to the API. |
| `agents/rattle-techdoc-author.md` | Senior technical-writer subagent. Walks the inventory → audit → plan → build → translate workflow for technical documentations. |
| `agents/rattle-techdoc-auditor.md` | Read-only auditor for technical documentations. Runs ~30 checks across structural, safety-notice, GHS, and language rules. |
| `agents/rattle-bom-architect.md` | Senior variant-BOM architect. Walks parts → placements → bom_items → validation, produces the canonical variant-bom.json for `rattle-config-builder` to apply. |
| `commands/rattle-analyse.md` | `/rattle-analyse` slash command. |
| `commands/rattle-suggest-config.md` | `/rattle-suggest-config` slash command. |
| `commands/rattle-audit.md` | `/rattle-audit` slash command. |
| `commands/rattle-build-offer.md` | `/rattle-build-offer` slash command. |
| `commands/rattle-build-techdoc.md` | `/rattle-build-techdoc` slash command — build technical docs from input manuals. |
| `commands/rattle-audit-techdoc.md` | `/rattle-audit-techdoc` slash command — audit a technical-doc template against ISO 20607 / IEC 82079-1 / MRL/MVO. |
| `commands/rattle-build-bom.md` | `/rattle-build-bom` slash command — design / fix / validate a variant BOM with usage_subclauses + option_scalings. |
| `AGENTS.md` | Cross-platform agent rules (Cursor, Codex, Aider, Continue). |

The Markdown content under `skills/rattle-configurator/references/` is the source of truth for rules / anti-patterns / checks. `rattle_api/knowledge.py` mirrors it as Python data structures so the CLI's prompts stay in sync. **When they conflict, the Markdown wins — update the Python to match.**

## Python execution layer

Standard Python package layout — all source lives in `rattle_api/`:

| Module | Purpose |
|--------|---------|
| `rattle_api/main.py` | CLI entry point (argparse dispatch). All AI imports are lazy to avoid import errors when a provider SDK isn't installed. |
| `rattle_api/config.py` | Loads `.env`, resolves tenant API keys from `RATTLE_API_KEY_*` env vars, selects AI provider. |
| `rattle_api/client.py` | `RattleClient` — HTTP client for the Rattle REST API (GET/POST/PATCH/PUT/DELETE + pagination + image upload). |
| `rattle_api/provider.py` | `AIProvider` ABC + 4 implementations (OpenAI, Anthropic, Ollama, CustomHTTP). Registry pattern via `PROVIDERS` dict. |
| `rattle_api/tasks.py` | Task functions: `describe_products`, `classify_products`, `transform_interchange`, `analyse_data`, `analyse_pricelist`, `suggest_configuration`. Each fetches data from Rattle, sends to AI, optionally pushes results back. |
| `rattle_api/knowledge.py` | Configurator consulting knowledge: data model, configuration rules, anti-patterns, system prompts, heuristic detection. Source of truth for all domain expertise. |
| `rattle_api/source.py` | Reads local files from `source/<tenant>/` — Excel (.xlsx/.xlsm), PDF, and Word (.docx). |
| `rattle_api/image.py` | Image processing — shadow generation for "ohne" (without) product options. |

## Key Patterns

- **Env-var config**: All configuration via environment variables (see `.env.example`). No config files.
- **Tenant convention**: `RATTLE_API_KEY_ACME=abc` → tenant name `acme` on CLI.
- **AI provider registry**: Add provider by subclassing `AIProvider`, implementing `complete()`, registering in `PROVIDERS` dict in `provider.py`.
- **Lazy AI imports**: `main.py` imports AI task functions inside command handlers to avoid requiring AI SDKs for non-AI commands.
- **JSON stdout**: All commands output JSON to stdout for piping/parsing. Progress messages go to stderr.
- **Relative imports**: Within the package, modules use relative imports (e.g. `from .config import BASE_URL`).

## Development

```bash
pip install -e ".[dev,all-ai,all-sources]"  # Install everything
make check                         # Run lint + type-check + test
make lint                          # Ruff linter + formatter check
make type-check                    # mypy
make test                          # pytest
make format                        # Auto-format with Ruff
```

## Testing

- `pytest` — 170+ tests, ~97% coverage
- All tests run **without network or real API keys** — `conftest.py` has an autouse `clean_env` fixture that strips credentials
- `FakeAIProvider` in `conftest.py` provides deterministic responses for testing
- Tests that need file I/O use `tmp_path` fixture
- Config tests use `importlib.reload(rattle_api.config)` to test env var changes
- Tests import from `rattle_api.*` (e.g. `from rattle_api.provider import get_provider`)

## Adding a New AI Provider

1. Subclass `AIProvider` in `rattle_api/provider.py`
2. Implement `complete(self, prompt, *, system=None, max_tokens=1024, temperature=0.2) -> str`
3. Register in the `PROVIDERS` dict at the bottom of `provider.py`
4. Document env vars in `config.py` comments and `.env.example`

## Adding a New CLI Command

1. Add handler function `cmd_your_command(tenant, args)` in `rattle_api/main.py`
2. Add subparser in `main()` function
3. Register in the `commands` dispatch dict
4. Add tests in `tests/test_main.py`

## Rattle REST API Reference

A comprehensive reference of all **462 REST API operations across 257 paths and 37 resource groups** is at `docs/API_REFERENCE.md`. It is **generated** — never hand-edited.

The generator **fetches the live spec by default** from <https://www.rattleapp.de/docs/api/openapi.json> (published alongside the human docs at `/docs/api/reference`). A checked-in copy goes stale silently, and nobody notices until an agent calls an endpoint that moved:

```bash
python3 scripts/build_api_reference.py            # fetch live, then render  ← do this
python3 scripts/build_api_reference.py --offline  # render from the local copy (CI, no network)
```

Fetching rewrites `docs/openapi.json`, renders `docs/API_REFERENCE.md`, and mirrors both into `skills/rattle-api/references/` — which is the copy the plugin Skill **and the MCP server** actually read, so they stay in lockstep.

**Do not hand-edit `docs/API_REFERENCE.md` or the skill mirror.** Both are generated; edits are destroyed on the next build.

### Adding knowledge the OpenAPI spec does not carry

Some endpoints the skills depend on are **absent from `openapi.json` entirely** — the Safety Reference group (`/safety-logos`, `/hp-statements`, `/safety-notices/signal-words`) is the live source of truth for the `safety_notice` and `hp_statement` EditorJS blocks, and `rattle-safety-notices` / `rattle-ghs-statements` instruct the model to call it *instead of guessing*. It exists nowhere in the spec.

Such content is an **input to the generator, never an edit to its output**:

1. Put the Markdown in `docs/api-supplement/<name>.md`.
2. Register it in the `SUPPLEMENTS` list in `scripts/build_api_reference.py`, declaring its tag and its operations so the resource-group and quick-reference tables stay accurate.
3. Re-run the generator. The section is emitted in its alphabetical slot, and regeneration is lossless and idempotent.

This mechanism exists because it was previously violated. The Safety Reference section and the corrected OCC status (`409 Conflict`, not `412 Precondition Failed`) had been hand-written into the *generated* mirror — so the next legitimate regen, which this file tells you to run, would have silently deleted 197 lines of verified knowledge and reverted the 409 back to 412. `scripts/validate_bundle.py` now fails the build if the two rendered copies ever diverge again.

Consult it before making any API calls to understand available endpoints, required parameters,
request/response shapes, and example JSON. The `RattleClient` in `rattle_api/client.py` is a
thin HTTP wrapper — paths are relative (e.g. `client.get("products")` calls `GET /api/v1/products`).

## Configurator Consulting Knowledge

This codebase embeds deep consulting expertise about building correct product configurators. The knowledge is codified in `rattle_api/knowledge.py` and automatically applied by the AI analysis tasks (`ai-analyse-pricelist`, `ai-suggest-config`).

### The #1 Rule: Explicit Options for ALL Variants

**NEVER build 'base product + add-ons' where the base configuration is implicit.** Every configurable feature MUST have an explicit group with ALL variants as separate options — including the 'standard' variant.

**Why?** Without an explicit option for the standard variant, no BOM item can carry a `usage_subclause` referencing it. The configurator can only activate BOM lines linked to selected options — it cannot remove an implicit baseline.

**Example — WRONG (classic pricelist):**
Product comes with 17" wheels as standard. Option '19 inch' (price: 500). Problem: no BOM item can have a usage_subclause for the 17" wheels because no option represents them.

**Example — CORRECT (BOM-aware):**
Group 'Wheels' (is_multi: false): Option '17 inch' (recommended: true, price: 0), Option '19 inch' (recommended: false, price: 500). BOM: child_part '17-inch wheel assy' with usage_subclauses: [{option_id: <17_inch>, factor: 1.0}]; child_part '19-inch wheel assy' with usage_subclauses: [{option_id: <19_inch>, factor: 1.0}].

### Rattle Data Model

```
Product
  ├── Areas (configurable sections, assigned via /products/{id}/areas)
  │   └── Groups (linked to areas via /groups/{id}/areas, is_multi: single/multi)
  │       └── Options (name, price, key, recommended)
  ├── Parts (physical components)
  │   └── BOM items (parent→child, quantity, usage_subclauses)
  └── Constraints (/constraints + /constraints/rules)
```

- **usage_subclauses** on BOM items: `[{"option_id": 301, "factor": 1.0}]` — when option 301 is selected, this BOM line is active with quantity × factor.
- **Option area-config** (`/options/{id}/area-config`): per-area overrides for option price, description, recommended flag — avoids duplicating groups.
- **Pair-level constraints** (`POST /constraints`): simple option-option exclusions as `{option_id1, option_id2}` pairs. Atomically replaces all pairs for a product (use `X-Constraints-Version` header).
- **Constraint rules** (`POST /constraints/rules`): conditional logic. `rule_json` is a single **object** — `{"requires": [<clause>, …], "invalid": [<option_id>, …]}` — where clauses are AND-folded and each clause is `anyOf` / `allOf` / `groupSelections` over option ids. The legacy array shape `[{"if": …, "then": {"forbid_options": …}}]` is **silently dropped** by the runtime evaluator (`app/utils/constraint_solver._rule_active`), so a rule written that way looks applied but never fires. The constraint DSL is presence-based only: no clause can read an option's numeric amount, so a quantity threshold ("forbid when panels > 20") is **not expressible** as a constraint.

### Configuration Rules

- **explicit-options-for-all-variants**: Every configurable feature MUST have an explicit group with ALL variants as separate options — including the "standard" variant. The standard variant must be a named, selectable option, never an implicit baseline.
- **price-on-option**: Price modifiers belong on the option level (the `price` field), not as separate line items
- **reuse-over-duplicate**: Always prefer reusing existing groups/options over creating duplicates; use option area-config and price-overrides for area-specific differences
- **forbidden-combinations**: Identify and define constraints for invalid option combinations. Use pair-level constraints (`POST /constraints` with `{option_id1, option_id2}` pairs) for simple exclusions, constraint rules (`POST /constraints/rules`) for conditional logic

Note: Not every option maps to BOM parts. Options for software features, services, or cosmetic choices may have no usage_subclauses — that is normal. Usage subclauses are only needed for options that affect the physical bill of materials.

### Anti-Patterns to Detect

- **Implicit Base Configuration** (`implicit-base-config`): Standard features listed without explicit options. Indicators: standard, Grundausstattung, Serienausstattung, im Lieferumfang, serienmäßig
- **Add-on Only Options** (`addon-only-options`): Options listed only as surcharges without stating the default. Indicators: Aufpreis, Zuschlag, zusätzlich, extra, Mehrpreis

### AI Commands for Configuration

- `rattle <tenant> ai-analyse-pricelist <file>` — Analyse a pricelist for configurator anti-patterns (heuristic + AI)
- `rattle <tenant> ai-suggest-config <file>` — Generate BOM-aware configuration recommendations (reuses existing groups, suggests forbidden combinations)
