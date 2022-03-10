import calendar
import datetime
import hashlib
import hmac
import json
import mimetypes
import tempfile
import os
import clearbit
import xmltodict
import tldextract
import requests

from django.conf import settings
from django.views.generic import View
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.files.base import ContentFile
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.timezone import now, get_default_timezone_name
from django.db import connection

from annoying.functions import get_object_or_None
from allauth.socialaccount.models import SocialToken
from hellosign_sdk import HSClient
from urlparse import urlparse
from suds.client import Client
from dateutil import parser
import pytz
from rest_framework import generics
from watson import search as watson
from watson.models import SearchEntry
from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.generics import RetrieveAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from med_social.utils import track_event, suds_to_json
from med_social.decorators import client_required
from med_social.utils import get_current_tenant
from categories.models import Category
from channels.models import Channel, Message
from locations.models import Location
from roles.models import Role
from divisions.models import Division
from users.filters import UserFilter
from users.utils import generate_unique_username
from users.tasks import user_invite
from vendors.models import Vendor, ProcurementContact
from vendors.filters import VendorFilter

from projects.utils import get_status_options
from projects.filters import ProjectFilter
from projects.models import Project, ProposedResource, ProposedResourceStatus, StaffingRequest

from med_social.filters import CATEGORIES_OPTGROUPS
from aggregators.models import Search
from aggregators.utils import hash_query
from aggregators.tasks import search_news_task

from vendors.forms import VendorInviteForm
from .permissions import IsClient, VendorReadOnly
from .serializers import (ProjectSerializer, ProposedUserSerializer, UserSerializer, RequestSerializer,
                          LocationSerializer, ResponseSerializer,
                          RoleSerializer, DivisionSerializer, VendorSerializer, SearchSerializer,
                          CategorySerializer, AggregatorSerializer, VendorNewsSerializer, MessageSerializer)

PRS = ProposedResourceStatus


class Filters(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        query = request.GET.get('q', '')
        results = []
        if query:
            results = []
            results.append({
                'pk': '{}-{}'.format('search', query),
                'text': query,
                'optgroup': 'Search'
            })
            matches = watson.search(query, models=[Vendor, Category, get_user_model()])
            if not matches:
                return HttpResponse(JSONRenderer().render(results), content_type="application/json")

            cat_ctype = ContentType.objects.get_for_model(Category)
            vendor_ctype = ContentType.objects.get_for_model(Vendor)
            user_ctype = ContentType.objects.get_for_model(get_user_model())

            for M in matches:
                if M.content_type == vendor_ctype:
                    results.append({
                        'pk': 'vendor-{}'.format(M.object_id),
                        'text': M.title,
                        'optgroup': 'Suppliers'
                    })
                elif M.content_type == user_ctype:
                    results.append({
                        'pk': 'user-{}'.format(M.object_id),
                        'text': M.title,
                        'optgroup': 'People'
                    })
                elif M.content_type == cat_ctype and M.object.kind == Category.KIND_CUSTOM:
                    results.append({
                        'pk': '{}-{}'.format('category', M.object_id),
                        'text': M.title,
                        'optgroup': CATEGORIES_OPTGROUPS[M.object.kind]
                    })
                elif M.content_type == cat_ctype:
                    if M.object.kind == Category.KIND_CATEGORY:
                        results.append({
                            'pk': '{}-{}'.format('skill', M.object_id),
                            'text': M.title,
                            'optgroup': CATEGORIES_OPTGROUPS[M.object.kind]
                        })
                    elif M.object.kind == Category.KIND_SERVICE:
                        results.append({
                            'pk': '{}-{}'.format(M.object.get_kind_display(), M.object_id),
                            'text': M.title,
                            'optgroup': CATEGORIES_OPTGROUPS[M.object.kind]
                        })

            return HttpResponse(
                JSONRenderer().render(results),
                content_type="application/json"
            )
        return HttpResponse(
            JSONRenderer().render([]),
            content_type="application/json"
        )
filters = Filters.as_view()


class VendorNewsViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorNewsSerializer

    def dispatch(self, request, vendor_pk):
        self.vendor = get_object_or_404(Vendor, id=vendor_pk)
        return super(VendorNewsViewSet, self).dispatch(request, vendor_pk)

    def get_object(self):
        return self.vendor

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class AggregatorViewSet(viewsets.ModelViewSet):
    queryset = Search.objects.all()
    serializer_class = AggregatorSerializer

    def get_queryset(self):
        qs = super(AggregatorViewSet, self).get_queryset()
        query = self.request.GET.get('query', '')
        if query:
            return qs.filter(hashed=hash_query(query))
        return qs




class RequestViewSet(viewsets.ModelViewSet):
    queryset = StaffingRequest.objects.all()
    serializer_class = RequestSerializer
    permission_classes = (IsAuthenticated,)

    @detail_route(methods=['POST'])
    def archive(self, request, pk=None):
        staffing_request = get_object_or_404(StaffingRequest, id=pk)
        if self.request.user.is_client:
            staffing_request.is_archived = True
            staffing_request.save()
            return HttpResponse(
                JSONRenderer().render({'status': 'OK'}), content_type="application/json")
        raise Http404()

    @detail_route(methods=['POST'])
    def unarchive(self, request, pk=None):
        staffing_request = get_object_or_404(StaffingRequest, id=pk)
        if self.request.user.is_client:
            staffing_request.is_archived = False
            staffing_request.save()
            return HttpResponse(
                JSONRenderer().render({'status': 'OK'}), content_type="application/json")
        raise Http404()


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = super(LocationViewSet, self).get_queryset()
        search = self.request.GET.get('search', None)
        if search:
            qs = qs.filter(city__icontains=search)
        kind = self.request.GET.get('kind', None)
        if kind:
            qs = qs.filter(kind=kind)
        return qs

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)


class DivisionViewSet(viewsets.ModelViewSet):
    queryset = Division.objects.all()
    serializer_class = DivisionSerializer
    permission_classes = (IsAuthenticated,)


class ProjectPeopleViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.none()
    serializer_class = ProposedUserSerializer
    permission_classes = (IsAuthenticated,)


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = super(UserViewSet, self).get_queryset()
        if self.request.user.is_vendor:
            qs = qs.filter(vendor=self.request.user.vendor)
        return UserFilter(self.request.QUERY_PARAMS, queryset=qs, request=self.request).qs.distinct()

    def perform_create(self, serializer):
        username = generate_unique_username([
            serializer.validated_data.get('first_name'),
            serializer.validated_data.get('last_name'),
            serializer.validated_data.get('email'),
        ])
        serializer.validated_data['username'] = username
        obj = serializer.save(vendor=self.request.user.vendor, kind=self.request.user.kind)
        if self.request.DATA.get('invite'):
            self.send_invitation(obj)

    def send_invitation(self, user, password=None):
        expires_at = now() + datetime.timedelta(days=7)
        tenant = get_current_tenant()
        invitation, created = user.invitations.get_or_create(
            sender=self.request.user, receiver=user, defaults={
                'expires_at': expires_at
            })
        invitation.expires_at = expires_at
        invitation.save()
        user_invite.delay(tenant_id=tenant.id, invite_id=invitation.id, password=password, message=None)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = super(CategoryViewSet, self).get_queryset()
        search = self.request.GET.get('search', None)
        if search:
            qs = qs.filter(name__icontains=search)
        kind = self.request.GET.get('kind', None)
        if kind:
            qs = qs.filter(kind=kind)
        return qs


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = (IsAuthenticated, IsClient)

    def get_queryset(self):
        qs = super(VendorViewSet, self).get_queryset()
        return VendorFilter(self.request.QUERY_PARAMS, request=self.request, queryset=qs).qs.distinct()

    @detail_route(methods=['POST'])
    def add_keyword(self, request, pk):
        if not request.user.is_client:
            raise Http404()
        vendor = get_object_or_404(Vendor, pk=pk)
        keyword = '{}'.format(request.data.get('keyword', '')).strip()
        if keyword:
            keywords = vendor.get_search_keywords()
            keywords.append(keyword)
            vendor.search_keywords = list(set(keywords))
            vendor.save()

        for keyword in vendor.get_search_keywords():
            search_news_task.delay(query=keyword)

        return HttpResponse(JSONRenderer().render(VendorNewsSerializer(vendor).data), content_type="application/json")

    @detail_route(methods=['POST'])
    def remove_keyword(self, request, pk):
        if not request.user.is_client:
            raise Http404()
        vendor = get_object_or_404(Vendor, pk=pk)
        keyword = '{}'.format(request.data.get('keyword', '')).strip()
        if keyword in vendor.search_keywords:
            vendor.search_keywords.remove(keyword)
            vendor.save()
        return HttpResponse(JSONRenderer().render(VendorNewsSerializer(vendor).data), content_type="application/json")

    @list_route(methods=['POST'])
    def invite(self, request):
        if not request.user.is_client:
            raise Http404()
        form = VendorInviteForm(request.DATA)
        if form.is_valid():
            vendor = form.save()
            vendor.vendor_invitations.get_or_create(user=request.user)
            return HttpResponse(
                JSONRenderer().render(
                    VendorSerializer(vendor).data
                ), content_type="application/json")
        else:
            return HttpResponse(JSONRenderer().render(form.errors), status=400, content_type="application/json")


# FIXME: Use a proper view using rest viewsets
from django.views.decorators.csrf import csrf_exempt


class AddToProject(View):
    def post(self, request):
        if not request.user.is_client:
            raise Http404()

        project = get_object_or_404(Project, id=request.POST.get('project_id'))
        user = get_object_or_404(get_user_model(), id=request.POST.get('user_id'))
        status = ProposedResourceStatus.objects.filter(value=ProposedResourceStatus.SUCCESS)[0]

        try:
            proposed = project.proposals.filter(resource=user, status__value=ProposedResourceStatus.SUCCESS)[0]
        except IndexError:
            proposed, created = project.proposals.get_or_create(resource=user, request=None, defaults={
                'start_date': project.start_date,
                'end_date': project.end_date,
                'status': status,
                'created_by': request.user,
                'changed_by': request.user,
            })
        return HttpResponse(JSONRenderer().render(ResponseSerializer(proposed).data), content_type="application/json")
add_to_project = client_required(csrf_exempt(AddToProject.as_view()))


class ChangeResourceStatus(View):
    def post(self, request):
        if not request.user.is_client:
            raise Http404()

        response = get_object_or_404(ProposedResource, id=request.POST.get('resource_id'))
        status = get_object_or_404(ProposedResourceStatus, id=request.POST.get('status_id'))
        if not response.status.forwards.filter(id=status.id).exists():
            raise Http404()
        else:
            response.status = status
            response.changed_by = request.user
            response.save()

        return HttpResponse(JSONRenderer().render(ResponseSerializer(response).data), content_type="application/json")
change_resource_status = client_required(csrf_exempt(ChangeResourceStatus.as_view()))


class SearchView(generics.ListAPIView):
    serializer_class = SearchSerializer
    permission_classes = (IsAuthenticated, IsClient)

    class FakeContentType(object):
        def __init__(self, title, content_type, url):
            self.title = title
            self.content_type = type('FakeContentType', (), {'name': content_type, 'id': content_type})
            self.object_id = 'fake'
            self.url = url

    def dispatch(self, request):
        ret = super(SearchView, self).dispatch(request)
        track_event('search:global', {
            'search_term': request.GET.get('q'),
            'user': self.request.user.username,
            'user_id': self.request.user.id
        })
        return ret

    def get_queryset(self):
        q = self.request.GET.get('q', '').strip()
        if not q:
            results = list(SearchEntry.objects.none())
        else:
            results = list(watson.search(q).distinct()[:4])
        #results.append(self.FakeContentType(q, 'users', '/users/?search=' + q))
        #results.append(self.FakeContentType(q, 'vendors', '/vendors/?search=' + q))
        #results.append(self.FakeContentType(q, 'projects', '/projects/?search=' + q))
        return results
search_view = SearchView.as_view()
