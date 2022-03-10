from django import forms
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

from parsley.decorators import parsleyfy

from med_social.forms.mixins import FieldsetMixin
from med_social.fields import (MultiSelectizeModelField, SelectizeMultiInput,
                               LazyModelChoiceField,)
from autoslug.utils import slugify

from divisions.models import Division
from vendors.models import Vendor
from features import models as features
from locations.models import Location
from categories.models import Category, SkillLevel
from roles.models import Role
from rates.models import Rate

from .models import (Project, StaffingResponse, StaffingRequest,
                     ProposedResource, ProposedResourceStatus, StatusFlow,
                     RequestVendorRelationship, DeliverableResponse)


class AddUserToProjectForm(forms.ModelForm):
    class Meta:
        model = ProposedResource
        exclude = ()

class SearchForm(forms.Form):
    q = forms.CharField(initial='')

    def clean_q(self):
        return self.cleaned_data.get('q', '')


def save_vendors(request, vendors, user):
    vendors = set(vendors)
    old_vendors = set(request.vendors.values_list('id', flat=True))
    to_remove = old_vendors - vendors
    request.request_vendors.filter(vendor__id__in=to_remove).delete()
    for vendor in vendors:
        RequestVendorRelationship.objects.get_or_create(
            request=request, vendor_id=vendor, defaults={
                'created_by': user
            })


def save_users(request, users, user, status=None):
    if not status:
        PRS = ProposedResourceStatus
        initiated = PRS.objects.filter(value=PRS.INITIATED)
        if initiated.exists():
            status = initiated[0]
    for resource in users:
        p, _ = ProposedResource.objects.get_or_create(
            resource=resource, project=request.project, request=request,
            defaults={
                'role': request.role,
                'location': request.location,
                'status': status,
                'created_by': user,
                'changed_by': user,
                'start_date': request.start_date,
                'end_date': request.end_date
            }
        )


class StaffingBaseForm(forms.ModelForm, FieldsetMixin):
    class Meta:
        model = StaffingRequest
        exclude = ()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.project = kwargs.pop('project')
        super(StaffingBaseForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        save_m2m_data = kwargs.pop('save_m2m_data', True)
        kwargs['commit'] = False
        obj = super(StaffingBaseForm, self).save(*args, **kwargs)
        obj.update_status()
        obj.save()
        if save_m2m_data:
            self.save_m2m()
        return obj


class StaffingBasicForm(StaffingBaseForm):
    fieldsets = (
        ('', {'rows': (
            ('project',),
            ('role', 'location',),
            ('categories',),
            ('num_resources', 'allocation'),
            ('start_date', 'end_date'),
            )
        }),
    )

    class Meta:
        model = StaffingRequest
        fields = ('role', 'location', 'categories', 'project', 'kind',
                  'created_by', 'num_resources', 'allocation', 'max_rate',
                  'title', 'start_date', 'end_date',)

    def __init__(self, *args, **kwargs):
        self.default_values = kwargs.pop('default_values', {})
        instance = kwargs.get('instance')
        self.kind = kwargs.pop('kind', None)
        if instance:
            self.kind = instance.kind
        super(StaffingBasicForm, self).__init__(*args, **kwargs)

        self.fields['start_date'].set_required(False)
        self.fields['end_date'].set_required(False)
        if self.instance and self.instance.kind == StaffingRequest.KIND_FIXED:
            self.fields['role'].set_required(False)

        if self.project:
            self.fields['project'].set_required(False)
            self.fields['project'].widget = forms.HiddenInput()
        elif Project.can_create(self.request.user):
            self.fields['project'].widget.attrs['data-kind'] = 'project'
            self.fields['project'].help_text = ('or <a href="{}" '
                'data-target="#genericModal" data-toggle="modal">'
                'add new project</a>').format(reverse('projects:create'))
        self.fields['kind'].set_required(False)
        self.fields['kind'].widget = forms.HiddenInput()
        self.fields['created_by'].set_required(False)
        self.fields['created_by'].widget = forms.HiddenInput()
        self.fields['categories'].help_text = ' '
        self.fields['categories'].label = 'Skills'
        self.fields['categories'].queryset = Category.skills.all()


        if 'role' in self.fields and Role.can_create(self.request.user):
            self.fields['role'].widget.attrs['selectize-create'] = 'true'
            self.fields['role'].widget.attrs['selectize-create-url'] = \
                Role.get_autocomplete_create_url()

        if Category.can_create(self.request.user):
            self.fields['categories'].widget.attrs['selectize-create'] = 'true'
            self.fields['categories'].widget.attrs['selectize-create-url'] = \
                Category.get_autocomplete_create_url({
                    'kind': Category.KIND_SKILL
                })

        if Location.can_create(self.request.user):
            self.fields['location'].widget.attrs['selectize-create'] = 'true'
            self.fields['location'].widget.attrs['selectize-create-url'] = \
                Location.get_autocomplete_create_url()

        if self.kind == StaffingRequest.KIND_FIXED:
            self.fields.pop('role')
            self.fields.pop('num_resources')
            self.fields.pop('allocation')
            self.fields['title'].set_required(True)

            self.fieldsets = (
                ('', {'rows': (
                    ('project',),
                    ('title',),
                    ('max_rate', 'location',),
                    ('categories',),
                    )
                }),
            )
        else:
            self.fields.pop('max_rate')

        self.__setup_fieldsets__()

    def clean_project(self):
        if self.project:
            return self.project
        else:
            return self.cleaned_data.get('project')

    def clean_kind(self):
        return self.kind

    def clean_created_by(self):
        return self.request.user

    def clean(self):
        cd = super(StaffingBasicForm, self).clean()
        if cd.get('users') and not cd.get('status'):
            self.add_error('status', forms.ValidationError(
                'You must select a status to assign the selected users'))

        return cd

    def save(self, *args, **kwargs):
        kwargs['commit'] = False
        kwargs['save_m2m_data'] = False
        req = super(StaffingBasicForm, self).save(*args, **kwargs)
        project = self.cleaned_data.get('project')
        req.start_date = project.start_date
        req.end_date = project.end_date

        for field, value in self.default_values.items():
            if not getattr(req, field):
                setattr(req, field, value)
        req.save()
        self.save_m2m()
        return req


@parsleyfy
class StaffingAdvancedForm(StaffingBaseForm):
    start_date = forms.DateField(label='Start', widget=forms.DateInput(
        format='%d %b, %Y', attrs={'placeholder': 'Tap to select'}))

    end_date = forms.DateField(label='End', widget=forms.DateInput(
        format='%d %b, %Y', attrs={'placeholder': 'Tap to select'}),
    )

    owners = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.filter(vendor=None),
        label='Contact(s)', help_text=' ')

    viewable_by = forms.ChoiceField(
        label='Visible to',
        help_text=' ',
        widget=forms.RadioSelect(attrs={
            'data-selectize': 'no',
        })
    )

    fieldsets = (
        ('', {'rows': (
            ('viewable_by',),
            ('owners',),
            ('skill_level',),
            ('title',),
            ('description',),
        )}),
    )


    class Meta:
        model = StaffingRequest
        fields = ('is_public', 'skill_level',
                  'owners', 'title', 'description')

    def __init__(self, *args, **kwargs):
        kwargs.pop('default_values', None)
        instance = kwargs.get('instance')
        self.kind = kwargs.pop('kind', None)
        if instance:
            self.kind = instance.kind
        super(StaffingAdvancedForm, self).__init__(*args, **kwargs)
        self.fields['viewable_by'].choices = (
            ('1', 'All existing suppliers',),
            ('2', 'Selected suppliers only',),
        )
        self.fields['is_public'].widget = forms.HiddenInput()
        self.fields['is_public'].set_required(False)
        if self.instance:
            self.fields['viewable_by'].initial = ('1'
                                                  if self.instance.is_public
                                                  else '2')
        else:
            self.fields['viewable_by'].initial = '1'
        self.fields['skill_level'].set_required(False)

        if self.instance and self.instance.kind == self.instance.KIND_FIXED:
            self.fields['title'].widget = forms.HiddenInput()

        if self.kind == StaffingRequest.KIND_FIXED:
            self.fields.pop('skill_level')
            self.fields.pop('title')

            self.fieldsets = (
                ('', {'rows': (
                    ('viewable_by',),
                    ('start_date', 'end_date'),
                    ('owners',),
                    ('description',),
                )}),
            )

        self.__setup_fieldsets__()

    def clean_title(self):
        if self.instance and self.instance.kind == self.instance.KIND_FIXED:
            return self.instance.title
        else:
            return self.cleaned_data.get('title')

    def clean(self):
        cd = super(StaffingAdvancedForm, self).clean()
        cd['is_public'] = cd.get('viewable_by') == '1'
        return cd


class StaffingACLForm(forms.ModelForm):
    class Meta:
        model = StaffingRequest
        fields = ('is_public',)

    def save(self, *args, **kwargs):
        obj = super(StaffingACLForm, self).save(*args, **kwargs)
        obj.vendors.clear()
        return obj


class StaffingACLVendorsForm(forms.ModelForm):
    class Meta:
        model = StaffingRequest
        fields = ('vendors',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(StaffingACLVendorsForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        kwargs['commit'] = False
        stfrq = super(StaffingACLVendorsForm, self).save(*args, **kwargs)
        stfrq.save()
        vendors = [v.id for v in self.cleaned_data.get('vendors', [])]
        save_vendors(stfrq, vendors, self.request.user)
        return stfrq


class ProjectSelectForm(forms.Form, FieldsetMixin):
    project = forms.ModelChoiceField(queryset=Project.objects.all())

    fieldsets = (
        ('', {'rows': (('project',),)},),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ProjectSelectForm, self).__init__(*args, **kwargs)
        if Project.can_create(self.request.user):
            self.fields['project'].help_text = ('or <a href="{}?next={}" '
                'data-target="#projectCreateModal" data-toggle="modal">'
                'add new project</a>').format(reverse('projects:create'),
                                            self.request.path)
        self.fields['project'].widget.attrs['data-kind'] = 'project'
        self.__setup_fieldsets__()


class ProposedStatusButtonForm(forms.ModelForm):
    class Meta:
        model = ProposedResource
        fields = ('status', 'changed_by',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.user = self.request.user
        self.resource = kwargs.pop('resource')
        super(ProposedStatusButtonForm, self).__init__(*args, **kwargs)
        self.fields['changed_by'].required = False
        self.fields['changed_by'].widget = forms.HiddenInput()
        if self.resource.status:
            self.fields['status'].queryset = self.resource.status\
                .get_possible_forward_statuses(self.user, self.resource)
        else:
            self.fields['status'].queryset = ProposedResourceStatus.objects.\
                filter(value=ProposedResourceStatus.INITIATED)

    def clean_changed_by(self):
        return self.request.user


@parsleyfy
class StatusFlowForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {
            'rows': (
                ('forward', 'driver',),
            ),
        }),
    )

    backward = forms.ModelChoiceField(
        queryset=ProposedResourceStatus.objects.all(),
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = StatusFlow
        exclude = ()

    def __init__(self, *args, **kwargs):
        self.backward = kwargs.pop('backward')
        super(StatusFlowForm, self).__init__(*args, **kwargs)
        self.fields['forward'].queryset = ProposedResourceStatus.objects\
            .exclude(id=self.backward.id)
        self.fields['forward'].label = 'Forward status'
        FieldsetMixin.__init__(self)

    def clean_backward(self):
        return self.backward



@parsleyfy
class ProposedStatusForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {
            'rows': (
                ('name', 'vendor_name',),
                ('value',),
            ),
        }),
    )

    class Meta:
        model = ProposedResourceStatus
        fields = ('name', 'vendor_name', 'value',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ProposedStatusForm, self).__init__(*args, **kwargs)
        self.__setup_fieldsets__()

    def clean_name(self):
        name = self.cleaned_data.get('name')
        existing = self.Meta.model.objects
        if self.instance:
            existing = existing.exclude(id=self.instance.id)
        existing = existing.filter(slug=slugify(name)).first()
        if existing:
            raise forms.ValidationError('Another status by the '
                                        'name "{}" already exists '\
                                        .format(existing.name))
        return name


from .fields import requests_as_choices


class RequestForm(forms.Form):
    S = StaffingRequest

    vendors = forms.ModelMultipleChoiceField(
        queryset=Vendor.objects.all(),
    )

    request = forms.ModelChoiceField(
        required=False,
        queryset=StaffingRequest.objects.all(),
        empty_label='Create a new request'
    )

    def __init__(self, *args, **kwargs):
        super(RequestForm, self).__init__(*args, **kwargs)
        self.fields['request'].choices = requests_as_choices()


@parsleyfy
class ProjectInviteForm(forms.Form, FieldsetMixin):
    users = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
    )

    message = forms.CharField(widget=forms.Textarea(
        attrs={'placeholder':'', 'autoresize': 'false'}))

    request = forms.ModelChoiceField(
        label='Include project and role information',
        required=False,
        queryset=StaffingRequest.objects.all(),
    )

    fieldsets = (
        (' ', {
            'rows': (
                ('users',),
                ('message',),
                ('request',),
            ),
        }),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        initial = kwargs.get('initial', {})
        initial['message'] = 'Hi, We are in the process of staffing the following project and wanted to understand if this would be of interest to you, if this is a good fit and if you are available during this time period.Can you please respond by clicking on the following link?'
        kwargs['initial'] = initial
        super(ProjectInviteForm, self).__init__(*args, **kwargs)
        self.fields['request'].choices = requests_as_choices()
        self.fields['message'].label = "Message to selected users and their organization's representative"
        self.fields['message'].widget.attrs = {'force_rows': 3}
        self.fields['users'].help_text = None
        self.__setup_fieldsets__()


@parsleyfy
class ProjectForm(forms.ModelForm, FieldsetMixin):
    start_date = forms.DateField(label='Start', widget=forms.DateInput(
        format='%d %b, %Y', attrs={'placeholder': 'Tap to select'}))

    end_date = forms.DateField(label='End', widget=forms.DateInput(
        format='%d %b, %Y', attrs={'placeholder': 'Tap to select'}),
    )

    fieldsets = (
        ('Project Description', {
            'rows': (
                ('title',),
                ('description',),
                ('start_date', 'end_date'),
                ('division',),
                ('owners',),
    #            ('tags',),
            )
        }),
    )

    class Meta:
        model = Project
        fields = ('title', 'description', 'budget', 'start_date', 'end_date',
                  'owners', 'division',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        initial = kwargs.get('initial', {})
        initial['user'] = self.request.user
        kwargs['initial'] = initial
        super(ProjectForm, self).__init__(*args, **kwargs)
        #self.fields['tags'].widget.attrs['data-type'] = 'tags'
        #self.fields['tags'].widget.attrs['selectize-url'] = \
        #    reverse('suggestions:tags')
        #self.fields['status'].widget = forms.widgets.HiddenInput()
        self.fields['budget'].label = mark_safe(
            '<a href="#" class="no-underline"'
            ' data-trigger="focus" data-container="body" data-toggle="popover"'
            ' data-trigger="click" data-html="true" data-placement="bottom"  data-content="<small><em>Only visible'
            ' to those with <strong>\'Can view financial information\'</strong>'
            ' permission. See <a href=\'{perm_url}\'>Permissions and '
            ' Groups</a>.</em></small>"><i class="fa fa-lock"></i></a> &nbsp;'
            'Budget <small class="text-muted">'
            '(<i class="fa fa-dollar"></i>)'
            '</small>'.format(
                perm_url=reverse('groups:list')
            )
        )
        if features.financials.is_enabled():
            self.fields['budget'].widget.attrs['placeholder'] =\
                'Budget for the project'
            self.fieldsets[0][1]['rows'] = (
                ('title',),
                ('description',),
                ('start_date', 'end_date'),
                ('owners',),
                ('division', 'budget',),
            )
        else:
            self.fields['budget'].widget = forms.HiddenInput()

        if Division.can_create(self.request.user):
            self.fields['division'].widget.attrs['selectize-create'] = 'true'
            self.fields['division'].widget.attrs['selectize-create-url'] = \
                Division.get_autocomplete_create_url()
        self.fields['division'].label = 'Group'
        self.fields['division'].initial = self.request.user.divisions.first()
        self.fields['budget'].required = False
        self.fields['budget'].widget.is_required = False

        self.fields['owners'].help_text = ''
        self.fields['owners'].label = 'Point of contact(s) for this project'
        self.fields['owners'].queryset = get_user_model().objects.filter(
            vendor=None)
        self.__setup_fieldsets__()

    def clean_budget(self):
        if features.financials.is_enabled():
            return self.cleaned_data['budget']
        else:
            return None


class ProposeResourceForm(forms.ModelForm, FieldsetMixin):
    allocation = forms.ChoiceField(
        choices=((i, '{}%'.format(i)) for i in range(10, 105, 5)),
        initial=100
    )

    start_date = forms.DateField(
        label='Start', required=True,
        widget=forms.DateInput(format='%d %b, %Y',
                               attrs={'placeholder': 'Tap to select'}))

    end_date = forms.DateField(
        label='End', required=True,
        widget=forms.DateInput(format='%d %b, %Y',
                               attrs={'placeholder': 'Tap to select'}))

    hourly_rate = forms.DecimalField(label='Hourly rate $', required=False)

    resource = LazyModelChoiceField(label='Resource',
        queryset=get_user_model().objects.none())

    #comments = forms.CharField(
    #    required=False, widget=forms.Textarea(
    #        attrs={'class': 'form-control'}))
    #
    _initiated = None

    fieldsets = [

        (' ',
            {'rows':
                (
                    ('resource','status'),
                    ('project','request',),
                )
            },
        ),

        ('Edit proposal below, if you cannot meet any of the requirements',
            {'rows':
                (
                    ('location', 'allocation'),
                    ('start_date', 'end_date'),
                )
            },
        ),

        ('Candidate Details',
            {'rows':
                (
                    ('role', 'skill_level'),
                )
            },
        ),
    ]

    class Meta:
        model = ProposedResource
        fields = (
            'project',
            'request',
            'resource',
            'role',
            'skill_level',
            'location',
            'allocation',
            'start_date',
            'end_date',
            'rate_card',
            'hourly_rate',
            'status',
            'changed_by',
        )
        widgets = {
            'request': forms.HiddenInput(),
            'project': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.project = kwargs.pop('project')
        self.staffing_request = kwargs.pop('staffing_request')
        self.vendor = kwargs.pop('vendor')
        self.user = self.request.user
        self.multiple_matches = False
        super(ProposeResourceForm, self).__init__(*args, **kwargs)
        self.fields['skill_level'].set_required(False)
        self.fields['rate_card'].set_required(False)
        self.fields['project'].set_required(False)
        self.fields['location'].set_required(False)
        self.fields['request'].set_required(False)
        self.fields['status'].set_required(True)
        self.fields['resource'].queryset = self.get_user_queryset()

        self.fields['changed_by'].set_required(False)
        self.fields['changed_by'].widget = forms.HiddenInput()

        PRS = ProposedResourceStatus
        self._initiated = PRS.objects.filter(value=PRS.INITIATED)
        if self._initiated.exists():
            self.fields['status'].initial = self._initiated.first()

        if self.user.is_vendor:
            self.fields['status'].queryset = ProposedResourceStatus\
                .objects.filter(value=ProposedResourceStatus.INITIATED)
            self.fields['status'].widget = forms.HiddenInput()

        if Location.can_create(self.request.user):
            self.fields['location'].widget.attrs['selectize-create'] = 'true'
            self.fields['location'].widget.attrs['selectize-create-url'] = \
                Location.get_autocomplete_create_url()

        if Role.can_create(self.request.user):
            self.fields['role'].widget.attrs['selectize-create'] = 'true'
            self.fields['role'].widget.attrs['selectize-create-url'] = \
                Role.get_autocomplete_create_url()

        self.fields['resource'].help_text = ('or <a href="{}?next={}" '
            'data-target="#userInviteModal" data-toggle="modal">'
            'add new user</a>').format(reverse('users:invite'),
                                       self.request.path)
        self.fields['resource'].widget.attrs['data-kind'] = 'user'
        self.fields['resource'].label = 'Select user'

        if not self.user.has_perm('rates.add'):
            self.fields.pop('rate_card')
            self.fields.pop('manual_rate')
            self.fields.pop('save_as_rate_card')

        if not features.financials.is_enabled():
            self.fields.pop('hourly_rate', None)
            self.fields.pop('rate_card', None)

        self.__setup_fieldsets__()

    def get_user_queryset(self):
        if self.user.is_vendor:
            self.vendor.users.all()
        elif self.user.is_client:
            return get_user_model().objects.all()

        return self.vendor.users.all()

    def clean_changed_by(self):
        return self.request.user

    def clean_allocation(self):
        allocation = self.cleaned_data.get('allocation')
        try:
            return int(allocation)
        except (ValueError, TypeError):
            return None

    def clean_rate_card(self):
        # TODO: Make sure the user can select this rate card.
        rate_card = self.cleaned_data.get('rate_card')
        if rate_card is not None and (self.user.is_client or
                                      (self.user.is_vendor and
                                       rate_card.vendor == self.user.vendor)):
            return rate_card
        return None

    def clean_status(self):
        if self.user.is_vendor and self._initiated.count() == 1:
            return self._initiated.first()
        return self.cleaned_data.get('status', None)

    def clean_project(self):
        return self.project

    def clean_request(self):
        return self.staffing_request

    def clean(self):
        cleaned_data = super(ProposeResourceForm, self).clean()
        start_date = cleaned_data.get('start_date', None)
        end_date = cleaned_data.get('end_date', None)
        role = cleaned_data.get('role', None)
        resource = cleaned_data.get('resource', None)
        if not all([start_date, end_date, role,
                    resource]):
            raise forms.ValidationError('There was an error in saving the '
                                        'data. Please try again.')
            return
        resource = cleaned_data.get('resource')
        status = cleaned_data.get('status', None)

        return cleaned_data

    def get_rate_card(self):
        hourly_rate = self.cleaned_data.get('hourly_rate')
        if not hourly_rate:
            return self.cleaned_data.get('rate_card')

        vendor = self.cleaned_data['resource'].vendor
        old_card = self.instance.rate_card
        if old_card:
            if old_card.cost != hourly_rate:
                old_card.cost = hourly_rate
                old_card.save()
            return old_card
        else:
            return Rate.local_cards.create(cost=hourly_rate,
                                           vendor=vendor,
                                           is_global=False)

    def save(self, *args, **kwargs):
        kwargs['commit'] = False
        self.instance = super(ProposeResourceForm, self).save(*args, **kwargs)
        self.instance.rate_card = self.get_rate_card()
        self.instance.save()
        return self.instance


class UpdateProposeResourceForm(forms.ModelForm, FieldsetMixin):

    start_date = forms.DateField(
        label='Start', required=True,
        widget=forms.DateInput(format='%d %b, %Y',
                               attrs={'placeholder': 'Tap to select'}))

    end_date = forms.DateField(
        label='End', required=True,
        widget=forms.DateInput(format='%d %b, %Y',
                               attrs={'placeholder': 'Tap to select'}))

    fieldsets = [

        ('Edit proposal below',
            {'rows':
                (
                    ('start_date', 'end_date'),
                    ('allocation',),
                )
            },
        ),

    ]

    class Meta:
        model = ProposedResource
        fields = (
            'start_date',
            'end_date',
            'allocation'
        )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.project = kwargs.pop('project')
        self.staffing_request = kwargs.pop('staffing_request')
        self.vendor = kwargs.pop('vendor')
        self.user = self.request.user
        super(UpdateProposeResourceForm, self).__init__(*args, **kwargs)
        self.__setup_fieldsets__()


class ProjectStaffForm(forms.ModelForm, FieldsetMixin):

    fieldsets = [(' ',
                    {'rows':
                        (
                            ('resource', 'status'),
                            ('role',),
                        )
                    },
                  ),
                ]

    class Meta:
        model = ProposedResource
        fields = (
            'project',
            'resource',
            'role',
            'status',
            'created_by',
            'changed_by',
            'start_date',
            'end_date',
        )
        widgets = {
            'project': forms.HiddenInput(),
            'changed_by': forms.HiddenInput(),
            'created_by': forms.HiddenInput(),
            'start_date': forms.HiddenInput(),
            'end_date': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.project = kwargs.pop('project')
        super(ProjectStaffForm, self).__init__(*args, **kwargs)
        self.fields['status'].initial = ProposedResourceStatus.objects.get(value=ProposedResourceStatus.SUCCESS)
        self.fields['role'].set_required(False)
        self.fields['project'].set_required(False)
        self.fields['created_by'].set_required(False)
        self.fields['changed_by'].set_required(False)
        self.fields['start_date'].set_required(False)
        self.fields['end_date'].set_required(False)
        self.fields['resource'].label = 'Name'

        self.__setup_fieldsets__()

    def get_user_queryset(self):
        if self.request.user.is_vendor:
            return get_user_model().objects.filter(
                vendor=self.request.user.vendor)
        elif self.request.user.is_client:
            return get_user_model().objects.all()

    def clean_project(self):
        return self.project

    def clean_created_by(self):
        return self.request.user

    def clean_changed_by(self):
        return self.request.user

    def clean_start_date(self):
        return self.project.start_date

    def clean_end_date(self):
        return self.project.end_date


class StaffingResponseForm(forms.ModelForm, FieldsetMixin):
    allocation = forms.ChoiceField(
        choices=((i, '{}%'.format(i)) for i in range(10, 105, 5)),
        initial=100
    )

    start_date = forms.DateField(label='Start', widget=forms.DateInput(
        format='%d %b, %Y', attrs={'placeholder': 'Tap to select'}))

    end_date = forms.DateField(label='End', widget=forms.DateInput(
        format='%d %b, %Y', attrs={'placeholder': 'Tap to select'}))

    fieldsets = (
        ('Dates', {'fields': ('start_date', 'end_date')}),
    )

    class Meta:
        model = StaffingResponse
        fields = ('start_date', 'end_date', 'allocation',
                  'location', 'role')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        super(StaffingResponseForm, self).__init__(*args, **kwargs)

        if Location.can_create(self.request.user):
            self.fields['location'].widget.attrs['selectize-create'] = 'true'
            self.fields['location'].widget.attrs['selectize-create-url'] = \
                Location.get_autocomplete_create_url()

        if Role.can_create(self.request.user):
            self.fields['role'].widget.attrs['selectize-create'] = 'true'
            self.fields['role'].widget.attrs['selectize-create-url'] = \
                Role.get_autocomplete_create_url()

        self.__setup_fieldsets__()


class FixedResponseForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('Billing', {'fields': ('rate',)}),
        ('Dates', {'fields': ('start_date', 'end_date')}),
    )

    class Meta:
        model = StaffingResponse
        fields = ('rate', 'start_date', 'end_date', 'status',)

    def __init__(self, *args, **kwargs):
        self.min_rate = kwargs.pop('min_rate')
        self.max_rate = kwargs.pop('max_rate')
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        super(FixedResponseForm, self).__init__(*args, **kwargs)
        self.fields['status'].widget = forms.HiddenInput()
        self.fields['status'].required = False
        self.fields['rate'].label = 'Proposed rate'
        self.fields['rate'].set_required(True)
        self.fields['start_date'].set_required(False)
        self.__setup_fieldsets__()

    def clean_status(self):
        return StaffingResponse.STATUS_SENT


class SendProposalForm(forms.ModelForm):
    class Meta:
        model = StaffingResponse
        fields = ('status', 'rate')
        widgets = {
            'status': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        self.is_fixed_price = kwargs.pop('is_fixed_price')
        super(SendProposalForm, self).__init__(*args, **kwargs)
        if not self.is_fixed_price:
            del self.fields['rate']


class SuggestedResourcesForm(forms.Form):
    role = forms.ModelChoiceField(queryset=Role.objects.all(), required=False)
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.filter(
        kind=Category.KIND_SKILL), required=False)
    skill_level = forms.ModelChoiceField(
        queryset=SkillLevel.objects.all(), required=False)
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(), required=False)
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)


class StaffignConfirmationForm(forms.ModelForm, FieldsetMixin):
    comment = forms.CharField(widget=forms.Textarea(), required=False)
    answer = forms.ChoiceField(widget=forms.Select(),
                               choices=((1, 'Yes, We are on it.'),
                                        (2, 'No, We will pass.')),
                               required = True,)

    fieldsets = [(' ',
                    {'rows':
                        (
                            ('answer',),
                            ('comment',),
                        )
                    },
                ),]

    class Meta:
            model = RequestVendorRelationship
            fields = ('answer', 'comment')

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        super(StaffignConfirmationForm, self).__init__(*args, **kwargs)
        self.initial['answer'] = initial.get('init_choice', 1)
        self.fields['comment'].label = 'Reason for your choice:'
        self.fields['answer'].label = 'Would you like to fulfill this request?'

        self.__setup_fieldsets__()


class DeliverableResponseForm(forms.ModelForm, FieldsetMixin):

    handlers = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        required=False,
        label='Staff',
    )

    fieldsets = [(' ',
                    {'rows':
                        (
                            ('description',),
                            ('location', 'rate',),
                            ('handlers',),
                        )
                    },
                ),]

    class Meta:
        model = DeliverableResponse
        fields = ('description', 'rate', 'location', 'request', 'vendor', 'posted_by', 'handlers')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.vendor = kwargs.pop('vendor')
        self.staffing_request = kwargs.pop('staffing_request')
        super(DeliverableResponseForm, self).__init__(*args, **kwargs)

        self.fields['description'].set_required(True)
        self.fields['request'].set_required(False)
        self.fields['vendor'].set_required(False)
        self.fields['posted_by'].set_required(False)
        self.fields['handlers'].queryset = get_user_model().objects.filter(vendor=self.vendor)
        self.fields['rate'].widget.attrs['placeholder'] = 'enter fixed rate here'
        self.fields['description'].widget.attrs['placeholder'] = 'Summary describing your deliverable proposal'
        self.fields['handlers'].help_text = ('or <a href="{}?next={}" '
            'data-target="#userInviteModal" data-toggle="modal">'
            'add new user</a>').format(reverse('users:invite'),
                                       self.request.path)
        self.fields['handlers'].widget.attrs['data-kind'] = 'user'
        if Location.can_create(self.request.user):
            self.fields['location'].widget.attrs['selectize-create'] = 'true'
            self.fields['location'].widget.attrs['selectize-create-url'] = \
                Location.get_autocomplete_create_url()

        self.__setup_fieldsets__()

    def clean_request(self):
        return self.staffing_request

    def clean_vendor(self):
        return self.vendor

    def clean_posted_by(self):
        return self.request.user


class ShareProjectForm(forms.Form, FieldsetMixin):
    users = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.filter(vendor=None),
    )
    message = forms.CharField(widget=forms.Textarea)

    fieldsets = [(' ',
                    {'rows':
                        (
                            ('users',),
                            ('message',),
                        )
                    },
                ),]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.project = kwargs.pop('project')
        super(ShareProjectForm, self).__init__(*args, **kwargs)
        self.__setup_fieldsets__()
