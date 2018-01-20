from channels.generic.websockets import JsonWebsocketConsumer
from .base import BaseConnectionContext
import json
from graphql.execution.executors.sync import SyncExecutor
from .base import (
    ConnectionClosedException,
    BaseConnectionContext,
    BaseSubscriptionServer
)
from .constants import (
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_ERROR
)
from django.conf import settings
from rx import Observer, Observable
from django.conf import settings
from graphene_django.settings import graphene_settings

class DjangoChannelConnectionContext(BaseConnectionContext):
    
    def __init__(self, message, request_context = None):
        self.message = message
        self.operations = {}
        self.request_context = request_context

    def send(self, data):
        self.message.reply_channel.send(data)
    
    def close(self, reason):
        data = {
            'close': True,
            'text': reason
        }
        self.message.reply_channel.send(data)

class DjangoChannelSubscriptionServer(BaseSubscriptionServer):

    def get_graphql_params(self, *args, **kwargs):
        params = super(DjangoChannelSubscriptionServer,
                       self).get_graphql_params(*args, **kwargs)
        return dict(params, executor=SyncExecutor())

    def handle(self, message, connection_context):
        self.on_message(connection_context, message)

    def send_message(self, connection_context, op_id=None, op_type=None, payload=None):
        message = {}
        if op_id is not None:
            message['id'] = op_id
        if op_type is not None:
            message['type'] = op_type
        if payload is not None:
            message['payload'] = payload

        assert message, "You need to send at least one thing"
        return connection_context.send({'text': json.dumps(message)})

    def on_open(self, connection_context):
        pass

    def on_connect(self, connection_context, payload):
        pass

    def on_connection_init(self, connection_context, op_id, payload):
        try:
            self.on_connect(connection_context, payload)
            self.send_message(connection_context, op_type=GQL_CONNECTION_ACK)

        except Exception as e:
            self.send_error(connection_context, op_id, e, GQL_CONNECTION_ERROR)
            connection_context.close(1011)

    def on_start(self, connection_context, op_id, params):
        try:
            execution_result = self.execute(
                connection_context.request_context, params)
            assert isinstance(
                execution_result, Observable), "A subscription must return an observable"
            execution_result.subscribe(SubscriptionObserver(
                connection_context,
                op_id,
                self.send_execution_result,
                self.send_error,
                self.on_close
            ))
        except Exception as e:
            self.send_error(connection_context, op_id, str(e))

    def on_close(self, connection_context):
        remove_operations = list(connection_context.operations.keys())
        for op_id in remove_operations:
            self.unsubscribe(connection_context, op_id)

    def on_stop(self, connection_context, op_id):
        self.unsubscribe(connection_context, op_id)


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
        self.connection_context = DjangoChannelConnectionContext(self.message)
        self.subscription_server = DjangoChannelSubscriptionServer(graphene_settings.SCHEMA)
        self.subscription_server.on_open(self.connection_context)
        self.subscription_server.handle(content, self.connection_context)

class SubscriptionObserver(Observer):

    def __init__(self, connection_context, op_id, send_execution_result, send_error, on_close):
        self.connection_context = connection_context
        self.op_id = op_id
        self.send_execution_result = send_execution_result
        self.send_error = send_error
        self.on_close = on_close

    def on_next(self, value):
        self.send_execution_result(self.connection_context, self.op_id, value)

    def on_completed(self):
        self.on_close(self.connection_context)

    def on_error(self, error):
        self.send_error(self.connection_context, self.op_id, error)
