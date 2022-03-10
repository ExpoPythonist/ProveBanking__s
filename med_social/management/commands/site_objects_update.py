from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

from med_social.utils import get_current_tenant


class Command(BaseCommand):

    def handle(self, *args, **options):
        current_tenant = get_current_tenant()
        if current_tenant.schema_name == 'public':
            Site.objects.update(name=current_tenant.name,
                                domain=current_tenant.domain_url)
        else:
            Site.objects.update(name=current_tenant.name + " at Proven",
                                domain=current_tenant.domain_url)
