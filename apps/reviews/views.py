from django.views.generic import (DetailView, DeleteView, TemplateView,
                                  UpdateView, ListView)

from django.views.generic.edit import CreateView

from django.shortcuts import get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages

from med_social.views.base import BaseEditView
from med_social.decorators import member_required, client_required
from .models import Review, Metric, ReviewToken
from .forms import ReviewForm, ReviewTokenForm


class ReviewObject(BaseEditView):
    template_name = 'reviews/create.html'
    model_form = ReviewForm

    def dispatch(self, request, content_type_pk, object_pk):
        self.content_type = get_object_or_404(ContentType, pk=content_type_pk)
        model = self.content_type.model_class()

        # HACK!! FIX THIS!!
        # if not model in Metric.get_supported_models():
        #     raise Http404()

        self.content_model = model
        self.content_object = get_object_or_404(self.content_model,
                                                pk=object_pk)

        if self.content_object == request.user:
            raise Http404()

        return super(ReviewObject, self).dispatch(request, content_type_pk,
                                                  object_pk)

    def post(self, request, *args, **kwargs):
        if not Metric.is_weight_sum_ok(self.content_type):
            return HttpResponseRedirect(request.path)
        return super(ReviewObject, self).post(request, *args, **kwargs)

    def create_form(self, *args, **kwargs):
        kwargs['content_type'] = self.content_type
        return super(ReviewObject, self).create_form(*args, **kwargs)

    def get_success_url(self):
        return reverse('reviews:detail', args=(self.object.pk,))

    def get_context_data(self):
        ctx = super(ReviewObject, self).get_context_data()
        ctx['content_object'] = self.content_object
        ctx['content_type'] = self.content_type
        ctx['content_model'] = self.content_model
        ctx['request_kwargs'] = self.kwargs
        ctx['weight_sum_ok'] = Metric.is_weight_sum_ok(self.content_type)
        return ctx

    def pre_save(self, instance):
        instance.content_object = self.content_object
        instance.posted_by = self.request.user
        return instance

    def post_save(self, instance):
        instance.review_metrics.all().delete()
        for name, score in self.bound_form.cleaned_data.items():
            metric = self.bound_form.metrics.get(name, None)
            if metric:
                instance.review_metrics.create(metric=metric, score=score)
        instance.score = instance.calculate_score()
        instance.save()
        return instance
review_object = client_required(ReviewObject.as_view())


class ReviewDetails(DetailView):
    model = Review
    template_name = 'reviews/detail.html'
    context_object_name = 'review'

    def get_object(self):
        return get_object_or_404(Review, id=self.kwargs['review_pk'])
review_details = member_required(ReviewDetails.as_view())


class DeleteMetric(DeleteView):
    model = Metric

    def get_success_url(self):
        return self.request.REQUEST.get(
            'next',
            reverse('client_settings:metrics_type_list'))

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_deleted = True
        self.object.save()
        return redirect(self.get_success_url())


class ConfirmDeleteMetric(TemplateView):
    template_name = 'reviews/confirm_delete_metric.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ConfirmDeleteMetric, self).get_context_data(*args,
                                                                    **kwargs)
        context['metric'] = get_object_or_404(Metric,
                                              pk=int(self.kwargs['pk']))
        return context


class UndeleteMetric(UpdateView):
    model = Metric

    def get_success_url(self):
        return self.request.REQUEST.get(
            'next',
            reverse('client_settings:metrics_type_list'))

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_deleted = False
        self.object.save()
        return redirect(self.get_success_url())


'''
class VendorAvgScoreBreakdown(DetailView):
    model = Vendor
    template_name = 'vendors/avg_score.html'

    def get_object(self):
        pk = self.kwargs['pk']
        user = self.request.user
        if user.is_client:
            return get_object_or_404(self.model, pk=pk)
        else:
            return get_object_or_404(self.model, pk=pk, users=user)

    def get_context_data(self, **kwargs):
        ctx = DetailView.get_context_data(self, **kwargs)
        ctx['avg_score'] = self.object.get_average_score()
        ctx['reviews'] = Review.objects.filter(response__vendor=self.object)
        return ctx
'''


class ReviewList(ListView):
    model = Review
    template_name = 'reviews/reviews_list.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        obj = self.content_type.get_object_for_this_type(pk=self.kwargs['object_pk'])

        if obj._meta.object_name == 'Vendor':
            reviews = list(super(ReviewList, self).get_queryset().filter(content_object=obj))
            portfolio_reviews = Review.objects.filter(content_object__in= obj.portfolio.all())
            if portfolio_reviews:
                reviews.extend(list(portfolio_reviews))
            return reviews
        return super(ReviewList, self).get_queryset().filter(content_object=obj)

    def get_context_data(self, **kwargs):
        ctx = super(ReviewList, self).get_context_data()
        ctx['content_type'] = self.content_type
        ctx['content_object'] = self.content_object
        return ctx

    def dispatch(self, *args, **kwargs):
        self.content_type = get_object_or_404(ContentType,
                                              pk=kwargs['content_type_pk'])
        if not self.content_type.model_class() in Metric._supported_models:
            raise Http404()
        self.content_object = get_object_or_404(
            self.content_type.model_class(),
            pk=kwargs['object_pk'])
        return super(ReviewList, self).dispatch(*args, **kwargs)
review_list = client_required(ReviewList.as_view())


class PublicReviewCreate(BaseEditView):
    template_name = 'reviews/create_anonymous_review.html'
    model_form = ReviewForm

    def dispatch(self, request, uuid):
        self.uuid = uuid
        self.review_token = get_object_or_404(ReviewToken, uuid=uuid)
        self.content_type = get_object_or_404(ContentType, pk=self.review_token.content_type.id)
        model = self.content_type.model_class()
        if self.review_token.is_expired() or self.review_token.is_used:
            raise Http404()
        if not model in Metric.get_supported_models():
            raise Http404()

        self.content_model = model
        self.content_object = get_object_or_404(self.content_model,
                                                pk=self.review_token.object_id)

        if self.content_object == request.user:
            raise Http404()

        return super(PublicReviewCreate, self).dispatch(request, uuid)

    def post(self, request, *args, **kwargs):
        if not Metric.is_weight_sum_ok(self.content_type):
            return HttpResponseRedirect(request.path)
        return super(PublicReviewCreate, self).post(request, *args, **kwargs)

    def create_form(self, *args, **kwargs):
        kwargs['content_type'] = self.content_type
        return super(PublicReviewCreate, self).create_form(*args, **kwargs)

    def get_success_url(self):
        return reverse('vendors:client_thanks')

    def get_context_data(self):
        ctx = super(PublicReviewCreate, self).get_context_data()
        ctx['content_object'] = self.content_object
        ctx['content_type'] = self.content_type
        ctx['content_model'] = self.content_model
        ctx['request_kwargs'] = self.kwargs
        ctx['weight_sum_ok'] = Metric.is_weight_sum_ok(self.content_type)
        ctx['uuid'] = self.uuid
        ctx['public_review'] = True
        return ctx

    def pre_save(self, instance):
        instance.content_object = self.content_object
        instance.token = self.review_token
        return instance

    def post_save(self, instance):
        instance.review_metrics.all().delete()
        for name, score in self.bound_form.cleaned_data.items():
            metric = self.bound_form.metrics.get(name, None)
            if metric:
                instance.review_metrics.create(metric=metric, score=score)
        instance.score = instance.calculate_score()
        self.review_token.is_used = True
        self.review_token.save()
        instance.save()
        return instance
public_review = PublicReviewCreate.as_view()


class ReviewTokenView(CreateView):
    template_name = 'reviews/partials/create_review_token.html'
    form_class = ReviewTokenForm
    model = ReviewToken

    def dispatch(self, request, *args, **kwargs):
        self.content_type_pk = kwargs.pop('content_type_pk')
        self.object_pk = kwargs.pop('object_pk')
        self.content_type = get_object_or_404(ContentType, pk=self.content_type_pk)
        model = self.content_type.model_class()
        if not model in Metric.get_supported_models():
            raise Http404()
        self.content_model = model
        self.content_object = get_object_or_404(self.content_model,
                                                pk=self.object_pk)

        if self.content_object == request.user:
            raise Http404()
        return super(ReviewTokenView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.content_object.get_absolute_url()

    def get_context_data(self, form=None):
        ctx = super(ReviewTokenView, self).get_context_data()
        ctx['content_type_pk'] = self.content_type_pk
        ctx['object_pk'] = self.object_pk
        if form:ctx['form'] = form
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.content_object = self.content_object
        self.object.created_by = self.request.user
        self.object.save()
        if self.request.is_ajax():
            return self.render_to_response(self.get_context_data(form))
        else:
            return HttpResponseRedirect(self.get_success_url())
create_review_token = client_required(ReviewTokenView.as_view())


