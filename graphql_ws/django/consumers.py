import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from ..constants import TRANSPORT_WS_PROTOCOL, WS_PROTOCOL
from .subscriptions import subscription_server


class GraphQLSubscriptionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.connection_context = None
        found_protocol = None
        for protocol in [WS_PROTOCOL, TRANSPORT_WS_PROTOCOL]:
            if protocol in self.scope["subprotocols"]:
                found_protocol = protocol
                break
        if not found_protocol:
            await self.close()
            return
        self.connection_context = await subscription_server.handle(
            ws=self, request_context=self.scope
        )
        await self.accept(subprotocol=found_protocol)

    async def disconnect(self, code):
        if self.connection_context:
            self.connection_context.socket_closed = True
            await subscription_server.on_close(self.connection_context)

    async def receive_json(self, content):
        subscription_server.on_message(self.connection_context, content)

    @classmethod
    async def encode_json(cls, content):
        return json.dumps(content)
