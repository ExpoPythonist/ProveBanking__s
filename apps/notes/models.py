from django.contrib.auth import get_user_model
from django.contrib.contenttypes import fields as generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import linebreaks, urlizetrunc, escape
from django.utils.html import strip_tags

from filtered_contenttypes.fields import FilteredGenericForeignKey

from med_social.utils import humanized_datetime


class NoteMixin(object):
    def __unicode__(self):
        return self.content[:64].strip()

    @property
    def html(self):
        return linebreaks(urlizetrunc(escape(self.content), 24))

    @property
    def excerpt(self, num_chars=256):
        return urlizetrunc(
            escape(self.content[:num_chars].strip()), 24)

    @property
    def natural_created_date(self):
        return humanized_datetime(self.created)


class Note(models.Model, NoteMixin):
    PERMISSIONS = (
        ('manage_notes', 'Can manage notes', Permission.CLIENT, True),
    )
    content = models.TextField()
    posted_by = models.ForeignKey('users.User',
                                  related_name='notes_set')

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = FilteredGenericForeignKey('content_type', 'object_id')

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'note'
        verbose_name_plural = 'notes'
        db_table = 'notes'
        ordering = ('-created',)

    def get_absolute_url(self):
        return reverse('notes:detail', args=[self.id, ])


class NoteComment(models.Model, NoteMixin):
    content = models.TextField()
    posted_by = models.ForeignKey('users.User',
                                  related_name='note_comments')
    note = models.ForeignKey(Note, related_name='comments')

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'note comment'
        verbose_name_plural = 'note comments'
        db_table = 'notes_comments'
        ordering = ('created',)

    def get_absolute_url(self):
        url = reverse('notes:detail', args=[self.note.id, ])
        return "{url}#comment-{id}".format(url=url, id=self.id)
