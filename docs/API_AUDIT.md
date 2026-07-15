# Rattle REST API — audit findings

**For:** the Rattle backend team
**Spec audited:** `https://www.rattleapp.de/docs/api/openapi.json`, fetched **2026-07-14** — OpenAPI 3.1, **463 operations · 258 paths · 37 tags · 210 schemas · 1,369 schema fields**
**Auditor:** [Grimoire](https://github.com/rattleai/grimoire) — 18 AI Skills that drive this API to build product configurations, variant BOMs, and CE-compliant technical documentation.

> ### Start here, not with this document
>
> This is the **diagnosis** — 42 findings, with evidence. It is worth reading once.
>
> But a 40-page audit does not get fixed, and **a failing test does**:
>
> ```bash
> git clone https://github.com/rattleai/grimoire.git && cd grimoire
> python3 scripts/rattle_api_conformance.py     # fetches your live spec. No credentials needed.
> ```
>
> It is **red on 27 checks** today. Fix one, it goes green. Drop it in your CI and gate on the
> exit code (which is the failure count) so a fixed defect cannot silently regress.
>
> - **[`API_REMEDIATION.md`](API_REMEDIATION.md)** — the prescription: what to change, in what
>   order, with copy-pasteable OpenAPI. **Wave 1 is one day and removes every silent-corruption
>   path in the API.**
> - **This document** — the reasoning behind each one.

---

## Why this report is different

Most API feedback comes from a human who read the docs. This comes from **building an AI agent that must call the API correctly with no human checking its work** — a much harsher test. A human reads a prose caveat and remembers it. An agent reads the machine-readable spec and does exactly what it says.

That drives the ranking. **A loud error is cheap; a silent wrong result is expensive.** An endpoint that returns `422` teaches the caller something. An endpoint that accepts a payload, returns `200`, and quietly does nothing teaches the caller a lie — and in CPQ a lie propagates into a customer's BOM, their pricing, and the offer PDF they send to *their* customer.

Every number here was produced by a script run against the published spec (reproduction at the end). Where a claim could not be settled from the spec alone, we **probed a live tenant with read-only `GET`s** and say so explicitly — P1-7 is the result, and it changed our conclusion **and caught a bug in our own code.**

Where we say "an agent will get this wrong," it is because **we got it wrong**, and the workaround is now permanently in our codebase.

---

## What is already correct — please don't "fix" these

We probed for these specifically. They are genuinely well-disciplined and we want the team to know it.

- **Error contract: 100% consistent.** All **1,601** declared 4xx/5xx responses use `ProblemDetails` (RFC 9457), with `type/title/status/detail/instance/request_id` and a per-field `errors[].code` on 422. **Zero exceptions.** Most APIs make you regex prose. This one doesn't.
- **The runtime error *messages* are outstanding** — and they saved this audit. `GET /products/32?expand=groups` returns:
  > *"Unknown expansion 'groups'. Valid expansions: areas, gallery, models, price_overrides, pricing_presets, videos."*

  It names the bad value **and enumerates every good one.** That is exactly right, and it is the only reason we could establish ground truth without backend access (see P1-7). **The tragedy is that this enumeration exists only at runtime, in a `400`, when it belongs in the spec** — where a client could read it *before* making the request.
- **Nullable/required: zero contradictions.** Across 1,369 properties, **0** fields are both `required` and nullable; **0** are both `required` and `default: null`. We validated the detector against known positives — the zero is real.
- **`DELETE`: 69 operations, all return `204`.** Perfectly uniform.
- **No `GET` performs a mutation.** Checked all of them.
- **Batch is excellent.** 10 endpoints, `207 Multi-Status` with per-item results, savepoint isolation, 100 ops/request, a universal `POST /batch`, **and `action: upsert` with a `match` field**. NDJSON export for products/parts/customers. Better than most CPQ APIs, and better than we assumed.
- **`usage_subclauses` is beautifully specified** — `$ref: UsageSubclause`, with the left-to-right boolean fold semantics spelled out. It is the hardest concept in the domain and the **best-documented field in the spec**. It is the proof that the rest could look like this.
- **`401`/`429` declared on 100% of operations.** Action endpoints are uniformly `POST` + verb-noun across 23 verbs.
- **Translation staleness is properly designed.** `POST /content-blocks/{id}/locales/{locale_id}/translate` sets a `source_content_hash`, and the target locale's **`is_stale`** flag flips to `true` if the source changes afterwards. That is exactly the right primitive for keeping a multilingual manual honest, and most systems do not have it. **Keep it — and please expose it more prominently**, because the glossary that should constrain the same translator is invisible (P0-9g).

**Three findings we killed as false** — we'd rather lose a finding than send you chasing one:

| Suspected | Reality |
|---|---|
| "No bulk/batch endpoints" | **False.** 10 + a universal `/batch`. Well designed. |
| "No upsert; clients need get-or-create loops" | **False.** `action: upsert` with `match`. *(One residual issue — P1-6.)* |
| "No bulk BOM import" | **False.** `POST /bom/batch` covers it. Our own skill says otherwise — **that's our bug, not yours**, and we're fixing it. |

---

# P0 — Silent corruption

A caller does everything the spec says and still writes wrong data, with a `200 OK`. Fix these first.

## P0-1. The spec declares **zero header parameters** — while the API requires four

```python
>>> {p["in"] for op in all_operations for p in op.get("parameters", [])}
{'query'}                       # path params are declared at path level; header: ZERO
>>> len(spec["components"]["parameters"])
0
```

**Not one `header` parameter across 463 operations.** Yet the API's own prose describes a header contract in four places:

| Header | Where it's documented | What it does |
|---|---|---|
| `X-Constraints-Version` | `POST /constraints` description + `info.description` | **Optimistic locking on an atomic replace-all** |
| `X-Price-Lists-Version` | `info.description` | Optimistic locking |
| `X-Idempotency-Key` | 8 batch endpoint descriptions ("24 h TTL") | **Safe retries** |
| `If-None-Match` | `GET /configurations/states/by-code/{code}` | ETag conditional caching |

`POST /api/v1/constraints` says it outright:

> "Atomically replaces all option-level forbidden combinations for a product. **Include the `X-Constraints-Version` header for optimistic concurrency control.**"

…and then declares `parameters` **not at all** (the key is absent, not empty), and no `409` response — while **23 other endpoints do declare `409`.**

**Consequence.** Every spec-driven consumer — codegen, SDKs, MCP tool generation, an AI agent — is **structurally incapable** of sending these headers. So:

- **Lost update.** Two users edit constraints concurrently. `POST /constraints` *replaces all pairs*. The second write **silently destroys the first, with a `200 OK`.** No error. No warning. The configurator starts selling combinations that cannot be built.
- **Duplicate writes.** A batch that times out and retries double-applies, because the idempotency mechanism **you built** is invisible.
- The client cannot even know it is causing either.

**Fix.** Declare all four as real `parameter` objects, plus the `409` on the OCC endpoints. **This is pure spec work against behaviour the backend already implements** — and nothing else on this list can cause a silent lost update.

## P0-2. You cannot `PUT` back the object the API just gave you

```python
GET  /api/v1/products/{id}   → ProductResponse:      22 fields
PUT  /api/v1/products/{id}   → ProductUpdateRequest:  9 fields, additionalProperties: false

# 13 fields the server SENDS and then REFUSES to accept back:
id · created_at · updated_at · links · image_url · background_url · gallery_count ·
public_token · areas_version · constraints_version · options_version · parts_version · pricing_version
```

**`readOnly: true` appears ZERO times in the entire spec.** `writeOnly`: zero.

**Consequence.** The single most common REST idiom — *fetch, change one field, send it back* — **returns `422`**, because `additionalProperties: false` rejects the server-computed fields the server itself just sent. Every client must hand-maintain a per-resource allowlist of which fields are safe to echo. Across 45 resources that is **200 response-only fields** to strip by hand.

An agent cannot infer this. It fetches a product, sets `name`, PUTs it, and gets a 422 listing fields it never touched.

**Fix.** Mark those 200 fields `readOnly: true`. **Zero API behaviour change**, and every generated client and every agent immediately does the right thing — codegen omits `readOnly` fields from request bodies automatically. This is the highest ratio of value to effort in the entire report.

## P0-3. `PUT` and `PATCH` are byte-identical aliases on 37 of 39 paths

- **39 paths expose both `PUT` and `PATCH`. On 37, the request schema is identical.**
- **43 of 47 `PUT` bodies have no `required` array at all** — every field optional.
- **21 `PUT`-only paths; 0 `PATCH`-only.**

**Consequence.** RFC 9110 says `PUT` **replaces**. An all-optional `PUT` body says it **merges**. The spec does not disambiguate — so an agent applying standard REST semantics (GET → modify one field → PUT) will either work fine, or **silently null out every field it omitted**. It cannot tell which from the spec, and neither can we.

That is a data-destruction path with a `200 OK` on it. And an agent that learned "PATCH for partial updates" hits `405` on 21 paths.

**Fix.** Pick one verb per path. If `PUT` really merges, say so explicitly in the description — but the honest fix is to make `PUT` replace (with `required` fields) and `PATCH` merge.

## P0-4. `rule_json` — the constraint DSL — is untyped, and your examples teach a shape that silently never executes

`ForbiddenRuleCreateRequest.rule_json`, in its entirety:

```json
{ "title": "Rule Json" }
```

No `type`. No `description`. No `example`. No schema. (`CombinationRuleCreateRequest.condition` is `{"anyOf": [{}, {"type":"null"}]}` — an **empty schema**.)

This field decides **which option combinations a customer is allowed to buy.**

**Consequence — this happened to us.** The correct shape is a single object:

```json
{"requires": [<clause>, …], "invalid": [<option_id>, …]}
```

A **legacy array shape** — `[{"if": {...}, "then": {"forbid_options": [...]}}]` — is *accepted on write and silently dropped by the runtime evaluator*. The rule saves. Returns `200`. **Never fires.** The customer buys the forbidden combination, and nobody finds out until a machine ships with parts that don't fit.

We shipped that bug into our skills, our examples and our prompt templates. **We got it from an example in your spec.** It took a line-by-line audit against backend source to catch. **Every integrator who trusts the spec has it wrong right now.**

**Fix.**
1. Schema it: `ForbiddenRuleJson { requires: RuleClause[], invalid: integer[] }`, with `RuleClause` as the `anyOf`/`allOf`/`groupSelections` union. **You already did exactly this for `UsageSubclause` — copy it.**
2. Type `CombinationRuleCreateRequest.condition`.
3. **`422` the legacy array.** A loud failure is worth a hundred silent ones. If back-compat demands it stays, mark it `deprecated: true` and state **that it does not execute**.
4. Purge the legacy `{if, then}` examples from the spec.

## P0-5. Money is encoded seven different ways, and `part_cost` is an integer

**76 price/amount/cost/discount/tax fields, in 7 different type-sets:**

| Type | Count | Examples |
|---|---|---|
| `string` | 26 | `OptionResponse.price`, `ProductResponse.base_price` |
| `number` (float) | 16 | `QuoteAnalyticsSnapshotResponse.total_amount` |
| **`integer`** | **3** | **`Part{Create,Update}Request.part_cost`, `PartResponse.part_cost`** |
| `number \| string` | 11 | `LineItemCreateRequest.unit_price`, `PriceOverrideCreateRequest.override_price` |
| `integer \| number \| string` | 2 | `Product{Create,Update}Request.base_price` |

Three distinct defects:

**`part_cost` is the only integer money field, with no documented unit.** €12.50 cannot be represented. And `part_cost` **rolls up through BOM explosion into product cost** — ghost parts are forced to `part_cost=0` with cost rolling up from children — so **one rounded child silently poisons every ancestor in the tree.** Across a 5,000-line BOM that is a real number on a real quote.

**Type flips across the read/write boundary.** `override_price` is `number|string` on the request and `string` on the response. `ProductCreateRequest.base_price` accepts `string|integer|number`; the response returns `string`. You cannot round-trip without a coercion the spec doesn't describe.

**`float` in the analytics schemas** exposes quote totals to binary-float drift.

**Consequence.** An agent summing a BOM will concatenate strings, or `int`-truncate a `part_cost`, and return a **plausible-but-wrong number with a `200 OK`.** Nothing errors. This lands directly on the money path.

**Fix.** One money type across the surface — decimal-as-string (`"12.50"`), matching the existing majority. Migrate `part_cost` (or rename it `part_cost_cents` and *say* the unit). Kill the multi-type unions: accept one type, return the same type.

## P0-6. `servers: [{"url": "/"}]` while every path embeds `/api/v1`

**Consequence.** The natural base URL is `https://www.rattleapp.de/api/v1` — it's what the docs hand you. Concatenating it with a spec path gives `/api/v1/api/v1/products` → `404`. **Every generated client and every agent hits this.** We had to write a `normalizePath()` shim and defend it with a test.

**Fix.** Either `servers: [{"url": "https://www.rattleapp.de/api/v1"}]` and drop the prefix from path keys, **or** keep the paths and set the server to `https://www.rattleapp.de`. Both are correct; the current combination isn't. **One line.**

## P0-7. `ConfiguratorSettingsResponse` describes a schema that does not exist — zero overlap with reality

This one is in a class of its own. We found it while writing a day-0 onboarding guide, and had to verify it twice because it looked like a bug in our tooling.

```python
# What the spec says GET /company/configurator-settings returns:
>>> sorted(spec["components"]["schemas"]["ConfiguratorSettingsResponse"]["properties"])
['custom_css', 'default_currency', 'require_login', 'show_prices', 'show_stock']     # 5 fields

# What the live API actually returns:
['allow_create_new_customer', 'allow_select_existing_customer', 'company_id',
 'customer_search_fields', 'require_company_contact_person', 'require_customer_address',
 'require_customer_contact_person', 'require_customer_email', 'require_customer_id',
 'require_customer_info', 'require_customer_organization', 'require_customer_phone',
 'show_company_contact_person', 'show_customer_address', 'show_customer_contact_person',
 'show_customer_email', 'show_customer_id', 'show_customer_organization',
 'show_customer_phone', 'start_search_digits']                                       # 20 fields

# Overlap: NONE. Not one field in common.
```

And the write side accepts anything at all:

```json
PATCH /company/configurator-settings  requestBody:
{ "type": "object", "additionalProperties": true }
```

**Consequence.** These 20 flags govern the **entire customer-capture UX of the configurator** — whether a customer must supply an organisation, which fields are searched, how many digits trigger search. They are the settings a new tenant *must* get right on day one.

An agent reading the spec will:
1. Try to set `show_prices` — which **does not exist**. `PATCH` returns `200`. Nothing happens.
2. **Never discover** `require_customer_organization`, `customer_search_fields`, or any of the 18 other flags that actually control the product.

So the spec is not merely incomplete here; **it is actively wrong**, and the endpoint silently accepts the wrong thing. There is no error anywhere in this loop.

**Fix.** Regenerate `ConfiguratorSettingsResponse` from the real model, give the `PATCH` body a real schema (`additionalProperties: false`), and `422` unknown flags. Until then, the 20 real flags are documented in `skills/rattle-onboarding/references/configurator-settings.md`, live-verified — **which is not where they belong.**

> We also found a `ConfiguratorSettingsResponse`-adjacent unknown: `require_customer_info` has no `show_customer_info` sibling, unlike the other seven `require_*`/`show_*` pairs. We could not determine whether it is a master switch, an independent requirement, or legacy. **Please clarify** — we left it alone rather than guess.

## P0-8. Six mechanisms can set one option's price. The spec never says which wins.

Pricing is the one thing a CPQ system cannot get subtly wrong. **Six separate mechanisms can set the price of a single option:**

| # | Mechanism | Keyed on | Endpoint |
|---|---|---|---|
| 1 | `Option.price` | the option | `POST /options` |
| 2 | **Option price-override** | **(option, area, price_list)** — all three `required` | `POST /options/{id}/price-overrides` |
| 3 | **Advanced price** | **(option, `condition_option_id`, area?, price_list?)** — a *conditional* price | `POST /options/{id}/advanced-prices` |
| 4 | **Area / Product price-override** | (area\|product, price_list) | `POST /{areas,products}/{id}/price-overrides` |

Plus **pricing presets** (product-level fees/surcharges) as a fifth layer — and a **sixth**, `PUT /options/{id}/area-config`, which carries a `price` and is scoped to an area with **no price list at all** (see P0-9d), so the six do not even share a single axis.

**Nowhere in the spec is the resolution order stated.** We grepped all 463 operations and 210 schemas:

```
"precedence"      → 1 hit — and it is about usage_subclauses BOOLEAN OPERATORS, not pricing
"resolution order" → 0
"takes priority"   → 0
"most specific"    → 0
"falls back"       → 0
"overrides the"    → 0
```

**Consequence.** A tenant configures an option price-override *and* an area price-override for the same option and price list. **Which one does the customer pay?** The API knows. The spec does not say. The client cannot know, and — this is the part that matters — **it will not error.** It will return a price. A plausible one. Possibly the wrong one, on a quote that goes to a customer.

This is the single highest-consequence undocumented behaviour in the API. Every other silent-wrongness finding in this report costs you a BOM line or a retry. **This one costs you money, on a document with your customer's signature on it.**

**We refused to guess.** Our pricing skill does **not** assert a precedence order. Instead it teaches agents to determine it empirically per tenant — using `POST /configurations/calculate` (*"Resolve constraints, compute pricing, and return a configuration state"*) as the oracle — and to record the observed order in tenant memory. That is a workaround for a documentation gap, and it should not be necessary.

**Fix.** Document the resolution order. One paragraph in `info.description` would do it. Ideally also expose it: a `price_breakdown` in the `/calculate` response showing which mechanism supplied the final number would make pricing auditable, which for a CPQ system is close to a compliance requirement.

## P0-9. `advanced-prices` — a conditional-price engine with no schema, no description, and no name

Five operations exist under `/options/{optionId}/advanced-prices`. Their request and response schemas are **inline** — `AdvancedPriceCreateRequest` does not exist in `components`. The endpoint summary is *"Create an advanced price"*. The description is **`null`**.

Here is the entire published definition of the mechanism:

```json
{ "properties": {
    "advanced_price":      {"type": "string"},
    "area_id":             {"type": "integer"},
    "condition_option_id": {"type": "integer"},
    "price_list_id":       {"type": "integer"} },
  "required": ["condition_option_id", "advanced_price"] }
```

`condition_option_id` is **required** — which tells us, by inference alone, that this is a **cross-option conditional price**: *this option costs X **when that other option is also selected**.*

That is a genuinely powerful CPQ feature — bundle pricing, cross-sell discounts, "the premium paint is cheaper if you also take the premium trim." It is the kind of thing a competitor puts on a datasheet.

**Consequence.** It is undiscoverable. No description, no named schema, no example, no mention in `info.description`. **We worked out what it does by reading a required field name.** An integrator will never find it, and an AI agent certainly won't. You have built a feature nobody can use.

**Fix.** Name the schemas (`AdvancedPriceCreateRequest` / `AdvancedPriceResponse`), write one sentence of description, add an example. This is 20 minutes of work on a feature that is presumably worth considerably more than that.

## P0-9b. `X-Price-Lists-Version` has no source. The OCC header cannot be obtained.

P0-1 said the four required headers are undeclared. The price-list one is worse than undeclared — **it is unobtainable.**

`info.description` says:

> "Bulk-replace endpoints for constraints and price lists use version headers (`X-Constraints-Version`, `X-Price-Lists-Version`) for optimistic locking. **Read the current version from a GET response**, send it back."

So we went to read it:

```python
>>> sorted(spec["components"]["schemas"]["PriceListResponse"]["properties"])
['created_at', 'currency', 'description', 'id', 'is_base', 'links', 'name', 'order_index', 'updated_at']
# fields containing "version": NONE
```

**`PriceListResponse` carries no version field of any kind.** There is nothing to read. The only candidate anywhere in the API is `ProductResponse.pricing_version`, and that it is the value for this header is **our inference, not a documented fact.**

**Consequence.** A client that *knows about* the header (which, per P0-1, it cannot) still **cannot construct it**. The optimistic-locking mechanism protecting bulk price-override replacement is therefore not merely undiscoverable — **it is unusable.** Concurrent `/price-overrides/replace` calls silently overwrite each other, and there is no defence available to the caller.

**Fix.** Return the version on `PriceListResponse` (and say which field feeds which header), then declare the header per P0-1.

## P0-9c. Within one resource family, a typo `422`s on one endpoint and is swallowed on the next

The three price-override families look like siblings. They are not:

| Endpoint | Request body | `additionalProperties: false`? |
|---|---|---|
| `POST /options/{id}/price-overrides` | **named** — `$ref: PriceOverrideCreateRequest` | **yes** → typo `422`s ✅ |
| `POST /products/{id}/price-overrides` | **named** — `ProductPriceOverrideCreateRequest` | **yes** → typo `422`s ✅ |
| `POST /areas/{id}/price-overrides` | **inline**, unnamed | **no** → **typo silently swallowed, `201`** ❌ |

The area body is also `override_price: string` only, while the option body accepts `number \| string`.

**Consequence.** An integrator writes the option override, gets a clean `422` on a typo, and reasonably concludes the API validates. They then write the *area* override — the same concept, the adjacent endpoint — and their typo'd field vanishes with a `201`. **The inconsistency is inside a single resource family, on the money path.**

The same pattern holds for `advanced-prices` and `PUT /options/{id}/area-config` (see P0-9d) — both inline, both permissive.

**Fix.** Name the inline schemas and set `additionalProperties: false`. This extends the list in P0-10 from 8 *named* schemas to include every *inline* body too.

## P0-9d. There is a sixth price-setting mechanism, and it needs no price list at all

`PUT /options/{optionId}/area-config?area_id=` — scope `prices:write` — carries a **`price`** field in an inline body.

So it sets an option's price **per area, with no price list involved**, entirely outside the price-list axis that every other override is keyed on.

**Consequence.** P0-8 asked which of five mechanisms wins. **It is six.** And this one is orthogonal to the price-list dimension the other five share, which makes the undocumented resolution order strictly harder to reason about — not just unordered, but not even a total order over a single axis.

**Fix.** Document it in the resolution order (P0-8), and say plainly how a price-list-scoped override interacts with a price-list-less one.

## P0-9e. `limit` declares `default: 200` and `maximum: 100`, and its prose says 500

```jsonc
// GET /configurations/states/by-code/{code}/parts
"limit": {
  "schema":      { "default": 200, "maximum": 100, "minimum": 1, "type": "integer" },
  "description": "Max parts per page (default 200, max 500)"
}
```

**The default exceeds the maximum.** Three different numbers appear in one parameter: the schema's `default` (200), the schema's `maximum` (100), and the description (500).

**Consequence.** The declared default is **schema-invalid against its own constraint**. A strict validator rejects it. A generated client sends `limit=200` — its own documented default — and gets a `422`. A caller who trusts the description sends `limit=500` and gets a `422`. **There is no value a caller can derive from this parameter that is guaranteed to work except by ignoring all three numbers and guessing.**

This one is a 30-second fix and it is the sort of thing that erodes trust in everything around it.

## P0-9f. The itemised price oracle is promised in prose and absent from the schema

`GET /configurations/states/by-code/{code}/selections` describes itself as:

> "Returns each selected option **enriched with group name, option name, price, quantity**, and wishlist status."

Its **declared `200` schema is `ConfigurationStateResponse`** — the same scalar state object as `/calculate`, with **no per-option array and no per-option price** anywhere in it.

**Consequence.** This endpoint, if it behaves as described, is **the answer to P0-8** — an itemised price breakdown would let a caller see *which mechanism supplied each number*, collapsing the entire precedence problem to a single read. As declared, it returns a scalar and answers nothing.

Either the schema is wrong (and a valuable feature is hidden — the P0-7 pattern again), or the description is wrong (and it promises something it does not deliver). **We could not determine which without writing to a live tenant, and did not.**

**Fix.** Whichever it is — make them agree. If the runtime really does return per-option prices, **say so in the schema, and P0-8 becomes much less urgent.**

## P0-9g. The glossary lock is invisible — and it is the only thing standing between DeepL and your brand terminology

`/translations/dictionary` (6 operations) is the **translation glossary**: the mechanism that stops a machine translator rendering a locked brand term however it likes. Its entire published definition:

```jsonc
// POST /translations/dictionary — summary: "Create or update a dictionary entry"
// description: null
// schema: INLINE, unnamed
{ "properties": { "base_term":    {"type": "string"},
                  "translations": {"type": "object", "additionalProperties": {"type": "string"}} },
  "required": ["base_term", "translations"] }
```

`GET /translations/dictionary` — *"Returns company-wide translation dictionary entries."* — takes **no query parameters at all**. Not filterable. Not paginated.

**Consequence.** The API ships a **DeepL-backed machine translator** (`POST /documents/templates/{id}/translate` — *"Translate all structure block titles and attached content block locales… via DeepL"*) and, separately, a glossary that constrains it. **The translator is documented. The glossary is not.** An integrator will find the first and never the second — and will therefore machine-translate a technical documentation with no terminological control at all.

In this domain that is not cosmetic. A locked term (a part name, a brand term, a regulated abbreviation) rendered three different ways across a manual is an `IEC/IEEE 82079-1` Clause 5 *consistency* defect.

**Fix.** Name the schema, describe what the dictionary is *for* (one sentence: "terms that must translate a specific way, or not at all"), state whether the DeepL pass actually consults it, and add filtering/pagination to the `GET`.

## P0-9h. Which entities can be translated at all is undiscoverable

`PUT /translations` upserts translations in bulk:

```jsonc
{"translations": [{"entity_id": integer, "entity_type": string, "field": string, "language": string, "value": …}]}
```

**`entity_type` is a free string. `field` is a free string. Neither has an enum.**

**Consequence.** A caller cannot determine **which entities are translatable**, nor **which of their fields**. `entity_type: "prodcut"` (typo) and `field: "nmae"` are both schema-valid. `GET /translations?entity_type=` filters on a vocabulary documented nowhere.

The `language` field appears on **20 schemas** — product, area, group, option, and more — so the translatable surface is clearly broad. It is simply not stated.

**Fix.** Enum both. `entity_type` is a closed set the backend already knows.

## P0-9i. A `PATCH` that says "partially update" and then deletes your other languages

```
PATCH /api/v1/translations/dictionary/{entry_id}

  summary:     "Partially update a dictionary entry"
  description: "Same semantics as PUT — a supplied `translations` map
                replaces (does not merge)."
```

**The operation contradicts itself inside its own definition.** The summary says *partially update*. The description says it does not.

**Consequence.** A dictionary entry holds `{base_term, {lang: translation}}` — the company-wide glossary. A caller adding Spanish does the obvious thing:

```jsonc
PATCH /translations/dictionary/42   { "translations": { "ES": "husillo" } }
→ 200 OK
```

**English, French, Italian and German are now gone.** Silently. From the company-wide terminology lock. The next machine translation of every document renders those terms however DeepL feels.

RFC 5789 defines `PATCH` as *partial* modification. Every other `PATCH` in this API behaves that way, which is exactly what makes this one lethal: an integrator who has correctly learned `PATCH` from the other 38 paths will destroy data here on their first try, and the endpoint's own **summary** will have told them it was safe.

This is the single easiest way to destroy data in the whole API, and it is reachable by doing the *conventional* thing.

**Fix.** Either make `PATCH` merge (correct, and what the summary already promises), or **remove `PATCH` entirely** and leave only `PUT` — whose "Replace a dictionary entry" summary is honest. Do not keep a `PATCH` that replaces. At minimum, change the summary to say "Replace" and the docs to shout it.

## P0-9j. `is_stale` exists on one locale type and not its sibling

| Schema | `source_content_hash` | `is_stale` |
|---|---|---|
| `ContentBlockLocaleResponse` | ✅ | ✅ |
| **`StructureBlockLocaleResponse`** | ✅ | ❌ **missing** |

Structure-block locales are **chapter and section titles**. Content-block locales are their bodies.

**Consequence.** You can ask whether a translated chapter *body* is stale. You **cannot ask the same about its title** — even though the hash that would answer it is right there on the response. And because the `source_content_hash` algorithm is undocumented, a client cannot recompute it to find out.

So: a technical writer edits a chapter title in German. Every translated title is now wrong. **Nothing in the API will tell you**, and a document ships with a heading that contradicts its own body.

**Fix.** Add `is_stale` to `StructureBlockLocaleResponse`. The hash is already there; this is a computed boolean the backend can produce for free.

## P0-10. Eight request schemas silently swallow unknown fields

`additionalProperties` is `false` on **116 of 124** request schemas — which is *good*, and means a typo'd field gets a loud `422`.

The **8 exceptions** are the danger, precisely because they're exceptions:

```
QuoteDetailsUpsertRequest      → PUT|PATCH /quotes/{quoteId}/details
QuoteContactAddRequest         → POST /quotes/{quoteId}/contacts
PartGroupCreateRequest         → POST /parts/groups
PartGroupUpdateRequest         → PATCH|PUT /parts/groups/{groupId}
GroupAreaLinkRequest           → POST /groups/{id}/areas
GalleryReorderRequest          → POST /products/{productId}/gallery/reorder
CompanyContactCreateRequest / CompanyContactUpdateRequest
```

**Consequence.** An agent learns from 116 schemas that a bad field `422`s — then hits `/quotes/{id}/details`, where its dropped field returns `200`. **The inconsistency is worse than either policy would be.**

**Fix.** `additionalProperties: false` on all 8.

---

# P1 — Machine-readability

The API works. The *spec* under-describes it, so everything that consumes the spec flies blind.

## P1-1. 119 enum-shaped fields are free strings; the whole spec has 14 enums

There are **14 string enums** in 210 schemas. There are **119 string fields whose names are unambiguously enum-shaped** (`*_type`, `status`, `state`, `*_mode`, `role`, `lifecycle_state`, …) typed as free strings.

Worse — **7 fields are an enum on one schema and a free string on another.** The vocabulary is known; it just isn't published where it's needed:

| Field | Enum in | Free string in |
|---|---|---|
| **`doc_type`** | `CloneRequest` = `['offer','technical_doc','ccms','custom']` | **`DocumentTemplateCreateRequest`** (the primary create endpoint!), `DocumentTemplateResponse`, `PartDocumentCreateRequest` |
| `attr_type` | `AttributeCreateRequest` | `AttributeResponse` |
| `method` | `EndpointCreateRequest` | `EndpointResponse` |
| `inheritance_mode`, `format`, `execution_mode`, `status` | their Request | their Response |

And `CombinationRuleCreateRequest.rule_type` is a **regex pattern**, not an enum:
`{"pattern": "^(forced|prerequisite|warning|visibility|recommendation|default|set_quantity)$"}` — codegen emits `string`, not a union.

`WebhookCreateRequest.events` is `array[string]` with **no enum at all** — the subscribable event set is undiscoverable from the spec.

**Consequence.** `POST /documents/templates` with `doc_type: "datasheet"` **passes schema validation.** The agent believes it succeeded. `additionalProperties: false` rejects unknown *keys*, never unknown *values*. And with every response-side enum a free string, an agent cannot exhaustively branch on `status` — it must guess the state machine.

**See also P2-6:** the one `doc_type` enum that does exist **is missing `quote`.**

**Fix.** Promote all 119 to `enum`, starting with `doc_type` on `DocumentTemplateCreateRequest` — the correct vocabulary already exists two schemas away.

## P1-2. 93% of schema fields have no description

| | count | share |
|---|---|---|
| Schema fields with no `description` | 1,274 / 1,369 | **93%** |
| Operations with no `description` | 294 / 463 | **63%** |
| Operations with no `summary` | 0 / 463 | **0%** ✅ |

**Consequence.** For 93% of fields, an agent must infer semantics from the field's *name*. `part_cost` — cents or euros? Per unit or per lot? `catalog_meta` — what goes in it? It guesses, and a guess in a BOM is a wrong quantity on a real quote.

`UsageSubclause` proves you can do this superbly. Extend that standard, starting with the fields an integration actually writes.

## P1-3. 24 free-form `object` fields with no shape

```
ForbiddenRuleCreateRequest.rule_json      ← P0-4, the worst
CombinationRuleCreateRequest.condition    ← an EMPTY schema {}
OptionCreateRequest.price_scalings        ← P1-4
BatchOperationRequest.match / .body       ← P1-6
StructureBlockCreateRequest.visibility
EndpointCreateRequest.response_extract
PartChangelogEntryResponse.changes
GalleryImageResponse.variants
…plus integration_metadata ×6, custom_fields ×4
```

Some are *legitimately* open (`integration_metadata`, `custom_fields` — customer-defined). But `rule_json`, `condition`, `price_scalings`, `visibility`, `match` and `response_extract` are **first-class product features with a fixed grammar**, typed as "an object, good luck."

**Fix.** Schema the ones with a grammar. For the genuinely open ones, *say so* ("arbitrary customer-defined key/value; never interpreted by Rattle") so callers know the freedom is intentional.

## P1-4. `option_scalings` is documented. `price_scalings` — its twin — is `additionalProperties: true`

```jsonc
// BomItemCreateRequest.option_scalings  ✅
{ "additionalProperties": {"type": "number"},
  "description": "Quantity scaling for numbered options: {option_id (string): multiplier}. ADDS to
                  the line's base quantity in proportion to a numbered option's selected amount…" }

// OptionCreateRequest.price_scalings  ❌
{ "additionalProperties": true, "title": "Price Scalings" }
```

Same mechanism. One fully specified; the other is `any`.

**Consequence.** An agent that learned `option_scalings` assumes `price_scalings` matches. And a scaling keyed against a **non-numbered** option is a **silent no-op** — accepted with a `200`, does nothing. The result is a wrong *price* — the one number the customer definitely reads.

**Fix.** Type it identically, with the parallel description — and **`422` on a key that isn't an `is_numbered: true` option id**, instead of silently ignoring it.

## P1-5. The `{"data": …}` envelope covers 93%, and the hole is the batch API

Of 389 JSON 2xx responses: **363 use `{"data": …}`; 22 are bare objects.** All 22 are batch/inbound — and they use **three mutually incompatible shapes**:

```
{total, succeeded, failed, results}   ← the 9 standard batch endpoints
{created, updated, errors}            ← POST /inbound/customers/batch
{count, product_id}                   ← POST /inbound/parts/batch
{job_id, status, task_id}             ← POST /inbound/triggers/{suffix}
```

**Consequence.** An agent doing `response["data"]` gets a `KeyError` (loud, fine). But the far more common **defensive** `response.get("data", [])` yields `[]` — so the agent concludes a 100-item batch **wrote nothing**, and may retry the entire thing.

**Fix.** Wrap batch results in `data`; collapse the three inbound shapes into the standard one.

## P1-6. Batch `upsert` is powerful and schema-blind

`BatchOperationRequest.action` includes `upsert` with a `match` field ("Match fields for upsert") — genuinely good. But **`match` is `{additionalProperties: true}`**, and so is `body`.

**Consequence.** Which fields are legal match keys, per resource, is **entirely undocumented**. An integrator cannot tell from the spec whether they may match a product on `name` — and certainly not on `sku`, which doesn't exist (P2-1). **The most valuable endpoint in the API is unusable without trial and error.**

**Fix.** Enumerate legal `match` keys per resource; `$ref` the real `*CreateRequest` into `body` via a discriminator.

## P1-7. `expand` is two-thirds undocumented — we probed a live tenant to find out

`expand` exists on **1 of 258 paths** (`GET /products/{id}`), typed as a free string, and its description says:

> "Comma-separated list of expansions: `areas`, `gallery`"

**That is not what the API does.** We ran read-only probes against a live tenant (2026-07-14) and the API told us the truth in its own error messages:

| Probe | Result |
|---|---|
| `expand=areas` | ✅ 200 |
| `expand=gallery` | ✅ 200 |
| `expand=models` | ✅ 200 — **undocumented** |
| `expand=price_overrides` | ✅ 200 — **undocumented** |
| `expand=pricing_presets` | ✅ 200 — **undocumented** |
| `expand=videos` | ✅ 200 — **undocumented** |
| `expand=areas.groups` | ✅ 200 — **dot-notation works, and is undocumented** |
| `expand=areas.groups,gallery,models` | ✅ 200 — **comma-combining works, undocumented** |
| `expand=areas.groups.options` | ❌ **400** — *"exceeds maximum depth of 2"* |
| `expand=groups` | ❌ 400 — *"Valid expansions: areas, gallery, models, price_overrides, pricing_presets, videos"* |

So: **the spec documents 2 of 6 expansions, and mentions neither the dot-notation nor its depth-2 limit.** Two-thirds of the feature is invisible.

**Credit where it's due:** the `400` bodies are *excellent* — they name the offending value **and enumerate every valid one**. That is exactly what a good API does, and it is the only reason we could establish the truth without backend access. **Please put that enumeration in the spec, where a client can read it before making the request instead of after.**

**We were wrong too, and we've fixed it.** Our own skill told agents to call `expand=areas.groups.options`. **It has never worked** — it is a `400`. That bug is now corrected in `skills/rattle-suggest-config/SKILL.md`, and this is a good illustration of the report's thesis: **an undocumented feature and a hallucinated feature are indistinguishable from the outside.** We guessed, the spec didn't contradict us, and the guess shipped.

**The real cost.** `options` is **not expandable at any depth** — the deepest a single call reaches is groups. So assembling a product's configuration graph is **irreducibly N+1**: one call for the tree, then **one call per group** to get its options. A modest product costs ~10 requests; a full catalogue costs thousands. There is no way to avoid it from the client side.

Worse still: **`GET /options/{optionId}/area-config` has `area_id` as a _required_ query parameter** and returns a single row. There is no list-all. Our audit tooling documents the consequence:

> *"There is no list-all-overrides endpoint for an option, so we must iterate the option's group's area links."*

For a 500-option catalogue across 6 areas that is **~3,000 sequential requests to audit price overrides alone.**

**Fix.**
1. **Document the four missing expansions, the dot-notation, and the depth-2 limit** — then make `expand` an `enum` so a client can discover them from the spec.
2. **Add `options` as an expandable value** (`expand=areas.groups.options`, i.e. raise max depth to 3). This single change collapses the most common read in the entire product from N+1 to 1.
3. **Make `area_id` optional on `/options/{optionId}/area-config`** — one line, deletes an entire N×M loop.

## P1-8. 78 of 116 collection endpoints declare no pagination

Where pagination *is* declared it is disciplined — 37 endpoints pair `cursor`+`limit` with a `meta` sibling, and **0 accept a `limit` without returning `meta`.** Credit for that.

But only **38 of 116** collection `GET`s declare it at all. The other **78** declare neither `cursor` nor `limit` — including `/areas/{id}/groups`, `/areas/library`, `/attributes/{id}/values`, `/catalog-filters`, `/baselines`.

**Consequence.** A caller cannot tell whether such a list is inherently bounded (fine) or unbounded-and-silently-truncated (data loss at scale). `/areas/{id}/groups` on a large catalogue is exactly the list that outgrows a default page — and an agent that reads 25 of 200 groups will confidently propose a **duplicate group that already exists.**

**Fix.** Declare `cursor`/`limit`, or state in the description that the list is complete and bounded. **Silence is the problem.**

## P1-9. Nothing is marked `deprecated`

`deprecated: true` — **0 of 463 operations; 1 of 1,369 fields.**

Yet legacy shapes demonstrably exist and are accepted: the legacy `rule_json` array (saves, never executes), `technical_documentation` as an alias for `doc_type=technical_doc`, and the legacy plurals `offers`/`quotes`.

**Consequence.** A caller cannot distinguish "the supported way" from "the way that still parses but is on its way out." We only learned which was which by reading backend source.

**Fix.** `deprecated: true` on every legacy path, field and enum value, naming the replacement. Free, and the clearest possible signal to an integrator.

---

# P2 — Capability gaps

Things a customer genuinely cannot do.

## P2-1. Products have no SKU — and the API already reads one back

**The most commercially significant gap in the API.**

`ProductCreateRequest` accepts exactly: `base_price · catalog_meta · currency · description · integration_metadata · is_active · language · name`. No `sku`, no `article_number` — on any product request or response.

**The smoking gun:**

```python
>>> spec["components"]["schemas"]["QuoteLineItemResponse"]["properties"]["product_sku"]
{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null, "title": "Product Sku"}
```

**`QuoteLineItemResponse.product_sku` exists** — and ships in your own example as `"WIN-PREM-001"`. The API surfaces a product SKU **on the customer-facing quote line**, the exact place an article number matters most. And there is **no public write path to ever populate it.** `sku` appears zero times as a settable field in the entire spec. It renders `null` on every quote.

**Consequence.** Every customer arrives with a pricelist keyed by article number — the most universal column in the domain, the join key to their ERP. There is nowhere canonical to put it. We were forced to invent a convention (`integration_metadata.<key>`), which is **unindexed** (no lookup by article number), **unvalidated** (no uniqueness), and **ours** — so two integrators pick two different keys and neither can read the other's data. Every ERP sync degrades to fetching the whole catalogue and matching client-side.

Contrast, and this is what makes the omission so odd: **`Part` has `part_number`. `Option`/`Group` have `key`. `Quote` has `quote_number`. `Customer` has `customer_id`** — a free-text external identifier, and the configurator can even be told to search on it (`customer_search_fields: ["organization", "customer_id"]`). **Every first-class entity has an external-identifier field except `Product` and `Area`.** The pattern exists; Product was simply left out of it.

> **Correction (2026-07-14).** An earlier revision of this report claimed "Product, Customer and Area have nothing." **That was wrong about `Customer`** — `CustomerCreateRequest.customer_id` exists (`string`, max 255) and is reachable via `?search=` and `/customers/search?q=`. We found this while mapping the CRM surface and are correcting it here rather than quietly editing it out. The finding stands for `Product` and `Area`.

**Fix.** Add `sku: string | null` to `Product{Create,Update}Request` + `ProductResponse` — **mirroring `Customer.customer_id`, which already proves the pattern.** Unique index per tenant, a `?sku=` exact-match filter, support as a batch `match` key, and wire it to `QuoteLineItemResponse.product_sku`.

## P2-1b. The entire sales lifecycle is a free string — the state machine is undiscoverable

The quote/opportunity lifecycle is the commercial core of a CPQ system. Not one of its states is declared:

```jsonc
QuoteStatusUpdateRequest.status  { "type": "string", "maxLength": 50 }   // PUT /quotes/{id}/status
QuoteResponse.status             { "type": "string", "default": "draft" }
OpportunityCreateRequest.stage   { "type": "string", "default": "qualification", "maxLength": 50 }
OpportunityResponse.stage        { "type": "string" }
```

**No enum. Anywhere.** And `GET /quotes?status=` accepts a filter whose **legal values are documented nowhere**.

**Consequence.** A client cannot:
- **enumerate the states** — so it cannot render a pipeline, a funnel, or a status dropdown without hard-coding a guess;
- **know the legal transitions** — is `draft → approved` allowed directly? Must it pass through `sent`? The API will tell you only by rejecting, or by silently accepting;
- **branch exhaustively** — every `switch` on quote status has an unreachable-in-theory `default` that is, in practice, where the bugs live.

`PUT /quotes/{id}/status` accepts **any string up to 50 characters.** `status: "aproved"` (typo) is a valid request as far as the schema is concerned.

**We could not establish the vocabulary.** Read-only observation of a live tenant surfaced only `draft`/`approved` (quotes) and `qualification` (opportunities) — and observed values are not the enum. Determining the rest would require *writing* to a live tenant, which we will not do. **So we are asking rather than guessing: what are the full status and stage vocabularies, and what transitions are legal?**

**Fix.** Declare `QuoteStatus` and `OpportunityStage` as enums, reference them from every request, response and query parameter, and document the legal transitions (even as prose). This is the single change that would make the CPQ half of the API programmable.

## P2-1c. There is no `POST /configurations` — the API cannot create the thing it quotes

Every write path in the configuration surface is missing. These are all ten operations:

```
GET  /configurations                       GET  /configurations/{id}
GET  /configurations/states/{hash}         GET  /configurations/states/by-code/{code}
GET  /configurations/states/by-code/{code}/parts
GET  /configurations/states/by-code/{code}/selections
GET  /customers/{customerId}/configurations
GET  /products/{productId}/configurations
POST /configurations/calculate             ← stateless pricing; returns a state, not an id
POST /configurations/{id}/finalize         ← locks one that already exists
```

**There is no endpoint that creates a saved configuration.** `POST /calculate` is stateless — it returns a `ConfigurationStateResponse` (a `config_code` / `config_hash`), not a persisted, finalizable `Configuration` with an `id`. `POST /{id}/finalize` can only lock a configuration that already exists.

**Consequence.** A saved configuration can apparently only originate **in the configurator UI**. So an integration that wants to go **quote-to-cash entirely through the API cannot**: it can price a configuration (`/calculate`), it can find one a human already made, and it can lock one — but it cannot *create* one. And a quote line item's `configuration_code` needs a configuration that exists.

For a CPQ platform, this is the load-bearing gap: **the API can quote a configuration, but it cannot produce one.** Every headless/automated quoting flow — an ERP raising a quote, a partner portal, an AI agent — stops here.

**Fix.** Add `POST /configurations` (persist a selection set against a product, returning an `id` and `config_code`). It is the missing half of an otherwise complete surface.

> If a create path *does* exist and we simply cannot see it, that is itself the finding — it is in neither the spec nor the reference. **Please tell us, and we will correct this section.**

## P2-1d. `POST /quotes` silently auto-creates an opportunity

Verbatim from the endpoint's own description:

> "Create a quote for an opportunity. **If no `opportunity_id` is given but a `customer_id` is provided, an opportunity is auto-created.**"

And the schemas disagree about whether it exists:

```jsonc
QuoteCreateRequest.opportunity_id  { "anyOf": [{"type":"integer"}, {"type":"null"}], "default": null }  // optional, nullable
QuoteResponse.opportunity_id       { "type": "integer" }                                                // REQUIRED, non-nullable
```

**Consequence.** Omitting `opportunity_id` does not mean "no opportunity." It means **an opportunity you did not name, did not stage, and do not know about** now exists in the customer's pipeline. Since `GET /customers/{id}/quotes` is documented as traversing *via opportunities*, these ghost opportunities are load-bearing — they are how quotes are found. A sales pipeline quietly fills with auto-generated records.

This is defensible behaviour, but it is a **side effect on a `POST`**, and it is discoverable only by reading one sentence of prose. The request/response asymmetry also breaks any generated client that round-trips the object.

**Fix.** Keep the behaviour if it is intended — but make the response asymmetry honest (`opportunity_id` is always present, so say so), and surface the auto-creation more loudly than a subordinate clause. Better: return the created opportunity in the response envelope so the caller can name it.

## P2-2. Constraints can *write* a quantity but cannot *read* one

The constraint DSL is presence-based only: clauses test whether an option is *selected*. No clause can read an option's numeric amount — even though `ConfigurationCalculateRequest.option_amounts` proves the runtime **has** those amounts at evaluation time.

**The asymmetry is stark.** `CombinationRuleCreateRequest` supports `rule_type: set_quantity` with `quantity_factor`, `quantity_offset`, `quantity_rounding`. **A rule can set a quantity as its effect — but cannot test one as its condition.**

**Consequence.** These are **not expressible, at all:**

- "Forbid the standard frame when panel count > 20."
- "Require the reinforced base above 15 m of run length."
- "This motor is valid only for 4–8 units."

**The configurator will happily let a customer order 40 panels on a frame rated for 20**, and that invalid configuration flows into a quote and onto the shop floor. In machinery most real rules are quantity-dependent. **This is the single largest class of missing configurator logic.**

**Fix.** Add a numeric clause: `{"option_amount": {"option_id": 117, "op": "gt", "value": 20}}`, AND-folded alongside the presence clauses, evaluated against the `option_amounts` map the calculator already receives. A DSL gap, not an architectural one.

## P2-3. Numbered options are integer-only, end to end

```json
"number_min":  {"type": "integer", "minimum": 0, "maximum": 1000000}
"number_step": {"type": "integer", "minimum": 1, …}
```

Not just an authoring limit — `ConfigurationCalculateRequest.option_amounts` is `{"additionalProperties": {"type": "integer"}}`, so the amount is an integer through the **entire pipeline**.

**Consequence.** A numbered option cannot express **2.5 m of profile**, **0.5 kg of coating**, or **1.75 m² of glass**. Every continuous quantity — length, area, weight, volume — is unrepresentable. That is cut-to-length, sheet goods, cabling, textiles.

The only workaround is unit inflation (model in mm, divide in the BOM factor). It is not free: **the customer sees `3000` where they think in `3 m`**, `number_unit` becomes a lie relative to their mental model, and every client carries an out-of-band conversion factor the API does not store. **Off-by-1000 errors here are silent and quote-destroying.**

Note the floor is inconsistent with the ceiling: **`option_scalings` is already `type: number`. The BOM side supports fractions. Only the option side is integer-locked.**

**Fix.** Widen `number_min/max/step` and `option_amounts` to decimal. Validate `(amount − min) % step == 0` in decimal, not float.

## P2-4. Fields accepted, returned `200`, and discarded

`ProductCreateRequest.currency` — its own description:

> "Accepted but ignored — currency is derived from the company's base price list"

But `currency` **is** returned on `ProductResponse`. A client writes `"USD"`, gets `200 OK`, reads back something else, never sees an error.

Same class: **`UsageSubclause.operator` is "ignored on the first term."** An author who writes `operator: AND` on clause 0 gets `OR` with **no warning**.

Note: the schemas `422` on **unknown** fields but silently discard **known-and-ignored** ones. **The API is strict about fields it doesn't know and permissive about fields it knows and throws away. That is backwards.**

**Fix.** Never return `200` for a write you discard. Either honour `currency` or `422` it. Reject a non-default first-clause `operator` rather than silently overriding it.

## P2-5. Parts have no image — not writable, not even readable

`part_img` appears **zero times in the entire spec.** Image upload exists for products (+ a full `/gallery`), areas, and options (even per-area). **Parts get nothing.** The field is populated only by the internal connector ingest pipeline; for parts created via the public API it stays `NULL` forever.

**Consequence.** Spare-parts catalogues, assembly instructions and exploded-view BOM UIs — core CPQ deliverables — cannot show part images through the public API.

**Fix.** Add `POST/DELETE /parts/{partId}/image`, mirroring the options route. Expose `part_img` on `PartResponse`.

## P2-6. The one `doc_type` enum is missing `quote`

```jsonc
CloneRequest.doc_type: {"enum": ["offer", "technical_doc", "ccms", "custom"]}   // ← where is "quote"?
```

**`quote` is a registered doc_type** — there is an entire `dynamic:document_line_items` contract around it — **and it is absent from the only enum in the spec.** On the face of it, **you cannot clone a quote template.** That looks like a plain omission. (Everywhere else `doc_type` is a free string — see P1-1.)

**Fix.** One `DocType` enum, referenced everywhere, **including `quote`**. Model the legacy values (`offers`, `quotes`, `technical_documentation`) as a separate `DocTypeFilter` enum, marked `deprecated`.

## P2-7. Webhooks cover quotes only — the catalogue emits nothing

The infrastructure is solid (`/webhooks`, `/deliveries`, `/rotate-secret`, `/test`). But the only event types referenced anywhere are **`quote.created`, `quote.status_changed`, `quote.updated`**. Nothing for product, part, option, group, area, bom, constraint, price-list, or document.

**Consequence.** Any system mirroring the catalogue — ERP, PIM, storefront, search index — **must poll.** There is no way to react to "a part cost changed" or "an option was added" — precisely the events that invalidate a cached price or BOM. Combined with P1-7 (no `expand`), a full catalogue poll is thousands of requests.

**Fix.** Emit `<resource>.{created,updated,deleted}` for product, part, option, group, area, bom_item, constraint, price_list. Publish the enum in `WebhookCreateRequest.events`.

---

# P3 — Consistency

Individually harmless. Together they mean an agent cannot generalise from one endpoint to the next — and **every generalisation it makes is a coin flip.**

## P3-1. 39 distinct path-parameter names; 13 resources use more than one

Across 419 path params: **39 distinct names in 3 casing conventions** — 25 camelCase (`productId`, `partId`…), 9 snake_case (`area_id`, `block_id`, `contact_id`…), 5 bare (`id`, `code`, `hash`, `lang`, `suffix`). `{id}` alone appears 106 times.

**13 of 59 resources name their own identifier more than one way** — and the *same resource* switches convention between its base path and its sub-resources:

```
/parts/{id}                     /products/{id}
/parts/{id}/bom                 /products/{productId}/areas
/parts/{partId}/revisions       /products/{productId}/areas/{areaId}
```

`areas` and `contacts` use **three** conventions each:

```
/areas/{id}/groups              /company/contacts/{id}
/areas/{areaId}/options         /customers/{id}/contacts/{contact_id}
/groups/{id}/areas/{area_id}    /quotes/{quoteId}/contacts/{contactId}
```

**Consequence.** Loud `404`, so it's recoverable — but **it defeats few-shot generalisation entirely.** An agent that has seen `/parts/{id}` cannot construct `/parts/{partId}/revisions`; it must look up all 258 paths individually. This is the finding that most directly costs an agent its ability to *guess*.

**Fix.** `{id}` for the resource that owns the path; `{parentId}` only to disambiguate a nested parent. One casing. **This changes the *spec*, not the *URLs*** — path-param names are local identifiers. Nearly free.

## P3-2. Create/update asymmetry: 37 create-only and 19 update-only fields

Two patterns are *correct* — keep them: immutable FKs are create-only (`Area.product_id`, `Option.group_id`, `BomItem.parent_part_id`), and lifecycle state is update-only (`ChangeOrder.state`).

The inconsistencies:

- **`order_index` is creatable on 13 resources but update-only on 5** (`Product`, `PriceList`, `Language`, `CatalogFilterDimension`, `CatalogFilterValue`). Same field, same meaning, arbitrarily different — forcing a create-then-PATCH round trip on exactly those 5, for no stated reason.
- **`Quote`**: `discount_amount`, `discount_percent`, `tax_amount`, `terms_and_conditions` are update-only. **You cannot create a discounted quote in one call.**
- **`DocumentTemplate` can be published two ways** — `PATCH {is_published: true}` *or* `POST /templates/{id}/publish` — with no statement of which is authoritative or whether they agree.

## P3-3. `429` on every operation, with no `Retry-After`

All 463 operations declare `429`. **None** declares `Retry-After`, `X-RateLimit-Limit`, `-Remaining` or `-Reset`.

**Consequence.** A rate-limited client cannot back off correctly — only guess. Agents are *bursty* by nature (they fan out reads), so they will hit this and guess badly.

## P3-4. Smaller items, each one line

- **`DELETE /documents/content-blocks/images` is the only operation with a body on a `DELETE`.** Bodies on DELETE are **widely stripped by proxies and HTTP clients** → **silent no-op deletion**. Move the URL to a query param.
- **3 image uploads declare no `requestBody` at all** — the multipart body exists only in prose ("Send as multipart/form-data with field name 'image'"). A spec-driven client sends an empty POST.
- **POST success codes vary** — `201`×76, `200`×38, `202`×7. And `Location` is **missing on 15 of 78** POSTs that can return `201`. An agent gating on `201` mishandles the 38 creates that return `200`.
- **Read-only actions use POST.** `POST /parts/{id}/bom/explode` is documented `Scope: parts:read` — a read via POST — while its siblings `GET /bom/flat` and `GET /bom/tree` are GETs. `POST /parts/{id}/bom/validate` takes **no body** yet is a POST, while the equivalent `GET /documents/templates/{id}/validate-config` is a GET.
- **5 orphan schemas** are defined but referenced by no operation (`ApiKeyCreateRequest`, `CompanyContactCreateRequest`, …). The endpoints exist but use **inline** schemas — which is also why they escaped the `additionalProperties: false` policy in P0-7.
- **5 Response schemas declare no `required` fields whatsoever** — an agent cannot rely on *any* field being present.

---

# Suggested order of work

| # | Finding | Why now | Cost |
|---|---|---|---|
| 1 | **P0-1** Declare the 4 headers + `409` | Silent lost update on an atomic replace-all. Nothing else here destroys data with a `200 OK`. | **Spec only** |
| 2 | **P0-2** `readOnly: true` on the 200 response-only fields | Makes read-modify-write work for every client and agent, automatically. | **Spec only** |
| 2b | **P0-7** Regenerate `ConfiguratorSettingsResponse` | The spec describes **5 fields that don't exist** and omits the **20 that do** — and they govern the customer-capture UX. Zero overlap. | **Spec only** |
| 2b2 | **P0-9i** Make dictionary `PATCH` merge (or delete it) | Its **summary says "Partially update"** and its description says it **replaces**. A `PATCH` adding one language **silently deletes the others**. Easiest data loss in the API, reachable by doing the conventional thing. | **Trivial** |
| 2c | **P0-8** Document the pricing resolution order | Four mechanisms can set one option's price and the spec never says which wins. Every other silent-wrongness finding costs a retry; **this one costs money on a signed quote.** One paragraph fixes it. | **Spec only** |
| 2d | **P0-9** Name + describe `advanced-prices` | A cross-option conditional-price engine with no schema, no description, and no name. We deduced what it does from a required field name. **A feature nobody can find.** | **Spec only** |
| 3 | **P0-6** Fix `servers` / `/api/v1` | One line. Every generated client hits it. | **One line** |
| 4 | **P0-4** Schema `rule_json`; `422` the legacy shape | Constraints that save and never fire. Ships broken machines. | Small |
| 5 | **P0-3** Disambiguate PUT vs PATCH | Silent field-nulling on a standard REST idiom. | Small |
| 6 | **P1-1** Promote 119 free strings to `enum` (start with `doc_type`) | `doc_type: "datasheet"` currently validates. | Spec only |
| 7 | **P2-6** Add `quote` to the `DocType` enum | Quote-template cloning appears simply broken. | Trivial |
| 8 | **P1-7** Document the 4 hidden expansions + dot-notation; add `options` as expandable; `area_id` optional on area-config | Two-thirds of `expand` is undocumented. Adding `options` collapses the most common read in the product from **N+1 to 1**. The area-config change alone deletes a ~3,000-request loop. | Small |
| 9 | **P0-5** One money type; fix `part_cost` | Silent precision loss that compounds up the BOM tree. | Migration |
| 10 | **P2-1** `Product.sku` | Most commercially significant gap. `product_sku` is already on the quote line with no writer. | Medium |
| 11 | **P2-2 / P2-3** Quantity-aware constraints; fractional numbered options | Unblocks most of industrial configuration. | Medium |
| 12 | **P3-1** Normalise path params | Cheap, and it makes the API learnable. | Spec only |

**The cheapest high-value pass — items 1, 2, 3, 6, 7 — is almost entirely *spec* work against behaviour the backend already implements.** Together they remove the silent lost-update path, make read-modify-write work, fix the universal double-prefix trap, stop `doc_type` typos validating, and unbreak quote cloning. **We'd estimate under a day, and it would be the single highest-leverage day anyone spends on this API this quarter.**

---

# A pattern worth naming

Two of the sharpest gaps — `product_sku` and `part_img` — share a shape: **fields the internal connector pipeline can populate but the public API cannot.** Both surface on read paths or adjacent schemas, which makes them *look* supported right up until an integrator tries to write one.

That asymmetry between the ingest pipeline and the public API is where a disproportionate share of these findings live, and it will keep producing new ones unless the public API is treated as a first-class writer of the same model.

---

# Reproducing every finding

```bash
git clone https://github.com/rattleai/grimoire.git && cd grimoire
python3 scripts/build_api_reference.py     # fetches the live spec → docs/openapi.json
```

```python
import json; d = json.load(open("docs/openapi.json"))
S, P = d["components"]["schemas"], d["paths"]

# P0-1 — the header is in the prose, not in the parameters
P["/api/v1/constraints"]["post"]["description"]      # "...Include the X-Constraints-Version header..."
"parameters" in P["/api/v1/constraints"]["post"]     # False
list(P["/api/v1/constraints"]["post"]["responses"])  # ['200','401','422','429'] — no 409

# P0-2 — you cannot PUT back what you GET
set(S["ProductResponse"]["properties"]) - set(S["ProductUpdateRequest"]["properties"])
# 13 fields the server sends and refuses back
S["ProductUpdateRequest"]["additionalProperties"]    # False  → 422

# P0-4 — the constraint DSL, in full
S["ForbiddenRuleCreateRequest"]["properties"]["rule_json"]     # {'title': 'Rule Json'}

# P0-6 — the double-prefix trap
d["servers"]                                          # [{'url': '/'}]
list(P)[0]                                            # '/api/v1/analytics/...'

# P2-1 — the smoking gun: a read-only SKU with no writer
S["QuoteLineItemResponse"]["properties"]["product_sku"]        # exists
sorted(S["ProductCreateRequest"]["properties"])                # no sku

# P2-6 — quote missing from the only doc_type enum
S["CloneRequest"]["properties"]["doc_type"]
```

**The live probe (P1-7)** — read-only, and it is how we found the four hidden expansions:

```bash
# Every valid expansion, straight from the API's own 400:
curl -s -H "Authorization: Bearer $RATTLE_API_KEY" \
     -H "User-Agent: grimoire/1.0" \
     "https://www.rattleapp.de/api/v1/products/{id}?expand=groups" | jq -r .detail
# → "Unknown expansion 'groups'. Valid expansions: areas, gallery, models,
#    price_overrides, pricing_presets, videos."

# The depth limit nobody documented:
curl -s … "…/products/{id}?expand=areas.groups.options" | jq -r .detail
# → "Expansion 'areas.groups.options' exceeds maximum depth of 2."
```

(Note: Cloudflare returns **1010 / `browser_signature_banned`** to the default `python-urllib` User-Agent. Any client must send a real UA — worth documenting for integrators, as it looks like an auth failure but isn't.)

Every count in this report was asserted by script against the published spec. We re-verified all of them before publishing and **corrected three of our own claims** in the process — including the `expand` bug that was live in our own skill.

---

# Closing

We built Grimoire because the **Rattle domain model is genuinely good** — `usage_subclauses`, ghost parts, `alt_group`, area-scoped overrides, savepoint-isolated batch upserts, a 100%-consistent RFC 9457 error contract. These are sophisticated, well-conceived primitives, and the fact that an AI agent can be taught to use them correctly is a compliment to the design.

**The gap is not in the model. It is that the spec describes a fraction of what the API knows** — and the parts it omits are exactly the parts that bite: the concurrency header, the constraint grammar, the idempotency key, the read-only fields, the SKU that already exists on the quote line.

An integrator with backend access can find these. **An autonomous agent — increasingly who is calling your API — cannot.**

Closing P0 and P1 would make this an API an AI can drive **safely, without a human checking its work.** In CPQ that is a real competitive position, and it is much closer than this list makes it look.

Happy to pair on any of it, and happy to re-run this audit against a new spec whenever you'd like.
