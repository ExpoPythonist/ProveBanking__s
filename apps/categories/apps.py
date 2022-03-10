from django.apps import AppConfig


class CategoriesConfig(AppConfig):
    name = 'categories'
    verbose_name = "Categories"

    def ready(self):
        from .watson_register import *
