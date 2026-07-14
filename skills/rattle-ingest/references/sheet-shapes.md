# Sheet shapes — the five normalization strategies

A source file has a **shape**: the implicit grain of one row. Get the shape wrong and every column mapping downstream is wrong in the same direction. This reference gives the fingerprint, a worked ASCII example, and the exact normalization strategy for each of the five shapes `detect_sheet_shape()` in `../scripts/profile_source.py` can return.

The output grain in every case is the same: a **flat list of dicts** keyed by role id (`normalized-rows.json`), with `record_type ∈ {product, option, bom_line}` and `_source_row` / `_source_column` provenance on every row. That is the shape `skills/rattle-pricelist-analysis/scripts/detect_anti_patterns.py` already consumes.

| Shape | Grain of one row | Goes to |
|---|---|---|
| `one-row-per-product` | a product | `rattle-suggest-config` (thin — options live elsewhere) |
| `one-row-per-option` | an option | `rattle-suggest-config` |
| `one-row-per-bom-line` | a parent→child BOM edge | **`rattle-bom-builder`**, not suggest-config |
| `wide-variant-matrix` | a product × N variants | `rattle-suggest-config` after a **pivot** |
| `mixed` | nothing coherent | **Split by hand first.** Never normalize in one pass. |

---

## 1 · `one-row-per-product`

**Fingerprint.** The identity column is near-unique per row (`distinct_ratio ≥ 0.95`), there is no `option_name` column, and there are no variant-label headers. Usually one `base_price` column.

```
┌───────────────┬───────────────┬───────────────┬──────────────────────────────────┐
│ Artikelnummer │ Produkt       │ Listenpreis   │ Beschreibung                     │
├───────────────┼───────────────┼───────────────┼──────────────────────────────────┤
│ WP-1000       │ Widget Pro    │ 12.000,00     │ Konfigurierbarer Industrie-…     │
│ WP-1100       │ Widget Pro S  │  9.800,00     │ Kompaktversion für kleinere …    │
│ WP-1200       │ Widget Max    │ 19.500,00     │ Großformat-Variante für …        │
└───────────────┴───────────────┴───────────────┴──────────────────────────────────┘
   product_sku    product_name    base_price      description
```

**Normalization.** One row → one `record_type: "product"`. `base_price` through `decimal_de`. `product_sku` into `product.integration_metadata` (there is no `Product.sku`).

```json
{"record_type": "product", "product_name": "Widget Pro", "product_sku": "WP-1000",
 "base_price": "12000.00", "description": "Konfigurierbarer Industrie-…", "_source_row": 0}
```

**The trap.** This sheet contains **no configuration at all** — no groups, no options, no BOM. That is a finding, not a success. Say so plainly: *"This file defines 3 products and zero configurable features. To build a configurator we need the option data: which features vary, which variants exist per feature, and which variant is standard."* Do not proceed to `rattle-suggest-config` with an empty groups array.

---

## 2 · `one-row-per-option`

**Fingerprint.** An `option_name` column exists alongside a `group_name` and/or `option_price` column, and the product identity **repeats** down the rows (`distinct_ratio < 0.5`) — the rows are sub-entities, not products.

```
┌────────────┬──────────────┬──────────────┬──────────┬───────┬───────────────────┐
│ Produkt    │ Gruppe       │ Option       │ Aufpreis │ Serie │ Beschreibung      │
├────────────┼──────────────┼──────────────┼──────────┼───────┼───────────────────┤
│ Widget Pro │ Räder        │ 17 Zoll      │     0,00 │   x   │ Standardbereifung │
│ Widget Pro │ Räder        │ 19 Zoll      │   500,00 │       │ Sportbereifung    │
│ Widget Pro │ Frässpindel  │ ISO 30       │     0,00 │   x   │ Standardspindel   │
│ Widget Pro │ Frässpindel  │ HSK-63F      │ 2.500,00 │       │ Encoder-Spindel   │
└────────────┴──────────────┴──────────────┴──────────┴───────┴───────────────────┘
 product_name  group_name    option_name   option_price recommended  description
                                                          _flag
```

**Normalization.** One row → one `record_type: "option"`. Group the rows by `group_name` to form the groups. `Serie`/`x` → `recommended_flag: true` via `boolean_marker`.

```json
{"record_type": "option", "product_name": "Widget Pro", "group_name": "Räder",
 "option_name": "17 Zoll", "option_price": "0.00", "recommended_flag": true,
 "description": "Standardbereifung", "_source_row": 0}
```

**This is the shape you want.** It already satisfies the #1 rule: every variant, including the standard, is an explicit row, and the standard is priced 0 and flagged. Validate it:

- Every `group_name` has **at least one** row with `recommended_flag: true` and `option_price` = 0. If a group has only surcharge rows → `missing-standard-variant` blocker (`implicit-base-config`).
- `group.is_multi` is **not in the data.** Default `false`, `review_required: true`, ask.

**If there is no `group_name` column** — just `Option` and `Aufpreis` — you have a flat option list with no feature structure. Do not invent groups by clustering names. Emit an `unresolved-column-role` blocker and ask which feature each option belongs to.

---

## 3 · `one-row-per-bom-line`

**Fingerprint.** `parent_part_number` **and** `part_number` (strongest), or `part_number` with `quantity`/`bom_factor`. The parent column *repeats* — one parent, many children.

```
┌───────────────┬──────────────┬──────────────┬───────┬─────────┬────────┐
│ Vaterartikel  │ Teilenummer  │ Bezeichnung  │ Menge │ Einheit │ Faktor │
├───────────────┼──────────────┼──────────────┼───────┼─────────┼────────┤
│ AX-55         │ BR-12        │ Bracket      │     4 │ Stk     │    1   │
│ AX-55         │ WH-17        │ Rad 17 Zoll  │     4 │ Stk     │    1   │
│ BR-12         │ SC-03        │ Schraube M6  │     8 │ Stk     │    1   │
└───────────────┴──────────────┴──────────────┴───────┴─────────┴────────┘
 parent_part_    part_number    part_name      quantity  unit    bom_factor
 number                         ↑ shape-context: a generic "Bezeichnung" in a BOM
                                  sheet is part.part_name, NOT product.name
```

**Normalization.** One row → one `record_type: "bom_line"` = one `BomItem` (Parent↔Child edge). A row with an `area_name` instead of a parent is a `PartPlacement` (Part↔Area edge) — the two are mutually exclusive.

```json
{"record_type": "bom_line", "parent_part_number": "AX-55", "part_number": "BR-12",
 "part_name": "Bracket", "quantity": 4, "unit": "Stk", "bom_factor": 1.0, "_source_row": 0}
```

**This sheet does NOT go to `rattle-suggest-config`.** It goes to `rattle-bom-builder` / `rattle-bom-architect`.

**The hard truth about this shape.** A BOM export is **variant-blind**. It lists the parts of *one* build; it does not say which option each line depends on. `bom_factor` is meaningless without the option it hangs off — `usage_subclauses` needs `{option_name, factor}`, and the source gives you only the `factor`.

> **The options must exist before the BOM can be wired.** Ingest the configuration sheet first, then come back and attach each BOM line to the option that activates it. A BOM ingested with no `usage_subclauses` produces a *static* BOM: every part in every configuration. That is not a variant BOM, and it is a lie dressed as data.

Emit a blocker per line whose activating option is unknown, or — if the whole sheet is one static build — one `notes` entry saying exactly that, and hand off to `rattle-bom-builder` with empty `usage_subclauses` (= "always include", the legitimate standard case).

---

## 4 · `wide-variant-matrix` — the nasty one

**Fingerprint.** Two or more **numeric** columns whose **headers are variant labels** — a value masquerading as a column name (`19 Zoll`, `HSK-63F mit Encoder`, `Multistep-Modul`) — beside an identity column. The variants have been hoisted out of the data and into the header row; the cells hold their surcharges.

This is what a salesperson's pricelist actually looks like, and it is the single most common real-world input.

```
                            ╔═══════════════════ THE VARIANTS ARE UP HERE ═════════════╗
┌────────────┬───────────────┬───────────┬──────────┬─────────────────────┬────────────────┐
│ Artikel    │ Artikelnummer │ Grundpreis│ 19 Zoll  │ HSK-63F mit Encoder │ Multistep-Modul│
├────────────┼───────────────┼───────────┼──────────┼─────────────────────┼────────────────┤
│ Widget Pro │ WP-1000       │ 12.000,00 │   500,00 │            2.500,00 │         500,00 │
│ Widget Pro │ WP-1100       │  9.800,00 │   500,00 │            2.500,00 │           0,00 │
└────────────┴───────────────┴───────────┴──────────┴─────────────────────┴────────────────┘
 product_name  product_sku    base_price  ╚════════ option_price × 3, headers = option names ═╝
```

**The pivot.** One **cell** → one normalized option row. The header becomes `option_name` (`header_to_option_name`), the cell becomes `option_price` (`cell_to_option_price`), the row's identity column becomes `product_name`.

```
FOR each variant column V:
    FOR each data row R:
        emit {
          record_type: "option",
          product_name: R[identity_column],
          group_name:   <NOT IN THE SOURCE — supplied by the reviewer>,
          option_name:  V.header,
          option_price: decimal_de(R[V]),
          recommended_flag: false,
          _source_row: R.index, _source_column: V.header
        }
```

**What the source does not contain — and you must not invent:**

1. **The group.** Nothing in the sheet says `19 Zoll` belongs to a feature called *Räder* and `HSK-63F mit Encoder` to *Frässpindel*. A human supplies `derived.group_name` per variant column. This is why a variant column is deliberately scored **near the 0.60 review floor** and always carries `review_required: true`.

2. **`is_multi`.** Are the three variants mutually exclusive, or stackable? Not in the data. Default `false`, ask.

3. **THE STANDARD VARIANT — and this is the #1 rule.** Every one of these columns is a **surcharge**. `19 Zoll` costs 500 *on top of* something. That something — the 17-inch wheel that ships as standard — **appears nowhere in the file**. There is no column for it, no zero-priced sibling, no row.

> Without an explicit standard option, no BOM item can carry a `usage_subclause` for the standard part. The configurator can only *add* parts linked to selected options — it cannot *remove* an implicit baseline. The BOM comes out broken. This is `implicit-base-config`, and the wide-variant matrix generates it by construction.

**So the pivot MUST also emit, per group, a placeholder + a blocker:**

```json
{
  "blocker_id": "missing-standard-variant",
  "pattern_id": "implicit-base-config",
  "message": "Column '19 Zoll' is a surcharge column with no standard sibling. The variant that ships as standard is not represented anywhere in the source.",
  "location": "columns[3]",
  "evidence": "header '19 Zoll'; every cell > 0; no zero-priced wheel column exists",
  "placeholder": "PLACEHOLDER-STANDARD-OPTION: <group> / <standard variant unconfirmed>",
  "question": "Which wheel size ships as standard, at what option price (expected 0), and which part does it pull into the BOM?",
  "related_rules": ["explicit-options-for-all-variants"]
}
```

and the matching hole in the normalized rows — **a hole with a label on it, never a guess**:

```json
{"record_type": "option", "product_name": "Widget Pro", "group_name": "Räder",
 "option_name": "PLACEHOLDER-STANDARD-OPTION", "option_price": null,
 "recommended_flag": true, "_blocker_id": "missing-standard-variant"}
```

Do **not** write `{"option_name": "17 Zoll", "option_price": "0.00"}`. You do not know that. A guessed 17-inch standard that is really 18-inch corrupts the BOM, the pricing, and every offer built on top of it — and it will be discovered months later.

**One exception.** A variant column with **zero-priced cells** (like `Multistep-Modul` at `0,00` for `Widget Pro S`) is telling you that variant is *included* for that product. That is a genuine standard signal — a zero in a surcharge column means "no surcharge", i.e. the option is included. Map it `recommended_flag: true` only if the group has no other standard candidate, and still mark `review_required`.

**Merged header cells.** Real matrices often have a merged banner row above the variant labels grouping them by feature (`Räder` spanning two columns). openpyxl in `read_only` mode returns the merged value only in the top-left cell and `None` in the rest. If the header row looks like `[None, None, "Räder", None, "Frässpindel", None]`, you have found the group names — forward-fill them and raise `merged-cells-detected`. If you cannot recover them, that is a `merged-header-cells` blocker.

---

## 5 · `mixed`

**Fingerprint.** Product, option, **and** BOM column families all present in one sheet — or nothing scored decisively (the top shape is below 0.20, or the top two are within 0.15 of each other → `sheet-shape-ambiguous`).

```
┌────────────┬───────────┬──────────┬──────────┬─────────────┬──────────────┬───────┐
│ Produkt    │ Grundpreis│ Option   │ Aufpreis │ Vaterartikel│ Teilenummer  │ Menge │
├────────────┼───────────┼──────────┼──────────┼─────────────┼──────────────┼───────┤
│ Widget Pro │ 12.000,00 │          │          │             │              │       │  ← product row
│            │           │ 17 Zoll  │     0,00 │             │              │       │  ← option row
│            │           │          │          │ AX-55       │ WH-17        │     4 │  ← BOM row
│            │           │ 19 Zoll  │   500,00 │             │              │       │  ← option row
└────────────┴───────────┴──────────┴──────────┴─────────────┴──────────────┴───────┘
```

Three grains stacked in one sheet, distinguished only by which columns are non-null. Blank-heavy columns; nothing near-unique.

**Normalization: do not.** A `mixed` sheet has no single grain, so there is no single correct normalization. Attempting one in a single pass produces rows that are part product, part option, part BOM — and every downstream skill will mis-read them.

**The strategy is to split, then ingest each block:**

1. **Segment by non-null signature.** Classify each row by which column families are populated (`{product_name, base_price}` / `{option_name, option_price}` / `{parent_part_number, part_number}`).
2. **Check for a forward-fill hierarchy.** In the example the blank `Produkt` cells are *inherited* from the row above — an indented outline flattened into a grid. If so, forward-fill the identity columns, then split. If the blanks are genuinely empty, they are not.
3. **Emit one `source-mapping.json` per block**, each with its own single, unambiguous `sheet_shape`.
4. **Ingest the blocks in dependency order**: products → options → BOM lines. The BOM cannot be wired to options that do not exist yet.

If segmentation is not clean — rows that populate two families at once, or an ambiguous forward-fill — stop. Emit an `ambiguous-sheet-shape` blocker with the row indices that resist classification, and ask the user to split the sheet. **A wrong guess here is more expensive than a question.**
