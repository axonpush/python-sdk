.PHONY: help install lint typecheck test test-unit test-e2e e2e-db-setup e2e-db-reset release-check

# easy-push checkout location (override with EASYPUSH_DIR=...)
EASYPUSH_DIR ?= ../easy-push
EASYPUSH_ENV := $(EASYPUSH_DIR)/.env

# Auto-read DB credentials from easy-push/.env via a tiny python helper.
# Cross-platform (no PGPASSWORD=value shell prefix, which doesn't work in
# Windows cmd.exe — and that's the shell make uses by default on Windows).
# If easy-push/.env doesn't exist or python isn't on PATH, we fall back to
# common defaults; the user can still override any of these by passing them
# on the make command line, e.g. `make e2e-db-setup PGPASSWORD=mypass`.
read_env = $(shell python tests/_read_env.py $(1) $(EASYPUSH_ENV))

PGHOST     ?= $(or $(call read_env,DB_HOST),localhost)
PGPORT     ?= $(or $(call read_env,DB_PORT),5432)
PGUSER     ?= $(or $(call read_env,DB_USERNAME),postgres)
PGPASSWORD ?= $(or $(call read_env,DB_PASSWORD),postgres)
TEST_DB    ?= axonpush_test

# Locate psql.exe — prefers PATH, falls back to the standard Windows install
# location (C:\Program Files\PostgreSQL\<version>\bin\). Override with PSQL=...
PSQL ?= $(shell python tests/_read_env.py --find-psql)

# psql connection URI — embeds credentials so we don't need PGPASSWORD env var.
PG_DEFAULT_URI = postgresql://$(PGUSER):$(PGPASSWORD)@$(PGHOST):$(PGPORT)/postgres

help:
	@echo "axonpush-python — common dev targets"
	@echo
	@echo "  make install         Install dev + all extras"
	@echo "  make lint            Run ruff (the release gate)"
	@echo "  make typecheck       Run mypy (advisory; not yet a release gate)"
	@echo "  make test-unit       Fast unit tests with respx mocks (no backend)"
	@echo "  make test-e2e        Full e2e: applies migrations, starts easy-push, runs tests, cleans up"
	@echo "  make e2e-db-setup    Create $(TEST_DB) DB and run easy-push migrations (idempotent)"
	@echo "  make e2e-db-reset    Drop and recreate $(TEST_DB) from scratch"
	@echo "  make release-check   Lint + unit tests — same as the release gate"
	@echo
	@echo "E2E quickstart:"
	@echo "  make test-e2e        # one command — handles everything"
	@echo
	@echo "Env knobs (set in your shell or pass as 'make VAR=value'):"
	@echo "  AXONPUSH_SKIP_SERVER=1   pytest won't start easy-push (use your own running instance)"
	@echo "  AXONPUSH_KEEP_SERVER=1   pytest leaves easy-push running on teardown (debugging)"
	@echo "  AXONPUSH_BASE_URL=...    point pytest at a different easy-push URL"
	@echo
	@echo "DB credentials are auto-read from $(EASYPUSH_ENV) (PGUSER=$(PGUSER) PGHOST=$(PGHOST))."
	@echo "Override with: make e2e-db-setup PGPASSWORD=mypass PGUSER=myuser"

install:
	uv sync --extra dev --extra all

lint:
	uv run ruff check .

typecheck:
	uv run mypy src/axonpush

test: test-unit

test-unit:
	uv run pytest tests/unit -v

# `test-e2e` depends on `e2e-db-setup` so migrations are always up to date
# before tests run. The pytest conftest then auto-starts easy-push (and
# auto-stops it on teardown). One command, full pipeline.
test-e2e: export AXONPUSH_EASYPUSH_DIR = $(EASYPUSH_DIR)
test-e2e: export AXONPUSH_TEST_DB = $(TEST_DB)
test-e2e: e2e-db-setup
	uv run pytest tests/e2e -v -m e2e

# `target: export VAR = value` is GNU make's portable way of putting an env var
# into the recipe's process environment. cmd.exe and bash both inherit it, so
# `bun run migration:run` picks up DB_DATABASE without any shell-specific syntax.
e2e-db-setup: export DB_DATABASE = $(TEST_DB)
e2e-db-setup:
	@echo "[+] Creating $(TEST_DB) (any 'already exists' error is harmless)..."
	-"$(PSQL)" "$(PG_DEFAULT_URI)" -c "CREATE DATABASE $(TEST_DB)"
	@echo "[+] Running easy-push migrations against $(TEST_DB)..."
	cd $(EASYPUSH_DIR) && bun run migration:run

e2e-db-reset:
	"$(PSQL)" "$(PG_DEFAULT_URI)" -c "DROP DATABASE IF EXISTS $(TEST_DB)"
	$(MAKE) e2e-db-setup

release-check: lint test-unit
	@echo "[+] Release gate would pass."
