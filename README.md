# GraphQL WS

Websocket server for GraphQL subscriptions.

Currently supports:
* [aiohttp](https://github.com/graphql-python/graphql-ws#aiohttp)
* [Gevent](https://github.com/graphql-python/graphql-ws#gevent)
* Sanic (uses [websockets](https://github.com/aaugustin/websockets/) library)

# Installation instructions

For instaling graphql-ws, just run this command in your shell

```bash
pip install graphql-ws
```

## Examples

### aiohttp

For setting up, just plug into your aiohttp server.

```python
from graphql_ws.aiohttp import AiohttpSubscriptionServer


subscription_server = AiohttpSubscriptionServer(schema)

async def subscriptions(request):
    ws = web.WebSocketResponse(protocols=('graphql-ws',))
    await ws.prepare(request)

    await subscription_server.handle(ws)
    return ws


app = web.Application()
app.router.add_get('/subscriptions', subscriptions)

web.run_app(app, port=8000)
```

### Sanic

Works with any framework that uses the websockets library for
it's websocket implementation. For this example, plug in
your Sanic server.

```python
from graphql_ws.websockets_lib import WsLibSubscriptionServer


app = Sanic(__name__)

subscription_server = WsLibSubscriptionServer(schema)

@app.websocket('/subscriptions', subprotocols=['graphql-ws'])
async def subscriptions(request, ws):
    await subscription_server.handle(ws)
    return ws


app.run(host="0.0.0.0", port=8000)
```

And then, plug into a subscribable schema:

```python
import asyncio
import graphene


class Query(graphene.ObjectType):
    base = graphene.String()


class Subscription(graphene.ObjectType):
    count_seconds = graphene.Float(up_to=graphene.Int())

    async def resolve_count_seconds(root, info, up_to):
        for i in range(up_to):
            yield i
            await asyncio.sleep(1.)
        yield up_to


schema = graphene.Schema(query=Query, subscription=Subscription)
```

You can see a full example here: https://github.com/graphql-python/graphql-ws/tree/master/examples/aiohttp

### Gevent

For setting up, just plug into your Gevent server.

```python
subscription_server = GeventSubscriptionServer(schema)
app.app_protocol = lambda environ_path_info: 'graphql-ws'

@sockets.route('/subscriptions')
def echo_socket(ws):
    subscription_server.handle(ws)
    return []
```

And then, plug into a subscribable schema:

```python
import graphene
from rx import Observable


class Query(graphene.ObjectType):
    base = graphene.String()


class Subscription(graphene.ObjectType):
    count_seconds = graphene.Float(up_to=graphene.Int())

    async def resolve_count_seconds(root, info, up_to=5):
        return Observable.interval(1000)\
                         .map(lambda i: "{0}".format(i))\
                         .take_while(lambda i: int(i) <= up_to)


schema = graphene.Schema(query=Query, subscription=Subscription)
```

You can see a full example here: https://github.com/graphql-python/graphql-ws/tree/master/examples/flask_gevent


### Django Channels

First `pip install channels` and it to your django apps

Then add the following to your settings.py

```python
    CHANNELS_WS_PROTOCOLS = ["graphql-ws", ]
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "asgiref.inmemory.ChannelLayer",
            "ROUTING": "django_subscriptions.urls.channel_routing",
        },

    }
```

Setup your graphql schema

```python
import graphene
from rx import Observable


class Query(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(self, info, **kwargs):
        return 'world'

class Subscription(graphene.ObjectType):

    count_seconds = graphene.Int(up_to=graphene.Int())


    def resolve_count_seconds(
        root, 
        info, 
        up_to=5
    ):
        return Observable.interval(1000)\
                         .map(lambda i: "{0}".format(i))\
                         .take_while(lambda i: int(i) <= up_to)



schema = graphene.Schema(
    query=Query,
    subscription=Subscription
)


````

Setup your schema in settings.py

```python
GRAPHENE = {
    'SCHEMA': 'path.to.schema'
}
```

and finally add the channel routes

```python
from channels.routing import route_class
from graphql_ws.django_channels import GraphQLSubscriptionConsumer

channel_routing = [
    route_class(GraphQLSubscriptionConsumer, path=r"^/subscriptions"),
]
```

### Django Channels 2

Set up with Django Channels just takes three steps:

1. Install the apps
2. Set up your schema
3. Configure the channels router application


First `pip install channels` and it to your `INSTALLED_APPS`. If you want
graphiQL, install the `graphql_ws.django` app before `graphene_django` to serve
a graphiQL template that will work with websockets:

```python
INSTALLED_APPS = [
    "channels",
    "graphql_ws.django",
    "graphene_django",
    # ...
]
```


Next, set up your graphql schema:

```python
import graphene
from rx import Observable


class Query(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(self, info, **kwargs):
        return "world"


class Subscription(graphene.ObjectType):

    count_seconds = graphene.Int(up_to=graphene.Int())

    def resolve_count_seconds(root, info, up_to=5):
        return (
            Observable.interval(1000)
            .map(lambda i: "{0}".format(i))
            .take_while(lambda i: int(i) <= up_to)
        )


schema = graphene.Schema(query=Query, subscription=Subscription)
```

...and point to your schema in Django settings
```python
GRAPHENE = {
    'SCHEMA': 'yourproject.schema'
}
```


Finally, you can set up channels routing yourself (maybe using
`graphql_ws.django.routing.websocket_urlpatterns` in your `URLRouter`), or you
can just use one of the preset channels applications:

```python
ASGI_APPLICATION = 'graphql_ws.django.routing.application'
# or
ASGI_APPLICATION = 'graphql_ws.django.routing.auth_application'
```

Run `./manage.py runserver` and go to `http://localhost:8000/graphql` to test!
