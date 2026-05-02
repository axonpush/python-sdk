"""09 — LangChain Deep Agents integration.

``AxonPushDeepAgentHandler`` traces planning steps, sub-agent delegation,
filesystem ops, LLM calls, and tool calls produced by ``deepagents``.

Run::

    uv sync --extra deepagents
    uv run examples/09_deepagents.py

Set ``OPENAI_API_KEY`` to actually run the agent; otherwise the script
just prints the wiring pattern.
"""

import sys

from config import APP_ID, BASE_URL, CHANNEL_ID, ENVIRONMENT, OPENAI_API_KEY, require_credentials

require_credentials()

from axonpush import AxonPush  # noqa: E402

try:
    from axonpush.integrations.deepagents import AxonPushDeepAgentHandler
except ImportError:
    print("Install Deep Agents integration: uv sync --extra deepagents")
    sys.exit(1)


def main() -> None:
    with AxonPush(base_url=BASE_URL, environment=ENVIRONMENT) as client:
        owns_app = APP_ID is None
        owns_channel = CHANNEL_ID is None
        app_id = APP_ID
        channel_id = CHANNEL_ID
        if owns_app:
            app = client.apps.create(name="deepagents-demo")
            assert app is not None
            app_id = app.id
        if owns_channel:
            assert app_id is not None
            channel = client.channels.create("agent-traces", app_id)
            assert channel is not None
            channel_id = channel.id
        assert channel_id is not None

        handler = AxonPushDeepAgentHandler(
            client, channel_id,
            agent_id="deep-agent",
            metadata={"model": "gpt-4o"},
        )
        print(f"Handler ready (channel={channel_id})\n")

        if OPENAI_API_KEY:
            try:
                from deepagents import create_deep_agent

                agent = create_deep_agent(
                    tools=[],
                    system_prompt="You are a helpful assistant. Be concise.",
                )
                print("Running Deep Agent with AxonPush tracing...")
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": "What is 2 + 2?"}]},
                    config={"callbacks": [handler]},
                )
                print(f"Result: {result['messages'][-1].content}\n")
            except Exception as exc:
                print(f"Deep Agent execution error: {exc}\n")
        else:
            print("OPENAI_API_KEY not set — pattern only:")
            print("  agent = create_deep_agent(tools=[...], system_prompt='...')")
            print("  agent.invoke({'messages': [...]}, config={'callbacks': [handler]})\n")

        listing = client.events.list(channel_id, limit=20)
        if listing is not None and listing.data:
            print(f"Events published ({len(listing.data)}):")
            for ev in listing.data:
                print(f"  [{ev.event_type}] {ev.identifier}")
        else:
            print("No events published (set OPENAI_API_KEY to run the agent).")

        if owns_channel:
            client.channels.delete(channel_id)
        if owns_app and app_id is not None:
            client.apps.delete(app_id)


if __name__ == "__main__":
    main()
