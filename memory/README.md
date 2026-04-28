# Tenant memory

Per-tenant preferences for the consulting system. One directory per tenant, matching `source/<tenant>/` and the `RATTLE_API_KEY_<TENANT>` env-var convention.

```
memory/
  <tenant>/
    profile.md           # curated preferences & style (LOCAL ONLY — gitignored)
    decisions.jsonl      # explicit decision log (LOCAL ONLY — gitignored)
    audit_history.jsonl  # audit findings over time (LOCAL ONLY — gitignored)
    catalogue_state.json # id cache for idempotent re-runs (LOCAL ONLY — gitignored)
```

## Privacy

**This directory is in a public repository. Nothing under `memory/<tenant>/` is committed.** `.gitignore` uses `memory/*` with a whitelist for `README.md` and `.gitkeep`, so every tenant subdirectory stays on your local machine only.

This is intentional: tenant profiles often contain pricing, SKUs, internal style decisions, and references to customer-facing documents. Keep it all local; share it through whatever private channel your team uses (1Password, internal wiki, encrypted Slack, etc.) rather than git.

## What goes in `profile.md`

Free-form markdown. The top of the file is a `# <tenant> — tenant preferences` header; anything below it is appended to the consulting system prompt under a `## Tenant preferences` section, so everything the AI does for this tenant inherits these choices.

A good profile captures:

- **Style**: naming conventions, language, units, decimal separator.
- **Structural preferences**: e.g. "never set custom `key` fields", "use shared library groups across products".
- **Offer documents**: which chapters are required, which hero image to use, doc_type.
- **Known anti-patterns to suppress**: e.g. "custom keys on this tenant are intentional, ignore options-with-custom-keys findings".

Generic example (save locally as `memory/acme/profile.md`, not committed):

```markdown
# acme — tenant preferences

## Style
- Product names: keep exact wording from the source pricelist
- Area naming: `"<SKU> — <Section>"` with em-dash separator

## Preferences
- **custom-keys**: never
- **option-standard-variant**: always present, price 0, recommended=true

## Offer documents
- doc_type: `offer`
- Required chapters: Product Overview (static content block) + Configuration (dynamic:document_configuration)
```

## How memory is read

`rattle_api/memory.py` → `TenantMemory(tenant).inject_into_prompt()` returns the profile plus the last 5 decisions. The consulting tasks (`analyse_pricelist`, `suggest_configuration`) call this automatically and pass the result into `system_prompt_base` as the `tenant_profile` parameter.

## How memory is written

**Only by explicit commands.** No task writes silently. The write paths are:

- `rattle <tenant> memory edit` — opens `profile.md` in `$EDITOR` (or prints the path).
- `rattle <tenant> memory set-preference <key> <value>` — upserts a bullet under `## Preferences` in `profile.md`.
- `rattle <tenant> memory record-decision "<text>"` — appends one line to `decisions.jsonl` with a UTC timestamp.

To see what's currently stored: `rattle <tenant> memory show`.

## Git policy (short version)

- `memory/README.md` — committed (this file).
- `memory/.gitkeep` — committed (keeps the directory in git).
- **Everything else under `memory/` — gitignored. Never commit tenant content.**
