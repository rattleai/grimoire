# `option_scalings` — quantity scaling reference

`option_scalings` is the field that scales a BOM line's `quantity` based on the selected **amount** of a numbered option. It is a dict keyed by stringified option id, mapping to one of three descriptor shapes.

> **Scope.** `option_scalings` only matters for options where the user picks a **number**. For boolean (selected / not selected) options, use `usage_subclauses` instead — option_scalings on a non-numbered option is a no-op since `option_amounts` carries no quantity.

## Field overview

| Edge | Field | Default |
|---|---|---|
| `PartPlacement` | `option_scalings` | `{}` |
| `BomItem` | `option_scalings` | `{}` |
| `BomLineRev` | `option_scalings` | `{}` |

The schema lives in `app/schemas/v1/part.py` (validators on placement and bom-item create / update) and the runtime evaluator in `app/utils/bom_explosion.py` (`_resolve_scaling_factor`, `_resolve_scaling_additive`) and `app/models.py` (`_apply_option_scalings`).

## The three descriptor shapes

### 1 · Legacy numeric

```json
"option_scalings": {"117": 1.25}
```

Pass-through factor. The semantic depends on the call site:

- **BOM explosion path** (`_resolve_scaling_factor`): treated as a multiplier — base quantity × 1.25.
- **Snapshot / additive path** (`_resolve_scaling_additive`): treated as a per-unit add — `qty_added = factor × selected_qty`.

> **Avoid this shape for new authoring.** It works, but the meaning is ambiguous across paths. Use the structured ratio or range descriptors below.

### 2 · Ratio — `{opt, part}`

```json
"option_scalings": {"117": {"opt": 4, "part": 1}}
```

Reads as: *"every 4 selected → emit 1 part."*

Resolution:

| Mode | Formula |
|---|---|
| **Multiplier** (`_resolve_scaling_factor`) | returned multiplier = `selected_qty × part / opt` |
| **Additive** (`_resolve_scaling_additive`, `_apply_option_scalings`) | added quantity = `selected_qty × part / opt` |

Both modes give the same numerical result for ratio descriptors — they just apply it differently to the base quantity (`base × factor` vs. `base + contribution`).

Edge cases:

- `opt ≤ 0` is treated as a no-op (returns 1.0 multiplier or 0 additive).
- `part = 0` means "do not add this option's contribution" (factor 0).
- Either field missing → defaults to 1.0.

### 3 · Range — `{areas: [{min, max, part}]}`

```json
"option_scalings": {
  "117": {
    "areas": [
      {"min":  1, "max": 10, "part": 2},
      {"min": 11, "max": 50, "part": 4},
      {"min": 51, "max": null, "part": 8}
    ]
  }
}
```

Reads as: *"if 1–10 selected, use 2 parts; 11–50 → 4; 51+ → 8."*

Resolution:

- Walk `areas[]` in order.
- First range whose `min ≤ selected_qty ≤ max` wins. `null`/missing `min` → `-∞`; `null`/missing `max` → `+∞`.
- Returns the **absolute** `part` value for the matched range.
- No matching range → returns 0 (no parts contributed).

> Range mode is **absolute, not multiplied** by the line's base quantity. The line's `quantity` field on the edge is effectively ignored when a range matches.

## Multiplicative vs. additive resolution

The same `option_scalings` dict is used by two separate code paths with two different resolution semantics:

### Multiplicative path

`_resolve_scaling_factor(entry, selected_qty)` → returns a **multiplier**.

The caller does `base_qty × multiplier`.

This path is used by **`bom_explosion.py`** when computing the explicit explosion of a parent's BOM tree.

### Additive path

`_resolve_scaling_additive(entry, selected_qty)` and `_apply_option_scalings(base, raw_scaling, area_id)` → return an **amount to add** (or pass through `base + Σ(contributions)`).

This path is used by:

- **Snapshot reconstruction** in `app/models.py` (`_apply_option_scalings` inside the snapshot loader).
- **Live computation** for option pricing and live BOM previews.

## Multi-option scaling — independent contributions

When `option_scalings` has **multiple** entries (multiple option ids), each is resolved independently and contributions sum:

```json
"option_scalings": {
  "117": {"opt": 1, "part": 2},
  "240": {"opt": 1, "part": 1}
}
```

If option 117 is selected with amount 5 and option 240 with amount 3:

- 117 contributes `5 × 2/1 = 10` parts.
- 240 contributes `3 × 1/1 = 3` parts.
- Total contribution = `10 + 3 = 13` parts.

The base `quantity` of the line is `base + 13` in additive mode, or `base × (1 + …)` style aggregation in multiplicative mode (path-dependent).

## Area-scoped lookup

Some call sites support an **area-scoped** option amount when the same option exists in multiple areas with different selected numbers. The lookup walks two keys:

1. `f"{opt_id}:{area_id}"` (e.g. `"117:3"`) — area-specific selection.
2. `opt_id` alone — fallback global selection.

This means an edge tied to a specific area can scale by the *per-area* numeric input. If you don't author area-scoped option amounts, only the global key is used.

## Clamping

Negative results are **clamped to 0**: `total = max(total, 0.0)`. The `bom_explosion.py` runtime additionally logs a warning if a BOM-line quantity goes negative after option scaling.

## Worked examples

### Example 1 — Constant per-selection

> "Each selected panel adds 1 bracket."

```json
"option_scalings": {"119": {"opt": 1, "part": 1}}
```

If selected = 24 → 24 brackets added.

### Example 2 — Proportional with ratio

> "Every 4 panels need 1 bracket (rounded behaviour ignored — fractional is fine for cost computation)."

```json
"option_scalings": {"119": {"opt": 4, "part": 1}}
```

If selected = 24 → 6 brackets.

### Example 3 — Inverse ratio

> "Each panel uses 2 fasteners."

```json
"option_scalings": {"119": {"opt": 1, "part": 2}}
```

Selected = 24 → 48 fasteners.

### Example 4 — Range / brackets

> "1–10 panels: 2 frames; 11–50: 4 frames; 51+: 8 frames."

```json
"option_scalings": {
  "119": {
    "areas": [
      {"min": 1, "max": 10, "part": 2},
      {"min": 11, "max": 50, "part": 4},
      {"min": 51, "part": 8}
    ]
  }
}
```

Selected = 24 → 4 frames (matches `[11, 50]`).

### Example 5 — Two numbered options compose

> "Each panel adds 1 bracket; each opening adds 1 cap."

```json
"option_scalings": {
  "119": {"opt": 1, "part": 1},
  "240": {"opt": 1, "part": 1}
}
```

Selected = 24 panels and 6 openings → 24 brackets + 6 caps added (= base + 30 parts in additive mode).

### Example 6 — Length-based scaling (number_unit = m)

> "Ribbon length: 1 m of ribbon per 0.5 m of run length."

```json
"option_scalings": {"117": {"opt": 1, "part": 2}}
```

(Each 1 m of selected length → 2 m of part length added.)

If user enters `length = 4.5 m` → 9 m ribbon.

### Example 7 — Stair-step (range with edges)

> "Up to 5 selected = 1 frame; 6–15 = 2; 16+ = 4."

```json
"option_scalings": {
  "117": {
    "areas": [
      {"max": 5, "part": 1},
      {"min": 6, "max": 15, "part": 2},
      {"min": 16, "part": 4}
    ]
  }
}
```

Note: omitted `min` → `-∞`, omitted `max` → `+∞`.

### Example 8 — Per-area numeric input

> "Area 3 has a length input; area 4 has a separate length input. Each contributes its own ribbon."

Per-area amounts come in as `option_amounts = {"117:3": 4, "117:4": 6}` for the same option 117. Author the line attached to area 3 with `option_scalings: {"117": {"opt": 1, "part": 1}}` and the area-scoped key resolves automatically.

### Example 9 — No-contribution placeholder

> "Track the option but don't change the part quantity."

```json
"option_scalings": {"117": {"opt": 1, "part": 0}}
```

The factor evaluates to 0 → no contribution. Equivalent to omitting the entry.

### Example 10 — Combined with usage_subclauses

> "When option 301 is selected, include 1 frame **per 4 panels** (numbered option 119)."

```json
{
  "usage_subclauses": [
    {"operator": "OR", "groupSelections": {"42": [301]}}
  ],
  "option_scalings": {
    "119": {"opt": 4, "part": 1}
  },
  "quantity": 1
}
```

> **Why `quantity: 1` and not `0`?** The API enforces `quantity > 0` (Pydantic `Field(gt=0)` on `BomItemCreateRequest`). A POST with `quantity: 0` returns 422. With `quantity: 1` the line contributes 1 base frame plus the scaled count. If the design truly needs zero baseline, model it via two BOM lines (one always-on with the baseline, one with `usage_subclauses` carrying only the scaling) or accept the 1-unit baseline.

### Example 11 — Quantity gate + ratio

> "Include 2 baseline frames (regardless of count) plus 1 frame per 4 panels."

```json
{
  "quantity": 2,
  "option_scalings": {"119": {"opt": 4, "part": 1}}
}
```

Selected = 24 → 2 + 6 = 8 frames.

### Example 12 — Range mode replaces base

> "Just use the range; the base quantity is not added separately."

```json
{
  "quantity": 1,
  "option_scalings": {
    "119": {"areas": [{"min": 1, "max": 10, "part": 2}]}
  }
}
```

Selected = 5 → 2 frames (range mode is absolute and overrides the base on the BOM-explosion path; the additive snapshot path adds the range value to the base).

> **Don't author `quantity: 0` for range-mode lines.** The Pydantic schema enforces `quantity > 0` and POSTs with `0` are 422-ed. Use `quantity: 1` (the minimum positive value) and rely on the range descriptor to deliver the absolute number at explosion time. Make the absolute-vs-additive intent explicit in the line's `note` so readers don't assume the base contributes.

## Common pitfalls

- **Numeric-string key.** `option_scalings` keys are **strings**. `"117"` not `117`. The runtime stringifies if needed but JSON authoring should be explicit.
- **Forgot to mark the option `is_numbered: true`.** A non-numbered option has no quantity to scale by; the entry is a no-op.
- **Negative `part` in range.** Allowed — but the line's total amount will be clamped to 0.
- **Overlapping ranges.** Order matters: the **first** matching range wins. Sort by `min` and ensure no overlap.
- **`opt = 0` ratio.** Treated as no-op (avoids division-by-zero). The line contributes 0.
- **Mixing legacy numeric with structured.** Don't. Pick one shape per option entry.

## Validator hints

`scripts/validate_variant_bom.py` should flag:

- `option_scalings` key not matching any option id in the recommendation.
- Range descriptors with overlapping or out-of-order intervals.
- Ratio descriptors with `opt ≤ 0`.
- Legacy numeric entries (warn — prefer structured).
- An `option_scalings` entry whose option is not `is_numbered: true` (warn — likely typo).
