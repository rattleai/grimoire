# System prompts — full reference

Mirror of the `system_prompt_*` builders in `rattle_api/knowledge.py`. Each section below describes one prompt, the inputs that shape it, and the JSON output contract the downstream caller expects. Use these as the canonical prompt set when integrating any LLM (Anthropic, OpenAI, Ollama, custom HTTP) with the Rattle consulting workflow — the Python CLI uses these too, so behaviour stays consistent.

A prompt always has three layers, in order:

1. **Base layer** (`system_prompt_base`) — Rattle data model summary + the #1 rule + 12 configuration rules + 4 anti-pattern names. **Every** task prompt prefixes this.
2. **Tenant layer** (optional) — `## Tenant preferences` block injected from `memory/<tenant>/profile.md` plus the last 5 decisions. Overrides defaults where they conflict.
3. **Task layer** — the specific instruction (analyse pricelist, suggest config, build offer template, audit findings, apply config).

---

## Base layer

`system_prompt_base(tenant_profile=None)` → string.

Always includes:

- A statement of the consultant's role (Rattle product configurator expert).
- A compact data-model recap: `Product → Areas → Groups → Options`, parts + BOM with `usage_subclauses`, constraints, documents.
- The **#1 rule** with the wheels example (wrong vs correct).
- The full list of `CONFIGURATION_RULES` rendered as numbered bullets `1. **<id>**: <rule text>`.
- The first five indicator keywords for each `ANTI_PATTERN`.

If `tenant_profile` is non-empty, appends:

```
## Tenant preferences
The following preferences apply specifically to this tenant and override
general defaults where they conflict. Respect them in all recommendations.

<profile content>
```

The `tenant_profile` argument is typically the return value of `TenantMemory(tenant).inject_into_prompt()` — the tenant's `profile.md` plus the last 5 decisions from `decisions.jsonl`.

---

## `system_prompt_analyse_pricelist`

**Inputs**

- `language` (default `de`) — `de` or `en`, sets the output language.
- `tenant_profile` (optional).

**Task layer (appended to base + tenant)**

> Analyse the following pricelist or technical document (respond in <German|English>). Identify:
> 1. **Products**: name, description, base price
> 2. **Configurable features**: what can be configured, variants, pricing
> 3. **Anti-patterns**: instances of the anti-patterns listed above
> 4. **Recommendations**: how to restructure for correct BOM-aware configuration
>
> Return a JSON object with keys: `products`, `features`, `anti_patterns`, `recommendations`.

**Output contract**

```json
{
  "products": [{"name": "...", "description": "...", "base_price": 0}],
  "features": [{"name": "...", "variants": [], "pricing": "..."}],
  "anti_patterns": [{"pattern_id": "implicit-base-config", "evidence": "...", "correction": "..."}],
  "recommendations": ["..."]
}
```

The user-facing message holding the pricelist contents is appended after the system prompt.

---

## `system_prompt_suggest_configuration`

**Inputs**

- `language` (default `de`).
- `existing_groups` (optional list of dicts `{id, name, options:[{id,name}]}`) — when present, the prompt includes a "MUST check for reuse" section listing up to 50 existing groups, instructing the AI to set `reuse_existing=true` and supply `existing_group_id` instead of creating duplicates.
- `tenant_profile` (optional).

**Output contract**

```json
{
  "products": [
    {
      "name": "...",
      "groups": [
        {
          "name": "...",
          "is_multi": false,
          "options": [{"name": "...", "recommended": true, "price": 0}],
          "reuse_existing": false,
          "existing_group_id": null
        }
      ],
      "bom_rules": [
        {"child_part_name": "...", "usage_subclauses": [{"option_name": "...", "factor": 1.0}]}
      ],
      "forbidden_pairs": [
        {"option_name_1": "...", "option_name_2": "...", "reason": "..."}
      ],
      "constraint_rules": [
        {
          "description": "...",
          "rule_json": [{"if": {"option_selected": "name"}, "then": {"forbid_options": ["name"]}}]
        }
      ]
    }
  ]
}
```

When the AI marks `reuse_existing=true`, it must set `existing_group_id` and may include a `price_overrides` map for area-specific pricing — those map to `option-area-config` writes downstream.

---

## `system_prompt_build_offer_template`

**Inputs**

- `doc_type_layout` (optional dict) — single entry from `GET /documents/doc-types`, the one with `key == "offer"`. Provides `default_layout` and `requires_configuration` flag.
- `dynamic_content_blocks` (optional list) — system content blocks from `GET /documents/content-blocks?is_dynamic=true`. Referenced by id in the AI's output.
- `language` (default `de`).
- `tenant_profile` (optional).

**Task layer**

> Propose a document template for the given product. The template must satisfy the doc_type contract above and follow `offer-requires-configuration-block` and `use-system-dynamic-blocks` rules. Respond in <language>.
>
> Structure chapters: at minimum include
>   1. "Product Overview" — static content block with EditorJS narrative (intro, core-features table, mechanics/sensors/electronics/software sub-sections). May reference an existing static content block by id or describe a new one.
>   2. "Configuration" — required attachment to the system `dynamic:document_configuration` content block. Look it up in the dynamic-blocks list above and use its id.

**Output contract**

```json
{
  "template_name": "...",
  "chapters": [
    {
      "slug": "...",
      "title": "...",
      "order_index": 0,
      "attachments": [
        {"content_block_id": null, "dynamic_key": "dynamic:document_configuration", "is_required": true}
      ]
    }
  ]
}
```

---

## `system_prompt_audit`

**Inputs**

- `findings` (list of dicts) — produced by a structural-check runner. Each finding has `check_id`, `severity`, `entity_type`, `entity_id`, `message`.
- `language` (default `de`).
- `tenant_profile` (optional).

**Task layer**

> Review the audit findings above and propose prioritised fixes (respond in <language>). For each finding:
> 1. Classify severity (error > warning > info)
> 2. Recommend the minimum change that resolves it
> 3. Cross-reference any configuration rule it violates (by id)

**Output contract**

```json
{
  "summary": "...",
  "fixes": [
    {
      "check_id": "areas-without-groups",
      "entity_id": 42,
      "severity": "error",
      "fix_description": "...",
      "related_rules": ["no-empty-areas"]
    }
  ]
}
```

---

## `system_prompt_apply_config`

**Inputs**

- `recommendation` (dict) — usually the JSON output of `suggest_configuration`.
- `tenant_profile` (optional).

**Task layer**

> Convert the recommendation above into a sequence of idempotent REST operations for the Rattle API. Each operation must be expressed as get-or-create so a second run is a safe no-op.
>
> Valid operation types:
>   - `ensure_product {name, base_price, description?}`
>   - `ensure_area {name, description?, parent_product: <name>}`
>   - `ensure_group {name, is_multi, description?, link_to_areas: [<area_names>]}`
>   - `ensure_option {name, price, recommended, description?, group: <group_name>}`
>   - `ensure_area_config {option: <name>, area: <name>, price}`
>   - `ensure_constraint_pair {option_1: <name>, option_2: <name>}`
>   - `ensure_constraint_rule {description, rule_json}`
>
> Honour `no-empty-areas` (do not emit `ensure_area` operations that end up with zero groups), `reuse-over-duplicate` (one `ensure_group` per distinct group, with `link_to_areas` across all products), and `minimal-keys` (never include a custom key unless the tenant profile explicitly requires one).

**Output contract**

```json
{
  "operations": [{"type": "ensure_product", "name": "...", "base_price": 0}],
  "notes": ["..."]
}
```

The downstream builder iterates `operations` in order, treating each as get-or-create against the live API (matching by name). The `notes` array surfaces any soft warnings the AI wants to bubble up (e.g. "I assumed default `is_multi=false` because the input didn't specify").

---

## Building these prompts in non-Python clients

Any AI client can reproduce these prompts by:

1. Reading `data-model.md`, `configuration-rules.md`, `anti-patterns.md` from this `references/` directory and concatenating them under the `## Rattle Data Model`, `## Configuration Rules`, `## Anti-Patterns to Detect` headings.
2. Optionally reading `memory/<tenant>/profile.md` and appending under `## Tenant preferences`.
3. Appending the task-layer template strings shown above.
4. Sending the user's input (pricelist, recommendation, findings, etc.) as the user message.

The Python CLI in `rattle_api/tasks.py` is one reference implementation. Other implementations (a TypeScript MCP server, a Node tool, a notebook) should produce identical output for identical inputs — the consulting behaviour is encoded in this Markdown, not the code.
