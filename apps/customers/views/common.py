import json

from django.views.generic.base import View
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views.generic.edit import CreateView
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import TemplateView

from urlobject import URLObject

from med_social.utils import get_current_tenant

from categories.models import Category, CategoryType
from features import models as features
from vendors.models import Vendor
from vendors.filters import VendorFilter
from locations.models import Location
from users.models import User

from ..forms import ClientInviteRequestForm, AutocompleteCreateForm, SearchForm


class CreateForAutocomplete(View):
    '''
    Create entities from autocomplete widgets or any form that just sends
    a `text` parameter in POST data.
    The models must implement the following interface in order to be able to
    suppoer autocomplete inline creation:

        class MyModel(models.Model):

            @classmethod
            def can_create(self, user):
                """Takes user instance and return True or False depending
                on whether the user should be allowed to create an object
                or not"""
                return True

            @classmethod
            def create_for_autocomplete(cls, text, extra_data):
                """Takes text parameter that was suplied by the form
                and a request object.
                Must return JSON in either of the following formats,

                    {
                        'text': 'Name of the created item',
                        'pk': 'Primary key of the created item'
                    }

                    {
                        'error': 'human readable error mesage',
                    }
                """
                slug = slugify(text)
                item, created = cls.objects.get_or_create(slug=slug,
                                                    defaults={'name': text})
                return {'text': item.name, 'pk': item.pk}

            @classmethod
            def get_autocomplete_create_url(cls, extra_data=None):
                """Should return the URL endpoint for inline creation for this
                model"""
                ctype = ContentType.objects.get_for_model(cls)
                return reverse('create_for_autocomplete', args=(ctype.id,))
    '''
    def render_to_json(self, result):
        result = json.dumps(result)
        return HttpResponse(result, content_type='application/json')

    def post(self, request, content_type_pk):
        ctype = get_object_or_404(ContentType, pk=content_type_pk)

        form = AutocompleteCreateForm(data=request.POST)
        if not form.is_valid():
            return self.render_to_json({'errors': form.errors})

        ModelClass = ctype.model_class()
        has_check_method = hasattr(ModelClass, 'can_create')
        has_create_method = hasattr(ModelClass, 'create_for_autocomplete')
        if not (has_check_method or has_create_method):
            return self.render_to_json(
                {'errors': 'The kind does not support creation from'
                           ' autocomplete'})

        if not ModelClass.can_create(request.user):
            return self.render_to_json({'errors': 'User not authorized to '
                                                  'take this action'})
        result = ModelClass.create_for_autocomplete(
            text=form.cleaned_data['text'], request=request)
        return self.render_to_json(result)


class HomeView(TemplateView):
    def get(self, request):
        tenant = get_current_tenant()
        if not request.user.is_authenticated():
            if tenant.is_public_instance:
                return HttpResponseRedirect(reverse('vendors:list'))
            return HttpResponseRedirect(reverse('account_login') + '?next=/')
        return HttpResponseRedirect(reverse('vendors:list'))


class ProjectsStatus(TemplateView):
    template_name = 'home/index.html'

    def get(self, request):
        if request.user.is_vendor:
            if features.projects.is_enabled():
                return HttpResponseRedirect(reverse('projects:list'))
            else:
                return HttpResponseRedirect(
                    request.user.vendor.get_absolute_url())
        else:
            return super(ProjectsStatus, self).get(request)


class MyProjectsStatus(TemplateView):
    template_name = 'home/index.html'

    def get(self, request):
        user = self.request.user
        url = URLObject(reverse('projects_status'))

        for group in user.divisions.all():
            url = url.add_query_param('group', str(group.id))
        return HttpResponseRedirect(url)


class ClientInviteRequestView(CreateView):
    template_name = 'client/request_invite.html'
    form_class = ClientInviteRequestForm

    def form_valid(self, form):
        super(ClientInviteRequestView, self).form_valid(form)
        return render_to_response(
            self.template_name, {'success': True},
            context_instance=RequestContext(self.request))

    def get_success_url(self):
        return '/'


class VendorSearch(TemplateView):
    template_name = 'home/search.html'

    def get_context_data(self, **kwargs):
        context = super(VendorSearch, self).get_context_data(**kwargs)
        context['form'] = SearchForm()
        value = self.request.user.meta.get('last-searched')

        obj_list = {}
        if value:
            for idx, V in enumerate(value):
                obj_list[idx] = []
                value_dict = {}
                for obj in V:
                    if '-' not in obj:
                        continue
                    field, val = obj.split('-', 1)

                    l = value_dict.get(field, [])
                    l.append(val)
                    value_dict[field] = l
                    print idx, obj_list[idx]

                if 'skill' in value_dict:
                    skills = list(Category.skills.filter(id__in=value_dict['skill']))
                    if skills:
                        skills.insert(0, 'Keyword:')
                    obj_list[idx].append(skills)

                if 'service' in value_dict:
                    services = list(Category.services.filter(id__in=value_dict['service']))
                    if services:
                        services.insert(0, 'Service:')
                    obj_list[idx].append(services)

                if 'category' in value_dict:
                    categ_type = CategoryType.objects.filter(vendor_editable=False).first()

                    categories = list(Category.objects.filter(custom_kind=categ_type, id__in=value_dict['category']))
                    if categories:
                        categories.insert(0, 'Categories:')
                    obj_list[idx].append(categories)

                if 'vendor' in value_dict:
                    vendors = list(Vendor.objects.filter(id__in=value_dict['vendor']))
                    if vendors:
                        vendors.insert(0, 'Supplier(s):')
                    obj_list[idx].append(vendors)

                if 'search' in value_dict:
                    searches = list(value_dict['search'])
                    if searches:
                        searches.insert(0, 'Text search:')
                    obj_list[idx].append(searches)

                if 'user' in value_dict:
                    users = list(User.objects.filter(id__in=value_dict['user']))
                    if users:
                        users.insert(0, 'User(s):')
                    obj_list[idx].append(users)

                if 'loc' in value_dict:
                    locations = list(Location.objects.filter(id__in=value_dict['loc']))
                    if locations:
                        locations.insert(0, 'in')
                    obj_list[idx].append(locations)

        context['past_query'] = self.request.user.meta.get('last-query')
        context['past_searches'] = obj_list
        context['vendor_filter'] = VendorFilter(
            self.request.GET,
            request=self.request,
            queryset=Vendor.objects.all()
        )
        context['included_filters'] = ('find',)
        return context
