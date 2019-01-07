from inspect import isawaitable
from enum import Enum

from asyncio import ensure_future, wait, shield
from graphql.execution.executors.asyncio import AsyncioExecutor

from .base import (
    ConnectionClosedException,
    BaseConnectionContext,
    BaseSubscriptionServer
    )
from .observable_aiter import setup_observable_extension

from .constants import (
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_ERROR,
    GQL_COMPLETE
)

setup_observable_extension()


class WebSocketState(Enum):
    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTED = 2


class AsgiConnectionContext(BaseConnectionContext):
    def __init__(self, scope, receive, send, request_context=None):
        assert scope["type"] == "websocket"
        self._receive = receive
        self._send = send
        self.client_state = WebSocketState.CONNECTING
        self.application_state = WebSocketState.CONNECTING
        super().__init__(ws=self, request_context=request_context)

    async def receive(self):
        assert self.client_state == WebSocketState.CONNECTED
        message = await self._receive()
        if message["type"] == "websocket.disconnect":
            self.client_state = WebSocketState.DISCONNECTED
            raise ConnectionClosedException()
        else:
            return message["text"]

    async def send(self, data):
        if self.closed:
            return
        await self._send({"type": "websocket.send", "text": data})

    async def close(self, code):
        if self.application_state == WebSocketState.DISCONNECTED:
            raise RuntimeError('disconnected')
        self.application_state = WebSocketState.DISCONNECTED
        await self._send({"type": "websocket.close", "code": code})

    @property
    def closed(self):
        return (self.application_state == WebSocketState.DISCONNECTED or
                self.client_state == WebSocketState.DISCONNECTED)

    async def accept(self):
        if self.client_state == WebSocketState.CONNECTING:
            message = await self._receive()
            message_type = message["type"]
            assert message_type == "websocket.connect"
            self.client_state = WebSocketState.CONNECTED

        assert self.application_state == WebSocketState.CONNECTING
        self.application_state = WebSocketState.CONNECTED
        await self._send({
            "type": "websocket.accept",
            "subprotocol": "graphql-ws",
            })        


class AsgiSubscriptionServer(BaseSubscriptionServer):
    def __init__(self, schema, keep_alive=True, loop=None):
        self.loop = loop
        super().__init__(schema, keep_alive)

    def get_graphql_params(self, connection_context, payload):
        params = super().get_graphql_params(connection_context, payload)

        if connection_context.request_context:
            if params['context_value']:
                context = params['context_value'].copy()
            else:
                context = {}
            if isinstance(context, dict):
                context.setdefault(
                    'request', connection_context.request_context
                )
            params['context_value'] = context

        return dict(params, return_promise=True, executor=AsyncioExecutor(loop=self.loop))

    async def _handle(self, scope, receive, send, request_context):
        connection_context = AsgiConnectionContext(
            scope, receive, send, request_context)
        print("HANDLE")
        await connection_context.accept()
        await self.on_open(connection_context)
        pending = set()
        while True:
            try:
                if connection_context.closed:
                    raise ConnectionClosedException()
                message = await connection_context.receive()
            except ConnectionClosedException:
                break
            finally:
                if pending:
                    (_, pending) = await wait(pending, timeout=0, loop=self.loop)

            task = ensure_future(
                self.on_message(connection_context, message), loop=self.loop)
            pending.add(task)

        self.on_close(connection_context)
        for task in pending:
            task.cancel()

    async def handle(self, scope, receive, send, request_context=None):
        await shield(self._handle(scope, receive, send, request_context), loop=self.loop)

    async def on_open(self, connection_context):
        pass

    def on_close(self, connection_context):
        remove_operations = list(connection_context.operations.keys())
        for op_id in remove_operations:
            self.unsubscribe(connection_context, op_id)

    async def on_connect(self, connection_context, payload):
        pass

    async def on_connection_init(self, connection_context, op_id, payload):
        try:
            await self.on_connect(connection_context, payload)
            await self.send_message(connection_context, op_type=GQL_CONNECTION_ACK)
        except Exception as e:
            await self.send_error(connection_context, op_id, e, GQL_CONNECTION_ERROR)
            await connection_context.close(1011)

    async def on_start(self, connection_context, op_id, params):
        execution_result = self.execute(
            connection_context.request_context, params)

        if isawaitable(execution_result):
            execution_result = await execution_result

        if not hasattr(execution_result, '__aiter__'):
            await self.send_execution_result(connection_context, op_id, execution_result)
        else:
            iterator = await execution_result.__aiter__()
            connection_context.register_operation(op_id, iterator)
            async for single_result in iterator:
                if not connection_context.has_operation(op_id):
                    break
                await self.send_execution_result(connection_context, op_id, single_result)
            await self.send_message(connection_context, op_id, GQL_COMPLETE)

    async def on_stop(self, connection_context, op_id):
        self.unsubscribe(connection_context, op_id)
