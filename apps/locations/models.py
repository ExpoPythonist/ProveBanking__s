from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from autoslug import AutoSlugField
from autoslug.settings import slugify


class Location(models.Model):
    KIND_CITY = 1
    KIND_STATE = 2
    KIND_COUNTRY = 3
    KIND_CHOICES = (
        (KIND_CITY, 'city'),
        (KIND_STATE, 'state'),
        (KIND_COUNTRY, 'country')
    )

    city = models.CharField(_('location'), max_length=255)
    slug = models.CharField(max_length=255, blank=True)  # AutoSlugField(populate_from='city', unique=True, always_update=True, null=True, blank=True)
    expanded = models.CharField(max_length=255, null=True, blank=True)
    kind = models.PositiveSmallIntegerField(choices=KIND_CHOICES, default=KIND_CITY)
    parent_idx = models.IntegerField(null=True, blank=True)
    location_id = models.IntegerField(null=True, blank=True)
    parent = models.ForeignKey("self", related_name='children', null=True, blank=True)
    iso = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ('city',)

    def save(self, *args, **kwargs):
        self.city = self.city.strip()
        return super(Location, self).save(*args, **kwargs)

    def __unicode__(self):
        return "{}".format(self.city.encode('utf-8'))

    @classmethod
    def can_create(self, user):
        return True

    @classmethod
    def create_for_autocomplete(cls, text, request):
        slug = slugify(text)
        item, created = cls.objects.get_or_create(slug=slug,
                                                  defaults={'city': text})
        return {'text': item.city, 'pk': item.pk}

    @classmethod
    def get_autocomplete_create_url(cls, extra_data=None):
        ctype = ContentType.objects.get_for_model(cls)
        return reverse('create_for_autocomplete', args=(ctype.id,))
