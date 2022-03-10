from django.views.generic.list import ListView
from django.views.generic.edit import CreateView
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.http.response import Http404
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404

from med_social.views.base import BaseEditView
from .models import Location
from .forms import LocationCreateForm, LocationEditForm


class LocationList(ListView):
    model = Location
    context_object_name = 'locations'
    template_name = 'locations/list.html'

    def get_queryset(self):
        user = self.request.user
        if user.is_client:
            return self.model.objects.all().order_by('city')
        else:
            Http404()


class CreateLocations(CreateView):
    template_name = 'locations/create.html'
    form_class = LocationCreateForm
    model = Location

    def get_success_url(self):
        return reverse('client_settings:location_list')


class EditLocations(BaseEditView):
    model_form = LocationEditForm
    template_name = 'locations/create.html'
    context_variable = 'location'

    def get_success_url(self):
        return reverse('client_settings:location_list')

    def get_instance(self, *args, **kwargs):
        user = self.request.user
        if user.is_client:
            qs = {'id': self.kwargs['pk']}
            return get_object_or_404(self.model, **qs)
        return Http404()

    def post_delete(self, instance):
        messages.warning(self.request,
                _('Location {} deleted successfully.'.format(instance)))


def location_search(request):
    q = request.GET.get('q')
    kind = request.GET.get('kind')
    if not kind:
        kind = Location.KIND_CITY
    if q:
        locs = Location.objects.filter(city__istartswith=q, kind=kind)[:10]
        data = [{'pk': loc.id, 'text': loc.city, 'caption': loc.expanded}
                for loc in locs]
    else:
        data = []
    return JsonResponse(data, safe=False)


def location_select_search(request):
    q = request.GET.get('q')
    kind = request.GET.get('kind')
    if not kind:
        kind = Location.KIND_CITY
    if q:
        locs = Location.objects.filter(city__istartswith=q, kind=kind)[:10]
        data = [{'value': loc.id, 'label': loc.city, 'caption': loc.expanded}
                for loc in locs]
    else:
        data = []
    return JsonResponse(data, safe=False)
