---
name: rattle-apply-config
description: Use this skill to apply an approved Rattle configuration recommendation to a live tenant. Translates the JSON output of rattle-suggest-config into a sequence of idempotent ensure_* REST operations matched by name (a second run is a safe no-op). Honours rules (no-empty-areas, reuse-over-duplicate, minimal-keys), respects tenant memory, uses optimistic concurrency where required, and stops on the first error. Pair with rattle-api (REST mechanics) and rattle-configurator (rules).
license: MIT
---

# Rattle apply configuration

Convert an approved recommendation into live-tenant writes. This is the only workflow in the Rattle bundle that mutates server state, so it is intentionally explicit, idempotent, and unambiguous about boundaries.

## When to use this skill

- The user has a recommendation JSON (from `rattle-suggest-config`, hand-edited, or imported from another source) and is ready to apply it to a live tenant.
- The user is fixing a single audit finding and wants the matching `ensure_*` operations.
- The user is migrating a "Description" area to documents (often emits both an `ensure_area` removal and a document-template build).

If the recommendation has not been validated yet, run `scripts/validate_recommendation.py` first — it catches rule violations without hitting the API.

## Workflow

1. **Pre-flight.** Read:
   - `skills/rattle-configurator/references/configuration-rules.md` — the rules every operation must respect.
   - `skills/rattle-configurator/references/system-prompts.md` § `system_prompt_apply_config` — the operation contract.
   - `skills/rattle-api/references/client-patterns.md` § 3 (Idempotent ensure) and § 4 (Sub-resource writes).
   - `references/operations-contract.md` (this skill) — the seven operation types with examples.
   - `memory/<tenant>/profile.md` — tenant overrides. **Mandatory** before any write.

2. **Validate the recommendation locally.** Run:
   ```
   python skills/rattle-apply-config/scripts/validate_recommendation.py <recommendation.json>
   ```
   The validator checks:
   - Every group has at least one option with `recommended=true` (unless `is_multi=true`).
   - No two groups share the same lower-cased name.
   - Every `usage_subclause` references an option that exists.
   - Every `forbidden_pair` references options that exist.
   - No group contains `key` fields when tenant memory says `custom-keys: never`.
   Exits non-zero on violation. Fix the recommendation before continuing.

3. **Plan the operations.** Walk the recommendation top-down, emitting operations in dependency order:
   - `ensure_product` — first.
   - `ensure_area` — second (depends on product).
   - `ensure_group` — third, with `link_to_areas` listing every area that needs the group. **One ensure_group per distinct group name across the entire recommendation** (the reuse-over-duplicate rule), not one per product.
   - `ensure_option` — after groups exist.
   - `ensure_area_config` — after both option and area exist; sets per-area price overrides.
   - `ensure_constraint_pair` — last (or as a separate batch keyed by product).
   - `ensure_constraint_rule` — last; conditional rules.

4. **Demand explicit confirmation before executing.** Restate: tenant, recommendation source, operation count by type. Ask the user to confirm by typing the tenant name. Do not execute on a generic "yes".

5. **Execute idempotently, name-matched.** For each operation:
   - List the existing entities (`GET /<resource>` filtered by name when the API supports it; otherwise paginate and filter client-side per `client-patterns.md` § 2).
   - If absent → create.
   - If present and the proposed fields differ → PATCH only the differing fields.
   - If present and identical → skip (`noop`).
   - Use sub-resource endpoints for associations (`POST /groups/{id}/areas`, `POST /products/{productId}/areas`, etc.) — never PATCH parent entities with `*_ids` arrays.

6. **Optimistic concurrency for constraints.** `POST /constraints` atomically replaces all pairs. Read `X-Constraints-Version` from the prior `GET /constraints?product_id=…`, send it back, retry once on `412 Precondition Failed`.

7. **Stop on the first error.** On any 4xx/5xx, abort the remaining operations. Restate what was applied so far (with `request_id`s) and the failed operation. Ask the user how to proceed.

8. **Log without leaking secrets.** Print one line per operation: `<type> <name> action=<created|updated|noop> id=<id> request_id=<req>`. Never echo `Bearer rk_live_…`.

9. **Persist the audit trail (only on explicit consent).** If the user asks, append a summary to `memory/<tenant>/decisions.jsonl`:
   ```
   rattle <tenant> memory record-decision "<summary>"
   ```
   Do not write silently.

## Output contract

```json
{
  "tenant": "acme",
  "recommendation_source": "<path or hash>",
  "applied": [
    {"type": "ensure_group", "name": "Wheels", "action": "created", "id": 312, "request_id": "req_..."}
  ],
  "skipped": [
    {"type": "ensure_option", "name": "17 inch", "reason": "noop — already matches"}
  ],
  "errors": []
}
```

The shape matches `agents/rattle-config-builder.md` so the agent and this skill share the same downstream consumers.

## Boundaries

- **Never delete** an entity unprompted. The recommendation is additive by default.
- **Never publish** an offer template (`is_published=true`) without verifying every `is_required=true` attachment resolves.
- **Never write** to `memory/<tenant>/*` silently.
- **Refuse** any operation type not in the seven documented in `references/operations-contract.md`.

## Bundled scripts

- `scripts/validate_recommendation.py` — deterministic recommendation validator. Runs without network or AI keys.

## Related skills

- `rattle-suggest-config` — produces the recommendation this skill applies.
- `rattle-api` — REST mechanics, including optimistic concurrency.
- `rattle-configurator` — the rules every write must satisfy.
- `rattle-tenant-memory` — tenant preferences that override defaults.
