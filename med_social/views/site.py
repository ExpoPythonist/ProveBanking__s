from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, DetailView, CreateView
from django.shortcuts import get_object_or_404, redirect

from allauth.account.adapter import get_adapter
from allauth.socialaccount.models import SocialToken
from annoying.functions import get_object_or_None
from braces.views import JSONResponseMixin

from customers.forms import RequestDemoForm
from posts.models import Post
from users.models import User


__all__ = ('HomeView', 'WaitListView', 'InviteView', 'GetVetted',
           'InviteApplyView', 'ThankYou', 'About', 'HeartBeat',)


class HeartBeat(JSONResponseMixin, DetailView):
    def get(self, request):
        return self.render_json_response({
            'status': 'OK',
            'is_secure': request.is_secure()
        })


class RequestDemoView(CreateView):
    form_class = RequestDemoForm
    template_name = 'demo_request.html'

    def get_success_url(self):
        return reverse('thankyou')

    def get(self, request):
        return HttpResponseRedirect(reverse('home'))

    def form_valid(self, form):
        self.object = form.save()
        ctx = form.cleaned_data
        print ctx
        get_adapter().send_mail('customers/email/request', ['phil@proven.cc', 'suzanne@proven.cc', 'kevin@proven.cc'], ctx)
        return super(RequestDemoView, self).form_valid(form)


class HomeView(TemplateView):
    def get(self, request):
        return super(HomeView, self).get(request)

    def get_template_names(self):
        return ['home.html']

    def get_context_data(self, **kwargs):
        ctx = super(HomeView, self).get_context_data(**kwargs)
        ctx['form'] = RequestDemoForm()
        return ctx


class ThankYou(TemplateView):
    template_name = 'thankyou.html'


class About(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        ctx = super(About, self).get_context_data(**kwargs)
        ctx['posts'] = Post.objects.all()[:10]
        return ctx


class InviteView(TemplateView):
    template_name = 'invite.html'


class InviteApplyView(TemplateView):
    template_name = 'apply.html'

    def get(self, request, username):
        self.inviter = get_object_or_404(User, username=username)
        if request.user.is_authenticated():
            return HttpResponseRedirect(self.inviter.profile_url)
        else:
            return super(InviteApplyView, self).get(request, username)

    def get_context_data(self):
        return {'inviter': self.inviter}


class WaitListView(TemplateView):
    template_name = 'waitlist.html'

    '''
    def get(self, request):
        user = request.user
        if user.is_authenticated() and user.is_approved:
            user.complete_setup_step(user.SETUP_WAITING)
            user.save()
            return HttpResponseRedirect(reverse('home'))
        else:
            return super(WaitListView, self).get(request)
    '''

    def get_context_data(self):
        ctx = {}
        user = self.request.user
        inv = get_object_or_None(User, email=user.email)
        ctx['invitation'] = inv
        return ctx


class GetVetted(TemplateView):
    template_name = 'get_vetted.html'

    def get_context_data(self, **kwargs):
        ctx = super(GetVetted, self).get_context_data(**kwargs)
        ctx['form'] = RequestDemoForm()
        return ctx
