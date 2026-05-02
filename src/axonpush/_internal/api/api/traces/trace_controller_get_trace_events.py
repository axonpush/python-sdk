from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.event_response_dto import EventResponseDto
from ...types import UNSET, Response, Unset


def _get_kwargs(
    trace_id: str,
    *,
    app_id: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["appId"] = app_id

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/traces/{trace_id}/events".format(
            trace_id=quote(str(trace_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> list[EventResponseDto] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = EventResponseDto.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[list[EventResponseDto]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    trace_id: str,
    *,
    client: AuthenticatedClient | Client,
    app_id: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> Response[list[EventResponseDto]]:
    """
    Args:
        trace_id (str):
        app_id (str | Unset):
        environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[EventResponseDto]]
    """

    kwargs = _get_kwargs(
        trace_id=trace_id,
        app_id=app_id,
        environment=environment,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    trace_id: str,
    *,
    client: AuthenticatedClient | Client,
    app_id: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> list[EventResponseDto] | None:
    """
    Args:
        trace_id (str):
        app_id (str | Unset):
        environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[EventResponseDto]
    """

    return sync_detailed(
        trace_id=trace_id,
        client=client,
        app_id=app_id,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    trace_id: str,
    *,
    client: AuthenticatedClient | Client,
    app_id: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> Response[list[EventResponseDto]]:
    """
    Args:
        trace_id (str):
        app_id (str | Unset):
        environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[EventResponseDto]]
    """

    kwargs = _get_kwargs(
        trace_id=trace_id,
        app_id=app_id,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    trace_id: str,
    *,
    client: AuthenticatedClient | Client,
    app_id: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> list[EventResponseDto] | None:
    """
    Args:
        trace_id (str):
        app_id (str | Unset):
        environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[EventResponseDto]
    """

    return (
        await asyncio_detailed(
            trace_id=trace_id,
            client=client,
            app_id=app_id,
            environment=environment,
        )
    ).parsed
