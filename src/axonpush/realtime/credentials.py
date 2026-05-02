"""IoT credential helpers — call the generated ``/auth/iot-credentials`` op.

These helpers are private to the realtime package; user-facing code reaches
them via :class:`axonpush.realtime.RealtimeClient` /
:class:`axonpush.realtime.AsyncRealtimeClient`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from axonpush._internal.api.api.auth import (
    iot_credentials_controller_get_credentials as _gen,
)
from axonpush._internal.api.models.iot_credentials_response_dto import (
    IotCredentialsResponseDto,
)

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush


@dataclass(frozen=True)
class IotCredentials:
    """Decoded ``/auth/iot-credentials`` payload.

    Attributes:
        endpoint: Bare AWS IoT endpoint host (no scheme).
        presigned_wss_url: Full presigned ``wss://`` URL the MQTT client
            should connect to.
        expires_at: When the presigned URL stops accepting new connections.
        topic_prefix: Org-scoped MQTT topic prefix
            (``"{prefix}/{org_id}"``). Pass to the topic builders.
        env_slug: Default env slug for this org — used when callers omit
            ``env_slug`` on publish.
        topic_template: Human-readable topic template (informational).
        client_id: Suggested MQTT client ID.
        region: AWS region the broker lives in.
    """

    endpoint: str
    presigned_wss_url: str
    expires_at: datetime
    topic_prefix: str
    env_slug: str
    topic_template: str
    client_id: str
    region: str

    def expires_in(self, *, now: datetime | None = None) -> float:
        """Seconds remaining until ``expires_at``."""
        current = now or datetime.now(timezone.utc)
        return (self.expires_at - current).total_seconds()


def _parse_expires_at(raw: str) -> datetime:
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _from_dto(dto: IotCredentialsResponseDto) -> IotCredentials:
    return IotCredentials(
        endpoint=dto.endpoint,
        presigned_wss_url=dto.presigned_wss_url,
        expires_at=_parse_expires_at(dto.expires_at),
        topic_prefix=dto.topic_prefix,
        env_slug=dto.env_slug,
        topic_template=dto.topic_template,
        client_id=dto.client_id,
        region=dto.region,
    )


def fetch_iot_credentials_sync(client: AxonPush) -> IotCredentials:
    """Fetch IoT credentials synchronously via the generated client.

    Args:
        client: Configured :class:`axonpush.client.AxonPush` facade. The
            call is routed through ``client._invoke`` so cross-cutting
            concerns (auth headers, retries, fail-open) apply uniformly.

    Returns:
        Parsed :class:`IotCredentials`.

    Raises:
        ConnectionError: If the backend returns an empty body or the
            facade is in fail-open mode and swallows a transport error.
        AxonPushError: Any documented API error subclass — raised by the
            facade's ``_invoke`` wrapper.
    """
    dto: IotCredentialsResponseDto | None = client._invoke(_gen)
    if dto is None:
        raise ConnectionError("Failed to fetch IoT credentials from /auth/iot-credentials")
    return _from_dto(dto)


async def fetch_iot_credentials_async(client: AsyncAxonPush) -> IotCredentials:
    """Async sibling of :func:`fetch_iot_credentials_sync`.

    Args:
        client: Configured :class:`axonpush.client.AsyncAxonPush` facade.

    Returns:
        Parsed :class:`IotCredentials`.

    Raises:
        ConnectionError: If the backend returns an empty body or the
            facade is in fail-open mode and swallows a transport error.
        AxonPushError: Any documented API error subclass.
    """
    dto: IotCredentialsResponseDto | None = await client._invoke(_gen)
    if dto is None:
        raise ConnectionError("Failed to fetch IoT credentials from /auth/iot-credentials")
    return _from_dto(dto)
