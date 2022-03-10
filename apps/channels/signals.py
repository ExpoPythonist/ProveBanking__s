from django.db import connection
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from .models import Message
from .tasks import new_message


@receiver(post_save, sender=Message,
          dispatch_uid='projects.ProposedResource.post_save')
def post_save_message(sender, **kwargs):
    created = kwargs.get('created')
    message = kwargs.get('instance')
    # if created:
    #     tenant = connection.get_tenant()
    #     new_message.delay(tenant.id, message.id)
