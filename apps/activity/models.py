from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import fields as generic

from simple_activity.models import Action as BaseAction


def _default_action_meta():
    return {}


class Event(models.Model):
    """
    any Model that wants to use the Event object is expected
    to have the undergiven method:

       def post_event_object_delete(self, user):
           function_suite

    """
    user = models.ForeignKey('users.User', related_name='events')
    content_type = models.ForeignKey(ContentType, related_name='events')
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = (("content_type", "object_id", "user"), )


class Action(BaseAction):
    CLIENTS = 1
    VENDORS = 2
    ALL = 3
    visibility_choices = (
        (CLIENTS, 'Client'),
        (VENDORS, 'Vendors'),
        (ALL, 'Both vendors and client'),
    )

    visibility = models.PositiveIntegerField(default=ALL, choices=visibility_choices)
