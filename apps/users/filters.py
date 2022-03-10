from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q

import django_filters
from watson import search as watson

from med_social.utils import get_current_tenant, this_week, get_week_from_date

from categories.models import Category
from roles.models import Role
from vendors.models import Vendor
from locations.models import Location
from divisions.models import Division
from users.models import User


def text_search(qs, value):
    if value:
        return watson.filter(qs, value)
    else:
        return qs


def organization_filter(qs, value):
    if '-1' in value:
        return qs.exclude(vendor=None)
    if value:
        q = Q(vendor_id__in=value)
        if '0' in value:
            q = q | Q(vendor=None)
    else:
        return qs
    return qs.filter(q)


def kind_filter(qs, value):
    if value == str(User.KIND_CLIENT):
        return qs.filter(kind=User.KIND_CLIENT)
    elif value == str(User.KIND_VENDOR):
        return qs.filter(kind=User.KIND_VENDOR)
    return qs


def role_filter(qs, value):
    if value:
        return qs.filter(roles=value)
    return qs


class UserFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(action=text_search)
    organization = django_filters.MultipleChoiceFilter(
        action=organization_filter)
    roles = django_filters.ModelMultipleChoiceFilter(
        action=role_filter,
        queryset=Role.objects.all())
    kind = django_filters.ChoiceFilter(
        action=kind_filter,
        choices=User.KIND_CHOICES,
        initial=User.KIND_CLIENT
    )

    class Meta:
        model = get_user_model()
        fields = ['organization', 'roles', 'search']
        exclude_from_render = ['user', 'search']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(UserFilter, self).__init__(*args, **kwargs)
        self.filters['organization'].extra.update(
            {'choices': [('0', get_current_tenant().name),
                         ('-1', 'any')] +

             list(Vendor.objects.values_list('id', 'name'))})

        for fltr in self.filters.values():
            fltr.field.widget.attrs['selectize-placeholder'] = '{}...'.format(fltr.field.label)
