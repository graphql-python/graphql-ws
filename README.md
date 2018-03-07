# GraphQL WS

Websocket server for GraphQL subscriptions.

Currently supports:
* [aiohttp](https://github.com/graphql-python/graphql-ws#aiohttp)
* [Gevent](https://github.com/graphql-python/graphql-ws#gevent)
* Sanic (uses [websockets](https://github.com/aaugustin/websockets/) library)

# Installation instructions

For installing graphql-ws, just run this command in your shell

```bash
pip install graphql-ws
```

## Subscription Server

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
### Django (with channels)

First `pip install channels` and add it to your django apps

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

Add the channel routes to your Django server.

```python
from channels.routing import route_class
from graphql_ws.django_channels import GraphQLSubscriptionConsumer

channel_routing = [
    route_class(GraphQLSubscriptionConsumer, path=r"^/subscriptions"),
]
```

## Publish-Subscribe
Included are several publish-subscribe (pubsub) classes for hooking
up your mutations to your subscriptions. When a client makes a
subscription, the pubsub can be used to map from one subscription name
to one or more channel names to subscribe to the right channels.
The subscription query will be re-run every time something is
published to one of these channels. Using these classes, a
subscription is just the result of a mutation. 

### Asyncio

There are two pubsub classes for asyncio, one that is in-memory and the other
that utilizes Redis (for production), via the [aredis](https://github.com/NoneGG/aredis) libary, which
is a asynchronous port of the excellent [redis-py](https://github.com/andymccurdy/redis-py) library.

The schema for asyncio would look something like this below:

```python
import asyncio
import graphene

from graphql_ws.pubsub import AsyncioPubsub

# create a new pubsub object; this class is in-memory and does
# not utilze Redis
pubsub = AsyncioPubsub()


class MutationExample(graphene.Mutation):
    class Arguments:
        input_text = graphene.String()

    output_text = graphene.String()

    async def mutate(self, info, input_text):
        # publish to the pubsub object before returning mutation
        await pubsub.publish('BASE', input_text)
        return MutationExample(output_text=input_text)


class Mutations(graphene.ObjectType):
    mutation_example = MutationExample.Field()


class Subscription(graphene.ObjectType):
    mutation_example = graphene.String()

    async def resolve_mutation_example(root, info):
        try:
            # pubsub subscribe_to_channel method returns
            # subscription id and an asyncio.Queue
            sub_id, q = pubsub.subscribe_to_channel('BASE')
            while True:
                payload = await q.get()
                yield payload
        except asyncio.CancelledError:
            # unsubscribe subscription id from channel
            # when coroutine is cancelled
            pubsub.unsubscribe('BASE', sub_id)

schema = graphene.Schema(mutation=Mutations,
                         subscription=Subscription)
```

You can see a full asyncio example here: https://github.com/graphql-python/graphql-ws/tree/master/examples/aiohttp

### Gevent

There are two pubsub classes for Gevent as well, one that is
in-memory and the other that utilizes Redis (for production), via
[redis-py](https://github.com/andymccurdy/redis-py).

Finally, plug into a subscribable schema:

```python
import graphene

from graphql_ws.pubsub import GeventRxRedisPubsub
from rx import Observable

# create a new pubsub object; in the case you'll need to
# be running a redis-server instance in a separate process
pubsub = GeventRxRedisPubsub()


class MutationExample(graphene.Mutation):
    class Arguments:
        input_text = graphene.String()

    output_text = graphene.String()

    def mutate(self, info, input_text):
        # publish to the pubsub before returning mutation
        pubsub.publish('BASE', input_text)
        return MutationExample(output_text=input_text)


class Mutations(graphene.ObjectType):
    mutation_example = MutationExample.Field()


class Subscription(graphene.ObjectType):
    mutation_example = graphene.String()

    def resolve_mutation_example(root, info):
        # pubsub subscribe_to_channel method returns an observable
        # when observable is disposed of, the subscription will
        # be cleaned up and unsubscribed from
        return pubsub.subscribe_to_channel('BASE')\
                         .map(lambda i: "{0}".format(i))


schema = graphene.Schema(mutation=Mutations,
                         subscription=Subscription)
```

You can see a full example here: https://github.com/graphql-python/graphql-ws/tree/master/examples/flask_gevent


### Django (with channels)


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
