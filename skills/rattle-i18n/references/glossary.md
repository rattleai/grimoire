# The glossary lock — `/translations/dictionary`

**Six operations. One inline, unnamed, undescribed schema. And the single most important open question in this skill.**

The translation dictionary is the mechanism that is supposed to stop a machine translator rendering a locked term however it likes — "Spindel" becoming "spindle", then "mandrel", then "shaft", across three chapters of the same manual.

---

## The contract, verbatim

Everything below is copied from `docs/openapi.json`. Nothing is inferred.

### Create

```jsonc
// POST /api/v1/translations/dictionary          → 201
// summary:      "Create or update a dictionary entry"
// description:  null
// schema:       INLINE, unnamed, additionalProperties NOT set to false
{ "properties": {
    "base_term":    {"type": "string"},
    "translations": {"type": "object", "additionalProperties": {"type": "string"}} },
  "required": ["base_term", "translations"] }
// responses: 201, 401, 422, 429      ← no 409, and no 200
```

### List

```jsonc
// GET /api/v1/translations/dictionary           → 200
// description: "Returns company-wide translation dictionary entries."
// parameters:  NONE.  Not filterable. Not paginated.
{"data": [{"id": integer, "base_term": string,
           "translations": {"<lang>": string}}]}
```

### Read one

```jsonc
// GET /api/v1/translations/dictionary/{entry_id}    → 200 | 404
// description: "Retrieve a single translation dictionary entry. Scope: `products:read`."
```

### Replace / update — **read this twice**

```jsonc
// PUT   /api/v1/translations/dictionary/{entry_id}  → 200
//   "Update an entry; a supplied `translations` map fully replaces the existing one."
// PATCH /api/v1/translations/dictionary/{entry_id}  → 200
//   "Same semantics as PUT — a supplied `translations` map replaces (does not merge)."
// Scope: `products:write`.   responses: 200, 400, 401, 404, 409, 422, 429
{ "properties": {
    "base_term":    {"type": "string", "maxLength": 255},
    "translations": {"type": "object", "additionalProperties": {"type": "string"},
                     "description": "Replaces the entry's full translation map"} } }
// nothing is required — an empty body is valid
```

### Delete

```jsonc
// DELETE /api/v1/translations/dictionary/{entry_id} → 204
// "Idempotent — returns 204 even if the entry does not exist. Scope: `products:write`."
// responses: 204, 401, 429      ← note: no 404, by design
```

**That is the complete published definition of the feature.** No named schema. No description on the `POST`. No statement anywhere of what the dictionary is *for*, when it is applied, or by what.

---

## The data model

An entry is a **base term** and a **map from language to translation**:

```json
{
  "id": 7,
  "base_term": "Spindel",
  "translations": {"EN": "Spindel", "FR": "Spindel", "IT": "Spindel", "ES": "Spindel"}
}
```

**Note what that example is doing.** The "translations" are all identical to the base term. **That is the lock**: the instruction is *"in every language, this term is 'Spindel'."* A glossary entry does not have to translate a term — **its most valuable use is to refuse to.**

The other shape is a **forced** translation — the term does translate, but exactly one way:

```json
{
  "id": 8,
  "base_term": "Schutzhaube",
  "translations": {"EN": "guard", "FR": "protecteur", "IT": "riparo"}
}
```

Here the point is not *whether* it translates but that it translates **the same way every time**. A manual that calls the same part a "guard" in Chapter 5, a "cover" in Chapter 9 and a "shield" in Chapter 13 has an **IEC/IEEE 82079-1:2019 Clause 5 *consistency*** defect (`rattle-techdoc-language`), and a service technician who orders the wrong part.

**Scope: company-wide.** Not per-product, not per-template, not per-document, not per-doc-type. One dictionary per tenant. **A term locked for the machine manual is locked for the offer templates too.** That is usually what you want; know that it is what you get.

---

## The open question — and it is the whole feature

> ### **It is not documented that the DeepL pass consults the dictionary.**

`docs/API_AUDIT.md` § **P0-9g** — *"The glossary lock is invisible — and it is the only thing standing between DeepL and your brand terminology"* — sets out the gap, and its requested fix includes, verbatim:

> *"Name the schema, describe what the dictionary is for (one sentence: 'terms that must translate a specific way, or not at all'), **state whether the DeepL pass actually consults it**, and add filtering/pagination to the `GET`."*

**That question is open.** Grep the spec: `POST /documents/templates/{id}/translate` and `POST …/locales/{locale_id}/translate` both say *"via DeepL"*, and **neither mentions the dictionary.** `GET /translations/dictionary` says *"company-wide translation dictionary entries"*, and **does not say what consumes them.** There is no cross-reference in either direction.

**Consequences you must act on:**

1. **A dictionary entry is a `201` and a row. It is not, on the evidence available, a guarantee.** Writing one and declaring the terminology safe is exactly the failure this repo has already shipped once — `expand=areas.groups.options` went into a skill because it *seemed* right and the spec did not contradict it, and **it had never worked** (audit § **P1-7**). *"An undocumented feature and a hallucinated feature are indistinguishable from the outside."*

2. **Verify the lock, per tenant, before you rely on it:**

   ```
   1. POST /translations/dictionary  {"base_term": "Spindel", "translations": {"EN": "Spindel"}}
   2. Create a throwaway content block whose source locale contains the word.
   3. POST /documents/content-blocks/{id}/locales/{locale_id}/translate  {"target_language": "EN"}
   4. GET the EN locale. Read the term back.
        "Spindel"  → the lock HELD.    Record it as OBSERVED, with the date and the tenant.
        "spindle"  → the lock DID NOT.  The dictionary is not wired to the translator, and
                     the only remaining protection is HUMAN REVIEW. Say so, plainly.
   5. Delete the throwaway block.
   ```

3. **Whatever you find is a measurement, not a contract.** One tenant, one release. Record it in `memory/<tenant>/profile.md` via `rattle-tenant-memory` — **explicit-write only**, with its provenance and its date. *"Observed"* and *"documented"* are different epistemic states, and the next session must be able to tell which one it is reading.

4. **If the lock does not hold, do not silently proceed.** A technical documentation machine-translated with no terminological control is what P0-9g warns about: *"An integrator will find the first and never the second — and will therefore machine-translate a technical documentation with no terminological control at all."* **Tell the human.** The mitigation is human review of the terminology, and that is a schedule and budget decision, not an API call.

---

## The trap that eats a whole language

> **`PATCH` does not merge. It replaces.**

This is one of the few things in this surface that **is** documented — *"Same semantics as PUT — a supplied `translations` map replaces (does not merge)"* — which means getting it wrong is inexcusable, and it is still the easiest mistake to make here, because **`PATCH` means partial update everywhere else in this API.**

```json
// Entry 7 today:
{"id": 7, "base_term": "Spindel",
 "translations": {"EN": "Spindel", "FR": "Spindel", "IT": "Spindel"}}

// You want to add Spanish. The obvious call:
PATCH /api/v1/translations/dictionary/7
{"translations": {"ES": "Spindel"}}
→ 200 OK

// Entry 7 now:
{"id": 7, "base_term": "Spindel", "translations": {"ES": "Spindel"}}
//                                                  ^^^^^^^^^^^^^^^
// EN, FR and IT are GONE. No warning. No 409. A 200.
// The lock silently stopped protecting three languages, and the next
// translation run into any of them renders the term however DeepL likes.
```

**The only correct way to add a language to an entry:**

```
1. GET  /api/v1/translations/dictionary/{entry_id}
2. Merge the new language into the returned `translations` map, LOCALLY.
3. PUT (or PATCH) the COMPLETE map back.
4. GET it again and diff. Confirm every language you expected is still there.
```

**There is no partial write to a dictionary entry. There is only read-merge-write.**

And because the failure is a `200 OK` with a smaller map, **nothing downstream will tell you.** The manual simply comes back with the term translated, in three languages, months later.

---

## What belongs in the dictionary

**Lock a term when a *wrong but fluent* translation would cost something.**

| Category | Examples (synthetic) | Why |
|---|---|---|
| **Brand and product names** | the product family name, the trade name of a subsystem | A product name is not a word. It is a name. It must be identical on the nameplate, the cover, the declaration of conformity and every chapter — `rattle-techdoc-language`: *"The product name on the cover, in section 1.2 validity, and on the nameplate must be **byte-identical**."* A translator does not know that. |
| **Part names that appear on the BOM** | "Spindelmutter", "Schutzhaube" | A service technician reads the manual and orders the part. If the manual's name and the parts list's name diverge across languages, **they order the wrong part.** `rattle-bom-builder` owns the parts; the dictionary keeps their names stable. |
| **HMI labels and control names** | the exact text on a button, a screen, a switch | `rattle-techdoc-language`: *"HMI-screen names exact."* **If the machine's UI is not localised, its labels must NOT be translated in the manual either** — a manual that tells a French operator to press *"Démarrage"* on a machine whose button says *"Start"* is worse than useless. **This is the strongest case for a same-in-every-language lock.** |
| **Regulated abbreviations** | PL, SIL, LOTO, PPE, WEEE, REACH, CE | These are defined terms with legal meaning. Some translate (PPE → EPI in French); many do not. **Whichever it is, it must be decided once.** |
| **Terms the glossary already defines** | anything in `sec-1-7-terms` or `sec-13-6-glossary` | If the document defines a term, that definition **is** the company's decision. **The dictionary is where you enforce it.** A term defined in the glossary and translated freely in the body is `terminology-drift`. |
| **Software / parameter names** | parameter identifiers, error-code mnemonics, config keys | Identifiers. Not prose. Usually a same-in-every-language lock. |

## What does NOT belong in it

| Do not lock | Why |
|---|---|
| **Signal words** (GEFAHR / WARNUNG / VORSICHT / HINWEIS) | **Bucket 2.** They are already correct in 32 locales, resolved from `level` by the renderer (`GET /safety-notices/signal-words`). Putting them in the dictionary is a *second, unauthoritative* source for a **normative** string — a conflict with ISO 3864-2 waiting to happen. **Omit `signalWord` from the block and let the renderer resolve it.** See `rattle-safety-notices`. |
| **CLP H / P / EUH statement text** | **Bucket 2, and this one is a legal defect.** The text is regulated by **(EC) No 1272/2008** and resolved from `codes[]` in 24 locales (`GET /hp-statements`). **A dictionary entry containing a CLP statement is a hand-maintained copy of a regulated string** — it will drift from the ECHA text, and nothing will tell you. **Leave `resolvedText` empty.** See `rattle-ghs-statements`. |
| **ISO 7010 symbol filenames** | **Bucket 0.** `W024_crushing_of_hands.svg` is a filename. It is not language. |
| **Whole sentences** | The dictionary is a **term** glossary. A locked sentence is a content block — put it in a reusable content block, not the dictionary. |
| **Numbers, units, tolerances** | **Bucket 0.** There is no target-language version of `45 Nm`. |
| **Anything you have not decided yet** | An entry is **company-wide**. Adding one is a **terminology decision for the whole tenant**, in every document and every doc_type. **Ask before you add one.** |

---

## Operating the dictionary

### Reading it

```
GET /api/v1/translations/dictionary        → the whole thing, always
```

**No filters. No pagination. No search.** You cannot ask "is `Spindel` locked?" — **you read every entry and look.** For a large tenant that is a large response, and there is no `cursor`/`limit` to bound it (audit § **P1-8** class): **you cannot distinguish "that was all of them" from "that was as many as it felt like sending."** Cache it for the run; re-read it before you write.

### The `ensure_dictionary_entry` operation

**Natural key: `base_term`.** Idempotent get-or-create:

```
1. GET /translations/dictionary                    (all of it — there is no filter)
2. Find the entry whose base_term matches EXACTLY.
     absent          → POST   {base_term, translations}
     present, differs → GET the entry, MERGE LOCALLY, PATCH the COMPLETE map
     present, matches → noop
3. GET it back and diff.  The body sets no `additionalProperties: false`
   (audit § P0-10 class) — a typo'd field is swallowed with a 2xx.
```

**Match `base_term` exactly.** Whether matching is case- or whitespace-sensitive **is not documented**. Do not normalise it yourself and assume the server agrees.

### The asymmetries — all verified, none explained

| Fact | What it means for you |
|---|---|
| **`POST` declares `201` only** — no `409`, no `200` — but its summary says *"Create **or update**"*. **`PUT`/`PATCH` DO declare `409`.** | The `409`s imply `base_term` is **unique**. The `POST`'s upsert behaviour exists **only in a summary line**, and what it returns when it updates rather than creates is not stated. **Do not rely on the upsert. Read first, then choose `POST` or `PATCH` yourself.** |
| **`base_term` has `maxLength: 255` on `PUT`/`PATCH` and NO `maxLength` on `POST`.** | **A `base_term` you can create, you may not be able to update.** Cap it at 255 yourself on create. |
| **No body sets `additionalProperties: false`** — not `POST`, not `PUT`, not `PATCH`. `additionalProperties` is `false` on **116 of 124** request schemas (audit § **P0-10**). | **A typo'd field is accepted with a `2xx` and dropped.** You have learned from 116 other schemas that a bad field errors. **That lesson is wrong here.** **`GET` after every write and diff.** |
| **`PUT`/`PATCH` declare a `400` that `POST` does not.** | Its condition is not documented. Handle it; you will not be able to predict it. |
| **`DELETE` is genuinely idempotent** — *"returns 204 even if the entry does not exist"* — and declares **no `404`**. | Good design, and rare. **But: a `204` is NOT evidence that anything was deleted.** If you need to know that an entry existed, `GET` it first. |
| **The `GET` response has no `created_at` / `updated_at`.** | **There is no way to tell when a lock was added or last changed**, or by whom. If provenance matters, record it in `memory/<tenant>/profile.md` yourself. |

---

## The honest summary

**What is verified:**
- An entry is `{base_term, {lang: translation}}`, company-wide, unique on `base_term` (inferred from the `409` on `PUT`/`PATCH`).
- `PATCH` **replaces** the translation map. Documented, explicitly, twice.
- The `GET` is unfilterable and unpaginated.
- `DELETE` is idempotent.
- Scopes: `products:read` to read, `products:write` to write.

**What is NOT verified, and must not be asserted:**
- **Whether `POST …/translate` (DeepL) consults the dictionary at all.** ← *the one that matters.* Audit § **P0-9g**.
- Whether `base_term` matching is case- or whitespace-sensitive.
- What `POST` returns when it updates rather than creates.
- What the `400` on `PUT`/`PATCH` means.
- Whether a locked term is matched as a **whole word**, a **substring**, or **case-insensitively** inside the source text — i.e. whether locking "Spindel" also locks "Spindelmutter", and whether that is desirable.
- Whether the dictionary applies to `PUT /translations` (the per-entity translation cache) as well as to the DeepL document pass, or to neither, or to both.

**Carry these as stated unknowns. Do not resolve them by guessing — resolve them by measuring, in a test tenant, and record the provenance.**
