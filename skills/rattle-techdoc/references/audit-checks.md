# Technical-documentation audit checks

Twelve structural checks every Rattle `doc_type=technical_documentation` template (and every input PDF/Word manual being inventoried) must pass before publication. The shape mirrors the configurator audit — same `id`, `severity`, `evidence`, `correction` fields — so a single tooling pipeline can ingest both kinds of findings.

Findings are emitted against `schemas/audit-findings.schema.json` (the existing schema is reused; `domain: "techdoc"` distinguishes from configurator findings).

> **Severity ladder.** `CRITICAL` blocks publication and CE-conformity assertion. `HIGH` is a legal gap that should be fixed before customer hand-off. `MEDIUM` is a maintainability concern. `LOW` is editorial polish.

---

## 1 · `missing-safety-chapter` *(CRITICAL)*

**Definition.** No structure block with `slug=ch-02-safety` exists, OR the chapter exists but contains zero attachments.

**Why CRITICAL.** Safety information is mandatory under MRL Anhang I 1.7.4.2, ISO 20607 (5), and ISO 12100 (6.4). Absence is a CE-conformity gap.

**Detection.** Walk the structure tree. If no `node_type=chapter` block has `slug=ch-02-safety`, raise. If it exists but has empty `sections[]` and empty `attachments[]`, raise.

**Correction.** Insert the canonical Chapter 2 with all nine sections (`sec-2-1-intended-use` … `sec-2-9-functional-safety`). Use the scaffold in `chapter-reference.md`.

---

## 2 · `missing-phase-safety-section` *(CRITICAL)*

**Definition.** Any life-cycle chapter (`ch-04-transport` through `ch-11-decommissioning`) is missing its `.1` safety section.

**Why CRITICAL.** Each life-cycle phase must carry phase-specific safety information per ISO 20607 (5.5).

**Detection.** For each life-cycle chapter, check that a child structure block exists whose `slug` ends in `-safety` and `order_index=0`. Specifically: `sec-4-1-transport-safety`, `sec-5-1-assembly-safety`, `sec-6-1-commissioning-safety`, `sec-7-1-operation-safety`, `sec-8-1-troubleshooting-safety`, `sec-9-1-loto`, `sec-10-1-...`, `sec-11-1-temporary` (the LOTO section in 9 carries the phase-specific safety role).

**Correction.** Insert the phase-specific safety section as the first child of the chapter, with a content block that lists phase-specific hazards and refers back to Chapter 2 for cross-cutting rules.

---

## 3 · `missing-residual-risks-table` *(CRITICAL)*

**Definition.** Section `sec-2-4-residual-risks` exists but contains no `table` EditorJS block (or contains only narrative paragraphs without a tabular hazard list).

**Why CRITICAL.** ISO 12100 (6.4.1) and ISO 20607 (5.5) require residual hazards to be listed with location / life-cycle phase / user mitigation. Tabular form is the standard expectation.

**Detection.** Section locale `block_json` must contain ≥ 1 `{type: "table"}` block whose first row contains a header column matching `/restgefahr|residual hazard|hazard|risk/i`.

**Correction.** Insert a table with columns: *Residual hazard* · *Location / Life-cycle phase* · *User mitigation*.

---

## 4 · `missing-signal-words-legend` *(HIGH)*

**Definition.** Section `sec-1-6-symbols` exists but its content has no four-row table with rows for DANGER / WARNING / CAUTION / NOTICE.

**Why HIGH.** Mandatory per IEC/IEEE 82079-1 (6.4, 6.5) and ISO 3864-2. Without it, signal words used elsewhere in the manual are not legally interpretable.

**Detection.** Section locale `block_json` must contain a `{type: "table"}` whose rows include all four signal words (case-insensitive, in the section locale).

**Correction.** Insert the four-row legend table from `chapter-reference.md` Chapter 1, plus rows for every ISO 7010 category actually used in the manual.

---

## 5 · `missing-target-groups-matrix` *(HIGH)*

**Definition.** Section `sec-1-3-target-groups` exists but contains no `table` EditorJS block.

**Why HIGH.** ISO 20607 (5.2) and IEC/IEEE 82079-1 (5.2, 6.2) require explicit target groups + required qualification.

**Detection.** Section locale `block_json` must contain a `{type: "table"}` with columns covering at minimum *target group* and *qualification*.

**Correction.** Insert the canonical 5-row target-groups matrix (Operator / Setter / Electrical / Service / Transport).

---

## 6 · `missing-declaration-of-conformity` *(CRITICAL)*

**Definition.** Section `sec-13-1-declaration` is absent, OR present but contains no usable text (placeholder only).

**Why CRITICAL.** MRL Anhang II A makes the EC/EU Declaration of Conformity mandatory. Without it, the product cannot legally be placed on the EU market.

**Detection.** Section locale `block_json` must contain at least one paragraph or attached image / file mentioning the EC/EU declaration text. A "TODO" / "FIXME" placeholder is treated as missing.

**Correction.** Either embed a static block with the declaration template, or attach a system dynamic block (`dynamic:document_declaration_of_conformity` if present) bound to the company's declaration data.

---

## 7 · `missing-disposal-section` *(HIGH)*

**Definition.** Chapter `ch-11-decommissioning` is absent, OR its `.4 Disposal` section is empty.

**Why HIGH.** ISO 20607 (Tab. 1) lists end-of-life information as required. WEEE Directive (2012/19/EU) may also require electronic-disposal information.

**Detection.** No `sec-11-4-disposal-materials` block, or the block has no attachments / no usable content.

**Correction.** Insert the disposal section. Reuse the `disposal-electronics-weee` content block if available.

---

## 8 · `unstructured-warnings` *(HIGH)*

**Definition.** A content block contains a `{type: "warning"}` EditorJS block whose `data.title` is missing OR whose level is not one of `danger / warning / caution / notice`. The frontend warning block (used for editorial notes) is allowed; the safety-relevant one must be a `safety_notice` block.

**Why HIGH.** Mandatory per ISO 3864-2 / IEC/IEEE 82079-1: every safety-relevant warning needs an explicit signal-word level.

**Detection.** Walk every content block locale's `block_json`. Flag every `{type: "warning"}` whose body looks safety-relevant (contains keywords: `gefahr|warn|caution|achtung|vorsicht|danger|hazard|injury|verletz|tod|fatal`) but has no `safety_notice` peer.

**Correction.** Convert to a `{type: "safety_notice"}` block with proper level, hazard description, consequences, avoidance, and ISO 7010 symbol. See `rattle-safety-notices/SKILL.md`.

---

## 9 · `non-normative-warning-words` *(MEDIUM)*

**Definition.** A content block uses non-normative warning words: "Achtung!", "Wichtig!", "ATTENTION", "Important", "WARNING:" inline in a paragraph instead of as a `safety_notice` block with the correct level.

**Why MEDIUM.** ISO 3864-2 expects DANGER / WARNING / CAUTION / NOTICE. "Achtung" maps approximately to "VORSICHT" but is non-normative.

**Detection.** Regex against paragraph text: `/^(achtung|wichtig|attention|important|note)[!:]/i` followed by a hazard-keyword sentence.

**Correction.** Convert to `safety_notice` with the appropriate level. If non-safety-related (purely editorial), keep as `paragraph` and remove the bold "Achtung!".

---

## 10 · `addressless-pictogram` *(MEDIUM)*

**Definition.** An ISO 7010 / GHS pictogram appears in an `image` EditorJS block (or as inline HTML) without a code reference (W-code / P-code / M-code / E-code / F-code / GHSXX).

**Why MEDIUM.** IEC/IEEE 82079-1 (6.5) and ISO 7010 require traceable identification of safety symbols.

**Detection.** Check every `image` URL whose path contains `/safety_logos/` or `/ghs/` against the alt text or surrounding paragraph for a code reference. Flag if absent.

**Correction.** Convert to a `safety_notice` block (preferred) or add the code reference inline.

---

## 11 · `unlabeled-original-language` *(MEDIUM)*

**Definition.** No statement in the document declares which locale is the original-language version (per MRL Anhang I 1.7.4.1).

**Why MEDIUM.** MRL/MVO require the original-language version to be marked "Originalbetriebsanleitung" (or equivalent) and translations to be marked "Übersetzung der Originalbetriebsanleitung".

**Detection.** Search the cover (`ch-00-cover`) and `sec-12-3-doc-status` for the regex `/original|übersetzung der original|translation of the original/i`. Flag if absent.

**Correction.** Add the statement on the cover and in section 12.3.

---

## 12 · `missing-validity-section` *(HIGH)*

**Definition.** Section `sec-1-2-validity` is absent or contains no identifying information (variant names, serial-number range, software version).

**Why HIGH.** ISO 20607 (5.2) requires explicit identification of which machines the manual applies to.

**Detection.** Section locale `block_json` must contain a `paragraph` mentioning a serial-number / type-number / version pattern, OR a `table` with a "Variant" / "Serial" / "Version" header.

**Correction.** Insert the validity table from `chapter-reference.md` Chapter 1.

---

## Aggregate audit output

```json
{
  "audit_id": "techdoc-pfm3200-2026-05-09T10:30:00Z",
  "domain": "techdoc",
  "template_id": 4711,
  "template_name": "PFM-3200 — Originalbetriebsanleitung",
  "doc_type": "technical_documentation",
  "checked_at": "2026-05-09T10:30:00Z",
  "summary": {
    "checks_run": 12,
    "critical": 1,
    "high": 2,
    "medium": 1,
    "low": 0,
    "passed": 8
  },
  "findings": [
    {
      "check_id": "missing-residual-risks-table",
      "severity": "CRITICAL",
      "structure_block_id": 23415,
      "structure_slug": "sec-2-4-residual-risks",
      "evidence": "Section sec-2-4-residual-risks has 2 paragraphs but no table block.",
      "correction": "Insert table with columns: Residual hazard / Location / Life-cycle phase / User mitigation. See chapter-reference.md Chapter 2."
    }
  ]
}
```
