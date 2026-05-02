from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.release_artifact_response_dto import ReleaseArtifactResponseDto
from ...types import Response


def _get_kwargs(
    version: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/releases/{version}/artifacts".format(
            version=quote(str(version), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ReleaseArtifactResponseDto | None:
    if response.status_code == 201:
        response_201 = ReleaseArtifactResponseDto.from_dict(response.json())

        return response_201

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ReleaseArtifactResponseDto]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    version: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ReleaseArtifactResponseDto]:
    """
    Args:
        version (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ReleaseArtifactResponseDto]
    """

    kwargs = _get_kwargs(
        version=version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    version: str,
    *,
    client: AuthenticatedClient | Client,
) -> ReleaseArtifactResponseDto | None:
    """
    Args:
        version (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ReleaseArtifactResponseDto
    """

    return sync_detailed(
        version=version,
        client=client,
    ).parsed


async def asyncio_detailed(
    version: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ReleaseArtifactResponseDto]:
    """
    Args:
        version (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ReleaseArtifactResponseDto]
    """

    kwargs = _get_kwargs(
        version=version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    version: str,
    *,
    client: AuthenticatedClient | Client,
) -> ReleaseArtifactResponseDto | None:
    """
    Args:
        version (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ReleaseArtifactResponseDto
    """

    return (
        await asyncio_detailed(
            version=version,
            client=client,
        )
    ).parsed
