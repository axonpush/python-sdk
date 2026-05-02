from enum import Enum


class SetupOrgDtoAction(str, Enum):
    CREATE = "create"
    JOIN = "join"

    def __str__(self) -> str:
        return str(self.value)
