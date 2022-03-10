import clearbit
import imghdr
import urlparse
import urllib
import os

from urlparse import urlparse
import requests

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.utils.timezone import now


from annoying.functions import get_object_or_None
from tenant_schemas.utils import tenant_context, get_tenant_model
from django_atomic_celery import task

from med_social.utils import get_current_tenant

from vendors.models import Vendor
from .models import Client


@task
def client_logo_update(tenant_id, instance_id):
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        instance = get_object_or_None(Client, id=instance_id)
        if not instance or not instance.website:
            return
        logo_url = 'http://logo.clearbit.com/{}'.format(instance.domain)
        resp = requests.get(logo_url)
        if resp and resp.content and imghdr.what('', resp.content):
            instance.logo.save(os.path.basename(instance.domain), ContentFile(resp.content))
            instance.save()


@task
def vendor_logo_update(tenant_id, instance_id):
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        instance = get_object_or_None(Vendor, id=instance_id)
        if not instance or not instance.website:
            return
        logo_url = 'http://logo.clearbit.com/{}'.format(instance.domain)
        resp = requests.get(logo_url)
        if resp and resp.content and imghdr.what('', resp.content):
            instance.logo.save(os.path.basename(instance.domain), ContentFile(resp.content))
            instance.save()
