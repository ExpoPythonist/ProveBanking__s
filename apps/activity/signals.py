from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from .models import Event


@receiver(post_delete, sender=Event, dispatch_uid='projects.Event.post_delete')
def post_delete_event(sender, **kwargs):
    instance = kwargs.get('instance')
    if instance.content_object and hasattr(instance.content_object, 'post_event_object_delete'):
        instance.content_object.post_event_object_delete(instance.user)
