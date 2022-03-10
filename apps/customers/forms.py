from django import forms
from django.utils.encoding import force_text

from features.models import get_all as get_all_features
from med_social.forms.mixins import FieldsetMixin

from categories.models import Category
from locations.models import Location

from .models import CustomerRequest, Customer
from vendors.models import Vendor


class FeatureForm(forms.ModelForm):
    features = forms.MultipleChoiceField(choices=[(int(F), F.title) for F in get_all_features()], required=False)

    class Meta:
        model = Customer
        fields = ('features',)


class WeightsForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ('weight_industry', 'weight_clients', 'weight_feedback', 'weight_market', 'weight_web')

    def clean(self):
        if sum(self.cleaned_data.values()) != 100:
            raise forms.ValidationError('Weights should amount to 100%.')
        return self.cleaned_data


class PremiumSettingsForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ('monthly_plan', 'invoice_limit')


class AutocompleteCreateForm(forms.Form):
    text = forms.CharField()

    def clean_text(self):
        return self.cleaned_data['text'].strip()


class ClientInviteRequestForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('Company Details', {'fields': ('company', 'website')},),
        ('Contact Information', {'fields': ('name', 'email', 'phone_number')},),
    )

    class Meta:
        model = CustomerRequest
        fields = ('name', 'company', 'website', 'email', 'phone_number')
        exclude = ('notes',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ClientInviteRequestForm, self).__init__(*args, **kwargs)
        self.__setup_fieldsets__()

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '')
        pn = phone_number.replace(' ', '').replace('-', '').replace('+', '')
        if not pn.isdigit():
            raise forms.ValidationError(
                'Please enter a valid phone number. It can only contain digits, spaces, -, and +.')
        return force_text(phone_number)


class RequestDemoForm(forms.ModelForm, FieldsetMixin):

    class Meta:
        model = CustomerRequest
        fields = ('name', 'email', 'company', 'website', 'phone_number')

    def __init__(self, *args, **kwargs):
        super(RequestDemoForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = False
        self.fields['phone_number'].required = False


class SearchForm(forms.Form):
    search = forms.CharField()
    services = forms.ModelMultipleChoiceField(
        label='', help_text=' ',
        queryset=Category.services.filter(vendor_service__is_archived=False),
    )
    location = forms.ModelMultipleChoiceField(
        label='', help_text=' ',
        queryset=Location.objects.filter(vendors__is_archived=False),
    )
    categories = forms.ModelMultipleChoiceField(
        label='', help_text=' ',
        queryset=Category.skills.filter(vendors__is_archived=False),
    )
    kind = forms.IntegerField(widget=forms.HiddenInput(), initial=Vendor.KIND_PREFERRED)

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['search'].widget.attrs['placeholder'] = '  Vendor name?'
        self.fields['location'].widget.attrs['selectize-placeholder'] = 'in locations...'
        self.fields['services'].widget.attrs['selectize-placeholder'] = 'Services..'
        self.fields['categories'].widget.attrs['selectize-placeholder'] = 'With what skills?'
        self.fields['categories'].widget.attrs['data-open-on-focus'] = 'false'
