from enum import Enum


class McpTokenResponseDtoAccess(str, Enum):
    DEBUG = "debug"
    SETUP_DEBUG = "setup_debug"

    def __str__(self) -> str:
        return str(self.value)
