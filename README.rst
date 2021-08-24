==========
GraphQL WS
==========

Websocket backend for GraphQL subscriptions.

Supports the following application servers:

Python 3 application servers, using asyncio:

    * `aiohttp`_
    * `websockets compatible servers`_ such as Sanic
      (via `websockets <https://github.com/aaugustin/websockets/>`__ library)
    * `Django v2+`_

Python 2 application servers:

    * `Gevent compatible servers`_ such as Flask
    * `Django v1.x`_
      (via `channels v1.x <https://channels.readthedocs.io/en/1.x/inshort.html>`__)


Installation instructions
=========================

For instaling graphql-ws, just run this command in your shell

.. code:: bash

    pip install graphql-ws


Examples
========

Python 3 servers
----------------

Create a subscribable schema like this:

.. code:: python

    import asyncio
    import graphene


    class Query(graphene.ObjectType):
        hello = graphene.String()

        @staticmethod
        def resolve_hello(obj, info, **kwargs):
            return "world"


    class Subscription(graphene.ObjectType):
        count_seconds = graphene.Float(up_to=graphene.Int())

        async def resolve_count_seconds(root, info, up_to):
            for i in range(up_to):
                yield i
                await asyncio.sleep(1.)
            yield up_to


    schema = graphene.Schema(query=Query, subscription=Subscription)

aiohttp
~~~~~~~

Then just plug into your aiohttp server.

.. code:: python

    from graphql_ws.aiohttp import AiohttpSubscriptionServer
    from .schema import schema

    subscription_server = AiohttpSubscriptionServer(schema)


    async def subscriptions(request):
        ws = web.WebSocketResponse(protocols=('graphql-ws',))
        await ws.prepare(request)

        await subscription_server.handle(ws)
        return ws


    app = web.Application()
    app.router.add_get('/subscriptions', subscriptions)

    web.run_app(app, port=8000)

You can see a full example here:
https://github.com/graphql-python/graphql-ws/tree/master/examples/aiohttp


websockets compatible servers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Works with any framework that uses the websockets library for its websocket
implementation. For this example, plug in your Sanic server.

.. code:: python

    from graphql_ws.websockets_lib import WsLibSubscriptionServer
    from . import schema

    app = Sanic(__name__)

    subscription_server = WsLibSubscriptionServer(schema)

    @app.websocket('/subscriptions', subprotocols=['graphql-ws'])
    async def subscriptions(request, ws):
        await subscription_server.handle(ws)
        return ws


    app.run(host="0.0.0.0", port=8000)


Django v2+
~~~~~~~~~~


Django Channels 2
~~~~~~~~~~~~~~~~~

Set up with Django Channels just takes three steps:

1. Install the apps
2. Set up your schema
3. Configure the channels router application

First ``pip install channels`` and it to your ``INSTALLED_APPS``. If you
want graphiQL, install the ``graphql_ws.django`` app before
``graphene_django`` to serve a graphiQL template that will work with
websockets:

.. code:: python

    INSTALLED_APPS = [
        "channels",
        "graphql_ws.django",
        "graphene_django",
        # ...
    ]

Point to your schema in Django settings:

.. code:: python

    GRAPHENE = {
        'SCHEMA': 'yourproject.schema.schema'
    }

Finally, you can set up channels routing yourself (maybe using
``graphql_ws.django.routing.websocket_urlpatterns`` in your
``URLRouter``), or you can just use one of the preset channels
applications:

.. code:: python

    ASGI_APPLICATION = 'graphql_ws.django.routing.application'
    # or
    ASGI_APPLICATION = 'graphql_ws.django.routing.auth_application'

Run ``./manage.py runserver`` and go to
`http://localhost:8000/graphql <http://localhost:8000/graphql>`__ to test!


Python 2  servers
-----------------

Create a subscribable schema like this:

.. code:: python

    import graphene
    from rx import Observable


    class Query(graphene.ObjectType):
        hello = graphene.String()

        @staticmethod
        def resolve_hello(obj, info, **kwargs):
            return "world"


    class Subscription(graphene.ObjectType):
        count_seconds = graphene.Float(up_to=graphene.Int())

        async def resolve_count_seconds(root, info, up_to=5):
            return Observable.interval(1000)\
                             .map(lambda i: "{0}".format(i))\
                             .take_while(lambda i: int(i) <= up_to)


    schema = graphene.Schema(query=Query, subscription=Subscription)

Gevent compatible servers
~~~~~~~~~~~~~~~~~~~~~~~~~

Then just plug into your Gevent server, for example, Flask:

.. code:: python

    from flask_sockets import Sockets
    from graphql_ws.gevent import GeventSubscriptionServer
    from schema import schema

    subscription_server = GeventSubscriptionServer(schema)
    app.app_protocol = lambda environ_path_info: 'graphql-ws'


    @sockets.route('/subscriptions')
    def echo_socket(ws):
        subscription_server.handle(ws)
        return []

You can see a full example here:
https://github.com/graphql-python/graphql-ws/tree/master/examples/flask_gevent

Django v1.x
~~~~~~~~~~~

For Django v1.x and Django Channels v1.x, setup your schema in ``settings.py``

.. code:: python

    GRAPHENE = {
        'SCHEMA': 'yourproject.schema.schema'
    }

Then ``pip install "channels<1"`` and it to your django apps, adding the
following to your ``settings.py``

.. code:: python

    CHANNELS_WS_PROTOCOLS = ["graphql-ws", ]
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "asgiref.inmemory.ChannelLayer",
            "ROUTING": "django_subscriptions.urls.channel_routing",
        },
    }

And finally add the channel routes

.. code:: python

    from channels.routing import route_class
    from graphql_ws.django_channels import GraphQLSubscriptionConsumer

    channel_routing = [
        route_class(GraphQLSubscriptionConsumer, path=r"^/subscriptions"),
    ]

You can see a full example here:
https://github.com/graphql-python/graphql-ws/tree/master/examples/django_subscriptions
