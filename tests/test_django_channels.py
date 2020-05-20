import mock
from django.conf import settings

settings.configure()  # noqa

from graphql_ws.django_channels import (
    DjangoChannelConnectionContext,
    DjangoChannelSubscriptionServer,
)


class TestConnectionContext:
    def test_send(self):
        msg = mock.Mock()
        connection_context = DjangoChannelConnectionContext(message=msg)
        connection_context.send("test")
        msg.reply_channel.send.assert_called_with("test")

    def test_close(self):
        msg = mock.Mock()
        connection_context = DjangoChannelConnectionContext(message=msg)
        connection_context.close(123)
        msg.reply_channel.send.assert_called_with({"close": True, "text": 123})


def test_subscription_server_smoke():
    DjangoChannelSubscriptionServer(schema=None)
