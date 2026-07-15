# Rattle API — remediation plan

**For:** Rattle backend engineers
**Companion to:** [`API_AUDIT.md`](API_AUDIT.md) (the *why*) — this document is the *what to do*
**Verify with:** `python3 scripts/rattle_api_conformance.py` — a red/green test for every item here

---

## How to use this document

There are three artifacts, and they do different jobs:

| | |
|---|---|
| **`API_AUDIT.md`** | The diagnosis. 42 findings, each with evidence and consequence. Read it once. |
| **`API_REMEDIATION.md`** *(this)* | The prescription. Organised by **work**, not by finding. Copy-pasteable. |
| **`scripts/rattle_api_conformance.py`** | The test. **Run it. It is red on 27 checks.** Fix one, it goes green. |

**Start with the test, not the prose.**

```bash
git clone https://github.com/rattleai/grimoire.git && cd grimoire
python3 scripts/rattle_api_conformance.py            # fetches your live spec
```

```
Rattle API conformance — 463 operations · 210 schemas

── P0 — silent corruption (do everything right, still write wrong data)
  [FAIL] P0-1    The four required headers are declared as real parameters
  [FAIL] P0-2    Server-computed fields are marked readOnly
  ...
0 passed · 27 failed
failing: P0 15 · P1 3 · P2 6 · P3 3
```

It needs **no credentials, no tenant, no backend access** — only your published OpenAPI document. Drop it into your CI and gate on the exit code (which is the failure count), ratcheting down as you go:

```yaml
- run: python3 rattle_api_conformance.py --max-fail 27   # today's baseline; lower it as you fix
```

That single line means **a defect you fix cannot silently come back.**

---

## The one-sentence summary

> **Rattle's domain model is genuinely good. Rattle's *spec* describes a fraction of what the API knows — and the parts it omits are precisely the parts that corrupt data.**

Most of the highest-value work below is **not backend work at all.** It is metadata: declaring headers you already accept, marking fields you already compute, naming schemas you already return. **Wave 1 is a day of work and it removes every silent-corruption path in the API.**

---

## Why "silent" is the axis that matters

An endpoint that returns `422` teaches the caller something. An endpoint that accepts a payload, returns `200`, and quietly does nothing teaches the caller **a lie** — and in CPQ a lie propagates into a customer's BOM, their pricing, and the PDF they send to *their* customer with a signature on it.

Every P0 below is a path where a caller does everything the spec says and still writes wrong data.

This matters more now than it did two years ago, and here is the reason:

> **An integrator with backend access can find these. An autonomous agent — increasingly who is calling your API — cannot.**
>
> A human reads a prose caveat in a description and remembers it. An agent reads the machine-readable spec and does exactly what it says. Every gap between "what the spec says" and "what the API does" is a bug an AI will hit **at machine speed, in production, with no human checking its work.**

We know because we built one. Every finding marked *"we got this wrong"* is a bug that shipped in our own codebase, sourced from your spec.

---

# Wave 1 — One day. Removes every silent-corruption path.

**Nothing in this wave changes API behaviour.** It is metadata against behaviour the backend already implements. If you do nothing else in this document, do this.

## 1.1 — Declare the four headers you already accept · `P0-1`, `P0-1b`

**The spec declares ZERO header parameters across 463 operations.** Yet four are required, and the API says so — in prose:

| Header | Where you documented it | What it does |
|---|---|---|
| `X-Constraints-Version` | `POST /constraints` description | **Optimistic locking on an atomic replace-all** |
| `X-Price-Lists-Version` | `info.description` | Optimistic locking |
| `X-Idempotency-Key` | 8 batch descriptions ("24 h TTL") | **Safe retries** |
| `If-None-Match` | `GET /configurations/states/by-code/{code}` | ETag caching |

`POST /constraints` says it outright — *"Include the `X-Constraints-Version` header for optimistic concurrency control"* — and then declares `parameters` **not at all**, and no `409`.

> **The consequence.** Every generated client, SDK and agent reads `parameters` and sends no version header. Two users edit constraints concurrently; `POST /constraints` **replaces all pairs**; the second write **silently destroys the first with a `200 OK`**. The configurator then sells combinations that cannot be built.
>
> The client cannot even know it caused this.

**Do this:**

```yaml
components:
  parameters:
    ConstraintsVersion:
      name: X-Constraints-Version
      in: header
      required: true
      description: >
        Optimistic concurrency token. Read `constraints_version` from
        `GET /products/{id}`, send it back. A stale value returns 409.
      schema: { type: integer }

    IdempotencyKey:
      name: X-Idempotency-Key
      in: header
      required: false
      description: >
        Client-generated key, 24-hour TTL. A replay with the same key returns the
        original response instead of re-applying the operation.
      schema: { type: string, maxLength: 255 }

paths:
  /api/v1/constraints:
    post:
      parameters:
        - $ref: '#/components/parameters/ConstraintsVersion'
      responses:
        '409':
          description: Stale version — another writer changed the constraints first.
          content:
            application/problem+json:
              schema: { $ref: '#/components/schemas/ProblemDetails' }
```

Apply `IdempotencyKey` to all 8 batch endpoints, and — see 3.4 — to every singular `POST`.

**Done when:** `rattle_api_conformance.py --only P0-1` and `--only P0-1b` pass.

## 1.2 — Make `X-Price-Lists-Version` obtainable · `P0-9b`

`info.description` says *"read the current version from a GET response."* So we did:

```python
>>> sorted(spec["components"]["schemas"]["PriceListResponse"]["properties"])
['created_at','currency','description','id','is_base','links','name','order_index','updated_at']
# fields containing "version": NONE
```

**There is nothing to read.** The header is not merely undeclared — it is **unobtainable**. A client that somehow knew about it still could not construct it. Bulk price-override replacement has **no available concurrency defence.**

**Do this:** add the version to `PriceListResponse`, and state which field feeds which header.

```yaml
PriceListResponse:
  properties:
    version:
      type: integer
      readOnly: true
      description: Send as `X-Price-Lists-Version` on bulk-replace endpoints.
```

## 1.3 — Mark the 200 server-computed fields `readOnly` · `P0-2`

**`readOnly: true` appears ZERO times in the entire spec.** `writeOnly`: zero.

```
GET  /api/v1/products/{id}   → ProductResponse:      22 fields
PUT  /api/v1/products/{id}   → ProductUpdateRequest:  9 fields, additionalProperties: false

13 fields the server SENDS and then REFUSES back:
  id · created_at · updated_at · links · image_url · background_url · gallery_count
  public_token · areas_version · constraints_version · options_version
  parts_version · pricing_version
```

> **You cannot `PUT` back the object the API just gave you.** The most common REST idiom in existence — *fetch, change one field, send it back* — **returns `422`**, listing fields the caller never touched.

Across 45 resources that is **200 fields** every client must hand-strip.

**Do this — and it is genuinely free.** `readOnly: true` changes no behaviour; every code generator then omits those fields from request bodies **automatically**, and read-modify-write starts working for every client and every agent on the planet.

```yaml
ProductResponse:
  properties:
    id:                  { type: integer, readOnly: true }
    created_at:          { type: string, format: date-time, readOnly: true }
    constraints_version: { type: integer, readOnly: true }
    public_token:        { type: string, readOnly: true }
    # …and the other 196
```

**This is the single highest ratio of value to effort in the entire report.**

## 1.4 — Fix the `servers` double-prefix · `P0-6`

```json
"servers": [{"url": "/"}]
"paths":   { "/api/v1/products": … }
```

The natural base URL is `https://www.rattleapp.de/api/v1` — it is what your docs hand out. Concatenating it with a spec path yields `/api/v1/api/v1/products` → **`404`**. Every generated client hits this. We had to ship a `normalizePath()` shim and defend it with a test.

**Do this — pick either. Both are correct; the current combination is the one that isn't.**

```yaml
# Option A (recommended)
servers: [{ url: "https://www.rattleapp.de/api/v1" }]
paths:   { "/products": … }        # drop the prefix from path keys

# Option B
servers: [{ url: "https://www.rattleapp.de" }]
paths:   { "/api/v1/products": … } # keep the prefix
```

## 1.5 — Fix the `PATCH` that deletes your other languages · `P0-9i`

```
PATCH /api/v1/translations/dictionary/{entry_id}
  summary:     "Partially update a dictionary entry"
  description: "Same semantics as PUT — a supplied `translations` map
                replaces (does not merge)."
```

**The operation contradicts itself inside its own definition.**

```jsonc
PATCH /translations/dictionary/42   { "translations": { "ES": "husillo" } }
→ 200 OK
```

**English, French, Italian and German are now gone.** Silently. From the *company-wide* terminology glossary. The next machine translation of every document renders those terms however DeepL feels.

Every other `PATCH` in this API merges — which is exactly what makes this one lethal. An integrator who correctly learned `PATCH` from your other 38 paths **destroys data on their first try**, and the endpoint's own **summary** told them it was safe.

**Do this:** make `PATCH` merge (as its summary already promises), **or delete `PATCH`** and keep only `PUT`, whose *"Replace a dictionary entry"* summary is honest. **Do not keep a `PATCH` that replaces.**

## 1.6 — Fix the parameter whose default is outside its own maximum · `P0-9e`

```jsonc
// GET /configurations/states/by-code/{code}/parts
"limit": {
  "schema":      { "default": 200, "maximum": 100, "minimum": 1 },
  "description": "Max parts per page (default 200, max 500)"
}
```

**Three different numbers in one parameter.** The declared default is **schema-invalid against its own constraint**. A generated client sends `limit=200` — its own documented default — and gets a `422`.

**Do this:** pick one number. 30 seconds. It is the sort of thing that erodes trust in everything near it.

## 1.7 — Regenerate `ConfiguratorSettingsResponse` · `P0-7`

```python
# What the spec says GET /company/configurator-settings returns:
['custom_css', 'default_currency', 'require_login', 'show_prices', 'show_stock']   # 5

# What the live API actually returns:
['allow_create_new_customer', 'customer_search_fields', 'require_customer_organization',
 'start_search_digits', 'require_customer_contact_person', … ]                     # 20

# Overlap: NONE. Not one field in common.
```

And the write side accepts anything: `PATCH` body is `{"type": "object", "additionalProperties": true}`.

> **The spec's schema for this endpoint is entirely fictional.** An agent sets `show_prices` (does not exist) → `200`, nothing happens. It never discovers `require_customer_organization` — which governs the **entire customer-capture UX** of your configurator.

**Do this:** regenerate from the real model; give the `PATCH` body a real schema with `additionalProperties: false`; `422` unknown flags.

> **Open question for you:** `require_customer_info` has no `show_customer_info` sibling, unlike the other seven `require_*`/`show_*` pairs. **We could not determine whether it is a master switch, an independent requirement, or legacy — so we left it alone rather than guess.** Please clarify.

---

# Wave 2 — Two to three days. Makes the API programmable.

## 2.1 — Give `rule_json` a real schema, and `422` the legacy shape · `P0-4`

`ForbiddenRuleCreateRequest.rule_json`, in its entirety:

```json
{ "title": "Rule Json" }
```

No type. No description. No example. **This field decides which option combinations a customer is allowed to buy.**

> **This one bit us, and it is the cleanest illustration of the whole report.**
>
> The correct shape is `{"requires": [<clause>…], "invalid": [<option_id>…]}`. A **legacy array shape** — `[{"if": {...}, "then": {"forbid_options": [...]}}]` — is **accepted on write and silently dropped by the runtime evaluator.** The rule saves. Returns `200`. **Never fires.** The customer buys the forbidden combination, and nobody finds out until a machine ships with parts that do not fit.
>
> **We shipped that bug into our skills, our examples and our prompt templates. We got it from an example in your spec.** It took a line-by-line audit against backend source to catch. Every integrator who trusts the spec has it wrong right now.

**Do this. You already did it perfectly once — `UsageSubclause` is the best-documented field in your spec. Copy that pattern:**

```yaml
ForbiddenRuleJson:
  type: object
  additionalProperties: false
  required: [requires, invalid]
  description: >
    Conditional constraint. Clauses in `requires` are AND-folded; when they all
    hold, every option id in `invalid` becomes unselectable.
  properties:
    requires:
      type: array
      items: { $ref: '#/components/schemas/RuleClause' }
    invalid:
      type: array
      items: { type: integer, description: Option id made invalid. }

RuleClause:
  oneOf:
    - { type: object, required: [anyOf],           properties: { anyOf:           { type: array, items: { type: integer } } } }
    - { type: object, required: [allOf],           properties: { allOf:           { type: array, items: { type: integer } } } }
    - { type: object, required: [groupSelections], properties: { groupSelections: { type: object, additionalProperties: { type: array, items: { type: integer } } } } }
```

Then: **reject the legacy array with a `422`.** A loud failure is worth a hundred silent ones. If back-compat demands it stays accepted, mark it `deprecated: true` and **say in the description that it does not execute.** And purge the legacy `{if, then}` examples from the spec — they are the source of the infection.

## 2.2 — Document the pricing resolution order · `P0-8` · **the most consequential item in this document**

**Six mechanisms can set the price of a single option:**

| # | Mechanism | Keyed on |
|---|---|---|
| 1 | `Option.price` | the option |
| 2 | Option price-override | (option, area, price_list) — all three required |
| 3 | **Advanced price** | (option, `condition_option_id`, area?, price_list?) — *conditional* |
| 4 | Area / Product price-override | (area\|product, price_list) |
| 5 | Pricing preset | product-level fee/surcharge |
| 6 | **`PUT /options/{id}/area-config`** | carries a `price` — **with no price list at all** |

**Nowhere in the spec is the resolution order stated.** We grepped all 463 operations and 210 schemas:

```
"precedence"       → 1 hit — and it is about usage_subclauses BOOLEAN OPERATORS, in the BOM
"resolution order" → 0     "takes priority" → 0
"most specific"    → 0     "falls back"     → 0
```

> A tenant sets an option override **and** an area override for the same option and price list. **Which does the customer pay?**
>
> The API knows. The spec does not say. The client cannot know — **and it will not error.** It returns a price. A plausible one. Possibly the wrong one, **on a document with your customer's signature on it.**
>
> Every other silent-wrongness finding in this report costs a BOM line or a retry. **This one costs money.**

**We refused to guess.** Our pricing skill asserts **no precedence table**, because any table we wrote would be a fabrication — and *indistinguishable from the outside* from a documented fact. (That is not hypothetical: we already shipped exactly that bug with `expand=areas.groups.options`, which seemed right, was not contradicted by the spec, and **had never worked**.) Instead we teach agents to reverse-engineer your pricing behaviour empirically, per tenant, using `/configurations/calculate` as an oracle.

**That is a workaround for a documentation gap, and it should not be necessary.**

**Do this — one paragraph:**

```yaml
info:
  description: |
    ## Pricing resolution
    When several mechanisms set a price for the same option, they resolve in this order
    (first match wins):
      1. Advanced price (condition_option_id matches a selected option)
      2. Option price-override   (option, area, price_list)
      3. Area/Product price-override (area|product, price_list)
      4. area-config price       (option, area — no price list)
      5. Option.price            (the base)
    Pricing presets are additive fees applied after the option price is resolved.
```

*(The order above is a **template**, not our claim — fill in the real one.)*

**And then make it auditable**, which is the part that turns this from a fix into a feature:

```yaml
# POST /configurations/calculate → response
price_breakdown:
  type: array
  description: Per-option, which mechanism supplied the final number.
  items:
    type: object
    properties:
      option_id:  { type: integer }
      price:      { type: string, description: Decimal. }
      source:     { type: string, enum: [base, option_override, advanced_price,
                                         area_override, product_override, area_config, preset] }
      source_id:  { type: integer, nullable: true }
```

**For a CPQ system, an auditable price is close to a compliance requirement.** Nobody else in this market has it.

## 2.3 — Name and describe `advanced-prices` · `P0-9`

Five operations. Schemas **inline, not in `components`**. Summary: *"Create an advanced price."* Description: **`null`**.

The entire published definition of the mechanism:

```json
{ "properties": { "advanced_price":      {"type": "string"},
                  "area_id":             {"type": "integer"},
                  "condition_option_id": {"type": "integer"},
                  "price_list_id":       {"type": "integer"} },
  "required": ["condition_option_id", "advanced_price"] }
```

`condition_option_id` is **required** — which tells us, **by inference from a field name alone**, that this is a **cross-option conditional price**: *this option costs X when that other option is also selected.*

> Bundle pricing. Cross-sell discounts. *"The premium paint is cheaper if you also take the premium trim."*
>
> **That is a datasheet feature — and it is undiscoverable. You have built something valuable that nobody can use.**

**Do this:** name `AdvancedPriceCreateRequest` / `AdvancedPriceResponse`, write **one sentence** of description, add an example. Twenty minutes, on a feature presumably worth considerably more.

## 2.4 — Make unknown fields fail consistently · `P0-10`, `P0-9c`

`additionalProperties: false` is set on **116 of 124** request schemas — which is *good*, and means a typo gets a loud `422`.

The **8 exceptions** are the danger, precisely *because* they are exceptions — and the inconsistency lives **inside a single resource family, on the money path**:

| Endpoint | Body | Typo behaviour |
|---|---|---|
| `POST /options/{id}/price-overrides` | named `PriceOverrideCreateRequest` | **`422`** ✅ |
| `POST /products/{id}/price-overrides` | named | **`422`** ✅ |
| **`POST /areas/{id}/price-overrides`** | **inline, unnamed** | **swallowed, `201`** ❌ |

Plus: `QuoteDetailsUpsertRequest`, `QuoteContactAddRequest`, `PartGroup{Create,Update}Request`, `GroupAreaLinkRequest`, `GalleryReorderRequest`, `CompanyContact{Create,Update}Request`, `advanced-prices`, `area-config`.

> An integrator writes the option override, gets a clean `422` on a typo, and reasonably concludes **the API validates**. They then write the *area* override — same concept, adjacent endpoint — and their typo'd field **vanishes with a `201`**.

**Do this:** name every inline body and set `additionalProperties: false`. The API is currently strict about fields it does not know and permissive about fields it knows and discards — **that is backwards.**

## 2.5 — Stop returning `200` for writes you discard · `P2-4`

`ProductCreateRequest.currency` — its own description:

> *"Accepted but ignored — currency is derived from the company's base price list"*

But `currency` **is** returned on `ProductResponse`. A client writes `"USD"`, gets `200 OK`, reads back something else, and **never sees an error.**

Same class: `UsageSubclause.operator` is *"ignored on the first term"* — an author who writes `operator: AND` on clause 0 gets `OR` with **no warning**.

**Do this:** remove `currency` from the request schemas, or `422` it when supplied. **Never `200` a write you discard.** (Being honest in the description is good. Not accepting it at all is better.)

## 2.6 — Disambiguate `PUT` vs `PATCH` · `P0-3`

- **39 paths expose both. On 37, the request body is byte-identical.**
- **43 of 47 `PUT` bodies have no `required` array** — every field optional.
- 21 `PUT`-only paths; **0** `PATCH`-only.

> RFC 9110 says `PUT` **replaces**. An all-optional `PUT` body says it **merges**. The spec does not disambiguate — so an agent applying standard REST semantics (GET → change one field → PUT) either works fine or **silently nulls every field it omitted.** It cannot tell which. **Neither could we.**

**Do this:** one verb per path. Make `PUT` replace (with `required` fields) and `PATCH` merge. If `PUT` really merges today, **say so explicitly** — but the honest fix is to make it behave.

---

# Wave 3 — A sprint. Makes the API discoverable.

## 3.1 — Promote the 119 enum-shaped free strings to `enum` · `P1-1`

The spec has **14 enums**. It has **119 string fields whose names are unambiguously enum-shaped** (`*_type`, `status`, `state`, `*_mode`, `stage`, `role`, `category`) typed as free strings.

And **7 fields are an enum on one schema and a free string on another** — the vocabulary is known, it is just not published where it is needed:

| Field | Enum in | Free string in |
|---|---|---|
| **`doc_type`** | `CloneRequest` = `['offer','technical_doc','ccms','custom']` | **`DocumentTemplateCreateRequest`** — the primary create endpoint! |
| `attr_type`, `method`, `inheritance_mode`, `format`, `execution_mode`, `status` | their Request | their Response |

Also: `CombinationRuleCreateRequest.rule_type` is a **regex `pattern`**, not an enum — codegen emits `string`, not a union.

> `POST /documents/templates` with `doc_type: "datasheet"` **passes schema validation.** `additionalProperties: false` rejects unknown *keys*, never unknown *values*.

**And the one `doc_type` enum you do have is missing `quote`** (`P2-6`) — which, on the face of it, means **you cannot clone a quote template.**

**Do this:**

```yaml
DocType:
  type: string
  enum: [offer, quote, technical_doc, ccms, custom]      # ← quote was missing

DocTypeFilter:   # reads only
  type: string
  enum: [offer, quote, technical_doc, ccms, custom, offers, quotes, technical_documentation]
  # the last three are legacy — mark them deprecated
```

Reference `DocType` from every request, response and query parameter.

## 3.2 — Publish the sales lifecycle · `P2-1b`

The quote/opportunity lifecycle is the **commercial core of a CPQ system**. Not one of its states is declared:

```jsonc
QuoteStatusUpdateRequest.status  { "type": "string", "maxLength": 50 }   // no enum
QuoteResponse.status             { "type": "string", "default": "draft" }
OpportunityCreateRequest.stage   { "type": "string", "default": "qualification" }
OpportunityResponse.status       // a THIRD state field — settable on NO request schema
```

`GET /quotes?status=` filters on values documented **nowhere**. `status: "aproved"` (typo) is a schema-valid request.

> A client cannot render a pipeline, a funnel, or a status dropdown without **hard-coding a guess**. It cannot know the legal transitions. Every `switch` on quote status has a `default` branch that is, in practice, where the bugs live.

**We could not establish the vocabulary.** Read-only observation surfaced `draft`/`approved` and `qualification` — and observed values are not the enum. Determining the rest would require *writing* to a live tenant, which we would not do.

**So we are asking rather than guessing: what are the full status and stage vocabularies, and what transitions are legal?**

**Do this:** declare `QuoteStatus` and `OpportunityStage` as enums; document the legal transitions, even as prose. **This is the single change that makes the CPQ half of your API programmable.**

## 3.3 — Describe the fields an integration writes · `P1-2`

| | count | share |
|---|---|---|
| Schema fields with **no** `description` | 1,274 / 1,369 | **93%** |
| Operations with **no** `description` | 294 / 463 | **63%** |
| Operations with no `summary` | 0 / 463 | **0%** ✅ |

Summaries are universal — good. But a summary tells you what an endpoint is *called*, not what a field *means*.

> For 93% of fields, an agent must infer semantics **from the field's name**. `part_cost` — cents or euros? Per unit or per lot? `catalog_meta` — what goes in it? It guesses. **A guess in a BOM is a wrong quantity on a real quote.**

**`UsageSubclause` proves you can do this superbly** — it spells out the left-to-right boolean fold, and it is the best-documented field in the spec. Extend that standard, starting with the fields an integration actually *writes*. You do not need 100%; **you need the write path.**

## 3.4 — Extend idempotency to singular writes · `P0-1`

`X-Idempotency-Key` exists on the 8 batch endpoints (24 h TTL). **No singular write has it.**

> A client times out on `POST /products` and retries → **duplicate product.** And with no `sku` (§4.1) and no uniqueness on name, **it cannot even detect the duplicate afterwards.**

**Do this:** accept `X-Idempotency-Key` on every singular `POST`. Standardise `/inbound/events` (which takes `idempotency_key` in the *body*) onto the header.

## 3.5 — Mark the legacy surface `deprecated` · `P1-9`

```
operations with deprecated: true    → 0 / 463
schema fields with deprecated: true → 1 / 1,369
```

Yet legacy shapes demonstrably exist and are accepted: the legacy `rule_json` array (saves, never executes), `technical_documentation` as an alias, the legacy plural doc_types.

> A caller cannot distinguish *"the supported way"* from *"the way that still parses but is on its way out."* **We only learned which was which by reading backend source.**

**Do this:** `deprecated: true` on every legacy path, field and enum value, naming the replacement in the description. Free, and the clearest possible signal to an integrator.

## 3.6 — Declare the rate-limit headers · `P3-3`

All 463 operations declare `429`. **None** declares `Retry-After`, `X-RateLimit-Limit`, `-Remaining` or `-Reset`.

> **Agents are bursty by nature** — they fan out reads. They will hit this, and they will back off by guessing.

**Do this:** declare the headers in the `429` response object. If the backend already sends them, this is a two-line spec change.

---

# Wave 4 — Capability. Things a customer cannot do today.

## 4.1 — `Product.sku` · `P2-1` · **the most commercially significant gap**

`ProductCreateRequest` accepts: `base_price · catalog_meta · currency · description · integration_metadata · is_active · language · name`. **No `sku`. No article number. No external identifier of any kind.**

**And here is the part that makes it strange:**

```python
>>> spec["components"]["schemas"]["QuoteLineItemResponse"]["properties"]["product_sku"]
{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null, "title": "Product Sku"}
```

**`QuoteLineItemResponse.product_sku` exists** — and ships in **your own example** as `"WIN-PREM-001"`. The API surfaces a product SKU **on the customer-facing quote line**, the exact place an article number matters most. **And there is no public write path to ever populate it.** It renders `null` on every quote.

> Every customer arrives with a pricelist keyed by article number. It is **the most universal column in the entire domain** — the join key to their ERP. There is nowhere canonical to put it.
>
> We were forced to invent a convention: `integration_metadata.<key>` — which is **unindexed** (no lookup by article number), **unvalidated** (no uniqueness), and **ours**, so two integrators pick two different keys and neither can read the other's data. Every ERP sync degrades to fetching the whole catalogue and matching client-side.

**The pattern already exists in your own model:** `Part` has `part_number`. `Option`/`Group` have `key`. `Quote` has `quote_number`. **`Customer` has `customer_id`** — and the configurator can even be told to search on it. **Every first-class entity has an external identifier except `Product` and `Area`.**

**Do this:**

```yaml
ProductCreateRequest:
  properties:
    sku:
      type: string
      maxLength: 255
      nullable: true
      description: >
        Your article number. Unique per tenant. Filter with GET /products?sku=,
        and use as a `match` key for batch upsert.
```

Add the `?sku=` exact-match filter, support it as a batch `match` key, and **wire it to `QuoteLineItemResponse.product_sku`**, which is already waiting for it.

## 4.2 — `POST /configurations` · `P2-1c` · **the load-bearing gap**

Every write path in the configuration surface is missing. These are all ten operations:

```
GET  /configurations                       GET  /configurations/{id}
GET  /configurations/states/{hash}         GET  /configurations/states/by-code/{code}
GET  /configurations/states/by-code/{code}/parts
GET  /configurations/states/by-code/{code}/selections
GET  /customers/{customerId}/configurations
GET  /products/{productId}/configurations
POST /configurations/calculate             ← stateless; returns a state, not an id
POST /configurations/{id}/finalize         ← locks one that already exists
```

**There is no endpoint that creates a saved configuration.**

> The API can **price** a configuration, **find** one a human already made, and **lock** one. **It cannot create one.**
>
> So a headless quote-to-cash flow is **impossible**. An ERP raising a quote, a partner portal, an AI agent — none can produce the thing a quote line item's `configuration_code` points at. Saved configurations apparently originate only in the configurator UI.
>
> **For a CPQ platform whose value proposition is programmable quoting, this is the load-bearing gap.**

**Do this:**

```yaml
/api/v1/configurations:
  post:
    summary: Create a configuration
    description: >
      Persist a selection set against a product. Returns the configuration id and
      config_code needed by quote line items. Use /calculate first to price it.
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required: [product_id, selected_options]
            properties:
              product_id:       { type: integer }
              selected_options: { type: object, additionalProperties: { type: array, items: { type: integer } } }
              option_amounts:   { type: object, additionalProperties: { type: number } }
              customer_id:      { type: integer, nullable: true }
```

> **If a create path already exists and we simply cannot see it, that is itself the finding** — it is in neither the spec nor the reference. **Tell us, and we will correct the audit.**

## 4.3 — Fractional numbered options · `P2-3`

```json
"number_min":  {"type": "integer", "minimum": 0, "maximum": 1000000}
"number_step": {"type": "integer", "minimum": 1, …}
```

And it is not just an authoring limit — `ConfigurationCalculateRequest.option_amounts` is `{"additionalProperties": {"type": "integer"}}`, so the amount is an integer through the **entire pipeline**.

> A numbered option cannot express **2.5 m of profile**, **0.5 kg of coating**, or **1.75 m² of glass**. Every continuous quantity — length, area, weight, volume — is unrepresentable. **That is cut-to-length, sheet goods, cabling, textiles.**
>
> The only workaround is unit inflation (model in mm, divide in the BOM factor). It is not free: **the customer sees `3000` where they think in `3 m`**, `number_unit` becomes a lie relative to their mental model, and every client carries an out-of-band conversion factor the API does not store. **Off-by-1000 errors here are silent and quote-destroying.**

**And the floor is inconsistent with the ceiling:** `option_scalings` is already `type: number`. **The BOM side already supports fractions. Only the option side is integer-locked.**

**Do this:** widen `number_min/max/step` and `option_amounts` to decimal. Validate `(amount − min) % step == 0` in decimal, not float.

## 4.4 — Quantity-aware constraints · `P2-2`

The constraint DSL is **presence-based only**. No clause can read an option's numeric amount — **even though `ConfigurationCalculateRequest.option_amounts` proves the runtime has those amounts at evaluation time.**

**The asymmetry is stark:** `CombinationRuleCreateRequest` supports `rule_type: set_quantity` with `quantity_factor`, `quantity_offset`, `quantity_rounding`. **A rule can *set* a quantity as its effect — but cannot *test* one as its condition.**

> These are **not expressible, at all**:
> - *"Forbid the standard frame when panel count > 20."*
> - *"Require the reinforced base above 15 m of run length."*
> - *"This motor is valid only for 4–8 units."*
>
> **The configurator will happily let a customer order 40 panels on a frame rated for 20**, and that invalid configuration flows into a quote and onto the shop floor. In machinery, most real rules are quantity-dependent. **This is the single largest class of missing configurator logic.**

**Do this — a DSL gap, not an architectural one:**

```yaml
RuleClause:
  oneOf:
    - # …existing anyOf / allOf / groupSelections clauses
    - type: object
      required: [option_amount]
      properties:
        option_amount:
          type: object
          required: [option_id, op, value]
          properties:
            option_id: { type: integer }
            op:        { type: string, enum: [lt, lte, gt, gte, eq, neq] }
            value:     { type: number }
```

Evaluate it against the `option_amounts` map the calculator already receives.

## 4.5 — Catalogue webhooks · `P2-7`

The infrastructure is solid (`/webhooks`, `/deliveries`, `/rotate-secret`, `/test`). But the only event types referenced anywhere are **`quote.created`, `quote.status_changed`, `quote.updated`**. Nothing for product, part, option, group, area, bom, constraint, price-list, or document. And `WebhookCreateRequest.events` has **no enum**, so the subscribable set is not discoverable at all.

> Any system mirroring the catalogue — ERP, PIM, storefront, search index — **must poll.** There is no way to react to *"a part cost changed"* or *"an option was added"* — precisely the events that invalidate a cached price or BOM.

**Do this:** emit `<resource>.{created,updated,deleted}` for product, part, option, group, area, bom_item, constraint, price_list. **Publish the enum.**

## 4.6 — Part images · `P2-5`

`part_img` appears **zero times in the entire spec.** Image upload exists for products (+ a full `/gallery`), areas, and options (even per-area). **Parts get nothing** — the field is populated only by the internal connector pipeline, so for parts created via the public API it stays `NULL` forever.

> Spare-parts catalogues, assembly instructions and exploded-view BOM UIs — **core CPQ deliverables** — cannot show part images through the public API.

**Do this:** `POST/DELETE /parts/{partId}/image`, mirroring the options route. Expose `part_img` on `PartResponse`.

---

# Wave 5 — Consistency. Cheap, and it makes the API learnable.

## 5.1 — Normalise path parameters · `P3-1`

Across 419 path params: **39 distinct names in 3 casing conventions** — 25 camelCase, 9 snake_case (`area_id`, `block_id`, `contact_id`…), 5 bare. `{id}` alone appears 106 times. **13 resources name their own identifier more than one way**, and the *same resource* switches convention between its base path and its sub-resources:

```
/parts/{id}                     /products/{id}
/parts/{id}/bom                 /products/{productId}/areas
/parts/{partId}/revisions       /products/{productId}/areas/{areaId}
```

`areas` and `contacts` use **three** conventions each.

> Loud `404`, so it is recoverable — but **it defeats few-shot generalisation entirely.** An agent that has seen `/parts/{id}` cannot construct `/parts/{partId}/revisions`; it must look up all 258 paths individually. **This is the finding that most directly costs an agent its ability to guess.**

**Do this:** `{id}` for the resource that owns the path; `{parentId}` only to disambiguate a nested parent. One casing. **This changes the *spec*, not the *URLs*** — path-param names are local identifiers. **Nearly free.**

## 5.2 — The `{"data": …}` envelope · `P1-5`

**363 of 389** JSON 2xx responses use `{"data": …}`. The **22** that do not are all batch/inbound, in **three mutually incompatible shapes**:

```
{total, succeeded, failed, results}   ← the 9 standard batch endpoints
{created, updated, errors}            ← POST /inbound/customers/batch
{count, product_id}                   ← POST /inbound/parts/batch
{job_id, status, task_id}             ← POST /inbound/triggers/{suffix}
```

> An agent doing `response["data"]` gets a `KeyError` (loud, fine). But the far more common **defensive** `response.get("data", [])` yields `[]` — so it concludes **a 100-item batch wrote nothing**, and may retry the entire thing.

**Do this:** wrap batch results in `data`; collapse the three inbound shapes into the standard one.

## 5.3 — Type the batch `match` · `P1-6`

`BatchOperationRequest.action` includes `upsert` with a `match` field — **genuinely good, and better than we assumed.** But `match` is `{additionalProperties: true}`, and so is `body`.

> Which fields are legal match keys, per resource, is **entirely undocumented.** An integrator cannot tell from the spec whether they may match a product on `name` — and certainly not on `sku`, which does not exist. **The most valuable endpoint in the API is unusable without trial and error.**

**Do this:** enumerate legal `match` keys per resource; `$ref` the real `*CreateRequest` into `body` via a discriminator.

## 5.4 — `expand` · `P1-7`

`expand` exists on **1 of 258 paths**, and its description says *"areas, gallery."* **That is not what the API does.** We probed a live tenant read-only and your own error message told us the truth:

> *"Unknown expansion 'groups'. **Valid expansions: areas, gallery, models, price_overrides, pricing_presets, videos.**"*

**The spec documents 2 of 6.** It mentions neither the dot-notation (`expand=areas.groups` **works**), nor its depth-2 limit, nor comma-combining.

**Credit where it is due:** those `400` bodies are *excellent* — they name the offending value **and enumerate every valid one.** That is exactly right, and **it is the only reason we could establish ground truth without backend access.** *Please put that enumeration in the spec, where a client can read it **before** making the request instead of after.*

> **We were wrong too, and we fixed it.** Our own skill told agents to call `expand=areas.groups.options`. **It has never worked** — it is a `400`. That bug is now corrected, and it is the cleanest possible illustration of this report's thesis: **an undocumented feature and a hallucinated feature are indistinguishable from the outside.** We guessed, the spec did not contradict us, and the guess shipped.

**Do this:**
1. Document the four missing expansions, the dot-notation, and the depth-2 limit — then make `expand` an `enum`.
2. **Add `options` as expandable** (raise max depth to 3). Today `options` is **not expandable at any depth**, so assembling a product's configuration graph is **irreducibly N+1** — one call, then one per group. **This single change collapses the most common read in the entire product from N+1 to 1.**
3. **Make `area_id` optional on `GET /options/{optionId}/area-config`** — it is currently *required*, and there is no list-all, so auditing price overrides across a 500-option catalogue costs **~3,000 sequential requests.** One line deletes the whole loop.

## 5.5 — Small items, each one line · `P3-4`

- **`DELETE /documents/content-blocks/images` is the only operation with a body on a `DELETE`.** Bodies on DELETE are **widely stripped by proxies and HTTP clients** → **silent no-op deletion**. Move the URL to a query param.
- **3 image uploads declare no `requestBody` at all** — the multipart body exists only in prose (*"Send as multipart/form-data with field name 'image'"*). A spec-driven client sends an empty POST.
- **`Location` is missing on 15 of 78** POSTs that can return `201`. And POST success codes vary — `201`×76, `200`×38, `202`×7 — so an agent gating on `201` mishandles the 38 creates that return `200`.
- **`is_stale` is on `ContentBlockLocaleResponse` but not `StructureBlockLocaleResponse`** (`P0-9j`) — though `source_content_hash` is on both. **You can ask whether a translated chapter *body* is stale; you cannot ask about its *title*.** A writer edits a German heading, every translation is now wrong, and **nothing in the API will tell you.**
- **5 orphan schemas** are defined but referenced by no operation (`ApiKeyCreateRequest`, `CompanyContactCreateRequest`, …). Their endpoints exist but use **inline** schemas — which is also why they escaped the `additionalProperties: false` policy.
- **5 Response schemas declare no `required` fields whatsoever** — an agent cannot rely on *any* field being present.

---

# What is already excellent — please do not "fix" these

We probed for these specifically, and we want to be clear that this report is not a general complaint. **The domain model is genuinely good**, and several things here are better than most of the market.

- **Error contract: 100% consistent.** All **1,601** declared 4xx/5xx responses use `ProblemDetails` (RFC 9457), with `type/title/status/detail/instance/request_id` and a **per-field `errors[].code`** on 422. **Zero exceptions.** Most APIs make you regex prose. Yours does not.
- **The runtime error *messages* are outstanding** — and they saved this audit. They name the bad value **and enumerate every good one**. The only tragedy is that the enumeration lives in a `400` instead of the spec.
- **Batch is excellent.** 10 endpoints, `207 Multi-Status` with per-item results, savepoint isolation, 100 ops/request, a universal `POST /batch`, **and `action: upsert` with `match`**. NDJSON export. **Better than we assumed, and better than most CPQ APIs.**
- **`usage_subclauses` is beautifully specified** — `$ref: UsageSubclause`, with the left-to-right boolean fold spelled out. It is **the hardest concept in the domain and the best-documented field in the spec.** *It is the proof that the rest could look like this.*
- **Translation staleness is properly designed.** `source_content_hash` + `is_stale` is exactly the right primitive for keeping a multilingual manual honest, and **most systems do not have it.**
- **Nullable/required: zero contradictions** across 1,369 properties. **`DELETE`: 69 operations, all `204`.** **No `GET` performs a mutation.** All checked.

**Three findings we killed as false** — we would rather lose a finding than send you chasing one:

| Suspected | Reality |
|---|---|
| "No bulk/batch endpoints" | **False.** 10 + a universal `/batch`. Well designed. |
| "No upsert" | **False.** `action: upsert` with `match`. |
| "No bulk BOM import" | **False.** `POST /bom/batch` covers it. **Our own skill said otherwise — that was our bug, not yours**, and it is fixed. |

---

# The SOTA argument — what this buys you

Everything above is remediation. **This section is the opportunity**, and it is why we think this work is worth a sprint rather than a backlog ticket.

**The customer calling your API is changing.** It used to be an integrator with your backend source open in another tab, who reads a prose caveat and remembers it. Increasingly it is an autonomous agent that reads your machine-readable spec and **does exactly what it says** — at machine speed, in production, with no human checking its work.

For that customer, **the spec is not documentation. It is the product.**

Close Waves 1–3 and Rattle becomes something that, as far as we can tell, no CPQ platform currently is:

| | Today | After |
|---|---|---|
| **Concurrency** | A `200 OK` can silently destroy another user's constraints | OCC declared, `409` on stale, safe by construction |
| **Read-modify-write** | `422`s on the API's own payload | Works for every generated client, automatically |
| **Constraints** | The DSL is `{"title": "Rule Json"}` | Typed, validated, and a legacy shape that *fails loudly* instead of never firing |
| **Pricing** | Six mechanisms, undocumented precedence, plausible-but-possibly-wrong numbers | **An auditable `price_breakdown`: which mechanism supplied each number.** Nobody else has this. |
| **Quote-to-cash** | Impossible headlessly — you cannot create a configuration | Fully programmable end to end |
| **Agents** | Must reverse-engineer your behaviour, and *will hallucinate the gaps* | Can drive the API **safely, without a human checking their work** |

That last row is the whole thesis. **We built 18 skills and 10 agents against this API.** Several of them are working *around* these gaps rather than through them — teaching an agent to reverse-engineer your pricing precedence, or to verify by experiment whether your glossary constrains your own translator, **because nobody knows.**

Those workarounds are careful, and they are honest about what they cannot prove. **But they should not have to exist.** Every one of them is a paragraph you could write instead.

**And here is the part that should worry you most:** where the spec is silent, an agent does not stop. **It guesses** — and a plausible guess is indistinguishable from documented fact until it reaches a customer. We know, because **we shipped exactly that bug twice** from your spec: the legacy `rule_json` shape that saves and never fires, and an `expand` depth that never worked. Both looked right. Neither was contradicted. Both shipped.

**Every gap in your spec is a hallucination waiting to happen in someone's production tenant.**

---

# Ticket-ready summary

Copy this into your tracker.

| # | Wave | Ticket | Finding | Type | Est. |
|---|---|---|---|---|---|
| 1 | 1 | Declare `X-Constraints-Version`, `X-Price-Lists-Version`, `X-Idempotency-Key`, `If-None-Match` + `409` | P0-1, P0-1b | **spec only** | 2 h |
| 2 | 1 | Return `version` on `PriceListResponse` (the OCC header is currently unobtainable) | P0-9b | schema | 1 h |
| 3 | 1 | `readOnly: true` on the ~200 server-computed fields | P0-2 | **spec only** | 3 h |
| 4 | 1 | Fix `servers` / `/api/v1` double prefix | P0-6 | **spec only** | 5 min |
| 5 | 1 | Dictionary `PATCH` must merge (or be removed) | P0-9i | **backend** | 1 h |
| 6 | 1 | `limit`: default 200 > maximum 100 > prose 500 — pick one | P0-9e | **spec only** | 5 min |
| 7 | 1 | Regenerate `ConfiguratorSettingsResponse` (5 fake fields, 20 real, zero overlap) | P0-7 | schema | 2 h |
| 8 | 2 | Schema `rule_json`; `422` the legacy `{if,then}` array | P0-4 | schema + backend | 1 d |
| 9 | 2 | **Document the pricing resolution order** + add `price_breakdown` to `/calculate` | P0-8 | **spec** + feature | 1 d |
| 10 | 2 | Name + describe `advanced-prices` | P0-9 | **spec only** | 30 min |
| 11 | 2 | `additionalProperties: false` on the 8 loose + all inline request bodies | P0-10, P0-9c | schema | 3 h |
| 12 | 2 | Stop `200`-ing writes you discard (`currency`, first-clause `operator`) | P2-4 | backend | 2 h |
| 13 | 2 | Disambiguate `PUT` vs `PATCH` (37 of 39 identical) | P0-3 | backend | 1 d |
| 14 | 3 | 119 free strings → `enum`; one `DocType` **including `quote`** | P1-1, P2-6 | **spec only** | 1 d |
| 15 | 3 | Publish `QuoteStatus` / `OpportunityStage` + legal transitions | P2-1b | **spec only** | 4 h |
| 16 | 3 | Describe the write-path fields (93% undescribed) | P1-2 | **spec only** | 2 d |
| 17 | 3 | `X-Idempotency-Key` on singular POSTs | P0-1 | backend | 4 h |
| 18 | 3 | `deprecated: true` on the legacy surface | P1-9 | **spec only** | 2 h |
| 19 | 3 | Rate-limit headers on `429` | P3-3 | **spec only** | 15 min |
| 20 | 4 | **`Product.sku`** (+ `?sku=` filter, batch `match`, wire to `product_sku`) | P2-1 | feature | 2 d |
| 21 | 4 | **`POST /configurations`** — headless quote-to-cash | P2-1c | feature | 3 d |
| 22 | 4 | Fractional numbered options (`number_min/max/step`, `option_amounts`) | P2-3 | feature | 2 d |
| 23 | 4 | Quantity-aware constraint clause (`option_amount`) | P2-2 | feature | 3 d |
| 24 | 4 | Catalogue webhooks + event enum | P2-7 | feature | 2 d |
| 25 | 4 | `POST /parts/{id}/image` | P2-5 | feature | 4 h |
| 26 | 5 | Normalise the 39 path-param names | P3-1 | **spec only** | 4 h |
| 27 | 5 | `expand`: document all 6, add `options` (N+1 → 1), `area_id` optional on area-config | P1-7 | feature | 1 d |
| 28 | 5 | `{"data": …}` envelope on batch; type the batch `match` | P1-5, P1-6 | schema | 4 h |
| 29 | 5 | Small items: DELETE body, missing `Location`, orphan schemas, `is_stale` on titles | P3-4, P0-9j | mixed | 4 h |

**Wave 1 alone is ~9 hours and removes every silent-corruption path in the API.**

---

# Questions we need you to answer

We refused to guess at these. Each one is a place where we would rather ask than fabricate — because a plausible fabrication is worse than an admitted gap.

1. **What is the pricing resolution order?** (§2.2) Six mechanisms; the spec states nothing. Our skill currently teaches agents to reverse-engineer it per tenant.
2. **What are the full `QuoteStatus` and `OpportunityStage` vocabularies, and what transitions are legal?** (§3.2) We observed `draft`/`approved` and `qualification` read-only — but observed ≠ enum.
3. **Is there a create path for configurations that we cannot see?** (§4.2) If so it is in neither the spec nor the reference, and *that* is the finding.
4. **Does the DeepL translate pass consult the `/translations/dictionary` glossary?** Nobody knows. Our i18n skill refuses to claim a locked term is protected until an agent has *watched it survive* a translation.
5. **Does `POST /documents/templates/{id}/translate` touch `safety_notice` / `hp_statement` blocks?** If it machine-translates a CLP hazard statement, **that is a legal defect in a CE-marked document, not a typo.** We did not assert either way.
6. **What is `require_customer_info`?** (§1.7) It has no `show_*` sibling, unlike the other seven pairs. Master switch, independent requirement, or legacy?
7. **`GET /configurations/states/by-code/{code}/selections`** describes itself as returning per-option **price** — but its declared schema is the same scalar as `/calculate`. **If the prose is right, that endpoint is the answer to §2.2** and the precedence problem collapses to one read. Which is it?

---

# Closing

We built Grimoire — 18 AI skills, 10 agents — because **the Rattle domain model is genuinely good.** `usage_subclauses`, ghost parts, `alt_group`, area-scoped overrides, savepoint-isolated batch upserts, a 100%-consistent RFC 9457 error contract. These are sophisticated, well-conceived primitives, and the fact that an AI can be taught to use them correctly is a **compliment to the design**.

**The gap is not in the model. It is that the spec describes a fraction of what the API knows** — and the parts it omits are exactly the parts that bite: the concurrency header, the constraint grammar, the idempotency key, the read-only fields, the pricing precedence, the SKU that already exists on the quote line with nothing to write to it.

An integrator with backend access can find these. **An autonomous agent cannot.**

Close P0 and P1 and this becomes an API an AI can drive **safely, without a human checking its work.** In CPQ that is a real competitive position — and it is **much closer than this list makes it look.** Wave 1 is a day.

---

**Verify your progress at any time:**

```bash
python3 scripts/rattle_api_conformance.py
```

Happy to pair on any of it, and happy to re-run the whole audit against a new spec whenever you would like.
