from django import forms
from phonenumber_field.formfields import PhoneNumberField
from med_social.forms.base import FieldsetMixin
from users.models import User
from vendors.models import RFP, Bid, Message


# TODO: move to utils, or replace with django bootstrap3
class BootstrapFormMixin(object):
    def __init__(self, *args, **kwargs):
        super(BootstrapFormMixin, self).__init__(*args, **kwargs)
        for key, value in self.fields.iteritems():
            if value.__class__.__name__ != 'BooleanField':
                if 'class' in value.widget.attrs:
                    value.widget.attrs['class'] += ' form-control'
                else:
                    value.widget.attrs['class'] = 'form-control'


class RFPForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('Request for Proposal', {
            'rows': (
                ('question',),
                ('description',),
                ('vendors',),
            )
        }),
        ('Contact Details', {
            'rows': (
                ('phone',),
                ('masked',),
                ('masked_expiry',),
            )
        }),
        ('Notifications', {
            'rows': (
                ('notif_call',),
                ('notif_text',),
                ('notif_email',),
            )
        }),
    )
    class Meta:
        model = RFP
        fields = (
            'question', 'description', 'vendors', 'masked', 'masked_expiry', 'notif_call', 'notif_text', 'notif_email',
            'open_rfp', 'categories',
        )

    def __init__(self, *args, **kwargs):
        client = kwargs.pop('client')
        shortlist = kwargs.pop('shortlist', None)
        super(RFPForm, self).__init__(*args, **kwargs)
        self.fields['phone'] = PhoneNumberField(initial=client.phone, required=False)
        if shortlist:
            self.fields['vendors'].initial = shortlist
        self.__setup_fieldsets__()


class MessageForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Message
        fields = ('message',)


class BidForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Bid
        fields = ('bid',)


class RFPNotificationSettingsForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = RFP
        fields = ('notif_call', 'notif_text', 'notif_email')
