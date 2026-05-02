"""AxonPush — real-time event infrastructure for AI agent systems.

Top-level package. Public API is re-exported here; internal helpers live
under ``axonpush._internal`` and are not part of the supported surface.
"""

from axonpush._version import __version__

# from _exports_a.txt
from axonpush.client import AxonPush, AsyncAxonPush
from axonpush.exceptions import (
    AxonPushError,
    APIConnectionError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RetryableError,
    ServerError,
    ValidationError,
)
from axonpush._tracing import TraceContext, current_trace, get_or_create_trace
from axonpush._config import Settings

# from _exports_b.txt
from axonpush.models import (
    App,
    ApiKey,
    Channel,
    CreateEventDto,
    DeliveryStatus,
    Environment,
    Event,
    EventDetails,
    EventType,
    Organization,
    TraceListItem,
    TraceStats,
    TraceSummary,
    User,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEndpointCreateResponseDto,
)
from axonpush.resources.api_keys import ApiKeys, AsyncApiKeys
from axonpush.resources.apps import Apps, AsyncApps
from axonpush.resources.channels import AsyncChannels, Channels
from axonpush.resources.environments import AsyncEnvironments, Environments
from axonpush.resources.events import AsyncEvents, Events
from axonpush.resources.organizations import AsyncOrganizations, Organizations
from axonpush.resources.traces import AsyncTraces, Traces
from axonpush.resources.webhooks import AsyncWebhooks, Webhooks

# from _exports_c.txt
from axonpush.realtime import AsyncRealtimeClient, RealtimeClient

# from _exports_d.txt
from axonpush.integrations.sentry import install_sentry

__all__ = [
    "APIConnectionError",
    "ApiKey",
    "ApiKeys",
    "App",
    "Apps",
    "AsyncApiKeys",
    "AsyncApps",
    "AsyncAxonPush",
    "AsyncChannels",
    "AsyncEnvironments",
    "AsyncEvents",
    "AsyncOrganizations",
    "AsyncRealtimeClient",
    "AsyncTraces",
    "AsyncWebhooks",
    "AuthenticationError",
    "AxonPush",
    "AxonPushError",
    "Channel",
    "Channels",
    "CreateEventDto",
    "DeliveryStatus",
    "Environment",
    "Environments",
    "Event",
    "EventDetails",
    "EventType",
    "Events",
    "ForbiddenError",
    "NotFoundError",
    "Organization",
    "Organizations",
    "RateLimitError",
    "RealtimeClient",
    "RetryableError",
    "ServerError",
    "Settings",
    "TraceContext",
    "TraceListItem",
    "TraceStats",
    "TraceSummary",
    "Traces",
    "User",
    "ValidationError",
    "WebhookDelivery",
    "WebhookEndpoint",
    "WebhookEndpointCreateResponseDto",
    "Webhooks",
    "__version__",
    "current_trace",
    "get_or_create_trace",
    "install_sentry",
]
