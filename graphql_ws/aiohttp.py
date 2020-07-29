import json
from asyncio import shield

from aiohttp import WSMsgType

from .base import ConnectionClosedException
from .base_async import BaseAsyncConnectionContext, BaseAsyncSubscriptionServer


class AiohttpConnectionContext(BaseAsyncConnectionContext):
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
        await self.ws.send_str(json.dumps(data))

    @property
    def closed(self):
        return self.ws.closed

    async def close(self, code):
        await self.ws.close(code=code)


class AiohttpSubscriptionServer(BaseAsyncSubscriptionServer):
    async def _handle(self, ws, request_context=None):
        connection_context = AiohttpConnectionContext(ws, request_context)
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
