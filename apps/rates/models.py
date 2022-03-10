from django.contrib.auth.models import Permission
from django.utils.html import mark_safe
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q

from aggregate_if import Count
from model_utils.managers import QueryManager

from locations.models import Location
from vendors.models import Vendor

HOUR = 2
DAY = 3
WEEK = 4
PERIOD_CHOICES = (
    (HOUR, 'per hour'),
    (DAY, 'per day'),
    (WEEK, 'per week'),
)

RATE_PERMISSIONS = (
    ('add', 'Can add/edit financial information', Permission.ALL, False),
    ('view', 'Can view financial information', Permission.ALL, False)
)


class Rate(models.Model):
    PERMISSIONS = RATE_PERMISSIONS

    cost = models.DecimalField(max_digits=10, decimal_places=0)

    location = models.ForeignKey(Location, null=True)
    skill_level = models.ForeignKey('categories.SkillLevel', null=True)
    unit = models.PositiveSmallIntegerField(choices=PERIOD_CHOICES,
                                            default=HOUR)
    role = models.ForeignKey('roles.Role', null=True)
    is_global = models.BooleanField(default=True)
    vendor = models.ForeignKey(Vendor,
                               null=True,
                               blank=True,
                               related_name='rates')
    user = models.OneToOneField('users.User',
                                null=True,
                                blank=True,
                                related_name='rate')

    objects = QueryManager()
    local_cards = QueryManager(is_global=False)
    global_cards = QueryManager(is_global=True)

    class Meta:
        verbose_name = 'rate'
        verbose_name_plural = 'rates'
        db_table = 'rates'
        unique_together = ('location', 'skill_level', 'role', 'vendor', 'user',
                           'is_global',)

    def __unicode__(self):
        return "{role}({skill}) @ {cost} {unit}".format(
            role=self.role,
            skill=self.skill_level,
            cost=self.cost,
            unit=self.get_unit_display(),
        )

    @property
    def rate(self):
        return "{cost} {unit}".format(
            cost=self.cost,
            unit=self.get_unit_display(),
        )

    @property
    def name(self):
        return "{location} - {skill_level} - {role}".format(
            skill_level=self.skill_level,
            role=self.role,
            location=self.location
        )

    @property
    def is_user_rate(self):
        return self.user is not None

    @property
    def is_vendor_rate(self):
        return self.vendor is not None

    @property
    def is_client_rate(self):
        return self.vendor is None

    @classmethod
    def get_suggested_rates(cls, **kwargs):
        # First try to fetch EXACT matches. If they don't exist, then fetch
        # suggestions.

        fields = {
            'location': 'location',
            'role': 'role',
            'skill_level': 'skill_level',
        }

        if not any(kwargs.values()):
            return cls.objects.none()

        exact_kwargs = {}
        for key, value in kwargs.items():
            if key in fields:
                exact_kwargs[fields[key]] = value
        qs = Rate.objects.filter(**exact_kwargs)

        if not qs.exists():
            filter_q = Q()
            aggregate_args = []
            order_keys = []
            for key, value in kwargs.items():
                if key in fields and value:
                    order_keys.append('-{}__count'.format(fields[key]))
                    q_kwargs = {fields[key]: value}
                    q = Q(**q_kwargs) | Q(**{key: None})
                    filter_q = filter_q & q
                    aggregate_args.append(Count(key, only=Q(**q_kwargs)))
            qs = cls.global_cards.filter(filter_q)\
                    .annotate(*aggregate_args).order_by(*order_keys)
        if kwargs.get('vendor'):
            qs = qs.filter(vendor=kwargs['vendor'])
        return qs

    def get_absolute_url(self):
        return reverse('rates:edit', args=(self.id,))

    def get_html(self):
        out = '{0} <small class="text-muted">per hour</small>'.format(
            self.cost
        )
        return mark_safe(out)
    get_html.allow_tags = True

    @property
    def is_fixed_rate(self):
        return False


class MockRate(object):
    """This is a wrapper object for where we need work with both rate model
    objects and normal decimal rates. This allows us to wrap decimal values
    so that we can do rate.cost, without a lot of if else juggling
    """

    def __init__(self, cost, is_fixed=True):
        self.cost = cost
        self.is_fixed = is_fixed

    @property
    def is_fixed_rate(self):
        return self.is_fixed
