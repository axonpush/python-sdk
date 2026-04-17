from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Union

try:
    import anthropic  # noqa: F401
except ImportError:
    raise ImportError(
        "Anthropic integration requires the 'anthropic' extra. "
        "Install it with: pip install axonpush[anthropic]"
    ) from None

from axonpush._tracing import get_or_create_trace
from axonpush.integrations._publisher import (
    AsyncBackgroundPublisher,
    BackgroundPublisher,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_SHUTDOWN_TIMEOUT_S,
    RqPublisher,
)
from axonpush.models.events import EventType

logger = logging.getLogger("axonpush")

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

_SyncPublisherT = Union[BackgroundPublisher, RqPublisher, None]
_AsyncPublisherT = Union[AsyncBackgroundPublisher, RqPublisher, None]


class AxonPushAnthropicTracer:

    def __init__(
        self,
        client: "AxonPush | AsyncAxonPush",
        channel_id: int,
        *,
        agent_id: str = "claude",
        trace_id: Optional[str] = None,
        mode: Optional[Literal["background", "sync", "rq"]] = None,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
        max_pending: int = DEFAULT_QUEUE_SIZE,
        rq_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._client = client
        self._channel_id = channel_id
        self._agent_id = agent_id
        self._trace = get_or_create_trace(trace_id)

        resolved_mode = mode or "background"

        self._sync_publisher: _SyncPublisherT = None
        self._async_publisher: _AsyncPublisherT = None

        if resolved_mode == "rq":
            rq_pub = RqPublisher(client, **(rq_options or {}))
            self._sync_publisher = rq_pub
            self._async_publisher = rq_pub
        elif resolved_mode == "background":
            from axonpush.client import AsyncAxonPush as _AsyncAxonPush
            if isinstance(client, _AsyncAxonPush):
                self._async_publisher = AsyncBackgroundPublisher(
                    client, max_pending=max_pending,
                )
            else:
                self._sync_publisher = BackgroundPublisher(
                    client, queue_size=queue_size, shutdown_timeout=shutdown_timeout,
                )

    def create_message(self, anthropic_client: Any, **kwargs: Any) -> Any:
        self._emit_sync(
            "conversation.turn", EventType.AGENT_START,
            {"model": kwargs.get("model"), "message_count": len(kwargs.get("messages", []))},
        )
        response = anthropic_client.messages.create(**kwargs)
        self._process_response(response)
        return response

    async def acreate_message(self, anthropic_client: Any, **kwargs: Any) -> Any:
        self._emit_async(
            "conversation.turn", EventType.AGENT_START,
            {"model": kwargs.get("model"), "message_count": len(kwargs.get("messages", []))},
        )
        response = await anthropic_client.messages.create(**kwargs)
        self._aprocess_response(response)
        return response

    def send_tool_result(self, tool_use_id: str, result: Any) -> None:
        self._emit_sync(
            "tool.result", EventType.AGENT_TOOL_CALL_END,
            {"tool_use_id": tool_use_id, "result_preview": str(result)[:500]},
        )

    async def asend_tool_result(self, tool_use_id: str, result: Any) -> None:
        self._emit_async(
            "tool.result", EventType.AGENT_TOOL_CALL_END,
            {"tool_use_id": tool_use_id, "result_preview": str(result)[:500]},
        )

    def _process_response(self, response: Any) -> None:
        for block in getattr(response, "content", []):
            block_type = getattr(block, "type", None)
            if block_type == "tool_use":
                self._emit_sync(
                    f"tool.{block.name}.start", EventType.AGENT_TOOL_CALL_START,
                    {"tool_name": block.name, "tool_use_id": block.id, "input": _truncate(block.input)},
                )
            elif block_type == "text":
                self._emit_sync(
                    "agent.response", EventType.AGENT_MESSAGE,
                    {"text_length": len(block.text)},
                )

    def _aprocess_response(self, response: Any) -> None:
        for block in getattr(response, "content", []):
            block_type = getattr(block, "type", None)
            if block_type == "tool_use":
                self._emit_async(
                    f"tool.{block.name}.start", EventType.AGENT_TOOL_CALL_START,
                    {"tool_name": block.name, "tool_use_id": block.id, "input": _truncate(block.input)},
                )
            elif block_type == "text":
                self._emit_async(
                    "agent.response", EventType.AGENT_MESSAGE,
                    {"text_length": len(block.text)},
                )

    def _emit_sync(
        self, identifier: str, event_type: EventType, payload: Dict[str, Any],
    ) -> None:
        try:
            publish_kwargs: Dict[str, Any] = {
                "identifier": identifier,
                "payload": payload,
                "channel_id": self._channel_id,
                "agent_id": self._agent_id,
                "trace_id": self._trace.trace_id,
                "span_id": self._trace.next_span_id(),
                "event_type": event_type,
                "metadata": {"framework": "anthropic"},
            }

            if self._sync_publisher is not None:
                self._sync_publisher.submit(publish_kwargs)
                return

            self._client.events.publish(**publish_kwargs)
        except Exception:
            logger.warning("AxonPush: failed to emit event %r, suppressing.", identifier, exc_info=True)

    def _emit_async(
        self, identifier: str, event_type: EventType, payload: Dict[str, Any],
    ) -> None:
        try:
            publish_kwargs: Dict[str, Any] = {
                "identifier": identifier,
                "payload": payload,
                "channel_id": self._channel_id,
                "agent_id": self._agent_id,
                "trace_id": self._trace.trace_id,
                "span_id": self._trace.next_span_id(),
                "event_type": event_type,
                "metadata": {"framework": "anthropic"},
            }

            if self._async_publisher is not None:
                self._async_publisher.submit(publish_kwargs)
                return

            logger.warning(
                "AxonPush: anthropic async tracer in sync mode — event %r not published.", identifier,
            )
        except Exception:
            logger.warning("AxonPush: failed to emit event %r, suppressing.", identifier, exc_info=True)

    def flush(self, timeout: Optional[float] = None) -> None:
        if self._sync_publisher is not None:
            self._sync_publisher.flush(timeout)

    async def aflush(self, timeout: Optional[float] = None) -> None:
        if isinstance(self._async_publisher, AsyncBackgroundPublisher):
            await self._async_publisher.flush(timeout)
        elif self._async_publisher is not None:
            self._async_publisher.flush(timeout)
        if self._sync_publisher is not None:
            self._sync_publisher.flush(timeout)

    def close(self) -> None:
        if self._sync_publisher is not None:
            self._sync_publisher.close()
            self._sync_publisher = None

    async def aclose(self) -> None:
        if isinstance(self._async_publisher, AsyncBackgroundPublisher):
            await self._async_publisher.close()
        elif self._async_publisher is not None:
            self._async_publisher.close()
        self._async_publisher = None
        if self._sync_publisher is not None:
            self._sync_publisher.close()
            self._sync_publisher = None


def _truncate(obj: Any, max_len: int = 500) -> Any:
    s = str(obj)
    return s[:max_len] if len(s) > max_len else s
