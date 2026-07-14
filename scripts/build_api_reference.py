#!/usr/bin/env python3
"""Regenerate docs/API_REFERENCE.md from the Rattle OpenAPI spec.

Pull the spec straight from the live docs — this is the default, because a
checked-in copy silently goes stale and nobody notices until an agent calls an
endpoint that moved:

    python3 scripts/build_api_reference.py            # fetch live, then render
    python3 scripts/build_api_reference.py --offline  # render from the local copy

`--offline` exists for CI and for working on a plane; it renders whatever is in
docs/openapi.json without touching the network.

Fetching rewrites docs/openapi.json, then mirrors both the rendered Markdown and
the spec into skills/rattle-api/references/ so the plugin Skill and the MCP
server (which reads the skill copy) stay in lockstep.

Guidance the spec cannot express — when a model *must* call an endpoint, and what
breaks if it guesses — lives in docs/api-supplement/ and is merged in at render
time. See SUPPLEMENTS below. Never hand-edit the generated output.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "docs" / "openapi.json"
OUT_PATH = ROOT / "docs" / "API_REFERENCE.md"
SKILL_REF_DIR = ROOT / "skills" / "rattle-api" / "references"

# The published spec, served alongside the human docs at
# https://www.rattleapp.de/docs/api/reference
SPEC_URL = "https://www.rattleapp.de/docs/api/openapi.json"

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


def fetch_spec() -> dict[str, Any]:
    """Download the live spec and write it to docs/openapi.json."""
    print(f"Fetching {SPEC_URL} …", file=sys.stderr)
    # urllib's default User-Agent ("Python-urllib/3.x") is rejected with 403 by
    # the edge in front of rattleapp.de. Identify ourselves properly.
    req = urllib.request.Request(
        SPEC_URL,
        headers={
            "User-Agent": "grimoire-build-api-reference/1.0 (+https://github.com/rattleai/grimoire)",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        sys.exit(
            f"Could not fetch the live spec ({exc}).\n"
            f"Re-run with --offline to render from the checked-in docs/openapi.json instead."
        )

    try:
        spec: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.exit(f"{SPEC_URL} did not return valid JSON: {exc}")

    # Refuse an obviously broken download rather than truncating the reference
    # and mirroring the damage into the skill the agents read.
    if not spec.get("paths"):
        sys.exit(
            f"{SPEC_URL} returned a spec with no paths — refusing to overwrite the local copy."
        )

    SPEC_PATH.write_text(json.dumps(spec, ensure_ascii=False) + "\n")
    print(f"Wrote {SPEC_PATH}", file=sys.stderr)
    return spec


def load_spec() -> dict[str, Any]:
    if not SPEC_PATH.exists():
        sys.exit(f"OpenAPI spec not found at {SPEC_PATH}. Run without --offline to fetch it.")
    spec: dict[str, Any] = json.loads(SPEC_PATH.read_text())
    return spec


def deref(
    spec: dict[str, Any], schema: dict[str, Any] | None
) -> tuple[str | None, dict[str, Any] | None]:
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
            return f"array<{items['$ref'].rsplit('/', 1)[-1]}>"
        return f"array<{items.get('type', '?')}>"
    if "$ref" in schema:
        return str(schema["$ref"]).rsplit("/", 1)[-1]
    if isinstance(t, list):
        return "|".join(t)
    fmt = schema.get("format")
    if fmt:
        return f"{t}({fmt})"
    return t or ("enum" if "enum" in schema else "object")


def render_field_list(
    spec: dict[str, Any], schema: dict[str, Any], max_fields: int = 12
) -> list[str]:
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
        out.append(
            f"  - _...{len(props) - max_fields} more — see `components.schemas` in `openapi.json`_"
        )
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
            options = [
                d.get("$ref", "").rsplit("/", 1)[-1] or d.get("type", "?")
                for d in resolved["oneOf"]
            ]
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
                ref = items.get("$ref", "").rsplit("/", 1)[-1] or items.get("type", "?")
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
            desc = (
                (p.get("description") or "").strip().splitlines()[0] if p.get("description") else ""
            )
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

Tokens are tenant-scoped (`rk_live_*` for production, `rk_test_*` for staging). The Python CLI \
loads them from `RATTLE_API_KEY_<TENANT>` env vars (e.g. `RATTLE_API_KEY_ACME=rk_live_…` → tenant \
`acme`). A small set of admin endpoints accepts a session cookie instead — these are noted \
per-operation in the spec under `SessionAuth`.

## Content type

```
Content-Type: application/json
```

Image uploads use `multipart/form-data` with field name `file`. Accepted types: JPEG, PNG, WebP, \
GIF. Maximum 10 MB.

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

Some endpoints are not paginated and return `{"data": []}` without `meta`. Check the response \
schema per operation.

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

422 responses include an `errors` array with per-field details. Always preserve `request_id` — \
Rattle support can use it to trace the request server-side.

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

A handful of bulk-replace endpoints accept an `X-<Resource>-Version` header so concurrent clients \
cannot silently overwrite each other:

- `POST /constraints` uses `X-Constraints-Version` (read latest from \
`GET /constraints?product_id=…`, send back). Server returns **`409 Conflict`** if stale \
(problem-detail body's `detail` contains `Version conflict:` to distinguish stale-version from \
other 409 conflicts; NOT `412 Precondition Failed`). Same OCC pattern applies to \
`POST /constraints/area` (`X-Areas-Version`) and `POST /price-lists/*` writes \
(`X-Price-Lists-Version`).

Other replace-style endpoints follow the same convention where applicable — see the operation's \
parameter list for `X-*-Version` headers.

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

Other languages should mirror these patterns — there is nothing Rattle-specific about the wrapper \
itself.
"""


# ---------------------------------------------------------------------------
# Supplements — consulting guidance the OpenAPI spec cannot carry
# ---------------------------------------------------------------------------
# A spec describes what an endpoint *accepts*. It does not say when a model must
# call it, or what happens if it guesses instead. That judgement is exactly what
# the skills need, and it has to live somewhere the generator will not destroy.
#
# A supplement is prose prepended to a tag's section in the rendered reference.
# It is an INPUT to the generator, never an edit to its output — because the
# latter was tried, and it was a loaded gun: the Safety guidance and the
# corrected 409 OCC status had been hand-written into the *generated* mirror,
# and CLAUDE.md tells contributors to re-run this script whenever the spec
# changes. The next legitimate run would have silently deleted 197 lines of
# verified knowledge and reverted 409 back to 412.
#
# `tag` must name a tag the spec actually defines. If the spec drops or renames
# it, the generator fails loudly rather than quietly discarding the guidance.
#
# To add one: drop a Markdown file in docs/api-supplement/ and register it here.
SUPPLEMENTS: list[dict[str, str]] = [
    {"tag": "Safety", "file": "safety-reference.md"},
]

SUPPLEMENT_DIR = Path(__file__).resolve().parent.parent / "docs" / "api-supplement"


def load_supplements(known_tags: set[str]) -> dict[str, str]:
    """Map tag -> guidance body, failing loudly rather than dropping content."""
    loaded: dict[str, str] = {}
    for sup in SUPPLEMENTS:
        body_path = SUPPLEMENT_DIR / sup["file"]
        if not body_path.exists():
            sys.exit(
                f"Supplement for tag '{sup['tag']}' declares {body_path}, which does not exist. "
                "Regenerating without it would silently drop that guidance from the reference."
            )
        if sup["tag"] not in known_tags:
            sys.exit(
                f"Supplement targets tag '{sup['tag']}', which the OpenAPI spec no longer "
                f"defines (known tags: {', '.join(sorted(known_tags))}). The spec was probably "
                "renamed or the group removed. Re-point the supplement rather than losing it."
            )
        # strip(), not rstrip(): render() emits the blank line after the heading,
        # so a leading newline in the body would double it.
        loaded[sup["tag"]] = body_path.read_text().strip()
    return loaded


def render(spec: dict[str, Any]) -> str:
    info = spec.get("info") or {}
    paths = spec.get("paths") or {}
    tags_meta = {
        t["name"]: t for t in (spec.get("tags") or []) if isinstance(t, dict) and "name" in t
    }
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
    method_order = {
        m.upper(): i
        for i, m in enumerate(("get", "post", "put", "patch", "delete", "head", "options"))
    }
    for tag in tag_ops:
        tag_ops[tag].sort(key=lambda t: (t[1], method_order.get(t[0], 99)))

    sorted_tags = sorted(tag_ops.keys(), key=str.lower)
    supplements = load_supplements(set(sorted_tags))

    out: list[str] = []
    out.append(
        PROSE_HEADER.replace("__OPENAPI_VERSION__", spec.get("openapi", "?"))
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

    # Per-tag detailed sections. A supplement's guidance is prepended to its
    # tag's section, ahead of the spec-derived operations — the spec says what
    # an endpoint accepts; the supplement says when a model must call it.
    for tag in sorted_tags:
        out.append(f"\n---\n\n## {tag}")

        meta = tags_meta.get(tag) or {}
        if meta.get("description"):
            out.append("")
            out.append(meta["description"].strip())

        if tag in supplements:
            out.append("")
            out.append(supplements[tag])

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
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--offline",
        action="store_true",
        help="Render from the checked-in docs/openapi.json instead of fetching the live spec.",
    )
    args = ap.parse_args()

    before = SPEC_PATH.read_bytes() if SPEC_PATH.exists() else b""
    spec = load_spec() if args.offline else fetch_spec()

    if not args.offline:
        if SPEC_PATH.read_bytes() == before:
            print("Spec unchanged — the local copy was already current.", file=sys.stderr)
        else:
            ops = sum(1 for item in spec["paths"].values() for m in item if m in HTTP_METHODS)
            print(
                f"Spec updated: {ops} operations across {len(spec['paths'])} paths.",
                file=sys.stderr,
            )

    rendered = render(spec)
    OUT_PATH.write_text(rendered)
    print(f"Wrote {OUT_PATH} ({len(rendered):,} bytes)")

    # Mirror into the skill so the plugin — and the MCP server, which reads the
    # skill copy — stay in sync.
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
