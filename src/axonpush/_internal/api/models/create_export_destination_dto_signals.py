from enum import Enum


class CreateExportDestinationDtoSignals(str, Enum):
    LOGS = "logs"
    TRACES = "traces"

    def __str__(self) -> str:
        return str(self.value)
