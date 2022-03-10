from datetime import date
from decimal import Decimal
from math import log
import urlparse

from dateutil.parser import parse

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from autoslug.fields import AutoSlugField
from picklefield.fields import PickledObjectField
from sorl.thumbnail import ImageField
from requests.exceptions import HTTPError

from vendors.utils import retrieve_clearbit_data


class Client(models.Model):
    SIZE_CHOICES = (
        (1, '1 - 5'),
        (2, '5 - 25'),
        (3, '25 - 50'),
        (4, '50 - 100'),
        (5, '100 - 1,000'),
        (6, '1,000 - 10,000'),
        (7, '10,000 - 100,000'),
        (8, '100,000+'),
    )
    REGISTRATION_TYPE = (
        ('public', 'Public'),
        ('private', 'Private'),
    )
    REGISTRATION_TYPE_SCORE = {'public': 10, 'private': 7}

    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='name', unique=True, null=True,
                         always_update=True)
    logo = ImageField(_('Client logo'), null=True, blank=True, upload_to=settings.COMPANY_LOGO_IMAGE_FOLDER)
    size = models.PositiveSmallIntegerField(null=True, choices=SIZE_CHOICES)
    industries = models.ManyToManyField('categories.Category', related_name='clients')
    created_by = models.ForeignKey('users.User', null=True, related_name='clients_created')

    is_partner = models.BooleanField(default=False)
    salesforce_token = models.CharField(max_length=255, null=True, blank=True)
    salesforce_instance = models.CharField(max_length=255, null=True, blank=True)
    users = models.ManyToManyField('users.User', related_name='clients')

    skills = models.ManyToManyField('categories.Category', related_name='client_skills')

    services = models.ManyToManyField('categories.Category', related_name='client_services')
    website = models.URLField(max_length=127, default='')
    email_domain = models.CharField(max_length=255, default='')

    clearbit_data = PickledObjectField(blank=True, null=True, editable=False)
    employee_count = models.PositiveIntegerField(blank=True, null=True, verbose_name='Employee Count')
    registration_type = models.CharField('Registration Type', choices=REGISTRATION_TYPE, blank=True, max_length=100)
    google_pagerank = models.PositiveIntegerField(blank=True, null=True, verbose_name='Google PageRank')
    alexa_rank = models.PositiveIntegerField(blank=True, null=True, verbose_name='Alexa Rank')
    twitter_followers = models.PositiveIntegerField(blank=True, null=True, verbose_name='Twitter Followers')
    market_cap = models.BigIntegerField(blank=True, null=True)
    annual_revenue = models.BigIntegerField(blank=True, null=True)
    founded_date = models.DateField(blank=True, null=True)
    client_quality_score = models.DecimalField('Client Quality Score', max_digits=5, decimal_places=2, blank=True, null=True, editable=False)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    @classmethod
    def can_create(cls, user):
        return True

    @classmethod
    def create_for_autocomplete(cls, text, request):
        from API.serializers.client_serializers import ClientSerializer
        item, created = cls.objects.get_or_create(
            name=text, created_by=request.user)
        data = {'text': item.name, 'pk': item.pk}
        data.update(ClientSerializer(item, context={'request': request}).data)
        return data

    @classmethod
    def get_autocomplete_create_url(cls, extra_data=None):
        ctype = ContentType.objects.get_for_model(cls)
        return reverse('create_for_autocomplete', args=(ctype.id,))

    def is_editable(self, user):
        return user.is_superuser or (self.created_by == user and not self.references.exists())

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
            if not self.founded_date and self.clearbit_data.get('foundedDate'):
                self.founded_date = parse(self.clearbit_data['foundedDate']).date()
            self.market_cap = self.market_cap or self.clearbit_data['metrics']['marketCap']
            self.annual_revenue = self.annual_revenue or self.clearbit_data['metrics']['annualRevenue']
            self.save()

    def client_quality_score_weighted(self):
        return (self.client_quality_score or 0) / Decimal(10)

    def compute_client_quality_score(self):
        data_points = []
        if self.employee_count is not None:
            data_points.append(self.score_employee_count())
        if self.registration_type is not None:
            data_points.append(self.score_registration_type())
        if self.google_pagerank is not None:
            data_points.append(self.score_google_pagerank())
        if self.alexa_rank is not None:
            data_points.append(self.score_alexa_rank())
        if self.twitter_followers is not None:
            data_points.append(self.score_twitter_followers())
        if self.market_cap is not None:
            data_points.append(self.score_market_cap())
        if self.annual_revenue is not None:
            data_points.append(self.score_annual_revenue())
        if self.founded_date is not None:
            data_points.append(self.score_company_age())
        self.client_quality_score = Decimal(sum(data_points)) / len(data_points) * 10 if data_points else 0
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

    def save(self, *args, **kwargs):
        created = not self.id
        super(Client, self).save(*args, **kwargs)
        if created:
            if not self.clearbit_data:
                self.sync_clearbit_data()
            self.copy_clearbit_data()
        if self.client_quality_score is None:
            self.compute_client_quality_score()
