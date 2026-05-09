---
name: rattle-tenant-memory
description: Use this skill whenever the user names a Rattle tenant or asks the AI to "remember" something about a tenant's preferences, decisions, or audit history. Documents the file-based memory model (profile.md, decisions.jsonl, audit_history.jsonl), how preferences are read into every system prompt, the explicit-write rule, and how to set / record / show / edit memory via the rattle CLI. Pair with rattle-configurator (which honours the preferences) and rattle-apply-config (which reads minimal-keys before any write).
license: MIT
---

# Rattle tenant memory

Per-tenant style preferences, decisions, and audit history. File-based, gitignored, explicit-write only. Auto-injected into every system prompt so consulting decisions stay tenant-coherent across sessions.

## When to use this skill

- The user names a tenant for the first time in a session and you need to know if there are saved preferences.
- The user says "always do X for this tenant" or "remember that we decided Y" — translate to the right memory write.
- A configuration recommendation conflicts with a tenant default (e.g. they always set German names verbatim).
- An audit run produces findings that should be saved for trend tracking.
- The user asks "what do you know about <tenant>?" — show the profile and recent decisions.

## File layout

```
memory/<tenant>/
  profile.md           Curated preferences and style (committed-or-not depending on the project — gitignored in this repo)
  decisions.jsonl      Append-only log of explicit decisions (UTC timestamps)
  audit_history.jsonl  Append-only log of audit findings batches
```

> **Note.** Earlier drafts mentioned a `catalogue_state.json` id-cache file — that was a planned feature that was never implemented (no script writes it, no script reads it). Removed from this layout. The builder agent (`rattle-config-builder`) re-resolves names → ids on every run via `GET ?search=` calls; there is no persistent cross-run id cache.

`memory/README.md` documents the gitignore policy. **Treat every file as private tenant data** — never commit, never log, never paste into chat verbatim.

## profile.md format

Free-form Markdown. The full file is appended into every system prompt under a `## Tenant preferences` section (auto-injected via `TenantMemory.inject_into_prompt()`). Keep it tight — short bullet preferences, not essays.

Conventional shape:

```markdown
# acme — tenant preferences

## Style
- Product names: keep exact wording from the source pricelist
- Area naming: `"<SKU> — <Section>"` with em-dash separator

## Preferences
- **custom-keys**: never
- **option-standard-variant**: always present, price 0, recommended=true
- **language**: de

## Offer documents
- doc_type: `offer`
- Required chapters: Product Overview (static content block) + Configuration (dynamic:document_configuration)

## Suppressions
- Suppress audit finding: `options-with-custom-keys` (we set keys intentionally for ERP integration)
```

The `## Preferences` section is special — `set_preference()` and `validate_recommendation.py` both parse it for `- **<key>**: <value>` lines. Other sections are free-form for the AI consultant to read.

## decisions.jsonl format

One JSON object per line:

```json
{"timestamp": "2026-04-28T18:00:00+00:00", "text": "Standardised on em-dash separator for area names across all products."}
```

Optional extra fields: `author`, `decision_id`, `tags`. The most recent 5 decisions are auto-injected into every system prompt under `### Recent decisions`.

## audit_history.jsonl format

One JSON object per line; each line is one audit run:

```json
{"timestamp": "2026-04-28T18:00:00+00:00", "findings": [<finding objects per rattle-audit/SKILL.md>]}
```

Used to track "did this finding appear in the last run?" over time. Not auto-injected into prompts (size).

## Reading memory (every consulting session)

When the user names a tenant, **always**:

1. Read `memory/<tenant>/profile.md` and respect every preference.
2. Read the last 5 entries in `memory/<tenant>/decisions.jsonl` to understand recent direction.
3. Pass the combined context into your system prompt (the Python CLI does this via `TenantMemory.inject_into_prompt()`; non-Python clients should replicate the format documented in `references/memory-format.md`).

If the tenant has **no memory directory yet**, that's fine — operate from defaults and offer to create a profile when you've learned something worth saving.

## Writing memory (explicit-only)

**Never write silently.** Tasks (analyse, suggest, audit) are read-only; writes happen only via these explicit commands:

```bash
# Show current memory:
rattle <tenant> memory show

# Open profile.md in $EDITOR:
rattle <tenant> memory edit

# Upsert a single preference under ## Preferences:
rattle <tenant> memory set-preference <key> <value>
# e.g. rattle acme memory set-preference custom-keys never

# Append a decision (with UTC timestamp auto-added):
rattle <tenant> memory record-decision "<text>"
```

For agents using this skill without the Python CLI, the equivalent operations are:

- `set-preference` → in-place edit of `profile.md`, upserting a `- **<key>**: <value>` line under `## Preferences`. If the section doesn't exist, create it. Idempotent.
- `record-decision` → append one line to `decisions.jsonl` with `{"timestamp": <UTC ISO 8601>, "text": <user_text>}`. Always append; never overwrite.
- Audit batches → append one line to `audit_history.jsonl` with `{"timestamp": <UTC>, "findings": [...]}`.

## Workflow recipes

### "Remember that for acme we never set custom keys"

```bash
rattle acme memory set-preference custom-keys never
```

The `validate_recommendation.py` script and `rattle-apply-config` will pick this up automatically — every group / option in the recommendation gets `key` stripped before write.

### "Save the audit findings from today"

```bash
# After the audit runner produces findings.json:
rattle acme memory record-decision "Audit found 3 errors, 7 warnings — see audit_history.jsonl 2026-04-28."
```

Optionally, append the full findings batch to `audit_history.jsonl` directly (no CLI shortcut yet — write to the file with explicit user consent).

### "What's our current profile?"

```bash
rattle acme memory show
```

Prints `profile.md` plus the last 5 decisions and last 3 audit summaries.

## Privacy boundaries

- **Never** commit `memory/<tenant>/*` to a public repository. The default `.gitignore` excludes everything under `memory/` except `README.md` and `.gitkeep`.
- **Never** read another tenant's memory — the consulting session is scoped to the tenant the user named.
- **Never** echo a tenant's profile verbatim into chat shared with another tenant.
- **Never** log API keys (`Bearer rk_live_…`) in `decisions.jsonl` or anywhere else.

## Related skills

- `rattle-configurator` — receives the profile via the `tenant_profile` parameter on every `system_prompt_*` builder.
- `rattle-apply-config` — reads `## Preferences` to enforce overrides (especially `custom-keys: never`).
- `rattle-audit` — reads opt-in flags (notably `custom-keys`) before running opt-in checks.
- `rattle-suggest-config` — incorporates style preferences (language, naming conventions) into recommendations.
