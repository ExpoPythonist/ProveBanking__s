from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    name = 'projects'
    verbose_name = "Projects"

    def ready(self):
        from .signals import *
        from .watson_register import *
