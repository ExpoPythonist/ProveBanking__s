from django import forms

from .models import ServiceVendor
from med_social.forms.mixins import FieldsetMixin


def _get_vendor_resources(vendor):
    vusers = list(vendor.users.all())
    return ((u.id, u.get_name_display()) for u in vusers)


class ServiceVendorForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('',{ 'rows':(('service','contact_user'),)},),
    )

    class Meta:
        model = ServiceVendor
        fields = ('service', 'contact_user')
        labels = {
            'contact_user': 'contact'
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(ServiceVendorForm, self).__init__(*args, **kwargs)
        self.fields['contact_user'].label = 'Main contact'
        self.fields['contact_user'].widget = forms.Select()
        self.fields['contact_user'].widget.choices = _get_vendor_resources(
            self.request.user.vendor)
        self.__setup_fieldsets__()
