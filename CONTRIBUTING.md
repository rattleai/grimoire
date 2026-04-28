# Contributing to Rattle AI Workspace

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/rattle_api.git
   cd rattle_api
   ```
3. **Create a branch** for your change:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Install** development dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev,all-ai]"
   ```

## Development Workflow

### Running checks

```bash
make lint     # Ruff linter
make test     # pytest
make check    # All checks
```

### Code style

- We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.
- Line length: 100 characters.
- Target Python version: 3.10+.
- Configuration lives in `pyproject.toml` under `[tool.ruff]`.

### Commit messages

Write clear, concise commit messages:

- Use the imperative mood: "Add feature" not "Added feature".
- Keep the first line under 72 characters.
- Reference issues where relevant: `Fix #42`.

### Pull requests

1. Ensure all checks pass (`make check`).
2. Update documentation if your change affects user-facing behaviour.
3. Add a changelog entry under `[Unreleased]` in `CHANGELOG.md`.
4. Keep pull requests focused — one feature or fix per PR.
5. Fill out the pull request template.

## Adding a New AI Provider

1. Create a new class in `rattle_api/provider.py` that extends `AIProvider`.
2. Implement the `complete()` method.
3. Register it in the `PROVIDERS` dict.
4. Document required environment variables in `rattle_api/config.py` and `.env.example`.
5. Add the provider to the table in `README.md`.

## Reporting Issues

- Use the [GitHub issue tracker](https://github.com/rattleai/grimoire/issues).
- Check existing issues before creating a new one.
- Include steps to reproduce, expected behaviour, and actual behaviour.
- For security vulnerabilities, see [SECURITY.md](SECURITY.md).

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.
