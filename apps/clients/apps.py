from django.apps import AppConfig


class ClientsConfig(AppConfig):
    name = 'clients'
    verbose_name = "clients"

    def ready(self):
        from .signals import *
