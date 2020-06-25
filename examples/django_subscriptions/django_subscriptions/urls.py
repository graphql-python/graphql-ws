"""django_subscriptions URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from .template import render_graphiql
from django.http import HttpResponse

from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

from channels.routing import route_class
from graphql_ws.django_channels import GraphQLSubscriptionConsumer


def graphiql(request):
    response = HttpResponse(content=render_graphiql())
    return response


urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^graphiql/", graphiql),
    url(r"^graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
]

channel_routing = [
    route_class(GraphQLSubscriptionConsumer, path=r"^/subscriptions"),
]
