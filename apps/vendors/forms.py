import urlparse
import re

from django import forms
from django.conf import settings
from django.forms import inlineformset_factory
from django.db import transaction, connection
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_email, URLValidator
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext as _

from annoying.functions import get_object_or_None
from parsley.decorators import parsleyfy

from API.serializers.cert_serializers import CertSerializer

from med_social.forms.base import FieldsetMixin
from med_social.utils import now, get_current_tenant
from med_social.fields import MultiSelectizeModelField, SelectWithData

from locations.models import Location
from categories.models import Category, CategoryType
from clients.models import Client
from certs.models import Cert
from roles.models import Role
from reviews.fields.formfields import NPSField

from .models import (Vendor, VendorLocation, VendorRoles, PortfolioItem, VendorServices,
                     ClientReference, Invoice, CertVerification, InsuranceVerification, VendorIndustry,
                     VendorCustomKind, ProcurementLink, Diversity, ClientQueue, VendorClaim)

from .tasks import user_invite_portfolio


class VendorBaseForm(forms.ModelForm, FieldsetMixin):
    class Meta:
        model = Vendor
        step = None
        exclude = ()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.vendor = kwargs.pop('vendor', None)
        super(VendorBaseForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        save_m2m_data = kwargs.pop('save_m2m_data', True)
        commit = kwargs.get('commit', True)
        kwargs['commit'] = False
        vendor = super(VendorBaseForm, self).save(*args, **kwargs)
        saved = False
        if not vendor.id:
            vendor.joined_on = now()
            vendor.save()
            saved = True
        if not saved and commit:
            vendor.save()
        return vendor


class VendorProfileForm(VendorBaseForm):

    contacts = forms.ModelMultipleChoiceField(
        label='List the administrators of your firm\'s profile',
        queryset=get_user_model().objects.none(),)

    fieldsets = (
        ('BASIC INFO', {
            'rows': (
                ('name', 'founded'),
                ('summary',),
                ('story',),
                ('open_for_business',),
            )
        }),
        ('COMPANY DETAILS', {
            'rows': (
                ('tin', 'duns'),
            )
        }),
        ('CONTACT POINTS', {
            'rows': (
                ('address',),
                ('contacts',),
                ('email',),
                ('phone',),
            )
        }),
    )

    class Meta:
        model = Vendor
        fields = ('name', 'open_for_business', 'email', 'phone', 'summary', 'story',
                  'founded', 'contacts', 'address', 'tin', 'duns')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Awesome Company'}),
            'email': forms.EmailInput(attrs={'placeholder': 'contact@company.com'}),
            'summary': forms.Textarea(attrs={'placeholder': "Summary of your company's services and differentiation"}),
        }
        labels = {
            'story': 'Why should clients choose you over your competitors ?',
            'open_for_business': 'Are you currently accepting commercial drone work?',
            'email': 'Email of key sales contact of your company',
            'phone': 'Phone no. of primary contact',
            'founded': 'Year founded',
            'address': 'Corporate address'
        }
        help_texts = {
            'summary': "<span class='word-wrap hide'><span class='word-left text-primary'>500</span> characters left</span><br/>"
                       'Spend time on this - this is often the first and the'
                       ' only thing clients will see about you',
            'story': 'Limit this to three crisp bullet points',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('request', None)
        self.vendor = kwargs.get('vendor', None)
        self.is_lean = kwargs.pop('lean', False)
        super(VendorProfileForm, self).__init__(*args, **kwargs)
        self.fields['contacts'].set_required(False)
        self.fields['contacts'].queryset = get_user_model().objects.filter(vendor=self.vendor)
        self.fields['contacts'].help_text = (
            'or <a href="{}" data-target="#userInviteModal" data-toggle="modal">'
            '<span class="h5" >add new user</span></a>').format(reverse('users:invite')+ "?vendor_id=" + str(self.vendor.id))
        self.fields['contacts'].widget.attrs['data-kind'] = 'user'
        self.fields['phone'].widget.attrs['data-phoneinput'] = 'true'
        self.fields['summary'].widget.attrs['class'] = "word-count"
        self.fields['summary'].label = "Company Description Summary"
        self.fields['tin'].set_required(False)
        self.fields['duns'].set_required(False)
        self.fields['tin'].label = "TIN number"
        self.fields['duns'].label = "DUNS number"
        if get_current_tenant().schema_name != 'commercialdrones':
            self.fields['open_for_business'].label = 'Open for Business'

        if self.is_lean:
            self.fields.pop('story')
            self.fieldsets = (
                ('BASIC INFO', {
                    'rows': (
                        ('name', 'founded'),
                        ('summary',),
                        ('open_for_business',),
                    )
                }),
                ('COMPANY DETAILS', {
                    'rows': (
                        ('tin', 'duns'),
                    )
                }),
                ('CONTACT POINTS', {
                    'rows': (
                        ('address',),
                        ('contacts',),
                        ('email',),
                        ('phone',),
                    )
                }),
            )

            if self.request.user.is_client:
                self.fields.pop('duns')
                self.fields.pop('tin')
                self.fieldsets = (
                    ('BASIC INFO', {
                        'rows': (
                            ('name', 'founded'),
                            ('summary',),
                            ('open_for_business',),
                        )
                    }),
                    ('CONTACT POINTS', {
                        'rows': (
                            ('address',),
                            ('contacts',),
                            ('email',),
                            ('phone',),
                        )
                    }),
                )

        if self.request.user.is_client:
            self.fields.pop('duns')
            self.fields.pop('tin')
            self.fieldsets = (
                ('BASIC INFO', {
                    'rows': (
                        ('name', 'founded'),
                        ('summary',),
                        ('story',),
                        ('open_for_business',),
                    )
                }),
                ('CONTACT POINTS', {
                    'rows': (
                        ('address',),
                        ('contacts',),
                        ('email',),
                        ('phone',),
                    )
                }),
            )

        self.__setup_fieldsets__()


class VendorMediaForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('Company video', {
            'rows': (
                ('video',),
            )
        }),
        ("Your Company's web presence", {
            'rows': (
                ('website', 'linkedin'),
                ('glassdoor', 'github'),
                ('facebook', 'twitter'),
            )
        }),
    )

    class Meta:
        model = Vendor
        fields = ('video', 'website', 'twitter', 'facebook', 'linkedin',
                  'glassdoor', 'github',)
        widgets = {
            'video': forms.TextInput(
                attrs={'placeholder': 'http://youtube.com/watch/?v=xyz'}),
            'website': forms.TextInput(
                attrs={'placeholder': 'http://company.com'}),
            'twitter': forms.TextInput(
                attrs={'placeholder': '@company_twitter_handle'}),
            'facebook': forms.TextInput(
                attrs={'placeholder': 'http://facebook.com/...'}),
            'linkedin': forms.TextInput(
                attrs={'placeholder': 'http://linkedin.com/...'}),
            'glassdoor': forms.TextInput(
                attrs={'placeholder': 'http://glassdoor.com/...'}),
            'github': forms.TextInput(
                attrs={'placeholder': 'github_username'}),
        }
        help_texts = {
            'video': 'Adding a corporate video helps give new customers a'
                    ' better understanding of what you do',
            'website': 'Use format http://example.com for the URL'
        }

    def __init__(self, *args, **kwargs):
        super(VendorMediaForm, self).__init__(*args, **kwargs)
        self.fields['twitter'].label = "Twitter Handle"
        self.fields['twitter'].help_text = ("Enter just the name of your company's twitter handle, not the URL please")



        if self.instance.video:
            url = self.instance.get_video_embed_url()
            if url:
                self.fields['video'].label = (
                    '<iframe type="text/html" width="410" height="250" src="%s"'
                    'frameborder="0"></iframe>' % url)

        self.__setup_fieldsets__()

    def clean_video(self):
        url = self.cleaned_data.get('video')
        if url:
            o = urlparse.urlparse(url)
            q = urlparse.parse_qs(o.query)
            if o.netloc not in ('youtube.com', 'www.youtube.com', 'youtu.be', 'www.youtu.be'):
                raise forms.ValidationError('Please enter a valid YouTube url')

            if o.hostname in ('youtu.be', 'www.youtu.be') and not o.path[1:]:
                raise forms.ValidationError('Please enter a valid YouTube url')

            if o.netloc in ('youtube.com', 'www.youtube.com',) and not q.get('v'):
                raise forms.ValidationError('Please enter a valid YouTube url')

        return url

    def clean_twitter(self):
        twitter = self.cleaned_data.get('twitter')
        if twitter and not re.match(r'^@{0,1}[a-zA-Z0-9_]+$', twitter):
            raise forms.ValidationError('Please enter a valid twitter handle')
        if twitter:
            twitter = re.sub('[@]', '', twitter)
        return twitter

    def clean_github(self):
        github = self.cleaned_data.get('github')
        if github and not re.match(r'^[a-zA-Z0-9-]+$', github):
            raise forms.ValidationError('Please enter a valid github username')
        return github


class VendorRecommendationsForm(forms.Form):
    location = forms.ModelChoiceField(queryset=Location.objects.all())
    categories = forms.ModelChoiceField(queryset=Category.objects.all())
    role = forms.ModelChoiceField(queryset=Role.objects.all())


class VendorInviteForm(forms.Form, FieldsetMixin):
    name = forms.CharField(label='Company Name', widget=forms.Select, required=True)
    email = forms.CharField(label='Email Address of Your Contact at the Company')
    website = forms.URLField(label='Website', required=False)

    fieldsets = (
        ('', {'rows': (('name', 'email', 'website'),)},),
    )

    class Meta:
        model = Vendor
        fields = ('name', 'email', 'website')

    def __init__(self, *args, **kwargs):
        self.is_admin = kwargs.pop('is_admin', False)
        super(VendorInviteForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['selectize-url'] = reverse('clients:search_basic')
        self.fields['name'].widget.attrs['selectize-create'] = 'true'
        self.fields['name'].widget.attrs['selectize-create'] = 'true'
        self.fields['name'].set_required(True)
        self.fields['website'].widget = forms.HiddenInput()
        self.__setup_fieldsets__()

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        '''
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user is already registered with this e-mail address.'))
        '''
        return email

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError('This field is required')
        return name

    def clean(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError('Required fields cannot be left blank')
        if len(name.split(' ', 1)) == 2:
            website, company = name.split(' ', 1)
        else:
            return self.cleaned_data
        validate = URLValidator()
        try:
            validate(website)
            self.cleaned_data['name'] = company
            self.cleaned_data['website'] = website
        except ValidationError:
            self.cleaned_data['name'] = name

        email = self.cleaned_data['email'].lower()
        '''
        domain = email.split('@')[-1]
        if not self.is_admin and website and domain not in website and domain != 'proven.cc':
            self.add_error('email', forms.ValidationError('The email domain should match the vendor\'s website.'))
        '''
        self.cleaned_data['email'] = email

        return self.cleaned_data


@parsleyfy
class VendorLocationForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {'rows': (
                ('location', 'num_resources',),
        )},),
    )

    location = forms.IntegerField(widget=forms.Select)

    class Meta:
        model = VendorLocation
        fields = ('location', 'num_resources', 'vendor',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        super(VendorLocationForm, self).__init__(*args, **kwargs)
        self.fields['vendor'].set_required(False)
        self.fields['vendor'].widget = forms.HiddenInput()

        self.fields['location'].widget.attrs['data-open-on-focus'] = 'false'
        self.fields['location'].widget.attrs['selectize-url'] = reverse('locations:search')
        self.__setup_fieldsets__()

    def clean_vendor(self):
        return self.vendor

    def clean_location(self):
        pk = self.cleaned_data['location']
        if Location.objects.filter(id=int(pk)).exists():
            return Location.objects.get(pk=pk)
        raise forms.ValidationError(
            'Location choice does not exist')

@parsleyfy
class VendorRoleForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {'rows': (
                ('role', ),
        )},),
    )

    class Meta:
        model = VendorRoles
        fields = ('role', 'allocation', 'vendor',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        self.initial_allocation = 0
        super(VendorRoleForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['allocation'].set_required(False)
        self.fields['vendor'].set_required(False)
        self.fields['vendor'].widget = forms.HiddenInput()
        roles = [x.role for x in self.vendor.vendor_roles.all()]
        self.fields['role'].queryset = Role.objects.exclude(name__in=roles)
        if Role.can_create(self.request.user):
            self.fields['role'].widget.attrs['selectize-create'] = 'true'
            self.fields['role'].widget.attrs['selectize-create-url'] = Role.get_autocomplete_create_url()

        self.fields['role'].widget.attrs['data-open-on-focus'] = 'false'
        self.__setup_fieldsets__()

    def clean_vendor(self):
        return self.vendor

    def clean_allocation(self):
        return self.initial_allocation


class VendorSearchForm(forms.Form, FieldsetMixin):

    role = forms.ModelChoiceField(queryset=Role.objects.all(), label='I am looking for')

    location = forms.ModelChoiceField(queryset=Location.objects.all(), label='in')

    def __init__(self, *args, **kwargs):
        super(VendorSearchForm, self).__init__(*args, **kwargs)
        self.fields['location'].widget.attrs.update({'class': 'location_input'})
        self.fields['role'].widget.attrs.update({'class': 'role_input'})


class VendorAllocationForm(forms.Form):

    def __init__(self, roles, *args, **kwargs):
        self.roles = roles
        super(VendorAllocationForm, self).__init__(*args, **kwargs)

    def clean(self):
        total = 0
        for role in self.roles:
            total += self.cleaned_data.get(unicode(role.id)) or role.allocation
        if total != 100:
            raise forms.ValidationError(
                'Sum of all role allocation must be 100%.')
        return self.cleaned_data

    def save(self, *args, **kwargs):
        with transaction.atomic():
            for role in self.roles:
                role.allocation = self.cleaned_data.get(unicode(role.id), 0)\
                    or role.allocation
                role.save()


@parsleyfy
class VendorCategoryForm(forms.Form, FieldsetMixin):
    categories = forms.ModelMultipleChoiceField(queryset=Category.skills.all())
    fieldsets = (
        ('', {'rows': (
                ('categories', ),
        )},),
    )

    class Meta:
        fields = ('categories',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        super(VendorCategoryForm, self).__init__(*args, **kwargs)
        self.fields['categories'].initial = self.vendor.categories.all()
        if Category.can_create(self.request.user):
            self.fields['categories'].widget.attrs['selectize-create'] = 'true'
            self.fields['categories'].widget.attrs['selectize-create-url'] = \
                Category.get_autocomplete_create_url(
                    {'kind': Category.KIND_SKILL})
        self.fields['categories'].widget.attrs['data-open-on-focus'] = 'false'
        self.fields['categories'].label = 'Keyword'

        self.__setup_fieldsets__()


@parsleyfy
class VendorServiceForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {'rows': (
                ('service', ),
        )},),
    )

    class Meta:
        model = VendorServices
        fields = ('service', 'allocation', 'vendor',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        self.initial_allocation = 0
        super(VendorServiceForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['allocation'].set_required(False)
        self.fields['vendor'].set_required(False)
        self.fields['vendor'].widget = forms.HiddenInput()
        services = [x.service for x in self.vendor.vendor_services.all()]
        self.fields['service'].queryset = Category.services.exclude(name__in=services)
        if Category.can_create(self.request.user):
            self.fields['service'].widget.attrs['selectize-create'] = 'true'
            self.fields['service'].widget.attrs['selectize-create-url'] = \
                Category.get_autocomplete_create_url(
                    {'kind': Category.KIND_SERVICE})
        self.fields['service'].widget.attrs['data-open-on-focus'] = 'false'
        self.__setup_fieldsets__()

    def clean_vendor(self):
        return self.vendor

    def clean_allocation(self):
        return self.initial_allocation


class VendorCategoryAllocationForm(forms.Form):

    def __init__(self, skills, *args, **kwargs):
        self.skills = skills
        super(VendorCategoryAllocationForm, self).__init__(*args, **kwargs)

    def clean(self):
        total = 0
        for skill in self.skills:
            total += self.cleaned_data.get(unicode(skill.id)) or skill.allocation
        if total != 100:
            raise forms.ValidationError(
                'Sum of all role allocation must be 100%.')
        return self.cleaned_data

    def save(self, *args, **kwargs):
        with transaction.atomic():
            for skill in self.skills:
                skill.allocation = self.cleaned_data.get(unicode(skill.id), 0)\
                    or skill.allocation
                skill.save()


class VendorLocationAllocationForm(forms.Form):

    def __init__(self, locations, *args, **kwargs):
        self.locations = locations
        super(VendorLocationAllocationForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            for location in self.locations:
                location.num_resources = self.cleaned_data.get(unicode(location.id), 0)\
                    or location.num_resources
                location.save()


class VendorServiceAllocationForm(forms.Form):

    def __init__(self, services, *args, **kwargs):
        self.services = services
        super(VendorServiceAllocationForm, self).__init__(*args, **kwargs)

    def clean(self):
        total = 0
        for service in self.services:
            total += self.cleaned_data.get(unicode(service.id)) or service.allocation
        if total != 100:
            raise forms.ValidationError(
                'Sum of all service allocation must be 100%.')
        return self.cleaned_data

    def save(self, *args, **kwargs):
        with transaction.atomic():
            for service in self.services:
                service.allocation = self.cleaned_data.get(unicode(service.id), 0)\
                    or service.allocation
                service.save()


class PortfolioItemForm(forms.ModelForm, FieldsetMixin):
    owners = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects
                                 .filter(kind=get_user_model().KIND_CLIENT))
    skills = forms.ModelMultipleChoiceField(
        queryset=Category.skills.all())

    fieldsets = (
        ('', {'rows': (
            ('title',),
            ('owners',),
            ('locations', 'skills'),
            ('start_date', 'end_date',),
            ('description',),
        )}),
    )

    class Meta:
        model = PortfolioItem
        fields = ('vendor', 'title', 'description', 'start_date', 'end_date', 'owners', 'locations', 'skills',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        tenant = get_current_tenant()
        if kwargs.get('data'):
            data = kwargs.get('data').copy()
            owners = kwargs.get('data').getlist('owners')
            if owners:
                self.owner_email = filter(lambda x: self.is_email(x), owners)
                self.rem_owners = set(owners).difference(set(self.owner_email))
                data.setlist('owners', self.rem_owners)
                kwargs['data'] = data

        super(PortfolioItemForm, self).__init__(*args, **kwargs)
        self.fields['vendor'].widget = forms.HiddenInput()
        self.fields['vendor'].set_required(False)
        self.fields['owners'].set_required(False)
        self.fields['skills'].set_required(False)
        if tenant.is_public_instance:
            self.fields['owners'].label = 'Client contact(s)'
            self.fields['owners'].widget.attrs['selectize-placeholder'] =\
                'Type to search by name enter an email address(optional)'\
                .format(client=tenant.name)
        else:
            self.fields['owners'].label = '{client} client contact(s)'\
                .format(client=tenant.name)
            self.fields['owners'].widget.attrs['selectize-placeholder'] =\
                'Type to search by name or enter an @{client} email address (optional)'\
                .format(client=tenant.name)
        self.fields['start_date'].label = 'Start date (approximately)'
        self.fields['end_date'].label = 'End date (approximately)'
        self.fields['description'].label = 'Description of your role in the project'
        self.fields['description'].help_text = ('Please do not describe the project in detail'
                                                 ' as certain aspects of the project could be confidential.')
        if Category.can_create(self.request.user):
            self.fields['skills'].widget.attrs['selectize-create'] = 'true'
            self.fields['skills'].widget.attrs['selectize-create-url'] = \
                Category.get_autocomplete_create_url({
                    'kind': Category.KIND_SKILL
                })
        if Location.can_create(self.request.user):
            self.fields['locations'].widget.attrs['selectize-create'] = 'true'
            self.fields['locations'].widget.attrs['selectize-create-url'] = \
                Location.get_autocomplete_create_url()

        self.fields['owners'].widget.attrs['selectize-url'] = reverse('users:search') + '?kind=1'
        self.fields['owners'].widget.model = get_user_model()

        self.__setup_fieldsets__()

    def is_email(self, q):
        try:
            validate_email(q)
            return True
        except ValidationError:
            return False

    def clean_vendor(self):
        if self.request.user.is_vendor:
            return self.request.user.vendor
        return self.vendor

    def save(self, *args, **kwargs):
        portfolio = super(PortfolioItemForm, self).save(*args, **kwargs)
        tenant = connection.tenant
        if hasattr(self, 'owner_email'):
            for email in self.owner_email:
                user_invite_portfolio.delay(tenant_id=tenant.id,
                                            sender_id=self.request.user.id,
                                            portfolio_id=portfolio.id,
                                            email=email,
                                            kind=get_user_model()
                                            .KIND_CLIENT)
        return portfolio


class VendorApplicationForm(forms.ModelForm, FieldsetMixin):
    client_contact = forms.EmailField(required=False)
    custom_categories = forms.ModelChoiceField(queryset=Category.objects.none(), required=False)

    fieldsets = (
        ('', {'rows': (
                ('name', 'email',),
                ('client_contact', 'custom_categories'),
        )}),
    )

    class Meta:
        model = Vendor
        fields = ('name', 'email', 'client_contact', 'custom_categories')
        labels = {
            'name': 'Your Company name',
            'email': 'Your Email Address'
        }

    def __init__(self, *args, **kwargs):
        super(VendorApplicationForm, self).__init__(*args, **kwargs)
        self.fields['client_contact'].label = ('Email address of your contact at %s' % get_current_tenant().name)
        self.fields['custom_categories'].queryset = Category.objects.filter(kind=Category.KIND_CUSTOM, custom_kind__vendor_editable=False)
        self.fields['custom_categories'].label = 'Primary service'
        self.__setup_fieldsets__()

    def clean_email(self):
        email = self.cleaned_data["email"]
        user_model = get_user_model()
        if user_model.objects.filter(email=email).exists():
            raise forms.ValidationError(_("A user is already registered"
                                        " with this e-mail address."))
        return email

    def clean_client_contact(self):
        client_contact = self.cleaned_data.get('client_contact')
        if client_contact:
            return get_object_or_None(get_user_model(),
                                      email=client_contact)


class CertAddForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('CERTIFICATION/ACCREDITATION DETAILS', {
            'rows': (
                ('cert', 'date_awarded', 'attached_file', ),
            )
        }),
        ('VERIFY CERTIFICATION/ACCREDITATION (optional)', {
            'rows': (
                ('email',),
                ('email_msg',),
                ('url',),
            )
        }),
    )

    class Meta:
        model = CertVerification
        fields = ('cert', 'url', 'email', 'email_msg', 'date_awarded', 'attached_file', )
        labels = {
            'url': 'URL',
            'email': 'Email address',
            'cert': 'Certification/Accreditation',
            'attached_file': 'Attach certificate file (image or PDF)'
        }
        help_texts = {
            'url': 'Link to proof of certification',
            'email': 'Email address of someone who can verify this certification.',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        super(CertAddForm, self).__init__(*args, **kwargs)
        self.fields['email_msg'].label = 'Email message to be sent'
        self.fields['email_msg'].widget.attrs['data-initial'] =\
            self.Meta.model.DEFAULT_EMAIL_MSG.format(
                vendor=self.vendor.name, first_name=self.request.user.first_name,
                full_name=self.request.user.get_name_display())
        self.fields['cert'].widget = SelectWithData(request=self.request, serializer=CertSerializer)
        self.fields['cert'].queryset = Cert.objects.exclude(vendors=self.vendor)
        if Cert.can_create(self.request.user):
            self.fields['cert'].widget.attrs['selectize-create'] = 'true'
            self.fields['cert'].widget.attrs['selectize-create-url'] = \
                Cert.get_autocomplete_create_url({'kind': Cert.KIND_CERT})
        self.fields['attached_file'].widget.attrs['accept'] = "image/*,.pdf"

        self.__setup_fieldsets__()

    def clean_email_msg(self):
        email = self.cleaned_data.get("email")
        email_msg = self.cleaned_data.get("email_msg")
        if email and not email_msg:
            email_msg = self.Meta.model.DEFAULT_EMAIL_MSG.format(
                vendor=self.vendor.name, first_name=self.request.user.first_name,
                full_name=self.request.user.get_name_display())
        return email_msg


class InsuranceAddForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('INSURANCE DETAILS', {
            'rows': (
                ('insurance',),
                ('extent', 'expiry_date'),
            )
        }),
        ('VERIFY INSURANCE (optional)', {
            'rows': (
                ('policy_document',),
                ('url',),
                ('email',),
                ('email_msg',),
            )
        }),
    )

    class Meta:
        model = InsuranceVerification
        fields = ('insurance', 'extent', 'url', 'expiry_date', 'policy_document', 'email', 'email_msg')
        labels = {
            'url': 'URL',
            'email': 'Email Address of Insurance Broker',
            'extent': 'Extent of Public Liability Cover',
            'expiry_date': 'Date of Expiry',
            'policy_document': 'Upload policy document',
        }
        help_texts = {
            'url': 'Link to proof of insurance',
            'email': 'Email address of someone who can verify this insurance.',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        super(InsuranceAddForm, self).__init__(*args, **kwargs)
        self.fields['email_msg'].label = 'Email message to be sent'
        self.fields['email_msg'].widget.attrs['data-initial'] =\
            self.Meta.model.DEFAULT_EMAIL_MSG.format(
                vendor=self.vendor.name, first_name=self.request.user.first_name,
                full_name=self.request.user.get_name_display())
        self.fields['insurance'].widget = SelectWithData(request=self.request, serializer=CertSerializer)
        self.fields['insurance'].queryset = Cert.objects.exclude(vendors=self.vendor)
        if Cert.can_create(self.request.user):
            self.fields['insurance'].widget.attrs['selectize-create'] = 'true'
            self.fields['insurance'].widget.attrs['selectize-create-url'] = \
                Cert.get_autocomplete_create_url({'kind': Cert.KIND_INSURANCE})

        self.__setup_fieldsets__()

    def clean_email_msg(self):
        email = self.cleaned_data.get("email")
        email_msg = self.cleaned_data.get("email_msg")
        if email and not email_msg:
            email_msg = self.Meta.model.DEFAULT_EMAIL_MSG.format(
                vendor=self.vendor.name, first_name=self.request.user.first_name,
                full_name=self.request.user.get_name_display())
        return email_msg


class ClientForm(forms.Form, FieldsetMixin):
    client = forms.CharField(widget=forms.Select)
    logo = forms.CharField(required=False)
    fieldsets = (
        ('', {
            'rows': (
                ('logo', 'client'),)
        }),
    )

    class Meta:
        fields = ('client', 'logo',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        self.result = kwargs.pop('result', None)
        super(ClientForm, self).__init__(*args, **kwargs)
        # self.fields['client'].widget = SelectWithData(
        #     request=self.request, serializer=ClientSerializer)
        # self.fields['client'].queryset = (
        #     Client.objects.filter(references__is_fulfilled=True,
        #                           references__use_alt_name=False) |
        #     Client.objects.filter(created_by=self.request.user)
        # ).exclude(references__vendor=self.vendor).distinct()
        # if Client.can_create(self.request.user):
        #     self.fields['client'].widget.attrs['selectize-create'] = 'true'
        #     self.fields['client'].widget.attrs['selectize-create-url'] = \
        #         Client.get_autocomplete_create_url()
        if self.result:
            self.fields['client'] = forms.ChoiceField(choices=((str(self.result.id), self.result.name),))
            self.fields['client'].initial = self.result
        else:
            self.fields['client'].widget.attrs['selectize-url'] = reverse('clients:search_basic')
        self.fields['client'].label = 'Client name'
        self.fields['client'].help_text = ""
        self.fields['logo'].widget = forms.HiddenInput()
        self.fields['logo'].max_length = 70
        self.fields['client'].widget.attrs['data-kind'] = 'client'
        self.fields['client'].help_text = (
        "Your client will remain anonymous if you check the button below to show anonymized name.<br>"
        'Unable to find your client? <a href="{}" '
            'data-target="#genericModal" data-toggle="modal">'
            '<span class="h5" >add here</span></a>').format(reverse('vendors:new_client_add', args=(self.vendor.id,)))
        self.__setup_fieldsets__()

    def clean_client(self):
        client = self.cleaned_data['client']
        if not self.result:
            website, name = self.cleaned_data['client'].split(' ', 1)
            if name and website:
                client, created = Client.objects.get_or_create(website__iexact=website,
                                                         defaults={
                                                         'website' :website,
                                                         'name' : name
                                                         })
                return client.id
        return client


class ClientAddForm(forms.ModelForm, FieldsetMixin):

    fieldsets = (
        ('', {
            'rows': (
                ('use_alt_name',),
                ('alt_name',),
            )
        }),
    )

    class Meta:
        model = ClientReference
        fields = ('email', 'use_alt_name', 'alt_name',
                  'duration', 'email_msg',)
        widgets = {
            'email': forms.EmailInput(
                attrs={'placeholder': 'contact@company.com'}),
            'alt_name': forms.TextInput(
                attrs={'placeholder': 'Top 10 tech company in San Francisco'}),
        }
        labels = {
            'email': 'Email address of your lead contact at client who can verify your relationship with them',
            'alt_name': 'I would like to hide my client name and list them as',
            'use_alt_name': '&nbsp;Show anonymized name instead for this client',
            'duration': 'Company has been a client since',
            'email_msg': 'Hi,<br>'
        }
        help_texts = {
            'email': 'This is the address to which the verification email'
                     ' will be sent',
            'alt_name': '',
            'use_alt_name': '',
        }

    def __init__(self, *args, **kwargs):
        self.vendor = kwargs.pop('vendor')
        self.request = kwargs.pop('request')
        super(ClientAddForm, self).__init__(*args, **kwargs)
        self.fields['alt_name'].set_required(False)
        self.fields['email'].set_required(False)
        self.fields['duration'].set_required(False)
        self.fields['email_msg'].set_required(False)

        self.initial['email_msg'] = self.Meta.model.DEFAULT_EMAIL_MSG.format(
            vendor=self.vendor.name, first_name=self.request.user.first_name,
            full_name=self.request.user.get_name_display())
        self.fields['email_msg'].help_text = (
            '<br>Thanks for helping %s out,<br>Proven'
            % self.request.user.first_name)
        self.fields['duration'].widget.attrs['selectize-placeholder'] = ' '

        self.__setup_fieldsets__()

    def clean_alt_name(self):
        alt_name = self.cleaned_data['alt_name']
        use_alt_name = self.cleaned_data['use_alt_name']
        if use_alt_name and not alt_name:
            raise forms.ValidationError('This is a required field')
        return alt_name


class ClientReferenceAddForm(forms.ModelForm, FieldsetMixin):
    billing_new = forms.ChoiceField(choices=ClientReference.BILLING_CHOICES_NEW + (('-1', 'I\'d rather not say'),))

    fieldsets = (

        ('Client details', {
            'rows': (
                ('email',),
                ('duration',),
                ('billing_new',),
            ),
            'description': 'advanced stuff',
        }),
        ('Email message', {
            'rows': (
                ('email_msg',),
            )
        }),
    )

    class Meta:
        model = ClientReference
        fields = ('email', 'alt_name', 'use_alt_name', 'billing_new', 'duration', 'email_msg',)
        widgets = {
            'email': forms.EmailInput(
                attrs={'placeholder': 'contact@company.com'}),
            'alt_name': forms.TextInput(
                attrs={'placeholder': 'Top 10 tech company in San Francisco'}),
        }
        labels = {
            'email': 'Email address of your lead contact',
            'alt_name': 'I would like to list my client as',
            'use_alt_name': '',
            'duration': 'Company has been a client since',
            'email_msg': 'Hi,<br>'
        }
        help_texts = {
            'email': 'Email address of your contact at client who can verify your relationship with them. '
                     'This is the address to which the verification email'
                     ' will be sent',
            'alt_name': 'Some clients may prefer not to show their real '
                        ' name to protect their privacy',
            'use_alt_name': '&nbsp;Show anonymized name to the client as '
                            'default<hr><input type="submit" value="Add client" class="btn btn-primary"/> &nbsp;&nbsp;or seek client verification below',
        }

    def __init__(self, *args, **kwargs):
        self.vendor = kwargs.pop('vendor')
        self.request = kwargs.pop('request')
        self.reference = kwargs.pop('reference')

        super(ClientReferenceAddForm, self).__init__(*args, **kwargs)
        self.fields['alt_name'].set_required(False)
        self.fields['duration'].set_required(False)
        self.fields['billing_new'].set_required(False)
        self.fields['billing_new'].choices = ClientReference.BILLING_CHOICES_NEW + (('-1', 'I\'d rather not say'),)
        self.fields['email_msg'].set_required(False)
        self.initial['email_msg'] = self.Meta.model.DEFAULT_EMAIL_MSG.format(
            vendor=self.vendor.name, first_name=self.request.user.first_name,
            full_name=self.request.user.get_name_display())
        self.fields['email_msg'].help_text = (
            '<br>Thanks for helping %s out,<br>Proven'
            % self.request.user.first_name)
        self.fields['billing_new'].widget.attrs['selectize-placeholder'] = ' '
        self.fields['billing_new'].label = 'Billings for the previous 12 months'
        self.fields['billing_new'].help_text = (
            'This information will never be shared publicly and '
            'will only be used to verify the importance of your '
            'client relationship. The higher the billing, the '
            'better your ranking.')
        self.initial['billing_new'] = 1
        self.fields['duration'].widget.attrs['selectize-placeholder'] = ' '
        self.fields['use_alt_name'].widget.attrs['ignore-enhance'] = 'true'

        self.__setup_fieldsets__()

    def clean_billing_new(self):
        if self.cleaned_data.get('billing_new') == str(-1):
            return None
        return self.cleaned_data.get('billing_new')

    def clean(self):
        email = self.cleaned_data['email'].lower()
        '''
        domain = email.split('@')[-1]
        if self.instance.client.website and domain not in self.instance.client.website and domain != 'proven.cc':
            self.add_error('email', forms.ValidationError('The email domain should match the client\'s website.'))
        '''
        self.cleaned_data['email'] = email
        return self.cleaned_data


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ('invoice', 'invoice_amount', 'invoice_date')

    def clean_invoice(self):
        max_upload_size = settings.MAX_FILE_SIZE
        invoice = self.cleaned_data['invoice']
        if invoice and invoice.size > max_upload_size:
            raise forms.ValidationError(_('Please keep file size under {}. (Current file is {}.)').format(
                 filesizeformat(max_upload_size), filesizeformat(invoice.size)))
        return invoice


class InvoiceTotalForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('How much business have you done with this company over the past 12 months?', {'rows': (('billing_new',),)}),
        ('Or if there\'s a public link you can use as proof, add it here', {'rows': (('proof_url',),)}),
        ('Upload as many documents as needed to prove that amount', {}),
    )

    class Meta:
        model = ClientReference
        fields = ('billing_new', 'proof_url')

    def __init__(self, *args, **kwargs):
        super(InvoiceTotalForm, self).__init__(*args, **kwargs)
        self.fields['billing_new'].label = 'Total Amount'
        self.fields['proof_url'].label = 'Public URL (Recent News Article or Case Study)'
        self.fields['proof_url'].widget.input_type = 'text'
        self.__setup_fieldsets__()


class InvoiceTotalUrlForm(InvoiceTotalForm):

    def __init__(self, *args, **kwargs):
        super(InvoiceTotalUrlForm, self).__init__(*args, **kwargs)
        self.fields['proof_url'].required = True


class BaseInvoiceFormSet(forms.BaseInlineFormSet):
    def add_fields(self, form, index):
        super(BaseInvoiceFormSet, self).add_fields(form, index)
        form.fields['invoice'].label = '{} {}'.format(form.fields['invoice'].label, index + 1)

    def clean(self):
        non_deleted_forms = self.total_form_count()
        non_empty_forms = 0
        for i in xrange(0, self.total_form_count()):
            form = self.forms[i]
            if self.can_delete and self._should_delete_form(form):
                non_deleted_forms -= 1
            if not (form.instance.id is None and not form.has_changed()):
                non_empty_forms += 1
        if non_deleted_forms < 1 or non_empty_forms < 1:
            raise forms.ValidationError('We require at least one invoice to verify this client.')

InvoiceFormSet = inlineformset_factory(ClientReference, Invoice, form=InvoiceForm, formset=BaseInvoiceFormSet, max_num=5, extra=5, fields=('invoice', 'invoice_amount', 'invoice_date'))


class ClientConfirmForm(forms.ModelForm, FieldsetMixin):
    rating = NPSField()
    has_ended = forms.TypedChoiceField(
        label='Is this relationship ongoing ?',
        coerce=lambda x: x == 'True',
        choices=((False, 'Yes, I am a current client'),
                 (True, 'No, I was a client but am no longer')),
        initial=False)
    client_size = forms.ChoiceField(choices=Client.SIZE_CHOICES,
                                    label='No. of Employees')
    client_website = forms.URLField(required=False, label='Company website')
    client_industries = MultiSelectizeModelField(
        label='Industries',
        queryset=Category.industries.all()
    )

    fieldsets = (
        ('', {
            'rows': (
                ('use_alt_name',),
                ('alt_name',),
            )
        }),
        ('Company details', {
            'rows': (
                ('client_size', 'client_industries',),
                ('client_website',),
            )
        }),
        ('Duration', {
            'rows': (
                ('has_ended', 'duration',),
                ('duration_private',),
            )
        }),
        ('Billing', {
            'rows': (
                ('billing_new',),
                ('billing_private',),
            )
        }),
        ('Private information', {
            'rows': (
                ('rating',),
            )
        }),
        ('Testimonial', {
            'rows': (
                ('review',),
                ('role', 'full_name'),
                ('review_anonymous',),
            )
        }),
    )

    class Meta:
        model = ClientReference
        fields = ('rating', 'review', 'alt_name', 'use_alt_name',
                  'billing_new', 'billing_private', 'duration',
                  'duration_private', 'has_ended', 'review_anonymous',
                  'client_industries', 'client_size', 'role', 'full_name',
                  'client_website',)
        labels = {
            'alt_name': '',
            'billing_private': 'This is correct',
            'duration_private': 'Don\'t publish this information ',
            'review_anonymous': 'It\'s OK to display my name with the '
                                'testimonial',
            'full_name': 'Your full name'
        }
        help_texts = {
            'billing_new': 'This information will never be shared publicly and '
                       'will only be used to verify the importance of your '
                       'client relationship. The higher the billing, the '
                       'better your ranking.'
        }

    def __init__(self, *args, **kwargs):
        super(ClientConfirmForm, self).__init__(*args, **kwargs)
        self.fields['rating'].label = (
            'How likely is it that you would recommend %s'
            ' to a  friend or colleague ?'
            % self.instance.vendor.name)
        self.fields['rating'].help_text = (
            'This is NOT shared publicly or with anyone at %s<br>'
            'This information is only used by our ranking robot'
            % self.instance.vendor.name)

        self.fields['review'].label = (
            'How has it been working with %s so far ? Specific examples '
            'are very powerful.' % self.instance.vendor.name)

        self.fields['billing_new'].label = (
            '%s said total billing with %s in the last 12 months'
            ' was approximately'
            % (self.instance.created_by.first_name,
               self.instance.vendor.name))
        self.fields['billing_new'].widget.attrs['selectize-placeholder'] = ' '
        self.fields['billing_private'].widget.attrs['ignore-enhance'] = 'true'

        self.fields['duration'].label = (
            '%s said you have been / you were a client for '
            % self.instance.created_by.first_name)

        self.fields['role'].label = (
            'Your title/role at %s'
            % self.instance.client.name)

        self.fields['duration_private'].widget.attrs['ignore-enhance'] = 'true'
        self.fields['use_alt_name'].widget.attrs['ignore-enhance'] = 'true'
        self.fields['review_anonymous'].widget.attrs['ignore-enhance'] = 'true'

        self.fields['use_alt_name'] = forms.TypedChoiceField(
            label=('Listing verified clients like you on Proven.cc will '
                   'greatly help %s' % self.instance.vendor.name),
            coerce=lambda x: x == 'True',
            choices=((False, ('Use %s as %s suggested'
                              % (self.instance.client.name,
                                 self.instance.created_by.first_name))),
                     (True, 'No, list my company as:')),
            initial=False,
            widget=forms.RadioSelect(attrs={'data-selectize': None}))

        self.initial['review_anonymous'] = not self.initial['review_anonymous']
        self.initial['client_size'] = self.instance.client.size
        self.initial['client_website'] = self.instance.client.website
        self.initial['client_industries'] = self.instance.client.industries.all()
        self.fields['alt_name'].set_required(False)
        self.fields['duration'].set_required(False)
        if not self.initial['billing_new']:
            self.fieldsets = self.fieldsets[:3] + self.fieldsets[4:]

        self.__setup_fieldsets__()

    def clean_review_anonymous(self):
        anon = self.cleaned_data.get('review_anonymous')
        return not anon


class ClientEditForm(forms.ModelForm, FieldsetMixin):
    industries = MultiSelectizeModelField(
        label='Industries',
        queryset=Category.industries.all()
    )

    fieldsets = (
        ('', {
            'rows': (
                ('name', 'logo'),
                ('size', 'industries',),
                ('website',),
            )
        }),
    )

    class Meta:
        model = Client
        fields = ('name', 'logo', 'size', 'industries', 'website',)
        labels = {
            'size': 'No. of employees',
        }
        help_texts = {
            'size': 'This helps us understand the size of the client, which '
                    'is one indicator of your quality and ability',
            'logo': 'Showing a logo dramatically improves recognition of the '
                    'client\'s brand and gets you additional views',
            'website': 'Use format http://example.com for the URL',
        }

    def __init__(self, *args, **kwargs):
        super(ClientEditForm, self).__init__(*args, **kwargs)
        self.fields['industries'].set_required(False)
        self.fields['size'].set_required(False)
        self.fields['logo'].max_length = 70
        self.__setup_fieldsets__()


class ClientReferenceEditForm(forms.ModelForm, FieldsetMixin):

    fieldsets = (
        ('', {
            'rows': (
                ('duration', ),
                ('anonymous', ),
            )
        }),
    )

    class Meta:
        model = ClientReference
        fields = ('duration', 'anonymous', )

    def __init__(self, *args, **kwargs):
        super(ClientReferenceEditForm, self).__init__(*args, **kwargs)
        self.__setup_fieldsets__()


class VendorIndustryForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {'rows': (
                ('industry',),
        )},),
    )

    class Meta:
        model = VendorIndustry
        fields = ('industry', 'allocation', 'vendor',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        self.initial_allocation = 0
        super(VendorIndustryForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['allocation'].set_required(False)
        self.fields['vendor'].set_required(False)
        self.fields['vendor'].widget = forms.HiddenInput()
        services = [x.id for x in self.vendor.industries_served.all()]
        self.fields['industry'].queryset = Category.industries.exclude(id__in=services)
        self.fields['industry'].widget.attrs['selectize-create'] = 'true'
        self.fields['industry'].widget.attrs['selectize-create-url'] = Category.get_autocomplete_create_url({
            'kind': Category.KIND_INDUSTRY,
        })

        self.__setup_fieldsets__()

    def clean_vendor(self):
        return self.vendor

    def clean_allocation(self):
        return self.initial_allocation


class VendorEngageProcess(forms.ModelForm, FieldsetMixin):
    engage_process = forms.CharField(label='Note content', widget=forms.Textarea)

    fieldsets = (
        ('', {'rows': (('engage_process',),)},),
    )

    class Meta:
        model = Vendor
        fields = ('engage_process',)

    def __init__(self, *args, **kwargs):
        super(VendorEngageProcess, self).__init__(*args, **kwargs)
        self.__setup_fieldsets__()


class VendorArchiveForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {'rows': (('is_archived',),)},),
    )

    class Meta:
        model = Vendor
        fields = ('is_archived',)

    def __init__(self, *args, **kwargs):
        super(VendorArchiveForm, self).__init__(*args, **kwargs)
        self.__setup_fieldsets__()

    def clean_is_archived(self):
        return True


class VendorProcurement(forms.Form, FieldsetMixin):

    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(kind=get_user_model().KIND_CLIENT))

    fieldsets = (
        ('', {'rows': (('user',),)},),
    )

    class Meta:
        fields = ('user',)

    def __init__(self, *args, **kwargs):
        super(VendorProcurement, self).__init__(*args, **kwargs)
        self.fields['user'].label = 'Select {} contact'.format(get_current_tenant().name)
        self.__setup_fieldsets__()



class VendorProcurementDelete(forms.Form, FieldsetMixin):

    delete = forms.BooleanField(required=False)

    fieldsets = (
        ('', {'rows': (('delete',),)},),
    )

    class Meta:
        fields = ('delete',)

    def __init__(self, *args, **kwargs):
        super(VendorProcurementDelete, self).__init__(*args, **kwargs)
        self.fields['delete'].widget = forms.HiddenInput()
        self.__setup_fieldsets__()

    def clean_delete(self):
        return True


@parsleyfy
class VendorProcurementForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {'rows': (
                ('category', ),
        )},),
    )

    class Meta:
        model = VendorCustomKind
        fields = ('category', 'allocation', 'vendor',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        self.initial_allocation = 0
        super(VendorProcurementForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['allocation'].set_required(False)
        self.fields['vendor'].set_required(False)
        self.fields['vendor'].widget = forms.HiddenInput()
        self.fields['category'].label = "service"

        self.custom_kind = CategoryType.objects.filter(vendor_editable=False).first()
        services = [x.category for x in self.vendor.vendor_custom.filter(category__custom_kind=self.custom_kind)]
        self.fields['category'].queryset = Category.objects.filter(kind=Category.KIND_CUSTOM,
                                                                   custom_kind=self.custom_kind)

        if True:  # self.request.user.is_procurement and Category.can_create(self.request.user):
            self.fields['category'].widget.attrs['selectize-create'] = 'true'
            self.fields['category'].widget.attrs['selectize-create-url'] = Category.get_autocomplete_create_url({
                'kind': Category.KIND_CUSTOM,
                'custom_kind': self.custom_kind.id if self.custom_kind else None,
            })
        self.fields['category'].widget.attrs['data-open-on-focus'] = 'false'
        self.__setup_fieldsets__()

    def clean_vendor(self):
        return self.vendor

    def clean_allocation(self):
        return self.initial_allocation


class VendorProcurementAllocationForm(forms.Form):

    def __init__(self, categories, *args, **kwargs):
        self.categories = categories
        super(VendorProcurementAllocationForm, self).__init__(*args, **kwargs)

    def clean(self):
        total = 0
        for categ in self.categories:
            total += self.cleaned_data.get(unicode(categ.id)) or categ.allocation
        if total != 100:
            raise forms.ValidationError(
                'Sum of all service allocation must be 100%.')
        return self.cleaned_data

    def save(self, *args, **kwargs):
        with transaction.atomic():
            for categ in self.categories:
                categ.allocation = self.cleaned_data.get(unicode(categ.id), 0)\
                    or categ.allocation
                categ.save()


class VendorProfileLogoForm(forms.ModelForm, FieldsetMixin):

    fieldsets = (
        ('Company logo', {
            'rows': (
                ('logo',),
                ('background',),
            )
        }),
    )

    class Meta:
        model = Vendor
        fields = ('logo', 'background')
        help_texts = {
            'logo': 'Clear sharp logos are important for your company to be noticed and recognized',
            'background': 'This is prominently displayed on your company\'s profile so pick a good one',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(VendorProfileLogoForm, self).__init__(*args, **kwargs)
        self.fields['logo'].max_length = 70
        if self.instance.logo:
            self.fields['logo'].label = (
                '<img src="%s" width="150"><br><br>'
                % self.instance.logo.url)

        self.fields['background'].max_length = 70
        if self.instance.background:
            self.fields['background'].label = (
                '<img src="%s" width="150"><br><br>'
                % self.instance.logo.url)

        self.__setup_fieldsets__()

    def clean_logo(self):
        return self.cleaned_data['logo']

    def clean_background(self):
        return self.cleaned_data['background']


class VendorProfileBrochureForm(forms.ModelForm, FieldsetMixin):

    fieldsets = (
        ('Company brochure', {
            'rows': (
                ('brochure',),
            )
        }),
    )

    class Meta:
        model = Vendor
        fields = ('brochure',)
        widgets = {
            'brochure': forms.FileInput(),
        }
        help_texts = {
            'brochure': 'Formats allowed: .ppt, .docx'
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(VendorProfileBrochureForm, self).__init__(*args, **kwargs)
        self.fields['brochure'].max_length = 70
        self.__setup_fieldsets__()


class VendorCustomPrimary(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {'rows': (
                ('primary',),
        )},),
    )

    class Meta:
        model = VendorCustomKind
        fields = ('primary',)

    def __init__(self, *args, **kwargs):
        super(VendorCustomPrimary, self).__init__(*args, **kwargs)
        self.__setup_fieldsets__()


class ProcurementLinkForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {'rows': (
            ('description',),
            ('url',),
        )},),
    )

    class Meta:
        model = ProcurementLink
        fields = ('description', 'url')
        widgets = {
            'url': forms.TextInput(attrs={'placeholder': 'http://www.example.com/'}),
            'description': forms.Textarea(),
        }

    def __init__(self, *args, **kwargs):
        super(ProcurementLinkForm, self).__init__(*args, **kwargs)
        self.fields['description'].initial = (
            'Click on the link below to be redirected to the system'
            ' where you can procure this service')
        self.__setup_fieldsets__()


class VendorStatusChange(forms.ModelForm, FieldsetMixin):
    kind = forms.ChoiceField(choices=Vendor.KIND_CHOICES)
    fieldsets = (
        ('', {'rows': (
                ('kind',),
        )},),
    )

    class Meta:
        model = Vendor
        fields = ('kind',)

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance', None)
        super(VendorStatusChange, self).__init__(*args, **kwargs)
        self.fields['kind'].label = 'Choose a supplier status'
        self.fields['kind'].choices = self.instance.kind_choices
        self.__setup_fieldsets__()


class VendorDiversitySelect(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {'rows': (
            ('diversity',),
        )},),
    )

    class Meta:
        model = Vendor
        fields = ('diversity',)

    def __init__(self, *args, **kwargs):
        self.kind = kwargs.pop('kind')
        super(VendorDiversitySelect, self).__init__(*args, **kwargs)
        self.fields['diversity'].queryset = Diversity.objects.filter(kind=self.kind)
        self.__setup_fieldsets__()


class ClientQueueForm(forms.ModelForm):
    class Meta:
        model = ClientQueue
        fields = ('email', 'notes',)

    def __init__(self, *args, **kwargs):
        super(ClientQueueForm, self).__init__(*args, **kwargs)
        self.fields['notes'].widget.attrs['data-skip'] = True


class VendorClaimForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {'rows': (
            ('email',),
            ('first_name', 'last_name'),
            ('notes',),
        )},),
    )

    class Meta:
        model = VendorClaim
        fields = ('email', 'first_name', 'last_name', 'notes')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(VendorClaimForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['email'].initial = user.email
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['first_name'].widget.attrs['readonly'] = True
            self.fields['last_name'].widget.attrs['readonly'] = True
        self.fields['notes'].widget.attrs['data-skip'] = True
        self.__setup_fieldsets__()
