import os
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import Group
from django.db import connection

from parsley.decorators import parsleyfy
from allauth.account.forms import ChangePasswordForm, LoginForm
from urlobject import URLObject
from notifications.models import Notification

from med_social.forms.mixins import FieldsetMixin
from med_social.forms.base import DeletableFieldsetForm
from med_social.fields import (MultiSelectizeModelField, SelectizeMultiInput)
from med_social.utils import now
from med_social.utils import get_current_tenant, get_absolute_url

from features import models as features
from users.models import UserDivisionRel, SignupToken, User
from divisions.models import Division
from roles.models import Role
from categories.models import Category
from vendors.models import Vendor, VendorType, VendorCategories, VendorRoles
from projects.models import ProposedResource
from locations.models import Location
from .utils import generate_unique_username


class NotificationsForm(forms.Form):
    notifications = forms.ModelMultipleChoiceField(
        queryset=Notification.objects.none())

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(NotificationsForm, self).__init__(*args, **kwargs)
        self.fields['notifications'].queryset = \
            self.request.user.notifications.all()


class UserFilterForm(forms.Form):
    filter_users = forms.ChoiceField(choices=(1,), initial=1)
    location = forms.ModelChoiceField(queryset=Location.objects.all())
    skills = forms.ModelChoiceField(queryset=Category.skills.all())
    role = forms.ModelMultipleChoiceField(queryset=Role.objects.all())

    def __init__(self, *args, **kwargs):
        super(UserFilterForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class AllocationForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('allocation',{'rows':(
            ('start_date', 'end_date'),
            ('allocation',),
            ),}),
        )
    # TODO: Migrate staffed to custom status

    class Meta:
        model = ProposedResource
        fields = ('start_date', 'end_date', 'allocation', 'resource',
                  'changed_by', 'created_by')
        widgets = {
            'resource': forms.HiddenInput,
            'changed_by': forms.HiddenInput,
            'created_by': forms.HiddenInput,
            'start_date': forms.DateInput(attrs={
                'class': 'form-group-inline',
                'placeholder': 'Tap to select'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-group-inline',
                'placeholder': 'Tap to select'
            }),
            'is_staffed': forms.HiddenInput
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.resource = kwargs.pop('resource')
        self.changed_by = kwargs.pop('changed_by')
        self.created_by = kwargs.pop('created_by')
        super(AllocationForm, self).__init__(*args, **kwargs)
        self.fields['resource'].set_required(False)
        self.fields['changed_by'].set_required(False)
        self.fields['created_by'].set_required(False)
        self.__setup_fieldsets__()

    def clean_is_staffed(self):
        return True

    def clean_resource(self):
        return self.resource

    def clean_changed_by(self):
        return self.changed_by

    def clean_created_by(self):
        return self.created_by

def validate_resume_name(value):
    allowed_exts = ['.pdf', '.doc', '.docx',
                    '.odt', '.jpg', '.jpeg',
                    '.png']
    allowed_exts_txt = ', '.join(allowed_exts)

    fname, ext = os.path.splitext(value.name)
    if ext not in allowed_exts:
        raise forms.ValidationError(
            'Only PDF, MS Word, Open Document Format, JPEG, and PNG '
            'files can be uploaded as resumes.'.format(allowed=allowed_exts_txt))


class UserSummaryForm(forms.ModelForm, FieldsetMixin):
    resume = forms.FileField(widget=forms.FileInput,
                             required=False,
                             validators=[validate_resume_name,])
    linkedin_profile_url = forms.URLField(label='LinkedIn profile URL', required=False)

    roles = MultiSelectizeModelField(
        label='Roles',
        help_text=' ',
        queryset=Role.objects.filter(),
        widget=SelectizeMultiInput(native_on_mobile=False),
        required=False)

    categories = MultiSelectizeModelField(
        label='Skills',
        help_text=' ',
        queryset=Category.objects.filter(kind=Category.KIND_SKILL),
    )

    divisions = MultiSelectizeModelField(
        label='Groups',
        help_text=' ',
        queryset=Division.objects.all(),
    )

    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
    }

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'username', 'roles', 'email',
                  'categories', 'skill_level', 'location', 'resume',
                  'linkedin_profile_url', 'bio', 'divisions', 'phone',
                  'is_staffable', 'organization_name')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(UserSummaryForm, self).__init__(*args, **kwargs)

        if features.projects.is_enabled() and self.instance.is_staffable:
            self.fieldsets = (
                ('Basic', {
                    'rows': (
                        ('first_name', 'last_name',),
                        ('username', 'email',),
                        ('phone', 'is_staffable',),
                )},),
                ('Profile (optional)', {
                    'rows': (
                        ('bio',),
                        ('resume', 'linkedin_profile_url',),
                        ('location', 'divisions',),
                        ('categories', 'skill_level'),
                        ('roles',)
                )}),
            )
        else:
            self.fields['is_staffable'].widget = forms.HiddenInput()

            if self.request.user.is_vendor:
                self.fieldsets = (
                    ('', {
                        'rows': (
                            ('first_name', 'last_name',),
                            ('username', 'roles',),
                            ('organization_name', 'is_staffable',),

                    )},),
                    ('YOUR CONTACT INFORMATION', {
                        'rows': (
                            ('email','phone',),
                    )},),
                )
            else:
                self.fieldsets = (
                    ('', {
                        'rows': (
                            ('first_name', 'last_name',),
                            ('username', 'roles',),
                            ('organization_name', 'is_staffable',),
                            ('divisions',)

                    )},),
                    ('YOUR CONTACT INFORMATION', {
                        'rows': (
                            ('email','phone',),
                    )},),
                )

        self.tenant = get_current_tenant()
        if not self.tenant.is_public_instance:
            self.fields['organization_name'].widget = forms.HiddenInput()
        elif self.request.user.is_vendor:
            self.fields['organization_name'].widget = forms.HiddenInput()
        self.instance = getattr(self, 'instance', None)
        if 'bio' in self.fields:
            self.fields['bio'].set_required(False)
            self.fields['bio'].label = 'Bio'
        self.fields['resume'].label = 'Resume'
        self.fields['first_name'].set_required(True)
        self.fields['first_name'].help_text = 'It is nice to meet you!'

        self.fields['last_name'].set_required(True)
        self.fields['roles'].help_text = "We realize that you wear many hats at work - just list the primary ones here"
        self.fields['categories'].set_required(False)
        self.fields['categories'].label = 'Skills'
        self.fields['categories'].help_text = None
        self.fields['phone'].widget.attrs['data-phoneinput'] = 'true'
        self.fields['email'].help_text = "Thanks! you can use this to login  if you forget your username or password"

        if Role.can_create(self.request.user):
            self.fields['roles'].widget.attrs['selectize-create'] = 'true'
            self.fields['roles'].widget.attrs['selectize-create-url'] = \
                Role.get_autocomplete_create_url()

        if Division.can_create(self.request.user):
            self.fields['divisions'].widget.attrs['selectize-create'] = 'true'
            self.fields['divisions'].widget.attrs['selectize-create-url'] = \
                Division.get_autocomplete_create_url()
        self.fields['divisions'].set_required(False)

        self.fields['location'].set_required(False)
        if Location.can_create(self.request.user):
            self.fields['location'].widget.attrs['selectize-create'] = 'true'
            self.fields['location'].widget.attrs['selectize-create-url'] = \
                Location.get_autocomplete_create_url()

        self.fields['categories'].set_required(False)
        if Category.can_create(self.request.user):
            self.fields['categories'].widget.attrs['selectize-create'] = 'true'
            self.fields['categories'].widget.attrs['selectize-create-url'] = \
                Category.get_autocomplete_create_url(
                    {'kind': Category.KIND_SKILL})
        self.fields['skill_level'].set_required(False)
        if self.request.user.is_vendor:
            self.fields['is_staffable'].widget = forms.HiddenInput()
            if self.instance and self.instance.linkedin_profile_url:
                self.fields['linkedin_profile_url'].widget = forms.HiddenInput()

        self.__setup_fieldsets__()

    def clean_is_staffed(self):
        if self.request.user.is_vendor:
            if self.instance:
                return self.instance.is_staffed
        else:
            return self.cleaned_data['is_staffed']

    def clean_linkedin_profile_url(self):
        if self.request.user.is_vendor:
            if self.instance and self.instance.linkedin_profile_url:
                return self.instance.linkedin_profile_url
        return self.cleaned_data['linkedin_profile_url']

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        UserModel = get_user_model()
        user = UserModel.objects.filter(email=email).first()
        if user and user != self.request.user:
            raise forms.ValidationError(_("A user is already registered"
                                        " with this e-mail address."))
        return email

    def clean_username(self):
        username = self.cleaned_data["username"].lower()
        UserModel = get_user_model()
        user = UserModel.objects.filter(username=username).first()
        if user and user != self.request.user:
            raise forms.ValidationError(_("User with this Username already exists."))
        return username

    def save(self, commit=True):
        user = super(UserSummaryForm, self).save(commit=False)
        if commit:
            user.save()

        #FIXME: Replace all this shit with `save_m2m` method
        divs = set(user.divisions.values_list('id', flat=True))
        new_divs = set(self.cleaned_data['divisions'].values_list(
            'id', flat=True))
        to_remove = divs - new_divs
        # TODO: need to move this to independent UI.
        UserDivisionRel.objects.filter(division__in=to_remove, user=user).exclude(is_admin=True).delete()
        for div in new_divs:
            UserDivisionRel.objects.get_or_create(user=user, division_id=div)

        roles = set(user.roles.values_list('id', flat=True))
        new_roles = set(self.cleaned_data['roles'].values_list(
            'id', flat=True))
        to_remove = roles - new_roles
        user.roles.remove(*to_remove)
        user.roles.add(*new_roles)

        categories = set(user.categories.values_list('id', flat=True))
        new_categories = set(self.cleaned_data['categories'].values_list(
            'id', flat=True))
        to_remove = categories - new_categories
        user.categories.remove(*to_remove)
        user.categories.add(*new_categories)
        return user


class UserProfileForm(UserSummaryForm):
    fieldsets = (
        ('Basic', {
            'rows': (
                ('first_name', 'last_name',),
                ('username', 'email',),
            )
        }),
        ('Profile', {
            'rows': (
                ('resume', 'linkedin_profile_url',),
                ('roles', 'location',),
                ('categories', 'skill_level',)
            )
        }),
    )

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'roles', 'email', 'resume',
                  'linkedin_profile_url', 'location', 'skill_level',
                  'username',)


class VendorBaseForm(forms.ModelForm, FieldsetMixin):
    class Meta:
        model = Vendor
        step = None
        exclude = ()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
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


class VendorBasicForm(VendorBaseForm):
    summary = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Summary of what you do (140 characters)'}))

    fieldsets = (
        ('', {
            'rows': (
                ('name', 'founded',),
                ('email', 'phone',),
                ('summary',),
                ('categories',),
                ('roles',),
                ('story',),
            )
        }),
    )

    class Meta:
        model = Vendor
        fields = ('name', 'categories', 'summary', 'roles', 'story', 'founded', 'email', 'phone')
        labels = {
            'categories': 'Core skills that you provide (note: this is how people will find you)',
            'story': 'Why should clients chose you over your competitors ?',
            'phone': 'Phone no. of lead salesperson',
            'founded': 'Year founded'
            }

        help_texts = {
            'summary': 'Spend time on this - this is often the first and the'
                       ' only thing clients will see about you',
            'story': 'Limit this to three crisp bullet points'
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(VendorBaseForm, self).__init__(*args, **kwargs)
        self.fields['categories'].widget.attrs['selectize-create'] = 'true'
        self.fields['categories'].widget.attrs['selectize-create-url'] = \
            Category.get_autocomplete_create_url({
                'kind': Category.KIND_CATEGORY
            })
        self.fields['roles'].widget.attrs['selectize-create'] = 'true'
        self.fields['roles'].widget.attrs['selectize-create-url'] = \
            Role.get_autocomplete_create_url()
        self.fields['phone'].widget.attrs['data-phoneinput'] = 'true'
        self.__setup_fieldsets__()

    def clean_categories(self):
        vendor = self.request.user.vendor
        previous_categories = set([category.skill for category in
                                   VendorCategories
                                   .objects.filter(vendor=vendor)])
        current_categories = set(self.cleaned_data['categories'])

        deleted_categories = previous_categories.difference(current_categories)
        VendorCategories.objects.filter(skill__in=deleted_categories).delete()

        for category in current_categories:
            VendorCategories.objects.get_or_create(vendor=vendor,
                                                   skill=category)
        return self.cleaned_data['categories']

    def clean_roles(self):
        vendor = self.request.user.vendor
        previous_roles = set([role.role for role in
                              VendorRoles.objects.filter(vendor=vendor)])
        current_roles = set(self.cleaned_data['roles'])

        deleted_roles = previous_roles.difference(current_roles)
        VendorRoles.objects.filter(role__in=deleted_roles).delete()

        for role in self.cleaned_data['roles']:
            VendorRoles.objects.get_or_create(vendor=self.request.user.vendor,
                                              role=role)
        return self.cleaned_data['roles']


@parsleyfy
class VendorDetailForm(VendorBaseForm):
    categories =\
        MultiSelectizeModelField(required=False,
                                 queryset=Category.objects
                                 .filter(kind=Category.KIND_CATEGORY),
                                 label="Specialities",
                                 widget=SelectizeMultiInput(
                                     native_on_mobile=False,
                                     attrs=
                                     {'placeholder': 'Choose categories'}))

    fieldsets = (
        ('', {
            'rows': (
                ('categories',),
            )
        }),
    )

    class Meta:
        model = Vendor
        fields = ('categories',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(VendorDetailForm, self).__init__(*args, **kwargs)

        self.fields['categories'].widget.attrs['selectize-create'] = 'true'
        self.fields['categories'].widget.attrs['selectize-create-url'] = \
            Category.get_autocomplete_create_url({
                'kind': Category.KIND_CATEGORY
            })

        self.__setup_fieldsets__()


@parsleyfy
class VendorWebForm(VendorBaseForm):

    fieldsets = (
        ('', {
            'rows': (
                ('logo', 'website'),
                ('linkedin', 'github'),
                ('facebook','twitter'),
                ('video', 'brochure')
            )
        }),
    )

    class Meta:
        model = Vendor
        fields = ('website','logo', 'github', 'video', 'twitter',
                  'facebook', 'linkedin', 'brochure',)
        next_step = None

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(VendorWebForm, self).__init__(*args, **kwargs)
        self.fields['website'].widget.attrs['placeholder'] = 'http://mycompany.com'
        self.fields['twitter'].widget.attrs['placeholder'] = '@twitterhandle'
        self.fields['facebook'].widget.attrs['placeholder'] = 'http://facebook.com/mycompany'
        self.fields['linkedin'].widget.attrs['placeholder'] = 'http://linkedin.com/mycompany'
        self.fields['logo'].widget.attrs['placeholder'] = 'your company logo here'
        self.fields['github'].widget.attrs['placeholder'] = 'github_username'
        self.fields['video'].widget.attrs['placeholder'] = 'http://youtube.com/watch/...'
        self.__setup_fieldsets__()


class UserPermissionForm(DeletableFieldsetForm, FieldsetMixin):
    groups = MultiSelectizeModelField(queryset=Group.objects.none(),
        widget=SelectizeMultiInput(native_on_mobile=False,
            attrs={'placeholder': 'Choose Groups'}))

    # fieldsets = (
    #     ('', { 'rows':(
    #             ('groups',),
    #         ),
    #     }),
    # )

    class Meta:
        model = get_user_model()
        fields = ('groups',)
        deletable = False

    def __init__(self, *args, **kwargs):
        DeletableFieldsetForm.__init__(self, *args, **kwargs)
        super(UserPermissionForm, self).__init__(*args, **kwargs)
        #self.__setup_fieldsets__()
        if self.request.user.is_client:
            queryset = Group.objects.filter(vendor=None)
        elif self.request.user.is_vendor:
            queryset = self.request.user.vendor.groups.all()
        self.fields['groups'].queryset = queryset
        self.fields['groups'].widget = SelectizeMultiInput(
            choices=queryset.values_list('id', 'display_name'))

    def save(self, *args, **kwargs):
        user = super(UserPermissionForm, self).save(*args, **kwargs)
        groups = set(user.groups.values_list('id', flat=True))
        new_groups = set(self.cleaned_data['groups'].values_list(
            'id', flat=True))
        to_remove = groups - new_groups
        user.groups.remove(*to_remove)
        user.groups.add(*new_groups)
        return user


class UserInviteForm(forms.ModelForm, FieldsetMixin):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-group-inline'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-group-inline'}))
    email = forms.EmailField(required=True)
    resume = forms.FileField(widget=forms.FileInput, label='Resume (optional)', required=False,
                             validators=[validate_resume_name,])
    linkedin_profile_url = forms.URLField(label='LinkedIn profile URL', required=False)
    invite = forms.BooleanField(
        label='Invite to join Proven', initial=False, required=False,
        help_text='Uncheck if you do not wish to involve the user in '
        'staffing discussions at this time. You can always invite them later '
        'via "Invite to join Proven" action on their user profile.')

    categories = MultiSelectizeModelField(
        label='Skills',
        queryset=Category.objects.filter(kind=Category.KIND_SKILL),
        required=False,
        widget=SelectizeMultiInput(native_on_mobile=False),
    )

    fieldsets = (
        ('Add colleague',{
            'rows':(
                    ('first_name', 'last_name'),
                    ('email', 'invite',),
                    ('vendor', 'is_staffable',),
                    ('roles', 'categories',),
                    ('resume','linkedin_profile_url'),
                ),
            }),
        )

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'vendor', 'email', 'username', 'categories',
                  'groups', 'resume', 'linkedin_profile_url',
                  'roles', 'is_staffable',)

        labels = {
            'vendor': 'Organization',
            'resume': 'Resume (optional)'
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.password = kwargs.pop('password')
        self.vendor = kwargs.pop('vendor', None)

        super(UserInviteForm, self).__init__(*args, **kwargs)


        if features.projects.is_enabled():
            self.fieldsets = (
            ('',{
                'rows':(
                        ('first_name', 'last_name'),
                        ('email', 'invite',),
                        ('vendor', 'is_staffable',),
                        ('roles', 'categories',),
                        ('resume','linkedin_profile_url'),
                    ),
                }),
            )
        else:
            self.fields['invite'].widget = forms.HiddenInput()
            self.fieldsets = (
            ('',{
                'rows':(
                        ('first_name', 'last_name'),
                        ('email',),
                        ('invite',),
                        ('vendor', 'is_staffable',)
                    ),
                }),
            )


        if self.request.user.is_vendor:
            self.fields['vendor'].widget = forms.HiddenInput()
        elif self.vendor:
            self.fields['vendor'].widget = forms.HiddenInput()

        self.fields['vendor'].set_required(False)
        self.fields['vendor'].empty_label = get_current_tenant()

        self.fields['roles'].set_required(False)
        if Role.can_create(self.request.user):
            self.fields['roles'].widget.attrs['selectize-create'] = 'true'
            self.fields['roles'].widget.attrs['selectize-create-url'] = \
                Role.get_autocomplete_create_url()

        self.fields['categories'].set_required(False)
        if Category.can_create(self.request.user):
            self.fields['categories'].widget.attrs['selectize-create'] = 'true'
            self.fields['categories'].widget.attrs['selectize-create-url'] = \
                Category.get_autocomplete_create_url({
                    'kind': Category.KIND_SKILL
                })
        self.fields['vendor'].widget.attrs['selectize-placeholder'] = ('Type to search')
        self.fields['is_staffable'].widget = forms.HiddenInput()
        self.fields['groups'].widget = forms.HiddenInput()
        self.fields['groups'].set_required(False)
        self.fields['username'].widget = forms.HiddenInput()

        self.fields['username'].set_required(False)

        self.__setup_fieldsets__()

    def clean_username(self):
        email = self.cleaned_data.get('email', '').split('@')[0]
        if not email:
            raise forms.ValidationError('Email address is required')
        username = generate_unique_username([
            self.cleaned_data.get('first_name'),
            self.cleaned_data.get('last_name'),
            email
        ])
        return username

    def clean_vendor(self):
        if self.vendor:
            return self.vendor
        if self.request.user.is_vendor:
            return self.request.user.vendor
        return self.cleaned_data['vendor']

    def clean_invite(self):
        if not features.projects.is_enabled():
            return True
        return self.cleaned_data['invite']

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        domain = email.split('@')[-1]
        vendor = self.cleaned_data.get('vendor', '')
        tenant = connection.get_tenant()
        client_domains = [d.strip() for d in tenant.email_domain.lower().split(',')]
        UserModel = get_user_model()

        if not tenant.is_public_instance:
            if not vendor and domain not in client_domains:
                raise forms.ValidationError(
                    'Only %s email addresses are allowed for this organisation' % ', '.join(client_domains))

        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError(_("A user is already registered with this e-mail address."))

        return email

    def clean(self):
        cd = super(UserInviteForm, self).clean()
        if cd.get('vendor'):
            cd['groups'] = Group.objects.filter(vendor=cd['vendor'], kind=Group.DEFAULT_USER)
        else:
            cd['groups'] = Group.objects.filter(vendor=None, kind=Group.DEFAULT_USER)

        return cd

    def save(self, *args, **kwargs):
        commit = kwargs.pop('commit', True)
        kwargs['commit'] = True
        user = super(UserInviteForm, self).save(*args, **kwargs)
        user.kind = user.KIND_CLIENT
        user.set_password(self.password)
        if commit:
            user.save()
        return user


class PasswordSetForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('instance', None)
        self.user = kwargs['user'] = kwargs.pop('request').user
        super(PasswordSetForm, self).__init__(*args, **kwargs)
        self.fields.pop('oldpassword')
        self.fields['password1'].help_text = ('Password must be at least 8 '
            'characters long and contain at least 1 upper case and 1 lower case alphabet '
            ' and a digit.')

    def save(self, *args, **kwargs):
        super(PasswordSetForm, self).save()
        return self.user


class UserSignupForm(forms.ModelForm, FieldsetMixin):
    email = forms.EmailField(required=True)

    fieldsets = (
        ('', {'rows': (
                ('first_name',),
                ('last_name',),
                ('email',),
        )}),
    )

    class Meta:
        model = SignupToken
        fields = ('first_name', 'last_name', 'email',)

    def __init__(self, *args, **kwargs):
        super(UserSignupForm, self).__init__(*args, **kwargs)
        tenant = connection.get_tenant()

        self.fields['email'].label = ''
        self.__setup_fieldsets__()

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        domain = email.split('@')[-1]
        tenant = connection.get_tenant()
        email_domain = tenant.email_domain or ''
        client_domains = [d.strip() for d in email_domain.lower().split(',')]
        client_domains = [d for d in client_domains if d]

        if not tenant.is_public_instance and domain not in client_domains:
            raise forms.ValidationError(
                'Only %s email addresses are allowed' % ', '.join(client_domains))

        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError(
                'User with this email already exists')
        return email


class UserResendInvite(forms.Form, FieldsetMixin):
    message = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Summary of what you do (140 characters)',
                                     'autoresize': 'false', 'style': 'height: 50em;'}))

    fieldsets = (
        ('', {'rows': (
                ('message',),
        )}),
    )

    def __init__(self, *args, **kwargs):
        self.tenant = connection.get_tenant()
        self.request = kwargs.pop('request')
        self.recipient = kwargs.pop('recipient')
        super(UserResendInvite, self).__init__(*args, **kwargs)
        self.fields['message'].label = 'Feel free to edit the following draft email and hit send at the bottom of this page'
        self.fields['message'].initial = \
            ("Hi {username},\n\n"
             "Welcome to the beta collaboration platform for {current_tenant} suppliers."
             "This private website will allow {current_tenant} employees to search and "
             "find existing {current_tenant} suppliers, view work history with "
             "{current_tenant}, and initiate requests. This website will be available to "
             "all {current_tenant} employees from the {current_tenant} Intranet "
             "and will be powered by the Proven platform.\n\n"
             "This will offer you and your company the opportunity to showcase your "
             "capabilities and past successes at {current_tenant}, and provide "
             "with supplier capability.\n\n"
             "Please create an account for yourself and your company by using the "
             "following personalized link:\n\n"
             "<<signup_url>>\n\n"
             "(For security, this link will expire in 48 hours)\n\n"
             "After you have created a username and password using the above link, "
             "you can access the website from {tenant_url}. Your email address is "
             "your user name and if you forget your password, you can create a new one "
             "using your email address.\n\n"
             "If you have any questions about the pilot, please contact {tenant_email}."
             " If you have any questions about the Proven platform, please contact Suzanne Jordan"
             " at suzanne@proven.cc."
             "This website is available from {current_tenant}'s intranet or directly at "
             "{tenant_url}\n\nBest,\n\n{sender},\n\n{sender_email}".format(current_tenant=self.tenant.name,
                                                                           tenant_url=get_absolute_url('/'),
                                                                           sender=self.request.user.get_name_display(),
                                                                           sender_email=self.request.user.email,
                                                                           username=self.recipient.first_name,
                                                                           tenant_email=self.tenant.email))
        self.__setup_fieldsets__()


class NotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = (
            'text_rfp_new', 'text_rfp_message', 'text_bid_change', 'text_bid_win', 'text_bid_lose',
            'email_rfp_new', 'email_rfp_message', 'email_bid_change', 'email_bid_win', 'email_bid_lose',
        )


class CustomLoginForm(LoginForm):
    '''Customized login form based on allauth's implementation
    '''

    def __init__(self, *args, **kwargs):
        error_message = _('Have you forgotten your password? '
                          'Want to try again?')
        self.error_messages['email_password_mismatch'] = error_message
        self.error_messages['username_password_mismatch'] = error_message
        self.error_messages['username_email_password_mismatch'] = error_message
        super(CustomLoginForm, self).__init__(*args, **kwargs)
