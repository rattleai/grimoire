# Rattle API client patterns

Language-agnostic patterns for building a Rattle client. These mirror the implementation in `rattle_api/client.py` (Python `RattleClient`) so any other client (TypeScript, Go, curl, MCP server) produces equivalent behaviour.

## 1. Authenticated request

```
GET https://www.rattleapp.de/api/v1/products?limit=25
Authorization: Bearer rk_live_<tenant_token>
Accept: application/json
```

Failure modes:

- **401** — missing or wrong token. Check the `RATTLE_API_KEY_<TENANT>` env var; tokens are tenant-scoped, not global.
- **403** — token valid but lacks scope. Confirm the tenant matches the resource you're accessing.
- **429** — rate-limited. Respect `Retry-After`. Default to exponential backoff starting at 1 s, max 30 s.

## 2. List-all (cursor pagination)

```
def list_all(endpoint, per_page=100):
    cursor = None
    while True:
        params = {"limit": per_page}
        if cursor: params["cursor"] = cursor
        page = GET endpoint with params
        yield from page["data"]
        meta = page.get("meta") or {}
        if not meta.get("has_next"): return
        cursor = meta["next_cursor"]
```

- Default `per_page=100` (the API max). 25 is the API default but is too chatty for any real catalogue.
- Some endpoints don't paginate — they return `{"data": [...]}` without `meta`. The loop above handles that (no `has_next` → return after first page).

## 3. Idempotent ensure (get-or-create)

The consulting workflows treat names as natural keys. Standard pattern:

```
def ensure_group(name, is_multi, area_ids):
    existing = next((g for g in list_all("/groups") if g["name"].lower() == name.lower()), None)
    if existing:
        # update is_multi / area links if they drifted
        if existing["is_multi"] != is_multi:
            PATCH /groups/{existing["id"]} {"is_multi": is_multi}
        for area_id in set(area_ids) - set(existing.get("area_ids", [])):
            POST /groups/{existing["id"]}/areas {"area_id": area_id}
        return existing["id"]
    created = POST /groups {"name": name, "is_multi": is_multi}
    for area_id in area_ids:
        POST /groups/{created["data"]["id"]}/areas {"area_id": area_id}
    return created["data"]["id"]
```

A second run with the same inputs is a no-op. This is what `system_prompt_apply_config` (see `rattle-configurator/references/system-prompts.md`) generates as `ensure_group` operations.

## 4. Sub-resource writes vs mass updates

When linking a group to areas, **always** use `POST /groups/{id}/areas {"area_id": X}` — one call per area. Do **not** PATCH the group with a new `area_ids` array; that endpoint exists but the dedicated sub-resource path is the documented happy path and supports per-link metadata.

Same for:

- `POST /products/{productId}/areas` (assign area to product)
- `PUT /options/{id}/area-config?area_id=X` (per-area option override)
- `POST /documents/templates/{id}/structure/blocks` (add a structure block)
- `POST /documents/templates/{id}/structure/blocks/{block_id}/attachments` (attach a content block)

## 5. Multipart image upload

```
POST /options/{id}/image
Content-Type: multipart/form-data; boundary=...

--boundary
Content-Disposition: form-data; name="file"; filename="wheel-19in.jpg"
Content-Type: image/jpeg

<binary>
--boundary--
```

Field name is **always** `file`. Accepted: JPEG, PNG, WebP, GIF; max 10 MB. Returns the updated entity with the image URL.

## 6. Optimistic concurrency: `POST /constraints`

`POST /constraints` atomically replaces all pair constraints for a product. To avoid the lost-update problem:

```
GET /constraints?product_id=42
→ response includes header: X-Constraints-Version: 17

POST /constraints
X-Constraints-Version: 17
{"product_id": 42, "forbidden": [{"option_id1": 100, "option_id2": 200}, ...]}
→ 200 OK if version still 17, 412 Precondition Failed otherwise
```

On 412: re-read `GET /constraints`, merge your changes with the new state, retry. Do not blindly retry with the old version — you would clobber another writer's changes.

## 7. Error handling

Every error body is RFC 9457 problem-details JSON. Always:

- Log `request_id` (for support traces).
- Log `type` and `detail` (machine-readable + human-readable).
- For 422, log the full `errors` array — it pinpoints the offending field.

Translate to client exceptions by `status`:

| status | client exception |
|---|---|
| 400 | `BadRequest` (your fault, malformed body) |
| 401 | `Unauthenticated` (missing/wrong token) |
| 403 | `Forbidden` (token lacks scope) |
| 404 | `NotFound` (id doesn't exist for this tenant) |
| 409 | `Conflict` (concurrent write or constraint violation) |
| 412 | `StaleVersion` (re-read and retry) |
| 422 | `ValidationFailed` (per-field errors) |
| 429 | `RateLimited` (honour `Retry-After`) |
| 5xx | `ServerError` (retry with backoff up to N times) |

## 8. Discovering capabilities at runtime

Where the model has runtime contracts, prefer reading them over hard-coding:

- `GET /documents/doc-types` — returns each registered doc_type with `default_layout` and `requires_configuration`. Use this to validate offer templates before publishing instead of hard-coding which dynamic blocks are required.
- `GET /documents/content-blocks?is_dynamic=true` — returns the system dynamic content blocks. Look up `dynamic:document_configuration` and similar by key, never by hard-coded id.

This is what makes the consulting workflow tenant-portable — the contract lives on the server.
