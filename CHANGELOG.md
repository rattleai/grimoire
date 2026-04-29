# Changelog — Rattle AI Workspace

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
