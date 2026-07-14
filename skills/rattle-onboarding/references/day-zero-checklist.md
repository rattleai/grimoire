# Day-zero checklist

Operator-grade. Tick through it in order. Every step gives the exact HTTP call and the response you should see; if you see something else, stop rather than continue.

**Base URL:** `https://www.rattleapp.de/api/v1`. Paths below are relative to it.

> **The double-prefix trap (P0-6).** The spec declares `servers: [{"url": "/"}]` while every path key already embeds `/api/v1`. Concatenating the documented base URL with a spec path yields `/api/v1/api/v1/products` → `404`. Every generated client hits this. Use `https://www.rattleapp.de` + the spec path, **or** `https://www.rattleapp.de/api/v1` + the path with the prefix stripped. Not both.

> **User-Agent.** Cloudflare returns **1010 / `browser_signature_banned`** to the default `python-urllib` UA. It looks exactly like an auth failure and is not. Send a real `User-Agent` on every request.

Auth on every call:

```
Authorization: Bearer rk_live_...
User-Agent: grimoire/1.0
```

Every response is wrapped in a `{"data": …}` envelope (363 of 389 JSON 2xx responses; the exceptions are all batch endpoints, which you do not need on day 0).

---

## ☐ Step 0 — Preflight (read-only, and it is a gate)

**0a. The key resolves and the company exists.**

```bash
curl -s -H "Authorization: Bearer $RATTLE_API_KEY" -H "User-Agent: grimoire/1.0" \
     "https://www.rattleapp.de/api/v1/company"
```

Expect **200**:

```json
{"data": {"id": 1, "company_name": null, "company_url": null,
          "config_code_prefix": null, "custom_domain": null,
          "custom_domain_verified": false, "default_language": "DE"}}
```

A fresh tenant has `null`s. A **401** means the key is wrong or unscoped; a **403** means the key lacks the scope. Onboarding needs `products:write` and `prices:write` at minimum.

**0b. THE GATE — the tenant must have no products.**

```bash
curl -s -H "Authorization: Bearer $RATTLE_API_KEY" -H "User-Agent: grimoire/1.0" \
     "https://www.rattleapp.de/api/v1/products?limit=1"
```

Expect **200** with an empty list:

```json
{"data": [], "meta": {"next_cursor": null}}
```

- `data: []` → **proceed.**
- `data: [ … ]` → **STOP. Do not onboard.** The conventions in step 4 have already been decided implicitly by whoever created those products. Route the user to `rattle-audit` (see the state) or `rattle-ingest` (add data) and report what you found.

**0c. No tenant memory yet.**

```bash
test -f memory/<tenant>/profile.md && echo "EXISTS — not a new tenant" || echo "absent — proceed"
```

---

## ☐ Step 1 — Company settings

`PATCH /company` · schema `CompanySettingsUpdateRequest` · **all four fields optional**, `additionalProperties: false` (a typo'd field is a loud **422** — good).

| Field | Type | Constraint |
|---|---|---|
| `company_name` | string \| null | 1–255 |
| `company_url` | string \| null | ≤ 255 |
| `config_code_prefix` | string \| null | ≤ 10 |
| `default_language` | string \| null | ≤ 8 |

**Idempotent:** `GET /company` first; PATCH **only the fields that differ**.

```bash
curl -s -X PATCH -H "Authorization: Bearer $RATTLE_API_KEY" \
     -H "User-Agent: grimoire/1.0" -H "Content-Type: application/json" \
     -d '{"company_name": "acme GmbH",
          "company_url": "https://acme.example",
          "config_code_prefix": "ACME",
          "default_language": "DE"}' \
     "https://www.rattleapp.de/api/v1/company"
```

Expect **200** with the updated `CompanySettingsResponse`. Verify `config_code_prefix` came back exactly as sent — it prefixes every configuration code the customer will ever see, and **existing codes do not migrate** if you change it.

---

## ☐ Step 2 — Languages (base language first)

`POST /languages` · schema `LanguageCreateRequest` · **required `code`, `name`**; optional `is_base` (default `false`).

| Field | Type | Constraint |
|---|---|---|
| `code` | string | **required**, 2–8 chars |
| `name` | string | **required**, 1–50 chars |
| `is_base` | boolean | default `false` |

**Create the base language first.** It should match the `default_language` set in step 1.

```bash
curl -s -X POST -H "Authorization: Bearer $RATTLE_API_KEY" \
     -H "User-Agent: grimoire/1.0" -H "Content-Type: application/json" \
     -d '{"code": "DE", "name": "Deutsch", "is_base": true}' \
     "https://www.rattleapp.de/api/v1/languages"
```

Expect **201** (or **200**; POST success codes vary across the API — P3-4):

```json
{"data": {"id": 7, "code": "DE", "name": "Deutsch", "is_base": true, "order_index": 0, "links": {…}}}
```

Then any additional languages with `is_base: false`:

```bash
-d '{"code": "EN-US", "name": "English (US)"}'
```

**Idempotent:** natural key is `code`.

```bash
curl -s … "https://www.rattleapp.de/api/v1/languages"   # not paginated: no cursor/limit params
```

Skip the POST if the code is already present.

> **The code is a convention.** `code` is a free-form 2–8-char string. `EN-US`, `en-US` and `en_US` are three different strings to this API and nothing normalises them. A live tenant carries `DE` + `EN-US`. **Record the spelling you chose** — every entity's `language` field must match it.

---

## ☐ Step 3 — Base price list ← **BEFORE ANY PRODUCT**

`POST /price-lists` · schema `PriceListCreateRequest` · **required `name`**.

| Field | Type | Constraint |
|---|---|---|
| `name` | string | **required**, 1–255 |
| `currency` | string | ≤ 3, default `"EUR"` |
| `description` | string | ≤ 2000, default `""` |
| `is_base` | boolean | default `false` |

```bash
curl -s -X POST -H "Authorization: Bearer $RATTLE_API_KEY" \
     -H "User-Agent: grimoire/1.0" -H "Content-Type: application/json" \
     -d '{"name": "Standard", "currency": "EUR", "is_base": true}' \
     "https://www.rattleapp.de/api/v1/price-lists"
```

Expect **201/200**:

```json
{"data": {"id": 3, "name": "Standard", "currency": "EUR", "description": "",
          "is_base": true, "order_index": 0,
          "created_at": "…", "updated_at": "…", "links": {…}}}
```

> ### ⚠ This is the step the whole ordering exists for.
>
> `ProductCreateRequest.currency` — verbatim from the spec:
>
> > *"Accepted but ignored — currency is derived from the company's base price list"*
>
> A product created **before** this base price list exists is denominated by the fallback, **not** by the `currency` you sent. `200 OK`, no error, wrong money. Verify `is_base: true` came back before you continue.

**Idempotent:** natural key is `name`. `GET /price-lists` first. **Exactly one** price list may be `is_base: true`.

Writes under `/price-lists/*` honour the **`X-Price-Lists-Version`** OCC header — send the version you read, retry once on **409** (the `detail` contains `Version conflict:`).

---

## ☐ Step 4 — Conventions (no API call — but do not skip it)

Get an **explicit human answer** to each. Do not default silently. These are written to `memory/<tenant>/profile.md` in step 9 and everything imported afterwards assumes them.

| ☐ | Decision | The question to ask the customer |
|---|---|---|
| ☐ | **Article-number key** | *"There is no SKU field on a Rattle product. Your article number has to live in `integration_metadata` under a key you choose. What should it be — `article_number`, `sku`, `sachnummer`? Whatever we pick, every product must use it forever; changing it later means re-importing everything."* |
| ☐ | **`part_cost` money unit** | *"`part_cost` is an integer — the API cannot store €12.50. Do we round to whole euros, or store cents as an integer? Costs roll up through the BOM, so this cannot change later without rescaling every part by 100×."* |
| ☐ | **Numbered-option unit** | *"Do you sell anything by length, area, weight or volume? Numbered options are integer-only — 2.5 m is unrepresentable. We model in mm and divide back in the BOM factor. The customer will see `3000` where they think `3 m`. Confirm the unit now; it is baked into every scaling afterwards."* |
| ☐ | **Custom keys** | *"Do groups and options need a `key` for an ERP join? If yes, we set them from the very first option. If no, we record `custom-keys: never` and the audit will flag any that appear."* |
| ☐ | **Base currency** | Confirmed by step 3. Record it. |
| ☐ | **Base language + code spelling** | Confirmed by steps 1–2. Record the exact spelling. |
| ☐ | **`config_code_prefix`** | Confirmed by step 1. Record it. |

---

## ☐ Step 5 — Areas

`POST /areas` · schema `AreaCreateRequest` · **required `name`**.

| Field | Type | Constraint |
|---|---|---|
| `name` | string | **required**, 1–255 |
| `product_id` | integer \| null | default `null` — *"Product to assign this area to"* |
| `area_group_id` | integer \| null | default `null` — *"AreaGroup to assign this area to"* |
| `allow_disable` | boolean | default `false` |
| `description` | string | ≤ 5000, default `""` |
| `language` | string | ≤ 8, default `"DE"` |
| `order_index` | integer \| null | default `null` (auto-assigned if omitted) |
| `price` | string | default `"0.00"` |

`product_id` is **optional**, so areas can exist before the first product:

```bash
curl -s -X POST -H "Authorization: Bearer $RATTLE_API_KEY" \
     -H "User-Agent: grimoire/1.0" -H "Content-Type: application/json" \
     -d '{"name": "Widget Pro — Konfiguration", "language": "DE", "price": "0.00"}' \
     "https://www.rattleapp.de/api/v1/areas"
```

Expect **201/200** with the new area id. It is now **unattached**, and therefore appears in the library:

```bash
curl -s … "https://www.rattleapp.de/api/v1/areas/library"
```

> ### `GET /areas/library` is NOT a starter-template library.
>
> Its own description: *"List areas not assigned to any product. Not paginated."* It is a **reuse pool of unattached areas.** On a fresh tenant it returns `{"data": []}` — verified, 0 areas on the live tenant. **Nothing seeds a new tenant with template content.** If the customer expects starter areas, tell them plainly there are none.

**Idempotent:** natural key is `name`. `GET /areas?search=<name>` (filters: `cursor`, `limit`, `product_id`, `search`).

**Rule `no-empty-areas` applies from the first area.** An area with zero groups is an audit **error** at step 8. Either fill it (step 7 / `rattle-suggest-config`) or do not create it yet.

---

## ☐ Step 6 — Configurator settings (the 19 flags)

`PATCH /company/configurator-settings`.

> **There is no schema.** The request body is an **inline** `{"type": "object", "additionalProperties": true}` — it is not in `components.schemas` at all. No field names, no types, no validation. **A typo'd flag is accepted with a `200` and does nothing.** Always read the settings back.

Read current state first:

```bash
curl -s -H "Authorization: Bearer $RATTLE_API_KEY" -H "User-Agent: grimoire/1.0" \
     "https://www.rattleapp.de/api/v1/company/configurator-settings"
```

Then PATCH only what differs. Full flag-by-flag contract, defaults and UX consequences: **`configurator-settings.md`** (this directory).

```bash
curl -s -X PATCH -H "Authorization: Bearer $RATTLE_API_KEY" \
     -H "User-Agent: grimoire/1.0" -H "Content-Type: application/json" \
     -d '{"allow_create_new_customer": true,
          "allow_select_existing_customer": true,
          "customer_search_fields": ["organization", "customer_id"],
          "start_search_digits": 3,
          "show_customer_organization": true,
          "require_customer_organization": true,
          "show_customer_email": true,
          "require_customer_email": true,
          "show_customer_id": true,
          "require_customer_id": false}' \
     "https://www.rattleapp.de/api/v1/company/configurator-settings"
```

Expect **200**. **Now GET it back and diff** — that is the only validation you have.

---

## ☐ Step 7 — First product

`POST /products` · schema `ProductCreateRequest` · **only `name` is required**.

| Field | Type | Constraint |
|---|---|---|
| `name` | string | **required**, 1–255 |
| `base_price` | string \| integer \| number | default `"0.00"` |
| `description` | string | ≤ 5000, default `""` |
| `is_active` | boolean | default `true` |
| `language` | string | ≤ 8, default `"DE"` |
| `catalog_meta` | object \| null | tags, badges, specs_summary, sort_priority, filters |
| `integration_metadata` | object \| null | **where the article number goes** |
| `currency` | string \| null | ⚠ *"Accepted but ignored"* — **never send it** |

```bash
curl -s -X POST -H "Authorization: Bearer $RATTLE_API_KEY" \
     -H "User-Agent: grimoire/1.0" -H "Content-Type: application/json" \
     -d '{"name": "Widget Pro",
          "base_price": "12000.00",
          "language": "DE",
          "integration_metadata": {"article_number": "WP-1000"}}' \
     "https://www.rattleapp.de/api/v1/products"
```

Expect **201** with a `Location` header (`Location` is missing on 15 of 78 creating POSTs across the API — P3-4 — so do not depend on it; read the id from the body).

**Verify the currency derived correctly:**

```bash
curl -s … "https://www.rattleapp.de/api/v1/products/401"
# → ProductResponse.currency should be the base price list's currency (EUR).
#   If it is not, step 3 was skipped or the base price list is not is_base.
```

**Attach the step-5 areas:**

```bash
curl -s -X POST -H "Authorization: Bearer $RATTLE_API_KEY" \
     -H "User-Agent: grimoire/1.0" -H "Content-Type: application/json" \
     -d '{"area_id": 88}' \
     "https://www.rattleapp.de/api/v1/products/401/areas"
```

**Idempotent:** natural key is `name`. `GET /products?search=<name>` (filters: `cursor`, `limit`, `search`, `status` — there is **no `?name=`** parameter; `search` is a case-insensitive ILIKE on `name` and `description`, so filter the result client-side for an exact match).

### ☐ Then STOP and hand off to `rattle-ingest`

Do **not** hand-build the customer's groups and options. Their pricelist goes through `rattle-ingest`, which refuses to invent a standard variant the pricelist does not state (the `#1 rule`, `explicit-options-for-all-variants`). An onboarding that guesses the standard variant has already broken the BOM.

For reference, when the options do come:

- `POST /groups` · `GroupCreateRequest` · **required `name`**; `area_id` optional; also `is_multi`, `is_required`, `selection_min`, `selection_max`, `key`, `description`, `language`, `order_index`.
- `POST /options` · `OptionCreateRequest` · **required `name` AND `group_id`**; also `price`, `recommended`, `key`, `is_numbered`, `number_min`, `number_max`, `number_step`, `number_unit`, `price_scalings`, `description`, `language`, `order_index`.
- Link a group to areas in **one** call: `POST /groups/{id}/areas` with body `{"area_ids": [88, 89]}` — note the **plural array**.

---

## ☐ Step 8 — Baseline audit

```bash
python skills/rattle-audit/scripts/audit_runner.py <tenant>
```

Runs the 6 structural checks. A day-0 tenant should come back clean:

```json
{"tenant": "acme", "ran_at": "…", "summary": {"errors": 0, "warnings": 0, "info": 0}, "findings": []}
```

The two you will realistically see:

| Finding | Cause | Minimum fix |
|---|---|---|
| `areas-without-groups` (**error**) | You created an area in step 5 and never filled it. | Add a group, or delete the area. |
| `offer-template-missing-configuration` (**error**) | An `offer` template was built without the `dynamic:document_configuration` attachment. | Attach it — see `rattle-document-templates`. |

Fix them now, while the catalogue is one product deep. This run is the baseline every later audit is compared against.

---

## ☐ Step 9 — Tenant memory

Write `memory/<tenant>/profile.md` with **every decision from step 4**. Show the file to the user and get consent — `rattle-tenant-memory` is **explicit-write only**.

```markdown
# acme — tenant preferences

## Conventions (decided at onboarding, 2026-07-14)
- **article-number-key**: `integration_metadata.article_number`
- **part-cost-unit**: whole EUR (part_cost is integer — the API cannot hold cents)
- **numbered-option-unit**: mm (length modelled in mm; BOM factor divides by 1000)
- **custom-keys**: never
- **base-currency**: EUR (base price list "Standard", id 3)
- **base-language**: DE (code spelled `DE`; secondary `EN-US`)
- **config-code-prefix**: ACME

## Preferences
- **custom-keys**: never
- **option-standard-variant**: always present, price 0, recommended=true
- **language**: de

## Style
- Area naming: `"<Product> — <Section>"` with em-dash separator
```

The `## Preferences` section is **parsed** — `set_preference()` and `validate_recommendation.py` read `- **<key>**: <value>` lines from it. Keep `custom-keys` in that exact shape. `## Conventions` and `## Style` are free-form prose the consultant reads.

Optionally record the decision:

```bash
rattle <tenant> memory record-decision "Onboarded 2026-07-14. Article number → integration_metadata.article_number; part_cost in whole EUR; numbered options in mm; custom keys never."
```

---

## Done

The tenant now has: company settings, a base language, a base price list (`is_base`, currency), recorded conventions, at least one area, deliberate configurator settings, one product, a clean baseline audit, and a memory profile every later session will honour.

**Next:** `rattle-ingest` with the customer's pricelist.
