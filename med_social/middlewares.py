from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.core.exceptions import MiddlewareNotUsed
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.contrib.auth import logout


class AjaxRedirectMiddleware(object):
    """Browsers transparently handle 302 redirect with giving programatic
    access to change the behaviour so we use a different status code for
    HttpResponseRedirect when the request was made from ajax"""

    def process_response(self, request, response):
        if request.META.get('HTTP_X_PJAX') == 'true':
            response['HTTP_X_PJAX'] = 'true'
        if request.is_ajax():
            if isinstance(response, HttpResponseRedirect):
                response.status_code = 278
        return response


class RestrictedAccessMiddleware(object):
    IGNORE_URLS = (reverse_lazy('account_logout'),
                   reverse_lazy('waitlist'),
                   '/accounts/linkedin/login/',
                   '/accounts/linkedin/login/callback/',)

    def __init__(self):
        if not settings.RESTRICTED_ACCESS:
            raise MiddlewareNotUsed()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if getattr(callback, 'restriction_exempt', False):
            return None

        user = request.user
        if user.is_superuser:
            # Rules don't apply to superusers
            return None

        path = request.path
        if settings.DEBUG and \
                (path.startswith(settings.MEDIA_URL) or
                 path.startswith(settings.STATIC_URL)):
            return None

        if path in self.IGNORE_URLS:
            return None

        if user.is_authenticated():
            if user.is_deleted:
                if request.method == 'GET' and not (path.startswith('/accounts/') and path.endswith('/login/')):
                    logout(request)
                    messages.success(request, _("Sorry, your account has been deleted."))
                    return HttpResponseRedirect(reverse('account_login'))
                elif not request.tenant.direct_signup and not self.is_invited and not path.startswith('/waitlist/'):
                    messages.success(request, _("Sorry, you need to get approved before you access this page."))
                    return HttpResponseRedirect(reverse('waitlist'))

        if path.startswith('/accounts/') and path.endswith('/login/'):
            # Ignore on links like '/accounts/linkedin/login/' or
            # '/accounts/login/'
            inv_token = request.GET.get('invitation_token')
            if inv_token:
                request.session['invitation_token'] = inv_token
            inviter = request.GET.get('inviter')
            if inviter:
                request.session['inviter'] = inviter
            account_kind = request.GET.get('account_kind')
            if account_kind:
                request.session['account_kind'] = account_kind

        if path.startswith('/admin'):
            if not (user.is_superuser or user.is_staff):
                return None
            else:
                return HttpResponseForbidden()

        if user.is_authenticated() and not request.is_ajax():
            if user.next_setup_step:
                next_url = request.GET.get('next', '')
                step_url = user.setup_step_url
                if path != step_url:
                    messages.warning(request, _("Please complete your profile before moving on."))
                    return HttpResponseRedirect('%s?next=%s' % (step_url, next_url))
            if request.tenant.is_public:
                return None
            if user.is_vendor and user.vendor and user.vendor.is_prospective:
                vendor_profile_url = user.vendor.get_absolute_url()
                user_profile = reverse('users:profile', args=(user.username,))
                is_onboarding = path.startswith('/u/')
                is_vendor_url = path.startswith('/vendors/')
                is_user_profile = path.startswith(user_profile)
                is_accounts = path.startswith('/accounts/')
                is_rfp = path.startswith('/rfps/')
                if not any([is_accounts, is_onboarding, is_vendor_url, is_user_profile]):
                    return HttpResponseRedirect(vendor_profile_url)
