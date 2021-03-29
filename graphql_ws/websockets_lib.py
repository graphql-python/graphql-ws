import json
from asyncio import shield

from websockets import ConnectionClosed

from .base import ConnectionClosedException
from .base_async import BaseAsyncConnectionContext, BaseAsyncSubscriptionServer


class WsLibConnectionContext(BaseAsyncConnectionContext):
    async def receive(self):
        try:
            msg = await self.ws.recv()
            return msg
        except ConnectionClosed:
            raise ConnectionClosedException()

    async def send(self, data):
        if self.closed:
            return
        await self.ws.send(json.dumps(data))

    @property
    def closed(self):
        return self.ws.open is False

    async def close(self, code):
        await self.ws.close(code)


class WsLibSubscriptionServer(BaseAsyncSubscriptionServer):
    async def _handle(self, ws, request_context):
        connection_context = WsLibConnectionContext(ws, request_context)
        await self.on_open(connection_context)
        while True:
            try:
                if connection_context.closed:
                    raise ConnectionClosedException()
                message = await connection_context.receive()
            except ConnectionClosedException:
                break

            self.on_message(connection_context, message)
        await self.on_close(connection_context)

    async def handle(self, ws, request_context=None):
        await shield(self._handle(ws, request_context), loop=self.loop)
