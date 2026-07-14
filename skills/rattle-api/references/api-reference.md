# Rattle REST API Reference

> Generated from `docs/openapi.json` by `scripts/build_api_reference.py`.
> Re-run that script after replacing the spec file to keep this document in sync.
> **Do not hand-edit** — changes will be overwritten on the next build.

## Overview

- **Base URL**: `https://www.rattleapp.de/api/v1` (override via env var `RATTLE_BASE_URL`).
- **OpenAPI version**: 3.1.0
- **Spec version**: 1.0.0
- **Operations**: 463 across 258 paths and 37 resource groups.

## Authentication

All requests require a bearer token:

```
Authorization: Bearer rk_live_<tenant_token>
```

Tokens are tenant-scoped (`rk_live_*` for production, `rk_test_*` for staging). The Python CLI loads them from `RATTLE_API_KEY_<TENANT>` env vars (e.g. `RATTLE_API_KEY_ACME=rk_live_…` → tenant `acme`). A small set of admin endpoints accepts a session cookie instead — these are noted per-operation in the spec under `SessionAuth`.

## Content type

```
Content-Type: application/json
```

Image uploads use `multipart/form-data` with field name `file`. Accepted types: JPEG, PNG, WebP, GIF. Maximum 10 MB.

## Response envelope

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

Some endpoints are not paginated and return `{"data": []}` without `meta`. Check the response schema per operation.

## Errors (RFC 9457 — Problem Details)

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

## Pagination

Cursor-based. Parameters:

- `cursor` — opaque string from the previous page's `meta.next_cursor`. Omit on first call.
- `limit` — default 25, max 100.

Loop pattern (also implemented as `RattleClient.list_all()` in `rattle_api/client.py`):

```python
cursor = None
while True:
    page = client.get("products", params={"cursor": cursor, "limit": 100})
    yield from page["data"]
    if not page["meta"].get("has_next"):
        break
    cursor = page["meta"]["next_cursor"]
```

## Optimistic concurrency

A handful of bulk-replace endpoints accept an `X-<Resource>-Version` header so concurrent clients cannot silently overwrite each other:

- `POST /constraints` uses `X-Constraints-Version` (read latest from `GET /constraints?product_id=…`, send back). Server returns **`409 Conflict`** if stale (problem-detail body's `detail` contains `Version conflict:` to distinguish stale-version from other 409 conflicts; NOT `412 Precondition Failed`). Same OCC pattern applies to `POST /constraints/area` (`X-Areas-Version`) and `POST /price-lists/*` writes (`X-Price-Lists-Version`).

Other replace-style endpoints follow the same convention where applicable — see the operation's parameter list for `X-*-Version` headers.

## Using with `RattleClient`

The Python client wraps every operation; paths are relative (no `/api/v1` prefix):

```python
from rattle_api.client import RattleClient
client = RattleClient("acme")

products  = client.list_all("products", per_page=100)
created   = client.post("products", json={"name": "Widget", "base_price": "99.00"})
patched   = client.patch(f"products/{created['data']['id']}", json={"description": "Updated"})
client.delete(f"products/{created['data']['id']}")
client.upload_image("options/301/image", "/path/to/image.jpg")
```

Other languages should mirror these patterns — there is nothing Rattle-specific about the wrapper itself.


## Resource groups

| Tag | Operations | Anchor |
| --- | ---: | --- |
| Analytics | 4 | [#analytics](#analytics) |
| API Keys | 3 | [#api-keys](#api-keys) |
| Area Groups | 7 | [#area-groups](#area-groups) |
| Areas | 19 | [#areas](#areas) |
| Attributes | 11 | [#attributes](#attributes) |
| Baselines | 4 | [#baselines](#baselines) |
| Batch | 8 | [#batch](#batch) |
| Branches | 4 | [#branches](#branches) |
| Catalog Filters | 10 | [#catalog-filters](#catalog-filters) |
| Change Orders | 13 | [#change-orders](#change-orders) |
| Change Requests | 8 | [#change-requests](#change-requests) |
| Company | 14 | [#company](#company) |
| Configurations | 8 | [#configurations](#configurations) |
| Connectors | 22 | [#connectors](#connectors) |
| Constraints | 16 | [#constraints](#constraints) |
| Customer Links | 6 | [#customer-links](#customer-links) |
| Customers | 14 | [#customers](#customers) |
| Documents | 78 | [#documents](#documents) |
| Export | 3 | [#export](#export) |
| Groups | 11 | [#groups](#groups) |
| Images | 16 | [#images](#images) |
| Inbound Webhooks | 7 | [#inbound-webhooks](#inbound-webhooks) |
| Item Revisions | 7 | [#item-revisions](#item-revisions) |
| Languages | 7 | [#languages](#languages) |
| Opportunities | 7 | [#opportunities](#opportunities) |
| Options | 15 | [#options](#options) |
| Part Documents | 11 | [#part-documents](#part-documents) |
| Parts | 33 | [#parts](#parts) |
| Price Lists | 8 | [#price-lists](#price-lists) |
| Price Overrides | 6 | [#price-overrides](#price-overrides) |
| Product Media | 10 | [#product-media](#product-media) |
| Products | 25 | [#products](#products) |
| Pull Requests | 5 | [#pull-requests](#pull-requests) |
| Quotes | 20 | [#quotes](#quotes) |
| Safety | 4 | [#safety](#safety) |
| Translations | 8 | [#translations](#translations) |
| Webhooks | 11 | [#webhooks](#webhooks) |

## Quick reference (all operations)

| Tag | Method | Path | Summary |
| --- | --- | --- | --- |
| Analytics | GET | `/api/v1/analytics/option-selections` | List option selection facts |
| Analytics | GET | `/api/v1/analytics/part-usage` | List part usage facts |
| Analytics | GET | `/api/v1/analytics/pipeline` | List pipeline snapshots |
| Analytics | GET | `/api/v1/analytics/quotes` | List quote analytics |
| API Keys | GET | `/api/v1/api-keys` | List API keys |
| API Keys | GET | `/api/v1/api-keys/usage` | Get API key usage statistics |
| API Keys | GET | `/api/v1/api-keys/{id}` | Get an API key |
| Area Groups | GET | `/api/v1/area-groups` | List area groups |
| Area Groups | POST | `/api/v1/area-groups` | Create an area group |
| Area Groups | GET | `/api/v1/area-groups/{id}` | Get an area group |
| Area Groups | PUT | `/api/v1/area-groups/{id}` | Update an area group |
| Area Groups | PATCH | `/api/v1/area-groups/{id}` | Partially update an area group |
| Area Groups | DELETE | `/api/v1/area-groups/{id}` | Delete an area group |
| Area Groups | GET | `/api/v1/area-groups/{id}/areas` | List areas in an area group |
| Areas | GET | `/api/v1/areas` | List areas |
| Areas | POST | `/api/v1/areas` | Create an area |
| Areas | GET | `/api/v1/areas/library` | List library areas |
| Areas | GET | `/api/v1/areas/{areaId}/options` | List area options |
| Areas | GET | `/api/v1/areas/{areaId}/price-overrides` | List area price overrides |
| Areas | POST | `/api/v1/areas/{areaId}/price-overrides` | Create area price override |
| Areas | POST | `/api/v1/areas/{areaId}/price-overrides/replace` | Replace all area price overrides |
| Areas | PUT | `/api/v1/areas/{areaId}/price-overrides/{overrideId}` | Update area price override |
| Areas | PATCH | `/api/v1/areas/{areaId}/price-overrides/{overrideId}` | Partially update area price override |
| Areas | DELETE | `/api/v1/areas/{areaId}/price-overrides/{overrideId}` | Delete area price override |
| Areas | GET | `/api/v1/areas/{id}` | Get an area |
| Areas | PUT | `/api/v1/areas/{id}` | Update an area |
| Areas | PATCH | `/api/v1/areas/{id}` | Partially update an area |
| Areas | DELETE | `/api/v1/areas/{id}` | Delete an area |
| Areas | GET | `/api/v1/areas/{id}/content` | Get area rich content |
| Areas | PUT | `/api/v1/areas/{id}/content` | Update area rich content |
| Areas | DELETE | `/api/v1/areas/{id}/content` | Delete area rich content |
| Areas | POST | `/api/v1/areas/{id}/content/images` | Upload content image |
| Areas | GET | `/api/v1/areas/{id}/groups` | List groups in an area |
| Attributes | GET | `/api/v1/attributes` | List technical attributes |
| Attributes | POST | `/api/v1/attributes` | Create an attribute |
| Attributes | PUT | `/api/v1/attributes/values/{id}` | Update an attribute value |
| Attributes | PATCH | `/api/v1/attributes/values/{id}` | Partially update an attribute value |
| Attributes | DELETE | `/api/v1/attributes/values/{id}` | Delete an attribute value |
| Attributes | GET | `/api/v1/attributes/{id}` | Get an attribute |
| Attributes | PUT | `/api/v1/attributes/{id}` | Update an attribute |
| Attributes | PATCH | `/api/v1/attributes/{id}` | Partially update an attribute |
| Attributes | DELETE | `/api/v1/attributes/{id}` | Delete an attribute |
| Attributes | GET | `/api/v1/attributes/{id}/values` | List attribute values |
| Attributes | POST | `/api/v1/attributes/{id}/values` | Create an attribute value |
| Baselines | GET | `/api/v1/baselines` | List baselines |
| Baselines | POST | `/api/v1/baselines` | Create a baseline |
| Baselines | GET | `/api/v1/baselines/{id}` | Get a baseline |
| Baselines | DELETE | `/api/v1/baselines/{id}` | Delete a baseline |
| Batch | POST | `/api/v1/areas/batch` | Batch areas operations |
| Batch | POST | `/api/v1/batch` | Universal batch operations |
| Batch | POST | `/api/v1/bom/batch` | Batch bom operations |
| Batch | POST | `/api/v1/customers/batch` | Batch customers operations |
| Batch | POST | `/api/v1/groups/batch` | Batch groups operations |
| Batch | POST | `/api/v1/options/batch` | Batch options operations |
| Batch | POST | `/api/v1/parts/batch` | Batch parts operations |
| Batch | POST | `/api/v1/products/batch` | Batch products operations |
| Branches | GET | `/api/v1/branches` | List branches |
| Branches | POST | `/api/v1/branches` | Create branch |
| Branches | GET | `/api/v1/branches/{branchId}` | Get branch |
| Branches | DELETE | `/api/v1/branches/{branchId}` | Delete branch |
| Catalog Filters | GET | `/api/v1/catalog-filters` | List catalog filter dimensions |
| Catalog Filters | POST | `/api/v1/catalog-filters` | Create a catalog filter dimension |
| Catalog Filters | POST | `/api/v1/catalog-filters/reorder` | Reorder catalog filter dimensions |
| Catalog Filters | GET | `/api/v1/catalog-filters/{id}` | Get a catalog filter dimension |
| Catalog Filters | PUT | `/api/v1/catalog-filters/{id}` | Update a catalog filter dimension |
| Catalog Filters | DELETE | `/api/v1/catalog-filters/{id}` | Delete a catalog filter dimension |
| Catalog Filters | POST | `/api/v1/catalog-filters/{id}/values` | Add a value to a catalog filter dimension |
| Catalog Filters | POST | `/api/v1/catalog-filters/{id}/values/reorder` | Reorder values within a dimension |
| Catalog Filters | PUT | `/api/v1/catalog-filters/{id}/values/{valueId}` | Update a catalog filter value |
| Catalog Filters | DELETE | `/api/v1/catalog-filters/{id}/values/{valueId}` | Delete a catalog filter value |
| Change Orders | GET | `/api/v1/change-orders/{ecoId}` | Get change order |
| Change Orders | PUT | `/api/v1/change-orders/{ecoId}` | Update change order |
| Change Orders | PATCH | `/api/v1/change-orders/{ecoId}` | Partially update change order |
| Change Orders | DELETE | `/api/v1/change-orders/{ecoId}` | Delete change order |
| Change Orders | GET | `/api/v1/change-orders/{ecoId}/approvals` | List change approvals |
| Change Orders | POST | `/api/v1/change-orders/{ecoId}/approvals` | Create change approval |
| Change Orders | PUT | `/api/v1/change-orders/{ecoId}/approvals/{approvalId}` | Update change approval |
| Change Orders | PATCH | `/api/v1/change-orders/{ecoId}/approvals/{approvalId}` | Partially update change approval |
| Change Orders | GET | `/api/v1/change-orders/{ecoId}/impacts` | List change impacts |
| Change Orders | POST | `/api/v1/change-orders/{ecoId}/impacts` | Create change impact |
| Change Orders | PUT | `/api/v1/change-orders/{ecoId}/impacts/{impactId}` | Update change impact |
| Change Orders | PATCH | `/api/v1/change-orders/{ecoId}/impacts/{impactId}` | Partially update change impact |
| Change Orders | DELETE | `/api/v1/change-orders/{ecoId}/impacts/{impactId}` | Delete change impact |
| Change Requests | GET | `/api/v1/change-requests` | List change requests |
| Change Requests | POST | `/api/v1/change-requests` | Create change request |
| Change Requests | GET | `/api/v1/change-requests/{ecrId}` | Get change request |
| Change Requests | PUT | `/api/v1/change-requests/{ecrId}` | Update change request |
| Change Requests | PATCH | `/api/v1/change-requests/{ecrId}` | Partially update change request |
| Change Requests | DELETE | `/api/v1/change-requests/{ecrId}` | Delete change request |
| Change Requests | GET | `/api/v1/change-requests/{ecrId}/orders` | List change orders for request |
| Change Requests | POST | `/api/v1/change-requests/{ecrId}/orders` | Create change order |
| Company | GET | `/api/v1/company` | Get company settings |
| Company | PUT | `/api/v1/company` | Update company settings |
| Company | PATCH | `/api/v1/company` | Partially update company settings |
| Company | GET | `/api/v1/company/configurator-settings` | Get configurator settings |
| Company | PUT | `/api/v1/company/configurator-settings` | Update configurator settings |
| Company | PATCH | `/api/v1/company/configurator-settings` | Partially update configurator settings |
| Company | GET | `/api/v1/company/connector-settings` | Get connector settings |
| Company | PUT | `/api/v1/company/connector-settings` | Update connector settings |
| Company | PATCH | `/api/v1/company/connector-settings` | Partially update connector settings |
| Company | GET | `/api/v1/company/contacts` | List company contacts |
| Company | POST | `/api/v1/company/contacts` | Create a company contact |
| Company | PUT | `/api/v1/company/contacts/{id}` | Update a company contact |
| Company | PATCH | `/api/v1/company/contacts/{id}` | Partially update a company contact |
| Company | DELETE | `/api/v1/company/contacts/{id}` | Delete a company contact |
| Configurations | GET | `/api/v1/configurations` | List saved configurations |
| Configurations | POST | `/api/v1/configurations/calculate` | Calculate a configuration |
| Configurations | GET | `/api/v1/configurations/states/by-code/{code}` | Get configuration state by code |
| Configurations | GET | `/api/v1/configurations/states/by-code/{code}/parts` | Get configured parts (BOM) |
| Configurations | GET | `/api/v1/configurations/states/by-code/{code}/selections` | Get enriched selected options |
| Configurations | GET | `/api/v1/configurations/states/{hash}` | Get configuration state by hash |
| Configurations | GET | `/api/v1/configurations/{id}` | Get a saved configuration |
| Configurations | POST | `/api/v1/configurations/{id}/finalize` | Finalize a configuration |
| Connectors | GET | `/api/v1/connectors` | List connectors |
| Connectors | POST | `/api/v1/connectors` | Create a connector |
| Connectors | DELETE | `/api/v1/connectors/endpoints/{id}` | Delete a connector endpoint |
| Connectors | GET | `/api/v1/connectors/jobs` | List connector jobs |
| Connectors | GET | `/api/v1/connectors/jobs/{id}` | Get a connector job |
| Connectors | POST | `/api/v1/connectors/jobs/{id}/replay` | Replay a connector job |
| Connectors | GET | `/api/v1/connectors/jobs/{jobId}/logs` | List job logs |
| Connectors | GET | `/api/v1/connectors/tasks/{id}` | Get a connector task |
| Connectors | DELETE | `/api/v1/connectors/tasks/{id}` | Delete a connector task |
| Connectors | POST | `/api/v1/connectors/tasks/{id}/run` | Run a connector task |
| Connectors | GET | `/api/v1/connectors/triggers` | List connector triggers |
| Connectors | POST | `/api/v1/connectors/triggers` | Create a connector trigger |
| Connectors | PUT | `/api/v1/connectors/triggers/{id}` | Update a connector trigger |
| Connectors | DELETE | `/api/v1/connectors/triggers/{id}` | Delete a connector trigger |
| Connectors | GET | `/api/v1/connectors/{id}` | Get a connector |
| Connectors | PUT | `/api/v1/connectors/{id}` | Update a connector |
| Connectors | PATCH | `/api/v1/connectors/{id}` | Partially update a connector |
| Connectors | DELETE | `/api/v1/connectors/{id}` | Delete a connector |
| Connectors | GET | `/api/v1/connectors/{id}/endpoints` | List connector endpoints |
| Connectors | POST | `/api/v1/connectors/{id}/endpoints` | Create a connector endpoint |
| Connectors | GET | `/api/v1/connectors/{id}/tasks` | List connector tasks |
| Connectors | POST | `/api/v1/connectors/{id}/tasks` | Create a connector task |
| Constraints | GET | `/api/v1/constraints` | List option-level forbidden combinations |
| Constraints | POST | `/api/v1/constraints` | Replace option-level forbidden combinations |
| Constraints | GET | `/api/v1/constraints/area` | List area-level forbidden combinations |
| Constraints | POST | `/api/v1/constraints/area` | Replace area-level forbidden combinations |
| Constraints | POST | `/api/v1/constraints/check` | Check if a combination is forbidden |
| Constraints | GET | `/api/v1/constraints/combination-rules` | List combination rules |
| Constraints | POST | `/api/v1/constraints/combination-rules` | Create a combination rule |
| Constraints | GET | `/api/v1/constraints/combination-rules/{id}` | Get a combination rule |
| Constraints | PUT | `/api/v1/constraints/combination-rules/{id}` | Update a combination rule |
| Constraints | DELETE | `/api/v1/constraints/combination-rules/{id}` | Delete a combination rule |
| Constraints | GET | `/api/v1/constraints/rules` | List constraint rules |
| Constraints | POST | `/api/v1/constraints/rules` | Create a constraint rule |
| Constraints | GET | `/api/v1/constraints/rules/{id}` | Get a constraint rule |
| Constraints | PUT | `/api/v1/constraints/rules/{id}` | Update a constraint rule |
| Constraints | PATCH | `/api/v1/constraints/rules/{id}` | Partially update a constraint rule |
| Constraints | DELETE | `/api/v1/constraints/rules/{id}` | Delete a constraint rule |
| Customer Links | GET | `/api/v1/customer-links` | List customer links |
| Customer Links | POST | `/api/v1/customer-links` | Create a customer link |
| Customer Links | GET | `/api/v1/customer-links/{id}` | Get a customer link |
| Customer Links | PUT | `/api/v1/customer-links/{id}` | Update a customer link |
| Customer Links | PATCH | `/api/v1/customer-links/{id}` | Partially update a customer link |
| Customer Links | DELETE | `/api/v1/customer-links/{id}` | Delete a customer link |
| Customers | GET | `/api/v1/customers` | List customers |
| Customers | POST | `/api/v1/customers` | Create a customer |
| Customers | GET | `/api/v1/customers/search` | Search customers |
| Customers | GET | `/api/v1/customers/{customerId}/configurations` | List customer configurations |
| Customers | GET | `/api/v1/customers/{customerId}/opportunities` | List customer opportunities |
| Customers | GET | `/api/v1/customers/{customerId}/quotes` | List customer quotes |
| Customers | GET | `/api/v1/customers/{id}` | Get a customer |
| Customers | PUT | `/api/v1/customers/{id}` | Update a customer |
| Customers | PATCH | `/api/v1/customers/{id}` | Partially update a customer |
| Customers | DELETE | `/api/v1/customers/{id}` | Delete a customer |
| Customers | GET | `/api/v1/customers/{id}/contacts` | List contacts for a customer |
| Customers | POST | `/api/v1/customers/{id}/contacts` | Add a contact to a customer |
| Customers | PUT | `/api/v1/customers/{id}/contacts/{contact_id}` | Update a contact |
| Customers | DELETE | `/api/v1/customers/{id}/contacts/{contact_id}` | Remove a contact |
| Documents | POST | `/api/v1/documents/conditions/preview` | Preview condition evaluation |
| Documents | GET | `/api/v1/documents/content-blocks` | List content blocks |
| Documents | POST | `/api/v1/documents/content-blocks` | Create a content block |
| Documents | POST | `/api/v1/documents/content-blocks/batch` | Batch content block operations |
| Documents | POST | `/api/v1/documents/content-blocks/images` | Upload EditorJS image |
| Documents | DELETE | `/api/v1/documents/content-blocks/images` | Delete EditorJS image by URL |
| Documents | GET | `/api/v1/documents/content-blocks/{id}` | Get a content block with locales |
| Documents | PUT | `/api/v1/documents/content-blocks/{id}` | Update a content block |
| Documents | DELETE | `/api/v1/documents/content-blocks/{id}` | Delete a content block |
| Documents | GET | `/api/v1/documents/content-blocks/{id}/locales` | List content block locales |
| Documents | POST | `/api/v1/documents/content-blocks/{id}/locales` | Create or upsert a content block locale |
| Documents | GET | `/api/v1/documents/content-blocks/{id}/locales/{locale_id}` | Get a content block locale |
| Documents | PUT | `/api/v1/documents/content-blocks/{id}/locales/{locale_id}` | Update a content block locale |
| Documents | DELETE | `/api/v1/documents/content-blocks/{id}/locales/{locale_id}` | Delete a content block locale |
| Documents | POST | `/api/v1/documents/content-blocks/{id}/locales/{locale_id}/translate` | Translate locale to target language |
| Documents | POST | `/api/v1/documents/content-blocks/{id}/set-version` | Set current version |
| Documents | GET | `/api/v1/documents/content-directories` | List content directories (tree) |
| Documents | POST | `/api/v1/documents/content-directories` | Create a content directory |
| Documents | GET | `/api/v1/documents/content-directories/{id}` | Get a content directory |
| Documents | PUT | `/api/v1/documents/content-directories/{id}` | Update a content directory |
| Documents | DELETE | `/api/v1/documents/content-directories/{id}` | Delete a content directory |
| Documents | GET | `/api/v1/documents/doc-types` | List registered document types |
| Documents | GET | `/api/v1/documents/instances` | List document instances |
| Documents | POST | `/api/v1/documents/instances` | Create a document instance (enriched) |
| Documents | GET | `/api/v1/documents/instances/{id}` | Get a document instance |
| Documents | DELETE | `/api/v1/documents/instances/{id}` | Delete a document instance |
| Documents | GET | `/api/v1/documents/instances/{id}/attachments` | List instance attachments |
| Documents | POST | `/api/v1/documents/instances/{id}/attachments` | Create instance attachment |
| Documents | GET | `/api/v1/documents/instances/{id}/attachments/{att_id}` | Get an instance attachment |
| Documents | PUT | `/api/v1/documents/instances/{id}/attachments/{att_id}` | Update instance attachment |
| Documents | DELETE | `/api/v1/documents/instances/{id}/attachments/{att_id}` | Delete instance attachment |
| Documents | GET | `/api/v1/documents/instances/{id}/blocks` | List instance blocks (tree) |
| Documents | POST | `/api/v1/documents/instances/{id}/blocks` | Create an instance block |
| Documents | GET | `/api/v1/documents/instances/{id}/blocks/{block_id}` | Get an instance block |
| Documents | PUT | `/api/v1/documents/instances/{id}/blocks/{block_id}` | Update an instance block |
| Documents | DELETE | `/api/v1/documents/instances/{id}/blocks/{block_id}` | Delete an instance block |
| Documents | GET | `/api/v1/documents/instances/{id}/public-links` | List public links |
| Documents | GET | `/api/v1/documents/instances/{id}/public-links/{link_id}` | Get a public link |
| Documents | DELETE | `/api/v1/documents/instances/{id}/public-links/{link_id}` | Delete a public link |
| Documents | POST | `/api/v1/documents/instances/{id}/publish` | Publish document instance |
| Documents | POST | `/api/v1/documents/renders/document` | Render a document instance PDF |
| Documents | POST | `/api/v1/documents/renders/offer` | Render an offer PDF |
| Documents | POST | `/api/v1/documents/renders/quote` | Render a quote PDF |
| Documents | GET | `/api/v1/documents/renders/{job_id}` | Get render job status |
| Documents | DELETE | `/api/v1/documents/renders/{job_id}` | Invalidate a render job |
| Documents | GET | `/api/v1/documents/renders/{job_id}/content` | Stream rendered PDF bytes |
| Documents | GET | `/api/v1/documents/templates` | List document templates |
| Documents | POST | `/api/v1/documents/templates` | Create a document template |
| Documents | GET | `/api/v1/documents/templates/resolve` | Preview template resolution |
| Documents | GET | `/api/v1/documents/templates/{id}` | Get a document template |
| Documents | PUT | `/api/v1/documents/templates/{id}` | Update a document template |
| Documents | PATCH | `/api/v1/documents/templates/{id}` | Partially update a document template |
| Documents | DELETE | `/api/v1/documents/templates/{id}` | Delete a document template |
| Documents | POST | `/api/v1/documents/templates/{id}/assign-products` | Assign a template to products |
| Documents | POST | `/api/v1/documents/templates/{id}/clone` | Deep clone a template |
| Documents | POST | `/api/v1/documents/templates/{id}/publish` | Publish a template |
| Documents | GET | `/api/v1/documents/templates/{id}/resolve` | Get the resolved template tree |
| Documents | GET | `/api/v1/documents/templates/{id}/structure` | Get template structure tree |
| Documents | POST | `/api/v1/documents/templates/{id}/structure/batch` | Batch structure operations |
| Documents | POST | `/api/v1/documents/templates/{id}/structure/blocks` | Create a structure block |
| Documents | GET | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}` | Get a structure block |
| Documents | PUT | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}` | Update a structure block |
| Documents | DELETE | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}` | Delete a structure block (cascade) |
| Documents | GET | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments` | List block attachments |
| Documents | POST | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments` | Attach content block |
| Documents | POST | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments/reorder` | Reorder attachments |
| Documents | GET | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments/{att_id}` | Get an attachment |
| Documents | PUT | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments/{att_id}` | Update an attachment |
| Documents | DELETE | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments/{att_id}` | Remove an attachment |
| Documents | GET | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}/locales` | List structure block locales |
| Documents | PUT | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}/locales/{lang}` | Upsert structure block locale title |
| Documents | DELETE | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}/locales/{lang}` | Delete structure block locale |
| Documents | POST | `/api/v1/documents/templates/{id}/structure/blocks/{block_id}/move` | Move block to new parent |
| Documents | POST | `/api/v1/documents/templates/{id}/structure/reorder` | Reorder structure blocks |
| Documents | POST | `/api/v1/documents/templates/{id}/translate` | Translate entire template |
| Documents | POST | `/api/v1/documents/templates/{id}/unpublish` | Unpublish a template |
| Documents | GET | `/api/v1/documents/templates/{id}/validate-config` | Validate a configuration against a template |
| Documents | POST | `/api/v1/documents/templates/{id}/variants` | Create an inheritance variant |
| Export | GET | `/api/v1/customers/export` | Export customers (NDJSON) |
| Export | GET | `/api/v1/parts/export` | Export parts (NDJSON) |
| Export | GET | `/api/v1/products/export` | Export products (NDJSON) |
| Groups | GET | `/api/v1/groups` | List groups |
| Groups | POST | `/api/v1/groups` | Create a group |
| Groups | GET | `/api/v1/groups/{id}` | Get a group |
| Groups | PUT | `/api/v1/groups/{id}` | Update a group |
| Groups | PATCH | `/api/v1/groups/{id}` | Partially update a group |
| Groups | DELETE | `/api/v1/groups/{id}` | Delete a group |
| Groups | GET | `/api/v1/groups/{id}/areas` | List areas linked to a group |
| Groups | POST | `/api/v1/groups/{id}/areas` | Link a group to areas |
| Groups | DELETE | `/api/v1/groups/{id}/areas/{area_id}` | Unlink a group from an area |
| Groups | POST | `/api/v1/groups/{id}/duplicate` | Duplicate a group |
| Groups | GET | `/api/v1/groups/{id}/options` | List options in a group |
| Images | POST | `/api/v1/areas/{areaId}/image` | Upload area image |
| Images | DELETE | `/api/v1/areas/{areaId}/image` | Delete area image |
| Images | POST | `/api/v1/options/{optionId}/image` | Upload option image |
| Images | DELETE | `/api/v1/options/{optionId}/image` | Delete option image |
| Images | POST | `/api/v1/options/{optionId}/image/areas/{areaId}` | Upload option area override image |
| Images | DELETE | `/api/v1/options/{optionId}/image/areas/{areaId}` | Delete option area override image |
| Images | POST | `/api/v1/products/{productId}/background` | Upload product background |
| Images | DELETE | `/api/v1/products/{productId}/background` | Delete product background |
| Images | GET | `/api/v1/products/{productId}/gallery` | List gallery images |
| Images | POST | `/api/v1/products/{productId}/gallery` | Upload gallery image |
| Images | POST | `/api/v1/products/{productId}/gallery/reorder` | Reorder gallery images |
| Images | GET | `/api/v1/products/{productId}/gallery/{imageId}` | Get gallery image |
| Images | PUT | `/api/v1/products/{productId}/gallery/{imageId}` | Replace gallery image |
| Images | DELETE | `/api/v1/products/{productId}/gallery/{imageId}` | Delete gallery image |
| Images | POST | `/api/v1/products/{productId}/image` | Upload product image |
| Images | DELETE | `/api/v1/products/{productId}/image` | Delete product image |
| Inbound Webhooks | POST | `/api/v1/inbound/connectors/tasks/{id}/trigger` | Trigger a connector task |
| Inbound Webhooks | POST | `/api/v1/inbound/customers` | Upsert an inbound customer |
| Inbound Webhooks | POST | `/api/v1/inbound/customers/batch` | Batch upsert inbound customers |
| Inbound Webhooks | POST | `/api/v1/inbound/events` | Send an inbound event |
| Inbound Webhooks | POST | `/api/v1/inbound/opportunities` | Create an inbound opportunity |
| Inbound Webhooks | POST | `/api/v1/inbound/parts/batch` | Batch upsert inbound parts |
| Inbound Webhooks | POST | `/api/v1/inbound/triggers/{suffix}` | Fire a webhook trigger by path |
| Item Revisions | GET | `/api/v1/parts/{partId}/revisions` | List revisions for a part |
| Item Revisions | POST | `/api/v1/parts/{partId}/revisions` | Create a revision |
| Item Revisions | GET | `/api/v1/parts/{partId}/revisions/{revisionId}` | Get a revision |
| Item Revisions | PUT | `/api/v1/parts/{partId}/revisions/{revisionId}` | Update a draft revision |
| Item Revisions | DELETE | `/api/v1/parts/{partId}/revisions/{revisionId}` | Delete a draft revision |
| Item Revisions | POST | `/api/v1/parts/{partId}/revisions/{revisionId}/obsolete` | Obsolete a revision |
| Item Revisions | POST | `/api/v1/parts/{partId}/revisions/{revisionId}/release` | Release a revision |
| Languages | GET | `/api/v1/languages` | List languages |
| Languages | POST | `/api/v1/languages` | Create a language |
| Languages | POST | `/api/v1/languages/reorder` | Reorder languages |
| Languages | GET | `/api/v1/languages/{id}` | Get a language |
| Languages | PUT | `/api/v1/languages/{id}` | Update a language |
| Languages | PATCH | `/api/v1/languages/{id}` | Partially update a language |
| Languages | DELETE | `/api/v1/languages/{id}` | Delete a language |
| Opportunities | GET | `/api/v1/opportunities` | List opportunities |
| Opportunities | POST | `/api/v1/opportunities` | Create an opportunity |
| Opportunities | GET | `/api/v1/opportunities/{id}` | Get an opportunity |
| Opportunities | PUT | `/api/v1/opportunities/{id}` | Update an opportunity |
| Opportunities | PATCH | `/api/v1/opportunities/{id}` | Partially update an opportunity |
| Opportunities | DELETE | `/api/v1/opportunities/{id}` | Delete an opportunity |
| Opportunities | GET | `/api/v1/opportunities/{id}/quotes` | List quotes for an opportunity |
| Options | GET | `/api/v1/options` | List options |
| Options | POST | `/api/v1/options` | Create an option |
| Options | GET | `/api/v1/options/{id}` | Get an option |
| Options | PUT | `/api/v1/options/{id}` | Update an option |
| Options | PATCH | `/api/v1/options/{id}` | Partially update an option |
| Options | DELETE | `/api/v1/options/{id}` | Delete an option |
| Options | GET | `/api/v1/options/{id}/effective` | Get effective price for an option |
| Options | GET | `/api/v1/options/{optionId}/advanced-prices` | List advanced prices |
| Options | POST | `/api/v1/options/{optionId}/advanced-prices` | Create an advanced price |
| Options | PUT | `/api/v1/options/{optionId}/advanced-prices/{priceId}` | Update an advanced price |
| Options | PATCH | `/api/v1/options/{optionId}/advanced-prices/{priceId}` | Partially update an advanced price |
| Options | DELETE | `/api/v1/options/{optionId}/advanced-prices/{priceId}` | Delete an advanced price |
| Options | GET | `/api/v1/options/{optionId}/area-config` | Get area-specific config for an option |
| Options | PUT | `/api/v1/options/{optionId}/area-config` | Set area-specific config for an option |
| Options | DELETE | `/api/v1/options/{optionId}/area-config` | Clear area-specific config for an option |
| Part Documents | GET | `/api/v1/part-documents` | List part documents |
| Part Documents | POST | `/api/v1/part-documents` | Create a part document |
| Part Documents | GET | `/api/v1/part-documents/{id}` | Get a part document |
| Part Documents | PUT | `/api/v1/part-documents/{id}` | Update a part document |
| Part Documents | PATCH | `/api/v1/part-documents/{id}` | Partially update a part document |
| Part Documents | DELETE | `/api/v1/part-documents/{id}` | Delete a part document |
| Part Documents | GET | `/api/v1/parts/{partId}/document-links` | List document links for a part |
| Part Documents | POST | `/api/v1/parts/{partId}/document-links` | Create a document link for a part |
| Part Documents | DELETE | `/api/v1/parts/{partId}/document-links/{linkId}` | Remove a document link |
| Part Documents | GET | `/api/v1/parts/{partId}/revisions/{revisionId}/document-links` | List document links for a revision |
| Part Documents | POST | `/api/v1/parts/{partId}/revisions/{revisionId}/document-links` | Create a document link for a revision |
| Parts | GET | `/api/v1/areas/{id}/placements` | List placements on an area |
| Parts | GET | `/api/v1/parts` | List parts |
| Parts | POST | `/api/v1/parts` | Create a part |
| Parts | PUT | `/api/v1/parts/bom/{id}` | Update a BOM item |
| Parts | PATCH | `/api/v1/parts/bom/{id}` | Partially update a BOM item |
| Parts | DELETE | `/api/v1/parts/bom/{id}` | Delete a BOM item |
| Parts | GET | `/api/v1/parts/ghosts` | List ghost parts |
| Parts | GET | `/api/v1/parts/groups` | List part groups |
| Parts | POST | `/api/v1/parts/groups` | Create part group |
| Parts | GET | `/api/v1/parts/groups/{groupId}` | Get part group |
| Parts | PUT | `/api/v1/parts/groups/{groupId}` | Update part group |
| Parts | PATCH | `/api/v1/parts/groups/{groupId}` | Partially update part group |
| Parts | DELETE | `/api/v1/parts/groups/{groupId}` | Delete part group |
| Parts | PUT | `/api/v1/parts/placements/{id}` | Update a part placement |
| Parts | PATCH | `/api/v1/parts/placements/{id}` | Partially update a part placement |
| Parts | DELETE | `/api/v1/parts/placements/{id}` | Delete a part placement |
| Parts | GET | `/api/v1/parts/{id}` | Get a part |
| Parts | PUT | `/api/v1/parts/{id}` | Update a part |
| Parts | PATCH | `/api/v1/parts/{id}` | Partially update a part |
| Parts | DELETE | `/api/v1/parts/{id}` | Delete a part |
| Parts | GET | `/api/v1/parts/{id}/bom` | List BOM children |
| Parts | POST | `/api/v1/parts/{id}/bom` | Add a BOM child |
| Parts | POST | `/api/v1/parts/{id}/bom/explode` | Explode a BOM tree |
| Parts | GET | `/api/v1/parts/{id}/bom/flat` | Get flattened BOM |
| Parts | GET | `/api/v1/parts/{id}/bom/tree` | Get multi-level BOM tree |
| Parts | POST | `/api/v1/parts/{id}/bom/validate` | Validate BOM integrity |
| Parts | POST | `/api/v1/parts/{id}/ghost/materialize` | Materialize a ghost assembly |
| Parts | POST | `/api/v1/parts/{id}/ghost/resolve` | Resolve a ghost assembly |
| Parts | GET | `/api/v1/parts/{id}/ghost/status` | Get ghost status for a part |
| Parts | GET | `/api/v1/parts/{id}/placements` | List part placements |
| Parts | POST | `/api/v1/parts/{id}/placements` | Create a part placement |
| Parts | GET | `/api/v1/parts/{id}/where-used` | Find where a part is used |
| Parts | GET | `/api/v1/parts/{partId}/changelog` | List part changelog |
| Price Lists | GET | `/api/v1/price-lists` | List price lists |
| Price Lists | POST | `/api/v1/price-lists` | Create a price list |
| Price Lists | POST | `/api/v1/price-lists/reorder` | Reorder price lists |
| Price Lists | GET | `/api/v1/price-lists/{id}` | Get a price list |
| Price Lists | PUT | `/api/v1/price-lists/{id}` | Update a price list |
| Price Lists | PATCH | `/api/v1/price-lists/{id}` | Partially update a price list |
| Price Lists | DELETE | `/api/v1/price-lists/{id}` | Delete a price list |
| Price Lists | GET | `/api/v1/price-lists/{priceListId}/overrides` | List price list overrides |
| Price Overrides | GET | `/api/v1/options/{optionId}/price-overrides` | List price overrides for an option |
| Price Overrides | POST | `/api/v1/options/{optionId}/price-overrides` | Create a price override |
| Price Overrides | POST | `/api/v1/options/{optionId}/price-overrides/replace` | Replace all price overrides |
| Price Overrides | PUT | `/api/v1/options/{optionId}/price-overrides/{overrideId}` | Update a price override |
| Price Overrides | PATCH | `/api/v1/options/{optionId}/price-overrides/{overrideId}` | Partially update a price override |
| Price Overrides | DELETE | `/api/v1/options/{optionId}/price-overrides/{overrideId}` | Delete a price override |
| Product Media | GET | `/api/v1/products/{productId}/models` | List 3D model links |
| Product Media | POST | `/api/v1/products/{productId}/models` | Create 3D model link |
| Product Media | POST | `/api/v1/products/{productId}/models/reorder` | Reorder 3D model links |
| Product Media | PUT | `/api/v1/products/{productId}/models/{modelId}` | Update 3D model link |
| Product Media | DELETE | `/api/v1/products/{productId}/models/{modelId}` | Delete 3D model link |
| Product Media | GET | `/api/v1/products/{productId}/videos` | List video links |
| Product Media | POST | `/api/v1/products/{productId}/videos` | Create video link |
| Product Media | POST | `/api/v1/products/{productId}/videos/reorder` | Reorder video links |
| Product Media | PUT | `/api/v1/products/{productId}/videos/{videoId}` | Update video link |
| Product Media | DELETE | `/api/v1/products/{productId}/videos/{videoId}` | Delete video link |
| Products | GET | `/api/v1/products` | List products |
| Products | POST | `/api/v1/products` | Create a product |
| Products | POST | `/api/v1/products/reorder` | Reorder products |
| Products | GET | `/api/v1/products/{id}` | Get a product |
| Products | PUT | `/api/v1/products/{id}` | Update a product |
| Products | PATCH | `/api/v1/products/{id}` | Partially update a product |
| Products | DELETE | `/api/v1/products/{id}` | Delete a product |
| Products | GET | `/api/v1/products/{productId}/areas` | List assigned areas |
| Products | POST | `/api/v1/products/{productId}/areas` | Assign an area to a product |
| Products | POST | `/api/v1/products/{productId}/areas/reorder` | Reorder product areas |
| Products | POST | `/api/v1/products/{productId}/areas/replace` | Replace all product area assignments |
| Products | DELETE | `/api/v1/products/{productId}/areas/{areaId}` | Remove area from product |
| Products | GET | `/api/v1/products/{productId}/configurations` | List product configurations |
| Products | GET | `/api/v1/products/{productId}/price-overrides` | List product price overrides |
| Products | POST | `/api/v1/products/{productId}/price-overrides` | Create product price override |
| Products | POST | `/api/v1/products/{productId}/price-overrides/replace` | Replace all product price overrides |
| Products | PUT | `/api/v1/products/{productId}/price-overrides/{overrideId}` | Update product price override |
| Products | PATCH | `/api/v1/products/{productId}/price-overrides/{overrideId}` | Partially update product price override |
| Products | DELETE | `/api/v1/products/{productId}/price-overrides/{overrideId}` | Delete product price override |
| Products | GET | `/api/v1/products/{productId}/pricing-presets` | List pricing presets |
| Products | POST | `/api/v1/products/{productId}/pricing-presets` | Create pricing preset |
| Products | POST | `/api/v1/products/{productId}/pricing-presets/reorder` | Reorder pricing presets |
| Products | PUT | `/api/v1/products/{productId}/pricing-presets/{presetId}` | Update pricing preset |
| Products | PATCH | `/api/v1/products/{productId}/pricing-presets/{presetId}` | Partially update pricing preset |
| Products | DELETE | `/api/v1/products/{productId}/pricing-presets/{presetId}` | Delete pricing preset |
| Pull Requests | GET | `/api/v1/branches/{branchId}/pull-requests` | List pull requests |
| Pull Requests | POST | `/api/v1/branches/{branchId}/pull-requests` | Create pull request |
| Pull Requests | GET | `/api/v1/pull-requests/{prId}` | Get pull request |
| Pull Requests | PUT | `/api/v1/pull-requests/{prId}` | Update pull request |
| Pull Requests | PATCH | `/api/v1/pull-requests/{prId}` | Partially update pull request |
| Quotes | GET | `/api/v1/quotes` | List quotes |
| Quotes | POST | `/api/v1/quotes` | Create a quote |
| Quotes | GET | `/api/v1/quotes/{id}` | Get a quote |
| Quotes | PUT | `/api/v1/quotes/{id}` | Update a quote |
| Quotes | PATCH | `/api/v1/quotes/{id}` | Partially update a quote |
| Quotes | DELETE | `/api/v1/quotes/{id}` | Delete a quote |
| Quotes | GET | `/api/v1/quotes/{id}/line-items` | List line items |
| Quotes | POST | `/api/v1/quotes/{id}/line-items` | Add a line item |
| Quotes | PUT | `/api/v1/quotes/{id}/line-items/{item_id}` | Update a line item |
| Quotes | PATCH | `/api/v1/quotes/{id}/line-items/{item_id}` | Partially update a line item |
| Quotes | DELETE | `/api/v1/quotes/{id}/line-items/{item_id}` | Remove a line item |
| Quotes | POST | `/api/v1/quotes/{id}/revise` | Create a new revision |
| Quotes | GET | `/api/v1/quotes/{id}/revisions` | List quote revisions |
| Quotes | PUT | `/api/v1/quotes/{id}/status` | Update quote status |
| Quotes | GET | `/api/v1/quotes/{quoteId}/contacts` | List quote contacts |
| Quotes | POST | `/api/v1/quotes/{quoteId}/contacts` | Add contact to quote |
| Quotes | DELETE | `/api/v1/quotes/{quoteId}/contacts/{contactId}` | Remove contact from quote |
| Quotes | GET | `/api/v1/quotes/{quoteId}/details` | Get quote details |
| Quotes | PUT | `/api/v1/quotes/{quoteId}/details` | Upsert quote details |
| Quotes | PATCH | `/api/v1/quotes/{quoteId}/details` | Partially update quote details |
| Safety | GET | `/api/v1/hp-statements` | List H/P statements |
| Safety | GET | `/api/v1/hp-statements/{code}` | Resolve an H/P statement |
| Safety | GET | `/api/v1/safety-logos` | List safety logos |
| Safety | GET | `/api/v1/safety-notices/signal-words` | List signal words |
| Translations | GET | `/api/v1/translations` | List translations |
| Translations | PUT | `/api/v1/translations` | Upsert translations |
| Translations | GET | `/api/v1/translations/dictionary` | List dictionary entries |
| Translations | POST | `/api/v1/translations/dictionary` | Create or update a dictionary entry |
| Translations | GET | `/api/v1/translations/dictionary/{entry_id}` | Get a dictionary entry |
| Translations | PUT | `/api/v1/translations/dictionary/{entry_id}` | Replace a dictionary entry |
| Translations | PATCH | `/api/v1/translations/dictionary/{entry_id}` | Partially update a dictionary entry |
| Translations | DELETE | `/api/v1/translations/dictionary/{entry_id}` | Delete a dictionary entry |
| Webhooks | GET | `/api/v1/webhooks` | List webhook subscriptions |
| Webhooks | POST | `/api/v1/webhooks` | Create a webhook subscription |
| Webhooks | GET | `/api/v1/webhooks/deliveries/{id}` | Get delivery detail |
| Webhooks | GET | `/api/v1/webhooks/events` | List available webhook events |
| Webhooks | GET | `/api/v1/webhooks/{id}` | Get a webhook subscription |
| Webhooks | PUT | `/api/v1/webhooks/{id}` | Update a webhook subscription |
| Webhooks | PATCH | `/api/v1/webhooks/{id}` | Partially update a webhook subscription |
| Webhooks | DELETE | `/api/v1/webhooks/{id}` | Delete a webhook subscription |
| Webhooks | GET | `/api/v1/webhooks/{id}/deliveries` | List delivery attempts |
| Webhooks | POST | `/api/v1/webhooks/{id}/rotate-secret` | Rotate webhook signing secret |
| Webhooks | POST | `/api/v1/webhooks/{id}/test` | Send a test event |

---

## Analytics

Read-only analytics: pipeline snapshots, quote analytics, option selection facts, and part usage facts. Scope: `analytics:read`.

### `GET /api/v1/analytics/option-selections` — List option selection facts
_operationId_: `listOptionSelectionFacts`

Query option selection analytics. Scope: `analytics:read`.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `from` (string) — Start date (ISO 8601, e.g. 2026-01-01)
- `to` (string) — End date (ISO 8601, e.g. 2026-03-31)
- `product_id` (integer) — Filter by product ID

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/analytics/part-usage` — List part usage facts
_operationId_: `listPartUsageFacts`

Query part usage analytics. Scope: `analytics:read`.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `from` (string) — Start date (ISO 8601, e.g. 2026-01-01)
- `to` (string) — End date (ISO 8601, e.g. 2026-03-31)
- `product_id` (integer) — Filter by product ID

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/analytics/pipeline` — List pipeline snapshots
_operationId_: `listPipelineSnapshots`

Query pipeline analytics snapshots (opportunity funnel data). Scope: `analytics:read`.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `from` (string) — Start date (ISO 8601, e.g. 2026-01-01)
- `to` (string) — End date (ISO 8601, e.g. 2026-03-31)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/analytics/quotes` — List quote analytics
_operationId_: `listQuoteAnalytics`

Query quote-level analytics snapshots. Scope: `analytics:read`.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `from` (string) — Start date (ISO 8601, e.g. 2026-01-01)
- `to` (string) — End date (ISO 8601, e.g. 2026-03-31)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## API Keys

Manage API keys for programmatic access. The plaintext key is shown only once at creation — store it securely. Requires session authentication for create/rotate/revoke operations. Scope: `api-keys:manage`.

### `GET /api/v1/api-keys` — List API keys
_operationId_: `listApiKeys`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/api-keys/usage` — Get API key usage statistics
_operationId_: `getApiKeyUsage`

Returns usage statistics for all API keys in the company, including active/inactive counts and per-key last-used timestamps.

**Responses:**
- `200` — Usage statistics
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/api-keys/{id}` — Get an API key
_operationId_: `getApiKey`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Area Groups

Named groups that organize areas within a product. Scope: `products:read`, `products:write`.

### `GET /api/v1/area-groups` — List area groups
_operationId_: `listAreaGroupResources`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `product_id` (integer) — Filter by product

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/area-groups` — Create an area group
_operationId_: `createAreaGroup`

**Request body:**
- `application/json` **required**
  - `description` (string)
  - `name` (string) **required**
  - `order_index` (integer)
  - `product_id` (integer) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/area-groups/{id}` — Get an area group
_operationId_: `getAreaGroup`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/area-groups/{id}` — Update an area group
_operationId_: `updateAreaGroup`

**Request body:**
- `application/json` **required**
  - `description` (string)
  - `name` (string)
  - `order_index` (integer)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/area-groups/{id}` — Partially update an area group
_operationId_: `patchAreaGroup`

**Request body:**
- `application/json` **required**
  - `description` (string)
  - `name` (string)
  - `order_index` (integer)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/area-groups/{id}` — Delete an area group
_operationId_: `deleteAreaGroup`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/area-groups/{id}/areas` — List areas in an area group
_operationId_: `listAreaGroupAreas`

Returns all areas belonging to this area group. Not paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Areas

Areas represent sections or modules within a product configuration (e.g., 'Exterior', 'Interior'). Each area contains option groups. Scope: `products:read`, `products:write`.

### `GET /api/v1/areas` — List areas
_operationId_: `listAreas`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `product_id` (integer) — Filter by product
- `search` (string) — Filter by name (case-insensitive partial match)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/areas` — Create an area
_operationId_: `createArea`

**Request body:**
- `application/json` **required** — schema: `AreaCreateRequest`
  - `allow_disable` (boolean)
  - `area_group_id` (object) — AreaGroup to assign this area to
  - `description` (string)
  - `language` (string)
  - `name` (string) **required**
  - `order_index` (object) — Position in area list (auto-assigned if omitted)
  - `price` (string)
  - `product_id` (object) — Product to assign this area to

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/areas/library` — List library areas
_operationId_: `listLibraryAreas`

List areas not assigned to any product. Not paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/areas/{areaId}/options` — List area options
_operationId_: `listAreaOptions`

List all options available in an area (across all groups assigned to it).

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/areas/{areaId}/price-overrides` — List area price overrides
_operationId_: `listAreaPriceOverrides`

List all price-list overrides for an area's base price.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/areas/{areaId}/price-overrides` — Create area price override
_operationId_: `createAreaPriceOverride`

**Request body:**
- `application/json` **required**
  - `override_price` (string) **required**
  - `price_list_id` (integer) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/areas/{areaId}/price-overrides/replace` — Replace all area price overrides
_operationId_: `replaceAreaPriceOverrides`

Bulk-replace all price-list overrides for an area.

**Request body:**
- `application/json` **required**
  - `overrides` (array<object>) **required**

**Responses:**
- `200` — Replaced
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/areas/{areaId}/price-overrides/{overrideId}` — Update area price override
_operationId_: `updateAreaPriceOverride`

**Request body:**
- `application/json` **required**
  - `override_price` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/areas/{areaId}/price-overrides/{overrideId}` — Partially update area price override
_operationId_: `patchAreaPriceOverride`

**Request body:**
- `application/json` **required**
  - `override_price` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/areas/{areaId}/price-overrides/{overrideId}` — Delete area price override
_operationId_: `deleteAreaPriceOverride`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/areas/{id}` — Get an area
_operationId_: `getArea`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/areas/{id}` — Update an area
_operationId_: `updateArea`

**Request body:**
- `application/json` **required** — schema: `AreaUpdateRequest`
  - `allow_disable` (object)
  - `area_group_id` (object) — AreaGroup to assign this area to (use 0 or null to unassign)
  - `description` (object)
  - `language` (object)
  - `name` (object)
  - `order_index` (object)
  - `price` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/areas/{id}` — Partially update an area
_operationId_: `patchArea`

**Request body:**
- `application/json` **required** — schema: `AreaUpdateRequest`
  - `allow_disable` (object)
  - `area_group_id` (object) — AreaGroup to assign this area to (use 0 or null to unassign)
  - `description` (object)
  - `language` (object)
  - `name` (object)
  - `order_index` (object)
  - `price` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/areas/{id}` — Delete an area
_operationId_: `deleteArea`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/areas/{id}/content` — Get area rich content
_operationId_: `getAreaContent`

Returns the EditorJS rich content blocks for an area. Supports all block types: header, paragraph, list, table, image, quote, delimiter, warning, embed, code, safety_notice, hp_statement.

**Query parameters:**
- `language` (string) — Language code (e.g. 'DE', 'EN')

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/areas/{id}/content` — Update area rich content
_operationId_: `updateAreaContent`

Create or replace rich content (EditorJS blocks) for an area. Image blocks should reference URLs obtained from the content image upload endpoint.

**Request body:**
- `application/json` **required** — schema: `AreaContentUpdateRequest`
  - `blocks` (array<object>) **required** — Array of EditorJS block objects. Each must have a 'type' and 'data' key.
  - `enabled` (boolean) — Whether this content is shown in the configurator
  - `language` (string) — Language code (e.g. 'DE', 'EN')

**Responses:**
- `200` — Success
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/areas/{id}/content` — Delete area rich content
_operationId_: `deleteAreaContent`

Delete rich content for an area. Pass `language` query param to delete a specific language; omit to delete all content.

**Query parameters:**
- `language` (string) — Language code to delete (omit for all)

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/areas/{id}/content/images` — Upload content image
_operationId_: `uploadAreaContentImage`

Upload an image for use in EditorJS content blocks. Accepts multipart/form-data with a 'file' field. Returns the URL to use in an image block's `data.file.url`.

**Responses:**
- `201` — Image uploaded
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `413` — Payload Too Large (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/areas/{id}/groups` — List groups in an area
_operationId_: `listAreaGroups`

Returns groups linked to this area. Not paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Attributes

Technical attributes (number, range, boolean, text) that can be attached to products, areas, or options for specification sheets and filtering. Scope: `products:read`, `products:write`.

### `GET /api/v1/attributes` — List technical attributes
_operationId_: `listAttributes`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/attributes` — Create an attribute
_operationId_: `createAttribute`

**Request body:**
- `application/json` **required** — schema: `AttributeCreateRequest`
  - `attr_type` (string) **required** — Attribute type: number, range, boolean, text
  - `name` (string) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/attributes/values/{id}` — Update an attribute value
_operationId_: `updateAttributeValue`

**Request body:**
- `application/json` **required**
  - `bool_value` (boolean)
  - `number_value` (number)
  - `range_max` (number)
  - `range_min` (number)
  - `text_value` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/attributes/values/{id}` — Partially update an attribute value
_operationId_: `patchAttributeValue`

**Request body:**
- `application/json` **required**
  - `bool_value` (boolean)
  - `number_value` (number)
  - `range_max` (number)
  - `range_min` (number)
  - `text_value` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/attributes/values/{id}` — Delete an attribute value
_operationId_: `deleteAttributeValue`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/attributes/{id}` — Get an attribute
_operationId_: `getAttribute`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/attributes/{id}` — Update an attribute
_operationId_: `updateAttribute`

**Request body:**
- `application/json` **required** — schema: `AttributeUpdateRequest`
  - `attr_type` (object)
  - `name` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/attributes/{id}` — Partially update an attribute
_operationId_: `patchAttribute`

**Request body:**
- `application/json` **required** — schema: `AttributeUpdateRequest`
  - `attr_type` (object)
  - `name` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/attributes/{id}` — Delete an attribute
_operationId_: `deleteAttribute`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/attributes/{id}/values` — List attribute values
_operationId_: `listAttributeValues`

**Query parameters:**
- `element_type` (string) — Filter: product, area, option
- `element_id` (integer) — Filter by element ID

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/attributes/{id}/values` — Create an attribute value
_operationId_: `createAttributeValue`

**Request body:**
- `application/json` **required**
  - `bool_value` (boolean)
  - `element_id` (integer) **required**
  - `element_type` (string) **required**
  - `number_value` (number)
  - `range_max` (number)
  - `range_min` (number)
  - `text_value` (string)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Baselines

Frozen snapshots of a product's part structure at a point in time. Used for engineering change management and audit trails. Scope: `parts:read`, `parts:write`.

### `GET /api/v1/baselines` — List baselines
_operationId_: `listBaselines`

**Query parameters:**
- `product_id` (integer) **required** — Product ID (required)

**Responses:**
- `200` — Success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/baselines` — Create a baseline
_operationId_: `createBaseline`

**Request body:**
- `application/json` **required** — schema: `BaselineCreateRequest`
  - `name` (string) **required**
  - `note` (object)
  - `product_id` (integer) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/baselines/{id}` — Get a baseline
_operationId_: `getBaseline`

Returns the baseline with its items.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/baselines/{id}` — Delete a baseline
_operationId_: `deleteBaseline`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Batch

Batch/bulk operations for creating, updating, deleting, or upserting multiple entities in a single request. Supports per-item error handling (partial success). Max 100 operations per request. Scope: varies by resource.

### `POST /api/v1/areas/batch` — Batch areas operations
_operationId_: `batchAreas`

Execute up to 100 create/update/delete/upsert operations on areas.

**Best-effort, not all-or-nothing.** Each operation is isolated in its own database savepoint, so successful items are committed even when others fail. The response body reports `total`, `succeeded`, `failed` and a per-item `results` array (each with its own status and error), so you can retry only the failed items. HTTP `200` means every item succeeded; `207` means at least one failed. A top-level `4xx` (e.g. malformed envelope or more than 100 operations) means nothing was applied.

Send `X-Idempotency-Key` to make a batch safe to retry: a replay with the same key and body returns the original response instead of re-applying it.

**Request body:**
- `application/json` **required** — schema: `ResourceBatchRequest`
  - `operations` (array<BatchOperationRequest>) **required** — List of operations (1–100)

**Responses:**
- `200` — All operations succeeded
- `207` — Partial success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/batch` — Universal batch operations
_operationId_: `universalBatch`

Execute multiple operations across different resource types in a single request. Max 100 operations.

**Best-effort, not all-or-nothing.** Each operation is isolated in its own database savepoint, so successful items are committed even when others fail. The response body reports `total`, `succeeded`, `failed` and a per-item `results` array (each with its own status and error), so you can retry only the failed items. HTTP `200` means every item succeeded; `207` means at least one failed. A top-level `4xx` (e.g. malformed envelope or more than 100 operations) means nothing was applied.

Send `X-Idempotency-Key` to make a batch safe to retry: a replay with the same key and body returns the original response instead of re-applying it.

**Request body:**
- `application/json` **required** — schema: `UniversalBatchRequest`
  - `operations` (array<UniversalBatchOperationRequest>) **required**

**Responses:**
- `200` — All operations succeeded
- `207` — Partial success — some operations failed
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/bom/batch` — Batch bom operations
_operationId_: `batchBom`

Execute up to 100 create/update/delete/upsert operations on bom.

**Best-effort, not all-or-nothing.** Each operation is isolated in its own database savepoint, so successful items are committed even when others fail. The response body reports `total`, `succeeded`, `failed` and a per-item `results` array (each with its own status and error), so you can retry only the failed items. HTTP `200` means every item succeeded; `207` means at least one failed. A top-level `4xx` (e.g. malformed envelope or more than 100 operations) means nothing was applied.

Send `X-Idempotency-Key` to make a batch safe to retry: a replay with the same key and body returns the original response instead of re-applying it.

**Request body:**
- `application/json` **required** — schema: `ResourceBatchRequest`
  - `operations` (array<BatchOperationRequest>) **required** — List of operations (1–100)

**Responses:**
- `200` — All operations succeeded
- `207` — Partial success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/customers/batch` — Batch customers operations
_operationId_: `batchCustomers`

Execute up to 100 create/update/delete/upsert operations on customers.

**Best-effort, not all-or-nothing.** Each operation is isolated in its own database savepoint, so successful items are committed even when others fail. The response body reports `total`, `succeeded`, `failed` and a per-item `results` array (each with its own status and error), so you can retry only the failed items. HTTP `200` means every item succeeded; `207` means at least one failed. A top-level `4xx` (e.g. malformed envelope or more than 100 operations) means nothing was applied.

Send `X-Idempotency-Key` to make a batch safe to retry: a replay with the same key and body returns the original response instead of re-applying it.

**Request body:**
- `application/json` **required** — schema: `ResourceBatchRequest`
  - `operations` (array<BatchOperationRequest>) **required** — List of operations (1–100)

**Responses:**
- `200` — All operations succeeded
- `207` — Partial success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/groups/batch` — Batch groups operations
_operationId_: `batchGroups`

Execute up to 100 create/update/delete/upsert operations on groups.

**Best-effort, not all-or-nothing.** Each operation is isolated in its own database savepoint, so successful items are committed even when others fail. The response body reports `total`, `succeeded`, `failed` and a per-item `results` array (each with its own status and error), so you can retry only the failed items. HTTP `200` means every item succeeded; `207` means at least one failed. A top-level `4xx` (e.g. malformed envelope or more than 100 operations) means nothing was applied.

Send `X-Idempotency-Key` to make a batch safe to retry: a replay with the same key and body returns the original response instead of re-applying it.

**Request body:**
- `application/json` **required** — schema: `ResourceBatchRequest`
  - `operations` (array<BatchOperationRequest>) **required** — List of operations (1–100)

**Responses:**
- `200` — All operations succeeded
- `207` — Partial success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/options/batch` — Batch options operations
_operationId_: `batchOptions`

Execute up to 100 create/update/delete/upsert operations on options.

**Best-effort, not all-or-nothing.** Each operation is isolated in its own database savepoint, so successful items are committed even when others fail. The response body reports `total`, `succeeded`, `failed` and a per-item `results` array (each with its own status and error), so you can retry only the failed items. HTTP `200` means every item succeeded; `207` means at least one failed. A top-level `4xx` (e.g. malformed envelope or more than 100 operations) means nothing was applied.

Send `X-Idempotency-Key` to make a batch safe to retry: a replay with the same key and body returns the original response instead of re-applying it.

**Request body:**
- `application/json` **required** — schema: `ResourceBatchRequest`
  - `operations` (array<BatchOperationRequest>) **required** — List of operations (1–100)

**Responses:**
- `200` — All operations succeeded
- `207` — Partial success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/batch` — Batch parts operations
_operationId_: `batchParts`

Execute up to 100 create/update/delete/upsert operations on parts.

**Best-effort, not all-or-nothing.** Each operation is isolated in its own database savepoint, so successful items are committed even when others fail. The response body reports `total`, `succeeded`, `failed` and a per-item `results` array (each with its own status and error), so you can retry only the failed items. HTTP `200` means every item succeeded; `207` means at least one failed. A top-level `4xx` (e.g. malformed envelope or more than 100 operations) means nothing was applied.

Send `X-Idempotency-Key` to make a batch safe to retry: a replay with the same key and body returns the original response instead of re-applying it.

**Request body:**
- `application/json` **required** — schema: `ResourceBatchRequest`
  - `operations` (array<BatchOperationRequest>) **required** — List of operations (1–100)

**Responses:**
- `200` — All operations succeeded
- `207` — Partial success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/batch` — Batch products operations
_operationId_: `batchProducts`

Execute up to 100 create/update/delete/upsert operations on products.

**Best-effort, not all-or-nothing.** Each operation is isolated in its own database savepoint, so successful items are committed even when others fail. The response body reports `total`, `succeeded`, `failed` and a per-item `results` array (each with its own status and error), so you can retry only the failed items. HTTP `200` means every item succeeded; `207` means at least one failed. A top-level `4xx` (e.g. malformed envelope or more than 100 operations) means nothing was applied.

Send `X-Idempotency-Key` to make a batch safe to retry: a replay with the same key and body returns the original response instead of re-applying it.

**Request body:**
- `application/json` **required** — schema: `ResourceBatchRequest`
  - `operations` (array<BatchOperationRequest>) **required** — List of operations (1–100)

**Responses:**
- `200` — All operations succeeded
- `207` — Partial success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Branches

Version control branches for product configuration. Scope: `parts:read`, `parts:write`.

### `GET /api/v1/branches` — List branches
_operationId_: `listBranches`

List version-control branches for product configuration. Scope: `parts:read`.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/branches` — Create branch
_operationId_: `createBranch`

**Request body:**
- `application/json` **required** — schema: `BranchCreateRequest`
  - `description` (object)
  - `name` (string) **required** — Branch name

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/branches/{branchId}` — Get branch
_operationId_: `getBranch`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/branches/{branchId}` — Delete branch
_operationId_: `deleteBranch`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Catalog Filters

Manage catalog filter dimensions and values for the public product selection page. Dimensions group filterable attributes (e.g. Product Line, Material); values are the selectable options within each dimension. Scope: `products:read`, `products:write`.

### `GET /api/v1/catalog-filters` — List catalog filter dimensions
_operationId_: `listCatalogFilters`

Returns all catalog filter dimensions with their values. Not paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/catalog-filters` — Create a catalog filter dimension
_operationId_: `createCatalogFilter`

Create a new filter dimension. Maximum 5 per company.

**Request body:**
- `application/json` **required** — schema: `CatalogFilterDimensionCreateRequest`
  - `display_type` (string)
  - `is_visible` (boolean)
  - `label` (string) **required**
  - `multi_select` (boolean)

**Responses:**
- `201` — Created
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/catalog-filters/reorder` — Reorder catalog filter dimensions
_operationId_: `reorderCatalogFilters`

Set the display order of filter dimensions.

**Request body:**
- `application/json` **required** — schema: `CatalogFilterReorderRequest`
  - `order` (array<integer>) **required**

**Responses:**
- `200` — Reordered
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/catalog-filters/{id}` — Get a catalog filter dimension
_operationId_: `getCatalogFilter`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/catalog-filters/{id}` — Update a catalog filter dimension
_operationId_: `updateCatalogFilter`

**Request body:**
- `application/json` **required** — schema: `CatalogFilterDimensionUpdateRequest`
  - `display_type` (object)
  - `is_visible` (object)
  - `label` (object)
  - `multi_select` (object)
  - `order_index` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/catalog-filters/{id}` — Delete a catalog filter dimension
_operationId_: `deleteCatalogFilter`

Deletes the dimension and cleans up filter references from all products.

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/catalog-filters/{id}/values` — Add a value to a catalog filter dimension
_operationId_: `createCatalogFilterValue`

Add a new value. Maximum 30 values per dimension.

**Request body:**
- `application/json` **required** — schema: `CatalogFilterValueCreateRequest`
  - `color` (object)
  - `label` (string) **required**

**Responses:**
- `201` — Created
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/catalog-filters/{id}/values/reorder` — Reorder values within a dimension
_operationId_: `reorderCatalogFilterValues`

Set the display order of values within a filter dimension.

**Request body:**
- `application/json` **required** — schema: `CatalogFilterValueReorderRequest`
  - `order` (array<integer>) **required**

**Responses:**
- `200` — Reordered
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/catalog-filters/{id}/values/{valueId}` — Update a catalog filter value
_operationId_: `updateCatalogFilterValue`

**Request body:**
- `application/json` **required** — schema: `CatalogFilterValueUpdateRequest`
  - `color` (object)
  - `label` (object)
  - `order_index` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/catalog-filters/{id}/values/{valueId}` — Delete a catalog filter value
_operationId_: `deleteCatalogFilterValue`

Deletes the value and cleans up filter references from all products.

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Change Orders

Engineering Change Orders (ECO) with impacts and approvals. Track item-level changes and approval workflows. Scope: `parts:read`, `parts:write`.

### `GET /api/v1/change-orders/{ecoId}` — Get change order
_operationId_: `getChangeOrder`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/change-orders/{ecoId}` — Update change order
_operationId_: `updateChangeOrder`

**Request body:**
- `application/json` **required** — schema: `ChangeOrderUpdateRequest`
  - `note` (object)
  - `state` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/change-orders/{ecoId}` — Partially update change order
_operationId_: `patchChangeOrder`

**Request body:**
- `application/json` **required** — schema: `ChangeOrderUpdateRequest`
  - `note` (object)
  - `state` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/change-orders/{ecoId}` — Delete change order
_operationId_: `deleteChangeOrder`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/change-orders/{ecoId}/approvals` — List change approvals
_operationId_: `listChangeApprovals`

List approval records for a change order.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/change-orders/{ecoId}/approvals` — Create change approval
_operationId_: `createChangeApproval`

**Request body:**
- `application/json` **required** — schema: `ApprovalCreateRequest`
  - `approver_id` (object)
  - `status` (string)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/change-orders/{ecoId}/approvals/{approvalId}` — Update change approval
_operationId_: `updateChangeApproval`

**Request body:**
- `application/json` **required** — schema: `ApprovalUpdateRequest`
  - `status` (string) **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/change-orders/{ecoId}/approvals/{approvalId}` — Partially update change approval
_operationId_: `patchChangeApproval`

**Request body:**
- `application/json` **required** — schema: `ApprovalUpdateRequest`
  - `status` (string) **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/change-orders/{ecoId}/impacts` — List change impacts
_operationId_: `listChangeImpacts`

List impacts (item-level changes) in a change order.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/change-orders/{ecoId}/impacts` — Create change impact
_operationId_: `createChangeImpact`

**Request body:**
- `application/json` **required** — schema: `ChangeImpactCreateRequest`
  - `action` (string) **required**
  - `hunk_key` (object)
  - `item_rev_id` (integer) **required**
  - `payload` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/change-orders/{ecoId}/impacts/{impactId}` — Update change impact
_operationId_: `updateChangeImpact`

**Request body:**
- `application/json` **required** — schema: `ChangeImpactUpdateRequest`
  - `payload` (object)
  - `status` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/change-orders/{ecoId}/impacts/{impactId}` — Partially update change impact
_operationId_: `patchChangeImpact`

**Request body:**
- `application/json` **required** — schema: `ChangeImpactUpdateRequest`
  - `payload` (object)
  - `status` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/change-orders/{ecoId}/impacts/{impactId}` — Delete change impact
_operationId_: `deleteChangeImpact`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Change Requests

Engineering Change Requests (ECR) for tracking proposed changes to product configurations. Scope: `parts:read`, `parts:write`.

### `GET /api/v1/change-requests` — List change requests
_operationId_: `listChangeRequests`

List Engineering Change Requests (ECR). Scope: `parts:read`.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `state` (string) — Filter by state (Open, Review, Approved, Rejected)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/change-requests` — Create change request
_operationId_: `createChangeRequest`

**Request body:**
- `application/json` **required** — schema: `ChangeRequestCreateRequest`
  - `description` (object)
  - `title` (string) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/change-requests/{ecrId}` — Get change request
_operationId_: `getChangeRequest`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/change-requests/{ecrId}` — Update change request
_operationId_: `updateChangeRequest`

**Request body:**
- `application/json` **required** — schema: `ChangeRequestUpdateRequest`
  - `description` (object)
  - `state` (object)
  - `title` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/change-requests/{ecrId}` — Partially update change request
_operationId_: `patchChangeRequest`

**Request body:**
- `application/json` **required** — schema: `ChangeRequestUpdateRequest`
  - `description` (object)
  - `state` (object)
  - `title` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/change-requests/{ecrId}` — Delete change request
_operationId_: `deleteChangeRequest`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/change-requests/{ecrId}/orders` — List change orders for request
_operationId_: `listChangeOrdersForRequest`

List Engineering Change Orders (ECO) under a change request.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/change-requests/{ecrId}/orders` — Create change order
_operationId_: `createChangeOrder`

**Request body:**
- `application/json` **required** — schema: `ChangeOrderCreateRequest`
  - `note` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Company

Read and update company-level settings (name, default language, URL prefix). Scope: `products:read`, `products:write`.

### `GET /api/v1/company` — Get company settings
_operationId_: `getCompanySettings`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/company` — Update company settings
_operationId_: `updateCompanySettings`

**Request body:**
- `application/json` **required** — schema: `CompanySettingsUpdateRequest`
  - `company_name` (object)
  - `company_url` (object)
  - `config_code_prefix` (object)
  - `default_language` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/company` — Partially update company settings
_operationId_: `patchCompanySettings`

**Request body:**
- `application/json` **required** — schema: `CompanySettingsUpdateRequest`
  - `company_name` (object)
  - `company_url` (object)
  - `config_code_prefix` (object)
  - `default_language` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/company/configurator-settings` — Get configurator settings
_operationId_: `getConfiguratorSettings`

Retrieve company-level configurator display and behavior settings.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/company/configurator-settings` — Update configurator settings
_operationId_: `updateConfiguratorSettings`

**Request body:**
- `application/json` **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/company/configurator-settings` — Partially update configurator settings
_operationId_: `patchConfiguratorSettings`

**Request body:**
- `application/json` **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/company/connector-settings` — Get connector settings
_operationId_: `getConnectorSettings`

Retrieve company-level connector/integration settings.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/company/connector-settings` — Update connector settings
_operationId_: `updateConnectorSettings`

**Request body:**
- `application/json` **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/company/connector-settings` — Partially update connector settings
_operationId_: `patchConnectorSettings`

**Request body:**
- `application/json` **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/company/contacts` — List company contacts
_operationId_: `listCompanyContacts`

Returns all contact persons for the company. Not paginated.

**Responses:**
- `200` — Company contacts
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/company/contacts` — Create a company contact
_operationId_: `createCompanyContact`

**Request body:**
- `application/json` **required**
  - `city` (string)
  - `country` (string)
  - `email` (string(email))
  - `integration_metadata` (object) — Metadata for external integrations (max 50 keys, 16KB serialized)
  - `name` (string) **required**
  - `organization` (string)
  - `phone` (string)
  - `position` (string)
  - `street` (string)
  - `zip` (string)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/company/contacts/{id}` — Update a company contact
_operationId_: `updateCompanyContact`

**Request body:**
- `application/json` **required**
  - `city` (string)
  - `country` (string)
  - `email` (string(email))
  - `integration_metadata` (object) — Metadata for external integrations (max 50 keys, 16KB serialized)
  - `name` (string)
  - `organization` (string)
  - `phone` (string)
  - `position` (string)
  - `street` (string)
  - `zip` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/company/contacts/{id}` — Partially update a company contact
_operationId_: `patchCompanyContact`

**Request body:**
- `application/json` **required**
  - `email` (string(email))
  - `integration_metadata` (object) — Metadata for external integrations (max 50 keys, 16KB serialized)
  - `name` (string)
  - `organization` (string)
  - `phone` (string)
  - `position` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/company/contacts/{id}` — Delete a company contact
_operationId_: `deleteCompanyContact`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Configurations

The configuration engine resolves option selections against constraints and computes pricing. Configuration states are identified by hash for deduplication. Scope: `configurations:read`, `configurations:write`.

### `GET /api/v1/configurations` — List saved configurations
_operationId_: `listConfigurations`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `product_id` (integer) — Filter by product

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/configurations/calculate` — Calculate a configuration
_operationId_: `calculateConfiguration`

Resolve constraints, compute pricing, and return a configuration state.

**Request body:**
- `application/json` **required** — schema: `ConfigurationCalculateRequest`
  - `disabled_areas` (array<integer>)
  - `enabled_areas` (array<integer>)
  - `option_amounts` (object)
  - `price_list_id` (object)
  - `product_id` (integer) **required**
  - `selected_options` (object)
  - `validate_config` (boolean)
  - `wishlist_options` (array<integer>)

**Responses:**
- `201` — Configuration calculated
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/configurations/states/by-code/{code}` — Get configuration state by code
_operationId_: `getConfigurationStateByCode`

Supports ETag/If-None-Match conditional caching. States are immutable.

**Responses:**
- `200` — Success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/configurations/states/by-code/{code}/parts` — Get configured parts (BOM)
_operationId_: `getConfigurationParts`

Returns the bill of materials for a configuration. Supports pagination via limit/offset and ETag caching.

**Query parameters:**
- `limit` (integer) — Max parts per page (default 200, max 500)
- `offset` (integer) — Number of parts to skip

**Responses:**
- `200` — Success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)
- `504` — Gateway Timeout (`application/json` → `ProblemDetails`)

### `GET /api/v1/configurations/states/by-code/{code}/selections` — Get enriched selected options
_operationId_: `getConfigurationSelections`

Returns each selected option enriched with group name, option name, price, quantity, and wishlist status. Supports ETag caching.

**Responses:**
- `200` — Success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/configurations/states/{hash}` — Get configuration state by hash
_operationId_: `getConfigurationState`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/configurations/{id}` — Get a saved configuration
_operationId_: `getConfiguration`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/configurations/{id}/finalize` — Finalize a configuration
_operationId_: `finalizeConfiguration`

Lock the configuration so it cannot be modified.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Connectors

External system integrations (ERP, CRM, PIM). Connectors define endpoints and tasks that can be triggered manually or on schedule. Jobs track execution history. Scope: `connectors:read`, `connectors:write`.

### `GET /api/v1/connectors` — List connectors
_operationId_: `listConnectors`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/connectors` — Create a connector
_operationId_: `createConnector`

**Request body:**
- `application/json` **required** — schema: `ConnectorCreateRequest`
  - `base_url` (object)
  - `connector_type` (string)
  - `name` (string) **required**
  - `settings` (object)
  - `verify_tls` (boolean)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/connectors/endpoints/{id}` — Delete a connector endpoint
_operationId_: `deleteConnectorEndpoint`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/connectors/jobs` — List connector jobs
_operationId_: `listConnectorJobs`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `status` (string) — Filter by status

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/connectors/jobs/{id}` — Get a connector job
_operationId_: `getConnectorJob`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/connectors/jobs/{id}/replay` — Replay a connector job
_operationId_: `replayConnectorJob`

Re-execute a completed or failed job using its original input context.

**Responses:**
- `202` — Accepted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/connectors/jobs/{jobId}/logs` — List job logs
_operationId_: `listConnectorJobLogs`

List execution log entries for a connector job.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/connectors/tasks/{id}` — Get a connector task
_operationId_: `getConnectorTask`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/connectors/tasks/{id}` — Delete a connector task
_operationId_: `deleteConnectorTask`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/connectors/tasks/{id}/run` — Run a connector task
_operationId_: `runConnectorTask`

**Request body:**
- `application/json` **required**
  - `context` (object) — Execution context

**Responses:**
- `202` — Task queued
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/connectors/triggers` — List connector triggers
_operationId_: `listConnectorTriggers`

Returns all triggers. Not paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/connectors/triggers` — Create a connector trigger
_operationId_: `createConnectorTrigger`

**Request body:**
- `application/json` **required**
  - `enabled` (boolean)
  - `event_key` (string)
  - `filter_template` (string)
  - `schedule_cron` (string)
  - `schedule_timezone` (string)
  - `task_id` (integer) **required**
  - `trigger_type` (string) **required**
  - `webhook_path_suffix` (string)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/connectors/triggers/{id}` — Update a connector trigger
_operationId_: `updateConnectorTrigger`

**Request body:**
- `application/json` **required**
  - `enabled` (boolean)
  - `event_key` (string)
  - `filter_template` (string)
  - `schedule_cron` (string)
  - `schedule_timezone` (string)
  - `webhook_path_suffix` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/connectors/triggers/{id}` — Delete a connector trigger
_operationId_: `deleteConnectorTrigger`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/connectors/{id}` — Get a connector
_operationId_: `getConnector`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/connectors/{id}` — Update a connector
_operationId_: `updateConnector`

**Request body:**
- `application/json` **required** — schema: `ConnectorUpdateRequest`
  - `base_url` (object)
  - `connector_type` (object)
  - `name` (object)
  - `settings` (object)
  - `verify_tls` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/connectors/{id}` — Partially update a connector
_operationId_: `patchConnector`

**Request body:**
- `application/json` **required** — schema: `ConnectorUpdateRequest`
  - `base_url` (object)
  - `connector_type` (object)
  - `name` (object)
  - `settings` (object)
  - `verify_tls` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/connectors/{id}` — Delete a connector
_operationId_: `deleteConnector`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/connectors/{id}/endpoints` — List connector endpoints
_operationId_: `listConnectorEndpoints`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/connectors/{id}/endpoints` — Create a connector endpoint
_operationId_: `createConnectorEndpoint`

**Request body:**
- `application/json` **required** — schema: `EndpointCreateRequest`
  - `body_template` (object)
  - `enabled` (boolean)
  - `headers_template` (object)
  - `key` (string) **required**
  - `method` (string)
  - `on_success` (array<?>)
  - `order_index` (integer)
  - `query_template` (object)
  - `response_extract` (object)
  - `timeout_sec` (integer)
  - `url_template` (string) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/connectors/{id}/tasks` — List connector tasks
_operationId_: `listConnectorTasks`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/connectors/{id}/tasks` — Create a connector task
_operationId_: `createConnectorTask`

**Request body:**
- `application/json` **required** — schema: `TaskCreateRequest`
  - `default_context` (object)
  - `enabled` (boolean)
  - `execution_mode` (string)
  - `name` (string) **required**
  - `steps` (array<object>)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Constraints

Rules that forbid certain option or area combinations. Includes pair-level forbidden combinations and JSON-based rules for complex logic. Uses optimistic concurrency via `X-Constraints-Version`. Scope: `products:read`, `products:write`.

### `GET /api/v1/constraints` — List option-level forbidden combinations
_operationId_: `listConstraints`

Returns all pair-level forbidden combinations for a product. These prevent two specific options from being selected together.

**Query parameters:**
- `product_id` (integer) **required** — Product ID

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/constraints` — Replace option-level forbidden combinations
_operationId_: `replaceConstraints`

Atomically replaces all option-level forbidden combinations for a product. Include the `X-Constraints-Version` header for optimistic concurrency control.

**Request body:**
- `application/json` **required**
  - `forbidden` (array<object>) **required**
  - `product_id` (integer) **required**

**Responses:**
- `200` — Replaced
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/constraints/area` — List area-level forbidden combinations
_operationId_: `listAreaConstraints`

**Query parameters:**
- `product_id` (integer) **required** — Product ID

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/constraints/area` — Replace area-level forbidden combinations
_operationId_: `replaceAreaConstraints`

**Request body:**
- `application/json` **required**
  - `forbidden` (array<object>) **required**
  - `product_id` (integer) **required**

**Responses:**
- `200` — Replaced
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/constraints/check` — Check if a combination is forbidden
_operationId_: `checkConstraint`

**Request body:**
- `application/json` **required** — schema: `ConstraintCheckRequest`
  - `option_id1` (integer) **required**
  - `option_id2` (integer) **required**
  - `product_id` (integer) **required**

**Responses:**
- `200` — Check result
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/constraints/combination-rules` — List combination rules
_operationId_: `listCombinationRules`

Combination rules express how options and areas relate beyond simple forbidden pairs. `rule_type` is one of `forced`, `prerequisite`, `warning`, `visibility`, `recommendation`, `default`, or `set_quantity`. Each side (`source`/`target`) is an option or an area (`source_type`/`target_type` = `option` | `area`). Option↔option rules must link different groups, or two options of the same multi-select group. Cross-area rules must stay coherent: a `forced`/`recommendation` rule with an area source requires the target option to be available in that area; `prerequisite`/`visibility` rules reject a gated entity that only exists inside the area it is paired with. `set_quantity` rules couple the target option's quantity to the source via `quantity_factor`, `quantity_offset`, `quantity_rounding` and `quantity_editable`. Requires the `combination_rules` plan feature.

**Query parameters:**
- `product_id` (integer) **required** — Product ID
- `area_id` (integer) — Filter by area
- `rule_type` (string) — Filter by rule type

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/constraints/combination-rules` — Create a combination rule
_operationId_: `createCombinationRule`

Combination rules express how options and areas relate beyond simple forbidden pairs. `rule_type` is one of `forced`, `prerequisite`, `warning`, `visibility`, `recommendation`, `default`, or `set_quantity`. Each side (`source`/`target`) is an option or an area (`source_type`/`target_type` = `option` | `area`). Option↔option rules must link different groups, or two options of the same multi-select group. Cross-area rules must stay coherent: a `forced`/`recommendation` rule with an area source requires the target option to be available in that area; `prerequisite`/`visibility` rules reject a gated entity that only exists inside the area it is paired with. `set_quantity` rules couple the target option's quantity to the source via `quantity_factor`, `quantity_offset`, `quantity_rounding` and `quantity_editable`. Requires the `combination_rules` plan feature.

**Request body:**
- `application/json` **required** — schema: `CombinationRuleCreateRequest`
  - `area_id` (object)
  - `condition` (object)
  - `direction` (string)
  - `message` (string)
  - `product_id` (integer) **required**
  - `quantity_editable` (object)
  - `quantity_factor` (object)
  - `quantity_offset` (object)
  - `quantity_rounding` (object)
  - `rule_type` (string) **required**
  - `source_area_id` (object)
  - `source_option_id` (object)
  - _...4 more — see `components.schemas` in `openapi.json`_

**Responses:**
- `201` — Created
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/constraints/combination-rules/{id}` — Get a combination rule
_operationId_: `getCombinationRule`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/constraints/combination-rules/{id}` — Update a combination rule
_operationId_: `updateCombinationRule`

Combination rules express how options and areas relate beyond simple forbidden pairs. `rule_type` is one of `forced`, `prerequisite`, `warning`, `visibility`, `recommendation`, `default`, or `set_quantity`. Each side (`source`/`target`) is an option or an area (`source_type`/`target_type` = `option` | `area`). Option↔option rules must link different groups, or two options of the same multi-select group. Cross-area rules must stay coherent: a `forced`/`recommendation` rule with an area source requires the target option to be available in that area; `prerequisite`/`visibility` rules reject a gated entity that only exists inside the area it is paired with. `set_quantity` rules couple the target option's quantity to the source via `quantity_factor`, `quantity_offset`, `quantity_rounding` and `quantity_editable`. Requires the `combination_rules` plan feature.

**Request body:**
- `application/json` **required** — schema: `CombinationRuleUpdateRequest`
  - `area_id` (object)
  - `condition` (object)
  - `direction` (object)
  - `message` (object)
  - `quantity_editable` (object)
  - `quantity_factor` (object)
  - `quantity_offset` (object)
  - `quantity_rounding` (object)
  - `rule_type` (object)
  - `source_area_id` (object)
  - `source_option_id` (object)
  - `source_type` (object)
  - _...3 more — see `components.schemas` in `openapi.json`_

**Responses:**
- `200` — Success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/constraints/combination-rules/{id}` — Delete a combination rule
_operationId_: `deleteCombinationRule`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/constraints/rules` — List constraint rules
_operationId_: `listConstraintRules`

**Query parameters:**
- `product_id` (integer) — Filter by product
- `area_id` (integer) — Filter by area

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/constraints/rules` — Create a constraint rule
_operationId_: `createConstraintRule`

Advanced rules use one of two `rule_json` shapes, validated and canonicalised identically to the in-app rule editor:

* **Forbidden pair** — `{"invalid": [a, b]}` with exactly two option ids from different groups (or the same multi-select group). Optional `"direction": "one_way"` plus `"source": a` makes resolution directed (selecting the source auto-removes the target); validity stays symmetric. Omit `direction` for a symmetric rule.
* **N-way mutual exclusion** — `{"type": "at_most_n", "options": [...], "max_selected": N}` with at least two distinct options and `1 <= max_selected < len(options)`.

Both shapes accept an optional `"requires"` list of condition clauses (`anyOf` / `allOf` / `groupSelections`, chained with `"operator": "AND"|"OR"`, default AND) that gates when the rule is active. This is the same condition grammar as a placement's `usage_subclauses` (see the `UsageSubclause` schema) — `groupSelections` and `operator` mean the same thing in both; constraint rules additionally accept the `anyOf`/`allOf` option-id shorthands. All referenced option ids must belong to the product.

**Request body:**
- `application/json` **required** — schema: `ForbiddenRuleCreateRequest`
  - `area_id` (object)
  - `description` (string)
  - `product_id` (integer) **required**
  - `rule_json` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/constraints/rules/{id}` — Get a constraint rule
_operationId_: `getConstraintRule`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/constraints/rules/{id}` — Update a constraint rule
_operationId_: `updateConstraintRule`

**Request body:**
- `application/json` **required** — schema: `ForbiddenRuleUpdateRequest`
  - `area_id` (object)
  - `description` (object)
  - `rule_json` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/constraints/rules/{id}` — Partially update a constraint rule
_operationId_: `patchConstraintRule`

**Request body:**
- `application/json` **required** — schema: `ForbiddenRuleUpdateRequest`
  - `area_id` (object)
  - `description` (object)
  - `rule_json` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/constraints/rules/{id}` — Delete a constraint rule
_operationId_: `deleteConstraintRule`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Customer Links

Pre-authenticated configurator links for specific products. Scope: `customers:read`, `customers:write`.

### `GET /api/v1/customer-links` — List customer links
_operationId_: `listCustomerLinks`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `product_id` (integer) — Filter by product

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/customer-links` — Create a customer link
_operationId_: `createCustomerLink`

**Request body:**
- `application/json` **required**
  - `expires_at` (string(date-time))
  - `is_protected` (boolean)
  - `max_completed_configs` (integer)
  - `name` (string) **required**
  - `price_list_id` (integer)
  - `product_id` (integer) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/customer-links/{id}` — Get a customer link
_operationId_: `getCustomerLink`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/customer-links/{id}` — Update a customer link
_operationId_: `updateCustomerLink`

**Request body:**
- `application/json` **required**
  - `expires_at` (string|null)
  - `is_protected` (boolean)
  - `max_completed_configs` (integer|null)
  - `name` (string)
  - `price_list_id` (integer)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/customer-links/{id}` — Partially update a customer link
_operationId_: `patchCustomerLink`

**Request body:**
- `application/json` **required**
  - `expires_at` (string|null)
  - `is_protected` (boolean)
  - `max_completed_configs` (integer|null)
  - `name` (string)
  - `price_list_id` (integer)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/customer-links/{id}` — Delete a customer link
_operationId_: `deleteCustomerLink`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Customers

Customer records with optional contact persons. Customers are linked to opportunities and quotes. Scope: `customers:read`, `customers:write`.

### `GET /api/v1/customers` — List customers
_operationId_: `listCustomers`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `search` (string) — Filter by organization, email, or ID (case-insensitive)
- `country` (string) — Filter by address country

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/customers` — Create a customer
_operationId_: `createCustomer`

**Request body:**
- `application/json` **required** — schema: `CustomerCreateRequest`
  - `address_city` (object)
  - `address_country` (object)
  - `address_street` (object)
  - `address_zip` (object)
  - `customer_id` (object)
  - `email` (object)
  - `integration_metadata` (object)
  - `organization` (object)
  - `phone` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/customers/search` — Search customers
_operationId_: `searchCustomers`

Quick search across organization, email, and customer ID. Returns up to 50 results. Not paginated.

**Query parameters:**
- `q` (string) **required** — Search query (min 2 chars)

**Responses:**
- `200` — Matching customers
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/customers/{customerId}/configurations` — List customer configurations
_operationId_: `listCustomerConfigurations`

List all configurations for a customer.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/customers/{customerId}/opportunities` — List customer opportunities
_operationId_: `listCustomerOpportunities`

List all opportunities for a customer.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/customers/{customerId}/quotes` — List customer quotes
_operationId_: `listCustomerQuotes`

List all quotes associated with a customer (via opportunities).

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/customers/{id}` — Get a customer
_operationId_: `getCustomer`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/customers/{id}` — Update a customer
_operationId_: `updateCustomer`

**Request body:**
- `application/json` **required** — schema: `CustomerUpdateRequest`
  - `address_city` (object)
  - `address_country` (object)
  - `address_street` (object)
  - `address_zip` (object)
  - `customer_id` (object)
  - `email` (object)
  - `integration_metadata` (object)
  - `organization` (object)
  - `phone` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/customers/{id}` — Partially update a customer
_operationId_: `patchCustomer`

**Request body:**
- `application/json` **required** — schema: `CustomerUpdateRequest`
  - `address_city` (object)
  - `address_country` (object)
  - `address_street` (object)
  - `address_zip` (object)
  - `customer_id` (object)
  - `email` (object)
  - `integration_metadata` (object)
  - `organization` (object)
  - `phone` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/customers/{id}` — Delete a customer
_operationId_: `deleteCustomer`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/customers/{id}/contacts` — List contacts for a customer
_operationId_: `listContacts`

Returns all contact persons for this customer. Not paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/customers/{id}/contacts` — Add a contact to a customer
_operationId_: `createContact`

**Request body:**
- `application/json` **required** — schema: `ContactCreateRequest`
  - `email` (object)
  - `first_name` (string)
  - `last_name` (string)
  - `phone` (object)
  - `position` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/customers/{id}/contacts/{contact_id}` — Update a contact
_operationId_: `updateContact`

**Request body:**
- `application/json` **required** — schema: `ContactUpdateRequest`
  - `email` (object)
  - `first_name` (object)
  - `last_name` (object)
  - `phone` (object)
  - `position` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/customers/{id}/contacts/{contact_id}` — Remove a contact
_operationId_: `deleteContact`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Documents

Full CMS/CCMS document workspace. **Content Blocks** are reusable EditorJS rich-text components organized in directories, with per-language locales and version tracking. **Structure** defines the hierarchical chapter/section tree of a template, with locale titles and content block attachments. **Templates** support deep cloning, inheritance variants (link/extend/fork), and full-template translation via DeepL. **Instances** are rendered snapshots of a template for a specific context (quote, configuration), with publishable output (HTML/PDF/Markdown) and shareable public links. Scope: `documents:read`, `documents:write`.

### `POST /api/v1/documents/conditions/preview` — Preview condition evaluation
_operationId_: `previewConditions`

Evaluate a conditions clause list against a configuration or inline selection. Returns ``{match: bool}``.

**Request body:**
- `application/json` **required**
  - `conditions` (array<object>) **required**
  - `config_token` (string)
  - `enabled_area_ids` (array<integer>)
  - `selected_option_ids` (array<integer>)

**Responses:**
- `200` — Evaluation result
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/content-blocks` — List content blocks
_operationId_: `listContentBlocks`

List reusable content blocks with cursor-based pagination. Filter by product, directory, tag, active status, or full-text search on title/key.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `product_id` (integer) — Filter by product
- `directory_id` (integer) — Filter by directory
- `tag` (string) — Filter by tag
- `search` (string) — Search by title or key
- `is_active` (string) — Filter by active status

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/content-blocks` — Create a content block
_operationId_: `createContentBlock`

Create a reusable content block. Optionally include an initial locale with EditorJS block content or a dynamic template_name. A unique key is auto-generated if not provided. Returns 409 if the key already exists for this company.

**Request body:**
- `application/json` **required** — schema: `ContentBlockCreateRequest`
  - `conditions` (array<object>)
  - `description` (string)
  - `directory_id` (object)
  - `is_active` (boolean)
  - `key` (object) — Unique key (auto-generated if omitted)
  - `locale` (object) — Initial locale to create with block
  - `order_index` (object)
  - `product_id` (object)
  - `tags` (array<string>)
  - `title` (string) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/content-blocks/batch` — Batch content block operations
_operationId_: `batchContentBlocks`

Create, update, or delete up to 100 content blocks in a single request. Each operation is processed independently — partial failures return 207 Multi-Status with per-operation results. Dynamic blocks cannot be deleted.

**Request body:**
- `application/json` **required** — schema: `ResourceBatchRequest`
  - `operations` (array<BatchOperationRequest>) **required** — List of operations (1–100)

**Responses:**
- `207` — Multi-Status (`application/json` → `BatchResponse`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/content-blocks/images` — Upload EditorJS image
_operationId_: `uploadEditorJsImage`

Upload an image for use in EditorJS content blocks. Send as multipart/form-data with field name 'image'.

**Responses:**
- `201` — Image uploaded
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `413` — Payload Too Large (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/content-blocks/images` — Delete EditorJS image by URL
_operationId_: `deleteEditorJsImage`

**Request body:**
- `application/json` **required**
  - `url` (string) **required**

**Responses:**
- `204` — Deleted
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/content-blocks/{id}` — Get a content block with locales
_operationId_: `getContentBlock`

Returns the content block metadata along with all associated locale payloads. Each locale includes an `is_stale` flag indicating if the content has changed since the last translation.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/documents/content-blocks/{id}` — Update a content block
_operationId_: `updateContentBlock`

Update content block metadata. Dynamic/system blocks only allow `directory_id` and `order_index` changes (returns 403 for other fields). Key changes are validated for uniqueness (409 on conflict).

**Request body:**
- `application/json` **required** — schema: `ContentBlockUpdateRequest`
  - `conditions` (object)
  - `description` (object)
  - `directory_id` (object)
  - `is_active` (object)
  - `key` (object)
  - `order_index` (object)
  - `product_id` (object)
  - `tags` (object)
  - `title` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/content-blocks/{id}` — Delete a content block
_operationId_: `deleteContentBlock`

Delete a content block and all its locales. Automatically cleans up EditorJS images and decrements storage quota. Dynamic/system blocks cannot be deleted (returns 403).

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/content-blocks/{id}/locales` — List content block locales
_operationId_: `listContentBlockLocales`

List all locale versions for a content block, sorted by language.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/content-blocks/{id}/locales` — Create or upsert a content block locale
_operationId_: `createContentBlockLocale`

Create a locale for a content block. If a locale with the same language and version already exists, it is updated (upsert). Provide either `blocks` (EditorJS JSON array) or `template_name` (dynamic slot) — not both. Orphaned EditorJS images are automatically cleaned up on update.

**Request body:**
- `application/json` **required** — schema: `ContentBlockLocaleCreateRequest`
  - `blocks` (object) — EditorJS block array
  - `is_active` (boolean)
  - `language` (string) **required**
  - `template_name` (object) — Dynamic template name (exclusive with blocks)
  - `version` (integer)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/content-blocks/{id}/locales/{locale_id}` — Get a content block locale
_operationId_: `getContentBlockLocale`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/documents/content-blocks/{id}/locales/{locale_id}` — Update a content block locale
_operationId_: `updateContentBlockLocale`

**Request body:**
- `application/json` **required** — schema: `ContentBlockLocaleUpdateRequest`
  - `blocks` (object)
  - `is_active` (object)
  - `language` (object)
  - `template_name` (object)
  - `version` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/content-blocks/{id}/locales/{locale_id}` — Delete a content block locale
_operationId_: `deleteContentBlockLocale`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/content-blocks/{id}/locales/{locale_id}/translate` — Translate locale to target language
_operationId_: `translateContentBlockLocale`

Translate the source locale's EditorJS content to the target language via DeepL. Creates or updates the target locale and sets `source_content_hash` for staleness detection. The `is_stale` flag on the target locale will be `true` if the source content changes after translation.

**Request body:**
- `application/json` **required** — schema: `TranslateRequest`
  - `source_language` (object)
  - `target_language` (string) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)
- `504` — Gateway Timeout (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/content-blocks/{id}/set-version` — Set current version
_operationId_: `setContentBlockVersion`

Set the `current_version` pointer for a content block. This determines which locale version is used when resolving content for documents.

**Request body:**
- `application/json` **required**
  - `version` (integer) **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/content-directories` — List content directories (tree)
_operationId_: `listContentDirectories`

Returns all content directories as a nested hierarchical tree. Root directories have `parent_id: null`; child directories are nested in `children`.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/content-directories` — Create a content directory
_operationId_: `createContentDirectory`

**Request body:**
- `application/json` **required** — schema: `ContentDirectoryCreateRequest`
  - `name` (string) **required**
  - `order_index` (object)
  - `parent_id` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/content-directories/{id}` — Get a content directory
_operationId_: `getContentDirectory`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/documents/content-directories/{id}` — Update a content directory
_operationId_: `updateContentDirectory`

**Request body:**
- `application/json` **required** — schema: `ContentDirectoryUpdateRequest`
  - `name` (object)
  - `order_index` (object)
  - `parent_id` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/content-directories/{id}` — Delete a content directory
_operationId_: `deleteContentDirectory`

Delete a directory. Content blocks in this directory are orphaned to root (directory_id set to null). Child directories are also orphaned to root.

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/doc-types` — List registered document types
_operationId_: `listDocumentTypes`

Return all registered document types and their default layouts, supported output formats, and context requirements.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/instances` — List document instances
_operationId_: `listDocumentInstances`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `template_id` (integer) — Filter by template
- `quote_id` (integer) — Filter by quote
- `context_type` (string) — Filter by context type

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/instances` — Create a document instance (enriched)
_operationId_: `createDocumentInstance`

Create a document instance from a template for a specific context (quote, configuration, or custom). The instance can then be populated with blocks, attachments, and published to HTML, PDF, or Markdown. Pass `metadata` to store custom data like a title.

**Request body:**
- `application/json` **required** — schema: `InstanceCreateRequest`
  - `context_id` (object)
  - `context_type` (string)
  - `lang` (object)
  - `metadata` (object)
  - `quote_id` (object)
  - `template_id` (integer) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/instances/{id}` — Get a document instance
_operationId_: `getDocumentInstance`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/instances/{id}` — Delete a document instance
_operationId_: `deleteDocumentInstance`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/instances/{id}/attachments` — List instance attachments
_operationId_: `listInstanceAttachments`

**Query parameters:**
- `block_id` (integer) — Filter by instance block

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/instances/{id}/attachments` — Create instance attachment
_operationId_: `createInstanceAttachment`

**Request body:**
- `application/json` **required** — schema: `InstanceAttachmentCreateRequest`
  - `block_id` (integer) **required**
  - `content_block_id` (integer) **required**
  - `content_snapshot` (object)
  - `is_active` (boolean)
  - `is_required` (boolean)
  - `order_index` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/instances/{id}/attachments/{att_id}` — Get an instance attachment
_operationId_: `getInstanceAttachment`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/documents/instances/{id}/attachments/{att_id}` — Update instance attachment
_operationId_: `updateInstanceAttachment`

**Request body:**
- `application/json` **required** — schema: `InstanceAttachmentUpdateRequest`
  - `content_snapshot` (object)
  - `is_active` (object)
  - `is_required` (object)
  - `order_index` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/instances/{id}/attachments/{att_id}` — Delete instance attachment
_operationId_: `deleteInstanceAttachment`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/instances/{id}/blocks` — List instance blocks (tree)
_operationId_: `listInstanceBlocks`

**Query parameters:**
- `include_attachments` (string) — Include attachment data

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/instances/{id}/blocks` — Create an instance block
_operationId_: `createInstanceBlock`

Add a new block (chapter / section / container) to a document instance.

**Request body:**
- `application/json` **required** — schema: `InstanceBlockCreateRequest`
  - `is_active` (boolean)
  - `node_type` (string) **required**
  - `order_index` (integer)
  - `parent_id` (object)
  - `repeat_for` (object)
  - `slug` (object)
  - `title` (object)
  - `visibility` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/instances/{id}/blocks/{block_id}` — Get an instance block
_operationId_: `getInstanceBlock`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/documents/instances/{id}/blocks/{block_id}` — Update an instance block
_operationId_: `updateInstanceBlock`

**Request body:**
- `application/json` **required** — schema: `InstanceBlockUpdateRequest`
  - `is_active` (object)
  - `order_index` (object)
  - `title` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/instances/{id}/blocks/{block_id}` — Delete an instance block
_operationId_: `deleteInstanceBlock`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/instances/{id}/public-links` — List public links
_operationId_: `listPublicLinks`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/instances/{id}/public-links/{link_id}` — Get a public link
_operationId_: `getPublicLink`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/instances/{id}/public-links/{link_id}` — Delete a public link
_operationId_: `deletePublicLink`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/instances/{id}/publish` — Publish document instance
_operationId_: `publishInstance`

Render the instance as HTML, PDF, or Markdown. Optionally create a public link.

**Request body:**
- `application/json` **required** — schema: `PublishRequest`
  - `create_public_link` (boolean) — Create a shareable public link
  - `format` (string) — Output format: html, pdf, markdown, docx
  - `language` (object)
  - `title` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/renders/document` — Render a document instance PDF
_operationId_: `renderDocumentPdf`

**Request body:**
- `application/json` **required**
  - `config_token` (string)
  - `instance_id` (integer) **required**
  - `language` (string)

**Responses:**
- `202` — Accepted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)
- `500` — Internal server error (`application/json` → `ProblemDetails`)
- `502` — Upstream dependency failure (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/renders/offer` — Render an offer PDF
_operationId_: `renderOfferPdf`

Queue an offer PDF render for a customer link + configuration. Returns ``202 Accepted`` with a ``PdfGenerationJob`` handle; poll via ``GET /documents/renders/{job_id}`` and fetch bytes via ``GET /documents/renders/{job_id}/content``.

**Request body:**
- `application/json` **required**
  - `config_token` (string) **required**
  - `language` (string)
  - `link_token` (string) **required**
  - `template_id` (integer)

**Responses:**
- `202` — Accepted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)
- `500` — Internal server error (`application/json` → `ProblemDetails`)
- `502` — Upstream dependency failure (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/renders/quote` — Render a quote PDF
_operationId_: `renderQuotePdf`

**Request body:**
- `application/json` **required**
  - `cover_bg_filename` (string)
  - `language` (string)
  - `quote_id` (integer) **required**
  - `template_id` (integer)

**Responses:**
- `202` — Accepted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)
- `500` — Internal server error (`application/json` → `ProblemDetails`)
- `502` — Upstream dependency failure (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/renders/{job_id}` — Get render job status
_operationId_: `getRenderJobStatus`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `410` — Gone — resource has expired (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/renders/{job_id}` — Invalidate a render job
_operationId_: `invalidateRenderJob`

Remove the cached PDF and mark the job expired.

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/renders/{job_id}/content` — Stream rendered PDF bytes
_operationId_: `getRenderJobContent`

Stream the completed PDF.  Returns ``202`` if the job is still running, ``410`` if the render has expired or the cache entry was evicted, ``500`` if rendering failed.

**Responses:**
- `200` — PDF bytes
- `202` — Job still running; retry after a short delay
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `410` — Gone — resource has expired (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)
- `500` — Internal server error (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/templates` — List document templates
_operationId_: `listDocumentTemplates`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `doc_type` (string) — Filter by type
- `product_id` (integer) — Filter by product

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates` — Create a document template
_operationId_: `createDocumentTemplate`

**Request body:**
- `application/json` **required** — schema: `DocumentTemplateCreateRequest`
  - `doc_type` (string) **required**
  - `inheritance_mode` (string)
  - `name` (string) **required**
  - `origin_template_id` (object)
  - `product_id` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/templates/resolve` — Preview template resolution
_operationId_: `previewTemplateResolution`

Preview which template will win the resolution cascade for a given (doc_type, product_id[, template_id]) tuple. Returns ``source ∈ {explicit, product, company, builtin_default}`` and marks virtual templates with ``is_virtual=true``.

**Query parameters:**
- `doc_type` (string) **required** — Registered doc_type key
- `product_id` (integer) — Scope to a product-specific template
- `template_id` (integer) — Force an explicit template

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/templates/{id}` — Get a document template
_operationId_: `getDocumentTemplate`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/documents/templates/{id}` — Update a document template
_operationId_: `updateDocumentTemplate`

**Request body:**
- `application/json` **required** — schema: `DocumentTemplateUpdateRequest`
  - `is_published` (object)
  - `name` (object)
  - `status` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/documents/templates/{id}` — Partially update a document template
_operationId_: `patchDocumentTemplate`

**Request body:**
- `application/json` **required** — schema: `DocumentTemplateUpdateRequest`
  - `is_published` (object)
  - `name` (object)
  - `status` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/templates/{id}` — Delete a document template
_operationId_: `deleteDocumentTemplate`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/assign-products` — Assign a template to products
_operationId_: `assignTemplateProducts`

Assign a template to one or many products. Single product updates in place; multiple products clone the template per product using the specified inheritance mode.

**Request body:**
- `application/json` **required**
  - `inheritance_mode` (string)
  - `product_ids` (array<integer>) **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/clone` — Deep clone a template
_operationId_: `cloneTemplate`

Create a full deep copy of a template including all structure blocks, locale titles, and content block attachments. Content block masters are referenced (not duplicated). Optionally override the name, product, or doc_type.

**Request body:**
- `application/json` **required** — schema: `CloneRequest`
  - `doc_type` (object)
  - `name` (object) — Name for clone (defaults to original + ' (Copy)')
  - `product_id` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/publish` — Publish a template
_operationId_: `publishDocumentTemplate`

Mark the template as published so it becomes a candidate for the resolution cascade.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/templates/{id}/resolve` — Get the resolved template tree
_operationId_: `resolveTemplateTree`

Return the fully resolved template tree (structure blocks, content blocks, and locales) with visibility conditions filtered against an optional configuration.

**Query parameters:**
- `language` (string) — Optional ISO language code
- `config_token` (string) — Optional — filter against this configuration

**Responses:**
- `200` — Resolved tree
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/templates/{id}/structure` — Get template structure tree
_operationId_: `getStructureTree`

Returns the full hierarchical tree of structure blocks (chapters, sections, containers). Pass `?language=DE` to resolve locale-specific titles. Extend-mode variants are automatically synced with their origin template before returning.

**Query parameters:**
- `language` (string) — Resolve titles for this language

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/structure/batch` — Batch structure operations
_operationId_: `batchStructureOperations`

**Request body:**
- `application/json` **required** — schema: `ResourceBatchRequest`
  - `operations` (array<BatchOperationRequest>) **required** — List of operations (1–100)

**Responses:**
- `207` — Multi-Status (`application/json` → `BatchResponse`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/structure/blocks` — Create a structure block
_operationId_: `createStructureBlock`

Add a chapter, section, container, repeater, or placeholder block to the template's structure tree. Slugs must be unique per template (auto-generated if omitted). Returns 403 for link-mode templates (read-only structure).

**Request body:**
- `application/json` **required** — schema: `StructureBlockCreateRequest`
  - `conditions` (array<object>)
  - `is_active` (boolean)
  - `node_type` (string)
  - `order_index` (object)
  - `parent_id` (object)
  - `repeat_for` (object)
  - `slug` (object)
  - `title` (object)
  - `visibility` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/templates/{id}/structure/blocks/{block_id}` — Get a structure block
_operationId_: `getStructureBlock`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/documents/templates/{id}/structure/blocks/{block_id}` — Update a structure block
_operationId_: `updateStructureBlock`

**Request body:**
- `application/json` **required** — schema: `StructureBlockUpdateRequest`
  - `conditions` (object)
  - `is_active` (object)
  - `node_type` (object)
  - `order_index` (object)
  - `parent_id` (object)
  - `repeat_for` (object)
  - `slug` (object)
  - `title` (object)
  - `visibility` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/templates/{id}/structure/blocks/{block_id}` — Delete a structure block (cascade)
_operationId_: `deleteStructureBlock`

Delete a structure block and all its descendants (children, locales, attachments). Returns 403 for link-mode templates.

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments` — List block attachments
_operationId_: `listStructureAttachments`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments` — Attach content block
_operationId_: `createStructureAttachment`

Attach a reusable content block to a structure block. The content block's locale will be resolved at render time based on the document's language. Supports conditions for conditional inclusion.

**Request body:**
- `application/json` **required** — schema: `AttachmentCreateRequest`
  - `conditions` (array<object>)
  - `content_block_id` (integer) **required**
  - `is_active` (boolean)
  - `is_required` (boolean)
  - `order_index` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments/reorder` — Reorder attachments
_operationId_: `reorderStructureAttachments`

**Request body:**
- `application/json` **required** — schema: `ReorderRequest`
  - `items` (array<ReorderItem>) **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments/{att_id}` — Get an attachment
_operationId_: `getStructureAttachment`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments/{att_id}` — Update an attachment
_operationId_: `updateStructureAttachment`

**Request body:**
- `application/json` **required** — schema: `AttachmentUpdateRequest`
  - `conditions` (object)
  - `is_active` (object)
  - `is_required` (object)
  - `order_index` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/templates/{id}/structure/blocks/{block_id}/attachments/{att_id}` — Remove an attachment
_operationId_: `deleteStructureAttachment`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/templates/{id}/structure/blocks/{block_id}/locales` — List structure block locales
_operationId_: `listStructureBlockLocales`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/documents/templates/{id}/structure/blocks/{block_id}/locales/{lang}` — Upsert structure block locale title
_operationId_: `upsertStructureBlockLocale`

Set the translated title for a structure block in a specific language. Creates the locale if it doesn't exist, updates it if it does.

**Request body:**
- `application/json` **required** — schema: `StructureBlockLocaleUpsertRequest`
  - `title` (string) **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/documents/templates/{id}/structure/blocks/{block_id}/locales/{lang}` — Delete structure block locale
_operationId_: `deleteStructureBlockLocale`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/structure/blocks/{block_id}/move` — Move block to new parent
_operationId_: `moveStructureBlock`

**Request body:**
- `application/json` **required** — schema: `MoveRequest`
  - `order_index` (object)
  - `parent_id` (object) — New parent block ID, null for root

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/structure/reorder` — Reorder structure blocks
_operationId_: `reorderStructureBlocks`

**Request body:**
- `application/json` **required** — schema: `ReorderRequest`
  - `items` (array<ReorderItem>) **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `403` — Insufficient scopes (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/translate` — Translate entire template
_operationId_: `translateTemplate`

Translate all structure block titles and attached content block locales to the target language via DeepL. Creates or updates locale rows for each block. Sets `source_content_hash` on content locales for staleness tracking. Returns counts of translated titles and content locales.

**Request body:**
- `application/json` **required** — schema: `TemplateTranslateRequest`
  - `source_language` (object)
  - `target_language` (string) **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)
- `504` — Gateway Timeout (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/unpublish` — Unpublish a template
_operationId_: `unpublishDocumentTemplate`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/documents/templates/{id}/validate-config` — Validate a configuration against a template
_operationId_: `validateTemplateConfig`

**Query parameters:**
- `config_token` (string) **required** — Configuration token or code

**Responses:**
- `200` — Validation result
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/documents/templates/{id}/variants` — Create an inheritance variant
_operationId_: `createVariant`

Create a derived template linked to this template as its origin. **link**: read-only mirror (structure writes return 403). **extend**: inherits origin structure, auto-syncs on read, allows additions. **fork**: deep copy with origin reference (independent after creation).

**Request body:**
- `application/json` **required** — schema: `VariantCreateRequest`
  - `inheritance_mode` (string) — link, extend, or fork
  - `name` (string) **required**
  - `product_id` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Export

Bulk export endpoints streaming NDJSON for incremental sync. Scope: varies by resource.

### `GET /api/v1/customers/export` — Export customers (NDJSON)
_operationId_: `exportCustomers`

Stream all customers as NDJSON for bulk export.

**Query parameters:**
- `updated_after` (string) — ISO 8601 timestamp for incremental sync

**Responses:**
- `200` — NDJSON stream (one JSON object per line)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/export` — Export parts (NDJSON)
_operationId_: `exportParts`

Stream all parts as NDJSON for bulk export.

**Query parameters:**
- `updated_after` (string) — ISO 8601 timestamp for incremental sync

**Responses:**
- `200` — NDJSON stream (one JSON object per line)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/products/export` — Export products (NDJSON)
_operationId_: `exportProducts`

Stream all products as NDJSON for bulk export. Use `updated_after` for incremental sync.

**Query parameters:**
- `updated_after` (string) — ISO 8601 timestamp for incremental sync

**Responses:**
- `200` — NDJSON stream (one JSON object per line)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Groups

Option groups are containers for related configuration choices within an area (e.g., 'Color', 'Material'). Groups can be duplicated with all their options. Cardinality constraints (`is_required`, `selection_min`, `selection_max`) control how many options must or may be selected. Scope: `products:read`, `products:write`.

### `GET /api/v1/groups` — List groups
_operationId_: `listGroups`

Returns a paginated list of groups. Use `search` to filter by name, `area_id` to filter by area assignment.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `search` (string) — Filter by name (case-insensitive partial match)
- `area_id` (integer) — Filter by area assignment

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/groups` — Create a group
_operationId_: `createGroup`

**Request body:**
- `application/json` **required** — schema: `GroupCreateRequest`
  - `area_id` (object) — Area to assign this group to
  - `description` (string)
  - `is_multi` (boolean)
  - `is_required` (boolean) — Require at least one selection in this group
  - `key` (string)
  - `language` (string)
  - `name` (string) **required**
  - `order_index` (object) — Position in group list (auto-assigned if omitted)
  - `selection_max` (object) — Maximum number of selections allowed (multi-select groups)
  - `selection_min` (object) — Minimum number of selections required (multi-select groups)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/groups/{id}` — Get a group
_operationId_: `getGroup`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/groups/{id}` — Update a group
_operationId_: `updateGroup`

**Request body:**
- `application/json` **required** — schema: `GroupUpdateRequest`
  - `description` (object)
  - `is_multi` (object)
  - `is_required` (object)
  - `key` (object)
  - `language` (object)
  - `name` (object)
  - `order_index` (object)
  - `selection_max` (object)
  - `selection_min` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/groups/{id}` — Partially update a group
_operationId_: `patchGroup`

**Request body:**
- `application/json` **required** — schema: `GroupUpdateRequest`
  - `description` (object)
  - `is_multi` (object)
  - `is_required` (object)
  - `key` (object)
  - `language` (object)
  - `name` (object)
  - `order_index` (object)
  - `selection_max` (object)
  - `selection_min` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/groups/{id}` — Delete a group
_operationId_: `deleteGroup`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/groups/{id}/areas` — List areas linked to a group
_operationId_: `listGroupAreas`

Returns all areas the group is currently linked to. Not paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/groups/{id}/areas` — Link a group to areas
_operationId_: `linkGroupAreas`

Link a group to one or more areas. Already-linked areas are silently skipped (idempotent).

**Request body:**
- `application/json` **required** — schema: `GroupAreaLinkRequest`
  - `area_ids` (array<integer>) **required** — IDs of areas to link to the group.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/groups/{id}/areas/{area_id}` — Unlink a group from an area
_operationId_: `unlinkGroupArea`

Remove the group-area association and clean up area-specific data (OptionAreaConfig, OptionPriceOverride, OptionAdvancedPrice rows).

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/groups/{id}/duplicate` — Duplicate a group
_operationId_: `duplicateGroup`

Deep-copy the group including all options.

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/groups/{id}/options` — List options in a group
_operationId_: `listGroupOptions`

Returns options belonging to this group. Not paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Images

Upload, replace, and delete images for products, areas, and options. Supports primary images, background images, galleries (up to 10), and area-specific option overrides. All uploads accept `multipart/form-data`. Scope: `products:read`, `products:write`.

### `POST /api/v1/areas/{areaId}/image` — Upload area image
_operationId_: `uploadAreaImage`

**Request body:**
- `multipart/form-data` **required**
  - `file` (string(binary)) **required** — Image file (JPEG, PNG, WebP, GIF)

**Responses:**
- `201` — Image uploaded
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `413` — Payload Too Large (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/areas/{areaId}/image` — Delete area image
_operationId_: `deleteAreaImage`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/options/{optionId}/image` — Upload option image
_operationId_: `uploadOptionImage`

Upload or replace the option's base image.

**Request body:**
- `multipart/form-data` **required**
  - `file` (string(binary)) **required** — Image file (JPEG, PNG, WebP, GIF)

**Responses:**
- `201` — Image uploaded
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `413` — Payload Too Large (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/options/{optionId}/image` — Delete option image
_operationId_: `deleteOptionImage`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/options/{optionId}/image/areas/{areaId}` — Upload option area override image
_operationId_: `uploadOptionAreaImage`

Upload or replace an area-specific image override for the option.

**Request body:**
- `multipart/form-data` **required**
  - `file` (string(binary)) **required** — Image file (JPEG, PNG, WebP, GIF)

**Responses:**
- `201` — Image uploaded
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `413` — Payload Too Large (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/options/{optionId}/image/areas/{areaId}` — Delete option area override image
_operationId_: `deleteOptionAreaImage`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/background` — Upload product background
_operationId_: `uploadProductBackground`

**Request body:**
- `multipart/form-data` **required**
  - `file` (string(binary)) **required** — Image file (JPEG, PNG, WebP, GIF)

**Responses:**
- `201` — Image uploaded
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `413` — Payload Too Large (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/products/{productId}/background` — Delete product background
_operationId_: `deleteProductBackground`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/products/{productId}/gallery` — List gallery images
_operationId_: `listGalleryImages`

Returns gallery images ordered by position.

**Responses:**
- `200` — Gallery images
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/gallery` — Upload gallery image
_operationId_: `uploadGalleryImage`

Upload a new gallery image (max 10 per product).

**Request body:**
- `multipart/form-data` **required**
  - `file` (string(binary)) **required** — Image file (JPEG, PNG, WebP, GIF)

**Responses:**
- `201` — Gallery image created
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `413` — Payload Too Large (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/gallery/reorder` — Reorder gallery images
_operationId_: `reorderGalleryImages`

**Request body:**
- `application/json` **required** — schema: `GalleryReorderRequest`
  - `order` (array<integer>) **required** — Gallery image IDs in desired display order.

**Responses:**
- `200` — Gallery images in new order
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/products/{productId}/gallery/{imageId}` — Get gallery image
_operationId_: `getGalleryImage`

Get metadata for a single gallery image by ID.

**Responses:**
- `200` — Gallery image metadata
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/products/{productId}/gallery/{imageId}` — Replace gallery image
_operationId_: `replaceGalleryImage`

Replace the file for a gallery image, preserving its ID and order position.

**Request body:**
- `multipart/form-data` **required**
  - `file` (string(binary)) **required** — Image file (JPEG, PNG, WebP, GIF)

**Responses:**
- `200` — Gallery image replaced
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `413` — Payload Too Large (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/products/{productId}/gallery/{imageId}` — Delete gallery image
_operationId_: `deleteGalleryImage`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/image` — Upload product image
_operationId_: `uploadProductImage`

**Request body:**
- `multipart/form-data` **required**
  - `file` (string(binary)) **required** — Image file (JPEG, PNG, WebP, GIF)

**Responses:**
- `201` — Image uploaded
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `413` — Payload Too Large (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/products/{productId}/image` — Delete product image
_operationId_: `deleteProductImage`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Inbound Webhooks

Receive data from external systems (CRM, ERP). Supports customer upsert, opportunity creation, part import, and connector triggering. Scope: `webhooks:inbound`, `customers:write`, `quotes:write`, `connectors:execute`.

### `POST /api/v1/inbound/connectors/tasks/{id}/trigger` — Trigger a connector task
_operationId_: `triggerInboundConnectorTask`

Fire a connector task with optional runtime context.

**Request body:**
- `application/json` **required**
  - `runtime_context` (object)

**Responses:**
- `202` — Task triggered
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/inbound/customers` — Upsert an inbound customer
_operationId_: `upsertInboundCustomer`

Create or update a customer from an external system.

**Request body:**
- `application/json` **required**
  - `address_city` (string)
  - `address_country` (string)
  - `address_street` (string)
  - `address_zip` (string)
  - `email` (string(email))
  - `external_id` (string) **required**
  - `organization` (string)
  - `phone` (string)

**Responses:**
- `201` — Customer created or updated
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/inbound/customers/batch` — Batch upsert inbound customers
_operationId_: `batchUpsertInboundCustomers`

Create or update multiple customers in one request.

**Request body:**
- `application/json` **required**
  - `items` (array<object>)

**Responses:**
- `200` — Batch result
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/inbound/events` — Send an inbound event
_operationId_: `sendInboundEvent`

Submit a generic event for processing.

**Request body:**
- `application/json` **required**
  - `data` (object) **required**
  - `event_type` (string) **required**
  - `idempotency_key` (string)

**Responses:**
- `201` — Event accepted
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/inbound/opportunities` — Create an inbound opportunity
_operationId_: `createInboundOpportunity`

Create an opportunity with optional configuration and quote from an external system.

**Request body:**
- `application/json` **required**
  - `config_hash` (string)
  - `config_token` (string)
  - `customer_id` (integer)
  - `description` (string)
  - `line_notes` (string)
  - `name` (string)
  - `price_list_id` (integer)
  - `product_id` (integer)
  - `quantity` (integer)
  - `stage` (string)
  - `total_price` (number)

**Responses:**
- `201` — Opportunity created
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/inbound/parts/batch` — Batch upsert inbound parts
_operationId_: `batchUpsertInboundParts`

Create or update part placements for a product/area.

**Request body:**
- `application/json` **required**
  - `area_id` (integer)
  - `delete_missing` (boolean)
  - `items` (array<object>)
  - `product_id` (integer) **required**

**Responses:**
- `200` — Batch result
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/inbound/triggers/{suffix}` — Fire a webhook trigger by path
_operationId_: `fireWebhookTrigger`

Fire a webhook-type trigger by its configured path suffix. External systems POST to this endpoint to trigger a connector task.

**Request body:**
- `application/json` **required**

**Responses:**
- `202` — Trigger accepted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Item Revisions

Revision tracking for parts with lifecycle states (Draft → Review → Released → Obsolete). Only Draft revisions can be edited or deleted. Releasing a revision locks it and obsoletes the previous released revision. Scope: `parts:read`, `parts:write`.

### `GET /api/v1/parts/{partId}/revisions` — List revisions for a part
_operationId_: `listItemRevisions`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/{partId}/revisions` — Create a revision
_operationId_: `createItemRevision`

**Request body:**
- `application/json` **required** — schema: `ItemRevisionCreateRequest`
  - `code` (string) **required**
  - `lifecycle_state` (string)
  - `note` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/{partId}/revisions/{revisionId}` — Get a revision
_operationId_: `getItemRevision`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/parts/{partId}/revisions/{revisionId}` — Update a draft revision
_operationId_: `updateItemRevision`

Only Draft or Review revisions can be updated.

**Request body:**
- `application/json` **required** — schema: `ItemRevisionUpdateRequest`
  - `code` (object)
  - `note` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/parts/{partId}/revisions/{revisionId}` — Delete a draft revision
_operationId_: `deleteItemRevision`

Only Draft or Review revisions can be deleted.

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/{partId}/revisions/{revisionId}/obsolete` — Obsolete a revision
_operationId_: `obsoleteItemRevision`

Marks a Released revision as Obsolete.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/{partId}/revisions/{revisionId}/release` — Release a revision
_operationId_: `releaseItemRevision`

Transitions to Released state. Obsoletes the previous released revision for the same part.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Languages

Supported languages for product translations. One language is marked as the base language. Scope: `products:read`, `products:write`.

### `GET /api/v1/languages` — List languages
_operationId_: `listLanguages`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/languages` — Create a language
_operationId_: `createLanguage`

**Request body:**
- `application/json` **required** — schema: `LanguageCreateRequest`
  - `code` (string) **required**
  - `is_base` (boolean)
  - `name` (string) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/languages/reorder` — Reorder languages
_operationId_: `reorderLanguages`

**Request body:**
- `application/json` **required** — schema: `LanguageReorderRequest`
  - `order` (array<integer>) **required** — Language IDs in desired order

**Responses:**
- `200` — Reordered
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/languages/{id}` — Get a language
_operationId_: `getLanguage`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/languages/{id}` — Update a language
_operationId_: `updateLanguage`

**Request body:**
- `application/json` **required** — schema: `LanguageUpdateRequest`
  - `code` (object)
  - `is_base` (object)
  - `name` (object)
  - `order_index` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/languages/{id}` — Partially update a language
_operationId_: `patchLanguage`

**Request body:**
- `application/json` **required** — schema: `LanguageUpdateRequest`
  - `code` (object)
  - `is_base` (object)
  - `name` (object)
  - `order_index` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/languages/{id}` — Delete a language
_operationId_: `deleteLanguage`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Opportunities

Sales opportunities track deals through stages (qualification → drafting → presented → negotiation → won/lost). Each opportunity has one or more quotes. Scope: `quotes:read`, `quotes:write`.

### `GET /api/v1/opportunities` — List opportunities
_operationId_: `listOpportunities`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `stage` (string) — Filter by stage
- `customer_id` (integer) — Filter by customer
- `search` (string) — Search by name

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/opportunities` — Create an opportunity
_operationId_: `createOpportunity`

**Request body:**
- `application/json` **required** — schema: `OpportunityCreateRequest`
  - `customer_id` (integer) **required**
  - `description` (object)
  - `expected_amount` (object)
  - `expected_close_date` (object)
  - `integration_metadata` (object)
  - `name` (string) **required**
  - `owner_contact_id` (object)
  - `probability` (integer)
  - `stage` (string)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/opportunities/{id}` — Get an opportunity
_operationId_: `getOpportunity`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/opportunities/{id}` — Update an opportunity
_operationId_: `updateOpportunity`

**Request body:**
- `application/json` **required** — schema: `OpportunityUpdateRequest`
  - `description` (object)
  - `expected_amount` (object)
  - `expected_close_date` (object)
  - `integration_metadata` (object)
  - `name` (object)
  - `owner_contact_id` (object)
  - `primary_quote_id` (object)
  - `probability` (object)
  - `stage` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/opportunities/{id}` — Partially update an opportunity
_operationId_: `patchOpportunity`

**Request body:**
- `application/json` **required** — schema: `OpportunityUpdateRequest`
  - `description` (object)
  - `expected_amount` (object)
  - `expected_close_date` (object)
  - `integration_metadata` (object)
  - `name` (object)
  - `owner_contact_id` (object)
  - `primary_quote_id` (object)
  - `probability` (object)
  - `stage` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/opportunities/{id}` — Delete an opportunity
_operationId_: `deleteOpportunity`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/opportunities/{id}/quotes` — List quotes for an opportunity
_operationId_: `listOpportunityQuotes`

Returns all quotes belonging to this opportunity. Not paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Options

Options are the individual selectable choices within a group (e.g., 'Red', 'Blue'). Each option has a base price that can be overridden per price-list/area combination. Scope: `products:read`, `products:write`, `prices:read`.

### `GET /api/v1/options` — List options
_operationId_: `listOptions`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `group_id` (integer) — Filter by group
- `search` (string) — Filter by name (case-insensitive partial match)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/options` — Create an option
_operationId_: `createOption`

**Request body:**
- `application/json` **required** — schema: `OptionCreateRequest`
  - `description` (string)
  - `group_id` (integer) **required** — Group this option belongs to
  - `is_numbered` (boolean)
  - `key` (string)
  - `language` (string)
  - `name` (string) **required**
  - `number_max` (object)
  - `number_min` (object)
  - `number_step` (object)
  - `number_unit` (string)
  - `order_index` (object) — Position in option list (auto-assigned if omitted)
  - `price` (string)
  - _...2 more — see `components.schemas` in `openapi.json`_

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/options/{id}` — Get an option
_operationId_: `getOption`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/options/{id}` — Update an option
_operationId_: `updateOption`

**Request body:**
- `application/json` **required** — schema: `OptionUpdateRequest`
  - `description` (object)
  - `is_numbered` (object)
  - `key` (object)
  - `language` (object)
  - `name` (object)
  - `number_max` (object)
  - `number_min` (object)
  - `number_step` (object)
  - `number_unit` (object)
  - `order_index` (object)
  - `price` (object)
  - `price_scalings` (object)
  - _...1 more — see `components.schemas` in `openapi.json`_

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/options/{id}` — Partially update an option
_operationId_: `patchOption`

**Request body:**
- `application/json` **required** — schema: `OptionUpdateRequest`
  - `description` (object)
  - `is_numbered` (object)
  - `key` (object)
  - `language` (object)
  - `name` (object)
  - `number_max` (object)
  - `number_min` (object)
  - `number_step` (object)
  - `number_unit` (object)
  - `order_index` (object)
  - `price` (object)
  - `price_scalings` (object)
  - _...1 more — see `components.schemas` in `openapi.json`_

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/options/{id}` — Delete an option
_operationId_: `deleteOption`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/options/{id}/effective` — Get effective price for an option
_operationId_: `getEffectivePrice`

Returns the effective price considering overrides.

**Query parameters:**
- `price_list_id` (integer) — Price list ID
- `area_id` (integer) — Area ID

**Responses:**
- `200` — Effective price
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/options/{optionId}/advanced-prices` — List advanced prices
_operationId_: `listAdvancedPrices`

List condition-based price overrides for an option. Not paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/options/{optionId}/advanced-prices` — Create an advanced price
_operationId_: `createAdvancedPrice`

**Request body:**
- `application/json` **required**
  - `advanced_price` (string) **required**
  - `area_id` (integer)
  - `condition_option_id` (integer) **required**
  - `price_list_id` (integer)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/options/{optionId}/advanced-prices/{priceId}` — Update an advanced price
_operationId_: `updateAdvancedPrice`

**Request body:**
- `application/json` **required**
  - `advanced_price` (string) **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/options/{optionId}/advanced-prices/{priceId}` — Partially update an advanced price
_operationId_: `patchAdvancedPrice`

**Request body:**
- `application/json` **required**
  - `advanced_price` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/options/{optionId}/advanced-prices/{priceId}` — Delete an advanced price
_operationId_: `deleteAdvancedPrice`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/options/{optionId}/area-config` — Get area-specific config for an option
_operationId_: `getOptionAreaConfig`

**Query parameters:**
- `area_id` (integer) **required** — Area ID

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/options/{optionId}/area-config` — Set area-specific config for an option
_operationId_: `setOptionAreaConfig`

**Query parameters:**
- `area_id` (integer) **required** — Area ID

**Request body:**
- `application/json` **required**
  - `is_numbered` (boolean)
  - `number_max` (number)
  - `number_min` (number)
  - `number_step` (number)
  - `number_unit` (string)
  - `option_description` (string)
  - `option_key` (string)
  - `price` (string)
  - `recommended` (boolean)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/options/{optionId}/area-config` — Clear area-specific config for an option
_operationId_: `deleteOptionAreaConfig`

Clear an option's area-specific override(s). Pass `field` to clear a single override column; omit it to delete the whole override row. Scope: `prices:write`.

**Query parameters:**
- `area_id` (integer) **required** — Area ID
- `field` (string) — Single override field to clear (e.g. price, option_key); omit to clear all

**Responses:**
- `204` — Deleted
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Part Documents

Technical document metadata (CAD files, drawings, specifications) associated with parts. Documents can be linked to parts or specific revisions. Scope: `parts:read`, `parts:write`.

### `GET /api/v1/part-documents` — List part documents
_operationId_: `listPartDocuments`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `doc_type` (string) — Filter by doc type (CAD, Drawing, Spec, Manual, Other)
- `lifecycle_state` (string) — Filter by lifecycle state
- `search` (string) — Search by document number

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/part-documents` — Create a part document
_operationId_: `createPartDocument`

**Request body:**
- `application/json` **required** — schema: `PartDocumentCreateRequest`
  - `doc_type` (string)
  - `lifecycle_state` (string)
  - `note` (object)
  - `number` (string) **required**
  - `source_system` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/part-documents/{id}` — Get a part document
_operationId_: `getPartDocument`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/part-documents/{id}` — Update a part document
_operationId_: `updatePartDocument`

**Request body:**
- `application/json` **required** — schema: `PartDocumentUpdateRequest`
  - `doc_type` (object)
  - `lifecycle_state` (object)
  - `note` (object)
  - `number` (object)
  - `source_system` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/part-documents/{id}` — Partially update a part document
_operationId_: `patchPartDocument`

**Request body:**
- `application/json` **required** — schema: `PartDocumentUpdateRequest`
  - `doc_type` (object)
  - `lifecycle_state` (object)
  - `note` (object)
  - `number` (object)
  - `source_system` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/part-documents/{id}` — Delete a part document
_operationId_: `deletePartDocument`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/{partId}/document-links` — List document links for a part
_operationId_: `listPartDocumentLinks`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/{partId}/document-links` — Create a document link for a part
_operationId_: `createPartDocumentLink`

**Request body:**
- `application/json` **required** — schema: `PartDocumentLinkCreateRequest`
  - `document_id` (integer) **required**
  - `role` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/parts/{partId}/document-links/{linkId}` — Remove a document link
_operationId_: `deletePartDocumentLink`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/{partId}/revisions/{revisionId}/document-links` — List document links for a revision
_operationId_: `listRevisionDocumentLinks`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/{partId}/revisions/{revisionId}/document-links` — Create a document link for a revision
_operationId_: `createRevisionDocumentLink`

**Request body:**
- `application/json` **required** — schema: `PartDocumentLinkCreateRequest`
  - `document_id` (integer) **required**
  - `role` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Parts

PLM (Product Lifecycle Management) parts catalog. Parts have placements on areas and Bill of Materials (BOM) hierarchies for manufacturing. Scope: `parts:read`, `parts:write`.

### `GET /api/v1/areas/{id}/placements` — List placements on an area
_operationId_: `listAreaPlacements`

The bulk read path for a configurable BOM: returns **every** part placement on the area, cursor-paginated (`limit` up to 100, default 100). Each item is a full placement — `part_id`, `area_id`, `usage_subclauses`, `option_scalings` — so you can reconstruct the area's conditional BOM in a handful of requests instead of one per part. Unknown query parameters are rejected with `400`.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (1-100, default 100)

**Responses:**
- `200` — Success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts` — List parts
_operationId_: `listParts`

Lists parts (cursor-paginated). Only the documented query parameters are accepted — any unknown parameter is rejected with `400` rather than silently ignored.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `status` (string) — Filter by lifecycle status
- `part_type` (string) — Filter by part type
- `search` (string) — Search by number or name
- `area_id` (integer) — Only parts that have a placement on this area. A non-integer value returns 400; an unknown area returns 404.

**Responses:**
- `200` — Success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts` — Create a part
_operationId_: `createPart`

**Request body:**
- `application/json` **required** — schema: `PartCreateRequest`
  - `bom_structure` (string) — 'normal' — an ordinary part/assembly. 'ghost' — a phantom assembly: a structural container that groups BOM ...
  - `commodity_code` (object)
  - `custom_fields` (object)
  - `integration_metadata` (object)
  - `make_or_buy` (object)
  - `part_cost` (integer)
  - `part_description` (object)
  - `part_name` (string) **required**
  - `part_number` (string) **required**
  - `part_type` (object)
  - `phantom_resolve_mode` (string) — For ghost (phantom) parts, controls how the phantom is resolved when materialised: 'dissolve' inlines the c...
  - `status` (string)
  - _...2 more — see `components.schemas` in `openapi.json`_

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/parts/bom/{id}` — Update a BOM item
_operationId_: `updateBomItem`

**Request body:**
- `application/json` **required** — schema: `BomItemUpdateRequest`
  - `alt_group` (object)
  - `effective_from` (object)
  - `effective_to` (object)
  - `ghost_part` (object)
  - `note` (object)
  - `option_scalings` (object) — Quantity scaling for numbered options: {option_id (string): multiplier}. ADDS to the line's base quantity i...
  - `order_index` (object)
  - `priority` (object)
  - `quantity` (object)
  - `scrap_percent` (object)
  - `uom` (object)
  - `usage_subclauses` (object) — Conditions that make this line configurable. The subclauses are evaluated left-to-right — each joins the ru...

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/parts/bom/{id}` — Partially update a BOM item
_operationId_: `patchBomItem`

**Request body:**
- `application/json` **required** — schema: `BomItemUpdateRequest`
  - `alt_group` (object)
  - `effective_from` (object)
  - `effective_to` (object)
  - `ghost_part` (object)
  - `note` (object)
  - `option_scalings` (object) — Quantity scaling for numbered options: {option_id (string): multiplier}. ADDS to the line's base quantity i...
  - `order_index` (object)
  - `priority` (object)
  - `quantity` (object)
  - `scrap_percent` (object)
  - `uom` (object)
  - `usage_subclauses` (object) — Conditions that make this line configurable. The subclauses are evaluated left-to-right — each joins the ru...

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/parts/bom/{id}` — Delete a BOM item
_operationId_: `deleteBomItem`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/ghosts` — List ghost parts
_operationId_: `listGhostParts`

List ghost (phantom assembly) parts — parts whose `bom_structure` is `ghost`. A ghost is a structural grouping whose children are pulled into the parent on BOM explosion; it is never itself purchased. You only need ghost parts if you model phantom sub-assemblies — a plain conditional BOM (parts placed on areas with `usage_subclauses`) does not require them. Scope: `parts:read`.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `status` (string) — Filter by lifecycle status
- `part_type` (string) — Filter by part type
- `search` (string) — Search by number or name

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/groups` — List part groups
_operationId_: `listPartGroups`

List logical part groups.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/groups` — Create part group
_operationId_: `createPartGroup`

**Request body:**
- `application/json` **required** — schema: `PartGroupCreateRequest`
  - `description` (string)
  - `name` (string) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/groups/{groupId}` — Get part group
_operationId_: `getPartGroup`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/parts/groups/{groupId}` — Update part group
_operationId_: `updatePartGroup`

**Request body:**
- `application/json` **required** — schema: `PartGroupUpdateRequest`
  - `description` (string)
  - `name` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/parts/groups/{groupId}` — Partially update part group
_operationId_: `patchPartGroup`

**Request body:**
- `application/json` **required** — schema: `PartGroupUpdateRequest`
  - `description` (string)
  - `name` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/parts/groups/{groupId}` — Delete part group
_operationId_: `deletePartGroup`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/parts/placements/{id}` — Update a part placement
_operationId_: `updatePartPlacement`

**Request body:**
- `application/json` **required** — schema: `PartPlacementUpdateRequest`
  - `area_id` (object)
  - `ghost_part` (object)
  - `option_scalings` (object) — Quantity scaling for numbered options: {option_id (string): multiplier}. ADDS to the line's base quantity i...
  - `order_index` (object)
  - `quantity` (object)
  - `uom` (object)
  - `usage_subclauses` (object) — Conditions that make this line configurable. The subclauses are evaluated left-to-right — each joins the ru...

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/parts/placements/{id}` — Partially update a part placement
_operationId_: `patchPartPlacement`

**Request body:**
- `application/json` **required** — schema: `PartPlacementUpdateRequest`
  - `area_id` (object)
  - `ghost_part` (object)
  - `option_scalings` (object) — Quantity scaling for numbered options: {option_id (string): multiplier}. ADDS to the line's base quantity i...
  - `order_index` (object)
  - `quantity` (object)
  - `uom` (object)
  - `usage_subclauses` (object) — Conditions that make this line configurable. The subclauses are evaluated left-to-right — each joins the ru...

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/parts/placements/{id}` — Delete a part placement
_operationId_: `deletePartPlacement`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/{id}` — Get a part
_operationId_: `getPart`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/parts/{id}` — Update a part
_operationId_: `updatePart`

**Request body:**
- `application/json` **required** — schema: `PartUpdateRequest`
  - `bom_structure` (object)
  - `commodity_code` (object)
  - `custom_fields` (object)
  - `integration_metadata` (object)
  - `make_or_buy` (object)
  - `part_cost` (object)
  - `part_description` (object)
  - `part_name` (object)
  - `part_number` (object)
  - `part_type` (object)
  - `phantom_resolve_mode` (object)
  - `status` (object)
  - _...2 more — see `components.schemas` in `openapi.json`_

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/parts/{id}` — Partially update a part
_operationId_: `patchPart`

**Request body:**
- `application/json` **required** — schema: `PartUpdateRequest`
  - `bom_structure` (object)
  - `commodity_code` (object)
  - `custom_fields` (object)
  - `integration_metadata` (object)
  - `make_or_buy` (object)
  - `part_cost` (object)
  - `part_description` (object)
  - `part_name` (object)
  - `part_number` (object)
  - `part_type` (object)
  - `phantom_resolve_mode` (object)
  - `status` (object)
  - _...2 more — see `components.schemas` in `openapi.json`_

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/parts/{id}` — Delete a part
_operationId_: `deletePart`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/{id}/bom` — List BOM children
_operationId_: `listBomChildren`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/{id}/bom` — Add a BOM child
_operationId_: `createBomItem`

**Request body:**
- `application/json` **required** — schema: `BomItemCreateRequest`
  - `alt_group` (object)
  - `child_part_id` (integer) **required**
  - `effective_from` (object)
  - `effective_to` (object)
  - `ghost_part` (object)
  - `note` (object)
  - `option_scalings` (object) — Quantity scaling for numbered options: {option_id (string): multiplier}. ADDS to the line's base quantity i...
  - `order_index` (integer)
  - `parent_part_id` (integer) **required**
  - `priority` (integer)
  - `quantity` (number)
  - `scrap_percent` (number)
  - _...2 more — see `components.schemas` in `openapi.json`_

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/{id}/bom/explode` — Explode a BOM tree
_operationId_: `explodeBom`

Explode a part's BOM with ghost resolution, effectivity (`as_of`), alternate handling, and product-option scaling. Scope: `parts:read`.

**Request body:**
- `application/json` **required**
  - `alternate_mode` (string)
  - `area_id` (integer) — Optional area context
  - `as_of` (string(date)) — Effectivity date (YYYY-MM-DD)
  - `max_depth` (integer)
  - `product_id` (integer) **required** — Product context for option scaling
  - `resolve_ghosts` (boolean)

**Responses:**
- `200` — BOM explosion
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/{id}/bom/flat` — Get flattened BOM
_operationId_: `getBomFlat`

Returns a flat list of all BOM items with level indicators.

**Query parameters:**
- `max_depth` (integer) — Maximum traversal depth

**Responses:**
- `200` — Flattened BOM
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/{id}/bom/tree` — Get multi-level BOM tree
_operationId_: `getBomTree`

Returns a recursive tree of BOM items with cycle detection.

**Query parameters:**
- `max_depth` (integer) — Maximum traversal depth
- `max_nodes` (integer) — Maximum number of nodes to return

**Responses:**
- `200` — BOM tree
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/{id}/bom/validate` — Validate BOM integrity
_operationId_: `validateBom`

Check for cycles, missing children, duplicates, and self-references.

**Responses:**
- `200` — Validation result
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/{id}/ghost/materialize` — Materialize a ghost assembly
_operationId_: `materializeGhostAssembly`

Materialize a ghost (phantom) part's resolved BOM into a concrete assembly, or dissolve it. Returns 201 when a new part is created, 200 when an existing part is reused or the ghost is dissolved. Scope: `parts:write`.

**Request body:**
- `application/json` **required**
  - `new_part_name` (string|null)
  - `new_part_number` (string|null)
  - `parent_quantity` (number|null)
  - `resolve_mode` (string|null)
  - `resolved_child_ids` (array<integer>) **required**

**Responses:**
- `200` — Materialized (existing part reused, or ghost dissolved)
- `201` — Created
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/{id}/ghost/resolve` — Resolve a ghost assembly
_operationId_: `resolveGhostAssembly`

Resolve a ghost (phantom) assembly into its configured 100% BOM. Scope: `parts:read`.

**Request body:**
- `application/json`
  - `as_of` (string(date)) — Effectivity date (YYYY-MM-DD)
  - `condition_option_ids` (array<integer>) — Option IDs whose conditioned children to include

**Responses:**
- `200` — Resolved ghost BOM
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/{id}/ghost/status` — Get ghost status for a part
_operationId_: `getGhostStatus`

Check ghost (phantom assembly) status and ghost-toggle eligibility for a part. Scope: `parts:read`.

**Responses:**
- `200` — Ghost status
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/{id}/placements` — List part placements
_operationId_: `listPartPlacements`

Returns **all** placements for this part in a single `{"data": [...]}` response — this endpoint is not paginated and takes no `cursor`/`limit`. To read a whole configurable BOM without one request per part, use `GET /areas/{id}/placements`, which is cursor-paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/parts/{id}/placements` — Create a part placement
_operationId_: `createPartPlacement`

**Request body:**
- `application/json` **required** — schema: `PartPlacementCreateRequest`
  - `area_id` (integer) **required**
  - `ghost_part` (boolean)
  - `option_scalings` (object) — Quantity scaling for numbered options: {option_id (string): multiplier}. ADDS to the line's base quantity i...
  - `order_index` (integer)
  - `part_id` (integer) **required**
  - `quantity` (number)
  - `uom` (string)
  - `usage_subclauses` (object) — Conditions that make this line configurable. The subclauses are evaluated left-to-right — each joins the ru...

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/{id}/where-used` — Find where a part is used
_operationId_: `getWhereUsed`

Reverse BOM lookup: find all parent assemblies that reference this part.

**Responses:**
- `200` — Where-used list
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/parts/{partId}/changelog` — List part changelog
_operationId_: `listPartChangelog`

List change history entries for a part.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Price Lists

Price lists represent different pricing contexts (e.g., currencies, regions, customer tiers). Each price list can override option prices. Scope: `prices:read`, `prices:write`.

### `GET /api/v1/price-lists` — List price lists
_operationId_: `listPriceLists`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/price-lists` — Create a price list
_operationId_: `createPriceList`

**Request body:**
- `application/json` **required** — schema: `PriceListCreateRequest`
  - `currency` (string)
  - `description` (string)
  - `is_base` (boolean)
  - `name` (string) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/price-lists/reorder` — Reorder price lists
_operationId_: `reorderPriceLists`

**Request body:**
- `application/json` **required** — schema: `PriceListReorderRequest`
  - `order` (array<integer>) **required** — Price list IDs in desired order

**Responses:**
- `200` — Reordered
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/price-lists/{id}` — Get a price list
_operationId_: `getPriceList`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/price-lists/{id}` — Update a price list
_operationId_: `updatePriceList`

**Request body:**
- `application/json` **required** — schema: `PriceListUpdateRequest`
  - `currency` (object)
  - `description` (object)
  - `is_base` (object)
  - `name` (object)
  - `order_index` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/price-lists/{id}` — Partially update a price list
_operationId_: `patchPriceList`

**Request body:**
- `application/json` **required** — schema: `PriceListUpdateRequest`
  - `currency` (object)
  - `description` (object)
  - `is_base` (object)
  - `name` (object)
  - `order_index` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/price-lists/{id}` — Delete a price list
_operationId_: `deletePriceList`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/price-lists/{priceListId}/overrides` — List price list overrides
_operationId_: `listPriceListOverrides`

List all option price overrides for a given price list.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Price Overrides

Per-option price overrides scoped to area and price list combinations. Supports individual CRUD and bulk replace operations. Scope: `prices:read`, `prices:write`.

### `GET /api/v1/options/{optionId}/price-overrides` — List price overrides for an option
_operationId_: `listPriceOverrides`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/options/{optionId}/price-overrides` — Create a price override
_operationId_: `createPriceOverride`

**Request body:**
- `application/json` **required** — schema: `PriceOverrideCreateRequest`
  - `area_id` (integer) **required**
  - `override_price` (object) **required** — Override price value
  - `price_list_id` (integer) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/options/{optionId}/price-overrides/replace` — Replace all price overrides
_operationId_: `replacePriceOverrides`

Delete all existing overrides and replace with the provided set.

**Request body:**
- `application/json` **required** — schema: `PriceOverrideReplaceRequest`
  - `overrides` (array<PriceOverrideCreateRequest>) **required** — Complete list of overrides to set (replaces all existing).

**Responses:**
- `200` — Replaced
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/options/{optionId}/price-overrides/{overrideId}` — Update a price override
_operationId_: `updatePriceOverride`

**Request body:**
- `application/json` **required** — schema: `PriceOverrideUpdateRequest`
  - `override_price` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/options/{optionId}/price-overrides/{overrideId}` — Partially update a price override
_operationId_: `patchPriceOverride`

**Request body:**
- `application/json` **required** — schema: `PriceOverrideUpdateRequest`
  - `override_price` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/options/{optionId}/price-overrides/{overrideId}` — Delete a price override
_operationId_: `deletePriceOverride`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Product Media

Video links and 3D model links for products. Scope: `products:read`, `products:write`.

### `GET /api/v1/products/{productId}/models` — List 3D model links
_operationId_: `listModelLinks`

List 3D model links for a product (max 20).

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/models` — Create 3D model link
_operationId_: `createModelLink`

**Request body:**
- `application/json` **required** — schema: `ModelLinkCreateRequest`
  - `url` (string) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/models/reorder` — Reorder 3D model links
_operationId_: `reorderModelLinks`

**Request body:**
- `application/json` **required** — schema: `ModelLinkReorderRequest`
  - `order` (array<integer>) **required** — 3D model link IDs in desired order

**Responses:**
- `200` — Reordered
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/products/{productId}/models/{modelId}` — Update 3D model link
_operationId_: `updateModelLink`

**Request body:**
- `application/json` **required** — schema: `ModelLinkUpdateRequest`
  - `url` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/products/{productId}/models/{modelId}` — Delete 3D model link
_operationId_: `deleteModelLink`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/products/{productId}/videos` — List video links
_operationId_: `listVideoLinks`

List video links for a product (max 20).

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/videos` — Create video link
_operationId_: `createVideoLink`

**Request body:**
- `application/json` **required** — schema: `VideoLinkCreateRequest`
  - `url` (string) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/videos/reorder` — Reorder video links
_operationId_: `reorderVideoLinks`

**Request body:**
- `application/json` **required** — schema: `VideoLinkReorderRequest`
  - `order` (array<integer>) **required** — Video link IDs in desired order

**Responses:**
- `200` — Reordered
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/products/{productId}/videos/{videoId}` — Update video link
_operationId_: `updateVideoLink`

**Request body:**
- `application/json` **required** — schema: `VideoLinkUpdateRequest`
  - `url` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/products/{productId}/videos/{videoId}` — Delete video link
_operationId_: `deleteVideoLink`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Products

Products are the top-level entities in your catalog. Each product contains areas, groups, and options that define its configurable structure. Scope: `products:read`, `products:write`.

### `GET /api/v1/products` — List products
_operationId_: `listProducts`

Returns a paginated list of products for your company. Use `search` to filter by name and `status` to filter by lifecycle state.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `search` (string) — Filter by name (case-insensitive partial match)
- `status` (string) — Filter: `active` (default), `inactive`, or `all`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products` — Create a product
_operationId_: `createProduct`

Create a new product in your catalog. Returns the created product with a `Location` header pointing to the new resource.

**Request body:**
- `application/json` **required** — schema: `ProductCreateRequest`
  - `base_price` (object) — Base price (string or number)
  - `catalog_meta` (object) — Catalog display metadata (tags, badges, specs_summary, sort_priority, filters)
  - `currency` (object) — Accepted but ignored — currency is derived from the company's base price list
  - `description` (string) — Product description
  - `integration_metadata` (object) — Metadata for external integrations
  - `is_active` (boolean) — Whether the product is active
  - `language` (string) — Language code
  - `name` (string) **required** — Product name

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/reorder` — Reorder products
_operationId_: `reorderProducts`

**Request body:**
- `application/json` **required** — schema: `ProductReorderRequest`
  - `order` (array<integer>) **required** — Product IDs in desired order

**Responses:**
- `200` — Reordered
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/products/{id}` — Get a product
_operationId_: `getProduct`

Retrieve a single product by ID. Use `expand` to inline related resources. Supported expansions: `areas`, `areas.groups`, `areas.groups.options`, `gallery`.

**Query parameters:**
- `expand` (string) — Comma-separated list of expansions: `areas`, `gallery`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/products/{id}` — Update a product
_operationId_: `updateProduct`

**Request body:**
- `application/json` **required** — schema: `ProductUpdateRequest`
  - `base_price` (object)
  - `catalog_meta` (object) — Catalog display metadata (tags, badges, specs_summary, sort_priority, filters)
  - `currency` (object) — Accepted but ignored — currency is derived from the company's base price list
  - `description` (object)
  - `integration_metadata` (object)
  - `is_active` (object)
  - `language` (object)
  - `name` (object)
  - `order_index` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/products/{id}` — Partially update a product
_operationId_: `patchProduct`

**Request body:**
- `application/json` **required** — schema: `ProductUpdateRequest`
  - `base_price` (object)
  - `catalog_meta` (object) — Catalog display metadata (tags, badges, specs_summary, sort_priority, filters)
  - `currency` (object) — Accepted but ignored — currency is derived from the company's base price list
  - `description` (object)
  - `integration_metadata` (object)
  - `is_active` (object)
  - `language` (object)
  - `name` (object)
  - `order_index` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/products/{id}` — Delete a product
_operationId_: `deleteProduct`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/products/{productId}/areas` — List assigned areas
_operationId_: `listProductAreas`

List all areas assigned to this product with their assignment metadata (area_id, area_name, order_index, enabled). Not paginated.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/areas` — Assign an area to a product
_operationId_: `assignProductArea`

**Request body:**
- `application/json` **required**
  - `area_id` (integer) **required**
  - `enabled` (boolean)
  - `order_index` (integer)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/areas/reorder` — Reorder product areas
_operationId_: `reorderProductAreas`

**Request body:**
- `application/json` **required**
  - `order` (array<integer>) **required** — Ordered list of area IDs

**Responses:**
- `200` — Reordered
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/areas/replace` — Replace all product area assignments
_operationId_: `replaceProductAreas`

**Request body:**
- `application/json` **required**
  - `areas` (array<object>) **required**

**Responses:**
- `200` — Replaced
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/products/{productId}/areas/{areaId}` — Remove area from product
_operationId_: `removeProductArea`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/products/{productId}/configurations` — List product configurations
_operationId_: `listProductConfigurations`

List all configurations created for a product.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/products/{productId}/price-overrides` — List product price overrides
_operationId_: `listProductPriceOverrides`

List all price-list overrides for a product's base price.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/price-overrides` — Create product price override
_operationId_: `createProductPriceOverride`

**Request body:**
- `application/json` **required** — schema: `ProductPriceOverrideCreateRequest`
  - `override_price` (object) **required** — Override price value
  - `price_list_id` (integer) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/price-overrides/replace` — Replace all product price overrides
_operationId_: `replaceProductPriceOverrides`

Bulk-replace all price-list overrides for a product.

**Request body:**
- `application/json` **required** — schema: `ProductPriceOverrideReplaceRequest`
  - `overrides` (array<ProductPriceOverrideCreateRequest>) **required** — Complete list of overrides to set (replaces all existing).

**Responses:**
- `200` — Replaced
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/products/{productId}/price-overrides/{overrideId}` — Update product price override
_operationId_: `updateProductPriceOverride`

**Request body:**
- `application/json` **required** — schema: `ProductPriceOverrideUpdateRequest`
  - `override_price` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/products/{productId}/price-overrides/{overrideId}` — Partially update product price override
_operationId_: `patchProductPriceOverride`

**Request body:**
- `application/json` **required** — schema: `ProductPriceOverrideUpdateRequest`
  - `override_price` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/products/{productId}/price-overrides/{overrideId}` — Delete product price override
_operationId_: `deleteProductPriceOverride`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/products/{productId}/pricing-presets` — List pricing presets
_operationId_: `listPricingPresets`

List pricing adjustment presets (surcharges, discounts, fees) for a product.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/pricing-presets` — Create pricing preset
_operationId_: `createPricingPreset`

**Request body:**
- `application/json` **required** — schema: `PricingPresetCreateRequest`
  - `amount_type` (string) **required**
  - `category` (string) **required**
  - `default_on` (boolean)
  - `key` (string) **required**
  - `label` (string) **required**
  - `taxable` (boolean)
  - `value` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/products/{productId}/pricing-presets/reorder` — Reorder pricing presets
_operationId_: `reorderPricingPresets`

**Request body:**
- `application/json` **required** — schema: `PricingPresetReorderRequest`
  - `order` (array<integer>) **required**

**Responses:**
- `200` — Reordered
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/products/{productId}/pricing-presets/{presetId}` — Update pricing preset
_operationId_: `updatePricingPreset`

**Request body:**
- `application/json` **required** — schema: `PricingPresetUpdateRequest`
  - `amount_type` (object)
  - `category` (object)
  - `default_on` (object)
  - `label` (object)
  - `taxable` (object)
  - `value` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/products/{productId}/pricing-presets/{presetId}` — Partially update pricing preset
_operationId_: `patchPricingPreset`

**Request body:**
- `application/json` **required** — schema: `PricingPresetUpdateRequest`
  - `amount_type` (object)
  - `category` (object)
  - `default_on` (object)
  - `label` (object)
  - `taxable` (object)
  - `value` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/products/{productId}/pricing-presets/{presetId}` — Delete pricing preset
_operationId_: `deletePricingPreset`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Pull Requests

Branch review workflows — create, review, approve, and merge pull requests. Scope: `parts:read`, `parts:write`.

### `GET /api/v1/branches/{branchId}/pull-requests` — List pull requests
_operationId_: `listPullRequests`

List pull requests for a branch. Scope: `parts:read`.

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/branches/{branchId}/pull-requests` — Create pull request
_operationId_: `createPullRequest`

**Request body:**
- `application/json` **required** — schema: `PullRequestCreateRequest`
  - `description` (object)
  - `title` (string) **required** — Pull request title

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/pull-requests/{prId}` — Get pull request
_operationId_: `getPullRequest`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/pull-requests/{prId}` — Update pull request
_operationId_: `updatePullRequest`

**Request body:**
- `application/json` **required** — schema: `PullRequestUpdateRequest`
  - `description` (object)
  - `state` (object)
  - `title` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/pull-requests/{prId}` — Partially update pull request
_operationId_: `patchPullRequest`

**Request body:**
- `application/json` **required** — schema: `PullRequestUpdateRequest`
  - `description` (object)
  - `state` (object)
  - `title` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Quotes

Quotes contain line items with pricing. They go through status transitions (draft → approved → presented → accepted/rejected) and support revisions for version control. Scope: `quotes:read`, `quotes:write`.

### `GET /api/v1/quotes` — List quotes
_operationId_: `listQuotes`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)
- `status` (string) — Filter by status
- `opportunity_id` (integer) — Filter by opportunity

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/quotes` — Create a quote
_operationId_: `createQuote`

Create a quote for an opportunity. If no opportunity_id is given but a customer_id is provided, an opportunity is auto-created.

**Request body:**
- `application/json` **required** — schema: `QuoteCreateRequest`
  - `customer_id` (object)
  - `integration_metadata` (object)
  - `notes` (object)
  - `opportunity_id` (object)
  - `price_list_id` (integer) **required**
  - `valid_from` (object)
  - `valid_until` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/quotes/{id}` — Get a quote
_operationId_: `getQuote`

Returns the quote with embedded line items.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/quotes/{id}` — Update a quote
_operationId_: `updateQuote`

**Request body:**
- `application/json` **required** — schema: `QuoteUpdateRequest`
  - `discount_amount` (object)
  - `discount_percent` (object)
  - `integration_metadata` (object)
  - `notes` (object)
  - `tax_amount` (object)
  - `terms_and_conditions` (object)
  - `valid_from` (object)
  - `valid_until` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/quotes/{id}` — Partially update a quote
_operationId_: `patchQuote`

**Request body:**
- `application/json` **required** — schema: `QuoteUpdateRequest`
  - `discount_amount` (object)
  - `discount_percent` (object)
  - `integration_metadata` (object)
  - `notes` (object)
  - `tax_amount` (object)
  - `terms_and_conditions` (object)
  - `valid_from` (object)
  - `valid_until` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/quotes/{id}` — Delete a quote
_operationId_: `deleteQuote`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/quotes/{id}/line-items` — List line items
_operationId_: `listLineItems`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/quotes/{id}/line-items` — Add a line item
_operationId_: `createLineItem`

**Request body:**
- `application/json` **required** — schema: `LineItemCreateRequest`
  - `configuration_code` (object)
  - `discount_percent` (object)
  - `integration_metadata` (object)
  - `notes` (object)
  - `product_id` (integer) **required**
  - `quantity` (integer)
  - `unit_price` (object)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/quotes/{id}/line-items/{item_id}` — Update a line item
_operationId_: `updateLineItem`

**Request body:**
- `application/json` **required** — schema: `LineItemUpdateRequest`
  - `discount_amount` (object)
  - `discount_percent` (object)
  - `integration_metadata` (object)
  - `notes` (object)
  - `position` (object)
  - `quantity` (object)
  - `unit_price` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/quotes/{id}/line-items/{item_id}` — Partially update a line item
_operationId_: `patchLineItem`

**Request body:**
- `application/json` **required** — schema: `LineItemUpdateRequest`
  - `discount_amount` (object)
  - `discount_percent` (object)
  - `integration_metadata` (object)
  - `notes` (object)
  - `position` (object)
  - `quantity` (object)
  - `unit_price` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/quotes/{id}/line-items/{item_id}` — Remove a line item
_operationId_: `deleteLineItem`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/quotes/{id}/revise` — Create a new revision
_operationId_: `reviseQuote`

Create a new version of this quote, incrementing the version number.

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/quotes/{id}/revisions` — List quote revisions
_operationId_: `listQuoteRevisions`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/quotes/{id}/status` — Update quote status
_operationId_: `updateQuoteStatus`

**Request body:**
- `application/json` **required** — schema: `QuoteStatusUpdateRequest`
  - `status` (string) **required**

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/quotes/{quoteId}/contacts` — List quote contacts
_operationId_: `listQuoteContacts`

List contact persons linked to a quote.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/quotes/{quoteId}/contacts` — Add contact to quote
_operationId_: `addQuoteContact`

**Request body:**
- `application/json` **required** — schema: `QuoteContactAddRequest`
  - `contact_id` (integer) **required**
  - `role` (string)

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/quotes/{quoteId}/contacts/{contactId}` — Remove contact from quote
_operationId_: `removeQuoteContact`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/quotes/{quoteId}/details` — Get quote details
_operationId_: `getQuoteDetails`

Retrieve extended details for a quote (payment terms, shipping, internal notes).

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/quotes/{quoteId}/details` — Upsert quote details
_operationId_: `upsertQuoteDetails`

Create or update extended details for a quote.

**Request body:**
- `application/json` **required** — schema: `QuoteDetailsUpsertRequest`
  - `custom_fields` (object)
  - `internal_notes` (string)
  - `payment_terms` (string)
  - `shipping_cost` (string)
  - `shipping_method` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/quotes/{quoteId}/details` — Partially update quote details
_operationId_: `patchQuoteDetails`

**Request body:**
- `application/json` **required** — schema: `QuoteDetailsUpsertRequest`
  - `custom_fields` (object)
  - `internal_notes` (string)
  - `payment_terms` (string)
  - `shipping_cost` (string)
  - `shipping_method` (string)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Safety

Read-only safety reference data — GHS/CLP safety logos, H/P (hazard/precautionary) statements, and ANSI Z535 / ISO 3864 signal words used by the `safety_notice` and `hp_statement` document blocks. Scope: `products:read`.

> **Use these instead of guessing.** Before emitting a `safety_notice` block, call `GET /api/v1/safety-logos[?category=…]` to pick the right ISO 7010 / GHS file. Before emitting an `hp_statement` block, call `GET /api/v1/hp-statements[/{code}]` to validate the code and obtain the locale-resolved text. These endpoints are the single source of truth. Falling back to a default symbol, or hand-typing a CLP text, is the audit finding `default-fallback-symbol` / `mismatched-ghs-pictogram` — and in a CE-marked technical documentation that is a legal defect, not a cosmetic one.

**Categories** returned by `GET /safety-logos`: the five ISO 7010 sets — `warning` (W*), `prohibition` (P*), `mandatory` (M*), `safe_condition` (E*), `fire_protection` (F*) — plus `gefahrstoffe`, the **separate** CLP/GHS pictogram set from Annex V of (EC) 1272/2008. GHS pictograms are not ISO 7010 symbols; never substitute one for the other.

**Statement text is regulated and locale-resolved — never AI-translated.** `GET /hp-statements/{code}` resolves combined codes (`H300+H310`) and enhanced statements carrying slot placeholders. Translations are ECHA-traceable to CLP Annex III / IV / VI on EUR-Lex.

Full block contracts, the 32-locale signal-word catalogue, and the 24-locale H/P/EUH catalogue live in `skills/rattle-safety-notices/` and `skills/rattle-ghs-statements/`.

### `GET /api/v1/hp-statements` — List H/P statements
_operationId_: `listHpStatements`

Hazard/precautionary statement codes and texts for a locale, with an optional GHS pictogram map. Scope: `products:read`.

**Query parameters:**
- `locale` (string) — Locale code
- `include_ghs_map` (string) — Include the H-code → GHS pictogram map (true/false)

**Responses:**
- `200` — H/P statements
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/hp-statements/{code}` — Resolve an H/P statement
_operationId_: `getHpStatement`

Resolve a single H/P statement by code, optionally filling slot placeholders. Scope: `products:read`.

**Query parameters:**
- `locale` (string) — Locale code
- `slot_1` (string) — Placeholder value for an enhanced variant
- `slot_2` (string) — Placeholder value for an enhanced variant

**Responses:**
- `200` — H/P statement
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/safety-logos` — List safety logos
_operationId_: `listSafetyLogos`

GHS/CLP safety logos grouped by category. Scope: `products:read`.

**Query parameters:**
- `category` (string) — Filter to a single category id

**Responses:**
- `200` — Safety logos
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/safety-notices/signal-words` — List signal words
_operationId_: `listSignalWords`

ANSI Z535 / ISO 3864 signal words for one locale (pass `locale`) or all locales (omit it). Scope: `products:read`.

**Query parameters:**
- `locale` (string) — Locale code; omit for all locales

**Responses:**
- `200` — Signal words
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Translations

Product catalog translations and dictionary entries. Scope: `products:read`, `products:write`.

### `GET /api/v1/translations` — List translations
_operationId_: `listTranslations`

Returns translations filtered by entity and language.

**Query parameters:**
- `entity_type` (string) — Entity type (product, area, group, option)
- `entity_id` (integer) — Entity ID
- `language` (string) — Language code

**Responses:**
- `200` — Translations
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/translations` — Upsert translations
_operationId_: `upsertTranslations`

Create or update translations in bulk.

**Request body:**
- `application/json` **required**
  - `translations` (array<object>) **required**

**Responses:**
- `200` — Updated
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/translations/dictionary` — List dictionary entries
_operationId_: `listDictionaryEntries`

Returns company-wide translation dictionary entries.

**Responses:**
- `200` — Dictionary entries
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/translations/dictionary` — Create or update a dictionary entry
_operationId_: `upsertDictionaryEntry`

**Request body:**
- `application/json` **required**
  - `base_term` (string) **required**
  - `translations` (object) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/translations/dictionary/{entry_id}` — Get a dictionary entry
_operationId_: `getDictionaryEntry`

Retrieve a single translation dictionary entry. Scope: `products:read`.

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/translations/dictionary/{entry_id}` — Replace a dictionary entry
_operationId_: `updateDictionaryEntry`

Update an entry; a supplied `translations` map fully replaces the existing one. Scope: `products:write`.

**Request body:**
- `application/json` **required**
  - `base_term` (string)
  - `translations` (object) — Replaces the entry's full translation map

**Responses:**
- `200` — Success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/translations/dictionary/{entry_id}` — Partially update a dictionary entry
_operationId_: `patchDictionaryEntry`

Same semantics as PUT — a supplied `translations` map replaces (does not merge). Scope: `products:write`.

**Request body:**
- `application/json` **required**
  - `base_term` (string)
  - `translations` (object) — Replaces the entry's full translation map

**Responses:**
- `200` — Success
- `400` — Bad Request (`application/json` → `ProblemDetails`)
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `409` — Conflict (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/translations/dictionary/{entry_id}` — Delete a dictionary entry
_operationId_: `deleteDictionaryEntry`

Idempotent — returns 204 even if the entry does not exist. Scope: `products:write`.

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

## Webhooks

Subscribe to real-time event notifications via HTTPS callbacks. Deliveries include HMAC-SHA256 signatures for verification. Failed deliveries are retried with exponential backoff. Scope: `webhooks:read`, `webhooks:write`.

### `GET /api/v1/webhooks` — List webhook subscriptions
_operationId_: `listWebhooks`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/webhooks` — Create a webhook subscription
_operationId_: `createWebhook`

Create a subscription for one or more event types. If you provide a `secret`, each delivery will include an `X-Webhook-Signature` header containing the HMAC-SHA256 hex digest of the request body, signed with your secret. The secret is returned only in the creation response — store it securely. The URL must use HTTPS and cannot point to private/internal networks.

**Request body:**
- `application/json` **required** — schema: `WebhookCreateRequest`
  - `events` (array<string>) **required**
  - `name` (object)
  - `secret` (object)
  - `url` (string) **required**

**Responses:**
- `201` — Created
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/webhooks/deliveries/{id}` — Get delivery detail
_operationId_: `getWebhookDelivery`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/webhooks/events` — List available webhook events
_operationId_: `listWebhookEvents`

Returns the catalog of all event types available for webhook subscriptions.

**Responses:**
- `200` — Event catalog
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/webhooks/{id}` — Get a webhook subscription
_operationId_: `getWebhook`

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PUT /api/v1/webhooks/{id}` — Update a webhook subscription
_operationId_: `updateWebhook`

**Request body:**
- `application/json` **required** — schema: `WebhookUpdateRequest`
  - `events` (object)
  - `is_active` (object)
  - `name` (object)
  - `url` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `PATCH /api/v1/webhooks/{id}` — Partially update a webhook subscription
_operationId_: `patchWebhook`

**Request body:**
- `application/json` **required** — schema: `WebhookUpdateRequest`
  - `events` (object)
  - `is_active` (object)
  - `name` (object)
  - `url` (object)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `DELETE /api/v1/webhooks/{id}` — Delete a webhook subscription
_operationId_: `deleteWebhook`

**Responses:**
- `204` — Deleted
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `GET /api/v1/webhooks/{id}/deliveries` — List delivery attempts
_operationId_: `listWebhookDeliveries`

**Query parameters:**
- `cursor` (string) — Opaque cursor for the next page
- `limit` (integer) — Items per page (server enforces configured maximum)

**Responses:**
- `200` — Success
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/webhooks/{id}/rotate-secret` — Rotate webhook signing secret
_operationId_: `rotateWebhookSecret`

Generate a new signing secret. The new secret is returned in the response (shown only once). The old secret remains valid briefly during rollover — verify signatures against both secrets during the transition.

**Responses:**
- `200` — Secret rotated
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

### `POST /api/v1/webhooks/{id}/test` — Send a test event
_operationId_: `testWebhook`

Queue a test delivery to verify the webhook endpoint.

**Responses:**
- `200` — Test queued
- `401` — Authentication required (`application/json` → `ProblemDetails`)
- `404` — Not found (`application/json` → `ProblemDetails`)
- `422` — Validation error (`application/json` → `ProblemDetails`)
- `429` — Rate limited (`application/json` → `ProblemDetails`)

---

_End of generated reference._
