# Price resolution — the mechanisms, and how to find out which one wins

> **The single most important sentence in this file:** Rattle does not document a pricing precedence, this file does not invent one, and **any precedence you act on must have been measured.**

---

## 1 · The mechanisms, in depth

Five things can set the price of one option. A sixth (`price_scalings`) scales it. Two more set the price of the *area* and the *product* rather than the option. All of them are live at the same time.

### 1.1 Base price — `Option.price`

```jsonc
OptionCreateRequest.price   { "type": "string", "default": "0.00" }
OptionResponse.price        { "type": "string", "default": "0.00" }
```

A decimal **string**, both directions. The unconditional default. Under the `#1 rule` (`rattle-configurator`) **every variant has an explicit option**, so the standard variant is an option at `price: "0.00"` and the upgrade is an option at `price: "500.00"` — the delta is expressed as two explicit prices, never as an implicit surcharge on an implicit baseline.

### 1.2 Price list — the axis, not a price

```jsonc
PriceListCreateRequest {
  "required": ["name"],
  "name":        { "type": "string", "maxLength": 255, "minLength": 1 },
  "currency":    { "type": "string", "maxLength": 3, "default": "EUR" },   // ← the currency lives HERE
  "description": { "type": "string", "maxLength": 2000, "default": "" },
  "is_base":     { "type": "boolean", "default": false },
  "additionalProperties": false
}
```

A price list **holds no prices.** It is the axis every override below is scoped to. Two things follow:

- **The currency lives here and nowhere else.** `Product.currency` is *"Accepted but ignored — currency is derived from the company's base price list"* (audit § **P2-4**). Sending it is a `200 OK` and a discarded field. The base price list must exist **before the first product** (`rattle-onboarding` § "The ordering rule that bites").
- **`is_base: true` on exactly one list is a convention, not an invariant.** Nothing in the schema, and nothing in any description, prevents two base lists — or zero. `GET /price-lists` and check. `PriceListResponse` also carries `order_index` (update-only — audit § **P3-2**), set via `POST /price-lists/reorder` (`{"order": [10, 11, 12]}`, maxItems 200).

> **`PriceListResponse` carries no version field.** Fields: `id`, `name`, `currency`, `description`, `is_base`, `order_index`, `created_at`, `updated_at`, `links`. This matters — see § 4.

**`DELETE /price-lists/{id}` returns `204`. What happens to the overrides that referenced it is not documented.** Cascade, orphan or `409` — the spec says nothing and declares no `409`. **Do not delete a price list that has overrides without checking `GET /price-lists/{id}/overrides` first**, and tell the user what you found.

### 1.3 Price-overrides — three families, three different shapes

The brief-level summary "same shape under `/areas/…` and `/products/…`" is **wrong**, and the differences bite. Verified against `docs/openapi.json`:

| | **Option** | **Area** | **Product** |
|---|---|---|---|
| Path | `/options/{optionId}/price-overrides` | `/areas/{areaId}/price-overrides` | `/products/{productId}/price-overrides` |
| Create schema | `PriceOverrideCreateRequest` (**named**) | **INLINE** — no named component | `ProductPriceOverrideCreateRequest` (**named**) |
| `additionalProperties: false` | **yes** | **NO — swallows unknown fields** | **yes** |
| Required | `area_id`, `price_list_id`, `override_price` | `price_list_id`, `override_price` | `price_list_id`, `override_price` |
| **Keyed on** | **(option, area, price_list)** — a **triple** | (area, price_list) | (product, price_list) |
| `override_price` type (request) | `number \| string` | **`string` only** | `number \| string` |
| `override_price` type (response) | `string` | `string` | `string` |
| `409` on POST | **NOT declared** | **declared** | **declared** |
| Replace `maxItems` | 500 | **none declared** | 500 |
| Overrides the price of | **the option** | **the area's base price** | **the product's base price** |

Three things to carry out of that table:

1. **The option override is keyed on a TRIPLE.** `area_id` is *required*. The same option, in two areas, on one price list, can carry two different prices. This is the mechanism that makes group reuse across areas viable (`reuse-over-duplicate`) without duplicating the group.
2. **The area and product overrides do not price options at all.** Their own descriptions: *"List all price-list overrides for an **area's base price**"* and *"…for a **product's base price**."* They move `Area.price` and `Product.base_price`. They are a different axis, not a competing one — which is why a "precedence" between an option override and a product override may not even be a coherent question. **Measure; do not reason.**
3. **The `409` asymmetry is a natural-key signal.** Area, product and preset `POST`s declare `409`; the option `POST` does not. **Inference, labelled as such:** the 409s imply the backend enforces uniqueness on (area, price_list), (product, price_list) and (product, `key`). For the option **triple**, uniqueness is **unverified** — the spec may have omitted the `409`, or duplicates may be accepted. **Do not rely on the API to reject a duplicate option override. Read the list and check yourself.**

**Every update request in all three families carries only the price:**

```jsonc
PriceOverrideUpdateRequest        { "override_price": "number|string|null" }   // and nothing else
ProductPriceOverrideUpdateRequest { "override_price": "number|string|null" }
// area PUT/PATCH (inline)        { "override_price": {"type": "string"} }
```

**The keying fields are create-only.** You cannot `PATCH` an override onto a different area or a different price list. It will not move and it will not complain. **DELETE and re-POST.**

### 1.4 Advanced price — the conditional

See **`advanced-prices.md`**. In one line: `condition_option_id` is **required**, so an advanced price is *"this option costs X when that other option is also selected"*.

### 1.5 Pricing preset — the product-level fee

```jsonc
PricingPresetCreateRequest {
  "required": ["key", "label", "category", "amount_type"],
  "key":         { "type": "string", "maxLength": 100, "minLength": 1 },   // natural key with product_id
  "label":       { "type": "string", "maxLength": 255, "minLength": 1 },
  "category":    { "type": "string", "maxLength": 50 },    // ← FREE STRING. No enum.
  "amount_type": { "type": "string", "maxLength": 50 },    // ← FREE STRING. No enum.
  "value":       { "anyOf": [{"type":"number"},{"type":"string"}], "default": "0" },
  "taxable":     { "type": "boolean", "default": false },
  "default_on":  { "type": "boolean", "default": false },
  "additionalProperties": false
}
// Response adds: id, product_id, sort_index (default 0). `value` comes back a STRING.
```

Not an option — a **product-level adjustment line**: assembly, freight, handling, a blanket surcharge, a blanket discount. `default_on: true` means it applies unless switched off. `POST …/pricing-presets/reorder` sets `sort_index` (`{"order": [5, 3, 7]}`, minItems 1, maxItems 100).

> **`category` and `amount_type` are free strings with no enum — the vocabulary is undiscoverable from the spec.** Exactly the disease audit § **P2-1b** names for quote `status`.
>
> **What is known, and what it is worth:** the spec's own *example* on `PricingPresetCreateRequest` reads `{"amount_type": "fixed", "category": "surcharge", "key": "assembly_fee", "label": "Assembly Fee", "taxable": true, "default_on": true, "value": "150.00"}`, and the `GET` description says *"pricing adjustment presets (**surcharges, discounts, fees**)"*. **That is an example and a prose hint. It is not an enum and it is not a vocabulary.** `amount_type: "fixed"` strongly implies a percentage sibling exists — but its spelling (`percent`? `percentage`? `pct`?) is **not knowable from the spec**, and a wrong string is a `200 OK` and a preset that no downstream consumer recognises.
>
> **The procedure:** `GET /products/{id}/pricing-presets` across the catalogue, collect the distinct `category` and `amount_type` values, and use only those. **If the one you need is absent, ASK THE USER.** Introducing a new category string is a business decision with reporting consequences, not an API call. Record the confirmed vocabulary in `memory/<tenant>/profile.md`.

### 1.6 The two that hide

- **Option area-config `price`** — `PUT /options/{optionId}/area-config?area_id=<id>` (scope `prices:write`). Inline body, **no required fields, no `additionalProperties: false`**:

  ```jsonc
  { "price": {"type":"string"}, "option_description": {"type":"string"}, "option_key": {"type":"string"},
    "recommended": {"type":"boolean"}, "is_numbered": {"type":"boolean"},
    "number_min": {"type":"number"}, "number_max": {"type":"number"}, "number_step": {"type":"number"},
    "number_unit": {"type":"string"} }
  ```

  **A price for an option, in an area, with no price list.** Keyed on **(option, area)**. `DELETE …?area_id=<id>&field=price` clears just that column; omit `field` and the whole override row goes.

  Two footnotes. `area_id` is a **required query param on the GET** and there is **no list-all**, so auditing area prices is an N × M loop (audit § **P1-7**). And `number_min/max/step` are **`number`** here while `OptionCreateRequest` types them **`integer`** (audit § P2-3) — the same three fields, two different types, in one API. Neither is documented as authoritative.

- **`price_scalings`** — `{"additionalProperties": true}`, untyped (audit § **P1-4**). Scales the option's price by a **numbered** option's selected amount. Its BOM twin `option_scalings` is `{"additionalProperties": {"type": "number"}}` with a full description, and its three descriptor shapes (legacy numeric / `{opt, part}` ratio / `{areas: [{min, max, part}]}` range) are documented in `rattle-bom-builder/references/option-scalings.md`.

  > **Do not assume `price_scalings` accepts the same three shapes.** It is plausible — same name, same mechanism, same codebase — and it is **not stated anywhere**. That is an inference, and inferences about money get measured, not shipped. **A scaling keyed against a non-`is_numbered` option is a silent no-op: `200 OK`, unchanged price.** Set `is_numbered: true` first, then verify the scaled price through `/calculate`. Nothing else will tell you.

---

## 2 · Which one wins?

**Unknown. Not documented. Not inferable.**

Grepped over the whole of `docs/openapi.json`:

| Term | Hits |
|---|---|
| `precedence` | **1** — and it is `usage_subclauses` boolean operators, in the BOM: *"There is no operator precedence; it is a pure left fold."* |
| `resolution order` · `takes priority` · `falls back` · `fallback` · `most specific` · `overrides the` · `supersede` · `wins` | **0** |

Nothing in any endpoint description, any schema description, or `info.description` states an order.

**Therefore this file states none.** "Most specific wins" is the intuitive answer and it may well be right — **and asserting it would be a fabrication**, indistinguishable from documentation to anyone reading this file six months from now. The repo has been burned by exactly that once already: `expand=areas.groups.options` was authored into a skill on the strength of it *seeming* correct. It had never worked — it is a `400` (audit § **P1-7**), and the audit's own conclusion is the rule for this file:

> *"An undocumented feature and a hallucinated feature are indistinguishable from the outside."*

**The cheapest way to be right is to never need the answer.** Do not stack two mechanisms on one option. One mechanism, per option, per purpose. A catalogue with no overlap has no precedence problem — and that, not a measured table, is the recommendation.

When you cannot avoid it: measure.

> **Reported upstream — `docs/API_AUDIT.md` § P0-8**, *"Four mechanisms can set one option's price. The spec never says which wins."* It states the consequence more sharply than this file does: *"A tenant configures an option price-override **and** an area price-override for the same option and price list. **Which one does the customer pay?** The API knows. The spec does not say. The client cannot know, and — this is the part that matters — **it will not error.** It will return a price. A plausible one. Possibly the wrong one, on a quote that goes to a customer."*
>
> The fix requested of Rattle is one paragraph in `info.description`, plus a **`price_breakdown` on the `/calculate` response** showing which mechanism supplied the final number. **That second item is what would retire this entire file.** Until it exists, § 3 is the only honest way to answer the question.

---

## 3 · Determining the resolution order empirically

### 3.0 Preconditions

- **A TEST tenant. Never production.** This procedure deliberately installs a conflicting override and deliberately provokes a wrong price. In a live catalogue, a customer can configure the machine mid-experiment.
- **A product you control end to end**, whose total is *only* the option under test. Any other contribution corrupts every reading.
- **A throwaway price list** (`is_base: false`), so the base list is untouched.

### 3.1 The oracle is a scalar — and that dictates the method

```
POST /api/v1/configurations/calculate     → 201
```
> *"Resolve constraints, **compute pricing**, and return a configuration state."*

```jsonc
ConfigurationCalculateRequest {
  "required": ["product_id"],
  "product_id":       { "type": "integer" },
  "selected_options": { "additionalProperties": {"items": {"type":"integer"}, "type":"array"} },  // {area_id: [option_id,…]}
  "option_amounts":   { "additionalProperties": {"type": "integer"} },                            // {option_id: int}
  "price_list_id":    { "type": "integer | null", "default": null },
  "enabled_areas": [], "disabled_areas": [], "wishlist_options": [],   // maxItems 500 each
  "validate_config":  { "type": "boolean", "default": true },
  "additionalProperties": false
}
```

**Note `selected_options` is keyed by AREA id**, mapping to a list of option ids. That is precisely what makes an (option, **area**, price_list) override addressable from the calculator.

It returns `ConfigurationStateResponse`:

```json
{"data": {"config_code": "…", "config_hash": "…", "price_snapshot": "2485.00",
          "is_valid": true, "validation_errors": null, "product_id": 42}}
```

> **`price_snapshot` is a single decimal string. The grand total. There is no itemisation.**

So **you cannot ask the API which price won.** You can only ask what the total is. The method is therefore **differential**: make the candidate prices arithmetically distinguishable, isolate one option, and decode the total.

**`POST /calculate` writes no catalogue data.** It persists an immutable *state* (content-addressed, retrievable by `config_hash` / `config_code`) — but it creates no product, option, override or configuration record. It is safe to call repeatedly. Note it returns **`201`**, not `200`.

### 3.2 The endpoint that should have answered this directly — and its defect

```
GET /api/v1/configurations/states/by-code/{code}/selections
```
> *"Get enriched selected options — Returns each selected option enriched with group name, option name, **price**, quantity, and wishlist status. Supports ETag caching."*

**Its declared `200` schema is `ConfigurationStateResponse`** — the same scalar state object. **No per-option array. No per-option price field. No `data[]`.** The itemised breakdown is promised in the description and absent from the schema. (It also declares **no parameters at all**, despite claiming ETag support — the `If-None-Match` header is undeclared, audit § **P0-1**.)

This is the same class of defect as audit § **P0-7** (`ConfiguratorSettingsResponse` describes five fields that do not exist and omits the twenty that do). **This instance is not yet in `docs/API_AUDIT.md`. Report it.**

> **Probe it FIRST anyway.** If the runtime returns what the *description* promises — enriched selections carrying a resolved per-option `price` — then **the entire precedence problem collapses into a single read**, and §§ 3.3–3.6 are unnecessary. If it returns what the *schema* declares, fall back to the differential method. **Report which one you got, either way.**

**A second, partial oracle — labelled as the inference it is.** `GET /analytics/option-selections` (scope `analytics:read`) returns `OptionSelectionFactResponse`, which carries `option_id`, `area_id`, `group_name`, **`unit_price`** and **`total_price`** — a **resolved per-option price**, after the pricing engine ran. Two caveats, both disqualifying for measurement: they are **`number` (float)** — audit § **P0-5**, never trust a float on the money path — and it is a **fact table of selections that already happened**, not a calculator you can drive. It is useful for *observing* what a live tenant has actually been charging. It is **not** a way to run an experiment.

### 3.3 Choose prices that cannot collide

Use **powers of ten**. Any observed total then decodes to exactly one hypothesis.

| Mechanism under test | Value |
|---|---|
| `Option.price` (base) | `"100.00"` |
| Option price-override | `"200.00"` |
| Advanced price | `"400.00"` |

Never pick values that can sum to one another (`100` + `200` = `300` is fine and unambiguous; `100` + `100` = `200` would be fatal — you could not tell "two applied" from "the override replaced").

### 3.4 The setup — synthetic, `acme-test`

```
Product  "Widget Pro"                       base_price "0.00"
Area     "Chassis"                (id A)    price      "0.00"
Group    "Wheels"  is_multi: false
  Option "17 inch"  recommended             price      "0.00"
  Option "19 inch"                 (id W)   price      "100.00"
Group    "Packages"  is_multi: true
  Option "Winter package"          (id X)   price      "0.00"      ← the condition option; price 0 so it
                                                                     contributes nothing to the total
Price list "TEST"                  (id L)   is_base: false, currency EUR
```

**`Winter package` is priced `"0.00"` deliberately.** It exists only to be *selected*, so that it can trigger the advanced price without adding anything to the total. If it had a price, every reading in § 3.6 would be contaminated.

### 3.5 Step 0 — baseline, and the gate

```json
POST /api/v1/configurations/calculate
{"product_id": <P>, "price_list_id": <L>, "selected_options": {"<A>": [<W>]}}
```

**Expect `price_snapshot: "100.00"`.**

**If it is anything else, STOP.** Something in the product contributes a price you have not accounted for — a preset with `default_on: true`, an area price, a product base price. Find it and zero it. Every subsequent reading is meaningless until this one is exact.

### 3.6 The worked two-level conflict

**Level 1 — `Option.price` vs. the option price-override.**

```json
POST /api/v1/options/<W>/price-overrides
{"area_id": <A>, "price_list_id": <L>, "override_price": "200.00"}      → 201
```

Re-run the **identical** calculate body from § 3.5:

| `price_snapshot` | What it means |
|---|---|
| `"200.00"` | The override **replaced** the base price. |
| `"300.00"` | The override was **added** to the base price. |
| `"100.00"` | **The override did not apply at all.** ← |

**The third row is the one that ruins a quarter.** `201 Created`, a row in the database, a `GET` that lists it happily — and **no effect on the price.** If you see it, the override is keyed against something the calculator is not looking at (wrong `area_id`, wrong `price_list_id`, or the option is not reachable in that area). It is silent, and only `/calculate` reveals it. **This alone is why every pricing write in this skill is read back through the calculator.**

**Level 2 — the override vs. the advanced price.**

```json
POST /api/v1/options/<W>/advanced-prices
{"condition_option_id": <X>, "advanced_price": "400.00", "area_id": <A>, "price_list_id": <L>}   → 201
```

Now select **both** the wheel and the condition option:

```json
POST /api/v1/configurations/calculate
{"product_id": <P>, "price_list_id": <L>, "selected_options": {"<A>": [<W>], "<Pkg>": [<X>]}}
```

| `price_snapshot` | Hypothesis |
|---|---|
| `"400.00"` | The advanced price **wins outright** — it replaces both the base and the override. |
| `"600.00"` | Advanced **adds** to the override (`200 + 400`). |
| `"500.00"` | Advanced **adds** to the base, ignoring the override (`100 + 400`). |
| `"200.00"` | The override wins; **the advanced price did not fire.** |
| `"700.00"` | All three stacked (`100 + 200 + 400`). |

Every total decodes to exactly one hypothesis. **That is what the powers of ten bought you.**

**Control run — always.** Re-calculate with the **condition option deselected**. The advanced price must *not* contribute. If it does, `condition_option_id` is not doing what its name says, and **nothing else you measured is trustworthy.**

```json
POST /api/v1/configurations/calculate
{"product_id": <P>, "price_list_id": <L>, "selected_options": {"<A>": [<W>]}}
→ must return the level-1 answer, unchanged
```

**Level 3 — the price list itself.** Re-run every calculate above with **`price_list_id` omitted**. Overrides scoped to list `L` should not fire. If they do, the scoping is not what the schema implies, and that is a finding worth reporting upstream.

### 3.7 Do not extrapolate

**Measure each pair you actually intend to use.** A system can replace in one pair and add in another; nothing in the API forbids it and nothing documents it. An order measured for (base, option-override) tells you **nothing** about (area-override, product-override), and the option/area/product families do not even price the same entity (§ 1.3).

### 3.8 Tear down

`DELETE` every override, advanced price and preset you created. An abandoned experiment is an unexplained override in a tenant six months from now — and it will be found by a customer, not by you.

### 3.9 Record it — with its provenance

`memory/<tenant>/profile.md`. `rattle-tenant-memory` is **explicit-write only**: show the file, get consent.

```markdown
## Pricing resolution (MEASURED — Rattle documents no precedence)
- **status**: observed, not specified
- **measured-on**: 2026-07-14
- **measured-in**: `acme-test` (a TEST tenant — never production)
- **method**: differential POST /configurations/calculate, powers-of-ten values.
  See skills/rattle-pricing/references/price-resolution.md § 3.
- **/selections probe**: returned the scalar state (schema), NOT the enriched per-option
  prices its description promises. Differential method required.
- **Option.price vs option price-override**: override REPLACES base   (100 → 200)
- **option price-override vs advanced price**: <what you measured>
- **control**: advanced price did NOT fire with the condition option deselected ✓
- **NOT measured**: area-override, product-override, price_scalings, two matching
  advanced prices on one option.
- **caveat**: This is a MEASUREMENT, not a contract. Rattle may change it without
  notice. Re-verify after any platform upgrade. Never present it as documented.
```

**"Observed" and "documented" are different epistemic states, and the next session must be able to tell which it is reading.** That is the whole reason the provenance block exists.

---

## 4 · The concurrency hole, in this surface

```
POST /api/v1/options/{optionId}/price-overrides/replace
POST /api/v1/areas/{areaId}/price-overrides/replace
POST /api/v1/products/{productId}/price-overrides/replace
```
> *"Delete all existing overrides and replace with the provided set."*

`info.description`, verbatim:

> *"Bulk-replace endpoints for constraints and price lists use version headers (`X-Constraints-Version`, `X-Price-Lists-Version`) for optimistic locking. **Read the current version from a GET response**, then include it in your write request to detect concurrent modifications."*

**Three problems, compounding (audit § P0-1):**

1. **No price-override `/replace` endpoint declares the header.** The current spec *does* declare `X-Price-Lists-Version` — but only on **price-list CRUD** (`POST/PATCH/PUT/DELETE /price-lists`), **not on a single `/replace`**. A spec-driven client — codegen, SDK, MCP tool, agent — is still *structurally incapable* of sending it to the endpoint that wipes overrides.
2. **No `/replace` declares a `409`.** So even a client that sends the header has no declared conflict response to handle.
3. **"Read the current version from a GET response" is now followable — for price-lists.** **`PriceListResponse` now carries a `version` field** (its field set: `id`, `name`, `currency`, `description`, `is_base`, `order_index`, `version`, `created_at`, `updated_at`, `links`), and price-list CRUD declares `X-Price-Lists-Version` to send it back in. **The gap that remains is the `/replace` endpoints themselves:** they replace price *overrides*, declare no version header and no `409`, so there is still no declared way to lock the very operation that does the damage.

   (`ProductResponse.pricing_version` — `integer`, default `0`, one of the server-computed fields from audit § **P0-2** — also exists. **Which value `X-Price-Lists-Version` wants is not documented**; do not guess, and prefer `PriceListResponse.version` where the header is actually declared.)

**The consequence, stated plainly:**

> **A concurrent `/replace` silently destroys another user's price overrides and returns `200 OK`.** No error. No warning. No conflict. The catalogue starts quoting numbers nobody set — and the only evidence is a customer noticing.

**Therefore:**

- **Never run a `/replace` without explicit human confirmation naming the tenant.** The `rattle-pricing-architect` agent refuses to, and that refusal has no override.
- **Prefer the granular `POST` / `PATCH` / `DELETE` path.** It touches one row. `/replace` touches all of them. The bulk endpoint saves requests and risks the catalogue; unless you are genuinely installing a complete, authoritative set, it is the wrong tool.
- **Send `X-Price-Lists-Version` if you can establish a value**, and handle `409` even though none is declared — the `X-Constraints-Version` sibling *does* return one at runtime, with `Version conflict:` in the `detail` (`rattle-apply-config` § 6). Retry once.
- **Respect the documented rate limit:** **`Price override replace | 30/minute`**, independent of plan. The current spec now declares **`Retry-After`** and **`X-RateLimit-Limit` / `-Remaining` / `-Reset`** on `429` responses (audit § **P3-3**, resolved) — **honour `Retry-After` when present**, and fall back to exponential backoff otherwise.
- **The area `/replace` body declares no `maxItems`** while the option and product bodies cap at 500. Do not read that as "unlimited" — read it as "unspecified", and stay under 500.

---

## 5 · Checklist before any pricing write

1. **Is there an explicit option to price?** If the standard variant is implicit, **stop** — `rattle-configurator`, the `#1 rule`. No override fixes a missing option.
2. **Does the base price list exist, with the right currency?** `GET /price-lists`. If it is empty, route to `rattle-onboarding`. **Never send `currency` on a product** (P2-4).
3. **Is this a catalogue price or a deal price?** A customer-specific discount belongs on the quote (`PATCH /quotes/{id}`, `rattle-crm-quotes`), **not** in a price list. A price list is shared; a deal is not.
4. **Is one mechanism enough?** If yes, use one — and the precedence question never arises. If no, **you must measure** (§ 3) before you write.
5. **Am I about to `/replace`?** Then a human types the tenant name first. Every time. (§ 4)
6. **Is the money a decimal string?** `"1250.00"`, never `1250.0`. Parse to `Decimal`, never to `float` (P0-5).
7. **Is this an inline-schema endpoint?** The **area** override and the **advanced price** bodies do **not** set `additionalProperties: false` — a typo'd field is swallowed with a `200`. **Read it back and diff it** (P0-10 class).
8. **Did I verify through `/calculate`?** A `201` proves a row exists. **Only `price_snapshot` proves a price.** The silent no-op (§ 3.6, the `"100.00"` row) is caught by nothing else.
