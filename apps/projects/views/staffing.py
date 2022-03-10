from datetime import timedelta

from django.views.generic import (ListView, UpdateView, CreateView, DeleteView,
                                  FormView, TemplateView)
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.db import connection
from django.db.models import Q, Count
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from watson import search as watson

from aggregate_if import Sum
from urlobject import URLObject

from med_social.decorators import member_required, client_required
from med_social.utils import this_week, get_week_from_date

from users.filters import UserFilter
from vendors.models import Vendor
from vendors.filters import VendorFilter

from ..models import (StaffingRequest, ProposedResource,
                      ProposedResourceStatus, Project,
                      RequestVendorRelationship)
from ..forms import (StaffingACLForm, StaffingACLVendorsForm,
                     StaffingBasicForm, StaffingAdvancedForm,
                     RequestForm, SearchForm)
from ..filters import StaffingFilter
from ..tasks import staffing_req_user_add, create_request_vendor_relation


class SearchVendorsandPeople(TemplateView):
    template_name = 'requests/recommendations.html'

    def get_context_data(self, results):
        ctx = super(SearchVendorsandPeople, self).get_context_data()
        ctx['results'] = results
        return ctx

    def get(self, request):
        f = SearchForm(data=request.GET)
        if f.is_valid():
            q = f.cleaned_data.get('q', '')
        else:
            q = ''
        results = watson.search(q, models=(Vendor, get_user_model(),))
        return self.render_to_response(self.get_context_data(results))
search_vendors_and_people = SearchVendorsandPeople.as_view()


class AddVendorsToRequest(FormView):
    form_class = RequestForm
    template_name = 'requests/partials/add_vendors.html'
    stfrq = None

    def get_success_url(self):
        if self.stfrq:
            return reverse('staffing:requests:detail', args=(self.stfrq.pk,))
        else:
            return reverse('vendors:list')

    def get_initial(self):
        initial = {}
        initial['vendors'] = self.request.GET.getlist('vendors', [])
        return initial

    def get_context_data(self, form=None):
        ctx = super(AddVendorsToRequest, self).get_context_data()
        if form:ctx['form'] = form
        if hasattr(form, 'cleaned_data'):
            ctx['vendors'] = form.cleaned_data.get('vendors', [])
        return ctx

    def form_valid(self, form):
        self.stfrq = form.cleaned_data.get('request')
        vendors = form.cleaned_data.get('vendors')
        if not self.stfrq:
            # handle new requests
            pass
        else:
            if vendors:
                messages.add_message(self.request, messages.INFO,
                                    'Added {} vendor(s) to the request.'.format(
                                        vendors.count()))
                for vendor in vendors:
                    RequestVendorRelationship.objects.get_or_create(
                        request=self.stfrq, vendor=vendor,
                        defaults={
                            'created_by': self.request.user
                        }
                    )
            return super(AddVendorsToRequest, self).form_valid(form)
add_vendors = client_required(AddVendorsToRequest.as_view())


class DeleteDraft(DeleteView):
    model = StaffingRequest
    template_name = 'requests/draft_deleted.html'

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data())
        else:
            return HttpResponseRedirect(self.get_success_url())

    def get(self, *args, **kwargs):
        return reverse('staffing:drafts')

    def get_queryset(self):
        return StaffingRequest.drafts.filter(created_by=self.request.user)

    def get_success_url(self):
        return reverse('staffing:drafts')

    def get_context_data(self):
        ctx = super(DeleteDraft, self).get_context_data()
        ctx['staffing_request'] = self.object
        return ctx
delete_draft = client_required(DeleteDraft.as_view())


class StaffingRequestCreateView(CreateView):
    model = StaffingRequest
    form_class = StaffingBasicForm
    template_name = 'requests/create.html'
    success = False
    kind = None

    def get_title(self):
        return 'New request'

    def get_entity_title(self):
        return 'Staffing request'

    def dispatch(self, request, project_pk=None, request_kind=None):
        self.object = None
        self.kind = StaffingRequest.KIND_NAMES_REVERSE.get(
            request_kind, StaffingRequest.KIND_STAFFING)
        if project_pk:
            self.project = get_object_or_404(Project, id=project_pk)
        else:
            self.project = None
        return super(StaffingRequestCreateView, self).dispatch(
            request, project_pk, request_kind)

    def form_valid(self, form):
        self.object = form.save()
        self.object.last_activity = self.request.user
        self.object.save()
        if (self.request.is_ajax() and \
                not 'HTTP_X_PJAX' in self.request.META):
            return self.render_to_response(self.get_context_data(form))
        if self.request.POST.get('submit') == 'advanced':
            return HttpResponseRedirect(reverse('staffing:requests:edit_advanced',
                                                args=(self.object.id,)))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.request.user.cart.exists():
            return reverse('checkout') + '?request={}'.format(self.object.id)
        return reverse('users:list')

    def get_initial(self):
        initial = {}
        if self.project:
            initial.update({
                'start_date': self.project.start_date,
                'end_date': self.project.end_date,
                'project': self.project,
                'owners': list(self.project.owners.all()) +
                    [self.request.user]
            })
        initial.update({
            'location': self.request.GET.get('location'),
            'role': self.request.GET.get('role'),
            'categories': self.request.GET.getlist('categories'),
        })
        return initial

    def get_form_kwargs(self):
        kwargs = super(StaffingRequestCreateView, self).get_form_kwargs()
        kwargs['kind'] = self.kind
        kwargs['request'] = self.request
        kwargs['project'] = self.project
        default_values = self.get_initial()
        kwargs['default_values'] = default_values
        return kwargs

    def get_context_data(self, form=None):
        context = super(StaffingRequestCreateView, self).get_context_data()
        context['form'] = form
        context['basic_form'] = form
        context['advanced_form'] = StaffingAdvancedForm(**self.get_form_kwargs())
        context['project'] = self.project
        context['staffing_request'] = self.object
        context['stfrq'] = self.object
        context['form_saved'] = bool(self.object)
        reverse_args = []
        if self.project:
            reverse_args.append(self.project.id)
        if self.kind == StaffingRequest.KIND_FIXED:
            reverse_args.append('fixed')
        else:
            reverse_args.append('staffing')
        context['action'] = reverse('staffing:requests:create', args=reverse_args)
        return context

    def get_template_names(self):
        if self.request.is_ajax() and not 'HTTP_X_PJAX' in self.request.META:
            return ['requests/partials/inline-form-section.html']
        else:
            return ['requests/create.html']
staffing_request_create = client_required(StaffingRequestCreateView.as_view())


class StaffingRequestBasic(UpdateView):
    model = StaffingRequest
    context_variable = 'stfrq'
    form_class = StaffingBasicForm

    def get_title(self):
        return 'Edit request'

    def get_entity_title(self):
        return 'Staffing request'

    def get_object(self):
        try:
            return StaffingRequest.objects.get(pk=self.kwargs['pk'])
        except StaffingRequest.DoesNotExist:
            raise Http404()

    def get_success_url(self):
        if self.request.user.cart.exists():
            return reverse('checkout') + '?request={}'.format(self.object.id)
        else:
            return self.object.get_absolute_url()

    def dispatch(self, request, pk, step=None):
        self.object = self.get_object()
        self.project = self.object.project
        return super(StaffingRequestBasic, self).dispatch(
            request, pk, step)

    def form_valid(self, form):
        ret = super(StaffingRequestBasic, self).form_valid(form)
        self.object.last_activity = self.request.user
        self.object.save()

        if self.request.is_ajax() and not 'HTTP_X_PJAX' in self.request.META:
            return self.render_to_response(self.get_context_data(form))
        if self.request.POST.get('submit') == 'advanced':
            return HttpResponseRedirect(reverse('staffing:requests:edit_advanced',
                                                args=(self.object.id,)))
        return ret

    def get_form_kwargs(self):
        kwargs = super(StaffingRequestBasic, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['project'] = self.project
        return kwargs

    def get_initial(self):
        initial = {}
        if self.project:
            initial.update({
                'start_date': self.project.start_date,
                'end_date': self.project.end_date,
                'project': self.project,
                'owners': list(self.project.owners.all()) +
                    [self.request.user]
            })
        return initial

    def get_context_data(self, form=None):
        context = super(StaffingRequestBasic, self).get_context_data()
        context['form'] = form
        context['basic_form'] = form
        context['advanced_form'] = StaffingAdvancedForm(
            request=self.request, project=self.project,
            instance=self.object,
            initial=self.get_initial()
        )
        context['project'] = self.object.project
        context['staffing_request'] = self.object
        context['stfrq'] = self.object
        return context

    def get_template_names(self):
        if self.request.is_ajax() and not 'HTTP_X_PJAX' in self.request.META:
            return 'requests/partials/create_form.html'
        else:
            return 'requests/create.html'

    def get_action_url(self):
        return reverse('staffing:requests:edit',
                       args=(self.object.id,))
staffing_basic = client_required(StaffingRequestBasic.as_view())


class StaffingRequestAdvanced(UpdateView):
    model = StaffingRequest
    form_class = StaffingAdvancedForm
    template_name = 'requests/create.html'

    def get_object(self):
        try:
            return StaffingRequest.objects.get(pk=self.kwargs['pk'])
        except StaffingRequest.DoesNotExist:
            raise Http404()

    def get_success_url(self):
        if self.request.user.cart.exists():
            return reverse('checkout') + '?request={}'.format(self.object.id)
        return reverse('users:list')

    def get_context_data(self, form=None):
        context = super(StaffingRequestAdvanced, self).get_context_data()
        context['advanced_form'] = form
        context['stfrq'] = self.object
        context['project'] = self.object.project
        return context

    def get_form_kwargs(self):
        kwargs = super(StaffingRequestAdvanced, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['project'] = self.object.project
        return kwargs
staffing_advanced = client_required(StaffingRequestAdvanced.as_view())



class ChangeStaffingACL(UpdateView):
    model = StaffingRequest
    form_class = StaffingACLForm
    template_name = 'requests/partials/acl_button.html'

    def dispatch(self, request, request_pk):
        self.object = self.get_object()
        # TODO: check for proper permissions
        return super(ChangeStaffingACL, self).dispatch(request, request_pk)

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_response(self.get_context_data(form))

    def get_object(self):
        return get_object_or_404(StaffingRequest, pk=self.kwargs['request_pk'])

    def get_context_data(self, form=None):
        ctx = super(ChangeStaffingACL, self).get_context_data()
        ctx['staffing_request'] = ctx['object'] = self.object
        return ctx
change_staffing_acl = client_required(ChangeStaffingACL.as_view())


class ChangeStaffingACLVendors(UpdateView):
    model = StaffingRequest
    form_class = StaffingACLVendorsForm
    template_name = 'requests/partials/acl_vendors.html'

    def dispatch(self, request, request_pk):
        self.object = self.get_object()
        # TODO: check for proper permissions
        return super(ChangeStaffingACLVendors, self).dispatch(request,
                                                              request_pk)

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_response(self.get_context_data(form))

    def get_object(self):
        return get_object_or_404(StaffingRequest,
                                 pk=self.kwargs['request_pk'])

    def get_context_data(self, form=None):
        ctx = super(ChangeStaffingACLVendors, self).get_context_data()
        ctx['object'] = self.object
        if form:ctx['form'] = form
        ctx['answered'] = self.object.request_vendors.exclude(answer=None)\
            .order_by('-answered_at')
        ctx['unanswered'] = self.object.request_vendors.filter(answer=None)
        return ctx

    def get_form_kwargs(self):
        kwargs = super(ChangeStaffingACLVendors, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
change_staffing_acl_vendors = client_required(
    ChangeStaffingACLVendors.as_view())


class UsersAddList(ListView):
    model = get_user_model()
    template_name = 'users/list.html'

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('stfrq_pk')
        staffing_request = get_object_or_404(StaffingRequest, pk=pk)
        cart = self.request.user.cart
        cart.request = staffing_request
        cart.save()
        url = URLObject(reverse('users:list'))
        if staffing_request.role:
            url = url.add_query_params(roles=str(staffing_request.role.id))
        if staffing_request.location:
            url = url.add_query_params(location=str(staffing_request.location.id))
        url = url.add_query_params(availability='now')
        for C in staffing_request.categories.values_list('id', flat=True):
            url = url.add_query_params(categories=str(C))
        return HttpResponseRedirect(url)


class VendorAddList(ListView):
    model = Vendor
    context_object_name = 'vendors'
    template_name = 'vendors/list.html'

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('stfrq_pk')
        staffing_request = get_object_or_404(StaffingRequest, pk=pk)
        cart = self.request.user.cart
        cart.request = staffing_request
        cart.save()
        url = URLObject(reverse('vendors:list'))
        if staffing_request.role:
            url = url.add_query_params(roles=str(staffing_request.role.id))
        if staffing_request.location:
            url = url.add_query_params(location=str(staffing_request.location.id))
        for C in staffing_request.categories.values_list('id', flat=True):
            url = url.add_query_params(categories=str(C))
        return HttpResponseRedirect(url)
