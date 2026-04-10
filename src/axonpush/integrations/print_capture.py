"""Capture print() and stdout/stderr writes and forward them to AxonPush.

Use this for AI agent projects where the agent (or its tools) emits free-form
output via ``print()``. The wizard wires this up automatically for detected
agent projects so that any ``print`` call shows up in the trace timeline.

Stdlib only — no extra dependencies.

Usage::

    from axonpush import AxonPush
    from axonpush.integrations.print_capture import setup_print_capture

    client = AxonPush(api_key="ak_...", tenant_id="1")
    handle = setup_print_capture(client, channel_id=1)

    print("agent started")  # forwarded to AxonPush as an agent.log event

    handle.unpatch()  # restore the original sys.stdout/sys.stderr
"""
from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from typing import IO, Any, Optional, TYPE_CHECKING

from axonpush._tracing import get_or_create_trace
from axonpush.integrations._otel_payload import build_log_payload
from axonpush.models.events import EventType

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

_logger = logging.getLogger("axonpush")


@dataclass
class PrintCaptureHandle:
    """Returned by ``setup_print_capture()``. Call ``unpatch()`` to restore stdio."""

    _orig_stdout: IO[str]
    _orig_stderr: IO[str]

    def unpatch(self) -> None:
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr


class _AxonPushTeeStream:
    """A file-like stream that writes to BOTH the original stream AND AxonPush.

    Buffers partial lines and only emits a log event when a newline is seen
    so we don't fragment the output across multiple events.
    """

    def __init__(
        self,
        original: IO[str],
        client: "AxonPush | AsyncAxonPush",
        channel_id: int,
        *,
        agent_id: Optional[str],
        source: str,
        stream_name: str,
        service_name: Optional[str],
    ) -> None:
        self._original = original
        self._client = client
        self._channel_id = channel_id
        self._agent_id = agent_id
        self._source = source
        self._stream_name = stream_name  # "stdout" or "stderr"
        self._service_name = service_name
        self._buffer = ""
        self._trace = get_or_create_trace()

    def write(self, data: str) -> int:
        # Always pass through to the original stream first.
        result = self._original.write(data)

        # Buffer until we see a newline; then emit one event per line.
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
        # Delegate any other attribute access to the original stream so the
        # tee is a drop-in replacement (isatty, fileno, encoding, etc.)
        return getattr(self._original, name)

    def _emit(self, line: str) -> None:
        # stderr → ERROR severity by default; stdout → INFO
        if self._stream_name == "stderr":
            severity_number, severity_text = (17, "ERROR")
        else:
            severity_number, severity_text = (9, "INFO")

        attributes = {
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

        try:
            # Use the events.publish API; both sync and async clients expose it.
            # For the async client, the call returns a coroutine — we ignore the
            # result (fire-and-forget). The user is responsible for keeping
            # an event loop running if they're using AsyncAxonPush.
            result = self._client.events.publish(  # type: ignore[union-attr]
                identifier="print",
                payload=payload,
                channel_id=self._channel_id,
                agent_id=self._agent_id,
                trace_id=self._trace.trace_id,
                span_id=self._trace.next_span_id(),
                event_type=event_type,
                metadata={"framework": "print-capture"},
            )
            # Async client returns a coroutine — schedule it on the running loop
            # if there is one, otherwise drop (the caller doesn't await us).
            if hasattr(result, "__await__"):
                try:
                    import asyncio

                    loop = asyncio.get_running_loop()
                    loop.create_task(result)
                except RuntimeError:
                    # No running loop; nothing we can do here.
                    pass
        except Exception as exc:
            _logger.warning("AxonPush print capture publish failed: %s", exc)


def setup_print_capture(
    client: "AxonPush | AsyncAxonPush",
    channel_id: int,
    *,
    agent_id: Optional[str] = None,
    source: str = "agent",
    service_name: Optional[str] = None,
) -> PrintCaptureHandle:
    """Patch ``sys.stdout`` / ``sys.stderr`` to forward writes to AxonPush.

    :param source: ``"agent"`` (default) → events tagged ``agent.log``;
                   ``"app"``             → events tagged ``app.log``.
    :param service_name: optional ``service.name`` resource attribute to
                         attach to every captured line.
    """
    if source not in ("agent", "app"):
        raise ValueError(f"source must be 'agent' or 'app', got {source!r}")

    orig_stdout, orig_stderr = sys.stdout, sys.stderr

    sys.stdout = _AxonPushTeeStream(  # type: ignore[assignment]
        orig_stdout,
        client,
        channel_id,
        agent_id=agent_id,
        source=source,
        stream_name="stdout",
        service_name=service_name,
    )
    sys.stderr = _AxonPushTeeStream(  # type: ignore[assignment]
        orig_stderr,
        client,
        channel_id,
        agent_id=agent_id,
        source=source,
        stream_name="stderr",
        service_name=service_name,
    )

    return PrintCaptureHandle(_orig_stdout=orig_stdout, _orig_stderr=orig_stderr)
