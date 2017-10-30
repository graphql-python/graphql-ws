# -*- coding: utf-8 -*-

"""Top-level package for GraphQL AioWS."""

__author__ = """Syrus Akbary"""
__email__ = 'me@syrusakbary.com'
__version__ = '0.1.0'


from .observable_aiter import setup_observable_extension
from .server import WebSocketSubscriptionServer
from .gevent_server import GeventSubscriptionServer

setup_observable_extension()
