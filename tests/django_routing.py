from channels.routing import route
from graphql_ws.django_channels import GraphQLSubscriptionConsumer

channel_routing = [
    route("websocket.receive", GraphQLSubscriptionConsumer),
]
