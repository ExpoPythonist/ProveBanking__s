from django.db import models, connection
from vlkjsonfield.fields import VLKJSONField

from . import types as answer_types


def _get_default_definitions():
    return {}


class SLA(models.Model):
    question = models.TextField()
    answer_type = models.PositiveSmallIntegerField(
        choices=answer_types.as_choices())
    definitions = VLKJSONField(default=_get_default_definitions)

    expires = models.DateTimeField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.definitions is None and self.answer_type:
            self.definitions = self.answer_class.get_default_definitions()
        return super(SLA, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.question

    @property
    def answer_class(self):
        return answer_types.get(self.answer_type)


class Response(models.Model):
    sla = models.ForeignKey(SLA, related_name='responses')
    # FIXME: We might have to add multple answer field or create a composite field
    # but for now we'll just use an integer field
    answer = models.IntegerField()
    answered_by = models.ForeignKey('users.User', related_name='sla_responses')
    created = models.DateTimeField(auto_now_add=True)
