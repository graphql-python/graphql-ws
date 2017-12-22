import json
from collections import OrderedDict

from graphql import graphql, format_error
from graphql.execution import ExecutionResult

from .constants import (
    GQL_CONNECTION_INIT,
    GQL_CONNECTION_TERMINATE,
    GQL_START,
    GQL_STOP,
    GQL_COMPLETE,
    GQL_ERROR,
    GQL_CONNECTION_ERROR,
    GQL_DATA
)


class ConnectionClosedException(Exception):
    pass


class BaseConnectionContext(object):
    def __init__(self, ws, request_context=None):
        self.ws = ws
        self.operations = {}
        self.request_context = request_context

    def has_operation(self, op_id):
        return op_id in self.operations

    def register_operation(self, op_id, async_iterator):
        self.operations[op_id] = async_iterator

    def get_operation(self, op_id):
        return self.operations[op_id]

    def remove_operation(self, op_id):
        del self.operations[op_id]

    def receive(self):
        raise NotImplementedError("receive method not implemented")

    def send(self, data):
        raise NotImplementedError("send method not implemented")

    @property
    def closed(self):
        raise NotImplementedError("closed property not implemented")

    def close(self, code):
        raise NotImplementedError("close method not implemented")


class BaseSubscriptionServer(object):

    def __init__(self, schema, keep_alive=True):
        self.schema = schema
        self.keep_alive = keep_alive

    def get_graphql_params(self, connection_context, payload):
        return {
            'request_string': payload.get('query'),
            'variable_values': payload.get('variables'),
            'operation_name': payload.get('operationName'),
            'context_value': payload.get('context'),
        }

    def build_message(self, id, op_type, payload):
        message = {}
        if id is not None:
            message['id'] = id
        if op_type is not None:
            message['type'] = op_type
        if payload is not None:
            message['payload'] = payload
        return message

    def process_message(self, connection_context, parsed_message):
        op_id = parsed_message.get('id')
        op_type = parsed_message.get('type')
        payload = parsed_message.get('payload')

        if op_type == GQL_CONNECTION_INIT:
            return self.on_connection_init(connection_context, op_id, payload)

        elif op_type == GQL_CONNECTION_TERMINATE:
            return self.on_connection_terminate(connection_context, op_id)

        elif op_type == GQL_START:
            assert isinstance(payload, dict), "The payload must be a dict"

            params = self.get_graphql_params(connection_context, payload)
            if not isinstance(params, dict):
                error = Exception(
                    "Invalid params returned from get_graphql_params! return values must be a dict.")
                return self.send_error(connection_context, op_id, error)

            # If we already have a subscription with this id, unsubscribe from
            # it first
            if connection_context.has_operation(op_id):
                self.unsubscribe(connection_context, op_id)

            return self.on_start(connection_context, op_id, params)

        elif op_type == GQL_STOP:
            return self.on_stop(connection_context, op_id)

        else:
            return self.send_error(connection_context, op_id,
                                   Exception('Invalid message type: {}.'.format(op_type)))

    def send_execution_result(self, connection_context, op_id, execution_result):
        result = self.execution_result_to_dict(execution_result)
        return self.send_message(connection_context, op_id, GQL_DATA, result)

    def execution_result_to_dict(self, execution_result):
        result = OrderedDict()
        if execution_result.data:
            result['data'] = execution_result.data
        if execution_result.errors:
            result['errors'] = [format_error(error)
                                for error in execution_result.errors]
        return result

    def send_message(self, connection_context, op_id=None, op_type=None, payload=None):
        message = {}
        if op_id is not None:
            message['id'] = op_id
        if op_type is not None:
            message['type'] = op_type
        if payload is not None:
            message['payload'] = payload

        assert message, "You need to send at least one thing"
        json_message = json.dumps(message)
        return connection_context.send(json_message)

    def send_error(self, connection_context, op_id, error, error_type=None):
        if error_type is None:
            error_type = GQL_ERROR

        assert error_type in [GQL_CONNECTION_ERROR, GQL_ERROR], (
            'error_type should be one of the allowed error messages'
            ' GQL_CONNECTION_ERROR or GQL_ERROR'
        )

        error_payload = {
            'message': str(error)
        }

        return self.send_message(
            connection_context,
            op_id,
            error_type,
            error_payload
        )

    def unsubscribe(self, connection_context, op_id):
        if connection_context.has_operation(op_id):
            # Close async iterator
            connection_context.get_operation(op_id).dispose()
            # Close operation
            connection_context.remove_operation(op_id)
        self.on_operation_complete(connection_context, op_id)

    def on_operation_complete(self, connection_context, op_id):
        pass

    def on_connection_terminate(self, connection_context, op_id):
        return connection_context.close(1011)

    def execute(self, request_context, params):
        return graphql(
            self.schema, **dict(params, allow_subscriptions=True))

    def handle(self, ws, request_context=None):
        raise NotImplementedError("handle method not implemented")

    def on_message(self, connection_context, message):
        try:
            if not isinstance(message, dict):
                parsed_message = json.loads(message)
                assert isinstance(
                    parsed_message, dict), "Payload must be an object."
            else:
                parsed_message = message
        except Exception as e:
            return self.send_error(connection_context, None, e)

        return self.process_message(connection_context, parsed_message)

    def on_open(self, connection_context):
        raise NotImplementedError("on_open method not implemented")

    def on_connect(self, connection_context, payload):
        raise NotImplementedError("on_connect method not implemented")

    def on_close(self, connection_context):
        raise NotImplementedError("on_close method not implemented")

    def on_connection_init(self, connection_context, op_id, payload):
        raise NotImplementedError("on_connection_init method not implemented")

    def on_stop(self, connection_context, op_id):
        raise NotImplementedError("on_stop method not implemented")

    def on_start(self, connection_context, op_id, params):
        raise NotImplementedError("on_start method not implemented")
