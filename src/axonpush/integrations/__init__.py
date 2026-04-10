# Integrations are lazily imported to avoid requiring optional dependencies.
# Import them directly:
#
# Agent frameworks:
#   from axonpush.integrations.langchain import AxonPushCallbackHandler
#   from axonpush.integrations.openai_agents import AxonPushRunHooks
#   from axonpush.integrations.anthropic import AxonPushAnthropicTracer
#   from axonpush.integrations.crewai import AxonPushCrewCallbacks
#   from axonpush.integrations.deepagents import AxonPushDeepAgentHandler
#
# Logging (no extra deps required for the first two):
#   from axonpush.integrations.print_capture import setup_print_capture
#   from axonpush.integrations.logging_handler import AxonPushLoggingHandler
#   from axonpush.integrations.loguru import create_axonpush_loguru_sink         # extra: loguru
#   from axonpush.integrations.structlog import axonpush_structlog_processor     # extra: structlog
#
# OpenTelemetry tracing (extra: otel):
#   from axonpush.integrations.otel import AxonPushSpanExporter
