# Changelog

All notable changes to the AxonPush Python SDK are documented here. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning is [SemVer](https://semver.org/spec/v2.0.0.html).

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
