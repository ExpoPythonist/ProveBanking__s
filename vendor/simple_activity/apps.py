from django.apps import AppConfig


class SimpleActivityConfig(AppConfig):
    name = 'simple_activity'
    verbose_name = "Simple Activity"

    def ready(self):
        from .verbs import *
        from .signals import *
