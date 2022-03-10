from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models.signals import post_migrate

from model_utils.managers import QueryManager
from autoslug import AutoSlugField
from annoying.functions import get_object_or_None

from med_social.utils import slugify


class CategoryKindMixin(object):
    KIND_CATEGORY = 1
    KIND_INDUSTRY = 2
    KIND_LANGUAGE = 3
    KIND_SERVICE = 4
    KIND_SKILL = KIND_CATEGORY
    KIND_CUSTOM = 5
    KIND_CHOICES = (
        (KIND_CATEGORY, 'category'),
        (KIND_INDUSTRY, 'industry'),
        (KIND_SKILL, 'skill'),
        (KIND_LANGUAGE, 'language'),
        (KIND_SERVICE, 'service'),
        (KIND_CUSTOM, 'custom'),
    )
    KIND_LABELS = {
        'category': 'categories',
        'industry': 'industries',
        'skill': 'skills',
        'language': 'languages',
        'service': 'services',
        'custom': 'custom',
    }


class Category(models.Model, CategoryKindMixin):
    name = models.CharField(max_length=511)
    slug = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('self',
                               related_name='categories',
                               null=True, blank=True)
    kind = models.PositiveSmallIntegerField(
        choices=CategoryKindMixin.KIND_CHOICES,
        default=CategoryKindMixin.KIND_CATEGORY)
    custom_kind = models.ForeignKey('categories.CategoryType',
                                    related_name='categories',
                                    null=True, blank=True)
    objects = models.Manager()
    skills = QueryManager(kind=CategoryKindMixin.KIND_SKILL)
    categories = QueryManager(kind=CategoryKindMixin.KIND_CATEGORY)
    industries = QueryManager(kind=CategoryKindMixin.KIND_INDUSTRY)
    languages = QueryManager(kind=CategoryKindMixin.KIND_LANGUAGE)
    services = QueryManager(kind=CategoryKindMixin.KIND_SERVICE)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        unique_together = ('slug', 'kind',)
        ordering = ('slug',)

    class AutocompleteCreateForm(forms.Form):
        kind = forms.ChoiceField(choices=CategoryKindMixin.KIND_CHOICES)
        custom_kind = forms.IntegerField(required=False)

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.slug = slugify(self.name)
        return super(Category, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    @classmethod
    def can_create(self, user):
        return user.is_client or user.is_vendor

    @classmethod
    def create_for_autocomplete(cls, text, request):
        extra_data = request.GET
        form = cls.AutocompleteCreateForm(data=extra_data)
        if not form.is_valid():
            return {'errors': form.errors}
        kind = form.cleaned_data['kind']
        custom_kind = form.cleaned_data.get('custom_kind')
        custom_kind_obj = CategoryType.objects.filter(id=custom_kind).first()
        slug = slugify(text)
        if custom_kind_obj:
            item, created = cls.objects.get_or_create(slug=slug, kind=kind,
                                                      custom_kind=custom_kind_obj,
                                                      defaults={'name': text})
        else:
            item, created = cls.objects.get_or_create(slug=slug, kind=kind,
                                                      defaults={'name': text})
        return {'text': item.name, 'pk': item.pk}

    @classmethod
    def get_autocomplete_create_url(cls, extra_data=None):
        extra_data = extra_data or {}
        kind = extra_data['kind']
        custom_kind = extra_data.get('custom_kind')
        if not kind in [k[0] for k in cls.KIND_CHOICES]:
            raise ValueError('Not a valid choice for kind')
        ctype = ContentType.objects.get_for_model(cls)
        if custom_kind:
            return '{}?kind={}&custom_kind={}'.format(
                reverse('create_for_autocomplete', args=(ctype.id,)),
                kind, custom_kind)
        return '{}?kind={}'.format(
            reverse('create_for_autocomplete', args=(ctype.id,)),
            kind)

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "name__icontains",)

    def get_top_vendor(self):
        return self.vendors_custom.order_by('-proven_score')[0]


class SkillLevel(models.Model):
    label = models.CharField(max_length=256,
                             unique=True)
    slug = AutoSlugField(max_length=256,
                         populate_from='label',
                         unique=True)
    level = models.PositiveSmallIntegerField()

    def get_absolute_url(self):
        return reverse('client_settings:skill_levels:edit',
                       args=[self.id, ])

    class Meta:
        verbose_name = 'skill level'
        verbose_name_plural = 'skill levels'
        ordering = ('-level',)

    def __unicode__(self):
        return self.label

    def clean(self):
        if self.level > 10:
            raise ValidationError('Level must be 0 - 10')


@receiver(post_migrate)
def load_fixtures(**kwargs):
    if kwargs.get('app') == 'categories':
        from django.core.management import call_command
        call_command('loaddata',
                     'med_social/apps/categories/fixtures/categories.json')


class CategoryType(models.Model):
    label = models.CharField(max_length=256,
                             unique=True)
    slug = AutoSlugField(max_length=256,
                         populate_from='label',
                         unique=True)
    filter_enabled = models.BooleanField(default=False)
    vendor_editable = models.BooleanField(default=True)

    def __unicode__(self):
        return self.label
