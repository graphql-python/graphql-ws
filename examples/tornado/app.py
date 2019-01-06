from asyncio import Queue
from tornado import web, ioloop, websocket

from graphene_tornado.tornado_graphql_handler import TornadoGraphQLHandler

from graphql_ws.tornado import TornadoSubscriptionServer
from graphql_ws.constants import GRAPHQL_WS

from .template import render_graphiql
from .schema import schema


class GraphiQLHandler(web.RequestHandler):
    def get(self):
        self.finish(render_graphiql())


class SubscriptionHandler(websocket.WebSocketHandler):
    def initialize(self, subscription_server):
        self.subscription_server = subscription_server
        self.queue = Queue(100)

    def select_subprotocol(self, subprotocols):
        return GRAPHQL_WS

    def open(self):
        ioloop.IOLoop.current().spawn_callback(self.subscription_server.handle, self)

    async def on_message(self, message):
        await self.queue.put(message)

    async def recv(self):
        return await self.queue.get()


subscription_server = TornadoSubscriptionServer(schema)

app = web.Application([
    (r"/graphql$", TornadoGraphQLHandler, dict(
        schema=schema)),
    (r"/subscriptions", SubscriptionHandler, dict(
        subscription_server=subscription_server)),
    (r"/graphiql$", GraphiQLHandler),
])

app.listen(8000)
ioloop.IOLoop.current().start()
