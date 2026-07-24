# The quote lifecycle you cannot discover

The commercial core of a CPQ system is its state machine: a quote is drafted, sent, accepted or rejected; an opportunity moves through a pipeline. **Not one state of that machine is declared anywhere in the Rattle API.**

This file states exactly what is known, exactly what is not, and what to do about it. It does not contain a lifecycle diagram, because **a lifecycle diagram cannot be built from what the API exposes**, and a confidently-drawn wrong one is worse than none.

Cross-reference: `docs/API_AUDIT.md` § **P2-1b** ("The entire sales lifecycle is a free string — the state machine is undiscoverable") and § **P1-1** (119 enum-shaped fields are free strings; the whole spec has 14 enums).

## 1 · What the spec actually says

Every state-carrying field in the funnel, verbatim from `docs/openapi.json`:

```jsonc
// PUT /quotes/{id}/status
QuoteStatusUpdateRequest.status   { "type": "string", "maxLength": 50 }              // required
QuoteResponse.status              { "type": "string", "default": "draft" }

// POST /opportunities  ·  PATCH /opportunities/{id}
OpportunityCreateRequest.stage    { "type": "string", "default": "qualification", "maxLength": 50 }
OpportunityUpdateRequest.stage    { "type": "string", "maxLength": 50, "nullable": true }
OpportunityResponse.stage         { "type": "string" }                               // required on the response

// Read-only — settable on NO request schema
OpportunityResponse.status        { "type": "string", "default": "open" }

// QuoteContactResponse (read-only; removed from POST /quotes/{quoteId}/contacts, which now takes only contact_id)
QuoteContactResponse.role         { "type": "string", "maxLength": 100 }

// Filters
GET /quotes?status=<string>            // "Filter by status"  — legal values documented nowhere
GET /opportunities?stage=<string>      // "Filter by stage"   — legal values documented nowhere
```

**Four free-string state fields, two filters over vocabularies that are never published, and zero enums** — and the quote-contact `role` free-string field has since been **removed from the write request** (it is read-only on `QuoteContactResponse` now).

`PUT /quotes/{id}/status` will accept `"aproved"`. It will accept `"banana"`. It will accept any of 50 characters. The schema has no opinion, and the endpoint declares no `422` for a bad status value — only the generic one.

## 2 · What is observable

Read-only observation of a live Rattle tenant surfaced:

| Field | Values seen |
|---|---|
| `QuoteResponse.status` | `draft`, `approved` |
| `OpportunityResponse.stage` | `qualification` |

**That is a sample. It is not the vocabulary.**

Observed values are a lower bound on the vocabulary and say nothing at all about:

- states the tenant has simply not used yet;
- states other tenants use;
- states the backend would accept;
- **which transitions between them are legal.**

The set was not extended further because extending it would require **writing** to a live customer tenant — POSTing speculative status strings to find out which stick. That is not an acceptable way to discover an API contract, and it would leave garbage states on real quotes.

## 3 · The one legitimate inference — labelled as an inference

`QuoteAnalyticsSnapshotResponse` (`GET /analytics/quotes`, scope `analytics:read`) carries these fields:

```
first_presented_at   accepted_at   rejected_at   ordered_at
hours_to_present     hours_to_accept             hours_to_order
```

The analytics model therefore **names four commercial moments**: presented, accepted, rejected, ordered.

**What this is:** evidence that the domain model has a notion of a quote being presented, then accepted or rejected, then ordered. It is a good basis for a *conversation with the user* about what their pipeline looks like.

**What this is NOT:**

- **It is not the enum.** These are timestamp field names on an analytics snapshot, not values of `status`.
- **It does not tell you the strings.** Nothing states that a status of `"presented"` (or `"sent"`, or `"versandt"`) is what sets `first_presented_at`. The setter may be an internal event, a webhook, or a UI action.
- **It does not tell you the transitions.** Whether `draft` may go straight to `approved`, or must pass through a presented-like state, is not answerable from this or anything else.

**Do not turn these four words into a status dropdown.** Do not write them into a tenant. They are a hypothesis to put to a human.

## 4 · How to discover the tenant's actual vocabulary — read-only

Three read-only calls. None of them writes. Run them **before** any status or stage write, every session — a vocabulary learned in March is not a vocabulary you may assume in July.

### 4.1 Quote statuses in use

```
GET /api/v1/quotes?limit=100          → paginate via meta cursor
```

Collect the distinct `status` values across every page. `QuoteResponse.status` is present on every quote (it defaults to `"draft"`), so a full pass gives you the complete set of statuses **this tenant has actually produced**.

### 4.2 Opportunity stages in use

```
GET /api/v1/opportunities?limit=100   → paginate via meta cursor
```

Collect the distinct `stage` values. Also collect `status` (the read-only, never-settable one, default `"open"`) — if you find a value other than `open`, something outside the public API is setting it, and that is worth telling the user.

### 4.3 Cross-check against analytics

```
GET /api/v1/analytics/quotes          → QuoteAnalyticsSnapshotResponse.status
```

A second, independent view of which status strings the tenant has recorded. If a status appears here that did not appear in 4.1, the quote carrying it may have been deleted — useful, and worth surfacing.

### 4.4 Probe the filter — still read-only

```
GET /api/v1/quotes?status=<candidate>
```

A status that returns rows **exists in this tenant**. A status that returns zero rows tells you **nothing** — it may be legal-but-unused, or it may be nonsense. **A zero-row filter is not evidence that a status is invalid, and it is certainly not evidence that it is valid.** Never promote a candidate to "supported" on the strength of an empty result set.

## 5 · The rules

1. **Never invent a status string.** Not `sent`, not `won`, not `lost`, not `versandt`, not `angenommen`. However obvious the word is, if the tenant has never used it, writing it makes the quote disappear from every list, filter, report and webhook consumer that keys on the statuses the tenant actually uses. The write returns `200`. Nothing tells you.

2. **Only ever set a status that is already in the tenant's observed set** (§ 4.1) — *or* one a human has explicitly named in this session.

3. **If the status you need is not in the set, ASK.** Introducing a new status into a tenant is a business decision with reporting consequences, not an API call. Present the observed set, present what you need, and let the human decide.

4. **Never assume a transition is legal.** There is no documented transition table. The API will not reject an illegal transition — as far as the schema is concerned there are no illegal transitions, because there are no states. If the user asks "can I go from draft straight to approved?", the honest answer is: *the API will accept it; whether your business process allows it is your call, and Rattle will not enforce it either way.*

5. **Never build a state diagram out of guesses.** If asked to render a pipeline, a funnel, or a status dropdown, use the tenant's observed vocabulary and **say that it is observed, not declared**.

6. **The same rules apply to `stage`** (opportunity) — a free string with no enum. (The quote-contact `role` field was once a third such vocabulary; the current spec has **removed it from the write request** — `QuoteContactAddRequest` now takes only `contact_id` — so there is no longer a `role` to set, only one to read on `QuoteContactResponse`.)

7. **Record the vocabulary once a human has confirmed it.** `memory/<tenant>/profile.md`, under a `## Conventions` heading — `rattle-tenant-memory` is explicit-write only, so show the file and get consent. A vocabulary recorded there is honoured by every later session; one that is not is re-guessed every time.

   ```markdown
   ## Conventions
   - **quote-statuses**: draft → approved (confirmed by <role>, 2026-07-14; observed set: draft, approved)
   - **opportunity-stages**: qualification (observed set; full pipeline not confirmed)
   ```

   Write the *provenance* into the line. "Observed" and "confirmed by a human" are different epistemic states and the next session needs to know which one it is looking at.

## 6 · What a correct answer sounds like

When a user asks "what are the quote statuses?", the correct answer is **not** a list of five plausible words. It is:

> The Rattle API does not declare them. `QuoteStatusUpdateRequest.status` is a free string capped at 50 characters, with no enum, and `GET /quotes?status=` filters on a vocabulary that is documented nowhere — so any list I gave you would be a guess that looks like a fact.
>
> What I *can* do is read your tenant: paginate `GET /quotes` and collect the distinct `status` values actually in use. That is the real working vocabulary, and it is the one your reports and filters key on.
>
> On a tenant we probed read-only, that set was `draft` and `approved` — but that is a sample of one tenant's history, not the legal vocabulary. If you need a status that is not in your set, tell me which, and I will use exactly that string.

That answer is longer than a guess and it is the only one that is true.

## 7 · Escalation

This is not a gap a skill can close — it is a gap in the API. `docs/API_AUDIT.md` § P2-1b asks Rattle directly:

> Declare `QuoteStatus` and `OpportunityStage` as enums, reference them from every request, response and query parameter, and document the legal transitions (even as prose). **This is the single change that would make the CPQ half of the API programmable.**

Until that lands, every client — this skill included — is guessing or asking. **Ask.**
