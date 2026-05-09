<p align="center">
  <img src="rattle_logos/rattle_long_black_transparent.png" width="320" alt="Rattle">
  <br>
  <strong>Grimoire</strong><br>
  <em>AI-native consulting workspace for the Rattle product configurator and technical-documentation system</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/node-18%2B-blue.svg" alt="Node 18+"></a>
</p>

<p align="center">
  <strong>13 skills · 6 subagents · 7 slash commands</strong><br>
  that teach <strong>any AI model</strong> how to produce correct, BOM-aware product configurations<br>
  <em>and</em> CE-compliant technical documentations on the Rattle SaaS platform (rattleapp.de).
</p>

---

## What is Grimoire?

A **portable consulting brain** that covers two domains on the Rattle SaaS platform:

```
        ┌────────────────────┐    ┌────────────────────────────┐
        │   CONFIGURATOR     │    │   TECHNICAL DOCUMENTATION  │
        │  (groups, options, │    │  (Betriebsanleitung, IFU,  │
        │   BOM, constraints)│    │   safety notices, GHS)     │
        └────────────────────┘    └────────────────────────────┘
                  ▲                            ▲
                  └────── shared API + tenant-memory ──────┘
```

Two layers:

1. **AI knowledge layer** — Anthropic-format Skills, Claude Code subagents, slash commands, JSON Schemas, golden I/O examples, the `.claude-plugin/` manifest, and a cross-platform `AGENTS.md`. Any AI model (Claude, GPT-4/5, Llama, Mistral, …) can read these and follow the same workflow.
2. **Python execution layer** — `rattle_api/` package + `rattle` CLI, a reference implementation that wires the same prompts up to OpenAI / Anthropic / Ollama / custom-HTTP providers.

Goal: every AI model gets the same consulting expertise — the #1 configurator rule, the data model, the **11 configuration rules**, anti-patterns, **6 configurator structural checks**, the 15-chapter normative technical-documentation structure (DIN EN ISO 20607, IEC/IEEE 82079-1 **Clause 5**, MRL/MVO) emitted as `doc_type=technical_doc` on writes, **14 technical-documentation audit checks**, the EditorJS `safety_notice` + `hp_statement` block contracts, the **5 ISO 7010 categories** plus the separate CLP/GHS pictogram set, the **32-locale signal-word catalogue**, the **24-locale CLP H/P/EUH catalogue**, and the REST API conventions (OCC `409 Conflict`, the **15 idempotent `ensure_*` operations** across configurator / BOM / documents tiers) — without retraining.

> **Production-grade precision.** Every endpoint, schema, and field name in this bundle is verified byte-for-byte against the rattleapp Pydantic / SQLAlchemy source (round-3 audit, 2026-05-09). Three rounds of audits removed phantom endpoints (`?include=options`, `?search=` on `/documents/templates`), aligned the rule_json shape (`{requires, invalid}` — the legacy `{if, then}` is silently dropped by the runtime evaluator), corrected the OCC error to `409` (was `412`), expanded the operation grammar to 15 ops across 3 tiers, dropped the phantom `datasheet` doc_type, and scoped MDR / IVDR firmly **out** of the machinery scaffold (a future `rattle-techdoc-medical` will own that domain). See `ROADMAP.md` for the prioritised backlog of next-tier expert depth.

## What's inside

```
rattle_api/                    Python execution layer (CLI, RattleClient, providers, prompts)
skills/                        13 Anthropic-format Skills (model-agnostic)
  ├─ Configurator domain (9) ─
  rattle-configurator/         Core consulting knowledge (the #1 rule, rules, anti-patterns)
  rattle-api/                  REST API surface (443+ ops, OpenAPI spec, Safety Reference)
  rattle-pricelist-analysis/   Workflow: scan input for anti-patterns
  rattle-suggest-config/       Workflow: produce BOM-aware recommendation JSON
  rattle-document-templates/   Workflow: build offer/quote/ccms/custom templates
  rattle-bom-builder/          Variant-BOM expert: usage_subclauses + option_scalings + numbered options
  rattle-apply-config/         Workflow: apply a recommendation idempotently
  rattle-audit/                Workflow: scan a live tenant against 6 structural checks
  rattle-tenant-memory/        Per-tenant preferences (file-based, explicit-write only)
  ├─ Technical-documentation domain (4) ─
  rattle-techdoc/              Host skill: 15-chapter structure (DIN EN ISO 20607, IEC 82079-1)
  rattle-safety-notices/       ISO 7010 + ISO 3864-2 + ANSI Z535.6, EditorJS safety_notice block
  rattle-ghs-statements/       CLP H/P/EUH codes + 9 GHS pictograms, EditorJS hp_statement block
  rattle-techdoc-language/     IEC/IEEE 82079-1 §7 quality criteria, mood, tone, terminology
agents/                        6 Claude Code subagents
  rattle-consultant            Senior configurator consultant (strategic decisions)
  rattle-auditor               Live-tenant configurator auditor (read-only)
  rattle-config-builder        Idempotent builder — only agent allowed to write to the API
  rattle-bom-architect         Senior variant-BOM architect (parts → placements → bom_items)
  rattle-techdoc-author        Senior tech writer (inventory → audit → plan → build → translate)
  rattle-techdoc-auditor       Tech-doc auditor (~30 checks, read-only)
commands/                      7 Claude Code slash commands
  /rattle-analyse              Pricelist anti-pattern analysis
  /rattle-suggest-config       Produce a BOM-aware configuration JSON
  /rattle-audit                Audit a live tenant catalogue
  /rattle-build-offer          Build / fix an offer / quote / ccms / custom template
  /rattle-build-bom            Design / fix / validate a variant BOM (usage_subclauses + option_scalings)
  /rattle-build-techdoc        Build a technical documentation from N input manuals
  /rattle-audit-techdoc        Audit a tech-doc template against ISO 20607 / IEC 82079-1 / MRL/MVO
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

## What you can do with it

1. **Drop in 1…N existing pricelists** → get an analysis of every implicit-baseline / addon-only-options anti-pattern, with the questions that block configuration design.
2. **Get a configuration recommendation** → BOM-aware groups + options + parts + constraints, ready to apply via the idempotent `ensure_*` operations.
3. **Audit a live Rattle tenant** → 6 structural checks across products / areas / groups / options / BOM / templates.
4. **Build offer / quote / ccms / custom templates** that honour the doc_type contract (every offer attaches `dynamic:document_configuration`; every quote attaches `dynamic:document_line_items`). The phantom `datasheet` doc_type was removed in the round-3 audit — the real backend registry is `{offer, quote, technical_doc, ccms, custom}` (plus the legacy plurals on read-side filters).
5. **Drop in 1…N existing product manuals (PDF / Word)** → get a coverage matrix against the 15 canonical chapters, an audit of every CRITICAL / HIGH legal gap (missing safety chapter, residual-risks table, declaration of conformity, …), a modular content plan (shared LOTO / signal-word legend / target groups + product-specific blocks), the EditorJS payload for every chapter, and the per-locale translation plan.
6. **Audit a published technical documentation** against ~30 checks (structure + safety-notice rules + GHS rules + language quality).
7. **Author normatively-correct safety notices** — symbol selection + signal-word locale + SAFE-principle structure resolved live from `/api/v1/safety-logos` and `/api/v1/safety-notices/signal-words`.
8. **Author normatively-correct chemical hazard statements** — H/P/EUH codes + GHS pictograms resolved live from `/api/v1/hp-statements`.
9. **Translate any document** to any of the 24+ supported EU locales while preserving normative wording (signal words, CLP statements) byte-identical from the official tables.

## Install

Three install paths. **Pick the one that matches your tooling — they're not mutually exclusive.**

### 1. Claude Code (richest)

Inside Claude Code:

```text
/plugin marketplace add rattleai/grimoire
/plugin install grimoire
```

Restart Claude Code. The slash-command palette gains `/rattle-analyse`, `/rattle-suggest-config`, `/rattle-audit`, `/rattle-build-offer`, `/rattle-build-bom`, `/rattle-build-techdoc`, `/rattle-audit-techdoc`. The 13 skills auto-load when you mention Rattle, technical documentation, safety notices, GHS statements, or variant BOMs (usage_subclauses, option_scalings, numbered options). The 6 subagents (`rattle-consultant`, `rattle-auditor`, `rattle-config-builder`, `rattle-bom-architect`, `rattle-techdoc-author`, `rattle-techdoc-auditor`) become invocable.

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

## The technical-documentation domain

A second normative rule governs every operating manual / Betriebsanleitung the workspace produces:

> **Safety information lives in two places: a global Safety chapter (Chapter 2) AND a phase-specific Safety section (.1) at the start of every life-cycle chapter (4–11).** Never collapse the global safety into the phase-specific safety, and never leave a life-cycle chapter without its own `.1` safety section.

Templates ship as `doc_type=technical_doc` on POST/PUT (the legacy alias `technical_documentation` is accepted only on `GET ?doc_type=…` filters — the create/update validator with `extra="forbid"` rejects it on writes) and follow the **15-chapter normative structure** (Cover · TOC · 1 About · 2 Safety · 3 Product · 4 Transport · 5 Assembly · 6 Commissioning · 7 Operation · 8 Troubleshooting · 9 Maintenance · 10 Modifications · 11 Decommissioning · 12 Conformity · 13 Appendix). All sections are defined in `skills/rattle-techdoc/references/chapter-reference.md`.

Two block types replace prose for normative content:

- **`safety_notice`** (ISO 3864-2 / ANSI Z535.6) — `level / title / hazard / consequences[] / avoidance[] / isoSymbol`. Symbols resolved live from `GET /api/v1/safety-logos` (no fallback to a default `W001_general_warning_sign.svg`).
- **`hp_statement`** (CLP EC 1272/2008) — `codes[]` validated live via `GET /api/v1/hp-statements/{code}`. Statement text and GHS pictogram are server-resolved per locale; never hand-typed or AI-translated. Translations are ECHA-traceable to Annex III/IV/VI on EUR-Lex.

**14 audit checks** (CRITICAL / HIGH / MEDIUM / LOW) — `missing-safety-chapter`, `missing-phase-safety-section`, `missing-residual-risks-table`, `missing-declaration-of-conformity`, `default-fallback-symbol`, `mismatched-ghs-pictogram`, `unknown-hp-code`, `unlabeled-original-language`, MRL Anh. I §1.7.4 lettered-content gaps, … — cover everything an MRL/MVO conformity assessment expects. The **MVO Article 10(7) digital-provision rule** (consumer-machinery paper mandate, ≥10 year online availability, paper-on-request within one month) is encoded for the cut-over on 20 January 2027.

> **MDR scope mismatch.** The 15-chapter scaffold targets **machinery** (MRL 2006/42/EC, MVO (EU) 2023/1230). It is **not** an MDR-compliant Instructions for Use (IFU) — that domain (ISO 20417 + ISO 15223-1 + IEC 62366-1 usability) is owned by a future `rattle-techdoc-medical` skill. The agents are wired to refuse the machinery scaffold and surface the scope mismatch when handed a medical device disguised as machinery (sterilising washer, powered hospital bed, UV cabinet).

Full reasoning in `skills/rattle-techdoc/SKILL.md` and `skills/rattle-techdoc/references/legal-basis.md`.

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
- [`ROADMAP.md`](ROADMAP.md) — prioritised backlog (P0/P1/P2) of skills, agents, and slash commands needed to close the value-chain gaps the PR #14 audits identified.
- [`PUBLISHING.md`](PUBLISHING.md) — how to release to npm, PyPI, and the Claude Code marketplace.
- [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) — full Rattle REST API reference (443 operations).
- [`SETUP.md`](SETUP.md) — beginner-friendly setup guide.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution guidelines.
- [`SECURITY.md`](SECURITY.md) — security policy.
- [`CHANGELOG.md`](CHANGELOG.md) — version history.

## License

[MIT](LICENSE)
