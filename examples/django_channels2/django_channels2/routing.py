from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from graphql_ws.django.graphql_channels import (
    websocket_urlpatterns as graphql_urlpatterns
)

application = ProtocolTypeRouter(
    {"websocket": AuthMiddlewareStack(URLRouter(graphql_urlpatterns))}
)
