# Legal and normative basis for technical documentation

Reference of the directives, regulations, and standards every Rattle technical documentation must satisfy. Use this when the user asks "what does the law actually require?" or when an audit flags a CRITICAL finding tied to legal compliance.

> **Triage rule.** Always distinguish *legally binding* (Directive / Regulation / national law) from *technically harmonised* (CEN / CENELEC / IEC / ISO). Standards become legally binding only when explicitly listed in the Official Journal of the EU or the national equivalent. Compliance with a harmonised standard yields *presumption of conformity* — not automatic conformity.

---

## EU directives and regulations (legally binding)

### Maschinenrichtlinie 2006/42/EG · Machinery Directive

Applicable until **20 January 2027**, then superseded by MVO 2023/1230.

| Annex / clause | Documentation requirement |
|---|---|
| Annex I, §1.7.4 | Information for use must accompany the machine. |
| Annex I, §1.7.4.1 | Original instructions in an official EU language; translations marked "Translation of the original instructions". |
| Annex I, §1.7.4.2 (a-x) | 24 explicit content requirements (intended use, residual risks, transport, installation, operation, maintenance, decommissioning, …). |
| Annex II, §1.A | EC Declaration of Conformity content requirements. |
| Annex VII | Technical file content requirements. |

**Practical effect on Rattle.** The 15-chapter structure exactly satisfies Annex I §1.7.4.2. Chapter 13.1 holds the Declaration. Chapter 12.1 lists every applied directive.

### Maschinenverordnung (EU) 2023/1230 · Machinery Regulation

Replaces MRL from **20 January 2027**. Already binding for products placed on the market on or after that date. Several practical updates:

| Article / annex | What it changes |
|---|---|
| Art. 10 | Information requirements clarified; product identification, traceability. |
| Art. 18 | "Substantial modifications" trigger re-conformity assessment + new CE; affects Chapter 10 of every existing manual. |
| Annex III, §1.7.4 | Digital provision of instructions allowed; must remain available "for the expected lifetime" (≥ 10 years), with offline copies and **paper version free within 30 days on request**. |
| Annex IV (1.A) | EU Declaration of Conformity replaces EC Declaration. |

**Practical effect on Rattle.** Section `sec-1-8-digital-access` and Section `sec-12-1-directives` need updating before 2027 cut-over. Chapter 10 needs the substantial-modifications definition.

### Niederspannungsrichtlinie 2014/35/EU · Low Voltage Directive

Applicable to electrical equipment in 50–1000 V AC / 75–1500 V DC range. If a machine is also LVD-scope, list it in Section 12.1.

### EMV-Richtlinie 2014/30/EU · EMC Directive

Electromagnetic compatibility. List in Section 12.1 when applicable.

### ATEX 2014/34/EU · Equipment for Explosive Atmospheres

If applicable: explicit ATEX category, marking on cover and nameplate, dedicated chapter or annex with the conditions of safe use.

### MDR (EU) 2017/745 · Medical Device Regulation

For medical devices, replaces "Betriebsanleitung" with "Instructions for Use" (IFU). The 15-chapter structure still applies but with these additions:

- ISO 15223-1 symbols mandatory in addition to ISO 7010.
- ISO 20417 for IFU content.
- Unique Device Identifier (UDI) on cover.

### CLP Regulation (EC) 1272/2008

Classification, Labelling, and Packaging of substances and mixtures. Source for H-statements / P-statements / EUH-statements / GHS pictograms. See `rattle-ghs-statements/references/legal-basis.md`.

### REACH (EC) 1907/2006

Where the manual references chemical substances, REACH SDS reference may be required.

### WEEE Directive 2012/19/EU

Disposal of electrical / electronic equipment. Drives the `disposal-electronics-weee` content block.

---

## Harmonised standards (presumption of conformity)

These are the standards that every technical-documentation skill in this workspace cites. All are **expectations** the audit checks enforce.

### DIN EN ISO 20607:2019

*Safety of machinery — Instructions for use — General drafting principles.*

The single most important standard for the structure of every operating manual. Defines:

- Tab. 1 — Required information per life-cycle phase. Maps 1:1 to the 15-chapter structure.
- §5.1–5.5 — Cover page, validity, target groups, intended use, residual risks.
- §5.6 — Construction, format, language, accessibility.

**This is what the chapter structure is built around.**

### IEC/IEEE 82079-1:2019

*Preparation of information for use (instructions for use) of products — Part 1: Principles and general requirements.*

The cross-industry meta-standard. Defines:

- §5.2 — Target audience analysis.
- §6 — Content requirements (purpose, scope, identification, terminology).
- §6.4 — Warnings and signal words. Mandatory cross-reference with ISO 3864-2 / ANSI Z535.
- §6.5 — Symbols and graphical elements.
- §7 — Quality criteria (clarity, accuracy, completeness, conciseness, consistency, currency).
- §8 — Process for producing IFU.

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

The catalogue of ~200 registered safety signs across six categories: warning (W), prohibition (P), mandatory action (M), safe condition (E), fire protection (F), and (cross-listed in `gefahrstoffe`) chemical hazard. See `rattle-safety-notices/references/iso-7010-symbols.md`.

### ANSI Z535.6:2023

*Product safety information in product manuals, instructions, and other collateral materials.*

US equivalent / harmonised reference for signal words. Used by Rattle's `safety_notice` block.

### IEC 60204-1:2016

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

### ISO/TR 22100-4:2018

*Safety of machinery — Relationship with ISO 12100 — Part 4: Guidance to machinery manufacturers for consideration of related IT-security (cyber security) aspects.*

Drives Section 2.9 (Functional Safety and IT Security).

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
