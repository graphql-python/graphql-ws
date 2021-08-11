from django.conf import settings

graphql_ws_path = getattr(settings, "GRAPHQL_WS_PATH", "subscriptions")
