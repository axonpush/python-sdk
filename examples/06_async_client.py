"""
06 — Async Client

Use AsyncAxonPush with asyncio for concurrent event publishing.
Run: uv run 06_async_client.py
"""

import asyncio
import time

from config import API_KEY, TENANT_ID, BASE_URL, require_credentials

require_credentials()

from axonpush import AsyncAxonPush, EventType


async def publish_agent_events(client, channel_id: int, agent_id: str, count: int):
    for i in range(count):
        await client.events.publish(
            identifier=f"{agent_id}.step",
            payload={"step": i + 1, "agent": agent_id},
            channel_id=channel_id, agent_id=agent_id, event_type=EventType.AGENT_MESSAGE,
        )
    return agent_id, count


async def main():
    async with AsyncAxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = await client.apps.create(name="async-demo")
        channel = await client.channels.create(name="concurrent", app_id=app.id)
        print(f"App: {app.name} | Channel: {channel.name}\n")

        agents = ["agent-alpha", "agent-beta", "agent-gamma", "agent-delta", "agent-epsilon"]
        events_per_agent = 10

        print(f"Publishing {events_per_agent} events from {len(agents)} agents concurrently...")
        start = time.monotonic()

        results = await asyncio.gather(
            *[publish_agent_events(client, channel.id, agent, events_per_agent) for agent in agents]
        )

        elapsed = time.monotonic() - start
        total = sum(count for _, count in results)
        print(f"Published {total} events in {elapsed:.2f}s ({total / elapsed:.0f} events/sec)\n")

        for agent_id, count in results:
            print(f"  {agent_id}: {count} events")

        events = await client.events.list(channel_id=channel.id, limit=100)
        print(f"\nTotal events in channel: {len(events)}")

        await client.channels.delete(channel_id=channel.id)
        await client.apps.delete(app_id=app.id)
        print("\nCleaned up.")


if __name__ == "__main__":
    asyncio.run(main())
