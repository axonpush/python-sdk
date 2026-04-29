# Changelog

All notable changes to the AxonPush Python SDK are documented here. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning is [SemVer](https://semver.org/spec/v2.0.0.html).

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

## [0.0.10] – 2026-04-25

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
