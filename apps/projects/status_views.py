from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from med_social.decorators import client_required
from projects.models import ProposedResourceStatus, StatusFlow
from projects.forms import ProposedStatusForm, StatusFlowForm


class CreateFlow(CreateView):
    model = StatusFlow
    form_class = StatusFlowForm
    template_name = 'projects/proposed_status/create_flow.html'
    context_object_name = 'flow_object'

    def dispatch(self, request, status_pk):
        self.status_object = get_object_or_404(ProposedResourceStatus,
                                               pk=status_pk)
        return super(CreateFlow, self).dispatch(request, status_pk)

    def get_success_url(self):
        return self.status_object.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super(CreateFlow, self).get_form_kwargs()
        kwargs['backward'] = self.status_object
        return kwargs
create_flow = client_required(CreateFlow.as_view())


class EditFlow(UpdateView):
    model = StatusFlow
    form_class = StatusFlowForm
    template_name = 'projects/proposed_status/create_flow.html'
    context_object_name = 'flow_object'

    def dispatch(self, request, pk):
        self.object = self.get_object()
        self.status_object = get_object_or_404(ProposedResourceStatus,
                                               pk=self.object.backward.id)
        return super(EditFlow, self).dispatch(request, pk)

    def get_success_url(self):
        return self.status_object.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super(EditFlow, self).get_form_kwargs()
        kwargs['backward'] = self.status_object
        return kwargs
edit_flow = client_required(EditFlow.as_view())


class ListStatus(ListView):
    template_name = 'projects/proposed_status/list.html'
    queryset = ProposedResourceStatus.objects.all()
    context_object_name = 'status_list'

    def get_context_data(self):
        ctx = super(ListStatus, self).get_context_data()
        for S in ctx['status_list']:
            if S.value == ProposedResourceStatus.INITIATED:
                ctx['initiated_exists'] = True
                break
        return ctx
list_status = client_required(ListStatus.as_view())


class CreateStatus(CreateView):
    template_name = 'projects/proposed_status/create.html'
    model = ProposedResourceStatus
    context_object_name = 'status'
    form_class = ProposedStatusForm

    def get_success_url(self):
        return reverse('projects:status:details', args=(self.object.id,))
create_status = client_required(CreateStatus.as_view())


class EditStatus(UpdateView):
    template_name = 'projects/proposed_status/create.html'
    model = ProposedResourceStatus
    form_class = ProposedStatusForm

    def get_object(self):
        return get_object_or_404(ProposedResourceStatus,
                                 pk=self.kwargs['status_pk'])

    def get_success_url(self):
        return reverse('projects:status:details', args=(self.object.id,))
edit_status = client_required(EditStatus.as_view())


class StatusDetails(DetailView):
    model = ProposedResourceStatus
    template_name = 'projects/proposed_status/details.html'

    def get_object(self):
        return get_object_or_404(ProposedResourceStatus,
                                 pk=self.kwargs['status_pk'])
status_details = client_required(StatusDetails.as_view())
