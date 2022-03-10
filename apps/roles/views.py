from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse

from med_social.decorators import client_required
from .models import Role


class ListRoles(ListView):
    model = Role
    template_name = 'roles/list.html'
    context_object_name = 'roles'
list_roles = client_required(ListRoles.as_view())


class CreateRole(CreateView):
    model = Role
    fields = '__all__'
    template_name = 'roles/create.html'
    context_object_name = 'role'

    def get_success_url(self):
        return reverse('client_settings:roles:list')
create_role = client_required(CreateRole.as_view())


class UpdateRole(UpdateView):
    model = Role
    fields = '__all__'
    template_name = 'roles/create.html'
    context_object_name = 'role'

    def get_success_url(self):
        return reverse('client_settings:roles:list')
update_role = client_required(UpdateRole.as_view())


class DeleteRole(DeleteView):
    model = Role
    context_object_name = 'role'

    def get_success_url(self):
        return reverse('client_settings:roles:list')
delete_role = client_required(DeleteRole.as_view())
