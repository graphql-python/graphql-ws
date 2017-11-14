# GraphQL WS

Websocket server for GraphQL subscriptions.

# Installation instructions

For having a demo with Python 3.6:

```shell
git clone https://github.com/graphql-python/graphql-ws.git
cd graphql-ws

# Install the package
python setup.py develop
pip install -r requirements_dev.txt

# Demo time!
cd examples
python aio.py
```

## Setup

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
