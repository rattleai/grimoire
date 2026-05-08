# Publishing Grimoire

Three distribution channels, three publish flows. Run them in order on every release; they are independent and any one can fail without blocking the others, but a clean release ships all three at the same version.

## Versioning

Bump these four locations in lock-step:

- `package.json` → `"version": "X.Y.Z"`
- `pyproject.toml` → `version = "X.Y.Z"`
- `.claude-plugin/plugin.json` → `"version": "X.Y.Z"`
- `.claude-plugin/marketplace.json` → `plugins[0].version = "X.Y.Z"`

Add a corresponding entry to `CHANGELOG.md`. Tag the commit `vX.Y.Z`.

## 1. npm — `@rattleai/grimoire`

Prerequisites:
- `npm` 9+ logged in as a member of the `@rattleai` org (`npm whoami`).
- The `@rattleai` scope must exist on npmjs.com; `npm org create rattleai` once if missing.

Smoke-test, dry-run, then publish:

```bash
# 1. Make sure the bundle is consistent
node bin/grimoire.mjs install --target /tmp --layout flat --dry-run

# 2. See exactly what npm would ship (uses the `files` array)
npm pack --dry-run

# 3. Publish (publishConfig.access=public is set in package.json)
npm publish

# 4. Verify
npm view @rattleai/grimoire
npx --yes @rattleai/grimoire install --dry-run
```

Hot-fix release: bump patch, re-run. To deprecate a bad version: `npm deprecate @rattleai/grimoire@X.Y.Z "<reason>"`.

## 2. PyPI — `grimoire`

If `grimoire` is taken on PyPI, fall back to `grimoire-rattle` and update `pyproject.toml`'s `name` field.

```bash
# 1. Clean previous builds
rm -rf dist/ build/ grimoire.egg-info/

# 2. Build sdist + wheel
python -m pip install --upgrade build twine
python -m build

# 3. Smoke-test the built artefact in a fresh venv
python -m venv /tmp/grimoire-test && source /tmp/grimoire-test/bin/activate
pip install dist/grimoire-X.Y.Z-py3-none-any.whl
rattle --help                # the CLI entry point still works
deactivate

# 4. Upload (TestPyPI first if uncertain)
twine upload --repository testpypi dist/*
twine upload dist/*

# 5. Verify
pip install --upgrade grimoire
```

The `rattle` console script remains the CLI entry point — `grimoire` is the **distribution name** on PyPI, not a renamed CLI.

## 3. Claude Code marketplace — `rattleai/grimoire`

Already public via the GitHub repo. No publish step beyond pushing to `main`. Verify the install path:

```text
/plugin marketplace add rattleai/grimoire
/plugin install grimoire
```

Inside Claude Code, after `/plugin install grimoire`:

- `/rattle-analyse`, `/rattle-suggest-config`, `/rattle-audit`, `/rattle-build-offer` should appear in the slash-command palette.
- The eight skills should auto-load when the user mentions Rattle / configurator topics.
- The three subagents (`rattle-consultant`, `rattle-auditor`, `rattle-config-builder`) should be invocable via the Agent tool.

If the marketplace add fails, double-check that `.claude-plugin/marketplace.json` is at the repo root and parses as valid JSON (`jq . .claude-plugin/marketplace.json`).

## 4. GitHub release

```bash
# Tag the commit on main
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z

# Optional: cut a GitHub release with the CHANGELOG entry as the body
gh release create vX.Y.Z --notes-file <(awk '/^## \[X.Y.Z\]/,/^## \[/{print}' CHANGELOG.md | head -n -1)
```

## Pre-release checklist

Before any of the three publish steps:

- [ ] `make clean-publish` (removes caches, egg-info, orphan dirs, and macOS metadata).
- [ ] `make check` (Python lint + type-check + 262 tests) is green.
- [ ] `node bin/grimoire.mjs install --dry-run` enumerates all expected artifacts.
- [ ] `python skills/rattle-apply-config/scripts/validate_recommendation.py examples/recommendation.json` returns `valid: true`.
- [ ] `python skills/rattle-pricelist-analysis/scripts/detect_anti_patterns.py examples/pricelist-input.json` matches `examples/pricelist-anti-patterns.json`.
- [ ] All four version locations match.
- [ ] CHANGELOG has the new entry above `## [Unreleased]`.

## Post-publish smoke test

After all three channels are live:

```bash
# npm path
npx --yes @rattleai/grimoire install --target /tmp/smoke-npm --dry-run

# PyPI path (in a fresh venv)
python -m venv /tmp/smoke-pypi && source /tmp/smoke-pypi/bin/activate
pip install grimoire
rattle --help
deactivate

# Claude Code path — open Claude Code, run:
#   /plugin marketplace add rattleai/grimoire
#   /plugin install grimoire
#   /rattle-analyse
```

If any of the three fails, deprecate the version and ship a patch — never paper over with a force-push.
