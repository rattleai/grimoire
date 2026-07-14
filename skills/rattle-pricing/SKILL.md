---
name: rattle-pricing
description: Use this skill whenever a number on a Rattle price has to move — price, pricing, Preis, price list, Preisliste, price override, Preisüberschreibung, advanced price, conditional price, pricing preset, surcharge, Aufschlag, Zuschlag, discount, Rabatt, currency, Währung, margin, volume, Staffel. Covers the 37 price-list / price-override / advanced-price / pricing-preset operations, and the five mechanisms that can each set the price of one option. Leads with the honest part - Rattle never states which mechanism wins. There is no precedence, resolution order or fallback anywhere in the spec, so this skill refuses to invent one and instead teaches you to determine the order empirically against POST /configurations/calculate in a TEST tenant, then record it in tenant memory. Carries the traps - /replace is a bulk atomic wipe whose OCC header is undeclared, price_scalings is untyped and silently no-ops on a non-numbered option, and money is encoded seven ways, so never do float arithmetic on it.
license: MIT
---

# Rattle pricing — the layer that decides the number

`rattle-configurator` decides **what** the customer can buy. `rattle-bom-builder` decides **what it is made of**. `rattle-crm-quotes` decides **who is billed**. Nothing in this bundle has, until now, owned **what it costs** — and it is the one number the customer definitely reads.

This skill covers **37 operations across six resource families**: price lists (8), option price-overrides (6), area price-overrides (6), product price-overrides (6), advanced prices (5), pricing presets (6). Scopes: `prices:read` / `prices:write`.

It is also the skill with the largest **stated unknown** in the bundle, and the way that unknown is handled is the point of the whole document. Read § "Which price wins?" before you write anything.

## When to use this skill

- The user says price, pricing, Preis, Preisliste, price override, Preisüberschreibung, advanced price, pricing preset, surcharge, Aufschlag, Zuschlag, Rabatt, currency, Währung, margin, Staffel — or asks why a configured product costs what it costs.
- A second price list is needed: a different currency, a partner tier, a regional list, a dated list.
- One option must cost something different **in one area**, **on one price list**, or **when another option is also selected**.
- A product needs a fee, a surcharge or a discount line that is not an option (assembly, freight, handling).
- A price came back **wrong** and nobody knows which of the five mechanisms produced it. That is § "Which price wins?" and it is the reason this skill exists.

**Do not use this skill to discount a quote.** A quote-level discount is `discount_amount` / `discount_percent` on `PATCH /quotes/{id}` — update-only, a second call, audit § **P3-2**. That is `rattle-crm-quotes`. This skill is the *catalogue* price; that one is the *deal* price. Putting a customer-specific deal into a price list contaminates the catalogue for everyone on that list.

**Do not use this skill to fix a wrong configuration.** If the standard variant has no explicit option, no price override can rescue it — the #1 rule in `rattle-configurator` comes first, always.

## The five mechanisms

Each of these can move the number. They are listed by scope, narrowest last.

| # | Mechanism | What it is | Keyed on | What it is for |
|---|---|---|---|---|
| **1** | **Base price** | `Option.price` (string, default `"0.00"`), `Area.price`, `Product.base_price`. The number on the entity itself. | the entity | The default. Everything else is a deviation from it. |
| **2** | **Price list** | `POST /price-lists` — required `name`; `currency` (default `"EUR"`, maxLength **3**), `description` (≤2000), `is_base` (default `false`). | `name` | **Not a price — an axis.** Every override below is scoped to one price list. **The currency lives here** and nowhere else. |
| **3** | **Price-override** | Three separate families. Replaces one entity's price **on one price list**. | option → **(option, area, price_list)**<br>area → (area, price_list)<br>product → (product, price_list) | Per-list, per-area pricing: partner tiers, regional lists, currency variants — without duplicating the option. |
| **4** | **Advanced price** | `POST /options/{optionId}/advanced-prices` — **required `condition_option_id` + `advanced_price`**. | **(option, condition_option, [area], [price_list])** | **A conditional price: this option costs X *when another option is also selected*.** Entirely undocumented upstream. See § below. |
| **5** | **Pricing preset** | `POST /products/{productId}/pricing-presets` — required `key`, `label`, `category`, `amount_type`. | **(product, `key`)** | Product-level fees, surcharges and discounts that are **not options**: assembly, freight, handling. `taxable`, `default_on`, `value`, `sort_index`. |

### Two more that also move the number — and are easy to miss

Neither is a "pricing" endpoint, so neither shows up when you go looking for one. Both change what the customer pays.

- **Option area-config `price`** — `PUT /options/{optionId}/area-config?area_id=<id>`, scope **`prices:write`**. An inline body carrying `price` (string), plus `option_description`, `option_key`, `recommended`, `is_numbered`, `number_*`. **This sets an option's price per area with no price list involved at all** — a *fourth* way to price one option, keyed on **(option, area)**. `DELETE …/area-config?area_id=<id>&field=price` clears just that column.

  > `area_id` is a **required query parameter on the GET**, and there is no list-all. Auditing every option's area prices is an **N × M loop** (audit § **P1-7**). Two undocumented expansions make it survivable: `GET /products/{id}?expand=price_overrides` and `?expand=pricing_presets` both work — the API's own `400` enumerates them — **but the spec claims `expand` accepts only `areas` and `gallery`.** Use them; know they are undeclared.

- **`price_scalings`** — on the option. Scales the price by a **numbered** option's selected amount. `OptionCreateRequest.price_scalings` is `{"additionalProperties": true}` — **completely untyped** (audit § **P1-4**), while its BOM twin `option_scalings` is the best-documented field in the spec. See § "Traps".

## Which price wins? Rattle does not say — and neither will this skill

**Five mechanisms can set the price of one option. The spec never states which one takes effect.**

This is not an oversight in the reading. It was checked directly against `docs/openapi.json`:

```
"precedence"        → 1 hit  — and it is about usage_subclauses boolean operators, in the BOM
"resolution order"  → 0 hits
"takes priority"    → 0 hits
"falls back"        → 0 hits
"most specific"     → 0 hits
"overrides the"     → 0 hits
"supersede" / "wins"→ 0 hits
```

**There is no documented pricing resolution order.** Not in a description, not in a schema, not in `info.description`.

So:

> **This skill does not have a precedence table, and it will not print one.**
>
> Not "most specific wins". Not "override beats base". Not "advanced price beats override". **Any such table would be a fabrication**, and it would be indistinguishable — from the outside — from a documented fact.

That is not a hypothetical failure mode. It is the exact one this repo already shipped: `expand=areas.groups.options` was written into a skill because it *seemed* right, the spec did not contradict it, and **it had never worked** — it is a `400` (audit § **P1-7**). The report's own conclusion: *"an undocumented feature and a hallucinated feature are indistinguishable from the outside."* A hallucinated **price** precedence is worse, because it lands on an invoice.

**What to do instead:**

1. **Never state a precedence as fact.** If a user asks "does the override beat the base price?", the answer is: *"Rattle does not document it. Here is how we find out in your tenant."*
2. **Determine it empirically** — § below. The API has an oracle: `POST /configurations/calculate` is **"Resolve constraints, compute pricing, and return a configuration state."** It is Rattle's own price computation, and it is a `POST` that persists nothing about your catalogue.
3. **Record what you observe** in `memory/<tenant>/profile.md`, with its provenance and its date.
4. **Avoid the question where you can.** The cheapest resolution order is the one you never have to know: **do not stack two mechanisms on the same option.** Pick one, per option, per purpose. A catalogue with no overlapping mechanisms has no precedence problem.

**Observed is not the same as specified.** An order you measure in one tenant, on one release, is exactly that. It is not a contract, Rattle may change it, and it must be re-verified. Say so, every time.

> **This gap is reported upstream: `docs/API_AUDIT.md` § P0-8** — *"Four mechanisms can set one option's price. The spec never says which wins."* Its verdict on why this one outranks every other silent-wrongness finding: *"Every other silent-wrongness finding in this report costs you a BOM line or a retry. **This one costs you money, on a document with your customer's signature on it.**"* The requested fix is one paragraph of `info.description` — plus a `price_breakdown` on the `/calculate` response, which would make pricing auditable. **Until that lands, this section stands.**

## Determining the resolution order in your tenant

**In a TEST tenant. Never in production.** This procedure deliberately writes a conflicting override and deliberately reads a wrong price. Doing it in a live catalogue means a customer can configure the machine mid-experiment and buy the wrong number.

### The oracle is a scalar — and that shapes the whole method

```
POST /api/v1/configurations/calculate     → 201  ConfigurationStateResponse
  required: product_id
  optional: selected_options {area_id: [option_id, …]}, option_amounts {option_id: int},
            price_list_id, enabled_areas, disabled_areas, wishlist_options,
            validate_config (default true)
```

It returns **`price_snapshot`** — and `price_snapshot` is **a single decimal string. The grand total.**

```json
{"data": {"config_code": "…", "config_hash": "…", "price_snapshot": "2485.00", "is_valid": true}}
```

**You cannot ask this API which price won. You can only ask it what the total is.** So the method is not "call `/calculate` and read the answer" — it is a **differential experiment**: make the candidate prices arithmetically distinguishable, isolate one option, and decode the total.

> **There is a second endpoint that would answer it directly — and its schema does not match its description.** `GET /configurations/states/by-code/{code}/selections` says: *"Returns each selected option enriched with group name, option name, **price**, quantity, and wishlist status."* Its **declared 200 schema is `ConfigurationStateResponse`** — the same scalar state object, with **no per-option array and no per-option price field.** The itemised breakdown is promised in prose and absent from the schema. (Same class as audit § **P0-7**; **this instance is not yet in `docs/API_AUDIT.md` — report it.**)
>
> **Probe it first anyway.** If the runtime really returns enriched per-option prices, the entire precedence problem collapses into one read, and this whole procedure is unnecessary. If it returns the scalar the schema declares, fall back to the differential method below. **Report which one you got.**

### The procedure

Use **powers of ten** for the candidate prices so that any total decodes to exactly one combination. Never use values that can sum to each other.

**Setup — synthetic, in a test tenant:**

```
Product  "Widget Pro"                    base_price "0.00"
Area     "Chassis"          (id A)       price "0.00"
Group    "Wheels"  is_multi: false
  Option "17 inch"  recommended, price "0.00"
  Option "19 inch"                       price "100.00"   ← Option.price          (mechanism 1)
Price list "TEST"  is_base: false, currency EUR            ← the axis             (mechanism 2)
```

**Step 0 — baseline.** Calculate with `19 inch` selected and `price_list_id` = TEST, before adding any override.

```json
POST /api/v1/configurations/calculate
{"product_id": <P>, "price_list_id": <TEST>, "selected_options": {"<A>": [<19_inch>]}}
→ price_snapshot "100.00"      the base price is live; the harness is sound
```

If this is not `100.00`, **stop.** Something else in the product is contributing and every later reading is contaminated. Zero it out first.

**Step 1 — add ONE mechanism. Re-calculate. Record the delta.** Add the option price-override, keyed on the triple:

```json
POST /api/v1/options/<19_inch>/price-overrides
{"area_id": <A>, "price_list_id": <TEST>, "override_price": "200.00"}

POST /api/v1/configurations/calculate   (identical body to step 0)
→ price_snapshot "200.00"  ⇒ the override REPLACED the base price
→ price_snapshot "300.00"  ⇒ the override was ADDED to the base price
→ price_snapshot "100.00"  ⇒ the override did NOT apply at all  ← the silent case; see below
```

**Three outcomes, three different systems.** "Replace" and "add" are both plausible designs and the spec picks neither. **And the third outcome is the dangerous one** — a `201 Created`, a row in the database, and no effect on the price.

**Step 2 — stack a SECOND mechanism on the same option. Re-calculate.** Now add the advanced price (mechanism 4), conditional on a second option, and select both:

```json
POST /api/v1/options/<19_inch>/advanced-prices
{"condition_option_id": <winter_pkg>, "advanced_price": "400.00",
 "area_id": <A>, "price_list_id": <TEST>}

POST /api/v1/configurations/calculate
{"product_id": <P>, "price_list_id": <TEST>,
 "selected_options": {"<A>": [<19_inch>, <winter_pkg>]}}
```

Decode the total against the powers you chose (`100` base / `200` override / `400` advanced). Any observed total maps to exactly one hypothesis — that is the whole reason for the powers.

**Step 3 — repeat, pairwise, for every pair you actually intend to use.** Do not extrapolate from one pair to the others. A system can replace in one pair and add in another; nothing forbids it, and nothing documents it.

**Step 4 — tear the test tenant back down.** `DELETE` every override you created. An abandoned experiment is an override nobody can explain six months later.

**Step 5 — record it.** `memory/<tenant>/profile.md`, `rattle-tenant-memory`, **explicit-write only** — show the file, get consent:

```markdown
## Pricing resolution (OBSERVED, not documented by Rattle — re-verify)
- **observed-on**: 2026-07-14, tenant `acme-test`
- **method**: differential POST /configurations/calculate; see rattle-pricing/references/price-resolution.md
- **option-override vs Option.price**: override REPLACES base   (100 → 200)
- **advanced-price vs option-override**: <what you measured>
- **caveat**: Rattle documents NO precedence. This is a measurement, not a contract.
  It may change without notice. Not verified for area/product overrides.
```

**Provenance is load-bearing.** "Observed" and "documented" are different epistemic states, and the next session must be able to tell which it is reading. Full step-by-step, plus a worked two-level conflict: **`references/price-resolution.md`**.

## Advanced prices — the undocumented conditional price

**The most powerful CPQ feature in the Rattle pricing surface, and the least documented anywhere.** Five operations. No named schema, no field descriptions, and a summary that reads, in its entirety, *"Create an advanced price"*. (Reported upstream: `docs/API_AUDIT.md` § **P0-9** — *"a conditional-price engine with no schema, no description, and no name … **You have built a feature nobody can use.**"*)

The request body is **inline** — `AdvancedPriceCreateRequest` **does not exist in `components`**. Verbatim from `docs/openapi.json`:

```json
{ "properties": {
    "advanced_price":      {"type": "string"},
    "area_id":             {"type": "integer"},
    "condition_option_id": {"type": "integer"},
    "price_list_id":       {"type": "integer"} },
  "required": ["condition_option_id", "advanced_price"] }
```

**`condition_option_id` is REQUIRED.** That single fact is the whole feature:

> **An advanced price is the price of *this* option **when another option is also selected**.** It is a cross-option conditional price — `GET /options/{optionId}/advanced-prices` calls them *"condition-based price overrides for an option"* — and it is the only mechanism in Rattle that prices an option **relative to the rest of the configuration**.

Synthetic example — the bundle discount that needs no discount field:

> *"The premium paint costs 800. But if the customer also takes the premium trim, the paint costs 500."*

```json
POST /api/v1/options/<premium_paint>/advanced-prices
{"condition_option_id": <premium_trim>, "advanced_price": "500.00"}
```

No coupon, no quote-level discount, no duplicated option. The configurator prices the bundle correctly on its own.

**What is NOT known, and must not be guessed:** what happens when **two** advanced prices on the same option both match (two condition options both selected); whether an advanced price with **no** `area_id` / `price_list_id` applies globally or not at all; and — again — **whether it beats an ordinary price-override.** None of it is documented. Measure it or say you do not know. Full treatment, worked examples, and the update asymmetry: **`references/advanced-prices.md`**.

## Traps

Every one of these returns a `2xx`. That is what makes them expensive.

| # | Trap | Consequence |
|---|---|---|
| **P0-1** | **`/replace` is a bulk atomic wipe and its OCC header is undeclared.** `POST …/price-overrides/replace` — *"Delete all existing overrides and replace with the provided set."* `info.description` says price-list bulk-replace uses **`X-Price-Lists-Version`** for optimistic locking. **The spec declares ZERO header parameters across all 463 operations**, and **no `409` on any `/replace`**. | **A concurrent `/replace` silently destroys another user's overrides with a `200 OK`.** No error, no warning, no conflict. Worse: the prose says *"read the current version from a GET response"* — **but `PriceListResponse` carries no version field at all.** The only candidate in the spec is `ProductResponse.pricing_version` (integer, one of the 13 read-only fields from § P0-2), and **that it is the value for this header is an inference, not documented.** Send the header if you can establish the value; **never batch a `/replace` you have not confirmed with a human.** Documented rate limit: **"Price override replace \| 30/minute"**. |
| **P1-4** | **`price_scalings` is `additionalProperties: true`** — untyped, while its BOM twin `option_scalings` is fully specified. | **A scaling keyed against a non-numbered option is a silent no-op** — `200 OK`, wrong price. The BOM side got a schema and a description; the *price* side got `any`. Set `is_numbered: true` on the option **first**, and verify the scaled price through `/calculate` — nothing else will tell you. |
| **P0-5** | **Money is encoded 7 ways across 76 fields.** `PriceOverrideCreateRequest.override_price` is `number\|string` on the **request** and `string` on the **response**. The **area** override's inline body accepts `string` **only**. `PricingPresetCreateRequest.value` is `number\|string`; the response is `string`. `OptionSelectionFactResponse.unit_price` / `total_price` are **floats**. `PartCreateRequest.part_cost` is an **integer**. | **Never do float arithmetic on money.** Decimal-as-string end to end; parse to `Decimal`, never to `float`; send `"1250.00"`, never `1250.0`. A float sum returns a plausible-but-wrong number with a `200 OK` on every call, and it lands on the customer's invoice. |
| **P2-4** | **`Product.currency` is accepted and ignored** — *"currency is derived from the company's base price list"*. | **Never send `currency` on a product.** The currency lives on the base price list (`rattle-onboarding` § "The ordering rule that bites"). A product created before the base price list exists is **already denominated wrong**, with a `200 OK`, and re-creating it is the only fix. |
| **P0-10** | **The area price-override and advanced-price bodies are INLINE and do not set `additionalProperties: false`.** The option and product override bodies are named schemas and **do**. | **In the same resource family, a typo'd field `422`s on one endpoint and is swallowed with a `200` on the next.** An agent that learned "a bad field errors" is wrong exactly here. **Read every area-override and advanced-price write back and diff it.** (This extends § P0-10's list of 8 *named* schemas; these **inline** bodies were not counted there — **report it.**) |
| — | **The keying fields are create-only.** Every update request in this surface carries **only the price**: `PriceOverrideUpdateRequest` = `{override_price}`. The advanced-price `PUT`/`PATCH` = `{advanced_price}`. | **You cannot re-point an override at a different area or price list.** `PATCH` will not move it and will not complain. **DELETE and re-POST.** (Note `PUT` *requires* `advanced_price` and `PATCH` does not — the only place the two verbs differ in this family.) |
| — | **A `409` is declared on three POSTs and not on the fourth.** Area price-override, product price-override and pricing-preset `POST` all declare `409`. **The option price-override `POST` does not.** | The 409s tell you the natural keys are **enforced unique** — (area, price_list), (product, price_list), (product, `key`). **For the option override triple, uniqueness is unknown**: either the spec omitted the `409`, or duplicates are permitted. **Treat a `409` as "already exists → read it and PATCH the price", and do not assume the option triple is protected.** Check before you create. |
| — | **`category` and `amount_type` on a pricing preset are free strings (maxLength 50) with no enum.** | **The vocabulary is undiscoverable** — same disease as quote `status` (audit § **P2-1b**). The spec's own *example* uses `category: "surcharge"`, `amount_type: "fixed"`, and the endpoint description says *"surcharges, discounts, fees"*. **That is an example and a prose hint, not a vocabulary.** **Read what the tenant already uses** — `GET /products/{id}/pricing-presets` across the catalogue, collect the distinct values — and if the one you need is absent, **ask the user.** Never invent a category. |

**Pagination.** Only `GET /price-lists/{priceListId}/overrides` declares `cursor` + `limit` (max 100). Every other pricing list endpoint declares **neither** (audit § **P1-8**) — and `GET /options/{id}/advanced-prices` states outright *"Not paginated."* A caller cannot tell "bounded" from "silently truncated". Prefer the price-list-scoped listing when you need completeness.

## Output contract

Same `applied` / `skipped` / `errors` shape as `rattle-apply-config`, `rattle-onboarding` and `rattle-crm-quotes`, plus the two things only a pricing run produces: the **resolution verdict** and the **mechanism map**.

```json
{
  "tenant": "acme",
  "priced_at": "2026-07-14T09:00:00+00:00",
  "preflight": {
    "price_lists": [{"id": 3, "name": "Standard", "currency": "EUR", "is_base": true}],
    "resolution_order": {
      "status": "unknown",
      "source": null,
      "note": "Rattle documents no pricing precedence. Not measured in this tenant. No mechanism was stacked, so no order is required."
    },
    "verdict": "one mechanism per option — precedence not engaged"
  },
  "applied": [
    {"type": "ensure_price_list", "name": "Partner EU", "action": "created", "id": 4, "request_id": "req_..."},
    {"type": "ensure_option_price_override", "name": "19 inch @ Chassis / Partner EU", "action": "created", "id": 77,
     "keyed_on": {"option_id": 302, "area_id": 88, "price_list_id": 4}, "override_price": "450.00", "request_id": "req_..."},
    {"type": "ensure_advanced_price", "name": "premium paint when premium trim", "action": "created", "id": 12,
     "keyed_on": {"option_id": 311, "condition_option_id": 315, "area_id": 88, "price_list_id": 4},
     "advanced_price": "500.00", "request_id": "req_..."},
    {"type": "ensure_pricing_preset", "name": "assembly_fee", "action": "updated", "id": 5,
     "keyed_on": {"product_id": 401, "key": "assembly_fee"},
     "category": "surcharge", "amount_type": "fixed", "value": "150.00", "request_id": "req_..."}
  ],
  "skipped": [
    {"type": "ensure_option_price_override", "name": "17 inch @ Chassis / Partner EU", "reason": "noop — already matches"}
  ],
  "verification": [
    {"check": "calculate", "product_id": 401, "price_list_id": 4,
     "selected_options": {"88": [302]}, "price_snapshot": "450.00",
     "expected": "450.00", "verdict": "pass"}
  ],
  "unknowns": [
    "Pricing resolution order is not documented by Rattle and was not measured in this tenant.",
    "Option price-override POST declares no 409 — uniqueness of (option, area, price_list) is unverified."
  ],
  "errors": []
}
```

**Every money value is a decimal string.** `resolution_order.status` is `"unknown"` unless it was **measured** in a test tenant, in which case `source` names the run and the date — **never an inference, never a default.** `verification` is not optional: **every pricing write is read back through `/calculate`**, because a `201` proves a row exists and proves nothing about the price.

**Pricing-tier operations.** Five `ensure_*` types, idempotent get-or-create by natural key, extending the grammar in `rattle-apply-config/references/operations-contract.md`:

| Operation | Natural key | REST |
|---|---|---|
| `ensure_price_list` | `name` | `GET /price-lists` (not paginated) → `POST /price-lists` / `PATCH /price-lists/{id}`. **Exactly one `is_base: true` — a convention, NOT enforced by the API.** |
| `ensure_option_price_override` | **(option_id, area_id, price_list_id)** | `GET /options/{id}/price-overrides` → `POST` / `PATCH …/{overrideId}`. **`PATCH` sets only `override_price`** — to move it, DELETE and re-POST. **No `409` declared: check for the existing row yourself.** |
| `ensure_area_price_override` · `ensure_product_price_override` | (area\|product, price_list_id) | `GET …/price-overrides` → `POST` (**`409` = already exists → PATCH the price**). **The area body is inline and swallows unknown fields — read it back.** |
| `ensure_advanced_price` | (option_id, condition_option_id, area_id, price_list_id) | `GET /options/{id}/advanced-prices` (**not paginated**) → `POST` / `PATCH …/{priceId}`. Inline body — **read it back.** |
| `ensure_pricing_preset` | **(product_id, `key`)** | `GET /products/{id}/pricing-presets` → `POST` (**`409` = exists**) / `PATCH …/{presetId}`. **Read the tenant's `category` / `amount_type` vocabulary first.** |

**One operation that is NOT `ensure_*`, because it is destructive and not idempotent:**

| Operation | Why it is different |
|---|---|
| `replace_price_overrides` | `POST …/price-overrides/replace`. **Deletes every existing override and installs the set you sent.** Its OCC header is undeclared (§ P0-1), so a concurrent replace **silently destroys** the other write with a `200 OK`. **Never emitted without an explicit human confirmation naming the tenant.** `maxItems` 500 on the option and product bodies; the **area** body declares **no `maxItems` at all**. |

## Handing off

```
rattle-onboarding      the base price list — day 0, BEFORE any product (P2-4)
  └→ rattle-configurator      explicit options for ALL variants — an option must exist to be priced
       └→ rattle-pricing      price lists, overrides, advanced prices, presets   ← you are here
            └→ rattle-apply-config     the idempotent ensure_* writes
            └→ rattle-bom-builder      option_scalings — price_scalings' fully-typed twin
            └→ rattle-crm-quotes       price_list_id is REQUIRED on every quote
            └→ rattle-tenant-memory    the measured resolution order + the preset vocabulary
```

- **Never invent a precedence.** It is the one rule in this skill that cannot be repaired after the fact, because the wrong number is already on the customer's invoice.
- **Never run a `/replace` without a human naming the tenant.** The OCC header is undeclared; a concurrent replace is a silent data loss.
- **Never do float arithmetic on money.** Decimal-as-string, end to end.
- **Never invent a preset `category` or `amount_type`.** Read the tenant's; if the one you need is absent, ask.
- **Verify every write through `/calculate`.** A `201` proves a row. Only `price_snapshot` proves a price.
- **Prefer not stacking mechanisms.** One mechanism per option per purpose. The precedence you never rely on is the one that cannot bite you.

## Reference files

| File | Use when |
|---|---|
| `references/price-resolution.md` | You are about to stack two mechanisms, or a price came back wrong — the four mechanisms in depth, the empirical `/calculate` procedure step by step, and a worked two-level conflict |
| `references/advanced-prices.md` | You are pricing an option **conditionally on another option** — the inline schema verbatim, what `condition_option_id` means, worked examples, and what remains unknown |

## Related skills

- `rattle-configurator` — the #1 rule and the data model. An option that does not exist cannot be priced; an implicit standard variant has no price at all.
- `rattle-onboarding` — where the base price list comes from, and why it must exist **before** the first product (`Product.currency` is accepted and discarded).
- `rattle-crm-quotes` — `price_list_id` is required on every quote. Deal discounts live there, not in a price list.
- `rattle-bom-builder` — `option_scalings`, the fully-documented twin of `price_scalings`. Read it to see what the price side should have looked like.
- `rattle-apply-config` — the idempotent `ensure_*` grammar this skill's pricing tier extends.
- `rattle-tenant-memory` — where a **measured** resolution order and the tenant's preset vocabulary are recorded, with their provenance.
- `rattle-api` — REST mechanics: auth, cursor pagination, RFC 9457 problem details, and the OCC headers the spec does not declare.
