from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.conf import settings
from django.utils.decorators import available_attrs
from django.contrib.auth.decorators import login_required
from functools import wraps

from .utils import get_current_tenant

LOGIN_URL = settings.LOGIN_REDIRECT_URL


__all__ = ('consultant_required', 'client_required', 'member_required',)


member_required = login_required


def user_passes_test(test_func, method, login_url=None):
    def _method(request, *args, **kwargs):
        if request.user.is_anonymous():
            return HttpResponseRedirect(login_url or LOGIN_URL)
        if not request.user.is_superuser and not test_func(request.user):
            return HttpResponseForbidden()
        return method(request, *args, **kwargs)
    return _method


def consultant_required(method, login_url=None):
    return user_passes_test(lambda u: u.is_consultant, method, login_url)


def client_required(method, login_url=None):
    return user_passes_test(lambda u: u.is_client, method, login_url)


def admin_required(method, login_url=None):
    return user_passes_test(lambda u: u.is_allowed_change, method, login_url)


def vendor_required(method, login_url=None):
    return user_passes_test(lambda u: u.is_vendor, method, login_url)


def restriction_exempt(method):
    def wrapped_view(*args, **kwargs):
        return method(*args, **kwargs)
    wrapped_view.restriction_exempt = True
    return wraps(method, assigned=available_attrs(method))(wrapped_view)


def member_or_client_required(method, login_url=None):
    def _method(*args, **kwargs):
        if get_current_tenant().is_public_instance:
            return login_required(method)(*args, **kwargs)
        return user_passes_test(
            lambda u: u.is_client, method, login_url)(*args, **kwargs)
    return _method
