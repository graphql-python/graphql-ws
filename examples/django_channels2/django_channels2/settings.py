"""
Django settings for django_channels2 project.
"""
SECRET_KEY = "0%1c709jhmggqhk&=tci06iy+%jedfxpcoai69jd8wjzm+k2f0"
DEBUG = True


INSTALLED_APPS = ["channels", "graphql_ws.django", "graphene_django"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ]
        },
    }
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = "django_channels2.urls"
ASGI_APPLICATION = "graphql_ws.django.routing.application"


CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
GRAPHENE = {"MIDDLEWARE": [], "SCHEMA": "django_channels2.schema.schema"}
