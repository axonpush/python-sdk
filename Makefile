.PHONY: help install lint format typecheck test test-unit test-realtime test-e2e codegen release-check

EASYPUSH_DIR ?= ../easy-push
SPEC_URL     ?= http://localhost:3000/swagger/json
SPEC_FILE    := spec/openapi.json
GEN_OUT      := src/axonpush/_internal/api

help:
	@echo "axonpush-python — common dev targets"
	@echo
	@echo "  make install         uv sync (dev + all extras)"
	@echo "  make codegen         dump backend OpenAPI spec, regenerate $(GEN_OUT)"
	@echo "  make lint            ruff check + format check"
	@echo "  make format          ruff format --write + ruff check --fix"
	@echo "  make typecheck       mypy --strict src/"
	@echo "  make test-unit       fast unit tests"
	@echo "  make test-realtime   realtime/MQTT unit tests (mocked broker)"
	@echo "  make test-e2e        e2e tests against $(SPEC_URL) (boot backend yourself)"
	@echo "  make release-check   lint + typecheck + test-unit"
	@echo
	@echo "Codegen requires the backend to be running on $(SPEC_URL)."
	@echo "Start it with: cd $(EASYPUSH_DIR) && bun run start:dev"

install:
	uv sync --extra dev --extra all

codegen:
	@echo "[+] Fetching OpenAPI spec from $(SPEC_URL)..."
	@mkdir -p spec tools
	@curl -fsS $(SPEC_URL) > $(SPEC_FILE) || (echo "ERR: backend not reachable at $(SPEC_URL)" && exit 1)
	@uv run python tools/patch-spec.py $(SPEC_FILE)
	@echo "[+] Generating client into $(GEN_OUT)..."
	@rm -rf _internal_api
	uv run openapi-python-client generate --path $(SPEC_FILE) --config tools/openapi-config.yaml --overwrite --meta none
	@rm -rf $(GEN_OUT)
	@mkdir -p src/axonpush/_internal
	@touch src/axonpush/_internal/__init__.py
	@mv _internal_api $(GEN_OUT)
	@echo "[+] Codegen complete. Run 'git diff' to review changes."

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check . --fix

typecheck:
	uv run mypy --strict src/

test: test-unit

test-unit:
	uv run pytest tests/unit -v

test-realtime:
	uv run pytest tests/realtime -v

test-e2e:
	uv run pytest tests/e2e -v -m e2e

release-check: lint typecheck test-unit
	@echo "[+] Release gate would pass."
