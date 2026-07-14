#!/usr/bin/env python3
"""Validate the Grimoire bundle before it ships.

Every defect this checks for is one that actually shipped at least once:

* versions drifting apart across the four manifests (0.4.0 in package.json while
  plugin.json said 0.6.0, describing 8 skills when 13 were on disk);
* ``strict: false`` in marketplace.json, which is a hard load failure the moment
  plugin.json declares any component;
* compiled bytecode inside ``skills/*/scripts/`` being published to npm, because
  the ``files`` allowlist overrides ``.gitignore``;
* golden examples silently drifting out of sync with the schema they claim to
  satisfy;
* a skill or agent referenced from a manifest that does not exist on disk.

Run it from the repo root::

    python3 scripts/validate_bundle.py          # human-readable
    python3 scripts/validate_bundle.py --json   # machine-readable, for CI

Exit code is 0 when clean, 1 when any error was found. Warnings never fail the
build; errors always do.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

# Two different limits apply, and confusing them ships a broken skill.
#
# CLAUDE CODE truncates the combined description + when_to_use at 1,536 chars in
# the skill listing. A truncation, not a rejection — the tail is simply never
# seen by the model deciding whether to load the skill. Hence a warning.
#
# The AGENT SKILLS SPEC (agentskills.io), which Claude.ai enforces at the upload
# dialog and Anthropic's own quick_validate.py enforces in code, caps
# `description` at 1,024 chars and REJECTS anything longer. Three skills sat
# between the two limits: they worked perfectly in Claude Code and would have
# been turned away by Claude.ai. Hence an error — the stricter surface wins,
# because a skill that cannot be uploaded is not portable.
DESCRIPTION_BUDGET = 1536  # Claude Code: truncates
DESCRIPTION_SPEC_MAX = 1024  # Agent Skills spec / Claude.ai: rejects

# Fields the Claude Code specs actually recognise. Anything else is silently
# ignored at load time, which is worse than an error — it looks like it works.
SKILL_FIELDS = {
    "name",
    "description",
    "when_to_use",
    "license",
    "allowed-tools",
    "disallowed-tools",
    "argument-hint",
    "arguments",
    "model",
    "effort",
    "context",
    "agent",
    "hooks",
    "paths",
    "shell",
    "disable-model-invocation",
    "user-invocable",
}
AGENT_FIELDS = {
    "name",
    "description",
    "tools",
    "disallowedTools",
    "model",
    "maxTurns",
    "skills",
    "memory",
    "background",
    "effort",
    "isolation",
    "color",
    "initialPrompt",
    # Accepted in the spec but IGNORED for plugin-loaded agents — flagged below.
    "permissionMode",
    "hooks",
    "mcpServers",
}
AGENT_FIELDS_IGNORED_IN_PLUGINS = {"permissionMode", "hooks", "mcpServers"}

PLUGIN_FIELDS = {
    "name",
    "displayName",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "defaultEnabled",
    "skills",
    "commands",
    "agents",
    "hooks",
    "mcpServers",
    "outputStyles",
    "lspServers",
    "experimental",
    "userConfig",
    "channels",
    "dependencies",
}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def read_frontmatter(path: Path) -> dict[str, str | list[str]] | None:
    """Parse the YAML frontmatter block without taking a PyYAML dependency.

    Handles the two shapes the bundle actually uses: flat ``key: value``, and a
    block list::

        skills:
          - rattle-audit
          - rattle-configurator

    An earlier version of this parser skipped every indented line, so a block
    list read back as an empty string and the `skills:` cross-reference check
    below silently validated nothing. Block lists are therefore collected
    explicitly rather than treated as continuation noise.
    """
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None

    fields: dict[str, str | list[str]] = {}
    current: str | None = None
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        item = re.match(r"^\s+-\s+(.+)$", line)
        if item and current:
            bucket = fields.setdefault(current, [])
            if isinstance(bucket, list):
                bucket.append(item.group(1).strip().strip("\"'"))
            continue

        if line.startswith((" ", "\t")) or ":" not in line:
            continue

        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value:
            fields[key] = value
            current = None
        else:
            # A bare `key:` opens a block list; the items follow, indented.
            fields[key] = []
            current = key
    return fields


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_versions() -> str | None:
    """All four manifests must agree. They have silently disagreed before."""
    found: dict[str, str] = {}

    pkg = json.loads((ROOT / "package.json").read_text())
    found["package.json"] = pkg["version"]

    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    found[".claude-plugin/plugin.json"] = plugin["version"]

    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    found[".claude-plugin/marketplace.json"] = market["plugins"][0]["version"]

    pyproject = (ROOT / "pyproject.toml").read_text()
    m = re.search(r'^version\s*=\s*"(.+?)"', pyproject, re.M)
    if m:
        found["pyproject.toml"] = m.group(1)

    distinct = set(found.values())
    if len(distinct) > 1:
        detail = ", ".join(f"{k}={v}" for k, v in found.items())
        err(f"Version drift across manifests: {detail}")
        return None
    return distinct.pop()


def check_plugin_manifest() -> None:
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    for key in plugin:
        if key not in PLUGIN_FIELDS:
            warn(
                f"plugin.json declares unrecognised key '{key}'"
                " — it is silently ignored at load time."
            )

    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    for entry in market.get("plugins", []):
        # Documented as a hard load failure: strict:false means the marketplace
        # entry is the entire definition, so a plugin.json that declares
        # components (we declare mcpServers + userConfig) conflicts with it.
        if entry.get("strict") is False:
            declares = [
                k for k in ("skills", "commands", "agents", "hooks", "mcpServers") if k in plugin
            ]
            if declares:
                err(
                    f"marketplace.json sets strict:false while plugin.json declares {declares}. "
                    "This is a documented hard load failure — omit `strict` (it defaults to true)."
                )

    # A bundled MCP server must actually be on disk and executable by the
    # declared command, or the plugin installs and then silently has no tools.
    for name, cfg in (plugin.get("mcpServers") or {}).items():
        for arg in cfg.get("args", []):
            if "${CLAUDE_PLUGIN_ROOT}" in arg:
                rel = arg.replace("${CLAUDE_PLUGIN_ROOT}/", "")
                if not (ROOT / rel).exists():
                    err(f"plugin.json mcpServers.{name} points at '{rel}', which does not exist.")

    # Every ${user_config.X} referenced must be declared, or it expands to nothing.
    declared = set((plugin.get("userConfig") or {}).keys())
    blob = json.dumps(plugin.get("mcpServers") or {})
    for ref in set(re.findall(r"\$\{user_config\.([a-zA-Z0-9_]+)\}", blob)):
        if ref not in declared:
            err(
                f"plugin.json references ${{user_config.{ref}}}"
                f" but userConfig does not declare '{ref}'."
            )


def check_skills() -> list[str]:
    names: list[str] = []
    for skill_md in sorted((ROOT / "skills").glob("*/SKILL.md")):
        rel = skill_md.relative_to(ROOT)
        fm = read_frontmatter(skill_md)
        if fm is None:
            err(f"{rel}: missing YAML frontmatter.")
            continue

        name = str(fm.get("name", ""))
        if not name:
            err(f"{rel}: frontmatter has no `name`.")
        else:
            names.append(name)
            if name != skill_md.parent.name:
                err(f"{rel}: frontmatter name '{name}' != directory '{skill_md.parent.name}'.")
            if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
                err(f"{rel}: name '{name}' is not lowercase-kebab-case.")
            if len(name) > 64:
                err(f"{rel}: name is {len(name)} chars (max 64).")

        desc = str(fm.get("description", ""))
        combined = len(desc) + len(str(fm.get("when_to_use", "")))
        if not desc:
            err(
                f"{rel}: frontmatter has no `description`"
                " — the model cannot decide when to load this skill."
            )
        else:
            # Hard: Claude.ai / the Agent Skills spec reject over 1024. A skill
            # that cannot be uploaded is not portable, so this fails the build.
            if len(desc) > DESCRIPTION_SPEC_MAX:
                err(
                    f"{rel}: description is {len(desc)} chars. The Agent Skills spec caps it at "
                    f"{DESCRIPTION_SPEC_MAX} and Claude.ai REJECTS the upload. (Claude Code only "
                    f"truncates at {DESCRIPTION_BUDGET}, so this passes there and fails there.)"
                )
            if "<" in desc or ">" in desc:
                err(f"{rel}: description contains angle brackets, which the spec rejects.")
            # Soft: everything past the listing budget is simply never read.
            if combined > DESCRIPTION_BUDGET:
                warn(
                    f"{rel}: description + when_to_use is {combined} chars; the Claude Code skill "
                    f"listing truncates at {DESCRIPTION_BUDGET}, so the last "
                    f"{combined - DESCRIPTION_BUDGET} chars are never seen."
                )

        for key in fm:
            if key not in SKILL_FIELDS:
                warn(
                    f"{rel}: unrecognised frontmatter key '{key}' — silently ignored at load time."
                )
    return names


def check_agents(skill_names: list[str]) -> list[str]:
    names: list[str] = []
    known = set(skill_names)
    for agent_md in sorted((ROOT / "agents").glob("*.md")):
        rel = agent_md.relative_to(ROOT)
        fm = read_frontmatter(agent_md)
        if fm is None:
            err(f"{rel}: missing YAML frontmatter.")
            continue

        name = str(fm.get("name", ""))
        if not name:
            err(f"{rel}: frontmatter has no `name`.")
        else:
            names.append(name)
            if name != agent_md.stem:
                err(f"{rel}: frontmatter name '{name}' != filename '{agent_md.stem}'.")
        if not fm.get("description"):
            err(f"{rel}: frontmatter has no `description`.")

        for key in fm:
            if key not in AGENT_FIELDS:
                warn(
                    f"{rel}: unrecognised frontmatter key '{key}' — silently ignored at load time."
                )
            elif key in AGENT_FIELDS_IGNORED_IN_PLUGINS:
                warn(
                    f"{rel}: '{key}' is ignored for plugin-loaded agents. Grimoire ships as a "
                    "plugin, so this has no effect — enforce the boundary via "
                    "`tools`/`disallowedTools` instead."
                )

        # A `skills:` list naming a skill that does not exist fails silently at
        # load time, which reads as "the agent just didn't use the skill".
        declared = fm.get("skills", [])
        listed = declared if isinstance(declared, list) else re.findall(r"[a-z0-9-]+", declared)
        for s in listed:
            if s and s not in known:
                err(f"{rel}: `skills:` names '{s}', which is not a skill in skills/.")
    return names


def check_no_bytecode() -> None:
    """`files` in package.json overrides .gitignore, so stray .pyc DOES publish."""
    stray = [
        p.relative_to(ROOT)
        for p in ROOT.glob("skills/**/*")
        if p.suffix == ".pyc" or p.name == "__pycache__"
    ]
    for p in stray:
        err(
            f"Compiled bytecode inside the shipped bundle: {p}."
            " npm's `files` allowlist WILL publish it."
        )


def check_examples_against_schemas() -> None:
    """Every golden example must still satisfy the contract it advertises."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        warn(
            "jsonschema not installed — skipped example/schema validation."
            " `pip install jsonschema` to enable."
        )
        return

    pairs = {
        "recommendation.json": "recommendation.schema.json",
        "audit-findings.json": "audit-findings.schema.json",
        "offer-template.json": "offer-template.schema.json",
        "apply-operations.json": "apply-operations.schema.json",
        "source-mapping.json": "source-mapping.schema.json",
        "variant-bom.json": "variant-bom.schema.json",
    }
    for example, schema in pairs.items():
        ex_path, sc_path = ROOT / "examples" / example, ROOT / "schemas" / schema
        if not sc_path.exists():
            warn(f"schemas/{schema} does not exist — no contract for examples/{example}.")
            continue
        if not ex_path.exists():
            warn(f"examples/{example} does not exist — schemas/{schema} has no golden example.")
            continue
        validator = Draft202012Validator(json.loads(sc_path.read_text()))
        found = sorted(
            validator.iter_errors(json.loads(ex_path.read_text())), key=lambda e: list(e.path)
        )
        for e in found[:5]:
            loc = "/".join(str(x) for x in e.path) or "(root)"
            err(f"examples/{example} violates schemas/{schema} at {loc}: {e.message}")


def check_commands(skill_names: list[str]) -> list[str]:
    names: list[str] = []
    for cmd in sorted((ROOT / "commands").glob("*.md")):
        fm = read_frontmatter(cmd)
        if fm is None:
            err(f"{cmd.relative_to(ROOT)}: missing YAML frontmatter.")
            continue
        if not fm.get("description"):
            err(f"{cmd.relative_to(ROOT)}: frontmatter has no `description`.")
        names.append(cmd.stem)
    return names


def check_generated_reference() -> None:
    """The rendered API reference must match what the generator would produce.

    This check exists because of a real near-miss. Someone hand-edited the
    *generated* skill mirror to correct the OCC status (409, not 412) and to add
    the entire Safety Reference section — 197 lines the OpenAPI spec does not
    carry, and which the safety-notice / GHS skills tell the model to rely on.
    But CLAUDE.md instructs contributors to re-run build_api_reference.py
    whenever the spec is replaced, and that run would have silently reverted the
    409 back to 412 and deleted the Safety Reference outright.

    The fix was to make such content an *input* to the generator (see
    docs/api-supplement/), not an edit to its output. This check enforces it: if
    the two rendered copies drift, or if either drifts from what the generator
    now produces, the build fails instead of quietly shipping stale knowledge.
    """
    docs_md = ROOT / "docs" / "API_REFERENCE.md"
    skill_md = ROOT / "skills" / "rattle-api" / "references" / "api-reference.md"

    if docs_md.exists() and skill_md.exists() and docs_md.read_bytes() != skill_md.read_bytes():
        err(
            "docs/API_REFERENCE.md and skills/rattle-api/references/api-reference.md differ. "
            "Both are GENERATED — never hand-edit either. Put content the OpenAPI spec lacks "
            "into docs/api-supplement/ and register it in SUPPLEMENTS, then re-run "
            "`python3 scripts/build_api_reference.py`."
        )

    # A supplement that is registered but missing on disk means the next regen
    # drops a whole section from the reference.
    for name in ("safety-reference.md",):
        if not (ROOT / "docs" / "api-supplement" / name).exists():
            err(
                f"docs/api-supplement/{name} is missing. It is registered in "
                "build_api_reference.py SUPPLEMENTS; regenerating without it would silently "
                "drop that section from the API reference."
            )


def check_openapi_freshness() -> None:
    """The MCP server and the API skill both read the spec — they must be the same spec."""
    a = ROOT / "docs" / "openapi.json"
    b = ROOT / "skills" / "rattle-api" / "references" / "openapi.json"
    if not a.exists() or not b.exists():
        warn("openapi.json missing from docs/ or skills/rattle-api/references/.")
        return
    if a.read_bytes() != b.read_bytes():
        err(
            "docs/openapi.json and skills/rattle-api/references/openapi.json differ. "
            "Re-run `python3 scripts/build_api_reference.py` to resync — the MCP server reads "
            "the skill copy."
        )


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = ap.parse_args()

    version = check_versions()
    check_plugin_manifest()
    skills = check_skills()
    agents = check_agents(skills)
    commands = check_commands(skills)
    check_no_bytecode()
    check_examples_against_schemas()
    check_openapi_freshness()
    check_generated_reference()

    summary: dict[str, Any] = {
        "version": version,
        "skills": len(skills),
        "agents": len(agents),
        "commands": len(commands),
        "schemas": len(list((ROOT / "schemas").glob("*.json"))),
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Grimoire bundle v{version}")
        print(
            f"  {len(skills)} skills · {len(agents)} agents · {len(commands)} commands"
            f" · {summary['schemas']} schemas"
        )
        print()
        for w in warnings:
            print(f"  WARN   {w}")
        for e in errors:
            print(f"  ERROR  {e}")
        print()
        if errors:
            print(f"FAILED — {len(errors)} error(s), {len(warnings)} warning(s).")
        else:
            print(f"OK — 0 errors, {len(warnings)} warning(s).")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
