from django.views.generic import (ListView,
                                  UpdateView,
                                  CreateView,
                                  FormView)
from django.shortcuts import redirect, get_object_or_404
from django.core.urlresolvers import reverse, reverse_lazy

from .models import Service, ServiceVendor
from .forms import ServiceVendorForm


class ServiceTypeList(ListView):
    model = Service
    template_name = 'services/list.html'
    context_object_name = 'services'


class CreateServiceType(CreateView):
    model = Service
    success_url = reverse_lazy('client_settings:services:list')
    template_name = 'services/form.html'
    fields = ('name', 'description')

    def get_context_data(self, *args, **kwargs):
        context = super(CreateServiceType, self).get_context_data(*args,
                                                                  **kwargs)
        context['action_label'] = 'create a'
        return context


class EditServiceType(UpdateView):
    model = Service
    success_url = reverse_lazy('client_settings:services:list')
    template_name = 'services/form.html'
    fields = ('name', 'description')

    def get_context_data(self, *args, **kwargs):
        context = super(EditServiceType, self).get_context_data(*args,
                                                                **kwargs)
        context['action_label'] = 'edit'
        return context


class AddServiceTypeContact(CreateView):
    model = ServiceVendor
    template_name = 'services/service_contact_form.html'
    form_class = ServiceVendorForm

    def form_valid(self, form):
        form.instance.vendor = self.request.user.vendor
        return super(AddServiceTypeContact, self).form_valid(form)

    def get_success_url(self):
        return self.request.user.vendor.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super(AddServiceTypeContact, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(AddServiceTypeContact, self).get_context_data(*args,
                                                                      **kwargs)
        context['action_label'] = 'add'
        return context


class EditServiceTypeContact(UpdateView):
    model = ServiceVendor
    template_name = 'services/service_contact_form.html'
    form_class = ServiceVendorForm

    def get_success_url(self):
        return self.request.user.vendor.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super(EditServiceTypeContact, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(EditServiceTypeContact, self).get_context_data(*args,
                                                                      **kwargs)
        context['action_label'] = 'edit'
        return context
