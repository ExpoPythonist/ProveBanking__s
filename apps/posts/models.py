from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Post(models.Model):
    title = models.CharField(max_length=255)
    intro = models.TextField(blank=True)
    body = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('posts:post_view', args=(self.pk,))
