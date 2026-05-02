from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.event_list_response_dto import EventListResponseDto
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    source: str | Unset = UNSET,
    payload_filter: str | Unset = UNSET,
    limit: float | Unset = UNSET,
    cursor: str | Unset = UNSET,
    until: str | Unset = UNSET,
    since: str | Unset = UNSET,
    trace_id: str | Unset = UNSET,
    agent_id: str | Unset = UNSET,
    event_type: list[str] | Unset = UNSET,
    channel_id: str | Unset = UNSET,
    app_id: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["source"] = source

    params["payloadFilter"] = payload_filter

    params["limit"] = limit

    params["cursor"] = cursor

    params["until"] = until

    params["since"] = since

    params["traceId"] = trace_id

    params["agentId"] = agent_id

    json_event_type: list[str] | Unset = UNSET
    if not isinstance(event_type, Unset):
        json_event_type = event_type

    params["eventType"] = json_event_type

    params["channelId"] = channel_id

    params["appId"] = app_id

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/events/search",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EventListResponseDto | None:
    if response.status_code == 200:
        response_200 = EventListResponseDto.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[EventListResponseDto]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    source: str | Unset = UNSET,
    payload_filter: str | Unset = UNSET,
    limit: float | Unset = UNSET,
    cursor: str | Unset = UNSET,
    until: str | Unset = UNSET,
    since: str | Unset = UNSET,
    trace_id: str | Unset = UNSET,
    agent_id: str | Unset = UNSET,
    event_type: list[str] | Unset = UNSET,
    channel_id: str | Unset = UNSET,
    app_id: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> Response[EventListResponseDto]:
    """
    Args:
        source (str | Unset):
        payload_filter (str | Unset):
        limit (float | Unset):
        cursor (str | Unset):
        until (str | Unset):
        since (str | Unset):
        trace_id (str | Unset):
        agent_id (str | Unset):
        event_type (list[str] | Unset):
        channel_id (str | Unset):
        app_id (str | Unset):
        environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EventListResponseDto]
    """

    kwargs = _get_kwargs(
        source=source,
        payload_filter=payload_filter,
        limit=limit,
        cursor=cursor,
        until=until,
        since=since,
        trace_id=trace_id,
        agent_id=agent_id,
        event_type=event_type,
        channel_id=channel_id,
        app_id=app_id,
        environment=environment,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    source: str | Unset = UNSET,
    payload_filter: str | Unset = UNSET,
    limit: float | Unset = UNSET,
    cursor: str | Unset = UNSET,
    until: str | Unset = UNSET,
    since: str | Unset = UNSET,
    trace_id: str | Unset = UNSET,
    agent_id: str | Unset = UNSET,
    event_type: list[str] | Unset = UNSET,
    channel_id: str | Unset = UNSET,
    app_id: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> EventListResponseDto | None:
    """
    Args:
        source (str | Unset):
        payload_filter (str | Unset):
        limit (float | Unset):
        cursor (str | Unset):
        until (str | Unset):
        since (str | Unset):
        trace_id (str | Unset):
        agent_id (str | Unset):
        event_type (list[str] | Unset):
        channel_id (str | Unset):
        app_id (str | Unset):
        environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EventListResponseDto
    """

    return sync_detailed(
        client=client,
        source=source,
        payload_filter=payload_filter,
        limit=limit,
        cursor=cursor,
        until=until,
        since=since,
        trace_id=trace_id,
        agent_id=agent_id,
        event_type=event_type,
        channel_id=channel_id,
        app_id=app_id,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    source: str | Unset = UNSET,
    payload_filter: str | Unset = UNSET,
    limit: float | Unset = UNSET,
    cursor: str | Unset = UNSET,
    until: str | Unset = UNSET,
    since: str | Unset = UNSET,
    trace_id: str | Unset = UNSET,
    agent_id: str | Unset = UNSET,
    event_type: list[str] | Unset = UNSET,
    channel_id: str | Unset = UNSET,
    app_id: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> Response[EventListResponseDto]:
    """
    Args:
        source (str | Unset):
        payload_filter (str | Unset):
        limit (float | Unset):
        cursor (str | Unset):
        until (str | Unset):
        since (str | Unset):
        trace_id (str | Unset):
        agent_id (str | Unset):
        event_type (list[str] | Unset):
        channel_id (str | Unset):
        app_id (str | Unset):
        environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EventListResponseDto]
    """

    kwargs = _get_kwargs(
        source=source,
        payload_filter=payload_filter,
        limit=limit,
        cursor=cursor,
        until=until,
        since=since,
        trace_id=trace_id,
        agent_id=agent_id,
        event_type=event_type,
        channel_id=channel_id,
        app_id=app_id,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    source: str | Unset = UNSET,
    payload_filter: str | Unset = UNSET,
    limit: float | Unset = UNSET,
    cursor: str | Unset = UNSET,
    until: str | Unset = UNSET,
    since: str | Unset = UNSET,
    trace_id: str | Unset = UNSET,
    agent_id: str | Unset = UNSET,
    event_type: list[str] | Unset = UNSET,
    channel_id: str | Unset = UNSET,
    app_id: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> EventListResponseDto | None:
    """
    Args:
        source (str | Unset):
        payload_filter (str | Unset):
        limit (float | Unset):
        cursor (str | Unset):
        until (str | Unset):
        since (str | Unset):
        trace_id (str | Unset):
        agent_id (str | Unset):
        event_type (list[str] | Unset):
        channel_id (str | Unset):
        app_id (str | Unset):
        environment (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EventListResponseDto
    """

    return (
        await asyncio_detailed(
            client=client,
            source=source,
            payload_filter=payload_filter,
            limit=limit,
            cursor=cursor,
            until=until,
            since=since,
            trace_id=trace_id,
            agent_id=agent_id,
            event_type=event_type,
            channel_id=channel_id,
            app_id=app_id,
            environment=environment,
        )
    ).parsed
