# BOM explosion — runtime semantics

The BOM-explosion engine walks every edge from a root product / placement down through `BomItem` rows, evaluates conditions, applies scalings, and emits a flat list of effective parts at every level. Source: `app/utils/bom_explosion.py`.

This reference documents what the engine does so you can predict the output of any variant-BOM you author.

## Inputs to the engine

| Input | Source |
|---|---|
| Root part(s) | The placement(s) of the product being exploded |
| `chosen_option_ids` | Set of option ids selected in the configuration |
| `enabled_area_ids` | Set of area ids enabled for the configuration |
| `option_amounts` | `{opt_id: number}` for numbered options; optional area-scoped keys `f"{opt_id}:{area_id}"` |
| `effective_option_context` | Override option/area context (rare; per-area resolution) |
| `as_of` | Date for `effective_from` / `effective_to` filtering |
| `resolve_ghosts` | Bool — whether to treat ghost parts as depth-transparent |
| `max_phantom_depth` | Default 3 — warn when ghost nesting exceeds this |

## Per-edge evaluation order

For each `PartPlacement` and `BomItem` the engine encounters:

1. **Effectivity filter** (BomItem only).
   `effective_from <= as_of <= effective_to`. If outside the window, the edge is skipped.

2. **Subclause evaluation** (both edges).
   `evaluate_subclauses(usage_subclauses, chosen_option_ids, enabled_area_ids)`. If False, skip the edge entirely.

3. **Quantity computation** (both edges).
   `_resolve_scaling_factor(option_scalings, selected_qty)` (multiplicative) OR `_resolve_scaling_additive(...)` (additive, snapshot path). Resolve every option entry, then apply to the line's `quantity`.

4. **Scrap allowance** (BomItem only).
   `direct_amount × (1 + scrap_percent / 100)`. Negative `scrap_percent` is clamped to 0; > 100 logs a warning but is honoured.

5. **Negative-clamp** (both edges).
   `max(direct_amount, 0)`. A negative result logs a warning and is clamped.

6. **Path-multiplier propagation.**
   `total_amount_structured = parent_path_multiplier × direct_amount`. The path multiplier is the product of all `direct_amount`s back to the root.

7. **Emit row.**
   The engine records `parent_part_id`, `child_part_id`, `level`, `amount` (this edge), `total_amount_structured` (path-rolled), `uom`, `scrap_percent`, `alt_group`, `priority`, `ghost_part`, `bom_item_id`.

8. **Recurse.**
   Push `(child_part_id, level+1, total_amount_structured)` onto the traversal stack. If the child is a ghost, its level is **not incremented** (ghosts are depth-transparent).

## Alternates (`alt_group`)

When multiple BomItem rows under the same parent share an `alt_group`:

1. Filter to edges that pass effectivity + subclause evaluation.
2. Sort by `priority` ASC, then `order_index` ASC.
3. Emit the first; skip the rest in the group.

> **Result:** exactly one alternate per group is emitted in the explosion output. Alternates are mutually exclusive in the manufacturing BOM.

## Ghost / phantom resolution

A `BomItem` (or `Part`) with `ghost_part: true` is **structural only**: it exists for editing convenience but does not consume a level in the manufactured BOM.

- The ghost row itself is still emitted (with `ghost_part: true` and `is_ghost_assembly: true` markers in `row_data`) so audits can see it.
- Its **children** inherit the ghost's level (not level+1) → depth-transparent.
- The `ghost_resolutions` map in the explosion result records `{ghost_part_id: [resolved_child_ids]}` so callers can replay the resolution.

If ghost depth > `max_phantom_depth` (default 3), the engine adds a `phantom_depth_warnings` entry recommending hierarchy simplification. The traversal continues — the warning is informational.

The standalone helper `resolve_ghost_assembly(ghost_part_id, ...)` returns the **100% BOM** for a ghost: every child that would resolve under the supplied condition predicate, with alternate-group selection applied. Use this for ghost previews and "what-if" tooling.

## Aggregation

The engine produces:

```json
{
  "rows": [{...}, ...],
  "totals_by_part": {<part_id>: <total_amount>},
  "area_id": <area_id>,
  "area_context_applied": true,
  "ghost_resolutions": {<ghost_part_id>: [<child_id>, ...]},
  "phantom_depth_warnings": [{...}]
}
```

`rows` is sorted by `(level, parent_part_id, child_part_number, bom_item_id)`. `totals_by_part` is summed across all paths and is the right field to use for cost / weight roll-ups.

## Worked example

Configuration:

- `chosen_option_ids = {301, 119}` (option 301 = "Premium frame", option 119 = "Panels" with `is_numbered=true`)
- `option_amounts = {119: 24}`
- `enabled_area_ids = {3}`

Edges (simplified):

```json
[
  {
    "edge": "Placement",
    "part": "AX-55",
    "area_id": 3,
    "quantity": 1,
    "usage_subclauses": [{"operator": "OR", "groupSelections": {"42": [301]}}],
    "option_scalings": {}
  },
  {
    "edge": "BomItem",
    "parent": "AX-55",
    "child": "BR-12",
    "quantity": 0,
    "scrap_percent": 5,
    "usage_subclauses": [],
    "option_scalings": {"119": {"opt": 4, "part": 1}}
  }
]
```

Evaluation:

1. Placement passes (option 301 chosen). Quantity = 1. Path mult = 1.
2. Recurse to AX-55 children.
3. BomItem `BR-12`: no subclause restriction → passes. Base quantity = 0. Option scaling `{119: opt=4 part=1}` with selected=24 → 6 brackets.
4. Apply scrap 5% → 6 × 1.05 = 6.3 brackets.
5. Path-rolled total = 1 (parent) × 6.3 = 6.3 brackets.

Output `rows`:

```json
[
  {"level": 0, "parent_part_id": null, "child_part_id": "<AX-55>", "amount": 1, "total_amount_structured": 1},
  {"level": 1, "parent_part_id": "<AX-55>", "child_part_id": "<BR-12>", "amount": 6.3, "total_amount_structured": 6.3, "scrap_percent": 5}
]
```

`totals_by_part = {<AX-55>: 1.0, <BR-12>: 6.3}`.

## Related runtime helpers

- `app/utils/conditions.py` — `evaluate_subclauses`, `subclause_satisfied`, `normalise_conditions`.
- `app/utils/bom_explosion.py` — `_resolve_scaling_factor`, `_resolve_scaling_additive`, `explode_bom`, `resolve_ghost_assembly`.
- `app/models.py` — `_apply_option_scalings` (snapshot path), helper methods on `Part`, `PartPlacement`, `BomItem`.
- `app/utils/profitability.py` — uses the explosion to roll cost up.
- `app/utils/ghost_materialization.py` / `ghost_validation.py` — ghost-specific tools.
