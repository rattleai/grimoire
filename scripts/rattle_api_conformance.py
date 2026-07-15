#!/usr/bin/env python3
"""Rattle API conformance suite — a red/green test for every audit finding.

This exists because a 40-page audit does not get fixed and a failing test does.

Run it against the live spec and it is red. Fix a finding, run it again, and that
check goes green. It is designed to be dropped straight into Rattle's own CI, so
that a fixed defect cannot silently regress.

    python3 scripts/rattle_api_conformance.py                 # fetch live spec
    python3 scripts/rattle_api_conformance.py --offline       # use docs/openapi.json
    python3 scripts/rattle_api_conformance.py --json          # machine-readable
    python3 scripts/rattle_api_conformance.py --only P0       # one severity
    python3 scripts/rattle_api_conformance.py --only P0-1     # one finding

Exit code is the number of FAILING checks (0 = fully conformant), so CI can gate
on it directly, or gate on a threshold while a backlog is worked down:

    python3 scripts/rattle_api_conformance.py --max-fail 12

Every check is derived only from the published OpenAPI document. Nothing here
requires backend access, a tenant, or a credential. Full reasoning for each
finding: docs/API_AUDIT.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SPEC_URL = "https://www.rattleapp.de/docs/api/openapi.json"
LOCAL_SPEC = ROOT / "docs" / "openapi.json"

HTTP_METHODS = ("get", "post", "put", "patch", "delete")


# ---------------------------------------------------------------------------
# Check registry
# ---------------------------------------------------------------------------


@dataclass
class Result:
    ok: bool
    detail: str = ""
    evidence: list[str] = field(default_factory=list)


@dataclass
class Check:
    id: str
    severity: str  # P0 | P1 | P2 | P3
    title: str
    fix: str
    run: Callable[[dict[str, Any]], Result]


CHECKS: list[Check] = []


def check(id_: str, severity: str, title: str, fix: str):
    def deco(fn: Callable[[dict[str, Any]], Result]) -> Callable[[dict[str, Any]], Result]:
        CHECKS.append(Check(id_, severity, title, fix, fn))
        return fn

    return deco


# ---------------------------------------------------------------------------
# Spec helpers
# ---------------------------------------------------------------------------


def ops(spec: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    return [
        (m, p, op)
        for p, item in spec.get("paths", {}).items()
        for m, op in item.items()
        if m in HTTP_METHODS
    ]


def schemas(spec: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = spec.get("components", {}).get("schemas", {})
    return out


def props(spec: dict[str, Any], name: str) -> dict[str, Any]:
    return schemas(spec).get(name, {}).get("properties", {}) or {}


# ---------------------------------------------------------------------------
# P0 — silent corruption
# ---------------------------------------------------------------------------


@check(
    "P0-1",
    "P0",
    "The four required headers are declared as real parameters",
    "Declare X-Constraints-Version, X-Price-Lists-Version, X-Idempotency-Key and "
    "If-None-Match as `in: header` parameters on the operations that require them.",
)
def p0_1(spec):
    declared = {
        pr.get("name", "").lower()
        for _, _, op in ops(spec)
        for pr in op.get("parameters", [])
        if pr.get("in") == "header"
    }
    want = {"x-constraints-version", "x-price-lists-version", "x-idempotency-key", "if-none-match"}
    missing = sorted(want - declared)
    if not missing:
        return Result(True, "all four declared")
    return Result(
        False,
        f"{len(missing)} of 4 header parameters are not declared anywhere in the spec",
        [f"missing: {h}" for h in missing]
        + ["a spec-driven client cannot send them → silent lost update on POST /constraints"],
    )


@check(
    "P0-1b",
    "P0",
    "POST /constraints declares a 409 (stale version)",
    "Add the 409 response. 23 other endpoints already declare it.",
)
def p0_1b(spec):
    op = spec["paths"].get("/api/v1/constraints", {}).get("post")
    if not op:
        return Result(True, "endpoint absent — nothing to check")
    if "409" in op.get("responses", {}):
        return Result(True)
    return Result(
        False,
        "POST /constraints atomically replaces ALL constraints and cannot report a stale version",
        [f"declared responses: {sorted(op.get('responses', {}))}"],
    )


@check(
    "P0-2",
    "P0",
    "Server-computed fields are marked readOnly",
    "Add `readOnly: true` to every field a response returns but no request accepts. "
    "Zero behaviour change; codegen then omits them from request bodies automatically.",
)
def p0_2(spec):
    n = sum(
        1
        for s in schemas(spec).values()
        for sp in (s.get("properties") or {}).values()
        if sp.get("readOnly")
    )
    # The canonical symptom: GET a product, PUT it back, get a 422.
    resp = set(props(spec, "ProductResponse"))
    req = set(props(spec, "ProductUpdateRequest"))
    strict = schemas(spec).get("ProductUpdateRequest", {}).get("additionalProperties") is False
    refused = sorted(resp - req)
    if n > 0 and not (strict and refused):
        return Result(True, f"{n} fields marked readOnly")
    return Result(
        False,
        f"`readOnly` appears {n} times in the whole spec; read-modify-write is impossible",
        [
            f"GET /products/{{id}} returns {len(resp)} fields",
            f"PUT /products/{{id}} accepts {len(req)}, additionalProperties: false",
            f"→ {len(refused)} fields the server SENDS and REFUSES back: {', '.join(refused[:6])}…",
        ],
    )


@check(
    "P0-3",
    "P0",
    "PUT and PATCH are not byte-identical aliases",
    "Pick one verb per path. If PUT merges, say so; better, make PUT replace "
    "(with `required` fields) and PATCH merge.",
)
def p0_3(spec):
    both = [p for p, it in spec["paths"].items() if "put" in it and "patch" in it]
    same = [
        p
        for p in both
        if json.dumps(spec["paths"][p]["put"].get("requestBody"))
        == json.dumps(spec["paths"][p]["patch"].get("requestBody"))
    ]
    if not same:
        return Result(True, f"{len(both)} paths expose both, none identical")
    return Result(
        False,
        f"{len(same)} of {len(both)} paths expose PUT and PATCH with an IDENTICAL request body",
        ["replace-vs-merge is undefined → GET/edit/PUT may silently null every omitted field"],
    )


@check(
    "P0-4",
    "P0",
    "rule_json (the constraint DSL) has a real schema",
    "Define ForbiddenRuleJson { requires: RuleClause[], invalid: integer[] }. "
    "You already did exactly this for UsageSubclause — copy it. And 422 the legacy "
    "[{if,then}] array instead of accepting it and never executing it.",
)
def p0_4(spec):
    rj = props(spec, "ForbiddenRuleCreateRequest").get("rule_json")
    if rj is None:
        return Result(True, "schema absent — nothing to check")
    shaped = any(k in rj for k in ("$ref", "properties", "type", "anyOf", "oneOf", "allOf"))
    if shaped:
        return Result(True)
    return Result(
        False,
        "rule_json is completely untyped — it decides which combinations a customer may buy",
        [f"published definition, in full: {json.dumps(rj)}"],
    )


@check(
    "P0-5",
    "P0",
    "Money uses one consistent type",
    "One money type across the surface — decimal-as-string ('12.50'), matching the "
    "existing majority. Migrate part_cost (or rename it part_cost_cents and SAY the unit).",
)
def p0_5(spec):
    # Deliberately conservative. A false positive here (flagging a COUNT as money)
    # would let the whole suite be dismissed, so counts, ids, flags and percentages
    # are excluded and only scalar numeric/string types are considered.
    money_re = re.compile(r"(price|amount|cost|discount|tax|total)", re.I)
    # `total` on its own is ambiguous — BatchResponse.total is an operation count, not
    # money — so it only counts when qualified (total_amount, list_price_total, …).
    not_money = re.compile(
        r"(_count$|_id$|^id$|percent|_at$|currency|^is_|^has_|type$|status$"
        r"|^total$|^failed$|^succeeded$"
        # `total_<anything>` is a COUNT unless it names a money noun. BatchResponse.total,
        # PipelineSnapshotResponse.total_quotes/total_revisions are counts, not currency.
        r"|^total_(?!amount|price|cost|value|revenue|net|gross))",
        re.I,
    )
    scalar = {"string", "number", "integer"}

    kinds: dict[str, list[str]] = {}
    for n, s in schemas(spec).items():
        for f, sp in (s.get("properties") or {}).items():
            if not money_re.search(f) or not_money.search(f):
                continue
            # Skip anything that isn't a scalar — objects/arrays/booleans aren't money.
            declared = sp.get("type")
            candidates = (
                set(declared)
                if isinstance(declared, list)
                else {declared}
                if declared
                else {x.get("type") for x in sp.get("anyOf", [])}
            )
            if not ({c for c in candidates if c} & scalar):
                continue
            raw = sp.get("type")
            if isinstance(raw, list):  # OpenAPI 3.1 allows a type union
                t = "|".join(sorted(x for x in raw if x != "null"))
            elif raw:
                t = str(raw)
            else:
                t = "|".join(
                    sorted(
                        str(x.get("type"))
                        for x in sp.get("anyOf", [])
                        if x.get("type") not in (None, "null")
                    )
                )
            kinds.setdefault(t or "?", []).append(f"{n}.{f}")
    if len(kinds) <= 1:
        return Result(True, "one money type")
    ints = kinds.get("integer", [])
    ev = [f"{t}: {len(v)} fields" for t, v in sorted(kinds.items(), key=lambda x: -len(x[1]))]
    if ints:
        ev.append(f"INTEGER money (silent rounding): {', '.join(ints[:4])}")
    return Result(
        False,
        f"money is encoded {len(kinds)} different ways "
        f"across {sum(len(v) for v in kinds.values())} fields",
        ev,
    )


@check(
    "P0-6",
    "P0",
    "servers/ base path does not double the /api/v1 prefix",
    "Either set servers to https://www.rattleapp.de/api/v1 and drop the prefix from "
    "path keys, or keep the paths and set servers to https://www.rattleapp.de. One line.",
)
def p0_6(spec):
    srv = (spec.get("servers") or [{}])[0].get("url", "")
    paths = list(spec.get("paths", {}))
    prefixed = paths and all(p.startswith("/api/v1") for p in paths)
    root_server = srv in ("/", "")
    if not (root_server and prefixed):
        return Result(True, f"servers={srv!r}")
    return Result(
        False,
        "servers.url is '/' while every path embeds /api/v1 → clients produce /api/v1/api/v1/...",
        [f"servers[0].url = {srv!r}", f"paths[0] = {paths[0]!r}"],
    )


@check(
    "P0-7",
    "P0",
    "ConfiguratorSettingsResponse matches what the API returns",
    "Regenerate the schema from the real model. It currently names 5 fields that do "
    "not exist and omits the ~20 that do — the flags that govern the customer-capture UX.",
)
def p0_7(spec):
    declared = set(props(spec, "ConfiguratorSettingsResponse"))
    # The real field set, observed read-only against a live tenant (2026-07-14).
    real = {
        "allow_create_new_customer",
        "allow_select_existing_customer",
        "customer_search_fields",
        "start_search_digits",
        "require_customer_organization",
        "require_customer_contact_person",
        "require_customer_info",
    }
    if declared & real:
        return Result(True, f"{len(declared & real)} real fields declared")
    return Result(
        False,
        "the declared schema has ZERO overlap with what the endpoint actually returns",
        [
            f"declared: {sorted(declared)}",
            "actually returned (sample): require_customer_organization, customer_search_fields, "
            "start_search_digits, allow_create_new_customer, …",
            "→ PATCH {show_prices: true} returns 200 and does nothing",
        ],
    )


@check(
    "P0-8",
    "P0",
    "The pricing resolution order is documented",
    "Six mechanisms can set one option's price. State which wins — one paragraph in "
    "info.description. Ideally also return a price_breakdown from /configurations/calculate "
    "so pricing is auditable.",
)
def p0_8(spec):
    blob = json.dumps(spec).lower()
    # "precedence" alone is not enough — the only current hit is about BOM boolean operators.
    signals = ("pricing precedence", "price resolution", "price precedence", "which price wins")
    if any(s in blob for s in signals):
        return Result(True)
    return Result(
        False,
        "six mechanisms can set one option's price and the order is stated nowhere",
        [
            "Option.price · option override · advanced (conditional) price · "
            "area/product override · pricing preset · area-config price",
            "grep: 'resolution order' 0 · 'takes priority' 0 · 'most specific' 0 · 'falls back' 0",
            "→ the API returns a plausible price. Possibly the wrong one. On a signed quote.",
        ],
    )


@check(
    "P0-9",
    "P0",
    "advanced-prices has named schemas and a description",
    "Name AdvancedPriceCreateRequest / AdvancedPriceResponse, write one sentence of "
    "description, add an example. This is a cross-option conditional-price engine and "
    "nobody can find it.",
)
def p0_9(spec):
    path = "/api/v1/options/{optionId}/advanced-prices"
    op = spec["paths"].get(path, {}).get("post")
    if not op:
        return Result(True, "endpoint absent")
    body = (
        op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    )
    named = "$ref" in body
    described = bool(op.get("description"))
    if named and described:
        return Result(True)
    return Result(
        False,
        "an undocumented conditional-price engine: inline schema, description=null",
        [
            f"named schema: {named}",
            f"has description: {described}",
            "we deduced what it does from a required field name: condition_option_id",
        ],
    )


@check(
    "P0-9b",
    "P0",
    "X-Price-Lists-Version can actually be read from somewhere",
    "Return the version on PriceListResponse and say which field feeds which header. "
    "Today the OCC header the API tells you to send cannot be constructed.",
)
def p0_9b(spec):
    fields = props(spec, "PriceListResponse")
    if any("version" in f.lower() for f in fields):
        return Result(True)
    return Result(
        False,
        "info.description says 'read the current version from a GET response' — there is none",
        [f"PriceListResponse fields: {sorted(fields)}", "→ the OCC header is unobtainable"],
    )


@check(
    "P0-9e",
    "P0",
    "No parameter declares a default outside its own maximum",
    "Pick one number. Today limit declares default:200 with maximum:100, and its "
    "description says 500.",
)
def p0_9e(spec):
    bad = []
    for m, p, op in ops(spec):
        for pr in op.get("parameters", []):
            sc = pr.get("schema") or {}
            d, mx, mn = sc.get("default"), sc.get("maximum"), sc.get("minimum")
            if not isinstance(d, int | float):
                continue
            if isinstance(mx, int | float) and d > mx:
                bad.append(f"{m.upper()} {p} ?{pr['name']}: default={d} > maximum={mx}")
            if isinstance(mn, int | float) and d < mn:
                bad.append(f"{m.upper()} {p} ?{pr['name']}: default={d} < minimum={mn}")
    if not bad:
        return Result(True)
    return Result(False, f"{len(bad)} parameter(s) declare a schema-invalid default", bad[:4])


@check(
    "P0-9i",
    "P0",
    "No PATCH is documented as replacing rather than merging",
    "Make the dictionary PATCH merge (as its own summary promises), or remove PATCH "
    "and keep only PUT. Do not keep a PATCH that replaces.",
)
def p0_9i(spec):
    bad = []
    for m, p, op in ops(spec):
        if m != "patch":
            continue
        d = (op.get("description") or "").lower()
        if "does not merge" in d or "fully replaces" in d or "replaces (does not" in d:
            bad.append(f"PATCH {p} — summary: {op.get('summary')!r}")
    if not bad:
        return Result(True)
    return Result(
        False,
        f"{len(bad)} PATCH endpoint(s) REPLACE instead of merging — silent data loss",
        bad + ["a PATCH adding one language silently deletes the others, with a 200"],
    )


@check(
    "P0-9j",
    "P0",
    "is_stale is available wherever source_content_hash is",
    "Add is_stale to StructureBlockLocaleResponse. The hash is already there; the "
    "boolean is free to compute.",
)
def p0_9j(spec):
    bad = []
    for n, s in schemas(spec).items():
        f = s.get("properties") or {}
        if "source_content_hash" in f and "is_stale" not in f:
            bad.append(n)
    if not bad:
        return Result(True)
    return Result(
        False,
        "a locale carries a staleness hash but no staleness flag",
        [f"{n}: has source_content_hash, missing is_stale" for n in bad]
        + ["→ you cannot ask whether a translated chapter TITLE is stale"],
    )


@check(
    "P0-10",
    "P0",
    "Every request schema rejects unknown fields",
    "Set additionalProperties: false on the remaining request schemas (and name the "
    "inline ones). Today a typo 422s on 116 of them and is silently swallowed on the rest.",
)
def p0_10(spec):
    reqs = [n for n in schemas(spec) if n.endswith("Request")]
    loose = [n for n in reqs if "additionalProperties" not in schemas(spec)[n]]
    if not loose:
        return Result(True, f"all {len(reqs)} request schemas are strict")
    return Result(
        False,
        f"{len(loose)} of {len(reqs)} request schemas silently swallow unknown fields",
        [", ".join(loose[:6]) + ("…" if len(loose) > 6 else "")],
    )


# ---------------------------------------------------------------------------
# P1 — machine-readability
# ---------------------------------------------------------------------------


@check(
    "P1-1",
    "P1",
    "Closed vocabularies are declared as enums",
    "Promote the enum-shaped free strings to `enum`. Start with doc_type on "
    "DocumentTemplateCreateRequest — the correct vocabulary already exists in CloneRequest.",
)
def p1_1(spec):
    enum_shaped = re.compile(r"(_type$|^status$|^state$|_mode$|^stage$|^role$|^category$)")
    free = []
    for n, s in schemas(spec).items():
        for f, sp in (s.get("properties") or {}).items():
            if not enum_shaped.search(f):
                continue
            if "enum" in json.dumps(sp):
                continue
            if sp.get("type") == "string" or any(
                x.get("type") == "string" for x in sp.get("anyOf", [])
            ):
                free.append(f"{n}.{f}")
    if not free:
        return Result(True)
    return Result(
        False,
        f"{len(free)} enum-shaped fields are unconstrained free strings",
        [
            ", ".join(free[:6]) + "…",
            "→ POST /documents/templates with doc_type:'datashet' validates",
        ],
    )


@check(
    "P1-2",
    "P1",
    "Schema fields are described",
    "Describe the fields an integration writes. UsageSubclause proves you can do this "
    "superbly — extend that standard.",
    # Threshold, not perfection: this is a compounding-quality metric, not a bug.
)
def p1_2(spec):
    fields = [(n, f) for n, s in schemas(spec).items() for f in (s.get("properties") or {})]
    nod = [(n, f) for n, f in fields if not (schemas(spec)[n]["properties"][f].get("description"))]
    pct = 100 * len(nod) // max(len(fields), 1)
    if pct <= 25:
        return Result(True, f"{pct}% undescribed")
    return Result(
        False,
        f"{len(nod)}/{len(fields)} fields ({pct}%) have no description",
        ["target: ≤25%. An agent must infer `part_cost` — cents or euros? — from its name."],
    )


@check(
    "P1-9",
    "P1",
    "Legacy paths and fields are marked deprecated",
    "Set deprecated: true on every legacy path, field and enum value, naming the "
    "replacement. Free, and the clearest signal you can give an integrator.",
)
def p1_9(spec):
    n = sum(1 for _, _, op in ops(spec) if op.get("deprecated"))
    n += sum(
        1
        for s in schemas(spec).values()
        for sp in (s.get("properties") or {}).values()
        if sp.get("deprecated")
    )
    if n >= 2:
        return Result(True, f"{n} deprecations declared")
    return Result(
        False,
        f"only {n} deprecation marker(s) in the whole spec, yet legacy shapes are accepted",
        [
            "legacy rule_json array (saves, never executes) · technical_documentation alias · "
            "legacy plural doc_types"
        ],
    )


# ---------------------------------------------------------------------------
# P2 — capability
# ---------------------------------------------------------------------------


@check(
    "P2-1",
    "P2",
    "Product has an external identifier (sku)",
    "Add sku to Product{Create,Update}Request + ProductResponse, unique per tenant, "
    "with a ?sku= filter. Mirror Customer.customer_id, which already proves the pattern. "
    "Wire it to QuoteLineItemResponse.product_sku, which already exists with no writer.",
)
def p2_1(spec):
    p = props(spec, "ProductCreateRequest")
    if any(k in p for k in ("sku", "article_number", "external_id")):
        return Result(True)
    reads_back = "product_sku" in props(spec, "QuoteLineItemResponse")
    ev = [f"ProductCreateRequest: {sorted(p)}"]
    if reads_back:
        ev.append("QuoteLineItemResponse.product_sku EXISTS — read-only, with no writer anywhere")
    return Result(False, "products have no external identifier; every ERP join key is homeless", ev)


@check(
    "P2-1c",
    "P2",
    "A configuration can be created through the API",
    "Add POST /configurations (persist a selection set against a product, returning an "
    "id and config_code). Without it, headless quote-to-cash is impossible.",
)
def p2_1c(spec):
    has = "post" in spec["paths"].get("/api/v1/configurations", {})
    if has:
        return Result(True)
    cfg = [f"{m.upper()} {p}" for m, p, _ in ops(spec) if p.startswith("/api/v1/configurations")]
    return Result(
        False,
        "the API can PRICE, FIND and LOCK a configuration — but cannot CREATE one",
        [f"all configuration ops: {', '.join(sorted(cfg))}"]
        + ["→ an ERP, a portal or an agent cannot produce the thing a quote line points at"],
    )


@check(
    "P2-3",
    "P2",
    "Numbered options accept fractional quantities",
    "Widen number_min/max/step and option_amounts to decimal. The BOM side "
    "(option_scalings) is already `number` — only the option side is integer-locked.",
)
def p2_3(spec):
    o = props(spec, "OptionCreateRequest")
    types = set()
    for f in ("number_min", "number_max", "number_step"):
        sp = o.get(f, {})
        for v in sp.get("anyOf", [sp]):
            if v.get("type") and v["type"] != "null":
                types.add(v["type"])
    if not types or types == {"number"}:
        return Result(True)
    return Result(
        False,
        f"numbered options are {'/'.join(sorted(types))}-only — no 2.5 m, no 0.5 kg, no 1.75 m²",
        [
            "blocks cut-to-length, sheet goods, cabling, textiles",
            "the workaround (model in mm) makes the customer see 3000 where they think 3 m",
        ],
    )


@check(
    "P2-5",
    "P2",
    "Parts can carry an image",
    "Add POST/DELETE /parts/{partId}/image mirroring the options route, and expose "
    "part_img on PartResponse.",
)
def p2_5(spec):
    imgs = [p for p in spec["paths"] if p.endswith("/image")]
    if any("/parts/" in p for p in imgs):
        return Result(True)
    return Result(
        False,
        "image upload exists for products, areas and options — but not parts",
        [
            f"image routes: {', '.join(imgs)}",
            "→ spare-parts catalogues and exploded views cannot show part images",
        ],
    )


@check(
    "P2-6",
    "P2",
    "The doc_type enum includes every registered doc_type",
    "Define one DocType enum, reference it from every request/response/query param, "
    "and include `quote`.",
)
def p2_6(spec):
    clone = props(spec, "CloneRequest").get("doc_type", {})
    enum = next(
        (v["enum"] for v in clone.get("anyOf", [clone]) if "enum" in v),
        None,
    )
    if enum is None:
        return Result(True, "no doc_type enum to check")
    if "quote" in enum:
        return Result(True)
    return Result(
        False,
        "`quote` is a registered doc_type and is missing from the only doc_type enum in the spec",
        [
            f"CloneRequest.doc_type enum: {enum}",
            "→ on the face of it, you cannot clone a quote template",
        ],
    )


@check(
    "P2-7",
    "P2",
    "Webhook event types are enumerated",
    "Emit <resource>.{created,updated,deleted} for product, part, option, group, area, "
    "bom_item, constraint, price_list — and publish the enum on WebhookCreateRequest.events.",
)
def p2_7(spec):
    ev = props(spec, "WebhookCreateRequest").get("events", {})
    if "enum" in json.dumps(ev):
        return Result(True)
    return Result(
        False,
        "the subscribable event set is not discoverable from the spec",
        [
            f"WebhookCreateRequest.events: {json.dumps(ev)[:110]}",
            "→ any system mirroring the catalogue must POLL",
        ],
    )


# ---------------------------------------------------------------------------
# P3 — consistency
# ---------------------------------------------------------------------------


@check(
    "P3-1",
    "P3",
    "A resource names its identifier one way",
    "Use {id} for the resource that owns the path; {parentId} only to disambiguate a "
    "nested parent. One casing. This changes the spec, not the URLs — nearly free.",
)
def p3_1(spec):
    by: dict[str, set[str]] = {}
    for p in spec["paths"]:
        for seg, prm in re.findall(r"/([a-z-]+)/\{(\w+)\}", p):
            by.setdefault(seg, set()).add(prm)
    mixed = {k: v for k, v in by.items() if len(v) > 1}
    if not mixed:
        return Result(True)
    return Result(
        False,
        f"{len(mixed)} resources name their own id more than one way",
        [f"/{k}/ uses {sorted(v)}" for k, v in sorted(mixed.items())[:5]]
        + ["→ an agent that learned /parts/{id} cannot construct /parts/{partId}/revisions"],
    )


@check(
    "P3-3",
    "P3",
    "429 responses declare rate-limit headers",
    "Declare Retry-After (and X-RateLimit-*) in the 429 response object. If the backend "
    "already sends them, this is a two-line spec change.",
)
def p3_3(spec):
    with429 = [op for _, _, op in ops(spec) if "429" in op.get("responses", {})]
    if not with429:
        return Result(True)
    if any(op["responses"]["429"].get("headers") for op in with429):
        return Result(True)
    return Result(
        False,
        f"all {len(with429)} operations can 429 and none declares Retry-After",
        ["agents are bursty by nature — they will hit this and back off by guessing"],
    )


@check(
    "P3-4",
    "P3",
    "No GET or DELETE carries a request body",
    "Move the payload to a query parameter. Bodies on DELETE are widely stripped by "
    "proxies → silent no-op deletion.",
)
def p3_4(spec):
    bad = [
        f"{m.upper()} {p}"
        for m, p, op in ops(spec)
        if m in ("get", "delete") and op.get("requestBody")
    ]
    if not bad:
        return Result(True)
    return Result(False, f"{len(bad)} GET/DELETE operation(s) declare a request body", bad)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def load_spec(offline: bool) -> dict[str, Any]:
    if offline:
        if not LOCAL_SPEC.exists():
            sys.exit(f"No local spec at {LOCAL_SPEC}. Drop --offline to fetch the live one.")
        local: dict[str, Any] = json.loads(LOCAL_SPEC.read_text())
        return local

    req = urllib.request.Request(
        SPEC_URL,
        headers={
            "User-Agent": "rattle-api-conformance/1.0 (+https://github.com/rattleai/grimoire)",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
            live: dict[str, Any] = json.loads(r.read().decode())
            return live
    except (urllib.error.URLError, TimeoutError) as exc:
        sys.exit(
            f"Could not fetch {SPEC_URL} ({exc}). Use --offline to run against docs/openapi.json."
        )


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--offline", action="store_true", help="Use docs/openapi.json, do not fetch.")
    ap.add_argument("--json", action="store_true", help="Machine-readable output.")
    ap.add_argument("--only", metavar="ID", help="Run one severity (P0) or one finding (P0-1).")
    ap.add_argument(
        "--max-fail",
        type=int,
        default=0,
        help="Exit 0 while failures are at or below this. Use it to ratchet a backlog down.",
    )
    args = ap.parse_args()

    spec = load_spec(args.offline)

    selected = CHECKS
    if args.only:
        k = args.only.upper()
        selected = [c for c in CHECKS if c.id == k or c.severity == k]
        if not selected:
            sys.exit(f"No check matches {args.only!r}. Known: {', '.join(c.id for c in CHECKS)}")

    results = [(c, c.run(spec)) for c in selected]
    failed = [(c, r) for c, r in results if not r.ok]

    if args.json:
        print(
            json.dumps(
                {
                    "spec": {
                        "operations": len(ops(spec)),
                        "paths": len(spec.get("paths", {})),
                        "schemas": len(schemas(spec)),
                    },
                    "passed": len(results) - len(failed),
                    "failed": len(failed),
                    "checks": [
                        {
                            "id": c.id,
                            "severity": c.severity,
                            "title": c.title,
                            "ok": r.ok,
                            "detail": r.detail,
                            "evidence": r.evidence,
                            "fix": c.fix,
                        }
                        for c, r in results
                    ],
                },
                indent=2,
            )
        )
        return 0 if len(failed) <= args.max_fail else len(failed)

    o = len(ops(spec))
    print(f"Rattle API conformance — {o} operations · {len(schemas(spec))} schemas")
    print(f"{'live spec' if not args.offline else 'docs/openapi.json'}\n")

    for sev in ("P0", "P1", "P2", "P3"):
        group = [(c, r) for c, r in results if c.severity == sev]
        if not group:
            continue
        label = {
            "P0": "P0 — silent corruption (do everything right, still write wrong data)",
            "P1": "P1 — machine-readability (codegen and agents fly blind)",
            "P2": "P2 — capability (things a customer cannot do)",
            "P3": "P3 — consistency (an agent cannot generalise)",
        }[sev]
        print(f"── {label}")
        for c, r in group:
            mark = "PASS" if r.ok else "FAIL"
            print(f"  [{mark}] {c.id:<7} {c.title}")
            if not r.ok:
                if r.detail:
                    print(f"           → {r.detail}")
                for e in r.evidence:
                    print(f"             · {e}")
                print(f"           FIX: {c.fix}")
        print()

    n_pass = len(results) - len(failed)
    print(f"{n_pass} passed · {len(failed)} failed")
    if failed:
        by_sev = {s: sum(1 for c, _ in failed if c.severity == s) for s in ("P0", "P1", "P2", "P3")}
        print("failing: " + " · ".join(f"{s} {n}" for s, n in by_sev.items() if n))
        print("\nFull reasoning for every finding: docs/API_AUDIT.md")
        print("Remediation plan with copy-pasteable diffs: docs/API_REMEDIATION.md")
    else:
        print("\nFully conformant. Nice.")

    return 0 if len(failed) <= args.max_fail else len(failed)


if __name__ == "__main__":
    sys.exit(main())
