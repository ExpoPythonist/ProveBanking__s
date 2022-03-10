from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def add_to_qs(context, *pairs):
    """ Adds item(s) to query string.
    
    Usage:
        {% add_to_qs key_1 value_1 key_2 value2 key_n value_n %}
    """
    query = context['request']['GET'].copy()
    keys = pairs[0:][::2] # 0,2,4, etc. are keys
    values = pairs[1:][::2] # 1,3,5, etc. are values
    for key, value in zip(keys, values):
        query[key] = value
    return query.urlencode()

@register.simple_tag(takes_context=True)
def remove_from_qs(query, *keys):
    """ Removes key(s) from query string

    Usage:
        {% remove_from_qs key_1 key_2 key_n %}
    """
    query = context['request']['GET'].copy()
    for key in keys:
        del query[key]
    return query.urlencode()

@register.simple_tag(takes_context=True)
def render_qs(context, separator=":"):
    """ Make html classes framework independent

    Usage, with default key/value separator:
        {% render_qs %}

    Usage, with custom key/value separator:
        {% render_qs '|' %}
    """
    ctx = {}
    ctx['separator'] = separator
    # Make HTML attributes configurable someway
    ctx['ul_class'] = 'query-list'
    ctx['li_class'] = 'query-list'
    ctx['ul_id'] = 'query-display'
    ctx['query'] = []
    for key, value in context['request']['GET'].items():
        key_display = key.replace('_', ' ').title()
        value_display = value.replace('_', ' ').title()
        del_key_href = '?%s' % query_remove(query, key)
        ctx['query'].append({
            'key': key,
            'value': value,
            'key_display' : key_display,
            'value_display': value_display,
            'del_key_href': '?%s' % query_remove(context['request']['GET'], key)
        })
    return mark_safe(out)
