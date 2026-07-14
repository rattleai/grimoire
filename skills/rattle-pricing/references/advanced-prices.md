# Advanced prices — the conditional price nobody documented

**Five operations. No named schema. No field descriptions. A summary that reads, in full, *"Create an advanced price"*.**

It is the only mechanism in Rattle that prices an option **relative to the rest of the configuration** — and it is, by a wide margin, the least documented feature on the money path. This file is the documentation.

---

## 1 · The surface

```
GET    /api/v1/options/{optionId}/advanced-prices              200
POST   /api/v1/options/{optionId}/advanced-prices              201
PUT    /api/v1/options/{optionId}/advanced-prices/{priceId}    200
PATCH  /api/v1/options/{optionId}/advanced-prices/{priceId}    200
DELETE /api/v1/options/{optionId}/advanced-prices/{priceId}    204
```

The **only** prose Rattle provides about any of them, in its entirety:

> **`GET`** — *"List advanced prices — List **condition-based price overrides** for an option. **Not paginated.**"*

That is the whole documentation. The `POST` has a summary (*"Create an advanced price"*) and **no description**. The `PUT`, `PATCH` and `DELETE` have summaries and no descriptions. There is **no named schema in `components`** — `AdvancedPriceCreateRequest` **does not exist**. The request bodies are **inline**, so a code generator emits an untyped `dict` and an agent reading the spec sees a feature with no explanation attached.

**Scope:** `prices:write` to create, `prices:read` to list.

---

## 2 · The schema, verbatim

Copied byte-for-byte out of `docs/openapi.json`. `POST /api/v1/options/{optionId}/advanced-prices` → `requestBody.content["application/json"].schema`:

```json
{
  "properties": {
    "advanced_price":      {"type": "string"},
    "area_id":             {"type": "integer"},
    "condition_option_id": {"type": "integer"},
    "price_list_id":       {"type": "integer"}
  },
  "required": ["condition_option_id", "advanced_price"],
  "type": "object"
}
```

Four fields. Two required. **No `additionalProperties: false`** — see § 6.

The update bodies are narrower still:

```jsonc
// PUT  /options/{optionId}/advanced-prices/{priceId}
{ "properties": {"advanced_price": {"type": "string"}}, "required": ["advanced_price"], "type": "object" }

// PATCH /options/{optionId}/advanced-prices/{priceId}
{ "properties": {"advanced_price": {"type": "string"}}, "type": "object" }
```

Two things follow, and both matter:

- **Only the price is updatable.** `condition_option_id`, `area_id` and `price_list_id` are **create-only**. You cannot re-point an advanced price at a different condition option. `PATCH` will not move it and **will not complain** — the field is silently dropped (§ 6). **DELETE and re-POST.**
- **`PUT` requires `advanced_price`; `PATCH` does not.** This is the *only* place in the pricing surface where the two verbs genuinely differ (contrast audit § **P0-3**: `PUT` and `PATCH` are byte-identical aliases on 37 of 39 paths). A `PATCH` with an empty body `{}` is schema-valid and does nothing.

---

## 3 · What `condition_option_id` means

**It is required. That single fact is the entire feature.**

An advanced price cannot exist without naming *another* option. So an advanced price is not "another override" — it is a fundamentally different kind of thing:

> ### An advanced price is the price of **this** option **when another option is also selected**.

The `GET` description confirms the reading in the API's own words: *"**condition-based** price overrides for an option."*

| Field | Meaning | Required |
|---|---|---|
| `{optionId}` (path) | **The option being priced.** The one whose cost changes. | ✅ (path) |
| `condition_option_id` | **The option whose selection triggers the price.** A *different* option — typically in a *different* group. | ✅ |
| `advanced_price` | The price `{optionId}` takes **when the condition holds**. A decimal **string**. | ✅ |
| `area_id` | Optional narrowing. Presumably scopes the rule to one area. | ❌ |
| `price_list_id` | Optional narrowing. Presumably scopes the rule to one price list. | ❌ |

**"Presumably" is doing real work in those last two rows, and it is deliberate.** The spec says nothing about what omitting them means (§ 7).

---

## 4 · Why this is a genuinely powerful CPQ feature

Every configurator eventually meets a price that is **not a property of one option**. The classic cases:

- **Bundle pricing.** "The premium paint is 800 on its own, but 500 with the premium trim."
- **Shared cost.** Two options need the same reinforced frame. Whichever is chosen alone pays for it; taken together, it is paid once.
- **Cannibalised labour.** Two options are installed in the same operation. The second one's fitting cost largely disappears.
- **Technical dependency discount.** An option is cheaper when the machine already carries the controller it needs.

**Without a conditional price, every one of these forces a bad modelling choice** — usually a combinatorial explosion of duplicate options ("Premium paint", "Premium paint with trim") that violates `reuse-over-duplicate`, doubles the BOM surface, and multiplies every constraint you then have to write to keep them mutually exclusive.

`advanced_prices` solves it in one row. **It deserves to be the best-documented field in the pricing surface. It is the worst.**

---

## 5 · Worked examples

All synthetic — the `Widget Pro` / `acme` universe. Ids are placeholders.

### 5.1 The bundle discount

> *"The premium paint costs 800. If the customer also takes the premium trim, the paint costs 500."*

```
Group "Paint"  is_multi: false
  Option "Standard paint"   (id 310)  price "0.00"    recommended
  Option "Premium paint"    (id 311)  price "800.00"          ← the option being priced
Group "Trim"   is_multi: false
  Option "Standard trim"    (id 314)  price "0.00"    recommended
  Option "Premium trim"     (id 315)  price "1200.00"         ← the condition option
```

```json
POST /api/v1/options/311/advanced-prices
{"condition_option_id": 315, "advanced_price": "500.00"}
```

Read it as: **"Option 311 costs 500.00 when option 315 is selected."**

Note that both groups obey the `#1 rule` — the standard variant is an explicit option at `price: "0.00"`, not an implicit baseline. **The conditional price rides on top of a correct configuration; it does not rescue a broken one.**

### 5.2 Scoped to one price list

> *"The bundle discount is a partner-tier perk. Retail customers pay full price."*

```json
POST /api/v1/options/311/advanced-prices
{"condition_option_id": 315, "advanced_price": "500.00", "price_list_id": 4}
```

The rule now names the partner list. **Whether the retail list therefore falls back to `Option.price`, or to an ordinary price-override, or to something else — that is the precedence question, and it is not documented.** See `price-resolution.md` § 2.

### 5.3 Scoped to one area

> *"On the compact chassis the two are fitted together and the labour is shared. On the heavy chassis they are not."*

```json
POST /api/v1/options/311/advanced-prices
{"condition_option_id": 315, "advanced_price": "500.00", "area_id": 88}
```

### 5.4 What it is NOT

**Not a quantity rule.** `condition_option_id` tests **presence**, not amount. "The paint is cheaper when the customer orders more than 20 panels" is **not expressible** — the constraint DSL is presence-based only (audit § **P2-2**, *"the single largest class of missing configurator logic"*), and nothing in the advanced-price schema reads a number either. For amount-driven pricing, the mechanism is `price_scalings` on a **numbered** option — untyped (audit § **P1-4**) and a silent no-op if the option is not `is_numbered: true`.

**Not a discount field.** There is no percentage, no delta, no "minus". `advanced_price` is an **absolute price**, expressed as a decimal string. A "10% bundle discount" must be computed by you, in `Decimal`, and written as the resulting absolute number. **Never compute it in `float`** (audit § **P0-5**).

**Not symmetric.** `POST /options/311/advanced-prices {"condition_option_id": 315, …}` prices **311**, conditional on 315. It says **nothing** about the price of 315. If the trim should also get cheaper when the paint is chosen, that is a **second row**, on option 315, conditioned on 311. Nothing links them, and nothing warns you that you wrote only one half of a rule you thought was symmetric.

---

## 6 · The inline-schema trap

**The advanced-price bodies do not set `additionalProperties: false`.**

Across the API, `additionalProperties: false` is set on **116 of 124 named request schemas** — so a typo'd field is a loud `422`, and an agent correctly *learns* that a bad field errors. Audit § **P0-10** names the 8 exceptions.

**These inline bodies are not in that list of 8** — they were not counted, because they are not named schemas at all. In the pricing surface the exceptions are:

| Endpoint | Body | `additionalProperties: false`? |
|---|---|---|
| `POST /options/{id}/price-overrides` | `PriceOverrideCreateRequest` (named) | ✅ typo → `422` |
| `POST /products/{id}/price-overrides` | `ProductPriceOverrideCreateRequest` (named) | ✅ typo → `422` |
| `POST /products/{id}/pricing-presets` | `PricingPresetCreateRequest` (named) | ✅ typo → `422` |
| **`POST /options/{id}/advanced-prices`** | **inline** | ❌ **typo → `201`, field dropped** |
| **`POST /areas/{id}/price-overrides`** | **inline** | ❌ **typo → `201`, field dropped** |
| **`PUT /options/{id}/area-config`** | **inline** | ❌ **typo → `200`, field dropped** |

**Within one resource family, a typo'd field errors on one endpoint and is silently swallowed on the next.** The inconsistency is worse than either policy would be.

**The failure this produces, concretely:**

```json
POST /api/v1/options/311/advanced-prices
{"condition_option_id": 315, "advanced_price": "500.00", "price_list": 4}
                                                          ^^^^^^^^^^^^ typo — should be price_list_id
→ 201 Created
```

**The row exists. The `price_list` key was dropped. The rule is now unscoped** — and whatever unscoped means (§ 7), it is not what you asked for. Nothing errored.

**The only defence is to read it back.** `GET /options/{optionId}/advanced-prices` after every write, and **diff what you sent against what came back.** Then verify the *price* through `POST /configurations/calculate` — because a row that exists and a price that applies are two different facts (`price-resolution.md` § 3.6).

**Report this.** The inline pricing bodies extend audit § **P0-10**'s list of 8 *named* schemas and are not currently counted in `docs/API_AUDIT.md`.

> **The mechanism itself is now reported.** `docs/API_AUDIT.md` § **P0-9** — *"`advanced-prices` — a conditional-price engine with no schema, no description, and no name"* — carries the finding upstream: the schemas are inline, the description is `null`, and *"we worked out what it does by reading a required field name."* The **inline-body swallow** (§ 6 above) is a *separate* defect and is **not** yet in the audit.

---

## 7 · What is NOT known — and must not be guessed

Everything in §§ 1–6 is verified against `docs/openapi.json`. Everything below is **not answerable from the spec**. If a user asks, **say so** and offer to measure it (`price-resolution.md` § 3).

| Question | Status |
|---|---|
| **Does an advanced price beat an ordinary price-override?** | **UNKNOWN.** No precedence is documented anywhere in the spec. Measure it. Never assert it. |
| **What if TWO advanced prices on the same option both match** (two condition options both selected)? | **UNKNOWN.** Lowest? Highest? Last created? Summed? Nothing states it, and there is no `priority` or `order_index` field on the entity to break the tie with. **This is a real configuration in a multi-select group, and it is undefined.** |
| **What does omitting `area_id` mean?** | **UNKNOWN.** "Applies in every area" is the intuitive reading. "Applies in no area" is equally consistent with a schema that says nothing. Measure it. |
| **What does omitting `price_list_id` mean?** | **UNKNOWN.** Same. Note the option *price-override* makes `price_list_id` **required** — so the pricing surface is not consistent about whether an unscoped price is even a coherent thing. |
| **Does the condition option have to be in a different group?** | **UNKNOWN.** In a single-select group (`is_multi: false`) two options are mutually exclusive, so an advanced price conditioned on a sibling **could never fire**. The API almost certainly accepts it. **It would be a silent no-op.** Do not author one. |
| **Can `condition_option_id` point at an option on a different *product*?** | **UNKNOWN**, and it would be nonsensical. The schema is a bare `integer` with no stated referential integrity. Assume not; do not test it in production. |
| **Is `advanced_price` an absolute price or a delta?** | **Absolute** — inferred from the field name, the `string` money type shared with `override_price` / `Option.price`, and the absence of any sign or percentage field. **Labelled as inference.** Confirm it on the first `/calculate` of any new tenant: a delta and an absolute are trivially distinguishable at the total. |
| **Is there a `409` on duplicate `(option, condition_option, area, price_list)`?** | **No `409` is declared** on the advanced-price `POST`. The area, product and preset `POST`s all declare one. **Uniqueness is unverified — check the list yourself before creating.** |

**The discipline:** an unknown, stated, costs a sentence. An unknown, guessed, costs a wrong number on a customer's invoice — and it arrives with a `200 OK`, which is precisely why nobody catches it.

---

## 8 · The idempotent operation

```
ensure_advanced_price
  natural key : (option_id, condition_option_id, area_id, price_list_id)
  REST        : GET  /options/{optionId}/advanced-prices        (NOT paginated — returns all)
                POST /options/{optionId}/advanced-prices        → 201
                PATCH /options/{optionId}/advanced-prices/{id}  → only advanced_price is updatable
                DELETE …/{id}                                    → 204
```

1. **`GET` the list.** It is not paginated — the API says so outright — so one call returns everything.
2. **Match on the full quadruple** `(option_id, condition_option_id, area_id, price_list_id)`. **No `409` is declared**, so the API may well let you create a duplicate. **Do not rely on it to stop you.**
3. **Absent** → `POST`. **Present with a different price** → `PATCH` with `{"advanced_price": "…"}`. **Present and identical** → `noop`.
4. **Need to change the condition, the area or the price list?** → **`DELETE` and re-`POST`.** They are create-only, and `PATCH` drops them silently.
5. **Read it back and diff it** (§ 6 — inline body, no `additionalProperties: false`).
6. **Verify the price through `POST /configurations/calculate`**, selecting the option **and** the condition option. Then run the **control**: calculate again with the condition option **deselected**, and confirm the advanced price does **not** contribute. A rule that fires unconditionally is worse than no rule.

```json
{"type": "ensure_advanced_price",
 "name": "premium paint when premium trim",
 "action": "created",
 "id": 12,
 "keyed_on": {"option_id": 311, "condition_option_id": 315, "area_id": 88, "price_list_id": 4},
 "advanced_price": "500.00",
 "verified": {"with_condition": "500.00", "without_condition": "800.00", "verdict": "pass"},
 "request_id": "req_..."}
```

**`verified` is not optional.** A `201` proves a row exists. Only the calculator proves a price — and only the control proves the *condition* works.
