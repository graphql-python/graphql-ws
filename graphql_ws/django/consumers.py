from channels.generic.websocket import AsyncJsonWebsocketConsumer
from ..constants import WS_PROTOCOL
from .subscriptions import subscription_server


class GraphQLSubscriptionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.connection_context = None
        if WS_PROTOCOL in self.scope["subprotocols"]:
            self.connection_context = await subscription_server.handle(self, self.scope)
            await self.accept(subprotocol=WS_PROTOCOL)
        else:
            await self.close()

    async def disconnect(self, code):
        if self.connection_context:
            await subscription_server.on_close(self.connection_context)

    async def receive_json(self, content):
        await subscription_server.on_message(self.connection_context, content)
