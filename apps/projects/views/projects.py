from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db import transaction, connection
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.generic import (View, DetailView, ListView, FormView,
                                  TemplateView, DeleteView, UpdateView,
                                  CreateView)
from annoying.functions import get_object_or_None
from urlobject import URLObject

from med_social.utils import today


from med_social.views.base import BaseEditView
from med_social.decorators import (client_required,
                                   member_required)

from users.models import UserDivisionRel
from vendors.models import Vendor
from rates.models import Rate
from channels.models import Channel
from rates.forms import SuggestedRateForm
from channels.forms import NewChannelForm, MessageForm
from activity.models import Event
from features import models as features
from ..forms import (ProjectForm,
                     StaffingResponseForm,
                     FixedResponseForm,
                     ProposeResourceForm,
                     SendProposalForm,
                     ProposedStatusButtonForm,
                     SuggestedResourcesForm,
                     ProjectInviteForm,
                     StaffignConfirmationForm,
                     StaffingBasicForm,
                     DeliverableResponseForm,
                     ProjectStaffForm,
                     ShareProjectForm,
                     UpdateProposeResourceForm)

from ..models import (Project,
                      StaffingRequest,
                      StaffingResponse,
                      ProposedResourceStatus,
                      ProposedResource,
                      RequestVendorRelationship,
                      RequestVendorRelationship,
                      DeliverableResponse)
from ..tasks import request_info_task, sr_confirmation, share_project_mail
from ..filters import ProjectFilter

# TODO: Make sure no one can edit/response/accept-response on an ended project
# TODO: Refactor this into a views module


class ProjectList(ListView):
    model = Project
    context_object_name = 'projects'
    template_name = 'projects/list.html'
    features_required = (features.projects,)
    status_filter = None

    def get_template_names(self):
        if self.request.is_ajax() and self.request.GET.get(
                'filter', '').strip() == 'yes':
            return 'projects/partials/filter_results.html'
        return self.template_name

    def get_context_data(self):
        user = self.request.user
        ctx = super(ProjectList, self).get_context_data()
        ctx['project_status_choices'] = StaffingRequest.STATUS

        ctx['projects'] = ProjectFilter(
            self.request.GET,
            request=self.request,
            queryset=ctx['projects']
        )

        if user.is_client:
            ctx['archived_projects'] = Project.objects.filter(is_archived=True)

        content_type = ContentType.objects.get_for_model(Project)

        unread = Event.objects.filter(Q(content_type=content_type,
                                        user=user))

        unread_events = {}
        for event in unread:
            events = unread_events.get(event.content_type.id, [])
            events.append(event)
            unread_events[event.content_type.id] = events

        ctx['unread_events'] = unread_events

        filters = {}
        ctx['filters'] = filters
        ctx['draft_requests_count'] = StaffingRequest.drafts.filter(
            created_by=self.request.user).count()
        ctx['active_nav_tab'] = 'projects'
        return ctx

    def get_queryset(self):
        user = self.request.user

        qs = self.model.objects.all()
        if user.is_vendor:
            q = Q(staffing_requests__is_public=True)
            q = q | Q(staffing_requests__vendors=user.vendor)
            v = Q(status=Project.DRAFT)
            v = v | Q(is_archived=True)
            qs = qs.filter(q).exclude(v)
        else:
            qs = qs.exclude(is_archived=True)

        return qs.distinct()
project_list = member_required(ProjectList.as_view())


class InviteUserToRequest(FormView):
    form_class = ProjectInviteForm
    template_name = 'projects/invite_to_project.html'
    success = False
    target_user = None
    proposed = None

    def get_template_names(self):
        if self.request.is_ajax():
            return 'projects/invite_to_project_modal.html'
        else:
            return self.template_name

    def get_success_url(self):
        if self.proposed:
            return self.proposed.get_absolute_url()
        elif self.target_user:
            return reverse('users:profile', args=(self.target_user.username,))
        else:
            return reverse('users:list')

    def get_context_data(self, form=None):
        context = super(InviteUserToRequest, self).get_context_data()
        context['staffing_projects'] = Project.objects.filter(
            staffing_requests__status=StaffingRequest.STAFFING)
        context['user_invite_form'] = form
        context['success'] = self.success
        return context

    def get_initial(self):
        initial = super(InviteUserToRequest, self).get_initial()
        initial['users'] = self.request.GET.getlist('users', [])
        return initial

    def get_form_kwargs(self):
        kwargs = super(InviteUserToRequest, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        staffing_request = form.cleaned_data['request']
        users = form.cleaned_data['users']
        message = form.cleaned_data['message']
        sender = self.request.user
        present = staffing_request.vendors.values_list('id', flat=True)
        vendors = Vendor.objects.filter(users=users).exclude(id__in=present)
        for vendor in vendors:
            RequestVendorRelationship\
                .objects.get_or_create(created_by=sender,
                                       request=staffing_request,
                                       vendor=vendor)
        tenant = connection.get_tenant()

        user_list = [user.id for user in users]

        request_info_task.delay(tenant_id=tenant.id, user_list=user_list,
                                message=message,
                                sender_id=sender.id,
                                sr_id=staffing_request.id)

        self.success = True
        if self.request.is_ajax() and not 'HTTP_X_PJAX' in self.request.META:
            return self.render_to_response(self.get_context_data(form))
        return super(InviteUserToRequest, self).form_valid(form)
invite_users = member_required(InviteUserToRequest.as_view())


# Client views
class CreateProject(BaseEditView):
    model_form = ProjectForm
    features_required = (features.projects,)

    def dispatch(self, *args, **kwargs):
        self.is_iframed = self.request.GET.get('iframed', '').strip() == 'yes'
        return super(CreateProject, self).dispatch(*args, **kwargs)

    def get_template_names(self):
        if self.is_iframed:
            if self.object:
                return ['projects/ajax_result.html']
            return ['projects/create_form.html']
        if self.request.is_ajax() and not 'HTTP_X_PJAX' in self.request.META:
            return ['projects/create_form_ajax.html']
        else:
            return ['projects/create.html']

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super(CreateProject, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial_data(self):
        tomorrow = today() + timedelta(days=1)
        return {'start_date': tomorrow, 'owners': [self.request.user]}

    def pre_save(self, instance):
        instance.user = self.request.user
        instance.last_activity = self.request.user
        return instance

    def get_context_data(self, *args, **kwargs):
        context = super(CreateProject, self).get_context_data(*args, **kwargs)
        context['STATUS_DESCRIPTIONS'] = StaffingRequest.STATUS_DESCRIPTIONS
        context['object'] = self.object
        return context

    def form_valid(self, form):
        ret_val = super(CreateProject, self).form_valid(form)

        ajax_or_iframe = self.request.is_ajax() or self.is_iframed
        is_pjax = 'HTTP_X_PJAX' in self.request.META
        if ajax_or_iframe and not is_pjax:
            return self.render_to_response(self.get_context_data(
                form=form, success=True))
        else:
            return ret_val


class UpdateProject(UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create.html'
    context_object_name = 'project'
    features_required = (features.projects,)

    def post_save(self, instance):
        # todo send notification from here
        return instance

    def get_initial(self):
        initial = super(UpdateProject, self).get_initial()
        initial['owners'] = [self.request.user.id]
        return initial

    def get_form_kwargs(self):
        kwargs = super(UpdateProject, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(UpdateProject, self).get_context_data(*args, **kwargs)
        context['STATUS_DESCRIPTIONS'] = StaffingRequest.STATUS_DESCRIPTIONS
        return context

    def form_valid(self, form):
        self.object.last_activity = self.request.user
        self.object.save()
        return super(UpdateProject, self).form_valid(form)


class ProjectDetails(DetailView):
    model = Project
    template_name = 'projects/details.html'
    features_required = (features.projects,)

    # FIXME: Do not show project if no staffing request is visible

    def get_object(self):
        pk = self.kwargs.get('pk')
        project = get_object_or_404(Project, pk=pk)

        if self.request.user.is_client:
            return project
        else:
            if project.staffing_requests.filter(
                Q(is_public=True) | Q(vendors=self.request.user.vendor)
            ).exists():
                return project
        raise Http404()

    def get_context_data(self, *args, **kwargs):
        ctx = super(ProjectDetails, self).get_context_data(*args, **kwargs)
        user = self.request.user
        ctx['proposed_statuses'] = ProposedResourceStatus.objects.all()
        if user.is_client:
            ctx['requests'] = self.object.staffing_requests.filter(is_archived=False)\
                .prefetch_related('proposed_staff', 'responses')
        elif user.is_vendor:
            qs = Q(is_public=True)
            qs = qs | Q(vendors=user.vendor)
            staffing_qs = qs & ~Q(status=StaffingRequest.DRAFT)
            ctx['requests'] = \
                self.object.staffing_requests.filter(is_archived=False).filter(staffing_qs).distinct()

        content_type = ContentType.objects.get_for_model(Project)
        staffing_content_type = ContentType.objects.get_for_model(StaffingRequest)

        ctx['project_content_id'] = content_type.id

        unread = Event.objects.filter(Q(content_type=staffing_content_type,
                                        user=user))

        unread_events = {}
        for event in unread:
            events = unread_events.get(event.content_type.id, [])
            events.append(event)
            unread_events[event.content_type.id] = events

        ctx['unread_events'] = unread_events
        ctx['date_today'] = date.today()
        ctx['staffing_form'] = StaffingBasicForm(request=self.request,
                                                 project=self.object,
                                                 kind=StaffingRequest.KIND_STAFFING)
        ctx['deliverable_form'] = StaffingBasicForm(request=self.request,
                                                    project=self.object,
                                                    kind=StaffingRequest.KIND_FIXED)
        return ctx


class AddUserToProject(CreateView):
    model = ProposedResource
    template_name = 'projects/add_user.html'
    form_class = ProjectStaffForm

    def dispatch(self, *args, **kwargs):
        pk = self.kwargs['pk']
        self.project = get_object_or_404(Project, pk=pk)
        return super(AddUserToProject, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        # Note: for now, let every client user staff people
        #if not self.request.user.division_rels.filter(
        #    division=self.project.division, is_admin=True).exists():
        #    messages.error(
        #        self.request,
        #        mark_safe('Only <b>{}</b> admins can staff resources from the'
        #        ' dedicated pool on this project.'.format(
        #            self.project.division.name
        #        )))
        #    return HttpResponseRedirect(self.project.get_absolute_url())
        return super(AddUserToProject, self).post(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(AddUserToProject, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['project'] = self.project
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(AddUserToProject, self).get_context_data()
        ctx['project'] = self.project
        if form:ctx['form'] = form
        ctx['object'] = self.object
        return ctx

    def get_success_url(self):
        return reverse('projects:detail',
                       args=(self.project.id, ))

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if not ProposedResource.objects.filter(resource=self.object.resource,
                                               project=self.object.project,).exists():
            self.object.save()

        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        return HttpResponseRedirect(self.get_success_url())
add_user_to_project = client_required(AddUserToProject.as_view())


class ProjectBudget(DetailView):
    model = Project
    template_name = 'projects/budget.html'
    features_required = (features.projects,)

    def get_context_data(self, object):
        ctx = super(ProjectBudget, self).get_context_data()
        ctx['project'] = object
        return ctx


class BudgetDetails(DetailView):
    model = Project
    template_name = 'projects/budget_details.html'

    def get_context_data(self, object):
        ctx = super(BudgetDetails, self).get_context_data()
        ctx['project'] = object
        if self.request.user.is_client:
            ctx['staffed'] = object.proposals.filter(
                status__value=ProposedResourceStatus.SUCCESS)
            ctx['total_cost'] = sum([S.total_cost() for S in ctx['staffed']])
        elif self.request.user.is_vendor:
            ctx['staffed'] = object.proposals.filter(
                resource__vendor=self.request.user.vendor,
                status__value=ProposedResourceStatus.SUCCESS)
            ctx['total_cost'] = sum([S.total_cost() for S in ctx['staffed']])
        return ctx
budget_details = member_required(BudgetDetails.as_view())


# Vendor Views
class CreateResponse(BaseEditView):
    template_name = 'responses/create.html'
    model_form = StaffingResponseForm

    def dispatch(self, request, pk, stfrq_pk, **kwargs):
        self.staffing_request = get_object_or_404(StaffingRequest, pk=stfrq_pk)
        self.project = self.staffing_request.project
        self.vendor = request.user.vendor
        # TODO: if request has already been accepted then redirect back to
        # request
        return super(CreateResponse, self).dispatch(request, pk)

    def get_success_url(self):
        return self.project.get_absolute_url()

    def get_hero_html(self):
        if self.staffing_request.is_fixed_price:
            min_rate, max_rate = (self.staffing_request.min_rate,
                                  self.staffing_request.max_rate,)
            min_rate = intcomma(min_rate) if min_rate else None
            max_rate = intcomma(max_rate) if max_rate else None
            if min_rate and max_rate:
                return 'Expected rate: ${0} - {1}'.format(min_rate, max_rate)
            elif min_rate:
                return 'Minimum expected rate: ${0}'.format(min_rate)
            elif max_rate:
                return 'Maximum expected rate: ${0}'.format(max_rate)
        else:
            return ('You can propose different people to be staffed'
                    ' on the project.')

    @property
    def form(self):
        if self.staffing_request.kind == self.staffing_request.KIND_STAFFING:
            return StaffingResponseForm
        elif self.staffing_request.kind == self.staffing_request.KIND_FIXED:
            return FixedResponseForm

    def create_form(self, *args, **kwargs):
        kwargs['vendor'] = self.vendor
        if self.staffing_request.kind == self.staffing_request.KIND_FIXED:
            kwargs['min_rate'] = self.staffing_request.min_rate
            kwargs['max_rate'] = self.staffing_request.max_rate
        return super(CreateResponse, self).create_form(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(CreateResponse, self).get_context_data(*args, **kwargs)
        ctx['staffing_request'] = self.staffing_request
        ctx['project'] = self.project
        ctx['response'] = self.object
        return ctx

    def get_initial_data(self):
        fields = list(self.form.Meta.fields)
        initial = self.staffing_request.serialize_fields(fields)
        if self.object:
            initial.update(self.object.serialize_fields(fields))
        return initial

    def get_instance(self, request, pk=None, *args, **kwargs):
        if 'response_id' in self.kwargs:
            return get_object_or_404(
                self.model,
                id=self.kwargs['response_id']
            )
        else:
            None

    def pre_save(self, instance):
        instance.request = self.staffing_request
        instance.posted_by = self.request.user
        instance.vendor = self.request.user.vendor
        return instance

    def post_save(self, instance):
        comments = self.bound_form.cleaned_data.get('comments', '').strip()
        if instance.id and comments:
            instance.comments.create(comments=comments,
                                     posted_by=self.request.user)
        return instance


class AcceptResponse(TemplateView):
    template_name = 'responses/response_accept.html'

    def get_success_url(self):
        return self.project.get_absolute_url()

    def dispatch(self, request, pk, stfrq_pk, response_pk):
        self.staffing_response = get_object_or_404(
            StaffingResponse,
            pk=response_pk
        )
        self.vendor = self.staffing_response.vendor
        self.staffing_request = self.staffing_response.request
        self.project = self.staffing_request.project
        self.user = self.request.user
        return super(AcceptResponse, self).dispatch(
            request, pk, stfrq_pk, response_pk)

    def post(self, request, pk, stfrq_pk, vendor_pk):
        self.staffing_response.accepted_by = request.user
        self.staffing_response.is_accepted = True
        self.staffing_response.save()
        return HttpResponseRedirect(self.staffing_request.get_absolute_url())

    def get_context_data(self):
        ctx = super(AcceptResponse, self).get_context_data()
        ctx.update({
            'staffing_request': self.staffing_request,
            'project': self.project,
            'vendor': self.vendor,
            'response': self.staffing_response,
        })
        return ctx
accept_response = transaction.atomic(AcceptResponse.as_view())


class CreateStaffingResponse(CreateView):
    model = StaffingResponse

    def get_success_url(self):
        return self.project.get_absolute_url()

    def dispatch(self, *args, **kwargs):
        self.user = self.request.user
        self.vendor = self.user.vendor
        if self.user.is_vendor and self.vendor != self.user.vendor:
            raise Http404()
        self.staffing_request = get_object_or_404(StaffingRequest,
                                                  id=kwargs['stfrq_pk'])
        self.project = self.staffing_request.project
        return super(CreateStaffingResponse, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        return redirect(reverse(
            'staffing:requests:detail',
            args=(self.project.id, self.staffing_request.id,)
        ))

    def post(self, *args, **kwargs):
        response = StaffingResponse.objects.create(
            request=self.staffing_request,
            vendor=self.vendor,
            posted_by=self.user
        )

        response.vendor = self.vendor
        response.request = self.staffing_request
        response.skill_level = self.staffing_request.skill_level
        response.role = self.staffing_request.role
        response.location = self.staffing_request.location
        response.start_date = self.staffing_request.start_date
        response.end_date = self.staffing_request.end_date
        response.save()

        return redirect(reverse(
            'staffing:requests:response_details',
            args=(
                response.request.project_id,
                response.request_id,
                response.id,
            )
        ))


class UserSuggestions(ListView):
    model = get_user_model()
    template_name = 'requests/suggestions.html'
    context_object_name = 'suggestions'

    def get_queryset(self, *args, **kwargs):
        self.form = SuggestedResourcesForm(data=self.request.GET)
        if not self.form.is_valid():
            return self.model.objects.none()
        if not any(self.form.cleaned_data.values()):
            return self.model.objects.none()
        return self.model.get_suggested_resources(**self.form.cleaned_data)


class VendorSuggestions(ListView):
    model = Vendor
    template_name = 'requests/vendor_suggestions.html'
    context_object_name = 'suggestions'

    def get_queryset(self, *args, **kwargs):
        self.form = SuggestedResourcesForm(data=self.request.GET)
        if not self.form.is_valid():
            return self.model.objects.none()
        if not any(self.form.cleaned_data.values()):
            return self.model.objects.none()
        return self.model.get_suggested_vendors(**self.form.cleaned_data)


class ResponseDetails(DetailView):
    model = StaffingResponse
    template_name = 'responses/details.html'
    context_object_name = 'response'

    def dispatch(self, *args, **kwargs):
        self.user = self.request.user
        self.object = self.get_object()
        self.vendor = self.object.vendor
        self.staffing_request = self.object.request

        if self.user.is_vendor and self.vendor != self.user.vendor:
            raise Http404()
        if self.user.is_client and self.object.is_draft:
            raise Http404()

        self.project = self.staffing_request.project
        return super(ResponseDetails, self).dispatch(*args, **kwargs)

    def get_context_data(self, object):
        ctx = super(ResponseDetails, self).get_context_data()
        object = self.get_object()
        ctx['project'] = object.request.project
        ctx['vendor'] = object.vendor
        #ctx['comment_form'] = ResponseCommentForm()
        ctx['staffing_request'] = object.request
        ctx['proposed_resources'] = object.proposed.all()
        ctx['has_accepted_response'] = object.proposed.filter(
            is_staffed=True).exists()
        ctx['reviews'] = object.reviews.all()
        return ctx

    def get_object(self):
        kwargs = {
            'pk': self.kwargs['response_id']
        }
        args = tuple()
        if self.request.user.is_client:
            args = (~Q(status=StaffingResponse.STATUS_DRAFT),)
        return get_object_or_404(StaffingResponse, *args, **kwargs)

        kwargs['vendor'] = self.request.user.vendor


class ChangeProposedStatusView(UpdateView):
    model = ProposedResource
    form_class = ProposedStatusButtonForm
    template_name = 'responses/partials/proposed_status_button_group.html'
    context_object_name = 'proposed_resource_object'

    def get_context_data(self, form=None):
        ctx = super(ChangeProposedStatusView, self).get_context_data()
        ctx['proposed_resource_object'] = self.object
        ctx['status'] = self.object.status
        ctx['project'] = self.object.project
        ctx['proposed_statuses'] = ProposedResourceStatus.objects.all()
        return ctx

    def get_form_kwargs(self):
        kwargs = super(ChangeProposedStatusView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['resource'] = self.object
        return kwargs

    def get(self, request, project_pk, pk):
        return HttpResponseRedirect(reverse('projects:detail',
                                            args=(project_pk,)))

    def form_valid(self, form):
        self.object = form.save()
        if self.object.project:
            self.object.project.last_activity = self.request.user
            self.object.project.save()
        if self.object.request:
            self.object.request.last_activity = self.request.user
            self.object.request.save()
        if self.request.is_ajax() and not 'HTTP_X_PJAX' in self.request.META:
            return self.render_to_response(self.get_context_data(form=form))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        project_pk = self.kwargs['project_pk']
        return HttpResponseRedirect(reverse('projects:detail',
                                            args=(project_pk,)))
change_proposed_status = ChangeProposedStatusView.as_view()


class CreateProposedResourceView(CreateView):
    model = ProposedResource
    form_class = ProposeResourceForm
    template_name = 'responses/proposed_resourse_create.html'

    def get_success_url(self):
        _next = self.request.GET.get('next')
        if _next:
            return _next
        else:
            if self.object.request:
                return self.object.request.get_absolute_url()
            else:
                return self.object.get_absolute_url()

    def dispatch(self, *args, **kwargs):
        # TODO: review for permissions.
        self.staffing_request = get_object_or_404(
            StaffingRequest, id=kwargs['request_pk'],
            kind=StaffingRequest.KIND_STAFFING)
        self.project = self.staffing_request.project
        return super(CreateProposedResourceView, self).dispatch(
            *args, **kwargs)

    def get_initial(self):
        return {
            'staffing_request': self.staffing_request,
            'role': self.staffing_request.role,
            'skill_level': self.staffing_request.skill_level,
            'location': self.staffing_request.location,
            'allocation': self.staffing_request.allocation,
            'start_date': self.staffing_request.start_date,
            'end_date': self.staffing_request.end_date,
        }

    def get_context_data(self, *args, **kwargs):
        ctx = super(CreateProposedResourceView,
                    self).get_context_data(*args, **kwargs)

        current_data = {}
        if self.request.method == 'POST':
            filter_form = SuggestedRateForm(data=self.request.POST)
            if filter_form.is_valid():
                current_data = filter_form.cleaned_data

        for key, value in self.get_initial().items():
            if not current_data.get(key):
                current_data[key] = value

        rates = Rate.get_suggested_rates(**current_data)
        if self.request.user.is_vendor:
            rates = rates.filter(vendor=self.request.user)
        ctx['form'] = kwargs.get('form')
        selected = ctx['form'].instance
        if selected and selected.rate_card_id:
            rates = rates.exclude(id=selected.rate_card_id)
        ctx['suggested_rates'] = rates
        ctx['project'] = self.staffing_request.project
        ctx['staffing_request'] = self.staffing_request
        return ctx

    def get_form_kwargs(self):
        kwargs = super(CreateProposedResourceView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['staffing_request'] = self.staffing_request
        kwargs['project'] = self.staffing_request.project
        kwargs['vendor'] = self.request.user.vendor

        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        ret = super(CreateProposedResourceView, self).form_valid(form)
        return ret

create_proposed_resource = transaction.atomic(
    member_required(CreateProposedResourceView.as_view()))


class EditProposedResourceView(UpdateView):
    model = ProposedResource
    form_class = ProposeResourceForm
    template_name = 'responses/proposed_resourse_create.html'

    def get_context_data(self, form=None):
        ctx = super(EditProposedResourceView,
                    self).get_context_data()
        filter_form = SuggestedRateForm(data=self.request.POST)
        if filter_form.is_valid():
            current_data = filter_form.cleaned_data
        else:
            current_data = {}
        rates = Rate.get_suggested_rates(**current_data)
        if self.request.user.is_vendor:
            rates = rates.filter(vendor=self.request.user)
        ctx['suggested_rates'] = rates
        if form:ctx['form'] = form

        ctx['project'] = self.object.project
        ctx['proposed'] = self.object
        ctx['staffing_request'] = self.staffing_request
        return ctx

    def get_template_names(self):
        if self.request.is_ajax():
            return 'projects/partials/proposed_edit_form.html'
        return self.template_name

    def get_form_class(self):
        if self.request.is_ajax():
            return UpdateProposeResourceForm
        return self.form_class

    def get_success_url(self):
        _next = self.request.GET.get('next')
        if _next:
            return _next
        else:
            if self.object.request:
                return self.object.request.get_absolute_url()
            else:
                return self.object.get_absolute_url()

    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        if self.request.user.is_vendor and self.object.is_staffed:
            messages.error(
                self.request,
                '{} has already been staffed.'
                ' Staffed resources cannot be edited'.format(
                    self.object.resource
                ))
            return redirect(self.get_success_url())

        self.staffing_request = self.object.request
        if self.request.user.is_vendor and\
                self.object.resource.vendor != self.request.user.vendor:
            raise Http404()
        return super(EditProposedResourceView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        if self.object.start_date:
            start_date = self.object.start_date
        else:
            start_date = self.staffing_request.start_date if\
                self.staffing_request else None

        if self.object.end_date:
            end_date = self.object.end_date
        else:
            end_date = self.staffing_request.end_date if\
                self.staffing_request else None

        skill_level = self.staffing_request.skill_level if\
            self.staffing_request else None
        if self.object.location:
            location = self.object.location
        else:
            location = self.staffing_request.location if\
                self.staffing_request else None

        return {
            'role': self.object.role or self.staffing_request.role,
            'skill_level': self.object.skill_level or skill_level,
            'location': location,
            'allocation': self.object.allocation or
            self.staffing_request.allocation,
            'start_date': start_date,
            'end_date': end_date,
        }

    def get_form_kwargs(self):
        kwargs = super(EditProposedResourceView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['staffing_request'] = self.staffing_request
        kwargs['project'] = self.object.project
        if self.object.resource.vendor is not None:
            kwargs['vendor'] = self.object.resource.vendor
        else:
            kwargs['vendor'] = self.request.user.vendor
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        self.object.updated = True
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        else:
            return HttpResponseRedirect(self.get_success_url())

edit_proposed_resource = transaction.atomic(
    member_required(EditProposedResourceView.as_view()))


class DeleteProposedResourceView(DeleteView):
    model = ProposedResource

    def get_success_url(self):
        if self.staffing_request:
            return self.staffing_request.get_absolute_url()
        else:
            return self.object.project.get_absolute_url()

    def dispatch(self, request, pk):
        self.object = get_object_or_404(ProposedResource, id=pk)
        self.staffing_request = self.object.request
        same_vendor = request.user.vendor == self.object.resource.vendor
        if request.user.is_client or same_vendor:
            return super(DeleteProposedResourceView, self
                         ).dispatch(request, pk)
        else:
            raise Http404()

    def delete(self, request, *args, **kwargs):
        val = super(DeleteProposedResourceView, self
                    ).delete(request, *args, **kwargs)
        if self.request.is_ajax():
            return HttpResponse(200)
        else:
            return val

delete_proposed_resource = DeleteProposedResourceView.as_view()


class ProposedResourceDetailView(DetailView):
    model = ProposedResource
    template_name = 'responses/proposed_resource_details.html'

    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        if self.request.user.is_vendor and\
                self.object.resource.vendor != self.request.user.vendor:
            raise Http404()
        return super(ProposedResourceDetailView,
                     self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProposedResourceDetailView, self).get_context_data(
            *args, **kwargs
        )

        if self.request.GET.get('q_status'):
            context['q_status'] = self.request.GET.get('q_status')

        if self.request.user.is_vendor:
            context['channels'] = self.object.channels.filter(
                vendors=self.request.user.vendor)
        else:
            context['channels'] = self.object.channels.all()

        channel_kwargs = {
            'content_type': ContentType.objects.get_for_model(self.object),
            'object_id': self.object.id,
            'vendor_choices': self.object.get_channel_vendor_choices(
                self.request.user),
            'request': self.request
        }
        context['new_channel_form'] = NewChannelForm(**channel_kwargs)
        context['message_form'] = MessageForm(request=self.request)
        return context
proposed_resource_details = member_required(
    ProposedResourceDetailView.as_view())


class RemoveProposedResourceView(DeleteView):
    model = ProposedResource
    template_name = 'responses/proposed_resource_confirm_remove.html'

    def get_success_url(self):
        return self.object.project.get_absolute_url()
remove_proposed_resource = transaction.atomic(
    member_required(RemoveProposedResourceView.as_view()))


class SendProposalView(UpdateView):
    model = StaffingResponse
    form_class = SendProposalForm
    template_name = 'responses/confirm_send_proposal.html'

    def get_success_url(self):
        return self.get_object().get_absolute_url()

    def post(self, *args, **kwargs):
        r = self.get_object()
        prs = ProposedResource.objects.filter(
            response=r,
        ).all()

        if r.request.is_fixed_price or prs.exists():
            r.mark_sent()
            r.save()
        else:
            messages.error(self.request, 'You cannot send respone without '
                                         'proposed resources')
        return redirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super(SendProposalView, self).get_form_kwargs()
        kwargs['is_fixed_price'] = self.object.request.is_fixed_price
        return kwargs


class StaffingRequestDetails(DetailView):
    model = StaffingRequest
    pk_url_kwarg = 'stfrq_pk'
    template_name = 'requests/details.html'
    context_object_name = 'staffing_request'

    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        self.project = self.object.project
        return super(StaffingRequestDetails, self).dispatch(*args, **kwargs)

    def get_page_title(self):
        if self.object.is_fixed_price:
            return _('Deliverable request')
        else:
            return _('Staffing request')

    def get_object(self):
        stfrq_pk = self.kwargs['stfrq_pk']
        if self.request.user.is_vendor:
            requests = StaffingRequest.objects.exclude(
                status=StaffingRequest.DRAFT)
        else:
            requests = StaffingRequest.objects.all()
        try:
            return requests.get(pk=stfrq_pk)
        except StaffingRequest.DoesNotExist:
            raise Http404()

    def get_context_data(self, object):
        ctx = super(StaffingRequestDetails, self).get_context_data()
        ctx['project'] = self.project
        user = self.request.user
        answer_choices = RequestVendorRelationship.answer_choices
        answer_labels = RequestVendorRelationship.ANSWER_LABELS
        answer_css = RequestVendorRelationship.CSS_CLASSES

        if user.is_client:
            ctx['responses'] = object.responses.exclude(
                status=StaffingResponse.STATUS_DRAFT
            )
            ctx['proposed_resources'] = ProposedResource.objects.filter(
            request=object,
            ).order_by('-status__value')

        elif user.is_vendor:
            ctx['responses'] = StaffingResponse.objects.filter(
                request=object,
                vendor=user.vendor,
            )
            ctx['proposed_resources'] = ProposedResource.objects.filter(
                request=object,
                resource__vendor=user.vendor,
            ).order_by('-status__value')

        if self.request.user.is_vendor:
            vendor_relation_object =\
                get_object_or_None(RequestVendorRelationship,
                                   vendor=user.vendor,
                                   request=object)
            vendor_relation_object.viewed_at = now()
            vendor_relation_object.viewed_by = self.request.user
            vendor_relation_object.save()

            ctx['relation_obj'] = vendor_relation_object
            ctx['show_confirm_box'] =\
                True if object.is_public or vendor_relation_object else False

            ctx['answer_choices'] = answer_choices
            ctx['answer_css'] = answer_css
            ctx['answer_labels'] = answer_labels

            if object.is_public:
                ctx['detail_confirmed'] = True
            if vendor_relation_object and\
               vendor_relation_object.answer == vendor_relation_object.accepted:
                ctx['detail_confirmed'] = True
            ctx['channels'] = self.object.channels.filter(
                vendors=self.request.user.vendor)
        else:
            ctx['detail_confirmed'] = True
            ctx['channels'] = self.object.channels.all()

        channel_kwargs = {
            'content_type': ContentType.objects.get_for_model(self.object),
            'object_id': self.object.id,
            'vendor_choices': self.object.get_channel_vendor_choices(
                self.request.user),
            'request': self.request
        }

        staffing_content_type = ContentType.objects\
            .get_for_model(StaffingRequest)
        proposed_content_type = ContentType.objects\
            .get_for_model(ProposedResource)
        channel_content_type = ContentType.objects\
            .get_for_model(Channel)

        ctx['staffing_content_id'] = staffing_content_type.id
        ctx['proposed_content_id'] = proposed_content_type.id

        unread = Event.objects.filter(Q(content_type=proposed_content_type, user=user) |
                                      Q(content_type=channel_content_type, user=user))

        unread_events = {}
        for event in unread:
            events = unread_events.get(event.content_type.id, [])
            events.append(event)
            unread_events[event.content_type.id] = events

        for proposed_resource in ctx['proposed_resources']:
            proposed_resource.past_projects =\
                proposed_resource.resource.proposed\
                .filter(status__value=ProposedResourceStatus.SUCCESS)\
                .distinct().count()
        ctx['unread_events'] = unread_events
        ctx['new_channel_form'] = NewChannelForm(**channel_kwargs)
        ctx['message_form'] = MessageForm(request=self.request)

        if self.request.GET.get('confirm'):
            ctx['confirm'] = self.request.GET.get('confirm')
        return ctx


class RemoveStaffFromProject(DeleteView):
    model = ProposedResource
    template_name = 'requests/confirm_remove_staff.html'

    def get_object(self):
        staff_id = self.kwargs.get('pk')
        return get_object_or_404(ProposedResource, pk=staff_id)

    def get_context_data(self, *args, **kwargs):
        context = super(RemoveStaffFromProject, self)\
            .get_context_data(*args, **kwargs)
        context['object'] = self.object
        return context

    def get_success_url(self):
        return self.object.project.get_absolute_url()

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        if self.object.response:
            self.object.accepted_by = None
        else:
            self.object.delete()
        return HttpResponseRedirect(self.get_success_url())
remove_staff_from_project = client_required(RemoveStaffFromProject.as_view())


class StaffingConfirmation(View):

    def get(self, request, *args, **kwargs):
        sr_pk = kwargs.get('sr_pk')
        answer = int(kwargs.get('answer'))
        user = request.user
        staffing_req = get_object_or_404(StaffingRequest, pk=sr_pk)

        try:
            rv_relation = RequestVendorRelationship\
                .objects.get(request=staffing_req,
                             vendor=user.vendor)

        except RequestVendorRelationship.DoesNotExist:
            if not staffing_req.is_public:
                raise Http404
            else:
                rv_relation = RequestVendorRelationship\
                    .objects.create(request=staffing_req,
                                    vendor=user.vendor,
                                    created_by=request.user)
        rv_relation.answered_by = self.request.user
        rv_relation.answer = answer
        rv_relation.save()

        if answer == RequestVendorRelationship.accepted:
            messages.success(self.request,
                             'We have updated the requestor '
                             'that you are on it')

        return HttpResponseRedirect(staffing_req.get_absolute_url())
staffing_confirmation = StaffingConfirmation.as_view()


class CreateDeliverableResponse(CreateView):
    template_name = 'responses/create.html'
    form_class = DeliverableResponseForm
    model = DeliverableResponse

    def dispatch(self, *args, **kwargs):
        stfrq_pk = kwargs.get('stfrq_pk')
        self.staffing_request = get_object_or_404(StaffingRequest, pk=stfrq_pk)
        self.project = self.staffing_request.project
        self.vendor = self.request.user.vendor
        # TODO: if request has already been accepted then redirect back to
        # request
        return super(CreateDeliverableResponse, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        url = reverse('home')
        url += '?project={proj_id}&request={req_id}'\
            .format(proj_id=self.project.id,
                    req_id=self.staffing_request.id)
        return url

    def get_form_kwargs(self):
        kwargs = super(CreateDeliverableResponse, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['staffing_request'] = self.staffing_request
        kwargs['vendor'] = self.vendor
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super(CreateDeliverableResponse, self).get_context_data(*args, **kwargs)
        ctx['staffing_request'] = self.staffing_request
        ctx['project'] = self.project
        return ctx

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())


class MyProjectList(View):

    def get(self, request):
        user = self.request.user
        url = URLObject(reverse('projects:list'))
        for group in user.divisions.all():
            url = url.add_query_param('group', str(group.id))
        return HttpResponseRedirect(url)

my_project_list = MyProjectList.as_view()


class ShareProjectView(FormView):
    template_name = 'projects/partials/share_project_form.html'
    form_class = ShareProjectForm

    def dispatch(self, *args, **kwargs):
        project_pk = self.kwargs['project_pk']
        self.project = get_object_or_404(Project, id=project_pk)
        return super(ShareProjectView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('projects:detail',
                       args=(self.project.id, ))

    def get_form_kwargs(self):
        kwargs = super(ShareProjectView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['project'] = self.project

        return kwargs

    def get_initial(self):
        initial = super(ShareProjectView, self).get_initial()
        initial_users = list()
        if self.project.division:
            division = self.project.division
            user_div_rel = UserDivisionRel.objects.filter(is_admin=True,
                                                          division=division)
            initial_users = get_user_model()\
                .objects.filter(division_rels__in=user_div_rel)

        initial['message'] = ("I have specified "
                              "staffing requirements for project "
                              "'{project}' in Proven. Can you please help?"
                              .format(project=self.project.title))
        initial['users'] = initial_users
        return initial

    def get_context_data(self, form=None):
        ctx = super(ShareProjectView, self).get_context_data()
        ctx['project'] = self.project
        if form:ctx['form'] = form
        return ctx

    def form_valid(self, form):

        message = form.cleaned_data['message']
        users = form.cleaned_data['users']

        tenant = connection.get_tenant()
        for obj in users:
            share_project_mail.delay(tenant_id=tenant.id,
                                     user_id=self.request.user.id,
                                     project_pk=self.project.id,
                                     message=message,
                                     recipient_id=obj.id)

        messages.success(self.request,
                         'Email notification sent to '
                         'the staffing team')
        return HttpResponseRedirect(self.get_success_url())

share_project = ShareProjectView.as_view()
