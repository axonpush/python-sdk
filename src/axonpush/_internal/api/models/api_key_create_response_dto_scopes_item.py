from enum import Enum


class ApiKeyCreateResponseDtoScopesItem(str, Enum):
    APPSMANAGE = "apps:manage"
    CHANNELSMANAGE = "channels:manage"
    EVENTSREAD = "events:read"
    PUBLISH = "publish"
    SUBSCRIBE = "subscribe"
    TRACESREAD = "traces:read"
    WEBHOOKSMANAGE = "webhooks:manage"

    def __str__(self) -> str:
        return str(self.value)
