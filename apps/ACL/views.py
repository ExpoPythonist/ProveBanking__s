from django.contrib import messages
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse, reverse_lazy
from django.http.response import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from med_social.views.base import BaseEditView
from .forms import GroupForm


class GroupCreateView(CreateView):
    template_name = 'ACL/create.html'
    form_class = GroupForm
    model = Group

    def get_form_kwargs(self):
        kwargs = super(GroupCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse('groups:list')


class GroupList(ListView):
    model = Group
    context_object_name = 'groups'
    template_name = 'ACL/list.html'

    def get_queryset(self):
        user = self.request.user
        if user.is_client:
            qs = self.model.objects.filter(vendor=None)
        elif user.is_vendor:
            qs = self.model.objects.filter(vendor=user.vendor)
        else:
            Http404()
        return qs.order_by('name')


class GroupEditView(BaseEditView):
    model_form = GroupForm
    template_name = 'ACL/create.html'
    context_variable = 'group'
    success_url = reverse_lazy('groups:list')
    deleted = False

    def get_instance(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_client:
            return get_object_or_404(self.model, pk=self.kwargs['pk'], vendor=None)
        elif user.is_vendor:
            return get_object_or_404(self.model, pk=self.kwargs['pk'], vendor=user.vendor)
        raise Http404()

    def form_delete(self, form):
        if self.object.kind in [Group.DEFAULT_USER, Group.DEFAULT_ADMIN]:
            messages.warning(
                self.request,
                _('{} is a system created group, it cannot be deleted.'.format(self.object.display_name)),
            )
            return HttpResponseRedirect(reverse('groups:edit', args=(self.object.id,)))
        return super(GroupEditView, self).form_delete(form)

    def save_m2m(self, form):
        pass
