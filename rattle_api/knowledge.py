"""
Configurator consulting knowledge for the Rattle product configurator.

Contains structured expertise about building correct, BOM-aware product
configurations.  Used as:
  (a) system prompts for AI tasks
  (b) heuristic anti-pattern detection (no AI needed)
  (c) reference documentation (Markdown export for CLAUDE.md)

All data is plain Python — zero external dependencies.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Rattle data model reference
# ---------------------------------------------------------------------------

RATTLE_DATA_MODEL: dict = {
    "product": {
        "description": (
            "Top-level entity representing a configurable product "
            "(e.g. a machine, furniture piece, vehicle). Areas are "
            "assigned to products via /products/{id}/areas."
        ),
        "key_fields": ["id", "name", "description", "base_price", "currency", "is_active"],
        "api_endpoint": "/products",
        "relationships": ["areas", "parts", "constraints"],
    },
    "area": {
        "description": (
            "A configurable section of a product. Areas are assigned to "
            "products and groups are linked to areas. Rich-text content "
            "(EditorJS blocks) is managed via /areas/{id}/content. "
            "Multiple areas per product (e.g. different configurable zones)."
        ),
        "key_fields": ["id", "name", "description", "price", "language", "allow_disable"],
        "api_endpoint": "/areas",
        "relationships": ["product", "groups"],
    },
    "group": {
        "description": (
            "Configuration group collecting related options "
            "(e.g. 'Wheels', 'Frässpindel', 'Auftragsverwaltung IoT'). "
            "Groups are linked to areas (not directly to products) via "
            "/groups/{id}/areas. The is_multi field controls whether "
            "the user can select one option (single-select) or multiple "
            "(multi-select)."
        ),
        "key_fields": ["id", "name", "description", "key", "is_multi", "area_ids"],
        "api_endpoint": "/groups",
        "relationships": ["areas", "options"],
    },
    "option": {
        "description": (
            "A single selectable choice within a group "
            "(e.g. '17 inch wheels', '19 inch wheels', 'ohne', 'mit'). "
            "Every variant — including the default/standard — must be an "
            "explicit option. The 'recommended' flag marks the pre-selected "
            "default. Per-area overrides (price, description) are set via "
            "/options/{id}/area-config?area_id=X."
        ),
        "key_fields": ["id", "name", "description", "price", "key", "recommended", "group_id"],
        "api_endpoint": "/options",
        "relationships": ["group"],
    },
    "part": {
        "description": (
            "A physical component, sub-assembly, or finished good that "
            "can appear in a product's bill of materials."
        ),
        "key_fields": ["id", "part_number", "part_name", "part_cost", "part_type", "status"],
        "api_endpoint": "/parts",
        "relationships": ["bom_items", "placements"],
    },
    "bom_item": {
        "description": (
            "A parent→child relationship in the hierarchical BOM. "
            "Each BOM item links a parent part to a child part with a "
            "quantity. The 'usage_subclauses' array conditionally includes "
            "this BOM line based on selected options: each entry is "
            '{"option_id": <id>, "factor": <multiplier>}. When the '
            "referenced option is selected, this BOM line is active with "
            "quantity × factor. This is the core mechanism that makes "
            "configuration drive the bill of materials."
        ),
        "key_fields": [
            "id",
            "parent_part_id",
            "child_part_id",
            "quantity",
            "uom",
            "usage_subclauses",
            "option_scalings",
        ],
        "api_endpoint": "/parts/{id}/bom",
        "relationships": ["parent_part", "child_part", "options (via usage_subclauses)"],
    },
    "constraint": {
        "description": (
            "Forbidden option combinations. Two mechanisms:\n"
            "1) Pair-level: simple option-option exclusions. "
            "POST /constraints atomically replaces all pairs for a product "
            "(use X-Constraints-Version header). Each pair is "
            "{option_id1, option_id2} — selecting one forbids the other. "
            "Check via POST /constraints/check "
            '{"product_id", "option_id1", "option_id2"}.\n'
            "2) Rule-level: conditional rules via /constraints/rules. "
            "Each rule has rule_json: "
            '[{"if": {"option_selected": X}, "then": {"forbid_options": [Y, Z]}}]. '
            "Scoped to product_id and optionally area_id."
        ),
        "key_fields": ["id", "product_id", "area_id", "description", "rule_json"],
        "api_endpoint": "/constraints (pairs), /constraints/rules (conditional)",
        "relationships": ["product", "options"],
    },
    "option_area_config": {
        "description": (
            "Per-area override for an option's price, key, description, "
            "or recommended flag. Allows reusing the same group/option "
            "across areas while adjusting properties per area. Avoids "
            "duplicating groups and options."
        ),
        "key_fields": ["option_id", "area_id", "price", "key", "description", "recommended"],
        "api_endpoint": "/options/{id}/area-config?area_id=X",
        "relationships": ["option", "area"],
    },
    # -- documents system (replaces the deprecated offer-sections) ------
    "document_template": {
        "description": (
            "A reusable template that defines the structure of a document "
            "(offer, quote, datasheet, …). Each template has a doc_type "
            "(e.g. 'offer'), an optional product_id binding, a tree of "
            "structure blocks, and an is_published / status lifecycle. "
            "The 'offer' doc_type has requires_configuration=true — its "
            "structure MUST contain an attachment referencing the system "
            "dynamic content block 'dynamic:document_configuration'. "
            "Assigned to products via /documents/templates/{id}/assign-products."
        ),
        "key_fields": [
            "id",
            "doc_type",
            "name",
            "product_id",
            "is_published",
            "status",
            "inheritance_mode",
        ],
        "api_endpoint": "/documents/templates",
        "relationships": ["product", "structure_blocks", "content_blocks (via attachments)"],
    },
    "document_content_block": {
        "description": (
            "A reusable content unit referenced by document templates. "
            "Each content block has one or more locales; each locale holds "
            "EITHER an EditorJS `blocks` array (static content) OR a "
            "`template_name` string (dynamic content resolved at render "
            "time — the two fields are mutually exclusive). System-provided "
            "dynamic blocks have is_dynamic=true and a well-known key like "
            "'dynamic:document_configuration'. NEVER wrap a system dynamic "
            "block in a new content block — attach it by id."
        ),
        "key_fields": ["id", "key", "title", "is_dynamic", "locales", "tags", "product_id"],
        "api_endpoint": "/documents/content-blocks",
        "relationships": ["locales", "attachments", "directory"],
    },
    "document_structure_block": {
        "description": (
            "A node in a document template's structure tree. node_type is "
            "one of: chapter, section, container, repeater, placeholder. "
            "Chapters are top-level sections; sections nest inside chapters; "
            "placeholders are empty slots filled by attachments. Slugs must "
            "be unique per template. Content blocks are connected via "
            "attachments, not directly."
        ),
        "key_fields": [
            "id",
            "template_id",
            "parent_id",
            "node_type",
            "title",
            "slug",
            "order_index",
        ],
        "api_endpoint": "/documents/templates/{id}/structure/blocks",
        "relationships": ["template", "parent (structure block)", "attachments"],
    },
    "document_attachment": {
        "description": (
            "Links a content block to a structure block in a document "
            "template. Multiple attachments per structure block are allowed "
            "(order_index controls order). is_required=true marks an "
            "attachment that must resolve for the document to publish — "
            "used for dynamic blocks like 'dynamic:document_configuration' "
            "that the offer doc_type requires."
        ),
        "key_fields": [
            "id",
            "structure_id",
            "content_block_id",
            "order_index",
            "is_active",
            "is_required",
        ],
        "api_endpoint": ("/documents/templates/{id}/structure/blocks/{block_id}/attachments"),
        "relationships": ["structure_block", "content_block"],
    },
    "doc_type_layout": {
        "description": (
            "Machine-readable contract for a document type. "
            "GET /documents/doc-types returns each registered doc_type with "
            "a default_layout (list of {slug, title, dynamic_key}) and "
            "boolean flags like requires_configuration and requires_quote. "
            "Consulting workflows should read this at runtime and use it as "
            "the source of truth for which dynamic blocks a template must "
            "contain to be valid for a given doc_type."
        ),
        "key_fields": [
            "key",
            "label",
            "default_layout",
            "requires_configuration",
            "requires_quote",
            "supported_formats",
        ],
        "api_endpoint": "/documents/doc-types",
        "relationships": ["document_template (via doc_type)"],
    },
}


# ---------------------------------------------------------------------------
# Configuration rules
# ---------------------------------------------------------------------------

CONFIGURATION_RULES: list[dict] = [
    {
        "id": "explicit-options-for-all-variants",
        "rule": (
            "Every configurable feature MUST have an explicit group with "
            "ALL variants as separate, selectable options — including the "
            "'standard' or 'default' variant. The standard variant must "
            "be a named, selectable option, never an implicit baseline."
        ),
        "rationale": (
            "Without an explicit option for the standard variant, it is "
            "impossible to write a usage_subclause that adds the standard "
            "parts to the BOM. The configurator cannot remove an implicit "
            "baseline — it can only activate parts linked to selected options. "
            "Example: if '17 inch wheels' is implicit (not an option), "
            "there is no way to write a rule that adds 17-inch wheel parts "
            "to the BOM."
        ),
        "applies_to": ["groups", "options"],
    },
    {
        "id": "price-on-option",
        "rule": (
            "Price modifiers belong on the option level, not on the "
            "group or as separate line items in the pricelist."
        ),
        "rationale": (
            "Prices attached to groups or external line items cannot "
            "be conditionally applied based on option selection."
        ),
        "applies_to": ["options"],
    },
    {
        "id": "reuse-over-duplicate",
        "rule": (
            "Always prefer reusing existing groups and options over "
            "creating duplicates. Use option area-config "
            "(/options/{id}/area-config) and price-overrides for "
            "per-area differences."
        ),
        "rationale": (
            "Duplicate groups with identical names fragment the "
            "configuration catalogue and make maintenance harder. "
            "Option area-config lets one group/option serve many areas "
            "with per-area pricing and descriptions."
        ),
        "applies_to": ["groups", "options"],
    },
    {
        "id": "forbidden-combinations",
        "rule": (
            "Identify and define constraints for invalid option "
            "combinations. Use pair-level constraints (POST /constraints "
            "with {option_id1, option_id2} pairs) for simple exclusions. "
            "Use constraint rules (POST /constraints/rules with rule_json) "
            "for conditional logic."
        ),
        "rationale": (
            "Without constraints, users can select impossible "
            "configurations that cannot be manufactured or delivered."
        ),
        "applies_to": ["options", "constraints"],
    },
    {
        "id": "no-empty-areas",
        "rule": (
            "Every area must contain at least one group. Areas exist to "
            "host configurable groups — they are not a place for narrative "
            "or marketing content. If you have a product section with no "
            "configurable choices, it does not belong in an area."
        ),
        "rationale": (
            "An area with zero groups is a dead end in the configurator "
            "UI: the user sees a section with nothing to configure. "
            "Narrative content for the product belongs in the documents "
            "system (see narrative-in-documents-system), not in a "
            "configuration area."
        ),
        "applies_to": ["areas", "groups"],
    },
    {
        "id": "narrative-in-documents-system",
        "rule": (
            "Product narrative (overview, specifications table, marketing "
            "copy, section headers like 'Mechanics', 'Electronics', "
            "'Software') belongs in /documents/content-blocks attached to "
            "an 'offer' document template — NOT in configuration areas."
        ),
        "rationale": (
            "Areas are for configurable options. Content blocks are for "
            "rich EditorJS narrative. Mixing the two leads to fake "
            "'Description' areas that violate no-empty-areas and fragment "
            "the configurator UX. The documents system is the canonical "
            "home for per-product narrative and renders into offer PDFs."
        ),
        "applies_to": ["areas", "document_content_block", "document_template"],
    },
    {
        "id": "offer-requires-configuration-block",
        "rule": (
            "Every published 'offer' document template MUST include a "
            "structure block with an attachment referencing the system-"
            "provided dynamic content block 'dynamic:document_configuration'."
        ),
        "rationale": (
            "The 'offer' doc_type is registered with "
            "requires_configuration=true (see GET /documents/doc-types). "
            "An offer template without a dynamic configuration attachment "
            "renders without the live product configuration and is therefore "
            "missing the primary payload customers expect in an offer."
        ),
        "applies_to": ["document_template", "document_attachment"],
    },
    {
        "id": "use-system-dynamic-blocks",
        "rule": (
            "When attaching dynamic content (configuration, pricing, "
            "company_contacts, document_summary, document_line_items, "
            "document_agreements), reference the pre-existing system content "
            "block by id. NEVER create a new content block whose only "
            "locale wraps `template_name: 'dynamic:...'` — that produces a "
            "duplicate shadow of a built-in resource."
        ),
        "rationale": (
            "System dynamic blocks are registered with is_dynamic=true and "
            "well-known keys. Look them up via "
            "GET /documents/content-blocks?is_dynamic=true and reference "
            "the id directly in attachments. Wrapping them fragments the "
            "catalogue, breaks rendering, and causes duplicate-dynamic-"
            "wrappers anti-pattern findings."
        ),
        "applies_to": ["document_content_block", "document_attachment"],
    },
    {
        "id": "shared-groups-across-products",
        "rule": (
            "Prefer one library group linked to many areas across products "
            "via POST /groups/{id}/areas, with per-area option-area-config "
            "overrides for price scaling. Do not duplicate a group per "
            "product unless the option list genuinely differs."
        ),
        "rationale": (
            "Shared groups stay in sync: rename once, fix once, add an "
            "option once. Duplicating fragments the catalogue and makes "
            "rename/refactor-across-products painful. Per-product price "
            "differences are a solved problem — use area-config overrides."
        ),
        "applies_to": ["groups", "option_area_config"],
    },
    {
        "id": "area-config-for-scaled-prices",
        "rule": (
            "When an option's price varies by product tier or area, keep "
            "a single option and set per-area prices via "
            "PUT /options/{id}/area-config?area_id=…. Do NOT duplicate "
            "the option for each tier."
        ),
        "rationale": (
            "Duplicating options for pricing variations breaks BOM "
            "consistency (a single 'T-slots M8' part gets split into "
            "tier-specific options) and defeats the reuse-over-duplicate "
            "rule. area-config is the purpose-built mechanism for exactly "
            "this case."
        ),
        "applies_to": ["options", "option_area_config"],
    },
    {
        "id": "minimal-keys",
        "rule": (
            "Do not invent custom `key` values on groups or options unless "
            "the tenant explicitly needs integration IDs (ERP, external "
            "system references). Auto-generated keys are fine; bespoke "
            "human-readable keys become clutter that has to be maintained "
            "alongside names."
        ),
        "rationale": (
            "Custom keys drift away from names over time and add a second "
            "source of truth. Per-tenant style preferences (e.g. 'never "
            "set custom keys') belong in the tenant memory profile, not "
            "scattered through the catalogue."
        ),
        "applies_to": ["groups", "options"],
    },
]


# ---------------------------------------------------------------------------
# Anti-patterns
# ---------------------------------------------------------------------------

ANTI_PATTERNS: list[dict] = [
    {
        "id": "implicit-base-config",
        "name": "Implicit Base Configuration",
        "description": (
            "The pricelist describes standard features as included in the "
            "base product without creating explicit options for them. "
            "Only upgrades/add-ons appear as selectable options."
        ),
        "indicators": [
            "standard",
            "Grundausstattung",
            "Serienausstattung",
            "im Lieferumfang",
            "included",
            "inkl.",
            "serienmäßig",
            "Basisausstattung",
        ],
        "correction": (
            "Create an explicit group with explicit options for ALL "
            "variants — including the standard one. Mark the standard "
            "option as default."
        ),
        "example_wrong": (
            'Product comes with 17" wheels as standard. '
            "Option '19 inch wheels' (price: 500). "
            "Problem: no BOM item can carry a usage_subclause for the "
            '17" wheels because no option represents them.'
        ),
        "example_correct": (
            "Group 'Wheels' (is_multi: false): "
            "Option '17 inch' (recommended: true, price: 0), "
            "Option '19 inch' (recommended: false, price: 500). "
            "BOM: child_part '17-inch wheel assy' with "
            "usage_subclauses: [{option_id: <17_inch>, factor: 1.0}]; "
            "child_part '19-inch wheel assy' with "
            "usage_subclauses: [{option_id: <19_inch>, factor: 1.0}]."
        ),
    },
    {
        "id": "addon-only-options",
        "name": "Add-on Only Options",
        "description": (
            "Options are listed only as surcharges or add-ons to a base "
            "product, without explicitly stating what the base/default is."
        ),
        "indicators": [
            "Aufpreis",
            "Zuschlag",
            "surcharge",
            "zusätzlich",
            "extra",
            "Mehrpreis",
            "Aufschlag",
            "optional",
        ],
        "correction": (
            "For every add-on, identify the base variant it replaces "
            "or supplements. Create a group with both the base and the "
            "add-on as explicit options."
        ),
        "example_wrong": (
            "Aufpreis Frässpindel HSK-63F mit Encoder: +2.500€. "
            "Problem: what is the default spindle? No option exists for it."
        ),
        "example_correct": (
            "Group 'Frässpindel' (is_multi: false): "
            "Option 'ISO 30 Standard' (recommended: true, price: 0), "
            "Option 'HSK-63F ohne Encoder' (price: 1800), "
            "Option 'HSK-63F mit Encoder' (price: 2500)."
        ),
    },
    {
        "id": "description-area-smell",
        "name": "Narrative Area Smell",
        "description": (
            "The input mentions narrative sections like 'Description', "
            "'Overview', 'Beschreibung', 'Produktbeschreibung', or chapter "
            "titles like 'Mechanics' / 'Sensors' / 'Electronics' / "
            "'Software' as if they were on par with configurable options. "
            "Signals the author is about to create a narrative-only area "
            "that will have no groups."
        ),
        "indicators": [
            "Beschreibung",
            "Produktbeschreibung",
            "Description",
            "Overview",
            "Übersicht",
            "Mechanics",
            "Mechanik",
            "Sensorik",
            "Elektronik",
            "Bedienung",
        ],
        "correction": (
            "Narrative content does not belong in a configuration area. "
            "Create a document template (doc_type='offer') with a "
            "'Product Overview' chapter and attach a static EditorJS "
            "content block carrying the narrative. Attach the system "
            "'dynamic:document_configuration' block in a separate chapter "
            "so the live configuration still renders."
        ),
        "example_wrong": (
            "Area 'Widget Pro — Description' (0 groups, just rich text "
            "about the product). The area has nothing to configure."
        ),
        "example_correct": (
            "Document template 'Widget Pro — Offer' (doc_type=offer): "
            "chapter 'Product Overview' with attached content block "
            "containing EditorJS narrative; chapter 'Configuration' with "
            "attached dynamic:document_configuration. Areas carry only "
            "configurable groups."
        ),
    },
    {
        "id": "addon-only-software-modules",
        "name": "Add-on Only Software Modules",
        "description": (
            "Software/licence modules appear only as surcharges without a "
            "matching base-module option. Common in pricelists because "
            "software has no physical BOM and is easy to miss when "
            "applying the explicit-options-for-all-variants rule."
        ),
        "indicators": [
            "Software-Modul",
            "Software Modul",
            "Modul-Aufpreis",
            "Lizenzmodul",
            "zusätzliches Modul",
            "Software surcharge",
        ],
        "correction": (
            "Create a group for the software capability (e.g. 'Cyclic "
            "testing software') with both the baseline option (price 0, "
            "recommended) and the upgrade module option. Set is_multi "
            "based on whether modules stack."
        ),
        "example_wrong": (
            "Aufpreis Software-Modul 'Multistep cyclic': 500€. Problem: "
            "no option exists for the default (no-module) state."
        ),
        "example_correct": (
            "Group 'Software — Cyclic testing' (is_multi: false): "
            "Option 'Manual cyclic testing (included)' (recommended: true, "
            "price: 0), Option 'Multistep cyclic testing module' (price: 500)."
        ),
    },
]


# ---------------------------------------------------------------------------
# Structural checks — declarative specs for live-tenant audit
# ---------------------------------------------------------------------------
#
# Each entry is a declarative check spec that a live-tenant audit runner can
# execute against a RattleClient. The runner lives outside this module (Part
# C follow-up); here we only keep the data so the consulting system can
# reference the checks by id in prompts, documentation, and future tooling.

STRUCTURAL_CHECKS: dict = {
    "areas-without-groups": {
        "name": "Areas without groups",
        "description": (
            "Areas that have zero groups linked to them. Violates the no-empty-areas rule."
        ),
        "severity": "error",
        "check_spec": {
            "list": "/areas",
            "per_entity": "/areas/{id}/groups",
            "flag_when": "len(groups) == 0",
        },
        "related_rules": ["no-empty-areas"],
    },
    "duplicate-group-names": {
        "name": "Duplicate group names",
        "description": (
            "Groups where the same (case-insensitive) name appears on "
            "multiple group ids. Indicates a reuse-over-duplicate failure."
        ),
        "severity": "warning",
        "check_spec": {
            "list": "/groups",
            "group_by": "lower(name)",
            "flag_when": "count > 1",
        },
        "related_rules": ["reuse-over-duplicate", "shared-groups-across-products"],
    },
    "offer-template-missing-configuration": {
        "name": "Offer template missing configuration block",
        "description": (
            "Offer document templates whose structure tree does not "
            "contain any attachment to the system dynamic content block "
            "'dynamic:document_configuration'. Violates the "
            "offer-requires-configuration-block rule and the doc_type "
            "requires_configuration contract."
        ),
        "severity": "error",
        "check_spec": {
            "list": "/documents/templates?doc_type=offer",
            "per_entity": "/documents/templates/{id}/structure",
            "flag_when": (
                "no attachment has content_block_key == 'dynamic:document_configuration'"
            ),
        },
        "related_rules": ["offer-requires-configuration-block"],
    },
    "duplicate-dynamic-wrappers": {
        "name": "Duplicate wrappers around system dynamic blocks",
        "description": (
            "User-created content blocks whose only locale has a "
            "template_name matching a system dynamic block key (e.g. "
            "'dynamic:document_configuration'). Indicates a built-in "
            "dynamic block was wrapped instead of referenced by id."
        ),
        "severity": "warning",
        "check_spec": {
            "list": "/documents/content-blocks",
            "flag_when": (
                "is_dynamic == False and any(locale.template_name startswith 'dynamic:')"
            ),
        },
        "related_rules": ["use-system-dynamic-blocks"],
    },
    "options-with-custom-keys": {
        "name": "Options with custom keys",
        "description": (
            "Options that have a non-empty `key` field. Not an error by "
            "itself — some tenants require integration keys — but reported "
            "so tenants who prefer minimal keys can audit. Opt-in via "
            "tenant memory profile."
        ),
        "severity": "info",
        "check_spec": {
            "list": "/options",
            "flag_when": "key != '' and key is not None",
        },
        "related_rules": ["minimal-keys"],
        "tenant_opt_in": True,
    },
    "options-with-conflicting-area-overrides": {
        "name": "Options with conflicting area overrides",
        "description": (
            "Options where an area-config has price 0 / null / missing "
            "while the base option price is non-zero. Indicates the option "
            "silently drops to free in that area."
        ),
        "severity": "warning",
        "check_spec": {
            "list": "/options",
            "per_entity": "/options/{id}/area-config?area_id={area_id}",
            "flag_when": ("base_price > 0 and area_config.price in (0, None, '')"),
        },
        "related_rules": ["price-on-option", "area-config-for-scaled-prices"],
    },
}


# ---------------------------------------------------------------------------
# System prompt builders
# ---------------------------------------------------------------------------


def system_prompt_base(*, tenant_profile: str | None = None) -> str:
    """Core consulting rules fragment, usable as a prefix for any prompt.

    Args:
        tenant_profile: Optional tenant-specific preferences markdown. When
            provided, it is appended under a ``## Tenant preferences``
            section so every downstream prompt inherits the tenant's style
            choices (e.g. "never set custom option keys"). Typically
            produced by :meth:`rattle_api.memory.TenantMemory.inject_into_prompt`.
    """
    rules_text = "\n".join(
        f"  {i + 1}. **{r['id']}**: {r['rule']}" for i, r in enumerate(CONFIGURATION_RULES)
    )

    anti_text = "\n".join(
        f"  - **{ap['name']}**: {ap['description']} Indicators: {', '.join(ap['indicators'][:5])}"
        for ap in ANTI_PATTERNS
    )

    base = (
        "You are a product configurator consultant with deep expertise in "
        "building correct, BOM-aware product configurations for the Rattle "
        "product configurator platform.\n\n"
        "## Rattle Data Model\n"
        "Product → Areas → Groups (is_multi: single/multi-select) → Options\n"
        "Parts → BOM items (parent→child with quantity + usage_subclauses)\n"
        "Constraints (forbidden option combinations + conditional rules)\n"
        "Documents system: document_template → structure_blocks → "
        "attachments → content_blocks (static EditorJS or system dynamic).\n\n"
        "- Groups are linked to Areas (not directly to Products). "
        "A group's is_multi field controls single-select vs multi-select.\n"
        "- Every area must contain at least one group — no narrative-only "
        "areas. Narrative content lives in the documents system.\n"
        "- Options have: name, price, key, recommended (=pre-selected default).\n"
        "- BOM items contain usage_subclauses: "
        '[{"option_id": <id>, "factor": <multiplier>}]. '
        "When the referenced option is selected, this BOM line is active "
        "with quantity × factor.\n"
        "- Per-area price/config overrides: /options/{id}/area-config "
        "and /options/{id}/price-overrides — avoids duplicating groups.\n"
        "- Pair-level constraints (POST /constraints): "
        "simple option-option exclusions as {option_id1, option_id2} pairs. "
        "Atomically replaces all pairs for a product.\n"
        "- Constraint rules (POST /constraints/rules): conditional logic "
        "with rule_json: "
        '[{"if": {"option_selected": X}, "then": {"forbid_options": [Y, Z]}}].\n'
        "- Documents system (offer templates): GET /documents/doc-types "
        "gives each doc_type's default_layout + requires_configuration "
        "flag. The 'offer' doc_type REQUIRES a structure block attachment "
        "to the system dynamic content block 'dynamic:document_configuration'. "
        "Built-in dynamic blocks (is_dynamic=true) are listed by "
        "GET /documents/content-blocks?is_dynamic=true — reference them by "
        "id, never wrap them in a new content block.\n\n"
        "## THE #1 RULE\n"
        "NEVER build 'base product + add-ons' where the base configuration is "
        "implicit. Every configurable feature MUST have an explicit group with "
        "ALL variants as separate options — including the 'standard' variant.\n\n"
        "WRONG: Product has 17\" wheels as standard. Option: '19 inch' (price: 500). "
        '→ No usage_subclause can include 17" wheel parts in the BOM.\n'
        "CORRECT: Group 'Wheels' (is_multi: false):\n"
        "  Option '17 inch' (recommended: true, price: 0)\n"
        "  Option '19 inch' (recommended: false, price: 500)\n"
        "BOM items:\n"
        '  child_part: "17-inch wheel assembly", '
        "usage_subclauses: [{option_id: <17_inch_opt>, factor: 1.0}]\n"
        '  child_part: "19-inch wheel assembly", '
        "usage_subclauses: [{option_id: <19_inch_opt>, factor: 1.0}]\n"
        "→ Each option's BOM line is only active when that option is selected.\n\n"
        f"## Configuration Rules\n{rules_text}\n\n"
        f"## Anti-Patterns to Detect\n{anti_text}"
    )

    if tenant_profile and tenant_profile.strip():
        base += (
            "\n\n## Tenant preferences\n"
            "The following preferences apply specifically to this tenant and "
            "override general defaults where they conflict. Respect them in "
            "all recommendations.\n\n"
            f"{tenant_profile.strip()}"
        )

    return base


def system_prompt_analyse_pricelist(
    *, language: str = "de", tenant_profile: str | None = None
) -> str:
    """System prompt for pricelist analysis with embedded consulting rules."""
    lang_name = "German" if language == "de" else language
    return (
        f"{system_prompt_base(tenant_profile=tenant_profile)}\n\n"
        "## Your Task\n"
        f"Analyse the following pricelist or technical document (respond in {lang_name}). "
        "Identify:\n"
        "1. **Products**: name, description, base price\n"
        "2. **Configurable features**: what can be configured, variants, pricing\n"
        "3. **Anti-patterns**: instances of the anti-patterns listed above\n"
        "4. **Recommendations**: how to restructure for correct BOM-aware configuration\n\n"
        "Return a JSON object with keys: products, features, anti_patterns, recommendations."
    )


def system_prompt_suggest_configuration(
    *,
    language: str = "de",
    existing_groups: list[dict] | None = None,
    tenant_profile: str | None = None,
) -> str:
    """System prompt for configuration suggestion with BOM-aware rules."""
    lang_name = "German" if language == "de" else language

    reuse_section = ""
    if existing_groups:
        groups_text = "\n".join(
            f"  - Group '{g.get('name', '?')}' (id={g.get('id', '?')}): "
            f"options: {[o.get('name', '?') for o in g.get('options', [])]}"
            for g in existing_groups[:50]  # limit to avoid token overflow
        )
        reuse_section = (
            "\n\n## Existing Groups & Options (MUST check for reuse)\n"
            f"{groups_text}\n\n"
            "IMPORTANT: Before suggesting a new group, check if an existing "
            "group with the same or very similar name already exists above. "
            "If it does:\n"
            "- Set reuse_existing=true and provide the existing_group_id\n"
            "- If prices differ for this area, use option area-config or "
            "price-overrides instead of creating a duplicate group\n"
            "- Only create a new group if the name and options genuinely differ"
        )

    return (
        f"{system_prompt_base(tenant_profile=tenant_profile)}{reuse_section}\n\n"
        "## Your Task\n"
        "Generate an explicit, BOM-aware configuration structure for the Rattle "
        f"product configurator (respond in {lang_name}).\n\n"
        "For each product found in the document, produce:\n"
        "1. **groups**: each with name, description, is_multi, and options "
        "(each option: name, recommended, price, description). "
        "If reusing existing group: set reuse_existing=true, existing_group_id, "
        "and note price_overrides for area-specific pricing.\n"
        "2. **bom_rules**: for options that affect physical parts, describe "
        "the BOM item with child_part_name and "
        "usage_subclauses [{option_id, factor}] format.\n"
        "3. **forbidden_pairs**: simple option-option exclusions as "
        "[{option_name_1, option_name_2, reason}] — these map directly to "
        "POST /constraints with {option_id1, option_id2} pairs.\n"
        "4. **constraint_rules**: conditional rules as "
        '[{"description", "rule_json": [{"if": {"option_selected": name}, '
        '"then": {"forbid_options": [names]}}]}].\n\n'
        "Return JSON with key 'products' (array of objects with keys: "
        "name, groups, bom_rules, forbidden_pairs, constraint_rules)."
    )


def system_prompt_build_offer_template(
    *,
    doc_type_layout: dict | None = None,
    dynamic_content_blocks: list[dict] | None = None,
    language: str = "de",
    tenant_profile: str | None = None,
) -> str:
    """System prompt for building an offer document template.

    Produces a prompt that instructs the AI to emit a template definition
    matching the live tenant's `offer` doc_type contract. The caller is
    expected to fetch:

    - `doc_type_layout`: a single entry from ``GET /documents/doc-types``
      (the one with ``key == "offer"``), providing ``default_layout`` and
      ``requires_configuration``.
    - `dynamic_content_blocks`: the list of system content blocks from
      ``GET /documents/content-blocks?is_dynamic=true`` — referenced by id
      in the AI's output.

    The AI's JSON output has the shape ``{template_name, chapters: [{slug,
    title, attachments: [{content_block_id?, dynamic_key?}]}]}`` — suitable
    for an idempotent builder to execute.
    """
    lang_name = "German" if language == "de" else language

    layout_section = ""
    if doc_type_layout:
        requires_cfg = doc_type_layout.get("requires_configuration", False)
        default_layout = doc_type_layout.get("default_layout", [])
        layout_lines = "\n".join(
            f"  - {entry.get('slug', '?')}: {entry.get('title', '?')} "
            f"(dynamic_key={entry.get('dynamic_key', 'none')})"
            for entry in default_layout
        )
        layout_section = (
            "\n\n## Target doc_type contract\n"
            f"doc_type: {doc_type_layout.get('key', 'offer')}  "
            f"(requires_configuration={requires_cfg})\n"
            f"Default layout:\n{layout_lines}\n\n"
            "Every dynamic_key in the default layout MUST appear in the "
            "template as an attachment referencing the corresponding system "
            "dynamic content block."
        )

    dynamic_section = ""
    if dynamic_content_blocks:
        dyn_lines = "\n".join(
            f"  - id={cb.get('id', '?')}  key={cb.get('key', '?')}  title={cb.get('title', '?')}"
            for cb in dynamic_content_blocks
        )
        dynamic_section = (
            "\n\n## Available system dynamic content blocks\n"
            f"{dyn_lines}\n\n"
            "Reference these by id in attachments. NEVER create a new content "
            "block that wraps a dynamic key — use the existing one."
        )

    return (
        f"{system_prompt_base(tenant_profile=tenant_profile)}"
        f"{layout_section}"
        f"{dynamic_section}\n\n"
        "## Your Task\n"
        "Propose a document template for the given product. The template "
        "must satisfy the doc_type contract above and follow the "
        "offer-requires-configuration-block and use-system-dynamic-blocks "
        f"rules. Respond in {lang_name}.\n\n"
        "Structure chapters: at minimum include\n"
        "  1. 'Product Overview' — static content block with EditorJS "
        "narrative (intro, core-features table, mechanics/sensors/"
        "electronics/software sub-sections). You may reference an existing "
        "static content block by id or describe a new one.\n"
        "  2. 'Configuration' — required attachment to the system "
        "'dynamic:document_configuration' content block. Look it up in the "
        "dynamic-blocks list above and use its id.\n\n"
        "Return JSON: {template_name, chapters: [{slug, title, "
        "order_index, attachments: [{content_block_id, dynamic_key, "
        "is_required}]}]}."
    )


def system_prompt_audit(
    *,
    findings: list[dict] | None = None,
    language: str = "de",
    tenant_profile: str | None = None,
) -> str:
    """System prompt for reviewing structural audit findings.

    Accepts a list of findings produced by a structural-check runner
    (future Part C ``audit.py``). Each finding is a dict with ``check_id``,
    ``severity``, ``entity_type``, ``entity_id``, and ``message``. The AI
    is asked to triage them and propose prioritised fixes.
    """
    lang_name = "German" if language == "de" else language

    findings_section = ""
    if findings:
        lines = "\n".join(
            f"  - [{f.get('severity', 'info')}] {f.get('check_id', '?')} on "
            f"{f.get('entity_type', '?')} {f.get('entity_id', '?')}: "
            f"{f.get('message', '')}"
            for f in findings
        )
        findings_section = f"\n\n## Audit findings\n{lines}"

    checks_section = "\n".join(
        f"  - **{cid}** ({spec['severity']}): {spec['description']}"
        for cid, spec in STRUCTURAL_CHECKS.items()
    )

    return (
        f"{system_prompt_base(tenant_profile=tenant_profile)}\n\n"
        f"## Available structural checks\n{checks_section}"
        f"{findings_section}\n\n"
        "## Your Task\n"
        "Review the audit findings above and propose prioritised fixes "
        f"(respond in {lang_name}). For each finding:\n"
        "1. Classify severity (error > warning > info)\n"
        "2. Recommend the minimum change that resolves it\n"
        "3. Cross-reference any configuration rule it violates (by id)\n\n"
        "Return JSON: {summary, fixes: [{check_id, entity_id, severity, "
        "fix_description, related_rules}]}."
    )


def system_prompt_apply_config(
    *,
    recommendation: dict | None = None,
    tenant_profile: str | None = None,
) -> str:
    """System prompt for converting a suggest_configuration output into REST calls.

    The consuming builder (future Part C ``builder.py``) executes the
    returned plan idempotently (get-or-create for each entity), so the AI
    output must be a sequence of idempotent operations keyed by natural
    identifiers (names) rather than ids.
    """
    rec_section = ""
    if recommendation:
        import json as _json

        rec_json = _json.dumps(recommendation, ensure_ascii=False, indent=2)[:6000]
        rec_section = f"\n\n## Recommendation payload\n```json\n{rec_json}\n```"

    return (
        f"{system_prompt_base(tenant_profile=tenant_profile)}"
        f"{rec_section}\n\n"
        "## Your Task\n"
        "Convert the recommendation above into a sequence of idempotent "
        "REST operations for the Rattle API. Each operation must be "
        "expressed as get-or-create so a second run is a safe no-op.\n\n"
        "Valid operation types:\n"
        "  - ensure_product {name, base_price, description?}\n"
        "  - ensure_area {name, description?, parent_product: <name>}\n"
        "  - ensure_group {name, is_multi, description?, link_to_areas: [<area_names>]}\n"
        "  - ensure_option {name, price, recommended, description?, group: <group_name>}\n"
        "  - ensure_area_config {option: <name>, area: <name>, price}\n"
        "  - ensure_constraint_pair {option_1: <name>, option_2: <name>}\n"
        "  - ensure_constraint_rule {description, rule_json}\n\n"
        "Honour the no-empty-areas rule (do not emit ensure_area operations "
        "that end up with zero groups), the reuse-over-duplicate rule (one "
        "ensure_group per distinct group, with link_to_areas across all "
        "products), and the minimal-keys rule (never include a custom key "
        "unless the tenant profile explicitly requires one).\n\n"
        "Return JSON: {operations: [...], notes: [string]}."
    )


# ---------------------------------------------------------------------------
# Heuristic anti-pattern detection (no AI required)
# ---------------------------------------------------------------------------


def detect_anti_patterns(data: list[dict]) -> list[dict]:
    """Scan parsed pricelist rows for common anti-patterns.

    Works on structured data (list of dicts from Excel parsing).
    Checks cell values against indicator keywords for each anti-pattern.

    Args:
        data: Row dicts from :func:`source.read_excel`.

    Returns:
        List of detected issues, each with ``pattern_id``, ``pattern_name``,
        ``row_index``, ``column``, ``value``, and ``correction``.
    """
    detections: list[dict] = []

    for row_idx, row in enumerate(data):
        for col, value in row.items():
            if value is None:
                continue
            cell_str = str(value).strip()
            if not cell_str:
                continue
            cell_lower = cell_str.lower()

            for ap in ANTI_PATTERNS:
                for indicator in ap["indicators"]:
                    if indicator.lower() in cell_lower:
                        detections.append(
                            {
                                "pattern_id": ap["id"],
                                "pattern_name": ap["name"],
                                "row_index": row_idx,
                                "column": col,
                                "value": cell_str[:200],
                                "indicator": indicator,
                                "correction": ap["correction"],
                            }
                        )
                        break  # one match per anti-pattern per cell

    return detections


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------


def as_markdown() -> str:
    """Render all knowledge as Markdown for embedding in CLAUDE.md or docs."""
    lines: list[str] = []

    # Header
    lines.append("## Configurator Consulting Knowledge")
    lines.append("")
    lines.append(
        "This codebase embeds deep consulting expertise about building correct "
        "product configurators. The knowledge is codified in "
        "`rattle_api/knowledge.py` and automatically applied by the AI "
        "analysis tasks (`ai-analyse-pricelist`, `ai-suggest-config`)."
    )
    lines.append("")

    # The #1 Rule
    lines.append("### The #1 Rule: Explicit Options for ALL Variants")
    lines.append("")
    lines.append(
        "**NEVER build 'base product + add-ons' where the base configuration "
        "is implicit.** Every configurable feature MUST have an explicit group "
        "with ALL variants as separate options — including the 'standard' variant."
    )
    lines.append("")
    lines.append(
        "**Why?** Without an explicit option for the standard variant, "
        "no BOM item can carry a `usage_subclause` referencing it. "
        "The configurator can only activate BOM lines linked to selected "
        "options — it cannot remove an implicit baseline."
    )
    lines.append("")
    lines.append("**Example — WRONG (classic pricelist):**")
    lines.append(
        'Product comes with 17" wheels as standard. '
        "Option '19 inch' (price: 500). "
        "Problem: no BOM item can have a usage_subclause for the "
        '17" wheels because no option represents them.'
    )
    lines.append("")
    lines.append("**Example — CORRECT (BOM-aware):**")
    lines.append(
        "Group 'Wheels' (is_multi: false): "
        "Option '17 inch' (recommended: true, price: 0), "
        "Option '19 inch' (recommended: false, price: 500). "
        "BOM: child_part '17-inch wheel assy' with "
        "usage_subclauses: [{option_id: <17_inch>, factor: 1.0}]; "
        "child_part '19-inch wheel assy' with "
        "usage_subclauses: [{option_id: <19_inch>, factor: 1.0}]."
    )
    lines.append("")

    # Data model
    lines.append("### Rattle Data Model")
    lines.append("")
    lines.append("```")
    lines.append("Product")
    lines.append("  ├── Areas (configurable sections, assigned via /products/{id}/areas)")
    lines.append("  │   └── Groups (linked to areas, is_multi: single/multi-select)")
    lines.append("  │       └── Options (name, price, key, recommended)")
    lines.append("  ├── Parts (physical components)")
    lines.append("  │   └── BOM items (parent→child, quantity, usage_subclauses)")
    lines.append("  └── Constraints (/constraints + /constraints/rules)")
    lines.append("```")
    lines.append("")
    lines.append(
        "- **usage_subclauses** on BOM items: "
        '`[{"option_id": 301, "factor": 1.0}]` — when option 301 is '
        "selected, this BOM line is active with quantity × factor."
    )
    lines.append(
        "- **Option area-config**: per-area overrides for option price, "
        "description, recommended flag — avoids duplicating groups."
    )
    lines.append(
        "- **Constraints**: pair-level forbidden combinations + conditional "
        'rules with `rule_json: [{"if": {"option_selected": X}, '
        '"then": {"forbid_options": [Y, Z]}}]`.'
    )
    lines.append("")

    # Configuration rules
    lines.append("### Configuration Rules")
    lines.append("")
    for r in CONFIGURATION_RULES:
        lines.append(f"- **{r['id']}**: {r['rule']}")
    lines.append("")

    # Anti-patterns
    lines.append("### Anti-Patterns to Detect")
    lines.append("")
    for ap in ANTI_PATTERNS:
        lines.append(f"- **{ap['name']}** (`{ap['id']}`): {ap['description']}")
        lines.append(f"  - Indicators: {', '.join(ap['indicators'])}")
        lines.append(f"  - Correction: {ap['correction']}")
    lines.append("")

    # New commands
    lines.append("### AI Commands for Configuration")
    lines.append("")
    lines.append(
        "- `rattle <tenant> ai-analyse-pricelist <file>` — "
        "Analyse a pricelist for configurator anti-patterns"
    )
    lines.append(
        "- `rattle <tenant> ai-suggest-config <file>` — "
        "Generate BOM-aware configuration recommendations "
        "(reuses existing groups, suggests forbidden combinations)"
    )
    lines.append("")

    return "\n".join(lines)
