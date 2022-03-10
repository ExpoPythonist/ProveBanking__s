from collections import OrderedDict

from django import forms
from django.db.models import Sum
from django.db import transaction, connection
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from vlkjsonfield.forms import JSONModelForm

from med_social.forms.base import FieldsetMixin
from med_social.forms.base import DeletableFieldsetForm

from .models import Metric, Review, ReviewToken


class ReviewForm(DeletableFieldsetForm):
    remarks = forms.CharField(label=_("Further remarks"),
                              widget=forms.Textarea,
                              required=True)

    anonymous = forms.BooleanField(label="I want to post review anonymously",
                                   required=False)

    vendor_viewable = forms.BooleanField(required=False,
                                         help_text=" ")
                                        
                                   #"posted the review")

    class Meta:
        model = Review
        fields = ('remarks', 'anonymous', 'vendor_viewable')
        deletable = False

    def __init__(self, *args, **kwargs):
        self.content_type = kwargs.pop('content_type')
        self.metrics = {}
        self.core_metrics = []
        super(ReviewForm, self).__init__(*args, **kwargs)
        data = kwargs.get('data', {}).copy()
        initial = kwargs.get('initial', {})
        for metric in Metric.objects.filter(content_type=self.content_type):
            FieldClass = metric.field.review_form_field_class
            self.fields[metric.slug] = FieldClass(
                label=metric.name,
                help_text=metric.help_text,
                choices=metric.get_display_choices())
            self.metrics[metric.slug] = metric
        self.fields['remarks'] = self.fields.pop('remarks')
        self.fields['anonymous'] = self.fields.pop('anonymous')
        self.fields['vendor_viewable'] = self.fields.pop('vendor_viewable')
        self.fields['vendor_viewable'].label="Share this feedback with the supplier.&nbsp; Leave unchecked if this is for {tenant} users only ".format(tenant=connection.tenant.name )
        if data:    
            kwargs['data'] = data
        kwargs['initial'] = initial


class MetricForm(DeletableFieldsetForm):
    fieldsets = (
        ('Metric details',
         {'fields': ('name', 'help_text', 'kind', 'content_type')},
         ),
    )

    class Meta:
        model = Metric
        deletable = True
        fields = ('name', 'help_text', 'kind', 'content_type', 'weight')
        labels = {
            'kind': 'Metric type',
        }

    def __init__(self, *args, **kwargs):
        self.content_type = kwargs.pop('content_type')
        super(MetricForm, self).__init__(*args, **kwargs)
        # Do this so that when form calls models clean() method, it has the
        # valid content_type set already.
        self.fields['content_type'].widget = forms.HiddenInput()
        self.fields['content_type'].required = False
        self.fields['weight'].widget = forms.HiddenInput()
        self.fields['weight'].required = False

        #for name in self.fields:
        #    self.fields[name].widget.attrs['ignore-labelinplace'] = 'true'

    def clean_weight(self):
        if self.instance and self.instance.id:
            return self.instance.weight
        existing_weight = self.content_type.metrics.aggregate(
            weight=Sum('weight')).get('weight', 0)
        if not existing_weight:
            existing_weight = 0
        weight = 100 - existing_weight
        if weight < 0:
            weight = 0
        return weight

    def clean_content_type(self):
        return self.content_type

    def save(self, *args, **kwargs):
        commit = kwargs.pop('commit', True)
        kwargs['commit'] = False
        metric = super(MetricForm, self).save(*args, **kwargs)
        metric.content_type = self.content_type
        if commit:
            metric.save()
        return metric


class MetricLabelsForm(JSONModelForm):
    fieldsets = []

    class Meta:
        model = Metric
        deletable = True
        fields = []

    def __init__(self, *args, **kwargs):
        self.kind = kwargs.pop('kind')
        super(MetricLabelsForm, self).__init__(*args, **kwargs)
        self.KindFieldClass = self.get_kind_field_class(self.kind)
        self.is_editable = self.KindFieldClass.editable
        self.score_labels = self.get_score_labels()
        self.generate_score_fields()

    @classmethod
    def label_field_name(self, label):
        return 'metric_data__labels__{}'.format(label)

    def get_kind_field_class(self, kind):
        return self.Meta.model.FIELD_CLASSES.get(kind)

    def get_score_labels(self):
        return OrderedDict(sorted(
            self.KindFieldClass.get_labels().iteritems(),
            key=lambda x: x[0]))

    def generate_score_fields(self):
        if not self.is_editable:
            return
        FieldClass = self.KindFieldClass.get_form_field_class()
        score_fields = []
        for K, V in self.score_labels.items():
            field_name = self.label_field_name(K)
            score_fields.append(field_name)
            if self.instance and self.instance.kind == self.kind:
                V = self.instance.metric_data['labels'][K]
            self.fields[field_name] = FieldClass(
                label=mark_safe('<span class="star-label"></span>'), initial=V)
            self.fields[field_name].widget.attrs['placeholder'] = 'Value'
            self.fields[field_name].widget.attrs['ignore-labelinplace'] = 'true'
        self.fieldsets = list(self.fieldsets) + [('Score values',
                                                 {'fields': score_fields})]


class MetricWeightageForm(forms.Form):
    def __init__(self, metrics, *args, **kwargs):
        self.metrics = metrics
        super(MetricWeightageForm, self).__init__(*args, **kwargs)

    def clean(self):
        total = 0
        for metric in self.metrics:
            total += self.cleaned_data.get(unicode(metric.id)) or metric.weight
        if total != 100:
            raise forms.ValidationError(
                'Sum of all metric weight must be 100%.')
        return self.cleaned_data

    def save(self, *args, **kwargs):
        with transaction.atomic():
            for metric in self.metrics:
                metric.weight = self.cleaned_data.get(unicode(metric.id), 0)\
                    or metric.weight
                metric.save()


class AnonymousReviewForm(DeletableFieldsetForm):
    remarks = forms.CharField(label=_("Further remarks"),
                              widget=forms.Textarea,
                              required=True)

    class Meta:
        model = Review
        fields = ('remarks',)
        deletable = False

    def __init__(self, *args, **kwargs):
        self.content_type = kwargs.pop('content_type')
        self.metrics = {}
        self.core_metrics = []
        super(ReviewForm, self).__init__(*args, **kwargs)
        data = kwargs.get('data', {}).copy()
        initial = kwargs.get('initial', {})
        for metric in Metric.objects.filter(content_type=self.content_type):
            FieldClass = metric.field.review_form_field_class
            self.fields[metric.slug] = FieldClass(
                label=metric.name,
                help_text=metric.help_text,
                choices=metric.get_display_choices())
            self.metrics[metric.slug] = metric
        self.fields['remarks'] = self.fields.pop('remarks')

        if data:
            kwargs['data'] = data
        kwargs['initial'] = initial


class ReviewTokenForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('', {'rows': (('email',),)},),
    )

    email = forms.EmailField()

    class Meta:
        model = ReviewToken
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super(ReviewTokenForm, self).__init__(*args, **kwargs)
        self.__setup_fieldsets__()
