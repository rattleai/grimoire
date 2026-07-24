# Quote line items in depth

A line item is where a configured machine becomes a number on a document a customer signs. It is the highest-consequence write in the bundle: wrong here and the customer is quoted the wrong price for the wrong thing, in writing.

Endpoints (5 of the 20 quote operations):

```
GET    /api/v1/quotes/{id}/line-items                 list
POST   /api/v1/quotes/{id}/line-items                 create   → 201
PATCH  /api/v1/quotes/{id}/line-items/{item_id}       partial update
PUT    /api/v1/quotes/{id}/line-items/{item_id}       full update
DELETE /api/v1/quotes/{id}/line-items/{item_id}       remove
```

`GET /quotes/{id}` also returns the quote **with embedded line items** — one call, not two, when you only need to read.

## 1 · The contract

### `LineItemCreateRequest` — `additionalProperties: false`

| Field | Type | Required | Notes |
|---|---|---|---|
| `product_id` | integer | **yes** | The only required field. FK to the product. |
| `configuration_code` | string \| null | no | **The link back to what the customer configured.** See § 2. |
| `quantity` | integer | no | Default `1`. Integer — see § 4. |
| `unit_price` | number \| string \| null | no | **Two money types in one field.** See § 3. |
| `discount_percent` | number \| null | no | 0–100. |
| `notes` | string \| null | no | ≤ 2000. |
| `integration_metadata` | object \| null | no | Your ERP join key lives here. |

### `LineItemUpdateRequest` — `additionalProperties: false`

| Field | Type | Notes |
|---|---|---|
| `quantity` | integer \| null | `exclusiveMinimum: 0` on **update** — but merely `integer` with default `1` on create. **`quantity: 0` is creatable and not updatable.** |
| `unit_price` | number \| string \| null | |
| `discount_percent` | number \| null | 0–100 |
| **`discount_amount`** | number \| string \| null | **UPDATE-ONLY.** Not on the create request. |
| **`position`** | integer \| null | **UPDATE-ONLY.** `minimum: 0`. The line's order on the document. |
| `notes` | string \| null | ≤ 2000 |
| `integration_metadata` | object \| null | |

> **`product_id` and `configuration_code` are CREATE-ONLY.** Neither appears on `LineItemUpdateRequest`. **A line item cannot be re-pointed at a different product or a different configuration.** To change either, DELETE the line and POST a new one. This is correct behaviour (immutable FKs — audit § P3-2 explicitly endorses it) but it is not stated anywhere the caller will see it, and an agent that tries to "just PATCH the configuration_code" will get a `422` on a field it believes exists.

### `QuoteLineItemResponse`

Reads back: `id`, `product_id`, `product_name`, **`product_sku`**, `configuration_code`, **`configuration_code_display`**, `quantity`, `unit_price`, `discount_percent`, `discount_amount`, `line_total`, `position`, `notes`, `integration_metadata`.

All money on the response is a **decimal string** (`unit_price`, `discount_amount`, `line_total`).

## 2 · `configuration_code` — the linkage

**This is the field that makes a quote line traceable.** Without it the line says "one Widget Pro, €24,000" and nothing on earth can reconstruct which Widget Pro. With it, the line resolves to the exact option set, the exact BOM, and the exact price snapshot the customer saw.

```
GET /api/v1/configurations/states/by-code/{code}              → ConfigurationStateResponse
GET /api/v1/configurations/states/by-code/{code}/selections   → each selected option, enriched
GET /api/v1/configurations/states/by-code/{code}/parts        → the BOM for that configuration
```

Those three routes are the entire reason to carry the code: **the sales document, the option list and the shop-floor BOM all dereference from one string.**

### Which string goes in it?

**The spec does not say.** Three candidate strings exist, and `configuration_code` is typed as a bare nullable string with no `format`, no `pattern`, and no stated referential integrity:

| Candidate | Where it comes from |
|---|---|
| `ConfigurationStateResponse.config_code` | `POST /configurations/calculate`, `GET /configurations/states/*` |
| `ConfigurationResponse.display_code` | `GET /configurations`, `GET /configurations/{id}` |
| `ConfigurationResponse.config_token` | same |

And `QuoteLineItemResponse` echoes back **both** `configuration_code` **and** `configuration_code_display` — which is direct evidence that the *stored* value and the *human-visible* value are not the same string. (The display form is very likely the one carrying the company's `config_code_prefix` — see `rattle-onboarding` step 1. **Likely. Not verified.**)

One further data point: `GET /documents/templates/{id}/validate-config` takes a query parameter `config_token` whose description is **"Configuration token or code"** — so *that* route accepts either form. Nothing says `configuration_code` on a line item is equally forgiving.

> ### The rule: round-trip before you send
>
> **Resolve the exact string first, then send what resolved.**
>
> ```
> GET /api/v1/configurations/states/by-code/<candidate>   → 200 ⇒ this string dereferences
>                                                          → 404 ⇒ do NOT put it on a line item
> ```
>
> This is a read-only, zero-cost check, and it converts an unverifiable guess into a verified fact. **Do it every time.** A `configuration_code` that does not resolve produces a line item that is accepted with a `201`, renders on the PDF, and points at nothing — the worst available outcome, because it *looks* correct.

### And finalize first

Per `SKILL.md` § "Finalize before you quote": **`POST /configurations/{id}/finalize` before the code goes on the line.** An unlocked configuration behind a sent quote can change after the customer has the PDF. The line item schema will not check this for you — `configuration_code` has no `is_finalized` precondition anywhere in the API.

## 3 · The money-type trap (audit § P0-5)

**`unit_price` is `number | string | null` on the request and `string` on the response.** The same value, two types, depending on the direction of travel.

Across the funnel the money types are:

| Where | Type |
|---|---|
| `LineItemCreateRequest.unit_price`, `discount_amount` | `number \| string \| null` |
| `QuoteLineItemResponse.unit_price`, `discount_amount`, `line_total` | **decimal string** |
| `QuoteResponse.total_amount`, `final_amount`, `discount_amount`, `tax_amount` | **decimal string** |
| `QuoteDetailsUpsertRequest.shipping_cost` | **string** |
| `QuoteAnalyticsSnapshotResponse.total_amount`, `final_amount`, … | **float** |
| `PartCreateRequest.part_cost` | **integer** (!) |

**Seven type-sets across 76 money fields in the API. This one field family spans four of them.**

### The rules

1. **Send decimal-as-string.** `"1250.00"`, never `1250.0`. It round-trips with the response type, it survives JSON serialisation, and it never acquires a binary-float artefact.
2. **Parse to `Decimal`, never to `float`.** `float("0.1") + float("0.2") != 0.3` and the difference lands on an invoice. Python: `decimal.Decimal("1250.00")`.
3. **Never sum the analytics floats and present the result as money.** `QuoteAnalyticsSnapshotResponse` totals are genuinely `number` (float). They are fine for a chart. They are not fine for a document.
4. **Never do arithmetic across the string/float boundary.** An agent that reads `total_amount` as a string, `part_cost` as an integer, and an analytics total as a float, then adds them, gets a plausible-but-wrong number **with a `200 OK` on every call.** Nothing in the API will ever tell you.
5. **Do not compute `line_total` yourself and send it.** There is no `line_total` field on either request schema — it is derived server-side from `quantity`, `unit_price` and the discount. Read it back; do not predict it.

## 4 · `quantity` is an integer

`quantity` is `integer` on create (default `1`) and `integer, exclusiveMinimum: 0` on update. **A line item cannot express 2.5 units.**

This is the same integer-only floor as numbered options (audit § **P2-3**), and it lands in the same place: anything sold by length, area, weight or volume cannot be quoted at a fractional quantity. **The workaround is the tenant's day-0 unit convention** — model in mm, quote in mm, and let the BOM factor divide back (`rattle-onboarding` § "Decisions you must make on day 0", `numbered-option-unit`).

**Read the tenant's `numbered-option-unit` from `memory/<tenant>/profile.md` before you set a quantity.** A quote line of `3` where the tenant means millimetres, or `3000` where the customer reads metres, is an off-by-1000 error on a signed document. This is precisely the failure that day-0 convention exists to prevent — and the quote line is where it finally becomes visible, to the customer, in writing.

## 5 · The discount needs a second call — twice

At **quote** level (audit § **P3-2**):

- `discount_amount`, `discount_percent`, `tax_amount`, `terms_and_conditions` are on `QuoteUpdateRequest` and **absent from `QuoteCreateRequest`**.
- **You cannot create a discounted quote in one call.** `POST /quotes` → `PATCH /quotes/{id}`.

At **line-item** level:

- `discount_percent` **is** creatable. `discount_amount` is **not** — it is update-only.
- So a **percentage** discount can go on in one call; an **absolute** discount (`"250.00"` off this line) needs `POST /quotes/{id}/line-items` → `PATCH /quotes/{id}/line-items/{item_id}`.

### Why this is a failure mode and not a nuisance

**A crash, timeout or rate-limit (`429`) between the two calls leaves a quote at full list price** — with correct customer, correct product, correct configuration, and no discount. It is not obviously broken. It is a perfectly plausible full-price quote, and if nobody notices, it is the one that gets sent.

**Therefore:**

- Treat POST + PATCH as **one logical operation** and report it as one. If the PATCH fails, the operation failed — say so loudly, name the quote id, and state that a full-price quote now exists in the tenant.
- **Never report `applied` for a discounted quote whose PATCH did not land.**
- On `429`, back off and retry the PATCH. (`Retry-After` is not declared on any Rattle operation — audit § P3-3 — so use exponential backoff.)

## 6 · Idempotency

**There is no natural key on a line item.** `POST /quotes/{id}/line-items` twice creates **two lines** for the same product and the same configuration, and the quote total silently doubles.

The builder convention (**not** a backend invariant — nothing in Rattle enforces it):

> Natural key: **`(quote_id, product_id, configuration_code)`**.

```
GET /api/v1/quotes/{id}/line-items
  → match on (product_id, configuration_code)
  → absent          → POST
  → present, differs → PATCH only the differing fields
  → present, same    → noop
```

When several identical products with **the same** configuration are genuinely wanted, that is `quantity: n` on **one** line — not *n* lines. If a tenant genuinely needs *n* separate lines for the same product+configuration (staggered delivery dates, per-line notes), the convention above cannot distinguish them: **disambiguate with your own key in `integration_metadata` and match on that instead.** Say which convention you used in the run report.

## 7 · `product_sku` renders `null`, always (audit § P2-1)

```jsonc
QuoteLineItemResponse.product_sku   { "anyOf": [{"type": "string"}, {"type": "null"}], "default": null }
```

**`product_sku` is populated from `Product.sku` — which now exists** as a settable field on `ProductCreateRequest` / `ProductUpdateRequest` (`string ≤255`, the ERP article-number join key; unique per tenant, a duplicate returns `409`; filter with `GET /products?sku=`). Set the product's `sku` and it flows through to the line item's `product_sku`.

- **A SKU column on the quote PDF works** — as long as the underlying product carries a `sku`. If `product_sku` reads back `null`, the product simply has no `sku` set; the field is no longer unwritable.
- **The article number lives in `product.sku`** (unique per tenant; filter with `GET /products?sku=`), and flows to `QuoteLineItemResponse.product_sku`. A pre-`sku` tenant may still carry it in `product.integration_metadata.<key>` (the `article-number-key` day-0 convention) — backfill it into `sku`.
- When a user asks why the SKU column is empty, **say this**. It is the single most commercially significant gap in the API, it is Rattle's to fix, and it is not a bug in the tenant's data.
