from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):
        from .watson_register import *
        from .autocomplete_light_registry import *
        from . import signals
