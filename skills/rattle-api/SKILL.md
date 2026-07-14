---
name: rattle-api
description: Use this skill whenever the user calls, debugs, or designs against the Rattle REST API (rattleapp.de — 462 operations across 257 paths in 37 resource groups). Covers authentication, base URL, response envelope, cursor pagination, RFC 9457 errors, image upload (multipart/form-data), and the conventions every endpoint follows. Pair with rattle-configurator for any task that combines API calls with consulting decisions. Refer to references/api-reference.md for the full endpoint catalogue.
license: MIT
---

# Rattle REST API

The Rattle SaaS exposes a REST API documented at `https://www.rattleapp.de/docs/api/interactive` (Swagger UI) and bundled here as `references/api-reference.md` (full operation table) and `references/openapi.json` (raw OpenAPI spec). Use this skill whenever you need to construct an API call, parse a response, page through a list, or upload an image.

## When to use this skill

- Crafting any HTTP call against `rattleapp.de/api/v1`
- Debugging a 4xx/5xx response from the API
- Choosing the right endpoint for a given entity (which there are many — there are sometimes 5+ ways to write to the same conceptual resource)
- Pagination across large lists
- Uploading an option image, a part image, or a content-block asset
- Authoring write logic that must respect optimistic concurrency (e.g. `X-Constraints-Version`)

If the question is about **what** to model rather than **how** to call the API, use `rattle-configurator` instead. They are designed to be loaded together.

## Conventions

### Base URL

```
https://www.rattleapp.de/api/v1
```

Override via env var `RATTLE_BASE_URL` (the Python CLI honours this; replicate in any other client).

### Authentication

Every request needs:

```
Authorization: Bearer rk_live_<tenant_token>
```

Tokens are tenant-scoped. The CLI loads them from env vars named `RATTLE_API_KEY_<TENANT>` (uppercased), e.g. `RATTLE_API_KEY_ACME=rk_live_…` → tenant `acme`. **Never log or echo the token; rotate immediately if exposed.**

### Content type

```
Content-Type: application/json
```

Image uploads use `multipart/form-data` with field name `file`. Accepted: JPEG, PNG, WebP, GIF. Max 10 MB.

### Response envelope

Single resource:

```json
{"data": {"id": 42, "name": "..."}}
```

Paginated list:

```json
{
  "data": [],
  "meta": {"limit": 25, "has_next": true, "next_cursor": "eyJ...", "total_count": 42}
}
```

Some endpoints are not paginated and return `{"data": []}` without `meta` — noted per endpoint in the reference table.

### Errors (RFC 9457)

```json
{
  "type": "/problems/not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "...",
  "request_id": "req_..."
}
```

422 responses include an `errors` array with per-field details. Always preserve `request_id` — Rattle support can use it to trace the request server-side.

### Pagination

Cursor-based. Parameters:

- `cursor` — opaque string from the previous page's `meta.next_cursor`. Omit on first call.
- `limit` — default 25, max 100.

A typical "list everything" loop:

```
cursor = None
while True:
    page = GET /<endpoint>?cursor=<cursor>&limit=100
    yield from page.data
    if not page.meta.has_next: break
    cursor = page.meta.next_cursor
```

The bundled Python `RattleClient.list_all(endpoint, per_page=100)` helper in `rattle_api/client.py` does exactly this. Replicate the loop in any other client.

### Optimistic concurrency

Three write surfaces accept an `X-<Resource>-Version` header for optimistic concurrency. Read the version from the prior GET, echo it on the POST, retry once on **`409 Conflict`** (the server returns 409 with a problem-detail body whose `detail` contains `Version conflict:` for stale-version, NOT 412 Precondition Failed):

- `POST /constraints` ↔ `X-Constraints-Version` — atomically replaces all forbidden option pairs for a product (body `{product_id, forbidden: [{option_id1, option_id2}, ...]}`).
- `POST /constraints/area` ↔ `X-Areas-Version` — atomically replaces all forbidden area pairs for a product.
- `POST /price-lists/*` (replace endpoints) ↔ `X-Price-Lists-Version` — bulk-replace price-list contents.

See `references/client-patterns.md` § 6 for the full read-modify-write recipe.

## How to use this skill

1. **Identify the entity.** The user's question maps to one of: products, areas, groups, options, parts, BOM items, constraints, document templates, content blocks, structure blocks, attachments, doc-types, files, organisations, ERP integrations, webhooks, etc.
2. **Find the right operation in `references/api-reference.md`.** It lists every endpoint with method, path, summary, and example bodies. Search by tag or by path fragment.
3. **Check for a sub-resource path.** Many associations have dedicated paths — e.g. groups are linked to areas via `POST /groups/{id}/areas` (not by editing the group's `area_ids` field directly), products to areas via `POST /products/{productId}/areas`, options' per-area config via `PUT /options/{id}/area-config?area_id=…`. Sub-resource paths are always more specific than mass updates.
4. **Page through lists.** Default to `limit=100` and the cursor loop unless you genuinely need only a single page.
5. **Treat writes as idempotent get-or-create.** Most consulting workflows match by name. Read first, decide create vs update, then write. The `system_prompt_apply_config` (see `rattle-configurator/references/system-prompts.md`) emits operations in this shape exactly.

## Reference files

- `references/api-reference.md` — full 462-operation table with method, path, summary, parameters, request body fields, response codes, and schema names. **Read this** when you need to compose any specific call.
- `references/openapi.json` — raw OpenAPI 3.1 spec. Use it programmatically (codegen, type generation) or when the Markdown reference is ambiguous.
- `references/client-patterns.md` — common call patterns: list-all, idempotent ensure, multipart upload, optimistic concurrency.

Both `api-reference.md` and `openapi.json` here are **mirrors** of `docs/openapi.json` and `docs/API_REFERENCE.md` at the repo root. They are regenerated together by `python3 scripts/build_api_reference.py` — never hand-edit them.

## Resource groups (36)

Analytics · API Keys · Area Groups · Areas · Attributes · Baselines · Batch · Branches · Catalog Filters · Change Orders · Change Requests · Company · Configurations · Connectors · Constraints · Customer Links · Customers · Documents (78 ops — largest group, includes templates, content/structure blocks, doc-types, conditions, instances, attachments, public links, render jobs) · Export · Groups · Images · Inbound Webhooks · Item Revisions · Languages · Opportunities · Options · Part Documents · Parts · Price Lists · Price Overrides · Product Media · Products · Pull Requests · Quotes · Translations · Webhooks.

## Related skills

- `rattle-configurator` — consulting knowledge that drives **what** to call.
- `rattle-pricelist-analysis`, `rattle-suggest-config`, `rattle-document-templates` — workflows that orchestrate API calls.
