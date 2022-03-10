from urlparse import urlparse

from django.contrib.sites.models import Site
from django.conf import settings
from django.core.urlresolvers import reverse

from med_social.utils import today
from customers.models import Customer
from users.models import User
from .constants import AvailabilityConstantsMixin


__all__ = ('constants',)


INEXEC = {
    'USER_KIND': dict([(v, k,) for k, v in User.KIND_CHOICES]),
    'debug_mode': settings.DEBUG,
    'WEBSITE': settings.SITE_INFO,
    'AVAILABILITY': AvailabilityConstantsMixin
}

# No trailing slash
INEXEC['WEBSITE']['ROOT_URL'] = 'http://%s' % settings.SITE_INFO['DOMAIN']


def constants(request):
    return INEXEC


def site_processor(request):
    if hasattr(request, 'tenant') and request.tenant is not None:
        current_tenant = request.tenant
    else:
        current_tenant = Customer.objects.get(schema_name='public')

    referer = request.META.get('HTTP_REFERER', None)
    if referer is not None:
        domain = urlparse(referer)
        if domain.hostname is not None:
            if not domain.hostname.endswith(current_tenant.domain_url):
                referer = domain.path

    referer = referer or reverse('home')
    next_page = request.GET.get('next') or ''
    return {
        'current_site': Site.objects.get_current(),
        'current_tenant': current_tenant,
        'referer': referer,
        'today': today,
        'next_page': next_page
    }


def tab_processor(request):
    return {
        'active_tab': request.GET.get('active_tab') or None
    }
