from flask import Flask, make_response
from flask_sockets import Sockets
from graphql_ws.server import GeventSubscriptionServer
import json
from template import render_graphiql
import graphene
import gevent
from flask_graphql import GraphQLView
import asyncio
from rx import Observable


class Query(graphene.ObjectType):
    base = graphene.String()


class Subscription(graphene.ObjectType):

    username = graphene.String()


    def resolve_username(root, info):
        return Observable.interval(1000).map(lambda i: "{0}".format(i))


schema = graphene.Schema(query=Query, subscription=Subscription)



app = Flask(__name__)
app.debug = True
sockets = Sockets(app)


@app.route('/graphiql')
def graphql_view():
    return make_response(render_graphiql())

app.add_url_rule(
    '/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=False))

subscription_server = GeventSubscriptionServer(schema)
app.app_protocol = lambda environ_path_info: 'graphql-ws'

@sockets.route('/subscriptions')
def echo_socket(ws):
    subscription_server.handle(ws)
    return []


if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()