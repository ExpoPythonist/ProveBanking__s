import datetime
import urlparse
import re
from urlparse import parse_qs
from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext as _
from django.utils.timezone import now
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import View, ListView, DetailView, FormView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from annoying.functions import get_object_or_None
from carton.cart import Cart
from notifications.signals import notify

from med_social.decorators import member_required
from med_social.utils import track_event, pretty_form_errors
from med_social.views.base import BaseEditView
from med_social.utils import get_current_tenant
from analytics.models import PageView
from clients.models import Client
from features import models as features
from projects.models import (Project, ProposedResourceStatus,)
from services.models import ServiceVendor

from aggregators.tasks import search_news_task
from categories.models import CategoryType, Category
from reviews.models import Review, ReviewToken
from users.models import User
from .models import (Vendor, VendorLocation, VendorRoles, VendorCategories, VendorInvitation,
                     PortfolioItem, VendorServices, ProcurementContact,
                     CertVerification, InsuranceVerification, ClientReference, Invoice, VendorIndustry,
                     VendorCustomKind, ProcurementLink, KindLabel, Diversity, VendorClaim)

from .emails.views import ClientReferenceEmail
from .forms import (VendorInviteForm, VendorLocationForm, VendorRoleForm,
                    VendorRecommendationsForm, VendorAllocationForm,
                    VendorCategoryAllocationForm, VendorCategoryForm,
                    VendorLocationAllocationForm, PortfolioItemForm,
                    VendorServiceAllocationForm, VendorServiceForm,
                    VendorApplicationForm, CertAddForm, InsuranceAddForm,
                    ClientAddForm, ClientConfirmForm, ClientForm,
                    ClientEditForm, VendorIndustryForm, VendorEngageProcess,
                    VendorArchiveForm, VendorProcurement,
                    VendorProcurementDelete, VendorProcurementForm,
                    VendorProcurementAllocationForm, VendorProfileLogoForm,
                    ClientReferenceAddForm, InvoiceForm, InvoiceTotalForm, InvoiceFormSet,
                    InvoiceTotalUrlForm, VendorCustomPrimary,
                    ProcurementLinkForm, VendorStatusChange, VendorDiversitySelect,
                    VendorProfileBrochureForm, ClientQueueForm, VendorClaimForm, ClientReferenceEditForm)

from .filters import VendorFilter
from .tasks import vendor_application_notif, client_add
from .resources import VendorResource


def user_can_vendors(user):
    return user.is_authenticated() and user.has_perm('vendors.edit_vendor')


class VendorRecommendations(ListView):
    model = Vendor
    context_object_name = 'vendors'
    result_type = 'recommendation'
    title = 'Vendor recommendations'
    view_id = 'recommendations'
    template_name = 'vendors/recommendations_list.html'

    def get_queryset(self):
        form = VendorRecommendationsForm(data=self.request.GET)
        form.is_valid()
        return Vendor.get_suggested_vendors(**form.cleaned_data)


class VendorSearch(VendorRecommendations):
    title = None
    view_id = 'search-results'
    result_type = 'search'

    def get_queryset(self):
        term = self.request.GET.get('q', '').strip()
        if term:
            return Vendor.objects.filter(name__icontains=term)
        else:
            return Vendor.objects.none()


class VendorList(ListView):
    model = Vendor
    context_object_name = 'vendors'
    items_per_page = 12

    def get_template_names(self):
        if self.request.is_ajax() and self.request.GET.get('filter', '').strip() == 'yes':
            return 'vendors/list.inc.html'
        return 'vendors/list.new.html'

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        self.tenant = get_current_tenant()
        if user.is_authenticated():
            if not self.request.is_ajax():
                user_search_meta = user.meta.get('last-searched')
                user_search_query = user.meta.get('last-query')
                query_string = '?' + self.request.META.get('QUERY_STRING')
                query_dict = parse_qs(urlparse.urlparse(query_string).query)
                find = query_dict.get('find')
                location = query_dict.get('location')
                if not find:
                    find = []
                if location:
                    for loc in location:
                        find.append('loc-' + loc)
                if find:
                    if user_search_meta and user_search_query:
                        if len(user_search_meta) > 2:
                            user_search_meta.pop(0)
                            user_search_query.pop(0)
                        user.meta['last-searched'].append(find)
                        user.meta['last-query'].append(query_string)
                    else:
                        user.meta['last-searched'] = []
                        user.meta['last-query'] = []
                        user.meta['last-searched'].append(find)
                        user.meta['last-query'].append(query_string)
                    user.save()
        elif not self.tenant.is_public_instance:
            return redirect(reverse('account_login') + '?next=' + self.request.get_full_path())
        return super(VendorList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        joined = self.request.GET.get('joined', None)
        is_filter = self.request.GET.get('filter', None)
        kind = self.request.GET.get('kind', None)
        oh_my = self.request.GET.get('my', None)

        qs = Vendor.objects.prefetch_related('custom_categories', 'locations', 'clients')

        if joined == 'no':
            qs = qs.filter(joined_on__isnull=True)
        elif joined == 'yes':
            qs = qs.filter(joined_on__isnull=False)

        if is_filter != 'yes' and not kind:
            if Vendor().kind_filter_choices:
                qs = qs.filter(kind__in=Vendor().kind_filter_choices)

        return qs.exclude(is_archived=True)

    def get_context_data(self, form=None):
        ctx = super(VendorList, self).get_context_data()

        filtered_vendors = VendorFilter(
            self.request.GET,
            request=self.request,
            queryset=ctx['vendors']
        )

        filterdata = self.request.GET.copy()
        all_vendors = VendorFilter(
            filterdata,
            request=self.request,
            queryset=ctx['vendors']
        )
        ctx['vendors'] = filtered_vendors

        try:
            page = int(self.request.GET.get('page', 1))
        except ValueError:
            page = 1

        slice_start = self.items_per_page * (page - 1)
        slice_end = slice_start + self.items_per_page
        ctx['filter_slice'] = '{}:{}'.format(slice_start, slice_end)

        ctx['vendors_count'] = all_vendors.qs.count()
        ctx['is_last_page'] = ctx['vendors_count'] <= slice_end

        getdata = self.request.GET.copy()
        getdata.pop('organization', None)
        getdata.pop('kind', None)
        users = get_user_model().staffable.order_by('next_available')
        if self.request.user.is_authenticated() and self.request.user.is_vendor:
            users = users.filter(vendor=self.request.user.vendor)

        ctx['Vendor'] = Vendor
        try:
            value = int(self.request.GET.get('kind', ''))
        except (ValueError, TypeError):
            value = None

        ctx['show_open_projects_btn'] = True
        ctx['active_nav_tab'] = 'vendors'
        ctx['kind_labels'] = KindLabel.objects.all()

        ctx['grade_colors'] = {
            'A': 'success', 'B': 'warning',
            'C': 'warning', 'D': 'danger',
            'E': 'danger'
        }

        return ctx

vendor_list_view = VendorList.as_view()


class VendorDetail(DetailView):
    model = Vendor

    def get_template_names(self):
        return 'vendors/details.new.html'

    def dispatch(self, *args, **kwargs):
        self.tenant = get_current_tenant()
        if not self.tenant.is_public_instance and not self.request.user.is_authenticated():
            return redirect(reverse('account_login') + '?next=' + self.request.get_full_path())
        return super(VendorDetail, self).dispatch(*args, **kwargs)

    def get_object(self):
        slug = self.kwargs['slug']
        user = self.request.user

        vendor = get_object_or_404(self.model, slug=slug)

        threshold = now() - timedelta(seconds=900)
        if user.is_authenticated() and not Review.objects.filter(content_object=vendor, created__gt=threshold, anonymous=True).exists():
            PageView.add_view(self.request, vendor)
            track_event('vendors:profile_visit', {
                'vendor_id': vendor.id,
                'vendor': vendor.name,
                'user': self.request.user.username,
                'user_id': self.request.user.id
            })

        for keyword in vendor.get_search_keywords():
            search_news_task.delay(query=keyword)

        return vendor

    def get_context_data(self, *args, **kwargs):
        context = super(VendorDetail, self).get_context_data(*args, **kwargs)

        context['content_type'] = ContentType.objects.get(app_label='vendors', model='vendor').id
        context['procurement_link'] = ProcurementLink.objects.filter(vendor=self.object).first()
        context['service_contacts'] = ServiceVendor.objects.filter(vendor=self.object)

        if self.request.user.is_authenticated() and self.request.user.is_vendor:
            is_admin = False
            if self.request.user.vendor == self.object:
                is_admin = True
            context['is_admin'] = is_admin

        context['accepted_responses'] = self.object.responses.filter(is_accepted=True).distinct('request')
        context['staffed'] = self.object.users.filter(assigned_projects__isnull=False)
        context['vendor_roles'] = VendorRoles.objects.filter(vendor=self.object)
        context['vendor_skills'] = VendorCategories.objects.filter(vendor=self.object)
        if 'show_welcome_banner' in self.request.session:
            context['show_welcome_banner'] = True
            self.request.session.pop('show_welcome_banner')
        if self.object.website:
            context['website'] = urlparse.urlsplit(self.object.website).netloc
        # FIXME
        PRS = ProposedResourceStatus
        context['completed_projects'] = Project.objects.filter(
            proposals__resource__vendor=self.object,
            proposals__status__value=PRS.SUCCESS
        ).distinct()

        context['portfolio'] = (PortfolioItem.objects
                                             .filter(vendor=self.object))
        context['portfolio_projects'] = (
            list(context['portfolio']) +
            list(context['completed_projects'])
        )

        context['diversity_owned'] = self.get_object().diversity\
            .filter(kind=Diversity.KIND_OWNERSHIP)
        context['diversity_employee'] = self.get_object().diversity\
            .filter(kind=Diversity.KIND_EMPLOYEES)

        # ENDFIXME
        sum_industry = 0
        for obj in self.object.vendor_industries.all():

            sum_industry += obj.allocation
        if sum_industry:
            context['industry_progress'] = True
        sum_role = 0
        for obj in self.object.vendor_roles.all():

            sum_role += obj.allocation
        if sum_role:
            context['role_progress'] = True
        sum_skill = 0
        for obj in self.object.vendor_skills.all():
            sum_skill += obj.allocation
        if sum_skill:
            context['skill_progress'] = True

        sum_service = 0
        for obj in self.object.vendor_services.all():
            sum_service += obj.allocation
        if sum_service:
            context['service_progress'] = True

        if self.object.engage_process:
            r = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
            context['engage_process'] = r.sub(r'<a href="\1">\1</a>',
                                              self.object.engage_process)
        context['primary_contact'] = get_object_or_None(get_user_model(),
                                                        email=self.object.email)

        context['activity_log'] = self.object.activity_stream()
        context['views_count'] = PageView.get_unique_views_count(item=self.object)
        last_week = now() - timedelta(days=7)
        views_recent = PageView.objects\
            .filter(item=self.object)\
            .filter(views__0__gte=last_week).distinct('by')

        context['views_recent'] = sorted(list(views_recent),
                                         key=lambda x: x.updated_at, reverse=True)

        context['views_recent_count'] = views_recent.count()

        q = Q(vendors=self.object)
        q = q | Q(categories__in=self.object.categories.values_list('id', flat=True))
        contacts = ProcurementContact.objects.filter(q).values_list('id', flat=True)
        if not contacts:
            contacts = ProcurementContact.objects.filter(always_show=True)

        context['procurement_contacts'] = get_user_model().objects.filter(
            procurement_contacts__in=contacts)

        supplier_contacts = list()
        if context['primary_contact']:
            supplier_contacts.append(context['primary_contact'])
        if self.object.contacts.all():
            supplier_contacts.extend(list(self.object.contacts.all()))

        context['supplier_contacts'] = set(supplier_contacts)

        context['client_references'] = self.object.client_references.exclude(review=None)

        # passing reviews to context: Vendor, Portfolio items and ClientRef
        if self.request.user.is_authenticated() and self.request.user.is_client:
            reviews = list()
            if self.object.reviews.all():
                reviews = list(self.object.reviews.all())
            if self.tenant.is_public_instance:
                client_ref = list(self.object.client_references.exclude(review=None))
                if client_ref:
                    reviews.extend(client_ref)
            project_reviews = list(Review.objects.filter(content_object__in=self.object.portfolio.all()))
            if project_reviews:
                reviews.extend(project_reviews)
            context['review_objects'] = reviews
        else:
            context['review_objects'] = Review.objects.filter(content_object=self.object, vendor_viewable=True)

        if self.request.user.is_authenticated():
            context['vendor_claimed'] = self.object.claims.filter(user=self.request.user).exists()

        return context

vendor_detail_view = VendorDetail.as_view()


def vendor_detail_view_redirect(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    return redirect(vendor.get_absolute_url())


def client_list_redirect(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    primary_service = vendor.get_primary_service()
    if primary_service:
        return redirect('vendors:client_list_new', category=primary_service.category.slug, slug=vendor.slug)
    return redirect('vendors:client_list_new', slug=vendor.slug)


class VendorModalDetail(VendorDetail):
    template_name = 'vendors/modal_details.html'


class VendorInviteView(FormView):
    template_name = 'vendors/invite_vendor.html'
    form_class = VendorInviteForm

    def get_form_kwargs(self):
        kwargs = super(VendorInviteView, self).get_form_kwargs()
        kwargs['is_admin'] = self.request.user.is_superuser
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(VendorInviteView, self).get_context_data()
        if form:
            ctx['form'] = form
        if hasattr(self, 'invite'):
            ctx['invite'] = self.invite
        return ctx

    def get_success_url(self):
        return reverse('vendors:list')

    def form_valid(self, form):
        self.vendor, owner = VendorInvitation.create_with_owner(**form.cleaned_data)
        vendor_invite = VendorInvitation.objects.get_or_create(vendor=self.vendor, owner=owner, user=self.request.user)[0]
        self.invite = vendor_invite.create_invite_email()
        if 'link' not in self.request.POST:
            vendor_invite.send_invite_email(self.invite)
            messages.success(self.request, _('Invitation sent successfully'))
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.success(self.request, _('Invitation link generated'))
            return render(self.request, self.get_template_names(), self.get_context_data(form))
vendor_invite_view = transaction.atomic(VendorInviteView.as_view())


class CreateVendorLocation(CreateView):
    template_name = 'vendors/location_create.html'
    form_class = VendorLocationForm

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(CreateVendorLocation, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateVendorLocation, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['vendor'] = self.vendor
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(CreateVendorLocation, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        ctx['object'] = self.object
        return ctx

    def get_success_url(self):
        return self.vendor.get_absolute_url()

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/partials/location_form.html'
        return self.template_name

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Location added successfully'))
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        else:
            return HttpResponseRedirect(self.get_success_url())


class EditVendorLocation(BaseEditView):
    model_form = VendorLocationForm
    template_name = 'vendors/location_create.html'
    context_variable = 'location'

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(CreateVendorLocation, self).dispatch(*args, **kwargs)

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/partials/location_form.html'
        return self.template_name

    def get_context_data(self, form=None):
        ctx = super(CreateVendorLocation, self).get_context_data()
        ctx['vendor'] = self.vendor
        return ctx

    def get_form_kwargs(self):
        kwargs = super(EditVendorLocation, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_instance(self, *args, **kwargs):
        return get_object_or_404(self.model, id=self.kwargs['loc_pk'])

    def post_delete(self, instance):
        messages.warning(self.request, _('Location {} deleted successfully.'.format(instance.location)))

    def get_success_url(self):
        return self.vendor.get_absolute_url()


class DeleteVendorLocation(DeleteView):
    template_name = 'vendors/confirm_delete_location.html'

    def get_object(self, *args, **kwargs):
        return get_object_or_404(VendorLocation, id=self.kwargs['pk'])

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_location', args=(self.object.vendor.id,))


class CreateVendorRole(CreateView):
    template_name = 'vendors/roles_create.html'
    form_class = VendorRoleForm

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(CreateVendorRole, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateVendorRole, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(CreateVendorRole, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        ctx['object'] = self.object
        return ctx

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_role', args=(self.vendor.id, ))

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/partials/role_form.html'
        return self.template_name

    def form_valid(self, form):
        self.object = form.save(commit=False)
        objects = VendorRoles.objects.filter(vendor=self.vendor)
        allocations = map(lambda l: l.allocation, objects)
        if len(set(allocations)) <= 1:
            new_allocation = 100 / (len(allocations) + 1)
            for obj in objects:
                obj.allocation = new_allocation
                obj.save()
            self.object.allocation = new_allocation
        self.object.save()
        messages.success(self.request, _('Role created successfully'))
        return HttpResponseRedirect(self.get_success_url())


class DeleteVendorRole(DeleteView):
    template_name = 'vendors/confirm_delete_vendor_role.html'

    def get_object(self, *args, **kwargs):
        return get_object_or_404(VendorRoles, id=self.kwargs['pk'])

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_role')


class VendorRoleList(FormView):
    template_name = 'vendors/role_list.html'
    model = VendorRoles

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(VendorRoleList, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_role', args=(self.vendor.id,))

    def get_form_class(self):
        self.roles = list(self.model.objects.filter(vendor=self.vendor))
        fields = {}
        for role in self.roles:
            field = forms.DecimalField(initial=role.allocation, max_value=100,
                                       required=False)
            field.instance = role
            fields[unicode(role.id)] = field
        return type('VendorAllocationForm', (VendorAllocationForm,), fields)

    def get_form(self, form_class=None):
        return self.get_form_class()(roles=self.roles, data=self.request.POST)

    def get_context_data(self, form=None):
        ctx = super(VendorRoleList, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['roles'] = self.roles
        ctx['total_role_allocation'] = sum(map(lambda x: x.allocation, self.roles))
        ctx['total_allocation_incorrect'] = (100 - ctx['total_role_allocation']) != 0
        ctx['vendor'] = self.vendor
        ctx['active_roles'] = True

        if Vendor.EDIT_ROLE in self.vendor.pending_edit_steps:
            self.vendor.pending_edit_steps.remove(Vendor.EDIT_ROLE)
            self.vendor.save()

        return ctx

    def form_invalid(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error, extra_tags="danger")
        if not form.non_field_errors:
            messages.error(self.request, 'Could not save the changes. Please '
                           ' make sure the sum of all weights is 100%',
                           extra_tags="danger")
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, form):
        form.save()
        return super(VendorRoleList, self).form_valid(form)


class CreateVendorSkill(FormView):
    template_name = 'vendors/category_create.html'
    form_class = VendorCategoryForm

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(CreateVendorSkill, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateVendorSkill, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['vendor'] = self.vendor
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(CreateVendorSkill, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        return ctx

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_skill', args=(self.vendor.id,))

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/partials/categories_form.html'
        return self.template_name

    def form_valid(self, form):
        category_ids = form.data.getlist('categories', None)
        previous_ids = [str(x.id) for x in self.vendor.categories.all()]

        deleted_ids = set(previous_ids) - set(category_ids)

        VendorCategories.objects.filter(skill__in=deleted_ids).delete()

        for obj_id in category_ids:
            VendorCategories.objects.get_or_create(vendor=self.vendor,
                                                   skill=Category.objects.get(id=obj_id))
        messages.success(self.request, _('Keywords added successfully'))
        return super(CreateVendorSkill, self).form_valid(form)


class DeleteVendorSkill(DeleteView):
    template_name = 'vendors/confirm_vendor_skill_delete.html'

    def get_object(self, *args, **kwargs):
        return get_object_or_404(VendorCategories, id=self.kwargs['pk'])

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_skill', args=(self.object.vendor.id,))


class DeleteVendorService(DeleteView):
    template_name = 'vendors/confirm_vendor_skill_delete.html'

    def get_object(self, *args, **kwargs):
        return get_object_or_404(VendorServices, id=self.kwargs['pk'])

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_service', args=(self.object.vendor.id,))

    def get_context_data(self, form=None):
        ctx = super(DeleteVendorService, self).get_context_data(*args, **kwargs)
        ctx['is_service'] = True
        return ctx


class VendorSkillList(FormView):
    template_name = 'vendors/category_list.html'
    model = VendorCategories

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(VendorSkillList, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_skill', args=(self.vendor.id,))

    def get_form_class(self):
        self.skills = list(self.model.objects.filter(vendor=self.vendor))
        fields = {}
        for skill in self.skills:
            field = forms.DecimalField(initial=skill.allocation, max_value=100,
                                       required=False)
            field.instance = skill
            fields[unicode(skill.id)] = field
        return type('VendorCategoryAllocationForm', (VendorCategoryAllocationForm,), fields)

    def get_form(self, form_class=None):
        return self.get_form_class()(skills=self.skills, data=self.request.POST)

    def get_context_data(self, form=None):
        ctx = super(VendorSkillList, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['objects'] = self.skills
        ctx['total_role_allocation'] = sum(map(lambda x: x.allocation, self.skills))
        ctx['total_allocation_incorrect'] = (100 - ctx['total_role_allocation']) != 0
        ctx['vendor'] = self.vendor
        ctx['active_categ'] = True

        if Vendor.EDIT_SKILL in self.vendor.pending_edit_steps:
            self.vendor.pending_edit_steps.remove(Vendor.EDIT_SKILL)
            self.vendor.score = self.vendor.score + Vendor.SCORE_SKILL
            self.vendor.save()

        return ctx

    def form_invalid(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error, extra_tags="danger")
        if not form.non_field_errors:
            messages.error(self.request, 'Could not save the changes. Please '
                           ' make sure the sum of all weights is 100%',
                           extra_tags="danger")
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, form):
        form.save()
        return super(VendorSkillList, self).form_valid(form)


class VendorLocationList(FormView):
    template_name = 'vendors/location_list.html'
    model = VendorLocation

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(VendorLocationList, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_location', args=(self.vendor.id,))

    def get_form_class(self):
        self.locations = list(self.model.objects.filter(vendor=self.vendor))
        fields = {}
        for location in self.locations:
            field = forms.IntegerField(initial=location.num_resources, required=False)
            field.instance = location
            fields[unicode(location.id)] = field
        return type('VendorLocationAllocationForm', (VendorLocationAllocationForm,), fields)

    def get_form(self, form_class=None):
        return self.get_form_class()(locations=self.locations, data=self.request.POST)

    def get_context_data(self, form=None):
        ctx = super(VendorLocationList, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['locations'] = self.locations
        ctx['vendor'] = self.vendor
        ctx['active_location'] = True
        if Vendor.EDIT_LOCATION in self.vendor.pending_edit_steps:
            self.vendor.pending_edit_steps.remove(Vendor.EDIT_LOCATION)
            self.vendor.score = self.vendor.score + Vendor.SCORE_LOCATION
            self.vendor.save()
        return ctx

    def form_invalid(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error, extra_tags="danger")
        if not form.non_field_errors:
            messages.error(self.request, 'Could not save the changes. Please '
                           ' make sure the sum of all weights is 100%',
                           extra_tags="danger")
        return HttpResponseRedirect(self.success_url)

    def form_valid(self, form):
        form.save()
        return super(VendorLocationList, self).form_valid(form)


class AddPortfolioItem(CreateView):
    model = PortfolioItem
    template_name = 'vendors/add_portfolio_item.html'
    form_class = PortfolioItemForm

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(AddPortfolioItem, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        ctx = super(AddPortfolioItem, self).get_form_kwargs()
        ctx['request'] = self.request
        ctx['vendor'] = self.vendor
        return ctx

    def get_context_data(self, form=None):
        ctx = super(AddPortfolioItem, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        return ctx

    def get_success_url(self):
        if self.request.is_ajax():
            return reverse('user_setup:setup_step_vendor_projects')
        return self.object.vendor.get_absolute_url()

    def form_valid(self, form):
        self.object = form.save()
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        return HttpResponseRedirect(self.get_success_url())

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/partials/portfolio_form.html'
        return self.template_name


class EditPortfolioItem(UpdateView):
    model = PortfolioItem
    template_name = 'vendors/add_portfolio_item.html'
    form_class = PortfolioItemForm

    def get_form_kwargs(self, *args, **kwargs):
        ctx = super(EditPortfolioItem, self).get_form_kwargs()
        ctx['request'] = self.request
        ctx['vendor'] = self.object.vendor
        return ctx

    def get_context_data(self, form=None):
        ctx = super(EditPortfolioItem, self).get_context_data()
        if form:
            ctx['form'] = form
        return ctx

    def get_success_url(self):
        if self.request.is_ajax():
            return reverse('user_setup:setup_step_vendor_projects', args=(self.object.vendor.id))
        return self.object.vendor.get_absolute_url()

    def form_valid(self, form):
        self.object = form.save()
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        return HttpResponseRedirect(self.get_success_url())

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/partials/edit_portfolio_form.html'
        return self.template_name


class DeletePortfolioItem(DeleteView):
    template_name = 'vendors/confirm_delete_portfolio.html'

    def get_object(self, *args, **kwargs):
        return get_object_or_404(PortfolioItem, id=self.kwargs['pk'])

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_projects', args=(self.object.vendor.id,))


class VendorSkillsModal(ListView):
    model = VendorCategories
    template_name = 'vendors/skill_as_modal.html'
    context_object_name = 'objects'

    def get_queryset(self):
        self.pk = self.kwargs.get('pk')
        return self.model.objects.filter(vendor__id=self.pk)

    def get_context_data(self, form=None):
        context = super(VendorSkillsModal, self).get_context_data()
        context['vendor'] = get_object_or_None(Vendor, pk=self.pk)

        sum_skill = 0
        for obj in context['vendor'].vendor_skills.all():
            sum_skill += obj.allocation
        if sum_skill:
            context['progress'] = True
        return context


class VendorRolesModal(ListView):
    model = VendorRoles
    template_name = 'vendors/role_as_modal.html'
    context_object_name = 'roles'

    def get_queryset(self):
        self.pk = self.kwargs.get('pk')
        return self.model.objects.filter(vendor__id=self.pk)

    def get_context_data(self, form=None):
        context = super(VendorRolesModal, self).get_context_data()
        context['vendor'] = get_object_or_None(Vendor, pk=self.pk)

        sum_role = 0
        for obj in context['vendor'].vendor_roles.all():
            sum_role += obj.allocation
        if sum_role:
            context['role_progress'] = True
        return context


class VendorServicesModal(ListView):
    model = VendorServices
    template_name = 'vendors/skill_as_modal.html'
    context_object_name = 'objects'

    def get_queryset(self):
        self.pk = self.kwargs.get('pk')
        return self.model.objects.filter(vendor__id=self.pk)

    def get_context_data(self, form=None):
        context = super(VendorServicesModal, self).get_context_data()
        context['vendor'] = get_object_or_None(Vendor, pk=self.pk)
        context['is_service'] = True
        sum_service = 0
        for obj in context['vendor'].vendor_services.all():
            sum_service += obj.allocation
        if sum_service:
            context['progress'] = True
        return context


class ContactInformation(TemplateView):
    template_name = 'vendors/partials/contact_info.html'

    def get_context_data(self, form=None):
        ctx = super(ContactInformation, self).get_context_data()
        vendor = ctx['vendor'] = get_object_or_404(Vendor, id=self.kwargs['pk'])
        q = Q(vendors=vendor)
        q = q | Q(categories__in=vendor.categories.values_list('id', flat=True))
        contacts = ProcurementContact.objects.filter(q).values_list('id', flat=True)
        if not contacts:
            contacts = ProcurementContact.objects.filter(always_show=True)

        ctx['procurement_contacts'] = get_user_model().objects.filter(
            procurement_contacts__in=contacts)
        return ctx


class VendorProjectEdit(TemplateView):
    template_name = 'vendors/profile_projects.html'

    def get_context_data(self, *args, **kwargs):
        vendor = get_object_or_404(Vendor, id=self.kwargs['pk'])

        ctx = super(VendorProjectEdit, self).get_context_data(*args, **kwargs)
        ctx['projects'] = PortfolioItem.objects.filter(vendor=vendor)
        ctx['vendor'] = vendor
        ctx['active_projects'] = True

        if Vendor.EDIT_PROJECT in vendor.pending_edit_steps:
            vendor.pending_edit_steps.remove(Vendor.EDIT_PROJECT)
            vendor.score = vendor.score + Vendor.SCORE_PROJECT
            vendor.save()
        return ctx


class PortfolioList(ListView):
    model = PortfolioItem
    context_object_name = 'projects'
    template_name = 'vendors/portfolio.html'

    def get_queryset(self):
        self.vendor = get_object_or_404(Vendor, id=self.kwargs['pk'])
        return PortfolioItem.objects.filter(vendor=self.vendor).order_by('-end_date')

    def get_context_data(self, *args, **kwargs):
        ctx = super(PortfolioList, self).get_context_data(*args, **kwargs)
        completed_projects = Project.objects.filter(
            proposals__resource__vendor=self.vendor,
            proposals__status__value=ProposedResourceStatus.SUCCESS
        ).distinct()
        ctx['vendor'] = self.vendor
        return ctx


class CreateVendorService(CreateView):
    template_name = 'vendors/category_create.html'
    form_class = VendorServiceForm

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(CreateVendorService, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateVendorService, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['vendor'] = self.vendor
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(CreateVendorService, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        ctx['object'] = self.object
        ctx['is_service'] = True
        return ctx

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_service', args=(self.vendor.id,))

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/partials/categories_form.html'
        return self.template_name

    def form_valid(self, form):
        self.object = form.save(commit=False)
        objects = VendorServices.objects.filter(vendor=self.vendor)
        allocations = map(lambda l: l.allocation, objects)
        if len(set(allocations)) <= 1:
            new_allocation = 100 / (len(allocations) + 1)
            for obj in objects:
                obj.allocation = new_allocation
                obj.save()
            self.object.allocation = new_allocation

        self.object.save()
        messages.success(self.request, _('Service created successfully'))
        return HttpResponseRedirect(self.get_success_url())


class VendorServicesList(FormView):
    template_name = 'vendors/category_list.html'
    model = VendorServices

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(VendorServicesList, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_service', args=(self.vendor.id,))

    def get_form_class(self):
        self.services = list(self.model.objects.filter(vendor=self.vendor))
        fields = {}
        for service in self.services:
            field = forms.DecimalField(initial=service.allocation, max_value=100,
                                       required=False)
            field.instance = service
            fields[unicode(service.id)] = field
        return type('VendorServiceAllocationForm', (VendorServiceAllocationForm,), fields)

    def get_form(self, form_class=None):
        return self.get_form_class()(services=self.services, data=self.request.POST)

    def get_context_data(self, form=None):
        ctx = super(VendorServicesList, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['objects'] = self.services
        ctx['total_role_allocation'] = sum(map(lambda x: x.allocation, self.services))
        ctx['total_allocation_incorrect'] = (100 - ctx['total_role_allocation']) != 0
        ctx['is_service'] = True
        ctx['vendor'] = self.vendor
        ctx['active_services'] = True

        if Vendor.EDIT_SERVICE in self.vendor.pending_edit_steps:
            self.vendor.pending_edit_steps.remove(Vendor.EDIT_SERVICE)
            self.vendor.score = self.vendor.score + Vendor.SCORE_SERVICE
            self.vendor.save()

        return ctx

    def form_invalid(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error, extra_tags="danger")
        if not form.non_field_errors:
            messages.error(self.request, 'Could not save the changes. Please '
                           ' make sure the sum of all weights is 100%',
                           extra_tags="danger")
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, form):
        form.save()
        return super(VendorServicesList, self).form_valid(form)


class VendorApplication(CreateView):
    model = Vendor
    template_name = 'vendors/application.html'
    form_class = VendorApplicationForm

    def get_context_data(self, form=None):
        ctx = super(VendorApplication, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['object'] = self.object
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.kind = Vendor.KIND_PROSPECTIVE
        category = form.cleaned_data['custom_categories']
        self.object.save()
        if self.object.client_contact:
            vendor_application_notif.delay(get_current_tenant().id, self.object.id)
        self.object.vendor_invitations.get_or_create()
        email = self.request.POST.get('client_contact')
        if email:
            ReviewToken.objects.create(content_object=self.object, email=email)
        if category:
            VendorCustomKind.objects.create(vendor=self.object, category=category)
        return self.render_to_response(self.get_context_data(form))


def vendor_kind_change(request, pk):
    if request.method == 'POST' and request.user.has_perm('auth.admin'):
        vendor = get_object_or_404(Vendor, id=pk)
        kind = int(request.POST.get('kind'))
        if kind in dict(Vendor.KIND_CHOICES).keys():
            vendor.kind = kind
            vendor.save()
    return HttpResponse()


class CertAdd(CreateView):
    model = CertVerification
    template_name = 'vendors/public/cert_add.html'
    form_class = CertAddForm

    def get_context_data(self, form=None):
        ctx = super(CertAdd, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        ctx['active_certs'] = True
        return ctx

    def get_form_kwargs(self):
        kwargs = super(CertAdd, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['vendor'] = self.vendor
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.vendor = self.vendor
        self.object.created_by = self.request.user
        self.object.save()
        messages.success(
            self.request,
            'Certificate successfully added')
        if self.vendor.EDIT_CERTS in self.vendor.pending_edit_steps:
            self.vendor.pending_edit_steps.remove(self.vendor.EDIT_CERTS)
            self.vendor.score = self.vendor.score + Vendor.SCORE_CERTS
            self.vendor.save(update_fields=['score', 'pending_edit_steps'])
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('vendors:cert_add', args=(self.vendor.id,))

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor, id=self.kwargs['pk'])
        return super(CertAdd, self).dispatch(*args, **kwargs)


class CertConfirm(View):
    template_name = 'vendors/public/cert_confirm.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'object': self.object})

    def post(self, request, *args, **kwargs):
        if request.POST.get('verify'):
            self.object.is_fulfilled = True
            self.object.save()

        return HttpResponseRedirect(self.object.vendor.get_absolute_url())

    def dispatch(self, *args, **kwargs):
        self.object = get_object_or_404(CertVerification, token=self.kwargs['token'])
        if self.object.is_expired:
            raise Http404()
        return super(CertConfirm, self).dispatch(*args, **kwargs)


class DeleteVendorCert(DeleteView):
    template_name = 'vendors/confirm_delete_certification.html'

    def get_object(self, *args, **kwargs):
        return get_object_or_404(CertVerification, id=self.kwargs['pk'])

    def get_success_url(self):
        messages.success(
            self.request,
            'Certificate deleted successfully!')
        return reverse('vendors:cert_add', args=(self.object.vendor.id,))


class InsuranceAdd(CreateView):
    model = InsuranceVerification
    template_name = 'vendors/public/insurance_add.html'
    form_class = InsuranceAddForm

    def get_context_data(self, form=None):
        ctx = super(InsuranceAdd, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        ctx['active_insurances'] = True
        return ctx

    def get_form_kwargs(self):
        kwargs = super(InsuranceAdd, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['vendor'] = self.vendor
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.vendor = self.vendor
        self.object.created_by = self.request.user
        self.object.save()
        messages.success(
            self.request,
            'Insurance successfully added')
        if self.vendor.EDIT_INSURANCE in self.vendor.pending_edit_steps:
            self.vendor.pending_edit_steps.remove(self.vendor.EDIT_INSURANCE)
            self.vendor.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('vendors:insurance_add', args=(self.vendor.id,))

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor, id=self.kwargs['pk'])
        return super(InsuranceAdd, self).dispatch(*args, **kwargs)


class InsuranceConfirm(View):
    template_name = 'vendors/public/insurance_confirm.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'object': self.object})

    def post(self, request, *args, **kwargs):
        if request.POST.get('verify'):
            self.object.is_fulfilled = True
            self.object.save()

        return HttpResponseRedirect(self.object.vendor.get_absolute_url())

    def dispatch(self, *args, **kwargs):
        self.object = get_object_or_404(InsuranceVerification, token=self.kwargs['token'])
        if self.object.is_expired:
            raise Http404()
        return super(InsuranceConfirm, self).dispatch(*args, **kwargs)


class InsuranceDelete(DeleteView):
    template_name = 'vendors/insurance_delete.html'

    def get_object(self, *args, **kwargs):
        return get_object_or_404(InsuranceVerification, id=self.kwargs['pk'])

    def get_success_url(self):
        messages.success(self.request, 'Insurance deleted successfully!')
        return reverse('vendors:insurance_add', args=(self.object.vendor.id,))


class ClientAdd(CreateView):
    model = ClientReference
    template_name = 'vendors/public/client_add.html'
    form_class = ClientAddForm
    form2_class = ClientForm

    def get_context_data(self, form=None):
        ctx = super(ClientAdd, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        ctx['total_clients'] = self.vendor.clients.count()
        ctx['active_clients'] = True
        ctx['result'] = self.result
        if self.result and self.result.website:
            parse = urlparse.urlparse(self.result.website)
            domain = parse.netloc if parse.netloc else parse.path
            ctx['client_domain'] = domain
        if self.request.POST:
            ctx['form2'] = self.form2_class(
                self.request.POST, self.request.FILES,
                prefix='client_form', request=self.request,
                vendor=self.vendor, result=self.result)
        else:
            ctx['form2'] = self.form2_class(
                prefix='client_form', request=self.request,
                vendor=self.vendor, result=self.result)

        return ctx

    def get_form_kwargs(self):
        kwargs = super(ClientAdd, self).get_form_kwargs()
        kwargs['vendor'] = self.vendor
        kwargs['request'] = self.request

        return kwargs

    def get_success_url(self):
        return reverse('vendors:client_added', args=(self.vendor.id, self.object.id))

    @transaction.atomic
    def form_valid(self, form):
        form2 = self.form2_class(
            self.request.POST,
            prefix='client_form', request=self.request,
            vendor=self.vendor, result=self.result)
        if form2.is_valid():
            client = Client.objects.get(pk=str(form2.cleaned_data.get('client')))
        else:
            if self.request.is_ajax():
                response = {
                    "status": "fail",
                }
                response.update(pretty_form_errors(form2))
                return JsonResponse(response, status=400)
            return render(self.request, self.template_name,
                          self.get_context_data(form), status=400)

        self.object = form.save(commit=False)
        if self.vendor.EDIT_CLIENTS in self.vendor.pending_edit_steps:
            self.vendor.pending_edit_steps.remove(self.vendor.EDIT_CLIENTS)
            self.vendor.score = self.vendor.score + Vendor.SCORE_CLIENTS
            self.vendor.save()
        self.object.vendor = self.vendor
        self.object.created_by = self.request.user
        self.object.client = client
        if not self.object.billing_new:
            self.object.billing_new = None

        if not self.object.duration:
            self.object.duration = 1

        self.object.save()
        for user in User.objects.filter(is_superuser=True):
            notify.send(
                self.request.user, verb='added the client', target=self.object, recipient=user)

        if self.request.is_ajax():
            logo = self.object.client.logo
            logo = logo and logo.url or ''
            response = {
                "status": "ok",
                "name": self.object.client.name,
                "logo": logo,
                "reference_id": self.object.id
            }
            return JsonResponse(response, status=200)

        return HttpResponseRedirect(self.get_success_url())

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        client_pk = self.request.GET.get('result')
        self.result = None
        if client_pk:
            self.result = get_object_or_404(Client,
                                        id=client_pk)
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(ClientAdd, self).dispatch(*args, **kwargs)


class ClientAdded(UpdateView):
    template_name = 'vendors/public/client_added.html'
    model = ClientReference
    form_class = ClientReferenceAddForm

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor, id=self.kwargs['pk'])
        self.reference = get_object_or_404(ClientReference, id=self.kwargs['ref_pk'])
        if self.request.GET and 'send_to_self' in self.request.GET:
            ClientReferenceEmail(self.reference, to=(self.request.user.email,)).send()
            messages.success(self.request, _('Invitation successfully sent to self'))
            return redirect(self.get_success_url())

        if not self.request.user.is_superuser and self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(ClientAdded, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_object(self):
        return self.reference

    def get_form_kwargs(self):
        kwargs = super(ClientAdded, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['reference'] = self.reference
        kwargs['vendor'] = self.reference.vendor
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(ClientAdded, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        ctx['reference'] = self.reference
        ctx['total_clients'] = self.vendor.clients.count()
        ctx['active_clients'] = True
        return ctx

    def get_success_url(self):
        return reverse('vendors:client_added', args=(self.vendor.id, self.reference.id))

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.invoice_verification = ('invoice_verification' in self.request.POST)
        self.object.save()


class ClientReferenceUpdate(UpdateView):
    model = ClientReference
    form_class = ClientReferenceAddForm

    def dispatch(self, *args, **kwargs):
        self.reference = get_object_or_404(ClientReference, id=self.kwargs['pk'])
        self.is_valid = False
        return super(ClientReferenceUpdate, self).dispatch(*args, **kwargs)

    def get_object(self):
        return self.reference

    def get_form_kwargs(self):
        kwargs = super(ClientReferenceUpdate, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['reference'] = self.reference
        kwargs['vendor'] = self.reference.vendor
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(ClientReferenceUpdate, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['reference'] = self.reference
        ctx['is_valid'] = self.is_valid
        return ctx

    def get_success_url(self):
        return reverse('vendors:client_added', args=(self.vendor.id, self.reference.id))

    def get_template_names(self):
        return 'vendors/partials/client_reference_confirm.html'

    def form_valid(self, form):
        self.object = form.save()
        self.is_valid = True
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        else:
            return HttpResponseRedirect(self.get_success_url())


def client_invoice_add(request, vendor_pk, reference_pk):
    vendor = get_object_or_404(Vendor, pk=vendor_pk)
    reference = get_object_or_404(ClientReference, pk=reference_pk)

    tenant = get_current_tenant()
    invoice_count = Invoice.objects.filter(reference__vendor=vendor).count()
    if features.premium.is_enabled() and not vendor.premium and invoice_count > tenant.invoice_limit:
        if request.is_ajax():
            template_name = 'vendors/partials/premium_paywall.html'
        else:
            template_name = 'vendors/premium_paywall.html'
        return render(request, template_name, {
            'vendor': vendor,
            'invoice_count': invoice_count,
        })

    if request.method == 'POST':
        form = InvoiceTotalForm(request.POST, request.FILES, instance=reference)
        formset = InvoiceFormSet(request.POST, request.FILES, instance=reference)
        if form.is_valid() and formset.is_valid():
            reference = form.save(commit=False)
            reference.invoice_verification = True
            reference.is_fulfilled = False
            reference.save()
            invoices = formset.save()
            if invoices:
                invoices[0].send_admin_email()
            messages.success(request, 'Invoices uploaded successfully!')
            return redirect('vendors:client_added', vendor.id, reference.id)
        form_url = InvoiceTotalUrlForm(request.POST, request.FILES, instance=reference)
        if form_url.is_valid():
            reference = form_url.save()
            reference.send_admin_email()
            messages.success(request, 'URL verification uploaded successfully!')
            return redirect('vendors:clients_list')
    else:
        form = InvoiceTotalForm(instance=reference)
        formset = InvoiceFormSet(instance=reference)

    if request.is_ajax():
        template_name = 'vendors/partials/client_invoice_add.html'
    else:
        template_name = 'vendors/client_invoice_add.html'
    return render(request, template_name, {
        'form': form,
        'formset': formset,
        'vendor': vendor,
        'reference': reference,
        'invoices': reference.invoices.all(),
    })


class ClientInvoiceAdd(CreateView):
    model = ClientReference
    form_class = InvoiceForm

    def dispatch(self, *args, **kwargs):
        self.is_valid = False
        return super(ClientInvoiceAdd, self).dispatch(*args, **kwargs)

    def get_object(self):
        return self.reference

    def get_context_data(self, form=None):
        ctx = super(ClientInvoiceAdd, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['reference'] = self.reference
        ctx['vendor'] = self.reference.vendor
        ctx['is_valid'] = self.is_valid
        ctx['invoices'] = self.reference.invoices.all()
        return ctx

    def get_success_url(self):
        return reverse('vendors:client_added', args=(self.vendor.id, self.reference.id))

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/partials/client_invoice_add.html'
        return 'vendors/client_invoice_add.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.invoice_verification = True
        self.object.save()

        invoice = Invoice(reference=self.object)
        assert form.cleaned_data['invoice'] is not None
        invoice.invoice = form.cleaned_data['invoice']
        invoice.invoice_amount = form.cleaned_data['invoice_amount']
        invoice.invoice_duration = form.cleaned_data['invoice_duration']
        invoice.save()

        messages.success(self.request, 'Invoice uploaded successfully!')

        self.is_valid = True
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        else:
            return HttpResponseRedirect(self.get_success_url())


@staff_member_required
def client_invoice_verify(request, pk, ref_pk, inv_pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    reference = get_object_or_404(ClientReference, pk=ref_pk)
    invoice = get_object_or_404(Invoice, pk=inv_pk)

    if request.user.is_superuser and request.user.is_client:
        invoice.date_verified = now()
        invoice.save()
        invoice.send_verification_email()
        messages.success(request, 'Invoice verified successfully!')

    if 'next' in request.GET:
        return redirect(request.GET['next'])
    return redirect('vendors:client_view', vendor.slug, reference.id)


@staff_member_required
def client_invoice_edit(request, pk, ref_pk, inv_pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    reference = get_object_or_404(ClientReference, pk=ref_pk)
    invoice = get_object_or_404(Invoice, pk=inv_pk)

    if (request.user.is_superuser and request.user.is_client) or request.user.vendor == vendor:
        if request.method == 'POST':
            form = InvoiceForm(request.POST, instance=invoice)
            if form.is_valid():
                form.save()
                messages.success(request, 'Invoice edited successfully!')
                return redirect('vendors:client_view', vendor.slug, reference.pk)
        else:
            form = InvoiceForm(instance=invoice)

        if request.is_ajax():
            template = 'vendors/partials/client_invoice_edit.html'
        else:
            template = 'vendors/client_invoice_edit.html'
        return render(request, template, locals())


@staff_member_required
def client_invoice_delete(request, pk, ref_pk, inv_pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    reference = get_object_or_404(ClientReference, pk=ref_pk)
    invoice = get_object_or_404(Invoice, pk=inv_pk)

    if (request.user.is_superuser and request.user.is_client) or request.user.vendor == vendor:
        invoice.delete()
        messages.success(request, 'Invoice deleted successfully!')

    if 'next' in request.GET:
        return redirect(request.GET['next'])
    return redirect('vendors:client_view', vendor.slug, reference.id)


@staff_member_required
def client_invoice_approve_all(request, pk, ref_pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    reference = get_object_or_404(ClientReference, pk=ref_pk)

    if request.user.is_superuser and request.user.is_client:
        for invoice in reference.invoices.all():
            invoice.date_verified = now()
            invoice.save()
        if 'declared_value' not in request.POST:
            reference.billing_new = 0
        reference.is_fulfilled = True
        reference.save()
        invoice = reference.invoices.first()
        if invoice:
            invoice.send_verification_email()
        messages.success(request, 'All invoices approved!')

    if 'next' in request.GET:
        return redirect(request.GET['next'])
    return redirect('vendors:client_view', vendor.slug, reference.id)


@staff_member_required
def client_reference_url_verify(request, pk):
    reference = get_object_or_404(ClientReference.objects.select_related('vendor'), pk=pk)
    vendor = reference.vendor

    if request.user.is_allowed_change:
        reference.is_fulfilled = True
        reference.save(update_fields=['is_fulfilled'])
        messages.success(request, 'Client was approved!')
        reference.send_verification_email()

    return redirect('vendors:client_view', vendor.slug, reference.id)


@staff_member_required
def client_reference_url_delete(request, pk):
    reference = get_object_or_404(ClientReference.objects.select_related('vendor'), pk=pk)
    vendor = reference.vendor

    if request.user.is_allowed_change:
        reference.proof_url = ''
        reference.save(update_fields=['proof_url'])
        reference.send_rejection_email()
        messages.success(request, 'URL deleted successfully!')

    return redirect('vendors:client_view', vendor.slug, reference.id)


@staff_member_required
def invoice_list(request, slug=None, ref_pk=None):
    vendor = get_object_or_404(Vendor, slug=slug) if slug else None
    if slug:
        if ref_pk:
            client_refs = ClientReference.objects.filter(vendor__slug=slug, pk=ref_pk).distinct()
        else:
            client_refs = ClientReference.objects.filter(vendor__slug=slug, invoices__isnull=False).distinct()
    else:
        client_refs = ClientReference.objects.filter(invoices__isnull=False, invoices__date_verified__isnull=True).distinct()
    return render(request, 'vendors/invoice_list.html', {
        'vendor': vendor,
        'client_refs': client_refs,
        'next': reverse('vendors:invoice_list'),
    })


class ClientConfirm(UpdateView):
    model = ClientReference
    template_name = 'vendors/public/client_confirm.html'
    form_class = ClientConfirmForm

    def get_context_data(self, form=None):
        ctx = super(ClientConfirm, self).get_context_data()
        if form:
            ctx['form'] = form
        return ctx

    def get_object(self):
        obj = get_object_or_404(self.model, token=self.kwargs['token'])
        if obj.is_expired:
            raise Http404()
        return obj

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.is_fulfilled = True
        self.object.save()

        self.object.client.size = form.cleaned_data['client_size']
        self.object.client.website = form.cleaned_data['client_website']
        new_industries = form.cleaned_data['client_industries']
        old_industries = self.object.client.industries.all()
        for industry in new_industries:
            if industry not in old_industries:
                self.object.client.industries.add(industry)
        self.object.client.save()

        return HttpResponseRedirect(reverse('vendors:client_thanks', args=[self.object.vendor.pk]))


class ClientsList(TemplateView):
    model = ClientReference
    template_name = 'vendors/clients_list.html'

    def get_context_data(self, vendor, **kwargs):
        context = super(ClientsList, self).get_context_data(**kwargs)
        context['vendor'] = vendor
        client_list = self.model.objects.filter(vendor=vendor).select_related(
                'client', 'vendor',
        ).prefetch_related(
                'invoices'
        )
        context['client_list'] = client_list
        context['clients_count'] = client_list.count()
        context['verified_clients_count'] = client_list.filter(is_fulfilled=True).count()

        return context

    def get(self, request, *args, **kwargs):
        vendor = request.user.vendor
        if not vendor:
            raise Http404()
        return super(ClientsList, self).get(request, *args, vendor=vendor, **kwargs)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClientsList, self).dispatch(*args, **kwargs)


class ClientList(ListView):
    model = ClientReference
    template_name = 'vendors/clients.new.html'
    context_object_name = 'references'

    def get_template_names(self):
        return self.template_name

    def get_queryset(self):
        return self.model.objects.filter(vendor=self.vendor)

    def get_context_data(self, form=None):
        ctx = super(ClientList, self).get_context_data()
        ctx['vendor'] = self.vendor
        return ctx

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor, slug=self.kwargs['slug'])
        if (
            self.request.user.is_vendor and
            self.request.user.vendor.id != self.vendor.id and
            self.request.user.vendor.get_primary_service() and
            self.vendor.get_primary_service() and
            self.request.user.vendor.get_primary_service().category == self.vendor.get_primary_service().category
        ):
            raise Http404()

        return super(ClientList, self).dispatch(*args, **kwargs)


class DeleteClient(DeleteView):
    template_name = 'vendors/confirm_delete_client.html'

    def get_object(self, *args, **kwargs):
        return get_object_or_404(ClientReference.objects.select_related('vendor'),
                                 id=self.kwargs['pk'])

    def get_success_url(self):
        messages.success(self.request, 'Client deleted successfully!')
        if self.admin_editing:
            return reverse('vendors:client_list_new', kwargs={'slug': self.vendor_slug})
        return reverse('vendors:clients_list')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        self.admin_editing = False
        reference = self.get_object(*args, **kwargs)

        if user.is_allowed_change and reference.vendor != user.vendor:
            self.admin_editing = True
            self.vendor_slug = reference.vendor.slug
            return super(DeleteClient, self).dispatch(request, *args, **kwargs)
        if user.is_vendor:
            if reference.vendor != user.vendor:
                raise Http404()
            return super(DeleteClient, self).dispatch(request, *args, **kwargs)
        raise Http404()


class ClientRequestResend(UpdateView):
    template_name = 'vendors/public/client_reference_resend.html'
    form_class = ClientAddForm
    model = ClientReference

    def get_context_data(self, form=None):
        ctx = super(ClientRequestResend, self).get_context_data()
        ctx['object'] = self.object
        if form:
            ctx['form'] = form
        return ctx

    def get_form_kwargs(self):
        kwargs = super(ClientRequestResend, self).get_form_kwargs()
        kwargs['vendor'] = self.vendor
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.last_sent = datetime.datetime.now()
        self.object.save()
        client_add.delay(self.object.id, get_current_tenant().id)
        return HttpResponseRedirect(self.get_success_url())

    def get_object(self):
        if self.request.user.is_superuser:
            self.vendor = get_object_or_404(Vendor, id=self.kwargs['pk'])
        else:
            self.vendor = get_object_or_404(Vendor, id=self.kwargs['pk'], users=self.request.user)
        return get_object_or_404(ClientReference, id=self.kwargs['cid'], vendor=self.vendor, is_fulfilled=False)

    def get_success_url(self):
        messages.success(self.request, 'Verification request successfully sent!')
        return reverse('vendors:client_list', args=(self.vendor.id,))


class NewClientAdd(CreateView):
    model = Client
    form_class = ClientEditForm
    template_name = 'vendors/client_add.html'

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor, id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(NewClientAdd, self).dispatch(*args, **kwargs)

    def get_context_data(self, form=None):
        ctx = super(NewClientAdd, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        return ctx

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/public/partials/client_add.html'
        return self.template_name

    def get_success_url(self):
        messages.success(self.request, 'Client details updated')
        return reverse('vendors:client_add', args=(self.vendor.id,)) + '?result=' + str(self.object.id)

    def form_valid(self, form):
        self.object = form.save()
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        return HttpResponseRedirect(self.get_success_url())


@member_required
def view_client(request, slug, ref_pk, category=None):
    vendor = get_object_or_404(Vendor, slug=slug)
    ref = get_object_or_404(ClientReference, vendor__slug=slug, pk=ref_pk)

    return render(request, 'vendors/client.html', {
        'vendor': vendor,
        'ref': ref,
    })


class ClientEdit(UpdateView):
    model = ClientReference
    form_class = ClientReferenceEditForm
    template_name = 'vendors/public/partials/client_edit.html'

    def get_context_data(self, form=None):
        ctx = super(ClientEdit, self).get_context_data()
        ctx['object'] = self.object
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        return ctx

    def get_object(self):
        self.vendor = get_object_or_404(Vendor, id=self.kwargs['pk'])
        obj = get_object_or_404(ClientReference, id=self.kwargs['cid'])
        return obj

    def get_success_url(self):
        messages.success(self.request, 'Client details updated')
        return reverse('vendors:client_view', args=(self.vendor.slug, self.object.id))

    def form_valid(self, form):
        self.object = form.save()
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        return HttpResponseRedirect(self.get_success_url())


class LearnMore(TemplateView):
    template_name = 'vendors/public/learmore.html'


class VendorIndustryList(FormView):
    template_name = 'vendors/industry_list.html'
    model = VendorIndustry

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(VendorIndustryList, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_industries', args=(self.vendor.id,))

    def get_form_class(self):
        self.industries = list(self.model.objects.filter(vendor=self.vendor))
        fields = {}
        for industry in self.industries:
            field = forms.IntegerField(initial=industry.allocation, required=False)
            field.instance = industry
            fields[unicode(industry.id)] = field
        return type('VendorServiceAllocationForm', (VendorServiceAllocationForm,), fields)

    def get_form(self, form_class=None):
        return self.get_form_class()(services=self.industries, data=self.request.POST)

    def get_context_data(self, form=None):
        ctx = super(VendorIndustryList, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['industries'] = self.industries
        ctx['vendor'] = self.vendor
        ctx['active_industry'] = True

        ctx['total_role_allocation'] = sum(map(lambda x: x.allocation, self.industries))
        ctx['total_allocation_incorrect'] = (100 - ctx['total_role_allocation']) != 0

        if Vendor.EDIT_INDUSTRIES in self.vendor.pending_edit_steps:
            self.vendor.pending_edit_steps.remove(Vendor.EDIT_INDUSTRIES)
            self.vendor.score = self.vendor.score + Vendor.SCORE_INDUSTRIES
            self.vendor.save()
        return ctx

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/industry_as_modal.html'
        return self.template_name

    def form_invalid(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error, extra_tags="danger")
        if not form.non_field_errors:
            messages.error(self.request, 'Could not save the changes. Please '
                           ' make sure the sum of all weights is 100%',
                           extra_tags="danger")
        return HttpResponseRedirect(self.success_url)

    def form_valid(self, form):
        form.save()
        return super(VendorIndustryList, self).form_valid(form)


class CreateVendorIndustry(CreateView):
    template_name = 'vendors/industry_create.html'
    form_class = VendorIndustryForm

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(CreateVendorIndustry, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateVendorIndustry, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['vendor'] = self.vendor
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(CreateVendorIndustry, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        ctx['object'] = self.object
        return ctx

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_industries', args=(self.vendor.id,))

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/partials/industry_form.html'
        return self.template_name

    def form_valid(self, form):
        self.object = form.save(commit=False)
        objects = VendorIndustry.objects.filter(vendor=self.vendor)
        allocations = map(lambda l: l.allocation, objects)
        if len(set(allocations)) <= 1:
            new_allocation = 100 / (len(allocations) + 1)
            for obj in objects:
                obj.allocation = new_allocation
                obj.save()
            self.object.allocation = new_allocation

        self.object.save()
        messages.success(self.request, _('Industry created successfully'))
        return HttpResponseRedirect(self.get_success_url())


class DeleteVendorIndustry(DeleteView):
    template_name = 'vendors/confirm_delete_industry.html'

    def get_object(self, *args, **kwargs):
        return get_object_or_404(VendorIndustry, id=self.kwargs['pk'])

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_industries', args=(self.object.vendor.id, ))


class VendorEngageEdit(UpdateView):
    model = Vendor
    form_class = VendorEngageProcess
    template_name = 'vendors/partials/engage_step_edit.html'

    def get_context_data(self, form=None):
        ctx = super(VendorEngageEdit, self).get_context_data()
        if form:
            ctx['form'] = form
        return ctx

    def get_object(self):

        if self.request.user.is_vendor:
            raise Http404()
        obj = get_object_or_404(Vendor, id=self.kwargs['pk'])
        return obj

    def get_success_url(self):
        messages.success(self.request, 'Procurement note updated')
        return self.object.get_absolute_url()

    def form_valid(self, form):
        self.object = form.save()
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        return HttpResponseRedirect(self.get_success_url())


class VendorArchive(UpdateView):
    model = Vendor
    form_class = VendorArchiveForm
    template_name = 'vendors/confirm_archive.html'

    def get_context_data(self, form=None):
        ctx = super(VendorArchive, self).get_context_data()
        if form:
            ctx['form'] = form
        return ctx

    def get_object(self):

        if self.request.user.is_vendor:
            raise Http404()
        obj = get_object_or_404(Vendor, id=self.kwargs['pk'])
        return obj

    def get_success_url(self):
        return reverse('vendors:list')

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())


class ProcurementAdd(FormView):
    form_class = VendorProcurement
    template_name = 'vendors/partials/vendor_procurement_edit.html'

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor, id=kwargs['pk'])
        return super(ProcurementAdd, self).dispatch(*args, **kwargs)

    def get_context_data(self, form=None, proc_obj=None):
        ctx = super(ProcurementAdd, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['proc_obj'] = proc_obj
        ctx['vendor'] = self.vendor
        return ctx

    def get_success_url(self):
        messages.success(self.request, 'Procurement contact added')
        return self.vendor.get_absolute_url()

    def form_valid(self, form):
        user = form.cleaned_data.get('user')
        proc_obj, _ = ProcurementContact.objects.get_or_create(user=user)
        proc_obj.vendors.add(self.vendor)
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form=form, proc_obj=proc_obj))
        return HttpResponseRedirect(self.get_success_url())


class ProcurementDelete(FormView):
    form_class = VendorProcurementDelete
    template_name = 'vendors/confirm_delete_procurement.html'

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=kwargs['pk'])
        self.proc_object = get_object_or_404(ProcurementContact,
                                        id=kwargs['obj_pk'])
        return super(ProcurementDelete, self).dispatch(*args, **kwargs)

    def get_context_data(self, form=None):
        ctx = super(ProcurementDelete, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['proc_obj'] = self.proc_object
        ctx['vendor'] = self.vendor
        return ctx

    def get_success_url(self):
        messages.success(self.request, 'Procurement contact removed')
        return reverse('user_setup:setup_step_vendor_profile', args=(self.vendor.id,))

    def form_valid(self, form):
        self.proc_object.vendors.remove(self.vendor)
        return HttpResponseRedirect(self.get_success_url())


def vendor_export(request):
    if not request.user.is_procurement:
        raise Http404()
    xlsx_data = VendorResource().export().xlsx
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=data.xlsx'
    response.write(xlsx_data)
    return response


class ProcurementCategoryList(FormView):
    template_name = 'vendors/procurement_categ_list.html'
    model = VendorCustomKind

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor, id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(ProcurementCategoryList, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('vendors:procurement:list', args=(self.vendor.id,))

    def get_form_class(self):
        custom_kind = CategoryType.objects.filter(vendor_editable=False).first()
        self.categories = list(self.model.objects.filter(vendor=self.vendor,
                                                         category__custom_kind=custom_kind))
        fields = {}
        for categ in self.categories:
            field = forms.DecimalField(initial=categ.allocation, max_value=100,
                                       required=False)
            field.instance = categ
            fields[unicode(categ.id)] = field
        return type('VendorProcurementAllocationForm', (VendorProcurementAllocationForm,), fields)

    def get_form(self, form_class=None):
        return self.get_form_class()(categories=self.categories, data=self.request.POST)

    def get_context_data(self, form=None):
        ctx = super(ProcurementCategoryList, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['objects'] = self.categories
        ctx['total_role_allocation'] = sum(map(lambda x: x.allocation, self.categories))
        ctx['total_allocation_incorrect'] = (100 - ctx['total_role_allocation']) != 0
        ctx['is_service'] = True
        ctx['vendor'] = self.vendor
        ctx['active_procurement'] = True

        if Vendor.EDIT_SERVICE in self.vendor.pending_edit_steps:
            self.vendor.pending_edit_steps.remove(Vendor.EDIT_SERVICE)
            self.vendor.score = self.vendor.score + Vendor.SCORE_SERVICE
            self.vendor.save()

        return ctx

    def form_invalid(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error, extra_tags="danger")
        if not form.non_field_errors:
            messages.error(self.request, 'Could not save the changes. Please '
                           ' make sure the sum of all weights is 100%',
                           extra_tags="danger")
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, form):
        form.save()
        return super(ProcurementCategoryList, self).form_valid(form)


class CreateProcurementCateg(CreateView):
    template_name = 'vendors/procurement_create.html'
    form_class = VendorProcurementForm

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
            raise Http404()
        return super(CreateProcurementCateg, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateProcurementCateg, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['vendor'] = self.vendor
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(CreateProcurementCateg, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.vendor
        ctx['object'] = self.object
        ctx['is_service'] = True
        return ctx

    def get_success_url(self):
        return reverse('vendors:procurement:list', args=(self.vendor.id,))

    def get_template_names(self):
        if self.request.is_ajax():
            return 'vendors/partials/procurement_form.html'
        return self.template_name

    def form_valid(self, form):
        self.object = form.save(commit=False)
        custom_kind = CategoryType.objects.filter(vendor_editable=False).first()
        objects = VendorCustomKind.objects.filter(category__custom_kind=custom_kind,
                                                  vendor=self.vendor)
        allocations = map(lambda l: l.allocation, objects)
        if len(set(allocations)) <= 1:
            new_allocation = 100 / (len(allocations) + 1)
            for obj in objects:
                obj.allocation = new_allocation
                obj.save()
            self.object.allocation = new_allocation

        if not objects.exists():
            self.object.primary = True
        self.object.save()
        messages.success(self.request, _('Service created successfully'))
        return HttpResponseRedirect(self.get_success_url())


class DeleteVendorProcurement(DeleteView):
    template_name = 'vendors/confirm_vendor_procurement_delete.html'

    def get_object(self, *args, **kwargs):
        custom_kind = CategoryType.objects.filter(vendor_editable=False).first()
        return get_object_or_404(VendorCustomKind,
                                 id=self.kwargs['pk'],
                                 category__custom_kind=custom_kind)

    def get_success_url(self):
        return reverse('vendors:procurement:list', args=(self.object.vendor.id,))


class ClientConfirmThanks(CreateView):
    template_name = 'vendors/public/client_verification_thank.html'
    form_class = ClientQueueForm

    def get_success_url(self):
        return reverse('vendors:client_thanks', args=[self.kwargs['pk']])

    def get_context_data(self, form=None):
        ctx = super(ClientConfirmThanks, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = get_object_or_404(Vendor, pk=self.kwargs['pk'])
        return ctx

    def form_valid(self, form):
        resp = super(ClientConfirmThanks, self).form_valid(form)
        messages.success(self.request, _('Information saved! We\'ll get back to you shortly'))
        return resp


class VendorProfileLogoEdit(UpdateView):
    model = Vendor
    template_name = 'vendors/partials/logo_edit.html'
    form_class = VendorProfileLogoForm

    def get_context_data(self, form=None):
        ctx = super(VendorProfileLogoEdit, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.object
        return ctx

    def get_object(self):
        return get_object_or_404(self.model,
                                 id=int(self.kwargs['pk']))

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_media',
                       args=(self.object.id,))

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())


class VendorProfileBrochureEdit(UpdateView):
    model = Vendor
    template_name = 'vendors/partials/brochure_edit.html'
    form_class = VendorProfileBrochureForm

    def get_context_data(self, form=None):
        ctx = super(VendorProfileBrochureEdit, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['vendor'] = self.object
        return ctx

    def get_object(self):
        return get_object_or_404(self.model,
                                 id=int(self.kwargs['pk']))

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_media',
                       args=(self.object.id,))

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('Brochure updated successfully'))
        return HttpResponseRedirect(self.get_success_url())


class VendorCustomPrimary(UpdateView):
    model = VendorCustomKind
    form_class = VendorCustomPrimary
    template_name = 'vendors/service_primary.html'

    def get_edit_step(self):
        return self.edit_step

    def get_object(self, *args, **kwargs):
        pk = self.kwargs['pk']
        self.is_valid = None
        vendor_custom = get_object_or_404(VendorCustomKind, pk=pk)
        return vendor_custom

    def get_context_data(self, form=None):
        ctx = super(VendorCustomPrimary, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['is_valid'] = self.is_valid
        return ctx

    def form_valid(self, form):
        prim_objs = VendorCustomKind.objects.filter(vendor=self.object.vendor, primary=True)
        prev_primary = prim_objs.first()
        if prev_primary:
            prev_primary.primary = False # hack: to fire the post save signal.
            prev_primary.save()
            if prim_objs.count() > 1:
                prim_objs.update(primary=False)
        self.object = form.save()
        self.is_valid = True
        messages.success(self.request, _('Primary service changed successfully'))
        return self.render_to_response(self.get_context_data(form))


class VendorProcurementLink(FormView):
    model = ProcurementLink
    form_class = ProcurementLinkForm
    template_name = 'vendors/procurement_link.html'

    def dispatch(self, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor,
                                        id=self.kwargs['pk'])
        self.object = get_object_or_None(ProcurementLink,
                                         vendor=self.vendor)
        return super(VendorProcurementLink, self).dispatch(*args, **kwargs)

    def get_context_data(self, form=None):
        context = super(VendorProcurementLink, self).get_context_data()
        context['form'] = form
        context['vendor'] = self.vendor
        return context

    def get_success_url(self):
        return self.vendor.get_absolute_url()

    def get_initial(self):
        if self.object is not None:
            return {
                'instance': self.object,
            }
        else:
            return {}

    def get_form_kwargs(self, *args, **kwargs):
        kw = super(VendorProcurementLink, self).get_form_kwargs(*args, **kwargs)
        if self.object:
            kw['instance'] = self.object
        return kw

    def post(self, *args, **kwargs):
        form = self.get_form(self.get_form_class())
        if form.is_valid():
            obj = form.save(commit=False)
            obj.vendor = self.vendor
            obj.save()
            return HttpResponseRedirect(self.vendor.get_absolute_url())
        else:
            return self.form_invalid(form)


class VendorReviews(TemplateView):
    model = Vendor
    template_name = 'vendors/partials/reviews.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(VendorReviews, self).get_context_data(*args, **kwargs)
        ctx['vendor'] = self.get_object()

        ctx['items'] = []
        for qpr in []:  # qprs:
            reviews = [r.calculate_score() for r in ctx['vendor'].reviews.filter(created__lt=qpr.created)]
            review_score = sum(reviews) / (len(reviews) or 1)
            ctx['items'].append({
                'qpr': qpr,
                'score': ((qpr.get_score() + review_score) / 2) if review_score else qpr.get_score(),
                'review_score': review_score
            })

        return ctx

    def get_object(self):
        if self.request.user.is_vendor:
            return self.request.user.vendor
        return get_object_or_404(self.model,
                                 id=int(self.kwargs['pk']))


class VendorStatusUpdate(UpdateView):
    model = Vendor
    form_class = VendorStatusChange
    template_name = 'vendors/update_status.html'

    def get_object(self, *args, **kwargs):
        pk = self.kwargs['pk']
        self.is_valid = None
        vendor = get_object_or_404(Vendor, pk=pk)
        return vendor

    def get_context_data(self, form=None):
        ctx = super(VendorStatusUpdate, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['is_valid'] = self.is_valid
        return ctx

    def get_form_kwargs(self, *args, **kwargs):
        kw = super(VendorStatusUpdate, self).get_form_kwargs(*args, **kwargs)
        kw['instance'] = self.object
        return kw

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        self.object = form.save()
        self.is_valid = True
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        else:
            return HttpResponseRedirect(self.get_success_url())


class DiversityList(TemplateView):
    model = Vendor
    template_name = 'vendors/diversity_form.html'

    def get_context_data(self, form=None):
        ctx = super(DiversityList, self).get_context_data()
        ctx['vendor'] = self.get_object()

        ctx['diversity_owned'] = self.get_object().diversity.filter(kind=Diversity.KIND_OWNERSHIP)
        ctx['diversity_owned_options'] = Diversity.objects.filter(kind=Diversity.KIND_OWNERSHIP)
        ctx['diversity_employee_options'] = Diversity.objects.filter(kind=Diversity.KIND_EMPLOYEES)
        ctx['diversity_employee'] = self.get_object().diversity.filter(kind=Diversity.KIND_EMPLOYEES)
        ctx['kind_ownership'] = Diversity.KIND_OWNERSHIP
        ctx['kind_employees'] = Diversity.KIND_EMPLOYEES
        return ctx

    def get_object(self):
        if self.request.user.is_vendor:
            return self.request.user.vendor
        return get_object_or_404(self.model,
                                 id=int(self.kwargs['pk']))


# class CreateDiversityObj(CreateView):
#     form_class = VendorDiversityForm

#     def dispatch(self, *args, **kwargs):
#         self.vendor = get_object_or_404(Vendor,
#                                         id=self.kwargs['pk'])
#         self.kind = self.kwargs['kind']
#         if self.request.user.is_vendor and self.request.user.vendor.id != self.vendor.id:
#             raise Http404()
#         return super(CreateDiversityObj, self).dispatch(*args, **kwargs)

#     def get_form_kwargs(self):
#         kwargs = super(CreateDiversityObj, self).get_form_kwargs()
#         kwargs['request'] = self.request
#         kwargs['vendor'] = self.vendor
#         return kwargs

#     def get_context_data(self, form=None):
#         ctx = super(CreateDiversityObj, self).get_context_data()
#         if form:
#             ctx['form'] = form
#         ctx['vendor'] = self.vendor
#         ctx['object'] = self.object
#         ctx['diversity_kind'] = self.kind
#         return ctx

#     def get_success_url(self):
#         return reverse('vendors:diversity:list', args=(self.vendor.id,))

#     def get_template_names(self):
#         return 'vendors/partials/diversity_create.html'

#     def form_valid(self, form):
#         self.object = form.save(commit=False)
#         self.object.kind = self.kind
#         self.object.save()
#         messages.success(self.request, _('Diversity information added successfully'))
#         return HttpResponseRedirect(self.get_success_url())

class VendorDiversitySelect(UpdateView):
    model = Vendor
    form_class = VendorDiversitySelect
    template_name = 'vendors/partials/diversity_create.html'

    def get_edit_step(self):
        return self.edit_step

    def get_object(self, *args, **kwargs):
        pk = self.kwargs['pk']
        self.kind = self.kwargs['kind']
        self.is_valid = None
        vendor = get_object_or_404(Vendor, pk=pk)
        return vendor

    def get_success_url(self):
        return reverse('vendors:diversity:list',
                       args=(self.object.id,))

    def get_form_kwargs(self):
        kwargs = super(VendorDiversitySelect, self).get_form_kwargs()
        kwargs['kind'] = self.kind
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(VendorDiversitySelect, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['is_valid'] = self.is_valid
        ctx['diversity_kind'] = self.kind
        return ctx

    def form_valid(self, form):
        diversity_objs =  list(self.object.diversity.exclude(kind=self.kind))
        self.object = form.save()
        for obj in diversity_objs:
            self.object.diversity.add(obj)
        self.is_valid = True
        messages.success(self.request, _('Diversity information updated successfully'))
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        else:
            return HttpResponseRedirect(self.get_success_url())


class VendorDiversityUpdate(View):
    def post(self, request, **kwargs):

        diversity = get_object_or_404(Diversity, pk=kwargs.get('object_pk'))
        vendor = get_object_or_404(Vendor, pk=kwargs.get('pk'))
        checked = request.POST.get('checked')
        if checked == 'true':
            vendor.diversity.add(diversity.id)
        else:
            vendor.diversity.remove(diversity.id)
        return HttpResponse()


class VendorPublicList(ListView):
    model = Vendor
    context_object_name = 'vendors'
    template_name = 'vendors/public_list.html'
    items_per_page = 12

    def dispatch(self, *args, **kwargs):
        tenant = get_current_tenant()
        if not tenant.is_public_instance:
            raise Http404()
        return super(VendorPublicList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        joined = self.request.GET.get('joined', None)
        is_filter = self.request.GET.get('filter', None)
        kind = self.request.GET.get('kind', None)

        qs = Vendor.objects.all()
        qs = qs.exclude(kind=Vendor.KIND_PROSPECTIVE)
        return qs.exclude(is_archived=True)

vendor_public_list_view = VendorPublicList.as_view()


def claim_vendor(request, slug):
    vendor = get_object_or_404(Vendor, slug=slug)
    user = request.user if request.user.is_authenticated() else None

    if request.method == 'POST':
        form = VendorClaimForm(request.POST, user=user)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.user = user
            claim.vendor = vendor
            claim.save()
            messages.success(request, _('Claim submitted for vendor {}'.format(vendor)))
            return redirect('vendors:detail_new', vendor.slug)
    else:
        form = VendorClaimForm(user=user)

    if request.is_ajax():
        template_name = 'vendors/claim_vendor.inc.html'
    else:
        template_name = 'vendors/claim_vendor.html'
    return render(request, template_name, {
        'vendor': vendor,
        'user': user,
        'form': form,
    })


@staff_member_required
def vendor_claims(request):
    claims = VendorClaim.objects.all()
    return render(request, 'vendors/vendor_claims.html', {'claims': claims})


@staff_member_required
def vendor_claim_approve(request, pk):
    claim = VendorClaim.objects.get(pk=pk)
    if request.user.is_superuser and request.user.is_client:
        claim.approved = True
        claim.save()
        invite = claim.create_user_and_invite()
        claim.vendor.users.add(claim.user)
        claim.user.vendor = claim.vendor
        if not claim.user.is_superuser:
            claim.user.kind = User.KIND_VENDOR
        claim.user.save()
        claim.send_approved_email(invite)
        messages.success(request, _('Claim approved for vendor {}'.format(claim.vendor)))
    return redirect('vendors:vendor_claims')


@staff_member_required
def vendor_claim_reject(request, pk):
    claim = VendorClaim.objects.get(pk=pk)
    if request.user.is_superuser and request.user.is_client:
        claim.approved = False
        claim.save()
        claim.send_rejected_email()
        messages.success(request, _('Claim rejected for vendor {}'.format(claim.vendor)))
    return redirect('vendors:vendor_claims')


@member_required
def shortlist(request):
    return render(request, 'vendors/shortlist.html')


@require_POST
@csrf_exempt
@member_required
def shortlist_add(request, slug):
    vendor = get_object_or_404(Vendor, slug=slug)
    cart = Cart(request.session)
    cart.add(vendor, price=0)
    if request.is_ajax():
        return JsonResponse({'shortlisted': True, 'count': cart.count})
    messages.success(request, _('Vendor added to shortlist'))
    return redirect('vendors:shortlist')


@require_POST
@csrf_exempt
@member_required
def shortlist_remove(request, slug):
    vendor = get_object_or_404(Vendor, slug=slug)
    cart = Cart(request.session)
    cart.remove(vendor)
    if request.is_ajax():
        return JsonResponse({'shortlisted': False, 'count': cart.count})
    messages.success(request, _('Vendor removed from shortlist'))
    return redirect('vendors:shortlist')
