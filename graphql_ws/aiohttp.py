from asyncio import ensure_future, shield, wait

from aiohttp import WSMsgType
from graphql import subscribe
from graphql.language import parse

from .base import (
    BaseConnectionContext,
    BaseSubscriptionServer,
    ConnectionClosedException,
)
from .constants import GQL_COMPLETE, GQL_CONNECTION_ACK, GQL_CONNECTION_ERROR


class AiohttpConnectionContext(BaseConnectionContext):
    async def receive(self):
        msg = await self.ws.receive()
        if msg.type == WSMsgType.TEXT:
            return msg.data
        elif msg.type == WSMsgType.ERROR:
            raise ConnectionClosedException()
        elif msg.type == WSMsgType.CLOSING:
            raise ConnectionClosedException()
        elif msg.type == WSMsgType.CLOSED:
            raise ConnectionClosedException()

    async def send(self, data):
        if self.closed:
            return
        await self.ws.send_str(data)

    @property
    def closed(self):
        return self.ws.closed

    async def close(self, code):
        await self.ws.close(code=code)


class AiohttpSubscriptionServer(BaseSubscriptionServer):
    def __init__(self, schema, keep_alive=True, loop=None):
        self.loop = loop
        super().__init__(schema, keep_alive)

    async def _handle(self, ws, request_context=None):
        connection_context = AiohttpConnectionContext(ws, request_context)
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
                self.on_message(connection_context, message), loop=self.loop
            )
            pending.add(task)

        self.on_close(connection_context)
        for task in pending:
            task.cancel()

    async def handle(self, ws, request_context=None):
        await shield(self._handle(ws, request_context), loop=self.loop)

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
        request_string = params.pop("request_string")
        query = parse(request_string)
        result = await subscribe(self.schema, query, **params)

        if not hasattr(result, "__aiter__"):
            await self.send_execution_result(connection_context, op_id, result)
        else:
            connection_context.register_operation(op_id, result)
            async for single_result in result:
                if not connection_context.has_operation(op_id):
                    break
                await self.send_execution_result(
                    connection_context, op_id, single_result
                )
            await self.send_message(connection_context, op_id, GQL_COMPLETE)

    async def on_stop(self, connection_context, op_id):
        self.unsubscribe(connection_context, op_id)
