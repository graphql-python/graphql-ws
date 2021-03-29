from graphql.execution.executors.sync import SyncExecutor
from rx import Observable, Observer

from .base import BaseSubscriptionServer
from .constants import GQL_COMPLETE, GQL_CONNECTION_ACK, GQL_CONNECTION_ERROR


class BaseSyncSubscriptionServer(BaseSubscriptionServer):
    graphql_executor = SyncExecutor

    def on_operation_complete(self, connection_context, op_id):
        pass

    def handle(self, ws, request_context=None):
        raise NotImplementedError("handle method not implemented")

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
        # Attempt to unsubscribe first in case we already have a subscription
        # with this id.
        connection_context.unsubscribe(op_id)
        try:
            execution_result = self.execute(params)
            assert isinstance(
                execution_result, Observable
            ), "A subscription must return an observable"
            disposable = execution_result.subscribe(
                SubscriptionObserver(
                    connection_context,
                    op_id,
                    self.send_execution_result,
                    self.send_error,
                    self.send_message,
                )
            )
            connection_context.register_operation(op_id, disposable)

        except Exception as e:
            self.send_error(connection_context, op_id, e)
            self.send_message(connection_context, op_id, GQL_COMPLETE)


class SubscriptionObserver(Observer):
    def __init__(
        self, connection_context, op_id, send_execution_result, send_error, send_message
    ):
        self.connection_context = connection_context
        self.op_id = op_id
        self.send_execution_result = send_execution_result
        self.send_error = send_error
        self.send_message = send_message

    def on_next(self, value):
        if isinstance(value, Exception):
            send_method = self.send_error
        else:
            send_method = self.send_execution_result
        send_method(self.connection_context, self.op_id, value)

    def on_completed(self):
        self.send_message(self.connection_context, self.op_id, GQL_COMPLETE)
        self.connection_context.remove_operation(self.op_id)

    def on_error(self, error):
        self.send_error(self.connection_context, self.op_id, error)
        self.on_completed()
