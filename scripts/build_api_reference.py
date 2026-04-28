#!/usr/bin/env python3
"""Regenerate docs/API_REFERENCE.md from docs/openapi.json.

This is the single source of truth for the human-readable API reference.
Re-run after replacing docs/openapi.json with a newer spec download:

    python3 scripts/build_api_reference.py

Also mirrors the output into skills/rattle-api/references/api-reference.md
and copies the spec into skills/rattle-api/references/openapi.json so the
plugin Skill stays in sync.
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "docs" / "openapi.json"
OUT_PATH = ROOT / "docs" / "API_REFERENCE.md"
SKILL_REF_DIR = ROOT / "skills" / "rattle-api" / "references"

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


def load_spec() -> dict[str, Any]:
    if not SPEC_PATH.exists():
        sys.exit(f"OpenAPI spec not found at {SPEC_PATH}")
    return json.loads(SPEC_PATH.read_text())


def deref(spec: dict[str, Any], schema: dict[str, Any] | None) -> tuple[str | None, dict[str, Any] | None]:
    """Return (ref_name, resolved_schema). If schema is a $ref, resolve one level."""
    if not schema:
        return None, None
    ref = schema.get("$ref")
    if ref and ref.startswith("#/components/schemas/"):
        name = ref.rsplit("/", 1)[-1]
        resolved = spec.get("components", {}).get("schemas", {}).get(name) or {}
        return name, resolved
    return None, schema


def schema_type(schema: dict[str, Any] | None) -> str:
    if not schema:
        return "?"
    t = schema.get("type")
    if t == "array":
        items = schema.get("items") or {}
        if "$ref" in items:
            return f"array<{items['$ref'].rsplit('/',1)[-1]}>"
        return f"array<{items.get('type','?')}>"
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if isinstance(t, list):
        return "|".join(t)
    fmt = schema.get("format")
    if fmt:
        return f"{t}({fmt})"
    return t or ("enum" if "enum" in schema else "object")


def render_field_list(spec: dict[str, Any], schema: dict[str, Any], max_fields: int = 12) -> list[str]:
    """Render a bulleted field list for an object schema."""
    out: list[str] = []
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    for name in list(props.keys())[:max_fields]:
        f = props[name] or {}
        ftype = schema_type(f)
        req = " **required**" if name in required else ""
        desc = (f.get("description") or "").strip().splitlines()[0] if f.get("description") else ""
        if desc and len(desc) > 110:
            desc = desc[:107] + "..."
        line = f"  - `{name}` ({ftype}){req}"
        if desc:
            line += f" — {desc}"
        out.append(line)
    if len(props) > max_fields:
        out.append(f"  - _...{len(props) - max_fields} more — see `components.schemas` in `openapi.json`_")
    return out


def render_request_body(spec: dict[str, Any], op: dict[str, Any]) -> list[str]:
    rb = op.get("requestBody") or {}
    if not rb:
        return []
    out = ["", "**Request body:**"]
    required = " **required**" if rb.get("required") else ""
    content = rb.get("content") or {}
    for ct, payload in content.items():
        schema = payload.get("schema") or {}
        ref_name, resolved = deref(spec, schema)
        if ref_name:
            out.append(f"- `{ct}`{required} — schema: `{ref_name}`")
        else:
            out.append(f"- `{ct}`{required}")
        if resolved and resolved.get("type") == "object" and resolved.get("properties"):
            out.extend(render_field_list(spec, resolved))
        elif resolved and "oneOf" in resolved:
            options = [d.get("$ref","").rsplit("/",1)[-1] or d.get("type","?") for d in resolved["oneOf"]]
            out.append(f"  - oneOf: {', '.join(options)}")
    return out


def render_responses(spec: dict[str, Any], op: dict[str, Any]) -> list[str]:
    resps = op.get("responses") or {}
    if not resps:
        return []
    out = ["", "**Responses:**"]
    for code in sorted(resps.keys(), key=lambda k: (k != "default", k)):
        r = resps[code] or {}
        desc = (r.get("description") or "").strip().splitlines()[0]
        line = f"- `{code}` — {desc}" if desc else f"- `{code}`"
        content = r.get("content") or {}
        for ct, payload in content.items():
            schema = payload.get("schema") or {}
            ref_name, _ = deref(spec, schema)
            if ref_name:
                line += f" (`{ct}` → `{ref_name}`)"
                break
            elif schema.get("type") == "array":
                items = schema.get("items") or {}
                ref = items.get("$ref","").rsplit("/",1)[-1] or items.get("type","?")
                line += f" (`{ct}` → array<{ref}>)"
                break
        out.append(line)
    return out


def render_parameters(op: dict[str, Any]) -> list[str]:
    params = op.get("parameters") or []
    if not params:
        return []
    by_loc: dict[str, list[dict]] = defaultdict(list)
    for p in params:
        by_loc[p.get("in", "?")].append(p)
    out: list[str] = []
    for loc in ("path", "query", "header", "cookie"):
        if loc not in by_loc:
            continue
        out.append("")
        out.append(f"**{loc.title()} parameters:**")
        for p in by_loc[loc]:
            name = p.get("name", "?")
            schema = p.get("schema") or {}
            ftype = schema_type(schema)
            req = " **required**" if p.get("required") else ""
            desc = (p.get("description") or "").strip().splitlines()[0] if p.get("description") else ""
            if desc and len(desc) > 110:
                desc = desc[:107] + "..."
            line = f"- `{name}` ({ftype}){req}"
            if desc:
                line += f" — {desc}"
            out.append(line)
    return out


def slugify(text: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")


PROSE_HEADER = """# Rattle REST API Reference

> Generated from `docs/openapi.json` by `scripts/build_api_reference.py`.
> Re-run that script after replacing the spec file to keep this document in sync.
> **Do not hand-edit** — changes will be overwritten on the next build.

## Overview

- **Base URL**: `https://www.rattleapp.de/api/v1` (override via env var `RATTLE_BASE_URL`).
- **OpenAPI version**: __OPENAPI_VERSION__
- **Spec version**: __SPEC_VERSION__
- **Operations**: __OP_COUNT__ across __PATH_COUNT__ paths and __TAG_COUNT__ resource groups.

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

- `POST /constraints` uses `X-Constraints-Version` (read latest from `GET /constraints?product_id=…`, send back). Server returns `412 Precondition Failed` if stale.

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
"""


def render(spec: dict[str, Any]) -> str:
    info = spec.get("info") or {}
    paths = spec.get("paths") or {}
    tags_meta = {t["name"]: t for t in (spec.get("tags") or []) if isinstance(t, dict) and "name" in t}

    # Index ops by tag
    tag_ops: dict[str, list[tuple[str, str, dict[str, Any]]]] = defaultdict(list)
    op_count = 0
    for path, methods in paths.items():
        for m, op in methods.items():
            if m not in HTTP_METHODS or not isinstance(op, dict):
                continue
            op_count += 1
            tags = op.get("tags") or ["(untagged)"]
            for tag in tags:
                tag_ops[tag].append((m.upper(), path, op))

    # Sort each tag's ops by (path, method order)
    method_order = {m.upper(): i for i, m in enumerate(("get", "post", "put", "patch", "delete", "head", "options"))}
    for tag in tag_ops:
        tag_ops[tag].sort(key=lambda t: (t[1], method_order.get(t[0], 99)))

    sorted_tags = sorted(tag_ops.keys(), key=str.lower)

    out: list[str] = []
    out.append(
        PROSE_HEADER
        .replace("__OPENAPI_VERSION__", spec.get("openapi", "?"))
        .replace("__SPEC_VERSION__", info.get("version", "?"))
        .replace("__OP_COUNT__", str(op_count))
        .replace("__PATH_COUNT__", str(len(paths)))
        .replace("__TAG_COUNT__", str(len(sorted_tags)))
    )

    # Tag overview
    out.append("\n## Resource groups")
    out.append("")
    out.append("| Tag | Operations | Anchor |")
    out.append("| --- | ---: | --- |")
    for tag in sorted_tags:
        anchor = slugify(tag)
        out.append(f"| {tag} | {len(tag_ops[tag])} | [#{anchor}](#{anchor}) |")

    # Quick reference table — every operation
    out.append("\n## Quick reference (all operations)")
    out.append("")
    out.append("| Tag | Method | Path | Summary |")
    out.append("| --- | --- | --- | --- |")
    for tag in sorted_tags:
        for method, path, op in tag_ops[tag]:
            summary = (op.get("summary") or "").replace("|", "\\|")
            out.append(f"| {tag} | {method} | `{path}` | {summary} |")

    # Per-tag detailed sections
    for tag in sorted_tags:
        out.append(f"\n---\n\n## {tag}")
        meta = tags_meta.get(tag) or {}
        if meta.get("description"):
            out.append("")
            out.append(meta["description"].strip())
        for method, path, op in tag_ops[tag]:
            summary = op.get("summary") or ""
            out.append("")
            out.append(f"### `{method} {path}` — {summary}".rstrip(" —"))
            op_id = op.get("operationId")
            if op_id:
                out.append(f"_operationId_: `{op_id}`")
            desc = (op.get("description") or "").strip()
            if desc:
                out.append("")
                out.append(desc)
            out.extend(render_parameters(op))
            out.extend(render_request_body(spec, op))
            out.extend(render_responses(spec, op))

    out.append("")
    out.append("---")
    out.append("")
    out.append("_End of generated reference._")
    return "\n".join(out) + "\n"


def main() -> int:
    spec = load_spec()
    rendered = render(spec)
    OUT_PATH.write_text(rendered)
    print(f"Wrote {OUT_PATH} ({len(rendered):,} bytes)")

    # Mirror into the skill so the plugin stays in sync.
    SKILL_REF_DIR.mkdir(parents=True, exist_ok=True)
    skill_md = SKILL_REF_DIR / "api-reference.md"
    skill_spec = SKILL_REF_DIR / "openapi.json"
    skill_md.write_text(rendered)
    shutil.copyfile(SPEC_PATH, skill_spec)
    print(f"Mirrored to {skill_md}")
    print(f"Mirrored to {skill_spec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
