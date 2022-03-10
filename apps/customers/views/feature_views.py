from django.core.urlresolvers import reverse_lazy
from django.contrib import messages
from django.views.generic import UpdateView
from django.shortcuts import get_object_or_404, render, redirect

from med_social.decorators import client_required
from med_social.utils import get_current_tenant
from ..forms import FeatureForm, WeightsForm, PremiumSettingsForm


class FeatureList(UpdateView):
    template_name = 'features/list.html'
    form_class = FeatureForm
    success_url = reverse_lazy('client_settings:features')

    def get_object(self):
        return get_current_tenant()

    def get_context_data(self, form=None):
        ctx = super(FeatureList, self).get_context_data()
        if form:ctx['form'] = form
        return ctx

    def form_valid(self, request):
        messages.success(self.request, 'Changes saved successfully.')
        return super(FeatureList, self).form_valid(request)

    def form_invalid(self, request):
        messages.error(self.request, 'Error saving changes')
        return super(FeatureList, self).form_invalid(request)

feature_list = FeatureList.as_view()


def weights(request):
    customer = get_current_tenant()
    if request.method == 'POST':
        form = WeightsForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Weights updated successfully.')
            return redirect('client_settings:weights')
    else:
        form = WeightsForm(instance=customer)

    return render(request, 'weights.html', {'form': form})


def premium_settings(request):
    customer = get_current_tenant()
    if request.method == 'POST':
        form = PremiumSettingsForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Premium settings updated successfully.')
            return redirect('client_settings:premium')
    else:
        form = PremiumSettingsForm(instance=customer)

    return render(request, 'premium.html', {'form': form})
