# Audit runner — language-agnostic spec

How to implement the audit runner in any language. The bundled Python script at `scripts/audit_runner.py` is one reference implementation; this file describes the algorithm so a TypeScript, Go, or curl-based equivalent stays behaviour-identical.

## Inputs

| Input | Source |
|---|---|
| `tenant` | CLI arg or function parameter |
| `RATTLE_API_KEY_<TENANT>` | env var (uppercased tenant) |
| `RATTLE_BASE_URL` | env var, defaults to `https://www.rattleapp.de/api/v1` |
| `memory/<tenant>/profile.md` | optional — Markdown, parsed for opt-in flags under `## Preferences` |
| `selected_checks` | optional comma-separated list; defaults to all six |

## Algorithm

```
prefs = parse_tenant_profile(memory_root / tenant / "profile.md")
custom_keys_opt_in = (prefs.get("custom-keys", "").lower() == "never")

findings = []
for check_id in selected_checks:
    if check_id in OPT_IN_CHECKS and not custom_keys_opt_in:
        continue
    findings.extend(run_check(check_id, base_url, token))

return {
    "tenant": tenant,
    "ran_at": now_utc_iso8601(),
    "summary": count_by_severity(findings),
    "findings": findings,
}
```

## Per-check pseudocode

### `areas-without-groups`

```
for area in list_all("/areas"):
    if len(GET "/areas/{area.id}/groups".data) == 0:
        emit error "Area has 0 groups"
```

### `duplicate-group-names`

```
groups_by_name = {}
for g in list_all("/groups"):
    groups_by_name.setdefault(g.name.lower(), []).append(g)
for name, dupes in groups_by_name:
    if len(dupes) > 1:
        for g in dupes[1:]:
            emit warning "duplicates group id={dupes[0].id}"
```

### `offer-template-missing-configuration`

```
for tmpl in list_all("/documents/templates", {doc_type: "offer"}):
    structure = GET "/documents/templates/{tmpl.id}/structure"
    if not contains_attachment(structure, "dynamic:document_configuration"):
        emit error "missing dynamic:document_configuration attachment"
```

`contains_attachment` walks the structure tree looking at every `attachments[*].content_block_key` and `attachments[*].dynamic_key`.

### `duplicate-dynamic-wrappers`

```
for cb in list_all("/documents/content-blocks"):
    if cb.is_dynamic: continue
    for locale in cb.locales:
        if locale.template_name.startswith("dynamic:"):
            emit warning "wraps system dynamic key"
            break
```

### `options-with-custom-keys` (opt-in)

Skipped silently unless `tenant_prefs["custom-keys"] == "never"`.

```
for opt in list_all("/options"):
    if opt.key:
        emit info "has custom key {opt.key}"
```

### `options-with-conflicting-area-overrides`

```
for opt in list_all("/options"):
    if opt.price <= 0: continue
    for cfg in GET "/options/{opt.id}/area-config".data:
        if cfg.price in (None, "", 0):
            emit warning "drops to free in area {cfg.area_id}"
```

## Pagination loop

Per `skills/rattle-api/references/client-patterns.md` § 2:

```
function list_all(endpoint, params={}):
    cursor = None
    while True:
        page = GET endpoint?{params}&limit=100&cursor={cursor}
        yield from page.data
        if not page.meta.has_next: return
        cursor = page.meta.next_cursor
```

## Auth

Every request: `Authorization: Bearer <RATTLE_API_KEY_<TENANT>>` and `Accept: application/json`. Never log the token. Surface RFC 9457 problem-details errors to stderr but continue with remaining checks.

## Output shape

See `skills/rattle-audit/SKILL.md` § Output contract. Top-level fields:

- `tenant` (string)
- `ran_at` (ISO 8601 UTC, e.g. `2026-04-28T21:00:00+00:00`)
- `summary` (`{errors, warnings, info}` integer counts)
- `findings` (array of finding objects)

Each finding:

```json
{
  "check_id": "areas-without-groups",
  "severity": "error" | "warning" | "info",
  "entity_type": "area" | "group" | "option" | "document_template" | "document_content_block",
  "entity_id": <int>,
  "entity_name": "<string>",
  "message": "<one-line summary>",
  "related_rules": ["<rule-id>", ...],
  "minimum_fix": "<actionable fix description>"
}
```

## Exit codes

- `0` — no errors found (warnings and info are not failures).
- `1` — at least one error finding.
- `2` — bad input (missing token, unknown check id, network failure on all checks).
