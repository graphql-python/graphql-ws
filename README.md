# GraphQL WS

.. image:: https://img.shields.io/pypi/v/graphql\_ws.svg :target: https://pypi.python.org/pypi/graphql\_ws

.. image:: https://img.shields.io/travis/graphql-python/graphql\_ws.svg :target: https://travis-ci.org/graphql-python/graphql\_ws

.. image:: https://readthedocs.org/projects/graphql-aiows/badge/?version=latest :target: https://graphql-aiows.readthedocs.io/en/latest/?badge=latest :alt: Documentation Status

.. image:: https://pyup.io/repos/github/graphql-python/graphql\_ws/shield.svg :target: https://pyup.io/repos/github/graphql-python/graphql\_ws/ :alt: Updates

Websocket server for GraphQL subscriptions.

-   Free software: MIT license

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

For setting up, just plug into your AioHTTP server.

```python
subscription_server = WebSocketSubscriptionServer(schema)

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
