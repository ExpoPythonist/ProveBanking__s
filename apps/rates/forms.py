from django import forms
from django.utils.html import mark_safe

from locations.models import Location
from med_social.utils import get_current_tenant
from med_social.forms.mixins import FieldsetMixin
from med_social.fields import LazyModelChoiceField
from django.contrib.auth import get_user_model
from roles.models import Role
from vendors.models import Vendor
from locations.models import Location
from categories.models import Category, SkillLevel

from .models import Rate


class RateForm(forms.ModelForm, FieldsetMixin):
    vendor = LazyModelChoiceField(Vendor.objects.all(),
                                  extra_allowed_values=['-1'],
                                  required=False)

    fieldsets = [
        ('Details', {'rows': (('location','role'), ('skill_level','cost',))},),
    ]

    class Meta:
        model = Rate
        fields = ('vendor', 'location', 'role', 'skill_level', 'cost')
        labels = {
            'cost': mark_safe(
                'Cost <small class="text-muted">'
                '(<i class="fa fa-dollar"></i> per hour)</small>'),
            'vendor': 'Company'
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.user = self.request.user

        super(RateForm, self).__init__(*args, **kwargs)

        for field in ['role', 'skill_level', 'location']:
            self.fields[field].required = False

        if Location.can_create(self.user):
            self.fields['location'].widget.attrs['selectize-create'] = 'true'
            self.fields['location'].widget.attrs['selectize-create-url'] = \
                Location.get_autocomplete_create_url()

        if Role.can_create(self.user):
            self.fields['role'].widget.attrs['selectize-create'] = 'true'
            self.fields['role'].widget.attrs['selectize-create-url'] = \
                Role.get_autocomplete_create_url()

        self.fields['vendor'].label = 'Company'
        if self.user.is_client:
            choices = list(self.fields['vendor'].choices)
            choices[0] = ('-1', str(get_current_tenant()))
            self.fields['vendor'].choices = choices
        else:
            self.fields['vendor'].widget = forms.HiddenInput()
        self.__setup_fieldsets__()

    def clean_vendor(self):
        vendor = self.cleaned_data['vendor']
        if self.user.is_vendor:
            return self.user.vendor
        elif self.user.is_client and hasattr(vendor, 'id') and vendor.id:
            return vendor
        elif self.user.is_client and vendor == '-1':
            return None

    def clean(self):
        role = self.cleaned_data.get('role', None)
        location = self.cleaned_data.get('location', None)
        skill_level = self.cleaned_data.get('skill_level', None)
        vendor = self.cleaned_data['vendor']

        if self.instance.id is None:
            rates = Rate.global_cards.filter(
                vendor=vendor,
                role=role,
                location=location,
                skill_level=skill_level,
                user=None
            )
            if rates.exists():
                raise forms.ValidationError('A rate card for already exists '
                                            'for provided location, role, and'
                                            ' skill level.')
        return self.cleaned_data


class UserRateForm(forms.ModelForm):
    class Meta:
        model = Rate
        fields = ('cost', 'user')
        widgets = {
            'user': forms.HiddenInput(),
        }


class SuggestedRateForm(forms.Form):
    resource = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        required=False
    )
    vendor = forms.ModelChoiceField(
        queryset=Vendor.objects.all(),
        required=False
    )
    role = forms.ModelChoiceField(queryset=Role.objects.all(), required=False)
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.filter(
        kind=Category.KIND_SKILL), required=False)
    skill_level = forms.ModelChoiceField(
        queryset=SkillLevel.objects.all(), required=False)
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(), required=False)

    def clean_vendor(self):
        resource = self.cleaned_data.get('resource', None)
        if resource:
            return resource.vendor
        else:
            return None
