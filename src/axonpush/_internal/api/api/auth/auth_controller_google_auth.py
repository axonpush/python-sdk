from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.auth_controller_google_auth_response_201 import AuthControllerGoogleAuthResponse201
from ...models.google_auth_dto import GoogleAuthDto
from ...models.google_auth_response_dto import GoogleAuthResponseDto
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: GoogleAuthDto,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/auth/google",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuthControllerGoogleAuthResponse201 | GoogleAuthResponseDto | None:
    if response.status_code == 200:
        response_200 = GoogleAuthResponseDto.from_dict(response.json())

        return response_200

    if response.status_code == 201:
        response_201 = AuthControllerGoogleAuthResponse201.from_dict(response.json())

        return response_201

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[AuthControllerGoogleAuthResponse201 | GoogleAuthResponseDto]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GoogleAuthDto,
) -> Response[AuthControllerGoogleAuthResponse201 | GoogleAuthResponseDto]:
    """
    Args:
        body (GoogleAuthDto):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthControllerGoogleAuthResponse201 | GoogleAuthResponseDto]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: GoogleAuthDto,
) -> AuthControllerGoogleAuthResponse201 | GoogleAuthResponseDto | None:
    """
    Args:
        body (GoogleAuthDto):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthControllerGoogleAuthResponse201 | GoogleAuthResponseDto
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GoogleAuthDto,
) -> Response[AuthControllerGoogleAuthResponse201 | GoogleAuthResponseDto]:
    """
    Args:
        body (GoogleAuthDto):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthControllerGoogleAuthResponse201 | GoogleAuthResponseDto]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: GoogleAuthDto,
) -> AuthControllerGoogleAuthResponse201 | GoogleAuthResponseDto | None:
    """
    Args:
        body (GoogleAuthDto):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthControllerGoogleAuthResponse201 | GoogleAuthResponseDto
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
