from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from axonpush._http import AsyncTransport, SyncTransport, _is_fail_open


@dataclass(frozen=True)
class IotCredentials:
    endpoint: str
    presigned_wss_url: str
    expires_at: datetime

    def expires_in(self, *, now: Optional[datetime] = None) -> float:
        current = now or datetime.now(timezone.utc)
        return (self.expires_at - current).total_seconds()


_CREDENTIAL_PATH = "/auth/iot-credentials"


def _parse(data: Any) -> Optional[IotCredentials]:
    if not isinstance(data, dict):
        return None
    try:
        endpoint = str(data["endpoint"])
        url = str(data["presignedWssUrl"])
        expires_raw = str(data["expiresAt"])
    except KeyError:
        return None
    expires_at = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return IotCredentials(endpoint=endpoint, presigned_wss_url=url, expires_at=expires_at)


def fetch_credentials_sync(
    transport: SyncTransport, *, iot_endpoint: Optional[str] = None
) -> Optional[IotCredentials]:
    params: Optional[Dict[str, Any]] = None
    if iot_endpoint:
        params = {"endpoint": iot_endpoint}
    data = transport.request("GET", _CREDENTIAL_PATH, params=params)
    if _is_fail_open(data):
        return None
    return _parse(data)


async def fetch_credentials_async(
    transport: AsyncTransport, *, iot_endpoint: Optional[str] = None
) -> Optional[IotCredentials]:
    params: Optional[Dict[str, Any]] = None
    if iot_endpoint:
        params = {"endpoint": iot_endpoint}
    data = await transport.request("GET", _CREDENTIAL_PATH, params=params)
    if _is_fail_open(data):
        return None
    return _parse(data)
