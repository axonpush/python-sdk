#!/usr/bin/env bash
#
# test-e2e.sh — End-to-end validation for axonpush-python against a live
# easy-push backend. Run this before pushing a release tag.
#
# What it does:
#   1. Brings up Postgres + Redis + the easy-push NestJS app via docker-compose
#   2. Waits for the backend to respond on http://localhost:3000
#   3. Runs scripts/setup-dev.ts on the easy-push side to bootstrap an org,
#      app, channel, and API key (idempotent only if the DB is fresh)
#   4. Captures API key / org id / app id from the setup output
#   5. Runs `pytest -m e2e` against the freshly-provisioned backend
#
# Prerequisites:
#   - Docker and docker-compose
#   - bun (for running the easy-push setup script) — only needed for fresh setup
#   - A sibling checkout of easy-push (override path with EASYPUSH_DIR=...)
#
# Usage:
#   ./scripts/test-e2e.sh                # default: ../easy-push
#   EASYPUSH_DIR=/path/to/easy-push ./scripts/test-e2e.sh
#   PYTEST_ARGS="-k events" ./scripts/test-e2e.sh   # pass extra args to pytest

set -euo pipefail

EASYPUSH_DIR="${EASYPUSH_DIR:-../easy-push}"
BASE_URL="${AXONPUSH_BASE_URL:-http://localhost:3000}"
PYTEST_ARGS="${PYTEST_ARGS:-}"

# Resolve to absolute path so we can cd back later
EASYPUSH_DIR_ABS=$(cd "$EASYPUSH_DIR" 2>/dev/null && pwd) || {
  echo "[x] easy-push not found at: $EASYPUSH_DIR" >&2
  echo "    Set EASYPUSH_DIR to your easy-push checkout path." >&2
  exit 1
}

PYDIR=$(pwd)

echo "[+] easy-push dir: $EASYPUSH_DIR_ABS"
echo "[+] python sdk dir: $PYDIR"
echo "[+] backend base url: $BASE_URL"

# 1. Bring up the backend
cd "$EASYPUSH_DIR_ABS"
echo "[+] Bringing up easy-push via docker-compose..."
docker compose up -d

# 2. Wait for /docs (Swagger) — proves the Nest app booted, not just Postgres
echo "[+] Waiting for backend to respond at $BASE_URL ..."
TIMEOUT=120
ELAPSED=0
until curl -fsS "$BASE_URL" >/dev/null 2>&1 || curl -fsS "$BASE_URL/docs" >/dev/null 2>&1; do
  if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    echo "[x] Backend did not become ready within ${TIMEOUT}s" >&2
    docker compose logs app | tail -50 >&2
    exit 1
  fi
  sleep 2
  ELAPSED=$((ELAPSED + 2))
  printf "."
done
echo
echo "[+] Backend is up."

# 3. Bootstrap dev data (signup → org → app → channel → api key)
echo "[+] Running setup-dev.ts ..."
SETUP_OUT=$(BASE_URL="$BASE_URL" bun run scripts/setup-dev.ts 2>&1) || {
  # If signup fails because the user already exists, we can't easily recover
  # without DB reset. Tell the operator what to do.
  echo "[x] setup-dev failed. If 'admin' already exists, reset the DB:" >&2
  echo "    docker compose down -v && docker compose up -d" >&2
  echo "    then re-run this script." >&2
  echo "$SETUP_OUT" >&2
  exit 1
}
echo "$SETUP_OUT"

# 4. Extract credentials from the setup output
API_KEY=$(echo "$SETUP_OUT" | grep -oE 'ak_[a-f0-9]{64}' | head -1)
ORG_ID=$(echo "$SETUP_OUT" | grep -oE 'Org ID:[[:space:]]+[0-9]+' | grep -oE '[0-9]+$' | head -1)
APP_ID=$(echo "$SETUP_OUT" | grep -oE 'App ID:[[:space:]]+[0-9]+' | grep -oE '[0-9]+$' | head -1)

if [ -z "$API_KEY" ] || [ -z "$ORG_ID" ] || [ -z "$APP_ID" ]; then
  echo "[x] Failed to parse API_KEY / ORG_ID / APP_ID from setup output" >&2
  exit 1
fi

echo "[+] Provisioned API key: ${API_KEY:0:16}..."
echo "[+] Org ID: $ORG_ID"
echo "[+] App ID: $APP_ID"

# 5. Run e2e tests against the live backend
cd "$PYDIR"
echo "[+] Running pytest -m e2e ..."
AXONPUSH_BASE_URL="$BASE_URL" \
AXONPUSH_API_KEY="$API_KEY" \
AXONPUSH_TENANT_ID="$ORG_ID" \
AXONPUSH_APP_ID="$APP_ID" \
uv run pytest tests/e2e -m e2e -v $PYTEST_ARGS

echo "[+] e2e tests completed."
