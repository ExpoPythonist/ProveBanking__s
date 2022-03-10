from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.contrib.auth import get_user_model

from med_social.decorators import member_required, login_required

from .emails.views import RequestUpdateEmail
from .models import UpdateRequest
from .forms import BatchRequestUpdateForm


class RequestUpdateView(TemplateView):
    template_name = 'availability/partials/last_updated.html'

    def dispatch(self, *args, **kwargs):
        user_pk = self.kwargs['user_pk']
        if self.request.user.is_vendor:
            self.object =\
                get_object_or_404(get_user_model(), id=user_pk,
                                  vendor=self.request.user.vendor)
        else:
            self.object = get_object_or_404(get_user_model(), id=user_pk)
        return super(RequestUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self):
        ctx = super(RequestUpdateView, self).get_context_data()
        ctx.update({
            'update_requested': True,
            'for_user': self.object
        })
        return ctx

    def post(self, request, user_pk):
        avl_rq, created = UpdateRequest.objects.get_or_create(
            user=self.object)
        avl_rq.requested_by.add(self.request.user)
        avl_rq.save()
        RequestUpdateEmail(
            user=self.object,
            requested_by=request.user
        ).send()
        return self.render_to_response(self.get_context_data())
request_update = member_required(RequestUpdateView.as_view())


class BatchRequestUpdateView(TemplateView):
    template_name = 'availability/partials/batch_update_request_form.html'

    def get_context_data(self, extra_context=None):
        extra_context = extra_context or {}
        ctx = super(BatchRequestUpdateView, self).get_context_data()
        ctx.update({
            'success': True,
        })
        ctx.update(extra_context)
        return ctx

    def post(self, request):
        form = BatchRequestUpdateForm(data=request.POST)
        if form.is_valid():
            for user in form.cleaned_data['users']:
                avl_rq, created = UpdateRequest.objects.get_or_create(
                    user=user)
                avl_rq.requested_by.add(self.request.user)
                avl_rq.save()
                RequestUpdateEmail(
                    user=user,
                    requested_by=request.user
                ).send()
            return self.render_to_response(
                self.get_context_data({'success': True}))
        else:
            return self.render_to_response(
                self.get_context_data({'success': False, 'form_error': True}))
batch_request_update = member_required(BatchRequestUpdateView.as_view())


class ConfirmAvailability(TemplateView):
    template_name = 'availability/confirm.html'
    confirmed = False

    def get(self, request):
        confirmed = request.GET.get('confirm', '').strip().lower()
        self.confirmed = confirmed == 'yes'
        if self.confirmed:
            request.user.last_updated_availability = now()
            request.user.save(update_fields=(('meta'),))
        return super(ConfirmAvailability, self).get(request)

    def get_context_data(self):
        ctx = super(ConfirmAvailability, self).get_context_data()
        ctx['availability'] = self.request.user.get_availability()
        ctx['object'] = self.request.user
        return ctx
confirm_availability = login_required(ConfirmAvailability.as_view())
