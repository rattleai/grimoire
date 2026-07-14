#!/usr/bin/env python3
"""Read-only structural auditor for a live Rattle tenant.

Implements the six checks documented in
``skills/rattle-configurator/references/structural-checks.md``:

  - areas-without-groups            (error)
  - duplicate-group-names           (warning)
  - offer-template-missing-configuration (error)
  - duplicate-dynamic-wrappers      (warning)
  - options-with-custom-keys        (info, opt-in)
  - options-with-conflicting-area-overrides (warning)

Usage:
    audit_runner.py <tenant> [--checks id1,id2,...] [--base-url <url>]
                              [--memory-root <path>]

Auth: reads ``RATTLE_API_KEY_<TENANT>`` env var (uppercased tenant). If missing,
exits 2. Reads ``memory/<tenant>/profile.md`` to detect opt-in checks.

Output: JSON to stdout matching the contract in
``skills/rattle-audit/SKILL.md``. Exit codes: 0 clean, 1 findings, 2 input/auth.

Standard library only (uses ``urllib.request``). No AI keys needed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "https://www.rattleapp.de/api/v1"
DEFAULT_MEMORY_ROOT = Path("memory")

DEFAULT_PER_PAGE = 100

ALL_CHECKS = [
    "areas-without-groups",
    "duplicate-group-names",
    "offer-template-missing-configuration",
    "duplicate-dynamic-wrappers",
    "options-with-custom-keys",
    "options-with-conflicting-area-overrides",
]

OPT_IN_CHECKS = {"options-with-custom-keys"}


# ---------------------------------------------------------------------------
# HTTP client (stdlib only)
# ---------------------------------------------------------------------------


class RattleHttpError(Exception):
    pass


def _http_get(url: str, token: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "rattle-audit-runner/0.2",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RattleHttpError(f"HTTP {exc.code} on {url}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RattleHttpError(f"network error on {url}: {exc}") from exc
    try:
        payload: dict[str, Any] = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RattleHttpError(f"non-JSON response from {url}: {body[:200]}") from exc
    return payload


def list_all(
    base_url: str,
    endpoint: str,
    token: str,
    params: dict[str, str] | None = None,
) -> Iterator[dict[str, Any]]:
    """Paginate through `endpoint` yielding entity dicts."""
    cursor: str | None = None
    while True:
        q: dict[str, Any] = {"limit": DEFAULT_PER_PAGE}
        if params:
            q.update(params)
        if cursor:
            q["cursor"] = cursor
        url = f"{base_url}/{endpoint.lstrip('/')}?{urllib.parse.urlencode(q)}"
        page = _http_get(url, token)
        data = page.get("data") or []
        for item in data:
            if isinstance(item, dict):
                yield item
        meta = page.get("meta") or {}
        if not meta.get("has_more"):
            return
        cursor = meta.get("next_cursor")
        if not cursor:
            return


def get_one(base_url: str, endpoint: str, token: str) -> dict[str, Any]:
    url = f"{base_url}/{endpoint.lstrip('/')}"
    page = _http_get(url, token)
    data = page.get("data")
    return data if isinstance(data, dict) else {}


def get_list(base_url: str, endpoint: str, token: str) -> list[dict[str, Any]]:
    url = f"{base_url}/{endpoint.lstrip('/')}"
    page = _http_get(url, token)
    data = page.get("data") or []
    return [x for x in data if isinstance(x, dict)]


# ---------------------------------------------------------------------------
# Tenant profile (opt-in detection)
# ---------------------------------------------------------------------------


def load_tenant_prefs(tenant: str, memory_root: Path) -> dict[str, str]:
    profile_path = memory_root / tenant.lower() / "profile.md"
    if not profile_path.exists():
        return {}
    text = profile_path.read_text(encoding="utf-8")
    prefs: dict[str, str] = {}
    in_prefs = False
    pat = re.compile(r"^\s*-\s+\*\*([^*]+)\*\*:\s*(.+?)\s*$")
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            in_prefs = s.lower().startswith("## preferences")
            continue
        if not in_prefs:
            continue
        m = pat.match(line)
        if m:
            prefs[m.group(1).strip()] = m.group(2).strip()
    return prefs


# ---------------------------------------------------------------------------
# Check implementations
# ---------------------------------------------------------------------------


def make_finding(
    check_id: str,
    severity: str,
    entity_type: str,
    entity_id: Any,
    entity_name: str,
    message: str,
    related_rules: Iterable[str],
    minimum_fix: str,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "severity": severity,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "message": message,
        "related_rules": list(related_rules),
        "minimum_fix": minimum_fix,
    }


def check_areas_without_groups(base_url: str, token: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for area in list_all(base_url, "areas", token):
        aid = area.get("id")
        if aid is None:
            continue
        groups = get_list(base_url, f"areas/{aid}/groups", token)
        if not groups:
            findings.append(
                make_finding(
                    "areas-without-groups",
                    "error",
                    "area",
                    aid,
                    area.get("name", "?"),
                    "Area has 0 groups",
                    ["no-empty-areas"],
                    "Add at least one group to this area, OR migrate the narrative to a document "
                    "template (see narrative-in-documents-system rule) and delete the area.",
                )
            )
    return findings


def check_duplicate_group_names(base_url: str, token: str) -> list[dict[str, Any]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for group in list_all(base_url, "groups", token):
        name = (group.get("name") or "").strip().lower()
        if not name:
            continue
        by_name.setdefault(name, []).append(group)
    findings: list[dict[str, Any]] = []
    for name, dupes in by_name.items():
        if len(dupes) <= 1:
            continue
        for g in dupes[1:]:
            findings.append(
                make_finding(
                    "duplicate-group-names",
                    "warning",
                    "group",
                    g.get("id"),
                    g.get("name", "?"),
                    f"Group name '{g.get('name')}' duplicates group id={dupes[0].get('id')}.",
                    ["reuse-over-duplicate", "shared-groups-across-products"],
                    f"Pick one canonical group (id={dupes[0].get('id')}), link it to all areas "
                    f"the duplicates were assigned to (POST /groups/{{id}}/areas), use "
                    f"option-area-config for any per-area pricing differences, then delete the "
                    f"duplicates.",
                )
            )
    return findings


def check_offer_template_missing_configuration(base_url: str, token: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for tmpl in list_all(base_url, "documents/templates", token, params={"doc_type": "offer"}):
        tid = tmpl.get("id")
        if tid is None:
            continue
        structure = get_one(base_url, f"documents/templates/{tid}/structure", token)
        # Walk attachments at any depth.
        has_dynamic_cfg = False
        stack: list[Any] = [structure]
        while stack:
            node = stack.pop()
            if not isinstance(node, dict):
                continue
            for att in node.get("attachments") or []:
                if isinstance(att, dict):
                    cb_key = (att.get("content_block_key") or "").strip()
                    dyn_key = (att.get("dynamic_key") or "").strip()
                    if (
                        cb_key == "dynamic:document_configuration"
                        or dyn_key == "dynamic:document_configuration"
                    ):
                        has_dynamic_cfg = True
                        break
            if has_dynamic_cfg:
                break
            for child in node.get("children") or []:
                stack.append(child)
            if "blocks" in node and isinstance(node["blocks"], list):
                stack.extend(node["blocks"])
        if not has_dynamic_cfg:
            findings.append(
                make_finding(
                    "offer-template-missing-configuration",
                    "error",
                    "document_template",
                    tid,
                    tmpl.get("name", "?"),
                    "Offer template has no attachment to dynamic:document_configuration",
                    ["offer-requires-configuration-block"],
                    "Add a structure block (node_type=section) and attach the system content block "
                    "whose key='dynamic:document_configuration'. Look up its id by paginating "
                    "GET /documents/content-blocks?search=dynamic:document_configuration and "
                    "matching the response's is_dynamic=true && "
                    "key='dynamic:document_configuration' entry "
                    "(the route does not honour ?is_dynamic= as a filter). Set is_required=true.",
                )
            )
    return findings


def check_duplicate_dynamic_wrappers(base_url: str, token: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    # `?include_locales=true` is required — the default ContentBlockResponse omits the
    # `locales` array (see app/schemas/v1/document_content.py), so without this
    # parameter the loop below would always observe `cb.get("locales") == []`.
    for cb in list_all(
        base_url,
        "documents/content-blocks",
        token,
        params={"include_locales": "true"},
    ):
        if cb.get("is_dynamic"):
            continue
        for locale in cb.get("locales") or []:
            if not isinstance(locale, dict):
                continue
            tn = (locale.get("template_name") or "").strip()
            if tn.startswith("dynamic:"):
                findings.append(
                    make_finding(
                        "duplicate-dynamic-wrappers",
                        "warning",
                        "document_content_block",
                        cb.get("id"),
                        cb.get("title") or cb.get("key", "?"),
                        f"Non-dynamic content block wraps system dynamic key '{tn}'",
                        ["use-system-dynamic-blocks"],
                        f"Find every attachment that points at this wrapper; rewrite the "
                        f"attachment to point at the system block id (where is_dynamic=true and "
                        f"key='{tn}'); delete this wrapper.",
                    )
                )
                break
    return findings


def check_options_with_custom_keys(base_url: str, token: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for opt in list_all(base_url, "options", token):
        key = (opt.get("key") or "").strip()
        if key:
            findings.append(
                make_finding(
                    "options-with-custom-keys",
                    "info",
                    "option",
                    opt.get("id"),
                    opt.get("name", "?"),
                    f"Option has custom key '{key}' but tenant profile sets `custom-keys: never`",
                    ["minimal-keys"],
                    "Either remove the key, or update the tenant profile to suppress this check "
                    "(remove `- **custom-keys**: never` from memory/<tenant>/profile.md).",
                )
            )
    return findings


def check_options_with_conflicting_area_overrides(
    base_url: str, token: str
) -> list[dict[str, Any]]:
    """Walk every option, then every area its group is linked to, then GET the
    area-config row (one per option×area pair). Flag overrides that drop the
    price to 0 / empty when the base price is non-zero.

    The REST endpoint is `GET /options/{oid}/area-config?area_id=<aid>` — the
    `?area_id=` query param is REQUIRED; calling without it returns 400. The
    endpoint returns one override row (or 404 if no override exists for that
    option×area pair). There is no list-all-overrides endpoint for an option,
    so we must iterate the option's group's area links.
    """
    findings: list[dict[str, Any]] = []
    # Cache groups so we don't refetch per option
    group_areas: dict[int, list[int]] = {}
    for opt in list_all(base_url, "options", token):
        oid = opt.get("id")
        gid = opt.get("group_id")
        base_price = opt.get("price")
        if oid is None or gid is None or base_price is None or base_price == 0:
            continue
        try:
            base_price_num = float(base_price)
        except (TypeError, ValueError):
            continue
        if base_price_num <= 0:
            continue
        if gid not in group_areas:
            try:
                group = get_one(base_url, f"groups/{gid}", token)
            except RattleHttpError:
                group_areas[gid] = []
                continue
            group_areas[gid] = [int(a) for a in (group.get("area_ids") or []) if a]
        for aid in group_areas[gid]:
            try:
                cfg = get_one(base_url, f"options/{oid}/area-config?area_id={aid}", token)
            except RattleHttpError:
                # 404 = no override for this (option, area) pair — skip
                continue
            if not cfg:
                continue
            cfg_price = cfg.get("price")
            if cfg_price in (None, "", 0, "0"):
                findings.append(
                    make_finding(
                        "options-with-conflicting-area-overrides",
                        "warning",
                        "option",
                        oid,
                        opt.get("name", "?"),
                        f"Option base price={base_price_num} but area_id={aid} "
                        f"override price is {cfg_price!r} — option silently drops to free in "
                        f"that area.",
                        ["price-on-option", "area-config-for-scaled-prices"],
                        f"Verify whether the zero price was intentional. If unintentional, "
                        f"PUT /options/{oid}/area-config?area_id={aid} with the correct price.",
                    )
                )
    return findings


CHECK_FUNCS = {
    "areas-without-groups": check_areas_without_groups,
    "duplicate-group-names": check_duplicate_group_names,
    "offer-template-missing-configuration": check_offer_template_missing_configuration,
    "duplicate-dynamic-wrappers": check_duplicate_dynamic_wrappers,
    "options-with-custom-keys": check_options_with_custom_keys,
    "options-with-conflicting-area-overrides": check_options_with_conflicting_area_overrides,
}


def run_audit(
    tenant: str,
    base_url: str,
    token: str,
    selected_checks: list[str],
    tenant_prefs: dict[str, str],
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    custom_keys_opt_in = tenant_prefs.get("custom-keys", "").lower() == "never"
    for check_id in selected_checks:
        if check_id in OPT_IN_CHECKS and not custom_keys_opt_in:
            continue
        fn = CHECK_FUNCS.get(check_id)
        if not fn:
            print(f"unknown check id: {check_id}", file=sys.stderr)
            continue
        try:
            findings.extend(fn(base_url, token))
        except RattleHttpError as exc:
            print(f"check {check_id} failed: {exc}", file=sys.stderr)
            findings.append(
                make_finding(
                    check_id,
                    "error",
                    "audit",
                    None,
                    "(runner)",
                    f"Check failed to execute: {exc}",
                    [],
                    "Re-run the audit; investigate the API failure if it persists.",
                )
            )

    summary = {"errors": 0, "warnings": 0, "info": 0}
    for f in findings:
        sev = f.get("severity")
        if sev == "error":
            summary["errors"] += 1
        elif sev == "warning":
            summary["warnings"] += 1
        elif sev == "info":
            summary["info"] += 1
    return {
        "tenant": tenant,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "findings": findings,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Read-only Rattle tenant auditor.")
    parser.add_argument("tenant", help="Tenant name (e.g. acme)")
    parser.add_argument(
        "--checks",
        default=",".join(ALL_CHECKS),
        help="Comma-separated check ids (default: all)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("RATTLE_BASE_URL", DEFAULT_BASE_URL),
        help=f"API base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--memory-root",
        default=str(DEFAULT_MEMORY_ROOT),
        help="Path to memory/ root (default: ./memory)",
    )
    args = parser.parse_args(argv[1:])

    token = os.environ.get(f"RATTLE_API_KEY_{args.tenant.upper()}")
    if not token:
        print(
            f"missing RATTLE_API_KEY_{args.tenant.upper()} env var. "
            f"Set it in your shell or .env before running the audit.",
            file=sys.stderr,
        )
        return 2

    selected = [c.strip() for c in args.checks.split(",") if c.strip()]
    unknown = [c for c in selected if c not in CHECK_FUNCS]
    if unknown:
        print(f"unknown check ids: {', '.join(unknown)}", file=sys.stderr)
        return 2

    tenant_prefs = load_tenant_prefs(args.tenant, Path(args.memory_root))
    result = run_audit(args.tenant, args.base_url.rstrip("/"), token, selected, tenant_prefs)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 1 if result["summary"]["errors"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
