from graphql import format_error
from graphql_ws.websockets_lib import WsLibSubscriptionServer
from sanic import Sanic, response
from schema import schema
from template import render_graphiql

app = Sanic(__name__)


@app.route('/graphql', methods=['GET', 'POST'])
async def graphql_view(request):
    payload = request.json
    result = await schema.execute(payload.get('query', ''),
                                  return_promise=True)
    data = {}
    if result.errors:
        data['errors'] = [format_error(e) for e in result.errors]
    if result.data:
        data['data'] = result.data
    return response.json(data,)


@app.route('/graphiql')
async def graphiql_view(request):
    return response.html(render_graphiql())

subscription_server = WsLibSubscriptionServer(schema)


@app.websocket('/subscriptions', subprotocols=['graphql-ws'])
async def subscriptions(request, ws):
    await subscription_server.handle(ws)
    return ws


app.run(host="0.0.0.0", port=8000)
