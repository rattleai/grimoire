# Configurator settings — the 19 flags

`PATCH /api/v1/company/configurator-settings` (also `PUT`; `GET` to read).

These 19 flags govern the **entire customer-capture UX** of the configurator: whether a salesperson may create a new customer or must pick an existing one, what the search box searches, which customer fields are displayed, and which are mandatory before a configuration can be saved. A new tenant must decide them **deliberately** — the shipped defaults are a starting point, not a design.

---

## These flags — now in the OpenAPI spec, and worth reading anyway

For most of this feature's life the configurator settings were an **orphan**: the `PATCH`/`PUT` bodies were an inline `{"type": "object", "additionalProperties": true}` schema (no field names, no types), `ConfiguratorSettingsResponse` declared five properties (`custom_css`, `default_currency`, `require_login`, `show_prices`, `show_stock`) that were **disjoint from the flags that actually matter**, and a typo'd flag name was accepted with a `200 OK` and silently did nothing (audit § **P3-4**). This file exists because an agent could not discover the real flags from the spec.

**The current spec has fixed this.** The settings are now named schemas:

- **Write:** `PATCH` / `PUT /company/configurator-settings` take **`ConfiguratorSettingsUpdateRequest`**, which **sets `additionalProperties: false`** — so a **typo'd flag name now returns `422`**, not a silent `200`.
- **Read:** **`ConfiguratorSettingsResponse`** now declares the customer-gate flags themselves (`allow_*`, `require_customer_*`, `show_customer_*`, `customer_search_fields`, `start_search_digits`, …). The five old, disjoint properties are gone.

Two things still hold, so keep the discipline below:

- **Read the settings back after every write.** The schema now catches an unknown *key*, but it cannot catch a *wrong value* (a flag set `true` where you meant `false`), and this is company-wide UI behaviour — verify it landed.
- **The enumeration below is still the useful part.** The spec now lists the field names and types; it still does not tell you what each flag *does to the salesperson's screen*, which combinations trip each other up, or what a sane default is. That is what the table gives you.

---

## The one invariant that matters

> **`require_X: true` with `show_X: false` is unsatisfiable.** The field is mandatory and never displayed. The salesperson cannot fill it in, so the configuration can never be saved.

Nothing in the API enforces this — the body has no schema, so there is no cross-field validation. **You will get a `200 OK` and a configurator that is impossible to complete.** Check every pair before you PATCH:

```
for each field F in {company_contact_person, customer_address, customer_contact_person,
                     customer_email, customer_id, customer_organization, customer_phone}:
    assert not (require_F and not show_F)
```

Seven `show_*` flags, eight `require_*` flags. Seven of the eight pair up. The odd one out is `require_customer_info` — see below.

---

## 1 · Customer selection mode (2 flags)

How a salesperson attaches a customer to a configuration. **At least one must be `true`,** or a configuration can never be attributed to anyone.

| Flag | Type | Recommended day-0 value | What it does | UX consequence |
|---|---|---|---|---|
| `allow_create_new_customer` | boolean | `true` | Salesperson may create a customer inline, from the configurator. | `false` → the customer must already exist in Rattle. Correct for a tenant whose customer master lives in the ERP and syncs in — it stops the configurator becoming a second, dirty customer database. Wrong for a tenant doing walk-up quoting: the salesperson hits a dead end mid-quote. |
| `allow_select_existing_customer` | boolean | `true` | Salesperson may search for and pick an existing customer. | `false` → every configuration creates a *new* customer record, even for a customer who bought last week. **Duplicate customers accumulate silently.** Only set `false` for a genuinely anonymous / one-shot flow. |

**Both `false` is a broken configurator.** Nothing in the API stops you setting it.

---

## 2 · Customer search behaviour (2 flags)

Only meaningful when `allow_select_existing_customer: true`.

| Flag | Type | Recommended day-0 value | What it does | UX consequence |
|---|---|---|---|---|
| `customer_search_fields` | array of strings | `["organization", "customer_id"]` | Which customer fields the search box matches against. Observed values on the live tenant: `"organization"`, `"customer_id"`. | Too narrow → the salesperson knows the company name but the box only searches the customer number, and they conclude the customer does not exist and create a duplicate. Too wide → slow, noisy results. Match it to **what the salesperson actually has in hand** when they start a quote. |
| `start_search_digits` | integer | `3` | Minimum characters typed before the search fires. | `0`–`1` → the search fires on every keystroke and returns most of the customer base; slow and useless. Too high (`5`+) → short organisation names and short customer numbers become **unfindable**, and the salesperson creates a duplicate. `3` is the usual balance. Set it against the *shortest real* customer identifier in the tenant's data, not against a round number. |

> **Not verified:** the full set of legal values for `customer_search_fields`. `"organization"` and `"customer_id"` were observed live. Other field names may or may not be accepted — and because the body is `additionalProperties: true` with no schema, **an unrecognised value will be accepted with a `200` and silently ignored.** Set it, then read it back and test the search.

---

## 3 · Which customer fields are shown (7 flags)

Each governs the visibility of one field in the customer-capture form. `false` = the field is not rendered at all.

| Flag | Type | Recommended day-0 value | What it does | UX consequence of `false` |
|---|---|---|---|---|
| `show_customer_organization` | boolean | `true` | The customer's company / organisation name. | Hidden. In B2B machinery this is the *primary* identifier of a customer — hiding it is almost always wrong. |
| `show_customer_id` | boolean | `true` | The customer number (the ERP join key). | Hidden → nothing links the quote back to the ERP customer master. If the tenant syncs quotes into an ERP, this must be shown. |
| `show_customer_contact_person` | boolean | `true` | The named person at the customer. | Hidden → the offer PDF has a company but no addressee. |
| `show_customer_email` | boolean | `true` | The customer's email. | Hidden → no way to send the offer from Rattle. |
| `show_customer_phone` | boolean | `true` | The customer's phone. | Hidden. Usually acceptable; sales teams that call before they email will disagree. |
| `show_customer_address` | boolean | `true` | The customer's postal address. | Hidden → the offer PDF has no delivery or invoice address. If any document template renders an address block, **the block renders empty.** |
| `show_company_contact_person` | boolean | `true` | The contact person **on the tenant's own side** (the salesperson / responsible person shown on the offer). Note: *company*, not *customer*. | Hidden → the offer does not say who at the tenant is responsible for it. |

> **The `company` vs `customer` distinction is load-bearing.** `show_company_contact_person` / `require_company_contact_person` are about **your own staff**; every other flag in this table is about **the buyer**. It is the easiest pair to misread, and the two are set independently.

---

## 4 · Which customer fields are mandatory (8 flags)

A `require_*` flag blocks the configuration from being saved until the field is filled.

**Never set `require_X: true` while `show_X: false`.** See "The one invariant that matters".

| Flag | Type | Recommended day-0 value | What it does | UX consequence of `true` |
|---|---|---|---|---|
| `require_customer_organization` | boolean | `true` | Organisation is mandatory. | Sound in B2B. In B2C or walk-up quoting it blocks every private buyer. |
| `require_customer_id` | boolean | `false` | Customer number is mandatory. | **The classic day-0 mistake.** `true` means a *brand-new* customer — who by definition has no customer number yet — cannot be quoted. Only set `true` when customers are created in the ERP first and never in Rattle (i.e. `allow_create_new_customer: false`). |
| `require_customer_contact_person` | boolean | `false` | The named person is mandatory. | Blocks quoting a company before you know who you are dealing with — common at the first-contact stage. |
| `require_customer_email` | boolean | `true` | Email is mandatory. | Sound if offers are sent from Rattle. Blocks phone-only quoting. |
| `require_customer_phone` | boolean | `false` | Phone is mandatory. | Rarely justified. Blocks a quote over an email-only lead. |
| `require_customer_address` | boolean | `false` | Postal address is mandatory. | Set `true` **only if** a document template renders an address block that must never be empty. Otherwise it blocks early-stage quoting, where the address genuinely is not known yet. |
| `require_company_contact_person` | boolean | `true` | The **tenant's own** responsible person is mandatory. | Cheap to satisfy (it is your own staff) and it keeps every offer attributable. A good default. |
| `require_customer_info` | boolean | `false` | **Semantics not fully verified — see below.** | Treat as an umbrella / master switch over the customer-info block. |

### `require_customer_info` — the one flag with no `show_` sibling

Seven of the eight `require_*` flags pair with a `show_*` flag. **`require_customer_info` does not.** There is no `show_customer_info`.

**What we know (fact):** the flag exists on the live tenant, in the same settings object, and its name is `require_customer_info`.

**What we do not know (stated rather than guessed):** whether it is (a) a **master switch** — "some customer information must be supplied at all" — that gates the individual `require_*` flags, (b) an independent requirement on a customer-info *section* of the form, or (c) a legacy flag. **This skill could not verify its runtime behaviour**, and the API offers no way to find out from the spec.

**Therefore:** leave it at whatever the tenant already has, or set it `false` and rely on the seven specific `require_*` flags, which have unambiguous semantics. If you do set it `true`, **test a full quote end-to-end before the tenant goes live** — the failure mode is a configuration that cannot be saved, and you want to find that in onboarding, not in front of a customer.

---

## Two worked profiles

### B2B machinery, ERP-driven customer master

Customers are created in the ERP and synced into Rattle. The configurator must never invent one.

```json
{
  "allow_create_new_customer": false,
  "allow_select_existing_customer": true,
  "customer_search_fields": ["organization", "customer_id"],
  "start_search_digits": 3,
  "show_customer_organization": true,   "require_customer_organization": true,
  "show_customer_id": true,             "require_customer_id": true,
  "show_customer_contact_person": true, "require_customer_contact_person": false,
  "show_customer_email": true,          "require_customer_email": true,
  "show_customer_phone": true,          "require_customer_phone": false,
  "show_customer_address": true,        "require_customer_address": true,
  "show_company_contact_person": true,  "require_company_contact_person": true,
  "require_customer_info": false
}
```

`require_customer_id: true` is safe **only because** `allow_create_new_customer` is `false` — every customer already has a number. Flip the first flag without the second and the configurator deadlocks on the first new customer.

### Walk-up / first-contact quoting

The salesperson is quoting a lead they met an hour ago and knows almost nothing about.

```json
{
  "allow_create_new_customer": true,
  "allow_select_existing_customer": true,
  "customer_search_fields": ["organization"],
  "start_search_digits": 3,
  "show_customer_organization": true,   "require_customer_organization": true,
  "show_customer_id": true,             "require_customer_id": false,
  "show_customer_contact_person": true, "require_customer_contact_person": false,
  "show_customer_email": true,          "require_customer_email": true,
  "show_customer_phone": true,          "require_customer_phone": false,
  "show_customer_address": true,        "require_customer_address": false,
  "show_company_contact_person": true,  "require_company_contact_person": true,
  "require_customer_info": false
}
```

Everything is *shown* so it can be captured when known; almost nothing is *required*, so a quote is never blocked. `allow_select_existing_customer` stays `true` — that is the only thing preventing duplicate customers.

---

## Applying them

Idempotent, like every other onboarding write:

1. `GET /api/v1/company/configurator-settings` — read current state.
2. Diff against the target.
3. `PATCH` **only the flags that differ**.
4. **`GET` again and verify.** The body accepts unknown fields with a `200`; this read-back is your only validation.

```bash
curl -s -X PATCH -H "Authorization: Bearer $RATTLE_API_KEY" \
     -H "User-Agent: grimoire/1.0" -H "Content-Type: application/json" \
     -d '{"allow_create_new_customer": true, "start_search_digits": 3}' \
     "https://www.rattleapp.de/api/v1/company/configurator-settings"

curl -s -H "Authorization: Bearer $RATTLE_API_KEY" -H "User-Agent: grimoire/1.0" \
     "https://www.rattleapp.de/api/v1/company/configurator-settings"   # verify
```

Record the chosen profile in `memory/<tenant>/profile.md` — the flags are not derivable from the catalogue, so a later session has no other way to know what was intended.
