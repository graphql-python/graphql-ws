from graphql_ws.websockets_lib import WsLibSubscriptionServer
from graphql.execution.executors.asyncio import AsyncioExecutor
from sanic import Sanic, response
from sanic_graphql import GraphQLView
from schema import schema
from template import render_graphiql

app = Sanic(__name__)


@app.listener("before_server_start")
def init_graphql(app, loop):
    app.add_route(
        GraphQLView.as_view(schema=schema, executor=AsyncioExecutor(loop=loop)),
        "/graphql",
    )


@app.route("/graphiql")
async def graphiql_view(request):
    return response.html(render_graphiql())


subscription_server = WsLibSubscriptionServer(schema)


@app.websocket("/subscriptions", subprotocols=["graphql-ws"])
async def subscriptions(request, ws):
    await subscription_server.handle(ws)
    return ws


app.run(host="0.0.0.0", port=8000)
