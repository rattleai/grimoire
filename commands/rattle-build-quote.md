---
description: Turn a saved Rattle configuration into a quote a customer can sign. Walks the 11-step quote-to-cash funnel — customer, contacts, opportunity, finalize the configuration, quote, line items, commercials, details, document, status, revise. Leads with the locking rule: finalize before you quote, or the configuration behind a sent quote can still change. Never invents a quote status — the vocabulary is a free string with no enum, so it reads the tenant's and asks before introducing a new one.
argument-hint: <tenant name> [configuration code or customer]
---

# /rattle-build-quote

Take the tenant the user names (`$ARGUMENTS`) from a **saved configuration** to a **quote** — customer, opportunity, line items, commercials, PDF. This is the money end of the funnel: every other Rattle command builds a configurator, and none of them can quote from it.

Quoting **writes to a live tenant**, and a wrong quote is worse than a wrong group — it is a document that has already been sent to a customer. Every write is idempotent get-or-create by natural key, and every write waits for explicit human confirmation.

## Workflow

1. **Load context** — Read `skills/rattle-crm-quotes/SKILL.md` and both reference files: `references/quote-lifecycle.md` (before touching a status) and `references/line-items.md` (before touching a line). Also load `skills/rattle-configurator/SKILL.md` — a quote is only as correct as the configuration under it — and `skills/rattle-document-templates/SKILL.md` for the PDF. Read `memory/<tenant>/profile.md`: it carries the article-number key, the numbered-option unit, and (if a human has confirmed it) the tenant's status vocabulary.

2. **Finalize before you quote** — State this before the first write. `POST /configurations/{id}/finalize` — *"Lock the configuration so it cannot be modified."* **A quote line pointing at a mutable configuration is a quote that can silently change after it was sent.** Check `is_finalized` on `GET /configurations/{id}`; if it is `false`, finalize (it is **irreversible** — there is no un-finalize). Also check `is_valid` and `validation_errors` on the state: an invalid configuration prices perfectly happily.

   **There is no `POST /configurations`.** The API cannot *create* a saved configuration — the configurator UI does. Find the existing one: `GET /customers/{customerId}/configurations`, `GET /products/{productId}/configurations`, `GET /configurations?product_id=`. `POST /configurations/calculate` is a calculator; it returns a state (`config_code`, `config_hash`), not a finalizable `id`.

3. **Customer → contacts → opportunity** — Get-or-create the customer on **`customer_id`, their ERP number** — never on `organization`, which collides. `GET /customers/search?q=` is fuzzy across organization, email and customer ID, caps at 50, and is not paginated: **filter client-side for an exact match.** Then the contact who receives the quote (`ContactCreateRequest` has **no required fields** — a nameless, email-less contact is accepted with a `201`; require an email yourself). Then the opportunity (`name` + `customer_id` required).

   **The opportunity is not optional in the way it looks.** `POST /quotes`: *"If no opportunity_id is given but a customer_id is provided, an opportunity is auto-created."* Skipping the step does not avoid an opportunity — it hands you one you did not name. And `GET /customers/{customerId}/quotes` lists quotes **"via opportunities"**, so the opportunity is the spine of the customer's commercial history. Pass `opportunity_id` explicitly.

4. **Quote → line items** — `POST /quotes` with **`price_list_id` — the only required field.** If `GET /price-lists` is empty, **stop and route to `/rattle-onboard`**; do not invent a price list. Then one line item per configured product, each carrying `configuration_code`.

   **Round-trip the code before you send it.** The spec never says which of `config_code` / `display_code` / `config_token` `configuration_code` expects, and the field has no declared referential integrity. `GET /configurations/states/by-code/{code}` must return `200` for the exact string you intend to write. A code that does not resolve produces a `201` line item that points at nothing and renders on the PDF anyway.

5. **Commercials and details — two calls, and say so** — `discount_amount`, `discount_percent`, `tax_amount`, `terms_and_conditions` are **update-only** (audit § P3-2): **you cannot create a discounted quote in one call.** POST, then PATCH. **A failure between them leaves a full-price quote that looks entirely intentional** — report it as half-applied, never as applied.

   Then `PUT /quotes/{quoteId}/details`. **This schema and `QuoteContactAddRequest` do not set `additionalProperties: false`** — 2 of only 8 in the whole API (audit § P0-8). **A typo'd field is swallowed with a `200`.** Everywhere else in Rattle it `422`s. **Read the details back and diff them** — that read-back is the only validation that exists.

   **Never do float arithmetic on money** (audit § P0-5): `unit_price` is `number|string`, quote totals are decimal strings, analytics totals are floats. Decimal-as-string, end to end.

6. **The document** — A **`doc_type=quote`** template MUST attach **`dynamic:document_line_items`**. (An **`offer`** attaches `dynamic:document_configuration` — different doc_type, different required block.) Validate, then render, then poll: `GET /documents/templates/{id}/validate-config?config_token=` → `POST /documents/renders/quote {"quote_id": …}` → **`202`, a job, not a PDF** → `GET /documents/renders/{job_id}` → `/content`.

7. **Status — read the tenant's vocabulary, never invent one** — `PUT /quotes/{id}/status` takes a **free string, max 50 chars, no enum anywhere** (audit § P2-1b). `"aproved"` is a schema-valid request. The full vocabulary and the legal transitions are **not discoverable from the API** — this is stated plainly, not papered over.

   Paginate `GET /quotes` and collect the distinct `status` values: that set is the tenant's actual working vocabulary and the only ground truth available. **If the status you need is not in it, ASK THE USER.** Introducing a new status string is a business decision with reporting consequences, not an API call.

8. **Revise — never mutate a sent quote** — `POST /quotes/{id}/revise` — *"Create a new version of this quote, incrementing the version number."* The API will **not** stop you from PATCHing a sent quote; there is no lock and no `409`. The discipline is entirely yours. `GET /quotes/{id}/revisions` lists the lineage.

9. **Record what was learned** — If a human confirmed the status vocabulary, write it to `memory/<tenant>/profile.md` with its provenance ("observed" vs "confirmed by a human" are different things and the next session must know which). `rattle-tenant-memory` is **explicit-write only**: show the file and get consent.

## Confirmation discipline

Every write pauses. Restate the tenant, the step, and the exact request body, then ask the user to **type the tenant name** to confirm. A generic "yes" is not consent. Three writes are not idempotent and get their own gate: **`finalize`** (irreversible), **`status`** (needs a human-named string), and **`revise`** (creates a new version every call — never retried blindly). If you cannot reach a human, stop and report the planned calls — an unapplied plan is recoverable, a quote sent to a customer is not.

## Delegation

Delegate the run to the `rattle-quote-author` subagent with the tenant name. It preloads `rattle-crm-quotes`, `rattle-configurator`, `rattle-api`, `rattle-document-templates` and `rattle-tenant-memory`, holds the confirmation gate, refuses to quote an unfinalized configuration, refuses to invent a status string, and **refuses to mutate a quote that is not in a draft-like state — it revises instead.**

$ARGUMENTS
