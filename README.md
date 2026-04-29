<p align="center">
  <img src="rattle_logos/rattle_long_black_transparent.png" width="320" alt="Rattle">
  <br>
  <strong>Grimoire</strong><br>
  <em>AI-native consulting workspace for the Rattle product configurator</em>
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

## What is Grimoire?

A **portable consulting brain** for the Rattle product configurator. Two layers:

1. **AI knowledge layer** — Anthropic-format Skills, Claude Code subagents, slash commands, JSON Schemas, golden I/O examples, the `.claude-plugin/` manifest, and a cross-platform `AGENTS.md`. Any AI model (Claude, GPT-4/5, Llama, Mistral, …) can read these and follow the same workflow.
2. **Python execution layer** — `rattle_api/` package + `rattle` CLI, a reference implementation that wires the same prompts up to OpenAI / Anthropic / Ollama / custom-HTTP providers.

Goal: every AI model gets the same consulting expertise — the #1 rule, the data model, configuration rules, anti-patterns, structural checks, REST API conventions — without retraining.

## What's inside

```
rattle_api/                    Python execution layer (CLI, RattleClient, providers, prompts)
skills/                        8 Anthropic-format Skills (model-agnostic)
  rattle-configurator/         Core consulting knowledge (the #1 rule, rules, anti-patterns)
  rattle-api/                  REST API surface (443 ops, OpenAPI spec, client patterns)
  rattle-pricelist-analysis/   Workflow: scan input for anti-patterns
  rattle-suggest-config/       Workflow: produce BOM-aware recommendation JSON
  rattle-document-templates/   Workflow: build offer/datasheet templates
  rattle-apply-config/         Workflow: apply a recommendation idempotently
  rattle-audit/                Workflow: scan a live tenant against 6 structural checks
  rattle-tenant-memory/        Per-tenant preferences (file-based, explicit-write only)
agents/                        3 Claude Code subagents (consultant, auditor, config-builder)
commands/                      4 Claude Code slash commands (/rattle-analyse, /rattle-audit, …)
schemas/                       JSON Schemas for every output contract
examples/                      Synthetic golden I/O for every workflow
.claude-plugin/                Plugin + marketplace manifest (Claude Code distribution)
AGENTS.md                      Cross-platform agent rules (Cursor, Codex, Aider, Continue)
CLAUDE.md                      Claude-Code-specific project instructions
package.json + bin/grimoire.mjs npm installer (npx @rattleai/grimoire install)
pyproject.toml                 PyPI distribution (pip install grimoire)
docs/API_REFERENCE.md          Full Rattle REST reference (also bundled into the API skill)
memory/                        Per-tenant style preferences (gitignored)
tests/                         262 tests, ~97% coverage
```

## Install

Three install paths. **Pick the one that matches your tooling — they're not mutually exclusive.**

### 1. Claude Code (richest)

Inside Claude Code:

```text
/plugin marketplace add rattleai/grimoire
/plugin install grimoire
```

Restart Claude Code. The slash-command palette gains `/rattle-analyse`, `/rattle-suggest-config`, `/rattle-audit`, `/rattle-build-offer`. The 8 skills auto-load when you mention Rattle. The 3 subagents (`rattle-consultant`, `rattle-auditor`, `rattle-config-builder`) become invocable.

### 2. NPM (Cursor, Codex, Aider, Continue, plain Claude.ai, any AGENTS.md tool)

The `npx` installer copies the same skills + subagents + commands + schemas + examples + AGENTS.md into your project, ready for any agent that reads `AGENTS.md` (the cross-platform standard).

```bash
# Drop everything into the current project root:
npx @rattleai/grimoire install

# Or only under .claude/ (project-local Claude Code layout):
npx @rattleai/grimoire install --layout claude

# Or machine-wide for every Claude Code session:
npx @rattleai/grimoire install --layout user

# Preview without copying:
npx @rattleai/grimoire install --dry-run
```

Idempotent — re-running just refreshes files. Run with `--help` for all options.

> Until the package is published to npm, install directly from the repo:
> ```bash
> git clone https://github.com/rattleai/grimoire.git
> node grimoire/bin/grimoire.mjs install --target ./my-project
> ```

### 3. PyPI (Python CLI execution layer)

For terminal-driven workflows that call your AI provider directly:

```bash
pip install grimoire[all-ai,all-sources]
cp .env.example .env
# Edit .env — RATTLE_API_KEY_<TENANT>, AI_PROVIDER, OPENAI_API_KEY / ANTHROPIC_API_KEY, …

rattle <tenant> test-connection
rattle <tenant> ai-analyse-pricelist <file>
rattle <tenant> ai-suggest-config <file>
```

Note: the CLI is still called `rattle` (it's the Rattle API CLI). `grimoire` is the **distribution name** on PyPI; `pip install grimoire` installs the `rattle` console script along with the workspace.

## How any AI model uses this

Every Skill is a self-contained Markdown bundle with a `SKILL.md` (frontmatter `name` + `description`) and optional `references/` and `scripts/`. Models load them by reading the frontmatter, deciding the skill is relevant, then reading the body and references on demand.

A typical engagement:

1. User: *"Analyse this pricelist for our `acme` tenant."*
2. Agent loads `skills/rattle-pricelist-analysis/SKILL.md` (+ `rattle-configurator` automatically).
3. Agent runs `scripts/detect_anti_patterns.py pricelist.xlsx` for deterministic keyword detection.
4. Agent calls its LLM with the prompt template documented in `system-prompts.md`.
5. Agent merges findings, prioritises `implicit-base-config` first, presents to the user.
6. User: *"OK, generate a configuration."*
7. Agent loads `skills/rattle-suggest-config/SKILL.md`, fetches existing groups, produces the canonical recommendation JSON.
8. User: *"Apply it."* Agent delegates to `rattle-config-builder` which calls `ensure_*` operations idempotently against the live API. `validate_recommendation.py` runs first; the agent never writes if validation fails.

The Python CLI implements steps 3–7 directly when you want a one-shot terminal command instead of an agent loop.

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

The `TenantMemory` class auto-injects this into every system prompt. Writes are explicit-only (`rattle <tenant> memory set-preference …`); tasks never write silently. Full docs: `memory/README.md` and `skills/rattle-tenant-memory/SKILL.md`. A starter template lives at `examples/tenant-profile.md`.

## Development

```bash
make check         # lint + type-check + 262 tests
make lint          # ruff
make type-check    # mypy
make test          # pytest
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

- [`AGENTS.md`](AGENTS.md) — cross-platform agent rules and the full knowledge map.
- [`CLAUDE.md`](CLAUDE.md) — Claude Code project instructions.
- [`PUBLISHING.md`](PUBLISHING.md) — how to release to npm, PyPI, and the Claude Code marketplace.
- [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) — full Rattle REST API reference (443 operations).
- [`SETUP.md`](SETUP.md) — beginner-friendly setup guide.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution guidelines.
- [`SECURITY.md`](SECURITY.md) — security policy.
- [`CHANGELOG.md`](CHANGELOG.md) — version history.

## License

[MIT](LICENSE)
