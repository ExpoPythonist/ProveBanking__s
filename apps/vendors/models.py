# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import datetime
import urlparse
import uuid
from datetime import date, timedelta
from decimal import Decimal
from math import log, tanh
from logging import getLogger

from dateutil.parser import parse

from django.db import models
from django.db.models import Count, Q, Sum
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes import fields as generic
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.crypto import get_random_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django_pgjson.fields import JsonBField
from requests.exceptions import HTTPError

from rest_framework.renderers import JSONRenderer
from autoslug.fields import AutoSlugField
from simple_activity.decorators import register_model
from djorm_pgarray.fields import ArrayField, TextArrayField
from notifications.signals import notify
from phonenumber_field.modelfields import PhoneNumberField
from picklefield.fields import PickledObjectField
from post_office import mail
from sorl.thumbnail import ImageField
from model_utils import FieldTracker
from uuidfield import UUIDField

from med_social.utils import slugify
from med_social.utils import humanized_datetime
from med_social.utils import get_score_level
from med_social.utils import get_current_tenant

from categories.models import Category
from notes.models import Note
from reviews.db.fields import ReviewsField
from reviews.models import Review
from metrics.models import Metric, MetricAggregate

from .mixins import KindMixin
from .managers import VendorManager
from .utils import retrieve_clearbit_data


logger = getLogger(__name__)


def default_array():
    return []


class VendorType(models.Model):
    name = models.CharField(max_length=254)
    slug = models.TextField(null=True, blank=True, unique=True)

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.slug = slugify(self.name)
        return super(VendorType, self).save(*args, **kwargs)

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


class VendorKind(models.Model):
    name = models.CharField(max_length=254)
    slug = models.TextField(null=True, blank=True, unique=True)
    title = models.CharField(_('Title'), max_length=127, default='',
                             blank=True)

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.slug = slugify(self.name)
        return super(VendorKind, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name


def default_pending_steps():
    return Vendor.DEFAULT_PENDING_STEPS


def _default_vendor_meta():
    return {}


def default_json():
    return {}


@register_model()
class Vendor(models.Model, KindMixin):

    EDIT_PROFILE = 1
    EDIT_MEDIA = 2
    EDIT_PROJECT = 3
    EDIT_SERVICE = 4
    EDIT_SKILL = 5
    EDIT_ROLE = 6
    EDIT_LOCATION = 7
    EDIT_CLIENTS = 8
    EDIT_CERTS = 9
    EDIT_INSURANCE = 11
    EDIT_INDUSTRIES = 10

    SCORE_PROFILE = 5
    SCORE_MEDIA = 5
    SCORE_PROJECT = 5
    SCORE_SERVICE = 5
    SCORE_SKILL = 5
    SCORE_ROLE = 5
    SCORE_LOCATION = 5
    SCORE_CLIENTS = 5
    SCORE_CERTS = 5
    SCORE_INDUSTRIES = 5

    EDIT_STEPS = (
        (EDIT_PROFILE, 'vendor_profile',),
        (EDIT_MEDIA, 'vendor_media',),
        (EDIT_PROJECT, 'vendor_projects',),
        (EDIT_SERVICE, 'vendor_service',),
        (EDIT_SKILL, 'vendor_skill',),
        (EDIT_ROLE, 'vendor_role',),
        (EDIT_LOCATION, 'vendor_location',),
        (EDIT_CLIENTS, 'clients',),
        (EDIT_CERTS, 'certs',),
        (EDIT_INSURANCE, 'insurance',),
        (EDIT_INDUSTRIES, 'industries',),
    )

    DEFAULT_PENDING_STEPS = [EDIT_PROFILE, EDIT_MEDIA,
                             EDIT_PROJECT, EDIT_SERVICE,
                             EDIT_SKILL, EDIT_ROLE, EDIT_CLIENTS,
                             EDIT_CERTS, EDIT_INSURANCE,
                             EDIT_LOCATION]
    REGISTRATION_TYPE = (
        ('public', 'Public'),
        ('private', 'Private'),
    )
    REGISTRATION_TYPE_SCORE = {'public': 10, 'private': 7}

    search_template = 'vendors/search_result.html'

    PERMISSIONS = (
        ('invite_vendor', 'Can invite vendor', Permission.CLIENT, False),
        ('edit_vendor', 'Can edit company profile', Permission.VENDOR, True),
    )

    YEAR_CHOICES = []
    for r in range(datetime.datetime.now().year, 1899, -1):
        YEAR_CHOICES.append((r, r))

    objects = VendorManager()
    all_vendors = models.Manager()

    name = models.CharField(_('Company name'), max_length=255)
    type = models.ForeignKey(VendorType, related_name='vendors', null=True, blank=True)
    slug = AutoSlugField(populate_from='name', unique=True, manager=all_vendors)
    search_keywords = TextArrayField(default=default_array, blank=True, null=True)
    email = models.EmailField(_('Email'), blank=True)
    open_for_business = models.BooleanField(default=False)
    is_global = models.BooleanField(default=False)
    invited_by = models.ManyToManyField(
        'users.User', related_name='invited_vendors', through='VendorInvitation', through_fields=('vendor', 'user',))
    industries = models.ManyToManyField('categories.Category', related_name='companies')
    logo = ImageField(_('Company logo'), null=True, blank=True, upload_to=settings.COMPANY_LOGO_IMAGE_FOLDER)
    background = ImageField(
        _('Company background image'), null=True, blank=True, upload_to=settings.COMPANY_BACKGROUND_IMAGE_FOLDER)

    reviews = ReviewsField(Review, count_field=None)

    website = models.URLField(_('Website'), max_length=255, default='', blank=True)
    twitter = models.CharField(_('Twitter'), max_length=127, default='', blank=True)
    facebook = models.CharField(_('Facebook'), max_length=255, default='', blank=True)
    linkedin = models.CharField(_('Linkedin'), max_length=255, default='', blank=True)
    github = models.CharField(_('Github'), max_length=255, default='', blank=True)

    glassdoor = models.URLField(_('Glassdoor'), max_length=255, default='', blank=True)

    partner_since = models.DateField(null=True, blank=True)

    joined_on = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    locations = models.ManyToManyField('locations.Location', through='VendorLocation', related_name='vendors')

    summary = models.CharField(_('Summary'), max_length=500, default='', blank=True)

    roles = models.ManyToManyField('roles.Role', through='VendorRoles', related_name='vendors')

    categories = models.ManyToManyField('categories.Category', through='VendorCategories', related_name='vendors')

    story = models.TextField(max_length=1000, null=True, blank=True)
    phone = PhoneNumberField(null=True, blank=True)
    video = models.URLField(_('Youtube video'), max_length=255, default='', blank=True)
    founded = models.IntegerField(null=True, blank=True, choices=YEAR_CHOICES)

    brochure = models.FileField(null=True, blank=True, upload_to=settings.COMPANY_BROCHURE_FOLDER)

    pending_edit_steps = ArrayField(
        verbose_name=_('Pending steps'), default=default_pending_steps, dbtype="int", dimension=1)

    service = models.ManyToManyField('categories.Category', through='VendorServices', related_name='vendor_service')

    client_contact = models.ForeignKey('users.User', related_name='vendor_contact', null=True, blank=True)

    engage_process = models.TextField(max_length=500, null=True, blank=True)

    kind = models.PositiveSmallIntegerField(
        default=KindMixin.KIND_PROSPECTIVE, choices=KindMixin.KIND_CHOICES, blank=True)
    is_archived = models.BooleanField(default=False)

    contacts = models.ManyToManyField('users.User', blank=True, related_name='contacts')
    custom_categories = models.ManyToManyField(
        'categories.Category', through='VendorCustomKind', related_name='vendors_custom')

    notes = GenericRelation(Note)
    metric_owned = generic.GenericRelation(Metric, content_type_field='target_type', object_id_field='target_id')
    metric_aggregate = generic.GenericRelation(MetricAggregate)

    certs = models.ManyToManyField(
        'certs.Cert', related_name='vendors', through='CertVerification', through_fields=('vendor', 'cert'))
    clients = models.ManyToManyField(
        'clients.Client', related_name='vendors', through='ClientReference', through_fields=('vendor', 'client'))
    industries_served = models.ManyToManyField(
        'categories.Category', through='VendorIndustry', related_name='vendor_industry')
    address = models.TextField(default='', blank=True)
    score = models.PositiveIntegerField(default=0, blank=True, db_index=True)

    diversity = models.ManyToManyField('vendors.Diversity', related_name='diversity', blank=True)

    tin = models.CharField(default='', max_length=255, blank=True)
    duns = models.CharField(default='', max_length=255, blank=True)
    meta = JsonBField(default=_default_vendor_meta, blank=True)
    verifications = JsonBField(default=_default_vendor_meta, blank=True)
    has_onboarded = models.BooleanField(default=False)
    tracker = FieldTracker(fields=['modified_on', 'pending_edit_steps', 'score', 'kind', 'website', 'tin', 'duns'])

    clearbit_data = PickledObjectField(
        blank=True,
        null=True,
        editable=False
    )

    sync_clearbit = models.BooleanField(
        'Synced with clearbit',
        default=False,
        db_index=True
    )

    employee_count = models.PositiveIntegerField(blank=True, null=True, verbose_name='Employee Count')
    registration_type = models.CharField('Registration Type', choices=REGISTRATION_TYPE, blank=True, max_length=100)
    google_pagerank = models.PositiveIntegerField(blank=True, null=True, verbose_name='Google PageRank')
    alexa_rank = models.PositiveIntegerField(blank=True, null=True, verbose_name='Alexa Rank')
    twitter_followers = models.PositiveIntegerField(blank=True, null=True, verbose_name='Twitter Followers')
    market_cap = models.BigIntegerField(blank=True, null=True)
    annual_revenue = models.BigIntegerField(blank=True, null=True)
    founded_date = models.DateField(blank=True, null=True)

    potential_client_score = models.DecimalField(
        'Potential Client Score', max_digits=5, decimal_places=2, blank=True, null=True, editable=False)
    client_score = models.DecimalField(
        'Client Score', max_digits=5, decimal_places=2, blank=True, null=True, editable=False)
    company_score = models.DecimalField(
        'Company Score', max_digits=5, decimal_places=2, blank=True, null=True, editable=False)
    web_score = models.DecimalField(
        'Web Score', max_digits=5, decimal_places=2, blank=True, null=True, editable=False)
    potential_proven_score = models.DecimalField(
        'Potential Proven Score', max_digits=5, decimal_places=2, blank=True, null=True, editable=False)
    proven_score = models.DecimalField(
        'Proven Score', max_digits=5, decimal_places=2, blank=True, null=True, editable=False)

    premium = models.BooleanField('Proven Premium Vendor', default=False)

    class Meta:
        ordering = ('-open_for_business', '-proven_score')

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        from .tasks import calculate_rank
        tenant = get_current_tenant()
        if self.id:
            self.score_update()
            self.compute_proven_score(commit=False)
            calculate_rank.delay(tenant.id, self.id)
            self.score = self.calulate_weighted_score()
        created = not self.id
        super(Vendor, self).save(*args, **kwargs)
        if created:
            if not self.clearbit_data:
                self.sync_clearbit_data()
            self.copy_clearbit_data()
            self.compute_proven_score()

    def as_json(self):
        from API.serializers.vendor_serializers import VendorSerializer
        return JSONRenderer().render(VendorSerializer(self).data)

    def get_search_keywords(self):
        return self.search_keywords or ['"{}"'.format(self.name)]

    @classmethod
    def get_content_type(cls):
        return ContentType.objects.get_for_model(cls)

    @classmethod
    def get_content_type_id(cls):
        return ContentType.objects.get_for_model(cls).id

    @classmethod
    def get_suggested_vendors(cls, role=None, location=None, categories=None):
        if not any([role, location, categories]):
            return cls.objects.none()

        q = Q()

        if role:
            q = Q(roles=role)

        if location:
            q = q & (Q(locations=location) | Q(users__location=location))

        if categories:
            q = q & (Q(categories=categories) |
                     Q(users__categories=categories))
        return cls.objects.filter(q).distinct()

    @property
    def is_prospective(self):
        return self.kind == self.KIND_PROSPECTIVE

    @property
    def rank(self):
        if self.avg_score:
            return Vendor.objects.filter(avg_score__gt=self.avg_score).count() + 1
        else:
            return None

    @property
    def natural_created_date(self):
        return humanized_datetime(self.created)

    @property
    def natural_joined_date(self):
        return humanized_datetime(self.joined_on)

    def get_edit_url(self, step=EDIT_PROFILE):
        step = self.pending_edit_steps[0] if self.pending_edit_steps else step
        return reverse('user_setup:setup_step_%s' % dict(self.EDIT_STEPS)[step])

    def get_default_group(self, kind, name, display_name):
        group, created = self.groups.get_or_create(
            kind=kind, defaults={'name': name, 'display_name': display_name})
        if not created and (group.name != name or group.display_name != display_name):
            group.name = name
            group.display_name = display_name
            group.save()
        return group

    def get_admins_group(self):
        return self.get_default_group(Group.DEFAULT_ADMIN, '{}:admin'.format(self.id), 'Admin')

    def get_users_group(self):
        return self.get_default_group(Group.DEFAULT_USER, '{}:user'.format(self.id), 'User')

    def get_score_level(self):
        return get_score_level(self.avg_score)

    def get_absolute_url(self):
        primary_service = self.get_primary_service()
        if primary_service:
            return reverse('vendors:detail_new', args=(primary_service.category.slug, self.slug))
        return reverse('vendors:detail_new', args=(self.slug,))

    def get_clients_url(self):
        primary_service = self.get_primary_service()
        if primary_service:
            return reverse('vendors:client_list_new', args=(primary_service.category.slug, self.slug))
        return reverse('vendors:client_list_new', args=(self.slug,))

    def get_average_rating(self):
        return None

    def get_current_year_billing(self):
        return None

    def get_first_user(self):
        return self.users.filter(is_admin=True).earliest('id')

    def get_previously_hired_by(self):
        from projects.models import ProposedResourceStatus as PRS
        qs = (get_user_model().objects.filter(
                edited_resources__status__value=PRS.SUCCESS,
                edited_resources__resource__vendor=self) |
              get_user_model().objects.filter(
                owned_portfolio__vendor=self)).distinct()
        return qs

    def get_skills_and_people(self):
        return Category.objects.filter(
            users__in=self.users.values_list('pk', flat=True)
        ).annotate(Count('users'))

    def get_people(self):
        return self.users.all()[:3]

    def get_meta_counts(self):
        from projects.models import ProposedResourceStatus, Project
        PRS = ProposedResourceStatus
        rel_review_count = Review.objects.filter(content_object__in=self.portfolio.all()).count()
        counts = {}
        counts['reviews'] = self.reviews.count() + rel_review_count
        counts['projects'] = Project.objects.filter(
            proposals__resource__vendor=self,
            proposals__status__value=PRS.SUCCESS).distinct().count()
        counts['projects'] += PortfolioItem.objects.filter(
            vendor=self).count()
        return counts

    def get_notification_receivers(self):
        return list()

    def send_notification(self, created, recipient, **kwargs):
        sender = get_user_model().objects.get(id=kwargs.get('sender'))
        data = dict(sender=sender,
                    target=self,
                    description='',
                    recipient=recipient
                    )
        if created:
            data['verb'] = 'invited'
            notify.send(**data)

    def get_video_embed_url(self):
        o = urlparse.urlparse(self.video)
        if o.hostname in ('youtu.be', 'www.youtu.be'):
            return 'https://youtube.com/embed/%s' % o.path[1:]

        q = urlparse.parse_qs(o.query).get('v', [])
        if q:
            return 'https://youtube.com/embed/%s' % q[0]

    def get_primary_service(self):
        return self.vendor_custom.filter(primary=True).first()

    def score_update(self):
        score_obj, _ = Score.objects.get_or_create(vendor=self, kind=Score.KIND_PROFILE)
        score_obj.score = (9 - len(self.pending_edit_steps)) * 5
        score_obj.save()

    def calulate_weighted_score(self):
        score = Score.objects.filter(vendor=self)
        score_total = 0
        for obj in score:
            if obj.kind == Score.KIND_CLIENT:
                score_total = score_total + (obj.score * Score.WEIGHT_CLIENT)
            if obj.kind == Score.KIND_REVIEW:
                score_total = score_total + (obj.score * Score.WEIGHT_REVIEW)
            if obj.kind == Score.KIND_PROFILE:
                score_total = score_total + (obj.score * Score.WEIGHT_PROFILE)
            if obj.kind == Score.KIND_PROJECT:
                score_total = score_total + (obj.score * Score.WEIGHT_PROJECT)
            if obj.kind == Score.KIND_VENDOR_KIND:
                score_total = score_total + (obj.score * Score.WEIGHT_VENDOR_KIND)

        return int(score_total / 100)

    def get_total_primary(self):
        primary = self.get_primary_service()
        total_related_objs = VendorCustomKind.objects.filter(category=primary.category, primary=True).count()
        return total_related_objs

    def get_employee_count(self):
        count = VendorLocation.objects.filter(vendor=self).aggregate(Sum('num_resources')).get('num_resources__sum', 0)
        if count:
            return count
        return 0

    def brochure_extension(self):
        extension = None
        if self.brochure:
            name, extension = os.path.splitext(self.brochure.name)
            return extension.lower()
        return extension

    def brochure_filename(self):
        return os.path.basename(self.brochure.name)

    @property
    def domain(self):
        if 'http' in self.website:
            return urlparse.urlparse(self.website).netloc
        return self.website

    def sync_clearbit_data(self):
        if self.domain:
            try:
                self.clearbit_data = retrieve_clearbit_data(self.domain)
            except HTTPError:
                logger.exception("Couldn't get Clearbit data")
                self.clearbit_data = []
            self.save()

    def copy_clearbit_data(self):
        if self.clearbit_data:
            self.google_pagerank = self.google_pagerank or self.clearbit_data['metrics']['googleRank']
            self.alexa_rank = self.alexa_rank or self.clearbit_data['metrics']['alexaGlobalRank']
            self.employee_count = self.employee_count or self.clearbit_data['metrics']['employees']
            self.twitter_followers = self.twitter_followers or self.clearbit_data['twitter']['followers']
            if not self.registration_type:
                self.registration_type = 'public' if self.clearbit_data['type'] == 'public' else 'private'
            if not self.founded_date and self.clearbit_data['foundedDate']:
                self.founded_date = parse(self.clearbit_data['foundedDate']).date()
            self.market_cap = self.market_cap or self.clearbit_data['metrics']['marketCap']
            self.annual_revenue = self.annual_revenue or self.clearbit_data['metrics']['annualRevenue']
            self.save()

    def calculate_market_score(self):
        ALPHA_MARKET = 1
        if self.market_cap and self.annual_revenue:
            return 100 * tanh(float(self.market_cap) / float(self.annual_revenue) * ALPHA_MARKET)
        return 0

    def calculate_web_score(self):
        weight_google = 0.4
        weight_alexa = 0.3
        weight_twitter = 0.3
        alpha_alexa = 1.0 / 10000
        alpha_twitter = 1.0 / 1000

        web_score = 0
        if self.google_pagerank is not None:
            web_score += weight_google * float(self.google_pagerank) * 10
        if self.alexa_rank is not None:
            web_score += 100 * weight_alexa * tanh(float(self.alexa_rank) * alpha_alexa)
        if self.twitter_followers is not None:
            web_score += 100 * weight_twitter * tanh(float(self.twitter_followers) * alpha_twitter)
        return web_score

    def calculate_feedback_score(self):
        return 0

    def calculate_client_score(self):
        BILLING_VALUES = [
            0, 1000, 5000, 10000, 20000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 50000000, 10000000]
        DURATION_VALUES = [0.1, 0.5, 2, 4, 7.5, 10]
        # ALPHA_CLIENTS = 1000.0

        client_references = self.client_references_verified()
        contracts_per_year_and_revenue = []
        for reference in client_references:
            if reference.get_billing_value() is not None and reference.get_duration_value() is not None:
                contracts_per_year_and_revenue.append([
                    float(BILLING_VALUES[int(reference.get_billing_value())]) /
                    float(DURATION_VALUES[int(reference.get_duration_value())]) or 10,
                    # float(reference.client.annual_revenue)
                ])
        '''
        sum_of_contracts = sum(contract[0] for contract in contracts_per_year_and_revenue)
        sum_weighted = sum(
            contract[0] * tanh(len(contracts_per_year_and_revenue) * ALPHA_CLIENTS * contract[0] / contract[1])
            for contract in contracts_per_year_and_revenue
        )
        client_score = 100 * sum_weighted / sum_of_contracts if sum_of_contracts else 0
        '''
        client_score = 100 * tanh(len(contracts_per_year_and_revenue) / 25.0)
        return client_score

    def calculate_industry_score(self):
        ALPHA_INDUSTRY = 1.0
        total_billings = self.total_billings()
        if total_billings:
            return 100 * tanh(ALPHA_INDUSTRY * total_billings / ClientReference.industry_mean())
        return 0

    def total_billings(self):
        client_references = self.client_references_verified()
        billings = []
        for reference in client_references:
            if reference.get_billing_value() is not None:
                billings.append(float(reference.get_billing_value()))
        return min(sum(billings), ClientReference.BILLING_CHOICES_NEW[-1][0])

    def total_billings_display(self):
        return ClientReference.BILLING_CHOICES_NEW[int(self.total_billings()) - 1][1]

    def industry_mean_display(self):
        return ClientReference.industry_mean_display()

    def calculate_proven_score(self):
        customer = get_current_tenant()
        return (
            self.calculate_market_score() * customer.weight_market / 100 +
            self.calculate_web_score() * customer.weight_web / 100 +
            self.calculate_industry_score() * customer.weight_industry / 100 +
            self.calculate_client_score() * customer.weight_clients / 100 +
            self.calculate_feedback_score() * customer.weight_feedback / 100
        )

    def compute_proven_score(self, commit=True):
        old_proven_score = self.proven_score
        self.proven_score = self.calculate_proven_score()
        '''
        self.sum_potential_weighted_scores(commit)
        self.sum_weighted_scores(commit=commit)
        self.compute_company_score(commit)
        self.compute_web_score(commit)

        self.potential_proven_score = min((
            float(self.potential_client_score) / 10 * 93 +
            float(self.company_score) * 5 +
            float(self.web_score) * 2
        ) / 10, 100)
        self.proven_score = min((
            float(self.client_score) / 10 * 93 +
            float(self.company_score) * 5 +
            float(self.web_score) * 2
        ) / 10, 100)
        print self.potential_proven_score, self.proven_score
        '''

        print old_proven_score, self.proven_score
        if commit and old_proven_score != self.proven_score:
            self.save()

    def sum_potential_weighted_scores(self, commit=True):
        client_references = self.client_references.all()

        client_scores = []
        for reference in client_references:
            client_scores.append(reference.weighted_value())
        self.potential_client_score = min(max(client_scores) / 4 + sum(client_scores) / 20, 100) if client_scores else 0

        if commit:
            self.save()

    def client_references_verified(self, commit=True):
        return self.client_references.filter(is_fulfilled=True)

    def sum_weighted_scores(self, all_clients=False, commit=True):
        client_references = self.client_references_verified()

        client_scores = []
        for reference in client_references:
            client_scores.append(reference.weighted_value())
        self.client_score = min(max(client_scores) / 4 + sum(client_scores) / 20, 100) if client_scores else 0

        if commit:
            self.save()

    def compute_company_score(self, commit=True):
        good_points = []
        if self.employee_count is not None:
            good_points.append(self.score_employee_count())
        if self.registration_type is not None:
            good_points.append(self.score_registration_type())
        if self.market_cap is not None:
            good_points.append(self.score_market_cap())
        if self.annual_revenue is not None:
            good_points.append(self.score_annual_revenue())
        if self.founded_date is not None:
            good_points.append(self.score_company_age())
        self.company_score = Decimal(sum(good_points)) / len(good_points) if good_points else 0

        if commit:
            self.save()

    def compute_web_score(self, commit=True):
        mini_points = []
        if self.google_pagerank is not None:
            mini_points.append(self.score_google_pagerank())
        if self.alexa_rank is not None:
            mini_points.append(self.score_alexa_rank())
        if self.twitter_followers is not None:
            mini_points.append(self.score_twitter_followers())
        self.web_score = Decimal(sum(mini_points)) / len(mini_points) if mini_points else 0

        if commit:
            self.save()

    def score_employee_count(self):
        return 0 if not self.employee_count else min(int(log(self.employee_count)), 10)

    def score_registration_type(self):
        return self.REGISTRATION_TYPE_SCORE.get(self.registration_type, 0)

    def score_google_pagerank(self):
        return 0 if not self.google_pagerank else self.google_pagerank

    def score_alexa_rank(self):
        return max(int(10 - log(self.alexa_rank, 10)), 0)

    def score_twitter_followers(self):
        return 0 if not self.twitter_followers else min(int(log(self.twitter_followers, 5)), 10)

    def score_market_cap(self):
        return 0 if not self.market_cap else min(int(log(self.market_cap)), 10)

    def score_annual_revenue(self):
        return 0 if not self.annual_revenue else min(int(log(self.annual_revenue)), 10)

    def score_company_age(self):
        return 0 if not self.founded_date else min(int(log((date.today() - self.founded_date).days, 2)), 10)

    def user_emails(self):
        return self.users.values_list('email', flat=True)


class ProcurementContact(models.Model):
    user = models.OneToOneField('users.User', related_name='procurement_contacts')
    vendors = models.ManyToManyField('vendors.Vendor', blank=True, related_name='procurement_contacts')
    categories = models.ManyToManyField('categories.Category', blank=True, related_name='procurement_contacts')
    locations = models.ManyToManyField('locations.Location', blank=True, related_name='procurement_contacts')
    always_show = models.BooleanField(default=False)

    def __unicode__(self):
        return 'Procurement Contact: {}'.format(self.user.get_name_display())


class VendorInvitation(models.Model):
    vendor = models.ForeignKey(Vendor, related_name='vendor_invitations')
    owner = models.ForeignKey('users.User', related_name='vendor_invitations', null=True, blank=True)

    user = models.ForeignKey('users.User', null=True, related_name='invited_vendor_invitations', blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('vendor', 'user',),)

    @classmethod
    def create_with_owner(cls, name, website, email):
        from users.utils import generate_unique_username
        username = generate_unique_username([email.split('@')[0]])
        owner, _ = get_user_model().objects.get_or_create(email=email, defaults={'username': username})
        owner.kind = get_user_model().KIND_VENDOR
        owner.save()
        '''
        password = get_user_model().objects.make_random_password()
        owner.set_password(password)
        owner.save()
        '''

        if website:
            vendor, created = Vendor.objects.get_or_create(website=website, defaults={'name': name, 'email': email})
        else:
            vendor, created = Vendor.objects.get_or_create(email=email, defaults={'name': name})
        if not created:
            vendor.name = name
            vendor.save()
        vendor.users.add(owner)
        return vendor, owner

    def save(self, *args, **kwargs):
        from activity.models import Action
        super(VendorInvitation, self).save(*args, **kwargs)
        if self.user:
            Action.add_action_invite(self.user, self.vendor)

    def create_invite_email(self):
        expires_at = now() + timedelta(days=7)
        invite, _ = self.owner.invitations.get_or_create(
            sender=self.user, receiver=self.owner, defaults={'expires_at': expires_at})
        invite.expires_at = expires_at
        invite.save()
        return invite

    def send_invite_email(self, invite):
        from .tasks import vendor_invite
        tenant = get_current_tenant()
        vendor_invite.delay(tenant_id=tenant.pk, invite_id=invite.pk)


class VendorLocation(models.Model):
    vendor = models.ForeignKey(Vendor, related_name='vendor_locations')
    location = models.ForeignKey('locations.Location')
    num_resources = models.PositiveIntegerField(_('Number of employees'), default=1)

    class Meta:
        unique_together = (('vendor', 'location',),)
        ordering = ('-num_resources', 'location',)


class VendorRoles(models.Model):
    vendor = models.ForeignKey(Vendor, related_name='vendor_roles')
    role = models.ForeignKey('roles.Role')
    allocation = models.PositiveSmallIntegerField(_('Role percentage'), default=0)

    class Meta:
        unique_together = (('vendor', 'role',),)
        ordering = ('role',)


class VendorCategories(models.Model):
    vendor = models.ForeignKey(Vendor, related_name='vendor_skills')
    skill = models.ForeignKey('categories.Category')
    allocation = models.PositiveSmallIntegerField(_('Skill percentage'), default=0)

    class Meta:
        unique_together = (('vendor', 'skill',),)
        ordering = ('-allocation',)


class VendorServices(models.Model):

    vendor = models.ForeignKey(Vendor, related_name='vendor_services')
    service = models.ForeignKey('categories.Category')
    allocation = models.PositiveSmallIntegerField(_('Service percentage'), default=0)

    class Meta:
        unique_together = (('vendor', 'service',),)
        ordering = ('service',)


class PortfolioItem(models.Model):
    vendor = models.ForeignKey(Vendor, related_name='portfolio')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owners = models.ManyToManyField('users.User', related_name='owned_portfolio', blank=True)
    locations = models.ManyToManyField('locations.Location', related_name='portfolio', blank=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True, blank=True)
    skills = models.ManyToManyField(Category, related_name='portfolio')
    reviews = ReviewsField(Review, average_field=None, count_field=None)

    def __unicode__(self):
        return self.title

    def get_kind_name(self):
        return 'portfolio'

    def score_update(self):
        score_obj, _ = Score.objects.get_or_create(vendor=self.vendor, kind=Score.KIND_PROJECT)
        score_with_owners = PortfolioItem.objects.filter(vendor=self.vendor).exclude(owners=None).count() * 5
        score_without_owners = PortfolioItem.objects.filter(vendor=self.vendor, owners=None).count()
        score_obj.score = score_with_owners + score_without_owners
        score_obj.save()
        self.vendor.save()


class VendorScoreAggregate(models.Model):
    vendor = models.OneToOneField(Vendor, related_name='score_aggregate')
    acceptance_rate = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    response_time = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    user_rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)


class VendorIndustry(models.Model):
    vendor = models.ForeignKey(Vendor, related_name='vendor_industries')
    industry = models.ForeignKey('categories.Category')
    allocation = models.PositiveSmallIntegerField(_('Industry percentage'), default=1)

    class Meta:
        unique_together = (('vendor', 'industry',),)
        ordering = ('industry',)


class ClientReference(models.Model):
    DURATION_CHOICES = (
        (1, 'less than 1 year'),
        (2, '1 - 3 years'),
        (3, '3 - 5 years'),
        (4, '5 - 10 years'),
        (5, '10+ years'),
    )

    BILLING_CHOICES = (
        (1, '$0 - $10K'),
        (2, '$10 - $50K'),
        (3, '$50 - $100K'),
        (4, '$100K - $500k'),
        (5, '$500K - $1M'),
        (6, '$1M - $5M'),
        (7, '$5M - $10M'),
        (8, '$10M+'),
    )
    BILLING_RANGES = (
        (1, (0, 10000)),
        (2, (10000, 50000)),
        (3, (50000, 100000)),
        (4, (100000, 500000)),
        (5, (500000, 1000000)),
        (6, (1000000, 5000000)),
        (7, (5000000, 10000000)),
        (8, (10000000, None)),
    )
    BILLING_MAPPING = {1: 1, 2: 4, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 11}
    BILLING_CHOICES_NEW = (
        (1, '<$1k'),
        (2, '$1K - $5K'),
        (3, '$5K - $10K'),
        (4, '$10K - $20K'),
        (5, '$20K - $50K'),
        (6, '$50K - $100K'),
        (7, '$100K - $500K'),
        (8, '$500K - $1M'),
        (9, '$1M - $5M'),
        (10, '$5M - $10M'),
        (11, '$10M - $50M'),
        (12, '$50M+'),
    )
    BILLING_RANGES_NEW = (
        (1, (0, 1000)),
        (2, (1000, 5000)),
        (3, (5000, 10000)),
        (4, (10000, 20000)),
        (5, (20000, 50000)),
        (6, (50000, 100000)),
        (7, (100000, 500000)),
        (8, (500000, 1000000)),
        (9, (1000000, 5000000)),
        (10, (5000000, 10000000)),
        (11, (10000000, 50000000)),
        (12, (50000000, None)),
    )
    DURATION_RANGES = (
        (1, (0, 360)),
        (2, (360, 360 * 3)),
        (3, (360 * 3, 360 * 5)),
        (4, (360 * 5, 360 * 10)),
        (5, (360 * 10, None)),
    )

    DEFAULT_EMAIL_MSG = (
        '{full_name} is using Proven to help verify that you are a client of'
        ' {vendor}.\nProven is a community of top professional services firms'
        ' built on trust and reputation of their clients. This information '
        'will help {vendor} to be trusted by new clients.\nWould you mind '
        'verifying that you are a client of {vendor} ? You do not have to '
        'share your company details if you don\'t want to, and your private '
        'information (name, email address) will never be shared without your '
        'permission.')

    vendor = models.ForeignKey(Vendor, related_name='client_references')
    client = models.ForeignKey('clients.Client', related_name='references')
    email = models.EmailField(null=True)
    email_msg = models.TextField(max_length=1000)
    alt_name = models.CharField(max_length=255, null=True)
    use_alt_name = models.BooleanField(default=False)
    billing = models.PositiveSmallIntegerField(null=True, blank=True, choices=BILLING_CHOICES)
    billing_new = models.PositiveSmallIntegerField(null=True, blank=True, choices=BILLING_CHOICES_NEW)
    billing_private = models.BooleanField(default=False)
    duration = models.PositiveSmallIntegerField(choices=DURATION_CHOICES, default=1)
    duration_private = models.BooleanField(default=False)
    has_ended = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=2, decimal_places=1, null=True)
    review = models.TextField(null=True, blank=True)
    review_anonymous = models.BooleanField(default=False)
    role = models.CharField(max_length=255, null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    token = models.CharField(max_length=40)
    is_fulfilled = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    last_sent = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('users.User', related_name='client_references')
    tracker = FieldTracker(fields=['is_fulfilled', 'email'])
    is_enabled = models.BooleanField(default=False)
    anonymous = models.BooleanField(default=False)

    invoice_verification = models.BooleanField(default=False)
    proof_url = models.URLField(max_length=255, default='', blank=True)

    class Meta:
        ordering = ('-is_fulfilled', '-client__client_quality_score')

    def get_absolute_url(self):
        return reverse('vendors:client_view', args=(self.vendor.slug, self.id,))

    @property
    def display_name(self):
        if self.use_alt_name:
            return self.alt_name
        return self.client.name

    @property
    def is_expired(self):
        return (now() - self.last_sent).days > 7

    def __unicode__(self):
        return '"{}" for "{}"'.format(self.client.name, self.vendor.name)

    def save(self, *args, **kwargs):
        if self.id is None:
            self.token = get_random_string(40)
        super(ClientReference, self).save(*args, **kwargs)

    def invoices_unapproved(self):
        return self.invoices.filter(date_verified=None)

    def score_update(self):
        '''
        score_obj, _ = Score.objects.get_or_create(vendor=self.vendor, kind=Score.KIND_CLIENT)
        verified = ClientReference.objects.filter(vendor=self.vendor, is_fulfilled=True).count()
        unverified = ClientReference.objects.filter(vendor=self.vendor, is_fulfilled=False).count()

        score_obj.score = unverified + (verified * 5)
        score_obj.save()
        self.vendor.save()
        '''
        self.vendor.compute_proven_score()

    def weighted_value(self):
        return int((
            self.client.client_quality_score_weighted() * 20 +
            (self.get_billing_value() or 0) * Decimal(1.2) * 60 +
            (self.get_duration_value() or 0) * 2 * 20
        ) / 10)

    def invoice_total(self, verified=False):
        if verified:
            return self.invoices.filter(
                date_verified__isnull=False).aggregate(total=models.Sum('invoice_amount'))['total']
        else:
            return self.invoices.aggregate(total=models.Sum('invoice_amount'))['total']

    def get_billing_value(self):
        if not self.invoices.exists():
            return self.billing_new

        total_billing = self.invoice_total(verified=True)
        if total_billing:
            for score, values in self.BILLING_RANGES:
                low, high = values
                if total_billing < high:
                    extra = Decimal(total_billing - low) / (high - low)
                    return score + extra
            return score  # will reach this when value hits the top limit
        return 0

    def get_duration_value(self):
        if not self.invoices.exists():
            return self.duration

        total_duration = self.invoices.filter(
            date_verified__isnull=False).aggregate(total=models.Sum('invoice_duration'))['total']
        if total_duration:
            for score, values in self.DURATION_RANGES:
                low, high = values
                if total_duration < high:
                    extra = Decimal(total_duration - low) / (high - low)
                    return score + extra
            return score  # will reach this when value hits the top limit
        return 0

    @classmethod
    def industry_mean(cls):
        industry_billings = []
        for reference in cls.objects.filter(is_fulfilled=True, billing_new__isnull=False):
            industry_billings.append(float(reference.billing_new))
        industry_mean = sum(industry_billings) / len(industry_billings) if industry_billings else 0
        return industry_mean

    @classmethod
    def industry_mean_display(cls):
        return cls.BILLING_CHOICES_NEW[int(cls.industry_mean()) - 1][1]

    def send_verification_email(self):
        tenant = get_current_tenant()
        context = {
            'community_url': tenant.get_full_url(),
            'proven_score_enabled': True,
            'reference': self
        }
        mail.send(
            list(self.vendor.user_emails()),
            template='Client Verified',
            context=context
        )

    def send_rejection_email(self):
        tenant = get_current_tenant()
        community_url = tenant and tenant.get_full_url()
        context = {
            'reference': self,
            'community_url': community_url,
        }
        mail.send(
            list(self.vendor.user_emails()),
            template='URL Rejected',
            context=context
        )

    def send_admin_email(self):
        tenant = get_current_tenant()
        mail.send(
            settings.VERIFICATION_REVIEWERS,
            template='New Proof to Verify', context={'reference': self, 'community_url': tenant.get_full_url()},
        )

    def get_absolute_url(self):
        return reverse('vendors:client_added', args=(self.vendor.id, self.id,))

    def pending_verification(self):
        return self.email or self.invoices.all() or self.proof_url


@python_2_unicode_compatible
class Invoice(models.Model):
    DURATION_CHOICES = (
        (1, '1 day+'),
        (7, '1 week+'),
        (30, '1 month+'),
        (30 * 3, '3 months+'),
        (30 * 6, '6 months+'),
        (360, '1 year+'),
        (540, '1.5 years+'),
        (360 * 2, '2 years+'),
        (360 * 3, '3 years+'),
        (360 * 4, '4 years+'),
        (360 * 5, '5 years+'),
    )
    reference = models.ForeignKey(ClientReference, related_name='invoices')

    invoice = models.FileField('Proof', upload_to='client-invoices', blank=True, null=True)
    invoice_amount = models.DecimalField('Invoice Amount', max_digits=20, decimal_places=2, null=True)
    invoice_date = models.DateField(null=True, blank=True)

    # DEPRECATED
    invoice_duration = models.IntegerField('Contract Duration', choices=DURATION_CHOICES, null=True)
    invoice_date_start = models.DateField(null=True)
    invoice_date_end = models.DateField(blank=True, null=True)

    date_verified = models.DateTimeField(blank=True, null=True)
    tracker = FieldTracker(fields=['date_verified'])

    uuid = UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_deleted = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ('date_verified', '-date_created')

    def __str__(self):
        return '{} | Invoice #{}'.format(self.reference, self.uuid)

    def is_image(self):
        invoice_url = self.invoice.url
        return not invoice_url.endswith('pdf')
        # return imghdr.what(self.invoice.path) is not None  # TODO: Does not work with urls

    def get_absolute_url(self):
        return reverse('vendors:client_added', args=(self.reference.vendor.id, self.reference.id,))

    def send_admin_email(self):
        tenant = get_current_tenant()
        mail.send(
            settings.VERIFICATION_REVIEWERS,
            template='New Invoice to Verify', context={'invoice': self, 'community_url': tenant.get_full_url()},
        )

    def send_verification_email(self):
        tenant = get_current_tenant()
        if not self.reference.is_fulfilled:
            self.reference.is_fulfilled = True
        self.reference.save()
        mail.send(
            list(self.reference.vendor.users.values_list('email', flat=True)),
            template='Invoice Verified', context={
                'invoice': self,
                'community_url': tenant.get_full_url(),
                'proven_score_enabled': True,
            },
        )


class CertVerification(models.Model):
    YEAR_CHOICES = []
    for r in range(datetime.datetime.now().year, 1899, -1):
        YEAR_CHOICES.append((r, r))

    DEFAULT_EMAIL_MSG = (
        '{full_name} from {vendor} has requested that you verify that '
        'they received certification from you. Please click here to verify '
        'that this is the case.'
    )

    vendor = models.ForeignKey(Vendor, related_name='cert_verifications')
    cert = models.ForeignKey('certs.Cert')
    url = models.URLField(max_length=255, default='', blank=True)
    email = models.EmailField(null=True, blank=True)
    email_msg = models.TextField(max_length=1000, null=True, blank=True)
    since = models.IntegerField(null=True, choices=YEAR_CHOICES)
    token = models.CharField(max_length=40)
    is_fulfilled = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.User', related_name='cert_verifications')
    tracker = FieldTracker(fields=['is_fulfilled', 'is_verified'])
    date_awarded = models.DateField(null=True, blank=True)
    attached_file = models.FileField(null=True, blank=True, upload_to='certs/')

    def __unicode__(self):
        return '"{}" for "{}"'.format(self.cert.name, self.vendor.name)

    @property
    def is_expired(self):
        return (now() - self.created).days > 7

    def save(self, *args, **kwargs):
        if self.id is None:
            self.token = get_random_string(40)
        super(CertVerification, self).save(*args, **kwargs)


class InsuranceVerification(models.Model):
    YEAR_CHOICES = []
    for r in range(datetime.datetime.now().year, 1899, -1):
        YEAR_CHOICES.append((r, r))

    DEFAULT_EMAIL_MSG = (
        '{full_name} from {vendor} has requested that you verify that '
        'they received insurance from you. Please click here to verify '
        'that this is the case.'
    )
    EXTENT_CHOICES = (
        (1, u'€2.6 million'),
        (2, u'€6.5 million'),
        (3, u'Other (please specify)'),
    )

    vendor = models.ForeignKey(Vendor, related_name='insurance_verifications')
    insurance = models.ForeignKey('certs.Cert')
    extent = models.IntegerField(null=True, choices=EXTENT_CHOICES)
    expiry_date = models.DateField(null=True, blank=True)

    policy_document = models.FileField(null=True, blank=True, upload_to=settings.INSURANCE_FOLDER)
    url = models.URLField(max_length=255, default='', blank=True)
    email = models.EmailField(null=True, blank=True)
    email_msg = models.TextField(max_length=1000, null=True, blank=True)

    token = models.CharField(max_length=40)
    is_fulfilled = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.User', related_name='insurance_verifications')
    tracker = FieldTracker(fields=['is_fulfilled', 'is_verified'])

    def __unicode__(self):
        return '"{}" for "{}"'.format(self.insurance.name, self.vendor.name)

    @property
    def is_expired(self):
        return (now() - self.created).days > 7

    def save(self, *args, **kwargs):
        if self.id is None:
            self.token = get_random_string(40)
        super(InsuranceVerification, self).save(*args, **kwargs)


class VendorCustomKind(models.Model):
    vendor = models.ForeignKey(Vendor, related_name='vendor_custom')
    category = models.ForeignKey('categories.Category', related_name='custom_kind_obj')
    allocation = models.PositiveSmallIntegerField(_('Category percentage'), default=0)
    rank = models.PositiveIntegerField(null=True, blank=True)
    primary = models.BooleanField(default=False)
    tracker = FieldTracker(fields=['primary'])

    class Meta:
        unique_together = (('vendor', 'category',),)
        ordering = ('-primary', '-allocation')


class Score(models.Model):

    KIND_REVIEW = 1
    KIND_CLIENT = 2
    KIND_PROFILE = 3
    KIND_PROJECT = 4
    KIND_VENDOR_KIND = 5

    WEIGHT_REVIEW = 40
    WEIGHT_CLIENT = 50
    WEIGHT_PROFILE = 10
    WEIGHT_PROJECT = 40
    WEIGHT_VENDOR_KIND = 100

    KIND_CHOICES = (
        (KIND_REVIEW, 'Review'),
        (KIND_CLIENT, 'Client'),
        (KIND_PROFILE, 'Profile'),
        (KIND_PROJECT, 'Project'),
        (KIND_VENDOR_KIND, 'VendorKind'),
    )

    vendor = models.ForeignKey('vendors.Vendor', related_name='score_obj')
    kind = models.PositiveSmallIntegerField(choices=KIND_CHOICES)
    score = models.DecimalField(max_digits=6,
                                decimal_places=1,
                                default=Decimal('0.0'))

    class Meta:
        unique_together = (("kind", "vendor"), )


class ProcurementLink(models.Model):
    vendor = models.OneToOneField(Vendor, related_name="procurement_link")
    description = models.TextField(default='')
    url = models.URLField(default='', blank=True)


class KindLabel(models.Model):
    label = models.CharField(max_length=256, unique=True)
    slug = AutoSlugField(max_length=256, populate_from='label', unique=True)
    kind = models.PositiveSmallIntegerField(choices=Vendor.KIND_CHOICES, unique=True)
    description = models.CharField(max_length=200, default='', blank=True)
    show_label = models.BooleanField(default=True, blank=True)
    filter_default = models.BooleanField(default=True, blank=True)

    def __unicode__(self):
        return self.label


class Diversity(models.Model):

    KIND_OWNERSHIP = 1
    KIND_EMPLOYEES = 2

    KIND_CHOICES = (
        (KIND_OWNERSHIP, 'Ownership'),
        (KIND_EMPLOYEES, 'Employees'),
    )

    kind = models.PositiveSmallIntegerField(choices=KIND_CHOICES)
    label = models.CharField(max_length=256,
                             unique=True)
    slug = AutoSlugField(max_length=256,
                         populate_from='label',
                         unique=True)

    def __unicode__(self):
        return self.label


class VendorWhois(models.Model):
    vendor = models.OneToOneField('vendors.Vendor', related_name='whois')
    domain = models.CharField(default='', blank=True, max_length=254)
    email = models.EmailField(null=True, blank=True)
    registrant = models.CharField(null=True, blank=True, max_length=254)
    created_on = models.DateTimeField(null=True, blank=True)
    expires_on = models.DateTimeField(null=True, blank=True)
    address = models.CharField(null=True, blank=True, max_length=254)
    phone = models.CharField(null=True, blank=True, max_length=254)
    social_handles = JsonBField(default=default_json, blank=True)
    metrics = JsonBField(default=default_json, blank=True)


class VendorClaim(models.Model):
    email = models.EmailField()
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    user = models.ForeignKey('users.User', related_name='vendor_claims', null=True, blank=True)
    vendor = models.ForeignKey(Vendor, related_name='claims')
    notes = models.TextField(blank=True)

    approved = models.NullBooleanField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '{}: {}'.format(self.user, self.vendor)

    def save(self, *args, **kwargs):
        created = not self.pk
        super(VendorClaim, self).save(*args, **kwargs)
        if created:
            self.send_admin_email()

    def send_admin_email(self):
        tenant = get_current_tenant()
        mail.send(
            ['phil@proven.cc', 'suzanne@proven.cc', 'kevin@proven.cc'],
            template='New Vendor Claim', context={'vendor_claim': self, 'community': tenant},
        )

    def create_user_and_invite(self):
        from users.models import User, UserInvitation
        from users.utils import generate_unique_username
        if not self.user:
            try:
                user = get_user_model().objects.get(email=self.email)
                invite = None
            except get_user_model().DoesNotExist:
                username = generate_unique_username([self.email])
                user = get_user_model().objects.get_or_create(
                    username=username, email=self.email,
                    defaults=dict(
                        first_name=self.first_name, last_name=self.last_name, kind=get_user_model().KIND_VENDOR,
                        last_login=now(),
                    )
                )[0]
                invite = UserInvitation.objects.get_or_create(receiver=user, defaults=dict(
                    expires_at=now() + timedelta(days=7)
                ))[0]
                invite.expires_at = now() + timedelta(days=7)
                invite.save()

            self.user = user
            self.save()
            return invite

    def send_approved_email(self, invite):
        tenant = get_current_tenant()
        mail.send(
            self.email,
            template='Vendor Claim Approved', context={'claim': self, 'community': tenant, 'invite': invite},
        )

    def send_rejected_email(self):
        tenant = get_current_tenant()
        mail.send(
            self.email, template='Vendor Claim Rejected', context={'claim': self, 'community': tenant},
        )

    class Meta:
        ordering = ('-created_on',)


class ClientQueue(models.Model):
    email = models.EmailField(_('Your Email'))
    notes = models.TextField(_('More Information'), blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.email

    def save(self, *args, **kwargs):
        created = not self.pk
        super(ClientQueue, self).save(*args, **kwargs)
        if created:
            mail.send(
                ['phil@proven.cc', 'suzanne@proven.cc', 'kevin@proven.cc'],
                template='New Community Request', context={'client_queue': self},
            )
            mail.send(self.email, template='New Community Request Autoresponder')

    class Meta:
        verbose_name = 'Community Request'
        verbose_name_plural = 'Community Requests'
        ordering = ('-created_on',)


from .rfp_models import RFP, Bid, Message
