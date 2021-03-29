from django.urls import path
from graphene_django.views import GraphQLView

urlpatterns = [path("graphql/", GraphQLView.as_view(graphiql=True))]
