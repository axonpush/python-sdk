from enum import Enum


class AdminSetStatusDtoSubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    TRIALING = "trialing"
    TRIAL_EXPIRED = "trial_expired"

    def __str__(self) -> str:
        return str(self.value)
