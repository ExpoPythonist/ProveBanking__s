from django import forms
from django.contrib.auth import get_user_model


class BatchRequestUpdateForm(forms.Form):
    users = forms.ModelMultipleChoiceField(queryset=get_user_model().objects.all())
