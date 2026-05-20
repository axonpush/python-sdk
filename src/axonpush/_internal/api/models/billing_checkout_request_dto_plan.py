from enum import Enum


class BillingCheckoutRequestDtoPlan(str, Enum):
    PRO = "pro"
    TEAM = "team"

    def __str__(self) -> str:
        return str(self.value)
