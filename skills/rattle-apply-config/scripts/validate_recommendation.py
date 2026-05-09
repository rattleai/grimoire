#!/usr/bin/env python3
"""Deterministic validator for Rattle configuration recommendation JSON.

Checks the output of `rattle-suggest-config` against the configuration rules
documented in ``skills/rattle-configurator/references/configuration-rules.md``
WITHOUT calling any LLM or REST API. A failed validation means the
recommendation must not be applied — fix it first.

Usage:
    validate_recommendation.py <recommendation.json> [--tenant-profile <path>]

Exit codes:
    0  valid
    1  violations found (non-empty `violations` array in output)
    2  bad input (file missing, invalid JSON, wrong shape)

Output: JSON to stdout

    {
        "valid": false,
        "violations": [
            {
                "rule_id": "explicit-options-for-all-variants",
                "severity": "error",
                "message": "Group 'Wheels' has no option with recommended=true",
                "location": "products[0].groups[0]"
            }
        ]
    }

The validator is a strict implementation of the rules in
``configuration-rules.md`` — keep them in sync. When in doubt, the Markdown
reference wins; this script is a deterministic projection of it.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# Rules we enforce. Maps to ids in
# skills/rattle-configurator/references/configuration-rules.md.
RULE_IDS = {
    "EXPLICIT_OPTIONS": "explicit-options-for-all-variants",
    "REUSE_OVER_DUPLICATE": "reuse-over-duplicate",
    "MINIMAL_KEYS": "minimal-keys",
    "VALID_USAGE_SUBCLAUSE": "explicit-options-for-all-variants",  # subclauses must reference real options
    "VALID_FORBIDDEN_PAIR": "forbidden-combinations",
    "PRICE_ON_OPTION": "price-on-option",
}


def parse_tenant_profile(profile_path: Path | None) -> dict[str, str]:
    """Parse a tenant profile.md, returning a dict of preference key → value.

    Looks for lines matching ``- **<key>**: <value>`` under ``## Preferences``.
    Returns an empty dict if the path is missing or the section is absent.
    """
    if profile_path is None or not profile_path.exists():
        return {}
    text = profile_path.read_text(encoding="utf-8")
    in_prefs = False
    prefs: dict[str, str] = {}
    pattern = re.compile(r"^\s*-\s+\*\*([^*]+)\*\*:\s*(.+?)\s*$")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_prefs = stripped.lower().startswith("## preferences")
            continue
        if not in_prefs:
            continue
        m = pattern.match(line)
        if m:
            prefs[m.group(1).strip()] = m.group(2).strip()
    return prefs


def add(
    violations: list[dict[str, Any]],
    rule_id: str,
    message: str,
    location: str,
    severity: str = "error",
) -> None:
    violations.append(
        {
            "rule_id": rule_id,
            "severity": severity,
            "message": message,
            "location": location,
        }
    )


def validate(recommendation: dict[str, Any], tenant_prefs: dict[str, str]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []

    products = recommendation.get("products")
    if not isinstance(products, list) or not products:
        add(violations, "schema", "recommendation.products must be a non-empty array", "$")
        return violations

    seen_group_names: dict[str, str] = {}  # lower(name) → first location
    custom_keys_forbidden = tenant_prefs.get("custom-keys", "").lower() == "never"

    for pi, product in enumerate(products):
        if not isinstance(product, dict):
            add(violations, "schema", "product must be an object", f"products[{pi}]")
            continue
        if not product.get("name"):
            add(violations, "schema", "product.name is required", f"products[{pi}]")

        groups = product.get("groups") or []
        product_option_names: set[str] = set()  # for forbidden_pair / usage_subclause cross-check

        for gi, group in enumerate(groups):
            gloc = f"products[{pi}].groups[{gi}]"
            if not isinstance(group, dict):
                add(violations, "schema", "group must be an object", gloc)
                continue
            gname = group.get("name") or ""
            if not gname:
                add(violations, "schema", "group.name is required", gloc)
                continue

            # Reuse-over-duplicate: no two groups should share a (lowercased) name.
            key = gname.lower()
            if key in seen_group_names:
                add(
                    violations,
                    RULE_IDS["REUSE_OVER_DUPLICATE"],
                    f"Group name '{gname}' duplicated. First seen at {seen_group_names[key]}. "
                    f"Use reuse_existing=true with the existing_group_id of the first occurrence, "
                    f"or rename one of them.",
                    gloc,
                )
            else:
                seen_group_names[key] = gloc

            # Minimal-keys: never set a custom key when the tenant profile says so.
            if custom_keys_forbidden and group.get("key"):
                add(
                    violations,
                    RULE_IDS["MINIMAL_KEYS"],
                    f"Group '{gname}' has a custom key ('{group['key']}') but the tenant profile "
                    f"sets `custom-keys: never`. Strip the key.",
                    gloc,
                )

            options = group.get("options") or []
            if not options:
                add(
                    violations,
                    RULE_IDS["EXPLICIT_OPTIONS"],
                    f"Group '{gname}' has no options. Every configurable feature must have at least "
                    f"one explicit option (the standard variant).",
                    gloc,
                )
                continue

            # Explicit-options-for-all-variants: every single-select group must have
            # exactly one recommended=true option. Multi-select groups may have zero.
            recommended_count = sum(1 for o in options if isinstance(o, dict) and o.get("recommended"))
            is_multi = bool(group.get("is_multi"))
            if not is_multi and recommended_count != 1:
                add(
                    violations,
                    RULE_IDS["EXPLICIT_OPTIONS"],
                    f"Single-select group '{gname}' has {recommended_count} options with "
                    f"recommended=true; expected exactly 1 (the standard variant).",
                    gloc,
                )

            # Per-option checks.
            seen_option_names: set[str] = set()
            for oi, opt in enumerate(options):
                oloc = f"{gloc}.options[{oi}]"
                if not isinstance(opt, dict):
                    add(violations, "schema", "option must be an object", oloc)
                    continue
                oname = opt.get("name") or ""
                if not oname:
                    add(violations, "schema", "option.name is required", oloc)
                    continue
                if oname.lower() in seen_option_names:
                    add(
                        violations,
                        "schema",
                        f"Option name '{oname}' duplicated within group '{gname}'.",
                        oloc,
                    )
                seen_option_names.add(oname.lower())
                product_option_names.add(oname.lower())

                # Price-on-option: price must be numeric (allow 0); reject negative.
                price = opt.get("price")
                if price is None:
                    add(
                        violations,
                        RULE_IDS["PRICE_ON_OPTION"],
                        f"Option '{oname}' in group '{gname}' has no price field. Set price=0 for "
                        f"the standard variant; surcharges go on upgrade options.",
                        oloc,
                    )
                elif not isinstance(price, (int, float)) or price < 0:
                    add(
                        violations,
                        RULE_IDS["PRICE_ON_OPTION"],
                        f"Option '{oname}' in group '{gname}' has invalid price ({price}). "
                        f"Must be a non-negative number.",
                        oloc,
                    )

                if custom_keys_forbidden and opt.get("key"):
                    add(
                        violations,
                        RULE_IDS["MINIMAL_KEYS"],
                        f"Option '{oname}' has a custom key ('{opt['key']}') but the tenant profile "
                        f"sets `custom-keys: never`. Strip the key.",
                        oloc,
                    )

        # Validate bom_rules — every usage_subclause must reference a real option.
        bom_rules = product.get("bom_rules") or []
        for bi, bom in enumerate(bom_rules):
            bloc = f"products[{pi}].bom_rules[{bi}]"
            if not isinstance(bom, dict):
                add(violations, "schema", "bom_rule must be an object", bloc)
                continue
            for si, sub in enumerate(bom.get("usage_subclauses") or []):
                if not isinstance(sub, dict):
                    continue
                opt_name = (sub.get("option_name") or "").lower()
                if opt_name and opt_name not in product_option_names:
                    add(
                        violations,
                        RULE_IDS["VALID_USAGE_SUBCLAUSE"],
                        f"BOM rule references option '{sub.get('option_name')}' which is not "
                        f"defined in any group of product '{product.get('name', '?')}'.",
                        f"{bloc}.usage_subclauses[{si}]",
                    )

        # Validate forbidden — both options must exist on the product.
        # Accept the canonical `forbidden` field name AND the legacy `forbidden_pairs`
        # alias for backward compatibility with pre-round-3 recommendations.
        forbidden_pairs_list = product.get("forbidden") or product.get("forbidden_pairs") or []
        forbidden_field_name = "forbidden" if product.get("forbidden") is not None else "forbidden_pairs"
        for fi, pair in enumerate(forbidden_pairs_list):
            ploc = f"products[{pi}].{forbidden_field_name}[{fi}]"
            if not isinstance(pair, dict):
                add(violations, "schema", "forbidden entry must be an object", ploc)
                continue
            for key in ("option_name_1", "option_name_2"):
                name = (pair.get(key) or "").lower()
                if name and name not in product_option_names:
                    add(
                        violations,
                        RULE_IDS["VALID_FORBIDDEN_PAIR"],
                        f"forbidden entry .{key} = '{pair.get(key)}' is not a defined option on this product.",
                        ploc,
                    )

    return violations


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    args = list(argv[1:])
    profile_path: Path | None = None
    if "--tenant-profile" in args:
        i = args.index("--tenant-profile")
        if i + 1 >= len(args):
            print("--tenant-profile requires a path argument", file=sys.stderr)
            return 2
        profile_path = Path(args[i + 1])
        del args[i : i + 2]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    rec_path = Path(args[0])
    if not rec_path.exists():
        print(f"File not found: {rec_path}", file=sys.stderr)
        return 2
    try:
        recommendation = json.loads(rec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(recommendation, dict):
        print("Top-level JSON must be an object", file=sys.stderr)
        return 2

    tenant_prefs = parse_tenant_profile(profile_path)
    violations = validate(recommendation, tenant_prefs)

    output = {"valid": len(violations) == 0, "violations": violations}
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
