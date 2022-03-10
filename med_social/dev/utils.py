from django.db import connection
from customers.models import Customer


def change_tenant(tenant_name):
    """ONLY FOR DEV. Don't user in production code"""
    connection.set_tenant(Customer.objects.get(schema_name=tenant_name))
