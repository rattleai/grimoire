# Legal and normative basis for technical documentation

Reference of the directives, regulations, and standards every Rattle technical documentation must satisfy. Use this when the user asks "what does the law actually require?" or when an audit flags a CRITICAL finding tied to legal compliance.

> **Triage rule.** Always distinguish *legally binding* (Directive / Regulation / national law) from *technically harmonised* (CEN / CENELEC / IEC / ISO). Standards become legally binding only when explicitly listed in the Official Journal of the EU or the national equivalent. Compliance with a harmonised standard yields *presumption of conformity* — not automatic conformity.

---

## EU directives and regulations (legally binding)

### Maschinenrichtlinie 2006/42/EG · Machinery Directive

Applies to machinery placed on the EU market **until 19 January 2027 (inclusive)**. Repealed with effect from 20 January 2027 by (EU) 2023/1230 Article 53(2).

| Annex / clause | Documentation requirement |
|---|---|
| Annex I, §1.7.4 | Information for use must accompany the machine. |
| Annex I, §1.7.4.1 | Original instructions in an official EU language; translations marked "Translation of the original instructions". |
| Annex I, §1.7.4.2 (a-v) | Lettered content requirements (intended use, residual risks, transport, installation, operation, maintenance, decommissioning, …) — refer to the consolidated text for the exact list. |
| Annex II, §1.A | EC Declaration of Conformity content requirements. |
| Annex VII | Technical file content requirements. |

**Practical effect on Rattle.** The 15-chapter structure satisfies Annex I §1.7.4.2. Chapter 13.1 holds the Declaration. Chapter 12.1 lists every applied directive.

### Maschinenverordnung (EU) 2023/1230 · Machinery Regulation

Applies to machinery placed on the EU market **from 20 January 2027** (Article 53(2)). Until that date, MVO conformity is **not yet certifiable** — the OJEU has not listed harmonised standards under MVO and Notified Bodies cannot yet issue MVO certificates.

| Article / annex | What it changes |
|---|---|
| Art. 10 | Information requirements clarified; product identification, traceability. |
| Art. 10(7) | **Digital-provision rule.** (a) Instructions may be supplied digitally **except** for machinery intended for or foreseeably used by non-professional users — for those, the **safety-essential** information must be provided **in paper form**, irrespective of any request. (b) Any user may request the full instructions in paper format **free of charge** at the time of purchase, to be delivered **within one month**. (c) Online availability must cover the **expected lifetime of the machinery** and **at minimum 10 years** after placement on the market. |
| Art. 18 | "Substantial modifications" trigger re-conformity assessment + new CE; affects Chapter 10 of every existing manual. |
| Annex IV (1.A) | EU Declaration of Conformity replaces EC Declaration. |

**Practical effect on Rattle.**
- Section `sec-1-8-digital-access` must distinguish professional-vs-consumer-use scope. The reusable content block `digital-access-mvo` should expose a `professional_use_only` switch; when `false`, the safety-essential paper supply is mandatory.
- Section `sec-12-1-directives` needs updating before 2027 cut-over.
- Chapter 10 needs the substantial-modifications definition.
- Until OJEU publishes harmonised standards under MVO, parallel MRL conformity remains the only certifiable path for products placed on the market before 20 January 2027.

### Niederspannungsrichtlinie 2014/35/EU · Low Voltage Directive

Applicable to electrical equipment in 50–1000 V AC / 75–1500 V DC range. If a machine is also LVD-scope, list it in Section 12.1.

### EMV-Richtlinie 2014/30/EU · EMC Directive

Electromagnetic compatibility. List in Section 12.1 when applicable.

### ATEX 2014/34/EU · Equipment for Explosive Atmospheres

If applicable: explicit ATEX category, marking on cover and nameplate, dedicated chapter or annex with the conditions of safe use.

### MDR (EU) 2017/745 · Medical Device Regulation *(out of scope for this skill)*

> **Important:** MDR governs **medical devices**, which are a different regulatory regime from machinery. The 15-chapter structure encoded in this skill targets **machinery (MRL/MVO)** — it is **not** a substitute for an MDR-compliant Instructions for Use (IFU). For medical devices use ISO 20417 (IFU content), ISO 15223-1 (medical-device symbols), and IEC 62366-1 (usability engineering applied to medical devices) — none of which are covered by `rattle-techdoc` today. A future `rattle-techdoc-medical` skill would own this scope. Treat any MDR-scope project as out of scope until that skill exists.

If a customer presents a medical device disguised as machinery (e.g. a sterilising washer, a powered hospital bed, a UV cabinet), refuse the machinery scaffold and flag the scope mismatch.

### CLP Regulation (EC) 1272/2008

Classification, Labelling, and Packaging of substances and mixtures. Source for H-statements / P-statements / EUH-statements / GHS pictograms. The 9 GHS pictograms (GHS01–GHS09) are EN-harmonised via the UN GHS adoption; CLP applies in the EU/EEA (and the UK retains a separate but materially-equivalent UK CLP regime since Brexit). The authoritative locale-specific statement texts live in ECHA's published Annex III/IV/VI translations on EUR-Lex; the open-source `mhchem/hpstatements` data Rattle ships is derived from those — for audit defensibility, every shipped statement should be checkable against the latest ECHA/EUR-Lex tables. See `rattle-ghs-statements/SKILL.md`.

### REACH (EC) 1907/2006

Where the manual references chemical substances, REACH SDS reference may be required.

### WEEE Directive 2012/19/EU

Disposal of electrical / electronic equipment. Drives the `disposal-electronics-weee` content block.

---

## Harmonised standards (presumption of conformity)

These are the standards that every technical-documentation skill in this workspace cites. All are **expectations** the audit checks enforce.

### DIN EN ISO 20607:2019

*Safety of machinery — Instructions for use — General drafting principles.*

The most important standard for the structure of every operating manual. Defines:

- Tab. 1 — Required information per life-cycle phase.
- §5.1–5.5 — Cover page, validity, target groups, intended use, residual risks.
- §5.6 — Construction, format, language, accessibility.

> **The 15-chapter structure encoded in this skill is *compatible with* but not *prescribed by* ISO 20607.** The standard recommends a structure that aligns with the lifecycle-phase content list; the 15-chapter Rattle scheme is one defensible interpretation. Audit findings should phrase the requirement as "addresses ISO 20607 §X.Y" rather than "violates the 15-chapter rule".

### IEC/IEEE 82079-1:2019

*Preparation of information for use (instructions for use) of products — Part 1: Principles and general requirements.*

The cross-industry meta-standard. Defines:

- **Clause 5** — General principles for information for use, including the **seven quality attributes**: complete, correct, concise, consistent, comprehensible, accessible, plus the principle of minimalism.
- **Clause 6** — Information-management process (planning, design, production, evaluation, sustainment). *Does not apply to consumer products.*
- **Clause 7** — Content of information for use (target-audience identification, what to include for safe / effective / efficient use). Subclauses 7.5 (warnings and warning messages) and 7.6 (graphical and textual symbols) drive the cross-reference with ISO 3864-2 / ANSI Z535.6.
- **Clause 8** — Structure of information.
- **Clause 9** — Media and format of information.

> Earlier drafts of this skill cited "§7 Quality criteria (clarity, accuracy, completeness, conciseness, consistency, currency)". Those attribute names were wrong and the section number was wrong — Clause 5 is the correct location, and the seven attributes above are the canonical list. "Clarity" is approximated by *comprehensible*; "currency" is a sustainment concern in Clause 6, not a quality attribute in Clause 5.

### ISO 12100:2010

*Safety of machinery — General principles for design — Risk assessment and risk reduction.*

- §6.4.1 — Residual risk information requirement.
- §6.4 — User information as the third level of risk reduction (after design and safeguards).

### ISO 3864-1, -2, -3, -4:2016

*Graphical symbols — Safety colours and safety signs.*

- Part 2 — Design principles for product safety labels.
- Annex B — Signal-word ladder (DANGER / WARNING / CAUTION / NOTICE) and colour assignments.

### ISO 7010:2019

*Graphical symbols — Safety colours and safety signs — Registered safety signs.*

The catalogue of ~200 registered safety signs across **five** categories: warning (W), prohibition (P), mandatory action (M), safe condition (E), fire protection (F). See `rattle-safety-notices/references/iso-7010-symbols.md`.

> **GHS pictograms are NOT part of ISO 7010.** They have a different normative basis (CLP Regulation (EC) 1272/2008 + the UN GHS), a different shape (red-bordered diamond on white), and a different scope (chemical labelling). The Rattle catalogue exposes them under the `gefahrstoffe` folder for presentational convenience inside `safety_notice` blocks, but treating them as a 6th ISO 7010 category in a CE-conformity dossier is a normative error. The canonical container for chemical hazards is the dedicated `hp_statement` block under `rattle-ghs-statements`.

### ANSI Z535.6-2011 (R2017)

*Product safety information in product manuals, instructions, and other collateral materials.*

US equivalent / harmonised reference for signal words and product-manual safety messages. Used by Rattle's `safety_notice` block. Verify the current edition at the ANSI webstore before publication — the standard was last reaffirmed in 2017.

### IEC 60204-1:2018

*Safety of machinery — Electrical equipment of machines — Part 1: General requirements.*

Drives Section 5.4 (Electrical Installation) requirements.

### ISO 13849-1:2015

*Safety of machinery — Safety-related parts of control systems — Part 1: General principles for design.*

Performance Levels (PL) for safety functions. Cited in 2.9 / 6.4.

### IEC 62061:2021

*Safety of machinery — Functional safety of safety-related control systems.*

Safety Integrity Level (SIL) for safety functions. Cited in 2.9.

### VDI 2770:2020

*Operation of process plants — Minimum requirements for digital documentation packages of components.*

Defines `vdi2770:2020` digital handover packages — relevant when the technical documentation must be delivered as a structured ZIP.

### ISO/TR 22100-4:2018 *(Technical Report — guidance only, no presumption of conformity)*

*Safety of machinery — Relationship with ISO 12100 — Part 4: Guidance to machinery manufacturers for consideration of related IT-security (cyber security) aspects.*

Informs Section 2.9 (Functional Safety and IT Security). As a Technical Report rather than an EN-harmonised standard, ISO/TR 22100-4 cannot grant presumption of conformity. Once MVO applies, the recommended IT-security implementation references are **IEC 62443-3-3** (system security requirements) and **IEC 62443-4-1 / -4-2** (product-development lifecycle and component requirements); for radio-equipped machinery, **RED 2014/53/EU Delegated Regulation 2022/30** + **EN 18031-1/-2/-3** apply.

### ISO 15223-1:2021 *(medical devices)*

*Medical devices — Symbols to be used with information to be supplied by the manufacturer — Part 1: General requirements.*

Adds medical-device symbol set when MDR applies.

### ISO 20417:2021 *(medical devices)*

*Medical devices — Information to be supplied by the manufacturer.*

Defines the IFU content for MDR-scope devices.

---

## Decision matrix — which directive applies?

| Product type | Primary directive | Additional standards |
|---|---|---|
| Industrial machine (CNC, robot, conveyor) | MRL / MVO | ISO 20607, IEC/IEEE 82079-1, ISO 12100, IEC 60204-1, ISO 13849-1 |
| Standalone electrical appliance | LVD + EMCD | IEC/IEEE 82079-1, IEC 61010-1 |
| Medical device | MDR | ISO 20417, ISO 15223-1, IEC/IEEE 82079-1 |
| ATEX equipment | MRL/MVO + ATEX | EN 1127-1, ISO/IEC 80079-* |
| Pressure equipment | PED 2014/68/EU | EN 13445 series |
| Radio equipment | RED 2014/53/EU | EN 301 489, EN 300 328 |

**For every Rattle template:** ask the user (or read from the product's `meta`) which directive applies, and have section 12.1 generated from a per-directive content block.

---

## Original-language obligation

MRL Annex I §1.7.4.1 (and MVO equivalent):

> *The instructions must be drafted in one or more official Community languages. The expression "Original instructions" must appear on the language version(s) verified by the manufacturer or his authorised representative. […] When the original instructions do not exist in the official language(s) of the country where the machinery is to be used, a translation into that language(s) must be provided by the manufacturer […]. These translations must bear the words "Translation of the original instructions".*

**Practical effect.** Always tag the original-language version on the cover (`Originalbetriebsanleitung`) and in `sec-12-3-doc-status`. Translations get the marker `Übersetzung der Originalbetriebsanleitung` (DE) / `Translation of the original instructions` (EN). The `unlabeled-original-language` audit check enforces this.
