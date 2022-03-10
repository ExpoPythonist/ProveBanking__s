from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    name = 'reviews'
    verbose_name = "Reviews"

    def ready(self):
        from .signals import *
