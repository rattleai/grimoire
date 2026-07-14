---
description: Design, fix or audit the pricing layer of a Rattle tenant — price lists, option/area/product price-overrides, conditional advanced prices, and pricing presets. Leads with the honest part: Rattle documents no pricing precedence anywhere, so this command never invents one. It determines the resolution order empirically against POST /configurations/calculate in a TEST tenant, or states plainly that it is unknown. Refuses to run a bulk /replace without a human naming the tenant — the OCC header is undeclared and a concurrent replace silently destroys overrides with a 200 OK.
argument-hint: <tenant name> [product, option, or price list]
---

# /rattle-price

Take the tenant the user names (`$ARGUMENTS`) and make the **number** right — price lists, price overrides, conditional advanced prices, product-level presets. This is the layer directly on the money path: `rattle-configurator` decides what the customer can buy, `rattle-bom-builder` what it is made of, `rattle-crm-quotes` who is billed. **Nothing else in this bundle owns what it costs.**

**37 operations across six families**, and the single largest stated unknown in the bundle. Read step 2 before anything else.

## Workflow

1. **Load context** — Read `skills/rattle-pricing/SKILL.md` and both reference files: `references/price-resolution.md` (before stacking two mechanisms, or when a price came back wrong) and `references/advanced-prices.md` (before pricing one option conditionally on another). Also load `skills/rattle-configurator/SKILL.md` — **an option that does not exist cannot be priced**, and an implicit standard variant has no price at all. Read `memory/<tenant>/profile.md`: it carries the base currency, the article-number key, the numbered-option unit, and — if it was ever measured — the observed pricing resolution order and the tenant's preset vocabulary.

2. **Which price wins? Say the true thing.** Five mechanisms can set the price of one option: `Option.price`, the option area-config `price`, an option price-override (keyed on the **triple** option/area/price_list), an advanced price (conditional on another option), and — for the area's and product's own base prices — area/product overrides. Plus pricing presets for product-level fees.

   **The spec never states which one wins.** Grepped: `precedence` → one hit, and it is about `usage_subclauses` boolean operators in the BOM. `resolution order`, `takes priority`, `falls back`, `most specific`, `overrides the`, `supersede` → **zero hits, all of them.**

   **Do not invent a precedence table.** Not "most specific wins", not "override beats base" — **any such table is a fabrication**, and from the outside it is indistinguishable from documentation. That is not hypothetical: `expand=areas.groups.options` shipped in a skill in this repo because it *seemed* right and the spec did not contradict it. It had never worked — it is a `400` (audit § **P1-7**). A hallucinated **price** precedence is worse, because it lands on an invoice.

   The gap is reported upstream — audit § **P0-8**: *"it will not error. It will return a price. A plausible one. Possibly the wrong one, on a quote that goes to a customer."* **It is not fixed.**

   **The cheapest answer is to not need one: do not stack two mechanisms on one option.** One mechanism, per option, per purpose. If you must stack, go to step 3.

3. **Determine the order empirically — in a TEST tenant, never production** — The API has an oracle: `POST /configurations/calculate` — *"Resolve constraints, **compute pricing**, and return a configuration state."*

   **But the oracle is a scalar.** It returns `price_snapshot` — **one decimal string, the grand total.** There is no itemisation, so you cannot ask which price won; you can only ask what the total is. The method is therefore **differential**: powers-of-ten prices (`100` base / `200` override / `400` advanced), one isolated option, decode the total.

   **Probe `GET /configurations/states/by-code/{code}/selections` first.** Its description promises *"each selected option enriched with … **price**"* — but its **declared schema is the same scalar state object, with no per-option prices.** (A P0-7-class defect **not yet in `docs/API_AUDIT.md` — report it.**) If the runtime honours the description, the whole problem collapses to one read. If not, run the differential. **Report which you got.**

   Full step-by-step, the baseline gate, the two-level worked conflict and the control run: `references/price-resolution.md` § 3. **Tear the experiment down afterwards**, and record the result in `memory/<tenant>/profile.md` **with its provenance** — "observed" and "documented" are different epistemic states and the next session must know which it is reading.

4. **Price lists — the currency lives here** — `POST /price-lists`: required `name`; `currency` (default `"EUR"`, maxLength 3), `description`, `is_base`. **`Product.currency` is accepted and discarded** — *"currency is derived from the company's base price list"* (audit § **P2-4**). **Never send it.** If `GET /price-lists` is empty, **stop and route to `/rattle-onboard`** — a tenant whose base list was created *after* its products has every price denominated wrong, with a `200 OK`. "Exactly one `is_base`" is a **convention, not enforced** — check.

5. **Overrides — the three families are NOT the same shape** — The option override is keyed on the **triple** `(option, area, price_list)` — `area_id` is **required**. The area and product overrides are keyed on a **pair**, and they override the **area's** and **product's own base price**, not an option's. The area body is **inline, `string`-only, and does not set `additionalProperties: false`** (audit § **P0-10** class) — a typo'd field is swallowed with a `201`, while the same typo `422`s on the option endpoint next door. **Read every area-override and advanced-price write back and diff it.**

   **A `409` is declared on the area, product and preset POSTs — and not on the option POST.** Treat `409` as "already exists → PATCH the price". **Do not assume the option triple is protected from duplicates; check the list yourself.** And note **every update body carries only the price**: the keying fields are **create-only**. To move an override to another price list, **DELETE and re-POST**.

6. **Advanced prices — the conditional nobody documented** — `POST /options/{optionId}/advanced-prices`, **required `condition_option_id` + `advanced_price`**. There is **no named schema** — the body is inline — and no description beyond *"Create an advanced price"*. `condition_option_id` being required *is* the feature:

   > **An advanced price is the price of this option WHEN another option is also selected.** *"The premium paint costs 800 — but 500 if the customer also takes the premium trim."*

   It is a genuinely powerful CPQ primitive and it is entirely undocumented upstream (audit § **P0-9**: *"a conditional-price engine with no schema, no description, and no name … you have built a feature nobody can use."*). **What two matching advanced prices do, and what omitting `area_id` / `price_list_id` means, is unknown** — say so, don't guess. `references/advanced-prices.md`.

7. **Pricing presets — read the vocabulary, never invent one** — `POST /products/{productId}/pricing-presets`: required `key`, `label`, `category`, `amount_type`. **`category` and `amount_type` are free strings (maxLength 50) with no enum** — the same disease as quote `status` (audit § **P2-1b**). The spec's *example* uses `"surcharge"` / `"fixed"`; that is an **example, not a vocabulary**. **`GET /products/{id}/pricing-presets` across the catalogue, collect the distinct values, use only those. If the one you need is absent, ASK THE USER.**

8. **`/replace` is a bulk atomic wipe — and it is the dangerous one** — *"Delete all existing overrides and replace with the provided set."* `info.description` says price-list bulk-replace uses **`X-Price-Lists-Version`** for optimistic locking — but **the spec declares zero header parameters** across all 463 operations and **no `409` on any `/replace`** (audit § **P0-1**). Worse: the prose says *"read the current version from a GET response"* and **`PriceListResponse` has no version field at all.**

   > **A concurrent `/replace` silently destroys another user's overrides with a `200 OK`.**

   **Never run one without explicit human confirmation naming the tenant.** Prefer the granular POST/PATCH/DELETE path — it touches one row; `/replace` touches all of them. Documented rate limit: **`Price override replace | 30/minute`**. No `Retry-After` is declared anywhere (audit § **P3-3**) — back off exponentially.

9. **Verify every write through `/calculate`** — **A `201` proves a row exists. It does not prove a price.** An override keyed against the wrong `area_id` or `price_list_id` returns `201`, lists happily on the `GET`, and **changes nothing** — a silent no-op that only the calculator reveals. Read every price back.

   **Never do float arithmetic on money** (audit § **P0-5**): `override_price` is `number|string` on the request and `string` on the response; the area body takes `string` only; analytics prices are **floats**; `part_cost` is an **integer**. Decimal-as-string end to end — send `"1250.00"`, never `1250.0`.

10. **Record what was learned** — The measured resolution order, the tenant's preset vocabulary, the base currency. `memory/<tenant>/profile.md` via `rattle-tenant-memory` — **explicit-write only**: show the file and get consent. **Record the provenance**, always: a measurement is not a contract, and Rattle may change it without notice.

## Confirmation discipline

Every write pauses. Restate the tenant, the mechanism, the natural key it is keyed on, and the exact request body — with money as a **decimal string** — then ask the user to **type the tenant name** to confirm. A generic "yes" is not consent.

**One operation gets its own hard gate: `/replace`.** It is a bulk atomic delete-and-reinstall whose concurrency header is undeclared. It is refused outright unless a human names the tenant in this session. If you cannot reach a human, **stop and report the planned calls** — an unapplied plan is recoverable; a wiped price list is not.

## Delegation

Delegate the run to the `rattle-pricing-architect` subagent with the tenant name. It preloads `rattle-pricing`, `rattle-configurator`, `rattle-api`, `rattle-crm-quotes` and `rattle-tenant-memory`, holds the confirmation gate, **refuses to state a precedence it has not measured**, **refuses to invent a preset `category` or `amount_type`**, verifies every price through `/calculate`, and **refuses to run a `/replace` against any tenant without explicit confirmation naming it.**

$ARGUMENTS
