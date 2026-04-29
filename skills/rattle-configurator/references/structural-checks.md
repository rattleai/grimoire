# Structural checks — full reference

Mirror of `rattle_api.knowledge.STRUCTURAL_CHECKS`. Six declarative check specs that a live-tenant audit runner executes against a Rattle API client. Each check is a `(list endpoint, optional per-entity endpoint, flag-when predicate)` triple. Cite by `id` in audit findings.

| id | severity | scope |
|---|---|---|
| `areas-without-groups` | error | catalogue structure |
| `duplicate-group-names` | warning | catalogue structure |
| `offer-template-missing-configuration` | error | documents system |
| `duplicate-dynamic-wrappers` | warning | documents system |
| `options-with-custom-keys` | info | catalogue style (tenant opt-in) |
| `options-with-conflicting-area-overrides` | warning | options pricing |

---

## 1. `areas-without-groups` — error

Areas that have zero groups linked to them. Violates `no-empty-areas`.

```yaml
list:        /areas
per_entity:  /areas/{id}/groups
flag_when:   len(groups) == 0
related_rules: [no-empty-areas]
```

**Why this matters.** An empty area is a dead end in the configurator UI. The user clicks it and sees no choices. The fix is either to add at least one group or to migrate the narrative content into a document template (see `narrative-in-documents-system`) and delete the area.

---

## 2. `duplicate-group-names` — warning

Groups where the same (case-insensitive) name appears on multiple group ids. Indicates a `reuse-over-duplicate` failure.

```yaml
list:        /groups
group_by:    lower(name)
flag_when:   count > 1
related_rules: [reuse-over-duplicate, shared-groups-across-products]
```

**Fix.** Pick one group as canonical, link it to every area that the duplicates were assigned to (`POST /groups/{id}/areas`), use option-area-config for any per-area pricing differences, then delete the duplicates. Watch out for differing option lists — only merge when the option content is genuinely identical.

---

## 3. `offer-template-missing-configuration` — error

Offer document templates whose structure tree does not contain any attachment to the system dynamic content block `dynamic:document_configuration`. Violates `offer-requires-configuration-block` and the doc_type `requires_configuration` contract.

```yaml
list:        /documents/templates?doc_type=offer
per_entity:  /documents/templates/{id}/structure
flag_when:   no attachment has content_block_key == 'dynamic:document_configuration'
related_rules: [offer-requires-configuration-block]
```

**Fix.** Add a structure block (`node_type=section` is fine), then attach the system content block whose `key=='dynamic:document_configuration'`. Look up its id via `GET /documents/content-blocks?is_dynamic=true&key=dynamic:document_configuration`. Set the attachment's `is_required=true`.

---

## 4. `duplicate-dynamic-wrappers` — warning

User-created content blocks whose only locale has a `template_name` matching a system dynamic block key (e.g. `dynamic:document_configuration`). Indicates a built-in dynamic block was wrapped instead of referenced by id.

```yaml
list:        /documents/content-blocks
flag_when:   is_dynamic == False AND any(locale.template_name startswith 'dynamic:')
related_rules: [use-system-dynamic-blocks]
```

**Fix.** Find every attachment that points at the wrapper content block; rewrite the attachment to point at the system block id (where `is_dynamic=true`); delete the wrapper.

---

## 5. `options-with-custom-keys` — info, opt-in

Options that have a non-empty `key` field. Not an error by itself — some tenants require integration keys (ERP, MES). Reported only when the tenant has explicitly opted in via the tenant memory profile.

```yaml
list:        /options
flag_when:   key != '' AND key is not None
related_rules: [minimal-keys]
tenant_opt_in: true
```

**Fix (when opted in).** Either set the tenant's `## Preferences` to `- **custom-keys**: never` and remove the keys, or update the tenant profile to suppress this check.

---

## 6. `options-with-conflicting-area-overrides` — warning

Options where an area-config has price 0 / null / missing while the base option price is non-zero. Indicates the option silently drops to free in that area.

```yaml
list:        /options
per_entity:  /options/{id}/area-config?area_id={area_id}
flag_when:   base_price > 0 AND area_config.price in (0, None, '')
related_rules: [price-on-option, area-config-for-scaled-prices]
```

**Fix.** Verify whether the zero-price was intentional (some areas legitimately get the option free). If unintentional, set `PUT /options/{id}/area-config?area_id=…` with the correct price.

---

## How to run an audit

The check specs are declarative. A runner (e.g. a future `rattle audit` subcommand or a notebook driving `RattleClient`) iterates over each check, fetches the listed endpoints, applies the predicate, and emits a list of findings. Each finding is a dict with synthetic shape:

```json
{
  "check_id": "areas-without-groups",
  "severity": "error",
  "entity_type": "area",
  "entity_id": 42,
  "message": "Area 'Widget Pro — Description' has no groups",
  "related_rules": ["no-empty-areas"]
}
```

The `system_prompt_audit(findings=…)` builder in `rattle_api.knowledge` (mirrored in `system-prompts.md`) takes a list of findings and produces a triage prompt: the AI ranks them, recommends the minimum change for each, and cross-references the violated rules.

When findings are written back to tenant memory (`audit_history.jsonl`), keep the full structure — that file is the input to "what changed since the last audit?" comparisons over time. The file is line-delimited JSON; each line is `{"timestamp": "<ISO 8601 UTC>", "findings": [<finding>, …]}`.
