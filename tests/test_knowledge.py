"""Tests for rattle_api.knowledge — configurator consulting knowledge module."""

from rattle_api.knowledge import (
    ANTI_PATTERNS,
    CONFIGURATION_RULES,
    RATTLE_DATA_MODEL,
    STRUCTURAL_CHECKS,
    as_markdown,
    detect_anti_patterns,
    system_prompt_analyse_pricelist,
    system_prompt_apply_config,
    system_prompt_audit,
    system_prompt_base,
    system_prompt_build_offer_template,
    system_prompt_suggest_configuration,
)

# ---------------------------------------------------------------------------
# Data structure integrity
# ---------------------------------------------------------------------------


class TestRattleDataModel:
    """RATTLE_DATA_MODEL structure."""

    REQUIRED_ENTITIES = [
        "product",
        "area",
        "group",
        "option",
        "part",
        "bom_item",
        "constraint",
        "option_area_config",
        # Documents system (new in Part A)
        "document_template",
        "document_content_block",
        "document_structure_block",
        "document_attachment",
        "doc_type_layout",
    ]

    def test_has_all_entity_types(self):
        for entity in self.REQUIRED_ENTITIES:
            assert entity in RATTLE_DATA_MODEL, f"Missing entity: {entity}"

    def test_entities_have_required_fields(self):
        for name, entity in RATTLE_DATA_MODEL.items():
            assert "description" in entity, f"{name} missing description"
            assert "key_fields" in entity, f"{name} missing key_fields"
            assert "api_endpoint" in entity, f"{name} missing api_endpoint"
            assert "relationships" in entity, f"{name} missing relationships"

    def test_entities_have_non_empty_descriptions(self):
        for name, entity in RATTLE_DATA_MODEL.items():
            assert len(entity["description"]) > 10, f"{name} description too short"


class TestConfigurationRules:
    """CONFIGURATION_RULES data structure integrity."""

    REQUIRED_KEYS = {"id", "rule", "rationale", "applies_to"}

    def test_all_entries_have_required_keys(self):
        for rule in CONFIGURATION_RULES:
            missing = self.REQUIRED_KEYS - set(rule.keys())
            assert not missing, f"Rule {rule.get('id', '?')} missing keys: {missing}"

    def test_ids_are_unique(self):
        ids = [r["id"] for r in CONFIGURATION_RULES]
        assert len(ids) == len(set(ids)), f"Duplicate rule IDs: {ids}"

    def test_has_the_number_one_rule(self):
        ids = [r["id"] for r in CONFIGURATION_RULES]
        assert "explicit-options-for-all-variants" in ids

    def test_has_reuse_rule(self):
        ids = [r["id"] for r in CONFIGURATION_RULES]
        assert "reuse-over-duplicate" in ids

    def test_has_forbidden_combinations_rule(self):
        ids = [r["id"] for r in CONFIGURATION_RULES]
        assert "forbidden-combinations" in ids

    # -- new Part A rules ---------------------------------------------------

    NEW_RULE_IDS = [
        "no-empty-areas",
        "narrative-in-documents-system",
        "offer-requires-configuration-block",
        "use-system-dynamic-blocks",
        "shared-groups-across-products",
        "area-config-for-scaled-prices",
        "minimal-keys",
    ]

    def test_new_rules_present(self):
        ids = {r["id"] for r in CONFIGURATION_RULES}
        missing = [rid for rid in self.NEW_RULE_IDS if rid not in ids]
        assert not missing, f"missing new rules: {missing}"

    def test_new_rules_non_empty(self):
        for rule in CONFIGURATION_RULES:
            if rule["id"] in self.NEW_RULE_IDS:
                assert len(rule["rule"]) > 30, f"{rule['id']} rule text too short"
                assert len(rule["rationale"]) > 30, f"{rule['id']} rationale too short"
                assert rule["applies_to"], f"{rule['id']} applies_to empty"


class TestAntiPatterns:
    """ANTI_PATTERNS data structure integrity."""

    REQUIRED_KEYS = {
        "id",
        "name",
        "description",
        "indicators",
        "correction",
        "example_wrong",
        "example_correct",
    }

    def test_all_entries_have_required_keys(self):
        for ap in ANTI_PATTERNS:
            missing = self.REQUIRED_KEYS - set(ap.keys())
            assert not missing, f"Pattern {ap.get('id', '?')} missing keys: {missing}"

    def test_ids_are_unique(self):
        ids = [ap["id"] for ap in ANTI_PATTERNS]
        assert len(ids) == len(set(ids)), f"Duplicate pattern IDs: {ids}"

    def test_indicators_are_non_empty(self):
        for ap in ANTI_PATTERNS:
            assert len(ap["indicators"]) > 0, f"Pattern {ap['id']} has no indicators"

    def test_has_implicit_base_pattern(self):
        ids = [ap["id"] for ap in ANTI_PATTERNS]
        assert "implicit-base-config" in ids

    def test_has_addon_only_pattern(self):
        ids = [ap["id"] for ap in ANTI_PATTERNS]
        assert "addon-only-options" in ids

    def test_has_description_area_smell(self):
        ids = [ap["id"] for ap in ANTI_PATTERNS]
        assert "description-area-smell" in ids

    def test_has_addon_only_software_modules(self):
        ids = [ap["id"] for ap in ANTI_PATTERNS]
        assert "addon-only-software-modules" in ids


class TestStructuralChecks:
    """STRUCTURAL_CHECKS declarative specs (runners are Part C)."""

    EXPECTED_CHECKS = [
        "areas-without-groups",
        "duplicate-group-names",
        "offer-template-missing-configuration",
        "duplicate-dynamic-wrappers",
        "options-with-custom-keys",
        "options-with-conflicting-area-overrides",
    ]

    def test_all_expected_checks_present(self):
        for cid in self.EXPECTED_CHECKS:
            assert cid in STRUCTURAL_CHECKS, f"missing structural check: {cid}"

    def test_all_checks_have_required_fields(self):
        for cid, spec in STRUCTURAL_CHECKS.items():
            assert "name" in spec, f"{cid} missing name"
            assert "description" in spec, f"{cid} missing description"
            assert "severity" in spec, f"{cid} missing severity"
            assert spec["severity"] in {"error", "warning", "info"}, (
                f"{cid} invalid severity: {spec['severity']}"
            )
            assert "check_spec" in spec, f"{cid} missing check_spec"
            assert "related_rules" in spec, f"{cid} missing related_rules"

    def test_related_rules_reference_existing_rules(self):
        rule_ids = {r["id"] for r in CONFIGURATION_RULES}
        for cid, spec in STRUCTURAL_CHECKS.items():
            for related in spec["related_rules"]:
                assert related in rule_ids, f"{cid} references unknown rule '{related}'"


# ---------------------------------------------------------------------------
# System prompt builders
# ---------------------------------------------------------------------------


class TestSystemPromptBase:
    """system_prompt_base() — core consulting rules fragment."""

    def test_contains_the_number_one_rule(self):
        prompt = system_prompt_base()
        assert "NEVER build" in prompt
        assert "base product" in prompt
        assert "implicit" in prompt

    def test_contains_data_model(self):
        prompt = system_prompt_base()
        assert "usage_subclauses" in prompt
        assert "Groups" in prompt
        assert "Options" in prompt
        assert "BOM" in prompt

    def test_contains_car_example(self):
        prompt = system_prompt_base()
        assert "17" in prompt or "wheels" in prompt.lower()

    def test_contains_all_rule_ids(self):
        prompt = system_prompt_base()
        for rule in CONFIGURATION_RULES:
            assert rule["id"] in prompt, f"Rule {rule['id']} missing from base prompt"

    def test_contains_anti_pattern_names(self):
        prompt = system_prompt_base()
        for ap in ANTI_PATTERNS:
            assert ap["name"] in prompt, f"Anti-pattern {ap['name']} missing from base prompt"

    def test_mentions_documents_system(self):
        """The base prompt should cover the documents-system vocabulary (Part A)."""
        prompt = system_prompt_base()
        assert "documents system" in prompt.lower() or "document_template" in prompt
        assert "dynamic:document_configuration" in prompt
        assert "is_dynamic" in prompt

    def test_empty_tenant_profile_does_not_add_section(self):
        prompt = system_prompt_base(tenant_profile=None)
        assert "Tenant preferences" not in prompt

        prompt2 = system_prompt_base(tenant_profile="")
        assert "Tenant preferences" not in prompt2

        prompt3 = system_prompt_base(tenant_profile="   \n  \n")
        assert "Tenant preferences" not in prompt3

    def test_tenant_profile_is_embedded(self):
        profile = "- **custom-keys**: never\n- **area-without-groups**: forbidden"
        prompt = system_prompt_base(tenant_profile=profile)
        assert "## Tenant preferences" in prompt
        assert "custom-keys" in prompt
        assert "area-without-groups" in prompt


class TestSystemPromptAnalysePricelist:
    """system_prompt_analyse_pricelist() — pricelist analysis prompt."""

    def test_contains_base_rules(self):
        prompt = system_prompt_analyse_pricelist()
        assert "NEVER build" in prompt

    def test_default_language_german(self):
        prompt = system_prompt_analyse_pricelist()
        assert "German" in prompt

    def test_custom_language(self):
        prompt = system_prompt_analyse_pricelist(language="en")
        assert "en" in prompt

    def test_requests_json_output(self):
        prompt = system_prompt_analyse_pricelist()
        assert "JSON" in prompt

    def test_requests_anti_pattern_detection(self):
        prompt = system_prompt_analyse_pricelist()
        assert "anti_patterns" in prompt.lower() or "Anti-patterns" in prompt


class TestSystemPromptSuggestConfiguration:
    """system_prompt_suggest_configuration() — configuration suggestion prompt."""

    def test_contains_bom_rules(self):
        prompt = system_prompt_suggest_configuration()
        assert "BOM" in prompt or "usage_subclause" in prompt

    def test_contains_forbidden_combinations(self):
        prompt = system_prompt_suggest_configuration()
        assert "forbidden" in prompt.lower()

    def test_default_language_german(self):
        prompt = system_prompt_suggest_configuration()
        assert "German" in prompt

    def test_without_existing_groups(self):
        prompt = system_prompt_suggest_configuration()
        assert "Existing Groups" not in prompt

    def test_with_existing_groups(self):
        groups = [
            {"id": 100, "name": "Frässpindel", "options": [{"label": "ISO 30"}]},
        ]
        prompt = system_prompt_suggest_configuration(existing_groups=groups)
        assert "Frässpindel" in prompt
        assert "reuse_existing" in prompt
        assert "price" in prompt.lower()

    def test_requests_json_output(self):
        prompt = system_prompt_suggest_configuration()
        assert "JSON" in prompt

    def test_tenant_profile_is_threaded(self):
        prompt = system_prompt_suggest_configuration(
            tenant_profile="- **custom-keys**: never",
        )
        assert "## Tenant preferences" in prompt
        assert "custom-keys" in prompt


class TestSystemPromptBuildOfferTemplate:
    """system_prompt_build_offer_template() — Part A offer template helper."""

    def test_without_context_contains_task(self):
        prompt = system_prompt_build_offer_template()
        assert "Your Task" in prompt
        assert "Product Overview" in prompt
        assert "dynamic:document_configuration" in prompt

    def test_with_doc_type_layout(self):
        layout = {
            "key": "offer",
            "requires_configuration": True,
            "default_layout": [
                {
                    "slug": "configuration",
                    "title": "Configuration",
                    "dynamic_key": "dynamic:document_configuration",
                },
                {
                    "slug": "price_summary",
                    "title": "Price Summary",
                    "dynamic_key": "dynamic:document_pricing",
                },
            ],
        }
        prompt = system_prompt_build_offer_template(doc_type_layout=layout)
        assert "Target doc_type contract" in prompt
        assert "configuration" in prompt
        assert "price_summary" in prompt
        assert "requires_configuration=True" in prompt

    def test_with_dynamic_content_blocks(self):
        dyn = [
            {"id": 264, "key": "dynamic:document_configuration", "title": "Config"},
            {"id": 265, "key": "dynamic:document_pricing", "title": "Pricing"},
        ]
        prompt = system_prompt_build_offer_template(dynamic_content_blocks=dyn)
        assert "id=264" in prompt
        assert "dynamic:document_configuration" in prompt
        assert "NEVER create a new content block" in prompt

    def test_threads_tenant_profile(self):
        prompt = system_prompt_build_offer_template(
            tenant_profile="- **custom-keys**: never",
        )
        assert "## Tenant preferences" in prompt


class TestSystemPromptAudit:
    """system_prompt_audit() — Part A audit triage helper."""

    def test_lists_all_checks(self):
        prompt = system_prompt_audit()
        for cid in STRUCTURAL_CHECKS:
            assert cid in prompt, f"check {cid} missing from audit prompt"

    def test_embeds_findings(self):
        findings = [
            {
                "check_id": "areas-without-groups",
                "severity": "error",
                "entity_type": "area",
                "entity_id": 42,
                "message": "Area 'Description' has 0 groups",
            },
        ]
        prompt = system_prompt_audit(findings=findings)
        assert "areas-without-groups" in prompt
        assert "42" in prompt
        assert "has 0 groups" in prompt

    def test_requests_json_output(self):
        prompt = system_prompt_audit()
        assert "JSON" in prompt


class TestSystemPromptApplyConfig:
    """system_prompt_apply_config() — Part A recommendation-to-REST helper."""

    def test_contains_ensure_operations(self):
        prompt = system_prompt_apply_config()
        for op in (
            "ensure_product",
            "ensure_area",
            "ensure_group",
            "ensure_option",
            "ensure_area_config",
            "ensure_constraint_pair",
            "ensure_constraint_rule",
        ):
            assert op in prompt, f"missing op: {op}"

    def test_embeds_recommendation(self):
        rec = {"products": [{"name": "Widget Pro", "groups": []}]}
        prompt = system_prompt_apply_config(recommendation=rec)
        assert "Widget Pro" in prompt

    def test_mentions_no_empty_areas_rule(self):
        prompt = system_prompt_apply_config()
        assert "no-empty-areas" in prompt


# ---------------------------------------------------------------------------
# Heuristic anti-pattern detection
# ---------------------------------------------------------------------------


class TestDetectAntiPatterns:
    """detect_anti_patterns() — heuristic scan of Excel data."""

    def test_detects_aufpreis_pattern(self):
        data = [{"Feature": "Aufpreis Frässpindel HSK-63F", "Price": 2500}]
        results = detect_anti_patterns(data)
        assert len(results) >= 1
        pattern_ids = {r["pattern_id"] for r in results}
        assert "addon-only-options" in pattern_ids

    def test_detects_standard_implicit(self):
        data = [{"Description": "Serienausstattung: 17 Zoll Räder"}]
        results = detect_anti_patterns(data)
        pattern_ids = {r["pattern_id"] for r in results}
        assert "implicit-base-config" in pattern_ids

    def test_clean_data_returns_empty(self):
        data = [
            {"Name": "Drill X100", "Price": 500},
            {"Name": "Saw Z3", "Price": 200},
        ]
        results = detect_anti_patterns(data)
        assert results == []

    def test_returns_row_references(self):
        data = [
            {"Feature": "Normal feature"},
            {"Feature": "Aufpreis: extra widget"},
        ]
        results = detect_anti_patterns(data)
        assert any(r["row_index"] == 1 for r in results)

    def test_returns_column_references(self):
        data = [{"Price": "Aufpreis 100€"}]
        results = detect_anti_patterns(data)
        assert results[0]["column"] == "Price"

    def test_handles_none_values(self):
        data = [{"A": None, "B": "text", "C": None}]
        results = detect_anti_patterns(data)
        assert results == []

    def test_handles_empty_data(self):
        assert detect_anti_patterns([]) == []

    def test_truncates_long_values(self):
        data = [{"Feature": "Aufpreis " + "x" * 500}]
        results = detect_anti_patterns(data)
        assert len(results[0]["value"]) <= 200


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------


class TestAsMarkdown:
    """as_markdown() — knowledge export as Markdown."""

    def test_contains_header(self):
        md = as_markdown()
        assert "## Configurator Consulting Knowledge" in md

    def test_contains_the_number_one_rule(self):
        md = as_markdown()
        assert "NEVER build" in md
        assert "base product" in md

    def test_contains_all_configuration_rules(self):
        md = as_markdown()
        for rule in CONFIGURATION_RULES:
            assert rule["id"] in md, f"Rule {rule['id']} missing from markdown"

    def test_contains_all_anti_patterns(self):
        md = as_markdown()
        for ap in ANTI_PATTERNS:
            assert ap["name"] in md, f"Anti-pattern {ap['name']} missing from markdown"

    def test_contains_data_model(self):
        md = as_markdown()
        assert "Product" in md
        assert "Groups" in md
        assert "Options" in md
        assert "usage_subclauses" in md
        assert "BOM" in md

    def test_contains_cli_commands(self):
        md = as_markdown()
        assert "ai-analyse-pricelist" in md
        assert "ai-suggest-config" in md

    def test_is_nonempty_string(self):
        md = as_markdown()
        assert isinstance(md, str)
        assert len(md) > 500
