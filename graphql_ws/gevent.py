from __future__ import absolute_import

import json

from .base import (
    BaseConnectionContext,
    ConnectionClosedException,
)
from .base_sync import BaseSyncSubscriptionServer


class GeventConnectionContext(BaseConnectionContext):
    def receive(self):
        msg = self.ws.receive()
        return msg

    def send(self, data):
        if self.closed:
            return
        self.ws.send(json.dumps(data))

    @property
    def closed(self):
        return self.ws.closed

    def close(self, code):
        self.ws.close(code)


class GeventSubscriptionServer(BaseSyncSubscriptionServer):
    def handle(self, ws, request_context=None):
        connection_context = GeventConnectionContext(ws, request_context)
        self.on_open(connection_context)
        while True:
            try:
                if connection_context.closed:
                    raise ConnectionClosedException()
                message = connection_context.receive()
            except ConnectionClosedException:
                self.on_close(connection_context)
                return
            self.on_message(connection_context, message)
