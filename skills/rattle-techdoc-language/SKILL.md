---
name: rattle-techdoc-language
description: Use this skill whenever the user is writing, editing, translating, or auditing the language and tone of a Rattle technical documentation. Activates for any "language", "tone", "Sprache", "Verständlichkeit", "Klartext", "imperative mood", "controlled language", "terminology", "translation", "Übersetzung", "Originalbetriebsanleitung" task. Encodes IEC/IEEE 82079-1 §7 quality criteria (clarity, accuracy, completeness, conciseness, consistency, currency), audience-tailored mood (imperative for instructions, indicative for descriptions), terminology rules, the original-language obligation per MRL §1.7.4.1, the MVO 2023/1230 digital provision rules, and the locale-resolution policy (normative content is locale-resolved, not AI-translated). Pair with rattle-techdoc (host skill) and the safety-notices / GHS sister skills for normative texts.
license: MIT
---

# Rattle technical documentation — language & tone

Technical documentation is a legally binding deliverable where wording matters. A vague verb in a maintenance instruction can shift liability; a missing imperative can void warranty cover. This skill encodes the language and tone rules that every Rattle technical documentation must follow, plus the locale and translation policies.

## When to use this skill

Activate when the user:

- Asks about **tone**, **mood**, **register**, **voice**, **clarity**, **conciseness**, or **terminology** in a technical document.
- Asks about the **original-language obligation** ("Originalbetriebsanleitung" vs translation).
- Asks how to **translate** an existing manual to another EU language.
- Asks about **MVO 2023/1230 digital provision** rules.
- Wants to convert **vague prose** ("man kann …", "you should …") into **imperative-mood instructions** ("entfernen Sie …", "remove the …").
- Asks about the **target audience** (operator vs setter vs service technician) and how each chapter speaks to them.
- Reviews a draft and asks "is this clear enough?" / "is this normative enough?".

For the chapter structure itself, use `rattle-techdoc`. For safety-notice wording, use `rattle-safety-notices`. For chemical-hazard wording, use `rattle-ghs-statements`.

## The IEC/IEEE 82079-1 §7 quality criteria

Every chapter's content must satisfy six quality criteria (IEC/IEEE 82079-1:2019 §7):

| Criterion | Definition | What to check |
|---|---|---|
| **Clarity** | The reader understands on first read what to do. | No ambiguity ("perhaps", "maybe"); no nominalisation when a verb works ("perform inspection of …" → "inspect the …"); short sentences. |
| **Accuracy** | Wording matches the product. | Part numbers, torque values, tolerances, software versions are exact. No "approximately" where a number is required. |
| **Completeness** | All information required by the audience is present. | Acceptance criteria, error states, post-condition checks. |
| **Conciseness** | No filler. Every sentence carries information. | No "in order to" (use "to"). No "it is recommended that" (use imperative). No restating chapter titles. |
| **Consistency** | Same term, same meaning, throughout. | One name per part / state / mode. No "controller / control unit / PLC" alternation. |
| **Currency** | The information is up-to-date. | Issue date present; revision-controlled; change log in `sec-12-3-doc-status`. |

The audit emits `quality-violation:<criterion>:<sub-id>` findings.

## Mood and voice

### Instructions → imperative mood

Every step in a procedure is an **imperative sentence**. The subject ("you") is implicit; the verb starts the sentence.

| Bad | Good |
|---|---|
| "The operator should engage the lockout-tagout before starting maintenance." | "Engage lockout-tagout before maintenance." |
| "Man muss vor Wartungsarbeiten den Schalter ausschalten." | "Schalten Sie vor Wartungsarbeiten den Schalter aus." |
| "It is necessary to wear gloves." | "Wear gloves." |
| "You may want to check the seal." | "Check the seal." |

> In German technical documentation, the convention is **Sie-form imperative** (formal "you"): "Schalten Sie ab.", "Sichern Sie gegen Wiedereinschalten." This stays grammatically polite while being unambiguous.

### Descriptions → present-tense indicative

For descriptive text (Chapter 3 product description, Chapter 7 controls, Chapter 8 error code tables), use **present-tense indicative**.

| Bad | Good |
|---|---|
| "The drive system would normally operate in synchronous mode." | "The drive system operates in synchronous mode." |
| "When the green LED is going to be on, the system is ready." | "When the green LED is on, the system is ready." |

### Avoid passive voice in instructions

| Bad (passive) | Good (active imperative) |
|---|---|
| "The seal must be checked before reinstalling the cover." | "Check the seal before reinstalling the cover." |
| "Vor Wiedereinbau ist die Dichtung zu prüfen." | "Prüfen Sie die Dichtung vor dem Wiedereinbau." |

Passive voice is acceptable in **descriptions of automatic processes** ("The valve is opened by the controller when …"), not in instructions.

## Audience-tailored register

Each chapter speaks to a specific audience. The audience is defined in `sec-1-3-target-groups`.

| Chapter | Primary audience | Vocabulary expectations |
|---|---|---|
| 1 (About this Document) | All | Plain language; no domain jargon. |
| 2 (Safety) | All | Plain language; safety-specific terms defined inline. |
| 3 (Product description) | All + service | Domain language allowed; cross-link to glossary 13.6. |
| 4 (Transport) | Transport personnel | Plain language; pictograms; no controller terminology. |
| 5 (Assembly) | Mechanical / electrical specialists | Domain-specific (torque, alignment, IEC 60204); cross-link to schematics. |
| 6 (Commissioning) | Service / setter | Tool-list precise; expected-result precise. |
| 7 (Operation) | Operator | Plain language; HMI-screen names exact. |
| 8 (Troubleshooting) | Operator + service | Two-column structure: operator-recoverable on top, service-required below. |
| 9 (Maintenance) | Service / maintenance | LOTO procedure repeated explicitly. |
| 11 (Decommissioning) | Service + waste-disposal | Waste-stream terminology (WEEE, REACH). |
| 12 (Conformity) | Quality / regulatory | Legal-precise; verbatim directive titles. |
| 13 (Appendix) | Service | Reference data only; no narrative. |

When a chapter must address multiple audiences, **split into sub-sections** by audience rather than mixing register. Section 8 typically does this with operator-recoverable error codes vs service-required error codes in separate tables.

## Terminology consistency

Every term used in the documentation must:

1. **Have a single definition** (in `sec-1-7-terms` or the glossary `sec-13-6-glossary`).
2. **Always be used the same way.** No "controller / control unit / PLC" alternation; pick one and use it throughout.
3. **Match the product nameplate.** The product name on the cover, in section 1.2 validity, and on the nameplate must be byte-identical.
4. **Resolve abbreviations on first use.** "Performance Level (PL)" first; then "PL" only.

A *terminology table* in the glossary lists every term with its definition; the audit `terminology-drift` flags terms used differently across chapters.

## Sentence and paragraph length

| Element | Target | Maximum |
|---|---|---|
| Sentence (instruction) | 8–15 words | 25 |
| Sentence (description) | 12–20 words | 30 |
| Paragraph | 2–4 sentences | 6 |
| Bullet item | 3–10 words | 15 |
| Procedure step | One sentence (imperative) | one + one expected-result clause |

When a procedure step requires more than one action, split into multiple steps. When a sentence runs > 25 words, split.

## Numbers, units, ranges

- **Always SI units** with the symbol after the value: `230 V`, `50 Hz`, `Nm`, `°C`. Use a non-breaking space between number and unit.
- **Tolerances** as `± n` with explicit unit: `± 0,5 mm` (DE) / `± 0.5 mm` (EN — note decimal separator).
- **Ranges** with en-dash and unit at the end: `5–10 Nm`, not `5 Nm – 10 Nm`.
- **Imperial units only** when the product is sold to a market that requires them; in that case, dual-unit `230 V (60 Hz)` becomes `120 V / 60 Hz` for US.

## Original-language obligation

MRL §1.7.4.1 (and MVO equivalent):

> *Original instructions in an official Community language. The expression "Original instructions" must appear on the language version verified by the manufacturer. Translations must bear the words "Translation of the original instructions".*

**Practical rules for Rattle templates:**

1. **Always** mark the cover page with the original-language label: "Originalbetriebsanleitung" (DE) / "Original Operating Instructions" (EN).
2. **Always** record the original locale in `sec-12-3-doc-status` (e.g. *"Sprache der Originalbetriebsanleitung: Deutsch"*).
3. **Translations** carry "Übersetzung der Originalbetriebsanleitung" / "Translation of the original instructions" on the cover.
4. The manufacturer (or representative) must **verify** the original-language version. Translation may be by a third party but is provided by the manufacturer.

## Translation policy

When the user asks for a translation:

1. **Use `POST /documents/templates/{id}/translate`** with `target_language`. The backend uses the configured AI provider plus DeepL if available.
2. **Normative text is NOT AI-translated.** Signal words (`safety_notice.signalWord`) and CLP statement text (`hp_statement.resolvedText`) are resolved at render time from the official tables in `safety_notice_words.py` / `hp_statements.py`.
3. **After translation, re-run the audit checks.** Translations can drop sentences, change voice, or break terminology consistency. The `unfinished-translation` audit flags target-locale `block_json` arrays shorter than the source-locale arrays.
4. **The translated document carries the translation marker** (see "Original-language obligation" above) — never just clone the cover from the source locale.
5. **Accuracy check.** Translated procedures must produce the same physical result as the source. For safety-critical procedures (LOTO, e-stop), require human review of the translation.

## MVO 2023/1230 digital provision rules (effective 20 January 2027)

The MVO replaces MRL and allows fully digital provision under conditions. Rattle's approach for `sec-1-8-digital-access`:

1. The user receives a URL or QR code to the digital instructions on first use.
2. The instructions remain available "for the expected lifetime of the machine" (≥ 10 years).
3. An **offline copy** must be obtainable (download, USB stick).
4. A **paper version** must be deliverable free within 30 days on request.

The standard content for `sec-1-8-digital-access` is the reusable content block `digital-access-mvo` (see `rattle-techdoc/references/chapter-reference.md` reusable list).

## Locale list and locale aliases

Locales for which Rattle ships normative content:

- **Signal words (safety_notice):** 31 locales — see `rattle-safety-notices/references/signal-words.md`.
- **H/P statements (hp_statement):** 24 EU locales + aliases — see `rattle-ghs-statements/references/hp-statement-locales.md`.
- **Document content (everything else):** any locale supported by your AI provider + DeepL.

When picking the document's primary locale, prefer the manufacturer's verification language (the original-language obligation). Translations follow.

## Audit-related rules this skill enforces

- `quality-violation:clarity:nominalisation` — "perform inspection of" / "carry out a check on" / "make a determination as to whether".
- `quality-violation:clarity:passive-instruction` — passive voice in an instruction.
- `quality-violation:conciseness:filler` — "in order to" / "due to the fact that" / "the reason for this is that".
- `quality-violation:consistency:terminology-drift` — same concept named differently across chapters.
- `quality-violation:accuracy:vague-number` — "approximately N" where the documentation requires a tolerance.
- `mood:non-imperative-instruction` — instruction sentence not in imperative mood.
- `original-language-obligation:missing-marker` — cover page missing "Originalbetriebsanleitung" / "Translation of the original instructions".
- `audience-mismatch` — domain jargon in a chapter targeted at operators.

## Output contract — `language-review.json`

```json
{
  "domain": "language_review",
  "template_id": 4711,
  "review_locale": "de",
  "summary": {
    "checks_run": 8,
    "violations": 12,
    "by_severity": {"high": 1, "medium": 6, "low": 5}
  },
  "violations": [
    {
      "rule_id": "quality-violation:clarity:nominalisation",
      "severity": "medium",
      "structure_block_slug": "sec-9-4-maintenance-tasks",
      "evidence": "\"Es ist eine Inspektion der Lager durchzuführen.\"",
      "correction": "\"Inspizieren Sie die Lager.\""
    },
    {
      "rule_id": "mood:non-imperative-instruction",
      "severity": "high",
      "structure_block_slug": "sec-9-1-loto",
      "evidence": "\"You should disconnect the mains plug.\"",
      "correction": "\"Disconnect the mains plug.\""
    }
  ]
}
```

## Related references

- `references/style-guide.md` — extended style guide with bad-vs-good rewrites for German + English.
- `references/locales.md` — the full locale matrix for technical documentation: which standards are met where.
- `rattle-techdoc/SKILL.md` — host skill.
- `rattle-safety-notices/SKILL.md` — normative safety-notice wording.
- `rattle-ghs-statements/SKILL.md` — normative chemical-hazard wording.
