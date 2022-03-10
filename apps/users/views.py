from datetime import timedelta

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction, connection
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.http.response import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.edit import View, CreateView, DeleteView, UpdateView, FormView
from django.views.generic.list import ListView
from annoying.functions import get_object_or_None
from avatar.forms import UploadAvatarForm
from avatar.models import Avatar
from avatar.signals import avatar_updated
from avatar.views import _get_avatars
from braces.views import JSONResponseMixin
from urlobject import URLObject

from med_social.constants import OnboardingConstantsMixin as ONB
from med_social.utils import this_week, get_week_from_date
from med_social.utils import get_current_tenant, get_absolute_url
from med_social.decorators import member_required, restriction_exempt, vendor_required
from med_social.views.base import BaseEditView
from projects.models import ProposedResource, ProposedResourceStatus, Project, StaffingRequest
from activity.models import Action
from reviews.models import Review
from vendors.models import Vendor
from projects.forms import ProjectInviteForm
from vendors.forms import VendorLocationForm, VendorProfileForm, VendorMediaForm
from .forms import (UserInviteForm, UserPermissionForm, UserProfileForm, UserSummaryForm, VendorBasicForm,
                    VendorDetailForm, VendorWebForm, AllocationForm, NotificationsForm, PasswordSetForm,
                    UserSignupForm, UserResendInvite, NotificationSettingsForm)
from .filters import UserFilter
from .models import UserInvitation, SignupToken
from .tasks import user_invite, signup_task
from .utils import generate_unique_username


class MarkNotifsRead(JSONResponseMixin, FormView):
    form_class = NotificationsForm

    def render_to_response(self, ctx):
        return self.render_json_response({})

    def get_form_kwargs(self):
        kwargs = super(MarkNotifsRead, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['data'] = {'notifications': self.request.POST.getlist('notifications')}
        return kwargs

    def form_invalid(self, form):
        return self.render_json_response({
            'success': True,
            'unread_count': self.request.user.notifications.filter(unread=True).count()
        })

    def form_valid(self, form):
        notifications = form.cleaned_data['notifications']
        notifications.update(unread=False)
        return self.render_json_response({
            'success': True,
            'unread_count': self.request.user.notifications
            .filter(unread=True).count()
        })
mark_notifs_read = member_required(MarkNotifsRead.as_view())


class BaseNotificationsView(TemplateView):
    template_name = 'notifications/list.html'

    def get_context_data(self, **kwargs):
        ctx = super(BaseNotificationsView, self).get_context_data(**kwargs)
        notifs = self.get_notifs()
        paginator = Paginator(notifs, 16)
        page = self.request.GET.get('p')
        try:
            notifs_list = paginator.page(page)
        except PageNotAnInteger:
            notifs_list = paginator.page(1)
        except EmptyPage:
            notifs_list = paginator.page(paginator.num_pages)
        ctx['notifications'] = notifs_list
        return ctx


class AllNotifications(BaseNotificationsView):
    page_title = 'All Notifications'

    def get_notifs(self):
        return self.request.user.notifications.all().order_by('-timestamp')
all_notifications = member_required(AllNotifications.as_view())


class ReadNotifications(BaseNotificationsView):
    page_title = 'Read Notifications'

    def get_notifs(self):
        return self.request.user.notifications.read().order_by('-timestamp')
read_notifications = member_required(ReadNotifications.as_view())


class UnreadNotifications(BaseNotificationsView):
    page_title = 'Unread Notifications'

    def get_notifs(self):
        return self.request.user.notifications.unread().order_by('-timestamp')
unread_notifications = member_required(UnreadNotifications.as_view())


class AddAllocationView(CreateView):
    model = ProposedResource
    form_class = AllocationForm
    template_name = 'users/allocation_form.html'

    def action_url(self):
        return reverse('users:add_allocation', args=(self.kwargs['username'],))

    def dispatch(self, request, username, pk=None):
        user = get_object_or_404(get_user_model(), username=username)
        if not user == self.request.user:
            raise Http404()
        self.target_user = user
        self.changed_by = self.request.user
        self.created_by = self.request.user
        return super(AddAllocationView, self).dispatch(request, username)

    def get_success_url(self):
        return reverse('users:profile', args=(self.target_user.username,))

    def get_form_kwargs(self):
        kwargs = super(AddAllocationView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['resource'] = self.target_user
        kwargs['changed_by'] = self.changed_by
        kwargs['created_by'] = self.created_by
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(AddAllocationView, self).get_context_data()
        if form:ctx['form'] = form
        ctx['target_user'] = self.target_user
        return ctx
add_allocation = transaction.atomic(
    member_required(AddAllocationView.as_view()))


class EditAllocationView(UpdateView):
    model = ProposedResource
    form_class = AllocationForm
    template_name = 'users/allocation_form.html'

    def action_url(self):
        return reverse('users:edit_allocation', args=(self.kwargs['username'],
                                                      self.kwargs['pk']))

    def dispatch(self, request, username, pk=None):
        user = get_object_or_404(get_user_model(), username=username)
        if not user == self.request.user:
            raise Http404()
        self.target_user = user
        self.changed_by = self.request.user
        self.created_by = self.request.user
        return super(EditAllocationView, self).dispatch(request, username)

    def get_context_data(self, form=None):
        ctx = super(EditAllocationView, self).get_context_data()
        if form:ctx['form'] = form
        ctx['target_user'] = self.target_user
        return ctx

    def get_success_url(self):
        return reverse('users:profile', args=(self.target_user.username,))

    def get_form_kwargs(self):
        kwargs = super(EditAllocationView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['resource'] = self.target_user
        kwargs['changed_by'] = self.changed_by
        kwargs['created_by'] = self.created_by
        return kwargs

    def get_object(self, *args, **kwargs):
        return get_object_or_404(ProposedResource, pk=self.kwargs['pk'],
                                 resource=self.request.user)
edit_allocation = transaction.atomic(
    member_required(EditAllocationView.as_view()))


class UserInviteView(CreateView):
    form_class = UserInviteForm
    invited = False

    @property
    def is_pjax(self):
        return 'HTTP_X_PJAX' in self.request.META

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.is_iframed = self.request.GET.get('iframed', '').strip() == 'yes'
        self.vendor_id = self.request.GET.get('vendor_id', '').strip()
        if self.vendor_id:
            self.vendor = get_object_or_None(Vendor, id=self.vendor_id)
        return super(UserInviteView, self).dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.is_iframed:
            if self.object:
                return 'users/ajax_result.html'
            return 'users/invite_form.html'
        if self.request.is_ajax() and not self.is_pjax:
            return 'users/invite_form_ajax.html'
        else:
            return 'users/invite.html'

    def get_context_data(self, form=None, success=False):
        ctx = super(UserInviteView, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['object'] = self.object
        ctx['success'] = success
        ctx['invited'] = self.invited
        if self.vendor_id and self.vendor:
            ctx['vendor'] = self.vendor
        if self.is_iframed:
            ctx['iframed'] = True
        return ctx

    def render_to_response(self, context_data, *args, **kwargs):
        response = super(UserInviteView, self).render_to_response(
            context_data, *args, **kwargs)
        response['X-Form-Valid'] = context_data.get('success', False)
        return response

    def get_form_kwargs(self):
        kwargs = super(UserInviteView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['password'] = self.generate_password()
        email = self.request.POST.get('email', '')
        user = get_object_or_None(get_user_model(), email=email)
        if user:
            kwargs['instance'] = user
        if self.vendor_id and self.vendor:
            kwargs['vendor'] = self.vendor
        return kwargs

    def get_success_url(self):
        return self.object.get_absolute_url()

    def generate_password(self):
        return get_user_model().objects.make_random_password()

    def send_invitation(self, user, password=None):
        expires_at = now() + timedelta(days=7)
        tenant = connection.get_tenant()
        invitation, created = user.invitations.get_or_create(
            sender=self.request.user, receiver=user, defaults={
                'expires_at': expires_at
            })
        invitation.expires_at = expires_at
        invitation.save()
        user_invite.delay(tenant_id=tenant.id,
                          invite_id=invitation.id,
                          password=password,
                          message=None)
        self.invited = True
        messages.success(self.request, _('Invitation sent successfully'))

    def form_valid(self, form):
        self.object = user = form.save()
        if form.cleaned_data['invite']:
            password = None
            if not user.has_joined:
                password = form.password
                user.set_password(form.password)
                user.save()
                self.object = user
            self.send_invitation(self.object, password)
        ajax_or_iframe = self.request.is_ajax() or self.is_iframed
        is_pjax = 'HTTP_X_PJAX' in self.request.META
        if ajax_or_iframe:
            return self.render_to_response(self.get_context_data(
                form=form, success=True))
        else:
            return HttpResponseRedirect(self.get_success_url())

user_invite_view = transaction.atomic(UserInviteView.as_view())


class UserDirectInviteView(UserInviteView):
    def post(self, request, pk):
        user = request.user
        self.object = get_object_or_404(get_user_model(),
                                        pk=self.kwargs['pk'])
        if user.is_vendor:
            self.object.groups.add(user.vendor.get_users_group())
        elif user.is_client:
            self.object.groups.add(*Group.objects.filter(
                vendor=None, kind=Group.DEFAULT_USER))

        password = None
        if not self.object.has_joined:
            password = self.generate_password()
            self.object.set_password(password)
            self.object.save()
        self.send_invitation(self.object, password)
        return HttpResponseRedirect(self.get_success_url())

user_direct_invite_view = transaction.atomic(
    UserDirectInviteView.as_view())


class UserResendInvite(FormView):
    form_class = UserResendInvite
    template_name = 'users/invite_resend.html'

    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        self.object = get_object_or_404(get_user_model(),
                                        pk=self.kwargs['pk'])
        return super(UserResendInvite, self).dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.request.is_ajax():
            return 'users/resend_invite_form_ajax.html'
        return self.template_name

    def get_form_kwargs(self):
        kwargs = super(UserResendInvite, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['recipient'] = self.object
        return kwargs

    def get_context_data(self, form=None):
        ctx = super(UserResendInvite, self).get_context_data()
        ctx['object'] = self.object
        if form:ctx['form'] = form
        return ctx

    def get_success_url(self):
        return self.object.get_absolute_url()

    def generate_password(self):
        return get_user_model().objects.make_random_password()

    def send_invitation(self, user, message, password=None):
        expires_at = now() + timedelta(days=7)
        tenant = connection.get_tenant()
        url = ''.join([settings.DEFAULT_HTTP_PROTOCOL, tenant.domain_url])

        invitation, created = user.invitations.get_or_create(
            sender=self.request.user, receiver=user, defaults={
                'expires_at': expires_at
            })
        invitation.expires_at = expires_at
        invitation.save()
        message = message.replace('<<signup_url>>', ''.join([url, invitation.get_absolute_url()]))
        user_invite.delay(tenant_id=tenant.id,
                          invite_id=invitation.id,
                          password=password,
                          message=message)
        self.invited = True
        messages.success(self.request, _('Invitation sent successfully'))

    def form_valid(self, form):
        message = form.cleaned_data.get('message')
        if self.user.is_vendor:
            self.object.groups.add(self.user.vendor.get_users_group())
        elif self.user.is_client:
            self.object.groups.add(*Group.objects.filter(
                vendor=None, kind=Group.DEFAULT_USER))

        password = None
        if not self.object.has_joined:
            password = self.generate_password()
            self.object.set_password(password)
            self.object.save()
        self.send_invitation(self.object, message, password)
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        return HttpResponseRedirect(self.get_success_url())

user_resend_invite_view = transaction.atomic(
    UserResendInvite.as_view())


class ProfileDetails(DetailView):
    model = get_user_model()
    template_name = 'users/profile.html'

    def get_context_data(self, object):
        ctx = super(ProfileDetails, self).get_context_data()
        ctx['object'] = object

        PRS = ProposedResourceStatus
        ctx['completed_projects'] = Project.objects.filter(
            proposals__resource=self.object,
            proposals__status__value=PRS.SUCCESS).distinct()

        ctx['reviews'] = object.get_all_reviews()
        ctx['reviews_count'] = ctx['reviews'].filter(posted_by=object).count()
        if self.request.user.is_client:
            ctx['matching_requests'] = StaffingRequest.staffing.filter(
                categories__in=object.categories.values_list(
                    'id', flat=True)).exclude(proposed__resource=object
                                              ).distinct()
        return ctx

    def get_object(self):
        return get_object_or_404(self.model,
                                 username=self.kwargs['username'].lower())


class ProfileModalDetails(DetailView):
    model = get_user_model()
    template_name = 'users/profile_modal_body.html'

    def get_object(self):
        return get_object_or_404(self.model, username=self.kwargs['username'])

    def get(self, request, username):
        if not request.is_ajax():
            return HttpResponseRedirect(reverse('users:profile',
                                                args=(username,)))
        return super(ProfileModalDetails, self).get(request, username)

    def get_context_data(self, object):
        ctx = super(ProfileModalDetails, self).get_context_data()
        ctx['object'] = object
        ctx['reviews_count'] = Review.objects.filter(posted_by=object).count()
        PRS = ProposedResourceStatus
        ctx['completed_projects_count'] = Project.objects.filter(
            proposals__resource=self.object,
            proposals__status__value=PRS.SUCCESS).distinct().count()
        return ctx


def _get_next_url(request):
    user = request.user
    next_step = user.setup_step_url
    return next_step or\
        request.GET.get('next') or\
        request.META.get('HTTP_REFERER', user.profile_url)


@login_required
def linkedin_import_view(request):
    user = request.user
    user.populate_linkedin_profile()
    user.complete_setup_step(user.SETUP_LINKEDIN_IMPORT)
    user.save()
    return HttpResponseRedirect(_get_next_url(request))


@login_required
def run_setup_wizard(request):
    user = request.user
    user.reset_setup_steps()
    user.save()
    return HttpResponseRedirect(user.setup_step_url)


class BaseSetupView(UpdateView):
    model = get_user_model()
    setup_step = None
    object = None

    def get_form_kwargs(self):
        kwargs = super(BaseSetupView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        user = self.object or self.request.user
        return user.setup_step_url or self.get_post_onboarding_url()

    def get_post_onboarding_url(self):
        user = self.request.user
        if user.is_vendor and user.has_perm('vendors.edit_vendor'):
            return self.request.user.vendor.get_absolute_url()
        return reverse('home')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.complete_setup_step(self.setup_step)
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.next_setup_step and self.setup_step != user.next_setup_step:
            next_url = request.GET.get(
                'next',
                ''
            ).strip()
            if next_url:
                return HttpResponseRedirect(next_url)
        return super(BaseSetupView, self).dispatch(request, *args, **kwargs)


class WelcomeStep(BaseSetupView):
    template_name = 'onboarding/welcome.html'
    setup_step = get_user_model().SETUP_WELCOME


class LinkedinUserProfileView(TemplateView):
    template_name = 'onboarding/user_linkedin_fetch.html'
    setup_step = get_user_model().SETUP_LINKEDIN_FETCH

    def get_success_url(self):
        user = self.request.user
        return user.setup_step_url or reverse('home')

    def get_context_data(self):
        ctx = super(LinkedinUserProfileView, self).get_context_data()
        ctx['next_url'] = self.request.GET.get('next', '').strip()
        return ctx


class CreateOnboardingUserProfileView(BaseSetupView):
    template_name = 'onboarding/user_profile.html'
    setup_step = get_user_model().SETUP_USER_PROFILE
    form_class = UserSummaryForm

    def get_initial(self):
        initial = super(CreateOnboardingUserProfileView, self).get_initial()
        initial['linkedin_profile_url'] = self.object.get_linkedin_url()
        return initial

    def get_context_data(self, form=None):
        ctx = super(CreateOnboardingUserProfileView, self).get_context_data()
        if form:ctx['form'] = form
        ctx['avatar_form'] = UploadAvatarForm(user=self.request.user)
        ctx['post_url'] = self.request.path
        return ctx


class ProfileEditView(CreateOnboardingUserProfileView):
    form_class = UserSummaryForm

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_initial(self):
        initial = super(CreateOnboardingUserProfileView, self).get_initial()
        initial['linkedin_profile_url'] = self.object.get_linkedin_url()
        return initial

    def get_object(self):
        user = self.request.user
        if self.kwargs['username'] == user.username:
            return get_object_or_404(get_user_model(), id=user.id)

        qs = get_user_model().objects.all()
        if user.is_client:
            qs = qs.filter(vendor=None)
        elif user.is_vendor:
            qs = qs.filter(vendor=user.vendor)
        try:
            return qs.get(username=self.kwargs['username'])
        except get_user_model().DoesNotExist:
            raise Http404()
profile_edit_view = member_required(ProfileEditView.as_view())


class CreateOnboardingVendorProfileView(BaseSetupView):
    setup_step = get_user_model().SETUP_VENDOR_PROFILE
    form_class = VendorProfileForm

    def get_initial(self):
        initial = {}

        initial.update({
            'website': self.object.website,
            'linkedin': self.object.linkedin,
            'twitter': self.object.twitter,
            'facebook': self.object.facebook,
            'categories': list(self.object.categories.all()),
            'video': self.object.video,
            'github': self.object.github
        })
        return initial

    def dispatch(self, request, *args, **kwargs):
        self.vendor_pk = kwargs.pop('pk', None)
        if self.request.user.is_vendor:
            if str(self.request.user.vendor.id) != self.vendor_pk:
                raise Http404()
        else:
            if not self.request.user.is_superuser:
                raise Http404()

        self.user_is_onboarding = self.request.user.pending_setup_steps != []
        return super(CreateOnboardingVendorProfileView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self):
        ctx = super(CreateOnboardingVendorProfileView, self).get_context_data()
        ctx['detail_form'] = VendorDetailForm(initial=self.get_initial())
        ctx['web_form'] = VendorWebForm(initial=self.get_initial())
        ctx['location_form'] = VendorLocationForm(request=self.request, vendor=self.object)
        ctx['active_profile'] = True
        # TODO: create permissions and groups
        ctx['admin_editing'] = self.request.user.is_superuser and self.request.user.pk != self.vendor_pk

        return ctx

    def get_form_kwargs(self, *args, **kwargs):
        kw = super(CreateOnboardingVendorProfileView,
                   self).get_form_kwargs(*args, **kwargs)
        kw['request'] = self.request
        kw['vendor'] = self.object
        return kw

    def get_object(self):
        if self.request.user.is_superuser:
            return get_object_or_404(Vendor, id=self.vendor_pk)
        return self.request.user.vendor

    def get_success_url(self):
        if self.user_is_onboarding:
            self.request.session['show_welcome_banner'] = True
        return reverse('user_setup:setup_step_vendor_profile', args=(self.object.id,))

    def form_valid(self, form):
        obj = form.save()
        form.save_m2m()
        if self.request.user.is_vendor and self.request.user.vendor is None:
            self.request.user.vendor = obj
            self.request.user.save()
        self.request.user.complete_setup_step(self.setup_step)
        self.request.user.save()

        if obj.EDIT_PROFILE in obj.pending_edit_steps:
            obj.pending_edit_steps.remove(self.object.EDIT_PROFILE)
            obj.score = obj.score + Vendor.SCORE_PROFILE
        obj.save()

        Action.add_action_edit(self.request.user, obj)

        if self.request.is_ajax() and not 'HTTP_X_PJAX' in self.request.META:
            return self.render_to_response(self.get_context_data(form))
        else:
            return HttpResponseRedirect(reverse('user_setup:setup_step_vendor_media',
                                                args=(self.object.id,)))

    def get_template_names(self):
        if self.request.is_ajax() and not 'HTTP_X_PJAX' in self.request.META:
            return 'onboarding/partials/vendor_first.html'
        else:
            return 'vendors/profile_edit_form.html'
vendor_profile_basic = member_required(CreateOnboardingVendorProfileView.as_view())


class VendorProfileDetailView(UpdateView):
    model = Vendor
    form_class = VendorDetailForm
    template_name = 'onboarding/partials/vendor_second.html'

    def get_edit_step(self):
        return self.edit_step

    def get_object(self):
        return self.request.user.vendor

    def form_valid(self, form):
        super(VendorProfileDetailView, self).form_valid(form)
        if form.cleaned_data.get('submit') == 'save':
            return HttpResponseRedirect(form.instance.get_absolute_url())
        return self.render_to_response(self.get_context_data(form))

    def get_context_data(self, form=None):
        context = super(VendorProfileDetailView, self).get_context_data()
        context['form'] = form
        context['vendor'] = self.object
        return context

    def get_success_url(self):
        return reverse('user_setup:setup_step_vendor_profile', args=(self.object.id,))


vendor_profile_detail = vendor_required(VendorProfileDetailView.as_view())


class VendorMediaEdit(UpdateView):
    model = Vendor
    template_name = 'vendors/media_edit_form.html'
    form_class = VendorMediaForm
    
    def dispatch(self, request, *args, **kwargs):
        self.vendor = get_object_or_404(Vendor, id=kwargs.get('pk'))
        request_vendor = request.user.vendor
        this_vendor = request_vendor and request_vendor.id == self.vendor.id
        if not this_vendor:
            if not request.user.is_allowed_change:
                raise Http404()
        return super(VendorMediaEdit, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, form=None):
        ctx = super(VendorMediaEdit, self).get_context_data()
        if form:ctx['form'] = form
        ctx['vendor'] = self.object
        ctx['active_media'] = True
        request_vendor = self.request.user.vendor
        request_vendor = request_vendor and request_vendor.id != self.vendor.id
        ctx['admin_editing'] = (self.request.user.is_allowed_change and not request_vendor)

        return ctx

    def get_object(self):
        return self.vendor

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if self.object.EDIT_MEDIA in self.object.pending_edit_steps:
            self.object.pending_edit_steps.remove(self.object.EDIT_MEDIA)
            self.object.score = self.object.score + Vendor.SCORE_MEDIA
        self.object.save()
        if connection.get_tenant().is_public_instance:
            return HttpResponseRedirect(reverse('vendors:client_add', args=(self.object.id,)))

        return HttpResponseRedirect(
            reverse('user_setup:setup_step_vendor_projects', args=(self.object.id,)))

vendor_profile_web = member_required(VendorMediaEdit.as_view())


class VendorProfileWebView(UpdateView):
    model = Vendor
    form_class = VendorWebForm
    template_name = 'onboarding/partials/vendor_third.html'

    def get_edit_step(self):
        return self.edit_step

    def get_object(self):
        return self.request.user.vendor

    def get_context_data(self, form=None):
        context = super(VendorProfileWebView, self).get_context_data()
        context['form'] = form
        context['vendor'] = self.object
        context['location_form'] = VendorLocationForm(request=self.request)
        return context


class PasswordSetView(BaseSetupView):
    template_name = 'onboarding/password_set.html'
    setup_step = get_user_model().SETUP_PASSWORD_SET
    form_class = PasswordSetForm

    def get_context_data(self, form=None):
        ctx = super(PasswordSetView, self).get_context_data()
        if form:ctx['form'] = form
        ctx['post_url'] = self.request.path
        return ctx

    def form_invalid(self, form):
        form.fields['password1'].help_text = ''
        return super(PasswordSetView, self).form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.SETUP_PASSWORD_SET not in user.pending_setup_steps:
            return HttpResponseRedirect(reverse('home'))
        return super(PasswordSetView, self).dispatch(request, *args, **kwargs)


class ProfileByID(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        user = get_object_or_404(get_user_model(), id=kwargs['pk'])
        return user.get_absolute_url()


class PasswordResetView(UpdateView):
    template_name = 'users/reset_password.html'
    form_class = PasswordSetForm
    model = get_user_model()

    def get_context_data(self, form=None):
        ctx = super(PasswordResetView, self).get_context_data()
        if form:ctx['form'] = form
        return ctx

    def get_form_kwargs(self):
        kwargs = super(PasswordResetView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_invalid(self, form):
        form.fields['password1'].help_text = ''
        return super(PasswordResetView, self).form_invalid(form)

    def get_object(self, queryset=None):
        return self.request.user
password_reset_view = member_required(PasswordResetView.as_view())


class UsersList(ListView):
    model = get_user_model()
    template_name = 'users/list.html'
    items_per_page = 20

    def get_template_names(self):
        if self.request.is_ajax() and self.request.GET.get(
                'filter', '').strip() == 'yes':
            if self.request.GET.get('page'):
                return 'users/partials/filter_cards.html'
            return 'users/partials/filter_results.html'
        return self.template_name

    def get_queryset(self):
        return self.model.objects.all().order_by('next_available')

    def get_context_data(self, *args, **kwargs):
        context = super(UsersList, self).get_context_data(*args, **kwargs)
        user = self.request.user
        users = self.get_queryset()
        if user.is_vendor:
            users = users.filter(vendor=user.vendor).all()
        filters = {}

        context['filters'] = filters

        context['users'] = UserFilter(self.request.GET, queryset=users,
                                      request=self.request)

        try:
            page = int(self.request.GET.get('page', 1))
        except ValueError:
            page = 1
        slice_start = self.items_per_page * (page - 1)
        slice_end = slice_start + self.items_per_page
        context['filter_slice'] = '{}:{}'.format(slice_start, slice_end)
        context['is_last_page'] = context['users'].qs.count() <= slice_end

        context['show_open_projects_btn'] = True
        return context


class UserPermissionsUpdate(BaseEditView):
    model_form = UserPermissionForm
    template_name = 'users/permission.html'
    context_variable = 'colleague'

    def get_context_data(self, *args, **kwargs):
        context = super(UserPermissionsUpdate, self).get_context_data(
            *args, **kwargs)
        context['user_being_edited'] = self.get_instance()
        return context

    def get_success_url(self):
        return self.get_instance().get_absolute_url()

    def get_delete_url(self):
        return reverse('users:list')

    def get_initial_data(self):
        kwargs = super(UserPermissionsUpdate, self).get_initial_data()
        kwargs['current_user'] = self.request.user
        return kwargs

    def get_instance(self, *args, **kwargs):
        user = self.request.user
        qs = {'id': self.kwargs['pk'],
              'kind': user.kind,
              'is_deleted': False,
              }
        if user.is_vendor:
            qs.update({'vendor': user.vendor})
        return get_object_or_404(self.model, **qs)
        return None

    def post_delete(self, instance):
        messages.warning(self.request,
                         'User {} deleted successfully.'.format(
                             instance.get_name_display().capitalize()))

    def delete_object(self, instance):
        instance.is_deleted = True
        instance.save()
        return instance


class UserDelete(DeleteView):
    model = get_user_model()

    def dispatch(self, *args, **kwargs):
        self.user = self.request.user
        return super(UserDelete, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('users:list')

    def get_object(self, pk=None):
        user = self.request.user
        qs = {'id': self.kwargs['pk'],
              'kind': user.kind,
              }
        if user.is_vendor:
            qs.update({'vendor': user.vendor})
        return get_object_or_404(self.model, **qs)

    def post(self, request, pk):
        user = self.get_object(pk)
        user.is_deleted = True
        user.save()
        messages.success(
            self.request,
            _('User %s is deleted successfully' %
              (user.get_name_display().capitalize()))
        )
        return HttpResponseRedirect(self.get_success_url())


class UserDirectJoinView(RedirectView):
    def get(self, request, uuid):
        user = request.user
        invitation = get_object_or_404(UserInvitation, uuid=uuid)
        if invitation.expires_at < now():
            return HttpResponseRedirect(reverse('home'))
        user = invitation.receiver
        logout(request)
        user.backend = settings.AUTHENTICATION_BACKENDS[1]
        login(request, user)
        Action.add_action_join(user, user, target=user.vendor)
        return HttpResponseRedirect(reverse('home'))


@restriction_exempt
@login_required
def upload_avatar(request, userid, extra_context=None, next_override=None, upload_form=UploadAvatarForm, *args, **kwargs):
    redirect_to = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('home')

    if extra_context is None:
        extra_context = {}

    user = get_object_or_404(get_user_model(), id=userid, first_login=None)
    current_user = request.user
    if current_user.vendor != user.vendor:
        raise Http404()
    elif (current_user != user):
        if not current_user.has_perm('users.invite_user'):
            raise Http404()

    avatar, avatars = _get_avatars(user)
    upload_avatar_form = upload_form(request.POST or None, request.FILES or None, user=user)

    if request.method == "POST" and 'avatar' in request.FILES:
        if upload_avatar_form.is_valid():
            avatar = Avatar(user=user, primary=True)
            image_file = request.FILES['avatar']
            avatar.avatar.save(image_file.name, image_file)
            avatar.is_primary = True
            avatar.save()
            messages.success(request, _("Successfully ""uploaded a new " "avatar."))
            avatar_updated.send(sender=Avatar, user=user, avatar=avatar)
        else:
            messages.error(request, _("Could not update the avatar. " "Please try again."))
    return HttpResponseRedirect(redirect_to)


class UserSignup(CreateView):
    model = SignupToken
    template_name = 'users/register.html'
    form_class = UserSignupForm

    def get_context_data(self, form=None):
        ctx = super(UserSignup, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['object'] = self.object
        return ctx

    def form_valid(self, form):
        tenant = connection.get_tenant()
        self.object = form.save(commit=False)
        self.object.expires_at = now() + timedelta(days=7)
        self.object.save()
        return self.render_to_response(self.get_context_data(form))


user_register_view = transaction.atomic(UserSignup.as_view())


class UserSignupConfirm(View):

    def get(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        token_obj = get_object_or_404(SignupToken, uuid=uuid)

        if token_obj.expires_at < now() or token_obj.is_verified:
            return HttpResponseRedirect(reverse('home'))

        username = generate_unique_username([token_obj.email])
        if not get_user_model().objects.filter(email=token_obj.email):
            user = get_user_model().objects.create(
                email=token_obj.email, first_name=token_obj.first_name, last_name=token_obj.last_name,
                username=username, kind=get_user_model().KIND_VENDOR,)
            user.pending_setup_steps.append(ONB.SETUP_PASSWORD_SET)
            user.vendor = Vendor.objects.create(name=unicode(user), email=user.email)
            user.save()
            token_obj.is_verified = True
            token_obj.save()
            user.backend = settings.AUTHENTICATION_BACKENDS[1]
            login(request, user)
        return HttpResponseRedirect(reverse('home'))

user_confirm_view = UserSignupConfirm.as_view()


def user_search(request):
    q = request.GET.get('q')
    kind = request.GET.get('kind')
    if q:
        users = UserFilter({'search': q, 'kind': kind},
                           queryset=get_user_model().objects.all(), request=request)[:10]
        data = [{'pk': user.id, 'text': user.get_name_display(), }
                for user in users]
        try:
            validate_email(q)
            tenant = connection.get_tenant()
            if tenant.is_public_instance:
                data.append({'pk': q, 'text': q, })
            else:
                domain = q.split('@')[-1]
                client_domains = [d.strip() for d in tenant.email_domain.lower().split(',')]

                if domain in client_domains:
                    data.append({'pk': q, 'text': q, })

        except ValidationError:
            pass
    else:
        data = []
    return JsonResponse(data, safe=False)


@transaction.atomic
def settings_notifications(request, username):
    user = get_object_or_404(get_user_model(), username=username)

    if request.method == 'POST':
        form = NotificationSettingsForm(request.POST, instance=user)
        user = form.save()
        messages.success(request, 'Settings updated.')
        return redirect('users:settings_notifications', user.username)
    else:
        form = NotificationSettingsForm(instance=user)

    return render(request, 'settings_notifications.html', {'user': user, 'form': form})


@staff_member_required
def signup_approve(request, pk):
    token = get_object_or_404(SignupToken, pk=pk)

    if request.user.is_superuser and request.user.is_client:
        token.is_approved = True
        token.save()
        messages.success(request, 'Signup approved successfully!')
        current_tenant = get_current_tenant()
        signup_task.delay(token.pk, current_tenant.pk)

    if 'next' in request.GET:
        return redirect(request.GET['next'])
    return redirect('users:signups')


@staff_member_required
def signup_delete(request, pk):
    token = get_object_or_404(SignupToken, pk=pk)

    if request.user.is_superuser and request.user.is_client:
        token.delete()
        messages.success(request, 'Signup rejected successfully!')

    if 'next' in request.GET:
        return redirect(request.GET['next'])
    return redirect('users:signups')


@staff_member_required
def signups(request):
    tokens = SignupToken.objects.order_by('-created')
    return render(request, 'users/signups.html', {
        'tokens': tokens,
        'next': reverse('users:signups'),
    })
