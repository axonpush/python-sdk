from enum import Enum


class CreateEventDtoEventType(str, Enum):
    AGENT_END = "agent.end"
    AGENT_ERROR = "agent.error"
    AGENT_HANDOFF = "agent.handoff"
    AGENT_LLM_TOKEN = "agent.llm.token"
    AGENT_LOG = "agent.log"
    AGENT_MESSAGE = "agent.message"
    AGENT_START = "agent.start"
    AGENT_TOOL_CALL_END = "agent.tool_call.end"
    AGENT_TOOL_CALL_START = "agent.tool_call.start"
    APP_LOG = "app.log"
    APP_SPAN = "app.span"
    CUSTOM = "custom"

    def __str__(self) -> str:
        return str(self.value)
