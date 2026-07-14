---
description: Translate, localise or audit the multilingual layer of a Rattle tenant — languages, per-entity translations, block locales, the DeepL document translator, and the glossary lock. Leads with the classification that is the whole job: every string is AI-translatable prose, LOCALE-RESOLVED regulated text (signal words, CLP H/P/EUH statements), or GLOSSARY-LOCKED terminology, and treating one as another is the failure mode. Refuses to run the bulk template translate against a document containing safety_notice or hp_statement blocks without a human naming the tenant — the spec never says what the DeepL pass does to regulated text, so it verifies on a clone rather than guessing.
argument-hint: <tenant name> [template, document, or target language]
---

# /rattle-translate

Take the tenant the user names (`$ARGUMENTS`) and make the document **true in a second language** — languages, block locales, the DeepL translator, the glossary lock, and the staleness gate.

**25 operations across four families**, and the sharpest legal exposure in the bundle. A wrong price costs money. **A wrong signal word or a mistranslated CLP hazard statement is a defect in a CE-marked document**, and it reads perfectly.

Read step 2 before anything else.

## Workflow

1. **Load context** — Read `skills/rattle-i18n/SKILL.md` and **both** reference files: `references/translation-policy.md` (the field-by-field bucket classification per EditorJS block — **have it open while you work**) and `references/glossary.md` (before locking a term, or when a locked term came back translated). Load `skills/rattle-techdoc-language/SKILL.md` — **this skill extends it and must not contradict it**: the original-language obligation and the imperative-mood rule are *its* rules, enforced on *your* output. Load `skills/rattle-safety-notices/SKILL.md` and `skills/rattle-ghs-statements/SKILL.md` — they define what **correct** regulated text is, and correct is **resolved from a code**, never translated. Read `memory/<tenant>/profile.md`: it carries the tenant's `entity_type` vocabulary, its language-code casing convention, and any **observed** translator behaviour.

2. **Three buckets. Classify before you translate.** Every string is exactly one of:

   - **AI-TRANSLATABLE** — free prose. Chapter bodies, captions, and the `title` / `hazard` / `consequences` / `avoidance` text *inside* a safety notice. DeepL is correct here. Apply the glossary.
   - **LOCALE-RESOLVED — NEVER TRANSLATE.** **Signal words** (GEFAHR / WARNUNG / VORSICHT / HINWEIS ↔ DANGER / WARNING / CAUTION / NOTICE) — resolved from `GET /safety-notices/signal-words`, **32 locales**, ISO 3864-2 / ANSI Z535.6. **CLP H/P/EUH statement text** — resolved from `GET /hp-statements`, **24 locales**, regulated by **(EC) 1272/2008**, ECHA-traceable to Annex III/IV/VI on EUR-Lex.

     > **DeepL-translating a CLP hazard statement is a legal defect in a CE-marked document, not a typo.** The correct German for H301 is not whatever DeepL says — it is the exact string in the CLP regulation's German annex. A fluent paraphrase is **worse** than an obvious error, because it survives review.

     **And the codes are not language either**: `level`, `codes[]`, `isoSymbol.file` (`W024_crushing_of_hands.svg` — a **filename**; translate it and the pictogram 404s), `list.style`, `image.file.url`. **A code that looks like a word is still a code.**
   - **GLOSSARY-LOCKED** — brand terms, part names, HMI labels, regulated abbreviations. `/translations/dictionary`.

3. **The bulk template translate — and what we could NOT verify** — `POST /documents/templates/{id}/translate` (**`200`**, not `201`): *"Translate **all** structure block titles and attached content block locales to the target language **via DeepL**."*

   **It does not say what it does to a `safety_notice` or an `hp_statement` block. We could not determine it from the spec, and we will not guess.** It is *probably* harmless — those blocks carry **codes** and the renderer resolves the regulated text — **but that is an inference.** `blocks` is typed `items: {additionalProperties: true}`; the spec does not know what a `safety_notice` *is*, so it cannot tell you what the translator does to one. This repo has shipped exactly this class of error before: `expand=areas.groups.options` went into a skill because it *seemed* right, and **it had never worked** (audit § **P1-7**). *"An undocumented feature and a hallucinated feature are indistinguishable from the outside."*

   **So: inventory the blocks first.** No `safety_notice` and no `hp_statement` → **use the bulk translate, it is fine.** Either one present → **clone the template, translate the clone, and diff the regulated fields** against `rattle-safety-notices` / `rattle-ghs-statements`. **Byte-identical, or empty. Anything else is a stop.**

   **The response returns counts, not ids** — `{translated_titles, translated_content_locales}` — so **you cannot tell what it touched.** Re-`GET`. And it declares a **`504`**: a timeout leaves the document **partially translated**, and the response that would have told you how far it got is the one you did not receive. **Never blind-retry — reconcile.**

4. **Harden the source first. This is the cheap fix and it makes step 3 moot.** **Omit `signalWord`** on every `safety_notice` — *"the renderer resolves it from the document locale"* (`rattle-safety-notices`). **Set `resolvedText: ""`** on every `hp_statement` — *"if the renderer does not yet know the locale, leave it empty"* (`rattle-ghs-statements`). **A regulated string that is not in the document cannot be mistranslated.** After this, the only regulated data left is **codes**, and codes are not prose. Do it once; the bulk translate is then safe **by construction**, whatever it does internally.

5. **The glossary lock — and the question nobody answered** — `POST /translations/dictionary`, `{base_term, {lang: translation}}`, **company-wide, unfilterable, unpaginated**. The mechanism that stops "Spindel" becoming "spindle".

   > **It is NOT documented that the DeepL pass consults it.** Audit § **P0-9g** — *"The glossary lock is invisible"* — asks upstream, verbatim, to *"**state whether the DeepL pass actually consults it**."* **That question is open. A dictionary entry is a `201` and a row; that it constrains the translator is an assumption.** **Verify it: lock a term, translate a throwaway block containing it, read the term back.** If it came back translated, the lock is not wired to the translator and **the only remaining protection is human review** — say so, plainly, rather than shipping on the strength of a lock that does nothing.

   **And: `PATCH` REPLACES the translation map — it does not merge.** Documented, twice. A `PATCH` with `{"translations": {"ES": "…"}}` **deletes EN, FR and IT**, with a `200 OK`. **`GET`, merge locally, send the complete map.** Always.

6. **`entity_type` and `field` are free strings with no enum** — `PUT /translations` upserts `{entity_id, entity_type, field, language, value}`. **Which entities are translatable is undiscoverable** (audit § **P0-9h**): *"`entity_type: "prodcut"` (typo) and `field: "nmae"` are both schema-valid."* The spec's *example* row is `{"entity_type": "area", "field": "name"}` — **an example, not a vocabulary.** **`GET /translations`, collect the distinct pairs the tenant already uses, and use only those. If the one you need is absent, ASK THE USER.** A typo is a `200 OK` and a translation nobody will ever read. Rate limit: **`Translation upserts | 30/minute`**.

7. **Staleness — the release gate. Credit where it is due.** `POST …/translate` writes a **`source_content_hash`**; if the source changes afterwards, the target's **`is_stale`** flips to `true`. The audit calls it out as genuinely good design: *"exactly the right primitive for keeping a multilingual manual honest."* **Check `is_stale` on every target locale before you ship. Every time.** A source chapter edited after translation leaves every downstream locale silently describing the old machine.

   > **But `StructureBlockLocaleResponse` has `source_content_hash` and NO `is_stale`.** **You cannot ask whether a translated chapter *title* is stale**, and the hash algorithm is undocumented so you cannot recompute it. Fall back to comparing the source title's `updated_at`. *(Not yet in `docs/API_AUDIT.md` — **report it**.)*

8. **Re-label the cover. MRL §1.7.4.1.** The source is the **"Originalbetriebsanleitung"**; **every** translation must say **"Übersetzung der Originalbetriebsanleitung"**. **The translator will not do this — it will translate the words "Originalbetriebsanleitung" and produce a false claim**, because that locale was never verified by the manufacturer. `rattle-techdoc-language`: *"never just clone the cover from the source locale."*

9. **Re-audit the language after every translation.** DeepL returns fluent, correct, **non-imperative** prose. *"Prüfen Sie die Dichtung"* → *"The seal should be checked"* is a **correct translation and a documentation defect** (`mood:non-imperative-instruction`). **Every `avoidance[]` bullet and every procedure step must still be an imperative in the target language.** Array lengths preserved (a merged step is a **deleted** step). Cross-reference numbers unchanged. **Decimal separators not "converted"** — DE `1.000` and EN `1,000` are not the same number, and a machine translator applying a thousands-separator convention to a torque value is a silent factor-of-1000 error.

10. **Record what was learned** — the tenant's `entity_type` vocabulary, its language-code casing (document examples are **UPPERCASE** `"DE"`; the normative lookups are **lowercase** `?locale=de`, and **nothing in the spec links the `/languages` resource to the `language` string on a locale row**), and any **observed** translator behaviour. `memory/<tenant>/profile.md` via `rattle-tenant-memory` — **explicit-write only**: show the file, get consent, and **record the provenance.** An observation is not a contract.

## Confirmation discipline

Every write pauses. Restate the tenant, the operation, the natural key, the source and target language, and the exact body — then ask the user to **type the tenant name**. A generic "yes" is not consent.

**Two operations get their own hard gate:**

- **`POST /documents/templates/{id}/translate` against a document containing `safety_notice` or `hp_statement` blocks.** Refused unless a human names the tenant *for that call*, and refused unless the regulated fields have been verified on a **clone** first. The spec does not say what the DeepL pass does to regulated text; **an unrun translation is recoverable, a mistranslated hazard statement in a shipped manual is not.**
- **`PATCH`/`PUT` on a dictionary entry.** Refused unless the **complete** merged map is being sent. A partial map silently destroys every language it omits.

## Delegation

Delegate the run to the `rattle-translator` subagent with the tenant name. It preloads `rattle-i18n`, `rattle-techdoc-language`, `rattle-safety-notices`, `rattle-ghs-statements`, `rattle-techdoc` and `rattle-api`, holds the confirmation gate, **refuses to AI-translate a signal word or a CLP statement**, **refuses the bulk template translate on a regulated document without a clone-and-diff and a human naming the tenant**, **refuses to `PATCH` a dictionary entry with a partial map**, **refuses to assert that the glossary lock constrains DeepL** without having watched a term survive, and **gates the release on `is_stale`**.

$ARGUMENTS
