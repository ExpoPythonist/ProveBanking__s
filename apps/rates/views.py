from django.core.urlresolvers import reverse_lazy
from django.http import Http404, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (ListView,
                                  DetailView,
                                  CreateView,
                                  UpdateView,
                                  DeleteView,
                                  FormView)

from med_social.decorators import member_required
from features import models as features
from vendors.models import Vendor
from .models import Rate
from .forms import RateForm, UserRateForm, SuggestedRateForm


class RateCardAsField(DetailView):
    model = Rate
    template_name = 'rates/rate_suggestion.html'
    features_required = (features.financials,)
    context_object_name = 'suggested'
rate_as_field = RateCardAsField.as_view()


class RateSuggestions(ListView):
    model = Rate
    template_name = 'rates/suggestions.html'
    context_object_name = 'suggestions'
    features_required = (features.financials,)

    def get_queryset(self, *args, **kwargs):
        self.form = SuggestedRateForm(data=self.request.GET)
        if not self.form.is_valid():
            rates = self.model.objects.none()
        if not any(self.form.cleaned_data.values()):
            rates = self.model.objects.none()
        rates = self.model.get_suggested_rates(**self.form.cleaned_data)
        if self.request.user.is_vendor:
            rates = rates.filter(vendor=self.request.user.vendor)
        return rates
suggestions = RateSuggestions.as_view()


class RateListView(ListView):
    model = Rate
    template_name = 'rates/list.html'
    context_object_name = 'rates'
    features_required = (features.financials,)

    def get_context_data(self, *args, **kwargs):
        user = self.request.user
        context = super(RateListView, self).get_context_data(*args, **kwargs)
        if user.is_client:
            context['my_rate_cards'] = self.get_queryset().filter(
                vendor__isnull=True,
                user__isnull=True
            )
            context['vendors'] = Vendor.objects.all().select_related()
        else:
            context['my_rate_cards'] = self.get_queryset().filter(
                vendor=user.vendor,
                user__isnull=True
            )
            context['vendors'] = None
        return context
rate_list = member_required(RateListView.as_view())


class CreateRateView(CreateView):
    model = Rate
    form_class = RateForm
    success_url = reverse_lazy('rates:list')
    features_required = (features.financials,)

    def dispatch(self, *args, **kwargs):
        self.is_iframed = self.request.GET.get('iframed', '').strip() == 'yes'
        return super(CreateRateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CreateRateView, self).get_context_data(*args, **kwargs)
        context['action_label'] = 'create'
        if self.is_iframed:
            context['iframed'] = True
            context['is_ajax'] = True
        return context

    def get_template_names(self):
        if self.is_iframed:
            if self.object:
                return 'rates/ajax_result.html'
            return 'rates/form_partial.html'
        if self.request.is_ajax() and not 'HTTP_X_PJAX' in self.request.META:
            return 'rates/form_ajax.html'
        else:
            return 'rates/form.html'

    def form_valid(self, form):
        self.object = form.save()
        ajax_or_iframe = self.request.is_ajax() or self.is_iframed
        is_pjax = 'HTTP_X_PJAX' in self.request.META
        if ajax_or_iframe and not is_pjax:
            return self.render_to_response(self.get_context_data(
                form=form, success=True))
        else:
            return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super(CreateRateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(CreateRateView, self).get_initial()
        if self.request.user.is_client:
            return initial
        else:
            return initial.update({
                'vendor': self.request.user.vendor
            })
create_rate = member_required(CreateRateView.as_view())


class EditRateView(UpdateView):
    model = Rate
    form_class = RateForm
    template_name = 'rates/form.html'
    success_url = reverse_lazy('rates:list')
    features_required = (features.financials,)

    #def dispatch(self, *args, **kwargs):
        #rate_object = self.get_object()
        #if user.is_vendor and rate_object.vendor != user.vendor:
            #raise Http404()
        #return super(EditRateView, self).dispatch(*args, **kwargs)

    def get_object(self):
        user = self.request.user
        rate = get_object_or_404(Rate, pk=self.kwargs['pk'])
        if not (user.is_client or (user.is_vendor and rate.vendor == user.vendor)):
            # clients can see all rates, vendors can see only their own
            raise Http404()
        return rate

    def get_context_data(self, *args, **kwargs):
        context = super(EditRateView, self).get_context_data(*args, **kwargs)
        context['action_label'] = 'edit'
        return context

    def get_form_kwargs(self):
        kwargs = super(EditRateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(EditRateView, self).get_initial()
        if self.request.user.is_client:
            return initial.update({
                'vendor': '-1'
            })
        else:
            return initial.update({
                'vendor': self.request.user.vendor
            })
edit_rate = member_required(EditRateView.as_view())


class DeleteRateView(DeleteView):
    model = Rate
    success_url = reverse_lazy('rates:list')
    features_required = (features.financials,)
    template_name = 'rates/confirm_remove_rate.html'
delete_rate = member_required(DeleteRateView.as_view())


class EditUserRateView(FormView):
    model = Rate
    form_class = UserRateForm
    template_name = 'rates/user_rate_form.html'
    features_required = (features.financials,)

    def dispatch(self, *args, **kwargs):
        self.user = get_object_or_404(get_user_model(),
                                      username=self.kwargs['username'])
        try:
            self.object = Rate.objects.get(user=self.user)
        except Rate.DoesNotExist:
            self.object = None
        return super(EditUserRateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(EditUserRateView, self).get_context_data(*args,
                                                                 **kwargs)
        context['account'] = self.user
        return context

    def get_success_url(self):
        return self.user.get_absolute_url()

    def get_initial(self):
        if self.object is not None:
            return {
                'cost': self.object.cost,
                'unit': self.object.unit,
                'user': self.user
            }
        else:
            return {
                'user': self.user
            }

    def post(self, *args, **kwargs):
        form = self.get_form(self.get_form_class())
        if form.is_valid():
            form.save()
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
edit_user_rate = member_required(EditUserRateView.as_view())
