PYTHON_DIRS := scripts tests skills/github-publish-changes/scripts skills/verify-repository/scripts
YAML_PATHS := .yamllint.yaml .github/dependabot.yml .github/workflows skills/*/agents/openai.yaml tests/fixtures/*.yaml

.PHONY: check basic-commit-check format format-check lint typecheck yaml-check skills-check behavior-check test secrets secrets-baseline diff-check staged-diff-check

check: format-check lint typecheck yaml-check skills-check behavior-check test secrets diff-check

basic-commit-check: secrets staged-diff-check

format:
	uv run --locked ruff format $(PYTHON_DIRS)
	uv run --locked ruff check --fix $(PYTHON_DIRS)

format-check:
	uv run --locked ruff format --check $(PYTHON_DIRS)

lint:
	uv run --locked ruff check $(PYTHON_DIRS)

typecheck:
	uv run --locked mypy

yaml-check:
	uv run --locked yamllint $(YAML_PATHS)

skills-check:
	uv run --locked python scripts/check_skills.py --root .

behavior-check:
	uv run --locked python scripts/check_skill_behavior.py --root .

test:
	uv run --locked pytest --cov --cov-report=term-missing

secrets:
	uv run --locked python scripts/check_secrets.py --root .  # pragma: allowlist secret

secrets-baseline:
	uv run --locked detect-secrets scan --baseline .secrets.baseline  # pragma: allowlist secret

diff-check:
	git diff --check

staged-diff-check:
	git diff --cached --check
