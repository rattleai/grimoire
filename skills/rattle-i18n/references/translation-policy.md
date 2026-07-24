# Translation policy — the three buckets, field by field

**Read this before any translation.** `SKILL.md` states the three buckets. This file applies them to **every field of every EditorJS block type** Rattle uses. It is the operational core of `rattle-i18n`.

The block shapes here are the ones in `rattle-techdoc/references/editorjs-blocks.md`. When they conflict, that file wins — it is the source of truth for the block contract; this file is the source of truth for **what happens to each field when the locale changes.**

---

## The three buckets, restated as a decision

For every field, ask **one** question: *where does the correct target-language string come from?*

| The correct target string comes from… | Bucket | Action |
|---|---|---|
| …a translator, working from the source string. | **1 — AI-TRANSLATABLE** | Translate. Apply the glossary. Re-audit mood and terminology afterwards. |
| …**an official table**, keyed by a code the block already carries. | **2 — LOCALE-RESOLVED** | **Do not translate. Do not copy. Do not paraphrase.** Leave the field **empty** and let the renderer resolve it. If you must pre-fill, fetch it from the authority and match byte-for-byte. |
| …a decision the company already made and wrote down. | **3 — GLOSSARY-LOCKED** | Lock it in `/translations/dictionary`. Then **verify it survived** — the spec does not say the translator consults the dictionary (audit § P0-9g). |
| …nowhere, because it is not language. | **0 — NOT LANGUAGE** | **Never touch.** Codes, enums, filenames, URLs, booleans, numbers, levels. A code that looks like a word is still a code. |

**Bucket 0 is the one that gets forgotten.** `isoSymbol.file` is `W024_crushing_of_hands.svg` — it reads like English, it is a **filename**, and a translator that "helpfully" renders it as `W024_Quetschen_der_Haende.svg` produces a broken image and a `200 OK`.

---

## Standard blocks

### `paragraph`

```json
{"type": "paragraph", "data": {"text": "Prüfen Sie die Dichtung vor dem Wiedereinbau."}}
```

| Field | Bucket | Notes |
|---|---|---|
| `data.text` | **1 — translate** | The core case. |

**Inline markup must survive.** `text` may carry `<strong>`, `<em>`, `<u>`, `<s>`, `<code>`, `<mark>`, `<a>`, `<sub>`, `<sup>`, `<br>`, `<footnote>`. **The tags are bucket 0; the text between them is bucket 1.** A translator that drops, reorders or *translates* a tag name corrupts the block — the server sanitises against an allow-list, so an invented tag is silently stripped and the emphasis simply vanishes.

- `<code>` content is usually a **parameter name or an HMI label** — check whether it belongs in bucket 3 (locked) rather than bucket 1.
- `<a href>` is **bucket 0**. Never translate a URL.
- `<footnote>` markers are **bucket 0** — the number is a reference, not prose.

**Post-translation audit (`rattle-techdoc-language`):** an instruction that came back in the indicative is `mood:non-imperative-instruction`. **DeepL will not preserve the imperative reliably.** German *"Prüfen Sie die Dichtung"* → EN *"The seal should be checked"* is a correct translation and a **documentation defect**. Re-audit every instruction paragraph.

### `header`

```json
{"type": "header", "data": {"text": "Subsystem overview", "level": 3}}
```

| Field | Bucket | Notes |
|---|---|---|
| `data.text` | **1 — translate** | Apply the glossary: chapter headings are where locked terms are most visible. |
| `data.level` | **0 — never** | Integer 2–6. Structural. |

### `list`

```json
{"type": "list", "data": {"style": "ordered", "items": ["Maschine stillsetzen.", "Gegen Wiedereinschalten sichern."]}}
```

| Field | Bucket | Notes |
|---|---|---|
| `data.items[]` | **1 — translate** | Each item independently. **Item count must be preserved** — a translator that merges two steps into one sentence has deleted a procedure step. `rattle-techdoc-language`'s `unfinished-translation` audit flags target arrays shorter than source arrays; **that check exists because this happens.** |
| `data.style` | **0 — never** | Enum: `unordered` / `ordered` / `checklist`. **It is a word. It is not prose.** Translating `ordered` → `geordnet` breaks the renderer. |

**Ordered lists are procedures.** Every item must stay an **imperative** in the target language. See `paragraph` above.

### `table`

```json
{"type": "table", "data": {"withHeadings": true,
  "content": [["Bauteil", "Anzugsmoment", "Toleranz"], ["Spindelmutter", "45 Nm", "± 0,5 mm"]]}}
```

| Field | Bucket | Notes |
|---|---|---|
| `data.content[][]` | **mixed — 1, 3 and 0 in the same array** | **This is the most dangerous block in the document.** See below. |
| `data.withHeadings` | **0 — never** | Boolean. |

**A table cell is not automatically prose.** In one row you can have all four buckets:

| Cell | Bucket | Why |
|---|---|---|
| `"Anzugsmoment"` (a column header) | **1** | Prose → "Torque". |
| `"Spindelmutter"` (a part name) | **3 — LOCKED** | It is a part on the BOM. It must render exactly as the company decided, in every language, or the reader orders the wrong spare. |
| `"45 Nm"` | **0 — NEVER TOUCH** | A **value**. There is no target-language version of 45 Nm. |
| `"± 0,5 mm"` | **0 — NEVER TOUCH, and watch the separator** | `rattle-techdoc-language`: *"`± 0,5 mm` (DE) / `± 0.5 mm` (EN — note decimal separator)."* **Do not let a translator "convert" it.** DE `0,5` and EN `0.5` are the same number; DE `1.000` and EN `1,000` are **not** the same number, and a machine translator applying a thousands-separator convention to a decimal is a silent factor-of-1000 error in a torque value. |
| `"H315"` in a hazard table | **2 — RESOLVED** | If a code appears in a table, the table is the wrong container. **Use an `hp_statement` block** (`rattle-ghs-statements`: `inline-hp-text` is an audit finding). |

**Rule: before translating a table, classify it.** A *technical data* table (Chapter 13) is mostly bucket 0 with bucket-1 headers. A *target-group* table (Chapter 1) is mostly bucket 1. An *error-code* table (Chapter 8) is bucket 0 codes with bucket-1 descriptions. **Never hand a whole table to a translator as an opaque string grid.**

### `quote`

```json
{"type": "quote", "data": {"text": "Diese Betriebsanleitung enthält …", "caption": "Formulierungsvorschlag", "alignment": "left"}}
```

| Field | Bucket | Notes |
|---|---|---|
| `data.text` | **1 — translate**, but see below | |
| `data.caption` | **1 — editorial** | `"Formulierungsvorschlag"` is a **redactor marker**, not user content. |
| `data.alignment` | **0 — never** | Enum: `left` / `center` / `right`. |

> **A `quote` block should not exist at translation time.** It carries *suggested wording* that the redactor is supposed to replace with a real `paragraph` before publication (`rattle-techdoc`'s `unfinished-suggested-wording` audit). **Translating one propagates unfinished content into a second language.** **Resolve the quotes in the source, then translate.**

### `warning`

```json
{"type": "warning", "data": {"title": "Redaktionshinweis", "message": "Seriennummernbereich fehlt."}}
```

| Field | Bucket | Notes |
|---|---|---|
| `data.title` | **1 — editorial** | |
| `data.message` | **1 — editorial** | |

> **`warning` is NOT a safety block.** `rattle-techdoc`: *"Editorial / non-safety-relevant note. **Do not use for hazard warnings** — those are `safety_notice`."* A `warning` block carrying safety content is the `unstructured-warnings` audit finding.
>
> **Two consequences for translation.** (1) An editorial note is a message to *the redactor* — translating it is a waste and it should not reach publication anyway. (2) **If the block turns out to contain a real hazard, translating it is worse than a waste — you have now produced a safety message in two languages, in a block type that carries no signal word, no level and no pictogram, in neither of them.** **Convert it to a `safety_notice` in the source first** (`rattle-safety-notices` § "Workflow — converting 'Achtung!' to a `safety_notice`"), *then* translate.

### `delimiter`

```json
{"type": "delimiter", "data": {}}
```

**Nothing to translate.** `data` is empty. A translator that emits `{"data": {"text": ""}}` has changed the block shape; the block array must come back structurally identical.

### `image`

```json
{"type": "image", "data": {"file": {"url": "/uploads/cb-images/loto-tag.png"},
                           "caption": "LOTO-Anhänger — Beispiel",
                           "withBorder": false, "withBackground": false, "stretched": false}}
```

| Field | Bucket | Notes |
|---|---|---|
| `data.caption` | **1 — translate** | Apply the glossary — captions name parts. |
| `data.file.url` | **0 — NEVER** | **A translated URL is a 404.** |
| `data.withBorder` / `withBackground` / `stretched` | **0 — never** | Booleans. |

> **The image itself may need localising, and no API field expresses that.** A photo of a German-language HMI screen, or a diagram with baked-in German labels, is **still German after a perfect translation of its caption**. There is no `alt` field and no per-locale image in the block contract. **Flag localised-artwork needs to the human — this skill cannot fix them.** `rattle-techdoc-language` requires *accessible media (alt text …)* under the Clause 5 **accessible** attribute; the block does not provide the field.
>
> **`POST …/locales` "automatically cleans up orphaned EditorJS images on update".** Verbatim. So a locale update that drops an `image` block **deletes the underlying upload**. If two locales referenced the same image and one drops it, **what happens to the other is not documented.** Do not remove image blocks from a locale casually.

---

## Safety-specialist blocks — where the legal exposure is

### `safety_notice` — **mixed bucket. This is the block that must not be handed to a translator whole.**

```json
{"type": "safety_notice", "data": {
  "level": "warning",
  "title": "Quetschgefahr durch bewegliche Maschinenteile",
  "hazard": "Bewegliche Teile können Hände und Finger einklemmen.",
  "consequences": ["Schwere Quetschverletzungen", "Knochenbrüche"],
  "avoidance": ["Vor dem Eingriff Maschine stillsetzen.", "Gegen Wiedereinschalten sichern."],
  "ref": "Kap. 9.4",
  "isoSymbol": {"category": "warning", "file": "W024_crushing_of_hands.svg"},
  "showAlertSymbol": true,
  "signalWord": "WARNUNG"}}
```

| Field | Bucket | What it is, and what happens if you get it wrong |
|---|---|---|
| `level` | **0 — NEVER** | Enum `danger` / `warning` / `caution` / `notice`. **Drives the colour AND the signal word.** It reads like an English word; it is **the code the whole block hangs off**. Translate it and the renderer cannot resolve the signal word at all. |
| `signalWord` | **2 — LOCALE-RESOLVED. NEVER TRANSLATE.** | GEFAHR / WARNUNG / VORSICHT / HINWEIS ↔ DANGER / WARNING / CAUTION / NOTICE. Normative under **ISO 3864-2:2016** Annex B and **ANSI Z535.6-2011 (R2017)**. Resolved from `GET /api/v1/safety-notices/signal-words?locale=<target>` — **32 locales**. <br><br> **The failure is silent and it demotes the hazard.** French *AVERTISSEMENT* is WARNING; *ATTENTION* is CAUTION. A translator that renders `WARNUNG` as `ATTENTION` has moved the notice **down one rung of the ISO 3864-2 ladder** and produced a document that understates a hazard that can kill. It will read perfectly. <br><br> **Best practice: OMIT the field.** `rattle-safety-notices`, verbatim: *"Every `safety_notice` block can omit `signalWord` and the renderer resolves it from the document locale."* **A field that is not there cannot be mistranslated.** |
| `title` | **1 + 3** | Prose, **and it must still name BOTH the hazard type AND its source** after translation (the "A" of SAFE — *Art und Quelle*). "Quetschgefahr durch bewegliche Maschinenteile" → "Crushing hazard **from moving machine parts**", not "Crushing hazard". **A translator that shortens it has deleted the source of the hazard.** Lock the part names. |
| `hazard` | **1** | One sentence. Prose. |
| `consequences[]` | **1** | **Array length must be preserved.** Two consequences in, two out. |
| `avoidance[]` | **1 — and it must stay IMPERATIVE** | These are the instructions that keep the reader alive. `rattle-techdoc-language` mandates imperative mood (Sie-form in German). **DeepL routinely returns the indicative or the passive** — *"Die Maschine ist stillzusetzen"* / *"The machine should be stopped"*. **Re-audit every `avoidance` bullet after translation** (`mood:non-imperative-instruction`, `quality-violation:clarity:passive-instruction`). This is the single highest-value post-translation check in the document. |
| `ref` | **0/1 — structural** | `"Kap. 9.4"` → `"Sec. 9.4"`. **The prefix is bucket 1; the NUMBER is bucket 0.** A translator that renumbers a cross-reference has broken it. Verify the digits are unchanged. |
| `isoSymbol.category` | **0 — NEVER** | Enum: `warning` / `prohibition` / `mandatory` / `safe_condition` / `fire_protection` / `gefahrstoffe`. |
| `isoSymbol.file` | **0 — NEVER. It is a FILENAME.** | `W024_crushing_of_hands.svg`. **Translate it and the pictogram 404s** — you have removed the ISO 7010 symbol from a safety notice and left a broken-image icon in a CE-marked manual. Verify byte-for-byte after any translation. |
| `showAlertSymbol` | **0 — never** | Boolean. |

**The whole point:** a `safety_notice` is **not** a prose block. It is a **code-bearing** block with prose fields inside it. **Translate the prose fields. Leave the codes. Resolve the signal word.**

### `hp_statement` — **almost entirely bucket 0 and 2. There is essentially nothing here for a translator to do.**

```json
{"type": "hp_statement", "data": {
  "codes": ["H315"], "combinedKey": "", "isCombined": false, "enhancedSlots": {},
  "resolvedLocale": "de", "resolvedText": "Verursacht Hautreizungen."}}
```

| Field | Bucket | What it is, and what happens if you get it wrong |
|---|---|---|
| `codes[]` | **0 — NEVER** | `H315`, `P264`, `EUH014`. Regulatory identifiers under **CLP (EC) No 1272/2008**, Annex III (H) / IV (P) / VI. |
| `combinedKey` | **0 — NEVER** | `"H300+H310"`. A lookup key. |
| `isCombined` | **0 — never** | Boolean. |
| `enhancedSlots` | **special — see below** | e.g. `{"1": "beim Einatmen"}`. The **value** is prose in a **regulated frame**. |
| `resolvedLocale` | **0 — NEVER** | A locale tag (`"de"`). It changes because the *locale* changed, not because anything was translated. |
| `resolvedText` | **2 — LOCALE-RESOLVED. NEVER TRANSLATE. NEVER HAND-EDIT.** | **This is the field that makes machine translation a legal problem.** See below. |

> ### `resolvedText` is the one that ends up in front of a regulator
>
> The text of H315 in German is **not** "whatever DeepL produces from *Causes skin irritation*". It is **"Verursacht Hautreizungen."** — the exact string in the German annex of the CLP Regulation, published by ECHA on EUR-Lex. It is the same regulated sentence that appears on the substance's own label.
>
> **A machine translation of it is not a translation of the statement. It is a different statement.** It will be fluent, plausible, and legally wrong — and because it is fluent and plausible, **it survives review.** `rattle-ghs-statements`, verbatim: *"Statement text is not user-editable and MUST NOT be AI-translated"* and *"**Cardinal rule.** Never hand-edit `resolvedText`."*
>
> **The correct value of `resolvedText` in every locale is `""`.** Leave it empty. The renderer resolves it from `codes[]` via the official table. **If** you pre-cache it — and there is rarely a reason to — fetch it from `GET /api/v1/hp-statements/<code>?locale=<target>` and match it **byte-for-byte**. `rattle-ghs-statements`: *"if you pre-cache, the value MUST match the official text byte-for-byte."*

**`enhancedSlots` — the one genuinely ambiguous field in this block.**

A slot fills a `{1}` placeholder in an official statement: `H340` = *"May cause genetic defects {1}"*, with `{"1": "beim Einatmen"}` producing *"Kann genetische Defekte verursachen beim Einatmen."*

- The **slot value is prose**, so it *looks* like bucket 1.
- **But the sentence it lands in is regulated**, and the phrasing of the route of exposure is itself CLP vocabulary. A DeepL rendering of *"beim Einatmen"* may not be the phrasing CLP uses in the target language.
- **Do not machine-translate a slot value. Re-derive it** from the **target-locale** safety data sheet (SDS Section 2.2), which is where the source value came from. If no target-locale SDS is available, **escalate to a human** — do not guess.
- If the slot value is unavoidably machine-translated, **flag it in `unknowns` and require human review.** It is the one place in this block where an automated pipeline cannot be made safe by construction.

---

## Structure-block titles

Not an EditorJS block — a chapter/section **title**, stored per-language.

```
PUT /api/v1/documents/templates/{id}/structure/blocks/{block_id}/locales/{localeId}
StructureBlockLocaleUpsertRequest: {"title": "1. Einführung"}    (required, 1–500 chars)
```

The `{localeId}` segment is named misleadingly: it is a **language code** (e.g. `DE`), uppercased server-side — not an integer locale id. Only the content-block route (`…/content-blocks/{id}/locales/{localeId}`) keys on an integer.

| Field | Bucket | Notes |
|---|---|---|
| `title` | **1 + 3** | Prose. **Apply the glossary — chapter titles are where terminology drift is most visible to the reader.** |

**Two things to know:**

1. **The body is `{title}` and nothing else.** A structure-block locale carries no content, no blocks, no metadata.
2. **`StructureBlockLocaleResponse` has `source_content_hash` and NO `is_stale`.** (`ContentBlockLocaleResponse` has both.) **You cannot ask whether a translated chapter title is stale**, and the hash algorithm is undocumented so you cannot recompute it. Fall back to comparing `updated_at` on the source. See `SKILL.md` § "Staleness". *(Not yet in `docs/API_AUDIT.md` — report it.)*
3. `PUT` and `DELETE` on this path declare a **`403`** that the content-block locale operations do not. The condition that produces it is not documented.

---

## The pre-flight checklist

Run this **before** any translation of a technical documentation. It takes minutes and it is the difference between a translation and a recall.

1. **Inventory the blocks.** How many `safety_notice`? How many `hp_statement`? **If zero: the bulk template translate is safe — use it.**
2. **Resolve the `quote` blocks.** Suggested wording must become real content in the **source** before it is propagated.
3. **Convert stray `warning` blocks** that carry real hazards into `safety_notice` blocks — **in the source.**
4. **Harden the source. This is the step that makes everything else safe:**
   - **Omit `signalWord`** on every `safety_notice`.
   - **Set `resolvedText: ""`** on every `hp_statement`.
   - **A regulated string that is not in the document cannot be mistranslated.** After this step, the only regulated data in the document is **codes**, and codes are not prose.
5. **Lock the terms.** Part names, brand terms, product names → `/translations/dictionary`. **Then verify one of them survives a translation** (audit § P0-9g — the spec does not say the translator consults the dictionary).
6. **Clone, translate the clone, diff.** For every `safety_notice`: `level`, `isoSymbol.category`, `isoSymbol.file`, `signalWord`. For every `hp_statement`: `codes[]`, `combinedKey`, `resolvedLocale`, `resolvedText`. **Byte-identical, or empty.** Anything else is a stop.
7. **Verify against the authorities**, not against the source: `GET /safety-notices/signal-words?locale=<target>`, `GET /hp-statements/<code>?locale=<target>`.
8. **Re-audit the language.** Imperative mood on every `avoidance[]` bullet and every procedure step. Array lengths preserved. Cross-reference numbers unchanged. Decimal separators not "converted".
9. **Re-label the cover.** *"Übersetzung der Originalbetriebsanleitung"*. MRL §1.7.4.1. **The translator will not do this for you — it will translate the words "Originalbetriebsanleitung" and produce a false claim.**
10. **Check `is_stale` on every target locale before you ship** — structure-block titles included: `StructureBlockLocaleResponse` now carries `is_stale` and `source_content_hash`.

---

## Summary table — every block, one line

| Block | Bucket 1 (translate) | Bucket 2 (resolve — NEVER translate) | Bucket 0 (never touch) |
|---|---|---|---|
| `paragraph` | `text` (inline tags survive) | — | tag names, `href`, `<footnote>` markers |
| `header` | `text` | — | `level` |
| `list` | `items[]` (**preserve count**) | — | `style` |
| `table` | prose cells, headers | codes in cells → move to `hp_statement` | `withHeadings`, **values, units, tolerances, separators** |
| `quote` | `text`, `caption` | — | `alignment` — **but resolve the block before translating** |
| `warning` | `title`, `message` (editorial) | — | — **but convert real hazards to `safety_notice` first** |
| `delimiter` | — | — | everything (`data` is `{}`) |
| `image` | `caption` | — | `file.url`, booleans — **and the artwork itself may need localising** |
| **`safety_notice`** | `title`, `hazard`, `consequences[]`, `avoidance[]` (**imperative!**), `ref` prefix | **`signalWord`** — ISO 3864-2 / ANSI Z535.6, 32 locales. **Best: omit it.** | **`level`**, `isoSymbol.category`, **`isoSymbol.file`**, `showAlertSymbol`, `ref` **number** |
| **`hp_statement`** | `enhancedSlots` values — **re-derive from the target SDS, do not machine-translate** | **`resolvedText`** — CLP (EC) 1272/2008, 24 locales. **Best: `""`.** | **`codes[]`**, `combinedKey`, `isCombined`, `resolvedLocale` |
| structure title | `title` | — | — |
