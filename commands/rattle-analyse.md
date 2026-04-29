---
description: Analyse a Rattle pricelist or product spec for configurator anti-patterns (implicit-base-config, addon-only-options, narrative-area smell, addon-only-software-modules). Combines deterministic keyword detection with LLM structural analysis.
argument-hint: <file path | tenant + source filename>
---

# /rattle-analyse

Analyse the input the user names (`$ARGUMENTS`) for Rattle configurator anti-patterns and produce a prioritised findings list.

## Workflow

1. **Load context** — Read `skills/rattle-pricelist-analysis/SKILL.md` and `skills/rattle-configurator/references/anti-patterns.md`. They are the source of truth for indicator keywords and corrections.

2. **Identify the input** — Common shapes:
   - Absolute or relative file path (Excel, JSON, PDF, Word, plain text).
   - `<tenant> <filename>` → resolve to `source/<tenant>/<filename>`.
   - Pasted text in the user's message.

3. **Run deterministic detection** — For Excel/JSON inputs, prefer:
   ```
   python skills/rattle-pricelist-analysis/scripts/detect_anti_patterns.py <path>
   ```
   For other formats, replicate the substring-indicator logic from `skills/rattle-configurator/references/anti-patterns.md`.

4. **Run LLM structural analysis** — When available, call:
   ```
   rattle <tenant> ai-analyse-pricelist <source-relative-path> --language de
   ```
   Otherwise compose the prompt described in `skills/rattle-configurator/references/system-prompts.md` § `system_prompt_analyse_pricelist` and call your AI provider directly.

5. **Merge and report** — Group findings by `pattern_id`, prioritise `implicit-base-config` first, then `addon-only-options`, `addon-only-software-modules`, `description-area-smell`. For each finding, output the evidence, the indicator that matched, and the correction shape from `anti-patterns.md`.

6. **Hand off** — Suggest `/rattle-suggest-config` as the next step if the user wants concrete recommendations.

## Delegation

For deep analysis with multi-file context, delegate to the `rattle-consultant` subagent with the input path and tenant name.

$ARGUMENTS
