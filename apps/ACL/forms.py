from django import forms
from django.contrib.auth.models import Permission, Group
from django.db.models import Q
from django.utils.translation import ugettext as _

from med_social.utils import slugify
from med_social.fields import MultiSelectizeModelField, SelectizeMultiInput
from med_social.forms.base import DeletableFieldsetForm
from med_social.forms.mixins import FieldsetMixin


class GroupForm(DeletableFieldsetForm, FieldsetMixin):
    permissions = MultiSelectizeModelField(
        queryset=Permission.objects.none(),
        widget=SelectizeMultiInput(native_on_mobile=False, attrs={'placeholder': 'Choose Permissions'}),
    )

    fieldsets = (
        ('', {
            'rows': (
                ('display_name',),
                ('permissions',),
            ),
        }),
    )

    class Meta:
        model = Group
        fields = ('display_name', 'permissions', 'name', 'vendor',)
        deletable = False
        labels = {
            'display_name': 'Group name',
        }

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.fields['permissions'].queryset = self.get_perms(self.request.user)
        choices = []
        for a in self.fields['permissions'].choices:
            choices.append((a[0], a[1].rsplit('|')[-1].strip()))
        self.fields['permissions'].choices = choices
        self.fields['name'].required = False
        self.fields['name'].widget = forms.HiddenInput()
        self.fields['vendor'].required = False
        self.fields['vendor'].widget = forms.HiddenInput()

    def clean_vendor(self):
        return self.request.user.vendor

    def clean_display_name(self):
        display_name = self.cleaned_data['display_name']
        if ':' in display_name:
            raise forms.ValidationError(_('display name cannot contain :'))
        return display_name

    def clean_name(self):
        display_name = slugify(self.data['display_name'])
        if self.request.user.is_client:
            return 'client:{}'.format(display_name)
        elif self.request.user.is_vendor:
            return '{0}:{1}'.format(self.request.user.vendor.id, display_name)

    def clean(self):
        qs = Group.objects.all()
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.filter(name=self.cleaned_data['name']).exists():
            raise forms.ValidationError('Another group with that name already exisits')
        return self.cleaned_data

    def get_perms(self, user):
        if user.is_client:
            qs = Q(visibility=Permission.CLIENT)
        else:
            qs = Q(visibility=Permission.VENDOR)
        qs = qs | Q(visibility=Permission.ALL)
        return Permission.objects.filter(qs)

    def save(self, *args, **kwargs):
        commit = kwargs.get('commit', True)
        group = super(GroupForm, self).save(*args, **kwargs)
        saved = False
        if not group.id:
            group.save()
            saved = True

        permissions = set(group.permissions.exclude(visibility=None).values_list('id', flat=True))
        new_permissions = set(self.cleaned_data['permissions'].values_list('id', flat=True))
        to_remove = permissions - new_permissions
        group.permissions.remove(*to_remove)
        group.permissions.add(*new_permissions)

        if not saved and commit:
            group.save()
        return group
