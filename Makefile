.PHONY: help install dev lint format type-check test test-cov validate mcp-smoke check clean clean-publish

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in editable mode
	pip install -e .

dev: ## Install with all development dependencies
	pip install -e ".[dev,all-ai]"

lint: ## Run Ruff linter and formatter check
	ruff check .
	ruff format --check .

format: ## Auto-format code with Ruff
	ruff check --fix .
	ruff format .

type-check: ## Run mypy type checker
	mypy . --ignore-missing-imports

test: ## Run tests with pytest
	pytest

test-cov: ## Run tests with coverage report
	pytest --cov --cov-report=term-missing

validate: ## Validate the shipped bundle (manifests, skills, agents, schemas, examples)
	python3 scripts/validate_bundle.py

mcp-smoke: ## Verify the Rattle MCP server speaks the protocol and stays read-only
	node scripts/mcp_smoke.mjs

check: lint type-check test validate mcp-smoke ## Run all checks (lint + type-check + test + bundle + mcp)

clean: ## Remove build artefacts and caches
	rm -rf build/ dist/ *.egg-info/
	rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/
	rm -f .coverage .coverage.*
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -not -path './.venv/*' -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -not -path './.git/*' -not -path './.venv/*' -delete 2>/dev/null || true

clean-publish: clean ## Strict cleanup before publishing — also removes orphan dirs (tools/, legacy egg-info)
	rm -rf tools/ rattle_ai_workspace.egg-info/
	@echo
	@echo "Repo is publish-ready. Verify with:"
	@echo "  git status        # working tree should be clean"
	@echo "  python -m build   # produces dist/grimoire-*.whl + .tar.gz"
	@echo "  npm pack --dry-run  # lists files that would ship to npm"
