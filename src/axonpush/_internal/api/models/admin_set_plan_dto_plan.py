from enum import Enum


class AdminSetPlanDtoPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    SCALE = "scale"
    SELFHOST = "selfhost"
    TEAM = "team"

    def __str__(self) -> str:
        return str(self.value)
