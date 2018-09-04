import asyncio
import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from promise import Promise

from ..constants import WS_PROTOCOL
from .subscriptions import subscription_server


class JSONPromiseEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Promise):
            return o.value
        return super(JSONPromiseEncoder, self).default(o)


json_promise_encoder = JSONPromiseEncoder()


class GraphQLSubscriptionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.connection_context = None
        if WS_PROTOCOL in self.scope["subprotocols"]:
            self.connection_context = await subscription_server.handle(
                ws=self, request_context=self.scope
            )
            await self.accept(subprotocol=WS_PROTOCOL)
        else:
            await self.close()

    async def disconnect(self, code):
        if self.connection_context:
            await subscription_server.on_close(self.connection_context)

    async def receive_json(self, content):
        asyncio.ensure_future(
            subscription_server.on_message(self.connection_context, content)
        )

    @classmethod
    async def encode_json(cls, content):
        return json_promise_encoder.encode(content)
