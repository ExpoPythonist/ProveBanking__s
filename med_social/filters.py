from django.db.models import Q
from django.core.urlresolvers import reverse
from django.forms.fields import MultipleChoiceField

import django_filters
from watson import search as watson

from locations.models import Location
from categories.models import Category
from vendors.models import Vendor
from users.models import User
from categories.models import CategoryType


def find_search(qs, value):
    value_dict = {}
    for V in value:
        if '-' not in V:
            continue
        field, val = V.split('-', 1)

        l = value_dict.get(field, [])
        l.append(val)
        value_dict[field] = l
    q = Q()

    if 'service' in value_dict:
        q = q | Q(service__in=value_dict['service'], )

    if 'skill' in value_dict:
        q = q | Q(categories__in=value_dict['skill'], )

    if 'category' in value_dict:
        q = q | Q(vendor_custom__category__in=value_dict['category'], vendor_custom__primary=True)

    if 'vendor' in value_dict:
        q = q | Q(id__in=value_dict['vendor'])

    if 'search' in value_dict:
        return watson.filter(qs, value_dict['search'][0])

    return qs.filter(q)


def location_search(qs, value):
    if value:
        q = Q()

        for obj in value:
            if obj.kind == Location.KIND_CITY:
                q = q | Q(locations=obj)
            elif obj.kind == Location.KIND_STATE:
                q = q | Q(locations__parent=obj)
            elif obj.kind == Location.KIND_COUNTRY:
                q = q | Q(locations__parent__parent=obj)
            return qs.filter(q)
    else:
        return qs


class BroMultipleChoiceField(MultipleChoiceField):
    """
    Throw anything at me bro. I won't valiate anything bro.
    """
    def validate(self, value):
        pass


class BroMultipleChoiceFilter(django_filters.MultipleChoiceFilter):
    field_class = BroMultipleChoiceField


CATEGORIES_OPTGROUPS = {
    Category.KIND_CATEGORY: 'Keywords',
    Category.KIND_CUSTOM: 'Categories',
    Category.KIND_SERVICE: 'Services',
    Category.KIND_INDUSTRY: 'Industry',
}


class BaseFilter(django_filters.FilterSet):
    find = BroMultipleChoiceFilter(
        choices=tuple(),
        action=find_search,
        label='FIND'
    )

    location = django_filters.ModelMultipleChoiceFilter(
        queryset=Location.objects.filter(
            Q(vendors__is_archived=False) |
            Q(children__vendors__is_archived=False) |
            Q(children__children__vendors__is_archived=False)),
        action=location_search,
        label='IN')

    class Meta:
        model = Vendor
        fields = ['find', 'location',]
        exclude_from_render = []

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(BaseFilter, self).__init__(*args, **kwargs)
        find_choices = []
        user_choices = []
        supplier_choices = []
        procurement_categ_choices = []
        skill_choices = []
        service_choices = []

        categ_type = CategoryType.objects.filter(vendor_editable=False).first()

        procurement_categ_choices.extend(
            [('category-{}'.format(C[0]), C[1],)
             for C in Category.objects.filter(custom_kind=categ_type,
                                              kind=Category.KIND_CUSTOM)
                .exclude(custom_kind_obj=None).values_list('id', 'name')]
        )

        find_choices.extend(
            [('service-{}'.format(C[0]), C[1],)
             for C in Category.services.values_list('id', 'name')]
        )

        user_choices.extend(
            [('user-{}'.format(C[0]), C[1] + ' ' + C[2],)
             for C in User.objects.values_list('id',
                                               'first_name',
                                               'last_name',)]
        )

        skill_choices.extend(
            [('skill-{}'.format(C[0]), C[1],)
             for C in Category.skills.all().values_list('id', 'name')]
        )

        service_choices.extend(
            [('service-{}'.format(C[0]), C[1],)
             for C in Category.services.all().values_list('id', 'name')]
        )

        search_choices = []

        search_choices.extend([(q, q.split('-', 1)[-1],)
                              for q in self.request.GET.getlist('find')])

        supplier_choices.extend([('vendor-{}'.format(C[0]), C[1],)
                                for C in Vendor.objects.values_list('id',
                                                                    'name')])

        self.filters['find'].field.choices = (
            ('Categories', procurement_categ_choices),
            ('Keywords', skill_choices),
            ('Suppliers', supplier_choices),
            ('People', user_choices),
            ('Search', search_choices),
        )

        find_attrs = self.filters['find'].field.widget.attrs
        find_attrs['selectize-url'] = reverse('api:filters')

        find_attrs['placeholder'] = find_attrs['selectize-placeholder'] = 'company name, categories, keywords'
        self.filters['find'].field.widget.attrs = find_attrs

        location_attrs = self.filters['location'].field.widget.attrs
        location_attrs['placeholder'] = location_attrs['selectize-placeholder'] = 'city or state'
        self.filters['location'].field.widget.attrs = location_attrs
