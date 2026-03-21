from axonpush.models.webhooks import WebhookEndpoint


class TestWebhooksResource:
    def test_create_endpoint(self, client, channel):
        endpoint = client.webhooks.create_endpoint(
            url="https://example.com/webhook",
            channel_id=channel.id,
            event_types=["agent.tool_call.start"],
            description="test endpoint",
        )
        assert isinstance(endpoint, WebhookEndpoint)
        assert endpoint.url == "https://example.com/webhook"
        assert endpoint.channel_id == channel.id
        client.webhooks.delete_endpoint(endpoint.id)

    def test_list_endpoints(self, client, channel):
        ep = client.webhooks.create_endpoint(
            url="https://example.com/hook-list",
            channel_id=channel.id,
        )
        endpoints = client.webhooks.list_endpoints(channel.id)
        assert isinstance(endpoints, list)
        ids = [e.id for e in endpoints]
        assert ep.id in ids
        client.webhooks.delete_endpoint(ep.id)

    def test_get_deliveries(self, client, channel):
        ep = client.webhooks.create_endpoint(
            url="https://example.com/hook-deliveries",
            channel_id=channel.id,
        )
        deliveries = client.webhooks.get_deliveries(ep.id)
        assert isinstance(deliveries, list)
        client.webhooks.delete_endpoint(ep.id)

    def test_delete_endpoint(self, client, channel):
        ep = client.webhooks.create_endpoint(
            url="https://example.com/hook-delete",
            channel_id=channel.id,
        )
        client.webhooks.delete_endpoint(ep.id)
        endpoints = client.webhooks.list_endpoints(channel.id)
        ids = [e.id for e in endpoints]
        assert ep.id not in ids
