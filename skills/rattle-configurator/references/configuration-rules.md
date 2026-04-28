# Configuration rules — full reference

Mirror of `rattle_api.knowledge.CONFIGURATION_RULES`. Twelve rules, ranked roughly by impact. Cite by `id` in any recommendation, audit finding, or commit message that touches configuration shape.

---

## 1. `explicit-options-for-all-variants` — THE #1 RULE

**Rule.** Every configurable feature MUST have an explicit group with ALL variants as separate, selectable options — including the "standard" or "default" variant. The standard variant must be a named, selectable option, never an implicit baseline.

**Rationale.** Without an explicit option for the standard variant, it is impossible to write a `usage_subclause` that adds the standard parts to the BOM. The configurator cannot remove an implicit baseline — it can only activate parts linked to selected options. Example: if "17 inch wheels" is implicit (not an option), there is no way to write a rule that adds 17-inch wheel parts to the BOM.

**Applies to**: groups, options.

**Detection signals**: pricelist text contains "standard", "Grundausstattung", "Serienausstattung", "im Lieferumfang", "included", "inkl.", "serienmäßig", "Basisausstattung".

---

## 2. `price-on-option`

**Rule.** Price modifiers belong on the option level (the `price` field), not on the group or as separate line items in the pricelist.

**Rationale.** Prices attached to groups or external line items cannot be conditionally applied based on option selection.

**Applies to**: options.

---

## 3. `reuse-over-duplicate`

**Rule.** Always prefer reusing existing groups and options over creating duplicates. Use option area-config (`/options/{id}/area-config`) and price-overrides for per-area differences.

**Rationale.** Duplicate groups with identical names fragment the configuration catalogue and make maintenance harder. Option area-config lets one group/option serve many areas with per-area pricing and descriptions.

**Applies to**: groups, options.

---

## 4. `forbidden-combinations`

**Rule.** Identify and define constraints for invalid option combinations. Use pair-level constraints (`POST /constraints` with `{option_id1, option_id2}` pairs) for simple exclusions. Use constraint rules (`POST /constraints/rules` with `rule_json`) for conditional logic.

**Rationale.** Without constraints, users can select impossible configurations that cannot be manufactured or delivered.

**Applies to**: options, constraints.

---

## 5. `no-empty-areas`

**Rule.** Every area must contain at least one group. Areas exist to host configurable groups — they are not a place for narrative or marketing content. If you have a product section with no configurable choices, it does not belong in an area.

**Rationale.** An area with zero groups is a dead end in the configurator UI: the user sees a section with nothing to configure. Narrative content for the product belongs in the documents system (see `narrative-in-documents-system`), not in a configuration area.

**Applies to**: areas, groups.

---

## 6. `narrative-in-documents-system`

**Rule.** Product narrative (overview, specifications table, marketing copy, section headers like "Mechanics", "Electronics", "Software") belongs in `/documents/content-blocks` attached to an `offer` document template — NOT in configuration areas.

**Rationale.** Areas are for configurable options. Content blocks are for rich EditorJS narrative. Mixing the two leads to fake "Description" areas that violate `no-empty-areas` and fragment the configurator UX. The documents system is the canonical home for per-product narrative and renders into offer PDFs.

**Applies to**: areas, document_content_block, document_template.

---

## 7. `offer-requires-configuration-block`

**Rule.** Every published `offer` document template MUST include a structure block with an attachment referencing the system-provided dynamic content block `dynamic:document_configuration`.

**Rationale.** The `offer` doc_type is registered with `requires_configuration=true` (see `GET /documents/doc-types`). An offer template without a dynamic configuration attachment renders without the live product configuration and is therefore missing the primary payload customers expect in an offer.

**Applies to**: document_template, document_attachment.

---

## 8. `use-system-dynamic-blocks`

**Rule.** When attaching dynamic content (configuration, pricing, company_contacts, document_summary, document_line_items, document_agreements), reference the pre-existing system content block by id. NEVER create a new content block whose only locale wraps `template_name: 'dynamic:...'` — that produces a duplicate shadow of a built-in resource.

**Rationale.** System dynamic blocks are registered with `is_dynamic=true` and well-known keys. Look them up via `GET /documents/content-blocks?is_dynamic=true` and reference the id directly in attachments. Wrapping them fragments the catalogue, breaks rendering, and causes duplicate-dynamic-wrappers anti-pattern findings.

**Applies to**: document_content_block, document_attachment.

---

## 9. `shared-groups-across-products`

**Rule.** Prefer one library group linked to many areas across products via `POST /groups/{id}/areas`, with per-area option-area-config overrides for price scaling. Do not duplicate a group per product unless the option list genuinely differs.

**Rationale.** Shared groups stay in sync: rename once, fix once, add an option once. Duplicating fragments the catalogue and makes rename/refactor-across-products painful. Per-product price differences are a solved problem — use area-config overrides.

**Applies to**: groups, option_area_config.

---

## 10. `area-config-for-scaled-prices`

**Rule.** When an option's price varies by product tier or area, keep a single option and set per-area prices via `PUT /options/{id}/area-config?area_id=…`. Do NOT duplicate the option for each tier.

**Rationale.** Duplicating options for pricing variations breaks BOM consistency (a single "T-slots M8" part gets split into tier-specific options) and defeats the `reuse-over-duplicate` rule. area-config is the purpose-built mechanism for exactly this case.

**Applies to**: options, option_area_config.

---

## 11. `minimal-keys`

**Rule.** Do not invent custom `key` values on groups or options unless the tenant explicitly needs integration IDs (ERP, external system references). Auto-generated keys are fine; bespoke human-readable keys become clutter that has to be maintained alongside names.

**Rationale.** Custom keys drift away from names over time and add a second source of truth. Per-tenant style preferences (e.g. "never set custom keys") belong in the tenant memory profile, not scattered through the catalogue.

**Applies to**: groups, options.

---

## How to apply these rules

When generating recommendations:

1. Start every group with the question: *what is the standard variant of this feature?* If the answer is implicit, you have an `explicit-options-for-all-variants` violation to surface.
2. Before proposing a new group, search the existing catalogue for a same/similar name (`reuse-over-duplicate`, `shared-groups-across-products`).
3. Before proposing per-tier duplicate options, propose area-config overrides (`area-config-for-scaled-prices`).
4. Before proposing a `Description` / `Overview` area, propose a document template chapter (`narrative-in-documents-system`).
5. Never publish an offer template without the `dynamic:document_configuration` attachment (`offer-requires-configuration-block`).
6. Default to no custom `key` field unless the tenant memory profile explicitly opts in (`minimal-keys`).

## Cross-reference to checks and anti-patterns

| Rule | Anti-pattern | Structural check |
|---|---|---|
| explicit-options-for-all-variants | `implicit-base-config`, `addon-only-options`, `addon-only-software-modules` | — |
| no-empty-areas | `description-area-smell` | `areas-without-groups` |
| reuse-over-duplicate | — | `duplicate-group-names` |
| offer-requires-configuration-block | — | `offer-template-missing-configuration` |
| use-system-dynamic-blocks | — | `duplicate-dynamic-wrappers` |
| price-on-option | — | `options-with-conflicting-area-overrides` |
| area-config-for-scaled-prices | — | `options-with-conflicting-area-overrides` |
| minimal-keys | — | `options-with-custom-keys` (info, opt-in) |
