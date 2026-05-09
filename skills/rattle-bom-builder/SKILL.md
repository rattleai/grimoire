---
name: rattle-bom-builder
description: Use this skill whenever the user is designing, building, restructuring, validating, or troubleshooting a variant Bill of Materials (BOM) in the Rattle product configurator. Activates for any "BOM", "variant BOM", "usage subclause", "usage_subclause", "option scaling", "option_scaling", "numbered option", "scaling factor", "BOM explosion", "ghost part", "phantom assembly", "alt group", "part placement", "configurable BOM", "Stücklistenkonfiguration", "Variantenstückliste", "Mengengerüst" task. Encodes the data model (Part / PartPlacement / BomItem with usage_subclauses + option_scalings + ghost_part + alt_group), the subclause DSL (groupSelections, areaStatuses, areaSubclauses with AND/OR operators), the four scaling modes (legacy numeric, ratio opt:part, range areas[min,max,part], additive vs multiplicative), the numbered-option semantics (is_numbered with number_min/number_max/number_step/number_unit), the BOM explosion engine (level, scrap_percent, alt_group + priority, ghost depth-transparent), and the validation rules. Pair with rattle-configurator (host) and rattle-suggest-config / rattle-apply-config (downstream).
license: MIT
---

# Rattle variant-BOM builder

You are the absolute expert for **configurable variant-BOM definition** on the Rattle SaaS platform. This skill picks up where `rattle-configurator` and `rattle-suggest-config` leave off: instead of high-level BOM rules, it documents every field, every DSL operator, every scaling mode, and every edge case the runtime evaluator and the BOM-explosion engine actually use.

When the user asks "how do I make 24 panels add 3 brackets each?", "how do I scale ribbon length with the configured run length?", "why is my standard part not appearing in the BOM?", "what does `option_scalings: {117: 1.25}` mean?", or "can I depend on two areas being enabled at once?" — this is the skill that gives the precise answer.

## When to use this skill

Activate when the user:

- Mentions **`usage_subclauses`**, **`option_scalings`**, **`numbered options`**, **`is_numbered`**, **`number_min/max/step/unit`**, **`scaling factor`**, **`scrap_percent`**, **`alt_group`**, **`ghost_part`**, **`phantom assembly`**, **`PartPlacement`**, **`BomItem`**.
- Asks how to **link parts to options** (the *core* mechanic of configurable BOMs).
- Asks how to **scale a part quantity** based on a numbered option's selected number, a range, or a ratio.
- Asks how to **conditionally include a BOM line** (groupSelections, areaStatuses, AND/OR composition).
- Asks how the **BOM explodes** at runtime (level depth, scrap waste, alternates, ghosts).
- Hits a "BOM appears empty" / "wrong quantity" / "ghost not resolving" / "alternate not selected" issue.
- Wants to **import / export** parts and BOM via the bulk endpoints.

If the question is about high-level configuration rules (the #1 rule, anti-patterns), stay in `rattle-configurator`. If the question is about producing a recommendation JSON, use `rattle-suggest-config` and let it call this skill for the BOM details. If the question is about applying writes idempotently, hand off to `rattle-apply-config`.

## The cardinal rule of variant BOMs

> **Every option that affects physical parts MUST have a `usage_subclause` on at least one BOM line that references it.** Conversely: every BOM line that should activate only under certain configurations MUST encode that condition in `usage_subclauses` — never in code, never as a separate part, never as an "implicit standard".

The runtime never invents inclusion logic. If no rule says "include this child when option X is selected", the part is **not** in the configured BOM. If no rule says "scale this child by factor Y", the quantity stays at the static base value.

## The two BOM-edge models

Rattle uses **two parallel edge models**, both with the same `usage_subclauses` + `option_scalings` shape:

### `PartPlacement` — Part ↔ Area edge

```
Area  ──(PartPlacement)──>  Part
              { quantity, uom, usage_subclauses, option_scalings, ghost_part, order_index }
```

A `PartPlacement` says: *"in **this area**, this part is included at quantity Q, optionally subject to subclauses on selected options and area enablement."*

This is how a part enters the **product context** at all. Without a placement on an area assigned to the product, the part is invisible.

### `BomItem` — Parent-Part ↔ Child-Part edge

```
Parent Part  ──(BomItem)──>  Child Part
              { quantity, uom, scrap_percent, usage_subclauses, option_scalings,
                alt_group, priority, order_index, effective_from, effective_to,
                ghost_part, part_group_id }
```

A `BomItem` says: *"the **parent part** is built from N × **child part**, optionally subject to subclauses, scaling, scrap, alternates, and a date window."*

This is how the BOM tree is structured. Every parent-child edge is a `BomItem`. Multi-level BOMs are pure traversal of these edges — the same fields apply at every depth.

> **Both edge types share the exact same DSL for `usage_subclauses` and `option_scalings`.** Learn it once, apply it everywhere. The reference for the DSL lives in `references/usage-subclauses.md` and the scaling reference in `references/option-scalings.md`.

## The 60-second mental model

```
   ┌──────────────────────────────────────────────────────────────────┐
   │  CONFIGURATION SELECTION at runtime:                             │
   │    chosen_option_ids   = {17, 119, 240}                          │
   │    enabled_area_ids    = {3, 4}                                  │
   │    option_amounts      = {119: 24}        ← numbered options     │
   └──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  FOR EACH BOM EDGE (placement OR bom_item):                      │
   │    1. evaluate_subclauses(edge.usage_subclauses, chosen_set,     │
   │                            area_set)   → True/False              │
   │       └── If False: skip the edge entirely.                      │
   │    2. compute amount = apply_option_scalings(                    │
   │         edge.quantity, edge.option_scalings, area_id)            │
   │       └── Multiplicative ratio, additive range, or pass-through. │
   │    3. apply scrap_percent (BomItem only) → amount × (1 + s/100)  │
   │    4. emit row at level L, multiply by parent path multiplier.   │
   └──────────────────────────────────────────────────────────────────┘
```

The runtime is **deterministic**. If the BOM is wrong, the rule is wrong — not the engine.

## The five capabilities you'll be asked about

### 1 · Conditional inclusion (`usage_subclauses`)

A list of **clauses** combined left-to-right with AND/OR (per clause `operator`). Each clause is satisfied when:

- Every group in `groupSelections` has at least one of its listed options chosen — AND
- The area conditions match (`areaStatuses` or nested `areaSubclauses`).

Empty `usage_subclauses` = **always include** (the standard / unconditional case). The legacy `isStandard: true` flag is **dropped** during normalisation — empty list does the same job.

```json
"usage_subclauses": [
  {
    "operator": "OR",
    "groupSelections": {"42": [301, 302]},
    "areaStatuses": {"3": true}
  },
  {
    "operator": "AND",
    "groupSelections": {"55": [410]}
  }
]
```

Reads as: *"include this line **when** (option 301 OR 302 is chosen in group 42 AND area 3 is enabled) **OR** (option 410 is chosen in group 55)."*

Full DSL reference + 8 worked examples: `references/usage-subclauses.md`.

### 2 · Quantity scaling (`option_scalings`)

A dict keyed by **option id (string)** mapping to a scaling **descriptor**. There are three descriptor shapes the engine recognises:

| Shape | Example | Semantic |
|---|---|---|
| **Legacy numeric** | `{"117": 1.25}` | Pass-through factor — the line's `quantity` is interpreted differently per code path (legacy: multiply qty × 1.25). |
| **Ratio (`opt`/`part`)** | `{"117": {"opt": 4, "part": 1}}` | Proportional: every 4 selected → add 1 part. Total contribution = `selected_qty × part / opt`. |
| **Range (`areas`)** | `{"117": {"areas": [{"min":1,"max":10,"part":2},{"min":11,"max":50,"part":4}]}}` | Bracketed: lookup the matching `[min, max]` → emit the absolute `part` value (no multiplication). |

The engine has **two modes** of resolution depending on caller:

- **Multiplicative** (`_resolve_scaling_factor` in `bom_explosion.py`) → returns a **multiplier** to apply to the line's base quantity.
- **Additive** (`_apply_option_scalings` / `_resolve_scaling_additive` in `models.py` snapshot path) → returns an **amount to add** to the base quantity.

Which mode is used depends on the call site:

- **Snapshot / runtime computation paths** (option-pricing engine, snapshot reconstruction) use the **additive** model: `total = base + Σ contributions`.
- **BOM explosion** with structured ranges uses **absolute** range values; with ratios uses **proportional multiplier**.

Full reference + 12 worked examples (including how the four modes interact, area-scoped `f"{opt}:{area_id}"` lookup, and clamping): `references/option-scalings.md`.

### 3 · Numbered options (`is_numbered`)

Numbered options carry a **selected quantity**, not just a presence flag.

| Field | Meaning |
|---|---|
| `is_numbered` | `true` to enable the numeric input UI. |
| `number_min` / `number_max` / `number_step` | Bounds for the input. |
| `number_unit` | Display unit (`m`, `pcs`, `mm`, `kg`, `m²`, `°`, …). |
| `price_scalings` | Same descriptor shape as `option_scalings` but for **price** instead of quantity. |

When a numbered option is selected, `option_amounts[opt_id] = selected_qty` flows through the runtime. Every BOM edge whose `option_scalings` references that option id resolves with `selected_qty` plugged in:

- **Ratio mode**: `qty_added = selected × part / opt` (e.g. opt=4 part=1, selected=24 → 6 parts).
- **Range mode**: walk `areas[]`, find `min ≤ selected ≤ max`, emit `part` absolute (e.g. selected=24 in `[11,50]` range → 4 parts).

> **Numbered-option scaling is the most-asked variant-BOM question.** A full numbered-option pattern catalogue is in `references/numbered-options.md` (with examples for length-scaled ribbon, count-scaled brackets, area-scaled trim, threshold-stepped beams).

### 4 · Alternates and priority (`alt_group` + `priority`)

When two or more `BomItem` rows under the same parent share an `alt_group`, the explosion picks **one** based on:

1. Filter: only edges whose `usage_subclauses` evaluate true.
2. Sort by `priority` (lowest first), then `order_index`.
3. Emit the first remaining edge; skip the rest in the group.

`alt_group` is a free-form string; pick a stable code (e.g. `"motor-class-A"`). Use it for *make-or-buy*, *standard-vs-premium*, or *region-specific* alternates.

### 5 · Ghost parts / phantom assemblies (`ghost_part`)

A ghost part is a "phantom assembly": it exists structurally (parents reference it via a `BomItem`) but at explode time its **own** child rows are bubbled up into its parent's level. Ghosts are **depth-transparent**: their children inherit the ghost's level instead of incrementing.

Use ghost parts to:

- Group a sub-assembly's children for editing convenience without forcing a build-level on the manufacturing BOM.
- Implement a "100% BOM" preview where the ghost shows what *would* exist if all conditions matched (`resolve_ghost_assembly` in `bom_explosion.py`).

The engine warns when ghost nesting exceeds 3 levels — keep ghosts shallow.

## Workflow — building a variant BOM from scratch

This is the canonical procedure. Walk it in order; every step has a verifiable output.

1. **Confirm the configuration is BOM-ready.**
   Every configurable feature has an explicit group with **all** variants as options, including the standard (rule `explicit-options-for-all-variants`). If not, stop and surface the gap.

2. **List the parts.** For each option that affects physical parts, identify the child part(s) and the parent (often the product's "root assembly" placeholder).
   *No part numbers? Use placeholders like `pn:standard-frame`, flag in `notes`.*

3. **Decide placement vs. multi-level.** A direct part-to-area edge → use `PartPlacement`. A parent-to-child structural edge → use `BomItem`.
   *Most configurable products use `PartPlacement` for top-level area assignments and `BomItem` only when the manufacturing BOM has real sub-assemblies.*

4. **Write `usage_subclauses` for every conditional edge.** Empty list = standard. Use `groupSelections` to require selected options. Use `areaStatuses` only when an entire **area** must be enabled (rare; most conditions are option-driven).

5. **Write `option_scalings` for every quantity that depends on a numbered option.** Pick the right descriptor:
   - Constant per-selection? Ratio `{opt: 1, part: 1}`.
   - Proportional? Ratio `{opt: N, part: M}`.
   - Bracketed by selected number? Range `{areas: [...]}`.
   - Single multiplier (legacy)? Bare numeric — but prefer `{opt, part}` for clarity.

6. **Set `scrap_percent`** (BomItem only, default 0). Negative is clamped, > 100 logs a warning.

7. **Set `alt_group` + `priority`** for any line that has true alternates. Most lines don't.

8. **Set `ghost_part: true`** only for legitimate phantom assemblies. Default `false`.

9. **Validate before applying.** Run `scripts/validate_variant_bom.py <recommendation.json>`:
   - Every `usage_subclause.groupSelections` references an option that exists.
   - Every `option_scalings` key references an option in the configuration.
   - Every `alt_group` member has a unique `priority`.
   - No edge has both `usage_subclauses=[]` AND `option_scalings={}` while sitting in an `alt_group` (would always win — ambiguous).
   - No part has a placement on an area not assigned to the product.

10. **Hand off to `rattle-config-builder`** for idempotent application (`ensure_part`, `ensure_part_placement`, `ensure_bom_item`).

## Output contract — `variant-bom.json`

```json
{
  "tenant": "acme",
  "product_id": 9001,
  "parts": [
    {
      "part_number": "AX-55",
      "part_name": "Axis assembly",
      "part_cost": 1950
    }
  ],
  "placements": [
    {
      "part_number": "AX-55",
      "area_id": 42,
      "quantity": 1.0,
      "uom": "pcs",
      "usage_subclauses": [
        {
          "operator": "OR",
          "groupSelections": {"42": [301]}
        }
      ],
      "option_scalings": {},
      "ghost_part": false,
      "order_index": 0
    }
  ],
  "bom_items": [
    {
      "parent_part_number": "AX-55",
      "child_part_number": "BR-12",
      "quantity": 1.0,
      "uom": "pcs",
      "scrap_percent": 0.0,
      "usage_subclauses": [],
      "option_scalings": {
        "119": {"opt": 4, "part": 1}
      },
      "alt_group": null,
      "priority": 0,
      "order_index": 0,
      "ghost_part": false,
      "note": "1 bracket per 4 selected panels (numbered option 119 = panels). quantity=1 baseline + scaled contribution. For range-mode lines that should ignore the base, still set quantity=1 — the API rejects quantity=0 with 422."
    }
  ],
  "validation": {"errors": [], "warnings": []},
  "notes": []
}
```

## Common corrections this skill handles

| Symptom | Diagnosis | Fix |
|---|---|---|
| BOM is empty even though options were selected | No `usage_subclause` references the selected option | Add a clause `groupSelections: {<group_id>: [<option_id>]}` on the edge |
| Standard parts vanish when an upgrade option is chosen | Either edge has no rule for the standard variant, or the alt_group locked it out | Make the standard variant an explicit option; add a clause that excludes the upgrade options (or use `alt_group` + priority to select) |
| Numbered option doesn't scale BOM | Edge has no `option_scalings` entry for that option id | Add `option_scalings: {<opt_id>: {"opt": N, "part": M}}` |
| Quantity is wrong by a factor | Confused additive vs multiplicative scaling | Range mode → absolute (no multiply by base); ratio mode → multiplied by selected_qty / opt |
| Ghost children not appearing | Ghost depth exceeds `max_phantom_depth` (3) | Flatten the ghost hierarchy |
| Alternate parts both selected | Missing `alt_group` or both have same `priority` | Set `alt_group` to a shared key, give each unique `priority` |
| "is_standard" clause kept being dropped | Legacy `isStandard: true` is dropped during normalisation | Express as empty `usage_subclauses` (the new standard) |

## What this skill does NOT do

- It does not produce strategic configuration recommendations — that's `rattle-suggest-config`.
- It does not apply writes to the API — that's `rattle-config-builder` via `rattle-apply-config`.
- It does not analyse a pricelist — that's `rattle-pricelist-analysis`.

## Related references

- `references/data-model.md` — the four edge classes and every field, lifted from `app/models.py`.
- `references/usage-subclauses.md` — full subclause DSL with 8 worked examples (groupSelections + areaStatuses + areaSubclauses + AND/OR).
- `references/option-scalings.md` — three scaling descriptors, additive vs multiplicative modes, area-scoped lookup, clamping, 12 worked examples.
- `references/numbered-options.md` — every numbered-option pattern (length-scaled, count-scaled, area-scaled, threshold-stepped).
- `references/bom-explosion.md` — how the runtime walks BOM edges, level depth, scrap, alt_group selection, ghost depth-transparency.
- `references/api-endpoints.md` — REST endpoints for parts, placements, BomItems, plus the bulk import/export contract.
- `scripts/validate_variant_bom.py` — pre-flight validator for a `variant-bom.json` payload.
- `rattle-configurator/SKILL.md` — host skill; the #1 rule.
- `rattle-suggest-config/SKILL.md` — produces the recommendation JSON this skill turns into BOM mechanics.
- `rattle-apply-config/SKILL.md` — idempotent writer that consumes the output.
- `rattle-api/references/api-reference.md` — the canonical REST reference.
