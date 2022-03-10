from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def icon(icon_name, size='1x', clsid=''):
    """Returns a html tag for font-awesome icons"""
    # TODO: Add support for Bootstrap Glyphicons.
    # TODO: Add support for Font-Awesome icon stacks.
    cls = 'fa fa-{icon_name} fa-{size}'.format(icon_name=icon_name, size=size)
    id=''
    for i in clsid.split(' '):
        if i.startswith('.'):
            cls = '%s %s' % (cls, i.lstrip('.'))
        elif i.startswith('#'):
            id = i.lstrip('#')
    return mark_safe('<i id="%s" class="%s"></i>' % (id, cls))


@register.simple_tag
def star_rating(rating, size='1x'):
    """Returns star icons"""
    # TODO: Add support for Bootstrap Glyphicons.

    from math import floor

    number = int(rating)
    decimal = rating - number
    remaining = int(floor(10 - number))

    out = ''
    for i in xrange(1, number):
        out = '{out}<i class="fa-star fa-{size}"></i>'.format(out=out, size=size)

    if decimal > 0:
        out = '{out}<i class="fa-star-half-full fa-{size}"></i>'.format(out=out, size=size)

    for i in xrange(1, remaining):
        out = '{out}<i class="fa-star-empty fa-{size}"></i>'.format(out=out, size=size)

    return mark_safe(out)
