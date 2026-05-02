from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.otlp_controller_ingest_traces_response_201 import (
    OtlpControllerIngestTracesResponse201,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    x_axonpush_channel: str,
    idempotency_key: str | Unset = UNSET,
    x_axonpush_environment: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["X-Axonpush-Channel"] = x_axonpush_channel

    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    if not isinstance(x_axonpush_environment, Unset):
        headers["X-Axonpush-Environment"] = x_axonpush_environment

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/traces",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | OtlpControllerIngestTracesResponse201 | None:
    if response.status_code == 200:
        response_200 = cast(Any, None)
        return response_200

    if response.status_code == 201:
        response_201 = OtlpControllerIngestTracesResponse201.from_dict(response.json())

        return response_201

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | OtlpControllerIngestTracesResponse201]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_axonpush_channel: str,
    idempotency_key: str | Unset = UNSET,
    x_axonpush_environment: str | Unset = UNSET,
) -> Response[Any | OtlpControllerIngestTracesResponse201]:
    """OTLP/HTTP traces ingest (protobuf or JSON)

    Args:
        x_axonpush_channel (str):
        idempotency_key (str | Unset):
        x_axonpush_environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | OtlpControllerIngestTracesResponse201]
    """

    kwargs = _get_kwargs(
        x_axonpush_channel=x_axonpush_channel,
        idempotency_key=idempotency_key,
        x_axonpush_environment=x_axonpush_environment,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    x_axonpush_channel: str,
    idempotency_key: str | Unset = UNSET,
    x_axonpush_environment: str | Unset = UNSET,
) -> Any | OtlpControllerIngestTracesResponse201 | None:
    """OTLP/HTTP traces ingest (protobuf or JSON)

    Args:
        x_axonpush_channel (str):
        idempotency_key (str | Unset):
        x_axonpush_environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | OtlpControllerIngestTracesResponse201
    """

    return sync_detailed(
        client=client,
        x_axonpush_channel=x_axonpush_channel,
        idempotency_key=idempotency_key,
        x_axonpush_environment=x_axonpush_environment,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_axonpush_channel: str,
    idempotency_key: str | Unset = UNSET,
    x_axonpush_environment: str | Unset = UNSET,
) -> Response[Any | OtlpControllerIngestTracesResponse201]:
    """OTLP/HTTP traces ingest (protobuf or JSON)

    Args:
        x_axonpush_channel (str):
        idempotency_key (str | Unset):
        x_axonpush_environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | OtlpControllerIngestTracesResponse201]
    """

    kwargs = _get_kwargs(
        x_axonpush_channel=x_axonpush_channel,
        idempotency_key=idempotency_key,
        x_axonpush_environment=x_axonpush_environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    x_axonpush_channel: str,
    idempotency_key: str | Unset = UNSET,
    x_axonpush_environment: str | Unset = UNSET,
) -> Any | OtlpControllerIngestTracesResponse201 | None:
    """OTLP/HTTP traces ingest (protobuf or JSON)

    Args:
        x_axonpush_channel (str):
        idempotency_key (str | Unset):
        x_axonpush_environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | OtlpControllerIngestTracesResponse201
    """

    return (
        await asyncio_detailed(
            client=client,
            x_axonpush_channel=x_axonpush_channel,
            idempotency_key=idempotency_key,
            x_axonpush_environment=x_axonpush_environment,
        )
    ).parsed
