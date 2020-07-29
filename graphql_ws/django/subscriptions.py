from graphene_django.settings import graphene_settings
from ..base_async import BaseAsyncConnectionContext, BaseAsyncSubscriptionServer
from ..observable_aiter import setup_observable_extension

setup_observable_extension()


class ChannelsConnectionContext(BaseAsyncConnectionContext):
    def __init__(self, *args, **kwargs):
        super(ChannelsConnectionContext, self).__init__(*args, **kwargs)
        self.socket_closed = False

    async def send(self, data):
        if self.closed:
            return
        await self.ws.send_json(data)

    @property
    def closed(self):
        return self.socket_closed

    async def close(self, code):
        await self.ws.close(code=code)

    async def receive(self, code):
        """
        Unused, as the django consumer handles receiving messages and passes
        them straight to ChannelsSubscriptionServer.on_message.
        """


class ChannelsSubscriptionServer(BaseAsyncSubscriptionServer):
    async def handle(self, ws, request_context=None):
        connection_context = ChannelsConnectionContext(ws, request_context)
        await self.on_open(connection_context)
        return connection_context


subscription_server = ChannelsSubscriptionServer(schema=graphene_settings.SCHEMA)
