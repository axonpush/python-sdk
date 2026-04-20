"""AxonPush — Python SDK for real-time event infrastructure for AI agent systems."""

from axonpush._tracing import TraceContext, get_or_create_trace
from axonpush._version import __version__
from axonpush.client import AsyncAxonPush, AxonPush
from axonpush.integrations.sentry import install_sentry as install_sentry
from axonpush.exceptions import (
    APIConnectionError,
    AuthenticationError,
    AxonPushError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from axonpush.models.apps import App
from axonpush.models.channels import Channel
from axonpush.models.events import Event, EventType
from axonpush.models.traces import TraceListItem, TraceSummary
from axonpush.models.webhooks import DeliveryStatus, WebhookDelivery, WebhookEndpoint

__all__ = [
    # Clients
    "AxonPush",
    "AsyncAxonPush",
    # Models
    "App",
    "Channel",
    "DeliveryStatus",
    "Event",
    "EventType",
    "TraceListItem",
    "TraceSummary",
    "WebhookDelivery",
    "WebhookEndpoint",
    # Tracing
    "TraceContext",
    "get_or_create_trace",
    # Integrations
    "install_sentry",
    # Exceptions
    "APIConnectionError",
    "AuthenticationError",
    "AxonPushError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    # Meta
    "__version__",
]
