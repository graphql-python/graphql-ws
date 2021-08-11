from django import template
from ..settings import graphql_ws_path


register = template.Library()

@register.simple_tag
def graphql_ws_get_path():
    return graphql_ws_path
