from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):

    def handle(self, *args, **options):
        ContentType.objects.filter(model=None).delete()        
