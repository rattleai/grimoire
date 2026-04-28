<p align="center">
  <img src="rattle_logos/rattle_long_black_transparent.png" width="320" alt="Rattle">
  <br>
  <strong>Rattle AI Workspace</strong><br>
  <em>AI-native workspace for the Rattle product configurator</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/node-18%2B-blue.svg" alt="Node 18+"></a>
</p>

<p align="center">
  Skills, subagents, slash commands, and rules that teach <strong>any AI model</strong><br>
  how to produce correct, BOM-aware product configurations on the Rattle SaaS platform (rattleapp.de).
</p>

---

## What this is

An **AI-native workspace** — a bundle of model-agnostic knowledge artifacts plus a thin Python execution layer. Two layers:

1. **AI knowledge layer** — Anthropic-format Skills, Claude Code subagents, slash commands, `.claude-plugin/` manifest, and a cross-platform `AGENTS.md`. Any AI model (Claude, GPT-4/5, Llama, Mistral, …) can read these and follow the workflow.
2. **Python execution layer** — `rattle_api/` package + `rattle` CLI, a reference implementation that wires the same prompts up to OpenAI / Anthropic / Ollama / custom-HTTP providers.

Goal: give every AI model the same consulting expertise — the #1 rule, the data model, configuration rules, anti-patterns, structural checks, REST API conventions — without retraining.

## What's inside

```
rattle_api/                    Python execution layer (CLI, RattleClient, providers, prompts)
skills/                        Anthropic-format Skills (model-agnostic)
  rattle-configurator/         Core consulting knowledge (the #1 rule, rules, anti-patterns)
  rattle-api/                  REST API surface (443 ops, 245 paths, 36 tags; OpenAPI spec, client patterns)
  rattle-pricelist-analysis/   Workflow: scan input for anti-patterns
  rattle-suggest-config/       Workflow: produce BOM-aware recommendation JSON
  rattle-document-templates/   Workflow: build offer/datasheet templates
agents/                        Claude Code subagents (consultant, auditor, config-builder)
commands/                      Claude Code slash commands (/rattle-analyse, /rattle-audit, …)
.claude-plugin/                Plugin + marketplace manifest (Claude Code distribution)
AGENTS.md                      Cross-platform agent rules (Cursor, Codex, Aider, Continue)
CLAUDE.md                      Claude-Code-specific project instructions
package.json + bin/            npm installer (npx @rattle/ai-workspace install)
pyproject.toml                 PyPI distribution (pip install rattle-ai-workspace)
docs/API_REFERENCE.md          Full Rattle REST reference (also bundled into the API skill)
memory/                        Per-tenant style preferences (gitignored)
tests/                         170+ tests, ~97% coverage
```

## Install

Three distribution channels — pick the one that matches your tooling.

### 1. Claude Code plugin (richest)

```bash
# In Claude Code:
/plugin marketplace add mngapps/rattle_api
/plugin install rattle-ai-workspace
```

Skills, subagents, and slash commands become available. The `/rattle-analyse`, `/rattle-suggest-config`, `/rattle-audit`, and `/rattle-build-offer` commands appear in the palette.

### 2. NPM (works with Cursor, Codex, Aider, Continue, plain Claude.ai)

```bash
# Drop skills/, agents/, commands/, AGENTS.md, .claude-plugin/ into the current project:
npx @rattle/ai-workspace install

# Or into a specific project, only under .claude/:
npx @rattle/ai-workspace install --target ./my-app --layout claude

# Or machine-wide (~/.claude/):
npx @rattle/ai-workspace install --layout user

# Preview without copying:
npx @rattle/ai-workspace install --dry-run
```

Run with `--help` for all options. Idempotent — re-running just refreshes files.

### 3. PyPI (Python CLI execution layer)

```bash
git clone https://github.com/mngapps/rattle_api.git
cd rattle_api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,all-ai,all-sources]"
```

Then configure `.env`:

```bash
cp .env.example .env
# Edit .env — RATTLE_API_KEY_<TENANT>, AI_PROVIDER, OPENAI_API_KEY / ANTHROPIC_API_KEY / OLLAMA_BASE_URL, …
```

Verify:

```bash
rattle <tenant> test-connection
```

## How any AI model uses this

Every Skill is a self-contained Markdown bundle with a `SKILL.md` (frontmatter `name` + `description`) and optional `references/`, `scripts/`. Models load them by reading the frontmatter, deciding the skill is relevant, then reading the body and references on demand.

The flow for a typical engagement:

1. User asks: *"Analyse this pricelist for our `acme` tenant."*
2. Agent loads `skills/rattle-pricelist-analysis/SKILL.md` (and `rattle-configurator` automatically).
3. Agent runs `scripts/detect_anti_patterns.py pricelist.xlsx` for deterministic keyword detection.
4. Agent calls its LLM with the prompt template documented in `system-prompts.md` to do the structural pass.
5. Agent merges findings, prioritises `implicit-base-config` first, presents to the user.
6. User asks: *"OK, generate a configuration."*
7. Agent loads `skills/rattle-suggest-config/SKILL.md`, fetches existing groups (via the Python CLI or its own HTTP client), produces the canonical recommendation JSON.
8. User asks to apply it. Agent delegates to `rattle-config-builder` which calls `ensure_*` operations idempotently against the live API.

The Python CLI `rattle <tenant> ai-analyse-pricelist` and `ai-suggest-config` subcommands implement steps 3-7 directly — useful when you want a one-shot terminal command instead of an agent loop.

## The #1 rule

> **Never build "base product + add-ons" where the base configuration is implicit.** Every configurable feature MUST have an explicit group with ALL variants as separate options — including the "standard" / default variant.

The Rattle BOM is driven by `usage_subclauses` on BOM items linking parts to options. If the standard variant has no option, no BOM line can reference it, and the configurator can't toggle the standard parts on or off.

Wrong:

```
Product: Widget Pro (17" wheels standard)
Option: 19 inch wheels (+500€)
```

Correct:

```
Group "Wheels" (is_multi=false):
  Option "17 inch" (recommended=true, price=0)
  Option "19 inch" (recommended=false, price=500)
BOM:
  child_part "17-inch wheel assy", usage_subclauses: [{option_id: <17_inch>, factor: 1.0}]
  child_part "19-inch wheel assy", usage_subclauses: [{option_id: <19_inch>, factor: 1.0}]
```

Full reasoning + 11 more rules in `skills/rattle-configurator/references/configuration-rules.md`.

## Python CLI commands

Every command writes JSON to stdout, progress to stderr, no interactive prompts.

| Command | Description |
|---|---|
| `rattle <tenant> test-connection` | Verify API connectivity |
| `rattle <tenant> list-sources` | List source files for a tenant |
| `rattle <tenant> ai-analyse-pricelist <file>` | Analyse a pricelist for anti-patterns |
| `rattle <tenant> ai-suggest-config <file>` | Generate BOM-aware configuration recommendation |
| `rattle <tenant> ai-describe` | Generate AI product descriptions |
| `rattle <tenant> ai-classify` | Classify products with AI |
| `rattle <tenant> ai-transform <src> <tgt> <file>` | Transform interchange data |
| `rattle <tenant> ai-analyse` | Custom data quality / analysis |
| `rattle <tenant> ai-providers` | List configured AI providers |
| `rattle <tenant> memory show / edit / set-preference / record-decision` | Tenant memory ops |

Switch AI providers with one env var: `AI_PROVIDER=openai|anthropic|ollama|custom`.

## Tenant memory

Per-tenant style preferences live under `memory/<tenant>/profile.md` (gitignored). Captured preferences override default rules:

```markdown
# acme — tenant preferences

## Preferences
- **custom-keys**: never
- **option-standard-variant**: always present, price 0, recommended=true

## Offer documents
- doc_type: `offer`
- Required chapters: Product Overview + Configuration (dynamic:document_configuration)
```

The `TenantMemory` class auto-injects this into every system prompt. Writes are explicit-only (`rattle <tenant> memory set-preference …`); tasks never write silently. Full docs: `memory/README.md`.

## Development

```bash
make check         # lint + type-check + test
make lint          # ruff
make type-check    # mypy
make test          # pytest (170+ tests, ~97% coverage)
make format        # ruff format
```

Pre-commit:

```bash
pre-commit install
```

## Adding new knowledge

1. Edit the **Markdown reference** under `skills/rattle-configurator/references/` — it is the source of truth.
2. Mirror the change in `rattle_api/knowledge.py` so the Python CLI stays in sync. Markdown wins on conflicts.
3. Run `make test` — the prompt-builder tests catch most drift.
4. If you add a new rule, cross-reference it from any matching anti-pattern and structural check.

Full conventions: `AGENTS.md` (cross-platform) and `CLAUDE.md` (Claude-Code-specific).

## Documentation

- [`AGENTS.md`](AGENTS.md) — cross-platform agent rules and where the knowledge lives.
- [`CLAUDE.md`](CLAUDE.md) — Claude Code project instructions.
- [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) — full Rattle REST API reference (443 operations across 245 paths). Regenerate with `python3 scripts/build_api_reference.py` after replacing `docs/openapi.json`.
- [`SETUP.md`](SETUP.md) — beginner-friendly setup guide.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution guidelines.
- [`SECURITY.md`](SECURITY.md) — security policy.
- [`CHANGELOG.md`](CHANGELOG.md) — version history.

## License

[MIT](LICENSE)
