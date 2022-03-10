from django import forms
from django.contrib.auth import get_user_model


class RequestUpdatePreviewForm(forms.Form):
    user = forms.ModelChoiceField(queryset=get_user_model().objects.all())
    requested_by = forms.ModelChoiceField(queryset=get_user_model().objects.all())

    def get_message_view_kwargs(self):
        return self.cleaned_data.copy() or {}
