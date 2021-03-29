from __future__ import unicode_literals

import json

import django
import mock
from channels import Channel
from channels.test import ChannelTestCase
from django.conf import settings
from django.core.management import call_command

settings.configure(
    CHANNEL_LAYERS={
        "default": {
            "BACKEND": "asgiref.inmemory.ChannelLayer",
            "ROUTING": "tests.django_routing.channel_routing",
        },
    },
    INSTALLED_APPS=[
        "django.contrib.sessions",
        "django.contrib.contenttypes",
        "django.contrib.auth",
    ],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)
django.setup()

from graphql_ws.constants import GQL_CONNECTION_ACK, GQL_CONNECTION_INIT  # noqa: E402
from graphql_ws.django_channels import (  # noqa: E402
    DjangoChannelConnectionContext,
    DjangoChannelSubscriptionServer,
    GraphQLSubscriptionConsumer,
)


class TestConnectionContext:
    def test_send(self):
        msg = mock.Mock()
        connection_context = DjangoChannelConnectionContext(message=msg)
        connection_context.send("test")
        msg.reply_channel.send.assert_called_with({"text": '"test"'})

    def test_close(self):
        msg = mock.Mock()
        connection_context = DjangoChannelConnectionContext(message=msg)
        connection_context.close(123)
        msg.reply_channel.send.assert_called_with({"close": True, "text": 123})


def test_subscription_server_smoke():
    DjangoChannelSubscriptionServer(schema=None)


class TestConsumer(ChannelTestCase):
    def test_connect(self):
        call_command("migrate")
        Channel("websocket.receive").send(
            {
                "path": "/graphql",
                "order": 0,
                "reply_channel": "websocket.receive",
                "text": json.dumps({"type": GQL_CONNECTION_INIT, "id": 1}),
            }
        )
        message = self.get_next_message("websocket.receive", require=True)
        GraphQLSubscriptionConsumer(message)
        result = self.get_next_message("websocket.receive", require=True)
        result_content = json.loads(result.content["text"])
        assert result_content == {"type": GQL_CONNECTION_ACK}
