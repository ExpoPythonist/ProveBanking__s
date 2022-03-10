from django.core.management.base import BaseCommand

from ACL.utils import create_default_client_groups, create_default_client_perms, create_default_vendor_perms


class Command(BaseCommand):
    GROUPS = {}

    def handle(self, *args, **options):
        from vendors.models import Vendor
        create_default_client_groups()
        create_default_client_perms()
        for vendor in Vendor.objects.all():
            create_default_vendor_perms(vendor)
