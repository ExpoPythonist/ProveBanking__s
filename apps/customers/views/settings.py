from django import forms
from django.views.generic import TemplateView, ListView, FormView, CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect, Http404
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.contrib import messages

from med_social.views.base import BaseEditView
from reviews.models import Metric
from reviews.forms import MetricForm, MetricWeightageForm, MetricLabelsForm
from categories.models import Category
from categories.forms import CategoryForm


class SettingsHome(TemplateView):
    template_name = 'customers/settings/home.html'


class MetricTypeList(ListView):
    template_name = 'metrics/type_list.html'
    context_object_name = 'content_types'

    def get_queryset(self):
        return ContentType.objects.get_for_models(*Metric.get_supported_models())


class MetricList(FormView):
    template_name = 'metrics/list.html'

    def dispatch(self, request, ctype_id):
        self.content_type = get_object_or_404(ContentType, id=ctype_id)
        if self.content_type.model_class() not in Metric.get_supported_models():
            raise Http404()
        return super(MetricList, self).dispatch(request, ctype_id)

    def get_success_url(self):
        return reverse_lazy('client_settings:metrics_list',
                            args=(self.content_type.id,))

    def get_form_class(self):
        self.metrics = list(self.content_type.metrics.filter(is_deleted=False))
        fields = {}
        for metric in self.metrics:
            field = forms.DecimalField(initial=metric.weight, max_value=100, required=False)
            field.instance = metric
            fields[unicode(metric.id)] = field
        return type('MetricWeightageForm', (MetricWeightageForm,), fields)

    def get_form(self, form_class=None):
        return self.get_form_class()(metrics=self.metrics, data=self.request.POST)

    def get_context_data(self, form=None):
        ctx = super(MetricList, self).get_context_data()
        if form:
            ctx['form'] = form
        ctx['metrics'] = self.metrics
        ctx['ctype'] = self.content_type
        ctx['total_metric_weight'] = sum(map(lambda x: x.weight, self.metrics))
        ctx['total_weight_incorrect'] = (100 - ctx['total_metric_weight']) != 0
        return ctx

    def form_invalid(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error, extra_tags="danger")
        if not form.non_field_errors:
            messages.error(
                self.request, 'Could not save the changes. Please make sure the sum of all weights is 100%',
                extra_tags="danger")
        return HttpResponseRedirect(self.success_url)

    def form_valid(self, form):
        form.save()
        return super(MetricList, self).form_valid(form)


class EditMetric(BaseEditView):
    model_form = MetricForm
    template_name = 'metrics/create.html'
    context_variable = 'metric'
    labels_form = None

    def dispatch(self, *args, **kwargs):
        self.content_type = get_object_or_404(ContentType, id=kwargs['ctype_id'])
        if self.content_type.model_class() not in Metric.get_supported_models():
            raise Http404()
        return super(EditMetric, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('client_settings:metrics_list',
                            args=(self.content_type.id,))

    def get_initial_data(self):
        if 'kind' in self.request.GET:
            kind = self.get_metric_kind_class()
            return {
                'kind': self.request.GET.get('kind'),
                'name': self.request.GET.get('name'),
                'help_text': kind.default_help_text or ''
            }
        else:
            return {}

    def get_form_kwargs(self):
        kwargs = super(EditMetric, self).get_form_kwargs()
        kwargs['content_type'] = self.content_type
        return kwargs

    def create_labels_form(self, data=None):
        kwargs = {
            'kind': self.get_metric_kind(),
            'instance': self.object
        }
        if data:
            kwargs['data'] = data
        return MetricLabelsForm(**kwargs)

    def get_metric_kind(self):
        kind = self.request.GET.get('kind') or self.request.POST.get('kind')
        if self.object:
            kind = kind or self.object.kind
        if not kind:
            return self.form.base_fields['kind'].initial
        return kind

    def get_metric_kind_class(self):
        kind = self.get_metric_kind()
        return self.model_form.Meta.model.FIELD_CLASSES.get(kind)

    def get_context_data(self):
        ctx = super(EditMetric, self).get_context_data()
        ctx['labels_form'] = self.labels_form or self.create_labels_form()
        ctx['ctype'] = self.content_type
        return ctx

    def get_instance(self, *args, **kwargs):
        if 'pk' in self.kwargs:
            return get_object_or_404(self.model_form.Meta.model,
                                     pk=self.kwargs['pk'],
                                     content_type=self.content_type)
        return None

    def validate_form(self, form):
        self.labels_form = self.labels_form or self.create_labels_form(
            data=self.request.POST)
        return self.labels_form.is_valid() and form.is_valid()

    def pre_save(self, instance):
        label_instance = self.labels_form.save(commit=False)
        instance.metric_data = label_instance.metric_data
        instance.content_type = self.content_type
        return instance

    def pre_delete(self, instance):
        if instance.weight != 0:
            # dont let delete
            messages.warning(self.request, 'Cannot delete Metric with weight greater than zero.'.format(self.object))

    def post_delete(self, instance):
        messages.warning(self.request, 'Metric {} deleted successfully.'.format(self.object))


def _get_kind(kind_label):
        kind_label = kind_label.lower()
        kind = [i for i, v in enumerate(Category.KIND_CHOICES) if kind_label == v[1].lower()]
        if kind:
            return Category.KIND_CHOICES[kind[0]][0]
        else:
            return None


class CategoryList(ListView):
    model = Category
    template_name = 'customers/settings/categories/list.html'
    context_object_name = 'categories'

    def dispatch(self, *args, **kwargs):
        self.kind_label = self.kwargs.get('kind', None)
        self.kind = _get_kind(self.kind_label)
        if self.kind is None:
            raise Http404()
        return super(CategoryList, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CategoryList, self).get_context_data(*args, **kwargs)
        context['kind_label'] = self.kind_label
        context['kind_label_plural'] = Category.KIND_LABELS[self.kind_label]
        context['kind'] = self.kind
        return context

    def get_queryset(self):
        return Category.objects.filter(kind=self.kind)


class CreateCategory(CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'customers/settings/categories/form.html'
    context_object_name = 'category'

    def dispatch(self, *args, **kwargs):
        self.kind_label = self.kwargs.get('kind', None)
        self.kind = _get_kind(self.kind_label)
        if self.kind is None:
            raise Http404()

        return super(CreateCategory, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CreateCategory, self).get_context_data(*args, **kwargs)
        context['kind_label'] = self.kind_label
        context['kind'] = self.kind
        context['action'] = "create"
        return context

    def form_valid(self, form):
        form.instance.kind = self.kind
        return super(CreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('client_settings:manage_categories', args=[self.kind_label])


class EditCategory(UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'customers/settings/categories/form.html'
    context_object_name = 'category'

    def dispatch(self, *args, **kwargs):
        self.kind_label = self.kwargs.get('kind', None)
        self.kind = _get_kind(self.kind_label)
        if self.kind is None:
            raise Http404()

        return super(EditCategory, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(EditCategory, self).get_context_data(*args, **kwargs)
        context['kind_label'] = self.kind_label
        context['kind'] = self.kind
        context['action'] = "edit"
        return context

    def get_success_url(self):
        return reverse('client_settings:manage_categories', args=[self.kind_label])


class DeleteCategory(DeleteView):
    model = Category

    def dispatch(self, *args, **kwargs):
        self.kind_label = self.kwargs.get('kind', None)
        self.kind = _get_kind(self.kind_label)
        if self.kind is None:
            raise Http404()

        return super(DeleteCategory, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('client_settings:manage_categories', args=[self.kind_label])
