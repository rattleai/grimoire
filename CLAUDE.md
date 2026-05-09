# Rattle AI Workspace

AI-native workspace for the Rattle product configurator (rattleapp.de). The repo is **two layers**:

1. **AI knowledge layer** — Anthropic-format Skills (`skills/`), Claude Code subagents (`agents/`), slash commands (`commands/`), the `.claude-plugin/` manifest, and the cross-platform `AGENTS.md`. This is the part any AI model can read and use, regardless of language or runtime.
2. **Python execution layer** — `rattle_api/` package + `rattle` CLI, which calls a configured AI provider (OpenAI / Anthropic / Ollama / custom HTTP) using the same prompts the Skills describe. One reference implementation; non-Python clients can build their own using the Skills.

**Read first:** when answering anything Rattle-related, load `skills/rattle-configurator/SKILL.md`. It encodes the #1 rule, the data model, configuration rules, anti-patterns, and structural checks. The cross-platform `AGENTS.md` lists every reference file with a one-line purpose.

## Knowledge layer (AI-native artifacts)

| Path | Purpose |
|---|---|
| `.claude-plugin/plugin.json` + `marketplace.json` | Claude Code plugin / marketplace manifest. Installable via `/plugin marketplace add rattleai/grimoire`. |
| `skills/rattle-configurator/` | Core consulting knowledge. **Always load first.** |
| `skills/rattle-api/` | REST API surface (auth, pagination, 443 operations across 245 paths, OpenAPI spec). |
| `skills/rattle-pricelist-analysis/` | Workflow: scan input for anti-patterns. Includes `scripts/detect_anti_patterns.py`. |
| `skills/rattle-suggest-config/` | Workflow: produce BOM-aware configuration recommendation JSON. |
| `skills/rattle-document-templates/` | Workflow: build offer/datasheet templates honouring the doc_type contract. |
| `skills/rattle-techdoc/` | Workflow: build full technical documentations (`doc_type=technical_documentation`). 15-chapter normative structure (DIN EN ISO 20607, IEC/IEEE 82079-1). Includes `scripts/inventory_techdocs.py` and reference files for chapters, audit checks, EditorJS blocks, legal basis. |
| `skills/rattle-safety-notices/` | Knowledge: ISO 7010 + ISO 3864-2 + ANSI Z535.6 safety notices. EditorJS `safety_notice` block contract, signal-word locales (31 languages), 6 ISO 7010 categories, SAFE-principle authoring. |
| `skills/rattle-ghs-statements/` | Knowledge: CLP Regulation EC 1272/2008 H/P/EUH statements + 9 GHS pictograms. EditorJS `hp_statement` block contract, 24-locale resolution, combined and enhanced statements. |
| `skills/rattle-techdoc-language/` | Knowledge: language, tone, mood, terminology rules per IEC/IEEE 82079-1 §7. Imperative-mood instructions, original-language obligation, MVO 2023/1230 digital provision. |
| `skills/rattle-apply-config/` | Workflow: apply a recommendation idempotently. Includes `scripts/validate_recommendation.py`. |
| `skills/rattle-audit/` | Workflow: scan a live tenant against the 6 structural checks. Includes `scripts/audit_runner.py`. |
| `skills/rattle-tenant-memory/` | Per-tenant preferences and decisions (file-based, explicit-write only). |
| `skills/rattle-bom-builder/` | Variant-BOM expert: usage_subclauses DSL, option_scalings (legacy / ratio / range), numbered-option scaling patterns, alt_group + priority alternates, ghost depth-transparency, BOM explosion semantics. Includes `scripts/validate_variant_bom.py` and 6 reference docs. |
| `schemas/` | JSON Schemas for the 4 output contracts (recommendation, audit-findings, offer-template, apply-operations). |
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

A comprehensive reference of all **443 REST API operations across 245 paths and 36 resource groups** is at `docs/API_REFERENCE.md`. It is **generated** from `docs/openapi.json` by `scripts/build_api_reference.py` — re-run that script whenever the spec is replaced:

```bash
python3 scripts/build_api_reference.py
```

The script also mirrors the rendered Markdown and the spec into `skills/rattle-api/references/` so the plugin Skill stays in sync. **Do not hand-edit `docs/API_REFERENCE.md`** — changes are overwritten on the next build.

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
- **Constraint rules** (`POST /constraints/rules`): conditional logic with `rule_json: [{"if": {"option_selected": X}, "then": {"forbid_options": [Y, Z]}}]`.

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
