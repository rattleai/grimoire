---
name: rattle-ingest
description: Use this skill whenever the user hands over raw customer data — an Excel/CSV pricelist, an ERP or PLM export, a Stückliste/BOM dump, an Artikelliste, a PDF Preisliste, an onboarding data drop — and it must be mapped onto Rattle entities. Activates for "ingest", "import", "column mapping", "Excel", "CSV", "spreadsheet", "ERP export", "SAP export", "Artikelliste", "Stückliste", "Preisliste", "data migration", "onboarding data", "which column is what", "normalize this sheet". The FIRST link in the chain: rattle-ingest → rattle-pricelist-analysis → rattle-suggest-config → rattle-apply-config. Profiles the source deterministically (dtype, cardinality, value samples — never the header alone), classifies every column into one of 24 roles, detects the sheet shape, and emits a reviewable source-mapping.json plus normalized rows. Enforces the #1 rule at the door: a surcharge column with no standard row is an implicit-base-config blocker — surface it, never invent the standard variant.
license: MIT
---

# Rattle source ingestion

Nothing downstream works until the customer's raw file has been mapped onto Rattle entities. `rattle-pricelist-analysis` emits *findings*, `rattle-suggest-config` emits a *recommendation* — but neither of them knows that column D of `Preisliste_2026.xlsx` is a surcharge for a wheel variant whose standard sibling exists nowhere in the file. **This skill is the first link.** It turns an arbitrary sheet into two artifacts: a `source-mapping.json` a human can review in one sitting, and a `normalized-rows.json` the rest of the chain consumes.

Ingestion is a **read-only, local** step. It never calls the Rattle API and never writes to a tenant.

## When to use this skill

- The user drops a pricelist, Artikelliste, Stückliste, ERP/PLM export, or configurator spreadsheet and asks "can you get this into Rattle?", "what's in this file?", "map these columns", "import this".
- The user is onboarding a new tenant and has a data pile but no configuration yet.
- `rattle-pricelist-analysis` or `rattle-suggest-config` was asked to run on a file whose columns have not been mapped — stop, run this first.
- The user asks why a column was ignored, or wants to correct a mapping and re-run.

If the file is already a list-of-dicts with unambiguous, agreed column meanings, skip straight to `rattle-pricelist-analysis`. If the data already lives in Rattle, this is an audit — use `rattle-audit`.

## The ingestion contract

Three promises, in priority order. Break any of them and the whole chain downstream inherits the damage.

1. **Never guess a column's meaning from its header alone.** Headers lie, are abbreviated, are in three languages, or are empty. A role is only credible when the **header keyword** and the **value shape** (dtype, cardinality, null count, samples) agree. `scripts/profile_source.py` computes both and scores them jointly; a header hit with a contradicting value shape scores *worse* than no hit at all.

2. **Never fabricate.** Not a standard option, not a price, not a part number, not a group name. Where the source is silent, emit a **placeholder** plus a **blocker** carrying the one question a human must answer. A guessed 17-inch standard wheel that turns out to be 18-inch corrupts the BOM, the pricing, and every offer built on it.

3. **Never silently drop a column.** Every column of the source appears either in `columns[]` with a role, or in `unmapped_columns[]` with a stated reason. Every mapping below the 0.60 confidence floor appears in `warnings[]` with `review_required: true`. Silence is the one unacceptable output.

## The #1 rule, enforced at the door

> **Every configurable feature MUST have an explicit group with ALL variants as separate options — including the standard variant.** (`explicit-options-for-all-variants`)

A classic pricelist is a list of **surcharges**. It says `Aufpreis 19 Zoll: 500 €` and says nothing at all about the 17-inch wheels that ship as standard — because to the salesperson who wrote it, the standard is invisible. Ingestion is where that invisibility becomes a **blocker**, not three steps later when a BOM comes out empty.

**The rule this skill applies:** a column (or row group) of surcharges with **no zero-priced / standard sibling** is an `implicit-base-config` (or `addon-only-options`, or `addon-only-software-modules`) finding. Emit:

```json
{
  "blocker_id": "missing-standard-variant",
  "pattern_id": "implicit-base-config",
  "message": "Column '19 Zoll' is a surcharge with no standard sibling. The variant that ships as standard is not represented anywhere in the source.",
  "location": "columns[5]",
  "evidence": "header '19 Zoll'; all cells > 0; no zero-priced wheel column",
  "placeholder": "PLACEHOLDER-STANDARD-OPTION: Räder / <standard variant unconfirmed>",
  "question": "Which wheel size ships as standard, at what option price (expected 0), and which part does it pull into the BOM?",
  "related_rules": ["explicit-options-for-all-variants"]
}
```

Do **not** invent `"17 Zoll", price 0, recommended true`. The placeholder is not a value — it is a hole with a label on it. `rattle-suggest-config` MUST NOT run while `blockers[]` is non-empty.

## Workflow

1. **Profile the source deterministically.** Never open the file and eyeball the headers. Run:

   ```bash
   python3 skills/rattle-ingest/scripts/profile_source.py <file> [--sheet NAME]
   ```

   Reading is delegated to the readers that already exist — `rattle_api.source.read_source()` (Excel via openpyxl, PDF via pymupdf, Word via python-docx) and the stdlib `csv`/`json` readers. Do not reinvent file parsing. The profiler returns, per column: `index`, `header`, `dtype`, `non_null`, `cardinality`, `distinct_ratio`, up to 5 verbatim `samples`, numeric stats where numeric, and a **ranked `candidate_roles` list with confidence scores**. It also returns a `sheet_shape` guess with its evidence.

   PDF and Word inputs have no columns. Extract the text, reconstruct the implied table, and profile *that* — recording `file_type: "pdf"` and a `notes` entry stating the table was reconstructed, not read.

2. **Classify every column into a column role.** Take the profiler's ranked candidates as a proposal, not a verdict. Apply the taxonomy below and the full heuristics in `references/column-roles.md`. Rules that hold every time:
   - Confidence `< 0.60` → `review_required: true` **and** a `low-confidence-mapping` warning.
   - A mapping that invents structure the source does not state (a pivot's `group_name`, for example) → `review_required: true` regardless of confidence.
   - Two columns claiming the same singular role (two `base_price` columns) → keep one, demote the other to `unmapped_columns` with the reason, or resolve with the user.

3. **Detect the shape of the sheet.** Five shapes, each with exactly one documented normalization strategy — the full worked examples live in `references/sheet-shapes.md`:

   | Shape | Fingerprint | Normalization |
   |---|---|---|
   | `one-row-per-product` | identity column near-unique per row; no option column; no variant-label headers | 1 row → 1 product. Options live elsewhere (or nowhere — say so). |
   | `one-row-per-option` | `option_name` column present, product identity repeats down the rows | 1 row → 1 option. Group from `group_name`, else one group per feature — ask. |
   | `one-row-per-bom-line` | `parent_part_number` + `part_number`, or `part_number` + `quantity`/`bom_factor` | 1 row → 1 BOM edge. Feed `rattle-bom-builder`, not `rattle-suggest-config`. |
   | `wide-variant-matrix` | ≥2 numeric columns whose **headers are variant labels** ("19 Zoll", "HSK-63F mit Encoder") beside an identity column | **Pivot.** 1 cell → 1 (group, option, price). The nastiest and the most common. |
   | `mixed` | product, option, and BOM column families all in one sheet; or nothing scores decisively | Split the sheet by hand into single-shape blocks, then ingest each. Never normalize a mixed sheet in one pass. |

   The shape also disambiguates roles a column cannot: in a `one-row-per-bom-line` sheet a generic `Bezeichnung` column is `part.part_name`, not `product.name`. The profiler applies this re-rank and records the signal `shape-context:one-row-per-bom-line`.

4. **Emit `source-mapping.json`.** This is the reviewable artifact and the point of the whole skill. It validates against `schemas/source-mapping.schema.json`. It carries the source metadata, the sheet shape and its evidence, one entry per column (role, confidence, `target_entity`, `target_field`, `transform`, samples, candidates), `unmapped_columns[]`, `blockers[]`, and `warnings[]`. **Present it to the user and get confirmation before normalizing.** A mapping is cheap to fix; a wrong configuration applied to a live tenant is not.

5. **Normalize to the intermediate row form.** Only after the mapping is confirmed. Emit `normalized-rows.json`: a **JSON array of flat objects** keyed by role id — exactly the list-of-dicts shape that `skills/rattle-pricelist-analysis/scripts/detect_anti_patterns.py` and `rattle-suggest-config` already consume. Apply the declared `transform` per column (`decimal_de` turns `"1.234,56 €"` into `"1234.56"`; `boolean_marker` turns `x` / `✓` / `ja` into `true`). Carry provenance on every row (`_source_row`, `_source_column`) so any finding can be traced back to a cell.

6. **Flag everything you could not resolve.** Every unmapped column, every low-confidence mapping, every coerced value, every assumed decimal separator, every placeholder — into `warnings[]` or `blockers[]`. Then report: blockers first, warnings second, the confirmed mapping last.

## Column-role taxonomy

24 roles. The detection heuristics (DE + EN keywords, value-shape signals, confidence rules) are in `references/column-roles.md`; this table is the contract.

| Role | What it looks like in real data | How to detect it | What it becomes in Rattle |
|---|---|---|---|
| `product_name` | `Widget Pro`, `Typ WX-200` | Header ~ Produkt/Artikel/Bezeichnung/Modell/Typ; dtype `string`, dense | `product.name` |
| `product_sku` | `WP-1000`, `4711-002` | Header ~ Artikelnummer/Sachnummer/SKU; `distinct_ratio ≥ 0.90`, digit-bearing | **No Rattle `Product.sku` field exists.** → `product.integration_metadata.<key>` (free-form object). Never invent a `sku` field. |
| `area_name` | `Mechanik`, `Steuerung` | Header ~ Bereich/Baugruppe/Sektion; low cardinality text | `area.name` |
| `group_name` | `Räder`, `Frässpindel` | Header ~ Gruppe/Merkmal/Kategorie; low cardinality text | `group.name` (`group.is_multi` must be decided — it is never in the data) |
| `option_name` | `17 Zoll`, `HSK-63F mit Encoder` | Header ~ Option/Variante/Ausführung; varied text. In a wide matrix the **header itself** is the option name | `option.name` |
| `option_price` | `500`, `2.500,00 €`, `0,00` | Header ~ Aufpreis/Mehrpreis/Zuschlag/Surcharge, **or** a variant-label header over numeric cells; dtype numeric | `option.price` (decimal string) |
| `base_price` | `12.000,00` | Header ~ Grundpreis/Listenpreis/Preis; numeric, dense, one per sheet | `product.base_price` (decimal string) |
| `currency` | `EUR`, `€` | Header ~ Währung/Currency; values in the ISO/symbol set | **Not writable.** `ProductCreateRequest.currency` is *accepted but ignored* — currency is derived from the company base price list. Use it only to pick the decimal parser. `target_entity: none`, and raise `currency-not-writable`. |
| `recommended_flag` | `x`, `✓`, `Serie`, `serienmäßig` | Header ~ Serie/Standard/Grundausstattung; dtype `boolean` or pure marker values | `option.recommended` (and the standard option's `price` should be `0`) |
| `quantity` | `4`, `1` | Header ~ Menge/Stück/Anzahl/Qty; numeric | `bom_item.quantity` / `part_placement.quantity` |
| `unit` | `Stk`, `m`, `kg` | Header ~ Einheit/ME/UoM; values in the UoM token set | `bom_item.uom` / `part_placement.uom` (default `pcs`) |
| `part_number` | `BR-12`, `100234` | Header ~ Teilenummer/Part No; near-unique | `part.part_number` (required, 1–255 chars) |
| `part_name` | `Bracket`, `Rad 17 Zoll` | Header ~ Benennung/Teilebezeichnung; or a generic name column **in a BOM-shaped sheet** | `part.part_name` (**required** by `PartCreateRequest` — a part cannot be created without it) |
| `parent_part_number` | `AX-55` repeated down the rows | Header ~ Vaterartikel/übergeordnet/Parent; **repeating** identifier (`0 < distinct_ratio < 1`) | `bom_item.parent_part_id` (resolved from the number at apply time) |
| `bom_factor` | `1.0`, `0.5` | Header ~ Faktor/Verwendungsfaktor/Multiplier; numeric | `usage_subclauses[].factor` — see `rattle-bom-builder` |
| `number_min` | `1` | Header token `min`/`von`/`Untergrenze`; numeric | `option.number_min` (requires `option.is_numbered = true`) |
| `number_max` | `50` | Header token `max`/`bis`/`Obergrenze`; numeric | `option.number_max` |
| `number_step` | `1` | Header token `step`/`Schritt`/`Schrittweite`; numeric | `option.number_step` |
| `number_unit` | `mm`, `Stk` | Header ~ Eingabeeinheit/Number unit | `option.number_unit` |
| `constraint_exclusion` | `nicht mit 19 Zoll; ohne Encoder` | Header ~ Ausschluss/nicht kombinierbar/Excludes; list-like text | `forbidden` pairs (`POST /constraints`, body field `forbidden`) or a `constraint_rule` — see `rattle-suggest-config` |
| `description` | long prose | Header ~ Beschreibung/Langtext/Bemerkung; avg sample length ≥ 40 | `product.description` / `option.description` / `group.description`. **Narrative prose is a `description-area-smell`** — it belongs in a document template, not an area. |
| `image_ref` | `wheel19.png`, `https://…` | Values match an image extension or an http(s) URL | Upload via `POST /options/{optionId}/image` (or `/products/{productId}/image`, `/areas/{areaId}/image`). **There is no public upload route for `Part.part_img`** — do not map part images. |
| `locale` | `DE`, `de-DE` | Header ~ Sprache/Language; values match a locale pattern | `language` on product / area / group / option (max 8 chars, default `DE`) |
| `ignore` | internal margin, buyer initials, colour codes | Deliberately excluded after review | Nothing. Must still appear in `unmapped_columns[]` or carry role `ignore` — the audit trail proves it was seen. |

**Fields that do not exist — do not invent them.** There is no `Product.sku`, no `Option.sku`, no writable `Product.currency`, and no public `Part.part_img` upload route. `Part.part_cost` is an **integer** (`ge=0`), not a decimal: a `12,50` cost column must be rounded and the rounding raised as a `part-cost-rounded` warning.

## Output contract

Two files. The first is for the human; the second is for the machines downstream.

### `source-mapping.json` — validates against `schemas/source-mapping.schema.json`

```json
{
  "tenant": "acme",
  "source": {
    "path": "source/acme/preisliste-2026.xlsx",
    "file_type": "xlsx",
    "sheet_name": "Preisliste",
    "header_row": 0,
    "row_count": 2,
    "column_count": 9
  },
  "sheet_shape": {
    "id": "wide-variant-matrix",
    "confidence": 0.7,
    "evidence": ["3 numeric columns whose headers are variant labels … → variants live in the header row"],
    "normalization": "Pivot each variant column into a (group, option, price) triple; one normalized row per non-empty cell."
  },
  "columns": [
    {
      "index": 5,
      "header": "19 Zoll",
      "role": "option_price",
      "confidence": 0.58,
      "target_entity": "option",
      "target_field": "price",
      "transform": "cell_to_option_price",
      "derived": {"group_name": "Räder", "option_name": "19 Zoll", "is_multi": false},
      "review_required": true,
      "evidence": "variant-label header over numeric cells; the GROUP is stated nowhere in the sheet"
    }
  ],
  "unmapped_columns": [
    {"index": 8, "header": "Bemerkung intern", "reason": "Internal margin note — not customer-facing.", "suggestion": "Confirm with the tenant before discarding."}
  ],
  "blockers": [
    {"blocker_id": "missing-standard-variant", "pattern_id": "implicit-base-config", "message": "…", "placeholder": "…", "question": "…"}
  ],
  "warnings": [
    {"code": "low-confidence-mapping", "message": "…", "column_index": 5}
  ],
  "normalized_rows_path": "source/acme/normalized-rows.json"
}
```

### `normalized-rows.json` — a JSON array of flat objects, keyed by role id

This is the exact shape `detect_anti_patterns.py` already eats (a list of dicts) and the shape `rattle-suggest-config` reads.

```json
[
  {
    "record_type": "option",
    "product_name": "Widget Pro",
    "group_name": "Räder",
    "option_name": "19 Zoll",
    "option_price": "500.00",
    "recommended_flag": false,
    "_source_row": 1,
    "_source_column": "19 Zoll"
  },
  {
    "record_type": "option",
    "product_name": "Widget Pro",
    "group_name": "Räder",
    "option_name": "PLACEHOLDER-STANDARD-OPTION",
    "option_price": null,
    "recommended_flag": true,
    "_blocker_id": "missing-standard-variant"
  }
]
```

`record_type` is one of `product`, `option`, `bom_line`. The placeholder row carries `_blocker_id` and a `null` price — it is a hole with a label, never a guess.

## Handing off

```
rattle-ingest            raw file → source-mapping.json + normalized-rows.json   ← you are here
  └→ rattle-pricelist-analysis   normalized rows → anti-pattern findings
       └→ rattle-suggest-config  findings + rows → recommendation.json
            └→ rattle-apply-config   recommendation → idempotent ensure_* writes
```

- **Gate:** while `blockers[]` is non-empty, `rattle-suggest-config` MUST NOT run. Answer the blocking questions with the customer first, then re-ingest.
- **Feed `rattle-pricelist-analysis`** with `normalized-rows.json`: `python3 skills/rattle-pricelist-analysis/scripts/detect_anti_patterns.py normalized-rows.json`. Its `pattern_id`s and this skill's `blockers[].pattern_id`s index against the same catalogue (`rattle-configurator/references/anti-patterns.md`), so findings merge cleanly.
- **A `one-row-per-bom-line` sheet does not go to `rattle-suggest-config`.** It goes to `rattle-bom-builder` / `rattle-bom-architect`, which turn `parent_part_number` + `part_number` + `quantity` + `bom_factor` into `usage_subclauses` and `option_scalings`. A BOM cannot be built before the options exist — ingest the configuration sheet first.

## Bundled scripts

- `scripts/profile_source.py` — deterministic column profiler. `.xlsx` / `.xlsm` / `.csv` / `.json`. Emits JSON to stdout, progress to stderr. Runs without network, AI keys, or the `rattle_api` package; Excel needs `openpyxl` and degrades gracefully without it.

## Reference files

| File | Use when |
|---|---|
| `references/column-roles.md` | You need the full DE/EN keyword tables, value-shape signals, and confidence rules for a role |
| `references/sheet-shapes.md` | You need the worked example and normalization strategy for a shape — especially the wide-variant-matrix pivot |

## Related skills

- `rattle-configurator` — the #1 rule, the data model, the anti-pattern catalogue every blocker cites.
- `rattle-pricelist-analysis` — the next step; consumes `normalized-rows.json`.
- `rattle-suggest-config` — turns the normalized rows into a BOM-aware recommendation. Gated on `blockers[] == []`.
- `rattle-bom-builder` — the destination for `one-row-per-bom-line` sheets (`usage_subclauses`, `option_scalings`).
- `rattle-apply-config` — the only skill that writes to a live tenant. Ingestion never does.
- `rattle-tenant-memory` — tenant column conventions worth remembering between imports ("their 'VK' column is always net list price").
