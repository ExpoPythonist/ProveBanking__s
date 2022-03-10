from django.db.models import Q
from django.contrib.auth import get_user_model

import django_filters
from watson import search as watson

from locations.models import Location
from categories.models import Category
from roles.models import Role
from divisions.models import Division
from .models import StaffingRequest, Project


class StaffingFilter(django_filters.FilterSet):
    def text_search(qs, value):
        return watson.filter(qs, value)

    search = django_filters.CharFilter(action=text_search)

    class Meta:
        model = StaffingRequest
        fields = ['project', 'location', 'categories', 'role']


class ProjectFilter(django_filters.FilterSet):
    def project_text_search(qs, value):
        return watson.filter(qs, value)

    def role_search(qs, value):
        if value:
            return qs.filter(staffing_requests__role=value)
        else:
            return qs

    def categories_search(qs, value):
        if value:
            return qs.filter(staffing_requests__categories=value).distinct()
        else:
            return qs

    def location_search(qs, value):
        if value:
            return qs.filter(staffing_requests__location=value)
        else:
            return qs

    def contact_search(qs, value):
        if value:
            return qs.filter(owners=value)
        else:
            return qs

    def status_search(qs, value):
        if not value:
            return qs
        try:
            value = str(value)
        except (ValueError, TypeError):
            return qs

        if value == str(Project.STAFFING):
            qs = qs.exclude(status=Project.STAFFED)
        elif value == str(Project.STAFFED):
            qs = qs.filter(status=Project.STAFFED)
        return qs

    def division_search(qs, value):
        if value:
            return qs.filter(division=value)
        else:
            return qs

    search = django_filters.CharFilter(action=project_text_search)
    location = django_filters.ModelMultipleChoiceFilter(
        queryset=Location.objects.exclude(staffing_requests=None),
        action=location_search)
    skills = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.exclude(staffing_requests=None),
        action=categories_search)
    role = django_filters.ModelMultipleChoiceFilter(
        queryset=Role.objects.exclude(staffing_requests=None),
        action=role_search)
    group = django_filters.ModelMultipleChoiceFilter(
        queryset=Division.objects.all(),
        action=division_search)

    status = django_filters.ChoiceFilter(
        choices=(
            ('', None),
            (Project.STAFFING, 'Staffing',),
            (Project.STAFFED, 'Staffed'),),
        action=status_search,
        initial=None
    )

    contact = django_filters.ModelMultipleChoiceFilter(
        label='Contact',
        queryset=get_user_model().objects.none(),
        action=contact_search,
    )

    class Meta:
        model = Project
        fields = ['search', 'role', 'skills', 'location', 'status',
                  'contact', 'group']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ProjectFilter, self).__init__(*args, **kwargs)
        if self.request.user.is_vendor:
            self.filters.pop('contact')
        else:
            self.filters['contact'].extra.update(
                {'queryset': get_user_model().objects.filter(vendor=None)}
            )
