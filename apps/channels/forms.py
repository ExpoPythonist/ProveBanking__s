from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from allauth.utils import generate_unique_username

from med_social.utils import get_current_tenant
from med_social.forms.mixins import FieldsetMixin
from .models import Message, Channel


class NewChannelForm(forms.ModelForm, FieldsetMixin):
    name = forms.CharField(required=True, help_text='',
                           label='Discussion name',
                           initial='External (w/ supplier)')

    private = forms.BooleanField(label='Private', required=False)

    class Meta:
        model = Channel
        fields = ('name', 'content_type', 'object_id', 'created_by')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.object_id = kwargs.pop('object_id')
        self.content_type = kwargs.pop('content_type')
        self.vendor_choices = kwargs.pop('vendor_choices', None)
        super(NewChannelForm, self).__init__(*args, **kwargs)

        field_row = ('name',)

        self.fields['created_by'].set_required(False)
        self.fields['created_by'].widget = forms.HiddenInput()

        if self.request.user.is_client:
            self.fields['private'].label = 'Private to {}'.format(
                get_current_tenant().name)

            if not self.vendor_choices:
                field_row = ('name',)
        else:
            field_row = ('name',)
            self.fields['name'].initial = '{tenant} w/ {vendor}'\
                .format(tenant=self.request.tenant.name,
                        vendor=self.request.user.vendor.name)

        vendors_help = ('Select suppliers that should be able to view and '
                        'take part in the discussion.')
        content_model = self.content_type.model_class()
        if hasattr(content_model, 'channels_extra_help_text'):
            vendors_help = '{} {}'.format(
                vendors_help, content_model.channels_extra_help_text)

        #self.fields['vendors'].required = False

        self.fields['content_type'].required = False
        self.fields['content_type'].widget = forms.HiddenInput()

        self.fields['object_id'].required = False
        self.fields['object_id'].widget = forms.HiddenInput()

        self.fieldsets = (
            ('', {'rows': (field_row,)}),
        )

        self.__setup_fieldsets__()

    def clean(self):
        cd = super(NewChannelForm, self).clean()
        if self.vendor_choices and len(self.vendor_choices) == 1:
            private = self.cleaned_data.get('private', False)
        return cd

    def clean_created_by(self):
        return self.request.user

    def clean_private(self):
        if self.request.user.is_vendor:
            return False
        return self.cleaned_data['private']

    def clean_content_type(self):
        return self.content_type

    def clean_object_id(self):
        return self.object_id


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('body',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(MessageForm, self).__init__(*args, **kwargs)
        self.fields['body'].label = ''
        self.fields['body'].widget.attrs['placeholder'] = ('start typing here'
        ' (@mention supported)')
        self.fields['body'].widget.attrs['force_rows'] = 1
        self.fields['body'].widget.attrs['class'] = 'channel-message'


class SuggestionSearchForm(forms.Form):
    search_term = forms.CharField()


class UserInviteForm(forms.ModelForm):

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'username',
                  'groups')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.message = kwargs.pop('message', None)
        super(UserInviteForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = forms.HiddenInput()
        self.fields['username'].set_required(False)
        self.fields['first_name'].set_required(True)
        self.fields['last_name'].set_required(True)
        self.fields['groups'].widget = forms.HiddenInput()
        self.fields['groups'].required = False

    def clean(self):
        cd = super(UserInviteForm, self).clean()
        cd['username'] = generate_unique_username([
            self.cleaned_data.get('email'),
            self.cleaned_data.get('first_name'),
            self.cleaned_data.get('last_name')
        ])
        return cd
