"""AxonPush integrations: optional helpers for popular Python tooling.

Each module is lazily imported — none of these are required at SDK
import time, and importing this package alone has zero side effects
besides loading internal helpers.

Agent frameworks (sync)
-----------------------
* ``axonpush.integrations.langchain`` — :class:`AxonPushCallbackHandler`
* ``axonpush.integrations.openai_agents`` — :class:`AxonPushRunHooks`
* ``axonpush.integrations.anthropic`` — :class:`AxonPushAnthropicTracer`
* ``axonpush.integrations.crewai`` — :class:`AxonPushCrewCallbacks`
* ``axonpush.integrations.deepagents`` — :class:`AxonPushDeepAgentHandler`

Agent frameworks (async)
------------------------
* ``axonpush.integrations.langchain.AsyncAxonPushCallbackHandler``
* ``axonpush.integrations.deepagents.AsyncAxonPushDeepAgentHandler``

Logging (no extra deps for the first two)
-----------------------------------------
* ``axonpush.integrations.print_capture.setup_print_capture``
* ``axonpush.integrations.logging_handler.AxonPushLoggingHandler``
* ``axonpush.integrations.loguru.create_axonpush_loguru_sink``  (extra: ``loguru``)
* ``axonpush.integrations.structlog.axonpush_structlog_processor``  (extra: ``structlog``)

OpenTelemetry tracing
---------------------
* ``axonpush.integrations.otel.AxonPushSpanExporter``  (extra: ``otel``)

Sentry compat
-------------
* ``axonpush.integrations.sentry.install_sentry``  (extra: ``sentry-sdk``)

Publishers (for custom integrations)
------------------------------------
* ``axonpush.integrations._publisher.BackgroundPublisher``
* ``axonpush.integrations._publisher.AsyncBackgroundPublisher``
* ``axonpush.integrations._publisher.RqPublisher``  (extra: ``rq``)
"""
