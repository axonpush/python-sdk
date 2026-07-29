from enum import Enum


class ApiKeyResponseDtoPurpose(str, Enum):
    GENERAL = "general"
    INGEST = "ingest"

    def __str__(self) -> str:
        return str(self.value)
