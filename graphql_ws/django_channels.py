import json

try:
    # Channels version > 1 renamed the websockets module to websocket.
    from channels.generic.websockets import JsonWebsocketConsumer
except ImportError:
    from channels.generic.websocket import JsonWebsocketConsumer
from graphene_django.settings import graphene_settings

from .base import BaseConnectionContext
from .base_sync import BaseSyncSubscriptionServer


class DjangoChannelConnectionContext(BaseConnectionContext):
    def __init__(self, message):
        super(DjangoChannelConnectionContext, self).__init__(
            message.reply_channel,
            request_context={"user": message.user, "session": message.http_session},
        )

    def send(self, data):
        self.ws.send({"text": json.dumps(data)})

    def close(self, reason):
        data = {"close": True, "text": reason}
        self.ws.send(data)


class DjangoChannelSubscriptionServer(BaseSyncSubscriptionServer):
    def handle(self, message, connection_context):
        self.on_message(connection_context, message)


subscription_server = DjangoChannelSubscriptionServer(graphene_settings.SCHEMA)


class GraphQLSubscriptionConsumer(JsonWebsocketConsumer):
    http_user_and_session = True
    strict_ordering = True

    def connect(self, message, **kwargs):
        message.reply_channel.send({"accept": True})

    def receive(self, content, **kwargs):
        """
        Called when a message is received with either text or bytes
        filled out.
        """
        context = DjangoChannelConnectionContext(self.message)
        subscription_server.on_open(context)
        subscription_server.handle(content, context)
