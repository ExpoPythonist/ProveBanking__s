from django.db.models import Q
from django import forms

from watson import search as watson
import django_filters

from med_social.filters import BaseFilter
from divisions.models import Division
from .models import Vendor, ProcurementContact


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
    if 'category' in value_dict:
        q = q | Q(vendor_custom__category__in=value_dict['category'], vendor_custom__primary=True)

    if 'vendor' in value_dict:
        q = q | Q(id__in=value_dict['vendor'])

    return qs.filter(q)


def text_search(qs, value):
    return watson.filter(qs, value)


def kind_search(qs, value):
    if value:
        return qs.filter(kind__in=value)
    return qs


def group_search(qs, value):
    return qs


class VendorFilter(BaseFilter):
    search = django_filters.CharFilter(action=text_search)
    group = django_filters.ModelMultipleChoiceFilter(queryset=Division.objects.none(), action=group_search)
    my_suppliers = django_filters.MethodFilter(action='is_procurement_search')
    kind = django_filters.MultipleChoiceFilter(choices=Vendor.KIND_CHOICES, action=kind_search)

    class Meta:
        model = Vendor
        fields = ['find', 'location', 'group', 'search', 'my_suppliers', 'kind']
        exclude_from_render = ['search']

    def __init__(self, *args, **kwargs):
        super(VendorFilter, self).__init__(*args, **kwargs)

        self.filters['find'].action = find_search
        self.filters['my_suppliers'].widget = forms.widgets.Select(choices=(('', ''), ('True', 'True'),))

        if not self.request.user.is_authenticated() or not self.request.user.divisions.count():
            self.filters.pop('group')
        else:
            self.filters['group'].field.queryset = Division.objects.filter(user_rels__user=self.request.user)

    def is_procurement_search(self, qs, value):
        if value == 'True' and self.request:
            procurement = ProcurementContact.objects.filter(user=self.request.user).first()
            if procurement:
                return procurement.vendors.all()
        return qs
