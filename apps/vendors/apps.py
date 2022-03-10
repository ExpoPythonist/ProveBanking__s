from django.apps import AppConfig


class VendorsConfig(AppConfig):
    name = 'vendors'
    verbose_name = "vendors"

    def ready(self):
        from .signals import *
        from .watson_register import *
