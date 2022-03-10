from django import forms
from locations.models import Location
from categories.models import Category

from med_social.fields import (MultiSelectizeModelField,)


class chartform(forms.Form):
    location = forms.ModelChoiceField(required=False,
                                      queryset=Location.objects.all(),
                                      empty_label='All',
                                      widget=forms.Select(attrs=
                                      {"selectize-allow-empty-option": "yes"}))
    skills = MultiSelectizeModelField(required=False,
                                      queryset=Category.objects.all())
