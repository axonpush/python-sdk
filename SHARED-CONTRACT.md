# SDK v0.0.10 — Shared Contract

**Read this before editing any file in `src/axonpush/`.** This document is the
single source of truth shared between the parallel work streams. If something
seems out of date, fix the contract first and surface the change to the
orchestrator before editing code.

---

## 1. Branch & version

- Working branch: `feat/sdk-v0.0.10-rewrite`.
- `pyproject.toml` and `src/axonpush/_version.py` both read `0.0.10`.
- Latest released versions are GitHub `v0.0.9` and PyPI `0.0.9`. We are
  shipping `0.0.10` next.

## 2. Generated layer (do not edit)

The OpenAPI-generated client lives at:

```
src/axonpush/_internal/api/
├── client.py                # Client + AuthenticatedClient
├── errors.py                # UnexpectedStatus
├── types.py                 # UNSET sentinel + Response
├── api/                     # one package per controller tag
│   ├── event/event_controller_create_event.py    # .sync / .asyncio / *_detailed
│   ├── event/event_controller_list_events.py
│   ├── auth/...
│   ├── apps/...
│   ├── channels/...
│   ├── environments/...
│   ├── webhooks/...
│   ├── traces/...
│   ├── api_keys/...
│   ├── organizations/...
│   ├── users/...
│   ├── feature_flags/...
│   ├── health/...
│   ├── public_tokens/...
│   ├── releases/...
│   ├── otlp/...
│   ├── sentry/...
│   ├── sso/...
│   ├── audit_logs/...
│   └── default/...
└── models/                  # 87 generated pydantic v2 models
```

Regeneration: `make codegen` (boots backend on `:3000`, dumps spec, runs
`openapi-python-client`, moves output back). Don't edit anything inside
`_internal/api/` by hand — the next codegen will overwrite.

## 3. Public surface

### `axonpush.client`

```python
class AxonPush:
    """Sync client. Kwargs-only ctor. Context-manager friendly."""
    def __init__(self, *, api_key=None, tenant_id=None, base_url=None,
                 environment=None, timeout=30.0, max_retries=3, fail_open=False): ...
    def __enter__(self) -> "AxonPush": ...
    def __exit__(self, *exc) -> None: ...
    @property
    def events(self) -> "Events": ...
    @property
    def channels(self) -> "Channels": ...
    @property
    def apps(self) -> "Apps": ...
    @property
    def environments(self) -> "Environments": ...
    @property
    def webhooks(self) -> "Webhooks": ...
    @property
    def traces(self) -> "Traces": ...
    @property
    def api_keys(self) -> "ApiKeys": ...
    @property
    def organizations(self) -> "Organizations": ...
    def connect_realtime(self, **kwargs) -> "RealtimeClient": ...
    def close(self) -> None: ...

class AsyncAxonPush:
    """Async mirror. Same surface; resource accessors return Async* classes;
    connect_realtime returns AsyncRealtimeClient; awaitable close()."""
```

### Resource accessor names (FROZEN — Stream B owns these)

`events`, `channels`, `apps`, `environments`, `webhooks`, `traces`,
`api_keys`, `organizations`. Method names per resource: `list`, `get`,
`create`, `update`, `delete` — plus the domain-specific verbs already
present (`events.publish`, `events.search`, `traces.list`, `traces.get`,
`traces.events`, `traces.summary`, `traces.stats`, `webhooks.deliveries`).

### Exceptions (FROZEN — Stream A owns these)

```
AxonPushError                     # base
├── APIConnectionError            # network / DNS / read timeout
├── AuthenticationError           # 401
├── ForbiddenError                # 403
├── NotFoundError                 # 404
├── ValidationError               # 4xx with code 'validation_error' / 422
├── RateLimitError                # 429 (carries retry_after)
├── ServerError                   # 5xx
└── RetryableError                # mixin — APIConnectionError, RateLimitError, ServerError inherit
```

Each exception carries `request_id: str | None`, `status_code: int | None`,
`code: str | None`, `hint: str | None` (from the global filter the backend
wires up).

### `axonpush.models` (PUBLIC re-exports — Stream B owns this)

This module is the **only** path users should use to access models. Internal
generated names are not exposed.

```python
from axonpush._internal.api.models import (
    AppResponseDto as App,
    ChannelResponseDto as Channel,
    CreateEventDto,
    EventResponseDto as Event,
    CreateEventDtoEventType as EventType,
    EnvironmentResponseDto as Environment,
    WebhookEndpointResponseDto as WebhookEndpoint,
    WebhookDeliveryResponseDto as WebhookDelivery,
    DeliveryStatus,
    TraceListItemDto as TraceListItem,
    TraceSummaryResponseDto as TraceSummary,
    UserResponseDto as User,
    ApiKeyResponseDto as ApiKey,
    OrganizationResponseDto as Organization,
)
```

If a name doesn't exist in the generated layer, check
`src/axonpush/_internal/api/models/` for the actual filename and report
back to the orchestrator before improvising.

### `axonpush.exceptions`, `axonpush.tracing`, `axonpush._config`

These are owned by Stream A. Stream B/C/D import from them; do not redefine.

## 4. ID type rule (FROZEN)

**All IDs are `str` UUIDs on the public boundary**, including:
`org_id`, `app_id`, `channel_id`, `environment_id`, `event_id`, `trace_id`,
`endpoint_id`, `user_id`, `api_key_id`, `release_id`, `agent_id`,
`span_id`, `parent_event_id`.

Integrations (`src/axonpush/integrations/`) accept `int | str` for
`channel_id` only as a softening for v0.0.9 callers; route every
user-supplied ID through `_utils.coerce_channel_id(value)` which emits
`DeprecationWarning` on int. Internally everything is `str`.

## 5. Cross-cutting concerns (Stream A owns the chokepoint)

- **HTTP retries**: `RetryableError` subclasses are retried up to
  `max_retries` with exponential backoff (250ms, 500ms, 1s, 2s, …).
  `RateLimitError` honours `Retry-After`.
- **Auth headers**: `_internal/transport.py` mounts an httpx event hook
  that sets `X-API-Key`, `x-tenant-id`, `X-Axonpush-Environment`. The
  generated `AuthenticatedClient` is configured to use this transport;
  resources never set headers directly.
- **Tracing headers**: when a `TraceContext` is current, `X-Axonpush-Trace-Id`
  is injected by the same event hook.
- **Fail-open**: when `fail_open=True` is set on the facade, `_invoke`
  swallows `APIConnectionError` and returns `None`. Resources MUST go
  through `client._invoke(...)` so this behavior is uniform.
- **Request IDs**: every response carries `X-Request-Id`. `_invoke` extracts
  it onto exceptions and attaches it to a returned model when possible.

## 6. File ownership matrix

| File / dir | Owned by |
|---|---|
| `src/axonpush/__init__.py` | **Orchestrator** — agents write `_exports_<stream>.txt` |
| `src/axonpush/resources/__init__.py` | **Orchestrator** |
| `src/axonpush/client.py`, `_config.py`, `exceptions.py`, `_tracing.py`, `_version.py`, `_internal/transport.py` | Stream A |
| `src/axonpush/resources/*.py`, `models.py` | Stream B |
| `src/axonpush/realtime/*.py` | Stream C |
| `src/axonpush/integrations/*.py` | Stream D |
| `examples/`, `README.md`, `CHANGELOG.md` | Stream E (after A–D land) |
| `src/axonpush/_internal/api/**` | **Generator only** — never edit by hand |
| `src/axonpush/_http.py` | DELETE (Stream A) — replaced by `_internal/transport.py` |
| `src/axonpush/_auth.py` | DELETE (Stream A) — folded into `_config.py` and transport |
| `src/axonpush/models/` (the directory) | DELETE (Stream B) — replaced by `models.py` re-exports |
| `src/axonpush/resources/events_query.py` | DELETE (Stream B) — folds into `resources/events.py` and `traces.py` |

## 7. `_exports_<stream>.txt` protocol

Each stream that wants to add a public top-level re-export writes lines to a
file at the repo root named `_exports_<stream>.txt`, one Python import line
per row:

```
# _exports_a.txt (Stream A)
from axonpush.client import AxonPush, AsyncAxonPush
from axonpush.exceptions import AxonPushError, AuthenticationError, ...
```

The orchestrator concatenates these into `src/axonpush/__init__.py` in the
final merge pass and removes the `_exports_*.txt` files.

## 8. Quality bar

- `mypy --strict src/` clean. No `# type: ignore` without a one-line
  reason comment.
- `ruff check .` clean. `ruff format --check .` clean.
- Every public class/function/method has a docstring with `Args` /
  `Returns` / `Raises` sections (numpydoc-ish but loose). Internal helpers
  may be undocumented.
- Minimal inline comments. Prefer well-named identifiers. When a comment
  is unavoidable, it explains *why*, not *what*.
- All sync code has a tested async sibling and vice versa.

## 9. Test layout

- `tests/unit/` — fast, no network. Mock the generated functions
  (`monkeypatch axonpush._internal.api.api.<tag>.<op>.sync`).
- `tests/realtime/` — fast, no network. MQTT clients are mocked.
- `tests/e2e/` — marked `@pytest.mark.e2e`. Skipped by default.
  Requires backend on `http://localhost:3000` (`bun run start:dev` in
  `../easy-push/`). Run with `pytest -m e2e`.
- `tests/integrations/` — Stream D's tests live here.

## 10. Final-merge order (orchestrator)

1. Stream A merges first.
2. Streams B and C merge in parallel (no overlap).
3. Stream D merges after B.
4. Orchestrator concatenates `_exports_*.txt` into `__init__.py`.
5. `ruff format . && ruff check . --fix && mypy --strict src/ && pytest`.
6. Stream E launches against the merged tree.
7. Final commit + tag `v0.0.10` (push held until user confirms).
