"""
07 — LangChain Integration

Use AxonPush as a callback handler for LangChain to automatically trace
chain executions, LLM calls, and tool usage.

Run: uv sync --extra langchain
     uv run 07_langchain.py

Requires OPENAI_API_KEY in .env for the actual LLM call.
"""

import sys

from config import API_KEY, TENANT_ID, BASE_URL, OPENAI_API_KEY, require_credentials

require_credentials()

from axonpush import AxonPush

try:
    from axonpush.integrations.langchain import AxonPushCallbackHandler
except ImportError:
    print("Install LangChain integration: uv sync --extra langchain")
    sys.exit(1)


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = client.apps.create(name="langchain-demo")
        channel = client.channels.create(name="llm-traces", app_id=app.id)
        print(f"App: {app.name} | Channel: {channel.name}\n")

        handler = AxonPushCallbackHandler(
            client=client, channel_id=channel.id,
            agent_id="langchain-agent",
            metadata={"framework": "langchain", "model": "gpt-4"},
        )
        print("AxonPushCallbackHandler created.")
        print(f"  Channel ID: {channel.id}")
        print(f"  Agent ID:   langchain-agent\n")

        if OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.prompts import ChatPromptTemplate

                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a helpful assistant. Be concise."),
                    ("human", "{question}"),
                ])
                chain = prompt | llm

                print("Running LangChain chain with AxonPush tracing...")
                result = chain.invoke(
                    {"question": "What is life in one sentence?"},
                    config={"callbacks": [handler]},
                )
                print(f"Result: {result.content}\n")
            except Exception as e:
                print(f"LangChain execution error: {e}\n")
        else:
            print("OPENAI_API_KEY not set — showing setup pattern only.\n")
            print("Usage with any LangChain chain:")
            print("  chain.invoke(input, config={'callbacks': [handler]})\n")

        events = client.events.list(channel_id=channel.id, limit=20)
        if events:
            print(f"Events published to AxonPush ({len(events)}):")
            for ev in events:
                print(f"  [{ev.event_type}] {ev.identifier}")
        else:
            print("No events published (set OPENAI_API_KEY in .env to run the chain).")

        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("\nCleaned up.")


if __name__ == "__main__":
    main()
