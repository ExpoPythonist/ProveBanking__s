import re
from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.template.defaultfilters import stringfilter
from django.utils.encoding import force_unicode
from rest_framework.renderers import JSONRenderer

from annoying.functions import get_object_or_None
from urlobject import URLObject

from features import models as features
from med_social.utils import get_current_tenant
from vendors.models import Vendor, ProcurementContact, Bid
from users.models import User

register = template.Library()


def __get_ctype_url__(name, obj):
    ctype = ContentType.objects.get_for_model(obj)
    return reverse(name, args=(ctype.id, obj.id,))


@register.simple_tag(takes_context=True)
def get_global_vars_as_json(context):
    user = context['request'].user
    tenant = get_current_tenant()
    config = {
        'features': {
            'financials': features.financials.is_enabled(),
            'projects': features.projects.is_enabled()
        },
        'client': {
            'name': tenant.name,
            'email': tenant.email,
        }
    }
    if user.is_authenticated():
        config['user'] = {
            'is_authenticated': True,
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_client': user.is_client,
            'email': user.email,
            'is_procurement': ProcurementContact.objects.filter(user=user).exists(),
        }
        if user.is_vendor and user.vendor:
            config['user']['vendor'] = user.vendor.id
    else:
        config['user'] = {'is_authenticated': False}
    return JSONRenderer().render(config)


@register.assignment_tag
def assign_ctype_url(name, obj):
    return __get_ctype_url__(name, obj)


@register.simple_tag
def get_ctype_url(name, obj):
    return __get_ctype_url__(name, obj)


@register.simple_tag
def url_with_hostname(url):
    tenant = get_current_tenant()

    if tenant:
        domain = tenant.domain_url
    else:
        domain = settings.SITE_INFO['DOMAIN']
    return URLObject(url).with_hostname(
        domain).with_scheme(settings.HTTP_SCHEME)


@register.assignment_tag
def featured(qs):
    return [q for q in qs if q.featured]


@register.assignment_tag(takes_context=True)
def common_connections(context, consultant):
    networks = context.get('user_networks', set([]))
    networks = list(networks.intersection(set(consultant.networks.all())))
    following = context.get('user_following', set([]))
    people = list(following.intersection(set(consultant.followers.all())))
    if networks or people:
        return {
            'networks': networks,
            'people': people
        }
    else:
        return None


@register.assignment_tag(takes_context=True)
def get_is_following(context, consultant):
    if context['user'].is_authenticated():
        return consultant.id in context['user'].cached_following
    else:
        return []


@register.assignment_tag(takes_context=True)
def load_featured_positions(context, consultant):
    return context.get('featured_positions',
                       [p for p in consultant.positions.all() if p.featured])


@register.assignment_tag(takes_context=True)
def load_featured_educations(context, consultant):
    return context.get('featured_educations',
                       [e for e in consultant.educations.all() if e.featured])


@register.filter(name='times')
def times(number):
    return range(number)


@register.filter(name='reverse_color')
def reverse_color(color):
    color = color or '#ffffff'
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    if brightness < 180:
        return '#FFFFFF'
    else:
        return '#00000'


@register.assignment_tag(takes_context=True)
def is_filter_enabled(context, filter):
    applied_filters = context['filters']
    return str(applied_filters.get(filter[0])) == str(filter[1])


@register.filter
@stringfilter
def an(text):
    contant_sound = re.compile(r'''
    one(![ir])
    ''', re.IGNORECASE | re.VERBOSE)
    vowel_sound = re.compile(r'''
    [aeio]|
    u([aeiou]|[^n][^aeiou]|ni[^dmnl]|nil[^l])|
    h(ier|onest|onou?r|ors\b|our(!i))|
    [fhlmnrsx]\b
    ''', re.IGNORECASE | re.VERBOSE)

    text = force_unicode(text)
    if not contant_sound.match(text) and vowel_sound.match(text):
        return 'an'
    return 'a'


@register.filter
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(key)


@register.simple_tag(name='rating_stars')
def rating_stars(rating):
    stars = ''
    if rating:
        for i in range(int(rating)):
            stars += '<i class="fa fa-star active"></i>'
        if (rating - int(rating)) > 0.1:
            stars += '<i class="fa fa-star-half active"></i>'
        for i in range(int(5 - rating)):
            stars += '<i class="fa fa-star"></i>'
    return stars


@register.simple_tag(name='rating_stars_color')
def rating_stars(rating):
    # rating = ''
    if rating is None:
        return 'secondary'
    if rating <= 1.5:
        return 'one'
    if 1.5 < rating <= 2.5:
        return 'two'
    if 2.5 < rating <= 3.5:
        return 'three'
    if 3.5 < rating <= 4.5:
        return 'four'
    if rating > 4.5:
        return 'five'


@register.filter(name="call")
def call_method(obj, method):
    method = getattr(obj, method)

    if "__callArg" in obj.__dict__:
        ret = method(*obj.__callArg)
        del obj.__callArg
        return ret
    return method()


@register.filter(name="args")
def args(obj, arg):
    if "__callArg" not in obj.__dict__:
        obj.__callArg = []

    obj.__callArg += [arg]
    return obj


# FIXME: move this to the "vendors" app
@register.assignment_tag
def get_total_vendors():
    qs = Vendor.objects.exclude(is_archived=True).count()
    return qs

@register.assignment_tag(takes_context=True)
def get_total_rfps(context):
    user = context['request'].user
    return user.rfps.count() + Bid.objects.filter(vendor__users=user).count()


@register.simple_tag
def get_remaining_allocation(objects, position):
    total_allocation = 0
    total_sum = 100
    for obj in objects[:position]:
        total_allocation += obj.allocation
    return total_sum - total_allocation


@register.filter
def index(List, i):
    return List[int(i)]


@register.filter(name="email_anonymize")
def email_anonymize(email):
    domain = email.split('@')[-1]
    return '********@' + domain


@register.assignment_tag
def get_user_count(user):
    qs = User.objects.all()
    return qs.distinct().count()
