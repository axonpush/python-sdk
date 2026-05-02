"""06 — Async client.

``AsyncAxonPush`` is the asyncio mirror of ``AxonPush``. The resource
methods are awaitable; everything else (resource layout, kwargs,
``connect_realtime``) is identical.

Run::

    uv run examples/06_async_client.py
"""

import asyncio
import time

from config import APP_ID, BASE_URL, CHANNEL_ID, ENVIRONMENT, require_credentials

require_credentials()

from axonpush import AsyncAxonPush, EventType  # noqa: E402


async def publish_agent_events(client: AsyncAxonPush, channel_id: str, agent_id: str, count: int) -> tuple[str, int]:
    for i in range(count):
        await client.events.publish(
            f"{agent_id}.step",
            {"step": i + 1, "agent": agent_id},
            channel_id,
            agent_id=agent_id,
            event_type=EventType.AGENT_MESSAGE,
        )
    return agent_id, count


async def main() -> None:
    async with AsyncAxonPush(base_url=BASE_URL, environment=ENVIRONMENT) as client:
        owns_app = APP_ID is None
        owns_channel = CHANNEL_ID is None
        app_id = APP_ID
        channel_id = CHANNEL_ID
        if owns_app:
            app = await client.apps.create(name="async-demo")
            assert app is not None
            app_id = app.id
        if owns_channel:
            assert app_id is not None
            channel = await client.channels.create("concurrent", app_id)
            assert channel is not None
            channel_id = channel.id
        assert channel_id is not None
        print(f"channel={channel_id}\n")

        agents = ["agent-alpha", "agent-beta", "agent-gamma", "agent-delta", "agent-epsilon"]
        per_agent = 10

        print(f"Publishing {per_agent} events from {len(agents)} agents concurrently...")
        start = time.monotonic()
        results = await asyncio.gather(
            *[publish_agent_events(client, channel_id, a, per_agent) for a in agents]
        )
        elapsed = time.monotonic() - start
        total = sum(c for _, c in results)
        print(f"Published {total} events in {elapsed:.2f}s ({total / elapsed:.0f} events/sec)\n")
        for agent_id, count in results:
            print(f"  {agent_id}: {count} events")

        listing = await client.events.list(channel_id, limit=100)
        if listing is not None:
            print(f"\nTotal events visible: {len(listing.data)}")

        if owns_channel:
            await client.channels.delete(channel_id)
        if owns_app and app_id is not None:
            await client.apps.delete(app_id)


if __name__ == "__main__":
    asyncio.run(main())
