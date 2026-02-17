.PHONY: dep
dep:
	uv sync

.PHONY: format-and-lint
format-and-lint:
	uv run --no-sync --project . ruff check --select I --fix
	uv run --no-sync --project . ruff format
	uv run --no-sync --project . ruff check --fix

.PHONY: check-api-key
check-api-key:
	uv run --no-sync --project . python -m alduin.llm
