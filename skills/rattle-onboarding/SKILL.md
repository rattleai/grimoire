---
name: rattle-onboarding
description: Use this skill whenever a brand-new Rattle tenant must be taken from empty to a working configurator: onboarding, onboard, setup, set up, bootstrap, getting started, day one, day-0, new tenant, first product, Einrichtung, Erstkonfiguration, neuer Mandant. Every other Rattle skill assumes a tenant that already has products; this is the one that creates them. Walks the 9-step dependency order: preflight, company, languages, base price list, conventions, areas, configurator settings, first product, baseline audit, tenant memory. Leads with the ordering rule that bites: ProductCreateRequest.currency is "accepted but ignored — currency is derived from the company's base price list", so the base price list MUST exist before any product or every price is silently denominated in the wrong currency. Forces the day-0 conventions (article-number key, part_cost unit, numbered-option unit, custom keys) to be decided and recorded. Refuses to onboard a tenant that already has products.
license: MIT
---

# Rattle onboarding — the day-0 bootstrap

Every other skill in this bundle assumes a tenant that **already has products**. `rattle-ingest` maps a pricelist onto entities that must exist. `rattle-suggest-config` reuses groups it expects to find. `rattle-audit` scans a catalogue. **Nobody walks the path from an empty tenant to a working configurator.** This skill is that path.

The audience is a **new Rattle customer (tenant admin)** on their first day. The output is a tenant that is *correctly ordered* — because the order is not obvious, several of the steps are irreversible in practice, and getting them wrong is silent.

Onboarding **writes to a live tenant.** Every write in this skill is idempotent get-or-create matched by a natural key, exactly as in `rattle-apply-config` — a second run is a safe no-op.

## When to use this skill

- A new tenant has been provisioned, the API key works, and there is nothing in it yet.
- The user says "onboard", "set up", "getting started", "wie richte ich das ein", "Erstkonfiguration", "neuer Mandant" — or asks what to do first.
- A tenant exists but company settings, languages, or the base price list were never configured, and the first product is about to be created.
- The user is about to hand over a pricelist for a tenant that has no configuration at all — run this **before** `rattle-ingest`.

**Do not use this skill when the tenant already has products.** That is a *migration* (`rattle-ingest` → `rattle-suggest-config` → `rattle-apply-config`) or an *audit* (`rattle-audit`), not an onboarding. See "Before you start (preflight)".

## Before you start (preflight)

Two read-only calls. Both are mandatory, and the second one is a gate.

```
GET /api/v1/company            → CompanySettingsResponse (company_name, company_url,
                                 config_code_prefix, custom_domain, custom_domain_verified,
                                 default_language, id)
GET /api/v1/products?limit=1   → the gate
```

**If `GET /products` returns any product, STOP.** Do not "onboard" the tenant. An existing catalogue means the day-0 conventions below have *already been decided implicitly* by whoever created those products — the article-number key is already in some `integration_metadata` object, the currency is already baked into every price, the numbered-option unit is already baked into every `option_scalings` descriptor. Re-deciding them now silently forks the tenant into two conventions. Report what you found and route the user to `rattle-audit` (to see the state) or `rattle-ingest` (to add data), and stop.

Also read, before any write:

- `memory/<tenant>/profile.md` — if it already exists, the tenant is not new. Treat as above.
- `skills/rattle-configurator/SKILL.md` — the #1 rule governs the first product exactly as it governs the thousandth.

## The ordering rule that bites

> **The base price list MUST exist before any product is created.**

`ProductCreateRequest.currency` carries this description, verbatim from the spec:

> *"Accepted but ignored — currency is derived from the company's base price list"*

So a product created before the base price list exists is denominated by whatever the company falls back to — **not** by the `currency` you sent. You sent `"USD"`, you got `200 OK`, `ProductResponse.currency` reads back something else, and **nothing errored**. Every `base_price`, every `option.price`, every offer PDF downstream is now in the wrong currency, and the only signal is that a customer eventually notices the number is wrong.

This is the single reason day-0 order is not a matter of taste. `POST /price-lists {"name": …, "currency": "EUR", "is_base": true}` is **step 3**, before `POST /products` at **step 7**, and no shortcut around it exists. (Audit finding **P2-4**: *fields accepted, returned 200, and discarded*.)

**Never send `currency` on a product.** It is a lie you tell yourself. Set the currency once, on the base price list, and let every product derive it.

### The other findings that bite on day 0

Each of these is a decision you make **once**, on day 0, because it is baked into every row you import afterwards. They are drawn from `docs/API_AUDIT.md`; the consequence column is the point.

| Finding | The trap | Consequence if you get it wrong |
|---|---|---|
| **P2-1 — `Product.sku` now exists ✓** | Earlier there was **no `sku`** on any product schema, so the ERP article number had to live in `integration_metadata.<key>` under a tenant-invented convention. **The current spec adds `Product.sku`** — `string ≤255` on `ProductCreateRequest` / `ProductUpdateRequest` / `ProductResponse`, **unique per tenant (duplicate → `409`), filterable via `GET /products?sku=`** — and it flows through to `QuoteLineItemResponse.product_sku`. | Put the article number in **`product.sku`** — the canonical, indexed, unique home. `integration_metadata` is now only for *secondary* identifiers. A tenant onboarded before this change may still carry its article number in `integration_metadata`; migrating it to `sku` is a one-time backfill. |
| **P2-4 — `currency` is silently ignored** | See above. | Every price in the tenant denominated wrong, with a `200 OK`. |
| **P0-1 — `X-Constraints-Version` is not in the spec** | `POST /constraints` **atomically replaces all** forbidden pairs for a product and documents an `X-Constraints-Version` OCC header **in its prose** — while declaring zero header parameters and no `409`. A spec-driven client is structurally incapable of sending it. | Two concurrent constraint writes: the second **silently destroys the first, with a `200 OK`.** The configurator starts selling combinations that cannot be built. Send the header from day 0 (`rattle-apply-config` § 6) — retry once on **409**, whose `detail` contains `Version conflict:`. |
| **P0-5 — `part_cost` is an `integer`** | `PartCreateRequest.part_cost` is `{"type": "integer", "minimum": 0}`. €12.50 **cannot be represented.** And `part_cost` rolls up through BOM explosion, so one rounded child poisons every ancestor. | Decide the money unit **now** — whole euros, or cents-as-integer. Across a 5,000-line BOM the difference is a real number on a real quote. Record it; every part import afterwards depends on it. |
| **P2-3 — numbered options are integer-only** | `number_min` / `number_max` / `number_step` are `integer`, and `ConfigurationCalculateRequest.option_amounts` is `{"additionalProperties": {"type": "integer"}}` — integer through the **entire** pipeline. **2.5 m, 0.5 kg, 1.75 m² are unrepresentable.** | If the customer sells anything by length, area, weight or volume, the only workaround is **unit inflation** (model in mm, divide back in the BOM factor). Decide mm-vs-m on day 0: it is baked into every `option_scalings` descriptor, the customer sees `3000` where they think `3 m`, and **off-by-1000 errors here are silent and quote-destroying.** |

## Workflow

Nine steps, in dependency order. Steps 1–3 and 5–7 write; steps 0, 4, 8, 9 do not touch the API. Every write is get-or-create by natural key.

### 0 · Preflight (read-only)

`GET /company`, `GET /products?limit=1`. **Refuse to onboard a tenant that already has products** — see above. Confirm `RATTLE_API_KEY_<TENANT>` resolves before anything else; an onboarding that dies halfway leaves a half-built tenant.

### 1 · Company — `PATCH /api/v1/company`

`CompanySettingsUpdateRequest` — **all four fields optional**, `additionalProperties: false`:

| Field | Constraint | Notes |
|---|---|---|
| `company_name` | 1–255 chars | |
| `company_url` | ≤ 255 chars | |
| `config_code_prefix` | ≤ 10 chars | Prefixes every saved configuration code. Customer-visible. Pick it once — existing codes do not migrate. |
| `default_language` | ≤ 8 chars | The fallback language for entities created without an explicit `language`. Must match the base language you create in step 2. |

Idempotent: `GET /company` first, PATCH **only the fields that differ**.

### 2 · Languages — `POST /api/v1/languages`

`LanguageCreateRequest`: **required `code` (2–8 chars), `name` (1–50 chars)**; optional `is_base` (default `false`).

**Create the base language first**, with `is_base: true`. `default_language` on the company (step 1) should name the same language. A live tenant we probed carries `DE` + `EN-US` — the `code` is free-form within its length bounds, so **the tenant's spelling of the code is itself a convention**: `EN-US` and `en_US` are different strings to this API. Record which one you chose.

Natural key: `code`. `GET /api/v1/languages` (not paginated — it declares no `cursor`/`limit`) → skip if the code is present.

### 3 · Base price list — `POST /api/v1/price-lists` ← **BEFORE ANY PRODUCT**

`PriceListCreateRequest`: **required `name`**; optional `currency` (≤ 3 chars, default `"EUR"`), `description` (≤ 2000), `is_base` (default `false`).

```json
{"name": "Standard", "currency": "EUR", "is_base": true}
```

**`is_base: true` is the whole point of this step.** It is what every product's currency is derived from (see "The ordering rule that bites"). Exactly one base price list. Do this before step 7 or the tenant is silently wrong.

Natural key: `name`. Writes to `/price-lists/*` use the `X-Price-Lists-Version` OCC header — same discipline as constraints (`rattle-apply-config` § 6).

### 4 · Conventions — decide and RECORD (no API call)

The heart of the skill. **Stop and get an explicit human answer to each row of the table in "Decisions you must make on day 0" below.** Do not guess, do not default silently, do not proceed while any of them is open. They are written to `memory/<tenant>/profile.md` in step 9, and everything imported afterwards assumes them.

### 5 · Areas — `POST /api/v1/areas`

`AreaCreateRequest`: **required `name`** (1–255); optional `product_id`, `area_group_id`, `allow_disable` (default `false`), `description` (≤ 5000), `language` (default `"DE"`), `order_index`, `price` (default `"0.00"`).

Areas are the configurable sections of a product. **`product_id` is optional** — so an area can be created now, before the first product exists, and attached in step 7 via `POST /products/{productId}/areas`. Unattached areas are exactly what `GET /api/v1/areas/library` returns.

> **`GET /areas/library` is NOT a starter-template library.** Its own description: *"List areas not assigned to any product. Not paginated."* It is a **reuse pool of unattached areas** — on a fresh tenant it returns `[]`. (Verified: 0 on the live tenant.) Nothing seeds a new tenant with template areas. If a user expects starter content, tell them plainly that there is none.

Rule `no-empty-areas` applies from the first area: an area with zero groups is an audit `error`. Create areas here, fill them with groups in step 7 (or via `rattle-ingest` → `rattle-suggest-config`), and do not leave one empty.

### 6 · Configurator settings — `PATCH /api/v1/company/configurator-settings`

**19 flags that govern the entire customer-capture UX of the configurator** — whether a salesperson may create a new customer, which fields are shown, which are required, what the search box searches. A new tenant must decide them **deliberately**; the defaults are not a design.

> **These flags are not in the OpenAPI spec.** The `PATCH`/`PUT` request body is an **inline** `{"type": "object", "additionalProperties": true}` — no schema, no field names, no validation. **An agent cannot discover them.** That is precisely why this skill lists them. Full contract, defaults, and the UX consequence of each: **`references/configurator-settings.md`**.

The 19, verified against a live tenant: `allow_create_new_customer`, `allow_select_existing_customer`, `customer_search_fields` (array), `start_search_digits` (int), `require_company_contact_person`, `require_customer_address`, `require_customer_contact_person`, `require_customer_email`, `require_customer_id`, `require_customer_info`, `require_customer_organization`, `require_customer_phone`, `show_company_contact_person`, `show_customer_address`, `show_customer_contact_person`, `show_customer_email`, `show_customer_id`, `show_customer_organization`, `show_customer_phone`.

Idempotent: `GET /company/configurator-settings` first, PATCH only what differs. Because the body is `additionalProperties: true`, **a typo'd flag name is accepted with a `200` and does nothing** — there is no `422` to protect you. Verify by reading the settings back.

### 7 · First product — `POST /api/v1/products`

`ProductCreateRequest`: **only `name` is required** (1–255). Optional: `base_price` (string|integer|number, default `"0.00"`), `description` (≤ 5000), `is_active` (default `true`), `language` (default `"DE"`), `catalog_meta`, `integration_metadata` — and `currency`, **which you must never send** (it is accepted and discarded).

The article number goes in `integration_metadata` under the key decided in step 4:

```json
{
  "name": "Widget Pro",
  "base_price": "12000.00",
  "language": "DE",
  "integration_metadata": {"article_number": "WP-1000"}
}
```

Then attach the step-5 areas: `POST /api/v1/products/{productId}/areas`.

**Now hand off.** Do not hand-build the configuration. The customer's pricelist goes to **`rattle-ingest`**, which maps its columns onto entities and — critically — **refuses to invent a standard variant that the pricelist does not state** (the `#1 rule`, enforced at the door). The chain from here is `rattle-ingest` → `rattle-pricelist-analysis` → `rattle-suggest-config` → `rattle-apply-config`.

Groups and options, when they come, obey: `GroupCreateRequest` requires `name` (`area_id` optional); `OptionCreateRequest` requires **`name` and `group_id`**.

### 8 · Baseline audit — `rattle-audit`

Run the 6 structural checks against the result:

```
python skills/rattle-audit/scripts/audit_runner.py <tenant>
```

A day-0 tenant should be clean. If it is not, the two you will actually see are `areas-without-groups` (you created an area in step 5 and never filled it) and `offer-template-missing-configuration` (if a template was built). Fix them now, while the catalogue is one product deep and a mistake costs minutes. This is the baseline every later audit is compared against.

### 9 · Tenant memory — write `memory/<tenant>/profile.md`

Persist **every decision from step 4**, plus the currency, base language and `config_code_prefix` from steps 1–3. This file is auto-injected into every downstream system prompt (`rattle-tenant-memory`), so a convention recorded here is a convention every later session honours — and a convention *not* recorded here is one the next session will silently re-invent.

Per `rattle-tenant-memory`, **writes are explicit-only** — show the user the file you intend to write and get consent. Onboarding is the one workflow where writing a profile is expected, not exceptional.

```markdown
# acme — tenant preferences

## Conventions (decided at onboarding, 2026-07-14)
- **article-number-key**: `integration_metadata.article_number`
- **part-cost-unit**: whole EUR (part_cost is integer — API cannot hold cents)
- **numbered-option-unit**: mm (length options modelled in mm; BOM factor divides by 1000)
- **custom-keys**: never
- **base-currency**: EUR (from base price list "Standard")
- **base-language**: DE (config_code_prefix: ACME)

## Preferences
- **custom-keys**: never
- **option-standard-variant**: always present, price 0, recommended=true
```

The `## Preferences` section is parsed by `set_preference()` and `validate_recommendation.py` for `- **<key>**: <value>` lines — keep `custom-keys` there in that exact shape. The `## Conventions` section is free-form prose the consultant reads.

## Decisions you must make on day 0

The conventions table. Each row is a decision that is **cheap now and expensive later**, because the API gives you no place to change it and no error when it drifts.

| Decision | What it is | Why day 0 | What breaks if you change it later | Where it gets recorded |
|---|---|---|---|---|
| **Article-number home** | Where the customer's article number / SKU / Sachnummer lives. **The current spec provides `Product.sku`** (`string ≤255`, unique per tenant → `409`, filter `GET /products?sku=`) — the canonical home (P2-1, resolved). `integration_metadata.<key>` remains for *secondary* identifiers only. | The article number finally has a real, indexed, unique home in `product.sku`. Decide day 0 whether any *additional* keys go into `integration_metadata` and under what key. | A pre-`sku` tenant that kept its article number in `integration_metadata` needs a one-time backfill into `sku`; inconsistent `integration_metadata` keys still split lookups. | `memory/<tenant>/profile.md` § Conventions, as `article-number-key` |
| **Money unit for `part_cost`** | Whether an integer `part_cost` means whole euros or cents. | `part_cost` is an `integer` with **no documented unit** (P0-5). €12.50 is unrepresentable either way; you are choosing which rounding error you accept. | Costs roll up through BOM explosion, so **switching the unit silently rescales every ancestor part by 100×.** No error, no warning — just a quote that is 100× wrong. | `memory/<tenant>/profile.md` § Conventions, as `part-cost-unit` |
| **Numeric unit for numbered options** | mm vs m, g vs kg, cm² vs m² — the unit a numbered option's integer amount is expressed in. | Numbered options are **integer-only, end to end** (P2-3). Anything continuous (cut-to-length, sheet goods, cable, textiles) needs unit inflation, and the inflation factor is not stored anywhere in the API. | The factor is baked into **every `option_scalings` descriptor and every BOM factor** already written. Changing it means rewriting all of them. Meanwhile `number_unit` becomes a lie relative to the customer's mental model — they think `3 m`, the field says `3000`. | `memory/<tenant>/profile.md` § Conventions, as `numbered-option-unit` |
| **Custom keys: yes or no** | Whether groups and options carry a `key` (both accept one, default `""`). | Keys are for ERP joins. A tenant that sets them must set them **consistently from the first option**; a tenant that does not want them must say so, or an agent will helpfully add them. | Half-keyed catalogues cannot be joined. The `options-with-custom-keys` audit check is **opt-in via tenant memory** — without the recorded preference it does not run, so nobody is told. | `memory/<tenant>/profile.md` § **Preferences**, as `- **custom-keys**: never` (this exact shape is parsed by `validate_recommendation.py`) |
| **Base currency** | The currency of the base price list. | Every product derives its currency from it (P2-4). The `currency` field on a product is accepted and discarded. | Products created before the base price list exists are **already denominated wrong**, and no error was raised. Fixing it means re-creating them. | The base price list itself (step 3) + `profile.md` § Conventions |
| **Base language + `default_language`** | The `is_base: true` language and the company's `default_language`. Also the exact spelling of the code (`EN-US` vs `en_US`). | Every entity has a `language` (default `"DE"`). Entities created before the base language exists inherit the fallback. | Mixed-language catalogues where half the entities carry a code that matches nothing. `code` is a free-form string of 2–8 chars — nothing normalises it. | Steps 1–2 + `profile.md` § Conventions |
| **`config_code_prefix`** | ≤ 10 chars, prefixes every saved configuration code. Customer-visible. | Configuration codes are handed to end customers and quoted back to support. | **Existing codes do not migrate.** You get two generations of code in the wild and no way to tell which is which. | Step 1 + `profile.md` § Conventions |

## Output contract

Onboarding emits one report. Same shape as `rattle-apply-config` (`applied` / `skipped` / `errors`), plus the three things only a day-0 run produces: the preflight verdict, the conventions, and the baseline audit.

```json
{
  "tenant": "acme",
  "onboarded_at": "2026-07-14T09:00:00+00:00",
  "preflight": {
    "products_found": 0,
    "company_name": null,
    "verdict": "empty-tenant — proceed"
  },
  "applied": [
    {"step": 1, "type": "ensure_company_settings", "name": "acme GmbH", "action": "updated", "id": 1, "request_id": "req_..."},
    {"step": 2, "type": "ensure_language", "name": "DE", "action": "created", "id": 7, "request_id": "req_..."},
    {"step": 3, "type": "ensure_price_list", "name": "Standard", "action": "created", "id": 3, "request_id": "req_..."},
    {"step": 5, "type": "ensure_area", "name": "Widget Pro — Konfiguration", "action": "created", "id": 88, "request_id": "req_..."},
    {"step": 6, "type": "ensure_configurator_settings", "name": "company", "action": "updated", "id": 1, "request_id": "req_..."},
    {"step": 7, "type": "ensure_product", "name": "Widget Pro", "action": "created", "id": 401, "request_id": "req_..."}
  ],
  "skipped": [
    {"type": "ensure_language", "name": "DE", "reason": "noop — already matches"}
  ],
  "conventions": {
    "article_number_key": "integration_metadata.article_number",
    "part_cost_unit": "EUR_whole",
    "numbered_option_unit": "mm",
    "custom_keys": "never",
    "base_currency": "EUR",
    "base_language": "DE",
    "config_code_prefix": "ACME"
  },
  "baseline_audit": {"errors": 0, "warnings": 0, "info": 0},
  "memory_written": "memory/acme/profile.md",
  "errors": []
}
```

**Onboarding-tier operations.** Six `ensure_*` types, all idempotent get-or-create by natural key:

| Operation | Natural key | REST |
|---|---|---|
| `ensure_company_settings` | singleton (the company) | `GET /company` → `PATCH /company` with only the differing fields |
| `ensure_language` | `code` | `GET /languages` (not paginated) → `POST /languages` |
| `ensure_price_list` | `name` | `GET /price-lists` → `POST /price-lists`. Exactly one `is_base: true`. |
| `ensure_configurator_settings` | singleton (the company) | `GET /company/configurator-settings` → `PATCH /company/configurator-settings`. **No schema validation — read back to verify.** |
| `ensure_area` | `name` | `GET /areas?search=<name>` → `POST /areas`; attach via `POST /products/{productId}/areas` |
| `ensure_product` | `name` | `GET /products?search=<name>` → `POST /products`. **Never send `currency`.** |

`ensure_area` and `ensure_product` are the same operations `rattle-apply-config` defines — identical semantics, identical natural keys. The first four are new in this tier and are executed by the `rattle-onboarder` agent, not by `rattle-config-builder`.

## Handing off

```
rattle-onboarding      empty tenant → company, languages, base price list,
                       conventions, areas, settings, first product   ← you are here
  └→ rattle-ingest             the customer's pricelist → source-mapping.json + normalized rows
       └→ rattle-pricelist-analysis   → anti-pattern findings
            └→ rattle-suggest-config  → recommendation.json
                 └→ rattle-apply-config   → idempotent ensure_* writes
  └→ rattle-audit              baseline: the 6 structural checks (step 8)
  └→ rattle-tenant-memory      profile.md with every day-0 decision (step 9)
```

- **Never skip step 3 to get to step 7 faster.** The currency trap is silent and it is the reason this skill exists.
- **Do not hand-build the customer's configuration** after step 7. `rattle-ingest` exists so that a missing standard variant becomes a **blocker**, not an invented option. An onboarding that guesses the standard variant has already violated the `#1 rule`.
- **A BOM comes last.** `rattle-bom-builder` / `rattle-bom-architect` need options to hang `usage_subclauses` on; they cannot run before the configuration exists.
- **Document templates come last too.** An `offer` template must attach `dynamic:document_configuration`; a `quote` template must attach `dynamic:document_line_items`. `GET /documents/doc-types` returns the registry. See `rattle-document-templates`.

## Reference files

| File | Use when |
|---|---|
| `references/day-zero-checklist.md` | You are actually doing it — an operator-grade checklist with the exact HTTP call and expected response for every step |
| `references/configurator-settings.md` | You are at step 6 — all 19 flags, their defaults, and the UX consequence of each |

## Related skills

- `rattle-configurator` — the #1 rule and the data model. Load it first, always; it governs the first product exactly as it governs the thousandth.
- `rattle-ingest` — the next step. The customer's pricelist goes here, never straight into a hand-built configuration.
- `rattle-apply-config` — the idempotent `ensure_*` grammar this skill's onboarding tier extends.
- `rattle-audit` — the baseline audit at step 8.
- `rattle-tenant-memory` — where every day-0 decision is recorded at step 9, and where every later session reads it back.
- `rattle-api` — REST mechanics: auth, pagination, the OCC headers the spec does not declare.
