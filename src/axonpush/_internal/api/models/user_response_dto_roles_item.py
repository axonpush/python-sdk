from enum import Enum


class UserResponseDtoRolesItem(str, Enum):
    ADMIN = "admin"
    OWNER = "owner"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
