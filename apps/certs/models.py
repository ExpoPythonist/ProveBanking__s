from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from autoslug.fields import AutoSlugField


class Cert(models.Model):
    KIND_CERT = 1
    KIND_PARTNER = 2
    KIND_INSURANCE = 3
    KIND_CHOICES = (
        (KIND_CERT, 'cert'),
        (KIND_PARTNER, 'partner'),
        (KIND_INSURANCE, 'insurance'),
    )

    name = models.CharField(max_length=127)
    slug = AutoSlugField(populate_from='name', unique=True, null=True, always_update=True)
    client = models.ForeignKey('clients.Client', related_name='certs', null=True)
    kind = models.PositiveSmallIntegerField(choices=KIND_CHOICES, default=KIND_CERT)

    def __unicode__(self):
        return self.name

    @classmethod
    def can_create(cls, user):
        return True

    @classmethod
    def create_for_autocomplete(cls, text, request):
        item, created = cls.objects.get_or_create(name=text)
        return {'text': item.name, 'pk': item.pk}

    @classmethod
    def get_autocomplete_create_url(cls, extra_data=None):
        ctype = ContentType.objects.get_for_model(cls)
        return reverse('create_for_autocomplete', args=(ctype.id,))
