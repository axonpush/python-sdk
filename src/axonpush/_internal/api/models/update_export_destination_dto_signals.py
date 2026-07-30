from enum import Enum


class UpdateExportDestinationDtoSignals(str, Enum):
    LOGS = "logs"
    TRACES = "traces"

    def __str__(self) -> str:
        return str(self.value)
