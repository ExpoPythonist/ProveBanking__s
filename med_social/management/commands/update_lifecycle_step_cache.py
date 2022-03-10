from django.core.management.base import BaseCommand

from lifecycles.models import LifecycleInstance
from lifecycles.utils import update_status_cache


class Command(BaseCommand):
    def handle(self, *args, **options):
        for lc in LifecycleInstance.objects.all():
            update_status_cache(lc)
