from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.success_response_dto import SuccessResponseDto
from ...types import Response


def _get_kwargs(
    id: str,
    invitation_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/organizations/{id}/invitations/{invitation_id}".format(
            id=quote(str(id), safe=""),
            invitation_id=quote(str(invitation_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> SuccessResponseDto | None:
    if response.status_code == 200:
        response_200 = SuccessResponseDto.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[SuccessResponseDto]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    invitation_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[SuccessResponseDto]:
    """
    Args:
        id (str):
        invitation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SuccessResponseDto]
    """

    kwargs = _get_kwargs(
        id=id,
        invitation_id=invitation_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    invitation_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> SuccessResponseDto | None:
    """
    Args:
        id (str):
        invitation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SuccessResponseDto
    """

    return sync_detailed(
        id=id,
        invitation_id=invitation_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: str,
    invitation_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[SuccessResponseDto]:
    """
    Args:
        id (str):
        invitation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SuccessResponseDto]
    """

    kwargs = _get_kwargs(
        id=id,
        invitation_id=invitation_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    invitation_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> SuccessResponseDto | None:
    """
    Args:
        id (str):
        invitation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SuccessResponseDto
    """

    return (
        await asyncio_detailed(
            id=id,
            invitation_id=invitation_id,
            client=client,
        )
    ).parsed
