from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.webhook_ingest_response_dto import WebhookIngestResponseDto
from ...types import UNSET, Response


def _get_kwargs(
    endpoint_id: str,
    *,
    x_webhook_signature: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["X-Webhook-Signature"] = x_webhook_signature

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/webhooks/ingest/{endpoint_id}".format(
            endpoint_id=quote(str(endpoint_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> WebhookIngestResponseDto | None:
    if response.status_code == 201:
        response_201 = WebhookIngestResponseDto.from_dict(response.json())

        return response_201

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[WebhookIngestResponseDto]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_webhook_signature: str,
) -> Response[WebhookIngestResponseDto]:
    """
    Args:
        endpoint_id (str):
        x_webhook_signature (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[WebhookIngestResponseDto]
    """

    kwargs = _get_kwargs(
        endpoint_id=endpoint_id,
        x_webhook_signature=x_webhook_signature,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_webhook_signature: str,
) -> WebhookIngestResponseDto | None:
    """
    Args:
        endpoint_id (str):
        x_webhook_signature (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        WebhookIngestResponseDto
    """

    return sync_detailed(
        endpoint_id=endpoint_id,
        client=client,
        x_webhook_signature=x_webhook_signature,
    ).parsed


async def asyncio_detailed(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_webhook_signature: str,
) -> Response[WebhookIngestResponseDto]:
    """
    Args:
        endpoint_id (str):
        x_webhook_signature (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[WebhookIngestResponseDto]
    """

    kwargs = _get_kwargs(
        endpoint_id=endpoint_id,
        x_webhook_signature=x_webhook_signature,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_webhook_signature: str,
) -> WebhookIngestResponseDto | None:
    """
    Args:
        endpoint_id (str):
        x_webhook_signature (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        WebhookIngestResponseDto
    """

    return (
        await asyncio_detailed(
            endpoint_id=endpoint_id,
            client=client,
            x_webhook_signature=x_webhook_signature,
        )
    ).parsed
