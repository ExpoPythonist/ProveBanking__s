import os
import sys
import redis
import json
from hashlib import md5
from datetime import date, datetime, timedelta
from suds.sudsobject import asdict

from html2text import HTML2Text
from django.conf import settings
from django.db import connection
from django.contrib.humanize.templatetags import humanize
from django.core.mail.message import EmailMessage
from django.utils.text import slugify as django_slugify
from django.template.defaultfilters import timesince, timeuntil
from django.template.loader import render_to_string
from django.utils.timezone import now, make_aware, get_current_timezone, is_naive
from django.utils.html import strip_tags

from mixpanel.tasks import EventTracker

from urlobject.urlobject import URLObject

TEST_ENVIRONMENT = settings.TEST_ENVIRONMENT
SQL_STATEMENT = "select opinr_add_m2m('%s', '%s', '%s', %s, %s)"

DAY = 24 * 60 * 60
WEEK = DAY * 7
MONTH = DAY * 31


def restart_slack_connections():
    # FIXME: This is horrible. Fix it
    circusctl = os.path.join(os.path.dirname(sys.executable), 'circusctl')
    os.system('{} restart slack'.format(circusctl))

def html2text(html):
    h2t = HTML2Text()
    h2t.ignore_links = True
    h2t.ignore_images = True
    return h2t.handle(strip_tags(html))


def escape_unicode_dict(D):
    escaped = {}
    for key, value in D.items():
        if isinstance(value, basestring):
            value = value.encode('unicode-escape')
        escaped[key] = value
    return escaped


def unescape_unicode_dict(D):
    unescaped = {}
    for key, value in D.items():
        if isinstance(value, basestring):
            value = value.decode('unicode-escape')
        unescaped[key] = value
    return unescaped


def to_base64_md5(text, also_slugify=False, also_lower=True):
    text = text.strip()
    if also_slugify:
        text = slugify(text)
    if also_lower:
        text = text.lower()
    return md5(text).digest().encode('base64')[:22]


def get_redis():
    return redis.Redis()


def m2m_exact_match(qs, field, values):
    for value in values:
        qs = qs.filter(**{field: value})
    return qs


def track_event(name, meta):
    if not getattr(settings, 'MIXPANEL_ENABLED', False):
        return
    tenant = get_current_tenant()
    meta['customer_id'] = tenant.id
    meta['site'] = tenant.domain_url
    EventTracker.delay(name, meta)


def get_current_tenant():
    return connection.tenant


def get_absolute_url(path):
    if get_current_tenant().schema_name == 'public':
        domain_url = settings.SITE_INFO['DOMAIN']
    else:
        domain_url = get_current_tenant().domain_url

    return str(URLObject().with_scheme(
        settings.HTTP_SCHEME
    ).with_hostname(
        domain_url
    ).with_path(path))


def get_score_level(score):
    if score == 0:
        return 'poor'
    elif not score:
        return 'N-A'
    elif score >= 4.0:
        return 'good'
    elif score >= 3.0:
        return 'average'
    elif score < 3.0:
        return 'poor'


def humanized_datetime(datetimeobj):
    if not datetimeobj:
        return ''
    if is_naive(datetimeobj):
        datetimeobj = make_aware(datetimeobj, get_current_timezone())
    _now = now()
    if _now.year != datetimeobj.year:
        return datetimeobj.strftime('%d %b, %Y')

    diff = _now - datetimeobj
    if diff.total_seconds() < 30:
        return 'just now'
    if diff.total_seconds() > (DAY * 2):
        return datetimeobj.strftime('%d %b')
    return humanize.naturaltime(datetimeobj)


def humanized_date(dateobj):
    if not dateobj:
        return ''
    _today = today()
    if _today.year != dateobj.year:
        return dateobj.strftime('%d %b, %Y')

    diff = _today - dateobj
    if diff.days in [1, -1, 0]:
        return humanize.naturalday(dateobj)
    return dateobj.strftime('%d %b')


def natural_date(dateobj):
    if not dateobj:
        return ''
    if isinstance(dateobj, datetime):
        natural = humanized_datetime(dateobj)
    else:
        natural = humanized_date(dateobj)
    if not natural:
        _today = today()
        if dateobj < _today:
            return timesince(dateobj)
        else:
            return timeuntil(dateobj)
    return natural


def slugify(text):
    return django_slugify(unicode(text))


def today():
    n = now()
    return date(year=n.year, month=n.month, day=n.day)


def this_week():
    return get_week_from_date(today())


def this_month():
    t = today()
    return date(year=t.year, month=t.month, day=1)


def get_week_from_date(dateobj):
    return dateobj - timedelta(days=dateobj.weekday())


def _get_database_details(key):
    database = settings.DATABASES[key]
    engine = database['ENGINE'].split('.')[-1]
    return engine, database['PASSWORD']


def send_notification_mail(template_prefix, emails, context):
    subj = render_to_string('{0}_subject.txt'.format(template_prefix), context)
    # remove superfluous line breaks
    subj = " ".join(subj.splitlines()).strip()
    body = render_to_string('{0}_message.txt'.format(template_prefix), context)
    msg = EmailMessage(subj, body, settings.DEFAULT_FROM_EMAIL, emails)
    msg.send()


def days_in_date_range(start, end, exclude_weekends=True):
    weekdays = 5 if exclude_weekends else 7
    days = (start + timedelta(x + 1)
            for x in xrange((end - start).days))
    # Number of days excluding weekends
    return sum(1 for day in days if day.weekday() < weekdays)


def recursive_asdict(d):
        """Convert Suds object into serializable format."""
        out = {}
        for k, v in asdict(d).iteritems():
            if hasattr(v, '__keylist__'):
                out[k] = recursive_asdict(v)
            elif isinstance(v, list):
                out[k] = []
                for item in v:
                    if hasattr(item, '__keylist__'):
                        out[k].append(recursive_asdict(item))
                    else:
                        out[k].append(item)
            else:
                out[k] = v
        return out


def suds_to_json(data):
    return json.dumps(recursive_asdict(data))


def add_business_days(from_date, add_days):
    business_days_to_add = add_days
    current_date = from_date
    while business_days_to_add > 0:
        current_date += timedelta(days=1)
        weekday = current_date.weekday()
        if weekday >= 5:
            continue
        business_days_to_add -= 1
    return current_date


def pretty_form_errors(form):
    errors = form.errors
    res = {}
    for field, field_errors in errors.items():
        res[field] = ' '.join(field_errors)
    return res
