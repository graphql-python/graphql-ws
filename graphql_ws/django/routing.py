from channels import __version__ as channels_version
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack
from django.utils.version import get_version_tuple
from django.apps import apps
from django.urls import path
from .consumers import GraphQLSubscriptionConsumer

if apps.is_installed("django.contrib.auth"):
    from channels.auth import AuthMiddlewareStack
else:
    AuthMiddlewareStack = None


channels_version_tuple = get_version_tuple(channels_version)


if channels_version_tuple > (3, 0, 0):
    websocket_urlpatterns = [
        path("subscriptions", GraphQLSubscriptionConsumer.as_asgi())
    ]
else:
    websocket_urlpatterns = [path("subscriptions", GraphQLSubscriptionConsumer)]

application = ProtocolTypeRouter({"websocket": URLRouter(websocket_urlpatterns)})

session_application = ProtocolTypeRouter(
    {"websocket": SessionMiddlewareStack(URLRouter(websocket_urlpatterns))}
)

if AuthMiddlewareStack:
    auth_application = ProtocolTypeRouter(
        {"websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns))}
    )
