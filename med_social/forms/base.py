from django import forms

from .mixins import FieldsetMixin


class BaseDeletableModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BaseDeletableModelForm, self).__init__(*args, **kwargs)
        if getattr(self.Meta, 'deletable', False):
            self.fields['delete'] = forms.BooleanField(initial=False,
                                    widget=forms.HiddenInput, required=False)


class DeletableFieldsetForm(BaseDeletableModelForm, FieldsetMixin):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(DeletableFieldsetForm, self).__init__(*args, **kwargs)
        FieldsetMixin.__init__(self)
