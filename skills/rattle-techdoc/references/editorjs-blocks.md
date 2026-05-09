# EditorJS block reference for technical documentation

Every chapter/section content in a Rattle `doc_type=technical_documentation` template is stored as a `ContentBlockLocale.block_json` field — an array of EditorJS blocks. This reference documents every block type used in technical documentations, the JSON shape, validation rules, and rendering notes.

EditorJS reference: https://editorjs.io/. Rattle's frontend renderer is in `app/static/js/editor_tools.js` (rattleapp); the server-side HTML renderer is `app/utils/editorjs_html.py`.

> **Cardinal rule.** Block JSON is **append-only first-class** content. Never produce HTML inline; produce blocks. The renderer handles HTML escaping, accessibility, and PDF rendering uniformly.

---

## Standard blocks

### `paragraph`

Plain text with allowed inline markup (`<strong>`, `<em>`, `<u>`, `<s>`, `<code>`, `<mark>`, `<a>`, `<sub>`, `<sup>`, `<br>`, `<footnote>`).

```json
{
  "type": "paragraph",
  "data": {"text": "This is a paragraph with <strong>emphasis</strong> and a footnote<footnote>1</footnote>."}
}
```

Validation: `text` must be a string. Inline HTML is sanitised by `bleach` against the allowed set.

### `header`

Section heading. Avoid inside content blocks if a structure-block locale title already exists for that level.

```json
{
  "type": "header",
  "data": {"text": "Subsystem overview", "level": 3}
}
```

`level`: 2..6.

### `list`

Three styles: `unordered`, `ordered`, `checklist`.

```json
{
  "type": "list",
  "data": {
    "style": "unordered",
    "items": ["Read the manual.", "Inspect the workspace.", "Engage LOTO."]
  }
}
```

For numbered procedures (commissioning, fault-finding, maintenance) prefer `ordered`. For acceptance / handover protocols prefer `checklist`.

### `table`

Tabular data. ALWAYS set `withHeadings: true` for technical-documentation tables. The first row is then rendered as a header.

```json
{
  "type": "table",
  "data": {
    "withHeadings": true,
    "content": [
      ["Target group", "Typical tasks", "Required qualification"],
      ["Operator", "Switch on, normal operation", "Instruction by operator"],
      ["Setter", "Format change, parameter adjustments", "Vocational training"]
    ]
  }
}
```

Use a table for: target groups, residual hazards, validity, technical data, error codes, maintenance schedule, spare parts.

### `quote`

Used in seed data to carry "suggested wording" (Formulierungsvorschlag) callouts the redactor should rewrite. The `caption` distinguishes editorial/non-normative text from final content.

```json
{
  "type": "quote",
  "data": {
    "text": "Diese Betriebsanleitung enthält alle Informationen, …",
    "caption": "Formulierungsvorschlag",
    "alignment": "left"
  }
}
```

> Quote blocks should be replaced with concrete `paragraph` blocks before publication. The audit `unfinished-suggested-wording` flags them.

### `warning`

Editorial / non-safety-relevant note. **Do not use for hazard warnings** — those are `safety_notice`.

```json
{
  "type": "warning",
  "data": {
    "title": "Editorial note",
    "message": "This section needs the customer's serial-number range before publication."
  }
}
```

Common titles: *Editorial note* / *Redaktionshinweis*, *Mandatory* / *Pflichtangabe*. Both are editorial, not user-facing.

### `delimiter`

Visual separator. Empty `data`.

```json
{"type": "delimiter", "data": {}}
```

### `image`

Inline image. URLs must come from `/api/v1/documents/content-blocks/images` (POST upload) — never external URLs.

```json
{
  "type": "image",
  "data": {
    "file": {"url": "/uploads/cb-images/loto-tag-2026-05-09.png"},
    "caption": "LOTO tag — example",
    "withBorder": false,
    "withBackground": false,
    "stretched": false
  }
}
```

For safety symbols (ISO 7010, GHS), prefer the dedicated `safety_notice` / `hp_statement` blocks — they carry symbol code metadata and locale-aware signal words.

---

## Safety-specialist blocks

### `safety_notice`

ANSI Z535.6 / ISO 3864-2 hazard warning. **Single source of truth for every safety-relevant message.**

> **Validate before emitting.** Before writing a `safety_notice` block, call `GET /api/v1/safety-logos[?category=<cat>]` and pick the `isoSymbol.file` from the returned `categories[].files[].file` list — match by `description` / `description_de`. Call `GET /api/v1/safety-notices/signal-words?locale=<doc-locale>` to pre-fill `signalWord`. See `rattle-safety-notices/SKILL.md` for the full picker workflow and `rattle-api/references/api-reference.md` § Safety Reference for the endpoint contracts.

```json
{
  "type": "safety_notice",
  "data": {
    "level": "warning",
    "title": "Quetschgefahr durch bewegliche Maschinenteile",
    "hazard": "Schwere Verletzungen an Händen und Fingern möglich.",
    "consequences": ["Quetschungen", "Knochenbrüche"],
    "avoidance": [
      "Vor dem Eingriff Maschine stillsetzen.",
      "Gegen Wiedereinschalten sichern."
    ],
    "ref": "Kap. 9.4",
    "isoSymbol": {
      "category": "warning",
      "file": "W024_crushing_of_hands.svg"
    },
    "showAlertSymbol": true,
    "signalWord": "WARNUNG"
  }
}
```

Field reference:

| Field | Type | Required | Notes |
|---|---|---|---|
| `level` | `"danger"` / `"warning"` / `"caution"` / `"notice"` | yes | Drives colour + signal word. |
| `title` | string | yes | Short hazard label (one line). |
| `hazard` | string | yes | What the hazard is. |
| `consequences` | string[] | yes | What happens if ignored. |
| `avoidance` | string[] | yes | How to prevent it (imperative mood). |
| `ref` | string | optional | Cross-reference to chapter / section. |
| `isoSymbol.category` | enum | yes | `warning` / `prohibition` / `mandatory` / `safe_condition` / `fire_protection` / `gefahrstoffe`. |
| `isoSymbol.file` | string | yes | SVG filename, e.g. `W024_crushing_of_hands.svg`. See `rattle-safety-notices/references/iso-7010-symbols.md`. |
| `showAlertSymbol` | bool | optional | Render the `!` triangle. Always `true` for danger/warning/caution; `false` allowed for notice. |
| `signalWord` | string | optional | Locale-resolved signal word. If absent, the renderer uses the locale default for `level`. |

Audit checks `unstructured-warnings` and `addressless-pictogram` flag deviations.

### `hp_statement`

EU CLP Regulation EC 1272/2008 hazard / precautionary statement. **Statement text is normative and MUST NOT be hand-edited or AI-translated** — it is resolved server-side from the official locale tables.

> **Validate before emitting.** For every `code` in the block, call `GET /api/v1/hp-statements/<code>?locale=<doc-locale>`. A 200 confirms the code is valid and returns the locale-correct text + GHS pictogram. A 404 means the code is unknown — re-check the SDS. For combined codes use the joined key (`H300+H310`); for enhanced codes pass `slot_1` / `slot_2`. See `rattle-ghs-statements/SKILL.md` for the full workflow and `rattle-api/references/api-reference.md` § Safety Reference for the endpoint contracts.

```json
{
  "type": "hp_statement",
  "data": {
    "codes": ["H315"],
    "combinedKey": "",
    "isCombined": false,
    "enhancedSlots": {},
    "resolvedLocale": "de",
    "resolvedText": "Verursacht Hautreizungen."
  }
}
```

Combined statement (e.g. `H300+H310`):

```json
{
  "type": "hp_statement",
  "data": {
    "codes": ["H300", "H310"],
    "combinedKey": "H300+H310",
    "isCombined": true,
    "enhancedSlots": {},
    "resolvedLocale": "de",
    "resolvedText": "Lebensgefahr bei Verschlucken oder Hautkontakt."
  }
}
```

Enhanced statement with a slot (e.g. H340 with the placeholder for "route of exposure"):

```json
{
  "type": "hp_statement",
  "data": {
    "codes": ["H340"],
    "isCombined": false,
    "enhancedSlots": {"1": "beim Einatmen"},
    "resolvedLocale": "de",
    "resolvedText": "Kann genetische Defekte verursachen beim Einatmen."
  }
}
```

GHS pictograms are derived automatically from the H-code via `ghs_pictogram_map.json` (see `rattle-ghs-statements/references/ghs-mapping.md`). The renderer displays the pictogram at the start of the block.

---

## Block ordering rules

For a typical chapter/section content block, this is the canonical order:

1. `warning` (editorial / mandatory note) — visible only to the redactor pre-publication, hidden in PDF rendering by config.
2. `header` (subsection title) if needed.
3. `paragraph` (introduction).
4. `safety_notice` (one or more if the section is safety-relevant).
5. `list` or `table` (substance).
6. `image` (illustrations).
7. `hp_statement` (where chemicals are involved).
8. `quote` (suggested wording — replace before publish).
9. `delimiter` (between unrelated subsections, sparingly).

---

## Mandatory metadata for content blocks

Every `ContentBlockMaster` for a technical documentation should carry:

| Field | Recommended value |
|---|---|
| `key` | kebab-case, e.g. `pfm3200-cover` or `loto-procedure` |
| `title` | Human-readable, in the primary locale |
| `description` | One-line purpose |
| `tags` | List of normative refs + theme: `["iso-20607", "safety", "lifecycle:maintenance"]` |
| `directory_id` | A directory representing the chapter or theme (`docs/safety/`, `docs/maintenance/`) |
| `product_id` | `null` for shared blocks; product id for product-specific ones |
| `is_active` | `true` |

---

## Validation rules (server-side)

`app/utils/editorjs_html.py` and `app/schemas/v1/document_content.py` enforce:

- `block_json` ≤ a configured size (defaults to 5 MB serialised) per locale.
- Inline HTML in `paragraph.text` etc is sanitised against `_ALLOWED_TAGS` / `_ALLOWED_ATTRS`.
- Anchors with `target` attribute get `rel="noopener"` enforced.
- `safety_notice.isoSymbol.file` is constrained to filenames present in `app/static/img/safety_logos/<category>/`.
- `hp_statement.codes` are validated against the loaded H/P/EUH code set per locale.

When you hand-write a block, expect the API to reject anything that violates these rules. The `validate_recommendation.py` helper in `rattle-apply-config/scripts/` covers shape; for content-block specifics, add a second pass with the block size + symbol-existence check.
