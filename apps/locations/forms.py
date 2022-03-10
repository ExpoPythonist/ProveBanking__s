from django import forms
from django.utils.translation import ugettext_lazy as _

from med_social.forms.base import DeletableFieldsetForm
from med_social.utils import slugify
from .models import Location
from med_social.forms.mixins import FieldsetMixin


class LocationCreateForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', { 'rows':(
                ('city',),
            ),
        }),
    )
    class Meta:
        model = Location
        fields = ('city',)
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(LocationCreateForm, self).__init__(*args, **kwargs)
        self.__setup_fieldsets__()
    
    def clean_city(self):
        city = self.cleaned_data.get("city")
        slug = slugify(city.strip())
        if self._meta.model.objects.filter(slug=slug).exists():
            raise forms.ValidationError(
                _("location '{}' already exists in database").format(city))
        return city
        

class LocationEditForm(DeletableFieldsetForm, FieldsetMixin):
    fieldsets = (
        ('', { 'rows':(
                ('city',),
            ),
        }),
    )

    class Meta:
        model = Location
        fields = ('city',)
        deletable = False

    def __init__(self, *args, **kwargs):
        super(LocationEditForm, self).__init__(*args, **kwargs)