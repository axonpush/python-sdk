"""Stdlib ``logging.Handler`` that forwards records to AxonPush.

Use this for backend services that use Python's standard library ``logging``
module — the most common case. Each LogRecord is converted into an OpenTelemetry
shaped ``app.log`` event with ``severityNumber`` derived from the Python level.

Stdlib only — no extra dependencies.

Usage::

    import logging
    from axonpush import AxonPush
    from axonpush.integrations.logging_handler import AxonPushLoggingHandler

    client = AxonPush(api_key="ak_...", tenant_id="1")
    handler = AxonPushLoggingHandler(
        client=client,
        channel_id=1,
        service_name="my-api",
    )

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    logging.error("connection refused", extra={"user_id": 42})
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, FrozenSet, Optional, Sequence, Tuple, TYPE_CHECKING

from axonpush._tracing import current_trace, get_or_create_trace
from axonpush.integrations._otel_payload import (
    build_log_payload,
    severity_from_python_level,
)
from axonpush.models.events import EventType

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

_internal_logger = logging.getLogger("axonpush")


# Standard LogRecord attributes we don't want to forward as user attributes
# (they're either header info or covered by other payload fields).
_STD_LOGRECORD_ATTRS = frozenset(
    {
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "module", "msecs",
        "message", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "thread", "threadName", "taskName",
    }
)


# Loggers whose records must NEVER be shipped back to AxonPush. Publishing an
# event triggers an httpx HTTP request, which httpx itself logs at INFO level
# via its own stdlib logger — if we forwarded that record, we'd emit another
# event, triggering another log, and so on until the channel is flooded with
# echoing "HTTP Request: POST /event" lines.
#
# - ``httpx`` / ``httpcore`` are matched as PREFIXES because those libraries
#   create several sub-loggers (``httpx._client``, ``httpcore.connection``,
#   ``httpcore.http11``, ...).
# - ``axonpush`` is the SDK's own internal logger for warnings/diagnostics.
#   We match it by EXACT equality (not prefix), so user code that happens to
#   use the ``axonpush.*`` namespace (e.g. ``axonpush.plugins.foo`` or
#   ``axonpush.test.*``) still gets its records shipped normally.
#
# These defaults are always-on and cannot be disabled. Users can add more
# logger-name PREFIXES via the ``exclude_loggers`` kwarg on
# ``AxonPushLoggingHandler`` — those are additive.
_DEFAULT_EXCLUDED_EXACT: FrozenSet[str] = frozenset({"axonpush"})
_DEFAULT_EXCLUDED_PREFIXES: Tuple[str, ...] = ("httpx", "httpcore")

#: Public listing of always-on excluded logger names, in one place for
#: discoverability. Union of the exact-match and prefix-match defaults.
DEFAULT_EXCLUDED_LOGGERS: Tuple[str, ...] = (
    tuple(sorted(_DEFAULT_EXCLUDED_EXACT)) + _DEFAULT_EXCLUDED_PREFIXES
)


class _SelfRecursionFilter(logging.Filter):
    """Drops records whose logger name matches an excluded name or prefix.

    ``exact`` and ``prefixes`` are both checked — a record is dropped if
    ``record.name`` is in ``exact`` OR starts with any prefix in ``prefixes``.
    """

    def __init__(
        self, exact: FrozenSet[str], prefixes: Tuple[str, ...]
    ) -> None:
        super().__init__()
        self._exact = exact
        self._prefixes = prefixes

    def filter(self, record: logging.LogRecord) -> bool:
        name = record.name
        if name in self._exact:
            return False
        return not name.startswith(self._prefixes)


class AxonPushLoggingHandler(logging.Handler):
    """A ``logging.Handler`` that ships log records to AxonPush as ``app.log`` events."""

    def __init__(
        self,
        *,
        client: Optional["AxonPush | AsyncAxonPush"] = None,
        channel_id: int,
        api_key: Optional[str] = None,
        tenant_id: Optional[str] = None,
        base_url: Optional[str] = None,
        source: str = "app",
        service_name: Optional[str] = None,
        service_version: Optional[str] = None,
        environment: Optional[str] = None,
        agent_id: Optional[str] = None,
        level: int = logging.NOTSET,
        exclude_loggers: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(level=level)
        if source not in ("agent", "app"):
            raise ValueError(f"source must be 'agent' or 'app', got {source!r}")

        # Mutual exclusion: a pre-built client and credential kwargs are two
        # separate configuration modes — mixing them is almost always a bug.
        has_credentials = any(x is not None for x in (api_key, tenant_id, base_url))
        if client is not None and has_credentials:
            raise ValueError(
                "AxonPushLoggingHandler: pass either client= or "
                "api_key=/tenant_id=, not both"
            )

        # dictConfig path: no client instance available, build one from
        # explicit kwargs or environment variables.
        if client is None:
            client = self._build_client(api_key, tenant_id, base_url)

        self._client = client
        self._channel_id = channel_id
        self._source = source
        self._agent_id = agent_id

        resource: Dict[str, Any] = {}
        if service_name is not None:
            resource["service.name"] = service_name
        if service_version is not None:
            resource["service.version"] = service_version
        if environment is not None:
            resource["deployment.environment"] = environment
        self._resource = resource or None

        # Install the always-on self-recursion filter plus any user-supplied
        # logger-name prefixes. Additive — defaults cannot be disabled.
        user_prefixes = tuple(exclude_loggers or ())
        self.addFilter(
            _SelfRecursionFilter(
                exact=_DEFAULT_EXCLUDED_EXACT,
                prefixes=_DEFAULT_EXCLUDED_PREFIXES + user_prefixes,
            )
        )

    @staticmethod
    def _build_client(
        api_key: Optional[str],
        tenant_id: Optional[str],
        base_url: Optional[str],
    ) -> "AxonPush":
        """Construct a sync ``AxonPush`` client for dictConfig / env-var callers."""
        # Explicit kwargs first, then fall back to environment variables.
        api_key = api_key or os.environ.get("AXONPUSH_API_KEY")
        tenant_id = tenant_id or os.environ.get("AXONPUSH_TENANT_ID")
        base_url = base_url or os.environ.get("AXONPUSH_BASE_URL")

        if not api_key or not tenant_id:
            raise ValueError(
                "AxonPushLoggingHandler: provide either client= or "
                "api_key=/tenant_id= (or set the AXONPUSH_API_KEY and "
                "AXONPUSH_TENANT_ID environment variables)"
            )

        # Lazy import to avoid any circular-import risk at module load time.
        from axonpush.client import AxonPush

        kwargs: Dict[str, Any] = {"api_key": api_key, "tenant_id": tenant_id}
        if base_url is not None:
            kwargs["base_url"] = base_url
        return AxonPush(**kwargs)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            severity_number, severity_text = severity_from_python_level(record.levelno)

            # Body: prefer the formatted message, fall back to raw msg
            try:
                body: Any = record.getMessage()
            except Exception:  # pragma: no cover - defensive
                body = str(record.msg)

            # Pull file/function metadata into attributes
            attributes: Dict[str, Any] = {
                "code.filepath": record.pathname,
                "code.function": record.funcName,
                "code.lineno": record.lineno,
                "logger.name": record.name,
                "thread.name": record.threadName,
                "process.pid": record.process,
            }
            if record.module:
                attributes["code.namespace"] = record.module

            # Forward extra={} kwargs (anything not in the standard LogRecord attrs)
            for key, value in record.__dict__.items():
                if key in _STD_LOGRECORD_ATTRS or key.startswith("_"):
                    continue
                attributes[key] = value

            # Format exception info if present
            if record.exc_info:
                attributes["exception.type"] = (
                    record.exc_info[0].__name__ if record.exc_info[0] else None
                )
                attributes["exception.message"] = (
                    str(record.exc_info[1]) if record.exc_info[1] else None
                )

            payload = build_log_payload(
                body=body,
                severity_number=severity_number,
                severity_text=severity_text,
                time_unix_nano=str(int(record.created * 1_000_000_000)),
                attributes=attributes,
                resource=self._resource,
            )

            # Trace correlation: use the current AxonPush trace if one exists,
            # otherwise create one. This way logs always have SOMETHING to group
            # by, but they don't force a new trace if the user already has one.
            trace = current_trace() or get_or_create_trace()

            event_type = (
                EventType.APP_LOG if self._source == "app" else EventType.AGENT_LOG
            )

            result = self._client.events.publish(
                identifier=record.name,
                payload=payload,
                channel_id=self._channel_id,
                agent_id=self._agent_id,
                trace_id=trace.trace_id,
                span_id=trace.next_span_id(),
                event_type=event_type,
                metadata={"framework": "stdlib-logging"},
            )

            # Async client returns a coroutine — schedule on running loop if any.
            import asyncio

            if asyncio.iscoroutine(result):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(result)
                except RuntimeError:
                    pass
        except Exception:
            # Per logging.Handler convention, never raise from emit().
            # Print to stderr (the original, NOT a tee) for visibility.
            try:
                self.handleError(record)
            except Exception:
                print("AxonPush logging handler failed", file=sys.__stderr__)
