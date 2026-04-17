from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass, field
from typing import IO, Any, Dict, Literal, Optional, TYPE_CHECKING

from axonpush._tracing import get_or_create_trace
from axonpush.integrations._otel_payload import build_log_payload
from axonpush.integrations._publisher import (
    BackgroundPublisher,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_SHUTDOWN_TIMEOUT_S,
)
from axonpush.integrations._utils import fire_and_forget
from axonpush.models.events import EventType

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

_logger = logging.getLogger("axonpush")


@dataclass
class PrintCaptureHandle:
    _orig_stdout: IO[str]
    _orig_stderr: IO[str]
    _publisher: Optional[BackgroundPublisher] = field(default=None, repr=False)

    def unpatch(self) -> None:
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr
        if self._publisher is not None:
            self._publisher.close()
            self._publisher = None

    def flush(self, timeout: Optional[float] = None) -> None:
        if self._publisher is not None:
            self._publisher.flush(timeout)


class _AxonPushTeeStream:

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
    channel_id: int,
    *,
    agent_id: Optional[str] = None,
    source: str = "agent",
    service_name: Optional[str] = None,
    mode: Optional[Literal["background", "sync"]] = None,
    queue_size: int = DEFAULT_QUEUE_SIZE,
    shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
) -> PrintCaptureHandle:
    if source not in ("agent", "app"):
        raise ValueError(f"source must be 'agent' or 'app', got {source!r}")

    resolved_mode = mode or "background"
    publisher: Optional[BackgroundPublisher] = None
    if resolved_mode == "background":
        publisher = BackgroundPublisher(
            client, queue_size=queue_size, shutdown_timeout=shutdown_timeout,
        )

    orig_stdout, orig_stderr = sys.stdout, sys.stderr

    sys.stdout = _AxonPushTeeStream(
        orig_stdout, client, channel_id,
        agent_id=agent_id, source=source, stream_name="stdout",
        service_name=service_name, publisher=publisher,
    )
    sys.stderr = _AxonPushTeeStream(
        orig_stderr, client, channel_id,
        agent_id=agent_id, source=source, stream_name="stderr",
        service_name=service_name, publisher=publisher,
    )

    return PrintCaptureHandle(
        _orig_stdout=orig_stdout,
        _orig_stderr=orig_stderr,
        _publisher=publisher,
    )
