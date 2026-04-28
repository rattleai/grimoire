"""Tenant memory — small, explicit, file-based per-tenant preferences.

Memory lives under ``memory/<tenant>/`` at the project root:

- ``profile.md`` — curated, human-edited tenant preferences & style. Committed
  to git so the team shares it.
- ``decisions.jsonl`` — append-only log of decisions the user explicitly
  chose to record (gitignored).
- ``audit_history.jsonl`` — append-only log of structural audit findings
  over time (gitignored, populated by the Part C follow-up).
- ``catalogue_state.json`` — optional id cache for idempotent re-runs
  (gitignored, populated by the Part C builder).

Reads are automatic — ``TenantMemory.inject_into_prompt`` is called by
``system_prompt_*`` builders via the ``tenant_profile`` parameter.
Writes are **only** triggered by explicit ``rattle <tenant> memory …``
CLI commands; task functions never write to memory silently.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# The package lives at ``rattle_api/``; the project root is one level up.
_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MEMORY_ROOT = _ROOT / "memory"

PROFILE_FILENAME = "profile.md"
DECISIONS_FILENAME = "decisions.jsonl"
AUDIT_FILENAME = "audit_history.jsonl"
CATALOGUE_STATE_FILENAME = "catalogue_state.json"

# Only this many recent decisions are injected into prompts to keep the
# prompt size bounded as the log grows.
DECISION_INJECT_LIMIT = 5

# Default heading used when writing preferences via set-preference.
PREFERENCES_HEADING = "## Preferences"


class TenantMemory:
    """Per-tenant memory accessor — reads are cheap, writes are explicit."""

    def __init__(self, tenant: str, root: str | os.PathLike[str] | None = None):
        self.tenant = tenant.lower()
        self.root = Path(root) if root is not None else DEFAULT_MEMORY_ROOT
        self.dir = self.root / self.tenant

    # -- paths ---------------------------------------------------------------

    @property
    def profile_path(self) -> Path:
        return self.dir / PROFILE_FILENAME

    @property
    def decisions_path(self) -> Path:
        return self.dir / DECISIONS_FILENAME

    @property
    def audit_path(self) -> Path:
        return self.dir / AUDIT_FILENAME

    @property
    def catalogue_state_path(self) -> Path:
        return self.dir / CATALOGUE_STATE_FILENAME

    # -- profile -------------------------------------------------------------

    @property
    def profile(self) -> str:
        """Return the contents of ``profile.md`` (empty string if missing)."""
        try:
            return self.profile_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def write_profile(self, markdown: str) -> None:
        """Overwrite ``profile.md`` with the given markdown, creating the dir."""
        self.dir.mkdir(parents=True, exist_ok=True)
        self.profile_path.write_text(markdown, encoding="utf-8")

    def set_preference(self, key: str, value: str) -> None:
        """Upsert a ``- **<key>**: <value>`` line under ``## Preferences``.

        Creates ``profile.md`` and the preferences heading on first use.
        If a line with the same key already exists, its value is replaced
        in-place — no duplicate lines are introduced.
        """
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError("preference key must be non-empty")

        current = self.profile
        line_prefix = f"- **{key}**: "
        new_line = f"{line_prefix}{value}"

        if not current:
            header = f"# {self.tenant} — tenant preferences\n\n"
            body = f"{PREFERENCES_HEADING}\n{new_line}\n"
            self.write_profile(header + body)
            return

        if PREFERENCES_HEADING not in current:
            if not current.endswith("\n"):
                current += "\n"
            current += f"\n{PREFERENCES_HEADING}\n{new_line}\n"
            self.write_profile(current)
            return

        # Heading exists; check whether the key line is already present.
        lines = current.splitlines()
        new_lines: list[str] = []
        replaced = False
        in_prefs = False
        inserted = False
        for line in lines:
            if line.strip() == PREFERENCES_HEADING:
                in_prefs = True
                new_lines.append(line)
                continue
            if in_prefs and line.startswith("## "):
                # Next section started — insert the line here if not replaced.
                if not replaced and not inserted:
                    new_lines.append(new_line)
                    inserted = True
                in_prefs = False
            if in_prefs and line.startswith(line_prefix):
                new_lines.append(new_line)
                replaced = True
                continue
            new_lines.append(line)

        if not replaced and not inserted:
            # Still inside the preferences section at EOF.
            new_lines.append(new_line)

        output = "\n".join(new_lines)
        if not output.endswith("\n"):
            output += "\n"
        self.write_profile(output)

    # -- decisions -----------------------------------------------------------

    def append_decision(self, decision: dict) -> dict:
        """Append a decision record to ``decisions.jsonl``.

        A ``timestamp`` field (UTC ISO 8601) is added automatically if not
        provided. Returns the decision as written (with timestamp populated).
        """
        record = dict(decision)
        record.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        self.dir.mkdir(parents=True, exist_ok=True)
        with self.decisions_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def load_decisions(self, *, limit: int | None = None) -> list[dict]:
        """Read decisions.jsonl, optionally limited to the last ``limit`` rows."""
        try:
            raw = self.decisions_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        entries: list[dict] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                # Skip malformed lines rather than failing the whole read.
                continue
        if limit is not None and limit >= 0:
            return entries[-limit:]
        return entries

    # -- audit history -------------------------------------------------------

    def record_audit(self, findings: list[dict]) -> None:
        """Append a batch of audit findings to ``audit_history.jsonl``.

        Writes one JSON line containing the full batch, with a timestamp.
        """
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "findings": findings,
        }
        self.dir.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def load_audit_history(self, *, limit: int | None = None) -> list[dict]:
        """Read audit_history.jsonl, optionally bounded to the last ``limit``."""
        try:
            raw = self.audit_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        entries: list[dict] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if limit is not None and limit >= 0:
            return entries[-limit:]
        return entries

    # -- catalogue state -----------------------------------------------------

    def load_catalogue_state(self) -> dict:
        """Return the parsed ``catalogue_state.json`` (empty dict if missing)."""
        try:
            raw = self.catalogue_state_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def save_catalogue_state(self, state: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.catalogue_state_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # -- prompt injection ----------------------------------------------------

    def inject_into_prompt(self) -> str:
        """Return the context block passed to ``system_prompt_base``.

        Contains the full ``profile.md`` (if present) followed by a short
        bullet list of the most recent decisions, bounded by
        :data:`DECISION_INJECT_LIMIT` so prompt size stays flat regardless
        of log growth. Returns an empty string if the tenant has no
        memory yet.
        """
        profile = self.profile.strip()
        recent = self.load_decisions(limit=DECISION_INJECT_LIMIT)

        if not profile and not recent:
            return ""

        parts: list[str] = []
        if profile:
            parts.append(profile)
        if recent:
            lines = ["### Recent decisions"]
            for entry in recent:
                ts = entry.get("timestamp", "")
                date = ts.split("T", 1)[0] if ts else ""
                text = (
                    entry.get("text")
                    or entry.get("message")
                    or json.dumps(
                        {k: v for k, v in entry.items() if k != "timestamp"},
                        ensure_ascii=False,
                    )
                )
                prefix = f"- {date} " if date else "- "
                lines.append(f"{prefix}{text}")
            parts.append("\n".join(lines))

        return "\n\n".join(parts)
