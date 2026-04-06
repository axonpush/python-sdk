"""
09 — LangChain Deep Agents Integration

Use AxonPush as a callback handler for LangChain Deep Agents to automatically
trace planning steps, subagent delegation, filesystem operations, LLM calls,
and tool usage.

Run: uv sync --extra deepagents
     uv run 09_deepagents.py

Requires OPENAI_API_KEY in .env for the actual LLM call.
"""

import sys

from config import API_KEY, TENANT_ID, BASE_URL, OPENAI_API_KEY, require_credentials

require_credentials()

from axonpush import AxonPush

try:
    from axonpush.integrations.deepagents import AxonPushDeepAgentHandler
except ImportError:
    print("Install Deep Agents integration: uv sync --extra deepagents")
    sys.exit(1)


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = client.apps.create(name="deepagents-demo")
        channel = client.channels.create(name="agent-traces", app_id=app.id)
        print(f"App: {app.name} | Channel: {channel.name}\n")

        handler = AxonPushDeepAgentHandler(
            client=client,
            channel_id=channel.id,
            agent_id="deep-agent",
            metadata={"model": "gpt-4o"},
        )
        print("AxonPushDeepAgentHandler created.")
        print(f"  Channel ID: {channel.id}")
        print(f"  Agent ID:   deep-agent\n")

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
                last_msg = result["messages"][-1]
                print(f"Result: {last_msg.content}\n")
            except Exception as e:
                print(f"Deep Agent execution error: {e}\n")
        else:
            print("OPENAI_API_KEY not set — showing setup pattern only.\n")
            print("Usage with Deep Agents:")
            print("  agent = create_deep_agent(tools=[...], system_prompt='...')")
            print("  agent.invoke({'messages': [...]}, config={'callbacks': [handler]})\n")

        events = client.events.list(channel_id=channel.id, limit=20)
        if events:
            print(f"Events published to AxonPush ({len(events)}):")
            for ev in events:
                print(f"  [{ev.event_type}] {ev.identifier}")
        else:
            print("No events published (set OPENAI_API_KEY in .env to run the agent).")

        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("\nCleaned up.")


if __name__ == "__main__":
    main()
