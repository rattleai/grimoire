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
  <strong>14 skills · 6 subagents · 8 slash commands · 1 MCP server</strong><br>
  Point <strong>any AI model</strong> at your pricelist, spreadsheet or ERP export —<br>
  get correct, BOM-aware entities in the Rattle CPQ configurator (rattleapp.de).
</p>

---

## The one-paragraph version

You have a pricelist. It is a spreadsheet of surcharges, written by a salesperson, in German, with a column nobody can explain. Rattle needs explicit groups, explicit options for **every** variant, parts wired to options through `usage_subclauses`, and constraints for the combinations that can't be built. Getting from one to the other is the whole job — and it is the job Grimoire teaches an AI to do.

```
  your spreadsheet          rattle-ingest          rattle-pricelist-analysis
  ─────────────────   ──▶   ─────────────    ──▶   ────────────────────────
  columns nobody            column roles,          anti-patterns, blockers
  agrees on                 sheet shape,           ("no standard variant
                            source-mapping.json     is stated anywhere")
                                                              │
      live Rattle tenant       rattle-apply-config      rattle-suggest-config
      ──────────────────  ◀──  ───────────────────  ◀──  ────────────────────
      groups · options ·       idempotent ensure_*        groups, options, BOM
      parts · constraints      (re-run = no-op)           rules, constraints
```

Every arrow is a skill. Every artifact between them is a JSON Schema you can validate. Nothing is a black box, and nothing is invented — where your data is silent, the chain **stops and asks** rather than guessing.

## What is Grimoire?

A **portable consulting brain** covering two domains on the Rattle CPQ platform:

```
        ┌────────────────────┐    ┌────────────────────────────┐
        │   CONFIGURATOR     │    │   TECHNICAL DOCUMENTATION  │
        │  (groups, options, │    │  (Betriebsanleitung, IFU,  │
        │   BOM, constraints)│    │   safety notices, GHS)     │
        └────────────────────┘    └────────────────────────────┘
                  ▲                            ▲
                  └────── shared API + tenant-memory ──────┘
```

Three layers:

1. **AI knowledge layer** — Anthropic-format Skills, subagents, slash commands, JSON Schemas, golden I/O examples, the `.claude-plugin/` manifest, and a cross-platform `AGENTS.md`. Any AI model (Claude, GPT, Llama, Mistral, …) can read these and follow the same workflow.
2. **MCP server** — `mcp/server.mjs`. Zero dependencies, zero drift. Gives Cursor, Windsurf, Claude Desktop and ChatGPT the same knowledge *and* live API access that Claude Code gets natively.
3. **Python execution layer** — `rattle_api/` + the `rattle` CLI, a reference implementation wiring the same prompts to OpenAI / Anthropic / Ollama / custom-HTTP providers.

Goal: every AI model gets the same consulting expertise — the #1 configurator rule, the data model, the **11 configuration rules**, anti-patterns, **6 configurator structural checks**, the 15-chapter normative technical-documentation structure (DIN EN ISO 20607, IEC/IEEE 82079-1 **Clause 5**, MRL/MVO) emitted as `doc_type=technical_doc` on writes, **14 technical-documentation audit checks**, the EditorJS `safety_notice` + `hp_statement` block contracts, the **5 ISO 7010 categories** plus the separate CLP/GHS pictogram set, the **32-locale signal-word catalogue**, the **24-locale CLP H/P/EUH catalogue**, and the REST API conventions (OCC `409 Conflict`, the **15 idempotent `ensure_*` operations** across configurator / BOM / documents tiers) — without retraining.

> **Production-grade precision.** Every endpoint, schema, and field name in this bundle is verified byte-for-byte against the rattleapp Pydantic / SQLAlchemy source (round-3 audit, 2026-05-09). Three rounds of audits removed phantom endpoints (`?include=options`, `?search=` on `/documents/templates`), aligned the rule_json shape (`{requires, invalid}` — the legacy `{if, then}` is silently dropped by the runtime evaluator), corrected the OCC error to `409` (was `412`), expanded the operation grammar to 15 ops across 3 tiers, dropped the phantom `datasheet` doc_type, and scoped MDR / IVDR firmly **out** of the machinery scaffold (a future `rattle-techdoc-medical` will own that domain). See `ROADMAP.md` for the prioritised backlog of next-tier expert depth.

## What's inside

```
skills/                        14 Anthropic-format Skills (model-agnostic)
  ├─ Configurator domain (10) ─
  rattle-ingest/               ★ Raw file → column roles → source-mapping.json. The FIRST link.
  rattle-configurator/         Core consulting knowledge (the #1 rule, rules, anti-patterns)
  rattle-api/                  REST API surface (462 ops, OpenAPI spec)
  rattle-pricelist-analysis/   Workflow: scan input for anti-patterns
  rattle-suggest-config/       Workflow: produce BOM-aware recommendation JSON
  rattle-bom-builder/          Variant-BOM expert: usage_subclauses + option_scalings + numbered options
  rattle-apply-config/         Workflow: apply a recommendation idempotently
  rattle-audit/                Workflow: scan a live tenant against 6 structural checks
  rattle-document-templates/   Workflow: build offer/quote/ccms/custom templates
  rattle-tenant-memory/        Per-tenant preferences (file-based, explicit-write only)
  ├─ Technical-documentation domain (4) ─
  rattle-techdoc/              Host skill: 15-chapter structure (DIN EN ISO 20607, IEC 82079-1)
  rattle-safety-notices/       ISO 7010 + ISO 3864-2 + ANSI Z535.6, EditorJS safety_notice block
  rattle-ghs-statements/       CLP H/P/EUH codes + 9 GHS pictograms, EditorJS hp_statement block
  rattle-techdoc-language/     IEC/IEEE 82079-1 Clause 5 quality criteria, mood, tone, terminology
agents/                        6 subagents (each preloads its skills via `skills:` frontmatter)
  rattle-consultant            Senior configurator consultant (orchestrates; the usual entry point)
  rattle-auditor               Live-tenant configurator auditor — read-only, enforced by allowlist
  rattle-config-builder        Idempotent builder — the ONLY agent allowed to write to the API
  rattle-bom-architect         Senior variant-BOM architect (parts → placements → bom_items)
  rattle-techdoc-author        Senior tech writer (inventory → audit → plan → build → translate)
  rattle-techdoc-auditor       Tech-doc auditor (14 checks) — read-only, enforced by allowlist
commands/                      8 slash commands
  /rattle-ingest               ★ Map a raw spreadsheet / ERP export onto Rattle entities
  /rattle-analyse              Pricelist anti-pattern analysis
  /rattle-suggest-config       Produce a BOM-aware configuration JSON
  /rattle-audit                Audit a live tenant catalogue
  /rattle-build-bom            Design / fix / validate a variant BOM
  /rattle-build-offer          Build / fix an offer / quote / ccms / custom template
  /rattle-build-techdoc        Build a technical documentation from N input manuals
  /rattle-audit-techdoc        Audit a tech-doc against ISO 20607 / IEC 82079-1 / MRL/MVO
mcp/server.mjs                 ★ Rattle MCP server — zero deps, zero drift, read-only by default
schemas/                       6 JSON Schemas — one per output contract, all CI-enforced
examples/                      Golden I/O for every workflow; every file validates against its schema
scripts/validate_bundle.py     Bundle gate: manifests, frontmatter, schemas, examples, bytecode
rattle_api/                    Python execution layer (CLI, RattleClient, providers, prompts)
.claude-plugin/                Plugin + marketplace manifest (Claude Code distribution)
.mcp.json                      MCP wiring for Cursor / Windsurf / Claude Desktop
AGENTS.md                      Cross-platform agent rules (Cursor, Codex, Aider, Continue)
docs/API_REFERENCE.md          Full Rattle REST reference (462 operations)
memory/                        Per-tenant style preferences (gitignored)
tests/                         262 tests, ~97% coverage
```

## What you can do with it

0. **Drop in a raw spreadsheet / CSV / ERP export nobody has mapped yet** → get a reviewable column→entity mapping, the detected sheet shape, and a blocker for every hole in the data. This is the step that used to be missing, and it is where most configurator projects actually fail.
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

Pick the path that matches your tooling — they're not mutually exclusive.

| Path | Best for | Needs publishing? |
|---|---|---|
| **1. Claude Code plugin** | Claude Code users | **No** — installs straight from GitHub |
| **2. MCP server** | Cursor, Windsurf, Claude Desktop, ChatGPT | **No** — clone and point at it |
| **3. npx installer** | Any AGENTS.md tool (Codex, Aider, Continue) | Yes — or clone and run the script directly |
| **4. Python CLI** | Terminal-driven, one-shot commands | Yes — or `pip install -e .` from a clone |

Paths **1 and 2 work today with nothing published**. That is deliberate: the bundle is text and a zero-dependency script, so a git clone is a complete install.

### 1. Claude Code (richest)

```text
/plugin marketplace add rattleai/grimoire
/plugin install grimoire
```

The plugin **prompts you for your Rattle API key at install** and stores it in your OS keychain — there is no `.env` to hand-edit. It also asks for your base URL, default tenant, and whether the MCP server may write to your live tenant (**off** by default).

Restart Claude Code and you get: 8 slash commands, 14 auto-loading skills, 6 invocable subagents, and the `rattle` MCP server wired up with your key.

Nothing needs to be published for this to work — Claude Code reads `.claude-plugin/marketplace.json` directly from the repo's default branch. Push to `main` and every user's next `/plugin update grimoire` picks it up.

To try a branch before merging it, or to hack on the bundle locally:

```bash
git clone https://github.com/rattleai/grimoire.git
```
```text
/plugin marketplace add ./grimoire
/plugin install grimoire
```

### 2. MCP — Cursor, Windsurf, Claude Desktop, ChatGPT

The MCP server is how clients **without** a native Skills mechanism get the same system. It hands them the skills *and* live API access:

| Tool | What it does |
|---|---|
| `rattle_knowledge_list` / `rattle_knowledge_get` | Serves every skill, reference and schema — Skills for clients that don't have Skills |
| `rattle_api_search` | Finds the right endpoint among 462 operations without loading a 7,000-line reference into context |
| `rattle_request` | Calls any Rattle endpoint. Read-only unless you explicitly enable writes |

Clone once — there is nothing to install, and no npm dependencies to resolve:

```bash
git clone https://github.com/rattleai/grimoire.git
```

Then add the server to your client's MCP config:

```jsonc
// Claude Desktop: claude_desktop_config.json
// Cursor:         .cursor/mcp.json      Windsurf: ~/.codeium/windsurf/mcp_config.json
{
  "mcpServers": {
    "rattle": {
      "command": "node",
      "args": ["/absolute/path/to/grimoire/mcp/server.mjs"],
      "env": {
        "RATTLE_API_KEY": "rk_live_…",
        "RATTLE_MCP_ALLOW_WRITES": "0"   // "1" to permit writes. Think first.
      }
    }
  }
}
```

Verify it before wiring it up — this needs no key and touches no network:

```bash
node grimoire/scripts/mcp_smoke.mjs
# OK — 462 API operations reachable, read-only enforced.
```

**Tell your agent where to start.** These clients have no Skills mechanism, so nothing auto-loads. Put this in your Cursor rules / project instructions / system prompt:

> For any Rattle task, first call `rattle_knowledge_get("skills/rattle-configurator/SKILL.md")` — it carries the #1 rule. Use `rattle_knowledge_list` to find the right skill for the task.

**Why it won't rot.** The Rattle API has 462 operations across 257 paths. A server hand-declaring one tool per endpoint would break every time rattleapp ships a new one. This one declares **no per-endpoint code at all** — `rattle_request` is a generic passthrough, `rattle_api_search` reads the bundled OpenAPI spec. A new endpoint works the day it ships. Node ≥ 18, zero npm dependencies.

**It is read-only until you say otherwise.** A live CPQ tenant is not a sandbox, and a generic passthrough in an agent loop could otherwise rewrite a customer's catalogue in one call. Writes belong in `rattle-config-builder`, which pauses for confirmation.

### 3. npx installer (Codex, Aider, Continue, any AGENTS.md tool)

Copies the skills, subagents, commands, schemas, examples, the MCP server and `AGENTS.md` into your project, ready for any agent that reads `AGENTS.md` (the cross-platform standard).

> **Not yet on npm.** `@rattleai/grimoire` is unpublished, so `npx @rattleai/grimoire` will 404. Run the installer from a clone — it is the same script the npm package would ship:

```bash
git clone https://github.com/rattleai/grimoire.git

node grimoire/bin/grimoire.mjs install --target ./my-project             # root-level layout
node grimoire/bin/grimoire.mjs install --target ./my-project --layout claude  # under .claude/
node grimoire/bin/grimoire.mjs install --layout user                     # machine-wide
node grimoire/bin/grimoire.mjs install --dry-run                         # preview
```

Idempotent — re-running just refreshes the files. `--help` lists every option.

Once published, the same thing becomes `npx @rattleai/grimoire install`.

### 4. Python CLI (optional execution layer)

Only needed for terminal-driven, one-shot commands that call your AI provider directly. **The skills and agents do not require it** — they are model-agnostic text.

> **Not on PyPI, and do not `pip install grimoire`.** That name belongs to an unrelated bioinformatics package. This project publishes as **`rattle-grimoire`**; until it is released, install from a clone:

```bash
git clone https://github.com/rattleai/grimoire.git && cd grimoire
pip install -e ".[all-ai,all-sources]"

cp .env.example .env
# Edit .env — RATTLE_API_KEY_<TENANT>, AI_PROVIDER, OPENAI_API_KEY / ANTHROPIC_API_KEY, …

rattle <tenant> test-connection
rattle <tenant> ai-analyse-pricelist <file>
```

The console script is `rattle` either way — only the distribution name is `rattle-grimoire`.

## Walkthrough — your spreadsheet to a live configurator

This is the whole product. Say you have `Preisliste_2026.xlsx`: a German pricelist, variants in the header row, prices in the cells.

**1. Ingest.** `/rattle-ingest source/acme/Preisliste_2026.xlsx`

The agent runs `profile_source.py` — it never guesses a column's meaning from the header alone, because headers lie, abbreviate, and mix languages. It scores each column on header keywords *and* value shape (dtype, cardinality, samples), classifies all 24 column roles, and detects the sheet shape. Yours comes back `wide-variant-matrix` — the nastiest and most common: the variants *are* the column headers.

Out comes a **`source-mapping.json` you review before anything is built**, and one blocker:

> `missing-standard-variant` — Column `19 Zoll` is a surcharge with no standard sibling. The variant that ships as standard is not represented anywhere in the source.
> **Which wheel size ships as standard, at what price (expected 0), and which part does it pull into the BOM?**

This is the #1 rule enforced at the door. The chain **will not proceed** while a blocker is open, and it will **not** invent a 17-inch standard wheel to make the error go away. A guessed standard variant corrupts the BOM, the pricing, and every offer built on top of it. So it stops and asks.

**2. Answer, re-ingest, analyse.** `/rattle-analyse`
Deterministic keyword detection plus LLM structural analysis, over the *normalized* rows. Findings index against the same anti-pattern catalogue the blockers do, so they merge cleanly.

**3. Recommend.** `/rattle-suggest-config`
Explicit groups. Explicit options for **every** variant including the standard. BOM rules wiring parts to options through `usage_subclauses`. Numbered options where the sheet priced per-metre. Forbidden pairs. Output validates against `schemas/recommendation.schema.json`.

**4. Apply.** The `rattle-config-builder` agent — the only one allowed to write — turns it into idempotent `ensure_*` operations. It runs `validate_recommendation.py` first and refuses to write if validation fails. **Re-running is a safe no-op**, so a half-finished apply can simply be run again.

**5. Audit.** `/rattle-audit` — 6 structural checks against the now-live tenant.

Every step emits a schema-validated artifact you can inspect, diff, and hand to a colleague. The Python CLI runs steps 2–3 as one-shot terminal commands if you'd rather not drive an agent loop.

## How any AI model uses this

Every Skill is a self-contained Markdown bundle: a `SKILL.md` (frontmatter `name` + `description`) plus optional `references/` and `scripts/`. A model reads the frontmatter, decides the skill is relevant, then loads the body and references on demand — so you pay context only for what the task needs.

Clients **with** a Skills mechanism (Claude Code) load them natively. Clients **without** one (Cursor, Windsurf, Claude Desktop, ChatGPT) get the identical content through the MCP server's `rattle_knowledge_*` tools. Same knowledge, same workflow, same output contracts.

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
make check         # lint + type-check + 262 tests + bundle + mcp
make lint          # ruff
make type-check    # mypy
make test          # pytest
make validate      # bundle gate — manifests, frontmatter, schemas, examples, bytecode
make mcp-smoke     # drives the MCP server over real stdio; asserts read-only holds
make format        # ruff format
```

`make validate` exists because every one of its checks corresponds to a defect that actually shipped: manifest versions drifting apart, a `strict: false` marketplace entry that becomes a hard load failure, `.pyc` files published to npm because `files:` overrides `.gitignore`, a golden example silently drifting from its schema, and an agent's `skills:` list naming a skill that doesn't exist. CI runs it on every push.

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
- [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) — full Rattle REST API reference (462 operations).
- [`SETUP.md`](SETUP.md) — beginner-friendly setup guide.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution guidelines.
- [`SECURITY.md`](SECURITY.md) — security policy.
- [`CHANGELOG.md`](CHANGELOG.md) — version history.

## License

[MIT](LICENSE)
