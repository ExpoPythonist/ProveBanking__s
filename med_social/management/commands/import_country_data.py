import xlrd
import re
import os
import string
import random

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import csv

from med_social.utils import get_current_tenant
from med_social.utils import slugify

from categories.models import Category
from locations.models import Location
from vendors.models import Vendor, VendorLocation, VendorCategories, ProcurementContact, VendorServices
from users.models import User


class Command(BaseCommand):

    def handle(self, *args, **options):
        module_dir = os.path.dirname(__file__)
        file_path = os.path.join(module_dir, 'loc.csv')
        with open(file_path) as csvfile:
            spamreader = csv.DictReader(csvfile)
            for row in spamreader:
                if row['Name'] and row['Target Type'] == 'Country':
                    print row['Name']
                    loc, _ = Location.objects.get_or_create(location_id=int(row['Criteria ID']),
                                                             defaults={
                                                                 'city': row['Name'],
                                                                 'expanded': row['Canonical Name'],
                                                                 'kind': 3})
                    if row['Country Code']:
                        loc.iso = row['Country Code']
                        loc.save()

