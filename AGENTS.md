# AGENTS.md — Rattle AI Workspace

This file follows the [agents.md](https://agents.md) convention so any AI agent (Claude Code, Cursor, Codex, Aider, Continue, Cline, etc.) can pick up the project conventions without bespoke configuration. Claude Code users get this same content layered with `CLAUDE.md`.

## What this repo is

An **AI-native workspace** for the Rattle product configurator (rattleapp.de). It bundles model-agnostic knowledge (Anthropic-format Skills under `skills/`), Claude-specific subagents and slash commands, and a Python CLI as one execution layer. The goal is that any AI model — Claude, GPT-4/5, Llama, Mistral — can produce correct, BOM-aware Rattle configurations by reading this repo.

## Where the knowledge lives

When the user asks anything Rattle-related, **read these files before answering**:

| File | Purpose |
|---|---|
| `skills/rattle-configurator/SKILL.md` | The #1 rule + workflow entry point. Always load this first. |
| `skills/rattle-configurator/references/data-model.md` | Full schema for every entity. |
| `skills/rattle-configurator/references/configuration-rules.md` | 12 configuration rules with rationales. |
| `skills/rattle-configurator/references/anti-patterns.md` | 4 anti-patterns with indicator keywords. |
| `skills/rattle-configurator/references/structural-checks.md` | 6 live-tenant audit checks. |
| `skills/rattle-configurator/references/system-prompts.md` | Canonical prompt templates for any LLM. |
| `skills/rattle-api/SKILL.md` | REST API conventions (auth, pagination, errors). |
| `skills/rattle-api/references/api-reference.md` | Full reference for 443 operations across 245 paths (36 tags). Generated from `openapi.json` by `scripts/build_api_reference.py`. |
| `skills/rattle-api/references/openapi.json` | Raw OpenAPI 3.x spec. |
| `skills/rattle-api/references/client-patterns.md` | List-all, idempotent ensure, multipart upload, optimistic concurrency. |
| `skills/rattle-pricelist-analysis/SKILL.md` | Workflow: analyse a pricelist for anti-patterns. Includes `scripts/detect_anti_patterns.py`. |
| `skills/rattle-suggest-config/SKILL.md` | Workflow: produce a BOM-aware config recommendation. |
| `skills/rattle-document-templates/SKILL.md` | Workflow: build offer/datasheet templates. |
| `skills/rattle-apply-config/SKILL.md` | Workflow: apply a recommendation idempotently via 7 `ensure_*` ops. Includes `scripts/validate_recommendation.py`. |
| `skills/rattle-audit/SKILL.md` | Workflow: scan a live tenant against the 6 structural checks. Includes `scripts/audit_runner.py`. |
| `skills/rattle-tenant-memory/SKILL.md` | Per-tenant preferences, decisions, audit history (file-based, explicit-write only). |
| `schemas/recommendation.schema.json` | JSON Schema for `rattle-suggest-config` output. |
| `schemas/audit-findings.schema.json` | JSON Schema for `rattle-audit` output. |
| `schemas/offer-template.schema.json` | JSON Schema for `rattle-document-templates` output. |
| `schemas/apply-operations.schema.json` | JSON Schema for `rattle-apply-config` operations array. |
| `examples/` | Synthetic golden I/O for every workflow (Widget Pro, acme tenant). |

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

## Distribution

This workspace is installable three ways:

1. **Claude Code plugin** (richest):
   ```
   /plugin marketplace add mngapps/rattle_api
   /plugin install rattle-ai-workspace
   ```

2. **NPM** (drops skills + AGENTS.md into any project):
   ```
   npx @rattle/ai-workspace install
   ```

3. **PyPI** (Python CLI execution layer):
   ```
   pip install rattle-ai-workspace[all-ai,all-sources]
   rattle <tenant> ai-analyse-pricelist <file>
   ```

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
