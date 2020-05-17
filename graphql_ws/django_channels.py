import json

from channels.generic.websockets import JsonWebsocketConsumer
from graphene_django.settings import graphene_settings

from .base import BaseConnectionContext
from .base_sync import BaseSyncSubscriptionServer


class DjangoChannelConnectionContext(BaseConnectionContext):
    def __init__(self, message, request_context=None):
        self.message = message
        self.operations = {}
        self.request_context = request_context

    def send(self, data):
        self.message.reply_channel.send({"text": json.dumps(data)})

    def close(self, reason):
        data = {"close": True, "text": reason}
        self.message.reply_channel.send(data)


class DjangoChannelSubscriptionServer(BaseSyncSubscriptionServer):
    def handle(self, message, connection_context):
        self.on_message(connection_context, message)


class GraphQLSubscriptionConsumer(JsonWebsocketConsumer):
    http_user_and_session = True
    strict_ordering = True

    def connect(self, message, **_kwargs):
        message.reply_channel.send({"accept": True})

    def receive(self, content, **_kwargs):
        """
        Called when a message is received with either text or bytes
        filled out.
        """
        self.connection_context = DjangoChannelConnectionContext(self.message)
        self.subscription_server = DjangoChannelSubscriptionServer(
            graphene_settings.SCHEMA
        )
        self.subscription_server.on_open(self.connection_context)
        self.subscription_server.handle(content, self.connection_context)
