# Numbered options — pattern catalogue

A **numbered option** carries a user-entered number, not a boolean presence. It powers every part-scaling pattern in the BOM. This catalogue lists the scaling patterns that come up most often in real configurators and the exact JSON to write.

## The numbered-option fields (`Option`)

```python
class Option(db.Model):
    option_name        # "Panels"
    option_price       # base price (often 0; price_scalings carries the real model)
    option_key         # custom integration key
    is_numbered        # True to enable the numeric input
    number_min         # int | None
    number_max         # int | None
    number_step        # int | None  (e.g. 1, 5, 25)
    number_unit        # "pcs" | "m" | "mm" | "kg" | "m²" | "°" | …
    price_scalings     # {opt_id_referenced: descriptor} — same shape as option_scalings
    recommended        # bool
```

> **`option_key`** is the stable code you reference from external systems (ERP / CRM / pricelist). Use it consistently for cross-system mapping.

## Runtime contract

When the user enters a number for a numbered option:

- The configuration carries it forward as `option_amounts[opt_id] = selected_qty` (and optionally `option_amounts[f"{opt_id}:{area_id}"]` for area-scoped inputs).
- Every BOM edge whose `option_scalings` references that option id is resolved with `selected_qty` plugged in.
- The `usage_subclauses` field of the same edge is **independent** — it controls whether the line is active at all (boolean inclusion). The `option_scalings` controls *how much*.

This means a typical numbered-option BOM line has both:

```json
{
  "usage_subclauses": [
    {"operator": "OR", "groupSelections": {"<panel-group-id>": [<panels-option-id>]}}
  ],
  "option_scalings": {
    "<panels-option-id>": {"opt": 1, "part": 1}
  }
}
```

## Pattern catalogue

### Pattern 1 — One-to-one count scaling

> "Each selected panel needs 1 bracket."

```json
"option_scalings": {"<panels>": {"opt": 1, "part": 1}}
```

Selected = 24 → 24 brackets.

### Pattern 2 — Many-to-one (every N selected → 1 part)

> "Every 4 panels need 1 brace."

```json
"option_scalings": {"<panels>": {"opt": 4, "part": 1}}
```

Selected = 24 → 6 braces.

### Pattern 3 — One-to-many (each selection brings multiple parts)

> "Each panel needs 2 fasteners."

```json
"option_scalings": {"<panels>": {"opt": 1, "part": 2}}
```

Selected = 24 → 48 fasteners.

### Pattern 4 — Length-scaled (numbered option in metres)

> "Ribbon length scales 1:1 with selected run length."

Option setup:

```json
{
  "option_name": "Run length",
  "is_numbered": true,
  "number_min": 0.5,
  "number_max": 30,
  "number_step": 0.1,
  "number_unit": "m"
}
```

BOM edge:

```json
"option_scalings": {"<run-length>": {"opt": 1, "part": 1}}
```

Selected = 4.5 m → ribbon part quantity = 4.5 m. Match the part's `uom` to the option's `number_unit`.

### Pattern 5 — Length-with-overlap (1.1× the run for splice waste)

> "Ribbon length = run length × 1.1 to allow for splice overlap."

```json
"option_scalings": {"<run-length>": {"opt": 1, "part": 1.1}}
```

Selected = 4.5 m → 4.95 m. Alternatively bake the splice into `scrap_percent: 10` and keep the ratio 1:1 — the latter is cleaner because scrap shows up separately on cost reports.

### Pattern 6 — Stair-stepped count (range descriptor)

> "Up to 5 panels: 1 frame; 6–15: 2 frames; 16+: 4 frames."

```json
"option_scalings": {
  "<panels>": {
    "areas": [
      {"max": 5, "part": 1},
      {"min": 6, "max": 15, "part": 2},
      {"min": 16, "part": 4}
    ]
  }
}
```

Set the line's `quantity` to `1` (the API rejects `0` with 422). Range-mode resolution is absolute on the explosion path; on the snapshot path the absolute value is added to the base. Document the absolute-vs-additive intent in the line's `note`.

### Pattern 7 — Threshold breakpoint (price/qty changes after threshold)

> "Below 50 m: standard ribbon; 50 m and above: premium ribbon (different part)."

Use **two BOM edges** with mutually exclusive ranges:

```json
[
  {
    "child_part_number": "RIB-STD",
    "option_scalings": {"<run-length>": {"areas": [{"max": 49.99, "part": 1}]}},
    "alt_group": "ribbon",
    "priority": 1
  },
  {
    "child_part_number": "RIB-PRM",
    "option_scalings": {"<run-length>": {"areas": [{"min": 50, "part": 1}]}},
    "alt_group": "ribbon",
    "priority": 2
  }
]
```

Or simpler: one edge per part with `usage_subclauses` keyed to a *separate* boolean option toggled by the configurator's logic.

### Pattern 8 — Multi-option composition

> "Each panel needs 1 bracket; each opening needs 1 cap; the configurator has both numbered options."

```json
"option_scalings": {
  "<panels>": {"opt": 1, "part": 1},
  "<openings>": {"opt": 1, "part": 1}
}
```

If selected_panels = 24 and selected_openings = 6 → 24 brackets + 6 caps total.

### Pattern 9 — Conditional + scaled

> "When the 'Premium frame' option is selected, also add 1 brace per 4 panels."

```json
{
  "usage_subclauses": [
    {"operator": "OR", "groupSelections": {"<frame-group>": [<premium-option>]}}
  ],
  "option_scalings": {
    "<panels>": {"opt": 4, "part": 1}
  },
  "quantity": 1
}
```

The line is active only when the premium frame is chosen; the count of braces is `1 + selected/4` (one baseline brace plus the scaled count). The API requires `quantity > 0` (Pydantic `gt=0`), so the baseline cannot be eliminated on a single line — model "scaled-only" via two BOM lines if the design demands it.

### Pattern 10 — Area-scoped scaling

> "Two areas, each with its own length input. Each area's ribbon is sized by its own length."

Configure the option once with `is_numbered: true`. Configure two areas in the product. Author one BOM edge per area, each with the same `option_scalings`:

```json
"option_scalings": {"<run-length>": {"opt": 1, "part": 1}}
```

The runtime resolves `option_amounts["117:3"]` for area 3 and `option_amounts["117:4"]` for area 4 independently. No special configuration needed beyond authoring the edges per area.

### Pattern 11 — Length × width (area dimension)

> "The wall area is computed from two numbered options (length, height); each m² uses 1 m² of insulation."

The configurator does not multiply numeric inputs. You have **two options**: implement the multiplication in the host application before sending `option_amounts`, OR derive a third numbered option (`area_m2`) and write your scaling against it. Most teams pre-compute and inject `area_m2` so the BOM stays in one shape.

### Pattern 12 — Floor / ceiling on scaled quantity

> "Always at least 4 brackets, even with few panels."

The runtime does not floor or ceil. Encode it via two edges:

```json
[
  {
    "child_part_number": "BRK-12",
    "quantity": 4,
    "option_scalings": {},
    "note": "minimum 4 brackets"
  },
  {
    "child_part_number": "BRK-12",
    "quantity": 1,
    "option_scalings": {"<panels>": {"areas": [{"min": 21, "part": 1}]}},
    "note": "extra brackets above 20 panels — quantity=1 is the API minimum (gt=0); on the additive snapshot path this 1 is added to the range value, on the explosion path the range value overrides"
  }
]
```

This composes the floor (always 4 from the first edge) with bracketed extras (from the second edge). The two lines aggregate via `totals_by_part` so the BOM rolls up the sum.

## How to validate

Run `scripts/validate_variant_bom.py` and confirm:

- Every numbered-option referenced in `option_scalings` is `is_numbered: true` in the configuration.
- `number_min` / `number_max` align with the BOM ranges (e.g. don't set a range `min: 51` if `number_max: 50`).
- `number_step` is consistent with the granularity assumed by the ratios (an `opt: 4` ratio with `step: 5` means selected counts of 5, 10, 15… give fractional frames).
- `number_unit` matches the part's `uom` for length / area scalings.

## Pitfalls specific to numbered options

- **Forgetting to set `is_numbered: true`** — the option renders as a checkbox; selecting it gives `option_amounts[id] = 1` regardless. Scaling factors silently use 1.
- **Inconsistent units** — option in `m`, part in `pcs`. The runtime computes anyway but cost reports become meaningless.
- **Step-aware fractional output** — a ratio `{opt: 4, part: 1}` with selected = 5 gives 1.25 parts. Decide if your manufacturing ERP rounds; if so, encode the rounding via a range descriptor instead.
- **Large `number_max`** — if `max = 1000` and ratio `{opt: 1, part: 1}`, the BOM contains 1000 part rows after explosion. Use range descriptors to compress.
