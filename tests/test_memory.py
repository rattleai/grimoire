"""Tests for rattle_api.memory — per-tenant explicit memory layer."""

from __future__ import annotations

import pytest

from rattle_api.memory import DECISION_INJECT_LIMIT, TenantMemory


@pytest.fixture
def mem(tmp_path):
    """Return a TenantMemory rooted in a fresh temp directory per test."""
    return TenantMemory("testco", root=tmp_path)


# ---------------------------------------------------------------------------
# Profile round-trip
# ---------------------------------------------------------------------------


class TestProfile:
    def test_missing_profile_returns_empty_string(self, mem):
        assert mem.profile == ""

    def test_write_then_read(self, mem):
        mem.write_profile("# testco — tenant preferences\n\nhello\n")
        assert "hello" in mem.profile
        assert mem.profile_path.exists()

    def test_write_creates_tenant_dir(self, mem):
        assert not mem.dir.exists()
        mem.write_profile("content")
        assert mem.dir.exists()
        assert mem.profile_path.read_text(encoding="utf-8") == "content"


class TestSetPreference:
    def test_creates_profile_with_preferences_section(self, mem):
        mem.set_preference("custom-keys", "never")
        profile = mem.profile
        assert "# testco — tenant preferences" in profile
        assert "## Preferences" in profile
        assert "- **custom-keys**: never" in profile

    def test_appends_preferences_section_if_missing(self, mem):
        mem.write_profile("# testco\n\nsome notes\n")
        mem.set_preference("custom-keys", "never")
        profile = mem.profile
        assert "some notes" in profile
        assert "## Preferences" in profile
        assert "- **custom-keys**: never" in profile

    def test_replaces_existing_preference_in_place(self, mem):
        mem.set_preference("custom-keys", "never")
        mem.set_preference("custom-keys", "always")
        profile = mem.profile
        # Only one line with custom-keys
        matching = [line for line in profile.splitlines() if line.startswith("- **custom-keys**")]
        assert len(matching) == 1
        assert matching[0] == "- **custom-keys**: always"

    def test_inserts_new_preference_without_disturbing_others(self, mem):
        mem.set_preference("custom-keys", "never")
        mem.set_preference("area-without-groups", "forbidden")
        profile = mem.profile
        assert "- **custom-keys**: never" in profile
        assert "- **area-without-groups**: forbidden" in profile

    def test_empty_key_rejected(self, mem):
        with pytest.raises(ValueError):
            mem.set_preference("  ", "value")

    def test_places_pref_above_next_section(self, mem):
        mem.write_profile(
            "# testco\n\n## Preferences\n- **existing**: keep\n\n## Style\n- em-dash\n"
        )
        mem.set_preference("new-pref", "added")
        profile = mem.profile
        # New preference must appear before the "## Style" heading.
        idx_pref = profile.index("- **new-pref**: added")
        idx_style = profile.index("## Style")
        assert idx_pref < idx_style


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


class TestDecisions:
    def test_missing_decisions_returns_empty_list(self, mem):
        assert mem.load_decisions() == []

    def test_append_and_read(self, mem):
        mem.append_decision({"text": "use per-area overrides"})
        entries = mem.load_decisions()
        assert len(entries) == 1
        assert entries[0]["text"] == "use per-area overrides"
        assert "timestamp" in entries[0]

    def test_append_respects_provided_timestamp(self, mem):
        mem.append_decision({"text": "manual timestamp", "timestamp": "2020-01-01T00:00:00+00:00"})
        entry = mem.load_decisions()[0]
        assert entry["timestamp"] == "2020-01-01T00:00:00+00:00"

    def test_load_with_limit(self, mem):
        for i in range(10):
            mem.append_decision({"text": f"d{i}"})
        assert len(mem.load_decisions(limit=3)) == 3
        assert mem.load_decisions(limit=3)[-1]["text"] == "d9"

    def test_skips_malformed_jsonl_lines(self, mem):
        mem.append_decision({"text": "ok"})
        with mem.decisions_path.open("a", encoding="utf-8") as f:
            f.write("this is not json\n")
        mem.append_decision({"text": "also ok"})

        entries = mem.load_decisions()
        assert len(entries) == 2
        assert [e["text"] for e in entries] == ["ok", "also ok"]


# ---------------------------------------------------------------------------
# Audit history
# ---------------------------------------------------------------------------


class TestAuditHistory:
    def test_record_and_load(self, mem):
        mem.record_audit([{"check_id": "areas-without-groups", "entity_id": 42}])
        history = mem.load_audit_history()
        assert len(history) == 1
        assert history[0]["findings"][0]["check_id"] == "areas-without-groups"
        assert "timestamp" in history[0]

    def test_limit(self, mem):
        for _ in range(5):
            mem.record_audit([{"check_id": "x"}])
        assert len(mem.load_audit_history(limit=2)) == 2


# ---------------------------------------------------------------------------
# Catalogue state
# ---------------------------------------------------------------------------


class TestCatalogueState:
    def test_missing_returns_empty_dict(self, mem):
        assert mem.load_catalogue_state() == {}

    def test_save_and_load(self, mem):
        state = {"products": {"Widget Pro": 1}, "groups": {"tslots": 10}}
        mem.save_catalogue_state(state)
        assert mem.load_catalogue_state() == state

    def test_malformed_json_returns_empty(self, mem):
        mem.dir.mkdir(parents=True, exist_ok=True)
        mem.catalogue_state_path.write_text("not json", encoding="utf-8")
        assert mem.load_catalogue_state() == {}


# ---------------------------------------------------------------------------
# Prompt injection
# ---------------------------------------------------------------------------


class TestInjectIntoPrompt:
    def test_empty_tenant_returns_empty_string(self, mem):
        assert mem.inject_into_prompt() == ""

    def test_profile_only(self, mem):
        mem.write_profile("# testco\n\n- custom-keys: never\n")
        injected = mem.inject_into_prompt()
        assert "testco" in injected
        assert "custom-keys" in injected
        # No decisions yet → no recent section
        assert "Recent decisions" not in injected

    def test_decisions_only(self, mem):
        mem.append_decision({"text": "use per-area overrides"})
        injected = mem.inject_into_prompt()
        assert "Recent decisions" in injected
        assert "use per-area overrides" in injected

    def test_profile_and_decisions_combined(self, mem):
        mem.write_profile("# testco\n\n- minimal keys\n")
        mem.append_decision({"text": "decision 1"})
        injected = mem.inject_into_prompt()
        assert "testco" in injected
        assert "decision 1" in injected
        assert "Recent decisions" in injected

    def test_bounded_to_decision_inject_limit(self, mem):
        for i in range(DECISION_INJECT_LIMIT + 5):
            mem.append_decision({"text": f"d{i}"})
        injected = mem.inject_into_prompt()
        # Only the last DECISION_INJECT_LIMIT decisions should appear
        for i in range(DECISION_INJECT_LIMIT):
            assert f"d{i + 5}" in injected, f"missing d{i + 5}"
        # Earliest ones should be absent
        assert "d0" not in injected
        assert "d1" not in injected

    def test_decision_date_is_prefixed(self, mem):
        mem.append_decision({"text": "foo", "timestamp": "2026-04-13T10:20:30+00:00"})
        injected = mem.inject_into_prompt()
        assert "2026-04-13" in injected


# ---------------------------------------------------------------------------
# Multiple tenants are isolated
# ---------------------------------------------------------------------------


class TestTenantIsolation:
    def test_tenants_do_not_share_profile(self, tmp_path):
        a = TenantMemory("alpha", root=tmp_path)
        b = TenantMemory("beta", root=tmp_path)
        a.write_profile("alpha content")
        assert a.profile == "alpha content"
        assert b.profile == ""

    def test_tenants_do_not_share_decisions(self, tmp_path):
        a = TenantMemory("alpha", root=tmp_path)
        b = TenantMemory("beta", root=tmp_path)
        a.append_decision({"text": "alpha decision"})
        assert len(a.load_decisions()) == 1
        assert b.load_decisions() == []

    def test_tenant_name_is_lowercased(self, tmp_path):
        upper = TenantMemory("ACME", root=tmp_path)
        lower = TenantMemory("acme", root=tmp_path)
        upper.write_profile("from upper")
        assert lower.profile == "from upper"
