"""Parity guard: every sync resource has the same public method set as its
async sibling. If they ever drift, users who switch sync to async will hit
mysterious AttributeErrors.
"""

from __future__ import annotations

from axonpush.resources.api_keys import ApiKeys, AsyncApiKeys
from axonpush.resources.apps import Apps, AsyncApps
from axonpush.resources.channels import AsyncChannels, Channels
from axonpush.resources.environments import AsyncEnvironments, Environments
from axonpush.resources.events import AsyncEvents, Events
from axonpush.resources.organizations import AsyncOrganizations, Organizations
from axonpush.resources.traces import AsyncTraces, Traces
from axonpush.resources.webhooks import AsyncWebhooks, Webhooks


def _public_methods(cls: type) -> set[str]:
    return {name for name, attr in vars(cls).items() if not name.startswith("_") and callable(attr)}


_PAIRS: list[tuple[type, type]] = [
    (Events, AsyncEvents),
    (Channels, AsyncChannels),
    (Apps, AsyncApps),
    (Environments, AsyncEnvironments),
    (Webhooks, AsyncWebhooks),
    (Traces, AsyncTraces),
    (ApiKeys, AsyncApiKeys),
    (Organizations, AsyncOrganizations),
]


def test_every_sync_class_has_async_sibling() -> None:
    for sync_cls, async_cls in _PAIRS:
        sync_methods = _public_methods(sync_cls)
        async_methods = _public_methods(async_cls)
        assert sync_methods == async_methods, (
            f"{sync_cls.__name__} <-> {async_cls.__name__} method-set drift: "
            f"only on sync = {sync_methods - async_methods}, "
            f"only on async = {async_methods - sync_methods}"
        )
