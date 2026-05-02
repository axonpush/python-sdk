"""Tee-based ``stdout`` / ``stderr`` capture that forwards prints to AxonPush.

Wraps ``sys.stdout`` and ``sys.stderr`` in a tee stream that buffers up
to a newline, then publishes each line as an OpenTelemetry-shaped log
event. Stdlib only — no extra dependencies.

Streams are restored on :meth:`PrintCaptureHandle.unpatch` and via an
``atexit`` hook so we never leave Python running with a dangling tee
stream after the user's app exits.
"""

from __future__ import annotations

import atexit
import logging
import sys
import time
import weakref
from dataclasses import dataclass, field
from typing import IO, TYPE_CHECKING, Any, Dict, Literal, Optional

from axonpush._tracing import get_or_create_trace
from axonpush.integrations._otel_payload import build_log_payload
from axonpush.integrations._publisher import (
    BackgroundPublisher,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_SHUTDOWN_TIMEOUT_S,
)
from axonpush.integrations._utils import (
    coerce_channel_id,
    fire_and_forget,
    is_async_client,
)
from axonpush.models import EventType

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

_logger = logging.getLogger("axonpush")

_LIVE_HANDLES: "weakref.WeakSet[PrintCaptureHandle]" = weakref.WeakSet()


@dataclass(eq=False)
class PrintCaptureHandle:
    """Returned by :func:`setup_print_capture`. Holds the originals."""

    _orig_stdout: IO[str]
    _orig_stderr: IO[str]
    _publisher: Optional[BackgroundPublisher] = field(default=None, repr=False)
    _unpatched: bool = field(default=False, repr=False)

    def unpatch(self) -> None:
        """Restore the original ``sys.stdout`` / ``sys.stderr`` streams."""
        if self._unpatched:
            return
        self._unpatched = True
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr
        if self._publisher is not None:
            self._publisher.close()
            self._publisher = None

    def flush(self, timeout: Optional[float] = None) -> None:
        if self._publisher is not None:
            self._publisher.flush(timeout)

    def __enter__(self) -> "PrintCaptureHandle":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.unpatch()


class _AxonPushTeeStream:
    """A tee that writes to the original stream and also publishes to AxonPush."""

    def __init__(
        self,
        original: IO[str],
        client: "AxonPush | AsyncAxonPush",
        channel_id: str,
        *,
        agent_id: Optional[str],
        source: str,
        stream_name: str,
        service_name: Optional[str],
        publisher: Optional[BackgroundPublisher] = None,
    ) -> None:
        self._original = original
        self._client = client
        self._channel_id = channel_id
        self._agent_id = agent_id
        self._source = source
        self._stream_name = stream_name
        self._service_name = service_name
        self._publisher = publisher
        self._buffer = ""
        self._trace = get_or_create_trace()

    def write(self, data: str) -> int:
        result = self._original.write(data)
        try:
            self._buffer += data
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                if line.strip():
                    self._emit(line)
        except Exception as exc:
            _logger.warning("AxonPush print capture failed: %s", exc)
        return result

    def flush(self) -> None:
        self._original.flush()
        if self._buffer.strip():
            try:
                self._emit(self._buffer)
            except Exception as exc:
                _logger.warning("AxonPush print capture flush failed: %s", exc)
            self._buffer = ""

    def __getattr__(self, name: str) -> Any:
        return getattr(self._original, name)

    def _emit(self, line: str) -> None:
        if self._stream_name == "stderr":
            severity_number, severity_text = (17, "ERROR")
        else:
            severity_number, severity_text = (9, "INFO")

        attributes: Dict[str, Any] = {
            "log.iostream": self._stream_name,
            "log.source": "print",
        }
        resource = {"service.name": self._service_name} if self._service_name else None

        payload = build_log_payload(
            body=line,
            severity_number=severity_number,
            severity_text=severity_text,
            time_unix_nano=str(int(time.time() * 1_000_000_000)),
            attributes=attributes,
            resource=resource,
        )

        event_type = EventType.APP_LOG if self._source == "app" else EventType.AGENT_LOG

        publish_kwargs: Dict[str, Any] = {
            "identifier": "print",
            "payload": payload,
            "channel_id": self._channel_id,
            "agent_id": self._agent_id,
            "trace_id": self._trace.trace_id,
            "span_id": self._trace.next_span_id(),
            "event_type": event_type,
            "metadata": {"framework": "print-capture"},
        }

        if self._publisher is not None:
            self._publisher.submit(publish_kwargs)
            return

        try:
            result = self._client.events.publish(**publish_kwargs)
            fire_and_forget(result)
        except Exception as exc:
            _logger.warning("AxonPush print capture publish failed: %s", exc)


def setup_print_capture(
    client: "AxonPush | AsyncAxonPush",
    channel_id: int | str,
    *,
    agent_id: Optional[str] = None,
    source: str = "agent",
    service_name: Optional[str] = None,
    mode: Optional[Literal["background", "sync"]] = None,
    queue_size: int = DEFAULT_QUEUE_SIZE,
    shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
) -> PrintCaptureHandle:
    """Tee ``sys.stdout`` / ``sys.stderr`` and forward each line to AxonPush.

    Returns a :class:`PrintCaptureHandle` whose :meth:`~PrintCaptureHandle.unpatch`
    restores the streams. Also registered with an ``atexit`` hook so the
    streams are unpatched if the user's app exits without calling unpatch.
    """
    if source not in ("agent", "app"):
        raise ValueError(f"source must be 'agent' or 'app', got {source!r}")

    coerced_channel = coerce_channel_id(channel_id)

    resolved_mode = mode or "background"
    publisher: Optional[BackgroundPublisher] = None
    if resolved_mode == "background":
        if not is_async_client(client):
            publisher = BackgroundPublisher(
                client,  # type: ignore[arg-type]
                queue_size=queue_size,
                shutdown_timeout=shutdown_timeout,
            )

    orig_stdout, orig_stderr = sys.stdout, sys.stderr

    sys.stdout = _AxonPushTeeStream(
        orig_stdout,
        client,
        coerced_channel,
        agent_id=agent_id,
        source=source,
        stream_name="stdout",
        service_name=service_name,
        publisher=publisher,
    )
    sys.stderr = _AxonPushTeeStream(
        orig_stderr,
        client,
        coerced_channel,
        agent_id=agent_id,
        source=source,
        stream_name="stderr",
        service_name=service_name,
        publisher=publisher,
    )

    handle = PrintCaptureHandle(
        _orig_stdout=orig_stdout,
        _orig_stderr=orig_stderr,
        _publisher=publisher,
    )
    _LIVE_HANDLES.add(handle)
    return handle


def _unpatch_all_handles() -> None:
    for handle in list(_LIVE_HANDLES):
        try:
            handle.unpatch()
        except Exception:
            pass


atexit.register(_unpatch_all_handles)
