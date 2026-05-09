#!/usr/bin/env python3
"""Validate a variant-bom.json payload before applying it via the API.

Usage:
    python validate_variant_bom.py <variant-bom.json> [--strict]

Checks:
    - Every usage_subclause clause is well-formed (operator + at least one of
      groupSelections / areaStatuses / areaSubclauses).
    - Every groupSelections key is a stringified group id and values are int lists.
    - Every option_scalings key is a stringified option id.
    - Every option_scalings descriptor matches one of the three valid shapes
      (legacy numeric, ratio with opt+part, range with areas[]).
    - Every range descriptor has non-overlapping intervals in ascending order.
    - Every alt_group has unique priorities across its members under the same parent
      (ERR — the alt_group selection algorithm is order-sensitive within a priority bucket).
    - No edge has `quantity <= 0` (ERR — Pydantic enforces gt=0 server-side and the
      API returns 422 even when option_scalings would override at explosion time).
    - Effective date pairs are well-ordered.

Exit code 0 = valid, 1 = errors, 2 = bad input.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

OK = "ok"
WARN = "warning"
ERR = "error"


def _validate_clause(clause: dict, idx: int, prefix: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if not isinstance(clause, dict):
        out.append((ERR, f"{prefix} clause[{idx}] is not a dict"))
        return out
    op = clause.get("operator")
    if op not in (None, "AND", "OR") and idx > 0:
        out.append((ERR, f"{prefix} clause[{idx}] operator must be 'AND' or 'OR'"))
    has_payload = any(
        clause.get(k)
        for k in ("groupSelections", "areaStatuses", "areaSubclauses")
    )
    if not has_payload:
        out.append((WARN, f"{prefix} clause[{idx}] has no groupSelections/areaStatuses/areaSubclauses — will be dropped on save"))

    gs = clause.get("groupSelections")
    if gs is not None:
        if not isinstance(gs, dict):
            out.append((ERR, f"{prefix} clause[{idx}].groupSelections is not a dict"))
        else:
            for gk, opts in gs.items():
                if not isinstance(gk, str):
                    out.append((ERR, f"{prefix} clause[{idx}].groupSelections keys must be strings (got {gk!r})"))
                if not isinstance(opts, list) or not all(isinstance(o, int) for o in opts):
                    out.append((ERR, f"{prefix} clause[{idx}].groupSelections[{gk}] must be a list of int option ids"))

    ast = clause.get("areaStatuses")
    if ast is not None:
        if not isinstance(ast, dict):
            out.append((ERR, f"{prefix} clause[{idx}].areaStatuses is not a dict"))
        else:
            for ak, st in ast.items():
                if not isinstance(ak, str):
                    out.append((ERR, f"{prefix} clause[{idx}].areaStatuses keys must be strings (got {ak!r})"))
                if not isinstance(st, bool):
                    out.append((ERR, f"{prefix} clause[{idx}].areaStatuses[{ak}] must be bool (got {st!r})"))
    return out


def _validate_subclauses(subclauses, prefix: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if subclauses is None or subclauses == []:
        return out
    if not isinstance(subclauses, list):
        out.append((ERR, f"{prefix}.usage_subclauses must be a list"))
        return out
    for i, c in enumerate(subclauses):
        out.extend(_validate_clause(c, i, prefix))
    return out


def _validate_scalings(scalings, prefix: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if scalings is None or scalings == {}:
        return out
    if not isinstance(scalings, dict):
        out.append((ERR, f"{prefix}.option_scalings must be a dict"))
        return out
    for opt_key, descriptor in scalings.items():
        if not isinstance(opt_key, str):
            out.append((ERR, f"{prefix}.option_scalings key {opt_key!r} must be a string option id"))
        if isinstance(descriptor, (int, float)):
            out.append((WARN, f"{prefix}.option_scalings[{opt_key}] uses legacy numeric form {descriptor} — prefer {{opt, part}} or {{areas: [...]}}"))
            continue
        if not isinstance(descriptor, dict):
            out.append((ERR, f"{prefix}.option_scalings[{opt_key}] must be number, ratio dict, or range dict"))
            continue
        if "areas" in descriptor:
            ranges = descriptor["areas"]
            if not isinstance(ranges, list):
                out.append((ERR, f"{prefix}.option_scalings[{opt_key}].areas must be a list"))
                continue
            last_max = float("-inf")
            for j, rng in enumerate(ranges):
                if not isinstance(rng, dict):
                    out.append((ERR, f"{prefix}.option_scalings[{opt_key}].areas[{j}] is not a dict"))
                    continue
                rmin = rng.get("min", float("-inf"))
                rmax = rng.get("max", float("inf"))
                rpart = rng.get("part")
                if rpart is None:
                    out.append((ERR, f"{prefix}.option_scalings[{opt_key}].areas[{j}] missing 'part'"))
                if isinstance(rmin, (int, float)) and isinstance(rmax, (int, float)) and rmin > rmax:
                    out.append((ERR, f"{prefix}.option_scalings[{opt_key}].areas[{j}] min({rmin}) > max({rmax})"))
                if isinstance(rmin, (int, float)) and rmin < last_max:
                    out.append((WARN, f"{prefix}.option_scalings[{opt_key}].areas[{j}] overlaps prior range (last_max={last_max}, this_min={rmin})"))
                if isinstance(rmax, (int, float)):
                    last_max = rmax
        elif "opt" in descriptor or "part" in descriptor:
            opt_v = descriptor.get("opt", 1)
            part_v = descriptor.get("part", 1)
            try:
                if float(opt_v) <= 0:
                    out.append((ERR, f"{prefix}.option_scalings[{opt_key}].opt must be > 0 (got {opt_v})"))
            except (TypeError, ValueError):
                out.append((ERR, f"{prefix}.option_scalings[{opt_key}].opt must be numeric"))
            try:
                float(part_v)
            except (TypeError, ValueError):
                out.append((ERR, f"{prefix}.option_scalings[{opt_key}].part must be numeric"))
        else:
            out.append((ERR, f"{prefix}.option_scalings[{opt_key}] descriptor must contain 'opt'+'part' or 'areas'"))
    return out


def validate(payload: dict) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    if not isinstance(payload, dict):
        return [(ERR, "payload root must be a JSON object")]

    placements = payload.get("placements") or []
    bom_items = payload.get("bom_items") or []

    for i, p in enumerate(placements):
        prefix = f"placements[{i}] (part={p.get('part_number')!r}, area={p.get('area_id')})"
        if not p.get("part_number"):
            issues.append((ERR, f"{prefix} missing part_number"))
        if not p.get("area_id"):
            issues.append((ERR, f"{prefix} missing area_id"))
        q = p.get("quantity", 1.0)
        try:
            qf = float(q)
            if qf <= 0:
                issues.append((ERR, f"{prefix} quantity={qf} ≤ 0 — API enforces gt=0 (Pydantic) and will return 422; use quantity=1 even when option_scalings will override at explosion time"))
        except (TypeError, ValueError):
            issues.append((ERR, f"{prefix} quantity not numeric"))
        issues.extend(_validate_subclauses(p.get("usage_subclauses"), prefix))
        issues.extend(_validate_scalings(p.get("option_scalings"), prefix))

    alt_group_priorities: dict[tuple[str, str], list[int]] = defaultdict(list)

    for i, b in enumerate(bom_items):
        prefix = f"bom_items[{i}] (parent={b.get('parent_part_number')!r}, child={b.get('child_part_number')!r})"
        if not b.get("parent_part_number"):
            issues.append((ERR, f"{prefix} missing parent_part_number"))
        if not b.get("child_part_number"):
            issues.append((ERR, f"{prefix} missing child_part_number"))
        if b.get("parent_part_number") == b.get("child_part_number"):
            issues.append((ERR, f"{prefix} self-reference (parent==child)"))
        q = b.get("quantity", 1.0)
        try:
            qf = float(q)
            if qf <= 0:
                issues.append((ERR, f"{prefix} quantity={qf} ≤ 0 — API enforces gt=0 (Pydantic) and will return 422; use quantity=1 even when option_scalings will override at explosion time"))
        except (TypeError, ValueError):
            issues.append((ERR, f"{prefix} quantity not numeric"))
        sp = b.get("scrap_percent", 0)
        try:
            spf = float(sp)
            if not (0 <= spf <= 100):
                issues.append((WARN, f"{prefix} scrap_percent={spf} outside 0..100"))
        except (TypeError, ValueError):
            issues.append((ERR, f"{prefix} scrap_percent not numeric"))
        ef = b.get("effective_from")
        et = b.get("effective_to")
        if ef and et and ef > et:
            issues.append((ERR, f"{prefix} effective_from > effective_to"))
        ag = b.get("alt_group")
        if ag:
            key = (b.get("parent_part_number") or "", ag)
            alt_group_priorities[key].append(b.get("priority", 0))
        issues.extend(_validate_subclauses(b.get("usage_subclauses"), prefix))
        issues.extend(_validate_scalings(b.get("option_scalings"), prefix))

    for (parent, ag), priorities in alt_group_priorities.items():
        if len(priorities) != len(set(priorities)):
            issues.append((ERR, f"alt_group ({parent}, {ag!r}) has duplicate priorities {priorities} — alt_group selection requires unique priority per member (per the cardinal rule in SKILL.md); fix before applying"))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Path to variant-bom.json")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    p = Path(args.path)
    if not p.is_file():
        print(f"error: {p} is not a file", file=sys.stderr)
        return 2
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        return 2

    issues = validate(payload)
    errors = [i for i in issues if i[0] == ERR]
    warnings = [i for i in issues if i[0] == WARN]

    for level, msg in issues:
        prefix = "ERROR" if level == ERR else "WARN"
        print(f"[{prefix}] {msg}")

    print(
        f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s) "
        f"in {len(payload.get('placements') or [])} placement(s) and "
        f"{len(payload.get('bom_items') or [])} bom_item(s)"
    )

    if errors:
        return 1
    if warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
