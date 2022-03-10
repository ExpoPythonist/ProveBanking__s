from datetime import datetime, timedelta
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import UserDivisionRel, SignupToken, SEOMetadata


Account = get_user_model()
csrf_protect_m = method_decorator(csrf_protect)


class AccountCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password.
    """
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = Account
        fields = ('email', 'username',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(AccountCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class AccountChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()
    # pending_setup_steps = forms.MultipleChoiceField(choices=Account.SETUP_STEP_CHOICES)
    linkedin_profile = forms.CharField(max_length=1550, required=False, widget=forms.widgets.TextInput(attrs={
        'readonly': True,
        'class': 'vTextField',
        'style': 'display: none;'
    }))

    class Meta:
        model = Account
        exclude = ()

    def __init__(self, *args, **kwargs):
        if 'initial' not in kwargs.keys():
            kwargs['initial'] = {}
        user = kwargs['instance']
        linkedin_url = user.get_linkedin_url()
        kwargs['initial']['linkedin_profile'] = linkedin_url
        super(AccountChangeForm, self).__init__(*args, **kwargs)
        # self.fields['categories'].required = False
        # self.fields['industries'].required = False
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['linkedin_profile'].help_text = \
                '<a href="%s" target="_blank">%s</a>' % (linkedin_url, linkedin_url)

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class IsAvailableListFilter(admin.SimpleListFilter):
    title = _("Available")
    parameter_name = 'available'

    def lookups(self, request, model_admin):
        return (
            ("1", _('Available')),
            ("2", _('Unavailable')),
        )

    def queryset(self, request, queryset):
        return queryset.filter()


class JoinDateListFilter(admin.SimpleListFilter):
    title = _("Joining Date")
    parameter_name = 'join_when'

    def lookups(self, request, model_admin):
        return (
            ("1", _('last 24 hours')),
            ("2", _('last week')),
            ("3", _('older than week')),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            temp = datetime.now() - timedelta(days=1)
            return queryset.filter(date_joined__gte=temp)
        elif self.value() == '2':
            temp = datetime.now() - timedelta(days=7)
            return queryset.filter(date_joined__gte=temp)
        elif self.value() == '3':
            temp = datetime.now() - timedelta(days=7)
            return queryset.filter(date_joined__lt=temp)


class LoginDateListFilter(admin.SimpleListFilter):
    title = _("First login")
    parameter_name = 'login_when'

    def lookups(self, request, model_admin):
        return (
            ("1", _('last 24 hours')),
            ("2", _('last week')),
            ("3", _('older than week')),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            temp = datetime.now() - timedelta(days=1)
            return queryset.filter(first_login__gte=temp)
        elif self.value() == '2':
            temp = datetime.now() - timedelta(days=7)
            return queryset.filter(first_login__gte=temp)
        elif self.value() == '3':
            temp = datetime.now() - timedelta(days=7)
            return queryset.filter(first_login__lt=temp)


class AccountAdmin(UserAdmin):
    # The forms to add and change user instances
    form = AccountChangeForm
    add_form = AccountCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    fieldsets = (
        (None, {'fields': ('username', 'password', 'linkedin_profile', 'vendor')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email',)}),
        (_('Other info'), {'fields': ('kind', 'meta', 'pending_setup_steps')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    list_display = ('username', 'email', 'first_name', 'last_name',
                    'kind', 'is_staff',
                    'date_joined', 'last_login', 'linkedin_url')
    list_filter = ('kind', JoinDateListFilter, LoginDateListFilter,
                   'is_staff', 'is_superuser', 'is_active',)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined', 'username',)
    filter_horizontal = ('groups', 'user_permissions',)

    def linkedin_url(self, obj):
        if obj.linkedin_account:
            return u'<a href="{0}"> {0} </a>'.format(
                        obj.get_linkedin_url())
        else:
            return ''

    linkedin_url.allow_tags = True


class DivisionRelAdmin(admin.ModelAdmin):
    list_filter = ('is_admin', 'division')

    class Meta:
        model = UserDivisionRel
        exclude = tuple()

admin.site.register(UserDivisionRel, DivisionRelAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(SignupToken)
admin.site.register(SEOMetadata)
