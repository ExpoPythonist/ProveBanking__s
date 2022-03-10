import csv
from logging import getLogger

from tenant_schemas.management.commands import BaseCommand
import requests
from requests.exceptions import HTTPError

from clients.models import Client
from vendors.models import Vendor, ClientReference
from users.models import User


logger = getLogger(__name__)


def return_client(row, key):
    if not row[key]:
        return None
    client_name = row[key]
    client = Client.objects.filter(name__iexact=client_name).first()
    if not client:
        url = u'https://autocomplete.clearbit.com/v1/companies/suggest?query={}'.format(client_name)
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            autocomplete_data = resp.json()
            data = None

            if autocomplete_data:
                data = autocomplete_data[0]
        except (KeyError, HTTPError):
            return None
        if not data:
            return None

        client = Client(name=client_name, website=data['domain'])
        client.save()
        client = Client.objects.get(id=client.id)
    return client


def return_vendor(row):
    name = row['Name of Company']

    vendor = Vendor.objects.filter(name__iexact=name).first()
    if vendor:
        return vendor

    twitter = row['Twitter']
    if twitter:
        twitter = twitter.replace("https://twitter.com/", "")
    website = row['Website URL']
    address = row['Address']
    phone = row['Telephone']
    data = dict(twitter=twitter, website=website, name=name, address=address, phone=phone)
    vendor = Vendor(**data)
    vendor.save()
    vendor = Vendor.objects.get(id=vendor.id)
    return vendor


def decode_row(row, fields):
    for key in fields:
        value = row.get(key)
        if value:
            row[key] = value.decode('utf8')


class Command(BaseCommand):
    help = 'Import Clients from csv file'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file', required=True, help='Path to file')
        parser.add_argument('--client-only', dest='clients', action='store_true')

    clients_keys = [
        'Client 1', 'Client 2', 'Client 3'
    ]
    need_decode = [
        'Client 1', 'Client 2', 'Client 3', 'Address', 'Name of Company'
    ]

    def handle(self, *args, **options):
        management = User.get_management_user()
        filename = options['file']
        with open(filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                logger.info("Processing row: {}".format(row))
                decode_row(row, self.need_decode)
                vendor = return_vendor(row)

                for client_key in self.clients_keys:
                    client = return_client(row, client_key)
                    if not client:
                        continue
                    is_exist = ClientReference.objects.filter(client=client, vendor=vendor).first()
                    if is_exist:
                        continue
                    cr = ClientReference(client=client, vendor=vendor, created_by=management,
                                         is_fulfilled=True)
                    cr.save()
                    logger.info("ClientReference {} saved".format(cr))
