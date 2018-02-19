from graphql_ws.django_channels import GraphQLSubscriptionConsumer
from django.urls import path

from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import logging 

logger = logging.getLogger('django')


application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("subscriptions", GraphQLSubscriptionConsumer),
        ])
    ),
})