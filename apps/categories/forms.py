from django import forms
from .models import Category
from med_social.forms.mixins import FieldsetMixin


class CategoryForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('',{'rows':( ('name','kind'),),}),
    )
    class Meta:
        model = Category
        fields = ('name', 'kind')

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.__setup_fieldsets__()