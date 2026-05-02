# Changelog

All notable changes to the AxonPush Python SDK are documented here. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning is [SemVer](https://semver.org/spec/v2.0.0.html).

## [0.0.10] – 2026-05-02

This is the actual `0.0.10` PyPI release. The two stale entries below
(`[0.0.10] – 2026-04-25` and `[0.0.11] – 2026-05-01`) were local bumps that
never shipped to PyPI; their content was a work-in-progress of what
eventually became this entry. Both are kept here as historical trail
markers — everything described in them is included in this release plus
the breaking changes called out below.

### Breaking

- **All IDs are `str` UUIDs on the public boundary.** Previously the SDK
  accepted a mix of `int` and `Union[int, str]` for `app_id`, `channel_id`,
  `event_id`, `trace_id`, `endpoint_id`, `agent_id`, `span_id`,
  `parent_event_id`, `org_id`, `user_id`, `api_key_id`, and
  `release_id`. They are all `str` now. Integration callbacks
  (`channel_id` argument on `AxonPushCallbackHandler`,
  `AxonPushLoggingHandler`, etc.) keep an `int | str` softening alias for
  one release; passing an `int` emits a `DeprecationWarning` and is
  coerced to `str`.
- **Removed `connect_websocket` and the `WebSocketClient` alias.** Use
  `client.connect_realtime()` and `RealtimeClient` (already the
  underlying implementation since v0.1.0).
- **Models moved to a flat `axonpush.models` namespace.** Every public
  model is re-exported from `axonpush.models` over the auto-generated
  `axonpush._internal.api.models` layer:

  ```python
  from axonpush.models import (
      App, Channel, Event, EventDetails, EventType, Environment,
      WebhookEndpoint, WebhookDelivery, Organization, User, ApiKey,
      TraceListItem, TraceSummary, TraceStats,
  )
  # or, equivalently, from axonpush import App, Channel, …
  ```

  Submodule paths like `axonpush.models.events.Event` and
  `axonpush.models.webhooks.WebhookEndpoint` are gone.

### Added

- **OpenAPI-driven HTTP client.** The transport layer at
  `src/axonpush/_internal/api/` is now generated from the backend's
  `/swagger/json` via `openapi-python-client`. Run `make codegen` to
  refresh after a schema change. Every resource method delegates to a
  generated `*_op.sync` / `*_op.asyncio` function — there are no
  hand-rolled HTTP wrappers left.
- **Structured backend errors.** Every `AxonPushError` carries
  `status_code`, `code`, `hint`, and `request_id` parsed from the
  backend's `{ code, message, hint, requestId }` global filter envelope.
  `request_id` falls back to the `X-Request-Id` response header when
  the body doesn't include it.
- **`RetryableError` mixin.** `APIConnectionError`, `RateLimitError`,
  and `ServerError` all subclass it. Catch `RetryableError` to handle
  every transient failure in one branch.
- **`Settings` reads env vars.** `AxonPush()` with zero kwargs now
  works — `Settings` (a `pydantic_settings.BaseSettings` subclass)
  picks up `AXONPUSH_API_KEY`, `AXONPUSH_TENANT_ID`, `AXONPUSH_BASE_URL`,
  `AXONPUSH_ENVIRONMENT`, `AXONPUSH_TIMEOUT`, `AXONPUSH_MAX_RETRIES`,
  and `AXONPUSH_FAIL_OPEN`. Constructor kwargs win over env vars.

### Improved

- **`BackgroundPublisher`** is now properly split into a sync
  (`BackgroundPublisher`) and an async
  (`AsyncBackgroundPublisher`) class. Both have a bounded queue, a
  graceful flush, per-event error isolation, and a re-entrancy guard
  against being called from inside their own worker (the sync/async
  conflation in v0.0.9 was a real bug — async callers were sometimes
  blocking the event loop on the sync queue).
- **Trace propagation in integrations.** `parent_run_id` →
  `parent_event_id` is now correctly threaded through the LangChain,
  Deep Agents, and OpenTelemetry callbacks, so nested chains and
  sub-agents land as a connected tree rather than as siblings.
- **Anthropic integration** captures `prompt_tokens` /
  `completion_tokens` / `total_tokens` from `Message.usage` and
  surfaces them on the published event.

### Fixed

- **`print_capture` no longer leaks file descriptors on uncaught exit.**
  The `atexit` hook now runs even when `setup_print_capture()` was never
  paired with an explicit `unpatch()`.
- **Realtime credential refresh race.** The refresh timer is now
  scheduled only after the broker's CONNACK confirms the initial
  connection landed. If the first connect fails the SDK no longer enters
  a silent reconnect loop — the `ConnectionError` propagates to the
  caller, who can decide how to retry.

### Migration from v0.0.9

1. **Replace `int` IDs with `str` everywhere.** Most callers were
   already using string UUIDs; if you were assembling URLs by hand or
   threading `int` IDs through your storage layer, switch to `str`.
2. **Replace deep model imports with the flat namespace:**

   ```python
   # before
   from axonpush.models.events import Event, EventType
   from axonpush.models.webhooks import WebhookEndpoint

   # after
   from axonpush import Event, EventType, WebhookEndpoint
   ```

3. **Replace `client.connect_websocket()` with `client.connect_realtime()`.**
   The signature is identical; the alias was only there to ease the
   v0.0.9 → v0.1.0 transition.
4. **Audit your error-handling clauses.** If you were catching
   `httpx.HTTPError` directly (because the SDK didn't wrap them), wrap
   with `AxonPushError` instead — every transport failure now flows
   through the SDK's hierarchy.

## [0.0.11] – 2026-05-01 (NEVER SHIPPED)

> Stale local version bump that never reached PyPI. Its content is
> rolled into the actual `0.0.10` release above.

**Breaking**: this release pairs with the backend move from per-app
environments to org-level environments, and reshapes the realtime MQTT
topic to include an env slot.

### Breaking changes
- **MQTT topic shape** now has an environment slot between org and app:

      old:  axonpush/{org}/{app}/{channel}/{eventType}/{agentId}
      new:  axonpush/{org}/{envSlug}/{app}/{channel}/{eventType}/{agentId}

  On subscribe, the env slot wildcards to ``+`` when the caller doesn't
  pass ``environment=...``. On publish, it falls back to the literal
  ``"default"`` so AWS IoT routes the message to the org's default
  environment. All segments are sanitised (``[^a-zA-Z0-9_-] -> _``) to
  match the backend topic-builder — e.g. ``agent.error`` is encoded as
  ``agent_error`` on the wire.
- **Environments are org-level**. The
  ``axonpush.resources.environments`` module now targets
  ``/environments`` (was ``/apps/{appId}/environments``). The ``app_id``
  argument is gone from every method on ``EnvironmentsResource`` /
  ``AsyncEnvironmentsResource``.
- ``Environment`` model drops the per-app ``app_id`` field; gains
  ``environment_id``, ``org_id``, ``slug``, ``is_default``,
  ``is_production``, ``is_ephemeral``, ``expires_at``.

### Added
- ``EnvironmentsResource`` / ``AsyncEnvironmentsResource`` with
  ``list()``, ``create(name, slug=, color=, is_production=,
  is_default=, clone_from_env_id=)``, ``update(env_id, ...)``,
  ``delete(env_id)``, ``promote_to_default(env_id)``. Wired in as
  ``client.environments``.
- ``environment=`` kwarg on
  ``RealtimeClient`` / ``AsyncRealtimeClient`` constructor,
  ``subscribe()``, ``unsubscribe()``, ``publish()``, plus
  ``client.connect_realtime(environment=...)``. Falls through to the
  client-level ``environment`` set on construction (or detected from
  ``AXONPUSH_ENVIRONMENT`` / ``SENTRY_ENVIRONMENT`` / ``APP_ENV`` /
  ``ENV``).
- ``Environment``, ``CreateEnvironmentParams``,
  ``UpdateEnvironmentParams`` exported from
  ``axonpush.models.environments`` (and ``axonpush.Environment``).

### Changed
- Topic-builder helpers ``build_subscribe_topic`` /
  ``build_publish_topic`` accept ``environment=`` (kw-only); subscribe
  wildcards missing slots, publish substitutes ``default`` for env and
  ``_`` for missing agent.

## [0.1.0] – 2026-04-29

**Breaking**: this release pairs with the AxonPush AWS-serverless rewrite
of the backend. Realtime moves from Socket.IO to AWS IoT Core MQTT-over-WSS;
SSE is removed; event search drops Lucene strings in favor of typed query
parameters.

### Removed
- `python-socketio[asyncio_client]` extra (was the `websocket` extra). The
  Socket.IO transport is gone; realtime now connects via MQTT-over-WSS to
  AWS IoT Core.
- `httpx-sse` core dependency. Server-Sent Events are no longer used.
- `q` (Lucene) parameter on `events.list()` / `events.search()`. Lucene is
  removed end-to-end.

### Added
- `paho-mqtt` and `aiomqtt` as core dependencies (sync and async MQTT
  transports respectively).
- `axonpush.realtime.RealtimeClient` and `AsyncRealtimeClient` with the
  same public surface as the previous WebSocket clients
  (`connect`, `on_event`, `subscribe(channel, event_type?, agent_id?)`,
  `publish`, `wait`, `disconnect`). The legacy
  `WebSocketClient`/`AsyncWebSocketClient` names are kept as aliases.
- `axonpush.realtime.topics.build_subscribe_topic` /
  `build_publish_topic` — public topic-builder helpers.
- `iot_endpoint` constructor parameter on `AxonPush(...)` and
  `AsyncAxonPush(...)` for callers who want to pre-pin the IoT Core ATS
  endpoint instead of letting `/auth/iot-credentials` return it.
- Typed event-query kwargs on `events.list()` / `events.search()`:
  `channel_id`, `app_id`, `environment_id`, `event_type` (str or list),
  `agent_id`, `trace_id`, `since`, `until`, `cursor`, `limit`,
  `payload_filter` (dict, JSON-encoded over the wire).
- `axonpush.resources.events_query.EventQuery` — Pydantic model mirroring
  the backend Zod schema.

### Changed
- `client.connect_websocket()` is now an alias for the new
  `client.connect_realtime()` (returns a `RealtimeClient`/`AsyncRealtimeClient`
  backed by MQTT). Existing callers keep working unchanged.
- `channels.subscribe_sse()` / `subscribe_event_sse()` retained as
  deprecation shims that internally open an MQTT subscription. They emit
  a `DeprecationWarning` on first call and will be removed in v0.2.0.

## [0.0.10] – 2026-04-25 (NEVER SHIPPED)

> Stale local version bump that never reached PyPI. Its content is
> rolled into the actual `0.0.10` release at the top of this file.

This release pairs with a server-side change: AxonPush now keys
retry-idempotency on a server-generated `dedup_key` UUID per record
instead of the user-facing `identifier`. Distinct logical events that
share an `identifier` (e.g. many log records on the same logger name)
all persist as separate rows. Requires AxonPush server with the
`AddEventDedupKeyAndSwapIndex` migration applied; older servers will
silently dedupe by `identifier`, same as before.

### Fixed
- Reconciled the version-string mismatch: `_version.py` (was `0.0.8`)
  now matches `pyproject.toml` and dist METADATA at `0.0.10`.

### Changed
- **`BackgroundPublisher`** now layers on top of stdlib
  `logging.handlers.QueueListener` instead of a hand-rolled worker
  thread. Public surface (`submit` / `flush` / `close`) and behavior
  unchanged; ~140 LOC removed.
- **Severity mapping** in `axonpush.integrations._otel_payload` now
  delegates to the canonical `opentelemetry._logs.severity.std_to_otel`
  when `opentelemetry-api` is installed (which it is whenever the
  `[otel]` extra is). Falls back to a small inline table otherwise.

### Notes for callers
- No SDK API changes. Every call site that constructs
  `BackgroundPublisher`, calls `events.publish`, or uses any of the
  observability integrations keeps working untouched.
- If you were working around the silent dedup-by-`identifier` bug with
  per-record unique suffixes (e.g. `f"{record.name}.{ts}.{seq}"`), you
  can drop that workaround once your AxonPush server is on the
  matching release. The plain `record.name` flows through and each
  record persists.

## [0.0.9] – earlier

Previous PyPI release. No CHANGELOG entry.
