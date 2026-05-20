from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.audit_log_list_response_dto import AuditLogListResponseDto
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: float | Unset = UNSET,
    limit: float | Unset = UNSET,
    action: str | Unset = UNSET,
    resource_type: str | Unset = UNSET,
    actor_id: str | Unset = UNSET,
    from_: str | Unset = UNSET,
    to: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    params["action"] = action

    params["resourceType"] = resource_type

    params["actorId"] = actor_id

    params["from"] = from_

    params["to"] = to

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/audit-logs",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuditLogListResponseDto | None:
    if response.status_code == 200:
        response_200 = AuditLogListResponseDto.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[AuditLogListResponseDto]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: float | Unset = UNSET,
    limit: float | Unset = UNSET,
    action: str | Unset = UNSET,
    resource_type: str | Unset = UNSET,
    actor_id: str | Unset = UNSET,
    from_: str | Unset = UNSET,
    to: str | Unset = UNSET,
) -> Response[AuditLogListResponseDto]:
    """
    Args:
        page (float | Unset):
        limit (float | Unset):
        action (str | Unset):
        resource_type (str | Unset):
        actor_id (str | Unset):
        from_ (str | Unset):
        to (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuditLogListResponseDto]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        action=action,
        resource_type=resource_type,
        actor_id=actor_id,
        from_=from_,
        to=to,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    page: float | Unset = UNSET,
    limit: float | Unset = UNSET,
    action: str | Unset = UNSET,
    resource_type: str | Unset = UNSET,
    actor_id: str | Unset = UNSET,
    from_: str | Unset = UNSET,
    to: str | Unset = UNSET,
) -> AuditLogListResponseDto | None:
    """
    Args:
        page (float | Unset):
        limit (float | Unset):
        action (str | Unset):
        resource_type (str | Unset):
        actor_id (str | Unset):
        from_ (str | Unset):
        to (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuditLogListResponseDto
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        action=action,
        resource_type=resource_type,
        actor_id=actor_id,
        from_=from_,
        to=to,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: float | Unset = UNSET,
    limit: float | Unset = UNSET,
    action: str | Unset = UNSET,
    resource_type: str | Unset = UNSET,
    actor_id: str | Unset = UNSET,
    from_: str | Unset = UNSET,
    to: str | Unset = UNSET,
) -> Response[AuditLogListResponseDto]:
    """
    Args:
        page (float | Unset):
        limit (float | Unset):
        action (str | Unset):
        resource_type (str | Unset):
        actor_id (str | Unset):
        from_ (str | Unset):
        to (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuditLogListResponseDto]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        action=action,
        resource_type=resource_type,
        actor_id=actor_id,
        from_=from_,
        to=to,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: float | Unset = UNSET,
    limit: float | Unset = UNSET,
    action: str | Unset = UNSET,
    resource_type: str | Unset = UNSET,
    actor_id: str | Unset = UNSET,
    from_: str | Unset = UNSET,
    to: str | Unset = UNSET,
) -> AuditLogListResponseDto | None:
    """
    Args:
        page (float | Unset):
        limit (float | Unset):
        action (str | Unset):
        resource_type (str | Unset):
        actor_id (str | Unset):
        from_ (str | Unset):
        to (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuditLogListResponseDto
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            action=action,
            resource_type=resource_type,
            actor_id=actor_id,
            from_=from_,
            to=to,
        )
    ).parsed
