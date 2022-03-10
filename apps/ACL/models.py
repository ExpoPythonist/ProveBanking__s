from django.dispatch import receiver
from django.db.models.signals import post_migrate


@receiver(post_migrate)
def load_fixtures(**kwargs):
    if kwargs.get('app') == 'reviews':
        from django.core.management import call_command
        call_command('permissions')
