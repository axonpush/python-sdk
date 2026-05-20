from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="IotCredentialsResponseDto")


@_attrs_define
class IotCredentialsResponseDto:
    """
    Attributes:
        endpoint (str):
        presigned_wss_url (str):
        expires_at (str):
        topic_prefix (str): Org-scoped MQTT topic prefix. Subscribe topics must extend this with
            `/{envSlug}/{appId}/{channelId}/{eventType}/{agentId}` (use `+` for wildcards).
        env_slug (str): Default environment slug for this org. Frontends should slot this segment between `topicPrefix`
            and the appId when subscribing without an explicit env.
        topic_template (str): Human-readable template showing every topic segment the broker will publish to. Mirrors
            the publish-side topic-builder layout.
        client_id (str):
        region (str):
        authorizer_name (str | Unset): IoT custom authorizer name to invoke. Already encoded in `presignedWssUrl` query
            string; exposed for clients that need to set it via header.
        auth_token (str | Unset): Bearer token to pass as the MQTT CONNECT username. The IoT custom authorizer reads it
            from `mqttContext.username`.
    """

    endpoint: str
    presigned_wss_url: str
    expires_at: str
    topic_prefix: str
    env_slug: str
    topic_template: str
    client_id: str
    region: str
    authorizer_name: str | Unset = UNSET
    auth_token: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        endpoint = self.endpoint

        presigned_wss_url = self.presigned_wss_url

        expires_at = self.expires_at

        topic_prefix = self.topic_prefix

        env_slug = self.env_slug

        topic_template = self.topic_template

        client_id = self.client_id

        region = self.region

        authorizer_name = self.authorizer_name

        auth_token = self.auth_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "endpoint": endpoint,
                "presignedWssUrl": presigned_wss_url,
                "expiresAt": expires_at,
                "topicPrefix": topic_prefix,
                "envSlug": env_slug,
                "topicTemplate": topic_template,
                "clientId": client_id,
                "region": region,
            }
        )
        if authorizer_name is not UNSET:
            field_dict["authorizerName"] = authorizer_name
        if auth_token is not UNSET:
            field_dict["authToken"] = auth_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        endpoint = d.pop("endpoint")

        presigned_wss_url = d.pop("presignedWssUrl")

        expires_at = d.pop("expiresAt")

        topic_prefix = d.pop("topicPrefix")

        env_slug = d.pop("envSlug")

        topic_template = d.pop("topicTemplate")

        client_id = d.pop("clientId")

        region = d.pop("region")

        authorizer_name = d.pop("authorizerName", UNSET)

        auth_token = d.pop("authToken", UNSET)

        iot_credentials_response_dto = cls(
            endpoint=endpoint,
            presigned_wss_url=presigned_wss_url,
            expires_at=expires_at,
            topic_prefix=topic_prefix,
            env_slug=env_slug,
            topic_template=topic_template,
            client_id=client_id,
            region=region,
            authorizer_name=authorizer_name,
            auth_token=auth_token,
        )

        iot_credentials_response_dto.additional_properties = d
        return iot_credentials_response_dto

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
