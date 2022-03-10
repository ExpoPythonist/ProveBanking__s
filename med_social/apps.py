from django.apps import AppConfig


class MedSocialConfig(AppConfig):
    name = 'med_social'
    verbose_name = "Med Social"

    def ready(self):
        from mixpanel.tasks import *
