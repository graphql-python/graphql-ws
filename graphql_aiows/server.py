from asyncio import ensure_future
from graphql.execution.executors.asyncio import AsyncioExecutor
from websockets.protocol import CONNECTING, OPEN
from inspect import isawaitable, isasyncgen
from graphql import graphql, format_error
from collections import OrderedDict
import json


GRAPHQL_WS = 'graphql-ws'
WS_PROTOCOL = GRAPHQL_WS

GQL_CONNECTION_INIT = 'connection_init'  # Client -> Server
GQL_CONNECTION_ACK = 'connection_ack'  # Server -> Client
GQL_CONNECTION_ERROR = 'connection_error'  # Server -> Client

# NOTE: This one here don't follow the standard due to connection optimization
GQL_CONNECTION_TERMINATE = 'connection_terminate'  # Client -> Server
GQL_CONNECTION_KEEP_ALIVE = 'ka'  # Server -> Client
GQL_START = 'start'  # Client -> Server
GQL_DATA = 'data'  # Server -> Client
GQL_ERROR = 'error'  # Server -> Client
GQL_COMPLETE = 'complete'  # Server -> Client
GQL_STOP = 'stop'  # Client -> Server


class ConnectionClosedException(Exception):
    pass


from aiohttp import WSMsgType


class ConnectionContext(object):
    def __init__(self, ws):
        self.ws = ws
        self.operations = {}

    def has_operation(self, op_id):
        return op_id in self.operations

    def register_operation(self, op_id, async_iterator):
        self.operations[op_id] = async_iterator

    def get_operation(self, op_id):
        return self.operations[op_id]

    def remove_operation(self, op_id):
        del self.operations[op_id]


class AioHTTPConnectionContext(ConnectionContext):
    async def receive(self):
        msg = await self.ws.receive()
        if msg.type == WSMsgType.TEXT:
            return msg.data
        elif msg.type == WSMsgType.ERROR:
            raise ConnectionClosedException()

    async def send(self, data):
        if self.closed:
            return
        await self.ws.send_str(data)

    @property
    def closed(self):
        return self.ws.closed

    async def close(self, code):
        await self.ws.close(code)


class BaseWebSocketSubscriptionServer(object):

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


class WebSocketSubscriptionServer(BaseWebSocketSubscriptionServer):

    def get_graphql_params(self, *args, **kwargs):
        params = super(WebSocketSubscriptionServer,
                       self).get_graphql_params(*args, **kwargs)
        return dict(params, executor=AsyncioExecutor())

    async def handle(self, ws):
        connection_context = AioHTTPConnectionContext(ws)
        await self.on_open(connection_context)
        while True:
            try:
                if connection_context.closed:
                    raise ConnectionClosedException()
                message = await connection_context.receive()
            except ConnectionClosedException:
                self.on_close(connection_context)
                return

            ensure_future(self.on_message(connection_context, message))

    async def on_open(self, connection_context):
        pass

    def on_close(self, connection_context):
        remove_operations = list(connection_context.operations.keys())
        # print("CONNECTION CLOSED", remove_operations)
        for op_id in remove_operations:
            self.unsubscribe(connection_context, op_id)

    async def on_connect(self, connection_context, payload):
        pass

    async def on_message(self, connection_context, message):
        try:
            parsed_message = json.loads(message)
            assert isinstance(
                parsed_message, dict), "Payload must be an object."
        except Exception as e:
            await self.send_error(connection_context, None, e)
            return

        await self.process_message(connection_context, parsed_message)

    async def on_connection_init(self, connection_context, op_id, payload):
        try:
            await self.on_connect(connection_context, payload)
            await self.send_message(connection_context, op_type=GQL_CONNECTION_ACK)

            # if self.keep_alive:
            # await self.send_message(connection_context,
            # op_type=GQL_CONNECTION_KEEP_ALIVE)
        except Exception as e:
            await self.send_error(connection_context, op_id, e, GQL_CONNECTION_ERROR)
            await connection_context.close(1011)

    async def on_connection_terminate(self, connection_context, op_id):
        await connection_context.close(1011)

    async def on_start(self, connection_context, op_id, params):

        execution_result = graphql(
            self.schema, return_promise=True, **params, allow_subscriptions=True)

        if isawaitable(execution_result):
            execution_result = await execution_result

        # print("execution result type", type(execution_result))
        if not hasattr(execution_result, '__aiter__'):
            await self.send_execution_result(connection_context, op_id, execution_result)
        else:
            iterator = await execution_result.__aiter__()
            connection_context.register_operation(op_id, iterator)
            async for single_result in iterator:
                if not connection_context.has_operation(op_id):
                    break
                await self.send_execution_result(connection_context, op_id, single_result)

    async def on_stop(self, connection_context, op_id):
        self.unsubscribe(connection_context, op_id)
