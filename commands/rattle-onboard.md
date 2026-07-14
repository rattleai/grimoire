---
description: Take a brand-new Rattle tenant from empty to a working configurator. Walks the 9-step day-0 dependency order — preflight, company, languages, base price list, conventions, areas, configurator settings, first product, baseline audit, tenant memory. Leads with the ordering rule that bites: the base price list must exist before any product, or every price is silently denominated in the wrong currency. Refuses to run against a tenant that already has products.
argument-hint: <tenant name>
---

# /rattle-onboard

Bootstrap the tenant the user names (`$ARGUMENTS`) from **empty** to a working configurator. Every other Rattle skill assumes a tenant that already has products — this is the one that creates them.

Onboarding **writes to a live tenant.** Every write is idempotent get-or-create by natural key, and every write waits for explicit human confirmation.

## Workflow

1. **Load context** — Read `skills/rattle-onboarding/SKILL.md`, `skills/rattle-onboarding/references/day-zero-checklist.md`, and `skills/rattle-onboarding/references/configurator-settings.md`. They are the source of truth for the 9-step order, the conventions table, and the 19 configurator flags. Also load `skills/rattle-configurator/SKILL.md` — the `#1 rule` governs the first product exactly as it governs the thousandth.

2. **Preflight, and honour the gate** — `GET /company` and `GET /products?limit=1`. Confirm `RATTLE_API_KEY_<TENANT>` resolves first; an onboarding that dies halfway leaves a half-built tenant.

   **If any product exists, STOP.** That is a *migration* (`/rattle-ingest`) or an *audit* (`/rattle-audit`), not an onboarding — the day-0 conventions have already been decided implicitly by whoever created those products, and re-deciding them now forks the tenant. Report what you found and route the user.

3. **The ordering rule that bites** — State it before the first write. `ProductCreateRequest.currency` is *"Accepted but ignored — currency is derived from the company's base price list"*. So the **base price list must exist before any product** (step 3 before step 7), or every price in the tenant is silently denominated in the wrong currency with a `200 OK` and no error. **Never send `currency` on a product.**

4. **Company → languages → base price list** — `PATCH /company` (`company_name`, `company_url`, `config_code_prefix`, `default_language`), then `POST /languages` (base language first, `is_base: true`), then `POST /price-lists` with `is_base: true` and the currency. Get-or-create each; PATCH only differing fields.

5. **Force the day-0 decisions** — Do not guess, do not default silently, do not proceed while any is open. Get an **explicit human answer** to each: the **article-number key** inside `integration_metadata` (there is no `Product.sku`), the **money unit** for the integer `part_cost`, the **numeric unit** for integer-only numbered options (mm vs m), and **custom keys yes/no**. Each is cheap now and expensive later — the conventions table in the SKILL states exactly what breaks.

6. **Areas → configurator settings → first product** — `POST /areas` (`product_id` is optional, so areas may precede the product; `GET /areas/library` is a **reuse pool of unattached areas**, not a starter-template library — it returns `[]` on a fresh tenant). Then `PATCH /company/configurator-settings` — the **19 flags are absent from the OpenAPI spec**, so a typo is accepted with a `200` and does nothing: **read the settings back to verify.** Then `POST /products` (only `name` is required) and attach the areas via `POST /products/{productId}/areas`.

7. **Hand off — do not hand-build the configuration** — The customer's pricelist goes to `/rattle-ingest`, which surfaces a missing standard variant as a **blocker** instead of inventing it (`explicit-options-for-all-variants`). Chain: `/rattle-ingest` → `/rattle-analyse` → `/rattle-suggest-config` → apply.

8. **Baseline audit** — `python skills/rattle-audit/scripts/audit_runner.py <tenant>`. A day-0 tenant should be clean; the realistic finding is `areas-without-groups` from an area created and never filled. Fix it now, while the catalogue is one product deep.

9. **Write tenant memory** — `memory/<tenant>/profile.md` with **every decision from step 5** plus the currency, base language and `config_code_prefix`. Show the file and get consent — `rattle-tenant-memory` is explicit-write only. A convention not recorded here is one the next session silently re-invents.

## Confirmation discipline

Every write pauses. Restate the tenant, the step, and the exact request body, then ask the user to **type the tenant name** to confirm. A generic "yes" is not consent. If you cannot reach a human, stop and report the planned calls — an unapplied plan is recoverable, a wrong write to a live tenant is not.

## Delegation

Delegate the run to the `rattle-onboarder` subagent with the tenant name. It preloads `rattle-onboarding`, `rattle-configurator`, `rattle-api`, `rattle-apply-config` and `rattle-tenant-memory`, holds the confirmation gate, and refuses a tenant that already has products.

$ARGUMENTS
