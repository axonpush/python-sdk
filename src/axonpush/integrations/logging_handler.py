"""Stdlib ``logging.Handler`` that forwards records to AxonPush.

Each :class:`logging.LogRecord` is converted into an OpenTelemetry-shaped
``app.log`` (or ``agent.log``) event with ``severityNumber`` derived
from the Python level. Stdlib only — no extra deps required.

The handler installs a :class:`_SelfRecursionFilter` that drops records
emitted by the publisher / httpx itself, plus a context-var check
(``_in_publisher_path``) so any record that does sneak through while the
publisher is busy is also discarded.

Tested against CPython 3.10–3.13.

Usage::

    import logging
    from axonpush import AxonPush
    from axonpush.integrations.logging_handler import AxonPushLoggingHandler

    client = AxonPush(api_key="ak_...", tenant_id="org_...")
    handler = AxonPushLoggingHandler(
        client=client,
        channel_id="ch_...",
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
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    FrozenSet,
    Literal,
    Optional,
    Sequence,
    Tuple,
)

from axonpush._tracing import current_trace, get_or_create_trace
from axonpush.integrations._otel_payload import (
    build_log_payload,
    severity_from_python_level,
)
from axonpush.integrations._publisher import (
    BackgroundPublisher,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_SHUTDOWN_TIMEOUT_S,
    detect_serverless,
    flush_after_invocation,
    in_publisher_path,
)
from axonpush.integrations._utils import (
    build_resource,
    coerce_channel_id,
    fire_and_forget,
    is_async_client,
)
from axonpush.models import EventType

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

__all__ = [
    "AxonPushLoggingHandler",
    "DEFAULT_EXCLUDED_LOGGERS",
    "flush_after_invocation",
]

_internal_logger = logging.getLogger("axonpush")


_STD_LOGRECORD_ATTRS = frozenset(
    {
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "module", "msecs",
        "message", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "thread", "threadName", "taskName",
    }
)


# Loggers whose records must NEVER be shipped back to AxonPush. Publishing
# triggers an httpx request, which httpx itself logs; without these defaults
# we'd loop forever.
_DEFAULT_EXCLUDED_EXACT: FrozenSet[str] = frozenset({"axonpush"})
_DEFAULT_EXCLUDED_PREFIXES: Tuple[str, ...] = ("httpx", "httpcore", "axonpush.publisher")

DEFAULT_EXCLUDED_LOGGERS: Tuple[str, ...] = (
    tuple(sorted(_DEFAULT_EXCLUDED_EXACT)) + _DEFAULT_EXCLUDED_PREFIXES
)


class _SelfRecursionFilter(logging.Filter):
    """Drops records whose logger name matches an excluded name or prefix."""

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
        channel_id: int | str,
        client: Optional["AxonPush | AsyncAxonPush"] = None,
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
        mode: Optional[Literal["background", "sync"]] = None,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
    ) -> None:
        super().__init__(level=level)
        if source not in ("agent", "app"):
            raise ValueError(f"source must be 'agent' or 'app', got {source!r}")

        has_credentials = any(x is not None for x in (api_key, tenant_id, base_url))
        if client is not None and has_credentials:
            raise ValueError(
                "AxonPushLoggingHandler: pass either client= or "
                "api_key=/tenant_id=, not both"
            )

        if client is None:
            client = self._build_client(api_key, tenant_id, base_url)

        self._client = client
        self._channel_id = coerce_channel_id(channel_id)
        self._source = source
        self._agent_id = agent_id
        self._environment = environment

        self._resource = build_resource(service_name, service_version, environment)

        user_prefixes = tuple(exclude_loggers or ())
        self.addFilter(
            _SelfRecursionFilter(
                exact=_DEFAULT_EXCLUDED_EXACT,
                prefixes=_DEFAULT_EXCLUDED_PREFIXES + user_prefixes,
            )
        )

        resolved_mode = mode or "background"
        if resolved_mode not in ("background", "sync"):
            raise ValueError(
                f"mode must be 'background' or 'sync', got {resolved_mode!r}"
            )
        if resolved_mode == "background":
            if is_async_client(self._client):
                self._publisher: Optional[BackgroundPublisher] = None
            else:
                self._publisher = BackgroundPublisher(
                    self._client,  # type: ignore[arg-type]
                    queue_size=queue_size,
                    shutdown_timeout=shutdown_timeout,
                )
        else:
            self._publisher = None

        serverless = detect_serverless()
        if serverless is not None and self._publisher is not None:
            _internal_logger.info(
                "AxonPush detected %s. Call handler.flush() at the end of "
                "each invocation (or wrap your handler with "
                "axonpush.integrations.logging_handler.flush_after_invocation) "
                "to avoid losing records when the container is frozen.",
                serverless,
            )

    @staticmethod
    def _build_client(
        api_key: Optional[str],
        tenant_id: Optional[str],
        base_url: Optional[str],
    ) -> "AxonPush":
        api_key = api_key or os.environ.get("AXONPUSH_API_KEY")
        tenant_id = tenant_id or os.environ.get("AXONPUSH_TENANT_ID")
        base_url = base_url or os.environ.get("AXONPUSH_BASE_URL")

        if not api_key or not tenant_id:
            raise ValueError(
                "AxonPushLoggingHandler: provide either client= or "
                "api_key=/tenant_id= (or set the AXONPUSH_API_KEY and "
                "AXONPUSH_TENANT_ID environment variables)"
            )

        from axonpush.client import AxonPush

        kwargs: Dict[str, Any] = {"api_key": api_key, "tenant_id": tenant_id}
        if base_url is not None:
            kwargs["base_url"] = base_url
        return AxonPush(**kwargs)

    def emit(self, record: logging.LogRecord) -> None:
        if in_publisher_path():
            return
        try:
            severity_number, severity_text = severity_from_python_level(record.levelno)

            try:
                body: Any = record.getMessage()
            except Exception:  # pragma: no cover - defensive
                body = str(record.msg)

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

            for key, value in record.__dict__.items():
                if key in _STD_LOGRECORD_ATTRS or key.startswith("_"):
                    continue
                attributes[key] = value

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

            trace = current_trace() or get_or_create_trace()

            event_type = (
                EventType.APP_LOG if self._source == "app" else EventType.AGENT_LOG
            )

            publish_kwargs: Dict[str, Any] = {
                "identifier": record.name,
                "payload": payload,
                "channel_id": self._channel_id,
                "agent_id": self._agent_id,
                "trace_id": trace.trace_id,
                "span_id": trace.next_span_id(),
                "event_type": event_type,
                "metadata": {"framework": "stdlib-logging"},
            }
            if self._environment is not None:
                publish_kwargs["environment"] = self._environment

            if self._publisher is not None:
                self._publisher.submit(publish_kwargs)
                return

            result = self._client.events.publish(**publish_kwargs)
            fire_and_forget(result)
        except Exception:
            try:
                self.handleError(record)
            except Exception:
                print("AxonPush logging handler failed", file=sys.__stderr__)

    def flush(self, timeout: Optional[float] = None) -> None:
        """Block until queued records are published, or until ``timeout``."""
        if self._publisher is not None:
            self._publisher.flush(timeout)
        super().flush()

    def close(self) -> None:
        """Stop the background worker and release resources."""
        if self._publisher is not None:
            self._publisher.close()
            self._publisher = None
        super().close()
