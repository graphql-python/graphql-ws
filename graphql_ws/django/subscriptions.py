from graphene_django.settings import graphene_settings
from graphql import MiddlewareManager

from ..base_async import (BaseAsyncConnectionContext,
                          BaseAsyncSubscriptionServer)
from ..observable_aiter import setup_observable_extension

setup_observable_extension()


class ChannelsConnectionContext(BaseAsyncConnectionContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    def get_graphql_params(self, connection_context, payload):
        params = super().get_graphql_params(connection_context, payload)
        middleware = graphene_settings.MIDDLEWARE
        if middleware:
            if not isinstance(middleware, MiddlewareManager):
                middleware = MiddlewareManager(
                    *middleware, wrap_in_promise=False
                )
            params["middleware"] = middleware
        return params


subscription_server = ChannelsSubscriptionServer(schema=graphene_settings.SCHEMA)
