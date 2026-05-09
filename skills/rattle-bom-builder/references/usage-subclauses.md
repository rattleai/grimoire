# `usage_subclauses` — the conditional-inclusion DSL

`usage_subclauses` is the field that makes a BOM line **conditional**. Both `PartPlacement.usage_subclauses` and `BomItem.usage_subclauses` use the **identical** schema and the **identical** evaluator (`evaluate_subclauses` in `app/utils/conditions.py`).

> **Top-level rule.** Empty list (`[]`) = always include. Any non-empty list is evaluated; the line is included only when the list evaluates `True`.

The legacy flag `isStandard: true` on a clause is **silently dropped** during normalisation — empty `usage_subclauses` does the same job.

## Clause shape

A clause is a dict with up to four keys:

```json
{
  "operator": "AND" | "OR",
  "groupSelections": {"<group_id>": [<option_id>, ...]},
  "areaStatuses":     {"<area_id>": <bool>},
  "areaSubclauses":   [<area_clause>, ...]
}
```

| Key | Type | Required | Meaning |
|---|---|---|---|
| `operator` | `"AND"` / `"OR"` | yes (default `"OR"` on first clause) | How this clause combines with the running result of all prior clauses. The first clause's operator is applied as the seed; subsequent clauses fold left-to-right. |
| `groupSelections` | `{group_id: [option_id, ...]}` | optional | The clause is satisfied for **groupSelections** when, for every group listed, **at least one** of the listed options is in `chosen_option_ids`. Note: keys are stringified group ids; values are arrays of integer option ids. |
| `areaStatuses` | `{area_id: bool}` | optional | The clause is satisfied for **areaStatuses** when **every** area listed has the matching enabled state. `true` = the area must be enabled; `false` = the area must be disabled. |
| `areaSubclauses` | `[{operator, areaStatuses}]` | optional | A nested list of area-only clauses combined with their own AND/OR operators. Use when you need (`area X enabled OR area Y enabled`) rather than the conjunction `areaStatuses` gives. |

A clause is satisfied iff its area part **AND** its `groupSelections` part both pass.

## Combining clauses

The full `usage_subclauses` list is folded **left-to-right**:

```
result = satisfied(clauses[0])
for clause in clauses[1:]:
    nxt = satisfied(clause)
    if clause.operator == "AND":
        result = result and nxt
    else:  # "OR"
        result = result or nxt
```

> Operator precedence is **left-to-right, no implicit grouping**. To express `A AND (B OR C)` you need to model the inner OR via `areaSubclauses` or via a single clause whose `groupSelections` already accepts B-or-C in one group.

## Worked examples

### Example 1 — Always include (the standard line)

```json
"usage_subclauses": []
```

The line is always active.

### Example 2 — Single option triggers

> "Include only when option `301` (the 19" wheel option) is selected."

```json
"usage_subclauses": [
  {"operator": "OR", "groupSelections": {"42": [301]}}
]
```

### Example 3 — Either-of in one group (OR within a group)

> "Include when option `301` OR `302` is selected in group 42."

```json
"usage_subclauses": [
  {"operator": "OR", "groupSelections": {"42": [301, 302]}}
]
```

The list semantic for a single group is *any-of* (logical OR over the option ids).

### Example 4 — Two groups, both required (AND across groups)

> "Include when (any of 301/302 in group 42) AND (option 410 in group 55)."

```json
"usage_subclauses": [
  {
    "operator": "OR",
    "groupSelections": {"42": [301, 302], "55": [410]}
  }
]
```

When `groupSelections` lists multiple groups in **one clause**, they are AND-combined automatically.

### Example 5 — Two clauses combined with OR (either configuration triggers)

> "Include when (option 301 in group 42) OR (option 410 in group 55) — these are independent triggers."

```json
"usage_subclauses": [
  {"operator": "OR", "groupSelections": {"42": [301]}},
  {"operator": "OR", "groupSelections": {"55": [410]}}
]
```

### Example 6 — Two clauses combined with AND

> "Include only when (option 301 in group 42) AND (option 410 in group 55) — both required."

```json
"usage_subclauses": [
  {"operator": "OR", "groupSelections": {"42": [301]}},
  {"operator": "AND", "groupSelections": {"55": [410]}}
]
```

The first clause's operator is the seed (`OR` against the empty start); the second clause AND-folds with the running result. Equivalent to Example 4, expressed differently.

### Example 7 — Area-gated line

> "Include this part only when area `3` is enabled (e.g. only for products that have the *outdoor* area assigned)."

```json
"usage_subclauses": [
  {"operator": "OR", "areaStatuses": {"3": true}}
]
```

### Example 8 — Either-area gating with area subclauses

> "Include when area `3` OR area `4` is enabled (the part lives on either)."

```json
"usage_subclauses": [
  {
    "operator": "OR",
    "areaSubclauses": [
      {"operator": "AND", "areaStatuses": {"3": true}},
      {"operator": "OR",  "areaStatuses": {"4": true}}
    ]
  }
]
```

`areaSubclauses` is the only way to OR area conditions inside a single clause. (Top-level `areaStatuses` AND-combines its keys.)

### Example 9 — Combined option + area

> "Include when option `301` is selected AND area `3` is enabled."

```json
"usage_subclauses": [
  {
    "operator": "OR",
    "groupSelections": {"42": [301]},
    "areaStatuses": {"3": true}
  }
]
```

The area and group parts of a clause are AND-combined. Both must pass.

## Common pitfalls

- **Stringified vs. integer keys.** `groupSelections` keys must be **stringified** group ids (`"42"`, not `42`). The normaliser stringifies them, but if you author by hand keep them as strings.
- **Unknown options in groupSelections.** Options that don't exist are kept in storage but evaluate `False` at runtime — so the clause silently never matches. Always validate via `scripts/validate_variant_bom.py`.
- **`isStandard: true` doesn't work anymore.** It's stripped on save. Use empty `usage_subclauses` instead.
- **First-clause operator is informational.** It seeds the fold but can't change the truth value of clause 0 itself. The visible behaviour is determined by clauses 1..N.
- **Empty clause is dropped.** A clause without `groupSelections`, `areaStatuses`, or `areaSubclauses` is removed during normalisation — it would always evaluate True and is meaningless.

## DSL evaluator reference

The actual evaluator code lives in `app/utils/conditions.py` (functions `normalise_conditions`, `subclause_satisfied`, `evaluate_subclauses`). Read it when you need to understand a corner case — it is the source of truth.
