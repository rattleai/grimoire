---
description: Map a customer's raw file (Excel, CSV, ERP export, Stückliste, PDF pricelist) onto Rattle entities. Profiles every column deterministically, classifies it into one of 24 column roles, detects the sheet shape, and emits a reviewable source-mapping.json + normalized rows. Surfaces missing standard variants as blockers instead of inventing them.
argument-hint: <file path | tenant + source filename>
---

# /rattle-ingest

Ingest the raw source the user names (`$ARGUMENTS`) and produce a reviewable column mapping. This is the **first link** in the chain — nothing downstream can run until the file has been mapped.

## Workflow

1. **Load context** — Read `skills/rattle-ingest/SKILL.md`, `skills/rattle-ingest/references/column-roles.md`, and `skills/rattle-ingest/references/sheet-shapes.md`. They are the source of truth for the 24 column roles, the 5 sheet shapes, and the confidence rules.

2. **Identify the input** — Common shapes:
   - Absolute or relative file path (`.xlsx`, `.xlsm`, `.csv`, `.json`, `.pdf`, `.docx`).
   - `<tenant> <filename>` → resolve to `source/<tenant>/<filename>`.
   - Pasted table in the user's message → write it to a temp `.csv` first, then profile it.

3. **Profile deterministically** — Never eyeball the headers. Run:
   ```
   python3 skills/rattle-ingest/scripts/profile_source.py <path> [--sheet NAME]
   ```
   Returns, per column: dtype, non-null count, cardinality, value samples, numeric stats, and a ranked `candidate_roles` list with confidence scores — plus a `sheet_shape` guess with its evidence. For PDF/Word, extract text via `rattle_api.source.read_source()`, reconstruct the implied table, and profile that.

4. **Classify and detect the shape** — Turn the profiler's proposal into decisions. Confidence `< 0.60` → `review_required: true` + a `low-confidence-mapping` warning. Any mapping that invents structure the source does not state (a wide-matrix pivot's `group_name`) → `review_required: true` regardless of confidence. Never drop a column silently: it goes in `columns[]` or in `unmapped_columns[]` with a reason.

5. **Enforce the #1 rule at the door** — A surcharge column or row-set with **no zero-priced / standard sibling** is `implicit-base-config` (or `addon-only-options` / `addon-only-software-modules`). Emit a `missing-standard-variant` blocker with a **placeholder + the blocking question**. Do **not** invent the standard option, its price, or its part number.

6. **Emit and confirm** — Write `source-mapping.json` (validates against `schemas/source-mapping.schema.json`), present it to the user, and get explicit confirmation of the roles, the `derived.group_name` values, and every `is_multi` decision **before** normalizing.

7. **Normalize** — Only after confirmation. Emit `normalized-rows.json`: a JSON array of flat objects keyed by role id, with `record_type` ∈ `product | option | bom_line` and `_source_row` / `_source_column` provenance on every row.

8. **Hand off** — Report blockers first, warnings second, the mapping last. Then:
   - `blockers[]` non-empty → **stop.** Answer the questions with the customer and re-ingest.
   - Clean → `/rattle-analyse normalized-rows.json`, then `/rattle-suggest-config`.
   - Sheet shape `one-row-per-bom-line` → `/rattle-build-bom` instead; a BOM cannot be wired before the options exist.

## Delegation

For a large or multi-sheet source, delegate to the `rattle-consultant` subagent with the file path and tenant name. Ingestion is read-only — never hand a source file to `rattle-config-builder`.

$ARGUMENTS
