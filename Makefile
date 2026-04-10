.PHONY: help install lint test test-unit test-e2e release-check clean

help:
	@echo "axonpush-python — common dev targets"
	@echo
	@echo "  make install      Install dev + all extras"
	@echo "  make lint         Run ruff (the release gate)"
	@echo "  make typecheck    Run mypy (advisory; not yet a release gate)"
	@echo "  make test-unit    Fast unit tests with respx mocks (no backend)"
	@echo "  make test-e2e     Full e2e against a live easy-push backend"
	@echo "  make release-check  Lint + unit tests — same as the release gate"

install:
	uv sync --extra dev --extra all

lint:
	uv run ruff check .

typecheck:
	uv run mypy src/axonpush

test: test-unit

test-unit:
	uv run pytest tests/unit -v

test-e2e:
	./scripts/test-e2e.sh

release-check: lint test-unit
	@echo "[+] Release gate would pass."
