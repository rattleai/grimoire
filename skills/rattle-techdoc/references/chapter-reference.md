# Chapter reference — 15-chapter normative structure

This document is the canonical chapter and section list for every Rattle `doc_type=technical_doc` template. Slugs match the seed data in `app/utils/techdoc_seed_data.py` of rattleapp. The legacy alias `technical_documentation` is accepted on read-side filters (e.g. `GET /documents/templates?doc_type=technical_documentation`) but rejected on POST/PUT — always send `technical_doc` on writes. To inspect the live registry use `GET /documents/doc-types` (the route accepts no query parameters; filter the response client-side on `key=technical_doc`). Use this file as the master template every audit reconciles against.

Each chapter row shows: slug · title (DE/EN) · norm refs · key sections · mandatory content callouts.

> **Convention:** in the normative text the symbols mean: `▸` editorial guideline · `✎` example/suggested wording · `⚠` mandatory/legal · `◉` optional · `☛` cross-reference.

---

## Cover · `ch-00-cover`

**Title:** Deckblatt / Cover Page · **Norm refs:** ISO 20607 (5.1), IEC/IEEE 82079-1 (6.1) · **Required**

The first visual contact point. Must immediately identify product and manufacturer.

⚠ Mandatory content (ISO 20607 + MRL/MVO):

- Product / installation name (full commercial name)
- Type designation / model number (exactly as on nameplate)
- Product image (overall view)
- Manufacturer (name, full address, contact)
- CE marking (logo, notified-body number if applicable)
- Document title (e.g. "Originalbetriebsanleitung")
- Document number (unique internal ID)
- Issue date and revision (e.g. "Issue 2.0, January 2026")

◉ Optional: branche-specific marks (ATEX, GS, UL listing). Statement of original-language version.

✎ Example: *"Originalbetriebsanleitung – Portalfräsmaschine Typ PFM-3200 – Dokumentnr. BA-PFM3200-DE – Ausgabe 2.0, Januar 2026"*

---

## Table of Contents · `ch-00-toc`

**Title:** Inhaltsverzeichnis / Table of Contents · **Norm refs:** IEC/IEEE 82079-1 · **Required**

Auto-generated index of all chapters and sections with page numbers. Cap depth at 3 levels for readability on large documents.

---

## Chapter 1 · `ch-01-about-document`

**Title:** Zu diesem Dokument / About This Document · **Norm refs:** IEC/IEEE 82079-1 (6.1, 6.2), ISO 20607 (5.2)

| Section | Slug | Mandatory | Content |
|---|---|---|---|
| 1.1 Purpose and Scope | `sec-1-1-purpose` | ⚠ | Why this manual exists; the lifecycle phases it covers; its status as part of the product. |
| 1.2 Validity | `sec-1-2-validity` | ⚠ | Exact identification: variants, type names, serial-number range, software version. Use a table. |
| 1.3 Target Groups and Qualification | `sec-1-3-target-groups` | ⚠ | Define every user group + required qualification. Operator / Setter / Electrical specialist / Service / Transport. |
| 1.4 Structure and Use of This Document | `sec-1-4-document-structure` | ▸ | Tell the reader how to navigate (lifecycle order, colour tabs, index, QR codes). |
| 1.5 Related Documents | `sec-1-5-related-documents` | ▸ | List schematics, HMI manual, supplier docs. Provide doc numbers + storage location. |
| 1.6 Symbols, Signal Words, and Text Conventions | `sec-1-6-symbols` | ⚠ | The four-row signal-word legend (DANGER / WARNING / CAUTION / NOTICE) + every ISO 7010 category used + typographic conventions. **Mandatory per IEC/IEEE 82079-1:2019 §7.5 (warnings and warning messages), §7.6 (graphical and textual symbols), and ISO 3864-2:2016.** |
| 1.7 Terms and Abbreviations | `sec-1-7-terms` | ▸ | Short product-specific definitions; cross-link to glossary in 13.6. |
| 1.8 Provision Format and Digital Access | `sec-1-8-digital-access` | ◉ | MVO 2023/1230 prep: digital availability, URL/QR, offline copy, paper-on-demand within 30 days. |

⚠ The four signal words and their colours are normatively fixed (ISO 3864-2 Annex B / ANSI Z535.6):

| Signal word | Meaning | Colour |
|---|---|---|
| **DANGER** | imminent hazard → death or serious injury | Red |
| **WARNING** | possible hazardous situation → death or serious injury | Orange |
| **CAUTION** | possible hazardous situation → minor / moderate injury | Yellow |
| **NOTICE** | property damage or functional impairment possible | Blue |

---

## Chapter 2 · `ch-02-safety`

**Title:** Sicherheit / Safety · **Norm refs:** ISO 20607 (5), ISO 12100 (6.4), MRL Anh. I 1.7.4.2

This is the **normatively and legally most important chapter**. It must be read BEFORE any life-cycle chapter. Each life-cycle chapter (4–11) carries its own `.1` safety section for phase-specific hazards.

| Section | Slug | Mandatory | Content |
|---|---|---|---|
| 2.1 Intended Use | `sec-2-1-intended-use` | ⚠ | Exact, complete statement of what the product is for. ISO 12100 (3.23), ISO 20607 (5.3), MRL Anh. I 1.1.2 (a). |
| 2.2 Foreseeable Misuse | `sec-2-2-foreseeable-misuse` | ⚠ | Concrete misuse cases that are realistically expected. ISO 12100 (3.24), ISO 20607 (5.4). |
| 2.3 General Safety Instructions | `sec-2-3-general-safety` | ⚠ | Cross-cutting rules for ALL life-cycle phases. Read manual, do not bypass guards, observe markings, no unauthorised modifications, LOTO, only approved spare parts. |
| 2.4 Residual Hazards and Remaining Risks | `sec-2-4-residual-risks` | ⚠ | Table of hazards remaining despite design + safeguards. Direct output of risk assessment per ISO 12100. ISO 12100 (6.4.1), ISO 20607 (5.5). |
| 2.5 Protective Devices and Safety Systems | `sec-2-5-protective-devices` | ⚠ | Each guard, light curtain, e-stop, safety interlock — function, location, test interval. |
| 2.6 Personal Protective Equipment (PPE) | `sec-2-6-ppe` | ⚠ | What PPE for what task; reference to ISO 7010 mandatory-action signs (M-codes). |
| 2.7 Personnel Qualification and Responsibilities | `sec-2-7-personnel-qualification` | ⚠ | Who may do what; training plan; instruction obligations of the operator (employer). |
| 2.8 Structure and Design of Warnings | `sec-2-8-warning-structure` | ▸ | The SAFE principle: signal word → hazard type → consequences → avoidance. |
| 2.9 Functional Safety and IT Security | `sec-2-9-functional-safety` | ◉ | PL/SIL of safety functions per ISO 13849-1 / IEC 62061; cybersecurity for connected machines. |

---

## Chapter 3 · `ch-03-product-description`

**Title:** Produkt- und Systembeschreibung / Product and System Description · **Norm refs:** ISO 20607, IEC/IEEE 82079-1

| Section | Slug | Mandatory | Content |
|---|---|---|---|
| 3.1 Product Identification | `sec-3-1-identification` | ⚠ | Nameplate description, ID fields, where to find them. |
| 3.2 Operating Environment and Limits | `sec-3-2-environment` | ⚠ | Climate, altitude, lighting, foundation, supply tolerances. |
| 3.3 Functional Description | `sec-3-3-function` | ⚠ | What the product does, in plain language for the operator. |
| 3.4 Components and Assemblies | `sec-3-4-components` | ⚠ | Overview drawings; map of subsystems; references to detailed drawings. |
| 3.5 Operating Modes | `sec-3-5-operating-modes` | ⚠ | Manual / automatic / setup / service modes; selection mechanism; permissions. |
| 3.6 Interfaces and Networks | `sec-3-6-interfaces` | ◉ | Bus systems, network ports, cybersecurity boundary. |
| 3.7 Technical Data | `sec-3-7-technical-data` | ⚠ | Power, dimensions, weight, capacity, noise, vibration. Use a table; bind dynamic block where possible. |
| 3.8 Type Plate and Markings | `sec-3-8-type-plate` | ⚠ | Photograph of nameplate + every safety / instructional marking on the machine. |

---

## Chapter 4 · `ch-04-transport`

**Title:** Transport, Anlieferung und Lagerung / Transport, Delivery and Storage · **Norm refs:** ISO 20607 (Tab. 1)

⚠ Every life-cycle chapter starts with `.1 Safety` for phase-specific hazards.

| Section | Slug | Content |
|---|---|---|
| 4.1 Safety During Transport and Handling | `sec-4-1-transport-safety` | Tipping, crushing, impact damage; only trained personnel; hoists with sufficient capacity; pre-check transport routes. |
| 4.2 Incoming Goods Inspection | `sec-4-2-incoming-inspection` | What to check on delivery; transport-damage protocol; complaint deadlines. |
| 4.3 Transport Methods and Lifting Points | `sec-4-3-transport-methods` | Forklift / crane / pallet jack; clearly marked lifting eyes / centre-of-gravity; weight class. |
| 4.4 Transport and Packaging Markings | `sec-4-4-transport-markings` | ISO 7000 / ISO 780 packaging marks; what they mean. |
| 4.5 Storage Conditions | `sec-4-5-storage` | Climate range, humidity, vibration, light; preservation; max storage time before commissioning. |

---

## Chapter 5 · `ch-05-assembly`

**Title:** Montage und Installation / Assembly and Installation · **Norm refs:** ISO 20607, IEC 60204-1

| Section | Slug | Content |
|---|---|---|
| 5.1 Safety During Assembly and Installation | `sec-5-1-assembly-safety` | Phase-specific hazards: working at height, crushed limbs, energised tooling. Refer back to LOTO. |
| 5.2 Site Requirements | `sec-5-2-site-requirements` | Floor type, foundation, supply media, lighting, ambient. |
| 5.3 Mechanical Assembly | `sec-5-3-mechanical-assembly` | Step-by-step assembly with tool list, torque values, alignment tolerances. |
| 5.4 Electrical Installation | `sec-5-4-electrical-installation` | IEC 60204-1; only qualified electrician; PE / earthing; supply-side protection. |
| 5.5 Pneumatic / Hydraulic Connection | `sec-5-5-pneumatic-hydraulic` | Pressure, flow, fluid type, filter requirements. |
| 5.6 Network and IT Connection | `sec-5-6-network` | IP scheme, firewall, certificates; integrator hand-off. |
| 5.7 Installation Tests and Acceptance | `sec-5-7-acceptance` | Insulation test, leakage, function tests; acceptance protocol template (link to Appendix). |

---

## Chapter 6 · `ch-06-commissioning`

**Title:** Inbetriebnahme und Einstellungen / Commissioning and Settings · **Norm refs:** ISO 20607

| Section | Slug | Content |
|---|---|---|
| 6.1 Safety During Commissioning | `sec-6-1-commissioning-safety` | Unexpected motion; first-energise risks; clearance zones. |
| 6.2 Pre-Commissioning Checks | `sec-6-2-pre-checks` | Visual inspection, supply checks, safety-circuit test. |
| 6.3 Initial Commissioning Sequence | `sec-6-3-first-startup` | Step-by-step ignition; expected results at each step; abort criteria. |
| 6.4 Safety Function Verification | `sec-6-4-safety-function-test` | Test of every e-stop, light curtain, interlock; protocol template. |
| 6.5 Basic Settings and Calibration | `sec-6-5-basic-settings` | Default parameters; calibration procedure; tolerance limits. |
| 6.6 Recommissioning After Standstill | `sec-6-6-recommissioning` | Refresh of pre-commissioning checks; expected actions when standstill > X. |
| 6.7 Handover Protocol | `sec-6-7-handover` | Customer hand-off checklist; training acknowledgement. |

---

## Chapter 7 · `ch-07-operation`

**Title:** Bedienung und Betrieb / Operation · **Norm refs:** ISO 20607, IEC/IEEE 82079-1

| Section | Slug | Content |
|---|---|---|
| 7.1 Safety During Operation | `sec-7-1-operation-safety` | Phase-specific operator hazards. |
| 7.2 Controls and Operator Interface | `sec-7-2-controls` | Every button, lamp, screen page; HMI map. |
| 7.3 Operating Modes in Detail | `sec-7-3-modes-detail` | When to select which mode; permission level per mode. |
| 7.4 Startup and Shutdown | `sec-7-4-startup-shutdown` | Daily start; orderly shutdown; emergency shutdown. |
| 7.5 Normal Operation Procedures | `sec-7-5-normal-ops` | The actual day-to-day workflow. |
| 7.6 Changeover / Reset Procedures | `sec-7-6-changeover` | Format change, recipe change. |
| 7.7 Operating Faults Handled by the Operator | `sec-7-7-operator-faults` | Distinguish "operator-recoverable" vs "service required". |

---

## Chapter 8 · `ch-08-troubleshooting`

**Title:** Störungen und Fehlerbehebung / Troubleshooting · **Norm refs:** ISO 20607

| Section | Slug | Content |
|---|---|---|
| 8.1 Safety During Troubleshooting | `sec-8-1-troubleshooting-safety` | Bypass-mode hazards; LOTO; service-mode access. |
| 8.2 Error Messages and Codes | `sec-8-2-error-codes` | Full table of error codes with cause + remedy + qualification. |
| 8.3 Systematic Fault Finding | `sec-8-3-fault-finding` | Decision-tree procedures; tooling required. |
| 8.4 Restart After Fault | `sec-8-4-restart` | Acknowledgement procedure; safety function re-test before normal operation. |
| 8.5 Customer Service Contact | `sec-8-5-service-contact` | Phone, e-mail, hotline hours; what info to provide. |

---

## Chapter 9 · `ch-09-maintenance`

**Title:** Reinigung, Wartung, Inspektion und Reparatur / Cleaning, Maintenance, Inspection, Repair · **Norm refs:** ISO 20607, MRL Anh. I 1.6.1

| Section | Slug | Content |
|---|---|---|
| 9.1 General Safety Measures (Lockout/Tagout) | `sec-9-1-loto` | Cross-cutting LOTO procedure; **prime reuse candidate**. |
| 9.2 Maintenance and Inspection Concept | `sec-9-2-maintenance-concept` | Periodicity matrix; who does what when. |
| 9.3 Cleaning | `sec-9-3-cleaning` | Allowed cleaning agents, prohibited agents, frequency. |
| 9.4 Maintenance Tasks | `sec-9-4-maintenance-tasks` | Per-task procedure with photos / step lists. |
| 9.5 Inspection Tasks | `sec-9-5-inspection-tasks` | Visual / functional / metrological inspection tasks. |
| 9.6 Repair | `sec-9-6-repair` | Authorised vs. unauthorised repairs; spare-parts policy. |
| 9.7 Tests After Maintenance and Repair | `sec-9-7-post-maintenance-tests` | Post-repair safety function re-test; release for service. |
| 9.8 Maintenance Log | `sec-9-8-maintenance-log` | Template fields for date / activity / inspector / signature. |

---

## Chapter 10 · `ch-10-modifications` *(optional)*

**Title:** Umbauten, Erweiterungen, Modernisierung / Modifications, Extensions, Modernisation · **Norm refs:** ISO 20607, MVO (EU) 2023/1230 Art. 18

| Section | Slug | Content |
|---|---|---|
| 10.1 Permissible Modifications by the Operator | `sec-10-1-allowed-modifications` | What the operator may change without losing CE. |
| 10.2 Substantial Modifications under MVO 2023/1230 | `sec-10-2-substantial-modifications` | What triggers a re-evaluation; new CE / new declaration. |
| 10.3 Documentation Obligations | `sec-10-3-documentation-obligations` | Operator must document modifications. |

---

## Chapter 11 · `ch-11-decommissioning`

**Title:** Außerbetriebnahme, Demontage und Entsorgung / Decommissioning, Disassembly, Disposal · **Norm refs:** ISO 20607, ISO 12100

| Section | Slug | Content |
|---|---|---|
| 11.1 Temporary Decommissioning | `sec-11-1-temporary` | Standstill > X days; preservation; secure-against-restart. |
| 11.2 Permanent Decommissioning | `sec-11-2-permanent` | Final shutdown; document end-of-life. |
| 11.3 Disassembly | `sec-11-3-disassembly` | Disassembly sequence reverse of assembly; energy-source isolation first. |
| 11.4 Disposal — Materials and Components | `sec-11-4-disposal-materials` | Material-by-material disposal; WEEE for electronics; oil / coolant / refrigerant. |
| 11.5 Hazardous Substances | `sec-11-5-hazardous-substances` | List with H/P statements (`hp_statement` blocks). |

---

## Chapter 12 · `ch-12-conformity`

**Title:** Konformität, Normen und rechtliche Hinweise / Conformity, Standards and Legal · **Norm refs:** ISO 20607, IEC/IEEE 82079-1, MRL Anh. I+II

| Section | Slug | Content |
|---|---|---|
| 12.1 Applied Directives and Regulations | `sec-12-1-directives` | ⚠ Every directive / regulation that applies (MRL, MVO, LVD, EMCD, ATEX, RED, MDR, …). |
| 12.2 Applied Harmonised Standards | `sec-12-2-standards` | Full list of applied standards with year + clause where relevant. |
| 12.3 Documentation Status | `sec-12-3-doc-status` | Original-language version statement; revision history; archive obligation. |
| 12.4 Liability and Warranty | `sec-12-4-liability` | Manufacturer liability disclaimer; warranty terms. |
| 12.5 Copyright | `sec-12-5-copyright` | Copyright notice; reproduction restrictions. |

---

## Chapter 13 · `ch-13-appendix`

**Title:** Anhang / Appendix · **Norm refs:** ISO 20607, IEC/IEEE 82079-1, MRL

| Section | Slug | Content |
|---|---|---|
| 13.1 EC/EU Declaration of Conformity | `sec-13-1-declaration` | ⚠ Mandatory per MRL Anhang II A. Original document or true copy. |
| 13.2 Technical Data (Detailed) | `sec-13-2-tech-data-detail` | Detailed performance / consumption / sound levels. |
| 13.3 Spare and Wear Parts Lists | `sec-13-3-spare-parts` | Pos. / drawing ref / part-no / location / remark. Order info. |
| 13.4 Drawings, Plans, Diagrams | `sec-13-4-drawings` | Electrical, pneumatic, hydraulic, layout, foundation drawings. Each with doc-no + revision. |
| 13.5 Checklists and Protocols | `sec-13-5-checklists` | Assembly completion, commissioning, safety function test, handover, periodic maintenance. |
| 13.6 Glossary and List of Abbreviations | `sec-13-6-glossary` | Alphabetical; abbreviations spelled out. |
| 13.7 Index | `sec-13-7-index` | Mandatory > 50 pages; safety terms, component names, error codes. |

---

## Reusable content-block candidates

These appear (with minor wording variation) in nearly every product manual. Build them once at company level (`product_id=null`) and attach them to every product's template.

| Key | Title (DE) | Reusability | Attach to |
|---|---|---|---|
| `signal-words-legend` | Signalwörter und Symbole | high | `ch-01-about-document.sec-1-6-symbols` |
| `target-groups-default` | Zielgruppen und Qualifikation | high | `ch-01-about-document.sec-1-3-target-groups` |
| `general-safety-rules` | Allgemeine Sicherheitshinweise | high | `ch-02-safety.sec-2-3-general-safety` |
| `loto-procedure` | Lockout/Tagout-Verfahren | high | `ch-09-maintenance.sec-9-1-loto` |
| `ppe-default` | Persönliche Schutzausrüstung (PSA) | medium | `ch-02-safety.sec-2-6-ppe` |
| `disposal-electronics-weee` | Entsorgung Elektronik (WEEE) | high | `ch-11-decommissioning.sec-11-4-disposal-materials` |
| `glossary-machine-default` | Glossar — Maschinenbau | high | `ch-13-appendix.sec-13-6-glossary` |
| `warning-structure-safe` | Aufbau Warnhinweise (SAFE-Prinzip) | high | `ch-02-safety.sec-2-8-warning-structure` |
| `digital-access-mvo` | Digitale Bereitstellung (MVO) | high | `ch-01-about-document.sec-1-8-digital-access` |
| `applied-directives-machine` | Angewandte Richtlinien (Maschine) | medium | `ch-12-conformity.sec-12-1-directives` |
