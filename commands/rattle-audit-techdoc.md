---
description: Audit a Rattle technical documentation (`doc_type=technical_doc` — write canonical; legacy alias `technical_documentation` accepted on filters only) — or a stack of input manuals — for compliance with DIN EN ISO 20607, IEC/IEEE 82079-1, ISO 12100, MRL/MVO, ISO 3864-2, ISO 7010, CLP. Runs 14 structural checks plus the safety-notice, H/P-statement, and language-quality rule sets. Read-only.
argument-hint: <tenant> <template-id-or-input-dir> [--language de|en] [--severity critical,high,medium,low]
---

# /rattle-audit-techdoc

Audit the technical documentation at `$ARGUMENTS`.

## Workflow

1. **Spawn the auditor agent.** Delegate to `rattle-techdoc-auditor`. It loads the host skill (`skills/rattle-techdoc/SKILL.md`) plus the safety-notices, GHS, and language sister skills.

2. **Establish scope.**
   - **Live template** — fetch via `GET /documents/templates/{id}/resolve`. Walk every chapter, section, content-block locale.
   - **Input manual(s)** — run `python skills/rattle-techdoc/scripts/inventory_techdocs.py` first; treat detected chapters as the structure tree.
   - **Mixed batch** — audit per-file and aggregate.

3. **Run all checks** — total ~30:
   - **12 structural checks** (`audit-checks.md`): missing-safety-chapter, missing-phase-safety-section, missing-residual-risks-table, missing-signal-words-legend, missing-target-groups-matrix, missing-declaration-of-conformity, missing-disposal-section, unstructured-warnings, non-normative-warning-words, addressless-pictogram, unlabeled-original-language, missing-validity-section.
   - **Safety-notice rules** (`rattle-safety-notices/SKILL.md`): wrong-level-for-severity, incomplete-safe-structure, unmatched-iso-symbol, plus 3 above.
   - **H/P-statement rules** (`rattle-ghs-statements/SKILL.md`): inline-hp-text, unknown-hp-code, untranslated-hp-resolved-text.
   - **Language-quality rules** (`rattle-techdoc-language/SKILL.md`): quality-violation:* (clarity / accuracy / completeness / conciseness / consistency / currency), mood:non-imperative-instruction, original-language-obligation:missing-marker, audience-mismatch.

4. **Score every finding.**
   - `severity`: CRITICAL (blocks publication / CE-conformity) / HIGH (legal-gap) / MEDIUM (maintainability) / LOW (editorial).
   - `evidence`: a quote or block-id pointer.
   - `correction`: one-line action.

5. **Emit the report.** Use `schemas/audit-findings.schema.json` shape with `domain: "techdoc"` (see `agents/rattle-techdoc-auditor.md` for the example).

6. **Order findings.** CRITICAL first, then HIGH, MEDIUM, LOW.

## Filtering

Optional `--severity` argument filters the report. Default: all severities. `--severity critical,high` produces only the CE-blocking and legal-gap findings.

## Hand-off

The audit is read-only. To fix the findings:

1. The user reviews the audit JSON.
2. For each finding, either:
   - Approve the proposed `correction` → spawn `rattle-techdoc-author` to draft the fix as new EditorJS blocks / structure operations.
   - Reject → annotate the finding with a `notes` reason and re-run the audit against a future revision.
3. Approved corrections go to `rattle-config-builder` for idempotent application.

The auditor never writes to the API or the local file system itself.

$ARGUMENTS
