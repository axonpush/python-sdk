# Integrations are lazily imported to avoid requiring optional dependencies.
# Import them directly:
#
# Agent frameworks (sync):
#   from axonpush.integrations.langchain import AxonPushCallbackHandler
#   from axonpush.integrations.openai_agents import AxonPushRunHooks
#   from axonpush.integrations.anthropic import AxonPushAnthropicTracer
#   from axonpush.integrations.crewai import AxonPushCrewCallbacks
#   from axonpush.integrations.deepagents import AxonPushDeepAgentHandler
#
# Agent frameworks (async — non-blocking fire-and-forget):
#   from axonpush.integrations.langchain import AsyncAxonPushCallbackHandler
#   from axonpush.integrations.deepagents import AsyncAxonPushDeepAgentHandler
#
# Factory functions (auto-detect sync vs async client):
#   from axonpush.integrations.langchain import get_langchain_handler
#   from axonpush.integrations.deepagents import get_deepagent_handler
#
# Publishers (for custom integrations):
#   from axonpush.integrations._publisher import AsyncBackgroundPublisher
#   from axonpush.integrations._publisher import RqPublisher              # extra: rq
#
# Logging (no extra deps required for the first two):
#   from axonpush.integrations.print_capture import setup_print_capture
#   from axonpush.integrations.logging_handler import AxonPushLoggingHandler
#   from axonpush.integrations.loguru import create_axonpush_loguru_sink         # extra: loguru
#   from axonpush.integrations.structlog import axonpush_structlog_processor     # extra: structlog
#
# OpenTelemetry tracing (extra: otel):
#   from axonpush.integrations.otel import AxonPushSpanExporter
