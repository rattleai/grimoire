#!/usr/bin/env python3
"""Package each skill as an upload-ready .zip for Claude.ai web chat.

Claude.ai (Customize → Skills → Create skill → Upload a skill) takes ONE zip per
skill, and the layout is unforgiving — a wrong one is the most common failure:

    rattle-ingest.zip
    └── rattle-ingest/          <- exactly one top-level folder,
        ├── SKILL.md               and its name MUST equal frontmatter `name`
        ├── references/
        └── scripts/

`SKILL.md` at the zip root is rejected.

The frontmatter rules here are the Agent Skills open spec (agentskills.io) as
enforced by Anthropic's own validator — NOT Claude Code's rules, which are
looser. The difference bites:

  * description: the spec caps it at 1024 characters and REJECTS anything over.
    Claude Code merely truncates the listing at 1536. Three of these skills were
    over 1024 and would have failed at the upload dialog.
  * frontmatter keys: the spec allows only name, description, license,
    compatibility, metadata, allowed-tools. Claude Code's extras (when_to_use,
    model, effort, hooks, …) are rejected.

So this validates before it zips, and refuses to package a skill that would be
turned away.

    python3 scripts/package_skills.py            # -> dist/skills/*.zip
    python3 scripts/package_skills.py --check     # validate only, write nothing
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
OUT_DIR = ROOT / "dist" / "skills"

# Agent Skills open spec (agentskills.io), as enforced by Anthropic's
# skill-creator/scripts/quick_validate.py.
NAME_MAX = 64
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DESCRIPTION_MAX = 1024
RESERVED = ("anthropic", "claude")
ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

# Never ship build residue to a user's Claude account.
EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git", "evals"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_NAMES = {".DS_Store"}


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError("no YAML frontmatter")
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.startswith((" ", "\t", "#")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def validate(skill_dir: Path) -> list[str]:
    """Return a list of spec violations. Empty means it will upload."""
    problems: list[str] = []
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        return [f"{skill_dir.name}: no SKILL.md"]

    try:
        fm = parse_frontmatter(skill_md)
    except ValueError as exc:
        return [f"{skill_dir.name}: {exc}"]

    name = fm.get("name", "")
    if not name:
        problems.append(f"{skill_dir.name}: frontmatter has no `name`")
    else:
        # The zip's single top-level folder is named from the directory, and
        # Claude.ai rejects the upload if it disagrees with the frontmatter.
        if name != skill_dir.name:
            problems.append(f"{skill_dir.name}: `name` is '{name}' but the directory is not")
        if len(name) > NAME_MAX:
            problems.append(f"{name}: name is {len(name)} chars (max {NAME_MAX})")
        if not NAME_RE.match(name):
            problems.append(f"{name}: name must be lowercase-kebab-case")
        for word in RESERVED:
            if word in name.lower():
                problems.append(f"{name}: name may not contain the reserved word '{word}'")

    desc = fm.get("description", "")
    if not desc:
        problems.append(f"{skill_dir.name}: frontmatter has no `description`")
    elif len(desc) > DESCRIPTION_MAX:
        problems.append(
            f"{skill_dir.name}: description is {len(desc)} chars — the spec caps it at "
            f"{DESCRIPTION_MAX} and Claude.ai REJECTS the upload (Claude Code only truncates, "
            "so this passes there and fails here)"
        )
    if "<" in desc or ">" in desc:
        problems.append(f"{skill_dir.name}: description may not contain angle brackets")

    for key in fm:
        if key not in ALLOWED_KEYS:
            problems.append(
                f"{skill_dir.name}: frontmatter key '{key}' is not in the Agent Skills spec "
                f"(allowed: {', '.join(sorted(ALLOWED_KEYS))})"
            )

    return problems


def included_files(skill_dir: Path) -> list[Path]:
    out = []
    for p in sorted(skill_dir.rglob("*")):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.suffix in EXCLUDE_SUFFIXES or p.name in EXCLUDE_NAMES:
            continue
        out.append(p)
    return out


def package(skill_dir: Path) -> tuple[Path, int, int]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OUT_DIR / f"{skill_dir.name}.zip"
    files = included_files(skill_dir)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            # arcname relative to the skill's PARENT — this is what produces the
            # single top-level folder Claude.ai requires.
            zf.write(f, f.relative_to(skill_dir.parent))
    return zip_path, len(files), zip_path.stat().st_size


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--check", action="store_true", help="Validate only; write nothing.")
    args = ap.parse_args()

    skills = sorted(d for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").exists())
    if not skills:
        sys.exit(f"No skills found under {SKILLS_DIR}")

    all_problems: list[str] = []
    for skill in skills:
        all_problems.extend(validate(skill))

    if all_problems:
        print("Refusing to package — these would be rejected at the upload dialog:\n")
        for p in all_problems:
            print(f"  ERROR  {p}")
        print(f"\nFAILED — {len(all_problems)} problem(s) across {len(skills)} skills.")
        return 1

    if args.check:
        print(f"OK — all {len(skills)} skills satisfy the Agent Skills spec and would upload.")
        return 0

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)

    total = 0
    print(f"Packaging {len(skills)} skills for Claude.ai → {OUT_DIR.relative_to(ROOT)}/\n")
    for skill in skills:
        zip_path, n_files, size = package(skill)
        total += size
        print(f"  {zip_path.name:34s} {n_files:3d} files  {size / 1024:8.1f} KB")

    print(f"\nOK — {len(skills)} zips, {total / 1024:.1f} KB total.")
    print("\nUpload each one in Claude.ai:")
    print("  1. Settings → Capabilities → enable 'Code execution and file creation'")
    print("     (Skills do not appear at all without it — even knowledge-only skills.)")
    print("  2. Customize → Skills → + → Create skill → Upload a skill")
    print(
        "\nStart with rattle-configurator (the #1 rule) and rattle-ingest (your data → entities)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
