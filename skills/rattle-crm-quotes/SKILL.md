---
name: rattle-crm-quotes
description: Use this skill whenever a Rattle configuration has to turn into money — quote, quotation, Angebot, offer, customer, Kunde, contact, opportunity, pipeline, CRM, line item, Position, discount, Rabatt, revise, revision, quote status, sales, Vertrieb, quote-to-cash. Covers the 49 Customers / Opportunities / Quotes / Configurations operations and the 11-step funnel: get-or-create the customer on their ERP customer_id, contacts, opportunity, finalize the configuration BEFORE quoting it, POST the quote (price_list_id is the only required field), line items carrying configuration_code, PATCH the update-only commercials, render a quote template attaching dynamic:document_line_items, then status, then revise. Leads with the locking rule — an unfinalized configuration on a quote line is a quote that can silently change after it was sent. States plainly that quote status and opportunity stage are free strings with no enum anywhere: read the tenant's vocabulary, never invent one.
license: MIT
---

# Rattle CRM and quotes — the money end of the funnel

Every other skill in this bundle builds a configurator. **None of them can quote from it.** `rattle-onboarding` creates the tenant, `rattle-ingest` maps the pricelist, `rattle-suggest-config` designs the groups, `rattle-apply-config` writes them, `rattle-bom-builder` explodes the BOM — and then the customer configures a machine and there is nowhere for the number to go. This skill is the path from a saved configuration to a signed quote.

It covers **49 operations across four resources**: Customers (14), Opportunities (7), Quotes (20), Configurations (8).

Quoting **writes to a live tenant** — and unlike a wrong group, a wrong quote is a document that has already been *sent to a customer*. Every write here is idempotent get-or-create matched by a natural key, exactly as in `rattle-apply-config`. Two of the transitions (`status`, `revise`) are not idempotent at all and are gated accordingly.

## When to use this skill

- The user says quote, quotation, Angebot, Kunde, customer, opportunity, pipeline, line item, Position, Rabatt, revision, Vertrieb — or asks how a configuration becomes a PDF with a price on it.
- A configurator exists and the question is now commercial: who is the customer, what did they configure, what does it cost, when does the quote expire.
- The user is wiring an ERP or CRM into Rattle and needs the join keys (`Customer.customer_id`, `Quote.integration_metadata`).
- A sent quote must change. **That is a revision, not an edit** — see § "Never mutate a sent quote".

**Do not use this skill to design the configuration itself.** If the product's options are wrong, the quote will be wrong in a way no CRM call can fix. Go to `rattle-configurator` and the `#1 rule` first.

## Finalize before you quote

> **`POST /configurations/{id}/finalize` — "Lock the configuration so it cannot be modified."**

Lead with this, every time. A quote line points at a configuration by `configuration_code`. If that configuration is still mutable, **the quote you sent and the configuration it references can drift apart, silently.** The customer accepts a price computed from a machine that is no longer the machine in the system. Nothing errors. Nothing warns. The `is_finalized` flag on `ConfigurationResponse` is the only thing standing between a quote and that outcome.

**The rule: `is_finalized: true` before the `configuration_code` goes on a line item. No exception.**

```
GET  /api/v1/configurations/{id}          → ConfigurationResponse.is_finalized
POST /api/v1/configurations/{id}/finalize → is_finalized: true   (no request body)
```

Read it back. If `is_finalized` is already `true`, skip — finalize is a lock, and locking a locked thing is a no-op, not an error you should provoke.

### Where a configuration comes from — and where it does not

Two different entities wear the word "configuration", and confusing them wastes an hour:

| | `ConfigurationStateResponse` | `ConfigurationResponse` |
|---|---|---|
| Returned by | `POST /configurations/calculate` (**201**), `GET /configurations/states/*` | `GET /configurations`, `GET /configurations/{id}`, `POST /configurations/{id}/finalize` |
| Identified by | `config_code`, `config_hash` | `id`, `config_token`, `display_code` |
| Carries | `price_snapshot`, `is_valid`, `validation_errors`, `product_id` | `customer_id`, `opportunity_id`, `price_list_id`, **`is_finalized`**, `offer_language` |
| Mutable? | **Immutable.** "States are immutable." (ETag / `If-None-Match` supported.) | Mutable until finalized |

`POST /configurations/calculate` (required `product_id`; plus `selected_options`, `option_amounts`, `price_list_id`, `enabled_areas`, `disabled_areas`, `wishlist_options`, `validate_config` default `true`) is a **calculator**. It resolves constraints, prices the selection, and hands back a *state*. It does **not** return an `id`, so you cannot finalize what it returns.

> **There is no `POST /configurations`.** The public API has **no write path that creates a saved configuration.** Saved configurations arrive from the configurator UI, where the end customer built them. An agent finds them read-only:
>
> ```
> GET /api/v1/customers/{customerId}/configurations   → this customer's configurations
> GET /api/v1/products/{productId}/configurations     → this product's configurations
> GET /api/v1/configurations?product_id=              → cursor, limit, product_id (no customer_id filter)
> ```
>
> **Do not try to create one.** If the user expects an agent to configure a product end-to-end and quote it, tell them plainly: the agent can *calculate* a price (`/calculate`), but the saved, finalizable, quotable configuration is produced by the configurator, not by this API.

**Always check `is_valid` and `validation_errors` on the state before quoting it.** A configuration that violates a constraint will price perfectly happily. `validate_config` defaults to `true` on calculate; leave it there.

## The funnel

Eleven steps. Steps 1–3 and 5–8 write; 4 finalizes; 9–11 are the document and the lifecycle.

```
1  Customer      get-or-create on their ERP customer_id — never on organization name
2  Contacts      the human who receives the quote
3  Opportunity   what makes the quote reportable — and it is created either way (§ 3)
4  Configuration calculate → then FINALIZE. Lock before you quote.
5  Quote         price_list_id is the only required field
6  Line items    one per configured product, carrying configuration_code
7  Commercials   discount / tax / terms are UPDATE-ONLY — a second call, always
8  Details       payment terms, shipping ⚠ silently swallows unknown fields
9  Document      doc_type=quote template attaching dynamic:document_line_items → render
10 Status        read the tenant's vocabulary first. Never invent a status string.
11 Revise        never mutate a sent quote
```

### 1 · Customer — `GET /customers/search?q=` → `POST /customers`

`CustomerCreateRequest` has **no required fields at all.** Every one is optional: `customer_id` (≤255), `organization` (≤255), `email` (≤255), `phone` (≤50), `address_street|city|country` (≤255), `address_zip` (≤50), `integration_metadata`. `additionalProperties: false`, so a typo `422`s. **`POST /customers` with `{}` is a valid request** — it creates a nameless customer. Nothing stops you; refuse to do it.

> **`customer_id` is the customer's own number** — their ERP / SAP / Debitorennummer, the join key back to their system. It is a free-text string, **unindexed and not unique**. It is also the *only* external identifier on the entity, and — per `docs/API_AUDIT.md` § P2-1 — the pattern `Product` was denied. Use it.

**Match on `customer_id`, not on `organization`.** Organization names collide (`Müller GmbH` is not one company), rename, and carry legal-form noise (`GmbH` / `GmbH & Co. KG` / `mbH`). The ERP number does not.

```
GET /api/v1/customers/search?q=<customer_id>   → up to 50 results, NOT paginated, min 2 chars
```

> **`/customers/search` is fuzzy across three fields** — "Quick search across organization, email, and customer ID". A query of `4711` also matches an organization containing `4711`. **Filter the result client-side for an exact `customer_id ==` match.** And because it caps at 50 with no pagination, a short or common query can silently truncate: for anything broader, use `GET /customers?search=` (`cursor`, `limit`, `search`, `country`), which paginates.

Absent → `POST /customers` (**201**). Present and differing → `PATCH /customers/{id}`. Present and identical → noop.

### 2 · Contacts — `POST /customers/{id}/contacts`

`ContactCreateRequest`: **no required fields either.** `first_name` / `last_name` default to `""`; `email` (≤255), `phone` (≤50), `position` (≤255) are optional.

**A contact with no name and no email is accepted with a `201`.** This is the human who receives the quote. Require an email of yourself, because the API will not.

`GET /customers/{id}/contacts` is **not paginated** — it returns all of them. Natural key: `email` when present, else `(first_name, last_name)`. Update with `PUT /customers/{id}/contacts/{contact_id}` (`ContactUpdateRequest` — all fields optional, nullable).

### 3 · Opportunity — `POST /opportunities`

`OpportunityCreateRequest`: **required `name` (≤255) and `customer_id` (integer FK)**. Optional: `stage` (free string ≤50, default `"qualification"`), `probability` (integer 0–100, default `10`), `expected_amount` (number|string), `expected_close_date`, `owner_contact_id`, `description` (≤2000), `integration_metadata`.

The brief on this step is usually "optional but recommended". **That is not quite what the API does**, and the difference matters:

> **`POST /quotes` description, verbatim: *"Create a quote for an opportunity. If no opportunity_id is given but a customer_id is provided, an opportunity is auto-created."***

So skipping this step **does not avoid an opportunity** — it just means one is created *for* you, with a name and a stage you did not choose. And it is not decorative:

> **`GET /customers/{customerId}/quotes` — "List all quotes associated with a customer (via opportunities)."**

The customer→quotes roll-up **traverses opportunities**. The opportunity is the spine of the customer's commercial history, not an optional CRM nicety. Create it deliberately, with a name a human will recognise six months later.

`OpportunityResponse` additionally carries `opportunity_number`, `primary_quote_id`, `quote_count`, `customer_name`, and **`status` (free string, default `"open"`)** — which is *not settable* on create or update. A second undiscoverable state field; see § "The lifecycle you cannot discover".

Natural key: `(customer_id, name)`. `GET /opportunities?customer_id=&search=` (filters: `cursor`, `limit`, `stage`, `customer_id`, `search` — search is by name).

### 4 · Configuration — calculate, then **finalize**

See § "Finalize before you quote". This step is the one that is easy to skip and expensive to have skipped.

### 5 · Quote — `POST /quotes`

`QuoteCreateRequest`: **required `price_list_id` — and nothing else.** `customer_id` and `opportunity_id` are both optional (see step 3). Optional: `valid_from`, `valid_until`, `notes` (≤5000), `integration_metadata`. `additionalProperties: false`. Returns **201**.

**`price_list_id` is required on every quote.** This is the day-0 dependency coming home: a tenant without a base price list cannot quote at all, and a tenant whose base price list was created *after* its products has every price denominated in the wrong currency (`rattle-onboarding` § "The ordering rule that bites", audit § **P2-4**). If `GET /price-lists` is empty, **stop and go back to onboarding** — do not invent a price list to get past this line.

Pass `customer_id` **and** `opportunity_id` explicitly. The response schema requires `opportunity_id` (non-nullable) while the request makes it optional — the auto-create in step 3 is what reconciles them. Passing it yourself means you never have to care.

`QuoteResponse` reads back: `quote_number`, `status` (default `"draft"`), `version_number` (default `1`), `parent_quote_id`, `is_primary`, `currency` (default `"EUR"` — **derived, not settable**), `total_amount`, `final_amount`, `discount_amount`, `discount_percent`, `tax_amount`, `line_item_count`, `price_list_name`.

> **A quote has no natural key you control.** `quote_number` is server-generated. `POST /quotes` twice creates **two quotes**, both valid, both quotable. To make quoting idempotent, carry your own key in `integration_metadata` and match on it client-side — `GET /opportunities/{id}/quotes` (**not paginated**) returns every quote on the opportunity. This is a **builder convention, not a backend invariant**: nothing in Rattle enforces it, and there is no `?integration_metadata=` filter. Same class of convention as option-uniqueness-within-a-group in `rattle-apply-config`.

### 6 · Line items — `POST /quotes/{id}/line-items`

`LineItemCreateRequest`: **required `product_id`**. Optional: `configuration_code` (string), `quantity` (integer, default `1`), `unit_price` (number|string), `discount_percent` (number 0–100), `notes` (≤2000), `integration_metadata`. Returns **201**.

**`configuration_code` is how a configuration becomes money.** It is the single field that ties this line back to the thing the customer actually configured. Omit it and the line is a bare product at a bare price — no options, no BOM, no traceability, and no way for anyone downstream to reconstruct what was sold.

Full contract, the money-type trap, and the create-only / update-only asymmetry: **`references/line-items.md`**. The one rule to carry here:

> **Round-trip the code before you send it.** `GET /configurations/states/by-code/{code}` must resolve the exact string you intend to put on the line. The spec never states *which* of the three candidate strings (`ConfigurationStateResponse.config_code`, `ConfigurationResponse.display_code`, `ConfigurationResponse.config_token`) `configuration_code` expects, `configuration_code` is a free string with no format and no declared referential integrity, and `QuoteLineItemResponse` echoes back **both** `configuration_code` and `configuration_code_display` — which tells you the stored value and its human-visible form are not the same string. Do not guess. Resolve it, then send what resolved.

### 7 · Commercials — `PATCH /quotes/{id}`

**You cannot create a discounted quote in one call.** `discount_amount`, `discount_percent`, `tax_amount` and `terms_and_conditions` (≤50000) are on `QuoteUpdateRequest` and **not** on `QuoteCreateRequest`. POST, then PATCH. Always two calls. (audit § **P3-2**)

This is not a style preference — it is a **failure mode**. A crash between the two calls leaves a **zero-discount quote in the tenant**, at full list price, indistinguishable from an intentional one. If the process dies at step 7, the quote that exists is *wrong and plausible*. Report it as half-applied; do not leave it implied.

### 8 · Details — `PUT /quotes/{quoteId}/details`

Upsert. `QuoteDetailsUpsertRequest`: `payment_terms` (≤500), `shipping_method` (≤255), `shipping_cost` (**string**), `internal_notes` (≤5000), `custom_fields` (object). No required fields.

> **⚠ This schema does NOT set `additionalProperties: false`.** It is one of only **8 request schemas out of 124** that swallow unknown fields — and `QuoteContactAddRequest` (step 8b) is a second. Everywhere else in Rattle a typo'd field is a loud `422`. **Here it is a silent `200`.** Send `payment_term` instead of `payment_terms` and the API tells you it worked. (audit § **P0-8**)
>
> **The only defence is to read it back.** `GET /quotes/{quoteId}/details` after every write and diff what you sent against what came back. This is exactly the discipline `rattle-onboarding` applies to the 19 configurator-settings flags, for exactly the same reason.

**8b · Quote contacts** — `POST /quotes/{quoteId}/contacts`. `QuoteContactAddRequest`: **required `contact_id`** (the contact must already exist under the customer, from step 2), optional `role` (free string ≤100 — *another* undeclared vocabulary). Same `additionalProperties` hole. This is **the only operation in the CRM surface that declares a `409`** — adding the same contact twice conflicts. Treat 409 as "already linked" → noop, not an error.

### 9 · Document — the quote PDF

> **A `doc_type=quote` template MUST attach `dynamic:document_line_items`.** Without it, the rendered PDF has no line items on it — an empty quote, sent to a customer.
>
> An **`offer`** template attaches `dynamic:document_configuration` instead. **They are different doc_types with different required blocks.** See `rattle-document-templates`; the live contract is `GET /documents/doc-types` (`requires_configuration` / `requires_quote`).

Validate, then render, then poll:

```
GET  /api/v1/documents/templates/{id}/validate-config?config_token=<code>   → gate before rendering
POST /api/v1/documents/renders/quote   {"quote_id": <id>}                   → 202 + job
     (optional: template_id, language, cover_bg_filename)
GET  /api/v1/documents/renders/{job_id}           → poll status (410 = job gone)
GET  /api/v1/documents/renders/{job_id}/content   → stream the PDF bytes
```

**Rendering is asynchronous — `202`, not `200`.** A client that treats the render call as the PDF gets a job id and no document. (The render body is an *inline* schema with no `additionalProperties: false` — same swallow risk as step 8. Send exactly the four documented fields.)

### 10 · Status — `PUT /quotes/{id}/status`

`QuoteStatusUpdateRequest`: **required `status`, typed `{"type": "string", "maxLength": 50}`. No enum.** See § "The lifecycle you cannot discover" — read it before you send this call.

### 11 · Revise — `POST /quotes/{id}/revise`

> **"Create a new version of this quote, incrementing the version number."**

**Never mutate a sent quote.** Once a quote has left the building, `PATCH /quotes/{id}` rewrites the document the customer is holding — the price they were quoted changes underneath them, and the audit trail of what was actually offered is destroyed. `POST /quotes/{id}/revise` (**201**) creates a new version instead; `GET /quotes/{id}/revisions` lists them; `QuoteResponse.version_number` / `parent_quote_id` / `is_primary` carry the lineage.

The API will **not** stop you from PATCHing a sent quote. There is no lock, no state check, no `409`. **The discipline is entirely yours** — which is why the `rattle-quote-author` agent refuses to mutate a quote that is not in a draft-like state, and revises instead.

## The lifecycle you cannot discover

**This is the largest single hole in the CPQ half of the Rattle API, and the skill will not paper over it.**

```jsonc
QuoteStatusUpdateRequest.status  { "type": "string", "maxLength": 50 }        // PUT /quotes/{id}/status
QuoteResponse.status             { "type": "string", "default": "draft" }
OpportunityCreateRequest.stage   { "type": "string", "default": "qualification", "maxLength": 50 }
OpportunityResponse.stage        { "type": "string" }
OpportunityResponse.status       { "type": "string", "default": "open" }      // not settable at all
QuoteContactAddRequest.role      { "type": "string", "maxLength": 100 }
```

**No enum. Anywhere.** `GET /quotes?status=` accepts a filter whose legal values are documented nowhere. `PUT /quotes/{id}/status` accepts **any string up to 50 characters** — `"aproved"` is a schema-valid request. (audit § **P2-1b**)

**What is known:** read-only observation of a live tenant surfaced quote statuses `draft` and `approved`, and opportunity stage `qualification`. **Observed is not the same as legal.** That is a sample, not a vocabulary, and it was not extended further because doing so would require *writing* to a live tenant.

**What is not known, and cannot be known from the API:** the full status vocabulary, the full stage vocabulary, and **which transitions are legal**. Whether `draft → approved` may skip a `sent`-like state is not answerable from the spec, from a response, or from an error message.

Therefore:

1. **Read the tenant's vocabulary before you write one.** Paginate `GET /quotes` and collect the distinct `status` values; `GET /opportunities` and collect the distinct `stage` values. That set is the tenant's *actual* working vocabulary, and it is the only ground truth available.
2. **Never invent a status string.** Not `"sent"`, not `"won"`, not `"versandt"` — however obvious it looks. A status the tenant has never used is a status nothing downstream filters on, reports on, or triggers a webhook for. The quote quietly vanishes from every pipeline view.
3. **If the status you need is not in the tenant's set, ASK THE USER.** Introducing a new status string into a tenant is a business decision, not an API call.
4. **Do not build a state diagram out of guesses.** If asked for one, say what this section says.

> **The one legitimate inference, labelled as such.** `QuoteAnalyticsSnapshotResponse` (`GET /analytics/quotes`, outside the 49) carries `first_presented_at`, `accepted_at`, `rejected_at`, `ordered_at` and `hours_to_present` / `hours_to_accept` / `hours_to_order`. The analytics model therefore *names* four commercial moments — presented, accepted, rejected, ordered. **That is evidence about the domain, not the enum**: those are timestamp field names, not status values, and nothing states which `status` string sets them. It is a useful hint for a conversation with the user. **It is not a dropdown.** `GET /analytics/quotes` is, however, a second read-only way to see which `status` values a tenant has actually recorded.

## Traps

Four findings from `docs/API_AUDIT.md` land squarely in this funnel. Each is silent.

| # | Trap | Consequence |
|---|---|---|
| **P3-2** | **`discount_amount`, `discount_percent`, `tax_amount`, `terms_and_conditions` are update-only** — on `QuoteUpdateRequest`, absent from `QuoteCreateRequest`. | **You cannot create a discounted quote in one call.** POST then PATCH. A failure between them leaves a full-price quote that looks entirely intentional. Same asymmetry on line items: `discount_amount` and `position` are update-only there too. |
| **P0-5** | **Money is encoded seven ways.** `LineItemCreateRequest.unit_price` is `number\|string\|null`. `QuoteResponse.total_amount` / `final_amount` are decimal **strings**. `QuoteAnalyticsSnapshotResponse.total_amount` is a **float**. `QuoteDetailsUpsertRequest.shipping_cost` is a **string**. `PartCreateRequest.part_cost` is an **integer**. | **Never do float arithmetic on money.** Keep decimal-as-string end to end; parse to `Decimal`, never to `float`; send `"1250.00"`, not `1250.0`. A float sum over a long BOM returns a plausible-but-wrong number with a `200 OK`, and it lands directly on the customer's invoice. |
| **P0-8** | **`QuoteDetailsUpsertRequest` and `QuoteContactAddRequest` do not set `additionalProperties: false`** — 2 of only 8 such schemas out of 124. | **A typo'd field is silently swallowed with a `200`.** Everywhere else in Rattle a bad field `422`s, so the agent has *learned* that a bad field errors — and that lesson is wrong exactly here. **Read every details write back and diff it.** |
| **P2-1** | **`QuoteLineItemResponse.product_sku` exists, is read-only, and has no writer anywhere in the API** — because there is no `Product.sku`. | **It renders `null` on every quote line, forever.** Do not promise the customer a SKU column on the quote PDF. The article number lives in `product.integration_metadata.<key>` (the day-0 convention from `rattle-onboarding`) and must be joined in client-side. Say this out loud when someone asks why the SKU is blank. |

## Output contract

Same `applied` / `skipped` / `errors` shape as `rattle-apply-config` and `rattle-onboarding`, plus the two things only a quoting run produces: the finalize verdict and the resolved commercial totals.

```json
{
  "tenant": "acme",
  "quoted_at": "2026-07-14T09:00:00+00:00",
  "preflight": {
    "price_list_id": 3,
    "configuration": {"id": 9001, "display_code": "ACME-4F2B", "is_finalized": true, "is_valid": true},
    "verdict": "configuration locked — safe to quote"
  },
  "applied": [
    {"step": 1, "type": "ensure_customer", "name": "K-10023", "action": "created", "id": 55, "request_id": "req_..."},
    {"step": 2, "type": "ensure_contact", "name": "a.mustermann@example.invalid", "action": "created", "id": 91, "request_id": "req_..."},
    {"step": 3, "type": "ensure_opportunity", "name": "Widget Pro — Linie 2", "action": "created", "id": 17, "request_id": "req_..."},
    {"step": 4, "type": "finalize_configuration", "name": "ACME-4F2B", "action": "finalized", "id": 9001, "request_id": "req_..."},
    {"step": 5, "type": "ensure_quote", "name": "Q-2026-0042", "action": "created", "id": 204, "request_id": "req_..."},
    {"step": 6, "type": "ensure_line_item", "name": "Widget Pro × 2", "action": "created", "id": 811, "request_id": "req_..."},
    {"step": 7, "type": "patch_quote_commercials", "name": "Q-2026-0042", "action": "updated", "id": 204, "request_id": "req_..."},
    {"step": 8, "type": "ensure_quote_details", "name": "Q-2026-0042", "action": "updated", "id": 204, "request_id": "req_..."}
  ],
  "skipped": [
    {"type": "ensure_quote_contact", "name": "contact 91", "reason": "409 — already linked"}
  ],
  "totals": {
    "currency": "EUR",
    "total_amount": "24000.00",
    "discount_amount": "1200.00",
    "tax_amount": "4332.00",
    "final_amount": "27132.00"
  },
  "status": {"current": "draft", "requested": null, "tenant_vocabulary_observed": ["draft", "approved"]},
  "document": {"template_id": 12, "doc_type": "quote", "render_job_id": "job_...", "attaches_line_items": true},
  "errors": []
}
```

Every money value is a **decimal string**. `status.requested` is `null` unless a human explicitly named a status from `tenant_vocabulary_observed`.

**CRM-tier operations.** Seven `ensure_*` types, idempotent get-or-create by natural key — extending the grammar in `rattle-apply-config/references/operations-contract.md` (7 configurator + 3 BOM + 5 document ops):

| Operation | Natural key | REST |
|---|---|---|
| `ensure_customer` | `customer_id` (the ERP number) | `GET /customers/search?q=` → **exact-match client-side** → `POST /customers` / `PATCH /customers/{id}` |
| `ensure_contact` | `(customer_id, email)`, else `(first_name, last_name)` | `GET /customers/{id}/contacts` (**not paginated**) → `POST /customers/{id}/contacts` / `PUT .../{contact_id}` |
| `ensure_opportunity` | `(customer_id, name)` | `GET /opportunities?customer_id=&search=` → `POST /opportunities` / `PATCH /opportunities/{id}` |
| `ensure_quote` | `(opportunity_id, integration_metadata.<key>)` — **convention, not enforced** | `GET /opportunities/{id}/quotes` (**not paginated**) → match client-side → `POST /quotes` |
| `ensure_line_item` | `(quote_id, product_id, configuration_code)` — **convention** | `GET /quotes/{id}/line-items` → `POST /quotes/{id}/line-items` / `PATCH .../{item_id}` |
| `ensure_quote_details` | singleton per quote | `PUT /quotes/{quoteId}/details` (upsert). **Read back and diff — unknown fields are swallowed.** |
| `ensure_quote_contact` | `(quote_id, contact_id)` | `GET /quotes/{quoteId}/contacts` → `POST /quotes/{quoteId}/contacts`. **409 = already linked → noop.** |

**Three operations that are NOT `ensure_*`, because they are state transitions and not idempotent creates:**

| Operation | Why it is different |
|---|---|
| `finalize_configuration` | `POST /configurations/{id}/finalize`. **Irreversible** — there is no un-finalize endpoint. Idempotent only in the sense that a locked configuration stays locked; check `is_finalized` first and skip rather than re-lock. |
| `set_quote_status` | `PUT /quotes/{id}/status`. **No enum, no legal-transition contract.** Requires an explicit human-named status drawn from the tenant's observed vocabulary. Never emitted by inference. |
| `revise_quote` | `POST /quotes/{id}/revise`. **Creates a new quote version every time it is called** — running it twice produces two revisions. Never batch it, never retry it blindly. |

## Handing off

```
rattle-onboarding      base price list exists   ← price_list_id is REQUIRED on every quote
  └→ rattle-ingest → rattle-suggest-config → rattle-apply-config   the configurator
       └→ rattle-bom-builder      the BOM behind the configured options
            └→ (the customer configures a product in the configurator UI)
                 └→ rattle-crm-quotes    customer → opportunity → finalize → quote → lines  ← you are here
                      └→ rattle-document-templates   doc_type=quote + dynamic:document_line_items → PDF
                      └→ rattle-tenant-memory        the tenant's status vocabulary, once learned
```

- **Never quote from an unfinalized configuration.** It is the one rule in this skill that cannot be repaired after the fact.
- **Never invent a quote status or an opportunity stage.** Read the tenant's, or ask.
- **Never mutate a sent quote.** Revise it.
- **Never do float arithmetic on money.** Decimal-as-string, end to end.
- **Record the tenant's status vocabulary** in `memory/<tenant>/profile.md` once a human has confirmed it — `rattle-tenant-memory`, explicit-write only. It is exactly the kind of convention that is otherwise silently re-invented every session.

## Adjacent surface (outside the 49)

Real, useful, and *not* covered by the funnel above — flagged so nobody re-discovers them the hard way:

- **`POST /customers/batch`** — up to 100 create/update/delete/upsert ops. **Best-effort, not atomic**: `200` = all succeeded, `207` = at least one failed, per-item `results` array. Supports **`X-Idempotency-Key`** (a replay with the same key and body returns the original response). The only real idempotency primitive in the CRM surface — but which fields are legal `match` keys is undocumented (audit § P1).
- **`POST /inbound/customers` · `/inbound/customers/batch` · `/inbound/opportunities`** — ERP-facing upserts. `/inbound/opportunities` claims to create "an opportunity with optional configuration and quote" in one call. **Unverified**: its request schema is not resolvable by name in the spec's `components`. Do not build on it without probing it first.
- **`GET /customers/export`** — streams all customers as NDJSON.
- **`GET /analytics/quotes`** — quote-level snapshots (scope `analytics:read`). Floats. See § "The lifecycle you cannot discover".

## Reference files

| File | Use when |
|---|---|
| `references/quote-lifecycle.md` | You are about to set a status or a stage — the missing-enum problem in depth, and how to discover the tenant's real vocabulary read-only |
| `references/line-items.md` | You are building the lines — `configuration_code` linkage, the money-type trap, and why a discount needs a second call |

## Related skills

- `rattle-configurator` — the `#1 rule` and the data model. A quote is only as correct as the configuration under it.
- `rattle-document-templates` — the `doc_type=quote` template that must attach `dynamic:document_line_items`. The PDF is the output of this funnel.
- `rattle-onboarding` — where `price_list_id` comes from. A tenant with no base price list cannot quote.
- `rattle-apply-config` — the idempotent `ensure_*` grammar this skill's CRM tier extends.
- `rattle-tenant-memory` — where the tenant's status vocabulary is recorded once a human confirms it.
- `rattle-api` — REST mechanics: auth, cursor pagination, RFC 9457 problem details, the OCC headers the spec does not declare.
