from enum import Enum


class WebhookDeliveryResponseDtoStatus(str, Enum):
    FAILED = "failed"
    PENDING = "pending"
    RETRYING = "retrying"
    SUCCESS = "success"

    def __str__(self) -> str:
        return str(self.value)
