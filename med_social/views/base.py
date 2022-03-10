from django.views.generic.base import TemplateView
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import get_object_or_404


# TODO: Extend UpdateView and make the API more inline with that.
class BaseEditView(TemplateView):
    template_name = None
    model_form = None
    context_variable = None
    success_url = None
    delete_url = None
    is_update = False

    @property
    def model(self):
        return self.model_form.Meta.model

    @property
    def form(self):
        return self.model_form

    def get_success_url(self):
        return self.success_url

    def get_delete_url(self):
        return self.delete_url or self.get_success_url()

    def create_form(self, *args, **kwargs):
        kwargs.update(self.get_form_kwargs())
        return self.form(*args, **kwargs)

    def render_to_response(self, context):
        response = render_to_response(self.get_template_names(), context,
                                      context_instance=RequestContext(
                                          self.request))
        if self.request.method == 'POST':
            response['X-Form-Valid'] = context['success']
        return response

    def get_initial_data(self):
        return {}

    def get_form_kwargs(self):
        return {}

    def get_instance(self, *args, **kwargs):
        user = self.request.user
        pk = self.kwargs.get('pk', None)
        if pk:
            return get_object_or_404(self.model, user=user, pk=pk)
        return None

    def pre_save(self, instance):
        return instance

    def post_save(self, instance):
        return instance

    def pre_delete(self, instance):
        return instance

    def delete_object(self, instance):
        instance.delete()
        return instance

    def post_delete(self, instance):
        return instance

    def dispatch(self, request, pk=None, *args, **kwargs):
        self.object = self.get_instance(request, pk, *args, **kwargs)
        if self.object:
            self.is_update = True
        return super(BaseEditView, self).dispatch(request, pk, *args, **kwargs)

    def get(self, request, pk=None, *args, **kwargs):
        form = self.create_form(instance=self.object,
                                initial=self.get_initial_data(),
                                request=request)
        self.bound_form = form # Remove and use self.form
        ctx = self.get_context_data()
        ctx.update({
            'success': False,
            'pk': pk,
            self.context_variable: form.instance,
            'form': form
        })
        return self.render_to_response(ctx)

    def validate_form(self, form):
        return form.is_valid()

    def form_delete(self, form):
        # FIXME: Come up with better names and subclass FormView
        self.object = self.pre_delete(self.object)
        if self.object.id:
            self.delete_object(self.object)
        self.object = self.post_delete(self.object)
        ctx = {}
        ctx['deleted'] = True
        ctx['success'] = True
        delete_url = self.get_delete_url()
        if delete_url:
            return HttpResponseRedirect(delete_url)
        else:
            return self.build_response(ctx, form)

    def save_m2m(self, form):
        if hasattr(form, 'save_m2m'):
            form.save_m2m()

    def form_valid(self, form):
        self.object = self.pre_save(form.save(commit=False))
        self.object.save()
        self.save_m2m(form)
        self.object = self.post_save(self.object)
        ctx = {}
        ctx['success'] = True
        success_url = self.get_success_url()
        if success_url:
            return HttpResponseRedirect(success_url)
        else:
            return self.build_response(ctx, form)

    def form_invalid(self, form):
        ctx = {}
        ctx['success'] = False
        return self.build_response(ctx, form)

    def build_response(self, ctx, form):
        ctx.update({
            'pk': self.kwargs.get('pk'),
            'form': form,
            self.context_variable: form.instance,
        })

        context = self.get_context_data()
        context.update(ctx)
        return self.render_to_response(context)

    def post(self, request, pk=None, *args, **kwargs):
        context = {}
        context[self.context_variable] = self.object
        form = self.create_form(data=request.POST, instance=self.object,
                                files=request.FILES, request=request)
        self.bound_form = form # Remove and use self.form
        delete = request.POST.get('delete', '').strip() == 'True'
        if delete:
            return self.form_delete(form)
        elif self.validate_form(form):
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
