from enum import Enum


class BillingCheckoutRequestDtoCadence(str, Enum):
    ANNUAL = "annual"
    MONTHLY = "monthly"

    def __str__(self) -> str:
        return str(self.value)
