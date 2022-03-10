from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from .models import (Customer, CustomerRequest, CustomerConfig)


class CustomerCreationForm(forms.ModelForm):
    email = forms.EmailField(
        label=_('Admin email address'),
        help_text=_("Provide company email address(eg: example@proven.cc) instead of personal email addresses"),
        error_messages={'invalid': _("This value is not a valid email address(eg: example@proven.cc)")},
    )

    class Meta:
        model = Customer
        fields = (
            "name", "domain_url", "schema_name", 'email', 'logo', 'background', "email_domain",
            'default_vendor_kind', 'description', 'about_page_content', 'about_page_video', 'about_page_guide',
            'features', 'is_public_instance'
        )
        readonly_fields = ("email_domain",)

    def clean_domain_url(self):
        domain = self.cleaned_data['domain_url']
        if domain in Customer.RESERVED_DOMAINS:
            raise ValidationError('%s is a reserved subdomain' % domain)
        return domain

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CustomerCreationForm, self).__init__(*args, **kwargs)
        self.fields['domain_url'].help_text = 'This is what the Proven url will be. syntax: *name*.proven.cc'
        self.fields['schema_name'].help_text = "This is what the internal database will be called."
        self.fields['email_domain'].help_text = "List of email address providers allowed"


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain_url', 'schema_name', 'created_on',)
    form = CustomerCreationForm


class CustomerRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'email', 'phone_number', 'created_on')
    ordering = ('-created_on',)


class CustomerConfigAdmin(admin.ModelAdmin):
    list_display = ('customer', 'enable_periodic_rank_email', 'enable_clearbit', )


admin.site.register(Customer, CustomerAdmin)
admin.site.register(CustomerRequest, CustomerRequestAdmin)
admin.site.register(CustomerConfig, CustomerConfigAdmin)
