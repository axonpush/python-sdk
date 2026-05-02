"""Sentry SDK integration helper.

Builds a Sentry DSN that points the official ``sentry-sdk`` at the
AxonPush ``/api/{projectId}/envelope`` endpoint and forwards every other
``sentry_sdk.init`` kwarg through. Makes wiring Sentry to AxonPush a
one-liner.

The backend's :file:`src/sentry/sentry.controller.ts` parses the
``:projectId`` URL segment as the AxonPush channel id and accepts any
non-empty string — including the new ``str`` UUIDs introduced in v0.0.10
— so callers can pass either ``int`` (deprecated, soft-converted) or
``str``.

Tested against ``sentry-sdk>=1.40,<3``.

Usage::

    from axonpush.integrations.sentry import install_sentry
    install_sentry(
        api_key="ak_...",
        channel_id="ch_...",
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

from axonpush.integrations._utils import coerce_channel_id

logger = logging.getLogger("axonpush.sentry")

_ENV_PRECEDENCE = (
    "AXONPUSH_ENVIRONMENT",
    "SENTRY_ENVIRONMENT",
    "APP_ENV",
    "ENV",
)


def build_dsn(api_key: str, channel_id: int | str, host: str) -> str:
    """Format an AxonPush-flavoured Sentry DSN."""
    project = coerce_channel_id(channel_id)
    scheme = "http" if host.startswith("localhost") or host.startswith("127.") else "https"
    return f"{scheme}://{api_key}@{host}/{project}"


def _detect_environment() -> Optional[str]:
    for name in _ENV_PRECEDENCE:
        val = os.getenv(name)
        if val:
            return val
    return None


def install_sentry(
    *,
    api_key: Optional[str] = None,
    channel_id: Optional[int | str] = None,
    host: Optional[str] = None,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    dsn: Optional[str] = None,
    **sentry_init_kwargs: Any,
) -> None:
    """Initialize the Sentry SDK, pointed at AxonPush.

    Args:
        api_key: AxonPush API key. Falls back to ``AXONPUSH_API_KEY``.
        channel_id: Destination channel. Either ``int`` (deprecated) or
            ``str`` UUID. Falls back to ``AXONPUSH_CHANNEL_ID``.
        host: AxonPush host. Falls back to ``AXONPUSH_HOST`` then
            ``api.axonpush.xyz``.
        environment: Deployment environment. Auto-detected from
            ``AXONPUSH_ENVIRONMENT`` / ``SENTRY_ENVIRONMENT`` / ``APP_ENV``
            / ``ENV`` when not provided.
        release: Release tag forwarded to ``sentry_sdk.init``.
        dsn: Fully-formed DSN. When set, all other AxonPush args are
            ignored — caller takes full responsibility.
        **sentry_init_kwargs: Forwarded to ``sentry_sdk.init`` verbatim.

    Raises:
        ImportError: ``sentry-sdk`` is not installed.
        ValueError: DSN can't be built and credentials weren't supplied.
    """
    try:
        import sentry_sdk
    except ImportError as exc:
        raise ImportError(
            "install_sentry requires sentry-sdk. Install it with `pip install sentry-sdk`.",
        ) from exc

    if dsn is None:
        api_key = api_key or os.getenv("AXONPUSH_API_KEY")
        if channel_id is None:
            channel_env = os.getenv("AXONPUSH_CHANNEL_ID")
            channel_id = channel_env if channel_env else None
        host = host or os.getenv("AXONPUSH_HOST") or "api.axonpush.xyz"
        if not api_key or channel_id in (None, ""):
            raise ValueError(
                "install_sentry needs api_key and channel_id (or a fully-formed dsn). "
                "Pass them as arguments or set AXONPUSH_API_KEY and AXONPUSH_CHANNEL_ID.",
            )
        assert channel_id is not None
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
