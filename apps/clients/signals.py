import clearbit
import os
import urllib

from urlparse import urlparse

from django.db import connection
from django.core.files import File
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save

from .models import (Client,)
from .tasks import client_logo_update


@receiver(post_save, sender=Client,
          dispatch_uid='clients.Client.post_save')
def post_save_client(sender, **kwargs):
    created = kwargs.get('created')
    instance = kwargs.get('instance')
    if instance.website and not instance.logo:
        client_logo_update.delay(tenant_id=connection.tenant.id,
                                 instance_id=instance.id)
        
