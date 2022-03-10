from django.dispatch import receiver
from django.db.models.signals import post_migrate


# load up all fixtures here and app specific fixtures in the app's models.py
@receiver(post_migrate)
def load_fixtures(**kwargs):
    pass
