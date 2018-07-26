from channels.routing import ProtocolTypeRouter, URLRouter
from django.apps import apps
from django.urls import path
from .consumers import GraphQLSubscriptionConsumer

if apps.is_installed("django.contrib.auth"):
    from channels.auth import AuthMiddlewareStack
else:
    AuthMiddlewareStack = None


websocket_urlpatterns = [path("subscriptions", GraphQLSubscriptionConsumer)]

application = ProtocolTypeRouter({"websocket": URLRouter(websocket_urlpatterns)})

if AuthMiddlewareStack:
    auth_application = ProtocolTypeRouter(
        {"websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns))}
    )
