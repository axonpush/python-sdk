"""E2E fixtures: live easy-push backend, bootstrapped per session via SQL+HTTP.

Expected workflow::

    # one time
    make e2e-db-setup

    # then just:
    make test-e2e

The session-scoped fixture below will:

1. Detect whether easy-push is already running on AXONPUSH_BASE_URL.
2. If not, spawn ``bun run start`` from ``$AXONPUSH_EASYPUSH_DIR`` (default
   ``../easy-push``) with ``DB_DATABASE=axonpush_test`` set in its environment,
   wait for it to respond, and **kill it again on session teardown**.
3. **SQL-insert** a fresh user / org / membership / API key directly into the
   test database (bypassing /auth/signup — see the comment in ``_bootstrap``
   for *why*), then use the API key over HTTP to create the test app and
   channel via the normal endpoints.

Override knobs (env vars):

* ``AXONPUSH_BASE_URL`` — where to look for easy-push. Default
  ``http://localhost:3000``.
* ``AXONPUSH_EASYPUSH_DIR`` — where to spawn easy-push from. Default
  ``../easy-push``.
* ``AXONPUSH_TEST_DB`` — Postgres database name. Default ``axonpush_test``.
* ``AXONPUSH_SKIP_SERVER=1`` — never spawn the server. Use this when you
  already have one running and want pytest to just connect.
* ``AXONPUSH_KEEP_SERVER=1`` — don't kill the server on teardown. Useful
  for debugging the backend after a test failure.
"""
from __future__ import annotations

import hashlib
import os
import secrets
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

import httpx
import pytest

from axonpush import AsyncAxonPush, AxonPush
from tests._read_env import find_psql, read_env_key

TEST_BASE_URL = os.getenv("AXONPUSH_BASE_URL", "http://localhost:3000")
EASYPUSH_DIR = Path(os.getenv("AXONPUSH_EASYPUSH_DIR", "../easy-push")).resolve()
TEST_DB = os.getenv("AXONPUSH_TEST_DB", "axonpush_test")
EASYPUSH_ENV = EASYPUSH_DIR / ".env"


@dataclass
class _BackendCreds:
    base_url: str
    api_key: str
    tenant_id: str
    app_id: int
    channel_id: int


def _ping_backend(base_url: str) -> bool:
    """Return True if the backend is currently responding."""
    try:
        r = httpx.get(base_url, timeout=2.0)
        return r.status_code < 500
    except httpx.HTTPError:
        return False


def _wait_for_backend(
    base_url: str,
    timeout: float = 60.0,
    server_proc: Optional[subprocess.Popen] = None,
) -> None:
    """Poll the root endpoint until the backend responds (or give up).

    If ``server_proc`` is supplied, also fail fast if the subprocess dies
    during startup — no point waiting 60s for a server that already crashed.
    """
    deadline = time.monotonic() + timeout
    last_exc: Exception | None = None
    while time.monotonic() < deadline:
        if server_proc is not None and server_proc.poll() is not None:
            raise RuntimeError(
                f"easy-push subprocess exited with code {server_proc.returncode} "
                f"before becoming ready"
            )
        try:
            r = httpx.get(base_url, timeout=2.0)
            if r.status_code < 500:
                return
        except httpx.HTTPError as exc:
            last_exc = exc
        time.sleep(1.0)
    raise TimeoutError(
        f"easy-push did not respond at {base_url} within {timeout:.0f}s "
        f"(last error: {last_exc})"
    )


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Kill a subprocess and all its children, cross-platform.

    NestJS spawns child workers, so a plain ``proc.terminate()`` would leave
    them orphaned. On Windows we use ``taskkill /F /T`` (kills tree by PID).
    On POSIX we kill the process group, which requires the process to have
    been spawned with ``start_new_session=True``.
    """
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


@pytest.fixture(scope="session")
def _easy_push_server() -> Iterator[None]:
    """Ensure an easy-push server is reachable for the test session.

    * If one's already running on AXONPUSH_BASE_URL → use it as-is.
    * If AXONPUSH_SKIP_SERVER=1 → don't spawn one (assume the user knows what
      they're doing — fail later if it isn't actually there).
    * Otherwise → spawn ``bun run start`` from $AXONPUSH_EASYPUSH_DIR with
      DB_DATABASE=$AXONPUSH_TEST_DB, wait for it to respond, and kill it on
      teardown (unless AXONPUSH_KEEP_SERVER=1).
    """
    if os.getenv("AXONPUSH_SKIP_SERVER") == "1":
        yield
        return

    if _ping_backend(TEST_BASE_URL):
        # Someone's already running easy-push (e.g., a long-running dev session
        # in another terminal). Use it. Don't kill it on teardown — we didn't
        # start it.
        print(f"\n[e2e] using already-running easy-push at {TEST_BASE_URL}")
        yield
        return

    if not EASYPUSH_DIR.exists():
        pytest.exit(
            f"easy-push directory not found at {EASYPUSH_DIR}.\n"
            f"Override with: AXONPUSH_EASYPUSH_DIR=/path/to/easy-push pytest -m e2e",
            returncode=2,
        )

    log_path = Path(tempfile.gettempdir()) / "axonpush-pytest-easypush.log"
    log_handle = open(log_path, "w", encoding="utf-8")

    env = os.environ.copy()
    env["DB_DATABASE"] = TEST_DB
    # Make sure the spawned server points at the test DB regardless of what
    # the user has in their shell environment.

    print(f"\n[e2e] starting easy-push from {EASYPUSH_DIR} (DB={TEST_DB})...")
    print(f"[e2e] server log: {log_path}")

    popen_kwargs: dict = {
        "cwd": str(EASYPUSH_DIR),
        "env": env,
        "stdout": log_handle,
        "stderr": subprocess.STDOUT,
    }
    if sys.platform == "win32":
        # Detach from console so Ctrl-C in pytest doesn't also hit the server
        # before we get a chance to clean up via taskkill.
        popen_kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        )
    else:
        # Put the server in its own process group so we can killpg() the whole
        # tree (NestJS spawns workers).
        popen_kwargs["start_new_session"] = True

    proc = subprocess.Popen(["bun", "run", "start"], **popen_kwargs)

    try:
        _wait_for_backend(TEST_BASE_URL, timeout=60.0, server_proc=proc)
        print(f"[e2e] easy-push is ready at {TEST_BASE_URL}")
    except (TimeoutError, RuntimeError) as exc:
        log_handle.close()
        try:
            log_tail = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
        except OSError:
            log_tail = "<could not read log file>"
        _kill_process_tree(proc)
        pytest.exit(
            f"\n[e2e] {exc}\n\n"
            f"[e2e] server log tail (last 4KB of {log_path}):\n"
            f"{'-' * 60}\n{log_tail}\n{'-' * 60}\n",
            returncode=2,
        )

    try:
        yield
    finally:
        if os.getenv("AXONPUSH_KEEP_SERVER") == "1":
            print(
                f"\n[e2e] AXONPUSH_KEEP_SERVER=1 — leaving easy-push running "
                f"at {TEST_BASE_URL} (PID {proc.pid}, log {log_path})"
            )
            return
        print(f"\n[e2e] stopping easy-push (PID {proc.pid})...")
        _kill_process_tree(proc)
        log_handle.close()


def _pg_uri_for_test_db() -> str:
    """Build a libpq connection URI for the easy-push test DB.

    Reads DB_HOST/PORT/USERNAME/PASSWORD from easy-push/.env (so we use the
    same Postgres instance the user already has configured) and uses
    AXONPUSH_TEST_DB for the database name (so we never touch the user's
    main DB).
    """
    host = read_env_key("DB_HOST", str(EASYPUSH_ENV)) or "localhost"
    port = read_env_key("DB_PORT", str(EASYPUSH_ENV)) or "5432"
    user = read_env_key("DB_USERNAME", str(EASYPUSH_ENV)) or "postgres"
    password = read_env_key("DB_PASSWORD", str(EASYPUSH_ENV)) or "postgres"
    return f"postgresql://{user}:{password}@{host}:{port}/{TEST_DB}"


def _run_psql(sql: str) -> str:
    """Pipe ``sql`` to psql against the test DB and return its stdout.

    Uses ``-tA`` (tuples-only, unaligned) so the output is easy to parse.
    Raises if psql exits non-zero.
    """
    psql = find_psql()
    result = subprocess.run(
        [psql, _pg_uri_for_test_db(), "-tA", "-v", "ON_ERROR_STOP=1", "-f", "-"],
        input=sql,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"psql failed (exit {result.returncode}):\n"
            f"STDERR: {result.stderr}\nSTDOUT: {result.stdout}"
        )
    return result.stdout.strip()


def _bootstrap(base_url: str) -> _BackendCreds:
    """SQL-insert user/org/membership/api-key, then use the API key to
    create the test app and channel via HTTP.

    **Why we don't call /auth/signup**

    There's an upstream bug in easy-push at
    ``src/auth/auth.controller.ts:120`` — the signup transaction creates the
    user via the transactional ``manager`` but then calls
    ``userOrgService.addMembership(createdUser.id, organizationId, role)``
    *without* the manager. ``addMembership`` uses the regular injected
    repository (``this.repo``), which runs on a separate connection from the
    pool — so it can't see the freshly-INSERTed user (still uncommitted in
    the open transaction). The FK on ``user_organization."userId"`` then
    fails with ``FK_29c3c8cc3ea9db22e4a347f4b5a violated``, the transaction
    rolls back, and signup returns 500.

    The fix upstream is one line: pass ``manager`` through to
    ``addMembership`` (and have the service use it instead of ``this.repo``).
    Until that lands, we bypass /auth/signup by inserting the rows directly.

    The bypass uses only the columns the entities require (see ``\\d user``
    etc. — password is nullable so we don't need bcrypt). API key auth then
    works for everything else because both POST /apps and POST /channel are
    accepting any auth method via ``auth.middleware.ts:36-44``.
    """
    suffix = uuid.uuid4().hex[:8]
    username = f"pytest-{suffix}"
    email = f"pytest-{suffix}@example.invalid"

    # API key: same scheme as easy-push's ApiKeyService.createApiKey:
    # `ak_` + 64 random hex chars; stored hashed via SHA-256 (no salt).
    raw_key = f"ak_{secrets.token_hex(32)}"
    prefix = raw_key[:11]  # "ak_" + 8 hex chars
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()

    # One SQL block — CTEs chain the inserts so we can pass IDs through
    # without round-tripping. Returns "user_id|org_id" for sanity-checking.
    # Dollar-quoted ($$...$$) string literals so we don't need to escape
    # the values (which are all UUIDs / hex / known-safe).
    sql = f"""
WITH new_org AS (
  INSERT INTO organization (slug, name, description)
  VALUES ($${'pytest-org-' + suffix}$$, $${'pytest-org-' + suffix}$$, $$ephemeral pytest org$$)
  RETURNING id
),
new_user AS (
  INSERT INTO "user" (username, email, roles, "organizationId", first_name, last_name)
  SELECT $${username}$$, $${email}$$, $$user,admin$$, id, $$Pytest$$, $$Runner$$ FROM new_org
  RETURNING id, "organizationId"
),
new_membership AS (
  INSERT INTO user_organization ("userId", "organizationId", role)
  SELECT id, "organizationId", $$admin$$ FROM new_user
  RETURNING id
),
new_apikey AS (
  INSERT INTO api_key (name, prefix, "hashedKey", "organizationId", "createdById", scopes)
  SELECT
    $${'pytest-key-' + suffix}$$,
    $${prefix}$$,
    $${hashed_key}$$,
    u."organizationId",
    u.id,
    $$publish,subscribe$$
  FROM new_user u
  RETURNING id
)
SELECT u.id || '|' || u."organizationId" FROM new_user u, new_membership, new_apikey;
"""
    output = _run_psql(sql)
    user_id_str, org_id = output.split("|", 1)
    int(user_id_str)  # sanity check it parsed

    # Now use the API key over HTTP to create the test app and channel.
    auth = {"X-API-Key": raw_key, "x-tenant-id": org_id}
    with httpx.Client(base_url=base_url, timeout=10.0) as http:
        r = http.post("/apps", json={"name": f"pytest-app-{suffix}"}, headers=auth)
        r.raise_for_status()
        app_id = int(r.json()["id"])

        r = http.post(
            "/channel",
            json={"name": f"pytest-ch-{suffix}", "appId": app_id},
            headers=auth,
        )
        r.raise_for_status()
        channel_id = int(r.json()["id"])

    return _BackendCreds(
        base_url=base_url,
        api_key=raw_key,
        tenant_id=org_id,
        app_id=app_id,
        channel_id=channel_id,
    )


@pytest.fixture(scope="session")
def backend(_easy_push_server) -> _BackendCreds:
    """Bootstrap a fresh org/app/channel/api-key for the session.

    Depends on ``_easy_push_server`` so the server is guaranteed to be up
    by the time we try to sign up. Session-scoped — bootstrap runs once
    per pytest invocation and all tests share the credentials.
    """
    return _bootstrap(TEST_BASE_URL)


# Override the per-test client/async_client fixtures from tests/conftest.py
# so e2e tests use the bootstrapped credentials, not the env-var defaults.
# pytest uses the closest fixture in the directory tree, so these win for
# anything under tests/e2e/.
@pytest.fixture()
def client(backend):
    c = AxonPush(
        api_key=backend.api_key,
        tenant_id=backend.tenant_id,
        base_url=backend.base_url,
    )
    yield c
    c.close()


@pytest.fixture()
async def async_client(backend):
    c = AsyncAxonPush(
        api_key=backend.api_key,
        tenant_id=backend.tenant_id,
        base_url=backend.base_url,
    )
    yield c
    await c.close()


@pytest.fixture()
def app(client, backend):
    return client.apps.get(backend.app_id)


@pytest.fixture()
def channel(client, backend):
    """A fresh per-test channel inside the bootstrapped app — keeps publish/SSE
    tests from interfering with each other."""
    name = f"test-ch-{uuid.uuid4().hex[:8]}"
    created = client.channels.create(name, backend.app_id)
    yield created
    try:
        client.channels.delete(created.id)
    except Exception:
        pass
