from os import path as op

from django.conf import settings
from django.db import connection
from django.test import TestCase

from tenant_schemas.test.client import TenantClient, TenantRequestFactory

from customers.models import Customer


class TenantTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        Customer.objects.get_or_create(
            domain_url='vetted.dev', schema_name='public',
            name='Vetted', email='admin@vetted.dev'
        )
        cls.tenant = Customer.objects.create(
            name='Westeros', schema_name='westeros',
            domain_url='westeros.vetted.dev', email='tommen@westeros.com'
        )
        cls.tenant.switch_to_tenant_db()

    @classmethod
    def tearDownClass(cls):
        cls.tenant.switch_to_public_db()
        cls.tenant.auto_drop_schema = True
        cls.tenant.delete()

    def _pre_setup(self):
        super(TenantTestCase, self)._pre_setup()
        self.client = TenantClient(self.tenant)
        self.factory = TenantRequestFactory(self.tenant)
