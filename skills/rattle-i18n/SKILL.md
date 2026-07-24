---
name: rattle-i18n
description: Use this skill whenever a Rattle string has to exist in a second language — translate, translation, Übersetzung, i18n, localisation, localization, Lokalisierung, language, Sprache, locale, glossary, Glossar, terminology, Terminologie, dictionary, Wörterbuch, DeepL, multilingual, mehrsprachig, Originalbetriebsanleitung. Covers the 25 language / translation / dictionary / block-locale operations. Leads with the classification that IS the job — every string is either AI-translatable prose, LOCALE-RESOLVED regulated text (signal words, CLP H/P/EUH statements — DeepL-translating those is a legal defect in a CE-marked document, not a typo), or GLOSSARY-LOCKED terminology. Carries the traps — the bulk DeepL template translate rewrites every attached content locale in one call and the spec never says what it does to safety_notice / hp_statement blocks, PATCH on a dictionary entry REPLACES the translation map rather than merging it, and is_stale exists on content locales but not on structure-block titles.
license: MIT
---

# Rattle i18n — translate, resolve, or lock

`rattle-techdoc` decides **what the document says**. `rattle-techdoc-language` decides **how it says it**. This skill decides **what happens to each string when the document has to say it in a second language** — and the answer is not "translate it", for a large and legally significant fraction of them.

**25 operations across four resource families**: languages (7), translations (2), the translation dictionary (6), block locales (9, incl. the two `translate` actions). Scopes: `products:read` / `products:write` for languages and the dictionary; `documents:write` covers *"clone, translate, publish"*.

Rattle ships a **DeepL-backed machine translator** and, separately, a **glossary** that is supposed to constrain it. The translator is documented. The glossary is not — and **whether the DeepL pass consults it at all is not stated anywhere in the spec** (audit § **P0-9g**, whose own requested fix is *"state whether the DeepL pass actually consults it"*). Read § "The glossary lock" before you assume a locked term is safe.

## When to use this skill

- The user says translate, translation, Übersetzung, i18n, localisation, Lokalisierung, Sprache, locale, glossary, Glossar, Terminologie, Wörterbuch, DeepL, mehrsprachig, Originalbetriebsanleitung.
- A technical documentation, offer template or product catalogue must ship in a second language.
- A brand term, part name or regulated abbreviation is coming back translated when it must not be ("Spindel" → "spindle").
- A translated document must be checked for **staleness** before it ships.
- A customer's offer must render in the customer's language.
- Somebody is about to run `POST /documents/templates/{id}/translate` on a document that contains safety notices. **That is the dangerous one. Go to § "The bulk template translate".**

**Do not use this skill to pick the signal word for a safety notice** — that is `rattle-safety-notices`, and it is *resolved*, not translated. **Do not use it to translate a CLP hazard statement** — that is `rattle-ghs-statements`, and doing so is a regulatory defect. Both are § "What must NEVER be AI-translated".

## Three buckets: translate, resolve, or lock

**Every string in a Rattle document falls into exactly one of three buckets. Treating one bucket as another is the entire failure mode of this domain.**

| | Bucket | What it is | Mechanism | What goes wrong if you mistake it for another bucket |
|---|---|---|---|---|
| **1** | **AI-TRANSLATABLE** | Free prose. Chapter bodies, product and option descriptions, table cells, image captions, and the `title` / `hazard` / `consequences` / `avoidance` free text **inside** a safety notice. | `POST …/locales/{locale_id}/translate` (DeepL), or author the target locale directly. Apply the glossary. | Treated as *locked*: the manual ships half in German. Treated as *resolved*: nothing resolves it, and the target locale is empty. |
| **2** | **LOCALE-RESOLVED — NEVER TRANSLATE** | **Regulated text that comes from an official table**, resolved by the renderer **from a code**. Signal words (GEFAHR / WARNUNG / VORSICHT / HINWEIS ↔ DANGER / WARNING / CAUTION / NOTICE) — `GET /safety-notices/signal-words`, **32 locales**, per ISO 3864-2 / ANSI Z535.6. CLP **H / P / EUH statement text** — `GET /hp-statements`, **24 locales**, regulated by **(EC) 1272/2008**, ECHA-traceable to Annex III/IV/VI on EUR-Lex. | **A code, not a string.** Carry `level` + `codes[]`; leave `signalWord` and `resolvedText` **empty** and let the renderer resolve them per locale. | **Translated: a legal defect in a CE-marked document.** The correct German for H301 is not what DeepL says — it is the exact string in the CLP regulation's German annex. A plausible paraphrase is *worse* than an obvious error, because it passes review. |
| **3** | **GLOSSARY-LOCKED** | Brand terms, part names, product names, regulated abbreviations. Terms that must translate exactly one way — **or not at all**. | `/translations/dictionary` — `{base_term, {lang: translation}}`, company-wide. | Translated freely: "Spindel" becomes "spindle" in one chapter and "mandrel" in the next — an **IEC/IEEE 82079-1 Clause 5 *consistency*** defect (`rattle-techdoc-language`), and the audit's `terminology-drift`. |

**The discipline in one line:** *prose gets translated, codes get resolved, terms get locked.* Before you send anything to DeepL, know which bucket every field in it is in. The field-by-field classification, per EditorJS block type, is **`references/translation-policy.md`** — that is the operational core of this skill and you should have it open while you work.

## What must NEVER be AI-translated

Two things. Both are regulated. Both are already correct, in every locale Rattle ships, **before you touch them** — because they are resolved from a code.

### Signal words — `safety_notice.signalWord`

Normative under **ISO 3864-2:2016** Annex B and **ANSI Z535.6-2011 (R2017)**. Rattle ships them for **32 locales**. The `safety_notice` block carries `level` (`danger` / `warning` / `caution` / `notice`) — **a code** — and the renderer resolves the word.

> `rattle-safety-notices`, verbatim: *"Every `safety_notice` block can **omit** `signalWord` and the renderer resolves it from the document locale."*

**Therefore the safest source locale is one where `signalWord` is absent.** There is then no signal word for a translator to damage. If you must pre-fill it, resolve it: `GET /api/v1/safety-notices/signal-words?locale=<target>`. **Never let a translator produce it.** DeepL rendering `WARNUNG` as `ATTENTION` (a *CAUTION*-level word in French, not a *WARNING*) silently demotes the hazard by one rung of the ISO 3864-2 ladder.

### CLP statement text — `hp_statement.resolvedText`

Normative under **CLP Regulation (EC) No 1272/2008**, Annex III (H), Annex IV (P), Annex VI. Rattle ships **24 EU locales**. The block carries `codes[]` — **codes**, not sentences — and the renderer resolves the official text.

> `rattle-ghs-statements`, verbatim: *"Statement text is **not user-editable and MUST NOT be AI-translated**: it is regulated, locale-resolved from the CLP Regulation tables."* And: *"**Cardinal rule.** Never hand-edit `resolvedText`. If the renderer does not yet know the locale, leave it empty."*

**DeepL-translating a CLP hazard statement is a legal defect in a CE-marked document, not a typo.** The statement text on a machine's documentation is the same regulated string that appears on the substance's label; a paraphrase is not a translation of it, it is a *different statement*. **Leave `resolvedText` empty in every locale** and let the server resolve it. If you pre-cache it, it must match the ECHA / EUR-Lex text **byte-for-byte** — verify with `GET /api/v1/hp-statements/<code>?locale=<target>`.

**Also in bucket 2, and easy to miss:** `isoSymbol.file` (`W024_crushing_of_hands.svg` — a **filename**; translate it and the image 404s), `isoSymbol.category`, `level`, `codes[]`, `combinedKey`, `resolvedLocale`, `list.style`, `image.file.url`. **A code that looks like a word is still a code.**

## The bulk template translate — and what we could not verify

```
POST /api/v1/documents/templates/{id}/translate     → 200   (NOT 201)
  TemplateTranslateRequest: required target_language (2–10), optional source_language
```

> Verbatim: *"Translate **all** structure block titles and attached content block locales to the target language **via DeepL**. Creates or updates locale rows for each block. Sets `source_content_hash` on content locales for staleness tracking. Returns counts of translated titles and content locales."*

**This is a one-call rewrite of an entire multilingual document.** It is genuinely useful and it is the single most dangerous operation in this skill, for one reason:

> ### It says "**all** … attached content block locales". It does not say what it does to a `safety_notice` or an `hp_statement` block.

**We could not determine this from the spec, and we will not guess.**

- **The likely behaviour** is that it is harmless: those blocks carry **codes** (`level`, `codes[]`, `isoSymbol.file`), the renderer resolves the regulated text from the codes, and a DeepL pass over the block's *prose* fields would leave the codes alone. That is what the architecture implies.
- **It is an inference, not a fact.** Nothing in `docs/openapi.json` states which fields of an EditorJS block the translator visits. `blocks` is typed `items: {additionalProperties: true}` — **an untyped object array**. The spec does not know what a `safety_notice` is, so it cannot tell you what the translator does to one.
- **And "harmless" has a failure mode even if the codes survive**: if the source locale has a **pre-filled** `signalWord` or `resolvedText`, those are plain strings sitting in the block, and a translator that walks string fields has no way to know they are regulated.

**This repo has already shipped exactly this class of error once.** `expand=areas.groups.options` went into a skill because it *seemed* right and the spec did not contradict it. **It had never worked** — it is a `400` (audit § **P1-7**). The audit's conclusion is the rule here: *"an undocumented feature and a hallucinated feature are indistinguishable from the outside."*

**So, operationally:**

1. **Before the bulk translate, inventory the blocks.** If the template contains **no** `safety_notice` and **no** `hp_statement` blocks, the bulk translate is fine — use it.
2. **If it contains either, do not run it on the live template.** **Clone the template, translate the copy, and diff the regulated fields.** For every `safety_notice`: `level`, `isoSymbol.category`, `isoSymbol.file`, `signalWord`. For every `hp_statement`: `codes[]`, `combinedKey`, `resolvedLocale`, `resolvedText`. **Every one of them must be byte-identical to the source, or empty.**
3. **Verify the resolved output against the authorities**, not against the source: the target-locale signal word from `GET /safety-notices/signal-words?locale=<target>`, the target-locale statement text from `GET /hp-statements/<code>?locale=<target>`. `rattle-safety-notices` and `rattle-ghs-statements` are what *correct* looks like.
4. **Harden the source first — this is the cheap fix and it makes the question moot.** **Blank the resolved fields in the source locale**: omit `signalWord`, set `resolvedText: ""`. Both siblings say the renderer resolves them from the code. **A regulated string that is not in the document cannot be mistranslated.** Do this once and the bulk translate is safe by construction, whatever it does internally.
5. **Report what you observed.** If you verify the behaviour on a copy, that is a **measurement in one tenant on one release** — record it as such (`rattle-tenant-memory`, with provenance and date). It is not a contract, and Rattle may change it.

**The response tells you counts, not identities.**

```json
{"data": {"template_id": 20, "target_language": "FR",
          "translated_titles": 15, "translated_content_locales": 42}}
```

**No ids. No list of what it touched. No list of what it skipped.** You cannot tell from the response *which* 42 locales were written, so **you cannot diff from the response** — you must re-`GET` the blocks. And **both** translate operations declare a **`504`** (only three operations in the whole spec do). **A timeout on a bulk translate leaves the document partially translated, and the response that would have told you how far it got is the one you did not receive.** Re-`GET` and reconcile; never blind-retry.

## The glossary lock — `/translations/dictionary`

The mechanism that is supposed to stop "Spindel" becoming "spindle" when the brand demands "Spindel".

```jsonc
// POST /api/v1/translations/dictionary   → 201
// summary: "Create or update a dictionary entry"    description: null
// schema: INLINE, unnamed, no additionalProperties: false
{ "properties": { "base_term":    {"type": "string"},
                  "translations": {"type": "object", "additionalProperties": {"type": "string"}} },
  "required": ["base_term", "translations"] }
```

An entry is `{base_term, {lang: translation}}`. It is **company-wide** — not per-product, not per-template, not per-document. `GET /translations/dictionary` — *"Returns company-wide translation dictionary entries."* — **takes no query parameters at all. Not filterable. Not paginated.** You read the whole thing or nothing.

**That is the entire published definition of the feature.** No named schema, no field descriptions, no statement of what it is *for*.

> ### The unknown that matters most: **it is not documented that the DeepL pass consults the dictionary.**
>
> Audit § **P0-9g** — *"The glossary lock is invisible — and it is the only thing standing between DeepL and your brand terminology"* — lists among its requested fixes: *"**state whether the DeepL pass actually consults it**."* **That question is open.** A dictionary entry is a `201` and a row; **that it constrains `POST …/translate` is an assumption, and this skill does not make it.**
>
> **Therefore: never treat a locked term as protected until you have seen it survive a translation in that tenant.** Write the entry, translate a throwaway block containing the term, and **read the term back.** If it was rendered anyway, the lock is not wired to the translator, and the only remaining protection is human review — say so, plainly, rather than shipping a manual on the strength of a lock that does nothing.

### The trap that eats a whole language

> **`PATCH` does not merge the `translations` map. It replaces it.**

Verbatim from the spec — and this is one of the few things in this surface that *is* documented, so there is no excuse for getting it wrong:

- `PUT /translations/dictionary/{entry_id}` — *"a supplied `translations` map **fully replaces** the existing one."*
- `PATCH /translations/dictionary/{entry_id}` — *"**Same semantics as PUT** — a supplied `translations` map **replaces (does not merge)**."*

```json
// entry 7: {"base_term": "Spindel", "translations": {"EN": "Spindel", "FR": "Spindel", "IT": "Spindel"}}

PATCH /api/v1/translations/dictionary/7
{"translations": {"ES": "Spindel"}}

// entry 7 is now: {"base_term": "Spindel", "translations": {"ES": "Spindel"}}
// EN, FR and IT are GONE.  200 OK.
```

**`PATCH` is the verb that means "partial update" everywhere else in this API, and here it destroys every language you did not name.** To add one language: **`GET` the entry, merge locally, send the complete map.** Always. There is no partial write to a dictionary entry.

### The rest of the contract

| Fact | Consequence |
|---|---|
| `POST` declares **`201` only** — no `409`, no `200` — while its summary says *"Create **or update**"*. `PUT`/`PATCH` **do** declare `409`. | The `409`s imply `base_term` is **unique**. The `POST`'s upsert-by-`base_term` behaviour is stated only in a summary. **Read the dictionary first and decide `POST` vs `PATCH` yourself** rather than relying on the upsert. |
| `base_term` has **`maxLength: 255` on `PUT`/`PATCH` and no `maxLength` at all on `POST`.** | Asymmetric validation in one resource family. A `base_term` you can create, you may not be able to update. |
| **No body sets `additionalProperties: false`** — not `POST`, not `PUT`, not `PATCH`, not `PUT /translations`. `additionalProperties` is `false` on **116 of 124** request schemas (audit § **P0-10**). | **A typo'd field is swallowed with a `2xx`.** You have learned from the other 116 schemas that a bad field errors. **That lesson is wrong exactly here.** `GET` after every write and **diff what you sent against what came back.** |
| `DELETE /translations/dictionary/{entry_id}` — *"Idempotent — returns `204` even if the entry does not exist."* | Genuinely good, and rare. A `204` is **not** evidence that anything was deleted. |

**What belongs in the dictionary, what does not, and the full mechanism: `references/glossary.md`.**

## Staleness — `is_stale` and `source_content_hash`

**Credit where it is due: this is a genuinely good design, and most systems do not have it.** The audit says so in its own "what is right" section: *"Translation staleness is properly designed … exactly the right primitive for keeping a multilingual manual honest."*

`POST …/locales/{locale_id}/translate` writes a **`source_content_hash`** onto the target locale. If the **source** content changes afterwards, the target's **`is_stale`** flips to `true`.

> **This is the difference between a multilingual manual and a manual with a lie in it.** A source chapter edited after translation leaves every downstream locale silently describing the old machine. `is_stale` is how you find out.

**Therefore: check `is_stale` on every target locale before you ship a document. Every time.** Not as an optimisation — as a release gate. `ContentBlockLocaleResponse` carries both fields, and the content-block `translate` returns that response, so you can read the flag back from the call that set it.

**And the asymmetry you must not walk into:**

> ### `StructureBlockLocaleResponse` carries `source_content_hash` — and **has no `is_stale` field at all.**

Verified against `docs/openapi.json`: `ContentBlockLocaleResponse` declares `is_stale` (bool, default `false`) **and** `source_content_hash`. `StructureBlockLocaleResponse` declares `source_content_hash` **and nothing else about staleness**.

**Consequence: you cannot ask whether a translated chapter *title* is stale.** The hash is there, but **the algorithm that produces it is not documented**, so you cannot recompute it and compare. A source title edited after translation leaves a stale translated title **with no flag, and no way to derive one.** *(This asymmetry is **not yet in `docs/API_AUDIT.md` — report it.**)*

Until it is fixed: **treat every structure-block title in a target language as stale whenever its source title's `updated_at` is newer**, and re-run the title upsert. It is coarse; it is the only mechanism available.

`ContentBlockResponse.locales` is typed `items: {additionalProperties: true}` — **an untyped array**, so `is_stale` is not declared on the *expanded* locale list either. **Read the locale rows from `GET /documents/content-blocks/{id}/locales`, which returns the typed response.**

## The original-language obligation

**MRL 2006/42/EC §1.7.4.1** (and the MVO 2023/1230 equivalent). This is not a formatting preference; it is what makes the document lawful.

> *The "Original instructions" designation must appear on the language version verified by the manufacturer. Every other language version must bear the words "Translation of the original instructions".*

**Every translation you produce creates an obligation on the document it produces:**

1. The source document — the one the manufacturer **verified** — is the **"Originalbetriebsanleitung"** / *"Original Operating Instructions"*, and must say so on its cover.
2. **Every locale produced by `POST …/translate` is a translation**, and its cover must say **"Übersetzung der Originalbetriebsanleitung"** / *"Translation of the original instructions"*.
3. The original locale is recorded in `sec-12-3-doc-status` (*"Sprache der Originalbetriebsanleitung: Deutsch"*).
4. **The cover is a content block like any other. The bulk translate will translate it — it will not re-label it.** A DeepL pass turns "Originalbetriebsanleitung" into "Original operating instructions" — **which is now a false claim**, because that locale was not verified by the manufacturer. **After every translation, fix the cover.** `rattle-techdoc-language` § "Original-language obligation": *"never just clone the cover from the source locale."*

Choose the source locale accordingly: it should be **the manufacturer's verification language**. Everything else follows from it.

## Traps

Every one of these returns a `2xx`.

| # | Trap | Consequence |
|---|---|---|
| **P0-9g** | **The glossary lock may not be wired to the translator.** The spec never says the DeepL pass consults `/translations/dictionary`. | **A locked term is not protected until you have watched it survive a translation in that tenant.** Verify; do not assume. |
| **P0-9h** | **`entity_type` and `field` on `PUT /translations` are free strings with no enum.** *"`entity_type: "prodcut"` (typo) and `field: "nmae"` are both schema-valid."* | **Which entities are translatable is undiscoverable.** The spec's own *example* row is `{"entity_type": "area", "field": "name", "language": "DE", "value": "Rahmenmaterial"}` — **that is an example, not a vocabulary.** **Read what the tenant already uses** (`GET /translations`, collect the distinct `entity_type` / `field` pairs) and **if the one you need is absent, ASK.** Never invent one — a typo is a `200 OK` and a translation nobody will ever read. |
| **—** | **`PATCH` on a dictionary entry REPLACES the translation map.** Documented, and still the easiest way to destroy a language. | **`GET`, merge locally, send the complete map.** See § above. |
| **—** | **A content-block locale's natural key is `(language, version)` — and `TranslateRequest` has no `version` field.** *"If a locale with the same language **and version** already exists, it is updated (upsert)."* | **Which `version` the translator writes to is not documented.** If a block has locales at more than one `version`, **what `POST …/translate` targets is unknown.** Establish the tenant's `version` convention before translating; if the tenant uses only `version: 1` (the default), the question does not arise — **verify that it does.** |
| **—** | **`blocks` and `template_name` are mutually exclusive — and the schema cannot say so.** *"Provide either `blocks` … or `template_name` … — not both."* Both are optional; there is no `oneOf`. | A body carrying both is **schema-valid** and fails only at runtime (`422`). And a locale with **neither** is also schema-valid — an empty locale row that renders as nothing. |
| **—** | **Language codes are UPPERCASE in every document example (`"DE"`, `"EN"`, `"FR"`); the normative-content lookups are lowercase (`?locale=de`).** `Language.code` is 2–8 chars; `ContentBlockLocale.language` is 1–10; `TranslateRequest.target_language` is 2–10. **Three different length bounds for the same concept.** | **Whether matching is case-insensitive is not stated, and nothing in the spec links the `/languages` resource to the `language` string on a locale row** — no FK, no reference, no validation. **A locale row in a language that is not in `/languages` is schema-valid.** Follow the tenant's existing casing exactly; **read it, do not assume it.** |
| **—** | **`ConfigurationResponse.offer_language` is response-only.** It appears on **no request schema anywhere in the spec.** | The customer's offer language is **readable and not settable** through any documented body. `CompanySettingsResponse.default_language` (default `"DE"`) is the tenant-wide fallback. **How `offer_language` is set is not discoverable from the spec — do not claim you can set it.** |
| **—** | **`DELETE /languages/{id}` has no description and declares no `409`.** | **What it does to translations, locale rows and documents in that language is not documented** — cascade, orphan or error. **List what depends on the language before deleting it, and show the user.** |
| **—** | **`order_index` is on `LanguageUpdateRequest` and NOT on `LanguageCreateRequest`** (audit § the `order_index` asymmetry: creatable on 13 resources, update-only on 5, `Language` among them). | You **cannot** set a language's position at create time. `POST`, then `PATCH` — or use `POST /languages/reorder` (`{"order": [ids]}`, `maxItems` 200), which is the intended path. |

**Pagination: there is none.** `GET /languages`, `GET /translations`, `GET /translations/dictionary`, `GET …/locales` — **none of them declares `cursor` or `limit`** (audit § **P1-8** class). A caller cannot distinguish "bounded" from "silently truncated". **Rate limits:** *"Translation upserts | 30/minute"* and *"Document endpoints | 200/hour"*. No `Retry-After` is declared anywhere (audit § **P3-3**) — back off exponentially.

## Output contract

Same `applied` / `skipped` / `errors` shape as `rattle-apply-config` and `rattle-pricing`, plus the three things only a translation run produces: the **bucket classification**, the **regulated-text verification**, and the **staleness gate**.

```json
{
  "tenant": "acme",
  "translated_at": "2026-07-14T09:00:00+00:00",
  "source_language": "DE",
  "target_language": "FR",
  "preflight": {
    "languages": [{"id": 1, "code": "DE", "name": "Deutsch", "is_base": true},
                  {"id": 2, "code": "FR", "name": "Français", "is_base": false}],
    "regulated_blocks": {"safety_notice": 12, "hp_statement": 5},
    "source_hardened": true,
    "note": "signalWord omitted and resolvedText blanked in the source locale — no regulated string is exposed to the translator.",
    "glossary": {
      "entries": 34,
      "consulted_by_translator": "unverified",
      "note": "Rattle does not document whether POST /translate consults /translations/dictionary (audit P0-9g). Verified empirically for 'Spindel' — see verification[]."
    },
    "verdict": "bulk translate permitted — source hardened, run on clone first"
  },
  "applied": [
    {"type": "ensure_language", "name": "FR", "action": "created", "id": 2, "request_id": "req_..."},
    {"type": "ensure_dictionary_entry", "base_term": "Spindel", "action": "updated", "id": 7,
     "translations": {"EN": "Spindel", "FR": "Spindel", "IT": "Spindel"},
     "note": "full map re-sent — PATCH replaces, it does not merge", "request_id": "req_..."},
    {"type": "translate_content_locale", "block_id": 101, "locale_id": 204, "action": "created",
     "target_language": "FR", "source_content_hash": "sha…", "is_stale": false, "request_id": "req_..."},
    {"type": "ensure_structure_block_locale", "block_id": 301, "language": "FR",
     "title": "1. Introduction", "action": "created", "request_id": "req_..."},
    {"type": "relabel_original_language", "block_id": 100, "language": "FR",
     "from": "Originalbetriebsanleitung", "to": "Traduction de la notice originale",
     "basis": "MRL 2006/42/EC §1.7.4.1", "request_id": "req_..."}
  ],
  "skipped": [
    {"type": "translate_content_locale", "block_id": 105, "reason": "noop — target locale exists and is_stale=false"}
  ],
  "verification": [
    {"check": "regulated-text-unchanged", "block_id": 108, "block_type": "safety_notice",
     "fields": ["level", "isoSymbol.category", "isoSymbol.file", "signalWord"],
     "verdict": "pass — codes byte-identical to source; signalWord absent in both locales"},
    {"check": "regulated-text-unchanged", "block_id": 112, "block_type": "hp_statement",
     "fields": ["codes", "combinedKey", "resolvedText"],
     "verdict": "pass — codes byte-identical; resolvedText empty in both locales"},
    {"check": "resolved-against-authority", "code": "H315", "locale": "fr",
     "source": "GET /hp-statements/H315?locale=fr", "verdict": "pass — renderer text matches ECHA"},
    {"check": "glossary-survived-translation", "base_term": "Spindel", "target_language": "FR",
     "observed": "Spindel", "verdict": "pass — lock held (OBSERVED in this tenant, not documented)"},
    {"check": "staleness-gate", "stale_locales": 0, "verdict": "pass — no target locale is stale"}
  ],
  "unknowns": [
    "Rattle does not document whether the DeepL pass consults /translations/dictionary (audit P0-9g).",
    "Rattle does not document what POST /documents/templates/{id}/translate does to safety_notice / hp_statement blocks. Verified on a clone for this template only.",
    "StructureBlockLocaleResponse has source_content_hash but no is_stale — staleness of a translated chapter title is not detectable. Not yet in docs/API_AUDIT.md — report it.",
    "The translatable entity_type / field vocabulary is undiscoverable (audit P0-9h). Read from the tenant."
  ],
  "errors": []
}
```

**`verification` is not optional.** A `201` from `/translate` proves a locale row exists. It proves **nothing** about whether the regulated text in it is lawful. **`unknowns` is not decoration** — it is the part of the report that keeps the next session honest.

**Translation operations.** Idempotent get-or-create by natural key, extending the grammar in `rattle-apply-config/references/operations-contract.md`:

| Operation | Natural key | REST |
|---|---|---|
| `ensure_language` | `code` | `GET /languages` (**not paginated**) → `POST` / `PATCH /languages/{id}`. Required `code` + `name`. **`order_index` is not settable on create** — `POST /languages/reorder` afterwards. |
| `ensure_dictionary_entry` | `base_term` | `GET /translations/dictionary` (**no filters, no pagination — read all of it**) → `POST` / `PATCH …/{entry_id}`. **`PATCH` REPLACES the map: `GET`, merge locally, send it whole.** |
| `upsert_translations` | **(entity_type, entity_id, field, language)** | `PUT /translations` — bulk. **`entity_type` and `field` are free strings: read the tenant's vocabulary, never invent one.** Rate limit **30/minute**. |
| `ensure_content_locale` | **(block_id, language, `version`)** | `GET …/locales` → `POST …/locales` (upsert on `(language, version)`) / `PUT …/locales/{locale_id}`. **`blocks` XOR `template_name`.** |
| `ensure_structure_block_locale` | (block_id, `lang`) | `PUT …/structure/blocks/{block_id}/locales/{localeId}` — a true upsert. **The `{localeId}` URL segment is a language code (e.g. `DE`), uppercased server-side — NOT an integer, despite the name** (the content-block route below is the one keyed by an integer). **Body is `{title}` and nothing else.** |
| `translate_content_locale` | (block_id, locale_id, target_language) | `POST …/locales/{locale_id}/translate` → **`201`**, returns the target `ContentBlockLocaleResponse` — **read `is_stale` and `source_content_hash` back from it.** Declares **`504`**. |

**One operation that is NOT an `ensure_*`, because it is bulk, destructive-by-overwrite, and not verifiable from its own response:**

| Operation | Why it is different |
|---|---|
| `translate_template` | `POST /documents/templates/{id}/translate` → **`200`**. Rewrites **every** structure title and **every** attached content locale in one call. **Returns counts, not ids — you cannot tell what it touched.** Declares **`504`**: a timeout leaves the document **partially** translated. **Never emitted against a template containing `safety_notice` or `hp_statement` blocks without an explicit human confirmation naming the tenant, and never without a clone-and-diff first.** |

## Handing off

```
rattle-techdoc            the document and its 15 chapters
rattle-techdoc-language   the mood, the register, the original-language obligation
  └→ rattle-i18n               translate / resolve / lock            ← you are here
       ├→ rattle-safety-notices   signal words are RESOLVED (32 locales) — never translated
       ├→ rattle-ghs-statements   CLP H/P/EUH text is RESOLVED (24 locales) — never translated
       ├→ rattle-document-templates   the offer / quote / custom / ccms doc_types
       └→ rattle-tenant-memory    the tenant's entity_type vocabulary, its casing convention,
                                  and any OBSERVED translator behaviour — with its provenance
```

- **Never AI-translate a signal word or a CLP statement.** It is a legal defect, not a typo. Resolve from the code.
- **Never assert what the bulk translate does to a regulated block.** Verify it on a clone; report what you observed.
- **Never assume the glossary lock is wired to the translator.** The spec does not say it is. Watch a term survive before you trust it.
- **Never `PATCH` a dictionary entry with a partial map.** It replaces. `GET`, merge, send whole.
- **Never ship a document without checking `is_stale`** — structure-block titles included: `StructureBlockLocaleResponse` now carries `is_stale` (and `source_content_hash`) too.
- **Never leave a translated cover claiming to be the Originalbetriebsanleitung.** MRL §1.7.4.1.
- **Never invent an `entity_type` or a `field`.** Read the tenant's; if the one you need is absent, ask.
- **Harden the source before you translate it.** Omit `signalWord`, blank `resolvedText`. A regulated string that is not in the document cannot be mistranslated.

## Reference files

| File | Use when |
|---|---|
| `references/translation-policy.md` | **Before any translation.** The three buckets applied field-by-field to every EditorJS block type — `paragraph`, `header`, `list`, `table`, `quote`, `warning`, `image`, `delimiter`, `safety_notice`, `hp_statement`. This is the operational core. |
| `references/glossary.md` | You are locking a term, or a locked term came back translated — the dictionary's inline schema verbatim, what belongs in it, the replace-not-merge trap, and what remains unverifiable. |

## Related skills

- `rattle-techdoc-language` — the **host** for language policy: the IEC/IEEE 82079-1 Clause 5 quality attributes, imperative mood, the original-language obligation, MVO Art. 10(7). **This skill extends it; it does not contradict it.** A translated `avoidance` bullet that comes back in the indicative is *its* finding (`mood:non-imperative-instruction`), surfaced by *your* translation.
- `rattle-safety-notices` — signal words are **locale-resolved from `GET /safety-notices/signal-words`, 32 locales**. Bucket 2.
- `rattle-ghs-statements` — CLP H/P/EUH text is **locale-resolved from `GET /hp-statements`, 24 locales**, regulated by (EC) 1272/2008. Bucket 2. **Never translated.**
- `rattle-techdoc` — the 15-chapter structure the locales hang off, and the `editorjs-blocks.md` field reference this skill classifies.
- `rattle-document-templates` — the offer / quote / custom / ccms doc_types, which have locales too.
- `rattle-tenant-memory` — where the tenant's `entity_type` vocabulary, casing convention and any **observed** translator behaviour are recorded, **with provenance**. "Observed" and "documented" are different epistemic states.
- `rattle-api` — auth, RFC 9457 problem details, and the pagination this surface does not have.
