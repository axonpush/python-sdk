"""Sentry SDK integration helper.

Builds a Sentry DSN from AxonPush credentials and forwards to sentry_sdk.init.
Makes it a one-liner to wire Sentry to AxonPush instead of Sentry's cloud.

Usage::

    from axonpush.integrations.sentry import install_sentry
    install_sentry(
        api_key="ak_...",
        channel_id=42,
        environment="production",
        release="my-app@1.2.3",
    )

Environment variable fallbacks (when args are omitted):
    - api_key:     AXONPUSH_API_KEY
    - channel_id:  AXONPUSH_CHANNEL_ID
    - host:        AXONPUSH_HOST (default: api.axonpush.xyz)
    - environment: AXONPUSH_ENVIRONMENT, then SENTRY_ENVIRONMENT, then APP_ENV, then ENV
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger("axonpush.sentry")

_ENV_PRECEDENCE = (
    "AXONPUSH_ENVIRONMENT",
    "SENTRY_ENVIRONMENT",
    "APP_ENV",
    "ENV",
)


def build_dsn(api_key: str, channel_id: int, host: str) -> str:
    scheme = "http" if host.startswith("localhost") or host.startswith("127.") else "https"
    return f"{scheme}://{api_key}@{host}/{channel_id}"


def _detect_environment() -> Optional[str]:
    for name in _ENV_PRECEDENCE:
        val = os.getenv(name)
        if val:
            return val
    return None


def install_sentry(
    *,
    api_key: Optional[str] = None,
    channel_id: Optional[int] = None,
    host: Optional[str] = None,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    dsn: Optional[str] = None,
    **sentry_init_kwargs: Any,
) -> None:
    """Initialize the Sentry SDK, pointed at AxonPush.

    Raises ImportError if the user hasn't installed `sentry-sdk`.
    """
    try:
        import sentry_sdk  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "install_sentry requires sentry-sdk. Install it with `pip install sentry-sdk`.",
        ) from exc

    if dsn is None:
        api_key = api_key or os.getenv("AXONPUSH_API_KEY")
        channel_id = channel_id or (
            int(os.getenv("AXONPUSH_CHANNEL_ID")) if os.getenv("AXONPUSH_CHANNEL_ID") else None
        )
        host = host or os.getenv("AXONPUSH_HOST") or "api.axonpush.xyz"
        if not api_key or not channel_id:
            raise ValueError(
                "install_sentry needs api_key and channel_id (or a fully-formed dsn). "
                "Pass them as arguments or set AXONPUSH_API_KEY and AXONPUSH_CHANNEL_ID.",
            )
        dsn = build_dsn(api_key, channel_id, host)

    resolved_env = environment if environment is not None else _detect_environment()
    logger.debug(
        "install_sentry: dsn host=%s environment=%s release=%s",
        dsn.rsplit("@", 1)[-1] if "@" in dsn else dsn,
        resolved_env,
        release,
    )

    init_kwargs: dict[str, Any] = {"dsn": dsn, **sentry_init_kwargs}
    if resolved_env is not None:
        init_kwargs.setdefault("environment", resolved_env)
    if release is not None:
        init_kwargs.setdefault("release", release)

    sentry_sdk.init(**init_kwargs)
