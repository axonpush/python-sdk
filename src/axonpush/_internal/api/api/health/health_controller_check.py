from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.health_response_dto import HealthResponseDto
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    deep: bool | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["deep"] = deep

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/health",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HealthResponseDto | None:
    if response.status_code == 200:
        response_200 = HealthResponseDto.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HealthResponseDto]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    deep: bool | Unset = UNSET,
) -> Response[HealthResponseDto]:
    """
    Args:
        deep (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HealthResponseDto]
    """

    kwargs = _get_kwargs(
        deep=deep,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    deep: bool | Unset = UNSET,
) -> HealthResponseDto | None:
    """
    Args:
        deep (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HealthResponseDto
    """

    return sync_detailed(
        client=client,
        deep=deep,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    deep: bool | Unset = UNSET,
) -> Response[HealthResponseDto]:
    """
    Args:
        deep (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HealthResponseDto]
    """

    kwargs = _get_kwargs(
        deep=deep,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    deep: bool | Unset = UNSET,
) -> HealthResponseDto | None:
    """
    Args:
        deep (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HealthResponseDto
    """

    return (
        await asyncio_detailed(
            client=client,
            deep=deep,
        )
    ).parsed
