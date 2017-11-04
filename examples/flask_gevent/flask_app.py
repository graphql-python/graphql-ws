import json

import graphene
from flask import Flask, make_response
from flask_graphql import GraphQLView
from flask_sockets import Sockets
from rx import Observable

from graphql_ws import GeventSubscriptionServer
from template import render_graphiql


class Query(graphene.ObjectType):
    base = graphene.String()


class RandomType(graphene.ObjectType):
    seconds = graphene.Int()
    random_int = graphene.Int()


class Subscription(graphene.ObjectType):

    count_seconds = graphene.Int(up_to=graphene.Int())

    random_int = graphene.Field(RandomType)


    def resolve_count_seconds(root, info, up_to):
        return Observable.interval(1000)\
                         .map(lambda i: "{0}".format(i))\
                         .take_while(lambda i: int(i) <= up_to)

    def resolve_random_int(root, info):
        import random
        return Observable.interval(1000).map(lambda i: RandomType(seconds=i, random_int=random.randint(0, 500)))

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
