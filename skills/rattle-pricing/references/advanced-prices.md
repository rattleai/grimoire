# Advanced prices — the conditional price nobody documented

**Four operations. For most of this feature's life: no named schema, no field descriptions, and a `POST` summary that read, in full, *"Create an advanced price"*.** The current spec has caught up on the worst of it — the request bodies are now named, described schemas that reject unknown fields, and the precedence rule against an option price-override is finally stated. This file records both: what the spec now settles, and what it still does not.

It is the only mechanism in Rattle that prices an option **relative to the rest of the configuration** — and it was, for a long time, by a wide margin the least documented feature on the money path. This file is the documentation.

---

## 1 · The surface

```
GET    /api/v1/options/{optionId}/advanced-prices              200
POST   /api/v1/options/{optionId}/advanced-prices              201
PUT    /api/v1/options/{optionId}/advanced-prices/{priceId}    200
DELETE /api/v1/options/{optionId}/advanced-prices/{priceId}    204
```

**The redundant `PATCH` is gone.** Earlier revisions of the spec carried both `PUT` and `PATCH` on `/{priceId}`; the current spec keeps only `PUT`. Update is one verb now.

The spec now describes the mechanic. `GET`, `POST` and `PUT` each carry a description — *"Cross-option conditional pricing: set what this option costs **when** another option (`condition_option_id`) is also selected, optionally scoped to an area and/or price list. An advanced price outranks an option price-override during pricing resolution."* Only `DELETE` has no description. The request bodies are **named schemas** — `AdvancedPriceCreateRequest`, `AdvancedPriceUpdateRequest` — with per-field descriptions, so a code generator emits a typed model rather than an untyped `dict`.

**Scope:** `prices:write` to create, `prices:read` to list.

---

## 2 · The schema, verbatim

Copied out of `docs/openapi.json`. `POST /api/v1/options/{optionId}/advanced-prices` → `AdvancedPriceCreateRequest`:

```json
{
  "additionalProperties": false,
  "required": ["condition_option_id", "advanced_price"],
  "type": "object",
  "properties": {
    "advanced_price":      {"type": "string", "pattern": "^-?\\d+(\\.\\d+)?$"},
    "condition_option_id": {"type": "integer"},
    "area_id":             {"type": "integer"},
    "price_list_id":       {"type": "integer"}
  }
}
```

Four fields. Two required. **`additionalProperties: false` is now set** — a typo'd field is a loud `422`, not a silently-swallowed `201` (this is the fix to the old § 6 trap; see § 6 for what was NOT fixed). `advanced_price` carries a decimal `pattern` — note the leading `-?`: a **negative** advanced price is schema-valid.

The update body, `AdvancedPriceUpdateRequest` on `PUT /options/{optionId}/advanced-prices/{priceId}`:

```json
{
  "additionalProperties": false,
  "required": ["advanced_price"],
  "type": "object",
  "properties": {
    "advanced_price":      {"type": "string", "pattern": "^-?\\d+(\\.\\d+)?$"},
    "area_id":             {"type": ["integer", "null"]},
    "price_list_id":       {"type": ["integer", "null"]},
    "condition_option_id": {"type": "integer", "readOnly": true},
    "option_id":           {"type": "integer", "readOnly": true},
    "id":                  {"type": "integer", "readOnly": true}
  }
}
```

Two things follow, and both matter:

- **The scoping IS updatable now; the condition is not.** `PUT` accepts `area_id` and `price_list_id` (both nullable — send `null` to widen to "all"). Only `condition_option_id` is create-only (`readOnly`, alongside `id` and `option_id`). So to **re-scope** an advanced price to a different area or price list, `PUT` it. To **re-point** it at a different condition option, you still **DELETE and re-POST** — `PUT` will reject `condition_option_id` as read-only.
- **`PUT` requires `advanced_price`.** Even a scope-only change must resend the current price. (There is no `PATCH` to send a partial body — see § 1.)

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
| `area_id` | Optional narrowing. Restricts the rule to one area; `null`/omitted = all areas. | ❌ |
| `price_list_id` | Optional narrowing. Restricts the rule to one price list; `null`/omitted = all lists. | ❌ |

The last two rows are now **documented**, not inferred: the schema descriptions state *"omit for all areas"* / *"omit for all"* and the create-schema description says *"`null` = applies to all"* (§ 7 tracks what changed).

---

## 4 · Why this is a genuinely powerful CPQ feature

Every configurator eventually meets a price that is **not a property of one option**. The classic cases:

- **Bundle pricing.** "The premium paint is 800 on its own, but 500 with the premium trim."
- **Shared cost.** Two options need the same reinforced frame. Whichever is chosen alone pays for it; taken together, it is paid once.
- **Cannibalised labour.** Two options are installed in the same operation. The second one's fitting cost largely disappears.
- **Technical dependency discount.** An option is cheaper when the machine already carries the controller it needs.

**Without a conditional price, every one of these forces a bad modelling choice** — usually a combinatorial explosion of duplicate options ("Premium paint", "Premium paint with trim") that violates `reuse-over-duplicate`, doubles the BOM surface, and multiplies every constraint you then have to write to keep them mutually exclusive.

`advanced_prices` solves it in one row.

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

The rule now names the partner list. On the partner list the advanced price applies and **outranks an option price-override** (now documented — § 7). On the **retail** list this scoped rule does not apply, so option 311 falls back to whatever prices it there — its `Option.price`, or a retail price-override. **Which of those wins on the retail list is the ordinary resolution question** (`price-resolution.md` § 2); the advanced-price-vs-override precedence the spec documents does not settle it, because here no advanced price is in play on the retail list at all.

### 5.3 Scoped to one area

> *"On the compact chassis the two are fitted together and the labour is shared. On the heavy chassis they are not."*

```json
POST /api/v1/options/311/advanced-prices
{"condition_option_id": 315, "advanced_price": "500.00", "area_id": 88}
```

### 5.4 What it is NOT

**Not a quantity rule.** `condition_option_id` tests **presence**, not amount. "The paint is cheaper when the customer orders more than 20 panels" is **not expressible** — the constraint DSL is presence-based only (audit § **P2-2**, *"the single largest class of missing configurator logic"*), and nothing in the advanced-price schema reads a number either. For amount-driven pricing, the mechanism is `price_scalings` on a **numbered** option — untyped (audit § **P1-4**) and a silent no-op if the option is not `is_numbered: true`.

**Not a discount field.** There is no percentage, no delta, no "minus". `advanced_price` is an **absolute price**, expressed as a decimal string — the schema description says outright *"this option costs `advanced_price` when the condition holds"*. A "10% bundle discount" must be computed by you, in `Decimal`, and written as the resulting absolute number. **Never compute it in `float`** (audit § **P0-5**). (The `pattern` does permit a leading `-`, so a negative absolute price is accepted at the schema level — but that is a strange thing to want; confirm the total on `/calculate`.)

**Not symmetric.** `POST /options/311/advanced-prices {"condition_option_id": 315, …}` prices **311**, conditional on 315. It says **nothing** about the price of 315. If the trim should also get cheaper when the paint is chosen, that is a **second row**, on option 315, conditioned on 311. Nothing links them, and nothing warns you that you wrote only one half of a rule you thought was symmetric.

---

## 6 · The inline-schema trap — fixed here, still live next door

**The advanced-price bodies now set `additionalProperties: false`.** A typo'd field on a `POST` or `PUT` to `/advanced-prices` is a loud `422`. The swallow-trap this section used to warn about **no longer applies to advanced prices.**

It has **not** been fixed for its neighbours. Across the API, `additionalProperties: false` is set on nearly every *named* request schema — so a typo'd field is a loud `422`. Two pricing bodies are still **inline** and still omit it:

| Endpoint | Body | `additionalProperties: false`? |
|---|---|---|
| `POST /options/{optionId}/price-overrides` | `PriceOverrideCreateRequest` (named) | ✅ typo → `422` |
| `POST /products/{productId}/price-overrides` | `ProductPriceOverrideCreateRequest` (named) | ✅ typo → `422` |
| `POST /products/{productId}/pricing-presets` | `PricingPresetCreateRequest` (named) | ✅ typo → `422` |
| `POST /options/{optionId}/advanced-prices` | **`AdvancedPriceCreateRequest`** (named) | ✅ **now typo → `422`** |
| **`POST /areas/{areaId}/price-overrides`** | **inline** | ❌ **typo → `201`, field dropped** |
| **`PUT /options/{optionId}/area-config`** | **inline** | ❌ **typo → `200`, field dropped** |

**The failure the two remaining inline bodies still produce, concretely** — an area price-override with a mistyped scope field:

```json
POST /api/v1/areas/88/price-overrides
{"override_price": "450.00", "price_list": 4}
                             ^^^^^^^^^^^ typo — should be price_list_id
→ 201 Created
```

**The row exists. The `price_list` key was dropped. The override is now unscoped** — and whatever unscoped means, it is not what you asked for. Nothing errored.

**The defence for the two inline endpoints is to read the write back** — `GET` the list after the write and **diff what you sent against what came back**. For advanced prices the schema now catches the typo for you, but you should still verify the *price* through `POST /configurations/calculate` — because a row that exists and a price that applies are two different facts (`price-resolution.md` § 3.6).

> **Provenance.** `docs/API_AUDIT.md` § **P0-9** recorded advanced-prices as *"a conditional-price engine with no schema, no description, and no name"*, and § **P0-10** flagged the inline bodies that swallow unknown fields. The current spec has **named and described** the advanced-price schemas and given them `additionalProperties: false` — so the P0-9 finding and the advanced-price half of P0-10 are **resolved upstream**. The **area price-override** and **option `area-config`** inline bodies (§ P0-10) are **not** fixed. Treat the audit doc as the point-in-time record it is; this file tracks the current spec.

---

## 7 · What the spec now settles — and what it still does not

Everything in §§ 1–6 is verified against `docs/openapi.json`. The table below separates what the current spec **now answers** from what remains **not answerable from the spec**. For the latter, if a user asks, **say so** and offer to measure it (`price-resolution.md` § 3).

| Question | Status |
|---|---|
| **Does an advanced price beat an ordinary option price-override?** | **DOCUMENTED.** The create/response schema descriptions and every operation description state it: *"an advanced price outranks **and replaces** an option price-override during pricing resolution."* Read as: when both would price the same option, the advanced price wins. (This does not order it against a *product* override, a pricing preset, or the base price — those remain unstated; see below.) |
| **What does omitting `area_id` mean?** | **DOCUMENTED.** *"omit for all areas"* / *"`null` = applies to all"*. Omitted or `null` ⇒ every area. |
| **What does omitting `price_list_id` mean?** | **DOCUMENTED.** Same: omitted or `null` ⇒ every price list. |
| **What if TWO advanced prices on the same option both match** (two condition options both selected)? | **UNKNOWN.** Lowest? Highest? Last created? Summed? Nothing states it, and there is no `priority` or `order_index` field on the entity to break the tie with. **This is a real configuration in a multi-select group, and it is undefined.** Measure it. |
| **How does an advanced price rank against a *product* price-override, a pricing preset, or the base price?** | **UNKNOWN.** Only the option-override relationship is documented. The full precedence across all five mechanisms is still not a table anywhere (`price-resolution.md` § 2). |
| **Does the condition option have to be in a different group?** | **UNSTATED.** In a single-select group (`is_multi: false`) two options are mutually exclusive, so an advanced price conditioned on a sibling **could never fire**. The API almost certainly accepts it. **It would be a silent no-op.** Do not author one. |
| **Can `condition_option_id` point at an option on a different *product*?** | **UNSTATED**, and it would be nonsensical. The schema is a bare `integer` with no stated referential integrity. Assume not; do not test it in production. |
| **Is `advanced_price` an absolute price or a delta?** | **Absolute** — now stated in the schema description (*"this option costs `advanced_price`"*), consistent with the `string` money type shared with `override_price` / `Option.price`. Confirm it on the first `/calculate` of any new tenant anyway. |
| **Is there a `409` on duplicate `(option, condition_option, area, price_list)`?** | **No `409` is declared** on the advanced-price `POST` (responses: `201/401/404/422/429`). The area, product and preset `POST`s all declare one. **Uniqueness is unverified — check the list yourself before creating.** |

**The discipline is unchanged:** an unknown, stated, costs a sentence. An unknown, guessed, costs a wrong number on a customer's invoice — and it arrives with a `200 OK`, which is precisely why nobody catches it.

---

## 8 · The idempotent operation

```
ensure_advanced_price
  natural key : (option_id, condition_option_id, area_id, price_list_id)
  REST        : GET  /options/{optionId}/advanced-prices        (NOT paginated — returns all)
                POST /options/{optionId}/advanced-prices        → 201
                PUT  /options/{optionId}/advanced-prices/{id}   → 200  (price + scoping; condition is read-only)
                DELETE …/{id}                                    → 204
```

1. **`GET` the list.** It is not paginated — the API says so outright — so one call returns everything.
2. **Match on the full quadruple** `(option_id, condition_option_id, area_id, price_list_id)`. **No `409` is declared**, so the API may well let you create a duplicate. **Do not rely on it to stop you.**
3. **Absent** → `POST`. **Present with a different price or scope** → `PUT` (resend `advanced_price`; adjust `area_id` / `price_list_id` as needed — both are updatable, `null` to widen). **Present and identical** → `noop`.
4. **Need to change the condition option?** → **`DELETE` and re-`POST`.** `condition_option_id` is `readOnly`; `PUT` will reject it. (Area and price-list scope no longer need this — `PUT` moves them.)
5. **Verify the price through `POST /configurations/calculate`**, selecting the option **and** the condition option. Then run the **control**: calculate again with the condition option **deselected**, and confirm the advanced price does **not** contribute. A rule that fires unconditionally is worse than no rule. (The create body now rejects unknown fields, so a scoping typo `422`s rather than silently dropping — but `/calculate` is still the only proof the price *applies*.)

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
