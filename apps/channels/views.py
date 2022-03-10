import re
from datetime import timedelta

from django.views.generic import DetailView, CreateView, ListView
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.db import connection
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from braces.views import JSONResponseMixin

from med_social.views.base import BaseEditView
from med_social.decorators import member_required

from users.tasks import user_invite
from .models import Channel
from .forms import MessageForm, NewChannelForm, UserInviteForm


class ChannelSuggestions(JSONResponseMixin, ListView):
    def get_queryset(self):
        vendors = self.channel.vendors.values_list('id', flat=True)
        restrictions = Q(vendor=None) | Q(vendor__in=vendors)

        query = self.request.GET.get('q', '').strip()
        filters = Q(username__icontains=query) \
            | Q(first_name__icontains=query) | Q(last_name__icontains=query)

        return get_user_model().objects.filter(
            restrictions).filter(filters)

    def get(self, request, channel_pk):
        self.channel = get_object_or_404(Channel, pk=channel_pk)
        self.results = list(self.get_queryset().values(
                            'id', 'username', 'first_name', 'last_name'))
        return self.render_json_response(self.results)
suggestions = ChannelSuggestions.as_view()


class CreateChannel(CreateView):
    model = Channel
    template_name = 'channels/create.html'
    context_object_name = 'channel'
    form_class = NewChannelForm

    def dispatch(self, request, content_type_pk, object_pk):
        self.content_type = get_object_or_404(ContentType, pk=content_type_pk)
        self.content_object = get_object_or_404(self.content_type.model_class(),
                                                pk=object_pk)
        return super(CreateChannel, self).dispatch(request,
                                                   content_type_pk,
                                                   object_pk)

    def get_form_kwargs(self):
        kwargs = super(CreateChannel, self).get_form_kwargs()
        kwargs['object_id'] = self.content_object.id
        kwargs['content_type'] = self.content_type
        kwargs['vendor_choices'] = self.content_object\
            .get_channel_vendor_choices(self.request.user)
        kwargs['request'] = self.request
        return kwargs

    def get_template_names(self):
        if self.request.is_ajax():
            return 'channels/partials/create.html'
        else:
            return self.template_name

    def get_success_url(self):
        url = self.content_object.get_absolute_url()
        return '{}?active_tab=channel-{}'.format(url, self.object.id)
create_channel = member_required(CreateChannel.as_view())


class ChannelPage(DetailView):
    model = Channel
    template_name = 'channels/details.html'
    context_object_name = 'channel'

    def get_object(self):
        kwargs = {'pk': self.kwargs['channel_pk']}
        if self.request.user.is_vendor:
            kwargs['vendors'] = self.request.user.vendor
        return Channel.objects.get(**kwargs)

    def get_context_data(self, object):
        ctx = super(ChannelPage, self).get_context_data()
        ctx['message_form'] = MessageForm(request=self.request)
        return ctx
channel_page = member_required(ChannelPage.as_view())


class PostComment(BaseEditView):
    model_form = MessageForm
    template_name = 'channels/comments/create.html'
    is_success = False

    def get_template_names(self):
        if self.is_success:
            return 'channels/comments/as_field.html'
        else:
            return self.template_name

    def get_context_data(self):
        ctx = super(PostComment, self).get_context_data()
        ctx['form'] = MessageForm(request=self.request)
        ctx['channel'] = self.channel
        ctx['success'] = self.is_success
        ctx['object'] = self.object
        emails = re.findall(settings.EMAIL_REGEX, self.object.body)
        existing = set(get_user_model().objects.filter(
            email__in=emails).values_list('email', flat=True))
        emails = set(emails) - existing
        ctx['emails'] = emails
        return ctx

    def get(self, request, channel_pk):
        return HttpResponseRedirect(self.response.get_absolute_url())

    def dispatch(self, request, channel_pk):
        self.user = self.request.user

        kwargs = {'pk': channel_pk}
        if self.user.is_vendor:
            kwargs['vendors'] = self.user.vendor
        self.channel = get_object_or_404(Channel, **kwargs)
        ret_val = super(PostComment, self).dispatch(request, channel_pk)
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data())
        return ret_val

    def get_success_url(self):
        return self.channel.content_object.get_absolute_url()

    def pre_save(self, instance):
        instance.channel = self.channel
        instance.posted_by = self.user
        return instance

    def post_save(self, instance):
        self.is_success = True
        return instance
post_comment = member_required(PostComment.as_view())


class InviteUser(CreateView):
    model = get_user_model()
    form_class = UserInviteForm
    template_name = 'channels/partials/invite_user_modal.html'
    ajax_template_name = 'channels/partials/invite_user_form.html'
    ajax_result_template_name = 'channels/partials/invite_result.html'

    def get_template_names(self):
        if self.request.method == 'POST':
            if self.object:
                return self.ajax_result_template_name
            else:
                return self.ajax_template_name
        else:
            return self.template_name

    def get_context_data(self, form=None):
        ctx = super(InviteUser, self).get_context_data()
        ctx['channel'] = get_object_or_404(
            Channel, id=self.kwargs['channel_pk'])
        if form:ctx['form'] = form
        ctx['object'] = self.object
        return ctx

    def get_initial(self):
        initial = super(InviteUser, self).get_initial()
        initial['email'] = self.request.GET.get('email', '')
        return initial

    def get_form_kwargs(self):
        kwargs = super(InviteUser, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        super(InviteUser, self).form_valid(form)
        password = get_user_model().objects.make_random_password()
        tenant = connection.get_tenant()
        self.object.kind = form.cleaned_data['kind']
        self.object.set_password(password)
        self.object.save()

        expires_at = now() + timedelta(days=7)
        user_invitation, _ = self.object.invitations.get_or_create(
                sender=self.request.user, receiver=self.object,
                defaults={'expires_at': expires_at})

        user_invitation.expires_at = expires_at
        user_invitation.save()
        user_invite.delay(tenant_id=tenant.id,
                          invite_id=user_invitation.id,
                          password=password)

        return self.render_to_response(self.get_context_data(form))
invite_user = member_required(InviteUser.as_view())
