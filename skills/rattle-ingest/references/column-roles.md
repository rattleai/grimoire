# Column roles — full detection reference

The 24 roles a source column can carry, with the German keywords, English keywords, value-shape signals, target Rattle entity/field, and confidence rules used to assign them. Mirror of the `ROLE_KEYWORDS` table in `../scripts/profile_source.py` — **when they conflict, this Markdown wins; update the script to match.**

## How a role is scored

A role is credible only when the **header** and the **values** agree. Neither alone is sufficient.

```
confidence = header_score + shape_score        (clamped to [0, 0.99])
```

### header_score

| Match | Score |
|---|---|
| Header equals the keyword exactly | **0.70** — an exact hit on a *specific* keyword must outrank a suffix hit on a generic one (`Vaterartikel` is a parent part, not a product) |
| Header starts or ends with the keyword | 0.50 |
| Keyword appears anywhere in the header | 0.42 |
| Keyword is short (≤ 4 chars, e.g. `me`, `min`, `step`, `vk`) | **0.55, token match only** — naive substring matching produces false friends: `Be`**`me`**`rkung` → `unit`, `Multi`**`step`**`-Modul` → `number_step`. Short keywords match a tokenised header (split on non-alphanumerics), never a substring. |
| No match | 0.00 |

### shape_score

Computed from the profiled values — `dtype`, `cardinality`, `distinct_ratio`, `non_null`, `samples`, numeric stats. Support adds; **contradiction subtracts**, so that a header hit with the wrong value shape scores *worse* than no header hit at all.

| Role family | Members | Support | Contradiction |
|---|---|---|---|
| Numeric | `option_price`, `base_price`, `quantity`, `bom_factor`, `number_min`, `number_max`, `number_step` | dtype `number`/`integer` → **+0.28**; dtype `mixed` → +0.08 | any other dtype → **−0.35** |
| Flag | `recommended_flag` | dtype `boolean` → **+0.32**; all values in the marker set → +0.28; ≤ 3 distinct strings → +0.10 | otherwise → −0.25 |
| Categorical | `area_name`, `group_name`, `unit`, `number_unit`, `currency`, `locale` | `distinct_ratio ≤ 0.35` → **+0.24**; cardinality ≤ 12 → +0.12 | numeric dtype → −0.30; too many distinct → −0.15 |
| Identifier | `product_sku`, `part_number` | `distinct_ratio ≥ 0.90` → **+0.26**; ≥ 0.60 → +0.10; every sample bears a digit → +0.06 | not unique → −0.20 |
| Text | `product_name`, `part_name` | dtype `string` and dense → +0.18 | any other dtype → −0.30 |

Role-specific bonuses:

| Signal | Effect |
|---|---|
| `option_price` and the column contains zero-priced rows | +0.05 — a zero price is the fingerprint of an explicit standard variant |
| `option_price` and the **header is a variant label** (`19 Zoll`, `HSK-63F mit Encoder`, `Multistep-Modul`) | **+0.30** — the wide-variant-matrix fingerprint. Deliberately calibrated to land *near* the 0.60 review floor: the option name is in the header, but the **group is stated nowhere in the sheet** and must come from a human. |
| `parent_part_number` with `0 < distinct_ratio < 1` | +0.16 — a parent-part column **repeats** (one parent, many children). That is what separates it from a product-identity column. |
| `currency` / `unit` / `number_unit` / `locale` whose samples all sit in the known token set | +0.30 |
| `image_ref` whose samples all match an image extension or an `http(s)://` URL | +0.34; otherwise −0.25 |
| `part_number` / `parent_part_number` with a numeric dtype | +0.06 — ERP part numbers are frequently pure digits; do not punish them for not being text |
| `description` with mean sample length ≥ 40 chars | +0.24 |

### Confidence rules

| Band | Meaning | Required action |
|---|---|---|
| `≥ 0.80` | Header and shape both strongly agree | Map it. Still list the samples for review. |
| `0.60 – 0.79` | Credible | Map it. |
| `< 0.60` | **Below the review floor** | Map it **and** set `review_required: true` **and** raise a `low-confidence-mapping` warning. |
| no candidate at all | Nothing scored | The column goes to `unmapped_columns[]` with a stated reason. **Never drop it silently.** |

Independent of confidence: **any mapping that invents structure the source does not state must set `review_required: true`.** The canonical case is a wide-matrix pivot, where `derived.group_name` is supplied by a human, not read from the file.

### Sheet-shape context

The shape disambiguates what a single column cannot. In a `one-row-per-bom-line` sheet, a generic name column (`Bezeichnung`) is `part.part_name`, not `product.name` — the profiler re-ranks it and records the signal `shape-context:one-row-per-bom-line`. The displaced role is kept as the runner-up so a reviewer can see what was overruled.

---

## The roles

### `product_name`

| | |
|---|---|
| **DE keywords** | Produkt, Artikel, Artikelbezeichnung, Bezeichnung, Modell, Maschine, Typ |
| **EN keywords** | product, item, model, machine |
| **Value shape** | `string`, dense. Near-unique in a product sheet; repeating in an option sheet (which is itself a shape signal). |
| **Target** | `product.name` (1–255 chars) |
| **Trap** | `Vaterartikel` ends with `artikel` and will collect a 0.50 suffix hit. The exact-match rule (0.70) plus the repeating-identifier bonus lets `parent_part_number` win. |

### `product_sku`

| | |
|---|---|
| **DE keywords** | Artikelnummer, Artikelnr, Art.-Nr, Sachnummer, Materialnummer, MatNr, ERP-ID |
| **EN keywords** | sku, item number, item no, article number, product code, erp id |
| **Value shape** | `distinct_ratio ≥ 0.90`, digit-bearing, short strings |
| **Target** | **`product.sku`** — the ERP article-number join key. |
| **Now available** | **`Product.sku` now exists** — `ProductCreateRequest` / `ProductUpdateRequest` accept it (`string ≤255`, unique per tenant → `409`, filter `GET /products?sku=`). Map the customer's article number to `product.sku`; use `integration_metadata.<key>` only for *secondary* identifiers. |

### `area_name`

| | |
|---|---|
| **DE keywords** | Bereich, Baugruppe, Sektion, Abschnitt, Zone, Modulgruppe |
| **EN keywords** | area, section, assembly, zone |
| **Value shape** | Low-cardinality text (a product has a handful of areas) |
| **Target** | `area.name` |
| **Note** | Rule `no-empty-areas`: an area with no groups is invalid. If the source names areas but no groups, that is a blocker, not a mapping. |

### `group_name`

| | |
|---|---|
| **DE keywords** | Gruppe, Optionsgruppe, Merkmal, Merkmalsgruppe, Kategorie, Ausstattungsgruppe |
| **EN keywords** | group, option group, feature, category, characteristic |
| **Value shape** | Low-cardinality text; repeats across the option rows it governs |
| **Target** | `group.name` |
| **Critical** | **`group.is_multi` is never in the data.** Single-select (one wheel size at a time) vs multi-select (stackable software modules) is a modelling decision. Default to `false`, mark `review_required`, and ask. |

### `option_name`

| | |
|---|---|
| **DE keywords** | Option, Variante, Ausführung, Ausstattung, Auswahl, Wert |
| **EN keywords** | variant, choice, value, trim |
| **Value shape** | Varied text (`distinct_ratio ≥ 0.30`); numeric dtype is a contradiction |
| **Target** | `option.name` |
| **Wide matrix** | In a `wide-variant-matrix` the option name is **the header itself**, not a cell. Transform `header_to_option_name`, and record it in `derived.option_name`. |

### `option_price`

| | |
|---|---|
| **DE keywords** | Aufpreis, Mehrpreis, Zuschlag, Aufschlag, Optionspreis |
| **EN keywords** | surcharge, option price, upcharge, add-on price, extra |
| **Value shape** | Numeric. Zero-priced rows are a *good* sign — they mark explicit standard variants. |
| **Target** | `option.price` — a **decimal string** (`OptionCreateRequest.price` defaults to `"0.00"`) |
| **Transform** | `decimal_de` (`"2.500,00 €"` → `"2500.00"`) or `decimal_en` (`"2,500.00"` → `"2500.00"`). Choose with the `currency` column and the DE/EN separator regexes — never guess; raise `decimal-separator-assumed` when you must. |
| **The #1 rule** | A surcharge column with **no zero-priced / standard sibling** is `implicit-base-config` (or `addon-only-options` / `addon-only-software-modules`). Emit a `missing-standard-variant` blocker with a placeholder. Never invent the standard. |

### `base_price`

| | |
|---|---|
| **DE keywords** | Grundpreis, Basispreis, Listenpreis, Nettopreis, Preis, VK, EK |
| **EN keywords** | base price, list price, net price, price, msrp |
| **Value shape** | Numeric, dense, **one per sheet**. Two `base_price` columns means one of them is something else (net vs gross, EK vs VK) — resolve with the user. |
| **Target** | `product.base_price` (decimal string; the API accepts string or number) |
| **Trap** | `Aufpreis` contains `preis`. The specific `option_price` keyword scores higher — but check the samples: a base-price column has no zeros. |

### `currency`

| | |
|---|---|
| **DE keywords** | Währung |
| **EN keywords** | currency, curr |
| **Value shape** | Cardinality 1–3; values in `{EUR, USD, CHF, GBP, €, $, £}` |
| **Target** | **`none`.** |
| **Critical** | `ProductCreateRequest.currency` is documented in the OpenAPI spec as *"Accepted but ignored — currency is derived from the company's base price list."* Writing it does nothing. Its only legitimate use in ingestion is **choosing the decimal parser**. Set `target_entity: "none"` and raise a `currency-not-writable` warning so nobody later believes the currency round-tripped. |

### `recommended_flag`

| | |
|---|---|
| **DE keywords** | Serie, serienmäßig, Serienausstattung, Standard, Grundausstattung, Basisausstattung, im Lieferumfang, Vorauswahl, empfohlen |
| **EN keywords** | default, included, recommended, std |
| **Value shape** | `boolean`, or markers: `x`, `✓`, `✔`, `•`, `ja`, `yes`, `S`, `Serie`, `inkl.` |
| **Target** | `option.recommended` |
| **Rule** | The recommended option in a single-select group is the standard variant and its `price` must be `0`. Exactly one `recommended=true` per single-select group (`rattle-apply-config` validates this). |
| **Note** | These keywords are *also* the `implicit-base-config` indicator list. A column named `Standard` holding prose (`"Standard 17-inch wheels"`) is not a flag — it is the anti-pattern itself. Check the dtype. |

### `quantity`

| | |
|---|---|
| **DE keywords** | Menge, Stück, Stk, Anzahl, Bedarf |
| **EN keywords** | quantity, qty, count, pieces, amount |
| **Value shape** | Numeric, usually small integers |
| **Target** | `bom_item.quantity` / `part_placement.quantity` (`> 0`, max 1e9). **The API rejects `quantity = 0` with 422** — a range-mode scaling line still needs `quantity: 1`. |

### `unit`

| | |
|---|---|
| **DE keywords** | Einheit, ME, Mengeneinheit |
| **EN keywords** | uom, unit, unit of measure |
| **Value shape** | Low cardinality; values in `{Stk, pcs, m, mm, cm, kg, g, l, m², h, Set, Paar, …}` |
| **Target** | `bom_item.uom` / `part_placement.uom` (max 16 chars, default `pcs`) |
| **Trap** | `ME` is 2 chars — token match only. Substring matching turns `Bemerkung` into a unit column. |

### `part_number`

| | |
|---|---|
| **DE keywords** | Teilenummer, Teile-Nr, Bauteilnummer, Komponentennummer |
| **EN keywords** | part number, part no, component number, child part |
| **Value shape** | Near-unique; often numeric |
| **Target** | `part.part_number` — **required**, 1–255 chars |
| **Rule** | Never invent a part number. A BOM line with no part number gets a `missing-part-number` blocker and a `pn:<slug>` placeholder, exactly as `rattle-suggest-config` step 4 prescribes. |

### `part_name`

| | |
|---|---|
| **DE keywords** | Benennung, Teilebezeichnung, Bauteilbezeichnung, Komponentenbezeichnung |
| **EN keywords** | part name, part description, component name, material description |
| **Value shape** | `string`, dense. **Or** a generic name column (`Bezeichnung`) in a sheet whose shape is `one-row-per-bom-line`. |
| **Target** | `part.part_name` — **required** by `PartCreateRequest` (1–255 chars). A part cannot be created without both `part_number` and `part_name`. |

### `parent_part_number`

| | |
|---|---|
| **DE keywords** | Vaterartikel, übergeordnet, Oberteil, Hauptbaugruppe, Elternteil |
| **EN keywords** | parent, parent part, assembly of, next assembly |
| **Value shape** | **Repeating** identifier — `0 < distinct_ratio < 1`. One parent, many children. |
| **Target** | `bom_item.parent_part_id`, resolved from the part number at apply time |
| **Note** | Its presence alongside `part_number` is the strongest signal for the `one-row-per-bom-line` shape. |

### `bom_factor`

| | |
|---|---|
| **DE keywords** | Faktor, Verwendungsfaktor, Multiplikator |
| **EN keywords** | factor, usage factor, multiplier, scaling |
| **Value shape** | Numeric, typically around 1.0 |
| **Target** | `usage_subclauses[].factor` in the recommendation contract (`{option_name, factor}`), or an `option_scalings` descriptor. |
| **See** | `rattle-bom-builder/references/usage-subclauses.md` and `option-scalings.md` — the factor is meaningless without the option it hangs off. |

### `number_min` / `number_max` / `number_step` / `number_unit`

| | |
|---|---|
| **DE keywords** | Min / Minimum / Untergrenze · Max / Maximum / Obergrenze · Schritt / Schrittweite / Raster · Eingabeeinheit / Zahleneinheit |
| **EN keywords** | min, lower · max, upper · step, increment · number unit, input unit |
| **Value shape** | Numeric (`number_unit`: a UoM token) |
| **Target** | `option.number_min` / `number_max` / `number_step` / `number_unit` |
| **Critical** | These four are only legal when **`option.is_numbered = true`**. `is_numbered` is a modelling decision that is never in the data — set it explicitly and mark `review_required`. `number_step ≥ 1`; `number_unit` max 32 chars. |
| **Trap** | `min`, `max`, `von`, `bis`, `step` are all ≤ 4 chars — token match only. |
| **Where they come from** | Usually nowhere. But a price expressed **per unit** — `Preis pro Meter`, `je Stück`, `Laufmeter`, `price per unit` — is the `per-unit-priced-row` anti-pattern, and it is the tell that the option must be **numbered**: `is_numbered=true`, `number_unit` from the unit in the header, and `price_scalings` / `option_scalings` carrying the per-unit rate. A per-unit price mapped as a flat `option.price` silently prices every configuration as if the customer ordered exactly one. Flag it, cite `per-unit-priced-row`, and hand the scaling design to `rattle-bom-builder`. |

### `constraint_exclusion`

| | |
|---|---|
| **DE keywords** | Ausschluss, nicht kombinierbar, unverträglich, Konflikt, sperrt |
| **EN keywords** | excludes, incompatible, conflict, forbidden, not with |
| **Value shape** | Free text, list-like (comma/semicolon separated) |
| **Target** | `forbidden` pairs — `POST /constraints`, body field **`forbidden`**: `{"product_id": <id>, "forbidden": [{"option_id1": <a>, "option_id2": <b>}]}` (atomic replace, `X-Constraints-Version` OCC). Conditional logic goes to `POST /constraints/rules` with `rule_json = {requires: [...], invalid: [...]}`. |
| **Transform** | `split_list`. The referenced option names must resolve against options that actually exist — otherwise it is a blocker, not a constraint. |

### `description`

| | |
|---|---|
| **DE keywords** | Beschreibung, Produktbeschreibung, Langtext, Bemerkung, Erläuterung |
| **EN keywords** | description, long text, remark, comment, notes |
| **Value shape** | Mean sample length ≥ 40 chars |
| **Target** | `product.description` / `option.description` / `group.description` / `area.description` — pick by the sheet shape. |
| **Anti-pattern** | Narrative prose in a *configuration* context is `description-area-smell`. It belongs in a document template (`doc_type=offer`, a "Product Overview" chapter with a static EditorJS content block) — **never** in an area with no groups. Flag it; do not model it as an area. |

### `image_ref`

| | |
|---|---|
| **DE keywords** | Bild, Bilddatei, Abbildung, Foto, Grafik |
| **EN keywords** | image, picture, photo, img, url |
| **Value shape** | Every sample matches `\.(png|jpe?g|webp|gif|svg)$` or `^https?://` |
| **Target** | Multipart upload: `POST /options/{optionId}/image` (and `/options/{optionId}/image/areas/{areaId}` for a per-area override), `POST /products/{productId}/image`, `POST /areas/{areaId}/image`. |
| **Part images** | `Part` images **now have an upload route**: `POST /parts/{partId}/image` (multipart), resolved to `image_url` on `PartResponse`. A part-image column can be mapped and uploaded once the part exists (spare-parts catalogues, exploded-view BOMs) — it no longer belongs in `unmapped_columns`. |

### `locale`

| | |
|---|---|
| **DE keywords** | Sprache, Sprachcode |
| **EN keywords** | language, locale, lang |
| **Value shape** | Matches `^[a-z]{2}([-_][A-Za-z]{2})?$` |
| **Target** | `language` on `product` / `area` / `group` / `option` (max 8 chars, default `"DE"`) |

### `ignore`

| | |
|---|---|
| **Looks like** | Internal margin, buyer initials, colour codes, "Auslauf 2027", empty columns |
| **Detection** | No role clears the floor, **or** a human reviewed it and decided it is not customer-facing |
| **Target** | Nothing |
| **Rule** | An ignored column still appears — either with role `ignore` or in `unmapped_columns[]` with a reason. The record that it was seen and rejected *is* the deliverable. |

---

## Fields that do not exist

Grep `docs/openapi.json` before naming any field. Some tempting names are still traps; two former gaps have since been filled — verify against the current spec:

| Tempting | Reality |
|---|---|
| `product.sku` | **Now exists** — first-class on `ProductCreateRequest` / `ProductUpdateRequest` (`string ≤255`, the ERP article-number join key; unique per tenant, duplicate → `409`; filter with `GET /products?sku=`). Map the ERP article number **here**, not to `integration_metadata`. |
| `product.currency` (writable) | Accepted but **ignored** — derived from the company base price list. |
| `part.part_img` | Surfaced as `image_url` on `PartResponse`, and there **is** now an upload route: `POST /parts/{partId}/image` (multipart). |
| `part.part_cost` (decimal) | **Integer**, `ge=0`. A `12,50` cost column must be rounded → raise `part-cost-rounded`. |
