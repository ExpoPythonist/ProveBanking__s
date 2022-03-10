from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from autoslug.fields import AutoSlugField
from autoslug.settings import slugify
from colorfield.fields import ColorField


class Role(models.Model):
    name = models.CharField(max_length=127)
    slug = AutoSlugField(populate_from='name', unique=True)
    color = ColorField(default='#f2f1f0')

    def __unicode__(self):
        return self.name

    @classmethod
    def can_create(self, user):
        return True

    @classmethod
    def create_for_autocomplete(cls, text, request):
        slug = slugify(text)
        item, created = cls.objects.get_or_create(slug=slug,
                                                  defaults={'name': text})
        return {'text': item.name, 'pk': item.pk}

    @classmethod
    def get_autocomplete_create_url(cls, extra_data=None):
        ctype = ContentType.objects.get_for_model(cls)
        return reverse('create_for_autocomplete', args=(ctype.id,))
