---
name: rattle-pricelist-analysis
description: Use this skill when the user wants to analyse a pricelist, technical document, product spec, or feature catalogue for Rattle configurator anti-patterns BEFORE building or restructuring a configuration. Detects implicit-base-config, addon-only-options, narrative-area smell, addon-only-software-modules, and per-unit-priced-row (per-metre / per-piece pricing that must become a NUMBERED option). Combines deterministic keyword detection with LLM-driven structural analysis. Pair with rattle-configurator (loads automatically when this is active) and rattle-suggest-config (the next step after analysis).
license: MIT
---

# Rattle pricelist analysis

The first step of every consulting engagement: read the user's input (Excel pricelist, PDF spec, Word document, or pasted text) and surface every anti-pattern before any group/option restructuring is proposed. Anti-patterns found here become the instructions to `rattle-suggest-config` in the next step.

## When to use this skill

- The user provides an Excel/PDF/Word pricelist or a block of pasted text and asks "what's wrong with this?", "is this configurator-ready?", "find the issues", or "analyse this for me".
- The user is about to start building a new product configuration and has source material.
- The user wants a quick second-opinion read before a customer call.

If the input is structured tenant data (already in Rattle) rather than a pricelist, use `rattle-configurator/references/structural-checks.md` and the audit workflow instead.

## Workflow

1. **Load the configurator skill if not already loaded.** This skill assumes `rattle-configurator/references/anti-patterns.md` and `configuration-rules.md` are available. They contain the indicator keywords and rule rationales.

2. **Run deterministic detection first.** For Excel/CSV inputs, run `scripts/detect_anti_patterns.py <file>` (or replicate the logic in any language). This walks every row × column and reports every cell whose value contains an anti-pattern indicator keyword. Output is a list of dicts with `pattern_id`, `row_index`, `column`, `value`, `indicator`, `correction`. Deterministic, no LLM, always cheap to run.

3. **Run structural / LLM analysis second.** For the things keywords miss (mixed feature lists, implicit assumptions in narrative prose, hierarchy mistakes), feed the input to an LLM with the prompt assembled by `system_prompt_analyse_pricelist` (documented in `rattle-configurator/references/system-prompts.md`). The Python entry point is `from rattle_api.tasks import analyse_pricelist; analyse_pricelist(tenant, source_file, language='de')`.

4. **Merge findings.** Deterministic findings have row/column anchors; LLM findings cite sections by name. Group both by `pattern_id` and present in priority order:
   - `implicit-base-config` (highest — always blocks correct configuration)
   - `addon-only-options`
   - `addon-only-software-modules`
   - `per-unit-priced-row` (the feature is a quantity, not a variant — it must become a numbered option)
   - `description-area-smell` (signals narrative-vs-configuration confusion)

   **The per-unit heuristic.** Per-metre / per-piece / per-unit pricing appearing as **its own pricelist row** ("Panel, pro Stück: 120€"; "Kabel, €/m: 8,50") is the signal that the feature is a **numbered option** (`is_numbered: true`), not a discrete option. Test it by asking: *would modelling this as discrete options force me to enumerate "1 ×, 2 ×, 3 × …"?* If yes, it is `per-unit-priced-row`. The keyword scan catches the obvious rows; the LLM pass must also catch the ones that state a unit price without a unit keyword (a row whose quantity column is open-ended, or a spec line reading "brackets: 3 per panel"). Report the required `number_min` / `number_max` / `number_step` / `number_unit` as the blocking question — the pricelist almost never states the bounds.

5. **Report with action items.** For each finding, output:
   - Pattern id and name (`implicit-base-config`)
   - Where it appears (row 7 column "Standard" / "section 2.1 Mechanik")
   - The correction shape (link to the matching example in `rattle-configurator/references/anti-patterns.md`)
   - The question that needs answering before fixing (e.g. "What is the actual standard wheel size?" — pricelists often elide this)

6. **Hand off to `rattle-suggest-config`.** When the user is ready to act on the findings, the next skill takes the merged findings + the original pricelist and produces a BOM-aware configuration JSON.

## Output contract

```json
{
  "products": [{"name": "...", "description": "...", "base_price": 0}],
  "features": [{"name": "...", "variants": [], "pricing": "..."}],
  "anti_patterns": [
    {
      "pattern_id": "implicit-base-config",
      "evidence": "Row 7, column 'Standard': 'Standard 17-inch wheels'",
      "indicator": "standard",
      "correction": "Create explicit Wheels group with 17-inch and 19-inch options.",
      "blocking_question": "What is the actual standard wheel size — 17 or 18?"
    }
  ],
  "recommendations": [
    "Restructure 'Frässpindel' as a single group with all three variants explicit."
  ]
}
```

## Bundled scripts

- `scripts/detect_anti_patterns.py` — deterministic scanner. Reads a list-of-dicts JSON or an Excel file (via openpyxl) and returns the findings list described above. Runs without network or AI keys.

## How this maps to the existing CLI

The Python CLI provides:

```bash
rattle <tenant> ai-analyse-pricelist source/<tenant>/pricelist.xlsx --language de
```

That command runs the full LLM analysis with the assembled `system_prompt_analyse_pricelist` and tenant memory injected. Use it when you want the canonical reference behaviour. This skill captures the *workflow* so any AI client (Claude.ai, Cursor, Codex, custom MCP server) can reproduce it without the CLI.

## Related skills

- `rattle-configurator` — the consulting knowledge backing every finding.
- `rattle-suggest-config` — the next step: turn findings into a configuration recommendation.
- `rattle-api` — only needed if the user wants to push results back to the live tenant.
